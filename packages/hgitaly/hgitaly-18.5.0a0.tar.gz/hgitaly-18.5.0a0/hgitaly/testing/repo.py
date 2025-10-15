# Copyright 2025 Georges Racinet <georges.racinet@cloudcrane.io>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
#
# SPDX-License-Identifier: GPL-2.0-or-later
from mercurial.match import always as match_always


def assert_empty_repo_status(repo_wrapper, ctx_from=None, ctx_to=None):
    repo = repo_wrapper.repo
    wctx = repo[None]
    if ctx_from is None:
        ctx_from = wctx.p1()
    if ctx_to is None:
        ctx_to = wctx
    status = repo_wrapper.repo.status(ctx_from, ctx_to, match_always(),
                                      ignored=True,
                                      clean=False,
                                      unknown=True,
                                      listsubrepos=False)
    assert not status.modified
    assert not status.added
    assert not status.removed
    assert not status.deleted
    assert not status.unknown
