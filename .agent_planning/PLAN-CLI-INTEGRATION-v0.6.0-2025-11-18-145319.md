# CLI Integration Plan - Template Discovery v0.6.0

**Generated**: 2025-11-18-145319
**Source STATUS**: STATUS-2025-11-18-144000.md (Latest evaluation)
**Spec Version**: CLAUDE.md (Configuration Templates System v0.5.0 + Template Discovery Engine)
**Target Ship**: v0.6.0 (2-3 days)

---

## Executive Summary

**Context**: Template Discovery Engine library is 100% complete (19/19 tests passing, 91% coverage). The recommendation algorithms work perfectly. The ONLY remaining work is CLI integration to make this feature accessible to end users.

**Goal**: Add `--recommend` flag to `mcpi add` command that automatically detects project context and suggests the best templates with confidence scores and explanations.

**Scope**: 3 focused tasks over 2-3 days (10 hours estimated)
- P1-1: Add --recommend flag and wire up discovery engine
- P1-2: Implement Rich console display for recommendations
- P1-3: Add interactive template selection flow

**Ship Criteria**:
- All 3 CLI integration tasks complete
- Interactive flow tested end-to-end
- Manual verification passes (5 scenarios)
- Documentation updated (CLAUDE.md)
- v0.6.0 tagged and ready to ship

**Risk**: MINIMAL - Library code is production-ready, only CLI wiring required

---

## Gap Analysis

### Current State (From STATUS-TEMPLATE-DISCOVERY-IMPLEMENTATION-EVALUATION-2025-11-18.md)

**Library Code (100% Complete)**:
- ✅ ProjectDetector class (283 lines, 10 tests passing)
  - Docker detection (Dockerfile, docker-compose.yml, services parsing)
  - Language detection (Node.js, Python, Go, Rust, Java)
  - Database detection (postgres, mysql, redis, mongodb, sqlite)
  - Graceful error handling (corrupted YAML, invalid paths)
  - Performance <100ms
- ✅ TemplateRecommender class (241 lines, 6 tests passing)
  - Confidence-based scoring algorithm (0.0-1.0 scale)
  - Multi-factor scoring (docker, language, database, service matching)
  - Ranked recommendations with explanations
  - Minimum confidence threshold (0.3 default)
- ✅ ServerTemplate model extensions (3 new fields)
  - best_for: list[str] - Use case tags
  - keywords: list[str] - Search terms
  - recommendations: dict[str, Any] - Recommendation hints
- ✅ All 12 templates updated with metadata
- ✅ 19/19 functional tests passing (100%)
- ✅ 91% test coverage on new code
- ✅ Production-ready (no hacks, clean code, well-documented)

**CLI Code (0% Complete)**:
- ❌ No --recommend flag on `mcpi add` command
- ❌ No recommendation display UI
- ❌ No interactive selection flow
- ❌ No CLI integration tests

**Documentation (0% Complete)**:
- ❌ CLAUDE.md not updated with Template Discovery section
- ❌ No usage examples for --recommend flag

### Target State (v0.6.0 Shipped)

**CLI Integration**:
- ✅ `mcpi add postgres --recommend` detects project and shows recommendations
- ✅ Rich table displays templates with confidence scores and reasons
- ✅ Interactive selection: user picks template or skips to manual config
- ✅ Graceful fallback if no project detected or low confidence
- ✅ Works with existing --scope, --client, --catalog flags

**User Experience Flow**:
```bash
$ cd my-nodejs-app  # Has docker-compose.yml with postgres service
$ mcpi add postgres --recommend

Analyzing project context...
✓ Detected: Docker Compose project
✓ Found service: postgres
✓ Language: Node.js

Recommended templates for 'postgres':

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Template         ┃ Confidence ┃ Why this matches                       ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ docker           │ 95%        │ • Docker Compose detected              │
│                  │            │ • Service 'postgres' found             │
│                  │            │ • Best for: containerized development  │
│ local-development│ 65%        │ • Node.js project                      │
│                  │            │ • Best for: local development          │
│ production       │ 40%        │ • Database needed                      │
└──────────────────┴────────────┴────────────────────────────────────────┘

Select a template:
  1) docker (recommended)
  2) local-development
  3) production
  4) Skip recommendation, configure manually

Choice [1]:
```

**Documentation**:
- ✅ CLAUDE.md updated with Template Discovery section
- ✅ Usage examples for --recommend flag
- ✅ Architecture documentation (how detection works)

---

## Implementation Backlog

### P1-1: Add --recommend Flag and Wire Up Discovery Engine

**Status**: Not Started
**Effort**: 3-4 hours
**Dependencies**: None (library code complete)
**Priority**: CRITICAL (enables feature)

#### Description

Add `--recommend` boolean flag to `mcpi add` command and wire up ProjectDetector and TemplateRecommender to analyze project context and retrieve recommendations.

#### Acceptance Criteria

- [ ] `--recommend` flag added to `mcpi add` command signature
- [ ] When `--recommend=True`:
  - [ ] Detect project path (use current working directory)
  - [ ] Create ProjectDetector instance (use factory function if available, or direct instantiation)
  - [ ] Call `detector.detect(project_path)` to get ProjectContext
  - [ ] Create TemplateRecommender instance with TemplateManager
  - [ ] Call `recommender.recommend(server_id, project_path)` to get recommendations
  - [ ] Handle empty recommendations gracefully (show message, fall back to normal flow)
  - [ ] Pass recommendations to display logic (P1-2)
- [ ] Works with existing flags (--scope, --client, --catalog)
- [ ] Graceful error handling:
  - [ ] Invalid project path → show warning, continue with manual config
  - [ ] No templates available → show message, continue with manual config
  - [ ] Exception during detection → log warning, continue with manual config
- [ ] Manual verification: `mcpi add postgres --recommend` in test project works

#### Technical Notes

**Location**: `src/mcpi/cli.py`, `add()` command (line ~1157)

**Implementation approach**:
1. Add `--recommend` flag to @click.option decorators
2. Add early-exit check: if `recommend` flag:
   - Get current working directory as project_path
   - Import and instantiate ProjectDetector and TemplateRecommender
   - Call detect() and recommend()
   - If recommendations exist, display them (P1-2) and prompt for selection (P1-3)
   - If no recommendations, show message and continue to manual config
3. Keep existing template logic unchanged (--template still works)

**Error Handling**:
- Wrap detection in try/except to catch file I/O errors
- Wrap recommendation in try/except to catch model errors
- Log warnings but don't crash - always allow fallback to manual config

**Integration Points**:
- Uses existing `get_template_manager(ctx)` helper
- Uses existing server validation from catalog
- Reuses template application logic from existing --template flow

---

### P1-2: Implement Rich Display for Recommendations

**Status**: Not Started
**Effort**: 3-4 hours
**Dependencies**: P1-1 (needs recommendations data)
**Priority**: CRITICAL (user experience)

#### Description

Create beautiful Rich console output to display template recommendations with confidence scores, explanations, and clear visual hierarchy. Users should immediately understand why each template is recommended.

#### Acceptance Criteria

- [ ] Rich Table displays recommendations with columns:
  - [ ] Template name (cyan, bold for top recommendation)
  - [ ] Confidence score (green ≥80%, yellow 60-79%, white <60%)
  - [ ] Explanation bullets (bulleted list of reasons)
- [ ] Context summary displayed above table:
  - [ ] Docker status (if detected)
  - [ ] Language (if detected)
  - [ ] Databases (if detected)
  - [ ] Services found (if any)
- [ ] Visual indicators:
  - [ ] "✓" for detected features
  - [ ] "★" or "(recommended)" badge on top recommendation
  - [ ] Color coding for confidence levels
- [ ] Recommendations sorted by confidence (highest first)
- [ ] Max 3 recommendations shown (top N)
- [ ] Empty state message if no recommendations:
  - "No template recommendations available for this project context"
  - "Use --list-templates to see all available templates"
- [ ] Console output clean and professional (no debug clutter)

#### Technical Notes

**Location**: Create new function in `src/mcpi/cli.py` or separate module `src/mcpi/cli_display.py`

**Function signature**:
```python
def display_template_recommendations(
    context: ProjectContext,
    recommendations: list[TemplateRecommendation],
    server_id: str,
) -> None:
    """Display template recommendations in Rich table format."""
```

**Design Reference**: Use existing template list display (line ~1209-1222) as pattern

**Rich Components**:
- `Table` - Main recommendations display
- `Panel` - Optional: wrap context summary in panel
- `Text` - Styled text for context summary
- Color palette: cyan (names), green/yellow/white (confidence), dim (hints)

**Confidence Display**:
- Convert 0.0-1.0 to percentage (multiply by 100)
- Color thresholds: ≥0.8 green, ≥0.6 yellow, <0.6 white
- Format: "95%" or "85%" (no decimal places)

**Explanation Formatting**:
- Each reason on new line with bullet "•"
- Truncate long reasons to fit table width (~50 chars)
- Most important reasons first (already sorted by recommender)

---

### P1-3: Add Interactive Template Selection Flow

**Status**: Not Started
**Effort**: 3-4 hours
**Dependencies**: P1-2 (needs display)
**Priority**: CRITICAL (user interaction)

#### Description

Add interactive prompt for users to select from recommended templates or opt out to manual configuration. Seamlessly integrate with existing template application flow.

#### Acceptance Criteria

- [ ] After displaying recommendations, show numbered selection prompt:
  - [ ] Options 1-N: Each recommended template (by name)
  - [ ] Option N+1: "Skip recommendation, configure manually"
  - [ ] Default: Option 1 (top recommendation)
- [ ] User input validation:
  - [ ] Accept numeric choice (1-N+1)
  - [ ] Accept empty (use default)
  - [ ] Reject invalid input (show error, re-prompt)
- [ ] Selected template flow:
  - [ ] Load selected template via TemplateManager
  - [ ] Call existing prompt collection logic (collect_template_values)
  - [ ] Apply template and add server (reuse existing --template flow)
  - [ ] Respect --scope flag if provided, else use template's default scope
- [ ] Manual config flow:
  - [ ] If user selects "Skip" option, proceed with standard add flow (no template)
  - [ ] Add server with default configuration
- [ ] Edge cases:
  - [ ] Only 1 recommendation → still show prompt (allow skip)
  - [ ] 0 recommendations → skip prompt, go straight to manual config
  - [ ] User presses Ctrl+C → graceful exit (no server added)

#### Technical Notes

**Location**: `src/mcpi/cli.py`, in `add()` command after display logic

**Prompt Library**: Use Rich's `Prompt.ask()` or Python's built-in `input()`
- Rich Prompt preferred for consistency with existing UI
- Support default value (top recommendation)
- Support numeric choices with validation

**Integration with Existing Flow**:
```python
# After P1-2 display
choice = Prompt.ask(
    "Select a template",
    choices=["1", "2", "3", "4"],  # Dynamic based on recommendations
    default="1"
)

if choice in ["1", "2", "3"]:  # Selected a recommendation
    # Map choice to template object
    template_obj = recommendations[int(choice) - 1].template

    # REUSE EXISTING LOGIC from --template flow (line ~1241-1256)
    user_values = collect_template_values(template_obj)
    config = template_manager.apply_template(template_obj, user_values)
    scope = scope or template_obj.scope
    # ... rest of template flow
else:  # choice == "4" (skip)
    # CONTINUE to manual config (existing flow after line ~1300)
```

**User Experience Details**:
- Show "(recommended)" after option 1
- Show template descriptions inline or in table
- Clear indication that skip is non-destructive (can run command again)

---

## Testing Strategy

### Manual Verification Scenarios

**Scenario 1: Docker Compose Project with Postgres**
```bash
# Setup: Create test project
mkdir test-docker-app
cd test-docker-app
cat > docker-compose.yml <<EOF
services:
  postgres:
    image: postgres:15
EOF

# Test command
mcpi add postgres --recommend

# Expected:
# - Detects Docker Compose
# - Detects postgres service
# - Recommends "docker" template with high confidence (>90%)
# - Shows interactive selection
# - Applies template successfully
```

**Scenario 2: Node.js Project (No Docker)**
```bash
# Setup
mkdir test-node-app
cd test-node-app
echo '{"name": "test"}' > package.json

# Test command
mcpi add postgres --recommend

# Expected:
# - Detects Node.js
# - Recommends "local-development" template (no Docker penalty)
# - Shows interactive selection
# - Applies template successfully
```

**Scenario 3: Empty Project**
```bash
# Setup
mkdir test-empty
cd test-empty

# Test command
mcpi add postgres --recommend

# Expected:
# - No strong recommendations (all low confidence)
# - Shows message: "No template recommendations..."
# - Falls back to manual config OR shows all templates with equal weight
```

**Scenario 4: Server with No Templates**
```bash
# Test command (use server that has no templates)
mcpi add some-server-without-templates --recommend

# Expected:
# - Shows message: "No templates available for 'some-server-without-templates'"
# - Falls back to normal add flow (manual config)
```

**Scenario 5: User Skips Recommendation**
```bash
# Setup: Docker project
cd test-docker-app

# Test command + interaction
mcpi add postgres --recommend
# Select option: 4 (Skip recommendation, configure manually)

# Expected:
# - Proceeds to standard add flow
# - Prompts for manual configuration (command, args, env)
# - Adds server successfully
```

### Automated Testing (Optional, Time Permitting)

**Test File**: `tests/test_cli_recommend_integration.py`

Focus on:
- `--recommend` flag parsing
- ProjectDetector integration (mock file system)
- TemplateRecommender integration (mock templates)
- Display function called with correct args
- Selection prompt handling (mock user input)

**Priority**: MEDIUM (manual testing sufficient for v0.6.0 ship)

---

## Documentation Updates

### CLAUDE.md Updates

**Section**: Configuration Templates System (v0.5.0+)

**Add subsection**: Template Discovery Engine (v0.6.0+)

**Content**:
```markdown
#### Template Discovery and Recommendations (v0.6.0+)

MCPI includes an intelligent template discovery system that analyzes your project context and recommends the best configuration templates automatically.

**Components (`mcpi.templates/`)**:

- `discovery.py`: Project detection engine
  - `ProjectDetector`: Analyzes project directory for characteristics
  - `ProjectContext`: Detected features (Docker, language, databases)
  - Detection methods: Docker, Docker Compose, languages, databases
- `recommender.py`: Template recommendation engine
  - `TemplateRecommender`: Scores templates against project context
  - `TemplateRecommendation`: Recommendation with confidence and explanation
  - Scoring algorithm: Multi-factor with confidence levels

**How Detection Works**:
1. Scans project directory for indicator files:
   - `Dockerfile`, `docker-compose.yml` → Docker detection
   - `package.json` → Node.js
   - `requirements.txt`, `pyproject.toml` → Python
   - `go.mod` → Go
   - Database services in docker-compose → Database detection
2. Builds ProjectContext with detected features
3. Scores each template against context (0.0-1.0 confidence)
4. Returns top 3 recommendations with explanations

**Scoring Algorithm**:
- Baseline: 0.35 for all templates
- Docker match: +0.4 (if project has Docker and template supports it)
- Service match: +0.5 (if docker-compose service matches server ID)
- Language match: +0.3 (if project language matches template metadata)
- Database match: +0.3 (if detected database matches template)
- Mismatch penalty: -0.25 (if Docker project but template is local-only)

**CLI Usage**:
```bash
# Analyze project and recommend templates
mcpi add postgres --recommend

# Works with other flags
mcpi add postgres --recommend --scope user-global
mcpi add postgres --recommend --catalog local

# Interactive flow:
# 1. Shows project context (Docker, language, databases)
# 2. Displays ranked template recommendations with confidence
# 3. Prompts user to select template or skip
# 4. Applies selected template with interactive prompts
```

**Template Metadata for Discovery**:
Templates include metadata to improve recommendations:
- `best_for`: Use case tags (e.g., "docker", "local-development")
- `keywords`: Search terms for matching
- `recommendations.languages`: Supported languages
- `recommendations.requires_docker`: Docker requirement flag

**Example metadata** (postgres/docker.yaml):
```yaml
name: docker
description: "PostgreSQL in Docker Compose"
best_for:
  - docker
  - docker-compose
  - containerized-development
  - team-environments
keywords:
  - docker
  - compose
  - container
recommendations:
  languages: ["javascript", "typescript", "python", "go", "java"]
  requires_docker: true
```

**Fallback Behavior**:
- If no project detected: Shows message, falls back to manual config
- If low confidence (<30%): Shows message, lists all templates
- If error during detection: Logs warning, continues with manual config
- Always allows user to skip recommendations and configure manually
```

---

## Ship Criteria

### Definition of Done for v0.6.0

**Functional Requirements**:
- [x] Template Discovery Engine library complete (19/19 tests passing)
- [ ] CLI integration complete (3 tasks: P1-1, P1-2, P1-3)
- [ ] `--recommend` flag functional and tested
- [ ] Interactive selection flow working end-to-end
- [ ] Rich display rendering correctly

**Testing Requirements**:
- [x] All library tests passing (19/19)
- [ ] All 5 manual verification scenarios pass
- [ ] No regressions in existing CLI tests
- [ ] Overall test pass rate maintained (≥92%)

**Documentation Requirements**:
- [ ] CLAUDE.md updated with Template Discovery section
- [ ] Usage examples documented
- [ ] Architecture explanation included

**Quality Requirements**:
- [ ] No crashes or unhandled exceptions
- [ ] Graceful error handling throughout
- [ ] Clean console output (no debug clutter)
- [ ] Professional user experience

**Ship Checklist**:
1. [ ] All code complete and working
2. [ ] All manual tests pass
3. [ ] Documentation updated
4. [ ] No known bugs
5. [ ] Clean git state (no uncommitted changes)
6. [ ] Ready to tag v0.6.0

---

## Timeline

**Target**: 2-3 days (10 hours total)

**Day 1** (4 hours):
- Morning: P1-1 - Add --recommend flag and wire up detection (3h)
- Afternoon: Manual test P1-1, fix issues (1h)

**Day 2** (4 hours):
- Morning: P1-2 - Implement Rich display (3h)
- Afternoon: Manual test display, refine formatting (1h)

**Day 3** (3 hours):
- Morning: P1-3 - Add interactive selection (2h)
- Afternoon: E2E testing all 5 scenarios, documentation (1h)

**Buffer**: +1 day if issues found during testing

**Ship Date**: 2025-11-20 or 2025-11-21 (by end of week)

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Rich display formatting issues | MEDIUM | LOW | Test in real terminal, iterate on layout |
| User input validation edge cases | LOW | MEDIUM | Comprehensive validation, clear error messages |
| Integration with existing template flow | LOW | MEDIUM | Reuse existing code, minimal new logic |
| Performance degradation | LOW | LOW | Detection already <100ms, minimal CLI overhead |
| Regressions in existing CLI | LOW | HIGH | Run full test suite before ship |

**Overall Risk**: LOW (library code proven, only CLI wiring)

---

## References

### Source Documents

- **Implementation STATUS**: STATUS-TEMPLATE-DISCOVERY-IMPLEMENTATION-EVALUATION-2025-11-18.md
- **Project Architecture**: CLAUDE.md (lines 219-382)
- **Existing CLI Code**: src/mcpi/cli.py (add command, lines 1157-1300)

### Related Files

**Library Code** (Complete):
- `src/mcpi/templates/discovery.py` (283 lines)
- `src/mcpi/templates/recommender.py` (241 lines)
- `src/mcpi/templates/models.py` (ServerTemplate extensions)

**CLI Code** (To Modify):
- `src/mcpi/cli.py` (add command, ~150 lines to add)

**Tests** (Complete):
- `tests/test_template_discovery_functional.py` (19 tests)

**Templates** (Complete):
- `data/templates/postgres/*.yaml` (3 templates with metadata)
- `data/templates/github/*.yaml` (3 templates with metadata)
- `data/templates/filesystem/*.yaml` (3 templates with metadata)
- `data/templates/slack/*.yaml` (2 templates with metadata)
- `data/templates/brave-search/*.yaml` (1 template with metadata)

---

**Plan Generated**: 2025-11-18 14:53:19
**Status**: Ready for Implementation
**Next Action**: Start P1-1 (Add --recommend flag)
**Estimated Completion**: 2025-11-20 or 2025-11-21
**Ship Target**: v0.6.0 by end of week
