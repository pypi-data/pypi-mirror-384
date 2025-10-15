# SPDX-License-Identifier: Apache-2.0

CENGINE ?= podman


#
# If you want to see the full commands, run:
#   NOISY_BUILD=y make
#
ifeq ($(NOISY_BUILD),)
    ECHO_PREFIX=@
    CMD_PREFIX=@
    PIPE_DEV_NULL=> /dev/null 2> /dev/null
else
    ECHO_PREFIX=@\#
    CMD_PREFIX=
    PIPE_DEV_NULL=
endif

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: action-lint actionlint
action-lint: actionlint
actionlint: ## Lint GitHub Action workflows
	$(ECHO_PREFIX) printf "  %-12s .github/...\n" "[ACTION LINT]"
	$(CMD_PREFIX) if ! command -v actionlint $(PIPE_DEV_NULL) ; then \
		echo "Please install actionlint." ; \
		echo "go install github.com/rhysd/actionlint/cmd/actionlint@latest" ; \
		exit 1 ; \
	fi
	$(CMD_PREFIX) if ! command -v shellcheck $(PIPE_DEV_NULL) ; then \
		echo "Please install shellcheck." ; \
		echo "https://github.com/koalaman/shellcheck#user-content-installing" ; \
		exit 1 ; \
	fi
	$(CMD_PREFIX) actionlint -color

.PHONY: check-tox
check-tox:
	@command -v tox &> /dev/null || (echo "'tox' is not installed" && exit 1)

.PHONY: md-lint
md-lint: ## Lint markdown files
	$(ECHO_PREFIX) printf "  %-12s ./...\n" "[MD LINT]"
	$(CMD_PREFIX) $(CENGINE) run --rm -v $(CURDIR):/workdir --security-opt label=disable docker.io/davidanson/markdownlint-cli2:latest > /dev/null

.PHONY: toml-lint
toml-lint:  ## Lint pyproject.toml
	$(ECHO_PREFIX) printf "  %-12s ./...\n" "[TOML LINT]"
	$(CMD_PREFIX) $(CENGINE) run --rm -v $(CURDIR):/workdir --security-opt label=disable --platform linux/amd64 docker.io/tamasfe/taplo:0.8.1 lint /workdir/pyproject.toml

.PHONY: toml-fmt
toml-fmt: check-engine ## Format pyproject.toml
	$(ECHO_PREFIX) printf "  %-12s ./...\n" "[TOML FMT]"
	$(CMD_PREFIX) $(CENGINE) run --rm -v $(CURDIR):/workdir --security-opt label=disable --platform linux/amd64 docker.io/tamasfe/taplo:0.8.1 fmt /workdir/pyproject.toml

.PHONY: check-engine
check-engine:
	@command -v $(CENGINE) &> /dev/null || (echo "'$(CENGINE)' container engine is not installed, you can override it with the 'CENGINE' variable" && exit 1)

.PHONY: verify
verify: check-tox ## Run linting, typing, and formatting checks via tox
	tox p -e fastlint,mypy,ruff


# TODO: add unit tests in the future
.PHONY: tests
tests: check-tox ## Run type checks.
	tox -e mypy


.PHONY: fix
fix: check-tox ## Fix everything that's fixable by the automated tooling.
	tox -e fix

