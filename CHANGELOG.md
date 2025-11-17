# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2025-11-17

### Added
- **Multi-Catalog Support**: Manage MCP servers across multiple catalogs
  - Two catalogs: `official` (built-in) and `local` (user-created)
  - Local catalog auto-created at `~/.mcpi/catalogs/local/`
- **New Commands**:
  - `mcpi catalog list` - Show all available catalogs
  - `mcpi catalog info <name>` - Display catalog details
- **New Flags**:
  - `--catalog <name>` - Search/use specific catalog (search, info, add commands)
- **CatalogManager API**: New `catalog_manager.py` module for programmatic access

### Changed
- **Breaking**: `mcpi search` now requires `--query` or `-q` flag (was positional argument)
  - Old: `mcpi search filesystem`
  - New: `mcpi search --query filesystem`
  - Reason: Improves compatibility with multi-catalog features

### Deprecated
- `create_default_catalog()` - Use `create_default_catalog_manager()` instead
  - Still works with deprecation warning
  - Will be removed in v1.0.0

### Migration Guide: v0.3.0 → v0.4.0

**No action required** - 100% backward compatible except for search command syntax.

If you use `mcpi search <term>`, change to `mcpi search --query <term>`:
```bash
# Old (v0.3.0)
mcpi search filesystem

# New (v0.4.0)
mcpi search --query filesystem
# or
mcpi search -q filesystem
```

All other commands work unchanged.

## [0.3.0] - 2025-11-16

### Added
- Factory functions for `ServerCatalog` and `MCPManager` to simplify API usage
  - `create_default_catalog()` - Creates catalog with default registry path
  - `create_test_catalog(path)` - Creates catalog with custom path for testing
  - `create_default_manager()` - Creates manager with auto-detected clients
  - `create_test_manager(registry)` - Creates manager with custom registry for testing
- Comprehensive DIP compliance test suite (26 new tests)
- Python API documentation in README.md
- Migration guide for v2.0 breaking changes

### Changed
- **BREAKING**: `ServerCatalog` constructor now requires `registry_path` parameter
  - Migration: Use `create_default_catalog()` instead of `ServerCatalog()`
- **BREAKING**: `MCPManager` constructor now requires `registry` parameter
  - Migration: Use `create_default_manager()` instead of `MCPManager()`
- Improved dependency injection for better testability and SOLID compliance
- All production code updated to use factory pattern

### Technical
- Implemented Dependency Inversion Principle (Phase 1)
  - Eliminates hidden dependencies and hardcoded paths
  - Enables true unit testing without file system access
  - Improves component isolation and modularity
- Test suite maintained at 85% pass rate (583/682 tests)
- Zero regressions from architectural changes

### Migration Guide: v0.2.0 → v0.3.0

If you were using MCPI as a Python library, update your code:

```python
# OLD (v0.2.0) - No longer works in v0.3.0:
from mcpi.registry.catalog import ServerCatalog
from mcpi.clients.manager import MCPManager
catalog = ServerCatalog()
manager = MCPManager()

# NEW (v0.3.0) - Use factory functions:
from mcpi.registry.catalog import create_default_catalog
from mcpi.clients.manager import create_default_manager
catalog = create_default_catalog()
manager = create_default_manager()

# NEW (v0.3.0) - Or pass required parameters explicitly:
from mcpi.registry.catalog import ServerCatalog
from mcpi.clients.manager import MCPManager
from mcpi.clients.registry import ClientRegistry
from pathlib import Path

catalog = ServerCatalog(registry_path=Path("custom/registry.json"))
manager = MCPManager(registry=ClientRegistry())
```

**CLI users**: No changes required - all commands work the same way.

## [1.0.0] - Previous Release

### Added
- Initial release with comprehensive MCP server management
- CLI interface with 13 commands
- Interactive TUI with fzf integration
- Multi-client support (Claude Code, Cursor, VS Code)
- Scope-based configuration management
- Server registry with 18+ servers
- Shell tab completion
- Plugin architecture for extensibility

[Unreleased]: https://github.com/user/mcpi/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/user/mcpi/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/user/mcpi/compare/v1.0.0...v0.3.0
[1.0.0]: https://github.com/user/mcpi/releases/tag/v1.0.0
