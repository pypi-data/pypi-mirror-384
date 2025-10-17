ifndef APPPY_DB_MK_INCLUDED
APPPY_DB_MK_INCLUDED := 1
DB_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: db db-dev db/build db/clean db/install db/install-dev

db: db/clean db/install

db-dev: db/clean db/install-dev

db/build:
	cd $(DB_PKG_DIR) && uvx --from build pyproject-build

db/clean:
	cd $(DB_PKG_DIR) && rm -rf dist/ *.egg-info .venv

db/install: db/build
	cd $(DB_PKG_DIR) && uv pip install dist/*.whl

db/install-dev:
	cd $(DB_PKG_DIR) && uv pip install -e .

endif # APPPY_DB_MK_INCLUDED