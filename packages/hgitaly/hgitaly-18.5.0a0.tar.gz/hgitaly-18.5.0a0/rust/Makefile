all: help

HGITALY_VERSION := $(shell cat ../hgitaly/VERSION)
MERCURIAL_SOURCE_REPO = dependencies/mercurial
MERCURIAL_SOURCE_REV := $(shell cat mercurial.rev)
MERCURIAL_SOURCE_REMOTE ?= https://foss.heptapod.net/mercurial/mercurial-devel
RS_ENRY_SOURCE_REPO = dependencies/rs-enry
RS_ENRY_SOURCE_REV = $(shell cat rs-enry.rev)
RS_ENRY_SOURCE_REMOTE ?= https://github.com/go-enry/rs-enry
GO_ENRY_SOURCE_REPO = dependencies/rs-enry/go-enry
GO_ENRY_SOURCE_REV = $(shell cat go-enry.rev)
GO_ENRY_SOURCE_REMOTE ?= https://github.com/go-enry/go-enry
SPDX_DATA_SOURCE_REPO = dependencies/spdx-license-list-data
SPDX_DATA_SOURCE_REV = $(shell cat spdx-data.rev)
SPDX_DATA_SOURCE_REMOTE ?= https://github.com/spdx/license-list-data

.PHONY: help
help:
	@echo "Makefile for RHGitaly development setup and packaging"
	@echo ""
	@echo "Available commands: "
	@echo "  make dev-dependencies:  prepare development dependencies"
	@echo "                          (hg-core, various resources)"
	@echo "  make src-tarball:       package the workspace as a tarball,"
	@echo "                          including all dependencies that "
	@echo "                          cannot be obtained from crates.io"
	@echo "  make ci-cd-src-tarball: make src-tarball and upload it"
	@echo
	@echo "Interesting variables: "
	@echo "  MERCURIAL_SHARE_FROM: if set, Mercurial sources repository"
	@echo "                        will be created (if needed) with"
	@echo "                        'hg share' from this given path."
	@echo "  MERCURIAL_SHARE_POOL: if set, Mercurial sources repository"
	@echo "                        will be cloned using the given path"
	@echo "                        as a share pool."

.PHONY: dev-dependencies
dev-dependencies: dependencies/mercurial/.hg dependencies/rs-enry/.git dependencies/rs-enry/go-enry/.git dependencies/spdx-license-list-data/.git
	hg -R $(MERCURIAL_SOURCE_REPO) pull -r $(MERCURIAL_SOURCE_REV) $(MERCURIAL_SOURCE_REMOTE)
	hg -R $(MERCURIAL_SOURCE_REPO) update --config commands.update.check=abort $(MERCURIAL_SOURCE_REV) --clean
	(cd $(MERCURIAL_SOURCE_REPO) && patch -p1 < ../mercurial.patch)
	git -C $(RS_ENRY_SOURCE_REPO) fetch --all
	git -C $(RS_ENRY_SOURCE_REPO) checkout $(RS_ENRY_SOURCE_REV)
	git -C $(GO_ENRY_SOURCE_REPO) fetch --all
	git -C $(GO_ENRY_SOURCE_REPO) checkout $(GO_ENRY_SOURCE_REV)
	git -C $(SPDX_DATA_SOURCE_REPO) fetch --all
	git -C $(SPDX_DATA_SOURCE_REPO) checkout $(SPDX_DATA_SOURCE_REV)

dependencies/mercurial/.hg:
ifdef MERCURIAL_SHARE_FROM
	hg share --noupdate $(MERCURIAL_SHARE_FROM) $(MERCURIAL_SOURCE_REPO)
else ifdef MERCURIAL_SHARE_POOL
	hg --config extensions.share= --config share.pool=${MERCURIAL_SHARE_POOL} clone --noupdate $(MERCURIAL_SOURCE_REMOTE) $(MERCURIAL_SOURCE_REPO)
else
	hg clone --noupdate $(MERCURIAL_SOURCE_REMOTE) $(MERCURIAL_SOURCE_REPO)
endif

dependencies/rs-enry/.git:
	git clone $(RS_ENRY_SOURCE_REMOTE) $(RS_ENRY_SOURCE_REPO)

dependencies/rs-enry/go-enry/.git: dependencies/rs-enry/.git
	git clone $(GO_ENRY_SOURCE_REMOTE) $(GO_ENRY_SOURCE_REPO)

dependencies/spdx-license-list-data/.git:
	git clone $(SPDX_DATA_SOURCE_REMOTE) $(SPDX_DATA_SOURCE_REPO)

.PHONY: src-tarball
src-tarball: dev-dependencies
	./src-tarball.sh ${HGITALY_VERSION}

.PHONY: tarball-compile
tarball-compile: src-tarball
	./build-from-tarball.sh ${HGITALY_VERSION}

.PHONY: ci-cd-upload
ci-cd-upload: tarball-compile
	../ci/upload-rhgitaly ${HGITALY_VERSION}
