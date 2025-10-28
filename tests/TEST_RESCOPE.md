# Rescope Command Test Documentation

This document describes the comprehensive test suite for the `mcpi rescope` command.

## Overview

The test suite in `test_cli_rescope.py` provides comprehensive validation of the rescope command's ability to move MCP server configurations between scopes with transaction safety, error handling, and complete configuration preservation.

## Test Philosophy: Un-Gameable Design

These tests are designed to be **un-gameable** - they cannot be satisfied by stub implementations or shortcuts. Each test validates actual system behavior through multiple verification points:

1. **Real File Operations**: Tests use the MCPTestHarness to perform actual file I/O operations
2. **Multiple Verification Points**: Each test checks both source removal AND destination addition
3. **Configuration Preservation**: Tests verify all configuration fields are preserved exactly
4. **Transaction Safety**: Tests validate rollback behavior on failures
5. **State Verification**: Tests check file contents directly, not just API responses

## Test Categories

### 1. Basic Flow Tests (`TestRescopeCommandBasicFlow`)

Tests core rescope functionality moving servers between scopes.

**Key Tests:**
- `test_rescope_project_to_user_scope`: Move from project to user scope with full config preservation
- `test_rescope_user_to_project_scope`: Move from user to project using prepopulated data

**What Makes Them Un-Gameable:**
- Verifies actual file deletion from source scope
- Verifies actual file creation in destination scope
- Validates complete configuration preservation (command, args, env, type)
- Checks both files independently

### 2. Position Independence Tests (`TestRescopePositionIndependence`)

Validates that rescope arguments can be provided in any order.

**Test Variations:**
- `mcpi rescope <server> --from <scope> --to <scope>`
- `mcpi rescope --from <scope> --to <scope> <server>`
- `mcpi rescope --to <scope> --from <scope> <server>`
- `mcpi rescope --from <scope> <server> --to <scope>`

**What Makes Them Un-Gameable:**
- Tests actual CLI argument parsing
- Verifies server exists in correct scope regardless of argument order
- No mocking of Click's argument processing

### 3. Error Handling Tests (`TestRescopeErrorHandling`)

Tests all documented error conditions and edge cases.

**Key Tests:**
- `test_rescope_server_not_in_source`: Server doesn't exist in source scope
- `test_rescope_server_exists_in_destination`: Server already exists in destination
- `test_rescope_invalid_source_scope`: Invalid source scope name
- `test_rescope_invalid_destination_scope`: Invalid destination scope name
- `test_rescope_same_source_and_destination`: Source and destination are identical

**What Makes Them Un-Gameable:**
- Verifies no files are created/modified on errors
- Checks specific error messages
- Validates system state unchanged after errors
- Tests data loss prevention

### 4. Dry-Run Tests (`TestRescopeDryRun`)

Validates dry-run mode shows what would happen without making changes.

**Key Tests:**
- `test_rescope_dry_run_no_changes`: Verifies no actual file changes
- `test_rescope_dry_run_shows_operation_details`: Verifies informative output

**What Makes Them Un-Gameable:**
- Counts servers in both scopes before and after
- Verifies files remain byte-for-byte identical
- Checks server still exists in source with exact same config
- Validates server NOT created in destination

### 5. Transaction Safety Tests (`TestRescopeTransactionSafety`)

Tests rollback functionality when operations fail midway.

**Key Tests:**
- `test_rescope_rollback_on_remove_failure`: Simulates remove failure, validates rollback
- `test_rescope_atomic_operation`: Verifies server in exactly one scope after operation

**What Makes Them Un-Gameable:**
- Simulates real failure conditions with mocks
- Verifies destination is cleaned up after failure
- Checks source remains unchanged
- Tests actual rollback logic execution
- Validates atomic state (server in one scope only)

### 6. Configuration Preservation Tests (`TestRescopeConfigurationPreservation`)

Tests that all configuration fields are preserved exactly during rescope.

**Key Tests:**
- `test_rescope_preserves_complex_config`: Tests complex config with all fields
- `test_rescope_preserves_minimal_config`: Tests minimal required-only config
- `test_rescope_preserves_empty_env`: Tests empty env dict preservation

**What Makes Them Un-Gameable:**
- Tests complete ServerConfig object
- Verifies every field individually
- Uses complex nested structures
- Validates exact equality including order
- Tests edge cases (empty dicts, long arrays)

### 7. Multi-Client Tests (`TestRescopeWithMultipleClients`)

Tests rescope behavior with client-specific scope validation.

**Key Tests:**
- `test_rescope_requires_valid_client_scopes`: Validates scopes per client
- `test_rescope_explicit_client_parameter`: Tests --client parameter

**What Makes Them Un-Gameable:**
- Tests actual client plugin scope validation
- Verifies error messages mention available scopes
- Uses real client registry

### 8. CLI Output Tests (`TestRescopeCLIOutput`)

Tests user experience and output quality.

**Key Tests:**
- `test_rescope_success_message`: Validates clear success messages
- `test_rescope_error_message_helpful`: Validates actionable error messages

### 9. Integration Scenarios (`TestRescopeIntegrationScenarios`)

Tests real-world developer workflows.

**Key Tests:**
- `test_workflow_project_testing_to_user_promotion`: Test server, then promote to user level
- `test_workflow_user_to_project_customization`: Customize user server for specific project

**What Makes Them Un-Gameable:**
- Simulates actual developer workflows
- Performs multiple operations in sequence
- Validates state at each step
- Uses prepopulated data for realism

### 10. Edge Cases Tests (`TestRescopeEdgeCases`)

Tests boundary conditions and unusual scenarios.

**Key Tests:**
- `test_rescope_with_special_characters_in_server_name`: Tests @scope/package names
- `test_rescope_between_all_scope_combinations`: Tests all valid scope pairs
- `test_rescope_with_empty_source_scope_file`: Tests empty source file
- `test_rescope_creates_destination_file_if_missing`: Tests file creation

**What Makes Them Un-Gameable:**
- Tests all possible scope combinations
- Verifies file creation and structure
- Validates special character handling
- Checks file permissions/content

## Test Infrastructure

### Fixtures Used

1. **`mcp_test_dir`**: Temporary directory for test files
2. **`mcp_harness`**: MCPTestHarness with scope files set up
3. **`mcp_manager_with_harness`**: MCPManager configured with test harness
4. **`prepopulated_harness`**: Harness with sample servers pre-loaded

### Test Harness Capabilities

The `MCPTestHarness` provides:
- Real file I/O operations in temporary directory
- Path override injection into client plugins
- Assertions for server existence and configuration
- JSON validation
- Server counting and config comparison

### Verification Methods

Tests use these verification methods to ensure un-gameable validation:

```python
# Verify server exists (reads actual file)
harness.assert_server_exists(scope, server_id)

# Verify server doesn't exist (reads actual file)
with pytest.raises(AssertionError):
    harness.assert_server_exists(scope, server_id)

# Get and compare configurations (reads actual file)
config = harness.get_server_config(scope, server_id)
assert config["command"] == expected_command

# Count servers (reads actual file)
count = harness.count_servers_in_scope(scope)
assert count == expected_count

# Validate JSON structure (parses actual file)
harness.assert_valid_json(scope)
```

## Expected Initial Test Results

Since the `rescope` command is not yet implemented, all tests should initially **FAIL** with one of:
- `Command not found` or similar error (rescope command doesn't exist)
- `Missing option` errors (required --from/--to options not defined)
- `No such command` from Click

This is **expected and correct**. The tests define the specification for the implementation.

## Running the Tests

```bash
# Run all rescope tests
pytest tests/test_cli_rescope.py -v

# Run specific test class
pytest tests/test_cli_rescope.py::TestRescopeCommandBasicFlow -v

# Run specific test
pytest tests/test_cli_rescope.py::TestRescopeCommandBasicFlow::test_rescope_project_to_user_scope -v

# Run with verbose output and show print statements
pytest tests/test_cli_rescope.py -v -s

# Run with coverage
pytest tests/test_cli_rescope.py --cov=src/mcpi --cov-report=term-missing
```

## Test Coverage Goals

- **Line Coverage**: ≥95% of rescope command code
- **Branch Coverage**: ≥90% of decision points
- **Error Path Coverage**: 100% of error conditions
- **Integration Coverage**: All scope combinations tested

## Success Criteria

Tests will pass when implementation provides:

1. ✅ Command works with all documented argument orders
2. ✅ Works with all clients that have multiple scopes
3. ✅ Gracefully handles all documented error cases
4. ✅ Provides clear, actionable error messages
5. ✅ Dry-run mode accurately shows what would happen
6. ✅ Rollback works if operation fails midway
7. ✅ All configuration fields are preserved during rescope
8. ✅ Server exists in exactly one scope after operation (atomic)

## Traceability to Requirements

### From BACKLOG.md

| Requirement | Test Coverage |
|-------------|---------------|
| Move server from one scope to another | `TestRescopeCommandBasicFlow` |
| Position-independent arguments | `TestRescopePositionIndependence` |
| Server not in source error | `TestRescopeErrorHandling::test_rescope_server_not_in_source` |
| Server exists in destination error | `TestRescopeErrorHandling::test_rescope_server_exists_in_destination` |
| Invalid scope names | `TestRescopeErrorHandling::test_rescope_invalid_*_scope` |
| Same source/dest error | `TestRescopeErrorHandling::test_rescope_same_source_and_destination` |
| Dry-run mode | `TestRescopeDryRun` |
| Transaction safety / rollback | `TestRescopeTransactionSafety` |
| Config preservation | `TestRescopeConfigurationPreservation` |
| Client scope validation | `TestRescopeWithMultipleClients` |

### From STATUS Report

These tests address gaps identified in the latest STATUS report:
- Validates incomplete rescope functionality (once implemented)
- Tests transaction safety (critical for data integrity)
- Covers error handling comprehensively
- Tests real user workflows

## Notes for Implementation

When implementing the `rescope` command, refer to these tests for:

1. **Required CLI signature**:
   ```python
   @main.command()
   @click.argument('server_name')
   @click.option('--from', 'from_scope', required=True, type=DynamicScopeType())
   @click.option('--to', 'to_scope', required=True, type=DynamicScopeType())
   @click.option('--client', default=None)
   @click.option('--dry-run', is_flag=True)
   def rescope(ctx, server_name, from_scope, to_scope, client, dry_run):
       ...
   ```

2. **Required operations**:
   - Validate scopes exist for client
   - Check server exists in source
   - Check server doesn't exist in destination
   - Read config from source
   - If dry-run, show details and exit
   - Write to destination
   - Remove from source (with rollback on failure)

3. **Error conditions to handle**:
   - Server not found in source
   - Server already in destination
   - Invalid scope names
   - Same source and destination
   - Write/remove failures

4. **Transaction safety**:
   - Use try/except around remove operation
   - If remove fails, remove from destination (rollback)
   - Ensure server in exactly one scope after operation

5. **Configuration preservation**:
   - Use `ScopeHandler.get_server_config()` to get full config
   - Pass exact config to destination (no transformations)
   - Preserve all fields: command, args, env, type

## Maintenance Notes

When updating tests:
- Maintain un-gameable properties (real file ops, multiple verifications)
- Add new edge cases as they're discovered
- Update traceability matrix when requirements change
- Keep test documentation in sync with implementation
- Run full test suite before committing changes
