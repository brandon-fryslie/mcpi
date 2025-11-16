# MCPI v2.0.1 Sprint Plan - Test Quality Improvements

**Generated**: 2025-11-16 07:36:37
**Source**: STATUS-2025-11-16-184500.md (Section 4: Test Failure Analysis)
**Sprint Duration**: 1 week (5 working days)
**Sprint Goal**: Achieve 98%+ test pass rate by fixing test quality issues
**Target Release**: v2.0.1

---

## Executive Summary

### Sprint Objective

Fix all 33 failing tests identified in v2.0 to achieve a 98%+ test pass rate. All failures are **test implementation issues**, not production bugs.

### Current State
- Test Pass Rate: 93% (644/692 passing)
- Test Failures: 33 (all test quality issues)
- Production Bugs: 0
- Ship Status: v2.0 READY TO SHIP

### Sprint Deliverables
1. ✅ All 33 test failures resolved
2. ✅ Test pass rate ≥ 98% (680+ tests passing)
3. ✅ Enable/disable mechanism documented
4. ✅ v2.0.1 tagged and released

### Sprint Timeline

```
Day 1: Fix safety check violations (25 tests)
Day 2: Continue safety check fixes + start CLI output updates
Day 3: Complete CLI output updates (7 tests) + fix schema test (1 test)
Day 4: Add enable/disable documentation + final testing
Day 5: Release v2.0.1
```

---

## Test Failure Categories

### Category 1: Safety Check Violations (25 tests)

**Count**: 25 tests
**Effort**: 3 hours
**Root Cause**: Tests not using `mcp_harness` fixture properly
**Priority**: P0 (Critical)

**Error Pattern**:
```
SAFETY VIOLATION: ClaudeCodePlugin instantiated in test mode without path_overrides!
This would modify real Claude Code configuration files.
```

**Affected Files**:
1. `tests/test_cli_integration.py` (3 tests)
2. `tests/test_cli_missing_coverage.py` (5 tests)
3. `tests/test_cli_scope_features.py` (2 tests)
4. `tests/test_cli_targeted_coverage.py` (4 tests)
5. `tests/test_functional_cli_workflows.py` (1 test)
6. `tests/test_functional_critical_workflows.py` (6 tests)
7. `tests/test_functional_rescope_prerequisites.py` (3 tests)
8. `tests/test_functional_user_workflows.py` (1 test)
9. `tests/test_installer_workflows_integration.py` (1 test)
10. `tests/test_rescope_aggressive.py` (1 test)
11. `tests/test_tui_reload.py` (4 tests)

### Category 2: CLI Output Assertion Mismatches (7 tests)

**Count**: 7 tests
**Effort**: 30 minutes
**Root Cause**: Tests expect old CLI output format (before Rich console updates)
**Priority**: P0 (Critical)

**Affected Tests**:
- `test_cli_integration.py::test_status_command_no_servers`
- `test_cli_integration.py::test_status_json_no_servers`
- `test_cli_integration.py::test_info_nonexistent`
- `test_cli_missing_coverage.py::test_registry_info_with_json_output`
- `test_cli_missing_coverage.py::test_registry_search_with_json_output_tuple_result`
- `test_cli_missing_coverage.py::test_status_command_with_json_output`
- `test_cli_missing_coverage.py::test_registry_info_server_not_found`
- `test_cli_missing_coverage.py::test_status_command_no_servers_configured`
- `test_cli_smoke.py::test_info_nonexistent`
- `test_cli_targeted_coverage.py::test_registry_show_json_output`
- `test_cli_targeted_coverage.py::test_registry_show_server_not_found`
- `test_cli_targeted_coverage.py::test_status_with_json_flag`
- `test_cli_targeted_coverage.py::test_status_no_servers_configured`

### Category 3: Test Data Schema Issues (1 test)

**Count**: 1 test
**Effort**: 10 minutes
**Root Cause**: Test data missing required `command` field
**Priority**: P0 (Critical)

**Affected Test**:
- `test_installer.py::TestBaseInstaller::test_validate_installation`

---

## Day 1: Safety Check Violations (Part 1)

**Goal**: Fix 15 of 25 safety check violations
**Time**: 6 hours (with testing)

### Tasks

#### Task 1.1: Fix test_cli_integration.py (3 tests)

**File**: `tests/test_cli_integration.py`
**Tests**: 3
**Time**: 30 minutes

**Tests to Fix**:
1. `test_status_command_no_servers`
2. `test_status_json_no_servers`
3. `test_info_nonexistent`

**Pattern**:
```python
# Add mcp_harness fixture
def test_status_command_no_servers(mcp_harness):
    # Setup harness
    harness = mcp_harness.setup_scope_files()

    # Create plugin with path overrides
    plugin = ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)

    # Continue with test...
```

**Verification**:
```bash
pytest tests/test_cli_integration.py -v
```

---

#### Task 1.2: Fix test_cli_missing_coverage.py (5 tests)

**File**: `tests/test_cli_missing_coverage.py`
**Tests**: 5
**Time**: 45 minutes

**Tests to Fix**:
1. `test_registry_info_with_json_output`
2. `test_registry_search_with_json_output_tuple_result`
3. `test_status_command_with_json_output`
4. `test_registry_info_server_not_found`
5. `test_status_command_no_servers_configured`

**Pattern**: Same as Task 1.1

**Verification**:
```bash
pytest tests/test_cli_missing_coverage.py -v
```

---

#### Task 1.3: Fix test_cli_scope_features.py (2 tests)

**File**: `tests/test_cli_scope_features.py`
**Tests**: 2
**Time**: 30 minutes

**Tests to Fix**:
1. `test_add_command_interactive_scope_selection`
2. `test_add_command_dry_run_auto_scope`

**Pattern**: Same as Task 1.1

**Verification**:
```bash
pytest tests/test_cli_scope_features.py::TestInteractiveScopeSelection -v
```

---

#### Task 1.4: Fix test_cli_targeted_coverage.py (4 tests)

**File**: `tests/test_cli_targeted_coverage.py`
**Tests**: 4
**Time**: 45 minutes

**Tests to Fix**:
1. `test_registry_show_json_output`
2. `test_registry_show_server_not_found`
3. `test_status_with_json_flag`
4. `test_status_no_servers_configured`

**Pattern**: Same as Task 1.1

**Verification**:
```bash
pytest tests/test_cli_targeted_coverage.py::TestCLIHighImpactCoverage -v
```

---

#### Task 1.5: Run Full Test Suite

**Time**: 15 minutes

**Command**:
```bash
pytest --override-ini="addopts=" --tb=short -q
```

**Expected**: 15 tests now passing (659/692 total)

**Commit**:
```bash
git add tests/test_cli_*.py
git commit -m "fix(tests): resolve safety check violations in CLI test files (15 tests)

- Add mcp_harness fixture to tests instantiating ClaudeCodePlugin
- Use path_overrides to prevent real file modification
- Tests now pass without triggering safety checks

Fixes 15 of 33 failing tests in v2.0
Part 1 of test quality improvements for v2.0.1"
```

---

## Day 2: Safety Check Violations (Part 2)

**Goal**: Fix remaining 10 safety check violations
**Time**: 6 hours

### Tasks

#### Task 2.1: Fix test_functional_cli_workflows.py (1 test)

**File**: `tests/test_functional_cli_workflows.py`
**Tests**: 1
**Time**: 15 minutes

**Test to Fix**:
1. `test_info_command_workflow`

**Verification**:
```bash
pytest tests/test_functional_cli_workflows.py::TestCLIBasicCommands::test_info_command_workflow -v
```

---

#### Task 2.2: Fix test_functional_critical_workflows.py (6 tests)

**File**: `tests/test_functional_critical_workflows.py`
**Tests**: 6
**Time**: 90 minutes

**Tests to Fix**:
1. `test_get_server_config_returns_complete_data`
2. `test_get_server_config_works_across_all_scopes`
3. `test_list_servers_across_scopes`
4. `test_add_and_remove_server_workflow`
5. `test_update_server_preserves_other_servers`
6. `test_manager_get_servers_aggregates_across_scopes`

**Verification**:
```bash
pytest tests/test_functional_critical_workflows.py -v
```

---

#### Task 2.3: Fix test_functional_rescope_prerequisites.py (3 tests)

**File**: `tests/test_functional_rescope_prerequisites.py`
**Tests**: 3
**Time**: 45 minutes

**Tests to Fix**:
1. `test_get_server_config_returns_full_config_dict`
2. `test_get_server_config_works_across_all_scope_types`
3. `test_get_server_config_with_complex_config`

**Verification**:
```bash
pytest tests/test_functional_rescope_prerequisites.py::TestP0_2_GetServerConfigAPI -v
```

---

#### Task 2.4: Fix test_functional_user_workflows.py (1 test)

**File**: `tests/test_functional_user_workflows.py`
**Tests**: 1
**Time**: 15 minutes

**Test to Fix**:
1. `test_server_state_management_workflow`

**Verification**:
```bash
pytest tests/test_functional_user_workflows.py::TestServerLifecycleWorkflows::test_server_state_management_workflow -v
```

---

#### Task 2.5: Fix test_installer_workflows_integration.py (1 test)

**File**: `tests/test_installer_workflows_integration.py`
**Tests**: 1
**Time**: 15 minutes

**Test to Fix**:
1. `test_server_state_transitions`

**Verification**:
```bash
pytest tests/test_installer_workflows_integration.py::TestInstallerWorkflowsWithHarness::test_server_state_transitions -v
```

---

#### Task 2.6: Fix test_rescope_aggressive.py (1 test)

**File**: `tests/test_rescope_aggressive.py`
**Tests**: 1
**Time**: 15 minutes

**Test to Fix**:
1. `test_rescope_add_fails_does_not_remove_from_sources`

**Verification**:
```bash
pytest tests/test_rescope_aggressive.py::TestRescopeAggressiveErrorHandling::test_rescope_add_fails_does_not_remove_from_sources -v
```

---

#### Task 2.7: Fix test_tui_reload.py (4 tests)

**File**: `tests/test_tui_reload.py`
**Tests**: 4
**Time**: 60 minutes

**Tests to Fix**:
1. `test_reload_outputs_to_stdout`
2. `test_reload_respects_server_states`
3. `test_tui_reload_respects_client_context`
4. `test_operation_changes_reflected_in_reload`

**Verification**:
```bash
pytest tests/test_tui_reload.py -v
```

---

#### Task 2.8: Run Full Test Suite

**Time**: 15 minutes

**Expected**: 25 tests now passing (669/692 total)

**Commit**:
```bash
git add tests/test_functional_*.py tests/test_installer_*.py tests/test_rescope_*.py tests/test_tui_*.py
git commit -m "fix(tests): resolve safety check violations in functional and TUI tests (10 tests)

- Add mcp_harness fixture to all functional workflow tests
- Update TUI reload tests to use path_overrides
- Prevent real file system modification during testing

Fixes 10 of 33 failing tests in v2.0
Part 2 of test quality improvements for v2.0.1"
```

---

## Day 3: CLI Output + Schema Fixes

**Goal**: Fix remaining 8 test failures
**Time**: 6 hours

### Tasks

#### Task 3.1: Update CLI Output Assertions (7 tests)

**Time**: 2 hours

**Strategy**:
1. Run each failing test to see actual vs expected output
2. Update assertions to match current Rich console format
3. Use flexible matching (contains, regex) where appropriate

**Files to Update**:
- `tests/test_cli_integration.py`
- `tests/test_cli_missing_coverage.py`
- `tests/test_cli_targeted_coverage.py`
- `tests/test_cli_smoke.py`

**Example Fix**:
```python
# OLD (rigid exact match)
assert output == "No MCP servers installed"

# NEW (flexible contains match)
assert "No MCP servers" in output or "no servers" in output.lower()
```

**Verification Per File**:
```bash
pytest tests/test_cli_integration.py -v
pytest tests/test_cli_missing_coverage.py -v
pytest tests/test_cli_targeted_coverage.py -v
pytest tests/test_cli_smoke.py -v
```

**Commit**:
```bash
git add tests/test_cli_*.py
git commit -m "fix(tests): update CLI output assertions to match Rich console format (7 tests)

- Update status command assertions for current output format
- Update info command assertions for current output format
- Use flexible matching (contains) instead of exact equals
- Verify CLI functionality is correct, not exact string match

Fixes 7 of 33 failing tests in v2.0
Part 3 of test quality improvements for v2.0.1"
```

---

#### Task 3.2: Fix Test Data Schema (1 test)

**File**: `tests/test_installer.py`
**Tests**: 1
**Time**: 15 minutes

**Test to Fix**:
`TestBaseInstaller::test_validate_installation`

**Fix**:
```python
# Find test data creation
# Add required 'command' field to MCPServer

test_server = MCPServer(
    name="test-server",
    description="Test server",
    command="npx",  # ADD THIS
    args=["test-package"],
    # ... other fields
)
```

**Verification**:
```bash
pytest tests/test_installer.py::TestBaseInstaller::test_validate_installation -v
```

**Commit**:
```bash
git add tests/test_installer.py
git commit -m "fix(tests): add required 'command' field to test data schema (1 test)

- Update MCPServer test data to include required 'command' field
- Aligns test data with current schema requirements

Fixes 1 of 33 failing tests in v2.0
Part 4 of test quality improvements for v2.0.1"
```

---

#### Task 3.3: Run Full Test Suite

**Time**: 15 minutes

**Expected**: 33 tests now passing (677/692 total = 98%)

**Command**:
```bash
pytest --override-ini="addopts=" --tb=short -q
```

**Verification**:
```bash
# Should see:
# 677 passed, 15 skipped in X.XXs
# Pass rate: 98%
```

**Commit**:
```bash
git add .
git commit -m "test(suite): verify all 33 test failures resolved

Test Results:
- Pass Rate: 98% (677/692 tests passing)
- Failures: 0
- Skipped: 15 (expected)

All test quality issues from v2.0 resolved:
- 25 safety check violations fixed
- 7 CLI output assertions updated
- 1 test data schema fixed

Ready for v2.0.1 release"
```

---

## Day 4: Documentation + Final Testing

**Goal**: Add documentation and verify release readiness
**Time**: 4 hours

### Tasks

#### Task 4.1: Add Enable/Disable Documentation

**File**: `CLAUDE.md`
**Time**: 2 hours

**Section to Add**: "Enable/Disable Mechanisms by Scope"

**Content Structure**:
```markdown
### Enable/Disable Mechanisms by Scope

MCPI supports enabling and disabling servers on a per-scope basis with two different mechanisms:

#### ArrayBased Handler (user-internal, user-mcp scopes)

Scopes where servers are defined as JSON arrays in the mcpServers key.

**Mechanism**:
- **Enable**: Server present in mcpServers array
- **Disable**: Server removed from mcpServers array
- **State Tracking**: Implicit (presence = enabled, absence = disabled)

**Scopes Using ArrayBased**:
- `user-internal`: `~/.claude/settings.json`
- `user-mcp`: `~/.mcp/servers.json` (if exists)

**Example Commands**:
```bash
# Enable server in user-internal scope
mcpi enable browser-tools --scope user-internal

# Disable server in user-internal scope
mcpi disable browser-tools --scope user-internal

# List shows enabled/disabled state
mcpi list --scope user-internal
```

**Configuration Example**:
```json
{
  "mcpServers": {
    "browser-tools": {
      "command": "npx",
      "args": ["-y", "@cloudflare/puppeteer-browser-tools"]
    }
    // Server is enabled by being present
  }
}
```

#### FileTracked Handler (user-global, user-local scopes)

Scopes where servers are defined as JSON objects without a wrapper key.

**Mechanism**:
- **Enable**: Remove server from tracking file
- **Disable**: Add server to tracking file
- **Tracking File**: `.mcpi-disabled-servers-{scope}.json`
- **State Tracking**: Explicit via tracking file

**Scopes Using FileTracked**:
- `user-global`: `.claude/settings.global.json` + `.claude/.mcpi-disabled-servers-global.json`
- `user-local`: `.claude/settings.local.json` + `.claude/.mcpi-disabled-servers-local.json`

**Example Commands**:
```bash
# Enable server in user-global scope
mcpi enable browser-tools --scope user-global

# Disable server in user-global scope
mcpi disable browser-tools --scope user-global

# List shows enabled/disabled state
mcpi list --scope user-global
```

**Configuration Example**:
```json
// .claude/settings.global.json
{
  "browser-tools": {
    "command": "npx",
    "args": ["-y", "@cloudflare/puppeteer-browser-tools"]
  }
  // Server is enabled if NOT in tracking file
}

// .claude/.mcpi-disabled-servers-global.json
{
  "disabled_servers": ["some-other-server"]
  // If browser-tools was here, it would be disabled
}
```

#### Implementation Details

**Code References**:
- ArrayBased Handler: `src/mcpi/clients/claude_code.py` lines 162-186
- FileTracked Handler: `src/mcpi/clients/claude_code.py` lines 188-212
- Tests: `tests/test_enable_disable_bugs.py`

**Design Rationale**:
- ArrayBased: Matches native Claude Code format (mcpServers array)
- FileTracked: Preserves existing server objects, tracks state separately
- Both mechanisms support atomic enable/disable operations
- State is persistent across MCPI invocations

#### Troubleshooting

**Server won't enable/disable**:
- Check scope type (ArrayBased vs FileTracked)
- Verify tracking file exists (FileTracked scopes)
- Run `mcpi list --scope <scope>` to see current state

**State not persisting**:
- Verify configuration files are writable
- Check for syntax errors in JSON files
- Ensure tracking files are in correct location

**See Also**:
- Scope-Based Configuration (CLAUDE.md)
- Test Files: `tests/test_enable_disable_bugs.py`
- Ship Checklist: `.agent_planning/completed/SHIP-CHECKLIST-v2.0-USER-INTERNAL-DISABLE-2025-11-13.md`
```

**Placement**: After "Scope-Based Configuration" section, before "Testing Strategy"

**Verification**:
```bash
# Check formatting
black --check CLAUDE.md

# Visual review
cat CLAUDE.md | grep -A 50 "Enable/Disable Mechanisms"
```

**Commit**:
```bash
git add CLAUDE.md
git commit -m "docs(claude): add comprehensive enable/disable mechanisms documentation

- Document ArrayBased handler (user-internal, user-mcp)
- Document FileTracked handler (user-global, user-local)
- Include examples, commands, and troubleshooting
- Link to implementation and tests

Closes documentation gap from v2.0"
```

---

#### Task 4.2: Final Test Suite Run

**Time**: 30 minutes

**Full Test Suite**:
```bash
pytest --override-ini="addopts=" --tb=short -v
```

**Expected Results**:
- Pass Rate: 98%+
- Failures: 0
- Skipped: 15 (expected)
- Total Time: <5 seconds

**Verification Checklist**:
- [ ] All 677 tests passing
- [ ] 15 tests skipped (as expected)
- [ ] No test failures
- [ ] No safety violations
- [ ] Test execution time <5s

---

#### Task 4.3: Code Quality Checks

**Time**: 30 minutes

**Black Formatting**:
```bash
black src/ tests/
```

**Ruff Linting**:
```bash
ruff check src/ tests/ --fix
```

**Type Checking**:
```bash
mypy src/
```

**Expected**: All checks pass or only non-blocking warnings

---

#### Task 4.4: Manual CLI Verification

**Time**: 15 minutes

**Test Commands**:
```bash
# Test 1: List command
mcpi list --scope user-internal

# Test 2: Search command
mcpi search browser

# Test 3: Info command
mcpi info playwright

# Test 4: Status command
mcpi status

# Test 5: Enable/disable
mcpi disable browser-tools --scope user-internal
mcpi list --scope user-internal  # Should show disabled
mcpi enable browser-tools --scope user-internal
mcpi list --scope user-internal  # Should show enabled
```

**Verification**: All commands work as expected

---

## Day 5: Release v2.0.1

**Goal**: Tag and release v2.0.1
**Time**: 2 hours

### Tasks

#### Task 5.1: Update Changelog

**File**: `.agent_planning/CHANGELOG.md`
**Time**: 30 minutes

**Entry to Add**:
```markdown
## [2.0.1] - 2025-11-XX

### Fixed
- Fixed 33 test failures from v2.0 (test quality issues, not production bugs)
  - 25 safety check violations - tests now use mcp_harness fixture properly
  - 7 CLI output assertion mismatches - updated to match Rich console format
  - 1 test data schema issue - added required 'command' field
- Improved test pass rate from 93% to 98%+ (677/692 tests passing)

### Added
- Comprehensive documentation for enable/disable mechanisms by scope
- Documentation for ArrayBased handler (user-internal, user-mcp)
- Documentation for FileTracked handler (user-global, user-local)

### Changed
- Test suite now runs 98%+ pass rate
- All tests use proper safety checks and fixtures
- CLI output tests use flexible matching instead of exact string comparison

### Testing
- Test pass rate: 98% (677/692 passing, 15 skipped)
- All functional tests passing
- Zero production bugs identified
```

**Commit**:
```bash
git add .agent_planning/CHANGELOG.md
git commit -m "docs(changelog): add v2.0.1 release notes"
```

---

#### Task 5.2: Create Release Tag

**Time**: 15 minutes

**Commands**:
```bash
# Ensure all changes committed
git status

# Create annotated tag
git tag -a v2.0.1 -m "Release v2.0.1 - Test Quality Improvements

Test Suite:
- Pass Rate: 98% (677/692 tests passing)
- Fixed 33 test failures from v2.0
- All safety checks working correctly

Documentation:
- Added enable/disable mechanisms documentation
- Comprehensive examples and troubleshooting

Quality:
- Black formatting clean
- No production bugs
- All CLI commands verified working

This is a quality improvement release. All features from v2.0 remain functional."

# Verify tag
git tag -l -n20 v2.0.1

# Push tag
git push origin v2.0.1
```

---

#### Task 5.3: Create GitHub Release

**Time**: 30 minutes

**Release Title**: MCPI v2.0.1 - Test Quality Improvements

**Release Notes**:
```markdown
# MCPI v2.0.1 - Test Quality Improvements

This release improves test suite quality from v2.0, achieving 98%+ test pass rate.

## What's New

### Test Suite Improvements
- ✅ **98% Test Pass Rate** (677/692 tests passing, up from 93%)
- ✅ **33 Test Failures Fixed** (all test quality issues, zero production bugs)
- ✅ **All Safety Checks Working** (prevents test pollution and real file modification)

### Documentation Additions
- ✅ **Enable/Disable Mechanisms** - Comprehensive guide to enabling/disabling servers by scope
- ✅ **ArrayBased Handler** - Documentation for user-internal and user-mcp scopes
- ✅ **FileTracked Handler** - Documentation for user-global and user-local scopes

## Test Failure Breakdown

All 33 failures were **test implementation issues**, not production bugs:

1. **25 Safety Check Violations** - Tests not using `mcp_harness` fixture properly ✅ FIXED
2. **7 CLI Output Mismatches** - Tests expecting old output format ✅ FIXED
3. **1 Test Data Schema Issue** - Missing required field ✅ FIXED

## Verification

All v2.0 features remain fully functional:
- ✅ All CLI commands working
- ✅ All scope management working
- ✅ Enable/disable per scope working
- ✅ TUI fully functional
- ✅ Zero production bugs

## Quality Metrics

| Metric | v2.0 | v2.0.1 | Change |
|--------|------|--------|--------|
| Test Pass Rate | 93% | 98% | +5% ✅ |
| Tests Passing | 644 | 677 | +33 ✅ |
| Test Failures | 33 | 0 | -33 ✅ |
| Production Bugs | 0 | 0 | 0 ✅ |

## Upgrade Notes

This is a drop-in replacement for v2.0. No configuration changes required.

```bash
# Update via pip
pip install --upgrade mcpi

# Or via uv
uv tool upgrade mcpi
```

## Next Steps

v2.1 is planned for ~1 month from now, featuring DIP Phase 2 architecture improvements for better testability.

See [ROADMAP-POST-V2.0](https://github.com/your-repo/mcpi/blob/master/.agent_planning/ROADMAP-POST-V2.0-2025-11-16-073637.md) for details.

---

**Full Changelog**: https://github.com/your-repo/mcpi/compare/v2.0...v2.0.1
```

**Attach**: Coverage report HTML (if available)

---

#### Task 5.4: Announce Release

**Time**: 15 minutes

**Channels**:
1. GitHub Discussions (if enabled)
2. Project README badge update
3. Documentation site (if exists)

**Message Template**:
```
MCPI v2.0.1 is now available! 🎉

This release improves test suite quality to 98%+ pass rate and adds comprehensive documentation for enable/disable mechanisms.

All 33 test failures from v2.0 have been resolved (they were test implementation issues, not production bugs).

Upgrade: pip install --upgrade mcpi

Release Notes: [link]
```

---

## Sprint Success Criteria

### Must Have (Blocking Release)
- [ ] All 33 test failures resolved
- [ ] Test pass rate ≥ 98%
- [ ] Enable/disable documentation added
- [ ] All quality checks pass (Black, Ruff)
- [ ] v2.0.1 tag created
- [ ] GitHub release published

### Should Have (Non-Blocking)
- [ ] Changelog updated
- [ ] Manual CLI verification complete
- [ ] Coverage report generated
- [ ] Release announcement sent

### Nice to Have
- [ ] Type checking (mypy) clean
- [ ] Coverage increase documented
- [ ] Test execution time benchmarked

---

## Risk Assessment

### Overall Risk: MINIMAL

All work is low-risk test fixes and documentation.

### Risks by Day

**Day 1-2: Safety Check Fixes**
- Risk: LOW - Known pattern, clear fix
- Mitigation: Test each file individually before moving on

**Day 3: CLI Output + Schema**
- Risk: MINIMAL - Simple assertion updates
- Mitigation: Verify CLI functionality, not just test passing

**Day 4: Documentation**
- Risk: NONE - Documentation only
- Mitigation: N/A

**Day 5: Release**
- Risk: LOW - Tag creation and publishing
- Mitigation: Verify all tests pass before tagging

---

## Rollback Plan

If v2.0.1 has issues:

1. **Revert tag**: `git tag -d v2.0.1 && git push origin :refs/tags/v2.0.1`
2. **Delete release**: Remove from GitHub releases
3. **Notify users**: Post rollback notice
4. **Fix issues**: Address problems in new branch
5. **Re-release**: Create v2.0.2 with fixes

---

## Daily Checklist

### Day 1
- [ ] Fix test_cli_integration.py (3 tests)
- [ ] Fix test_cli_missing_coverage.py (5 tests)
- [ ] Fix test_cli_scope_features.py (2 tests)
- [ ] Fix test_cli_targeted_coverage.py (4 tests)
- [ ] Run full test suite
- [ ] Commit changes

### Day 2
- [ ] Fix test_functional_cli_workflows.py (1 test)
- [ ] Fix test_functional_critical_workflows.py (6 tests)
- [ ] Fix test_functional_rescope_prerequisites.py (3 tests)
- [ ] Fix test_functional_user_workflows.py (1 test)
- [ ] Fix test_installer_workflows_integration.py (1 test)
- [ ] Fix test_rescope_aggressive.py (1 test)
- [ ] Fix test_tui_reload.py (4 tests)
- [ ] Run full test suite
- [ ] Commit changes

### Day 3
- [ ] Update CLI output assertions (7 tests)
- [ ] Fix test data schema (1 test)
- [ ] Run full test suite
- [ ] Verify 98% pass rate
- [ ] Commit changes

### Day 4
- [ ] Add enable/disable documentation to CLAUDE.md
- [ ] Run full test suite
- [ ] Run code quality checks (Black, Ruff, mypy)
- [ ] Manual CLI verification
- [ ] Commit documentation

### Day 5
- [ ] Update CHANGELOG.md
- [ ] Create v2.0.1 tag
- [ ] Push tag to remote
- [ ] Create GitHub release
- [ ] Announce release
- [ ] Celebrate! 🎉

---

## Conclusion

This sprint plan provides a clear path to v2.0.1 release with 98%+ test pass rate.

**Key Points**:
- All work is low-risk test fixes
- 1 week timeline is realistic
- No production code changes required
- Documentation gap will be closed
- Sets foundation for v2.1 (DIP Phase 2)

**Next Steps After v2.0.1**:
1. Start planning v2.1 (DIP Phase 2)
2. Gather user feedback on v2.0.1
3. Identify any additional bugs or features
4. Begin DIP Phase 2 implementation

---

**Sprint Plan Date**: 2025-11-16 07:36:37
**Sprint Duration**: 5 days
**Sprint Goal**: 98%+ test pass rate + documentation
**Target Release**: v2.0.1
