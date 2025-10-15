use std::collections::{BTreeMap, BTreeSet};
use std::fmt::{Debug, Formatter};
use std::iter::Iterator;
use std::sync::Arc;

use tonic::{codegen::BoxStream, Response, Status};
use tracing::{info, warn};

use hg::repo::Repo;
use hg::revlog::changelog::{Changelog, ChangelogEntry};
use hg::revlog::{NodePrefix, Revision, RevlogError, NULL_REVISION};
use hg::utils::hg_path::HgPath;
use hg::AncestorsIterator;

use super::revlog_err_from_graph_err;
use crate::config::Config;
use crate::git::{self, GitPathSpec};
use crate::gitaly::{
    list_last_commits_for_tree_response::CommitForTree, LastCommitForPathRequest,
    LastCommitForPathResponse, ListLastCommitsForTreeRequest, ListLastCommitsForTreeResponse,
    Repository,
};
use crate::gitlab::revision::gitlab_revision_node_prefix;
use crate::mercurial::ls_path_sorted_dirs_first;
use crate::message;
use crate::repository::{
    default_repo_spec_error_status, load_changelog_and_stream, load_changelog_and_then,
    repo_store_vfs, RequestWithRepo,
};
use crate::streaming::{empty_response_stream, stream_chunks, BlockingResponseSender};

struct LastCommitForPathTracingRequest<'a>(&'a LastCommitForPathRequest);

impl Debug for LastCommitForPathTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("LastCommitForPathRequest")
            .field("repository", &self.0.repository)
            .field("revision", &String::from_utf8_lossy(&self.0.revision))
            .field("path", &String::from_utf8_lossy(&self.0.path))
            .field("literal_pathspec", &self.0.literal_pathspec)
            .finish()
    }
}

struct ListLastCommitsForTreeTracingRequest<'a>(&'a ListLastCommitsForTreeRequest);

impl Debug for ListLastCommitsForTreeTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ListLastCommitsForTreeRequest")
            .field("repository", &self.0.repository)
            .field("revision", &self.0.revision)
            .field("path", &String::from_utf8_lossy(&self.0.path))
            .field("global_options", &self.0.global_options)
            .field("limit", &self.0.limit)
            .field("offset", &self.0.offset)
            .finish()
    }
}

impl RequestWithRepo for LastCommitForPathRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

impl RequestWithRepo for ListLastCommitsForTreeRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

pub async fn one_for_path(
    config: &Arc<Config>,
    request: LastCommitForPathRequest,
) -> Result<Response<LastCommitForPathResponse>, Status> {
    info!(
        "Processing, request={:?}",
        LastCommitForPathTracingRequest(&request)
    );
    if request.revision.is_empty() {
        return Err(Status::invalid_argument("empty revision"));
    }

    let config = config.clone();
    let store_vfs = repo_store_vfs(&config, &request.repository)
        .await
        .map_err(default_repo_spec_error_status)?;

    let literal_pathspec = request.literal_pathspec
        || if let Some(ref opts) = request.global_options {
            opts.literal_pathspecs
        } else {
            false
        };

    match gitlab_revision_node_prefix(&store_vfs, &request.revision)
        .await
        .map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))?
    {
        None => {
            info!("Revision not resolved");
            Ok(Response::new(LastCommitForPathResponse::default()))
        }
        Some(node_prefix) => {
            info!("Revision resolved as {:x}", &node_prefix);

            load_changelog_and_then(
                config.clone(),
                request,
                default_repo_spec_error_status,
                move |req, _repo, cl| {
                    lcfp_in_thread(req, cl, node_prefix, literal_pathspec)
                        .map_err(|e| Status::internal(format!("Repository corruption {:?}", e)))
                },
            )
            .await
            .map(Response::new)
        }
    }
}

/// in-thread implementation for `LastCommitForPath`
///
/// This means that this is synchronous code, running in the separate thread
/// than opens repo and changelog.
///
/// This is in particular useful to concentrate `RevlogError` in one return
/// type, to avoid littering with map_err everywhere
fn lcfp_in_thread(
    req: LastCommitForPathRequest,
    cl: &Changelog,
    node_prefix: NodePrefix,
    literal_pathspec: bool,
) -> Result<LastCommitForPathResponse, RevlogError> {
    let rev = cl.rev_from_node(node_prefix)?;
    if rev == NULL_REVISION {
        // a bit of an edge cas for this error variant, but
        // the Gitaly error is the same as for non resolvable revisions,
        // so it fits
        return Err(RevlogError::InvalidRevision(rev.to_string()));
    }
    let maybe_entry = if literal_pathspec {
        lcfp_ancestors_walk(git::GitLiteralPathSpec::new(&req.path), cl, rev)
    } else {
        lcfp_ancestors_walk(git::GitWildcardPathSpec::new(&req.path), cl, rev)
    }?;

    maybe_entry.map_or_else(
        || Ok(LastCommitForPathResponse::default()), // no match
        |cl_entry| {
            Ok(LastCommitForPathResponse {
                commit: Some(message::commit(cl_entry)?),
            })
        },
    )
}

fn lcfp_ancestors_walk(
    path_spec: impl GitPathSpec,
    cl: &Changelog,
    rev: Revision,
) -> Result<Option<ChangelogEntry>, RevlogError> {
    if path_spec.matches_root() {
        return Ok(Some(cl.entry_for_unchecked_rev(rev.into())?));
    }
    for anc_rev in
        AncestorsIterator::new(cl, [rev], NULL_REVISION, true).map_err(revlog_err_from_graph_err)?
    {
        let cl_entry =
            cl.entry_for_unchecked_rev(anc_rev.map_err(revlog_err_from_graph_err)?.into())?;
        let cl_data = cl_entry.data()?;
        for cl_path in cl_data.files() {
            if path_spec.matches(cl_path.as_bytes()) {
                return Ok(Some(cl_entry));
            }
        }
    }
    Ok(None)
}

pub async fn several_for_tree(
    config: &Arc<Config>,
    request: ListLastCommitsForTreeRequest,
) -> Result<Response<BoxStream<ListLastCommitsForTreeResponse>>, Status> {
    info!(
        "Processing, request={:?}",
        ListLastCommitsForTreeTracingRequest(&request)
    );
    if request.revision.is_empty() {
        return Err(Status::invalid_argument("empty revision"));
    }

    if request.limit == 0 {
        return empty_response_stream();
    }

    let offset = request
        .offset
        .try_into()
        // let's not image for more than 1 sec that usize may be smaller than u32
        .map_err(|_| Status::invalid_argument("offset negative"))?;

    let limit: usize = request
        .limit
        .try_into()
        .map_err(|_| Status::invalid_argument("limit negative"))?;

    let config = config.clone();
    let store_vfs = repo_store_vfs(&config, &request.repository)
        .await
        .map_err(default_repo_spec_error_status)?;

    match gitlab_revision_node_prefix(&store_vfs, request.revision.as_bytes())
        .await
        .map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))?
    {
        None => {
            info!("Revision not resolved");
            Err(Status::internal("exit status 128"))
        }
        Some(node_prefix) => load_changelog_and_stream(
            config.clone(),
            request.clone(),
            default_repo_spec_error_status,
            move |req, repo, cl, tx| {
                // no literal_pathspec, see doc-comment of the 'in_thread' method
                if let Err(e) = list_lcft_in_thread(req, repo, cl, node_prefix, offset, limit, &tx)
                {
                    let details = match e {
                        RevlogError::InvalidRevision(_) => "exit status 128".to_owned(),
                        e => format!("Repository corruption {:?}", e),
                    };
                    tx.send(Err(Status::internal(details)))
                }
            },
        ),
    }
}

/// Similar to [`lfcp_in_thread`] for `ListLastCommitsForTree`
fn list_lcft_in_thread(
    req: ListLastCommitsForTreeRequest,
    repo: &Repo,
    cl: &Changelog,
    node_prefix: NodePrefix,
    offset: usize,
    limit: usize,
    tx: &BlockingResponseSender<ListLastCommitsForTreeResponse>,
) -> Result<(), RevlogError> {
    let mut req_path = req.path;
    if &req_path == b"." || &req_path == b"/" || &req_path == b"./" {
        req_path.clear();
    }

    let rev = cl.rev_from_node(node_prefix)?;
    if rev == NULL_REVISION {
        tx.send(Err(Status::internal("exit status 128")));
        return Ok(());
    }

    if req_path.last().map_or(b'/', |c| *c) != b'/' {
        if offset > 0 {
            return Ok(()); // we have exactly one result, hence offset skips it
        }
        // No glob matching, despite what the commit history of Gitaly says.
        // Gitaly's LLCFT implementation is based on a first path by `git ls-tree`
        // whose man page claims that paths are patterns. However, be it in our
        // Gitaly Comparison tests or on the command-line we never succeded to
        // have any glob-like expansion.
        // Example: git ls-tree -r --full-name branch/default -- 'fo*'
        // was supposed to match 'foo' and gave nothing.
        //
        // There is no response to send if lcfp_ancestors_walk returns None
        if let Some(cl_entry) =
            lcfp_ancestors_walk(git::GitLiteralPathSpec::new(&req_path), cl, rev)?
        {
            tx.send(Ok(ListLastCommitsForTreeResponse {
                commits: vec![CommitForTree {
                    path_bytes: req_path.to_vec(),
                    commit: Some(message::commit(cl_entry)?),
                }], // commit_for_tree(b"", cl_entry, path)?],
            }));
        } else {
            warn!("Path not found or not a directory")
        }
        return Ok(());
    }

    let manifestlog = repo.manifestlog()?;
    let changelog_entry = cl.entry_for_unchecked_rev(rev.into())?;
    let manifest = manifestlog.data_for_node(changelog_entry.data()?.manifest_node()?.into())?;

    let trimmed = if req_path.is_empty() {
        &req_path
    } else {
        &req_path[0..req_path.len() - 1]
    };
    if let Some((subtrees, file_paths)) =
        ls_path_sorted_dirs_first(&manifest, trimmed, offset, limit)?
    {
        let (subtree_cl_entries, file_path_cl_entries) =
            lcft_ancestors_walk(&req_path, subtrees, file_paths, cl, rev)?;
        stream_chunks(
            tx,
            subtree_cl_entries
                .into_iter()
                .chain(file_path_cl_entries)
                .map(|(path, cl_entry)| commit_for_tree(&req_path, cl_entry, path)),
            |chunk, _is_first| ListLastCommitsForTreeResponse { commits: chunk },
            |e| Status::internal(format!("Repository corruption: {}", e)),
        );
    } else {
        info!("Unknown directory (revision resolved as {:x})", node_prefix);
    }
    Ok(())
}

fn commit_for_tree(
    parent_slash: &[u8],
    entry: ChangelogEntry,
    path: Vec<u8>,
) -> Result<CommitForTree, RevlogError> {
    let mut full_path = Vec::with_capacity(parent_slash.len() + path.len());
    full_path.extend_from_slice(parent_slash);
    full_path.extend_from_slice(&path);
    Ok(CommitForTree {
        commit: Some(message::commit(entry)?),
        path_bytes: full_path,
    })
}

/// Inner `LastCommitsforTree` result type (for subtrees or files)
type LastCommitsForTreeMap<'cl> = BTreeMap<Vec<u8>, ChangelogEntry<'cl>>;

/// Walk the changelog for `ListLastCommitsForTree`
///
/// Performance notes:
///
/// - We chose [`ChangelogEntry`] in returned values.
///   As each is expected to appear several times, this means they
///   are cloned, and that is reasonably cheap (the bulk of the payload is
///   just a reference), at least cheaper than performing lookups and
///   conversions that are already done since we start from them.
/// - We still have to clone matches from `subtrees` because the
///   [extract_if](`BTreeSet#method.extract_if`) method of `BTreeSet` is currently unstable.
fn lcft_ancestors_walk<'cl>(
    parent_slash: &[u8],
    mut subtrees: BTreeSet<Vec<u8>>,
    mut file_paths: BTreeSet<Vec<u8>>,
    cl: &'cl Changelog,
    rev: Revision,
) -> Result<(LastCommitsForTreeMap<'cl>, LastCommitsForTreeMap<'cl>), RevlogError> {
    let mut subtree_cl_entries = BTreeMap::new();
    let mut file_cl_entries = BTreeMap::new();
    let mut found_subtrees_tmp = Vec::new();

    for anc_rev in
        AncestorsIterator::new(cl, [rev], NULL_REVISION, true).map_err(revlog_err_from_graph_err)?
    {
        if subtrees.is_empty() && file_paths.is_empty() {
            break;
        }

        let cl_entry =
            cl.entry_for_unchecked_rev(anc_rev.map_err(revlog_err_from_graph_err)?.into())?;
        changeset_files_match_subtrees_and_files(
            cl_entry.data()?.files(),
            parent_slash,
            &mut subtrees,
            &mut file_paths,
            &mut found_subtrees_tmp,
            |found_tree| {
                subtree_cl_entries.insert(found_tree, cl_entry.clone());
            },
            |found_file| {
                file_cl_entries.insert(found_file, cl_entry.clone());
            },
        );
    }

    Ok((subtree_cl_entries, file_cl_entries))
}

/// For a given iterator of changeset files, search and register for subtree and file matches
/// inside a given tree.
///
/// Singled out to be unit-testable.
///
/// 'parent_slash` is the path of the tree to look into, with included trailing slash
/// `found_subtrees` is a reusable vector to park matching subtrees before handing them over to
/// the `register_found_subtrees` closure.
fn changeset_files_match_subtrees_and_files<'cl, RS, RF>(
    cl_files: impl Iterator<Item = &'cl HgPath>,
    parent_slash: &[u8],
    subtrees: &mut BTreeSet<Vec<u8>>,
    file_paths: &mut BTreeSet<Vec<u8>>,
    found_subtrees_tmp: &mut Vec<Vec<u8>>,
    mut register_found_subtree: RS,
    mut register_found_file: RF,
) where
    RS: FnMut(Vec<u8>),
    RF: FnMut(Vec<u8>),
{
    let mut subtrees_iter = subtrees.iter();
    let mut current_subtree = subtrees_iter.next();
    let mut in_parent = false;

    // a binary search for beginning of parent dir is not possible: all we have is
    // an iterator on affected files: we'd need to collect in a vector. It is dubious
    // it could be a performance improvement.
    for cl_full_path in cl_files {
        if !cl_full_path.as_bytes().starts_with(parent_slash) {
            if in_parent {
                break;
            }
            continue;
        }
        in_parent = true;
        let cl_path = &cl_full_path.as_bytes()[parent_slash.len()..];
        if let Some(file_path) = file_paths.take(cl_path) {
            register_found_file(file_path);
            continue;
        }

        // Iterating on `current_subtree`, yet only in matching cases.
        // If not matching, `current_subtree` is to be considered again for next value of `cl_path`.
        while let Some(tree_path) = current_subtree {
            if tree_path.as_slice() > cl_path {
                // if `tree_path` is greater than `cl_path`, it cannot be a prefix
                // of `cl_path`, even less with an added slash. By transitivity of
                // the lexicographical ordering, the same holds for all subsequent
                // entries emitted by `subtrees_iter`.
                break;
            }

            if cl_path.starts_with(tree_path) {
                if cl_path.get(tree_path.len()).cloned() == Some(b'/') {
                    // we need to clone `tree_path`, otherwise it is a live shared ref to
                    // the set, and it blocks all mutations, something that the `extract_if`
                    // method would probably help with.
                    found_subtrees_tmp.push(tree_path.clone());
                } else {
                    // tree_path is a prefix of cl_path, but not because the latter is a file inside
                    // the former. We must prevent going to the next value of tree_path
                    eprintln!("Break2");
                    break;
                }
            }

            current_subtree = subtrees_iter.next();
        }
    }
    // Keeping the allocation of the `found_subtrees` vector
    for tree_path in found_subtrees_tmp.drain(..) {
        subtrees.remove(&tree_path);
        register_found_subtree(tree_path);
    }
}

#[cfg(test)]
mod tests {

    use super::*;

    fn cl_files_match(
        parent_slash: &[u8],
        cl_files: Vec<&'static str>,
        subtrees: Vec<&'static str>,
        file_paths: Vec<&'static str>,
    ) -> (Vec<String>, Vec<String>) {
        let mut found_trees = Vec::new();
        let mut found_files = Vec::new();
        let mut found_subtrees_tmp = Vec::new();

        let cl_files: Vec<_> = cl_files
            .into_iter()
            .map(|f| HgPath::new(f.as_bytes()))
            .collect();
        let mut subtrees: BTreeSet<_> = subtrees
            .into_iter()
            .map(|t| t.as_bytes().to_vec())
            .collect();
        let mut file_paths: BTreeSet<_> = file_paths
            .into_iter()
            .map(|f| f.as_bytes().to_vec())
            .collect();

        changeset_files_match_subtrees_and_files(
            cl_files.into_iter(),
            parent_slash,
            &mut subtrees,
            &mut file_paths,
            &mut found_subtrees_tmp,
            |found_tree| found_trees.push(found_tree),
            |found_file| found_files.push(found_file),
        );
        (
            found_trees
                .into_iter()
                .map(|t| String::from_utf8(t).unwrap())
                .collect(),
            found_files
                .into_iter()
                .map(|f| String::from_utf8(f).unwrap())
                .collect(),
        )
    }

    #[test]
    fn test_cl_files_match() {
        // basic case
        assert_eq!(
            cl_files_match(
                b"sub/",
                vec!["foo", "sub/a", "sub/b/b", "sub/b/c", "sub/bar"],
                vec!["b"],
                vec!["bar"]
            ),
            (vec!["b".to_owned()], vec!["bar".to_owned()])
        );

        // recall that `.` is smaller than `/`. This used to fail in a previous revision
        // because subtrees iterator was advanced too liberally.
        assert_eq!(
            cl_files_match(
                b"sub/",
                vec!["foo", "sub/b.", "sub/b/b", "sub/b/c", "sub/bar"],
                vec!["b"],
                vec!["b."]
            ),
            (vec!["b".to_owned()], vec!["b.".to_owned()])
        );

        assert_eq!(
            cl_files_match(
                b"sub/",
                vec!["foo", "sub/b.", "sub/b/b", "sub/b/c", "sub/bar"],
                vec!["b"],
                vec![]
            ),
            (vec!["b".to_owned()], vec![])
        );
    }

    #[test]
    fn test_cl_files_match_issue_heptapod_1642() {
        // commit files taken from mercurial-devel@9624bf057c2
        assert_eq!(
            cl_files_match(
                b"tests/",
                vec![
                    "hgext/phabricator.py",
                    "tests/phabricator/phabupdate-revs.json",
                    "tests/test-phabricator.t"
                ],
                vec!["gpg", "phabricator", "sslcerts", "svn", "testlib"],
                vec![
                    ".balto.toml",
                    "README",
                    "binfile.bin",
                    "bzr-definitions",
                    "cgienv",
                    "check-gendoc"
                ]
            ),
            (vec!["phabricator".to_owned()], vec![])
        );
    }
}
