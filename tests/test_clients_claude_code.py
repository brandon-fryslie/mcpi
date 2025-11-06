"""Tests for Claude Code client plugin."""

import pytest

from mcpi.clients.claude_code import ClaudeCodePlugin
from mcpi.clients.types import ServerConfig, ServerState


class TestClaudeCodePlugin:
    """Test ClaudeCodePlugin class."""

    @pytest.fixture
    def plugin(self, mcp_harness):
        """Create a ClaudeCodePlugin instance for testing using harness for safety."""
        return ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)

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
            "user-mcp",
        ]

        scopes = plugin.get_scope_names()
        assert set(scopes) == set(expected_scopes)

    def test_scope_priorities(self, plugin):
        """Test that scopes have correct priorities."""
        scopes = plugin.get_scopes()

        scope_priorities = {s.name: s.priority for s in scopes}

        assert scope_priorities["project-mcp"] == 1
        assert scope_priorities["project-local"] == 2
        assert scope_priorities["user-local"] == 3
        assert scope_priorities["user-global"] == 4
        assert scope_priorities["user-internal"] == 5
        assert scope_priorities["user-mcp"] == 6

    def test_scope_types(self, plugin):
        """Test that scopes are correctly categorized as user/project."""
        scopes = plugin.get_scopes()

        project_scopes = [s for s in scopes if s.is_project_level]
        user_scopes = [s for s in scopes if s.is_user_level]

        project_names = [s.name for s in project_scopes]
        assert "project-mcp" in project_names
        assert "project-local" in project_names

        user_names = [s.name for s in user_scopes]
        assert "user-local" in user_names
        assert "user-global" in user_names
        assert "user-internal" in user_names
        assert "user-mcp" in user_names

    def test_get_primary_scope(self, plugin):
        """Test that primary scope is user-mcp."""
        assert plugin.get_primary_scope() == "user-mcp"

    def test_get_project_scopes(self, plugin):
        """Test getting project-level scopes."""
        project_scopes = plugin.get_project_scopes()
        assert "project-mcp" in project_scopes
        assert "project-local" in project_scopes
        assert "user-local" not in project_scopes

    def test_get_user_scopes(self, plugin):
        """Test getting user-level scopes."""
        user_scopes = plugin.get_user_scopes()
        assert "user-local" in user_scopes
        assert "user-global" in user_scopes
        assert "user-mcp" in user_scopes
        assert "project-mcp" not in user_scopes

    def test_is_installed_no_claude_dir(self, plugin, tmp_path, monkeypatch):
        """Test is_installed when Claude directory doesn't exist."""
        # Use monkeypatch to override home directory
        monkeypatch.setenv("HOME", str(tmp_path))
        # Force re-check with new home
        assert not plugin.is_installed()

    def test_is_installed_with_claude_dir(self, plugin, tmp_path, monkeypatch):
        """Test is_installed when Claude directory exists."""
        monkeypatch.setenv("HOME", str(tmp_path))
        (tmp_path / ".claude").mkdir()
        assert plugin.is_installed()

    def test_get_installation_info(self, plugin):
        """Test getting installation information."""
        info = plugin.get_installation_info()

        assert info["client"] == "claude-code"
        assert "installed" in info
        assert "config_dir" in info
        assert "scopes" in info
        assert len(info["scopes"]) == 6

    def test_validate_server_config_valid(self, plugin):
        """Test validating a valid server configuration."""
        config = ServerConfig(
            command="python", args=["-m", "test_server"], type="stdio"
        )

        errors = plugin.validate_server_config(config)
        assert len(errors) == 0

    def test_validate_server_config_invalid_type(self, plugin):
        """Test validating server config with invalid type."""
        config = ServerConfig(command="python", args=["-m", "test"], type="invalid")

        errors = plugin.validate_server_config(config)
        assert len(errors) > 0
        assert any("Invalid server type" in e for e in errors)

    def test_validate_server_config_npx_without_args(self, plugin):
        """Test validating npx command without args."""
        config = ServerConfig(command="npx", args=[])

        errors = plugin.validate_server_config(config)
        assert any("NPX commands should specify a package" in e for e in errors)

    def test_validate_server_config_python_without_module(self, plugin):
        """Test validating python command without module syntax."""
        config = ServerConfig(command="python", args=["script.py"])

        errors = plugin.validate_server_config(config)
        assert any("Python commands should use module syntax" in e for e in errors)

    def test_list_servers_no_existing_files(self, plugin):
        """Test listing servers when no config files exist."""
        servers = plugin.list_servers()
        assert len(servers) == 0

    def test_list_servers_with_data(self, plugin, mcp_harness):
        """Test listing servers when config files exist."""
        # Prepopulate server data
        mcp_harness.prepopulate_file(
            "user-mcp",
            {
                "mcpServers": {
                    "test-server": {
                        "command": "python",
                        "args": ["-m", "test_server"],
                        "type": "stdio",
                    }
                }
            },
        )

        servers = plugin.list_servers()

        assert len(servers) == 1
        qualified_id = "claude-code:user-mcp:test-server"
        assert qualified_id in servers

        server_info = servers[qualified_id]
        assert server_info.id == "test-server"
        assert server_info.client == "claude-code"
        assert server_info.scope == "user-mcp"
        assert server_info.state == ServerState.ENABLED

    def test_list_servers_with_disabled_server(self, plugin, mcp_harness):
        """Test listing servers with disabled server using Claude's actual format.

        BUG-FIX: This test now correctly tests scope isolation. A server installed in
        user-local and marked disabled in user-local's disabled array should show as
        DISABLED. Previously this test incorrectly expected cross-scope pollution.
        """
        # Prepopulate server in user-local (which supports enable/disable arrays)
        mcp_harness.prepopulate_file(
            "user-local",
            {
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": ["disabled-server"],
                "mcpServers": {
                    "disabled-server": {
                        "command": "python",
                        "args": ["-m", "test_server"],
                        "type": "stdio",
                    }
                },
            },
        )

        servers = plugin.list_servers()

        qualified_id = "claude-code:user-local:disabled-server"
        server_info = servers[qualified_id]
        assert server_info.state == ServerState.DISABLED

    def test_list_servers_filtered_by_scope(self, plugin, mcp_harness):
        """Test listing servers filtered by specific scope."""
        # Prepopulate servers in different scopes
        mcp_harness.prepopulate_file(
            "user-mcp",
            {
                "mcpServers": {
                    "user-server": {"command": "python", "args": ["-m", "user_server"]}
                }
            },
        )
        mcp_harness.prepopulate_file(
            "project-mcp",
            {
                "mcpServers": {
                    "project-server": {"command": "node", "args": ["project_server.js"]}
                }
            },
        )

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

        result = plugin.add_server("test-server", config, "user-mcp")

        assert result.success

        # Verify server was added
        servers = plugin.list_servers(scope="user-mcp")
        qualified_id = "claude-code:user-mcp:test-server"
        assert qualified_id in servers

    def test_remove_server_invalid_scope(self, plugin):
        """Test removing server from invalid scope."""
        result = plugin.remove_server("test-server", "invalid-scope")

        assert not result.success
        assert "Unknown scope" in result.message

    def test_remove_server_success(self, plugin, mcp_harness):
        """Test successful server removal."""
        # Prepopulate a server first
        mcp_harness.prepopulate_file(
            "user-mcp",
            {
                "mcpServers": {
                    "test-server": {"command": "python", "args": ["-m", "test_server"]}
                }
            },
        )

        # Verify it exists
        servers_before = plugin.list_servers(scope="user-mcp")
        qualified_id = "claude-code:user-mcp:test-server"
        assert qualified_id in servers_before

        # Remove it
        result = plugin.remove_server("test-server", "user-mcp")

        assert result.success

        # Verify it's gone
        servers_after = plugin.list_servers(scope="user-mcp")
        assert qualified_id not in servers_after

    def test_get_server_state_not_installed(self, plugin):
        """Test getting state of non-existent server."""
        state = plugin.get_server_state("nonexistent-server")
        assert state == ServerState.NOT_INSTALLED

    def test_get_server_state_enabled(self, plugin, mcp_harness):
        """Test getting state of enabled server."""
        # Prepopulate an enabled server
        mcp_harness.prepopulate_file(
            "user-mcp",
            {
                "mcpServers": {
                    "test-server": {"command": "python", "args": ["-m", "test_server"]}
                }
            },
        )

        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

    def test_get_server_state_disabled(self, plugin, mcp_harness):
        """Test getting state of disabled server using Claude's actual format.

        BUG-FIX: This test now correctly tests a server in user-local (which supports
        enable/disable arrays) rather than testing cross-scope pollution.
        """
        # Prepopulate server in user-local (which supports enable/disable)
        mcp_harness.prepopulate_file(
            "user-local",
            {
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": ["test-server"],
                "mcpServers": {
                    "test-server": {"command": "python", "args": ["-m", "test_server"]}
                },
            },
        )

        state = plugin.get_server_state("test-server")
        assert state == ServerState.DISABLED

    def test_enable_server_not_found(self, plugin):
        """Test enabling non-existent server.

        BUG-FIX: After fixing the bug, enabling a non-existent server now correctly
        returns an error instead of succeeding with the wrong behavior.
        """
        result = plugin.enable_server("nonexistent-server")

        # Should fail because server doesn't exist in any scope
        assert not result.success
        assert "not found" in result.message.lower()

    def test_enable_server_already_enabled(self, plugin, mcp_harness):
        """Test enabling already enabled server."""
        # Prepopulate an enabled server in user-local (which supports enable/disable)
        mcp_harness.prepopulate_file(
            "user-local",
            {
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": [],
                "mcpServers": {
                    "test-server": {"command": "python", "args": ["-m", "test_server"]}
                },
            },
        )

        result = plugin.enable_server("test-server")

        assert result.success

    def test_enable_server_success(self, plugin, mcp_harness):
        """Test successful server enabling using Claude's actual format.

        BUG-FIX: This test now correctly tests enabling a server that exists in user-local
        (which supports enable/disable arrays).
        """
        # Prepopulate server in user-local with disabled state
        mcp_harness.prepopulate_file(
            "user-local",
            {
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": ["test-server"],
                "mcpServers": {
                    "test-server": {"command": "python", "args": ["-m", "test_server"]}
                },
            },
        )

        # Verify it's disabled
        state_before = plugin.get_server_state("test-server")
        assert state_before == ServerState.DISABLED

        # Enable it
        result = plugin.enable_server("test-server")

        assert result.success
        assert "Enabled server" in result.message

        # Verify it's enabled
        state_after = plugin.get_server_state("test-server")
        assert state_after == ServerState.ENABLED

    def test_disable_server_success(self, plugin, mcp_harness):
        """Test successful server disabling using Claude's actual format."""
        # Prepopulate an enabled server in user-local (which supports enable/disable)
        mcp_harness.prepopulate_file(
            "user-local",
            {
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": [],
                "mcpServers": {
                    "test-server": {"command": "python", "args": ["-m", "test_server"]}
                },
            },
        )

        # Verify it's enabled
        state_before = plugin.get_server_state("test-server")
        assert state_before == ServerState.ENABLED

        # Disable it
        result = plugin.disable_server("test-server")

        assert result.success
        assert "Disabled server" in result.message

        # Verify it's disabled
        state_after = plugin.get_server_state("test-server")
        assert state_after == ServerState.DISABLED
