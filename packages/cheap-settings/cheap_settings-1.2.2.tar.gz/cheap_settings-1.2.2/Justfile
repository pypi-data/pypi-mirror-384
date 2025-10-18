#!/usr/bin/env just  --justfile

default:

# Run tests
test:
    uv run pytest tests/ -v

# Quick test run
test-quick:
    uv run pytest tests/ -q

# Format code
format:
    uv run ruff format .
    uv run isort .

# Lint code
lint:
    uv run ruff check .

# Run all checks (tests + lint)
check: lint test

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Deploy documentation to GitHub Pages
deploy-docs:
    uv run mkdocs gh-deploy

# Serve documentation locally
serve-docs:
    uv run mkdocs serve --dev-addr=127.0.0.1:8001

# Build the package
build:
    uv build

# Publish to PyPI (without building)
publish-only:
    uvx uv-publish

# Build and publish to PyPI
publish: build publish-only

# Pre-release checklist
release-prep: check clean build
    @echo "✓ Tests passing"
    @echo "✓ Code formatted and linted"
    @echo "✓ Build artifacts cleaned"
    @echo "✓ Package built"
    @echo ""
    @echo "Don't forget to:"
    @echo "• Deploy docs: just deploy-docs"
    @echo "• Then publish: just publish"

bump *ARGS:
    uvx bump-my-version {{ARGS}}
bump-bump *ARGS:
    uvx bump-my-version bump --allow-dirty {{ARGS}}
