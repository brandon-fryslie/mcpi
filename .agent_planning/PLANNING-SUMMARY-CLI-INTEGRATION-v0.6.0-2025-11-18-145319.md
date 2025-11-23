# Planning Summary - v0.6.0 CLI Integration

**Generated**: 2025-11-18-145319
**Planning Cycle**: Final Sprint (CLI Integration Only)
**Source Evaluation**: STATUS-2025-11-18-144000.md (Latest evaluation)
**Target Release**: v0.6.0 (Ship by 2025-11-21)

---

## Situation Overview

### What We Have (COMPLETE)
The Template Discovery Engine library is 100% production-ready:
- ✅ 19/19 tests passing (100% pass rate)
- ✅ 91% test coverage on new code
- ✅ ProjectDetector: Detects Docker, languages, databases (<100ms)
- ✅ TemplateRecommender: Scores templates with confidence + explanations
- ✅ 12 templates updated with metadata
- ✅ Clean, well-documented, no hacks or shortcuts
- ✅ Evaluator verdict: "SHIP IT - EXIT LOOP"

### What We Need (3 TASKS)
CLI integration to make the feature accessible to end users:
- ❌ Add `--recommend` flag to `mcpi add` command
- ❌ Rich console display for recommendations
- ❌ Interactive selection prompt

**Gap**: Library works perfectly, users just can't access it yet.

---

## Planning Documents Created

### 1. PLAN-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md
**Purpose**: Detailed implementation plan for CLI integration
**Contents**:
- Gap analysis (library vs CLI state)
- 3 prioritized tasks (P1-1, P1-2, P1-3)
- Acceptance criteria for each task
- Technical implementation notes
- 5 manual verification scenarios
- Documentation requirements
- Risk assessment
- Timeline (2-3 days)

**Key Sections**:
- **P1-1**: Add --recommend flag, wire up detection/recommendation (3-4h)
- **P1-2**: Implement Rich display (context + table + colors) (3-4h)
- **P1-3**: Interactive selection prompt (template or skip) (2-3h)
- **Testing**: 5 scenarios (Docker, Node.js, empty, no-templates, skip)
- **Documentation**: Update CLAUDE.md with Template Discovery section

### 2. SPRINT-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md
**Purpose**: Sprint execution plan with daily goals
**Contents**:
- Day-by-day breakdown of 3 tasks
- Subtasks with time estimates
- Exit criteria for each day
- Manual testing plan with setup scripts
- Definition of done checklist
- Risk management
- Communication plan

**Daily Goals**:
- **Day 1**: P1-1 complete (--recommend flag functional)
- **Day 2**: P1-2 complete (Rich display working)
- **Day 3**: P1-3 complete + testing + documentation + ship

### 3. BACKLOG.md (UPDATED)
**Changes**:
- Updated executive summary (library 100% complete)
- Replaced "Week 1/2/3" breakdown with "3 tasks, 10 hours"
- Updated sprint status to "FINAL SPRINT"
- Simplified ship criteria (focus on 3 CLI tasks)
- Updated target ship date (2025-11-21 vs 2025-12-08)

**Key Message**: "Only 3 CLI tasks remaining to ship v0.6.0"

---

## Task Breakdown

### P1-1: Add --recommend Flag and Wire Up Discovery (Day 1, 3-4h)
**What**: Add flag to CLI, call ProjectDetector and TemplateRecommender
**Deliverable**: `mcpi add postgres --recommend` detects project and gets recommendations
**Testing**: Verify detection works, recommendations returned, errors handled
**Status**: Not Started - NEXT TASK

### P1-2: Implement Rich Display (Day 2, 3-4h)
**What**: Create beautiful table showing context summary and recommendations
**Deliverable**: Professional console output with colors, confidence scores, reasons
**Testing**: Verify formatting, colors, empty state
**Status**: Not Started - Depends on P1-1

### P1-3: Interactive Selection Flow (Day 3, 2-3h)
**What**: Add numbered prompt for user to select template or skip
**Deliverable**: User can pick recommendation or choose manual config
**Testing**: All 5 scenarios pass
**Status**: Not Started - Depends on P1-2

---

## Ship Criteria

**Must Complete**:
- [x] Library code complete (DONE - 19/19 tests)
- [ ] P1-1: --recommend flag working
- [ ] P1-2: Rich display rendering correctly
- [ ] P1-3: Interactive selection functional
- [ ] All 5 manual scenarios pass
- [ ] CLAUDE.md updated with Template Discovery section
- [ ] No regressions in existing tests
- [ ] Clean git state, v0.6.0 tagged

**Target Ship**: 2025-11-20 or 2025-11-21 (end of week)

---

## Testing Strategy

### Manual Verification (5 Scenarios)

**Required test projects**:
```bash
# Setup once
mkdir -p ~/test-mcpi-v060/{docker-app,node-app,empty-app}

# Docker + postgres
cd ~/test-mcpi-v060/docker-app
echo "services:\n  postgres:\n    image: postgres:15" > docker-compose.yml

# Node.js
cd ~/test-mcpi-v060/node-app
echo '{"name": "test"}' > package.json

# Empty
cd ~/test-mcpi-v060/empty-app
# (leave empty)
```

**Scenarios to test**:
1. **Docker + postgres**: Should recommend "docker" template with 90%+ confidence
2. **Node.js project**: Should recommend "local-development", penalize Docker templates
3. **Empty project**: Should show low confidence or equal weights, graceful fallback
4. **No templates**: Should show message, fall back to manual config
5. **User skips**: Should proceed to manual config, no template applied

**Pass criteria**: All 5 scenarios work without crashes or errors

### Automated Testing (Optional)
- Priority: LOW (manual testing sufficient)
- If time: Add CLI integration tests with mocked components
- Location: `tests/test_cli_recommend_integration.py`

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rich display formatting issues | LOW | Test early in real terminal, iterate |
| Integration with existing template flow | MEDIUM | Reuse existing code, minimal new logic |
| User input validation edge cases | MEDIUM | Comprehensive validation, clear errors |
| Performance degradation | LOW | Detection already <100ms |

**Overall Risk**: MINIMAL (library proven, only wiring required)

---

## Documentation Plan

### CLAUDE.md Updates
**Section**: Configuration Templates System (v0.5.0+)
**New Subsection**: Template Discovery Engine (v0.6.0+)

**Content to add**:
- Component overview (discovery.py, recommender.py)
- Detection algorithm explanation
- Scoring algorithm details (weights, factors)
- CLI usage examples (`mcpi add <server> --recommend`)
- Template metadata fields (best_for, keywords, recommendations)
- Fallback behavior documentation

**Estimated time**: 30 minutes

---

## File Management Actions

### New Files Created
- ✅ `PLAN-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md`
- ✅ `SPRINT-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md`
- ✅ `PLANNING-SUMMARY-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md` (this file)

### Files Updated
- ✅ `BACKLOG.md` (updated sprint status, simplified tasks)

### Files to Archive (OLD PLANNING)
These files represent the OLD 3-week plan (Week 1/2/3) that was superseded by the library implementation completing:
- `PLAN-2025-11-18-060344.md` → Move to archive (old 3-week plan)
- `SPRINT-2025-11-18-060344.md` → Move to archive (old Week 1/2/3 breakdown)
- `PLANNING-SUMMARY-2025-11-18-060344.md` → Move to archive (old summary)

**Reason**: Library work finished ahead of schedule. These plans assumed starting from scaffolding (5% complete). Reality: Library is now 100% complete. New plan focuses only on remaining CLI work (10 hours vs 84 hours).

### Files Already in Completed
- ✅ `STATUS-TEMPLATE-DISCOVERY-EVALUATION-2025-11-17-080057.md`
- ✅ `PLAN-TEMPLATE-DISCOVERY-2025-11-17-080505.md`
- ✅ `SPRINT-TEMPLATE-DISCOVERY-2025-11-17-080505.md`
- ✅ `PLANNING-SUMMARY-TEMPLATE-DISCOVERY-2025-11-17-080505.md`
- ✅ `PLAN-TEMPLATE-DISCOVERY-2025-11-17-132624.md`
- ✅ `SPRINT-TEMPLATE-DISCOVERY-2025-11-17-132624.md`
- ✅ `PLANNING-SUMMARY-TEMPLATE-DISCOVERY-2025-11-17-132624.md`

**Action**: No changes needed - already properly organized

### Retention Policy Check
**Current counts** (after cleanup):
- **PLAN** files: 4 (CLI Integration + 3 older)
- **SPRINT** files: 4 (CLI Integration + 3 older)
- **STATUS** files: 2 (Implementation Evaluation + 1 older)
- **PLANNING-SUMMARY** files: 4 (CLI Integration + 3 older)

**Policy**: Keep 4 most recent per prefix
**Status**: All within limits after archiving old 3-week plan

---

## Success Metrics

### Sprint Success (Internal)
- [ ] All 3 P1 tasks complete
- [ ] All 5 scenarios pass
- [ ] v0.6.0 shipped on time

### Feature Success (Post-Ship, 30 Days)
- **Adoption**: % of users using --recommend flag (target 40%+)
- **Acceptance**: % accepting top recommendation (target 85%+)
- **Time Savings**: Template selection time (target <10s vs ~45s)
- **Satisfaction**: User feedback, GitHub issues

---

## Next Steps

### Immediate (Today)
1. **Archive old planning files** (3-week plan superseded)
2. **Start P1-1** (Add --recommend flag)
3. **Set up test projects** (docker-app, node-app, empty-app)

### Tomorrow (Day 2)
1. Complete P1-2 (Rich display)
2. Manual test display formatting

### End of Week (Day 3)
1. Complete P1-3 (Interactive selection)
2. Run all 5 scenarios
3. Update documentation
4. Ship v0.6.0

---

## Communication

### Status Updates
- End of Day 1: P1-1 status (flag working or issues)
- End of Day 2: Display screenshots/demo
- End of Day 3: Ship announcement

### Escalation Triggers
- Any task >2x estimated time
- Test scenarios failing repeatedly
- Integration issues with existing code

---

## Key Insights from Planning

### Why This Plan is Different
**Old Plan** (PLAN-2025-11-18-060344.md):
- Assumed 5% complete (scaffolding only)
- 21 tasks, 84 hours, 3 weeks
- Weeks 1-2: Implement library
- Week 3: CLI integration

**New Plan** (This Plan):
- Reality: Library 100% complete (unexpected fast progress)
- 3 tasks, 10 hours, 2-3 days
- All focus on CLI integration
- Ship by end of week (not 3 weeks from now)

### Risk Reduction
- Library proven (19/19 tests) → Low implementation risk
- Only wiring/UI work remaining → Minimal technical complexity
- Clear acceptance criteria → Easy to verify success
- Manual testing focus → Fast feedback loop

### Timeline Acceleration
- Original estimate: Ship 2025-12-08 (3 weeks)
- New estimate: Ship 2025-11-21 (3 days)
- Acceleration: 2.5 weeks saved (library finished early)

---

**Summary**: Library complete, 3 CLI tasks remaining, ship by Friday. MINIMAL RISK.

**First Action**: Archive old 3-week plan, start P1-1 (add --recommend flag)

**Expected Outcome**: v0.6.0 shipped to end users by 2025-11-21 with intelligent template recommendations fully functional.
