// Copyright 2025 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later

use std::ffi::OsString;
use std::fmt::{Debug, Formatter};
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio_stream::wrappers::ReceiverStream;
use tokio_util::sync::CancellationToken;
use tonic::{metadata::MetadataMap, Response, Status};
use tracing::{debug, info, warn};

use crate::config::Config;
use crate::gitaly::{
    CreateBundleRequest, CreateBundleResponse, CreateRepositoryFromBundleRequest,
    FetchBundleRequest, Repository, User,
};
use crate::repository::spawner::{BytesChunking, RepoProcessSpawnerTemplate, RequestHgSpawnable};
use crate::repository::{
    checked_git_repo_path_for_creation, default_repo_spec_error_status, RequestWithBytesChunk,
    RequestWithRepo,
};
use crate::streaming::{ResultResponseStream, WRITE_BUFFER_SIZE};

/// In this function, the Repository is assumed to be a Git repository,
/// sitting exacly at the given relative path (no switch to hg, no diversion to +hgitaly area)
pub async fn create_git_bundle(
    config: Arc<Config>,
    repo_path: PathBuf,
    shutdown_token: CancellationToken,
    metadata: &MetadataMap,
) -> ResultResponseStream<CreateBundleResponse> {
    let git_config = Vec::new();
    let spawner_tmpl = RepoProcessSpawnerTemplate::new_git_at_path(
        config.clone(),
        repo_path,
        metadata,
        git_config,
    )
    .await?;
    let mut spawner = spawner_tmpl.git_spawner();
    // TODO evaluate needs for buffers? One can expect RHGitaly to read it fast
    // unless all threads are busy.
    let (stdout_tx, mut stdout_rx) = mpsc::channel(3);
    spawner.capture_stdout(stdout_tx, BytesChunking::Binary(*WRITE_BUFFER_SIZE));
    let args: Vec<OsString> = vec!["bundle".into(), "create".into(), "-".into(), "--all".into()];
    spawner.args(&args);

    let (tx, rx) = mpsc::channel(1);
    let spawned = spawner.spawn(shutdown_token);
    let tx2 = tx.clone();

    let read_stdout = async move {
        while let Some(data) = stdout_rx.recv().await {
            debug!("Received {} bytes", data.len());
            tx.send(Ok(CreateBundleResponse { data }))
                .await
                .unwrap_or_else(|e| {
                    warn!(
                        "Request cancelled by client before all results \
                             could be streamed back: {e}"
                    )
                })
        }
        info!("Finished listening on internal channel for bundle data");
    };

    tokio::task::spawn(async move {
        let spawn_result = tokio::join!(spawned, read_stdout).0;
        let err = match spawn_result {
            Ok(0) => return,
            Ok(git_exit_code) => {
                Status::internal(format!("Git subprocess exited with code {}", git_exit_code))
            }
            Err(e) => e,
        };

        if tx2.send(Err(err.clone())).await.is_err() {
            warn!("Request cancelled by client before error {err:?} could be streamed back");
        }
    });

    Ok(Response::new(Box::pin(ReceiverStream::new(rx))))
}

pub async fn create_repo_from_git_bundle(
    config: Arc<Config>,
    opt_repo: Option<&Repository>,
    divert_aux_git_repo: bool,
    bundle_path: PathBuf,
    shutdown_token: CancellationToken,
    metadata: &MetadataMap,
) -> Result<(), Status> {
    let (_gl_repo, repo_path) =
        checked_git_repo_path_for_creation(&config, opt_repo, divert_aux_git_repo)
            .await
            .map_err(default_repo_spec_error_status)?;

    let git_config = vec![
        // See comment in FetchBundle
        ("transfer.fsckObjects".into(), "false".into()),
    ];

    let cwd = config.repositories_root.clone();

    let mut spawner =
        RepoProcessSpawnerTemplate::new_git_at_path(config, cwd, metadata, git_config)
            .await?
            .git_spawner();

    let args: Vec<OsString> = vec![
        "clone".into(),
        "--bare".into(),
        "--quiet".into(),
        bundle_path.into(),
        repo_path.into(),
    ];
    spawner.args(&args);
    info!("Git args: {:?}", &args);
    let git_exit_code = spawner.spawn(shutdown_token).await?;
    if git_exit_code != 0 {
        warn!("Git subprocess exited with code {git_exit_code}");
        return Err(Status::internal(format!(
            "Git subprocess exited with code {git_exit_code}"
        )));
    }
    Ok(())
}

pub async fn git_fetch_bundle<Req: RequestWithRepo>(
    config: Arc<Config>,
    req: Req,
    bundle_path: PathBuf,
    shutdown_token: CancellationToken,
    metadata: &MetadataMap,
) -> Result<(), Status> {
    // call git fetch on the bundle, using the in-memory remote trick
    let git_config = vec![
        ("remote.inmemory.url".into(), bundle_path.into()),
        // Comment from Gitaly 17.8:
        //
        //   Starting in Git version 2.46.0, executing git-fetch(1) on a bundle
        //   performs fsck checks when `transfer.fsckObjects` is enabled.
        //   Prior to this, this configuration was always ignored and fsck checks
        //   were not run.
        //   Unfortunately, fsck message severity configuration is ignored by
        //   Git only for bundle fetches. Until this is supported by
        //   Git, disable `transfer.fsckObjects` so bundles containing fsck
        //   errors can continue to be fetched.
        //   This matches behavior prior to Git version 2.46.0.
        ("transfer.fsckObjects".into(), "false".into()),
        // Comment from Gitaly 17.8:
        //
        //   Git is so kind to point out that we asked it to not show forced updates
        //   by default, so we need to ask it not to do that.
        ("advice.fetchShowForcedUpdates".into(), "false".into()),
    ];
    let mut spawner = RepoProcessSpawnerTemplate::new_git(
        config,
        req,
        metadata,
        git_config,
        default_repo_spec_error_status,
    )
    .await?
    .git_spawner();
    // TODO support `update_head`.
    //
    // Gitaly uses the `MirroRefSpec`: "+refs/*:refs/*", but it look like
    // our simpler refspec below always includes HEAD (and any other symref, to be
    // fair, so they have to update HEAD separately, and it is a pain to
    // find in the bundle etc.
    // For the current purposes (backup/restore of auxiliary Git repositories),
    // we do not care, but otherwise playing
    // with a negative refspec for HEAD when we do not want to update it would
    // probably be the way to go.
    let args: Vec<OsString> = vec![
        "fetch".into(),
        "--quiet".into(),
        "--atomic".into(),
        "--force".into(),
        "inmemory".into(), // name of Git remote
        "+*:*".into(),     // refspec to update all refs from the remote (the bundle)
    ];
    spawner.args(&args);

    let git_exit_code = spawner.spawn(shutdown_token).await?;
    if git_exit_code != 0 {
        warn!("Git subprocess exited with code {git_exit_code}");
        return Err(Status::internal(format!(
            "Git subprocess exited with code {git_exit_code}"
        )));
    }
    Ok(())
}

pub async fn hg_unbundle<Req: RequestHgSpawnable>(
    config: Arc<Config>,
    req: Req,
    bundle_path: PathBuf,
    shutdown_token: CancellationToken,
    metadata: &MetadataMap,
    skip_gl_hooks: Option<bool>,
) -> Result<(), Status> {
    let mut spawner =
        RepoProcessSpawnerTemplate::new_hg(config, req, metadata, default_repo_spec_error_status)
            .await?
            .hg_spawner();

    let args: Vec<OsString> = vec!["unbundle".into(), bundle_path.into()];
    spawner.args(&args);
    if let Some(skip) = skip_gl_hooks {
        spawner.env(
            "HEPTAPOD_SKIP_ALL_GITLAB_HOOKS",
            if skip { "yes" } else { "no" },
        )
    }
    info!("Mercurial args: {:?}", &args);
    let hg_exit_code = spawner.spawn(shutdown_token).await?;
    if hg_exit_code != 0 {
        let msg = format!("Mercurial subprocess exited with code {hg_exit_code}");
        warn!(msg);
        return Err(Status::internal(msg));
    }
    Ok(())
}

pub struct CreateBundleTracingRequest<'a>(pub &'a CreateBundleRequest);

impl Debug for CreateBundleTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("CreateBundle")
            .field("repository", &self.0.repository)
            .finish()
    }
}

impl RequestWithRepo for CreateBundleRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

pub struct CreateRepositoryFromBundleTracingRequest<'a>(pub &'a CreateRepositoryFromBundleRequest);

impl Debug for CreateRepositoryFromBundleTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("CreateRepositoryFromBundle")
            .field("repository", &self.0.repository)
            .finish()
    }
}

impl RequestWithRepo for CreateRepositoryFromBundleRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestHgSpawnable for CreateRepositoryFromBundleRequest {
    fn user_ref(&self) -> Option<&User> {
        None // no user field in this request
    }
}
impl RequestWithBytesChunk for CreateRepositoryFromBundleRequest {
    fn bytes_chunk(&self) -> &[u8] {
        &self.data
    }
}
impl RequestWithRepo for FetchBundleRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}
impl RequestHgSpawnable for FetchBundleRequest {
    fn user_ref(&self) -> Option<&User> {
        None
    }
}
