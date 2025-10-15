#!/bin/sh

set -e

if [ -z "$1" ]; then
    echo "usage: $0 HGITALY_VERSION";
    exit 1
fi

HGITALY_VERSION=$1

set -u

cd `dirname $0`/../dist


DIST_PWD=${PWD}

echo "Performing extraction in ${DIST_PWD}"
tar xzf rhgitaly-${HGITALY_VERSION}.tgz
cd rhgitaly-${HGITALY_VERSION}/rust

BIN_PATH=`realpath ${DIST_PWD}/rhgitaly-${HGITALY_VERSION}_linux_amd64`
echo "Compiling and moving resulting binary to ${BIN_PATH}"
cargo build --locked --release
mv target/release/rhgitaly ${BIN_PATH}

echo "Cleaning up build directory"
cd ../..
rm -rf rhgitaly-${HGITALY_VERSION}
