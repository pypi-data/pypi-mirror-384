# Copyright 2025 Georges Racinet <georges.racinet@cloudcrane.io>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
#
# SPDX-License-Identifier: GPL-2.0-or-later
import logging
import os
import tarfile
import tempfile

from grpc import StatusCode

from ..logging import LoggerAdapter
from ..stream import (
    WRITE_BUFFER_SIZE,
    streaming_request_tempfile_extract,
)
from ..stub.mercurial_namespace_pb2 import (
    MercurialNamespacesConfigArchive,
    RestoreMercurialNamespacesConfigResponse,
)
from ..stub.mercurial_namespace_pb2_grpc import (
    MercurialNamespaceServiceServicer,
)
from ..servicer import HGitalyServicer

base_logger = logging.getLogger(__name__)


class MercurialNamespaceServicer(MercurialNamespaceServiceServicer,
                                 HGitalyServicer):
    """MercurialNamespaceService implementation.

    The ordering of methods in this source file is the same as in the proto
    file.
    """

    def unique_storage_root(self, context):
        if len(self.storages) > 1:  # pragma no cover
            # we will need something to accomodate the case where
            # several storages are in a common root directory
            # or just have HGitaly (like RHGitaly) handle only one storage,
            # but it is not the GitLab standard.
            # another option (quite premature) is to accept the fact that
            # this will be duplicated for each storage, not only each
            # server.
            context.abort(
                StatusCode.FAILED_PRECONDITION,
                "cannot efficiently backup namespaces configurations "
                "when handling several storages"
            )
        return next(iter(self.storages.values()))

    def BackupMercurialNamespacesConfig(self, request, context):
        logger = LoggerAdapter(base_logger, context)
        root = self.unique_storage_root(context)
        with tempfile.TemporaryFile() as tmpf:
            with tarfile.open(fileobj=tmpf, mode='w:gz') as tarf:
                for tld in os.listdir(root):
                    if tld in (b'+gitaly', b'+hgitaly', b'@hashed'):
                        continue
                    tld_abs = os.path.join(root, tld)
                    if not os.path.isdir(tld_abs):
                        continue
                    if b'.hg' in os.listdir(tld_abs):
                        # This is a Mercurial repository, should not
                        # happen in normal operation, but it does in tests
                        # let's bail
                        continue

                    logger.debug("Dumping namespace hgrc files for "
                                 "top-level dir %r", tld)
                    for (dir_abspath, subdirs, files) in os.walk(tld_abs):
                        if b'hgrc' in files:
                            file_abspath = os.path.join(dir_abspath, b'hgrc')
                            file_relpath = os.path.relpath(file_abspath,
                                                           root)
                            # tarfile wants to operate on str, not bytes
                            tarf.add(file_abspath,
                                     arcname=os.fsdecode(file_relpath))
            tmpf.seek(0)
            first = True
            while True:
                chunk = tmpf.read(WRITE_BUFFER_SIZE)
                if not chunk and not first:
                    break
                first = False
                yield MercurialNamespacesConfigArchive(data=chunk)

    def RestoreMercurialNamespacesConfig(self, request, context):
        logger = LoggerAdapter(base_logger, context)
        with streaming_request_tempfile_extract(
                request, context) as (_options, tmpf):
            tmpf.flush()
            logger.info("Extracting tarball for Namespaces hgrc files")
            with tarfile.open(fileobj=tmpf, mode='r:gz') as tarf:
                # The client being the Rails app, it is deeply trusted
                tarf.extractall(
                    path=os.fsdecode(self.unique_storage_root(context)))
        return RestoreMercurialNamespacesConfigResponse()
