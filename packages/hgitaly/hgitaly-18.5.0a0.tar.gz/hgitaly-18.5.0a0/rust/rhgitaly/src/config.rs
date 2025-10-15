// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::env;
use std::error::Error;
use std::ffi::OsString;
use std::fmt;
use std::fs;
use std::net::SocketAddr;
use std::path::PathBuf;
use uuid::Uuid;

use hg::config::Config as CoreConfig;

const CLIENT_ID_FILE_NAME: &str = "rhgitaly.client-id";
const DEFAULT_CONFIG_DIRECTORY: &str = "/etc/gitlab";

#[derive(Debug)]
#[allow(clippy::upper_case_acronyms)]
/// Necessary infortion to bind the listening socket
pub enum BindAddress {
    Unix(PathBuf),
    TCP(SocketAddr),
}

#[derive(Debug, Clone)]
#[allow(clippy::upper_case_acronyms)]
/// Necessary infortion to call a server (e.g., HGitaly (Python) sidecar)
pub enum ServerAddress {
    Unix(PathBuf),
    URI(String),
}

/// Parse the URL to listen to
///
/// There are two cases: `unix:/some/path/sock` and `tcp://hostname:port`, where
/// hostname can only be an IP address (v4 or v6).
///
/// This is a toy implementation anyway, we'll add a proper dependency to the `url` crate later on
fn parse_listen_url(url: &str) -> Result<BindAddress, Box<dyn Error>> {
    if let Some(path) = url.strip_prefix("unix:") {
        return Ok(BindAddress::Unix(path.into()));
    }
    if let Some(addr) = url.strip_prefix("tcp://") {
        return Ok(BindAddress::TCP(addr.parse()?));
    }
    Err("Unsupported URL".into())
}

/// Parse the URI of a gRPC server
///
/// There are two cases: `unix:/some/path/sock` and URIs directly supported by Tonic
/// (`http` or `https` schemes). The latter are not validated at this point.
fn parse_server_uri(uri: &str) -> Result<ServerAddress, Box<dyn Error>> {
    if let Some(path) = uri.strip_prefix("unix:") {
        return Ok(ServerAddress::Unix(path.into()));
    }
    Ok(ServerAddress::URI(uri.to_owned()))
}

pub struct Config {
    pub client_id: String,
    pub incarnation_id: String,
    pub repositories_root: PathBuf,
    pub listen_address: BindAddress,
    pub hg_executable: OsString,
    pub git_executable: OsString,
    pub hgitaly_sidecar_address: ServerAddress,
    pub hg_core_config: CoreConfig,
    hgrc_path: Option<OsString>,
}

impl Default for Config {
    fn default() -> Self {
        let incarnation = Uuid::new_v4();
        Self {
            client_id: "filled once config dir is known".into(),
            incarnation_id: incarnation.into(),
            repositories_root: "".into(),
            hg_executable: "hg".into(),
            git_executable: "git".into(),
            listen_address: BindAddress::Unix("/tmp/rhgitaly.socket".into()),
            hgitaly_sidecar_address: ServerAddress::Unix("/tmp/hgitaly.socket".into()),
            hgrc_path: None,
            hg_core_config: CoreConfig::load_non_repo()
                .expect("Should have been able to read Mercurial core config"),
        }
    }
}

impl fmt::Debug for Config {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Config")
            .field("repositories_root", &self.repositories_root)
            .field("listen_address", &self.listen_address)
            .field("hg_executable", &self.hg_executable)
            .field("git_executable", &self.git_executable)
            .field("hgitaly_sidecar_address", &self.hgitaly_sidecar_address)
            .field(
                "hg_core_config",
                &self.hgrc_path.as_ref().map_or(
                    "read from global and user configuration files".to_owned(),
                    |path| format!("read from HGRCPATH={:?}", &path),
                ),
            )
            .field("client_id", &self.client_id)
            .field("incarnation_id", &self.incarnation_id)
            .finish()
    }
}

fn load_set_client_id() -> String {
    let mut client_id_path: PathBuf = env::var_os("RHGITALY_CONFIG_DIRECTORY")
        .unwrap_or_else(|| DEFAULT_CONFIG_DIRECTORY.into())
        .into();
    client_id_path.push(CLIENT_ID_FILE_NAME);
    if client_id_path.exists() {
        fs::read_to_string(&client_id_path)
    } else {
        let client_id = format!("rhgitaly-{}", &Uuid::new_v4());
        fs::write(&client_id_path, &client_id).map(|_| client_id)
    }
    .unwrap_or_else(|_| {
        panic!(
            "Could not read or write client id file {}",
            client_id_path.display()
        )
    })
}

impl Config {
    /// Read configuration from environment variables
    ///
    /// This is useful for Gitaly Comparison tests, especially until we can
    /// support the HGitaly configuration file (i.e., HGRC)
    pub fn from_env() -> Self {
        Config {
            repositories_root: env::var_os("RHGITALY_REPOSITORIES_ROOT")
                .expect("RHGITALY_REPOSITORIES_ROOT not set in environment")
                .into(),
            client_id: load_set_client_id(),
            listen_address: parse_listen_url(
                &env::var("RHGITALY_LISTEN_URL")
                    .expect("RHGITALY_LISTEN_URL not set in environment"),
            )
            .expect("Could not parse listen URL"),
            hgitaly_sidecar_address: parse_server_uri(
                &env::var("RHGITALY_SIDECAR_ADDRESS")
                    .expect("RHGITALY_SIDECAR_ADDRESS not set in environment"),
            )
            .expect("Could not parse sidecar URL"),
            hg_executable: env::var("RHGITALY_HG_EXECUTABLE").map_or_else(
                |e| match e {
                    env::VarError::NotPresent => "hg".into(),
                    env::VarError::NotUnicode(os_string) => os_string,
                },
                |v| v.into(),
            ),
            git_executable: env::var("RHGITALY_GIT_EXECUTABLE").map_or_else(
                |e| match e {
                    env::VarError::NotPresent => "git".into(),
                    env::VarError::NotUnicode(os_string) => os_string,
                },
                |v| v.into(),
            ),
            hgrc_path: env::var_os("HGRCPATH"),
            ..Default::default()
        }
    }
}
