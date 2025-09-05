# MCP Manager (mcpi) - Project Specification

## Overview

MCP Manager (mcpi) is a comprehensive command-line tool and Python library for managing Model Context Protocol (MCP) servers. It provides an exhaustive registry of known MCP servers and abstracts the installation logic to seamlessly integrate them with Claude Code and other compatible tools.

## Goals

### Primary Goals
- **Centralized MCP Server Registry**: Maintain a comprehensive, up-to-date catalog of all known MCP servers
- **Universal Installation**: Abstract installation complexity across different tools (Claude Code, other MCP clients)
- **Configuration Management**: Simplify MCP server configuration and dependency management
- **Developer Experience**: Provide intuitive CLI and programmatic interfaces

### Secondary Goals
- **Discovery**: Help users find relevant MCP servers for their use cases
- **Validation**: Ensure MCP servers are properly configured and functional
- **Updates**: Manage MCP server updates and version compatibility
- **Documentation**: Provide comprehensive documentation for each MCP server

## Architecture

### Core Components

#### 1. MCP Server Registry (`mcpi.registry`)
- **Server Catalog**: JSON-based registry of all known MCP servers
- **Metadata Management**: Server descriptions, capabilities, dependencies, installation methods
- **Version Tracking**: Support for multiple versions and compatibility matrices
- **Category Organization**: Servers organized by functionality (file systems, databases, APIs, etc.)

#### 2. Installation Engine (`mcpi.installer`)
- **Multi-Target Support**: Install to Claude Code, other MCP clients
- **Dependency Resolution**: Handle Python packages, system dependencies, configuration files
- **Installation Methods**: Support npm, pip/uv, git, binary downloads
- **Rollback Capability**: Safe installation with rollback on failure

#### 3. Configuration Manager (`mcpi.config`)
- **Profile Management**: Different configuration profiles for different tools
- **Template System**: Pre-built configuration templates for common setups
- **Validation**: Validate configurations before deployment
- **Backup/Restore**: Configuration backup and restore functionality

#### 4. CLI Interface (`mcpi.cli`)
- **Discovery Commands**: Search, list, info commands
- **Installation Commands**: Install, uninstall, update commands
- **Management Commands**: Status, validate, config commands
- **Interactive Mode**: Guided installation and configuration

### Data Structures

#### Server Registry Entry
```python
{
    "id": "filesystem",
    "name": "Filesystem MCP Server",
    "description": "Access local filesystem operations",
    "category": ["filesystem", "local"],
    "author": "Anthropic",
    "repository": "https://github.com/anthropics/mcp-server-filesystem",
    "documentation": "https://docs.anthropic.com/mcp/servers/filesystem",
    "versions": {
        "latest": "1.0.0",
        "supported": ["1.0.0", "0.9.0"]
    },
    "installation": {
        "method": "npm",
        "package": "@anthropic/mcp-server-filesystem",
        "system_dependencies": [],
        "python_dependencies": []
    },
    "configuration": {
        "template": "filesystem_template.json",
        "required_params": ["root_path"],
        "optional_params": ["allowed_extensions"]
    },
    "capabilities": ["file_operations", "directory_listing"],
    "platforms": ["linux", "darwin", "windows"],
    "license": "MIT"
}
```

## Technical Implementation

### Technology Stack
- **Language**: Python 3.9+
- **Package Manager**: uv for dependency management
- **CLI Framework**: Click for command-line interface
- **Configuration**: TOML/JSON for configuration files
- **HTTP Client**: httpx for web requests
- **JSON Handling**: Pydantic for data validation

### Project Structure
```
mcpi/
├── src/mcpi/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── catalog.py      # Server catalog management
│   │   ├── discovery.py    # Server discovery logic
│   │   └── validation.py   # Registry validation
│   ├── installer/
│   │   ├── __init__.py
│   │   ├── base.py         # Base installer interface
│   │   ├── claude_code.py  # Claude Code specific installer
│   │   ├── npm.py          # NPM package installer
│   │   ├── python.py       # Python package installer
│   │   └── git.py          # Git repository installer
│   ├── config/
│   │   ├── __init__.py
│   │   ├── manager.py      # Configuration management
│   │   ├── profiles.py     # Profile management
│   │   └── templates.py    # Configuration templates
│   └── utils/
│       ├── __init__.py
│       ├── filesystem.py   # File system utilities
│       ├── validation.py   # Validation utilities
│       └── logging.py      # Logging setup
├── data/
│   ├── registry.json       # MCP server registry
│   └── templates/          # Configuration templates
├── tests/
│   ├── __init__.py
│   ├── test_registry.py
│   ├── test_installer.py
│   ├── test_config.py
│   └── test_cli.py
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## Features

### Core Features

#### Registry Management
- `mcpi list`: List all available MCP servers
- `mcpi search <query>`: Search servers by name, description, or capability
- `mcpi info <server>`: Show detailed information about a server
- `mcpi categories`: List server categories

#### Installation Management
- `mcpi install <server>`: Install MCP server
- `mcpi uninstall <server>`: Remove MCP server
- `mcpi update <server>`: Update MCP server to latest version
- `mcpi status`: Show status of installed servers

#### Configuration Management
- `mcpi config init`: Initialize configuration
- `mcpi config profile create <name>`: Create new profile
- `mcpi config profile switch <name>`: Switch active profile
- `mcpi config validate`: Validate current configuration

#### Advanced Features
- `mcpi doctor`: Diagnose installation and configuration issues
- `mcpi backup`: Backup current configuration
- `mcpi restore <backup>`: Restore from backup
- `mcpi sync`: Sync with remote registry updates

### Integration Features

#### Claude Code Integration
- Automatic detection of Claude Code installation
- Direct integration with Claude Code configuration files
- Support for Claude Code-specific features and settings

#### Generic MCP Client Support
- Plugin architecture for supporting additional MCP clients
- Generic configuration templates
- Standard MCP protocol compliance

## Dependencies

### Runtime Dependencies
- `click`: CLI framework
- `pydantic`: Data validation and settings management
- `httpx`: HTTP client for registry updates
- `toml`: TOML configuration parsing
- `jsonschema`: JSON schema validation
- `rich`: Rich text and beautiful formatting for CLI

### Development Dependencies
- `pytest`: Testing framework
- `pytest-asyncio`: Async testing support
- `black`: Code formatting
- `ruff`: Linting
- `mypy`: Type checking
- `coverage`: Test coverage

## Quality Standards

### Code Quality
- Type hints for all public APIs
- 95% test coverage minimum
- Comprehensive error handling
- Structured logging throughout

### Documentation
- Complete API documentation
- Usage examples for all CLI commands
- Server registry contribution guidelines
- Installation troubleshooting guides

### Testing Strategy
- Unit tests for all core functionality
- Integration tests for installation workflows
- CLI command testing
- Mock external dependencies appropriately

## Security Considerations

### Installation Security
- Verify package signatures where available
- Sandbox installation processes
- Validate configuration parameters
- Secure handling of credentials and API keys

### Registry Security
- Cryptographic verification of registry updates
- Malware scanning integration hooks
- Community reporting mechanisms for malicious packages

## Deployment & Distribution

### Package Distribution
- PyPI package distribution
- GitHub releases with binaries
- Docker container support
- Homebrew formula for macOS

### Installation Methods
```bash
# Via uv
uv add mcpi

# Via pip
pip install mcpi

# Via homebrew
brew install mcpi

# Development installation
git clone https://github.com/user/mcpi
cd mcpi
uv sync
```

## Future Enhancements

### Planned Features
- Web dashboard for registry management
- Plugin system for custom installers
- Integration with package managers (Homebrew, APT)
- Automated server compatibility testing
- Community server submission system

### Integration Opportunities
- VS Code extension integration
- GitHub Actions for CI/CD workflows
- Docker Compose template generation
- Kubernetes deployment manifests