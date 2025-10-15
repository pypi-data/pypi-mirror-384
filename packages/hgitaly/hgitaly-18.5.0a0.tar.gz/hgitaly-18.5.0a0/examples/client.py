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

from hgitaly.stub import (
    ref_pb2,
    ref_pb2_grpc,
)
from hgitaly.stub.shared_pb2 import (
    Repository,
)

PID = os.getpid()


def rpc(channel, storage, rel_path):
    """An example RPC call."""
    ref_stub = ref_pb2_grpc.RefServiceStub(channel)
    return ref_stub.FindAllBranchNames(
        ref_pb2.FindAllBranchNamesRequest(
            repository=Repository(relative_path=rel_path,
                                  storage_name=storage))
    )


def run(storage, rel_path):
    with grpc.insecure_channel('localhost:9237') as channel:
        resp = rpc(channel, storage, rel_path)
        print("%d: got branch name chunks of size %r" % (
            PID,
            [len(chunk.names) for chunk in resp]
        ))


if __name__ == '__main__':
    for _ in range(100):
        run('default', 'test-repo-relative-path')
