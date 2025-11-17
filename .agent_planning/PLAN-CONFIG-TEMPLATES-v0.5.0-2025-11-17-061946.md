# Configuration Templates Implementation Plan - v0.5.0

**Generated**: 2025-11-17 06:19:46
**Source STATUS**: STATUS-INTERACTIVE-CONFIG-EVALUATION-2025-11-17.md
**Source Spec**: FEATURE_PROPOSAL_POST_V04_DELIGHT.md (Alternative A)
**Project**: MCPI v0.4.0 → v0.5.0
**Feature**: Configuration Templates (Quick Win Alternative to Interactive Wizard)

---

## Provenance

**Input Documents**:
- **STATUS Report**: `.agent_planning/STATUS-INTERACTIVE-CONFIG-EVALUATION-2025-11-17.md` (Evaluation timestamp: 2025-11-17)
- **Feature Proposal**: `.agent_planning/FEATURE_PROPOSAL_POST_V04_DELIGHT.md` (Feature 1, Alternative A)
- **Spec Version**: `PROJECT_SPEC.md` (last modified: 2025-11-17)
- **Generation Time**: 2025-11-17 06:19:46

**Key Findings from STATUS Report**:
- Full Interactive Wizard requires 6-8 weeks (catalog schema extension + enrichment)
- **BLOCKER**: Catalog lacks parameter metadata (env vars, types, defaults, validation)
- **Alternative**: Configuration Templates provides 80% of value with 20% of effort
- **Effort**: 1 week vs 6-8 weeks
- **Risk**: LOW (simple addition, no schema changes)

---

## Executive Summary

### The Problem

Users installing MCP servers face a painful configuration workflow:
1. Run `mcpi add postgres` (server added but doesn't work)
2. Google "mcp postgres server setup"
3. Find GitHub README, scroll through examples
4. Copy/paste example, modify for their setup
5. Manually edit `.mcp.json` (prone to syntax errors)
6. Debug connection issues
7. **Time spent**: 10-30 minutes per server

### The Solution

**Configuration Templates** - Pre-tested configurations for common server scenarios:

```bash
# Instead of manual configuration hunt
$ mcpi add postgres --template production
✓ Installing postgres with production template
✓ Prompts: Database name? Password?
✓ Configuration saved to .mcp.json
✓ Server ready to use

# Quick development setup
$ mcpi add postgres --template local-docker
✓ Pre-configured for localhost:5432
✓ Default credentials: postgres/postgres
✓ Database: myapp_dev
```

### Value Proposition

**Before Templates**:
- 15-30 minutes per server setup
- Trial and error with configuration
- Frequent syntax errors
- Unknown best practices

**After Templates**:
- 2-3 minutes per server setup
- Pre-tested configurations
- Guided prompts for customization
- Learn best practices through examples

### Implementation Strategy

**Phase 1 Only**: Ship Configuration Templates in v0.5.0
- **Effort**: 1 week (vs 6-8 weeks for full wizard)
- **Value**: 80% of wizard benefit for 20% of effort
- **Risk**: LOW (additive feature, no schema changes)
- **Scope**: 5-10 popular servers with 2-3 templates each

**Defer to v0.6.0**: Full Interactive Wizard
- **Prerequisites**: Catalog schema extension (1 week) + Catalog enrichment (2-3 weeks)
- **Total**: 6-8 weeks including wizard implementation
- **Benefit**: Templates inform parameter metadata research

---

## 1. Architecture Design

### 1.1 Template Structure

**Template Definition** (YAML format):

```yaml
# data/templates/postgres/production.yaml
name: production
description: "Production PostgreSQL with TLS and connection pooling"
server_id: postgres
scope: user-global  # Recommended scope
priority: high  # Used for sorting in template list

# Static configuration (always applied)
config:
  command: npx
  args:
    - "-y"
    - "@modelcontextprotocol/server-postgres"
  env:
    POSTGRES_PORT: "5432"
    POSTGRES_SSL_MODE: "require"

# Dynamic prompts (ask user)
prompts:
  - name: POSTGRES_HOST
    description: "Database host (e.g., db.example.com)"
    type: string
    required: true
    default: null
    validate: "^[a-zA-Z0-9.-]+$"

  - name: POSTGRES_DB
    description: "Database name"
    type: string
    required: true
    default: null

  - name: POSTGRES_USER
    description: "Database username"
    type: string
    required: true
    default: "postgres"

  - name: POSTGRES_PASSWORD
    description: "Database password"
    type: secret  # Hidden input
    required: true
    default: null

# Documentation
notes: |
  Production template with:
  - TLS encryption enabled
  - Default port 5432
  - Requires valid database credentials

  Test connection with:
    psql -h <host> -U <user> -d <db>
```

### 1.2 Template Manager Architecture

**New Module**: `src/mcpi/templates/template_manager.py`

```python
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

class PromptDefinition(BaseModel):
    """Interactive prompt for template parameter."""
    name: str
    description: str
    type: str  # string, secret, path, port, url
    required: bool = False
    default: Optional[str] = None
    validate: Optional[str] = None  # Regex pattern

class ServerTemplate(BaseModel):
    """Template for server configuration."""
    name: str
    description: str
    server_id: str
    scope: str
    priority: str  # high, medium, low
    config: Dict[str, Any]
    prompts: List[PromptDefinition]
    notes: str

class TemplateManager:
    """Manages configuration templates."""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self._templates: Dict[str, Dict[str, ServerTemplate]] = {}

    def load_templates(self) -> None:
        """Load all templates from template directory."""
        # Structure: data/templates/{server_id}/{template_name}.yaml
        for server_dir in self.template_dir.iterdir():
            if server_dir.is_dir():
                server_id = server_dir.name
                self._templates[server_id] = {}

                for template_file in server_dir.glob("*.yaml"):
                    template = self._load_template_file(template_file)
                    self._templates[server_id][template.name] = template

    def list_templates(self, server_id: str) -> List[ServerTemplate]:
        """List available templates for a server."""
        return sorted(
            self._templates.get(server_id, {}).values(),
            key=lambda t: ("high", "medium", "low").index(t.priority)
        )

    def get_template(self, server_id: str, template_name: str) -> Optional[ServerTemplate]:
        """Get specific template."""
        return self._templates.get(server_id, {}).get(template_name)

    def apply_template(
        self,
        template: ServerTemplate,
        user_values: Dict[str, str]
    ) -> ServerConfig:
        """Apply template with user-provided values."""
        # Merge static config with user values
        env = {**template.config.get("env", {}), **user_values}

        return ServerConfig(
            command=template.config["command"],
            args=template.config["args"],
            env=env
        )

# Factory functions
def create_default_template_manager() -> TemplateManager:
    """Create template manager with default template directory."""
    package_dir = Path(__file__).parent.parent.parent
    template_dir = package_dir / "data" / "templates"
    return TemplateManager(template_dir=template_dir)

def create_test_template_manager(test_dir: Path) -> TemplateManager:
    """Create template manager for testing."""
    return TemplateManager(template_dir=test_dir)
```

### 1.3 Integration with Existing Architecture

**No Breaking Changes**:
- ✅ Templates are ADDITIVE (new `--template` flag on `mcpi add`)
- ✅ Existing `mcpi add <server>` behavior unchanged
- ✅ No changes to `ServerCatalog`, `MCPManager`, or plugin system
- ✅ No catalog schema modifications required

**Integration Points**:
1. **CLI** (`src/mcpi/cli.py`):
   - Add `--template` option to `add` command
   - Add `--list-templates` flag to show available templates
   - Interactive prompts using Rich.Prompt

2. **Template Discovery**:
   - Template files in `data/templates/{server_id}/*.yaml`
   - Lazy loading (only load when `--template` flag used)
   - Validation with Pydantic models

3. **User Interaction Flow**:
   ```
   User: mcpi add postgres --template production
   ↓
   CLI loads template from data/templates/postgres/production.yaml
   ↓
   CLI prompts for required values (host, db, user, password)
   ↓
   Template Manager merges static + dynamic config
   ↓
   MCPManager.add_server() called with complete config
   ↓
   Server installed with working configuration
   ```

---

## 2. Implementation Breakdown

### 2.1 Phase 1: Template Infrastructure (Days 1-2)

**TMPL-001: Template Data Models**
- **Status**: Not Started
- **Effort**: Small (4-6 hours)
- **Dependencies**: None
- **Priority**: P0 (Critical)

**Description**: Define Pydantic models for template schema

**Acceptance Criteria**:
- [ ] `PromptDefinition` model validates prompt structure
- [ ] `ServerTemplate` model validates template structure
- [ ] Type support: string, secret, path, port, url
- [ ] Validation regex support for prompts
- [ ] Default value support
- [ ] Required vs optional prompt distinction

**Technical Notes**:
- Use Pydantic's field validators for type checking
- Support for secret masking (type="secret")
- Path validation (check if directory exists)
- Port validation (1-65535 range)

**Files to Create**:
- `src/mcpi/templates/__init__.py`
- `src/mcpi/templates/models.py`

---

**TMPL-002: Template Manager Implementation**
- **Status**: Not Started
- **Effort**: Medium (6-8 hours)
- **Dependencies**: TMPL-001
- **Priority**: P0 (Critical)

**Description**: Implement `TemplateManager` class with load/apply logic

**Acceptance Criteria**:
- [ ] Loads templates from `data/templates/{server_id}/*.yaml`
- [ ] `list_templates(server_id)` returns sorted templates
- [ ] `get_template(server_id, name)` returns specific template
- [ ] `apply_template(template, values)` merges config
- [ ] Graceful handling of missing template directory
- [ ] Validation errors provide clear messages

**Technical Notes**:
- Lazy loading (don't load until needed)
- Cache loaded templates in memory
- Use YAML safe_load for security
- Factory functions for DIP compliance

**Files to Create**:
- `src/mcpi/templates/template_manager.py`

---

**TMPL-003: Template Infrastructure Tests**
- **Status**: Not Started
- **Effort**: Small (4-6 hours)
- **Dependencies**: TMPL-001, TMPL-002
- **Priority**: P0 (Critical)

**Description**: Comprehensive unit tests for template models and manager

**Acceptance Criteria**:
- [ ] Test template loading from YAML
- [ ] Test template validation (invalid templates rejected)
- [ ] Test template listing and sorting
- [ ] Test template application with user values
- [ ] Test error handling (missing files, invalid YAML)
- [ ] 100% code coverage for template module

**Technical Notes**:
- Use pytest fixtures for test templates
- Test with tmp_path for isolated file operations
- Mock YAML loading for error scenarios

**Files to Create**:
- `tests/test_templates_models.py`
- `tests/test_template_manager.py`
- `tests/fixtures/templates/` (test data)

---

### 2.2 Phase 2: CLI Integration (Days 2-3)

**TMPL-004: Add --template Flag to CLI**
- **Status**: Not Started
- **Effort**: Medium (4-6 hours)
- **Dependencies**: TMPL-002
- **Priority**: P0 (Critical)

**Description**: Integrate `--template` option into `mcpi add` command

**Acceptance Criteria**:
- [ ] `mcpi add <server> --template <name>` works
- [ ] `mcpi add <server> --list-templates` shows available templates
- [ ] Error if template doesn't exist for server
- [ ] Error if both `--template` and `--env` provided (conflicting)
- [ ] Help text explains template usage
- [ ] Tab completion for template names

**Technical Notes**:
- Use Click's option with callback for `--list-templates`
- Lazy-load TemplateManager (fast CLI startup)
- Rich table for displaying template list
- Clear error messages for missing templates

**Files to Modify**:
- `src/mcpi/cli.py` (add command modifications)

---

**TMPL-005: Interactive Prompt System**
- **Status**: Not Started
- **Effort**: Medium (6-8 hours)
- **Dependencies**: TMPL-004
- **Priority**: P0 (Critical)

**Description**: Implement interactive prompting for template parameters

**Acceptance Criteria**:
- [ ] Prompt for each required template parameter
- [ ] Show default value in prompt
- [ ] Validate input against regex (if provided)
- [ ] Mask secret input (type="secret")
- [ ] Allow user to abort (Ctrl+C)
- [ ] Beautiful Rich UI with clear descriptions

**Technical Notes**:
- Use `rich.prompt.Prompt` for text input
- Use `rich.prompt.Confirm` for yes/no
- Use `getpass` for secret input
- Validate in real-time, re-prompt if invalid
- Show validation errors clearly

**Files to Modify**:
- `src/mcpi/cli.py` (add command prompt logic)

**Files to Create**:
- `src/mcpi/templates/prompt_handler.py` (reusable prompt logic)

---

**TMPL-006: CLI Integration Tests**
- **Status**: Not Started
- **Effort**: Medium (6-8 hours)
- **Dependencies**: TMPL-004, TMPL-005
- **Priority**: P0 (Critical)

**Description**: Integration tests for CLI template functionality

**Acceptance Criteria**:
- [ ] Test `mcpi add --template` with mock prompts
- [ ] Test `--list-templates` output format
- [ ] Test error cases (invalid template, missing server)
- [ ] Test template application end-to-end
- [ ] Test secret masking in prompts
- [ ] Test validation failures and retry

**Technical Notes**:
- Use Click's CliRunner for testing
- Mock Rich prompts for predictable input
- Verify config file written correctly
- Test with real template files

**Files to Create**:
- `tests/test_cli_templates.py`

---

### 2.3 Phase 3: Template Content Creation (Days 3-5)

**TMPL-007: Research Server Parameters**
- **Status**: Not Started
- **Effort**: Large (12-16 hours)
- **Dependencies**: None (can run in parallel with TMPL-001-006)
- **Priority**: P1 (High)

**Description**: Research configuration requirements for 5-10 popular servers

**Acceptance Criteria**:
- [ ] Document parameters for: postgres, github, slack, filesystem, brave-search
- [ ] Identify 2-3 common scenarios per server
- [ ] Test each configuration manually
- [ ] Document best practices and gotchas
- [ ] Create template specification document

**Technical Notes**:
- Consult official documentation for each server
- Test with real server instances (Docker for databases)
- Identify common environment variables
- Note required vs optional parameters
- Document default values and validation rules

**Deliverable**: `data/templates/TEMPLATE_SPECS.md` (parameter documentation)

---

**TMPL-008: Create Template Files**
- **Status**: Not Started
- **Effort**: Large (12-16 hours)
- **Dependencies**: TMPL-007
- **Priority**: P1 (High)

**Description**: Write YAML templates for 5-10 popular servers

**Acceptance Criteria**:
- [ ] PostgreSQL: production, local-docker, development
- [ ] GitHub: full-access, read-only, public-repos
- [ ] Slack: bot-token, user-token
- [ ] Filesystem: project-files, user-documents, read-only
- [ ] Brave Search: free-tier, api-key
- [ ] All templates validated against schema
- [ ] All templates tested manually

**Technical Notes**:
- Follow template structure from TMPL-001
- Include clear descriptions and notes
- Set appropriate defaults
- Test each template by installing server

**Files to Create**:
- `data/templates/postgres/production.yaml`
- `data/templates/postgres/local-docker.yaml`
- `data/templates/postgres/development.yaml`
- `data/templates/github/full-access.yaml`
- `data/templates/github/read-only.yaml`
- `data/templates/github/public-repos.yaml`
- `data/templates/slack/bot-token.yaml`
- `data/templates/slack/user-token.yaml`
- `data/templates/filesystem/project-files.yaml`
- `data/templates/filesystem/user-documents.yaml`
- `data/templates/filesystem/read-only.yaml`
- `data/templates/brave-search/free-tier.yaml`
- `data/templates/brave-search/api-key.yaml`

---

**TMPL-009: Template Validation Tests**
- **Status**: Not Started
- **Effort**: Small (4-6 hours)
- **Dependencies**: TMPL-008
- **Priority**: P1 (High)

**Description**: Validate all template files against schema

**Acceptance Criteria**:
- [ ] All template files parse successfully
- [ ] All templates pass Pydantic validation
- [ ] All prompts have valid types
- [ ] All regex patterns compile
- [ ] Integration test loads all templates
- [ ] No duplicate template names per server

**Technical Notes**:
- Automated test that loads all templates
- Fail fast on first validation error
- Clear error messages for template authors

**Files to Create**:
- `tests/test_template_validation.py`

---

### 2.4 Phase 4: Documentation & Polish (Day 5)

**TMPL-010: User Documentation**
- **Status**: Not Started
- **Effort**: Medium (4-6 hours)
- **Dependencies**: All above
- **Priority**: P1 (High)

**Description**: Update user-facing documentation with template examples

**Acceptance Criteria**:
- [ ] README.md updated with template section
- [ ] CLAUDE.md updated with template architecture
- [ ] CHANGELOG.md updated with v0.5.0 features
- [ ] Template usage examples
- [ ] Template authoring guide
- [ ] FAQ section for templates

**Technical Notes**:
- Include example workflows
- Screenshot of `--list-templates` output
- Clear explanation of when to use templates vs manual config
- Migration guide (none needed, fully additive)

**Files to Modify**:
- `README.md`
- `CLAUDE.md`
- `CHANGELOG.md`

**Files to Create**:
- `docs/TEMPLATE_AUTHORING_GUIDE.md`

---

**TMPL-011: Manual Testing & Bug Fixes**
- **Status**: Not Started
- **Effort**: Medium (4-6 hours)
- **Dependencies**: All above
- **Priority**: P0 (Critical)

**Description**: Comprehensive manual testing of template feature

**Acceptance Criteria**:
- [ ] Test all templates on clean system
- [ ] Test with invalid input (validation works)
- [ ] Test secret masking (passwords hidden)
- [ ] Test Ctrl+C abort (graceful exit)
- [ ] Test `--list-templates` for all servers
- [ ] Fix all bugs discovered
- [ ] Zero test regressions

**Technical Notes**:
- Use fresh install environment
- Test with real MCP clients (Claude Code)
- Verify servers actually work after template install
- Document any edge cases found

**Deliverable**: Manual test report + bug fixes

---

## 3. Dependency Graph

```
Prerequisites (can run in parallel):
├─ TMPL-007: Research Server Parameters
│
Implementation (sequential):
├─ TMPL-001: Template Data Models
├─ TMPL-002: Template Manager Implementation
├─ TMPL-003: Template Infrastructure Tests
│
CLI Integration (sequential):
├─ TMPL-004: Add --template Flag
├─ TMPL-005: Interactive Prompt System
├─ TMPL-006: CLI Integration Tests
│
Content Creation (parallel with CLI work):
├─ TMPL-007: Research (prerequisite for TMPL-008)
├─ TMPL-008: Create Template Files
├─ TMPL-009: Template Validation Tests
│
Final (sequential):
├─ TMPL-010: User Documentation
├─ TMPL-011: Manual Testing & Bug Fixes
```

**Critical Path**:
1. TMPL-001 → TMPL-002 → TMPL-004 → TMPL-005 (CLI working with templates)
2. TMPL-007 → TMPL-008 (template content ready)
3. TMPL-010 → TMPL-011 (documentation + testing)

**Parallelizable Work**:
- TMPL-007 (research) can start immediately
- TMPL-008 (content) can progress while CLI is being built
- TMPL-009 (validation tests) can start as templates are created

---

## 4. Risk Assessment

### 4.1 Technical Risks

**RISK-001: Template Format Insufficient**
- **Severity**: MEDIUM
- **Likelihood**: LOW
- **Impact**: Templates can't express all configuration scenarios
- **Mitigation**:
  - Start with 5 well-understood servers
  - Iterate template schema based on real needs
  - Support escape hatch (combine `--template` with manual editing later)
  - Templates are YAML (easy to extend schema)
- **Contingency**: Add advanced template features in v0.5.1 if needed

**RISK-002: Prompt UX Complexity**
- **Severity**: MEDIUM
- **Likelihood**: MEDIUM
- **Impact**: Too many prompts annoy users
- **Mitigation**:
  - Only prompt for REQUIRED parameters
  - Use smart defaults (show in prompt)
  - Allow skipping optional prompts (Enter = use default)
  - Beautiful Rich UI with clear descriptions
- **Contingency**: Add `--quick` flag to use all defaults

**RISK-003: Template Maintenance Burden**
- **Severity**: LOW
- **Likelihood**: MEDIUM
- **Impact**: Templates become outdated as servers evolve
- **Mitigation**:
  - Version templates with creation date
  - Include server version compatibility in template
  - Document template testing process
  - Community can contribute template updates
- **Contingency**: Mark outdated templates as deprecated

### 4.2 User Experience Risks

**RISK-004: Template Discovery**
- **Severity**: MEDIUM
- **Likelihood**: MEDIUM
- **Impact**: Users don't know templates exist
- **Mitigation**:
  - `mcpi add <server>` suggests `--list-templates` if available
  - Help text prominently features templates
  - README examples use templates
  - Error messages suggest templates
- **Contingency**: Add `mcpi templates` command to list all

**RISK-005: Template vs Manual Confusion**
- **Severity**: LOW
- **Likelihood**: LOW
- **Impact**: Users don't know when to use templates
- **Mitigation**:
  - Clear documentation of use cases
  - Templates for common scenarios only
  - Manual config still fully supported
  - Error if both `--template` and `--env` used
- **Contingency**: Add FAQ section addressing this

### 4.3 Implementation Risks

**RISK-006: Research Time Underestimated**
- **Severity**: HIGH
- **Likelihood**: MEDIUM
- **Impact**: TMPL-007/008 takes longer than 2 days
- **Mitigation**:
  - Start research immediately (parallel with code)
  - Reduce scope to 3-5 servers if needed
  - Prioritize most popular servers (postgres, github, filesystem)
  - Template format is simple (YAML with prompts)
- **Contingency**: Ship v0.5.0 with 3 servers, add more in v0.5.1

**RISK-007: Integration Bugs**
- **Severity**: MEDIUM
- **Likelihood**: LOW
- **Impact**: Template system breaks existing functionality
- **Mitigation**:
  - Feature is ADDITIVE (new flag only)
  - Comprehensive integration tests
  - Manual testing before release
  - Zero changes to existing code paths
- **Contingency**: Feature flag to disable templates if critical bug found

---

## 5. Success Criteria

### 5.1 Functional Requirements

**Must Have** (v0.5.0):
- [ ] `mcpi add <server> --template <name>` installs with template
- [ ] `mcpi add <server> --list-templates` shows available templates
- [ ] Interactive prompts for required parameters
- [ ] Secret masking for password inputs
- [ ] Input validation (regex, type checking)
- [ ] 5+ servers with 2-3 templates each (10+ total templates)
- [ ] All templates manually tested and working
- [ ] Clear error messages for invalid input
- [ ] Documentation complete (README, CLAUDE.md, CHANGELOG)
- [ ] Zero test regressions

**Should Have** (v0.5.0 or v0.5.1):
- [ ] Template notes displayed before prompts
- [ ] Default values shown in prompts
- [ ] Validation error messages show examples
- [ ] Template authoring guide for community

**Could Have** (v0.6.0):
- [ ] `mcpi template list` (dedicated command)
- [ ] Template versioning and compatibility tracking
- [ ] Community template repository
- [ ] Template testing framework

### 5.2 Quality Requirements

**Code Quality**:
- [ ] 100% code coverage for template module
- [ ] All new code passes black, ruff, mypy
- [ ] Zero security vulnerabilities (secret handling)
- [ ] Clear, maintainable code (follows MCPI patterns)

**Testing**:
- [ ] Unit tests for all template functions
- [ ] Integration tests for CLI workflows
- [ ] Validation tests for all template files
- [ ] Manual testing checklist completed
- [ ] All tests pass (no regressions)

**Performance**:
- [ ] Template loading < 100ms
- [ ] No impact on `mcpi add` without `--template`
- [ ] CLI startup time unchanged (lazy loading)

**Documentation**:
- [ ] README examples use templates
- [ ] CLAUDE.md explains template architecture
- [ ] CHANGELOG.md lists v0.5.0 features
- [ ] Template authoring guide complete
- [ ] Help text clear and accurate

### 5.3 Release Criteria

**Blocking** (must be done):
- [ ] All P0 tasks complete (TMPL-001-006, TMPL-011)
- [ ] All template files created and tested (TMPL-008)
- [ ] Documentation complete (TMPL-010)
- [ ] Manual testing passed (TMPL-011)
- [ ] Zero critical bugs
- [ ] All tests passing

**Non-Blocking** (can defer):
- [ ] Template authoring guide (nice-to-have)
- [ ] Community contribution process (v0.5.1)
- [ ] Additional servers beyond initial 5 (v0.5.1)

---

## 6. Timeline & Milestones

### 6.1 Day-by-Day Plan

**Day 1: Infrastructure (TMPL-001, TMPL-002, TMPL-003)**
- Morning: Template data models (4h)
- Afternoon: TemplateManager implementation (4h)
- Evening: Unit tests (4h)
- **Deliverable**: Template infrastructure working, tested

**Day 2: CLI Integration (TMPL-004, TMPL-005, TMPL-006)**
- Morning: Add --template flag to CLI (4h)
- Afternoon: Interactive prompt system (4h)
- Evening: CLI integration tests (4h)
- **Deliverable**: `mcpi add --template` working end-to-end

**Day 3: Research & Content (TMPL-007, TMPL-008 start)**
- Morning: Research postgres, github parameters (4h)
- Afternoon: Research filesystem, slack, brave-search (4h)
- Evening: Start creating template files (4h)
- **Deliverable**: Parameter specs documented, first templates created

**Day 4: Content Completion (TMPL-008, TMPL-009)**
- Morning: Finish creating template files (4h)
- Afternoon: Template validation tests (4h)
- Evening: Test all templates manually (4h)
- **Deliverable**: All templates created, validated, tested

**Day 5: Documentation & Release (TMPL-010, TMPL-011)**
- Morning: Update README, CLAUDE.md, CHANGELOG (4h)
- Afternoon: Comprehensive manual testing (4h)
- Evening: Bug fixes, final testing (4h)
- **Deliverable**: v0.5.0 ready to ship

### 6.2 Milestones

**M1: Infrastructure Complete** (End of Day 1)
- Template models defined
- TemplateManager working
- 100% unit test coverage

**M2: CLI Integration Complete** (End of Day 2)
- `--template` flag working
- Interactive prompts functional
- Integration tests passing

**M3: Content Complete** (End of Day 4)
- 5+ servers with templates
- All templates tested
- Validation suite passing

**M4: Release Ready** (End of Day 5)
- Documentation complete
- Manual testing passed
- v0.5.0 tagged and ready

### 6.3 Buffer Time

**Built-in Buffer**:
- Each task estimated conservatively (high end of range)
- Day 5 has buffer for unexpected bugs
- Can reduce server count if behind schedule

**Contingency Plan**:
- If Day 3-4 runs long, ship with 3 servers instead of 5
- If Day 5 blocked, slip to Day 6 (still within 1 week)
- Templates can be added incrementally in v0.5.1

---

## 7. Post-Release Plan

### 7.1 Immediate Follow-Up (v0.5.1)

**Incremental Improvements**:
- Add templates for 5-10 more servers
- Community template contribution process
- Template testing framework
- Performance optimizations if needed

**Effort**: 2-3 days
**Timeline**: 1-2 weeks after v0.5.0

### 7.2 Long-Term Evolution (v0.6.0)

**Templates Inform Interactive Wizard**:
1. Templates demonstrate common parameter patterns
2. Template research reveals parameter metadata
3. Use template content to populate catalog schema
4. Build Interactive Wizard using template learnings

**Benefits of This Approach**:
- Templates provide immediate user value NOW
- Template research reduces catalog enrichment effort (already done)
- Template feedback informs wizard design
- No wasted work (templates remain useful after wizard ships)

**v0.6.0 Timeline** (after v0.5.0 ships):
- Week 1: Catalog schema extension (use template research)
- Week 2-3: Catalog enrichment (port template data to catalog)
- Week 4-5: Interactive Wizard implementation
- Week 6: Testing, documentation, release

---

## 8. Comparison to Full Interactive Wizard

### 8.1 Feature Comparison

| Aspect | Templates (v0.5.0) | Interactive Wizard (v0.6.0) |
|--------|-------------------|---------------------------|
| **Effort** | 1 week | 6-8 weeks |
| **Schema Changes** | None | Catalog schema extension required |
| **Server Coverage** | 5-10 servers | 8-12 servers |
| **Customization** | Pre-defined scenarios | Fully dynamic |
| **Validation** | Basic (regex) | Advanced (connection testing) |
| **User Experience** | Good (guided prompts) | Excellent (intelligent wizard) |
| **Risk** | LOW | MEDIUM |
| **Value Delivered** | 80% of wizard benefit | 100% |

### 8.2 Why Templates First

**Strategic Advantages**:
1. **Immediate Value**: Users get help with configuration NOW (not in 2 months)
2. **Learning Opportunity**: Template research informs catalog metadata
3. **Risk Reduction**: Low-risk feature to test user acceptance
4. **Foundation Building**: Templates remain useful after wizard ships
5. **Incremental Progress**: Ship value every 1-2 weeks, not 2 months

**User Journey**:
- **v0.5.0**: User installs postgres with `--template production` (2 minutes, works perfectly)
- **v0.6.0**: User installs new server with `--interactive` (wizard uses catalog metadata)
- **Both coexist**: Templates for quick setups, wizard for custom configs

---

## 9. Open Questions

### 9.1 Design Decisions

**Q1: Should templates support conditional prompts?**
- Example: Only prompt for SSL cert if SSL_MODE=require
- **Answer**: DEFER to v0.5.1 (YAGNI - keep templates simple for v0.5.0)

**Q2: Should `--template` and `--env` be mutually exclusive?**
- **Answer**: YES (prevent confusion, clear error message)

**Q3: Should we support template composition (base + overrides)?**
- Example: base postgres template + production overrides
- **Answer**: DEFER to v0.5.1 (simple templates first, add complexity if needed)

**Q4: Should templates specify recommended scope?**
- **Answer**: YES (template includes `scope: user-global`, but user can override with `--scope`)

### 9.2 Implementation Decisions

**Q5: YAML vs JSON for template format?**
- **Answer**: YAML (more human-readable, supports comments, better for docs)

**Q6: Where to store templates?**
- **Answer**: `data/templates/{server_id}/{template_name}.yaml` (mirrors catalog structure)

**Q7: Should template manager be singleton or injected?**
- **Answer**: DIP-compliant (factory functions, injectable for tests)

---

## 10. Appendix: Example Workflows

### 10.1 User Workflow: First-Time Postgres Setup

**Without Templates** (current v0.4.0):
```bash
$ mcpi add postgres
✓ Server added to .mcp.json

$ claude mcp list
postgres: NOT WORKING (missing env vars)

$ # User googles "mcp postgres setup"
$ # User finds GitHub README
$ # User edits .mcp.json manually
$ # User adds POSTGRES_HOST, POSTGRES_DB, etc.
$ # User reloads Claude Code
$ # User tests, finds typo in JSON
$ # User fixes, reloads again
$ # Finally works after 15 minutes
```

**With Templates** (v0.5.0):
```bash
$ mcpi add postgres --list-templates

Available templates for postgres:
  1. production - Production PostgreSQL with TLS
  2. local-docker - Local Docker PostgreSQL
  3. development - Development PostgreSQL

$ mcpi add postgres --template local-docker

Installing postgres with template: local-docker
─────────────────────────────────────────────

Database Configuration
──────────────────────
Database name: myapp_dev
Database password: ••••••••

✓ Installing postgres to project-mcp scope
✓ Configuration saved to .mcp.json
✓ Server ready to use

Next: Reload Claude Code to activate

$ # Works immediately, 2 minutes total
```

### 10.2 Developer Workflow: Adding New Template

**Step 1: Research server parameters**
```bash
$ cd ~/projects/mcpi
$ # Read server documentation
$ # Test server manually
$ # Document required env vars
```

**Step 2: Create template file**
```yaml
# data/templates/myserver/production.yaml
name: production
description: "Production setup with API key"
server_id: myserver
scope: user-global
priority: high

config:
  command: npx
  args: ["-y", "@example/mcp-server-myserver"]
  env:
    API_ENDPOINT: "https://api.example.com"

prompts:
  - name: API_KEY
    description: "Your API key from example.com"
    type: secret
    required: true
    validate: "^[A-Za-z0-9_-]{32,}$"

notes: |
  Get your API key at: https://example.com/api-keys
  Free tier limited to 1000 requests/day
```

**Step 3: Test template**
```bash
$ mcpi add myserver --template production
# Verify prompts work, server installs correctly
```

**Step 4: Add validation test**
```python
# tests/test_template_validation.py
def test_myserver_production_template():
    template = manager.get_template("myserver", "production")
    assert template is not None
    assert len(template.prompts) == 1
```

---

**Plan Status**: READY FOR IMPLEMENTATION
**Confidence Level**: 95% (LOW risk, well-understood scope)
**Next Action**: Begin TMPL-001 (Template Data Models)

---

*Generated by: Strategic Product Planner*
*Plan Duration: 5 days (1 week)*
*Files to Create: 25+ (code, tests, templates, docs)*
*Lines of Code: ~1000 (estimated)*
