# MCPI Development Tasks

# Default recipe: show available commands
default:
    @just --list

# Run all tests
test *args:
    uv run pytest {{ args }}

# Run tests with coverage
test-cov:
    uv run pytest --cov=src/mcpi --cov-report=term-missing

# Format code
fmt:
    uv run black src/ tests/
    uv run ruff check src/ tests/ --fix

# Check code quality without fixing
check:
    uv run black --check src/ tests/
    uv run ruff check src/ tests/
    uv run mypy src/

# Run the CLI
run *args:
    uv run mcpi {{ args }}

# Build the package
build:
    rm -rf dist/
    uv run python -m build

# Publish the latest tag as a GitHub release (triggers PyPI publish via CI)
publish:
    #!/usr/bin/env bash
    set -euo pipefail

    # Get the latest tag
    latest_tag=$(git describe --tags --abbrev=0)

    if [[ -z "$latest_tag" ]]; then
        echo "Error: No tags found"
        exit 1
    fi

    echo "Latest tag: $latest_tag"

    # Check if release already exists
    if gh release view "$latest_tag" &>/dev/null; then
        echo "Release $latest_tag already exists"
        echo "View at: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/releases/tag/$latest_tag"
        exit 0
    fi

    # Generate release notes from tag annotation or commits
    echo "Creating GitHub release for $latest_tag..."

    # Get the previous tag for changelog
    previous_tag=$(git describe --tags --abbrev=0 "$latest_tag^" 2>/dev/null || echo "")

    if [[ -n "$previous_tag" ]]; then
        echo "Generating changelog from $previous_tag to $latest_tag"
        gh release create "$latest_tag" \
            --title "$latest_tag" \
            --generate-notes \
            --notes-start-tag "$previous_tag"
    else
        echo "No previous tag found, creating release with tag annotation"
        gh release create "$latest_tag" \
            --title "$latest_tag" \
            --generate-notes
    fi

    echo ""
    echo "Release created! PyPI publish will be triggered by CI."
    echo "View at: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/releases/tag/$latest_tag"

# Publish to TestPyPI (via workflow dispatch)
publish-test:
    gh workflow run publish.yml -f target=testpypi
    echo "TestPyPI publish workflow triggered. Check Actions tab for progress."

# Create a new version tag
tag version:
    #!/usr/bin/env bash
    set -euo pipefail

    if [[ ! "{{ version }}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Error: Version must be in format X.Y.Z (e.g., 1.2.3)"
        exit 1
    fi

    # Update pyproject.toml
    sed -i '' 's/^version = ".*"/version = "{{ version }}"/' pyproject.toml

    git add pyproject.toml
    git commit -m "chore: Bump version to {{ version }}"
    git tag -a "v{{ version }}" -m "v{{ version }}"

    echo "Created tag v{{ version }}"
    echo "Run 'git push origin master && git push origin v{{ version }}' to push"
    echo "Then run 'just publish' to create the GitHub release"

# Show current version info
version:
    @echo "Package version: $(grep '^version' pyproject.toml | cut -d'"' -f2)"
    @echo "Latest tag: $(git describe --tags --abbrev=0 2>/dev/null || echo 'none')"
    @echo "Commits since tag: $(git rev-list $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD)..HEAD --count 2>/dev/null || echo 'N/A')"

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info src/*.egg-info .pytest_cache .mypy_cache .ruff_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Install in development mode
dev:
    uv sync --dev
