from pathlib import Path
import pytest

import grpc
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

from hgitaly.service.interceptors import (
    RequestLoggerInterceptor,
)
from hgitaly.service.analysis import AnalysisServicer
from hgitaly.service.blob import BlobServicer
from hgitaly.service.commit import CommitServicer
from hgitaly.service.ref import RefServicer
from hgitaly.service.diff import DiffServicer
from hgitaly.service.mercurial_changeset import MercurialChangesetServicer
from hgitaly.service.mercurial_operations import MercurialOperationsServicer
from hgitaly.service.mercurial_repository import MercurialRepositoryServicer
from hgitaly.service.operations import OperationServicer
from hgitaly.service.repository import RepositoryServicer
from hgitaly.service.server import ServerServicer

from hgitaly.stub.analysis_pb2_grpc import (
    add_AnalysisServiceServicer_to_server,
)
from hgitaly.stub.blob_pb2_grpc import add_BlobServiceServicer_to_server
from hgitaly.stub.commit_pb2_grpc import add_CommitServiceServicer_to_server
from hgitaly.stub.ref_pb2_grpc import add_RefServiceServicer_to_server
from hgitaly.stub.diff_pb2_grpc import add_DiffServiceServicer_to_server
from hgitaly.stub.operations_pb2_grpc import (
    add_OperationServiceServicer_to_server
)
from hgitaly.stub.repository_pb2_grpc import (
    add_RepositoryServiceServicer_to_server
)
from hgitaly.stub.mercurial_changeset_pb2_grpc import (
    add_MercurialChangesetServiceServicer_to_server
)
from hgitaly.stub.mercurial_operations_pb2_grpc import (
    add_MercurialOperationsServiceServicer_to_server
)
from hgitaly.stub.mercurial_repository_pb2_grpc import (
    add_MercurialRepositoryServiceServicer_to_server
)
from hgitaly.stub.server_pb2_grpc import add_ServerServiceServicer_to_server
from hgitaly.testing.storage import storage_path


@pytest.fixture(scope='module')
def grpc_interceptors():
    return [RequestLoggerInterceptor(),
            ]


@pytest.fixture(scope='module')
def grpc_server(_grpc_server, grpc_addr, server_repos_root):
    storages = dict(
        default=str(storage_path(server_repos_root, 'default')).encode(),
    )

    add_AnalysisServiceServicer_to_server(AnalysisServicer(storages),
                                          _grpc_server)
    add_BlobServiceServicer_to_server(BlobServicer(storages),
                                      _grpc_server)
    add_CommitServiceServicer_to_server(CommitServicer(storages),
                                        _grpc_server)
    add_RefServiceServicer_to_server(RefServicer(storages),
                                     _grpc_server)
    add_DiffServiceServicer_to_server(DiffServicer(storages),
                                      _grpc_server)
    add_OperationServiceServicer_to_server(
        OperationServicer(storages),
        _grpc_server)
    add_RepositoryServiceServicer_to_server(
        RepositoryServicer(storages),
        _grpc_server)
    add_MercurialChangesetServiceServicer_to_server(
        MercurialChangesetServicer(storages),
        _grpc_server)
    add_MercurialOperationsServiceServicer_to_server(
        MercurialOperationsServicer(storages),
        _grpc_server)
    add_MercurialRepositoryServiceServicer_to_server(
        MercurialRepositoryServicer(storages),
        _grpc_server)
    add_ServerServiceServicer_to_server(ServerServicer(storages),
                                        _grpc_server)
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, _grpc_server)

    _grpc_server.add_insecure_port(grpc_addr)
    _grpc_server.start()
    yield _grpc_server
    _grpc_server.stop(grace=None)


@pytest.fixture(scope='module')
def server_repos_root(tmp_path_factory):
    return Path(tmp_path_factory.mktemp("server-repos"))
