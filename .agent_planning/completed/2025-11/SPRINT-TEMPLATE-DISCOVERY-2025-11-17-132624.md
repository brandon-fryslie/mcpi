# Template Discovery Engine - Sprint Backlog v0.6.0

**Generated**: 2025-11-17 13:26:24
**Source Plan**: `PLAN-TEMPLATE-DISCOVERY-2025-11-17-132624.md`
**Source STATUS**: `STATUS-2025-11-17-132221.md`
**Target Version**: v0.6.0
**Sprint Duration**: 3 weeks (15 working days)
**Total Estimated Hours**: 84 hours (~5.6 hours/day)
**Current Status**: DAY 0 - Ready to begin

---

## Sprint Goals

**Week 1 Goal**: Detection infrastructure works programmatically + templates have metadata
**Week 2 Goal**: Recommendations work end-to-end with 95%+ test coverage
**Week 3 Goal**: CLI integration polished and ready to ship v0.6.0

**Critical Success Factor**: Test-first approach - write tests as you implement

---

## Week 1: Detection Infrastructure & Template Metadata

### Day 1 (Monday) - Foundation

**Goal**: Basic detection infrastructure exists
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **Setup** (30 min)
   - Create feature branch: `git checkout -b feature/template-discovery`
   - Create file: `src/mcpi/templates/discovery.py`
   - Create file: `tests/test_project_detector.py`
   - Verify branch and files exist

2. **P0-1: ProjectContext Dataclass** (2 hours)
   - Define `ProjectContext` with all fields
   - Add type hints and docstrings
   - Implement `__str__` method for debugging
   - Write 3-5 basic tests
   - **✓ Done when**: Can instantiate ProjectContext and tests pass

**Afternoon (3 hours)**:
3. **P0-2: Docker Detection (Part 1)** (3 hours)
   - Create `ProjectDetector` class skeleton
   - Implement `_detect_docker()` method
   - Check for docker-compose.yml presence
   - Check for Dockerfile presence
   - Write 5-8 tests for Docker detection
   - **✓ Done when**: Can detect Docker files, tests pass

**Deliverable**:
- `discovery.py` created with ProjectContext + ProjectDetector stub
- 8-13 tests written and passing
- Manual test: Can detect Docker in a test project

**Quality Gate**: `pytest tests/test_project_detector.py -v` passes

---

### Day 2 (Tuesday) - Docker Parsing & Language Detection

**Goal**: Multi-dimensional project detection works
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **P0-2: Docker Detection (Part 2)** (3 hours)
   - Implement `_parse_docker_compose()` with PyYAML
   - Extract service names from docker-compose.yml
   - Handle YAML parsing errors gracefully
   - Write 5-7 tests for service parsing
   - Test with realistic docker-compose.yml examples
   - **✓ Done when**: Can parse service names, handles errors

**Afternoon (3 hours)**:
2. **P0-3: Language Detection** (3 hours)
   - Implement `_detect_language()` method
   - Detect Node.js (package.json)
   - Detect Python (requirements.txt, pyproject.toml)
   - Detect Go (go.mod)
   - Write 8-10 tests for language detection
   - **✓ Done when**: Can detect 3 languages, tests pass

**Deliverable**:
- Docker service parsing works
- Language detection works
- 13-17 additional tests passing
- Total tests: ~25 passing

**Quality Gate**: Manual test with Node.js + Docker project

**Manual Verification**:
```bash
mkdir -p /tmp/test-project
cd /tmp/test-project
echo '{"name": "test"}' > package.json
cat > docker-compose.yml <<EOF
services:
  postgres:
    image: postgres:15
  redis:
    image: redis:7
EOF

python -c "
from pathlib import Path
from mcpi.templates.discovery import ProjectDetector

detector = ProjectDetector()
context = detector.detect(Path('/tmp/test-project'))
print(f'Language: {context.language}')
print(f'Docker Compose: {context.has_docker_compose}')
print(f'Services: {context.docker_services}')
"
# Expected: Language: nodejs, Docker Compose: True, Services: ['postgres', 'redis']
```

---

### Day 3 (Wednesday) - Database Detection & Model Extension

**Goal**: Detection complete + template models extended
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **P0-4: Database Detection** (2 hours)
   - Implement `_detect_database()` method
   - Parse databases from docker-compose services
   - Support postgres, mysql, redis, mongodb
   - Write 6-8 tests for database detection
   - **✓ Done when**: Can detect databases from services

2. **P0-5: ProjectDetector Integration** (1 hour)
   - Wire up `detect()` main method
   - Call all detection methods
   - Write 3-5 integration tests with realistic projects
   - **✓ Done when**: Full detection works end-to-end

**Afternoon (3 hours)**:
3. **P0-6: Extend ServerTemplate Model** (3 hours)
   - Add `best_for: list[str]` field to models.py
   - Add `keywords: list[str]` field
   - Add `recommendations: Optional[dict]` field
   - Make all fields optional with defaults
   - Write 5-7 tests for model validation
   - Test backward compatibility (old templates still load)
   - **✓ Done when**: Extended model validates, tests pass

**Deliverable**:
- Detection infrastructure 100% complete
- ServerTemplate model extended
- 14-20 additional tests passing
- Total tests: ~40 passing

**Quality Gate**:
- Run full detector test suite: `pytest tests/test_project_detector.py -v`
- Verify existing templates still load: `pytest tests/test_template*.py -v`

---

### Day 4 (Thursday) - Template Metadata & Scoring Foundation

**Goal**: All templates have metadata + scoring algorithm works
**Hours**: 7 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **P0-7: Update Template YAML Files** (3 hours)
   - Add metadata to postgres templates (3 files)
   - Add metadata to github templates (3 files)
   - Add metadata to filesystem templates (3 files)
   - Add metadata to slack templates (2 files)
   - Add metadata to brave-search template (1 file)
   - Validate YAML syntax after each edit
   - **✓ Done when**: All 12 templates have complete metadata

**Afternoon (4 hours)**:
2. **P0-8: Scoring Algorithm** (3 hours)
   - Create `src/mcpi/templates/recommender.py`
   - Implement `_score_template()` method
   - Define scoring weights (docker=0.4, language=0.3, service=0.5)
   - Generate human-readable reasons
   - Write 8-10 tests for scoring
   - **✓ Done when**: Scoring returns confidence + reasons

3. **P0-9: TemplateRecommendation Dataclass** (1 hour)
   - Define `TemplateRecommendation` dataclass
   - Implement sorting by confidence
   - Write 3-5 tests
   - **✓ Done when**: Can create and sort recommendations

**Deliverable**:
- All 12 templates have metadata
- Scoring algorithm works
- 11-15 additional tests passing
- Total tests: ~55 passing

**Quality Gate**:
- Templates load: `mcpi add postgres --list-templates`
- Scoring test: Manual test with mock template and context

---

### Day 5 (Friday) - Week 1 Testing & Wrap-Up

**Goal**: Week 1 validated with high test coverage
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **P1-15: Unit Tests - Detection (Part 1)** (3 hours)
   - Review all detection code for gaps
   - Write additional tests for edge cases
   - Test corrupted YAML handling
   - Test missing files handling
   - Test polyglot projects
   - **✓ Done when**: Coverage >= 95% for discovery.py

**Afternoon (3 hours)**:
2. **Code Review & Cleanup** (2 hours)
   - Self-review all Week 1 code
   - Run black, ruff, mypy on new code
   - Fix any TODOs or FIXMEs
   - Improve docstrings where needed
   - **✓ Done when**: All quality checks pass

3. **Week 1 Verification** (1 hour)
   - Run full test suite
   - Verify coverage >= 95% on discovery.py
   - Manual test with real projects (mcpi, other projects)
   - Document any issues found
   - **✓ Done when**: Confidence Week 1 is solid

**Deliverable**:
- Week 1 complete with high quality
- Test coverage >= 95% on new code
- All quality checks passing
- Ready to start Week 2

**Quality Gate**:
```bash
pytest tests/test_project_detector.py --cov=src/mcpi/templates/discovery --cov-report=term
# Target: 95%+ coverage

pytest tests/test_template*.py -v
# All tests pass
```

**Week 1 Retrospective**:
- What went well?
- What blocked progress?
- Adjust Week 2 plan if needed

---

## Week 2: Recommendation Engine & Testing

### Day 6 (Monday) - TemplateRecommender Core

**Goal**: Recommendation engine works programmatically
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (4 hours)**:
1. **P0-10: TemplateRecommender Class** (4 hours)
   - Implement `TemplateRecommender` class
   - Implement `recommend()` method
   - Integrate ProjectDetector
   - Filter by confidence threshold (0.3)
   - Sort by confidence descending
   - Handle errors gracefully (server not found, etc.)
   - **✓ Done when**: Can get ranked recommendations for a server

**Afternoon (2 hours)**:
2. **P0-10: TemplateRecommender Tests (Part 1)** (2 hours)
   - Write 5-7 basic tests for recommend()
   - Test ranking by confidence
   - Test threshold filtering
   - Test graceful failures
   - **✓ Done when**: Basic recommendation flow works

**Deliverable**:
- TemplateRecommender class complete
- Recommendations work programmatically
- 5-7 recommender tests passing

**Quality Gate**:
Manual test shows postgres/docker recommended for Docker project:
```bash
python -c "
from pathlib import Path
from mcpi.templates.recommender import create_default_template_recommender

recommender = create_default_template_recommender()
recs = recommender.recommend('postgres', Path('/tmp/docker-project'))
for rec in recs:
    print(f'{rec.template.name}: {rec.confidence*100:.0f}% - {rec.reasons}')
"
# Expected: docker at top with high confidence
```

---

### Day 7 (Tuesday) - Factory Functions & Scoring Tests

**Goal**: Recommender integrates with existing system
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (2 hours)**:
1. **P0-11: Factory Functions** (2 hours)
   - Implement `create_default_template_recommender()`
   - Implement `create_test_template_recommender()`
   - Add exports to `__init__.py`
   - Write 3-5 factory tests
   - **✓ Done when**: Factories create working recommenders

**Afternoon (4 hours)**:
2. **P1-16: Unit Tests - Scoring** (4 hours)
   - Write tests for all scoring scenarios
   - Test perfect match (score = 1.0)
   - Test partial match (0.3 < score < 1.0)
   - Test no match (score < 0.3)
   - Test docker service match bonus
   - Test ranking and sorting
   - Test reason generation
   - **✓ Done when**: Coverage >= 95% for scoring code

**Deliverable**:
- Factory functions complete
- Comprehensive scoring tests
- 7-12 additional tests passing
- Total tests: ~70 passing

**Quality Gate**:
```bash
pytest tests/test_template_recommender.py --cov=src/mcpi/templates/recommender
# Target: 95%+ coverage
```

---

### Day 8 (Wednesday) - Integration Testing

**Goal**: End-to-end flow works with real data
**Hours**: 6 hours
**Status**: NOT STARTED

**All Day (6 hours)**:
1. **P1-17: Integration Tests - End-to-End** (6 hours)
   - Create `tests/test_template_discovery_e2e.py`
   - Test: Docker project → postgres/docker recommended
   - Test: No Docker → postgres/local-development recommended
   - Test: Node.js project → appropriate templates
   - Test: Empty project → graceful fallback
   - Test with all 12 templates in appropriate contexts
   - Use realistic test project structures
   - **✓ Done when**: E2E scenarios pass with real templates

**Deliverable**:
- E2E test file created
- 8-10 integration tests passing
- Total tests: ~80 passing
- Confidence in full workflow

**Quality Gate**:
```bash
pytest tests/test_template_discovery_e2e.py -v
# All E2E scenarios pass
```

---

### Day 9 (Thursday) - Edge Cases & Polish

**Goal**: Edge cases handled, Week 2 code solid
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **P2-18: Edge Case Testing** (3 hours)
   - Test: Docker detected but not used
   - Test: Polyglot project (multiple languages)
   - Test: Monorepo (detect from cwd)
   - Test: CI/CD docker-compose mistaken for app
   - Test: All templates score equally (tie-breaking)
   - Test: No templates pass threshold
   - Test: Old templates without metadata
   - Test: Invalid metadata caught by validation
   - **✓ Done when**: All edge cases pass

**Afternoon (3 hours)**:
2. **Code Review & Refactoring** (2 hours)
   - Review all Week 2 code
   - Refactor complex methods
   - Improve error messages
   - Enhance docstrings
   - **✓ Done when**: Code is clean and maintainable

3. **P1-15: Unit Tests - Detection (Part 2)** (1 hour)
   - Fill any gaps in detection test coverage
   - Ensure 95%+ coverage on discovery.py
   - **✓ Done when**: Coverage target met

**Deliverable**:
- Edge cases covered
- Code polished and reviewed
- 8-10 additional tests passing
- Total tests: ~90 passing

**Quality Gate**:
```bash
pytest --cov=src/mcpi/templates --cov-report=term
# Target: 95%+ coverage on all templates code
```

---

### Day 10 (Friday) - Week 2 Testing Marathon

**Goal**: Week 2 complete with exceptional quality
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (2 hours)**:
1. **P2-20: Performance Testing** (2 hours)
   - Write performance benchmarks
   - Test detection speed (< 100ms target)
   - Test recommendation speed (< 50ms target)
   - Test with large projects
   - Profile slow operations
   - Add caching if needed
   - **✓ Done when**: Performance targets met

**Afternoon (4 hours)**:
2. **Week 2 Testing Marathon** (4 hours)
   - Run full test suite 3+ times
   - Test with variety of project types
   - Fix any bugs found
   - Achieve 95%+ coverage on all new code
   - Manual testing with real projects
   - **✓ Done when**: All tests pass consistently

**Deliverable**:
- Week 2 complete with high quality
- Performance targets met
- 95%+ coverage on all new code
- Ready for CLI integration

**Quality Gate**:
```bash
pytest --cov=src/mcpi/templates --cov-report=html
# Open htmlcov/index.html - verify 95%+ coverage

time pytest tests/test_template_discovery_e2e.py
# Verify reasonable performance (< 5 seconds total)
```

**Week 2 Retrospective**:
- Recommendation quality assessment
- Any scoring weight adjustments needed?
- Ready for CLI integration?

---

## Week 3: CLI Integration & Ship

### Day 11 (Monday) - CLI Integration

**Goal**: --recommend flag works in CLI
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (4 hours)**:
1. **P1-12: Add --recommend Flag** (4 hours)
   - Update `src/mcpi/cli.py`
   - Add `@click.option("--recommend")`
   - Add recommendation logic to add command
   - Integrate with existing template selection flow
   - Handle edge cases (no recommendations, errors)
   - Test flag in real terminal
   - **✓ Done when**: --recommend flag triggers recommendations

**Afternoon (2 hours)**:
2. **P1-13: Rich Console Output** (2 hours)
   - Implement `_handle_recommendations()` function
   - Format recommendation header with confidence
   - Format "Why this template?" section with reasons
   - Show alternative templates (top 3)
   - Add color coding (cyan, dim)
   - Test output in real terminal
   - **✓ Done when**: Output matches proposal examples

**Deliverable**:
- --recommend flag works
- Beautiful Rich output
- Manual CLI testing successful

**Quality Gate**:
```bash
cd ~/icode/mcpi
mcpi add postgres --recommend
# Verify output looks professional and matches examples
```

---

### Day 12 (Tuesday) - CLI Polish & Documentation

**Goal**: CLI integration complete, documented
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **P1-14: Integrate with Template Selection Flow** (3 hours)
   - Refactor template selection code
   - Add confirmation prompt for recommendations
   - Handle accept/decline flows
   - Preserve existing behavior (no breaking changes)
   - Write 5-8 CLI integration tests
   - **✓ Done when**: User can accept/decline recommendations

**Afternoon (3 hours)**:
2. **P2-19: Documentation** (3 hours)
   - Update README.md with --recommend examples
   - Update CLAUDE.md with usage guide and architecture
   - Create docs/TEMPLATE_METADATA_GUIDE.md
   - Update CLI help text
   - Create CHANGELOG entry for v0.6.0
   - **✓ Done when**: All docs updated and accurate

**Deliverable**:
- CLI integration complete
- Comprehensive documentation
- 5-8 CLI tests passing
- Total tests: ~100 passing

**Quality Gate**:
- New user can understand feature from README
- Template authors can add metadata from guide
- CLI help is clear: `mcpi add --help`

---

### Day 13 (Wednesday) - Final Testing & Bug Fixes

**Goal**: All tests pass, bugs fixed
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **Comprehensive Test Run** (3 hours)
   - Run full test suite (all tests)
   - Test in different project types (dogfooding)
   - Test edge cases manually
   - Verify no regressions in existing features
   - Test on fresh environment (if possible)
   - **✓ Done when**: 100% tests pass

**Afternoon (3 hours)**:
2. **Bug Fixing** (3 hours)
   - Fix any bugs found in testing
   - Address any TODOs or FIXMEs
   - Improve error messages
   - Handle any edge cases discovered
   - Re-run tests after each fix
   - **✓ Done when**: No known bugs remain

**Deliverable**:
- Feature complete with no known bugs
- All tests passing (100%)
- Ready for final polish

**Quality Gate**:
```bash
pytest --tb=short -v
# 100% pass rate (ignore pre-existing failures in other subsystems)

pytest tests/test_template*.py tests/test_project_detector.py tests/test_template_recommender.py tests/test_template_discovery_e2e.py -v
# ALL new tests pass
```

---

### Day 14 (Thursday) - Polish & Pre-Ship Review

**Goal**: Code ready for merge
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (4 hours)**:
1. **P3-21: Final Integration & Polish** (4 hours)
   - Run black, ruff, mypy on all code
   - Self-review entire feature (all files changed)
   - Verify CLI output looks professional
   - Test in real terminal (not just tests)
   - Check error handling is user-friendly
   - Ensure all acceptance criteria met
   - **✓ Done when**: Feature is "shippable"

**Afternoon (2 hours)**:
2. **Pre-Ship Checklist** (2 hours)
   - [ ] All tests passing (100%)
   - [ ] Coverage >= 95% for new code
   - [ ] Documentation complete and accurate
   - [ ] No regressions in existing features
   - [ ] Git history is clean (good commit messages)
   - [ ] CHANGELOG updated
   - [ ] No TODOs or FIXMEs (or tracked in backlog)
   - **✓ Done when**: Checklist 100% complete

**Deliverable**:
- Feature ready for PR
- Pre-ship checklist complete
- Confidence: ready to ship

**Quality Gate**:
```bash
# Run full quality suite
pytest --cov=src/mcpi/templates --cov-report=term
black src/ tests/ --check
ruff check src/ tests/
mypy src/

# All pass
```

---

### Day 15 (Friday) - Ship v0.6.0

**Goal**: Merge to main, ship v0.6.0
**Hours**: 6 hours
**Status**: NOT STARTED

**Morning (3 hours)**:
1. **Create Pull Request** (1 hour)
   - Create PR from feature/template-discovery branch
   - Write comprehensive PR description
   - Link to planning documents
   - List all changes and acceptance criteria met
   - **✓ Done when**: PR is created

2. **Final Verification** (2 hours)
   - Review PR diff carefully (every line)
   - Test in fresh environment if possible
   - Verify CI/CD passes
   - Address any review comments
   - Manual E2E verification
   - **✓ Done when**: PR is approved

**Afternoon (3 hours)**:
3. **Ship v0.6.0** (3 hours)
   - Merge PR to main
   - Verify merge successful
   - Tag release v0.6.0: `git tag v0.6.0`
   - Push tag: `git push origin v0.6.0`
   - Update version in pyproject.toml if needed
   - Announce feature (optional - social media, Discord, etc.)
   - **✓ Done when**: v0.6.0 is live

**Deliverable**:
- v0.6.0 shipped to users
- Users can install and use --recommend flag
- Feature is live in production

**Quality Gate**:
```bash
# Verify on main branch
git checkout main
git pull
mcpi --version
# Should show v0.6.0

mcpi add postgres --recommend
# Works for end users
```

**Post-Ship**:
- Monitor for issues/feedback
- Begin gathering user feedback
- Plan v0.6.1 improvements based on feedback

---

## Sprint Metrics

### Velocity Tracking

| Week | Planned Hours | Actual Hours | Tasks Completed | Notes |
|------|---------------|--------------|-----------------|-------|
| Week 1 | 31 hours | ___ | ___/11 tasks | Detection + Metadata |
| Week 2 | 30 hours | ___ | ___/6 tasks | Recommender + Tests |
| Week 3 | 30 hours | ___ | ___/4 tasks | CLI + Ship |
| **Total** | **91 hours** | **___** | **___/21 tasks** | |

### Daily Progress Tracker

**Week 1**:
- [ ] Day 1: P0-1, P0-2 (Part 1) - ProjectContext + Docker detection
- [ ] Day 2: P0-2 (Part 2), P0-3 - Docker parsing + Language detection
- [ ] Day 3: P0-4, P0-5, P0-6 - Database + Integration + Model extension
- [ ] Day 4: P0-7, P0-8, P0-9 - Template metadata + Scoring + Data model
- [ ] Day 5: P1-15 (Part 1), Code review - Testing + Polish

**Week 2**:
- [ ] Day 6: P0-10 (Part 1) - TemplateRecommender class
- [ ] Day 7: P0-11, P1-16 - Factories + Scoring tests
- [ ] Day 8: P1-17 - Integration tests E2E
- [ ] Day 9: P2-18, P1-15 (Part 2) - Edge cases + Detection tests
- [ ] Day 10: P2-20, Testing marathon - Performance + Verification

**Week 3**:
- [ ] Day 11: P1-12, P1-13 - CLI flag + Rich output
- [ ] Day 12: P1-14, P2-19 - Integration + Documentation
- [ ] Day 13: Testing + Bug fixes - All tests pass
- [ ] Day 14: P3-21, Pre-ship checklist - Polish + Verification
- [ ] Day 15: PR + Ship - v0.6.0 LIVE

---

## Contingency Plans

### If Running Behind Schedule

**Week 1 Delays** (cut scope, maintain quality):
- Reduce database detection complexity (postgres only)
- Simplify metadata (3 templates initially)
- Defer performance optimization

**Week 2 Delays** (cut nice-to-haves):
- Reduce edge case coverage (focus critical paths)
- Skip performance testing (optimize in v0.6.1)
- Reduce integration tests (90% instead of 95%)

**Week 3 Delays** (ship MVP):
- Simplify CLI output (basic text instead of Rich)
- Reduce documentation scope (README only)
- Ship v0.6.0-beta first, polish in v0.6.1

### If Ahead of Schedule

**Bonus Features** (nice to have):
- Framework detection (Django, Express, React)
- Environment detection (production vs development)
- Additional detectors (cloud provider, CI/CD)
- Caching for performance
- User feedback mechanism

---

## Daily Standup Template

**Date**: ___________

**Yesterday**:
- Completed: _________________
- Tests written: ___ tests
- Blockers: _________________

**Today**:
- Plan: _________________
- Goal: _________________
- Tests to write: ___ tests

**Blockers/Risks**:
- _________________

**Notes**:
- _________________

---

## Quality Gates Summary

| Day | Quality Gate | Pass Criteria |
|-----|--------------|---------------|
| Day 1 | Detection setup | ProjectContext + tests pass |
| Day 2 | Docker parsing | Service extraction works |
| Day 3 | Full detection | E2E detection works |
| Day 5 | Week 1 complete | 95%+ coverage on discovery.py |
| Day 8 | E2E tests | Integration tests pass |
| Day 10 | Week 2 complete | 95%+ coverage on all new code |
| Day 13 | All tests pass | 100% pass rate on new tests |
| Day 14 | Pre-ship | Checklist 100% complete |
| Day 15 | Ship | v0.6.0 live in production |

---

## Sprint Retrospective Template

**After v0.6.0 ships, conduct retrospective**:

### What Went Well
- _________________
- _________________

### What Didn't Go Well
- _________________
- _________________

### What to Improve
- _________________
- _________________

### Action Items for Next Sprint
- _________________
- _________________

### Metrics Review
- Actual time vs. planned time: ___
- Test coverage achieved: ___%
- Bugs found in production: ___
- User feedback: _________________

---

**Generated by**: Implementation Planner Agent
**Date**: 2025-11-17 13:26:24
**Status**: Ready to execute
**First Task**: Day 1 - Create feature branch and ProjectContext dataclass
**Expected Ship Date**: ~2025-12-08 (3 weeks from start)
