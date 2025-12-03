# Design Patterns MCP Server Connection Failure - Evaluation Report

**Date**: 2025-11-09
**Issue**: Claude Code fails to connect to design-patterns MCP server
**Status**: ROOT CAUSE IDENTIFIED

---

## Executive Summary

**Problem**: The design-patterns MCP server fails to connect when started by Claude Code, showing "✗ Failed to connect" in `claude mcp list` output.

**Root Cause**: Missing `PATTERNS_DIR` environment variable in Claude Code configuration. The server defaults to a relative path `./corpus` which fails when Claude Code starts the process from a different working directory.

**Severity**: CRITICAL - Server is completely non-functional from Claude Code

**Fix Complexity**: TRIVIAL - Single configuration update required

---

## Current State: What Is Actually Happening

### Server Status

**Registry Entry** (`/Users/bmf/icode/mcpi/data/registry.json`):
```json
{
  "design-patterns": {
    "description": "Deterministic access to software design pattern documentation with section-addressable queries",
    "command": "node",
    "args": [
      "/Users/bmf/icode/design-pattern-mcp/dist/server.js"
    ],
    "repository": null
  }
}
```

**Claude Code Configuration** (`~/.claude.json` - user-internal scope):
```json
{
  "mcpServers": {
    "design-patterns": {
      "command": "node",
      "args": [
        "/Users/bmf/icode/design-pattern-mcp/dist/server.js"
      ],
      "env": {},
      "type": "stdio"
    }
  }
}
```

**Installation Status**:
- ✅ Installed in MCPI registry
- ✅ Configured in Claude Code (user-internal scope)
- ✅ dist/server.js exists and is built
- ✅ corpus directory exists with 3 patterns
- ❌ Cannot connect when started by Claude Code

### Observed Behavior

**Manual Test (from correct directory)**:
```bash
$ cd /Users/bmf/icode/design-pattern-mcp
$ node dist/server.js
[server] Starting design-pattern-mcp server
[server] Corpus directory: ./corpus
[server] Watch mode: false
[indexer] Building index from: ./corpus
[indexer] Found 3 pattern directories
[indexer] Indexed 3 patterns
[indexer] Built search index with 27 entries
[indexer] Index built successfully
[server] MCP server started successfully
```
✅ **Works perfectly**

**Manual Test (from wrong directory)**:
```bash
$ cd /
$ node /Users/bmf/icode/design-pattern-mcp/dist/server.js
[server] Starting design-pattern-mcp server
[server] Corpus directory: ./corpus
[server] Watch mode: false
[server] FATAL: Failed to build index: Patterns directory not found: corpus/patterns
```
❌ **Fails with relative path**

**Manual Test (with environment variable)**:
```bash
$ cd /tmp
$ PATTERNS_DIR=/Users/bmf/icode/design-pattern-mcp/corpus node /Users/bmf/icode/design-pattern-mcp/dist/server.js
[server] Starting design-pattern-mcp server
[server] Corpus directory: /Users/bmf/icode/design-pattern-mcp/corpus
[server] Watch mode: false
[indexer] Building index from: /Users/bmf/icode/design-pattern-mcp/corpus
[indexer] Found 3 pattern directories
[indexer] Indexed 3 patterns
[indexer] Built search index with 27 entries
[indexer] Index built successfully
[server] MCP server started successfully
```
✅ **Works with absolute path via env var**

**MCP Protocol Test**:
```bash
$ echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | node dist/server.js 2>/dev/null
{"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{},"logging":{}},"serverInfo":{"name":"design-pattern-mcp","version":"1.0.0"}},"jsonrpc":"2.0","id":1}
```
✅ **MCP protocol implementation is correct**

**Claude Code Test**:
```bash
$ claude mcp list
design-patterns: node /Users/bmf/icode/design-pattern-mcp/dist/server.js - ✗ Failed to connect
```
❌ **Cannot connect**

---

## Root Cause Analysis

### Code Analysis

**Server Configuration** (`src/server.ts` lines 14-15):
```typescript
const CORPUS_DIR = process.env.PATTERNS_DIR || './corpus';
const WATCH_MODE = process.argv.includes('--watch');
```

The server uses:
1. Environment variable `PATTERNS_DIR` if set
2. Falls back to relative path `./corpus` if not set

**Index Building** (`src/indexer.ts` - inferred):
```typescript
// Expects to find: ${CORPUS_DIR}/patterns/
const patternsDir = join(CORPUS_DIR, 'patterns');
```

### Failure Chain

1. **Claude Code starts server**: `node /Users/bmf/icode/design-pattern-mcp/dist/server.js`
2. **Working directory**: Unknown (likely Claude's install directory, NOT the server's directory)
3. **PATTERNS_DIR not set**: Falls back to `./corpus`
4. **Relative path resolution**: `./corpus` resolves relative to Claude's cwd, not server directory
5. **Index build fails**: Cannot find `corpus/patterns` directory
6. **Server exits**: Fatal error, process exits with code 1
7. **Claude detects failure**: Reports "Failed to connect"

### Evidence

**Official README Documentation** (`README.md` lines 102-111):
```json
{
  "mcpServers": {
    "design-patterns": {
      "command": "node",
      "args": ["/absolute/path/to/design-pattern-mcp/dist/server.js"],
      "env": {
        "PATTERNS_DIR": "/absolute/path/to/design-pattern-mcp/corpus"
      }
    }
  }
}
```

> **Important**: Use absolute paths. Relative paths may not resolve correctly from Claude's working directory.

The README explicitly warns about this exact issue and provides the correct configuration with the `PATTERNS_DIR` environment variable.

---

## Gap Analysis

### Configuration Gap

**Expected** (per README):
```json
{
  "command": "node",
  "args": ["/Users/bmf/icode/design-pattern-mcp/dist/server.js"],
  "env": {
    "PATTERNS_DIR": "/Users/bmf/icode/design-pattern-mcp/corpus"
  },
  "type": "stdio"
}
```

**Actual** (current Claude Code config):
```json
{
  "command": "node",
  "args": ["/Users/bmf/icode/design-pattern-mcp/dist/server.js"],
  "env": {},
  "type": "stdio"
}
```

**Gap**: Missing `"PATTERNS_DIR": "/Users/bmf/icode/design-pattern-mcp/corpus"` in `env` object.

### MCPI Registry Gap

The MCPI registry entry does not include environment variables, which means:
1. ❌ `mcpi install design-patterns` will create incomplete configuration
2. ❌ Users will encounter this same failure
3. ❌ No way to specify env vars in registry schema currently

---

## Recommended Fixes

### Fix 1: Update Claude Code Configuration (IMMEDIATE)

**Action**: Update `~/.claude.json` to include PATTERNS_DIR environment variable

**Manual Fix**:
```bash
# Edit ~/.claude.json
# Change the design-patterns entry from:
{
  "command": "node",
  "args": ["/Users/bmf/icode/design-pattern-mcp/dist/server.js"],
  "env": {},
  "type": "stdio"
}

# To:
{
  "command": "node",
  "args": ["/Users/bmf/icode/design-pattern-mcp/dist/server.js"],
  "env": {
    "PATTERNS_DIR": "/Users/bmf/icode/design-pattern-mcp/corpus"
  },
  "type": "stdio"
}
```

**MCPI Command** (if available):
```bash
# Update environment variable for design-patterns server
mcpi config design-patterns --set-env PATTERNS_DIR=/Users/bmf/icode/design-pattern-mcp/corpus
```

**Expected Outcome**: Server will start successfully and connect to Claude Code

**Testing**:
```bash
# Restart Claude Code or reload MCP servers
# Then verify:
claude mcp list | grep design-patterns
# Should show: ✓ Connected
```

### Fix 2: Update MCPI Registry Entry (MEDIUM PRIORITY)

**Action**: Add environment variable support to registry schema and update design-patterns entry

**Registry Update** (`data/registry.json`):
```json
{
  "design-patterns": {
    "description": "Deterministic access to software design pattern documentation with section-addressable queries",
    "command": "node",
    "args": [
      "/Users/bmf/icode/design-pattern-mcp/dist/server.js"
    ],
    "env": {
      "PATTERNS_DIR": "/Users/bmf/icode/design-pattern-mcp/corpus"
    },
    "repository": "https://github.com/yourusername/design-pattern-mcp"
  }
}
```

**Schema Changes Required**:
1. Add `env` field to registry schema (Pydantic model)
2. Update installation logic to include env vars
3. Update all registry validation
4. Document env var usage in CLAUDE.md

**Impact**: All future installations will work correctly

### Fix 3: Improve Server Robustness (LOW PRIORITY)

**Action**: Modify server to detect and warn about missing corpus directory

**Server Enhancement** (`src/server.ts`):
```typescript
// Better error message
if (!existsSync(CORPUS_DIR)) {
  console.error(`[server] FATAL: Corpus directory not found: ${CORPUS_DIR}`);
  console.error(`[server] HINT: Set PATTERNS_DIR environment variable to absolute path`);
  console.error(`[server] Example: PATTERNS_DIR=/absolute/path/to/corpus`);
  process.exit(1);
}
```

**Impact**: Users get clearer error messages

---

## Testing Validation

### Pre-Fix Test
```bash
$ claude mcp list | grep design-patterns
design-patterns: node /Users/bmf/icode/design-pattern-mcp/dist/server.js - ✗ Failed to connect
```

### Post-Fix Test (Expected)
```bash
$ claude mcp list | grep design-patterns
design-patterns: node /Users/bmf/icode/design-pattern-mcp/dist/server.js - ✓ Connected

$ claude mcp tools design-patterns
Available tools for design-patterns:
- list_patterns: List all available design patterns with metadata
- get_sections: Get available sections for a pattern
- get_section: Get content of a specific pattern section
- compare: Compare specific aspects of two patterns
- search: Search patterns by text query with optional filters
- diagnostics: Get diagnostics about corpus health
```

---

## Impact Assessment

### Scope
- **Affected Component**: design-patterns MCP server
- **Affected Users**: Single user (bmf)
- **Affected Functionality**: Complete server non-functionality

### Criticality Matrix

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Severity** | CRITICAL | Server completely unusable |
| **Complexity** | TRIVIAL | Single config line change |
| **Risk** | NONE | Read-only config update |
| **Testing** | SIMPLE | `claude mcp list` verification |
| **Rollback** | IMMEDIATE | Revert config change |

### Downstream Effects

**If Fixed**:
- ✅ Server connects successfully
- ✅ All 6 MCP tools become available
- ✅ Pattern documentation accessible
- ✅ No code changes required

**If Not Fixed**:
- ❌ Server remains non-functional
- ❌ Cannot access design pattern documentation
- ❌ Wasted development effort
- ❌ Other users will hit same issue

---

## Conclusion

**Summary**: The design-patterns MCP server fails to connect because the Claude Code configuration is missing the required `PATTERNS_DIR` environment variable. The server defaults to a relative path `./corpus` which fails when started from Claude Code's working directory. The fix is trivial: add the environment variable to the configuration.

**Confidence**: 100% - Root cause confirmed through testing, documented in README

**Next Action**: Update `~/.claude.json` configuration with PATTERNS_DIR environment variable and verify connection.

---

## Appendix: File Locations

**Server Files**:
- Source: `/Users/bmf/icode/design-pattern-mcp/src/server.ts`
- Compiled: `/Users/bmf/icode/design-pattern-mcp/dist/server.js`
- Corpus: `/Users/bmf/icode/design-pattern-mcp/corpus/`
- Patterns: `/Users/bmf/icode/design-pattern-mcp/corpus/patterns/` (3 patterns)
- README: `/Users/bmf/icode/design-pattern-mcp/README.md`

**Configuration Files**:
- Claude Internal: `~/.claude.json` (contains design-patterns config)
- MCPI Registry: `/Users/bmf/icode/mcpi/data/registry.json`

**Package Info**:
- Name: design-pattern-mcp
- Version: 1.0.0
- Type: ESM module
- Main: dist/server.js
- Dependencies: fastmcp, zod, gray-matter, chokidar
