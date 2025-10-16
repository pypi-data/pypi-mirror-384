# Makefile for easy development workflows.
# See devtools/development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

.PHONY: default install lint test upgrade build clean agent-rules

default: agent-rules install lint test docs-check

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

agent-rules: CLAUDE.md AGENTS.md .copilot-instructions.md

# Use .cursor/rules for sources of rules.
# Create Claude, Codex, and GitHub Copilot rules from these.
CLAUDE.md: .cursor/rules/general.mdc .cursor/rules/python.mdc
	cat .cursor/rules/general.mdc .cursor/rules/python.mdc > CLAUDE.md

AGENTS.md: .cursor/rules/general.mdc .cursor/rules/python.mdc
	cat .cursor/rules/general.mdc .cursor/rules/python.mdc > AGENTS.md

.copilot-instructions.md: .cursor/rules/general.mdc .cursor/rules/python.mdc
	cat .cursor/rules/general.mdc .cursor/rules/python.mdc > .copilot-instructions.md

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .mypy_cache/
	-rm -rf .ruff_cache/
	-rm -rf .venv/
	-rm -rf docs/build/
	-rm -rf CLAUDE.md AGENTS.md .copilot-instructions.md
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
