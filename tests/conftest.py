"""Test configuration and common utilities."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

try:
    from mcpi.config.manager import ConfigManager, MCPIConfig, ProfileConfig
except ImportError:
    # These may not exist in the new structure
    ConfigManager = ProfileConfig = MCPIConfig = None

from mcpi.registry.catalog import MCPServer

# Import test harness fixtures - pytest uses these via dependency injection
# noqa comments prevent Black from removing these "unused" imports
from tests.test_harness import (  # noqa: F401
    MCPTestHarness,
    mcp_harness,
    mcp_manager_with_harness,
    mcp_test_dir,
    prepopulated_harness,
)

# =============================================================================
# CRITICAL SAFETY: Prevent tests from modifying real user files
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def protect_real_user_files():
    """Prevent tests from EVER touching real user configuration files.

    This fixture runs automatically for ALL tests and blocks access to:
    - ~/.claude/* (user-level Claude settings)
    - ~/.mcp.json (legacy MCP config)
    - ./.mcp.json in real project directories
    - ./.claude/* in real project directories

    Tests MUST use temporary directories and path_overrides for isolation.

    If this fixture fails your test, your test is UNSAFE and must be fixed
    to use proper isolation via the test harness fixtures.
    """
    home_dir = Path.home()
    protected_paths = [
        home_dir / ".claude",
        home_dir / ".mcp.json",
        home_dir / ".claude.json",
    ]

    # Set environment variable to signal we're in test mode
    original_env = os.environ.get("MCPI_TEST_MODE")
    os.environ["MCPI_TEST_MODE"] = "1"

    def check_path_safety(path: Path) -> None:
        """Check if a path is safe to write to during tests."""
        path = Path(path).resolve()

        # Allow writes to temp directories
        temp_prefixes = [
            Path("/tmp"),
            Path("/var/folders"),  # macOS temp
            Path(os.environ.get("TMPDIR", "/tmp")).resolve(),
        ]

        for temp_prefix in temp_prefixes:
            try:
                path.relative_to(temp_prefix)
                return  # Safe - it's in a temp directory
            except ValueError:
                continue

        # Block writes to protected user directories
        for protected in protected_paths:
            if path == protected or protected in path.parents:
                raise RuntimeError(
                    f"SAFETY VIOLATION: Test attempted to access protected path: {path}\n"
                    f"Protected location: {protected}\n"
                    f"Tests MUST use temporary directories and path_overrides.\n"
                    f"Use mcp_harness or mcp_manager_with_harness fixtures for isolation."
                )

        # Block writes to real .mcp.json or .claude directories in project
        if path.name in [
            ".mcp.json",
            ".claude",
            "settings.json",
            "settings.local.json",
        ]:
            # Check if it's NOT in a temp directory
            path_str = str(path)
            if "/tmp" not in path_str and "/var/folders" not in path_str:
                raise RuntimeError(
                    f"SAFETY VIOLATION: Test attempted to write to real config file: {path}\n"
                    f"Tests MUST use temporary directories.\n"
                    f"Use mcp_harness or mcp_manager_with_harness fixtures for isolation."
                )

    # Patch Path.write_text, Path.write_bytes, and open() to check safety
    original_write_text = Path.write_text
    original_write_bytes = Path.write_bytes
    original_open = open

    def safe_write_text(self, *args, **kwargs):
        check_path_safety(self)
        return original_write_text(self, *args, **kwargs)

    def safe_write_bytes(self, *args, **kwargs):
        check_path_safety(self)
        return original_write_bytes(self, *args, **kwargs)

    def safe_open(file, mode="r", *args, **kwargs):
        if "w" in mode or "a" in mode or "+" in mode:
            check_path_safety(Path(file))
        return original_open(file, mode, *args, **kwargs)

    # Apply patches
    Path.write_text = safe_write_text
    Path.write_bytes = safe_write_bytes
    builtins_open = (
        __builtins__["open"] if isinstance(__builtins__, dict) else __builtins__.open
    )

    with patch("builtins.open", side_effect=safe_open):
        try:
            yield
        finally:
            # Restore original functions
            Path.write_text = original_write_text
            Path.write_bytes = original_write_bytes
            if original_env is not None:
                os.environ["MCPI_TEST_MODE"] = original_env
            else:
                os.environ.pop("MCPI_TEST_MODE", None)


# =============================================================================


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager with common setup."""
    return Mock(spec=ConfigManager)


@pytest.fixture
def mock_profile_config():
    """Create a mock ProfileConfig with common attributes."""
    profile = Mock(spec=ProfileConfig)
    profile.target = "claude-code"
    profile.config_path = "/test/config"
    profile.install_global = True
    profile.use_uv = True
    profile.python_path = None
    return profile


@pytest.fixture
def mock_mcpi_config():
    """Create a mock MCPIConfig with common setup."""
    config = Mock(spec=MCPIConfig)
    config.general = Mock()
    config.general.default_profile = "default"
    config.profiles = {}
    return config


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCPServer with common setup."""
    server = Mock(spec=MCPServer)

    # New structure fields
    server.id = "test-server"
    server.name = "Test Server"
    server.description = "Test description"
    server.command = "npx"
    server.package = "test-package"
    server.args = []
    server.env = {}
    server.install_method = "npx"
    server.required_config = []
    server.optional_config = {}

    return server


def create_mock_profile(**overrides):
    """Create a mock profile with default values and optional overrides."""
    defaults = {
        "target": "claude-code",
        "config_path": "/test/config",
        "install_global": True,
        "use_uv": True,
        "python_path": None,
    }
    defaults.update(overrides)

    profile = Mock()
    for key, value in defaults.items():
        setattr(profile, key, value)

    return profile


def create_mock_server(
    method="npx", package="test-package", required_config=None, optional_config=None
):
    """Create a mock MCP server with specified configuration."""
    server = Mock()

    # New structure
    server.id = "test-server"
    server.name = "Test Server"
    server.description = "Test description"
    server.command = "npx" if method == "npx" else "python"
    server.package = package
    server.args = []
    server.env = {}
    server.install_method = method
    server.required_config = required_config or []
    server.optional_config = optional_config or {}

    return server
