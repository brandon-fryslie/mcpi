# User-Internal Enable/Disable Functional Tests

## Overview

This document describes the functional tests for user-internal scope enable/disable functionality added to `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/tests/test_enable_disable_bugs.py`.

## Test Class: TestUserInternalEnableDisable

### Purpose

Validate that the user-internal scope (`~/.claude.json`) supports enable/disable operations using file-based tracking, following the same pattern as user-global scope.

### Implementation Pattern

- **Mechanism**: `FileTrackedEnableDisableHandler` with tracking file at `~/.claude/.mcpi-disabled-servers-internal.json`
- **Config File**: `~/.claude.json` (remains unchanged during operations)
- **Tracking File**: `~/.claude/.mcpi-disabled-servers-internal.json` (separate JSON array of disabled server IDs)

## Tests Added

### 1. test_user_internal_disable_server_creates_tracking_file

**What it tests**: Disabling a server in user-internal scope creates the tracking file.

**Why un-gameable**:
- Creates actual config file in temp directory
- Verifies tracking file is created on disable
- Checks actual JSON content of tracking file
- Uses real `plugin.disable_server()` method
- Verifies config file remains unchanged

**Assertions**:
- Operation succeeds
- Tracking file exists at expected path
- Server ID present in tracking file
- Original config file unchanged (exact JSON comparison)
- Server still present in config (not removed)

### 2. test_user_internal_enable_server_removes_from_tracking_file

**What it tests**: Enabling a disabled server removes it from the tracking file.

**Why un-gameable**:
- Sets up disabled state using real disable operation
- Verifies enable removes server from tracking file
- Checks actual tracking file contents
- Verifies config file remains unchanged throughout

**Assertions**:
- Operation succeeds
- Server removed from tracking file
- Config file unchanged (exact JSON comparison)

### 3. test_user_internal_disabled_server_shows_correct_state

**What it tests**: `list_servers()` shows correct state for disabled user-internal server.

**Why un-gameable**:
- Uses actual `list_servers()` API (what users see)
- Verifies state changes from ENABLED -> DISABLED -> ENABLED
- Tests the complete user workflow
- Cannot pass if state logic is wrong

**Assertions**:
- Initially shows ENABLED
- After disable shows DISABLED
- After enable shows ENABLED again
- Server remains in list throughout

### 4. test_user_internal_idempotent_disable

**What it tests**: Disabling a server twice is idempotent (safe).

**Why un-gameable**:
- Tests real-world usage (user runs disable command twice)
- Verifies tracking file doesn't have duplicates
- Checks both operations succeed

**Assertions**:
- Both disable operations succeed
- Server appears exactly once in tracking file

### 5. test_user_internal_idempotent_enable

**What it tests**: Enabling a server twice is idempotent (safe).

**Why un-gameable**:
- Tests real-world usage (user runs enable command twice)
- Verifies server removed from tracking file
- Checks both operations succeed

**Assertions**:
- Both enable operations succeed
- Server not in tracking file after enables

### 6. test_user_internal_scope_isolation

**What it tests**: user-internal enable/disable doesn't affect other scopes.

**Why un-gameable**:
- Tests multiple scopes simultaneously
- Verifies complete isolation between scopes
- Uses different server IDs to avoid scope-resolution ambiguity

**Assertions**:
- user-internal server shows DISABLED
- user-local server shows ENABLED (unaffected)
- user-local config file unchanged (no array modifications)

## Running the Tests

### Run all user-internal tests

```bash
pytest tests/test_enable_disable_bugs.py::TestUserInternalEnableDisable -v
```

### Run specific test

```bash
pytest tests/test_enable_disable_bugs.py::TestUserInternalEnableDisable::test_user_internal_disable_server_creates_tracking_file -v
```

### Expected Initial Failure

All tests currently fail with:
```
AssertionError: Failed to disable server: Scope 'user-internal' does not support enable/disable operations
```

This is EXPECTED because the implementation hasn't been added yet. Tests are designed to fail until:

1. Test harness adds `user-internal-disabled` path override
2. ClaudeCodePlugin adds `FileTrackedEnableDisableHandler` for user-internal scope

## Gaming Resistance Features

These tests are designed to be un-gameable:

- **Real File I/O**: Uses test harness with actual file operations, no mocks
- **Actual Content Verification**: Checks JSON file contents, not just method calls
- **Observable Behavior**: Asserts on ServerState enum values users would see
- **Side Effect Checking**: Verifies tracking file creation, config immutability
- **Idempotency Testing**: Tests real-world usage patterns (repeat operations)
- **Multi-scope Testing**: Validates isolation between scopes

### Cannot Pass With

- Stub implementations
- Mocked file operations
- Hardcoded return values
- Implementation shortcuts
- Missing tracking file support
- Incorrect state reporting
- Cross-scope pollution

## Traceability

### STATUS Gaps Addressed

From `STATUS-2025-11-13-DISABLE-EVALUATION.md`:
- **Gap**: user-internal scope does not support enable/disable operations
- **Evidence**: Error message "Scope 'user-internal' does not support enable/disable operations"

### PLAN Items Validated

From `PLAN-USER-INTERNAL-DISABLE-2025-11-13-175252.md`:
- **P1-2**: Add Functional Tests for user-internal Enable/Disable
  - Minimum 3 tests implemented ✓ (6 tests added)
  - Tests use MCPTestHarness ✓
  - Tests verify actual file contents ✓
  - Tests verify ServerState values ✓
  - Un-gameable (no mocks) ✓

### Acceptance Criteria Met

From PLAN P1-2:
- [x] Test class `TestUserInternalEnableDisable` created
- [x] Minimum 3 tests implemented (6 tests added)
  - [x] test_user_internal_disable_server_creates_tracking_file
  - [x] test_user_internal_enable_server_removes_from_tracking_file
  - [x] test_user_internal_disabled_server_shows_correct_state
  - [x] test_user_internal_idempotent_disable (bonus)
  - [x] test_user_internal_idempotent_enable (bonus)
  - [x] test_user_internal_scope_isolation (bonus)
- [x] All tests use MCPTestHarness (no mocks)
- [x] Tests verify actual file contents
- [x] Tests verify ServerState values
- [x] Tests currently fail (as expected)

## Test Quality Criteria

From CLAUDE.md Testing Philosophy:

- **USEFUL** ✓: Tests verify actual user-facing behavior (disable/enable/list)
- **COMPLETE** ✓: Covers all critical paths (disable, enable, state checking, idempotency, isolation)
- **FLEXIBLE** ✓: Uses test harness, not tied to implementation details
- **AUTOMATED** ✓: Fully automated, runs in CI/CD

## Implementation Dependencies

Before tests will pass:

1. **Test Harness Update** (`tests/test_harness.py`):
   - Add `user-internal-disabled` to `path_overrides` dictionary
   - Path: `{tmp_dir}/claude-code_user-internal-disabled_.mcpi-disabled-servers-internal.json`
   - Pattern matches existing `user-global-disabled` implementation

2. **ClaudeCodePlugin Update** (`src/mcpi/clients/claude_code.py`):
   - Add `user_internal_disabled_tracker_path` variable (lines 162-179)
   - Replace `enable_disable_handler=None` with `FileTrackedEnableDisableHandler(...)`
   - Use `DisabledServersTracker(user_internal_disabled_tracker_path)`
   - Update comment from "doesn't support" to "supports enable/disable via tracking file"

## Next Steps

1. Update test harness to add `user-internal-disabled` path override
2. Implement `FileTrackedEnableDisableHandler` for user-internal scope
3. Run tests to verify they pass
4. Update CLAUDE.md documentation with enable/disable mechanisms
5. Manual verification via CLI

## File Locations

- **Test File**: `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/tests/test_enable_disable_bugs.py`
- **Test Class**: `TestUserInternalEnableDisable` (lines 708-1066)
- **Implementation File**: `src/mcpi/clients/claude_code.py` (lines 162-179 need modification)
- **Test Harness**: `tests/test_harness.py` (needs path override addition)

## Success Metrics

When implementation is complete:
- All 6 tests pass (100% pass rate)
- No test regressions in existing tests
- Test coverage for user-internal scope matches user-global scope
- `mcpi disable <server>` works for user-internal servers (no error)
- `mcpi enable <server>` works for user-internal servers (no error)
- `mcpi list --scope user-internal` shows correct state
