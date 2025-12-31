"""Functional tests for Smart Server Bundles feature.

This test suite validates the complete bundle functionality end-to-end,
testing real user workflows that cannot be satisfied by stubs or shortcuts.

These tests verify:
1. Bundle catalog loading and querying
2. Bundle data structure validation
3. CLI commands for bundle management
4. Error handling and edge cases

Testing Philosophy:
- Tests execute actual user-facing commands
- Verification checks real file system state
- Multiple verification points per test
"""

import json
from pathlib import Path
from typing import Dict, Any

import pytest
from click.testing import CliRunner

from mcpi.bundles.catalog import BundleCatalog, create_test_bundle_catalog
from mcpi.bundles.installer import BundleInstaller
from mcpi.bundles.models import Bundle, BundleServer
from mcpi.registry.catalog_manager import create_default_catalog_manager


# =============================================================================
# Fixtures - Test Environment Setup
# =============================================================================


@pytest.fixture
def isolated_bundles_dir(tmp_path: Path) -> Path:
    """Create isolated directory for bundle files.

    Returns:
        Path: Temporary bundles directory
    """
    bundles_dir = tmp_path / "bundles"
    bundles_dir.mkdir()
    return bundles_dir


@pytest.fixture
def sample_bundle_json(isolated_bundles_dir: Path) -> Path:
    """Create a sample bundle JSON file.

    Returns:
        Path: Path to the created bundle file
    """
    bundle_data = {
        "name": "test-bundle",
        "description": "Test bundle for integration tests",
        "version": "1.0.0",
        "servers": [
            {
                "id": "filesystem",
                "config": {
                    "env": {"CUSTOM_VAR": "test_value"},
                },
            },
            {
                "id": "github",
                "config": {"env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}},
            },
        ],
    }

    bundle_file = isolated_bundles_dir / "test_bundle.json"
    with open(bundle_file, "w") as f:
        json.dump(bundle_data, f, indent=2)

    return bundle_file


@pytest.fixture
def multi_bundle_dir(isolated_bundles_dir: Path) -> Path:
    """Create directory containing multiple test bundles.

    Returns:
        Path: Directory with multiple bundle JSON files
    """
    bundles = [
        {
            "name": "dev-bundle",
            "description": "Development tools",
            "servers": [{"id": "filesystem", "config": {"env": {"DEV_MODE": "true"}}}],
        },
        {
            "name": "prod-bundle",
            "description": "Production tools",
            "servers": [{"id": "github", "config": {"env": {"PROD": "true"}}}],
        },
    ]

    for bundle_data in bundles:
        bundle_file = isolated_bundles_dir / f"{bundle_data['name']}.json"
        with open(bundle_file, "w") as f:
            json.dump(bundle_data, f, indent=2)

    return isolated_bundles_dir


@pytest.fixture
def real_server_catalog():
    """Create REAL ServerCatalog loaded from actual data/catalog.json.

    CRITICAL: This is NOT a mock. It loads the real catalog.
    This ensures tests fail if implementation uses servers not in catalog.

    Returns:
        ServerCatalog: Real catalog instance
    """
    manager = create_default_catalog_manager()
    return manager.get_catalog("official")


# =============================================================================
# 1. Bundle Catalog Tests - Loading and Querying
# =============================================================================


class TestBundleCatalog:
    """Test BundleCatalog loading and querying functionality.

    These tests verify:
    1. Actual file loading from disk
    2. Parsed data matches file contents
    3. Multiple validation points per bundle
    """

    def test_load_empty_catalog_directory(self, isolated_bundles_dir: Path):
        """Load catalog from directory with no bundles."""
        catalog = BundleCatalog(bundles_dir=isolated_bundles_dir)

        bundles = catalog.list_bundles()

        assert bundles == [], "Empty directory should return empty list"

    def test_load_single_bundle(self, sample_bundle_json: Path):
        """Load catalog with single bundle file."""
        catalog = BundleCatalog(bundles_dir=sample_bundle_json.parent)

        bundles = catalog.list_bundles()

        assert len(bundles) == 1, "Should load exactly one bundle"
        bundle_name, bundle = bundles[0]
        assert bundle_name == "test-bundle"
        assert bundle.name == "test-bundle"
        assert bundle.description == "Test bundle for integration tests"
        assert bundle.version == "1.0.0"
        assert len(bundle.servers) == 2

    def test_bundle_server_details_preserved(self, sample_bundle_json: Path):
        """Verify bundle server details are correctly parsed."""
        catalog = BundleCatalog(bundles_dir=sample_bundle_json.parent)
        bundle = catalog.get_bundle("test-bundle")

        assert bundle is not None

        # Check first server
        server1 = bundle.servers[0]
        assert server1.id == "filesystem"
        assert server1.config is not None
        assert server1.config["env"]["CUSTOM_VAR"] == "test_value"

        # Check second server
        server2 = bundle.servers[1]
        assert server2.id == "github"
        assert server2.config["env"]["GITHUB_TOKEN"] == "${GITHUB_TOKEN}"

    def test_get_bundle_by_name(self, sample_bundle_json: Path):
        """Get specific bundle by name."""
        catalog = BundleCatalog(bundles_dir=sample_bundle_json.parent)

        bundle = catalog.get_bundle("test-bundle")

        assert bundle is not None
        assert bundle.name == "test-bundle"

    def test_get_nonexistent_bundle(self, sample_bundle_json: Path):
        """Attempt to get bundle that doesn't exist."""
        catalog = BundleCatalog(bundles_dir=sample_bundle_json.parent)

        bundle = catalog.get_bundle("nonexistent-bundle")

        assert bundle is None, "Should return None for missing bundle"

    def test_load_multiple_bundles(self, multi_bundle_dir: Path):
        """Load catalog with multiple bundle files."""
        catalog = BundleCatalog(bundles_dir=multi_bundle_dir)

        bundles = catalog.list_bundles()

        assert len(bundles) == 2, "Should load both bundles"
        bundle_names = {name for name, _ in bundles}
        assert bundle_names == {"dev-bundle", "prod-bundle"}


# =============================================================================
# 2. Bundle CLI Tests
# =============================================================================


class TestBundleCLI:
    """Test bundle CLI commands.

    These tests use the CLI runner to test actual command output.
    """

    def test_bundle_list_command(self, multi_bundle_dir: Path, monkeypatch):
        """Test 'mcpi bundle list' command."""
        from mcpi.cli import main

        # Patch the bundle catalog factory
        def mock_create_bundle_catalog():
            return create_test_bundle_catalog(multi_bundle_dir)

        monkeypatch.setattr(
            "mcpi.cli.create_default_bundle_catalog", mock_create_bundle_catalog
        )

        runner = CliRunner()
        result = runner.invoke(main, ["bundle", "list"])

        assert result.exit_code == 0
        assert "dev-bundle" in result.output
        assert "prod-bundle" in result.output

    def test_bundle_info_command(self, sample_bundle_json: Path, monkeypatch):
        """Test 'mcpi bundle info <bundle_id>' command."""
        from mcpi.cli import main

        # Patch the bundle catalog factory
        def mock_create_bundle_catalog():
            return create_test_bundle_catalog(sample_bundle_json.parent)

        monkeypatch.setattr(
            "mcpi.cli.create_default_bundle_catalog", mock_create_bundle_catalog
        )

        runner = CliRunner()
        result = runner.invoke(main, ["bundle", "info", "test-bundle"])

        assert result.exit_code == 0
        assert "test-bundle" in result.output
        assert "Test bundle for integration tests" in result.output

    def test_bundle_info_not_found(self, sample_bundle_json: Path, monkeypatch):
        """Test 'mcpi bundle info' with non-existent bundle."""
        from mcpi.cli import main

        # Patch the bundle catalog factory
        def mock_create_bundle_catalog():
            return create_test_bundle_catalog(sample_bundle_json.parent)

        monkeypatch.setattr(
            "mcpi.cli.create_default_bundle_catalog", mock_create_bundle_catalog
        )

        runner = CliRunner()
        result = runner.invoke(main, ["bundle", "info", "nonexistent"])

        assert "not found" in result.output.lower()


# =============================================================================
# 3. Bundle Model Tests
# =============================================================================


class TestBundleModels:
    """Test bundle Pydantic models."""

    def test_bundle_server_model(self):
        """Test BundleServer model."""
        server = BundleServer(id="test-server", config={"env": {"KEY": "value"}})

        assert server.id == "test-server"
        assert server.config == {"env": {"KEY": "value"}}

    def test_bundle_server_without_config(self):
        """Test BundleServer model without config."""
        server = BundleServer(id="test-server")

        assert server.id == "test-server"
        assert server.config is None

    def test_bundle_model(self):
        """Test Bundle model."""
        bundle = Bundle(
            name="test-bundle",
            description="A test bundle",
            version="2.0.0",
            author="Test Author",
            servers=[BundleServer(id="test-server")],
            suggested_scope="project-mcp",
        )

        assert bundle.name == "test-bundle"
        assert bundle.description == "A test bundle"
        assert bundle.version == "2.0.0"
        assert bundle.author == "Test Author"
        assert len(bundle.servers) == 1
        assert bundle.suggested_scope == "project-mcp"

    def test_bundle_model_defaults(self):
        """Test Bundle model with default values."""
        bundle = Bundle(
            name="test-bundle",
            description="A test bundle",
            servers=[BundleServer(id="test-server")],
        )

        assert bundle.version == "1.0.0"  # default
        assert bundle.author is None  # default
        assert bundle.suggested_scope == "user-global"  # default


# =============================================================================
# 4. Bundle Error Handling Tests
# =============================================================================


class TestBundleErrorHandling:
    """Test error handling in bundle operations."""

    def test_invalid_json_file_skipped(self, isolated_bundles_dir: Path):
        """Test that invalid JSON files are skipped gracefully."""
        # Create invalid JSON file
        invalid_file = isolated_bundles_dir / "invalid.json"
        invalid_file.write_text("{ not valid json }")

        # Create valid bundle file
        valid_bundle = {
            "name": "valid-bundle",
            "description": "Valid bundle",
            "servers": [{"id": "test"}],
        }
        valid_file = isolated_bundles_dir / "valid.json"
        with open(valid_file, "w") as f:
            json.dump(valid_bundle, f)

        catalog = BundleCatalog(bundles_dir=isolated_bundles_dir)
        bundles = catalog.list_bundles()

        # Should load valid bundle and skip invalid
        assert len(bundles) == 1
        assert bundles[0][0] == "valid-bundle"

    def test_missing_required_fields_skipped(self, isolated_bundles_dir: Path):
        """Test that bundles missing required fields are skipped."""
        # Create bundle missing 'servers' field
        invalid_bundle = {
            "name": "invalid-bundle",
            "description": "Missing servers",
            # No 'servers' field
        }
        invalid_file = isolated_bundles_dir / "invalid.json"
        with open(invalid_file, "w") as f:
            json.dump(invalid_bundle, f)

        catalog = BundleCatalog(bundles_dir=isolated_bundles_dir)
        bundles = catalog.list_bundles()

        # Invalid bundle should be skipped
        assert len(bundles) == 0

    def test_nonexistent_directory_handled(self, tmp_path: Path):
        """Test handling of nonexistent bundles directory."""
        nonexistent = tmp_path / "does_not_exist"

        catalog = BundleCatalog(bundles_dir=nonexistent)
        bundles = catalog.list_bundles()

        # Should return empty list, not error
        assert bundles == []


# =============================================================================
# 5. Factory Function Tests
# =============================================================================


class TestBundleFactories:
    """Test bundle factory functions."""

    def test_create_test_bundle_catalog(self, sample_bundle_json: Path):
        """Test create_test_bundle_catalog factory."""
        catalog = create_test_bundle_catalog(sample_bundle_json.parent)

        bundles = catalog.list_bundles()
        assert len(bundles) == 1
        assert bundles[0][0] == "test-bundle"
