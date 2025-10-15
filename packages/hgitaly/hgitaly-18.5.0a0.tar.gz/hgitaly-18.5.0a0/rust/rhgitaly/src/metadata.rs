// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
//! Handling of gRPC metadata
use std::time::Duration;

use tonic::{
    metadata::{Ascii, MetadataMap, MetadataValue},
    Status,
};

pub const HG_GIT_MIRRORING_MD_KEY: &str = "x-heptapod-hg-git-mirroring";
pub const NATIVE_PROJECT_MD_KEY: &str = "x-heptapod-hg-native";
pub const SKIP_HOOKS_MD_KEY: &str = "x-heptapod-skip-gl-hooks";
pub const ACCEPT_MR_IID_KEY: &str = "x-heptapod-accept-mr-iid";
pub const GRPC_TIMEOUT_HEADER: &str = "grpc-timeout"; // to bad it's not public in `tonic::metadata`

pub fn correlation_id(metadata: &MetadataMap) -> Option<&MetadataValue<Ascii>> {
    metadata.get("x-gitlab-correlation-id")
}

pub fn get_boolean_md_value(metadata: &MetadataMap, key: &str, default: bool) -> bool {
    if let Some(v) = metadata.get(key) {
        match v.to_str() {
            Err(_) => default,
            Ok(s) => s.eq_ignore_ascii_case("true"),
        }
    } else {
        default
    }
}

pub fn grpc_timeout_to_duration(s: &MetadataValue<Ascii>) -> Option<Duration> {
    // Switching to bytes in order to index freely without be bothered
    // with codepoint boundaries that are irrelevant, since it is supposed
    // to be full ASCII anyway.
    let s = s.as_bytes();
    if s.is_empty() {
        return None;
    }
    if let Ok(val) = String::from_utf8_lossy(&s[..s.len() - 1]).parse::<u64>() {
        match s[s.len() - 1] {
            b'H' => Some(Duration::from_secs(val * 3600)),
            b'M' => Some(Duration::from_secs(val * 60)),
            b'S' => Some(Duration::from_secs(val)),
            b'm' => Some(Duration::from_millis(val)),
            b'u' => Some(Duration::from_micros(val)),
            b'n' => Some(Duration::from_nanos(val)),
            _ => None,
        }
    } else {
        None
    }
}

pub fn grpc_timeout(metadata: &MetadataMap) -> Option<Duration> {
    metadata
        .get(GRPC_TIMEOUT_HEADER)
        .and_then(grpc_timeout_to_duration)
}

/// Return whether the Gitaly feature flags in metadata mean the feature is enabled.
///
/// ** Parameters
///
/// - `name`: provide the name with dash separators, without the `gitaly-`
///   prefix. Hence if a feature flag is seen as `gitaly_my_feature` by Rails,
///   the caller should set `name` to `"my-feature"`.
/// - `default`: as the Rails application does not transmit anything if the
///   feature flag has not explicitely been set, it cannot enforce a `true`
///   default value. Hence the default has to be provided server-side, which is
///   what the `default` parameter here does.
pub fn is_feature_enabled(metadata: &MetadataMap, name: &str, default: bool) -> bool {
    let key = format!("gitaly-feature-{name}");
    get_boolean_md_value(metadata, &key, default)
}

/// Shortcut for easy fallback to sidecar depending on feature flag
///
/// In context of a conditional fallback to sidecar, such as with [`sidecar::fallback_unary!`],
/// this can be used with question mark to trigger the fallbacking.
pub fn fallback_if_feature_disabled(
    metadata: &MetadataMap,
    name: &str,
    default: bool,
) -> Result<(), Status> {
    if !is_feature_enabled(metadata, name, default) {
        return Err(Status::unimplemented("needs enabled feature flag"));
    }
    Ok(())
}
