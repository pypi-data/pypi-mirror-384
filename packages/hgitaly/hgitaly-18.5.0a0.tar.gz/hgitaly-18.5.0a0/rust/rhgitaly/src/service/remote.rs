// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
/// Implementation for Gitaly's RemoteService, hence about **Git** remote repositories.
use regex::bytes::Regex;
use std::collections::HashMap;
use std::ffi::{OsStr, OsString};
use std::fmt::{Debug, Formatter};
use std::net::IpAddr;
use std::os::unix::ffi::OsStrExt;
use std::sync::Arc;

use lazy_static::lazy_static;
use tokio::sync::mpsc;
use tokio_stream::StreamExt;
use tokio_util::sync::CancellationToken;
use tonic::{
    metadata::Ascii, metadata::MetadataMap, metadata::MetadataValue, Request, Response, Status,
    Streaming,
};
use tracing::{info, instrument, warn};
use url::Url;

use crate::config::Config;
use crate::gitaly::remote_service_server::{RemoteService, RemoteServiceServer};
use crate::gitaly::{update_remote_mirror_request, Repository};
use crate::gitaly::{
    FindRemoteRepositoryRequest, FindRemoteRepositoryResponse, UpdateRemoteMirrorRequest,
    UpdateRemoteMirrorResponse,
};
use crate::gitlab::state::get_gitlab_default_branch;
use crate::gitlab::{gitlab_branch_from_ref, gitlab_branch_ref, GITLAB_TAG_REF_PREFIX};
use crate::glob::star_patterns_to_regex;
use crate::metadata::correlation_id;
use crate::repository::{
    default_repo_spec_error_status, repo_store_vfs,
    spawner::{BytesChunking, RepoProcessSpawnerTemplate},
    RequestWithRepo,
};
use crate::ssh::SSHOptions;

use crate::util::tracing_span_id;

/// PUSH_BATCH_SIZE is the maximum number of refs to push in a single Git push call.
const PUSH_BATCH_SIZE: usize = 100;
/// MAX_DIVERGENT_REFS
const MAX_DIVERGENT_REFS: usize = 100;
const MERCURIAL_EXPECTED_CAPABILITIES: &str = "getbundle known";
const REMOTE_REPO_NOT_EXISTS: FindRemoteRepositoryResponse =
    FindRemoteRepositoryResponse { exists: false };

lazy_static! {
    static ref MERCURIAL_CONTENT_TYPE_RX: Regex =
        Regex::new(r"^application/mercurial-\d+.\d+").unwrap();
}

#[derive(Debug)]
pub struct RemoteServiceImpl {
    config: Arc<Config>,
    shutdown_token: CancellationToken,
}

#[tonic::async_trait]
impl RemoteService for RemoteServiceImpl {
    /// This pushes to a *Git* repository
    async fn update_remote_mirror(
        &self,
        request: Request<Streaming<UpdateRemoteMirrorRequest>>,
    ) -> Result<Response<UpdateRemoteMirrorResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_push(inner, correlation_id(&metadata), &metadata)
            .await
    }

    /// This checks a remote *Mercurial* repository
    async fn find_remote_repository(
        &self,
        request: Request<FindRemoteRepositoryRequest>,
    ) -> Result<Response<FindRemoteRepositoryResponse>, Status> {
        let (metadata, _ext, inner) = request.into_parts();

        self.inner_find_remote_repository(inner, correlation_id(&metadata))
            .await
            .map(Response::new)
    }
}

/// Return Git remote name and URL from the request, collapsing errors in one stroke.
///
/// # gRPC errors
/// - `INVALID_ARGUMENT` if `remote` is missing or has an empty URL
///    (see Gitaly `validateUpdateRemoteMirrorRequest()` and its callers).
fn extract_git_remote<'r>(
    req: &'r UpdateRemoteMirrorRequest,
    git_config: &mut Vec<(OsString, OsString)>,
) -> Result<(String, String, &'r str), Status> {
    if let Some(ref git_remote) = req.remote {
        let url = &git_remote.url;

        if url.is_empty() {
            return Err(Status::invalid_argument("remote is missing URL"));
        }
        let git_remote_name = format!("inmemory-{:x}", rand::random::<u64>());

        let resolved_address = &git_remote.resolved_address;
        if !resolved_address.is_empty() && resolved_address.parse::<IpAddr>().is_err() {
            return Err(Status::invalid_argument(
                "resolved address has invalid IPv4/IPv6 address",
            ));
        }

        let resolved_url = if resolved_address.is_empty() {
            url.clone()
        } else if url.starts_with("http://")
            || url.starts_with("https://")
            || url.starts_with("git://")
        {
            get_url_and_resolve_config_for_url(git_config, url, resolved_address)?
        } else if url.starts_with("ssh://") {
            get_url_and_resolve_config_for_ssh(git_config, url, resolved_address)?
        } else {
            get_url_and_resolve_config_for_scp(git_config, url, resolved_address)?
        };

        Ok((
            git_remote_name,
            resolved_url,
            &git_remote.http_authorization_header,
        ))
    } else {
        Err(Status::invalid_argument("missing Remote"))
    }
}

fn get_url_and_resolve_config_for_scp(
    _git_config: &[(OsString, OsString)],
    url: &str,
    resolved_address: &str,
) -> Result<String, Status> {
    // this would not be general enough for host being an IPv6 address.
    // however, this is what the Golang impl does, and given that the point
    // is to replace the host by an address for security reasons, we don't see
    // why it should be different.
    let mut split = url.splitn(2, ':');
    let host = split
        .next()
        .expect("The case of empty URL should already have been ruled out");
    if let Some(path) = split.next() {
        if host.contains('/') {
            return Err(Status::invalid_argument(
                "SSH URLs with '/' before colon are unsupported",
            ));
        }

        let user_prefix = host.find('@').map_or("", |i| &host[..i + 1]);

        Ok(format!("{user_prefix}{resolved_address}:{path}"))
    } else {
        Err(Status::invalid_argument(format!(
            "invalid protocol/URL encountered: {url}"
        )))
    }
}

fn parse_url_set_host(url: &str, resolved_address: &str) -> Result<Url, Status> {
    let mut parsed = Url::parse(url)
        .map_err(|e| Status::invalid_argument(format!("couldn't parse remote URL: {e}")))?;
    parsed.set_host(Some(resolved_address)).map_err(|e| {
        Status::invalid_argument(format!(
            "couldn't change host of URL into resolved IP address: {e}"
        ))
    })?;
    Ok(parsed)
}

fn get_url_and_resolve_config_for_ssh(
    _git_config: &mut [(OsString, OsString)],
    url: &str,
    resolved_address: &str,
) -> Result<String, Status> {
    Ok(parse_url_set_host(url, resolved_address)?.to_string())
}

fn get_url_and_resolve_config_for_url(
    git_config: &mut Vec<(OsString, OsString)>,
    url: &str,
    resolved_address: &str,
) -> Result<String, Status> {
    let parsed = Url::parse(url)
        .map_err(|e| Status::invalid_argument(format!("couldn't parse remote URL: {e}")))?;

    if let Some(port) = parsed.port_or_known_default().or_else(|| {
        if parsed.scheme() == "git" {
            Some(9418)
        } else {
            None
        }
    }) {
        if let Some(host) = parsed.host_str() {
            git_config.push((
                "http.curloptResolve".into(),
                format!("{host}:{port}:{resolved_address}").into(),
            ));
        } else {
            return Err(Status::invalid_argument(format!(
                "Cannot-be-a-base URL is invalid for Git push: {url}",
            )));
        }
    } else {
        return Err(Status::invalid_argument(format!(
            "unknown scheme provided: {}",
            parsed.scheme()
        )));
    }

    Ok(url.to_string())
}

/// Safely log HTTP errors at info level
///
/// In `find_remote_repository`, HTTP request errors are usually considered normal
fn log_find_repo_reqwest_error(err: reqwest::Error) {
    // URL can be sensitive (password) and we should already have logged it properly
    let safe_err = err.without_url();
    info!("Error performing request: {}", &safe_err);
}

/// Wrapper to treat TCP errors only once
///
/// Return status code, Content-Type check result and body
async fn find_repo_get(url: Url) -> Result<(reqwest::StatusCode, bool, String), reqwest::Error> {
    let resp = reqwest::get(url).await?;
    let status = resp.status();
    let headers = resp.headers();

    if let Some(ctype) = headers.get("Content-Type") {
        if !MERCURIAL_CONTENT_TYPE_RX.is_match(ctype.as_bytes()) {
            return Ok((status, false, String::default()));
        }
    } else {
        return Ok((status, false, String::default()));
    }

    let body = resp.text().await?;
    Ok((status, true, body))
}

impl RemoteServiceImpl {
    #[instrument(name = "find_remote_repository", skip(self, request))]
    async fn inner_find_remote_repository(
        &self,
        request: FindRemoteRepositoryRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<FindRemoteRepositoryResponse, Status> {
        tracing_span_id!();
        info!("Processing");
        // Gitaly would return Internal here because of failure in git ls-remote, although it is
        // obviously a client error. We cannot log the URL because even malformed, it could bear
        // sensitive information.
        let mut url = Url::parse(&request.remote)
            .map_err(|e| Status::internal(format!("Could not parse URL: {}", e)))?;

        let mut log_url = url.clone();
        if log_url.password().is_some() {
            log_url
                .set_password(Some("*********"))
                // given the URL has a password, the error case below is probably impossible:
                .map_err(|_| {
                    Status::internal(
                        "Could not obfuscate password on incoming URL \
                        (empty host or cannot be a base)",
                    )
                })?;
        }
        info!("Checking if there is a Mercurial repository at {}", log_url);

        url.set_query(Some("cmd=capabilities"));
        let (status, content_type_ok, body) = match find_repo_get(url).await {
            Ok(r) => r,
            Err(e) => {
                log_find_repo_reqwest_error(e);
                // actually Gitaly manages to return false
                return Ok(REMOTE_REPO_NOT_EXISTS);
            }
        };
        // Perhaps return Unavailable for status code 503 (see protocol comment)
        if status != reqwest::StatusCode::OK {
            info!("GET response status code {}: returning false", status);
            return Ok(REMOTE_REPO_NOT_EXISTS);
        }
        if !content_type_ok {
            info!("GET response does not have expected Content-Type: returning false");
            return Ok(REMOTE_REPO_NOT_EXISTS);
        }

        // Finally, checking capabilities.
        // This is a quadratic search, but it does not matter: there are as of this writing
        // only 2 expected capabilities being checked
        let capas: Vec<_> = body.split(' ').collect();
        for exp_capa in MERCURIAL_EXPECTED_CAPABILITIES.split(' ') {
            let mut found = false;
            // returned capabilities seem to be sorted, hence we could perform a binary search
            // if it were guaranteed by some specification. Saving perhaps 1 µs here
            // does not matter.
            for capa in capas.iter() {
                if *capa == exp_capa {
                    found = true;
                    break;
                }
            }
            if !found {
                return Ok(REMOTE_REPO_NOT_EXISTS);
            }
        }
        Ok(FindRemoteRepositoryResponse { exists: true })
    }

    #[instrument(name = "update_remote_mirror", skip(self, request, metadata))]
    async fn inner_push(
        &self,
        mut request: Streaming<UpdateRemoteMirrorRequest>,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<Response<UpdateRemoteMirrorResponse>, Status> {
        tracing_span_id!();
        if let Some(first_req) = request.next().await {
            let first_req = first_req?;
            info!(
                "Processing, first request chunk={:?}",
                UpdateRemoteMirrorTracingRequest(&first_req)
            );
            let ssh_opts = SSHOptions::new(&first_req.ssh_key, &first_req.known_hosts).await?;
            let keep_divergent = first_req.keep_divergent_refs;

            let mut git_config = Vec::new();
            let (git_remote_name, git_remote_url, auth_header) =
                extract_git_remote(&first_req, &mut git_config)?;
            git_config.push((
                format!("remote.{}.url", &git_remote_name).into(),
                (&git_remote_url).into(),
            ));
            if !auth_header.is_empty() {
                let mut full_header = "Authorization: ".to_string();
                full_header.push_str(auth_header);
                git_config.push((
                    format!("http.{}.extraHeader", &git_remote_url).into(),
                    full_header.into(),
                ));
            }

            let store_vfs = repo_store_vfs(&self.config, &first_req.repository)
                .await
                .map_err(default_repo_spec_error_status)?;
            let default_branch_name = get_gitlab_default_branch(&store_vfs)
                .await
                .map_err(|e| {
                    Status::internal(format!(
                        "Error reading or checking GitLab default branch: {:?}",
                        e
                    ))
                })?
                .map(|name| gitlab_branch_ref(&name));

            let config = self.config.clone();
            let mut spawner_tmpl = RepoProcessSpawnerTemplate::new_aux_git(
                config.clone(),
                first_req.clone(), // cloning perhaps not needed in the end
                metadata,
                git_config,
                default_repo_spec_error_status,
            )
            .await?
            .with_git_ssh_options(&ssh_opts);

            let mut only_branches_matching = first_req.only_branches_matching;
            while let Some(req) = request.next().await {
                only_branches_matching.extend_from_slice(&req?.only_branches_matching);
            }
            let branches_rx = if only_branches_matching.is_empty() {
                None
            } else {
                Some(star_patterns_to_regex(&only_branches_matching))
            };
            let mut remote_refs = self
                .ls_remote(&spawner_tmpl, &git_remote_name, false)
                .await?;

            let mut to_update: Vec<Vec<u8>> = Vec::new();
            let mut divergent_refs: Vec<Vec<u8>> = Vec::new();
            let mut default_branch_exists = false;
            for (local_ref_name, local_ref_tgt) in
                self.branches_and_tags_as_refs(&spawner_tmpl).await?
            {
                if default_branch_name.as_ref() == Some(&local_ref_name) {
                    default_branch_exists = true;
                }
                // we have no symbolic refs
                match remote_refs.remove(&local_ref_name) {
                    None => {
                        // remote does not have this one, scheduling for Git push
                        to_update.push(local_ref_name);
                    }
                    Some(remote_tgt) => {
                        if remote_tgt != local_ref_tgt {
                            if keep_divergent {
                                if self
                                    .is_ancestor(
                                        &spawner_tmpl,
                                        remote_tgt.as_bytes(),
                                        local_ref_tgt.as_bytes(),
                                        true,
                                    )
                                    .await?
                                {
                                    to_update.push(local_ref_name);
                                } else if divergent_refs.len() < MAX_DIVERGENT_REFS {
                                    divergent_refs.push(local_ref_name)
                                }
                            } else {
                                to_update.push(local_ref_name)
                            }
                        }
                    }
                }
            }
            let to_delete: Option<Vec<Vec<u8>>> =
                if let Some(ref default_branch) = default_branch_name {
                    if !default_branch_exists || keep_divergent {
                        None
                    } else {
                        let mut todel = Vec::with_capacity(remote_refs.len());
                        for (name, tgt) in remote_refs {
                            if self
                                .is_ancestor(&spawner_tmpl, tgt.as_bytes(), default_branch, true)
                                .await?
                            {
                                todel.push(name)
                            }
                        }
                        Some(todel)
                    }
                } else {
                    None
                };

            let mut default_branch_idx: Option<usize> = None;
            // For an update of `ref_name`, the push refspec is simply `ref_name`
            let mut refspecs: Vec<Vec<u8>> = to_update
                .into_iter()
                .enumerate()
                .filter_map(|(i, ref_name)| {
                    if Some(&ref_name) == default_branch_name.as_ref() {
                        default_branch_idx = Some(i)
                    }
                    if remote_mirror_ref_match(&branches_rx, &ref_name) {
                        Some(ref_name)
                    } else {
                        None
                    }
                })
                .collect();
            // Comment from Gitaly:
            //   The default branch needs to be pushed in the first batch of refspecs as some
            //   features depend on it existing in the repository. The default branch may not exist
            //   in the repo yet if this is the first mirroring push.
            if let Some(i) = default_branch_idx {
                refspecs.swap(0, i);
            }

            // For a deletion of `ref_name`, the push refspec is `:ref_name`
            if let Some(to_del) = to_delete {
                for mut ref_name in to_del {
                    if remote_mirror_ref_match(&branches_rx, &ref_name) {
                        ref_name.insert(0, b':');
                        refspecs.push(ref_name);
                    }
                }
            }

            spawner_tmpl.add_arg("push".into());
            if !keep_divergent {
                spawner_tmpl.add_arg("-f".into());
            }
            spawner_tmpl.add_arg(git_remote_name.into());
            for chunk in refspecs.chunks(PUSH_BATCH_SIZE) {
                let mut spawner = spawner_tmpl.git_spawner();
                // This copy is annoying, yet this will not be the first thing to optimize
                let args: Vec<OsString> = chunk
                    .iter()
                    .map(|refspec| OsStr::from_bytes(refspec).to_os_string())
                    .collect();
                spawner.args(&args);

                let git_exit_code = spawner.spawn(self.shutdown_token.clone()).await?;
                if git_exit_code != 0 {
                    warn!("Git subprocess exited with code {git_exit_code}");
                    return Err(Status::internal(format!(
                        "Git subprocess exited with code {git_exit_code}"
                    )));
                }
            }
            Ok(Response::new(UpdateRemoteMirrorResponse { divergent_refs }))
        } else {
            Err(Status::cancelled(
                "Did not get any request message in stream",
            ))
        }
    }

    /// Call ls-remote and parse results
    ///
    /// # Parameters
    /// - `peel_tags`: if `true` peeled annotated tag, e.g. `refs/tags/v17.6.2-ee^{}`
    ///   are *added* to the output.
    async fn ls_remote(
        &self,
        spawner_tmpl: &RepoProcessSpawnerTemplate,
        remote_name: &str,
        peel_tags: bool,
    ) -> Result<HashMap<Vec<u8>, String>, Status> {
        let mut spawner = spawner_tmpl.git_spawner();
        let mut args: Vec<OsString> = vec!["ls-remote".into()];
        if !peel_tags {
            args.push("--ref".into());
        }
        args.push(remote_name.into());
        args.push("refs/heads/*".into());
        args.push("refs/tags/*".into());
        // One can hope RHGitaly to read the git stdout faster than it will be produced,
        // but that could not be true if it is not streamed all the way. TODO check chan size
        let (stdout_tx, mut stdout_rx) = mpsc::channel(3);
        spawner.capture_stdout(stdout_tx, BytesChunking::Lines);
        spawner.args(&args);
        let spawned = spawner.spawn(self.shutdown_token.clone());
        let read_stdout = async {
            let mut refs = HashMap::new();
            while let Some(line) = stdout_rx.recv().await {
                let mut split = line.split(|c| *c == b'\t');
                let sha = String::from_utf8_lossy(
                    split
                        .next()
                        .ok_or_else(|| Status::internal("Empty line in `git ls-remote` output"))?,
                )
                .to_string();
                // TODO validate sha?
                let name = split.next().ok_or_else(|| {
                    Status::internal("Missing ref name in `git ls-remote` output")
                })?;
                let name = name.strip_suffix(b"\n").unwrap_or(name);
                refs.insert(name.to_vec(), sha);
            }
            Ok(refs)
        };
        let (spawn_result, refs) = tokio::join!(spawned, read_stdout);
        let exit_code = spawn_result?;
        if exit_code != 0 {
            warn!("`git ls-remote` exited with code {}", exit_code);
            return Err(Status::internal(format!(
                "`git ls-remote` exited with code {}",
                exit_code
            )));
        }
        refs
    }

    /// Call for-each-ref and parse results
    ///
    /// TODO what a duplication from `ls_remote`!
    async fn branches_and_tags_as_refs(
        &self,
        spawner_tmpl: &RepoProcessSpawnerTemplate,
    ) -> Result<Vec<(Vec<u8>, String)>, Status> {
        let mut spawner = spawner_tmpl.git_spawner();
        let args: Vec<OsString> = vec![
            "for-each-ref".into(),
            "--format".into(),
            "%(objectname) %(refname)".into(),
            "refs/heads/".into(),
            "refs/tags/".into(),
        ];
        // One can hope RHGitaly to read the git stdout faster than it will be produced,
        // but that could not be true if it is not streamed all the way. TODO check chan size
        let (stdout_tx, mut stdout_rx) = mpsc::channel(3);
        spawner.capture_stdout(stdout_tx, BytesChunking::Lines);
        spawner.args(&args);
        let spawned = spawner.spawn(self.shutdown_token.clone());
        let read_stdout = async {
            let mut refs = Vec::new();
            while let Some(line) = stdout_rx.recv().await {
                let mut split = line.split(|c| *c == b' ');
                let sha = String::from_utf8_lossy(
                    split
                        .next()
                        .ok_or_else(|| Status::internal("Empty line in `git ls-remote` output"))?,
                )
                .to_string();
                // TODO validate sha?
                let name = split.next().ok_or_else(|| {
                    Status::internal("Missing ref name in `git for-each-ref` output")
                })?;
                let name = name.strip_suffix(b"\n").unwrap_or(name);
                refs.push((name.to_vec(), sha))
            }
            Ok(refs)
        };
        let (spawn_result, refs) = tokio::join!(spawned, read_stdout);
        let exit_code = spawn_result?;
        if exit_code != 0 {
            warn!("`git for-each-ref` exited with code {}", exit_code);
            return Err(Status::internal(format!(
                "`git for-each-ref` exited with code {}",
                exit_code
            )));
        }
        refs
    }

    async fn is_ancestor(
        &self,
        spawner_tmpl: &RepoProcessSpawnerTemplate,
        rev1: &[u8],
        rev2: &[u8],
        catch_unknown_rev: bool,
    ) -> Result<bool, Status> {
        let mut spawner = spawner_tmpl.git_spawner();
        let args: Vec<OsString> = vec![
            "merge-base".into(),
            "--is-ancestor".into(),
            OsStr::from_bytes(rev1).to_os_string(),
            OsStr::from_bytes(rev2).to_os_string(),
        ];
        spawner.args(&args);
        match spawner.spawn(self.shutdown_token.clone()).await? {
            0 => Ok(true),
            1 => Ok(false),
            // TODO we should check the error message "fatal: Not a valid object name {rev1}"
            // but for that we should grow stderr capture capability
            128 => {
                if catch_unknown_rev {
                    Ok(false)
                } else {
                    Err(git_subprocess_error(128))
                }
            }
            code => Err(git_subprocess_error(code)),
        }
    }
}

fn git_subprocess_error(exit_code: i32) -> Status {
    Status::internal(format!("Git subprocess exited with code {exit_code}"))
}

fn remote_mirror_ref_match(rx: &Option<Regex>, ref_name: &[u8]) -> bool {
    if let Some(rx) = rx {
        if ref_name.starts_with(GITLAB_TAG_REF_PREFIX) {
            return true;
        }
        if let Some(branch_name) = gitlab_branch_from_ref(ref_name) {
            return rx.is_match(branch_name);
        }
        false
    } else {
        true
    }
}

impl RequestWithRepo for UpdateRemoteMirrorRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

struct UpdateRemoteMirrorTracingRequest<'a>(&'a UpdateRemoteMirrorRequest);

impl Debug for UpdateRemoteMirrorTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        let secure_remote = self.0.remote.as_ref().map(|rem| {
            let mut parsed = Url::parse(&rem.url);
            let stripped_url = match parsed {
                Ok(ref mut url) => {
                    let _ignore_errors = url.set_password(None);
                    url.to_string()
                }
                Err(_) => rem.url.clone(),
            };
            update_remote_mirror_request::Remote {
                url: stripped_url,
                http_authorization_header: format!(
                    "<{}> bytes",
                    &rem.http_authorization_header.len()
                ),
                resolved_address: rem.resolved_address.clone(),
            }
        });

        f.debug_struct("UpdateRemoteMirrorRequest")
            .field("repository", &self.0.repository)
            .field("remote", &secure_remote)
            .field("ssh_key", &format!("<{} bytes>", self.0.ssh_key.len()))
            .field(
                "known_hosts",
                &format!("<{} bytes>", self.0.known_hosts.len()),
            )
            .finish()
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn remote_server(
    config: &Arc<Config>,
    shutdown_token: &CancellationToken,
) -> RemoteServiceServer<RemoteServiceImpl> {
    RemoteServiceServer::new(RemoteServiceImpl {
        config: config.clone(),
        shutdown_token: shutdown_token.clone(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scp_subst() -> Result<(), Status> {
        let mut conf = Vec::new();
        let ip = "192.0.2.13";
        assert_eq!(
            get_url_and_resolve_config_for_scp(&mut conf, "joe@git.example:my/repo", ip)?,
            "joe@192.0.2.13:my/repo"
        );
        assert_eq!(
            get_url_and_resolve_config_for_scp(&mut conf, "git.example:my/repo", ip)?,
            "192.0.2.13:my/repo"
        );
        Ok(())
    }

    #[test]
    fn test_ssh_subst() -> Result<(), Status> {
        let mut conf = Vec::new();
        let ip = "192.0.2.13";
        assert_eq!(
            get_url_and_resolve_config_for_ssh(&mut conf, "ssh://joe@git.example/my/repo", ip)?,
            "ssh://joe@192.0.2.13/my/repo"
        );
        assert_eq!(
            get_url_and_resolve_config_for_ssh(&mut conf, "ssh://git.example/my/repo", ip)?,
            "ssh://192.0.2.13/my/repo"
        );
        Ok(())
    }

    /// Assert that url is unchanged and assert value of added Git config parameter
    fn assert_unchanged_url_added_git_config(url: &str, conf_value: &str) -> Result<(), Status> {
        let mut conf = Vec::new();
        let ip = "192.0.2.13";
        assert_eq!(get_url_and_resolve_config_for_url(&mut conf, url, ip)?, url);
        assert_eq!(
            conf,
            vec![("http.curloptResolve".into(), conf_value.into())]
        );
        Ok(())
    }

    #[test]
    fn test_http_and_git() -> Result<(), Status> {
        assert_unchanged_url_added_git_config(
            "http://joe@git.example/my/repo",
            "git.example:80:192.0.2.13",
        )?;
        assert_unchanged_url_added_git_config(
            "http://git.example/my/repo",
            "git.example:80:192.0.2.13",
        )?;
        assert_unchanged_url_added_git_config(
            "https://joe:test@git.example/my/repo",
            "git.example:443:192.0.2.13",
        )?;
        assert_unchanged_url_added_git_config(
            "git://git.example/my/repo",
            "git.example:9418:192.0.2.13",
        )?;
        assert_unchanged_url_added_git_config(
            "https://joe:test@git.example:8443/my/repo",
            "git.example:8443:192.0.2.13",
        )?;
        Ok(())
    }
}
