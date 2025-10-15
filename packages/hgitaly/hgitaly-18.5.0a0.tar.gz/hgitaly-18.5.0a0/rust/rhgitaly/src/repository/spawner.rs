// Copyright 2024 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
//! Utilities to spawn and manage specialized subprocesses, in particular involving repositories
use futures_core::Future;
use std::ffi::{OsStr, OsString};
use std::marker::Send;
use std::os::unix::ffi::OsStringExt;
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;

use tokio::io::{AsyncBufReadExt, AsyncReadExt, BufReader};
use tokio::process::{ChildStdout, Command};
use tokio::select;
use tokio::sync::mpsc::{self, Sender};
use tokio::time::{sleep, Duration};
use tokio_util::sync::CancellationToken;
use tonic::metadata::MetadataMap;
use tonic::Status;
use tracing::{debug, info, warn};

use hg::repo::Repo;

use super::{
    checked_git_repo_path, checked_repo_path, load_repo_at_and_then, RepoSpecError, RequestWithRepo,
};
use crate::config::Config;
use crate::gitaly::{Repository, User};
use crate::metadata::{
    get_boolean_md_value, ACCEPT_MR_IID_KEY, HG_GIT_MIRRORING_MD_KEY, NATIVE_PROJECT_MD_KEY,
    SKIP_HOOKS_MD_KEY,
};
use crate::process;
use crate::ssh::SSHOptions;
use crate::streaming::WRITE_BUFFER_SIZE;

/// Serialize booleans in the same way as was done by heptapod-rails.
///
/// The `"true"` and `"false"` strings would work the same way, but would
/// create differences in `hg config` output, as it just repeats the configuration
/// as it was passed.
fn hg_config_bool2str(b: bool) -> &'static str {
    if b {
        "yes"
    } else {
        "no"
    }
}

/// This enum to specify how streams of bytes should be chunkded for internal transmission
///
/// the `Lines` variant means to cut them at line endings, whereas the `Binary ` variant means
/// to cut in chunks of the given size.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum BytesChunking {
    Lines,
    Binary(usize),
}

/// Trait for requests whose treatment involves spawning a hg child process
///
/// It provides the needed uniformity for [`HgSpawner`]
pub trait RequestHgSpawnable: RequestWithRepo {
    /// Grab a reference to the [`User`] field from the request.
    ///
    /// Like all submessages, the user is optional if it is indeed part of protocol.
    ///
    /// In the case of read-only gRPC methods, it is totally acceptable not to have
    /// any [`User`] field, whence the blanket implementation returning `None`.
    fn user_ref(&self) -> Option<&User> {
        None
    }
}

pub struct RepoProcessSpawnerTemplate {
    config: Arc<Config>,
    common_args: Vec<OsString>,
    common_env: Vec<(OsString, OsString)>,
    repo_path: PathBuf,
}

pub struct RepoProcessSpawner {
    config: Arc<Config>,
    cmd: Command,
    stdout_tx: Option<Sender<Vec<u8>>>,
    stdout_chunking: BytesChunking,
    repo_path: PathBuf,
    /// Used for logging purposes, e.g., `Mercurial`
    logging_name: &'static str,
}

impl RepoProcessSpawnerTemplate {
    /// Reusable preparations to instantiate [`RepoProcessSpawner`] objects for Mercurial
    ///
    /// If the request specifies an [`User`], all necessary environment variables are given to
    /// the child process so that repository mutation on behalf of the given user can work.
    /// This is similar to the legacy code in the Rails application. A difference lies in the way
    /// the (usually necessary) `HGRCPATH` environment variable is given to the child process:
    /// nothing special is done about it, hence it is assumed it is set on the whole RHGitaly
    /// service.
    pub async fn new_hg<Req: RequestHgSpawnable>(
        config: Arc<Config>,
        request: Req,
        metadata: &MetadataMap,
        repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static + Copy,
    ) -> Result<Self, Status> {
        let (gitaly_repo, repo_path) = checked_repo_path(&config, request.repository_ref())
            .await
            .map_err(repo_spec_error_status)?;
        Self::new_hg_at_path(config, repo_path, gitaly_repo, request.user_ref(), metadata).await
    }

    pub async fn new_hg_at_path(
        config: Arc<Config>,
        cwd: PathBuf,
        gitaly_repo: &Repository,
        opt_user: Option<&User>,
        metadata: &MetadataMap,
    ) -> Result<Self, Status> {
        let mut common_args = Vec::new();
        let mut common_env: Vec<(OsString, OsString)> = vec![
            (
                "GL_REPOSITORY".into(),
                gitaly_repo.gl_repository.clone().into(),
            ),
            // same hardcoding as in Gitaly
            ("GL_PROTOCOL".into(), "web".into()),
        ];

        debug!("Invocation metadata: {:?}", &metadata);
        let mirroring = get_boolean_md_value(metadata, HG_GIT_MIRRORING_MD_KEY, false);
        let native = get_boolean_md_value(metadata, NATIVE_PROJECT_MD_KEY, false);
        let skip_gl_hooks = get_boolean_md_value(metadata, SKIP_HOOKS_MD_KEY, false);

        common_args.push("--config".into());
        common_args.push(format!("heptapod.native={}", hg_config_bool2str(native)).into());
        common_args.push("--config".into());
        common_args.push(format!("heptapod.no-git={}", !mirroring).into());

        if skip_gl_hooks {
            common_env.push(("HEPTAPOD_SKIP_ALL_GITLAB_HOOKS".into(), "yes".into()));
        }

        if let Some(user) = opt_user {
            common_env.push(("HEPTAPOD_USERINFO_GL_ID".into(), user.gl_id.clone().into()));
            common_env.push((
                "HEPTAPOD_USERINFO_USERNAME".into(),
                user.gl_username.clone().into(),
            ));
            common_env.push((
                "HEPTAPOD_USERINFO_NAME".into(),
                OsString::from_vec(user.name.clone()),
            ));
            common_env.push((
                "HEPTAPOD_USERINFO_EMAIL".into(),
                OsString::from_vec(user.email.clone()),
            ));

            if let Some(v) = metadata.get(ACCEPT_MR_IID_KEY) {
                if let Ok(iid) = v.to_str() {
                    common_env.push(("HEPTAPOD_ACCEPT_MR_IID".into(), iid.into()));
                }
            }
        }

        Ok(Self {
            common_args,
            common_env,
            config,
            repo_path: cwd,
        })
    }

    /// This variant on [`new_git`] interprets the repository on the incoming request as
    /// the corresponding auxiliary Git repository.
    ///
    /// In other words, it keeps the `.git` and inserts the hg-git area prefix.
    pub async fn new_aux_git<Req: RequestWithRepo>(
        config: Arc<Config>,
        request: Req,
        metadata: &MetadataMap,
        git_config: Vec<(OsString, OsString)>,
        repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static + Copy,
    ) -> Result<Self, Status> {
        let (_gitaly_repo, repo_path) =
            checked_git_repo_path(&config, request.repository_ref(), true)
                .await
                .map_err(repo_spec_error_status)?;
        Self::new_git_at_path(config, repo_path, metadata, git_config).await
    }

    /// This variant on [`new_git`] interprets the repository on the incoming request litteraly.
    pub async fn new_git<Req: RequestWithRepo>(
        config: Arc<Config>,
        request: Req,
        metadata: &MetadataMap,
        git_config: Vec<(OsString, OsString)>,
        repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static + Copy,
    ) -> Result<Self, Status> {
        let (_gitaly_repo, repo_path) =
            checked_git_repo_path(&config, request.repository_ref(), false)
                .await
                .map_err(repo_spec_error_status)?;
        Self::new_git_at_path(config, repo_path, metadata, git_config).await
    }

    /// Reusable preparations to instantiate [`RepoProcessSpawner`] objects for Git.
    ///
    /// # Arguments
    ///
    /// Some arguments may not be used yet, but have a good chance of being useful at some point.
    ///
    /// - `git_config` allows to set transient configuration as in `git-config(1)` via environment
    ///   variables, so that it can be used for sensitive value. Ownership is taken for simplicity
    ///   (beware of the global counter if wanting to change that).
    pub async fn new_git_at_path(
        config: Arc<Config>,
        repo_path: PathBuf,
        _metadata: &MetadataMap,
        git_config: Vec<(OsString, OsString)>,
    ) -> Result<Self, Status> {
        let common_args = Vec::new();
        let mut common_env: Vec<(OsString, OsString)> = vec![];
        if !git_config.is_empty() {
            common_env.push((
                "GIT_CONFIG_COUNT".into(),
                git_config.len().to_string().into(),
            ));
        }
        for (i, (key, value)) in git_config.into_iter().enumerate() {
            common_env.push((format!("GIT_CONFIG_KEY_{i}").into(), key));
            common_env.push((format!("GIT_CONFIG_VALUE_{i}").into(), value));
        }

        Ok(Self {
            common_args,
            common_env,
            config,
            repo_path,
        })
    }

    pub fn with_git_ssh_options(mut self, opts: &SSHOptions) -> Self {
        self.common_env
            .push(("GIT_SSH_COMMAND".into(), opts.ssh_command()));
        self
    }

    /// Adds arguments to this template
    ///
    /// On top of the structural arguments for proper Mercurial or Git invocation, it happens
    /// that callers have to perform repetitive tasks, hence with a common subset of arguments
    pub fn add_arg(&mut self, arg: OsString) {
        self.common_args.push(arg)
    }

    pub fn hg_spawner(&self) -> RepoProcessSpawner {
        let mut cmd = Command::new(&self.config.hg_executable);
        cmd.args(&self.common_args);
        cmd.envs(self.common_env.iter().map(|item| (&item.0, &item.1)));
        cmd.current_dir(&self.repo_path);

        RepoProcessSpawner {
            cmd,
            config: self.config.clone(),
            repo_path: self.repo_path.clone(),
            stdout_tx: None,
            stdout_chunking: BytesChunking::Lines,
            logging_name: "Mercurial",
        }
    }

    pub fn git_spawner(&self) -> RepoProcessSpawner {
        let mut cmd = Command::new(&self.config.git_executable);
        cmd.args(&self.common_args);
        cmd.envs(self.common_env.iter().map(|item| (&item.0, &item.1)));
        cmd.current_dir(&self.repo_path);

        RepoProcessSpawner {
            cmd,
            config: self.config.clone(),
            repo_path: self.repo_path.clone(),
            stdout_tx: None,
            stdout_chunking: BytesChunking::Lines,
            logging_name: "Git",
        }
    }

    /// Spawn a `hg log` subprocess on the given revsec, return a vector
    /// of Node Ids (hexadecimal representation)
    pub async fn hg_log(
        &self,
        revset: &OsStr,
        cancel_token: CancellationToken,
        limit: Option<usize>,
    ) -> Result<Vec<String>, Status> {
        let mut spawner = self.hg_spawner();

        let mut args: Vec<OsString> = vec![
            "log".into(),
            "-r".into(),
            revset.to_owned(),
            "-T{node}\\n".into(),
        ];
        if let Some(limit) = limit {
            args.push(format!("-l{}", limit).into())
        }
        let (stdout_tx, mut stdout_rx) = mpsc::channel(3);
        spawner.capture_stdout(stdout_tx, BytesChunking::Lines);
        spawner.args(&args);
        let spawned = spawner.spawn(cancel_token);
        let mut changesets = Vec::new();
        let read_stdout = async {
            while let Some(mut line) = stdout_rx.recv().await {
                if line.last() == Some(&b'\n') {
                    line.pop();
                }
                match String::from_utf8(line) {
                    Ok(changeset) => changesets.push(changeset),
                    Err(e) => {
                        // actually returning an Err from there is really painful and this can
                        // happen in pratice only if `hg` is very buggy (been replaced by something
                        // else?).
                        warn!(
                            "Unexpected non utf-8 `hg log -T '{{node}}\\n'` output: {:?}",
                            e.as_bytes()
                        )
                    }
                };
            }
        };
        let spawn_result = tokio::join!(spawned, read_stdout).0;
        let hg_exit_code = spawn_result?;
        if hg_exit_code != 0 {
            return Err(Status::internal(format!(
                "Mercurial subprocess exited with code {}",
                hg_exit_code
            )));
        }
        Ok(changesets)
    }
}

impl RepoProcessSpawner {
    /// Object to spawn a `hg` child process on the repository specified by the request
    ///
    /// First repository loading is similar to [`load_repo_and_then`], executing the provided
    /// `before_spawn` closure on the repository and the prepared [`Command`].
    ///
    /// The entire environment of the current process is passed down to the child process.
    ///
    /// The path to the `hg` executable is taken from `Config`.
    pub async fn prepare_hg<Req: RequestHgSpawnable>(
        config: Arc<Config>,
        request: Req,
        metadata: &MetadataMap,
        repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static + Copy,
    ) -> Result<Self, Status> {
        Ok(
            RepoProcessSpawnerTemplate::new_hg(config, request, metadata, repo_spec_error_status)
                .await?
                .hg_spawner(),
        )
    }

    /// Convenience method similar to [`crate::repository::load_repo_and_then`]
    ///
    /// It is typically used to gather information from the repository to tweak arguments.
    ///
    /// Compared to calling `load_repo_and_then`, it avoids redoing some checks already done
    /// and passing some arguments again. Also, since the closure does not take a request
    /// argument, it also prevents some unnecessary cloning (just extract the needed information
    /// from the request in the caller task before hand).
    pub fn hg_load_repo_and_then<Res: Send + 'static>(
        &self,
        and_then: impl FnOnce(Repo) -> Result<Res, Status> + Send + 'static,
    ) -> impl Future<Output = Result<Res, Status>> {
        load_repo_at_and_then(self.config.clone(), self.repo_path.clone(), and_then)
    }

    /// Configure for stdout capture.
    ///
    /// With this, the child process standard output will be captured and either sent line by line
    /// if `chunk_size` is `None` or in chunks (suitable for binary output without a temporary file)
    /// otherwise.
    ///
    /// The line by line use case can be useful to gather information about what happened, although
    /// in general, other means of obtaining information should be preferred if available.
    pub fn capture_stdout(&mut self, tx: Sender<Vec<u8>>, chunking: BytesChunking) {
        self.stdout_tx = Some(tx);
        self.stdout_chunking = chunking
    }

    /// Set child process arguments
    pub fn args<Arg: AsRef<OsStr>>(&mut self, args: impl IntoIterator<Item = Arg>) {
        self.cmd.args(args);
    }

    /// Set environment variable to child process
    ///
    /// Being done after Command creation, this can override existing variables
    pub fn env<K: AsRef<OsStr>, V: AsRef<OsStr>>(&mut self, key: K, val: V) {
        self.cmd.env(key, val);
    }

    /// Run the subprocess asynchronously.
    ///
    /// The entire environment of the current process is passed down to the child process. Notably
    /// this is how `HGRCPATH` is supposed to be set (see comment about that in
    /// [prepare](`Self::prepare`)).
    pub async fn spawn(mut self, shutdown_token: CancellationToken) -> Result<i32, Status> {
        let logging_name = self.logging_name;
        if self.stdout_tx.is_some() {
            self.cmd.stdout(Stdio::piped());
        }
        debug!("Spawning command {:#?}", self.cmd);
        let shutdown_token = shutdown_token.clone();
        let mut subprocess = self.cmd.spawn().map_err(|e| {
            Status::internal(format!("Error spawning {logging_name} subprocess: {e}"))
        })?;

        let stdout_and_tx = self.stdout_tx.take().map(|stdtx| {
            (
                subprocess
                    .stdout
                    .take()
                    .expect("Spawned process has no stdout (already been taken?)"),
                stdtx,
            )
        });

        let token = CancellationToken::new();
        let _drop_guard = token.clone().drop_guard();

        let (tx, mut rx) = mpsc::channel(1);
        tokio::spawn(async move {
            let subprocess_status = select! {
                res = subprocess.wait() => res.map_err(|e| {
                    Status::internal(
                        format!("Error waiting for {logging_name} subprocess: {e}"))
                    }),
                _ = token.cancelled() => {
                    // TODO logs from a subthread are not in the context of the request
                    // hence will turn pretty useless without correlation_id etc.
                    info!("Task cancelled, terminating {logging_name} child process with SIGTERM");
                    process::terminate(subprocess).await;
                    Err(Status::cancelled("Task dropped, probably due to \
                                           client-side cancellation"))
                },
                _ = shutdown_token.cancelled() => {
                    warn!("General shutdown required, terminating {logging_name} child \
                           process with SIGTERM");
                    process::terminate(subprocess).await;
                    Err(Status::unavailable("RHGitaly server is shutting down"))
                },
            };
            tx.send(subprocess_status).await
        });

        let subprocess_status = if let Some((stdout, stdout_tx)) = stdout_and_tx {
            let mut reader = BufReader::new(stdout);

            async move {
                let subprocess_status: Result<_, Status>;
                let (in_lines, buf_capa) = match self.stdout_chunking {
                    BytesChunking::Lines => (true, *WRITE_BUFFER_SIZE),
                    BytesChunking::Binary(size) => (false, size),
                };
                let mut buf = Vec::with_capacity(buf_capa);
                loop {
                    select! {
                        maybe_bytes = read_line_or_chunk(&mut reader, &mut buf, in_lines) => {
                            match maybe_bytes {
                                Ok(0) => {
                                    // we can be reading much faster than the child process
                                    // outputs data, especially if it is terminating, let us relax
                                    // that a bit (seen about 1.5ms for termination in case of a
                                    // tiny Git bundle)
                                    sleep(Duration::from_millis(1)).await;
                                }
                                Ok(n) => {
                                    debug!("read {n} bytes (in_lines={in_lines}) \
                                            from child stdout");
                                    if buf.capacity() == buf.len() || in_lines {
                                        // it seems that a vector clone has capacity==length
                                        // (perfect in this case)
                                        if stdout_tx.send(buf.clone()).await.is_err() {
                                            // we have no other choice than ignoring it,
                                            // although it is probably symptom
                                            // of some really unexpected problem
                                            warn!("Subprocess stdout receiver already dropped!")
                                        }
                                        buf.clear();
                                    }
                                },
                                Err(e) => {
                                    // probably the error is not due to stdout already closed, but
                                    // in any case, we must let the other arm of `select!` run so
                                    // that the process is eventually reaped
                                    warn!("Got error reading from child process stdout: {}", e)
                                }
                            }
                        },
                        res = rx.recv() => {
                            debug!("Process finished");
                            subprocess_status = res.unwrap_or_else(|| Err(Status::internal(
                                "Channel closed before sending back {logging_name} \
                                 subprocess status")));
                            break;
                        }
                    }
                }

                // The child process being done, let's read remaining data in the pipe
                // (or all buffers) if any, not looking for EOL in any case
                if let Ok(n) = reader.read_buf(&mut buf).await {
                    if n != 0 {
                        debug!("Read {n} bytes from subprocess output after completion");
                    }
                }
                if !buf.is_empty() && stdout_tx.send(buf).await.is_err() {
                    warn!("Subprocess stdout receiver already dropped!")
                }
                subprocess_status
            }
            .await?
        } else {
            rx.recv().await.unwrap_or_else(|| {
                Err(Status::internal(
                    "Channel closed before sending back {logging_name} subprocess status",
                ))
            })?
        };

        let res = subprocess_status.code().ok_or(Status::internal(
            "{logging_name} subprocess killed or stopped by signal",
        ));
        info!("Returning {res:?}");
        res
    }
}

/// This is to be put in a `select!` with the process termination, otherwise it does not end.
async fn read_line_or_chunk(
    reader: &mut BufReader<ChildStdout>,
    buf: &mut Vec<u8>,
    in_lines: bool,
) -> Result<usize, std::io::Error> {
    if in_lines {
        reader.read_until(b'\n', buf).await
    } else {
        reader.read_buf(buf).await
    }
}

#[cfg(test)]
mod tests {

    use super::*;
    use crate::gitaly::{Repository, ServerInfoRequest};

    impl RequestWithRepo for ServerInfoRequest {
        fn repository_ref(&self) -> Option<&Repository> {
            None // would not be acceptable in main code
        }
    }
    impl RequestHgSpawnable for ServerInfoRequest {}

    #[test]
    fn test_request_hg_spawnable() {
        assert!(ServerInfoRequest::default().user_ref().is_none());
    }
}
