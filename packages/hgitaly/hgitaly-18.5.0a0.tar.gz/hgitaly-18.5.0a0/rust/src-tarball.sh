#!/bin/sh

set -e

if [ -z "$1" ]; then
    echo "usage: $0 HGITALY_VERSION";
    exit 1
fi

HGITALY_VERSION=$1

set -u

DIST_HGITALY=hgitaly-${HGITALY_VERSION}
DIST_RHGITALY=rhgitaly-${HGITALY_VERSION}
TARBALL=${DIST_RHGITALY}.tgz

cd `dirname $0`

mkdir -p ../dist
cd ../dist
DEPS_DIR=../rust/dependencies

rm -rf ${DIST_HGITALY} ${DIST_RHGITALY}

echo "Performing extractions"
hg archive ${DIST_HGITALY}

rm -f ${DIST_HGITALY}/rust/dependencies/hg-core # cp -Lrf cannot do this
cp -Lr ${DEPS_DIR}/hg-core ${DIST_HGITALY}/rust/dependencies
mkdir ${DIST_HGITALY}/rust/mercurial/
# a bit lame for this file not to be under rust/dependencies,
# but that is the result of the relative path in hg-core/src/config/mod.rs,
# we're lucky it does not climb up outside of our package root.
cp ${DEPS_DIR}/mercurial/mercurial/configitems.toml \
   ${DEPS_DIR}/mercurial/mercurial/bdiff.* \
   ${DEPS_DIR}/mercurial/mercurial/bitmanipulation.h \
   ${DEPS_DIR}/mercurial/mercurial/compat.h \
   ${DIST_HGITALY}/rust/mercurial/

mkdir -p ${DIST_RHGITALY}/hgitaly/linguist
for path in hgitaly/VERSION protos rust; do
    cp -r ${DIST_HGITALY}/${path} ${DIST_RHGITALY}/${path}
done

DIST_RS_ENRY=${DIST_RHGITALY}/rust/dependencies/rs-enry
DIST_GO_ENRY=${DIST_RS_ENRY}/go-enry
DEPS_RS_ENRY=${DEPS_DIR}/rs-enry
DEPS_GO_ENRY=${DEPS_RS_ENRY}/go-enry
echo "Extracting rs-enry to ${DIST_RS_ENRY}"
mkdir ${DIST_RS_ENRY}
git -C ${DEPS_RS_ENRY} log -n1 --oneline > ${DIST_RS_ENRY}/.git-revision
git -C ${DEPS_RS_ENRY} archive HEAD | tar -C ${DIST_RS_ENRY} -x
git -C ${DEPS_GO_ENRY} log -n1 --oneline > ${DIST_GO_ENRY}/.git-revision
git -C ${DEPS_GO_ENRY} archive HEAD | tar -C ${DIST_GO_ENRY} -x

DIST_SPDX_DATA=${DIST_RHGITALY}/rust/dependencies/spdx-license-list-data
DEPS_SPDX_DATA=${DEPS_DIR}/spdx-license-list-data
echo "Extracting SPDX data to ${DIST_SPDX_DATA}"
mkdir ${DIST_SPDX_DATA}
git -C ${DEPS_SPDX_DATA} log -n1 --oneline > ${DIST_SPDX_DATA}/.git-revision
git -C ${DEPS_SPDX_DATA} archive HEAD | tar -C ${DIST_SPDX_DATA} -x

echo "Creating tarball"
tar czf ${TARBALL} ${DIST_RHGITALY}

echo "Removing temporary directories ${DIST_HGITALY} and ${DIST_RHGITALY}"
rm -rf ${DIST_HGITALY} ${DIST_RHGITALY}

echo "tarball available in `realpath ${TARBALL}`"
