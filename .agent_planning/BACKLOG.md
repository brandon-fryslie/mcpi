# MCPI Project Backlog

**Last Updated**: 2025-10-28 06:35:09
**Status Source**: STATUS-2025-10-28-063053.md
**Current Completion**: 68% (functional core with test infrastructure issues)

This backlog contains all remaining work items for the MCPI project, organized by priority. For detailed implementation plans, see `PLAN-2025-10-28-063509.md`.

---

## P0: BLOCKING ISSUES (Must Fix Immediately)

### P0-1: Fix Broken Test Import Errors (19 files)
**Effort**: 3-5 days • **Status**: Not Started

19 of 60 test files fail at import due to references to deleted modules (`registry.manager`, `ServerInstallation`, `get_method_string`, etc.). This blocks all validation work.

**Action**: Categorize tests (delete obsolete vs update outdated), fix imports, align with current API.

---

### P0-2: Remove Dead Code Files
**Effort**: 1-2 days • **Status**: Not Started

Delete legacy CLI files wasting 75KB:
- `cli_old.py` (41KB)
- `cli_optimized.py` (8.6KB)
- `cli_original.py` (25KB)

**Action**: Delete files, verify no references, confirm CLI still works.

---

### P0-3: Verify Core Functionality with Manual Testing
**Effort**: 1-2 days • **Status**: Not Started
**Dependencies**: P0-1

Manual testing needed for `add`, `remove`, `status` commands. Tests fail but unclear if commands broken or tests wrong.

**Action**: Manually test with real servers, document actual behavior vs test expectations.

---

## P1: CRITICAL FOR PRODUCTION (MVP Blockers)

### P1-1: Fix or Verify Installation System
**Effort**: 3-5 days • **Status**: Not Started
**Dependencies**: P0-3

Installation commands (`add`, `remove`, `status`) have failing tests. Need to determine if implementation broken or tests wrong.

**Action**: Based on P0-3 findings, fix implementation and/or tests. Verify all installation methods work.

---

### P1-2: Update README to Remove Non-Existent Features
**Effort**: 1-2 days • **Status**: Not Started
**Dependencies**: P0-3, P1-1

README describes features that don't exist (`config init`, profile management) and doesn't document implemented features (`rescope`, `completion`).

**Action**: Remove false claims, document actual features, explain scope-based architecture.

---

### P1-3: Update PROJECT_SPEC.md to Match Implementation
**Effort**: 3-5 days • **Status**: Not Started
**Dependencies**: P0-3, P1-1

PROJECT_SPEC describes profile-based architecture but implementation uses scope-based plugin architecture.

**Action**: Rewrite spec to match actual implementation, document plugin system, remove outdated content.

---

### P1-4: Implement `mcpi categories` Command
**Effort**: 1-2 days • **Status**: Not Started

Simple discovery command to list all server categories from registry.

**Action**: Add command, format output with Rich table, write tests, update docs.

---

### P1-5: Implement `mcpi update` Command
**Effort**: 3-5 days • **Status**: Not Started
**Dependencies**: P1-1

Command to update MCP servers to latest version. Required by spec but not implemented.

**Action**: Implement version detection, update mechanism per installation method, preserve config.

---

### P1-6: Fix `mcpi status` Command
**Effort**: 1-2 days • **Status**: Not Started
**Dependencies**: P1-1

Command exists but tests fail. Unclear if functional.

**Action**: Verify functionality, fix implementation or tests, ensure shows accurate server states.

---

## P2: IMPORTANT (Quality and Completeness)

### P2-1: Refactor cli.py (1,381 LOC → modules)
**Effort**: 3-5 days • **Status**: Not Started
**Dependencies**: P0-1, P1-1

cli.py is a god object at 1,381 lines. Should be split into logical modules.

**Action**: Extract command groups to separate modules, max 500 LOC per file.

---

### P2-2: Add Integration Tests for Installation Workflows
**Effort**: 3-5 days • **Status**: Not Started
**Dependencies**: P1-1

Missing end-to-end tests for installation workflows (search → install → verify → remove).

**Action**: Write comprehensive integration tests for all installation methods.

---

### P2-3: Implement Advanced Features (doctor, backup, restore, sync)
**Effort**: 1-2 weeks • **Status**: Not Started
**Dependencies**: P1-1, P1-2, P1-3

Advanced features from spec not implemented. Nice-to-have for 1.0.

**Action**: Implement if time permits, otherwise defer to 1.1.

---

### P2-4: Achieve 80%+ Test Coverage
**Effort**: 3-5 days • **Status**: Not Started
**Dependencies**: P0-1, P1-1, P2-2

Cannot measure coverage due to broken tests. Target 80% meaningful coverage.

**Action**: Fix tests, add missing coverage, focus on functional tests.

---

## P3: NICE-TO-HAVE (Polish and Improvements)

### P3-1: Add CI/CD Pipeline
**Effort**: 1-2 days • **Status**: Not Started
**Dependencies**: P0-1

No automated testing on commits. Tests can break unnoticed.

**Action**: Add GitHub Actions workflow for tests, linting, type checking.

---

### P3-2: Implement Tab Completion for More Shells
**Effort**: 1-2 days • **Status**: Not Started

Current completion supports bash/zsh/fish. Could add PowerShell, Nushell.

**Action**: Add additional shell support if requested by users.

---

### P3-3: Create Architecture Documentation for Contributors
**Effort**: 1-2 days • **Status**: Not Started
**Dependencies**: P1-3

Plugin architecture not documented for contributors.

**Action**: Create ARCHITECTURE.md explaining plugin system, scope hierarchy, data flow.

---

### P3-4: Clean Remaining Technical Debt
**Effort**: 3-5 days • **Status**: Not Started
**Dependencies**: P0-1, P0-2

Prior STATUS mentioned 171+ broken references. After P0 cleanup, may still have references in comments/docs.

**Action**: Search for and clean all references to deleted modules.

---

## Completed Work (Recent)

### ✓ Rescope Feature
**Status**: COMPLETE (27/28 tests passing)

Implemented `mcpi rescope` command to move servers between scopes. Well-tested and functional.

---

### ✓ Tab Completion Feature
**Status**: COMPLETE (69/72 tests passing)

Implemented `mcpi completion` for bash/zsh/fish shells. Well-tested and functional.

---

### ✓ CUE Schema Validation
**Status**: COMPLETE

Added CUE schema validation for registry data. See `REGISTRY_VALIDATION_TESTING.md`.

---

## Work Items by Sprint

### Sprint 1: Test Infrastructure (Week 1)
- P0-1: Fix test imports
- P0-2: Remove dead code
- P0-3: Manual verification

### Sprint 2: Documentation (Week 2)
- P1-1: Fix installation system
- P1-2: Update README
- P1-3: Update PROJECT_SPEC

### Sprint 3: Core Features (Week 3)
- P1-4: categories command
- P1-5: update command
- P1-6: status command

### Sprint 4: Quality (Week 4)
- P2-1: Refactor CLI
- P2-2: Integration tests
- P2-4: 80% coverage
- P3-1: CI/CD

---

## Priority Definitions

**P0 (Blocking)**: Blocks all other work, must fix immediately
**P1 (Critical)**: Required for production/MVP, blocks release
**P2 (Important)**: Improves quality/completeness, should have for 1.0
**P3 (Nice-to-Have)**: Polish and improvements, can defer to 1.x

---

## Estimation Guidelines

**Small (1-2 days)**: Single feature, clear scope, low risk
**Medium (3-5 days)**: Multiple components, some unknowns, moderate complexity
**Large (1-2 weeks)**: Complex feature, many dependencies, high uncertainty
**XL (2+ weeks)**: Major initiative, multiple features, significant unknowns

---

## Success Metrics for 1.0

**Must Have**:
- [ ] 0 test import errors
- [ ] All core commands working (list, search, info, add, remove, status, update, categories)
- [ ] Installation system functional
- [ ] Documentation accurate (no false claims)
- [ ] 80%+ test coverage
- [ ] CI/CD running

**Should Have**:
- [ ] cli.py refactored into modules
- [ ] Integration tests for workflows
- [ ] PROJECT_SPEC aligned with reality

**Nice to Have**:
- [ ] Advanced features (doctor, backup, restore, sync)
- [ ] Additional shell completions
- [ ] Architecture documentation
- [ ] All technical debt cleaned

---

## Notes

- **rescope feature already implemented** - See old BACKLOG.md for original spec, implementation is complete
- **Focus on test infrastructure first** - Cannot validate anything with 31% of tests broken
- **Documentation critically misleading** - High priority to fix README
- **Architecture evolved beyond spec** - Scope system is better than profile system, spec needs update

---

For detailed implementation plan with acceptance criteria, technical notes, and dependency graphs, see `PLAN-2025-10-28-063509.md`.
