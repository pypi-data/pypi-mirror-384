// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::fmt;
use std::future::Future;
use std::io::ErrorKind;
use std::marker::Send;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use futures::executor::block_on;
use tokio::fs;
use tokio::sync::mpsc::{self};
use tokio::task::JoinError;
use tokio_stream::wrappers::ReceiverStream;
use tokio_stream::StreamExt;
use tonic::codegen::BoxStream;
use tonic::{Response, Status, Streaming};
use tracing::span::Span;

use hg::repo::{Repo, RepoError};
use hg::revlog::changelog::Changelog;

use super::config::Config;
use super::gitaly::Repository;

use super::streaming::{empty_response_stream, BlockingResponseSender};

pub mod spawner;

pub const AUX_GIT_REPOS_RELATIVE_DIR: &str = "+hgitaly/hg-git";

pub const TMP_RELATIVE_DIR: &str = "+hgitaly/tmp";

/// Represent errors that are due to a wrong repository specification.
///
/// In terms of gRPC methods, the specifications is usually enclosed in  a [`Repository`] message
/// and these errors are considered to be client errors.
#[derive(Debug, PartialEq, Eq)]
pub enum RepoSpecError {
    MissingSpecification,
    UnknownStorage(String),
    RepoNotFound(PathBuf),
    AlreadyExists(PathBuf),
}

/// Represent errors loading a repository (bad specification or internal errors)
#[derive(Debug, derive_more::From)] // TODO add PartialEq, but do it in core for RepoError first
pub enum RepoLoadError {
    #[from]
    SpecError(RepoSpecError),
    LoadError(RepoError),
}

impl From<RepoError> for RepoLoadError {
    fn from(value: RepoError) -> Self {
        if let RepoError::NotFound { at } = value {
            return Self::SpecError(RepoSpecError::RepoNotFound(at));
        }
        Self::LoadError(value)
    }
}

/// Default conversion of ['RepoSpecError'] into a gRPC ['Status']
///
/// This function does not care to precisely match the error details, focusing on the error
/// codes instead.
///
/// The resulting codes match the most common behaviour of Gitaly, which actually behaves more
/// and more like this with time (e.g., as internal Git error get catched and handled).
pub fn default_repo_spec_error_status(err: RepoSpecError) -> Status {
    match err {
        RepoSpecError::MissingSpecification => Status::invalid_argument("repository not set"),
        RepoSpecError::UnknownStorage(storage) => Status::invalid_argument(format!(
            "GetStorageByName: no such storage: \"{}\"",
            storage
        )),
        RepoSpecError::RepoNotFound(at) => {
            Status::not_found(format!("repository at \"{}\" not found", at.display()))
        }
        RepoSpecError::AlreadyExists(_) => {
            Status::already_exists("creating repository: repository exists already")
        }
    }
}

pub fn is_repo_aux_git<Req: RequestWithRepo>(req: &Req) -> bool {
    if let Some(repo) = req.repository_ref() {
        repo.relative_path.starts_with(AUX_GIT_REPOS_RELATIVE_DIR)
    } else {
        false
    }
}

pub fn aux_git_to_main_hg<Req: RequestWithRepo>(req: &Req) -> Option<&str> {
    if let Some(repo) = req.repository_ref() {
        let rpath = &repo.relative_path;
        if rpath.starts_with(AUX_GIT_REPOS_RELATIVE_DIR) {
            Some(&rpath[AUX_GIT_REPOS_RELATIVE_DIR.len() + 1..])
        } else {
            None
        }
    } else {
        None
    }
}

fn check_storage(repo: &Repository) -> Result<(), RepoSpecError> {
    if repo.storage_name.rsplit(':').next() == Some("default") {
        Ok(())
    } else {
        Err(RepoSpecError::UnknownStorage(repo.storage_name.clone()))
    }
}

pub fn repo_hg_relpath(repo: &Repository) -> String {
    match repo.relative_path.strip_suffix(".git") {
        Some(stripped) => stripped.to_owned() + ".hg",
        None => repo.relative_path.to_owned(),
    }
}

pub fn repo_path(config: &Config, repo: &Repository) -> Result<PathBuf, RepoSpecError> {
    check_storage(repo)?;

    let root = &config.repositories_root;

    // TODO forbid climbing up (same in Python, will be necessary for HGitaly3, even
    // though clients are deeply trusted.
    Ok(root.join(repo_hg_relpath(repo)))
}

pub fn git_repo_path(
    config: &Config,
    repo: &Repository,
    divert_aux_area: bool,
) -> Result<PathBuf, RepoSpecError> {
    check_storage(repo)?;

    let mut path = if divert_aux_area {
        config.repositories_root.join(AUX_GIT_REPOS_RELATIVE_DIR)
    } else {
        config.repositories_root.clone()
    };

    match repo.relative_path.strip_suffix(".hg") {
        Some(stripped) => path.push(&(stripped.to_owned() + ".git")),
        None => path.push(&repo.relative_path),
    };

    // TODO forbid climbing up (same in Python, will be necessary for HGitaly3, even
    // though clients are deeply trusted.
    Ok(path)
}

/// Ensure existence of temporary directory for given storage and return path
pub async fn ensure_tmp_dir(
    config: &Config,
    repository: Option<&Repository>,
) -> Result<PathBuf, Status> {
    if let Some(repo) = repository {
        check_storage(repo)
    } else {
        Err(RepoSpecError::MissingSpecification)
    }
    .map_err(default_repo_spec_error_status)?;

    let path = config.repositories_root.join(TMP_RELATIVE_DIR);
    fs::create_dir_all(&path).await.map_err(|e| {
        Status::internal(format!(
            "Could not ensure existence of tmp directory at {}: {}",
            path.display(),
            e
        ))
    })?;
    Ok(path)
}

/// Default gRPC error ['Status'] for repository not found.
///
/// To be used if repository path does not exist on disk.
pub fn default_repo_not_found_error_status(path: &Path) -> Status {
    Status::not_found(format!(
        "Mercurial repository at {} not found",
        path.display()
    ))
}

pub async fn checked_repo_path<'a>(
    config: &Config,
    gl_repo: Option<&'a Repository>,
) -> Result<(&'a Repository, PathBuf), RepoSpecError> {
    let repo = gl_repo
        .as_ref()
        .ok_or(RepoSpecError::MissingSpecification)?;
    let path = repo_path(config, repo)?;
    if match fs::metadata(&path).await {
        Ok(md) => md.is_dir(),
        Err(_) => false,
    } {
        return Ok((repo, path));
    }
    Err(RepoSpecError::RepoNotFound(path))
}

/// Checks that repo is specified, and that there is nothing at its path
pub async fn checked_repo_path_for_creation<'a>(
    config: &Config,
    gl_repo: Option<&'a Repository>,
) -> Result<(&'a Repository, PathBuf), RepoSpecError> {
    let repo = gl_repo
        .as_ref()
        .ok_or(RepoSpecError::MissingSpecification)?;
    let path = repo_path(config, repo)?;
    if fs::metadata(&path).await.is_ok() {
        return Err(RepoSpecError::AlreadyExists(path));
    }
    Ok((repo, path))
}

pub async fn checked_git_repo_path<'a>(
    config: &Config,
    gl_repo: Option<&'a Repository>,
    divert_aux_area: bool,
) -> Result<(&'a Repository, PathBuf), RepoSpecError> {
    let repo = gl_repo
        .as_ref()
        .ok_or(RepoSpecError::MissingSpecification)?;
    let path = git_repo_path(config, repo, divert_aux_area)?;
    if match fs::metadata(&path).await {
        Ok(md) => md.is_dir(),
        Err(_) => false,
    } {
        return Ok((repo, path));
    }
    Err(RepoSpecError::RepoNotFound(path))
}

pub async fn checked_git_repo_path_for_creation<'a>(
    config: &Config,
    gl_repo: Option<&'a Repository>,
    divert_aux_area: bool,
) -> Result<(&'a Repository, PathBuf), RepoSpecError> {
    let repo = gl_repo
        .as_ref()
        .ok_or(RepoSpecError::MissingSpecification)?;
    let path = git_repo_path(config, repo, divert_aux_area)?;
    if fs::metadata(&path).await.is_ok() {
        return Err(RepoSpecError::AlreadyExists(path));
    }
    Ok((repo, path))
}

/// Return a path to virtual filesystem for the repository store.
///
/// As of this writing, this is nothing but a [`Path`], but it could become something
/// more advanced in the future (perhaps not as much as `hg_core` `Vfs` type, though).
///
/// Parameter `repo` is an `Option`, so that a service method can pass directly
/// something like `&request.repository`, with `None` giving rise to the natural
/// `MissingSpecification` error.
///
/// If the repository is not found on disc, the appropriate error is also returned.
pub async fn repo_store_vfs(
    config: &Config,
    repo: &Option<Repository>,
) -> Result<PathBuf, RepoSpecError> {
    repo_ref_store_vfs(config, repo.as_ref()).await
}

/// Same as [`repo_store_vfs`], returning the ordinary VFS (parent of store)
pub async fn repo_vfs(
    config: &Config,
    repo: &Option<Repository>,
) -> Result<PathBuf, RepoSpecError> {
    repo_ref_vfs(config, repo.as_ref()).await
}

/// Same as [`repo_store_vfs`], taking a `Option<&Repository>` instead.
///
/// When one only has an `Option<&Repository>`, it is usually due to the request
/// beeng bound as `RequestWithRepo`. One should then use the trait method.
async fn repo_ref_store_vfs(
    config: &Config,
    repo: Option<&Repository>,
) -> Result<PathBuf, RepoSpecError> {
    let root = checked_repo_path(config, repo).await?.1;
    Ok(root.join(".hg/store"))
}

/// Same as [`repo_ref_store_vfs`], for the main VFS
async fn repo_ref_vfs(
    config: &Config,
    repo: Option<&Repository>,
) -> Result<PathBuf, RepoSpecError> {
    let root = checked_repo_path(config, repo).await?.1;
    Ok(root.join(".hg"))
}

/// Read repository VFS requirements and tell whether one fulfills the given condition
///
/// Note that some requirements are in the 'store` VFS (most of those that
/// will be of interest with RHGitaly), while some others are on the 'working dir' VFS.
///
/// Inspired by [`hg::requirements::load`] with thw following differences:
///
/// - we do not need to build a full `HashSet`, just to check a single value. If the caller
///   needs to use the requirements repeatedly, we will provide a more general parsing function
///   with storable results.
/// - this is async
pub async fn has_requirement_with(
    vfs: &Path,
    condition: impl FnMut(&[u8]) -> bool,
) -> Result<bool, Status> {
    let path = vfs.join("requires"); // TODO const
    let reqs = match fs::read(&path).await {
        Ok(bytes) => bytes,
        Err(e) => {
            if e.kind() == ErrorKind::NotFound {
                return Ok(false);
            } else {
                return Err(Status::internal(format!(
                    "Could not open requirements at {}: {}",
                    path.display(),
                    e
                )));
            }
        }
    };
    Ok(reqs.split(|b| *b == b'\n').any(condition))
}

/// Return `Status::Unimplemented` if the repo has the `largefiles` requirement.
pub async fn unimplemented_if_largefiles(
    config: &Config,
    repo: &Option<Repository>,
) -> Result<(), Status> {
    let store_vfs = repo_store_vfs(config, repo)
        .await
        .map_err(default_repo_spec_error_status)?;
    if has_requirement_with(&store_vfs, |req| req == b"largefiles").await? {
        // TODO const
        return Err(Status::unimplemented("largefiles repo requirement"));
    };
    // The requires file can be in the working dir vfs (probably older
    // repositories, that don't have any .hg/store/requires)
    if let Some(root_vfs) = store_vfs.parent() {
        if has_requirement_with(root_vfs, |req| req == b"largefiles").await? {
            // TODO const
            return Err(Status::unimplemented("largefiles repo requirement"));
        }
    }
    Ok(())
}

pub fn load_repo_at(config: &Config, repo_path: PathBuf) -> Result<Repo, RepoError> {
    // TODO better to use Repo::new_at_path, but it is private
    // (Repo::find does verifications that are useless to us.
    // At least it does not try to climb up when passed an explicit path)
    Repo::find(&config.hg_core_config, Some(repo_path))
}

pub fn load_repo(config: &Config, opt_repo: Option<&Repository>) -> Result<Repo, RepoLoadError> {
    Ok(load_repo_at(
        config,
        repo_path(config, opt_repo.ok_or(RepoSpecError::MissingSpecification)?)?,
    )?)
}

/// Trait for requests with a repository field
///
/// It provides the needed uniformity for methods such as [`load_repo_and_stream`]
pub trait RequestWithRepo: Send + 'static {
    /// Grab a reference to the [`Repository`] field from the request.
    ///
    /// Like all submessages, the repository is optional.
    fn repository_ref(&self) -> Option<&Repository>;

    /// Return the repositoru store VFS.
    fn repo_store_vfs(
        &self,
        config: &Config,
    ) -> impl Future<Output = Result<PathBuf, RepoSpecError>> {
        repo_ref_store_vfs(config, self.repository_ref())
    }
}

/// Trait for streaming requests with a bytes field
///
/// The Gitaly convention is that streaming requests provide full arguments
/// only in the first request, and then streaming is about one field. In this
/// case, the streamed data is just bytes, but we abstract over the field name.
pub trait RequestWithBytesChunk: Send + 'static {
    /// Retrieve the bytes chunk
    fn bytes_chunk(&self) -> &[u8];
}

/// Load a repository and initiate streaming responses
///
/// This setups the `mpsc` channel expected by Tonic and spawns a blocking task (typically run
/// in a separate thread) loads the repository, and passes over the repository and the transmitting
/// end of the channel to the caller supplied closure.
///
/// The `and_then` closure must perform its streaming by sending `Result<Resp, Status>` values
/// on the channel, using the provided [`BlockingResponseSender`].
///
/// If the repository loading fails, the appropriate gRPC error response is sent over
/// or logged if sending is not possible.
///
/// Because Gitaly's error responses are not uniform, and we want to match them closely,
/// ethe caller has to supply a callable for conversion of [`RepoSpecError`] to the appropriate
/// [`Status`]. The [`default_repo_spec_error_status`] function can be used in the majority of
/// cases and serve as an example for other cases.
pub fn load_repo_and_stream<Req: RequestWithRepo, Resp: fmt::Debug + Send + 'static>(
    config: Arc<Config>,
    request: Req,
    repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static,
    and_then: impl FnOnce(Req, Repo, BlockingResponseSender<Resp>) + Send + 'static,
) -> Result<Response<BoxStream<Resp>>, Status> {
    // no point having channel capacity for several messages, since `blocking_send` is the only
    // way to use it.
    let (tx, rx) = mpsc::channel(1);
    let current_span = Span::current();
    tokio::task::spawn_blocking(move || {
        let btx: BlockingResponseSender<Resp> = tx.into();
        let _entered = current_span.enter();
        match load_repo(&config, request.repository_ref()) {
            Err(RepoLoadError::SpecError(e)) => btx.send(Err(repo_spec_error_status(e))),
            Err(RepoLoadError::LoadError(e)) => btx.send(Err(Status::internal(format!(
                "Error loading repository: {:?}",
                e
            )))),
            Ok(repo) => and_then(request, repo, btx),
        }
    });
    Ok(Response::new(Box::pin(ReceiverStream::new(rx))))
}

/// Load a repo and run closures for a bidirectional gRPC method
///
/// Similar to [`load_repo_and_stream`] except that the request is actually a stream
/// and the closure is called repeatedly, once per request message, hence there is
/// at least one response message per request message.
///
/// The repository is loaded from the first request message, the additional boolean argument
/// to the closure tells it if it is called on the first message.
///
/// Possible improvements: consume the request faster, parking the values using another
/// inner channel.
pub async fn load_repo_and_stream_bidir<
    Req: RequestWithRepo,
    T,
    Resp: fmt::Debug + Send + 'static,
>(
    config: Arc<Config>,
    mut request: Streaming<Req>,
    repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static,
    treat_first: impl Fn(Req, &Repo, &BlockingResponseSender<Resp>) -> T + Send + 'static,
    treat_subsequent: impl Fn(Req, &T, &Repo, &BlockingResponseSender<Resp>) + Send + 'static,
) -> Result<Response<BoxStream<Resp>>, Status> {
    // no point having channel capacity for several messages, since `blocking_send` is the only
    // way to use it.
    let (tx, rx) = mpsc::channel(1);
    let current_span = Span::current();
    if let Some(first_res) = request.next().await {
        let first_req = first_res?; // TODO provide specific error treatment

        tokio::task::spawn_blocking(move || {
            let btx: BlockingResponseSender<Resp> = tx.into();
            let _entered = current_span.enter();
            match load_repo(&config, first_req.repository_ref()) {
                Err(RepoLoadError::SpecError(e)) => btx.send(Err(repo_spec_error_status(e))),
                Err(RepoLoadError::LoadError(e)) => btx.send(Err(Status::internal(format!(
                    "Error loading repository: {:?}",
                    e
                )))),
                Ok(repo) => {
                    let first_out = treat_first(first_req, &repo, &btx);
                    while let Some(res) = block_on(request.next()) {
                        match res {
                            Err(e) => btx.send(Err(e)), // TODO expose specific error treatment
                            Ok(req) => treat_subsequent(req, &first_out, &repo, &btx),
                        }
                    }
                }
            }
        });
        Ok(Response::new(Box::pin(ReceiverStream::new(rx))))
    } else {
        empty_response_stream()
    }
}

pub fn blocking_join_error_status(err: JoinError) -> Status {
    if err.is_cancelled() {
        // According to https://grpc.io/docs/guides/error/, it should be
        // `Unavailable()` if this is a graceful shutdown, but now the question is how
        // to tell that apart from user cancellation.
        Status::cancelled("Inner blocking task on Mercurial repo was cancelled")
    } else {
        Status::internal(format!("Unexpected error in inner thread: {:?}", err))
    }
}

/// Load a repository in a separate thread and hand it over to a closure
///
/// This creates a new thread suitable for blocking operations, using
/// [`tokio::task::spawn_blocking`] and then hands it over together with the orignal request
/// to the `and_then` closure, whose return value is finally returned to the caller.
/// The closure is at liberty to use any blocking operation (most calls to `hg-core` are blocking).
///
/// If the repository loading fails, the appropriate gRPC error [`Status`] is returned
///
/// `repo_spec_error_status` plays the same role as in [`load_repo_and_stream`], and again
/// the [`default_repo_spec_error_status`] function can be used in the majority of
/// cases.
pub async fn load_repo_and_then<Req: RequestWithRepo, Res: Send + 'static>(
    config: Arc<Config>,
    request: Req,
    repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static,
    and_then: impl FnOnce(Req, Repo) -> Result<Res, Status> + Send + 'static,
) -> Result<Res, Status> {
    let current_span = Span::current();
    tokio::task::spawn_blocking(move || {
        let _entered = current_span.enter();
        match load_repo(&config, request.repository_ref()) {
            Err(RepoLoadError::SpecError(e)) => Err(repo_spec_error_status(e)),
            Err(RepoLoadError::LoadError(e)) => Err(Status::internal(format!(
                "Error loading repository: {:?}",
                e
            ))),
            Ok(repo) => and_then(request, repo),
        }
    })
    .await
    .map_err(blocking_join_error_status)?
}

async fn load_repo_at_and_then<Res: Send + 'static>(
    config: Arc<Config>,
    repo_path: PathBuf,
    and_then: impl FnOnce(Repo) -> Result<Res, Status> + Send + 'static,
) -> Result<Res, Status> {
    let current_span = Span::current();
    tokio::task::spawn_blocking(move || {
        let _entered = current_span.enter();
        match load_repo_at(&config, repo_path) {
            Err(e) => Err(Status::internal(format!(
                "Error loading repository: {:?}",
                e
            ))),
            Ok(repo) => and_then(repo),
        }
    })
    .await
    .map_err(blocking_join_error_status)?
}

/// Load a repository and its changelog in a separate thread and hand it over to a closure
///
/// See [`load_repo_and_then`] on which this builds upon for more details.
pub async fn load_changelog_and_then<Req: RequestWithRepo, Res: Send + 'static>(
    config: Arc<Config>,
    request: Req,
    repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static,
    and_then: impl FnOnce(Req, &Repo, &Changelog) -> Result<Res, Status> + Send + 'static,
) -> Result<Res, Status> {
    load_repo_and_then(config, request, repo_spec_error_status, |req, repo| {
        let cl = repo
            .changelog()
            .map_err(|e| Status::internal(format!("Could not open changelog: {:?}", e)))?;
        and_then(req, &repo, &cl)
    })
    .await
}

/// Load a repository and its changelog in a separate thread for streaming responses
///
/// See [`load_repo_and_stream`] on which this builds upon for more details.
pub fn load_changelog_and_stream<Req: RequestWithRepo, Resp: fmt::Debug + Send + 'static>(
    config: Arc<Config>,
    request: Req,
    repo_spec_error_status: impl Fn(RepoSpecError) -> Status + Send + 'static,
    and_then: impl FnOnce(Req, &Repo, &Changelog, BlockingResponseSender<Resp>) + Send + 'static,
) -> Result<Response<BoxStream<Resp>>, Status> {
    load_repo_and_stream(
        config,
        request,
        repo_spec_error_status,
        |req, repo, tx| match repo.changelog() {
            Ok(cl) => and_then(req, &repo, &cl, tx),
            Err(e) => tx.send(Err(Status::internal(format!(
                "Could not open changelog: {:?}",
                e
            )))),
        },
    )
}

#[cfg(test)]
mod tests {

    use super::*;

    #[test]
    fn test_repo_path() {
        let mut config = Config::default();
        config.repositories_root = "/repos".into();
        let mut repo = Repository::default();
        repo.storage_name = "default".into();
        repo.relative_path = "foo/bar".into();
        assert_eq!(repo_path(&config, &repo), Ok("/repos/foo/bar".into()));

        repo.relative_path = "foo/bar.git".into();
        assert_eq!(repo_path(&config, &repo), Ok("/repos/foo/bar.hg".into()));

        repo.storage_name = "hg:default".into();
        assert_eq!(repo_path(&config, &repo), Ok("/repos/foo/bar.hg".into()));
    }
}
