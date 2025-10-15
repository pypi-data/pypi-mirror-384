// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::borrow::Cow;
use std::fmt::{Debug, Formatter};
use std::sync::Arc;

use tonic::{
    codegen::BoxStream,
    metadata::{Ascii, MetadataMap, MetadataValue},
    Request, Response, Status,
};

use hg::repo::Repo;
use hg::revlog::RevlogError;
use hg::NodePrefix;

use crate::config::Config;
use crate::gitaly::blob_service_server::{BlobService, BlobServiceServer};
use crate::gitaly::{
    blob_service_client::BlobServiceClient, get_blobs_request::RevisionPath, GetBlobRequest,
    GetBlobResponse, GetBlobsRequest, GetBlobsResponse, Repository,
};
use crate::gitlab::revision::{blocking_gitlab_revision_node_prefix, RefError};
use crate::mercurial::{lookup_blob, ObjectMetadata};
use crate::message::{empty_blobs_response, BlobResponseChunk};
use crate::metadata::correlation_id;
use crate::oid::extract_blob_oid;
use crate::repository::{
    default_repo_spec_error_status, load_repo_and_stream, unimplemented_if_largefiles,
    RequestWithRepo,
};
use crate::sidecar;
use crate::streaming::{BlockingResponseSender, ResultResponseStream, WRITE_BUFFER_SIZE};
use crate::util::tracing_span_id;

use tracing::{info, instrument};

impl RequestWithRepo for GetBlobRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestWithRepo for GetBlobsRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

#[derive(Debug)]
pub struct BlobServiceImpl {
    config: Arc<Config>,
    sidecar_servers: Arc<sidecar::Servers>,
}

#[tonic::async_trait]
impl BlobService for BlobServiceImpl {
    async fn get_blob(
        &self,
        request: Request<GetBlobRequest>,
    ) -> Result<Response<BoxStream<GetBlobResponse>>, Status> {
        sidecar::fallback_server_streaming!(
            self,
            inner_get_blob,
            request,
            BlobServiceClient,
            get_blob
        )
    }

    async fn get_blobs(
        &self,
        request: Request<GetBlobsRequest>,
    ) -> Result<Response<BoxStream<GetBlobsResponse>>, Status> {
        sidecar::fallback_server_streaming!(
            self,
            inner_get_blobs,
            request,
            BlobServiceClient,
            get_blobs
        )
    }
}

struct GetBlobTracingRequest<'a>(&'a GetBlobRequest);

impl Debug for GetBlobTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("GetBlobsRequest")
            .field("repository", &self.0.repository)
            .field("oid", &self.0.oid)
            .field("limit", &self.0.limit)
            .finish()
    }
}

struct GetBlobsTracingRequest<'a>(&'a GetBlobsRequest);

struct TracingRevisionPaths<'a>(&'a Vec<RevisionPath>);

impl<'a> TracingRevisionPaths<'a> {
    fn to_utf8_lossy(&self) -> Vec<(&'a str, Cow<'a, str>)> {
        self.0
            .iter()
            .map(|rp| (rp.revision.as_ref(), String::from_utf8_lossy(&rp.path)))
            .collect()
    }
}

impl Debug for GetBlobsTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("GetBlobsRequest")
            .field("repository", &self.0.repository)
            .field(
                "revision_paths",
                &TracingRevisionPaths(&self.0.revision_paths).to_utf8_lossy(),
            )
            .finish()
    }
}

impl BlobServiceImpl {
    #[instrument(name = "get_blob", skip(self, request, _metadata), fields(span_id))]
    async fn inner_get_blob(
        &self,
        request: &GetBlobRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        _metadata: &MetadataMap,
    ) -> ResultResponseStream<GetBlobResponse> {
        tracing_span_id!();
        info!("Processing, request={:?}", GetBlobTracingRequest(request));
        if request.oid.is_empty() {
            return Err(Status::invalid_argument("empty Oid"));
        }

        let (node, path) = extract_blob_oid(&request.oid).map_err(|e| {
            Status::invalid_argument(format!("Error parsing Oid {:?}: {:?}", request.oid, e))
        })?;

        unimplemented_if_largefiles(&self.config, &request.repository).await?;
        load_repo_and_stream(
            self.config.clone(),
            request.clone(),
            default_repo_spec_error_status,
            move |req, repo, tx| match lookup_blob(&repo, node.into(), &path) {
                Ok(Some((mut data, metadata))) => {
                    if req.limit >= 0 {
                        data.truncate(req.limit as usize);
                    }
                    stream_blob(&tx, data, metadata);
                }
                Ok(None) => {
                    tx.send(Ok(GetBlobResponse::default()));
                }
                Err(RevlogError::InvalidRevision(_)) => {
                    tx.send(Ok(GetBlobResponse::default()));
                }
                Err(e) => {
                    tx.send(Err(Status::internal(format!(
                        "Error looking up blob: {:?}",
                        e
                    ))));
                }
            },
        )
    }

    #[instrument(name = "get_blobs", skip(self, request, _metadata), fields(span_id))]
    async fn inner_get_blobs(
        &self,
        request: &GetBlobsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        _metadata: &MetadataMap,
    ) -> ResultResponseStream<GetBlobsResponse> {
        tracing_span_id!();
        info!("Processing, request={:?}", GetBlobsTracingRequest(request));
        unimplemented_if_largefiles(&self.config, &request.repository).await?;
        load_repo_and_stream(
            self.config.clone(),
            request.clone(),
            default_repo_spec_error_status,
            move |req, repo, tx| {
                let store_path = repo.working_directory_path().join(".hg/store");
                for rev_path in req.revision_paths {
                    let node_prefix = blocking_gitlab_revision_node_prefix(
                        &store_path,
                        rev_path.revision.as_bytes(),
                    );
                    get_blobs_stream_one(&tx, &repo, node_prefix, rev_path, req.limit)
                        .unwrap_or_else(|status| tx.send(Err(status)));
                }
            },
        )
    }
}

/// Part of GetBlobs implementation streaming one blob
///
/// This takes the incoming [`RevisionPath`] and its resolution result to a [`NodePrefix`],
/// so that the various error cases can be flattened into a single [`Status`], using the question
/// mark operator in the control flow.
fn get_blobs_stream_one(
    tx: &BlockingResponseSender<GetBlobsResponse>,
    repo: &Repo,
    node_prefix: Result<Option<NodePrefix>, RefError>,
    rev_path: RevisionPath,
    limit: i64,
) -> Result<(), Status> {
    match node_prefix.map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))? {
        None => tx.send(Ok(empty_blobs_response(rev_path))),
        Some(node_prefix) => match lookup_blob(repo, node_prefix, &rev_path.path) {
            Ok(Some((mut data, mut metadata))) => {
                if limit >= 0 {
                    data.truncate(limit as usize);
                }
                metadata.revision_path = Some((rev_path.revision, rev_path.path));
                stream_blob(tx, data, metadata);
            }
            Ok(None) => tx.send(Ok(empty_blobs_response(rev_path))),
            Err(RevlogError::InvalidRevision(_)) => {
                tx.send(Ok(GetBlobsResponse::default()));
            }
            Err(e) => {
                return Err(Status::internal(format!("Error looking up blob: {:?}", e)));
            }
        },
    }
    Ok(())
}

pub fn stream_blob<R: BlobResponseChunk>(
    tx: &BlockingResponseSender<R>,
    data: Vec<u8>,
    metadata: ObjectMetadata,
) {
    let mut chunks = data.chunks(*WRITE_BUFFER_SIZE);
    // In case `data` is empty, the iterator will yield `None` immediately,
    // but we still need to send a response with empty data and the metadata,
    // as it is a common pattern for clients to use `limit=0` just to get metadata.
    // One would hope not to have to retrieve the entire content in this case, but
    // sadly this is needed to return the correct size.
    tx.send(Ok(R::with_metadata(chunks.next().unwrap_or(&[]), metadata)));
    for chunk in chunks {
        tx.send(Ok(R::only_data(chunk)));
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn blob_server(
    config: &Arc<Config>,
    sidecar_servers: &Arc<sidecar::Servers>,
) -> BlobServiceServer<BlobServiceImpl> {
    BlobServiceServer::new(BlobServiceImpl {
        config: config.clone(),
        sidecar_servers: sidecar_servers.clone(),
    })
}
