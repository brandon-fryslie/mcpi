# MCPI Project Backlog

**Last Updated**: 2025-11-05
**Status Source**: STATUS-2025-10-30-062049.md (Emergency Assessment - CLI issues now resolved)
**Current Status**: CLI functional, project stable, ready for feature work

---

## Current Status - 2025-11-05

### Project Health
- **CLI Status**: FUNCTIONAL - packaging issues resolved
- **Commands Working**: Core functionality operational
- **Production Ready**: Baseline functionality established
- **Current Focus**: Feature enhancement (rescope auto-detection)

### Recent Resolution
The emergency packaging issues identified in STATUS-2025-10-30 have been resolved. The project is now in a stable state suitable for feature development and enhancements.

---

## Active Work

### Critical: FZF TUI Reload Fix (HIGH PRIORITY)
**Backlog**: BACKLOG-FZF-IMPLEMENTATION-FIX-2025-11-05.md
**Status**: BLOCKING SHIP - Critical bug prevents feature from working
**Current State**: 65% complete - UI works, reload mechanism broken
**Effort**: 2-4 hours for minimum viable fix, 9-15 hours for production quality

The fzf interactive TUI is implemented but has a critical blocker: the `mcpi-tui-reload` command doesn't exist, making the real-time refresh mechanism non-functional. Users can browse servers but operations (add/remove/enable/disable) don't refresh the list.

**Critical Blocker**:
- Missing `mcpi-tui-reload` command breaks all operation bindings
- Operations execute successfully but UI doesn't update
- Users must exit and re-launch to see changes

**Quick Fix Path** (2-4 hours to ship):
1. P0-1: Implement mcpi-tui-reload command (1-2 hours) - CRITICAL
2. P0-2: Add integration tests (1 hour basic coverage)
3. P1-1: Fix false "real-time updates" claim in README (30 min)
4. Manual testing verification (30 min)

**Full Production Path** (9-15 hours for polish):
- All quick fix items PLUS
- P2-1: Use Python API instead of subprocess (2-3 hours faster)
- P2-2: Reduce code duplication in bindings (1 hour)
- P2-3: Improve server ID extraction robustness (1-2 hours)
- P2-4: Add error handling for reload failures (1 hour)

### Feature: Rescope Auto-Detection (LOWER PRIORITY)
**Backlog**: BACKLOG-RESCOPE-AUTO-DETECT-2025-11-05.md
**Status**: Ready to implement (deferred until FZF fix complete)
**Approach**: OPTION B (Conservative) - Auto-detect single scope, error on multiple
**Effort**: 3.5-5.5 hours total

This feature makes the `--from` parameter optional in the rescope command. The system will auto-detect the source scope when a server exists in exactly one scope, making the common case (95% of usage) simpler while maintaining safety for edge cases.

**NOTE**: This is lower priority than the FZF fix. Complete FZF work first.

**Key Work Items** (see detailed backlog):
1. P0-1: Add find_all_server_scopes() method (30-45 min)
2. P0-2: Make --from optional (15 min)
3. P0-3: Implement auto-detection logic (1-1.5 hours)
4. P0-4: Unit tests for new method (30 min)
5. P0-5: Integration tests (1-1.5 hours)
6. P0-6: Update existing tests (30 min)
7. P0-7: Update documentation (30 min)
8. P0-8: Manual testing and verification (30 min)

---

## Current Backlog Structure

This file serves as the index to current planning. For detailed work items, see:

### Active Plans (Priority Order)

1. **BACKLOG-FZF-IMPLEMENTATION-FIX-2025-11-05.md**: CRITICAL - Fix broken fzf TUI reload mechanism
   - **Priority**: P0 - BLOCKING SHIP
   - **Status**: 65% complete - UI works, reload broken
   - **Critical Blocker**: Missing mcpi-tui-reload command
   - **Quick Fix**: 2-4 hours (implement reload, basic tests, fix docs)
   - **Full Fix**: 9-15 hours (add all quality improvements)
   - 8 prioritized work items (P0-P3)
   - Detailed testing strategy (unit + integration)
   - Clear success criteria for shipping

2. **BACKLOG-RESCOPE-AUTO-DETECT-2025-11-05.md**: Feature enhancement for rescope command
   - **Priority**: P1 - After FZF fix
   - **Status**: Ready to implement
   - 8 prioritized work items with acceptance criteria
   - Estimated 3.5-5.5 hours total effort
   - Conservative approach (OPTION B)
   - Comprehensive testing strategy
   - Low risk, high value enhancement

### Reference Documents
- **STATUS-2025-11-05-162258.md**: Latest assessment - FZF TUI evaluation (65% complete)
- **STATUS-2025-10-30-062049.md**: Previous assessment - CLI packaging issues (now resolved)
- **CLAUDE.md**: Project architecture and development workflow
- **pyproject.toml**: Package configuration

### Archived Documents (Contradicts Reality)
The following documents claimed production readiness but were based on false assumptions:
- STATUS-2025-10-29-015500.md (claimed 90% ready - INCORRECT)
- BACKLOG.md (2025-10-29 version - OBSOLETE)
- RELEASE-PLAN-1.0-FINAL.md (2025-10-29 - INCORRECT timeline)
- PLANNING-SUMMARY-2025-10-29.md (optimistic summary - INCORRECT)
- COMPLETION-AUDIT-2025-10-29.md (audit of incorrect status - INCORRECT)

**Action**: These files should be moved to `archive/` with `.archived` suffix to prevent confusion.

---

## Work Items Summary (see PLAN-2025-10-30-062544.md for details)

### P0: EMERGENCY BLOCKERS (4-8 hours)
1. **P0-EMERGENCY-1**: Fix broken packaging (1-4 hours) - BLOCKS ALL WORK
2. **P0-EMERGENCY-2**: Verify ALL 17 commands work (4-8 hours) - BLOCKS CLAIMS
3. **P0-EMERGENCY-3**: Investigate 82 test failures (8-16 hours) - BLOCKS QUALITY

### P1: CRITICAL BUGS (1-2 hours)
1. **P1-BUG-1**: Fix `mcpi client info` TypeError (1 hour) - DOCUMENTED FEATURE BROKEN

### P2: IMPORTANT CLEANUP (6-10 hours)
1. **P2-CLEANUP-1**: Delete 1,748 lines dead code (2 hours) - 18% OF CODEBASE
2. **P2-CLEANUP-2**: Add packaging tests (4-8 hours) - PREVENT REGRESSION
3. **P2-DOC-1**: Align documentation with reality (4-6 hours) - MISLEADING DOCS

### P0: RELEASE PREPARATION (4-6 hours)
1. **P0-SHIP-1**: Version bump & CHANGELOG (2 hours)
2. **P0-SHIP-2**: Tag and release (1 hour)

### P3: NICE-TO-HAVE (Defer to 1.0.1+)
1. **P3-REFACTOR-1**: Refactor cli.py (3-5 days) - WORKS FINE, JUST LARGE
2. **P3-TEST-1**: Add integration tests (3-5 days) - MANUAL TESTS SUFFICIENT
3. **P3-COV-1**: Achieve 80%+ coverage (3-5 days) - 50% ACCEPTABLE FOR 1.0

---

## Timeline

### Revised Realistic Timeline
- **Emergency Day (Day 0)**: Fix packaging + verify commands (4-8 hours)
- **Day 1**: Investigate failures + fix bugs (8-16 hours)
- **Day 2**: Quality cleanup (6-10 hours)
- **Day 3**: Release prep + ship (4-6 hours)

**Total**: 22-40 hours over 3-4 days
**Target Ship**: 2025-11-02 or 2025-11-03
**Confidence**: 40% (many unknowns until packaging fixed)

### Comparison to Previous Plans
| Plan | Claimed Timeline | Reality |
|------|------------------|---------|
| Days 1-4 (OBSOLETE) | 90% ready | 0% - app doesn't run |
| Days 5-6 (OBSOLETE) | 2 days to ship | IMPOSSIBLE - CLI broken |
| Emergency Plan (NEW) | 3-4 days | REALISTIC |
| Timeline Slip | +1-2 days | NECESSARY FOR QUALITY |

---

## Key Metrics (Honest Assessment)

| Metric | Previous Claim | Actual Reality | Evidence |
|--------|----------------|----------------|----------|
| Production Ready | 90% | 0% | CLI doesn't load |
| Commands Working | 16/17 | 0/17 | Cannot verify - CLI broken |
| Test Pass Rate | 83.6% | 84.1% | Tests pass, app fails |
| Test Errors | 0 | 0 | True but misleading |
| Days to Ship | 2 | 3-4 minimum | Account for unknowns |
| Confidence | 85% | 40% | Too many unknowns |

---

## Critical Lessons Learned

1. **Tests Passing ≠ Application Working**
   - Pytest injects pythonpath manually
   - Tests work in isolation, app fails in production
   - Need packaging tests to catch integration failures

2. **Always Verify Claims**
   - Don't claim "90% ready" without running the app
   - Don't dismiss 82 test failures without investigation
   - Don't extrapolate from tests to production

3. **Documentation Must Match Reality**
   - README examples untested
   - PROJECT_SPEC describes obsolete architecture
   - CLAUDE.md instructions don't work

4. **Honest Assessment > Optimistic Planning**
   - Better to under-promise and over-deliver
   - Account for unknowns in estimates
   - Add buffer for investigation work

---

## Success Criteria for 1.0 (Revised)

**MUST HAVE**:
- [ ] Packaging works (CLI loads)
- [ ] All 17 commands manually tested
- [ ] Critical bugs fixed
- [ ] Known issues documented honestly
- [ ] Documentation accurate

**SHOULD HAVE**:
- [ ] 82 test failures investigated
- [ ] Dead code deleted
- [ ] Packaging tests added
- [ ] Coverage > 50%

**NICE TO HAVE** (defer to 1.0.1):
- [ ] cli.py refactored
- [ ] Integration tests
- [ ] 80%+ coverage

---

## Next Actions

1. **Read PLAN-2025-10-30-062544.md** for detailed work items
2. **Start with P0-EMERGENCY-1**: Fix packaging (choose solution, implement)
3. **Then P0-EMERGENCY-2**: Manual test ALL commands
4. **Then proceed** through P0-EMERGENCY-3, P1, P2, and P0-SHIP items

**DO NOT**:
- Assume anything works without testing
- Dismiss test failures without investigation
- Claim production readiness without verification
- Skip manual testing of CLI

---

**For detailed implementation steps, acceptance criteria, and technical notes, see:**
**PLAN-2025-10-30-062544.md**
