# Template Discovery Engine - Planning Summary

**Generated**: 2025-11-17 13:26:24
**Source STATUS**: `STATUS-2025-11-17-132221.md` (Zero-Optimism Protocol)
**Plan**: `PLAN-TEMPLATE-DISCOVERY-2025-11-17-132624.md`
**Sprint**: `SPRINT-TEMPLATE-DISCOVERY-2025-11-17-132624.md`
**Target Version**: v0.6.0
**Current Status**: DAY 0 - Ready to Begin

---

## TL;DR - Executive Summary

**What**: Intelligent template recommendation system that analyzes your project (Docker, language, databases) and recommends the best template with confidence scores and explanations.

**Why**: As template library grows (12 → 50+ templates), manual selection becomes time-consuming. Recommendations reduce selection time by 75% (45 sec → 10 sec).

**Status**: 0% implemented, 100% planned, READY TO START NOW

**Timeline**: 2-3 weeks (21 tasks, ~84 hours)

**Risk**: LOW (no breaking changes, conservative approach, solid foundation)

**Next Step**: Create feature branch and begin P0-1 (ProjectContext dataclass)

---

## The Feature

### What Users Will Experience

**Before (Current Behavior)**:
```bash
$ mcpi add postgres --list-templates
# Shows 3 templates in a table
# User reads descriptions, picks one manually (30-60 seconds)
```

**After (With --recommend Flag)**:
```bash
$ mcpi add postgres --recommend

Analyzing your project...
  ✓ Detected Docker Compose in project root
  ✓ Found docker-compose.yml with postgres service
  ✓ Project type: Node.js application

🧠 Recommended Template: docker
   Confidence: 90%

Why this template?
  • Your project uses Docker Compose
  • Matches your docker-compose service: postgres
  • Optimized for nodejs projects

Alternatives:
  • local-development (40% match)
  • production (30% match)

Continue with 'docker' template? [Y/n]:
```

**Impact**: 75% faster template selection, 85%+ users accept top recommendation

---

## Architecture Overview

### New Components

**1. Project Detection** (`src/mcpi/templates/discovery.py` ~300 lines)
   - `ProjectContext`: Dataclass holding detected characteristics
   - `ProjectDetector`: Analyzes project files and structure
   - Detects: Docker, Docker Compose, language, databases

**2. Recommendation Engine** (`src/mcpi/templates/recommender.py` ~250 lines)
   - `TemplateRecommendation`: Dataclass for recommendations
   - `TemplateRecommender`: Scores and ranks templates
   - Scoring algorithm: Confidence-based matching (0.0-1.0)

**3. Template Metadata** (Extend existing models)
   - Add `best_for`, `keywords`, `recommendations` fields to ServerTemplate
   - Update all 12 existing templates with metadata

**4. CLI Integration** (Extend existing CLI)
   - Add `--recommend` flag to `mcpi add` command
   - Rich console output for recommendations
   - Seamless integration with existing template flow

---

## Implementation Timeline

### Week 1: Detection Infrastructure (Nov 18-22)

**Days 1-2**: Core Detection
- ProjectContext dataclass
- Docker detection (files + service parsing)
- Language detection (Node.js, Python, Go)
- Database detection (from docker-compose services)

**Days 3-4**: Metadata & Scoring
- Extend ServerTemplate model (3 new fields)
- Update all 12 templates with metadata
- Implement scoring algorithm
- TemplateRecommendation dataclass

**Day 5**: Testing & Verification
- Unit tests for detection (95%+ coverage)
- Verify detection works with real projects
- Week 1 quality gate

**Deliverable**: Detection infrastructure works programmatically

---

### Week 2: Recommendation Engine (Nov 25-29)

**Days 6-7**: Recommender Core
- TemplateRecommender class
- Factory functions (DIP-compliant)
- Comprehensive scoring tests

**Day 8**: Integration Testing
- E2E tests with real templates
- Test all 12 templates in appropriate contexts
- Realistic project structures

**Days 9-10**: Edge Cases & Performance
- Edge case testing (polyglot, monorepo, etc.)
- Performance testing (< 100ms target)
- Testing marathon (run suite 3+ times)

**Deliverable**: Recommendations work end-to-end with 95%+ coverage

---

### Week 3: CLI Integration & Ship (Dec 2-6)

**Days 11-12**: CLI Integration
- Add --recommend flag
- Rich console output
- Integration with template selection flow
- Documentation updates

**Days 13-14**: Final Testing & Polish
- Bug fixes
- Pre-ship checklist
- Final integration testing
- Manual E2E verification

**Day 15**: Ship v0.6.0
- Create PR
- Review and merge
- Tag v0.6.0
- Ship to production

**Deliverable**: v0.6.0 live in production

---

## Key Design Decisions

### 1. Conservative Scoring (Risk Mitigation)

**Decision**: Use confidence threshold of 0.3 (30%), show all templates even if confident

**Rationale**:
- False positives are worse than false negatives (wrong recommendation = lost trust)
- Users can always see full template list
- Conservative approach = safer, more trusted

**Weights**:
- Docker match: 0.4
- Language match: 0.3
- Docker service match: 0.5 (bonus, can exceed 1.0)
- Environment match: 0.2 (future)

---

### 2. Incremental Detection (Start Simple)

**Decision**: Start with 5 core detectors, add more later

**Initial Detectors**:
1. Docker (docker-compose.yml, Dockerfile)
2. Docker Compose services (parse service names)
3. Language (Node.js, Python, Go)
4. Database (from docker-compose services)
5. (Future: Frameworks, environment, cloud providers)

**Rationale**:
- 80/20 rule: 5 detectors cover 80% of use cases
- Fast to implement and test
- Easy to extend (add new detectors incrementally)
- Proven pattern (start MVP, iterate)

---

### 3. DIP Compliance (Architecture)

**Decision**: Follow existing factory pattern for all new components

**Implementation**:
```python
# Production use
recommender = create_default_template_recommender()

# Testing use
recommender = create_test_template_recommender(mock_manager)
```

**Rationale**:
- Consistent with v2.0 DIP architecture
- Testability (inject mocks in tests)
- No global state
- Easy to extend

---

### 4. Backward Compatibility (No Breaking Changes)

**Decision**: All new fields optional, old templates work without metadata

**Implementation**:
- `best_for: list[str] = Field(default_factory=list)`
- `keywords: list[str] = Field(default_factory=list)`
- `recommendations: Optional[dict] = Field(default=None)`

**Rationale**:
- Existing templates keep working (zero disruption)
- Gradual migration (update templates one by one)
- Users can create templates without metadata (just less smart recommendations)

---

## Success Metrics

### Quantitative (Track After Ship)

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Adoption Rate | 40%+ | % of `mcpi add` commands using --recommend |
| Acceptance Rate | 85%+ | % of users accepting top recommendation |
| Time Savings | 75% | Template selection time (45s → 10s) |
| False Positive Rate | < 10% | User reports of wrong recommendations |

### Qualitative (User Feedback)

- "It knew my project uses Docker!"
- "The explanation helped me understand why"
- "I trust MCPI's recommendations"
- "This saved me so much time"

---

## Risk Management

### Identified Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| False positives | MEDIUM | LOW | Conservative scoring, show all templates |
| Missing project types | HIGH | MEDIUM | Start with 5 detectors, incremental |
| Performance slow | LOW | LOW | Cache results, < 100ms target |
| Poor scoring | MEDIUM | MEDIUM | Extensive tests, tunable weights |
| Metadata incomplete | LOW | LOW | Pydantic validation |

**Overall Risk**: LOW

### Contingency Plans

**If Behind Schedule**:
- Week 1: Reduce database detection complexity
- Week 2: Reduce edge case coverage (focus critical paths)
- Week 3: Simplify CLI output (basic text, not Rich)

**If Major Issue Found**:
- Feature flag to disable recommendations
- Fall back to existing template selection
- No user disruption (--recommend is optional)

---

## Ship Criteria (All Must Pass)

**Code Complete**:
- [ ] All 21 tasks completed (0/21)
- [ ] ~2220 lines of code written
- [ ] ~1500 lines of tests written

**Quality Standards**:
- [ ] All new tests passing (100% pass rate)
- [ ] Coverage >= 95% on new code
- [ ] No regressions in existing features
- [ ] All quality checks pass (black, ruff, mypy)

**Documentation Complete**:
- [ ] README.md updated with --recommend examples
- [ ] CLAUDE.md updated with architecture changes
- [ ] Template metadata guide created
- [ ] CHANGELOG.md has v0.6.0 entry

**User Experience Validated**:
- [ ] Manual E2E testing passes (8 scenarios)
- [ ] CLI output looks professional
- [ ] Error messages are helpful
- [ ] Performance meets targets (< 100ms detection)

**If ANY criteria fails, DO NOT SHIP.** Quality over speed.

---

## What Could Go Wrong (Honest Assessment)

### Implementation Challenges

**Challenge 1: Docker Compose Parsing Complexity**
- **Risk**: Real-world docker-compose.yml files can be complex
- **Mitigation**: Graceful failure (return empty list on error), focus on common patterns
- **Fallback**: If parsing fails, still show templates (just less smart recommendations)

**Challenge 2: Scoring Weight Tuning**
- **Risk**: Initial weights may not match user expectations
- **Mitigation**: Make weights configurable, gather user feedback, iterate
- **Fallback**: Start conservative, can always increase confidence later

**Challenge 3: Project Type Coverage**
- **Risk**: 5 detectors may miss some project types
- **Mitigation**: Show all templates if no clear recommendation, incremental detector additions
- **Fallback**: Users can always use --list-templates or specify --template directly

### User Experience Challenges

**Challenge 1: Recommendation Disagreement**
- **Risk**: Users may disagree with top recommendation
- **Mitigation**: Clear explanations (why this template?), easy to decline, show alternatives
- **Fallback**: User can always see full list or use --template flag

**Challenge 2: Over-Reliance on Recommendations**
- **Risk**: Users may blindly accept without understanding
- **Mitigation**: Always show explanations, encourage reading template notes
- **Fallback**: Template prompts still educate users (no loss of learning)

---

## Post-Ship Plan (v0.6.1+)

### Immediate (Week 1 After Ship)
- Monitor adoption metrics (--recommend usage)
- Gather user feedback (surveys, Discord, GitHub issues)
- Fix any critical bugs found
- Tune scoring weights if needed

### Short Term (Month 1)
- Analyze recommendation acceptance rates
- Identify most common false positives/negatives
- Plan v0.6.1 improvements based on data

### Medium Term (Month 2-3)
- Add more detectors based on demand (frameworks, cloud providers)
- Implement performance caching if needed
- Consider ML-based scoring (based on user acceptance patterns)

### Long Term (v0.7.0+)
- Template Test Drive (preview + validate before install)
- Template Workflows (multi-server setups)
- Template Marketplace (community contributions)

---

## Critical Path

### Must Complete in Order

**Week 1 Dependencies**:
1. P0-1 (ProjectContext) → BLOCKS → P0-2, P0-3, P0-4, P0-5
2. P0-5 (ProjectDetector complete) → BLOCKS → P0-8, P0-10
3. P0-6 (ServerTemplate extension) → BLOCKS → P0-7
4. P0-7 (Template metadata) → BLOCKS → P0-8, P0-10

**Week 2 Dependencies**:
1. P0-8 (Scoring algorithm) → BLOCKS → P0-10, P1-16
2. P0-10 (TemplateRecommender) → BLOCKS → P0-11, P1-17
3. P0-11 (Factories) → BLOCKS → P1-12

**Week 3 Dependencies**:
1. P0-11 (Factories) → BLOCKS → P1-12
2. P1-12 (CLI flag) → BLOCKS → P1-13, P1-14
3. All implementation → BLOCKS → P3-21 (Polish & Ship)

**Critical Success Factor**: Complete Week 1 on time (detection foundation). Everything else builds on it.

---

## Resources & References

### Planning Documents
- **Detailed Plan**: PLAN-TEMPLATE-DISCOVERY-2025-11-17-132624.md (comprehensive)
- **Sprint Backlog**: SPRINT-TEMPLATE-DISCOVERY-2025-11-17-132624.md (daily breakdown)
- **Status Assessment**: STATUS-2025-11-17-132221.md (zero-optimism evaluation)
- **This Summary**: PLANNING-SUMMARY-TEMPLATE-DISCOVERY-2025-11-17-132624.md

### Original Proposal
- FEATURE_PROPOSAL_POST_v0.5.0_2025-11-17.md (original idea)
- STATUS-TEMPLATE-DISCOVERY-EVALUATION-2025-11-17-080057.md (initial evaluation)

### Foundation (v0.5.0)
- 12 production templates (working, 100% tests passing)
- Template infrastructure (95%+ coverage)
- DIP-compliant architecture (v2.0)
- Test harness patterns established

---

## Key Takeaways

1. **Day 0 Reality**: Zero code exists for v0.6.0. All ~2220 lines need to be written. This is the starting line.

2. **Solid Foundation**: v0.5.0 is rock solid (95%+ coverage, 100% template tests passing). Ready to build on.

3. **Low Risk**: Conservative approach, no breaking changes, extensive testing planned. Risk is LOW.

4. **Clear Plan**: 21 tasks, 3 weeks, daily breakdown, acceptance criteria defined. Ready to execute.

5. **High Value**: Solves real problem (template selection time), scales with library growth (12 → 50+ templates).

6. **Test-First Approach**: Write tests before implementation. 95%+ coverage is non-negotiable.

7. **Quality Over Speed**: Do not ship until ALL ship criteria met. No shortcuts.

---

## Final Checklist (Before Starting)

- [x] Planning complete (PLAN, SPRINT, STATUS, SUMMARY)
- [x] All prerequisites verified (dependencies installed, v0.5.0 working)
- [x] No blockers identified (zero technical blockers)
- [x] Success metrics defined (quantitative + qualitative)
- [x] Risk mitigation planned (contingencies for all risks)
- [x] Ship criteria clear (all must pass before merge)
- [ ] Feature branch created (git checkout -b feature/template-discovery)
- [ ] First task ready (P0-1 ProjectContext dataclass)

**Status**: READY TO BEGIN 🚀

**First Action**: Create feature branch and begin P0-1

**Expected Ship**: ~2025-12-08 (3 weeks from start)

---

**Generated by**: Implementation Planner Agent
**Date**: 2025-11-17 13:26:24
**Confidence**: HIGH (9/10) - Excellent foundation, clear plan, low risk
**Recommendation**: START IMMEDIATELY - All prerequisites met
