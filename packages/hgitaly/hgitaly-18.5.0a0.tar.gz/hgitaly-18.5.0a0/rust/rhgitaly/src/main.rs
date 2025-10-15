// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use clap::Parser;
use std::sync::Arc;

use tokio::fs::remove_file;
use tokio::net::UnixListener;
use tokio_stream::wrappers::UnixListenerStream;
use tonic::transport::Server;

use rhgitaly::config::{BindAddress, Config};
use rhgitaly::license::load_license_nicknames;
use rhgitaly::service::analysis::analysis_server;
use rhgitaly::service::blob::blob_server;
use rhgitaly::service::commit::commit_server;
use rhgitaly::service::diff::diff_server;
use rhgitaly::service::health::health_server;
use rhgitaly::service::mercurial_aux_git::mercurial_aux_git_server;
use rhgitaly::service::mercurial_changeset::mercurial_changeset_server;
use rhgitaly::service::mercurial_operations::mercurial_operations_server;
use rhgitaly::service::mercurial_repository::mercurial_repository_server;
use rhgitaly::service::operations::operations_server;
use rhgitaly::service::r#ref::ref_server;
use rhgitaly::service::remote::remote_server;
use rhgitaly::service::repository::repository_server;
use rhgitaly::service::server::{server_server, HGITALY_VERSION};
use rhgitaly::sidecar;
use rhgitaly::streaming::WRITE_BUFFER_SIZE;
use tracing::{info, Level};
use tracing_subscriber::{fmt::format::FmtSpan, FmtSubscriber};

fn setup_tracing() {
    // a builder for `FmtSubscriber`.
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .with_span_events(FmtSpan::CLOSE)
        .finish();

    tracing::subscriber::set_global_default(subscriber).expect("setting default subscriber failed");
}

#[derive(Parser, Debug)]
#[command(name = "RHGitaly")]
#[command(
    about = "RHGitaly is a partial implementation of the Gitaly and HGitaly gRPC protocols \
for Mercurial repositories"
)]
#[command(
    long_about = "RHGitaly is a performance-oriented partial implementation of the Gitaly \
and HGitaly gRPC protocols for Mercurial repositories.

It is asynchronous with a pool of worker threads, leveraging the Tonic (Tokio) gRPC framework, \
and the Mercurial primitives implemented in Rust (hg-core crate).

Configuration is for now entirely done by environment variables (see
https://foss.heptapod.net/heptapod/hgitaly/-/issues/181 to follow progress on this)
"
)]
#[command(version = HGITALY_VERSION)]
struct Args {}

use tokio::signal::unix::{signal, SignalKind};
use tokio_util::sync::CancellationToken;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    load_license_nicknames();
    let _args = Args::parse();

    setup_tracing();

    info!("RHGitaly starting, version {}", HGITALY_VERSION);
    info!("WRITE_BUFFER_SIZE={}", *WRITE_BUFFER_SIZE);

    let shutdown_token = CancellationToken::new();

    let config = Arc::new(Config::from_env());
    let sidecar_servers = Arc::new(sidecar::Servers::new(&config));
    let server = Server::builder()
        .add_service(server_server(&sidecar_servers))
        .add_service(analysis_server(&config))
        .add_service(blob_server(&config, &sidecar_servers))
        .add_service(commit_server(&config, &sidecar_servers))
        .add_service(diff_server(&config, &sidecar_servers))
        .add_service(health_server(&sidecar_servers))
        .add_service(mercurial_aux_git_server(&config, &shutdown_token))
        .add_service(mercurial_changeset_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(mercurial_operations_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(mercurial_repository_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(operations_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(ref_server(&config, &sidecar_servers))
        .add_service(remote_server(&config, &shutdown_token))
        .add_service(repository_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ));

    let mut sigterm = signal(SignalKind::terminate())?;
    // sigterm.recv() returns `None` if "no more events can be received by this stream"
    // In the case of SIGTERM, it probably cannot happen, and by default we will consider
    // it to be a termination condition.
    let wait_sigterm = async move {
        sigterm.recv().await;
        shutdown_token.cancel();
    };

    let bind_addr = &config.listen_address;
    info!("RHGitaly binding to {:?}", bind_addr);
    match bind_addr {
        BindAddress::TCP(addr) => server.serve_with_shutdown(*addr, wait_sigterm).await?,
        BindAddress::Unix(ref path) => {
            let uds = UnixListener::bind(path)?;
            let uds_stream = UnixListenerStream::new(uds);
            server
                .serve_with_incoming_shutdown(uds_stream, wait_sigterm)
                .await?
        }
    };

    // Server now has shut down
    if let BindAddress::Unix(path) = bind_addr {
        info!("Removing Unix Domain socket file at '{}'", &path.display());
        remove_file(&path).await?
    }

    Ok(())
}
