"""Tests for stateful installer."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mcpi.installer.stateful_installer import StatefulInstaller
from mcpi.config.server_state import ServerState
from mcpi.registry.catalog import MCPServer, ServerInstallation, InstallationMethod, ServerConfiguration, ServerVersions
from mcpi.installer.base import InstallationResult


class TestStatefulInstaller:
    """Test cases for StatefulInstaller."""
    
    @pytest.fixture
    def mock_server(self):
        """Create a mock MCP server for testing."""
        return MCPServer(
            id="test-server",
            name="Test Server",
            description="A test MCP server",
            author="Test Author",
            category=["test"],
            license="MIT",
            platforms=["darwin", "linux"],
            installation=ServerInstallation(
                method=InstallationMethod.PIP,
                package="test-server"
            ),
            configuration=ServerConfiguration(
                required_params=[],
                optional_params=[]
            ),
            versions=ServerVersions(
                latest="1.0.0",
                supported=["1.0.0"]
            ),
            capabilities=["test"]
        )
    
    def test_init_claude_code(self):
        """Test initialization for Claude Code client."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller'):
            installer = StatefulInstaller("claude-code")
            assert installer.client == "claude-code"
            assert installer.state_manager.client == "claude-code"
    
    def test_init_unsupported_client(self):
        """Test initialization with unsupported client."""
        with pytest.raises(ValueError, match="Unsupported client"):
            StatefulInstaller("unsupported-client")
    
    def test_add_server_success(self, mock_server):
        """Test successfully adding a server."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Mock installer
                mock_installer = MagicMock()
                mock_installer.install.return_value = InstallationResult(
                    server_id="test-server",
                    success=True,
                    message="Success",
                    details={"server_config": {"command": "python3", "args": ["-m", "test-server"]}}
                )
                mock_installer.uninstall.return_value = InstallationResult(
                    server_id="test-server",
                    success=True,
                    message="Uninstalled"
                )
                mock_installer_class.return_value = mock_installer
                
                # Mock state manager paths
                with patch.object(StatefulInstaller, '__init__') as mock_init:
                    mock_init.return_value = None
                    installer = StatefulInstaller("claude-code")
                    installer.client = "claude-code"
                    installer.dry_run = False
                    installer.installer = mock_installer
                    
                    # Mock state manager
                    mock_state_manager = MagicMock()
                    mock_state_manager.get_server_state.return_value = ServerState.NOT_INSTALLED
                    mock_state_manager.add_server.return_value = True
                    installer.state_manager = mock_state_manager
                    
                    # Add server
                    result = installer.add_server(mock_server)
                    
                    assert result.success
                    assert "test-server" in result.message
                    mock_installer.install.assert_called_once()
                    mock_installer.uninstall.assert_called_once()
                    mock_state_manager.add_server.assert_called_once()
    
    def test_add_server_already_exists(self, mock_server):
        """Test adding a server that already exists."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                mock_state_manager = MagicMock()
                mock_state_manager.get_server_state.return_value = ServerState.ENABLED
                installer.state_manager = mock_state_manager
                
                # Try to add existing server
                result = installer.add_server(mock_server)
                
                assert not result.success
                assert "already added" in result.message
    
    def test_disable_server_success(self):
        """Test successfully disabling a server."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                mock_state_manager = MagicMock()
                mock_state_manager.get_server_state.return_value = ServerState.ENABLED
                mock_state_manager.disable_server.return_value = True
                installer.state_manager = mock_state_manager
                
                # Disable server
                result = installer.disable_server("test-server")
                
                assert result.success
                assert "disabled" in result.message
                mock_state_manager.disable_server.assert_called_once_with("test-server")
    
    def test_disable_server_not_installed(self):
        """Test disabling a server that's not installed."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                mock_state_manager = MagicMock()
                mock_state_manager.get_server_state.return_value = ServerState.NOT_INSTALLED
                installer.state_manager = mock_state_manager
                
                # Try to disable non-installed server
                result = installer.disable_server("test-server")
                
                assert not result.success
                assert "not installed" in result.message
    
    def test_enable_server_success(self):
        """Test successfully enabling a server."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                mock_state_manager = MagicMock()
                mock_state_manager.get_server_state.return_value = ServerState.DISABLED
                mock_state_manager.enable_server.return_value = True
                installer.state_manager = mock_state_manager
                
                # Enable server
                result = installer.enable_server("test-server")
                
                assert result.success
                assert "enabled" in result.message
                mock_state_manager.enable_server.assert_called_once_with("test-server")
    
    def test_enable_server_already_enabled(self):
        """Test enabling a server that's already enabled."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                mock_state_manager = MagicMock()
                mock_state_manager.get_server_state.return_value = ServerState.ENABLED
                installer.state_manager = mock_state_manager
                
                # Try to enable already enabled server
                result = installer.enable_server("test-server")
                
                assert not result.success
                assert "already enabled" in result.message
    
    def test_remove_server_success(self):
        """Test successfully removing a server."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                mock_state_manager = MagicMock()
                mock_state_manager.get_server_state.return_value = ServerState.ENABLED
                mock_state_manager.remove_server.return_value = True
                installer.state_manager = mock_state_manager
                
                # Remove server
                result = installer.remove_server("test-server")
                
                assert result.success
                assert "removed" in result.message
                mock_state_manager.remove_server.assert_called_once_with("test-server")
    
    def test_list_servers(self):
        """Test listing servers."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                mock_servers = {
                    "server1": {"state": ServerState.ENABLED, "config": {"command": "python3"}},
                    "server2": {"state": ServerState.DISABLED, "config": {"command": "node"}}
                }
                mock_state_manager = MagicMock()
                mock_state_manager.get_all_servers.return_value = mock_servers
                installer.state_manager = mock_state_manager
                
                # List servers
                result = installer.list_servers()
                
                assert result == mock_servers
                mock_state_manager.get_all_servers.assert_called_once()
    
    def test_dry_run_mode(self, mock_server):
        """Test operations in dry run mode."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code", dry_run=True)
                installer.client = "claude-code"
                installer.dry_run = True
                installer.installer = mock_installer
                
                # Mock state manager
                mock_state_manager = MagicMock()
                mock_state_manager.get_server_state.return_value = ServerState.ENABLED
                installer.state_manager = mock_state_manager
                
                # Test dry run disable
                result = installer.disable_server("test-server")
                
                assert result.success
                # State manager should not be called in dry run
                mock_state_manager.disable_server.assert_not_called()
    
    def test_get_enabled_servers(self):
        """Test getting enabled servers."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                enabled_servers = {"server1": {"command": "python3"}}
                mock_state_manager = MagicMock()
                mock_state_manager.get_enabled_servers.return_value = enabled_servers
                installer.state_manager = mock_state_manager
                
                # Get enabled servers
                result = installer.get_enabled_servers()
                
                assert result == ["server1"]
                mock_state_manager.get_enabled_servers.assert_called_once()
    
    def test_get_disabled_servers(self):
        """Test getting disabled servers."""
        with patch('mcpi.installer.stateful_installer.ClaudeCodeInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            
            with patch.object(StatefulInstaller, '__init__') as mock_init:
                mock_init.return_value = None
                installer = StatefulInstaller("claude-code")
                installer.client = "claude-code"
                installer.dry_run = False
                installer.installer = mock_installer
                
                # Mock state manager
                disabled_servers = {"server2": {"command": "node"}}
                mock_state_manager = MagicMock()
                mock_state_manager.get_disabled_servers.return_value = disabled_servers
                installer.state_manager = mock_state_manager
                
                # Get disabled servers
                result = installer.get_disabled_servers()
                
                assert result == ["server2"]
                mock_state_manager.get_disabled_servers.assert_called_once()