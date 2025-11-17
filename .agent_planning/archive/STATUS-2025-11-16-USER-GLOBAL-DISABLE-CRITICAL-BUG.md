# STATUS: User-Global MCP Server Disable/Enable Functionality - CRITICAL BUG IDENTIFIED

**Date**: 2025-11-16-18:45:00
**Evaluator**: Claude Code (Ruthless Auditor Mode)
**Focus**: Custom disable mechanism for user-global scope using `~/.claude/.disabled-mcp.json`
**Status**: ❌ **CRITICAL BUG - IMPLEMENTATION DOES NOT WORK AS REQUIRED**

---

## Executive Summary

### CRITICAL FAILURE DETECTED

The custom disable mechanism for user-global MCP servers is **FUNDAMENTALLY BROKEN**. While the code implementation exists and unit tests pass, the feature **DOES NOT WORK** in production because:

1. **Claude Code ignores the tracking file** - Disabled servers still show as enabled in `claude mcp list`
2. **MCPI reports incorrect state** - Shows servers as DISABLED when Claude sees them as ENABLED
3. **The feature is unusable** - Users cannot actually disable user-global servers

### The Problem (Evidence-Based)

**VALIDATION TEST RESULT (CRITICAL)**:
```bash
# What Claude Code sees (ground truth):
$ claude mcp list | grep frida-mcp
frida-mcp: frida-mcp  - ✓ Connected

# What MCPI claims:
$ mcpi list --scope user-internal | grep frida-mcp
│ frida-mcp     │ claude-code │ user-internal │ DISABLED │ frida-mcp │

# Tracking file content:
$ cat ~/.claude/.mcpi-disabled-servers-internal.json
[
  "frida-mcp",
  "internal-server"
]
```

**CONCLUSION**: The tracking file has NO EFFECT on Claude Code. Servers marked as "disabled" by MCPI are still running and connected in Claude.

---

## Critical Gap Analysis

### Required Implementation (From User Requirements)

1. ✅ Custom disable mechanism exists (tracking file approach)
2. ✅ File format works (`~/.claude/.mcpi-disabled-servers.json`)
3. ✅ MCPI operations work (disable/enable commands succeed)
4. ❌ **CRITICAL**: Claude Code does NOT respect the tracking file
5. ❌ **CRITICAL**: No mechanism to actually disable servers in Claude

### What Exists Today

**Code Implementation**: ✅ COMPLETE
- Location: `src/mcpi/clients/claude_code.py` lines 139-164
- Handler: `FileTrackedEnableDisableHandler` with `DisabledServersTracker`
- Tracking files:
  - User-global: `~/.claude/.mcpi-disabled-servers.json`
  - User-internal: `~/.claude/.mcpi-disabled-servers-internal.json`

**Test Coverage**: ✅ COMPLETE (but tests are misleading)
- User-internal tests: 6/6 passing
- User-global tests: Would pass (same pattern)
- **ISSUE**: Tests only verify MCPI's internal state, not Claude's actual behavior

**Runtime Behavior**: ❌ **BROKEN**
- MCPI can track disabled state internally
- MCPI cannot actually disable servers in Claude Code
- Tracking file is ignored by Claude Code

---

## The Fundamental Design Flaw

### What the Current Implementation Does

```
User runs: mcpi disable frida-mcp

1. MCPI reads ~/.claude.json (server exists)
2. MCPI adds "frida-mcp" to ~/.claude/.mcpi-disabled-servers-internal.json
3. MCPI shows server as DISABLED in `mcpi list`

BUT CLAUDE CODE:
4. Still reads ~/.claude.json
5. Still loads frida-mcp server
6. Server is still connected and working
```

### What's Missing (The Critical Gap)

**Claude Code has NO KNOWLEDGE of MCPI's tracking files**. Claude only reads:
- `~/.claude/settings.json` (user-global scope)
- `~/.claude.json` (user-internal scope)
- Plugin configurations

Claude Code does NOT read:
- `~/.claude/.mcpi-disabled-servers.json`
- `~/.claude/.mcpi-disabled-servers-internal.json`

**IMPLICATION**: The tracking file approach is USELESS for user-global and user-internal scopes because Claude Code never checks these files.

---

## Required Implementation (Correct Approach)

### For User-Global Scope (~/.claude/settings.json)

**The ONLY way to disable servers that Claude Code respects**:

**Option 1: Move Config to Different File (Original User Request)**
```bash
# Disable: Move config from settings.json to .disabled-mcp.json
mcpi disable <server>
  1. Read ~/.claude/settings.json
  2. Extract server config for <server>
  3. Write config to ~/.claude/.disabled-mcp.json
  4. Remove server from ~/.claude/settings.json

# Enable: Move config back
mcpi enable <server>
  1. Read ~/.claude/.disabled-mcp.json
  2. Extract server config for <server>
  3. Write config to ~/.claude/settings.json
  4. Remove server from ~/.claude/.disabled-mcp.json
```

**Result**: Claude only sees servers in `settings.json`, so disabled servers won't load.

**Option 2: Use Inline "disabled" Field**
```bash
# Disable: Add "disabled": true to server config
mcpi disable <server>
  1. Read ~/.claude/settings.json
  2. Find server config for <server>
  3. Add "disabled": true to config
  4. Write back to ~/.claude/settings.json

# Enable: Remove "disabled" field
mcpi enable <server>
  1. Read ~/.claude/settings.json
  2. Find server config for <server>
  3. Remove "disabled" field from config
  4. Write back to ~/.claude/settings.json
```

**Result**: Need to verify if Claude Code respects inline "disabled" field in settings.json.

---

## Validation Test Results (Runtime Evidence)

### Test 1: Claude vs MCPI State Comparison (user-internal scope)

**Servers in `~/.claude.json`**:
```json
{
  "mcpServers": {
    "browser-tools": { "command": "npx", ... },
    "frida-mcp": { "command": "frida-mcp", ... },
    "playwright": { "command": "pnpm", ... }
  }
}
```

**MCPI Tracking File (`~/.claude/.mcpi-disabled-servers-internal.json`)**:
```json
[
  "frida-mcp",
  "internal-server"
]
```

**Claude Code Output**:
```
$ claude mcp list
plugin:beads:beads: uv --directory /Users/bmf/.claude/plugins/... - ✓ Connected
plugin:dev-loop:chrome-devtools: npx -y chrome-devtools-mcp@latest - ✓ Connected
browser-tools: npx -y @agentdeskai/browser-tools-mcp - ✓ Connected
frida-mcp: frida-mcp  - ✓ Connected  ← SHOULD BE DISABLED BUT IS CONNECTED
playwright: pnpm dlx @playwright/mcp@latest --extension - ✓ Connected
```

**MCPI Output**:
```
$ mcpi list --scope user-internal
│ browser-tools │ claude-code │ user-internal │ ENABLED  │ npx       │
│ frida-mcp     │ claude-code │ user-internal │ DISABLED │ frida-mcp │ ← MCPI thinks it's disabled
│ playwright    │ claude-code │ user-internal │ ENABLED  │ pnpm      │
```

**VERDICT**: ❌ **CRITICAL MISMATCH** - MCPI shows DISABLED, Claude shows CONNECTED

### Test 2: User-Global Scope (Similar Issue Expected)

**File**: `~/.claude/settings.json`
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "type": "stdio"
    }
  }
}
```

**Tracking File**: `~/.claude/.mcpi-disabled-servers.json`
```json
[
  "test-server"
]
```

**Expected Issue**: If we disable context7, MCPI would add it to tracking file but Claude would still load it.

---

## Test Coverage Analysis

### What Tests Actually Verify

**Current Tests (test_enable_disable_bugs.py)**:
- ✅ MCPI can write to tracking file
- ✅ MCPI can read from tracking file
- ✅ MCPI shows correct state in `mcpi list`
- ✅ Tracking file format is correct
- ✅ Operations are idempotent

**What Tests DO NOT Verify**:
- ❌ Claude Code respects the tracking file
- ❌ Disabled servers actually stop loading
- ❌ `claude mcp list` shows disabled servers correctly
- ❌ End-to-end user workflow works

### Missing Tests (E2E Validation)

**Required Test**:
```python
def test_disabled_server_not_loaded_by_claude():
    """Verify that a disabled server does NOT appear in 'claude mcp list'."""
    # 1. Add server to ~/.claude.json
    # 2. Verify 'claude mcp list' shows it
    # 3. Run 'mcpi disable <server>'
    # 4. Verify 'claude mcp list' does NOT show it
    # 5. Run 'mcpi enable <server>'
    # 6. Verify 'claude mcp list' shows it again
```

**This test would FAIL** because Claude ignores the tracking file.

---

## Root Cause Analysis

### Why The Implementation Is Wrong

**Original User Requirement (Misunderstood)**:
> "For user-global MCP servers, there is NO built-in disable mechanism in Claude Code.
> We must implement a CUSTOM disable mechanism using `~/.claude/.disabled-mcp.json`.
> This file will contain the configuration objects for disabled MCP servers (removed from `~/.claude/settings.json`)."

**What Was Implemented Instead**:
- Tracking file that stores server IDs (not configs)
- Config remains in `settings.json` (not moved)
- Claude Code never checks the tracking file

**The Disconnect**:
- User asked for: "Move config to different file"
- We implemented: "Track disabled IDs in separate file"
- Result: Feature doesn't work

### Why This Happened

**Pattern Reuse Without Validation**:
- User-internal implementation copied from user-global
- Both use `FileTrackedEnableDisableHandler`
- Tests verify MCPI behavior only
- No end-to-end validation that Claude respects the mechanism

**Assumption Failure**:
- Assumed tracking file would affect Claude's behavior
- Never verified that assumption
- Tests passed because they only check MCPI's internal state

---

## Gap Summary (Specification vs Reality)

### Specification Requirements

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Custom disable mechanism exists | ✅ | Code in claude_code.py |
| Uses separate tracking file | ✅ | .mcpi-disabled-servers.json |
| Servers in settings.json = enabled | ❌ | Servers in tracking file are also enabled in Claude |
| Servers in .disabled-mcp.json = disabled | ❌ | No such file exists (only tracking file) |
| `mcpi list` shows combined state | ⚠️ | Shows MCPI's state, not Claude's state |
| `mcpi disable` actually disables | ❌ | Only updates MCPI's tracking, Claude ignores it |
| `mcpi enable` actually enables | N/A | Server was never disabled in Claude |
| Validation: Disabled servers not in `claude mcp list` | ❌ | CRITICAL FAILURE |

**Completion**: 2/8 requirements met (25%)

### What Works

1. ✅ MCPI can track which servers user wants disabled
2. ✅ MCPI shows correct state in its own `list` command
3. ✅ File operations are safe (idempotent, atomic)
4. ✅ Code quality is good (follows patterns)
5. ✅ Unit tests pass

### What Doesn't Work

1. ❌ Servers don't actually get disabled in Claude Code
2. ❌ `claude mcp list` still shows disabled servers
3. ❌ No real effect on Claude's behavior
4. ❌ Feature is cosmetic (MCPI UI only)
5. ❌ User cannot achieve their goal (disable servers)

---

## Blocking Issues

### BLOCKER-1: Claude Code Ignores Tracking File

**Severity**: CRITICAL
**Impact**: Feature completely non-functional
**Evidence**: `claude mcp list` shows frida-mcp as connected despite being in tracking file

**Fix Required**:
- Option A: Implement config file movement approach (as originally requested)
- Option B: Modify settings.json to add "disabled": true field
- Option C: Give up on this approach and use a different scope that supports arrays

**Estimated Effort**: 2-4 hours (design + implementation + testing)

### BLOCKER-2: No End-to-End Validation

**Severity**: HIGH
**Impact**: Cannot verify fix works without manual testing
**Evidence**: All tests pass but feature doesn't work

**Fix Required**:
- Add E2E test that runs `claude mcp list` and verifies output
- Add test that checks actual Claude behavior, not just MCPI state
- Add integration test with real Claude Code instance

**Estimated Effort**: 2-3 hours (complex test setup)

### BLOCKER-3: Misleading Documentation

**Severity**: MEDIUM
**Impact**: Users think feature works when it doesn't
**Evidence**: SHIP-CHECKLIST says "READY TO SHIP ✅" but feature is broken

**Fix Required**:
- Update all planning docs to acknowledge bug
- Add warning to CLAUDE.md that feature is not yet functional
- Create new plan for correct implementation

**Estimated Effort**: 1 hour (documentation updates)

---

## Recommendations

### Immediate Actions (STOP SHIP)

1. **DO NOT SHIP v2.0** - Feature is broken, would damage user trust
2. **Revert or disable user-global/user-internal disable handlers** - Set back to `None`
3. **Create bug ticket** - Document the issue for proper fix
4. **Update documentation** - Remove claims that feature works

### Short-Term Fix (Correct Implementation)

**Recommended Approach**: Implement config file movement (original user request)

```python
class FileMovedEnableDisableHandler:
    """Enable/disable by moving config between files."""

    def __init__(self, config_path: Path, disabled_path: Path, ...):
        self.config_path = config_path  # ~/.claude/settings.json
        self.disabled_path = disabled_path  # ~/.claude/.disabled-mcp.json

    def disable_server(self, server_id: str) -> bool:
        """Move server config from settings.json to .disabled-mcp.json"""
        # 1. Read settings.json
        # 2. Extract server config
        # 3. Write to .disabled-mcp.json
        # 4. Remove from settings.json

    def enable_server(self, server_id: str) -> bool:
        """Move server config from .disabled-mcp.json to settings.json"""
        # 1. Read .disabled-mcp.json
        # 2. Extract server config
        # 3. Write to settings.json
        # 4. Remove from .disabled-mcp.json

    def is_disabled(self, server_id: str) -> bool:
        """Check if server exists in .disabled-mcp.json"""
        # Read .disabled-mcp.json and check for server
```

**Why This Will Work**:
- Claude only loads servers from `settings.json`
- If server is in `.disabled-mcp.json`, Claude won't see it
- No need for Claude to check tracking file
- Actually achieves the goal

**Testing Strategy**:
1. Unit tests for file operations
2. **E2E test**: Verify `claude mcp list` output changes
3. Manual validation before ship

**Estimated Effort**:
- Implementation: 3 hours
- Testing: 2 hours
- E2E validation: 1 hour
- **Total**: 6 hours (1 work session)

### Long-Term Improvements

1. **Add `mcpi doctor` command** - Detect state drift between MCPI and Claude
2. **Consolidate tracking files** - Single file with scope namespacing
3. **Better error messages** - Warn users when operations don't affect Claude
4. **Integration tests** - Always verify Claude's actual behavior

---

## Test Suite Status

### Passing Tests (Misleading)

```
tests/test_enable_disable_bugs.py::TestUserInternalEnableDisable
✓ test_user_internal_disable_server_creates_tracking_file
✓ test_user_internal_enable_server_removes_from_tracking_file
✓ test_user_internal_disabled_server_shows_correct_state
✓ test_user_internal_idempotent_disable
✓ test_user_internal_idempotent_enable
✓ test_user_internal_scope_isolation

Status: 6/6 passing
Issue: Tests verify MCPI state, not Claude behavior
```

### Missing Tests (Critical)

```
tests/test_e2e_claude_integration.py (DOES NOT EXIST)
✗ test_disabled_server_not_in_claude_mcp_list
✗ test_enabled_server_appears_in_claude_mcp_list
✗ test_disable_actually_stops_server_loading
✗ test_enable_actually_starts_server_loading

Status: 0/4 (tests don't exist)
Issue: No end-to-end validation of Claude behavior
```

---

## Manual Validation Results

### Test Procedure

```bash
# Step 1: Check current state
$ claude mcp list
frida-mcp: frida-mcp  - ✓ Connected  # Server is running

# Step 2: Check MCPI state
$ mcpi list --scope user-internal | grep frida-mcp
│ frida-mcp     │ claude-code │ user-internal │ DISABLED │ frida-mcp │

# Step 3: Check tracking file
$ cat ~/.claude/.mcpi-disabled-servers-internal.json
["frida-mcp", "internal-server"]

# Step 4: Check config file
$ jq '.mcpServers | keys[]' ~/.claude.json
browser-tools
frida-mcp  # Server still in config file
playwright
```

### Validation Results

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| frida-mcp in tracking file | Yes | Yes | ✅ |
| frida-mcp in config file | Yes | Yes | ✅ |
| MCPI shows DISABLED | Yes | Yes | ✅ |
| Claude shows disconnected | Yes | **No (Connected)** | ❌ **FAIL** |

**CONCLUSION**: ❌ **FEATURE DOES NOT WORK**

---

## Impact Assessment

### User Impact

**If Shipped As-Is**:
1. Users try to disable servers
2. MCPI says "Server disabled successfully"
3. Server continues running in Claude
4. Users confused/frustrated
5. Loss of trust in MCPI tool

**User Expectations vs Reality**:
- **User expects**: `mcpi disable <server>` stops the server
- **Reality**: Server keeps running, only MCPI's internal state changes
- **Gap**: Complete disconnect between UI and behavior

### Technical Debt

**Current State**:
- Two tracking files that don't do anything useful
- Code that claims to support disable but doesn't
- Tests that pass but don't validate the feature
- Documentation that incorrectly says "READY TO SHIP"

**If Not Fixed**:
- Users will file bugs
- Code becomes legacy debt (can't remove without breaking existing tracking files)
- More complex to fix later (users may have disabled servers in tracking files)

---

## Next Steps

### Critical Path (Required Before ANY Ship)

1. **IMMEDIATE**: Stop v2.0 ship process
2. **Day 1**: Implement correct approach (config file movement)
3. **Day 1**: Add E2E tests that verify Claude behavior
4. **Day 2**: Manual validation with real Claude Code
5. **Day 2**: Update documentation to match implementation
6. **Day 3**: Ship v2.0 with working feature

### Alternative Path (If Time Constrained)

1. **IMMEDIATE**: Revert enable/disable handlers for user-global and user-internal to `None`
2. **IMMEDIATE**: Ship v2.0 WITHOUT user-global/user-internal disable support
3. **Future**: Implement correct approach in v2.1
4. **Future**: Add E2E testing framework

**Recommendation**: Take the critical path. Feature is 50% done, might as well finish it correctly.

---

## Conclusion

### Overall Status: ❌ **NOT READY TO SHIP**

**Summary**:
- Code exists: ✅
- Tests pass: ✅
- Feature works: ❌ **CRITICAL FAILURE**
- Ready to ship: ❌ **ABSOLUTELY NOT**

### Confidence Level: **ZERO (0/10)**

The feature is **completely broken** and would not work for users. All tests pass because they only verify MCPI's internal state, not the actual behavior users care about (disabling servers in Claude Code).

### Final Recommendation: **BLOCK SHIP, FIX CRITICAL BUG**

**Three Options**:
1. **Option A (Recommended)**: Implement correct approach (6 hours), ship v2.0 when working
2. **Option B**: Revert feature, ship v2.0 without it, fix in v2.1
3. **Option C**: Ship broken feature, damage user trust, fix in emergency patch

**Recommended**: **Option A** - Do it right the first time.

---

**Report Generated**: 2025-11-16-18:45:00
**Evaluator**: Claude Code (Ruthless Auditor)
**Status**: ❌ **CRITICAL BUG - IMPLEMENTATION BROKEN**
**Action Required**: **BLOCK SHIP UNTIL FIXED**
