# Multi-Catalog Feature Evaluation

**Date**: 2025-11-17 02:18:48
**Project**: MCPI v0.3.0
**Feature**: Multi-catalog support with git-based synchronization
**Evaluator**: Project Auditor Agent
**Status**: COMPREHENSIVE TECHNICAL ASSESSMENT

---

## Executive Summary

**Assessment**: The multi-catalog feature requires **MAJOR ARCHITECTURAL CHANGES** spanning catalog management, CLI interface, dependency injection, and file system layout. This is a **v0.6.0+ feature** requiring 4-6 weeks of development.

**Critical Findings**:
- Current architecture: Single hardcoded catalog at `data/catalog.json`
- Current state: Tightly coupled catalog loading throughout codebase
- Breaking changes: Required for ServerCatalog initialization, CLI commands, and catalog path management
- Test impact: 48 test files need updates, catalog validation tests need rewrite
- Migration complexity: HIGH - users have no local catalogs to migrate

**Recommendation**: **DEFER to v0.6.0+**. Complete DIP Phase 2-4 first (v0.4.0-v0.5.0) to establish dependency injection patterns that will make multi-catalog implementation cleaner.

---

## 1. Current Architecture Analysis

### 1.1 Existing Catalog System

**File**: `src/mcpi/registry/catalog.py`

**Current Design**:
```python
class ServerCatalog:
    def __init__(self, catalog_path: Path, validate_with_cue: bool = True):
        """Single catalog at a fixed path."""
        self.catalog_path = catalog_path  # Single path
        self._registry: Optional[ServerRegistry] = None
        self._loaded = False

def create_default_catalog(validate_with_cue: bool = True) -> ServerCatalog:
    """Hardcoded path to data/catalog.json"""
    package_dir = Path(__file__).parent.parent.parent.parent
    catalog_path = package_dir / "data" / "catalog.json"
    return ServerCatalog(catalog_path=catalog_path, validate_with_cue=validate_with_cue)
```

**Problems**:
1. **Single catalog assumption**: All code assumes exactly one catalog exists
2. **Hardcoded path**: Factory function hardcodes `data/catalog.json`
3. **No catalog identity**: Catalogs have no name/ID, only a path
4. **No catalog metadata**: No version, author, description, git remote
5. **No catalog discovery**: No mechanism to find/list multiple catalogs

**Evidence**: Lines 130-356 in `src/mcpi/registry/catalog.py`
- ServerCatalog class takes single `catalog_path` parameter
- No concept of catalog collections or catalog manager
- No git integration anywhere in catalog code

### 1.2 Data File Structure

**Current Catalog Format** (`data/catalog.json`):
```json
{
  "server-id": {
    "description": "...",
    "command": "npx",
    "args": ["..."],
    "repository": "...",
    "categories": ["..."]
  }
}
```

**Current Schema** (`data/catalog.cue`):
```cue
#MCPServer: {
    description: string & !=""
    command:     string & !=""
    args:        [...string]
    env?:        [string]: string
    repository:  string | null
    categories:  [...string]
}

{
    [string]: #MCPServer
}
```

**Problems**:
1. **No catalog metadata**: Schema only defines server format, not catalog metadata
2. **No versioning**: No schema version field
3. **No catalog identity**: No name, description, author fields for the catalog itself
4. **Flat structure**: Single-level dictionary, no catalog wrapper object

**Evidence**: Lines 1-18 in `data/catalog.cue`
- Schema defines server format only
- No catalog-level fields (name, version, remote URL, etc.)

### 1.3 Usage Throughout Codebase

**CLI Loading** (`src/mcpi/cli.py`):
```python
def get_catalog(ctx: click.Context):
    """Lazy initialization of ServerCatalog using factory function."""
    if "catalog" not in ctx.obj:
        ctx.obj["catalog"] = create_default_catalog()  # Hardcoded
        ctx.obj["catalog"].load_catalog()
    return ctx.obj["catalog"]
```

**Usage Sites** (26 files reference catalog):
- `src/mcpi/cli.py`: CLI commands (search, info, add)
- `src/mcpi/bundles/installer.py`: Bundle installation
- `src/mcpi/tui/*.py`: TUI interface
- `tests/*.py`: 10+ test files

**Problems**:
1. **Single catalog assumption**: All commands assume one catalog
2. **No catalog selection**: No way to specify which catalog to use
3. **No catalog management**: No commands for catalog operations

**Evidence**: Grep output shows 26 files with "catalog" references
- All usages assume single catalog via `get_catalog(ctx)`
- No code for catalog switching, listing, or management

### 1.4 Dependency Injection Status

**DIP Phase 1 Complete** (v0.3.0):
- ✅ ServerCatalog: Accepts `catalog_path` parameter
- ✅ MCPManager: Accepts `registry` parameter
- ✅ Factory functions: `create_default_catalog()`, `create_test_catalog()`

**DIP Phase 2-4 Pending** (v0.4.0-v0.5.0):
- ⏳ ClaudeCodePlugin
- ⏳ FileBasedScope
- ⏳ FileMoveEnableDisableHandler
- ⏳ JSONFileReader/JSONFileWriter
- ⏳ SchemaValidator
- ⏳ CUEValidator
- ⏳ 6 more components

**Status**: DIP Phase 1 provides foundation for multi-catalog, but incomplete coverage means injection patterns not fully established.

---

## 2. Gap Analysis: Current vs. Requirements

### 2.1 Requirement: Multiple Catalogs Support

**Requirement**: Users can work with multiple catalogs simultaneously

**Current State**: DOES NOT EXIST
- ServerCatalog is singleton per CLI invocation
- CLI context holds single catalog reference
- No concept of catalog collections

**Gap**: Need CatalogManager class to manage multiple catalogs

**Implementation Needed**:
```python
class CatalogManager:
    """Manages multiple server catalogs."""

    def __init__(self, catalog_dir: Path):
        self.catalog_dir = catalog_dir
        self.catalogs: Dict[str, ServerCatalog] = {}
        self.default_catalog: Optional[str] = None

    def list_catalogs(self) -> List[CatalogInfo]:
        """List all available catalogs."""

    def get_catalog(self, name: str) -> Optional[ServerCatalog]:
        """Get a specific catalog by name."""

    def add_catalog(self, name: str, source: str) -> OperationResult:
        """Add a catalog from git URL or local path."""

    def remove_catalog(self, name: str) -> OperationResult:
        """Remove a catalog."""

    def sync_catalog(self, name: str) -> OperationResult:
        """Sync catalog with git remote."""

    def search_all(self, query: str) -> List[Tuple[str, str, MCPServer]]:
        """Search across all catalogs."""
```

**Breaking Changes**:
- CLI commands need `--catalog` flag
- `get_catalog(ctx)` must return catalog manager or accept catalog name
- All catalog operations need catalog name parameter

### 2.2 Requirement: Default Local Catalog

**Requirement**: Users have a default 'local' catalog for custom servers

**Current State**: DOES NOT EXIST
- No user-specific catalog directory
- No concept of local vs remote catalogs
- No mechanism to distinguish catalog sources

**Gap**: Need local catalog directory and initialization

**Implementation Needed**:
- **Directory structure**:
  ```
  ~/.mcpi/catalogs/
      local/
          catalog.json      # User's custom servers
          .catalog.yaml     # Catalog metadata (name, version, etc.)
      official/
          catalog.json      # Cloned from github.com/user/mcpi-catalog
          .git/             # Git repository
          .catalog.yaml     # Catalog metadata
  ```

- **Catalog metadata** (`.catalog.yaml`):
  ```yaml
  name: local
  version: "1.0.0"
  type: local  # or "git", "url"
  description: "User's custom MCP servers"
  remote: null  # or git URL for synced catalogs
  created: "2025-11-17T02:18:48Z"
  updated: "2025-11-17T02:18:48Z"
  ```

- **Initialization logic**:
  ```python
  def initialize_local_catalog():
      """Create local catalog if it doesn't exist."""
      local_path = Path.home() / ".mcpi" / "catalogs" / "local"
      local_path.mkdir(parents=True, exist_ok=True)

      catalog_file = local_path / "catalog.json"
      if not catalog_file.exists():
          catalog_file.write_text("{}")

      metadata_file = local_path / ".catalog.yaml"
      if not metadata_file.exists():
          # Write default metadata
  ```

**Breaking Changes**: None (new functionality)

### 2.3 Requirement: Git-Based Catalogs

**Requirement**: Catalogs stored in separate git repositories

**Current State**: DOES NOT EXIST
- No git integration in catalog code
- Catalog is file in package data directory
- No concept of remote catalogs

**Gap**: Need git clone, pull, and sync functionality

**Implementation Needed**:
```python
class GitCatalogBackend:
    """Git backend for catalog synchronization."""

    def clone(self, url: str, target_dir: Path) -> OperationResult:
        """Clone a git repository containing a catalog."""
        # Use subprocess to run: git clone <url> <target_dir>

    def pull(self, catalog_dir: Path) -> OperationResult:
        """Pull latest changes from remote."""
        # Use subprocess to run: git pull in catalog_dir

    def status(self, catalog_dir: Path) -> Dict[str, Any]:
        """Get git status (clean, modified, ahead/behind)."""
        # Use subprocess to run: git status --porcelain

    def get_remote_url(self, catalog_dir: Path) -> Optional[str]:
        """Get remote URL for catalog."""
        # Use subprocess to run: git remote get-url origin

    def is_clean(self, catalog_dir: Path) -> bool:
        """Check if working directory is clean."""
        # Use subprocess to run: git status --porcelain
```

**Dependencies**:
- Git must be installed on user's system
- Need git error handling (not installed, network errors, auth issues)

**Breaking Changes**: None (new functionality)

### 2.4 Requirement: Versioned Schema

**Requirement**: Well-defined, versioned catalog schema

**Current State**: PARTIAL
- CUE schema exists (`data/catalog.cue`)
- Schema defines server format but not catalog metadata
- No version field in schema
- No backward compatibility mechanism

**Gap**: Need schema versioning and migration

**Implementation Needed**:
```cue
// catalog-v1.cue
#CatalogMetadata: {
    schema_version: "1.0.0"
    name: string & !=""
    description: string
    version: string
    author?: string
    repository?: string | null
    created: string  // ISO 8601 timestamp
    updated: string  // ISO 8601 timestamp
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

**Schema Evolution**:
- v1.0.0: Current flat format (backward compat)
- v2.0.0: Wrapped format with metadata
- Need migration tool: v1 → v2

**Breaking Changes**:
- Catalog file format changes from flat dict to wrapped object
- Existing catalogs need migration
- CUE validator needs version detection

### 2.5 Requirement: Local Changes Don't Affect Remote

**Requirement**: Local modifications to catalogs don't impact git remotes

**Current State**: N/A (no git integration)

**Gap**: Need local overlay mechanism

**Implementation Needed**:
```python
class CatalogWithOverlay:
    """Catalog with local overlay on top of git remote."""

    def __init__(self, base_path: Path, overlay_path: Path):
        self.base = ServerCatalog(base_path)  # Git-tracked
        self.overlay = ServerCatalog(overlay_path)  # Local changes

    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Check overlay first, fall back to base."""
        server = self.overlay.get_server(server_id)
        if server:
            return server
        return self.base.get_server(server_id)

    def list_servers(self) -> List[Tuple[str, MCPServer]]:
        """Merge base and overlay servers."""
        # Overlay servers override base servers

    def add_server(self, server_id: str, server: MCPServer):
        """Add to overlay only (never modify git-tracked catalog)."""
        self.overlay.add_server(server_id, server)
        self.overlay.save_catalog()
```

**Directory Structure**:
```
~/.mcpi/catalogs/
    official/
        catalog.json      # Git-tracked (never modified)
        .git/
        .catalog.yaml
    official-overlay/
        catalog.json      # Local additions/overrides
        .catalog.yaml
```

**Breaking Changes**: None (new functionality)

---

## 3. Technical Challenges and Risks

### 3.1 Catalog Discovery and Loading

**Challenge**: How does CatalogManager discover catalogs?

**Options**:
1. **Directory scan**: Scan `~/.mcpi/catalogs/` for subdirectories with `catalog.json`
2. **Registry file**: Maintain `~/.mcpi/catalogs.yaml` listing all catalogs
3. **Convention-based**: Any directory with `.catalog.yaml` is a catalog

**Recommendation**: Option 3 (convention-based)
- Flexible: Users can add catalogs by copying directories
- Self-describing: Metadata file indicates what catalog is
- No central registry to corrupt

**Implementation**:
```python
def discover_catalogs(catalog_dir: Path) -> List[CatalogInfo]:
    """Discover all catalogs in directory."""
    catalogs = []
    for item in catalog_dir.iterdir():
        if item.is_dir():
            metadata_file = item / ".catalog.yaml"
            if metadata_file.exists():
                metadata = load_yaml(metadata_file)
                catalogs.append(CatalogInfo(
                    name=metadata["name"],
                    path=item,
                    type=metadata["type"],
                    remote=metadata.get("remote"),
                ))
    return catalogs
```

**Risk**: **MEDIUM**
- What if `.catalog.yaml` is missing or corrupted?
- What if catalog name conflicts with directory name?
- What if user manually creates conflicting catalogs?

**Mitigation**:
- Graceful degradation: Skip invalid catalogs, log warnings
- Name validation: Enforce catalog name = directory name
- Conflict detection: Error on duplicate catalog names

### 3.2 Catalog Name Conflicts

**Challenge**: What if multiple catalogs have same name?

**Scenarios**:
1. User clones same catalog twice to different directories
2. User creates local catalog with same name as remote
3. Two git repos have same catalog name in metadata

**Recommendation**: Use directory name as canonical ID
- Catalog name in `.catalog.yaml` must match directory name
- Enforce uniqueness at directory level
- Reject operations that would create conflicts

**Implementation**:
```python
def validate_catalog_name(catalog_dir: Path, metadata: dict) -> bool:
    """Ensure catalog name matches directory name."""
    dir_name = catalog_dir.name
    meta_name = metadata["name"]

    if dir_name != meta_name:
        raise ValueError(
            f"Catalog name mismatch: directory={dir_name}, metadata={meta_name}"
        )

    return True
```

**Risk**: **LOW**
- Simple validation catches most issues
- Users can rename directories to resolve conflicts

### 3.3 Schema Versioning and Migration

**Challenge**: How to handle schema version mismatches?

**Scenarios**:
1. MCPI v0.6.0 expects schema v2, catalog is v1
2. MCPI v0.5.0 encounters schema v2 (forward compatibility)
3. Catalog has no schema version (legacy format)

**Recommendation**: Version detection with auto-migration
```python
def load_catalog_with_migration(path: Path) -> ServerCatalog:
    """Load catalog and migrate to current schema if needed."""
    data = json.loads(path.read_text())

    # Detect version
    if "metadata" in data and "schema_version" in data["metadata"]:
        version = data["metadata"]["schema_version"]
    else:
        version = "1.0.0"  # Legacy format

    # Migrate if needed
    if version == "1.0.0":
        data = migrate_v1_to_v2(data)

    return ServerCatalog.from_dict(data)

def migrate_v1_to_v2(data: dict) -> dict:
    """Migrate legacy flat format to wrapped format."""
    return {
        "metadata": {
            "schema_version": "2.0.0",
            "name": "unknown",
            "description": "Migrated from v1",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        },
        "servers": data  # Old flat dict becomes servers dict
    }
```

**Risk**: **MEDIUM**
- Migration bugs could corrupt catalogs
- Forward compatibility not guaranteed
- User confusion about version mismatches

**Mitigation**:
- Create backup before migration
- Comprehensive migration tests
- Clear error messages for unsupported versions

### 3.4 Git Integration Complexity

**Challenge**: Git operations can fail in many ways

**Failure Modes**:
1. Git not installed
2. Network errors during clone/pull
3. Authentication failures (private repos)
4. Merge conflicts (if user modifies git catalog)
5. Detached HEAD state
6. Submodules not initialized

**Recommendation**: Robust error handling with helpful messages
```python
class GitCatalogBackend:
    def clone(self, url: str, target_dir: Path) -> OperationResult:
        """Clone with comprehensive error handling."""
        try:
            # Check git installed
            result = subprocess.run(["git", "--version"], capture_output=True)
            if result.returncode != 0:
                return OperationResult.failure_result(
                    "Git is not installed. Please install git: https://git-scm.com"
                )

            # Clone repository
            result = subprocess.run(
                ["git", "clone", url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                # Parse error message
                if "Authentication failed" in result.stderr:
                    return OperationResult.failure_result(
                        f"Authentication failed for {url}. "
                        "Check your credentials or use SSH keys."
                    )
                elif "Network is unreachable" in result.stderr:
                    return OperationResult.failure_result(
                        "Network error. Check your internet connection."
                    )
                else:
                    return OperationResult.failure_result(
                        f"Git clone failed: {result.stderr}"
                    )

            return OperationResult.success_result("Catalog cloned successfully")

        except subprocess.TimeoutExpired:
            return OperationResult.failure_result(
                "Git clone timed out after 5 minutes. "
                "Check your network connection or try again later."
            )
        except Exception as e:
            return OperationResult.failure_result(f"Unexpected error: {e}")
```

**Risk**: **HIGH**
- Many failure modes
- Platform-specific git behaviors
- User environment variability

**Mitigation**:
- Comprehensive error handling for each failure mode
- Clear, actionable error messages
- Fallback to HTTP if SSH fails
- Timeout limits to prevent hangs

### 3.5 Performance Impact

**Challenge**: Loading multiple catalogs could be slow

**Current Performance**: ~500ms for list operation (single catalog, 50 servers)

**Multi-Catalog Impact**:
- 3 catalogs × 500ms = 1.5 seconds (3x slowdown)
- 10 catalogs × 500ms = 5 seconds (10x slowdown)

**Recommendation**: Lazy loading + caching
```python
class CatalogManager:
    def __init__(self, catalog_dir: Path):
        self.catalog_dir = catalog_dir
        self._catalogs: Dict[str, ServerCatalog] = {}
        self._catalog_info_cache: Optional[List[CatalogInfo]] = None

    def list_catalogs(self) -> List[CatalogInfo]:
        """List catalog metadata without loading servers."""
        if self._catalog_info_cache is None:
            # Only read .catalog.yaml files, don't load servers
            self._catalog_info_cache = self._discover_catalogs()
        return self._catalog_info_cache

    def get_catalog(self, name: str) -> ServerCatalog:
        """Load catalog on demand and cache."""
        if name not in self._catalogs:
            catalog_path = self.catalog_dir / name / "catalog.json"
            self._catalogs[name] = ServerCatalog(catalog_path)
            self._catalogs[name].load_catalog()
        return self._catalogs[name]
```

**Risk**: **LOW**
- Lazy loading prevents unnecessary work
- Caching amortizes load cost

**Mitigation**:
- Only load catalogs when needed
- Cache loaded catalogs in memory
- Parallel loading for bulk operations (v0.7.0+)

---

## 4. Breaking Changes Assessment

### 4.1 ServerCatalog Initialization

**Current**:
```python
catalog = create_default_catalog()
```

**After Multi-Catalog**:
```python
manager = create_default_catalog_manager()
catalog = manager.get_catalog("official")  # Explicit catalog selection
```

**Impact**: **BREAKING**
- All code using `create_default_catalog()` must change
- Factory function signature preserved but semantics change
- Migration path: `create_default_catalog()` returns first catalog from manager

**Mitigation**:
```python
def create_default_catalog() -> ServerCatalog:
    """Backward compat: Return default catalog from manager."""
    manager = create_default_catalog_manager()
    return manager.get_default_catalog()
```

### 4.2 CLI Command Changes

**Current**:
```bash
mcpi search filesystem
mcpi add filesystem
```

**After Multi-Catalog**:
```bash
# Search in default catalog (backward compatible)
mcpi search filesystem

# Search in specific catalog
mcpi search filesystem --catalog official

# Search across all catalogs
mcpi search filesystem --all-catalogs

# Add from specific catalog
mcpi add filesystem --catalog official
```

**Impact**: **BACKWARD COMPATIBLE** (with defaults)
- New `--catalog` flag added (optional)
- Default behavior unchanged (use default catalog)
- New `--all-catalogs` flag for cross-catalog search

**Mitigation**: None needed (backward compatible)

### 4.3 Catalog File Format

**Current Format** (v1.0.0):
```json
{
  "server-id": {
    "description": "...",
    ...
  }
}
```

**New Format** (v2.0.0):
```json
{
  "metadata": {
    "schema_version": "2.0.0",
    "name": "official",
    "description": "Official MCP servers",
    "version": "1.0.0",
    "author": "MCPI Maintainers",
    "repository": "https://github.com/user/mcpi-catalog",
    "created": "2025-11-17T00:00:00Z",
    "updated": "2025-11-17T02:18:48Z"
  },
  "servers": {
    "server-id": {
      "description": "...",
      ...
    }
  }
}
```

**Impact**: **BREAKING** (with migration)
- Old catalogs cannot be read without migration
- New catalogs cannot be read by old MCPI versions
- Users with custom catalogs need migration

**Mitigation**:
- Auto-migration on first load (with backup)
- Support both formats during transition (v0.6.0-v0.7.0)
- Deprecation warning for v1 format
- Migration tool: `mcpi catalog migrate`

### 4.4 Test Suite Impact

**Files Requiring Updates**: 48 test files
- All tests using `create_default_catalog()` need review
- Catalog validation tests need complete rewrite
- Integration tests need multi-catalog scenarios

**Specific Test Changes**:
1. `tests/test_catalog_rename.py` - Update for new format
2. `tests/test_catalog_rename_regression.py` - Update for new format
3. `tests/test_registry_dependency_injection.py` - Add catalog manager tests
4. `tests/test_bundles.py` - Update catalog mocking
5. 44 other files with catalog references

**Estimated Effort**: 2-3 days
- Review each test file
- Update mocking and fixtures
- Add new test scenarios
- Verify 100% pass rate

---

## 5. Migration Path

### 5.1 From Single to Multi-Catalog

**User Impact**: Existing users have no local catalogs

**Migration Steps**:
1. On first run of MCPI v0.6.0:
   ```
   Initializing catalog system...
   ✓ Created local catalog at ~/.mcpi/catalogs/local
   ✓ Migrated built-in catalog to ~/.mcpi/catalogs/official

   You now have 2 catalogs:
   - official (50 servers) - Default catalog
   - local (0 servers) - Your custom servers

   Use 'mcpi catalog list' to see all catalogs.
   ```

2. Built-in catalog becomes git-cloneable:
   ```bash
   # Remove old official catalog
   rm -rf ~/.mcpi/catalogs/official

   # Clone from GitHub
   mcpi catalog add official --git https://github.com/user/mcpi-catalog
   ```

3. Users can add their own catalogs:
   ```bash
   mcpi catalog add my-company --git git@github.com:company/mcp-catalog.git
   ```

**Automated Migration**:
```python
def migrate_single_to_multi_catalog():
    """Auto-migration on first run of v0.6.0."""
    catalog_dir = Path.home() / ".mcpi" / "catalogs"

    # Check if already migrated
    if catalog_dir.exists():
        return

    # Create catalog directory
    catalog_dir.mkdir(parents=True, exist_ok=True)

    # Create local catalog
    local_dir = catalog_dir / "local"
    local_dir.mkdir()
    (local_dir / "catalog.json").write_text("{}")
    (local_dir / ".catalog.yaml").write_text("""
name: local
version: "1.0.0"
type: local
description: "Your custom MCP servers"
remote: null
""")

    # Copy built-in catalog to official
    official_dir = catalog_dir / "official"
    official_dir.mkdir()

    # Copy from package data
    package_catalog = Path(__file__).parent.parent.parent.parent / "data" / "catalog.json"
    shutil.copy(package_catalog, official_dir / "catalog.json")

    # Create metadata
    (official_dir / ".catalog.yaml").write_text("""
name: official
version: "1.0.0"
type: builtin
description: "Official MCP server catalog"
remote: https://github.com/user/mcpi-catalog
""")

    # Set default catalog
    (catalog_dir / "default").write_text("official")

    print("✓ Catalog system initialized")
```

**Risk**: **MEDIUM**
- Migration could fail (disk full, permissions)
- User confusion about new structure
- Existing scripts break if hardcoded paths used

**Mitigation**:
- Clear migration message
- Rollback on failure
- Detailed migration documentation
- Migration dry-run command

### 5.2 Backward Compatibility Strategy

**Approach**: Dual-mode support during transition

**v0.6.0** (Multi-catalog release):
- Support both single catalog (old) and multi-catalog (new) modes
- Auto-detect which mode based on directory structure
- Print migration nudge if still in single-catalog mode

**v0.7.0** (6 months later):
- Force migration on startup
- Remove single-catalog code paths
- Full multi-catalog only

**Implementation**:
```python
def get_catalog_mode() -> str:
    """Detect catalog mode: 'single' or 'multi'."""
    catalog_dir = Path.home() / ".mcpi" / "catalogs"

    if catalog_dir.exists():
        return "multi"
    else:
        return "single"

def create_default_catalog() -> ServerCatalog:
    """Factory function with dual-mode support."""
    mode = get_catalog_mode()

    if mode == "multi":
        # New: Use catalog manager
        manager = create_default_catalog_manager()
        return manager.get_default_catalog()
    else:
        # Old: Use built-in catalog
        package_dir = Path(__file__).parent.parent.parent.parent
        catalog_path = package_dir / "data" / "catalog.json"
        return ServerCatalog(catalog_path=catalog_path)
```

---

## 6. Recommended File System Structure

### 6.1 Directory Layout

```
~/.mcpi/
    catalogs/
        local/                      # User's custom servers
            catalog.json            # Server definitions
            .catalog.yaml           # Catalog metadata
        official/                   # Official MCPI catalog (git)
            catalog.json
            .catalog.yaml
            .git/                   # Git repository
        my-company/                 # Company catalog (git)
            catalog.json
            .catalog.yaml
            .git/
        experimental/               # Experimental servers (git)
            catalog.json
            .catalog.yaml
            .git/
    default                         # Contains name of default catalog ("official")
    config.yaml                     # Global MCPI configuration (optional)
```

### 6.2 Catalog Metadata Format

**File**: `.catalog.yaml` (in each catalog directory)

```yaml
# Catalog identity
name: official                      # MUST match directory name
version: "1.0.0"                    # Catalog version (not schema version)
schema_version: "2.0.0"             # Schema version for catalog.json

# Catalog source
type: git                           # "local", "git", "url"
remote: https://github.com/user/mcpi-catalog
branch: main                        # Default branch to track

# Metadata
description: "Official MCP server catalog maintained by MCPI community"
author: "MCPI Maintainers"
license: "MIT"
homepage: "https://github.com/user/mcpi-catalog"

# Timestamps
created: "2025-11-17T00:00:00Z"
updated: "2025-11-17T02:18:48Z"
last_sync: "2025-11-17T02:18:48Z"   # Last git pull

# Catalog settings
allow_local_changes: false          # If true, use overlay for local edits
priority: 50                        # Higher priority catalogs override lower
```

### 6.3 Server Catalog Format (v2.0.0)

**File**: `catalog.json` (in each catalog directory)

```json
{
  "metadata": {
    "schema_version": "2.0.0",
    "name": "official",
    "description": "Official MCP server catalog",
    "version": "1.0.0",
    "author": "MCPI Maintainers",
    "repository": "https://github.com/user/mcpi-catalog",
    "created": "2025-11-17T00:00:00Z",
    "updated": "2025-11-17T02:18:48Z"
  },
  "servers": {
    "filesystem": {
      "description": "Access and manage local filesystem operations",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-filesystem"],
      "repository": "https://github.com/anthropics/mcp-filesystem-server",
      "categories": ["filesystem", "utility"],
      "tags": ["file", "directory", "read", "write"],
      "install_method": "npx",
      "language": "typescript",
      "license": "MIT",
      "author": "Anthropic"
    }
  }
}
```

**Schema Evolution**:
- v1.0.0: Flat format (current)
- v2.0.0: Wrapped format with metadata + servers
- v3.0.0: (Future) Add server dependencies, health checks, etc.

---

## 7. Git Integration Strategy

### 7.1 Git Operations

**Supported Operations**:
1. **Clone**: `mcpi catalog add <name> --git <url>`
2. **Pull**: `mcpi catalog sync <name>` or `mcpi catalog sync --all`
3. **Status**: `mcpi catalog status <name>` (show git status)
4. **Info**: `mcpi catalog info <name>` (show metadata + git info)

**Not Supported** (by design):
- Commit: Local changes go to overlay, not git catalog
- Push: Users don't push to remote catalogs
- Branch switching: Always use default branch (main/master)
- Merge: Abort on merge conflicts, require manual resolution

### 7.2 Sync Strategy

**Question**: When to sync catalogs with git remote?

**Options**:
1. **Manual only**: User must run `mcpi catalog sync`
2. **Auto on startup**: Check for updates on every CLI invocation
3. **Scheduled**: Check daily/weekly
4. **On-demand**: Check before search/add operations

**Recommendation**: Manual + optional auto-check
```bash
# Manual sync
mcpi catalog sync official

# Sync all catalogs
mcpi catalog sync --all

# Enable auto-check (checks on startup, but doesn't auto-pull)
mcpi config set auto_check_updates true

# Auto-pull (checks and pulls automatically - DANGEROUS)
mcpi config set auto_pull_updates false  # Default: false
```

**Auto-Check Behavior**:
```
$ mcpi search filesystem
[INFO] Catalog 'official' has updates available (15 commits behind)
[INFO] Run 'mcpi catalog sync official' to update

Searching for 'filesystem'...
<results>
```

**Risk**: **LOW**
- Manual sync gives users control
- Auto-check is informative, not disruptive
- Auto-pull disabled by default (avoid surprises)

### 7.3 Conflict Handling

**Scenario**: User modifies git-tracked catalog, then syncs

**Git Behavior**: Merge conflict or error

**MCPI Behavior**: ABORT with helpful message
```bash
$ mcpi catalog sync official
[ERROR] Catalog 'official' has local modifications.

Git catalogs should not be modified directly. Use your 'local' catalog instead.

Options:
  1. Discard local changes: mcpi catalog reset official
  2. Move servers to local catalog: mcpi catalog export official --to local
  3. Resolve manually: cd ~/.mcpi/catalogs/official && git status

Aborting sync.
```

**Design Principle**: Git catalogs are READ-ONLY
- All user changes go to 'local' catalog
- Git catalogs never modified by MCPI
- Clean git state at all times

---

## 8. CLI Design

### 8.1 New Commands

**Catalog Management**:
```bash
# List all catalogs
mcpi catalog list

# Add a catalog from git
mcpi catalog add <name> --git <url>

# Add a catalog from local directory
mcpi catalog add <name> --path <path>

# Remove a catalog
mcpi catalog remove <name>

# Sync catalog with remote
mcpi catalog sync <name>
mcpi catalog sync --all

# Show catalog information
mcpi catalog info <name>

# Set default catalog
mcpi catalog set-default <name>

# Export servers from one catalog to another
mcpi catalog export <from> --to <to>

# Validate catalog
mcpi catalog validate <name>

# Migrate catalog to new schema version
mcpi catalog migrate <name>
```

**Enhanced Server Commands**:
```bash
# Search in specific catalog
mcpi search filesystem --catalog official

# Search across all catalogs
mcpi search filesystem --all-catalogs

# Add server from specific catalog
mcpi add filesystem --catalog official

# Show which catalog a server came from
mcpi info filesystem --show-catalog
```

### 8.2 Command Examples

```bash
# Initial setup
$ mcpi catalog list
No catalogs found. Run 'mcpi catalog init' to initialize.

$ mcpi catalog init
✓ Created local catalog at ~/.mcpi/catalogs/local
✓ Created official catalog at ~/.mcpi/catalogs/official
✓ Set default catalog to 'official'

# Add company catalog
$ mcpi catalog add my-company --git git@github.com:company/mcp-servers.git
Cloning catalog...
✓ Cloned 25 servers from my-company catalog

# List catalogs
$ mcpi catalog list
NAME         TYPE    SERVERS  UPDATED              DEFAULT
official     git     50       2025-11-17 02:18     ✓
my-company   git     25       2025-11-17 02:20
local        local   0        2025-11-17 02:18

# Search across all catalogs
$ mcpi search database --all-catalogs
CATALOG      ID          COMMAND  DESCRIPTION
official     sqlite      npx      Query and manage SQLite databases
official     postgres    npx      Query and manage PostgreSQL databases
my-company   oracle      docker   Oracle database MCP server
local        my-db       python   My custom database server

# Add from specific catalog
$ mcpi add oracle --catalog my-company
Found in catalog: my-company
Installing oracle...
✓ Added oracle to project-mcp scope

# Sync catalogs
$ mcpi catalog sync --all
Syncing official... ✓ Already up to date
Syncing my-company... ✓ Pulled 3 new servers
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**New Components**:
1. `CatalogManager` - Catalog discovery, loading, management
2. `GitCatalogBackend` - Git operations (clone, pull, status)
3. `CatalogMetadata` - Metadata parsing and validation
4. `CatalogMigrator` - Schema migration (v1 → v2)
5. `CatalogValidator` - Validate catalog structure

**Test Coverage Requirements**:
- 100% coverage for all new components
- Edge cases: Missing files, corrupted metadata, git errors
- Error handling: Network failures, auth failures, conflicts

**Example Tests**:
```python
class TestCatalogManager:
    def test_discover_catalogs(self, tmp_path):
        """Test catalog discovery."""
        # Setup: Create 3 catalog directories
        # Expected: Discover all 3 catalogs
        # Edge case: Ignore directories without .catalog.yaml

    def test_get_catalog_lazy_loading(self, tmp_path):
        """Test lazy loading of catalogs."""
        # Setup: Create catalog directory
        # Expected: Catalog not loaded until get_catalog() called
        # Verify: Load happens exactly once

    def test_catalog_name_conflict(self, tmp_path):
        """Test handling of catalog name conflicts."""
        # Setup: Create two catalogs with same name
        # Expected: Error with clear message

    def test_add_catalog_git(self, tmp_path, mock_git):
        """Test adding catalog from git URL."""
        # Setup: Mock git clone
        # Expected: Catalog cloned and registered
        # Edge case: Clone failure handled gracefully

class TestGitCatalogBackend:
    def test_clone_success(self, tmp_path, mock_git):
        """Test successful git clone."""

    def test_clone_auth_failure(self, tmp_path, mock_git):
        """Test authentication failure handling."""

    def test_pull_with_conflicts(self, tmp_path, mock_git):
        """Test pull with merge conflicts."""

    def test_git_not_installed(self, tmp_path):
        """Test error when git not installed."""
```

**Estimated Effort**: 5-7 days
- Write ~100 new test cases
- Mock git operations
- Test all error paths
- Achieve 100% coverage

### 9.2 Integration Tests

**Scenarios**:
1. End-to-end catalog workflow (add, sync, search, remove)
2. Multi-catalog search across 3+ catalogs
3. Schema migration v1 → v2
4. Git sync with real git repository (local test repo)
5. Catalog overlay (base + local changes)

**Example Tests**:
```python
class TestMultiCatalogIntegration:
    def test_add_sync_search_workflow(self, tmp_path, git_test_repo):
        """Test complete workflow with real git repo."""
        # 1. Initialize catalog system
        # 2. Add catalog from git test repo
        # 3. Sync catalog
        # 4. Search servers in catalog
        # 5. Add server from catalog
        # 6. Verify server installed

    def test_cross_catalog_search(self, tmp_path):
        """Test search across multiple catalogs."""
        # Setup: 3 catalogs with overlapping servers
        # Search: Query appears in 2 catalogs
        # Expected: Results from both catalogs, deduplicated

    def test_catalog_migration(self, tmp_path):
        """Test v1 → v2 migration."""
        # Setup: Create v1 format catalog
        # Migrate: Run migration
        # Verify: Catalog now in v2 format
        # Verify: All servers preserved
```

**Estimated Effort**: 3-4 days

### 9.3 Existing Test Updates

**Impact**: 48 test files need review

**Categories**:
1. **Catalog mocking** (10 files): Update to use CatalogManager
2. **Factory function usage** (20 files): Verify backward compat
3. **CLI tests** (15 files): Add `--catalog` flag tests
4. **Integration tests** (3 files): Add multi-catalog scenarios

**Estimated Effort**: 2-3 days
- Review each file
- Update mocking patterns
- Verify backward compatibility
- Run full test suite

**Total Test Effort**: 10-14 days

---

## 10. Documentation Requirements

### 10.1 User Documentation

**New Sections**:
1. **Catalog Concepts**: Explain what catalogs are, why multiple catalogs
2. **Catalog Management**: How to add/remove/sync catalogs
3. **Local Catalog**: How to add custom servers
4. **Git Catalogs**: How to create and publish git-based catalogs
5. **Schema Versioning**: What schema versions mean, migration process
6. **Troubleshooting**: Common catalog issues and solutions

**Updates to Existing Docs**:
1. **Installation**: Mention catalog initialization on first run
2. **Quick Start**: Show catalog selection in examples
3. **CLI Reference**: Document new `catalog` subcommand
4. **Architecture**: Explain multi-catalog system

**Estimated Effort**: 3-4 days

### 10.2 Developer Documentation

**New Sections**:
1. **CatalogManager API**: How to use in code
2. **Creating Catalogs**: How to structure a catalog repository
3. **Schema Specification**: Full schema documentation (v2.0.0)
4. **Migration Guide**: How to migrate from v0.5.0 to v0.6.0
5. **Testing Catalogs**: How to test catalog code

**Estimated Effort**: 2-3 days

**Total Documentation Effort**: 5-7 days

---

## 11. Implementation Roadmap

### 11.1 Phase 1: Foundation (Week 1-2)

**Goal**: Core catalog infrastructure

**Tasks**:
1. Design and implement `CatalogMetadata` model (1 day)
2. Design and implement `CatalogManager` (2 days)
3. Update `ServerCatalog` for v2.0.0 format (1 day)
4. Implement catalog discovery (1 day)
5. Write unit tests (3 days)

**Deliverables**:
- `CatalogMetadata` class with Pydantic models
- `CatalogManager` class with multi-catalog support
- Updated `ServerCatalog` supporting both v1 and v2 formats
- 100% test coverage for new components

### 11.2 Phase 2: Git Integration (Week 2-3)

**Goal**: Git operations for catalogs

**Tasks**:
1. Design and implement `GitCatalogBackend` (2 days)
2. Implement git clone operation (1 day)
3. Implement git pull operation (1 day)
4. Implement git status operation (1 day)
5. Write unit tests with mocked git (2 days)
6. Integration tests with real git (1 day)

**Deliverables**:
- `GitCatalogBackend` class with git operations
- Error handling for all git failure modes
- 100% test coverage with mocked and real git tests

### 11.3 Phase 3: CLI Integration (Week 3-4)

**Goal**: CLI commands for catalog management

**Tasks**:
1. Implement `mcpi catalog` subcommand group (1 day)
2. Implement catalog list/add/remove commands (2 days)
3. Implement catalog sync/info commands (1 day)
4. Update existing commands for `--catalog` flag (2 days)
5. Update CLI tests (2 days)
6. Manual testing and bug fixes (1 day)

**Deliverables**:
- Complete `mcpi catalog` command suite
- Updated search/add commands with catalog selection
- All CLI tests passing

### 11.4 Phase 4: Migration and Docs (Week 4-5)

**Goal**: Migration, documentation, polish

**Tasks**:
1. Implement schema migration (v1 → v2) (2 days)
2. Implement auto-migration on first run (1 day)
3. Write migration tests (1 day)
4. Write user documentation (3 days)
5. Write developer documentation (2 days)
6. Update README and examples (1 day)

**Deliverables**:
- Working migration from v0.5.0 to v0.6.0
- Complete user documentation
- Complete developer documentation
- Updated README with multi-catalog examples

### 11.5 Phase 5: Testing and Polish (Week 5-6)

**Goal**: Comprehensive testing and polish

**Tasks**:
1. Run full test suite (1 day)
2. Fix failing tests (2 days)
3. Manual end-to-end testing (2 days)
4. Performance testing (1 day)
5. Bug fixes and polish (2 days)
6. Release preparation (1 day)

**Deliverables**:
- 100% test pass rate
- Performance benchmarks
- Release notes
- Migration guide

**Total Effort**: 4-6 weeks (1 developer, full-time)

---

## 12. Recommendation

### 12.1 DEFER to v0.6.0+

**Rationale**:
1. **DIP not complete**: Phases 2-4 pending (v0.4.0-v0.5.0)
2. **Architecture immature**: Injection patterns not fully established
3. **High complexity**: 4-6 weeks of development
4. **Breaking changes**: Schema format, CLI, tests
5. **No user demand**: No evidence users need multiple catalogs yet

**Better Approach**: Complete DIP first
- v0.4.0: Complete DIP Phase 2 (5 components)
- v0.5.0: Complete DIP Phases 3-4 (6 components)
- v0.6.0: Multi-catalog with clean DI patterns

**Benefits of Waiting**:
- Cleaner architecture: All components use DI
- Easier testing: Mock all dependencies
- Less refactoring: Build on stable foundation
- More user feedback: Learn what users actually need

### 12.2 Alternative: Minimal v0.6.0

**If Multi-Catalog is P1 (high priority)**:

Reduce scope to MVP:
1. **Two catalogs only**: 'official' (git) + 'local' (user)
2. **No catalog manager**: Simple if/else logic
3. **No overlay**: Local catalog is completely separate
4. **Manual git**: User clones, MCPI reads directory
5. **No migration**: Keep v1 format, add metadata as separate file

**Effort**: 2-3 weeks (vs. 4-6 weeks for full implementation)

**Tradeoffs**:
- Limited to 2 catalogs (no arbitrary catalogs)
- No sophisticated catalog management
- Manual git setup (user clones, MCPI doesn't manage)
- Technical debt (will need refactor later)

**Only recommend if**: User demand is high and feature is blocking

---

## 13. Risk Summary

### 13.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes affect users | HIGH | HIGH | Backward compat mode, migration tool |
| Git operations fail | MEDIUM | MEDIUM | Comprehensive error handling |
| Schema migration corrupts data | LOW | HIGH | Backup before migration, extensive tests |
| Performance degrades | LOW | MEDIUM | Lazy loading, caching |
| Test suite breaks | MEDIUM | HIGH | Systematic test updates |

### 13.2 Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | MEDIUM | HIGH | Strict MVP definition |
| Complexity underestimated | MEDIUM | MEDIUM | Add 20% buffer to estimates |
| DIP incomplete | HIGH | HIGH | Defer to v0.6.0+ |
| Testing takes longer | MEDIUM | MEDIUM | Parallel test development |

### 13.3 User Impact Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Users confused by migration | MEDIUM | MEDIUM | Clear messaging, docs |
| Users lose custom catalogs | LOW | HIGH | Backup before migration |
| Users don't need feature | HIGH | LOW | Gather feedback first |
| Breaking changes break scripts | MEDIUM | MEDIUM | Backward compat, deprecation period |

---

## 14. Conclusion

**Status**: Multi-catalog is a **v0.6.0+ FEATURE** requiring major architectural work

**Findings**:
- Current architecture: Single hardcoded catalog, no multi-catalog support
- Required changes: CatalogManager, git integration, schema versioning, CLI updates, test updates
- Breaking changes: Schema format, some CLI semantics, factory functions
- Effort estimate: 4-6 weeks (full implementation), 2-3 weeks (MVP)
- Test impact: 48 files need review, ~100 new tests needed
- Documentation: 5-7 days for complete docs

**Recommendation**: **DEFER to v0.6.0+**
- Complete DIP Phases 2-4 first (v0.4.0-v0.5.0)
- Build on mature dependency injection patterns
- Gather user feedback on multi-catalog need
- Consider MVP approach only if high user demand

**Next Steps** (if proceeding):
1. Create detailed technical design document
2. Get user feedback on feature design
3. Prototype CatalogManager and GitCatalogBackend
4. Validate performance assumptions
5. Create migration plan
6. Begin Phase 1 implementation

**Alternative**: If multi-catalog is P0, implement minimal version in v0.6.0 with these constraints:
- Two catalogs only (official + local)
- No sophisticated catalog manager
- Manual git operations
- Accept technical debt for later cleanup

---

**Status**: EVALUATION COMPLETE - READY FOR DECISION
**Confidence**: 95% (comprehensive analysis, clear recommendation)
**Next Action**: Review with stakeholders, decide on priority and timeline

---

*Evaluation conducted by: Project Auditor Agent*
*Date: 2025-11-17 02:18:48*
*MCPI Version: v0.3.0*
*Recommendation: DEFER to v0.6.0+ pending DIP completion*
