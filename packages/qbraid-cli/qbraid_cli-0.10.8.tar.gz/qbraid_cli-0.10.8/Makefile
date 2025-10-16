.PHONY: help docs clean build check_dependencies

DOCS_DIR := docs
BUILD_DIR := $(DOCS_DIR)/build
TREE_DIR := $(DOCS_DIR)/tree
DIST_DIR := dist
SRC_DIR := qbraid_cli
TOOLS_DIR := tools
TESTS_DIR := tests

.DEFAULT_GOAL := help

help: ## Display this help message
	@echo "Available commands:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo

docs: check_dependencies_docs check_build_version ## Generate documentation (Sphinx)
	@python -c "import pathlib; pathlib.Path('$(TREE_DIR)').mkdir(parents=True, exist_ok=True)"
	@python -c "import glob, os; [os.remove(f) for f in glob.glob('$(TREE_DIR)/*')]"
	@typer qbraid_cli.main utils docs --name=qbraid --output=$(TREE_DIR)/qbraid.md
	@m2r $(TREE_DIR)/qbraid.md
	@python -c "import os; os.remove('$(TREE_DIR)/qbraid.md')"
	@python $(TOOLS_DIR)/split_rst.py $(TREE_DIR)/qbraid.rst
	@sphinx-build -W -b html $(DOCS_DIR) $(BUILD_DIR)

docs-mdx: check_dependencies_docs check_build_version ## Generate documentation (Mintlify)
	@python -c "import pathlib; pathlib.Path('$(TREE_DIR)').mkdir(parents=True, exist_ok=True)"
	@python -c "import glob, os; [os.remove(f) for f in glob.glob('$(TREE_DIR)/*')]"
	@typer qbraid_cli.main utils docs --name=qbraid --output=$(TREE_DIR)/qbraid.md
	@python $(TOOLS_DIR)/split_md.py $(TREE_DIR)/qbraid.md

test: check_dependencies_test ## Run tests with pytest
	@python -m pytest $(TESTS_DIR)

clean: ## Clean up generated docs and build artifacts
	@python -c "import shutil; shutil.rmtree('$(BUILD_DIR)', ignore_errors=True)"
	@python -c "import shutil; shutil.rmtree('$(TREE_DIR)', ignore_errors=True)"
	@python -c "import shutil; shutil.rmtree('$(DIST_DIR)', ignore_errors=True)"
	@python -c "import os; os.remove('$(SRC_DIR)/_version.py') if os.path.exists('$(SRC_DIR)/_version.py') else None"

build: check_dependencies_build ## Build the package
	@python -m build .

check_build_version:
	@python -c "import os; assert os.path.exists('$(SRC_DIR)/_version.py'), 'Error: $(SRC_DIR)/_version.py does not exist. Please \'make build\' before proceeding.'"

check_dependencies_docs:
	@command -v typer >/dev/null 2>&1 || { echo >&2 "Error: Python 'typer-cli' module is not installed. Please install it to proceed."; exit 1; }
	@command -v m2r >/dev/null 2>&1 || { echo >&2 "Error: Python 'm2r' module is not installed. Please install it to proceed."; exit 1; }
	@command -v sphinx-build >/dev/null 2>&1 || { echo >&2 "Error: Python 'sphinx' module is not installed. Please install it to proceed."; exit 1; }

check_dependencies_test:
	@python -c "import pytest" 2>/dev/null || { echo >&2 "Error: Python 'pytest' module is not installed. Please install it to proceed."; exit 1; }

check_dependencies_build:
	@python -c "import build" 2>/dev/null || { echo >&2 "Error: Python 'build' module is not installed. Please install it to proceed."; exit 1; }
