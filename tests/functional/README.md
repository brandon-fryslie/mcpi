# MCPI Functional Test Suite

## Overview

This test suite contains **un-gameable functional tests** that validate real user workflows in MCPI. These tests are designed to be immune to shortcuts, stubs, and gaming attempts by AI agents or developers.

## Test Philosophy

### What Makes These Tests Un-Gameable

1. **Real Interface Testing**: Tests execute through actual CLI commands and public APIs that users interact with
2. **Multiple Verification Points**: Each test validates multiple observable outcomes, not just pass/fail
3. **State Persistence**: Tests verify that changes persist to the filesystem and configuration
4. **Error Path Validation**: Tests ensure proper error handling without allowing bypasses
5. **Integration Validation**: Tests exercise complete workflows from input to observable output

### Gaming Resistance Features

- **No Core Functionality Mocking**: Tests do not mock the primary functionality being validated
- **Real File Operations**: Tests create and verify actual files, directories, and configurations
- **Observable Outcomes**: Tests verify externally observable results that users would see
- **Side Effect Validation**: Tests confirm all expected side effects occur (logs, configs, state changes)
- **Architecture Validation**: Tests confirm the actual implementation architecture works

## Test Coverage Mapping

### STATUS Report Gap → Test Validation

| STATUS Gap | Test Coverage | Validation Method |
|------------|---------------|-------------------|
| CLI 0% coverage (447/447 lines missed) | `test_cli_to_mcp_manager_integration` | Real CLI command execution |
| Registry Manager 0% coverage (249/249 lines missed) | `test_registry_manager_functionality` | Direct class instantiation + file ops |
| ALL installer modules 0% coverage (827/827 lines missed) | `test_installation_method_validation` | Installer class validation |
| Configuration Management 11-19% coverage | `test_configuration_profile_management` | Real profile creation + persistence |
| CLI architectural mismatch (ClaudeCodeInstaller vs MCPManager) | `test_mcp_manager_architecture_validation` | Direct architecture validation |

### PLAN Priority → Test Implementation

| PLAN Item | Priority | Test Implementation | Acceptance Criteria Validated |
|-----------|----------|---------------------|-------------------------------|
| P0-1: Fix CLI test architecture | Critical | `test_mcp_manager_architecture_validation` | MCPManager integration works |
| P0-2: Installation workflow testing | Critical | `test_installation_method_validation` | All installer types instantiate |
| P0-3: Registry management validation | Critical | `test_registry_manager_functionality` | Registry loading and search work |
| P1-1: Configuration management testing | High | `test_configuration_profile_management` | Profile switching persists |
| P2-2: Error handling validation | Medium | `test_cli_error_handling` | Graceful error handling |

## Test Structure

### Core User Workflows (`test_end_to_end_workflows.py`)

**Class: `TestCoreUserWorkflows`**
- Tests the complete user journey through discovery, selection, and management
- Validates MCPManager-based architecture (not ClaudeCodeInstaller)
- Confirms CLI integration works correctly
- Tests registry functionality with real data

**Class: `TestInstallationWorkflows`**
- Validates all installer types can be instantiated and configured
- Tests installation method detection and validation
- Confirms installer prerequisites are properly checked

**Class: `TestErrorHandlingAndRecovery`**
- Tests error scenarios that users might encounter
- Validates graceful degradation and helpful error messages
- Confirms system recovery from corrupted configurations

## Running Tests

### Prerequisites
```bash
# Install development dependencies
uv sync --dev
source .venv/bin/activate
```

### Execution
```bash
# Run all functional tests
pytest tests/functional/ -v

# Run specific test class
pytest tests/functional/test_end_to_end_workflows.py::TestCoreUserWorkflows -v

# Run with detailed output
pytest tests/functional/ -v -s --tb=short
```

### Expected Initial Results

These tests are designed to **FAIL initially** because they validate functionality that is currently broken or missing according to the STATUS report:

- `test_cli_to_mcp_manager_integration` - Will expose CLI architectural issues
- `test_registry_manager_functionality` - Will reveal registry loading problems  
- `test_configuration_profile_management` - Will show configuration gaps
- `test_installation_method_validation` - Will expose installer instantiation issues

## Gaming Resistance Validation

Each test includes comments explaining why it cannot be gamed:

```python
def test_example_workflow(self):
    # This test cannot be gamed because:
    # 1. Uses actual CLI interface (not mocked internals)
    # 2. Verifies file system changes occurred
    # 3. Validates multiple observable outcomes
    # 4. Checks persistent state changes
    # An AI cannot fake this with stubs
```

### Anti-Gaming Patterns

❌ **Easily Gamed (Avoided)**:
```python
# Bad: Can be faked with mocks
assert some_function_called == True
assert mock_installer.install.called

# Bad: Tests implementation details
assert internal_variable == expected_value
```

✅ **Un-Gameable (Implemented)**:
```python
# Good: Tests observable outcomes
assert config_file.exists()
assert "server_name" in config_file.read_text()

# Good: Tests through real interface
result = runner.invoke(main, ['list'])
assert result.exit_code == 0
assert "6 servers" in result.output
```

## Test Data and Fixtures

### Temporary Test Environment

Tests create isolated temporary environments to avoid affecting the real system:
- Temporary directories for configuration files
- Test registry files with known data
- Isolated profile configurations

### Test Registry Structure

Tests use a controlled registry file with known servers:
```toml
[servers.test-server-npm]
name = "Test NPM Server"
installation = { method = "npm", package = "test-package" }

[servers.test-server-git] 
name = "Test Git Server"
installation = { method = "git", url = "https://github.com/test/repo.git" }
```

## Maintenance Guidelines

### Adding New Tests

When adding functional tests:

1. **Identify User Workflow**: What complete workflow are you testing?
2. **Define Observable Outcomes**: What would a user see if this works?
3. **Test Real Interface**: Use CLI commands, not internal APIs
4. **Verify Multiple Points**: Check primary outcome + side effects
5. **Document Gaming Resistance**: Explain why the test can't be faked

### Updating Tests

When implementation changes:

1. **Preserve Intent**: Keep the user workflow focus
2. **Update Interface Only**: Change how test calls functionality, not what it validates
3. **Maintain Resistance**: Ensure new test version still can't be gamed
4. **Verify Traceability**: Update STATUS/PLAN mapping if needed

## Success Criteria

These tests will be considered successful when:

1. **All Tests Pass**: Every test executes without errors
2. **Real Functionality Validated**: Tests confirm actual user workflows work
3. **Architecture Confirmed**: MCPManager-based architecture validated
4. **Error Handling Proven**: Error scenarios handle gracefully
5. **Coverage Gaps Closed**: STATUS report gaps addressed with working functionality

The goal is not just passing tests, but **confidence that MCPI actually works for real users**.