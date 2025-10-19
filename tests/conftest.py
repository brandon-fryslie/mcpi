"""Test configuration and common utilities."""

import pytest
from pathlib import Path
from unittest.mock import Mock
from mcpi.config.manager import ConfigManager, ProfileConfig, MCPIConfig
from mcpi.registry.catalog import MCPServer, ServerInstallation, ServerConfiguration


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
    
    # Mock installation info
    installation = Mock(spec=ServerInstallation)
    installation.method = "npm"
    installation.package = "test-package"
    server.installation = installation
    
    # Mock configuration info
    configuration = Mock(spec=ServerConfiguration)
    configuration.required_params = []
    configuration.optional_params = []
    configuration.template = None
    server.configuration = configuration
    
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


def create_mock_server(method="npm", package="test-package", required_params=None, optional_params=None, template=None):
    """Create a mock MCP server with specified configuration."""
    server = Mock()
    
    # Installation info
    installation = Mock()
    installation.method = method
    installation.package = package
    server.installation = installation
    
    # Configuration info
    configuration = Mock()
    configuration.required_params = required_params or []
    configuration.optional_params = optional_params or []
    configuration.template = template
    server.configuration = configuration
    
    return server