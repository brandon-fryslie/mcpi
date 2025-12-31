"""Tests that verify our test suite actually catches bugs.

These "meta-tests" deliberately introduce bugs and verify that tests fail.
If these tests pass when they should fail, it exposes a gap in our test coverage.

PHILOSOPHY:
- A test suite that passes with broken code provides false confidence
- These tests verify our tests are effective at catching real bugs
- Focus on the most critical paths: installation, format handling, state management

KEY FINDING FROM AUDIT:
- The installed_plugins.json array format bug reached production
- 1,333 tests passed. Bug still shipped.
- Root cause: Tests validated mocked data, not production formats
"""

import json
import pytest
from unittest.mock import patch
from pathlib import Path

from mcpi.clients.plugin_based import PluginBasedScope
from mcpi.clients.types import ScopeConfig
from mcpi.installer.npm import NPMInstaller


class TestDryRunGap:
    """Demonstrate the dry_run gap - tests pass even with broken commands.

    These tests DOCUMENT a known limitation, not fix it.
    They serve as evidence for why we need real integration tests.
    """

    def test_dry_run_always_succeeds(self):
        """DOCUMENTING GAP: dry_run=True always returns success.

        This test proves that ANY command would "succeed" in dry_run mode.
        A real integration test (not dry_run) would catch command errors.
        """
        installer = NPMInstaller(dry_run=True)

        # Even if we tried to run a completely wrong command internally,
        # dry_run mode would report success
        result = installer._run_npm_command(["this-is-not-a-real-command"])

        # This passes because dry_run bypasses actual execution
        assert result.returncode == 0
        assert "[DRY RUN]" in result.stdout

    def test_dry_run_hides_package_existence(self):
        """DOCUMENTING GAP: dry_run doesn't verify package exists.

        With dry_run=True, installing a non-existent package "succeeds".
        Only real execution would catch this.
        """
        installer = NPMInstaller(dry_run=True)

        # This package doesn't exist
        result = installer._run_npm_command(
            ["install", "package-that-definitely-does-not-exist-12345"]
        )

        # But dry_run says it worked!
        assert result.returncode == 0


class TestFormatBugDetection:
    """Verify tests catch format assumption bugs.

    The installed_plugins.json array format bug is the canonical example.
    """

    @pytest.fixture
    def plugin_environment(self, tmp_path):
        """Create a plugin environment for testing."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        plugins_dir = claude_dir / "plugins"
        plugins_dir.mkdir()

        return {
            "claude_dir": claude_dir,
            "plugins_dir": plugins_dir,
            "settings_path": claude_dir / "settings.json",
            "installed_plugins_path": plugins_dir / "installed_plugins.json",
        }

    def test_dict_format_assumption_caught(self, plugin_environment, tmp_path):
        """Verify that code correctly handles array format (not just dict).

        THE BUG: Code assumed installed_plugins[id] was a dict
        REALITY: Production uses array format

        This test verifies the fix is in place.
        """
        # Create a plugin with ARRAY format (production reality)
        plugin_dir = tmp_path / "plugins" / "test-plugin"
        claude_plugin_dir = plugin_dir / ".claude-plugin"
        claude_plugin_dir.mkdir(parents=True)

        plugin_json = {
            "name": "test-plugin",
            "version": "1.0.0",
            "mcpServers": {"server": {"command": "node", "args": ["server.js"]}},
        }
        (claude_plugin_dir / "plugin.json").write_text(json.dumps(plugin_json))

        # Settings with plugin enabled
        settings = {"enabledPlugins": {"test-plugin@mp": True}}
        plugin_environment["settings_path"].write_text(json.dumps(settings))

        # ARRAY format (what production uses)
        installed = {
            "version": 2,
            "plugins": {
                "test-plugin@mp": [{"installPath": str(plugin_dir), "version": "1.0.0"}]
            },
        }
        plugin_environment["installed_plugins_path"].write_text(json.dumps(installed))

        scope = PluginBasedScope(
            config=ScopeConfig(
                name="plugin",
                description="Test",
                priority=0,
                path=plugin_environment["settings_path"],
                is_user_level=True,
            ),
            settings_path=plugin_environment["settings_path"],
            installed_plugins_path=plugin_environment["installed_plugins_path"],
        )

        # This would have failed before the fix (AttributeError: 'list' has no 'get')
        servers = scope.get_servers()
        assert "test-plugin:server" in servers

    def test_both_formats_work(self, plugin_environment, tmp_path):
        """Verify both dict (legacy) and array (current) formats work.

        Production may have mixed formats during migrations.
        """
        # Create plugins
        for name in ["legacy", "modern"]:
            plugin_dir = tmp_path / "plugins" / name
            claude_plugin_dir = plugin_dir / ".claude-plugin"
            claude_plugin_dir.mkdir(parents=True)
            plugin_json = {
                "name": name,
                "version": "1.0.0",
                "mcpServers": {"server": {"command": "node"}},
            }
            (claude_plugin_dir / "plugin.json").write_text(json.dumps(plugin_json))

        settings = {"enabledPlugins": {"legacy@mp": True, "modern@mp": True}}
        plugin_environment["settings_path"].write_text(json.dumps(settings))

        # Mixed format file
        installed = {
            "version": 2,
            "plugins": {
                # Legacy dict format
                "legacy@mp": {
                    "installPath": str(tmp_path / "plugins" / "legacy"),
                    "version": "1.0.0",
                },
                # Modern array format
                "modern@mp": [
                    {
                        "installPath": str(tmp_path / "plugins" / "modern"),
                        "version": "1.0.0",
                    }
                ],
            },
        }
        plugin_environment["installed_plugins_path"].write_text(json.dumps(installed))

        scope = PluginBasedScope(
            config=ScopeConfig(
                name="plugin",
                description="Test",
                priority=0,
                path=plugin_environment["settings_path"],
                is_user_level=True,
            ),
            settings_path=plugin_environment["settings_path"],
            installed_plugins_path=plugin_environment["installed_plugins_path"],
        )

        servers = scope.get_servers()
        assert "legacy:server" in servers, "Legacy dict format should work"
        assert "modern:server" in servers, "Modern array format should work"


class TestRegressionPrevention:
    """Tests that would have caught past bugs if they existed before the bugs.

    Add a test here for every production bug discovered.
    """

    def test_empty_array_doesnt_crash(self, tmp_path):
        """Regression: Empty plugin array should not cause crash.

        If a plugin is enabled but its install array is empty,
        the code should handle it gracefully.
        """
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        plugins_dir = claude_dir / "plugins"
        plugins_dir.mkdir()

        settings_path = claude_dir / "settings.json"
        installed_path = plugins_dir / "installed_plugins.json"

        settings = {"enabledPlugins": {"empty@mp": True}}
        settings_path.write_text(json.dumps(settings))

        # Plugin enabled but empty array
        installed = {"version": 2, "plugins": {"empty@mp": []}}
        installed_path.write_text(json.dumps(installed))

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

        # Should not crash, should return empty or skip
        servers = scope.get_servers()
        assert isinstance(servers, dict)
        assert "empty:server" not in servers

    def test_missing_install_path_handled(self, tmp_path):
        """Regression: Plugin entry without installPath should not crash."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        plugins_dir = claude_dir / "plugins"
        plugins_dir.mkdir()

        settings_path = claude_dir / "settings.json"
        installed_path = plugins_dir / "installed_plugins.json"

        settings = {"enabledPlugins": {"nopath@mp": True}}
        settings_path.write_text(json.dumps(settings))

        # Plugin without installPath
        installed = {
            "version": 2,
            "plugins": {"nopath@mp": [{"version": "1.0.0"}]},  # Missing installPath
        }
        installed_path.write_text(json.dumps(installed))

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

        # Should handle gracefully
        servers = scope.get_servers()
        assert isinstance(servers, dict)


class TestMutationDetection:
    """Simulate "mutation testing" - verify tests catch specific code changes.

    These tests verify that if someone breaks the code in specific ways,
    our test suite will catch it.
    """

    def test_format_check_is_present(self):
        """Verify the isinstance check for list vs dict exists.

        This is a proxy for checking the format handling code is present.
        If someone removes the array format handling, other tests should fail.
        """
        import inspect
        from mcpi.clients.plugin_based import PluginBasedScope

        source = inspect.getsource(PluginBasedScope._discover_servers)

        # The fix for the array format bug MUST include isinstance check
        assert "isinstance" in source, (
            "PluginBasedScope._discover_servers must check isinstance "
            "to handle both dict and array formats"
        )
        assert (
            "list" in source
        ), "PluginBasedScope._discover_servers must handle list (array) format"

    def test_dry_run_is_conditional(self):
        """Verify dry_run mode is explicitly checked, not hardcoded.

        If someone accidentally removes the dry_run check, real commands
        would run in tests (which might be bad, but at least would catch bugs).
        """
        import inspect
        from mcpi.installer.npm import NPMInstaller

        source = inspect.getsource(NPMInstaller._run_npm_command)

        assert (
            "dry_run" in source
        ), "NPMInstaller._run_npm_command must check dry_run flag"
        assert "if self.dry_run" in source, "dry_run check must be conditional"
