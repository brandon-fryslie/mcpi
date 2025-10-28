# MCP Test Harness Documentation

## Overview

The MCP test harness provides a comprehensive testing framework for testing MCP client operations against real files in isolated temporary directories. This ensures tests are reproducible, isolated, and can validate actual file operations.

## Key Features

1. **Isolated Testing**: Each test gets its own temporary directory
2. **Path Mocking**: File paths are redirected to test directories with predictable naming
3. **Data Prepopulation**: Easily set up test data before running tests
4. **Validation Helpers**: Assert file validity, server existence, and configurations
5. **Manager Integration**: Test the full MCP manager stack with real file I/O

## Architecture

### File Naming Convention

Test files follow the pattern: `<tmp_dir>/<client_name>_<scope_name>_<original_filename>`

Example:
- `claude-code_user-global_settings.json`
- `claude-code_project-mcp_.mcp.json`
- `claude-code_user-internal_.claude.json`

### Components

1. **MCPTestHarness**: Main harness class with utilities for file operations and assertions
2. **Fixtures**:
   - `mcp_test_dir`: Creates temporary directory
   - `mcp_harness`: Creates harness with scope setup
   - `mcp_manager_with_harness`: Creates manager with custom paths
   - `prepopulated_harness`: Harness with sample data

## Usage Examples

### Basic Setup

```python
def test_with_harness(mcp_harness):
    """Basic test using the harness."""
    # Prepopulate a file
    mcp_harness.prepopulate_file("user-global", {
        "mcpServers": {
            "test-server": {
                "command": "npx",
                "args": ["test-package"],
                "type": "stdio"
            }
        }
    })
    
    # Assertions
    mcp_harness.assert_valid_json("user-global")
    mcp_harness.assert_server_exists("user-global", "test-server")
    mcp_harness.assert_server_command("user-global", "test-server", "npx")
```

### Testing with MCP Manager

```python
def test_manager_operations(mcp_manager_with_harness):
    """Test manager with real file operations."""
    manager, harness = mcp_manager_with_harness
    
    # Add a server
    config = ServerConfig(
        command="python",
        args=["-m", "mcp_server"],
        type="stdio"
    )
    result = manager.add_server("my-server", config, "user-global", "claude-code")
    assert result.success
    
    # Verify file was written
    harness.assert_server_exists("user-global", "my-server")
    
    # Check server configuration
    server_config = harness.get_server_config("user-global", "my-server")
    assert server_config["command"] == "python"
```

### Testing Multiple Scopes

```python
def test_scope_isolation(mcp_manager_with_harness):
    """Test that scopes are isolated."""
    manager, harness = mcp_manager_with_harness
    
    # Add servers to different scopes
    for scope in ["user-global", "project-mcp", "user-local"]:
        config = ServerConfig(
            command="npx",
            args=[f"{scope}-server"],
            type="stdio"
        )
        manager.add_server(f"{scope}-test", config, scope, "claude-code")
    
    # Verify isolation
    assert harness.count_servers_in_scope("user-global") == 1
    assert harness.count_servers_in_scope("project-mcp") == 1
    assert harness.count_servers_in_scope("user-local") == 1
```

## Available Assertions

### File Validation
- `assert_valid_json(scope_name)`: Verify file contains valid JSON
- `read_scope_file(scope_name)`: Read and parse a scope file

### Server Assertions
- `assert_server_exists(scope_name, server_id)`: Verify server exists
- `assert_server_command(scope_name, server_id, expected_command)`: Verify command
- `get_server_config(scope_name, server_id)`: Get full server configuration
- `count_servers_in_scope(scope_name)`: Count servers in a scope

### Data Setup
- `prepopulate_file(scope_name, content)`: Set up test data
- `setup_scope_files(client_name)`: Initialize all scope paths

## Scope Types

The harness supports all Claude Code scopes:

1. **project-mcp**: Project-level MCP configuration (`.mcp.json`)
2. **project-local**: Project-local Claude settings (`.claude/settings.local.json`)
3. **user-local**: User-local Claude settings (`~/.claude/settings.local.json`)
4. **user-global**: User-global Claude settings (`~/.claude/settings.json`)
5. **user-internal**: User internal configuration (`~/.claude.json`)
6. **user-mcp**: User MCP servers configuration (`~/.claude/mcp_servers.json`)

## File Format Expectations

Different scopes use different file formats:

### MCP Configuration Format (project-mcp, user-mcp)
```json
{
  "mcpServers": {
    "server-id": {
      "command": "npx",
      "args": ["package"],
      "type": "stdio"
    }
  }
}
```

### Claude Settings Format (project-local, user-local, user-global)
```json
{
  "mcpEnabled": true,
  "mcpServers": {
    "server-id": {
      "command": "python",
      "args": ["-m", "module"],
      "type": "stdio"
    }
  }
}
```

### Internal Configuration Format (user-internal)
```json
{
  "mcpServers": {
    "server-id": {
      "command": "node",
      "args": ["server.js"],
      "type": "stdio",
      "disabled": false
    }
  }
}
```

## Best Practices

1. **Always use fixtures**: Don't create harnesses manually
2. **Clean assertions**: Use provided assertion methods for clarity
3. **Test isolation**: Each test should be independent
4. **Prepopulate sparingly**: Only add data needed for the specific test
5. **Verify both positive and negative cases**: Test both success and failure scenarios

## Running Tests

```bash
# Run all harness tests
pytest tests/test_harness_example.py -v

# Run specific test class
pytest tests/test_harness_example.py::TestMCPHarnessBasics -v

# Run with coverage
pytest tests/test_harness_example.py --cov=mcpi.clients
```