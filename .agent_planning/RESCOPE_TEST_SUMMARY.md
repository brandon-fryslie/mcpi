# Rescope Command Test Implementation Summary

**Generated**: 2025-10-23
**Status**: Tests Implemented, Feature Not Implemented
**Test Count**: 28 comprehensive functional tests
**Coverage**: All requirements from BACKLOG.md

## Executive Summary

Comprehensive un-gameable functional tests for the `rescope` command have been implemented in `/Users/bmf/icode/mcpi/tests/test_cli_rescope.py`. These tests define the complete specification for the rescope feature and will serve as acceptance criteria for implementation.

## Test Suite Structure

### Test Files Created

1. **`tests/test_cli_rescope.py`** (755 lines)
   - 28 functional tests across 10 test classes
   - Un-gameable design using real file operations
   - Comprehensive edge case coverage
   - Transaction safety validation

2. **`tests/TEST_RESCOPE.md`** (documentation)
   - Test philosophy and design principles
   - Category descriptions and traceability
   - Running instructions and success criteria
   - Implementation guidance

3. **`.agent_planning/RESCOPE_TEST_SUMMARY.md`** (this file)
   - Test implementation summary
   - Traceability to requirements
   - Next steps for implementation

## Test Categories (28 tests)

### 1. Basic Flow (2 tests)
- ✅ `test_rescope_project_to_user_scope` - Move from project to user with config preservation
- ✅ `test_rescope_user_to_project_scope` - Move from user to project using prepopulated data

### 2. Position Independence (4 tests)
- ✅ `test_rescope_args_server_first` - Server name first
- ✅ `test_rescope_args_from_first` - --from option first
- ✅ `test_rescope_args_to_first` - --to option first
- ✅ `test_rescope_args_mixed_order` - Mixed argument order

### 3. Error Handling (5 tests)
- ✅ `test_rescope_server_not_in_source` - Server doesn't exist in source
- ✅ `test_rescope_server_exists_in_destination` - Server already in destination
- ✅ `test_rescope_invalid_source_scope` - Invalid source scope name
- ✅ `test_rescope_invalid_destination_scope` - Invalid destination scope name
- ✅ `test_rescope_same_source_and_destination` - Same scope error

### 4. Dry-Run (2 tests)
- ✅ `test_rescope_dry_run_no_changes` - No actual changes made
- ✅ `test_rescope_dry_run_shows_operation_details` - Informative output

### 5. Transaction Safety (2 tests)
- ✅ `test_rescope_rollback_on_remove_failure` - Rollback on failure
- ✅ `test_rescope_atomic_operation` - Server in exactly one scope

### 6. Configuration Preservation (3 tests)
- ✅ `test_rescope_preserves_complex_config` - All fields with complex nested data
- ✅ `test_rescope_preserves_minimal_config` - Minimal required-only config
- ✅ `test_rescope_preserves_empty_env` - Empty env dict preservation

### 7. Multi-Client (2 tests)
- ✅ `test_rescope_requires_valid_client_scopes` - Scope validation per client
- ✅ `test_rescope_explicit_client_parameter` - --client parameter

### 8. CLI Output (2 tests)
- ✅ `test_rescope_success_message` - Clear success messages
- ✅ `test_rescope_error_message_helpful` - Actionable error messages

### 9. Integration Scenarios (2 tests)
- ✅ `test_workflow_project_testing_to_user_promotion` - Real developer workflow
- ✅ `test_workflow_user_to_project_customization` - Customization workflow

### 10. Edge Cases (4 tests)
- ✅ `test_rescope_with_special_characters_in_server_name` - @scope/package names
- ✅ `test_rescope_between_all_scope_combinations` - All scope pairs
- ✅ `test_rescope_with_empty_source_scope_file` - Empty source file
- ✅ `test_rescope_creates_destination_file_if_missing` - File creation

## Un-Gameable Design Principles

Each test is designed to resist gaming through:

### 1. Real File Operations
- Tests use `MCPTestHarness` for actual file I/O
- No mocking of file operations (except for failure simulation)
- Validates actual JSON content in files

### 2. Multiple Verification Points
- Each test checks source removal AND destination addition
- Verifies configuration preservation field-by-field
- Validates file structure and content

### 3. Observable Outcomes
- Tests verify externally observable file system state
- Checks that can be independently validated
- No reliance on internal implementation details

### 4. Transaction Safety
- Tests simulate real failure conditions
- Validates rollback cleans up properly
- Ensures atomic operations (server in one scope only)

### 5. Configuration Preservation
- Tests all ServerConfig fields individually
- Validates nested structures (env vars, args arrays)
- Checks edge cases (empty dicts, special characters)

## Traceability to Requirements

### From `.agent_planning/BACKLOG.md`

| Requirement | Status | Test Coverage |
|-------------|--------|---------------|
| Move server from one scope to another | ✅ Specified | `TestRescopeCommandBasicFlow` (2 tests) |
| Position-independent arguments | ✅ Specified | `TestRescopePositionIndependence` (4 tests) |
| Server not in source error | ✅ Specified | `TestRescopeErrorHandling::test_rescope_server_not_in_source` |
| Server exists in destination error | ✅ Specified | `TestRescopeErrorHandling::test_rescope_server_exists_in_destination` |
| Invalid scope names | ✅ Specified | `TestRescopeErrorHandling::test_rescope_invalid_*_scope` (2 tests) |
| Same source/dest error | ✅ Specified | `TestRescopeErrorHandling::test_rescope_same_source_and_destination` |
| Dry-run mode | ✅ Specified | `TestRescopeDryRun` (2 tests) |
| Transaction safety / rollback | ✅ Specified | `TestRescopeTransactionSafety` (2 tests) |
| Config preservation | ✅ Specified | `TestRescopeConfigurationPreservation` (3 tests) |
| Client scope validation | ✅ Specified | `TestRescopeWithMultipleClients` (2 tests) |
| **TOTAL** | **10/10** | **28 tests** |

### From `.agent_planning/STATUS-2025-10-23-130000.md`

These tests address status gaps:
- ✅ Tests for missing rescope functionality
- ✅ Transaction safety validation (critical for data integrity)
- ✅ Comprehensive error handling coverage
- ✅ Real user workflow validation

## Test Execution Status

### Initial Run (Expected Failures)

```bash
$ pytest tests/test_cli_rescope.py::TestRescopeCommandBasicFlow::test_rescope_project_to_user_scope -v

FAILED - AssertionError: Command failed: Error: No such command 'rescope'.
```

**Status**: ✅ EXPECTED - Command not yet implemented

All 28 tests are expected to fail with "No such command 'rescope'" until the feature is implemented.

### Test Collection

```bash
$ pytest tests/test_cli_rescope.py --collect-only

collected 28 items
  <Module test_cli_rescope.py>
    <Class TestRescopeCommandBasicFlow> (2 tests)
    <Class TestRescopePositionIndependence> (4 tests)
    <Class TestRescopeErrorHandling> (5 tests)
    <Class TestRescopeDryRun> (2 tests)
    <Class TestRescopeTransactionSafety> (2 tests)
    <Class TestRescopeConfigurationPreservation> (3 tests)
    <Class TestRescopeWithMultipleClients> (2 tests)
    <Class TestRescopeCLIOutput> (2 tests)
    <Class TestRescopeIntegrationScenarios> (2 tests)
    <Class TestRescopeEdgeCases> (4 tests)
```

**Status**: ✅ All tests collected successfully

## Implementation Guidance

The tests define the complete specification for implementation. Key requirements:

### 1. CLI Command Signature

```python
@main.command()
@click.argument('server_name')
@click.option('--from', 'from_scope', required=True, type=DynamicScopeType(),
              help='Source scope to move from')
@click.option('--to', 'to_scope', required=True, type=DynamicScopeType(),
              help='Destination scope to move to')
@click.option('--client', default=None,
              help='MCP client to use (auto-detected if not specified)')
@click.option('--dry-run', is_flag=True,
              help='Show what would happen without making changes')
@click.pass_context
def rescope(ctx, server_name, from_scope, to_scope, client, dry_run):
    """Move an MCP server configuration from one scope to another."""
    pass
```

### 2. Required Operations

1. Get client plugin via `MCPManager`
2. Validate scopes exist for client
3. Check server exists in source scope
4. Check server doesn't exist in destination scope
5. Read full config from source using `ScopeHandler.get_server_config()`
6. If dry-run, show details and exit
7. Write to destination using `ScopeHandler.add_server()`
8. Remove from source using `ScopeHandler.remove_server()` (with rollback)

### 3. Transaction Safety Pattern

```python
# Write to destination
result = dest_handler.add_server(server_name, server_config)
if not result.success:
    raise OperationError(...)

# Remove from source (with rollback on failure)
try:
    result = source_handler.remove_server(server_name)
    if not result.success:
        # Rollback: remove from destination
        dest_handler.remove_server(server_name)
        raise OperationError(...)
except Exception as e:
    # Rollback: remove from destination
    dest_handler.remove_server(server_name)
    raise
```

### 4. Error Messages

Tests expect specific error patterns:
- "not found" - Server doesn't exist in source
- "already exists" - Server exists in destination
- "invalid" / "not a valid" - Invalid scope names
- "same" - Source and destination identical

### 5. Methods Required

**Already exists** (no changes needed):
- ✅ `ScopeHandler.get_server_config(server_id)` - Implemented in `file_based.py:200`
- ✅ `ScopeHandler.add_server(server_id, config)` - Implemented in `file_based.py:219`
- ✅ `ScopeHandler.remove_server(server_id)` - Implemented in `file_based.py:270`
- ✅ `ScopeHandler.has_server(server_id)` - Implemented in `base.py:90`
- ✅ `MCPClientPlugin.get_scope_handler(scope)` - Implemented in `base.py:165`

**New methods needed**:
- ❌ `cli.py:rescope()` command - Main CLI command (NEW)
- ❌ Helper function for rescope logic (optional, can be inline in command)

## Test Coverage Goals

| Metric | Target | Expected with Implementation |
|--------|--------|------------------------------|
| Line Coverage | ≥95% | ~98% (comprehensive tests) |
| Branch Coverage | ≥90% | ~95% (all error paths tested) |
| Error Path Coverage | 100% | 100% (all error conditions tested) |
| Integration Coverage | 100% | 100% (all scope combinations tested) |

## Next Steps

### For Test Implementation (COMPLETED ✅)
- ✅ Write 28 comprehensive tests
- ✅ Document test philosophy and design
- ✅ Verify tests fail with expected error
- ✅ Ensure un-gameable properties
- ✅ Map to requirements

### For Feature Implementation (PENDING ⏳)
1. Add `rescope` command to `src/mcpi/cli.py`
2. Implement transaction logic with rollback
3. Add error handling for all edge cases
4. Implement dry-run mode
5. Add helpful error messages
6. Run tests to verify implementation
7. Achieve ≥95% test coverage
8. Update CHANGELOG.md
9. Update README.md with examples

### For Documentation (PENDING ⏳)
1. Add rescope examples to README.md
2. Update CLI help text
3. Add to feature list
4. Document common workflows

## Files Modified/Created

### Test Files
- ✅ `tests/test_cli_rescope.py` - 28 functional tests (755 lines)
- ✅ `tests/TEST_RESCOPE.md` - Test documentation

### Planning Files
- ✅ `.agent_planning/RESCOPE_TEST_SUMMARY.md` - This summary

### Implementation Files (Pending)
- ⏳ `src/mcpi/cli.py` - Add rescope command
- ⏳ `README.md` - Add rescope documentation
- ⏳ `CHANGELOG.md` - Add rescope feature entry

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Transaction rollback incomplete | Low | High | Comprehensive rollback tests |
| Config data loss during rescope | Low | Critical | Field-by-field preservation tests |
| Race condition with concurrent ops | Low | Medium | Atomic operation tests |
| Invalid scope combinations | Medium | Low | All combinations tested |
| Special characters in server names | Low | Low | Special character tests |

## Success Criteria

Implementation is complete when:
- ✅ All 28 tests pass
- ✅ Test coverage ≥95%
- ✅ Error messages are clear and actionable
- ✅ Dry-run mode works correctly
- ✅ Transaction rollback works on failures
- ✅ All config fields preserved exactly
- ✅ Documentation updated
- ✅ CHANGELOG.md updated

## Maintenance

- Run full test suite before commits: `pytest tests/test_cli_rescope.py`
- Update tests when requirements change
- Keep documentation in sync with implementation
- Monitor test execution time (should be <5s for full suite)
- Add new edge cases as discovered

## Conclusion

The test suite provides comprehensive, un-gameable validation of the rescope command. The tests:
- Define complete functional specification
- Validate real file operations
- Ensure transaction safety
- Cover all error conditions
- Test real user workflows
- Cannot be satisfied by stubs or shortcuts

The implementation phase can now proceed with confidence that the tests will validate correct behavior.
