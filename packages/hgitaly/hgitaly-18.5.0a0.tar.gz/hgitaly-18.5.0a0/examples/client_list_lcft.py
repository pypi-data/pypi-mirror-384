# Copyright 2020 Georges Racinet <georges.racinet@octobus.net>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
#
# SPDX-License-Identifier: GPL-2.0-or-later
"""HGitaly example client.

Can be expanded upon for debugging sessions.

To run multiple concurrent
"""
import grpc
import os
from pprint import pprint

from hgitaly.stub import (
    commit_pb2,
    commit_pb2_grpc,
)
from hgitaly.stub.shared_pb2 import (
    Repository,
)

PID = os.getpid()


def rpc(channel, storage, rel_path, **kw):
    """An example RPC call."""
    client_stub = commit_pb2_grpc.CommitServiceStub(channel)
    return client_stub.ListLastCommitsForTree(
        commit_pb2.ListLastCommitsForTreeRequest(
            repository=Repository(relative_path=rel_path,
                                  storage_name=storage),
            **kw)
    )


def run(rel_path, storage='default', **kw):
    with grpc.insecure_channel('localhost:9237') as channel:
        paths = [(ct.path_bytes, ct.commit.id[:11])
                 for resp in rpc(channel, storage, rel_path, **kw)
                 for ct in resp.commits]
        print("Got %d paths" % len(paths))
        pprint(paths)


if __name__ == '__main__':
    run("@hashed/6f/4b/"
        "6f4b6612125fb3a0daecd2799dfd6c9c299424fd920f9b308110a2c1fbd8f443.git",
        revision=b'branch/default',
        path=b"tests/",
        offset=0,
        limit=26,
        )
