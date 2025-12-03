# STATUS: MCPI List Bugs Investigation

**Date**: 2025-11-24 23:55:56
**Project**: MCPI - MCP Server Management CLI
**Issue**: Discrepancies between `mcpi list` and `claude mcp list` outputs

---

## Executive Summary

Two critical bugs have been identified where `mcpi list` output does not match `claude mcp list` output:

1. **BUG 1**: `mcpi list` shows 4 servers that `claude mcp list` doesn't show (context7, frida-mcp, playwright, browser-tools)
2. **BUG 2**: `mcpi list` doesn't show 1 server that `claude mcp list` does show (plugin:beads:beads)

**Root Cause Summary**: MCPI's ClaudeCodePlugin is missing critical configuration scopes that Claude Code actually reads from. The plugin only implements 6 scopes but misses the plugin-based MCP server discovery mechanism that Claude Code uses.

---

## Investigation Findings

### Configuration Files on Disk

**Files that contain MCP servers**:
1. `~/.claude/settings.json` - user-global scope (MCPI: ✓ reads this)
   - Contains: `context7`
2. `~/.claude.json` - user-internal scope (MCPI: ✓ reads this)
   - Contains: `jetbrains`
3. `~/.claude/.disabled-servers.json` - disabled servers (MCPI: ✓ reads this)
   - Contains: `frida-mcp`, `playwright`, `browser-tools`
4. `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/.mcp.json` - project-mcp scope (MCPI: ✓ reads this)
   - Contains: `example-name`
5. `~/.config/claude/settings.json` - UNKNOWN scope (MCPI: ✗ does NOT read this)
   - Contains: empty `mcpServers` object (not relevant for this bug)
6. **`~/.claude/plugins/marketplaces/beads-marketplace/.claude-plugin/plugin.json` - PLUGIN scope (MCPI: ✗ does NOT read this)**
   - Contains: `beads` MCP server definition

**What Claude Code reads** (based on `claude mcp list` output):
- ✓ Plugin-based MCP servers from `~/.claude/plugins/*/.claude-plugin/plugin.json`
- ✓ User-internal MCP servers from `~/.claude.json`
- ✗ Does NOT read from `~/.claude/settings.json` (context7 not shown)
- ✗ Does NOT read from `~/.claude/.disabled-servers.json` (disabled servers not shown)
- ✗ Does NOT read from project-level `.mcp.json` (not in current project context)

**What MCPI reads** (based on ClaudeCodePlugin implementation):
- ✓ project-mcp: `.mcp.json`
- ✓ project-local: `.claude/settings.local.json`
- ✓ user-local: `~/.claude/settings.local.json`
- ✓ user-global: `~/.claude/settings.json` + `~/.claude/disabled-mcp.json` (FileMoveEnableDisableHandler)
- ✓ user-internal: `~/.claude.json` + `~/.claude/.disabled-servers.json` (FileMoveEnableDisableHandler)
- ✓ user-mcp: `~/.claude/mcp_servers.json`
- ✗ Does NOT read plugin-based MCP servers

---

## Bug Analysis

### BUG 1: mcpi shows servers that claude doesn't show

**Affected servers**: context7, frida-mcp, playwright, browser-tools

**Root Cause**:
1. **context7**: Located in `~/.claude/settings.json` (user-global scope)
   - MCPI reads this file via user-global scope and shows it as ENABLED
   - Claude Code does NOT show this server at all
   - **Hypothesis**: Claude Code doesn't read from `~/.claude/settings.json` for MCP servers
   - **Alternative Hypothesis**: The file path `~/.claude/settings.json` is used for other configuration (permissions, hooks, plugins) but NOT for MCP servers

2. **frida-mcp, playwright, browser-tools**: Located in `~/.claude/.disabled-servers.json` (user-internal scope)
   - MCPI reads disabled servers via FileMoveEnableDisableHandler.get_disabled_servers() for user-internal scope
   - These are correctly shown as DISABLED in `mcpi list`
   - Claude Code correctly does NOT show disabled servers
   - **This is CORRECT behavior** - mcpi should show disabled servers with state, claude should not show them at all

**Detailed Analysis**:

Looking at the actual file contents:
- `~/.claude/settings.json` contains `context7` in its `mcpServers` section
- `~/.claude/.disabled-servers.json` contains `frida-mcp`, `playwright`, `browser-tools`
- `claude mcp list` shows neither of these

This suggests that:
1. Claude Code does NOT read from `~/.claude/settings.json` at all (or reads from different file)
2. Claude Code correctly ignores disabled servers in `~/.claude/.disabled-servers.json`

**File Path Analysis**:
The ClaudeCodePlugin has TWO scopes with FileMoveEnableDisableHandler:

1. **user-global scope**:
   - Active: `~/.claude/settings.json` (contains context7)
   - Disabled: `~/.claude/disabled-mcp.json` (EMPTY - only `{"mcpServers": {}}`)

2. **user-internal scope**:
   - Active: `~/.claude.json` (contains jetbrains)
   - Disabled: `~/.claude/.disabled-servers.json` (contains frida-mcp, playwright, browser-tools)

The disabled servers (frida-mcp, playwright, browser-tools) are correctly being read from user-internal scope's disabled file. This is actually working as designed.

**However**, there's still a discrepancy:
- `mcpi list` shows these 3 servers as DISABLED (correct)
- `claude mcp list` does NOT show these servers (also correct - disabled servers shouldn't show)
- But `mcpi list` also shows `context7` from user-global scope, which `claude mcp list` doesn't show

**The real issue**: Why does `claude mcp list` not show `context7` from `~/.claude/settings.json`?

### BUG 2: claude shows servers that mcpi doesn't show

**Affected servers**: plugin:beads:beads

**Root Cause**:
Claude Code has a plugin system that automatically discovers MCP servers from installed plugins. The plugin definition is at:
- `~/.claude/plugins/marketplaces/beads-marketplace/.claude-plugin/plugin.json`

This file contains:
```json
{
  "mcpServers": {
    "beads": {
      "command": "uv",
      "args": [
        "--directory",
        "${CLAUDE_PLUGIN_ROOT}/integrations/beads-mcp",
        "run",
        "beads-mcp"
      ],
      "env": {}
    }
  }
}
```

Additionally, `~/.claude/settings.json` has:
```json
{
  "enabledPlugins": {
    "beads@beads-marketplace": true,
    "dev-loop@loom99": true
  }
}
```

**The Problem**:
MCPI's ClaudeCodePlugin does NOT implement plugin-based MCP server discovery. It only reads from 6 hardcoded scope files. There is no "plugin" scope handler.

When `claude mcp list` runs, it:
1. Reads enabled plugins from settings
2. For each enabled plugin, reads `.claude-plugin/plugin.json`
3. Extracts `mcpServers` from plugin definitions
4. Shows them with prefix `plugin:<plugin-name>:<server-name>`

When `mcpi list` runs, it:
1. Only reads from 6 hardcoded scope files
2. Completely misses plugin-based MCP servers
3. Shows incomplete list

---

## Additional Observations

### Disabled File Path Analysis

**Analysis**: The ClaudeCodePlugin uses TWO different disabled file paths:

1. **user-global scope** (line 155-158 in claude_code.py):
```python
user_global_disabled_path = Path.home() / ".claude" / "disabled-mcp.json"
```
   - File on disk: `~/.claude/disabled-mcp.json` - EXISTS but EMPTY
   - This file is never used in practice (no servers in it)
   - **Status**: Unused file, possibly created by previous MCPI operations

2. **user-internal scope** (line 190-193 in claude_code.py):
```python
user_internal_disabled_file_path = Path.home() / ".claude" / ".disabled-servers.json"
```
   - File on disk: `~/.claude/.disabled-servers.json` - Contains 3 disabled servers
   - This file is actively used and working correctly
   - **Status**: Working as designed

**Conclusion**: There is NO bug with the disabled file paths. Both paths are correct for their respective scopes. The empty `disabled-mcp.json` file is likely just an artifact from testing or unused configuration.

### Scope Priority Confusion

Looking at the scope priorities in ClaudeCodePlugin:
1. project-mcp (priority 1)
2. project-local (priority 2)
3. user-local (priority 3)
4. user-global (priority 4)
5. user-internal (priority 5)
6. user-mcp (priority 6)

But `claude mcp list` output shows only:
- plugin:beads:beads (from plugin system)
- jetbrains (from user-internal `~/.claude.json`)

This suggests Claude Code's actual reading priority is:
1. Plugin-based MCP servers (highest priority)
2. user-internal `~/.claude.json`
3. Other scopes (lower priority or not read at all)

---

## Proposed Solutions

### Solution 1: Implement Plugin-Based MCP Server Discovery

**Description**: Add a new scope handler that discovers MCP servers from Claude Code plugins.

**Implementation Approach**:
1. Create new `PluginBasedScope` class that:
   - Reads `~/.claude/settings.json` to get `enabledPlugins`
   - For each enabled plugin, finds plugin directory at `~/.claude/plugins/marketplaces/<marketplace>/.claude-plugin/plugin.json`
   - Extracts `mcpServers` from plugin definition
   - Returns servers with qualified ID format: `plugin:<plugin-name>:<server-id>`
2. Add this scope to ClaudeCodePlugin with priority 0 (highest priority)
3. Ensure server state is always ENABLED (plugins can't be disabled via mcpi)

**Metrics**:
- **Implementation Complexity**: Medium
  - Need to parse plugin JSON files
  - Need to resolve plugin paths (handle `${CLAUDE_PLUGIN_ROOT}` variables)
  - Need to handle marketplace vs plugin naming
  - Estimated: 200-300 lines of code
- **Mental Load**: Low (positive impact)
  - Makes the system MORE comprehensible by aligning with Claude Code's actual behavior
  - Clearly separates plugin-based from file-based scopes
  - Self-documenting: "plugins are discovered, not configured"
- **Certainty**: 95%
  - We have the plugin.json format from inspection
  - We know the file paths and structure
  - 5% uncertainty: edge cases in variable expansion, multiple marketplaces
- **Flexibility**: High
  - Easy to extend to support new plugin features
  - Can add plugin-specific operations later (e.g., `mcpi plugin list`)
  - Can reuse for other plugin discovery needs
- **Replaceability**: High
  - Isolated scope handler, can be replaced without affecting other scopes
  - Clear interface boundary (ScopeHandler protocol)
  - No dependencies on other scopes
- **Foundational-ness**: FIRST
  - This is a fundamental missing piece of the architecture
  - Other features might depend on accurate server listing
  - Fixing this unblocks other work that assumes mcpi list is accurate

**Files to create/modify**:
- Create: `src/mcpi/clients/plugin_based.py` (new PluginBasedScope)
- Modify: `src/mcpi/clients/claude_code.py` (add plugin scope to _initialize_scopes)
- Create: `tests/test_plugin_based_scope.py` (unit tests)
- Modify: `tests/test_functional_user_workflows.py` (integration tests)

---

### Solution 2: Investigate ~/.claude/settings.json MCP Server Usage

**Description**: Investigate whether Claude Code actually reads MCP servers from `~/.claude/settings.json` or if this file is only used for non-MCP configuration.

**Implementation Approach**:
1. Use system monitoring tools to trace file access:
   ```bash
   sudo fs_usage -w -f filesys claude mcp list | grep settings.json
   ```
2. Search Claude Code documentation for file path references
3. Test adding a server to `~/.claude/settings.json` and verify if `claude mcp list` shows it
4. Review file structure: `~/.claude/settings.json` contains many fields (permissions, hooks, enabledPlugins) but only minimal `mcpServers` config
5. Determine if this file is legacy, unused, or for specific use cases

**Metrics**:
- **Implementation Complexity**: Low
  - Investigation and testing, no coding
  - Estimated: 30-60 minutes
- **Mental Load**: Low (positive impact)
  - Clarifies which files are actually used
  - Reduces confusion about scope mappings
- **Certainty**: N/A (this solution provides certainty for other solutions)
- **Flexibility**: High
  - Results inform whether to keep or remove user-global scope
- **Replaceability**: N/A (knowledge gathering)
- **Foundational-ness**: FIRST
  - Must understand actual file usage before making changes
  - Prevents removing/modifying code that might be correct

**Expected Outcome**:
Either:
- Confirm `~/.claude/settings.json` is NOT used for MCP servers → Remove user-global scope from MCPI
- Confirm it IS used in certain contexts → Update investigation findings and keep the scope

---

### Solution 3: Remove user-global Scope from ClaudeCodePlugin

**Description**: Remove the user-global scope entirely since Claude Code doesn't actually read from `~/.claude/settings.json`.

**Implementation Approach**:
1. Remove user-global scope from `_initialize_scopes` method
2. Update documentation to reflect accurate scope list
3. Update tests to not expect user-global scope
4. Ensure FileMoveEnableDisableHandler tests still pass for user-internal scope

**Metrics**:
- **Implementation Complexity**: Low
  - Remove code rather than add
  - Update tests and docs
  - Estimated: 30-60 minutes
- **Mental Load**: Low (positive impact)
  - Simplifies mental model by removing non-existent scope
  - Reduces confusion about which files Claude Code actually reads
  - Makes system MORE comprehensible
- **Certainty**: 85%
  - We verified claude doesn't show servers from ~/.claude/settings.json
  - 15% uncertainty: might be used in different contexts or by other tools
- **Flexibility**: Low
  - Removing functionality is hard to extend
  - If we're wrong, have to re-add it
- **Replaceability**: Medium
  - Easy to re-add if needed (code is in git history)
  - But creates churn and confusion
- **Foundational-ness**: SECOND or NEVER
  - Should investigate WHY the file exists first
  - Maybe it's used for other purposes (permissions, hooks, etc.)
  - Need more research before removing

**Files to modify**:
- `src/mcpi/clients/claude_code.py`
- Multiple test files
- Documentation files

**RECOMMENDATION**: Do NOT implement this solution until we understand the purpose of `~/.claude/settings.json`. It might be used for non-MCP configuration.

---

### Solution 4: Investigate Actual Claude Code Scope Reading

**Description**: Research Claude Code's actual implementation to understand which files it reads and in what priority order.

**Implementation Approach**:
1. Use `strings` command on Claude Code binary to find file paths
2. Use `fs_usage` or `dtrace` to monitor file access when running `claude mcp list`
3. Check Claude Code documentation or source code (if available)
4. Interview Claude Code developers or community
5. Document findings and update MCPI accordingly

**Metrics**:
- **Implementation Complexity**: Low (research task)
  - No coding required initially
  - Mostly investigation and documentation
  - Estimated: 2-4 hours
- **Mental Load**: High (positive long-term)
  - Initial investigation is complex
  - But results in accurate mental model
  - Eliminates guesswork and assumptions
- **Certainty**: N/A (this solution increases certainty for other solutions)
- **Flexibility**: High
  - Research findings can inform multiple solutions
  - Can be used to validate or invalidate assumptions
- **Replaceability**: N/A (knowledge is permanent)
- **Foundational-ness**: FIRST
  - Should be done BEFORE implementing other solutions
  - Prevents wasted work on wrong solutions
  - Provides ground truth for validation

**Method**:
```bash
# Monitor file access when running claude mcp list
sudo fs_usage -w -f filesys claude mcp list

# Or use dtrace
sudo dtrace -n 'syscall::open*:entry /execname == "claude"/ { printf("%s", copyinstr(arg0)); }'

# Run claude mcp list in another terminal
claude mcp list
```

---

## Recommended Implementation Order

1. **FIRST**: Solution 4 (Investigate Actual Claude Code Scope Reading)
   - Provides ground truth for all other solutions
   - Prevents wasted work on wrong assumptions
   - Time: 2-4 hours
   - **CRITICAL**: Must understand what Claude Code actually does

2. **SECOND**: Solution 2 (Investigate ~/.claude/settings.json MCP Server Usage)
   - Determines if user-global scope is correct or should be removed
   - Low effort, high value for decision making
   - Time: 30-60 minutes
   - **OUTCOME**: Informs whether to proceed with Solution 3

3. **THIRD**: Solution 1 (Implement Plugin-Based MCP Server Discovery)
   - Addresses BUG 2 (missing plugin:beads:beads)
   - Fundamental architecture gap
   - High value, medium complexity
   - Time: 4-8 hours
   - **PRIORITY**: This is the actual missing feature that breaks parity with Claude Code

4. **MAYBE**: Solution 3 (Remove user-global Scope)
   - Only if Solution 2 confirms the file isn't used for MCP servers
   - Low priority since it doesn't break anything
   - Time: 30-60 minutes if needed
   - **DECISION**: Wait for investigation results

---

## Testing Requirements

After implementing solutions:

1. **Validation Tests**:
   - Run `claude mcp list` and capture output
   - Run `mcpi list` and capture output
   - Compare outputs programmatically
   - Assert: Every server in claude's output appears in mcpi's output
   - Assert: Every enabled server in mcpi's output appears in claude's output
   - Assert: Disabled servers in mcpi don't appear in claude's output

2. **Unit Tests**:
   - Test PluginBasedScope reads plugin.json correctly
   - Test PluginBasedScope handles missing plugins gracefully
   - Test PluginBasedScope resolves ${CLAUDE_PLUGIN_ROOT} variables
   - Test FileMoveEnableDisableHandler uses correct file paths

3. **Integration Tests**:
   - Test full enable/disable workflow with correct file paths
   - Test list shows plugin-based MCP servers
   - Test plugin servers can't be disabled via mcpi (error message)

---

## Conclusion

**BUG 1** (mcpi shows extra servers): Mix of correct behavior and uncertain scope
- `frida-mcp`, `playwright`, `browser-tools` showing up as DISABLED is **CORRECT BEHAVIOR**
  - These are disabled servers in user-internal scope
  - MCPI correctly shows them with state=DISABLED
  - Claude Code correctly doesn't show disabled servers at all
  - **No fix needed** - this is working as designed
- `context7` showing up from `~/.claude/settings.json` is **UNCERTAIN**
  - MCPI reads this from user-global scope
  - Claude Code doesn't show it
  - **Needs investigation**: Is this scope actually used by Claude Code?
  - **Action**: Run Solution 2 and Solution 4 to investigate

**BUG 2** (mcpi missing plugin servers): **CONFIRMED MISSING FEATURE**
- Plugin-based MCP server discovery is not implemented in MCPI
- This is a fundamental architectural gap
- Must be fixed for MCPI to achieve parity with Claude Code
- **Action**: Implement Solution 1 (high priority)

**Summary**:
- 3 of 4 servers in BUG 1 are correct behavior (disabled servers)
- 1 of 4 servers in BUG 1 needs investigation (context7)
- BUG 2 is a real missing feature that must be implemented

**Next Steps**:
1. **Investigate** actual Claude Code file reading behavior (Solution 4) - 2-4 hours
2. **Investigate** whether `~/.claude/settings.json` is used for MCP servers (Solution 2) - 30-60 minutes
3. **Implement** plugin-based MCP server discovery (Solution 1) - 4-8 hours
4. **Decide** whether to remove user-global scope based on investigation results (Solution 3) - TBD
5. **Validate** with comprehensive integration tests matching claude's actual behavior
