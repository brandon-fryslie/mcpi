# MCP Manager (mcpi) - Project Specification

## Overview

MCP Manager (mcpi) is a comprehensive command-line tool and Python library for managing Model Context Protocol (MCP) servers. It provides an exhaustive registry of known MCP servers and uses a scope-based plugin architecture to seamlessly integrate them with Claude Code and other compatible MCP clients.

## Goals

### Primary Goals
- **Centralized MCP Server Registry**: Maintain a comprehensive, up-to-date catalog of all known MCP servers
- **Universal Installation**: Abstract installation complexity across different MCP clients (Claude Code, Cursor, VS Code)
- **Scope-Based Configuration Management**: Manage servers across multiple hierarchical configuration scopes
- **Developer Experience**: Provide intuitive CLI and programmatic interfaces

### Secondary Goals
- **Discovery**: Help users find relevant MCP servers for their use cases
- **Validation**: Ensure MCP servers are properly configured and functional
- **Multi-Client Support**: Support multiple MCP clients through plugin architecture
- **Documentation**: Provide comprehensive documentation for each MCP server

## Architecture

### Core Components

#### 1. MCP Server Registry (`mcpi.registry`)
- **Server Catalog**: JSON-based registry of all known MCP servers
- **Metadata Management**: Server descriptions, capabilities, dependencies, installation methods
- **Category Organization**: Servers organized by functionality (filesystem, databases, APIs, etc.)
- **Pydantic Models**: Strong type validation using `MCPServer` and `ServerRegistry` models

#### 2. Plugin-Based Client System (`mcpi.clients`)
- **MCPClientPlugin Protocol**: Abstract interface for implementing MCP client support
- **Scope-Based Configuration**: Each client defines multiple configuration scopes with priorities
- **File-Based Implementation**: Most scopes use JSON/YAML configuration files
- **Schema Validation**: Configuration validated against client-specific YAML schemas
- **Client Registry**: Dynamic client detection and plugin loading

##### Key Classes
- `MCPClientPlugin`: Abstract base class for client plugins
- `ScopeHandler`: Abstract base class for scope implementations
- `FileBasedScope`: Reusable file-based scope implementation
- `ClaudeCodePlugin`: Reference implementation for Claude Code
- `MCPManager`: Orchestrates all client plugins

#### 3. Scope Hierarchy System
Each client plugin defines multiple configuration scopes with different priorities:

**Example: Claude Code Scopes**
| Scope Name | Type | Priority | Path | Description |
|------------|------|----------|------|-------------|
| `project-mcp` | Project | 1 | `.mcp.json` | Project-level MCP configuration (highest) |
| `project-local` | Project | 2 | `.claude/settings.local.json` | Project-local Claude settings |
| `user-local` | User | 3 | `~/.claude/settings.local.json` | User-local Claude settings |
| `user-global` | User | 4 | `~/.claude/settings.json` | User-global Claude settings |
| `user-internal` | User | 5 | `~/.claude.json` | User internal configuration |
| `user-mcp` | User | 6 | `~/.claude/mcp_servers.json` | User MCP servers (lowest) |

**Priority System**: Lower priority numbers override higher. Project-level scopes override user-level.

#### 4. Installation Engine (`mcpi.installer`)
- **Multi-Method Support**: npm/npx, pip/uv, git, docker
- **Method-Specific Installers**: Separate installer for each installation method
- **Dependency Resolution**: Handle package managers, system dependencies
- **Stateful Installation**: Track installation state and support rollback

#### 5. CLI Interface (`mcpi.cli`)
- **Click Framework**: Command-line interface with rich help
- **Lazy Initialization**: Fast startup with lazy-loaded components
- **Rich Console Output**: Enhanced tables and formatting
- **Dynamic Scope Type**: Validates scope names based on selected client
- **Tab Completion**: Shell completion for bash, zsh, fish

### Data Structures

#### Server Registry Entry (`MCPServer`)
```python
{
    "description": "Access local filesystem operations",
    "command": "npx",
    "args": ["-y", "@anthropic/mcp-server-filesystem", "/path/to/allowed/files"],
    "repository": "https://github.com/anthropics/mcp-server-filesystem",
    "categories": ["filesystem", "local"]
}
```

#### Scope Configuration (`ScopeConfig`)
```python
ScopeConfig(
    name="project-mcp",
    description="Project-level MCP configuration",
    priority=1,
    path=Path(".mcp.json"),
    is_project_level=True
)
```

#### Server Configuration (`ServerConfig`)
```python
ServerConfig(
    command="npx",
    args=["-y", "@anthropic/mcp-server-filesystem"],
    env={"ALLOWED_PATH": "/path/to/files"}
)
```

## Technical Implementation

### Technology Stack
- **Language**: Python 3.9+
- **Package Manager**: uv for dependency management
- **CLI Framework**: Click for command-line interface
- **Console Output**: Rich for enhanced formatting
- **Data Validation**: Pydantic for type validation
- **Schema Validation**: jsonschema with YAML schemas
- **Configuration**: JSON for runtime config, YAML for schemas

### Project Structure
```
mcpi/
├── src/mcpi/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point (Click-based commands)
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base.py         # MCPClientPlugin, ScopeHandler protocols
│   │   ├── file_based.py   # FileBasedScope implementation
│   │   ├── claude_code.py  # Claude Code plugin implementation
│   │   ├── manager.py      # MCPManager orchestration
│   │   ├── registry.py     # Client plugin registry
│   │   ├── protocols.py    # Protocol definitions
│   │   ├── types.py        # Shared type definitions
│   │   └── schemas/        # YAML schema files
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── catalog.py      # ServerCatalog, MCPServer models
│   │   ├── discovery.py    # Server search and discovery
│   │   ├── validation.py   # Registry validation
│   │   └── cue_validator.py # CUE schema validation
│   ├── installer/
│   │   ├── __init__.py
│   │   ├── base.py         # Base installer interface
│   │   ├── npm.py          # NPM/npx installer
│   │   ├── python.py       # pip/uv installer
│   │   └── git.py          # Git repository installer
│   ├── config/             # Legacy modules (mostly unused)
│   └── utils/
│       ├── __init__.py
│       ├── filesystem.py   # File system utilities
│       ├── validation.py   # Validation utilities
│       └── logging.py      # Logging setup
├── data/
│   ├── registry.json       # MCP server registry
│   └── registry.cue        # CUE schema for registry
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Shared fixtures
│   ├── test_harness.py     # Test harness for complex scenarios
│   ├── test_registry_*.py  # Registry tests
│   ├── test_clients_*.py   # Client plugin tests
│   ├── test_cli_*.py       # CLI command tests
│   └── test_functional_*.py # Functional workflow tests
├── pyproject.toml
├── README.md
├── LICENSE
└── PROJECT_SPEC.md (this file)
```

## Features

### Core Features

#### Discovery
- `mcpi search <query>`: Search servers by name, description, or capability
- `mcpi info <server>`: Show detailed information (registry + install status)
- `mcpi fzf`: Interactive fuzzy finder interface for browsing and managing servers (requires fzf)

#### Server Management
- `mcpi list`: List installed servers across all scopes
- `mcpi add <server>`: Install MCP server to a scope
- `mcpi remove <server>`: Remove MCP server from a scope
- `mcpi enable <server>`: Enable a disabled server
- `mcpi disable <server>`: Disable a server without removing
- `mcpi status`: Show system status and installed servers

#### Scope Management
- `mcpi scope list`: List available configuration scopes for current client
- `mcpi scope show <scope>`: Show details about a specific scope
- `mcpi rescope <server> --to <scope>`: Consolidate server to target scope (auto-removes from all other scopes)

#### Client Management
- `mcpi client list`: List detected MCP clients
- `mcpi client info <client>`: Show information about a specific client
- `mcpi client set-default <client>`: Set default client

#### Shell Integration
- `mcpi completion --shell bash`: Install bash completion
- `mcpi completion --shell zsh`: Install zsh completion
- `mcpi completion --shell fish`: Install fish completion

### Deferred Features (Post-1.0)

#### Not Yet Implemented
- `mcpi update <server>`: Update MCP server to latest version (1.1)
- `mcpi doctor`: Diagnose installation and configuration issues (1.1)
- `mcpi backup`: Backup current configuration (1.1)
- `mcpi restore <backup>`: Restore from backup (1.1)
- `mcpi sync`: Sync with remote registry updates (1.2)

## Dependencies

### Runtime Dependencies
- `click`: CLI framework
- `pydantic`: Data validation and settings management
- `jsonschema`: JSON schema validation
- `rich`: Rich text and beautiful formatting for CLI
- `pyyaml`: YAML parsing for schemas

### Development Dependencies
- `pytest`: Testing framework
- `black`: Code formatting
- `ruff`: Linting
- `mypy`: Type checking

## Quality Standards

### Code Quality
- Type hints for all public APIs
- Comprehensive error handling
- Structured logging throughout
- Plugin architecture for extensibility

### Documentation
- Complete README with accurate examples
- CLI help text for all commands
- Docstrings for all public functions
- PROJECT_SPEC aligned with implementation

### Testing Strategy
- Unit tests for individual components
- Integration tests for installation workflows
- Functional tests for CLI commands
- Test harness pattern for complex scenarios
- Current test pass rate: 85.3%

## Security Considerations

### Installation Security
- Validate configuration parameters
- Secure handling of environment variables
- Test mode protection to prevent touching real files
- Schema validation before writing configuration

### Registry Security
- CUE schema validation for registry data
- Pydantic model validation for type safety
- Manual review of registry entries
- Community contribution guidelines

## Deployment & Distribution

### Package Distribution
- PyPI package distribution (planned)
- GitHub releases
- Development installation via uv

### Installation Methods
```bash
# Via uvx (recommended)
uvx mcpi

# Via uv
uv tool install mcpi

# Development installation
git clone https://github.com/user/mcpi
cd mcpi
uv sync
source .venv/bin/activate
```

## Architecture Design Patterns

### Plugin Pattern
- `MCPClientPlugin` protocol defines client interface
- Each client is an independent plugin
- Plugins register themselves via `ClientRegistry`
- Easy to add new client support

### Scope-Based Configuration
- Hierarchical configuration with priority system
- Lower priority numbers override higher
- Scopes isolated by file paths
- Project-level vs user-level separation

### File-Based Storage
- Configuration stored in JSON files
- YAML schemas for validation
- Direct file manipulation (no database)
- Human-readable configuration

### Dependency Injection
- Protocols define interfaces (`ConfigReader`, `ConfigWriter`)
- Dependencies injected for testability
- Test harness provides safe overrides
- No global state or singletons

### Lazy Initialization
- CLI commands lazy-load components
- Fast startup time
- Only load what's needed
- Efficient for quick operations

## Implementation Notes

### Design Evolution
The current implementation evolved from an earlier profile-based design to a more flexible scope-based architecture:

**Old Approach (Deprecated)**:
- Profile-based configuration (`ProfileManager`)
- Template system for configuration
- Separate config manager layer

**Current Approach (Implemented)**:
- Scope-based plugin architecture
- Direct file manipulation with validation
- Each client defines its own scopes
- No template layer (configuration in files)

### Why Scope-Based Is Better
1. **More Flexible**: Clients define their own scope structure
2. **Less Abstraction**: Direct file manipulation is simpler
3. **Extensible**: Easy to add new clients with different scope models
4. **Standard-Aligned**: Matches how MCP clients actually work
5. **Test-Friendly**: Scope handlers easy to isolate and test

### Key Lessons Learned
- **Delete Over Fix**: Removing obsolete code faster than fixing
- **Documentation Matters**: Accurate docs more valuable than features
- **Test Infrastructure First**: Healthy tests enable fast development
- **Architecture Pays Off**: Good design makes features quick to add

## Future Enhancements

### Planned for 1.1
- `mcpi update` command for updating servers
- `mcpi doctor` for diagnostics
- Test coverage improvements to 90%+
- CLI refactoring (modularize 1,381-line cli.py)
- Additional integration tests

### Planned for 1.2+
- Additional client plugins (Cursor, VS Code)
- Web dashboard for registry management
- Configuration backup/restore
- Remote registry sync
- Community server submission system

### Integration Opportunities
- VS Code extension integration
- GitHub Actions for CI/CD workflows
- Homebrew formula for macOS
- Docker container support
