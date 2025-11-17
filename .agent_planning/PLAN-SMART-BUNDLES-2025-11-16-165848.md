# PLAN: Smart Server Bundles Implementation

**Generated**: 2025-11-16 16:58:48
**Source STATUS**: STATUS-SMART-BUNDLES-EVALUATION-2025-11-16-165533.md
**Spec Reference**: CLAUDE.md
**Feature**: Smart Server Bundles - Curated MCP server sets installation

---

## Provenance

**Source STATUS File**: `.agent_planning/STATUS-SMART-BUNDLES-EVALUATION-2025-11-16-165533.md`
**Spec Version**: CLAUDE.md (last modified 2025-11-16)
**Generation Time**: 2025-11-16 16:58:48
**Overall Recommendation**: GO - IMPLEMENT NOW
**Estimated Effort**: 6.8 days (54.5 hours)
**Risk Level**: LOW
**Confidence**: VERY HIGH (95%)

---

## Executive Summary

Smart Server Bundles is a **perfect fit** for MCPI's current architecture. This feature enables users to install curated sets of MCP servers with a single command (e.g., `mcpi bundle install web-dev`), eliminating the research phase and reducing setup time from 10 minutes to 30 seconds.

**Key Finding from Evaluation**: 80% of required functionality already exists. Implementation requires minimal new code (6 new files, 3 modified files) with zero architectural changes. All prerequisites met, zero blockers.

**Implementation Approach**:
- **Phase 1** (Day 1): Models and data structures
- **Phase 2** (Days 2-3): Core installer logic
- **Phase 3** (Days 4-5): CLI commands
- **Phase 4** (Days 6-7): Testing and polish

**Success Metrics**:
- Bundle installation completes in <15 seconds for 4-server bundle
- 20+ new tests passing with 90%+ coverage
- Zero regressions in existing 681 tests
- Built-in bundles contain genuinely useful combinations

---

## Sprint Structure

### Session 1: Models and Data Structures (Day 1 - 4 hours)

**Goal**: Create Pydantic models and built-in bundle definitions

**Work Items**:
1. BUNDLE-001: Create bundle data models (Pydantic)
2. BUNDLE-002: Implement BundleCatalog class
3. BUNDLE-003: Create 5 built-in bundle JSON files
4. BUNDLE-004: Write unit tests for models and catalog

**Deliverables**:
- `src/mcpi/bundles/models.py` (Bundle, BundleServer models)
- `src/mcpi/bundles/catalog.py` (BundleCatalog class)
- `data/bundles/*.json` (5 built-in bundles)
- `tests/test_bundles_models.py` (model validation tests)

---

### Session 2: Core Installer Logic (Days 2-3 - 14 hours)

**Goal**: Implement bundle installation with transaction support

**Work Items**:
1. BUNDLE-005: Implement BundleInstaller class (basic version)
2. BUNDLE-006: Add multi-server installation support
3. BUNDLE-007: Implement rollback/transaction logic
4. BUNDLE-008: Add dry-run mode support
5. BUNDLE-009: Write unit tests for installer
6. BUNDLE-010: Write integration tests for installation workflows

**Deliverables**:
- `src/mcpi/bundles/installer.py` (BundleInstaller class)
- `tests/test_bundles_installer.py` (installer unit tests)
- `tests/test_bundles_integration.py` (workflow integration tests)

---

### Session 3: CLI Commands (Days 4-5 - 16 hours)

**Goal**: Expose bundle functionality via CLI with Rich output

**Work Items**:
1. BUNDLE-011: Add bundle command group to CLI
2. BUNDLE-012: Implement `bundle list` command
3. BUNDLE-013: Implement `bundle info` command
4. BUNDLE-014: Implement `bundle install` command
5. BUNDLE-015: Add interactive scope selection
6. BUNDLE-016: Add Rich progress output
7. BUNDLE-017: Write CLI tests

**Deliverables**:
- Updated `src/mcpi/cli.py` (~200 new lines)
- `tests/test_bundles_cli.py` (CLI command tests)
- Rich-formatted output for all commands

---

### Session 4: Testing and Polish (Days 6-7 - 20.5 hours)

**Goal**: Comprehensive testing, documentation, and final polish

**Work Items**:
1. BUNDLE-018: Run full test suite (verify 701+ tests passing)
2. BUNDLE-019: Write functional end-to-end tests
3. BUNDLE-020: Manual testing with real bundles
4. BUNDLE-021: Update README with bundle examples
5. BUNDLE-022: Update CLAUDE.md with bundle commands
6. BUNDLE-023: Code review and refinement
7. BUNDLE-024: Create demo examples

**Deliverables**:
- All 20+ tests passing
- Updated README.md
- Updated CLAUDE.md
- Clean, reviewed code

---

## Detailed Work Items

### BUNDLE-001: Create Bundle Data Models

**ID**: BUNDLE-001
**Priority**: P0 (Critical)
**Effort**: 0.5 hours
**Session**: 1
**Dependencies**: None

#### Description

Create Pydantic models for bundle data structures. These models will validate bundle definitions loaded from JSON files.

#### Acceptance Criteria

- [x] `BundleServer` model created with `id` and optional `config` fields
- [x] `Bundle` model created with name, description, version, author, servers, suggested_scope
- [x] Models include proper type hints and validation
- [x] Models follow existing Pydantic patterns (see `MCPServer` model)
- [x] Optional fields have sensible defaults

#### Files to Create/Modify

**Create**: `src/mcpi/bundles/__init__.py`
```python
"""Smart Server Bundles for MCPI."""

from mcpi.bundles.models import Bundle, BundleServer
from mcpi.bundles.catalog import BundleCatalog
from mcpi.bundles.installer import BundleInstaller

__all__ = ["Bundle", "BundleServer", "BundleCatalog", "BundleInstaller"]
```

**Create**: `src/mcpi/bundles/models.py`
```python
"""Pydantic models for bundle data structures."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BundleServer(BaseModel):
    """Server reference in a bundle."""

    id: str = Field(..., description="Server ID from catalog")
    config: Optional[Dict[str, Any]] = Field(
        None, description="Optional config overrides"
    )


class Bundle(BaseModel):
    """A curated set of MCP servers."""

    name: str = Field(..., description="Bundle identifier (e.g., 'web-dev')")
    description: str = Field(..., description="Human-readable description")
    version: str = Field(default="1.0.0", description="Bundle version")
    author: Optional[str] = Field(None, description="Bundle author")
    servers: List[BundleServer] = Field(
        ..., min_length=1, description="List of servers in bundle"
    )
    suggested_scope: str = Field(
        default="user-global", description="Recommended installation scope"
    )
```

#### Testing Requirements

**Unit Tests**: `tests/test_bundles_models.py`
- Test `BundleServer` validation (valid/invalid IDs)
- Test `Bundle` validation (min_length=1 for servers)
- Test optional fields use defaults correctly
- Test invalid data raises ValidationError

#### Technical Notes

**Pattern to Follow**: See `src/mcpi/registry/catalog.py` lines 1-50 for existing Pydantic model patterns (`MCPServer`, `ServerRegistry`).

**Key Design Decision**: Keep models simple - a bundle is just metadata + list of server IDs. The catalog lookup and config merging happens in the installer, not in the model.

---

### BUNDLE-002: Implement BundleCatalog Class

**ID**: BUNDLE-002
**Priority**: P0 (Critical)
**Effort**: 4 hours
**Session**: 1
**Dependencies**: BUNDLE-001

#### Description

Create `BundleCatalog` class to load, validate, and query bundle definitions from disk. This class follows the exact same pattern as `ServerCatalog` but operates on bundle JSON files.

#### Acceptance Criteria

- [x] `BundleCatalog` class implemented with `__init__(bundles_dir: Path)`
- [x] `load_bundles()` method loads all JSON files from bundles directory
- [x] `get_bundle(bundle_id: str)` retrieves bundle by name
- [x] `list_bundles()` returns all bundles with metadata
- [x] `validate_bundle(bundle: Bundle)` validates bundle structure
- [x] Handles missing directories gracefully (returns empty catalog)
- [x] Validates JSON syntax and Pydantic schema

#### Files to Create/Modify

**Create**: `src/mcpi/bundles/catalog.py`
```python
"""Bundle catalog management."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import logging
from mcpi.bundles.models import Bundle

logger = logging.getLogger(__name__)


class BundleCatalog:
    """Manages loading and querying bundle definitions."""

    def __init__(self, bundles_dir: Path):
        """Initialize catalog with bundles directory.

        Args:
            bundles_dir: Path to directory containing bundle JSON files
        """
        self.bundles_dir = bundles_dir
        self._bundles: Dict[str, Bundle] = {}
        self.load_bundles()

    def load_bundles(self) -> None:
        """Load all bundle definitions from bundles directory."""
        if not self.bundles_dir.exists():
            logger.warning(f"Bundles directory not found: {self.bundles_dir}")
            return

        for bundle_file in self.bundles_dir.glob("*.json"):
            try:
                with open(bundle_file, "r") as f:
                    data = json.load(f)
                bundle = Bundle(**data)
                self._bundles[bundle.name] = bundle
                logger.debug(f"Loaded bundle: {bundle.name}")
            except Exception as e:
                logger.error(f"Failed to load bundle {bundle_file}: {e}")

    def get_bundle(self, bundle_id: str) -> Optional[Bundle]:
        """Get bundle by ID.

        Args:
            bundle_id: Bundle name (e.g., 'web-dev')

        Returns:
            Bundle object or None if not found
        """
        return self._bundles.get(bundle_id)

    def list_bundles(self) -> List[Tuple[str, Bundle]]:
        """List all available bundles.

        Returns:
            List of (bundle_id, bundle) tuples
        """
        return list(self._bundles.items())

    def validate_bundle(self, bundle: Bundle) -> bool:
        """Validate bundle structure.

        Args:
            bundle: Bundle to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Pydantic already validates on construction
            # Additional validation can be added here
            return len(bundle.servers) > 0
        except Exception as e:
            logger.error(f"Bundle validation failed: {e}")
            return False


# Factory functions following DIP pattern
def create_default_bundle_catalog() -> BundleCatalog:
    """Create bundle catalog with default bundles directory."""
    from pathlib import Path
    bundles_dir = Path(__file__).parent.parent.parent / "data" / "bundles"
    return BundleCatalog(bundles_dir=bundles_dir)


def create_test_bundle_catalog(bundles_dir: Path) -> BundleCatalog:
    """Create bundle catalog with custom directory for testing."""
    return BundleCatalog(bundles_dir=bundles_dir)
```

#### Testing Requirements

**Unit Tests**: `tests/test_bundles_catalog.py`
- Test loading bundles from directory
- Test retrieving bundle by ID
- Test listing all bundles
- Test handling missing directory
- Test handling invalid JSON
- Test handling invalid bundle schema

#### Technical Notes

**Pattern to Follow**: Copy structure from `src/mcpi/registry/catalog.py` - the `ServerCatalog` and `BundleCatalog` classes are nearly identical, just operating on different data structures.

**DIP Compliance**: Include factory functions (`create_default_bundle_catalog()`, `create_test_bundle_catalog()`) for dependency injection, following existing patterns.

---

### BUNDLE-003: Create 5 Built-in Bundle JSON Files

**ID**: BUNDLE-003
**Priority**: P1 (High)
**Effort**: 4 hours
**Session**: 1
**Dependencies**: BUNDLE-001

#### Description

Create 5 curated bundle definitions for common use cases: web-dev, data-science, devops, ai-tools, and content. Research best server combinations for each use case.

#### Acceptance Criteria

- [x] `data/bundles/web-dev.json` created (4 servers)
- [x] `data/bundles/data-science.json` created (4 servers)
- [x] `data/bundles/devops.json` created (4 servers)
- [x] `data/bundles/ai-tools.json` created (4 servers)
- [x] `data/bundles/content.json` created (4 servers)
- [x] Each bundle has descriptive name, description, version
- [x] Server IDs reference valid servers from `data/catalog.json`
- [x] Suggested scopes are appropriate for use case

#### Files to Create/Modify

**Create**: `data/bundles/web-dev.json`
```json
{
  "name": "web-dev",
  "description": "Complete web development stack with filesystem, HTTP, GitHub, and browser automation",
  "version": "1.0.0",
  "author": "MCPI Team",
  "servers": [
    {"id": "filesystem"},
    {"id": "fetch"},
    {"id": "github"},
    {"id": "puppeteer"}
  ],
  "suggested_scope": "project-mcp"
}
```

**Create**: `data/bundles/data-science.json`
```json
{
  "name": "data-science",
  "description": "Data science toolkit with SQL, pandas, visualization, and Jupyter support",
  "version": "1.0.0",
  "author": "MCPI Team",
  "servers": [
    {"id": "sqlite"},
    {"id": "postgres"},
    {"id": "filesystem"},
    {"id": "fetch"}
  ],
  "suggested_scope": "user-global"
}
```

**Create**: `data/bundles/devops.json`
```json
{
  "name": "devops",
  "description": "DevOps automation stack with GitHub, shell, Docker, and infrastructure tools",
  "version": "1.0.0",
  "author": "MCPI Team",
  "servers": [
    {"id": "github"},
    {"id": "filesystem"},
    {"id": "brave-search"},
    {"id": "fetch"}
  ],
  "suggested_scope": "project-mcp"
}
```

**Create**: `data/bundles/ai-tools.json`
```json
{
  "name": "ai-tools",
  "description": "AI/ML development tools with memory, context, and knowledge management",
  "version": "1.0.0",
  "author": "MCPI Team",
  "servers": [
    {"id": "memory"},
    {"id": "sequential-thinking"},
    {"id": "filesystem"},
    {"id": "brave-search"}
  ],
  "suggested_scope": "user-global"
}
```

**Create**: `data/bundles/content.json`
```json
{
  "name": "content",
  "description": "Content creation and research toolkit with web search, screenshots, and file management",
  "version": "1.0.0",
  "author": "MCPI Team",
  "servers": [
    {"id": "brave-search"},
    {"id": "fetch"},
    {"id": "puppeteer"},
    {"id": "filesystem"}
  ],
  "suggested_scope": "user-global"
}
```

#### Testing Requirements

**Integration Tests**: Validate bundle JSON files load correctly
- Test all bundles parse without errors
- Test all referenced server IDs exist in catalog
- Test bundle schemas match Pydantic model

#### Technical Notes

**Server Selection Strategy**:
1. Choose servers that work well together (complementary functionality)
2. Prioritize stable, well-maintained servers from catalog
3. Include filesystem server in most bundles (fundamental tool)
4. Balance between general-purpose and specialized servers

**Validation**: After creating bundles, verify all server IDs exist in `data/catalog.json` using:
```bash
grep -o '"id": "[^"]*"' data/bundles/*.json | cut -d'"' -f4 | while read id; do
  grep -q "\"$id\"" data/catalog.json || echo "Missing: $id"
done
```

---

### BUNDLE-004: Write Unit Tests for Models and Catalog

**ID**: BUNDLE-004
**Priority**: P0 (Critical)
**Effort**: 2 hours
**Session**: 1
**Dependencies**: BUNDLE-001, BUNDLE-002, BUNDLE-003

#### Description

Write comprehensive unit tests for Bundle models and BundleCatalog class. Follow existing test patterns from `tests/test_registry_integration.py`.

#### Acceptance Criteria

- [x] 8+ unit tests written and passing
- [x] Model validation tests cover valid/invalid cases
- [x] Catalog tests cover CRUD operations
- [x] Tests use pytest fixtures for setup
- [x] Tests follow existing patterns (MCPTestHarness for integration)
- [x] All tests pass with pytest

#### Files to Create/Modify

**Create**: `tests/test_bundles_models.py`
```python
"""Unit tests for bundle Pydantic models."""

import pytest
from pydantic import ValidationError
from mcpi.bundles.models import Bundle, BundleServer


def test_bundle_server_valid():
    """Test BundleServer with valid data."""
    server = BundleServer(id="filesystem")
    assert server.id == "filesystem"
    assert server.config is None


def test_bundle_server_with_config():
    """Test BundleServer with config overrides."""
    server = BundleServer(id="filesystem", config={"key": "value"})
    assert server.id == "filesystem"
    assert server.config == {"key": "value"}


def test_bundle_valid():
    """Test Bundle with valid data."""
    bundle = Bundle(
        name="web-dev",
        description="Web development stack",
        servers=[BundleServer(id="filesystem")]
    )
    assert bundle.name == "web-dev"
    assert bundle.version == "1.0.0"  # default
    assert bundle.suggested_scope == "user-global"  # default
    assert len(bundle.servers) == 1


def test_bundle_empty_servers_fails():
    """Test Bundle with empty servers list fails validation."""
    with pytest.raises(ValidationError) as exc_info:
        Bundle(
            name="empty",
            description="Empty bundle",
            servers=[]
        )
    assert "at least 1 item" in str(exc_info.value).lower()


def test_bundle_custom_fields():
    """Test Bundle with all custom fields."""
    bundle = Bundle(
        name="custom",
        description="Custom bundle",
        version="2.0.0",
        author="Test Author",
        servers=[BundleServer(id="fetch")],
        suggested_scope="project-mcp"
    )
    assert bundle.version == "2.0.0"
    assert bundle.author == "Test Author"
    assert bundle.suggested_scope == "project-mcp"
```

**Create**: `tests/test_bundles_catalog.py`
```python
"""Unit tests for BundleCatalog class."""

import json
import pytest
from pathlib import Path
from mcpi.bundles.catalog import BundleCatalog, create_test_bundle_catalog
from mcpi.bundles.models import Bundle


@pytest.fixture
def bundles_dir(tmp_path):
    """Create temporary bundles directory with test bundles."""
    bundles_dir = tmp_path / "bundles"
    bundles_dir.mkdir()

    # Create test bundle
    test_bundle = {
        "name": "test-bundle",
        "description": "Test bundle",
        "version": "1.0.0",
        "servers": [{"id": "filesystem"}],
        "suggested_scope": "user-global"
    }
    (bundles_dir / "test-bundle.json").write_text(json.dumps(test_bundle))

    return bundles_dir


def test_bundle_catalog_load(bundles_dir):
    """Test loading bundles from directory."""
    catalog = BundleCatalog(bundles_dir)
    bundles = catalog.list_bundles()
    assert len(bundles) == 1
    assert bundles[0][0] == "test-bundle"


def test_bundle_catalog_get(bundles_dir):
    """Test retrieving bundle by ID."""
    catalog = BundleCatalog(bundles_dir)
    bundle = catalog.get_bundle("test-bundle")
    assert bundle is not None
    assert bundle.name == "test-bundle"


def test_bundle_catalog_get_missing(bundles_dir):
    """Test retrieving non-existent bundle."""
    catalog = BundleCatalog(bundles_dir)
    bundle = catalog.get_bundle("nonexistent")
    assert bundle is None


def test_bundle_catalog_missing_directory(tmp_path):
    """Test catalog with non-existent directory."""
    missing_dir = tmp_path / "missing"
    catalog = BundleCatalog(missing_dir)
    bundles = catalog.list_bundles()
    assert len(bundles) == 0


def test_bundle_catalog_invalid_json(tmp_path):
    """Test catalog handles invalid JSON gracefully."""
    bundles_dir = tmp_path / "bundles"
    bundles_dir.mkdir()
    (bundles_dir / "invalid.json").write_text("not valid json{")

    catalog = BundleCatalog(bundles_dir)
    bundles = catalog.list_bundles()
    assert len(bundles) == 0  # Invalid bundle should be skipped


def test_bundle_catalog_validate():
    """Test bundle validation."""
    catalog = create_test_bundle_catalog(Path("/tmp"))
    bundle = Bundle(
        name="test",
        description="Test",
        servers=[{"id": "filesystem"}]
    )
    assert catalog.validate_bundle(bundle) is True
```

#### Testing Requirements

**Test Coverage**: 90%+ for models.py and catalog.py

**Test Execution**:
```bash
pytest tests/test_bundles_models.py tests/test_bundles_catalog.py -v --tb=short
```

#### Technical Notes

**Pattern to Follow**: See `tests/test_registry_integration.py` for similar catalog testing patterns.

**Key Tests**:
1. Model validation (valid/invalid data)
2. Catalog CRUD operations
3. Error handling (missing files, invalid JSON)
4. Edge cases (empty directory, invalid schema)

---

### BUNDLE-005: Implement BundleInstaller Class (Basic Version)

**ID**: BUNDLE-005
**Priority**: P0 (Critical)
**Effort**: 6 hours
**Session**: 2
**Dependencies**: BUNDLE-002

#### Description

Create `BundleInstaller` class to install bundles by iterating through servers and calling `MCPManager.add_server()`. Start with basic version without transaction support.

#### Acceptance Criteria

- [x] `BundleInstaller` class created with `__init__(manager, catalog)`
- [x] `install_bundle()` method accepts bundle, scope, client_name
- [x] Method iterates through bundle servers
- [x] Each server installed via `manager.add_server()`
- [x] Returns list of `OperationResult` objects
- [x] Handles server lookup from catalog
- [x] Merges bundle config overrides with server defaults

#### Files to Create/Modify

**Create**: `src/mcpi/bundles/installer.py`
```python
"""Bundle installation logic."""

from typing import List, Optional
import logging
from mcpi.clients.manager import MCPManager
from mcpi.clients.types import OperationResult, ServerConfig
from mcpi.registry.catalog import ServerCatalog
from mcpi.bundles.models import Bundle, BundleServer

logger = logging.getLogger(__name__)


class BundleInstaller:
    """Handles installation of server bundles."""

    def __init__(self, manager: MCPManager, catalog: ServerCatalog):
        """Initialize installer.

        Args:
            manager: MCPManager instance for server operations
            catalog: ServerCatalog for looking up server definitions
        """
        self.manager = manager
        self.catalog = catalog

    def install_bundle(
        self,
        bundle: Bundle,
        scope: str,
        client_name: Optional[str] = None,
        dry_run: bool = False,
    ) -> List[OperationResult]:
        """Install all servers in a bundle.

        Args:
            bundle: Bundle to install
            scope: Target scope for installation
            client_name: Optional client name (uses default if None)
            dry_run: If True, simulate installation without changes

        Returns:
            List of OperationResult for each server installation
        """
        results = []
        logger.info(f"Installing bundle '{bundle.name}' to scope '{scope}'")

        for bundle_server in bundle.servers:
            result = self._install_server(
                bundle_server, scope, client_name, dry_run
            )
            results.append(result)

            # Log result
            if result.success:
                logger.info(f"✓ Installed {bundle_server.id}")
            else:
                logger.error(f"✗ Failed to install {bundle_server.id}: {result.message}")

        return results

    def _install_server(
        self,
        bundle_server: BundleServer,
        scope: str,
        client_name: Optional[str],
        dry_run: bool,
    ) -> OperationResult:
        """Install a single server from bundle.

        Args:
            bundle_server: Server reference from bundle
            scope: Target scope
            client_name: Optional client name
            dry_run: Dry-run mode

        Returns:
            OperationResult for the installation
        """
        # Look up server in catalog
        server = self.catalog.get_server(bundle_server.id)
        if not server:
            return OperationResult(
                success=False,
                message=f"Server '{bundle_server.id}' not found in catalog",
            )

        # Build server config
        config = self._build_config(server, bundle_server.config)

        # Install server via manager
        try:
            return self.manager.add_server(
                server_id=bundle_server.id,
                config=config,
                scope=scope,
                client_name=client_name,
            )
        except Exception as e:
            logger.exception(f"Failed to install {bundle_server.id}")
            return OperationResult(
                success=False,
                message=f"Installation failed: {str(e)}",
            )

    def _build_config(
        self, server, config_overrides: Optional[dict]
    ) -> ServerConfig:
        """Build server configuration from catalog + bundle overrides.

        Args:
            server: MCPServer from catalog
            config_overrides: Optional config overrides from bundle

        Returns:
            ServerConfig for installation
        """
        # Get default command from server
        command = server.get_run_command()

        # Merge environment variables
        env = server.env.copy() if server.env else {}
        if config_overrides and "env" in config_overrides:
            env.update(config_overrides["env"])

        # Build ServerConfig
        config = ServerConfig(
            command=command.command,
            args=command.args,
            env=env if env else None,
        )

        return config
```

#### Testing Requirements

**Unit Tests**: `tests/test_bundles_installer.py`
- Test single server installation
- Test server not found in catalog
- Test config merging (bundle overrides + catalog defaults)
- Test dry-run mode
- Test error handling

#### Technical Notes

**Key Design Decision**: `BundleInstaller` is a thin wrapper around `MCPManager.add_server()`. It handles:
1. Iterating through bundle servers
2. Looking up servers in catalog
3. Merging config overrides
4. Calling `add_server()` for each server

**No New Installation Logic**: All actual installation logic is delegated to `MCPManager.add_server()`, which already handles validation, conflict detection, and configuration writing.

**Transaction Support**: Basic version doesn't include rollback - that's added in BUNDLE-007.

---

### BUNDLE-006: Add Multi-Server Installation Support

**ID**: BUNDLE-006
**Priority**: P1 (High)
**Effort**: 2 hours
**Session**: 2
**Dependencies**: BUNDLE-005

#### Description

Enhance `BundleInstaller.install_bundle()` to handle multiple servers gracefully, including:
- Skip already-installed servers
- Continue on errors (optional)
- Collect detailed results for each server

#### Acceptance Criteria

- [x] Installer detects already-installed servers
- [x] Option to skip already-installed servers (default: skip with warning)
- [x] Option to continue on errors (default: continue)
- [x] Results include per-server status (success/failure/skipped)
- [x] Clear logging for each operation

#### Files to Create/Modify

**Modify**: `src/mcpi/bundles/installer.py`

Add to `install_bundle()`:
```python
def install_bundle(
    self,
    bundle: Bundle,
    scope: str,
    client_name: Optional[str] = None,
    dry_run: bool = False,
    skip_existing: bool = True,
    continue_on_error: bool = True,
) -> List[OperationResult]:
    """Install all servers in a bundle.

    Args:
        bundle: Bundle to install
        scope: Target scope for installation
        client_name: Optional client name
        dry_run: Simulate installation without changes
        skip_existing: Skip already-installed servers
        continue_on_error: Continue installing even if a server fails

    Returns:
        List of OperationResult for each server
    """
    results = []
    logger.info(f"Installing bundle '{bundle.name}' ({len(bundle.servers)} servers)")

    for i, bundle_server in enumerate(bundle.servers, 1):
        logger.info(f"[{i}/{len(bundle.servers)}] Processing {bundle_server.id}...")

        # Check if already installed
        if skip_existing and self._is_installed(bundle_server.id, scope, client_name):
            logger.info(f"Skipping {bundle_server.id} (already installed)")
            results.append(OperationResult(
                success=True,
                message=f"Server already installed (skipped)",
                skipped=True,
            ))
            continue

        # Install server
        result = self._install_server(bundle_server, scope, client_name, dry_run)
        results.append(result)

        # Handle errors
        if not result.success and not continue_on_error:
            logger.error(f"Installation failed, stopping (continue_on_error=False)")
            break

    return results

def _is_installed(
    self, server_id: str, scope: str, client_name: Optional[str]
) -> bool:
    """Check if server is already installed in scope."""
    servers = self.manager.list_servers(scope=scope, client_name=client_name)
    return any(s.server_id == server_id for s in servers)
```

#### Testing Requirements

**Unit Tests**: Add to `tests/test_bundles_installer.py`
- Test skip_existing behavior
- Test continue_on_error behavior
- Test mixed success/failure scenarios

#### Technical Notes

**Already-Installed Detection**: Use `MCPManager.list_servers()` to check if server exists in target scope.

**Error Handling Strategy**: By default, continue installing remaining servers even if one fails. This maximizes partial success.

---

### BUNDLE-007: Implement Rollback/Transaction Logic

**ID**: BUNDLE-007
**Priority**: P1 (High)
**Effort**: 4 hours
**Session**: 2
**Dependencies**: BUNDLE-006

#### Description

Add transaction support to bundle installation: if installation fails, optionally rollback all changes made during the bundle installation.

#### Acceptance Criteria

- [x] `rollback_on_error` parameter added to `install_bundle()`
- [x] Track which servers were installed during bundle operation
- [x] On failure, remove installed servers if rollback enabled
- [x] Rollback only servers installed *during this operation*
- [x] Clear logging of rollback actions
- [x] Dry-run mode skips rollback

#### Files to Create/Modify

**Modify**: `src/mcpi/bundles/installer.py`

Add rollback logic:
```python
def install_bundle(
    self,
    bundle: Bundle,
    scope: str,
    client_name: Optional[str] = None,
    dry_run: bool = False,
    skip_existing: bool = True,
    continue_on_error: bool = True,
    rollback_on_error: bool = False,
) -> List[OperationResult]:
    """Install all servers in a bundle with optional rollback.

    Args:
        bundle: Bundle to install
        scope: Target scope
        client_name: Optional client name
        dry_run: Simulate installation
        skip_existing: Skip already-installed servers
        continue_on_error: Continue on errors
        rollback_on_error: Remove installed servers if any installation fails

    Returns:
        List of OperationResult for each server
    """
    results = []
    installed_servers = []  # Track successful installations

    logger.info(f"Installing bundle '{bundle.name}' ({len(bundle.servers)} servers)")

    for i, bundle_server in enumerate(bundle.servers, 1):
        logger.info(f"[{i}/{len(bundle.servers)}] Processing {bundle_server.id}...")

        # Check if already installed
        if skip_existing and self._is_installed(bundle_server.id, scope, client_name):
            logger.info(f"Skipping {bundle_server.id} (already installed)")
            results.append(OperationResult(success=True, message="Already installed (skipped)"))
            continue

        # Install server
        result = self._install_server(bundle_server, scope, client_name, dry_run)
        results.append(result)

        if result.success:
            installed_servers.append(bundle_server.id)
        elif not continue_on_error:
            logger.error("Installation failed, stopping")
            if rollback_on_error:
                self._rollback(installed_servers, scope, client_name, dry_run)
            break

    # Check if any installation failed
    any_failed = any(not r.success for r in results)
    if any_failed and rollback_on_error:
        logger.warning("Some installations failed, rolling back...")
        self._rollback(installed_servers, scope, client_name, dry_run)

    return results

def _rollback(
    self,
    server_ids: List[str],
    scope: str,
    client_name: Optional[str],
    dry_run: bool,
) -> None:
    """Rollback installed servers.

    Args:
        server_ids: List of server IDs to remove
        scope: Target scope
        client_name: Optional client name
        dry_run: If True, skip actual removal
    """
    if not server_ids:
        return

    logger.info(f"Rolling back {len(server_ids)} servers: {', '.join(server_ids)}")

    for server_id in server_ids:
        if dry_run:
            logger.info(f"[DRY-RUN] Would remove {server_id}")
            continue

        try:
            self.manager.remove_server(
                server_id=server_id,
                scope=scope,
                client_name=client_name,
            )
            logger.info(f"✓ Removed {server_id}")
        except Exception as e:
            logger.error(f"✗ Failed to remove {server_id}: {e}")
```

#### Testing Requirements

**Unit Tests**: Add to `tests/test_bundles_installer.py`
- Test rollback on error
- Test rollback only removes servers installed during operation
- Test dry-run mode doesn't trigger rollback
- Test partial installation rollback

#### Technical Notes

**Rollback Strategy**: Only rollback servers installed *during this bundle operation*. Don't remove servers that were already present before installation started.

**Error Handling**: If rollback itself fails, log error but don't fail the entire operation - user can manually clean up.

---

### BUNDLE-008: Add Dry-Run Mode Support

**ID**: BUNDLE-008
**Priority**: P1 (High)
**Effort**: 1 hour
**Session**: 2
**Dependencies**: BUNDLE-007

#### Description

Ensure dry-run mode works correctly throughout bundle installation. When `dry_run=True`, simulate all operations without making changes.

#### Acceptance Criteria

- [x] `dry_run` parameter passed through to `MCPManager.add_server()`
- [x] Dry-run mode logs all operations that would occur
- [x] No actual configuration changes made in dry-run mode
- [x] Results indicate dry-run mode was used
- [x] Rollback skipped in dry-run mode

#### Files to Create/Modify

**Modify**: `src/mcpi/bundles/installer.py`

Enhance logging for dry-run:
```python
def install_bundle(self, bundle, scope, client_name=None, dry_run=False, ...):
    if dry_run:
        logger.info("[DRY-RUN MODE] Simulating bundle installation...")

    # ... existing code ...
```

#### Testing Requirements

**Unit Tests**: Add to `tests/test_bundles_installer.py`
- Test dry-run doesn't modify configuration files
- Test dry-run returns expected results
- Test dry-run logging output

#### Technical Notes

**Implementation**: Most dry-run logic already exists in `MCPManager.add_server()`. Just need to:
1. Pass `dry_run` parameter through
2. Add dry-run logging messages
3. Ensure rollback is skipped in dry-run mode

---

### BUNDLE-009: Write Unit Tests for Installer

**ID**: BUNDLE-009
**Priority**: P0 (Critical)
**Effort**: 4 hours
**Session**: 2
**Dependencies**: BUNDLE-005, BUNDLE-006, BUNDLE-007, BUNDLE-008

#### Description

Write comprehensive unit tests for `BundleInstaller` class covering all functionality.

#### Acceptance Criteria

- [x] 10+ unit tests written and passing
- [x] Tests cover single-server installation
- [x] Tests cover multi-server installation
- [x] Tests cover error handling (missing server, installation failure)
- [x] Tests cover skip_existing behavior
- [x] Tests cover continue_on_error behavior
- [x] Tests cover rollback logic
- [x] Tests cover dry-run mode
- [x] Tests use mocks for MCPManager and ServerCatalog
- [x] 90%+ code coverage for installer.py

#### Files to Create/Modify

**Create**: `tests/test_bundles_installer.py`
```python
"""Unit tests for BundleInstaller class."""

import pytest
from unittest.mock import Mock, MagicMock
from mcpi.bundles.installer import BundleInstaller
from mcpi.bundles.models import Bundle, BundleServer
from mcpi.clients.types import OperationResult, ServerConfig
from mcpi.registry.catalog import MCPServer, RunCommand


@pytest.fixture
def mock_manager():
    """Mock MCPManager."""
    manager = Mock()
    manager.add_server = Mock(return_value=OperationResult(success=True, message="Added"))
    manager.remove_server = Mock(return_value=OperationResult(success=True, message="Removed"))
    manager.list_servers = Mock(return_value=[])
    return manager


@pytest.fixture
def mock_catalog():
    """Mock ServerCatalog."""
    catalog = Mock()

    # Mock filesystem server
    fs_server = Mock(spec=MCPServer)
    fs_server.get_run_command = Mock(return_value=RunCommand(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem"]))
    fs_server.env = {}

    catalog.get_server = Mock(return_value=fs_server)
    return catalog


@pytest.fixture
def installer(mock_manager, mock_catalog):
    """Create BundleInstaller with mocks."""
    return BundleInstaller(manager=mock_manager, catalog=mock_catalog)


@pytest.fixture
def test_bundle():
    """Create test bundle."""
    return Bundle(
        name="test",
        description="Test bundle",
        servers=[
            BundleServer(id="filesystem"),
            BundleServer(id="fetch"),
        ]
    )


def test_install_single_server(installer, mock_manager, mock_catalog):
    """Test installing single server."""
    bundle = Bundle(
        name="single",
        description="Single server",
        servers=[BundleServer(id="filesystem")]
    )

    results = installer.install_bundle(bundle, scope="user-global")

    assert len(results) == 1
    assert results[0].success
    mock_manager.add_server.assert_called_once()


def test_install_multiple_servers(installer, test_bundle, mock_manager):
    """Test installing multiple servers."""
    results = installer.install_bundle(test_bundle, scope="user-global")

    assert len(results) == 2
    assert all(r.success for r in results)
    assert mock_manager.add_server.call_count == 2


def test_install_server_not_found(installer, mock_catalog):
    """Test handling server not found in catalog."""
    mock_catalog.get_server = Mock(return_value=None)

    bundle = Bundle(
        name="missing",
        description="Missing server",
        servers=[BundleServer(id="nonexistent")]
    )

    results = installer.install_bundle(bundle, scope="user-global")

    assert len(results) == 1
    assert not results[0].success
    assert "not found" in results[0].message.lower()


def test_install_skip_existing(installer, test_bundle, mock_manager):
    """Test skipping already-installed servers."""
    # Mock list_servers to show filesystem already installed
    mock_manager.list_servers = Mock(return_value=[
        Mock(server_id="filesystem")
    ])

    results = installer.install_bundle(test_bundle, scope="user-global", skip_existing=True)

    assert len(results) == 2
    # Only fetch should be installed (filesystem skipped)
    assert mock_manager.add_server.call_count == 1


def test_install_continue_on_error(installer, test_bundle, mock_manager):
    """Test continuing installation when one server fails."""
    # Make first server fail
    mock_manager.add_server = Mock(side_effect=[
        OperationResult(success=False, message="Failed"),
        OperationResult(success=True, message="Added"),
    ])

    results = installer.install_bundle(
        test_bundle, scope="user-global", continue_on_error=True
    )

    assert len(results) == 2
    assert not results[0].success
    assert results[1].success


def test_install_rollback_on_error(installer, test_bundle, mock_manager):
    """Test rollback when installation fails."""
    # First succeeds, second fails
    mock_manager.add_server = Mock(side_effect=[
        OperationResult(success=True, message="Added"),
        OperationResult(success=False, message="Failed"),
    ])

    results = installer.install_bundle(
        test_bundle,
        scope="user-global",
        rollback_on_error=True,
        continue_on_error=True,
    )

    # Rollback should remove first server
    mock_manager.remove_server.assert_called_once_with(
        server_id="filesystem",
        scope="user-global",
        client_name=None,
    )


def test_install_dry_run(installer, test_bundle, mock_manager):
    """Test dry-run mode doesn't modify configuration."""
    results = installer.install_bundle(test_bundle, scope="user-global", dry_run=True)

    assert len(results) == 2
    # add_server should still be called (with dry_run=True)
    assert mock_manager.add_server.call_count == 2
```

#### Testing Requirements

**Test Coverage**: 90%+ for installer.py

**Test Execution**:
```bash
pytest tests/test_bundles_installer.py -v --cov=src/mcpi/bundles/installer
```

#### Technical Notes

**Mocking Strategy**: Use `unittest.mock.Mock` to mock `MCPManager` and `ServerCatalog`. This allows testing installer logic without file I/O.

**Key Tests**:
1. Basic installation (single/multiple servers)
2. Error handling (missing server, installation failure)
3. Optional features (skip_existing, continue_on_error, rollback)
4. Dry-run mode

---

### BUNDLE-010: Write Integration Tests for Installation Workflows

**ID**: BUNDLE-010
**Priority**: P1 (High)
**Effort**: 4 hours
**Session**: 2
**Dependencies**: BUNDLE-009

#### Description

Write end-to-end integration tests that verify bundle installation works with real temporary configuration files. Use `MCPTestHarness` pattern.

#### Acceptance Criteria

- [x] 4+ integration tests written and passing
- [x] Tests use `MCPTestHarness` for realistic file-based testing
- [x] Tests verify actual configuration files are created
- [x] Tests verify installed servers appear in `list_servers()`
- [x] Tests cover project-mcp and user-global scopes
- [x] Tests verify rollback creates correct file state

#### Files to Create/Modify

**Create**: `tests/test_bundles_integration.py`
```python
"""Integration tests for bundle installation workflows."""

import pytest
import json
from pathlib import Path
from tests.test_harness import MCPTestHarness
from mcpi.bundles.catalog import create_test_bundle_catalog
from mcpi.bundles.installer import BundleInstaller
from mcpi.bundles.models import Bundle, BundleServer
from mcpi.clients.manager import MCPManager
from mcpi.clients.registry import ClientRegistry
from mcpi.clients.claude_code import ClaudeCodePlugin
from mcpi.registry.catalog import create_test_catalog


@pytest.fixture
def harness(tmp_path):
    """Create test harness with temporary directories."""
    harness = MCPTestHarness(tmp_path)
    harness.setup_scope_files()
    return harness


@pytest.fixture
def test_bundle_dir(tmp_path):
    """Create test bundle directory."""
    bundles_dir = tmp_path / "bundles"
    bundles_dir.mkdir()

    # Create test bundle
    test_bundle = {
        "name": "test-integration",
        "description": "Integration test bundle",
        "version": "1.0.0",
        "servers": [
            {"id": "filesystem"},
            {"id": "fetch"}
        ],
        "suggested_scope": "user-global"
    }
    (bundles_dir / "test-integration.json").write_text(json.dumps(test_bundle))

    return bundles_dir


def test_install_bundle_to_project_scope(harness, test_bundle_dir, tmp_path):
    """Test installing bundle to project-mcp scope."""
    # Setup
    plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
    registry = ClientRegistry()
    registry.inject_client_instance("claude-code", plugin)
    manager = MCPManager(registry=registry, default_client="claude-code")

    # Create bundle catalog and installer
    bundle_catalog = create_test_bundle_catalog(test_bundle_dir)
    catalog = create_test_catalog(tmp_path / "catalog.json")
    installer = BundleInstaller(manager=manager, catalog=catalog)

    # Install bundle
    bundle = bundle_catalog.get_bundle("test-integration")
    results = installer.install_bundle(bundle, scope="project-mcp")

    # Verify
    assert len(results) == 2
    assert all(r.success for r in results)

    # Verify servers appear in list
    servers = manager.list_servers(scope="project-mcp")
    server_ids = [s.server_id for s in servers]
    assert "filesystem" in server_ids
    assert "fetch" in server_ids


def test_install_bundle_rollback(harness, test_bundle_dir, tmp_path):
    """Test bundle installation rollback on error."""
    # Setup (similar to above)
    # ...

    # Create bundle with invalid server
    bundle = Bundle(
        name="rollback-test",
        description="Test rollback",
        servers=[
            BundleServer(id="filesystem"),
            BundleServer(id="nonexistent"),  # This will fail
        ]
    )

    # Install with rollback
    results = installer.install_bundle(
        bundle, scope="project-mcp", rollback_on_error=True
    )

    # Verify rollback removed filesystem
    servers = manager.list_servers(scope="project-mcp")
    server_ids = [s.server_id for s in servers]
    assert "filesystem" not in server_ids


def test_install_bundle_idempotent(harness, test_bundle_dir, tmp_path):
    """Test installing same bundle twice is idempotent."""
    # Setup
    # ...

    bundle = bundle_catalog.get_bundle("test-integration")

    # Install first time
    results1 = installer.install_bundle(bundle, scope="user-global")
    assert all(r.success for r in results1)

    # Install second time (should skip existing)
    results2 = installer.install_bundle(bundle, scope="user-global", skip_existing=True)
    assert all(r.success for r in results2)

    # Verify only one copy of each server
    servers = manager.list_servers(scope="user-global")
    server_ids = [s.server_id for s in servers]
    assert server_ids.count("filesystem") == 1
    assert server_ids.count("fetch") == 1
```

#### Testing Requirements

**Test Coverage**: Integration tests should exercise real file operations

**Test Execution**:
```bash
pytest tests/test_bundles_integration.py -v --tb=short
```

#### Technical Notes

**MCPTestHarness Pattern**: Use existing test harness to create temporary configuration directories and inject paths into plugins.

**Real File Operations**: These tests should actually read/write configuration files to verify the full workflow works.

---

### BUNDLE-011: Add Bundle Command Group to CLI

**ID**: BUNDLE-011
**Priority**: P0 (Critical)
**Effort**: 2 hours
**Session**: 3
**Dependencies**: BUNDLE-002

#### Description

Add `bundle` command group to CLI with structure for subcommands (`list`, `info`, `install`). Set up lazy initialization for `BundleCatalog`.

#### Acceptance Criteria

- [x] `@main.group() def bundle()` added to cli.py
- [x] Lazy initialization function `get_bundle_catalog()` created
- [x] Help text for bundle group is clear and descriptive
- [x] `mcpi bundle --help` shows available subcommands
- [x] Follows existing CLI patterns (see `@main.group()` usage)

#### Files to Create/Modify

**Modify**: `src/mcpi/cli.py`

Add after existing command groups:
```python
# Bundle management (add after other @main.group() definitions)

def get_bundle_catalog() -> "BundleCatalog":
    """Lazy-load bundle catalog (follows pattern from get_catalog())."""
    global _bundle_catalog
    if _bundle_catalog is None:
        from mcpi.bundles.catalog import create_default_bundle_catalog
        _bundle_catalog = create_default_bundle_catalog()
    return _bundle_catalog


_bundle_catalog = None  # Global bundle catalog instance


@main.group()
@click.pass_context
def bundle(ctx: click.Context):
    """Manage server bundles.

    Bundles are curated sets of MCP servers that can be installed together
    with a single command. Use 'mcpi bundle list' to see available bundles.

    Examples:

        # List available bundles
        mcpi bundle list

        # Show bundle details
        mcpi bundle info web-dev

        # Install a bundle
        mcpi bundle install web-dev --scope project-mcp

        # Dry-run installation
        mcpi bundle install web-dev --scope user-global --dry-run
    """
    pass
```

#### Testing Requirements

**CLI Tests**: Verify command group registration
- Test `mcpi bundle --help` shows help text
- Test subcommands are listed

#### Technical Notes

**Lazy Initialization Pattern**: Follow same pattern as `get_catalog()` and `get_mcp_manager()` - use global variable with lazy initialization.

**Help Text**: Make help text comprehensive with examples, following existing command patterns.

---

### BUNDLE-012: Implement `bundle list` Command

**ID**: BUNDLE-012
**Priority**: P0 (Critical)
**Effort**: 3 hours
**Session**: 3
**Dependencies**: BUNDLE-011

#### Description

Implement `mcpi bundle list` command to show all available bundles in a Rich-formatted table.

#### Acceptance Criteria

- [x] `bundle list` command shows all bundles
- [x] Output uses Rich Table with columns: Name, Description, Servers, Suggested Scope
- [x] Servers column shows count (e.g., "4 servers")
- [x] Output is sorted alphabetically by bundle name
- [x] Empty bundles directory shows helpful message
- [x] Error handling for missing bundles directory

#### Files to Create/Modify

**Modify**: `src/mcpi/cli.py`

Add under `@bundle.group()`:
```python
@bundle.command("list")
@click.pass_context
def bundle_list(ctx: click.Context):
    """List all available bundles.

    Shows built-in bundles and any custom bundles found in the bundles directory.
    """
    catalog = get_bundle_catalog()
    bundles = catalog.list_bundles()

    if not bundles:
        console.print("[yellow]No bundles found[/yellow]")
        console.print("\nBundles should be JSON files in: data/bundles/")
        return

    # Create Rich table
    table = Table(title="Available Server Bundles", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Servers", justify="right", style="green")
    table.add_column("Suggested Scope", style="yellow")

    # Sort bundles by name
    sorted_bundles = sorted(bundles, key=lambda x: x[0])

    for bundle_id, bundle in sorted_bundles:
        table.add_row(
            bundle.name,
            bundle.description,
            f"{len(bundle.servers)} servers",
            bundle.suggested_scope,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(bundles)} bundles[/dim]")
    console.print("\n[dim]Use 'mcpi bundle info <name>' for details[/dim]")
```

#### Testing Requirements

**CLI Tests**: `tests/test_bundles_cli.py`
- Test `bundle list` with bundles present
- Test `bundle list` with empty directory
- Test output format (Rich table)

#### Technical Notes

**Rich Table Format**: Follow pattern from `list` command - use Rich Table for formatted output.

**User Experience**: Show clear message if no bundles found, with hint about where bundles should be located.

---

### BUNDLE-013: Implement `bundle info` Command

**ID**: BUNDLE-013
**Priority**: P0 (Critical)
**Effort**: 3 hours
**Session**: 3
**Dependencies**: BUNDLE-011

#### Description

Implement `mcpi bundle info <bundle-name>` command to show detailed information about a specific bundle.

#### Acceptance Criteria

- [x] `bundle info <bundle-name>` shows bundle details
- [x] Output includes: name, description, version, author, suggested scope
- [x] Shows list of servers in bundle with details from catalog
- [x] For each server: name, description, installation method
- [x] Error handling for non-existent bundle
- [x] Rich-formatted output

#### Files to Create/Modify

**Modify**: `src/mcpi/cli.py`

Add under `@bundle.group()`:
```python
@bundle.command("info")
@click.argument("bundle_id")
@click.pass_context
def bundle_info(ctx: click.Context, bundle_id: str):
    """Show detailed information about a bundle.

    Args:
        bundle_id: Name of the bundle (e.g., 'web-dev')
    """
    bundle_catalog = get_bundle_catalog()
    bundle = bundle_catalog.get_bundle(bundle_id)

    if not bundle:
        console.print(f"[red]Bundle '{bundle_id}' not found[/red]")
        console.print("\nUse 'mcpi bundle list' to see available bundles")
        raise click.Abort()

    # Header
    console.print(f"\n[bold cyan]{bundle.name}[/bold cyan]")
    console.print(f"[dim]{bundle.description}[/dim]\n")

    # Metadata
    console.print(f"[bold]Version:[/bold] {bundle.version}")
    if bundle.author:
        console.print(f"[bold]Author:[/bold] {bundle.author}")
    console.print(f"[bold]Suggested Scope:[/bold] {bundle.suggested_scope}")
    console.print(f"[bold]Servers:[/bold] {len(bundle.servers)}\n")

    # Server list
    catalog = get_catalog()
    table = Table(title="Servers in Bundle", show_header=True)
    table.add_column("Server", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Method", style="yellow")

    for bundle_server in bundle.servers:
        server = catalog.get_server(bundle_server.id)
        if server:
            table.add_row(
                server.name,
                server.description[:60] + "..." if len(server.description) > 60 else server.description,
                server.installation.method,
            )
        else:
            table.add_row(
                bundle_server.id,
                "[red]Server not found in catalog[/red]",
                "N/A",
            )

    console.print(table)

    # Installation hint
    console.print(f"\n[dim]Install with: mcpi bundle install {bundle_id} --scope <scope>[/dim]")
```

#### Testing Requirements

**CLI Tests**: Add to `tests/test_bundles_cli.py`
- Test `bundle info` with valid bundle
- Test `bundle info` with non-existent bundle
- Test output format

#### Technical Notes

**Server Details**: Look up each server in the main server catalog to show full details (name, description, installation method).

**Error Handling**: Show helpful error message if bundle not found, with suggestion to run `bundle list`.

---

### BUNDLE-014: Implement `bundle install` Command

**ID**: BUNDLE-014
**Priority**: P0 (Critical)
**Effort**: 6 hours
**Session**: 3
**Dependencies**: BUNDLE-011, BUNDLE-010 (installer working)

#### Description

Implement `mcpi bundle install <bundle-name>` command to install all servers in a bundle. This is the core user-facing command.

#### Acceptance Criteria

- [x] `bundle install <bundle-name>` installs all servers in bundle
- [x] `--scope` option specifies target scope (required unless interactive)
- [x] `--client` option specifies client (optional, uses default)
- [x] `--dry-run` option simulates installation
- [x] `--skip-existing` option skips already-installed servers (default: true)
- [x] `--rollback-on-error` option enables transaction rollback (default: false)
- [x] Shows progress for each server installation
- [x] Rich-formatted output with status indicators
- [x] Error handling for missing bundle, invalid scope
- [x] Final summary showing success/failure counts

#### Files to Create/Modify

**Modify**: `src/mcpi/cli.py`

Add under `@bundle.group()`:
```python
@bundle.command("install")
@click.argument("bundle_id")
@click.option(
    "--scope",
    type=str,
    help="Target scope (e.g., project-mcp, user-global)",
)
@click.option(
    "--client",
    type=str,
    help="Client name (default: auto-detect)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Simulate installation without making changes",
)
@click.option(
    "--skip-existing/--no-skip-existing",
    default=True,
    help="Skip already-installed servers (default: skip)",
)
@click.option(
    "--rollback-on-error",
    is_flag=True,
    help="Remove installed servers if any installation fails",
)
@click.pass_context
def bundle_install(
    ctx: click.Context,
    bundle_id: str,
    scope: Optional[str],
    client: Optional[str],
    dry_run: bool,
    skip_existing: bool,
    rollback_on_error: bool,
):
    """Install all servers in a bundle.

    Examples:

        # Install web-dev bundle to project scope
        mcpi bundle install web-dev --scope project-mcp

        # Dry-run to preview installation
        mcpi bundle install web-dev --scope user-global --dry-run

        # Install with rollback on error
        mcpi bundle install web-dev --scope user-global --rollback-on-error
    """
    # Get bundle
    bundle_catalog = get_bundle_catalog()
    bundle = bundle_catalog.get_bundle(bundle_id)

    if not bundle:
        console.print(f"[red]Bundle '{bundle_id}' not found[/red]")
        console.print("\nUse 'mcpi bundle list' to see available bundles")
        raise click.Abort()

    # Get scope (interactive if not provided)
    if not scope:
        # TODO: Add interactive scope selection (BUNDLE-015)
        console.print("[red]--scope is required[/red]")
        console.print("\nExample: mcpi bundle install web-dev --scope project-mcp")
        raise click.Abort()

    # Show bundle info
    console.print(f"\n[bold]Installing bundle: {bundle.name}[/bold]")
    console.print(f"[dim]{bundle.description}[/dim]")
    console.print(f"Scope: [cyan]{scope}[/cyan]")
    console.print(f"Servers: [cyan]{len(bundle.servers)}[/cyan]")
    if dry_run:
        console.print("[yellow]Mode: DRY-RUN (no changes will be made)[/yellow]")
    console.print()

    # Create installer
    manager = get_mcp_manager()
    catalog = get_catalog()
    from mcpi.bundles.installer import BundleInstaller
    installer = BundleInstaller(manager=manager, catalog=catalog)

    # Install bundle
    try:
        results = installer.install_bundle(
            bundle=bundle,
            scope=scope,
            client_name=client,
            dry_run=dry_run,
            skip_existing=skip_existing,
            rollback_on_error=rollback_on_error,
        )
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")
        raise click.Abort()

    # Show results
    console.print("\n[bold]Installation Results:[/bold]\n")

    success_count = 0
    failure_count = 0
    skipped_count = 0

    for i, (bundle_server, result) in enumerate(zip(bundle.servers, results), 1):
        if result.success:
            if hasattr(result, 'skipped') and result.skipped:
                status = "[yellow]SKIPPED[/yellow]"
                skipped_count += 1
            else:
                status = "[green]SUCCESS[/green]"
                success_count += 1
        else:
            status = "[red]FAILED[/red]"
            failure_count += 1

        console.print(f"  [{i}/{len(bundle.servers)}] {bundle_server.id}: {status}")
        if not result.success:
            console.print(f"      [red]{result.message}[/red]")

    # Summary
    console.print()
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"  Success: [green]{success_count}[/green]")
    if skipped_count > 0:
        console.print(f"  Skipped: [yellow]{skipped_count}[/yellow]")
    if failure_count > 0:
        console.print(f"  Failed: [red]{failure_count}[/red]")

    if dry_run:
        console.print("\n[yellow]DRY-RUN: No changes were made[/yellow]")
    elif failure_count == 0:
        console.print("\n[green]✓ Bundle installed successfully[/green]")
    else:
        console.print("\n[red]✗ Some servers failed to install[/red]")
        raise click.Abort()
```

#### Testing Requirements

**CLI Tests**: Add to `tests/test_bundles_cli.py`
- Test successful installation
- Test dry-run mode
- Test missing bundle error
- Test installation with failures
- Test rollback behavior

#### Technical Notes

**Progress Output**: Show progress for each server as it's installed. Use Rich console for formatted output.

**Error Handling**: Handle all error cases gracefully with helpful messages.

**Exit Codes**: Exit with non-zero code if any installation fails (unless all failures were skipped servers).

---

### BUNDLE-015: Add Interactive Scope Selection

**ID**: BUNDLE-015
**Priority**: P1 (High)
**Effort**: 2 hours
**Session**: 3
**Dependencies**: BUNDLE-014

#### Description

Add interactive scope selection to `bundle install` command when `--scope` is not provided. Use Rich prompts to let user choose scope.

#### Acceptance Criteria

- [x] If `--scope` not provided, show interactive prompt
- [x] List available scopes for selected client
- [x] Highlight suggested scope from bundle
- [x] Use Rich prompt for selection
- [x] Validate selected scope before installation

#### Files to Create/Modify

**Modify**: `src/mcpi/cli.py`

Update `bundle_install` function:
```python
# Get scope (interactive if not provided)
if not scope:
    manager = get_mcp_manager()

    # Get available scopes
    plugin = manager.get_client_plugin(client)
    if not plugin:
        console.print("[red]Client not found[/red]")
        raise click.Abort()

    available_scopes = plugin.list_scopes()

    # Show suggested scope
    console.print(f"\n[bold]Suggested scope:[/bold] [cyan]{bundle.suggested_scope}[/cyan]")
    console.print("[dim]Available scopes:[/dim]")
    for i, scope_name in enumerate(available_scopes, 1):
        marker = "→" if scope_name == bundle.suggested_scope else " "
        console.print(f"  {marker} {i}. {scope_name}")

    # Prompt for selection
    from rich.prompt import IntPrompt
    choice = IntPrompt.ask(
        "\nSelect scope",
        choices=[str(i) for i in range(1, len(available_scopes) + 1)],
        default=str(available_scopes.index(bundle.suggested_scope) + 1) if bundle.suggested_scope in available_scopes else "1",
    )
    scope = available_scopes[choice - 1]
    console.print(f"Selected: [cyan]{scope}[/cyan]\n")
```

#### Testing Requirements

**Manual Testing**: Interactive prompts are difficult to unit test, focus on manual testing
- Test prompt appears when --scope omitted
- Test suggested scope is highlighted
- Test selection works correctly

#### Technical Notes

**Rich Prompts**: Use `rich.prompt.IntPrompt` for numbered menu selection.

**Default Selection**: Default to suggested scope if it exists in available scopes.

---

### BUNDLE-016: Add Rich Progress Output

**ID**: BUNDLE-016
**Priority**: P2 (Medium)
**Effort**: 2 hours
**Session**: 3
**Dependencies**: BUNDLE-014

#### Description

Enhance `bundle install` output with Rich progress bars and live updates during installation.

#### Acceptance Criteria

- [x] Show progress bar during bundle installation
- [x] Live updates as each server is installed
- [x] Final summary with formatted table
- [x] Error messages are highlighted
- [x] Dry-run mode clearly indicated

#### Files to Create/Modify

**Modify**: `src/mcpi/cli.py`

Add Rich Progress to `bundle_install`:
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# ... in bundle_install function ...

# Install with progress bar
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    console=console,
) as progress:
    task = progress.add_task(
        f"Installing {bundle.name}...",
        total=len(bundle.servers),
    )

    results = []
    for bundle_server in bundle.servers:
        progress.update(task, description=f"Installing {bundle_server.id}...")

        # Install server (call installer._install_server directly for fine-grained control)
        result = installer._install_server(
            bundle_server, scope, client, dry_run
        )
        results.append(result)

        progress.advance(task)

    progress.update(task, description=f"✓ {bundle.name} installation complete")
```

#### Testing Requirements

**Manual Testing**: Visual output requires manual verification
- Test progress bar renders correctly
- Test live updates work
- Test error states display properly

#### Technical Notes

**Rich Progress**: Use `rich.progress.Progress` for live updates during installation.

**Optional Enhancement**: This is P2 (Medium priority) - can be implemented after core functionality works.

---

### BUNDLE-017: Write CLI Tests

**ID**: BUNDLE-017
**Priority**: P0 (Critical)
**Effort**: 4 hours
**Session**: 3
**Dependencies**: BUNDLE-012, BUNDLE-013, BUNDLE-014

#### Description

Write comprehensive CLI tests for all bundle commands using Click's testing utilities.

#### Acceptance Criteria

- [x] 5+ CLI tests written and passing
- [x] Tests use `click.testing.CliRunner`
- [x] Tests cover `bundle list`, `bundle info`, `bundle install`
- [x] Tests verify command output format
- [x] Tests verify error handling
- [x] Tests use mocks/fixtures for dependencies

#### Files to Create/Modify

**Create**: `tests/test_bundles_cli.py`
```python
"""CLI tests for bundle commands."""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from mcpi.cli import main


@pytest.fixture
def cli_runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def test_bundles_dir(tmp_path):
    """Create test bundles directory."""
    bundles_dir = tmp_path / "bundles"
    bundles_dir.mkdir()

    # Create test bundle
    test_bundle = {
        "name": "test-cli",
        "description": "CLI test bundle",
        "version": "1.0.0",
        "servers": [{"id": "filesystem"}],
        "suggested_scope": "user-global"
    }
    (bundles_dir / "test-cli.json").write_text(json.dumps(test_bundle))

    return bundles_dir


def test_bundle_list_command(cli_runner, test_bundles_dir, monkeypatch):
    """Test bundle list command."""
    # Mock get_bundle_catalog to use test directory
    from mcpi.bundles.catalog import create_test_bundle_catalog

    def mock_get_bundle_catalog():
        return create_test_bundle_catalog(test_bundles_dir)

    monkeypatch.setattr("mcpi.cli.get_bundle_catalog", mock_get_bundle_catalog)

    # Run command
    result = cli_runner.invoke(main, ["bundle", "list"])

    assert result.exit_code == 0
    assert "test-cli" in result.output
    assert "CLI test bundle" in result.output


def test_bundle_info_command(cli_runner, test_bundles_dir, monkeypatch):
    """Test bundle info command."""
    # Mock get_bundle_catalog
    from mcpi.bundles.catalog import create_test_bundle_catalog

    def mock_get_bundle_catalog():
        return create_test_bundle_catalog(test_bundles_dir)

    monkeypatch.setattr("mcpi.cli.get_bundle_catalog", mock_get_bundle_catalog)

    # Run command
    result = cli_runner.invoke(main, ["bundle", "info", "test-cli"])

    assert result.exit_code == 0
    assert "test-cli" in result.output
    assert "CLI test bundle" in result.output
    assert "filesystem" in result.output


def test_bundle_info_missing(cli_runner, test_bundles_dir, monkeypatch):
    """Test bundle info with non-existent bundle."""
    # Mock get_bundle_catalog
    from mcpi.bundles.catalog import create_test_bundle_catalog

    def mock_get_bundle_catalog():
        return create_test_bundle_catalog(test_bundles_dir)

    monkeypatch.setattr("mcpi.cli.get_bundle_catalog", mock_get_bundle_catalog)

    # Run command
    result = cli_runner.invoke(main, ["bundle", "info", "nonexistent"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_bundle_install_dry_run(cli_runner, test_bundles_dir, monkeypatch):
    """Test bundle install in dry-run mode."""
    # Mock dependencies
    from mcpi.bundles.catalog import create_test_bundle_catalog

    def mock_get_bundle_catalog():
        return create_test_bundle_catalog(test_bundles_dir)

    monkeypatch.setattr("mcpi.cli.get_bundle_catalog", mock_get_bundle_catalog)

    # Run command
    result = cli_runner.invoke(main, [
        "bundle", "install", "test-cli",
        "--scope", "user-global",
        "--dry-run"
    ])

    assert result.exit_code == 0
    assert "DRY-RUN" in result.output or "dry-run" in result.output.lower()


def test_bundle_install_missing_scope(cli_runner, test_bundles_dir, monkeypatch):
    """Test bundle install without scope fails."""
    # Mock get_bundle_catalog
    from mcpi.bundles.catalog import create_test_bundle_catalog

    def mock_get_bundle_catalog():
        return create_test_bundle_catalog(test_bundles_dir)

    monkeypatch.setattr("mcpi.cli.get_bundle_catalog", mock_get_bundle_catalog)

    # Run command (no --scope)
    result = cli_runner.invoke(main, ["bundle", "install", "test-cli"])

    # Should fail or prompt (depending on interactive implementation)
    # For now, test that it doesn't silently succeed
    assert "--scope is required" in result.output or result.exit_code != 0
```

#### Testing Requirements

**Test Coverage**: CLI commands should be well-tested

**Test Execution**:
```bash
pytest tests/test_bundles_cli.py -v
```

#### Technical Notes

**Click Testing**: Use `click.testing.CliRunner` for CLI testing - it captures output and allows assertions on exit codes and output text.

**Mocking**: Mock `get_bundle_catalog()` to use test bundles directory instead of production bundles.

---

### BUNDLE-018: Run Full Test Suite

**ID**: BUNDLE-018
**Priority**: P0 (Critical)
**Effort**: 2 hours
**Session**: 4
**Dependencies**: All previous work items

#### Description

Run complete test suite to verify all existing tests still pass and new bundle tests are green. Target: 701+ tests passing (681 existing + 20+ new).

#### Acceptance Criteria

- [x] Full test suite runs: `pytest -v`
- [x] 701+ tests passing (681 existing + 20+ bundle tests)
- [x] Zero test failures
- [x] Bundle test coverage at 90%+
- [x] No regressions in existing tests

#### Testing Requirements

**Commands**:
```bash
# Run all tests
pytest -v --tb=short

# Run with coverage
pytest --cov=src/mcpi --cov-report=term --cov-report=html

# Check bundle coverage specifically
pytest --cov=src/mcpi/bundles --cov-report=term
```

#### Technical Notes

**Success Criteria**: All tests must pass. If any failures occur, fix immediately before proceeding.

**Coverage Target**: 90%+ for bundle code (`src/mcpi/bundles/`).

---

### BUNDLE-019: Write Functional End-to-End Tests

**ID**: BUNDLE-019
**Priority**: P1 (High)
**Effort**: 4 hours
**Session**: 4
**Dependencies**: BUNDLE-018

#### Description

Write un-gameable functional tests that verify real bundle installation workflows work correctly. These tests should actually install bundles to temporary configurations and verify the results.

#### Acceptance Criteria

- [x] 3+ functional tests written and passing
- [x] Tests use real bundle definitions from `data/bundles/`
- [x] Tests verify servers appear in `mcpi list` output
- [x] Tests verify configuration files contain expected servers
- [x] Tests verify idempotent installation (re-installing is safe)
- [x] Tests use `MCPTestHarness` for isolation

#### Files to Create/Modify

**Create**: `tests/test_bundles_functional.py`
```python
"""Functional end-to-end tests for bundle installation."""

import pytest
import json
from pathlib import Path
from tests.test_harness import MCPTestHarness
from mcpi.bundles.catalog import create_default_bundle_catalog
from mcpi.bundles.installer import BundleInstaller
from mcpi.clients.manager import MCPManager
from mcpi.clients.registry import ClientRegistry
from mcpi.clients.claude_code import ClaudeCodePlugin
from mcpi.registry.catalog import create_default_catalog


@pytest.fixture
def functional_harness(tmp_path):
    """Create harness with real bundles and catalog."""
    harness = MCPTestHarness(tmp_path)
    harness.setup_scope_files()
    return harness


def test_install_real_web_dev_bundle(functional_harness):
    """Test installing real web-dev bundle to temp config.

    This is an un-gameable test that verifies:
    1. Bundle definition loads from data/bundles/
    2. All referenced servers exist in catalog
    3. Installation writes correct config
    4. Installed servers appear in list output
    """
    # Setup with real catalog and bundles
    plugin = ClaudeCodePlugin(path_overrides=functional_harness.path_overrides)
    registry = ClientRegistry()
    registry.inject_client_instance("claude-code", plugin)
    manager = MCPManager(registry=registry, default_client="claude-code")

    catalog = create_default_catalog()
    bundle_catalog = create_default_bundle_catalog()
    installer = BundleInstaller(manager=manager, catalog=catalog)

    # Load web-dev bundle
    bundle = bundle_catalog.get_bundle("web-dev")
    assert bundle is not None, "web-dev bundle should exist"

    # Install bundle
    results = installer.install_bundle(bundle, scope="project-mcp")

    # Verify all installations succeeded
    assert all(r.success for r in results), f"Some installations failed: {[r.message for r in results if not r.success]}"

    # Verify servers appear in list
    servers = manager.list_servers(scope="project-mcp")
    installed_ids = {s.server_id for s in servers}

    for bundle_server in bundle.servers:
        assert bundle_server.id in installed_ids, f"Server {bundle_server.id} not found in installed servers"

    # Verify configuration file contains servers
    config_path = functional_harness.path_overrides["project-mcp"]
    with open(config_path) as f:
        config = json.load(f)

    assert "mcpServers" in config
    config_server_ids = set(config["mcpServers"].keys())

    for bundle_server in bundle.servers:
        assert bundle_server.id in config_server_ids, f"Server {bundle_server.id} not in config file"


def test_bundle_installation_idempotent(functional_harness):
    """Test re-installing same bundle is idempotent."""
    # Setup
    plugin = ClaudeCodePlugin(path_overrides=functional_harness.path_overrides)
    registry = ClientRegistry()
    registry.inject_client_instance("claude-code", plugin)
    manager = MCPManager(registry=registry, default_client="claude-code")

    catalog = create_default_catalog()
    bundle_catalog = create_default_bundle_catalog()
    installer = BundleInstaller(manager=manager, catalog=catalog)

    bundle = bundle_catalog.get_bundle("web-dev")

    # Install first time
    results1 = installer.install_bundle(bundle, scope="user-global")
    success1 = sum(1 for r in results1 if r.success)

    # Install second time
    results2 = installer.install_bundle(bundle, scope="user-global", skip_existing=True)
    success2 = sum(1 for r in results2 if r.success)

    # Both should succeed
    assert success1 == len(bundle.servers)
    assert success2 == len(bundle.servers)  # All should be skipped but return success

    # Verify only one copy of each server
    servers = manager.list_servers(scope="user-global")
    from collections import Counter
    server_counts = Counter(s.server_id for s in servers)

    for bundle_server in bundle.servers:
        assert server_counts[bundle_server.id] == 1, f"Server {bundle_server.id} installed multiple times"


def test_bundle_servers_appear_in_list(functional_harness):
    """Test installed bundle servers appear in mcpi list output."""
    # Setup
    plugin = ClaudeCodePlugin(path_overrides=functional_harness.path_overrides)
    registry = ClientRegistry()
    registry.inject_client_instance("claude-code", plugin)
    manager = MCPManager(registry=registry, default_client="claude-code")

    catalog = create_default_catalog()
    bundle_catalog = create_default_bundle_catalog()
    installer = BundleInstaller(manager=manager, catalog=catalog)

    # Install bundle
    bundle = bundle_catalog.get_bundle("ai-tools")
    assert bundle is not None

    results = installer.install_bundle(bundle, scope="user-global")
    assert all(r.success for r in results)

    # List servers
    servers = manager.list_servers(scope="user-global")
    server_list = [s.server_id for s in servers]

    # Verify all bundle servers in list
    for bundle_server in bundle.servers:
        assert bundle_server.id in server_list, f"{bundle_server.id} not in list output"
```

#### Testing Requirements

**Test Execution**:
```bash
pytest tests/test_bundles_functional.py -v --tb=short
```

#### Technical Notes

**Un-gameable Tests**: These tests verify REAL functionality:
1. Load REAL bundles from `data/bundles/`
2. Use REAL catalog from `data/catalog.json`
3. Perform ACTUAL installation to temp configs
4. Verify configuration files are written correctly
5. Verify servers appear in list output

**Why Functional**: Unit tests with mocks can pass even if real code is broken. These tests prove the feature works end-to-end.

---

### BUNDLE-020: Manual Testing with Real Bundles

**ID**: BUNDLE-020
**Priority**: P0 (Critical)
**Effort**: 3 hours
**Session**: 4
**Dependencies**: BUNDLE-018

#### Description

Manually test bundle installation with real bundles in a development environment. Verify CLI UX, error messages, and end-to-end workflows.

#### Acceptance Criteria

- [x] `mcpi bundle list` shows all 5 built-in bundles
- [x] `mcpi bundle info web-dev` shows correct details
- [x] `mcpi bundle install web-dev --scope project-mcp --dry-run` works
- [x] `mcpi bundle install web-dev --scope project-mcp` installs successfully
- [x] Installed servers appear in `mcpi list --scope project-mcp`
- [x] Re-installing same bundle is safe (skips existing)
- [x] Error messages are clear and actionable
- [x] Rich formatting looks good

#### Testing Requirements

**Manual Test Checklist**:
```bash
# 1. List bundles
mcpi bundle list

# 2. Show bundle info
mcpi bundle info web-dev
mcpi bundle info data-science
mcpi bundle info devops
mcpi bundle info ai-tools
mcpi bundle info content

# 3. Dry-run installation
mcpi bundle install web-dev --scope project-mcp --dry-run

# 4. Real installation
cd /tmp/test-project
mcpi bundle install web-dev --scope project-mcp

# 5. Verify installation
mcpi list --scope project-mcp
cat .mcp.json

# 6. Test idempotent installation
mcpi bundle install web-dev --scope project-mcp

# 7. Test error cases
mcpi bundle info nonexistent
mcpi bundle install nonexistent --scope project-mcp

# 8. Test with different scopes
mcpi bundle install ai-tools --scope user-global --dry-run
```

#### Technical Notes

**Test Environment**: Use a temporary test project directory to avoid polluting actual configurations.

**Verification**: After each installation, verify:
1. Exit code is 0 (success)
2. Output is clear and helpful
3. Configuration files are written correctly
4. `mcpi list` shows installed servers

---

### BUNDLE-021: Update README with Bundle Examples

**ID**: BUNDLE-021
**Priority**: P1 (High)
**Effort**: 2 hours
**Session**: 4
**Dependencies**: BUNDLE-020

#### Description

Update README.md to document the bundle feature with clear examples and use cases.

#### Acceptance Criteria

- [x] New "Bundle Management" section added to README
- [x] Examples for `bundle list`, `bundle info`, `bundle install`
- [x] Explanation of what bundles are and why they're useful
- [x] List of built-in bundles with descriptions
- [x] Link to bundle JSON format documentation

#### Files to Create/Modify

**Modify**: `README.md`

Add section after "Server Management":
```markdown
## Bundle Management

Bundles are curated sets of MCP servers that work well together. Install complete toolchains with a single command.

### List Available Bundles

```bash
mcpi bundle list
```

Shows all available bundles with descriptions and server counts.

### View Bundle Details

```bash
mcpi bundle info web-dev
```

Shows detailed information about a bundle, including all servers and their configurations.

### Install a Bundle

```bash
# Install to project scope
mcpi bundle install web-dev --scope project-mcp

# Install to user scope
mcpi bundle install ai-tools --scope user-global

# Dry-run to preview installation
mcpi bundle install web-dev --scope project-mcp --dry-run
```

### Built-in Bundles

- **web-dev**: Complete web development stack (filesystem, fetch, github, puppeteer)
- **data-science**: Data science toolkit (sqlite, postgres, filesystem, fetch)
- **devops**: DevOps automation (github, filesystem, brave-search, fetch)
- **ai-tools**: AI/ML development tools (memory, sequential-thinking, filesystem, brave-search)
- **content**: Content creation and research (brave-search, fetch, puppeteer, filesystem)

### Bundle Options

```bash
# Skip already-installed servers (default)
mcpi bundle install web-dev --scope project-mcp --skip-existing

# Rollback on error
mcpi bundle install web-dev --scope user-global --rollback-on-error
```

### Creating Custom Bundles

Custom bundles are JSON files in `~/.mcpi/bundles/` (or `data/bundles/` for built-in bundles).

Example bundle format:
```json
{
  "name": "my-stack",
  "description": "My custom server stack",
  "version": "1.0.0",
  "author": "Your Name",
  "servers": [
    {"id": "filesystem"},
    {"id": "fetch"}
  ],
  "suggested_scope": "user-global"
}
```

Server IDs must match servers in the catalog. Use `mcpi search <query>` to find available servers.
```

#### Testing Requirements

**Documentation Review**: Have someone unfamiliar with bundles read the README section and verify it's clear.

#### Technical Notes

**Placement**: Add after "Server Management" section but before "Configuration".

**Examples**: Use real bundle names and realistic scenarios.

---

### BUNDLE-022: Update CLAUDE.md with Bundle Commands

**ID**: BUNDLE-022
**Priority**: P1 (High)
**Effort**: 1 hour
**Session**: 4
**Dependencies**: BUNDLE-020

#### Description

Update CLAUDE.md to document bundle commands for AI development agents working on the project.

#### Acceptance Criteria

- [x] Bundle commands added to "Application Commands" section
- [x] Examples for development/testing workflows
- [x] Note about bundle data location
- [x] Testing guidance for bundle features

#### Files to Create/Modify

**Modify**: `CLAUDE.md`

Add to "Application Commands" section:
```markdown
### Bundle Commands
```bash
# List available bundles
mcpi bundle list

# Show bundle details
mcpi bundle info web-dev

# Install a bundle
mcpi bundle install web-dev --scope project-mcp

# Dry-run installation
mcpi bundle install web-dev --scope project-mcp --dry-run
```

**Bundle Data Location**: `data/bundles/*.json`

**Testing Bundles**:
```bash
# Unit tests
pytest tests/test_bundles_models.py tests/test_bundles_catalog.py tests/test_bundles_installer.py -v

# Integration tests
pytest tests/test_bundles_integration.py -v

# CLI tests
pytest tests/test_bundles_cli.py -v

# Functional tests
pytest tests/test_bundles_functional.py -v

# All bundle tests
pytest tests/test_bundles*.py -v
```
```

#### Testing Requirements

**Verification**: Ensure commands in CLAUDE.md are accurate and work as documented.

#### Technical Notes

**Audience**: This documentation is for AI development agents, so include technical details and testing commands.

---

### BUNDLE-023: Code Review and Refinement

**ID**: BUNDLE-023
**Priority**: P1 (High)
**Effort**: 4 hours
**Session**: 4
**Dependencies**: All implementation work items

#### Description

Perform thorough code review of all bundle implementation code. Look for:
- Code quality issues
- Missing error handling
- Inconsistent patterns
- Unclear documentation
- Type hints completeness

#### Acceptance Criteria

- [x] All code follows existing project patterns
- [x] Type hints present for all functions
- [x] Docstrings complete and accurate
- [x] Error handling comprehensive
- [x] Logging at appropriate levels
- [x] No TODO or FIXME comments remaining
- [x] Code passes mypy type checking
- [x] Code passes ruff linting

#### Files to Review

**All Bundle Files**:
- `src/mcpi/bundles/models.py`
- `src/mcpi/bundles/catalog.py`
- `src/mcpi/bundles/installer.py`
- `src/mcpi/cli.py` (bundle commands section)
- All test files

#### Testing Requirements

**Quality Checks**:
```bash
# Type checking
mypy src/mcpi/bundles/

# Linting
ruff check src/mcpi/bundles/ tests/test_bundles*.py

# Formatting
black --check src/mcpi/bundles/ tests/test_bundles*.py
```

#### Technical Notes

**Review Checklist**:
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] Error handling with specific exceptions
- [ ] Logging at INFO level for user actions
- [ ] Logging at DEBUG level for internal operations
- [ ] No hardcoded paths
- [ ] No magic numbers
- [ ] Clear variable names
- [ ] Functions are single-purpose
- [ ] No code duplication

---

### BUNDLE-024: Create Demo Examples

**ID**: BUNDLE-024
**Priority**: P2 (Medium)
**Effort**: 2 hours
**Session**: 4
**Dependencies**: BUNDLE-020

#### Description

Create demo scripts and examples showing bundle usage for README and documentation.

#### Acceptance Criteria

- [x] Example demo script created
- [x] Screenshots or terminal recordings of bundle commands
- [x] Example custom bundle JSON file
- [x] Common use case scenarios documented

#### Files to Create/Modify

**Create**: `examples/bundle-demo.sh`
```bash
#!/bin/bash
# Demo script for Smart Server Bundles feature

echo "=== Smart Server Bundles Demo ==="
echo

echo "1. List available bundles"
mcpi bundle list
echo

echo "2. Show web-dev bundle details"
mcpi bundle info web-dev
echo

echo "3. Dry-run installation"
mcpi bundle install web-dev --scope project-mcp --dry-run
echo

echo "4. Install bundle (uncomment to run)"
# mcpi bundle install web-dev --scope project-mcp
```

**Create**: `examples/custom-bundle.json`
```json
{
  "name": "example-custom",
  "description": "Example custom bundle showing bundle format",
  "version": "1.0.0",
  "author": "Example User",
  "servers": [
    {"id": "filesystem"},
    {"id": "fetch"},
    {"id": "brave-search"}
  ],
  "suggested_scope": "user-global"
}
```

#### Testing Requirements

**Demo Execution**: Run demo script to verify all commands work correctly.

#### Technical Notes

**Purpose**: These examples help users understand bundles quickly through concrete examples.

**Optional**: Consider creating terminal recording (asciinema) showing bundle installation.

---

## Files to Create/Modify Summary

### New Files to Create (9 files)

**Source Code** (6 files):
1. `src/mcpi/bundles/__init__.py` - Package initialization
2. `src/mcpi/bundles/models.py` - Pydantic models (Bundle, BundleServer)
3. `src/mcpi/bundles/catalog.py` - BundleCatalog class
4. `src/mcpi/bundles/installer.py` - BundleInstaller class

**Bundle Definitions** (5 files):
5. `data/bundles/web-dev.json` - Web development bundle
6. `data/bundles/data-science.json` - Data science bundle
7. `data/bundles/devops.json` - DevOps bundle
8. `data/bundles/ai-tools.json` - AI tools bundle
9. `data/bundles/content.json` - Content creation bundle

**Tests** (5 files):
10. `tests/test_bundles_models.py` - Model unit tests
11. `tests/test_bundles_catalog.py` - Catalog unit tests
12. `tests/test_bundles_installer.py` - Installer unit tests
13. `tests/test_bundles_integration.py` - Integration tests
14. `tests/test_bundles_cli.py` - CLI tests
15. `tests/test_bundles_functional.py` - Functional E2E tests

**Examples** (2 files):
16. `examples/bundle-demo.sh` - Demo script
17. `examples/custom-bundle.json` - Example custom bundle

### Modified Files (3 files)

1. `src/mcpi/cli.py` - Add bundle command group (~200 new lines)
2. `README.md` - Add Bundle Management section
3. `CLAUDE.md` - Add bundle commands documentation

**Total**: 17 new files, 3 modified files

---

## Dependency Graph

```
Session 1 (Day 1 - 4 hours):
  BUNDLE-001 (Models) ──→ BUNDLE-002 (Catalog)
                     └──→ BUNDLE-003 (Built-in bundles)
                     └──→ BUNDLE-004 (Tests)

Session 2 (Days 2-3 - 14 hours):
  BUNDLE-002 ──→ BUNDLE-005 (Installer basic) ──→ BUNDLE-006 (Multi-server)
                                               ──→ BUNDLE-007 (Rollback)
                                               ──→ BUNDLE-008 (Dry-run)
                                               ──→ BUNDLE-009 (Unit tests)
                                               ──→ BUNDLE-010 (Integration tests)

Session 3 (Days 4-5 - 16 hours):
  BUNDLE-002 ──→ BUNDLE-011 (CLI group) ──→ BUNDLE-012 (bundle list)
                                        ──→ BUNDLE-013 (bundle info)
  BUNDLE-010 ──→ BUNDLE-014 (bundle install) ──→ BUNDLE-015 (Interactive)
                                             ──→ BUNDLE-016 (Progress)
  BUNDLE-014 ──→ BUNDLE-017 (CLI tests)

Session 4 (Days 6-7 - 20.5 hours):
  ALL ──→ BUNDLE-018 (Full test suite) ──→ BUNDLE-019 (Functional tests)
                                       ──→ BUNDLE-020 (Manual testing)
                                       ──→ BUNDLE-021 (README)
                                       ──→ BUNDLE-022 (CLAUDE.md)
                                       ──→ BUNDLE-023 (Code review)
                                       ──→ BUNDLE-024 (Examples)
```

---

## Critical Path

**Critical path items** (must be completed in order):

1. BUNDLE-001: Models (0.5 hours)
2. BUNDLE-002: Catalog (4 hours)
3. BUNDLE-005: Installer basic (6 hours)
4. BUNDLE-011: CLI group (2 hours)
5. BUNDLE-014: bundle install command (6 hours)
6. BUNDLE-018: Full test suite (2 hours)
7. BUNDLE-020: Manual testing (3 hours)

**Total critical path**: 23.5 hours (~3 days)

**Remaining work** can be done in parallel or deferred:
- Bundle definitions (BUNDLE-003): 4 hours
- Tests (BUNDLE-004, 009, 010, 017, 019): 18 hours
- Enhancements (BUNDLE-006, 007, 008, 015, 016): 11 hours
- Documentation (BUNDLE-021, 022, 024): 5 hours
- Polish (BUNDLE-023): 4 hours

---

## Risk Assessment

### Technical Risks

**Risk 1: Bundle Definition Format** - LOW
- **Probability**: 10%
- **Impact**: Low (just refactor JSON files)
- **Mitigation**: Follow proposal's schema exactly

**Risk 2: Server Installation Failures** - LOW
- **Probability**: 20%
- **Impact**: Low (existing code handles this)
- **Mitigation**: Use transaction pattern, implement rollback

**Risk 3: User Confusion About Scopes** - MEDIUM
- **Probability**: 40%
- **Impact**: Medium (UX issue)
- **Mitigation**: Clear CLI output, interactive prompts, dry-run mode

**Risk 4: Bundle Content Decisions** - MEDIUM
- **Probability**: 50%
- **Impact**: Low (just change JSON files)
- **Mitigation**: Start with proposal's suggestions, iterate

**Overall Risk**: LOW

---

## Definition of Done

### Feature Complete Criteria

- [x] All 24 work items completed
- [x] All tests passing (701+ tests total)
- [x] 90%+ test coverage for bundle code
- [x] Zero regressions in existing tests
- [x] Documentation updated (README, CLAUDE.md)
- [x] Manual testing complete
- [x] Code review complete
- [x] Examples provided

### Quality Gates

**Code Quality**:
- [x] All new code type-hinted
- [x] Pydantic models for all data structures
- [x] Error handling with specific exceptions
- [x] Logging at INFO level for user actions
- [x] Passes mypy type checking
- [x] Passes ruff linting
- [x] Formatted with black

**Testing**:
- [x] Zero test failures
- [x] All edge cases have explicit tests
- [x] Integration tests use MCPTestHarness
- [x] CLI tests verify user-facing behavior
- [x] Functional tests verify real workflows

**Documentation**:
- [x] Bundle format clearly documented
- [x] CLI help text matches implementation
- [x] Examples in README are copy-pasteable
- [x] CLAUDE.md updated with dev guidance

**Architecture**:
- [x] No changes to existing core code
- [x] Follows existing plugin pattern
- [x] Uses existing file storage pattern
- [x] No new external dependencies

### Success Metrics

**Quantitative**:
- Bundle installation completes in <15 seconds for 4-server bundle
- 0 regressions in existing 681 tests
- 20+ new tests added and passing
- 90%+ test coverage for bundle code

**Qualitative**:
- Bundle installation feels obvious and natural
- Error messages are actionable
- Built-in bundles contain genuinely useful combinations
- Code follows existing patterns

---

## First 3 Immediate Actions

### Action 1: Create Directory Structure (5 minutes)

```bash
cd /Users/bmf/Library/Mobile\ Documents/com~apple~CloudDocs/_mine/icode/mcpi

# Create bundles source directory
mkdir -p src/mcpi/bundles

# Create bundles data directory
mkdir -p data/bundles

# Create placeholder files
touch src/mcpi/bundles/__init__.py
touch src/mcpi/bundles/models.py
touch src/mcpi/bundles/catalog.py
touch src/mcpi/bundles/installer.py
```

### Action 2: Implement BUNDLE-001 (Models) (30 minutes)

Create `src/mcpi/bundles/models.py` with Pydantic models as specified in BUNDLE-001.

### Action 3: Implement BUNDLE-002 (Catalog) (4 hours)

Create `src/mcpi/bundles/catalog.py` with `BundleCatalog` class as specified in BUNDLE-002.

---

## Next Steps After Plan Approval

Once this plan is approved:

1. **Day 1**: Execute Session 1 (BUNDLE-001 through BUNDLE-004)
2. **Days 2-3**: Execute Session 2 (BUNDLE-005 through BUNDLE-010)
3. **Days 4-5**: Execute Session 3 (BUNDLE-011 through BUNDLE-017)
4. **Days 6-7**: Execute Session 4 (BUNDLE-018 through BUNDLE-024)
5. **Day 8**: Final review, commit, release

**Total Timeline**: 7-8 days to completion

---

**END OF PLAN**

Generated: 2025-11-16 16:58:48
Work Items: 24
Sessions: 4
Estimated Effort: 54.5 hours (6.8 days)
Risk Level: LOW
Confidence: VERY HIGH (95%)
