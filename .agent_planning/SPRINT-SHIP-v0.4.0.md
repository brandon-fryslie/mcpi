# Sprint: Ship v0.4.0 - Multi-Catalog Phase 1

**Sprint Goal**: Fix critical bug, write documentation, and ship v0.4.0
**Duration**: 1.5 days (11 hours)
**Start Date**: 2025-11-17
**Target Ship Date**: 2025-11-18
**Source**: BACKLOG-CATALOG-PHASE1-FINAL.md
**Status**: STATUS-CATALOG-PHASE1-FINAL-EVALUATION-2025-11-17-043800.md

---

## Sprint Overview

**Current State**: 91% complete (10/11 tasks done), 777/805 tests passing
**Blockers**: 1 critical CLI bug, documentation not started
**Goal**: Ship production-ready v0.4.0 with multi-catalog support

**What's Working**:
- CatalogManager API: 100% functional
- All catalog commands: 100% functional
- search/info/add with --catalog: 100% functional
- Unit tests: 27/27 passing (100%)
- Integration tests: 27/27 passing (100%)

**What's Broken**:
- search with --all-catalogs: Click parser bug
- E2E tests: 24/24 failing (test infrastructure, not product bug)
- Documentation: Not started

---

## Sprint Backlog

### Day 1: Morning Session (2 hours)

#### Task 1: Fix --all-catalogs Bug
**Priority**: P0 (Critical - Blocks Release)
**Effort**: 1 hour
**Assignee**: Developer
**Status**: Not Started

**Problem**:
```bash
$ mcpi search git --all-catalogs
Error: No such option: --all-catalogs
```

**Root Cause**: Click parser treats options after optional argument as top-level

**Solution** (Recommended: Option 2):
```python
# File: src/mcpi/cli.py

# BEFORE (line 1691)
@click.argument("query", required=False)
@click.option("--all-catalogs", is_flag=True, ...)

# AFTER (Option 2 - Most Robust)
@click.option("--query", "-q", default=None, help="Search query (optional)")
@click.option("--all-catalogs", is_flag=True, help="Search all catalogs")

# Update search() function signature
def search(ctx, query, catalog, all_catalogs):
    """Search for MCP servers."""
    # query can now be None (means search all servers)
    if query is None and not all_catalogs:
        # Interactive mode or error
        pass
```

**Alternative** (Option 1 - Simplest):
```python
# Make query required
@click.argument("query")  # Remove required=False

# Help text explains: use "*" or "" for all servers
```

**Acceptance Criteria**:
- [ ] `mcpi search git --all-catalogs` works
- [ ] `mcpi search --all-catalogs git` works
- [ ] `mcpi search filesystem --catalog official` still works
- [ ] All existing search patterns still work
- [ ] Help text updated with examples

**Testing**:
- [ ] Manual test all combinations (see checklist below)
- [ ] Add regression tests
- [ ] Verify backward compatibility

---

#### Task 2: Add Regression Tests
**Priority**: P0 (Critical)
**Effort**: 0.5 hours
**Assignee**: Developer
**Status**: Not Started

**Add to** `tests/test_cli_catalog_commands.py`:

```python
def test_search_all_catalogs_flag_order_variant1(cli_runner, test_catalogs):
    """Test: mcpi search git --all-catalogs"""
    result = cli_runner.invoke(main, ["search", "git", "--all-catalogs"])
    assert result.exit_code == 0
    assert "official" in result.output
    assert "local" in result.output

def test_search_all_catalogs_flag_order_variant2(cli_runner, test_catalogs):
    """Test: mcpi search --all-catalogs git"""
    result = cli_runner.invoke(main, ["search", "--all-catalogs", "git"])
    assert result.exit_code == 0
    assert "official" in result.output
    assert "local" in result.output

def test_search_all_catalogs_empty_query(cli_runner, test_catalogs):
    """Test: mcpi search --all-catalogs (no query)"""
    result = cli_runner.invoke(main, ["search", "--all-catalogs"])
    # Should show all servers from all catalogs
    assert result.exit_code == 0

def test_search_catalog_and_all_catalogs_mutually_exclusive(cli_runner):
    """Test: Error if both --catalog and --all-catalogs used"""
    result = cli_runner.invoke(
        main, ["search", "git", "--catalog", "official", "--all-catalogs"]
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()
```

**Acceptance Criteria**:
- [ ] 4 new regression tests added
- [ ] All tests pass
- [ ] Tests cover both flag order variants
- [ ] Tests cover error cases

---

#### Task 3: Manual Test All Search Variants
**Priority**: P0 (Critical)
**Effort**: 0.5 hours
**Assignee**: Developer
**Status**: Not Started

**Test Checklist**:
```bash
# Default behavior (backward compat)
mcpi search filesystem
# Expected: Searches official catalog only

# Specific catalog
mcpi search filesystem --catalog official
# Expected: Searches official catalog

mcpi search filesystem --catalog local
# Expected: Searches local catalog

mcpi search filesystem --catalog OFFICIAL
# Expected: Case-insensitive, searches official

# All catalogs (both flag orders)
mcpi search git --all-catalogs
# Expected: Searches both, groups by catalog

mcpi search --all-catalogs git
# Expected: Same as above

# Empty query with all catalogs
mcpi search --all-catalogs
# Expected: Lists all servers from all catalogs

# Error cases
mcpi search git --catalog unknown
# Expected: Error, exit code 1

mcpi search git --catalog official --all-catalogs
# Expected: Error, mutually exclusive

# Edge cases
mcpi search ""
# Expected: Lists all servers (official only)

mcpi search "" --all-catalogs
# Expected: Lists all servers from all catalogs
```

**Acceptance Criteria**:
- [ ] All test cases pass
- [ ] No regressions from v0.3.0
- [ ] Error messages clear and helpful
- [ ] Performance acceptable (<500ms for search)

---

### Day 1: Afternoon Session (6 hours)

#### Task 4: Update CLAUDE.md
**Priority**: P0 (Critical - Blocks Release)
**Effort**: 2.5 hours
**Assignee**: Writer
**Status**: Not Started

**Sections to Update**:

1. **Add "Multi-Catalog System" Section** (after "Server Catalog System")
```markdown
### Multi-Catalog System

MCPI supports multiple server catalogs starting in v0.4.0:

**Catalogs**:
- **Official Catalog**: Curated MCP servers (`data/catalog.json` in package)
- **Local Catalog**: User's custom servers (`~/.mcpi/catalogs/local/catalog.json`)

**CatalogManager**:
The `CatalogManager` class manages multiple catalogs with lazy loading and dependency injection.

**Usage**:
```python
from mcpi.registry.catalog_manager import create_default_catalog_manager

# Get manager with both catalogs
manager = create_default_catalog_manager()

# List all catalogs
catalogs = manager.list_catalogs()  # Returns [CatalogInfo, CatalogInfo]

# Get specific catalog (lazy loaded)
official = manager.get_catalog("official")
local = manager.get_catalog("local")

# Search across all catalogs
results = manager.search_all("git")
# Returns: List[(catalog_name, server_id, server)]
```

**Factory Functions**:
- `create_default_catalog_manager()`: Production manager with default paths
- `create_test_catalog_manager(official_path, local_path)`: Test manager with custom paths

**Design Patterns**:
- Dependency Injection: Paths injected via constructor
- Lazy Loading: Catalogs loaded on first access
- Factory Pattern: Separate factories for production/test
```

2. **Update "Server Catalog System" Section**
```markdown
### Server Catalog System (`mcpi.registry/`)

**Two Catalogs** (v0.4.0+):
- `catalog.py`: `ServerCatalog` class for single catalog
- `catalog_manager.py`: `CatalogManager` for multiple catalogs
- Data: `data/catalog.json` (official), `~/.mcpi/catalogs/local/catalog.json` (local)

**Migration**:
- v0.3.0: Single catalog via `create_default_catalog()`
- v0.4.0: Multi-catalog via `create_default_catalog_manager()`
- Backward compatibility: Old API still works with deprecation warning
```

3. **Update "DIP Implementation" Section**
```markdown
### CatalogManager Examples

**Production**:
```python
from mcpi.registry.catalog_manager import create_default_catalog_manager
manager = create_default_catalog_manager()  # Uses default paths
```

**Testing**:
```python
from mcpi.registry.catalog_manager import CatalogManager
from pathlib import Path

# Custom paths for testing
manager = CatalogManager(
    official_path=tmp_path / "official.json",
    local_path=tmp_path / "local.json"
)
```

**Old Pattern** (deprecated):
```python
from mcpi.registry.catalog import create_default_catalog
catalog = create_default_catalog()  # Shows deprecation warning
```
```

4. **Update "Testing Strategy" Section**
```markdown
### Multi-Catalog Testing Patterns

**Unit Tests**:
```python
def test_catalog_manager(tmp_path):
    official = tmp_path / "official.json"
    official.write_text('{"servers": {...}}')

    local = tmp_path / "local.json"
    local.write_text('{}')

    manager = CatalogManager(
        official_path=official,
        local_path=local
    )

    assert manager.get_catalog("official") is not None
    assert manager.get_catalog("local") is not None
```

**Integration Tests**:
Use `create_default_catalog_manager()` and mock catalog contents.

**E2E Tests**:
Create temporary catalogs with full server data.
```

**Acceptance Criteria**:
- [ ] All sections updated
- [ ] Code examples tested and working
- [ ] Migration guidance clear
- [ ] Backward compatibility explained

---

#### Task 5: Update README.md
**Priority**: P0 (Critical - Blocks Release)
**Effort**: 2.5 hours
**Assignee**: Writer
**Status**: Not Started

**Sections to Add/Update**:

1. **Add "Multiple Catalogs" Section** (after "Features")
```markdown
## Multiple Catalogs

MCPI supports multiple server catalogs (v0.4.0+):

**Official Catalog**: Curated collection of MCP servers
- Location: Included in package (`data/catalog.json`)
- Servers: High-quality, well-maintained servers
- Updates: Via MCPI package updates

**Local Catalog**: Your personal server collection
- Location: `~/.mcpi/catalogs/local/catalog.json`
- Servers: Custom, private, or experimental servers
- Management: Manual editing or future CLI commands (Phase 2+)

**Use Cases for Local Catalog**:
- Private company servers
- Development/testing servers
- Experimental servers not yet in official catalog
- Custom configurations of official servers
```

2. **Add Examples Section**
```markdown
## Working with Catalogs

### List Available Catalogs
```bash
mcpi catalog list
```

### View Catalog Details
```bash
# Official catalog
mcpi catalog info official

# Local catalog
mcpi catalog info local
```

### Search Specific Catalog
```bash
# Search official only (default)
mcpi search filesystem

# Search official explicitly
mcpi search filesystem --catalog official

# Search local catalog
mcpi search my-server --catalog local

# Search all catalogs
mcpi search git --all-catalogs
```

### Add Server from Specific Catalog
```bash
# From official (default)
mcpi add filesystem

# From local
mcpi add my-server --catalog local
```

3. **Add FAQ Section**
```markdown
## FAQ

**Q: What are catalogs?**
A: Catalogs are collections of MCP server definitions. MCPI includes an official catalog and supports a local catalog for your custom servers.

**Q: Where is the local catalog stored?**
A: `~/.mcpi/catalogs/local/catalog.json` (auto-created on first use)

**Q: How do I add a server to my local catalog?**
A: Currently, edit `~/.mcpi/catalogs/local/catalog.json` manually. Future versions will add CLI commands for this (Phase 2+).

**Q: Can I have more than 2 catalogs?**
A: Not yet. Phase 2+ will add support for custom catalogs.

**Q: What happens if I delete my local catalog?**
A: It will be re-created (empty) on next `mcpi` run. Your custom servers will be lost unless you have a backup.

**Q: Do I need to migrate from v0.3.0?**
A: No! v0.4.0 is 100% backward compatible. All existing commands work unchanged.
```

4. **Update Quick Start**
```markdown
## Quick Start

# List available catalogs
mcpi catalog list

# Search for servers
mcpi search git

# Search all catalogs
mcpi search git --all-catalogs

# View catalog details
mcpi catalog info official

# Add a server (searches official by default)
mcpi add filesystem
```

**Acceptance Criteria**:
- [ ] All sections added
- [ ] Examples tested and accurate
- [ ] FAQ answers common questions
- [ ] User-friendly and clear

---

#### Task 6: Update CHANGELOG.md
**Priority**: P0 (Critical - Blocks Release)
**Effort**: 1 hour
**Assignee**: Writer
**Status**: Not Started

**Add v0.4.0 Section**:
```markdown
## [0.4.0] - 2025-11-18

### Added
- **Multi-Catalog Support**: MCPI now supports multiple server catalogs
  - Official catalog: Curated MCP servers (included in package)
  - Local catalog: Your custom servers (`~/.mcpi/catalogs/local/catalog.json`)
- **New Commands**:
  - `mcpi catalog list`: List all available catalogs
  - `mcpi catalog info <name>`: Show catalog details (stats, categories, sample servers)
- **New Flags**:
  - `--catalog <name>`: Search/info/add from specific catalog
  - `--all-catalogs`: Search across all catalogs (groups results by catalog)
- **Auto-Initialization**: Local catalog automatically created on first run

### Changed
- `search` command: Now defaults to official catalog only (was implicit, now explicit)
- `info` command: Now defaults to official catalog only (was implicit, now explicit)
- `add` command: Now defaults to official catalog only (was implicit, now explicit)
- CLI help text: Updated to explain catalog flags and behavior

### Deprecated
- `create_default_catalog()` function: Use `create_default_catalog_manager()` instead
  - Will show deprecation warning starting in v0.4.0
  - Will be removed in v1.0.0
  - Still works for backward compatibility

### Migration Guide: v0.3.0 → v0.4.0

**No Action Required!**

v0.4.0 is 100% backward compatible with v0.3.0. All existing CLI commands and Python code work unchanged.

**What's New (Optional)**:
- Try `mcpi catalog list` to see both official and local catalogs
- Use `--catalog local` to work with your local catalog
- Use `--all-catalogs` to search across all catalogs at once

**For Python Library Users**:

Old pattern (still works, with deprecation warning):
```python
from mcpi.registry.catalog import create_default_catalog
catalog = create_default_catalog()  # Returns official catalog
```

New pattern (recommended for new code):
```python
from mcpi.registry.catalog_manager import create_default_catalog_manager
manager = create_default_catalog_manager()
official = manager.get_catalog("official")
local = manager.get_catalog("local")
results = manager.search_all("git")  # Search both catalogs
```

**Breaking Changes**: None

**Known Issues**: None

**Performance**: No regressions (lazy loading ensures catalogs only loaded when accessed)

### Internal
- Added `CatalogManager` class for managing multiple catalogs
- Added 27 unit tests (100% coverage)
- Added 27 integration tests (100% CLI coverage)
- Updated 48 test files for multi-catalog compatibility
- Zero test regressions (777/805 tests passing, same as v0.3.0)
```

**Acceptance Criteria**:
- [ ] All new features listed
- [ ] Changes documented
- [ ] Deprecations clearly marked with timeline
- [ ] Migration guide emphasizes "no action required"
- [ ] Known issues section accurate
- [ ] Internal changes documented

---

### Day 2: Morning Session (3 hours)

#### Task 7: Complete Manual Test Checklist
**Priority**: P0 (Critical)
**Effort**: 2 hours
**Assignee**: QA/Developer
**Status**: Not Started

**Full Manual Test Checklist**:

**Fresh Install**:
- [ ] Delete `~/.mcpi/` directory
- [ ] Run `mcpi catalog list`
- [ ] Verify local catalog created at `~/.mcpi/catalogs/local/catalog.json`
- [ ] Verify file contains `{}`
- [ ] Verify command shows 2 catalogs (official + local)

**Catalog Commands**:
- [ ] `mcpi catalog list` shows Rich table with 2 rows
- [ ] Table shows: name, type, server count, description
- [ ] `mcpi catalog info official` shows: path, servers, categories, samples
- [ ] `mcpi catalog info local` shows local catalog (empty initially)
- [ ] `mcpi catalog info unknown` shows error, exits with code 1

**Search Command - Default Behavior**:
- [ ] `mcpi search filesystem` searches official only
- [ ] `mcpi search git` searches official only
- [ ] Output matches v0.3.0 behavior (backward compat)

**Search Command - Catalog Flag**:
- [ ] `mcpi search filesystem --catalog official` works
- [ ] `mcpi search filesystem --catalog local` works (empty results initially)
- [ ] `mcpi search filesystem --catalog OFFICIAL` works (case-insensitive)
- [ ] `mcpi search filesystem --catalog unknown` shows error

**Search Command - All Catalogs Flag**:
- [ ] `mcpi search git --all-catalogs` searches both
- [ ] `mcpi search --all-catalogs git` works (flag order variant)
- [ ] Results grouped by catalog name
- [ ] Shows "official" section with results
- [ ] Shows "local" section (empty initially)

**Info/Add Commands**:
- [ ] `mcpi info filesystem` finds in official
- [ ] `mcpi info filesystem --catalog official` works
- [ ] `mcpi info filesystem --catalog local` doesn't find (local empty)
- [ ] `mcpi add filesystem` uses official (default)
- [ ] `mcpi add filesystem --catalog local` (can't test without server in local)

**Local Catalog Workflow**:
- [ ] Manually edit `~/.mcpi/catalogs/local/catalog.json`
- [ ] Add custom server: `{"my-test-server": {"name": "Test", "method": "stdio", ...}}`
- [ ] `mcpi catalog list` shows local with 1 server
- [ ] `mcpi catalog info local` shows the custom server
- [ ] `mcpi search my-test-server` doesn't find (official only)
- [ ] `mcpi search my-test-server --catalog local` finds it
- [ ] `mcpi search my-test-server --all-catalogs` finds in local section
- [ ] `mcpi info my-test-server --catalog local` shows details

**Persistence**:
- [ ] Close terminal
- [ ] Open new terminal
- [ ] `mcpi catalog list` still shows 2 catalogs
- [ ] Custom server still in local catalog

**Backward Compatibility**:
- [ ] All v0.3.0 commands work unchanged
- [ ] Python: `create_default_catalog()` works with deprecation warning
- [ ] Warning message is clear and helpful

**Error Handling**:
- [ ] Unknown catalog name: Clear error message, exit code 1
- [ ] Mutually exclusive flags: Clear error message
- [ ] Missing server: Helpful error with suggestions
- [ ] Corrupted JSON: Graceful error (test if time permits)

**Acceptance Criteria**:
- [ ] All manual tests pass
- [ ] No regressions from v0.3.0
- [ ] Error messages helpful and clear
- [ ] Feature works as designed

---

#### Task 8: Performance Verification
**Priority**: P1 (High)
**Effort**: 0.5 hours
**Assignee**: QA/Developer
**Status**: Not Started

**Performance Benchmarks**:
```bash
# Catalog list (target: <100ms)
time mcpi catalog list

# Search official (target: <500ms, same as v0.3.0)
time mcpi search filesystem

# Search all catalogs (target: <1000ms)
time mcpi search filesystem --all-catalogs

# Catalog info (target: <200ms)
time mcpi catalog info official
```

**Acceptance Criteria**:
- [ ] `catalog list` runs in <100ms
- [ ] `search` (official) runs in <500ms (no regression)
- [ ] `search --all-catalogs` runs in <1000ms
- [ ] `catalog info` runs in <200ms
- [ ] No noticeable slowdown from v0.3.0

**If Performance Issues Found**:
- Profile with `cProfile`
- Identify bottlenecks
- Optimize or defer to v0.4.1

---

#### Task 9: Final Review and Polish
**Priority**: P1 (High)
**Effort**: 0.5 hours
**Assignee**: Tech Lead
**Status**: Not Started

**Review Checklist**:
- [ ] Run full test suite: `pytest -v --tb=short`
- [ ] Verify 777/805 tests passing (same as before)
- [ ] Run code quality: `black src/ tests/ && ruff check src/ tests/`
- [ ] Review all documentation updates (CLAUDE.md, README.md, CHANGELOG.md)
- [ ] Verify all examples in docs are accurate and tested
- [ ] Review git diff for any accidental changes
- [ ] Verify version number updated in `pyproject.toml` (or wherever)

**Git Status Check**:
```bash
git status
# Should show:
# - Modified: src/mcpi/cli.py (--all-catalogs fix)
# - Modified: CLAUDE.md
# - Modified: README.md
# - Modified: CHANGELOG.md
# - Modified: tests/test_cli_catalog_commands.py (regression tests)
# - Possibly: pyproject.toml (version bump)
```

**Acceptance Criteria**:
- [ ] All tests passing
- [ ] Code quality clean
- [ ] Documentation accurate
- [ ] Git state clean (no unexpected changes)
- [ ] Ready to commit and tag

---

## Ship Checklist

**Before Tagging v0.4.0**:
- [ ] All sprint tasks complete
- [ ] All manual tests pass
- [ ] Performance benchmarks met
- [ ] Documentation complete and accurate
- [ ] Code quality clean (black, ruff)
- [ ] Test suite passing (777/805 or better)
- [ ] Git status clean (only expected changes)

**Commit and Tag**:
```bash
# Commit all changes
git add .
git commit -m "feat: Multi-Catalog Phase 1 - Add official and local catalogs

- Add CatalogManager for managing multiple catalogs
- Add 'catalog list' and 'catalog info' commands
- Add --catalog and --all-catalogs flags to search/info/add
- Auto-initialize local catalog at ~/.mcpi/catalogs/local/catalog.json
- Deprecate create_default_catalog() in favor of create_default_catalog_manager()
- 100% backward compatible with v0.3.0
- Add 27 unit tests, 27 integration tests (all passing)
- Update CLAUDE.md, README.md, CHANGELOG.md

Closes #XXX (multi-catalog epic)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Tag release
git tag -a v0.4.0 -m "Release v0.4.0: Multi-Catalog Support

See CHANGELOG.md for full details"

# Push
git push origin master
git push origin v0.4.0
```

**Post-Ship**:
- [ ] Update GitHub release notes (copy from CHANGELOG.md)
- [ ] Announce in relevant channels
- [ ] Monitor for issues
- [ ] Prepare v0.4.1 backlog for deferred items

---

## Definition of Done

**Sprint is DONE when**:
- [x] All P0 tasks complete
- [x] --all-catalogs bug fixed and tested
- [x] CLAUDE.md updated with multi-catalog architecture
- [x] README.md updated with examples and FAQ
- [x] CHANGELOG.md updated with v0.4.0 release notes
- [x] All manual tests pass
- [x] Performance benchmarks met
- [x] v0.4.0 tagged and pushed
- [x] GitHub release created

**Ship Criteria Met**:
- Feature complete (10/11 tasks + bug fix)
- Quality high (777/805 tests passing, 100% catalog coverage)
- Documentation complete
- No regressions
- Performance acceptable

---

## Risk Mitigation

**Risk 1: --all-catalogs fix reveals deeper issues**
- Mitigation: Have 3 fix options ready, test thoroughly
- Fallback: If complex, defer flag and ship without it (document in known issues)

**Risk 2: Documentation takes longer than expected**
- Mitigation: Use structured templates, focus on examples
- Fallback: Ship with minimal docs, improve in v0.4.1

**Risk 3: Performance regression discovered**
- Mitigation: Profile and optimize
- Fallback: If unfixable, document and defer optimization to v0.4.1

**Overall Risk**: LOW (implementation solid, only polish remains)

---

## Success Metrics

**Post-Ship Success**:
- [ ] v0.4.0 tagged and released
- [ ] Zero critical bugs reported in first 48 hours
- [ ] Documentation feedback positive
- [ ] Users discover and use local catalog feature
- [ ] No rollback required

---

**END OF SPRINT PLAN**

**Status**: READY TO EXECUTE
**Estimated Completion**: 2025-11-18 EOD
**Confidence**: 95% (clear tasks, realistic timeline)

---

*Sprint plan created by: Implementation Planner Agent*
*Date: 2025-11-17 04:44:21*
*Source: BACKLOG-CATALOG-PHASE1-FINAL.md*
*Target: v0.4.0 Release*
