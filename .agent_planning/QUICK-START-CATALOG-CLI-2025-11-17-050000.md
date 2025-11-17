# Multi-Catalog CLI Integration - Quick Start

**What to do next**: Implement CLI integration for multi-catalog feature
**Time needed**: 3-4 days (23.5 hours)
**Current status**: Backend complete, CLI blocked

---

## What You Need to Know

### Current State
- ✅ **Backend complete**: CatalogManager working (25/25 tests passing)
- ❌ **CLI blocked**: Missing `get_catalog_manager(ctx)` function
- ❌ **User value**: 0% - users cannot access multi-catalog features

### The Blocker
**CATALOG-003**: CLI Context Integration (1.5 hours)
- Missing function: `get_catalog_manager(ctx)`
- Blocks: All CLI commands, 24 failing tests
- **Start here first**

---

## What to Build (3-4 Days)

### Day 1: Unblock and First Value (6 hours)

**Morning (1.5h): CATALOG-003 - CLI Context**
```python
# Add to src/mcpi/cli.py
def get_catalog_manager(ctx: click.Context) -> CatalogManager:
    if "catalog_manager" not in ctx.obj:
        ctx.obj["catalog_manager"] = create_default_catalog_manager()
    return ctx.obj["catalog_manager"]

def get_catalog(ctx: click.Context, catalog_name: Optional[str] = None):
    manager = get_catalog_manager(ctx)
    if catalog_name is None:
        return manager.get_default_catalog()
    catalog = manager.get_catalog(catalog_name)
    if catalog is None:
        raise click.ClickException(f"Unknown catalog: {catalog_name}")
    return catalog
```

**Afternoon (4h): CATALOG-004 - Catalog Commands**
```bash
mcpi catalog list           # List both catalogs
mcpi catalog info official  # Show catalog details
```

---

### Day 2: Multi-Catalog Search (8 hours)

**CATALOG-005: Add --catalog Flags**
```bash
mcpi search filesystem --catalog local
mcpi search filesystem --all-catalogs
mcpi info filesystem --catalog local
mcpi add filesystem --catalog local
```

---

### Day 3: Fix Tests (6 hours)

**Morning: CATALOG-006 - CLI Integration Tests**
- Fix 24 failing tests
- Expected: 27/27 passing

**Afternoon: CATALOG-007 - E2E Tests**
- Fix 8 failing tests
- Expected: 26/26 passing

---

### Day 4: Polish (6 hours)

**CATALOG-008: Documentation**
- Update CLAUDE.md, README.md, CHANGELOG.md

**CATALOG-009: Manual Testing**
- Run through checklist
- Fix any bugs
- Performance check

---

## Files to Modify

### Implementation Files
- `src/mcpi/cli.py` - Add ~350 lines
  - Context helpers (50 lines)
  - Catalog commands (120 lines)
  - Flag updates (180 lines)
- `src/mcpi/registry/catalog.py` - Add 10 lines (deprecation)

### Documentation Files
- `CLAUDE.md` - Architecture update (~100 lines)
- `README.md` - Usage examples (~50 lines)
- `CHANGELOG.md` - Release notes (~30 lines)

### Test Files (Already Written!)
- `tests/test_cli_catalog_commands.py` - 27 tests (3 passing, 24 to fix)
- `tests/test_multi_catalog_e2e.py` - 26 tests (18 passing, 8 to fix)

---

## Quick Commands Reference

### What Works After Each Task

**After CATALOG-003**:
```bash
# Nothing user-visible yet, but:
# - get_catalog_manager(ctx) exists
# - Can start building CLI commands
```

**After CATALOG-004**:
```bash
mcpi catalog list
mcpi catalog info official
mcpi catalog info local
```

**After CATALOG-005**:
```bash
# All existing commands still work (backward compat)
mcpi search filesystem

# New multi-catalog features
mcpi search filesystem --catalog local
mcpi search filesystem --all-catalogs
mcpi info filesystem --catalog local
mcpi add filesystem --catalog local
```

**After CATALOG-006/007**:
```bash
# All features work, all tests pass
pytest tests/test_catalog_manager.py          # 25/25 ✅
pytest tests/test_cli_catalog_commands.py     # 27/27 ✅
pytest tests/test_multi_catalog_e2e.py        # 26/26 ✅
```

---

## Success Checklist

### Implementation
- [ ] CATALOG-003: CLI context (1.5h) - **START HERE**
- [ ] CATALOG-004: Catalog commands (4h)
- [ ] CATALOG-005: --catalog flags (8h)
- [ ] CATALOG-006: Fix CLI tests (4h)
- [ ] CATALOG-007: Fix E2E tests (2h)
- [ ] CATALOG-008: Documentation (4h)
- [ ] CATALOG-009: Manual testing (2h)

### Quality Gates
- [ ] 78/78 tests passing (100%)
- [ ] Code passes black, ruff, mypy
- [ ] No regressions (752 existing tests)
- [ ] Performance: no slowdown vs v0.3.0

### User Value
- [ ] Users can list catalogs
- [ ] Users can search specific catalogs
- [ ] Users can search all catalogs
- [ ] Existing workflows unchanged
- [ ] Local catalog auto-initializes

---

## What to Test Manually

### Basic Operations
```bash
# List catalogs
mcpi catalog list
# Expect: Table with official (42 servers) and local (0 servers)

# Show catalog info
mcpi catalog info official
mcpi catalog info local

# Search operations
mcpi search filesystem                    # Default (official)
mcpi search filesystem --catalog local
mcpi search filesystem --all-catalogs
```

### Local Catalog Workflow
```bash
# Add custom server to local catalog (manual)
cat > ~/.mcpi/catalogs/local/catalog.json <<EOF
{
  "test-server": {
    "description": "Test custom server",
    "command": "node",
    "args": ["test.js"],
    "repository": null,
    "categories": ["test"]
  }
}
EOF

# Find it
mcpi search test-server --catalog local
mcpi search test --all-catalogs
mcpi info test-server --catalog local
```

### Backward Compatibility
```bash
# Old commands still work (no breaking changes)
mcpi search filesystem
mcpi info filesystem
mcpi add filesystem --scope project-mcp
```

---

## Performance Targets

- `mcpi catalog list`: < 100ms
- `mcpi search <query>`: < 500ms (no regression)
- `mcpi search <query> --all-catalogs`: < 1000ms

---

## Key APIs to Know

### Context Helpers (cli.py)
```python
manager = get_catalog_manager(ctx)
catalog = get_catalog(ctx, catalog_name=None)
```

### CatalogManager API (catalog_manager.py)
```python
catalog = manager.get_catalog("official" | "local")
catalogs = manager.list_catalogs()  # List[CatalogInfo]
results = manager.search_all(query)  # List[(name, id, server)]
```

---

## Common Patterns to Follow

### Lazy Loading
```python
def get_catalog_manager(ctx):
    if "catalog_manager" not in ctx.obj:
        ctx.obj["catalog_manager"] = create_default_catalog_manager()
    return ctx.obj["catalog_manager"]
```

### Error Handling
```python
try:
    catalog = get_catalog(ctx, catalog_name)
except click.ClickException:
    raise
except Exception as e:
    if ctx.obj.get("verbose"):
        console.print_exception()
    raise click.ClickException(f"Error: {e}")
```

### Rich Output
```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Available Catalogs")
table.add_column("Name", style="cyan")
table.add_column("Servers", justify="right", style="green")
console.print(table)
```

---

## Git Commit Strategy

After each completed task:
```bash
git add .
git commit -m "feat(catalog): <task description>"
```

Commit messages:
1. "feat(catalog): add CLI context integration for multi-catalog"
2. "feat(catalog): add catalog list and info commands"
3. "feat(catalog): add --catalog flags to search/info/add"
4. "test(catalog): fix all CLI integration and E2E tests"
5. "docs(catalog): complete multi-catalog documentation"

---

## Help! I'm Stuck

### If CATALOG-003 is taking too long
- Review existing `get_mcp_manager(ctx)` pattern in cli.py
- Copy the lazy loading pattern
- Use factory function: `create_default_catalog_manager()`
- Test with: `mcpi search filesystem` (should still work)

### If tests are failing
- Read the test code - it shows expected behavior
- Run single test: `pytest tests/test_cli_catalog_commands.py::test_name -v`
- Check error messages - they're usually clear
- Compare with existing CLI command patterns

### If Rich output looks wrong
- Look at existing Rich usage in cli.py (search/list commands)
- Follow the same patterns (Table, Panel, Console)
- Test with different terminal widths

### If backward compat is broken
- All existing commands must work unchanged
- `get_catalog(ctx)` with no args = official catalog
- Old factory `create_default_catalog()` still works (with warning)

---

## What Success Looks Like

### End of Day 1
```bash
$ mcpi catalog list
Available Catalogs
┏━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name    ┃ Type   ┃ Servers ┃ Description           ┃
┡━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ official│ builtin│ 42     │ Official MCP servers  │
│ local   │ local  │ 0      │ Your custom servers   │
└─────────┴────────┴────────┴───────────────────────┘
```

### End of Day 2
```bash
$ mcpi search filesystem --all-catalogs

OFFICIAL CATALOG
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Server ID  ┃ Description                      ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ filesystem │ MCP filesystem operations server │
└────────────┴──────────────────────────────────┘

LOCAL CATALOG
(no matches)
```

### End of Day 3
```bash
$ pytest tests/test_catalog*.py tests/test_cli_catalog*.py tests/test_multi_catalog*.py -v
====================== 78 passed in 1.2s ======================
```

### End of Day 4
- Documentation complete
- Manual testing passes
- Ready to tag v0.4.0

---

**QUICK START STATUS**: READY
**Next action**: Implement CATALOG-003 (1.5 hours)
**Full plan**: SPRINT-CATALOG-CLI-2025-11-17-050000.md

---

*Quick start guide created by: Project Planner Agent*
*Date: 2025-11-17 05:00:00*
*For implementer: Start with CATALOG-003, follow the sprint plan*
