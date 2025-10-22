# MCPI Functional Tests Documentation

## Overview

This document describes the functional test suite for MCPI, designed to validate critical user workflows with un-gameable tests that verify real functionality.

## Test Philosophy

Our functional tests follow these principles:

1. **Un-gameable**: Tests verify real functionality, not implementation details or mocks
2. **Traceable**: Each test maps to specific STATUS gaps and PLAN items
3. **Critical**: Focus on essential user journeys that must work
4. **Observable**: Verify outcomes users would actually see
5. **Complete**: Test entire workflows, not isolated units

## Test Structure

### File: `test_functional_critical_workflows.py`

Contains 11 functional tests organized into 4 test classes:

1. **TestCriticalAPI** - Tests for required API methods (P0-2)
2. **TestCoreUserWorkflows** - Tests for basic CRUD operations (P0-4)
3. **TestRescopeFeaturePreparation** - TDD tests for rescope feature (P1-1, P1-2)
4. **TestManagerIntegration** - Tests for MCPManager functionality (P0-4)

## Traceability Matrix

| Test Function | STATUS Gap | PLAN Item | Priority | Status |
|---------------|------------|-----------|----------|--------|
| `test_get_server_config_api_exists` | Missing get_server_config() method | P0-2 | CRITICAL | Active |
| `test_get_server_config_returns_complete_data` | Missing get_server_config() method | P0-2 | CRITICAL | Active |
| `test_get_server_config_works_across_all_scopes` | Missing get_server_config() method | P0-2 | CRITICAL | Active |
| `test_list_servers_across_scopes` | Test infrastructure broken | P0-1 | HIGH | Active |
| `test_add_and_remove_server_workflow` | Untested add/remove operations | P0-4 | HIGH | Active |
| `test_update_server_preserves_other_servers` | Untested operations | P0-4 | MEDIUM | Active |
| `test_manager_lists_all_scopes` | MCPManager untested | P0-4 | MEDIUM | Active |
| `test_manager_get_servers_aggregates_across_scopes` | MCPManager untested | P0-4 | HIGH | Active |
| `test_rescope_basic_workflow` | Rescope doesn't exist | P1-1 | FUTURE | Skipped |
| `test_rescope_preserves_complex_config` | Rescope doesn't exist | P1-1 | FUTURE | Skipped |
| `test_rescope_rollback_on_failure` | Rescope doesn't exist | P1-1 | FUTURE | Skipped |

## STATUS Report Findings Addressed

### From `STATUS-2025-10-21-225033.md`:

1. **"MISSING BASE METHOD: ScopeHandler.get_server_config()"** (line 27)
   - **Tests**: 3 tests in `TestCriticalAPI` class
   - **Validation**: Method exists, returns correct data, works across scopes
   - **Priority**: CRITICAL (blocks rescope feature)

2. **"Cannot verify add/remove operations"** (line 282)
   - **Tests**: `test_add_and_remove_server_workflow`
   - **Validation**: Complete workflow with file verification
   - **Priority**: HIGH

3. **"Cannot verify enable/disable functionality"** (line 283)
   - **Tests**: `test_update_server_preserves_other_servers`
   - **Validation**: Update operations work correctly
   - **Priority**: MEDIUM

4. **"MCPManager exists but untested"** (line 366)
   - **Tests**: 2 tests in `TestManagerIntegration` class
   - **Validation**: Manager works with scopes, aggregates servers
   - **Priority**: MEDIUM

5. **"Rescope Feature Readiness: BLOCKED"** (line 15)
   - **Tests**: 3 tests in `TestRescopeFeaturePreparation` (currently skipped)
   - **Validation**: TDD approach - tests define the contract
   - **Priority**: FUTURE (after P0-2 complete)

## How Tests Resist Gaming

### Principle 1: Real File I/O
All tests use the `MCPTestHarness` which performs actual file operations:
- Creates real JSON files in temporary directories
- Reads and parses actual file contents
- Verifies file modifications persist to disk

**Why this prevents gaming**: Cannot fake with in-memory stubs or mocks.

### Principle 2: Multiple Verification Points
Each test verifies multiple observable outcomes:
- File exists
- File contains valid JSON
- Server appears in listing
- Configuration matches expectations
- State changes persist

**Why this prevents gaming**: Must satisfy all assertions, not just one.

### Principle 3: Cross-Validation
Tests verify outcomes using different methods:
- Check via API (`get_servers()`)
- Check via file read (`read_scope_file()`)
- Check via test harness (`count_servers_in_scope()`)

**Why this prevents gaming**: Cannot satisfy one check without satisfying all.

### Principle 4: Complete Workflows
Tests validate entire user workflows:
- Add server → Verify in file → Verify in listing → Remove → Verify deleted
- Not just: Add server → Assert True

**Why this prevents gaming**: Must implement full functionality, not just return success.

### Principle 5: State Verification
Tests check that operations have expected side effects:
- Other servers not affected by updates
- File structure preserved
- Rollback works on failure

**Why this prevents gaming**: Tests capture regression scenarios.

## Running the Tests

### Run All Functional Tests
```bash
cd /Users/bmf/icode/mcpi
uv run pytest tests/test_functional_critical_workflows.py -v
```

### Run Specific Test Class
```bash
# Test critical APIs only
uv run pytest tests/test_functional_critical_workflows.py::TestCriticalAPI -v

# Test core workflows only
uv run pytest tests/test_functional_critical_workflows.py::TestCoreUserWorkflows -v

# Test manager integration only
uv run pytest tests/test_functional_critical_workflows.py::TestManagerIntegration -v
```

### Run Specific Test
```bash
uv run pytest tests/test_functional_critical_workflows.py::TestCriticalAPI::test_get_server_config_api_exists -v
```

### Run with Coverage
```bash
uv run pytest tests/test_functional_critical_workflows.py --cov=src/mcpi --cov-report=html
```

### Expected Initial Results

**Tests that SHOULD FAIL initially** (functionality not implemented):
- `test_get_server_config_api_exists` - Method doesn't exist yet (P0-2)
- `test_get_server_config_returns_complete_data` - Method doesn't exist yet (P0-2)
- `test_get_server_config_works_across_all_scopes` - Method doesn't exist yet (P0-2)

**Tests that SHOULD PASS** (functionality exists):
- `test_list_servers_across_scopes` - `get_servers()` exists
- `test_add_and_remove_server_workflow` - `add_server()`, `remove_server()` exist
- `test_update_server_preserves_other_servers` - `update_server()` exists
- `test_manager_lists_all_scopes` - Manager scope listing exists
- `test_manager_get_servers_aggregates_across_scopes` - Manager `list_servers()` exists

**Tests that are SKIPPED** (TDD for future features):
- `test_rescope_basic_workflow` - Rescope feature not implemented
- `test_rescope_preserves_complex_config` - Rescope feature not implemented
- `test_rescope_rollback_on_failure` - Rescope feature not implemented

## Test Dependencies

### Required Test Infrastructure
- `test_harness.py` - MCPTestHarness for file operations
- `conftest.py` - Shared pytest fixtures
- `pytest` - Test runner
- `pytest-cov` - Coverage measurement

### Required Application Code
- `mcpi.clients.base.ScopeHandler` - Base scope handler class
- `mcpi.clients.claude_code.ClaudeCodePlugin` - Claude Code client plugin
- `mcpi.clients.manager.MCPManager` - MCP manager
- `mcpi.clients.registry.ClientRegistry` - Client registry
- `mcpi.clients.types` - Type definitions

## Test Maintenance

### When to Update These Tests

1. **When implementing P0-2 (get_server_config)**:
   - Remove `@pytest.mark.skip` from get_server_config tests
   - Verify all 3 tests in `TestCriticalAPI` pass
   - If tests fail, implementation is incomplete or incorrect

2. **When implementing rescope feature (P1-1, P1-2)**:
   - Remove `@pytest.mark.skip` from rescope tests
   - Verify all 3 tests in `TestRescopeFeaturePreparation` pass
   - Add any additional rescope tests for edge cases

3. **When adding new user-facing features**:
   - Add new functional test following same principles
   - Map to STATUS gap or PLAN item
   - Ensure test is un-gameable
   - Update this documentation

### How to Add New Functional Tests

1. **Identify the user workflow**: What does the user want to accomplish?
2. **Map to STATUS/PLAN**: Which gap or work item does this address?
3. **Design test workflow**: Input → Operation → Observable Outcome
4. **Implement with test harness**: Use real files, no mocks
5. **Verify multiple outcomes**: File state, API responses, listings, etc.
6. **Document traceability**: Add to matrix above
7. **Make it un-gameable**: Review against principles above

## Example: Anatomy of an Un-Gameable Test

```python
def test_add_and_remove_server_workflow(self, mcp_harness):
    """Complete add → verify → remove workflow."""

    # 1. Setup: Real file with known state
    mcp_harness.prepopulate_file("user-global", {
        "mcpEnabled": True,
        "mcpServers": {}
    })

    # 2. Get real plugin instance (no mocks)
    plugin = ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)
    scope_handler = plugin.get_scope_handler("user-global")

    # 3. Perform operation
    result = scope_handler.add_server("memory-server", new_server_config)

    # 4. Verify multiple outcomes:

    # - Operation reported success
    assert result.success

    # - File was actually modified
    mcp_harness.assert_server_exists("user-global", "memory-server")

    # - Server appears in API listing
    servers = scope_handler.get_servers()
    assert "memory-server" in servers

    # - Configuration matches what was saved
    saved_config = mcp_harness.get_server_config("user-global", "memory-server")
    assert saved_config["command"] == "npx"

    # 5. Perform reverse operation
    result = scope_handler.remove_server("memory-server")

    # 6. Verify cleanup:

    # - Operation reported success
    assert result.success

    # - File count updated
    final_count = mcp_harness.count_servers_in_scope("user-global")
    assert final_count == 0

    # - Server gone from listing
    servers = scope_handler.get_servers()
    assert "memory-server" not in servers
```

**Why this is un-gameable**:
1. Uses real file I/O (not mocks)
2. Verifies 6+ different outcomes
3. Cross-validates using different methods
4. Tests complete workflow, not isolated operations
5. Checks both success and cleanup paths

## Integration with TDD Workflow

These functional tests support Test-Driven Development:

### Phase 1: Write Failing Tests (DONE)
- ✅ Tests for P0-2 (get_server_config) written
- ✅ Tests for P0-4 (core workflows) written
- ✅ Tests for P1-1 (rescope) written (skipped for now)

### Phase 2: Implement Minimum to Pass (TODO)
- ⏳ Implement `ScopeHandler.get_server_config()` until P0-2 tests pass
- ⏳ Fix any issues with core workflows until P0-4 tests pass

### Phase 3: Refactor with Confidence (TODO)
- With tests passing, refactor implementation
- Tests ensure behavior preserved

### Phase 4: Implement Rescope (TODO)
- Un-skip rescope tests
- Implement rescope feature until tests pass
- Tests define the contract, implementation fulfills it

## Success Metrics

### Phase 1 Complete (Foundation Repair)
- ✅ 8/8 active tests passing
- ✅ 0 test import errors
- ✅ All P0-2 tests passing (get_server_config implemented)
- ✅ All P0-4 tests passing (core workflows validated)

### Phase 2 Complete (Rescope Feature)
- ✅ 11/11 tests passing (including un-skipped rescope tests)
- ✅ All P1-1 tests passing (rescope feature implemented)
- ✅ Test coverage >95% for rescope code

## Troubleshooting

### Test Failures

**If `test_get_server_config_api_exists` fails**:
- Cause: Method not implemented in `ScopeHandler` base class
- Fix: Add abstract method to `ScopeHandler` in `src/mcpi/clients/base.py`
- PLAN: P0-2 acceptance criteria

**If `test_get_server_config_returns_complete_data` fails**:
- Cause: Method returns wrong data or doesn't handle errors
- Fix: Implement method properly in `FileBasedScope`
- PLAN: P0-2 acceptance criteria

**If `test_add_and_remove_server_workflow` fails**:
- Cause: File operations not working correctly
- Fix: Check `add_server()` and `remove_server()` implementations
- Likely: File path issues or JSON serialization problems

**If `test_manager_get_servers_aggregates_across_scopes` fails**:
- Cause: Manager not querying all scopes
- Fix: Check `MCPManager.list_servers()` implementation
- Likely: Scope discovery or aggregation logic

### Import Errors

**If tests can't import `mcpi` modules**:
```bash
cd /Users/bmf/icode/mcpi
uv pip install -e .
```

**If test harness not found**:
- Ensure `test_harness.py` is in tests directory
- Check imports in test file

### Test Hangs

**If tests hang or timeout**:
- Likely: Trying to access network or external resources
- Fix: Ensure test harness uses temporary directories
- Check: No real HTTP calls, no actual client connections

## Future Enhancements

### Additional Tests to Consider

1. **Concurrent operations**: Test thread safety
2. **Large configurations**: Test performance with many servers
3. **Malformed files**: Test error recovery
4. **Permission errors**: Test file access error handling
5. **Cross-client operations**: Test multi-client scenarios

### Test Infrastructure Improvements

1. **Parametrized scope testing**: Test all scopes systematically
2. **Property-based testing**: Use hypothesis for edge cases
3. **Performance benchmarks**: Track operation timing
4. **Integration with CI**: Automated testing on commits

## References

- **STATUS Report**: `/Users/bmf/icode/mcpi/.agent_planning/STATUS-2025-10-21-225033.md`
- **PLAN Document**: `/Users/bmf/icode/mcpi/.agent_planning/PLAN-2025-10-21-225314.md`
- **Rescope Spec**: `/Users/bmf/icode/mcpi/.agent_planning/BACKLOG.md`
- **Project Architecture**: `/Users/bmf/icode/mcpi/CLAUDE.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-22
**Maintainer**: Test Infrastructure Team
