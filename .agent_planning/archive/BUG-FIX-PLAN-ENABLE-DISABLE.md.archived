# Enable/Disable Bug Fix Plan - MCPI 1.0 Release

**Date**: 2025-10-28
**Source**: EVALUATION-ENABLE-DISABLE-2025-10-28-CORRECTED.md
**Context**: Days 1-3 complete, Day 4 starting, 1.0 release 2025-11-03 (4 days)
**Priority**: CRITICAL - Must assess impact on 1.0 timeline

---

## Executive Summary: CRITICAL BUGS FOUND

### Discovered Bugs (NOT in Original Release Plan)

**Original Day 4 Plan**: 1 critical bug (`mcpi client info` TypeError)
**NEW Finding**: 3 ADDITIONAL critical bugs in enable/disable functionality

### Critical Bugs Overview

| Bug ID | Description | Severity | Impact | Fix Time |
|--------|-------------|----------|--------|----------|
| BUG-1 | Cross-scope state pollution | **P0-CRITICAL** | Production correctness | 2-4 hours |
| BUG-2 | No disable mechanism for user-global | **P1-HIGH** | Feature gap | 8-16 hours |
| BUG-3 | Wrong scope modification | **P0-CRITICAL** | Data corruption risk | 2-4 hours |
| ORIG | `mcpi client info` TypeError | **P0-CRITICAL** | Documented feature broken | 1 hour |

**Total NEW bugs**: 3 critical bugs
**Total NEW fix time**: 4-8 hours (P0 only) to 12-24 hours (all)

---

## Impact on 1.0 Release Timeline

### Original Day 4 Plan
- **Critical bug fix**: 1 hour (`mcpi client info`)
- **Optional investigations**: 2-4 hours
- **Total Day 4**: 3-5 hours

### NEW Day 4 Reality
- **Original critical bug**: 1 hour (`mcpi client info`)
- **NEW critical bugs**: 4-8 hours (BUG-1, BUG-3)
- **NEW feature gap**: 8-16 hours (BUG-2, architectural)
- **Total NEW work**: 5-9 hours (P0 only) to 13-25 hours (all)

### Timeline Impact Assessment

**Option A: Fix All Bugs Before 1.0**
- Days added: 2-3 days (13-25 hours of work)
- NEW release date: 2025-11-05 to 2025-11-06 (2-3 day delay)
- Risk: MEDIUM (architectural changes, potential regressions)
- Quality: HIGH (all bugs fixed, no known issues)

**Option B: Fix P0 Bugs Only (Cross-Scope Pollution)**
- Days added: 1 day (5-9 hours of work)
- NEW release date: 2025-11-04 (1 day delay)
- Risk: LOW (minimal code changes)
- Quality: MEDIUM (2/3 enable/disable bugs fixed, 1 architectural issue deferred)

**Option C: Ship 1.0 With Known Bugs**
- Days added: 0 (maintain 2025-11-03 schedule)
- Risk: HIGH (production bugs, user confusion)
- Quality: LOW (shipping known critical bugs)
- User impact: HIGH (enable/disable shows wrong state)

**Option D: Disable Enable/Disable Features**
- Days added: 0 (maintain 2025-11-03 schedule)
- Risk: LOW (remove broken feature)
- Quality: MEDIUM (no bugs, but feature gap)
- User impact: MEDIUM (feature unavailable)

---

## Recommended Approach: PHASED FIX (Option B+)

### Phase 1: P0 Fixes for 1.0 (Day 4-5, 5-9 hours)

**MUST FIX for 1.0** (ship-blocking):
1. **BUG-ORIG**: `mcpi client info` TypeError (1 hour)
2. **BUG-1**: Cross-scope state pollution (2-4 hours)
3. **BUG-3**: Wrong scope modification (2-4 hours)

**Total**: 5-9 hours over 2 days (Day 4-5)
**New release date**: 2025-11-04 (1 day delay)
**Risk**: LOW (minimal code changes, scope-aware fixes)
**Quality**: HIGH (all P0 bugs fixed, production correctness)

### Phase 2: Architectural Fix for 1.1 (Post-1.0, 8-16 hours)

**DEFER to 1.1** (important but not ship-blocking):
1. **BUG-2**: Implement disable tracking for user-global (8-16 hours)
   - Add `~/.claude/disabled-servers.json` tracking file
   - Implement scope-specific enable/disable handlers
   - Full architectural refactor (proper solution)

**Timeline**: 1.1 release (~2025-11-11, 1 week after 1.0)
**Rationale**: Architectural change, high complexity, can work around in 1.0

### Phase 3: Workaround for 1.0 (30 minutes)

**DOCUMENT in 1.0 known issues**:
- Enable/disable only works for `user-local` and `project-local` scopes
- User-global servers cannot be disabled (remove from config manually)
- Clear error message when attempting to disable user-global servers
- Plan to fix in 1.1 with architectural refactor

**Total**: 30 minutes (documentation update)

---

## Detailed Bug Fix Plan

### BUG-ORIG: `mcpi client info` TypeError - 1 HOUR

**Status**: From original Day 4 plan
**Priority**: P0 - BLOCKING
**Effort**: 1 hour
**File**: `src/mcpi/cli.py` line 560

**Fix**:
```python
# Add error check before scope iteration:
if "error" in client_data:
    info_text += f"[bold]Error:[/bold] {client_data['error']}\n"
    return info_text  # Early return
# ... existing scope iteration code
```

**Testing**:
- Manual: `mcpi client info claude-code`
- Unit test: Add error scenario test
- Regression: `pytest --tb=no -q` (maintain 85.3% pass rate)

**Acceptance Criteria**:
- [ ] No TypeError on error conditions
- [ ] Error message displayed gracefully
- [ ] Test case added
- [ ] No regression in test suite

---

### BUG-1: Cross-Scope State Pollution - 2-4 HOURS

**Status**: NEW from enable/disable evaluation
**Priority**: P0 - CRITICAL (production correctness)
**Effort**: 2-4 hours
**File**: `src/mcpi/clients/claude_code.py` line 167-205

**Problem**: `_get_server_state()` checks enable/disable arrays across ALL scopes, causing servers in one scope to be affected by disable arrays in other scopes.

**Real Impact**: User has `@scope/package-name` in user-global, but it shows as DISABLED because user-local's `disabledMcpjsonServers` contains it.

**Fix** (Solution B from evaluation):
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
1. **Scope Isolation Test**:
   - Install server in user-global
   - Disable in user-local
   - Verify user-global shows as ENABLED (not cross-polluted)

2. **Real System Test**:
   - Fix user's polluted state
   - Verify `@scope/package-name` shows correctly
   - Verify other scopes unaffected

**Acceptance Criteria**:
- [ ] State is scope-specific (no cross-scope pollution)
- [ ] User-global servers show correct state
- [ ] User-local disable arrays only affect user-local
- [ ] Test cases added for scope isolation
- [ ] No regression in existing tests

**Estimated Effort**:
- Code changes: 30 minutes (update `_get_server_state()`)
- Test updates: 1-2 hours (add scope isolation tests)
- Manual verification: 30 minutes (test real system)
- Total: **2-4 hours**

---

### BUG-3: Wrong Scope Modification - 2-4 HOURS

**Status**: NEW from enable/disable evaluation
**Priority**: P0 - CRITICAL (data corruption risk)
**Effort**: 2-4 hours
**File**: `src/mcpi/clients/claude_code.py` line 323-427

**Problem**: `enable_server()` and `disable_server()` iterate through settings_scopes and modify the FIRST scope they find. This causes operations on user-global servers to actually modify user-local.

**Real Impact**: User disables user-global server, but code adds it to user-local's `disabledMcpjsonServers` array instead.

**Fix**:
```python
def disable_server(self, server_id: str, scope: Optional[str] = None) -> OperationResult:
    """Disable server (SCOPE-AWARE)"""
    # Find server's actual scope
    actual_scope = self._find_server_scope(server_id)
    if not actual_scope:
        return OperationResult(
            success=False,
            message=f"Server {server_id} not found in any scope"
        )

    # Check if scope supports enable/disable
    handler = self._scopes[actual_scope]
    data = handler.reader.read(handler.config.path)

    if "disabledMcpjsonServers" not in data:
        # Scope doesn't support enable/disable
        return OperationResult(
            success=False,
            message=f"Enable/disable not supported for scope '{actual_scope}'. "
                   f"To disable this server, remove it from the config file: {handler.config.path}"
        )

    # Scope supports enable/disable, proceed
    if server_id not in data.get("disabledMcpjsonServers", []):
        data.setdefault("disabledMcpjsonServers", []).append(server_id)
        handler.writer.write(handler.config.path, data)

    return OperationResult(
        success=True,
        message=f"Disabled {server_id} in {actual_scope}"
    )
```

**Helper Function**:
```python
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
1. **Scope-Specific Modification Test**:
   - Install server in user-global
   - Attempt to disable
   - Verify clear error message (not supported)
   - Verify user-local NOT modified

2. **Supported Scope Test**:
   - Install server in user-local
   - Disable server
   - Verify user-local modified (correct scope)
   - Verify user-global NOT modified

**Acceptance Criteria**:
- [ ] Enable/disable operations modify correct scope
- [ ] Clear error for unsupported scopes
- [ ] No cross-scope modifications
- [ ] Test cases added for scope-specific operations
- [ ] No regression in existing tests

**Estimated Effort**:
- Code changes: 1 hour (update `enable_server()`, `disable_server()`, add helper)
- Test updates: 1-2 hours (add scope-specific tests)
- Manual verification: 30 minutes (test real system)
- Total: **2-4 hours**

---

### BUG-2: No Disable Mechanism for user-global - 8-16 HOURS (DEFER TO 1.1)

**Status**: NEW from enable/disable evaluation
**Priority**: P1 - HIGH (feature gap, not production bug)
**Effort**: 8-16 hours (ARCHITECTURAL)
**Defer to**: 1.1 release (~2025-11-11)

**Problem**: user-global scope has NO way to track disabled servers. Schema defines `enabledMcpjsonServers`/`disabledMcpjsonServers` arrays, but real user-global files DON'T have them.

**Current Workaround for 1.0**:
- Document limitation in known issues
- Show clear error when attempting to disable user-global servers
- Suggest manual removal from config file
- Plan architectural fix for 1.1

**Architectural Fix for 1.1** (Solution A from evaluation):
1. Create `~/.claude/disabled-servers.json` tracking file
2. Enable = add to settings.json + remove from disabled tracking
3. Disable = remove from settings.json + add to disabled tracking (preserve config)
4. List = merge mcpServers (enabled) + disabled tracking (disabled)

**Why Defer to 1.1**:
- Architectural change (new file, new logic)
- High complexity (8-16 hours)
- Not production bug (workaround exists)
- Can ship 1.0 with documented limitation
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

**Future Plans (1.1)**:
- Implement disabled server tracking for user-global scope
- Add scope-specific enable/disable handlers
- Full architectural refactor for correct behavior

**Issue**: [Link to GitHub issue #XXX]
```

---

## Updated Day 4-6 Timeline

### Day 4: CRITICAL BUG FIXES (6-10 hours)

**BLOCKING P0 Fixes** (5-9 hours):
1. BUG-ORIG: `mcpi client info` TypeError (1 hour)
2. BUG-1: Cross-scope state pollution (2-4 hours)
3. BUG-3: Wrong scope modification (2-4 hours)

**Documentation** (30 minutes):
4. Document known issues (BUG-2 deferred to 1.1)

**Optional** (2-4 hours):
5. P1 investigations (interactive scope, API contracts) - CAN DEFER to 1.0.1

**Total Day 4**: 6-10 hours (P0 only) or 8-14 hours (with optional)

### Day 5: POLISH & TESTING (4-6 hours)

**REQUIRED**:
1. Final test run after bug fixes (30 min)
2. Code formatting (black, ruff) (15 min)
3. Type checking (mypy) (15 min)
4. Update CLAUDE.md with coverage info (30 min)
5. Create known issues list (1 hour)
6. Update README with enable/disable limitations (30 min)

**OPTIONAL**:
7. Update PROJECT_SPEC (2-3 hours) - CAN DEFER to 1.0.1

**Total Day 5**: 3-7 hours

### Day 6: RELEASE PREPARATION (4-6 hours)

**REQUIRED**:
1. Version bump to 1.0.0 (30 min)
2. Create CHANGELOG.md (1-2 hours)
3. Write release notes (1 hour)
4. Tag and release (1 hour)
5. Announcement (30 min)

**Total Day 6**: 4-6 hours

### NEW Timeline Summary

**Days 4-6 Total**: 13-23 hours (vs original 10-17 hours)
**Days Available**: 3 days (Day 4, 5, 6)
**Hours Per Day**: 4.3-7.7 hours per day
**Buffer**: 1.0-1.7x (vs original 2.4x)

**NEW Release Date**: 2025-11-04 (1 day delay) or 2025-11-05 (2 day delay if issues)

---

## Risk Assessment

### Risks of Fixing Bugs Before 1.0

**MEDIUM RISK: Regression from Bug Fixes**
- **Likelihood**: 30%
- **Impact**: 1-2 day delay
- **Mitigation**:
  - Comprehensive test suite (85.3% pass rate)
  - Scope isolation tests
  - Manual verification
  - Can roll back if regression found

**LOW RISK: Fix Takes Longer Than Estimated**
- **Likelihood**: 20%
- **Impact**: 1 day delay
- **Mitigation**:
  - Estimates are conservative (2-4 hours per bug)
  - Simple fixes (scope-aware logic)
  - Clear fix strategy from evaluation

**MEDIUM RISK: BUG-1 and BUG-3 Fixes Reveal More Bugs**
- **Likelihood**: 25%
- **Impact**: 1-2 day delay
- **Mitigation**:
  - Defer P1 investigations if needed
  - Focus on P0 fixes only
  - Can extend to 2025-11-05 if needed

### Risks of Shipping With Bugs

**HIGH RISK: Production Data Corruption**
- **Likelihood**: 60% (users will encounter BUG-3)
- **Impact**: User configuration files corrupted
- **Example**: User disables user-global server, user-local config corrupted
- **Severity**: CRITICAL

**HIGH RISK: User Confusion from Wrong State**
- **Likelihood**: 80% (users will encounter BUG-1)
- **Impact**: Servers show wrong enabled/disabled state
- **Example**: Server shows DISABLED even though it's running
- **Severity**: HIGH

**MEDIUM RISK: Support Burden**
- **Likelihood**: 50%
- **Impact**: Support questions, bug reports, user frustration
- **Severity**: MEDIUM

### Risks of Disabling Enable/Disable

**MEDIUM RISK: Feature Gap**
- **Likelihood**: 100%
- **Impact**: Users cannot disable servers (must remove from config)
- **Severity**: MEDIUM (workaround exists)

**LOW RISK: User Disappointment**
- **Likelihood**: 30%
- **Impact**: Missing expected feature
- **Severity**: LOW (can add in 1.1)

---

## Comparison Matrix: Fix vs Ship vs Disable

| Criteria | Fix P0 Bugs (B+) | Ship With Bugs (C) | Disable Feature (D) |
|----------|------------------|---------------------|---------------------|
| **Timeline** | 2025-11-04 (+1 day) | 2025-11-03 (on time) | 2025-11-03 (on time) |
| **Risk** | LOW | HIGH | LOW |
| **Quality** | HIGH | LOW | MEDIUM |
| **User Impact** | LOW | HIGH | MEDIUM |
| **Support Burden** | LOW | HIGH | MEDIUM |
| **Technical Debt** | MEDIUM | HIGH | LOW |
| **Correctness** | HIGH | LOW | HIGH |
| **Feature Completeness** | MEDIUM | MEDIUM | LOW |
| **Release Confidence** | 85% | 40% | 75% |

**Recommendation**: **Fix P0 Bugs (Option B+)** - 1 day delay, high quality, low risk

---

## Final Recommendation: PHASED FIX

### Phase 1: P0 Fixes for 1.0 (RECOMMENDED)

**What**: Fix BUG-ORIG, BUG-1, BUG-3 (5-9 hours)
**When**: Day 4-5 (2025-10-28 to 2025-10-29)
**Ship**: 2025-11-04 (1 day delay)
**Risk**: LOW
**Quality**: HIGH
**Rationale**: Ensures production correctness, prevents data corruption, maintains user trust

### Phase 2: Architectural Fix for 1.1 (DEFER)

**What**: Fix BUG-2 with proper architecture (8-16 hours)
**When**: 1.1 release (~2025-11-11, 1 week after 1.0)
**Risk**: MEDIUM (architectural change)
**Quality**: EXCELLENT
**Rationale**: Do it right with no time pressure, comprehensive solution

### Phase 3: Documentation for 1.0 (30 minutes)

**What**: Document known limitations in release notes
**When**: Day 5 (2025-10-29)
**Risk**: NONE
**Quality**: MEDIUM
**Rationale**: Clear user expectations, plan for 1.1 improvement

---

## Updated Release Date Estimate

**Original Target**: 2025-11-03
**NEW Target**: 2025-11-04 (1 day delay)
**Alternative**: 2025-11-05 (2 day delay if issues found)

**Confidence**: 80% (HIGH, down from 85% due to new bugs)

**Rationale for 1 Day Delay**:
- 3 NEW critical bugs found (not in original plan)
- 5-9 hours of P0 fix work (vs 1 hour originally)
- Maintain high quality and correctness
- Prevent production data corruption
- Low risk of further delays

**What Could Extend to 2025-11-05**:
- Bug fixes take longer than 5-9 hours (20% chance)
- Regressions found during testing (30% chance)
- P1 investigations reveal more P0 bugs (15% chance)

**Most Likely**: Ship on 2025-11-04 (1 day delay, HIGH confidence)

---

## Testing Strategy for Bug Fixes

### Test Cases to Add

**BUG-1: Cross-Scope State Pollution**
```python
def test_scope_isolation_no_cross_pollution():
    """Verify servers in one scope not affected by disable arrays in other scopes"""
    # Install server in user-global
    install_server("test-server", scope="user-global")

    # Disable in user-local
    disable_server("test-server", scope="user-local")

    # Verify user-global shows ENABLED (not cross-polluted)
    state = get_server_state("test-server", scope="user-global")
    assert state == ServerState.ENABLED

    # Verify user-local shows DISABLED (correct)
    state = get_server_state("test-server", scope="user-local")
    assert state == ServerState.DISABLED
```

**BUG-3: Wrong Scope Modification**
```python
def test_disable_unsupported_scope_error():
    """Verify clear error when disabling server in unsupported scope"""
    # Install server in user-global (no enable/disable support)
    install_server("test-server", scope="user-global")

    # Attempt to disable
    result = disable_server("test-server")

    # Verify error message
    assert not result.success
    assert "not supported" in result.message.lower()
    assert "remove it from the config file" in result.message.lower()

    # Verify user-local NOT modified
    user_local_data = read_config("user-local")
    assert "test-server" not in user_local_data.get("disabledMcpjsonServers", [])

def test_disable_supported_scope_success():
    """Verify disable works correctly in supported scopes"""
    # Install server in user-local (has enable/disable support)
    install_server("test-server", scope="user-local")

    # Disable server
    result = disable_server("test-server")

    # Verify success
    assert result.success

    # Verify correct scope modified
    user_local_data = read_config("user-local")
    assert "test-server" in user_local_data["disabledMcpjsonServers"]

    # Verify other scopes NOT modified
    user_global_data = read_config("user-global")
    assert "disabledMcpjsonServers" not in user_global_data
```

### Manual Testing Checklist

**After BUG-1 Fix**:
- [ ] Install server in user-global
- [ ] Add to user-local's disabledMcpjsonServers
- [ ] Run `mcpi list --scope user-global`
- [ ] Verify server shows ENABLED (not DISABLED)
- [ ] Run `mcpi list --scope user-local`
- [ ] Verify server shows DISABLED (correct)

**After BUG-3 Fix**:
- [ ] Install server in user-global
- [ ] Run `mcpi disable <server>`
- [ ] Verify clear error message (not supported)
- [ ] Verify user-local config NOT modified
- [ ] Install server in user-local
- [ ] Run `mcpi disable <server>`
- [ ] Verify success message
- [ ] Verify user-local config modified (correct)

**Regression Testing**:
- [ ] Run full test suite: `pytest --tb=no -q`
- [ ] Verify pass rate ≥ 85.3% (no regression)
- [ ] Manual test all 17 commands
- [ ] Verify no new bugs introduced

---

## Success Criteria for P0 Bug Fixes

**BUG-ORIG: `mcpi client info`**:
- [ ] No TypeError on error conditions
- [ ] Error message displayed gracefully
- [ ] Test case added
- [ ] Manual testing confirms fix

**BUG-1: Cross-Scope State Pollution**:
- [ ] State is scope-specific (no cross-scope pollution)
- [ ] User-global servers show correct state
- [ ] User-local disable arrays only affect user-local
- [ ] Test cases added for scope isolation
- [ ] Manual testing confirms fix

**BUG-3: Wrong Scope Modification**:
- [ ] Enable/disable operations modify correct scope
- [ ] Clear error for unsupported scopes
- [ ] No cross-scope modifications
- [ ] Test cases added for scope-specific operations
- [ ] Manual testing confirms fix

**Regression Prevention**:
- [ ] Test pass rate ≥ 85.3% (no regression)
- [ ] All 17 commands still work
- [ ] No new bugs introduced
- [ ] CI/CD pipeline passes

---

## Communication Plan

### Internal Team
- **Day 4 Start**: Notify team of 3 NEW critical bugs found
- **Day 4 Progress**: Update on bug fix progress (hourly standups)
- **Day 4 End**: Confirm all P0 bugs fixed, new release date
- **Day 5**: Final testing and polish updates
- **Day 6**: Release preparation updates

### External (If Applicable)
- **Release Notes**: Document known limitations (BUG-2 deferred to 1.1)
- **Changelog**: List bug fixes in 1.0 release
- **GitHub Issues**: Create issue for BUG-2 (architectural fix for 1.1)
- **Announcement**: Highlight quality focus (delayed 1 day to fix critical bugs)

---

## Lessons Learned

### What Went Well
1. ✅ Enable/disable evaluation FOUND critical bugs before 1.0 ship
2. ✅ Early detection (4 days before release) allows time to fix
3. ✅ Clear fix strategy from comprehensive evaluation
4. ✅ Test infrastructure healthy (can catch regressions)

### What Could Be Better
1. ⚠️ Enable/disable not included in original Day 3 manual testing
2. ⚠️ Cross-scope behavior not tested in original test suite
3. ⚠️ Schema validation didn't catch missing arrays in user-global
4. ⚠️ Assumption that all scopes have enable/disable arrays (wrong)

### Process Improvements for Future
1. **More Comprehensive Manual Testing**: Test all features, not just commands
2. **Real-World Testing**: Test with actual user configurations
3. **Schema Validation**: Ensure schema matches reality
4. **Assumption Verification**: Verify architectural assumptions early

---

## Conclusion

**CRITICAL BUGS FOUND**: 3 new bugs in enable/disable functionality (cross-scope pollution, wrong scope modification, no disable mechanism for user-global).

**RECOMMENDED APPROACH**: Fix P0 bugs (BUG-ORIG, BUG-1, BUG-3) before 1.0, defer architectural fix (BUG-2) to 1.1.

**TIMELINE IMPACT**: 1 day delay (ship 2025-11-04 instead of 2025-11-03).

**RISK**: LOW (simple fixes, comprehensive testing, can roll back if needed).

**QUALITY**: HIGH (all P0 bugs fixed, production correctness, no data corruption).

**CONFIDENCE**: 80% (down from 85%, but still HIGH).

**RATIONALE**: Shipping with known critical bugs is UNACCEPTABLE. 1 day delay is worth the quality and correctness. Users expect MCPI to be RELIABLE, not FAST. Do it right.

---

**SHIP DATE**: 2025-11-04 (1 day delay, HIGH confidence)

**PATH FORWARD**: Fix P0 bugs (Day 4-5), polish & test (Day 5), ship (Day 6).

---

**END OF BUG FIX PLAN**
