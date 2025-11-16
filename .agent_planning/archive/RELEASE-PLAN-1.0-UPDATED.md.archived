# MCPI 1.0 RELEASE PLAN: UPDATED for Enable/Disable Bugs

**Source**: STATUS-2025-10-28-132841.md + EVALUATION-ENABLE-DISABLE-2025-10-28-CORRECTED.md
**Original Target**: Ship production-ready 1.0 on 2025-11-03
**NEW Target**: Ship production-ready 1.0 on 2025-11-04 (1 day delay)
**Generated**: 2025-10-28 (updated for enable/disable critical bugs)
**Status**: DAYS 1-3 COMPLETE - NEW CRITICAL BUGS FOUND

---

## CRITICAL UPDATE: NEW BUGS DISCOVERED

### Original Day 4 Plan (Now Obsolete)
- **1 critical bug**: `mcpi client info` TypeError (1 hour)
- **Total Day 4**: 3-5 hours
- **Ship date**: 2025-11-03

### NEW Reality After Enable/Disable Evaluation
- **4 critical bugs**: `mcpi client info` + 3 enable/disable bugs
- **Total P0 fixes**: 5-9 hours
- **NEW ship date**: 2025-11-04 (1 day delay)

### New Critical Bugs Found

| Bug ID | Description | Severity | Impact | Fix Time |
|--------|-------------|----------|--------|----------|
| BUG-ORIG | `mcpi client info` TypeError | P0-CRITICAL | Documented feature broken | 1 hour |
| BUG-1 | Cross-scope state pollution | P0-CRITICAL | Production correctness | 2-4 hours |
| BUG-2 | No disable mechanism for user-global | P1-HIGH | Feature gap | 8-16 hours |
| BUG-3 | Wrong scope modification | P0-CRITICAL | Data corruption risk | 2-4 hours |

**Total NEW bugs**: 3 (BUG-1, BUG-2, BUG-3)
**Total P0 bugs**: 3 (BUG-ORIG, BUG-1, BUG-3) = 5-9 hours
**Total P1 bugs**: 1 (BUG-2) = 8-16 hours (DEFER TO 1.1)

---

## UPDATED Executive Summary

### Overall Assessment: 1 DAY DELAY RECOMMENDED

**Original Timeline**: Ship 2025-11-03 (4 days from Day 1-3 complete)
**NEW Timeline**: Ship 2025-11-04 (5 days, +1 day delay)
**Rationale**: 3 NEW critical bugs require 4-8 hours of fix work

### Why Delay is Necessary

**Production Impact of Shipping With Bugs**:
1. **BUG-1 (Cross-scope pollution)**: Servers show WRONG enabled/disabled state
   - Real user impact: `@scope/package-name` in user-global shows DISABLED even though it's running
   - Support burden: HIGH (confusing behavior, users will file bugs)

2. **BUG-3 (Wrong scope modification)**: Enable/disable operations modify WRONG scope
   - Real user impact: Disabling user-global server corrupts user-local config
   - Data corruption risk: HIGH (user config files modified incorrectly)

**Why We Can't Ship With These Bugs**:
- Production correctness is FUNDAMENTAL
- Data corruption is UNACCEPTABLE
- User trust is CRITICAL for 1.0 release
- Support burden from buggy release is EXPENSIVE

**Why 1 Day Delay is Acceptable**:
- Quality > Speed for 1.0 release
- 1 day delay to fix 3 critical bugs is REASONABLE
- Alternative (ship buggy) would require emergency 1.0.1 patch (worse)
- Users expect RELIABILITY, not SPEED

---

## UPDATED Day 4-6 Timeline

### Day 4: CRITICAL BUG FIXES (6-10 hours) - 2025-10-28

**BLOCKING P0 Fixes** (5-9 hours):

1. **BUG-ORIG: `mcpi client info` TypeError** (1 hour)
   - **File**: `src/mcpi/cli.py` line 560
   - **Fix**: Add error check before scope iteration
   - **Testing**: Manual + unit test + regression test
   - **Acceptance**: No TypeError, error message displays, test added

2. **BUG-1: Cross-Scope State Pollution** (2-4 hours)
   - **File**: `src/mcpi/clients/claude_code.py` line 167-205
   - **Fix**: Make `_get_server_state()` scope-aware
   - **Testing**: Scope isolation test + real system test
   - **Acceptance**: State is scope-specific, no cross-pollution

3. **BUG-3: Wrong Scope Modification** (2-4 hours)
   - **File**: `src/mcpi/clients/claude_code.py` line 323-427
   - **Fix**: Update `enable_server()` and `disable_server()` to be scope-aware
   - **Testing**: Scope-specific modification test + error message test
   - **Acceptance**: Operations modify correct scope, clear errors for unsupported

**Documentation** (30 minutes):
4. Document known limitations (BUG-2 deferred to 1.1)
   - Update known issues list
   - Add to release notes
   - Create GitHub issue for 1.1 fix

**DEFERRED (to 1.0.1)**:
- P1 investigations (interactive scope, API contracts) - 2-4 hours
- Manual test `mcpi client set-default` - 15 min

**Total Day 4**: 6-10 hours (P0 fixes + documentation)

---

### Day 5: POLISH & TESTING (4-6 hours) - 2025-10-29

**REQUIRED**:
1. Final test run after bug fixes (30 min)
   - Run full test suite: `pytest --tb=no -q`
   - Verify pass rate ≥ 85.3%
   - Confirm 0 regressions

2. Code quality pass (45 min)
   - Format: `black src/ tests/`
   - Lint: `ruff check src/ tests/ --fix`
   - Type check: `mypy src/`

3. Update documentation (1.5 hours)
   - Update CLAUDE.md with coverage info (40%)
   - Update README with enable/disable limitations
   - Verify all examples work
   - Update testing documentation

4. Create known issues list (1 hour)
   - 82 test failures (88% test infrastructure)
   - Coverage at 40% (target 80% in 1.1)
   - Deferred features (update, doctor, backup/restore)
   - Enable/disable limitations (BUG-2 deferred to 1.1)

**OPTIONAL** (can defer to 1.0.1):
5. Update PROJECT_SPEC (2-3 hours) - LOW PRIORITY

**Total Day 5**: 4-7 hours

---

### Day 6: RELEASE PREPARATION (4-6 hours) - 2025-11-04

**REQUIRED**:
1. Version bump to 1.0.0 (30 min)
   ```bash
   # Update pyproject.toml, src/mcpi/__init__.py, README.md
   git commit -m "chore: bump version to 1.0.0"
   ```

2. Create CHANGELOG.md (1-2 hours)
   - Document all features added
   - Document all bugs fixed (including enable/disable)
   - Document known issues
   - Document deferred items for 1.1

3. Write release notes (1 hour)
   - Highlight quality focus (delayed 1 day to fix critical bugs)
   - Comprehensive feature list
   - Known limitations section
   - Quick start guide

4. Tag and release (1 hour)
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   gh release create v1.0.0 --title "MCPI 1.0.0" --notes-file RELEASE_NOTES.md
   ```

5. Announcement (30 min)
   - Update README badges
   - Close 1.0 milestone
   - Create 1.1 milestone
   - Post announcement

**Total Day 6**: 4-6 hours

---

## UPDATED Timeline Summary

**Original Plan**:
- Day 4: 3-5 hours (1 critical bug)
- Day 5: 4-6 hours (polish)
- Day 6: 4-6 hours (release prep)
- **Total**: 11-17 hours over 3 days
- **Ship**: 2025-11-03

**NEW Plan**:
- Day 4: 6-10 hours (4 critical bugs, 3 P0 fixes)
- Day 5: 4-7 hours (polish + updated docs)
- Day 6: 4-6 hours (release prep)
- **Total**: 14-23 hours over 3 days
- **Ship**: 2025-11-04 (1 day delay)

**Work Increase**: +3-6 hours (from 3 NEW critical bugs)
**Days Added**: +1 day (to accommodate extra work)
**Buffer**: 1.0-1.7x (reduced from 2.4x, still acceptable)

---

## Bug Details & Fix Strategy

### BUG-ORIG: `mcpi client info` TypeError (1 hour)

**From Original Plan** - Already documented

**Problem**: Code assumes `scope` is a dict, but can be string "error"
**File**: `src/mcpi/cli.py` line 560
**Fix**: Add error check before scope iteration

```python
if "error" in client_data:
    info_text += f"[bold]Error:[/bold] {client_data['error']}\n"
    return info_text
# ... existing scope iteration
```

**Testing**:
- Manual: `mcpi client info claude-code`
- Unit test: Add error scenario test
- Regression: Full test suite

---

### BUG-1: Cross-Scope State Pollution (2-4 hours)

**NEW from Enable/Disable Evaluation**

**Problem**: `_get_server_state()` checks enable/disable arrays across ALL scopes, causing cross-scope pollution. User has `@scope/package-name` in user-global, but it shows DISABLED because user-local's `disabledMcpjsonServers` contains it.

**File**: `src/mcpi/clients/claude_code.py` line 167-205

**Fix**: Make state checking scope-aware
```python
def _get_server_state(self, server_id: str, scope: str) -> ServerState:
    """Get server state (SCOPE-AWARE)"""
    handler = self._scopes[scope]
    if not handler.exists():
        return ServerState.NOT_INSTALLED

    data = handler.reader.read(handler.config.path)

    # Only check arrays if this scope has them
    if "disabledMcpjsonServers" in data:
        if server_id in data["disabledMcpjsonServers"]:
            return ServerState.DISABLED

    if "enabledMcpjsonServers" in data:
        if server_id in data["enabledMcpjsonServers"]:
            return ServerState.ENABLED

    # Check if server exists in mcpServers
    if "mcpServers" in data and server_id in data["mcpServers"]:
        return ServerState.ENABLED

    return ServerState.NOT_INSTALLED
```

**Testing**:
1. Scope Isolation Test:
   - Install server in user-global
   - Disable in user-local
   - Verify user-global shows ENABLED (not cross-polluted)

2. Real System Test:
   - Fix user's polluted state
   - Verify `@scope/package-name` shows correctly

**Acceptance Criteria**:
- [ ] State is scope-specific (no cross-pollution)
- [ ] User-global servers show correct state
- [ ] User-local disable arrays only affect user-local
- [ ] Test cases added for scope isolation

**Effort**: 2-4 hours (code 30m, tests 1-2h, verification 30m)

---

### BUG-2: No Disable Mechanism for user-global (8-16 hours) - DEFER TO 1.1

**NEW from Enable/Disable Evaluation**

**Problem**: user-global scope has NO way to track disabled servers. Schema defines `enabledMcpjsonServers`/`disabledMcpjsonServers` arrays, but real user-global files DON'T have them.

**Impact**: Users cannot disable servers in user-global scope (must remove from config)

**Decision**: **DEFER TO 1.1** (architectural fix, not production bug)

**Workaround for 1.0**:
- Document limitation in known issues
- Show clear error when attempting to disable user-global servers
- Suggest manual removal from config file
- Plan architectural fix for 1.1

**Architectural Fix for 1.1**:
1. Create `~/.claude/disabled-servers.json` tracking file
2. Enable = add to settings.json + remove from disabled tracking
3. Disable = remove from settings.json + add to disabled tracking (preserve config)
4. List = merge mcpServers (enabled) + disabled tracking (disabled)

**Rationale for Deferral**:
- Architectural change (8-16 hours)
- High complexity, new file, new logic
- Not production bug (workaround exists)
- Better to do it right in 1.1 with no time pressure

**Documentation for 1.0 Known Issues**:
```markdown
## Known Limitations

### Enable/Disable Functionality

**Supported Scopes**:
- `user-local` (~/.claude/settings.local.json): Full enable/disable support
- `project-local` (.claude/settings.local.json): Full enable/disable support

**Unsupported Scopes**:
- `user-global` (~/.claude/settings.json): Cannot disable servers
  - Workaround: Remove server from config file manually
  - Planned for 1.1: Disabled server tracking file
```

---

### BUG-3: Wrong Scope Modification (2-4 hours)

**NEW from Enable/Disable Evaluation**

**Problem**: `enable_server()` and `disable_server()` iterate through settings_scopes and modify the FIRST scope they find. This causes operations on user-global servers to actually modify user-local.

**Real Impact**: User disables user-global server, but code adds it to user-local's `disabledMcpjsonServers` array instead. This corrupts user-local config.

**File**: `src/mcpi/clients/claude_code.py` line 323-427

**Fix**: Make enable/disable scope-aware
```python
def disable_server(self, server_id: str, scope: Optional[str] = None) -> OperationResult:
    """Disable server (SCOPE-AWARE)"""
    # Find server's actual scope
    actual_scope = self._find_server_scope(server_id)
    if not actual_scope:
        return OperationResult(
            success=False,
            message=f"Server {server_id} not found"
        )

    # Check if scope supports enable/disable
    handler = self._scopes[actual_scope]
    data = handler.reader.read(handler.config.path)

    if "disabledMcpjsonServers" not in data:
        # Scope doesn't support enable/disable
        return OperationResult(
            success=False,
            message=f"Enable/disable not supported for scope '{actual_scope}'. "
                   f"To disable, remove from config: {handler.config.path}"
        )

    # Scope supports enable/disable, proceed
    if server_id not in data.get("disabledMcpjsonServers", []):
        data.setdefault("disabledMcpjsonServers", []).append(server_id)
        handler.writer.write(handler.config.path, data)

    return OperationResult(
        success=True,
        message=f"Disabled {server_id} in {actual_scope}"
    )

def _find_server_scope(self, server_id: str) -> Optional[str]:
    """Find which scope contains the server"""
    for scope_name, handler in self._scopes.items():
        if not handler.exists():
            continue
        data = handler.reader.read(handler.config.path)
        if "mcpServers" in data and server_id in data["mcpServers"]:
            return scope_name
    return None
```

**Testing**:
1. Scope-Specific Modification Test:
   - Install server in user-global
   - Attempt to disable
   - Verify clear error message (not supported)
   - Verify user-local NOT modified

2. Supported Scope Test:
   - Install server in user-local
   - Disable server
   - Verify user-local modified (correct scope)
   - Verify user-global NOT modified

**Acceptance Criteria**:
- [ ] Enable/disable operations modify correct scope
- [ ] Clear error for unsupported scopes
- [ ] No cross-scope modifications
- [ ] Test cases added for scope-specific operations

**Effort**: 2-4 hours (code 1h, tests 1-2h, verification 30m)

---

## Testing Strategy for All Bug Fixes

### Test Cases to Add

**BUG-1: Scope Isolation Test**
```python
def test_scope_isolation_no_cross_pollution():
    """Verify servers in one scope not affected by disable arrays in other scopes"""
    install_server("test-server", scope="user-global")
    disable_server("test-server", scope="user-local")

    # user-global should show ENABLED
    state = get_server_state("test-server", scope="user-global")
    assert state == ServerState.ENABLED

    # user-local should show DISABLED
    state = get_server_state("test-server", scope="user-local")
    assert state == ServerState.DISABLED
```

**BUG-3: Scope-Specific Modification Test**
```python
def test_disable_unsupported_scope_error():
    """Verify clear error when disabling server in unsupported scope"""
    install_server("test-server", scope="user-global")
    result = disable_server("test-server")

    assert not result.success
    assert "not supported" in result.message.lower()

    # Verify user-local NOT modified
    user_local_data = read_config("user-local")
    assert "test-server" not in user_local_data.get("disabledMcpjsonServers", [])

def test_disable_supported_scope_success():
    """Verify disable works correctly in supported scopes"""
    install_server("test-server", scope="user-local")
    result = disable_server("test-server")

    assert result.success
    user_local_data = read_config("user-local")
    assert "test-server" in user_local_data["disabledMcpjsonServers"]
```

### Manual Testing Checklist

**After All Bug Fixes**:
- [ ] BUG-ORIG: `mcpi client info claude-code` works
- [ ] BUG-1: Scope isolation (user-global not polluted)
- [ ] BUG-3: Disable unsupported scope shows error
- [ ] BUG-3: Disable supported scope works correctly
- [ ] Regression: All 17 commands still work
- [ ] Regression: Test pass rate ≥ 85.3%

---

## Success Criteria for 1.0 Release

### UPDATED Must Have (for 1.0 ship)

**Functionality**:
- ✅ All 13 commands work (verified)
- ✅ Installation methods functional (npm, pip, uv, git)
- ✅ Scope management works (rescope, scope list/show)
- ✅ Client management works (client list/show)
- ✅ Shell completion works (bash/zsh/fish)
- **BLOCKING** 0 critical bugs - Need to fix:
  - [ ] BUG-ORIG: `mcpi client info` TypeError (1 hour)
  - [ ] BUG-1: Cross-scope state pollution (2-4 hours)
  - [ ] BUG-3: Wrong scope modification (2-4 hours)

**Quality**:
- ✅ >80% test pass rate (85.3% achieved)
- ✅ 0 test import errors
- ✅ 0 test setup errors
- ✅ CI/CD running
- ✅ Coverage measured (40%)
- [ ] 0 critical bugs (must fix 3 bugs)

**Documentation**:
- ✅ README accurate and complete (95% quality)
- ✅ All commands documented with examples
- ✅ Quick Start guide works
- [ ] Known issues documented (add BUG-2 limitation)
- [ ] CHANGELOG created (Day 6)
- [ ] Release notes written (Day 6)

**Release**:
- [ ] Version bumped to 1.0.0 (Day 6)
- [ ] Git tag created (Day 6)
- [ ] GitHub release published (Day 6)

### UPDATED Should Have (nice to have)

**Documentation**:
- [ ] PROJECT_SPEC updated (can defer to 1.0.1)

**Testing**:
- [ ] P1 test failures investigated (defer to 1.0.1)

**All P2 items**: Defer to 1.1 (no change from original plan)

---

## Risk Assessment

### Risks of Fixing Bugs Before 1.0

**MEDIUM RISK: Regression from Bug Fixes**
- **Likelihood**: 30%
- **Impact**: 1-2 day delay
- **Mitigation**: Comprehensive test suite (85.3% pass rate), manual verification

**LOW RISK: Fix Takes Longer Than Estimated**
- **Likelihood**: 20%
- **Impact**: 1 day delay
- **Mitigation**: Estimates are conservative, simple fixes

**MEDIUM RISK: More Bugs Found During Testing**
- **Likelihood**: 25%
- **Impact**: 1-2 day delay
- **Mitigation**: Can extend to 2025-11-05 if needed

### Risks of Shipping With Bugs (NOT RECOMMENDED)

**HIGH RISK: Production Data Corruption**
- **Likelihood**: 60% (users will encounter BUG-3)
- **Impact**: User configuration files corrupted
- **Severity**: CRITICAL

**HIGH RISK: User Confusion from Wrong State**
- **Likelihood**: 80% (users will encounter BUG-1)
- **Impact**: Servers show wrong enabled/disabled state
- **Severity**: HIGH

**MEDIUM RISK: Support Burden**
- **Likelihood**: 50%
- **Impact**: Support questions, bug reports, frustration
- **Severity**: MEDIUM

---

## UPDATED Release Date Estimate

**Original Target**: 2025-11-03
**NEW Target**: 2025-11-04 (1 day delay)
**Alternative**: 2025-11-05 (2 day delay if issues found)

**Confidence**: 80% (down from 85% due to new bugs, still HIGH)

**Rationale for 1 Day Delay**:
1. 3 NEW critical bugs found (not in original plan)
2. 5-9 hours of P0 fix work (vs 1 hour originally)
3. Quality > Speed for 1.0 release
4. Prevent production data corruption
5. Users expect RELIABILITY, not SPEED

**What Could Extend to 2025-11-05**:
- Bug fixes take longer than 5-9 hours (20% chance)
- Regressions found during testing (30% chance)
- P1 investigations reveal more P0 bugs (15% chance)

**Most Likely**: Ship on 2025-11-04 (1 day delay, HIGH confidence)

---

## Communication Plan

### Internal Team
- **Today (Day 4 Start)**: Notify team of 3 NEW critical bugs, 1 day delay
- **Day 4 Progress**: Hourly updates on bug fix progress
- **Day 4 End**: Confirm all P0 bugs fixed, verify new release date
- **Day 5**: Final testing and polish updates
- **Day 6**: Release preparation updates

### Release Notes Messaging
- **Highlight**: Quality focus (delayed 1 day to fix critical bugs)
- **Transparency**: Document known limitations (BUG-2 deferred to 1.1)
- **Commitment**: Reliability over speed for 1.0 release

---

## Lessons Learned

### What Went Well
1. ✅ Enable/disable evaluation FOUND critical bugs before 1.0 ship
2. ✅ Early detection (4 days before release) allows time to fix
3. ✅ Test infrastructure healthy (can catch regressions)

### What Could Be Better
1. ⚠️ Enable/disable not included in original Day 3 manual testing
2. ⚠️ Cross-scope behavior not tested in original test suite
3. ⚠️ Schema validation didn't catch missing arrays in user-global

### Process Improvements for Future
1. **More Comprehensive Manual Testing**: Test all features, not just commands
2. **Real-World Testing**: Test with actual user configurations
3. **Assumption Verification**: Verify architectural assumptions early

---

## Final Verdict: DELAY 1 DAY, FIX BUGS, SHIP QUALITY 1.0

**CRITICAL BUGS FOUND**: 3 new bugs in enable/disable functionality

**RECOMMENDED APPROACH**: Fix P0 bugs (BUG-ORIG, BUG-1, BUG-3) before 1.0, defer architectural fix (BUG-2) to 1.1

**TIMELINE IMPACT**: 1 day delay (ship 2025-11-04 instead of 2025-11-03)

**RISK**: LOW (simple fixes, comprehensive testing)

**QUALITY**: HIGH (all P0 bugs fixed, production correctness)

**CONFIDENCE**: 80% (still HIGH)

**RATIONALE**: Shipping with known critical bugs is UNACCEPTABLE. 1 day delay is worth the quality and correctness. Users expect MCPI to be RELIABLE.

---

**SHIP DATE**: 2025-11-04 (1 day delay, HIGH confidence)

**PATH FORWARD**: Fix P0 bugs (Day 4-5), polish & test (Day 5), ship (Day 6)

---

## Day-by-Day Checklist

### Day 4 (2025-10-28) - 6-10 hours

**P0 Bug Fixes**:
- [ ] BUG-ORIG: Fix `mcpi client info` TypeError (1 hour)
- [ ] BUG-1: Fix cross-scope state pollution (2-4 hours)
- [ ] BUG-3: Fix wrong scope modification (2-4 hours)

**Documentation**:
- [ ] Document BUG-2 limitation in known issues (30 min)

**Verification**:
- [ ] Run full test suite (maintain 85.3% pass rate)
- [ ] Manual test all bug fixes
- [ ] Verify no regressions

### Day 5 (2025-10-29) - 4-7 hours

**Quality**:
- [ ] Final test run
- [ ] Code formatting (black, ruff)
- [ ] Type checking (mypy)

**Documentation**:
- [ ] Update CLAUDE.md with coverage info
- [ ] Update README with enable/disable limitations
- [ ] Create known issues list
- [ ] Verify all examples work

### Day 6 (2025-11-04) - 4-6 hours

**Release Prep**:
- [ ] Version bump to 1.0.0
- [ ] Create CHANGELOG.md
- [ ] Write release notes
- [ ] Tag and release
- [ ] Announcement

**SHIP 1.0!**

---

**END OF UPDATED RELEASE PLAN**

See `BUG-FIX-PLAN-ENABLE-DISABLE.md` for detailed bug fix implementation.
