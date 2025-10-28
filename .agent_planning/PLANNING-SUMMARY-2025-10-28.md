# MCPI Planning Summary - Test Infrastructure Repair and MVP Completion

**Generated**: 2025-10-28 06:35:09
**Based On**: STATUS-2025-10-28-063053.md (comprehensive project audit)
**Previous Plan**: PLAN-2025-10-21-225314.md (rescope feature - NOW COMPLETE)

---

## Executive Summary

The project-evaluator completed a comprehensive audit revealing the MCPI project at **68% functional completion** with a **solid architecture** but **critical test infrastructure issues**:

**Key Findings**:
- **Core functionality WORKS**: list, search, info, rescope, completion all functional
- **Test infrastructure BROKEN**: 19 of 60 test files (31%) fail at import
- **Recent features EXCELLENT**: rescope (27/28 tests), completion (69/72 tests)
- **Documentation MISLEADING**: README describes features that don't exist
- **Architecture evolved BEYOND spec**: scope-based system better than spec's profile-based

**Major Progress Since Oct 21**:
- ✅ **Rescope feature COMPLETE** (was planned, now implemented with 27/28 tests passing)
- ✅ **Tab completion COMPLETE** (69/72 tests passing)
- ✅ **CUE schema validation COMPLETE** (registry validation working)
- ⚠️ **Test infrastructure still broken** (same 19 import errors)
- ⚠️ **Dead code still present** (75KB legacy files)

**Strategic Shift**:
- Previous plan focused on rescope feature (DONE)
- Current plan focuses on test infrastructure + MVP completion
- Timeline extended: 4 weeks to production 1.0 (vs 5-7 days for rescope)

---

## Planning Files Created

### Primary Planning Documents

**PLAN-2025-10-28-063509.md** (40KB)
- Comprehensive backlog based on STATUS-2025-10-28-063053.md
- 16 prioritized work items (P0: 3, P1: 6, P2: 4, P3: 4)
- Four-sprint roadmap to production 1.0
- Detailed acceptance criteria and technical notes
- Risk assessment and dependency graphs
- Location: `.agent_planning/PLAN-2025-10-28-063509.md`

**BACKLOG.md** (Updated)
- All 16 work items with effort estimates
- Priority definitions (P0=blocking, P1=critical, P2=important, P3=nice-to-have)
- Sprint breakdown by week
- Success metrics for 1.0 release
- References rescope feature as COMPLETE
- Location: `.agent_planning/BACKLOG.md`

### Supporting Documents

**STATUS-2025-10-28-063053.md** (32KB)
- Comprehensive audit with zero-optimism protocol
- Actual test execution results (not just code inspection)
- Evidence-based completion percentage (68%)
- Detailed gap analysis vs PROJECT_SPEC.md
- Location: `.agent_planning/STATUS-2025-10-28-063053.md`

---

## Current State Summary

### What Works (68% Complete)

**Discovery & Registry** (90%):
- ✅ `mcpi list` - Shows servers in Rich table
- ✅ `mcpi search` - Searches registry
- ✅ `mcpi info` - Shows server details
- ❌ `mcpi categories` - NOT IMPLEMENTED

**Scope Management** (95%):
- ✅ `mcpi rescope` - Move servers between scopes (27/28 tests)
- ✅ `mcpi scope list/show` - Inspect scopes
- ✅ Dry-run mode, rollback on failure

**Tab Completion** (95%):
- ✅ `mcpi completion install bash/zsh/fish` (69/72 tests)
- ✅ Dynamic completion for servers, clients, scopes

**Client Management** (90%):
- ✅ `mcpi client list/show` - Detect and inspect clients
- ✅ Auto-detection of Claude Code

**Plugin Architecture** (90%):
- ✅ MCPClientPlugin protocol
- ✅ ScopeHandler abstraction
- ✅ FileBasedScope implementation
- ✅ Claude Code plugin with 4 scopes

### What's Broken or Missing (32% Gap)

**Test Infrastructure** (40%):
- ❌ 19 of 60 test files fail at import (31% broken)
- ❌ Cannot measure test coverage accurately
- ❌ Tests reference deleted modules (ServerInstallation, registry.manager, etc.)

**Installation System** (Status Uncertain):
- ❓ `mcpi add` - Tests fail, unclear if functional
- ❓ `mcpi remove` - Tests fail, unclear if functional
- ❓ `mcpi status` - Tests fail, unclear if functional

**Documentation** (50%):
- ❌ README describes `mcpi config init` (doesn't work)
- ❌ README describes profile management (doesn't exist)
- ❌ No docs for rescope (implemented, not documented)
- ❌ No docs for completion (implemented, not documented)
- ❌ PROJECT_SPEC describes profile-based arch (reality: scope-based)

**Missing Core Features**:
- ❌ `mcpi update` - Required by spec, not implemented
- ❌ `mcpi categories` - Required by spec, not implemented
- ❌ `mcpi doctor` - Advanced feature, not implemented
- ❌ `mcpi backup/restore` - Advanced feature, not implemented

**Code Quality**:
- ❌ 3 dead code files (75KB: cli_old.py, cli_optimized.py, cli_original.py)
- ❌ cli.py is 1,381 LOC (god object)
- ❌ 171+ references to deleted modules (from prior audit)
- ❌ No CI/CD (tests can break unnoticed)

---

## Four-Week Roadmap to 1.0

### Sprint 1: Test Infrastructure Repair (Week 1)

**Goal**: Fix broken tests, remove dead code, verify functionality
**Work Items**: P0-1, P0-2, P0-3

**Deliverables**:
- [ ] 0 test import errors (down from 19)
- [ ] Dead code deleted (3 files removed)
- [ ] Core functionality manually verified
- [ ] Know which commands work vs broken

**Success Metric**: Can run `pytest tests/` without import errors

---

### Sprint 2: Documentation Alignment (Week 2)

**Goal**: Fix installation system, align docs with reality
**Work Items**: P1-1, P1-2, P1-3

**Deliverables**:
- [ ] Installation system verified/fixed
- [ ] README accurate (no false claims)
- [ ] README documents rescope + completion
- [ ] PROJECT_SPEC matches implementation

**Success Metric**: Documentation matches actual functionality

---

### Sprint 3: Core Feature Completion (Week 3)

**Goal**: Implement missing MVP commands
**Work Items**: P1-4, P1-5, P1-6

**Deliverables**:
- [ ] `mcpi categories` implemented
- [ ] `mcpi update` implemented
- [ ] `mcpi status` fixed
- [ ] All commands tested

**Success Metric**: All core commands from spec work

---

### Sprint 4: Quality and Production Readiness (Week 4)

**Goal**: Improve code quality, coverage, add CI/CD
**Work Items**: P2-1, P2-2, P2-4, P3-1

**Deliverables**:
- [ ] cli.py refactored into modules
- [ ] Integration tests added
- [ ] 80%+ test coverage achieved
- [ ] CI/CD pipeline running

**Success Metric**: Production-ready codebase with automated quality gates

---

## Priority Breakdown

### P0: BLOCKING (Must Fix Immediately)

**3 work items, 5-8 days total**

1. **P0-1: Fix Test Import Errors** (3-5 days)
   - 19 files fail on deleted modules
   - Categorize: delete obsolete vs update outdated
   - Align with current API

2. **P0-2: Remove Dead Code** (1-2 days)
   - Delete cli_old.py, cli_optimized.py, cli_original.py
   - Quick win, immediate clarity

3. **P0-3: Manual Verification** (1-2 days)
   - Test add/remove/status manually
   - Determine if broken or just tests wrong
   - Document actual behavior

### P1: CRITICAL (MVP Blockers)

**6 work items, 13-21 days total**

1. **P1-1: Fix Installation System** (3-5 days)
   - Based on P0-3 findings
   - Fix implementation and/or tests

2. **P1-2: Update README** (1-2 days)
   - Remove false claims
   - Document rescope + completion
   - Explain scope architecture

3. **P1-3: Update PROJECT_SPEC** (3-5 days)
   - Replace profile-based with scope-based
   - Document plugin architecture

4. **P1-4: Implement `categories`** (1-2 days)
   - Simple discovery command

5. **P1-5: Implement `update`** (3-5 days)
   - Complex: version detection, update mechanism

6. **P1-6: Fix `status`** (1-2 days)
   - Verify or fix command

### P2: IMPORTANT (Quality)

**4 work items, 10-18 days total**

1. **P2-1: Refactor cli.py** (3-5 days)
   - 1,381 LOC → modules <500 LOC each

2. **P2-2: Integration Tests** (3-5 days)
   - End-to-end workflows

3. **P2-3: Advanced Features** (1-2 weeks)
   - doctor, backup, restore, sync
   - OPTIONAL for 1.0

4. **P2-4: 80% Coverage** (3-5 days)
   - Meaningful tests, not tautological

### P3: NICE-TO-HAVE (Polish)

**4 work items, 7-13 days total**

1. **P3-1: CI/CD** (1-2 days) - HIGH VALUE
2. **P3-2: More Shell Completions** (1-2 days)
3. **P3-3: Architecture Docs** (1-2 days)
4. **P3-4: Clean Tech Debt** (3-5 days)

---

## Dependencies and Critical Path

### Critical Path to 1.0 (Minimum 15 days)

```
P0-1 (Fix tests) [3-5 days]
  ↓
P0-3 (Manual verify) [1-2 days]
  ↓
P1-1 (Fix installation) [3-5 days]
  ↓
P1-4 (categories) [1-2 days]
  ↓
P1-5 (update) [3-5 days]
  ↓
P2-4 (coverage) [3-5 days]
  ↓
P3-1 (CI/CD) [1-2 days]

Total: 15-26 days (3-5 weeks)
```

### Parallelizable Work

**Can run during P0-1**:
- P0-2 (Remove dead code)

**Can run during P1-1**:
- P1-2 (Update README)
- P1-3 (Update PROJECT_SPEC)

**Can run during Sprint 4**:
- P2-1 (Refactor CLI) while doing P2-2 (Integration tests)

---

## Risk Assessment

### HIGH RISK: Test Repairs Reveal Deeper Issues

**Probability**: MEDIUM
**Impact**: Could extend Sprint 1 by 1-2 weeks
**Mitigation**: Delete obsolete tests quickly, focus on core functionality
**Contingency**: Ship 1.0 with functional tests for working features, defer edge cases

### MEDIUM RISK: Installation System Actually Broken

**Probability**: LOW (app works, likely test issue)
**Impact**: Could extend P1-1 to 1-2 weeks
**Mitigation**: P0-3 discovers early
**Contingency**: Ship 1.0 without installation, make it 1.1 feature

### LOW RISK: Timeline Optimism

**Probability**: MEDIUM (surprises always happen)
**Impact**: 4 weeks becomes 5-6 weeks
**Mitigation**: P2 and P3 items can be deferred
**Contingency**: Ship 1.0 with P0+P1 complete, P2/P3 in 1.x

---

## Success Metrics for 1.0

### Must Have (MVP)
- [ ] 0 test import errors
- [ ] All core commands working (list, search, info, add, remove, status, update, categories)
- [ ] Installation system functional
- [ ] Documentation accurate
- [ ] 80%+ test coverage
- [ ] CI/CD running

### Should Have (Quality)
- [ ] cli.py refactored
- [ ] Integration tests
- [ ] PROJECT_SPEC aligned

### Nice to Have (Polish)
- [ ] Advanced features (doctor, backup, restore, sync)
- [ ] Architecture docs
- [ ] All tech debt cleaned

---

## Comparison with Previous Plan

### PLAN-2025-10-21-225314.md Results

**What Was Planned** (Oct 21):
- Phase 1: Foundation repair (3-4 days)
- Phase 2: Rescope feature (2-3 days)
- Total: 5-7 days

**What Actually Happened**:
- ✅ Rescope feature IMPLEMENTED (27/28 tests)
- ✅ Tab completion IMPLEMENTED (69/72 tests)
- ❌ Test infrastructure NOT FIXED (still 19 import errors)
- ❌ Dead code NOT REMOVED (still 3 legacy files)
- ❌ Technical debt NOT CLEANED (still 171+ references)

**Lessons Learned**:
1. Feature work proceeded despite foundation issues
2. New features are high quality (good testing)
3. Foundation work was deferred
4. Test infrastructure continues to decay

**New Plan Approach**:
1. **FORCE foundation work first** (P0 items)
2. Block new features until tests healthy
3. Focus on production readiness, not just features
4. Add CI/CD to prevent future decay

---

## Files to Archive

### Outdated Planning Documents

**PLANNING-SUMMARY-2025-10-21.md** → archive/
- Focused on rescope feature (now complete)
- Referenced 40% completion (now 68%)
- Foundation issues unresolved

**rescope_test_implementation.json** → Keep
- Documents completed rescope tests
- Historical record of implementation

**installation_implementation_summary.json** → Keep
- Documents installation system state
- May be useful for P1-1

**FEATURE_PROPOSAL_CLI_TAB_COMPLETION.md** → archive/
- Tab completion now implemented
- Keep as historical record of design

---

## Next Actions

### Immediate (This Week)

**Day 1-2**:
1. Start P0-1: Categorize 19 broken test files
2. Complete P0-2: Delete dead code (quick win)

**Day 3-4**:
3. Continue P0-1: Fix or delete categorized tests
4. Start P0-3: Manual verification of add/remove/status

**Day 5**:
5. Complete P0-3: Document findings
6. Review Sprint 1 progress
7. Plan Sprint 2 based on P0-3 findings

### This Month

**Week 1**: Sprint 1 (P0 items)
**Week 2**: Sprint 2 (P1 documentation)
**Week 3**: Sprint 3 (P1 features)
**Week 4**: Sprint 4 (P2 quality + P3-1 CI/CD)

### This Quarter

**Month 1**: Ship 1.0 with P0+P1+critical P2/P3
**Month 2**: 1.1 with remaining P2/P3 items
**Month 3**: 1.2 with community feedback

---

## Key Insights

### Architecture Quality: EXCELLENT

The scope-based plugin architecture is:
- Better than spec (scope > profile)
- Extensible and maintainable
- Well type-hinted with protocols
- Clean separation of concerns

**Recommendation**: Keep architecture, update spec to match

### Recent Feature Quality: EXCELLENT

Rescope and completion features show:
- High test coverage (95%+)
- Un-gameable functional tests
- Good error handling
- Transaction safety (rollback)

**Recommendation**: Use as template for future features

### Test Infrastructure: CRITICAL ISSUE

31% of tests broken for extended period shows:
- No CI/CD enforcement
- Tests not run regularly
- Code changes without test updates
- Coverage metrics unreliable

**Recommendation**: Make P0-1 and P3-1 (CI/CD) highest priority

### Documentation: MISLEADING

README describes features that don't exist:
- Poor user experience
- Support burden
- Credibility issues

**Recommendation**: Make P1-2 high priority, only document what works

---

## Conclusion

The MCPI project has a **solid foundation** (68% complete) with **excellent recent work** (rescope, completion) but suffers from **neglected test infrastructure** and **documentation drift**.

**Path to 1.0 is clear**: Fix tests (Sprint 1), align docs (Sprint 2), complete features (Sprint 3), add quality gates (Sprint 4).

**Timeline is realistic**: 4 weeks with contingencies for surprises.

**Success depends on**: Discipline to fix foundation before adding features, maintaining test health with CI/CD, keeping docs in sync.

**Confidence level**: HIGH - Foundation is sound, gap is execution not design.

---

**END OF SUMMARY**

Next: Begin Sprint 1, P0-1 (Fix test imports)
