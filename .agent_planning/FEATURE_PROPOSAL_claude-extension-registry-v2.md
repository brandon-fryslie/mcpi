# Feature Proposal: MCPI Extension Registry - Plugin-Based Extension Management

**Date**: 2025-11-27
**Version**: 2.1
**Status**: Proposal
**Target Release**: v3.0

---

## Executive Summary

Transform MCPI into a **uv-style package manager for Claude Code plugin extensions** with a focus on rapid context switching through declarative extension sets.

**Core Innovation**: Extension Sets - declarative profiles that let users switch their entire Claude configuration in seconds:

```bash
# Morning: Web frontend development
mcpi extension-set activate frontend

# Afternoon: iOS bug investigation
mcpi extension-set activate ios-debug

# Multiple Claude instances with different configs
mcpi launch --extension-set python-ml
mcpi launch --extension-set golang-microservices
```

**Why This Matters**: Developers context-switch constantly. Each context needs different tools. Manual reconfiguration takes 10-15 minutes. Extension sets make it instant.

---

## Problem Statement

### Current Pain Points

**1. Plugin Extensions Are Invisible**

Users install plugins like `beads@beads-marketplace` or `dev-loop@loom99`, but:
- Can't see what individual extensions (commands, agents, skills) the plugin provides
- Can't selectively enable/disable parts of a plugin
- Can't cherry-pick commands from multiple plugins into a cohesive workflow
- Have no searchable index of "What commands are available across all my plugins?"

**2. Context Switching Is Manual and Slow**

A developer's day involves multiple contexts:
- Morning: React frontend work (needs: prettier, eslint, react-devtools commands)
- Afternoon: Python backend (needs: pytest, mypy, postgres commands)
- Evening: iOS app (needs: xcode-build, swift-format commands)

Currently they must:
- Manually edit .claude/settings.json
- Add/remove commands from .claude/commands/
- Enable/disable plugins
- Restart Claude instances
- **Total time: 10-15 minutes per switch**

**3. Extension Discovery Is Plugin-Scoped**

Users discover plugins, not extensions. Questions like:
- "Which plugin has a good git commit message generator?"
- "What test runner commands are available across all plugins?"
- "Give me ALL database-related extensions from all plugins"

...are impossible to answer without manual inspection of every plugin.

**4. No Way to Browse Available Extensions**

Users can only see what's already installed. There's no way to:
- Browse available extensions from known marketplaces
- Discover plugins you don't have yet
- Compare similar extensions across plugins

---

## Proposed Solution

### Vision Statement

MCPI becomes the **universal index and manager for plugin-sourced Claude extensions** with four core capabilities:

1. **Extension Index**: Hierarchical index of Marketplaces → Plugins → Individual Extensions
2. **Browse Available**: Discover extensions from known marketplaces (not just installed plugins)
3. **Extension Selection**: Cherry-pick any extension from any plugin
4. **Extension Sets**: Declarative profiles for instant configuration switching

### Key Constraint: Plugin-Only Indexing

We ONLY index extensions that come from Claude Code plugins. Plugins have:
- Structured metadata (plugin.json)
- Known distribution points (marketplaces)
- Proper versioning and maintenance
- Clear ownership and security model

This constraint dramatically simplifies discovery, security, and maintenance while focusing on the highest-quality extensions.

### High-Level Architecture

```
Marketplaces (Discovery Points)
└── Plugins (Structured Packages)
    └── Extensions (Individual Units)
        ├── Commands (slash commands)
        ├── Agents (AI agents)
        ├── Skills (reusable capabilities)
        ├── Hooks (event automation)
        └── MCP Servers (tool integrations)
```

**Central Installation** (uv-style): Extensions are installed to a central location (`~/.mcpi/extensions/`) and symlinked into projects when activated.

**Extension Sets**: Declarative YAML files that specify which extensions to activate. Simple flat lists - no inheritance, no extends, no complexity.

---

## Core Features

### 1. Extension Index

**What**: A searchable index of all extensions from installed plugins AND known marketplaces.

**User Experience**:
```bash
# Search across all indexed extensions
mcpi search pytest
mcpi search --type command database

# Show extension details
mcpi info beads:list

# List all extensions
mcpi list-extensions --type command
```

**Requirements**:
- Index must support schema migrations for safe evolution over time
- Search must return results in <100ms
- Index both installed plugins AND available (not-yet-installed) plugins from known marketplaces

### 2. Browse Available Extensions

**What**: Discover extensions from known marketplaces without installing them first.

**User Experience**:
```bash
# Browse all available extensions (installed + available)
mcpi browse

# Browse specific marketplace
mcpi browse --marketplace beads-marketplace

# Show details for an available extension
mcpi info pytest:run --available

# Install an extension (and its plugin if needed)
mcpi install pytest:run
```

**Requirements**:
- Must work offline for installed plugins
- Online browsing should be optional and fast
- Design this subsystem to be relatively independent - it may become its own project later
- Must be forward-compatible with however marketplace discovery evolves

### 3. Extension Sets

**What**: Declarative YAML profiles that define a collection of extensions to activate together.

**User Experience**:
```bash
# Create a new extension set
mcpi extension-set create python-tdd

# Activate a set
mcpi extension-set activate python-tdd

# Launch Claude with a specific set
mcpi launch --extension-set python-tdd

# List available sets
mcpi extension-set list
```

**Extension Set Format**:
```yaml
# Must include version for format evolution
format_version: 1

name: python-tdd
description: Python test-driven development workflow

# Simple flat list - no extends, no inheritance
extensions:
  - beads:create
  - beads:list
  - dev-loop:test-and-implement
  - pytest:run
  - mypy:check

mcp_servers:
  - beads:beads
  - postgres:local

hooks:
  - python-tools:format-on-save
```

**Requirements**:
- Extension set YAML format must be versioned for forward compatibility
- No inheritance/extends - keep it simple, focus on ergonomic management instead
- Sets are flat lists that are easy to create, edit, and share

### 4. Managed Configuration

**What**: When MCPI manages extensions for a project, it fully manages `.mcp.json`, hooks, etc.

**Design Constraints**:
- When using extension sets, MCPI owns the configuration completely
- Multiple approaches may work (wrapper launcher, symlink swapping, CLI arguments)
- Implementation should be flexible enough to iterate until we find the right solution
- Claude reads config on startup, so temporary configuration during launch may be sufficient

**Possible Approaches** (to be explored during implementation):
- Wrapper that sets up config before launching Claude
- Temporary config swapping during Claude startup
- Using Claude's CLI arguments for config location
- Full management mode where manual .mcp.json editing is not allowed

---

## Technical Constraints

### Symlinks Only

Extension activation uses symlinks. Period.
- No fallback to copying files
- No alternative mechanisms
- If symlinks don't work on a system, that system is not supported

### Plugin-Only Sources

We only index extensions from:
- Installed Claude Code plugins
- Known marketplaces (for browse/discovery)

No arbitrary git repos, no user-contributed extension files, no unstructured sources.

---

## Success Metrics

### Must Have (v3.0 Release)
- Index 100% of installed plugins
- Index 100% of extensions in indexed plugins
- Search returns results in <100ms
- Extension set activation completes in <5 seconds
- Zero data loss during activation/deactivation
- Works on macOS, Linux
- Browse available extensions from at least 2 known marketplaces

### Nice to Have
- Index updates incrementally
- Extension set templates for common workflows
- Community sharing of extension sets

---

## Risk Analysis

### Risk 1: Plugin Structure Changes

**Problem**: Anthropic changes plugin.json format, breaking indexer.

**Mitigation**:
- Version plugin.json schema understanding in indexer
- Graceful degradation for unknown fields
- Monitor Anthropic docs for changes

### Risk 2: Browse Available Scope Creep

**Problem**: The "browse available" feature becomes its own massive project.

**Mitigation**:
- Keep the subsystem modular and independent
- Design for eventual extraction as separate project
- MVP: just index known marketplaces, don't build full discovery system

### Risk 3: Configuration Management Complexity

**Problem**: Managing .mcp.json and hooks during activation/deactivation is complex.

**Mitigation**:
- Start with simplest approach (wrapper launcher)
- Iterate based on real usage
- Keep implementation flexible

---

## Alternatives Considered

### Git-Based Registry (Like Homebrew)
**Rejected**: Plugin-only approach is simpler and provides structured metadata.

### Copy Instead of Symlink
**Rejected**: Wastes disk space, updates don't propagate, harder to track state.

### Extension Set Inheritance
**Rejected**: Too much complexity. Focus on making sets easy to manage instead.

### Marketplace Crawling
**Deferred**: For v1, only index known marketplaces. Full crawling may come later.

---

## Next Steps

1. Research: Examine real plugin.json files for schema patterns
2. Design: Draft example extension sets
3. Prototype: Build minimal indexer and activation flow
4. Iterate: Test with real workflows, refine based on feedback

---

## Sources

- [Plugins reference - Claude Code Docs](https://docs.claude.com/en/docs/claude-code/plugins-reference)
- [Customize Claude Code with plugins | Claude](https://www.anthropic.com/news/claude-code-plugins)
- [Creating Claude Code Plugins | Arthur's Blog](https://clune.org/posts/creating-claude-code-plugins/)
- [Claude Code Plugin Directory](https://www.claudecodeplugin.com/)
