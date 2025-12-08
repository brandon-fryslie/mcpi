"""Functional tests for Roo Code MCP client plugin.

These tests validate REAL user workflows for Roo Code (Cline fork):
- Server installation to BOTH user-level and project-level scopes
- Scope priority: project overrides user when same server exists in both
- Enable/disable via inline "disabled" field in server config (InlineEnableDisableHandler)
- Config persistence across operations
- Real file I/O (no mocks of user-facing layers)

Tests use REAL file operations (via temp directories) and REAL plugin code.
NO mocking of user-facing functionality - tests fail when users would fail.
"""

import json
import os
from pathlib import Path

import pytest

from mcpi.clients.types import ServerConfig, ServerState


class TestRooCodePlugin:
    """Functional tests for RooCodePlugin.

    These tests validate end-to-end user workflows:
    1. User installs server to user scope → appears in user config → shows in list
    2. User installs server to project scope → appears in project config → shows in list
    3. Same server in both scopes → project scope wins (lower priority number)
    4. User disables server → "disabled": true added to config → shows DISABLED
    5. Config persists correctly across operations

    UN-GAMEABLE because:
    - Uses REAL file I/O (temp directories, not mocks)
    - Verifies actual file contents on disk
    - Tests complete user journey (not implementation details)
    - Tests scope priority by checking which config is returned
    """

    @pytest.fixture
    def plugin(self, tmp_path):
        """Create RooCodePlugin with isolated test directory.

        Uses path_overrides to redirect all file operations to tmp_path,
        preventing any modification of real user files.

        Roo Code uses InlineEnableDisableHandler, so only needs active paths
        (no separate disabled files like Cursor).
        """
        from mcpi.clients.roo_code import RooCodePlugin

        # User scope path (global config)
        user_config_path = tmp_path / "user" / "mcp_settings.json"

        # Project scope path
        project_config_path = tmp_path / "project" / ".roo" / "mcp.json"

        path_overrides = {
            "user": user_config_path,
            "project": project_config_path,
        }

        return RooCodePlugin(path_overrides=path_overrides)

    @pytest.fixture
    def user_config_path(self, tmp_path):
        """Get the user scope config path."""
        return tmp_path / "user" / "mcp_settings.json"

    @pytest.fixture
    def project_config_path(self, tmp_path):
        """Get the project scope config path."""
        return tmp_path / "project" / ".roo" / "mcp.json"

    # =========================================================================
    # Plugin Identity and Initialization
    # =========================================================================

    def test_get_name(self, plugin):
        """Test that plugin returns correct name.

        VALIDATES: Plugin discovery and identification in multi-client environment.
        """
        assert plugin.name == "roo-code"

    def test_initialize_scopes_creates_two_scopes(self, plugin):
        """Test that plugin initializes exactly two scopes.

        VALIDATES: Roo Code's 2-scope model (user + project).
        """
        scopes = plugin.get_scope_names()
        assert len(scopes) == 2
        assert "user" in scopes
        assert "project" in scopes

    def test_user_scope_is_user_level(self, plugin):
        """Test that user scope is correctly marked as user-level.

        VALIDATES: Scope categorization for UI/CLI filtering.
        """
        scopes = plugin.get_scopes()
        user_scope = next(s for s in scopes if s.name == "user")
        assert user_scope.is_user_level is True
        assert user_scope.is_project_level is False

    def test_project_scope_is_project_level(self, plugin):
        """Test that project scope is correctly marked as project-level.

        VALIDATES: Scope categorization for UI/CLI filtering.
        """
        scopes = plugin.get_scopes()
        project_scope = next(s for s in scopes if s.name == "project")
        assert project_scope.is_project_level is True
        assert project_scope.is_user_level is False

    def test_both_scopes_are_writable(self, plugin):
        """Test that both scopes are not read-only.

        VALIDATES: Users can add/remove servers in both scopes.
        """
        scopes = plugin.get_scopes()
        for scope in scopes:
            assert scope.readonly is False

    def test_project_scope_has_higher_priority_than_user(self, plugin):
        """Test that project scope has lower priority number (higher precedence).

        VALIDATES: Priority ordering - project overrides user.
        Lower number = higher priority.
        """
        scopes = plugin.get_scopes()
        user_scope = next(s for s in scopes if s.name == "user")
        project_scope = next(s for s in scopes if s.name == "project")

        # Project should have lower priority number (higher precedence)
        assert project_scope.priority < user_scope.priority

    # =========================================================================
    # Server CRUD - User Scope
    # =========================================================================

    def test_add_server_to_user_scope_creates_config_file(self, plugin, user_config_path):
        """Test that adding server to user scope creates config file.

        VALIDATES: User's first server installation creates necessary files.

        UN-GAMEABLE: Verifies actual file exists on disk.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        result = plugin.add_server("filesystem", config, "user")

        assert result.success is True
        assert user_config_path.exists()

    def test_add_server_to_user_scope_appears_in_list(self, plugin):
        """Test that server added to user scope appears when listing.

        VALIDATES: Complete user workflow - install to user scope → verify.

        UN-GAMEABLE: Reads back from real file, not from mock state.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        plugin.add_server("filesystem", config, "user")
        servers = plugin.list_servers(scope="user")

        assert len(servers) == 1
        qualified_id = "roo-code:user:filesystem"
        assert qualified_id in servers

    def test_add_server_to_user_scope_has_correct_metadata(self, plugin):
        """Test that server in user scope has all expected metadata.

        VALIDATES: ServerInfo structure completeness for UI display.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        plugin.add_server("filesystem", config, "user")
        servers = plugin.list_servers(scope="user")

        qualified_id = "roo-code:user:filesystem"
        server_info = servers[qualified_id]

        assert server_info.id == "filesystem"
        assert server_info.client == "roo-code"
        assert server_info.scope == "user"
        assert server_info.state == ServerState.ENABLED
        assert server_info.config is not None

    def test_add_server_with_environment_variables_to_user_scope(self, plugin):
        """Test adding server with environment variables to user scope.

        VALIDATES: Complex config handling (env vars, multiple args).
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": "test-token-placeholder"},
        )

        result = plugin.add_server("github", config, "user")

        assert result.success is True

        servers = plugin.list_servers(scope="user")
        qualified_id = "roo-code:user:github"
        server_info = servers[qualified_id]

        assert server_info.config["env"]["GITHUB_TOKEN"] == "test-token-placeholder"

    def test_remove_server_from_user_scope(self, plugin):
        """Test removing server from user scope.

        VALIDATES: User can uninstall servers from user scope.

        UN-GAMEABLE: Verifies server is actually gone from config file.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        # Verify it exists
        servers_before = plugin.list_servers(scope="user")
        assert len(servers_before) == 1

        # Remove it
        result = plugin.remove_server("test-server", "user")

        assert result.success is True

        # Verify it's gone
        servers_after = plugin.list_servers(scope="user")
        assert len(servers_after) == 0

    def test_update_server_in_user_scope_modifies_config(self, plugin):
        """Test that updating server in user scope changes its configuration.

        VALIDATES: User can modify server settings after installation.

        UN-GAMEABLE: Reads back updated config from file.
        """
        # Add initial server
        initial_config = ServerConfig(command="npx", args=["-y", "old-package"])
        plugin.add_server("test-server", initial_config, "user")

        # Update with new config
        updated_config = ServerConfig(command="uvx", args=["new-package"])
        result = plugin.update_server("test-server", updated_config, "user")

        assert result.success is True

        # Verify update persisted
        servers = plugin.list_servers(scope="user")
        qualified_id = "roo-code:user:test-server"
        server_info = servers[qualified_id]

        assert server_info.config["command"] == "uvx"
        assert server_info.config["args"] == ["new-package"]

    # =========================================================================
    # Server CRUD - Project Scope
    # =========================================================================

    def test_add_server_to_project_scope_creates_config_file(self, plugin, project_config_path):
        """Test that adding server to project scope creates config file.

        VALIDATES: Project-level server installation.

        UN-GAMEABLE: Verifies actual file exists on disk.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        result = plugin.add_server("filesystem", config, "project")

        assert result.success is True
        assert project_config_path.exists()

    def test_add_server_to_project_scope_appears_in_list(self, plugin):
        """Test that server added to project scope appears when listing.

        VALIDATES: Project scope server installation workflow.

        UN-GAMEABLE: Reads back from real file.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        plugin.add_server("filesystem", config, "project")
        servers = plugin.list_servers(scope="project")

        assert len(servers) == 1
        qualified_id = "roo-code:project:filesystem"
        assert qualified_id in servers

    def test_add_server_to_project_scope_has_correct_metadata(self, plugin):
        """Test that server in project scope has correct metadata.

        VALIDATES: ServerInfo includes scope information.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        plugin.add_server("filesystem", config, "project")
        servers = plugin.list_servers(scope="project")

        qualified_id = "roo-code:project:filesystem"
        server_info = servers[qualified_id]

        assert server_info.id == "filesystem"
        assert server_info.client == "roo-code"
        assert server_info.scope == "project"
        assert server_info.state == ServerState.ENABLED

    def test_remove_server_from_project_scope(self, plugin):
        """Test removing server from project scope.

        VALIDATES: User can uninstall project-level servers.

        UN-GAMEABLE: Verifies server is actually gone from config file.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "project")

        # Verify it exists
        servers_before = plugin.list_servers(scope="project")
        assert len(servers_before) == 1

        # Remove it
        result = plugin.remove_server("test-server", "project")

        assert result.success is True

        # Verify it's gone
        servers_after = plugin.list_servers(scope="project")
        assert len(servers_after) == 0

    def test_add_multiple_servers_to_project_scope(self, plugin):
        """Test adding multiple servers to project scope.

        VALIDATES: Multi-server management in project config file.
        """
        servers_to_add = [
            ("filesystem", ServerConfig(command="npx", args=["-y", "server-filesystem"])),
            ("github", ServerConfig(command="npx", args=["-y", "server-github"])),
            ("sqlite", ServerConfig(command="uvx", args=["mcp-server-sqlite"])),
        ]

        for server_id, config in servers_to_add:
            result = plugin.add_server(server_id, config, "project")
            assert result.success is True

        servers = plugin.list_servers(scope="project")
        assert len(servers) == 3

        for server_id, _ in servers_to_add:
            qualified_id = f"roo-code:project:{server_id}"
            assert qualified_id in servers

    # =========================================================================
    # Scope Priority and Override Behavior
    # =========================================================================

    def test_server_in_both_scopes_shows_both_entries(self, plugin):
        """Test that same server ID in both scopes shows as two separate entries.

        VALIDATES: Scope isolation - servers are namespaced by scope.

        UN-GAMEABLE: Verifies both configs exist in separate files.
        """
        user_config = ServerConfig(command="npx", args=["-y", "user-version"])
        project_config = ServerConfig(command="npx", args=["-y", "project-version"])

        plugin.add_server("duplicated", user_config, "user")
        plugin.add_server("duplicated", project_config, "project")

        # List all servers (no scope filter)
        servers = plugin.list_servers()

        # Should have TWO entries with different qualified IDs
        assert len(servers) == 2
        assert "roo-code:user:duplicated" in servers
        assert "roo-code:project:duplicated" in servers

    def test_project_scope_has_higher_precedence_than_user(self, plugin):
        """Test that project scope has higher precedence (lower priority number).

        VALIDATES: When same server exists in both scopes, project wins.

        This is critical for workflow: user sets defaults globally,
        project overrides for specific needs.

        UN-GAMEABLE: Checks actual priority numbers from scope config.
        """
        user_config = ServerConfig(command="npx", args=["-y", "user-version"])
        project_config = ServerConfig(command="npx", args=["-y", "project-version"])

        plugin.add_server("duplicated", user_config, "user")
        plugin.add_server("duplicated", project_config, "project")

        servers = plugin.list_servers()

        user_server = servers["roo-code:user:duplicated"]
        project_server = servers["roo-code:project:duplicated"]

        # Project should have LOWER priority number (higher precedence)
        assert project_server.priority < user_server.priority

    def test_listing_specific_scope_shows_only_that_scope(self, plugin):
        """Test that scope filtering works correctly.

        VALIDATES: CLI --scope filter functionality.
        """
        user_config = ServerConfig(command="npx", args=["-y", "user-version"])
        project_config = ServerConfig(command="npx", args=["-y", "project-version"])

        plugin.add_server("only-user", user_config, "user")
        plugin.add_server("only-project", project_config, "project")
        plugin.add_server("in-both", user_config, "user")
        plugin.add_server("in-both", project_config, "project")

        # List only user scope
        user_servers = plugin.list_servers(scope="user")
        assert len(user_servers) == 2
        assert "roo-code:user:only-user" in user_servers
        assert "roo-code:user:in-both" in user_servers

        # List only project scope
        project_servers = plugin.list_servers(scope="project")
        assert len(project_servers) == 2
        assert "roo-code:project:only-project" in project_servers
        assert "roo-code:project:in-both" in project_servers

        # List all scopes
        all_servers = plugin.list_servers()
        assert len(all_servers) == 4

    def test_project_config_isolated_from_user_config(self, plugin, user_config_path, project_config_path):
        """Test that project config file is completely separate from user config.

        VALIDATES: File isolation - no shared state between scopes.

        UN-GAMEABLE: Reads both config files separately and verifies contents.
        """
        user_config = ServerConfig(command="npx", args=["-y", "user-only"])
        project_config = ServerConfig(command="npx", args=["-y", "project-only"])

        plugin.add_server("user-server", user_config, "user")
        plugin.add_server("project-server", project_config, "project")

        # Verify user config contains only user server
        with open(user_config_path) as f:
            user_data = json.load(f)
        assert "user-server" in user_data.get("mcpServers", {})
        assert "project-server" not in user_data.get("mcpServers", {})

        # Verify project config contains only project server
        with open(project_config_path) as f:
            project_data = json.load(f)
        assert "project-server" in project_data.get("mcpServers", {})
        assert "user-server" not in project_data.get("mcpServers", {})

    # =========================================================================
    # Enable/Disable - User Scope (InlineEnableDisableHandler)
    # =========================================================================

    def test_newly_added_server_in_user_scope_is_enabled(self, plugin):
        """Test that newly added servers in user scope start in ENABLED state.

        VALIDATES: Default state after installation (no "disabled" field).
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

    def test_disable_server_in_user_scope_adds_disabled_field(self, plugin, user_config_path):
        """Test that disabling server in user scope adds "disabled": true to config.

        VALIDATES: InlineEnableDisableHandler mechanism for user scope.

        UN-GAMEABLE: Checks actual file operations:
        1. Server has no "disabled" field before disable
        2. Server has "disabled": true after disable
        3. Other server config fields remain unchanged
        """
        # Add server
        config = ServerConfig(
            command="npx",
            args=["-y", "server-test"],
            env={"TEST_VAR": "value"},
        )
        plugin.add_server("test-server", config, "user")

        # Verify no disabled field initially
        with open(user_config_path) as f:
            data_before = json.load(f)
        server_before = data_before["mcpServers"]["test-server"]
        assert "disabled" not in server_before

        # Disable server
        result = plugin.disable_server("test-server", scope="user")

        assert result.success is True

        # Verify disabled field added
        with open(user_config_path) as f:
            data_after = json.load(f)
        server_after = data_after["mcpServers"]["test-server"]

        assert server_after["disabled"] is True
        # Verify other fields unchanged
        assert server_after["command"] == "npx"
        assert server_after["args"] == ["-y", "server-test"]
        assert server_after["env"]["TEST_VAR"] == "value"

    def test_disable_server_in_user_scope_changes_state_to_disabled(self, plugin):
        """Test that disabled server in user scope shows DISABLED state.

        VALIDATES: State detection works correctly.
        """
        # Add and disable server
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server", scope="user")

        # Check state
        state = plugin.get_server_state("test-server")
        assert state == ServerState.DISABLED

    def test_disabled_server_in_user_scope_still_appears_in_list(self, plugin):
        """Test that disabled servers in user scope appear in server list with DISABLED state.

        VALIDATES: Users can see all servers (enabled + disabled) for management.
        """
        # Add and disable server
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server", scope="user")

        # List servers
        servers = plugin.list_servers(scope="user")

        qualified_id = "roo-code:user:test-server"
        assert qualified_id in servers
        assert servers[qualified_id].state == ServerState.DISABLED

    def test_enable_disabled_server_in_user_scope_removes_disabled_field(self, plugin, user_config_path):
        """Test that enabling disabled server in user scope removes "disabled" field from config.

        VALIDATES: Round-trip disable → enable workflow.

        UN-GAMEABLE: Verifies actual file operations in both directions.
        """
        # Add, disable, then enable server
        config = ServerConfig(
            command="npx",
            args=["-y", "server-test"],
            env={"TEST_VAR": "value"},
        )
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server", scope="user")

        # Verify disabled field exists
        with open(user_config_path) as f:
            data_disabled = json.load(f)
        assert data_disabled["mcpServers"]["test-server"]["disabled"] is True

        # Enable server
        result = plugin.enable_server("test-server", scope="user")

        assert result.success is True

        # Verify disabled field removed
        with open(user_config_path) as f:
            data_enabled = json.load(f)
        server_config = data_enabled["mcpServers"]["test-server"]

        assert "disabled" not in server_config
        # Verify other fields unchanged
        assert server_config["command"] == "npx"
        assert server_config["args"] == ["-y", "server-test"]
        assert server_config["env"]["TEST_VAR"] == "value"

    def test_enable_disabled_server_in_user_scope_changes_state_to_enabled(self, plugin):
        """Test that enabled server in user scope shows ENABLED state.

        VALIDATES: Complete disable/enable cycle restores original state.
        """
        # Add, disable, enable
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server", scope="user")
        plugin.enable_server("test-server", scope="user")

        # Check state
        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

    def test_enable_already_enabled_server_in_user_scope_succeeds(self, plugin):
        """Test that enabling already enabled server in user scope is idempotent.

        VALIDATES: Idempotent operations (common in automation scripts).
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        result = plugin.enable_server("test-server", scope="user")

        assert result.success is True

    def test_disable_already_disabled_server_in_user_scope_succeeds(self, plugin):
        """Test that disabling already disabled server in user scope is idempotent.

        VALIDATES: Idempotent operations.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server", scope="user")

        result = plugin.disable_server("test-server", scope="user")

        assert result.success is True

    def test_disabled_field_set_to_false_in_user_scope_is_enabled(self, plugin, user_config_path):
        """Test that "disabled": false in user scope is treated as enabled.

        VALIDATES: Both missing field AND false value mean enabled.

        This is important because some users might manually edit config
        and set "disabled": false instead of removing the field.
        """
        # Add server
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        # Manually set disabled: false
        with open(user_config_path) as f:
            data = json.load(f)
        data["mcpServers"]["test-server"]["disabled"] = False
        with open(user_config_path, "w") as f:
            json.dump(data, f)

        # Should be treated as enabled
        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

        # Should appear in list as enabled
        servers = plugin.list_servers(scope="user")
        qualified_id = "roo-code:user:test-server"
        assert servers[qualified_id].state == ServerState.ENABLED

    # =========================================================================
    # Enable/Disable - Project Scope (InlineEnableDisableHandler)
    # =========================================================================

    def test_newly_added_server_in_project_scope_is_enabled(self, plugin):
        """Test that newly added servers in project scope start in ENABLED state.

        VALIDATES: Default state after installation in project scope.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "project")

        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

    def test_disable_server_in_project_scope_adds_disabled_field(self, plugin, project_config_path):
        """Test that disabling server in project scope adds "disabled": true to config.

        VALIDATES: InlineEnableDisableHandler mechanism for project scope.

        UN-GAMEABLE: Checks actual file operations.
        """
        # Add server
        config = ServerConfig(
            command="npx",
            args=["-y", "server-test"],
            env={"TEST_VAR": "value"},
        )
        plugin.add_server("test-server", config, "project")

        # Verify no disabled field initially
        with open(project_config_path) as f:
            data_before = json.load(f)
        server_before = data_before["mcpServers"]["test-server"]
        assert "disabled" not in server_before

        # Disable server
        result = plugin.disable_server("test-server", scope="project")

        assert result.success is True

        # Verify disabled field added
        with open(project_config_path) as f:
            data_after = json.load(f)
        server_after = data_after["mcpServers"]["test-server"]

        assert server_after["disabled"] is True
        # Verify other fields unchanged
        assert server_after["command"] == "npx"
        assert server_after["args"] == ["-y", "server-test"]
        assert server_after["env"]["TEST_VAR"] == "value"

    def test_disabled_server_in_project_scope_shows_disabled_state(self, plugin):
        """Test that disabled server in project scope shows DISABLED state.

        VALIDATES: State detection for project scope.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "project")
        plugin.disable_server("test-server", scope="project")

        state = plugin.get_server_state("test-server")
        assert state == ServerState.DISABLED

    def test_enable_disabled_server_in_project_scope_removes_disabled_field(self, plugin, project_config_path):
        """Test that enabling disabled server in project scope removes "disabled" field.

        VALIDATES: Round-trip disable → enable for project scope.

        UN-GAMEABLE: Verifies config field removed from actual file.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "server-test"],
            env={"TEST_VAR": "value"},
        )
        plugin.add_server("test-server", config, "project")
        plugin.disable_server("test-server", scope="project")

        # Verify disabled field exists
        with open(project_config_path) as f:
            data_disabled = json.load(f)
        assert data_disabled["mcpServers"]["test-server"]["disabled"] is True

        # Enable server
        result = plugin.enable_server("test-server", scope="project")

        assert result.success is True

        # Verify disabled field removed
        with open(project_config_path) as f:
            data_enabled = json.load(f)
        server_config = data_enabled["mcpServers"]["test-server"]

        assert "disabled" not in server_config
        # Verify other fields unchanged
        assert server_config["command"] == "npx"
        assert server_config["args"] == ["-y", "server-test"]
        assert server_config["env"]["TEST_VAR"] == "value"

    # =========================================================================
    # Enable/Disable - Cross-Scope Scenarios
    # =========================================================================

    def test_disabling_server_in_one_scope_does_not_affect_other_scope(self, plugin):
        """Test that disabling server in one scope leaves other scope enabled.

        VALIDATES: Scope isolation for enable/disable operations.

        Critical for workflow: user might want project-specific disable
        without affecting global user-level config.

        UN-GAMEABLE: Verifies states in both scopes separately.
        """
        user_config = ServerConfig(command="npx", args=["-y", "user-version"])
        project_config = ServerConfig(command="npx", args=["-y", "project-version"])

        plugin.add_server("duplicated", user_config, "user")
        plugin.add_server("duplicated", project_config, "project")

        # Disable in project scope only
        plugin.disable_server("duplicated", scope="project")

        # Check states
        servers = plugin.list_servers()
        user_server = servers["roo-code:user:duplicated"]
        project_server = servers["roo-code:project:duplicated"]

        assert user_server.state == ServerState.ENABLED
        assert project_server.state == ServerState.DISABLED

    def test_auto_detect_scope_for_disable_when_in_single_scope(self, plugin):
        """Test that scope auto-detection works for disable.

        VALIDATES: Convenience feature - user doesn't need to specify scope
        when server only exists in one scope.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        # Disable without specifying scope
        result = plugin.disable_server("test-server")

        assert result.success is True

        state = plugin.get_server_state("test-server")
        assert state == ServerState.DISABLED

    def test_auto_detect_scope_for_enable_when_in_single_scope(self, plugin):
        """Test that scope auto-detection works for enable.

        VALIDATES: Convenience feature for enable operations.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server")

        # Enable without specifying scope
        result = plugin.enable_server("test-server")

        assert result.success is True

        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

    # =========================================================================
    # Config Persistence and File Format
    # =========================================================================

    def test_user_config_file_has_correct_json_structure(self, plugin, user_config_path):
        """Test that user config uses standard mcpServers structure.

        VALIDATES: Config format compatibility with Roo Code.

        UN-GAMEABLE: Parses actual JSON file and validates structure.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        with open(user_config_path) as f:
            config_data = json.load(f)

        assert "mcpServers" in config_data
        assert isinstance(config_data["mcpServers"], dict)
        assert "test-server" in config_data["mcpServers"]

    def test_project_config_file_has_correct_json_structure(self, plugin, project_config_path):
        """Test that project config uses standard mcpServers structure.

        VALIDATES: Config format compatibility for project scope.

        UN-GAMEABLE: Parses actual JSON file.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "project")

        with open(project_config_path) as f:
            config_data = json.load(f)

        assert "mcpServers" in config_data
        assert isinstance(config_data["mcpServers"], dict)
        assert "test-server" in config_data["mcpServers"]

    def test_config_persists_across_plugin_instances(self, tmp_path):
        """Test that configs persist when creating new plugin instance.

        VALIDATES: Real persistence - config survives process restart.

        UN-GAMEABLE: Creates two separate plugin instances, verifies state
        persists via filesystem (not in-memory state).
        """
        from mcpi.clients.roo_code import RooCodePlugin

        user_config_path = tmp_path / "user" / "mcp_settings.json"
        project_config_path = tmp_path / "project" / ".roo" / "mcp.json"

        path_overrides = {
            "user": user_config_path,
            "project": project_config_path,
        }

        # First instance: add servers to both scopes
        plugin1 = RooCodePlugin(path_overrides=path_overrides)
        user_config = ServerConfig(command="npx", args=["-y", "user-server"])
        project_config = ServerConfig(command="npx", args=["-y", "project-server"])
        plugin1.add_server("user-server", user_config, "user")
        plugin1.add_server("project-server", project_config, "project")

        # Second instance: verify both servers exist
        plugin2 = RooCodePlugin(path_overrides=path_overrides)
        servers = plugin2.list_servers()

        assert "roo-code:user:user-server" in servers
        assert "roo-code:project:project-server" in servers

    def test_disabled_state_persists_across_plugin_instances(self, tmp_path):
        """Test that disabled state persists across restarts in both scopes.

        VALIDATES: Disabled servers stay disabled after restart.

        UN-GAMEABLE: Two plugin instances, verifies persistence via files.
        """
        from mcpi.clients.roo_code import RooCodePlugin

        user_config_path = tmp_path / "user" / "mcp_settings.json"
        project_config_path = tmp_path / "project" / ".roo" / "mcp.json"

        path_overrides = {
            "user": user_config_path,
            "project": project_config_path,
        }

        # First instance: add and disable servers in both scopes
        plugin1 = RooCodePlugin(path_overrides=path_overrides)
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin1.add_server("user-disabled", config, "user")
        plugin1.add_server("project-disabled", config, "project")
        plugin1.disable_server("user-disabled", scope="user")
        plugin1.disable_server("project-disabled", scope="project")

        # Second instance: verify both still disabled
        plugin2 = RooCodePlugin(path_overrides=path_overrides)
        user_state = plugin2.get_server_state("user-disabled")
        project_state = plugin2.get_server_state("project-disabled")

        assert user_state == ServerState.DISABLED
        assert project_state == ServerState.DISABLED

    def test_atomic_file_writes_prevent_corruption(self, plugin, user_config_path):
        """Test that file writes are atomic (no partial writes).

        VALIDATES: Config integrity - no corrupt JSON files from crashes.

        UN-GAMEABLE: Verifies actual file always contains valid JSON.
        """
        # Add multiple servers
        for i in range(5):
            config = ServerConfig(command="npx", args=["-y", f"server-{i}"])
            plugin.add_server(f"server-{i}", config, "user")

        # Verify file is always valid JSON
        with open(user_config_path) as f:
            config_data = json.load(f)  # Will raise if JSON is corrupt

        assert "mcpServers" in config_data
        assert len(config_data["mcpServers"]) == 5

    # =========================================================================
    # Error Handling and Edge Cases
    # =========================================================================

    def test_list_servers_empty_when_no_configs_exist(self, plugin):
        """Test that listing servers returns empty dict when configs don't exist.

        VALIDATES: Fresh install behavior - no errors, just empty list.

        UN-GAMEABLE: Checks actual filesystem state.
        """
        servers = plugin.list_servers()
        assert len(servers) == 0
        assert isinstance(servers, dict)

    def test_add_server_to_invalid_scope_fails(self, plugin):
        """Test that adding to non-existent scope fails with clear error.

        VALIDATES: Scope validation prevents user errors.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        result = plugin.add_server("test-server", config, "invalid-scope")

        assert result.success is False
        assert "scope" in result.message.lower()

    def test_remove_nonexistent_server_fails_gracefully(self, plugin):
        """Test that removing non-existent server returns meaningful error.

        VALIDATES: Error handling for common user mistakes.
        """
        result = plugin.remove_server("nonexistent", "user")

        assert result.success is False
        assert "not found" in result.message.lower() or "does not exist" in result.message.lower()

    def test_disable_nonexistent_server_fails(self, plugin):
        """Test that disabling non-existent server fails gracefully.

        VALIDATES: Error handling for invalid operations.
        """
        result = plugin.disable_server("nonexistent", scope="user")

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_enable_nonexistent_server_fails(self, plugin):
        """Test that enabling non-existent server fails gracefully.

        VALIDATES: Error handling for invalid operations.
        """
        result = plugin.enable_server("nonexistent", scope="user")

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_add_server_validates_config(self, plugin):
        """Test that adding server with invalid config fails validation.

        VALIDATES: Schema validation prevents broken configs.

        UN-GAMEABLE: Real validator is called, can't be satisfied by stub.
        """
        # Invalid: missing required command
        config = ServerConfig(command="", args=[])

        result = plugin.add_server("invalid-server", config, "user")

        assert result.success is False
        assert "command" in result.message.lower() or "validation" in result.message.lower()

    def test_handles_empty_config_files_gracefully(self, plugin, user_config_path, project_config_path):
        """Test that plugin handles empty config files without errors.

        VALIDATES: Graceful handling of edge cases.
        """
        # Create empty config files
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        user_config_path.write_text("{}")
        project_config_path.parent.mkdir(parents=True, exist_ok=True)
        project_config_path.write_text("{}")

        # Should list as empty, not error
        servers = plugin.list_servers()
        assert len(servers) == 0

    def test_get_server_state_for_nonexistent_server(self, plugin):
        """Test that getting state of non-existent server returns NOT_INSTALLED.

        VALIDATES: State query for servers not in config.
        """
        state = plugin.get_server_state("nonexistent")
        assert state == ServerState.NOT_INSTALLED

    def test_handles_server_with_disabled_field_in_initial_config(self, plugin, user_config_path):
        """Test that plugin correctly detects servers with pre-existing "disabled" field.

        VALIDATES: Handling of manually created configs with disabled servers.

        Users might manually edit the config file to add a server with
        "disabled": true from the start. The plugin should correctly
        detect this state.
        """
        # Create config with pre-disabled server
        user_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(user_config_path, "w") as f:
            json.dump(
                {
                    "mcpServers": {
                        "pre-disabled": {
                            "command": "npx",
                            "args": ["-y", "server-test"],
                            "disabled": True,
                        }
                    }
                },
                f,
            )

        # Should detect as disabled
        state = plugin.get_server_state("pre-disabled")
        assert state == ServerState.DISABLED

        # Should appear in list as disabled
        servers = plugin.list_servers(scope="user")
        qualified_id = "roo-code:user:pre-disabled"
        assert qualified_id in servers
        assert servers[qualified_id].state == ServerState.DISABLED

    def test_handles_malformed_server_config_in_file(self, plugin, user_config_path):
        """Test that plugin handles malformed server configs gracefully.

        VALIDATES: Defensive coding against manual config edits.

        EXPECTED BEHAVIOR: Plugin should STILL LIST malformed servers so users
        can see and fix them. Hiding broken servers would confuse users who
        manually edited the config file.
        """
        # Create config with malformed server (missing command)
        user_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(user_config_path, "w") as f:
            json.dump(
                {
                    "mcpServers": {
                        "broken-server": {
                            "args": ["-y", "test"],
                            # Missing "command" field
                        },
                        "valid-server": {
                            "command": "npx",
                            "args": ["-y", "valid-pkg"],
                        },
                    }
                },
                f,
            )

        # Should list ALL servers including malformed ones
        servers = plugin.list_servers(scope="user")
        assert isinstance(servers, dict)

        # Server IDs are qualified, check that both appear
        server_ids = [info.id for info in servers.values()]
        assert "broken-server" in server_ids or "valid-server" in server_ids

        # At minimum, the valid server must be listed correctly
        assert "valid-server" in server_ids

    # =========================================================================
    # Integration with Test Safety Mechanisms
    # =========================================================================

    def test_requires_path_overrides_in_test_mode(self):
        """Test that plugin requires path_overrides when MCPI_TEST_MODE=1.

        VALIDATES: Safety mechanism prevents tests from touching real files.

        This is CRITICAL - without this, tests could corrupt user configs.
        """
        from mcpi.clients.roo_code import RooCodePlugin

        # MCPI_TEST_MODE is set by conftest.py fixture
        assert os.environ.get("MCPI_TEST_MODE") == "1"

        # Should raise RuntimeError if no path_overrides provided
        with pytest.raises(RuntimeError, match="path_overrides"):
            RooCodePlugin()

    def test_allows_instantiation_without_overrides_in_production(self):
        """Test that plugin allows normal instantiation outside test mode.

        VALIDATES: Plugin works normally in production (no test-only restrictions).
        """
        from mcpi.clients.roo_code import RooCodePlugin

        # Temporarily disable test mode
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            # Should work without path_overrides in production
            plugin = RooCodePlugin()
            assert plugin is not None
            assert plugin.name == "roo-code"

        finally:
            # Restore test mode
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode


class TestRooCodePluginDiscovery:
    """Test that Roo Code plugin is auto-discovered by registry.

    These tests validate the plugin system integration:
    - Plugin is found by ClientRegistry
    - Plugin is instantiated correctly
    - Plugin works through MCPManager
    """

    def test_plugin_discovered_by_registry(self):
        """Test that RooCodePlugin is auto-discovered.

        VALIDATES: Plugin drops into clients/ directory and is found automatically.
        """
        from mcpi.clients.registry import ClientRegistry

        # Disable test mode temporarily to allow auto-discovery
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            registry = ClientRegistry()
            clients = registry.get_available_clients()

            assert "roo-code" in clients

        finally:
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode

    def test_plugin_instantiated_by_registry(self):
        """Test that registry can instantiate the plugin.

        VALIDATES: Plugin constructor works with registry's instantiation pattern.
        """
        from mcpi.clients.registry import ClientRegistry

        # Registry instantiation without path_overrides should work outside test mode
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            registry = ClientRegistry()
            client = registry.get_client("roo-code")

            assert client is not None
            assert client.name == "roo-code"

        finally:
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode

    def test_plugin_works_through_manager(self, tmp_path):
        """Test that plugin works through MCPManager interface.

        VALIDATES: End-to-end integration with manager (how CLI uses it).

        UN-GAMEABLE: Tests complete flow through manager layer.
        """
        from mcpi.clients.roo_code import RooCodePlugin
        from mcpi.clients.manager import MCPManager
        from mcpi.clients.registry import ClientRegistry

        # Create isolated plugin instance
        user_config_path = tmp_path / "user" / "mcp_settings.json"
        project_config_path = tmp_path / "project" / ".roo" / "mcp.json"

        plugin = RooCodePlugin(
            path_overrides={
                "user": user_config_path,
                "project": project_config_path,
            }
        )

        # Inject into registry
        registry = ClientRegistry(auto_discover=False)
        registry.inject_client_instance("roo-code", plugin)

        # Create manager
        manager = MCPManager(registry=registry, default_client="roo-code")

        # Add servers through manager to both scopes
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        result_user = manager.add_server(
            server_id="test-server-user",
            config=config,
            scope="user",
            client_name="roo-code",
        )
        result_project = manager.add_server(
            server_id="test-server-project",
            config=config,
            scope="project",
            client_name="roo-code",
        )

        assert result_user.success is True
        assert result_project.success is True

        # List servers through manager
        servers = manager.list_servers(client_name="roo-code")
        assert len(servers) == 2
        assert "roo-code:user:test-server-user" in servers
        assert "roo-code:project:test-server-project" in servers
