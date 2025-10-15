// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
//
// SPDX-License-Identifier: GPL-2.0-or-later
//! Utilities for Object identifiers, mimicking Git in Mercurial context.
//!
//! This matches the `hgitaly.oid` reference Python module
use std::convert::AsRef;

use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};

use hg::revlog::{FromHexError, Node};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OidError {
    /// If the extracted Node ID is ill formed
    InvalidNodeId,
    /// If the path part is invalid (as base64 in current version)
    InvalidPathComponent,
    /// For oids that are expected to contain a path (e.g., blob case)
    MissingPath,
}

impl From<FromHexError> for OidError {
    fn from(_e: FromHexError) -> Self {
        Self::InvalidNodeId
    }
}

fn concat_chgsid_path<P: AsRef<[u8]> + ?Sized>(changeset_id: &Node, path: &P) -> String {
    let mut res = format!("{:x}_", &changeset_id);
    res.push_str(&BASE64.encode(path));
    res
}

fn split_chgsid_path(oid: &str) -> Result<(Node, Option<Vec<u8>>), OidError> {
    Ok(match oid.find('_') {
        Some(idx) => (
            Node::from_hex(&oid[0..idx])?,
            Some(
                BASE64
                    .decode(&oid[idx + 1..])
                    .map_err(|_| OidError::InvalidPathComponent)?,
            ),
        ),
        None => (Node::from_hex(oid)?, None),
    })
}

pub fn blob_oid<P: AsRef<[u8]> + ?Sized>(changeset_id: &Node, path: &P) -> String {
    concat_chgsid_path(changeset_id, path)
}

pub fn extract_blob_oid(oid: &str) -> Result<(Node, Vec<u8>), OidError> {
    let (oid, path) = split_chgsid_path(oid)?;
    Ok((oid, path.ok_or(OidError::MissingPath)?))
}

pub fn tree_oid<P: AsRef<[u8]> + ?Sized>(changeset_id: &Node, path: &P) -> String {
    concat_chgsid_path(changeset_id, path)
}

pub fn extract_tree_oid(oid: &str) -> Result<(Node, Vec<u8>), OidError> {
    let (oid, path) = split_chgsid_path(oid)?;
    Ok((oid, path.ok_or(OidError::MissingPath)?))
}

#[cfg(test)]
/// Same test data as in Python hgitaly.tests.test_oid
mod tests {

    use super::*;

    #[test]
    fn test_blob_oid() {
        let chgs_id = Node::from_hex("56de78ad56de78ad56de78ad56de78ad56de78ad").unwrap();
        let path = b"rang\xe9";
        let blob_id = blob_oid(&chgs_id, &path);
        // explicit same result as Python impl
        assert_eq!(blob_id, "56de78ad56de78ad56de78ad56de78ad56de78ad_cmFuZ+k=");
        let (decoded_cid, decoded_path) = extract_blob_oid(&blob_id).unwrap();
        assert_eq!(decoded_cid, chgs_id);
        assert_eq!(decoded_path, path);
    }
}
