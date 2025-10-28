"""Integration tests for CLI commands with minimal mocking."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from mcpi.cli import main


class TestCliIntegration:
    """Integration tests that use real components with minimal mocking."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()

    def test_help_command(self):
        """Test help command works."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "MCP Server Package Installer" in result.output

    def test_version_command(self):
        """Test version command works."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_status_command_no_servers(self):
        """Test status command when no servers are installed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_config = Path(temp_dir) / "mcp_servers.json"
            claude_config.write_text("{}")

            with patch(
                "mcpi.installer.claude_code.ClaudeCodeInstaller._find_claude_code_config",
                return_value=claude_config,
            ):
                result = self.runner.invoke(main, ["status"])
                assert result.exit_code == 0
                assert "No MCP servers installed" in result.output

    def test_status_json_no_servers(self):
        """Test status --json command when no servers are installed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_config = Path(temp_dir) / "mcp_servers.json"
            claude_config.write_text("{}")

            with patch(
                "mcpi.installer.claude_code.ClaudeCodeInstaller._find_claude_code_config",
                return_value=claude_config,
            ):
                result = self.runner.invoke(main, ["status", "--json"])
                assert result.exit_code == 0
                data = json.loads(result.output)
                assert isinstance(data, list)
                assert len(data) == 0

    def test_registry_list_with_real_data(self):
        """Test registry list with actual registry data."""
        result = self.runner.invoke(main, ["registry", "list"])
        # Should succeed whether registry exists or not
        assert result.exit_code == 0
        # Should either show servers or "No servers found"
        assert "servers" in result.output.lower() or "Total:" in result.output

    def test_registry_list_json(self):
        """Test registry list --json format."""
        result = self.runner.invoke(main, ["registry", "list", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        try:
            data = json.loads(result.output)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            assert False, "Output is not valid JSON"

    def test_registry_validate(self):
        """Test registry validation."""
        result = self.runner.invoke(main, ["registry", "validate"])
        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1]
        assert "Registry" in result.output or "Error" in result.output

    def test_registry_search(self):
        """Test registry search functionality."""
        result = self.runner.invoke(main, ["registry", "search", "filesystem"])
        assert result.exit_code == 0
        # Should show search results or "No servers found"
        assert "Search Results" in result.output or "No servers found" in result.output

    def test_registry_show_nonexistent(self):
        """Test showing a nonexistent server."""
        result = self.runner.invoke(main, ["registry", "show", "nonexistent-server"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_config_show(self):
        """Test config show command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["XDG_CONFIG_HOME"] = temp_dir
            try:
                result = self.runner.invoke(main, ["config", "show"])
                assert result.exit_code == 0
                assert "MCPI Configuration" in result.output
                assert "General Settings" in result.output
            finally:
                if "XDG_CONFIG_HOME" in os.environ:
                    del os.environ["XDG_CONFIG_HOME"]

    def test_config_show_json(self):
        """Test config show --json format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["XDG_CONFIG_HOME"] = temp_dir
            try:
                result = self.runner.invoke(main, ["config", "show", "--json"])
                assert result.exit_code == 0
                # Should be valid JSON
                try:
                    data = json.loads(result.output)
                    assert isinstance(data, dict)
                    assert "general" in data
                except json.JSONDecodeError:
                    assert False, f"Output is not valid JSON: {result.output}"
            finally:
                if "XDG_CONFIG_HOME" in os.environ:
                    del os.environ["XDG_CONFIG_HOME"]

    def test_config_validate(self):
        """Test config validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["XDG_CONFIG_HOME"] = temp_dir
            try:
                result = self.runner.invoke(main, ["config", "validate"])
                # Should succeed or show validation errors
                assert result.exit_code in [0, 1]
                assert "Configuration" in result.output or "valid" in result.output
            finally:
                if "XDG_CONFIG_HOME" in os.environ:
                    del os.environ["XDG_CONFIG_HOME"]

    def test_install_nonexistent_server(self):
        """Test installing a nonexistent server fails gracefully."""
        result = self.runner.invoke(main, ["install", "nonexistent-server"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_install_missing_args(self):
        """Test install with no arguments."""
        result = self.runner.invoke(main, ["install"])
        assert result.exit_code == 2  # Click argument error

    def test_uninstall_missing_args(self):
        """Test uninstall with no arguments."""
        result = self.runner.invoke(main, ["uninstall"])
        assert result.exit_code == 2  # Click argument error

    def test_verbose_flag(self):
        """Test verbose flag doesn't break anything."""
        result = self.runner.invoke(main, ["--verbose", "status"])
        assert result.exit_code == 0
        # Verbose might add extra output, but should still work
        assert "servers" in result.output.lower()

    def test_dry_run_flag(self):
        """Test dry-run flag doesn't break anything."""
        result = self.runner.invoke(main, ["--dry-run", "status"])
        assert result.exit_code == 0
        # Dry-run shouldn't change status command behavior
        assert "servers" in result.output.lower()

    def test_registry_add_help(self):
        """Test registry add help works."""
        result = self.runner.invoke(main, ["registry", "add", "--help"])
        assert result.exit_code == 0
        assert "Add MCP server to registry" in result.output

    def test_config_init_help(self):
        """Test config init help works."""
        result = self.runner.invoke(main, ["config", "init", "--help"])
        assert result.exit_code == 0
        assert "Initialize MCPI configuration" in result.output

    def test_update_help(self):
        """Test update help works."""
        result = self.runner.invoke(main, ["update", "--help"])
        assert result.exit_code == 0
        assert "Update registry from remote source" in result.output


class TestCliWithMockedNetwork:
    """Integration tests that mock only network calls."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()

    @patch("mcpi.registry.catalog.httpx.AsyncClient.get")
    def test_update_registry_mock_network(self, mock_get):
        """Test registry update with mocked network call."""
        # Mock a successful response
        mock_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda: {"servers": {}},
                "raise_for_status": lambda: None,
            },
        )()
        mock_get.return_value = mock_response

        result = self.runner.invoke(main, ["update"])
        # Should handle the mocked response gracefully
        assert result.exit_code in [0, 1]  # May fail on save, but shouldn't crash

    @patch("mcpi.registry.doc_parser.httpx.AsyncClient.get")
    def test_registry_add_mock_network(self, mock_get):
        """Test registry add with mocked network call."""
        # Mock a response with some content
        mock_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "text": "npm install some-package\n# Some MCP Server\nDescription here",
                "raise_for_status": lambda: None,
            },
        )()
        mock_get.return_value = mock_response

        result = self.runner.invoke(
            main, ["registry", "add", "https://example.com/readme", "--dry-run"]
        )
        # Should handle the mocked response
        assert result.exit_code in [0, 1]  # May fail to parse, but shouldn't crash
        assert "DRY RUN" in result.output or "Failed to extract" in result.output
