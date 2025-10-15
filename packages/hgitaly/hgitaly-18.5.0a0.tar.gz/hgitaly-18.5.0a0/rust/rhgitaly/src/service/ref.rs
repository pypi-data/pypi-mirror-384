// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::fmt::{Debug, Formatter};
use std::string::String;
use std::sync::Arc;

use tokio_stream::StreamExt;

use tonic::{
    metadata::{Ascii, MetadataValue},
    Code, Request, Response, Status, Streaming,
};
use tracing::{info, instrument};

use crate::config::Config;
use crate::errors::{
    status_with_structured_error, unimplemented_with_issue, FromReferenceNotFoundError,
};
use crate::gitaly::ref_service_client::RefServiceClient;
use crate::gitaly::ref_service_server::{RefService, RefServiceServer};
use crate::gitaly::{
    find_tag_error, Branch, DeleteRefsRequest, DeleteRefsResponse, FindAllBranchesRequest,
    FindAllBranchesResponse, FindAllRemoteBranchesRequest, FindAllRemoteBranchesResponse,
    FindAllTagsRequest, FindAllTagsResponse, FindBranchRequest, FindBranchResponse,
    FindDefaultBranchNameRequest, FindDefaultBranchNameResponse, FindLocalBranchesRequest,
    FindLocalBranchesResponse, FindRefsByOidRequest, FindRefsByOidResponse, FindTagError,
    FindTagRequest, FindTagResponse, GetTagMessagesRequest, GetTagMessagesResponse,
    GetTagSignaturesRequest, GetTagSignaturesResponse, ListBranchNamesContainingCommitRequest,
    ListBranchNamesContainingCommitResponse, ListRefsRequest, ListRefsResponse,
    ListTagNamesContainingCommitRequest, ListTagNamesContainingCommitResponse, RefExistsRequest,
    RefExistsResponse, ReferenceNotFoundError, Repository, Tag, UpdateReferencesRequest,
    UpdateReferencesResponse,
};
use crate::gitlab::revision::{existing_default_gitlab_branch, map_full_ref, RefError};
use crate::gitlab::state::{lookup_typed_ref_as_node, stream_gitlab_branches, stream_gitlab_tags};
use crate::gitlab::{gitlab_branch_ref, gitlab_tag_ref};
use crate::message::{self};
use crate::metadata::correlation_id;
use crate::repository::{aux_git_to_main_hg, default_repo_spec_error_status, repo_store_vfs};
use crate::repository::{load_changelog_and_then, RequestWithRepo};
use crate::sidecar;
use crate::streaming::ResultResponseStream;
use crate::util::tracing_span_id;

mod find_many;
mod list;

#[derive(Debug)]
pub struct RefServiceImpl {
    config: Arc<Config>,
    sidecar_servers: Arc<sidecar::Servers>,
}

impl RequestWithRepo for FindTagRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestWithRepo for FindBranchRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestWithRepo for FindDefaultBranchNameRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestWithRepo for ListRefsRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl FromReferenceNotFoundError for FindTagError {
    fn from_reference_not_found_error(err: ReferenceNotFoundError) -> Self {
        FindTagError {
            error: Some(find_tag_error::Error::TagNotFound(err)),
        }
    }
}

#[tonic::async_trait]
impl RefService for RefServiceImpl {
    async fn find_default_branch_name(
        &self,
        request: Request<FindDefaultBranchNameRequest>,
    ) -> Result<Response<FindDefaultBranchNameResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_default_branch_name(inner, correlation_id(&metadata))
            .await
    }

    async fn find_local_branches(
        &self,
        request: Request<FindLocalBranchesRequest>,
    ) -> ResultResponseStream<FindLocalBranchesResponse> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_local_branches(inner, correlation_id(&metadata))
            .await
    }

    async fn find_all_branches(
        &self,
        request: Request<FindAllBranchesRequest>,
    ) -> ResultResponseStream<FindAllBranchesResponse> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_all_branches(inner, correlation_id(&metadata))
            .await
    }

    async fn find_all_tags(
        &self,
        request: Request<FindAllTagsRequest>,
    ) -> ResultResponseStream<FindAllTagsResponse> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_all_tags(inner, correlation_id(&metadata))
            .await
    }

    async fn find_tag(
        &self,
        request: Request<FindTagRequest>,
    ) -> Result<Response<FindTagResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_tag(inner, correlation_id(&metadata)).await
    }

    async fn find_all_remote_branches(
        &self,
        request: Request<FindAllRemoteBranchesRequest>,
    ) -> ResultResponseStream<FindAllRemoteBranchesResponse> {
        sidecar::server_streaming!(self, request, RefServiceClient, find_all_remote_branches)
    }

    async fn ref_exists(
        &self,
        request: Request<RefExistsRequest>,
    ) -> Result<Response<RefExistsResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_ref_exists(inner, correlation_id(&metadata))
            .await
    }

    async fn find_branch(
        &self,
        request: Request<FindBranchRequest>,
    ) -> Result<Response<FindBranchResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_branch(inner, correlation_id(&metadata))
            .await
    }

    #[instrument(name = "update_references", skip(self, request))]
    async fn update_references(
        &self,
        request: Request<Streaming<UpdateReferencesRequest>>,
    ) -> Result<Response<UpdateReferencesResponse>, Status> {
        sidecar::client_streaming!(self, request, RefServiceClient, update_references)
    }

    async fn delete_refs(
        &self,
        request: Request<DeleteRefsRequest>,
    ) -> Result<Response<DeleteRefsResponse>, Status> {
        sidecar::unary!(self, request, RefServiceClient, delete_refs)
    }

    async fn list_branch_names_containing_commit(
        &self,
        request: Request<ListBranchNamesContainingCommitRequest>,
    ) -> ResultResponseStream<ListBranchNamesContainingCommitResponse> {
        sidecar::server_streaming!(
            self,
            request,
            RefServiceClient,
            list_branch_names_containing_commit
        )
    }

    async fn list_tag_names_containing_commit(
        &self,
        request: Request<ListTagNamesContainingCommitRequest>,
    ) -> ResultResponseStream<ListTagNamesContainingCommitResponse> {
        sidecar::server_streaming!(
            self,
            request,
            RefServiceClient,
            list_tag_names_containing_commit
        )
    }

    async fn get_tag_signatures(
        &self,
        _request: Request<GetTagSignaturesRequest>,
    ) -> ResultResponseStream<GetTagSignaturesResponse> {
        Err(unimplemented_with_issue(75))
    }

    async fn get_tag_messages(
        &self,
        request: Request<GetTagMessagesRequest>,
    ) -> ResultResponseStream<GetTagMessagesResponse> {
        sidecar::server_streaming!(self, request, RefServiceClient, get_tag_messages)
    }

    async fn list_refs(
        &self,
        request: Request<ListRefsRequest>,
    ) -> ResultResponseStream<ListRefsResponse> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_list_refs(inner, correlation_id(&metadata)).await
    }

    async fn find_refs_by_oid(
        &self,
        request: Request<FindRefsByOidRequest>,
    ) -> Result<Response<FindRefsByOidResponse>, Status> {
        sidecar::unary!(self, request, RefServiceClient, find_refs_by_oid)
    }
}

struct RefExistsTracingRequest<'a>(&'a RefExistsRequest);

impl Debug for RefExistsTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("RefExistRequest")
            .field("repository", &self.0.repository)
            .field("ref", &String::from_utf8_lossy(&self.0.r#ref))
            .finish()
    }
}

struct FindBranchTracingRequest<'a>(&'a FindBranchRequest);

impl Debug for FindBranchTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FindBranchRequest")
            .field("repository", &self.0.repository)
            .field("name", &String::from_utf8_lossy(&self.0.name))
            .finish()
    }
}

struct FindTagTracingRequest<'a>(&'a FindTagRequest);

impl Debug for FindTagTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FindTagRequest")
            .field("repository", &self.0.repository)
            .field("tag_name", &String::from_utf8_lossy(&self.0.tag_name))
            .finish()
    }
}

impl prost::Name for FindTagError {
    const NAME: &'static str = "FindTagError";
    const PACKAGE: &'static str = "gitaly";
}

impl RefServiceImpl {
    #[instrument(name = "find_default_branch_name", skip(self, request))]
    async fn inner_find_default_branch_name(
        &self,
        mut request: FindDefaultBranchNameRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<FindDefaultBranchNameResponse>, Status> {
        tracing_span_id!();
        info!("Processing, repository={:?}", &request.repository);

        if let Some(main_hg_path) = aux_git_to_main_hg(&request) {
            let main_hg_path = main_hg_path.to_owned();
            if let Some(repo) = request.repository.as_mut() {
                repo.relative_path = main_hg_path;
            }
        }

        let store_vfs = repo_store_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        Ok(Response::new(FindDefaultBranchNameResponse {
            name: existing_default_gitlab_branch(&store_vfs)
                .await
                .map_err(|e| {
                    Status::internal(format!(
                        "Error reading or checking GitLab default branch: {:?}",
                        e
                    ))
                })?
                .map(|ref name_node| gitlab_branch_ref(&name_node.0))
                .unwrap_or_else(Vec::new),
        }))
    }

    #[instrument(name = "find_local_branches", skip(self, request), fields(span_id))]
    async fn inner_find_local_branches(
        &self,
        request: FindLocalBranchesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<FindLocalBranchesResponse> {
        tracing_span_id!();
        find_many::local_branches(&self.config, &request).await
    }

    #[instrument(name = "find_all_branches", skip(self, request), fields(span_id))]
    async fn inner_find_all_branches(
        &self,
        request: FindAllBranchesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<FindAllBranchesResponse> {
        tracing_span_id!();
        find_many::all_branches(&self.config, &request).await
    }

    #[instrument(name = "find_all_tags", skip(self, request), fields(span_id))]
    async fn inner_find_all_tags(
        &self,
        request: FindAllTagsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<FindAllTagsResponse> {
        tracing_span_id!();
        find_many::all_tags(&self.config, &request).await
    }

    #[instrument(name = "ref_exists", skip(self, request), fields(span_id))]
    async fn inner_ref_exists(
        &self,
        request: RefExistsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<RefExistsResponse>, Status> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            RefExistsTracingRequest(&request)
        );

        let store_vfs = repo_store_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        let value = match map_full_ref(&store_vfs, &request.r#ref, |_tr| (), |_ka| ()).await {
            Ok(()) => Ok(true),
            Err(RefError::NotFound) => Ok(false),
            Err(RefError::MissingRefName) => Ok(false),
            Err(RefError::NotAFullRef) => Err(Status::invalid_argument("invalid refname")),
            Err(RefError::GitLabStateFileError(e)) => Err(Status::internal(format!("{:?}", e))),
        }?;

        Ok(Response::new(RefExistsResponse { value }))
    }

    #[instrument(name = "find_branch", skip(self, request), fields(span_id))]
    async fn inner_find_branch(
        &self,
        request: FindBranchRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<FindBranchResponse>, Status> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            FindBranchTracingRequest(&request)
        );

        let store_vfs = repo_store_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        let branch_name = request.name.clone();
        let commit =
            match lookup_typed_ref_as_node(stream_gitlab_branches(&store_vfs).await?, &branch_name)
                .await
                .map_err(|e| Status::internal(format!("GitLab state file error: {:?}", e)))?
            {
                None => {
                    return Ok(Response::new(FindBranchResponse::default()));
                }
                Some(node) => {
                    // TODO totally duplicated from FindCommit. Find a way to make a helper!
                    load_changelog_and_then(
                        self.config.clone(),
                        request.clone(),
                        default_repo_spec_error_status,
                        move |_req, _repo, cl| {
                            message::commit_for_node_prefix_or_none(cl, node.into()).map_err(|e| {
                                Status::internal(format!("Repository corruption {:?}", e))
                            })
                        },
                    )
                    .await
                }
            }?;

        Ok(Response::new(FindBranchResponse {
            branch: Some(Branch {
                name: branch_name,
                target_commit: commit,
            }),
        }))
    }

    #[instrument(name = "find_tag", skip(self, request), fields(span_id))]
    async fn inner_find_tag(
        &self,
        request: FindTagRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<FindTagResponse>, Status> {
        tracing_span_id!();
        info!("Processing, request={:?}", FindTagTracingRequest(&request));

        let store_vfs = repo_store_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        let tag_name = request.tag_name.clone();
        let commit =
            match lookup_typed_ref_as_node(stream_gitlab_tags(&store_vfs).await?, &tag_name)
                .await
                .map_err(|e| Status::internal(format!("GitLab state file error: {:?}", e)))?
            {
                None => {
                    return Err(status_with_structured_error(
                        Code::NotFound,
                        "tag does not exist",
                        FindTagError::reference_not_found_error(gitlab_tag_ref(&tag_name)),
                    ));
                }
                Some(node) => {
                    // TODO totally duplicated from FindCommit. Find a way to make a helper!
                    load_changelog_and_then(
                        self.config.clone(),
                        request,
                        default_repo_spec_error_status,
                        move |_req, _repo, cl| {
                            message::commit_for_node_prefix_or_none(cl, node.into()).map_err(|e| {
                                Status::internal(format!("Repository corruption {:?}", e))
                            })
                        },
                    )
                    .await
                }
            }?;

        Ok(Response::new(FindTagResponse {
            tag: Some(Tag {
                name: tag_name,
                target_commit: commit,
                ..Default::default()
            }),
        }))
    }

    #[instrument(name = "list_refs", skip(self, request), fields(span_id))]
    async fn inner_list_refs(
        &self,
        request: ListRefsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<ListRefsResponse> {
        tracing_span_id!();
        list::refs(&self.config, request).await
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn ref_server(
    config: &Arc<Config>,
    sidecar_servers: &Arc<sidecar::Servers>,
) -> RefServiceServer<RefServiceImpl> {
    RefServiceServer::new(RefServiceImpl {
        config: config.clone(),
        sidecar_servers: sidecar_servers.clone(),
    })
}
