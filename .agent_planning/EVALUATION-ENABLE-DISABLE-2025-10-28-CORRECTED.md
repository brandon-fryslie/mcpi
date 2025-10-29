# Enable/Disable Functionality Evaluation (CORRECTED)

**Date**: 2025-10-28
**Status**: CRITICAL BUGS IDENTIFIED

## Executive Summary

The enable/disable functionality has **MULTIPLE CRITICAL BUGS** due to incorrect assumptions about scope structure:

1. **Cross-scope state pollution**: user-local's disabled array incorrectly affects user-global servers
2. **Missing disable mechanism**: user-global scope has no way to track disabled servers
3. **Scope structure confusion**: Code assumes all scopes use enable/disable arrays (WRONG)

**Evidence**: Real user has `@scope/package-name` installed in user-global (~/.claude/settings.json), listed in user-local's disabledMcpjsonServers, and it shows as DISABLED even though user-global scope has no disable arrays.

## Actual Scope Structures (VERIFIED)

### Scopes WITH Enable/Disable Arrays

**user-local** (~/.claude/settings.local.json):
```json
{
  "enabledMcpjsonServers": [],
  "disabledMcpjsonServers": ["frida-mcp", "ida-pro-mcp", "@scope/package-name"]
}
```

**project-local** (.claude/settings.local.json):
```json
{
  "enabledMcpjsonServers": [],
  "disabledMcpjsonServers": []
}
```

### Scopes WITHOUT Enable/Disable Arrays

**user-global** (~/.claude/settings.json):
```json
{
  "mcpServers": {
    "@scope/package-name": {
      "command": "npx",
      "args": ["@scope/package-name"]
    }
  }
}
```

**project-mcp** (.mcp.json):
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

**user-internal** (~/.claude.json):
```json
{
  "mcpServers": {
    "browser-tools": { ... },
    "ida-pro-mcp": { ... },
    "frida-mcp": { ... }
  }
}
```

**user-mcp** (~/.claude/mcp_servers.json):
- Same structure as user-global (mcpServers object)

## Critical Bugs Identified

### Bug #1: Cross-Scope State Pollution

**Location**: `claude_code.py:167-205` (`_get_server_state()`)

**Problem**: The function checks enable/disable arrays across ALL settings scopes, causing servers in one scope to be affected by disable arrays in other scopes.

**Example**:
```python
# Server is in user-global
user-global:
  mcpServers:
    "@scope/package-name": { ... }

# But user-local disables it
user-local:
  disabledMcpjsonServers: ["@scope/package-name"]

# Result: Server shows as DISABLED even though user-global has no disable mechanism!
```

**Evidence from real system**:
```
claude-code:user-global:@scope/package-name: state=2 (DISABLED), scope=user-global
user-local: disabledMcpjsonServers: ['@scope/package-name']
user-global: mcpServers: {'@scope/package-name': {...}}
```

### Bug #2: No Disable Mechanism for user-global

**Location**: user-global scope has NO enable/disable arrays

**Problem**:
- user-global uses `mcpServers: {}` object structure (like .mcp.json)
- Schema (claude-settings-schema.yaml) defines enabledMcpjsonServers/disabledMcpjsonServers arrays
- But real user-global files DON'T have these arrays
- Code assumes they exist (lines 186-189)

**Current behavior**:
```python
# claude_code.py:186-189
current_data = handler.reader.read(handler.config.path)
enabled_servers = current_data.get("enabledMcpjsonServers", [])  # Returns []
disabled_servers = current_data.get("disabledMcpjsonServers", [])  # Returns []
```

### Bug #3: Wrong enable/disable Implementation

**Location**: `claude_code.py:323-427` (`enable_server()`, `disable_server()`)

**Problem**: These functions iterate through settings_scopes and modify the FIRST scope they find. This causes:

1. Enable/disable operations may modify the wrong scope
2. Operations on user-global servers actually modify user-local
3. No way to actually disable user-global servers

**Example**:
```python
# User wants to disable user-global server
mcpi disable @scope/package-name

# Code checks scopes in order: ["project-local", "user-local", "user-global"]
# Finds user-local first (exists)
# Adds "@scope/package-name" to user-local's disabledMcpjsonServers
# Result: Wrong scope modified!
```

## Scope-by-Scope Analysis

### Scopes that WORK with current code:

1. **user-local** (~/.claude/settings.local.json)
   - ✅ Has enabledMcpjsonServers/disabledMcpjsonServers arrays
   - ✅ Enable/disable operations work correctly
   - ✅ State tracking works correctly

2. **project-local** (.claude/settings.local.json)
   - ✅ Has enabledMcpjsonServers/disabledMcpjsonServers arrays
   - ✅ Enable/disable operations work correctly
   - ✅ State tracking works correctly

### Scopes that FAIL with current code:

3. **user-global** (~/.claude/settings.json)
   - ❌ NO enabledMcpjsonServers/disabledMcpjsonServers arrays
   - ❌ Enable/disable operations modify wrong scope (user-local)
   - ❌ State tracking polluted by other scopes
   - ❌ Cannot actually disable servers in this scope

4. **project-mcp** (.mcp.json)
   - ❌ NO enabledMcpjsonServers/disabledMcpjsonServers arrays
   - ❌ No enable/disable support at all
   - ⚠️  May not need enable/disable (project-level config)

5. **user-internal** (~/.claude.json)
   - ❌ NO enabledMcpjsonServers/disabledMcpjsonServers arrays
   - ❌ No enable/disable support at all
   - ⚠️  May be managed by Claude directly

6. **user-mcp** (~/.claude/mcp_servers.json)
   - ❌ NO enabledMcpjsonServers/disabledMcpjsonServers arrays
   - ❌ No enable/disable support at all
   - ⚠️  May be legacy/unused

## What Actually Needs to Work

### Use Cases

1. **User installs server to user-global**: `mcpi install --scope user-global <server>`
   - Server added to ~/.claude/settings.json mcpServers
   - Server should be ENABLED by default
   - ✅ This works

2. **User disables user-global server**: `mcpi disable <server>`
   - Where should disabled state be tracked?
   - Option A: Add to user-local's disabledMcpjsonServers (current buggy behavior)
   - Option B: Remove from user-global's mcpServers (loses configuration)
   - Option C: Add "disabled": true field to server config (violates schema)
   - Option D: Create separate disabled tracking file (new mechanism)

3. **User enables user-global server**: `mcpi enable <server>`
   - Where should enabled state come from?
   - How to restore configuration if removed?

4. **User lists servers**: `mcpi list`
   - Should show ALL servers with correct state
   - Should NOT show cross-scope pollution
   - State should be scope-specific

## Architectural Issues

### Issue #1: Conflating Scope-Specific State

Current code treats enable/disable as GLOBAL state across all scopes. But it should be SCOPE-SPECIFIC:

- user-local's disabled array should only affect servers viewed through user-local scope
- user-global servers should have independent state
- No cross-scope pollution

### Issue #2: Different Scope Models

The system has TWO different scope models:

**Model A: Enable/Disable Arrays** (user-local, project-local)
- Servers listed in mcpServers object
- State controlled by separate arrays
- Can disable without removing

**Model B: Presence = Enabled** (user-global, project-mcp, user-internal, user-mcp)
- Servers listed in mcpServers object
- Presence = enabled
- Removal = disabled (loses config)

Current code assumes Model A everywhere (WRONG).

### Issue #3: No Scope-Specific Handlers

Each scope needs its OWN enable/disable strategy:

- user-local: Use existing arrays ✅
- project-local: Use existing arrays ✅
- user-global: Needs NEW mechanism ❌
- project-mcp: Maybe doesn't need enable/disable ❌
- user-internal: Probably shouldn't support enable/disable ❌
- user-mcp: Unclear if used ❌

## Proposed Solutions

### Solution A: Scope-Specific Enable/Disable Handlers (ARCHITECTURAL)

**What**: Each scope gets its own enable/disable strategy

**user-global approach**:
1. Create ~/.claude/disabled-servers.json to track disabled servers
2. Enable = add to settings.json mcpServers + remove from disabled tracking
3. Disable = remove from settings.json mcpServers + add to disabled tracking (preserve config)
4. List = merge mcpServers (enabled) + disabled tracking (disabled)

**project-mcp approach**:
1. Don't support enable/disable (project config is explicit)
2. Or use disabled tracking file like user-global

**user-internal approach**:
1. Don't support enable/disable (managed by Claude)

**Pros**:
- Each scope works correctly
- No cross-scope pollution
- Clear separation of concerns

**Cons**:
- Requires refactoring FileBasedScope
- Need to implement disabled tracking for user-global
- More complex architecture

**Effort**: 8-16 hours

### Solution B: Fix Cross-Scope Pollution Only (BUG FIX)

**What**: Make _get_server_state() scope-aware

**Changes**:
1. Pass scope parameter to _get_server_state()
2. Only check enable/disable arrays in SAME scope
3. For scopes without arrays, default to ENABLED if present

**Example**:
```python
def _get_server_state(self, server_id: str, scope: str) -> ServerState:
    handler = self._scopes[scope]
    if handler.exists():
        data = handler.reader.read(handler.config.path)

        # Only check arrays if this scope has them
        if "disabledMcpjsonServers" in data:
            if server_id in data["disabledMcpjsonServers"]:
                return ServerState.DISABLED

        if "enabledMcpjsonServers" in data:
            if server_id in data["enabledMcpjsonServers"]:
                return ServerState.ENABLED

    # Default: if server exists, it's enabled
    return ServerState.ENABLED
```

**Pros**:
- Fixes immediate cross-scope pollution bug
- Minimal code changes
- Doesn't require new architecture

**Cons**:
- Still no way to disable user-global servers
- Still no enable/disable for other scopes
- Doesn't solve fundamental architecture issue

**Effort**: 2-4 hours

### Solution C: Defer Enable/Disable for 1.0 (DESCOPE)

**What**: Disable enable/disable commands for 1.0 release

**Changes**:
1. Mark enable/disable as NOT IMPLEMENTED
2. Return clear error message
3. Add to post-1.0 roadmap

**Pros**:
- No risk of bugs in 1.0
- Can do it right in 1.1
- Core install/uninstall still works

**Cons**:
- Feature gap
- Users may want this functionality

**Effort**: 1 hour

## Recommendation

**For 1.0 Release**: Solution B (Fix Cross-Scope Pollution) + Solution C (Disable user-global enable/disable)

**Rationale**:
1. Fix the cross-scope pollution bug (critical correctness issue)
2. Keep enable/disable working for user-local and project-local (already works)
3. Explicitly disable enable/disable for user-global (prevent incorrect behavior)
4. Plan Solution A for 1.1 (do it right with proper architecture)

**Changes required**:
1. Fix _get_server_state() to be scope-aware (2 hours)
2. Update enable_server()/disable_server() to check scope type (2 hours)
3. Add clear error messages for unsupported scopes (1 hour)
4. Update tests to verify scope isolation (2 hours)
5. Update documentation (1 hour)

**Total effort**: 8 hours

**Release impact**:
- ✅ Core functionality (install/uninstall) unaffected
- ✅ Enable/disable works correctly for supported scopes
- ✅ No buggy behavior for unsupported scopes
- ✅ Clear path to full feature in 1.1

## Testing Requirements

To verify fixes:

1. **Scope Isolation Test**:
   - Install server in user-global
   - Disable in user-local
   - Verify user-global shows as ENABLED (not cross-polluted)

2. **Enable/Disable Test per Scope**:
   - user-local: enable/disable should work ✅
   - project-local: enable/disable should work ✅
   - user-global: enable/disable should error clearly ⚠️
   - Other scopes: enable/disable should error clearly ⚠️

3. **List Servers Test**:
   - List should show correct state per scope
   - No cross-scope pollution
   - State matches actual configuration

4. **Real System Test**:
   - Fix current user's polluted state
   - Verify @scope/package-name shows correctly
   - Verify other scopes unaffected

## File References

**Bug locations**:
- `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/claude_code.py:167-205` - Cross-scope pollution
- `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/claude_code.py:323-427` - Wrong scope modification

**Schema files**:
- `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/schemas/claude-settings-schema.yaml` - Defines enable/disable arrays
- `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/schemas/mcp-config-schema.yaml` - Defines mcpServers object

**Real files affected**:
- `~/.claude/settings.json` (user-global)
- `~/.claude/settings.local.json` (user-local)
- `.mcp.json` (project-mcp)
- `~/.claude.json` (user-internal)

## Conclusion

This is a **CRITICAL BUG** that should block 1.0 release if left unfixed. However, it's NOT a fundamental architecture failure - it's a bug in state tracking logic that can be fixed with scope-aware state queries.

The recommended approach (Solution B + C) provides:
- ✅ Correct behavior for all cases
- ✅ No cross-scope pollution
- ✅ Clear error messages
- ✅ Path to full feature in 1.1
- ✅ Minimal risk to 1.0 schedule (8 hours effort)
