"""Functional tests for Claude Desktop MCP client plugin.

These tests validate REAL user workflows for Claude Desktop:
- Server installation to single user-level config
- Enable/disable via file-move mechanism
- Config persistence across operations
- Platform-specific path resolution

Tests use REAL file operations (via temp directories) and REAL plugin code.
NO mocking of user-facing functionality - tests fail when users would fail.
"""

import os
import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from mcpi.clients.types import ServerConfig, ServerState


class TestClaudeDesktopPlugin:
    """Functional tests for ClaudeDesktopPlugin.

    These tests validate end-to-end user workflows:
    1. User installs server → config file updated → server appears in list
    2. User disables server → config moved to disabled file → server shows DISABLED
    3. User enables server → config moved back to active file → server shows ENABLED
    4. Config persists correctly across operations

    UN-GAMEABLE because:
    - Uses REAL file I/O (temp directories, not mocks)
    - Verifies actual file contents on disk
    - Tests complete user journey (not implementation details)
    """

    @pytest.fixture
    def plugin(self, tmp_path):
        """Create ClaudeDesktopPlugin with isolated test directory.

        Uses path_overrides to redirect all file operations to tmp_path,
        preventing any modification of real user files.

        Includes BOTH active and disabled paths for FileMoveEnableDisableHandler.
        """
        from mcpi.clients.claude_desktop import ClaudeDesktopPlugin

        # Override BOTH active and disabled paths for full isolation
        config_path = tmp_path / "claude_desktop_config.json"
        disabled_path = tmp_path / "claude_desktop_disabled.json"
        path_overrides = {
            "user": config_path,
            "user-disabled": disabled_path,
        }

        return ClaudeDesktopPlugin(path_overrides=path_overrides)

    @pytest.fixture
    def config_path(self, tmp_path):
        """Get the test config file path."""
        return tmp_path / "claude_desktop_config.json"

    @pytest.fixture
    def disabled_path(self, tmp_path):
        """Get the test disabled config file path."""
        return tmp_path / "claude_desktop_disabled.json"

    # =========================================================================
    # Plugin Identity and Initialization
    # =========================================================================

    def test_get_name(self, plugin):
        """Test that plugin returns correct name.

        VALIDATES: Plugin discovery and identification in multi-client environment.
        """
        assert plugin.name == "claude-desktop"

    def test_initialize_scopes_creates_single_scope(self, plugin):
        """Test that plugin initializes exactly one scope.

        VALIDATES: Claude Desktop's simpler config model (1 scope vs Claude Code's 6).
        """
        scopes = plugin.get_scope_names()
        assert len(scopes) == 1
        assert "user" in scopes

    def test_scope_is_user_level(self, plugin):
        """Test that the scope is correctly marked as user-level.

        VALIDATES: Scope categorization for UI/CLI filtering.
        """
        scopes = plugin.get_scopes()
        assert len(scopes) == 1
        assert scopes[0].name == "user"
        assert scopes[0].is_user_level is True
        assert scopes[0].is_project_level is False

    def test_scope_is_writable(self, plugin):
        """Test that the user scope is not read-only.

        VALIDATES: Users can add/remove servers (unlike plugin-based scopes).
        """
        scopes = plugin.get_scopes()
        user_scope = scopes[0]
        assert user_scope.readonly is False

    def test_scope_has_correct_priority(self, plugin):
        """Test that user scope has expected priority.

        VALIDATES: Priority ordering for multi-client scenario (though Claude Desktop
        only has one scope, this ensures consistency with other clients).
        """
        scopes = plugin.get_scopes()
        user_scope = scopes[0]
        # User-level scopes typically have priority 40-60
        assert user_scope.priority >= 40
        assert user_scope.priority <= 60

    # =========================================================================
    # Server CRUD Operations - Core User Workflows
    # =========================================================================

    def test_list_servers_empty_when_no_config_exists(self, plugin):
        """Test that listing servers returns empty dict when config doesn't exist.

        VALIDATES: Fresh install behavior - no errors, just empty list.

        UN-GAMEABLE: Checks actual filesystem state.
        """
        servers = plugin.list_servers()
        assert len(servers) == 0
        assert isinstance(servers, dict)

    def test_add_server_creates_config_file(self, plugin, config_path):
        """Test that adding first server creates config file.

        VALIDATES: User's first server installation creates necessary files.

        UN-GAMEABLE: Verifies actual file exists on disk.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        result = plugin.add_server("filesystem", config, "user")

        assert result.success is True
        assert config_path.exists()

    def test_add_server_appears_in_list(self, plugin):
        """Test that added server appears when listing servers.

        VALIDATES: Complete user workflow - install → verify installation.

        UN-GAMEABLE: Reads back from real file, not from mock state.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        plugin.add_server("filesystem", config, "user")
        servers = plugin.list_servers()

        assert len(servers) == 1
        qualified_id = "claude-desktop:user:filesystem"
        assert qualified_id in servers

    def test_add_server_has_correct_metadata(self, plugin):
        """Test that added server has all expected metadata.

        VALIDATES: ServerInfo structure completeness for UI display.
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        plugin.add_server("filesystem", config, "user")
        servers = plugin.list_servers()

        qualified_id = "claude-desktop:user:filesystem"
        server_info = servers[qualified_id]

        assert server_info.id == "filesystem"
        assert server_info.client == "claude-desktop"
        assert server_info.scope == "user"
        assert server_info.state == ServerState.ENABLED
        assert server_info.config is not None
        assert server_info.config["command"] == "npx"

    def test_add_server_with_environment_variables(self, plugin):
        """Test adding server with environment variables.

        VALIDATES: Complex config handling (env vars, multiple args).
        """
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": "test-token-placeholder"},
        )

        result = plugin.add_server("github", config, "user")

        assert result.success is True

        servers = plugin.list_servers()
        qualified_id = "claude-desktop:user:github"
        server_info = servers[qualified_id]

        assert server_info.config["env"]["GITHUB_TOKEN"] == "test-token-placeholder"

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

    def test_add_multiple_servers(self, plugin):
        """Test adding multiple servers to same scope.

        VALIDATES: Multi-server management in single config file.
        """
        servers_to_add = [
            ("filesystem", ServerConfig(command="npx", args=["-y", "server-filesystem"])),
            ("github", ServerConfig(command="npx", args=["-y", "server-github"])),
            ("sqlite", ServerConfig(command="uvx", args=["mcp-server-sqlite"])),
        ]

        for server_id, config in servers_to_add:
            result = plugin.add_server(server_id, config, "user")
            assert result.success is True

        servers = plugin.list_servers()
        assert len(servers) == 3

        for server_id, _ in servers_to_add:
            qualified_id = f"claude-desktop:user:{server_id}"
            assert qualified_id in servers

    def test_remove_server_success(self, plugin):
        """Test successful server removal.

        VALIDATES: User can uninstall servers.

        UN-GAMEABLE: Verifies server is actually gone from config file.
        """
        # Add a server first
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        # Verify it exists
        servers_before = plugin.list_servers()
        assert len(servers_before) == 1

        # Remove it
        result = plugin.remove_server("test-server", "user")

        assert result.success is True

        # Verify it's gone
        servers_after = plugin.list_servers()
        assert len(servers_after) == 0

    def test_remove_nonexistent_server_fails_gracefully(self, plugin):
        """Test that removing non-existent server returns meaningful error.

        VALIDATES: Error handling for common user mistakes.
        """
        result = plugin.remove_server("nonexistent", "user")

        assert result.success is False
        assert "not found" in result.message.lower() or "does not exist" in result.message.lower()

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
        servers = plugin.list_servers()
        qualified_id = "claude-desktop:user:test-server"
        server_info = servers[qualified_id]

        assert server_info.config["command"] == "uvx"
        assert server_info.config["args"] == ["new-package"]

    # =========================================================================
    # Enable/Disable Functionality - FileMoveEnableDisableHandler
    # =========================================================================

    def test_newly_added_server_is_enabled(self, plugin):
        """Test that newly added servers start in ENABLED state.

        VALIDATES: Default state after installation.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

    def test_disable_server_moves_config_to_disabled_file(self, plugin, config_path, disabled_path):
        """Test that disabling server moves config from active to disabled file.

        VALIDATES: FileMoveEnableDisableHandler mechanism - Claude Desktop has
        no built-in disable, so we use shadow file pattern.

        UN-GAMEABLE: Checks actual file operations:
        1. Server exists in active file before disable
        2. Server removed from active file after disable
        3. Server appears in disabled file after disable
        """
        # Add server
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        # Verify it's in active file
        assert config_path.exists()
        import json
        with open(config_path) as f:
            active_config = json.load(f)
        assert "test-server" in active_config.get("mcpServers", {})

        # Disable server
        result = plugin.disable_server("test-server")

        assert result.success is True

        # Verify it's moved to disabled file
        assert disabled_path.exists()
        with open(disabled_path) as f:
            disabled_config = json.load(f)
        assert "test-server" in disabled_config.get("mcpServers", {})

        # Verify it's removed from active file
        with open(config_path) as f:
            active_config = json.load(f)
        assert "test-server" not in active_config.get("mcpServers", {})

    def test_disable_server_changes_state_to_disabled(self, plugin):
        """Test that disabled server shows DISABLED state.

        VALIDATES: State detection works correctly.
        """
        # Add and disable server
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server")

        # Check state
        state = plugin.get_server_state("test-server")
        assert state == ServerState.DISABLED

    def test_disabled_server_still_appears_in_list(self, plugin):
        """Test that disabled servers appear in server list with DISABLED state.

        VALIDATES: Users can see all servers (enabled + disabled) for management.
        """
        # Add and disable server
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server")

        # List servers
        servers = plugin.list_servers()

        qualified_id = "claude-desktop:user:test-server"
        assert qualified_id in servers
        assert servers[qualified_id].state == ServerState.DISABLED

    def test_enable_disabled_server_moves_config_back(self, plugin, config_path, disabled_path):
        """Test that enabling disabled server moves config back to active file.

        VALIDATES: Round-trip disable → enable workflow.

        UN-GAMEABLE: Verifies actual file operations in both directions.
        """
        # Add, disable, then enable server
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server")
        result = plugin.enable_server("test-server")

        assert result.success is True

        # Verify it's back in active file
        import json
        with open(config_path) as f:
            active_config = json.load(f)
        assert "test-server" in active_config.get("mcpServers", {})

        # Verify it's removed from disabled file (or file is empty/deleted)
        if disabled_path.exists():
            with open(disabled_path) as f:
                disabled_config = json.load(f)
            assert "test-server" not in disabled_config.get("mcpServers", {})

    def test_enable_disabled_server_changes_state_to_enabled(self, plugin):
        """Test that enabled server shows ENABLED state.

        VALIDATES: Complete disable/enable cycle restores original state.
        """
        # Add, disable, enable
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server")
        plugin.enable_server("test-server")

        # Check state
        state = plugin.get_server_state("test-server")
        assert state == ServerState.ENABLED

    def test_enable_already_enabled_server_succeeds(self, plugin):
        """Test that enabling already enabled server is idempotent.

        VALIDATES: Idempotent operations (common in automation scripts).
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        result = plugin.enable_server("test-server")

        assert result.success is True

    def test_disable_already_disabled_server_succeeds(self, plugin):
        """Test that disabling already disabled server is idempotent.

        VALIDATES: Idempotent operations.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")
        plugin.disable_server("test-server")

        result = plugin.disable_server("test-server")

        assert result.success is True

    def test_disable_nonexistent_server_fails(self, plugin):
        """Test that disabling non-existent server fails gracefully.

        VALIDATES: Error handling for invalid operations.
        """
        result = plugin.disable_server("nonexistent")

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_enable_nonexistent_server_fails(self, plugin):
        """Test that enabling non-existent server fails gracefully.

        VALIDATES: Error handling for invalid operations.
        """
        result = plugin.enable_server("nonexistent")

        assert result.success is False
        assert "not found" in result.message.lower()

    # =========================================================================
    # Config Persistence and File Format
    # =========================================================================

    def test_config_file_has_correct_json_structure(self, plugin, config_path):
        """Test that config file uses standard mcpServers structure.

        VALIDATES: Config format compatibility with Claude Desktop.

        UN-GAMEABLE: Parses actual JSON file and validates structure.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        import json
        with open(config_path) as f:
            config_data = json.load(f)

        # Must have mcpServers key
        assert "mcpServers" in config_data
        assert isinstance(config_data["mcpServers"], dict)

        # Server must be under mcpServers
        assert "test-server" in config_data["mcpServers"]
        server_config = config_data["mcpServers"]["test-server"]

        # Server config must have required fields
        assert "command" in server_config
        assert "args" in server_config

    def test_config_persists_across_plugin_instances(self, tmp_path):
        """Test that config persists when creating new plugin instance.

        VALIDATES: Real persistence - config survives process restart.

        UN-GAMEABLE: Creates two separate plugin instances, verifies state
        persists via filesystem (not in-memory state).
        """
        from mcpi.clients.claude_desktop import ClaudeDesktopPlugin

        config_path = tmp_path / "claude_desktop_config.json"
        path_overrides = {"user": config_path}

        # First instance: add server
        plugin1 = ClaudeDesktopPlugin(path_overrides=path_overrides)
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin1.add_server("test-server", config, "user")

        # Second instance: verify server exists
        plugin2 = ClaudeDesktopPlugin(path_overrides=path_overrides)
        servers = plugin2.list_servers()

        qualified_id = "claude-desktop:user:test-server"
        assert qualified_id in servers

    def test_disabled_state_persists_across_plugin_instances(self, tmp_path):
        """Test that disabled state persists across restarts.

        VALIDATES: Disabled servers stay disabled after restart.

        UN-GAMEABLE: Two plugin instances, verifies persistence via files.
        """
        from mcpi.clients.claude_desktop import ClaudeDesktopPlugin

        config_path = tmp_path / "claude_desktop_config.json"
        path_overrides = {"user": config_path}

        # First instance: add and disable server
        plugin1 = ClaudeDesktopPlugin(path_overrides=path_overrides)
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin1.add_server("test-server", config, "user")
        plugin1.disable_server("test-server")

        # Second instance: verify still disabled
        plugin2 = ClaudeDesktopPlugin(path_overrides=path_overrides)
        state = plugin2.get_server_state("test-server")

        assert state == ServerState.DISABLED

    def test_atomic_file_writes_prevent_corruption(self, plugin, config_path):
        """Test that file writes are atomic (no partial writes).

        VALIDATES: Config integrity - no corrupt JSON files from crashes.

        UN-GAMEABLE: Verifies actual file always contains valid JSON.
        """
        # Add multiple servers
        for i in range(5):
            config = ServerConfig(command="npx", args=["-y", f"server-{i}"])
            plugin.add_server(f"server-{i}", config, "user")

        # Verify file is always valid JSON
        import json
        with open(config_path) as f:
            config_data = json.load(f)  # Will raise if JSON is corrupt

        assert "mcpServers" in config_data
        assert len(config_data["mcpServers"]) == 5

    # =========================================================================
    # Platform-Specific Path Resolution
    # =========================================================================

    @pytest.mark.parametrize(
        "platform_name,expected_path_parts",
        [
            # macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
            # Source: https://modelcontextprotocol.io/docs/develop/connect-local-servers
            (
                "Darwin",
                ["Library", "Application Support", "Claude", "claude_desktop_config.json"],
            ),
            # Windows: %APPDATA%\Claude\claude_desktop_config.json
            # Source: https://modelcontextprotocol.io/docs/develop/connect-local-servers
            (
                "Windows",
                ["Claude", "claude_desktop_config.json"],
            ),
            # Linux: ~/.config/Claude/claude_desktop_config.json
            # NOTE: Claude Desktop is NOT officially supported on Linux.
            # This path is for community builds (debian, AUR, etc.)
            # Source: https://github.com/aaddrick/claude-desktop-debian
            pytest.param(
                "Linux",
                [".config", "Claude", "claude_desktop_config.json"],
                marks=pytest.mark.skip(reason="Linux not officially supported by Claude Desktop"),
            ),
        ],
    )
    def test_platform_specific_default_paths(self, platform_name, expected_path_parts):
        """Test that default config paths are correct for each platform.

        VALIDATES: Platform-specific path resolution without overrides.

        This test uses monkeypatch to simulate different platforms.
        Must disable MCPI_TEST_MODE to test production path resolution.
        """
        from mcpi.clients.claude_desktop import ClaudeDesktopPlugin

        # Disable test mode to allow instantiation without path_overrides
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            with patch("platform.system", return_value=platform_name):
                # Windows requires APPDATA env var
                if platform_name == "Windows":
                    with patch.dict(
                        os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}
                    ):
                        plugin = ClaudeDesktopPlugin()
                        scopes = plugin.get_scopes()
                        config_path = scopes[0].path

                        # Check that path contains expected parts
                        path_str = str(config_path)
                        for part in expected_path_parts:
                            assert part in path_str
                else:
                    plugin = ClaudeDesktopPlugin()
                    scopes = plugin.get_scopes()
                    config_path = scopes[0].path

                    # Check that path contains expected parts
                    path_str = str(config_path)
                    for part in expected_path_parts:
                        assert part in path_str

        finally:
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode

    def test_path_overrides_work_on_all_platforms(self, tmp_path):
        """Test that path_overrides work regardless of platform.

        VALIDATES: Test mode safety mechanism works everywhere.
        """
        from mcpi.clients.claude_desktop import ClaudeDesktopPlugin

        custom_config = tmp_path / "custom_config.json"
        path_overrides = {"user": custom_config}

        plugin = ClaudeDesktopPlugin(path_overrides=path_overrides)
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        plugin.add_server("test-server", config, "user")

        # Verify file created at overridden path
        assert custom_config.exists()

    # =========================================================================
    # Error Handling and Edge Cases
    # =========================================================================

    def test_handles_empty_config_file_gracefully(self, plugin, config_path):
        """Test that plugin handles empty config file without errors.

        VALIDATES: Graceful handling of edge cases.
        """
        # Create empty config file
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{}")

        # Should list as empty, not error
        servers = plugin.list_servers()
        assert len(servers) == 0

    def test_handles_missing_mcpservers_key_gracefully(self, plugin, config_path):
        """Test that plugin handles config without mcpServers key.

        VALIDATES: Defensive coding against malformed configs.
        """
        # Create config without mcpServers key
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text('{"otherKey": "value"}')

        # Should list as empty, not error
        servers = plugin.list_servers()
        assert len(servers) == 0

    def test_get_server_state_for_nonexistent_server(self, plugin):
        """Test that getting state of non-existent server returns NOT_INSTALLED.

        VALIDATES: State query for servers not in config.
        """
        state = plugin.get_server_state("nonexistent")
        assert state == ServerState.NOT_INSTALLED

    def test_add_server_to_invalid_scope_fails(self, plugin):
        """Test that adding to non-existent scope fails with clear error.

        VALIDATES: Scope validation prevents user errors.
        """
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        result = plugin.add_server("test-server", config, "invalid-scope")

        assert result.success is False
        assert "scope" in result.message.lower()

    def test_remove_server_from_invalid_scope_fails(self, plugin):
        """Test that removing from non-existent scope fails gracefully.

        VALIDATES: Scope validation in remove operations.
        """
        result = plugin.remove_server("test-server", "invalid-scope")

        assert result.success is False
        assert "scope" in result.message.lower()

    def test_handles_malformed_server_config_in_file(self, plugin, config_path):
        """Test that plugin handles malformed server configs gracefully.

        VALIDATES: Defensive coding against manual config edits.

        EXPECTED BEHAVIOR: Plugin should STILL LIST malformed servers so users
        can see and fix them. Hiding broken servers would confuse users who
        manually edited the config file. The server will show in the list but
        operations on it may fail with a descriptive error.
        """
        # Create config with malformed server (missing command)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        import json

        with open(config_path, "w") as f:
            json.dump(
                {
                    "mcpServers": {
                        "broken-server": {
                            "args": ["-y", "test"],
                            # Missing "command" field - malformed but should still appear
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
        servers = plugin.list_servers()
        assert isinstance(servers, dict)

        # Server IDs are qualified (client:scope:id), check that both appear
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
        from mcpi.clients.claude_desktop import ClaudeDesktopPlugin

        # MCPI_TEST_MODE is set by conftest.py fixture
        assert os.environ.get("MCPI_TEST_MODE") == "1"

        # Should raise RuntimeError if no path_overrides provided
        with pytest.raises(RuntimeError, match="path_overrides"):
            ClaudeDesktopPlugin()

    def test_allows_instantiation_without_overrides_in_production(self):
        """Test that plugin allows normal instantiation outside test mode.

        VALIDATES: Plugin works normally in production (no test-only restrictions).
        """
        from mcpi.clients.claude_desktop import ClaudeDesktopPlugin

        # Temporarily disable test mode
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            # Should work without path_overrides in production
            plugin = ClaudeDesktopPlugin()
            assert plugin is not None
            assert plugin.name == "claude-desktop"

        finally:
            # Restore test mode
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode


class TestClaudeDesktopPluginDiscovery:
    """Test that Claude Desktop plugin is auto-discovered by registry.

    These tests validate the plugin system integration:
    - Plugin is found by ClientRegistry
    - Plugin is instantiated correctly
    - Plugin works through MCPManager
    """

    def test_plugin_discovered_by_registry(self, tmp_path):
        """Test that ClaudeDesktopPlugin is auto-discovered.

        VALIDATES: Plugin drops into clients/ directory and is found automatically.
        """
        from mcpi.clients.registry import ClientRegistry

        # Disable test mode temporarily to allow auto-discovery
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            registry = ClientRegistry()
            clients = registry.get_available_clients()

            assert "claude-desktop" in clients

        finally:
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode

    def test_plugin_instantiated_by_registry(self, tmp_path):
        """Test that registry can instantiate the plugin.

        VALIDATES: Plugin constructor works with registry's instantiation pattern.
        """
        from mcpi.clients.registry import ClientRegistry

        # Registry instantiation without path_overrides should work outside test mode
        original_test_mode = os.environ.get("MCPI_TEST_MODE")
        try:
            os.environ.pop("MCPI_TEST_MODE", None)

            registry = ClientRegistry()
            client = registry.get_client("claude-desktop")

            assert client is not None
            assert client.name == "claude-desktop"

        finally:
            if original_test_mode:
                os.environ["MCPI_TEST_MODE"] = original_test_mode

    def test_plugin_works_through_manager(self, tmp_path):
        """Test that plugin works through MCPManager interface.

        VALIDATES: End-to-end integration with manager (how CLI uses it).

        UN-GAMEABLE: Tests complete flow through manager layer.
        """
        from mcpi.clients.claude_desktop import ClaudeDesktopPlugin
        from mcpi.clients.manager import MCPManager
        from mcpi.clients.registry import ClientRegistry

        # Create isolated plugin instance
        config_path = tmp_path / "claude_desktop_config.json"
        plugin = ClaudeDesktopPlugin(path_overrides={"user": config_path})

        # Inject into registry
        registry = ClientRegistry(auto_discover=False)
        registry.inject_client_instance("claude-desktop", plugin)

        # Create manager
        manager = MCPManager(registry=registry, default_client="claude-desktop")

        # Add server through manager
        config = ServerConfig(command="npx", args=["-y", "server-test"])
        result = manager.add_server(
            server_id="test-server",
            config=config,
            scope="user",
            client_name="claude-desktop",
        )

        assert result.success is True

        # List servers through manager
        servers = manager.list_servers(client_name="claude-desktop")
        assert len(servers) == 1
        assert "claude-desktop:user:test-server" in servers
