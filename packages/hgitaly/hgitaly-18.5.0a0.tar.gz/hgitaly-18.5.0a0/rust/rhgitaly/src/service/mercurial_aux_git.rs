// Copyright 2025 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later

use std::fmt::Debug;
use std::sync::Arc;
use tokio_util::sync::CancellationToken;
use tonic::{
    codegen::BoxStream,
    metadata::{Ascii, MetadataMap, MetadataValue},
    Request, Response, Status, Streaming,
};
use tracing::{info, instrument};
use walkdir::WalkDir;

use crate::bundle::{
    create_git_bundle, create_repo_from_git_bundle, CreateBundleTracingRequest,
    CreateRepositoryFromBundleTracingRequest,
};
use crate::config::Config;
use crate::gitaly::{
    CreateBundleRequest, CreateBundleResponse, CreateRepositoryFromBundleRequest,
    CreateRepositoryFromBundleResponse, RepositorySizeRequest, RepositorySizeResponse,
};
use crate::hgitaly::mercurial_aux_git_service_server::{
    MercurialAuxGitService, MercurialAuxGitServiceServer,
};
use crate::hgitaly::{AuxGitCommitMappingRequest, AuxGitCommitMappingResponse};

use crate::hg_git;
use crate::metadata::correlation_id;
use crate::repository::{
    blocking_join_error_status, checked_git_repo_path, default_repo_spec_error_status, repo_vfs,
    RequestWithRepo,
};
use crate::streaming::{with_streaming_request_data_as_file, ResultResponseStream};
use crate::util::tracing_span_id;

#[derive(Debug)]
pub struct MercurialAuxGitServiceImpl {
    config: Arc<Config>,
    shutdown_token: CancellationToken,
}

#[tonic::async_trait]
impl MercurialAuxGitService for MercurialAuxGitServiceImpl {
    async fn aux_git_create_bundle(
        &self,
        request: Request<CreateBundleRequest>,
    ) -> Result<Response<BoxStream<CreateBundleResponse>>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_aux_git_create_bundle(inner, correlation_id(&metadata), &metadata)
            .await
    }

    async fn aux_git_create_from_bundle(
        &self,
        request: Request<Streaming<CreateRepositoryFromBundleRequest>>,
    ) -> Result<Response<CreateRepositoryFromBundleResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_aux_git_create_from_bundle(inner, correlation_id(&metadata), &metadata)
            .await
    }

    async fn aux_git_repository_size(
        &self,
        request: Request<RepositorySizeRequest>,
    ) -> Result<Response<RepositorySizeResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_aux_git_repository_size(inner, correlation_id(&metadata))
            .await
    }

    async fn aux_git_commit_mapping(
        &self,
        request: Request<AuxGitCommitMappingRequest>,
    ) -> Result<Response<AuxGitCommitMappingResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_aux_git_commit_mapping(inner, correlation_id(&metadata))
            .await
    }
}

impl MercurialAuxGitServiceImpl {
    #[instrument(name = "aux_git_create_bundle", skip(self, request, metadata))]
    async fn inner_aux_git_create_bundle(
        &self,
        request: CreateBundleRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> ResultResponseStream<CreateBundleResponse> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            CreateBundleTracingRequest(&request)
        );
        let (_gitaly_repo, repo_path) =
            checked_git_repo_path(&self.config, request.repository_ref(), true)
                .await
                .map_err(default_repo_spec_error_status)?;

        create_git_bundle(
            self.config.clone(),
            repo_path,
            self.shutdown_token.clone(),
            metadata,
        )
        .await
    }

    #[instrument(name = "aux_git_create_from_bundle", skip(self, request, metadata))]
    async fn inner_aux_git_create_from_bundle(
        &self,
        request: Streaming<CreateRepositoryFromBundleRequest>,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<CreateRepositoryFromBundleResponse>, Status> {
        tracing_span_id!();
        let config = self.config.clone();
        let shutdown_token = self.shutdown_token.clone();

        with_streaming_request_data_as_file(
            &self.config,
            request,
            |_repo| format!("{}.bundle", rand::random::<u128>()),
            |first_req, bundle_path| async move {
                info!(
                    "Processing, all streamed data already dumped to disk. \
                     First request chunk={:?}",
                    CreateRepositoryFromBundleTracingRequest(&first_req)
                );
                create_repo_from_git_bundle(
                    config,
                    first_req.repository_ref(),
                    true,
                    bundle_path,
                    shutdown_token,
                    metadata,
                )
                .await
            },
        )
        .await?;

        Ok(Response::new(CreateRepositoryFromBundleResponse::default()))
    }

    #[instrument(name = "aux_git_repository_size", skip(self, request))]
    async fn inner_aux_git_repository_size(
        &self,
        request: RepositorySizeRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<RepositorySizeResponse>, Status> {
        info!("Processing");
        match checked_git_repo_path(&self.config, request.repository.as_ref(), true).await {
            Err(_) => Ok(0),
            Ok((_repo, path)) => {
                tokio::task::spawn_blocking(move || {
                    let mut size = 0;
                    // we swallow all errors because the repository might be undergoing heavy
                    // mutations while we are walking it. It does not matter if the size of
                    // this moving target is imprecise in that case
                    for entry in WalkDir::new(path).into_iter().filter_map(|e| e.ok()) {
                        if let Ok(md) = entry.metadata() {
                            size += md.len()
                        }
                    }
                    Ok(size / 1024)
                })
                .await
                .map_err(blocking_join_error_status)?
            }
        }
        .map(|kb| Response::new(RepositorySizeResponse { size: kb as i64 }))
    }
    #[instrument(name = "aux_git_commit_mapping", skip(self, request))]
    async fn inner_aux_git_commit_mapping(
        &self,
        request: AuxGitCommitMappingRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<AuxGitCommitMappingResponse>, Status> {
        info!("Processing");
        let vfs = repo_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        let ids = if request.reverse {
            hg_git::lookup_hg_commit_ids(&vfs, &request.ids).await
        } else {
            hg_git::lookup_git_commit_ids(&vfs, &request.ids).await
        }
        .map_err(|e| Status::internal(format!("Error reading Git map file: {:?}", e)))?;

        Ok(Response::new(AuxGitCommitMappingResponse { ids }))
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn mercurial_aux_git_server(
    config: &Arc<Config>,
    shutdown_token: &CancellationToken,
) -> MercurialAuxGitServiceServer<MercurialAuxGitServiceImpl> {
    MercurialAuxGitServiceServer::new(MercurialAuxGitServiceImpl {
        config: config.clone(),
        shutdown_token: shutdown_token.clone(),
    })
}
