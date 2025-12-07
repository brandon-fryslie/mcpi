"""Functional tests for Cursor MCP client plugin.

These tests validate REAL user workflows for Cursor IDE:
- Server installation to BOTH user-level and project-level scopes
- Scope priority: project overrides user when same server exists in both
- Enable/disable via file-move mechanism (both scopes)
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


class TestCursorPlugin:
    """Functional tests for CursorPlugin.

    These tests validate end-to-end user workflows:
    1. User installs server to user scope → appears in user config → shows in list
    2. User installs server to project scope → appears in project config → shows in list
    3. Same server in both scopes → project scope wins (lower priority number)
    4. User disables server → config moved to disabled file → shows DISABLED
    5. Config persists correctly across operations

    UN-GAMEABLE because:
    - Uses REAL file I/O (temp directories, not mocks)
    - Verifies actual file contents on disk
    - Tests complete user journey (not implementation details)
    - Tests scope priority by checking which config is returned
    """

    @pytest.fixture
    def plugin(self, tmp_path):
        """Create CursorPlugin with isolated test directory.

        Uses path_overrides to redirect all file operations to tmp_path,
        preventing any modification of real user files.

        Includes paths for BOTH scopes (user and project) and their disabled variants.
        """
        from mcpi.clients.cursor import CursorPlugin

        # User scope paths
        user_config_path = tmp_path / "user" / "mcp.json"
        user_disabled_path = tmp_path / "user" / "mcp_disabled.json"

        # Project scope paths
        project_config_path = tmp_path / "project" / ".cursor" / "mcp.json"
        project_disabled_path = tmp_path / "project" / ".cursor" / "mcp_disabled.json"

        path_overrides = {
            "user": user_config_path,
            "user-disabled": user_disabled_path,
            "project": project_config_path,
            "project-disabled": project_disabled_path,
        }

        return CursorPlugin(path_overrides=path_overrides)

    @pytest.fixture
    def user_config_path(self, tmp_path):
        """Get the user scope config path."""
        return tmp_path / "user" / "mcp.json"

    @pytest.fixture
    def user_disabled_path(self, tmp_path):
        """Get the user scope disabled config path."""
        return tmp_path / "user" / "mcp_disabled.json"

    @pytest.fixture
    def project_config_path(self, tmp_path):
        """Get the project scope config path."""
        return tmp_path / "project" / ".cursor" / "mcp.json"

    @pytest.fixture
    def project_disabled_path(self, tmp_path):
        """Get the project scope disabled config path."""
        return tmp_path / "project" / ".cursor" / "mcp_disabled.json"

    # =========================================================================
    # Plugin Identity and Initialization
    # =========================================================================

    def test_get_name(self, plugin):
        """Test that plugin returns correct name.

        VALIDATES: Plugin discovery and identification in multi-client environment.
        """
        assert plugin.name == "cursor"

    def test_initialize_scopes_creates_two_scopes(self, plugin):
        """Test that plugin initializes exactly two scopes.

        VALIDATES: Cursor's 2-scope model (user + project).
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
        qualified_id = "cursor:user:filesystem"
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

        qualified_id = "cursor:user:filesystem"
        server_info = servers[qualified_id]

        assert server_info.id == "filesystem"
        assert server_info.client == "cursor"
        assert server_info.scope == "user"
        assert server_info.state == ServerState.ENABLED
        assert server_info.config is not None

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
        qualified_id = "cursor:project:filesystem"
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

        qualified_id = "cursor:project:filesystem"
        server_info = servers[qualified_id]

        assert server_info.id == "filesystem"
        assert server_info.client == "cursor"
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
        assert "cursor:user:duplicated" in servers
        assert "cursor:project:duplicated" in servers

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

        user_server = servers["cursor:user:duplicated"]
        project_server = servers["cursor:project:duplicated"]

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
        assert "cursor:user:only-user" in user_servers
        assert "cursor:user:in-both" in user_servers

        # List only project scope
        project_servers = plugin.list_servers(scope="project")
        assert len(project_servers) == 2
        assert "cursor:project:only-project" in project_servers
        assert "cursor:project:in-both" in project_servers

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
    # Enable/Disable - User Scope
    # =========================================================================

    def test_disable_server_in_user_scope_moves_to_disabled_file(
        self, plugin, user_config_path, user_disabled_path
    ):
        """Test that disabling user-scope server moves config to disabled file.

        VALIDATES: FileMoveEnableDisableHandler for user scope.

        UN-GAMEABLE: Checks actual file operations.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        # Disable server
        result = plugin.disable_server("test-server", scope="user")

        assert result.success is True

        # Verify moved to disabled file
        assert user_disabled_path.exists()
        with open(user_disabled_path) as f:
            disabled_config = json.load(f)
        assert "test-server" in disabled_config.get("mcpServers", {})

        # Verify removed from active file
        with open(user_config_path) as f:
            active_config = json.load(f)
        assert "test-server" not in active_config.get("mcpServers", {})

    def test_disabled_server_in_user_scope_shows_disabled_state(self, plugin):
        """Test that disabled user-scope server shows DISABLED state.

        VALIDATES: State detection for user scope.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server", scope="user")

        state = plugin.get_server_state("test-server")
        assert state == ServerState.DISABLED

    def test_enable_disabled_server_in_user_scope(self, plugin, user_config_path):
        """Test re-enabling disabled user-scope server.

        VALIDATES: Round-trip disable → enable for user scope.

        UN-GAMEABLE: Verifies config moved back to active file.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server", scope="user")
        result = plugin.enable_server("test-server", scope="user")

        assert result.success is True

        # Verify back in active file
        with open(user_config_path) as f:
            active_config = json.load(f)
        assert "test-server" in active_config.get("mcpServers", {})

        # Verify state is ENABLED
        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

    # =========================================================================
    # Enable/Disable - Project Scope
    # =========================================================================

    def test_disable_server_in_project_scope_moves_to_disabled_file(
        self, plugin, project_config_path, project_disabled_path
    ):
        """Test that disabling project-scope server moves config to disabled file.

        VALIDATES: FileMoveEnableDisableHandler for project scope.

        UN-GAMEABLE: Checks actual file operations.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "project")

        # Disable server
        result = plugin.disable_server("test-server", scope="project")

        assert result.success is True

        # Verify moved to disabled file
        assert project_disabled_path.exists()
        with open(project_disabled_path) as f:
            disabled_config = json.load(f)
        assert "test-server" in disabled_config.get("mcpServers", {})

        # Verify removed from active file
        with open(project_config_path) as f:
            active_config = json.load(f)
        assert "test-server" not in active_config.get("mcpServers", {})

    def test_disabled_server_in_project_scope_shows_disabled_state(self, plugin):
        """Test that disabled project-scope server shows DISABLED state.

        VALIDATES: State detection for project scope.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "project")
        plugin.disable_server("test-server", scope="project")

        state = plugin.get_server_state("test-server")
        assert state == ServerState.DISABLED

    def test_enable_disabled_server_in_project_scope(self, plugin, project_config_path):
        """Test re-enabling disabled project-scope server.

        VALIDATES: Round-trip disable → enable for project scope.

        UN-GAMEABLE: Verifies config moved back to active file.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "project")
        plugin.disable_server("test-server", scope="project")
        result = plugin.enable_server("test-server", scope="project")

        assert result.success is True

        # Verify back in active file
        with open(project_config_path) as f:
            active_config = json.load(f)
        assert "test-server" in active_config.get("mcpServers", {})

        # Verify state is ENABLED
        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

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
        user_server = servers["cursor:user:duplicated"]
        project_server = servers["cursor:project:duplicated"]

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

        VALIDATES: Config format compatibility with Cursor.

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
        from mcpi.clients.cursor import CursorPlugin

        user_config_path = tmp_path / "user" / "mcp.json"
        project_config_path = tmp_path / "project" / ".cursor" / "mcp.json"

        path_overrides = {
            "user": user_config_path,
            "project": project_config_path,
        }

        # First instance: add servers to both scopes
        plugin1 = CursorPlugin(path_overrides=path_overrides)
        user_config = ServerConfig(command="npx", args=["-y", "user-server"])
        project_config = ServerConfig(command="npx", args=["-y", "project-server"])
        plugin1.add_server("user-server", user_config, "user")
        plugin1.add_server("project-server", project_config, "project")

        # Second instance: verify both servers exist
        plugin2 = CursorPlugin(path_overrides=path_overrides)
        servers = plugin2.list_servers()

        assert "cursor:user:user-server" in servers
        assert "cursor:project:project-server" in servers

    def test_disabled_state_persists_across_plugin_instances(self, tmp_path):
        """Test that disabled state persists across restarts in both scopes.

        VALIDATES: Disabled servers stay disabled after restart.

        UN-GAMEABLE: Two plugin instances, verifies persistence via files.
        """
        from mcpi.clients.cursor import CursorPlugin

        user_config_path = tmp_path / "user" / "mcp.json"
        project_config_path = tmp_path / "project" / ".cursor" / "mcp.json"

        path_overrides = {
            "user": user_config_path,
            "project": project_config_path,
        }

        # First instance: add and disable servers in both scopes
        plugin1 = CursorPlugin(path_overrides=path_overrides)
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin1.add_server("user-disabled", config, "user")
        plugin1.add_server("project-disabled", config, "project")
        plugin1.disable_server("user-disabled", scope="user")
        plugin1.disable_server("project-disabled", scope="project")

        # Second instance: verify both still disabled
        plugin2 = CursorPlugin(path_overrides=path_overrides)
        user_state = plugin2.get_server_state("user-disabled")
        project_state = plugin2.get_server_state("project-disabled")

        assert user_state == ServerState.DISABLED
        assert project_state == ServerState.DISABLED

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

    def test_update_server_modifies_config(self, plugin):
        """Test that updating server changes its configuration.

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
        qualified_id = "cursor:user:test-server"
        server_info = servers[qualified_id]

        assert server_info.config["command"] == "uvx"
        assert server_info.config["args"] == ["new-package"]

    # =========================================================================
    # Integration with Test Safety Mechanisms
    # =========================================================================

    def test_requires_path_overrides_in_test_mode(self):
        """Test that plugin requires path_overrides when MCPI_TEST_MODE=1.

        VALIDATES: Safety mechanism prevents tests from touching real files.

        This is CRITICAL - without this, tests could corrupt user configs.
        """
        from mcpi.clients.cursor import CursorPlugin

        # MCPI_TEST_MODE is set by conftest.py fixture
        assert os.environ.get("MCPI_TEST_MODE") == "1"

        # Should raise RuntimeError if no path_overrides provided
        with pytest.raises(RuntimeError, match="path_overrides"):
            CursorPlugin()

    def test_allows_instantiation_without_overrides_in_production(self):
        """Test that plugin allows normal instantiation outside test mode.

        VALIDATES: Plugin works normally in production (no test-only restrictions).
        """
        from mcpi.clients.cursor import CursorPlugin

        # Temporarily disable test mode
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            # Should work without path_overrides in production
            plugin = CursorPlugin()
            assert plugin is not None
            assert plugin.name == "cursor"

        finally:
            # Restore test mode
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode


class TestCursorPluginDiscovery:
    """Test that Cursor plugin is auto-discovered by registry.

    These tests validate the plugin system integration:
    - Plugin is found by ClientRegistry
    - Plugin is instantiated correctly
    - Plugin works through MCPManager
    """

    def test_plugin_discovered_by_registry(self):
        """Test that CursorPlugin is auto-discovered.

        VALIDATES: Plugin drops into clients/ directory and is found automatically.
        """
        from mcpi.clients.registry import ClientRegistry

        # Disable test mode temporarily to allow auto-discovery
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            registry = ClientRegistry()
            clients = registry.get_available_clients()

            assert "cursor" in clients

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
            client = registry.get_client("cursor")

            assert client is not None
            assert client.name == "cursor"

        finally:
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode

    def test_plugin_works_through_manager(self, tmp_path):
        """Test that plugin works through MCPManager interface.

        VALIDATES: End-to-end integration with manager (how CLI uses it).

        UN-GAMEABLE: Tests complete flow through manager layer.
        """
        from mcpi.clients.cursor import CursorPlugin
        from mcpi.clients.manager import MCPManager
        from mcpi.clients.registry import ClientRegistry

        # Create isolated plugin instance
        user_config_path = tmp_path / "user" / "mcp.json"
        project_config_path = tmp_path / "project" / ".cursor" / "mcp.json"

        plugin = CursorPlugin(
            path_overrides={
                "user": user_config_path,
                "project": project_config_path,
            }
        )

        # Inject into registry
        registry = ClientRegistry(auto_discover=False)
        registry.inject_client_instance("cursor", plugin)

        # Create manager
        manager = MCPManager(registry=registry, default_client="cursor")

        # Add servers through manager to both scopes
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        result_user = manager.add_server(
            server_id="test-server-user",
            config=config,
            scope="user",
            client_name="cursor",
        )
        result_project = manager.add_server(
            server_id="test-server-project",
            config=config,
            scope="project",
            client_name="cursor",
        )

        assert result_user.success is True
        assert result_project.success is True

        # List servers through manager
        servers = manager.list_servers(client_name="cursor")
        assert len(servers) == 2
        assert "cursor:user:test-server-user" in servers
        assert "cursor:project:test-server-project" in servers
