# Sprint: Multi-Catalog Phase 1 (MVP Foundation)

**Sprint**: Phase 1 - MVP Foundation
**Version**: v0.4.0
**Duration**: 2-3 weeks
**Start Date**: TBD (pending user approval)
**Goal**: Basic multi-catalog support with two catalogs (official + local)

**Source Plan**: PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md
**Planning Summary**: PLANNING-SUMMARY-CATALOG-2025-11-17-022352.md
**Source STATUS**: STATUS-CATALOG-EVALUATION-2025-11-17-021848.md

---

## Sprint Goal

Implement **MVP multi-catalog support** with:
- Two catalogs: `official` (built-in) + `local` (user)
- Basic catalog management (list, info)
- Catalog selection in search/add operations
- **100% backward compatibility**
- Complete test coverage
- Documentation

---

## Sprint Scope

### IN SCOPE ✅

- CatalogManager class with DI patterns
- Two catalogs only (official + local)
- `mcpi catalog list` command
- `mcpi catalog info <name>` command
- `--catalog` flag for search/add/info commands
- `--all-catalogs` flag for search
- Local catalog auto-initialization
- Backward compatible factory functions
- Complete test suite (unit, integration, E2E)
- Documentation updates

### OUT OF SCOPE ❌ (Deferred to Phase 2-3)

- Git integration
- Arbitrary number of catalogs
- `catalog add/remove/sync` commands
- Schema versioning
- Overlay mechanism
- Auto-update checks

---

## Week 1: Core Infrastructure

### Task 1.1: CatalogManager Implementation

**Effort**: 2 days
**Priority**: P0 (Critical)
**Status**: Not Started
**Assignee**: TBD

**Description**:
Implement `CatalogManager` class to manage multiple catalogs. This is the foundation for all multi-catalog functionality.

**Files to Create**:
- `src/mcpi/registry/catalog_manager.py`

**Implementation Checklist**:
- [ ] Create `CatalogInfo` dataclass
- [ ] Create `CatalogManager` class with DI constructor
- [ ] Implement `__init__(official_path, local_path)`
- [ ] Implement `get_catalog(name)` with lazy loading
- [ ] Implement `get_default_catalog()`
- [ ] Implement `list_catalogs()`
- [ ] Implement `search_all(query)`
- [ ] Create `create_default_catalog_manager()` factory
- [ ] Create `create_test_catalog_manager()` factory
- [ ] Add docstrings to all public methods
- [ ] Type hints for all parameters and returns

**Acceptance Criteria**:
- [ ] CatalogManager class created with DI constructor
- [ ] `get_catalog()` lazy loads catalogs (official, local)
- [ ] `list_catalogs()` returns 2 CatalogInfo objects
- [ ] `search_all()` searches both catalogs, returns list of (catalog_name, server_id, server) tuples
- [ ] Factory functions created and working
- [ ] Local catalog auto-initialized if doesn't exist
- [ ] Local catalog path: `~/.mcpi/catalogs/local/catalog.json`
- [ ] Official catalog path: `data/catalog.json` (existing)
- [ ] Code passes mypy type checking
- [ ] Code formatted with black
- [ ] Code passes ruff linting

**Testing Plan**:
- Unit tests in Task 1.2

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Phase 1: Architecture Design"
- STATUS-CATALOG-EVALUATION-2025-11-17-021848.md, Section 2.1

---

### Task 1.2: Unit Tests for CatalogManager

**Effort**: 1 day
**Priority**: P0 (Critical)
**Status**: Not Started
**Dependencies**: Task 1.1
**Assignee**: TBD

**Description**:
Write comprehensive unit tests for CatalogManager class. Tests must achieve 100% code coverage.

**Files to Create**:
- `tests/test_catalog_manager.py`

**Test Checklist**:
- [ ] `test_init_with_paths()` - Constructor accepts paths
- [ ] `test_get_catalog_official()` - Returns official catalog
- [ ] `test_get_catalog_local()` - Returns local catalog
- [ ] `test_get_catalog_invalid()` - Returns None for unknown name
- [ ] `test_get_catalog_lazy_loading()` - Catalogs loaded on first access only
- [ ] `test_get_default_catalog()` - Returns official catalog
- [ ] `test_list_catalogs()` - Returns 2 CatalogInfo objects
- [ ] `test_list_catalogs_server_count()` - Shows correct server counts
- [ ] `test_search_all_single_match()` - Finds server in one catalog
- [ ] `test_search_all_multiple_matches()` - Finds servers in both catalogs
- [ ] `test_search_all_no_matches()` - Returns empty list
- [ ] `test_create_default_catalog_manager()` - Factory creates manager
- [ ] `test_create_test_catalog_manager()` - Test factory works
- [ ] `test_local_catalog_auto_initialization()` - Creates local catalog if missing

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] 100% code coverage for CatalogManager
- [ ] Tests use tmp_path fixture for filesystem isolation
- [ ] Tests mock filesystem where appropriate
- [ ] Tests verify both success and error paths
- [ ] Tests run in <1 second

**Testing Pattern**:
```python
def test_get_catalog_lazy_loading(tmp_path):
    """Test that catalogs are lazy loaded."""
    official_path = tmp_path / "official.json"
    local_path = tmp_path / "local.json"

    # Create empty catalogs
    official_path.write_text("{}")
    local_path.write_text("{}")

    manager = CatalogManager(official_path, local_path)

    # Catalogs not loaded yet
    assert manager._official is None
    assert manager._local is None

    # Access triggers loading
    official = manager.get_catalog("official")
    assert manager._official is not None
    assert manager._local is None  # Still not loaded

    # Second access uses cache
    official2 = manager.get_catalog("official")
    assert official is official2  # Same instance
```

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 1.2"
- STATUS-CATALOG-EVALUATION-2025-11-17-021848.md, Section 9.1

---

### Task 1.3: CLI Context Integration

**Effort**: 1 day
**Priority**: P0 (Critical)
**Status**: Not Started
**Dependencies**: Task 1.1
**Assignee**: TBD

**Description**:
Update CLI context to use CatalogManager. Maintain backward compatibility with existing code.

**Files to Modify**:
- `src/mcpi/cli.py` (update `get_catalog()` function)
- `src/mcpi/registry/catalog.py` (add deprecation warning to `create_default_catalog()`)

**Implementation Checklist**:
- [ ] Add `get_catalog_manager(ctx)` function
- [ ] Update `get_catalog(ctx, catalog_name=None)` to accept optional catalog name
- [ ] Default behavior: returns official catalog (backward compat)
- [ ] With catalog_name: returns specified catalog or raises ClickException
- [ ] Add deprecation warning to `create_default_catalog()` in catalog.py
- [ ] Deprecation message points to `create_default_catalog_manager()`
- [ ] Update imports at top of cli.py

**Code Changes**:

```python
# In src/mcpi/cli.py

def get_catalog_manager(ctx: click.Context) -> CatalogManager:
    """Lazy initialization of CatalogManager.

    Args:
        ctx: Click context

    Returns:
        CatalogManager instance
    """
    if "catalog_manager" not in ctx.obj:
        from mcpi.registry.catalog_manager import create_default_catalog_manager
        ctx.obj["catalog_manager"] = create_default_catalog_manager()
    return ctx.obj["catalog_manager"]


def get_catalog(ctx: click.Context, catalog_name: Optional[str] = None) -> ServerCatalog:
    """Get catalog by name (defaults to official catalog).

    Args:
        ctx: Click context
        catalog_name: Catalog name ("official" or "local"), or None for default

    Returns:
        ServerCatalog instance

    Raises:
        click.ClickException: If catalog_name not found
    """
    manager = get_catalog_manager(ctx)

    if catalog_name is None:
        return manager.get_default_catalog()

    catalog = manager.get_catalog(catalog_name)
    if catalog is None:
        raise click.ClickException(
            f"Unknown catalog: {catalog_name}. "
            f"Available catalogs: official, local"
        )

    return catalog
```

```python
# In src/mcpi/registry/catalog.py

def create_default_catalog(validate_with_cue: bool = True) -> ServerCatalog:
    """Create ServerCatalog with default production catalog path.

    DEPRECATED: Use create_default_catalog_manager() for multi-catalog support.
    This function maintained for backward compatibility.

    Args:
        validate_with_cue: Whether to validate with CUE schema

    Returns:
        ServerCatalog instance configured with official catalog
    """
    import warnings
    warnings.warn(
        "create_default_catalog() is deprecated. "
        "Use create_default_catalog_manager() for multi-catalog support.",
        DeprecationWarning,
        stacklevel=2
    )

    from mcpi.registry.catalog_manager import create_default_catalog_manager
    manager = create_default_catalog_manager()
    return manager.get_catalog("official")
```

**Acceptance Criteria**:
- [ ] `get_catalog_manager(ctx)` function added
- [ ] `get_catalog(ctx, catalog_name)` updated with optional parameter
- [ ] Backward compatibility: `get_catalog(ctx)` still returns official catalog
- [ ] Unknown catalog name raises ClickException with helpful message
- [ ] Deprecation warning added to `create_default_catalog()`
- [ ] Warning uses DeprecationWarning category
- [ ] Warning message is clear and actionable
- [ ] Code passes type checking
- [ ] All existing CLI commands still work

**Testing Plan**:
- Test in Task 2.3 (CLI Integration Tests)

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 1.3"

---

## Week 2: CLI Commands

### Task 2.1: Add --catalog Flag to Existing Commands

**Effort**: 2 days
**Priority**: P0 (Critical)
**Status**: Not Started
**Dependencies**: Task 1.3
**Assignee**: TBD

**Description**:
Add `--catalog` and `--all-catalogs` flags to existing CLI commands (search, info, add, remove).

**Files to Modify**:
- `src/mcpi/cli.py` (update commands: search, info, add, remove)

**Implementation Checklist**:

**search command**:
- [ ] Add `--catalog` option (Choice: official, local)
- [ ] Add `--all-catalogs` flag
- [ ] Default: search official catalog only (backward compat)
- [ ] `--catalog <name>`: search specific catalog
- [ ] `--all-catalogs`: search both, group results by catalog
- [ ] Update help text

**info command**:
- [ ] Add `--catalog` option (Choice: official, local)
- [ ] Default: search official catalog first, then local
- [ ] `--catalog <name>`: search specific catalog only
- [ ] Update help text

**add command**:
- [ ] Add `--catalog` option (Choice: official, local)
- [ ] Default: search official catalog (backward compat)
- [ ] `--catalog <name>`: search specific catalog
- [ ] Update help text

**remove command**:
- [ ] Already scope-aware, no catalog flag needed
- [ ] Document that remove operates on installed servers, not catalog

**Code Example**:

```python
@cli.command()
@click.argument("query")
@click.option(
    "--catalog",
    type=click.Choice(["official", "local"], case_sensitive=False),
    help="Search in specific catalog (default: official)",
)
@click.option(
    "--all-catalogs",
    is_flag=True,
    help="Search across all catalogs",
)
@click.pass_context
def search(ctx, query: str, catalog: Optional[str], all_catalogs: bool):
    """Search for MCP servers.

    Examples:
        mcpi search filesystem
        mcpi search database --catalog local
        mcpi search git --all-catalogs
    """
    if all_catalogs:
        # Search all catalogs
        manager = get_catalog_manager(ctx)
        results = manager.search_all(query)

        if not results:
            click.echo(f"No servers found matching '{query}'")
            return

        # Group by catalog for display
        from collections import defaultdict
        by_catalog = defaultdict(list)
        for catalog_name, server_id, server in results:
            by_catalog[catalog_name].append((server_id, server))

        # Display results grouped by catalog
        for catalog_name in ["official", "local"]:
            if catalog_name in by_catalog:
                click.echo(f"\n{catalog_name.upper()} CATALOG:")
                for server_id, server in by_catalog[catalog_name]:
                    click.echo(f"  {server_id}: {server.description}")
    else:
        # Search single catalog
        cat = get_catalog(ctx, catalog)
        results = cat.search_servers(query)

        if not results:
            click.echo(f"No servers found matching '{query}'")
            return

        for server_id, server in results:
            click.echo(f"{server_id}: {server.description}")
```

**Acceptance Criteria**:
- [ ] `search` command has `--catalog` and `--all-catalogs` flags
- [ ] `info` command has `--catalog` flag
- [ ] `add` command has `--catalog` flag
- [ ] Default behavior unchanged (uses official catalog)
- [ ] `--all-catalogs` groups results by catalog name
- [ ] Help text updated with examples
- [ ] Mutually exclusive flags validated (can't use both --catalog and --all-catalogs)
- [ ] Rich table formatting preserved
- [ ] Error messages are clear and helpful

**Testing Plan**:
- Test in Task 2.3 (CLI Integration Tests)

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 2.1"
- STATUS-CATALOG-EVALUATION-2025-11-17-021848.md, Section 8.1

---

### Task 2.2: Implement catalog Subcommand Group

**Effort**: 2 days
**Priority**: P0 (Critical)
**Status**: Not Started
**Dependencies**: Task 1.3
**Assignee**: TBD

**Description**:
Add new `mcpi catalog` command group with `list` and `info` subcommands.

**Files to Modify**:
- `src/mcpi/cli.py` (add catalog group and commands)

**Implementation Checklist**:
- [ ] Create `catalog` command group
- [ ] Implement `catalog list` command
- [ ] Implement `catalog info <name>` command
- [ ] Use Rich tables for output
- [ ] Add help text and examples
- [ ] Follow existing CLI patterns (colors, formatting)

**Commands to Implement**:

```python
@cli.group()
def catalog():
    """Manage MCP server catalogs.

    MCPI supports multiple server catalogs:
    - official: Built-in catalog of MCP servers
    - local: Your custom servers
    """
    pass


@catalog.command("list")
@click.pass_context
def catalog_list(ctx):
    """List all available catalogs.

    Example:
        mcpi catalog list
    """
    manager = get_catalog_manager(ctx)
    catalogs = manager.list_catalogs()

    # Display as Rich table
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Available Catalogs", show_header=True)

    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Servers", justify="right", style="green")
    table.add_column("Description", style="white")

    for cat in catalogs:
        table.add_row(
            cat.name,
            cat.type,
            str(cat.server_count),
            cat.description
        )

    console.print(table)
    console.print(f"\nUse [cyan]mcpi catalog info <name>[/cyan] for details")


@catalog.command("info")
@click.argument("name", type=click.Choice(["official", "local"]))
@click.pass_context
def catalog_info(ctx, name: str):
    """Show detailed information about a catalog.

    Examples:
        mcpi catalog info official
        mcpi catalog info local
    """
    manager = get_catalog_manager(ctx)
    cat = manager.get_catalog(name)

    if not cat:
        click.echo(f"Catalog '{name}' not found", err=True)
        ctx.exit(1)

    # Get catalog metadata
    servers = cat.list_servers()
    categories = cat.list_categories()

    # Display using Rich
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    # Catalog header
    console.print(Panel(
        f"[bold cyan]{name}[/bold cyan] catalog\n{cat.catalog_path}",
        title="Catalog Information"
    ))

    # Stats
    console.print(f"\n[bold]Statistics:[/bold]")
    console.print(f"  Servers: {len(servers)}")
    console.print(f"  Categories: {len(categories)}")

    # Top categories
    if categories:
        console.print(f"\n[bold]Top Categories:[/bold]")
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_cats[:10]:
            console.print(f"  {category}: {count}")

    # Sample servers
    if servers:
        console.print(f"\n[bold]Sample Servers:[/bold]")
        for server_id, server in servers[:5]:
            console.print(f"  {server_id}: {server.description}")

        if len(servers) > 5:
            console.print(f"  ... and {len(servers) - 5} more")

    console.print(f"\nUse [cyan]mcpi search <query> --catalog {name}[/cyan] to search this catalog")
```

**Acceptance Criteria**:
- [ ] `mcpi catalog` group created
- [ ] `mcpi catalog list` command implemented
- [ ] `mcpi catalog info <name>` command implemented
- [ ] Rich table output for `list` command
- [ ] Rich panel/table output for `info` command
- [ ] Help text includes examples
- [ ] Commands follow existing CLI style (colors, formatting)
- [ ] Error handling for invalid catalog names
- [ ] Performance: list command runs in <100ms

**Testing Plan**:
- Test in Task 2.3 (CLI Integration Tests)

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 2.2"
- STATUS-CATALOG-EVALUATION-2025-11-17-021848.md, Section 8.1

---

### Task 2.3: CLI Integration Tests

**Effort**: 1 day
**Priority**: P0 (Critical)
**Status**: Not Started
**Dependencies**: Task 2.1, Task 2.2
**Assignee**: TBD

**Description**:
Write integration tests for CLI commands with catalog support.

**Files to Create/Modify**:
- `tests/test_cli_catalog_commands.py` (new)
- Update existing CLI tests if needed

**Test Checklist**:
- [ ] `test_search_default_catalog()` - Default searches official
- [ ] `test_search_with_catalog_flag()` - --catalog flag works
- [ ] `test_search_all_catalogs()` - --all-catalogs searches both
- [ ] `test_search_all_catalogs_groups_results()` - Results grouped by catalog
- [ ] `test_info_default_catalog()` - Default searches official
- [ ] `test_info_with_catalog_flag()` - --catalog flag works
- [ ] `test_info_unknown_catalog()` - Error for unknown catalog
- [ ] `test_catalog_list_command()` - Lists both catalogs
- [ ] `test_catalog_info_command()` - Shows catalog details
- [ ] `test_catalog_info_unknown()` - Error for unknown catalog
- [ ] `test_add_with_catalog_flag()` - Add from specific catalog

**Test Pattern**:

```python
from click.testing import CliRunner
from mcpi.cli import cli
from mcpi.registry.catalog_manager import create_test_catalog_manager

def test_search_with_catalog_flag(tmp_path):
    """Test search with --catalog flag."""
    runner = CliRunner()

    # Setup test catalogs
    official_path = tmp_path / "official.json"
    local_path = tmp_path / "local.json"

    official_path.write_text('{"filesystem": {"description": "File system server", "command": "npx", "args": [], "repository": null, "categories": []}}')
    local_path.write_text('{"my-server": {"description": "My custom server", "command": "python", "args": [], "repository": null, "categories": []}}')

    # Mock catalog manager in CLI context
    # ... (use appropriate mocking pattern)

    # Test searching official catalog
    result = runner.invoke(cli, ["search", "filesystem", "--catalog", "official"])
    assert result.exit_code == 0
    assert "filesystem" in result.output
    assert "my-server" not in result.output

    # Test searching local catalog
    result = runner.invoke(cli, ["search", "server", "--catalog", "local"])
    assert result.exit_code == 0
    assert "my-server" in result.output
    assert "filesystem" not in result.output
```

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Tests use CliRunner for CLI testing
- [ ] Tests use tmp_path for filesystem isolation
- [ ] Tests mock CatalogManager appropriately
- [ ] Tests verify both success and error paths
- [ ] Tests verify output formatting
- [ ] Tests run in <5 seconds total

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 2.3"
- STATUS-CATALOG-EVALUATION-2025-11-17-021848.md, Section 9.2

---

## Week 3: Testing and Documentation

### Task 3.1: End-to-End Tests

**Effort**: 2 days
**Priority**: P1 (High)
**Status**: Not Started
**Dependencies**: All previous tasks
**Assignee**: TBD

**Description**:
Write end-to-end tests for complete multi-catalog workflows.

**Files to Create**:
- `tests/test_multi_catalog_e2e.py`

**Test Scenarios**:
- [ ] `test_fresh_install_two_catalogs()` - Fresh install creates two catalogs
- [ ] `test_search_and_add_from_official()` - Complete workflow: search official, add server
- [ ] `test_search_and_add_from_local()` - Add custom server to local catalog
- [ ] `test_local_catalog_persistence()` - Local catalog persists across sessions
- [ ] `test_catalog_list_shows_both()` - catalog list shows both catalogs
- [ ] `test_catalog_info_official()` - catalog info shows official details
- [ ] `test_catalog_info_local()` - catalog info shows local details
- [ ] `test_search_all_catalogs_workflow()` - Search both catalogs, find servers in each
- [ ] `test_backward_compatibility()` - Old code patterns still work

**Test Pattern**:

```python
def test_fresh_install_two_catalogs(tmp_path, monkeypatch):
    """Test that fresh install creates two catalogs."""
    # Mock home directory
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Create manager (should auto-init local catalog)
    from mcpi.registry.catalog_manager import create_default_catalog_manager
    manager = create_default_catalog_manager()

    # Verify two catalogs exist
    catalogs = manager.list_catalogs()
    assert len(catalogs) == 2

    catalog_names = [c.name for c in catalogs]
    assert "official" in catalog_names
    assert "local" in catalog_names

    # Verify local catalog was created
    local_catalog_path = fake_home / ".mcpi" / "catalogs" / "local" / "catalog.json"
    assert local_catalog_path.exists()
```

**Acceptance Criteria**:
- [ ] All E2E tests pass
- [ ] Tests use MCPTestHarness where appropriate
- [ ] Tests verify complete workflows
- [ ] Tests verify filesystem state after operations
- [ ] Tests verify persistence across sessions
- [ ] Tests run in <30 seconds total

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 3.1"
- STATUS-CATALOG-EVALUATION-2025-11-17-021848.md, Section 9.2

---

### Task 3.2: Update Existing Tests

**Effort**: 2 days
**Priority**: P1 (High)
**Status**: Not Started
**Dependencies**: Task 3.1
**Assignee**: TBD

**Description**:
Review and update existing tests for multi-catalog compatibility. Ensure backward compatibility is maintained.

**Files to Review**:
- All 48 test files that reference catalog (from STATUS evaluation)

**Review Checklist**:
- [ ] Identify tests using `create_default_catalog()`
- [ ] Verify deprecation warnings don't break tests
- [ ] Update tests to suppress warnings if needed
- [ ] Add multi-catalog scenarios where appropriate
- [ ] Ensure all tests still pass
- [ ] Document any TODOs for Phase 2 enhancements

**Update Pattern**:

```python
# Before
def test_something(tmp_path):
    catalog = create_default_catalog()
    # ...

# After (Option 1: Keep old pattern, suppress warning)
def test_something(tmp_path):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        catalog = create_default_catalog()
    # ...

# After (Option 2: Use new pattern)
def test_something(tmp_path):
    manager = create_default_catalog_manager()
    catalog = manager.get_catalog("official")
    # ...
```

**Acceptance Criteria**:
- [ ] All 48 test files reviewed
- [ ] Backward compatibility verified
- [ ] All existing tests still pass
- [ ] No test regressions
- [ ] Deprecation warnings handled appropriately
- [ ] Added multi-catalog scenarios where appropriate
- [ ] TODO comments for Phase 2 enhancements

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 3.2"
- STATUS-CATALOG-EVALUATION-2025-11-17-021848.md, Section 9.3

---

### Task 3.3: Documentation

**Effort**: 2 days
**Priority**: P1 (High)
**Status**: Not Started
**Dependencies**: Task 3.2
**Assignee**: TBD

**Description**:
Update all project documentation for multi-catalog feature.

**Files to Update**:
- `CLAUDE.md` (project documentation)
- `README.md` (user-facing documentation)
- `CHANGELOG.md` (release notes)
- CLI help text (verify completeness)

**Documentation Checklist**:

**CLAUDE.md**:
- [ ] Update "Project Architecture" section
- [ ] Add "Multi-Catalog System" subsection
- [ ] Document CatalogManager design
- [ ] Update "Server Catalog System" section
- [ ] Add factory function examples
- [ ] Update "Testing Strategy" section
- [ ] Add backward compatibility notes

**README.md**:
- [ ] Add "Multiple Catalogs" section
- [ ] Show examples of catalog commands
- [ ] Show examples of --catalog flag
- [ ] Document local catalog location
- [ ] Add FAQ about catalogs
- [ ] Update quick start guide

**CHANGELOG.md**:
- [ ] Add v0.4.0 section
- [ ] List new features
- [ ] List deprecations
- [ ] Migration guide from v0.3.0
- [ ] Backward compatibility notes

**CLI Help**:
- [ ] Verify all commands have help text
- [ ] Verify all options have help text
- [ ] Verify examples are clear
- [ ] Test `mcpi --help`, `mcpi catalog --help`, etc.

**Example Documentation**:

```markdown
## Multiple Catalogs

MCPI v0.4.0 introduces support for multiple server catalogs:

### Available Catalogs

- **official**: Built-in catalog of MCP servers maintained by the MCPI community
- **local**: Your custom servers (stored in `~/.mcpi/catalogs/local/`)

### Managing Catalogs

List all catalogs:
```bash
mcpi catalog list
```

Show catalog details:
```bash
mcpi catalog info official
mcpi catalog info local
```

### Using Catalogs

Search in specific catalog:
```bash
mcpi search filesystem --catalog official
mcpi search my-server --catalog local
```

Search across all catalogs:
```bash
mcpi search database --all-catalogs
```

Add server from specific catalog:
```bash
mcpi add filesystem --catalog official
```

### Migration from v0.3.0

No action required! Your existing code continues to work:

- `mcpi search` still searches the official catalog by default
- `create_default_catalog()` still works (returns official catalog)
- All existing commands work unchanged

To use the new multi-catalog features, simply add `--catalog` or `--all-catalogs` flags.
```

**Acceptance Criteria**:
- [ ] CLAUDE.md updated with architecture changes
- [ ] README.md updated with user-facing examples
- [ ] CHANGELOG.md updated with release notes
- [ ] CLI help text verified for completeness
- [ ] Migration guide clear and actionable
- [ ] Examples tested and working
- [ ] Documentation reviewed for accuracy

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 3.3"
- STATUS-CATALOG-EVALUATION-2025-11-17-021848.md, Section 10.1

---

### Task 3.4: Manual Testing and Bug Fixes

**Effort**: 1 day
**Priority**: P1 (High)
**Status**: Not Started
**Dependencies**: Task 3.3
**Assignee**: TBD

**Description**:
Manual testing of all features and bug fixes before release.

**Manual Test Checklist**:
- [ ] Fresh install creates local catalog
- [ ] `mcpi catalog list` shows both catalogs
- [ ] `mcpi catalog info official` shows details
- [ ] `mcpi catalog info local` shows details
- [ ] `mcpi search <query>` searches official (default)
- [ ] `mcpi search <query> --catalog local` searches local
- [ ] `mcpi search <query> --all-catalogs` searches both
- [ ] `mcpi info <server>` finds servers in official
- [ ] `mcpi add <server>` adds from official (default)
- [ ] Add custom server to local catalog (manual JSON edit)
- [ ] Search finds custom server in local catalog
- [ ] Local catalog persists across sessions
- [ ] Old code patterns still work (backward compat)
- [ ] Deprecation warnings appear appropriately
- [ ] Error messages are clear and helpful
- [ ] Performance: no noticeable slowdowns

**Bug Fix Checklist**:
- [ ] Fix any bugs discovered in manual testing
- [ ] Add regression tests for bugs
- [ ] Verify fixes don't break other functionality
- [ ] Re-run full test suite after fixes

**Performance Benchmarks**:
- [ ] `mcpi catalog list` runs in <100ms
- [ ] `mcpi search <query>` runs in <500ms (official catalog)
- [ ] `mcpi search <query> --all-catalogs` runs in <1000ms
- [ ] No regression vs. v0.3.0 performance

**Acceptance Criteria**:
- [ ] All manual tests pass
- [ ] All bugs fixed
- [ ] Regression tests added for bugs
- [ ] Performance benchmarks met
- [ ] No regressions vs. v0.3.0
- [ ] Ready for release

**Spec Reference**:
- PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md, Section "Task 3.4"
- User's CLAUDE.md (testing philosophy: "do it right the first time")

---

## Sprint Success Criteria

### Functional Requirements ✅

- [ ] Two catalogs working (official + local)
- [ ] `mcpi catalog list` shows both catalogs
- [ ] `mcpi catalog info <name>` shows catalog details
- [ ] `mcpi search --catalog <name>` searches specific catalog
- [ ] `mcpi search --all-catalogs` searches both catalogs
- [ ] Users can add servers to local catalog (manual JSON edit)
- [ ] Local catalog persists across sessions

### Quality Requirements ✅

- [ ] 100% backward compatibility (no breaking changes)
- [ ] All tests pass (unit, integration, E2E)
- [ ] 100% code coverage for new components
- [ ] All existing tests still pass
- [ ] Documentation complete and accurate
- [ ] Zero performance regression
- [ ] Code passes mypy, black, ruff

### Release Requirements ✅

- [ ] CHANGELOG.md updated
- [ ] Migration guide complete
- [ ] CLI help text verified
- [ ] Manual testing complete
- [ ] All bugs fixed
- [ ] Ready for v0.4.0 release

---

## Definition of Done

A task is "done" when:

1. **Implementation complete** - All code written and working
2. **Tests pass** - Unit, integration, and E2E tests all pass
3. **Code quality** - Passes mypy, black, ruff
4. **Code coverage** - 100% for new code
5. **Documentation** - Inline docs, help text, user docs updated
6. **Review** - Code reviewed (self-review minimum)
7. **Manual testing** - Manually verified to work
8. **No regressions** - Existing functionality still works

---

## Risk Management

### Top Risks This Sprint

1. **Backward compatibility breaks**
   - Mitigation: Extensive testing, deprecation warnings
   - Contingency: Rollback breaking changes

2. **Performance regression**
   - Mitigation: Lazy loading, benchmarking
   - Contingency: Optimize or defer features

3. **Existing tests fail**
   - Mitigation: Incremental updates, careful review
   - Contingency: Fix tests or update implementation

4. **Local catalog initialization fails**
   - Mitigation: Error handling, fallback logic
   - Contingency: Official catalog always works

---

## Daily Checklist

Each day, verify:

- [ ] All tests pass
- [ ] Code formatted (black)
- [ ] No linting errors (ruff)
- [ ] Type checking passes (mypy)
- [ ] Progress documented
- [ ] Blockers identified
- [ ] Help needed communicated

---

## Sprint Retrospective (End of Sprint)

After sprint completion, review:

1. **What went well?**
2. **What didn't go well?**
3. **What should we do differently in Phase 2?**
4. **Did we meet our success criteria?**
5. **Is the feature ready for release?**

---

**Sprint Status**: READY TO START (pending user approval)
**Next Action**: User review and approval to begin implementation

---

*Sprint plan created by: Project Planner Agent*
*Date: 2025-11-17 02:23:52*
*Source: PLAN-CATALOG-IMPLEMENTATION-2025-11-17-022352.md*
