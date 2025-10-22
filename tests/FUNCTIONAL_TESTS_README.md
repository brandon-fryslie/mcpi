# MCPI Functional Tests Documentation

This document describes the functional test suite for the MCPI project, designed with TDD principles and anti-gaming mechanisms.

## Overview

The functional tests validate critical user workflows and API contracts. Tests are organized by priority (P0, P1) matching the project PLAN and STATUS reports.

## Test Files

### test_functional_rescope_prerequisites.py

**Purpose**: Validate prerequisites for the rescope feature and core user workflows.

**Test Coverage**: 14 tests across 3 test classes

**Test Classes**:
1. `TestP0_2_GetServerConfigAPI` (5 tests) - CRITICAL
2. `TestP0_4_CoreCLIWorkflows` (3 tests) - HIGH
3. `TestP0_4_ScopeOperations` (2 tests) - HIGH
4. `TestP1_1_RescopeFeature_TDD` (4 tests) - FUTURE (skipped)

## Test Traceability Matrix

| Test Function | STATUS Gap | PLAN Item | Priority | Status |
|---------------|------------|-----------|----------|--------|
| test_get_server_config_api_exists_on_scope_handler | Missing get_server_config() | P0-2 | CRITICAL | FAILING |
| test_get_server_config_returns_full_config_dict | Missing get_server_config() | P0-2 | CRITICAL | FAILING |
| test_get_server_config_raises_error_on_missing_server | Missing get_server_config() | P0-2 | CRITICAL | FAILING |
| test_get_server_config_works_across_all_scope_types | Missing get_server_config() | P0-2 | CRITICAL | FAILING |
| test_get_server_config_with_complex_config | Missing get_server_config() | P0-2 | CRITICAL | FAILING |
| test_cli_status_command_works | Untested CLI workflows | P0-4 | HIGH | PASSING |
| test_cli_list_shows_servers | Untested CLI workflows | P0-4 | HIGH | PASSING |
| test_cli_help_command_works | Untested CLI workflows | P0-4 | HIGH | PASSING |
| test_scope_handler_can_add_server_to_file | Untested add operations | P0-4 | HIGH | PASSING |
| test_scope_handler_can_remove_server_from_file | Untested remove operations | P0-4 | HIGH | PASSING |
| test_rescope_command_exists_in_cli | Rescope doesn't exist | P1-1 | FUTURE | SKIPPED (TDD) |
| test_rescope_moves_server_between_scopes_via_cli | Rescope doesn't exist | P1-1 | FUTURE | SKIPPED (TDD) |
| test_rescope_preserves_complex_config_fields | Rescope doesn't exist | P1-1 | FUTURE | SKIPPED (TDD) |
| test_rescope_rollback_on_failure | Rescope doesn't exist | P1-1 | FUTURE | SKIPPED (TDD) |

## Current Test Status

**As of**: 2025-10-22

```
Total Tests: 14
- Passing: 5 (35.7%)
- Failing: 5 (35.7%) - Expected failures for P0-2
- Skipped: 4 (28.6%) - TDD tests for future feature
```

### P0-2: get_server_config API (5 tests - ALL FAILING)

**Status**: BLOCKED - Method not implemented
**Priority**: CRITICAL
**Blocks**: Rescope feature (P1-1)

Tests validate:
- Method exists on ScopeHandler base class
- Returns complete server configuration
- Raises appropriate errors for missing servers
- Works across all scope types (user-global, project-mcp, user-internal)
- Preserves complex configurations (env vars, args, etc.)

**Expected Behavior**: Tests will PASS once `ScopeHandler.get_server_config()` is implemented.

### P0-4: Core CLI Workflows (5 tests - ALL PASSING)

**Status**: WORKING
**Priority**: HIGH

Tests validate:
- `bin/mcpi status` command works
- `bin/mcpi list` command shows servers
- `bin/mcpi --help` shows usage
- Scope handlers can add servers to files
- Scope handlers can remove servers from files

**Current Status**: All tests passing - core CLI is functional!

### P1-1: Rescope Feature (4 tests - ALL SKIPPED)

**Status**: NOT IMPLEMENTED (TDD approach)
**Priority**: P1 (Future)
**Dependencies**: P0-2 must be completed first

Tests define acceptance criteria for rescope:
- `bin/mcpi rescope` command exists
- Moves servers between scopes (not copy)
- Preserves all configuration fields
- Rolls back on failure

**Expected Behavior**: Tests will be un-skipped and run once rescope implementation begins.

## Gaming Resistance Mechanisms

These tests are designed to be **un-gameable** - they cannot pass without proper implementation:

### 1. Real CLI Execution
- Tests invoke `bin/mcpi` via subprocess
- Cannot fake with Python API stubs
- Validates actual exit codes and stdout/stderr
- Tests the real user-facing interface

### 2. Real File Operations
- Tests read/write actual JSON config files
- Compare file contents before/after operations
- Use test harness for independent file verification
- Cannot pass without proper file I/O

### 3. Multiple Side Effects
Each test validates:
- Primary outcome (operation succeeds)
- File state changes (configs updated)
- Output correctness (shows expected data)
- Error handling (fails appropriately)

### 4. Complete Workflows
- Tests run end-to-end user journeys
- Setup → Execute → Verify → Cleanup
- No shortcuts possible
- Must implement full functionality

### 5. API Contract Validation
For `get_server_config()`:
- Method must exist (hasattr check)
- Must be callable
- Must return correct data structure
- Must match file contents exactly
- Must raise appropriate errors

### 6. Data Equality Checks
- Not just type validation
- Full data structure comparison
- Independent file reading for verification
- Cannot hardcode responses

## Running the Tests

### Run all functional tests:
```bash
pytest tests/test_functional_rescope_prerequisites.py -v
```

### Run specific test class:
```bash
# P0-2 tests (should fail until get_server_config implemented)
pytest tests/test_functional_rescope_prerequisites.py::TestP0_2_GetServerConfigAPI -v

# P0-4 tests (should pass)
pytest tests/test_functional_rescope_prerequisites.py::TestP0_4_CoreCLIWorkflows -v
pytest tests/test_functional_rescope_prerequisites.py::TestP0_4_ScopeOperations -v

# P1-1 tests (skipped until ready to implement)
pytest tests/test_functional_rescope_prerequisites.py::TestP1_1_RescopeFeature_TDD -v
```

### Run with detailed output:
```bash
pytest tests/test_functional_rescope_prerequisites.py -vv --tb=short
```

## Test Development Workflow

### Phase 1: P0-2 Implementation
1. Implement `ScopeHandler.get_server_config()` in base class
2. Implement in `FileBasedScope`
3. Run P0-2 tests - should now pass
4. Coverage should increase significantly

### Phase 2: P1-1 Rescope Feature (TDD)
1. Un-skip P1-1 tests
2. Tests will fail (feature doesn't exist)
3. Implement `bin/mcpi rescope` command
4. Implement rescope logic in MCPManager
5. Run P1-1 tests - should pass when complete
6. All 14 tests passing = feature complete

## Expected Timeline

Based on PLAN-2025-10-21-225314.md:

- **P0-2 Implementation**: 4 hours
  - Add method to base class: 1 hour
  - Implement in FileBasedScope: 2 hours
  - Test and validate: 1 hour
  - Expected: 5 tests go from FAIL → PASS

- **P1-1 Rescope Feature**: 2-3 days
  - Design CLI command: 4 hours
  - Implement rescope logic: 8 hours
  - Error handling and rollback: 4 hours
  - Testing and validation: 4 hours
  - Expected: 4 tests go from SKIP → PASS

**Total**: Feature-complete with 14/14 tests passing

## Success Criteria

### P0-2 Complete
- ✓ All 5 P0-2 tests passing
- ✓ `get_server_config()` works across all scope types
- ✓ Method properly integrated in base class

### P1-1 Complete
- ✓ All 4 P1-1 tests passing (un-skipped)
- ✓ `bin/mcpi rescope` command functional
- ✓ Server config moves between scopes correctly
- ✓ Rollback mechanism tested and working

### Overall
- ✓ 14/14 tests passing
- ✓ 0 tests skipped
- ✓ All critical user workflows validated
- ✓ No gaming possible - tests verify real functionality

## Integration with Project Workflow

These tests integrate with the project's test-and-implement cycle:

1. **Evaluate**: STATUS report identifies gaps
2. **Plan**: PLAN assigns priorities (P0, P1, etc.)
3. **Test**: Write functional tests for acceptance criteria (THIS FILE)
4. **Implement**: Write code to make tests pass
5. **Validate**: Run tests to confirm implementation
6. **Repeat**: Move to next priority

This test suite represents the "Test" phase for P0-2 and P1-1.

## Notes

- Tests use the test harness from `test_harness.py` for file operations
- Tests require `bin/mcpi` to be executable
- P1-1 tests are skipped with `@pytest.mark.skip(reason="TDD: ...")`
- Remove skip decorators when ready to implement rescope
- All tests are designed to fail initially (TDD principle)
- Tests should pass ONLY when functionality is properly implemented

## References

- **STATUS Report**: STATUS-2025-10-21-225033.md (identified missing get_server_config)
- **PLAN**: PLAN-2025-10-21-225314.md (defined P0-2 and P1-1 work items)
- **Feature Spec**: .agent_planning/BACKLOG.md (rescope feature requirements)
- **Architecture**: CLAUDE.md (plugin-based scope system)
