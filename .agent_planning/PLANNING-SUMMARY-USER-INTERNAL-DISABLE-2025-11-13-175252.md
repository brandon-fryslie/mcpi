# Planning Summary: user-internal Enable/Disable Support

**Date**: 2025-11-13 17:52:52
**Full Plan**: `PLAN-USER-INTERNAL-DISABLE-2025-11-13-175252.md`
**Status File**: `STATUS-2025-11-13-DISABLE-EVALUATION.md`
**Priority**: P1 (HIGH)
**Total Effort**: 2-3 hours
**Risk**: LOW

---

## The Problem

Users cannot disable servers in the `user-internal` scope (~/.claude.json). When they try, they get:
```
Scope 'user-internal' does not support enable/disable operations
```

**Root Cause**: Line 178 in `src/mcpi/clients/claude_code.py` sets `enable_disable_handler=None` for user-internal scope.

---

## The Solution

Add `FileTrackedEnableDisableHandler` to user-internal scope (same pattern as user-global):
- Tracking file: `~/.claude/.mcpi-disabled-servers-internal.json`
- Pattern: Reuse existing FileTrackedEnableDisableHandler implementation
- Impact: Additive only (no breaking changes)

---

## Work Items (4 items, 2-3 hours total)

### P1-1: Code Change (30 min)
**File**: `src/mcpi/clients/claude_code.py` (lines 162-179)
**Change**: Replace `enable_disable_handler=None` with:
```python
enable_disable_handler=FileTrackedEnableDisableHandler(
    DisabledServersTracker(user_internal_disabled_tracker_path)
)
```

### P1-2: Tests (1 hour)
**File**: `tests/test_enable_disable_bugs.py`
**Add**: Class `TestUserInternalEnableDisable` with 3 tests:
- test_user_internal_disable_server_creates_tracking_file
- test_user_internal_enable_server_removes_from_tracking_file
- test_user_internal_disabled_server_shows_correct_state

### P1-3: Documentation (30 min)
**File**: `CLAUDE.md`
**Add**: Section "Enable/Disable Mechanisms by Scope" explaining:
- Array-based scopes (project-local, user-local)
- File-tracked scopes (user-global, **user-internal**)
- No-support scopes (project-mcp, user-mcp)

### P1-4: Manual Verification (20 min)
**Test workflow**:
```bash
mcpi add test-server --scope user-internal
mcpi disable test-server  # Should work (not error)
mcpi list --scope user-internal  # Should show DISABLED
cat ~/.claude/.mcpi-disabled-servers-internal.json  # Should contain "test-server"
mcpi enable test-server  # Should work
mcpi list --scope user-internal  # Should show ENABLED
```

---

## Success Criteria

- [ ] `mcpi disable <server>` works for user-internal servers (no error)
- [ ] Tracking file created at `~/.claude/.mcpi-disabled-servers-internal.json`
- [ ] All new tests pass (3/3)
- [ ] No test regressions
- [ ] Documentation explains mechanisms clearly
- [ ] Manual verification successful
- [ ] ~/.claude.json file format unchanged

---

## Dependencies

```
P1-1 (Code) → P1-2 (Tests) → P1-3 (Docs) → P1-4 (Verify)
```

All items are sequential. Execute in order.

---

## Risk Assessment: LOW

**Why Low Risk**:
- ✅ Reusing proven FileTrackedEnableDisableHandler pattern
- ✅ Same implementation as user-global (already tested and working)
- ✅ Additive change only (no breaking changes)
- ✅ No file format modifications
- ✅ Clear rollback path (revert to None)

**Highest Risk**: Handler instantiation failure (Very Low likelihood)
**Mitigation**: Following exact pattern from user-global scope

---

## Testing Strategy

**Functional Tests** (Un-gameable):
- Real file I/O through MCPTestHarness
- Verify actual file contents
- Execute real plugin operations
- Assert on observable behavior

**Test Coverage**:
- Disable creates tracking file ✓
- Enable removes from tracking file ✓
- State shown correctly in list ✓
- Config file unchanged ✓
- Idempotent operations ✓

**Quality Criteria**:
- ✅ USEFUL: Tests real user behavior
- ✅ COMPLETE: Covers all critical paths
- ✅ FLEXIBLE: Not tied to implementation
- ✅ AUTOMATED: Fully automated

---

## Timeline

**Single Session** (2-3 hours):

**Hour 1**:
- P1-1: Code change (30 min)
- P1-2: Tests, first pass (30 min)

**Hour 2**:
- P1-2: Tests, complete (30 min)
- P1-3: Documentation (30 min)

**Hour 3**:
- P1-4: Manual verification (20 min)
- Buffer/cleanup (40 min)

**Checkpoints**:
- ✓ After P1-1: Code compiles
- ✓ After P1-2: All tests pass
- ✓ After P1-3: Docs reviewed
- ✓ After P1-4: Manual verification successful

---

## Key Implementation Details

### Code Change (P1-1)

**Location**: `src/mcpi/clients/claude_code.py` line 178

**Before**:
```python
scopes["user-internal"] = FileBasedScope(
    # ... config ...
    enable_disable_handler=None,  # user-internal doesn't support enable/disable
)
```

**After**:
```python
user_internal_disabled_tracker_path = self._get_scope_path(
    "user-internal-disabled",
    Path.home() / ".claude" / ".mcpi-disabled-servers-internal.json",
)
scopes["user-internal"] = FileBasedScope(
    # ... config ...
    enable_disable_handler=FileTrackedEnableDisableHandler(
        DisabledServersTracker(user_internal_disabled_tracker_path)
    ),  # Supports enable/disable via tracking file
)
```

### Test Pattern (P1-2)

Copy from user-global tests, change scope name to "user-internal":
```python
class TestUserInternalEnableDisable:
    """Test enable/disable for user-internal scope."""

    @pytest.fixture
    def plugin(self, mcp_harness):
        return ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)

    def test_user_internal_disable_server_creates_tracking_file(...):
        # Setup: Install server
        mcp_harness.prepopulate_file("user-internal", {...})

        # Execute: Disable
        result = plugin.disable_server("test-server")

        # Verify: Tracking file created
        assert tracking_path.exists()
        # Verify: Server in tracking file
        assert "test-server" in disabled
```

### Documentation (P1-3)

Add to CLAUDE.md under "## Project Architecture":
```markdown
### Enable/Disable Mechanisms by Scope

#### Scopes with File-Tracked Enable/Disable

**Scopes**: user-global, user-internal

**Tracking Files**:
- `~/.claude/.mcpi-disabled-servers.json` (for user-global)
- `~/.claude/.mcpi-disabled-servers-internal.json` (for user-internal)

**Mechanism**: Server configs stay in config file. Disabled servers tracked
in separate file.
```

---

## Edge Cases Handled

1. **Tracking file already exists**: Adds to existing list ✓
2. **Server doesn't exist**: Returns error (existing validation) ✓
3. **Tracking file corrupted**: Treats as empty, overwrites on next write ✓
4. **Concurrent access**: Last write wins (acceptable for rare scenario) ✓
5. **Manual file edits**: Respected by MCPI ✓

---

## What Success Looks Like

**After implementation**:
```bash
$ mcpi add my-server --scope user-internal
✓ Added server 'my-server' to user-internal

$ mcpi disable my-server
✓ Disabled server 'my-server' in scope 'user-internal'

$ mcpi list --scope user-internal
ID        │ Client      │ Scope         │ State    │ Command
my-server │ claude-code │ user-internal │ DISABLED │ npx

$ cat ~/.claude/.mcpi-disabled-servers-internal.json
["my-server"]

$ cat ~/.claude.json | jq '.mcpServers."my-server"'
{
  "command": "npx",
  "args": ["-y", "my-server"],
  "type": "stdio"
}

$ mcpi enable my-server
✓ Enabled server 'my-server' in scope 'user-internal'

$ mcpi list --scope user-internal
ID        │ Client      │ Scope         │ State   │ Command
my-server │ claude-code │ user-internal │ ENABLED │ npx
```

---

## Alternatives Rejected

**Option A: File Movement Handler** - Too complex (4-8 hours), higher risk
**Option B: Documentation Only** - Doesn't solve user's problem
**Option C: Array-Based Handler** - Modifies official Claude format (risky)

**Selected: Option D (Hybrid)** - FileTracked handler + documentation (LOW risk, 2-3 hours)

---

## Post-Implementation

**Cleanup Planning Files** (retain 4 most recent per prefix):
- Keep: PLAN-USER-INTERNAL-DISABLE-2025-11-13-175252.md (newest)
- Keep: PLAN-2025-11-09-060623.md
- Keep: PLAN-2025-11-09-054705.md
- Keep: PLAN-2025-11-09-052500.md
- Archive: PLAN-2025-11-07-052005.md (5th oldest)

**Git Commit Message** (after completion):
```
feat(clients): add enable/disable support to user-internal scope

- Add FileTrackedEnableDisableHandler to user-internal scope
- Use tracking file: ~/.claude/.mcpi-disabled-servers-internal.json
- Add comprehensive tests for user-internal enable/disable
- Update documentation to explain enable/disable mechanisms
- Resolves user request: disable command now works for user-internal

This is an additive change with no breaking impacts. Servers in
user-internal can now be disabled/enabled using the same mechanism
as user-global scope (separate tracking file).

Tests: 3 new functional tests, all passing
Risk: LOW (reusing proven FileTrackedEnableDisableHandler pattern)
```

---

## Quick Reference

**Files to Modify**:
1. `src/mcpi/clients/claude_code.py` (lines 162-179)
2. `tests/test_enable_disable_bugs.py` (add class at end)
3. `CLAUDE.md` (add section under Architecture)

**Key Classes**:
- `FileTrackedEnableDisableHandler` (already exists)
- `DisabledServersTracker` (already exists)
- `TestUserInternalEnableDisable` (new)

**Tracking File Path**:
- Production: `~/.claude/.mcpi-disabled-servers-internal.json`
- Testing: `mcp_harness.path_overrides["user-internal-disabled"]`

**Test Command**:
```bash
pytest tests/test_enable_disable_bugs.py::TestUserInternalEnableDisable -v
```

---

**Status**: READY FOR IMPLEMENTATION
**Assignee**: test-driven-implementer
**Estimated Time**: 2-3 hours
**Priority**: P1 (HIGH)
**Risk**: LOW
