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
```

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

### Application Commands
```bash
# Run the CLI tool
python -m mcpi.cli --help

# Or use the installed script
mcpi --help
```

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

### Key Dependencies

- **Pydantic**: Data validation and settings management
- **Click**: CLI framework with rich help system
- **Rich**: Enhanced console output and tables
- **jsonschema**: JSON schema validation for configuration
- **PyYAML**: YAML schema support