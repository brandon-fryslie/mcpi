# Functional Tests for Rescope OPTION A (AGGRESSIVE)

**Date**: 2025-11-05
**Test File**: `tests/test_rescope_aggressive.py`
**Command Spec**: `mcpi rescope <server-id> --to <target-scope> [--client <client>]`

---

## OPTION A Requirements

### Core Behavior
1. **NO --from parameter** - removed entirely from command signature
2. **Auto-detect ALL scopes** where server is defined (no user input needed)
3. **ADD to target scope FIRST** (critical safety: prevents data loss if add fails)
4. **Then remove from ALL old scopes** automatically (no confirmation, no prompts)
5. **Works the same way EVERY time** - no optional behavior, no fallbacks

### Critical Ordering for Safety
```
Step 1: Add server config to target scope (--to)
Step 2: ONLY IF step 1 succeeds, remove from all old scopes
```

This prevents the user from losing their configuration entirely if the add operation fails.

---

## Test Coverage Matrix

### Test Class: `TestRescopeAggressiveSingleScope`
**Scenario**: Server exists in one scope only

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_from_single_scope_to_different_scope` | Basic rescope works | - Verifies actual file deletion from source<br>- Verifies actual file creation in destination<br>- Validates complete config preservation<br>- No --from parameter |
| `test_rescope_preserves_complex_configuration` | Complex configs preserved | - Tests all config fields (command, args, env)<br>- Verifies exact equality<br>- Uses nested structures (5 env vars, 7 args) |

### Test Class: `TestRescopeAggressiveMultipleScopes`
**Scenario**: Server exists in MULTIPLE scopes (key OPTION A behavior)

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_from_multiple_scopes_removes_from_all` | Removes from ALL 3 source scopes | - Creates in 3 different scopes<br>- Verifies removal from ALL 3<br>- Verifies addition to 1 destination<br>- Checks actual file content in all 4 scopes |
| `test_rescope_handles_many_scopes` | Scales to 4+ scopes | - Tests with 4 source scopes<br>- Verifies ALL cleaned up<br>- Only ONE destination |

### Test Class: `TestRescopeAggressiveSameScopeIdempotent`
**Scenario**: Server already in target scope

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_to_same_scope_is_idempotent` | Idempotent operation | - Config unchanged<br>- No errors<br>- Not duplicated<br>- Tests no-op behavior |
| `test_rescope_removes_from_other_scopes_even_if_in_target` | Cleans up other scopes | - Server in target + 2 others<br>- Verifies cleanup of 2 others<br>- Tests edge case |

### Test Class: `TestRescopeAggressiveErrorHandling`
**Scenario**: Error cases

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_server_not_found_anywhere` | Error when server missing | - No files created<br>- Clear error message<br>- System unchanged |
| `test_rescope_invalid_target_scope` | Invalid --to scope | - Error before changes<br>- Source unchanged<br>- Validation logic |
| `test_rescope_add_fails_does_not_remove_from_sources` | **CRITICAL SAFETY**: Add fails → sources unchanged | - Simulates add failure<br>- Sources remain unchanged<br>- Destination not modified<br>- Tests ADD FIRST, REMOVE SECOND |

### Test Class: `TestRescopeAggressiveDryRun`
**Scenario**: Dry-run mode

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_dry_run_no_changes_single_scope` | Dry-run makes no changes (1 scope) | - Files unchanged<br>- Server counts unchanged<br>- Config identical |
| `test_rescope_dry_run_no_changes_multiple_scopes` | Dry-run with 3 scopes | - All 3 sources unchanged<br>- Destination unchanged<br>- Complex scenario |

### Test Class: `TestRescopeAggressiveOrdering`
**Scenario**: Critical ordering requirement

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_ordering_add_before_remove` | ADD happens BEFORE REMOVE | - Verifies final state<br>- Safety proven by rollback test<br>- Most important requirement |

### Test Class: `TestRescopeAggressiveWorkflows`
**Scenario**: Real-world use cases

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_workflow_consolidate_scattered_config` | Cleanup scattered config | - Server in 3 scopes<br>- Consolidate to 1<br>- Simulates user mistake |
| `test_workflow_project_testing_to_user_promotion` | Project → user promotion | - Developer workflow<br>- Migration path<br>- Practical use |

### Test Class: `TestRescopeAggressiveEdgeCases`
**Scenario**: Edge cases

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_with_special_characters_in_server_name` | Special chars (@scope/package) | - Real npm package names<br>- Special chars don't break |
| `test_rescope_between_all_scope_combinations` | All scope transitions | - 4 different transitions<br>- Independent verification<br>- Auto-detection works everywhere |

### Test Class: `TestRescopeAggressiveCLIOutput`
**Scenario**: User experience

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_success_message_shows_scopes_cleaned` | Informative success message | - Shows what happened<br>- User sees scopes cleaned<br>- Transparency |
| `test_rescope_error_message_helpful` | Helpful error messages | - Error UX<br>- Actionable messages<br>- User-facing quality |

### Test Class: `TestRescopeAggressiveNoFromParameter`
**Scenario**: Verify --from removed

| Test | Validates | Un-Gameable Because |
|------|-----------|---------------------|
| `test_rescope_rejects_from_parameter` | **OPTION A REQ #1**: --from rejected | - --from causes error<br>- Parameter removed<br>- No changes if --from used |

---

## Un-Gameable Properties

### 1. Real File Operations
- Tests use `MCPTestHarness` which performs actual file I/O
- No mocks for file operations
- Tests verify actual JSON file content
- Cannot fake by mocking

### 2. Multiple Verification Points
Each test verifies:
- Source file(s) modified correctly
- Destination file modified correctly
- Configuration content preserved
- Server counts accurate
- No side effects in other scopes

### 3. Actual Configuration Preservation
- Tests with complex configs (5 env vars, 7 args)
- Verifies every field individually
- Checks exact equality, not just presence
- Cannot satisfy with stub data

### 4. Safety Property Testing
- `test_rescope_add_fails_does_not_remove_from_sources` explicitly tests:
  - If add fails, remove doesn't happen
  - Sources remain unchanged
  - No data loss occurs
- This is the CRITICAL safety requirement

### 5. Edge Case Coverage
- Multiple scopes (3-4 scopes)
- Same scope (idempotent)
- No scopes (error)
- Invalid scope (validation)
- Special characters
- All scope combinations

---

## Test Scenarios Summary

| Scenario | Test Count | Critical? | Validates |
|----------|------------|-----------|-----------|
| Single scope move | 2 | YES | Basic functionality |
| Multiple scopes move | 2 | **CRITICAL** | Core OPTION A behavior |
| Same scope (idempotent) | 2 | YES | No-op handling |
| Error handling | 3 | **CRITICAL** | Safety & validation |
| Dry-run mode | 2 | YES | Preview without changes |
| Ordering verification | 1 | **CRITICAL** | ADD FIRST, REMOVE SECOND |
| Real workflows | 2 | YES | Practical use cases |
| Edge cases | 2 | YES | Robustness |
| CLI output | 2 | NO | User experience |
| --from parameter removed | 1 | **CRITICAL** | OPTION A requirement |
| **TOTAL** | **19** | **10 critical** | **Full OPTION A spec** |

---

## Critical Tests (Must Pass)

These 10 tests validate the core OPTION A requirements and safety properties:

1. **`test_rescope_from_single_scope_to_different_scope`** - Basic functionality works
2. **`test_rescope_from_multiple_scopes_removes_from_all`** - Core OPTION A: removes from ALL scopes
3. **`test_rescope_to_same_scope_is_idempotent`** - Idempotent (no errors on same scope)
4. **`test_rescope_server_not_found_anywhere`** - Error handling for missing server
5. **`test_rescope_invalid_target_scope`** - Validation before changes
6. **`test_rescope_add_fails_does_not_remove_from_sources`** - **CRITICAL SAFETY**: ADD FIRST, REMOVE SECOND
7. **`test_rescope_ordering_add_before_remove`** - Ordering requirement
8. **`test_rescope_handles_many_scopes`** - Scalability (4+ scopes)
9. **`test_rescope_removes_from_other_scopes_even_if_in_target`** - Cleanup even if in target
10. **`test_rescope_rejects_from_parameter`** - --from parameter removed

---

## What Implementation Must Do

Based on these tests, the rescope command must:

### Command Signature
```python
@main.command()
@click.argument("server_name", shell_complete=complete_rescope_server_name)
@click.option(
    "--to",
    "to_scope",
    required=True,
    type=DynamicScopeType(),
    help="Destination scope to move to",
)
@click.option(
    "--client",
    default=None,
    shell_complete=complete_client_names,
    help="MCP client to use (auto-detected if not specified)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would happen without making changes"
)
@click.pass_context
def rescope(
    ctx: click.Context,
    server_name: str,
    to_scope: str,
    client: Optional[str],
    dry_run: bool,
) -> None:
```

**NOTE**: NO `from_scope` parameter!

### Algorithm
```python
def rescope(ctx, server_name, to_scope, client, dry_run):
    # 1. Get manager and client
    manager = get_mcp_manager(ctx)
    client_name = client or manager.default_client

    # 2. Validate to_scope is valid for client
    # (DynamicScopeType does this)

    # 3. Find server in ALL scopes (auto-detect)
    all_servers = manager.list_servers(client_name=client_name)
    source_scopes = []
    for qualified_id, server_info in all_servers.items():
        if server_info.id == server_name:
            source_scopes.append(server_info.scope)

    if not source_scopes:
        raise error("Server not found in any scope")

    # 4. Get server config from first source
    server_config = ... # from any source scope

    # 5. Check if already in target scope
    if to_scope in source_scopes:
        # Idempotent case: remove from others only
        source_scopes.remove(to_scope)
        if not source_scopes:
            # Already only in target, no-op
            return success("Server already in target scope")

    # 6. Dry-run exit
    if dry_run:
        show_what_would_happen()
        return

    # 7. CRITICAL: ADD FIRST (safety requirement)
    if to_scope not in [s for _, info in all_servers.items() if info.id == server_name for s in [info.scope]]:
        add_result = manager.add_server(server_name, server_config, to_scope, client_name)
        if not add_result.success:
            raise error("Failed to add to target: " + add_result.message)

    # 8. THEN REMOVE FROM ALL OLD SCOPES (only after add succeeds)
    for source_scope in source_scopes:
        remove_result = manager.remove_server(server_name, source_scope, client_name)
        if not remove_result.success:
            # Rollback: try to remove from target
            # (though this is partial failure - need transaction support)
            raise error("Failed to remove from source: " + remove_result.message)

    # 9. Success
    return success(f"Rescoped {server_name} to {to_scope}")
```

### Key Properties
1. **No --from parameter** - command auto-detects
2. **Finds ALL source scopes** - not just one
3. **Adds to target FIRST** - safety requirement
4. **Removes from ALL sources** - cleanup requirement
5. **Idempotent** - safe to run multiple times
6. **Validates target scope** - before any changes
7. **Dry-run support** - preview changes

---

## Running the Tests

```bash
# Run all rescope OPTION A tests
pytest tests/test_rescope_aggressive.py -v

# Run critical tests only
pytest tests/test_rescope_aggressive.py -v -k "critical or safety or multiple_scopes or from_parameter"

# Run with coverage
pytest tests/test_rescope_aggressive.py --cov=src/mcpi/cli --cov-report=term

# Run specific test class
pytest tests/test_rescope_aggressive.py::TestRescopeAggressiveMultipleScopes -v
```

---

## Expected Initial Results

**Before implementation**: All 19 tests should FAIL because:
1. Current implementation has `--from` parameter (required)
2. Current implementation doesn't auto-detect multiple scopes
3. Current implementation doesn't remove from ALL scopes

**After implementation**: All 19 tests should PASS, proving:
1. --from parameter removed
2. Auto-detection works
3. Removes from ALL scopes
4. ADD FIRST, REMOVE SECOND ordering
5. Idempotent behavior
6. Error handling
7. Dry-run support

---

## Integration with Planning Documents

### STATUS Gaps Addressed
From `STATUS-2025-10-30-062049.md`, these tests address:
- GAP #2: Unknown command functionality - provides comprehensive test coverage
- GAP #3: 82 test failures - adds functional tests that can't be gamed

### PLAN Items Validated
From `PLAN-2025-10-30-062544.md`, these tests support:
- P0-EMERGENCY-2: Verify actual command functionality
- P2-CLEANUP-2: Add packaging tests (functional level)
- P0-SHIP criteria: All commands tested and documented

### Traceability
```json
{
  "tests_added": [
    "TestRescopeAggressiveSingleScope",
    "TestRescopeAggressiveMultipleScopes",
    "TestRescopeAggressiveSameScopeIdempotent",
    "TestRescopeAggressiveErrorHandling",
    "TestRescopeAggressiveDryRun",
    "TestRescopeAggressiveOrdering",
    "TestRescopeAggressiveWorkflows",
    "TestRescopeAggressiveEdgeCases",
    "TestRescopeAggressiveCLIOutput",
    "TestRescopeAggressiveNoFromParameter"
  ],
  "workflows_covered": [
    "rescope from single scope",
    "rescope from multiple scopes (core OPTION A)",
    "rescope to same scope (idempotent)",
    "rescope with add failure (safety)",
    "rescope dry-run",
    "consolidate scattered config",
    "project to user promotion"
  ],
  "initial_status": "failing",
  "commit": "pending",
  "gaming_resistance": "high",
  "status_gaps_addressed": [
    "GAP #2: Unknown command functionality",
    "Need for un-gameable functional tests"
  ],
  "plan_items_validated": [
    "P0-EMERGENCY-2: Verify actual command functionality",
    "P2-CLEANUP-2: Functional test coverage"
  ],
  "critical_requirements": [
    "NO --from parameter (OPTION A req #1)",
    "Auto-detect ALL scopes (OPTION A req #2)",
    "ADD to target FIRST (OPTION A req #3)",
    "Remove from ALL old scopes (OPTION A req #4)",
    "Works same every time (OPTION A req #5)"
  ]
}
```

---

## Success Criteria

The OPTION A implementation is correct when:
- [ ] All 19 tests pass
- [ ] No --from parameter in command signature
- [ ] Auto-detection finds all source scopes
- [ ] Server added to target before removing from sources
- [ ] All source scopes cleaned up
- [ ] Idempotent (safe to run multiple times)
- [ ] Helpful error messages
- [ ] Dry-run shows what would happen
- [ ] Complex configurations preserved exactly
- [ ] Special characters handled

---

## Notes for Implementation

### Transaction Safety
The current test `test_rescope_add_fails_does_not_remove_from_sources` tests the safety property but relies on the implementation to:
1. Add to target first
2. Only remove from sources if add succeeds
3. Ideally rollback on failure

For true transaction safety, consider:
- Backup source configs before removing
- Rollback if remove fails
- Atomic file operations where possible

### Error Messages
Tests verify error messages exist but not exact text. Implementation should provide:
- "Server 'X' not found in any scope"
- "'invalid-scope' is not a valid scope for client 'claude-code'"
- Clear indication of what scopes were cleaned up

### Output Format
Success output should show:
- Server name
- Target scope
- Source scopes cleaned up (ideally list them)
- Client used

Example: "Rescoped 'test-server' to user-global (removed from project-mcp, user-internal)"

---

**Test Suite Complete**: 2025-11-05
**Ready for Implementation**: YES
**Test File**: `tests/test_rescope_aggressive.py`
**Test Count**: 19 tests (10 critical)
**Coverage**: Full OPTION A specification
