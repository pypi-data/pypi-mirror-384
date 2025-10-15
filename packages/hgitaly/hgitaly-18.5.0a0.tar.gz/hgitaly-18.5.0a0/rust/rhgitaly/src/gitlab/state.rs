// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later

//! Support for GitLab primary state information
//!
//! Heptapod keeps specific data inside Mercurial repositories.
//! This data is notably updated by the server-side Python `heptapod` package on each standard
//! Mercurial write operation.
//!
//! Some of it can be reconstructed by a repository analysis similar to what happens when
//! new content is added to the repository. However, the mere fact that these values have been
//! sent to the Rails application and perhaps other components should be considered part of the
//! state, with side effects such as launching pipelines, changing status of Merge Requests etc.
//! Hence this should not be considered to be a cache.
//!
//! As of this writing, the GitLab state is made of
//!
//! - refs, believed by other components to actually be Git refs. These are kept in several
//!   files, due to vastly different read/write frequencies. Among them are typed refs (branches,
//!   tags etc), and keep-arounds (just hashes). These two cases are represented with different
//!   Rust types in this implementation, whereas the Python reference would consider them all to be
//!   typed refs with a different serialization format for keep-arounds (name would just be
//!   repeating the hash, which is a waste).
//! - default branch, as ultimately defined by end users
//!
//! For a full documentation of the concepts, related file formats and atomicity properties, see the
//! Python docstring.
//!
//! Since the GitLab refs were meant from the onset to be easily understandable by the Rails
//! application, they are also the primary information for HGitaly.
//! The format is simple enough to get an ad-hoc pure async Rust implementation.
use bytes::{Bytes, BytesMut};
use std::io;
use std::path::Path;
use tokio::fs::{metadata, read, File};
use tokio::io::{AsyncBufRead, AsyncBufReadExt, AsyncReadExt, BufReader};
use tokio_stream::wrappers::LinesStream;
use tokio_stream::StreamExt;
use tokio_util::codec::{Decoder, FramedRead};

use hg::{errors::HgError, vfs::VfsImpl, Node, NodePrefix, NULL_NODE};

// Imports used in doc-comments only
#[allow(unused_imports)]
use futures_core::stream::Stream;
#[allow(unused_imports)]
use tokio::io::AsyncRead;

use crate::util::io_error_not_found_as_none;

/// A GitLab typed ref, as in Python `hgext3rd.heptapod.typed_ref`
///
/// The name part is not supposed to repeat the type, typical examples being
/// - `branch/default` or `topic/default/zz` for GitLab branches
/// - the tag name for GitLab tags
/// - `merge-requests/1/head`, `pipeline/2` etc for GitLab special refs
///
/// This means that it must be clear from context in code handling `TypedRef`s what
/// their type is suppposed to be.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TypedRef {
    pub name: Vec<u8>,
    pub target_sha: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq, derive_more::From)]
/// Express that a line does not follow the expected file format
///
/// Absence of this error does not mean that the line components are themselves valid.
/// For example, a typed ref line could be split correctly into its hash and name parts with the
/// hash part not being hexadecimal.
pub struct InvalidLine {
    pub line: Vec<u8>,
}

impl From<&[u8]> for InvalidLine {
    fn from(line: &[u8]) -> Self {
        Self {
            line: line.to_vec(),
        }
    }
}

/// General error type for the public API of this module
#[derive(Debug, derive_more::From)]
pub enum StateFileError {
    UnknownFileFormat,
    #[from]
    InvalidTypedRefLine(InvalidLine),
    #[from]
    IoError(io::Error),
    #[from]
    HgError(HgError),
    InvalidNode(Vec<u8>),
    NotExpectedValue, // TODO add details
}

impl From<StateFileError> for tonic::Status {
    fn from(e: StateFileError) -> Self {
        tonic::Status::internal(format!("GitLab state file error: {:?}", &e))
    }
}

// Yes `..` is ugly, but in truth that file should be in the `store/` subdirectory
const DEFAULT_BRANCH_RPATH: &str = "../default_gitlab_branch";

const VERSION_PREAMBLE: &[u8] = b"001\n";
const SPECIAL_REFS_FILE_NAME: &str = "gitlab.special-refs";
const KEEP_AROUNDS_FILE_NAME: &str = "gitlab.keep-arounds";

/// Read the GitLab default branch information
///
/// This notion is stateful and repository specific (can be tweaked by users). It is independent
/// from what Git and Mercurial would consider to be the default branch (a global setting at most).
pub async fn get_gitlab_default_branch(
    store_vfs: &Path,
) -> Result<Option<Vec<u8>>, StateFileError> {
    let path = store_vfs.join(DEFAULT_BRANCH_RPATH);
    Ok(io_error_not_found_as_none(read(&path).await)?)
}

/// Write the GitLab default branch information
///
/// This is blocking because the store lock must be acquired first, hence
/// we already need the repo.
pub fn set_gitlab_default_branch(vfs: VfsImpl, target_ref: &[u8]) -> Result<(), HgError> {
    vfs.atomic_write(DEFAULT_BRANCH_RPATH, target_ref)
}

pub async fn has_gitlab_default_branch(store_vfs: &Path) -> Result<bool, StateFileError> {
    let path = store_vfs.join(DEFAULT_BRANCH_RPATH);
    Ok(match metadata(&path).await {
        Ok(md) => Ok(md.len() != 0),
        Err(e) => {
            if e.kind() == io::ErrorKind::NotFound {
                Ok(false)
            } else {
                Err(e)
            }
        }
    }?)
}

/// A [`Decoder`] for the typed refs file format, allowing to stream [`TypedRef`]s.
///
/// This can be used with [`FramedRead`] to turn any [`AsyncRead`]
/// into a [`Stream`] of [`TypedRef`]
///
/// The content of the [`AsyncRead`] is expected to follow the file format specification,
/// starting after the version preamble. Examples are available in the tests.
pub struct TypedRefDecoder {
    // Next index of the given buffer to start scanning from.
    // This is a common best-practice for [`Decoder`] implementations, taken
    // traight from https://v0-1--tokio.netlify.app/docs/going-deeper/frames/
    next_index: usize,
}

/// Convenience alias for actual type returned by streaming functions
pub type TypedRefsFileStream = Option<FramedRead<BufReader<File>, TypedRefDecoder>>;
pub type KeepAroundsFileStream = Option<LinesStream<BufReader<File>>>;

type TypedRefsFileStreamResult = Result<TypedRefsFileStream, StateFileError>;

impl Decoder for TypedRefDecoder {
    type Item = TypedRef;
    type Error = StateFileError;

    fn decode(&mut self, buf: &mut BytesMut) -> Result<Option<Self::Item>, Self::Error> {
        if let Some(newline_offset) = buf[self.next_index..].iter().position(|b| *b == b'\n') {
            let newline_index = newline_offset + self.next_index;
            let mut line = buf.split_to(newline_index + 1);
            line.truncate(newline_index);
            self.next_index = 0;
            Ok(Some(parse_line(line.into())?))
        } else {
            Ok(None)
        }
    }
}

fn parse_line(mut bytes: Bytes) -> Result<TypedRef, InvalidLine> {
    if bytes.len() < 42 || bytes[40] != b' ' {
        return Err(bytes.to_vec().into());
    }

    let name = bytes.split_off(41);

    bytes.truncate(40);
    // TODO PERF using to_vec() to limit the scope of refactoring, but it is worth asking
    // whether the zero-copy approach of `Bytes` wouldn't be more efficient (for gRPC requests
    // that don't need to finally copy it) at the price of dynamic dispatch etc (see doc).
    let name = name.to_vec();
    let target_sha = bytes.to_vec();

    Ok(TypedRef {
        name: name.to_vec(),
        target_sha: target_sha.to_vec(),
    })
}

/// Parse a line given as a simple bytes slice
///
/// The line must not include EOL
fn parse_bytes_slice_line(line: &[u8]) -> Result<(&[u8], Node), InvalidLine> {
    if line.len() < 42 || line[40] != b' ' {
        return Err(line.into());
    }
    Ok((
        &line[41..],
        Node::from_hex(&line[..40]).map_err(|_| InvalidLine::from(line))?,
    ))
}

async fn check_version_preamble<R: AsyncBufRead + Unpin>(
    buf: &mut R,
) -> Result<(), StateFileError> {
    let mut version_preamble = [0; 4];
    buf.read_exact(&mut version_preamble).await?;
    if version_preamble != VERSION_PREAMBLE {
        return Err(StateFileError::UnknownFileFormat);
    }
    Ok(())
}

async fn stream_typed_refs<R: AsyncBufRead + Unpin>(
    mut buf: R,
) -> Result<FramedRead<R, TypedRefDecoder>, StateFileError> {
    check_version_preamble(&mut buf).await?;
    Ok(FramedRead::new(buf, TypedRefDecoder { next_index: 0 }))
}

/// Generic function to open a state file and stream [`TypedRef`]s from it.
///
/// It is a perfectly normal condition that the file does not exist, as this is what happens
/// when no ref of the given type has ever been recorded. In that case `None` is returned.
///
/// The repository representation is kept to a bare minimum, as only the path to the `store`
/// subdirectory is used.
///
/// It would look nicer to use hg::vfs::Vfs but that entails going through full repository
/// instantiation, which reads config (useless to us at this point, an order of magnitude slower
/// than what we need for the simplest Gitaly requests) and is definitely not async.
///
/// What we need Vfs for boils down to a base path, so perhaps our own async Vfs would be
/// better when we feel like introducing it, either in RHGitaly or upstream in `hg-core`.
pub async fn stream_typed_refs_file(store_vfs: &Path, filename: &str) -> TypedRefsFileStreamResult {
    Ok(
        match io_error_not_found_as_none(File::open(store_vfs.join(filename)).await)? {
            // not using `map()` because async closures are a pain (unstable in Rust 1.63, notably)
            None => None,
            Some(f) => Some(stream_typed_refs(BufReader::new(f)).await?),
        },
    )
}

/// Specialization of [`stream_typed_refs_file`] for GitLab branches
pub async fn stream_gitlab_branches(store_vfs: &Path) -> TypedRefsFileStreamResult {
    stream_typed_refs_file(store_vfs, "gitlab.branches").await
}

/// Specialization of [`stream_typed_refs_file`] for tags.
pub async fn stream_gitlab_tags(store_vfs: &Path) -> TypedRefsFileStreamResult {
    stream_typed_refs_file(store_vfs, "gitlab.tags").await
}

/// Specialization of [`stream_typed_refs_file`] for GitLab special refs.
pub async fn stream_gitlab_special_refs(store_vfs: &Path) -> TypedRefsFileStreamResult {
    stream_typed_refs_file(store_vfs, SPECIAL_REFS_FILE_NAME).await
}

/// Specialization of [`write_typed_ref`] for GitLab special refs
pub fn write_gitlab_special_ref(
    store_vfs: &VfsImpl,
    sref_name: &[u8],
    target: NodePrefix,
    expected_previous_value: Option<Node>,
) -> Result<(), StateFileError> {
    write_typed_ref(
        store_vfs,
        SPECIAL_REFS_FILE_NAME,
        sref_name,
        target,
        expected_previous_value,
    )
}

/// Read the typed ref file, check format and return full content and offset of actual payload
fn read_typed_ref_file(
    store_vfs: &VfsImpl,
    file_name: &str,
) -> Result<(Vec<u8>, usize), StateFileError> {
    let content = store_vfs
        .try_read(file_name)?
        .unwrap_or_else(|| VERSION_PREAMBLE.to_vec());

    if !content.starts_with(VERSION_PREAMBLE) {
        return Err(StateFileError::UnknownFileFormat);
    }

    Ok((content, VERSION_PREAMBLE.len()))
}

fn write_typed_ref(
    store_vfs: &VfsImpl,
    file_name: &str,
    name: &[u8],
    target: NodePrefix,
    expected_previous_value: Option<Node>,
) -> Result<(), StateFileError> {
    if target.nybbles_len() != 40 {
        return Err(StateFileError::InvalidNode(
            format!("{:x}", target).into_bytes(),
        ));
    }

    // TODO upstream: atomic_write() only accepts a full buffer, hence we
    // have to read the entire content in memory. The file can be noticeably large however.
    let (mut content, payload_start) = read_typed_ref_file(store_vfs, file_name)?;

    if target == NULL_NODE {
        delete_typed_ref_slice_v1(&mut content, payload_start, name, expected_previous_value)?
    } else {
        let target_hex = format!("{:x}", target);
        upsert_typed_ref_slice_v1(
            &mut content,
            payload_start,
            name,
            target_hex.as_bytes(),
            expected_previous_value,
        )?
    };
    Ok(store_vfs.atomic_write(SPECIAL_REFS_FILE_NAME, &content)?)
}

fn delete_typed_ref_slice_v1(
    content: &mut Vec<u8>,
    payload_start: usize,
    name: &[u8],
    expected_previous_value: Option<Node>,
) -> Result<(), StateFileError> {
    let mut line_start = None;
    let payload = &content[payload_start..];
    for (i, c) in payload.iter().enumerate() {
        if *c != b' ' {
            continue;
        }
        if payload[i + 1..].starts_with(name) {
            let after_index = i + name.len() + 1;
            if after_index < payload.len() && payload[after_index] == b'\n' {
                if i < 40 {
                    return Err(InvalidLine {
                        line: payload[..after_index].to_vec(),
                    }
                    .into());
                }
                line_start = Some(i - 40);
                if let Some(val) = expected_previous_value {
                    let expected_hex = format!("{:x}", &val);
                    if expected_hex.as_bytes() != &payload[i - 40..i] {
                        return Err(StateFileError::NotExpectedValue);
                    }
                }
                break;
            }
        }
    }
    if let Some(start) = line_start {
        let line_length = name.len() + 42;
        content[payload_start + start..].rotate_left(line_length);
        content.truncate(content.len() - line_length);
    } // not an error if not found
    Ok(())
}

fn upsert_typed_ref_slice_v1(
    content: &mut Vec<u8>,
    payload_start: usize,
    name: &[u8],
    target_hex: &[u8],
    expected_previous_value: Option<Node>,
) -> Result<(), StateFileError> {
    let mut found = false;
    for line in content[payload_start..].split_mut(|c| *c == b'\n') {
        if line.is_empty() {
            // happens if split_mut is given an empty slice.
            continue; // has the side effect of ignoring empty lines if any, which is harmless
        }
        let (existing_name, existing_target) = parse_bytes_slice_line(line)?;
        if existing_name == name {
            if let Some(expected_previous_value) = expected_previous_value {
                if expected_previous_value != existing_target {
                    return Err(StateFileError::NotExpectedValue);
                }
            }
            line[..40].copy_from_slice(target_hex);
            found = true;
            break;
        }
    }
    if !found {
        if let Some(expected) = expected_previous_value {
            if expected != NULL_NODE {
                return Err(StateFileError::NotExpectedValue);
            }
        }
        content.reserve(name.len() + 42);
        content.extend_from_slice(target_hex);
        content.push(b' ');
        content.extend_from_slice(name);
        content.push(b'\n')
    }
    Ok(())
}

pub fn write_keep_around(
    store_vfs: &VfsImpl,
    name: &[u8],
    target: NodePrefix,
) -> Result<(), StateFileError> {
    let (mut content, payload_start) = read_typed_ref_file(store_vfs, KEEP_AROUNDS_FILE_NAME)?;

    if target == NULL_NODE {
        delete_keep_around_slice_v1(&mut content, payload_start, name)?;
    } else {
        let target_hex = format!("{:x}", target);
        if target_hex.as_bytes() != name {
            return Err(StateFileError::InvalidNode(target_hex.into_bytes()));
        }
        create_keep_around_slice_v1(&mut content, payload_start, name)?;
    }
    Ok(store_vfs.atomic_write(KEEP_AROUNDS_FILE_NAME, &content)?)
}

fn create_keep_around_slice_v1(
    content: &mut Vec<u8>,
    payload_start: usize,
    ka: &[u8],
) -> Result<(), StateFileError> {
    for line in content[payload_start..].split_mut(|c| *c == b'\n') {
        if line.is_empty() {
            // happens if split_mut is given an empty slice.
            continue; // has the side effect of ignoring empty lines if any, which is harmless
        }
        if line == ka {
            return Ok(());
        }
    }
    content.reserve(41);
    content.extend_from_slice(ka);
    content.push(b'\n');
    Ok(())
}

fn delete_keep_around_slice_v1(
    content: &mut Vec<u8>,
    payload_start: usize,
    ka: &[u8],
) -> Result<(), StateFileError> {
    let mut line_start = None;
    let payload = &content[payload_start..];
    for (i, c) in payload.iter().enumerate() {
        if *c != b'\n' {
            continue;
        }
        if i < 40 {
            return Err(InvalidLine {
                line: payload[..i].to_vec(),
            }
            .into());
        }
        if ka == &payload[i - 40..i] {
            line_start = Some(i - 40);
            break;
        }
    }
    if let Some(start) = line_start {
        content[payload_start + start..].rotate_left(41);
        content.truncate(content.len() - 41);
    }
    Ok(())
}

/// Look for a typed ref with given name in a [`TypedRefsFileStream`] and apply a closure if found.
///
/// Returns `Ok(None)` if the typed ref was not found, otherwise `Ok(f(tr))` where `tr` is
/// a [`TypedRef`] representing the successfully found item.
pub async fn map_lookup_typed_ref<F, T>(
    stream_res: TypedRefsFileStream,
    name: &[u8],
    f: F,
) -> Result<Option<T>, StateFileError>
where
    F: FnOnce(TypedRef) -> T + Copy,
{
    match stream_res {
        None => Ok(None),
        Some(stream) => stream
            .filter_map(|res| match res {
                Ok(tr) => {
                    if tr.name == name {
                        Some(Ok(Some(f(tr))))
                    } else {
                        None
                    }
                }
                Err(e) => Some(Err(e)),
            })
            .next()
            .await
            .unwrap_or(Ok(None)),
    }
}

/// Look for [`TypedRef`] with given `name` in a [`TypedRefsFileStream`], returning as [`Node`]
pub async fn lookup_typed_ref_as_node(
    stream_res: TypedRefsFileStream,
    name: &[u8],
) -> Result<Option<Node>, StateFileError> {
    map_lookup_typed_ref(stream_res, name, |tr| {
        Node::from_hex(&tr.target_sha).map_err(|_| StateFileError::InvalidNode(tr.target_sha))
    })
    .await?
    .transpose()
}

async fn stream_keep_arounds<R: AsyncBufRead + Unpin>(
    mut buf: R,
) -> Result<LinesStream<R>, StateFileError> {
    check_version_preamble(&mut buf).await?;
    Ok(LinesStream::new(buf.lines()))
}

/// Open the keep-arounds state file and stream its content as a [`LinesStream`]
///
/// Returns `None` if the state file does not exist.
/// In particular, iterating on the stream yields [`String`] objects, not [`Vec<u8>`].
pub async fn stream_keep_arounds_file(
    store_vfs: &Path,
) -> Result<KeepAroundsFileStream, StateFileError> {
    Ok(
        match io_error_not_found_as_none(File::open(store_vfs.join(KEEP_AROUNDS_FILE_NAME)).await)?
        {
            None => None,
            Some(f) => Some(stream_keep_arounds(BufReader::new(f)).await?),
        },
    )
}

/// Tell whether the repository has a keep-around, given in hexadecimal form
///
/// As other functions in this module, the repository is given just by its
/// `store` subdirectory.
pub async fn has_keep_around(store_vfs: &Path, ka: &[u8]) -> Result<bool, StateFileError> {
    if let Some(mut stream) = stream_keep_arounds_file(store_vfs).await? {
        // cannot use stream.any() and propagate error as it needs the closure to return `bool`,
        // not some Result
        while let Some(res) = stream.next().await {
            if res?.as_bytes() == ka {
                return Ok(true);
            }
        }
        Ok(false)
    } else {
        Ok(false)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use tokio::io::AsyncWriteExt;
    use tokio_stream::StreamExt;

    async fn write_test_file(
        store_vfs: &Path,
        name: &str,
        content: &[u8],
    ) -> Result<(), io::Error> {
        Ok(File::create(store_vfs.join(name))
            .await?
            .write_all(content)
            .await?)
    }

    #[test]
    fn test_parse_bytes_slice_line() {
        assert_eq!(
            parse_bytes_slice_line(b"437bd1bf68ac037eb6956490444e2d7f9a5655c9 branch/default"),
            Ok((
                b"branch/default" as &[u8],
                Node::from_hex(b"437bd1bf68ac037eb6956490444e2d7f9a5655c9").unwrap(),
            ))
        );
        for line in &[
            b"437bd1bf68 branch/default" as &[u8],
            b"X7bd1bf68ac037eb6956490444e2d7f9a5655c9 branch/default",
        ] {
            assert_eq!(parse_bytes_slice_line(line), Err((*line).into()));
        }
    }

    #[test]
    fn test_delete_typed_ref_slice_v1() -> Result<(), StateFileError> {
        let testdata: &[u8] = b"001\n\
                               437bd1bf68ac037eb6956490444e2d7f9a5655c9 merge-requests/head/3\n\
                               d304871165365c6dc923c4bca0b652486959c506 environments/36\n\
                               a617939803200b543730ccdade9df6c6e0952093 pipelines/2\n";

        for (name, expected) in &[
            (
                b"merge-requests/head/3" as &[u8],
                b"001\n\
                  d304871165365c6dc923c4bca0b652486959c506 environments/36\n\
                  a617939803200b543730ccdade9df6c6e0952093 pipelines/2\n"
                    as &[u8],
            ),
            (
                b"environments/36" as &[u8],
                b"001\n\
                  437bd1bf68ac037eb6956490444e2d7f9a5655c9 merge-requests/head/3\n\
                  a617939803200b543730ccdade9df6c6e0952093 pipelines/2\n"
                    as &[u8],
            ),
            (
                b"pipelines/2" as &[u8],
                b"001\n\
                  437bd1bf68ac037eb6956490444e2d7f9a5655c9 merge-requests/head/3\n\
                  d304871165365c6dc923c4bca0b652486959c506 environments/36\n"
                    as &[u8],
            ),
        ] {
            let mut content = testdata.to_vec();
            delete_typed_ref_slice_v1(&mut content, VERSION_PREAMBLE.len(), *name as &[u8], None)?;
            assert_eq!(&content, *expected);
        }
        Ok(())
    }

    #[test]
    fn test_delete_keep_around_slice_v1() -> Result<(), StateFileError> {
        let testdata: &[u8] = b"001\n\
                               437bd1bf68ac037eb6956490444e2d7f9a5655c9\n\
                               d304871165365c6dc923c4bca0b652486959c506\n\
                               a617939803200b543730ccdade9df6c6e0952093\n";
        let mut content = testdata.to_vec();
        delete_keep_around_slice_v1(
            &mut content,
            VERSION_PREAMBLE.len(),
            b"d304871165365c6dc923c4bca0b652486959c506" as &[u8],
        )?;
        assert_eq!(
            &content,
            b"001\n\
                437bd1bf68ac037eb6956490444e2d7f9a5655c9\n\
                a617939803200b543730ccdade9df6c6e0952093\n"
        );
        Ok(())
    }

    #[tokio::test]
    async fn test_stream_typed_refs() -> Result<(), StateFileError> {
        let buf: &[u8] = b"001\n\
                           437bd1bf68ac037eb6956490444e2d7f9a5655c9 branch/default\n\
                           a617939803200b543730ccdade9df6c6e0952093 branch/other\n";
        let stream = stream_typed_refs(buf).await?;
        let res: Vec<TypedRef> = stream.map(|r| r.unwrap()).collect().await;
        assert_eq!(
            res,
            vec![
                TypedRef {
                    name: b"branch/default".to_vec(),
                    target_sha: b"437bd1bf68ac037eb6956490444e2d7f9a5655c9".to_vec()
                },
                TypedRef {
                    name: b"branch/other".to_vec(),
                    target_sha: b"a617939803200b543730ccdade9df6c6e0952093".to_vec()
                },
            ]
        );
        Ok(())
    }

    #[tokio::test]
    async fn test_stream_typed_refs_file() -> Result<(), StateFileError> {
        let tmp_dir = tempdir().unwrap(); // not async, but it doesn't matter much in tests
        let store_vfs = tmp_dir.path();

        assert!(stream_typed_refs_file(store_vfs, "unknown.file")
            .await?
            .is_none());

        write_test_file(
            store_vfs,
            "some.refs",
            b"001\n437bd1bf68ac037eb6956490444e2d7f9a5655c9 branch/default\n",
        )
        .await?;
        let stream = stream_typed_refs_file(store_vfs, "some.refs")
            .await?
            .unwrap();
        let res: Vec<TypedRef> = stream.map(|r| r.unwrap()).collect().await;
        assert_eq!(
            res,
            vec![TypedRef {
                name: b"branch/default".to_vec(),
                target_sha: b"437bd1bf68ac037eb6956490444e2d7f9a5655c9".to_vec()
            }]
        );

        // Error cases

        write_test_file(
            store_vfs,
            "time.paradox",
            b"002\n437bd1bf68ac037eb6956490444e2d7f9a5655c9 branch/default\n",
        )
        .await?;
        match stream_typed_refs_file(store_vfs, "time.paradox").await {
            Ok(_) => {
                panic!("Expected error before actual streaming");
            }
            Err(StateFileError::UnknownFileFormat) => Ok(()),
            Err(e) => Err(e),
        }?;

        write_test_file(store_vfs, "short.hash", b"001\n437bd1bf branch/default\n").await?;
        let mut stream = stream_typed_refs_file(store_vfs, "short.hash")
            .await?
            .unwrap();
        match stream.next().await.unwrap().unwrap_err() {
            StateFileError::InvalidTypedRefLine(il) => {
                assert_eq!(il.line, b"437bd1bf branch/default")
            }
            e => Err(e)?,
        };

        write_test_file(
            store_vfs,
            "wrong.sep",
            b"001\n437bd1bf68ac037eb6956490444e2d7f9a5655c9_branch/default\n",
        )
        .await?;
        let mut stream = stream_typed_refs_file(store_vfs, "wrong.sep")
            .await?
            .unwrap();

        match stream.next().await.unwrap().unwrap_err() {
            StateFileError::InvalidTypedRefLine(il) => Ok(assert_eq!(
                il.line,
                b"437bd1bf68ac037eb6956490444e2d7f9a5655c9_branch/default"
            )),
            e => Err(e),
        }?;
        Ok(())
    }

    #[tokio::test]
    async fn test_map_lookup_typed_refs() -> Result<(), StateFileError> {
        let tmp_dir = tempdir().unwrap(); // not async, but it doesn't matter much in tests
        let store_vfs = tmp_dir.path();

        let empty = stream_gitlab_tags(store_vfs).await?;

        assert_eq!(map_lookup_typed_ref(empty, b"v1.2.3", |_| ()).await?, None);

        write_test_file(
            store_vfs,
            "gitlab.tags",
            b"001\n437bd1bf68ac037eb6956490444e2d7f9a5655c9 v1.2\n",
        )
        .await?;

        let tags = stream_gitlab_tags(store_vfs).await?;
        assert_eq!(
            map_lookup_typed_ref(tags, b"v1.2", |tr| tr).await?,
            Some(TypedRef {
                name: b"v1.2".to_vec(),
                target_sha: b"437bd1bf68ac037eb6956490444e2d7f9a5655c9".to_vec()
            })
        );

        // The stream having been consumed, we need to recreate it
        let tags = stream_gitlab_tags(store_vfs).await?;
        assert_eq!(map_lookup_typed_ref(tags, b"v1.3", |tr| tr).await?, None);
        Ok(())
    }

    #[tokio::test]
    async fn test_stream_keep_arounds_file() -> Result<(), StateFileError> {
        let tmp_dir = tempdir().unwrap(); // not async, but it doesn't matter much in tests
        let store_vfs = tmp_dir.path();

        assert!(stream_keep_arounds_file(store_vfs).await?.is_none());

        write_test_file(
            store_vfs,
            "gitlab.keep-arounds",
            b"001\n437bd1bf68ac037eb6956490444e2d7f9a5655c9",
        )
        .await?;
        let stream = stream_keep_arounds_file(store_vfs).await?.unwrap();
        let res: Vec<String> = stream.map(|r| r.unwrap()).collect().await;
        assert_eq!(
            res,
            vec!["437bd1bf68ac037eb6956490444e2d7f9a5655c9".to_owned()]
        );
        Ok(())
    }

    #[tokio::test]
    async fn test_has_keep_around() -> Result<(), StateFileError> {
        let tmp_dir = tempdir().unwrap(); // not async, but it doesn't matter much in tests
        let store_vfs = tmp_dir.path();

        assert!(!has_keep_around(store_vfs, b"437bd1bf68ac037eb6956490444e2d7f9a5655c9").await?);

        write_test_file(
            store_vfs,
            "gitlab.keep-arounds",
            b"001\n437bd1bf68ac037eb6956490444e2d7f9a5655c9",
        )
        .await?;

        assert!(has_keep_around(store_vfs, b"437bd1bf68ac037eb6956490444e2d7f9a5655c9").await?);
        assert!(!has_keep_around(store_vfs, b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").await?);
        Ok(())
    }
}
