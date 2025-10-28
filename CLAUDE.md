# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Development installation
uv sync
source .venv/bin/activate

# Install development dependencies
uv sync --dev
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mcpi

# Run specific test file or class
pytest tests/test_registry.py
pytest tests/test_cli_scope_features.py::TestDynamicScopeType

# Run tests with verbose output and short traceback
pytest -v --tb=short

# Run with PYTHONPATH set (for when imports fail)
PYTHONPATH=src uv run pytest tests/test_cli_scope_features.py::TestDynamicScopeType -v --tb=short

# Validate registry data (integration tests for data/registry.json)
pytest tests/test_registry_integration.py -v
```

**Registry Validation**: The test suite includes integration tests that validate the actual `data/registry.json` file through multiple layers (JSON syntax, CUE schema, Pydantic models, semantic validation). This eliminates the need for ad-hoc validation commands. See `.agent_planning/REGISTRY_VALIDATION_TESTING.md` for details.

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
- All tests must pass (currently ~85% pass rate expected)
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

### Viewing CI Results

**GitHub Actions UI**:
1. Navigate to repository on GitHub
2. Click "Actions" tab
3. Select workflow run to view results
4. Download coverage report from artifacts

**Status Badge**:
The README displays a CI status badge showing the current build status.

### Python Version Support

**Current**: Python 3.12+ (as specified in `pyproject.toml`)

**CI Testing**: Tests on both Python 3.12 and 3.13

**Future**: To support older Python versions (3.9-3.11), update:
1. `requires-python` in `pyproject.toml`
2. `python-version` matrix in `.github/workflows/test.yml`
3. Test and fix any compatibility issues

## Project Architecture

MCPI (Model Context Protocol Interface) is a command-line tool and Python library for managing MCP servers across different MCP-compatible clients. The architecture uses a **plugin-based design** with scope-based configuration management.

### Core Architecture: Plugin System

**MCP Client Plugins (`mcpi.clients/`)**

The system uses a plugin architecture where each MCP client (Claude Code, Cursor, VS Code) is implemented as a plugin:

- `base.py`: Abstract base classes (`MCPClientPlugin`, `ScopeHandler`)
- `file_based.py`: Reusable file-based scope implementations (`FileBasedScope`, `JSONFileReader`, `JSONFileWriter`)
- `claude_code.py`: Claude Code plugin with 4 configuration scopes
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

**Registry System (`mcpi.registry/`)**

- `catalog.py`: Server catalog with Pydantic models (`MCPServer`)
- `discovery.py`: Server search and discovery functionality
- `validation.py`: Registry data validation
- Data source: `data/registry.json` contains all known MCP servers

**CLI Interface (`mcpi.cli`)**

- Click-based command structure with lazy initialization
- Rich console output for enhanced user experience
- Dynamic scope parameter type that validates based on selected client
- Commands: `list`, `search`, `info`, `install`, `uninstall`, `status`, etc.

### Key Design Patterns

**Plugin Architecture**: Each MCP client is an independent plugin implementing `MCPClientPlugin` protocol

**Dependency Injection**: Uses protocols (`ConfigReader`, `ConfigWriter`, `SchemaValidator`) for testability

**Lazy Initialization**: CLI lazy-loads `MCPManager` and `ServerCatalog` for fast startup

**Scope-based Configuration**: Multi-level configuration with priority-based merging

**Type Safety**: Extensive use of Pydantic models and TypedDict for configuration

### Data Flow

1. **Client Detection**: `MCPManager` auto-detects installed clients (priority: claude-code, cursor, vscode)
2. **Registry Loading**: `ServerCatalog` loads `data/registry.json` with available servers
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
