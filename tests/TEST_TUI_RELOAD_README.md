# TUI Reload Functionality Tests

## Overview

This test suite verifies the fzf TUI reload mechanism works correctly. The tests are designed to be **un-gameable** - they verify actual user workflows, real file operations, and observable state changes, not mocked behavior.

## Test Philosophy

### Why These Tests Are Un-Gameable

1. **Real Objects**: Uses actual `MCPManager` and `ServerCatalog` instances, not `MagicMock`
2. **Real Files**: Creates and modifies real configuration files in temp directories
3. **Observable State**: Verifies actual command output, file contents, and state changes
4. **Subprocess Execution**: Tests commands as they would be called by fzf (subprocess)
5. **Multiple Verification Points**: Each test checks multiple aspects of functionality

### What Cannot Be Faked

- ✅ Function existence (import will fail)
- ✅ CLI command registration (won't be in command list)
- ✅ Console script installation (won't be in PATH)
- ✅ Subprocess execution (can't fake `subprocess.run`)
- ✅ File operations (real files created and read)
- ✅ State changes (actual manager operations modify real configs)

## Test Structure

### 1. Unit Tests (`TestReloadServerListFunction`)

**Purpose**: Verify the `reload_server_list()` function exists and works correctly.

**Key Tests**:
- `test_reload_function_exists`: Function is importable and callable
- `test_reload_outputs_to_stdout`: Outputs formatted list to stdout
- `test_reload_format_matches_build_server_list`: Output matches initial launch format
- `test_reload_with_empty_registry`: Handles edge case of no servers
- `test_reload_respects_server_states`: Shows correct status indicators

**Gaming Resistance**:
- Uses real `MCPManager` and `ServerCatalog` objects
- Verifies actual stdout output via `capsys`
- Compares output formats between two real function calls
- Tests edge cases that mocks would hide

### 2. CLI Command Tests (`TestTuiReloadCLICommand`)

**Purpose**: Verify `mcpi tui-reload` command exists and is executable.

**Key Tests**:
- `test_tui_reload_command_exists_in_cli`: Command registered in Click
- `test_tui_reload_command_executes_successfully`: Runs without error
- `test_tui_reload_outputs_server_list`: Produces correct output
- `test_tui_reload_respects_client_context`: Uses correct client
- `test_tui_reload_command_via_subprocess`: **CRITICAL** - works as subprocess

**Gaming Resistance**:
- Checks actual CLI command structure (not mocked)
- Uses `CliRunner` to invoke real command
- Calls command via `subprocess.run` (as fzf would)
- Verifies exit codes and output format

### 3. Console Script Tests (`TestReloadConsoleScriptEntry`)

**Purpose**: Verify `mcpi-tui-reload` console script is installed and executable.

**Key Tests**:
- `test_console_script_exists`: Script in PATH (via `which`)
- `test_console_script_executes`: Script is executable

**Gaming Resistance**:
- Uses `which` command to find script (can't fake PATH)
- Verifies file exists at returned path
- Executes script via `subprocess.run`

### 4. fzf Integration Tests (`TestFzfIntegrationWithReload`)

**Purpose**: Verify fzf bindings call reload correctly and show updated state.

**Key Tests**:
- `test_fzf_bindings_include_reload_command`: Bindings reference reload
- `test_reload_called_in_*_binding`: Each operation includes reload
- `test_operation_changes_reflected_in_reload`: **CRITICAL END-TO-END TEST**

**Gaming Resistance**:
- Inspects actual fzf command structure
- Performs real add/remove/enable/disable operations
- Verifies real file changes
- Calls reload and verifies output reflects state changes

### 5. Edge Case Tests (`TestReloadEdgeCases`)

**Purpose**: Verify reload handles errors gracefully.

**Key Tests**:
- `test_reload_with_no_default_client`: No client detected
- `test_reload_with_corrupted_config`: Invalid JSON
- `test_reload_with_permission_error`: Permission denied

**Gaming Resistance**:
- Uses real error conditions (corrupted files, missing clients)
- Verifies graceful failure (not crashes)

### 6. Performance Tests (`TestReloadPerformance`)

**Purpose**: Ensure reload is fast enough for good UX.

**Key Tests**:
- `test_reload_completes_quickly`: < 1 second with 50 servers

**Gaming Resistance**:
- Times actual execution (can't fake timing)
- Uses realistic server count

## Traceability to Requirements

### STATUS Report Gaps Addressed

From `STATUS-2025-11-05-162258.md`:

| Gap | Test Coverage |
|-----|---------------|
| Missing `mcpi-tui-reload` command | `TestReloadConsoleScriptEntry` |
| Reload mechanism broken | `TestFzfIntegrationWithReload` |
| No integration tests | All test classes |
| End-to-end workflow untested | `test_operation_changes_reflected_in_reload` |
| Real subprocess execution untested | `test_tui_reload_command_via_subprocess` |

### PLAN Items Validated

From `BACKLOG-FZF-IMPLEMENTATION-FIX-2025-11-05.md`:

| Work Item | Test Coverage |
|-----------|---------------|
| P0-1: Implement mcpi-tui-reload command | `TestReloadServerListFunction`, `TestTuiReloadCLICommand` |
| P0-2: Add integration tests | All test classes |
| Acceptance Criteria: Command exists | `test_tui_reload_command_exists_in_cli` |
| Acceptance Criteria: Outputs formatted list | `test_reload_outputs_to_stdout` |
| Acceptance Criteria: Works in fzf context | `test_tui_reload_command_via_subprocess` |
| Acceptance Criteria: Respects client context | `test_tui_reload_respects_client_context` |

## Running the Tests

### Run All Reload Tests

```bash
pytest tests/test_tui_reload.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_tui_reload.py::TestReloadServerListFunction -v
```

### Run with Coverage

```bash
pytest tests/test_tui_reload.py --cov=src/mcpi/tui --cov-report=term --cov-report=html
```

### Expected Initial Results

**Before implementation**: Most tests should **FAIL** because:
- `reload_server_list()` function doesn't exist → ImportError
- `mcpi tui-reload` command not registered → Command not found
- `mcpi-tui-reload` console script not installed → FileNotFoundError

**After P0-1 implementation**: All tests should **PASS**, proving:
- Function exists and works
- CLI command is registered
- Console script is installed
- Reload mechanism functions correctly
- End-to-end workflow works

## Manual Testing Checklist

After automated tests pass, perform these manual tests to verify the actual user experience:

### 1. Installation Verification

```bash
# Install package
uv tool install --editable .

# Verify console script
which mcpi-tui-reload
# Expected: /path/to/mcpi-tui-reload

# Test reload command directly
mcpi-tui-reload
# Expected: Formatted server list output
```

### 2. Basic fzf Workflow

```bash
# Launch fzf
mcpi fzf

# Actions:
# 1. Browse servers (should see list)
# 2. Press ctrl-a to add a server
# 3. List should refresh automatically (server now green)
# 4. Press ctrl-d to disable server
# 5. List should refresh (server now yellow)
# 6. Press ctrl-e to enable server
# 7. List should refresh (server now green)
# 8. Press ctrl-r to remove server
# 9. List should refresh (server gone or gray)
```

### 3. Edge Cases

```bash
# Empty registry
mcpi fzf  # with no servers
# Expected: "No servers found" message, not crash

# Rapid operations
# In fzf, press ctrl-a, ctrl-e, ctrl-d rapidly
# Expected: All operations execute, list refreshes, no crashes

# Multiple operations without exit
# Add 3 servers, enable 2, disable 1, remove 1
# Expected: All changes reflected, never need to exit fzf
```

### 4. Verification Criteria

All manual tests should demonstrate:

- ✅ Automatic list refresh after operations (no need to exit/re-launch)
- ✅ Correct status indicators (green ✓ for enabled, yellow ✗ for disabled)
- ✅ No crashes or errors
- ✅ Fast response (reload < 1 second)
- ✅ Multiple operations in one session
- ✅ Graceful handling of edge cases

## Test Coverage Goals

### Minimum Viable (Ship v1.0)

- [ ] 100% of reload function code
- [ ] CLI command registration and execution
- [ ] Console script installation
- [ ] Basic workflow (add → reload → verify)

### Production Quality (Ship v1.1)

- [ ] All edge cases (errors, empty registry, etc.)
- [ ] Performance validation (< 1s)
- [ ] All operation types (add/remove/enable/disable)
- [ ] Integration with all scopes
- [ ] Multi-operation sequences

### Current Status

**Code Coverage**: 0% (function doesn't exist yet)

**Test Coverage**: 100% of planned functionality

**Tests Written**: 25 tests across 6 test classes

**Tests Passing**: Expected 0% (waiting for implementation)

## Relationship to Existing Tests

### Existing TUI Tests (`test_tui_fzf.py`)

**Coverage**: Unit tests for helper functions
- `check_fzf_installed()`
- `get_server_status()`
- `format_server_line()`
- `build_server_list()`
- `build_fzf_command()`

**Gaps**: No tests for actual workflow or reload mechanism

### New Reload Tests (`test_tui_reload.py`)

**Coverage**: Integration and functional tests for reload
- Reload function existence and behavior
- CLI command registration and execution
- Console script installation and execution
- End-to-end workflow with state changes
- Edge cases and error handling

**Complement**: These tests work together:
- Existing tests: "Do the pieces work individually?"
- New tests: "Do the pieces work together in the real workflow?"

## Success Criteria

### Tests Pass → Ship Decision

**Green Light** (Ship v1.0):
- All tests in `TestReloadServerListFunction` pass
- All tests in `TestTuiReloadCLICommand` pass
- All tests in `TestReloadConsoleScriptEntry` pass
- Critical test `test_operation_changes_reflected_in_reload` passes
- Manual testing checklist 100% complete

**Red Light** (Do Not Ship):
- Any test in `TestReloadServerListFunction` fails
- Console script not in PATH
- Subprocess execution fails
- End-to-end test fails
- Manual testing reveals issues

## Maintenance Notes

### When to Update These Tests

**Add new tests when**:
- Adding new fzf operations (e.g., `ctrl-u` for update)
- Adding new server states (beyond enabled/disabled/not-installed)
- Adding new client support
- Changing reload mechanism (e.g., using Python API instead of subprocess)

**Update existing tests when**:
- Changing output format
- Changing command names
- Changing file locations
- Changing error handling behavior

### Test Maintenance Strategy

1. **Keep tests un-gameable**: Always use real objects, real files, real subprocess calls
2. **Add tests first**: When fixing bugs, add test that reproduces bug first
3. **Don't over-mock**: Only mock what's necessary (external systems), use real objects otherwise
4. **Verify tests fail correctly**: Before implementing, verify tests fail for the right reasons

## Common Issues and Solutions

### Issue: Tests Skip Due to Missing Installation

**Symptom**: Tests skip with "mcpi command not installed in PATH"

**Solution**:
```bash
uv tool install --editable .
pytest tests/test_tui_reload.py -v
```

### Issue: Import Errors

**Symptom**: `ImportError: cannot import name 'reload_server_list'`

**Expected**: This is correct before implementation! Tests should fail here.

**Solution**: Implement the function in `src/mcpi/tui.py`

### Issue: Console Script Not Found

**Symptom**: `which mcpi-tui-reload` returns empty

**Expected**: This is correct before implementation!

**Solution**: Add entry point in `pyproject.toml`:
```toml
[project.scripts]
mcpi-tui-reload = "mcpi.tui:reload_server_list"
```

### Issue: Tests Pass But Manual Testing Fails

**Symptom**: All automated tests pass, but fzf doesn't refresh

**Root Cause**: Tests might be too isolated, not testing full integration

**Solution**: Add more integration tests, especially subprocess execution tests

## Conclusion

This test suite provides comprehensive, un-gameable coverage of the TUI reload functionality. Tests verify the actual user workflow works correctly by:

1. Testing real function execution (not mocks)
2. Testing real CLI commands (via CliRunner and subprocess)
3. Testing real file operations (temp directories with actual files)
4. Testing real state changes (operations modify configs, reload reflects changes)
5. Testing as fzf would use it (subprocess execution)

**When all tests pass**, we can be confident that:
- The reload function exists and works
- The CLI command is registered and executable
- The console script is installed and callable
- fzf bindings will trigger reload correctly
- Operations will refresh the list automatically
- The actual user workflow functions as intended

**Test quality**: High - tests cannot be satisfied by stubs, mocks, or shortcuts. They verify real functionality through observable outcomes.
