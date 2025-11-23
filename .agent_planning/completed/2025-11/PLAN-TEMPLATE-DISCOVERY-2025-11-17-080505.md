# Template Discovery Engine - Implementation Plan

**Generated**: 2025-11-17 08:05:05
**Source STATUS**: `STATUS-TEMPLATE-DISCOVERY-EVALUATION-2025-11-17-080057.md`
**Source Proposal**: `FEATURE_PROPOSAL_POST_v0.5.0_2025-11-17.md`
**Target Version**: v0.6.0
**Readiness Score**: 85/100 (READY TO IMPLEMENT NOW)

---

## Executive Summary

This plan details the implementation of the Template Discovery Engine, a feature that analyzes project context and recommends the best templates for MCP server configuration. The evaluation report confirms this feature is ready for immediate implementation with low risk and high value.

**Key Metrics**:
- Timeline: 2-3 weeks (incremental MVP approach)
- Risk Level: LOW
- Test Coverage Target: 95%+
- Expected Adoption: 40%+ of users

**Foundation**: v0.5.0 Configuration Templates (12 templates, 87% time savings, 100% test pass rate)

---

## 1. Architecture Overview

### 1.1 New Components

**Core Modules** (all in `src/mcpi/templates/`):

1. **discovery.py** (~300 lines)
   - `ProjectContext` dataclass: Detected project characteristics
   - `ProjectDetector` class: Analyzes project files and structure
   - Detection methods: Docker, language, database, framework, environment

2. **recommender.py** (~250 lines)
   - `TemplateRecommendation` dataclass: Template + confidence + reasons
   - `TemplateRecommender` class: Scores and ranks templates
   - Factory functions: `create_default_template_recommender()`, `create_test_template_recommender()`

### 1.2 Extended Components

**Modified Files**:

1. **models.py** (extend `ServerTemplate`)
   - Add `best_for: List[str]` field (tags for matching)
   - Add `keywords: List[str]` field (fuzzy search support)
   - Add `recommendations: Optional[Dict[str, Any]]` field (scoring hints)

2. **cli.py** (add `--recommend` flag)
   - Lines ~1000-1084 (existing template code)
   - Add recommendation logic before template selection
   - Rich formatting for recommendations

**Template Data** (update all 12 templates):
- postgres (3 templates): docker, local-development, production
- github (3 templates): personal-full-access, read-only, public-repos
- filesystem (3 templates): project-files, user-documents, custom-directories
- slack (2 templates): bot-token, limited-channels
- brave-search (1 template): api-key

### 1.3 Integration Points

**Dependency Injection** (DIP Compliant):
```python
# Factory pattern (production)
def create_default_template_recommender() -> TemplateRecommender:
    template_manager = create_default_template_manager()
    return TemplateRecommender(template_manager=template_manager)

# Test pattern (injectable)
def create_test_template_recommender(
    template_manager: TemplateManager
) -> TemplateRecommender:
    return TemplateRecommender(template_manager=template_manager)
```

**No Breaking Changes**:
- All new fields are optional
- Existing templates work without modification
- `--recommend` flag is optional
- Falls back to current behavior if no recommendations

---

## 2. Work Breakdown Structure

### Phase 1: Detection Infrastructure (Week 1)

#### P0-1: ProjectContext Data Model
**Status**: Not Started
**Effort**: Small (2 hours)
**Dependencies**: None
**Spec Reference**: Proposal lines 886-896 • **Status Reference**: Section 2.1

**Description**:
Create the `ProjectContext` dataclass to hold detected project characteristics. This is the foundation for all detection logic.

**Acceptance Criteria**:
- [ ] `ProjectContext` dataclass defined in `src/mcpi/templates/discovery.py`
- [ ] Fields: `root_path`, `has_docker`, `has_docker_compose`, `docker_services`, `language`, `databases`, `environment`
- [ ] All fields have sensible defaults (empty lists, False booleans)
- [ ] Type hints for all fields
- [ ] Docstring explaining each field

**Technical Notes**:
- Use `@dataclass` decorator with `field(default_factory=list)` for list fields
- Keep immutable where possible (frozen=True if no mutation needed)
- Consider adding `__str__` for debugging output

---

#### P0-2: Docker Detection
**Status**: Not Started
**Effort**: Medium (4 hours)
**Dependencies**: P0-1
**Spec Reference**: Proposal lines 960-972 • **Status Reference**: Section 2.1

**Description**:
Implement Docker detection logic to identify projects using Docker and Docker Compose. Parse docker-compose.yml to extract service names.

**Acceptance Criteria**:
- [ ] `ProjectDetector._detect_docker()` method implemented
- [ ] Detects `docker-compose.yml` existence
- [ ] Detects `Dockerfile` existence
- [ ] Parses docker-compose.yml to extract service names (graceful failure)
- [ ] Sets `context.has_docker_compose`, `context.has_docker`, `context.docker_services`
- [ ] Unit tests cover: docker-compose only, Dockerfile only, both, neither, corrupted YAML

**Technical Notes**:
- Use PyYAML (already installed) for parsing
- Wrap YAML parsing in try/except (return empty list on failure)
- Only check project root, not subdirectories (avoid false positives)
- Test with real docker-compose.yml examples

---

#### P0-3: Language Detection
**Status**: Not Started
**Effort**: Small (3 hours)
**Dependencies**: P0-1
**Spec Reference**: Proposal lines 974-981 • **Status Reference**: Section 2.1

**Description**:
Detect programming language by checking for package manager files (package.json, requirements.txt, go.mod, etc.).

**Acceptance Criteria**:
- [ ] `ProjectDetector._detect_language()` method implemented
- [ ] Detects Node.js (package.json)
- [ ] Detects Python (requirements.txt, pyproject.toml)
- [ ] Detects Go (go.mod)
- [ ] Sets `context.language` to appropriate string
- [ ] Unit tests cover: each language, polyglot projects, no language detected

**Technical Notes**:
- Check for multiple indicators (pyproject.toml OR requirements.txt)
- Handle polyglot projects (choose primary language or set first detected)
- Add new languages incrementally (start with 3-4 most common)

---

#### P0-4: Database Detection
**Status**: Not Started
**Effort**: Medium (3 hours)
**Dependencies**: P0-1, P0-2
**Spec Reference**: Evaluation Section 2.1 • **Status Reference**: Section 2.1

**Description**:
Detect database usage by parsing docker-compose services and checking for common database indicators.

**Acceptance Criteria**:
- [ ] `ProjectDetector._detect_database()` method implemented
- [ ] Identifies databases from docker-compose services (postgres, mysql, redis, mongodb)
- [ ] Checks for .env files with DATABASE_URL patterns
- [ ] Sets `context.databases` list
- [ ] Unit tests cover: docker-compose databases, env file databases, none detected

**Technical Notes**:
- Use docker-compose service names as hints (postgres, mysql, etc.)
- Check common env variable names (DATABASE_URL, DB_HOST, POSTGRES_HOST)
- Start conservative (high-confidence detections only)

---

#### P0-5: ProjectDetector Integration
**Status**: Not Started
**Effort**: Small (2 hours)
**Dependencies**: P0-2, P0-3, P0-4
**Spec Reference**: Proposal lines 947-959 • **Status Reference**: Section 2.1

**Description**:
Create the main `ProjectDetector` class that orchestrates all detection methods and returns a complete `ProjectContext`.

**Acceptance Criteria**:
- [ ] `ProjectDetector` class defined
- [ ] `detect(project_path: Path) -> ProjectContext` method implemented
- [ ] Calls all detection methods in sequence
- [ ] Returns populated `ProjectContext`
- [ ] Integration tests with realistic project structures
- [ ] Performance: < 100ms for typical project

**Technical Notes**:
- Detection order doesn't matter (all independent)
- Consider caching results (same project path = same result)
- Add timing/logging for debugging (optional)

---

### Phase 2: Template Metadata & Scoring (Week 1-2)

#### P0-6: Extend ServerTemplate Model
**Status**: Not Started
**Effort**: Medium (3 hours)
**Dependencies**: None
**Spec Reference**: Proposal lines 1007-1030 • **Status Reference**: Section 1.2

**Description**:
Extend the `ServerTemplate` Pydantic model to include recommendation metadata fields.

**Acceptance Criteria**:
- [ ] Add `best_for: List[str] = []` to `ServerTemplate`
- [ ] Add `keywords: List[str] = []` to `ServerTemplate`
- [ ] Add `recommendations: Optional[Dict[str, Any]] = None` to `ServerTemplate`
- [ ] All fields are optional (backward compatible)
- [ ] Pydantic validation works with and without new fields
- [ ] Unit tests for model validation

**Technical Notes**:
- Use Pydantic `Field()` with defaults for optional fields
- Add docstrings explaining each field's purpose
- Ensure existing templates load without modification

---

#### P0-7: Update Template YAML Files
**Status**: Not Started
**Effort**: Medium (3 hours)
**Dependencies**: P0-6
**Spec Reference**: Proposal lines 1084-1121 • **Status Reference**: Section 1.2

**Description**:
Add recommendation metadata to all 12 existing templates. This is the data foundation for the recommendation engine.

**Acceptance Criteria**:
- [ ] All 12 templates updated with `best_for`, `keywords`, `recommendations` fields
- [ ] postgres/docker: best_for includes "docker", "docker-compose", "development"
- [ ] postgres/local-development: best_for includes "local", "development"
- [ ] postgres/production: best_for includes "production", "cloud"
- [ ] Similar metadata for all other templates
- [ ] YAML syntax valid (pytest tests pass)
- [ ] Templates load successfully in TemplateManager

**Technical Notes**:
- Create a spreadsheet or checklist for all 12 templates
- Validate YAML syntax after each edit (run tests)
- Consider creating a template metadata validator (optional)

---

#### P0-8: Scoring Algorithm
**Status**: Not Started
**Effort**: Medium (5 hours)
**Dependencies**: P0-5, P0-7
**Spec Reference**: Proposal lines 972-1002 • **Status Reference**: Section 2.2

**Description**:
Implement the scoring algorithm that matches project context against template metadata and returns confidence scores with explanations.

**Acceptance Criteria**:
- [ ] `TemplateRecommender._score_template()` method implemented
- [ ] Scoring weights: docker_match=0.4, language_match=0.3, environment_match=0.2, service_match=0.5
- [ ] Returns tuple of (score: float, reasons: List[str])
- [ ] Scores capped at 1.0
- [ ] Explanations are clear and actionable
- [ ] Unit tests cover: perfect match, partial match, no match, edge cases

**Technical Notes**:
- Use additive scoring (sum individual matches)
- Make weights configurable (class attributes or constants)
- Generate human-readable reasons for each match
- Conservative scoring (prefer false negatives over false positives)

---

#### P0-9: TemplateRecommendation Data Model
**Status**: Not Started
**Effort**: Small (1 hour)
**Dependencies**: None
**Spec Reference**: Proposal lines 925-931 • **Status Reference**: Section 2.2

**Description**:
Create the `TemplateRecommendation` dataclass to represent a template recommendation with metadata.

**Acceptance Criteria**:
- [ ] `TemplateRecommendation` dataclass defined
- [ ] Fields: `template`, `confidence`, `reasons`, `match_details`
- [ ] Type hints for all fields
- [ ] Docstring explaining usage
- [ ] Can be sorted by confidence score

**Technical Notes**:
- Use `@dataclass` decorator
- Consider adding `__lt__` for sorting by confidence
- Keep simple (no complex logic in dataclass)

---

#### P0-10: TemplateRecommender Class
**Status**: Not Started
**Effort**: Large (6 hours)
**Dependencies**: P0-5, P0-8, P0-9
**Spec Reference**: Proposal lines 1000-1066 • **Status Reference**: Section 2.2

**Description**:
Implement the main `TemplateRecommender` class that orchestrates detection, scoring, and ranking.

**Acceptance Criteria**:
- [ ] `TemplateRecommender` class defined
- [ ] Constructor takes `template_manager: TemplateManager`
- [ ] `recommend(server_id, project_path) -> List[TemplateRecommendation]` method
- [ ] Detects project context
- [ ] Scores all templates for server
- [ ] Filters by minimum confidence threshold (0.3)
- [ ] Sorts by confidence descending
- [ ] Returns ranked list of recommendations
- [ ] Unit tests with mocked detector and template manager

**Technical Notes**:
- Inject `ProjectDetector` via constructor or create internally
- Make confidence threshold configurable (default 0.3)
- Handle empty results gracefully (no recommendations)
- Consider caching recommendations for same project

---

#### P0-11: Factory Functions
**Status**: Not Started
**Effort**: Small (2 hours)
**Dependencies**: P0-10
**Spec Reference**: Proposal lines 1069-1079 • **Status Reference**: Section 5.1

**Description**:
Create DIP-compliant factory functions for creating recommender instances in production and test scenarios.

**Acceptance Criteria**:
- [ ] `create_default_template_recommender()` function defined
- [ ] `create_test_template_recommender(template_manager)` function defined
- [ ] Default factory uses `create_default_template_manager()`
- [ ] Test factory accepts injected dependencies
- [ ] Unit tests verify factory functions work
- [ ] Integration tests use test factory

**Technical Notes**:
- Follow existing factory pattern (see `create_default_catalog()`)
- Import from appropriate modules (avoid circular imports)
- Document usage in docstrings

---

### Phase 3: CLI Integration & Testing (Week 2-3)

#### P1-12: Add --recommend Flag
**Status**: Not Started
**Effort**: Medium (4 hours)
**Dependencies**: P0-11
**Spec Reference**: Proposal lines 1126-1174 • **Status Reference**: Section 2.3

**Description**:
Add `--recommend` flag to the `mcpi add` command that enables automatic template recommendation.

**Acceptance Criteria**:
- [ ] `@click.option("--recommend", is_flag=True)` added to `add` command
- [ ] Flag triggers recommendation flow before template selection
- [ ] If recommendations exist, show top recommendation with reasons
- [ ] User can accept/decline recommendation
- [ ] Falls back to normal template selection if declined or no recommendations
- [ ] CLI tests verify flag behavior

**Technical Notes**:
- Add flag to existing `add` command (lines ~1000-1084 in cli.py)
- Use existing Rich console for output
- Preserve existing behavior when flag not used
- Handle edge cases (no templates, no recommendations)

---

#### P1-13: Rich Console Output
**Status**: Not Started
**Effort**: Medium (3 hours)
**Dependencies**: P1-12
**Spec Reference**: Proposal lines 1152-1169 • **Status Reference**: Section 2.3

**Description**:
Implement beautiful Rich-formatted output for displaying recommendations with confidence scores and explanations.

**Acceptance Criteria**:
- [ ] Recommendation header with template name and confidence percentage
- [ ] "Why this template?" section with bullet points
- [ ] Alternative templates listed (top 3)
- [ ] Color coding (cyan for recommended, dim for confidence)
- [ ] Confirmation prompt to use recommended template
- [ ] Matches example output from proposal

**Technical Notes**:
- Use existing Rich console instance from CLI
- Follow existing output style (see template list formatting)
- Consider using Rich Panel or Table for structure
- Test output in terminal (not just unit tests)

---

#### P1-14: Integrate with Template Selection Flow
**Status**: Not Started
**Effort**: Medium (3 hours)
**Dependencies**: P1-13
**Spec Reference**: CLI Integration • **Status Reference**: Section 2.3

**Description**:
Seamlessly integrate recommendations into the existing template selection workflow without breaking current behavior.

**Acceptance Criteria**:
- [ ] Recommendations shown BEFORE template list (if --recommend used)
- [ ] User can accept recommendation and skip template list
- [ ] User can decline recommendation and see full template list
- [ ] If no recommendations, show template list as normal
- [ ] --recommend flag and --template flag can coexist (--template wins)
- [ ] No breaking changes to existing behavior

**Technical Notes**:
- Refactor existing template selection code if needed
- Preserve all existing flags and behavior
- Add feature flag or env var for testing (optional)

---

#### P1-15: Unit Tests - Detection
**Status**: Not Started
**Effort**: Large (6 hours)
**Dependencies**: P0-5
**Spec Reference**: Section 6.1 • **Status Reference**: Section 6.1

**Description**:
Comprehensive unit tests for all project detection logic. Target: 95%+ coverage for discovery.py.

**Acceptance Criteria**:
- [ ] Test Docker detection (compose only, Dockerfile only, both, neither)
- [ ] Test language detection (each language, polyglot, none)
- [ ] Test database detection (docker-compose, env files, none)
- [ ] Test docker-compose YAML parsing (valid, invalid, corrupted)
- [ ] Test ProjectDetector integration (realistic projects)
- [ ] Test graceful failure (missing files, permission errors)
- [ ] Coverage: 95%+ for discovery.py

**Technical Notes**:
- Use pytest fixtures for test project structures
- Create tmp_path fixtures with realistic files
- Mock file I/O where appropriate (fast tests)
- Test both positive and negative cases

---

#### P1-16: Unit Tests - Scoring
**Status**: Not Started
**Effort**: Large (5 hours)
**Dependencies**: P0-10
**Spec Reference**: Section 6.1 • **Status Reference**: Section 6.1

**Description**:
Comprehensive unit tests for scoring algorithm and recommendation ranking. Ensure scoring is accurate and explanations are clear.

**Acceptance Criteria**:
- [ ] Test scoring with perfect match (score = 1.0)
- [ ] Test scoring with partial match (0.3 < score < 1.0)
- [ ] Test scoring with no match (score = 0.0, filtered out)
- [ ] Test docker service match bonus
- [ ] Test confidence threshold filtering (< 0.3 excluded)
- [ ] Test ranking by confidence (descending order)
- [ ] Test reason generation (explanations match scores)
- [ ] Coverage: 95%+ for recommender.py

**Technical Notes**:
- Mock template metadata for controlled testing
- Test edge cases (ties, empty reasons, etc.)
- Verify scoring weights are applied correctly
- Test threshold boundary conditions (exactly 0.3)

---

#### P1-17: Integration Tests - End-to-End
**Status**: Not Started
**Effort**: Large (6 hours)
**Dependencies**: P1-14
**Spec Reference**: Section 6.2 • **Status Reference**: Section 6.2

**Description**:
End-to-end integration tests that verify the entire recommendation flow from detection to CLI output.

**Acceptance Criteria**:
- [ ] Test: Docker Compose project recommends postgres/docker template
- [ ] Test: No Docker project recommends postgres/local-development
- [ ] Test: Node.js project gets appropriate language-specific recommendations
- [ ] Test: --recommend flag works in CLI (smoke test)
- [ ] Test: No recommendations falls back to template list
- [ ] Test: User accepts/declines recommendation (interactive)
- [ ] Test: All 12 templates can be recommended in appropriate contexts

**Technical Notes**:
- Use MCPTestHarness for realistic test environment
- Create fixtures for different project types
- Test with actual template files (not mocks)
- Use CLI runner for command-line tests

---

#### P2-18: Edge Case Testing
**Status**: Not Started
**Effort**: Medium (4 hours)
**Dependencies**: P1-17
**Spec Reference**: Section 7 • **Status Reference**: Section 7

**Description**:
Test edge cases and error conditions identified in the evaluation report.

**Acceptance Criteria**:
- [ ] Test: Docker detected but not actually used (conservative scoring)
- [ ] Test: Polyglot project (multiple languages detected)
- [ ] Test: Monorepo (detect from cwd, not root)
- [ ] Test: CI/CD docker-compose mistaken for app (only check root)
- [ ] Test: All templates score equally (tie-breaking by priority)
- [ ] Test: No templates pass threshold (show message)
- [ ] Test: Old templates without metadata (graceful handling)
- [ ] Test: Invalid metadata (validation catches at load time)

**Technical Notes**:
- Reference Section 7 of evaluation report for edge cases
- Create fixtures for each edge case scenario
- Verify mitigation strategies work as designed
- Document any new edge cases found

---

#### P2-19: Documentation
**Status**: Not Started
**Effort**: Medium (4 hours)
**Dependencies**: P1-17
**Spec Reference**: Implementation Week 3 • **Status Reference**: N/A

**Description**:
Update all documentation to reflect the new Template Discovery feature.

**Acceptance Criteria**:
- [ ] Update README.md with --recommend flag usage
- [ ] Update CLAUDE.md with new commands and examples
- [ ] Add "Template Discovery" section to docs
- [ ] Document how to add metadata to new templates
- [ ] Add examples of recommendation output
- [ ] Update CLI help text
- [ ] Create CHANGELOG entry for v0.6.0

**Technical Notes**:
- Include before/after examples
- Show recommendation output with screenshots or ASCII art
- Document metadata schema for template authors
- Link to proposal document for design rationale

---

#### P2-20: Performance Testing
**Status**: Not Started
**Effort**: Small (2 hours)
**Dependencies**: P1-17
**Spec Reference**: Section 2.1 • **Status Reference**: Section 2.1

**Description**:
Verify that project detection and recommendation runs efficiently with acceptable performance.

**Acceptance Criteria**:
- [ ] Detection completes in < 100ms for typical project
- [ ] Detection completes in < 500ms for large monorepo
- [ ] Recommendation scoring completes in < 50ms for 10 templates
- [ ] No performance regression in existing template selection
- [ ] Memory usage is acceptable (< 10MB additional)

**Technical Notes**:
- Use pytest-benchmark for performance tests
- Test with realistic project sizes
- Profile slow operations (docker-compose parsing)
- Consider caching if performance issues found

---

#### P3-21: Final Integration & Polish
**Status**: Not Started
**Effort**: Medium (4 hours)
**Dependencies**: P2-18, P2-19, P2-20
**Spec Reference**: Week 3 Summary • **Status Reference**: N/A

**Description**:
Final polish, bug fixes, and integration verification before release.

**Acceptance Criteria**:
- [ ] All tests passing (100% pass rate)
- [ ] Coverage >= 95% for new code
- [ ] No regressions in existing features
- [ ] CLI output looks professional (Rich formatting)
- [ ] Error messages are clear and helpful
- [ ] Code reviewed (self-review or peer review)
- [ ] All TODOs addressed or tracked

**Technical Notes**:
- Run full test suite multiple times
- Test in real projects (dogfooding)
- Check for any TODO/FIXME comments
- Verify git commit history is clean

---

## 3. Testing Strategy

### 3.1 Test Coverage Goals

**Target Coverage**: 95%+ for new code

**Breakdown**:
- `discovery.py`: 95%+ (unit tests for each detector)
- `recommender.py`: 95%+ (unit tests for scoring)
- CLI integration: 90%+ (integration tests)
- Template metadata: 100% (validation tests)

### 3.2 Test Categories

**Unit Tests** (15-20 tests):
- ProjectDetector: Docker, language, database detection
- Scoring algorithm: Various match scenarios
- TemplateRecommender: Ranking, filtering, threshold

**Integration Tests** (8-10 tests):
- Full recommendation flow (detect → score → rank)
- CLI with --recommend flag
- Template loading with metadata
- Real project structures

**Edge Case Tests** (8-10 tests):
- False positives/negatives
- Missing metadata (backward compatibility)
- Tie-breaking scenarios
- Error conditions

### 3.3 Test Data

**Fixtures Needed**:
- Sample docker-compose.yml files (valid, invalid, various services)
- Sample package.json, requirements.txt, go.mod files
- Minimal project structures (Node.js, Python, Go, polyglot)
- Templates with and without metadata

**Test Projects**:
- Docker Compose + Node.js + postgres
- Local Python project (no Docker)
- Go project with containers
- Polyglot project (Node.js + Python)

---

## 4. Dependencies & Prerequisites

### 4.1 Existing Infrastructure (All Available)

- [x] Template system fully functional (v0.5.0)
- [x] Pydantic models for validation
- [x] YAML parsing (PyYAML dependency)
- [x] File system utilities
- [x] Rich console output
- [x] CLI framework (Click)
- [x] Factory pattern established
- [x] DIP architecture in place
- [x] Test infrastructure solid

### 4.2 New Dependencies

**None Required** - All dependencies already installed:
- PyYAML: For parsing docker-compose.yml
- Pydantic: For models
- Rich: For console output
- Click: For CLI

---

## 5. Risk Mitigation

### 5.1 Technical Risks

| Risk | Mitigation |
|------|------------|
| False positive detection | Conservative scoring, always show all templates |
| Missing project types | Start with 5 detectors, document adding more |
| Performance issues | Cache detection results, fast file checks |
| Scoring algorithm poor quality | Extensive testing, tunable weights, user feedback |
| Template metadata incomplete | Validation in Pydantic models |

### 5.2 Implementation Risks

| Risk | Mitigation |
|------|------------|
| Scope creep | Stick to 5 detectors initially, incremental approach |
| Breaking existing templates | Backward compatible metadata, extensive tests |
| Integration issues | DIP architecture makes testing easy |

---

## 6. Success Metrics

### 6.1 Quantitative Goals

- **Adoption Rate**: 40%+ users enable --recommend flag
- **Success Rate**: 85%+ users accept top recommendation
- **Time Savings**: Template selection 75% faster (45 sec → 10 sec)
- **Coverage**: 95%+ test coverage on new code

### 6.2 Qualitative Goals

User feedback themes:
- "It knew my project uses Docker!"
- "The explanation helped me understand"
- "I trust MCPI's recommendations"

---

## 7. Ship Criteria for v0.6.0

### 7.1 Must Have

- [ ] All P0 tasks completed (detection, scoring, CLI integration)
- [ ] Test coverage >= 95% for new code
- [ ] All tests passing (100% pass rate)
- [ ] No regressions in existing features
- [ ] Documentation updated
- [ ] All 12 templates have metadata

### 7.2 Nice to Have (Defer to v0.6.1)

- [ ] Additional detectors (framework detection, cloud provider)
- [ ] Caching for performance optimization
- [ ] Machine learning scoring (v2.0)
- [ ] User feedback mechanism (thumbs up/down)

---

## 8. Timeline

### Week 1: Detection Infrastructure
- **Days 1-2**: P0-1 through P0-5 (ProjectDetector)
- **Day 3**: P0-6, P0-7 (Template metadata)
- **Day 4**: P0-8, P0-9 (Scoring algorithm)

**Deliverable**: Detection works programmatically, all templates have metadata

### Week 2: Recommendation Engine
- **Days 5-6**: P0-10, P0-11 (TemplateRecommender)
- **Days 7-8**: P1-15, P1-16 (Unit tests)
- **Day 9**: P1-17 (Integration tests)

**Deliverable**: Recommendations work end-to-end

### Week 3: CLI Integration & Polish
- **Days 10-11**: P1-12, P1-13, P1-14 (CLI integration)
- **Day 12**: P2-19 (Documentation)
- **Days 13-14**: P2-18, P2-20, P3-21 (Edge cases, performance, polish)

**Deliverable**: Ship to users as v0.6.0

---

## 9. Rollback Plan

### If Issues Arise

**Minimal Risk** - Feature is purely additive:
- Remove `--recommend` flag (users fall back to current behavior)
- Metadata fields are optional (templates work without them)
- No database migrations or file format changes
- Can disable feature with feature flag if needed

**Recovery Steps**:
1. Git revert CLI integration commits
2. Remove metadata from templates (optional, doesn't break anything)
3. Ship patch release with feature disabled

---

## 10. Post-Implementation

### 10.1 Monitoring

Track these metrics after v0.6.0 release:
- Usage of `--recommend` flag (telemetry or user surveys)
- Template selection patterns (which templates recommended/selected)
- User feedback (GitHub issues, Discord, social media)
- Performance issues (detection slowness reports)

### 10.2 Future Enhancements

Planned for v0.7.0+:
- Framework detection (Django, Express, React)
- Environment detection (production vs development)
- Cloud provider detection (AWS, GCP, Azure)
- Template Testing framework
- Workflow recommendations (combine with Template Workflows feature)

---

## 11. Implementation Notes

### 11.1 Coding Standards

- Follow existing MCPI code style
- Use type hints everywhere
- Add docstrings to all public methods
- Write tests before implementation (TDD where appropriate)
- DIP compliance (injectable dependencies)

### 11.2 Git Workflow

**Branch Strategy**:
- Create branch: `feature/template-discovery`
- Commit frequently with clear messages
- PR when P0 tasks complete (early review)

**Commit Message Format**:
```
feat(templates): add project detection for Docker and languages

- Implement ProjectDetector class with Docker and language detection
- Add ProjectContext dataclass to hold detected characteristics
- Include tests for docker-compose.yml parsing and language detection

Ref: PLAN-TEMPLATE-DISCOVERY-2025-11-17-080505.md
```

### 11.3 Code Review Checklist

Before PR submission:
- [ ] All tests passing locally
- [ ] Code formatted (black, ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated
- [ ] No TODOs or FIXMEs (or tracked in backlog)
- [ ] Self-review completed
- [ ] Examples work in real terminal

---

## Appendix A: File Structure

```
src/mcpi/templates/
├── __init__.py
├── models.py              # MODIFIED: Add metadata fields
├── template_manager.py    # EXISTING: No changes
├── prompt_handler.py      # EXISTING: No changes
├── discovery.py           # NEW: ProjectDetector, ProjectContext
└── recommender.py         # NEW: TemplateRecommender, TemplateRecommendation

data/templates/
├── postgres/
│   ├── docker.yaml        # MODIFIED: Add metadata
│   ├── local-development.yaml
│   └── production.yaml
├── github/
│   ├── personal-full-access.yaml
│   ├── read-only.yaml
│   └── public-repos.yaml
└── ... (all 12 templates updated)

tests/
├── test_project_detector.py       # NEW: Detection tests
├── test_template_recommender.py   # NEW: Recommendation tests
├── test_template_scoring.py       # NEW: Scoring tests
└── test_template_discovery_e2e.py # NEW: Integration tests

.agent_planning/
├── STATUS-TEMPLATE-DISCOVERY-EVALUATION-2025-11-17-080057.md  # Input
├── PLAN-TEMPLATE-DISCOVERY-2025-11-17-080505.md               # This file
├── SPRINT-TEMPLATE-DISCOVERY-2025-11-17-080505.md             # Sprint backlog
└── PLANNING-SUMMARY-TEMPLATE-DISCOVERY-2025-11-17-080505.md   # Executive summary
```

---

## Appendix B: Example Outputs

### Recommendation Output (Success Case)

```
$ mcpi add postgres --recommend

Analyzing your project...
  ✓ Detected Docker Compose in project root
  ✓ Found docker-compose.yml with postgres service
  ✓ Project type: Node.js application

🧠 Recommended Template: postgres/docker
   Confidence: 90%

Why this template?
  • Your project uses Docker Compose
  • The 'docker' template will connect to your existing postgres service
  • Matches docker-compose service: postgres

Alternative: postgres/local-development
  If you prefer postgres outside Docker

Continue with 'docker' template? [Y/n]:
```

### Recommendation Output (No Match)

```
$ mcpi add postgres --recommend

Analyzing your project...
  ✓ No Docker detected
  ✓ Project type: Python

No clear recommendation - showing all templates

Available templates for postgres:
  1. local-development - PostgreSQL on localhost (recommended for your setup)
  2. docker - PostgreSQL in Docker container
  3. production - Production-ready configuration

Which template? [1]:
```

---

**Generated by**: Implementation Planner Agent
**Date**: 2025-11-17 08:05:05
**Next Step**: Create sprint backlog (SPRINT-TEMPLATE-DISCOVERY-*.md)
