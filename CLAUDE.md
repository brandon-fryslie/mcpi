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

# Run specific test file
pytest tests/test_registry.py

# Run tests with verbose output
pytest -v
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

MCPI (Model Context Protocol Interface) is a command-line tool and Python library for managing MCP servers. The architecture follows a modular design with clear separation of concerns:

### Core Modules

**Registry System (`mcpi.registry/`)**
- `catalog.py`: Server catalog management with Pydantic models (MCPServer, InstallationConfig)
- `discovery.py`: Server discovery and search functionality
- `doc_parser.py`: Documentation parsing and extraction
- `validation.py`: Registry data validation

**Installation Engine (`mcpi.installer/`)**
- `base.py`: Abstract base installer with InstallationResult dataclass
- `claude_code.py`: Claude Code-specific installer (primary target)
- `npm.py`: NPM package installer
- `python.py`: Python/pip package installer  
- `git.py`: Git repository installer

**Configuration Management (`mcpi.config/`)**
- `manager.py`: Main ConfigManager class with profile support
- `profiles.py`: Profile creation and switching
- `templates.py`: Configuration templates and validation

**CLI Interface (`mcpi.cli`)**
- Click-based command structure with lazy initialization
- Rich console output for enhanced user experience
- Commands organized by: discovery (list, search, info), installation (install, uninstall, update), management (status, config)

### Key Design Patterns

**Lazy Initialization**: CLI uses lazy loading for ServerCatalog and ConfigManager to improve startup performance

**Enum-based Configuration**: Uses Pydantic enums for InstallationMethod, Platform, and InstallationStatus to ensure type safety

**Profile-based Configuration**: Supports multiple configuration profiles for different environments (development, production)

**Template System**: Pre-built configuration templates for common MCP server setups

### Data Flow

1. **Registry Loading**: JSON/YAML registry files loaded into Pydantic models
2. **Server Discovery**: Search and filtering through catalog metadata
3. **Installation**: Method-specific installers handle package management
4. **Configuration**: Profile-aware config management updates target tool configs
5. **Validation**: Multi-layer validation from Pydantic models to custom validators

### Configuration Structure

The project uses TOML configuration with profile support:
- Default profile targets Claude Code (`~/.claude/mcp_servers.json`)
- Support for generic MCP clients
- Platform-specific path resolution (Darwin, Linux, Windows)

### Testing Strategy

Comprehensive test suite with:
- Unit tests for each module
- Integration tests for installation workflows
- Mock-based testing for external dependencies
- Coverage reporting with 95% target minimum

### Key Dependencies

- **Pydantic**: Data validation and settings management
- **Click**: CLI framework with rich help system
- **Rich**: Enhanced console output and tables
- **httpx**: Async HTTP client for registry updates
- **platformdirs**: Cross-platform directory management