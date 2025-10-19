"""Tests for server state management."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mcpi.config.server_state import ServerStateManager, ServerState


class TestServerStateManager:
    """Test cases for ServerStateManager."""
    
    def test_init_claude_code_client(self):
        """Test initialization for claude-code client."""
        manager = ServerStateManager("claude-code")
        assert manager.client == "claude-code"
        assert "claude" in str(manager.enabled_config_path)
        assert "mcpi-disabled-servers.json" in str(manager.disabled_config_path)
    
    def test_init_generic_client(self):
        """Test initialization for generic client."""
        manager = ServerStateManager("generic")
        assert manager.client == "generic"
        assert "generic" in str(manager.enabled_config_path)
        assert "generic" in str(manager.disabled_config_path)
    
    def test_empty_state_initial(self):
        """Test initial state when no configs exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                mock_enabled.return_value = Path(temp_dir) / "enabled.json"
                mock_disabled.return_value = Path(temp_dir) / "disabled.json"
                
                manager = ServerStateManager("claude-code")
                
                # Should return NOT_INSTALLED for any server
                assert manager.get_server_state("test-server") == ServerState.NOT_INSTALLED
                assert manager.get_enabled_servers() == {}
                assert manager.get_disabled_servers() == {}
                assert manager.get_all_servers() == {}
    
    def test_add_server(self):
        """Test adding a server (enabled by default)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                enabled_path = Path(temp_dir) / "enabled.json"
                disabled_path = Path(temp_dir) / "disabled.json"
                mock_enabled.return_value = enabled_path
                mock_disabled.return_value = disabled_path
                
                manager = ServerStateManager("claude-code")
                
                server_config = {
                    "command": "python3",
                    "args": ["-m", "test_server"]
                }
                
                # Add server
                success = manager.add_server("test-server", server_config)
                assert success
                
                # Check state
                assert manager.get_server_state("test-server") == ServerState.ENABLED
                enabled_servers = manager.get_enabled_servers()
                assert "test-server" in enabled_servers
                assert enabled_servers["test-server"] == server_config
                
                # Check file was created
                assert enabled_path.exists()
                with open(enabled_path) as f:
                    data = json.load(f)
                    assert data["mcpServers"]["test-server"] == server_config
    
    def test_disable_server(self):
        """Test disabling an enabled server."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                enabled_path = Path(temp_dir) / "enabled.json"
                disabled_path = Path(temp_dir) / "disabled.json"
                mock_enabled.return_value = enabled_path
                mock_disabled.return_value = disabled_path
                
                manager = ServerStateManager("claude-code")
                
                server_config = {
                    "command": "python3",
                    "args": ["-m", "test_server"]
                }
                
                # Add server first
                manager.add_server("test-server", server_config)
                
                # Disable server
                success = manager.disable_server("test-server")
                assert success
                
                # Check state
                assert manager.get_server_state("test-server") == ServerState.DISABLED
                assert manager.get_enabled_servers() == {}
                
                disabled_servers = manager.get_disabled_servers()
                assert "test-server" in disabled_servers
                assert disabled_servers["test-server"] == server_config
                
                # Check files
                with open(enabled_path) as f:
                    enabled_data = json.load(f)
                    assert "test-server" not in enabled_data["mcpServers"]
                
                with open(disabled_path) as f:
                    disabled_data = json.load(f)
                    assert disabled_data["mcpServers"]["test-server"] == server_config
    
    def test_enable_server(self):
        """Test enabling a disabled server."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                enabled_path = Path(temp_dir) / "enabled.json"
                disabled_path = Path(temp_dir) / "disabled.json"
                mock_enabled.return_value = enabled_path
                mock_disabled.return_value = disabled_path
                
                manager = ServerStateManager("claude-code")
                
                server_config = {
                    "command": "python3",
                    "args": ["-m", "test_server"]
                }
                
                # Add and disable server first
                manager.add_server("test-server", server_config)
                manager.disable_server("test-server")
                
                # Enable server
                success = manager.enable_server("test-server")
                assert success
                
                # Check state
                assert manager.get_server_state("test-server") == ServerState.ENABLED
                assert manager.get_disabled_servers() == {}
                
                enabled_servers = manager.get_enabled_servers()
                assert "test-server" in enabled_servers
                assert enabled_servers["test-server"] == server_config
    
    def test_remove_server(self):
        """Test completely removing a server."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                enabled_path = Path(temp_dir) / "enabled.json"
                disabled_path = Path(temp_dir) / "disabled.json"
                mock_enabled.return_value = enabled_path
                mock_disabled.return_value = disabled_path
                
                manager = ServerStateManager("claude-code")
                
                server_config = {
                    "command": "python3",
                    "args": ["-m", "test_server"]
                }
                
                # Add server
                manager.add_server("test-server", server_config)
                
                # Remove server
                success = manager.remove_server("test-server")
                assert success
                
                # Check state
                assert manager.get_server_state("test-server") == ServerState.NOT_INSTALLED
                assert manager.get_enabled_servers() == {}
                assert manager.get_disabled_servers() == {}
    
    def test_remove_disabled_server(self):
        """Test removing a disabled server."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                enabled_path = Path(temp_dir) / "enabled.json"
                disabled_path = Path(temp_dir) / "disabled.json"
                mock_enabled.return_value = enabled_path
                mock_disabled.return_value = disabled_path
                
                manager = ServerStateManager("claude-code")
                
                server_config = {
                    "command": "python3",
                    "args": ["-m", "test_server"]
                }
                
                # Add and disable server
                manager.add_server("test-server", server_config)
                manager.disable_server("test-server")
                
                # Remove server
                success = manager.remove_server("test-server")
                assert success
                
                # Check state
                assert manager.get_server_state("test-server") == ServerState.NOT_INSTALLED
                assert manager.get_disabled_servers() == {}
    
    def test_get_all_servers(self):
        """Test getting all servers with their states."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                enabled_path = Path(temp_dir) / "enabled.json"
                disabled_path = Path(temp_dir) / "disabled.json"
                mock_enabled.return_value = enabled_path
                mock_disabled.return_value = disabled_path
                
                manager = ServerStateManager("claude-code")
                
                # Add enabled server
                enabled_config = {"command": "python3", "args": ["-m", "enabled_server"]}
                manager.add_server("enabled-server", enabled_config)
                
                # Add disabled server
                disabled_config = {"command": "node", "args": ["disabled_server"]}
                manager.add_server("disabled-server", disabled_config)
                manager.disable_server("disabled-server")
                
                # Get all servers
                all_servers = manager.get_all_servers()
                
                assert len(all_servers) == 2
                assert all_servers["enabled-server"]["state"] == ServerState.ENABLED
                assert all_servers["enabled-server"]["config"] == enabled_config
                assert all_servers["disabled-server"]["state"] == ServerState.DISABLED
                assert all_servers["disabled-server"]["config"] == disabled_config
    
    def test_update_server_config(self):
        """Test updating server configuration while preserving state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                enabled_path = Path(temp_dir) / "enabled.json"
                disabled_path = Path(temp_dir) / "disabled.json"
                mock_enabled.return_value = enabled_path
                mock_disabled.return_value = disabled_path
                
                manager = ServerStateManager("claude-code")
                
                # Add server
                original_config = {"command": "python3", "args": ["-m", "test_server"]}
                manager.add_server("test-server", original_config)
                
                # Update config
                new_config = {"command": "node", "args": ["test_server", "--verbose"]}
                success = manager.update_server_config("test-server", new_config)
                assert success
                
                # Check config was updated and state preserved
                assert manager.get_server_state("test-server") == ServerState.ENABLED
                assert manager.get_server_config("test-server") == new_config
    
    def test_error_handling_invalid_json(self):
        """Test error handling for invalid JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                enabled_path = Path(temp_dir) / "enabled.json"
                disabled_path = Path(temp_dir) / "disabled.json"
                mock_enabled.return_value = enabled_path
                mock_disabled.return_value = disabled_path
                
                # Create invalid JSON file
                enabled_path.parent.mkdir(parents=True, exist_ok=True)
                with open(enabled_path, 'w') as f:
                    f.write("invalid json content")
                
                manager = ServerStateManager("claude-code")
                
                # Should handle invalid JSON gracefully
                assert manager.get_server_state("test-server") == ServerState.NOT_INSTALLED
                assert manager.get_enabled_servers() == {}
    
    def test_disable_nonexistent_server(self):
        """Test disabling a server that doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                mock_enabled.return_value = Path(temp_dir) / "enabled.json"
                mock_disabled.return_value = Path(temp_dir) / "disabled.json"
                
                manager = ServerStateManager("claude-code")
                
                # Should return False for nonexistent server
                success = manager.disable_server("nonexistent-server")
                assert not success
    
    def test_enable_nonexistent_server(self):
        """Test enabling a server that doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ServerStateManager, '_get_enabled_config_path') as mock_enabled, \
                 patch.object(ServerStateManager, '_get_disabled_config_path') as mock_disabled:
                
                mock_enabled.return_value = Path(temp_dir) / "enabled.json"
                mock_disabled.return_value = Path(temp_dir) / "disabled.json"
                
                manager = ServerStateManager("claude-code")
                
                # Should return False for nonexistent server
                success = manager.enable_server("nonexistent-server")
                assert not success