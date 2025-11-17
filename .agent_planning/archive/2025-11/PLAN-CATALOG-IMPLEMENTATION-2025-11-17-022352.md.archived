# Multi-Catalog Feature Implementation Plan

**Date**: 2025-11-17 02:23:52
**Project**: MCPI v0.4.0 → v0.6.0
**Feature**: Multi-catalog support with git-based synchronization
**Source STATUS**: STATUS-CATALOG-EVALUATION-2025-11-17-021848.md
**Spec**: CLAUDE.md (Project Architecture, DIP patterns)
**Planning Approach**: Phased implementation with pragmatic MVP first

---

## Executive Summary

### Acknowledgment of Evaluation

The STATUS evaluation (STATUS-CATALOG-EVALUATION-2025-11-17-021848.md) **recommends DEFERRING** this feature to v0.6.0+ after completing DIP Phases 2-4. The evaluation identifies:

- **Major architectural changes** spanning catalog management, CLI, DI, and filesystem
- **4-6 weeks full implementation** vs. **2-3 weeks MVP**
- **Breaking changes** to schema format and CLI semantics
- **48 test files** requiring updates
- **HIGH complexity** with incomplete DIP foundation

### User's Explicit Request

Despite the evaluation's recommendation, the user has **explicitly requested** immediate implementation with these requirements:

1. Multiple catalogs support
2. Default 'local' catalog for user customizations
3. Catalogs stored outside application (git repos)
4. Well-defined, versioned schema
5. Git-based synchronization
6. Local changes don't affect remote catalogs

### Pragmatic Strategy: Phased Approach

**Decision**: Proceed with **3-phase implementation** that:

1. **Phase 1 (v0.4.0)**: MVP Foundation (2-3 weeks) - Core multi-catalog with minimal scope
2. **Phase 2 (v0.5.0)**: Git Integration (2-3 weeks) - Add git synchronization
3. **Phase 3 (v0.6.0)**: Advanced Features (2-3 weeks) - Schema versioning, overlays, polish

**Rationale**:
- Delivers user value incrementally
- Allows feedback and course correction
- Reduces risk of big-bang failure
- Aligns with "do it right the first time" philosophy
- Each phase is independently testable and shippable
- Total timeline: 6-9 weeks vs. 4-6 weeks (controlled risk increase)

---

## Phase 1: MVP Foundation (v0.4.0)

**Timeline**: 2-3 weeks
**Goal**: Basic multi-catalog support with two catalogs (official + local)
**Priority**: P0 (Foundation for all subsequent work)

### Scope Constraints (MVP)

**IN SCOPE**:
- Two catalogs only: `official` (built-in) + `local` (user)
- Simple catalog manager (no complex discovery)
- Basic CLI commands: `catalog list`, `catalog info`
- `--catalog` flag for search/add operations
- Local catalog for user servers
- Keep v1 schema format (no breaking changes yet)
- DIP patterns: All new components use dependency injection

**OUT OF SCOPE** (deferred to Phase 2-3):
- Git integration (manual setup only)
- Arbitrary number of catalogs
- Catalog add/remove operations
- Schema versioning and migration
- Overlay mechanism
- Auto-sync functionality

### Architecture Design

#### 1. CatalogManager (New Component)

**File**: `src/mcpi/registry/catalog_manager.py`

```python
"""Multi-catalog management."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .catalog import ServerCatalog


@dataclass
class CatalogInfo:
    """Metadata about a catalog."""
    name: str
    path: Path
    type: str  # "builtin", "local"
    description: str
    server_count: int


class CatalogManager:
    """Manages multiple server catalogs (MVP: 2 catalogs only)."""

    def __init__(self, official_path: Path, local_path: Path):
        """Initialize with explicit paths for DI.

        Args:
            official_path: Path to official catalog
            local_path: Path to local (user) catalog
        """
        self.official_path = official_path
        self.local_path = local_path
        self._official: Optional[ServerCatalog] = None
        self._local: Optional[ServerCatalog] = None
        self._default_catalog = "official"

    def get_catalog(self, name: str) -> Optional[ServerCatalog]:
        """Get catalog by name (lazy loading)."""
        if name == "official":
            if self._official is None:
                self._official = ServerCatalog(
                    catalog_path=self.official_path,
                    validate_with_cue=True
                )
                self._official.load_catalog()
            return self._official
        elif name == "local":
            if self._local is None:
                self._local = ServerCatalog(
                    catalog_path=self.local_path,
                    validate_with_cue=False  # Local catalog is user-controlled
                )
                self._local.load_catalog()
            return self._local
        return None

    def get_default_catalog(self) -> ServerCatalog:
        """Get the default catalog."""
        return self.get_catalog(self._default_catalog)

    def list_catalogs(self) -> List[CatalogInfo]:
        """List available catalogs (MVP: returns 2 catalogs)."""
        catalogs = []

        # Official catalog
        official = self.get_catalog("official")
        catalogs.append(CatalogInfo(
            name="official",
            path=self.official_path,
            type="builtin",
            description="Official MCP server catalog",
            server_count=len(official.list_servers())
        ))

        # Local catalog
        local = self.get_catalog("local")
        catalogs.append(CatalogInfo(
            name="local",
            path=self.local_path,
            type="local",
            description="Your custom MCP servers",
            server_count=len(local.list_servers())
        ))

        return catalogs

    def search_all(self, query: str) -> List[tuple[str, str, MCPServer]]:
        """Search across all catalogs.

        Returns:
            List of (catalog_name, server_id, server) tuples
        """
        results = []

        for catalog_name in ["official", "local"]:
            catalog = self.get_catalog(catalog_name)
            for server_id, server in catalog.search_servers(query):
                results.append((catalog_name, server_id, server))

        return results
```

#### 2. Factory Functions (Updated)

**File**: `src/mcpi/registry/catalog_manager.py` (continued)

```python
def create_default_catalog_manager() -> CatalogManager:
    """Create CatalogManager with default production paths.

    Factory function for production use. Handles:
    - Official catalog from package data
    - Local catalog from ~/.mcpi/catalogs/local
    - Auto-initialization of local catalog
    """
    # Official catalog (existing location)
    package_dir = Path(__file__).parent.parent.parent.parent
    official_path = package_dir / "data" / "catalog.json"

    # Local catalog (new user directory)
    local_dir = Path.home() / ".mcpi" / "catalogs" / "local"
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / "catalog.json"

    # Initialize local catalog if it doesn't exist
    if not local_path.exists():
        local_path.write_text("{}")

    return CatalogManager(
        official_path=official_path,
        local_path=local_path
    )


def create_test_catalog_manager(
    official_path: Path,
    local_path: Path
) -> CatalogManager:
    """Create CatalogManager for testing with custom paths."""
    return CatalogManager(
        official_path=official_path,
        local_path=local_path
    )
```

#### 3. Backward Compatibility

**File**: `src/mcpi/registry/catalog.py` (update existing factory)

```python
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

    # Return official catalog from manager
    manager = create_default_catalog_manager()
    return manager.get_catalog("official")
```

### CLI Changes

#### 1. Update get_catalog() Context Helper

**File**: `src/mcpi/cli.py` (update existing)

```python
def get_catalog_manager(ctx: click.Context) -> CatalogManager:
    """Lazy initialization of CatalogManager."""
    if "catalog_manager" not in ctx.obj:
        ctx.obj["catalog_manager"] = create_default_catalog_manager()
    return ctx.obj["catalog_manager"]


def get_catalog(ctx: click.Context, catalog_name: Optional[str] = None) -> ServerCatalog:
    """Get catalog by name (defaults to official catalog).

    Args:
        ctx: Click context
        catalog_name: Catalog name ("official" or "local"), or None for default

    Returns:
        ServerCatalog instance
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

#### 2. Add --catalog Flag to Existing Commands

**File**: `src/mcpi/cli.py` (update existing commands)

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
    """Search for MCP servers."""
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


@cli.command()
@click.argument("server-id")
@click.option(
    "--catalog",
    type=click.Choice(["official", "local"], case_sensitive=False),
    help="Use specific catalog (default: official)",
)
@click.pass_context
def info(ctx, server_id: str, catalog: Optional[str]):
    """Show detailed information about a server."""
    cat = get_catalog(ctx, catalog)
    server = cat.get_server(server_id)

    if not server:
        click.echo(f"Server '{server_id}' not found in catalog")
        return

    # Display server info (existing logic)
    # ...
```

#### 3. New catalog Subcommand Group

**File**: `src/mcpi/cli.py` (new)

```python
@cli.group()
def catalog():
    """Manage MCP server catalogs."""
    pass


@catalog.command("list")
@click.pass_context
def catalog_list(ctx):
    """List all available catalogs."""
    manager = get_catalog_manager(ctx)
    catalogs = manager.list_catalogs()

    # Display as table
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Available Catalogs")

    table.add_column("Name", style="cyan")
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


@catalog.command("info")
@click.argument("name", type=click.Choice(["official", "local"]))
@click.pass_context
def catalog_info(ctx, name: str):
    """Show detailed information about a catalog."""
    manager = get_catalog_manager(ctx)
    cat = manager.get_catalog(name)

    if not cat:
        click.echo(f"Catalog '{name}' not found")
        return

    # Display catalog metadata
    servers = cat.list_servers()
    categories = cat.list_categories()

    click.echo(f"Catalog: {name}")
    click.echo(f"Path: {cat.catalog_path}")
    click.echo(f"Servers: {len(servers)}")
    click.echo(f"Categories: {len(categories)}")
    click.echo()

    # Show top categories
    click.echo("Top Categories:")
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_cats[:10]:
        click.echo(f"  {category}: {count}")
```

### Implementation Tasks

#### Week 1: Core Infrastructure

**Task 1.1: CatalogManager Implementation** (2 days)
- Status: Not Started
- Effort: Medium (2 days)
- Dependencies: None
- Spec Reference: Section 2.1 in STATUS evaluation

**Description**: Implement `CatalogManager` class with two-catalog support

**Acceptance Criteria**:
- [ ] CatalogManager class created with DI constructor
- [ ] get_catalog() lazy loads catalogs
- [ ] list_catalogs() returns 2 CatalogInfo objects
- [ ] search_all() searches both catalogs
- [ ] Factory functions created: create_default_catalog_manager(), create_test_catalog_manager()
- [ ] Local catalog auto-initialized on first run

**Technical Notes**:
- Use Path objects for all filesystem paths
- Lazy loading prevents unnecessary I/O
- Local catalog has CUE validation disabled (user-controlled)

---

**Task 1.2: Unit Tests for CatalogManager** (1 day)
- Status: Not Started
- Effort: Small (1 day)
- Dependencies: Task 1.1
- Spec Reference: Section 9.1 in STATUS evaluation

**Description**: Write comprehensive unit tests for CatalogManager

**Acceptance Criteria**:
- [ ] test_get_catalog_lazy_loading()
- [ ] test_list_catalogs()
- [ ] test_search_all_across_catalogs()
- [ ] test_get_default_catalog()
- [ ] test_local_catalog_auto_initialization()
- [ ] test_catalog_not_found()
- [ ] 100% code coverage for CatalogManager

**Technical Notes**:
- Use tmp_path fixture for test catalogs
- Mock filesystem operations where appropriate
- Test both official and local catalog paths

---

**Task 1.3: CLI Context Integration** (1 day)
- Status: Not Started
- Effort: Small (1 day)
- Dependencies: Task 1.1
- Spec Reference: Section 8.1 in STATUS evaluation

**Description**: Update CLI context to use CatalogManager

**Acceptance Criteria**:
- [ ] get_catalog_manager() function added
- [ ] get_catalog() updated to accept catalog_name parameter
- [ ] Backward compatibility preserved (no catalog_name = official)
- [ ] Error handling for unknown catalog names
- [ ] Deprecation warning added to old create_default_catalog()

**Technical Notes**:
- Update cli.py carefully to preserve existing behavior
- Use click.ClickException for user-facing errors
- Test backward compatibility thoroughly

#### Week 2: CLI Commands

**Task 2.1: Add --catalog Flag to Existing Commands** (2 days)
- Status: Not Started
- Effort: Medium (2 days)
- Dependencies: Task 1.3
- Spec Reference: Section 8.1 in STATUS evaluation

**Description**: Add --catalog flag to search, info, add, remove commands

**Acceptance Criteria**:
- [ ] search command has --catalog and --all-catalogs flags
- [ ] info command has --catalog flag
- [ ] add command has --catalog flag
- [ ] remove command has --catalog flag
- [ ] Default behavior unchanged (uses official catalog)
- [ ] --all-catalogs flag shows results grouped by catalog
- [ ] Help text updated for all commands

**Technical Notes**:
- Use click.Choice for catalog validation
- Group multi-catalog results by catalog name
- Preserve Rich table formatting

---

**Task 2.2: Implement catalog Subcommand Group** (2 days)
- Status: Not Started
- Effort: Medium (2 days)
- Dependencies: Task 1.3
- Spec Reference: Section 8.1 in STATUS evaluation

**Description**: Add new `mcpi catalog` command group

**Acceptance Criteria**:
- [ ] catalog list command implemented
- [ ] catalog info command implemented
- [ ] Rich table output for catalog list
- [ ] Detailed metadata display for catalog info
- [ ] Help text and examples added

**Technical Notes**:
- Use Rich library for table display
- Show server counts, categories, and metadata
- Follow existing CLI patterns

---

**Task 2.3: CLI Integration Tests** (1 day)
- Status: Not Started
- Effort: Small (1 day)
- Dependencies: Task 2.1, Task 2.2
- Spec Reference: Section 9.2 in STATUS evaluation

**Description**: Write integration tests for CLI commands

**Acceptance Criteria**:
- [ ] test_search_with_catalog_flag()
- [ ] test_search_all_catalogs()
- [ ] test_info_with_catalog_flag()
- [ ] test_catalog_list_command()
- [ ] test_catalog_info_command()
- [ ] test_add_to_local_catalog()
- [ ] All tests pass

**Technical Notes**:
- Use CliRunner for testing
- Mock CatalogManager for isolation
- Test both success and error paths

#### Week 3: Testing and Documentation

**Task 3.1: End-to-End Tests** (2 days)
- Status: Not Started
- Effort: Medium (2 days)
- Dependencies: All previous tasks
- Spec Reference: Section 9.2 in STATUS evaluation

**Description**: Write end-to-end tests for multi-catalog workflows

**Acceptance Criteria**:
- [ ] test_full_workflow_two_catalogs() - search, add, list across catalogs
- [ ] test_local_catalog_persistence() - add to local, verify on next run
- [ ] test_catalog_priority() - official overrides local for same server ID
- [ ] test_backward_compatibility() - old code still works
- [ ] All E2E tests pass

**Technical Notes**:
- Use MCPTestHarness pattern
- Test complete workflows, not just individual operations
- Verify filesystem state after operations

---

**Task 3.2: Update Existing Tests** (2 days)
- Status: Not Started
- Effort: Medium (2 days)
- Dependencies: Task 3.1
- Spec Reference: Section 9.3 in STATUS evaluation

**Description**: Update existing tests for multi-catalog compatibility

**Acceptance Criteria**:
- [ ] Review all 48 test files referencing catalog
- [ ] Update tests using create_default_catalog()
- [ ] Add multi-catalog test scenarios where appropriate
- [ ] All existing tests pass
- [ ] No test regressions

**Technical Notes**:
- Focus on backward compatibility
- Use deprecation warnings, not errors
- Add TODO comments for Phase 2 enhancements

---

**Task 3.3: Documentation** (2 days)
- Status: Not Started
- Effort: Medium (2 days)
- Dependencies: Task 3.2
- Spec Reference: Section 10.1 in STATUS evaluation

**Description**: Update documentation for multi-catalog feature

**Acceptance Criteria**:
- [ ] CLAUDE.md updated with multi-catalog architecture
- [ ] README.md updated with catalog examples
- [ ] CLI help text verified for all commands
- [ ] Migration guide added for v0.3.0 → v0.4.0
- [ ] CHANGELOG.md updated

**Technical Notes**:
- Emphasize backward compatibility
- Show examples of both old and new patterns
- Document local catalog location and purpose

---

**Task 3.4: Manual Testing and Bug Fixes** (1 day)
- Status: Not Started
- Effort: Small (1 day)
- Dependencies: Task 3.3
- Spec Reference: User's CLAUDE.md (testing philosophy)

**Description**: Manual testing and bug fixes before release

**Acceptance Criteria**:
- [ ] Manual test all CLI commands
- [ ] Test catalog persistence across sessions
- [ ] Test error handling (missing files, permissions)
- [ ] Fix any bugs discovered
- [ ] Performance check (no regressions)

**Technical Notes**:
- Test on clean system (no existing catalogs)
- Test with populated local catalog
- Verify help text and error messages

### Breaking Changes (Phase 1)

**NONE** - Phase 1 is fully backward compatible:

- Old code using `create_default_catalog()` still works (returns official catalog)
- New code can opt-in to multi-catalog via `create_default_catalog_manager()`
- No schema changes (keeping v1 format)
- No CLI breaking changes (new flags are optional)
- Deprecation warnings guide users to new patterns

### Risk Mitigation

**Risk 1**: Local catalog initialization fails
- **Mitigation**: Comprehensive error handling, clear error messages
- **Fallback**: Official catalog always works, local catalog optional

**Risk 2**: Existing tests break
- **Mitigation**: Deprecation warnings, not errors; backward compat factory
- **Validation**: Run full test suite after each change

**Risk 3**: Performance regression
- **Mitigation**: Lazy loading, caching
- **Validation**: Benchmark before/after

### Success Criteria (Phase 1)

1. ✅ Two catalogs working (official + local)
2. ✅ `mcpi catalog list` shows both catalogs
3. ✅ `mcpi search --all-catalogs` searches both
4. ✅ Users can add servers to local catalog
5. ✅ 100% backward compatibility (no breaking changes)
6. ✅ All tests pass (unit, integration, E2E)
7. ✅ Documentation complete
8. ✅ No performance regression

---

## Phase 2: Git Integration (v0.5.0)

**Timeline**: 2-3 weeks
**Goal**: Add git-based catalog synchronization
**Priority**: P1 (High value, builds on Phase 1)

### Scope

**IN SCOPE**:
- Git clone catalog from URL
- Git pull to sync catalog
- Git status to check for updates
- `catalog add` command (git only)
- `catalog sync` command
- `catalog remove` command
- Support for multiple git-based catalogs

**OUT OF SCOPE** (deferred to Phase 3):
- Schema versioning (still using v1)
- Overlay mechanism
- Catalog migration tools
- Auto-sync functionality

### Architecture Design

#### 1. GitCatalogBackend (New Component)

**File**: `src/mcpi/registry/git_backend.py`

```python
"""Git backend for catalog synchronization."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mcpi.clients.types import OperationResult


@dataclass
class GitStatus:
    """Git repository status."""
    is_clean: bool
    ahead: int
    behind: int
    remote_url: Optional[str]


class GitCatalogBackend:
    """Git operations for catalog management."""

    def __init__(self):
        """Initialize git backend."""
        self._check_git_installed()

    def _check_git_installed(self) -> None:
        """Check if git is installed."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Git is not installed")
        except FileNotFoundError:
            raise RuntimeError(
                "Git is not installed. Please install git: https://git-scm.com"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git check timed out")

    def clone(self, url: str, target_dir: Path) -> OperationResult:
        """Clone a git repository."""
        try:
            # Ensure parent directory exists
            target_dir.parent.mkdir(parents=True, exist_ok=True)

            # Clone repository
            result = subprocess.run(
                ["git", "clone", url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                # Parse error message
                stderr = result.stderr.lower()
                if "authentication" in stderr or "permission denied" in stderr:
                    return OperationResult.failure_result(
                        f"Authentication failed for {url}. "
                        "Check your credentials or use SSH keys."
                    )
                elif "network" in stderr or "could not resolve" in stderr:
                    return OperationResult.failure_result(
                        "Network error. Check your internet connection."
                    )
                else:
                    return OperationResult.failure_result(
                        f"Git clone failed: {result.stderr}"
                    )

            return OperationResult.success_result(
                f"Successfully cloned catalog from {url}"
            )

        except subprocess.TimeoutExpired:
            return OperationResult.failure_result(
                "Git clone timed out after 5 minutes. "
                "Check your network connection or try again later."
            )
        except Exception as e:
            return OperationResult.failure_result(f"Unexpected error: {e}")

    def pull(self, catalog_dir: Path) -> OperationResult:
        """Pull latest changes from remote."""
        try:
            # Check if directory is clean first
            status = self.get_status(catalog_dir)
            if not status.is_clean:
                return OperationResult.failure_result(
                    f"Catalog has local modifications. "
                    f"Git catalogs should not be modified directly. "
                    f"Use your 'local' catalog instead."
                )

            # Pull changes
            result = subprocess.run(
                ["git", "pull"],
                cwd=catalog_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return OperationResult.failure_result(
                    f"Git pull failed: {result.stderr}"
                )

            # Parse output to determine if there were updates
            stdout = result.stdout.lower()
            if "already up to date" in stdout or "already up-to-date" in stdout:
                return OperationResult.success_result(
                    "Catalog is already up to date"
                )
            else:
                return OperationResult.success_result(
                    "Catalog updated successfully"
                )

        except subprocess.TimeoutExpired:
            return OperationResult.failure_result(
                "Git pull timed out after 60 seconds."
            )
        except Exception as e:
            return OperationResult.failure_result(f"Unexpected error: {e}")

    def get_status(self, catalog_dir: Path) -> GitStatus:
        """Get git repository status."""
        try:
            # Check if working directory is clean
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=catalog_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            is_clean = len(result.stdout.strip()) == 0

            # Get remote tracking info
            result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
                cwd=catalog_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            ahead, behind = 0, 0
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) == 2:
                    ahead, behind = int(parts[0]), int(parts[1])

            # Get remote URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=catalog_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            remote_url = result.stdout.strip() if result.returncode == 0 else None

            return GitStatus(
                is_clean=is_clean,
                ahead=ahead,
                behind=behind,
                remote_url=remote_url
            )

        except Exception:
            # Return default status on error
            return GitStatus(is_clean=True, ahead=0, behind=0, remote_url=None)
```

#### 2. CatalogManager Extensions

**File**: `src/mcpi/registry/catalog_manager.py` (extend existing)

```python
# Add to CatalogManager class

def __init__(
    self,
    catalog_dir: Path,  # New: directory containing all catalogs
    git_backend: Optional[GitCatalogBackend] = None
):
    """Initialize with catalog directory.

    Args:
        catalog_dir: Directory containing catalog subdirectories
        git_backend: Git backend for clone/pull operations (DI)
    """
    self.catalog_dir = catalog_dir
    self.git_backend = git_backend or GitCatalogBackend()
    self._catalogs: Dict[str, ServerCatalog] = {}
    self._default_catalog = "official"

def discover_catalogs(self) -> List[CatalogInfo]:
    """Discover all catalogs in catalog directory."""
    catalogs = []

    if not self.catalog_dir.exists():
        return catalogs

    for item in self.catalog_dir.iterdir():
        if not item.is_dir():
            continue

        # Check for catalog.json
        catalog_file = item / "catalog.json"
        if not catalog_file.exists():
            continue

        # Determine catalog type
        is_git = (item / ".git").exists()
        catalog_type = "git" if is_git else "local"

        # Load catalog to get server count
        cat = ServerCatalog(catalog_path=catalog_file, validate_with_cue=False)
        cat.load_catalog()

        catalogs.append(CatalogInfo(
            name=item.name,
            path=item,
            type=catalog_type,
            description=f"{catalog_type.capitalize()} catalog",
            server_count=len(cat.list_servers())
        ))

    return catalogs

def add_catalog(self, name: str, git_url: str) -> OperationResult:
    """Add a catalog from git URL.

    Args:
        name: Catalog name (will be directory name)
        git_url: Git repository URL

    Returns:
        OperationResult with success/failure
    """
    target_dir = self.catalog_dir / name

    # Check if catalog already exists
    if target_dir.exists():
        return OperationResult.failure_result(
            f"Catalog '{name}' already exists at {target_dir}"
        )

    # Clone repository
    result = self.git_backend.clone(git_url, target_dir)
    if not result.success:
        return result

    # Verify catalog.json exists
    catalog_file = target_dir / "catalog.json"
    if not catalog_file.exists():
        # Cleanup failed clone
        import shutil
        shutil.rmtree(target_dir)
        return OperationResult.failure_result(
            f"Repository does not contain catalog.json"
        )

    # Clear cache to pick up new catalog
    self._catalogs.pop(name, None)

    return OperationResult.success_result(
        f"Catalog '{name}' added successfully"
    )

def sync_catalog(self, name: str) -> OperationResult:
    """Sync a git catalog with remote.

    Args:
        name: Catalog name

    Returns:
        OperationResult with success/failure
    """
    catalog_dir = self.catalog_dir / name

    if not catalog_dir.exists():
        return OperationResult.failure_result(f"Catalog '{name}' not found")

    # Check if it's a git catalog
    if not (catalog_dir / ".git").exists():
        return OperationResult.failure_result(
            f"Catalog '{name}' is not a git catalog"
        )

    # Pull changes
    result = self.git_backend.pull(catalog_dir)

    # Clear cache to reload catalog
    self._catalogs.pop(name, None)

    return result

def remove_catalog(self, name: str) -> OperationResult:
    """Remove a catalog.

    Args:
        name: Catalog name

    Returns:
        OperationResult with success/failure
    """
    # Prevent removing built-in catalogs
    if name in ["official", "local"]:
        return OperationResult.failure_result(
            f"Cannot remove built-in catalog '{name}'"
        )

    catalog_dir = self.catalog_dir / name

    if not catalog_dir.exists():
        return OperationResult.failure_result(f"Catalog '{name}' not found")

    # Remove directory
    import shutil
    shutil.rmtree(catalog_dir)

    # Clear cache
    self._catalogs.pop(name, None)

    return OperationResult.success_result(
        f"Catalog '{name}' removed successfully"
    )
```

#### 3. New CLI Commands

**File**: `src/mcpi/cli.py` (extend catalog subcommand)

```python
@catalog.command("add")
@click.argument("name")
@click.option("--git", "git_url", required=True, help="Git repository URL")
@click.pass_context
def catalog_add(ctx, name: str, git_url: str):
    """Add a catalog from git repository.

    Examples:
        mcpi catalog add official https://github.com/user/mcpi-catalog
        mcpi catalog add my-company git@github.com:company/mcp-servers.git
    """
    manager = get_catalog_manager(ctx)
    result = manager.add_catalog(name, git_url)

    if result.success:
        click.echo(f"✓ {result.message}")
    else:
        click.echo(f"✗ {result.message}", err=True)
        ctx.exit(1)


@catalog.command("sync")
@click.argument("name", required=False)
@click.option("--all", "sync_all", is_flag=True, help="Sync all git catalogs")
@click.pass_context
def catalog_sync(ctx, name: Optional[str], sync_all: bool):
    """Sync catalog with git remote.

    Examples:
        mcpi catalog sync official
        mcpi catalog sync --all
    """
    manager = get_catalog_manager(ctx)

    if sync_all:
        # Sync all git catalogs
        catalogs = manager.discover_catalogs()
        git_catalogs = [c for c in catalogs if c.type == "git"]

        if not git_catalogs:
            click.echo("No git catalogs to sync")
            return

        for cat in git_catalogs:
            click.echo(f"Syncing {cat.name}...")
            result = manager.sync_catalog(cat.name)
            if result.success:
                click.echo(f"  ✓ {result.message}")
            else:
                click.echo(f"  ✗ {result.message}", err=True)
    elif name:
        # Sync specific catalog
        result = manager.sync_catalog(name)
        if result.success:
            click.echo(f"✓ {result.message}")
        else:
            click.echo(f"✗ {result.message}", err=True)
            ctx.exit(1)
    else:
        click.echo("Error: Must specify catalog name or --all", err=True)
        ctx.exit(1)


@catalog.command("remove")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to remove this catalog?")
@click.pass_context
def catalog_remove(ctx, name: str):
    """Remove a catalog.

    Examples:
        mcpi catalog remove my-company
    """
    manager = get_catalog_manager(ctx)
    result = manager.remove_catalog(name)

    if result.success:
        click.echo(f"✓ {result.message}")
    else:
        click.echo(f"✗ {result.message}", err=True)
        ctx.exit(1)


@catalog.command("status")
@click.argument("name")
@click.pass_context
def catalog_status(ctx, name: str):
    """Show git status for a catalog.

    Examples:
        mcpi catalog status official
    """
    manager = get_catalog_manager(ctx)
    catalog_dir = manager.catalog_dir / name

    if not catalog_dir.exists():
        click.echo(f"Catalog '{name}' not found", err=True)
        ctx.exit(1)

    if not (catalog_dir / ".git").exists():
        click.echo(f"Catalog '{name}' is not a git catalog", err=True)
        ctx.exit(1)

    status = manager.git_backend.get_status(catalog_dir)

    click.echo(f"Catalog: {name}")
    click.echo(f"Remote: {status.remote_url or 'unknown'}")
    click.echo(f"Clean: {'yes' if status.is_clean else 'no (local modifications)'}")

    if status.ahead > 0:
        click.echo(f"Ahead: {status.ahead} commits")
    if status.behind > 0:
        click.echo(f"Behind: {status.behind} commits (updates available)")

    if not status.is_clean:
        click.echo()
        click.echo("Warning: Catalog has local modifications.")
        click.echo("Git catalogs should not be modified directly.")
        click.echo("Use your 'local' catalog for custom servers.")
```

### Implementation Tasks (Phase 2)

**[Similar structure to Phase 1, with tasks for:]**

- Week 1: GitCatalogBackend implementation and tests
- Week 2: CatalogManager extensions and CLI commands
- Week 3: Integration tests, E2E tests, documentation

### Success Criteria (Phase 2)

1. ✅ Users can add catalogs via `mcpi catalog add --git <url>`
2. ✅ Users can sync catalogs via `mcpi catalog sync`
3. ✅ Git error handling covers common failures
4. ✅ Multiple git catalogs supported
5. ✅ All tests pass
6. ✅ Documentation complete

---

## Phase 3: Advanced Features (v0.6.0)

**Timeline**: 2-3 weeks
**Goal**: Schema versioning, overlays, polish
**Priority**: P2 (Nice-to-have, rounds out feature)

### Scope

**IN SCOPE**:
- Schema versioning (v1.0.0 → v2.0.0)
- Catalog metadata format
- Schema migration tools
- Overlay mechanism (local changes on git catalogs)
- Auto-update checks (optional)
- Performance optimization

**OUT OF SCOPE**:
- Advanced git features (branches, tags)
- Catalog dependencies
- Catalog publishing tools

### Architecture Design

#### 1. Schema v2.0.0

**File**: `data/catalog-v2.cue`

```cue
// Catalog schema v2.0.0 with metadata

#CatalogMetadata: {
    schema_version: "2.0.0"
    name: string & !=""
    description: string
    version: string
    author?: string
    repository?: string | null
    created: string  // ISO 8601
    updated: string  // ISO 8601
}

#MCPServer: {
    description: string & !=""
    command:     string & !=""
    args:        [...string]
    env?:        [string]: string
    repository:  string | null
    categories:  [...string]
}

#Catalog: {
    metadata: #CatalogMetadata
    servers: {
        [string]: #MCPServer
    }
}
```

#### 2. Schema Migration

**File**: `src/mcpi/registry/migration.py`

```python
"""Catalog schema migration tools."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json
import shutil


class CatalogMigrator:
    """Migrate catalogs between schema versions."""

    @staticmethod
    def detect_version(catalog_path: Path) -> str:
        """Detect catalog schema version."""
        with open(catalog_path) as f:
            data = json.load(f)

        if "metadata" in data and "schema_version" in data["metadata"]:
            return data["metadata"]["schema_version"]
        else:
            return "1.0.0"  # Legacy format

    @staticmethod
    def migrate_v1_to_v2(catalog_path: Path, backup: bool = True) -> bool:
        """Migrate catalog from v1 to v2 format."""
        if backup:
            # Create backup
            backup_path = catalog_path.with_suffix(".json.v1.backup")
            shutil.copy2(catalog_path, backup_path)

        # Load v1 data
        with open(catalog_path) as f:
            v1_data = json.load(f)

        # Convert to v2 format
        v2_data = {
            "metadata": {
                "schema_version": "2.0.0",
                "name": catalog_path.parent.name,
                "description": "Migrated from v1",
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
            },
            "servers": v1_data  # Old flat dict becomes servers dict
        }

        # Write v2 data
        with open(catalog_path, "w") as f:
            json.dump(v2_data, f, indent=2, ensure_ascii=False)

        return True

    @staticmethod
    def auto_migrate(catalog_path: Path) -> bool:
        """Auto-migrate catalog to latest version if needed."""
        version = CatalogMigrator.detect_version(catalog_path)

        if version == "1.0.0":
            return CatalogMigrator.migrate_v1_to_v2(catalog_path)

        return True  # Already latest version
```

#### 3. Overlay Mechanism

**File**: `src/mcpi/registry/overlay.py`

```python
"""Catalog overlay for local modifications on top of git catalogs."""

from pathlib import Path
from typing import Optional, List, Tuple
from .catalog import ServerCatalog, MCPServer


class CatalogWithOverlay:
    """Catalog with local overlay on top of base (git) catalog."""

    def __init__(self, base_path: Path, overlay_path: Path):
        """Initialize with base and overlay paths.

        Args:
            base_path: Path to base catalog (git-tracked)
            overlay_path: Path to overlay catalog (local changes)
        """
        self.base = ServerCatalog(catalog_path=base_path, validate_with_cue=True)
        self.base.load_catalog()

        # Create overlay catalog if it doesn't exist
        if not overlay_path.exists():
            overlay_path.parent.mkdir(parents=True, exist_ok=True)
            overlay_path.write_text("{}")

        self.overlay = ServerCatalog(catalog_path=overlay_path, validate_with_cue=False)
        self.overlay.load_catalog()

    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server, checking overlay first."""
        # Check overlay first
        server = self.overlay.get_server(server_id)
        if server:
            return server

        # Fall back to base
        return self.base.get_server(server_id)

    def list_servers(self) -> List[Tuple[str, MCPServer]]:
        """List all servers, merging base and overlay."""
        # Start with base servers
        servers = dict(self.base.list_servers())

        # Override with overlay servers
        for server_id, server in self.overlay.list_servers():
            servers[server_id] = server

        return sorted(servers.items(), key=lambda x: x[0])

    def add_server(self, server_id: str, server: MCPServer) -> bool:
        """Add server to overlay (never modifies base)."""
        if not self.overlay.add_server(server_id, server):
            return False

        return self.overlay.save_catalog()

    def remove_server(self, server_id: str) -> bool:
        """Remove server from overlay."""
        if not self.overlay.remove_server(server_id):
            return False

        return self.overlay.save_catalog()
```

### Implementation Tasks (Phase 3)

**[Similar structure to Phase 1-2, with tasks for:]**

- Week 1: Schema v2.0.0 design and migration tools
- Week 2: Overlay mechanism and integration
- Week 3: Polish, optimization, final documentation

### Success Criteria (Phase 3)

1. ✅ Catalogs use v2.0.0 schema with metadata
2. ✅ Migration from v1 to v2 works reliably
3. ✅ Overlay mechanism allows local changes on git catalogs
4. ✅ All features from evaluation STATUS implemented
5. ✅ Performance benchmarks met
6. ✅ Complete documentation

---

## Testing Strategy

### Unit Tests

**Coverage Target**: 100% for all new components

**Components to Test**:
- CatalogManager (Phase 1)
- GitCatalogBackend (Phase 2)
- CatalogMigrator (Phase 3)
- CatalogWithOverlay (Phase 3)

**Test Patterns**:
- Use tmp_path for filesystem operations
- Mock git operations where appropriate
- Test both success and error paths
- Edge cases: missing files, corrupt data, network failures

### Integration Tests

**Scenarios**:
- Multi-catalog workflows (search, add, list)
- Git operations (clone, pull, status)
- Schema migration (v1 → v2)
- Overlay operations (base + local changes)

**Test Harness**:
- Extend MCPTestHarness for multi-catalog scenarios
- Create test git repositories for git tests
- Test catalog persistence across sessions

### End-to-End Tests

**User Workflows**:
1. Fresh install → two catalogs (official + local)
2. Add git catalog → search → add server
3. Sync git catalog → verify updates
4. Add to local catalog → verify persistence
5. Schema migration → verify no data loss

### Existing Test Updates

**Phase 1**: Minimal changes (backward compatible)
**Phase 2**: Update tests for git catalogs
**Phase 3**: Update tests for v2 schema

**Validation**: All 100% of tests pass after each phase

---

## Documentation Plan

### User Documentation

**Phase 1** (v0.4.0):
- Multi-catalog concepts
- Local catalog usage
- CLI reference (`catalog` subcommand)
- Migration guide (v0.3.0 → v0.4.0)

**Phase 2** (v0.5.0):
- Git catalog setup
- Sync workflows
- Troubleshooting git issues

**Phase 3** (v0.6.0):
- Schema versioning
- Overlay mechanism
- Advanced usage patterns

### Developer Documentation

**Phase 1**:
- CatalogManager API
- Factory functions
- Testing patterns

**Phase 2**:
- GitCatalogBackend API
- Creating git catalogs
- Testing git operations

**Phase 3**:
- Schema specification (v2.0.0)
- Migration API
- Overlay API

### CLAUDE.md Updates

**Each phase**:
- Update architecture section
- Update testing strategy
- Update development commands
- Add examples

---

## Risk Assessment

### Technical Risks

| Risk | Phase | Probability | Impact | Mitigation |
|------|-------|-------------|--------|------------|
| Breaking changes affect users | 1 | LOW | HIGH | Full backward compatibility |
| Git operations fail | 2 | MEDIUM | MEDIUM | Comprehensive error handling |
| Schema migration corrupts data | 3 | LOW | HIGH | Backup before migration, extensive tests |
| Performance degradation | 1-3 | LOW | MEDIUM | Lazy loading, benchmarking |
| Test suite breaks | 1-3 | MEDIUM | HIGH | Incremental updates, deprecation warnings |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Phase 1 takes longer | MEDIUM | MEDIUM | Buffer in estimates (2-3 weeks) |
| Git complexity underestimated | MEDIUM | MEDIUM | Phase 2 can expand timeline |
| Schema migration issues | LOW | HIGH | Phase 3 can be deferred if needed |
| User feedback requires changes | HIGH | MEDIUM | Iterative approach allows adjustments |

### User Impact Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users confused by catalogs | MEDIUM | MEDIUM | Clear documentation, intuitive CLI |
| Users lose custom servers | LOW | HIGH | Local catalog auto-initialized |
| Git setup too complex | MEDIUM | MEDIUM | Clear examples, helpful errors |
| Performance issues | LOW | MEDIUM | Benchmarking, optimization |

---

## Alternative Approaches Considered

### Alternative 1: Big Bang (4-6 weeks, all at once)

**Rejected because**:
- High risk of failure
- No incremental user feedback
- All-or-nothing delivery
- Difficult to test comprehensively

### Alternative 2: Defer Entirely (wait for DIP completion)

**Rejected because**:
- User explicitly requested feature NOW
- Business value of feature is high
- DIP Phase 2-4 timeline uncertain
- Can implement with current DIP patterns

### Alternative 3: Super-MVP (1 week, minimal features)

**Rejected because**:
- Too limited to be useful
- Would require immediate follow-up
- Technical debt from shortcuts
- Not aligned with "do it right the first time"

### Selected Approach: 3-Phase Incremental

**Why this is best**:
- ✅ Delivers value incrementally
- ✅ Allows user feedback between phases
- ✅ Each phase independently useful
- ✅ Aligns with "do it right the first time"
- ✅ Manageable risk per phase
- ✅ Can pause/adjust based on feedback
- ✅ Uses existing DIP patterns
- ✅ Backward compatible (Phase 1)

---

## Success Metrics

### Phase 1 (v0.4.0)

- [ ] Two catalogs working (official + local)
- [ ] 100% backward compatibility
- [ ] All existing tests pass
- [ ] 100% new code coverage
- [ ] Documentation complete
- [ ] Zero performance regression
- [ ] User can add custom servers to local catalog

### Phase 2 (v0.5.0)

- [ ] Git clone/pull/status working
- [ ] Users can add git catalogs
- [ ] Error handling covers 95% of git failures
- [ ] All tests pass
- [ ] Documentation complete
- [ ] User feedback positive

### Phase 3 (v0.6.0)

- [ ] Schema v2.0.0 implemented
- [ ] Migration tool works reliably
- [ ] Overlay mechanism working
- [ ] All evaluation requirements met
- [ ] Performance benchmarks met
- [ ] Complete feature documentation
- [ ] Ready for production use

---

## Next Steps

1. **Review this plan** with user for approval
2. **Create Phase 1 SPRINT** file with detailed task breakdown
3. **Set up test infrastructure** (expand MCPTestHarness)
4. **Begin Phase 1 Task 1.1**: CatalogManager implementation
5. **Daily progress reviews** to ensure alignment

---

## Conclusion

This **3-phase approach** provides a pragmatic path to implementing the multi-catalog feature while managing risk and complexity:

- **Phase 1 (v0.4.0)**: MVP with two catalogs, fully backward compatible (2-3 weeks)
- **Phase 2 (v0.5.0)**: Git integration for remote catalogs (2-3 weeks)
- **Phase 3 (v0.6.0)**: Advanced features and polish (2-3 weeks)

**Total timeline**: 6-9 weeks vs. 4-6 weeks (big bang) or indefinite (defer)

**Key advantages**:
- Incremental user value
- Feedback loops between phases
- Manageable risk per phase
- Each phase independently useful
- Aligns with user's "do it right" philosophy
- Uses existing DIP patterns

**Recommendation**: Proceed with **Phase 1 immediately**, review after completion, then decide on Phase 2-3 based on user feedback and priorities.

---

**Plan Status**: READY FOR REVIEW
**Confidence**: 90% (pragmatic approach, well-scoped)
**Next Action**: User review and approval to proceed with Phase 1

---

*Planning conducted by: Project Planner Agent*
*Date: 2025-11-17 02:23:52*
*MCPI Version: v0.3.0 → v0.6.0*
*Approach: Phased implementation with MVP first*
