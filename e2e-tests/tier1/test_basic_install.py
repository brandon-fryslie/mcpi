"""True End-to-End CLI Tests.

These tests exercise the actual mcpi CLI via subprocess calls:
1. Set up isolated directory fixtures (fake HOME with Claude config structure)
2. Call mcpi CLI commands via shell with real arguments
3. Assert against actual files written to disk

This validates the full user experience from command line to file output.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def e2e_home(tmp_path):
    """Create isolated HOME directory with Claude Code structure.

    This mimics a real user's home directory where Claude Code stores config:
    - ~/.claude/           (Claude settings directory)
    - ~/.claude.json       (user-internal scope - main config file)
    - ~/.mcp.json          (user-mcp scope)
    - ~/.config/claude/    (XDG config location)

    The HOME environment variable is set so Path.home() returns this directory.
    """
    home = tmp_path / "home"
    home.mkdir()

    # Create Claude directory structure
    claude_dir = home / ".claude"
    claude_dir.mkdir()

    config_claude_dir = home / ".config" / "claude"
    config_claude_dir.mkdir(parents=True)

    return home


@pytest.fixture
def run_mcpi(e2e_home):
    """Run mcpi CLI command with isolated HOME.

    Returns a function that:
    - Executes mcpi commands via subprocess
    - Uses the isolated HOME directory
    - Returns CompletedProcess with stdout, stderr, returncode

    Usage:
        result = run_mcpi("list")
        result = run_mcpi("add", "@anthropic/filesystem", "--scope", "user-internal")
        result = run_mcpi("search", "-q", "filesystem", check=False)
    """

    def run(*args: str, check: bool = True, timeout: int = 60) -> subprocess.CompletedProcess:
        # Build environment with isolated HOME
        env = os.environ.copy()
        env["HOME"] = str(e2e_home)
        env["USERPROFILE"] = str(e2e_home)  # Windows
        env["XDG_CONFIG_HOME"] = str(e2e_home / ".config")

        # Run mcpi as subprocess
        cmd = ["mcpi", *args]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=str(e2e_home),
        )

        if check and result.returncode != 0:
            raise RuntimeError(
                f"Command failed: {' '.join(cmd)}\n"
                f"Exit code: {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

        return result

    return run


@pytest.fixture
def claude_config_path(e2e_home) -> Path:
    """Path to the main Claude config file (~/.claude.json)."""
    return e2e_home / ".claude.json"


@pytest.fixture
def mcp_config_path(e2e_home) -> Path:
    """Path to the user MCP config file (~/.mcp.json)."""
    return e2e_home / ".mcp.json"


def read_json_file(path: Path) -> dict:
    """Read and parse a JSON file."""
    return json.loads(path.read_text())


# =============================================================================
# CLI Search and Info Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.tier1
class TestCLISearch:
    """Test mcpi search command via CLI."""

    def test_search_finds_filesystem(self, e2e_mode, run_mcpi):
        """CLI search returns filesystem server."""
        result = run_mcpi("search", "-q", "filesystem")

        assert result.returncode == 0
        assert "filesystem" in result.stdout.lower()

    def test_search_with_no_matches(self, e2e_mode, run_mcpi):
        """CLI search with no matches doesn't crash."""
        result = run_mcpi("search", "-q", "nonexistent12345xyz", check=False)

        # Should complete (might be 0 or 1 depending on implementation)
        assert result.returncode in (0, 1)


@pytest.mark.e2e
@pytest.mark.tier1
class TestCLIInfo:
    """Test mcpi info command via CLI."""

    def test_info_shows_server_details(self, e2e_mode, run_mcpi):
        """CLI info shows server command and args."""
        result = run_mcpi("info", "@anthropic/filesystem")

        assert result.returncode == 0
        # Should show npx command
        assert "npx" in result.stdout.lower() or "command" in result.stdout.lower()


# =============================================================================
# CLI Add/Remove Tests - Verify Actual Files
# =============================================================================


@pytest.mark.e2e
@pytest.mark.tier1
class TestCLIAdd:
    """Test mcpi add command creates actual config files."""

    def test_add_creates_config_file(self, e2e_mode, run_mcpi, claude_config_path):
        """mcpi add creates the config file with server entry."""
        # Run CLI add command
        result = run_mcpi(
            "add", "@anthropic/filesystem",
            "--client", "claude-code",
            "--scope", "user-internal",
        )

        assert result.returncode == 0

        # VERIFY: Config file actually exists on disk
        assert claude_config_path.exists(), (
            f"Config file should exist at {claude_config_path}\n"
            f"CLI output: {result.stdout}"
        )

        # VERIFY: File contains valid JSON with correct structure
        config = read_json_file(claude_config_path)
        assert "mcpServers" in config, f"Config should have mcpServers key: {config}"

        # VERIFY: Server entry exists
        servers = config["mcpServers"]
        assert len(servers) > 0, "Should have at least one server"

        # Find filesystem server
        filesystem_found = False
        for server_id, server_config in servers.items():
            if "filesystem" in server_id.lower():
                filesystem_found = True
                # VERIFY: Server has required fields
                assert "command" in server_config, f"Server should have command: {server_config}"
                assert "args" in server_config, f"Server should have args: {server_config}"
                assert server_config["command"] == "npx", f"Command should be npx: {server_config}"
                break

        assert filesystem_found, f"Should find filesystem server in {list(servers.keys())}"

    def test_add_to_user_mcp_scope(self, e2e_mode, run_mcpi, mcp_config_path):
        """mcpi add to user-mcp scope creates ~/.mcp.json."""
        result = run_mcpi(
            "add", "@anthropic/memory",
            "--client", "claude-code",
            "--scope", "user-mcp",
        )

        assert result.returncode == 0

        # VERIFY: ~/.mcp.json file created
        assert mcp_config_path.exists(), f"Should create {mcp_config_path}"

        config = read_json_file(mcp_config_path)
        assert "mcpServers" in config
        assert len(config["mcpServers"]) > 0

    def test_add_multiple_servers(self, e2e_mode, run_mcpi, claude_config_path):
        """Can add multiple servers to same config file."""
        # Add first server
        run_mcpi(
            "add", "@anthropic/filesystem",
            "--client", "claude-code",
            "--scope", "user-internal",
        )

        # Add second server
        run_mcpi(
            "add", "@anthropic/memory",
            "--client", "claude-code",
            "--scope", "user-internal",
        )

        # VERIFY: Both servers in config
        config = read_json_file(claude_config_path)
        servers = config["mcpServers"]

        server_ids = list(servers.keys())
        assert any("filesystem" in s.lower() for s in server_ids), f"Should have filesystem: {server_ids}"
        assert any("memory" in s.lower() for s in server_ids), f"Should have memory: {server_ids}"


@pytest.mark.e2e
@pytest.mark.tier1
class TestCLIRemove:
    """Test mcpi remove command actually removes from config files."""

    def test_remove_deletes_from_config(self, e2e_mode, run_mcpi, claude_config_path):
        """mcpi remove actually removes server from config file."""
        # First add a server
        run_mcpi(
            "add", "@anthropic/filesystem",
            "--client", "claude-code",
            "--scope", "user-internal",
        )

        # Verify it's there
        config = read_json_file(claude_config_path)
        assert len(config["mcpServers"]) > 0

        # Remove it
        result = run_mcpi(
            "remove", "@anthropic/filesystem",
            "--client", "claude-code",
        )

        assert result.returncode == 0

        # VERIFY: Server actually removed from file
        config = read_json_file(claude_config_path)
        servers = config.get("mcpServers", {})
        for server_id in servers.keys():
            assert "filesystem" not in server_id.lower(), (
                f"Filesystem server should be removed but found: {server_id}"
            )


# =============================================================================
# CLI List Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.tier1
class TestCLIList:
    """Test mcpi list command shows installed servers."""

    def test_list_shows_added_server(self, e2e_mode, run_mcpi, claude_config_path):
        """mcpi list shows servers that were added."""
        # Add a server
        run_mcpi(
            "add", "@anthropic/filesystem",
            "--client", "claude-code",
            "--scope", "user-internal",
        )

        # List servers
        result = run_mcpi("list")

        assert result.returncode == 0
        assert "filesystem" in result.stdout.lower(), (
            f"List should show filesystem server\nOutput: {result.stdout}"
        )

    def test_list_empty_when_no_servers(self, e2e_mode, run_mcpi):
        """mcpi list works with no servers installed."""
        result = run_mcpi("list", check=False)

        # Should not crash
        assert result.returncode == 0


# =============================================================================
# CLI Enable/Disable Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.tier1
class TestCLIEnableDisable:
    """Test mcpi enable/disable commands modify actual files."""

    def test_disable_removes_from_active_config(self, e2e_mode, run_mcpi, claude_config_path):
        """mcpi disable moves server out of active config."""
        # Add server
        run_mcpi(
            "add", "@anthropic/filesystem",
            "--client", "claude-code",
            "--scope", "user-internal",
        )

        # Verify in config
        config = read_json_file(claude_config_path)
        assert len(config["mcpServers"]) > 0

        # Disable
        result = run_mcpi("disable", "@anthropic/filesystem")
        assert result.returncode == 0

        # VERIFY: Server no longer in active config
        config = read_json_file(claude_config_path)
        servers = config.get("mcpServers", {})
        for server_id in servers.keys():
            assert "filesystem" not in server_id.lower(), (
                f"Disabled server should not be in active config: {server_id}"
            )

    def test_enable_restores_to_active_config(self, e2e_mode, run_mcpi, claude_config_path):
        """mcpi enable restores server to active config."""
        # Add and disable
        run_mcpi(
            "add", "@anthropic/filesystem",
            "--client", "claude-code",
            "--scope", "user-internal",
        )
        run_mcpi("disable", "@anthropic/filesystem")

        # Enable
        result = run_mcpi("enable", "@anthropic/filesystem")
        assert result.returncode == 0

        # VERIFY: Server back in active config
        config = read_json_file(claude_config_path)
        servers = config.get("mcpServers", {})
        server_ids = list(servers.keys())
        assert any("filesystem" in s.lower() for s in server_ids), (
            f"Enabled server should be in config: {server_ids}"
        )


# =============================================================================
# CLI Dry-Run Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.tier1
class TestCLIDryRun:
    """Test --dry-run flag doesn't modify files."""

    def test_add_dry_run_no_file_created(self, e2e_mode, run_mcpi, claude_config_path):
        """mcpi add --dry-run should not create config file."""
        result = run_mcpi(
            "add", "@anthropic/filesystem",
            "--client", "claude-code",
            "--scope", "user-internal",
            "--dry-run",
        )

        assert result.returncode == 0

        # VERIFY: No file created
        assert not claude_config_path.exists(), (
            f"Dry run should not create config file at {claude_config_path}"
        )
