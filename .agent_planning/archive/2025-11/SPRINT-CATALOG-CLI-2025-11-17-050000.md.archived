# Multi-Catalog Phase 1: CLI Integration Sprint

**Date**: 2025-11-17 05:00:00
**Project**: MCPI v0.3.0 → v0.4.0
**Sprint Goal**: Complete CLI integration for multi-catalog MVP
**Source STATUS**: STATUS-2025-11-17-040500.md
**Total Effort**: ~23.5 hours (3-4 days)
**Current Progress**: 46/78 tests passing (59%)

---

## Sprint Overview

### Current State
- ✅ **Backend Complete**: CatalogManager implemented (268 lines, 25/25 tests passing)
- ❌ **CLI Blocked**: 0% complete, all commands missing
- ❌ **User Value**: 0% - users cannot access multi-catalog features

### Critical Blocker
**CATALOG-003** (CLI Context Integration) blocks all remaining work.
- **Effort**: 1.5 hours
- **Impact**: Unblocks 4 tasks, 24 failing tests
- **Priority**: P0 - DO FIRST

### Success Criteria
- [ ] 78/78 tests passing (100%)
- [ ] `mcpi catalog list` shows both catalogs
- [ ] `mcpi search --all-catalogs` works
- [ ] 100% backward compatibility
- [ ] Documentation complete

---

## Day-by-Day Implementation Schedule

### Day 1: Unblock CLI and First User Value (6-8 hours)

**Morning (3 hours): CATALOG-003 - CLI Context Integration**

**What**: Implement `get_catalog_manager(ctx)` and update `get_catalog()`

**Files to modify**:
- `src/mcpi/cli.py` - Add 50 lines
- `src/mcpi/registry/catalog.py` - Add 10 lines (deprecation)

**Implementation steps**:

1. **Add catalog manager context helper** (30 min)
```python
def get_catalog_manager(ctx: click.Context) -> CatalogManager:
    """Lazy initialization of CatalogManager using factory function."""
    if "catalog_manager" not in ctx.obj:
        try:
            from mcpi.registry.catalog_manager import create_default_catalog_manager
            ctx.obj["catalog_manager"] = create_default_catalog_manager()
        except Exception as e:
            if ctx.obj.get("verbose"):
                console.print(f"[red]Error initializing catalog manager: {e}[/red]")
                console.print_exception()
            raise click.ClickException(
                "Failed to initialize catalog manager. "
                "Run with --verbose for details."
            )
    return ctx.obj["catalog_manager"]
```

2. **Update get_catalog() signature** (30 min)
```python
def get_catalog(ctx: click.Context, catalog_name: Optional[str] = None) -> ServerCatalog:
    """Get catalog by name (defaults to official catalog).

    Args:
        ctx: Click context
        catalog_name: Catalog name ("official" or "local"), or None for default

    Returns:
        ServerCatalog instance

    Raises:
        ClickException: If catalog_name is invalid
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

3. **Add deprecation warning** (15 min)
```python
# In src/mcpi/registry/catalog.py
def create_default_catalog(validate_with_cue: bool = True) -> ServerCatalog:
    """Create ServerCatalog with default production catalog path.

    DEPRECATED: Use create_default_catalog_manager() for multi-catalog support.
    This function maintained for backward compatibility.

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

4. **Manual testing** (15 min)
```bash
# Test context loads correctly
mcpi search filesystem  # Should still work (backward compat)

# Test error handling
# (will fail with "No such command 'catalog'" - expected)
```

**Done when**:
- [ ] `get_catalog_manager(ctx)` added to cli.py
- [ ] `get_catalog(ctx, catalog_name=None)` signature updated
- [ ] Backward compatibility verified (existing commands work)
- [ ] Deprecation warning added
- [ ] Code passes black, ruff, mypy

**Expected outcome**: CLI context ready, can start building catalog commands

---

**Afternoon (3-4 hours): CATALOG-004 - Catalog Command Group**

**What**: Implement `mcpi catalog list` and `mcpi catalog info`

**Files to modify**:
- `src/mcpi/cli.py` - Add ~120 lines

**Implementation steps**:

1. **Create catalog command group** (15 min)
```python
@cli.group()
def catalog():
    """Manage MCP server catalogs.

    The catalog system supports multiple server catalogs:
    - official: Built-in catalog of official MCP servers
    - local: Your custom MCP servers

    Examples:
        # List available catalogs
        mcpi catalog list

        # Show catalog details
        mcpi catalog info official
        mcpi catalog info local
    """
    pass
```

2. **Implement catalog list command** (90 min)
```python
@catalog.command("list")
@click.pass_context
def catalog_list(ctx):
    """List all available catalogs.

    Shows catalog name, type, server count, and description.

    Examples:
        mcpi catalog list
    """
    try:
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

    except Exception as e:
        if ctx.obj.get("verbose"):
            console.print(f"[red]Error listing catalogs: {e}[/red]")
            console.print_exception()
        raise click.ClickException(f"Failed to list catalogs: {e}")
```

3. **Implement catalog info command** (90 min)
```python
@catalog.command("info")
@click.argument("name", type=click.Choice(["official", "local"], case_sensitive=False))
@click.pass_context
def catalog_info(ctx, name: str):
    """Show detailed information about a catalog.

    Displays:
    - Catalog path
    - Server count
    - Categories
    - Sample servers

    Examples:
        mcpi catalog info official
        mcpi catalog info local
    """
    try:
        manager = get_catalog_manager(ctx)
        cat = manager.get_catalog(name)

        if not cat:
            raise click.ClickException(f"Catalog '{name}' not found")

        # Get catalog metadata
        servers = cat.list_servers()
        categories = cat.list_categories()

        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        # Header panel
        header = f"[bold cyan]{name.upper()}[/bold cyan] Catalog"
        info_text = f"Path: {cat.catalog_path}\nServers: {len(servers)}\nCategories: {len(categories)}"
        console.print(Panel(info_text, title=header))

        # Top categories table
        if categories:
            console.print("\n[bold]Top Categories:[/bold]")
            table = Table(show_header=True)
            table.add_column("Category", style="cyan")
            table.add_column("Count", justify="right", style="green")

            sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_cats[:10]:
                table.add_row(category, str(count))

            console.print(table)

        # Sample servers
        if servers:
            console.print("\n[bold]Sample Servers:[/bold]")
            for server_id, server in servers[:5]:
                console.print(f"  • [cyan]{server_id}[/cyan]: {server.description}")

            if len(servers) > 5:
                console.print(f"  ... and {len(servers) - 5} more")

    except click.ClickException:
        raise
    except Exception as e:
        if ctx.obj.get("verbose"):
            console.print(f"[red]Error showing catalog info: {e}[/red]")
            console.print_exception()
        raise click.ClickException(f"Failed to show catalog info: {e}")
```

4. **Manual testing** (15 min)
```bash
# Test catalog list
mcpi catalog list
# Expected: Table showing official (42 servers) and local (0 servers)

# Test catalog info
mcpi catalog info official
mcpi catalog info local

# Test error handling
mcpi catalog info unknown  # Should show error
```

**Done when**:
- [ ] `mcpi catalog` command group exists
- [ ] `mcpi catalog list` shows Rich table with both catalogs
- [ ] `mcpi catalog info <name>` shows detailed information
- [ ] Help text includes examples
- [ ] Error handling works for invalid catalog names
- [ ] Manual testing passes

**Expected outcome**: Users can see both catalogs and explore them

---

### Day 2: Multi-Catalog Search (6-8 hours)

**CATALOG-005: Add --catalog Flags to Existing Commands**

**Morning (4 hours): Update search command**

**What**: Add `--catalog` and `--all-catalogs` flags to search

**Files to modify**:
- `src/mcpi/cli.py` - Update search command (~80 lines)

**Implementation steps**:

1. **Add flags to search command** (30 min)
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
    """Search for MCP servers in catalogs.

    By default, searches the official catalog. Use --catalog to search
    a specific catalog, or --all-catalogs to search all catalogs.

    Examples:
        # Search official catalog (default)
        mcpi search filesystem

        # Search local catalog
        mcpi search filesystem --catalog local

        # Search all catalogs
        mcpi search filesystem --all-catalogs
    """
    # Validate flags
    if catalog and all_catalogs:
        raise click.ClickException(
            "--catalog and --all-catalogs are mutually exclusive"
        )

    # ... (implementation below)
```

2. **Implement all-catalogs search** (90 min)
```python
    if all_catalogs:
        # Search all catalogs
        try:
            manager = get_catalog_manager(ctx)
            results = manager.search_all(query)

            if not results:
                click.echo(f"No servers found matching '{query}'")
                return

            # Group results by catalog for display
            from collections import defaultdict
            from rich.console import Console
            from rich.table import Table

            console = Console()
            by_catalog = defaultdict(list)

            for catalog_name, server_id, server in results:
                by_catalog[catalog_name].append((server_id, server))

            # Display results grouped by catalog
            for catalog_name in ["official", "local"]:
                if catalog_name not in by_catalog:
                    continue

                # Header for this catalog
                console.print(f"\n[bold cyan]{catalog_name.upper()} CATALOG[/bold cyan]")

                # Table for servers in this catalog
                table = Table(show_header=True)
                table.add_column("Server ID", style="cyan")
                table.add_column("Description", style="white")

                for server_id, server in by_catalog[catalog_name]:
                    table.add_row(server_id, server.description)

                console.print(table)

        except Exception as e:
            if ctx.obj.get("verbose"):
                console.print(f"[red]Error searching catalogs: {e}[/red]")
                console.print_exception()
            raise click.ClickException(f"Search failed: {e}")
```

3. **Update single-catalog search** (60 min)
```python
    else:
        # Search single catalog (default: official)
        try:
            cat = get_catalog(ctx, catalog)
            results = cat.search_servers(query)

            if not results:
                catalog_display = catalog or "official"
                click.echo(f"No servers found matching '{query}' in {catalog_display} catalog")
                return

            # Display results (existing Rich table pattern)
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title=f"Search Results: '{query}'", show_header=True)

            table.add_column("Server ID", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Categories", style="magenta")

            for server_id, server in results:
                categories_str = ", ".join(server.categories) if server.categories else ""
                table.add_row(server_id, server.description, categories_str)

            console.print(table)

        except click.ClickException:
            raise
        except Exception as e:
            if ctx.obj.get("verbose"):
                console.print(f"[red]Error searching catalog: {e}[/red]")
                console.print_exception()
            raise click.ClickException(f"Search failed: {e}")
```

4. **Manual testing** (30 min)
```bash
# Test default search (official)
mcpi search filesystem

# Test catalog-specific search
mcpi search filesystem --catalog official
mcpi search filesystem --catalog local

# Test all-catalogs search
mcpi search filesystem --all-catalogs

# Test error handling
mcpi search filesystem --catalog official --all-catalogs  # Should error
```

**Done when**:
- [ ] `--catalog` flag works on search command
- [ ] `--all-catalogs` flag works on search command
- [ ] Flags are mutually exclusive
- [ ] Results grouped by catalog for --all-catalogs
- [ ] Default behavior unchanged (searches official)
- [ ] Help text updated with examples
- [ ] Manual testing passes

---

**Afternoon (2-3 hours): Update info and add commands**

**What**: Add `--catalog` flag to info and add commands

**Files to modify**:
- `src/mcpi/cli.py` - Update info and add commands (~40 lines each)

**Implementation steps**:

1. **Update info command** (60 min)
```python
@cli.command()
@click.argument("server-id")
@click.option(
    "--catalog",
    type=click.Choice(["official", "local"], case_sensitive=False),
    help="Use specific catalog (default: official)",
)
@click.pass_context
def info(ctx, server_id: str, catalog: Optional[str]):
    """Show detailed information about a server.

    By default, searches the official catalog. Use --catalog to search
    a different catalog.

    Examples:
        # Get info from official catalog (default)
        mcpi info filesystem

        # Get info from local catalog
        mcpi info my-server --catalog local
    """
    try:
        cat = get_catalog(ctx, catalog)
        server = cat.get_server(server_id)

        if not server:
            catalog_display = catalog or "official"
            raise click.ClickException(
                f"Server '{server_id}' not found in {catalog_display} catalog"
            )

        # Display server info (existing Rich panel pattern)
        # ... (keep existing display logic)

    except click.ClickException:
        raise
    except Exception as e:
        if ctx.obj.get("verbose"):
            console.print(f"[red]Error getting server info: {e}[/red]")
            console.print_exception()
        raise click.ClickException(f"Failed to get server info: {e}")
```

2. **Update add command** (60 min)
```python
@cli.command()
@click.argument("server-id")
@click.option(
    "--catalog",
    type=click.Choice(["official", "local"], case_sensitive=False),
    help="Use specific catalog (default: official)",
)
# ... (other existing options)
@click.pass_context
def add(ctx, server_id: str, catalog: Optional[str], **kwargs):
    """Add an MCP server to client configuration.

    By default, looks up the server in the official catalog. Use --catalog
    to look up from a different catalog.

    Examples:
        # Add from official catalog (default)
        mcpi add filesystem

        # Add from local catalog
        mcpi add my-server --catalog local
    """
    try:
        cat = get_catalog(ctx, catalog)
        server = cat.get_server(server_id)

        if not server:
            catalog_display = catalog or "official"
            raise click.ClickException(
                f"Server '{server_id}' not found in {catalog_display} catalog"
            )

        # Rest of existing add logic...
        # ... (keep existing installation logic)

    except click.ClickException:
        raise
    except Exception as e:
        if ctx.obj.get("verbose"):
            console.print(f"[red]Error adding server: {e}[/red]")
            console.print_exception()
        raise click.ClickException(f"Failed to add server: {e}")
```

3. **Manual testing** (30 min)
```bash
# Test info with catalog flag
mcpi info filesystem
mcpi info filesystem --catalog official

# Test add with catalog flag (dry-run or test scope)
mcpi add filesystem --catalog official --dry-run

# Test error handling
mcpi info unknown-server --catalog local  # Should error
```

**Done when**:
- [ ] `--catalog` flag works on info command
- [ ] `--catalog` flag works on add command
- [ ] Default behavior unchanged (uses official)
- [ ] Help text updated
- [ ] Manual testing passes

---

### Day 3: Testing and Quality (6-8 hours)

**CATALOG-006 & CATALOG-007: Fix All Tests**

**Morning (3-4 hours): Fix CLI integration tests**

**What**: Fix 24 failing CLI integration tests

**Files to verify**:
- `tests/test_cli_catalog_commands.py` - 27 tests

**Implementation steps**:

1. **Run test suite** (15 min)
```bash
pytest tests/test_cli_catalog_commands.py -v --tb=short
```

2. **Fix catalog list tests** (45 min)
```python
# Expected failures before implementation:
# - test_catalog_list_shows_both_catalogs
# - test_catalog_list_table_format
# - test_catalog_list_server_counts

# After implementation, these should pass
# Verify Rich table output matches expected format
```

3. **Fix catalog info tests** (45 min)
```python
# Expected failures before implementation:
# - test_catalog_info_official
# - test_catalog_info_local
# - test_catalog_info_shows_path
# - test_catalog_info_shows_categories
# - test_catalog_info_invalid_name

# After implementation, these should pass
```

4. **Fix search flag tests** (60 min)
```python
# Expected failures before implementation:
# - test_search_with_catalog_flag_official
# - test_search_with_catalog_flag_local
# - test_search_all_catalogs_flag
# - test_search_all_catalogs_groups_by_catalog
# - test_search_catalog_flags_mutually_exclusive

# After implementation, these should pass
```

5. **Fix info and add flag tests** (45 min)
```python
# Expected failures before implementation:
# - test_info_with_catalog_flag
# - test_add_with_catalog_flag

# After implementation, these should pass
```

6. **Run full CLI test suite** (15 min)
```bash
pytest tests/test_cli_catalog_commands.py -v
# Expected: 27/27 passing
```

**Done when**:
- [ ] 27/27 CLI integration tests passing
- [ ] No regressions in other test files
- [ ] Test execution time < 5 seconds

---

**Afternoon (3-4 hours): Fix E2E tests and verify backward compatibility**

**What**: Fix 8 failing E2E tests, verify backward compat

**Files to verify**:
- `tests/test_multi_catalog_e2e.py` - 26 tests

**Implementation steps**:

1. **Run E2E test suite** (15 min)
```bash
pytest tests/test_multi_catalog_e2e.py -v --tb=short
```

2. **Fix catalog workflow tests** (90 min)
```python
# Expected failures before implementation:
# - test_catalog_list_workflow
# - test_catalog_info_workflow
# - test_search_all_catalogs_workflow
# - test_add_from_local_catalog_workflow

# After implementation, these should pass
# May need to adjust test expectations if CLI output changed
```

3. **Verify backward compatibility tests** (60 min)
```python
# These should already be passing:
# - test_existing_search_still_works
# - test_existing_info_still_works
# - test_existing_add_still_works
# - test_create_default_catalog_shows_deprecation

# If failing, fix CLI implementation to preserve backward compat
```

4. **Fix any remaining E2E failures** (60 min)
```bash
# Debug and fix any unexpected test failures
# Common issues:
# - Output format changes
# - Error message changes
# - Timing issues
```

5. **Run full test suite** (15 min)
```bash
pytest tests/test_catalog_manager.py tests/test_cli_catalog_commands.py tests/test_multi_catalog_e2e.py -v
# Expected: 78/78 passing
```

**Done when**:
- [ ] 26/26 E2E tests passing
- [ ] All backward compatibility tests passing
- [ ] 78/78 total multi-catalog tests passing
- [ ] No regressions in existing test suite

---

### Day 4: Documentation and Release (4-6 hours)

**CATALOG-008 & CATALOG-009: Documentation and Manual Testing**

**Morning (3-4 hours): Documentation**

**What**: Update all documentation for multi-catalog feature

**Files to update**:
- `CLAUDE.md` - Architecture section
- `README.md` - Usage examples
- `CHANGELOG.md` - v0.4.0 section
- CLI help text (verify)

**Implementation steps**:

1. **Update CLAUDE.md** (90 min)
```markdown
## Project Architecture

### Core Architecture: Multi-Catalog System

MCPI supports multiple server catalogs:

**Built-in Catalogs**:
- `official`: Official MCP server catalog (bundled with MCPI)
- `local`: User's custom MCP servers (~/.mcpi/catalogs/local/)

**Catalog Manager** (`mcpi.registry.catalog_manager`):
- Manages multiple catalogs with lazy loading
- Case-insensitive catalog name lookup
- Search across all catalogs
- Factory functions for production and testing

**CLI Commands**:
```bash
# List available catalogs
mcpi catalog list

# Show catalog details
mcpi catalog info official
mcpi catalog info local

# Search in specific catalog
mcpi search <query> --catalog local

# Search all catalogs
mcpi search <query> --all-catalogs
```

**Backward Compatibility**:
- Existing commands work unchanged (use official catalog by default)
- `create_default_catalog()` deprecated but functional
- Deprecation warnings guide users to new API
```

2. **Update README.md** (60 min)
```markdown
## Multi-Catalog Support

MCPI supports multiple server catalogs, allowing you to organize servers from
different sources:

### Built-in Catalogs

**Official Catalog**: Curated list of official MCP servers
**Local Catalog**: Your custom MCP servers (stored in ~/.mcpi/catalogs/local/)

### Working with Catalogs

```bash
# List available catalogs
mcpi catalog list

# View catalog details
mcpi catalog info official

# Search official catalog (default)
mcpi search filesystem

# Search local catalog
mcpi search my-server --catalog local

# Search all catalogs
mcpi search database --all-catalogs
```

### Adding Custom Servers to Local Catalog

The local catalog is automatically created at `~/.mcpi/catalogs/local/catalog.json`.
You can manually add servers by editing this file:

```json
{
  "my-server": {
    "description": "My custom MCP server",
    "command": "node",
    "args": ["path/to/server.js"],
    "repository": "https://github.com/me/my-server",
    "categories": ["custom"]
  }
}
```

Then use it like any other server:

```bash
mcpi search my-server --catalog local
mcpi add my-server --catalog local
```
```

3. **Update CHANGELOG.md** (30 min)
```markdown
# Changelog

## [0.4.0] - 2025-11-17

### Added
- Multi-catalog support for organizing MCP servers from different sources
- Built-in `official` and `local` catalogs
- New `mcpi catalog` command group:
  - `mcpi catalog list` - List available catalogs
  - `mcpi catalog info <name>` - Show catalog details
- `--catalog` flag for `search`, `info`, and `add` commands
- `--all-catalogs` flag for `search` command to search all catalogs
- Local catalog auto-initialized at `~/.mcpi/catalogs/local/catalog.json`
- CatalogManager class for managing multiple catalogs (DIP-compliant)

### Changed
- Default catalog behavior unchanged (commands use official catalog by default)
- `create_default_catalog()` deprecated in favor of `create_default_catalog_manager()`

### Deprecated
- `create_default_catalog()` - Use `create_default_catalog_manager()` instead

### Migration Guide (v0.3.0 → v0.4.0)
- All existing commands work unchanged
- To use multiple catalogs, use new `--catalog` flags
- Library users should migrate to `create_default_catalog_manager()`
- Deprecation warnings provide migration guidance
```

4. **Verify CLI help text** (30 min)
```bash
# Verify help text includes new features
mcpi --help
mcpi catalog --help
mcpi catalog list --help
mcpi catalog info --help
mcpi search --help  # Should show --catalog and --all-catalogs
mcpi info --help    # Should show --catalog
mcpi add --help     # Should show --catalog
```

**Done when**:
- [ ] CLAUDE.md updated with multi-catalog architecture
- [ ] README.md updated with usage examples
- [ ] CHANGELOG.md has v0.4.0 section with migration guide
- [ ] All CLI help text verified

---

**Afternoon (2 hours): Manual Testing and Bug Fixes**

**What**: Manual end-to-end testing, fix any bugs

**Test scenarios**:

1. **Fresh install scenario** (15 min)
```bash
# Simulate fresh install (clean local catalog)
rm -rf ~/.mcpi/catalogs/local/

# Run catalog list
mcpi catalog list
# Expected: Shows official (42 servers) and local (0 servers)
# Verify: Local catalog auto-created at ~/.mcpi/catalogs/local/catalog.json
```

2. **Basic catalog operations** (15 min)
```bash
# List catalogs
mcpi catalog list

# Show catalog info
mcpi catalog info official
mcpi catalog info local

# Verify output formatting, counts, categories
```

3. **Search operations** (20 min)
```bash
# Search official (default)
mcpi search filesystem

# Search with catalog flag
mcpi search filesystem --catalog official
mcpi search filesystem --catalog local

# Search all catalogs
mcpi search filesystem --all-catalogs

# Verify grouping, formatting, counts
```

4. **Info and add operations** (20 min)
```bash
# Get server info
mcpi info filesystem
mcpi info filesystem --catalog official

# Add server (test in project-mcp scope)
cd /tmp/test-project
mcpi add filesystem --scope project-mcp
mcpi list --scope project-mcp

# Verify server added correctly
```

5. **Local catalog workflow** (20 min)
```bash
# Manually add server to local catalog
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

# Search local catalog
mcpi search test-server --catalog local
mcpi search test --all-catalogs

# Get info
mcpi info test-server --catalog local

# Verify server appears correctly
```

6. **Backward compatibility** (15 min)
```bash
# Verify old commands still work
mcpi search filesystem  # Uses official by default
mcpi info filesystem    # Uses official by default
mcpi add filesystem --scope project-mcp  # Uses official by default

# Verify no breaking changes
```

7. **Error handling** (15 min)
```bash
# Test invalid catalog names
mcpi catalog info unknown  # Should error with helpful message
mcpi search test --catalog unknown  # Should error

# Test mutually exclusive flags
mcpi search test --catalog official --all-catalogs  # Should error

# Test missing servers
mcpi info unknown-server --catalog local  # Should error with helpful message

# Verify error messages are clear and helpful
```

8. **Performance check** (10 min)
```bash
# Benchmark commands
time mcpi catalog list  # Should be < 100ms
time mcpi search filesystem  # Should be < 500ms
time mcpi search filesystem --all-catalogs  # Should be < 1000ms

# Compare with v0.3.0 baseline
# Verify no significant regression
```

**Bug fix process**:
- Document any bugs found
- Prioritize by severity (blocking vs. minor)
- Fix blocking bugs immediately
- File issues for minor bugs (can fix later)
- Re-test after fixes

**Done when**:
- [ ] All manual test scenarios pass
- [ ] No blocking bugs found
- [ ] Error messages are clear and helpful
- [ ] Performance benchmarks met (< 100ms, < 500ms, < 1s)
- [ ] Backward compatibility verified
- [ ] Local catalog workflow works end-to-end

---

## Success Metrics

### Implementation Complete When:
- [ ] 78/78 tests passing (100%)
- [ ] All 9 tasks complete (CATALOG-001 through CATALOG-009)
- [ ] `mcpi catalog list` shows both catalogs
- [ ] `mcpi search --all-catalogs` searches both catalogs
- [ ] `--catalog` flag works on search/info/add
- [ ] Local catalog auto-initializes
- [ ] 100% backward compatibility
- [ ] Documentation complete
- [ ] Manual testing passes
- [ ] No performance regression

### Quality Gates:
- [ ] Code passes mypy type checking
- [ ] Code formatted with black
- [ ] Code passes ruff linting
- [ ] All tests run in < 10 seconds total
- [ ] No regressions in existing test suite (752 tests)

### User Value Delivered:
- [ ] Users can list available catalogs
- [ ] Users can explore catalog details
- [ ] Users can search specific catalogs
- [ ] Users can search all catalogs
- [ ] Users can add custom servers to local catalog
- [ ] Existing workflows continue to work

---

## Risk Management

### Known Risks

**Risk 1: Backward compatibility breaks**
- **Probability**: LOW
- **Impact**: HIGH
- **Mitigation**: Optional parameters, deprecation warnings, extensive testing
- **Contingency**: Rollback CLI changes, keep only backend implementation

**Risk 2: Tests fail unexpectedly**
- **Probability**: MEDIUM
- **Impact**: MEDIUM
- **Mitigation**: Tests already written, incremental debugging
- **Contingency**: Fix tests or implementation, extend timeline if needed

**Risk 3: Performance regression**
- **Probability**: LOW
- **Impact**: MEDIUM
- **Mitigation**: Lazy loading, benchmarking during manual testing
- **Contingency**: Profile and optimize, or defer non-critical features

**Risk 4: Timeline slip**
- **Probability**: MEDIUM
- **Impact**: MEDIUM
- **Mitigation**: Clear task breakdown, daily progress tracking
- **Contingency**: Reduce documentation scope, defer minor polish items

### Daily Checkpoints

**End of Day 1**:
- [ ] CATALOG-003 complete
- [ ] CATALOG-004 complete
- [ ] `mcpi catalog list` works
- [ ] Can proceed to Day 2

**End of Day 2**:
- [ ] CATALOG-005 complete
- [ ] `mcpi search --all-catalogs` works
- [ ] All CLI commands support --catalog flag
- [ ] Can proceed to Day 3

**End of Day 3**:
- [ ] CATALOG-006 and 007 complete
- [ ] 78/78 tests passing
- [ ] No regressions
- [ ] Can proceed to Day 4

**End of Day 4**:
- [ ] CATALOG-008 and 009 complete
- [ ] Documentation complete
- [ ] Manual testing passes
- [ ] Ready for release

---

## Next Actions

### Immediate (Right Now)
1. **Read this sprint plan** to understand the 4-day schedule
2. **Start Day 1, Morning** - CATALOG-003 (CLI Context Integration)
3. **Set timer for 1.5 hours** - this is a focused, time-boxed task

### Day 1 Morning Checklist
- [ ] Open `src/mcpi/cli.py`
- [ ] Add `get_catalog_manager(ctx)` function
- [ ] Update `get_catalog(ctx, catalog_name=None)` signature
- [ ] Add deprecation warning to `create_default_catalog()`
- [ ] Test manually: `mcpi search filesystem` (should still work)
- [ ] Run: `black src/ && ruff check src/ && mypy src/`
- [ ] Verify: No errors, backward compat preserved

### Progress Tracking
Use `git commit` after each completed task:
- After CATALOG-003: "feat(catalog): add CLI context integration for multi-catalog"
- After CATALOG-004: "feat(catalog): add catalog list and info commands"
- After CATALOG-005: "feat(catalog): add --catalog flags to search/info/add"
- After CATALOG-006/007: "test(catalog): fix all CLI integration and E2E tests"
- After CATALOG-008/009: "docs(catalog): complete multi-catalog documentation"

---

## Appendix: Quick Reference

### Files to Modify
- `src/mcpi/cli.py` - Main CLI implementation (~350 lines added)
- `src/mcpi/registry/catalog.py` - Deprecation warning (~10 lines)
- `CLAUDE.md` - Architecture docs (~100 lines)
- `README.md` - Usage examples (~50 lines)
- `CHANGELOG.md` - Release notes (~30 lines)

### Tests to Fix
- `tests/test_catalog_manager.py` - 25/25 passing ✅
- `tests/test_cli_catalog_commands.py` - 3/27 passing → 27/27
- `tests/test_multi_catalog_e2e.py` - 18/26 passing → 26/26

### Key APIs
```python
# Context helpers (cli.py)
manager = get_catalog_manager(ctx)
catalog = get_catalog(ctx, catalog_name=None)

# CatalogManager API (catalog_manager.py)
catalog = manager.get_catalog("official" | "local")
catalogs = manager.list_catalogs()  # List[CatalogInfo]
results = manager.search_all(query)  # List[(name, id, server)]
```

### Manual Test Commands
```bash
# Essential tests
mcpi catalog list
mcpi catalog info official
mcpi search filesystem --all-catalogs
mcpi search filesystem --catalog local

# Backward compat
mcpi search filesystem  # Should use official by default
mcpi info filesystem    # Should use official by default

# Performance
time mcpi catalog list  # < 100ms
time mcpi search filesystem --all-catalogs  # < 1s
```

---

**Sprint Status**: READY TO START
**Next Action**: Begin Day 1, CATALOG-003 (CLI Context Integration)
**Estimated Completion**: 3-4 days from start
**Confidence**: HIGH (95%)

---

*Sprint plan created by: Project Planner Agent*
*Date: 2025-11-17 05:00:00*
*Source: STATUS-2025-11-17-040500.md*
*Focus: CLI Integration for Multi-Catalog MVP*
