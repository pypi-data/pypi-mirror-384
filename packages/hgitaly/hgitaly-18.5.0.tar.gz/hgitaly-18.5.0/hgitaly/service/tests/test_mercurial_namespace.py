# Copyright 2025 Georges Racinet <georges.racinet@cloudcrane.io>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
#
# SPDX-License-Identifier: GPL-2.0-or-later
import tarfile
import os
import shutil

import pytest

from hgitaly.stub.mercurial_namespace_pb2 import (
    MercurialNamespacesConfigArchive,
    BackupMercurialNamespacesConfigRequest,
)
from hgitaly.stub.mercurial_namespace_pb2_grpc import (
    MercurialNamespaceServiceStub,
)

from .fixture import ServiceFixture

parametrize = pytest.mark.parametrize


class NamespaceFixture(ServiceFixture):
    stub_cls = MercurialNamespaceServiceStub

    def backup(self, target, **kw):
        with open(target, 'wb') as targetf:
            for resp in self.stub.BackupMercurialNamespacesConfig(
                    BackupMercurialNamespacesConfigRequest(**kw)):
                targetf.write(resp.data)

    def restore(self, tarball, **kw):
        with open(tarball, 'rb') as fobj:
            def gen():
                while True:
                    r = fobj.read(100)
                    yield MercurialNamespacesConfigArchive(data=r)
                    if not r:
                        break

            return self.stub.RestoreMercurialNamespacesConfig(gen())


@pytest.fixture
def namespace_fixture(grpc_channel, server_repos_root):
    with NamespaceFixture(grpc_channel, server_repos_root) as fixture:
        yield fixture


def test_backup_restore(namespace_fixture, server_repos_root, tmpdir):
    fixture = namespace_fixture

    group1 = server_repos_root / 'default/group1'
    group2 = server_repos_root / 'default/group2'
    group3 = server_repos_root / 'default/group3'
    subgroup = group2 / 'sub'
    os.makedirs(group1)
    os.makedirs(subgroup)
    os.makedirs(group3)
    (group1 / 'hgrc').write_text("something\n")
    (group2 / 'hgrc').write_text("some for two\n")
    include = "%include ../hgrc\n"
    (subgroup / 'hgrc').write_text(include)
    # there is a repo at storage root (part of standard fixture),
    # let's add some more stuff that we do not want
    hashed = server_repos_root / 'default/@hashed'
    os.makedirs(hashed)
    (hashed / 'hgrc').write_text("unwnated\n")
    (server_repos_root / 'default/stray-file').write_text(
        "ignore top-level files")

    tarball = tmpdir / 'testbak1.tgz'
    fixture.backup(tmpdir / 'testbak1.tgz')

    with tarfile.open(tarball) as tarf:
        assert set(tarf.getnames()) == {
            'group1/hgrc',
            'group2/hgrc',
            'group2/sub/hgrc',
            }

    shutil.rmtree(group1)
    shutil.rmtree(group2)
    shutil.rmtree(group3)
    fixture.restore(tarball)

    assert (group1 / 'hgrc').read_text() == "something\n"
    assert (group2 / 'hgrc').read_text() == "some for two\n"
    assert (subgroup / 'hgrc').read_text() == include
    assert not group3.exists()
