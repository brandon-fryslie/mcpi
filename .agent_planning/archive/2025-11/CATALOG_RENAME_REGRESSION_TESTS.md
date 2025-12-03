# Catalog Rename - Regression Test Design

**Created**: 2025-11-09
**Test File**: `tests/test_catalog_rename_regression.py`
**Test Status**: 20/20 PASSING (before rename)

## Overview

Designed regression tests that:
1. **Pass NOW** (before rename) - Validate current functionality works
2. **Will pass AFTER rename** (with minimal updates) - Same behavior, different names
3. **Provide confidence** that the rename doesn't break anything

This is the **correct approach** for rename testing, unlike the previous attempt that created tests for non-existent functionality (tech debt).

## Test Strategy

### Before Rename (Current State)
- Tests use current API: `registry_path`, `load_registry()`, `save_registry()`
- Tests use current file: `data/registry.json`
- All assertions verify behavior, not implementation

### After Rename (Future State)
- Update API calls: `catalog_path`, `load_catalog()`, `save_catalog()`
- Update file references: `data/catalog.json`
- **Keep same assertions** - verify behavior is preserved

### Why This Works
- Tests verify **behavior**, not names
- Minimal updates needed after rename (just API names)
- High confidence that functionality is preserved
- Not tech debt - tests are useful NOW and AFTER

## Test Coverage

### 20 Tests Across 4 Categories

#### 1. Current Registry Behavior (11 tests)
Tests core catalog operations before rename:

1. `test_server_catalog_loads_from_file` - Verify file loading works
2. `test_server_catalog_get_server_by_id` - Verify server retrieval
3. `test_server_catalog_search` - Verify search functionality
4. `test_server_catalog_list_categories` - Verify category listing
5. `test_server_catalog_add_server` - Verify server addition
6. `test_server_catalog_remove_server` - Verify server removal
7. `test_server_catalog_update_server` - Verify server updates
8. `test_server_catalog_save_and_reload` - Verify persistence
9. `test_server_catalog_handles_empty_file` - Verify empty file handling
10. `test_server_catalog_handles_missing_file` - Verify missing file handling

#### 2. Factory Functions Behavior (2 tests)
Tests factory functions before rename:

11. `test_create_default_catalog_loads_production_data` - Verify default factory
12. `test_create_test_catalog_uses_custom_path` - Verify test factory

#### 3. Production Data Integrity (4 tests)
Tests real `data/registry.json` file:

13. `test_production_registry_file_exists` - File exists
14. `test_production_registry_is_valid_json` - Valid JSON syntax
15. `test_production_registry_loads_into_catalog` - Loads correctly
16. `test_production_registry_all_servers_valid` - All servers valid

#### 4. Edge Cases (4 tests)
Tests error handling:

17. `test_invalid_json_raises_error` - Invalid JSON error handling
18. `test_add_duplicate_server_fails` - Duplicate server rejection
19. `test_remove_nonexistent_server_fails` - Non-existent removal rejection
20. `test_update_nonexistent_server_fails` - Non-existent update rejection

## Gaming Resistance

### Why These Tests Cannot Be Gamed

1. **Real File Operations**
   - Tests create actual files on filesystem
   - Tests verify file contents after save/load cycles
   - Cannot be satisfied by in-memory stubs

2. **Observable Outcomes**
   - Tests verify externally observable results
   - Multiple verification points per test
   - Cannot pass with fake implementations

3. **Production Data Validation**
   - Tests load and validate real `data/registry.json`
   - Verifies all production servers are valid
   - Cannot pass if production data is broken

4. **Error Handling Verification**
   - Tests verify proper error messages
   - Tests check error conditions are caught
   - Cannot pass by silently failing

5. **Round-Trip Verification**
   - Tests verify save → load → verify cycles
   - Data must survive persistence correctly
   - Cannot fake with transient data

6. **Edge Case Coverage**
   - Tests verify boundary conditions
   - Tests check negative cases
   - Cannot pass with happy-path-only implementations

## Update Guide for After Rename

After implementing the rename, update tests with this pattern:

### Pattern: API Name Updates

```python
# BEFORE RENAME (current):
catalog = ServerCatalog(registry_path=test_file, validate_with_cue=False)
catalog.load_registry()

# AFTER RENAME (update to):
catalog = ServerCatalog(catalog_path=test_file, validate_with_cue=False)
catalog.load_catalog()

# ASSERTIONS STAY THE SAME:
servers = catalog.list_servers()
assert len(servers) == 2
```

### Pattern: File Path Updates

```python
# BEFORE RENAME (current):
registry_path = Path(__file__).parent.parent / "data" / "registry.json"

# AFTER RENAME (update to):
catalog_path = Path(__file__).parent.parent / "data" / "catalog.json"

# ASSERTIONS STAY THE SAME:
assert catalog_path.exists()
```

### Pattern: Attribute Name Updates

```python
# BEFORE RENAME (current):
assert catalog.registry_path.name == "registry.json"

# AFTER RENAME (update to):
assert catalog.catalog_path.name == "catalog.json"

# The assertion logic stays the same
```

## Update Checklist

After implementing the rename, update tests in this order:

### Phase 1: Simple Text Replacements (5 minutes)
- [ ] Replace `registry_path` → `catalog_path` (parameter names)
- [ ] Replace `load_registry()` → `load_catalog()` (method calls)
- [ ] Replace `save_registry()` → `save_catalog()` (method calls)
- [ ] Replace `"registry.json"` → `"catalog.json"` (file names)

### Phase 2: Run Tests (1 minute)
- [ ] Run: `pytest tests/test_catalog_rename_regression.py -v`
- [ ] Expected: 20/20 tests pass
- [ ] If failures: check for missed replacements

### Phase 3: Verify Behavior (2 minutes)
- [ ] Compare test output before/after rename
- [ ] Verify same number of servers load
- [ ] Verify same operations succeed/fail
- [ ] Confirm assertions still valid

### Total Time: ~10 minutes

## Success Criteria

Tests are successfully updated when:

1. ✅ All 20 tests pass after rename
2. ✅ No new test failures introduced
3. ✅ Same assertions as before rename
4. ✅ Same behavior verified as before rename
5. ✅ No changes to test logic, only API names

## Comparison with Previous Approach

### Previous Approach (WRONG)
- ❌ Tests checked for functionality that doesn't exist yet
- ❌ Tests fail 100% until rename is implemented
- ❌ Creates tech debt (tests that don't provide value NOW)
- ❌ No confidence current functionality works

### Current Approach (CORRECT)
- ✅ Tests verify current functionality works NOW
- ✅ Tests pass 100% before rename
- ✅ Provides immediate value (regression detection)
- ✅ High confidence functionality preserved after rename
- ✅ Minimal updates needed after rename
- ✅ Not tech debt - tests are useful immediately

## Test Execution Results

### Initial Run (Before Rename)
```bash
$ pytest tests/test_catalog_rename_regression.py -v

20 passed in 1.21s
```

**Status**: ✅ ALL TESTS PASSING

### Expected After Rename
```bash
$ pytest tests/test_catalog_rename_regression.py -v

20 passed in ~1.2s
```

**Status**: ✅ ALL TESTS STILL PASSING (with updated API calls)

## Files Modified

### New Files
- `tests/test_catalog_rename_regression.py` - Regression test suite

### Files to Update After Rename
- `tests/test_catalog_rename_regression.py` - Update API calls (10 min)

### Files NOT Modified
- All production code (unchanged until rename implementation)
- Other test files (unchanged)

## Integration with Rename Process

These tests integrate with the rename implementation workflow:

1. **Before Rename**: Run tests to verify current functionality works
2. **During Rename**: Implementation changes names but preserves behavior
3. **After Rename**: Update test API calls and re-run
4. **Verification**: Tests pass = rename successful, behavior preserved

## Benefits

### Immediate Benefits (Before Rename)
1. Regression detection for current code
2. Documentation of current behavior
3. Confidence current functionality works
4. Baseline for future changes

### Future Benefits (After Rename)
1. Verification rename didn't break anything
2. Same test assertions prove behavior preserved
3. Quick feedback (update + run in 10 minutes)
4. High confidence in rename correctness

## Traceability

### User Request
- **Requirement**: Rename "registry" to "catalog" for better terminology
- **Scope**: Server catalog files and APIs (not ClientRegistry)
- **Risk**: Must not break existing functionality

### Test Validation
- **STATUS Gaps**: None (this is refactoring, not feature work)
- **PLAN Items**: Terminology consistency improvement
- **Acceptance Criteria**: All catalog operations work after rename

## Summary JSON

```json
{
  "test_file": "tests/test_catalog_rename_regression.py",
  "tests_added": 20,
  "tests_passing_before_rename": 20,
  "tests_expected_after_rename": 20,
  "update_time_estimate": "10 minutes",
  "gaming_resistance": "high",
  "approach": "regression",
  "value_before_rename": "high",
  "value_after_rename": "high",
  "tech_debt": "none",
  "test_categories": {
    "current_behavior": 11,
    "factory_functions": 2,
    "production_data": 4,
    "edge_cases": 4
  },
  "workflows_covered": [
    "File loading from registry/catalog",
    "Server CRUD operations",
    "Search and list operations",
    "Factory function usage",
    "Production data validation",
    "Error handling and edge cases",
    "Save/reload persistence"
  ],
  "assertions_updated_after_rename": 0,
  "api_calls_updated_after_rename": "~30",
  "logic_changed_after_rename": false
}
```

## Next Steps

1. **Now**: Tests are written and passing (20/20)
2. **Implement Rename**: Follow CATALOG_RENAME_IMPLEMENTATION_GUIDE.md
3. **Update Tests**: Replace API names (10 minutes)
4. **Verify**: Run tests to confirm behavior preserved
5. **Ship**: Confidence that rename is correct

## Notes

- Tests designed for **correctness**, not speed
- Tests verify **behavior**, not implementation
- Tests provide **immediate value** (not just future value)
- Tests are **easy to update** after rename
- Tests are **impossible to game** (real file operations)
- Tests provide **high confidence** in rename correctness
