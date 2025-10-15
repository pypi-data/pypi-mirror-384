// Copyright 2024 Georges Racinet <georges.racinet@cloudcrane.io>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later

use std::fmt::Debug;

use std::sync::Arc;

use tonic::{
    metadata::{Ascii, MetadataMap, MetadataValue},
    Request, Response, Status,
};
use tracing::{info, instrument};

use crate::config::Config;
use crate::gitaly::diff_service_client::DiffServiceClient;
use crate::gitaly::diff_service_server::{DiffService, DiffServiceServer};
use crate::gitaly::{
    CommitDeltaRequest, CommitDeltaResponse, CommitDiffRequest, CommitDiffResponse,
    DiffStatsRequest, DiffStatsResponse, FindChangedPathsRequest, FindChangedPathsResponse,
    GetPatchIdRequest, GetPatchIdResponse, RawDiffRequest, RawDiffResponse, RawPatchRequest,
    RawPatchResponse,
};
use crate::metadata::correlation_id;
use crate::sidecar;
use crate::streaming::ResultResponseStream;
use crate::util::tracing_span_id;

#[derive(Debug)]
#[allow(dead_code)]
pub struct DiffServiceImpl {
    config: Arc<Config>,
    sidecar_servers: Arc<sidecar::Servers>,
}

#[tonic::async_trait]
impl DiffService for DiffServiceImpl {
    async fn commit_diff(
        &self,
        request: Request<CommitDiffRequest>,
    ) -> ResultResponseStream<CommitDiffResponse> {
        sidecar::server_streaming!(self, request, DiffServiceClient, commit_diff)
    }

    async fn commit_delta(
        &self,
        request: Request<CommitDeltaRequest>,
    ) -> ResultResponseStream<CommitDeltaResponse> {
        sidecar::server_streaming!(self, request, DiffServiceClient, commit_delta)
    }

    async fn raw_diff(
        &self,
        request: Request<RawDiffRequest>,
    ) -> ResultResponseStream<RawDiffResponse> {
        sidecar::fallback_server_streaming!(
            self,
            inner_raw_diff,
            request,
            DiffServiceClient,
            raw_diff
        )
    }

    async fn raw_patch(
        &self,
        request: Request<RawPatchRequest>,
    ) -> ResultResponseStream<RawPatchResponse> {
        sidecar::fallback_server_streaming!(
            self,
            inner_raw_patch,
            request,
            DiffServiceClient,
            raw_patch
        )
    }

    async fn diff_stats(
        &self,
        request: Request<DiffStatsRequest>,
    ) -> ResultResponseStream<DiffStatsResponse> {
        sidecar::server_streaming!(self, request, DiffServiceClient, diff_stats)
    }

    async fn find_changed_paths(
        &self,
        request: Request<FindChangedPathsRequest>,
    ) -> ResultResponseStream<FindChangedPathsResponse> {
        sidecar::server_streaming!(self, request, DiffServiceClient, find_changed_paths)
    }

    async fn get_patch_id(
        &self,
        request: Request<GetPatchIdRequest>,
    ) -> Result<Response<GetPatchIdResponse>, Status> {
        sidecar::unary!(self, request, DiffServiceClient, get_patch_id)
    }
}

impl DiffServiceImpl {
    #[instrument(name = "raw_diff", skip(self, _request), fields(span_id))]
    async fn inner_raw_diff(
        &self,
        _request: &RawDiffRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> ResultResponseStream<RawDiffResponse> {
        tracing_span_id!();
        info!("Processing");
        Err(Status::unimplemented(""))
    }

    #[instrument(name = "raw_patch", skip(self, _request, _metadata), fields(span_id))]
    async fn inner_raw_patch(
        &self,
        _request: &RawPatchRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        _metadata: &MetadataMap,
    ) -> ResultResponseStream<RawPatchResponse> {
        tracing_span_id!();
        info!("Processing");
        Err(Status::unimplemented(""))
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn diff_server(
    config: &Arc<Config>,
    sidecar_servers: &Arc<sidecar::Servers>,
) -> DiffServiceServer<DiffServiceImpl> {
    DiffServiceServer::new(DiffServiceImpl {
        config: config.clone(),
        sidecar_servers: sidecar_servers.clone(),
    })
}
