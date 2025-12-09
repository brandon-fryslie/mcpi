# MCP Client Support Roadmap

Research compiled December 2025.

## Overview

This document tracks MCP (Model Context Protocol) clients that MCPI should support. Clients are prioritized by user base, MCP maturity, and strategic importance.

---

## Tier 1 - High Priority

Essential clients with large user bases and mature MCP implementations.

### 1. Claude Code (CLI) ✅ IMPLEMENTED
- **Type**: CLI terminal agent
- **Developer**: Anthropic
- **Config Location**: Multiple scopes (project `.mcp.json`, user `~/.claude/settings.json`, etc.)
- **Status**: Full support implemented
- **Notes**: Primary development target, 6 scope hierarchy

### 2. Claude Desktop ✅ IMPLEMENTED
- **Type**: Desktop application
- **Developer**: Anthropic
- **Config Location**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- **Config Format**: JSON with `mcpServers` object
- **Status**: Full support implemented (commit aa2e4ab)
- **Priority**: HIGH - Anthropic's flagship consumer product
- **Complexity**: Low - simple single-file config
- **Notes**: Single "user" scope, 43 comprehensive tests
- **Sources**: [Anthropic announcement](https://www.anthropic.com/news/model-context-protocol)

### 3. Cursor ✅ IMPLEMENTED
- **Type**: IDE (VS Code fork)
- **Developer**: Cursor Inc.
- **Config Location**: `~/.cursor/mcp.json` or project `.cursor/mcp.json`
- **Config Format**: JSON with `mcpServers` object
- **Transport**: Supports SSE protocol (easier remote MCP setup)
- **Status**: Full support implemented (commit fe2b455)
- **Priority**: HIGH - Extremely popular AI coding IDE
- **Complexity**: Low-Medium
- **Notes**: 2-scope model (user + project), 45 comprehensive tests
- **Sources**: [DataCamp Top MCP Clients](https://www.datacamp.com/blog/top-mcp-servers-and-clients)

### 4. VS Code (GitHub Copilot) ✅ IMPLEMENTED
- **Type**: IDE extension
- **Developer**: Microsoft
- **Config Location**:
  - User: Platform-specific (~/Library/Application Support/Code/User/mcp.json on macOS)
  - Workspace: `.vscode/mcp.json`
- **Config Format**: JSON with `"servers"` object (NOT "mcpServers")
- **Status**: Full support implemented (commit 56f578e)
- **Priority**: HIGH - Largest IDE user base, native MCP in VS Code 1.101+
- **Complexity**: Medium - 2-scope model, different JSON key
- **Notes**: CRITICAL - Uses "servers" key instead of "mcpServers". Required FileBasedScope enhancement.
- **Test Coverage**: 45 comprehensive tests
- **Sources**: [VS Code MCP Docs](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)

### 5. Windsurf ✅ IMPLEMENTED
- **Type**: IDE
- **Developer**: Codeium
- **Config Location**: `~/.codeium/windsurf/mcp_config.json` (all platforms)
- **Config Format**: JSON with `mcpServers` object
- **Status**: Full support implemented (commit ace05f8)
- **Priority**: HIGH - Popular alternative to Cursor
- **Complexity**: Low - single-scope model, same path on all platforms
- **Notes**: Single "user" scope, 44 comprehensive tests
- **Sources**: [Windsurf](https://windsurf.com/)

---

## Tier 2 - Medium Priority

Significant user bases, active development, strong MCP support.

### 6. Cline ✅ IMPLEMENTED
- **Type**: VS Code extension
- **Developer**: Open source (Saoud Rizwan)
- **Config Location**: VS Code extension globalStorage
  - macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
  - Windows: `%APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
  - Linux: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Config Format**: JSON with `mcpServers`
- **Transport**: Supports Streamable HTTP and SSE
- **User Base**: 4M+ developers, 30k GitHub stars
- **Status**: Full support implemented (commit ca32c2a)
- **Priority**: MEDIUM-HIGH
- **Complexity**: Low - single-scope model with InlineEnableDisableHandler
- **Notes**: Single "user" scope, 46 comprehensive tests, first client using InlineEnableDisableHandler pattern
- **Sources**: [Cline](https://cline.bot/), [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)

### 7. Roo Code ✅ IMPLEMENTED
- **Type**: VS Code extension (Cline fork)
- **Developer**: Roo Code Inc.
- **Config Location**:
  - User: VS Code globalStorage (`rooveterinaryinc.roo-cline/settings/mcp_settings.json`)
  - Project: `.roo/mcp.json`
- **Config Format**: JSON with `mcpServers` object
- **User Base**: 750k VS Code installs, 18k GitHub stars
- **Status**: Full support implemented (commit e52632f)
- **Priority**: MEDIUM
- **Complexity**: Low - 2-scope model with InlineEnableDisableHandler
- **Notes**: Combines Cline's inline disable pattern with 2-scope model, 57 comprehensive tests
- **Sources**: [Roo Code Docs](https://docs.roocode.com/features/mcp/using-mcp-in-roo), [GitHub](https://github.com/RooCodeInc/Roo-Code)

### 8. Zed
- **Type**: Native code editor
- **Developer**: Zed Industries
- **Config Location**: Zed settings or extensions
- **Config Format**: Custom (settings file with `context_servers` section)
- **Status**: 🔴 Not implemented
- **Priority**: MEDIUM
- **Complexity**: Medium - different config format, extension system
- **Notes**: Collaborated with Anthropic on MCP, supports ACP (Agent Client Protocol)
- **Sources**: [Zed MCP Docs](https://zed.dev/docs/ai/mcp), [Zed Blog](https://zed.dev/blog/mcp)

### 9. OpenAI Codex CLI
- **Type**: CLI terminal agent
- **Developer**: OpenAI
- **Config Location**: `~/.codex/config.toml`
- **Config Format**: TOML with `[mcp_servers.<name>]` tables
- **Transport**: STDIO and OAuth (with RMCP feature flag)
- **Status**: 🔴 Not implemented
- **Priority**: MEDIUM
- **Complexity**: Low - TOML format, similar structure to mcpi.toml
- **Notes**: Can also run AS an MCP server for other clients
- **Sources**: [OpenAI Codex MCP Docs](https://developers.openai.com/codex/mcp/), [GitHub](https://github.com/openai/codex)

### 10. Continue
- **Type**: IDE extension (VS Code + JetBrains)
- **Developer**: Open source
- **Config Location**: Assistant configuration with `mcpServers` blocks
- **Status**: 🔴 Not implemented
- **Priority**: MEDIUM
- **Complexity**: Medium - dual IDE support
- **Sources**: [DataCamp](https://www.datacamp.com/blog/top-mcp-servers-and-clients)

---

## Tier 3 - Lower Priority

Notable clients with smaller or specialized user bases.

### 11. Goose
- **Type**: CLI + Desktop agent
- **Developer**: Block (Square)
- **Config Format**: Custom configuration
- **Status**: 🔴 Not implemented
- **Priority**: LOW-MEDIUM
- **Notes**: Block has 60+ internal MCP servers, very active in MCP ecosystem
- **Sources**: [Goose](https://block.github.io/goose/), [GitHub](https://github.com/block/goose)

### 12. JetBrains IDEs
- **Type**: IDE family (IntelliJ, PyCharm, WebStorm, etc.)
- **Developer**: JetBrains
- **Status**: 🔴 Not implemented
- **Priority**: LOW-MEDIUM
- **Complexity**: High - multiple IDEs, plugin system
- **Notes**: JetBrains MCP Server exists for IDE automation

### 13. Cherry Studio
- **Type**: Desktop client
- **Developer**: Open source
- **Config Format**: JSON
- **Status**: 🔴 Not implemented
- **Priority**: LOW
- **Notes**: Multi-LLM desktop client

### 14. LibreChat
- **Type**: Web application (self-hosted)
- **Developer**: Open source
- **Config Format**: JSON with `mcpServers`
- **Status**: 🔴 Not implemented
- **Priority**: LOW
- **Notes**: ChatGPT alternative, supports many providers

### 15. NextChat
- **Type**: Cross-platform client
- **Developer**: Open source
- **Status**: 🔴 Not implemented
- **Priority**: LOW

---

## Implementation Strategy

### Phase 1: Anthropic Ecosystem ✅ COMPLETE
1. ✅ Claude Code (complete)
2. ✅ Claude Desktop (complete - commit aa2e4ab)

### Phase 2: Popular IDEs ✅ COMPLETE
3. ✅ Cursor (complete - commit fe2b455)
4. ✅ VS Code/Copilot (complete - commit 56f578e)
5. ✅ Windsurf (complete - commit ace05f8)

### Phase 3: VS Code Extensions ✅ COMPLETE
6. ✅ Cline (complete - commit ca32c2a)
7. ✅ Roo Code (complete - commit e52632f)

### Phase 4: Alternative Editors & CLIs
8. Zed (native MCP support, modern editor)
9. OpenAI Codex (TOML config, CLI-native)
10. Continue (dual IDE support)

### Phase 5: Specialized Clients
11. Goose, JetBrains, others as demand warrants

---

## Config Format Summary

| Client | Format | Location | Complexity |
|--------|--------|----------|------------|
| Claude Code | JSON | Multiple scopes | Medium |
| Claude Desktop | JSON | App support dir | Low |
| Cursor | JSON | `.cursor/` | Low |
| VS Code | JSON | `.vscode/` | Medium |
| Windsurf | JSON | Settings | Medium |
| Cline | JSON | Extension config | Low |
| Roo Code | JSON | `.roo/` + global | Low |
| Zed | Custom | Settings | Medium |
| Codex | TOML | `~/.codex/` | Low |

---

## References

- [Anthropic MCP Announcement](https://www.anthropic.com/news/model-context-protocol)
- [DataCamp: Top MCP Servers & Clients](https://www.datacamp.com/blog/top-mcp-servers-and-clients)
- [KDnuggets: Top 7 MCP Clients](https://www.kdnuggets.com/top-7-mcp-clients-for-ai-tooling)
- [VS Code MCP Documentation](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [Zed MCP Documentation](https://zed.dev/docs/ai/mcp)
- [OpenAI Codex MCP](https://developers.openai.com/codex/mcp/)
- [Cline](https://cline.bot/)
- [Roo Code Documentation](https://docs.roocode.com/features/mcp/using-mcp-in-roo)
- [Goose by Block](https://block.github.io/goose/)
