use std::fmt::{Debug, Formatter};
use std::iter::Iterator;
use std::sync::Arc;

use itertools::Itertools;
use tonic::Status;
use tracing::info;

use hg::revlog::changelog::Changelog;
use hg::revlog::{Graph, GraphError, NodePrefix, Revision, RevlogError, NULL_REVISION};
use hg::AncestorsIterator;

use super::revlog_err_from_graph_err;
use crate::config::Config;
use crate::git::GitRevSpec;
use crate::gitaly::{find_commits_request, FindCommitsRequest, FindCommitsResponse, Repository};
use crate::gitlab::revision::gitlab_revision_node_prefix;
use crate::message;
use crate::repository::{
    default_repo_spec_error_status, load_changelog_and_stream, repo_store_vfs, RequestWithRepo,
};
use crate::streaming::{
    empty_response_stream, stream_chunks, BlockingResponseSender, ResultResponseStream,
};
use crate::util::{bytes_strings_as_str, tracing_span_id};

struct FindCommitsTracingRequest<'a>(&'a FindCommitsRequest);

impl Debug for FindCommitsTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FindCommitsRequest")
            .field("repository", &self.0.repository)
            .field("revision", &String::from_utf8_lossy(&self.0.revision))
            .field("follow", &self.0.follow)
            .field("paths", &bytes_strings_as_str(&self.0.paths))
            .finish()
    }
}

impl RequestWithRepo for FindCommitsRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

fn stream_find_commits(
    cl: &Changelog,
    iter: impl Iterator<Item = Result<Revision, GraphError>>,
    tx: &BlockingResponseSender<FindCommitsResponse>,
    offset: usize,
    limit: usize,
) -> Result<(), RevlogError> {
    stream_chunks(
        tx,
        iter.filter(|r| *r != Ok(NULL_REVISION))
            .get(offset..offset + limit)
            .map(|r| {
                r.map_err(|e| RevlogError::Other(revlog_err_from_graph_err(e)))
                    .and_then(|r| cl.entry_for_unchecked_rev(r.into()))
                    .and_then(|e| message::commit(e))
            }),
        |chunk, _is_first| FindCommitsResponse { commits: chunk },
        |e| {
            Status::internal(format!(
                "Repository corruption in ancestors iteration: {}",
                e
            ))
        },
    );
    Ok(())
}

fn stream_find_commits_ancestors(
    cl: &Changelog,
    node_prefix: NodePrefix,
    skip_merges: bool,
    offset: usize,
    limit: usize,
    tx: &BlockingResponseSender<FindCommitsResponse>,
) -> Result<(), RevlogError> {
    let init_rev = cl.rev_from_node(node_prefix)?;
    let iter = AncestorsIterator::new(cl, [init_rev], NULL_REVISION, true)
        .map_err(revlog_err_from_graph_err)?;
    if skip_merges {
        let iter = iter.filter(|r| {
            match *r {
                Err(_) => true, // let the error propagate
                Ok(rev) => {
                    // ignoring errors in parents: normally, the ancestors
                    // iterator should get the same
                    // error, so it does not harm to just ignore it.
                    match cl.parents(rev) {
                        Err(_) => true,
                        Ok(parents) => parents[0] == NULL_REVISION || parents[1] == NULL_REVISION,
                    }
                }
            }
        });
        stream_find_commits(cl, iter, tx, offset, limit)
    } else {
        stream_find_commits(cl, iter, tx, offset, limit)
    }
}

pub async fn inner_impl(
    config: &Arc<Config>,
    request: &FindCommitsRequest,
) -> ResultResponseStream<FindCommitsResponse> {
    tracing_span_id!();
    info!(
        "Processing, request={:?}",
        FindCommitsTracingRequest(request)
    );
    if request.limit < 0 {
        return Err(Status::invalid_argument(format!(
            "Got negative limit {}",
            request.limit,
        )));
    }
    let limit = request.limit as usize;
    if request.offset < 0 {
        return Err(Status::invalid_argument(format!(
            "Got negative offset {}",
            request.offset,
        )));
    }
    let offset = request.offset as usize;

    if limit == 0 {
        return empty_response_stream();
    }
    // `FindCommits` gets called a lot with `follow=true` but without `paths` in which case the
    // `follow` has no imlications (must be a default options system on the client side). It is
    // important not to fall back in these cases
    if !request.paths.is_empty() {
        return Err(Status::unimplemented("with paths"));
    }
    if !request.include_referenced_by.is_empty() || request.include_shortstat {
        return Err(Status::unimplemented("with short stats and referenced by"));
    }
    let topo: i32 = find_commits_request::Order::Topo.into();
    if request.order == topo {
        return Err(Status::unimplemented("with topological sorting"));
    }
    if request.all {
        return Err(Status::unimplemented("with 'all' option"));
    }
    if !request.author.is_empty() {
        return Err(Status::unimplemented("with author"));
    }
    if !request.message_regex.is_empty() {
        return Err(Status::unimplemented("with message_regex"));
    }
    if request.after.is_some() || request.before.is_some() {
        return Err(Status::unimplemented("with date options"));
    }
    let revision: &[u8] = if request.revision.is_empty() {
        b"HEAD"
    } else {
        &request.revision
    };
    let revision = match GitRevSpec::parse(revision) {
        GitRevSpec::Revision(rev) => rev,
        rs => {
            info!("revision parsed as {:?}", rs);
            return Err(Status::unimplemented("Git pseudo ranges"));
        }
    };

    let config = config.clone();
    let store_vfs = repo_store_vfs(&config, &request.repository)
        .await
        .map_err(default_repo_spec_error_status)?;
    match gitlab_revision_node_prefix(&store_vfs, revision)
        .await
        .map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))?
    {
        None => {
            // using the sidecar rather than tedious Rust structured errors
            Err(Status::unimplemented("when revision is not resolved"))
        }
        Some(node_prefix) => {
            info!("Revision resolved as {:x}", &node_prefix);
            load_changelog_and_stream(
                config.clone(),
                request.clone(),
                default_repo_spec_error_status,
                move |req, _repo, cl, tx| {
                    if let Err(e) = stream_find_commits_ancestors(
                        cl,
                        node_prefix,
                        req.skip_merges,
                        offset,
                        limit,
                        &tx,
                    ) {
                        tx.send(Err(Status::internal(format!(
                            "Repository corruption {:?}",
                            e
                        ))));
                    }
                },
            )
        }
    }
}
