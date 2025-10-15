use std::fmt::{Debug, Formatter};
use std::sync::Arc;

use tonic::Status;
use tracing::info;

use hg::repo::Repo;
use hg::revlog::changelog::Changelog;
use hg::revlog::NodePrefix;
use hg::utils::hg_path::HgPath;

use super::not_found_for_path;
use crate::config::Config;
use crate::git::{self};
use crate::gitaly::{
    tree_entry_response::ObjectType, Repository, TreeEntryRequest, TreeEntryResponse,
};
use crate::gitlab::revision::gitlab_revision_node_prefix;
use crate::mercurial::{changelog_entry_manifest, ls_path, read_blob, PathContent};
use crate::oid::tree_oid;
use crate::repository::{
    default_repo_spec_error_status, load_changelog_and_stream, repo_store_vfs,
    unimplemented_if_largefiles, RequestWithRepo,
};
use crate::service::blob::stream_blob;
use crate::streaming::{BlockingResponseSender, ResultResponseStream};

struct TreeEntryTracingRequest<'a>(&'a TreeEntryRequest);

impl Debug for TreeEntryTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("TreeEntryRequest")
            .field("repository", &self.0.repository)
            .field("revision", &String::from_utf8_lossy(&self.0.revision))
            .field("path", &String::from_utf8_lossy(&self.0.path))
            .field("limit", &self.0.limit)
            .field("max_size", &self.0.max_size)
            .finish()
    }
}

impl RequestWithRepo for TreeEntryRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

fn stream_tree_entry(
    req: TreeEntryRequest,
    repo: &Repo,
    changelog: &Changelog,
    node_prefix: NodePrefix,
    tx: &BlockingResponseSender<TreeEntryResponse>,
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
    let trimmed = &req.path[0..pl];

    match ls_path(&manifest, trimmed)
        .map_err(|e| Status::internal(format!("Error reading manifest {:?}", e)))?
    {
        PathContent::File(manifest_entry) => {
            let hg_path = HgPath::new(&req.path);
            let (mut data, metadata) = read_blob(repo, &cs_node, manifest_entry, hg_path)
                .map_err(|e| Status::internal(format!("Error reading file {:?}", e)))?;
            if req.max_size != 0 && metadata.size > req.max_size {
                tx.send(Err(Status::failed_precondition(format!(
                    "object size ({}) is bigger than the maximum allowed size ({})",
                    metadata.size, req.max_size
                ))));
            } else {
                if req.limit > 0 {
                    data.truncate(req.limit as usize);
                }
                stream_blob(tx, data, metadata)
            }
        }
        PathContent::NotFound => {
            return Err(not_found_for_path(&req.path));
        }
        PathContent::Directory(listing) => {
            let mut size: usize = 0;
            // See Python impl for explanation (note that the Rust implementation is using
            // the relative path instead of the absolute path).
            for elt in listing.iter() {
                if elt.is_file() {
                    size += 28
                } else {
                    size += 27
                }
                size += elt.relative_path.len();
            }
            tx.send(Ok(TreeEntryResponse {
                r#type: ObjectType::Tree as i32,
                oid: tree_oid(&cs_node, trimmed),
                mode: git::OBJECT_MODE_TREE,
                size: size as i64,
                ..Default::default()
            }));
        }
    }
    Ok(())
}

pub async fn inner_impl(
    config: &Arc<Config>,
    request: &TreeEntryRequest,
) -> ResultResponseStream<TreeEntryResponse> {
    info!("Processing request={:?}", TreeEntryTracingRequest(request));

    if request.revision.is_empty() {
        return Err(Status::invalid_argument("empty revision"));
    }

    let config = config.clone();
    let store_vfs = repo_store_vfs(&config, &request.repository)
        .await
        .map_err(default_repo_spec_error_status)?;

    unimplemented_if_largefiles(&config, &request.repository).await?;

    match gitlab_revision_node_prefix(&store_vfs, &request.revision)
        .await
        .map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))?
    {
        None => {
            info!("Revision not resolved");
            Err(not_found_for_path(&request.path))
        }
        Some(node_prefix) => {
            info!("Revision resolved as {:x}", &node_prefix);

            load_changelog_and_stream(
                config.clone(),
                request.clone(),
                default_repo_spec_error_status,
                move |req, repo, cl, tx| {
                    if let Err(e) = stream_tree_entry(req, repo, cl, node_prefix, &tx) {
                        tx.send(Err(e));
                    }
                },
            )
        }
    }
}
