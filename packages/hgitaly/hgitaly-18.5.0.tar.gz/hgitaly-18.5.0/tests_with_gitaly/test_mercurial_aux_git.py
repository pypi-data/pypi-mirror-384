from heptapod.testhelpers.git import GitRepo

from hgitaly.stub.shared_pb2 import Repository
from hgitaly.stub.repository_pb2 import (
    CreateBundleRequest,
    CreateRepositoryFromBundleRequest,
    RepositorySizeRequest,
)
from hgitaly.stub.mercurial_aux_git_pb2 import (
    AuxGitCommitMappingRequest,
)
from hgitaly.stub.mercurial_aux_git_pb2_grpc import MercurialAuxGitServiceStub
from hgitaly.testing.storage import stowed_away_git_repo_path

import pytest
from . import skip_comparison_tests


if skip_comparison_tests():  # pragma no cover
    pytestmark = pytest.mark.skip


def test_create_bundle_create_from_bundle(gitaly_rhgitaly_comparison_native,
                                          tmpdir,
                                          server_repos_root):
    fixture = gitaly_rhgitaly_comparison_native
    wrapper = fixture.hg_repo_wrapper
    src_git_repo = fixture.git_repo
    wrapper.write_commit('foo', message="Some foo")
    wrapper.command('hpd-export-native-to-git')
    # export worked
    assert set(src_git_repo.branches()) == {b'branch/default'}

    rpc_helper = fixture.rpc_helper(
        hg_server='rhgitaly',
        stub_cls=MercurialAuxGitServiceStub,
        method_name='AuxGitCreateBundle',
        request_cls=CreateBundleRequest,
        streaming=True,
    )

    bundle_data = [r.data for r in rpc_helper.rpc('hg')]

    # direct check
    clone = GitRepo.create_from_bundle_data(
        tmpdir / 'restored.git',
        bundle_data,
        stream=True,
        tmpdir=tmpdir
    )
    assert clone.branch_titles() == {b'branch/default': b'Some foo'}

    # remounting via rpc
    rpc_helper = fixture.rpc_helper(
        hg_server='rhgitaly',
        stub_cls=MercurialAuxGitServiceStub,
        method_name='AuxGitCreateFromBundle',
        request_cls=CreateRepositoryFromBundleRequest,
        streaming_request_field='data',
    )

    restored_gl_repo = Repository(
        relative_path="restore2.git",
        storage_name=fixture.gitaly_repo.storage_name
    )

    # rpc_helper does not know how to stream on bytes, and we need
    # a custom repository field, let's get down to manual mode
    def stream_requests():
        first = True
        for data in bundle_data:
            if first:
                kw = dict(repository=restored_gl_repo, data=data)
            else:
                kw = dict(data=data)  # pragma no cover
            yield CreateRepositoryFromBundleRequest(**kw)
            first = False

    rpc_helper.stubs['hg'].AuxGitCreateFromBundle(stream_requests())

    clone2 = GitRepo(stowed_away_git_repo_path(server_repos_root,
                                               'restore2.git'))
    assert clone2.branch_titles() == {b'branch/default': b'Some foo'}


def test_repository_size(gitaly_rhgitaly_comparison_native):
    fixture = gitaly_rhgitaly_comparison_native
    wrapper = fixture.hg_repo_wrapper
    src_git_repo = fixture.git_repo
    wrapper.write_commit('foo', message="Some foo",
                         content=b"foobar" * 17000)
    wrapper.command('hpd-export-native-to-git')
    # export worked
    assert set(src_git_repo.branches()) == {b'branch/default'}

    rpc_helper = fixture.rpc_helper(
        hg_server='rhgitaly',
        stub_cls=MercurialAuxGitServiceStub,
        method_name='AuxGitRepositorySize',
        request_cls=RepositorySizeRequest,
    )
    # results may vary according to how system reports size of small files
    assert rpc_helper.rpc('hg').size > 20


def test_commit_mapping(gitaly_rhgitaly_comparison_native):
    fixture = gitaly_rhgitaly_comparison_native
    wrapper = fixture.hg_repo_wrapper
    src_git_repo = fixture.git_repo
    cs0 = wrapper.write_commit('foo')
    hg_sha0 = cs0.hex().decode()
    cs1 = wrapper.write_commit('bar', parent=cs0, branch='other')
    hg_sha1 = cs1.hex().decode()
    wrapper.command('hpd-export-native-to-git')
    # export worked
    git_branches = src_git_repo.branches()
    assert set(git_branches) == {b'branch/default', b'branch/other'}
    git_sha0 = git_branches[b'branch/default']['sha'].decode()
    git_sha1 = git_branches[b'branch/other']['sha'].decode()

    rpc_helper = fixture.rpc_helper(
        hg_server='rhgitaly',
        stub_cls=MercurialAuxGitServiceStub,
        method_name='AuxGitCommitMapping',
        request_cls=AuxGitCommitMappingRequest,
    )

    unknown = '12fe34ca' * 5

    def rpc(*ids, **kw):
        return rpc_helper.rpc('hg', ids=ids, **kw).ids

    assert rpc(git_sha0) == [hg_sha0]
    assert rpc(git_sha1, git_sha0) == [hg_sha1, hg_sha0]
    assert rpc(git_sha0, git_sha0) == [hg_sha0, hg_sha0]
    assert rpc(git_sha0, git_sha1) == [hg_sha0, hg_sha1]
    assert rpc(hg_sha0, hg_sha1, reverse=True) == [git_sha0, git_sha1]

    assert rpc(unknown) == ['']
    assert rpc(unknown, reverse=True) == ['']
    assert rpc(git_sha0, unknown) == [hg_sha0, '']
    assert rpc(unknown, git_sha0) == ['', hg_sha0]
