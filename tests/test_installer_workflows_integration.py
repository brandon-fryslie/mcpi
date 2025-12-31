"""Integration tests for installer workflows using the test harness."""

from unittest.mock import MagicMock, patch

import pytest

from mcpi.clients.types import ServerConfig, ServerState


class TestInstallerWorkflowsWithHarness:
    """Test installation workflows with real file operations."""

    @patch("subprocess.run")
    def test_npx_server_installation(self, mock_run, mcp_manager_with_harness):
        """Test installing an NPX-based server."""
        manager, harness = mcp_manager_with_harness

        # Mock successful npx installation
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Installation successful"
        )

        # Add an NPX server
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            type="stdio",
        )

        result = manager.add_server("filesystem", config, "user-mcp", "claude-code")
        assert result.success

        # Verify file was created with correct content
        harness.assert_valid_json("user-mcp")
        harness.assert_server_exists("user-mcp", "filesystem")
        harness.assert_server_command("user-mcp", "filesystem", "npx")

        # Verify the full configuration
        server_config = harness.get_server_config("user-mcp", "filesystem")
        assert server_config["args"] == [
            "-y",
            "@modelcontextprotocol/server-filesystem",
        ]
        assert server_config["type"] == "stdio"

    @patch("subprocess.run")
    def test_pip_server_installation(self, mock_run, mcp_manager_with_harness):
        """Test installing a pip-based server."""
        manager, harness = mcp_manager_with_harness

        # Mock successful pip installation
        mock_run.return_value = MagicMock(returncode=0, stdout="Successfully installed")

        # Add a Python server
        config = ServerConfig(
            command="python",
            args=["-m", "mcp_server_git"],
            env={"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
            type="stdio",
        )

        result = manager.add_server("git-server", config, "user-mcp", "claude-code")
        assert result.success

        # Verify configuration
        harness.assert_server_exists("user-mcp", "git-server")
        server_config = harness.get_server_config("user-mcp", "git-server")
        assert server_config["command"] == "python"
        assert server_config["env"]["GITHUB_TOKEN"] == "${GITHUB_TOKEN}"


    def test_environment_variable_handling(self, mcp_manager_with_harness):
        """Test proper handling of environment variables."""
        manager, harness = mcp_manager_with_harness

        # Add server with multiple env vars
        config = ServerConfig(
            command="python",
            args=["-m", "secure_server"],
            env={"API_KEY": "${API_KEY}", "DEBUG": "true", "PORT": "3000"},
            type="stdio",
        )

        result = manager.add_server("env-test", config, "user-internal", "claude-code")
        assert result.success

        # Verify all env vars are preserved
        server_config = harness.get_server_config("user-internal", "env-test")
        assert server_config["env"]["API_KEY"] == "${API_KEY}"
        assert server_config["env"]["DEBUG"] == "true"
        assert server_config["env"]["PORT"] == "3000"


class TestComplexWorkflows:
    """Test complex multi-step workflows."""


    def test_bulk_operations(self, mcp_manager_with_harness):
        """Test bulk adding and removing servers."""
        manager, harness = mcp_manager_with_harness

        # Add multiple servers in bulk
        servers_to_add = [
            ("server1", ServerConfig(command="npx", args=["pkg1"], type="stdio")),
            ("server2", ServerConfig(command="npx", args=["pkg2"], type="stdio")),
            (
                "server3",
                ServerConfig(command="python", args=["-m", "pkg3"], type="stdio"),
            ),
            ("server4", ServerConfig(command="node", args=["pkg4.js"], type="stdio")),
        ]

        # Add all servers to user-mcp scope
        for server_id, config in servers_to_add:
            result = manager.add_server(server_id, config, "user-mcp", "claude-code")
            assert result.success

        # Verify all were added
        assert harness.count_servers_in_scope("user-mcp") == 4

        # List and verify each
        servers = manager.list_servers("claude-code", "user-mcp")
        server_ids = {info.id for info in servers.values()}
        assert "server1" in server_ids
        assert "server2" in server_ids
        assert "server3" in server_ids
        assert "server4" in server_ids

        # Remove servers 2 and 3
        manager.remove_server("server2", "user-mcp", "claude-code")
        manager.remove_server("server3", "user-mcp", "claude-code")

        # Verify removal
        assert harness.count_servers_in_scope("user-mcp") == 2
        harness.assert_server_exists("user-mcp", "server1")
        harness.assert_server_exists("user-mcp", "server4")

        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-mcp", "server2")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-mcp", "server3")

    def test_error_recovery(self, mcp_manager_with_harness):
        """Test recovery from various error conditions."""
        manager, harness = mcp_manager_with_harness

        # Add a server
        config = ServerConfig(
            command="python", args=["-m", "test_server"], type="stdio"
        )
        manager.add_server("test-server", config, "user-mcp", "claude-code")

        # Try to add duplicate (should handle gracefully)
        result = manager.add_server("test-server", config, "user-mcp", "claude-code")
        # This might succeed (overwrite) or fail (duplicate check)

        # Try to remove non-existent server
        result = manager.remove_server("nonexistent", "user-mcp", "claude-code")
        assert not result.success

        # Original server should still be there
        harness.assert_server_exists("user-mcp", "test-server")

        # Try to add to non-existent scope
        result = manager.add_server(
            "bad-scope-test", config, "invalid-scope", "claude-code"
        )
        assert not result.success

        # No file should have been created for invalid scope
        assert "invalid-scope" not in harness.path_overrides
