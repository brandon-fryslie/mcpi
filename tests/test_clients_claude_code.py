"""Tests for Claude Code client plugin."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from mcpi.clients.claude_code import ClaudeCodePlugin
from mcpi.clients.types import ServerConfig, ServerState, OperationResult


class TestClaudeCodePlugin:
    """Test ClaudeCodePlugin class."""
    
    @pytest.fixture
    def plugin(self):
        """Create a ClaudeCodePlugin instance for testing."""
        with patch('mcpi.clients.claude_code.Path.home') as mock_home, \
             patch('mcpi.clients.claude_code.Path.cwd') as mock_cwd:
            
            # Mock home and current working directory
            mock_home.return_value = Path("/test/home")
            mock_cwd.return_value = Path("/test/project")
            
            return ClaudeCodePlugin()
    
    def test_get_name(self, plugin):
        """Test that plugin returns correct name."""
        assert plugin.name == "claude-code"
    
    def test_initialize_scopes(self, plugin):
        """Test that all expected scopes are initialized."""
        expected_scopes = [
            "project-mcp",
            "project-local", 
            "user-local",
            "user-global",
            "user-internal",
            "user-mcp"
        ]
        
        scope_names = plugin.get_scope_names()
        assert set(scope_names) == set(expected_scopes)
    
    def test_scope_priorities(self, plugin):
        """Test that scopes have correct priorities."""
        scopes = plugin.get_scopes()
        scope_priorities = {scope.name: scope.priority for scope in scopes}
        
        # Lower priority number = higher priority
        assert scope_priorities["project-mcp"] < scope_priorities["user-mcp"]
        assert scope_priorities["user-local"] < scope_priorities["user-global"]
    
    def test_scope_types(self, plugin):
        """Test that scopes are correctly marked as user/project level."""
        scopes = plugin.get_scopes()
        
        project_scopes = [s for s in scopes if s.is_project_level]
        user_scopes = [s for s in scopes if s.is_user_level]
        
        project_scope_names = {s.name for s in project_scopes}
        user_scope_names = {s.name for s in user_scopes}
        
        assert project_scope_names == {"project-mcp", "project-local"}
        assert user_scope_names == {"user-local", "user-global", "user-internal", "user-mcp"}
    
    def test_get_primary_scope(self, plugin):
        """Test getting primary scope."""
        assert plugin.get_primary_scope() == "user-mcp"
    
    def test_get_project_scopes(self, plugin):
        """Test getting project-level scopes."""
        project_scopes = plugin.get_project_scopes()
        assert set(project_scopes) == {"project-mcp", "project-local"}
    
    def test_get_user_scopes(self, plugin):
        """Test getting user-level scopes."""
        user_scopes = plugin.get_user_scopes()
        assert set(user_scopes) == {"user-local", "user-global", "user-internal", "user-mcp"}
    
    def test_is_installed_no_claude_dir(self, plugin):
        """Test is_installed() when Claude directory doesn't exist."""
        with patch('mcpi.clients.claude_code.Path.home') as mock_home:
            mock_home.return_value = Path("/test/home")
            
            # Mock that .claude directory doesn't exist
            with patch.object(Path, 'exists', return_value=False):
                assert not plugin.is_installed()
    
    def test_is_installed_with_claude_dir(self, plugin):
        """Test is_installed() when Claude directory exists."""
        with patch('mcpi.clients.claude_code.Path.home') as mock_home:
            mock_home.return_value = Path("/test/home")
            
            # Mock that .claude directory exists
            with patch.object(Path, 'exists', return_value=True):
                assert plugin.is_installed()
    
    def test_get_installation_info(self, plugin):
        """Test getting installation information."""
        with patch.object(plugin, 'is_installed', return_value=True):
            info = plugin.get_installation_info()
            
            assert info["client"] == "claude-code"
            assert info["installed"] is True
            assert info["config_dir"] == "/test/home/.claude"
            assert "scopes" in info
            assert len(info["scopes"]) == 6
            
            # Check scope info structure
            for scope_name, scope_info in info["scopes"].items():
                assert "path" in scope_info
                assert "exists" in scope_info
                assert "description" in scope_info
                assert "priority" in scope_info
                assert "is_user_level" in scope_info
                assert "is_project_level" in scope_info
    
    def test_validate_server_config_valid(self, plugin):
        """Test validation of valid server configuration."""
        config = ServerConfig(
            command="python",
            args=["-m", "mcp_server"],
            type="stdio"
        )
        
        errors = plugin.validate_server_config(config)
        assert errors == []
    
    def test_validate_server_config_invalid_type(self, plugin):
        """Test validation with invalid server type."""
        config = ServerConfig(
            command="python",
            args=["-m", "mcp_server"],
            type="invalid_type"
        )
        
        errors = plugin.validate_server_config(config)
        assert len(errors) > 0
        assert any("Invalid server type" in error for error in errors)
    
    def test_validate_server_config_npx_without_args(self, plugin):
        """Test validation of npx command without args."""
        config = ServerConfig(
            command="npx",
            args=[],
            type="stdio"
        )
        
        errors = plugin.validate_server_config(config)
        assert len(errors) > 0
        assert any("NPX commands should specify a package" in error for error in errors)
    
    def test_validate_server_config_python_without_module(self, plugin):
        """Test validation of python command without -m flag."""
        config = ServerConfig(
            command="python",
            args=["script.py"],  # No -m flag
            type="stdio"
        )
        
        errors = plugin.validate_server_config(config)
        assert len(errors) > 0
        assert any("Python commands should use module syntax" in error for error in errors)
    
    def test_list_servers_no_existing_files(self, plugin):
        """Test listing servers when no configuration files exist."""
        # Mock all scope handlers to return empty
        for handler in plugin._scopes.values():
            handler.exists = Mock(return_value=False)
            handler.get_servers = Mock(return_value={})
        
        servers = plugin.list_servers()
        assert servers == {}
    
    def test_list_servers_with_data(self, plugin):
        """Test listing servers with existing data."""
        # Mock one scope to have data
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.exists = Mock(return_value=True)
        mock_handler.get_servers = Mock(return_value={
            "test-server": {
                "command": "python",
                "args": ["-m", "test_server"],
                "type": "stdio"
            }
        })
        
        # Mock other scopes to be empty
        for name, handler in plugin._scopes.items():
            if name != "user-mcp":
                handler.exists = Mock(return_value=False)
                handler.get_servers = Mock(return_value={})
        
        servers = plugin.list_servers()
        
        assert len(servers) == 1
        qualified_id = "claude-code:user-mcp:test-server"
        assert qualified_id in servers
        
        server_info = servers[qualified_id]
        assert server_info.id == "test-server"
        assert server_info.client == "claude-code"
        assert server_info.scope == "user-mcp"
        assert server_info.state == ServerState.ENABLED
    
    def test_list_servers_with_disabled_server(self, plugin):
        """Test listing servers with disabled server."""
        # Mock scope with disabled server
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.exists = Mock(return_value=True)
        mock_handler.get_servers = Mock(return_value={
            "disabled-server": {
                "command": "python",
                "args": ["-m", "test_server"],
                "type": "stdio",
                "disabled": True
            }
        })
        
        # Mock other scopes to be empty
        for name, handler in plugin._scopes.items():
            if name != "user-mcp":
                handler.exists = Mock(return_value=False)
                handler.get_servers = Mock(return_value={})
        
        servers = plugin.list_servers()
        
        qualified_id = "claude-code:user-mcp:disabled-server"
        server_info = servers[qualified_id]
        assert server_info.state == ServerState.DISABLED
    
    def test_list_servers_filtered_by_scope(self, plugin):
        """Test listing servers filtered by specific scope."""
        # Mock user-mcp scope to have data
        user_mcp_handler = plugin._scopes["user-mcp"]
        user_mcp_handler.exists = Mock(return_value=True)
        user_mcp_handler.get_servers = Mock(return_value={
            "user-server": {"command": "python", "args": ["-m", "user_server"]}
        })
        
        # Mock project-mcp scope to have different data
        project_mcp_handler = plugin._scopes["project-mcp"]
        project_mcp_handler.exists = Mock(return_value=True)
        project_mcp_handler.get_servers = Mock(return_value={
            "project-server": {"command": "node", "args": ["project_server.js"]}
        })
        
        # List servers for user-mcp scope only
        servers = plugin.list_servers(scope="user-mcp")
        
        assert len(servers) == 1
        qualified_id = "claude-code:user-mcp:user-server"
        assert qualified_id in servers
        
        # Ensure project server is not included
        project_qualified_id = "claude-code:project-mcp:project-server"
        assert project_qualified_id not in servers
    
    def test_add_server_invalid_scope(self, plugin):
        """Test adding server to invalid scope."""
        config = ServerConfig(command="python", args=["-m", "test"])
        
        result = plugin.add_server("test-server", config, "invalid-scope")
        
        assert not result.success
        assert "Unknown scope" in result.message
    
    def test_add_server_validation_failure(self, plugin):
        """Test adding server with invalid configuration."""
        config = ServerConfig(command="", args=[])  # Invalid: no command
        
        result = plugin.add_server("test-server", config, "user-mcp")
        
        assert not result.success
        assert "Invalid server configuration" in result.message
    
    def test_add_server_success(self, plugin):
        """Test successful server addition."""
        config = ServerConfig(command="python", args=["-m", "test_server"])
        
        # Mock the scope handler
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.add_server = Mock(return_value=OperationResult.success_result("Server added"))
        
        result = plugin.add_server("test-server", config, "user-mcp")
        
        assert result.success
        mock_handler.add_server.assert_called_once_with("test-server", config)
    
    def test_remove_server_invalid_scope(self, plugin):
        """Test removing server from invalid scope."""
        result = plugin.remove_server("test-server", "invalid-scope")
        
        assert not result.success
        assert "Unknown scope" in result.message
    
    def test_remove_server_success(self, plugin):
        """Test successful server removal."""
        # Mock the scope handler
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.remove_server = Mock(return_value=OperationResult.success_result("Server removed"))
        
        result = plugin.remove_server("test-server", "user-mcp")
        
        assert result.success
        mock_handler.remove_server.assert_called_once_with("test-server")
    
    def test_get_server_state_not_installed(self, plugin):
        """Test getting state of non-existent server."""
        # Mock all handlers to not have the server
        for handler in plugin._scopes.values():
            handler.has_server = Mock(return_value=False)
        
        state = plugin.get_server_state("nonexistent-server")
        assert state == ServerState.NOT_INSTALLED
    
    def test_get_server_state_enabled(self, plugin):
        """Test getting state of enabled server."""
        # Mock handler to have enabled server
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.has_server = Mock(return_value=True)
        mock_handler.get_servers = Mock(return_value={
            "test-server": {"command": "python", "disabled": False}
        })
        
        # Mock other handlers to not have the server
        for name, handler in plugin._scopes.items():
            if name != "user-mcp":
                handler.has_server = Mock(return_value=False)
        
        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED
    
    def test_get_server_state_disabled(self, plugin):
        """Test getting state of disabled server."""
        # Mock handler to have disabled server
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.has_server = Mock(return_value=True)
        mock_handler.get_servers = Mock(return_value={
            "test-server": {"command": "python", "disabled": True}
        })
        
        # Mock other handlers to not have the server
        for name, handler in plugin._scopes.items():
            if name != "user-mcp":
                handler.has_server = Mock(return_value=False)
        
        state = plugin.get_server_state("test-server")
        assert state == ServerState.DISABLED
    
    def test_enable_server_not_found(self, plugin):
        """Test enabling non-existent server."""
        # Mock all handlers to not have the server
        for handler in plugin._scopes.values():
            handler.has_server = Mock(return_value=False)
        
        result = plugin.enable_server("nonexistent-server")
        
        assert not result.success
        assert "not found" in result.message
    
    def test_enable_server_already_enabled(self, plugin):
        """Test enabling already enabled server."""
        # Mock handler to have enabled server
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.has_server = Mock(return_value=True)
        mock_handler.get_servers = Mock(return_value={
            "test-server": {"command": "python"}  # No disabled flag = enabled
        })
        
        # Mock other handlers to not have the server
        for name, handler in plugin._scopes.items():
            if name != "user-mcp":
                handler.has_server = Mock(return_value=False)
        
        result = plugin.enable_server("test-server")
        
        assert result.success
        assert "already enabled" in result.message
    
    def test_enable_server_success(self, plugin):
        """Test successful server enabling."""
        # Mock handler to have disabled server
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.has_server = Mock(return_value=True)
        mock_handler.get_servers = Mock(return_value={
            "test-server": {"command": "python", "disabled": True}
        })
        mock_handler.update_server = Mock(return_value=OperationResult.success_result("Server updated"))
        
        # Mock other handlers to not have the server
        for name, handler in plugin._scopes.items():
            if name != "user-mcp":
                handler.has_server = Mock(return_value=False)
        
        result = plugin.enable_server("test-server")
        
        assert result.success
        assert "Enabled server" in result.message
        
        # Verify update_server was called with config without disabled flag
        mock_handler.update_server.assert_called_once()
        call_args = mock_handler.update_server.call_args
        updated_config = call_args[0][1]  # Second argument is the ServerConfig
        assert "disabled" not in updated_config.to_dict()
    
    def test_disable_server_success(self, plugin):
        """Test successful server disabling."""
        # Mock handler to have enabled server
        mock_handler = plugin._scopes["user-mcp"]
        mock_handler.has_server = Mock(return_value=True)
        mock_handler.get_servers = Mock(return_value={
            "test-server": {"command": "python"}  # No disabled flag = enabled
        })
        mock_handler.update_server = Mock(return_value=OperationResult.success_result("Server updated"))
        
        # Mock other handlers to not have the server
        for name, handler in plugin._scopes.items():
            if name != "user-mcp":
                handler.has_server = Mock(return_value=False)
        
        result = plugin.disable_server("test-server")
        
        assert result.success
        assert "Disabled server" in result.message
        
        # Verify update_server was called with config with disabled flag
        mock_handler.update_server.assert_called_once()
        call_args = mock_handler.update_server.call_args
        updated_config = call_args[0][1]  # Second argument is the ServerConfig
        config_dict = updated_config.to_dict()
        assert config_dict.get("disabled") is True