# Multi-Catalog Phase 1: CLI Integration Backlog

**Updated**: 2025-11-17 05:00:00
**Source STATUS**: STATUS-2025-11-17-040500.md
**Source SPRINT**: SPRINT-CATALOG-CLI-2025-11-17-050000.md
**Previous BACKLOG**: BACKLOG-CATALOG-PHASE1-2025-11-17-033001.md
**Phase**: 1 (MVP Foundation - v0.4.0)
**Current Progress**: 46/78 tests passing (59%)
**Overall Status**: CLI INTEGRATION PHASE

---

## Executive Summary

**Status**: **2/9 tasks complete (22%)** - Backend complete, CLI blocked

**What's Done** ✅:
- CATALOG-001: CatalogManager (268 lines, 100% quality) - COMPLETE
- CATALOG-002: Unit tests (25/25 passing, 100% coverage) - COMPLETE

**What's Blocked** ❌:
- All CLI features blocked by missing `get_catalog_manager(ctx)`
- 24/27 CLI integration tests failing
- 8/26 E2E tests failing
- Zero user-accessible functionality

**Critical Blocker**: CATALOG-003 (CLI Context Integration)
- **Effort**: 1.5 hours
- **Impact**: Unblocks all remaining work
- **Status**: NOT STARTED

**Timeline**:
- **Remaining effort**: 23.5 hours (3-4 days)
- **Original estimate**: 2-3 weeks for Phase 1
- **On track**: YES - backend ahead of schedule

---

## Task Status (2/9 Complete)

### ✅ COMPLETE (2 tasks)

#### CATALOG-001: CatalogManager Implementation
- **Status**: COMPLETE (2025-11-17)
- **Effort**: 2 days (as estimated)
- **Quality**: EXCELLENT
- **Evidence**: 268 lines, passes black/ruff/mypy, 25/25 tests passing

#### CATALOG-002: CatalogManager Unit Tests
- **Status**: COMPLETE (2025-11-17)
- **Effort**: 1 day (as estimated)
- **Quality**: EXCELLENT
- **Evidence**: 25/25 passing, 100% coverage, 0.28s runtime

---

### ❌ BLOCKED BY CATALOG-003 (6 tasks)

All tasks below blocked by missing CLI integration.

#### CATALOG-003: CLI Context Integration **[CRITICAL BLOCKER]**
- **Status**: NOT STARTED
- **Effort**: 1.5 hours (Small)
- **Priority**: P0 (blocks everything)
- **Dependencies**: None (CatalogManager ready)
- **Blocks**: CATALOG-004, 005, 006, 007, 008

**What it is**:
Add `get_catalog_manager(ctx)` function and update `get_catalog()` signature to accept optional catalog name.

**Files to modify**:
- `src/mcpi/cli.py` (~50 lines)
- `src/mcpi/registry/catalog.py` (~10 lines for deprecation)

**Acceptance Criteria**:
- [ ] `get_catalog_manager(ctx)` function exists and works
- [ ] `get_catalog(ctx)` returns official (backward compat)
- [ ] `get_catalog(ctx, "local")` returns local catalog
- [ ] `get_catalog(ctx, "unknown")` raises ClickException
- [ ] Deprecation warning added to `create_default_catalog()`
- [ ] Code passes black, ruff, mypy

**Expected outcome**: Unblocks all CLI development

---

#### CATALOG-004: Catalog Command Group
- **Status**: NOT STARTED
- **Effort**: 4 hours (Medium)
- **Priority**: P0 (user value)
- **Dependencies**: CATALOG-003
- **Blocked until**: get_catalog_manager() exists

**What it is**:
Implement `mcpi catalog list` and `mcpi catalog info <name>` commands.

**Commands after implementation**:
```bash
mcpi catalog list           # Shows table: name, type, servers, description
mcpi catalog info official  # Shows details: path, categories, samples
mcpi catalog info local     # Shows local catalog details
```

**Acceptance Criteria**:
- [ ] `mcpi catalog` command group exists
- [ ] `mcpi catalog list` shows Rich table with both catalogs
- [ ] `mcpi catalog info <name>` shows detailed information
- [ ] Help text includes examples
- [ ] Error handling for invalid catalog names

**Expected outcome**: First user-visible multi-catalog feature

---

#### CATALOG-005: Search/Info/Add --catalog Flags
- **Status**: NOT STARTED
- **Effort**: 8 hours (Medium)
- **Priority**: P0 (core functionality)
- **Dependencies**: CATALOG-003
- **Can parallelize**: Yes (with CATALOG-004 after 003)

**What it is**:
Add `--catalog` and `--all-catalogs` flags to existing commands.

**Commands after implementation**:
```bash
# Search
mcpi search filesystem                    # Official (default, backward compat)
mcpi search filesystem --catalog local    # Search local only
mcpi search filesystem --all-catalogs     # Search both, grouped

# Info
mcpi info filesystem --catalog local

# Add
mcpi add filesystem --catalog local
```

**Acceptance Criteria**:
- [ ] `search` has `--catalog` and `--all-catalogs` flags
- [ ] `info` has `--catalog` flag
- [ ] `add` has `--catalog` flag
- [ ] Flags mutually exclusive where appropriate
- [ ] Default behavior unchanged (uses official)
- [ ] `--all-catalogs` groups results by catalog

**Expected outcome**: Full multi-catalog search functionality

---

#### CATALOG-006: CLI Integration Tests (Fix)
- **Status**: WRITTEN, 3/27 PASSING
- **Effort**: 4 hours (fix tests)
- **Priority**: P0 (quality gate)
- **Dependencies**: CATALOG-003, 004, 005
- **Current state**: 24 tests failing (missing implementation)

**What it is**:
Fix 24 failing CLI integration tests by implementing missing commands.

**Test categories**:
- Catalog list tests (3 failing)
- Catalog info tests (4 failing)
- Search with catalog (8 failing)
- Info with catalog (3 failing)
- Add with catalog (2 failing)
- Backward compat (4 failing)
- Help text (3 passing ✅)

**Acceptance Criteria**:
- [ ] 27/27 tests passing
- [ ] No regressions in other tests
- [ ] Test execution < 5 seconds

**Expected outcome**: All CLI features verified by tests

---

#### CATALOG-007: E2E Tests (Fix)
- **Status**: WRITTEN, 18/26 PASSING
- **Effort**: 2 hours (remove guards, fix 8 tests)
- **Priority**: P0 (quality gate)
- **Dependencies**: CATALOG-006
- **Current state**: 8 tests failing (awaiting CLI)

**What it is**:
Fix 8 failing E2E tests that validate complete user workflows.

**Acceptance Criteria**:
- [ ] 26/26 tests passing
- [ ] All backward compatibility tests passing
- [ ] Workflow tests verify end-to-end functionality

**Expected outcome**: Complete workflows verified

---

#### CATALOG-008: Documentation
- **Status**: NOT STARTED
- **Effort**: 4 hours (Medium)
- **Priority**: P1 (release requirement)
- **Dependencies**: CATALOG-007 (all tests passing)

**What it is**:
Update documentation for multi-catalog feature.

**Files to update**:
- `CLAUDE.md` - Architecture section
- `README.md` - Usage examples
- `CHANGELOG.md` - v0.4.0 release notes

**Acceptance Criteria**:
- [ ] CLAUDE.md updated with multi-catalog architecture
- [ ] README.md has usage examples
- [ ] CHANGELOG.md has v0.4.0 section
- [ ] Migration guide complete
- [ ] CLI help text verified

**Expected outcome**: Feature fully documented

---

#### CATALOG-009: Manual Testing and Bug Fixes
- **Status**: NOT STARTED
- **Effort**: 2 hours (Small)
- **Priority**: P1 (release requirement)
- **Dependencies**: CATALOG-008

**What it is**:
Manual end-to-end testing and bug fixes before release.

**Test scenarios**:
- Fresh install workflow
- Catalog list and info commands
- Search operations (default, --catalog, --all-catalogs)
- Local catalog workflow
- Backward compatibility
- Error handling
- Performance benchmarks

**Acceptance Criteria**:
- [ ] All manual tests pass
- [ ] All bugs fixed
- [ ] Performance benchmarks met (<100ms, <500ms, <1s)
- [ ] Backward compatibility verified
- [ ] Ready for v0.4.0 release

**Expected outcome**: Production-ready feature

---

## Dependency Graph

```
CATALOG-001 (CatalogManager) ✅ COMPLETE
  │
  └─> CATALOG-002 (Unit Tests) ✅ COMPLETE
       │
       └─> CATALOG-003 (CLI Context) ❌ NOT STARTED ← **START HERE** (1.5h)
            │
            ├─> CATALOG-004 (catalog commands) ❌ (4h, parallel)
            │
            ├─> CATALOG-005 (--catalog flags) ❌ (8h, parallel)
            │
            └─> [After 004 & 005 complete]
                 │
                 └─> CATALOG-006 (Fix CLI tests) ❌ (4h)
                      │
                      └─> CATALOG-007 (Fix E2E tests) ❌ (2h)
                           │
                           └─> CATALOG-008 (Documentation) ❌ (4h)
                                │
                                └─> CATALOG-009 (Manual test) ❌ (2h)
```

**Critical Path**: 003 → 005 → 006 → 007 → 008 → 009 = 21.5 hours
**With parallelization**: 003 → (004 || 005) → 006 → 007 → 008 → 009 = 21.5 hours

**Total Effort**: 23.5 hours (3-4 days)

---

## Implementation Schedule

See **SPRINT-CATALOG-CLI-2025-11-17-050000.md** for detailed day-by-day schedule.

**Quick summary**:
- **Day 1**: CATALOG-003 + CATALOG-004 (5.5 hours)
- **Day 2**: CATALOG-005 (8 hours)
- **Day 3**: CATALOG-006 + CATALOG-007 (6 hours)
- **Day 4**: CATALOG-008 + CATALOG-009 (6 hours)

---

## Success Criteria

### Implementation Complete When:
- [ ] 78/78 tests passing (100%)
- [ ] All 9 tasks complete
- [ ] Users can list/explore catalogs
- [ ] Users can search specific catalogs
- [ ] Users can search all catalogs
- [ ] 100% backward compatibility
- [ ] Documentation complete
- [ ] Ready for v0.4.0 release

### Quality Gates:
- [ ] Code passes mypy, black, ruff
- [ ] Test execution < 10 seconds
- [ ] No regressions (752 existing tests)
- [ ] Performance: no degradation vs v0.3.0

### User Value:
- [ ] `mcpi catalog list` works
- [ ] `mcpi search --all-catalogs` works
- [ ] Local catalog auto-initializes
- [ ] Existing workflows unchanged

---

## Risk Assessment

**Technical Risks**: LOW
- Clear implementation path
- Proven patterns (lazy loading, factory functions)
- Tests already written

**Schedule Risks**: MEDIUM
- Could take 3-4 days instead of 2-3
- Bug fixes may add time
- Mitigation: Built-in buffer (23.5h estimate)

**User Impact Risks**: LOW
- 100% backward compatible design
- Optional new features
- Clear documentation

**Overall Risk**: **LOW-MEDIUM**

---

## Next Actions

### Immediate
1. **Review SPRINT plan**: Read SPRINT-CATALOG-CLI-2025-11-17-050000.md
2. **Start CATALOG-003**: Open src/mcpi/cli.py
3. **Set timer**: 1.5 hours for focused work

### Day 1 Checklist
- [ ] Add `get_catalog_manager(ctx)` to cli.py
- [ ] Update `get_catalog(ctx, catalog_name=None)` signature
- [ ] Add deprecation warning to catalog.py
- [ ] Test manually: `mcpi search filesystem`
- [ ] Run quality checks: black, ruff, mypy
- [ ] Implement `mcpi catalog list` command
- [ ] Implement `mcpi catalog info` command
- [ ] Test manually: verify tables display correctly

### Progress Tracking
Commit after each task:
- "feat(catalog): add CLI context integration"
- "feat(catalog): add catalog list and info commands"
- "feat(catalog): add --catalog flags to search/info/add"
- "test(catalog): fix CLI integration and E2E tests"
- "docs(catalog): complete multi-catalog documentation"

---

**BACKLOG STATUS**: READY FOR IMPLEMENTATION
**Completion**: 22% (2/9 tasks)
**Next Task**: CATALOG-003 (CLI Context Integration)
**Estimated Completion**: 23.5 hours (3-4 days)
**Confidence**: 95%

---

*Backlog created by: Project Planner Agent*
*Date: 2025-11-17 05:00:00*
*Source: STATUS-2025-11-17-040500.md*
*Sprint Plan: SPRINT-CATALOG-CLI-2025-11-17-050000.md*
