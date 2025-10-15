// Copyright 2024 Georges Racinet <georges.racinet@cloudcrane.io>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later

use std::fmt::{Debug, Formatter};
use std::sync::Arc;

use enry::is_generated;
use tonic::{
    codegen::BoxStream, metadata::Ascii, metadata::MetadataValue, Request, Response, Status,
    Streaming,
};
use tracing::{info, instrument};

use hg::repo::Repo;
use hg::revlog::{Node, RevlogError};

use crate::config::Config;
use crate::gitaly::analysis_service_server::{AnalysisService, AnalysisServiceServer};
use crate::gitaly::{
    check_blobs_generated_request::Blob as GeneratedBlobInReq,
    check_blobs_generated_response::Blob as GeneratedBlobInResp, CheckBlobsGeneratedRequest,
    CheckBlobsGeneratedResponse, Repository,
};
use crate::mercurial::lookup_blob;
use crate::metadata::correlation_id;
use crate::oid::extract_blob_oid;
use crate::repository::{
    default_repo_spec_error_status, load_repo_and_stream_bidir, RequestWithRepo,
};
use crate::streaming::{BlockingResponseSender, ResultResponseStream};

use crate::util::tracing_span_id;

#[derive(Debug)]
pub struct AnalysisServiceImpl {
    config: Arc<Config>,
}

#[tonic::async_trait]
impl AnalysisService for AnalysisServiceImpl {
    async fn check_blobs_generated(
        &self,
        request: Request<Streaming<CheckBlobsGeneratedRequest>>,
    ) -> Result<Response<BoxStream<CheckBlobsGeneratedResponse>>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_check_blobs_generated(inner, correlation_id(&metadata))
            .await
    }
}

fn parse_blobs_generated_revision(revision: &[u8]) -> Result<(Node, Vec<u8>), Status> {
    let mut split = revision.splitn(2, |c| *c == b':');
    let req_rev = split
        .next()
        .ok_or_else(|| Status::invalid_argument("Empty revision"))?;

    if let Some(path) = split.next() {
        Ok((
            Node::from_hex(req_rev).map_err(|_| {
                Status::internal(format!("Invalid node {}", String::from_utf8_lossy(req_rev)))
            })?,
            path.to_vec(),
        ))
    } else {
        extract_blob_oid(&String::from_utf8_lossy(req_rev)).map_err(|e| {
            Status::internal(format!(
                "Invalid blob oid {:?}: {:?}",
                String::from_utf8_lossy(req_rev),
                e
            ))
        })
    }
}

fn check_blob_generated(
    repo: &Repo,
    req_blob: GeneratedBlobInReq,
) -> Result<GeneratedBlobInResp, Status> {
    let (node, path) = parse_blobs_generated_revision(&req_blob.revision)?;
    let data = lookup_blob(repo, node.into(), &path)
        .map_err(|e| match e {
            RevlogError::InvalidRevision(_) => Status::internal("unknown revision"),
            e => Status::internal(format!("corrupted repository: {}", e)),
        })?
        .ok_or_else(|| Status::internal("path not found in given revision"))?
        .0;
    let req_path = String::from_utf8_lossy(&req_blob.path);
    Ok(GeneratedBlobInResp {
        revision: req_blob.revision.clone(),
        // errors in is_generated are if req_path or data contain the null byte.
        // It makes sense to claim that no *source* code generation tool would do
        // that.
        generated: is_generated(&req_path, &data).unwrap_or(false),
    })
}

struct CheckBlobsGeneratedTracingRequest<'a>(&'a CheckBlobsGeneratedRequest);

impl Debug for CheckBlobsGeneratedTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        let blobs: Vec<_> = self
            .0
            .blobs
            .iter()
            .map(|blob| {
                format!(
                    "Blob {{ revision:{:?} path:{:?} }}",
                    String::from_utf8_lossy(&blob.revision),
                    String::from_utf8_lossy(&blob.path),
                )
            })
            .collect();

        f.debug_struct("CheckBlobsGeneratedRequest")
            .field("repository", &self.0.repository)
            .field("blobs", &blobs)
            .finish()
    }
}

fn check_blobs_generated_chunk(
    req: CheckBlobsGeneratedRequest,
    repo: &Repo,
    tx: &BlockingResponseSender<CheckBlobsGeneratedResponse>,
) {
    info!(
        "Processing, request chunk={:?}",
        CheckBlobsGeneratedTracingRequest(&req)
    );
    let mut resp_blobs = Vec::with_capacity(req.blobs.len());
    // could also be done by iter/map/collect with error but how well
    for req_blob in req.blobs {
        match check_blob_generated(repo, req_blob) {
            Err(e) => {
                tx.send(Err(e));
                return;
            }
            Ok(blob_in_resp) => resp_blobs.push(blob_in_resp),
        }
    }
    tx.send(Ok(CheckBlobsGeneratedResponse { blobs: resp_blobs }));
}

impl AnalysisServiceImpl {
    #[instrument(name = "check_blobs_generated", skip(self, request))]
    async fn inner_check_blobs_generated(
        &self,
        request: Streaming<CheckBlobsGeneratedRequest>,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<CheckBlobsGeneratedResponse> {
        tracing_span_id!();
        load_repo_and_stream_bidir(
            self.config.clone(),
            request,
            default_repo_spec_error_status,
            move |req, repo, tx| {
                check_blobs_generated_chunk(req, repo, tx);
            },
            move |req, _first_out, repo, tx| {
                // TODO optim open changelog and manifest only once (use first_out!)
                check_blobs_generated_chunk(req, repo, tx);
            },
        )
        .await
    }
}

impl RequestWithRepo for CheckBlobsGeneratedRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn analysis_server(config: &Arc<Config>) -> AnalysisServiceServer<AnalysisServiceImpl> {
    AnalysisServiceServer::new(AnalysisServiceImpl {
        config: config.clone(),
    })
}
