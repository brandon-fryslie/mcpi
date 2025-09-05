"""Smoke tests for CLI commands to ensure they don't crash immediately."""

import json
import subprocess
import pytest
from pathlib import Path
from typing import List


def run_cli_command(args: List[str]) -> tuple[int, str, str]:
    """Run a CLI command and return exit code, stdout, stderr."""
    cmd = ["uv", "run", "mcpi"] + args
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestCliSmoke:
    """Smoke tests to ensure CLI commands don't immediately fail."""

    def test_mcpi_help(self):
        """Test that mcpi --help works."""
        code, stdout, stderr = run_cli_command(["--help"])
        assert code == 0
        assert "MCPI - MCP Server Package Installer" in stdout
        assert "Commands:" in stdout

    def test_mcpi_version(self):
        """Test that mcpi --version works."""
        code, stdout, stderr = run_cli_command(["--version"])
        assert code == 0

    def test_status_command(self):
        """Test that mcpi status works without crashing."""
        code, stdout, stderr = run_cli_command(["status"])
        assert code == 0
        # Should show either "No MCP servers installed" or a table
        assert "MCP servers" in stdout or "No MCP" in stdout

    def test_status_json(self):
        """Test that mcpi status --json works."""
        code, stdout, stderr = run_cli_command(["status", "--json"])
        assert code == 0
        # Should be valid JSON (empty array if no servers)
        try:
            data = json.loads(stdout)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            pytest.fail("status --json did not output valid JSON")

    def test_registry_list_help(self):
        """Test that registry list --help works."""
        code, stdout, stderr = run_cli_command(["registry", "list", "--help"])
        assert code == 0
        assert "List available MCP servers" in stdout

    def test_registry_list_basic(self):
        """Test that registry list works without crashing."""
        code, stdout, stderr = run_cli_command(["registry", "list"])
        # Should succeed even if no servers or registry doesn't exist
        assert code == 0 or "No servers found" in stdout or "Error" in stderr

    def test_registry_validate(self):
        """Test that registry validate works without crashing."""
        code, stdout, stderr = run_cli_command(["registry", "validate"])
        # Should succeed or fail gracefully
        assert code in [0, 1]  # Valid registry or validation errors

    def test_config_help(self):
        """Test that config --help works."""
        code, stdout, stderr = run_cli_command(["config", "--help"])
        assert code == 0
        assert "Configuration management" in stdout

    def test_config_show(self):
        """Test that config show works without crashing."""
        code, stdout, stderr = run_cli_command(["config", "show"])
        # Should work even with default config
        assert code == 0
        assert "MCPI Configuration" in stdout or "General Settings" in stdout

    def test_config_show_json(self):
        """Test that config show --json works."""
        code, stdout, stderr = run_cli_command(["config", "show", "--json"])
        assert code == 0
        # Should be valid JSON
        try:
            data = json.loads(stdout)
            assert isinstance(data, dict)
            assert "general" in data
        except json.JSONDecodeError:
            pytest.fail("config show --json did not output valid JSON")

    def test_config_validate(self):
        """Test that config validate works without crashing."""
        code, stdout, stderr = run_cli_command(["config", "validate"])
        # Should succeed or show validation errors
        assert code in [0, 1]

    def test_install_help(self):
        """Test that install --help works."""
        code, stdout, stderr = run_cli_command(["install", "--help"])
        assert code == 0
        assert "Install one or more MCP servers" in stdout

    def test_install_no_args(self):
        """Test that install with no arguments shows appropriate error."""
        code, stdout, stderr = run_cli_command(["install"])
        assert code == 2  # Click error for missing argument
        assert "Missing argument" in stderr

    def test_install_invalid_server(self):
        """Test that install with invalid server ID fails gracefully."""
        code, stdout, stderr = run_cli_command(["install", "nonexistent-server"])
        assert code == 1  # Should exit with error code
        assert "not found" in stdout

    def test_uninstall_help(self):
        """Test that uninstall --help works."""
        code, stdout, stderr = run_cli_command(["uninstall", "--help"])
        assert code == 0
        assert "Uninstall one or more MCP servers" in stdout

    def test_uninstall_no_args(self):
        """Test that uninstall with no arguments shows appropriate error."""
        code, stdout, stderr = run_cli_command(["uninstall"])
        assert code == 2  # Click error for missing argument
        assert "Missing argument" in stderr

    def test_update_help(self):
        """Test that update --help works."""
        code, stdout, stderr = run_cli_command(["update", "--help"])
        assert code == 0
        assert "Update registry from remote source" in stdout

    def test_registry_search_help(self):
        """Test that registry search --help works."""
        code, stdout, stderr = run_cli_command(["registry", "search", "--help"])
        assert code == 0
        assert "Search for MCP servers" in stdout

    def test_registry_search_basic(self):
        """Test that registry search works without crashing."""
        code, stdout, stderr = run_cli_command(["registry", "search", "test"])
        # Should work even if no results
        assert code == 0
        assert "Search Results" in stdout or "No servers found" in stdout

    def test_registry_show_help(self):
        """Test that registry show --help works."""
        code, stdout, stderr = run_cli_command(["registry", "show", "--help"])
        assert code == 0
        assert "Show detailed information" in stdout

    def test_registry_add_help(self):
        """Test that registry add --help works."""
        code, stdout, stderr = run_cli_command(["registry", "add", "--help"])
        assert code == 0
        assert "Add MCP server to registry" in stdout

    def test_verbose_flag(self):
        """Test that --verbose flag works."""
        code, stdout, stderr = run_cli_command(["--verbose", "status"])
        assert code == 0
        # Should not crash with verbose flag

    def test_dry_run_flag(self):
        """Test that --dry-run flag works."""
        code, stdout, stderr = run_cli_command(["--dry-run", "status"])
        assert code == 0
        # Should not crash with dry-run flag


class TestCliEdgeCases:
    """Test edge cases and error conditions."""

    def test_registry_show_nonexistent(self):
        """Test showing nonexistent server."""
        code, stdout, stderr = run_cli_command(["registry", "show", "nonexistent"])
        assert code == 1
        assert "not found" in stdout

    def test_invalid_command(self):
        """Test invalid command."""
        code, stdout, stderr = run_cli_command(["invalid-command"])
        assert code == 2  # Click error
        assert "No such command" in stderr

    def test_config_init_help(self):
        """Test that config init --help works."""
        code, stdout, stderr = run_cli_command(["config", "init", "--help"])
        assert code == 0
        assert "Initialize MCPI configuration" in stdout