# Multi-Catalog Phase 1 Test Suite Summary

**Created**: 2025-11-17
**Status**: Tests written, awaiting implementation
**Total Tests**: 72 (23 unit + 28 integration + 21 E2E)
**Current Result**: All 72 tests SKIPPED (implementation not started)

---

## Overview

This document summarizes the comprehensive test suite for Multi-Catalog Phase 1 (v0.4.0) feature. Tests are designed to be **un-gameable**, validate real functionality, and serve as the contract for implementation.

### Test Philosophy

These tests follow the principles from your instructions:

1. **Useful** - Test real functionality, not implementation details
2. **Complete** - Cover all edge cases, error paths, and user workflows
3. **Flexible** - Allow refactoring without changing tests
4. **Automated** - Use pytest framework with proper fixtures
5. **Un-gameable** - Validate actual user-facing behavior, not mocks

### Gaming Resistance Features

- ✅ Real filesystem operations (tmp_path fixtures)
- ✅ Actual JSON file validation (not mocked)
- ✅ Observable outcomes (file existence, content verification)
- ✅ CLI integration testing (Click's CliRunner)
- ✅ Complete workflows (search → info → add)
- ✅ Session persistence testing (destroy object, recreate, verify state)
- ✅ Error handling validation (permission errors, corrupted files)

---

## Test Files

### 1. tests/test_catalog_manager.py (23 unit tests)

**Purpose**: Unit tests for CatalogManager class core functionality

**Test Coverage**:
- Constructor and dependency injection (2 tests)
- Lazy loading behavior (6 tests)
- Case-insensitive catalog lookup (verified in get_catalog tests)
- Search across catalogs with ordering (5 tests)
- Factory functions (3 tests)
- Error handling (3 tests)

**Key Test Classes**:

```python
TestCatalogManagerInit (2 tests)
├── test_init_with_paths - Constructor accepts paths
└── test_init_does_not_load_catalogs - Lazy loading (catalogs not loaded on init)

TestCatalogManagerGetCatalog (7 tests)
├── test_get_catalog_official - Returns official catalog
├── test_get_catalog_local - Returns local catalog
├── test_get_catalog_invalid - Returns None for unknown
├── test_get_catalog_case_insensitive - OFFICIAL/Official/official all work
├── test_get_catalog_lazy_loading - Only loads on first access
├── test_get_catalog_caching - Returns same instance on repeat access
└── test_get_default_catalog - Default is official

TestCatalogManagerListCatalogs (3 tests)
├── test_list_catalogs - Returns 2 CatalogInfo objects
├── test_list_catalogs_metadata - Correct name, type, path, description
└── test_list_catalogs_server_count - Accurate server counts

TestCatalogManagerSearchAll (5 tests)
├── test_search_all_official_only - Finds in official
├── test_search_all_local_only - Finds in local
├── test_search_all_both_catalogs - Finds in both, correct order
├── test_search_all_same_id_not_deduplicated - Duplicates NOT removed
└── test_search_all_empty - Empty list when no matches

TestCatalogManagerFactories (3 tests)
├── test_create_default_catalog_manager - Factory creates with correct paths
├── test_create_default_catalog_manager_init_error - Handles PermissionError
└── test_create_test_catalog_manager - Test factory accepts custom paths

TestCatalogManagerErrorHandling (3 tests)
├── test_local_catalog_missing - Graceful handling
├── test_official_catalog_missing_raises - Appropriate error
└── test_corrupted_catalog_file - JSON error handling
```

**Gaming Resistance**:
- Creates real JSON files in tmp_path
- Verifies actual file content, not mocked responses
- Tests lazy loading by checking private attributes (_official, _local)
- Validates ordering by inspecting actual result order
- Tests error paths with real filesystem errors

---

### 2. tests/test_cli_catalog_commands.py (28 integration tests)

**Purpose**: Integration tests for CLI commands with catalog support

**Test Coverage**:
- catalog list command (3 tests)
- catalog info command (4 tests)
- search --catalog flag (8 tests)
- info --catalog flag (4 tests)
- add --catalog flag (2 tests)
- Help text validation (3 tests)
- Backward compatibility (3 tests)

**Key Test Classes**:

```python
TestCatalogListCommand (3 tests)
├── test_catalog_list_shows_both - Shows official + local
├── test_catalog_list_shows_metadata - Shows type, count, description
└── test_catalog_list_rich_table - Rich table formatting

TestCatalogInfoCommand (4 tests)
├── test_catalog_info_official - Shows official details
├── test_catalog_info_local - Shows local details
├── test_catalog_info_case_insensitive - OFFICIAL/Official work
└── test_catalog_info_unknown - Error for unknown catalog

TestSearchWithCatalog (8 tests)
├── test_search_default_catalog - Default is official (backward compat)
├── test_search_with_catalog_official - --catalog official works
├── test_search_with_catalog_local - --catalog local works
├── test_search_with_catalog_case_insensitive - Case-insensitive
├── test_search_all_catalogs - --all-catalogs searches both
├── test_search_all_catalogs_groups_results - Results grouped by catalog
├── test_search_catalog_mutually_exclusive - Error if both flags used
└── test_search_unknown_catalog - Error for unknown catalog

TestInfoWithCatalog (4 tests)
├── test_info_default_catalog - Default searches official
├── test_info_with_catalog_official - --catalog official works
├── test_info_with_catalog_local - --catalog local works
└── test_info_server_not_in_catalog - Clear error when not found

TestAddWithCatalog (2 tests)
├── test_add_default_catalog - Default uses official
└── test_add_with_catalog_local - --catalog local works

TestCatalogHelpText (3 tests)
├── test_catalog_group_help - Help text exists
├── test_search_help_shows_catalog_flags - Flags documented
└── test_info_help_shows_catalog_flag - Flag documented

TestBackwardCompatibility (3 tests)
├── test_search_without_flags - Old pattern still works
├── test_info_without_flags - Old pattern still works
└── test_add_without_flags - Old pattern still works
```

**Gaming Resistance**:
- Uses Click's CliRunner for actual CLI invocation
- Verifies exit codes (0 for success, non-zero for errors)
- Validates actual output text (not mocked responses)
- Tests with real catalog files in tmp_path
- Checks for specific strings in output (proves command executed)

---

### 3. tests/test_multi_catalog_e2e.py (21 E2E tests)

**Purpose**: End-to-end workflow tests for complete user scenarios

**Test Coverage**:
- Fresh install behavior (4 tests)
- Local catalog persistence (2 tests)
- Complete workflows (3 tests)
- Backward compatibility (3 tests)
- Deprecation warnings (2 tests)
- Error handling (2 tests)
- Catalog info details (2 tests)
- Search ordering (1 test)
- CLI usability (3 tests)

**Key Test Classes**:

```python
TestFreshInstall (4 tests)
├── test_fresh_install_creates_local_catalog - Auto-creates local
├── test_local_catalog_auto_initialization - Creates if missing
├── test_local_catalog_empty_on_first_run - Empty initially
└── test_official_catalog_always_available - Works even if local fails

TestLocalCatalogPersistence (2 tests)
├── test_local_catalog_persistence - Survives session restart
└── test_multiple_sessions_accumulate - Multiple adds work

TestCompleteWorkflows (3 tests)
├── test_search_and_add_from_official - Full workflow
├── test_search_all_catalogs_workflow - Multi-catalog search
└── test_catalog_list_shows_both - List command works

TestBackwardCompatibility (3 tests)
├── test_old_factory_function_still_works - Deprecated but functional
├── test_old_cli_patterns_work - Old CLI unchanged
└── test_no_breaking_changes_to_cli - No regressions

TestDeprecationWarnings (2 tests)
├── test_create_default_catalog_shows_warning - Warning appears
└── test_deprecation_warning_clear_and_helpful - Message is clear

TestErrorHandling (2 tests)
├── test_permission_error_graceful_degradation - Handles permissions
└── test_corrupted_local_catalog_handled - Handles corrupt JSON

TestCatalogInfoDetails (2 tests)
├── test_catalog_info_shows_server_samples - Shows examples
└── test_catalog_info_shows_categories - Shows stats

TestSearchOrdering (1 test)
└── test_search_all_catalogs_ordering - Catalog priority + alphabetical

TestCLIUsability (3 tests)
├── test_helpful_error_for_unknown_catalog - Clear errors
├── test_help_text_includes_examples - Documentation exists
└── test_catalog_commands_fast - Performance < 1 second
```

**Gaming Resistance**:
- Creates isolated home directories (monkeypatch Path.home())
- Tests actual filesystem persistence (destroy object, recreate, verify)
- Validates deprecation warnings appear (catches warnings context)
- Tests permission errors with real chmod operations
- Validates timing (ensures performance requirements met)

---

## Test Execution

### Run All Tests

```bash
pytest tests/test_catalog_manager.py tests/test_cli_catalog_commands.py tests/test_multi_catalog_e2e.py -v
```

### Run by Category

```bash
# Unit tests only
pytest tests/test_catalog_manager.py -v

# Integration tests only
pytest tests/test_cli_catalog_commands.py -v

# E2E tests only
pytest tests/test_multi_catalog_e2e.py -v
```

### Run Specific Test

```bash
pytest tests/test_catalog_manager.py::TestCatalogManagerSearchAll::test_search_all_both_catalogs -v
```

### Current Status (Before Implementation)

```bash
$ pytest tests/test_catalog_manager.py tests/test_cli_catalog_commands.py tests/test_multi_catalog_e2e.py -v

============================= test session starts ==============================
collected 72 items

tests/test_catalog_manager.py::TestCatalogManagerInit::test_init_with_paths SKIPPED
tests/test_catalog_manager.py::TestCatalogManagerInit::test_init_does_not_load_catalogs SKIPPED
[... 70 more SKIPPED ...]

============================= 72 skipped in 0.07s ==============================
```

**All tests SKIPPED** - This is correct! Tests skip because:
- `from mcpi.registry.catalog_manager import CatalogManager` fails (doesn't exist yet)
- `pytestmark = pytest.mark.skipif(not CATALOG_MANAGER_EXISTS, ...)` skips all

---

## Expected Test Results After Implementation

### Phase 1 Complete (v0.4.0)

After implementing CatalogManager and CLI commands:

```bash
$ pytest tests/test_catalog_manager.py tests/test_cli_catalog_commands.py tests/test_multi_catalog_e2e.py -v

============================= 72 passed in X.XXs ==============================
```

**Success Criteria**:
- ✅ All 72 tests pass
- ✅ No skipped tests
- ✅ 100% code coverage for CatalogManager
- ✅ All CLI commands work as documented
- ✅ Backward compatibility verified
- ✅ Performance benchmarks met (<1s for catalog list)

---

## Test Coverage Mapping

### Requirements → Tests

**From BACKLOG-CATALOG-PHASE1-2025-11-17-023825.md**:

| Requirement | Test(s) | File |
|-------------|---------|------|
| CatalogManager with DI | test_init_with_paths | test_catalog_manager.py |
| Lazy loading | test_get_catalog_lazy_loading, test_init_does_not_load_catalogs | test_catalog_manager.py |
| Case-insensitive | test_get_catalog_case_insensitive | test_catalog_manager.py |
| Search ordering | test_search_all_both_catalogs | test_catalog_manager.py |
| No deduplication | test_search_all_same_id_not_deduplicated | test_catalog_manager.py |
| catalog list | TestCatalogListCommand | test_cli_catalog_commands.py |
| catalog info | TestCatalogInfoCommand | test_cli_catalog_commands.py |
| search --catalog | TestSearchWithCatalog | test_cli_catalog_commands.py |
| search --all-catalogs | test_search_all_catalogs | test_cli_catalog_commands.py |
| Backward compat | TestBackwardCompatibility | test_cli_catalog_commands.py + test_multi_catalog_e2e.py |
| Local catalog auto-init | test_fresh_install_creates_local_catalog | test_multi_catalog_e2e.py |
| Persistence | TestLocalCatalogPersistence | test_multi_catalog_e2e.py |
| Deprecation warnings | TestDeprecationWarnings | test_multi_catalog_e2e.py |
| Error handling | TestErrorHandling | test_multi_catalog_e2e.py |

### Spec Clarifications → Tests

**From BACKLOG § Pragmatic Decisions**:

| Decision | Test(s) |
|----------|---------|
| Local init errors → WARN + continue | test_create_default_catalog_manager_init_error, test_permission_error_graceful_degradation |
| Case-insensitive names | test_get_catalog_case_insensitive, test_catalog_info_case_insensitive |
| Search ordering (priority + alpha) | test_search_all_both_catalogs, test_search_all_catalogs_ordering |

---

## Test Data Patterns

### Minimal Test Catalog

```python
create_test_catalog_file(path, {
    "server-id": {
        "description": "Server description",
        "command": "npx",
        "args": ["-y", "package"],
        "categories": ["cat1", "cat2"]
    }
})
```

### Multi-Server Catalog

```python
create_test_catalog_file(path, {
    "filesystem": {
        "description": "File system access",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "categories": ["filesystem", "tools"]
    },
    "github": {
        "description": "GitHub API",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "categories": ["api"]
    }
})
```

### Empty Catalog

```python
create_test_catalog_file(path, {})
```

---

## Fixtures

### Provided Fixtures

```python
@pytest.fixture
def cli_runner():
    """Create Click CLI runner."""
    return CliRunner()

@pytest.fixture
def test_catalogs(tmp_path: Path, monkeypatch):
    """Create test catalogs and configure environment."""
    # Creates official + local catalogs in tmp_path
    # Mocks environment to use test catalogs
    return official_path, local_path

@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch):
    """Create isolated home directory for testing."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    return fake_home
```

### Helper Functions

```python
def create_test_catalog_file(path: Path, servers: Dict[str, Any]) -> None:
    """Create a test catalog JSON file."""
    # Creates parent dirs, writes JSON
```

---

## Implementation Checklist

Use this checklist to track progress:

### Week 1: Core Infrastructure
- [ ] CATALOG-001: Implement CatalogManager class
  - Run: `pytest tests/test_catalog_manager.py::TestCatalogManagerInit -v`
  - Expected: 2 tests pass
- [ ] CATALOG-002: All unit tests pass
  - Run: `pytest tests/test_catalog_manager.py -v`
  - Expected: 23 tests pass
- [ ] CATALOG-003: CLI context integration
  - No specific test, but needed for CLI tests

### Week 2: CLI Commands
- [ ] CATALOG-004: search --catalog flag
  - Run: `pytest tests/test_cli_catalog_commands.py::TestSearchWithCatalog -v`
  - Expected: 8 tests pass
- [ ] CATALOG-005: info/add --catalog flags
  - Run: `pytest tests/test_cli_catalog_commands.py::TestInfoWithCatalog -v`
  - Expected: 4 tests pass
- [ ] CATALOG-006: catalog subcommand
  - Run: `pytest tests/test_cli_catalog_commands.py::TestCatalogListCommand -v`
  - Run: `pytest tests/test_cli_catalog_commands.py::TestCatalogInfoCommand -v`
  - Expected: 7 tests pass
- [ ] CATALOG-007: All CLI tests pass
  - Run: `pytest tests/test_cli_catalog_commands.py -v`
  - Expected: 28 tests pass

### Week 3: Testing & Polish
- [ ] CATALOG-008: E2E tests pass
  - Run: `pytest tests/test_multi_catalog_e2e.py -v`
  - Expected: 21 tests pass
- [ ] CATALOG-009: All existing tests still pass
  - Run: `pytest`
  - Expected: 752+ tests pass (no regressions)
- [ ] CATALOG-010: Documentation complete
  - Verify CLAUDE.md, README.md, CHANGELOG.md updated
- [ ] CATALOG-011: Manual testing complete
  - Final verification before release

---

## Performance Benchmarks

Tests include performance validation:

```python
def test_catalog_commands_fast(cli_runner, isolated_home):
    """Catalog commands execute quickly (< 1 second)."""
    import time
    start = time.time()
    result = cli_runner.invoke(cli, ["catalog", "list"])
    duration = time.time() - start

    assert result.exit_code == 0
    assert duration < 1.0  # Must be fast
```

**Target Performance**:
- `mcpi catalog list` < 100ms
- `mcpi search <query>` < 500ms (no regression from v0.3.0)
- `mcpi search --all-catalogs` < 1000ms

---

## Traceability

### Tests → Backlog Tasks

| Backlog Task | Tests | Count |
|--------------|-------|-------|
| CATALOG-001 | TestCatalogManagerInit, TestCatalogManagerGetCatalog | 9 tests |
| CATALOG-002 | All test_catalog_manager.py | 23 tests |
| CATALOG-003 | CLI integration tests | Indirect |
| CATALOG-004 | TestSearchWithCatalog | 8 tests |
| CATALOG-005 | TestInfoWithCatalog, TestAddWithCatalog | 6 tests |
| CATALOG-006 | TestCatalogListCommand, TestCatalogInfoCommand | 7 tests |
| CATALOG-007 | All test_cli_catalog_commands.py | 28 tests |
| CATALOG-008 | All test_multi_catalog_e2e.py | 21 tests |
| CATALOG-009 | Existing test suite | 752+ tests |
| CATALOG-010 | Manual verification | N/A |
| CATALOG-011 | Manual testing | N/A |

### Tests → STATUS Gaps

| STATUS Gap | Addressed By |
|------------|--------------|
| "Two-catalog MVP needed" | All tests validate two-catalog system |
| "Lazy loading required" | test_get_catalog_lazy_loading |
| "Case-insensitive lookup" | test_get_catalog_case_insensitive |
| "Search ordering unclear" | test_search_all_both_catalogs |
| "Local init errors" | test_create_default_catalog_manager_init_error |
| "Backward compat critical" | TestBackwardCompatibility (both files) |

---

## Notes for Implementation

### Test-Driven Development

Follow this flow:

1. **Pick a test** - Start with `test_init_with_paths`
2. **Run it** - `pytest tests/test_catalog_manager.py::TestCatalogManagerInit::test_init_with_paths -v`
3. **See it fail** - ImportError or AssertionError
4. **Write minimal code** - Just enough to pass
5. **Run it** - Should pass now
6. **Refactor** - Clean up if needed
7. **Next test** - Move to `test_init_does_not_load_catalogs`

### Test Failures Are Your Friend

When a test fails, it tells you exactly what's wrong:

```bash
AssertionError: assert None == '/tmp/pytest.../official/catalog.json'
```

This means: "You didn't set `manager.official_path` correctly"

### Don't Mock What You're Testing

These tests intentionally avoid mocking the code under test:

- ❌ DON'T: Mock `CatalogManager.get_catalog()`
- ✅ DO: Create real catalog files and call `get_catalog()`

- ❌ DON'T: Mock `cli.invoke()`
- ✅ DO: Use `CliRunner` to invoke real CLI

### Coverage Is Not the Goal

100% coverage is required, but it's a **side effect** of good tests, not the goal:

- Write tests that validate behavior
- Coverage follows naturally
- If coverage < 100%, you missed a code path
- If coverage = 100% but bugs exist, tests are wrong

---

## Questions or Issues?

If tests are unclear or seem wrong:

1. **Check the planning docs**:
   - STATUS-CATALOG-PHASE1-EVALUATION-2025-11-17-023400.md
   - BACKLOG-CATALOG-PHASE1-2025-11-17-023825.md
   - PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md

2. **Understand the requirement** - Why does this test exist?

3. **Propose a change** - Tests are contracts, but they can be updated if requirements change

4. **Don't skip failing tests** - If a test fails, either:
   - Fix the implementation (test is correct)
   - Fix the test (test is wrong)
   - Update the requirement (spec changed)

---

## Success Metrics

Phase 1 is complete when:

- ✅ All 72 catalog tests pass
- ✅ All 752+ existing tests still pass (no regressions)
- ✅ Coverage for CatalogManager = 100%
- ✅ Performance benchmarks met
- ✅ Manual testing checklist complete

**Current Status**: 0/72 passing (0%) - Implementation not started
**Target Status**: 72/72 passing (100%) - Ready for v0.4.0 release

---

**Test Suite Status**: READY FOR IMPLEMENTATION
**Next Action**: Begin CATALOG-001 (CatalogManager implementation)
**First Test to Pass**: `test_init_with_paths`

---

*Test suite created by: Functional Testing Architect*
*Date: 2025-11-17*
*Multi-Catalog Phase 1 (v0.4.0)*
*Test-First Development: Write tests, then implement*
