# Environment Variable Support - Functional Test Documentation

## Overview

This document explains the functional test suite for environment variable support in the MCPI registry system. The tests in `test_registry_env_vars.py` validate the complete workflow from registry → model → installation → configuration files.

## Feature Being Tested

**Feature**: Optional `env` field in MCP server registry entries

**Problem**: Some MCP servers require environment variables to function (e.g., `design-patterns` needs `PATTERNS_DIR`, `github` needs `GITHUB_TOKEN`). Without env var support, users must manually edit config files after installation.

**Solution**: Add optional `env` field to registry entries so:
1. Registry documents required env vars for each server
2. Installation process includes env vars in generated config
3. Users can override env var values with their own
4. Claude Code receives env vars when launching servers

## Test Suite Structure

The test suite is organized into 6 test classes, each validating a specific part of the workflow:

### 1. TestRegistryEnvVarLoading
**What it tests**: Loading servers with env vars from catalog.json into Pydantic models

**User workflow**:
- Developer adds server with `env` field to catalog.json
- Catalog loads file and parses JSON
- Pydantic creates MCPServer model with env preserved

**Tests**:
- `test_load_server_with_env_vars_from_catalog` - Loads server with env, validates preservation
- `test_load_server_without_env_vars_backward_compat` - Existing servers without env still work
- `test_load_server_with_empty_env_dict` - Edge case: explicit empty `env: {}`
- `test_load_multiple_servers_mixed_env_presence` - Mixed catalog with various env configurations

**Key assertions**:
- Server loads without errors
- Env dict accessible via `server.env`
- All env keys and values preserved
- Backward compatibility maintained

### 2. TestEnvVarConfigurationGeneration
**What it tests**: Env vars included in generated config via `get_run_command()`

**User workflow**:
- Server model calls `get_run_command()` to generate config
- Output includes env vars from registry
- User config can override env var values

**Tests**:
- `test_get_run_command_includes_env_vars_from_registry` - Env in method output
- `test_get_run_command_merges_user_config_env_vars` - User overrides work
- `test_get_run_command_without_env_backward_compat` - No env = no env in output

**Key assertions**:
- `run_config["env"]` exists and contains registry env vars
- User-provided env vars override registry defaults
- User can add additional env vars not in registry
- Servers without env don't pollute config with empty env

### 3. TestEnvVarEndToEndInstallation
**What it tests**: COMPLETE workflow from registry → installation → file on disk

**User workflow (CRITICAL)**:
1. User runs: `mcpi add design-patterns --scope user-global`
2. MCPI loads server from catalog (with env)
3. MCPI generates config for Claude Code
4. Config written to `~/.claude/settings.json`
5. File contains server with env vars
6. User can edit env var values
7. Claude Code reads file and launches server with env

**Tests**:
- `test_add_server_with_env_vars_to_config_file` - **MOST IMPORTANT TEST**
- `test_add_multiple_servers_with_different_env_configs` - Multiple servers scenario
- `test_add_server_across_different_scopes_with_env` - All scopes work

**Key assertions**:
- Config file exists on disk
- File contains valid JSON
- Server entry has env vars from registry
- Env var keys and values match registry exactly
- File format matches Claude Code schema

**Why this is the most important test**:
- Tests COMPLETE user-visible workflow
- Uses REAL file I/O (no mocks)
- Validates ACTUAL observable outcome (file on disk)
- Cannot be satisfied by stubs or shortcuts

### 4. TestEnvVarSchemaValidation
**What it tests**: Pydantic validation accepts valid env, rejects invalid

**User workflow**:
- Developer adds server to catalog
- Schema validation runs
- Valid configs pass, invalid configs fail

**Tests**:
- `test_pydantic_accepts_valid_env_dict` - Dict env accepted
- `test_pydantic_accepts_missing_env_field` - Optional field (backward compat)
- `test_pydantic_rejects_invalid_env_type` - String/list env rejected
- `test_pydantic_accepts_empty_env_dict` - `{}` accepted

**Key assertions**:
- Valid env dict passes Pydantic validation
- Missing env field doesn't raise error
- Invalid types (string, list) raise ValidationError
- Empty dict is valid

### 5. TestEnvVarCatalogPersistence
**What it tests**: Round-trip catalog save/load preserves env vars

**User workflow**:
- Load catalog with servers (some with env)
- Modify servers
- Save catalog
- Reload catalog
- Verify env vars intact

**Tests**:
- `test_save_and_reload_catalog_with_env_vars` - Full round-trip
- `test_save_catalog_mixed_env_presence` - Mixed catalog persistence

**Key assertions**:
- Saved file contains env vars
- Reloaded catalog has identical env vars
- File format correct (valid JSON)
- Mixed catalogs save correctly

## Gaming Resistance

These tests are designed to be **un-gameable** (impossible to pass with shortcuts or fake implementations):

### 1. Real File Operations
- Uses `tmp_path` fixture for REAL file I/O
- Writes actual JSON files to disk
- Reads back files to validate contents
- Cannot pass with mocked file operations

### 2. Multiple Verification Points
Each test validates multiple aspects:
- File exists on disk (not just in memory)
- File contains valid JSON (parseable)
- Server entry exists in file
- Env vars present with correct values
- Other fields not corrupted

### 3. Cross-Validation
Tests verify consistency across layers:
- Registry file → Pydantic model → Generated config → Disk file
- Cannot fake one layer without breaking another

### 4. Observable Outcomes
Tests assert on what users would see:
- File at expected path
- File contents match expectations
- Commands produce expected results
- Errors are clear and actionable

### 5. Real Object Usage
- Uses actual `ServerCatalog` class (not mocked)
- Uses actual `MCPServer` Pydantic model (not mocked)
- Uses actual `ClaudeCodePlugin` (with path overrides for testing)
- Only test infrastructure (harness, temp paths) is mocked

### 6. Error Path Testing
Tests validate error handling:
- Invalid env types raise errors
- Missing servers raise errors
- Error messages are clear

## Test Execution

### Run all env var tests:
```bash
pytest tests/test_registry_env_vars.py -v
```

### Run specific test class:
```bash
pytest tests/test_registry_env_vars.py::TestEnvVarEndToEndInstallation -v
```

### Run most critical test:
```bash
pytest tests/test_registry_env_vars.py::TestEnvVarEndToEndInstallation::test_add_server_with_env_vars_to_config_file -v
```

### Run with coverage:
```bash
pytest tests/test_registry_env_vars.py --cov=src/mcpi/registry --cov=src/mcpi/clients -v
```

## Expected Test Behavior

### Before Implementation
All tests should **FAIL** with clear errors:
- `AttributeError: 'MCPServer' object has no attribute 'env'` - Model doesn't have env field yet
- `KeyError: 'env'` - get_run_command() doesn't include env
- Config files missing env vars - Installation doesn't preserve env

### After Implementation
All tests should **PASS**:
- 21 tests across 5 test classes
- All tests green
- No warnings about missing fields
- Config files contain env vars correctly

## Traceability

### STATUS Gaps Addressed
(See test file docstring for complete list)

**Key gaps**:
- No env var support in registry
- Cannot configure servers requiring environment variables
- Manual config editing required for env-dependent servers

### PLAN Items Validated
- Add `env` field to MCPServer model
- Update CUE schema to allow optional env field
- Pydantic validation accepts env dict
- `get_run_command()` includes env vars
- Backward compatibility maintained

### Which Tests Validate Which Requirements

| Requirement | Test |
|-------------|------|
| Add env field to MCPServer | `test_load_server_with_env_vars_from_catalog` |
| Pydantic validation | `TestEnvVarSchemaValidation` (all tests) |
| get_run_command() includes env | `test_get_run_command_includes_env_vars_from_registry` |
| User config override | `test_get_run_command_merges_user_config_env_vars` |
| Config file generation | `test_add_server_with_env_vars_to_config_file` |
| Backward compatibility | `test_load_server_without_env_vars_backward_compat` |
| CUE schema update | Manual verification (CUE validation in catalog.py) |
| Round-trip persistence | `test_save_and_reload_catalog_with_env_vars` |

## Integration with Existing Tests

### Test Harness Integration
Tests use the existing `MCPTestHarness` from `test_harness.py`:
- `mcp_harness` fixture for file operations
- `path_overrides` for safe test file paths
- Helper methods: `assert_valid_json()`, `get_server_config()`, etc.

### Fixture Usage
```python
def test_example(mcp_harness):
    # Plugin with test paths (doesn't touch real files)
    plugin = ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)

    # Add server
    result = plugin.add_server("test", config, "user-global")

    # Verify in file
    mcp_harness.assert_server_exists("user-global", "test")
    config = mcp_harness.get_server_config("user-global", "test")
    assert config["env"] == expected_env
```

### Separation from Unit Tests
These are **functional tests** (not unit tests):
- Test complete workflows, not isolated functions
- Use real file I/O, not mocks
- Validate observable outcomes, not internal state
- Focus on user experience, not implementation details

## Success Criteria

The test suite passes when:

1. **All tests pass** (21/21 green)
2. **No implementation details leaked** (tests remain valid after refactoring)
3. **Clear failure messages** (developers know what broke)
4. **Fast execution** (< 5 seconds total)
5. **No flaky tests** (deterministic, no race conditions)
6. **Coverage complete** (all env var workflows tested)

## Maintenance

### When to Update Tests

**Add tests when**:
- New env var features added (e.g., env var validation, templating)
- New scopes added that handle env differently
- Bug discovered in env var handling

**Don't update tests when**:
- Implementation details change (refactoring)
- Internal method names change
- Code organization changes

**Red flags** (tests might be too brittle):
- Tests break on every refactor
- Tests mock internal methods
- Tests assert on private attributes
- Tests depend on execution order

### Test Quality Checklist

Before committing new env var tests:
- [ ] Tests use real file I/O (via tmp_path)
- [ ] Tests validate observable outcomes (files on disk)
- [ ] Tests check multiple side effects (exists, valid, correct content)
- [ ] Tests cannot pass with stubs or mocks
- [ ] Error paths tested with real exceptions
- [ ] Backward compatibility validated
- [ ] Tests are deterministic (no randomness)
- [ ] Tests are isolated (no shared state)
- [ ] Clear assertions with error messages
- [ ] Docstrings explain user workflow

## Future Enhancements

Potential future test additions:

1. **Env var templating**: `env: {"KEY": "${HOME}/path"}`
2. **Env var validation**: Required vs optional env vars
3. **Env var secrets**: Redaction in logs, secure storage
4. **Env var inheritance**: Scope-based env var defaults
5. **CLI integration**: `mcpi add server --env KEY=value`
6. **Error reporting**: Clear messages when env vars missing

Each enhancement should add functional tests following the same principles:
- Real file I/O
- Observable outcomes
- Un-gameable
- User workflow focused
