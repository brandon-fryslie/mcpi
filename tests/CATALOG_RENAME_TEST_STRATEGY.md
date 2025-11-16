# Catalog Rename Test Strategy

## Overview

This document describes the functional test strategy for validating the registry→catalog rename throughout the MCPI codebase. The tests in `test_catalog_rename.py` are designed to be **un-gameable** - they verify real functionality and cannot be satisfied by stubs, mocks, or shortcuts.

## Rename Scope

### What Gets Renamed

**File/Directory Names:**
- `data/registry.json` → `data/catalog.json`
- `data/registry.cue` → `data/catalog.cue`

**Code Elements in `src/mcpi/registry/catalog.py`:**
- `ServerCatalog.__init__(registry_path=...)` → `ServerCatalog.__init__(catalog_path=...)`
- `ServerCatalog.registry_path` attribute → `ServerCatalog.catalog_path`
- `ServerCatalog._registry` internal attribute → `ServerCatalog._catalog`
- `load_registry()` method → `load_catalog()`
- `save_registry()` method → `save_catalog()`
- `_load_json_registry()` → `_load_json_catalog()`
- `_load_yaml_registry()` → `_load_yaml_catalog()`
- `_save_json_registry()` → `_save_json_catalog()`
- `_save_yaml_registry()` → `_save_yaml_catalog()`
- Factory function: References to `registry.json` → `catalog.json`

**Code Elements in Other Files:**
- CLI: `get_catalog()` function (already correct)
- Comments/docstrings: "registry" → "catalog" where referring to server data
- Error messages: "registry" → "catalog" where appropriate

### What Stays Unchanged

**KEEP AS-IS:**
- `ClientRegistry` class in `src/mcpi/clients/registry.py` (different concept - manages MCP clients, not servers)
- `mcpi.registry` module name (standard terminology for this type of module)
- `ServerRegistry` Pydantic model name (internal implementation detail, could be renamed but not required)
- Test file names in `tests/test_registry_*.py` (these test the registry module, name is still appropriate)

## Test Categories

### 1. File Existence Tests (`TestCatalogFileRename`)

**Purpose:** Verify renamed files exist and old files don't

**Gaming Resistance:**
- Tests actual filesystem operations
- Validates file content is parseable JSON/CUE
- Checks data structure matches expected schema
- Cannot be faked - files must actually exist with correct names

**Tests:**
- `test_catalog_json_exists()` - Verifies `data/catalog.json` exists and contains valid JSON
- `test_catalog_cue_schema_exists()` - Verifies `data/catalog.cue` exists with valid CUE content
- `test_old_registry_files_do_not_exist()` - Ensures `registry.json` and `registry.cue` are gone

### 2. API Rename Tests (`TestServerCatalogAPIRename`)

**Purpose:** Verify ServerCatalog class uses new naming

**Gaming Resistance:**
- Tests real method calls that modify state
- Verifies data actually loads from files
- Checks persistence (save/load round-trip)
- Validates old method names are removed
- Cannot be satisfied by stubs - requires real implementations

**Tests:**
- `test_catalog_path_parameter()` - Verifies `__init__(catalog_path=...)` works, old `registry_path` raises TypeError
- `test_load_catalog_method_exists()` - Verifies `load_catalog()` exists, works, and old `load_registry()` is removed
- `test_save_catalog_method_exists()` - Verifies `save_catalog()` exists, persists data, and old `save_registry()` is removed

### 3. Factory Function Tests (`TestFactoryFunctionRename`)

**Purpose:** Verify factory functions use catalog terminology

**Gaming Resistance:**
- Tests actual path resolution
- Verifies returned instances can load real data
- Validates path names match expected catalog naming
- Cannot be faked - must return working instances

**Tests:**
- `test_create_default_catalog_uses_catalog_path()` - Verifies factory references `catalog.json` not `registry.json`
- `test_create_test_catalog_uses_catalog_path_param()` - Verifies test factory accepts and uses path correctly

### 4. Backward Compatibility Tests (`TestClientRegistryUnchanged`)

**Purpose:** Ensure ClientRegistry is NOT renamed (different concept)

**Gaming Resistance:**
- Tests real ClientRegistry class functionality
- Verifies client plugin discovery works
- Validates core client management features
- Cannot be satisfied by mocks - requires real plugin system

**Tests:**
- `test_client_registry_class_exists()` - Verifies ClientRegistry class still exists with correct name
- `test_client_registry_functionality()` - Verifies ClientRegistry discovers and manages clients correctly

### 5. CLI Integration Tests (`TestCLIIntegration`)

**Purpose:** Verify CLI commands work with renamed catalog

**Gaming Resistance:**
- Uses actual CLI context and catalog loading
- Verifies real data loading from catalog.json
- Tests end-to-end user workflows
- Cannot be faked - requires functional CLI integration

**Tests:**
- `test_search_command_uses_catalog()` - Verifies search loads from `catalog.json`
- `test_list_command_uses_catalog()` - Verifies list command uses catalog

### 6. Validation Tests (`TestCatalogValidation`)

**Purpose:** Ensure CUE validation works with renamed schema

**Gaming Resistance:**
- Tests real CUE validation if available
- Verifies schema file integration
- Validates data against renamed schema file
- Cannot be satisfied by stubs - requires real validation

**Tests:**
- `test_catalog_loads_with_cue_validation()` - Verifies loading with CUE validation enabled
- `test_catalog_saves_with_cue_validation()` - Verifies saving validates against `catalog.cue`

### 7. Regression Tests (`TestNoRegressions`)

**Purpose:** Ensure core functionality still works after rename

**Gaming Resistance:**
- Tests real CRUD operations (add/remove/update/search)
- Verifies state changes persist
- Validates data integrity across operations
- Cannot be gamed - requires actual data manipulation

**Tests:**
- `test_add_server_still_works()` - Verifies server addition and retrieval
- `test_remove_server_still_works()` - Verifies server removal
- `test_search_servers_still_works()` - Verifies search functionality
- `test_list_categories_still_works()` - Verifies category listing

## Running the Tests

### Run all catalog rename tests:
```bash
pytest tests/test_catalog_rename.py -v
```

### Run specific test class:
```bash
pytest tests/test_catalog_rename.py::TestCatalogFileRename -v
pytest tests/test_catalog_rename.py::TestServerCatalogAPIRename -v
```

### Run specific test:
```bash
pytest tests/test_catalog_rename.py::TestCatalogFileRename::test_catalog_json_exists -v
```

### Run with coverage:
```bash
pytest tests/test_catalog_rename.py --cov=src/mcpi/registry --cov-report=term
```

## Expected Results

### Before Rename (Tests SHOULD FAIL)

All tests should fail with clear error messages:
- File existence tests: "catalog.json not found"
- API tests: "ServerCatalog has no attribute 'catalog_path'"
- Method tests: "ServerCatalog has no attribute 'load_catalog'"
- Factory tests: "Expected catalog.json, got registry.json"

### After Rename (Tests SHOULD PASS)

All tests should pass, confirming:
- ✅ Catalog files exist with correct names
- ✅ Old registry files are gone
- ✅ ServerCatalog uses catalog_path parameter
- ✅ load_catalog() and save_catalog() methods work
- ✅ Old method names are removed
- ✅ Factory functions reference catalog.json
- ✅ ClientRegistry remains unchanged
- ✅ CLI integration works
- ✅ CUE validation works with catalog.cue
- ✅ All core functionality preserved

## Integration with Existing Tests

### Update Required in Existing Tests

The following existing test files will need updates:

1. **`tests/test_registry_integration.py`**
   - Update `REGISTRY_PATH` to point to `catalog.json`
   - Update `CUE_SCHEMA_PATH` to point to `catalog.cue`
   - No code changes needed (uses same data, just different filename)

2. **`tests/test_registry_dependency_injection.py`**
   - Update factory function calls to use `catalog_path` parameter
   - No structural changes needed

3. **Any test using `create_default_catalog()` or `create_test_catalog()`**
   - Should work without changes (factory functions handle paths internally)

### Tests That Don't Need Updates

- `test_cli_*.py` - Already use factory functions
- `test_installer_*.py` - Don't directly interact with catalog files
- `test_clients_*.py` - Use ClientRegistry (unchanged)
- `test_manager_*.py` - Use factory functions

## Why These Tests Are Un-Gameable

### 1. Real File Operations
Tests verify actual files exist on the filesystem at expected paths. Cannot be faked by returning hardcoded values.

### 2. Content Validation
Tests load and parse file contents, verifying structure and data integrity. Cannot be satisfied by empty files or stubs.

### 3. State Verification
Tests perform operations (add/remove/update) and verify state changes persist. Cannot be gamed by returning success without actually performing operations.

### 4. Method Existence Checks
Tests verify old methods are removed and new methods exist. Cannot be satisfied by keeping both old and new methods.

### 5. Round-Trip Validation
Tests save data and reload it, verifying persistence. Cannot be faked by in-memory stubs.

### 6. Negative Testing
Tests verify old files DON'T exist and old methods DON'T work. Forces complete migration.

### 7. End-to-End Workflows
Tests exercise complete user workflows (CLI commands, search, etc.). Cannot be satisfied by partial implementations.

## Implementation Checklist

When implementing the rename, use these tests as validation:

- [ ] Rename `data/registry.json` → `data/catalog.json`
- [ ] Rename `data/registry.cue` → `data/catalog.cue`
- [ ] Update `ServerCatalog.__init__` parameter: `registry_path` → `catalog_path`
- [ ] Update `ServerCatalog.registry_path` attribute → `catalog_path`
- [ ] Rename `load_registry()` → `load_catalog()`
- [ ] Rename `save_registry()` → `save_catalog()`
- [ ] Rename internal methods: `_load_json_registry()` → `_load_json_catalog()` (etc.)
- [ ] Update `create_default_catalog()` to reference `catalog.json`
- [ ] Update comments/docstrings to use "catalog" terminology
- [ ] Update error messages to use "catalog" terminology
- [ ] Run `pytest tests/test_catalog_rename.py -v` - all tests should pass
- [ ] Run full test suite to ensure no regressions
- [ ] Update `tests/test_registry_integration.py` paths
- [ ] Verify `ClientRegistry` remains unchanged

## Success Criteria

The rename is complete and correct when:

1. ✅ All tests in `test_catalog_rename.py` pass
2. ✅ All existing tests still pass (no regressions)
3. ✅ `pytest tests/ -v` shows 100% pass rate for catalog-related tests
4. ✅ CLI commands (`mcpi search`, `mcpi list`, etc.) work correctly
5. ✅ Documentation is updated to use "catalog" terminology
6. ✅ No references to "registry" remain except:
   - `ClientRegistry` class (different concept)
   - `mcpi.registry` module name (acceptable)
   - `ServerRegistry` Pydantic model (internal detail)
   - Test file names (acceptable)

## Traceability

These tests validate the following requirements:

- **User Request**: Rename "registry" to "catalog" as it's more fitting terminology
- **STATUS Gaps**: None (this is a refactoring/improvement, not a gap fix)
- **PLAN Items**: Terminology consistency improvement
- **Core Functionality**: Ensure server catalog management continues to work correctly after rename
