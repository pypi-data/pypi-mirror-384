// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use regex::bytes::Regex;
use std::ffi::{OsStr, OsString};
use std::fmt::{Debug, Formatter};
use std::io::ErrorKind;
use std::os::unix::ffi::OsStrExt;
use std::sync::Arc;
use std::time::Duration;

use rust_embed::Embed;

use tokio::fs;
use tokio::sync::mpsc;
use tokio_stream::{wrappers::ReceiverStream, StreamExt};
use tokio_util::sync::CancellationToken;
use tonic::{
    codegen::BoxStream,
    metadata::{Ascii, MetadataMap, MetadataValue},
    Extensions, Request, Response, Status, Streaming,
};
use tracing::{info, instrument, warn};

use hg::{
    repo::Repo,
    revlog::{changelog::Changelog, NodePrefix, RevlogError},
};

use crate::bundle::{
    create_git_bundle, create_repo_from_git_bundle, git_fetch_bundle, hg_unbundle,
    CreateBundleTracingRequest, CreateRepositoryFromBundleTracingRequest,
};
use crate::config::Config;
use crate::gitaly::repository_service_client::RepositoryServiceClient;
use crate::gitaly::repository_service_server::{RepositoryService, RepositoryServiceServer};
use crate::gitaly::{
    CreateBundleRequest, CreateBundleResponse, CreateRepositoryFromBundleRequest,
    CreateRepositoryFromBundleResponse, CreateRepositoryRequest, CreateRepositoryResponse,
    FetchBundleRequest, FetchBundleResponse, FindLicenseRequest, FindLicenseResponse,
    FindMergeBaseRequest, FindMergeBaseResponse, GetArchiveRequest, GetArchiveResponse,
    GetCustomHooksRequest, GetCustomHooksResponse, GetRawChangesRequest, GetRawChangesResponse,
    HasLocalBranchesRequest, HasLocalBranchesResponse, ObjectFormat, ObjectFormatRequest,
    ObjectFormatResponse, RemoveRepositoryRequest, RemoveRepositoryResponse, Repository,
    RepositoryExistsRequest, RepositoryExistsResponse, RepositorySizeRequest,
    RepositorySizeResponse, RestoreCustomHooksRequest, RestoreCustomHooksResponse,
    SearchFilesByContentRequest, SearchFilesByContentResponse, SearchFilesByNameRequest,
    SearchFilesByNameResponse, SetCustomHooksRequest, SetCustomHooksResponse, WriteRefRequest,
    WriteRefResponse,
};
use crate::gitlab::gitlab_branch_from_ref;
use crate::gitlab::revision::gitlab_revision_node_prefix;
use crate::gitlab::state::stream_gitlab_branches;
use crate::license::license_analysis;
use crate::mercurial::{changelog_entry_manifest, ManifestDirIterator};
use crate::metadata::{correlation_id, fallback_if_feature_disabled, grpc_timeout};
use crate::repository::{
    checked_git_repo_path, checked_repo_path, default_repo_spec_error_status, ensure_tmp_dir,
    git_repo_path, is_repo_aux_git, load_changelog_and_stream, load_changelog_and_then,
    load_repo_and_then, repo_store_vfs, spawner::RepoProcessSpawnerTemplate, RepoSpecError,
    RequestWithBytesChunk, RequestWithRepo,
};
use crate::sidecar;
use crate::streaming::{
    stream_chunks, with_streaming_request_data_as_file, AsyncResponseSender,
    BlockingResponseSender, ResultResponseStream,
};
use crate::util::{bytes_strings_as_str, tracing_span_id};
use crate::workdir::working_directories_root;

mod write_ref;

const SEARCH_FILES_FILTER_MAX_LENGTH: usize = 1000;

#[derive(Embed)]
#[folder = "../dependencies/licenses_data"]
pub struct LicensesDataCache;

//#[derive(Debug)]
pub struct RepositoryServiceImpl {
    config: Arc<Config>,
    shutdown_token: CancellationToken,
    sidecar_servers: Arc<sidecar::Servers>,
    licenses_db: Arc<askalono::Store>,
}

#[tonic::async_trait]
impl RepositoryService for RepositoryServiceImpl {
    async fn repository_exists(
        &self,
        request: Request<RepositoryExistsRequest>,
    ) -> Result<Response<RepositoryExistsResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_repository_exists(inner, correlation_id(&metadata))
            .await
    }

    async fn repository_size(
        &self,
        request: Request<RepositorySizeRequest>,
    ) -> Result<Response<RepositorySizeResponse>, Status> {
        sidecar::unary!(self, request, RepositoryServiceClient, repository_size)
    }

    async fn object_format(
        &self,
        request: Request<ObjectFormatRequest>,
    ) -> Result<Response<ObjectFormatResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_object_format(inner, correlation_id(&metadata))
            .await
            .map(|v| Response::new(ObjectFormatResponse { format: v as i32 }))
    }

    async fn create_repository(
        &self,
        request: Request<CreateRepositoryRequest>,
    ) -> Result<Response<CreateRepositoryResponse>, Status> {
        sidecar::fallback_unary!(
            self,
            inner_create_repository,
            request,
            RepositoryServiceClient,
            create_repository
        )
    }

    async fn get_archive(
        &self,
        request: Request<GetArchiveRequest>,
    ) -> Result<Response<BoxStream<GetArchiveResponse>>, Status> {
        sidecar::fallback_server_streaming!(
            self,
            inner_get_archive,
            request,
            RepositoryServiceClient,
            get_archive
        )
    }

    async fn has_local_branches(
        &self,
        request: Request<HasLocalBranchesRequest>,
    ) -> Result<Response<HasLocalBranchesResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_has_local_branches(inner, correlation_id(&metadata))
            .await
            .map(|v| Response::new(HasLocalBranchesResponse { value: v }))
    }

    async fn write_ref(
        &self,
        request: Request<WriteRefRequest>,
    ) -> Result<Response<WriteRefResponse>, Status> {
        sidecar::fallback_unary!(
            self,
            inner_write_ref,
            request,
            RepositoryServiceClient,
            write_ref
        )
    }

    async fn find_merge_base(
        &self,
        request: Request<FindMergeBaseRequest>,
    ) -> Result<Response<FindMergeBaseResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_merge_base(inner, correlation_id(&metadata))
            .await
            .map(Response::new)
    }

    async fn create_bundle(
        &self,
        request: Request<CreateBundleRequest>,
    ) -> Result<Response<BoxStream<CreateBundleResponse>>, Status> {
        sidecar::fallback_server_streaming!(
            self,
            inner_create_bundle,
            request,
            RepositoryServiceClient,
            create_bundle
        )
    }

    async fn create_repository_from_bundle(
        &self,
        request: Request<Streaming<CreateRepositoryFromBundleRequest>>,
    ) -> Result<Response<CreateRepositoryFromBundleResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_create_repository_from_bundle(inner, correlation_id(&metadata), &metadata)
            .await
    }

    async fn find_license(
        &self,
        request: Request<FindLicenseRequest>,
    ) -> Result<Response<FindLicenseResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();
        self.inner_find_license(&inner, correlation_id(&metadata))
            .await
    }

    async fn get_raw_changes(
        &self,
        request: Request<GetRawChangesRequest>,
    ) -> Result<Response<BoxStream<GetRawChangesResponse>>, Status> {
        sidecar::server_streaming!(self, request, RepositoryServiceClient, get_raw_changes)
    }

    async fn search_files_by_name(
        &self,
        request: Request<SearchFilesByNameRequest>,
    ) -> Result<Response<BoxStream<SearchFilesByNameResponse>>, Status> {
        let (metadata, _ext, inner) = request.into_parts();
        self.inner_search_files_by_name(inner, correlation_id(&metadata))
            .await
    }

    async fn search_files_by_content(
        &self,
        request: Request<SearchFilesByContentRequest>,
    ) -> Result<Response<BoxStream<SearchFilesByContentResponse>>, Status> {
        sidecar::server_streaming!(
            self,
            request,
            RepositoryServiceClient,
            search_files_by_content
        )
    }

    async fn fetch_bundle(
        &self,
        request: Request<Streaming<FetchBundleRequest>>,
    ) -> Result<Response<FetchBundleResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_fetch_bundle(inner, correlation_id(&metadata), &metadata)
            .await
    }

    async fn restore_custom_hooks(
        &self,
        request: Request<Streaming<RestoreCustomHooksRequest>>,
    ) -> Result<Response<RestoreCustomHooksResponse>, Status> {
        sidecar::client_streaming!(self, request, RepositoryServiceClient, restore_custom_hooks)
    }

    async fn set_custom_hooks(
        &self,
        request: Request<Streaming<SetCustomHooksRequest>>,
    ) -> Result<Response<SetCustomHooksResponse>, Status> {
        sidecar::client_streaming!(self, request, RepositoryServiceClient, set_custom_hooks)
    }

    async fn get_custom_hooks(
        &self,
        request: Request<GetCustomHooksRequest>,
    ) -> Result<Response<BoxStream<GetCustomHooksResponse>>, Status> {
        sidecar::fallback_server_streaming!(
            self,
            inner_get_custom_hooks,
            request,
            RepositoryServiceClient,
            get_custom_hooks
        )
    }

    async fn remove_repository(
        &self,
        request: Request<RemoveRepositoryRequest>,
    ) -> Result<Response<RemoveRepositoryResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_remove_repository(inner, correlation_id(&metadata))
            .await
    }
}

impl RepositoryServiceImpl {
    #[instrument(name = "repository_exists", skip(self, request), fields(span_id))]
    async fn inner_repository_exists(
        &self,
        request: RepositoryExistsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<RepositoryExistsResponse>, Status> {
        tracing_span_id!();
        info!("Processing, repository={:?}", &request.repository);

        match checked_repo_path(&self.config, request.repository.as_ref()).await {
            Ok(_) => Ok(true),
            Err(RepoSpecError::RepoNotFound(_)) => Ok(false),
            Err(e) => Err(default_repo_spec_error_status(e)),
        }
        .map(|res| Response::new(RepositoryExistsResponse { exists: res }))
    }

    #[instrument(name = "object_format", skip(self, request), fields(span_id))]
    async fn inner_object_format(
        &self,
        request: ObjectFormatRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<ObjectFormat, Status> {
        tracing_span_id!();
        info!("Processing, repository={:?}", &request.repository);

        // return standard errors if repo does not exist, as Gitaly does
        if is_repo_aux_git(&request) {
            checked_git_repo_path(&self.config, request.repository_ref(), false)
                .await
                .map_err(default_repo_spec_error_status)?;
        } else {
            repo_store_vfs(&self.config, &request.repository)
                .await
                .map_err(default_repo_spec_error_status)?;
        }
        Ok(ObjectFormat::Unspecified)
    }

    #[instrument(
        name = "create_repository",
        skip(self, request, metadata),
        fields(span_id)
    )]
    async fn inner_create_repository(
        &self,
        request: &CreateRepositoryRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<CreateRepositoryResponse>, Status> {
        tracing_span_id!();
        info!("Processing, repository={:?}", &request.repository);
        let config = &self.config;
        if is_repo_aux_git(request) {
            let repo_path = git_repo_path(
                config,
                request
                    .repository_ref()
                    .expect("Repository should be specified since we know it to be an aux Git"),
                false,
            )
            .map_err(default_repo_spec_error_status)?;
            // Gitaly does the creation in its tmp directory, for transactional purposes. We are not
            // at his point, and maybe will not need to handle the aux Git repository when we do.
            let mut spawner = RepoProcessSpawnerTemplate::new_git_at_path(
                config.clone(),
                config.repositories_root.clone(),
                metadata,
                vec![],
            )
            .await?
            .git_spawner();
            let mut args: Vec<OsString> = vec!["init".into(), "--bare".into(), "--quiet".into()];
            // TODO initial default branch name
            let default_branch = &request.default_branch;
            if !default_branch.is_empty() {
                args.push("--initial-branch".into());
                args.push(OsStr::from_bytes(default_branch).to_os_string())
            }
            args.push(repo_path.into()); // git init does create all needed intermediate directories
            spawner.args(&args);
            let git_exit_code = spawner.spawn(self.shutdown_token.clone()).await?;
            if git_exit_code != 0 {
                warn!("Git subprocess exited with code {git_exit_code}");
                return Err(Status::internal(format!(
                    "Git subprocess exited with code {git_exit_code}"
                )));
            }
            Ok(Response::new(CreateRepositoryResponse::default()))
        } else {
            Err(Status::unimplemented("")) // fallback to HGitaly
        }
    }

    #[instrument(name = "get_archive", skip(self, _request, _metadata), fields(span_id))]
    async fn inner_get_archive(
        &self,
        _request: &GetArchiveRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        _metadata: &MetadataMap,
    ) -> ResultResponseStream<GetArchiveResponse> {
        tracing_span_id!();
        info!("Processing");
        Err(Status::unimplemented("")) // fallback to HGitaly
    }

    #[instrument(name = "has_local_branches", skip(self, request), fields(span_id))]
    async fn inner_has_local_branches(
        &self,
        request: HasLocalBranchesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<bool, Status> {
        tracing_span_id!();
        info!("Processing, repository={:?}", &request.repository);

        let store_vfs = repo_store_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;
        if let Some(mut stream) = stream_gitlab_branches(&store_vfs).await.map_err(|e| {
            Status::internal(format!("Problem reading Gitlab branches file: {:?}", e))
        })? {
            Ok(stream.next().await.is_some())
        } else {
            Ok(false)
        }
    }

    #[instrument(name = "write_ref", skip(self, request, metadata), fields(span_id))]
    async fn inner_write_ref(
        &self,
        request: &WriteRefRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<WriteRefResponse>, Status> {
        tracing_span_id!();
        fallback_if_feature_disabled(metadata, "rhgitaly-write-ref", false)?;
        info!(
            "Processing, request={:?}",
            write_ref::TracingRequest(request)
        );

        let to_write = &request.r#ref;
        let target = &request.revision;

        if to_write == b"HEAD" && gitlab_branch_from_ref(target).is_none() {
            return Err(Status::invalid_argument(format!(
                "The default GitLab branch can only be set to a branch ref, got '{}' instead",
                String::from_utf8_lossy(target)
            )));
        }
        let timeout = grpc_timeout(metadata).unwrap_or(Duration::from_secs(10));
        load_repo_and_then(
            self.config.clone(),
            request.clone(),
            default_repo_spec_error_status,
            move |req, repo| write_ref::write(req, repo, timeout),
        )
        .await?;
        Ok(Response::new(WriteRefResponse::default()))
    }

    #[instrument(name = "find_merge_base", skip(self, request), fields(span_id))]
    async fn inner_find_merge_base(
        &self,
        request: FindMergeBaseRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<FindMergeBaseResponse, Status> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            FindMergeBaseTracingRequest(&request)
        );

        if request.revisions.len() < 2 {
            return Err(Status::invalid_argument(
                "at least 2 revisions are required",
            ));
        }

        let store_vfs = repo_store_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        let mut nodes: Vec<NodePrefix> = Vec::with_capacity(request.revisions.len());
        // TODO perf we are reading potentially all state files for each revision, but we
        // have to hurry, to unblock Heptapod's own MRs.
        // (according to comments in protocol the case when there would be more than 2 revisions
        // is very unlikely).
        for revision in &request.revisions {
            match gitlab_revision_node_prefix(&store_vfs, revision)
                .await
                .map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))?
            {
                None => {
                    info!(
                        "Revision {} not resolved",
                        String::from_utf8_lossy(revision)
                    );
                    return Ok(FindMergeBaseResponse::default());
                }
                Some(node_prefix) => {
                    nodes.push(node_prefix);
                }
            }
        }
        let maybe_gca_node = load_changelog_and_then(
            self.config.clone(),
            request,
            default_repo_spec_error_status,
            move |_req, _repo, cl| {
                // TODO unwrap*2
                let revs: Result<Vec<_>, _> =
                    nodes.into_iter().map(|n| cl.rev_from_node(n)).collect();
                let revs = revs.map_err(|e| {
                    Status::internal(format!(
                        "Inconsistency: Node ID from GitLab state file \
                     or received from client could not be resolved {:?}",
                        e
                    ))
                })?;
                Ok(cl
                    .get_index()
                    .ancestors(&revs)
                    .map_err(|e| Status::internal(format!("GraphError: {:?}", e)))?
                    .first()
                    .map(|rev| cl.node_from_rev(*rev))
                    .copied())
            },
        )
        .await?;

        Ok(
            maybe_gca_node.map_or_else(FindMergeBaseResponse::default, |node| {
                FindMergeBaseResponse {
                    base: format!("{:x}", node),
                }
            }),
        )
    }

    #[instrument(name = "create_bundle", skip(self, request, metadata))]
    async fn inner_create_bundle(
        &self,
        request: &CreateBundleRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> ResultResponseStream<CreateBundleResponse> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            CreateBundleTracingRequest(request)
        );
        if is_repo_aux_git(request) {
            let (_gitaly_repo, repo_path) =
                checked_git_repo_path(&self.config, request.repository_ref(), false)
                    .await
                    .map_err(default_repo_spec_error_status)?;

            create_git_bundle(
                self.config.clone(),
                repo_path,
                self.shutdown_token.clone(),
                metadata,
            )
            .await
        } else {
            Err(Status::unimplemented("")) // fallback to HGitaly
        }
    }

    #[instrument(name = "create_repository_from_bundle", skip(self, request, metadata))]
    async fn inner_create_repository_from_bundle(
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
                if is_repo_aux_git(&first_req) {
                    create_repo_from_git_bundle(
                        config,
                        first_req.repository_ref(),
                        false,
                        bundle_path,
                        shutdown_token,
                        metadata,
                    )
                    .await
                } else {
                    let create_request = Request::from_parts(
                        metadata.clone(),
                        Extensions::default(),
                        CreateRepositoryRequest {
                            repository: first_req.repository.clone(),
                            ..Default::default()
                        },
                    );
                    info!("Invoking sidecar for repository creation itself");
                    sidecar::unary!(
                        self,
                        create_request,
                        RepositoryServiceClient,
                        create_repository
                    )?;

                    hg_unbundle(
                        config,
                        first_req,
                        bundle_path,
                        shutdown_token,
                        metadata,
                        Some(true),
                    )
                    .await
                }
            },
        )
        .await?;

        Ok(Response::new(CreateRepositoryFromBundleResponse::default()))
    }

    #[instrument(name = "find_license", skip(self, request))]
    async fn inner_find_license(
        &self,
        request: &FindLicenseRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<FindLicenseResponse>, Status> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            FindLicenseTracingRequest(request),
        );
        let config = self.config.clone();

        let store_vfs = repo_store_vfs(&config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;
        let maybe_node = gitlab_revision_node_prefix(&store_vfs, b"HEAD")
            .await
            .map_err(|e| {
                Status::internal(format!("Error looking for default branch head: {:?}", e))
            })?;
        if let Some(node) = maybe_node {
            let licenses_db = self.licenses_db.clone();

            load_changelog_and_then(
                self.config.clone(),
                request.clone(),
                default_repo_spec_error_status,
                move |_req, repo, cl| {
                    license_analysis(&licenses_db, repo, cl, node)
                        .map_err(|e| {
                            Status::internal(format!("Error looking for license files: {}", e))
                        })
                        .map(Response::new)
                },
            )
            .await
        } else {
            Ok(Response::new(FindLicenseResponse::default()))
        }
    }

    #[instrument(name = "search_files_by_name", skip(self, request))]
    async fn inner_search_files_by_name(
        &self,
        request: SearchFilesByNameRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<SearchFilesByNameResponse> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            SearchFilesByNameTracingRequest(&request)
        );
        let gitlab_ref = &request.r#ref;
        let store_vfs = repo_store_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;
        let gitlab_ref = if gitlab_ref.is_empty() {
            b"HEAD".as_ref()
        } else {
            gitlab_ref
        };
        if request.query.is_empty() {
            return Err(Status::invalid_argument("no query given"));
        }
        if request.filter.len() > SEARCH_FILES_FILTER_MAX_LENGTH {
            return Err(Status::invalid_argument("filter exceeds maximum length"));
        }
        let filter_rx = if request.filter.is_empty() {
            None
        } else {
            Some(Regex::new(&request.filter).map_err(|e| {
                Status::invalid_argument(format!("Invalid regular expression: {}", e))
            })?)
        };

        let maybe_node = gitlab_revision_node_prefix(&store_vfs, gitlab_ref)
            .await
            .map_err(|e| {
                Status::internal(format!("Error looking for default branch head: {:?}", e))
            })?;
        load_changelog_and_stream(
            self.config.clone(),
            request.clone(),
            default_repo_spec_error_status,
            move |req, repo, cl, tx| {
                if let Some(node) = maybe_node {
                    if let Err(e) = stream_search_files_by_name(req, repo, node, cl, filter_rx, &tx)
                    {
                        tx.send(Err(Status::internal(format!("RevLogError: {}", e))));
                    }
                } else {
                    // Gitaly does send an empty response in this case
                    tx.send(Ok(SearchFilesByNameResponse::default()))
                }
            },
        )
    }

    #[instrument(name = "fetch_bundle", skip(self, request, metadata))]
    async fn inner_fetch_bundle(
        &self,
        request: Streaming<FetchBundleRequest>,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<FetchBundleResponse>, Status> {
        tracing_span_id!();
        let token = self.shutdown_token.clone();
        let config = self.config.clone();
        with_streaming_request_data_as_file(
            &self.config,
            request,
            |_repo| format!("{}.bundle", rand::random::<u128>()),
            |first_req, bundle_path| async move {
                info!(
                    "Processing, all streamed data already dumped to disk. \
                     First request chunk={:?}",
                    FetchBundleTracingRequest(&first_req)
                );
                if is_repo_aux_git(&first_req) {
                    git_fetch_bundle(config, first_req, bundle_path, token, metadata).await
                } else {
                    hg_unbundle(config, first_req, bundle_path, token, metadata, Some(true)).await
                }
            },
        )
        .await?;

        Ok(Response::new(FetchBundleResponse::default()))
    }

    #[instrument(name = "get_custom_hooks", skip(self, request, _metadata))]
    async fn inner_get_custom_hooks(
        &self,
        request: &GetCustomHooksRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        _metadata: &MetadataMap,
    ) -> ResultResponseStream<GetCustomHooksResponse> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            GetCustomHooksTracingRequest(request)
        );
        if is_repo_aux_git(request) {
            // TODO cases of missing repo and empty repo
            let (tx, rx) = mpsc::channel(1);
            let tx: AsyncResponseSender<_> = tx.into();
            tx.send(Ok(GetCustomHooksResponse::default())).await;
            return Ok(Response::new(Box::pin(ReceiverStream::new(rx))));
        } else {
            Err(Status::unimplemented("")) // fallback to HGitaly
        }
    }

    #[instrument(name = "remove_repository", skip(self, request), fields(span_id))]
    async fn inner_remove_repository(
        &self,
        request: RemoveRepositoryRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<RemoveRepositoryResponse>, Status> {
        tracing_span_id!();
        info!("Processing, repository={:?}", &request.repository);

        let repo = request.repository.as_ref();

        let path = if is_repo_aux_git(&request) {
            checked_git_repo_path(&self.config, repo, false).await
        } else {
            checked_repo_path(&self.config, repo).await
        }
        .map_err(default_repo_spec_error_status)?
        .1;
        let mut tmp_slug = path
            .file_name()
            .expect("Repository absolute path should have a file name")
            .to_owned();
        tmp_slug.push("+removed-");
        tmp_slug.push(rand::random::<u64>().to_string());
        let trash_path = ensure_tmp_dir(&self.config, repo).await?.join(tmp_slug);

        fs::rename(&path, &trash_path).await.map_err(|e| {
            Status::internal(format!(
                "Failed to move repo at {} to trash path {}: {}",
                path.display(),
                trash_path.display(),
                e
            ))
        })?;
        fs::remove_dir_all(trash_path)
            .await
            .map_err(|e| Status::internal(format!("Failed to clean up trash path {e}")))?;

        if !is_repo_aux_git(&request) {
            let repo =
                repo.expect("Repository should be present and should already have been checked");

            let workdirs = working_directories_root(&self.config, repo);
            info!("Removign workdirs at {}", workdirs.display());
            if let Err(e) = fs::remove_dir_all(&workdirs).await {
                if e.kind() != ErrorKind::NotFound {
                    let feedback = workdirs.display();
                    return Err(Status::internal(format!(
                        "Failed to clean up working directories at {feedback}: {e}"
                    )));
                }
            }
            let aux_git =
                git_repo_path(&self.config, repo, true).map_err(default_repo_spec_error_status)?;
            if let Err(e) = fs::remove_dir_all(&aux_git).await {
                if e.kind() != ErrorKind::NotFound {
                    let feedback = aux_git.display();
                    return Err(Status::internal(format!(
                        "Failed to clean up working directories at {feedback}: {e}"
                    )));
                }
            }
        }
        Ok(Response::new(RemoveRepositoryResponse::default()))
    }
}

fn stream_search_files_by_name(
    mut req: SearchFilesByNameRequest,
    repo: &Repo,
    node: NodePrefix,
    cl: &Changelog,
    filter_rx: Option<Regex>,
    tx: &BlockingResponseSender<SearchFilesByNameResponse>,
) -> Result<(), RevlogError> {
    if req.query == "." {
        req.query.clear()
    }

    let manifestlog = repo.manifestlog()?;
    let limit = if req.limit == 0 {
        usize::MAX // for the sake of type uniformity with actual limit
    } else {
        req.limit as usize
    };

    // manifest is None is node resolves to NULL_REVISION. In that case not streaming
    // anything is fine
    if let Some((_node, manifest)) = changelog_entry_manifest(cl, &manifestlog, node)? {
        let entries_iter =
            ManifestDirIterator::new(manifest.iter(), req.query.as_bytes(), filter_rx);

        if !stream_chunks(
            tx,
            entries_iter
                .skip(req.offset as usize)
                .take(limit)
                .map(|res| res.map(|entry| entry.path.as_bytes().to_vec())),
            |chunk, _is_first| SearchFilesByNameResponse { files: chunk },
            |e| Status::internal(format!("Unexpected manifest error {}", e)),
        ) {
            // Gitaly does send an empty response if there is no match
            tx.send(Ok(SearchFilesByNameResponse::default()));
        }
    };
    Ok(())
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn repository_server(
    config: &Arc<Config>,
    shutdown_token: &CancellationToken,
    sidecar_servers: &Arc<sidecar::Servers>,
) -> RepositoryServiceServer<RepositoryServiceImpl> {
    let licenses_db_cache = LicensesDataCache::get("cache.zstd").unwrap();

    RepositoryServiceServer::new(RepositoryServiceImpl {
        config: config.clone(),
        shutdown_token: shutdown_token.clone(),
        sidecar_servers: sidecar_servers.clone(),
        licenses_db: Arc::new(
            askalono::Store::from_cache(licenses_db_cache.data.as_ref()).unwrap(),
        ),
    })
}

impl RequestWithRepo for SearchFilesByNameRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestWithRepo for FindMergeBaseRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestWithRepo for FindLicenseRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestWithRepo for ObjectFormatRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestWithRepo for GetCustomHooksRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestWithRepo for RemoveRepositoryRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestWithRepo for CreateRepositoryRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestWithBytesChunk for FetchBundleRequest {
    fn bytes_chunk(&self) -> &[u8] {
        &self.data
    }
}
impl RequestWithRepo for SetCustomHooksRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestWithBytesChunk for SetCustomHooksRequest {
    fn bytes_chunk(&self) -> &[u8] {
        &self.data
    }
}

struct FindMergeBaseTracingRequest<'a>(&'a FindMergeBaseRequest);

impl Debug for FindMergeBaseTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FindMergeBaseRequest")
            .field("repository", &self.0.repository)
            .field("revisions", &bytes_strings_as_str(&self.0.revisions))
            .finish()
    }
}

struct FindLicenseTracingRequest<'a>(&'a FindLicenseRequest);

impl Debug for FindLicenseTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FindLicenseRequest")
            .field("repository", &self.0.repository)
            .finish()
    }
}

struct SearchFilesByNameTracingRequest<'a>(&'a SearchFilesByNameRequest);

impl Debug for SearchFilesByNameTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SearchFilesByNameRequest")
            .field("repository", &self.0.repository)
            .field("query", &self.0.query)
            .field("ref", &String::from_utf8_lossy(&self.0.r#ref))
            .field("filter", &self.0.filter)
            .field("limit", &self.0.limit)
            .finish()
    }
}

pub struct GetCustomHooksTracingRequest<'a>(pub &'a GetCustomHooksRequest);

impl Debug for GetCustomHooksTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("GetCustomHooks")
            .field("repository", &self.0.repository)
            .finish()
    }
}

pub struct FetchBundleTracingRequest<'a>(pub &'a FetchBundleRequest);

impl Debug for FetchBundleTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FetchBundle")
            .field("repository", &self.0.repository)
            .field("data_len", &self.0.data.len())
            .field("update_head", &self.0.update_head)
            .finish()
    }
}

pub struct SetCustomHooksTracingRequest<'a>(pub &'a SetCustomHooksRequest);

impl Debug for SetCustomHooksTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SetCustomHooks")
            .field("repository", &self.0.repository)
            .field("data_len", &self.0.data.len())
            .finish()
    }
}
