# Multi-Catalog Phase 1: CLI Integration - Planning Summary

**Generated**: 2025-11-17 05:00:00
**Project**: MCPI v0.3.0 → v0.4.0
**Feature**: Multi-Catalog Phase 1 MVP - CLI Integration
**Source STATUS**: STATUS-2025-11-17-040500.md
**Phase**: Implementation (Backend complete, CLI blocked)

---

## Executive Summary

### What We're Building
Complete CLI integration for multi-catalog feature, enabling users to:
- List available catalogs (`mcpi catalog list`)
- Explore catalog details (`mcpi catalog info`)
- Search specific catalogs (`mcpi search --catalog local`)
- Search all catalogs (`mcpi search --all-catalogs`)

### Current State
- ✅ **Backend**: 100% complete (CatalogManager, 25/25 tests passing)
- ❌ **CLI**: 0% complete (blocked by missing context integration)
- ❌ **User Value**: 0% (users cannot access features)

### What's Blocking
**CATALOG-003**: CLI Context Integration (1.5 hours)
- Missing: `get_catalog_manager(ctx)` function
- Impact: Blocks all CLI development
- **Start here first**

### Timeline
- **Total effort**: 23.5 hours (3-4 days)
- **Test status**: 46/78 passing (59%)
- **Completion**: 22% (2/9 tasks)

---

## Implementation Plan

### Detailed Planning Documents

**SPRINT Plan** (Day-by-day schedule):
- File: `SPRINT-CATALOG-CLI-2025-11-17-050000.md`
- Content: Hour-by-hour implementation schedule with code examples
- Use for: Daily execution

**BACKLOG** (Task tracking):
- File: `BACKLOG-CATALOG-PHASE1-2025-11-17-050000.md`
- Content: All 9 tasks with dependencies and acceptance criteria
- Use for: Task management

**QUICK START** (One-page reference):
- File: `QUICK-START-CATALOG-CLI-2025-11-17-050000.md`
- Content: Essential commands, patterns, and success checklist
- Use for: Quick reference during implementation

---

## 4-Day Schedule

### Day 1: Unblock CLI and First User Value (6 hours)

**Morning (1.5h): CATALOG-003 - CLI Context Integration**
- Add `get_catalog_manager(ctx)` to cli.py
- Update `get_catalog(ctx, catalog_name=None)` signature
- Add deprecation warning to catalog.py
- **Done when**: Context loads manager, backward compat works

**Afternoon (4h): CATALOG-004 - Catalog Command Group**
- Implement `mcpi catalog list`
- Implement `mcpi catalog info <name>`
- **Done when**: Users can list and explore catalogs

**Deliverable**: First user-visible multi-catalog feature

---

### Day 2: Multi-Catalog Search (8 hours)

**CATALOG-005: Add --catalog Flags to Existing Commands**
- Add `--catalog` and `--all-catalogs` to search (4h)
- Add `--catalog` to info and add (2h)
- Manual testing (2h)
- **Done when**: Multi-catalog search works

**Deliverable**: Full multi-catalog functionality

---

### Day 3: Fix All Tests (6 hours)

**Morning (4h): CATALOG-006 - CLI Integration Tests**
- Fix 24 failing CLI tests
- **Done when**: 27/27 CLI tests passing

**Afternoon (2h): CATALOG-007 - E2E Tests**
- Fix 8 failing E2E tests
- **Done when**: 26/26 E2E tests passing

**Deliverable**: 78/78 tests passing (100%)

---

### Day 4: Documentation and Release (6 hours)

**Morning (4h): CATALOG-008 - Documentation**
- Update CLAUDE.md (architecture)
- Update README.md (usage examples)
- Update CHANGELOG.md (v0.4.0 notes)
- **Done when**: Feature fully documented

**Afternoon (2h): CATALOG-009 - Manual Testing**
- Run manual test checklist
- Fix any bugs found
- Performance benchmarks
- **Done when**: Ready for v0.4.0 release

**Deliverable**: Production-ready feature

---

## Task Breakdown (9 Tasks)

### ✅ Complete (2/9)
1. CATALOG-001: CatalogManager (268 lines, 25/25 tests)
2. CATALOG-002: Unit tests (100% coverage, 0.28s)

### ❌ Remaining (7/9)
3. **CATALOG-003**: CLI context (1.5h) - **CRITICAL BLOCKER**
4. CATALOG-004: Catalog commands (4h)
5. CATALOG-005: --catalog flags (8h)
6. CATALOG-006: Fix CLI tests (4h)
7. CATALOG-007: Fix E2E tests (2h)
8. CATALOG-008: Documentation (4h)
9. CATALOG-009: Manual testing (2h)

**Total remaining**: 23.5 hours (3-4 days)

---

## Critical Path

```
START → CATALOG-003 (1.5h) → CATALOG-004 (4h) ─┐
                          └→ CATALOG-005 (8h) ─┴→ CATALOG-006 (4h)
                                                  → CATALOG-007 (2h)
                                                  → CATALOG-008 (4h)
                                                  → CATALOG-009 (2h)
                                                  → DONE
```

**Bottleneck**: CATALOG-003 blocks everything
**Parallelization**: After 003, can do 004 and 005 in parallel (saves ~4 hours)

---

## Success Criteria

### Implementation Complete When:
- [ ] 78/78 tests passing (100%)
- [ ] All 9 tasks complete
- [ ] `mcpi catalog list` shows both catalogs
- [ ] `mcpi search --all-catalogs` works
- [ ] Local catalog auto-initializes
- [ ] 100% backward compatibility
- [ ] Documentation complete
- [ ] Manual testing passes
- [ ] No performance regression

### Quality Gates:
- [ ] Code passes mypy, black, ruff
- [ ] Test execution < 10 seconds
- [ ] No regressions (752 existing tests)
- [ ] Performance: < 100ms (list), < 500ms (search), < 1s (all)

### User Value Delivered:
- [ ] Users can list available catalogs
- [ ] Users can explore catalog details
- [ ] Users can search specific catalogs
- [ ] Users can search all catalogs
- [ ] Users can add custom servers to local catalog
- [ ] Existing workflows continue to work unchanged

---

## Files to Modify

### Implementation (Total: ~410 lines)
- `src/mcpi/cli.py` - Add ~350 lines
  - Context helpers (50 lines)
  - Catalog commands (120 lines)
  - Flag updates (180 lines)
- `src/mcpi/registry/catalog.py` - Add 10 lines
  - Deprecation warning for `create_default_catalog()`

### Documentation (Total: ~180 lines)
- `CLAUDE.md` - Add ~100 lines (architecture)
- `README.md` - Add ~50 lines (usage)
- `CHANGELOG.md` - Add ~30 lines (release notes)

### Tests (Already Written!)
- `tests/test_catalog_manager.py` - 25/25 passing ✅
- `tests/test_cli_catalog_commands.py` - 3/27 passing (fix 24)
- `tests/test_multi_catalog_e2e.py` - 18/26 passing (fix 8)

---

## What Success Looks Like

### After CATALOG-003 (End of Hour 1.5)
```bash
# Test backward compatibility
$ mcpi search filesystem
# Works as before (uses official catalog)

# Context ready for catalog commands
# (No user-visible changes yet)
```

### After CATALOG-004 (End of Day 1)
```bash
$ mcpi catalog list
Available Catalogs
┏━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name    ┃ Type   ┃ Servers ┃ Description          ┃
┡━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ official│ builtin│ 42     │ Official MCP servers │
│ local   │ local  │ 0      │ Your custom servers  │
└─────────┴────────┴────────┴──────────────────────┘

$ mcpi catalog info official
OFFICIAL Catalog
Path: /path/to/data/catalog.json
Servers: 42
Categories: 8
```

### After CATALOG-005 (End of Day 2)
```bash
# Search specific catalog
$ mcpi search filesystem --catalog official
# Shows filesystem server from official catalog

# Search all catalogs
$ mcpi search filesystem --all-catalogs

OFFICIAL CATALOG
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Server ID  ┃ Description                    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ filesystem │ MCP filesystem operations      │
└────────────┴────────────────────────────────┘

LOCAL CATALOG
(no matches)
```

### After CATALOG-006/007 (End of Day 3)
```bash
$ pytest tests/test_catalog_manager.py tests/test_cli_catalog_commands.py tests/test_multi_catalog_e2e.py -v
====================== 78 passed in 1.2s ======================
```

### After CATALOG-008/009 (End of Day 4)
- All documentation updated
- Manual testing complete
- Performance benchmarks met
- Ready to tag and release v0.4.0

---

## Risk Management

### Technical Risks: LOW
- **Risk**: Backward compatibility breaks
  - **Mitigation**: Optional parameters, deprecation warnings
  - **Test**: Extensive backward compat tests already written
- **Risk**: Performance regression
  - **Mitigation**: Lazy loading, benchmarking
  - **Test**: Performance benchmarks in manual testing

### Schedule Risks: MEDIUM
- **Risk**: Implementation takes 4+ days
  - **Mitigation**: 23.5h estimate includes buffer
  - **Fallback**: Can defer documentation polish if needed
- **Risk**: Tests fail unexpectedly
  - **Mitigation**: Tests already written, debugging path clear
  - **Fallback**: Fix incrementally, extend timeline if needed

### User Impact Risks: LOW
- **Risk**: Users confused by catalogs
  - **Mitigation**: Clear documentation, intuitive CLI
  - **Test**: Manual testing validates UX
- **Risk**: Users lose custom servers
  - **Mitigation**: Local catalog auto-initialized, persists
  - **Test**: E2E tests verify persistence

**Overall Risk**: **LOW-MEDIUM** - Clear path, proven patterns, tests ready

---

## Next Actions

### Immediate (Right Now)
1. **Read SPRINT plan**: Review SPRINT-CATALOG-CLI-2025-11-17-050000.md
2. **Read QUICK START**: Review quick reference for patterns
3. **Start CATALOG-003**: Open src/mcpi/cli.py
4. **Set timer**: 1.5 hours for focused implementation

### First Task Checklist (CATALOG-003)
- [ ] Add `get_catalog_manager(ctx)` to cli.py
- [ ] Update `get_catalog(ctx, catalog_name=None)` signature
- [ ] Add deprecation warning to catalog.py
- [ ] Test manually: `mcpi search filesystem` (backward compat)
- [ ] Run quality checks: `black src/ && ruff check src/ && mypy src/`

### Daily Progress Tracking
Commit after each task:
```bash
# After CATALOG-003
git add . && git commit -m "feat(catalog): add CLI context integration for multi-catalog"

# After CATALOG-004
git add . && git commit -m "feat(catalog): add catalog list and info commands"

# After CATALOG-005
git add . && git commit -m "feat(catalog): add --catalog flags to search/info/add"

# After CATALOG-006/007
git add . && git commit -m "test(catalog): fix all CLI integration and E2E tests"

# After CATALOG-008/009
git add . && git commit -m "docs(catalog): complete multi-catalog documentation"
```

---

## Key Reference Information

### APIs to Use
```python
# Context helpers (add to cli.py)
manager = get_catalog_manager(ctx)
catalog = get_catalog(ctx, catalog_name=None)

# CatalogManager API (already implemented)
catalog = manager.get_catalog("official" | "local")
catalogs = manager.list_catalogs()  # List[CatalogInfo]
results = manager.search_all(query)  # List[(name, id, server)]
```

### Patterns to Follow
- **Lazy loading**: Only load catalogs when accessed
- **Error handling**: Use ClickException for user-facing errors
- **Rich output**: Follow existing table/panel patterns
- **Case-insensitive**: Catalog names accept any case
- **Backward compat**: Default to official catalog

### Manual Test Commands
```bash
# Essential tests
mcpi catalog list
mcpi catalog info official
mcpi search filesystem --all-catalogs
mcpi search filesystem --catalog local

# Backward compat
mcpi search filesystem  # Should use official by default

# Performance
time mcpi catalog list  # < 100ms
time mcpi search filesystem --all-catalogs  # < 1s
```

---

## Documentation References

**Detailed Planning**:
- `SPRINT-CATALOG-CLI-2025-11-17-050000.md` - Hour-by-hour schedule
- `BACKLOG-CATALOG-PHASE1-2025-11-17-050000.md` - Task tracking
- `QUICK-START-CATALOG-CLI-2025-11-17-050000.md` - Quick reference

**Status and Evaluation**:
- `STATUS-2025-11-17-040500.md` - Current state assessment
- `STATUS-CATALOG-PHASE1-EVALUATION-2025-11-17-023400.md` - Pre-implementation evaluation

**Project Documentation**:
- `CLAUDE.md` - Project architecture (to be updated)
- `README.md` - User documentation (to be updated)
- `CHANGELOG.md` - Release notes (to be updated)

---

## File Retention Status

This planning session created:
- ✅ SPRINT-CATALOG-CLI-2025-11-17-050000.md (kept - latest)
- ✅ BACKLOG-CATALOG-PHASE1-2025-11-17-050000.md (kept - latest)
- ✅ QUICK-START-CATALOG-CLI-2025-11-17-050000.md (kept - quick ref)
- ✅ PLANNING-SUMMARY-CATALOG-CLI-2025-11-17-050000.md (this file)

Archived old files (4-file retention policy):
- 🗄️ SPRINT-2025-11-16-150158.md → archive/2025-11/

Current active SPRINT files (4 kept):
1. SPRINT-CATALOG-CLI-2025-11-17-050000.md (latest - use this)
2. SPRINT-CATALOG-CLI-2025-11-17-033001.md
3. SPRINT-CATALOG-PHASE1-2025-11-17-022352.md
4. SPRINT-2025-11-16-161127.md

---

## Success Metrics Dashboard

### Completion Tracking
- **Tasks**: 2/9 complete (22%)
- **Tests**: 46/78 passing (59%)
- **Timeline**: 23.5 hours remaining (3-4 days)
- **Quality**: Backend 100%, CLI 0%

### Daily Targets
- **Day 1**: +2 tasks → 4/9 (44%)
- **Day 2**: +1 task → 5/9 (56%)
- **Day 3**: +2 tasks → 7/9 (78%), 78/78 tests passing
- **Day 4**: +2 tasks → 9/9 (100%), ready to ship

### Final Success
- [ ] 9/9 tasks complete (100%)
- [ ] 78/78 tests passing (100%)
- [ ] Documentation complete
- [ ] Manual testing passes
- [ ] Performance benchmarks met
- [ ] v0.4.0 tagged and ready

---

**PLANNING STATUS**: COMPLETE AND READY
**Next Action**: Begin CATALOG-003 (CLI Context Integration)
**Timeline**: 3-4 days to completion
**Confidence**: 95%

---

*Planning summary created by: Project Planner Agent*
*Date: 2025-11-17 05:00:00*
*Source: STATUS-2025-11-17-040500.md*
*For implementer: Start with CATALOG-003, follow sprint plan*
*Estimated completion: 2025-11-20 or 2025-11-21*
