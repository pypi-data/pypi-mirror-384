use std::fmt::{Debug, Formatter};
use std::iter::Iterator;
use std::sync::Arc;

use prost;
use tonic::{Code, Status};
use tracing::info;

use hg::errors::HgError;
use hg::repo::Repo;
use hg::revlog::changelog::Changelog;
use hg::revlog::NodePrefix;

use super::not_found_for_path;
use crate::config::Config;
use crate::errors::{
    status_with_structured_error, FromPathError, FromResolveRevisionError, PathErrorType,
};
use crate::gitaly::{
    get_tree_entries_error, get_tree_entries_request::SortBy, tree_entry::EntryType,
    GetTreeEntriesError, GetTreeEntriesRequest, GetTreeEntriesResponse, PaginationParameter,
    PathError, Repository, ResolveRevisionError, TreeEntry,
};
use crate::gitlab::revision::gitlab_revision_node_prefix;
use crate::mercurial::{
    changelog_entry_manifest, ls_path, DirIteratorWithFlatPaths, DirIteratorWithoutFlatPaths,
    PathContent, RecursiveDirIterator,
};
use crate::repository::{
    default_repo_spec_error_status, load_changelog_and_stream, repo_store_vfs, RequestWithRepo,
};
use crate::streaming::{
    empty_response_stream, stream_with_pagination, BlockingResponseSender, PaginableMessageItem,
    ResultResponseStream,
};

impl PaginableMessageItem for TreeEntry {
    fn match_token(&self, token: &str) -> bool {
        self.oid == token
    }

    fn next_cursor(&self) -> String {
        self.oid.clone()
    }
}

struct GetTreeEntriesTracingRequest<'a>(&'a GetTreeEntriesRequest);

impl Debug for GetTreeEntriesTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("GetTreeEntriesRequest")
            .field("repository", &self.0.repository)
            .field("revision", &String::from_utf8_lossy(&self.0.revision))
            .field("path", &String::from_utf8_lossy(&self.0.path))
            .field("recursive", &self.0.recursive)
            .field("sort", &self.0.sort)
            .field("pagination_params", &self.0.pagination_params)
            .field("skip_flat_paths", &self.0.skip_flat_paths)
            .finish()
    }
}

impl RequestWithRepo for GetTreeEntriesRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl prost::Name for GetTreeEntriesError {
    const NAME: &'static str = "GetTreeEntriesError";
    const PACKAGE: &'static str = "gitaly";
}

impl FromPathError for GetTreeEntriesError {
    fn from_path_error(err: PathError) -> Self {
        GetTreeEntriesError {
            error: Some(get_tree_entries_error::Error::Path(err)),
        }
    }
}

impl FromResolveRevisionError for GetTreeEntriesError {
    fn from_resolve_revision_error(err: ResolveRevisionError) -> Self {
        GetTreeEntriesError {
            error: Some(get_tree_entries_error::Error::ResolveTree(err)),
        }
    }
}

fn stream_get_tree_entries(
    req: GetTreeEntriesRequest,
    repo: &Repo,
    changelog: &Changelog,
    node_prefix: NodePrefix,
    tx: &BlockingResponseSender<GetTreeEntriesResponse>,
) -> Result<(), Status> {
    let manifestlog = repo
        .manifestlog()
        .map_err(|e| Status::internal(format!("Error getting manifestlog: {:?}", e)))?;
    let (cs_node, manifest) = changelog_entry_manifest(changelog, &manifestlog, node_prefix)
        .map_err(|e| Status::internal(format!("Error obtaining manifest: {:?}", e)))?
        .ok_or_else(|| not_found_for_path(&req.path))?;

    let mut pl = req.path.len();
    while pl > 0 && req.path[pl - 1] == b'/' {
        pl -= 1;
    }
    if pl == 1 && req.path[0] == b'.' {
        pl = 0
    };
    let trimmed = &req.path[0..pl];

    let commit_oid = String::from_utf8_lossy(&req.revision).to_string();

    let non_empty_tree = if req.recursive {
        stream_get_tree_entries_from_iterator(
            tx,
            &req,
            RecursiveDirIterator::new(commit_oid, cs_node, manifest.iter(), trimmed),
        )
    } else if req.skip_flat_paths {
        stream_get_tree_entries_from_iterator(
            tx,
            &req,
            DirIteratorWithoutFlatPaths::new(commit_oid, cs_node, manifest.iter(), trimmed),
        )
    } else {
        stream_get_tree_entries_from_iterator(
            tx,
            &req,
            DirIteratorWithFlatPaths::new(commit_oid, cs_node, manifest.iter(), trimmed),
        )
    };
    if !non_empty_tree {
        // There is no such thing as an empty Mercurial directory
        // this is potentially long and unnecessary in almost all requests,
        // this is why we are doing it only if the iterator ends up being
        // empty.
        return match ls_path(&manifest, trimmed) {
            Ok(PathContent::File(_)) => Err(status_with_structured_error(
                Code::InvalidArgument,
                "path not treeish",
                GetTreeEntriesError::resolve_revision_error(req.revision.clone()),
            )),
            Ok(PathContent::NotFound) => {
                let code = if req.recursive {
                    Code::NotFound
                } else {
                    Code::InvalidArgument
                };
                Err(status_with_structured_error(
                    code,
                    "invalid revision or path",
                    GetTreeEntriesError::resolve_revision_error(req.revision.clone()),
                ))
            }
            Ok(PathContent::Directory(_)) => Err(Status::internal(
                "Empty GetTreeEntries iteration, but contradiction when analyzing \
                 for error return",
            )),
            Err(e) => Err(Status::internal(format!(
                "Empty GetTreeEntries iteration and further error when analyzing \
                 for error return: {:?}",
                e
            ))),
        };
    }
    Ok(())
}

/// Stream `GetTreeEntries` responses, using the inner iterator.
///
/// Various options (e.g., `recursive`) give rise to different types of iterators on entries.
/// This function applies the sort and pagination parameters, final chunking and streams responses
/// to the channel.
fn stream_get_tree_entries_from_iterator<It>(
    tx: &BlockingResponseSender<GetTreeEntriesResponse>,
    request: &GetTreeEntriesRequest,
    iterator: It,
) -> bool
where
    It: Iterator<Item = Result<TreeEntry, HgError>>,
{
    let pagination = &request.pagination_params;
    if request.sort == SortBy::TreesFirst as i32 {
        let mut trees = Vec::new();
        let mut blobs = Vec::new();
        for res in iterator {
            match res {
                Ok(ent) => {
                    if ent.r#type == EntryType::Tree as i32 {
                        trees.push(Ok(ent));
                    } else if ent.r#type == EntryType::Blob as i32 {
                        blobs.push(Ok(ent));
                    }
                }
                // arbitrary choice, weakly motivated by errors being more likely with blobs
                // than with trees at this point.
                err => blobs.push(err),
            }
        }
        stream_get_tree_entries_paginated(tx, pagination, trees.into_iter().chain(blobs))
    } else {
        stream_get_tree_entries_paginated(tx, pagination, iterator)
    }
}

/// Stream [`GetTreeEntriesResponse`] messages with pagination
///
/// This function takes care of the offset and limit logic enclosed into the given pagination
/// parameter, regrouping the `TreeEntry` elements yielded by the iterator into suitable chunks,
/// and providing the `next_cursor` value, but does not take care of ordering.
/// Instead it expects the incoming iiterator to be already properly ordered.
fn stream_get_tree_entries_paginated<It>(
    tx: &BlockingResponseSender<GetTreeEntriesResponse>,
    pagination: &Option<PaginationParameter>,
    iterator: It,
) -> bool
where
    It: Iterator<Item = Result<TreeEntry, HgError>>,
{
    stream_with_pagination(
        tx,
        pagination,
        iterator,
        |entries, pagination_cursor| GetTreeEntriesResponse {
            entries,
            pagination_cursor,
        },
        |err| Status::internal(format!("error reading manifest: #{:?}", err)),
        |token| Status::internal(format!("could not find starting OID: {}", token)),
    )
}

pub async fn inner_impl(
    config: &Arc<Config>,
    request: GetTreeEntriesRequest,
) -> ResultResponseStream<GetTreeEntriesResponse> {
    info!(
        "Processing, request={:?}",
        GetTreeEntriesTracingRequest(&request)
    );

    if request.revision.is_empty() {
        return Err(Status::invalid_argument("empty revision"));
    }

    if request.path.is_empty() {
        return Err(status_with_structured_error(
            Code::InvalidArgument,
            "empty path",
            GetTreeEntriesError::path_error(request.path, PathErrorType::EmptyPath),
        ));
    }

    let config = config.clone();
    let store_vfs = repo_store_vfs(&config, &request.repository)
        .await
        .map_err(default_repo_spec_error_status)?;

    match gitlab_revision_node_prefix(&store_vfs, &request.revision)
        .await
        .map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))?
    {
        None => Err(status_with_structured_error(
            Code::InvalidArgument,
            "invalid revision or path",
            GetTreeEntriesError::resolve_revision_error(request.revision.clone()),
        )),
        Some(node_prefix) => {
            info!("Revision resolved as {:x}", &node_prefix);

            if request.pagination_params.as_ref().map(|p| p.limit) == Some(0) {
                // let's not even load the repo (see Gitaly Comparison tests,
                // no error case either)
                return empty_response_stream();
            }

            load_changelog_and_stream(
                config.clone(),
                request,
                default_repo_spec_error_status,
                move |req, repo, cl, tx| {
                    if let Err(e) = stream_get_tree_entries(req, repo, cl, node_prefix, &tx) {
                        tx.send(Err(e));
                    }
                },
            )
        }
    }
}
