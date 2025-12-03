# Bug Report: Cross-Scope State Pollution

**Date**: 2025-10-28
**Severity**: CRITICAL
**Status**: BLOCKS 1.0 RELEASE

## Summary

Servers installed in user-global scope (~/.claude/settings.json) incorrectly show as DISABLED when they appear in user-local scope's (~/.claude/settings.local.json) disabledMcpjsonServers array.

## Evidence

### Real System State

**user-global** (~/.claude/settings.json):
```json
{
  "mcpServers": {
    "@scope/package-name": {
      "command": "npx",
      "args": ["@scope/package-name"],
      "env": {},
      "type": "stdio"
    }
  }
}
```

**user-local** (~/.claude/settings.local.json):
```json
{
  "enabledMcpjsonServers": [],
  "disabledMcpjsonServers": [
    "frida-mcp",
    "ida-pro-mcp",
    "@scope/package-name"
  ]
}
```

### Incorrect Behavior

```bash
$ mcpi list --client claude-code --scope user-global
MCP Servers
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ ID                  ┃ Client      ┃ Scope       ┃ State    ┃ Command ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ @scope/package-name │ claude-code │ user-global │ DISABLED │ npx     │
└─────────────────────┴─────────────┴─────────────┴──────────┴─────────┘
```

**WRONG**: Server is in user-global (which has no disable mechanism) but shows as DISABLED because it appears in user-local's disabled array.

**EXPECTED**: Server should show as ENABLED because it exists in user-global's mcpServers object.

## Root Cause

### Bug Location

File: `src/mcpi/clients/claude_code.py`
Function: `_get_server_state()` (lines 167-205)

### Buggy Code

```python
def _get_server_state(self, server_id: str) -> ServerState:
    """Get the actual state of a server using Claude's enable/disable arrays."""
    # Check Claude settings scopes for enabled/disabled arrays
    settings_scopes = ["project-local", "user-local", "user-global"]

    for scope_name in settings_scopes:
        if scope_name in self._scopes:
            handler = self._scopes[scope_name]

            if handler.exists():
                try:
                    current_data = handler.reader.read(handler.config.path)
                    enabled_servers = current_data.get("enabledMcpjsonServers", [])
                    disabled_servers = current_data.get("disabledMcpjsonServers", [])

                    # If explicitly disabled, return DISABLED
                    if server_id in disabled_servers:
                        return ServerState.DISABLED  # <-- BUG: Returns disabled even for other scopes!

                    # If explicitly enabled, return ENABLED
                    if server_id in enabled_servers:
                        return ServerState.ENABLED

                except Exception:
                    continue

    return ServerState.ENABLED
```

### Problem

The function checks ALL settings scopes for enable/disable arrays WITHOUT considering which scope the server actually belongs to. This causes:

1. Server is queried from user-global scope
2. Function checks user-local first (in iteration order)
3. Finds server_id in user-local's disabledMcpjsonServers
4. Returns DISABLED for user-global server (WRONG!)

### Architecture Flaw

The function assumes enable/disable state is GLOBAL across all scopes. But it should be SCOPE-SPECIFIC:

- user-local's disabled array should ONLY affect servers in user-local scope
- user-global servers should have INDEPENDENT state
- No cross-scope pollution should occur

## Impact

### User Impact

1. Users cannot see true state of servers in user-global scope
2. Disabling a server name in user-local affects ALL scopes with that name
3. Confusing behavior: "Why is my user-global server disabled?"

### Code Impact

1. `list_servers()` returns incorrect state for user-global servers
2. CLI `mcpi list` shows wrong information
3. Users may take incorrect actions based on wrong state

## Fix

### Solution: Make State Queries Scope-Aware

```python
def _get_server_state(self, server_id: str, scope: str) -> ServerState:
    """Get the actual state of a server in a SPECIFIC scope.

    Args:
        server_id: Server identifier
        scope: The scope to check state in

    Returns:
        Server state within that scope only
    """
    handler = self._scopes.get(scope)
    if not handler or not handler.exists():
        return ServerState.NOT_INSTALLED

    try:
        current_data = handler.reader.read(handler.config.path)

        # Only check arrays if THIS SCOPE has them
        disabled_servers = current_data.get("disabledMcpjsonServers", [])
        if server_id in disabled_servers:
            return ServerState.DISABLED

        enabled_servers = current_data.get("enabledMcpjsonServers", [])
        if server_id in enabled_servers:
            return ServerState.ENABLED

    except Exception:
        pass

    # Default: if server exists in scope, it's enabled
    return ServerState.ENABLED
```

### Required Changes

1. Add `scope` parameter to `_get_server_state()`
2. Update call sites in `list_servers()` to pass scope
3. Only check enable/disable arrays in the SAME scope
4. Add tests to verify scope isolation

### Testing

```python
def test_no_cross_scope_pollution():
    """Verify user-local disabled array doesn't affect user-global."""
    # Setup: Server in user-global, disabled in user-local
    user_global_data = {"mcpServers": {"test-server": {...}}}
    user_local_data = {"disabledMcpjsonServers": ["test-server"]}

    # Query user-global state
    state = plugin._get_server_state("test-server", "user-global")

    # Should be ENABLED (not affected by user-local)
    assert state == ServerState.ENABLED
```

## Additional Issues Found

While investigating this bug, two related issues were discovered:

### Issue #2: user-global Scope Has No Disable Mechanism

**Problem**: user-global (~/.claude/settings.json) does NOT have enabledMcpjsonServers/disabledMcpjsonServers arrays in real files.

**Structure**:
- Code/schema ASSUMES: enabledMcpjsonServers/disabledMcpjsonServers arrays exist
- Reality: Only has mcpServers object (like .mcp.json)

**Impact**: No way to actually disable servers in user-global scope.

**Fix for 1.0**: Return clear error when trying to enable/disable user-global servers.

**Fix for 1.1**: Implement disabled tracking file (~/.claude/disabled-servers.json).

### Issue #3: enable/disable Operations Modify Wrong Scope

**Problem**: `enable_server()`/`disable_server()` iterate through scopes and modify FIRST one found.

**Example**:
```python
# User disables user-global server
mcpi disable @scope/package-name

# Code checks: ["project-local", "user-local", "user-global"]
# Finds user-local first (exists)
# Modifies user-local's disabledMcpjsonServers (WRONG SCOPE!)
```

**Fix**: Check which scope the server belongs to first, then modify that scope.

## Recommendation

1. **Fix Bug #1 (Cross-Scope Pollution)**: Make state queries scope-aware (8 hours)
2. **Document Issue #2**: user-global enable/disable not supported in 1.0
3. **Fix Issue #3**: Make enable/disable operations scope-aware (4 hours)
4. **Add Tests**: Verify scope isolation (4 hours)

**Total effort**: 16 hours
**Risk**: Low (fixes bugs, no new features)
**Should block 1.0**: YES (correctness issue)

## References

- Full evaluation: `.agent_planning/EVALUATION-ENABLE-DISABLE-2025-10-28-CORRECTED.md`
- Summary: `.agent_planning/SUMMARY-ENABLE-DISABLE-BUGS.md`
- Code location: `src/mcpi/clients/claude_code.py:167-205`
