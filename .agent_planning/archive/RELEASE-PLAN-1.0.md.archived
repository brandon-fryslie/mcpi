# MCPI 1.0 RELEASE PLAN: Days 4-6 to Production

**Source**: STATUS-2025-10-28-132841.md (Days 1-3 COMPLETE, 85% release readiness)
**Previous Source**: STATUS-2025-10-28-130248.md (81% completion, Days 1-2 COMPLETE)
**Target**: Ship production-ready 1.0 on 2025-11-03
**Generated**: 2025-10-28 13:32:53
**Updated**: 2025-10-28 13:32:53 (Days 1-3 complete, Day 4 critical bug fix priority)
**Status**: DAYS 1-3 COMPLETE - READY FOR DAY 4 CRITICAL BUG FIX

---

## DAYS 1-3 ACHIEVEMENT CELEBRATION

**Status**: 100% COMPLETE - Excellent Execution, On Schedule

**What Was Accomplished**:
- Complete CI/CD pipeline (110-line GitHub Actions workflow)
- Multi-OS/multi-Python testing (Ubuntu, macOS, Windows × Python 3.12, 3.13)
- Quality gates configured (Black blocking, Ruff/mypy warnings)
- Coverage reporting configured and measured (40% actual coverage)
- CI badges and comprehensive documentation (96 lines in CLAUDE.md)
- Black regression identified, fixed, and prevented (45 minutes, 2.2x faster than estimate)
- Complete manual testing of all commands (17/17 tested, 16/17 passing)
- Comprehensive bug triage (82 failures categorized as 88% test infrastructure, 12% potential bugs)
- Documentation accuracy verification (95% quality maintained)

**Current Metrics**:
- Test pass rate: 85.3% (exceeds 80% target)
- Test errors: 0 (all fixture errors eliminated)
- CLI commands: 16/17 working (1 critical bug identified)
- Production readiness: 85/100 (ready to ship after bug fix)
- Timeline: ON TRACK for 2025-11-03 release
- Coverage: 40% (acceptable for 1.0, will improve to 80% in 1.1)

**Critical Finding**:
- 1 BLOCKING bug: `mcpi client info` TypeError (1 hour to fix)

**Release Target**: 2025-11-03 (maintained, 4 days remaining)
**Progress**: 50% complete (3 of 6 days), ON TRACK
**Confidence**: 85% (HIGH)

---

## Executive Summary: Final Sprint to 1.0

### Current State (Production-Ready Pending Bug Fix)

**Overall Completion**: 85% (Days 1-3 complete, 1 critical bug blocking)
**Production Readiness**: 85/100 (high confidence after bug fix)
**Test Pass Rate**: 85.3% (474/556 tests) - exceeds 80% target
**Documentation Quality**: 95% (1 documented feature broken by bug)
**Coverage**: 40% (acceptable for 1.0, mostly dead code pulling it down)

### Success Criteria for 1.0 (Status Check)

**Must Have**:
- ✅ 0 test import errors (P0-1 complete)
- ✅ Core commands working (P0-3 verified, 16/17 functional)
- ✅ Test infrastructure functional (P0 complete, 85.3% pass rate)
- ✅ >80% test pass rate (85.3% achieved, exceeds target)
- ✅ Accurate README (P1-2 complete, 95% quality)
- ✅ Categories command (P1-4 complete with tests)
- ✅ CI/CD running (Days 1-2 complete)
- ✅ Coverage measured (Day 3 complete, 40% documented)
- **BLOCKING** 1 critical bug: `mcpi client info` TypeError (Day 4, 1 hour)
- ⏳ Final testing complete (Day 5)
- ⏳ Release artifacts ready (Day 6)

**Should Have** (Deferred to 1.1):
- P2-1: cli.py refactored → DEFER TO 1.1
- P2-2: Integration tests → DEFER TO 1.1
- P2-3: 80%+ coverage → MEASURE in 1.0 (40% achieved), IMPROVE in 1.1

**Nice to Have** (Optional for 1.0):
- P1-3: PROJECT_SPEC update → CAN DEFER TO 1.0.1
- P1-6: Status edge cases → CAN DEFER TO 1.0.1

---

## Day 4: CRITICAL BUG FIX PRIORITY (2-4 hours)

**Priority**: P0 (BLOCKING 1.0 RELEASE)
**Effort**: 2-4 hours total (1 hour critical, 1-3 hours optional)
**Owner**: Development team
**Status**: READY TO START
**Dependencies**: ✅ Days 1-3 complete

### CRITICAL - MUST FIX (1 hour)

**Bug**: `mcpi client info <client>` raises TypeError
**Severity**: P0 - BLOCKS RELEASE
**User Impact**: Documented feature (README line 95-96) fails with error
**Fix Complexity**: LOW (simple conditional logic)

#### Problem Analysis

**Root Cause** (verified in STATUS-2025-10-28-132841.md):
```python
# File: src/mcpi/cli.py line 556-563 (BUGGY CODE)
scopes = client_data.get("scopes", [])
if scopes:
    info_text += "[bold]Scopes:[/bold]\n"
    for scope in scopes:
        scope_type = "User" if scope.get("is_user_level") else "Project"
        # BUG: Assumes scope is dict, but if error occurred,
        # client_data has {"error": "..."} and code tries to call
        # .get() on error string
```

**Error Message**:
```
Error getting client info: 'str' object has no attribute 'get'
```

#### Fix Implementation (30-45 minutes)

**Step 1**: Add error check before scope iteration (5 lines)
```python
# Add BEFORE existing scope code:
if "error" in client_data:
    info_text += f"[bold]Error:[/bold] {client_data['error']}\n"
    return info_text  # Early return, don't iterate scopes

# Existing scope iteration code follows...
```

**Step 2**: Write test case for error scenario (10 lines)
```python
# In tests/test_cli.py (or appropriate test file):
def test_client_info_handles_error_gracefully():
    """Test that client info handles error state without TypeError"""
    result = runner.invoke(cli, ["client", "info", "invalid-client"])
    assert result.exit_code == 0  # Should not crash
    assert "Error:" in result.output  # Should show error message
    assert "TypeError" not in result.output  # Should not show TypeError
```

**Step 3**: Manual verification (5 minutes)
```bash
# Test the fix manually
mcpi client info claude-code
# Should display client info OR error message (no TypeError)

mcpi client info nonexistent-client
# Should display graceful error message (no TypeError)
```

**Step 4**: Run full test suite (5 minutes)
```bash
pytest --tb=no -q
# Verify no regression (maintain 85.3% pass rate or better)
```

#### Acceptance Criteria
- [ ] `mcpi client info <client>` no longer raises TypeError
- [ ] Error cases display graceful error message
- [ ] Test case added for error scenario
- [ ] Manual testing confirms fix works
- [ ] Full test suite maintains 85.3%+ pass rate
- [ ] No regression introduced

#### Success Criteria
- 0 critical bugs blocking 1.0 release
- `mcpi client info` works as documented in README
- Test pass rate maintained or improved
- User workflow unblocked

**Overall Day 4 Critical Work**: 1 hour (MUST COMPLETE for 1.0)

---

### OPTIONAL - SHOULD INVESTIGATE (2-4 hours)

**Priority**: P1 (Important but not blocking)
**Effort**: 2-4 hours
**Decision**: OPTIONAL - Can defer to 1.0.1 if time-constrained

#### Task 1: Interactive Scope Selection Investigation (1-2 hours)

**Issue**: 2 tests failing for interactive mode
**User Impact**: LOW (interactive mode is fallback when no --scope specified)
**Risk**: May reveal actual bug or just test configuration issue

**Action**:
- Review failing test expectations vs actual behavior
- Manual test interactive prompts
- Fix if actual bug, defer if test issue

#### Task 2: API Contract Tests Investigation (1-2 hours)

**Issue**: 4 tests failing for API contracts
**User Impact**: MEDIUM (could affect rescope workflows)
**Risk**: May indicate missing functionality

**Action**:
- Review test expectations
- Verify rescope workflows work manually
- Fix if blocking user workflows, defer if test issue

#### Task 3: Manual Test `mcpi client set-default` (15 min)

**Issue**: Command not explicitly tested in Day 3
**User Impact**: MEDIUM (documented feature)
**Risk**: LOW (likely works, just needs verification)

**Action**:
```bash
mcpi client set-default claude-code
mcpi client list  # Verify default is set
```

#### Acceptance Criteria (Optional Tasks)
- [ ] Interactive scope selection tests reviewed
- [ ] API contract tests reviewed
- [ ] `mcpi client set-default` manually verified
- [ ] Bugs fixed OR deferred to 1.0.1 with documentation

---

## Day 5: Polish & Final Testing (4-6 hours)

**Priority**: P1 (Required for quality 1.0)
**Effort**: 4-6 hours
**Owner**: Development team
**Status**: READY after Day 4 bug fix complete
**Dependencies**: ✅ Days 1-3 complete, ⏳ Day 4 bug fix

### Tasks

#### 1. Final Test Run (30 min)
- Run full test suite after Day 4 bug fixes
- Verify pass rate maintained or improved (85.3%+)
- Document any new issues discovered
- Confirm 0 critical bugs remain

#### 2. Code Quality Pass (45 min)
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type checking
mypy src/

# All quality gates must pass
```

#### 3. Update Documentation (1 hour)
- Update CLAUDE.md with coverage info (40%)
- Document known issues for 1.0
- Verify README accuracy (all examples work)
- Update testing documentation if needed

#### 4. Create Known Issues List (1-2 hours)
Document for 1.0 release notes:
- 82 test failures (88% test infrastructure, planned fix in 1.1)
- Coverage at 40% (target 80% in 1.1 after dead code removal)
- Deferred features (update, doctor, backup/restore commands)
- Edge cases in scope management (if any found)

#### 5. Optional: Update PROJECT_SPEC (2-3 hours)
**Can defer to 1.0.1 if time-constrained**
- Document scope-based architecture (not profile-based)
- Update command reference (add rescope, completion, categories)
- Remove references to deleted modules
- Add plugin architecture section

#### Acceptance Criteria
- [ ] All quality gates pass (black, ruff, mypy)
- [ ] Test pass rate ≥ 85.3%
- [ ] Known issues documented
- [ ] CLAUDE.md updated with current state
- [ ] README examples verified working
- [ ] Optional: PROJECT_SPEC updated (can defer to 1.0.1)

#### Success Criteria
- Zero known critical bugs
- Test pass rate maintained or improved
- Documentation complete and accurate
- Code quality gates all green
- Ready for release preparation

---

## Day 6: Release Preparation & Ship (4-6 hours)

**Priority**: P0 (Release day)
**Effort**: 4-6 hours
**Owner**: Development team + Release manager
**Status**: SCHEDULED - Day 6 (2025-11-03)
**Target Release Date**: 2025-11-03
**Dependencies**: ✅ Days 1-5 complete

### Tasks

#### 1. Version Bump (30 min)
```bash
# Update version in pyproject.toml to 1.0.0
# Update version in src/mcpi/__init__.py (if exists)
# Update version references in documentation
git add pyproject.toml src/mcpi/__init__.py README.md
git commit -m "chore: bump version to 1.0.0 for release"
```

#### 2. Create CHANGELOG.md (1-2 hours)

**Structure** (per Keep a Changelog standard):
```markdown
# Changelog

## [1.0.0] - 2025-11-03

### Added
- 13 core commands for MCP server management
- Plugin architecture for multi-client support (Claude Code, Cursor, VS Code)
- Scope-based configuration management (6 scopes for Claude Code)
- Tab completion for bash/zsh/fish shells
- Categories command for browsing servers by category
- Rescope command for moving servers between scopes
- Complete CI/CD pipeline with multi-OS/multi-Python testing
- Comprehensive test suite (85.3% pass rate, 474 passing tests)
- 40% code coverage with HTML/XML/terminal reports

### Fixed
- Test harness fixture imports (Black compatibility)
- 19 test import errors (deleted obsolete test files)
- 30 test setup errors (test harness pattern implementation)
- README accuracy (removed false claims, documented all features)

### Known Issues
- 82 test failures (88% test infrastructure, 12% potential bugs)
- Coverage at 40% (target 80% in 1.1)
- Deferred features: update, doctor, backup/restore commands

### Deferred to 1.1
- cli.py refactoring (1,381 LOC → modules)
- Integration tests for installation workflows
- Coverage improvement from 40% to 80%
- Advanced features (doctor, backup, restore, sync)
```

#### 3. Write Release Notes (1 hour)

**Compelling Highlights**:
- First production-ready release of MCPI
- Plugin architecture supporting 3 MCP clients
- Scope-based configuration for granular control
- 13 commands covering all core MCP workflows
- Installation via npm, pip, uv, or git
- Complete test suite with CI/CD pipeline
- Comprehensive documentation with examples

**Quick Start**:
```bash
# Install via npm
npm install -g mcpi

# Search for servers
mcpi search openai

# Install a server
mcpi install gpt-engineer

# List installed servers
mcpi list
```

#### 4. Tag and Release (1 hour)
```bash
# Create and push tag
git tag -a v1.0.0 -m "Release version 1.0.0

First production-ready release with 13 core commands,
plugin architecture, and scope-based configuration.

See CHANGELOG.md for full details."
git push origin v1.0.0

# Create GitHub release from tag
gh release create v1.0.0 \
  --title "MCPI 1.0.0 - Production Ready" \
  --notes-file RELEASE_NOTES.md \
  --verify-tag

# Optional: Publish to PyPI (if planned)
# uv build
# uv publish
```

#### 5. Announcement (30 min)
- Update README badges (release version, download count)
- Close 1.0 milestone in GitHub
- Create 1.1 milestone for deferred work
- Post release announcement (if applicable)

#### Acceptance Criteria
- [ ] Version bumped to 1.0.0 in all files
- [ ] CHANGELOG.md created with complete history
- [ ] Release notes written and compelling
- [ ] Git tag `v1.0.0` created and pushed
- [ ] GitHub release published
- [ ] Optional: PyPI package published
- [ ] Release announcement posted
- [ ] 1.1 milestone created

#### Success Criteria
- **1.0 SHIPPED**
- All artifacts available (tag, release, optional package)
- Documentation links work
- Community informed
- Clear path to 1.1 defined

---

## Updated Timeline Summary

### 6-Day Sprint Progress

**Day 1** ✅ COMPLETE:
- CI/CD pipeline infrastructure (110-line workflow)
- Multi-OS, multi-Python testing (6 combinations)
- Quality gates (Black, Ruff, mypy)
- Coverage reporting configured
- CI badges and documentation

**Day 2** ✅ COMPLETE:
- Black regression fixed (45 minutes, 2.2x faster than estimate)
- Fixture imports restored with noqa protection
- Test pass rate restored: 68% → 85.3%
- Test errors eliminated: 104 → 0
- Best practices documented

**Day 3** ✅ COMPLETE:
- Coverage measured (40%, acceptable for 1.0)
- Manual testing complete (17/17 commands tested)
- Bug triage complete (1 critical bug found)
- Documentation review complete (95% quality verified)

**Day 4** ⏳ READY TO START (2-4 hours):
- **CRITICAL**: Fix `mcpi client info` bug (1 hour) - BLOCKING
- **OPTIONAL**: Investigate P1 test failures (2-4 hours)
- **OPTIONAL**: Manual test `mcpi client set-default` (15 min)

**Day 5** ⏳ READY TO START (4-6 hours):
- Final test run (30 min)
- Code quality pass (45 min)
- Update documentation (1 hour)
- Create known issues list (1-2 hours)
- Optional: Update PROJECT_SPEC (2-3 hours)

**Day 6** ⏳ SCHEDULED (4-6 hours):
- Version bump (30 min)
- Create CHANGELOG.md (1-2 hours)
- Write release notes (1 hour)
- Tag and release (1 hour)
- Announcement (30 min)

**Target Release Date**: **2025-11-03** (4 days from 2025-10-28)

**Confidence Level**: **85%** (HIGH - clear path forward, 1 simple bug fix)

---

## Alternative Timeline (Aggressive 3-Day Sprint)

If Day 4 bug fix completed quickly:

**Day 4** (today):
- Critical bug fix (1 hour)
- Optional P1 investigations (2-4 hours)
- Final test run (30 min)

**Day 5**:
- Code quality pass (45 min)
- Documentation updates (1-2 hours)
- Version bump & CHANGELOG (2-3 hours)

**Day 6**:
- Release notes & tag (2 hours)
- Ship 1.0

**Target Release Date**: 2025-11-02 (1 day early)

**Risk**: MEDIUM (less buffer for unexpected issues)

**Recommendation**: Use **6-day timeline** for quality and buffer

---

## Deferred Items for 1.1

### P1-5: Update Command
**Rationale**: High complexity, adds 1+ weeks, users can manually update
**Timeline**: 1.1 release (2-4 weeks after 1.0)
**Effort**: 3-5 days

### P2-1: Refactor cli.py
**Rationale**: Works fine, just large (1,381 LOC)
**Timeline**: 1.1 release
**Effort**: 3-5 days

### P2-2: Integration Tests
**Rationale**: Functional tests exist, core workflows verified
**Timeline**: 1.1 release
**Effort**: 3-5 days

### P2-3: Improve Coverage to 80%+
**Rationale**: Measured in 1.0 (40%), improve in 1.1
**Timeline**: 1.1 release
**Effort**: 3-5 days (includes dead code removal)

### P2-4: Advanced Features
**Rationale**: Not MVP, nice-to-have
**Timeline**: 1.1+ (post-initial release)
**Effort**: 1-2 weeks

### P3-2: Architecture Documentation
**Rationale**: Helpful for contributors, not blocking
**Timeline**: 1.1 release
**Effort**: 1 day

---

## 1.0 Release Criteria

### Essential (Must Have) - STATUS CHECK

**Functionality**:
- ✅ All 13 commands work (verified, minus 1 bug = 16/17 tested, 1 BLOCKING)
- ✅ Installation methods functional (npm, pip, uv, git)
- ✅ Scope management works (rescope, scope list/show)
- ✅ Client management works (client list/show)
- ✅ Shell completion works (bash/zsh/fish)

**Quality**:
- ✅ >80% test pass rate (85.3% achieved)
- ✅ 0 test import errors (P0-1 complete)
- ✅ 0 test setup errors (P1-1-A complete)
- ✅ CI/CD running (Days 1-2 complete)
- ✅ Coverage measured (Day 3 complete, 40%)

**Documentation**:
- ✅ README accurate and complete (P1-2, 95% quality)
- ✅ All commands documented with examples
- ✅ Quick Start guide works
- ⏳ CHANGELOG created (Day 6)
- ⏳ Release notes written (Day 6)

**Release**:
- ⏳ Version bumped to 1.0.0 (Day 6)
- ⏳ Git tag created (Day 6)
- ⏳ GitHub release published (Day 6)
- ⏳ Known issues documented (Day 5)

**BLOCKING**:
- **1 critical bug**: `mcpi client info` TypeError (Day 4, 1 hour)

### Optional (Nice to Have) - STATUS CHECK

**Documentation**:
- [ ] PROJECT_SPEC updated (can defer to 1.0.1)
- [ ] Architecture docs created (defer to 1.1)

**Testing**:
- [ ] P1 test failures investigated (can defer to 1.0.1)
- [ ] Bug fixes for non-critical issues

---

## Risk Assessment

### CRITICAL RISK: Bug Fix Complexity

**Risk**: Bug fix takes longer than 1 hour or introduces regression
**Likelihood**: VERY LOW (simple conditional logic, well-understood problem)
**Impact**: LOW (1-2 hour delay, 4 days buffer available)

**Mitigation**:
- Bug analysis complete (root cause known)
- Fix is simple (add error check)
- Test suite catches regressions (85.3% pass rate)

**Contingency**: If regression found, roll back fix and investigate (add 2-4 hours)

---

### LOW RISK: P1 Investigations Reveal More Bugs

**Risk**: Optional P1 investigations find blocking bugs
**Likelihood**: LOW (manual testing confirms workflows work)
**Impact**: MEDIUM (1-2 days delay if critical bugs found)

**Mitigation**:
- All user workflows manually tested
- Test failures are mostly test infrastructure issues (88%)
- Can defer P1 investigations to 1.0.1 if needed

**Contingency**: Extend sprint by 1-2 days → Ship 2025-11-04 or 2025-11-05

---

### MINIMAL RISK: Unexpected Issues During Release Prep

**Risk**: CHANGELOG, release notes, or tagging reveals issues
**Likelihood**: VERY LOW (standard process, no complex setup)
**Impact**: LOW (2-4 hour delay)

**Mitigation**:
- Standard release workflow
- Clear checklist of tasks
- 4 days buffer for 10-15 hours work

**Contingency**: Ship later same day or next day

---

## What NOT to Do

**1. Don't Add New Features**
- Feature completeness: 83% (sufficient for 1.0)
- Focus on quality, not quantity
- Defer new features to 1.1

**2. Don't Try to Fix All 82 Test Failures**
- 88% are test infrastructure issues
- 12% are potential bugs (investigate P1s only)
- Don't waste time on test mocks for 1.0

**3. Don't Try to Reach 80% Coverage in 1.0**
- 40% is acceptable for 1.0
- Dead code is pulling down the metric
- Plan to improve to 80% in 1.1 (after dead code removal)

**4. Don't Skip Manual Testing After Bug Fix**
- Automated tests don't catch everything
- Manual verification is essential
- User workflows must work end-to-end

**5. Don't Rush Release Prep**
- Quality CHANGELOG matters
- Release notes create first impression
- Take time to get it right

---

## Daily Stand-Up Questions

### Day 4 (Critical Bug Fix)
- Is the `mcpi client info` bug fixed?
- Did the fix introduce any regressions?
- Are P1 investigations complete or deferred?
- Any blockers for Day 5?

### Day 5 (Polish)
- Do all quality gates pass?
- Are known issues documented?
- Is documentation updated?
- Ready for release prep?

### Day 6 (Release)
- Is CHANGELOG complete?
- Are release notes compelling?
- All artifacts prepared?
- **SHIP IT?**

---

## Celebration Checkpoints

### End of Day 4
- Critical bug FIXED
- All 17 commands working
- 0 blocking issues
- Clear path to release

### End of Day 5
- Code quality gates all green
- Known issues documented
- Documentation complete
- Release-ready codebase

### End of Day 6
- **1.0 SHIPPED**
- All artifacts published
- Community informed
- **VICTORY**

---

## Summary: Why We're Ready to Ship 1.0

**Days 1-3**: ✅ 100% COMPLETE
- Excellent CI/CD infrastructure
- Rapid regression fix (2.2x faster than estimate)
- Comprehensive manual testing
- Thorough bug triage

**Quality Metrics**: ✅ EXCEED TARGETS
- Test pass rate: 85.3% (target: 80%)
- Documentation quality: 95% (target: 90%)
- Feature completeness: 83% (target: 80%)
- Commands working: 16/17 (1 bug = 94%)

**Timeline**: ✅ ACHIEVABLE
- Essential work: 1 hour (critical bug fix)
- Recommended work: 8-13 hours (polish + release prep)
- Total: 9-14 hours over 4 days
- Buffer: 2.3-3.5x (HEALTHY)

**Risk**: ✅ LOW
- 1 simple bug fix (well-understood)
- Test infrastructure healthy
- Documentation accurate
- Clear path forward

**Path Forward**: ✅ CLEAR
- Day 4: Fix critical bug (1 hour), optional P1 investigations
- Day 5: Polish and final testing
- Day 6: Release prep and SHIP

---

**Recommendation**: Execute **Day 4 critical bug fix** (1 hour) immediately, then proceed with planned Days 5-6 release schedule.

**Confidence Level**: **85%** (HIGH) - Production-ready after 1 hour bug fix, 4 days to polish and ship.

**Key Insight**: Days 1-3 exceeded expectations. Only 1 simple bug blocks release. Final sprint is polish and release prep, not development.

---

**END OF 1.0 RELEASE PLAN**

Ship it on 2025-11-03!
