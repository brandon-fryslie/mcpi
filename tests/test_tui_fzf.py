"""Tests for the fzf-based TUI functionality."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcpi.clients.types import ServerInfo, ServerState
from mcpi.registry.catalog import MCPServer
from mcpi.tui import (
    build_fzf_command,
    build_server_list,
    check_fzf_installed,
    format_server_line,
    get_server_status,
)


class TestCheckFzfInstalled:
    """Test fzf installation detection."""

    def test_fzf_installed(self):
        """Test when fzf is installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            assert check_fzf_installed() is True
            mock_run.assert_called_once()
            # Verify we're checking for fzf
            args = mock_run.call_args[0][0]
            assert "fzf" in args

    def test_fzf_not_installed(self):
        """Test when fzf is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert check_fzf_installed() is False

    def test_fzf_check_error(self):
        """Test when fzf check returns error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)
            assert check_fzf_installed() is False


class TestGetServerStatus:
    """Test getting server status from manager."""

    def test_get_status_enabled(self):
        """Test getting status for an enabled server."""
        mock_manager = Mock()
        mock_manager.get_server_state.return_value = ServerState.ENABLED
        mock_manager.get_server_info.return_value = ServerInfo(
            id="test-server",
            client="claude-code",
            scope="user",
            config={"command": "npx", "args": ["test"]},
            state=ServerState.ENABLED,
        )

        status = get_server_status(mock_manager, "test-server")

        assert status["installed"] is True
        assert status["state"] == ServerState.ENABLED
        assert status["info"] is not None

    def test_get_status_disabled(self):
        """Test getting status for a disabled server."""
        mock_manager = Mock()
        mock_manager.get_server_state.return_value = ServerState.DISABLED
        mock_manager.get_server_info.return_value = ServerInfo(
            id="test-server",
            client="claude-code",
            scope="user",
            config={"command": "npx", "args": ["test"]},
            state=ServerState.DISABLED,
        )

        status = get_server_status(mock_manager, "test-server")

        assert status["installed"] is True
        assert status["state"] == ServerState.DISABLED

    def test_get_status_not_installed(self):
        """Test getting status for a not-installed server."""
        mock_manager = Mock()
        mock_manager.get_server_state.return_value = ServerState.NOT_INSTALLED
        mock_manager.get_server_info.return_value = None

        status = get_server_status(mock_manager, "test-server")

        assert status["installed"] is False
        assert status["state"] == ServerState.NOT_INSTALLED
        assert status["info"] is None


class TestFormatServerLine:
    """Test server line formatting."""

    def test_format_enabled_server(self):
        """Test formatting an enabled server."""
        server = MCPServer(
            description="Test server description",
            command="npx",
            args=["test-server"],
        )
        status = {
            "installed": True,
            "state": ServerState.ENABLED,
            "info": ServerInfo(
                id="test-server",
                client="claude-code",
                scope="user",
                config={},
                state=ServerState.ENABLED,
            ),
        }

        line = format_server_line("test-server", server, status)

        # Should have green checkmark and bold
        assert "[✓]" in line or "✓" in line
        assert "test-server" in line
        assert "Test server description" in line
        # Should contain ANSI codes for green and bold
        assert "\033[" in line  # ANSI escape sequence

    def test_format_disabled_server(self):
        """Test formatting a disabled server."""
        server = MCPServer(
            description="Test server description",
            command="npx",
            args=["test-server"],
        )
        status = {
            "installed": True,
            "state": ServerState.DISABLED,
            "info": ServerInfo(
                id="test-server",
                client="claude-code",
                scope="user",
                config={},
                state=ServerState.DISABLED,
            ),
        }

        line = format_server_line("test-server", server, status)

        # Should have yellow X and bold
        assert "[✗]" in line or "✗" in line
        assert "test-server" in line
        assert "Test server description" in line
        # Should contain ANSI codes for yellow and bold
        assert "\033[" in line

    def test_format_not_installed_server(self):
        """Test formatting a not-installed server."""
        server = MCPServer(
            description="Test server description",
            command="npx",
            args=["test-server"],
        )
        status = {
            "installed": False,
            "state": ServerState.NOT_INSTALLED,
            "info": None,
        }

        line = format_server_line("test-server", server, status)

        # Should have empty brackets and normal color
        assert "[ ]" in line
        assert "test-server" in line
        assert "Test server description" in line

    def test_format_line_truncates_long_description(self):
        """Test that long descriptions are truncated."""
        server = MCPServer(
            description="A" * 200,  # Very long description
            command="npx",
            args=["test-server"],
        )
        status = {
            "installed": False,
            "state": ServerState.NOT_INSTALLED,
            "info": None,
        }

        line = format_server_line("test-server", server, status)

        # Description should be truncated
        assert "..." in line
        # Line shouldn't be excessively long (accounting for ANSI codes)
        assert len(line) < 250


class TestBuildServerList:
    """Test building the complete server list."""

    def test_build_list_empty(self):
        """Test building list when no servers exist."""
        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = []
        mock_manager = Mock()

        lines = build_server_list(mock_catalog, mock_manager)

        assert lines == []

    def test_build_list_sorts_by_status(self):
        """Test that servers are sorted with installed first."""
        # Create mock servers
        servers = [
            ("not-installed-server", MCPServer(description="Not installed", command="npx")),
            ("enabled-server", MCPServer(description="Enabled", command="npx")),
            ("disabled-server", MCPServer(description="Disabled", command="npx")),
        ]

        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = servers

        mock_manager = Mock()

        def get_state(server_id, client=None):
            if server_id == "enabled-server":
                return ServerState.ENABLED
            elif server_id == "disabled-server":
                return ServerState.DISABLED
            else:
                return ServerState.NOT_INSTALLED

        def get_info(server_id, client=None):
            if server_id in ["enabled-server", "disabled-server"]:
                return ServerInfo(
                    id=server_id,
                    client="claude-code",
                    scope="user",
                    config={},
                    state=get_state(server_id),
                )
            return None

        mock_manager.get_server_state.side_effect = get_state
        mock_manager.get_server_info.side_effect = get_info

        lines = build_server_list(mock_catalog, mock_manager)

        # Should have 3 lines
        assert len(lines) == 3

        # Enabled should be first (green)
        assert "enabled-server" in lines[0]
        # Disabled should be second (yellow)
        assert "disabled-server" in lines[1]
        # Not installed should be last (no color)
        assert "not-installed-server" in lines[2]


class TestBuildFzfCommand:
    """Test building the fzf command."""

    def test_build_fzf_command_basic(self):
        """Test building basic fzf command."""
        cmd = build_fzf_command()

        assert cmd[0] == "fzf"
        assert "--ansi" in cmd

        # Check for header (could be --header= or --header as separate item)
        cmd_str = " ".join(cmd)
        assert "--header" in cmd_str

        # Find header content
        header_found = False
        for item in cmd:
            if item.startswith("--header=") or (item == "--header"):
                header_found = True
                # Get the header text (either after = or next item)
                if item.startswith("--header="):
                    header_content = item.split("=", 1)[1]
                else:
                    # Find index and get next item
                    idx = cmd.index(item)
                    if idx + 1 < len(cmd):
                        header_content = cmd[idx + 1]
                    else:
                        continue

                # Should contain keyboard shortcuts
                assert "ctrl-a" in header_content.lower()
                assert "ctrl-r" in header_content.lower()
                assert "ctrl-e" in header_content.lower()
                assert "ctrl-d" in header_content.lower()
                break

        assert header_found

    def test_fzf_command_has_bindings(self):
        """Test that fzf command has all required bindings."""
        cmd = build_fzf_command()

        cmd_str = " ".join(cmd)

        # Check for all required bindings
        assert "--bind" in cmd_str
        assert "ctrl-a:" in cmd_str  # Add
        assert "ctrl-r:" in cmd_str  # Remove
        assert "ctrl-e:" in cmd_str  # Enable
        assert "ctrl-d:" in cmd_str  # Disable
        assert "ctrl-i:" in cmd_str or "enter:" in cmd_str  # Info

    def test_fzf_command_has_preview(self):
        """Test that fzf command has preview configured."""
        cmd = build_fzf_command()

        cmd_str = " ".join(cmd)

        # Should have preview configuration
        assert "--preview" in cmd_str
        assert "mcpi info" in cmd_str


class TestLaunchFzfInterface:
    """Test launching the fzf interface (integration-style tests)."""

    def test_launch_fails_if_fzf_not_installed(self):
        """Test that launch fails gracefully if fzf is not installed."""
        with patch("mcpi.tui.check_fzf_installed", return_value=False):
            from mcpi.tui import launch_fzf_interface

            mock_manager = Mock()
            mock_catalog = Mock()

            # Should raise or handle error gracefully
            with pytest.raises(RuntimeError, match="fzf"):
                launch_fzf_interface(mock_manager, mock_catalog)

    @patch("mcpi.tui.check_fzf_installed", return_value=True)
    @patch("subprocess.run")
    def test_launch_calls_fzf_with_server_list(
        self, mock_run, mock_check_fzf
    ):
        """Test that launch calls fzf with properly formatted server list."""
        from mcpi.tui import launch_fzf_interface

        # Mock catalog with one server
        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = [
            ("test-server", MCPServer(description="Test", command="npx"))
        ]

        # Mock manager
        mock_manager = Mock()
        mock_manager.get_server_state.return_value = ServerState.NOT_INSTALLED
        mock_manager.get_server_info.return_value = None

        # Mock subprocess to exit immediately
        mock_run.return_value = Mock(returncode=0, stdout="")

        launch_fzf_interface(mock_manager, mock_catalog)

        # Verify fzf was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args

        # Verify input contains server list
        if "input" in call_args.kwargs:
            input_data = call_args.kwargs["input"]
            assert "test-server" in input_data

    @patch("mcpi.tui.check_fzf_installed", return_value=True)
    @patch("subprocess.run")
    def test_launch_handles_user_cancellation(
        self, mock_run, mock_check_fzf
    ):
        """Test that launch handles user cancellation (Ctrl-C) gracefully."""
        from mcpi.tui import launch_fzf_interface

        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = []
        mock_manager = Mock()

        # Simulate user cancellation (exit code 130)
        mock_run.return_value = Mock(returncode=130, stdout="")

        # Should not raise exception
        launch_fzf_interface(mock_manager, mock_catalog)
