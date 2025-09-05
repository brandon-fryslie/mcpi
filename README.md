# MCP Manager (mcpi)

A comprehensive command-line tool and Python library for managing Model Context Protocol (MCP) servers. Discover, install, and configure MCP servers for Claude Code and other compatible tools with ease.

## Features

- **Comprehensive Registry**: Exhaustive catalog of known MCP servers
- **Universal Installation**: Install MCP servers across different tools and platforms
- **Configuration Management**: Simplified configuration with templates and profiles
- **CLI Interface**: Intuitive command-line interface for all operations
- **Claude Code Integration**: Native support for Claude Code configuration
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Installation

### Using uvx (Recommended)
```bash
uvx mcpi
```

### Using uv
```bash
uv tool install mcpi
```

### Development Installation
```bash
git clone https://github.com/user/mcpi
cd mcpi
uv sync
source .venv/bin/activate
```

## Quick Start

### Initialize Configuration
```bash
mcpi config init
```

### Discover MCP Servers
```bash
# List all available servers
mcpi list

# Search for specific functionality
mcpi search filesystem

# Get detailed information about a server
mcpi info filesystem
```

### Install MCP Servers
```bash
# Install to Claude Code (auto-detected)
mcpi install filesystem

# Install with specific configuration
mcpi install database --config postgres_template

# Install multiple servers
mcpi install filesystem database github
```

### Manage Installations
```bash
# Check status of installed servers
mcpi status

# Update a server
mcpi update filesystem

# Uninstall a server
mcpi uninstall filesystem
```

## CLI Commands

### Discovery Commands

#### `mcpi list [OPTIONS]`
List available MCP servers.

**Options:**
- `--category TEXT`: Filter by category
- `--platform TEXT`: Filter by platform
- `--json`: Output in JSON format

**Examples:**
```bash
mcpi list --category filesystem
mcpi list --platform darwin --json
```

#### `mcpi search <query> [OPTIONS]`
Search MCP servers by name, description, or capabilities.

**Examples:**
```bash
mcpi search "file system"
mcpi search database --category data
```

#### `mcpi info <server> [OPTIONS]`
Show detailed information about an MCP server.

**Options:**
- `--version TEXT`: Show specific version info
- `--json`: Output in JSON format

**Examples:**
```bash
mcpi info filesystem
mcpi info database --version 2.1.0
```

#### `mcpi categories`
List all available server categories.

### Installation Commands

#### `mcpi install <server> [OPTIONS]`
Install one or more MCP servers.

**Options:**
- `--version TEXT`: Install specific version
- `--config TEXT`: Use configuration template
- `--profile TEXT`: Install to specific profile
- `--dry-run`: Preview installation without executing
- `--force`: Force reinstallation

**Examples:**
```bash
mcpi install filesystem
mcpi install database --config postgres_template
mcpi install github --version 1.2.0 --profile development
```

#### `mcpi uninstall <server> [OPTIONS]`
Remove installed MCP servers.

**Options:**
- `--profile TEXT`: Remove from specific profile
- `--keep-config`: Keep configuration files

**Examples:**
```bash
mcpi uninstall filesystem
mcpi uninstall database --keep-config
```

#### `mcpi update <server> [OPTIONS]`
Update installed MCP servers.

**Options:**
- `--all`: Update all installed servers
- `--version TEXT`: Update to specific version
- `--profile TEXT`: Update in specific profile

**Examples:**
```bash
mcpi update filesystem
mcpi update --all
mcpi update database --version 2.2.0
```

### Configuration Commands

#### `mcpi config init [OPTIONS]`
Initialize mcpi configuration.

**Options:**
- `--profile TEXT`: Initialize specific profile
- `--template TEXT`: Use configuration template

#### `mcpi config profile create <name>`
Create new configuration profile.

#### `mcpi config profile switch <name>`
Switch to different configuration profile.

#### `mcpi config profile list`
List available configuration profiles.

#### `mcpi config validate [OPTIONS]`
Validate current configuration.

**Options:**
- `--profile TEXT`: Validate specific profile
- `--fix`: Attempt to fix validation errors

### Management Commands

#### `mcpi status [OPTIONS]`
Show status of installed MCP servers.

**Options:**
- `--profile TEXT`: Show status for specific profile
- `--json`: Output in JSON format

#### `mcpi doctor [OPTIONS]`
Diagnose installation and configuration issues.

**Options:**
- `--profile TEXT`: Diagnose specific profile
- `--verbose`: Show detailed diagnostic information

#### `mcpi backup [OPTIONS]`
Backup current configuration.

**Options:**
- `--output TEXT`: Backup file path
- `--profile TEXT`: Backup specific profile

#### `mcpi restore <backup_file> [OPTIONS]`
Restore configuration from backup.

**Options:**
- `--profile TEXT`: Restore to specific profile

## Configuration

### Configuration File Location
- **Linux/macOS**: `~/.config/mcpi/config.toml`
- **Windows**: `%APPDATA%/mcpi/config.toml`

### Configuration Structure
```toml
[general]
registry_url = "https://registry.mcpi.dev/v1/servers.json"
auto_update_registry = true
default_profile = "default"

[profiles.default]
target = "claude-code"
config_path = "~/.claude/mcp_servers.json"

[profiles.development]
target = "generic"
config_path = "./mcp_config.json"

[logging]
level = "INFO"
file = "~/.config/mcpi/mcpi.log"
```

### Profile Management
Profiles allow you to maintain different MCP server configurations for different environments or tools.

**Create a new profile:**
```bash
mcpi config profile create production
```

**Switch between profiles:**
```bash
mcpi config profile switch production
```

**Install servers to specific profile:**
```bash
mcpi install filesystem --profile production
```

## MCP Server Registry

The registry contains comprehensive information about available MCP servers, including:

- **Basic Information**: Name, description, author, license
- **Installation Details**: Package manager, dependencies, platforms
- **Configuration**: Required and optional parameters
- **Capabilities**: What the server can do
- **Documentation**: Links to documentation and examples

### Registry Categories
- **Filesystem**: Local and remote file system operations
- **Database**: Database connectivity and operations  
- **API**: REST API and web service integrations
- **Development**: Development tools and utilities
- **Media**: Image, video, and audio processing
- **Data**: Data processing and transformation
- **AI/ML**: Machine learning and AI service integrations

## Integration with Claude Code

mcpi provides seamless integration with Claude Code:

**Automatic Detection**: mcpi automatically detects Claude Code installations and configures MCP servers appropriately.

**Configuration Management**: Updates Claude Code's `mcp_servers.json` configuration file directly.

**Validation**: Ensures configurations are compatible with Claude Code's requirements.

**Example Claude Code Integration:**
```bash
# Install filesystem server for Claude Code
mcpi install filesystem

# This automatically updates ~/.claude/mcp_servers.json:
# {
#   "mcpServers": {
#     "filesystem": {
#       "command": "npx",
#       "args": ["@anthropic/mcp-server-filesystem", "/Users/username/allowed-directory"]
#     }
#   }
# }
```

## Supported MCP Servers

### Core Servers (Anthropic)
- **filesystem**: Local filesystem operations
- **sqlite**: SQLite database operations
- **git**: Git repository management
- **brave-search**: Web search via Brave Search API
- **slack**: Slack workspace integration

### Community Servers
- **github**: GitHub repository and API integration
- **postgres**: PostgreSQL database operations
- **redis**: Redis data structure operations
- **docker**: Docker container management
- **kubernetes**: Kubernetes cluster operations

### API Integration Servers
- **openai**: OpenAI API integration
- **anthropic**: Anthropic API integration
- **google-drive**: Google Drive file operations
- **aws-s3**: Amazon S3 bucket operations
- **notion**: Notion workspace integration

*Full registry available at: `mcpi list`*

## Development

### Project Structure
```
mcpi/
├── src/mcpi/           # Source code
├── data/               # Registry data and templates
├── tests/              # Test suite
├── docs/               # Documentation
└── scripts/            # Development scripts
```

### Development Setup
```bash
git clone https://github.com/user/mcpi
cd mcpi
uv sync --dev
source .venv/bin/activate
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcpi

# Run specific test file
pytest tests/test_registry.py
```

### Code Quality
```bash
# Format code
black src/
ruff check src/ --fix

# Type checking
mypy src/
```

## Contributing

### Contributing to the Registry
To add a new MCP server to the registry:

1. Fork the repository
2. Add server details to `data/registry.json`
3. Include configuration template in `data/templates/`
4. Add tests for the new server
5. Submit a pull request

### Server Entry Format
```json
{
  "id": "your-server",
  "name": "Your MCP Server",
  "description": "Brief description of functionality",
  "category": ["category1", "category2"],
  "author": "Your Name",
  "repository": "https://github.com/user/repo",
  "documentation": "https://docs.yourserver.com",
  "versions": {
    "latest": "1.0.0",
    "supported": ["1.0.0"]
  },
  "installation": {
    "method": "npm|pip|git|binary",
    "package": "package-name",
    "system_dependencies": [],
    "python_dependencies": []
  },
  "configuration": {
    "template": "template_name.json",
    "required_params": ["param1"],
    "optional_params": ["param2"]
  },
  "capabilities": ["capability1", "capability2"],
  "platforms": ["linux", "darwin", "windows"],
  "license": "MIT"
}
```

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive tests
- Update documentation for new features
- Use semantic versioning

## Troubleshooting

### Common Issues

**Installation fails with permission errors:**
```bash
# Try installing with user flag
pip install --user mcpi

# Or use uv which manages virtual environments automatically
uv add mcpi
```

**MCP server not working after installation:**
```bash
# Validate configuration
mcpi config validate

# Run diagnostic
mcpi doctor

# Check server status
mcpi status
```

**Registry update failures:**
```bash
# Force registry update
mcpi sync --force

# Check network connectivity
mcpi doctor --verbose
```

### Getting Help

- **GitHub Issues**: [Report bugs and request features](https://github.com/user/mcpi/issues)
- **Documentation**: [Full documentation](https://mcpi.dev/docs)
- **Discord**: [Community chat](https://discord.gg/mcpi)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Anthropic](https://anthropic.com) for the Model Context Protocol
- [Claude Code](https://claude.ai/code) integration
- Community contributors to the MCP server registry

---

**Made with ❤️ for the MCP community**
