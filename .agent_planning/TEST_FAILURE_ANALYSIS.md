# Test Failure Analysis - Path to 100% Pass Rate

**Date**: 2025-11-07
**Current Status**: 593/682 passing (87%), 74 failures
**Goal**: 100% pass rate with all tests useful, complete, and flexible

## Executive Summary

The 74 failing tests fall into 5 clear categories:

1. **Obsolete Commands** (26 tests) - Tests for removed/renamed commands
2. **API Contract Changes** (10 tests) - Tests expect dict, API returns ServerConfig object
3. **Missing Command Options** (7 tests) - Tests use --scope flag on commands that don't support it
4. **Test Implementation Bugs** (6 tests) - Edge case assertions with off-by-one errors
5. **Mock/Harness Issues** (25 tests) - Tests patching wrong imports or using stale mocks

**Estimated Effort**: 2-3 hours for 90% of fixes, remainder are easy cleanup

---

## Category 1: Obsolete Commands (26 tests) - DELETE

These tests validate commands that no longer exist in the CLI:

### Commands That Don't Exist:
- `config` command (replaced by client-specific management)
- `install` command (replaced by `add`)
- `uninstall` command (replaced by `remove`)
- `registry validate` command (validation now in integration tests)
- `registry add` command (registry is static JSON)
- `update` command (no auto-update feature)

### Tests to DELETE (26 total):

**test_cli_smoke.py** (13 tests):
- test_registry_validate
- test_config_help
- test_config_show
- test_config_show_json
- test_config_validate
- test_install_help
- test_install_no_args
- test_install_invalid_server
- test_uninstall_help
- test_uninstall_no_args
- test_update_help
- test_registry_add_help
- test_config_init_help (TestCliEdgeCases)

**test_cli_integration.py** (11 tests):
- test_registry_validate
- test_config_show
- test_config_show_json
- test_config_validate
- test_install_nonexistent_server
- test_registry_add_help
- test_config_init_help
- test_update_help
- test_update_registry_mock_network (TestCliWithMockedNetwork)
- test_registry_add_mock_network (TestCliWithMockedNetwork)

**test_cli_targeted_coverage.py** (2 tests):
- test_registry_show_json_output (should use `info` command)
- test_registry_show_server_not_found (should use `info` command)

**Why DELETE not UPDATE**: These commands were intentionally removed as part of architecture changes. The CLI moved from:
- `install/uninstall` → `add/remove` (simpler, clearer names)
- `config` group → client-specific management via plugins
- `registry validate/add` → static registry with integration test validation
- `update` → no auto-update (would require network, package management complexity)

**Alternative Coverage**: Functionality IS tested elsewhere:
- Add/remove: test_functional_cli_workflows.py, test_cli_rescope.py
- Config management: test_clients_*.py unit tests
- Registry validation: test_registry_integration.py
- Server info: test_info_plain_flag.py

---

## Category 2: API Contract Changes (10 tests) - FIX

Tests expect `get_server_config()` to return `dict`, but API now returns `ServerConfig` object.

### Root Cause:
The API evolved to return Pydantic models for type safety, but tests weren't updated.

### Tests to FIX (10 total):

**test_functional_rescope_prerequisites.py** (3 tests):
- test_get_server_config_returns_full_config_dict
  - **Issue**: `assert isinstance(server_config, dict)` but returns `ServerConfig`
  - **Fix**: Accept `ServerConfig | dict`, use `.model_dump()` if needed

- test_get_server_config_works_across_all_scope_types
  - **Issue**: Same as above, checks for dict type
  - **Fix**: Accept `ServerConfig | dict`, validate fields exist

- test_get_server_config_with_complex_config
  - **Issue**: Same as above
  - **Fix**: Accept `ServerConfig | dict`, validate nested data

**test_functional_critical_workflows.py** (3 tests):
- test_get_server_config_returns_complete_data
- test_get_server_config_works_across_all_scopes
- test_manager_get_servers_aggregates_across_scopes (may be related)

**test_functional_user_workflows.py** (1 test):
- test_server_state_management_workflow

**test_installer_workflows_integration.py** (1 test):
- test_server_state_transitions

**test_cli_missing_coverage.py** (2 tests):
- test_status_command_with_json_output
- test_status_command_no_servers_configured

### Fix Strategy:
```python
# OLD (expects dict):
assert isinstance(config, dict)
assert config["command"] == "npx"

# NEW (accepts both):
if isinstance(config, ServerConfig):
    config = config.model_dump()
assert isinstance(config, dict)
assert config["command"] == "npx"

# OR (better - validate object directly):
assert isinstance(config, (dict, ServerConfig))
if isinstance(config, ServerConfig):
    assert config.command == "npx"
else:
    assert config["command"] == "npx"
```

**Estimated Effort**: 30 minutes (straightforward type checking fixes)

---

## Category 3: Missing Command Options (7 tests) - FIX

Tests use `--scope` flag on `enable`/`disable` commands, but those commands don't have that option.

### Root Cause:
Commands have `--client` option (to select client) but not `--scope` (scope is determined by where server is installed).

### Actual Command Signature:
```bash
# What exists:
mcpi enable [OPTIONS] SERVER_ID
  --client TEXT  Target client
  --dry-run

# What tests expect:
mcpi enable --scope user-local SERVER_ID  # ❌ --scope doesn't exist
```

### Tests to FIX (7 total):

**test_tui_scope_cycling.py** (7 tests):
- test_enable_command_respects_scope_parameter
  - **Issue**: `result.invoke(main, ["enable", "test-server", "--scope", "user-local"])`
  - **Fix**: Remove `--scope` parameter, or update to test `--client` parameter

- test_disable_command_respects_scope_parameter
  - **Issue**: Same as above
  - **Fix**: Same as above

- test_scope_list_shows_available_scopes
  - **Issue**: Likely uses `--scope` flag
  - **Fix**: Update to use actual command structure

- test_workflow_add_with_scope_then_list
  - **Issue**: Workflow uses `--scope` on enable/disable
  - **Fix**: Update workflow to match actual CLI

- test_workflow_add_enable_disable_with_scope
  - **Issue**: Same as above
  - **Fix**: Same as above

- test_workflow_list_servers_across_multiple_scopes
  - **Issue**: Same as above
  - **Fix**: Same as above

- test_invalid_scope_shows_clear_error
  - **Issue**: Tests for scope validation on wrong commands
  - **Fix**: Update to test invalid client names instead

### Design Decision Needed:
**Should enable/disable have --scope parameter?**

Current behavior: `enable`/`disable` modify the server where it's installed (determined by scanning all scopes).

Option A: Keep current design, update tests to remove `--scope`
Option B: Add `--scope` parameter to enable/disable for explicit control

**Recommendation**: Option A (keep current design). Scope is an implementation detail - users think "enable the server" not "enable the server in this specific scope". If server exists in multiple scopes, they can use `--client` to disambiguate.

**Estimated Effort**: 45 minutes (update test logic + verify commands work correctly)

---

## Category 4: Test Implementation Bugs (6 tests) - FIX

Edge case tests with incorrect assertions (off-by-one errors, wrong expected values).

### Tests to FIX (6 total):

**test_utils_validation_missing_lines.py** (2 tests):
- test_sanitize_filename_over_255_empty_extension
  - **Issue**: `assert len(result) == 255` but actual is 254
  - **Fix**: Check actual implementation behavior - is 254 or 255 correct?
  - **Root Cause**: When extension is empty (ends with "."), implementation likely strips trailing dot, resulting in 254 chars

- test_sanitize_filename_multiple_dots_over_255
  - **Issue**: Same as above
  - **Fix**: Same as above

**test_utils_logging_comprehensive.py** (2 tests):
- test_setup_logging_with_empty_format_string
  - **Issue**: `assert logger.handlers[0].formatter._fmt == ""` but actual is `'%(message)s'`
  - **Fix**: Implementation uses default format when empty string provided (defensive programming)
  - **Fix**: Update test to expect default format, or change implementation to allow empty

- test_get_logger_with_empty_name
  - **Issue**: Unknown (need to check traceback)
  - **Fix**: Likely similar to above

**test_cli_integration.py** (2 tests):
- test_status_command_no_servers
  - **Issue**: Exit code 2 instead of 0
  - **Fix**: Check if status command has an error in empty state

- test_status_json_no_servers
  - **Issue**: Same as above
  - **Fix**: Same as above

### Fix Strategy:
1. Run each test individually to see exact failure
2. Check implementation to understand actual behavior
3. Update test to match correct behavior OR fix implementation bug
4. Document why the behavior is correct in test comments

**Estimated Effort**: 45 minutes (requires investigation + decision on correct behavior)

---

## Category 5: Mock/Harness Issues (25 tests) - FIX

Tests use outdated mocks, patch wrong imports, or have harness setup issues.

### Tests to FIX (25 total):

**test_cli_new.py** (4 tests) - Wrong Mock Imports:
- test_list_command_basic
  - **Issue**: `@patch("mcpi.cli.ClaudeCodeInstaller")` but that doesn't exist in mcpi.cli
  - **Fix**: Remove obsolete mocks, test passes with real objects

- test_search_command
  - **Issue**: `@patch("mcpi.cli.ServerCatalog")` - patching wrong location
  - **Fix**: Patch where it's used: `@patch("mcpi.cli.get_catalog")` or remove mocks

- test_search_command_json_output
  - **Issue**: Same as above
  - **Fix**: Same as above

- test_search_command_no_results
  - **Issue**: Same as above
  - **Fix**: Same as above

**test_cli_missing_coverage.py** (4 tests) - Obsolete Commands:
- test_registry_info_with_json_output
  - **Issue**: Uses `registry info` command (doesn't exist, should be `info`)
  - **Fix**: Change to `info --json`

- test_registry_search_with_json_output_tuple_result
  - **Issue**: May use obsolete command or mock structure
  - **Fix**: Update to current API

- test_registry_info_server_not_found
  - **Issue**: Uses `registry info` (should be `info`)
  - **Fix**: Change to `info`

**test_functional_rescope_prerequisites.py** (3 tests) - CLI Subprocess Tests:
- test_cli_status_command_works
  - **Issue**: Uses `bin/mcpi` which may not exist or have wrong shebang
  - **Fix**: Use CliRunner instead of subprocess

- test_cli_list_shows_servers
  - **Issue**: Same as above
  - **Fix**: Same as above

- test_cli_help_command_works
  - **Issue**: Same as above
  - **Fix**: Same as above

**test_functional_critical_workflows.py** (3 tests) - API Changes:
- test_list_servers_across_scopes
  - **Issue**: Unknown (needs investigation)
  - **Fix**: Check traceback

- test_add_and_remove_server_workflow
  - **Issue**: Unknown (needs investigation)
  - **Fix**: Check traceback

- test_update_server_preserves_other_servers
  - **Issue**: Unknown (needs investigation)
  - **Fix**: Check traceback

**test_functional_cli_workflows.py** (1 test):
- test_info_command_workflow
  - **Issue**: May expect different output format
  - **Fix**: Update assertions to match current output

**test_cli_scope_features.py** (2 tests) - Interactive Selection:
- test_add_command_interactive_scope_selection
  - **Issue**: Mock/harness setup for interactive input
  - **Fix**: Check mock setup for questionary/prompt

- test_add_command_dry_run_auto_scope
  - **Issue**: Same as above
  - **Fix**: Same as above

**test_cli_smoke.py** (1 test):
- test_info_nonexistent
  - **Issue**: May check wrong exit code or output
  - **Fix**: Verify command returns proper error

**test_tui_reload.py** (4 tests) - TUI Integration:
- test_reload_outputs_to_stdout
  - **Issue**: Mock/capture setup issue
  - **Fix**: Check capsys fixture usage

- test_reload_respects_server_states
  - **Issue**: Mock setup for server states
  - **Fix**: Update mock structure

- test_tui_reload_respects_client_context
  - **Issue**: Client context mock issue
  - **Fix**: Update mock setup

- test_operation_changes_reflected_in_reload
  - **Issue**: Integration test timing/state issue
  - **Fix**: Ensure operations complete before reload

**test_rescope_aggressive.py** (1 test) - Harness Safety:
- test_rescope_add_fails_does_not_remove_from_sources
  - **Issue**: `SAFETY VIOLATION: ClaudeCodePlugin instantiated without path_overrides`
  - **Fix**: Add `path_overrides=harness.path_overrides` to plugin instantiation

**test_installer.py** (1 test) - Pydantic Schema Change:
- test_validate_installation
  - **Issue**: MCPServer schema now requires `command` field
  - **Fix**: Add `command` to test data dict

**test_cli_integration.py** (1 test):
- test_info_nonexistent
  - **Issue**: Duplicate of test_cli_smoke test
  - **Fix**: Check assertions match actual behavior

### Fix Strategy:
1. **Group A - Wrong Patches** (4 tests): Remove obsolete mocks, use real objects
2. **Group B - CLI Subprocess** (3 tests): Switch from subprocess to CliRunner
3. **Group C - Harness Safety** (1 test): Add path_overrides parameter
4. **Group D - Schema Updates** (1 test): Update test data to match current schema
5. **Group E - Output Format** (remaining): Update assertions to match current CLI output

**Estimated Effort**: 90 minutes (most are simple fixes once you understand the pattern)

---

## Priority Order for Implementation

### Phase 1: Quick Wins (30 minutes)
**Delete obsolete tests** - Category 1 (26 tests)
- Delete test files or mark tests as obsolete
- Run test suite to verify 26 fewer failures
- **Impact**: 26 failures → 48 failures (35% reduction)

### Phase 2: API Contract Fixes (30 minutes)
**Fix dict vs ServerConfig** - Category 2 (10 tests)
- Update type checking to accept both dict and ServerConfig
- Add `.model_dump()` conversions where needed
- **Impact**: 48 failures → 38 failures (21% reduction)

### Phase 3: Mock/Harness Fixes (90 minutes)
**Fix mock/harness issues** - Category 5 (25 tests)
- Fix wrong import patches (Group A)
- Switch subprocess to CliRunner (Group B)
- Add path_overrides (Group C)
- Update test data schemas (Group D)
- Fix output assertions (Group E)
- **Impact**: 38 failures → 13 failures (66% reduction)

### Phase 4: Command Option Fixes (45 minutes)
**Remove --scope from enable/disable** - Category 3 (7 tests)
- Update tests to use --client or remove scope parameter
- Verify actual command behavior
- **Impact**: 13 failures → 6 failures (54% reduction)

### Phase 5: Edge Case Fixes (45 minutes)
**Fix test assertions** - Category 4 (6 tests)
- Investigate actual vs expected behavior
- Update assertions or fix implementation
- Document correct behavior
- **Impact**: 6 failures → 0 failures (100% pass rate!)

---

## Test Quality Assessment

### Tests to Keep (All passing tests + fixed failing tests):

**High Value Tests** (testing real functionality):
- test_cli_rescope.py - Comprehensive rescope feature tests
- test_enable_disable_bugs.py - Tests for cross-scope state pollution bugs
- test_functional_cli_workflows.py - End-to-end CLI workflows
- test_info_plain_flag.py - Plain vs rich output modes
- test_cli_completion.py - Shell completion functionality
- test_harness_example.py - Test harness validation
- test_clients_*.py - Client plugin unit tests

**Medium Value Tests** (useful but could be better):
- test_cli_integration.py - After removing obsolete command tests
- test_cli_smoke.py - After removing obsolete command tests
- test_functional_rescope_prerequisites.py - After API contract fixes

**Tests That Need Improvement** (but keep for now):
- test_cli_new.py - Remove excessive mocks, test with real objects
- test_tui_*.py - Some tests are integration tests masquerading as unit tests

### Tests to Delete:
- All tests for obsolete commands (listed in Category 1)

### Tests to Refactor Later (not blocking 100%):
- test_cli_new.py - Consolidate with other CLI tests
- test_cli_missing_coverage.py - Merge into appropriate test files
- test_cli_targeted_coverage.py - Merge into appropriate test files

---

## Success Criteria

After all fixes:
- ✅ 100% test pass rate (682/682 or reduced total after deletions)
- ✅ No tests for non-existent commands
- ✅ All tests use correct API contracts
- ✅ All mocks patch correct imports
- ✅ All harness tests use path_overrides
- ✅ Edge case assertions match actual behavior
- ✅ Test suite runs in <15 seconds
- ✅ All tests follow TestCriteria (useful, complete, flexible)

---

## Estimated Total Effort

- Phase 1: 30 minutes (delete obsolete tests)
- Phase 2: 30 minutes (API contract fixes)
- Phase 3: 90 minutes (mock/harness fixes)
- Phase 4: 45 minutes (command option fixes)
- Phase 5: 45 minutes (edge case fixes)

**Total: 4 hours to 100% pass rate**

**Confidence Level**: High
- Most failures are straightforward (wrong command names, wrong types, wrong mocks)
- No complex logic bugs identified
- No architecture changes needed
- Test infrastructure is solid (harness, fixtures work well)

---

## Risks & Mitigation

### Risk 1: Hidden Dependencies
Some tests may depend on each other or on test execution order.

**Mitigation**: Run tests in random order with `pytest --random-order` to verify independence.

### Risk 2: Real Bugs Discovered
Some test failures may reveal actual bugs in implementation, not just test issues.

**Mitigation**: For each fix, verify actual command behavior manually before updating test. If bug found, fix implementation first, then re-run test.

### Risk 3: Breaking Changes in Fixes
Fixing tests for new API contracts may reveal breaking changes we didn't intend.

**Mitigation**: Review API contract changes carefully. If change breaks user workflows, consider adding backward compatibility or versioning.

---

## Next Steps

1. **Confirm Strategy**: Review this analysis with team/stakeholder
2. **Create Work Items**: Break down into trackable tasks
3. **Execute Phases 1-5**: Implement fixes in priority order
4. **Verify 100%**: Run full test suite, confirm all pass
5. **Refactor**: Consider consolidating test files for maintainability
6. **Document**: Update test documentation with current command structure

---

## Appendix: Detailed Test List

### Category 1: DELETE (26 tests)
```
tests/test_cli_smoke.py::TestCliSmoke::test_registry_validate
tests/test_cli_smoke.py::TestCliSmoke::test_config_help
tests/test_cli_smoke.py::TestCliSmoke::test_config_show
tests/test_cli_smoke.py::TestCliSmoke::test_config_show_json
tests/test_cli_smoke.py::TestCliSmoke::test_config_validate
tests/test_cli_smoke.py::TestCliSmoke::test_install_help
tests/test_cli_smoke.py::TestCliSmoke::test_install_no_args
tests/test_cli_smoke.py::TestCliSmoke::test_install_invalid_server
tests/test_cli_smoke.py::TestCliSmoke::test_uninstall_help
tests/test_cli_smoke.py::TestCliSmoke::test_uninstall_no_args
tests/test_cli_smoke.py::TestCliSmoke::test_update_help
tests/test_cli_smoke.py::TestCliSmoke::test_registry_add_help
tests/test_cli_smoke.py::TestCliEdgeCases::test_config_init_help
tests/test_cli_integration.py::TestCliIntegration::test_registry_validate
tests/test_cli_integration.py::TestCliIntegration::test_config_show
tests/test_cli_integration.py::TestCliIntegration::test_config_show_json
tests/test_cli_integration.py::TestCliIntegration::test_config_validate
tests/test_cli_integration.py::TestCliIntegration::test_install_nonexistent_server
tests/test_cli_integration.py::TestCliIntegration::test_registry_add_help
tests/test_cli_integration.py::TestCliIntegration::test_config_init_help
tests/test_cli_integration.py::TestCliIntegration::test_update_help
tests/test_cli_integration.py::TestCliWithMockedNetwork::test_update_registry_mock_network
tests/test_cli_integration.py::TestCliWithMockedNetwork::test_registry_add_mock_network
tests/test_cli_targeted_coverage.py::TestCLIHighImpactCoverage::test_registry_show_json_output
tests/test_cli_targeted_coverage.py::TestCLIHighImpactCoverage::test_registry_show_server_not_found
tests/test_cli_integration.py::TestCliIntegration::test_info_nonexistent (if duplicate)
```

### Category 2: FIX - API Contract (10 tests)
```
tests/test_functional_rescope_prerequisites.py::TestP0_2_GetServerConfigAPI::test_get_server_config_returns_full_config_dict
tests/test_functional_rescope_prerequisites.py::TestP0_2_GetServerConfigAPI::test_get_server_config_works_across_all_scope_types
tests/test_functional_rescope_prerequisites.py::TestP0_2_GetServerConfigAPI::test_get_server_config_with_complex_config
tests/test_functional_critical_workflows.py::TestCriticalAPI::test_get_server_config_returns_complete_data
tests/test_functional_critical_workflows.py::TestCriticalAPI::test_get_server_config_works_across_all_scopes
tests/test_functional_critical_workflows.py::TestManagerIntegration::test_manager_get_servers_aggregates_across_scopes
tests/test_functional_user_workflows.py::TestServerLifecycleWorkflows::test_server_state_management_workflow
tests/test_installer_workflows_integration.py::TestInstallerWorkflowsWithHarness::test_server_state_transitions
tests/test_cli_missing_coverage.py::TestCLIMissingCoverage::test_status_command_with_json_output
tests/test_cli_missing_coverage.py::TestCLIMissingCoverage::test_status_command_no_servers_configured
```

### Category 3: FIX - Missing Options (7 tests)
```
tests/test_tui_scope_cycling.py::TestScopeParameterSupport::test_enable_command_respects_scope_parameter
tests/test_tui_scope_cycling.py::TestScopeParameterSupport::test_disable_command_respects_scope_parameter
tests/test_tui_scope_cycling.py::TestTUICommandIntegration::test_scope_list_shows_available_scopes
tests/test_tui_scope_cycling.py::TestEndToEndScopeWorkflows::test_workflow_add_with_scope_then_list
tests/test_tui_scope_cycling.py::TestEndToEndScopeWorkflows::test_workflow_add_enable_disable_with_scope
tests/test_tui_scope_cycling.py::TestEndToEndScopeWorkflows::test_workflow_list_servers_across_multiple_scopes
tests/test_tui_scope_cycling.py::TestScopeEdgeCases::test_invalid_scope_shows_clear_error
```

### Category 4: FIX - Test Bugs (6 tests)
```
tests/test_utils_validation_missing_lines.py::TestMissingValidationCoverage::test_sanitize_filename_over_255_empty_extension
tests/test_utils_validation_missing_lines.py::TestMissingValidationCoverage::test_sanitize_filename_multiple_dots_over_255
tests/test_utils_logging_comprehensive.py::TestLoggingErrorScenarios::test_setup_logging_with_empty_format_string
tests/test_utils_logging_comprehensive.py::TestLoggingErrorScenarios::test_get_logger_with_empty_name
tests/test_cli_integration.py::TestCliIntegration::test_status_command_no_servers
tests/test_cli_integration.py::TestCliIntegration::test_status_json_no_servers
```

### Category 5: FIX - Mock/Harness (25 tests)
```
tests/test_cli_new.py::TestCLICommands::test_list_command_basic
tests/test_cli_new.py::TestCLICommands::test_search_command
tests/test_cli_new.py::TestCLICommands::test_search_command_json_output
tests/test_cli_new.py::TestCLICommands::test_search_command_no_results
tests/test_cli_missing_coverage.py::TestCLIMissingCoverage::test_registry_info_with_json_output
tests/test_cli_missing_coverage.py::TestCLIMissingCoverage::test_registry_search_with_json_output_tuple_result
tests/test_cli_missing_coverage.py::TestCLIMissingCoverage::test_registry_info_server_not_found
tests/test_functional_rescope_prerequisites.py::TestP0_4_CoreCLIWorkflows::test_cli_status_command_works
tests/test_functional_rescope_prerequisites.py::TestP0_4_CoreCLIWorkflows::test_cli_list_shows_servers
tests/test_functional_rescope_prerequisites.py::TestP0_4_CoreCLIWorkflows::test_cli_help_command_works
tests/test_functional_critical_workflows.py::TestCoreUserWorkflows::test_list_servers_across_scopes
tests/test_functional_critical_workflows.py::TestCoreUserWorkflows::test_add_and_remove_server_workflow
tests/test_functional_critical_workflows.py::TestCoreUserWorkflows::test_update_server_preserves_other_servers
tests/test_functional_cli_workflows.py::TestCLIBasicCommands::test_info_command_workflow
tests/test_cli_scope_features.py::TestInteractiveScopeSelection::test_add_command_interactive_scope_selection
tests/test_cli_scope_features.py::TestInteractiveScopeSelection::test_add_command_dry_run_auto_scope
tests/test_cli_smoke.py::TestCliEdgeCases::test_info_nonexistent
tests/test_tui_reload.py::TestReloadServerListFunction::test_reload_outputs_to_stdout
tests/test_tui_reload.py::TestReloadServerListFunction::test_reload_respects_server_states
tests/test_tui_reload.py::TestTuiReloadCLICommand::test_tui_reload_respects_client_context
tests/test_tui_reload.py::TestFzfIntegrationWithReload::test_operation_changes_reflected_in_reload
tests/test_rescope_aggressive.py::TestRescopeAggressiveErrorHandling::test_rescope_add_fails_does_not_remove_from_sources
tests/test_installer.py::TestBaseInstaller::test_validate_installation
```

---

## Conclusion

The path to 100% pass rate is clear and achievable. Most failures are from:
1. Tests for commands that were intentionally removed (DELETE)
2. API contracts that evolved (easy FIX)
3. Tests using wrong options (easy FIX)

The test suite is fundamentally sound - no major refactoring needed. After these fixes, we'll have a robust, un-gameable test suite that validates real functionality.
