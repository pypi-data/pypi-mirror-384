// Copyright 2025 Georges Racinet <georges.racinet@cloudcrane.io>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
//! Utilities interaction with Mercurial
use hg::revlog::{
    changelog::Changelog,
    manifest::{Manifest, Manifestlog},
    Node, NodePrefix, RevlogError, NULL_REVISION,
};

pub mod blob_tree;
pub mod lock;

pub use blob_tree::*;

/// Return the [`Manifest`] for the changelog entry given by a [`NodePrefix`]
pub fn changelog_entry_manifest(
    changelog: &Changelog,
    manifestlog: &Manifestlog,
    changeset_node_prefix: NodePrefix,
) -> Result<Option<(Node, Manifest)>, RevlogError> {
    let rev = changelog.rev_from_node(changeset_node_prefix)?;
    if rev == NULL_REVISION {
        return Ok(None);
    }
    // TODO submit UPSTREAM an `entry_for_rev` to avoid back-and-forth
    // between Revision and UncheckedRevision
    let changelog_entry = changelog.entry_for_unchecked_rev(rev.into())?;
    let manifest = manifestlog.data_for_node(changelog_entry.data()?.manifest_node()?.into())?;
    Ok(Some((*changelog_entry.as_revlog_entry().node(), manifest)))
}
