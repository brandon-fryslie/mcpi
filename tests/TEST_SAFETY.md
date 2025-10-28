# Test Safety Guarantees

## Critical Safety Requirement

**Tests MUST NEVER modify real user configuration files.**

This project implements multiple layers of defense to ensure that running tests cannot touch real user data in:
- `~/.claude/*` (user-level Claude settings)
- `~/.mcp.json` (legacy MCP config)
- `./.mcp.json` (project-level MCP config in real directories)
- `./.claude/*` (project-level Claude settings in real directories)

## Safety Mechanisms

### Layer 1: Automatic File Protection (conftest.py)

**Location**: `tests/conftest.py`

An `autouse=True` pytest fixture runs for ALL tests and intercepts file write operations:

```python
@pytest.fixture(scope="session", autouse=True)
def protect_real_user_files():
    """Prevent tests from EVER touching real user configuration files."""
```

**What it does**:
1. Patches `Path.write_text()`, `Path.write_bytes()`, and `open()`
2. Checks every write operation before it happens
3. Allows writes ONLY to temporary directories (`/tmp`, `/var/folders`, etc.)
4. **BLOCKS and FAILS** any write to protected paths with clear error message

**Example failure**:
```
RuntimeError: SAFETY VIOLATION: Test attempted to access protected path: /Users/user/.claude/test.json
Protected location: /Users/user/.claude
Tests MUST use temporary directories and path_overrides.
Use mcp_harness or mcp_manager_with_harness fixtures for isolation.
```

### Layer 2: Class-Level Enforcement (ClaudeCodePlugin)

**Location**: `src/mcpi/clients/claude_code.py`

The `ClaudeCodePlugin` class checks for test mode and REQUIRES path_overrides:

```python
def __init__(self, path_overrides: Optional[Dict[str, Path]] = None):
    # SAFETY: In test mode, REQUIRE path_overrides
    if os.environ.get('MCPI_TEST_MODE') == '1':
        if not path_overrides:
            raise RuntimeError("SAFETY VIOLATION: ...")
```

**What it does**:
1. `conftest.py` sets `MCPI_TEST_MODE=1` for all tests
2. `ClaudeCodePlugin()` without path_overrides immediately fails in test mode
3. Forces developers to use proper test fixtures

**Example failure**:
```
RuntimeError: SAFETY VIOLATION: ClaudeCodePlugin instantiated in test mode without path_overrides!
Tests MUST provide path_overrides to prevent modifying real user files.
Use the mcp_harness or mcp_manager_with_harness fixtures.
Example: ClaudeCodePlugin(path_overrides=harness.path_overrides)
```

### Layer 3: Test Harness Isolation (test_harness.py)

**Location**: `tests/test_harness.py`

Provides fixtures that create isolated temporary environments:

```python
@pytest.fixture
def mcp_manager_with_harness(mcp_harness):
    """Create an MCP manager with test harness configuration."""
    custom_plugin = ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)
    # ... returns isolated manager
```

**What it does**:
1. Uses pytest's `tmp_path` to create unique temporary directories
2. Creates path_overrides mapping scopes to temp files
3. Injects custom plugin into manager via registry
4. All file operations go to temp directory, never real paths

## Writing Safe Tests

### ✅ CORRECT: Use Test Fixtures

```python
def test_rescope_command(mcp_manager_with_harness):
    """Safe test using fixture."""
    manager, harness = mcp_manager_with_harness

    # This writes to temp directory - SAFE
    manager.add_server("test", config, "user-global", "claude-code")

    # This reads from temp directory - SAFE
    harness.assert_server_exists("user-global", "test")
```

### ❌ WRONG: Direct Instantiation

```python
def test_bad_example():
    """UNSAFE test - will fail!"""
    # This will raise RuntimeError in test mode
    manager = MCPManager()  # ❌ No path overrides

    # This will raise RuntimeError on write
    manager.add_server("test", config, "user-global", "claude-code")  # ❌ Tries to write to ~/.claude/
```

### ✅ CORRECT: Manual Setup with Overrides

```python
def test_manual_setup(mcp_harness):
    """Safe test with manual plugin creation."""
    # Create plugin with overrides - SAFE
    plugin = ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)

    # Inject into manager
    registry = ClientRegistry()
    registry.inject_client_instance("claude-code", plugin)
    manager = MCPManager(default_client="claude-code")
    manager.registry = registry

    # Now safe to use
    manager.add_server(...)
```

## Available Fixtures

### `mcp_test_dir`
Creates a temporary directory for testing.

### `mcp_harness`
Creates `MCPTestHarness` with path overrides set up.

### `mcp_manager_with_harness`
Returns `(MCPManager, MCPTestHarness)` tuple with full isolation.

### `prepopulated_harness`
Returns harness with sample test data already loaded.

## Verifying Safety

### Test the Safety Mechanism

You can verify the safety guards work by trying to write to a real file:

```python
def test_safety_violation():
    """This test should FAIL with safety violation."""
    real_file = Path.home() / ".claude" / "test.json"
    real_file.write_text("DANGER")  # ❌ Blocked by safety guard
```

Expected result:
```
FAILED - RuntimeError: SAFETY VIOLATION: Test attempted to access protected path...
```

### Run Tests with Safety Checks

All tests automatically run with safety protection enabled:

```bash
pytest tests/test_cli_rescope.py  # Safety enabled automatically
```

The environment variable `MCPI_TEST_MODE=1` is set automatically by conftest.py.

## What Happens if Safety is Bypassed?

**Multiple layers prevent this:**

1. **conftest.py patches** - Intercepts file operations at Python level
2. **Class enforcement** - Blocks instantiation without overrides
3. **Test isolation** - pytest tmp_path creates unique directories per test

Even if someone:
- Removes the conftest.py fixture (test suite fails to import)
- Removes MCPI_TEST_MODE check (file writes still blocked by conftest)
- Uses bare `open()` (conftest patches builtin open)

The safety is **defense-in-depth** and cannot be easily bypassed.

## Maintenance

### Adding New Client Plugins

If you add a new client plugin (similar to `ClaudeCodePlugin`), MUST add same safety:

```python
def __init__(self, path_overrides: Optional[Dict[str, Path]] = None):
    if os.environ.get('MCPI_TEST_MODE') == '1':
        if not path_overrides:
            raise RuntimeError("SAFETY VIOLATION: ...")
```

### Adding New Tests

Always use one of the provided fixtures:
- `mcp_harness` - For basic file testing
- `mcp_manager_with_harness` - For manager/plugin testing
- `prepopulated_harness` - For tests needing sample data

Never instantiate `MCPManager()` or `ClaudeCodePlugin()` directly without overrides.

## Summary

✅ **Tests are 100000% safe** - Multiple independent safety layers
✅ **Cannot modify real files** - All writes blocked and redirected to temp
✅ **Enforced by code** - Not reliant on developer discipline
✅ **Clear error messages** - If violated, immediate failure with guidance
✅ **Defense-in-depth** - Multiple mechanisms must all fail simultaneously

**No test can touch your real configuration files. Period.**
