# Enable/Disable Bugs - Executive Summary

**Date**: 2025-10-28
**Status**: CRITICAL BUGS IDENTIFIED - BLOCKS 1.0 RELEASE

## TL;DR

The enable/disable functionality has **3 critical bugs** caused by incorrect assumptions about scope structure. Current code assumes all scopes use enable/disable arrays, but only 2 of 6 scopes actually have them.

## The Bugs

### Bug #1: Cross-Scope State Pollution (CRITICAL)

**What**: Servers in user-global scope show as DISABLED because they appear in user-local's disabledMcpjsonServers array.

**Evidence**: Real user has `@scope/package-name` installed in user-global, listed in user-local's disabled array, and it incorrectly shows as DISABLED.

**Root cause**: `_get_server_state()` checks ALL settings scopes for enable/disable arrays, causing state pollution across scopes.

**Location**: `claude_code.py:167-205`

### Bug #2: No Disable Mechanism for user-global (CRITICAL)

**What**: user-global scope (~/.claude/settings.json) has NO enable/disable arrays in real files, despite code assuming they exist.

**Structure mismatch**:
- **Code assumes** (claude-settings-schema.yaml): enabledMcpjsonServers/disabledMcpjsonServers arrays exist
- **Reality** (real user-global files): Only has mcpServers object, no enable/disable arrays

**Impact**: No way to actually disable servers in user-global scope.

### Bug #3: Wrong Scope Modified (CRITICAL)

**What**: enable/disable operations on user-global servers actually modify user-local scope.

**Root cause**: `enable_server()`/`disable_server()` iterate through scopes ["project-local", "user-local", "user-global"] and modify the FIRST scope found.

**Location**: `claude_code.py:323-427`

## Scope Structure Reality Check

### ✅ Scopes WITH Enable/Disable Arrays (WORK)
1. **user-local** (~/.claude/settings.local.json)
2. **project-local** (.claude/settings.local.json)

### ❌ Scopes WITHOUT Enable/Disable Arrays (BROKEN)
3. **user-global** (~/.claude/settings.json) - Only has mcpServers object
4. **project-mcp** (.mcp.json) - Only has mcpServers object
5. **user-internal** (~/.claude.json) - Only has mcpServers object
6. **user-mcp** (~/.claude/mcp_servers.json) - Only has mcpServers object

## Recommended Fix for 1.0

**Approach**: Solution B (Fix Cross-Scope Pollution) + Solution C (Disable unsupported scopes)

**Changes**:
1. Make `_get_server_state()` scope-aware (don't check other scopes)
2. Make `enable_server()`/`disable_server()` check if scope supports enable/disable
3. Return clear error for unsupported scopes
4. Add tests to verify scope isolation

**Effort**: 8 hours
**Risk**: Low (fixes bugs, no new features)

**Result**:
- ✅ user-local enable/disable works correctly
- ✅ project-local enable/disable works correctly
- ✅ user-global returns clear error (not supported yet)
- ✅ No cross-scope pollution
- ✅ Core functionality (install/uninstall) unaffected

## Post-1.0 (v1.1)

**Approach**: Solution A (Scope-Specific Handlers)

Implement proper enable/disable for user-global:
1. Create ~/.claude/disabled-servers.json to track disabled state
2. Enable = add to mcpServers + remove from disabled tracking
3. Disable = remove from mcpServers + add to disabled tracking (preserve config)
4. List = merge both sources

**Effort**: 8-16 hours

## Should This Block 1.0?

**YES** - The cross-scope pollution bug (Bug #1) is a critical correctness issue that causes incorrect behavior. However, it can be fixed quickly (8 hours) with low risk.

## Full Details

See: `.agent_planning/EVALUATION-ENABLE-DISABLE-2025-10-28-CORRECTED.md`
