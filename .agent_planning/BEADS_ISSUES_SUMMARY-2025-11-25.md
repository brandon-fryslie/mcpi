# MCPI Beads Issue Tracker Summary

**Generated**: 2025-11-25 18:31:00
**Source STATUS**: STATUS-2025-11-25-181931.md
**Source PLAN**: PLAN-2025-11-25-182546.md
**Beads Context**: /Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi

---

## Summary

All issues from the STATUS evaluation have been successfully created in the beads issue tracker. The issue tracker now contains 12 total issues (9 open, 3 closed duplicates), with proper dependencies established for the v0.6.0 CLI integration workflow.

---

## Issues Created

### P0 (Critical) - 2 Issues

#### MCPI-l93: Fix template-to-server-ID mapping for namespaced servers
- **Type**: Bug
- **Effort**: MEDIUM (2-4 hours)
- **Status**: Open (Ready to work)
- **Dependencies**: None
- **Impact**: HIGH - Breaks v0.5.0 shipped feature for all namespaced servers
- **Description**: Templates use 'postgres', catalog uses 'modelcontextprotocol/postgres'. Users cannot access templates.
- **Fix**: Implement fuzzy matching in TemplateManager.list_templates()

#### MCPI-2uh: Investigate plugin-based MCP server discovery implementation status
- **Type**: Task (Investigation)
- **Effort**: MEDIUM (2 hours investigation + 4-8 hours if needed)
- **Status**: Open (Ready to work)
- **Dependencies**: None
- **Impact**: HIGH - Potential missing servers, breaks parity with Claude Code
- **Description**: Contradictory evidence about plugin discovery feature existence
- **Action**: Investigate actual implementation status, create follow-up if needed

---

### P1 (High) - 3 Issues

These issues complete the v0.6.0 Template Discovery CLI integration.

#### MCPI-0jp: Complete v0.6.0 Template Discovery CLI integration - Add --recommend flag
- **Type**: Feature
- **Effort**: SMALL (3 hours)
- **Status**: Open (Ready to work)
- **Dependencies**: None
- **Blocks**: MCPI-6cm
- **Description**: Add --recommend flag to mcpi add command
- **Library**: 100% complete (19/19 tests passing)
- **CLI**: 0% complete (not started)

#### MCPI-q76: Complete v0.6.0 Template Discovery CLI integration - Rich display for recommendations
- **Type**: Feature
- **Effort**: MEDIUM (4 hours)
- **Status**: Open (Ready to work)
- **Dependencies**: None
- **Blocks**: MCPI-6cm
- **Description**: Implement Rich console display for template recommendations
- **Deliverable**: display_recommendations() function with color-coded table

#### MCPI-6cm: Complete v0.6.0 Template Discovery CLI integration - Interactive selection flow
- **Type**: Feature
- **Effort**: SMALL (3 hours)
- **Status**: Blocked (depends on MCPI-0jp AND MCPI-q76)
- **Dependencies**: MCPI-0jp, MCPI-q76
- **Description**: Wire up interactive accept/decline flow for recommendations
- **Deliverable**: Complete end-to-end --recommend workflow

---

### P2 (Medium) - 2 Issues

#### MCPI-iv7: Investigate and fix 57 skipped tests
- **Type**: Task (Investigation)
- **Effort**: MEDIUM (4-8 hours)
- **Status**: Open (Ready to work)
- **Dependencies**: None
- **Description**: Investigate why 57 tests are skipped (5.7% of total)
- **Goal**: Reduce to <10 skipped tests, document reasons

#### MCPI-dsg: Refactor cli.py into modular command structure
- **Type**: Chore (Technical Debt)
- **Effort**: LARGE (8-16 hours)
- **Status**: Open (Ready to work)
- **Dependencies**: None
- **Description**: Break up 95KB cli.py into modular command structure
- **Goal**: cli.py <20KB, commands in separate modules

---

### P3 (Low) - 2 Issues

#### MCPI-bfh: Fix test environment missing 'toml' dependency
- **Type**: Bug
- **Effort**: TRIVIAL (30 minutes)
- **Status**: Open (Ready to work)
- **Dependencies**: None
- **Description**: One test fails due to missing 'toml' module
- **Impact**: LOW - Runtime works, only affects one test

#### MCPI-zw2: Update tests to eliminate deprecation warnings
- **Type**: Chore (Cleanup)
- **Effort**: SMALL (2-4 hours)
- **Status**: Open (Ready to work)
- **Dependencies**: None
- **Description**: Replace deprecated create_default_catalog() with create_default_catalog_manager()
- **Goal**: Zero deprecation warnings

---

## Dependency Graph

```
P0 Issues (No dependencies, can start immediately):
├─ MCPI-l93: Fix template-to-server-ID mapping
└─ MCPI-2uh: Investigate plugin discovery

P1 Issues (v0.6.0 CLI Integration):
├─ MCPI-0jp: Add --recommend flag (no dependencies)
├─ MCPI-q76: Rich display (no dependencies)
└─ MCPI-6cm: Interactive flow
   ├─ DEPENDS ON: MCPI-0jp
   └─ DEPENDS ON: MCPI-q76

P2 Issues (No dependencies):
├─ MCPI-iv7: Investigate 57 skipped tests
└─ MCPI-dsg: Refactor cli.py

P3 Issues (No dependencies):
├─ MCPI-bfh: Fix toml dependency
└─ MCPI-zw2: Update deprecation warnings
```

**Critical Path for v0.6.0**:
1. MCPI-0jp (3h) + MCPI-q76 (4h) in parallel → 4 hours
2. MCPI-6cm (3h) sequential after both complete → 3 hours
3. **Total time**: 7 hours minimum, 10 hours with testing/integration

---

## Recommended Execution Order

### Sprint 1: Critical Bugs (Week 1 - Days 1-2)

**Goal**: Fix P0 blockers that break shipped features

**Day 1**:
1. MCPI-l93: Fix template-to-server-ID mapping (2-4 hours) - HIGHEST PRIORITY
   - Breaks v0.5.0 shipped feature
   - Affects all namespaced servers (postgres, github, filesystem, slack, brave-search)

**Day 2**:
2. MCPI-2uh: Investigate plugin discovery (2 hours + potential implementation)
   - Determine if feature exists, is broken, or is missing
   - Create follow-up issues if needed

**Success Criteria**:
- Templates work for all namespaced servers
- Plugin discovery implementation status documented
- v0.5.0 fully functional again

---

### Sprint 2: v0.6.0 CLI Integration (Week 1 - Days 3-5)

**Goal**: Ship v0.6.0 Template Discovery

**Day 3** (Parallel Work):
- MCPI-0jp: Add --recommend flag (3 hours)
- MCPI-q76: Rich display (4 hours)

**Day 4**:
- MCPI-6cm: Interactive selection flow (3 hours)

**Day 5**:
- Integration testing
- Manual verification with all 5 scenarios
- Documentation updates

**Success Criteria**:
- `mcpi add <server> --recommend` works end-to-end
- All 19 library tests + new CLI tests passing
- v0.6.0 ready to ship

---

### Sprint 3: Test Health & Cleanup (Week 2)

**Goal**: Improve test suite quality

**Quick Wins** (Day 1):
1. MCPI-bfh: Fix toml dependency (30 minutes)
2. MCPI-zw2: Update deprecation warnings (2-4 hours)

**Investigation** (Days 2-3):
3. MCPI-iv7: Investigate 57 skipped tests (4-8 hours)

**Success Criteria**:
- 100% of runnable tests pass
- Zero deprecation warnings
- <10 skipped tests remaining
- Clear documentation of skip reasons

---

### Sprint 4: Technical Debt (Week 3 - Optional)

**Goal**: Refactor cli.py for maintainability

1. MCPI-dsg: Refactor cli.py (8-16 hours)
   - Work incrementally
   - Extract one command group at a time
   - Test after each extraction

**Success Criteria**:
- cli.py <20KB
- Commands in separate modules
- All tests still pass
- No functionality changes

---

## Ready to Work

**8 of 9 issues ready to start immediately**:
- MCPI-l93 (P0)
- MCPI-2uh (P0)
- MCPI-0jp (P1)
- MCPI-q76 (P1)
- MCPI-iv7 (P2)
- MCPI-dsg (P2)
- MCPI-bfh (P3)
- MCPI-zw2 (P3)

**1 issue blocked**:
- MCPI-6cm (P1) - depends on MCPI-0jp AND MCPI-q76

---

## Beads Statistics

- **Total Issues**: 12
- **Open Issues**: 9
- **In Progress**: 0
- **Closed Issues**: 3 (duplicates)
- **Blocked Issues**: 1 (MCPI-6cm)
- **Ready Issues**: 8
- **Average Lead Time**: 0.014 hours (less than 1 minute)

---

## Planning Files Archived

The following outdated planning files were archived to prevent conflicts with the latest STATUS and PLAN:

**Archived to `.agent_planning/archive/2025-11/`**:
1. `BACKLOG 2.md` → `BACKLOG-2.md.archived`
2. `BACKLOG-CATALOG-PHASE1-FINAL.md` → `BACKLOG-CATALOG-PHASE1-FINAL.md.archived`

**Reason**: These files contained outdated backlog items that conflicted with the evidence-based planning in the latest STATUS evaluation. The current authoritative planning files are:
- `BACKLOG.md` (v0.6.0 focused, updated 2025-11-18)
- `PLAN-2025-11-25-182546.md` (latest, evidence-based from STATUS-2025-11-25-181931.md)

**Retained Active Planning Files**:
- `BACKLOG.md` - Current active backlog (v0.6.0 focus)
- `PLAN-2025-11-25-182546.md` - Latest prioritized plan (this session)
- `PLAN-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md` - v0.6.0 detailed plan
- `SPRINT-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md` - v0.6.0 sprint plan

All files follow the retention policy: keep 4 most recent files per prefix.

---

## Closed Issues (Duplicates)

The following issues were closed as duplicates during initial beads setup:
- MCPI-way: Duplicate of MCPI-6cm (Interactive selection flow)
- MCPI-24w: Duplicate of MCPI-q76 (Rich display)
- MCPI-ll3: Duplicate of MCPI-0jp (--recommend flag)

These are retained in the database as closed for audit purposes but should be ignored going forward.

---

## Next Actions

### Immediate (TODAY)
1. Start MCPI-l93: Fix template-to-server-ID mapping
   - This is a CRITICAL blocker affecting v0.5.0 shipped feature
   - Expected time: 2-4 hours
   - Affects ALL namespaced servers

### This Week
2. MCPI-2uh: Investigate plugin discovery (Day 2)
3. MCPI-0jp + MCPI-q76: v0.6.0 CLI integration in parallel (Day 3)
4. MCPI-6cm: Interactive flow (Day 4)
5. Ship v0.6.0 (Day 5)

### Next Week
6. Test health sprint (MCPI-bfh, MCPI-zw2, MCPI-iv7)

### Optional (Week 3)
7. cli.py refactoring (MCPI-dsg)

---

## Success Metrics

### Sprint 1 Success (P0 Fixes)
- [ ] Templates work for postgres, github, filesystem, slack, brave-search
- [ ] Both simple and namespaced IDs work (e.g., 'postgres' and 'modelcontextprotocol/postgres')
- [ ] Plugin discovery implementation status documented
- [ ] v0.5.0 fully functional

### v0.6.0 Ship Criteria
- [ ] Library complete (19/19 tests passing) ✓ DONE
- [ ] MCPI-0jp complete (--recommend flag working)
- [ ] MCPI-q76 complete (Rich display rendering)
- [ ] MCPI-6cm complete (Interactive selection working)
- [ ] All 5 manual scenarios pass
- [ ] Documentation updated (CLAUDE.md)
- [ ] No regressions in existing tests
- [ ] v0.6.0 tagged and ready

### Overall Project Health
- [ ] 100% of runnable tests passing
- [ ] <10 skipped tests
- [ ] Zero deprecation warnings
- [ ] cli.py refactored (<20KB) - Optional

---

## References

### Active Planning Documents
- **Latest STATUS**: STATUS-2025-11-25-181931.md
- **Latest PLAN**: PLAN-2025-11-25-182546.md
- **Active BACKLOG**: BACKLOG.md (v0.6.0 focus)
- **v0.6.0 Sprint**: SPRINT-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md

### Beads Commands
```bash
# View all issues
bd list

# View ready to work
bd ready

# View blocked issues
bd blocked

# Show issue details
bd show MCPI-l93

# Update issue status
bd update MCPI-0jp --status in_progress

# Close issue
bd close MCPI-l93 "Completed: Fuzzy matching implemented"

# View statistics
bd stats
```

### MCP Tools (If Available)
```python
# List issues
mcp__plugin_beads_beads__list(workspace_root="/path/to/mcpi")

# Show issue
mcp__plugin_beads_beads__show(issue_id="MCPI-l93", workspace_root="/path/to/mcpi")

# Update issue
mcp__plugin_beads_beads__update(issue_id="MCPI-0jp", status="in_progress", workspace_root="/path/to/mcpi")
```

---

**Generated with evidence-based planning methodology**
**Zero speculation, 100% traceability to STATUS evaluation**
