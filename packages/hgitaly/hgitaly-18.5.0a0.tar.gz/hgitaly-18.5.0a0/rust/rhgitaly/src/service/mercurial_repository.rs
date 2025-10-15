// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::ffi::{OsStr, OsString};
use std::fmt::{Debug, Formatter};
use std::os::unix::ffi::{OsStrExt, OsStringExt};
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio_stream::wrappers::ReceiverStream;
use tokio_stream::StreamExt;
use tokio_util::sync::CancellationToken;
use tonic::{
    codegen::BoxStream, metadata::Ascii, metadata::MetadataMap, metadata::MetadataValue, Request,
    Response, Status,
};
use tracing::{info, instrument, warn};
use url::Url;

use crate::config::Config;
use crate::gitaly::{Repository, User};
use crate::gitlab::state::stream_gitlab_branches;
use crate::glob::star_patterns_to_regex;
use crate::hgitaly::mercurial_repository_service_client::MercurialRepositoryServiceClient;
use crate::hgitaly::mercurial_repository_service_server::{
    MercurialRepositoryService, MercurialRepositoryServiceServer,
};
use crate::hgitaly::{
    GetConfigItemRequest, GetConfigItemResponse, GetManagedConfigRequest, GetManagedConfigResponse,
    HgCallRequest, HgCallResponse, HousekeepingRequest, HousekeepingResponse, MercurialPeer,
    PullRequest, PullResponse, PushRequest, PushResponse, SetManagedConfigRequest,
    SetManagedConfigResponse,
};
use crate::metadata::correlation_id;
use crate::repository::{
    default_repo_spec_error_status, repo_store_vfs,
    spawner::{BytesChunking, RepoProcessSpawner, RepoProcessSpawnerTemplate, RequestHgSpawnable},
    RequestWithRepo,
};
use crate::sidecar;
use crate::ssh::SSHOptions;
use crate::streaming::WRITE_BUFFER_SIZE;
use crate::util::{bytes_strings_as_str, tracing_span_id};

#[derive(Debug)]
pub struct MercurialRepositoryServiceImpl {
    config: Arc<Config>,
    shutdown_token: CancellationToken,
    sidecar_servers: Arc<sidecar::Servers>,
}

#[tonic::async_trait]
impl MercurialRepositoryService for MercurialRepositoryServiceImpl {
    // TODO InitConfig has never been implemented in HGitaly, and would
    // still help keeping the client-side simple. We cannot just add the
    // logic to CreateRepository because we have the additional group path.
    // Another option would be to introduce our CreateMercurialRepository that
    // would do both (in Python, then).

    async fn get_config_item(
        &self,
        request: Request<GetConfigItemRequest>,
    ) -> Result<Response<GetConfigItemResponse>, Status> {
        sidecar::unary!(
            self,
            request,
            MercurialRepositoryServiceClient,
            get_config_item
        )
    }

    async fn get_managed_config(
        &self,
        request: Request<GetManagedConfigRequest>,
    ) -> Result<Response<GetManagedConfigResponse>, Status> {
        sidecar::unary!(
            self,
            request,
            MercurialRepositoryServiceClient,
            get_managed_config
        )
    }

    async fn set_managed_config(
        &self,
        request: Request<SetManagedConfigRequest>,
    ) -> Result<Response<SetManagedConfigResponse>, Status> {
        sidecar::unary!(
            self,
            request,
            MercurialRepositoryServiceClient,
            set_managed_config
        )
    }

    async fn hg_call(
        &self,
        request: Request<HgCallRequest>,
    ) -> Result<Response<BoxStream<HgCallResponse>>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_hg_call(inner, correlation_id(&metadata), &metadata)
            .await
    }

    async fn pull(&self, request: Request<PullRequest>) -> Result<Response<PullResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_pull(inner, correlation_id(&metadata), &metadata)
            .await
    }

    async fn push(&self, request: Request<PushRequest>) -> Result<Response<PushResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_push(inner, correlation_id(&metadata), &metadata)
            .await
    }

    async fn housekeeping(
        &self,
        request: Request<HousekeepingRequest>,
    ) -> Result<Response<HousekeepingResponse>, Status> {
        sidecar::unary!(
            self,
            request,
            MercurialRepositoryServiceClient,
            housekeeping
        )
    }
}

impl MercurialRepositoryServiceImpl {
    #[instrument(name = "pull", skip(self, request, metadata))]
    async fn inner_pull(
        &self,
        request: PullRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<PullResponse>, Status> {
        tracing_span_id!();
        info!("Processing, request={:?}", PullTracingRequest(&request));
        let config = self.config.clone();
        let mut spawner = RepoProcessSpawner::prepare_hg(
            config,
            request.clone(),
            metadata,
            default_repo_spec_error_status,
        )
        .await?;
        let url = &request
            .remote_peer
            .as_ref()
            .ok_or(Status::invalid_argument("Missing remote peer"))?
            .url
            .clone();
        let mut args: Vec<OsString> = Vec::with_capacity(4 + request.mercurial_revisions.len() * 2);
        let allow_bookmarks = spawner
            .hg_load_repo_and_then(move |repo| {
                repo.config()
                    .get_bool(b"heptapod", b"allow-bookmarks")
                    .map_err(|e| {
                        Status::internal(format!("Error reading repository config: {}", e))
                    })
            })
            .await?;
        info!("Allow bookmarks: {}", allow_bookmarks);

        if !allow_bookmarks {
            args.push("--config".into());
            args.push("heptapod.exchange-ignore-bookmarks=yes".into());
        };
        args.push("pull".into());
        for revspec in &request.mercurial_revisions {
            args.push("-r".into());
            args.push(OsString::from_vec(revspec.clone()));
        }
        args.push(url.into());
        // One can expect RHGitaly to read the hg stdout much faster than it will be produced,
        // hence we do not need a very large buffer
        let (stdout_tx, mut stdout_rx) = mpsc::channel(3);
        spawner.capture_stdout(stdout_tx, BytesChunking::Lines);
        spawner.args(&args);
        let spawned = spawner.spawn(self.shutdown_token.clone());
        let read_stdout = async {
            let mut new_changesets = true;
            while let Some(line) = stdout_rx.recv().await {
                if line == b"no changes found\n" {
                    new_changesets = false;
                }
            }
            new_changesets
        };
        let (spawn_result, new_changesets) = tokio::join!(spawned, read_stdout);
        let hg_exit_code = spawn_result?;
        if hg_exit_code != 0 {
            return Err(Status::internal(format!(
                "Mercurial subprocess exited with code {}",
                hg_exit_code
            )));
        }
        Ok(Response::new(PullResponse { new_changesets }))
    }

    #[instrument(name = "hg_call", skip(self, request, metadata))]
    async fn inner_hg_call(
        &self,
        request: HgCallRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<BoxStream<HgCallResponse>>, Status> {
        tracing_span_id!();
        info!("Processing, request={:?}", HgCallTracingRequest(&request));
        let config = self.config.clone();
        let mut spawner = RepoProcessSpawner::prepare_hg(
            config,
            request.clone(),
            metadata,
            default_repo_spec_error_status,
        )
        .await?;
        // One can expect RHGitaly to read the hg stdout much faster than it will be produced,
        // hence we do not need a very large buffer
        let (stdout_tx, mut stdout_rx) = mpsc::channel(3);
        spawner.capture_stdout(stdout_tx, BytesChunking::Lines);
        let args: Vec<_> = request
            .args
            .iter()
            .map(|a| OsStr::from_bytes(a).to_os_string())
            .collect();
        spawner.args(&args);
        let spawned = spawner.spawn(self.shutdown_token.clone());

        let (tx, rx) = mpsc::channel(1);
        // We decided to stream lines of bytes, and to explicitly state the method not to
        // be suitable for outputing large binary content.
        // If a single "line" is bigger than the gRPC buffer, some data may be lost (not
        // sent over the wire), but that is the caller's fault: they should not have used this
        // method.
        let read_stdout = async move {
            let mut current_size = 0;
            let mut current_stdout_lines = Vec::with_capacity(50);

            while let Some(line) = stdout_rx.recv().await {
                current_size += line.len();
                current_stdout_lines.push(line);
                if current_size >= *WRITE_BUFFER_SIZE {
                    // TODO consider some overhead or precreate the response and use .size()
                    if tx
                        .send(Ok(HgCallResponse {
                            exit_code: 0,
                            stdout: current_stdout_lines.clone(),
                        }))
                        .await
                        .is_err()
                    {
                        // not logging because it will occur yet again in the final async task
                        return (current_stdout_lines, tx);
                    }
                    current_stdout_lines.clear();
                    current_size = 0;
                }
            }
            (current_stdout_lines, tx)
        };
        tokio::task::spawn(async move {
            let (spawn_result, (stdout_lines, tx)) = tokio::join!(spawned, read_stdout);
            let msg = spawn_result.map(|code| HgCallResponse {
                exit_code: code,
                stdout: stdout_lines,
            });
            if tx.send(msg).await.is_err() {
                warn!("Request cancelled by client before all results could be streamed back");
            };
        });

        Ok(Response::new(Box::pin(ReceiverStream::new(rx))))
    }

    #[instrument(name = "push", skip(self, request, metadata))]
    async fn inner_push(
        &self,
        request: PushRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<PushResponse>, Status> {
        tracing_span_id!();
        info!("Processing, request={:?}", PushTracingRequest(&request));

        let config = self.config.clone();
        let spawner_tmpl = RepoProcessSpawnerTemplate::new_hg(
            config.clone(),
            request.clone(),
            metadata,
            default_repo_spec_error_status,
        )
        .await?;
        let mut spawner = spawner_tmpl.hg_spawner();
        let peer = &request
            .remote_peer
            .as_ref()
            .ok_or(Status::invalid_argument("Missing remote peer"))?;
        let url = peer.url.clone();
        let ssh_opts = SSHOptions::hg_new(peer).await?;
        let mut args: Vec<OsString> = Vec::with_capacity(4);

        args.push("push".into());
        let mut revset = String::new();
        if !request.only_gitlab_branches_matching.is_empty() {
            let store_vfs = repo_store_vfs(&self.config, &request.repository)
                .await
                .map_err(default_repo_spec_error_status)?;
            let rx = star_patterns_to_regex(&request.only_gitlab_branches_matching);
            // Gitaly's UpdateRemoteMirror matching behaves exactly
            // according to its doc: `*` is the only wildcard: As of
            // revision 839d9cc922e06ce7 (a week before v17.6), Gitaly builds
            // a big regexp by replacing `*` with `.*` and escaping the rest.
            revset.push_str("::("); // necessary because we'll cross with other criteria
            let mut has_match = false;
            if let Some(mut branch_stream) = stream_gitlab_branches(&store_vfs).await? {
                while let Some(res) = branch_stream.next().await {
                    let branch = res?;
                    if rx.is_match(&branch.name) {
                        if has_match {
                            revset.push('+');
                        }
                        has_match = true;
                        revset.push_str(&String::from_utf8_lossy(&branch.target_sha));
                    }
                }
                revset.push(')');
            }
        }
        if !request.include_drafts {
            if !revset.is_empty() {
                revset.push_str(" and ")
            };
            revset.push_str("public()");
        };

        let revset: OsString = revset.into();
        if !revset.is_empty() {
            args.push("-r".into());
            args.push(revset.clone());
        }
        if url.starts_with("ssh://") {
            args.push("-e".into());
            args.push(ssh_opts.ssh_command());
        }
        if !peer.ssh_remote_command.is_empty() {
            args.push("--remotecmd".into());
            args.push(OsStr::from_bytes(&peer.ssh_remote_command).to_owned());
        }
        args.push(url.into());

        spawner.args(&args);
        let hg_exit_code = spawner.spawn(self.shutdown_token.clone()).await?;
        // In case the revset evaluates to an empty set, Mercurial exits with
        // code 255, so we have to check if that was the cause, so that we
        // would not consider this an error.
        // It would be slightly more efficient to introduce our own `hpd-push`
        // that does not do this, but this is good enough for now.
        if hg_exit_code != 0 && hg_exit_code != 1 {
            if hg_exit_code == 255
                && !revset.is_empty()
                && spawner_tmpl
                    .hg_log(&revset, self.shutdown_token.clone(), Some(1))
                    .await?
                    .is_empty()
            {
                return Ok(Response::new(PushResponse {
                    new_changesets: false,
                }));
            }
            return Err(Status::internal(format!(
                "Mercurial subprocess exited with code {}",
                hg_exit_code
            )));
        }
        Ok(Response::new(PushResponse {
            new_changesets: hg_exit_code == 0,
        }))
    }
}

impl RequestWithRepo for HgCallRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestHgSpawnable for HgCallRequest {
    fn user_ref(&self) -> Option<&User> {
        self.user.as_ref()
    }
}

struct HgCallTracingRequest<'a>(&'a HgCallRequest);

impl Debug for HgCallTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("HgCallRequest")
            .field("repository", &self.0.repository)
            .field("args", &bytes_strings_as_str(&self.0.args))
            .finish()
    }
}

impl RequestWithRepo for PullRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestHgSpawnable for PullRequest {
    fn user_ref(&self) -> Option<&User> {
        self.user.as_ref()
    }
}

impl RequestHgSpawnable for PushRequest {}

impl RequestWithRepo for PushRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

struct MercurialPeerTracing<'a>(&'a MercurialPeer);

impl Debug for MercurialPeerTracing<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        let mut parsed = Url::parse(&self.0.url);
        let stripped_url = match parsed {
            Ok(ref mut url) => {
                let _ignore_errors = url.set_password(None);
                url.as_str()
            }
            Err(_) => &self.0.url,
        };
        f.debug_struct("RemotePeer")
            .field("url", &stripped_url)
            .field("ssh_key", &format!("<{} bytes>", &self.0.ssh_key.len()))
            .field(
                "ssh_known_hosts",
                &format!("<{} bytes>", &self.0.ssh_known_hosts.len()),
            )
            .field(
                "ssh_remote_command",
                &String::from_utf8_lossy(&self.0.ssh_remote_command),
            )
            .finish()
    }
}

struct PullTracingRequest<'a>(&'a PullRequest);

impl Debug for PullTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PullRequest")
            .field("repository", &self.0.repository)
            .field(
                "remote_peer",
                &self.0.remote_peer.as_ref().map(MercurialPeerTracing),
            )
            .finish()
    }
}

struct PushTracingRequest<'a>(&'a PushRequest);

impl Debug for PushTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PushRequest")
            .field("repository", &self.0.repository)
            .field(
                "remote_peer",
                &self.0.remote_peer.as_ref().map(MercurialPeerTracing),
            )
            .finish()
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn mercurial_repository_server(
    config: &Arc<Config>,
    shutdown_token: &CancellationToken,
    sidecar_servers: &Arc<sidecar::Servers>,
) -> MercurialRepositoryServiceServer<MercurialRepositoryServiceImpl> {
    MercurialRepositoryServiceServer::new(MercurialRepositoryServiceImpl {
        config: config.clone(),
        shutdown_token: shutdown_token.clone(),
        sidecar_servers: sidecar_servers.clone(),
    })
}
