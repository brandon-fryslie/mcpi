# Enable/Disable Bugs - Test Documentation

**Date**: 2025-10-29
**Test File**: `tests/test_enable_disable_bugs.py`
**Status**: Tests written and failing (as expected - bugs not yet fixed)

## Overview

This test suite provides comprehensive functional tests for three critical bugs in the enable/disable functionality:

1. **BUG-1: Cross-Scope State Pollution** (CRITICAL)
2. **BUG-3: Wrong Scope Modification** (CRITICAL)
3. **BUG-ORIG: TypeError in client info** (documented for CLI tests)

## Test Results Summary

**Initial Test Run**: 2025-10-29

```
Tests: 11 total
- FAILED: 7 tests (bugs detected correctly!)
- PASSED: 3 tests (baseline functionality works)
- SKIPPED: 1 test (CLI test placeholder)

Status: EXPECTED - Tests fail because bugs are not yet fixed
```

### Failed Tests (Catching Bugs)

#### BUG-1: Cross-Scope State Pollution (2 failures)

1. ✗ `test_user_global_server_state_not_polluted_by_user_local_disabled_array`
   - **Expected**: user-global server shows ENABLED
   - **Actual**: Shows DISABLED (polluted by user-local's disabled array)
   - **Verification**: This is BUG-1 in action!

2. ✗ `test_multiple_scopes_maintain_independent_state`
   - **Expected**: Each scope maintains independent state
   - **Actual**: user-global server polluted by user-local
   - **Verification**: Cross-scope pollution confirmed

#### BUG-3: Wrong Scope Modification (5 failures)

3. ✗ `test_disable_server_in_user_local_modifies_correct_scope`
   - **Expected**: Server added to user-local's disabled array
   - **Actual**: Server not added (wrong scope modified)
   - **Verification**: This is BUG-3 - modifies wrong scope

4. ✗ `test_enable_server_in_user_local_modifies_correct_scope`
   - **Expected**: Server removed from disabled array, added to enabled
   - **Actual**: Arrays not modified correctly
   - **Verification**: Enable operation has same bug

5. ✗ `test_enable_disable_operations_are_idempotent`
   - **Expected**: Repeated operations work safely
   - **Actual**: First disable doesn't work, so idempotency fails
   - **Verification**: Cascading failure from BUG-3

6. ✗ `test_list_shows_correct_state_for_each_scope`
   - **Expected**: All servers show correct state
   - **Actual**: user-global servers show wrong state
   - **Verification**: User-facing symptom of BUG-1

7. ✗ `test_list_with_scope_filter_shows_only_that_scope`
   - **Expected**: Filtered list shows correct state
   - **Actual**: State still polluted in filtered view
   - **Verification**: Scope filtering doesn't fix pollution

### Passing Tests (Baseline Works)

1. ✓ `test_user_local_server_state_correctly_reflects_own_disabled_array`
   - user-local scope works correctly (has enable/disable arrays)

2. ✓ `test_user_global_server_with_no_disable_arrays_shows_enabled`
   - Works when no pollution exists

3. ✓ `test_disable_server_in_user_global_returns_error`
   - Correctly prevents modification of unsupported scope
   - NOTE: Doesn't modify wrong scope (good!)

### Skipped Test

1. ⊘ `test_client_info_with_error_response_no_typeerror`
   - Documented for CLI test suite implementation
   - BUG-ORIG belongs in `test_cli.py`

## Test Design: Gaming Resistance

These tests are **UN-GAMEABLE** because they:

### 1. Real File I/O
- All tests use `mcp_harness` fixture for actual file operations
- Files created in temporary directories with real JSON content
- File contents verified before and after operations
- No mocks or stubs of file operations

### 2. Observable Behavior
- Tests verify what users would actually see
- ServerState enum values (ENABLED, DISABLED, NOT_INSTALLED)
- File contents match expected configuration
- Error messages checked for clarity

### 3. Side Effect Verification
- Check that ONLY the target scope was modified
- Verify other scopes remain unchanged
- Confirm array contents after operations
- Validate idempotency (safe to repeat operations)

### 4. Multiple Verification Points
Each test verifies:
- Setup is correct (files created as expected)
- Operation result (success/failure)
- Primary outcome (state, file contents)
- Side effects (no unintended modifications)
- Error messages (clear and helpful)

### 5. Cannot Pass With:
- ✗ Stub implementations
- ✗ Hardcoded return values
- ✗ Mocked file operations
- ✗ Implementation shortcuts
- ✗ Cross-scope pollution
- ✗ Wrong scope modifications

## Test Coverage Mapping

### BUG-1: Cross-Scope State Pollution

| Test | Aspect Tested | Bug Verification |
|------|---------------|------------------|
| `test_user_global_server_state_not_polluted_by_user_local_disabled_array` | Core bug scenario | Directly tests pollution |
| `test_user_local_server_state_correctly_reflects_own_disabled_array` | Positive case | Verifies local arrays work |
| `test_user_global_server_with_no_disable_arrays_shows_enabled` | Baseline | Verifies default state |
| `test_multiple_scopes_maintain_independent_state` | Comprehensive | Tests all scopes simultaneously |
| `test_list_shows_correct_state_for_each_scope` | User-facing | What users actually see |

**Coverage**: 5/5 tests verify state is scope-specific

### BUG-3: Wrong Scope Modification

| Test | Aspect Tested | Bug Verification |
|------|---------------|------------------|
| `test_disable_server_in_user_global_returns_error` | Unsupported scope | Error handling |
| `test_disable_server_in_user_local_modifies_correct_scope` | Correct scope | Verifies right file modified |
| `test_enable_server_in_user_local_modifies_correct_scope` | Enable operation | Both enable and disable |
| `test_enable_disable_operations_are_idempotent` | Repeated ops | Safe to run multiple times |

**Coverage**: 4/4 tests verify operations modify correct scope only

## Running the Tests

### Run All Enable/Disable Bug Tests
```bash
pytest tests/test_enable_disable_bugs.py -v
```

### Run Specific Bug Category
```bash
# BUG-1: Cross-scope pollution
pytest tests/test_enable_disable_bugs.py::TestCrossScopeStatePollution -v

# BUG-3: Wrong scope modification
pytest tests/test_enable_disable_bugs.py::TestWrongScopeModification -v

# User-facing list behavior
pytest tests/test_enable_disable_bugs.py::TestListServersWithCorrectState -v
```

### Run Single Test
```bash
pytest tests/test_enable_disable_bugs.py::TestCrossScopeStatePollution::test_user_global_server_state_not_polluted_by_user_local_disabled_array -v
```

### Watch Mode (Run on File Changes)
```bash
pytest-watch tests/test_enable_disable_bugs.py -v
```

## Expected Test Lifecycle

### Phase 1: Before Bug Fix (CURRENT)
```
Status: 7 failed, 3 passed, 1 skipped
Result: Tests correctly identify bugs
Action: Fix implementation in claude_code.py
```

### Phase 2: After BUG-1 Fix
```
Expected: 5 tests pass (cross-scope pollution fixed)
Still failing: 2 tests (BUG-3 not yet fixed)
Action: Verify BUG-1 fix, continue to BUG-3
```

### Phase 3: After BUG-3 Fix
```
Expected: 10 tests pass, 1 skipped
Result: All bugs fixed!
Action: Ship to production
```

### Phase 4: Regression Prevention
```
Status: All tests pass
Purpose: Prevent re-introduction of bugs
Run: In CI/CD pipeline on every commit
```

## Bug Fix Implementation Guide

### Fixing BUG-1: Cross-Scope State Pollution

**File**: `src/mcpi/clients/claude_code.py`
**Location**: Lines 167-205 (`_get_server_state()`)

**Problem**: Function checks ALL scopes for enable/disable arrays

**Solution**: Make function scope-aware
```python
def _get_server_state(self, server_id: str, scope: str) -> ServerState:
    """Get server state (SCOPE-AWARE)"""
    handler = self._scopes[scope]
    if not handler.exists():
        return ServerState.NOT_INSTALLED

    data = handler.reader.read(handler.config.path)

    # Only check arrays if THIS scope has them
    if "disabledMcpjsonServers" in data:
        if server_id in data["disabledMcpjsonServers"]:
            return ServerState.DISABLED

    if "enabledMcpjsonServers" in data:
        if server_id in data["enabledMcpjsonServers"]:
            return ServerState.ENABLED

    # Check if server exists in mcpServers
    if "mcpServers" in data and server_id in data["mcpServers"]:
        return ServerState.ENABLED

    return ServerState.NOT_INSTALLED
```

**Tests that verify fix**:
- `test_user_global_server_state_not_polluted_by_user_local_disabled_array`
- `test_multiple_scopes_maintain_independent_state`
- `test_list_shows_correct_state_for_each_scope`

### Fixing BUG-3: Wrong Scope Modification

**File**: `src/mcpi/clients/claude_code.py`
**Location**: Lines 323-427 (`enable_server()`, `disable_server()`)

**Problem**: Functions modify first scope found, not server's actual scope

**Solution**: Find server's scope first, check if it supports enable/disable
```python
def _find_server_scope(self, server_id: str) -> Optional[str]:
    """Find which scope contains the server"""
    for scope_name, handler in self._scopes.items():
        if not handler.exists():
            continue
        data = handler.reader.read(handler.config.path)
        if "mcpServers" in data and server_id in data["mcpServers"]:
            return scope_name
    return None

def disable_server(self, server_id: str) -> OperationResult:
    """Disable server (SCOPE-AWARE)"""
    # Find server's actual scope
    actual_scope = self._find_server_scope(server_id)
    if not actual_scope:
        return OperationResult.failure_result(
            f"Server {server_id} not found in any scope"
        )

    # Check if scope supports enable/disable
    handler = self._scopes[actual_scope]
    data = handler.reader.read(handler.config.path)

    if "disabledMcpjsonServers" not in data:
        return OperationResult.failure_result(
            f"Enable/disable not supported for scope '{actual_scope}'. "
            f"To disable this server, remove it from the config file."
        )

    # Proceed with disable operation...
```

**Tests that verify fix**:
- `test_disable_server_in_user_local_modifies_correct_scope`
- `test_enable_server_in_user_local_modifies_correct_scope`
- `test_enable_disable_operations_are_idempotent`

## Traceability

### Planning Documents
- **Evaluation**: `.agent_planning/EVALUATION-ENABLE-DISABLE-2025-10-28-CORRECTED.md`
- **Bug Fix Plan**: `.agent_planning/BUG-FIX-PLAN-ENABLE-DISABLE.md`
- **Bug Report**: `.agent_planning/BUG-REPORT-CROSS-SCOPE-POLLUTION.md`

### Source Files Under Test
- `src/mcpi/clients/claude_code.py` (main plugin implementation)
- `src/mcpi/clients/file_based.py` (scope handlers)
- `src/mcpi/clients/types.py` (ServerState, ServerInfo)

### Test Infrastructure
- `tests/test_harness.py` (MCPTestHarness, fixtures)
- `tests/conftest.py` (shared fixtures)

## Success Criteria

### Before Fix
- ✓ Tests fail with clear bug descriptions
- ✓ Failure messages match expected bug behavior
- ✓ No false positives (passing tests should pass)

### After Fix
- ☐ All BUG-1 tests pass (5 tests)
- ☐ All BUG-3 tests pass (4 tests)
- ☐ No new test failures (no regressions)
- ☐ Coverage maintained or improved
- ☐ Manual verification confirms fix

### Regression Prevention
- ☐ Tests added to CI/CD pipeline
- ☐ Tests run on every commit
- ☐ Tests included in pre-release verification
- ☐ Documentation updated with test requirements

## Maintenance Notes

### When to Update These Tests

**Add new tests when**:
- New scopes are added to ClaudeCodePlugin
- Enable/disable behavior changes
- New state values added to ServerState enum
- Bug reports related to cross-scope behavior

**Update existing tests when**:
- Scope file formats change
- Enable/disable array names change
- Error message formats change
- Test harness infrastructure changes

**DO NOT update tests to pass broken code**:
- Tests define correct behavior
- Implementation must match tests
- If tests fail, fix implementation (not tests)
- Only update tests if requirements change

## Related Documentation

- **Test Harness Guide**: `tests/TEST_HARNESS.md`
- **Test Rescope**: `tests/TEST_RESCOPE.md`
- **Test Safety**: `tests/TEST_SAFETY.md`
- **Project Spec**: `CLAUDE.md` (testing strategy section)

## Questions & Clarifications

**Q: Why are some tests passing if bugs exist?**
A: Those tests cover scenarios where the bug doesn't manifest. For example, `test_user_local_server_state_correctly_reflects_own_disabled_array` passes because user-local scope DOES have enable/disable arrays and the bug is about CROSS-scope pollution, not SAME-scope behavior.

**Q: Can I run just the failing tests?**
A: Yes, use `pytest tests/test_enable_disable_bugs.py --lf` (last failed) or `--failed-first`.

**Q: Why is client info test skipped?**
A: BUG-ORIG is a CLI command bug, not a plugin bug. It should be tested in `test_cli.py` where the CLI commands are tested. It's documented here for completeness but implementation belongs elsewhere.

**Q: What if tests start passing before bugs are fixed?**
A: That's a RED FLAG! It means either:
1. Tests are gaming-friendly (bad - rewrite them)
2. Someone changed tests to pass broken code (bad - revert)
3. Bugs were actually fixed (good - verify manually!)

Always verify that passing tests correspond to working functionality, not just passing assertions.

---

**Status**: Tests written and verified to catch real bugs ✓
**Next Step**: Fix BUG-1 and BUG-3 implementation
**Goal**: All tests passing + manual verification of fixes
