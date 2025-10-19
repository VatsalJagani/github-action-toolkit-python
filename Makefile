# Makefile for easy development workflows.
# See devtools/development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

.PHONY: default install lint test upgrade build clean

default: install lint test docs-check

install:
	uv sync --all-extras

lint:
	uv run python devtools/lint.py

test:
	uv run pytest

upgrade:
	uv sync --upgrade --all-extras --dev

build:
	uv build

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .mypy_cache/
	-rm -rf .ruff_cache/
	-rm -rf .venv/
	-rm -rf docs/build/
	-find . -type d -name "__pycache__" -exec rm -rf {} +


.PHONY : docs-live
docs-live :
	rm -rf docs/build/
	sphinx-autobuild -b html --watch github_action_toolkit/ docs/source/ docs/build/

.PHONY : docs-check
docs-check:
	rm -rf docs/build/
	uv sync --all-extras
	$(MAKE) -C docs html


.PHONY : create-release
create-release:
	./devtools/release.sh
