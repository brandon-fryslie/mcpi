# MCP Manager (mcpi)

[![Test](https://github.com/user/mcpi/actions/workflows/test.yml/badge.svg)](https://github.com/user/mcpi/actions/workflows/test.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line tool for managing Model Context Protocol (MCP) servers across different MCP-compatible clients. Discover, install, and configure MCP servers for Claude Code and other compatible tools with ease.

## Features

- **Comprehensive Registry**: Catalog of known MCP servers with metadata
- **Scope-Based Configuration**: Manage servers across multiple configuration scopes (project-level, user-level)
- **Multi-Client Support**: Works with Claude Code, Cursor, VS Code, and other MCP clients
- **CLI Interface**: Intuitive command-line interface with shell tab completion
- **Plugin Architecture**: Extensible client plugin system for supporting new MCP clients

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

**Note for macOS iCloud Drive users**: If your project is in iCloud Drive, use `.venv.nosync` to avoid intermittent import issues. See [Troubleshooting](#troubleshooting) for details.

## Quick Start

### Discover MCP Servers
```bash
# Search for specific functionality
mcpi search filesystem

# Get detailed information about a server (shows registry + install status)
mcpi info filesystem
```

### Manage Installed Servers
```bash
# List currently installed servers
mcpi list

# List servers in a specific scope
mcpi list --scope user-global

# List servers for a specific client
mcpi list --client claude-code

# Add a server (interactive scope selection)
mcpi add filesystem

# Add a server to a specific scope
mcpi add filesystem --scope project-mcp

# Remove a server
mcpi remove filesystem

# Check system status
mcpi status
```

### Scope Management
```bash
# List available scopes for the default client
mcpi scope list

# List scopes for a specific client
mcpi scope list --client claude-code

# Consolidate a server to a specific scope (removes from all other scopes)
mcpi rescope filesystem --to user-global
```

### Client Management
```bash
# List detected MCP clients
mcpi client list

# Get information about a specific client
mcpi client info claude-code

# Set the default client
mcpi client set-default claude-code
```

### Shell Tab Completion
```bash
# Enable tab completion for bash
mcpi completion --shell bash

# Enable tab completion for zsh
mcpi completion --shell zsh

# Enable tab completion for fish
mcpi completion --shell fish
```

## Architecture

MCPI uses a **scope-based configuration system** with a **plugin architecture** for supporting multiple MCP clients.

### Scope-Based Configuration

Instead of traditional profile-based configuration, mcpi uses **scopes** which are hierarchical configuration levels with different priorities. Each MCP client defines its own scopes.

#### Example Scopes (Claude Code)

| Scope Name | Type | Priority | Description |
|------------|------|----------|-------------|
| `project-mcp` | Project | 10 | Project-level `.mcp.json` (highest priority) |
| `project-local` | Project | 20 | Project-local `.claude/settings.local.json` |
| `project-internal` | Project | 30 | Project-internal `.claude/settings.json` |
| `user-internal` | User | 40 | User-internal `~/.claude/settings.json` |
| `user-global` | User | 50 | User-global `~/.config/claude/settings.json` |
| `user-local` | User | 60 | User-local `~/.claude/settings.local.json` (lowest priority) |

**Priority System**: Lower priority numbers override higher priority numbers. Project-level scopes override user-level scopes.

### Plugin Architecture

Each MCP client (Claude Code, Cursor, VS Code) is implemented as a **plugin** that conforms to the `MCPClientPlugin` protocol:

- **Client Detection**: Automatically detects installed clients
- **Scope Handlers**: Each scope is managed by a handler that knows how to read/write that specific configuration file
- **Schema Validation**: Configuration changes are validated against client-specific schemas
- **Extensible**: Easy to add support for new MCP clients

## CLI Commands

### Discovery Commands

#### `mcpi search <query>`
Search for servers by name or description in the registry.

```bash
mcpi search filesystem
mcpi search "database operations"
```

#### `mcpi info <server-id>`
Show detailed information about a server, including registry info and local installation status.

```bash
mcpi info filesystem
mcpi info brave-search
```

### Interactive Interface

#### `mcpi fzf`
Launch an interactive fuzzy finder interface for managing MCP servers.

**Features:**
- Browse all servers from the registry with fuzzy search
- Installed servers shown at top (green=enabled, yellow=disabled)
- Real-time status updates after operations
- Preview pane shows server details

**Keyboard Shortcuts:**
- `ctrl-a`: Add server to configuration
- `ctrl-r`: Remove server from configuration
- `ctrl-e`: Enable server
- `ctrl-d`: Disable server
- `ctrl-i` / `enter`: Show detailed info
- `esc` / `ctrl-c`: Exit

**Requirements:**
- Requires `fzf` to be installed (`brew install fzf` on macOS, `apt install fzf` on Ubuntu)

**Example:**
```bash
# Launch interactive interface
mcpi fzf
```

### Server Management Commands

#### `mcpi list [OPTIONS]`
List installed MCP servers.

**Options:**
- `--client TEXT`: Filter by client (uses default if not specified)
- `--scope TEXT`: Filter by scope (available scopes depend on client)
- `--state TEXT`: Filter by state (enabled, disabled, not_installed)
- `--verbose, -v`: Show detailed information

**Examples:**
```bash
# List all installed servers
mcpi list

# List servers in a specific scope
mcpi list --scope user-global

# List servers for a specific client
mcpi list --client claude-code

# List only enabled servers
mcpi list --state enabled

# Show detailed information
mcpi list --verbose
```

#### `mcpi add <server-id> [OPTIONS]`
Add an MCP server from the registry.

**Options:**
- `--client TEXT`: Target client (uses default if not specified)
- `--scope TEXT`: Target scope (interactive selection if not specified)
- `--dry-run`: Show what would be done without making changes

**Examples:**
```bash
# Add a server (interactive scope selection)
mcpi add filesystem

# Add to a specific scope
mcpi add filesystem --scope project-mcp

# Preview without making changes
mcpi add filesystem --dry-run
```

#### `mcpi remove <server-id> [OPTIONS]`
Remove an MCP server.

**Options:**
- `--client TEXT`: Target client (uses default if not specified)
- `--scope TEXT`: Source scope (auto-detected if not specified)
- `--dry-run`: Show what would be done without making changes

**Examples:**
```bash
# Remove a server (prompts for confirmation)
mcpi remove filesystem

# Remove from a specific scope
mcpi remove filesystem --scope project-mcp
```

#### `mcpi enable <server-id> [OPTIONS]`
Enable a disabled MCP server.

**Options:**
- `--client TEXT`: Target client (uses default if not specified)
- `--dry-run`: Show what would be done without making changes

**Examples:**
```bash
mcpi enable filesystem
```

#### `mcpi disable <server-id> [OPTIONS]`
Disable an enabled MCP server.

**Options:**
- `--client TEXT`: Target client (uses default if not specified)
- `--dry-run`: Show what would be done without making changes

**Examples:**
```bash
mcpi disable filesystem
```

#### `mcpi rescope <server-name> --to <scope> [OPTIONS]`
Consolidate an MCP server configuration to a specific scope, automatically removing it from all other scopes.

**Options:**
- `--to TEXT`: Target scope (required)
- `--client TEXT`: MCP client to use (auto-detected if not specified)
- `--dry-run`: Show what would happen without making changes

**Examples:**
```bash
# Consolidate server to user-global scope (removes from all other scopes)
mcpi rescope filesystem --to user-global

# Preview the operation
mcpi rescope filesystem --to user-global --dry-run

# Specify a client explicitly
mcpi rescope filesystem --to user-global --client claude-code
```

**How it works:**
1. Automatically detects ALL scopes where the server is currently configured
2. Adds the server to the target scope (preserving existing config if already present)
3. Removes the server from all other scopes
4. Operation is atomic: adds to target first, then removes from sources (prevents data loss)

**Notes:**
- **Idempotent**: Safe to run multiple times - consolidates to target scope regardless of current state
- **Automatic detection**: No need to specify source scope(s) - automatically finds them all
- **Safety**: If server already in target scope, preserves target config and cleans up other scopes
- **Multi-scope cleanup**: If server scattered across multiple scopes, consolidates to single target scope

#### `mcpi info [server-id] [OPTIONS]`
Show detailed information about a server or system status.

**Options:**
- `--client TEXT`: Target client (uses default if not specified)

**Examples:**
```bash
# Show system status
mcpi info

# Show server information
mcpi info filesystem
```

### Scope Management Commands

#### `mcpi scope list [OPTIONS]`
List available configuration scopes.

**Options:**
- `--client TEXT`: Filter by client (uses default if not specified)

**Examples:**
```bash
# List scopes for default client
mcpi scope list

# List scopes for a specific client
mcpi scope list --client claude-code
```

### Client Management Commands

#### `mcpi client list`
List available MCP clients.

```bash
mcpi client list
```

#### `mcpi client info [client-name]`
Show detailed information about a client.

```bash
# Show default client info
mcpi client info

# Show specific client info
mcpi client info claude-code
```

#### `mcpi client set-default <client-name>`
Set the default client for MCPI operations.

```bash
mcpi client set-default claude-code
```

### System Commands

#### `mcpi status`
Show system status and summary information.

```bash
mcpi status
```

#### `mcpi completion --shell <shell>`
Generate shell completion script for mcpi.

**Tab completion provides intelligent suggestions for:**
- Command names (list, add, remove, etc.)
- Option flags (--client, --scope, --help)
- Client names (based on detected MCP clients)
- Scope names (filtered by selected client)
- Server IDs (from the registry)

**Options:**
- `--shell TEXT`: Shell type (bash, zsh, fish) - auto-detects if not specified

**Examples:**
```bash
# Auto-detect shell and show instructions
mcpi completion

# Generate bash completion
mcpi completion --shell bash

# Generate zsh completion
mcpi completion --shell zsh

# Generate fish completion
mcpi completion --shell fish
```

**Installation:**

For **bash**, add to `~/.bashrc`:
```bash
eval "$(_MCPI_COMPLETE=bash_source mcpi)"
```

For **zsh**, add to `~/.zshrc`:
```bash
eval "$(_MCPI_COMPLETE=zsh_source mcpi)"
```

For **fish**, add to `~/.config/fish/config.fish`:
```bash
eval (env _MCPI_COMPLETE=fish_source mcpi)
```

## MCP Server Registry

The registry contains information about available MCP servers, including:

- **Basic Information**: Name, description, repository
- **Installation Details**: Command and arguments needed to run the server
- **Categories**: Classification for easy discovery (when populated)

### Registry Format

The registry is stored in `data/registry.json` with the following structure:

```json
{
  "server-id": {
    "description": "Brief description of server functionality",
    "command": "npx",
    "args": ["-y", "@package/mcp-server"],
    "repository": "https://github.com/org/repo",
    "categories": ["category1", "category2"]
  }
}
```

### Adding Servers to Registry

To add a new MCP server to the registry:

1. Edit `data/registry.json`
2. Add a new entry with the server details
3. Ensure the command and args are correct
4. Optionally add categories for classification
5. Submit a pull request

## Supported MCP Servers

### Core Servers (Anthropic)
- **filesystem**: Local filesystem operations
- **sqlite**: SQLite database operations
- **brave-search**: Web search via Brave Search API
- **fetch**: Make HTTP requests and fetch web content
- **github**: Interact with GitHub repositories, issues, and pull requests

### Community Servers
The registry contains additional community-contributed servers. Use `mcpi search` to find available servers.

## Integration with Claude Code

mcpi provides seamless integration with Claude Code:

**Automatic Detection**: mcpi automatically detects Claude Code installations and configures MCP servers appropriately.

**Multiple Configuration Scopes**: Claude Code supports 6 different configuration scopes, from project-level to user-level.

**Configuration Management**: Updates Claude Code's configuration files directly with proper validation.

**Example Claude Code Integration:**
```bash
# Add filesystem server to project scope
mcpi add filesystem --scope project-mcp

# This updates .mcp.json in your project:
# {
#   "mcpServers": {
#     "filesystem": {
#       "command": "npx",
#       "args": ["-y", "@anthropic/mcp-server-filesystem"]
#     }
#   }
# }
```

## Development

### Project Structure
```
mcpi/
├── src/mcpi/              # Source code
│   ├── cli.py            # CLI interface
│   ├── clients/          # Client plugins
│   │   ├── base.py       # Base protocols and types
│   │   ├── manager.py    # MCPManager orchestration
│   │   ├── claude_code.py # Claude Code plugin
│   │   └── file_based.py # File-based scope implementations
│   └── registry/         # Server registry
│       └── catalog.py    # Server catalog and models
├── data/                 # Registry data
│   └── registry.json     # Server definitions
└── tests/                # Test suite
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
pytest --cov=src/mcpi

# Run specific test file
pytest tests/test_registry_categories.py

# Validate registry data
pytest tests/test_registry_integration.py -v
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type checking
mypy src/
```

## Contributing

### Contributing to the Registry
To add a new MCP server to the registry:

1. Fork the repository
2. Add server details to `data/registry.json`
3. Test the server entry: `mcpi info <your-server-id>`
4. Submit a pull request

### Server Entry Format
```json
{
  "your-server-id": {
    "description": "Brief description of functionality",
    "command": "npx",
    "args": ["-y", "@package/your-mcp-server"],
    "repository": "https://github.com/user/repo",
    "categories": ["category1", "category2"]
  }
}
```

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write tests for new features
- Update documentation for new features
- Use semantic versioning

## Troubleshooting

### Common Issues

**Server not showing up after adding:**
```bash
# Check if server was added successfully
mcpi list --verbose

# Check specific scope
mcpi list --scope project-mcp
```

**Cannot find default client:**
```bash
# List available clients
mcpi client list

# Set default client manually
mcpi client set-default claude-code
```

**Scope not found:**
```bash
# List available scopes
mcpi scope list

# Check scope existence in current directory
mcpi scope list --client claude-code
```

**Tab completion not working:**
```bash
# Re-run the completion setup
mcpi completion --shell bash

# Make sure to source your shell config
source ~/.bashrc  # or ~/.zshrc for zsh
```

**ImportError in development (macOS iCloud Drive):**

If developing in iCloud Drive, you may encounter intermittent `ModuleNotFoundError: No module named 'mcpi'` due to iCloud setting hidden flags on `.pth` files.

**Solution 1: Use .venv.nosync (Recommended for Development)**
```bash
cd ~/path/to/mcpi

# Remove existing venv
rm -rf .venv

# Create .venv.nosync (excluded from iCloud sync)
python -m venv .venv.nosync
ln -s .venv.nosync .venv

# Install in editable mode
source .venv/bin/activate
pip install -e .
```

The `.nosync` suffix tells iCloud to exclude the directory from sync, preventing hidden flag issues.

**Solution 2: Use UV Tool Install (Recommended for CLI Usage)**
```bash
# Install as UV tool (stored in ~/.local/, not in iCloud)
uv tool install --editable ~/path/to/mcpi

# Use from anywhere without venv activation
mcpi --help

# For testing
cd ~/path/to/mcpi
pytest  # Uses pythonpath from pyproject.toml
```

**Emergency fix (temporary):**
```bash
# Remove hidden flags manually
./scripts/fix-pth-flags.sh

# Or manually:
cd ~/path/to/mcpi
chflags nohidden .venv/lib/python3.*/site-packages/*.pth
```

See `.agent_planning/ICLOUD-COMPATIBLE-FIX-2025-10-30.md` for technical details.

### Getting Help

- **GitHub Issues**: [Report bugs and request features](https://github.com/user/mcpi/issues)
- **Documentation**: See CLAUDE.md in the repository for development documentation

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Anthropic](https://anthropic.com) for the Model Context Protocol
- [Claude Code](https://claude.ai/code) integration
- Community contributors to the MCP server registry

---

**Note**: This tool manages MCP server configurations. It does not install the underlying npm/pip packages - those are installed automatically when the MCP client (like Claude Code) first uses the server.
