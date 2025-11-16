# Test Documentation: Scope Cycling Functionality

**Feature**: fzf TUI Scope Cycling (Option B)
**Reference**: `.agent_planning/ANALYSIS-FZF-UX-ISSUES-2025-11-06.md`
**Test File**: `tests/test_tui_scope_cycling.py`
**Status**: Tests written, implementation pending

---

## Overview

This document explains the comprehensive test suite for the scope cycling functionality in the fzf TUI. The tests are designed to be **un-gameable** - they verify real functionality and cannot be satisfied by stubs or shortcuts.

## Feature Requirements

### User-Facing Behavior

1. **Scope Cycling**: User presses `ctrl-s` to cycle through available scopes
2. **Scope Order**: Cycles through: `project-mcp` → `user-global` → `user-internal` → `user-mcp` → (repeat)
3. **Header Display**: Current scope shown in header as "Target Scope: <scope-name>"
4. **Persistent State**: Scope persists across reload operations
5. **No Prompts**: Operations (`ctrl-a`, `ctrl-e`, `ctrl-d`) never trigger interactive scope selection

### Technical Requirements

1. Scope state management (get/set current scope)
2. Scope cycling logic (get next scope with wrapping)
3. Header formatting with scope display
4. fzf command structure with `ctrl-s` binding
5. Operations pass `--scope` parameter to avoid prompts

---

## Test Structure

The test suite is organized into 5 test classes, each focusing on a different layer of functionality:

### 1. `TestScopeCyclingLogic` - Unit Tests

**Purpose**: Verify core scope cycling functions work correctly

**Key Tests**:
- `test_get_available_scopes_returns_correct_list`: Verifies all claude-code scopes available
- `test_get_next_scope_cycles_in_order`: Verifies correct cycling order
- `test_get_next_scope_wraps_around`: Verifies last scope wraps to first
- `test_get_next_scope_handles_single_scope`: Edge case - single scope cycles to itself
- `test_get_next_scope_invalid_current_defaults_to_first`: Error recovery
- `test_format_scope_header_displays_current_scope`: Header formatting
- `test_format_scope_header_fits_80_columns`: Terminal width constraint

**Why Un-gameable**:
- Tests use real scope names from claude-code client
- Tests verify concrete behavior (cycling order, wrapping)
- Tests enforce real-world constraints (80-column terminals)
- Cannot pass without correct logic

### 2. `TestFzfCommandStructure` - Integration Tests

**Purpose**: Verify fzf command structure includes scope cycling

**Key Tests**:
- `test_build_fzf_command_includes_ctrl_s_binding`: Verifies ctrl-s binding exists
- `test_ctrl_s_binding_triggers_scope_cycle`: Verifies binding triggers reload/execute
- `test_header_displays_current_scope`: Verifies scope shown in header
- `test_header_shows_ctrl_s_shortcut`: Verifies discoverability
- `test_operations_include_scope_parameter`: Verifies --scope passed to operations

**Why Un-gameable**:
- Tests extract actual command structure passed to fzf
- Tests verify real fzf binding syntax
- Tests check observable command content
- Cannot pass without proper bindings

### 3. `TestScopeCyclingWorkflow` - Functional Tests

**Purpose**: Verify end-to-end workflows work correctly

**Key Tests**:
- `test_default_scope_on_launch`: Verifies default scope selection
- `test_scope_state_persists_across_operations`: Verifies state management
- `test_cycle_then_add_uses_correct_scope`: **Critical** - verifies add uses cycled scope
- `test_multiple_cycles_maintain_correct_order`: Verifies state integrity
- `test_scope_cycling_no_interactive_prompts`: **Critical** - verifies no Prompt.ask() called
- `test_enable_uses_current_scope_no_prompt`: Verifies enable workflow
- `test_disable_uses_current_scope_no_prompt`: Verifies disable workflow

**Why Un-gameable**:
- Tests complete user workflows from start to finish
- Tests verify actual file system state (config files)
- Tests mock Prompt.ask() to raise if called - ensures no prompts
- Tests verify server added to correct scope by checking scope in config
- Cannot pass without full feature implementation

### 4. `TestScopeCyclingEdgeCases` - Edge Case Tests

**Purpose**: Verify error handling and boundary conditions

**Key Tests**:
- `test_scope_cycling_with_only_one_scope`: Single scope handling
- `test_scope_cycling_with_empty_scope_list`: Empty list handling
- `test_scope_becomes_unavailable_during_session`: Recovery from invalid state
- `test_scope_state_survives_reload_operations`: State persistence

**Why Un-gameable**:
- Tests real-world scenarios users will encounter
- Tests verify graceful error handling (no crashes)
- Tests verify recovery mechanisms work
- Cannot pass without robust error handling

### 5. `TestCompleteScopeCyclingUserJourney` - Integration Test

**Purpose**: Verify complete user journey works end-to-end

**Key Test**:
- `test_complete_user_journey`: **Most Important Test**
  1. Launch fzf (default scope)
  2. Press ctrl-s to cycle to user-global
  3. Press ctrl-s again to cycle to user-internal
  4. Press ctrl-a to add server (should use user-internal)
  5. Verify server added to user-internal scope
  6. Cycle to user-global
  7. Add another server to user-global
  8. Disable server in user-global
  9. Press ctrl-e to enable (should use user-global)
  10. Verify server enabled in user-global scope

**Why Un-gameable**:
- Tests the exact workflow users will perform
- Verifies state at every step of the journey
- Checks actual config files and server states
- Simulates every key press and operation
- Cannot pass without full feature working correctly
- This test alone validates the entire feature

---

## Test Assertions Explained

### Why These Assertions Cannot Be Gamed

1. **File System Checks**:
   ```python
   info = manager.get_server_info("test-server")
   assert info.scope == "user-internal"
   ```
   - Tests verify actual config files on disk
   - Cannot fake with stubs - must write real files
   - Tests use test harness with isolated directories

2. **Command Structure Checks**:
   ```python
   cmd = build_fzf_command(current_scope="user-global")
   assert "user-global" in cmd_str
   assert "--scope" in cmd_str
   ```
   - Tests verify actual command passed to fzf subprocess
   - Cannot pass without proper command structure
   - Tests extract real arguments from command list

3. **State Persistence Checks**:
   ```python
   set_current_scope("user-internal")
   current = get_current_scope()
   assert current == "user-internal"
   ```
   - Tests verify state stored and retrieved correctly
   - Must use real storage mechanism (env var or file)
   - Cannot fake - tests call real get/set functions

4. **No-Prompt Checks**:
   ```python
   monkeypatch.setattr("rich.prompt.Prompt.ask", mock_prompt_ask)
   # mock_prompt_ask raises AssertionError if called
   manager.add_server(..., scope="user-global")
   ```
   - Tests mock Prompt.ask() to raise if called
   - Any prompt triggers test failure
   - Forces implementation to use --scope parameter

5. **Cycling Logic Checks**:
   ```python
   assert get_next_scope("user-mcp", scopes) == "project-mcp"  # Wrap
   ```
   - Tests verify actual cycling behavior
   - Tests check wrapping from last to first
   - Cannot pass without correct modulo arithmetic

---

## Running the Tests

### Run All Scope Cycling Tests

```bash
pytest tests/test_tui_scope_cycling.py -v
```

### Run Specific Test Classes

```bash
# Unit tests only
pytest tests/test_tui_scope_cycling.py::TestScopeCyclingLogic -v

# Functional tests only
pytest tests/test_tui_scope_cycling.py::TestScopeCyclingWorkflow -v

# Complete user journey
pytest tests/test_tui_scope_cycling.py::TestCompleteScopeCyclingUserJourney -v
```

### Run Specific Tests

```bash
# Test the most critical workflow
pytest tests/test_tui_scope_cycling.py::TestCompleteScopeCyclingUserJourney::test_complete_user_journey -v

# Test no-prompt behavior
pytest tests/test_tui_scope_cycling.py::TestScopeCyclingWorkflow::test_scope_cycling_no_interactive_prompts -v
```

### Expected Test Status

**Before Implementation**:
- All tests should **FAIL** with `ImportError` or assertion failures
- Placeholder tests will fail indicating functions don't exist
- This is expected and correct behavior

**After Implementation**:
- All tests should **PASS**
- If any test fails, the implementation is incomplete or incorrect
- Pay special attention to the no-prompt tests

---

## Implementation Checklist

Use tests to guide implementation:

### Phase 1: Core Functions (tui.py)

- [ ] Implement `get_available_scopes(manager: MCPManager) -> List[str]`
- [ ] Implement `get_next_scope(current: str, scopes: List[str]) -> str`
- [ ] Implement `get_current_scope() -> str`
- [ ] Implement `set_current_scope(scope: str) -> None`
- [ ] Implement `get_default_scope(manager: MCPManager) -> str`
- [ ] Implement `format_scope_header(scope: str) -> str`

**Run tests**: `pytest tests/test_tui_scope_cycling.py::TestScopeCyclingLogic -v`

### Phase 2: fzf Command Updates (tui.py)

- [ ] Update `build_fzf_command()` to accept `current_scope` parameter
- [ ] Add scope to header display
- [ ] Add ctrl-s binding for scope cycling
- [ ] Update operation bindings to include `--scope` parameter

**Run tests**: `pytest tests/test_tui_scope_cycling.py::TestFzfCommandStructure -v`

### Phase 3: Integration (tui.py + cli.py)

- [ ] Create console entry point for scope cycling: `mcpi-tui-cycle-scope`
- [ ] Ensure operations respect `--scope` parameter (already in CLI)
- [ ] Update `launch_fzf_interface()` to use default scope

**Run tests**: `pytest tests/test_tui_scope_cycling.py::TestScopeCyclingWorkflow -v`

### Phase 4: Validation

- [ ] Run complete user journey test
- [ ] Manual testing with real fzf
- [ ] Verify no regressions in existing tests

**Run tests**: `pytest tests/test_tui_scope_cycling.py -v`

---

## Test-Driven Development Workflow

1. **Start**: All tests fail (functions don't exist)
2. **Implement Core Functions**: Run unit tests until they pass
3. **Update fzf Command**: Run integration tests until they pass
4. **Wire Everything Together**: Run functional tests until they pass
5. **Verify Complete Journey**: Run user journey test
6. **Manual Verification**: Test with actual fzf interface

**Advantage of TDD Approach**:
- Tests define exact function signatures needed
- Tests verify behavior at each step
- Tests catch regressions immediately
- Tests provide concrete success criteria
- Cannot skip steps - tests enforce completeness

---

## Success Criteria

The implementation is complete when:

1. ✅ All unit tests pass (scope cycling logic works)
2. ✅ All integration tests pass (fzf command structure correct)
3. ✅ All functional tests pass (workflows work end-to-end)
4. ✅ All edge case tests pass (error handling robust)
5. ✅ Complete user journey test passes (feature works as specified)
6. ✅ Manual testing confirms fzf interface works correctly
7. ✅ No regressions in existing tests

---

## Traceability

### STATUS Gaps Addressed

From `STATUS-2025-11-05-232752.md`:
- **Scope Selection UX**: Tests verify no interactive prompts during add/enable/disable
- **fzf Integration**: Tests verify complete fzf command structure with bindings

### PLAN Items Validated

From `PLAN-2025-11-05-233212.md`:
- **P0: Fix Scope Selection Flow**: Tests enforce no-prompt behavior
- **Scope Cycling Feature**: Complete test coverage for Option B implementation

### Requirements Mapped

From `ANALYSIS-FZF-UX-ISSUES-2025-11-06.md`, Issue #3:
- ✅ Scope cycling with ctrl-s
- ✅ Header displays current scope
- ✅ Scope persists across operations
- ✅ Operations use current scope without prompting
- ✅ Scope wraps around correctly
- ✅ Default scope on launch
- ✅ Edge cases handled

---

## Anti-Gaming Measures

### Why These Tests Cannot Be Gamed

1. **Real Execution Paths**: Tests invoke actual functions with real parameters
2. **Observable Outcomes**: Tests verify file system state, command structure, server states
3. **Multiple Verification Points**: Each test checks multiple aspects of behavior
4. **Concrete Assertions**: Tests use specific values (scope names, commands, states)
5. **State Verification**: Tests check persistent changes (config files, scope state)
6. **Error Detection**: Tests mock Prompt.ask() to detect unwanted prompts
7. **End-to-End Validation**: Complete user journey test validates entire workflow

### Common Gaming Attempts Prevented

❌ **Hardcoding scope in add command**: Tests verify scope comes from state, not hardcode
❌ **Stubbing file operations**: Tests use real test harness with actual files
❌ **Faking scope cycling**: Tests verify each step in cycle, including wrap-around
❌ **Ignoring edge cases**: Tests explicitly cover single scope, empty list, invalid scope
❌ **Skipping state persistence**: Tests verify scope survives reload operations
❌ **Triggering prompts**: Tests mock Prompt.ask() to raise if called
❌ **Incomplete implementation**: Complete user journey test validates full workflow

---

## Future Enhancements

These tests provide a foundation for future enhancements:

1. **Bidirectional Cycling**: Add ctrl-shift-s for reverse cycling
2. **Scope Persistence Across Sessions**: Remember last-used scope
3. **Color-Coded Scopes**: Visual distinction between scope types
4. **Scope Filtering**: Only show scopes that support current operation

To add these features:
1. Write tests first (following patterns in this file)
2. Implement feature
3. Verify tests pass
4. Document in this file

---

## Maintenance Notes

### When to Update Tests

- **New scope added**: Update available_scopes assertions
- **Scope order changed**: Update cycling order tests
- **New operation added**: Add no-prompt test for that operation
- **fzf binding changed**: Update command structure tests

### Test Stability

These tests are stable because:
- They test user-visible behavior, not implementation details
- They use real scope names from client plugin
- They verify concrete requirements from specification
- They don't depend on internal refactoring

---

## Summary

This test suite provides:

1. **Comprehensive Coverage**: Unit, integration, functional, edge case, and user journey tests
2. **Un-Gameable Design**: Tests verify real behavior with observable outcomes
3. **TDD-Friendly**: Tests guide implementation step-by-step
4. **Regression Protection**: Tests catch any breaking changes
5. **Documentation**: Tests serve as specification of correct behavior

**Most Important Test**: `test_complete_user_journey` validates the entire feature works as users expect.

**Critical Tests for No-Prompt Requirement**:
- `test_scope_cycling_no_interactive_prompts`
- `test_enable_uses_current_scope_no_prompt`
- `test_disable_uses_current_scope_no_prompt`

If these tests pass, the feature is complete and correct.
