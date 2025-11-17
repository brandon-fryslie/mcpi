# Sprint: Multi-Catalog CLI Implementation

**Sprint Start**: 2025-11-17
**Sprint Duration**: 10 days (2 weeks)
**Sprint Goal**: Complete Multi-Catalog Phase 1 - Make feature usable from CLI
**Source**: BACKLOG-CATALOG-PHASE1-2025-11-17-033001.md, STATUS-2025-11-17-033001.md
**Phase**: 1 (MVP Foundation - v0.4.0)

---

## Sprint Objective

**Primary Goal**: Implement CLI integration for multi-catalog feature, making it fully usable from command line

**Success Criteria**:
- [ ] All CLI commands support --catalog flag
- [ ] New `mcpi catalog` command group working
- [ ] All integration tests passing (27/27)
- [ ] All E2E tests passing (26/26)
- [ ] All regression tests fixed (805/805 passing)
- [ ] Documentation complete
- [ ] Feature ready for v0.4.0 release

**Current Status**: 35% complete (core done, CLI missing)

---

## Sprint Backlog

### Week 1: CLI Implementation (Days 1-5)

#### Day 1: Unblock CLI Work

**Task**: CATALOG-003 - CLI Context Integration
**Assignee**: Implementation team
**Status**: NOT STARTED
**Effort**: 1 day
**Priority**: P0 (CRITICAL BLOCKER)

**Goal**: Add catalog manager to CLI context, unblock all CLI work

**Sub-tasks**:
1. [ ] Add `get_catalog_manager(ctx)` function to `cli.py`
   - Lazy initialization
   - Store in ctx.obj
   - Return CatalogManager instance

2. [ ] Update `get_catalog(ctx, catalog_name=None)` function
   - Accept optional catalog_name parameter
   - Default to official catalog (backward compat)
   - Case-insensitive lookup
   - Error handling for unknown catalogs

3. [ ] Add deprecation warning to `create_default_catalog()`
   - Use DeprecationWarning category
   - stacklevel=2
   - Clear message pointing to new function

4. [ ] Update imports in cli.py
   - Import create_default_catalog_manager
   - Import CatalogManager type

5. [ ] Verify backward compatibility
   - Run existing CLI commands
   - Ensure no breaking changes

**Acceptance Criteria**:
- [ ] `get_catalog_manager(ctx)` returns CatalogManager
- [ ] `get_catalog(ctx)` returns official catalog (backward compat)
- [ ] `get_catalog(ctx, "local")` returns local catalog
- [ ] `get_catalog(ctx, "OFFICIAL")` works (case-insensitive)
- [ ] Unknown catalog raises ClickException
- [ ] Deprecation warning shows for old factory
- [ ] All existing commands work unchanged

**Testing**:
- [ ] Unit test: test_get_catalog_manager()
- [ ] Unit test: test_get_catalog_default()
- [ ] Unit test: test_get_catalog_with_name()
- [ ] Unit test: test_get_catalog_case_insensitive()
- [ ] Unit test: test_get_catalog_unknown()
- [ ] Integration test: Verify backward compat

**Blockers**: None (depends on CATALOG-001 which is complete)
**Blocked by this**: CATALOG-004, CATALOG-005, CATALOG-006

---

#### Days 2-3: Catalog Flags (Parallel Work Possible)

**Task**: CATALOG-004 - Add --catalog Flag to search Command
**Assignee**: Implementation team
**Status**: NOT STARTED
**Effort**: 1 day
**Priority**: P0 (Critical)

**Goal**: Enable catalog selection in search command

**Sub-tasks**:
1. [ ] Add `--catalog` option to search command
   - Type: click.Choice(["official", "local"], case_sensitive=False)
   - Help text with examples

2. [ ] Add `--all-catalogs` flag to search command
   - Boolean flag
   - Help text

3. [ ] Make --catalog and --all-catalogs mutually exclusive
   - Error if both provided

4. [ ] Implement single catalog search
   - Get catalog by name
   - Call catalog.search_servers(query)
   - Display results (existing Rich table)

5. [ ] Implement all-catalogs search
   - Call manager.search_all(query)
   - Group results by catalog name
   - Display with catalog headers

**Acceptance Criteria**:
- [ ] `mcpi search <query>` works (backward compat)
- [ ] `mcpi search <query> --catalog official` works
- [ ] `mcpi search <query> --catalog local` works
- [ ] `mcpi search <query> --all-catalogs` works
- [ ] Results grouped by catalog in --all-catalogs mode
- [ ] Error if both flags used
- [ ] Help text clear and complete

**Testing**:
- [ ] 8 integration tests in test_cli_catalog_commands.py
- [ ] Manual test: search with each flag

**Blockers**: CATALOG-003
**Parallel with**: CATALOG-005

---

**Task**: CATALOG-005 - Add --catalog Flag to info/add Commands
**Assignee**: Implementation team
**Status**: NOT STARTED
**Effort**: 1 day
**Priority**: P0 (Critical)

**Goal**: Enable catalog selection in info and add commands

**Sub-tasks**:
1. [ ] Add `--catalog` option to info command
   - Type: click.Choice(["official", "local"], case_sensitive=False)
   - Default: search official first (backward compat)
   - Help text

2. [ ] Add `--catalog` option to add command
   - Type: click.Choice(["official", "local"], case_sensitive=False)
   - Default: official
   - Help text

3. [ ] Update info command logic
   - Use get_catalog(ctx, catalog_name)
   - Display server info

4. [ ] Update add command logic
   - Use get_catalog(ctx, catalog_name)
   - Add server from specified catalog

**Acceptance Criteria**:
- [ ] `mcpi info <server>` searches official (backward compat)
- [ ] `mcpi info <server> --catalog local` searches local
- [ ] `mcpi add <server>` adds from official (backward compat)
- [ ] `mcpi add <server> --catalog local` adds from local
- [ ] Help text clear
- [ ] Error handling for unknown catalog

**Testing**:
- [ ] 5 integration tests in test_cli_catalog_commands.py
- [ ] Manual test: info/add with each catalog

**Blockers**: CATALOG-003
**Parallel with**: CATALOG-004

---

#### Days 4-5: New catalog Command Group

**Task**: CATALOG-006 - Implement catalog Subcommand Group
**Assignee**: Implementation team
**Status**: NOT STARTED
**Effort**: 2 days
**Priority**: P0 (Critical)

**Goal**: Add new `mcpi catalog` command group

**Sub-tasks**:
1. [ ] Create catalog command group
   - @cli.group()
   - Docstring
   - Help text

2. [ ] Implement `catalog list` command
   - Get manager.list_catalogs()
   - Create Rich table (name, type, servers, description)
   - Display table
   - Color scheme: cyan names, green counts

3. [ ] Implement `catalog info` command
   - Get catalog by name
   - Display metadata (path, server count)
   - Show top 10 categories by count
   - Show first 5 servers as samples
   - Use Rich panels/tables

4. [ ] Add comprehensive help text
   - Examples for each command
   - Clear descriptions

5. [ ] Error handling
   - Unknown catalog name
   - Missing catalog file
   - Corrupt catalog data

**Acceptance Criteria**:
- [ ] `mcpi catalog` shows help
- [ ] `mcpi catalog list` shows Rich table with 2 rows
- [ ] Table columns: name, type, servers, description
- [ ] `mcpi catalog info official` shows detailed info
- [ ] `mcpi catalog info local` shows local catalog info
- [ ] `mcpi catalog info unknown` shows error (exit code 1)
- [ ] Help text includes examples
- [ ] Output follows CLI style (colors, formatting)
- [ ] Fast execution (<100ms list, <200ms info)

**Testing**:
- [ ] 7 integration tests in test_cli_catalog_commands.py
- [ ] Manual test: all catalog commands

**Blockers**: CATALOG-003
**Can parallelize**: Partially (Day 4 parallel with 004/005 testing)

---

#### Day 5: Fix E2E Test Guards

**Task**: CATALOG-008 - Remove NotImplementedError Guards
**Assignee**: Implementation team
**Status**: PARTIAL (9/26 passing)
**Effort**: 1 day
**Priority**: P0 (Critical)

**Goal**: Fix 8 E2E tests failing due to NotImplementedError guards

**Sub-tasks**:
1. [ ] Remove NotImplementedError guards from 8 tests
   - test_fresh_install_creates_local_catalog
   - test_local_catalog_auto_initialization
   - test_local_catalog_empty_on_first_run
   - test_official_catalog_always_available
   - test_local_catalog_persistence
   - test_multiple_sessions_accumulate
   - test_permission_error_graceful_degradation
   - test_corrupted_local_catalog_handled

2. [ ] Verify test logic works with real implementation
   - Update assertions if needed
   - Fix any test bugs discovered

3. [ ] Fix CLI integration test (needs CLI complete)
   - test_catalog_operations_visible_to_claude_cli

**Acceptance Criteria**:
- [ ] All 8 stub tests pass (remove guards)
- [ ] 1 CLI integration test passes (needs 003-006)
- [ ] Total: 26/26 E2E tests passing
- [ ] No new failures introduced

**Testing**:
- [ ] Run pytest tests/test_multi_catalog_e2e.py -v
- [ ] Verify all 26 tests pass

**Blockers**: CATALOG-003, 004, 005, 006 (for CLI test)
**Depends on**: CLI implementation complete

---

### Week 2: Testing, Documentation, Release (Days 6-10)

#### Days 6-7: Fix Regressions

**Task**: CATALOG-009 - Update Existing Tests
**Assignee**: Implementation team
**Status**: NOT STARTED (45 failures)
**Effort**: 2 days
**Priority**: P1 (High)

**Goal**: Fix 45 regression failures, get to 100% test pass rate

**Strategy**:
1. **Identify failure categories** (1-2 hours)
   - Run full test suite
   - Categorize failures by root cause
   - Create fix plan

2. **Fix deprecation warning failures** (4-6 hours)
   - Option 1: Suppress warnings in tests
   - Option 2: Update to new pattern
   - Prefer Option 1 for minimal churn

3. **Fix manager/harness integration failures** (4-6 hours)
   - Update test harnesses to use CatalogManager
   - Fix catalog path references

4. **Verify no new failures** (2 hours)
   - Run full test suite
   - Fix any new issues discovered

**Sub-tasks by Day**:

**Day 6**:
1. [ ] Run full test suite, categorize 45 failures
2. [ ] Fix deprecation warning failures (estimated 20-25 tests)
3. [ ] Test: Run affected test files, verify fixes

**Day 7**:
4. [ ] Fix manager/harness integration failures (estimated 15-20 tests)
5. [ ] Fix any remaining miscellaneous failures (estimated 5 tests)
6. [ ] Run full test suite, verify 805/805 passing
7. [ ] Check execution time (no performance regression)

**Acceptance Criteria**:
- [ ] All 48 test files reviewed
- [ ] All 45 regression failures fixed
- [ ] 805/805 tests passing (100%)
- [ ] No new failures introduced
- [ ] Test execution time unchanged (<120s for full suite)
- [ ] Deprecation warnings handled consistently

**Testing**:
- [ ] Run full test suite: pytest -v
- [ ] Run with coverage: pytest --cov=src/mcpi
- [ ] Verify coverage still 100% for new code

**Blockers**: CATALOG-008 (should be complete)

---

#### Days 8-9: Documentation

**Task**: CATALOG-010 - Update Documentation
**Assignee**: Implementation team
**Status**: NOT STARTED
**Effort**: 2 days
**Priority**: P1 (High)

**Goal**: Complete documentation for multi-catalog feature

**Sub-tasks by Day**:

**Day 8 - Technical Documentation**:
1. [ ] Update CLAUDE.md
   - [ ] Add "Multi-Catalog System" section to Architecture
   - [ ] Explain CatalogManager design
   - [ ] Show factory function usage (old vs. new)
   - [ ] Update "Server Catalog System" section
   - [ ] Add backward compatibility notes
   - [ ] Update testing strategy with multi-catalog patterns

2. [ ] Update development commands examples
   - [ ] Add catalog search examples
   - [ ] Add catalog list/info examples
   - [ ] Show --catalog flag usage

**Day 9 - User Documentation and Release Notes**:
3. [ ] Update README.md
   - [ ] Add "Multiple Catalogs" section
   - [ ] Show `mcpi catalog list` example with output
   - [ ] Show `mcpi catalog info` example with output
   - [ ] Show `mcpi search --catalog` examples
   - [ ] Show `mcpi search --all-catalogs` example
   - [ ] Document local catalog location
   - [ ] Add FAQ: "What are catalogs?", "How do I use local catalog?"

4. [ ] Update CHANGELOG.md
   - [ ] Add v0.4.0 section header
   - [ ] List new features (multi-catalog support)
   - [ ] List new commands (catalog list/info)
   - [ ] List new flags (--catalog, --all-catalogs)
   - [ ] List deprecations (create_default_catalog())
   - [ ] Add migration guide (emphasize: no action needed)
   - [ ] Note: 100% backward compatible

5. [ ] Verify CLI help text
   - [ ] `mcpi --help` shows catalog group
   - [ ] `mcpi catalog --help` shows subcommands
   - [ ] `mcpi search --help` shows catalog flags
   - [ ] `mcpi info --help` shows catalog flag
   - [ ] `mcpi add --help` shows catalog flag
   - [ ] All examples are clear

**Acceptance Criteria**:
- [ ] CLAUDE.md has complete multi-catalog architecture section
- [ ] README.md has user-friendly examples
- [ ] CHANGELOG.md has complete v0.4.0 release notes
- [ ] Migration guide clear: "backward compatible, no action needed"
- [ ] All CLI help text verified
- [ ] Examples tested and work correctly
- [ ] Documentation reviewed for accuracy

**Testing**:
- [ ] Manual verification: All examples work
- [ ] Manual verification: Help text matches docs
- [ ] Manual verification: No broken links or examples

**Blockers**: CATALOG-009 (tests should be passing)

---

#### Day 10: Manual Testing and Release Prep

**Task**: CATALOG-011 - Manual Testing and Bug Fixes
**Assignee**: Implementation team
**Status**: NOT STARTED
**Effort**: 1 day
**Priority**: P1 (High)

**Goal**: Final verification before v0.4.0 release

**Manual Test Checklist**:

**Fresh Install Tests** (1 hour):
- [ ] Clean up ~/.mcpi/catalogs/ if exists
- [ ] Run `mcpi catalog list`
- [ ] Verify local catalog created at ~/.mcpi/catalogs/local/catalog.json
- [ ] Verify local catalog is empty initially

**Catalog Commands** (1 hour):
- [ ] `mcpi catalog list` - verify shows 2 rows
- [ ] `mcpi catalog info official` - verify shows correct stats
- [ ] `mcpi catalog info local` - verify shows 0 servers initially
- [ ] `mcpi catalog info unknown` - verify error message

**Search Commands** (1 hour):
- [ ] `mcpi search filesystem` - searches official (default)
- [ ] `mcpi search filesystem --catalog official` - same result
- [ ] `mcpi search filesystem --catalog local` - empty results
- [ ] `mcpi search filesystem --all-catalogs` - shows both, grouped
- [ ] Verify case-insensitive: `mcpi search filesystem --catalog OFFICIAL`

**Info/Add Commands** (1 hour):
- [ ] `mcpi info filesystem` - shows details from official
- [ ] `mcpi info filesystem --catalog local` - not found
- [ ] `mcpi add <server>` - adds from official (verify with client)

**Local Catalog Workflow** (1 hour):
- [ ] Manually add custom server to ~/.mcpi/catalogs/local/catalog.json
- [ ] `mcpi search <custom-name>` - not found (official only)
- [ ] `mcpi search <custom-name> --catalog local` - found
- [ ] `mcpi search <custom-name> --all-catalogs` - found in local section
- [ ] `mcpi info <custom-name> --catalog local` - shows details
- [ ] Restart terminal
- [ ] `mcpi search <custom-name> --catalog local` - still found (persistence)

**Backward Compatibility** (30 min):
- [ ] Old code patterns work (create_default_catalog())
- [ ] Deprecation warning shown
- [ ] No breaking changes in CLI

**Error Handling** (30 min):
- [ ] Unknown catalog name - clear error
- [ ] Missing catalog file - graceful handling
- [ ] Corrupt catalog JSON - clear error message
- [ ] Permission errors - graceful degradation

**Performance Benchmarks** (30 min):
- [ ] `time mcpi catalog list` - <100ms
- [ ] `time mcpi search filesystem` - <500ms (compare to v0.3.0)
- [ ] `time mcpi search filesystem --all-catalogs` - <1000ms
- [ ] No noticeable slowdowns vs. v0.3.0

**Bug Fix Process**:
1. [ ] Document all bugs discovered
2. [ ] Create regression test for each bug
3. [ ] Fix bug
4. [ ] Verify fix works
5. [ ] Run full test suite (ensure no regressions)
6. [ ] Re-test manually

**Acceptance Criteria**:
- [ ] All manual tests pass
- [ ] All bugs discovered are fixed
- [ ] Regression tests added for bugs
- [ ] Performance benchmarks met
- [ ] No regressions vs. v0.3.0
- [ ] Feature ready for v0.4.0 release tag

**Final Checklist**:
- [ ] All automated tests passing (805/805)
- [ ] All manual tests passing
- [ ] Documentation complete
- [ ] CHANGELOG.md ready
- [ ] No known bugs
- [ ] Performance benchmarks met
- [ ] Ready to tag v0.4.0

**Blockers**: CATALOG-010 (docs should be complete)

---

## Sprint Summary by Day

| Day | Tasks | Hours | Focus | Deliverable |
|-----|-------|-------|-------|-------------|
| 1 | CATALOG-003 | 6-8 | CLI Context | CLI unblocked |
| 2 | CATALOG-004, 005 | 6-8 | Catalog flags | Search/info/add with --catalog |
| 3 | CATALOG-004, 005 cont. | 6-8 | Testing flags | Integration tests passing |
| 4 | CATALOG-006 | 6-8 | Catalog commands | catalog list/info working |
| 5 | CATALOG-006, 008 | 6-8 | Finish + E2E fixes | All new tests passing |
| 6 | CATALOG-009 | 6-8 | Fix regressions (part 1) | 50% regressions fixed |
| 7 | CATALOG-009 | 6-8 | Fix regressions (part 2) | 100% tests passing |
| 8 | CATALOG-010 | 6-8 | Technical docs | CLAUDE.md updated |
| 9 | CATALOG-010 | 6-8 | User docs + changelog | README, CHANGELOG updated |
| 10 | CATALOG-011 | 6-8 | Manual testing | v0.4.0 ready to ship |

**Total Effort**: 60-80 hours (10 days at 6-8 hours/day)

---

## Daily Standup Format

**Each day, report**:

1. **What did I complete yesterday?**
   - Tasks finished
   - Tests passing
   - Blockers resolved

2. **What am I working on today?**
   - Current task
   - Sub-tasks planned
   - Expected completion time

3. **Are there any blockers?**
   - Technical issues
   - Unclear requirements
   - External dependencies

4. **Test status**:
   - New tests passing/failing
   - Regression test status
   - Overall pass rate

---

## Definition of Done

**Task is complete when**:
- [ ] Code written and passes all quality checks (black, ruff, mypy)
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests passing (if applicable)
- [ ] No regressions introduced
- [ ] Code reviewed (self-review minimum)
- [ ] Documentation updated (inline comments, docstrings)

**Sprint is complete when**:
- [ ] All 11 tasks complete (CATALOG-001 through CATALOG-011)
- [ ] 805/805 tests passing (100%)
- [ ] All manual tests pass
- [ ] Documentation complete (CLAUDE.md, README.md, CHANGELOG.md)
- [ ] Performance benchmarks met
- [ ] v0.4.0 ready to tag and ship

---

## Risk Management

### High Priority Risks

**Risk 1**: CLI integration takes longer than 1 day (CATALOG-003)
- **Probability**: LOW
- **Impact**: HIGH (blocks all CLI work)
- **Mitigation**: Clear implementation plan, simple changes
- **Contingency**: Extend to 1.5 days if needed

**Risk 2**: Regression fixes take longer than 2 days (CATALOG-009)
- **Probability**: MEDIUM
- **Impact**: MEDIUM (delays release)
- **Mitigation**: Categorize failures first, fix systematically
- **Contingency**: Extend to 3 days if needed, deprioritize low-impact tests

**Risk 3**: Manual testing discovers major bugs (CATALOG-011)
- **Probability**: LOW
- **Impact**: HIGH (delays release)
- **Mitigation**: Thorough automated testing, incremental verification
- **Contingency**: Add 1-2 days for bug fixes, re-run manual tests

### Medium Priority Risks

**Risk 4**: Documentation takes longer than 2 days (CATALOG-010)
- **Probability**: LOW
- **Impact**: LOW (can extend)
- **Mitigation**: Clear structure, examples already planned
- **Contingency**: Parallelize with manual testing if needed

**Risk 5**: E2E test fixes reveal implementation issues (CATALOG-008)
- **Probability**: LOW
- **Impact**: MEDIUM (need to fix core code)
- **Mitigation**: Core code is solid (100% unit tests passing)
- **Contingency**: Fix implementation, re-run tests

---

## Success Metrics

**Sprint Success**:
- [ ] All 11 tasks complete
- [ ] 100% test pass rate (805/805)
- [ ] 0 known bugs
- [ ] Feature usable from CLI
- [ ] Documentation complete
- [ ] Ready to ship v0.4.0

**Quality Success**:
- [ ] 100% code coverage for new code
- [ ] All quality checks passing (black, ruff, mypy)
- [ ] No performance regression
- [ ] 100% backward compatibility

**User Success**:
- [ ] Feature intuitive to use
- [ ] Clear error messages
- [ ] Examples work correctly
- [ ] Migration path clear (no action needed)

---

## Post-Sprint Actions

**After Sprint Complete**:
1. [ ] Tag v0.4.0 release
2. [ ] Update GitHub release notes
3. [ ] Announce feature in docs
4. [ ] Monitor for user issues
5. [ ] Plan Phase 2 (Git integration) based on feedback

**Retrospective Questions**:
- What went well?
- What could be improved?
- What should we do differently in Phase 2?
- What lessons learned from this sprint?

---

**SPRINT STATUS**: READY TO START
**Start Date**: 2025-11-17
**Target End Date**: 2025-11-29 (10 working days)
**Confidence**: 90% (clear plan, proven quality, manageable scope)

---

*Sprint plan created by: Implementation Planner Agent*
*Date: 2025-11-17 03:30:01*
*Source: BACKLOG-CATALOG-PHASE1-2025-11-17-033001.md*
*Sprint Type: Feature completion sprint*
*Goal: Ship v0.4.0 with multi-catalog support*
