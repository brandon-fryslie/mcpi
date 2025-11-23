# Template Discovery Engine - Sprint Backlog

**Generated**: 2025-11-17 08:05:05
**Source Plan**: `PLAN-TEMPLATE-DISCOVERY-2025-11-17-080505.md`
**Target Version**: v0.6.0
**Sprint Duration**: 3 weeks (15 working days)
**Total Estimated Hours**: 84 hours (~5.6 hours/day)

---

## Sprint Goals

**Week 1**: Detection infrastructure works programmatically
**Week 2**: Recommendations work end-to-end with comprehensive tests
**Week 3**: CLI integration polished and ready to ship

---

## Week 1: Detection Infrastructure & Template Metadata

### Day 1 - Monday: Project Detection Foundation

**Goal**: Basic detection infrastructure works

**Tasks**:
1. **P0-1: ProjectContext Data Model** (2 hours)
   - Create `src/mcpi/templates/discovery.py`
   - Define `ProjectContext` dataclass
   - Add type hints and defaults
   - Write docstrings
   - ✓ Definition: Done when dataclass instantiates with all fields

2. **P0-2: Docker Detection** (4 hours)
   - Implement `ProjectDetector` class skeleton
   - Add `_detect_docker()` method
   - Check for docker-compose.yml and Dockerfile
   - Parse docker-compose.yml with PyYAML
   - Handle YAML parsing errors gracefully
   - ✓ Definition: Done when docker detection works with real docker-compose.yml

**Deliverable**: Can detect Docker usage in a project

**Quality Gate**: Run manual test with sample docker-compose.yml

---

### Day 2 - Tuesday: Language & Database Detection

**Goal**: Multi-dimensional project detection works

**Tasks**:
1. **P0-3: Language Detection** (3 hours)
   - Add `_detect_language()` method
   - Check for package.json (Node.js)
   - Check for requirements.txt/pyproject.toml (Python)
   - Check for go.mod (Go)
   - Handle polyglot projects
   - ✓ Definition: Done when language detection works for 3+ languages

2. **P0-4: Database Detection** (3 hours)
   - Add `_detect_database()` method
   - Parse databases from docker-compose services
   - Check for DATABASE_URL in .env files (optional)
   - ✓ Definition: Done when can identify postgres, mysql, redis from compose

**Deliverable**: ProjectDetector can analyze realistic projects

**Quality Gate**: Test with 3 different project types (Node.js+Docker, Python local, Go+containers)

---

### Day 3 - Wednesday: Detection Integration & Template Metadata

**Goal**: Detection complete, templates have metadata

**Tasks**:
1. **P0-5: ProjectDetector Integration** (2 hours)
   - Implement `detect(project_path)` main method
   - Wire up all detection methods
   - Add integration tests with real project structures
   - ✓ Definition: Done when can detect all project characteristics in one call

2. **P0-6: Extend ServerTemplate Model** (3 hours)
   - Update `src/mcpi/templates/models.py`
   - Add `best_for`, `keywords`, `recommendations` fields
   - Make all fields optional (backward compatible)
   - Add unit tests for model validation
   - ✓ Definition: Done when templates load with and without new fields

3. **P0-7: Update Template YAML Files** (Start - 1 hour)
   - Begin adding metadata to postgres templates (3 files)
   - Validate YAML syntax
   - ✓ Definition: Done when postgres templates have complete metadata

**Deliverable**: Detection works end-to-end, 3 templates have metadata

**Quality Gate**: Run TemplateManager.load_templates() successfully

---

### Day 4 - Thursday: Template Metadata & Scoring Foundation

**Goal**: All templates have metadata, scoring algorithm designed

**Tasks**:
1. **P0-7: Update Template YAML Files** (Continue - 2 hours)
   - Add metadata to github templates (3 files)
   - Add metadata to filesystem templates (3 files)
   - Add metadata to slack templates (2 files)
   - Add metadata to brave-search template (1 file)
   - Validate all templates load correctly
   - ✓ Definition: Done when all 12 templates have complete metadata

2. **P0-8: Scoring Algorithm** (3 hours)
   - Design scoring weights
   - Implement `_score_template()` method
   - Generate explanations (reasons)
   - Test with various match scenarios
   - ✓ Definition: Done when scoring returns confidence + reasons

3. **P0-9: TemplateRecommendation Data Model** (1 hour)
   - Create `TemplateRecommendation` dataclass
   - Add type hints
   - ✓ Definition: Done when can create recommendation instances

**Deliverable**: Scoring algorithm works, all templates ready

**Quality Gate**: Manually test scoring with sample project + templates

---

### Day 5 - Friday: Week 1 Wrap-Up & Testing

**Goal**: Detection + Scoring validated with tests

**Tasks**:
1. **P1-15: Unit Tests - Detection** (4 hours)
   - Write tests for Docker detection
   - Write tests for language detection
   - Write tests for database detection
   - Write tests for ProjectDetector integration
   - Test edge cases (missing files, corrupted YAML)
   - ✓ Definition: Done when coverage >= 95% for discovery.py

2. **Code Review & Cleanup** (2 hours)
   - Self-review all Week 1 code
   - Fix any TODOs or FIXMEs
   - Run black, ruff, mypy
   - Ensure all tests pass
   - ✓ Definition: Done when all quality checks pass

**Deliverable**: Week 1 complete with high test coverage

**Quality Gate**: pytest passes with 95%+ coverage on new code

---

## Week 2: Recommendation Engine & Testing

### Day 6 - Monday: TemplateRecommender Core

**Goal**: Recommendation engine works programmatically

**Tasks**:
1. **P0-10: TemplateRecommender Class** (6 hours)
   - Create `src/mcpi/templates/recommender.py`
   - Implement `TemplateRecommender` class
   - Implement `recommend()` method
   - Integrate ProjectDetector
   - Filter by confidence threshold (0.3)
   - Sort by confidence descending
   - ✓ Definition: Done when can get ranked recommendations for a server

**Deliverable**: TemplateRecommender returns ranked recommendations

**Quality Gate**: Manual test shows postgres/docker recommended for Docker project

---

### Day 7 - Tuesday: Factory Functions & Integration

**Goal**: Recommender integrates with existing system

**Tasks**:
1. **P0-11: Factory Functions** (2 hours)
   - Create `create_default_template_recommender()`
   - Create `create_test_template_recommender()`
   - Add to `__init__.py` exports
   - Test factory functions
   - ✓ Definition: Done when factories create working recommender instances

2. **P1-16: Unit Tests - Scoring** (4 hours)
   - Write tests for scoring algorithm
   - Test perfect match (score = 1.0)
   - Test partial match (0.3 < score < 1.0)
   - Test no match (score < 0.3, filtered)
   - Test ranking and sorting
   - Test reason generation
   - ✓ Definition: Done when coverage >= 95% for recommender.py

**Deliverable**: Recommendation engine fully tested

**Quality Gate**: All scoring tests pass, edge cases covered

---

### Day 8 - Wednesday: Integration Testing

**Goal**: End-to-end flow works with real data

**Tasks**:
1. **P1-17: Integration Tests - End-to-End** (6 hours)
   - Create `tests/test_template_discovery_e2e.py`
   - Test: Docker project → postgres/docker recommended
   - Test: No Docker → postgres/local-development recommended
   - Test: Node.js project → appropriate templates
   - Test: No recommendations → graceful fallback
   - Test with all 12 templates
   - Use MCPTestHarness for realistic environment
   - ✓ Definition: Done when E2E scenarios pass with real templates

**Deliverable**: Recommendation flow validated end-to-end

**Quality Gate**: Integration tests pass with realistic test data

---

### Day 9 - Thursday: Edge Cases & Polish

**Goal**: Edge cases handled, Week 2 code solid

**Tasks**:
1. **P2-18: Edge Case Testing** (4 hours)
   - Test: Docker detected but not used
   - Test: Polyglot project (multiple languages)
   - Test: Monorepo (detect from cwd)
   - Test: CI/CD docker-compose (only check root)
   - Test: All templates score equally (tie-breaking)
   - Test: No templates pass threshold
   - Test: Old templates without metadata
   - Test: Invalid metadata (Pydantic validation)
   - ✓ Definition: Done when all edge cases pass

2. **Code Review & Refactoring** (2 hours)
   - Review all Week 2 code
   - Refactor any complex methods
   - Improve error messages
   - Update docstrings
   - ✓ Definition: Done when code is clean and documented

**Deliverable**: Edge cases covered, code polished

**Quality Gate**: All tests pass (unit + integration + edge cases)

---

### Day 10 - Friday: Week 2 Wrap-Up & Performance

**Goal**: Week 2 complete, performance validated

**Tasks**:
1. **P2-20: Performance Testing** (2 hours)
   - Test detection speed (< 100ms target)
   - Test recommendation speed (< 50ms target)
   - Profile slow operations
   - Add caching if needed
   - ✓ Definition: Done when performance meets targets

2. **Week 2 Testing Marathon** (4 hours)
   - Run full test suite multiple times
   - Test with variety of project types
   - Fix any bugs found
   - Achieve 95%+ coverage on all new code
   - ✓ Definition: Done when all tests pass consistently

**Deliverable**: Week 2 complete with high quality

**Quality Gate**: Coverage >= 95%, performance targets met

---

## Week 3: CLI Integration & Ship Preparation

### Day 11 - Monday: CLI Integration

**Goal**: --recommend flag works in CLI

**Tasks**:
1. **P1-12: Add --recommend Flag** (4 hours)
   - Update `src/mcpi/cli.py`
   - Add `@click.option("--recommend")`
   - Add recommendation logic to add command
   - Integrate with existing template selection flow
   - Handle edge cases (no recommendations, no templates)
   - ✓ Definition: Done when --recommend flag triggers recommendations

2. **P1-13: Rich Console Output** (2 hours)
   - Format recommendation header with confidence
   - Format "Why this template?" section with reasons
   - Show alternative templates (top 3)
   - Add color coding (cyan, dim)
   - Test output in real terminal
   - ✓ Definition: Done when output matches proposal examples

**Deliverable**: --recommend flag works with beautiful output

**Quality Gate**: CLI test in terminal looks professional

---

### Day 12 - Tuesday: CLI Polish & Documentation

**Goal**: CLI integration complete, documented

**Tasks**:
1. **P1-14: Integrate with Template Selection Flow** (3 hours)
   - Refactor template selection code
   - Add confirmation prompt for recommendations
   - Handle accept/decline flows
   - Preserve existing behavior (no breaking changes)
   - Add CLI tests
   - ✓ Definition: Done when user can accept/decline recommendations

2. **P2-19: Documentation** (3 hours)
   - Update README.md with --recommend examples
   - Update CLAUDE.md with usage guide
   - Add "Template Discovery" section to docs
   - Document metadata schema for template authors
   - Update CLI help text
   - Create CHANGELOG entry for v0.6.0
   - ✓ Definition: Done when all docs updated and accurate

**Deliverable**: CLI complete with comprehensive docs

**Quality Gate**: New user can understand feature from README

---

### Day 13 - Wednesday: Final Testing & Bug Fixes

**Goal**: All tests pass, bugs fixed

**Tasks**:
1. **Comprehensive Test Run** (3 hours)
   - Run full test suite (all tests)
   - Test in different project types (dogfooding)
   - Test edge cases manually
   - Verify no regressions in existing features
   - ✓ Definition: Done when 100% tests pass

2. **Bug Fixing** (3 hours)
   - Fix any bugs found in testing
   - Address any TODOs or FIXMEs
   - Improve error messages
   - Handle any edge cases discovered
   - ✓ Definition: Done when no known bugs remain

**Deliverable**: Feature complete with no known bugs

**Quality Gate**: Full test suite passes 3 times in a row

---

### Day 14 - Thursday: Polish & Pre-Ship Review

**Goal**: Code ready for merge

**Tasks**:
1. **P3-21: Final Integration & Polish** (4 hours)
   - Run black, ruff, mypy on all code
   - Self-review entire feature (all files)
   - Verify CLI output looks professional
   - Test in real terminal (not just tests)
   - Ensure all acceptance criteria met
   - ✓ Definition: Done when feature is "shippable"

2. **Pre-Ship Checklist** (2 hours)
   - All tests passing (100%)
   - Coverage >= 95% for new code
   - Documentation complete and accurate
   - No regressions in existing features
   - Git history is clean
   - CHANGELOG updated
   - ✓ Definition: Done when all checklist items checked

**Deliverable**: Feature ready for PR

**Quality Gate**: Pre-ship checklist 100% complete

---

### Day 15 - Friday: Ship to v0.6.0

**Goal**: Merge to main, ship v0.6.0

**Tasks**:
1. **Create Pull Request** (2 hours)
   - Create PR from feature/template-discovery branch
   - Write comprehensive PR description
   - Link to planning documents
   - Request review (or self-review)
   - ✓ Definition: Done when PR is created

2. **Final Verification** (2 hours)
   - Review PR diff carefully
   - Test in fresh environment
   - Verify CI/CD passes
   - Address any review comments
   - ✓ Definition: Done when PR is approved

3. **Ship v0.6.0** (2 hours)
   - Merge PR to main
   - Tag release v0.6.0
   - Push to GitHub
   - Announce feature (optional)
   - ✓ Definition: Done when v0.6.0 is live

**Deliverable**: v0.6.0 shipped to users

**Quality Gate**: Users can install and use --recommend flag

---

## Sprint Metrics

### Velocity Tracking

| Week | Planned Hours | Actual Hours | Tasks Completed | Notes |
|------|---------------|--------------|-----------------|-------|
| Week 1 | 28 hours | ___ | ___/11 tasks | Detection + Metadata |
| Week 2 | 28 hours | ___ | ___/6 tasks | Recommender + Tests |
| Week 3 | 28 hours | ___ | ___/4 tasks | CLI + Ship |
| **Total** | **84 hours** | **___** | **___/21 tasks** | |

### Daily Checklist

Use this to track daily progress:

**Week 1**:
- [ ] Day 1: P0-1, P0-2 complete
- [ ] Day 2: P0-3, P0-4 complete
- [ ] Day 3: P0-5, P0-6, P0-7 (partial) complete
- [ ] Day 4: P0-7 (done), P0-8, P0-9 complete
- [ ] Day 5: P1-15 complete, Week 1 quality gate passed

**Week 2**:
- [ ] Day 6: P0-10 complete
- [ ] Day 7: P0-11, P1-16 complete
- [ ] Day 8: P1-17 complete
- [ ] Day 9: P2-18 complete, code review done
- [ ] Day 10: P2-20 complete, Week 2 quality gate passed

**Week 3**:
- [ ] Day 11: P1-12, P1-13 complete
- [ ] Day 12: P1-14, P2-19 complete
- [ ] Day 13: All tests pass, bugs fixed
- [ ] Day 14: P3-21 complete, pre-ship checklist done
- [ ] Day 15: v0.6.0 shipped

---

## Contingency Plans

### If Running Behind Schedule

**Week 1 Delays**:
- Cut P0-4 (database detection) - can add in v0.6.1
- Simplify scoring algorithm (fewer weights)
- Reduce template metadata (only postgres templates)

**Week 2 Delays**:
- Reduce edge case testing (focus on critical paths)
- Skip performance testing (optimize in v0.6.1)
- Reduce integration test coverage (90% instead of 95%)

**Week 3 Delays**:
- Simplify CLI output (text instead of Rich formatting)
- Reduce documentation scope (README only)
- Ship v0.6.0-beta first, polish later

### If Ahead of Schedule

**Bonus Features** (nice to have):
- Framework detection (Django, Express, React)
- Environment detection (production vs development)
- Caching for performance
- User feedback mechanism (thumbs up/down)
- Additional detectors (cloud provider, CI/CD)

---

## Daily Standup Template

Use this template for daily progress tracking:

**Date**: ___________

**Yesterday**:
- Completed: _________________
- Blockers: _________________

**Today**:
- Plan: _________________
- Goal: _________________

**Blockers/Risks**:
- _________________

**Notes**:
- _________________

---

## Quality Gates Summary

| Week | Quality Gate | Pass Criteria |
|------|--------------|---------------|
| Week 1 | Detection Works | pytest passes with 95%+ coverage on discovery.py |
| Week 2 | Recommender Works | Integration tests pass, coverage >= 95% |
| Week 3 | Ship Ready | Pre-ship checklist 100%, all tests pass |

---

## Sprint Retrospective (Post-Sprint)

After v0.6.0 ships, conduct retrospective:

**What Went Well**:
- _________________

**What Didn't Go Well**:
- _________________

**What to Improve**:
- _________________

**Action Items for Next Sprint**:
- _________________

---

**Generated by**: Implementation Planner Agent
**Date**: 2025-11-17 08:05:05
**Status**: Ready to execute
**First Task**: Day 1, P0-1 - Create ProjectContext dataclass
