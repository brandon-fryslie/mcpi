# Template Discovery Engine - Planning Summary

**Generated**: 2025-11-17 08:05:05
**Source Evaluation**: `STATUS-TEMPLATE-DISCOVERY-EVALUATION-2025-11-17-080057.md`
**Implementation Plan**: `PLAN-TEMPLATE-DISCOVERY-2025-11-17-080505.md`
**Sprint Backlog**: `SPRINT-TEMPLATE-DISCOVERY-2025-11-17-080505.md`
**Target Version**: v0.6.0

---

## TL;DR - Executive Overview

**What**: Intelligent template recommendation system that analyzes project context and suggests the best configuration templates

**Why**: As template library grows (12 → 50+ templates), users face choice paralysis. This solves "which template should I use?"

**Timeline**: 2-3 weeks (21 work items, 84 hours estimated)

**Risk**: LOW - Pure recommendation engine, no destructive operations, backward compatible

**Value**: 75% faster template selection, 85%+ acceptance rate, immediate user delight

---

## Feature Overview

### The Problem

**Current state** (v0.5.0 with 12 templates):
```bash
$ mcpi add postgres --list-templates

Available templates for postgres:
1. local-development - PostgreSQL on localhost
2. docker - PostgreSQL in Docker container
3. production - Production-ready configuration

Which template? [1]:
```

Users must guess which template fits their project. As library grows to 50+ templates, this becomes unmanageable.

### The Solution

**With Template Discovery**:
```bash
$ mcpi add postgres --recommend

Analyzing your project...
  ✓ Detected Docker Compose in project root
  ✓ Found postgres service in docker-compose.yml

🧠 Recommended: postgres/docker (Confidence: 90%)

Why this template?
  • Your project uses Docker Compose
  • Matches your postgres service
  • Easier than running postgres locally

Continue with 'docker' template? [Y/n]:
```

### Key Benefits

1. **Smart Detection**: Analyzes Docker, language, databases, frameworks
2. **Explainable**: Shows WHY each template is recommended
3. **Confidence Scores**: 0-100% confidence with reasoning
4. **Local-First**: No telemetry, no external services
5. **Optional**: Falls back to normal flow if no recommendations

---

## Implementation Summary

### Week 1: Detection Infrastructure (28 hours)

**Goal**: Detection works programmatically

**Deliverables**:
- `ProjectContext` dataclass (detected characteristics)
- `ProjectDetector` class (Docker, language, database detection)
- All 12 templates updated with metadata
- Scoring algorithm implemented
- Unit tests (95%+ coverage on detection)

**Key Components**:
- `src/mcpi/templates/discovery.py` (~300 lines)
- Template metadata updates (12 YAML files)
- Extended `ServerTemplate` model

### Week 2: Recommendation Engine (28 hours)

**Goal**: Recommendations work end-to-end

**Deliverables**:
- `TemplateRecommender` class (scoring + ranking)
- Factory functions (DIP compliant)
- Comprehensive unit tests (scoring, ranking)
- Integration tests (realistic scenarios)
- Edge case tests (8-10 edge cases)

**Key Components**:
- `src/mcpi/templates/recommender.py` (~250 lines)
- Test suite (30+ tests)
- Coverage: 95%+ on new code

### Week 3: CLI Integration & Ship (28 hours)

**Goal**: Feature ships to users

**Deliverables**:
- `--recommend` flag in `mcpi add` command
- Rich console output (beautiful formatting)
- Complete documentation
- Performance validation
- v0.6.0 release

**Key Components**:
- CLI integration (`src/mcpi/cli.py`)
- Documentation updates (README, CLAUDE.md)
- CHANGELOG entry
- Ship checklist completed

---

## Technical Architecture

### New Components

**discovery.py**:
```python
@dataclass
class ProjectContext:
    root_path: Path
    has_docker: bool
    has_docker_compose: bool
    docker_services: List[str]
    language: Optional[str]
    databases: List[str]
    environment: str

class ProjectDetector:
    def detect(self, project_path: Path) -> ProjectContext
```

**recommender.py**:
```python
@dataclass
class TemplateRecommendation:
    template: ServerTemplate
    confidence: float
    reasons: List[str]

class TemplateRecommender:
    def recommend(
        self,
        server_id: str,
        project_path: Path
    ) -> List[TemplateRecommendation]
```

### Extended Components

**models.py**:
```python
class ServerTemplate(BaseModel):
    # Existing fields...
    best_for: List[str] = []  # NEW
    keywords: List[str] = []  # NEW
    recommendations: Optional[Dict[str, Any]] = None  # NEW
```

**Template metadata** (example):
```yaml
# data/templates/postgres/docker.yaml
metadata:
  best_for:
    - docker
    - docker-compose
    - development
  keywords:
    - containerized
  recommendations:
    docker_service_match: postgres
```

### Integration Points

- **DIP Compliant**: Factory functions, injectable dependencies
- **Backward Compatible**: All new fields optional, existing behavior preserved
- **Test-Driven**: 95%+ coverage, comprehensive test suite
- **Performance**: < 100ms detection, < 50ms recommendation

---

## Work Breakdown

### Phase 1: Detection (11 tasks)

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P0-1 | ProjectContext data model | 2h | P0 |
| P0-2 | Docker detection | 4h | P0 |
| P0-3 | Language detection | 3h | P0 |
| P0-4 | Database detection | 3h | P0 |
| P0-5 | ProjectDetector integration | 2h | P0 |
| P0-6 | Extend ServerTemplate model | 3h | P0 |
| P0-7 | Update 12 template files | 3h | P0 |
| P0-8 | Scoring algorithm | 5h | P0 |
| P0-9 | TemplateRecommendation model | 1h | P0 |
| P0-10 | TemplateRecommender class | 6h | P0 |
| P0-11 | Factory functions | 2h | P0 |

**Subtotal**: 34 hours

### Phase 2: Testing (6 tasks)

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P1-15 | Unit tests - Detection | 6h | P1 |
| P1-16 | Unit tests - Scoring | 5h | P1 |
| P1-17 | Integration tests E2E | 6h | P1 |
| P2-18 | Edge case testing | 4h | P2 |
| P2-19 | Documentation | 4h | P2 |
| P2-20 | Performance testing | 2h | P2 |

**Subtotal**: 27 hours

### Phase 3: CLI & Ship (4 tasks)

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P1-12 | Add --recommend flag | 4h | P1 |
| P1-13 | Rich console output | 3h | P1 |
| P1-14 | Template selection integration | 3h | P1 |
| P3-21 | Final polish & ship | 4h | P3 |

**Subtotal**: 14 hours

### Code Review & Cleanup (3 tasks)

| Task | Effort | When |
|------|--------|------|
| Week 1 review & cleanup | 2h | Day 5 |
| Week 2 review & refactor | 2h | Day 9 |
| Pre-ship review | 2h | Day 14 |

**Subtotal**: 6 hours

**Grand Total**: 81 hours (budgeted 84 hours)

---

## Success Metrics

### Quantitative Goals

| Metric | Target | Measurement |
|--------|--------|-------------|
| Adoption Rate | 40%+ | % users using --recommend flag |
| Acceptance Rate | 85%+ | % accepting top recommendation |
| Time Savings | 75% | Template selection time (45s → 10s) |
| Test Coverage | 95%+ | Coverage on new code |
| Performance | < 100ms | Detection time |

### Qualitative Goals

**User Feedback Themes**:
- "It knew my project uses Docker!"
- "The explanation helped me understand"
- "I trust MCPI's recommendations"

### Ship Criteria

**Must Have** (v0.6.0):
- [ ] All P0 tasks completed
- [ ] Test coverage >= 95%
- [ ] All tests passing (100%)
- [ ] No regressions
- [ ] Documentation complete
- [ ] All 12 templates have metadata

**Nice to Have** (v0.6.1+):
- Framework detection
- Environment detection
- Performance caching
- User feedback mechanism

---

## Risk Assessment

### Risk Matrix

| Risk | Probability | Impact | Mitigation | Residual |
|------|------------|--------|------------|----------|
| False positive detection | MEDIUM | LOW | Conservative scoring, always show all templates | LOW |
| Missing project types | HIGH | MEDIUM | Start with 5 detectors, incremental approach | LOW |
| Performance issues | LOW | LOW | Cache results, fast file checks | VERY LOW |
| Scoring algorithm poor | MEDIUM | MEDIUM | Extensive testing, tunable weights | LOW |
| Breaking existing features | LOW | HIGH | Backward compatible, comprehensive tests | VERY LOW |

**Overall Risk**: LOW

### Rollback Plan

**If issues arise**:
1. Remove `--recommend` flag (users fall back to current behavior)
2. Metadata fields are optional (templates work without them)
3. No database migrations or file format changes
4. Can disable with feature flag if needed

**Recovery**: Simple git revert, ship patch release

---

## Dependencies & Prerequisites

### All Prerequisites Met ✓

- [x] Template system functional (v0.5.0)
- [x] Pydantic models for validation
- [x] YAML parsing (PyYAML)
- [x] Rich console output
- [x] CLI framework (Click)
- [x] Factory pattern established
- [x] DIP architecture in place
- [x] Test infrastructure solid

### No New Dependencies Required

- PyYAML: Already installed
- Pydantic: Already installed
- Rich: Already installed
- Click: Already installed

---

## Timeline Visualization

```
Week 1: Detection Infrastructure
├─ Day 1-2: ProjectDetector (Docker, Language, Database)
├─ Day 3: Integration + Template Metadata (start)
├─ Day 4: Template Metadata (finish) + Scoring
└─ Day 5: Unit Tests + Week 1 Review

Week 2: Recommendation Engine
├─ Day 6: TemplateRecommender Class
├─ Day 7: Factory Functions + Scoring Tests
├─ Day 8: Integration Tests E2E
├─ Day 9: Edge Cases + Code Review
└─ Day 10: Performance Tests + Week 2 Review

Week 3: CLI Integration & Ship
├─ Day 11: --recommend Flag + Rich Output
├─ Day 12: Template Selection Flow + Documentation
├─ Day 13: Final Testing + Bug Fixes
├─ Day 14: Polish + Pre-Ship Review
└─ Day 15: Create PR + Merge + Ship v0.6.0
```

---

## Next Steps

### Immediate Actions

1. **Create feature branch**: `feature/template-discovery`
2. **Start Day 1 tasks**: P0-1 (ProjectContext dataclass)
3. **Set up test fixtures**: Sample docker-compose.yml files
4. **Review evaluation report**: Refresh on implementation details

### Daily Workflow

1. **Morning**: Review day's tasks in sprint backlog
2. **Work**: Implement tasks, write tests as you go
3. **Testing**: Run tests after each task
4. **Evening**: Update sprint backlog, commit progress

### Weekly Checkpoints

- **End of Week 1**: Detection works, 95%+ coverage
- **End of Week 2**: Recommender works E2E, all tests pass
- **End of Week 3**: Ship v0.6.0 to users

---

## Questions & Decisions

### Open Questions

None - Evaluation report addressed all concerns

### Key Decisions Made

1. **Confidence Threshold**: 0.3 (30%) minimum for recommendations
2. **Scoring Weights**: docker_match=0.4, language_match=0.3, service_match=0.5
3. **Detection Scope**: Start with 5 detectors (Docker, language, database, framework, environment)
4. **Template Metadata**: Optional fields (backward compatible)
5. **CLI Behavior**: --recommend is optional flag, preserves existing flow

---

## References

### Planning Documents

- **Evaluation Report**: `.agent_planning/STATUS-TEMPLATE-DISCOVERY-EVALUATION-2025-11-17-080057.md`
- **Feature Proposal**: `.agent_planning/FEATURE_PROPOSAL_POST_v0.5.0_2025-11-17.md`
- **Implementation Plan**: `.agent_planning/PLAN-TEMPLATE-DISCOVERY-2025-11-17-080505.md`
- **Sprint Backlog**: `.agent_planning/SPRINT-TEMPLATE-DISCOVERY-2025-11-17-080505.md`

### Related Code

- **Template Manager**: `src/mcpi/templates/template_manager.py`
- **Template Models**: `src/mcpi/templates/models.py`
- **CLI**: `src/mcpi/cli.py` (lines 998-1084)
- **Test Harness**: `tests/test_harness.py`

### External Resources

- **PyYAML Documentation**: https://pyyaml.org/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Rich Documentation**: https://rich.readthedocs.io/

---

## Appendix: Quick Start Guide

### For Implementation

1. **Read evaluation report** (15 min)
2. **Review implementation plan** (30 min)
3. **Set up development environment** (10 min)
4. **Create feature branch** (2 min)
5. **Start Day 1 tasks** (begin coding)

### For Code Review

1. **Check test coverage** (must be >= 95%)
2. **Run full test suite** (must pass 100%)
3. **Review new files** (discovery.py, recommender.py)
4. **Test CLI manually** (--recommend flag)
5. **Verify no regressions** (existing features work)

### For Testing

1. **Unit tests**: `pytest tests/test_project_detector.py -v`
2. **Integration tests**: `pytest tests/test_template_discovery_e2e.py -v`
3. **Coverage**: `pytest --cov=src/mcpi/templates --cov-report=html`
4. **Manual test**: `mcpi add postgres --recommend` in test project

---

**Status**: Ready to implement
**Confidence**: 9/10 (high confidence based on evaluation)
**First Task**: Create ProjectContext dataclass (2 hours)
**Ship Date**: ~3 weeks from start (v0.6.0)

---

**Generated by**: Implementation Planner Agent
**Date**: 2025-11-17 08:05:05
**Approved by**: Evaluation Agent (Readiness Score: 85/100)
