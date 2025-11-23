# Configuration Templates Sprint Backlog - v0.5.0

**Generated**: 2025-11-17 06:19:46
**Source Plan**: PLAN-CONFIG-TEMPLATES-v0.5.0-2025-11-17-061946.md
**Sprint Duration**: 5 days (1 week)
**Sprint Goal**: Ship Configuration Templates feature for 5+ popular servers

---

## Sprint Overview

### Sprint Goal

Enable users to install MCP servers with pre-tested configurations using `mcpi add <server> --template <name>`, reducing setup time from 15-30 minutes to 2-3 minutes.

### Success Metrics

**Functional**:
- [ ] 5+ servers with 2-3 templates each (10+ total templates)
- [ ] `--template` flag working end-to-end
- [ ] Interactive prompts with validation
- [ ] All templates manually tested and working

**Quality**:
- [ ] 100% code coverage for template module
- [ ] Zero test regressions
- [ ] All tests passing
- [ ] Documentation complete

**User Experience**:
- [ ] Setup time reduced from 15+ min to 2-3 min
- [ ] Clear error messages
- [ ] Beautiful Rich UI for prompts

---

## Day 1: Infrastructure (8-12 hours)

### Morning: Template Models (4-6h)

**TMPL-001: Template Data Models**
- **Priority**: P0 (CRITICAL)
- **Effort**: 4-6 hours
- **Assignee**: Implementation Agent

**Tasks**:
1. Create `src/mcpi/templates/__init__.py`
2. Create `src/mcpi/templates/models.py`:
   - [ ] Define `PromptDefinition` Pydantic model
   - [ ] Define `ServerTemplate` Pydantic model
   - [ ] Add field validators for types (string, secret, path, port, url)
   - [ ] Add regex validation support
   - [ ] Add default value support
   - [ ] Add required/optional distinction

**Acceptance Criteria**:
```python
# Must validate successfully
prompt = PromptDefinition(
    name="DATABASE_URL",
    description="Database connection string",
    type="url",
    required=True,
    validate="^postgres://.*"
)

template = ServerTemplate(
    name="production",
    description="Production setup",
    server_id="postgres",
    scope="user-global",
    priority="high",
    config={"command": "npx", "args": [...], "env": {...}},
    prompts=[prompt],
    notes="Setup instructions"
)
```

**Definition of Done**:
- [ ] Models defined in `models.py`
- [ ] All type validators working
- [ ] Pydantic validation passes
- [ ] Code formatted (black)
- [ ] Linting passes (ruff)

---

### Afternoon: Template Manager (4-6h)

**TMPL-002: Template Manager Implementation**
- **Priority**: P0 (CRITICAL)
- **Effort**: 6-8 hours
- **Assignee**: Implementation Agent
- **Dependencies**: TMPL-001

**Tasks**:
1. Create `src/mcpi/templates/template_manager.py`:
   - [ ] `TemplateManager.__init__(template_dir)`
   - [ ] `load_templates()` - load from YAML files
   - [ ] `list_templates(server_id)` - return sorted list
   - [ ] `get_template(server_id, name)` - get specific template
   - [ ] `apply_template(template, user_values)` - merge config
   - [ ] Factory functions (DIP compliance)

**Acceptance Criteria**:
```python
# Must work
manager = create_default_template_manager()
manager.load_templates()

templates = manager.list_templates("postgres")
assert len(templates) >= 2

template = manager.get_template("postgres", "production")
assert template is not None

config = manager.apply_template(template, {"POSTGRES_DB": "mydb"})
assert config.env["POSTGRES_DB"] == "mydb"
```

**Definition of Done**:
- [ ] TemplateManager class implemented
- [ ] All methods working
- [ ] Lazy loading implemented
- [ ] Factory functions defined
- [ ] Error handling graceful
- [ ] Code formatted and linted

---

### Evening: Unit Tests (4-6h)

**TMPL-003: Template Infrastructure Tests**
- **Priority**: P0 (CRITICAL)
- **Effort**: 4-6 hours
- **Assignee**: Implementation Agent
- **Dependencies**: TMPL-001, TMPL-002

**Tasks**:
1. Create `tests/test_templates_models.py`:
   - [ ] Test PromptDefinition validation
   - [ ] Test ServerTemplate validation
   - [ ] Test type validators (string, secret, path, port, url)
   - [ ] Test regex validation
   - [ ] Test invalid models rejected

2. Create `tests/test_template_manager.py`:
   - [ ] Test template loading from YAML
   - [ ] Test list_templates sorting
   - [ ] Test get_template retrieval
   - [ ] Test apply_template merging
   - [ ] Test missing template directory
   - [ ] Test invalid YAML files
   - [ ] Test factory functions

3. Create `tests/fixtures/templates/`:
   - [ ] Test template files for postgres, github
   - [ ] Invalid template for error testing

**Acceptance Criteria**:
- [ ] 100% code coverage for `models.py`
- [ ] 100% code coverage for `template_manager.py`
- [ ] All tests pass
- [ ] Tests run fast (< 1s)

**Definition of Done**:
- [ ] Test files created
- [ ] All tests passing
- [ ] Coverage report shows 100%
- [ ] Test fixtures committed

---

## Day 2: CLI Integration (8-12 hours)

### Morning: CLI Flag (4-6h)

**TMPL-004: Add --template Flag to CLI**
- **Priority**: P0 (CRITICAL)
- **Effort**: 4-6 hours
- **Assignee**: Implementation Agent
- **Dependencies**: TMPL-002

**Tasks**:
1. Modify `src/mcpi/cli.py` (add command):
   - [ ] Add `--template` option
   - [ ] Add `--list-templates` flag
   - [ ] Lazy-load TemplateManager (CLI startup performance)
   - [ ] Show templates in Rich table format
   - [ ] Error if template doesn't exist
   - [ ] Error if both `--template` and `--env` provided
   - [ ] Update help text
   - [ ] Add tab completion for template names

**Acceptance Criteria**:
```bash
# Must work
$ mcpi add postgres --list-templates
# Shows Rich table with template names and descriptions

$ mcpi add postgres --template production
# Triggers interactive prompts

$ mcpi add postgres --template invalid
# Error: Template 'invalid' not found for server 'postgres'

$ mcpi add postgres --template prod --env KEY=val
# Error: Cannot use both --template and --env
```

**Definition of Done**:
- [ ] CLI accepts `--template` flag
- [ ] `--list-templates` shows available templates
- [ ] Error handling working
- [ ] Help text updated
- [ ] Code formatted and linted

---

### Afternoon: Prompt System (6-8h)

**TMPL-005: Interactive Prompt System**
- **Priority**: P0 (CRITICAL)
- **Effort**: 6-8 hours
- **Assignee**: Implementation Agent
- **Dependencies**: TMPL-004

**Tasks**:
1. Create `src/mcpi/templates/prompt_handler.py`:
   - [ ] `prompt_for_value(prompt_def)` - single prompt
   - [ ] `prompt_for_template(template)` - all prompts
   - [ ] Validation logic (regex, type checking)
   - [ ] Secret masking (type="secret")
   - [ ] Default value handling
   - [ ] Error recovery (re-prompt on invalid)
   - [ ] Ctrl+C handling (graceful abort)

2. Integrate with `src/mcpi/cli.py`:
   - [ ] Call prompt_handler when `--template` used
   - [ ] Display template notes before prompts
   - [ ] Merge prompt results with template config
   - [ ] Pass complete config to MCPManager

**Acceptance Criteria**:
```python
# Validation must work
prompt = PromptDefinition(
    name="PORT",
    type="port",
    validate="^[1-9][0-9]{3,4}$"
)

# Must reject "abc", "0", "70000"
# Must accept "5432", "8080", "3000"
```

**UI Requirements**:
- Show template description/notes first
- Show parameter description in prompt
- Show default value: `Name [default]:`
- Mask secrets: `Password: ••••••••`
- Re-prompt on validation error with example

**Definition of Done**:
- [ ] Prompt handler implemented
- [ ] All prompt types working (string, secret, path, port, url)
- [ ] Validation working
- [ ] Error messages clear
- [ ] Beautiful Rich UI
- [ ] Code formatted and linted

---

### Evening: Integration Tests (6-8h)

**TMPL-006: CLI Integration Tests**
- **Priority**: P0 (CRITICAL)
- **Effort**: 6-8 hours
- **Assignee**: Implementation Agent
- **Dependencies**: TMPL-004, TMPL-005

**Tasks**:
1. Create `tests/test_cli_templates.py`:
   - [ ] Test `mcpi add --template` with mock prompts
   - [ ] Test `--list-templates` output
   - [ ] Test invalid template error
   - [ ] Test missing server error
   - [ ] Test `--template` + `--env` conflict error
   - [ ] Test secret masking
   - [ ] Test validation failures
   - [ ] Test Ctrl+C abort
   - [ ] Test config file written correctly
   - [ ] Test end-to-end workflow

**Mocking Strategy**:
```python
# Mock Rich prompts for predictable input
with patch('rich.prompt.Prompt.ask') as mock_ask:
    mock_ask.side_effect = ["mydb", "postgres", "secret123"]
    # Test template application
```

**Acceptance Criteria**:
- [ ] All CLI template paths tested
- [ ] Error cases covered
- [ ] Integration with MCPManager verified
- [ ] Config file validation
- [ ] Tests run fast (< 2s)

**Definition of Done**:
- [ ] Test file created
- [ ] All tests passing
- [ ] No test regressions
- [ ] Coverage report updated

---

## Day 3: Research & Content Start (10-14 hours)

### Morning: Research Postgres & GitHub (4-6h)

**TMPL-007: Research Server Parameters (Part 1)**
- **Priority**: P1 (HIGH)
- **Effort**: 4-6 hours
- **Assignee**: Research Agent

**Tasks - PostgreSQL Server**:
1. Read official documentation
2. Test server manually:
   - [ ] Local PostgreSQL installation
   - [ ] Docker PostgreSQL container
   - [ ] Cloud PostgreSQL (AWS RDS, etc.)
3. Document parameters:
   - [ ] POSTGRES_HOST (required? default?)
   - [ ] POSTGRES_PORT (default: 5432)
   - [ ] POSTGRES_DB (required)
   - [ ] POSTGRES_USER (default: postgres)
   - [ ] POSTGRES_PASSWORD (required, secret)
   - [ ] POSTGRES_SSL_MODE (optional)
4. Identify scenarios:
   - [ ] Production (TLS, remote host)
   - [ ] Local Docker (localhost, standard ports)
   - [ ] Development (local, no TLS)

**Tasks - GitHub Server**:
1. Read GitHub MCP server docs
2. Test server manually:
   - [ ] Personal access token (full access)
   - [ ] Read-only token
   - [ ] Public repos only
3. Document parameters:
   - [ ] GITHUB_TOKEN (required, secret)
   - [ ] GITHUB_API_URL (optional, default: https://api.github.com)
4. Identify scenarios:
   - [ ] Full access (private + public repos)
   - [ ] Read-only (fetch only)
   - [ ] Public repos (no token needed)

**Deliverable**: `data/templates/TEMPLATE_SPECS.md` (partial)

**Definition of Done**:
- [ ] Both servers tested manually
- [ ] All parameters documented
- [ ] Scenarios identified
- [ ] Spec document started

---

### Afternoon: Research Remaining Servers (4-6h)

**TMPL-007: Research Server Parameters (Part 2)**
- **Priority**: P1 (HIGH)
- **Effort**: 4-6 hours
- **Assignee**: Research Agent

**Tasks - Filesystem Server**:
1. Read documentation
2. Test with different paths
3. Document parameters:
   - [ ] ALLOWED_PATHS (required, path list)
   - [ ] READ_ONLY (optional, boolean)
4. Identify scenarios:
   - [ ] Project files (current project only)
   - [ ] User documents (~/Documents)
   - [ ] Read-only (prevent writes)

**Tasks - Slack Server**:
1. Read documentation
2. Test with bot and user tokens
3. Document parameters:
   - [ ] SLACK_BOT_TOKEN (secret)
   - [ ] SLACK_USER_TOKEN (secret)
4. Identify scenarios:
   - [ ] Bot token (automated actions)
   - [ ] User token (user context)

**Tasks - Brave Search Server**:
1. Read documentation
2. Test with API key
3. Document parameters:
   - [ ] BRAVE_API_KEY (required, secret)
4. Identify scenarios:
   - [ ] Free tier (rate limited)
   - [ ] API key (full access)

**Deliverable**: `data/templates/TEMPLATE_SPECS.md` (complete)

**Definition of Done**:
- [ ] All 5 servers researched
- [ ] Parameters documented
- [ ] Scenarios identified
- [ ] Spec document complete

---

### Evening: Start Template Creation (4-6h)

**TMPL-008: Create Template Files (Part 1)**
- **Priority**: P1 (HIGH)
- **Effort**: 4-6 hours
- **Assignee**: Content Author
- **Dependencies**: TMPL-007

**Tasks**:
1. Create directory structure:
   ```
   data/templates/
   ├── postgres/
   ├── github/
   ├── filesystem/
   ├── slack/
   └── brave-search/
   ```

2. Create PostgreSQL templates:
   - [ ] `postgres/production.yaml`
   - [ ] `postgres/local-docker.yaml`
   - [ ] `postgres/development.yaml`

3. Create GitHub templates:
   - [ ] `github/full-access.yaml`
   - [ ] `github/read-only.yaml`
   - [ ] `github/public-repos.yaml`

**Template Checklist** (each file):
- [ ] YAML syntax valid
- [ ] All required fields present
- [ ] Prompts have clear descriptions
- [ ] Defaults are sensible
- [ ] Validation regex correct
- [ ] Notes include setup instructions

**Definition of Done**:
- [ ] 6 template files created
- [ ] All files parse successfully
- [ ] Templates follow schema
- [ ] Git committed

---

## Day 4: Content Completion (10-14 hours)

### Morning: Finish Template Creation (4-6h)

**TMPL-008: Create Template Files (Part 2)**
- **Priority**: P1 (HIGH)
- **Effort**: 4-6 hours
- **Assignee**: Content Author

**Tasks**:
1. Create Filesystem templates:
   - [ ] `filesystem/project-files.yaml`
   - [ ] `filesystem/user-documents.yaml`
   - [ ] `filesystem/read-only.yaml`

2. Create Slack templates:
   - [ ] `slack/bot-token.yaml`
   - [ ] `slack/user-token.yaml`

3. Create Brave Search templates:
   - [ ] `brave-search/free-tier.yaml`
   - [ ] `brave-search/api-key.yaml`

**Total Templates**: 13 files across 5 servers

**Definition of Done**:
- [ ] All 13 template files created
- [ ] All YAML valid
- [ ] All templates tested with validator
- [ ] Git committed

---

### Afternoon: Template Validation (4-6h)

**TMPL-009: Template Validation Tests**
- **Priority**: P1 (HIGH)
- **Effort**: 4-6 hours
- **Assignee**: Implementation Agent
- **Dependencies**: TMPL-008

**Tasks**:
1. Create `tests/test_template_validation.py`:
   - [ ] Test that loads all template files
   - [ ] Verify Pydantic validation passes
   - [ ] Verify no duplicate names per server
   - [ ] Verify all prompts have valid types
   - [ ] Verify all regex patterns compile
   - [ ] Test each template individually

2. Create validation report script:
   ```python
   # scripts/validate_templates.py
   # Standalone script to validate all templates
   # Useful for CI/CD and manual verification
   ```

**Acceptance Criteria**:
```python
# Must pass
def test_all_templates_valid():
    manager = create_default_template_manager()
    manager.load_templates()

    for server_id in ["postgres", "github", "filesystem", "slack", "brave-search"]:
        templates = manager.list_templates(server_id)
        assert len(templates) >= 2  # At least 2 templates per server

        for template in templates:
            # Must parse and validate
            assert template.name
            assert template.description
            assert template.server_id == server_id
```

**Definition of Done**:
- [ ] Validation test created
- [ ] All templates pass validation
- [ ] Validation script working
- [ ] CI integration (optional)

---

### Evening: Manual Testing (4-6h)

**TMPL-011: Manual Testing (Part 1)**
- **Priority**: P0 (CRITICAL)
- **Effort**: 4-6 hours
- **Assignee**: QA / Implementation Agent

**Tasks**:
1. Setup test environment:
   - [ ] Fresh MCPI installation
   - [ ] Clean `.mcp.json` files
   - [ ] Claude Code available for testing

2. Test each template:
   - [ ] postgres/production
   - [ ] postgres/local-docker
   - [ ] postgres/development
   - [ ] github/full-access
   - [ ] github/read-only
   - [ ] github/public-repos
   - [ ] filesystem/project-files
   - [ ] filesystem/user-documents
   - [ ] filesystem/read-only
   - [ ] slack/bot-token
   - [ ] slack/user-token
   - [ ] brave-search/free-tier
   - [ ] brave-search/api-key

3. For each template:
   - [ ] Run `mcpi add <server> --list-templates`
   - [ ] Run `mcpi add <server> --template <name>`
   - [ ] Verify prompts appear correctly
   - [ ] Verify validation works
   - [ ] Verify secret masking works
   - [ ] Verify config written to file
   - [ ] Verify server works in Claude Code

4. Test error cases:
   - [ ] Invalid template name
   - [ ] Invalid input (validation)
   - [ ] Ctrl+C abort
   - [ ] `--template` + `--env` conflict

**Deliverable**: Manual test report with screenshots

**Definition of Done**:
- [ ] All 13 templates tested manually
- [ ] All templates work correctly
- [ ] All error cases handled
- [ ] Test report documented
- [ ] Bugs filed (if any)

---

## Day 5: Documentation & Release (10-14 hours)

### Morning: Documentation (4-6h)

**TMPL-010: User Documentation**
- **Priority**: P1 (HIGH)
- **Effort**: 4-6 hours
- **Assignee**: Documentation Writer
- **Dependencies**: All above

**Tasks**:
1. Update `README.md`:
   - [ ] Add "Configuration Templates" section
   - [ ] Add examples for each server
   - [ ] Add `--list-templates` example
   - [ ] Update quick start guide
   - [ ] Add FAQ section

2. Update `CLAUDE.md`:
   - [ ] Add "Template System" to Project Architecture
   - [ ] Document TemplateManager architecture
   - [ ] Add template testing patterns
   - [ ] Add DIP compliance notes

3. Update `CHANGELOG.md`:
   - [ ] Create v0.5.0 section
   - [ ] List new features (templates)
   - [ ] List new CLI flags
   - [ ] Add template examples
   - [ ] Migration guide (none needed - additive)

4. Create `docs/TEMPLATE_AUTHORING_GUIDE.md`:
   - [ ] Template file format
   - [ ] Prompt types and validation
   - [ ] Testing templates
   - [ ] Contributing templates

**Documentation Quality Checklist**:
- [ ] All examples tested manually
- [ ] Code blocks syntax-highlighted
- [ ] Screenshots included (optional)
- [ ] Links working
- [ ] Clear, concise writing

**Definition of Done**:
- [ ] All docs updated
- [ ] Examples accurate
- [ ] Authoring guide complete
- [ ] Git committed

---

### Afternoon: Final Testing (4-6h)

**TMPL-011: Manual Testing (Part 2)**
- **Priority**: P0 (CRITICAL)
- **Effort**: 4-6 hours
- **Assignee**: QA / Implementation Agent

**Tasks**:
1. Regression testing:
   - [ ] Run full test suite (pytest)
   - [ ] Verify zero regressions
   - [ ] Check code coverage
   - [ ] Run black, ruff, mypy

2. Integration testing:
   - [ ] Test on clean system (VM or Docker)
   - [ ] Test with Claude Code
   - [ ] Test all documented examples
   - [ ] Test error cases

3. Performance testing:
   - [ ] Measure CLI startup time (should be unchanged)
   - [ ] Measure template loading time (< 100ms)
   - [ ] Verify no impact on `mcpi add` without `--template`

4. Documentation review:
   - [ ] Verify all examples work
   - [ ] Check for typos
   - [ ] Verify links
   - [ ] Test code blocks

**Definition of Done**:
- [ ] All tests passing
- [ ] Zero regressions
- [ ] Performance acceptable
- [ ] Documentation accurate

---

### Evening: Bug Fixes & Release (4-6h)

**TMPL-011: Bug Fixes & Release Prep**
- **Priority**: P0 (CRITICAL)
- **Effort**: 4-6 hours
- **Assignee**: Implementation Agent

**Tasks**:
1. Fix bugs found in testing:
   - [ ] Prioritize critical bugs
   - [ ] Fix and re-test
   - [ ] Update tests if needed

2. Pre-release checklist:
   - [ ] All P0 tasks complete
   - [ ] All tests passing
   - [ ] Documentation complete
   - [ ] CHANGELOG updated
   - [ ] Version bumped (0.4.0 → 0.5.0)

3. Create release:
   - [ ] Git tag v0.5.0
   - [ ] Create GitHub release
   - [ ] Write release notes
   - [ ] Announce release

**Release Criteria** (ALL must be ✓):
- [ ] All 11 tasks complete
- [ ] All tests passing (zero regressions)
- [ ] 13+ templates created and tested
- [ ] Documentation complete
- [ ] Manual testing passed
- [ ] Zero critical bugs

**Definition of Done**:
- [ ] v0.5.0 tagged
- [ ] GitHub release created
- [ ] Release notes published
- [ ] Ready to announce

---

## Sprint Velocity & Estimates

### Time Estimates by Task

| Task ID | Task Name | Estimate | Actual | Variance |
|---------|-----------|----------|--------|----------|
| TMPL-001 | Template Models | 4-6h | ___ | ___ |
| TMPL-002 | Template Manager | 6-8h | ___ | ___ |
| TMPL-003 | Infrastructure Tests | 4-6h | ___ | ___ |
| TMPL-004 | CLI Flag | 4-6h | ___ | ___ |
| TMPL-005 | Prompt System | 6-8h | ___ | ___ |
| TMPL-006 | Integration Tests | 6-8h | ___ | ___ |
| TMPL-007 | Research | 8-12h | ___ | ___ |
| TMPL-008 | Template Creation | 8-12h | ___ | ___ |
| TMPL-009 | Validation Tests | 4-6h | ___ | ___ |
| TMPL-010 | Documentation | 4-6h | ___ | ___ |
| TMPL-011 | Testing & Fixes | 8-12h | ___ | ___ |
| **TOTAL** | **Full Sprint** | **62-90h** | ___ | ___ |

**Note**: Estimates are high-confidence ranges. Track actual time for future planning.

### Daily Velocity Goals

| Day | Tasks | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1 | TMPL-001, 002, 003 | 14-20h | Infrastructure working |
| 2 | TMPL-004, 005, 006 | 16-22h | CLI integration complete |
| 3 | TMPL-007, 008(part) | 12-18h | Research + templates started |
| 4 | TMPL-008(part), 009, 011(part) | 12-18h | All templates created + tested |
| 5 | TMPL-010, 011(part) | 12-18h | Docs + release ready |

---

## Sprint Risks & Mitigation

### Risk 1: Research Takes Longer Than Expected
- **Likelihood**: MEDIUM
- **Impact**: HIGH (blocks template creation)
- **Mitigation**:
  - Start research on Day 1 (parallel with code)
  - Reduce scope to 3 servers if needed (postgres, github, filesystem)
  - Defer additional servers to v0.5.1

### Risk 2: Templates Don't Cover All Use Cases
- **Likelihood**: MEDIUM
- **Impact**: LOW (templates are best-effort)
- **Mitigation**:
  - Focus on common scenarios only
  - Document manual config as fallback
  - Templates are v1 (can iterate in v0.5.1)

### Risk 3: Integration Bugs Discovered Late
- **Likelihood**: LOW
- **Impact**: MEDIUM (delays release)
- **Mitigation**:
  - Integration tests on Day 2 (early validation)
  - Manual testing on Day 4 (buffer time on Day 5)
  - Feature is additive (low risk to existing functionality)

---

## Sprint Retrospective (Post-Release)

### What Went Well
- ___ (fill in after sprint)

### What Could Be Improved
- ___ (fill in after sprint)

### Action Items for Next Sprint
- ___ (fill in after sprint)

---

**Sprint Status**: READY TO START
**Confidence**: 95% (LOW risk, well-scoped sprint)
**Next Action**: Begin Day 1 with TMPL-001

---

*Generated by: Sprint Planner*
*Sprint Duration: 5 days*
*Total Effort: 62-90 hours (conservative estimates)*
