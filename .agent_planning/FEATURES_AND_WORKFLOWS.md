# MCPI Features and Workflows Documentation

**Created**: 2025-12-03
**Purpose**: Document all expected features and workflows for end-to-end testing

## Overview

MCPI (MCP Server Package Installer) manages MCP server configurations across multiple clients (Claude Code, Cursor, VS Code) using a plugin-based architecture with scope-based configuration.

---

## Core Features

### 1. Server Management

#### 1.1 Add Server (`mcpi add`)
Add an MCP server from the registry to a client configuration.

**Options:**
- `--catalog [official|local]` - Search in specific catalog
- `--client TEXT` - Target client (default: auto-detect)
- `--scope` - Target scope (varies by client)
- `--template TEXT` - Use a configuration template
- `--list-templates` - List available templates for this server
- `--dry-run` - Preview changes without writing

**Workflows:**
1. **Basic Add**: `mcpi add filesystem` - Add server to default scope
2. **Add to Specific Scope**: `mcpi add filesystem --scope project-mcp`
3. **Add from Local Catalog**: `mcpi add my-server --catalog local`
4. **Add with Template**: `mcpi add postgres --template production`
5. **Preview Add**: `mcpi add filesystem --dry-run`

#### 1.2 Remove Server (`mcpi remove`)
Remove an MCP server from client configuration.

**Options:**
- `--client TEXT` - Target client
- `--scope` - Source scope (auto-detected if not specified)
- `--dry-run` - Preview changes

**Workflows:**
1. **Basic Remove**: `mcpi remove filesystem`
2. **Remove from Specific Scope**: `mcpi remove filesystem --scope project-mcp`
3. **Preview Remove**: `mcpi remove filesystem --dry-run`

#### 1.3 Enable Server (`mcpi enable`)
Enable a previously disabled MCP server.

**Options:**
- `--client TEXT` - Target client
- `--dry-run` - Preview changes

**Workflows:**
1. **Enable Server**: `mcpi enable filesystem`
2. **Preview Enable**: `mcpi enable filesystem --dry-run`

#### 1.4 Disable Server (`mcpi disable`)
Disable an enabled MCP server (keeps configuration, just marks as disabled).

**Options:**
- `--client TEXT` - Target client
- `--dry-run` - Preview changes

**Workflows:**
1. **Disable Server**: `mcpi disable filesystem`
2. **Preview Disable**: `mcpi disable filesystem --dry-run`

#### 1.5 Rescope Server (`mcpi rescope`)
Move an MCP server configuration from one scope to another.

**Options:**
- `--to SCOPE` - Destination scope (required)
- `--client TEXT` - Target client
- `--dry-run` - Preview changes

**Workflows:**
1. **Move to User Scope**: `mcpi rescope my-server --to user-mcp`
2. **Move to Project Scope**: `mcpi rescope my-server --to project-mcp`
3. **Preview Rescope**: `mcpi rescope my-server --to user-mcp --dry-run`

---

### 2. Discovery and Information

#### 2.1 List Servers (`mcpi list`)
List MCP servers with optional filtering.

**Options:**
- `--client TEXT` - Filter by client
- `--scope` - Filter by specific scope
- `--state [enabled|disabled|unapproved|not_installed]` - Filter by state
- `-v, --verbose` - Show detailed information

**Workflows:**
1. **List All Servers**: `mcpi list`
2. **List by Scope**: `mcpi list --scope user-mcp`
3. **List Enabled Only**: `mcpi list --state enabled`
4. **List Disabled Only**: `mcpi list --state disabled`
5. **Verbose List**: `mcpi list -v`

#### 2.2 Search Servers (`mcpi search`)
Search for MCP servers in the registry.

**Options:**
- `-q, --query TEXT` - Search query (required)
- `--catalog [official|local]` - Search in specific catalog
- `--limit INTEGER` - Maximum results
- `--json` - JSON output

**Workflows:**
1. **Basic Search**: `mcpi search -q filesystem`
2. **Search Local Catalog**: `mcpi search -q database --catalog local`
3. **Limited Search**: `mcpi search -q git --limit 5`
4. **JSON Output**: `mcpi search -q filesystem --json`

#### 2.3 Server Info (`mcpi info`)
Show detailed information about a server.

**Options:**
- `--catalog [official|local]` - Search in specific catalog
- `--client TEXT` - Target client
- `--plain` - Plain text output
- `--json` - JSON output

**Workflows:**
1. **Server Info**: `mcpi info filesystem`
2. **System Status**: `mcpi info` (no server specified)
3. **Plain Text**: `mcpi info filesystem --plain`
4. **JSON Output**: `mcpi info filesystem --json`

---

### 3. Scope Management

#### 3.1 List Scopes (`mcpi scope list`)
List available configuration scopes.

**Claude Code Scopes (priority order):**
- `project-mcp` (10): `.mcp.json` - Project-level MCP config
- `project-local` (20): `.claude/settings.local.json` - Project local settings
- `user-local` (40): `~/.claude/settings.local.json` - User local settings
- `user-internal` (50): `~/.claude/.claude.json` - Internal user config
- `user-mcp` (60): `~/.mcp.json` - User-level MCP config

**Workflows:**
1. **List Scopes**: `mcpi scope list`

---

### 4. Client Management

#### 4.1 List Clients (`mcpi client list`)
List available MCP clients.

**Workflows:**
1. **List Clients**: `mcpi client list`

#### 4.2 Client Info (`mcpi client info`)
Show detailed information about a client.

**Workflows:**
1. **Client Info**: `mcpi client info claude-code`

#### 4.3 Set Default Client (`mcpi client set-default`)
Set the default client for MCPI operations.

**Workflows:**
1. **Set Default**: `mcpi client set-default claude-code`

---

### 5. Catalog Management

#### 5.1 List Catalogs (`mcpi catalog list`)
List all MCP server catalogs.

**Workflows:**
1. **List Catalogs**: `mcpi catalog list`

#### 5.2 Catalog Info (`mcpi catalog info`)
Show detailed information about a catalog.

**Workflows:**
1. **Official Info**: `mcpi catalog info official`
2. **Local Info**: `mcpi catalog info local`

#### 5.3 Add to Catalog (`mcpi catalog add`)
Add an MCP server to the local catalog using Claude.

**Workflows:**
1. **Add Server**: `mcpi catalog add --source https://github.com/example/mcp-server`

---

### 6. Bundle Management

#### 6.1 Bundle Commands (`mcpi bundle`)
Manage MCP server bundles (grouped installations).

**Subcommands:**
- `list` - List available bundles
- `info BUNDLE` - Show bundle details
- `install BUNDLE` - Install a bundle
- `remove BUNDLE` - Remove a bundle

**Workflows:**
1. **List Bundles**: `mcpi bundle list`
2. **Bundle Info**: `mcpi bundle info development`
3. **Install Bundle**: `mcpi bundle install development`
4. **Remove Bundle**: `mcpi bundle remove development`

---

### 7. Interactive Features

#### 7.1 FZF Browser (`mcpi fzf`)
Interactive fuzzy finder for managing MCP servers.

**Workflows:**
1. **Browse Servers**: `mcpi fzf`

---

### 8. Configuration Templates

Templates provide guided setup for servers with interactive prompts.

**Available Templates:**
- PostgreSQL: `local-development`, `docker`, `production`
- GitHub: `personal-full-access`, `read-only`, `public-repos`
- Filesystem: `project-files`, `user-documents`, `custom-directories`
- Slack: `bot-token`, `limited-channels`
- Brave Search: `api-key`

**Workflows:**
1. **List Templates**: `mcpi add postgres --list-templates`
2. **Use Template**: `mcpi add postgres --template production`

---

## Critical User Workflows to Test

### Workflow 1: First-Time Server Installation
1. User searches for a server: `mcpi search -q filesystem`
2. User views server details: `mcpi info filesystem`
3. User adds server: `mcpi add filesystem`
4. User verifies installation: `mcpi list`

### Workflow 2: Project-Specific Configuration
1. User adds server to project scope: `mcpi add project-tool --scope project-mcp`
2. User verifies project scope: `mcpi list --scope project-mcp`
3. User rescopes if needed: `mcpi rescope project-tool --to user-mcp`

### Workflow 3: Enable/Disable Server Management
1. User lists enabled servers: `mcpi list --state enabled`
2. User disables a server: `mcpi disable filesystem`
3. User verifies disabled: `mcpi list --state disabled`
4. User re-enables: `mcpi enable filesystem`

### Workflow 4: Multi-Scope Management
1. User lists all scopes: `mcpi scope list`
2. User checks servers per scope: `mcpi list --scope user-mcp`
3. User moves server between scopes: `mcpi rescope my-server --to project-mcp`

### Workflow 5: Template-Based Installation
1. User lists templates: `mcpi add postgres --list-templates`
2. User installs with template: `mcpi add postgres --template production`
3. User verifies configuration: `mcpi info postgres`

### Workflow 6: Complete Server Lifecycle
1. Search: `mcpi search -q filesystem`
2. Add: `mcpi add filesystem`
3. Verify: `mcpi list`
4. Disable: `mcpi disable filesystem`
5. Re-enable: `mcpi enable filesystem`
6. Remove: `mcpi remove filesystem`
7. Verify removal: `mcpi list`

---

## File Locations (Claude Code)

| Scope | File Path | Format |
|-------|-----------|--------|
| project-mcp | `.mcp.json` | `{"mcpServers": {...}}` |
| project-local | `.claude/settings.local.json` | `{"mcpServers": {...}}` |
| user-local | `~/.claude/settings.local.json` | `{"mcpServers": {...}}` |
| user-internal | `~/.claude/.claude.json` | `{"mcpServers": {...}}` |
| user-mcp | `~/.mcp.json` | `{"mcpServers": {...}}` |

---

## Test Coverage Requirements

Each workflow above should have:
1. **Happy path test** - Normal operation succeeds
2. **Error handling test** - Invalid inputs handled gracefully
3. **Dry-run verification** - Preview mode works correctly
4. **File isolation** - All tests use temporary files only
5. **State verification** - Final state matches expectations
