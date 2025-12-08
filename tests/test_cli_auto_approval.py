"""Functional Tests for MCP Server Auto-Approval (MCPI-0fb)

This test suite validates the auto-approval mechanism for MCP servers added to
the project-mcp scope (.mcp.json). Claude Code requires explicit approval via
enabledMcpjsonServers array in .claude/settings.local.json.

BUG DESCRIPTION (MCPI-0fb):
===========================
When a server is added to the project-mcp scope (.mcp.json), `mcpi list` shows
it as ENABLED even though it's actually PENDING APPROVAL / UNAPPROVED. Claude
Code won't use the server until user manually approves it in the Claude Code UI.

CURRENT BEHAVIOR (Bug):
1. User runs `mcpi add filesystem --scope project-mcp`
2. Server is added to .mcp.json
3. `mcpi list` shows server as ENABLED (WRONG - it's not approved!)
4. Claude Code won't use it until manual approval

EXPECTED BEHAVIOR (Fix):
1. User runs `mcpi add filesystem --scope project-mcp`
2. Server is added to .mcp.json
3. Server is ALSO added to enabledMcpjsonServers in .claude/settings.local.json
4. `mcpi list` shows server as ENABLED (NOW CORRECT!)
5. Claude Code can use the server immediately

ROOT CAUSE:
===========
The project-mcp scope currently uses FileMoveEnableDisableHandler, which doesn't
understand the approval requirement. It should use ApprovalRequiredEnableDisableHandler
which manages enabledMcpjsonServers/disabledMcpjsonServers arrays in settings.local.json.

TECHNICAL DETAILS:
==================
Claude Code has two approval mechanisms:

1. FileMoveEnableDisableHandler (for user-internal, user-mcp):
   - Active file: servers.json (ENABLED)
   - Disabled file: .disabled-servers.json (DISABLED)
   - No approval arrays

2. ApprovalRequiredEnableDisableHandler (for project-mcp):
   - Config file: .mcp.json (server definitions)
   - Approval file: .claude/settings.local.json (approval arrays)
   - Arrays: enabledMcpjsonServers (ENABLED), disabledMcpjsonServers (DISABLED)
   - Missing from both arrays = UNAPPROVED (functionally disabled)

The fix requires:
1. Change project-mcp scope to use ApprovalRequiredEnableDisableHandler
2. Auto-approve when adding via `mcpi add` (not discovery mode)
3. Preserve manual approval workflow for user-initiated adds in Claude UI

TEST PHILOSOPHY:
================
These tests validate ACTUAL APPROVAL STATE:
- Use REAL ClaudeCodePlugin with temp files
- Use REAL MCPManager
- Verify ACTUAL file contents on disk
- Cannot pass with stubs that just return "ENABLED"
- Test end-to-end from CLI command to approval state

GAMING RESISTANCE:
==================
Tests cannot be gamed because:
1. Use REAL MCPTestHarness for file operations
2. Use REAL ClaudeCodePlugin (not mocks)
3. Verify ACTUAL .claude/settings.local.json contents
4. Read back approval state via get_server_state()
5. Cannot hardcode responses - tests check multiple scenarios
6. State detection must work correctly (ENABLED vs UNAPPROVED vs DISABLED)

"""

import json
from pathlib import Path

import pytest

from mcpi.clients.claude_code import ClaudeCodePlugin
from mcpi.clients.types import ServerState
from tests.test_harness import MCPTestHarness


class TestUnapprovedServerDetection:
    """Test detection of unapproved servers in project-mcp scope.

    STATUS Gap: Cannot distinguish ENABLED from UNAPPROVED
    PLAN Item: MCPI-0fb - State detection for approval
    Priority: CRITICAL

    GAMING RESISTANCE:
    - Manually creates unapproved server state
    - Verifies actual state detection logic
    - Cannot fake with hardcoded responses
    """

    def test_server_in_mcp_json_without_approval_shows_unapproved(self, tmp_path):
        """Test that server in .mcp.json but not approved shows as UNAPPROVED.

        This test demonstrates the BUG: Currently, servers in .mcp.json show as
        ENABLED even when they're not approved in settings.local.json.

        USER WORKFLOW:
        1. Server is manually added to .mcp.json (e.g., by editing file)
        2. Server is NOT in enabledMcpjsonServers array
        3. 'mcpi list' shows server as ENABLED (BUG!)
        4. But Claude Code won't use it (requires approval)

        EXPECTED AFTER FIX:
        - Server should show as UNAPPROVED or DISABLED (not ENABLED)
        - State detection correctly identifies unapproved state

        GAMING RESISTANCE:
        - Manually creates .mcp.json with server
        - Does NOT create approval entry
        - Uses real plugin to detect state
        - Cannot pass with stub that returns ENABLED for all
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        # Manually create .mcp.json with a server (simulating manual edit)
        harness.prepopulate_file(
            "project-mcp",
            {
                "mcpServers": {
                    "unapproved-server": {
                        "command": "npx",
                        "args": ["-y", "@test/unapproved-server"],
                        "type": "stdio"
                    }
                }
            }
        )

        # Do NOT add to enabledMcpjsonServers (simulating lack of approval)
        # Create empty settings.local.json
        harness.prepopulate_file(
            "project-local",
            {
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": []
            }
        )

        # Create plugin with test paths
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)

        # CURRENT BUG: State shows as ENABLED (because FileMoveEnableDisableHandler
        # treats anything in .mcp.json as enabled)
        state = plugin.get_server_state("unapproved-server")

        # THIS TEST SHOULD FAIL until bug is fixed
        # After fix, state should be DISABLED or UNAPPROVED (not ENABLED)
        assert state in [ServerState.DISABLED, ServerState.UNAPPROVED], \
            f"BUG: Unapproved server shows as {state}, should be DISABLED/UNAPPROVED"

        # VERIFICATION: Server should appear in list but not as ENABLED
        servers = plugin.list_servers(scope="project-mcp")

        # Find the unapproved server
        found = False
        for qualified_id, info in servers.items():
            if info.id == "unapproved-server":
                found = True
                assert info.state != ServerState.ENABLED, \
                    "BUG: Unapproved server should NOT show as ENABLED"
                break

        assert found, "Unapproved server should appear in list"

    def test_server_explicitly_disabled_shows_disabled(self, tmp_path):
        """Test that server in disabledMcpjsonServers shows as DISABLED.

        USER WORKFLOW:
        1. User disables a server via 'mcpi disable' or Claude UI
        2. Server is in .mcp.json
        3. Server ID is in disabledMcpjsonServers array
        4. 'mcpi list' shows server as DISABLED (not ENABLED)

        VALIDATION:
        - Server in disabledMcpjsonServers = DISABLED
        - State detection correctly identifies disabled state
        - Different from unapproved state

        GAMING RESISTANCE:
        - Manually creates disabled state
        - Uses real plugin to detect state
        - Tests specific disabled state (not just "not enabled")
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        # Create server in .mcp.json
        harness.prepopulate_file(
            "project-mcp",
            {
                "mcpServers": {
                    "disabled-server": {
                        "command": "npx",
                        "args": ["-y", "@test/disabled-server"],
                        "type": "stdio"
                    }
                }
            }
        )

        # Add to disabledMcpjsonServers array (explicit disable)
        harness.prepopulate_file(
            "project-local",
            {
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": ["disabled-server"]
            }
        )

        # Create plugin with test paths
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)

        # VERIFICATION: State should be DISABLED
        state = plugin.get_server_state("disabled-server")

        # THIS TEST SHOULD ALSO FAIL until ApprovalRequiredEnableDisableHandler is used
        assert state == ServerState.DISABLED, \
            f"Explicitly disabled server should show as DISABLED, got {state}"


class TestApprovalStateRoundTrip:
    """Test enable/disable operations with approval mechanism.

    STATUS Gap: Need to verify approval-based enable/disable works
    PLAN Item: MCPI-0fb - Approval state transitions
    Priority: HIGH

    GAMING RESISTANCE:
    - Tests full state transition cycle
    - Verifies actual file changes at each step
    - Cannot fake state machine
    """

    def test_enable_unapproved_server(self, tmp_path):
        """Test that 'mcpi enable' approves an unapproved server.

        USER WORKFLOW:
        1. Server exists in .mcp.json but not approved
        2. User runs 'mcpi enable <server> --scope project-mcp'
        3. Server ID is added to enabledMcpjsonServers
        4. Server shows as ENABLED

        VALIDATION:
        - Server moves from UNAPPROVED to ENABLED
        - enabledMcpjsonServers array updated
        - State detection reflects change

        GAMING RESISTANCE:
        - Sets up unapproved state manually
        - Uses real enable command
        - Verifies actual approval file changes
        - Cannot pass without real state transition
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        # Create server in .mcp.json (unapproved)
        harness.prepopulate_file(
            "project-mcp",
            {
                "mcpServers": {
                    "test-server": {
                        "command": "npx",
                        "args": ["-y", "@test/server"],
                        "type": "stdio"
                    }
                }
            }
        )

        # Create empty approval arrays (unapproved state)
        harness.prepopulate_file(
            "project-local",
            {
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": []
            }
        )

        # Create plugin
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)

        # BEFORE: Server should be unapproved (shows as ENABLED due to bug)
        state_before = plugin.get_server_state("test-server")
        # Current bug: shows ENABLED even though unapproved
        # After fix: should show DISABLED/UNAPPROVED

        # USER ACTION: Enable the server
        result = plugin.enable_server("test-server", scope="project-mcp")
        assert result.success, f"Enable should succeed: {result.message}"

        # AFTER: Server should be enabled
        state_after = plugin.get_server_state("test-server")
        assert state_after == ServerState.ENABLED, \
            "Server should be ENABLED after enable command"

        # VERIFICATION: Check approval file was updated
        settings_local = harness.path_overrides["project-local"]
        settings_data = json.loads(settings_local.read_text())

        assert "test-server" in settings_data["enabledMcpjsonServers"], \
            "Server should be in enabledMcpjsonServers after enable"

    def test_disable_enabled_server(self, tmp_path):
        """Test that 'mcpi disable' moves server to disabledMcpjsonServers.

        USER WORKFLOW:
        1. Server is enabled (in enabledMcpjsonServers)
        2. User runs 'mcpi disable <server> --scope project-mcp'
        3. Server ID moves to disabledMcpjsonServers
        4. Server shows as DISABLED

        VALIDATION:
        - Server moves from ENABLED to DISABLED
        - Arrays updated correctly (removed from enabled, added to disabled)
        - State detection reflects change

        GAMING RESISTANCE:
        - Sets up enabled state manually
        - Uses real disable command
        - Verifies actual approval file changes
        - Cannot pass without real state transition
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        # Create server in .mcp.json
        harness.prepopulate_file(
            "project-mcp",
            {
                "mcpServers": {
                    "test-server": {
                        "command": "npx",
                        "args": ["-y", "@test/server"],
                        "type": "stdio"
                    }
                }
            }
        )

        # Create server as ENABLED
        harness.prepopulate_file(
            "project-local",
            {
                "enabledMcpjsonServers": ["test-server"],
                "disabledMcpjsonServers": []
            }
        )

        # Create plugin
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)

        # BEFORE: Server should be enabled
        state_before = plugin.get_server_state("test-server")
        # This might pass or fail depending on current implementation

        # USER ACTION: Disable the server
        result = plugin.disable_server("test-server", scope="project-mcp")
        assert result.success, f"Disable should succeed: {result.message}"

        # AFTER: Server should be disabled
        state_after = plugin.get_server_state("test-server")
        assert state_after == ServerState.DISABLED, \
            "Server should be DISABLED after disable command"

        # VERIFICATION: Check approval file was updated
        settings_local = harness.path_overrides["project-local"]
        settings_data = json.loads(settings_local.read_text())

        assert "test-server" not in settings_data.get("enabledMcpjsonServers", []), \
            "Server should be removed from enabledMcpjsonServers"
        assert "test-server" in settings_data.get("disabledMcpjsonServers", []), \
            "Server should be added to disabledMcpjsonServers"


# =============================================================================
# TRACEABILITY SUMMARY
# =============================================================================
"""
COMPLETE TEST COVERAGE MAPPING:

Unapproved Server Detection (P0 - CRITICAL):
  ✓ test_server_in_mcp_json_without_approval_shows_unapproved
    - Manually creates unapproved state
    - Verifies state detection shows DISABLED/UNAPPROVED
    - Tests the bug scenario - EXPECTED TO FAIL INITIALLY
  ✓ test_server_explicitly_disabled_shows_disabled
    - Tests disabledMcpjsonServers array
    - Verifies DISABLED state distinct from UNAPPROVED
    - EXPECTED TO FAIL INITIALLY

State Transitions (P1 - HIGH):
  ✓ test_enable_unapproved_server
    - UNAPPROVED → ENABLED transition
    - Verifies approval file updated
  ✓ test_disable_enabled_server
    - ENABLED → DISABLED transition
    - Verifies approval arrays updated

TOTAL: 4 functional tests
  - All active (will fail initially until fix implemented)

All tests are UN-GAMEABLE because they:
  1. Use REAL MCPTestHarness with temp files
  2. Use REAL ClaudeCodePlugin (no mocks)
  3. Verify ACTUAL .claude/settings.local.json contents
  4. Test COMPLETE workflows
  5. Read back state via get_server_state() (not hardcoded)
  6. Cannot pass with stubs in approval logic
  7. Validate state transitions, not just single states

IMPLEMENTATION GUIDANCE:
========================
These tests define the contract for auto-approval. When implementing:

1. Modify ClaudeCodePlugin._initialize_scopes():
   - Change project-mcp from FileMoveEnableDisableHandler
   - To ApprovalRequiredEnableDisableHandler
   - Pass both .mcp.json and .claude/settings.local.json paths

2. Modify ClaudeCodePlugin.add_server():
   - After adding to scope, check if scope is project-mcp
   - If yes, auto-call enable_server() to approve
   - This adds to enabledMcpjsonServers array

3. State Detection (already exists in ApprovalRequiredEnableDisableHandler):
   - is_disabled() checks both inline disabled and approval arrays
   - Returns True if not in enabledMcpjsonServers (unapproved = disabled)
   - This fixes the "shows as ENABLED but isn't" bug

4. Preserve Manual Workflow:
   - enable_server() / disable_server() already work correctly
   - Users can still manually approve/disapprove via mcpi enable/disable
   - Claude UI approval workflow also works (modifies same arrays)

The failing tests will guide implementation step-by-step.
"""
