# Configuration Templates - v0.5.0 Planning Summary

**Generated**: 2025-11-17 06:19:46
**Source STATUS**: STATUS-INTERACTIVE-CONFIG-EVALUATION-2025-11-17.md
**Source Spec**: PROJECT_SPEC.md + FEATURE_PROPOSAL_POST_V04_DELIGHT.md
**Planning Files**:
- Detailed Plan: `PLAN-CONFIG-TEMPLATES-v0.5.0-2025-11-17-061946.md`
- Sprint Backlog: `SPRINT-CONFIG-TEMPLATES-v0.5.0-2025-11-17-061946.md`

---

## Executive Summary

### The Decision

Ship **Configuration Templates** in v0.5.0 instead of the full Interactive Configuration Wizard.

**Why This Decision**:
- Full wizard requires 6-8 weeks (catalog schema extension + enrichment)
- Templates provide 80% of value with 20% of effort (1 week vs 6-8 weeks)
- Templates are LOW risk (additive feature, no schema changes)
- Templates inform future wizard implementation (research reuse)

### Value Proposition

**User Pain Point** (from STATUS evaluation):
> Users installing MCP servers spend 10-30 minutes per server:
> 1. Install server (doesn't work - missing env vars)
> 2. Google "mcp postgres setup"
> 3. Find GitHub README, copy examples
> 4. Manually edit JSON (prone to syntax errors)
> 5. Debug connection issues
> 6. Finally works after 15+ minutes

**Solution**:
```bash
# Before v0.5.0: 15-30 minutes of manual config
$ mcpi add postgres
# User googles, edits JSON, debugs...

# After v0.5.0: 2-3 minutes with template
$ mcpi add postgres --template production
Database host: db.example.com
Database name: myapp
Database user: admin
Database password: ••••••••
✓ Server ready to use
```

**Impact**:
- **Time Savings**: 15-30 min → 2-3 min (87-90% reduction)
- **Success Rate**: ~40% → ~90% first-time success
- **User Delight**: Pre-tested configs, guided prompts, validation

---

## Implementation Overview

### Scope

**v0.5.0 Deliverables**:
1. **Template Infrastructure**: Models, manager, loading system
2. **CLI Integration**: `--template` flag, interactive prompts
3. **Template Content**: 13+ templates for 5 popular servers
4. **Documentation**: README, CLAUDE.md, authoring guide
5. **Quality**: 100% test coverage, zero regressions

**Servers with Templates**:
- **PostgreSQL**: production, local-docker, development (3 templates)
- **GitHub**: full-access, read-only, public-repos (3 templates)
- **Filesystem**: project-files, user-documents, read-only (3 templates)
- **Slack**: bot-token, user-token (2 templates)
- **Brave Search**: free-tier, api-key (2 templates)

**Total**: 13 templates across 5 servers

### Effort Estimate

**Total Effort**: 62-90 hours (1 week, 5 days)

**Breakdown by Phase**:
| Phase | Effort | Days | Tasks |
|-------|--------|------|-------|
| Infrastructure | 14-20h | Day 1 | Models, Manager, Tests |
| CLI Integration | 16-22h | Day 2 | Flag, Prompts, Tests |
| Research & Content | 24-30h | Days 3-4 | Parameter research, Template creation |
| Documentation | 12-18h | Day 5 | Docs, Testing, Release |

**Confidence**: 95% (LOW risk, well-understood requirements)

---

## Architecture

### Template Structure (YAML)

```yaml
# data/templates/{server_id}/{template_name}.yaml
name: production
description: "Production PostgreSQL with TLS"
server_id: postgres
scope: user-global  # Recommended scope
priority: high

# Static configuration
config:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-postgres"]
  env:
    POSTGRES_PORT: "5432"
    POSTGRES_SSL_MODE: "require"

# Dynamic prompts (user input)
prompts:
  - name: POSTGRES_HOST
    description: "Database host"
    type: string
    required: true
    validate: "^[a-zA-Z0-9.-]+$"

  - name: POSTGRES_PASSWORD
    description: "Database password"
    type: secret  # Masked input
    required: true

notes: |
  Production template with TLS enabled.
  Test connection: psql -h <host> -U <user> -d <db>
```

### Integration Points

**No Breaking Changes**:
- ✅ New `--template` option on `mcpi add` (optional)
- ✅ New `--list-templates` flag to show available
- ✅ Existing `mcpi add` behavior unchanged
- ✅ Zero changes to catalog, manager, or plugin system

**New Components**:
1. `src/mcpi/templates/models.py` - Pydantic models
2. `src/mcpi/templates/template_manager.py` - Template loading/application
3. `src/mcpi/templates/prompt_handler.py` - Interactive prompts
4. `data/templates/{server}/` - Template YAML files

**CLI Flow**:
```
User: mcpi add postgres --template production
↓
CLI loads template from data/templates/postgres/production.yaml
↓
CLI prompts for required values (host, db, user, password)
↓
TemplateManager merges static + dynamic config
↓
MCPManager.add_server() called with complete ServerConfig
↓
Server installed with working configuration
```

---

## Task Breakdown (11 Tasks)

### Day 1: Infrastructure (3 tasks, 14-20h)

**TMPL-001**: Template Data Models (4-6h) - P0
- Pydantic models for templates and prompts
- Type validation (string, secret, path, port, url)
- Regex validation support

**TMPL-002**: Template Manager (6-8h) - P0
- Load templates from YAML files
- List, get, apply templates
- Factory functions (DIP compliance)

**TMPL-003**: Infrastructure Tests (4-6h) - P0
- 100% coverage for models and manager
- Test fixtures for template files

### Day 2: CLI Integration (3 tasks, 16-22h)

**TMPL-004**: CLI Flag (4-6h) - P0
- Add `--template` option to `mcpi add`
- Add `--list-templates` flag
- Lazy loading, error handling

**TMPL-005**: Prompt System (6-8h) - P0
- Interactive prompts with Rich UI
- Validation, secret masking
- Error recovery

**TMPL-006**: CLI Tests (6-8h) - P0
- Integration tests for CLI workflows
- Mock prompts for predictable testing

### Days 3-4: Content (3 tasks, 24-30h)

**TMPL-007**: Research Parameters (8-12h) - P1
- Document parameters for 5 servers
- Identify common scenarios
- Test configurations manually

**TMPL-008**: Create Templates (8-12h) - P1
- Write 13 YAML template files
- Follow template schema
- Test each template

**TMPL-009**: Validation Tests (4-6h) - P1
- Automated template validation
- Verify all templates parse

### Day 5: Documentation & Release (2 tasks, 12-18h)

**TMPL-010**: Documentation (4-6h) - P1
- Update README, CLAUDE.md, CHANGELOG
- Create template authoring guide

**TMPL-011**: Testing & Release (8-12h) - P0
- Manual testing (all templates)
- Bug fixes
- Release v0.5.0

---

## Risk Assessment

### Low Risk Factors

**Technical** (95% confidence):
- ✅ No catalog schema changes (purely additive)
- ✅ No changes to existing code paths
- ✅ Simple YAML format (easy to validate)
- ✅ DIP-compliant architecture (testable)
- ✅ Feature flag possible (can disable if critical bug)

**Implementation** (90% confidence):
- ✅ Well-scoped (clear boundaries)
- ✅ Incremental delivery (can ship with 3 servers if needed)
- ✅ Existing patterns (similar to bundles feature)
- ✅ Conservative estimates (buffer built in)

### Medium Risk Factors

**Content Creation** (80% confidence):
- ⚠️ Research may take longer than estimated
- ⚠️ Templates may not cover all use cases
- **Mitigation**: Start research early, reduce scope to 3 servers if needed

**User Experience** (85% confidence):
- ⚠️ Prompt UX might be too verbose
- ⚠️ Users might not discover templates
- **Mitigation**: Only prompt for required params, suggest templates in help

### Mitigation Strategy

**If Behind Schedule**:
1. Reduce to 3 servers (postgres, github, filesystem)
2. Ship with 6-9 templates instead of 13
3. Add remaining servers in v0.5.1 (1-2 days)

**If Critical Bug Found**:
1. Templates are optional (existing workflow unaffected)
2. Can disable `--template` flag if needed
3. Fix in v0.5.1, release in days (not weeks)

---

## Success Metrics

### Functional Requirements (Must Have)

- [ ] `mcpi add <server> --template <name>` works end-to-end
- [ ] `mcpi add <server> --list-templates` shows available templates
- [ ] Interactive prompts for required parameters
- [ ] Secret masking (type="secret")
- [ ] Input validation (regex, type checking)
- [ ] 5+ servers with 2-3 templates each (10+ total)
- [ ] All templates manually tested and working
- [ ] Clear error messages
- [ ] Zero test regressions

### Quality Requirements (Must Have)

- [ ] 100% code coverage for template module
- [ ] All tests passing
- [ ] Black, ruff, mypy clean
- [ ] Zero security issues (secret handling)
- [ ] Documentation complete

### User Experience Goals (Should Have)

- [ ] Setup time reduced: 15+ min → 2-3 min
- [ ] First-time success rate: 40% → 90%
- [ ] Clear, beautiful Rich UI
- [ ] Helpful validation error messages

---

## Release Plan

### Pre-Release Checklist

**Must Complete** (blocking):
- [ ] All P0 tasks complete (TMPL-001-006, TMPL-011)
- [ ] All templates created and tested (TMPL-008)
- [ ] Documentation complete (TMPL-010)
- [ ] Manual testing passed
- [ ] Zero critical bugs
- [ ] All tests passing

**Should Complete** (high priority):
- [ ] Template authoring guide
- [ ] All 5 servers with templates
- [ ] Performance benchmarks

**Could Defer** (v0.5.1):
- [ ] Additional servers beyond 5
- [ ] Template versioning system
- [ ] Community contribution process

### Release Timeline

**Day 1-2**: Infrastructure + CLI (4 tasks, 30-42h)
**Day 3-4**: Content (3 tasks, 24-30h)
**Day 5**: Documentation + Release (2 tasks, 12-18h)

**Ship Date**: End of Day 5 (v0.5.0)

**Post-Release** (v0.5.1, 1-2 weeks later):
- Add templates for 5-10 more servers
- Community contribution guidelines
- Template testing framework

---

## Comparison to Alternatives

### Why Not Full Interactive Wizard? (v0.6.0)

**Wizard Requirements** (from STATUS report):
1. Catalog schema extension (1 week)
2. Catalog enrichment for 8-12 servers (2-3 weeks)
3. Validation framework (1 week)
4. Interactive wizard implementation (2-3 weeks)
5. **Total**: 6-8 weeks

**Why Templates First**:
- ✅ Ship value NOW (1 week) instead of later (2 months)
- ✅ 80% of wizard benefit for 20% of effort
- ✅ Templates inform catalog metadata research (reuse work)
- ✅ Lower risk (additive, no schema changes)
- ✅ Can still ship wizard in v0.6.0 (not wasted effort)

### Templates vs Wizard Feature Comparison

| Aspect | Templates (v0.5.0) | Wizard (v0.6.0) |
|--------|-------------------|-----------------|
| **Effort** | 1 week | 6-8 weeks |
| **Schema Changes** | None | Catalog extension required |
| **Coverage** | 5-10 servers | 8-12 servers |
| **Customization** | Pre-defined scenarios | Fully dynamic |
| **Validation** | Basic (regex) | Advanced (connection testing) |
| **User Experience** | Good (guided) | Excellent (intelligent) |
| **Risk** | LOW | MEDIUM |
| **Value** | 80% | 100% |

**Strategic Decision**: Ship templates in v0.5.0, wizard in v0.6.0. Templates remain useful after wizard ships (quick setups vs custom configs).

---

## Long-Term Vision

### v0.5.0: Configuration Templates (1 week)
- **Goal**: Quick win, immediate user value
- **Effort**: 1 week
- **Deliverable**: 13 templates for 5 servers

### v0.5.1: Template Expansion (1-2 weeks later)
- **Goal**: More servers, community contributions
- **Effort**: 2-3 days
- **Deliverable**: 20+ templates for 10+ servers

### v0.6.0: Interactive Wizard (6-8 weeks total)
- **Prerequisites**:
  - Catalog schema extension (use template research)
  - Catalog enrichment (port template data)
- **Goal**: Full interactive configuration experience
- **Deliverable**: Intelligent wizard with connection testing

**Key Insight**: Templates are NOT wasted work. They:
1. Provide immediate user value (ship in 1 week)
2. Inform catalog metadata research (reuse for wizard)
3. Remain useful after wizard ships (quick setups)
4. De-risk wizard implementation (learn from template feedback)

---

## Dependencies & Prerequisites

### External Dependencies (None)

**No blocking dependencies**:
- ✅ No catalog schema changes needed
- ✅ No new libraries required (YAML, Rich, Pydantic already used)
- ✅ No MCP client changes needed
- ✅ No upstream server changes needed

### Internal Dependencies (Minimal)

**Builds on existing v0.4.0 architecture**:
- ✅ Uses existing `MCPManager.add_server()`
- ✅ Uses existing `ServerConfig` type
- ✅ Uses existing Rich console output
- ✅ Uses existing Click CLI framework

**Only new components**:
- Template models (new Pydantic models)
- Template manager (new module)
- Template files (new data files)

---

## Open Questions & Decisions

### Design Decisions (Resolved)

**Q1**: YAML vs JSON for template format?
- **Answer**: YAML (more readable, supports comments)

**Q2**: Should `--template` and `--env` be mutually exclusive?
- **Answer**: YES (prevent confusion, clear error message)

**Q3**: Should templates support conditional prompts?
- **Answer**: DEFER to v0.5.1 (YAGNI - keep simple for v0.5.0)

**Q4**: Should templates specify recommended scope?
- **Answer**: YES (template includes `scope`, user can override)

### Implementation Decisions (Resolved)

**Q5**: Where to store templates?
- **Answer**: `data/templates/{server_id}/{template_name}.yaml`

**Q6**: Should template manager be singleton or injected?
- **Answer**: DIP-compliant (factory functions, injectable for tests)

**Q7**: How to handle template versioning?
- **Answer**: DEFER to v0.5.1 (ship simple v1, iterate if needed)

---

## Communication Plan

### User-Facing Changes

**New CLI Commands**:
```bash
# List available templates for a server
mcpi add postgres --list-templates

# Install server with template
mcpi add postgres --template production
```

**Documentation Updates**:
- README.md: New "Configuration Templates" section
- CLAUDE.md: Template architecture documentation
- CHANGELOG.md: v0.5.0 release notes

### Migration Guide

**No migration needed** - Feature is purely additive:
- ✅ Existing `mcpi add` behavior unchanged
- ✅ No breaking changes to CLI
- ✅ No config file format changes
- ✅ Templates are optional (existing workflows work)

### Release Announcement

**v0.5.0 Highlights**:
1. **Configuration Templates**: Pre-tested configs for popular servers
2. **Quick Setup**: Install servers in 2-3 minutes (vs 15-30 minutes)
3. **Guided Prompts**: Interactive setup with validation
4. **13 Templates**: PostgreSQL, GitHub, Filesystem, Slack, Brave Search

---

## Appendix: Evidence from Evaluation

### Key Findings (from STATUS report)

**Problem Statement**:
> Users installing postgres, github, or slack servers face painful workflow:
> 1. Run `mcpi add postgres` (doesn't work)
> 2. Google "mcp postgres server setup"
> 3. Find README, copy examples
> 4. Edit JSON manually (syntax errors)
> 5. Debug connection issues
> 6. Time spent: 10-30 minutes

**Blocker Identified**:
> BLOCKER: Catalog lacks parameter metadata (env vars, types, defaults, validation).
> Cannot build interactive wizard without catalog schema extension (1 week) + enrichment (2-3 weeks).

**Alternative Recommended**:
> Configuration Templates (Alternative A):
> - Effort: 1 week (vs 6-8 weeks for wizard)
> - Value: 80% of wizard benefit for 20% of effort
> - Risk: LOW (no schema changes)
> - Recommendation: Ship templates first, defer wizard to v0.6.0

### Evaluation Confidence

**Architecture Feasibility**: 95%
- Plugin system supports configuration operations
- CLI framework has necessary UI components (Rich, Click)
- No architectural blockers

**Implementation Feasibility**: 95%
- Templates are simple (YAML + prompts)
- No complex validation required (regex sufficient)
- Additive feature (low regression risk)

**User Value**: 99%
- Addresses REAL pain point (evidence-based)
- Clear before/after improvement
- Measurable impact (time savings)

---

**Planning Status**: COMPLETE
**Recommendation**: APPROVE v0.5.0 with Configuration Templates
**Next Action**: Begin implementation (TMPL-001: Template Data Models)
**Timeline**: 5 days to release

---

*Generated by: Strategic Planning Agent*
*Based on: Ruthless Project Evaluation (2025-11-17)*
*Confidence: 95% (HIGH - evidence-based, low risk)*
