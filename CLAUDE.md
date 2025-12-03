# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup

**For iCloud Drive users** (this repo): Use `.venv.nosync` to avoid intermittent import issues:
```bash
python -m venv .venv.nosync
source .venv/bin/activate  # .venv is symlinked to .venv.nosync
pip install -e .
```

**Standard setup**:
```bash
uv sync --dev
source .venv/bin/activate
```

### Testing
```bash
pytest                                    # Run all tests
pytest -v --tb=short                     # Verbose with short traceback
pytest tests/test_catalog.py             # Single file
pytest tests/test_cli_scope_features.py::TestDynamicScopeType  # Single class
pytest --cov=src/mcpi                    # With coverage
```

### Code Quality
```bash
black src/ tests/ && ruff check src/ tests/ --fix && mypy src/
```

**After formatting**: Always run `pytest --tb=no -q` - Black may remove pytest fixture imports that appear unused.

### CLI
```bash
mcpi --help           # Installed CLI
python -m mcpi.cli    # Direct module
```

## Project Architecture

MCPI manages MCP server configurations across clients (Claude Code, Cursor, VS Code) using a **plugin-based architecture** with **scope-based configuration**.

### Core Modules

```
src/mcpi/
├── cli.py                    # Click-based CLI with lazy initialization
├── clients/                  # MCP client plugins
│   ├── base.py              # Abstract MCPClientPlugin, ScopeHandler protocols
│   ├── claude_code.py       # Claude Code plugin (6 scopes)
│   ├── manager.py           # MCPManager orchestrates all clients
│   ├── registry.py          # ClientRegistry for plugin discovery
│   ├── file_based.py        # FileBasedScope implementations
│   ├── types.py             # ServerInfo, ServerConfig, OperationResult
│   └── file_move_enable_disable_handler.py  # User-global disable mechanism
├── registry/                 # Server catalog system
│   ├── catalog.py           # ServerCatalog, MCPServer models
│   ├── catalog_manager.py   # Multi-catalog management (official + local)
│   └── cue_validator.py     # CUE schema validation
├── templates/               # Configuration templates
│   ├── models.py            # PromptDefinition, ServerTemplate
│   ├── template_manager.py  # Template loading with lazy init
│   └── prompt_handler.py    # Rich-based interactive prompts
├── tui/                     # Interactive interfaces
│   └── adapters/fzf.py      # fzf-based server browser
├── bundles/                 # Server bundles (grouped installs)
└── installer/               # Installation methods (npm, pip, git)
```

### Key Concepts

**Scopes**: Hierarchical configuration levels with priority. Lower numbers override higher:
- Project scopes (10-30): `.mcp.json`, `.claude/settings.local.json`, `.claude/settings.json`
- User scopes (40-60): `~/.claude/settings.json`, `~/.config/claude/settings.json`

**Catalogs**: `official` (read-only, `data/catalog.json`) and `local` (read-write, `~/.mcpi/catalogs/local/`)

**Templates**: YAML files in `data/templates/<server-id>/` providing guided setup with prompts

### Key Design Patterns

**Dependency Injection**: Components accept dependencies via constructor, with factory functions for defaults:
```python
# Production
from mcpi.registry.catalog_manager import create_default_catalog_manager
from mcpi.clients.manager import create_default_manager

# Testing
from mcpi.registry.catalog_manager import create_test_catalog_manager
manager = create_test_catalog_manager(official_path, local_path)
```

**Test Harness**: Use `MCPTestHarness` for integration tests involving file operations:
```python
from tests.test_harness import MCPTestHarness
harness = MCPTestHarness(tmp_path)
harness.setup_scope_files()
```

### Terminology

- **Server Catalog** (`data/catalog.json`): Available MCP server definitions
- **Client Registry** (`ClientRegistry`): Plugin system for MCP clients (different concept)

## User-Global Disable Mechanism

Claude Code has no built-in disable for user-global servers. MCPI implements this via shadow file:
- Active: `~/.config/claude/settings.json`
- Disabled: `~/.claude/disabled-mcp.json`

`mcpi disable` moves config from active to shadow; `mcpi enable` reverses it.

## CI/CD

GitHub Actions runs on push/PR to main branches:
- **Tests**: pytest across Python 3.12/3.13 on Linux/macOS/Windows
- **Quality**: Black (blocking), ruff + mypy (warnings only)

Run locally before pushing:
```bash
black --check src/ tests/ && pytest -v --tb=short
```
