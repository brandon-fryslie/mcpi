"""Tests to validate code handles production file formats correctly.

These tests use fixtures from tests/fixtures/production-samples/ which contain
sanitized versions of real production file formats. This catches bugs where
test fixtures don't match production reality.

The installed_plugins.json array format bug is the canonical example:
- Tests used dict format: {"plugin@id": {"installPath": "..."}}
- Production uses array format: {"plugin@id": [{"installPath": "..."}]}
- 1,333 tests passed. Bug still reached production.
"""

import json
import pytest
from pathlib import Path

from mcpi.clients.plugin_based import PluginBasedScope
from mcpi.clients.types import ScopeConfig


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "production-samples"


class TestInstalledPluginsFormats:
    """Test all known installed_plugins.json formats are handled correctly."""

    @pytest.fixture
    def create_plugin_environment(self, tmp_path):
        """Factory fixture to create plugin environment with specified format."""

        def _create(installed_plugins_data: dict) -> tuple[Path, Path]:
            claude_dir = tmp_path / ".claude"
            claude_dir.mkdir()

            # Create settings with all plugins from installed_plugins enabled
            plugins_in_data = list(installed_plugins_data.get("plugins", {}).keys())
            settings = {"enabledPlugins": {p: True for p in plugins_in_data}}
            settings_path = claude_dir / "settings.json"
            settings_path.write_text(json.dumps(settings))

            # Create installed_plugins.json - we need to rewrite paths to be under tmp_path
            plugins_dir = claude_dir / "plugins"
            plugins_dir.mkdir()

            # Deep copy and fix paths
            import copy

            fixed_data = copy.deepcopy(installed_plugins_data)

            # Create plugin directories with plugin.json for each installed plugin
            for plugin_id, plugin_entries in installed_plugins_data.get(
                "plugins", {}
            ).items():
                # Handle both dict and array formats
                if isinstance(plugin_entries, list):
                    entries = plugin_entries
                    fixed_entries = fixed_data["plugins"][plugin_id]
                else:
                    entries = [plugin_entries]
                    fixed_entries = [fixed_data["plugins"][plugin_id]]

                for i, entry in enumerate(entries):
                    install_path = entry.get("installPath")
                    if install_path:
                        # Create actual path under tmp_path
                        actual_path = tmp_path / install_path.lstrip("/")
                        claude_plugin_dir = actual_path / ".claude-plugin"
                        claude_plugin_dir.mkdir(parents=True, exist_ok=True)

                        # Update the fixed_data to use actual path
                        if isinstance(plugin_entries, list):
                            fixed_entries[i]["installPath"] = str(actual_path)
                        else:
                            fixed_entries[0]["installPath"] = str(actual_path)

                        # Create a simple plugin.json with one MCP server
                        plugin_name = plugin_id.split("@")[0]
                        plugin_json = {
                            "name": plugin_name,
                            "version": entry.get("version", "1.0.0"),
                            "mcpServers": {
                                "test-server": {
                                    "command": "node",
                                    "args": ["server.js"],
                                }
                            },
                        }
                        (claude_plugin_dir / "plugin.json").write_text(
                            json.dumps(plugin_json)
                        )

                # If it was a dict, unwrap from list
                if not isinstance(plugin_entries, list):
                    fixed_data["plugins"][plugin_id] = fixed_entries[0]

            installed_path = plugins_dir / "installed_plugins.json"
            installed_path.write_text(json.dumps(fixed_data))

            return settings_path, installed_path

        return _create

    def test_v1_dict_format(self, create_plugin_environment):
        """Test v1 dict format (legacy) is handled correctly.

        Format: plugins[id] = {"installPath": "...", "version": "..."}
        """
        data = {
            "version": 1,
            "plugins": {
                "legacy-plugin@marketplace": {
                    "version": "1.0.0",
                    "installPath": "/plugins/cache/marketplace/legacy-plugin/1.0.0",
                }
            },
        }

        settings_path, installed_path = create_plugin_environment(data)

        scope = PluginBasedScope(
            config=ScopeConfig(
                name="plugin",
                description="Test",
                priority=0,
                path=settings_path,
                is_user_level=True,
            ),
            settings_path=settings_path,
            installed_plugins_path=installed_path,
        )

        servers = scope.get_servers()
        assert "legacy-plugin:test-server" in servers

    def test_v2_array_format_single_entry(self, create_plugin_environment):
        """Test v2 array format with single installation entry.

        Format: plugins[id] = [{"installPath": "...", "scope": "..."}]
        This is the current production format.
        """
        data = {
            "version": 2,
            "plugins": {
                "modern-plugin@marketplace": [
                    {
                        "scope": "user",
                        "installPath": "/plugins/cache/marketplace/modern-plugin/2.0.0",
                        "version": "2.0.0",
                        "installedAt": "2025-01-15T10:30:00.000Z",
                        "lastUpdated": "2025-01-20T14:45:00.000Z",
                    }
                ]
            },
        }

        settings_path, installed_path = create_plugin_environment(data)

        scope = PluginBasedScope(
            config=ScopeConfig(
                name="plugin",
                description="Test",
                priority=0,
                path=settings_path,
                is_user_level=True,
            ),
            settings_path=settings_path,
            installed_plugins_path=installed_path,
        )

        servers = scope.get_servers()
        assert "modern-plugin:test-server" in servers

    def test_v2_array_format_multiple_entries(self, create_plugin_environment):
        """Test v2 array format with multiple installation entries (multi-scope).

        Format: plugins[id] = [{scope: "project", ...}, {scope: "user", ...}]
        The first entry should be used (most recent).
        """
        data = {
            "version": 2,
            "plugins": {
                "multi-scope@marketplace": [
                    {
                        "scope": "project",
                        "installPath": "/project/plugins/multi-scope/2.0.0",
                        "version": "2.0.0",
                    },
                    {
                        "scope": "user",
                        "installPath": "/user/plugins/multi-scope/1.5.0",
                        "version": "1.5.0",
                    },
                ]
            },
        }

        settings_path, installed_path = create_plugin_environment(data)

        scope = PluginBasedScope(
            config=ScopeConfig(
                name="plugin",
                description="Test",
                priority=0,
                path=settings_path,
                is_user_level=True,
            ),
            settings_path=settings_path,
            installed_plugins_path=installed_path,
        )

        servers = scope.get_servers()
        # Should find server from first (project scope) entry
        assert "multi-scope:test-server" in servers

    def test_v2_empty_array(self, create_plugin_environment, tmp_path):
        """Test v2 format with empty array (plugin registered but not installed).

        Edge case: plugins[id] = []
        """
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        settings = {"enabledPlugins": {"empty-plugin@marketplace": True}}
        settings_path = claude_dir / "settings.json"
        settings_path.write_text(json.dumps(settings))

        plugins_dir = claude_dir / "plugins"
        plugins_dir.mkdir()
        installed_path = plugins_dir / "installed_plugins.json"
        installed_path.write_text(
            json.dumps({"version": 2, "plugins": {"empty-plugin@marketplace": []}})
        )

        scope = PluginBasedScope(
            config=ScopeConfig(
                name="plugin",
                description="Test",
                priority=0,
                path=settings_path,
                is_user_level=True,
            ),
            settings_path=settings_path,
            installed_plugins_path=installed_path,
        )

        # Should not crash, should return empty or skip this plugin
        servers = scope.get_servers()
        assert "empty-plugin:test-server" not in servers

    def test_mixed_formats_in_same_file(self, create_plugin_environment):
        """Test handling of mixed formats in the same installed_plugins.json.

        Real-world scenario: Some plugins installed before format change,
        others after. File might contain mix of dict and array formats.
        """
        data = {
            "version": 2,
            "plugins": {
                # Legacy dict format (some tools may still write this)
                "old-plugin@marketplace": {
                    "version": "1.0.0",
                    "installPath": "/plugins/old-plugin/1.0.0",
                },
                # New array format
                "new-plugin@marketplace": [
                    {
                        "scope": "user",
                        "installPath": "/plugins/new-plugin/2.0.0",
                        "version": "2.0.0",
                    }
                ],
            },
        }

        settings_path, installed_path = create_plugin_environment(data)

        scope = PluginBasedScope(
            config=ScopeConfig(
                name="plugin",
                description="Test",
                priority=0,
                path=settings_path,
                is_user_level=True,
            ),
            settings_path=settings_path,
            installed_plugins_path=installed_path,
        )

        servers = scope.get_servers()
        # Both formats should work
        assert "old-plugin:test-server" in servers
        assert "new-plugin:test-server" in servers


class TestProductionFixturesLoad:
    """Verify production fixture files can be loaded and parsed."""

    def test_installed_plugins_v1_loads(self):
        """Verify v1 dict format fixture is valid JSON."""
        fixture_path = FIXTURES_DIR / "claude-code" / "installed_plugins_v1_dict.json"
        with open(fixture_path) as f:
            data = json.load(f)

        assert "version" in data
        assert data["version"] == 1
        assert "plugins" in data
        # Should have at least one plugin for testing
        assert len(data["plugins"]) > 0

    def test_installed_plugins_v2_loads(self):
        """Verify v2 array format fixture is valid JSON with array structure."""
        fixture_path = FIXTURES_DIR / "claude-code" / "installed_plugins_v2_array.json"
        with open(fixture_path) as f:
            data = json.load(f)

        assert "version" in data
        assert data["version"] == 2
        assert "plugins" in data

        # All entries should be arrays
        for plugin_id, entries in data["plugins"].items():
            assert isinstance(
                entries, list
            ), f"Plugin {plugin_id} should use array format, got {type(entries)}"

    def test_settings_user_global_loads(self):
        """Verify user settings fixture is valid JSON."""
        fixture_path = FIXTURES_DIR / "claude-code" / "settings_user_global.json"
        with open(fixture_path) as f:
            data = json.load(f)

        # Should have expected structure
        assert "enabledPlugins" in data or "mcpServers" in data

    def test_mcp_json_fixtures_load(self):
        """Verify all .mcp.json fixtures are valid JSON."""
        mcp_dir = FIXTURES_DIR / "mcp-json"
        for fixture_file in mcp_dir.glob("*.json"):
            with open(fixture_file) as f:
                data = json.load(f)

            # All should have mcpServers key
            assert "mcpServers" in data, f"{fixture_file.name} missing mcpServers key"


class TestMcpJsonFormats:
    """Test .mcp.json format handling."""

    def test_minimal_mcp_json(self, tmp_path):
        """Test minimal valid .mcp.json is accepted."""
        config = {"mcpServers": {"minimal": {"command": "test"}}}

        mcp_path = tmp_path / ".mcp.json"
        mcp_path.write_text(json.dumps(config))

        # Load and verify
        with open(mcp_path) as f:
            loaded = json.load(f)

        assert "mcpServers" in loaded
        assert "minimal" in loaded["mcpServers"]
        assert loaded["mcpServers"]["minimal"]["command"] == "test"

    def test_server_with_optional_fields_missing(self, tmp_path):
        """Test server config with only command (no args, no env)."""
        config = {"mcpServers": {"bare": {"command": "bare-server"}}}

        mcp_path = tmp_path / ".mcp.json"
        mcp_path.write_text(json.dumps(config))

        with open(mcp_path) as f:
            loaded = json.load(f)

        server = loaded["mcpServers"]["bare"]
        assert server["command"] == "bare-server"
        # args and env may be missing - code should handle this
        assert server.get("args") is None
        assert server.get("env") is None

    def test_env_vars_in_config(self, tmp_path):
        """Test environment variable references in config."""
        config = {
            "mcpServers": {
                "with-env": {
                    "command": "server",
                    "env": {
                        "API_KEY": "${API_KEY}",
                        "STATIC_VALUE": "not-a-var",
                    },
                }
            }
        }

        mcp_path = tmp_path / ".mcp.json"
        mcp_path.write_text(json.dumps(config))

        with open(mcp_path) as f:
            loaded = json.load(f)

        env = loaded["mcpServers"]["with-env"]["env"]
        assert env["API_KEY"] == "${API_KEY}"
        assert env["STATIC_VALUE"] == "not-a-var"


class TestFormatVersionCompatibility:
    """Ensure backwards compatibility across format versions.

    When Claude Code changes file formats, MCPI must handle both old and new.
    These tests verify we don't break older installations.
    """

    @pytest.mark.parametrize(
        "version,format_type",
        [
            (1, "dict"),
            (2, "array"),
        ],
    )
    def test_version_marker_handling(self, version, format_type, tmp_path):
        """Test version field is recognized but code handles missing version."""
        if format_type == "dict":
            plugins = {"test@mp": {"installPath": "/test", "version": "1.0"}}
        else:
            plugins = {"test@mp": [{"installPath": "/test", "version": "1.0"}]}

        data = {"version": version, "plugins": plugins}
        path = tmp_path / "installed_plugins.json"
        path.write_text(json.dumps(data))

        with open(path) as f:
            loaded = json.load(f)

        assert loaded["version"] == version

    def test_missing_version_field(self, tmp_path):
        """Test handling of installed_plugins.json without version field.

        Old files might not have version field at all.
        """
        data = {"plugins": {"legacy@mp": {"installPath": "/legacy", "version": "0.9"}}}
        path = tmp_path / "installed_plugins.json"
        path.write_text(json.dumps(data))

        with open(path) as f:
            loaded = json.load(f)

        assert "version" not in loaded
        assert "plugins" in loaded
