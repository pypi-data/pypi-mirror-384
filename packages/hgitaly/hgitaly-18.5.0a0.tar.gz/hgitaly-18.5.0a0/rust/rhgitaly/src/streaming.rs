// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::env;
use std::fmt::Debug;
use std::future::Future;
use std::path::PathBuf;
use std::str::FromStr;

use lazy_static::lazy_static;

use tokio::fs;
use tokio::io::AsyncWriteExt;
use tokio::sync::mpsc::{self, Sender};
use tokio_stream::{wrappers::ReceiverStream, StreamExt};
use tonic::{codegen::BoxStream, Response, Status, Streaming};
use tracing::{debug, error};

use crate::config::Config;
use crate::gitaly::{PaginationCursor, PaginationParameter, Repository};
use crate::repository::{ensure_tmp_dir, RequestWithBytesChunk, RequestWithRepo};

const DEFAULT_WRITE_BUFFER_SIZE: usize = 131072;

lazy_static! {
    pub static ref WRITE_BUFFER_SIZE: usize = {
        env::var("GITALY_STREAMIO_WRITE_BUFFER_SIZE")
            .map(|ref s| usize::from_str(s).unwrap_or(DEFAULT_WRITE_BUFFER_SIZE))
            .unwrap_or(DEFAULT_WRITE_BUFFER_SIZE)
    };
}

/// Simple shortcut: return type for inner implementations
pub type ResultResponseStream<Resp> = Result<Response<BoxStream<Resp>>, Status>;

/// Return a valid, yet empty response stream
pub fn empty_response_stream<Resp: Send + 'static>() -> ResultResponseStream<Resp> {
    let (_tx, rx) = mpsc::channel(1);
    Ok(Response::new(Box::pin(ReceiverStream::new(rx))))
}

/// A specialization of [`Sender`] allowing only blocking sends and logging sending errors
///
/// Server streaming methods involving a repository typically spawn a new thread with
/// [`tokio::task::spawn_blocking`] because the primitives in `hg-core` are blocking. From this
/// thread, the only possible output is to use the [`Sender`] end of a multiple-producer,
/// single-consumer (mpsc) channel, with its `blocking_send` method.
///
/// This is currently the recommended way to send from synchronous to asynchronous code.
/// The only error condition to handle on these sends happens if the receiving side (which takes
/// care of sending the response to the client over the wire) is closing down or closed (e.g. for
/// loss of connectivity?). Since the channel is the only way for the task to report back
/// anything to the client, the only thing that can be done about such errors is to log them.
///
/// This struct also has the advantage to enforce that code from Tokio blocking tasks should never
/// use the (async) `send` method of the underlying mpsc Sender.
#[derive(Debug, derive_more::From)]
pub struct BlockingResponseSender<Resp>(Sender<Result<Resp, Status>>);

impl<Resp> BlockingResponseSender<Resp> {
    pub fn send(&self, res: Result<Resp, Status>) {
        self.0.blocking_send(res).unwrap_or_else(|send_error| {
            let msg = match send_error.0 {
                Ok(_) => "an ordinary response".into(),
                Err(status) => format!("an error response: {}", status),
            };
            // logging at error level because when we implement graceful
            // shutdown, we will try and avoid to write on channels that are
            // closing down.
            // TODO take the opportunity to fully log the original error
            error!("Channel closing down or closed while streaming {}", msg)
        });
    }
}

#[derive(Debug, derive_more::From)]
pub struct AsyncResponseSender<Resp>(Sender<Result<Resp, Status>>);

impl<Resp> AsyncResponseSender<Resp> {
    pub async fn send(&self, res: Result<Resp, Status>) {
        self.0.send(res).await.unwrap_or_else(|send_error| {
            let msg = match send_error.0 {
                Ok(_) => "an ordinary response".into(),
                Err(status) => format!("an error response: {}", status),
            };
            error!("Channel closing down or closed while streaming {}", msg)
        });
    }
}

/// Wrap an inner iterator over Results to aggregate into chunks.
///
/// As soon as an error is encountered while iterating for a chunk, it is yielded in place
/// of the chunk.
///
/// As of Rust 1.65, the stdlib  the [`Iterator`] trait has a `next_chunk` method but
/// - it is unstable
/// - it yields arrays
/// - the remainder still needs to be collected, making it not so practical
/// - it does not have the error handling, of course
struct ChunkedIterator<T, IT, E>
where
    IT: Iterator<Item = Result<T, E>>,
{
    inner: IT,
    chunk_size: usize,
}

impl<T, IT, E> Iterator for ChunkedIterator<T, IT, E>
where
    IT: Iterator<Item = Result<T, E>>,
{
    type Item = Result<Vec<T>, E>;

    fn next(&mut self) -> Option<Result<Vec<T>, E>> {
        let mut chunk: Vec<T> = Vec::new();
        while chunk.len() < self.chunk_size {
            match self.inner.next() {
                None => {
                    if chunk.is_empty() {
                        return None;
                    } else {
                        break;
                    }
                }
                Some(Ok(v)) => chunk.push(v),
                Some(Err(e)) => {
                    return Some(Err(e));
                }
            }
        }
        Some(Ok(chunk))
    }
}

pub const DEFAULT_CHUNK_SIZE: usize = 50;

/// Stream responses by aggregating an inner iterator into chunks
///
/// This is useful when streamed responses have a repeated field: the inner iterator
/// would yield individual elements, and this generic function can be used to
/// collect them in chunks, from which responses are built and sent to the channel.
///
/// The resulting chunks are guaranteed not to be empty.
///
/// Returns `true` iff the iterator was not empty.
///
/// In `resp_builder`, the boolean tells whether the response to build is the first one.
/// It is indeed frequent in the Gitaly protocol for streamed responses with a repeated field
/// and additional metadata to put the metadata on the first response only, the subsequent
/// ones being only about chunking the repeated field.
///
/// This parallels Python `hgitaly.util.chunked` except that the chunk size is for now
/// the constant [`DEFAULT_CHUNK_SIZE`].
/// Note that this flexibility was introduced early in the Python implementation, but has
/// not been actually used yet.
/// Gitaly seems to apply a more subtle logic based on actual response size
/// in some cases. It looks like a better avenue for improvement to mimick that rather than
/// making the chunk size customizable.
pub fn stream_chunks<Iter, Resp, Item, E>(
    tx: &BlockingResponseSender<Resp>,
    iter: Iter,
    resp_builder: impl FnOnce(Vec<Item>, bool) -> Resp + Copy,
    err_handler: impl FnOnce(E) -> Status + Copy,
) -> bool
where
    Iter: Iterator<Item = Result<Item, E>>,
{
    let mut first = true;
    for res in (ChunkedIterator {
        inner: iter,
        chunk_size: DEFAULT_CHUNK_SIZE,
    }) {
        tx.send(res.map_or_else(
            |e| Err(err_handler(e)),
            |chunk| Ok(resp_builder(chunk, first)),
        ));
        if first {
            first = false;
        }
    }
    !first
}

/// This trait is for elements of responses which rely on the Pagination protocol
///
/// Typically, the response will include a repeated field, and the traait is to be
/// implemented on inividual items of that field.
///
/// For an example, see [`crate::gitaly::GetTreeEntriesResponse`]
pub trait PaginableMessageItem: Debug {
    /// Provide the `next_cursor` field of `PaginationCursor`
    ///
    /// This is the value to tell clients that the next page of results would
    /// start after the current item, which is typically the last one returned
    /// by the current call
    fn next_cursor(&self) -> String;

    /// Tell whether this item is the one bearing the givn token.
    ///
    /// This means typically that the wanted results start right afterwards.
    fn match_token(&self, token: &str) -> bool;
}

/// Stream responses by grouping them in chunks and abiding to pagination parameters.
///
/// This is meant to take into account incoming [`PaginationParameter`] and provide in turn
/// the appropriate responses so that the client can request the next page. These together
/// represent an effort in the Gitaly protocol to standardize  a client-driven second level of
/// batching on top of the server-driven streaming responses.
///
/// Returns: `true` iff the entire iterator (regardless of pagination) was
///   not empty
///
/// This function takes severak closure arguments:
///
/// - `resp_builder` is a closure responsible to build a response from collected items and a
///   [`PaginationCursor`] message.
/// - `err_handler` is the generic transformation from the errors that `iterator` may yield.
/// - `token_not_found` provides the error [`Status`] in case no item matches
///    `pagination.page_token`. It is expected to differ among gRPC methods and possibly need
///    some contextual information.
pub fn stream_with_pagination<Iter, Resp, Item, E>(
    tx: &BlockingResponseSender<Resp>,
    pagination: &Option<PaginationParameter>,
    mut iterator: Iter,
    resp_builder: impl FnOnce(Vec<Item>, Option<PaginationCursor>) -> Resp + Copy,
    err_handler: impl FnOnce(E) -> Status + Copy,
    token_not_found: impl FnOnce(&str) -> Status + Copy,
) -> bool
where
    Iter: Iterator<Item = Result<Item, E>>,
    Item: PaginableMessageItem,
{
    match pagination {
        None => {
            // no pagination param: in particular, no limit
            stream_chunks_with_cursor(tx, iterator, "", resp_builder, err_handler)
        }
        Some(pagination) => {
            let mut is_empty = true;
            let token = &pagination.page_token;
            if !token.is_empty() {
                let mut found = false;
                for res in iterator.by_ref() {
                    match res {
                        Ok(item) => {
                            if is_empty {
                                is_empty = false;
                            }
                            if item.match_token(token) {
                                found = true;
                                break;
                            }
                        }
                        Err(e) => {
                            tx.send(Err(err_handler(e)));
                            return true;
                        }
                    }
                }
                if !found {
                    tx.send(Err(token_not_found(token)));
                    return !is_empty;
                }
            }

            if pagination.limit < 0 {
                return stream_chunks_with_cursor(tx, iterator, "", resp_builder, err_handler);
            }

            // No other choice than collecting to truncate and derive `next_cursor`
            let limit = pagination.limit as usize;
            let mut limited: Vec<Result<Item, E>> = Vec::new();
            for (i, item) in iterator.enumerate() {
                if i >= limit {
                    break;
                }
                if is_empty {
                    is_empty = false;
                }
                limited.push(item);
            }
            match limited.last() {
                None => {}
                // In case it is an error, we need to take ownership, since `err_handler` does
                // not work on references. We cannot clone because some of the errors we have to
                // deal with do not implement `Clone` (e.g., [`HgError`] does not)
                Some(Err(_e)) => tx.send(Err(err_handler(
                    limited
                        .pop()
                        .expect("Last element already known to exist and to be an error")
                        .unwrap_err(),
                ))),
                Some(Ok(ref item)) => {
                    // We need to take a ref for next_cursor, so that the closure used in the
                    // underlying `stream_chunks()` is `Copy`, with leads us to clone in actual
                    // `PaginationCursor` instantiation (this is bearable).
                    // We also need to take the ref right now, to make the borrow checker accept its
                    // use in the call below.
                    let next_cursor = &item.next_cursor();
                    stream_chunks_with_cursor(
                        tx,
                        limited.into_iter(),
                        next_cursor,
                        resp_builder,
                        err_handler,
                    );
                }
            }
            !is_empty
        }
    }
}

/// Shortcut to reduce code dupliaction in `stream_chunks_with_pagination`
fn stream_chunks_with_cursor<Iter, Resp, Item, E>(
    tx: &BlockingResponseSender<Resp>,
    iter: Iter,
    next_cursor: &str,
    resp_builder: impl FnOnce(Vec<Item>, Option<PaginationCursor>) -> Resp + Copy,
    err_handler: impl FnOnce(E) -> Status + Copy,
) -> bool
where
    Iter: Iterator<Item = Result<Item, E>>,
{
    stream_chunks(
        tx,
        iter,
        |chunk, first| {
            resp_builder(
                chunk,
                if first {
                    Some(PaginationCursor {
                        next_cursor: next_cursor.to_string(),
                    })
                } else {
                    None
                },
            )
        },
        err_handler,
    )
}

fn dump_streaming_request_error_status(err: tokio::io::Error) -> Status {
    Status::internal(format!(
        "Error dumping streaming request data to file: {err}"
    ))
}

pub async fn with_streaming_request_data_as_file<
    Req: RequestWithRepo + RequestWithBytesChunk,
    Fut: Future<Output = Result<(), Status>>,
>(
    config: &Config,
    mut requests: Streaming<Req>,
    file_name: impl FnOnce(&Repository) -> String,
    and_then: impl FnOnce(Req, PathBuf) -> Fut,
) -> Result<(), Status> {
    if let Some(first_req) = requests.next().await {
        let first_req = first_req?;
        debug!("Dumping streaming request bytes to disk before actual processing");
        let repo = first_req.repository_ref();
        let storage_tmp_dir = ensure_tmp_dir(config, repo).await?;
        let path = storage_tmp_dir.join(file_name(
            repo.expect("Repository should not be None by now"),
        ));
        let mut file = fs::OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(&path)
            .await
            .map_err(dump_streaming_request_error_status)?;
        file.write_all(first_req.bytes_chunk())
            .await
            .map_err(dump_streaming_request_error_status)?;
        while let Some(req) = requests.next().await {
            file.write_all(req?.bytes_chunk())
                .await
                .map_err(dump_streaming_request_error_status)?;
        }
        file.flush()
            .await
            .map_err(dump_streaming_request_error_status)?;

        // Cloning the path is necessary because it will typically be handed over to some async
        // block and a ref would cause problems of lifetimes not being comparable.
        let res = and_then(first_req, path.clone()).await;

        fs::remove_file(&path)
            .await
            .map_err(|e| Status::internal(format!("Could not remove temporary file: {e}")))?;

        res
    } else {
        Err(Status::cancelled("No request received"))
    }
}
