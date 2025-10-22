"""Test configuration and common utilities."""

import pytest
from pathlib import Path
from unittest.mock import Mock
try:
    from mcpi.config.manager import ConfigManager, ProfileConfig, MCPIConfig
except ImportError:
    # These may not exist in the new structure
    ConfigManager = ProfileConfig = MCPIConfig = None

from mcpi.registry.catalog import MCPServer


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
        "python_path": None
    }
    defaults.update(overrides)
    
    profile = Mock()
    for key, value in defaults.items():
        setattr(profile, key, value)
    
    return profile


def create_mock_server(method="npx", package="test-package", required_config=None, optional_config=None):
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