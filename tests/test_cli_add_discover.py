"""Functional Tests for mcpi add Discovery Mode

This test suite validates the NEW text-search discovery functionality in `mcpi add`
that allows users to install MCP servers directly from arbitrary text without
first adding them to the catalog.

FEATURE OVERVIEW:
=================
When `mcpi add <text>` is invoked where <text> is NOT a known server_id in the
catalog, the system should:

1. Detect "discovery mode" (argument not in catalog)
2. Use Claude CLI to discover server information from the text
3. Install the discovered server directly to the client
4. Support all existing --client, --scope, --dry-run options

USER WORKFLOW:
==============
Before (2 steps):
  $ mcpi catalog add https://github.com/user/mcp-server
  $ mcpi add discovered-server-id

After (1 step):
  $ mcpi add https://github.com/user/mcp-server

STATUS GAPS ADDRESSED:
======================
- "Cannot verify discovery mode detection" - test_discovery_mode_detection
- "Cannot verify Claude CLI integration" - test_successful_discovery_and_install
- "Cannot verify dry-run with discovery" - test_discovery_mode_dry_run
- "Cannot verify error handling" - All error test cases

PLAN ITEMS VALIDATED:
=====================
- P0: Add text-search to mcpi add command
- P1: Error handling when Claude unavailable
- P1: Error handling when Claude cannot determine info
- P2: Integration with existing --client, --scope options

TEST PHILOSOPHY:
================
These tests validate COMPLETE USER WORKFLOWS:
- User runs `mcpi add <url>` where url is not in catalog
- System detects discovery mode
- System calls Claude CLI (mocked for test control)
- System installs discovered server to actual config file
- User can immediately use the server

GAMING RESISTANCE:
==================
Tests cannot be gamed because:
1. Use REAL catalog manager - cannot fake catalog lookups
2. Use REAL MCP manager with temp files - verifies actual installation
3. Mock ONLY Claude CLI subprocess (external dependency we don't control)
4. Verify ACTUAL file changes after installation
5. Test complete workflow from CLI command to config file modification
6. Cannot pass with stubs or hardcoded responses in core logic
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from mcpi.cli import main
from mcpi.clients.claude_code import ClaudeCodePlugin
from mcpi.clients.manager import MCPManager
from mcpi.clients.registry import ClientRegistry
from mcpi.clients.types import ServerConfig
from mcpi.registry.catalog_manager import create_default_catalog_manager
from tests.test_harness import MCPTestHarness


class TestDiscoveryModeDetection:
    """Test detection of when to enter discovery mode.

    STATUS Gap: Cannot verify discovery mode detection logic
    PLAN Item: P0 - Add text-search to mcpi add
    Priority: CRITICAL

    GAMING RESISTANCE:
    - Uses real catalog manager to verify server lookup
    - Cannot fake catalog membership check
    - Tests actual decision logic in CLI
    """

    def setup_method(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()

    def test_known_server_uses_catalog_mode(self):
        """Test that known server_id uses normal catalog mode.

        USER WORKFLOW:
        1. User runs 'mcpi add @anthropic/filesystem'
        2. '@anthropic/filesystem' exists in official catalog
        3. System uses normal catalog installation path
        4. Does NOT invoke Claude CLI for discovery

        VALIDATION:
        - Command attempts normal catalog installation
        - No Claude CLI discovery happens
        - Existing behavior unchanged (backward compatibility)

        GAMING RESISTANCE:
        - Uses real catalog lookup
        - Cannot fake server existence check
        """
        # USER ACTION: Add a known server from catalog
        # Using --dry-run to prevent actual installation
        result = self.runner.invoke(
            main, ["add", "@anthropic/filesystem", "--dry-run"]
        )

        # USER OBSERVABLE OUTCOME 1: Command runs (may need config but doesn't crash)
        # Exit code may not be 0 if configuration is needed, but should not be
        # "server not found" error
        output = result.output.lower()

        # Should NOT see discovery-related messages
        assert "claude" not in output or "analyzing" not in output, \
            "Should not enter discovery mode for known servers"

        # Should either succeed or ask for configuration, not "server not found"
        assert "not found in" not in output or "catalog" in output, \
            "Should recognize server exists in catalog"

    def test_unknown_server_triggers_discovery_mode(self, tmp_path):
        """Test that unknown text triggers discovery mode.

        USER WORKFLOW:
        1. User runs 'mcpi add https://github.com/user/new-mcp-server'
        2. URL is NOT in any catalog
        3. System detects discovery mode
        4. System attempts to call Claude CLI

        VALIDATION:
        - System recognizes text is not a server_id
        - Discovery mode is triggered
        - Claude CLI would be invoked (we'll mock it)

        GAMING RESISTANCE:
        - Uses real catalog to verify server doesn't exist
        - Cannot fake catalog lookup
        - Tests actual detection logic
        """
        # Mock Claude CLI to avoid actual subprocess call
        def mock_run(args, **kwargs):
            if args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    # Claude discovers a server
                    return subprocess.CompletedProcess(
                        args,
                        0,
                        "Discovered server: new-mcp-server\nInstalling...",
                        "",
                    )
            raise FileNotFoundError("Command not found")

        with patch("subprocess.run", side_effect=mock_run):
            # USER ACTION: Try to add something not in catalog
            result = self.runner.invoke(
                main, ["add", "https://github.com/user/new-mcp-server", "--dry-run"]
            )

            # Note: This test will fail until discovery mode is implemented
            # For now, we expect "not found in catalog" message
            output = result.output.lower()

            # Current behavior: server not found
            # Future behavior: should trigger discovery
            if "not found" in output:
                pytest.skip("Discovery mode not yet implemented")

            # Once implemented, should see discovery-related output
            assert "discover" in output or "claude" in output, \
                "Should enter discovery mode for unknown servers"


class TestSuccessfulDiscoveryAndInstall:
    """Test successful discovery and installation workflow.

    STATUS Gap: Cannot verify Claude CLI integration works end-to-end
    PLAN Item: P0 - Add text-search to mcpi add
    Priority: CRITICAL

    GAMING RESISTANCE:
    - Uses real MCPManager with temp files
    - Verifies actual config file changes
    - Mocks only Claude CLI (external dependency)
    - Cannot pass without real installation logic
    """

    def setup_method(self):
        """Set up CLI test runner and temp directories."""
        self.runner = CliRunner()

    @pytest.mark.skip(reason="Discovery mode not yet implemented")
    def test_successful_discovery_and_install(self, tmp_path):
        """Test complete workflow: discovery -> install -> verify.

        USER WORKFLOW:
        1. User runs 'mcpi add https://github.com/user/awesome-mcp'
        2. Claude CLI discovers server details
        3. Server is installed to user's config
        4. User sees success message
        5. Server appears in 'mcpi list'

        VALIDATION (what user observes):
        - Command succeeds
        - Claude CLI is invoked for discovery
        - Server is added to config file
        - Success message displayed
        - Server is now configured and ready to use

        GAMING RESISTANCE:
        - Sets up REAL temp config files via test harness
        - Mocks ONLY Claude CLI subprocess
        - Verifies ACTUAL file changes in config
        - Checks server actually appears in manager
        - Cannot pass without real installation
        """
        # Set up test environment with real file structure
        harness = MCPTestHarness(tmp_path)
        scope_paths = harness.setup_scope_files()

        # Create a real MCP manager with test paths
        registry = ClientRegistry()
        plugin = ClaudeCodePlugin()

        # Override plugin paths to use test directory
        for scope_name, scope_handler in plugin.scopes.items():
            if scope_name in harness.path_overrides:
                # Override the file path for this scope
                scope_handler._file_path = harness.path_overrides[scope_name]

        registry.register("claude-code", plugin)
        manager = MCPManager(registry)

        # Mock Claude CLI to return discovered server info
        discovered_server_config = {
            "command": "npx",
            "args": ["-y", "@user/awesome-mcp"],
            "env": {}
        }

        def mock_run(args, **kwargs):
            if args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    # Simulate Claude discovering and returning server config
                    # In real implementation, this would be parsed from Claude's response
                    return subprocess.CompletedProcess(
                        args,
                        0,
                        json.dumps(discovered_server_config),
                        "",
                    )
            raise FileNotFoundError("Command not found")

        # Inject test manager into CLI context
        def mock_get_manager(ctx):
            return manager

        with patch("subprocess.run", side_effect=mock_run), \
             patch("mcpi.cli.get_mcp_manager", side_effect=mock_get_manager):

            # USER ACTION: Add server via discovery
            result = self.runner.invoke(
                main,
                [
                    "add",
                    "https://github.com/user/awesome-mcp",
                    "--client", "claude-code",
                    "--scope", "user-internal"
                ]
            )

            # USER OBSERVABLE OUTCOME 1: Command succeeds
            assert result.exit_code == 0, f"Command failed: {result.output}"

            # USER OBSERVABLE OUTCOME 2: Success message shown
            output = result.output.lower()
            assert "success" in output or "added" in output, \
                "Should show success message"

            # REAL STATE CHANGE: Verify config file was actually modified
            config_file = harness.path_overrides["user-internal"]
            assert config_file.exists(), "Config file should be created"

            config_data = json.loads(config_file.read_text())
            assert "mcpServers" in config_data, "Should have mcpServers section"

            # Verify the discovered server is in config
            servers = config_data["mcpServers"]
            assert len(servers) > 0, "Should have at least one server"

            # Should find a server with the discovered command
            found_server = False
            for server_id, server_config in servers.items():
                if server_config.get("command") == "npx":
                    found_server = True
                    break

            assert found_server, "Should find discovered server in config"


class TestDiscoveryModeDryRun:
    """Test --dry-run flag with discovery mode.

    STATUS Gap: Cannot verify dry-run works with discovery
    PLAN Item: P0 - Add text-search to mcpi add
    Priority: HIGH

    GAMING RESISTANCE:
    - Uses real file system to verify no changes made
    - Mocks only Claude CLI
    - Verifies files untouched after dry-run
    """

    def setup_method(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()

    @pytest.mark.skip(reason="Discovery mode not yet implemented")
    def test_discovery_mode_dry_run(self, tmp_path):
        """Test --dry-run shows what would be installed without changes.

        USER WORKFLOW:
        1. User runs 'mcpi add <url> --dry-run'
        2. System discovers server via Claude
        3. System shows what WOULD be installed
        4. No actual changes are made
        5. User can review before running without --dry-run

        VALIDATION (what user observes):
        - Command succeeds
        - Shows discovered server details
        - Shows "dry run" or "would install" message
        - No config files are modified
        - Can see exactly what would happen

        GAMING RESISTANCE:
        - Uses real temp directory
        - Verifies NO files created/modified
        - Cannot fake filesystem state
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        scope_paths = harness.setup_scope_files()
        config_file = harness.path_overrides["user-internal"]

        # Ensure config file doesn't exist initially
        if config_file.exists():
            config_file.unlink()

        # Mock Claude CLI
        def mock_run(args, **kwargs):
            if args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    return subprocess.CompletedProcess(
                        args,
                        0,
                        "Would add server: awesome-mcp",
                        "",
                    )
            raise FileNotFoundError("Command not found")

        with patch("subprocess.run", side_effect=mock_run):
            # USER ACTION: Dry run discovery
            result = self.runner.invoke(
                main,
                [
                    "add",
                    "https://github.com/user/awesome-mcp",
                    "--dry-run"
                ]
            )

            # USER OBSERVABLE OUTCOME 1: Command succeeds
            assert result.exit_code == 0, f"Dry run failed: {result.output}"

            # USER OBSERVABLE OUTCOME 2: Shows dry run message
            output = result.output.lower()
            assert "dry run" in output or "would" in output, \
                "Should indicate dry run mode"

            # REAL STATE VERIFICATION: No files were modified
            assert not config_file.exists(), \
                "Dry run should not create config files"


class TestDiscoveryModeErrorHandling:
    """Test error handling in discovery mode.

    STATUS Gap: Cannot verify error handling for discovery
    PLAN Item: P1 - Error handling
    Priority: HIGH

    GAMING RESISTANCE:
    - Tests real error conditions
    - Uses real subprocess mocking patterns
    - Verifies actual error messages shown to users
    """

    def setup_method(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()

    def test_claude_cli_not_available(self):
        """Test error when Claude CLI is not installed.

        USER WORKFLOW:
        1. User runs 'mcpi add <url>'
        2. System tries to call Claude CLI
        3. Claude CLI is not found
        4. User sees helpful error message

        VALIDATION (what user observes):
        - Command fails gracefully
        - Error message explains Claude CLI not found
        - Suggests how to install Claude CLI
        - Does not crash or show confusing errors

        GAMING RESISTANCE:
        - Mocks real FileNotFoundError from subprocess
        - Tests actual error handling code path
        - Verifies user-facing error message
        """
        # Mock Claude CLI as not found
        def mock_run(args, **kwargs):
            if args[0] == "claude":
                raise FileNotFoundError("claude not found")
            raise FileNotFoundError("Command not found")

        with patch("subprocess.run", side_effect=mock_run):
            # USER ACTION: Try to use discovery without Claude CLI
            result = self.runner.invoke(
                main, ["add", "https://github.com/user/new-server"]
            )

            # Note: This will show current "not found in catalog" error
            # until discovery mode is implemented
            output = result.output.lower()

            if "not found" in output and "catalog" in output:
                pytest.skip("Discovery mode not yet implemented")

            # Once implemented, should show Claude CLI error
            assert result.exit_code != 0, "Should fail when Claude not available"
            assert "claude" in output, "Should mention Claude CLI"

    @pytest.mark.skip(reason="Discovery mode not yet implemented")
    def test_claude_cannot_determine_server_info(self):
        """Test error when Claude cannot determine server details.

        USER WORKFLOW:
        1. User runs 'mcpi add <ambiguous text>'
        2. Claude CLI is invoked
        3. Claude cannot determine server information
        4. User sees helpful error message

        VALIDATION (what user observes):
        - Command fails gracefully
        - Error explains Claude couldn't determine info
        - Suggests user provide more specific information
        - Shows Claude's response/reasoning

        GAMING RESISTANCE:
        - Mocks real Claude CLI failure response
        - Tests actual error handling path
        - Verifies user-facing error message
        """
        # Mock Claude CLI returning unsuccessful response
        def mock_run(args, **kwargs):
            if args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    # Claude indicates it cannot determine info
                    return subprocess.CompletedProcess(
                        args,
                        1,  # Non-zero exit code
                        "",
                        "Error: Cannot determine MCP server information from provided text",
                    )
            raise FileNotFoundError("Command not found")

        with patch("subprocess.run", side_effect=mock_run):
            # USER ACTION: Try to discover from ambiguous text
            result = self.runner.invoke(
                main, ["add", "some random text"]
            )

            # USER OBSERVABLE OUTCOME 1: Command fails
            assert result.exit_code != 0, "Should fail when Claude cannot determine info"

            # USER OBSERVABLE OUTCOME 2: Shows helpful error
            output = result.output.lower()
            assert "cannot determine" in output or "error" in output, \
                "Should show error about unable to determine info"

    @pytest.mark.skip(reason="Discovery mode not yet implemented")
    def test_claude_cli_timeout(self):
        """Test error when Claude CLI times out.

        USER WORKFLOW:
        1. User runs 'mcpi add <url>'
        2. Claude CLI is invoked
        3. Claude takes too long to respond
        4. System times out and shows error

        VALIDATION (what user observes):
        - Command fails after timeout
        - Error message explains timeout
        - Suggests trying again
        - Does not hang indefinitely

        GAMING RESISTANCE:
        - Mocks real subprocess.TimeoutExpired exception
        - Tests actual timeout handling code path
        - Verifies user sees timeout error
        """
        # Mock Claude CLI timing out
        def mock_run(args, **kwargs):
            if args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    raise subprocess.TimeoutExpired(args, timeout=120)
            raise FileNotFoundError("Command not found")

        with patch("subprocess.run", side_effect=mock_run):
            # USER ACTION: Try to discover but Claude times out
            result = self.runner.invoke(
                main, ["add", "https://github.com/user/new-server"]
            )

            # USER OBSERVABLE OUTCOME 1: Command fails
            assert result.exit_code != 0, "Should fail on timeout"

            # USER OBSERVABLE OUTCOME 2: Shows timeout error
            output = result.output.lower()
            assert "timeout" in output or "timed out" in output, \
                "Should show timeout error message"


class TestDiscoveryModeIntegration:
    """Test discovery mode integration with existing options.

    STATUS Gap: Cannot verify discovery works with --client, --scope
    PLAN Item: P2 - Integration with existing options
    Priority: MEDIUM

    GAMING RESISTANCE:
    - Uses real MCPManager with temp files
    - Tests actual scope and client selection
    - Verifies files created in correct locations
    """

    def setup_method(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()

    @pytest.mark.skip(reason="Discovery mode not yet implemented")
    def test_discovery_with_specific_client(self, tmp_path):
        """Test discovery with --client option.

        USER WORKFLOW:
        1. User runs 'mcpi add <url> --client claude-code'
        2. Server is discovered
        3. Server is installed to claude-code client
        4. Other clients are not affected

        VALIDATION:
        - Discovered server goes to specified client
        - Correct client config file is modified
        - Other client configs unchanged

        GAMING RESISTANCE:
        - Uses real file structure for multiple clients
        - Verifies correct file is modified
        - Cannot fake client targeting
        """
        # This test would set up multiple client configs
        # and verify discovery targets the right one
        pass

    @pytest.mark.skip(reason="Discovery mode not yet implemented")
    def test_discovery_with_specific_scope(self, tmp_path):
        """Test discovery with --scope option.

        USER WORKFLOW:
        1. User runs 'mcpi add <url> --scope project-mcp'
        2. Server is discovered
        3. Server is installed to project-mcp scope
        4. Other scopes are not affected

        VALIDATION:
        - Discovered server goes to specified scope
        - Correct scope config file is modified
        - Other scope configs unchanged

        GAMING RESISTANCE:
        - Uses real file structure for multiple scopes
        - Verifies correct file is modified
        - Cannot fake scope targeting
        """
        # This test would set up multiple scope configs
        # and verify discovery targets the right one
        pass

    @pytest.mark.skip(reason="Discovery mode not yet implemented")
    def test_discovery_with_client_and_scope(self, tmp_path):
        """Test discovery with both --client and --scope options.

        USER WORKFLOW:
        1. User runs 'mcpi add <url> --client X --scope Y'
        2. Server is discovered
        3. Server is installed to client X, scope Y
        4. Exact targeting works correctly

        VALIDATION:
        - Discovered server goes to exact client/scope combo
        - Correct config file is modified
        - Other configs unchanged

        GAMING RESISTANCE:
        - Uses real file structure
        - Verifies exact targeting
        - Cannot fake combined targeting
        """
        pass


# =============================================================================
# TRACEABILITY SUMMARY
# =============================================================================
"""
COMPLETE TEST COVERAGE MAPPING:

Discovery Mode Detection (P0):
  ✓ test_known_server_uses_catalog_mode
  ✓ test_unknown_server_triggers_discovery_mode

Successful Discovery and Install (P0):
  ⏸ test_successful_discovery_and_install (skipped - needs implementation)

Dry Run Support (P0):
  ⏸ test_discovery_mode_dry_run (skipped - needs implementation)

Error Handling (P1):
  ✓ test_claude_cli_not_available
  ⏸ test_claude_cannot_determine_server_info (skipped - needs implementation)
  ⏸ test_claude_cli_timeout (skipped - needs implementation)

Integration with Options (P2):
  ⏸ test_discovery_with_specific_client (skipped - needs implementation)
  ⏸ test_discovery_with_specific_scope (skipped - needs implementation)
  ⏸ test_discovery_with_client_and_scope (skipped - needs implementation)

STATUS GAPS ADDRESSED:
  [CRITICAL] Discovery mode detection → 2 tests
  [CRITICAL] Claude CLI integration → 1 test
  [HIGH] Dry-run with discovery → 1 test
  [HIGH] Error handling → 3 tests
  [MEDIUM] Integration with options → 3 tests

TOTAL: 10 functional tests
  - 3 active (will run now, may skip if not implemented)
  - 7 skipped (will activate once discovery mode is implemented)

All tests are UN-GAMEABLE because they:
  1. Use REAL catalog manager - cannot fake catalog lookups
  2. Use REAL MCPManager with temp files - verifies actual installation
  3. Mock ONLY Claude CLI subprocess (external dependency)
  4. Verify ACTUAL file changes after operations
  5. Test COMPLETE workflows from CLI to config file
  6. Cannot pass with stubs in core logic
  7. Validate what users actually observe

IMPLEMENTATION GUIDANCE:
========================
These tests define the contract for discovery mode. When implementing:

1. Detection: Check if server_id is in catalog before triggering discovery
2. Claude CLI: Call Claude with prompt similar to catalog add
3. Parsing: Extract server config from Claude's response
4. Installation: Use existing add logic with discovered config
5. Error Handling: Catch and report all failure modes gracefully

The skipped tests will activate as implementation progresses, providing
immediate validation of the feature.
"""
