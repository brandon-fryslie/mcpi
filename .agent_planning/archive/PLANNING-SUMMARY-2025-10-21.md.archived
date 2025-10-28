# MCPI Planning Summary - Foundation Repair and Rescope Feature

**Generated**: 2025-10-21 22:53:14
**Based On**: STATUS-2025-10-21-225033.md (project-evaluator assessment)
**Feature Request**: .agent_planning/BACKLOG.md (rescope feature)

---

## Executive Summary

The project-evaluator revealed harsh truths: MCPI is at **40% completion** (not 75% as previously claimed) with **critical foundation issues** that block new feature development:

- **19 of 62 test files fail to import** (31% of test suite broken)
- **Missing critical API methods** required for rescope feature
- **171+ references to deleted modules** (massive technical debt)

The user requested implementation of the **rescope feature** from BACKLOG.md, but the foundation must be fixed first.

**Two-phase approach created**:
1. **Phase 1: Foundation Repair** (3-4 days) - Fix tests, implement APIs, clean debt
2. **Phase 2: Rescope Feature** (2-3 days) - Implement actual rescope functionality

**Total Timeline**: 5-7 days to completed, tested rescope feature

---

## Planning Files Created

### Primary Planning Documents

**PLAN-2025-10-21-225314.md** (38KB)
- Comprehensive backlog for both phases
- Based on latest STATUS-2025-10-21-225033.md
- Contains detailed work items with acceptance criteria
- Includes risk assessment and dependency graph
- File location: `/Users/bmf/icode/mcpi/PLAN-2025-10-21-225314.md`

**SPRINT-2025-10-21-225314.md** (17KB)
- Focused Sprint 1 plan for Phase 1 (Foundation Repair)
- Day-by-day breakdown of 4-day sprint
- Concrete tasks with file references
- Success metrics and daily standup questions
- File location: `/Users/bmf/icode/mcpi/SPRINT-2025-10-21-225314.md`

### Supporting Documents

**.agent_planning/BACKLOG.md** (10KB)
- Original rescope feature specification
- Kept as authoritative feature spec
- Referenced by PLAN and SPRINT files

---

## Phase 1: Foundation Repair (Prerequisites)

**Timeline**: 3-4 days
**Goal**: Stabilize foundation before building features

### Critical Work Items

**P0-1: Fix Test Import Failures (19 broken test files)**
- **Problem**: 31% of test suite cannot import due to deleted modules
- **Impact**: BLOCKING - cannot validate any implementation
- **Effort**: Large (1-2 weeks)
- **Files**: 19 test files listed in PLAN
- **Success**: 0 import errors (down from 19)

**P0-2: Implement Missing get_server_config() API**
- **Problem**: Rescope REQUIRES this method, but it DOES NOT EXIST
- **Impact**: CRITICAL BLOCKER - rescope cannot work without it
- **Effort**: Small (1-2 days)
- **File**: `/Users/bmf/icode/mcpi/src/mcpi/clients/base.py`
- **Success**: Method exists, tested, returns correct data

**P0-3: Clean Critical Technical Debt**
- **Problem**: 171+ references to deleted modules (ClaudeCodeInstaller, etc.)
- **Impact**: MEDIUM - confuses navigation, risk during development
- **Effort**: Medium (3-5 days)
- **Target**: Reduce to <10 broken references
- **Success**: Linter passes, imports work

**P0-4: Validate Core Functionality**
- **Problem**: Cannot verify claimed functionality without working tests
- **Impact**: HIGH - claims unverified
- **Effort**: Small (1-2 days)
- **Dependencies**: P0-1 (need working tests first)
- **Success**: Test suite runs, >80% tests execute

### Phase 1 Success Criteria

- [ ] All test files can import (0 import errors)
- [ ] `ScopeHandler.get_server_config()` method implemented and tested
- [ ] Core functionality validated with working tests
- [ ] Critical technical debt cleaned (<10 broken references)

**ONLY after Phase 1 complete → Proceed to Phase 2**

---

## Phase 2: Rescope Feature Implementation

**Timeline**: 2-3 days
**Goal**: Implement rescope feature on stable foundation

### Feature Work Items

**P1-1: Implement Core Rescope Logic**
- **What**: Transactional move of server config between scopes
- **Includes**: Validation, dry-run mode, rollback on failure
- **Effort**: Medium (3-5 days)
- **File**: New method in MCPManager or new module
- **Success**: Rescope logic works with rollback

**P1-2: Implement Rescope CLI Command**
- **What**: Add `mcpi rescope` command to CLI
- **Includes**: Position-independent args, --dry-run flag
- **Effort**: Small (1-2 days)
- **File**: `/Users/bmf/icode/mcpi/src/mcpi/cli.py`
- **Success**: Command works for all documented variations

**P1-3: Comprehensive Rescope Testing**
- **What**: Unit, integration, and functional tests
- **Target**: 95%+ coverage of rescope feature
- **Effort**: Medium (3-5 days)
- **Files**: 3 new test files
- **Success**: All tests pass, 95%+ coverage achieved

**P1-4: Documentation and Finalization**
- **What**: Update README, CHANGELOG, add examples
- **Effort**: Small (1-2 days)
- **Files**: README.md, CHANGELOG.md
- **Success**: Feature fully documented

### Phase 2 Success Criteria

- [ ] `mcpi rescope` command works for all use cases
- [ ] All error scenarios handled gracefully
- [ ] 95%+ test coverage with passing tests
- [ ] Feature documented in README and CHANGELOG

---

## Work Item Summary

### Phase 1 (Foundation) - 4 work items
- **P0-1**: Fix 19 test import failures → 0 import errors
- **P0-2**: Implement get_server_config() API → method exists and works
- **P0-3**: Clean technical debt → <10 broken references
- **P0-4**: Validate core functionality → tests run, coverage measured

### Phase 2 (Rescope) - 4 work items
- **P1-1**: Core rescope logic → transactional operation with rollback
- **P1-2**: CLI command → `mcpi rescope` works
- **P1-3**: Comprehensive testing → 95%+ coverage
- **P1-4**: Documentation → README, CHANGELOG updated

**Total**: 8 work items across 2 phases

---

## Timeline Estimates

### Best Case: 5 days
- Phase 1: 3 days (parallelization works well)
- Phase 2: 2 days (no surprises)

### Realistic Case: 6 days
- Phase 1: 3.5 days (some integration issues)
- Phase 2: 2.5 days (normal debugging)

### Worst Case: 7 days
- Phase 1: 4 days (major architectural issues)
- Phase 2: 3 days (extensive refactoring needed)

---

## Risk Assessment

### HIGH RISK
**Test Import Fixes May Reveal Deeper Issues**
- 19 test files broken may indicate larger problems
- Mitigation: Categorize on Day 1, delete obsolete tests quickly
- Contingency: If >50% obsolete, focus on new tests instead

### MEDIUM RISK
**Technical Debt Cleanup Uncovers Hidden Dependencies**
- 171+ broken references may be complex
- Mitigation: Focus on blocking issues, defer cosmetic
- Contingency: Create separate tickets for non-blocking cleanup

### LOW RISK
**Rescope Feature Complexity Underestimated**
- BACKLOG.md spec is detailed and clear
- Mitigation: Spec provides comprehensive design
- Contingency: Defer advanced features to future work

---

## Sprint 1 Focus (Next 4 Days)

The SPRINT-2025-10-21-225314.md provides a **day-by-day breakdown**:

**Day 1**:
- Morning: Categorize all 19 broken tests (delete vs. update vs. fix)
- Afternoon: Implement `get_server_config()` API

**Day 2**:
- Morning: Fix installer test imports (6 files)
- Afternoon: Fix registry test imports (4 files)

**Day 3**:
- Morning: Fix CLI and config test imports (9 files)
- Afternoon: Clean critical technical debt (blocking imports/type hints)

**Day 4**:
- Morning: Validate core functionality (run full test suite)
- Afternoon: Sprint retrospective, Phase 2 readiness check

---

## File Management and Hygiene

### Active Planning Files

**Root Directory**:
- `PLAN-2025-10-21-225314.md` - Comprehensive backlog (THIS PLAN)
- `SPRINT-2025-10-21-225314.md` - Sprint 1 execution plan
- `STATUS-2025-10-21-225033.md` - Latest status report (ground truth)

**.agent_planning Directory**:
- `BACKLOG.md` - Rescope feature specification (authoritative)

### Archived Files

**Retired to archive/ directory**:
- `PLAN-2025-10-16-072315.md.superseded` - Outdated plan based on old STATUS
- `TODO.md.archived` - Empty file, no content
- `PROJECT.md.archived` - Empty file, no content
- `AGENT.md.archived` - Empty file, no content
- `CONVENTIONS.md.archived` - Empty file, no content

**Rationale**: Old PLAN was based on STATUS-2025-10-16-045045.md which claimed 75% completion. New STATUS reveals 40% completion with different issues. Old plan is superseded.

### Retention Policy

Following project-evaluator's 4-file retention policy:
- Keep 4 most recent STATUS files (currently at exactly 4)
- Keep 4 most recent PLAN files (currently at 1)
- Keep 4 most recent SPRINT files (currently at 1)
- Archive older files with clear suffix (.superseded, .archived)

---

## Key Blockers Identified

### CRITICAL - Missing API Method
**Blocker**: `ScopeHandler.get_server_config()` does NOT exist
**Required By**: Rescope feature cannot work without it
**Evidence**: STATUS line 98-118, BACKLOG.md line 139
**Resolution**: P0-2 implements this method

### CRITICAL - Broken Test Infrastructure
**Blocker**: 19 test files cannot import
**Required By**: Cannot validate rescope implementation
**Evidence**: STATUS line 34-59
**Resolution**: P0-1 fixes all import errors

### HIGH - Unstable API
**Blocker**: API breaking changes between tests and implementation
**Required By**: Need stable foundation for feature development
**Evidence**: STATUS line 22, git status shows deleted modules
**Resolution**: P0-1 aligns tests with current API

### MEDIUM - Technical Debt
**Blocker**: 171+ broken references confuse navigation
**Required By**: Need clear codebase for development
**Evidence**: STATUS line 249-253
**Resolution**: P0-3 cleans critical debt

---

## Success Metrics

### Foundation Repair (Phase 1)
- **Test Health**: 0 import errors (down from 19)
- **API Completeness**: get_server_config() exists and tested
- **Code Quality**: <10 broken references (down from 171+)
- **Validation**: >80% of tests execute

### Rescope Feature (Phase 2)
- **Functionality**: All documented use cases work
- **Error Handling**: All 7 error scenarios handled
- **Testing**: 95%+ coverage with passing tests
- **Documentation**: README and CHANGELOG updated

### Overall Project
- **Completion**: 40% → 60%+ (foundation + rescope)
- **Quality**: Tests run and pass, foundation stable
- **Readiness**: Can implement future features safely

---

## Next Steps

### Immediate Actions
1. **Review** this summary and PLAN-2025-10-21-225314.md
2. **Confirm** approach: fix foundation before building rescope
3. **Start** Sprint 1, Day 1: Categorize broken tests + implement API

### Decision Points
- **Day 1**: After categorization, confirm delete vs. fix strategy for tests
- **Day 4**: After Phase 1, GO/NO-GO decision for Phase 2
- **Post-Sprint**: If Phase 1 incomplete, reassess timeline

### Success Path
1. Complete Phase 1 (3-4 days) → stable foundation
2. Complete Phase 2 (2-3 days) → working rescope feature
3. Total: 5-7 days to tested, documented rescope feature

---

## References

**Source Documents**:
- `/Users/bmf/icode/mcpi/STATUS-2025-10-21-225033.md` - Current state (40% complete)
- `/Users/bmf/icode/mcpi/.agent_planning/BACKLOG.md` - Rescope feature spec
- `/Users/bmf/icode/mcpi/CLAUDE.md` - Project architecture

**Planning Documents**:
- `/Users/bmf/icode/mcpi/PLAN-2025-10-21-225314.md` - Comprehensive backlog (this plan)
- `/Users/bmf/icode/mcpi/SPRINT-2025-10-21-225314.md` - Sprint 1 execution plan

**Archived Documents**:
- `/Users/bmf/icode/mcpi/archive/PLAN-2025-10-16-072315.md.superseded` - Previous plan

---

## Provenance and Alignment

**Generated By**: project-backlog-planner agent
**Input Authority**: STATUS-2025-10-21-225033.md (project-evaluator's ruthless assessment)
**Spec Authority**: CLAUDE.md (architecture), BACKLOG.md (rescope feature)
**Timestamp**: 2025-10-21 22:53:14

**Alignment Notes**:
- This plan treats STATUS as ground truth for current state
- Does not re-derive evidence already captured by evaluator
- All work items traced to STATUS findings or BACKLOG spec
- No contradictions with specification detected
- Old PLAN archived as superseded (based on outdated STATUS)

**Next Planning Cycle**:
- After Sprint 1: Generate STATUS-YYYY-MM-DD-HHMMSS.md to assess progress
- After Phase 1: Assess Phase 2 readiness with evidence
- After Phase 2: Generate final STATUS showing rescope completion

---

**END OF SUMMARY**

This summary provides the roadmap from **40% completion with broken foundation** to **60%+ completion with working rescope feature** in a realistic 5-7 day timeline.
