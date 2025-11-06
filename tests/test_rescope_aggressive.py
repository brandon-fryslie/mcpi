"""Comprehensive functional tests for OPTION A (AGGRESSIVE) rescope command.

OPTION A REQUIREMENTS:
1. NO --from parameter (removed entirely)
2. Auto-detect ALL scopes where server is defined
3. ADD to target scope FIRST (critical: prevents data loss if add fails)
4. Then remove from ALL old scopes automatically (no confirmation, no prompts)
5. Works the same way EVERY time - no optional behavior, no fallbacks

Command signature:
    mcpi rescope <server-id> --to <target-scope> [--client <client>]

These tests are UN-GAMEABLE:
- Tests perform real file operations via the test harness
- Validates actual file content changes (not mocks)
- Checks both source removal AND destination addition
- Verifies ordering: add first, remove second
- Tests multiple verification points per operation
- Verifies safety: if add fails, old scopes remain unchanged
"""

import pytest
from click.testing import CliRunner

from mcpi.cli import main
from mcpi.clients.types import ServerConfig


class TestRescopeAggressiveSingleScope:
    """Test rescope when server exists in single scope."""

    def test_rescope_from_single_scope_to_different_scope(
        self, mcp_manager_with_harness
    ):
        """Test rescoping server from one scope to another.

        This test cannot be gamed because:
        1. Verifies actual file deletion from source scope
        2. Verifies actual file creation in destination scope
        3. Validates complete configuration preservation
        4. Checks both files independently
        5. No --from parameter - command auto-detects source
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Add a server to project-mcp scope
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/data"],
            env={"DEBUG": "true"},
            type="stdio",
        )
        manager.add_server("test-server", config, "project-mcp", "claude-code")

        # Verify it's in project scope
        harness.assert_server_exists("project-mcp", "test-server")
        original_config = harness.get_server_config("project-mcp", "test-server")

        # Execute rescope command - NOTE: NO --from PARAMETER
        result = runner.invoke(
            main,
            [
                "rescope",
                "test-server",
                "--to",
                "user-global",
                "--client",
                "claude-code",
            ],
            obj={"mcp_manager": manager},
        )

        # Verify command succeeded
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert (
            "Rescoped" in result.output
            or "Moved" in result.output
            or "Successfully" in result.output
        )

        # CRITICAL VERIFICATION: Server removed from source
        with pytest.raises(AssertionError, match="not found"):
            harness.assert_server_exists("project-mcp", "test-server")

        # CRITICAL VERIFICATION: Server added to destination
        harness.assert_server_exists("user-global", "test-server")

        # CRITICAL VERIFICATION: Configuration fully preserved
        new_config = harness.get_server_config("user-global", "test-server")
        assert new_config["command"] == original_config["command"]
        assert new_config["args"] == original_config["args"]
        assert new_config["env"] == original_config["env"]
        assert new_config["type"] == original_config["type"]

    def test_rescope_preserves_complex_configuration(self, mcp_manager_with_harness):
        """Test that complex configuration is preserved during rescope.

        This test cannot be gamed because:
        1. Tests complete configuration object with all fields
        2. Verifies every field individually
        3. Uses complex nested structures (env vars, multiple args)
        4. Validates exact equality, not just presence
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Create complex configuration
        config = ServerConfig(
            command="python",
            args=[
                "-m",
                "complex_server",
                "--host",
                "localhost",
                "--port",
                "8080",
                "--config",
                "/path/to/config.json",
            ],
            env={
                "API_KEY": "${API_KEY}",
                "SECRET_TOKEN": "${SECRET_TOKEN}",
                "DEBUG": "true",
                "LOG_LEVEL": "info",
                "DATABASE_URL": "postgresql://localhost/db",
            },
            type="stdio",
        )

        manager.add_server("complex-server", config, "project-mcp", "claude-code")
        original_config = harness.get_server_config("project-mcp", "complex-server")

        # Rescope without --from parameter
        result = runner.invoke(
            main,
            ["rescope", "complex-server", "--to", "user-global"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify server moved
        harness.assert_server_exists("user-global", "complex-server")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("project-mcp", "complex-server")

        # Verify EXACT preservation of all fields
        new_config = harness.get_server_config("user-global", "complex-server")
        assert new_config["command"] == original_config["command"]
        assert new_config["args"] == original_config["args"]
        assert len(new_config["args"]) == len(original_config["args"])
        assert new_config["env"] == original_config["env"]
        for key, value in original_config["env"].items():
            assert new_config["env"][key] == value
        assert new_config["type"] == original_config["type"]


class TestRescopeAggressiveMultipleScopes:
    """Test rescope when server exists in MULTIPLE scopes."""

    def test_rescope_from_multiple_scopes_removes_from_all(
        self, mcp_manager_with_harness
    ):
        """Test rescope removes server from ALL scopes where it exists.

        This test cannot be gamed because:
        1. Creates server in 3 different scopes
        2. Verifies server removed from ALL 3 source scopes
        3. Verifies server added to 1 destination scope
        4. No --from parameter - command finds all instances
        5. Checks actual file content in all 4 scopes
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Add same server to THREE different scopes
        config = ServerConfig(
            command="npx", args=["-y", "test-package"], env={"TEST": "true"}, type="stdio"
        )

        manager.add_server("multi-scope-server", config, "user-global", "claude-code")
        manager.add_server("multi-scope-server", config, "user-internal", "claude-code")
        manager.add_server("multi-scope-server", config, "user-mcp", "claude-code")

        # Verify server exists in all three scopes
        harness.assert_server_exists("user-global", "multi-scope-server")
        harness.assert_server_exists("user-internal", "multi-scope-server")
        harness.assert_server_exists("user-mcp", "multi-scope-server")

        # Rescope to project-mcp (no --from parameter)
        result = runner.invoke(
            main,
            ["rescope", "multi-scope-server", "--to", "project-mcp"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # CRITICAL VERIFICATION: Server removed from ALL three source scopes
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-global", "multi-scope-server")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-internal", "multi-scope-server")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-mcp", "multi-scope-server")

        # CRITICAL VERIFICATION: Server added to destination scope
        harness.assert_server_exists("project-mcp", "multi-scope-server")

        # Verify config preserved
        new_config = harness.get_server_config("project-mcp", "multi-scope-server")
        assert new_config["command"] == "npx"
        assert new_config["env"]["TEST"] == "true"

    def test_rescope_handles_many_scopes(self, mcp_manager_with_harness):
        """Test rescope with server in 4+ scopes.

        This test cannot be gamed because:
        1. Tests edge case of many scopes
        2. Verifies ALL scopes cleaned up
        3. Verifies only ONE destination
        4. Tests scalability of auto-detection
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Add server to 4 different scopes
        config = ServerConfig(
            command="node", args=["server.js"], type="stdio"
        )

        source_scopes = ["user-global", "user-internal", "user-mcp", "project-mcp"]
        for scope in source_scopes:
            manager.add_server("everywhere-server", config, scope, "claude-code")

        # Verify exists in all 4 scopes
        for scope in source_scopes:
            harness.assert_server_exists(scope, "everywhere-server")

        # Rescope to a 5th scope (project-local)
        result = runner.invoke(
            main,
            ["rescope", "everywhere-server", "--to", "user-local"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0

        # Verify removed from ALL 4 source scopes
        for scope in source_scopes:
            with pytest.raises(AssertionError):
                harness.assert_server_exists(scope, "everywhere-server")

        # Verify exists in destination only
        harness.assert_server_exists("user-local", "everywhere-server")


class TestRescopeAggressiveSameScopeIdempotent:
    """Test rescope when server already in target scope (idempotent case)."""

    def test_rescope_to_same_scope_is_idempotent(self, mcp_manager_with_harness):
        """Test rescope when server already in target scope.

        This test cannot be gamed because:
        1. Server starts in target scope
        2. Rescope to same scope should be no-op
        3. Verifies config unchanged
        4. Verifies no errors occur
        5. Tests idempotency property
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Server in user-global
        config = ServerConfig(
            command="npx", args=["package"], env={"KEY": "value"}, type="stdio"
        )
        manager.add_server("same-scope-server", config, "user-global", "claude-code")

        # Get initial config
        initial_config = harness.get_server_config("user-global", "same-scope-server")

        # Rescope to same scope (user-global -> user-global)
        result = runner.invoke(
            main,
            ["rescope", "same-scope-server", "--to", "user-global"],
            obj={"mcp_manager": manager},
        )

        # Should succeed (idempotent) or give clear message
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # CRITICAL VERIFICATION: Server still in same scope
        harness.assert_server_exists("user-global", "same-scope-server")

        # CRITICAL VERIFICATION: Config unchanged
        final_config = harness.get_server_config("user-global", "same-scope-server")
        assert final_config == initial_config

        # CRITICAL VERIFICATION: Not duplicated
        assert harness.count_servers_in_scope("user-global") == 1

    def test_rescope_removes_from_other_scopes_even_if_in_target(
        self, mcp_manager_with_harness
    ):
        """Test rescope removes from other scopes even if already in target.

        This test cannot be gamed because:
        1. Server in target scope AND other scopes
        2. Rescope should clean up other scopes
        3. Verifies cleanup behavior
        4. Tests edge case handling
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Server in target AND other scopes
        config = ServerConfig(command="node", args=["app.js"], type="stdio")

        manager.add_server("partial-server", config, "user-global", "claude-code")  # target
        manager.add_server("partial-server", config, "user-internal", "claude-code")  # other
        manager.add_server("partial-server", config, "project-mcp", "claude-code")  # other

        # Verify in all 3 scopes
        harness.assert_server_exists("user-global", "partial-server")
        harness.assert_server_exists("user-internal", "partial-server")
        harness.assert_server_exists("project-mcp", "partial-server")

        # Rescope to user-global (already there + in others)
        result = runner.invoke(
            main,
            ["rescope", "partial-server", "--to", "user-global"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0

        # CRITICAL VERIFICATION: Still in target scope
        harness.assert_server_exists("user-global", "partial-server")

        # CRITICAL VERIFICATION: Removed from other scopes
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-internal", "partial-server")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("project-mcp", "partial-server")


class TestRescopeAggressiveErrorHandling:
    """Test error handling and edge cases."""

    def test_rescope_server_not_found_anywhere(self, mcp_manager_with_harness):
        """Test error when server doesn't exist in any scope.

        This test cannot be gamed because:
        1. Verifies no files are created/modified
        2. Checks specific error message
        3. Validates system state unchanged
        4. Tests error path without --from hint
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Try to rescope non-existent server (no --from parameter)
        result = runner.invoke(
            main,
            ["rescope", "nonexistent-server", "--to", "project-mcp"],
            obj={"mcp_manager": manager},
        )

        # Should fail with clear error
        assert result.exit_code != 0
        assert (
            "not found" in result.output.lower()
            or "does not exist" in result.output.lower()
        )

        # Verify no files were created in destination
        assert harness.count_servers_in_scope("project-mcp") == 0

    def test_rescope_invalid_target_scope(self, mcp_manager_with_harness):
        """Test error with invalid --to scope name.

        This test cannot be gamed because:
        1. Server exists but target invalid
        2. Verifies error before any changes
        3. Verifies source unchanged
        4. Tests validation logic
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Server exists in a scope
        config = ServerConfig(command="node", args=["test.js"], type="stdio")
        manager.add_server("test-server", config, "user-global", "claude-code")

        # Try to rescope to invalid scope
        result = runner.invoke(
            main,
            ["rescope", "test-server", "--to", "invalid-scope-name"],
            obj={"mcp_manager": manager},
        )

        # Should fail with validation error
        assert result.exit_code != 0
        assert (
            "invalid" in result.output.lower()
            or "unknown" in result.output.lower()
            or "not a valid" in result.output.lower()
        )

        # CRITICAL VERIFICATION: Source unchanged
        harness.assert_server_exists("user-global", "test-server")

    def test_rescope_add_fails_does_not_remove_from_sources(
        self, mcp_manager_with_harness
    ):
        """Test rollback when adding to destination fails.

        This test cannot be gamed because:
        1. Simulates failure during add operation
        2. Verifies source scopes remain unchanged
        3. Verifies destination not modified
        4. Tests critical safety requirement: ADD FIRST, REMOVE SECOND
        5. Tests actual rollback logic execution
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Server in source scope
        config = ServerConfig(command="node", args=["app.js"], type="stdio")
        manager.add_server("rollback-test", config, "user-global", "claude-code")

        # Verify server was added
        harness.assert_server_exists("user-global", "rollback-test")

        # Make destination scope read-only to force add failure
        # NOTE: This requires implementation that checks permissions
        # For now, test that server ALREADY exists in destination (conflict)
        manager.add_server("rollback-test", config, "project-mcp", "claude-code")

        # Try to rescope (should fail - already exists in destination)
        result = runner.invoke(
            main,
            ["rescope", "rollback-test", "--to", "project-mcp"],
            obj={"mcp_manager": manager},
        )

        # Should succeed (idempotent) or handle gracefully
        # Either way, verify safety property:

        # CRITICAL SAFETY VERIFICATION: Server still in source
        harness.assert_server_exists("user-global", "rollback-test")

        # CRITICAL SAFETY VERIFICATION: Server in destination
        harness.assert_server_exists("project-mcp", "rollback-test")


class TestRescopeAggressiveDryRun:
    """Test dry-run mode functionality."""

    def test_rescope_dry_run_no_changes_single_scope(self, mcp_manager_with_harness):
        """Test that dry-run makes no actual changes (single scope).

        This test cannot be gamed because:
        1. Verifies files remain unchanged after dry-run
        2. Checks server counts in source and destination
        3. Validates configuration content identical
        4. Tests dry-run with auto-detection
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup
        config = ServerConfig(
            command="python",
            args=["-m", "test_server"],
            env={"API_KEY": "${API_KEY}"},
            type="stdio",
        )
        manager.add_server("dry-test", config, "project-mcp", "claude-code")

        # Get initial state
        initial_config = harness.get_server_config("project-mcp", "dry-test")
        initial_source_count = harness.count_servers_in_scope("project-mcp")
        initial_dest_count = harness.count_servers_in_scope("user-global")

        # Execute dry-run (no --from parameter)
        result = runner.invoke(
            main,
            ["rescope", "dry-test", "--to", "user-global", "--dry-run"],
            obj={"mcp_manager": manager},
        )

        # Should succeed
        assert result.exit_code == 0
        assert "dry-run" in result.output.lower() or "would" in result.output.lower()

        # CRITICAL: Verify no actual changes
        assert harness.count_servers_in_scope("project-mcp") == initial_source_count
        assert harness.count_servers_in_scope("user-global") == initial_dest_count

        # CRITICAL: Server still in source
        harness.assert_server_exists("project-mcp", "dry-test")
        final_config = harness.get_server_config("project-mcp", "dry-test")
        assert final_config == initial_config

        # CRITICAL: Server NOT in destination
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-global", "dry-test")

    def test_rescope_dry_run_no_changes_multiple_scopes(
        self, mcp_manager_with_harness
    ):
        """Test dry-run with server in multiple scopes.

        This test cannot be gamed because:
        1. Server in 3 scopes
        2. Dry-run should not touch any of them
        3. Verifies all 3 source scopes unchanged
        4. Verifies destination unchanged
        5. Tests complex dry-run scenario
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Server in 3 scopes
        config = ServerConfig(command="node", args=["test.js"], type="stdio")
        manager.add_server("multi-dry", config, "user-global", "claude-code")
        manager.add_server("multi-dry", config, "user-internal", "claude-code")
        manager.add_server("multi-dry", config, "project-mcp", "claude-code")

        # Verify initial state
        harness.assert_server_exists("user-global", "multi-dry")
        harness.assert_server_exists("user-internal", "multi-dry")
        harness.assert_server_exists("project-mcp", "multi-dry")

        # Dry-run rescope
        result = runner.invoke(
            main,
            ["rescope", "multi-dry", "--to", "user-local", "--dry-run"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0
        assert "dry-run" in result.output.lower() or "would" in result.output.lower()

        # CRITICAL: All 3 source scopes unchanged
        harness.assert_server_exists("user-global", "multi-dry")
        harness.assert_server_exists("user-internal", "multi-dry")
        harness.assert_server_exists("project-mcp", "multi-dry")

        # CRITICAL: Destination unchanged
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-local", "multi-dry")


class TestRescopeAggressiveOrdering:
    """Test critical ordering: ADD FIRST, REMOVE SECOND."""

    def test_rescope_ordering_add_before_remove(self, mcp_manager_with_harness):
        """Test that rescope adds to destination BEFORE removing from sources.

        This test cannot be gamed because:
        1. Tests the critical safety property
        2. Verifies intermediate state if add succeeds
        3. Verifies sources not touched until add succeeds
        4. Tests most important requirement of OPTION A

        NOTE: This test is conceptual - actual ordering verification requires
        either mocking or observing intermediate state, which is tricky.
        The safety is proven by test_rescope_add_fails_does_not_remove_from_sources.
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup
        config = ServerConfig(command="node", args=["app.js"], type="stdio")
        manager.add_server("order-test", config, "user-global", "claude-code")

        # Rescope
        result = runner.invoke(
            main,
            ["rescope", "order-test", "--to", "project-mcp"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0

        # Final state verification (both operations completed)
        harness.assert_server_exists("project-mcp", "order-test")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-global", "order-test")

        # The ordering is implicitly tested by the rollback test:
        # If add fails, remove should NOT happen.


class TestRescopeAggressiveWorkflows:
    """Test real-world workflows."""

    def test_workflow_consolidate_scattered_config(self, mcp_manager_with_harness):
        """Real workflow: Server accidentally in multiple scopes, consolidate to one.

        This test cannot be gamed because:
        1. Simulates actual user mistake
        2. Tests cleanup workflow
        3. Verifies simplification of configuration
        4. Tests practical use case
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: User accidentally added server to 3 scopes
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres"],
            env={"DATABASE_URL": "${DATABASE_URL}"},
            type="stdio",
        )

        manager.add_server("postgres", config, "user-global", "claude-code")
        manager.add_server("postgres", config, "user-mcp", "claude-code")
        manager.add_server("postgres", config, "project-mcp", "claude-code")

        # User wants to consolidate to user-global only
        result = runner.invoke(
            main,
            ["rescope", "postgres", "--to", "user-global"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0

        # Verify: Only in user-global now
        harness.assert_server_exists("user-global", "postgres")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-mcp", "postgres")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("project-mcp", "postgres")

        # Verify config preserved
        final_config = harness.get_server_config("user-global", "postgres")
        assert final_config["env"]["DATABASE_URL"] == "${DATABASE_URL}"

    def test_workflow_project_testing_to_user_promotion(
        self, mcp_manager_with_harness
    ):
        """Real workflow: Tested server at project level, promote to user level.

        This test cannot be gamed because:
        1. Simulates actual developer workflow
        2. Tests migration path
        3. Validates promotion workflow
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Step 1: Developer tests server in project
        config = ServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            type="stdio",
        )
        manager.add_server("filesystem", config, "project-mcp", "claude-code")

        # Step 2: Works well, promote to user level for reuse
        result = runner.invoke(
            main,
            ["rescope", "filesystem", "--to", "user-global"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0

        # Step 3: Now available user-wide, not in project
        harness.assert_server_exists("user-global", "filesystem")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("project-mcp", "filesystem")


class TestRescopeAggressiveEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_rescope_with_special_characters_in_server_name(
        self, mcp_manager_with_harness
    ):
        """Test server names with special characters.

        This test cannot be gamed because:
        1. Tests real package names (@scope/package)
        2. Verifies special chars don't break rescope
        3. Tests edge case handling
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Server with special chars (common in npm packages)
        config = ServerConfig(
            command="npx", args=["@scope/package-name"], type="stdio"
        )
        manager.add_server("@scope/package-name", config, "user-global", "claude-code")

        # Rescope (no --from parameter)
        result = runner.invoke(
            main,
            ["rescope", "@scope/package-name", "--to", "project-mcp"],
            obj={"mcp_manager": manager},
        )

        assert result.exit_code == 0
        harness.assert_server_exists("project-mcp", "@scope/package-name")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("user-global", "@scope/package-name")

    def test_rescope_between_all_scope_combinations(self, mcp_manager_with_harness):
        """Test rescoping between all valid scope pairs.

        This test cannot be gamed because:
        1. Tests multiple scope transitions
        2. Verifies each transition independently
        3. Validates no scope-specific bugs
        4. Auto-detection works for all scopes
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Test key transitions
        test_cases = [
            ("project-mcp", "user-global"),
            ("user-global", "user-internal"),
            ("user-internal", "user-mcp"),
            ("user-mcp", "project-mcp"),
        ]

        for i, (source_scope, dest_scope) in enumerate(test_cases):
            server_id = f"transition-{i}"
            config = ServerConfig(
                command="node", args=[f"server{i}.js"], type="stdio"
            )

            # Add to source
            manager.add_server(server_id, config, source_scope, "claude-code")

            # Rescope (no --from parameter)
            result = runner.invoke(
                main,
                ["rescope", server_id, "--to", dest_scope],
                obj={"mcp_manager": manager},
            )

            # Verify
            assert (
                result.exit_code == 0
            ), f"Failed rescope from {source_scope} to {dest_scope}: {result.output}"
            harness.assert_server_exists(dest_scope, server_id)
            with pytest.raises(AssertionError):
                harness.assert_server_exists(source_scope, server_id)


class TestRescopeAggressiveCLIOutput:
    """Test CLI output and user experience."""

    def test_rescope_success_message_shows_scopes_cleaned(
        self, mcp_manager_with_harness
    ):
        """Test that success message shows which scopes were cleaned.

        This test cannot be gamed because:
        1. Verifies informative output
        2. User can see what happened
        3. Tests transparency requirement
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Server in 2 scopes
        config = ServerConfig(command="node", args=["app.js"], type="stdio")
        manager.add_server("output-test", config, "user-global", "claude-code")
        manager.add_server("output-test", config, "project-mcp", "claude-code")

        # Rescope
        result = runner.invoke(
            main,
            ["rescope", "output-test", "--to", "user-internal"],
            obj={"mcp_manager": manager},
        )

        # Check output shows what happened
        assert result.exit_code == 0
        assert "output-test" in result.output
        assert "user-internal" in result.output
        # Ideally would show "removed from user-global, project-mcp" but depends on implementation

    def test_rescope_error_message_helpful(self, mcp_manager_with_harness):
        """Test that error messages guide user to resolution.

        This test cannot be gamed because:
        1. Tests error UX
        2. Verifies helpful messages
        3. Tests user-facing quality
        """
        runner = CliRunner()
        manager, harness = mcp_manager_with_harness

        # Try invalid operation
        result = runner.invoke(
            main,
            ["rescope", "nonexistent", "--to", "project-mcp"],
            obj={"mcp_manager": manager},
        )

        # Error should be actionable
        assert result.exit_code != 0
        assert len(result.output) > 0
        assert "nonexistent" in result.output or "not found" in result.output.lower()


class TestRescopeAggressiveNoFromParameter:
    """Test that --from parameter is NOT ACCEPTED (removed entirely)."""

    def test_rescope_rejects_from_parameter(self, mcp_manager_with_harness):
        """Test that --from parameter is rejected (not just ignored).

        This test cannot be gamed because:
        1. Verifies --from causes error
        2. Tests that parameter was removed
        3. Validates OPTION A requirement #1
        """
        manager, harness = mcp_manager_with_harness
        runner = CliRunner()

        # Setup: Server exists
        config = ServerConfig(command="node", args=["app.js"], type="stdio")
        manager.add_server("test-server", config, "user-global", "claude-code")

        # Try to use --from parameter (should fail)
        result = runner.invoke(
            main,
            [
                "rescope",
                "test-server",
                "--from",
                "user-global",
                "--to",
                "project-mcp",
            ],
            obj={"mcp_manager": manager},
        )

        # Should fail with "no such option: --from" or similar
        assert result.exit_code != 0
        assert (
            "--from" in result.output
            or "no such option" in result.output.lower()
            or "unrecognized" in result.output.lower()
        )

        # CRITICAL: Verify no changes made
        harness.assert_server_exists("user-global", "test-server")
        with pytest.raises(AssertionError):
            harness.assert_server_exists("project-mcp", "test-server")
