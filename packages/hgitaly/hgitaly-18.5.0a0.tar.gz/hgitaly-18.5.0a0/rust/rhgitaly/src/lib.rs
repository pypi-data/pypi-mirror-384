// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
#[macro_use]
extern crate build_const;

// The generated module is derived from the Protobuf "package" name
// Hence as soon as we start compiling the HGitaly-specific proto files,
// we'll also get a `hgitaly` module.
// using `include!` lets us add attributes, in this case to control clippy
pub mod gitaly {
    #![allow(unknown_lints)]
    #![allow(clippy::all)]
    include! {"generated/gitaly.rs"}
}

pub mod hgitaly {
    #![allow(unknown_lints)]
    include! {"generated/hgitaly.rs"}
}

pub mod bundle;
pub mod config;
pub mod errors;
pub mod git;
pub mod gitlab;
pub mod glob;
pub mod hg_git;
pub mod license;
pub mod mercurial;
pub mod message;
pub mod metadata;
pub mod oid;
pub mod process;
pub mod repository;
pub mod service;
pub mod sidecar;
pub mod ssh;
pub mod streaming;
pub mod util;
pub mod wait;
pub mod workdir;

pub use config::*;
pub use gitaly::*;
