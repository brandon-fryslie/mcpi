# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup

**Important for macOS iCloud Drive**: This repository supports development in iCloud Drive with special configuration to avoid intermittent import issues caused by iCloud's hidden file flags.

**Option 1: .venv.nosync (Recommended for full development)**
```bash
# Use .venv.nosync (excluded from iCloud sync)
python -m venv .venv.nosync
source .venv.nosync/bin/activate  # via symlink: source .venv/bin/activate
pip install -e .
pip install pytest pytest-cov black ruff mypy
```

**Option 2: UV Tool Install (Recommended for CLI development)**
```bash
# Install as UV tool (stored in ~/.local/, not in iCloud)
uv tool install --editable .

# Use from anywhere
mcpi --help

# For testing (no activation needed)
pytest  # Uses pythonpath from pyproject.toml
```

**Standard setup (works outside iCloud Drive)**
```bash
# Development installation
uv sync
source .venv/bin/activate

# Install development dependencies
uv sync --dev
```

**Current Configuration**: This project is configured with `.venv` as a symlink to `.venv.nosync`, making it safe for iCloud Drive development while maintaining compatibility with standard tooling.

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mcpi

# Run specific test file or class
pytest tests/test_catalog.py
pytest tests/test_cli_scope_features.py::TestDynamicScopeType

# Run tests with verbose output and short traceback
pytest -v --tb=short

# Run with PYTHONPATH set (for when imports fail)
PYTHONPATH=src uv run pytest tests/test_cli_scope_features.py::TestDynamicScopeType -v --tb=short

# Validate catalog data (integration tests for data/catalog.json)
pytest tests/test_registry_integration.py -v
```

**Catalog Validation**: The test suite includes integration tests that validate the actual `data/catalog.json` file through multiple layers (JSON syntax, CUE schema, Pydantic models, semantic validation). This eliminates the need for ad-hoc validation commands.

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type checking
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ --fix && mypy src/
```

**IMPORTANT: Black + Pytest Best Practice**

When formatting test code, Black may remove imports that appear unused to static analysis but are actually pytest fixtures used via dependency injection. To prevent this:

1. **Always add `# noqa: F401` to fixture imports**:
   ```python
   # In conftest.py or test module __init__.py
   from tests.test_harness import (  # noqa: F401
       mcp_harness,
       mcp_test_dir,
       prepopulated_harness,
   )
   ```

2. **Always run tests after formatting**:
   ```bash
   black src/ tests/ && pytest --tb=no -q
   ```

3. **Watch for these patterns in diffs**:
   - Lines starting with `-from tests.` (fixture imports being removed)
   - Lines starting with `-from .conftest import` (fixture imports being removed)

4. **If Black removes fixture imports**:
   - Restore the import
   - Add `# noqa: F401` comment
   - Re-run Black to verify it preserves the import
   - Run tests to verify fixtures work

This is a known limitation when formatting pytest code - fixtures appear unused because they're injected by pytest's dependency injection system, not explicitly called in code.

### Application Commands
```bash
# Run the CLI tool
python -m mcpi.cli --help

# Or use the installed script
mcpi --help
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and quality assurance.

### Workflow Overview

**Location**: `.github/workflows/test.yml`

**Triggers**:
- Push to `master`, `main`, or `develop` branches
- Pull requests to `master`, `main`, or `develop` branches
- Manual workflow dispatch

**Python Versions**: 3.12, 3.13 (matching `requires-python >= 3.12`)

**Operating Systems**: Ubuntu (Linux), macOS, Windows

### CI Jobs

**1. Test Job**
- Runs pytest across all Python versions and operating systems
- Generates coverage report on Ubuntu + Python 3.12
- Uploads coverage HTML report as artifact (30-day retention)
- Uses uv for fast dependency installation with caching

**2. Quality Job**
- Runs on Ubuntu + Python 3.12
- **Black**: Code formatting check (blocking - must pass)
- **Ruff**: Linting (non-blocking - warnings shown)
- **mypy**: Type checking (non-blocking - errors shown)

**3. Test Summary Job**
- Aggregates results from test and quality jobs
- Fails if tests fail
- Shows warnings if quality checks have issues

### Quality Gates

**Blocking (Must Pass)**:
- All tests must pass
- Black formatting must be clean

**Non-Blocking (Warnings Only)**:
- Ruff linting issues (shown but don't fail build)
- mypy type errors (shown but don't fail build)

### Local CI Simulation

Run the same checks locally before pushing:

```bash
# Run tests
pytest -v --tb=short

# Generate coverage report
pytest --cov=src/mcpi --cov-report=term --cov-report=html

# Check formatting
black --check src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Fix issues
black src/ tests/
ruff check src/ tests/ --fix

# IMPORTANT: Always verify tests pass after formatting
pytest --tb=no -q
```

## Project Architecture

MCPI (Model Context Protocol Interface) is a command-line tool and Python library for managing MCP servers across different MCP-compatible clients. The architecture uses a **plugin-based design** with scope-based configuration management.

### Core Architecture: Plugin System

**MCP Client Plugins (`mcpi.clients/`)**

The system uses a plugin architecture where each MCP client (Claude Code, Cursor, VS Code) is implemented as a plugin:

- `base.py`: Abstract base classes (`MCPClientPlugin`, `ScopeHandler`)
- `file_based.py`: Reusable file-based scope implementations (`FileBasedScope`, `JSONFileReader`, `JSONFileWriter`)
- `claude_code.py`: Claude Code plugin with 6 configuration scopes
- `protocols.py`: Protocol definitions for dependency injection
- `types.py`: Shared type definitions (`ServerInfo`, `ServerConfig`, `ServerState`, `OperationResult`)
- `manager.py`: Main `MCPManager` orchestrating all clients
- `registry.py`: Client plugin registry and discovery

**Scope-Based Configuration**

Each client plugin defines multiple configuration scopes (e.g., project-level, user-level) with different priorities:

1. **Scope Hierarchy**: Lower priority numbers override higher (e.g., project overrides user)
2. **Scope Types**: Project-level (`.mcp.json`), project-local (`.claude/settings.local.json`), user-level (`~/.claude/settings.json`)
3. **File-Based Implementation**: Most scopes use file-based configuration with JSON/YAML support
4. **Schema Validation**: Each scope validates against a schema (located in `clients/schemas/`)

**Server Catalog System (`mcpi.registry/`)**

- `catalog.py`: Server catalog with Pydantic models (`MCPServer`, `ServerRegistry`)
- `discovery.py`: Server search and discovery functionality
- `validation.py`: Catalog data validation
- `cue_validator.py`: CUE schema validation for catalog data
- Data source: `data/catalog.json` contains all known MCP servers

**CLI Interface (`mcpi.cli`)**

- Click-based command structure with lazy initialization
- Rich console output for enhanced user experience
- Dynamic scope parameter type that validates based on selected client
- Commands: `list`, `search`, `info`, `add`, `remove`, `enable`, `disable`, `rescope`, etc.

### Terminology: Catalog vs Registry

**Important distinction**:
- **Server Catalog** (`data/catalog.json`): The data file containing definitions of available MCP servers
- **Client Registry** (`ClientRegistry` class): The registry of MCP client plugins (Claude Code, Cursor, VS Code)

When updating code or documentation, use "catalog" when referring to the server data, and "registry" only when referring to the client plugin system.

### Key Design Patterns

**Plugin Architecture**: Each MCP client is an independent plugin implementing `MCPClientPlugin` protocol

**Dependency Injection**: Uses protocols (`ConfigReader`, `ConfigWriter`, `SchemaValidator`) for testability

**Lazy Initialization**: CLI lazy-loads `MCPManager` and `ServerCatalog` for fast startup

**Scope-based Configuration**: Multi-level configuration with priority-based merging

**Type Safety**: Extensive use of Pydantic models and TypedDict for configuration

### Data Flow

1. **Client Detection**: `MCPManager` auto-detects installed clients (priority: claude-code, cursor, vscode)
2. **Catalog Loading**: `ServerCatalog` loads `data/catalog.json` with available servers
3. **Scope Resolution**: Plugin determines which scope to use based on CLI flags (--scope, --client)
4. **Configuration Operations**: Scope handler reads/writes configuration files with validation
5. **Installation**: Servers installed using method-specific commands (npx, npm, pip, uv, git)

### Testing Strategy

- **Unit Tests**: Test individual components in isolation with mocking
- **Integration Tests**: Test workflows end-to-end (see `test_installer_workflows_integration.py`)
- **Functional Tests**: Un-gameable tests that verify real functionality (see `test_cli_scope_features.py`)
- **Test Harness**: Custom test harness pattern for complex scenarios (see `test_harness.py`)
- **CI/CD**: Automated testing on every push via GitHub Actions

### Key Dependencies

- **Pydantic**: Data validation and settings management
- **Click**: CLI framework with rich help system
- **Rich**: Enhanced console output and tables
- **jsonschema**: JSON schema validation for configuration
- **PyYAML**: YAML schema support

## Dependency Inversion Principle (DIP) Implementation

### Overview

MCPI follows the Dependency Inversion Principle to enable true unit testing, improve modularity, and maintain SOLID architecture. This was implemented in Phase 1 (v2.0) for core components.

### What Changed (Breaking Changes)

**Before (v1.x)**:
```python
# Components created dependencies internally (hidden dependencies)
catalog = ServerCatalog()  # Hardcoded path to data/catalog.json
manager = MCPManager()      # Created ClientRegistry internally
```

**After (v2.0)**:
```python
# Dependencies must be injected explicitly
catalog = ServerCatalog(catalog_path=Path("data/catalog.json"))
manager = MCPManager(registry=ClientRegistry())

# OR use factory functions (recommended)
catalog = create_default_catalog()  # Handles default path
manager = create_default_manager()  # Creates default registry
```

### When to Use Each Pattern

**Use Factory Functions** (Production Code):
```python
from mcpi.registry.catalog import create_default_catalog
from mcpi.clients.manager import create_default_manager

# Simple, handles all defaults
catalog = create_default_catalog()
manager = create_default_manager()
```

**Use Explicit Injection** (Testing/Advanced Use):
```python
from mcpi.registry.catalog import ServerCatalog, create_test_catalog
from mcpi.clients.manager import MCPManager, create_test_manager
from mcpi.clients.registry import ClientRegistry
from pathlib import Path

# Testing with custom dependencies
test_catalog = ServerCatalog(catalog_path=Path("/tmp/test.json"))
test_manager = MCPManager(registry=mock_registry)

# Or use test factories
test_catalog = create_test_catalog(Path("/tmp/test.json"))
test_manager = create_test_manager(mock_registry)
```

### Testing Patterns

**Unit Testing** (No File I/O):
```python
# Create catalog with explicit path to temp file
test_path = tmp_path / "test-catalog.json"
test_path.write_text(json.dumps({...}))
catalog = ServerCatalog(catalog_path=test_path)

# Or use test factory
catalog = create_test_catalog(test_path)
```

**Integration Testing** (Use MCPTestHarness):
```python
from tests.test_harness import MCPTestHarness

harness = MCPTestHarness(tmp_path)
harness.setup_scope_files()

# Create plugin with path overrides
plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
registry = ClientRegistry()
registry.inject_client_instance("claude-code", plugin)

# Create manager with injected registry
manager = MCPManager(registry=registry, default_client="claude-code")
```

### Benefits of DIP

1. **True Unit Testing**: No file system access required
2. **Component Isolation**: Each component has explicit dependencies
3. **Easier Mocking**: Dependencies injected, not created internally
4. **SOLID Compliance**: High-level modules depend on abstractions
5. **Parallel Testing**: No shared state between test instances

### Migration Checklist

If updating code that uses MCPI as a library:

- [ ] Replace `ServerCatalog()` with `create_default_catalog()`
- [ ] Replace `MCPManager()` with `create_default_manager()`
- [ ] Update tests to use `create_test_catalog(path)` and `create_test_manager(registry)`
- [ ] Remove any workarounds for testing (mocks, patches)
- [ ] Use explicit injection for advanced use cases
- [ ] Run tests to verify no regressions

## User-Global Disable Mechanism

### Overview

For user-global MCP servers in Claude Code, there is NO built-in disable mechanism. MCPI implements a custom disable mechanism using a shadow configuration file.

### Implementation Design

**Files**:
- `~/.config/claude/settings.json`: Active (enabled) MCP servers
- `~/.claude/disabled-mcp.json`: Disabled MCP servers (custom MCPI file)

**Behavior**:
1. **Enabled servers**: Stored in the active configuration file
2. **Disabled servers**: Configuration moved from active file to disabled file
3. **Added servers**: Combination of configurations from both files
4. **State detection**: Servers in active file = enabled, servers in disabled file = disabled

### Operations

**Enable a server** (`mcpi enable <server-name>`):
1. Remove server configuration from `~/.claude/disabled-mcp.json`
2. Add server configuration to `~/.config/claude/settings.json`
3. Result: Server appears in `claude mcp list` output

**Disable a server** (`mcpi disable <server-name>`):
1. Remove server configuration from `~/.config/claude/settings.json`
2. Add server configuration to `~/.claude/disabled-mcp.json`
3. Result: Server removed from `claude mcp list` output

**List servers** (`mcpi list`):
1. Read configurations from both active and disabled files
2. Display combined list with state indicators (enabled/disabled)
3. Show accurate state for each server

### Validation Requirements

**Critical validation**:
- Running `claude mcp list` shows only enabled servers
- Running `mcpi list` shows ALL servers (enabled + disabled) with correct state
- No servers in user-global scope should appear as 'disabled' in `claude mcp list` output
- Servers disabled via `mcpi disable` must not appear in `claude mcp list` output
- Servers enabled via `mcpi enable` must appear in `claude mcp list` output

**Test Coverage Requirements**:
- Unit tests for enable/disable operations
- Integration tests for file operations
- End-to-end tests validating `claude mcp list` behavior
- Edge case tests (already enabled, already disabled, non-existent server)
- 100% test coverage for this functionality
- 100% tests passing

### Implementation Files

- `src/mcpi/clients/file_move_enable_disable_handler.py`: Handler for file-based enable/disable
- `src/mcpi/clients/claude_code.py`: Integration with Claude Code plugin
- `tests/test_user_global_disable_mechanism.py`: Comprehensive test suite

### Status

This is the **TOP PRIORITY** feature. All work must be paused until:
1. Functionality works correctly in manual testing
2. All unit, integration, and E2E tests pass
3. 100% test coverage achieved
4. All edge cases handled
5. Validation against `claude mcp list` succeeds
