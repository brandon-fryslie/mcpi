# Catalog Rename - Test Design Summary

## Overview

Designed comprehensive functional tests for the registry→catalog rename refactoring. Tests are **un-gameable** and validate that the rename is complete, correct, and preserves all functionality.

## Test File

**Location:** `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/tests/test_catalog_rename.py`

**Documentation:** `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/tests/CATALOG_RENAME_TEST_STRATEGY.md`

## Test Coverage

### 18 Tests Across 7 Categories

1. **File Existence** (3 tests)
   - Verify catalog.json exists
   - Verify catalog.cue exists
   - Verify old registry files are gone

2. **API Rename** (3 tests)
   - catalog_path parameter works, registry_path fails
   - load_catalog() exists and works, load_registry() removed
   - save_catalog() exists and works, save_registry() removed

3. **Factory Functions** (2 tests)
   - create_default_catalog() uses catalog.json
   - create_test_catalog() accepts catalog_path parameter

4. **Backward Compatibility** (2 tests)
   - ClientRegistry class unchanged
   - ClientRegistry functionality preserved

5. **CLI Integration** (2 tests)
   - Search command uses catalog
   - List command uses catalog

6. **Validation** (2 tests)
   - CUE validation works with catalog.cue
   - Saving validates against catalog.cue

7. **Regression Testing** (4 tests)
   - Add server still works
   - Remove server still works
   - Search still works
   - List categories still works

## Current Status

### Test Execution Results

```
18 tests total
16 FAILED (expected - rename not yet implemented)
2 PASSED (ClientRegistry tests - should remain unchanged)
```

### Expected Failures (Before Implementation)

All tests correctly fail with clear error messages:
- ✅ "catalog.json not found" - file doesn't exist yet
- ✅ "catalog_path unexpected keyword argument" - parameter not renamed yet
- ✅ "no attribute 'catalog_path'" - attribute not renamed yet
- ✅ "no attribute 'load_catalog'" - method not renamed yet
- ✅ "old registry.json still exists" - files not renamed yet

### Passing Tests (Backward Compatibility)

- ✅ `test_client_registry_class_exists` - ClientRegistry should NOT be renamed
- ✅ `test_client_registry_functionality` - ClientRegistry works correctly

## Gaming Resistance Features

### Why These Tests Cannot Be Gamed

1. **Real File Operations**
   - Tests verify actual files exist on filesystem
   - Tests parse and validate file contents
   - Cannot be satisfied by mock files or stubs

2. **State Verification**
   - Tests perform operations and verify state changes
   - Tests use save/load round-trips to verify persistence
   - Cannot be faked by in-memory stubs

3. **Method Existence Checks**
   - Tests verify old methods are REMOVED
   - Tests verify new methods EXIST and WORK
   - Cannot be satisfied by keeping both old and new APIs

4. **Negative Testing**
   - Tests verify old files DON'T exist
   - Tests verify old parameters DON'T work
   - Forces complete migration, not partial fixes

5. **End-to-End Workflows**
   - Tests exercise complete user workflows (CLI, search, etc.)
   - Tests verify integration between components
   - Cannot be satisfied by isolated unit tests with mocks

6. **Content Validation**
   - Tests verify data structure and integrity
   - Tests check that operations actually modify data
   - Cannot be faked by returning hardcoded success values

## Implementation Checklist

When implementing the rename, follow this checklist:

### Phase 1: File Rename
- [ ] `mv data/registry.json data/catalog.json`
- [ ] `mv data/registry.cue data/catalog.cue`
- [ ] Run: `pytest tests/test_catalog_rename.py::TestCatalogFileRename -v`
- [ ] Expected: 3 tests pass

### Phase 2: Parameter Rename
- [ ] Update `ServerCatalog.__init__`: `registry_path` → `catalog_path`
- [ ] Update `self.registry_path` → `self.catalog_path` throughout class
- [ ] Run: `pytest tests/test_catalog_rename.py::TestServerCatalogAPIRename::test_catalog_path_parameter -v`
- [ ] Expected: 1 test passes

### Phase 3: Method Rename
- [ ] Rename `load_registry()` → `load_catalog()`
- [ ] Rename `save_registry()` → `save_catalog()`
- [ ] Rename internal methods: `_load_json_registry()`, etc. → `_*_catalog()`
- [ ] Run: `pytest tests/test_catalog_rename.py::TestServerCatalogAPIRename -v`
- [ ] Expected: 3 tests pass

### Phase 4: Factory Function Update
- [ ] Update `create_default_catalog()` to reference `catalog.json`
- [ ] Run: `pytest tests/test_catalog_rename.py::TestFactoryFunctionRename -v`
- [ ] Expected: 2 tests pass

### Phase 5: CLI Integration
- [ ] Verify CLI already uses `get_catalog()` correctly
- [ ] Run: `pytest tests/test_catalog_rename.py::TestCLIIntegration -v`
- [ ] Expected: 2 tests pass

### Phase 6: Full Validation
- [ ] Run: `pytest tests/test_catalog_rename.py -v`
- [ ] Expected: 18/18 tests pass
- [ ] Run: `pytest tests/ -v`
- [ ] Expected: No regressions in existing tests

### Phase 7: Documentation
- [ ] Update comments/docstrings to use "catalog" terminology
- [ ] Update error messages
- [ ] Update README if it references registry files
- [ ] Update CLAUDE.md if needed

## Files Requiring Updates

### Core Implementation
1. **`src/mcpi/registry/catalog.py`** - Primary changes
   - Parameter rename
   - Method rename
   - Attribute rename
   - Factory function update

### Data Files
2. **`data/registry.json`** → **`data/catalog.json`**
3. **`data/registry.cue`** → **`data/catalog.cue`**

### Existing Tests (Update Paths)
4. **`tests/test_registry_integration.py`**
   - Update `REGISTRY_PATH` constant
   - Update `CUE_SCHEMA_PATH` constant

### Documentation (Optional)
5. **`README.md`** - If it mentions registry files
6. **`CLAUDE.md`** - Update validation commands if needed
7. **`.agent_planning/REGISTRY_VALIDATION_TESTING.md`** - Rename or update references

## Success Criteria

The rename is complete when:

1. ✅ All 18 tests in `test_catalog_rename.py` pass
2. ✅ All existing tests still pass (no regressions)
3. ✅ CLI commands work (`mcpi search`, `mcpi list`, etc.)
4. ✅ CUE validation works with new schema file
5. ✅ No references to "registry" remain except:
   - `ClientRegistry` class (different concept)
   - `mcpi.registry` module name (acceptable)
   - Test file names (acceptable)

## Test Execution

### Run All Tests
```bash
pytest tests/test_catalog_rename.py -v
```

### Run Specific Category
```bash
pytest tests/test_catalog_rename.py::TestCatalogFileRename -v
pytest tests/test_catalog_rename.py::TestServerCatalogAPIRename -v
```

### Run With Coverage
```bash
pytest tests/test_catalog_rename.py --cov=src/mcpi/registry --cov-report=term
```

### Run Direct (Standalone)
```bash
python tests/test_catalog_rename.py
```

## Traceability

### User Request
- **Requirement**: Rename "registry" to "catalog" as more fitting terminology
- **Scope**: Server catalog files and APIs (not ClientRegistry)
- **Goal**: Improve code clarity and terminology consistency

### Test Validation
- **STATUS Gaps**: None (this is refactoring/improvement)
- **PLAN Items**: Terminology consistency
- **Acceptance Criteria**: All catalog operations work with new naming

## Output Summary JSON

```json
{
  "tests_added": [
    "test_catalog_json_exists",
    "test_catalog_cue_schema_exists",
    "test_old_registry_files_do_not_exist",
    "test_catalog_path_parameter",
    "test_load_catalog_method_exists",
    "test_save_catalog_method_exists",
    "test_create_default_catalog_uses_catalog_path",
    "test_create_test_catalog_uses_catalog_path_param",
    "test_client_registry_class_exists",
    "test_client_registry_functionality",
    "test_search_command_uses_catalog",
    "test_list_command_uses_catalog",
    "test_catalog_loads_with_cue_validation",
    "test_catalog_saves_with_cue_validation",
    "test_add_server_still_works",
    "test_remove_server_still_works",
    "test_search_servers_still_works",
    "test_list_categories_still_works"
  ],
  "workflows_covered": [
    "File rename validation (registry→catalog)",
    "API parameter rename (registry_path→catalog_path)",
    "Method rename (load_registry→load_catalog)",
    "Factory function path updates",
    "ClientRegistry backward compatibility",
    "CLI integration with renamed catalog",
    "CUE validation with renamed schema",
    "Core catalog operations (add/remove/search/list)"
  ],
  "initial_status": "failing",
  "commit": "pending",
  "gaming_resistance": "high",
  "status_gaps_addressed": [],
  "plan_items_validated": [
    "Terminology consistency improvement",
    "Server catalog management"
  ],
  "test_categories": {
    "file_existence": 3,
    "api_rename": 3,
    "factory_functions": 2,
    "backward_compatibility": 2,
    "cli_integration": 2,
    "validation": 2,
    "regression": 4
  },
  "expected_failures_before_rename": 16,
  "expected_passes_after_rename": 18
}
```

## Next Steps

1. **Review test design** - Confirm test strategy is appropriate
2. **Implement rename** - Follow checklist in phases
3. **Validate incrementally** - Run tests after each phase
4. **Update existing tests** - Fix path references in `test_registry_integration.py`
5. **Run full test suite** - Ensure no regressions
6. **Update documentation** - Reflect new terminology
7. **Commit changes** - With descriptive commit message

## Notes

- Tests designed for **maximum gaming resistance**
- All tests verify **real functionality**, not mocks
- Tests use **multiple verification points** per scenario
- Tests include **negative validation** (old names fail)
- Tests validate **end-to-end workflows**
- Tests are **runnable independently**
- Tests provide **clear failure messages**
