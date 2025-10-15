// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later

//! High level support for GitLab revisions.
//!
//! This matches roughly the `hgitaly.revision` Python module.
//!
//! There is no precise definition of revision, it is merely what Gitaly clients
//! can pass legitimately in the various `revision` fields of requests. Often, it is just
//! the subset of of `git log` would accept and treat as a single revision, e.g., by default
//! `main` would be tried first as a tag name, then as a branch name.
//!
//! Refs given in their full path from, e.g., as `refs/heads/tags/v1.2` are valid revisions, hence
//! the helpers to handle them are in particular provided by this module.
use futures::executor::block_on;
use std::path::Path;

use tracing::{info, warn};

use hg::revlog::node::{Node, NodePrefix};
use hg::revlog::RevlogError;

use super::state::{
    get_gitlab_default_branch, has_keep_around, lookup_typed_ref_as_node, map_lookup_typed_ref,
    stream_gitlab_branches, stream_gitlab_special_refs, stream_gitlab_tags, StateFileError,
    TypedRef,
};

#[derive(Debug, derive_more::From)]
pub enum RefError {
    /// Returned to indicate that a full ref path does not start with `refs/`
    NotAFullRef,
    /// Returned to indicate that a given full path starts like a typed ref, yet ends
    /// without the "name" part, as does e.g., `refs/heads`
    MissingRefName,
    /// Returned when a ref is not found for the given repository.
    NotFound,
    #[from]
    /// Errors reading and parsing GitLab state files
    GitLabStateFileError(StateFileError),
}

#[derive(Debug, derive_more::From)]
pub enum RefOrRevlogError {
    #[from]
    Ref(RefError),
    #[from]
    Revlog(RevlogError),
}

/// From GitLab state files in `store_vfs`, resolve a ref and convert using the given closures
///
/// Parameter `ref_path` must be the full ref path, i.e., starting with `refs/`
/// Parameter `map_ka` is used if the ref is found to be a keep-around
/// Parameter `map_ref` is used in other cases
pub async fn map_full_ref<R, MK, MR>(
    store_vfs: &Path,
    ref_path: &[u8],
    map_ref: MR,
    map_ka: MK,
) -> Result<R, RefError>
where
    MK: FnOnce(&[u8]) -> R,
    MR: FnOnce(TypedRef) -> R + Copy,
{
    let mut split = ref_path.splitn(3, |c| *c == b'/');
    if split.next() != Some(b"refs") {
        return Err(RefError::NotAFullRef);
    }

    let ref_type = split
        .next() // `None` happens when `ref_path` is just `"refs"`
        .ok_or(RefError::NotAFullRef)?;

    if ref_type == b"keep-around" {
        let ka = split.next().ok_or(RefError::NotAFullRef)?;
        if has_keep_around(store_vfs, ka).await? {
            return Ok(map_ka(ka));
        }
    }

    let (stream, name_is_next) = match ref_type {
        b"heads" => (stream_gitlab_branches(store_vfs).await?, true),
        b"tags" => (stream_gitlab_tags(store_vfs).await?, true),
        _ => (stream_gitlab_special_refs(store_vfs).await?, false),
    };

    let wanted = if name_is_next {
        split.next().ok_or(RefError::MissingRefName)?
    } else {
        &ref_path[5..]
    };

    map_lookup_typed_ref(stream, wanted, map_ref)
        .await?
        .ok_or(RefError::NotFound)
}

/// From GitLab state files in `store_vfs`, resolve a ref, returning the corresponding [`Node`]
///
/// Parameter `ref_path` must be the full ref path, i.e., starting with `refs/`
pub async fn full_ref_node(store_vfs: &Path, ref_path: &[u8]) -> Result<Node, RefError> {
    Ok(map_full_ref(
        store_vfs,
        ref_path,
        |typed_ref| {
            Node::from_hex(&typed_ref.target_sha)
                .map_err(|_| StateFileError::InvalidNode(typed_ref.target_sha))
        },
        |keep_around| {
            Node::from_hex(keep_around)
                .map_err(|_| StateFileError::InvalidNode(keep_around.to_vec()))
        },
    )
    .await??)
}

pub async fn existing_default_gitlab_branch(
    store_vfs: &Path,
) -> Result<Option<(Vec<u8>, Node)>, StateFileError> {
    match get_gitlab_default_branch(store_vfs).await? {
        None => {
            info!("No GitLab default branch");
            Ok(None)
        }
        Some(branch) => {
            match lookup_typed_ref_as_node(stream_gitlab_branches(store_vfs).await?, &branch)
                .await?
            {
                None => {
                    warn!("GitLab default branch not found in state file");
                    Ok(None)
                }
                Some(node) => Ok(Some((branch, node))),
            }
        }
    }
}

/// From GitLab state files in `store_vfs`, resolve a given GitLab revision as a [`NodePrefix`]
///
/// Valid GitLab revisions include shortened commit SHAs, this is why the return type
/// is [`NodePrefix`] rather than [`Node`].
///
/// Returns `Ok(None)` if the revision could not be found.
pub async fn gitlab_revision_node_prefix(
    store_vfs: &Path,
    revision: &[u8],
) -> Result<Option<NodePrefix>, RefError> {
    if revision == b"HEAD" {
        match existing_default_gitlab_branch(store_vfs).await? {
            None => {
                info!("No GitLab default branch or pointing to missing branch");
                return Ok(None);
            }
            Some((_name, node)) => {
                return Ok(Some(node.into()));
            }
        }
    }

    // Full nodes have the highest precedence in Gitaly.
    // They also are frequently used and cheap to check (no I/O).
    if let Ok(node) = Node::from_hex(revision) {
        return Ok(Some(node.into()));
    }

    // Full refs are well qualified, hence have high precedence
    if let Ok(node) = full_ref_node(store_vfs, revision).await {
        return Ok(Some(node.into()));
    }

    // Tags have the highest precedence amongst potentially ambiguous revisions
    if let Some(node) =
        lookup_typed_ref_as_node(stream_gitlab_tags(store_vfs).await?, revision).await?
    {
        return Ok(Some(node.into()));
    }

    // Branches. TODO duplication, maybe chain the streams if not None
    if let Some(node) =
        lookup_typed_ref_as_node(stream_gitlab_branches(store_vfs).await?, revision).await?
    {
        return Ok(Some(node.into()));
    }

    // Last case: Node Prefix
    if let Ok(prefix) = NodePrefix::from_hex(revision) {
        return Ok(Some(prefix));
    }

    Ok(None)
}

/// Blocking variant of [`gitlab_revision_node_prefix`]
///
/// This is to be used in the cases when execution is happening in a blocking
/// thread (typically because repository had to be fully loaded before hand).
pub fn blocking_gitlab_revision_node_prefix(
    store_vfs: &Path,
    revision: &[u8],
) -> Result<Option<NodePrefix>, RefError> {
    block_on(gitlab_revision_node_prefix(store_vfs, revision))
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use tokio::fs::File;

    use tokio::io::AsyncWriteExt;

    async fn write_test_file(
        // TODO deduplicate with gitlab::state::tests
        store_vfs: &Path,
        name: &str,
        content: &[u8],
    ) -> Result<(), StateFileError> {
        Ok(File::create(store_vfs.join(name))
            .await?
            .write_all(content)
            .await?)
    }

    /// A simple wrapper that returns the hash for a full ref name
    ///
    /// One of the goals is the error treatment to map [`RefError::NotFound`] to `None` and
    /// hence allow the testing code to use the question mark operator
    async fn full_ref_hash(store_vfs: &Path, full_ref: &[u8]) -> Result<Option<Vec<u8>>, RefError> {
        match map_full_ref(store_vfs, full_ref, |tr| tr.target_sha, |ka| ka.to_vec()).await {
            Err(RefError::NotFound) => Ok(None),
            Ok(res) => Ok(Some(res)),
            Err(e) => Err(e),
        }
    }

    #[tokio::test]
    async fn test_map_full_ref() -> Result<(), RefError> {
        let tmp_dir = tempdir().unwrap(); // not async, but it doesn't matter much in tests
        let store_vfs = tmp_dir.path();

        write_test_file(
            store_vfs,
            "gitlab.branches",
            b"001\n437bd1bf68ac037eb6956490444e2d7f9a5655c9 branch/default\n",
        )
        .await?;
        write_test_file(
            store_vfs,
            "gitlab.tags",
            b"001\nb50274b9b1c58fc97c45357a7c901d39bafc264d v6\n",
        )
        .await?;
        write_test_file(
            store_vfs,
            "gitlab.special-refs",
            b"001\nf61a76dc97fb1a58f30e1b74245b957bb8c8d609 merge-requests/35/train\n",
        )
        .await?;
        write_test_file(
            store_vfs,
            "gitlab.keep-arounds",
            b"001\n9787c1a7b9390e3f09babce1506254eb698dfba3\n",
        )
        .await?;

        assert_eq!(
            full_ref_hash(store_vfs, b"refs/heads/branch/default").await?,
            Some(b"437bd1bf68ac037eb6956490444e2d7f9a5655c9".to_vec())
        );
        assert_eq!(
            full_ref_hash(store_vfs, b"refs/tags/v6").await?,
            Some(b"b50274b9b1c58fc97c45357a7c901d39bafc264d".to_vec())
        );
        assert_eq!(
            full_ref_hash(store_vfs, b"refs/merge-requests/35/train").await?,
            Some(b"f61a76dc97fb1a58f30e1b74245b957bb8c8d609".to_vec())
        );
        assert_eq!(
            full_ref_hash(
                store_vfs,
                b"refs/keep-around/9787c1a7b9390e3f09babce1506254eb698dfba3"
            )
            .await?,
            Some(b"9787c1a7b9390e3f09babce1506254eb698dfba3".to_vec())
        );

        assert_eq!(full_ref_hash(store_vfs, b"refs/heads/other").await?, None);
        assert_eq!(full_ref_hash(store_vfs, b"refs/pipelines/54").await?, None);
        assert_eq!(full_ref_hash(store_vfs, b"refs/tags/v8").await?, None);
        assert_eq!(
            full_ref_hash(
                store_vfs,
                b"refs/keep-around/b50274b9b1c58fc97c45357a7c901d39bafc264d"
            )
            .await?,
            None
        );

        // input errors
        match full_ref_hash(store_vfs, b"REF/foo").await.unwrap_err() {
            RefError::NotAFullRef => Ok(()),
            e => Err(e),
        }?;
        match full_ref_hash(store_vfs, b"refs").await.unwrap_err() {
            RefError::NotAFullRef => Ok(()),
            e => Err(e),
        }?;
        match full_ref_hash(store_vfs, b"refs/tags").await.unwrap_err() {
            RefError::MissingRefName => Ok(()),
            e => Err(e),
        }?;

        Ok(())
    }
}
