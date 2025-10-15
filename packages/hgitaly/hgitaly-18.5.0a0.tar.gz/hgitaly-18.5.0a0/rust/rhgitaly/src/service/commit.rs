// Copyright 2023-2025 Georges Racinet <georges.racinet@cloudcrane.io>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::fmt::{Debug, Formatter};
use std::path::Path;
use std::sync::Arc;

use tonic::{
    codegen::BoxStream,
    metadata::{Ascii, MetadataMap, MetadataValue},
    Request, Response, Status, Streaming,
};
use tracing::{info, instrument};

use hg::errors::HgError;
use hg::revlog::changelog::Changelog;
use hg::revlog::{GraphError, NodePrefix, RevlogError, NULL_REVISION};

use crate::config::Config;
use crate::errors::unimplemented_with_issue;
use crate::gitaly::commit_service_client::CommitServiceClient;
use crate::gitaly::commit_service_server::{CommitService, CommitServiceServer};
use crate::gitaly::{
    list_commits_by_ref_name_response, CheckObjectsExistRequest, CheckObjectsExistResponse,
    CommitIsAncestorRequest, CommitIsAncestorResponse, CommitLanguagesRequest,
    CommitLanguagesResponse, CommitStatsRequest, CommitStatsResponse, CommitsByMessageRequest,
    CommitsByMessageResponse, CountCommitsRequest, CountCommitsResponse,
    CountDivergingCommitsRequest, CountDivergingCommitsResponse, FilterShasWithSignaturesRequest,
    FilterShasWithSignaturesResponse, FindAllCommitsRequest, FindAllCommitsResponse,
    FindCommitRequest, FindCommitResponse, FindCommitsRequest, FindCommitsResponse,
    GetCommitMessagesRequest, GetCommitMessagesResponse, GetCommitSignaturesRequest,
    GetCommitSignaturesResponse, GetTreeEntriesRequest, GetTreeEntriesResponse,
    LastCommitForPathRequest, LastCommitForPathResponse, ListCommitsByOidRequest,
    ListCommitsByOidResponse, ListCommitsByRefNameRequest, ListCommitsByRefNameResponse,
    ListCommitsRequest, ListCommitsResponse, ListFilesRequest, ListFilesResponse,
    ListLastCommitsForTreeRequest, ListLastCommitsForTreeResponse, RawBlameRequest,
    RawBlameResponse, Repository, TreeEntryRequest, TreeEntryResponse,
};
use crate::gitlab::revision::{
    blocking_gitlab_revision_node_prefix, gitlab_revision_node_prefix, RefOrRevlogError,
};
use crate::message;
use crate::metadata::{correlation_id, fallback_if_feature_disabled};
use crate::repository::{
    default_repo_spec_error_status, load_changelog_and_stream, load_changelog_and_then,
    repo_store_vfs, RequestWithRepo,
};
use crate::sidecar;
use crate::streaming::ResultResponseStream;
use crate::util::{bytes_strings_as_str, tracing_span_id};
use crate::workdir::with_workdir;

mod commit_languages;
mod find_commits;
mod get_tree_entries;
mod last_commits;
mod raw_blame;
mod tree_entry;

#[derive(Debug)]
pub struct CommitServiceImpl {
    config: Arc<Config>,
    sidecar_servers: Arc<sidecar::Servers>,
}

const COMMITS_CHUNK_SIZE: usize = 50;

/// Return the [`ListCommitsByOidResponse`] for a chunk of oids (changeset ids)
///
/// Behaving like Gitaly imposes that
/// - oids that cannot be found in the repository are ignored. This is actually one of the
///   use cases for the `ListCommitsByOid` call: it can be called indiscriminately with anything
///   that looks like a hash, in particular from Markdown renderings
/// - oids that are not even hexadecimal are ignored, too. This is possibly coincidental.
///
/// [`RevlogError`] is returned in cases of repository corruption.
fn commits_by_oid_chunk(
    cl: &Changelog,
    oids: &[String],
) -> Result<ListCommitsByOidResponse, RevlogError> {
    // Not using Vec::with_capacity(oids.len()), because clients will often call this with a single
    // argument, precisely to know whether it is a commit id prefix in this repo (happens a lot
    // in Markdown rendering), and this will result in needless allocations.
    let mut commits = Vec::new();
    for oid in oids {
        match NodePrefix::from_hex(oid) {
            Err(_) => {
                continue; // non-hexadecimal values for oid are just ignored by Gitaly
            }
            Ok(node_pref) => match cl.rev_from_node(node_pref) {
                Ok(NULL_REVISION) => (),
                Ok(rev) => commits.push(message::commit(cl.entry_for_unchecked_rev(rev.into())?)?),
                Err(RevlogError::InvalidRevision(_)) => (),
                Err(e) => {
                    return Err(e);
                }
            },
        }
    }
    Ok(ListCommitsByOidResponse { commits })
}

fn commits_by_ref_name_chunk(
    store_vfs: &Path,
    cl: &Changelog,
    ref_names: &[Vec<u8>],
) -> Result<ListCommitsByRefNameResponse, RefOrRevlogError> {
    let mut commit_refs = Vec::with_capacity(ref_names.len());
    for ref_name in ref_names {
        match blocking_gitlab_revision_node_prefix(store_vfs, ref_name) {
            Ok(Some(np)) => {
                let rev = cl.rev_from_node(np)?;
                commit_refs.push(list_commits_by_ref_name_response::CommitForRef {
                    commit: Some(message::commit(cl.entry_for_unchecked_rev(rev.into())?)?),
                    ref_name: ref_name.clone(),
                });
            }
            Ok(None) => {}
            Err(e) => {
                return Err(e.into());
            }
        }
    }
    Ok(ListCommitsByRefNameResponse { commit_refs })
}

fn not_found_for_path(_path: &[u8]) -> Status {
    Status::not_found("tree entry not found")
}

impl RequestWithRepo for CountCommitsRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestWithRepo for ListCommitsByOidRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestWithRepo for ListCommitsByRefNameRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestWithRepo for FindCommitRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

#[tonic::async_trait]
impl CommitService for CommitServiceImpl {
    async fn commit_is_ancestor(
        &self,
        request: Request<CommitIsAncestorRequest>,
    ) -> Result<Response<CommitIsAncestorResponse>, Status> {
        sidecar::unary!(self, request, CommitServiceClient, commit_is_ancestor)
    }

    async fn list_commits_by_oid(
        &self,
        request: Request<ListCommitsByOidRequest>,
    ) -> Result<Response<BoxStream<ListCommitsByOidResponse>>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_list_commits_by_oid(inner, correlation_id(&metadata))
            .await
    }

    async fn list_commits_by_ref_name(
        &self,
        request: Request<ListCommitsByRefNameRequest>,
    ) -> Result<Response<BoxStream<ListCommitsByRefNameResponse>>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_list_commits_by_ref_name(inner, correlation_id(&metadata))
            .await
    }

    async fn find_commits(
        &self,
        request: Request<FindCommitsRequest>,
    ) -> Result<Response<BoxStream<FindCommitsResponse>>, Status> {
        sidecar::fallback_server_streaming!(
            self,
            inner_find_commits,
            request,
            CommitServiceClient,
            find_commits
        )
    }

    async fn commit_languages(
        &self,
        request: Request<CommitLanguagesRequest>,
    ) -> Result<Response<CommitLanguagesResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_commit_languages(inner, correlation_id(&metadata), &metadata)
            .await
    }

    async fn last_commit_for_path(
        &self,
        request: Request<LastCommitForPathRequest>,
    ) -> Result<Response<LastCommitForPathResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_last_commit_for_path(inner, correlation_id(&metadata))
            .await
    }

    async fn list_last_commits_for_tree(
        &self,
        request: Request<ListLastCommitsForTreeRequest>,
    ) -> Result<Response<BoxStream<ListLastCommitsForTreeResponse>>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_list_last_commits_for_tree(inner, correlation_id(&metadata))
            .await
    }

    async fn find_commit(
        &self,
        request: Request<FindCommitRequest>,
    ) -> Result<Response<FindCommitResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_commit(inner, correlation_id(&metadata))
            .await
    }

    async fn tree_entry(
        &self,
        request: Request<TreeEntryRequest>,
    ) -> Result<Response<BoxStream<TreeEntryResponse>>, Status> {
        sidecar::fallback_server_streaming!(
            self,
            inner_tree_entry,
            request,
            CommitServiceClient,
            tree_entry
        )
    }

    async fn count_commits(
        &self,
        request: Request<CountCommitsRequest>,
    ) -> Result<Response<CountCommitsResponse>, Status> {
        sidecar::fallback_unary!(
            self,
            inner_count_commits,
            request,
            CommitServiceClient,
            count_commits
        )
    }

    async fn count_diverging_commits(
        &self,
        request: Request<CountDivergingCommitsRequest>,
    ) -> Result<Response<CountDivergingCommitsResponse>, Status> {
        sidecar::unary!(self, request, CommitServiceClient, count_diverging_commits)
    }

    async fn get_tree_entries(
        &self,
        request: Request<GetTreeEntriesRequest>,
    ) -> Result<Response<BoxStream<GetTreeEntriesResponse>>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_get_tree_entries(inner, correlation_id(&metadata))
            .await
    }

    async fn list_files(
        &self,
        request: Request<ListFilesRequest>,
    ) -> Result<Response<BoxStream<ListFilesResponse>>, Status> {
        sidecar::server_streaming!(self, request, CommitServiceClient, list_files)
    }

    async fn commit_stats(
        &self,
        request: Request<CommitStatsRequest>,
    ) -> Result<Response<CommitStatsResponse>, Status> {
        sidecar::unary!(self, request, CommitServiceClient, commit_stats)
    }

    async fn find_all_commits(
        &self,
        request: Request<FindAllCommitsRequest>,
    ) -> Result<Response<BoxStream<FindAllCommitsResponse>>, Status> {
        sidecar::server_streaming!(self, request, CommitServiceClient, find_all_commits)
    }

    async fn raw_blame(
        &self,
        request: Request<RawBlameRequest>,
    ) -> ResultResponseStream<RawBlameResponse> {
        sidecar::fallback_server_streaming!(
            self,
            inner_raw_blame,
            request,
            CommitServiceClient,
            raw_blame
        )
    }

    async fn commits_by_message(
        &self,
        request: Request<CommitsByMessageRequest>,
    ) -> Result<Response<BoxStream<CommitsByMessageResponse>>, Status> {
        sidecar::server_streaming!(self, request, CommitServiceClient, commits_by_message)
    }

    async fn check_objects_exist(
        &self,
        _request: Request<Streaming<CheckObjectsExistRequest>>,
    ) -> Result<Response<BoxStream<CheckObjectsExistResponse>>, Status> {
        Err(unimplemented_with_issue(101))
    }

    async fn list_commits(
        &self,
        request: Request<ListCommitsRequest>,
    ) -> Result<Response<BoxStream<ListCommitsResponse>>, Status> {
        sidecar::server_streaming!(self, request, CommitServiceClient, list_commits)
    }

    async fn filter_shas_with_signatures(
        &self,
        _request: Request<Streaming<FilterShasWithSignaturesRequest>>,
    ) -> Result<Response<BoxStream<FilterShasWithSignaturesResponse>>, Status> {
        Err(unimplemented_with_issue(24))
    }

    async fn get_commit_signatures(
        &self,
        _request: Request<GetCommitSignaturesRequest>,
    ) -> Result<Response<BoxStream<GetCommitSignaturesResponse>>, Status> {
        Err(unimplemented_with_issue(24))
    }

    async fn get_commit_messages(
        &self,
        request: Request<GetCommitMessagesRequest>,
    ) -> Result<Response<BoxStream<GetCommitMessagesResponse>>, Status> {
        sidecar::server_streaming!(self, request, CommitServiceClient, get_commit_messages)
    }
}

struct ListCommitsByOidTracingRequest<'a>(&'a ListCommitsByOidRequest);

impl Debug for ListCommitsByOidTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("LisCommitsByOidRequest")
            .field("repository", &self.0.repository)
            .field("oid", &self.0.oid)
            .finish()
    }
}

struct FindCommitTracingRequest<'a>(&'a FindCommitRequest);

impl Debug for FindCommitTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FindCommitRequest")
            .field("repository", &self.0.repository)
            .field("revision", &String::from_utf8_lossy(&self.0.revision))
            .finish()
    }
}

struct ListCommitsByRefNameTracingRequest<'a>(&'a ListCommitsByRefNameRequest);

impl Debug for ListCommitsByRefNameTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ListCommitsByRefNameRequest")
            .field("repository", &self.0.repository)
            .field("ref_names", &bytes_strings_as_str(&self.0.ref_names))
            .finish()
    }
}

/// Convert a GraphError to RevlogError
///
/// Talk upstream about this. When both are intertwined, it is painful not to have the
/// `From<GraphError>` implementation.
fn revlog_err_from_graph_err(err: GraphError) -> HgError {
    HgError::corrupted(format!("{:?}", err))
}

impl CommitServiceImpl {
    #[instrument(name = "tree_entry", skip(self, request, _metadata), fields(span_id))]
    async fn inner_tree_entry(
        &self,
        request: &TreeEntryRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        _metadata: &MetadataMap,
    ) -> ResultResponseStream<TreeEntryResponse> {
        tracing_span_id!();
        tree_entry::inner_impl(&self.config, request).await
    }

    #[instrument(
        name = "count_commits",
        skip(self, request, _metadata),
        fields(span_id)
    )]
    async fn inner_count_commits(
        &self,
        request: &CountCommitsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        _metadata: &MetadataMap,
    ) -> Result<Response<CountCommitsResponse>, Status> {
        if request.revision.is_empty() && !request.all {
            // minimal case to prove that fallback works
            Err(Status::invalid_argument("empty Revision and false All"))
        } else {
            Err(Status::unimplemented("soon"))
        }
    }

    #[instrument(name = "get_tree_entries", skip(self, request), fields(span_id))]
    async fn inner_get_tree_entries(
        &self,
        request: GetTreeEntriesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<GetTreeEntriesResponse> {
        tracing_span_id!();
        get_tree_entries::inner_impl(&self.config, request).await
    }

    #[instrument(name = "raw_blame", skip(self, request, metadata), fields(span_id))]
    async fn inner_raw_blame(
        &self,
        request: &RawBlameRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> ResultResponseStream<RawBlameResponse> {
        tracing_span_id!();
        fallback_if_feature_disabled(metadata, "rhgitaly-raw-blame", false)?;
        raw_blame::inner_impl(&self.config, request).await
    }

    #[instrument(name = "list_commits_by_oid", skip(self, request), fields(span_id))]
    async fn inner_list_commits_by_oid(
        &self,
        request: ListCommitsByOidRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<ListCommitsByOidResponse> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            ListCommitsByOidTracingRequest(&request)
        );

        load_changelog_and_stream(
            self.config.clone(),
            request,
            default_repo_spec_error_status,
            move |req, _repo, cl, tx| {
                for oid_chunk in req.oid.chunks(COMMITS_CHUNK_SIZE) {
                    match commits_by_oid_chunk(cl, oid_chunk) {
                        Ok(resp) => {
                            if !resp.commits.is_empty() {
                                tx.send(Ok(resp));
                            }
                        }
                        Err(e) => tx.send(Err(Status::internal(format!(
                            "Repository corruption {:?}",
                            e
                        )))),
                    }
                }
            },
        )
    }

    #[instrument(
        name = "list_commits_by_ref_name",
        skip(self, request),
        fields(span_id)
    )]
    async fn inner_list_commits_by_ref_name(
        &self,
        request: ListCommitsByRefNameRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<ListCommitsByRefNameResponse> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            ListCommitsByRefNameTracingRequest(&request)
        );

        let config = self.config.clone();
        let store_vfs = repo_store_vfs(&config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        load_changelog_and_stream(
            self.config.clone(),
            request,
            default_repo_spec_error_status,
            move |req, _repo, cl, tx| {
                for ref_chunk in req.ref_names.chunks(COMMITS_CHUNK_SIZE) {
                    match commits_by_ref_name_chunk(&store_vfs, cl, ref_chunk) {
                        Ok(resp) => {
                            if !resp.commit_refs.is_empty() {
                                tx.send(Ok(resp));
                            }
                        }
                        Err(e) => tx.send(Err(Status::internal(format!(
                            "Repository corruption {:?}",
                            e
                        )))),
                    }
                }
            },
        )
    }

    #[instrument(name = "find_commits", skip(self, request, _metadata), fields(span_id))]
    async fn inner_find_commits(
        &self,
        request: &FindCommitsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        _metadata: &MetadataMap,
    ) -> ResultResponseStream<FindCommitsResponse> {
        tracing_span_id!();
        find_commits::inner_impl(&self.config, request).await
    }

    #[instrument(
        name = "commit_languages",
        skip(self, request, metadata),
        fields(span_id)
    )]
    async fn inner_commit_languages(
        &self,
        request: CommitLanguagesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<CommitLanguagesResponse>, Status> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            commit_languages::CommitLanguagesTracingRequest(&request)
        );
        let rev: &[u8] = if request.revision.is_empty() {
            b"HEAD"
        } else {
            &request.revision
        };

        with_workdir(
            &self.config,
            request.repository.as_ref().unwrap(), // TODO unwrap
            rev,
            &self.sidecar_servers,
            metadata,
            |path| tokio::task::spawn_blocking(move || commit_languages::at_path(&path)),
        )
        .await
    }

    #[instrument(name = "last_commit_for_path", skip(self, request), fields(span_id))]
    async fn inner_last_commit_for_path(
        &self,
        request: LastCommitForPathRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<LastCommitForPathResponse>, Status> {
        tracing_span_id!();
        last_commits::one_for_path(&self.config, request).await
    }

    #[instrument(
        name = "list_last_commits_for_tree",
        skip(self, request),
        fields(span_id)
    )]
    async fn inner_list_last_commits_for_tree(
        &self,
        request: ListLastCommitsForTreeRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<BoxStream<ListLastCommitsForTreeResponse>>, Status> {
        tracing_span_id!();
        last_commits::several_for_tree(&self.config, request).await
    }

    #[instrument(name = "find_commit", skip(self, request), fields(span_id))]
    async fn inner_find_commit(
        &self,
        request: FindCommitRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<Response<FindCommitResponse>, Status> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            FindCommitTracingRequest(&request)
        );
        if request.revision.is_empty() {
            return Err(Status::invalid_argument("empty revision"));
        }

        let config = self.config.clone();
        let store_vfs = repo_store_vfs(&config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        match gitlab_revision_node_prefix(&store_vfs, &request.revision)
            .await
            .map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))?
        {
            None => {
                info!("Revision not resolved");
                Ok(Response::new(FindCommitResponse::default()))
            }
            Some(node_prefix) => {
                info!("Revision resolved as {:x}", &node_prefix);
                let commit = load_changelog_and_then(
                    self.config.clone(),
                    request,
                    default_repo_spec_error_status,
                    move |_req, _repo, cl| {
                        message::commit_for_node_prefix_or_none(cl, node_prefix)
                            .map_err(|e| Status::internal(format!("Repository corruption {:?}", e)))
                    },
                )
                .await?;

                Ok(Response::new(FindCommitResponse { commit }))
            }
        }
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn commit_server(
    config: &Arc<Config>,
    sidecar_servers: &Arc<sidecar::Servers>,
) -> CommitServiceServer<CommitServiceImpl> {
    CommitServiceServer::new(CommitServiceImpl {
        config: config.clone(),
        sidecar_servers: sidecar_servers.clone(),
    })
}
