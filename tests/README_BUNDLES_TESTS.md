# Smart Server Bundles - Functional Test Suite

**Created**: 2025-11-16
**Feature**: Smart Server Bundles (Pre-Implementation Tests)
**Test File**: `tests/test_bundles.py`
**Status**: Tests written, awaiting implementation

---

## Overview

This test suite defines the expected behavior for the Smart Server Bundles feature through comprehensive functional tests. These tests validate real user workflows and cannot be satisfied by stub implementations.

**Key Principle**: Tests written FIRST to define the contract that implementation must fulfill.

---

## Test Coverage Summary

### Total Tests: 18

**By Category**:
- Bundle Catalog Tests: 5 tests
- Bundle Installation Tests: 5 tests
- CLI Command Tests: 5 tests
- Integration Workflow Tests: 3 tests

**By User Journey**:
- Discovery & Information: 4 tests
- Installation & Configuration: 8 tests
- Error Handling & Edge Cases: 4 tests
- End-to-End Workflows: 2 tests

---

## Test Categories

### 1. Bundle Catalog Tests (5 tests)

Tests that validate bundle loading, querying, and catalog management.

**User Workflows Covered**:
- Loading bundle definitions from JSON files
- Listing all available bundles
- Retrieving specific bundle information
- Handling missing or corrupted bundle files
- Enforcing Pydantic schema validation

**Why These Tests Are Un-Gameable**:
- Verify actual file I/O from disk
- Check parsed data matches file contents exactly
- Validate Pydantic schema enforcement (typed objects)
- Test error handling with real invalid data
- Multiple verification points per test

**Tests**:
1. `test_catalog_loads_bundle_from_file` - Basic bundle loading
2. `test_catalog_lists_all_bundles` - Catalog listing functionality
3. `test_catalog_handles_missing_directory` - Graceful degradation
4. `test_catalog_rejects_invalid_json` - Error handling for corrupted files
5. `test_catalog_validates_bundle_schema` - Schema validation enforcement

---

### 2. Bundle Installation Tests (5 tests)

Tests that validate server installation from bundles with real file operations.

**User Workflows Covered**:
- Installing all servers from a bundle to a scope
- Installing same bundle to multiple scopes
- Handling already-installed servers (skip duplicates)
- Dry-run mode (preview without changes)
- Error recovery when bundle references missing servers

**Why These Tests Are Un-Gameable**:
- Verify actual config files created on disk
- Check file contents match expected structure
- Validate all servers from bundle installed
- Test integration with real MCPManager
- Multiple independent verification points

**Tests**:
1. `test_install_bundle_adds_all_servers_to_scope` - Core installation
2. `test_install_bundle_to_different_scope` - Scope independence
3. `test_install_bundle_skips_existing_servers` - Duplicate handling
4. `test_install_bundle_dry_run_mode` - Preview functionality
5. `test_install_bundle_handles_missing_server_in_catalog` - Error recovery

---

### 3. CLI Command Tests (5 tests)

Tests that validate user-facing CLI commands using Click test runner.

**User Workflows Covered**:
- `mcpi bundle list` - Show available bundles
- `mcpi bundle info <name>` - Show bundle details
- `mcpi bundle install <name>` - Install bundle
- Error handling for invalid bundle names
- Dry-run flag functionality

**Why These Tests Are Un-Gameable**:
- Execute actual CLI commands via Click CliRunner
- Verify command output matches expectations
- Check exit codes (success vs error)
- Validate error messages are helpful
- Test side effects (files created, etc.)

**Tests**:
1. `test_bundle_list_command_shows_available_bundles` - List command
2. `test_bundle_info_command_shows_bundle_details` - Info command
3. `test_bundle_info_command_handles_missing_bundle` - Error handling
4. `test_bundle_install_command_installs_bundle` - Install command
5. `test_bundle_install_command_dry_run_flag` - Dry-run mode

---

### 4. Integration Workflow Tests (3 tests)

Tests that validate complete end-to-end user journeys.

**User Workflows Covered**:
- Complete workflow: list → info → install → verify
- Test harness isolation (safe parallel testing)
- Custom server configurations in bundles

**Why These Tests Are Un-Gameable**:
- Test complete workflows start to finish
- Verify integration between all components
- Check real file system state changes
- Validate actual MCP client config files
- Multi-step verification chains

**Tests**:
1. `test_complete_bundle_workflow_list_info_install` - Full workflow
2. `test_bundle_installation_isolated_in_test_harness` - Test safety
3. `test_bundle_with_custom_server_configs` - Config overrides

---

## Running the Tests

### Current State (Pre-Implementation)

All tests currently **skip** because the feature isn't implemented yet:

```bash
pytest tests/test_bundles.py -v

# Output:
# 18 skipped in 0.03s
```

This is expected! Tests define what needs to be built.

### After Implementation

Once the Smart Server Bundles feature is implemented, run:

```bash
# Run all bundle tests
pytest tests/test_bundles.py -v

# Run specific test class
pytest tests/test_bundles.py::TestBundleCatalog -v

# Run specific test
pytest tests/test_bundles.py::TestBundleCatalog::test_catalog_loads_bundle_from_file -v

# Run with coverage
pytest tests/test_bundles.py --cov=src/mcpi/bundles --cov-report=term
```

**Expected Results After Implementation**:
- All 18 tests passing (0 failures)
- 90%+ code coverage for bundle module
- Fast test execution (<5 seconds total)
- No warnings or errors

---

## Test Design Principles

### 1. User-Centric Structure

Every test follows this pattern:

```
Given: [Realistic starting state user would have]
When: [User performs actual action via real interface]
Then: [Verify all observable outcomes user would see]
And: [Verify side effects and state changes]
```

### 2. Multiple Verification Points

Each test validates multiple independent aspects:
- Primary outcome (did the operation succeed?)
- File system changes (were files created/modified correctly?)
- Data integrity (is file content valid and complete?)
- Error handling (are failures graceful with clear messages?)
- State consistency (is overall system state correct?)

### 3. Real Execution Path

Tests invoke the actual user-facing interfaces:
- BundleCatalog class (real file loading)
- BundleInstaller class (real manager integration)
- CLI commands (real Click command execution)
- MCPTestHarness (real file operations in temp dirs)

### 4. Gaming Resistance

Tests structured to prevent shortcuts:

**Cannot be faked by**:
- Returning hardcoded data (tests check file contents)
- Using mocks for primary functionality (tests use real components)
- Skipping validation (tests verify Pydantic enforcement)
- Ignoring errors (tests check error handling explicitly)
- Empty implementations (tests verify complete data flow)

**Must use real**:
- File I/O (read/write JSON files)
- Pydantic validation (schema enforcement)
- MCPManager integration (actual server installation)
- Click CLI framework (real command execution)

---

## Traceability to Requirements

### STATUS Report Gaps Addressed

From `.agent_planning/STATUS-SMART-BUNDLES-EVALUATION-2025-11-16-165533.md`:

| STATUS Gap | Test Coverage |
|------------|---------------|
| Bundle catalog loading | TestBundleCatalog (5 tests) |
| Bundle installation | TestBundleInstallation (5 tests) |
| CLI commands | TestBundleCLICommands (5 tests) |
| Error handling | All categories (distributed) |
| Integration with MCPManager | TestBundleIntegrationWorkflows |

### PLAN Work Items Validated

From `.agent_planning/PLAN-SMART-BUNDLES-2025-11-16-165848.md`:

| Work Item | Test Coverage |
|-----------|---------------|
| BUNDLE-001: Bundle models | All tests (Pydantic validation) |
| BUNDLE-002: BundleCatalog class | TestBundleCatalog |
| BUNDLE-005-010: BundleInstaller | TestBundleInstallation |
| BUNDLE-011-017: CLI commands | TestBundleCLICommands |
| BUNDLE-019: Functional tests | TestBundleIntegrationWorkflows |

---

## Acceptance Criteria Coverage

From implementation plan, these tests validate:

**Must-Have Functionality**:
- ✅ `mcpi bundle list` shows all available bundles (tested)
- ✅ `mcpi bundle info <bundle>` shows bundle details (tested)
- ✅ `mcpi bundle install <bundle>` installs all servers (tested)
- ✅ Dry-run mode works correctly (tested)
- ✅ Interactive scope selection (framework tested, CLI test added)
- ✅ Clear progress output (CLI test validates)

**Error Handling**:
- ✅ Missing bundle: Clear error message (tested)
- ✅ Already-installed servers: Skip with message (tested)
- ✅ Installation failures: Graceful handling (tested)
- ✅ Invalid scope: Error with valid scopes (testable via manager)

**Data Integrity**:
- ✅ Bundle JSON validation (tested)
- ✅ Server catalog integration (tested)
- ✅ Config file correctness (tested)
- ✅ Scope isolation (tested)

---

## Implementation Guidance

### For Developers Implementing This Feature

**Start Here**:
1. Read test docstrings - they describe exact user workflows
2. Run `pytest tests/test_bundles.py --collect-only` to see all tests
3. Implement until tests pass (TDD approach)

**Development Process**:
1. **Phase 1**: Implement `Bundle` and `BundleServer` Pydantic models
   - Run: `pytest tests/test_bundles.py::TestBundleCatalog -v`
   - Fix until catalog tests pass

2. **Phase 2**: Implement `BundleInstaller` class
   - Run: `pytest tests/test_bundles.py::TestBundleInstallation -v`
   - Fix until installation tests pass

3. **Phase 3**: Implement CLI commands
   - Run: `pytest tests/test_bundles.py::TestBundleCLICommands -v`
   - Fix until CLI tests pass

4. **Phase 4**: Integration & polish
   - Run: `pytest tests/test_bundles.py -v`
   - Fix until all 18 tests pass

**Key Implementation Notes**:

From the tests, implementation MUST:
- Use Pydantic models for all data structures (`Bundle`, `BundleServer`)
- Follow DIP pattern with factory functions (`create_test_bundle_catalog()`)
- Integrate with existing `MCPManager` (use `add_server()` method)
- Support dry-run mode throughout
- Handle errors gracefully (invalid JSON, missing servers, etc.)
- Write valid JSON config files
- Use MCPTestHarness for test isolation

---

## Test Fixtures

### Provided Fixtures

**Bundle Data**:
- `bundle_data_dir` - Temporary directory for bundle files
- `sample_bundle_json` - Minimal valid bundle (2 servers)
- `web_dev_bundle_json` - Realistic web-dev bundle (4 servers)
- `multi_bundle_dir` - Directory with 3 test bundles

**Test Infrastructure**:
- `mcp_manager_with_harness` - MCPManager + test harness (from conftest)
- `mcp_test_dir` - Temporary directory (from conftest)

**File Creation**:
- `sample_bundle_file` - Creates bundle JSON file on disk
- `multi_bundle_dir` - Creates multiple bundle files

### Fixture Philosophy

Fixtures create realistic test data that:
- Matches planned bundle structure (web-dev, data-science, etc.)
- Uses real server IDs from catalog
- Creates actual files on disk (JSON)
- Provides both minimal and realistic test cases

---

## Success Metrics

### When Implementation is Complete

**Quantitative**:
- 18/18 tests passing (100%)
- 90%+ code coverage for `src/mcpi/bundles/`
- Test execution time <5 seconds
- Zero test warnings or errors

**Qualitative**:
- Tests pass without modification (implementation fits contract)
- No tests skipped or xfailed
- Error messages in tests are helpful
- Test output is clean and readable

### If Tests Fail After Implementation

**Common Issues**:

1. **Import errors** - Feature modules not created
   - Create `src/mcpi/bundles/` directory
   - Add `__init__.py`, `models.py`, `catalog.py`, `installer.py`

2. **Pydantic validation errors** - Model schema mismatch
   - Check `Bundle` and `BundleServer` model definitions
   - Ensure required fields match test data

3. **File I/O errors** - Path handling issues
   - Use `Path` objects consistently
   - Handle missing directories gracefully

4. **Integration errors** - MCPManager compatibility
   - Use existing `add_server()` method
   - Don't duplicate installation logic

5. **Test harness errors** - Path override issues
   - Use `path_overrides` from harness
   - Don't write to real user directories

---

## Maintenance

### When to Update Tests

**Add new tests when**:
- New bundle functionality added (e.g., bundle remove, bundle update)
- New error cases discovered
- New CLI options added
- Edge cases found in production

**Modify existing tests when**:
- Bundle data structure changes (update fixtures)
- CLI output format changes (update assertions)
- Error message wording changes (update checks)

**Never modify tests to**:
- Make failing tests pass (fix implementation instead)
- Remove verification points (maintain test rigor)
- Add mocks for primary functionality (keep tests real)

### Test Hygiene

**Before committing**:
```bash
# Ensure tests pass
pytest tests/test_bundles.py -v

# Check test coverage
pytest tests/test_bundles.py --cov=src/mcpi/bundles --cov-report=term

# Verify no test pollution
pytest tests/test_bundles.py --tb=short -x
```

**Keep tests**:
- Independent (no test order dependencies)
- Isolated (use fixtures and temp directories)
- Fast (avoid unnecessary delays)
- Clear (good docstrings and assertions)

---

## Contact & Questions

**Test Suite Author**: AI Test Architect
**Created For**: MCPI Smart Server Bundles Feature
**Related Files**:
- Implementation Plan: `.agent_planning/PLAN-SMART-BUNDLES-2025-11-16-165848.md`
- Evaluation: `.agent_planning/STATUS-SMART-BUNDLES-EVALUATION-2025-11-16-165533.md`
- Main Test File: `tests/test_bundles.py`

**Questions?**
- Read test docstrings for detailed user journey descriptions
- Check assertions for exact validation requirements
- See fixtures for test data structure examples
- Review existing test patterns in `tests/test_installer_workflows_integration.py`

---

**Remember**: These tests define the contract. Implementation must fulfill the contract, not the other way around.
