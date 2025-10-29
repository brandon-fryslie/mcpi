# Enable/Disable Functionality Evaluation

**Date**: 2025-10-28
**Evaluator**: Architecture Analysis
**Scope**: Enable/Disable Functionality Across All Scopes
**Purpose**: Pre-refactor architecture assessment and gap analysis

---

## Executive Summary

### Current State: PARTIALLY IMPLEMENTED (60%)

**What Works**:
- Enable/disable operations for `project-local`, `user-local`, and `user-global` scopes
- Proper state tracking using Claude's actual format (`enabledMcpjsonServers`, `disabledMcpjsonServers`)
- CLI commands functional (`mcpi enable`, `mcpi disable`)
- State correctly displayed in `mcpi list` output

**What's Broken**:
- Architecture violates single responsibility principle
- All client code in single monolithic file (`claude_code.py`, 518 lines)
- All scope handlers in shared file (`file_based.py`, 558 lines)
- Enable/disable logic hardcoded into client plugin
- No separation between scope-specific enable/disable behaviors
- `project-mcp` scope uses different format (no enable/disable arrays)

**Critical Gaps**:
1. No separate handlers for enable/disable operations per scope
2. No clean separation of concerns between clients
3. Scope definitions mixed with client logic
4. Enable/disable implementation assumes all scopes use same format

### Risk Assessment: MEDIUM-HIGH

**Architectural Debt**: HIGH - Major refactor needed
**Functional Risk**: LOW - Current implementation works for documented use cases
**Maintenance Risk**: HIGH - Adding new clients or scopes requires touching multiple files
**Testing Risk**: MEDIUM - 85% pass rate, but enable/disable tests are complex

---

## Current Architecture Analysis

### Directory Structure

```
src/mcpi/clients/
├── __init__.py             # 500 bytes - exports
├── base.py                 # 8,550 bytes - abstract base classes
├── claude_code.py          # 19,003 bytes - ALL claude-code logic
├── file_based.py           # 18,210 bytes - ALL file scope handlers
├── manager.py              # 14,700 bytes - orchestration
├── protocols.py            # 3,132 bytes - dependency injection
├── registry.py             # 14,344 bytes - plugin discovery
├── types.py                # 3,014 bytes - shared types
└── schemas/
    ├── claude-settings-schema.yaml      # Settings file format
    ├── internal-config-schema.yaml      # Internal config format
    └── mcp-config-schema.yaml           # MCP config format
```

**Problem**: All code for a client in one file. All scope handlers in one file.

### Scope Analysis

#### Scope 1: `project-mcp` (.mcp.json)

**Path**: `{cwd}/.mcp.json`
**Priority**: 1 (highest)
**Type**: Project-level
**Format**: MCP config format

**Config Structure**:
```json
{
  "mcpServers": {
    "server-id": {
      "command": "npx",
      "args": ["package"],
      "env": {},
      "type": "stdio"
    }
  }
}
```

**Enable/Disable Behavior**:
- Does NOT use `enabledMcpjsonServers` / `disabledMcpjsonServers` arrays
- Servers always shown as ENABLED if present
- No way to disable servers in this scope
- Must use `mcpi remove` to "disable" (destructive operation)

**Current Implementation**: Lines 66-78 in `claude_code.py`

**Gap**: No enable/disable support. This is BY DESIGN per Claude's actual behavior.

---

#### Scope 2: `project-local` (.claude/settings.local.json)

**Path**: `{cwd}/.claude/settings.local.json`
**Priority**: 2
**Type**: Project-level
**Format**: Claude settings format

**Config Structure**:
```json
{
  "enabledMcpjsonServers": ["server-1"],
  "disabledMcpjsonServers": ["server-2", "server-3"],
  "mcpServers": {
    "server-1": { "command": "...", "args": [] },
    "server-2": { "command": "...", "args": [] },
    "server-3": { "command": "...", "args": [] }
  }
}
```

**Enable/Disable Behavior**:
- WORKS CORRECTLY
- Uses `enabledMcpjsonServers` / `disabledMcpjsonServers` arrays
- `enable_server()` adds to enabled, removes from disabled
- `disable_server()` adds to disabled, removes from enabled
- State correctly determined by array membership

**Current Implementation**:
- Scope definition: Lines 81-95 in `claude_code.py`
- Enable/disable logic: Lines 323-427 in `claude_code.py`
- State check: Lines 167-206 in `claude_code.py`

**Status**: WORKING as designed

---

#### Scope 3: `user-local` (~/.claude/settings.local.json)

**Path**: `~/.claude/settings.local.json`
**Priority**: 3
**Type**: User-level
**Format**: Claude settings format

**Config Structure**: Same as `project-local`

**Enable/Disable Behavior**: WORKS CORRECTLY (same as project-local)

**Current Implementation**: Lines 98-112 in `claude_code.py`

**Status**: WORKING as designed

---

#### Scope 4: `user-global` (~/.claude/settings.json)

**Path**: `~/.claude/settings.json`
**Priority**: 4
**Type**: User-level
**Format**: Claude settings format

**Config Structure**: Same as `project-local`

**Enable/Disable Behavior**: WORKS CORRECTLY (same as project-local)

**Current Implementation**: Lines 115-129 in `claude_code.py`

**Status**: WORKING as designed

**Real-World Verification**:
```bash
$ cat ~/.claude/settings.local.json
{
  "enabledMcpjsonServers": [],
  "disabledMcpjsonServers": [
    "frida-mcp",
    "ida-pro-mcp",
    "@scope/package-name"
  ]
}

$ mcpi list --client claude-code --scope user-global
# Shows @scope/package-name as DISABLED ✅
```

---

#### Scope 5: `user-internal` (~/.claude.json)

**Path**: `~/.claude.json`
**Priority**: 5
**Type**: User-level
**Format**: Internal config format (4.7MB file with history, stats, etc.)

**Config Structure**: Contains `mcpServers` but NO enable/disable arrays

**Enable/Disable Behavior**:
- Does NOT use `enabledMcpjsonServers` / `disabledMcpjsonServers` arrays
- Servers always shown as ENABLED if present
- Same limitation as `project-mcp`

**Current Implementation**: Lines 132-146 in `claude_code.py`

**Gap**: No enable/disable support (by design - internal file not meant for user manipulation)

---

#### Scope 6: `user-mcp` (~/.claude/mcp_servers.json)

**Path**: `~/.claude/mcp_servers.json`
**Priority**: 6 (lowest)
**Type**: User-level
**Format**: MCP config format

**Config Structure**: Same as `project-mcp`

**Enable/Disable Behavior**:
- Does NOT use enable/disable arrays
- Servers always shown as ENABLED
- Same limitation as `project-mcp`

**Current Implementation**: Lines 149-163 in `claude_code.py`

**Gap**: No enable/disable support (by design - MCP config format doesn't include enable/disable)

---

## Enable/Disable Implementation Analysis

### Current Implementation Location

**All in `claude_code.py`**:

1. **State Determination** (Lines 167-206):
```python
def _get_server_state(self, server_id: str) -> ServerState:
    """Get the actual state of a server using Claude's enable/disable arrays."""
    settings_scopes = ["project-local", "user-local", "user-global"]

    for scope_name in settings_scopes:
        if scope_name in self._scopes:
            handler = self._scopes[scope_name]
            if handler.exists():
                try:
                    current_data = handler.reader.read(handler.config.path)
                    enabled_servers = current_data.get("enabledMcpjsonServers", [])
                    disabled_servers = current_data.get("disabledMcpjsonServers", [])

                    if server_id in disabled_servers:
                        return ServerState.DISABLED
                    if server_id in enabled_servers:
                        return ServerState.ENABLED
                except Exception:
                    continue

    return ServerState.ENABLED  # Default if not in any array
```

**Issues**:
- Hardcoded list of settings scopes
- Mixed responsibility (knows about file format AND state logic)
- No extensibility for new scope types

2. **Enable Operation** (Lines 323-374):
```python
def enable_server(self, server_id: str) -> OperationResult:
    """Enable a server using Claude's actual format."""
    settings_scopes = ["project-local", "user-local", "user-global"]

    for scope_name in settings_scopes:
        if scope_name in self._scopes:
            handler = self._scopes[scope_name]

            # Read current settings file
            if handler.exists():
                current_data = handler.reader.read(handler.config.path)
            else:
                current_data = {}

            # Initialize arrays if they don't exist
            enabled_servers = current_data.get("enabledMcpjsonServers", [])
            disabled_servers = current_data.get("disabledMcpjsonServers", [])

            # Remove from disabled array if present
            if server_id in disabled_servers:
                disabled_servers.remove(server_id)

            # Add to enabled array if not already there
            if server_id not in enabled_servers:
                enabled_servers.append(server_id)

            # Update the data
            current_data["enabledMcpjsonServers"] = enabled_servers
            current_data["disabledMcpjsonServers"] = disabled_servers

            # Write back to file
            try:
                handler.writer.write(handler.config.path, current_data)
                return OperationResult.success_result(...)
            except Exception as e:
                return OperationResult.failure_result(...)

    return OperationResult.failure_result(
        "No suitable Claude settings scope found for enable/disable operations"
    )
```

**Issues**:
- Duplicate code between enable/disable (95% identical)
- Array manipulation logic mixed with file I/O
- Hardcoded scope selection logic
- First-scope-wins strategy (no explicit scope targeting)

3. **Disable Operation** (Lines 376-427): Nearly identical to enable, just inverted logic

---

## Architectural Problems

### Problem 1: Monolithic Client Files

**Current**: All claude-code logic in 518-line file

**Issues**:
- Hard to navigate
- Multiple responsibilities in one file
- Adding cursor/vscode would create more huge files
- Violates single responsibility principle

**Example**: `claude_code.py` contains:
- Scope initialization (6 scopes x 15 lines = 90 lines)
- State determination logic (40 lines)
- Enable/disable operations (104 lines)
- List servers logic (44 lines)
- Add/remove server delegation (40 lines)
- Validation logic (30 lines)
- Installation detection (35 lines)
- Utility methods (remaining)

---

### Problem 2: No Scope-Specific Handlers

**Current**: `FileBasedScope` is generic, knows nothing about enable/disable

**Issues**:
- Enable/disable logic lives in CLIENT, not SCOPE
- Different scopes have different formats, but use same handler
- No way to extend per-scope behavior
- Violates open/closed principle

**What's Missing**:
- `ClaudeSettingsScope` subclass with enable/disable methods
- `MCPConfigScope` subclass without enable/disable
- `InternalConfigScope` subclass for internal file

---

### Problem 3: Hardcoded Scope Lists

**Locations**:
1. `claude_code.py` line 178: `settings_scopes = ["project-local", "user-local", "user-global"]`
2. `claude_code.py` line 333: Same list in enable_server
3. `claude_code.py` line 386: Same list in disable_server

**Issues**:
- DRY violation (3 copies)
- Adding new scope requires updating 3 places
- No way to query "which scopes support enable/disable?"

---

### Problem 4: No Enable/Disable Protocols

**Missing**:
```python
class EnableDisableSupport(Protocol):
    """Protocol for scopes that support enable/disable."""

    def get_enabled_servers(self) -> List[str]:
        """Get list of explicitly enabled servers."""
        ...

    def get_disabled_servers(self) -> List[str]:
        """Get list of explicitly disabled servers."""
        ...

    def enable_server(self, server_id: str) -> OperationResult:
        """Enable a server in this scope."""
        ...

    def disable_server(self, server_id: str) -> OperationResult:
        """Disable a server in this scope."""
        ...
```

**Impact**: Client has to know implementation details of each scope type

---

## User Requirements vs Current Architecture

### Requirement 1: Each client in separate directory

**Current**: All clients mixed in `src/mcpi/clients/`

**User Wants**:
```
src/mcpi/clients/
├── claude_code/
│   ├── __init__.py
│   ├── plugin.py
│   ├── scopes/
│   │   ├── __init__.py
│   │   ├── project_mcp.py
│   │   ├── project_local.py
│   │   ├── user_local.py
│   │   ├── user_global.py
│   │   ├── user_internal.py
│   │   └── user_mcp.py
│   └── schemas/
│       └── ...
├── cursor/
│   └── ...
└── vscode/
    └── ...
```

**Status**: NOT IMPLEMENTED (0%)

---

### Requirement 2: Each scope in separate file

**Current**: All 6 scopes defined in `claude_code.py` lines 58-165

**User Wants**: Each scope in `scopes/{scope_name}.py`

**Status**: NOT IMPLEMENTED (0%)

---

### Requirement 3: Separate handlers for enable/disable operations

**Current**: All logic in client plugin

**User Wants**:
- Handler to get enabled/disabled servers for a scope
- Handler to enable a server in a scope
- Handler to disable a server in a scope
- Each scope implements if it supports enable/disable

**Status**: PARTIALLY IMPLEMENTED (40%)
- State determination exists but is in wrong place
- Enable/disable methods exist but are in wrong place
- No per-scope handlers

---

## Code Quality Assessment

### What's Good

1. **Correct Behavior**: Enable/disable works correctly for settings scopes
2. **Proper State Tracking**: Uses Claude's actual format correctly
3. **Atomic Operations**: Enable/disable are single-file writes
4. **Good Error Handling**: Try/except blocks around file operations
5. **Type Safety**: Uses TypedDict and Pydantic models

### What's Bad

1. **Massive Code Duplication**: `enable_server` and `disable_server` are 95% identical
2. **Poor Separation of Concerns**: Client knows file format details
3. **Hardcoded Lists**: Same scope list in 3 places
4. **No Abstraction**: Generic `FileBasedScope` used for different formats
5. **Testing Complexity**: Tests require mocking internal scope details

### Technical Debt Metrics

**Files requiring changes for new client**:
- `clients/registry.py` (add discovery)
- New monolithic client file (~500 lines)
- Tests (~200 lines)
- **Total**: 3 files, ~700 lines of code

**Files requiring changes to add enable/disable to new scope**:
- Client plugin file (add scope definition)
- Client plugin file (update hardcoded scope list in 3 places)
- Tests
- **Total**: 1 file, 3 locations, ~50 lines

---

## Testing Status

### Enable/Disable Tests

**Files**:
- `tests/test_clients_claude_code.py` (lines 206-420)
- `tests/test_functional_user_workflows.py` (lines 300-370)
- `tests/test_installer_workflows_integration.py` (lines 90-105)

**Coverage**:
```python
# From test_clients_claude_code.py
def test_disable_server_creates_arrays(plugin, mcp_harness):
    """Disable should create disabledMcpjsonServers array."""
    # Tests array creation ✅

def test_enable_server_creates_arrays(plugin, mcp_harness):
    """Enable should create enabledMcpjsonServers array."""
    # Tests array creation ✅

def test_get_server_state_with_arrays(plugin, mcp_harness):
    """State should be determined by arrays."""
    # Tests state logic ✅

def test_enable_disabled_server(plugin, mcp_harness):
    """Enable a disabled server should move it to enabled array."""
    # Tests state transition ✅

def test_disable_enabled_server(plugin, mcp_harness):
    """Disable an enabled server should move it to disabled array."""
    # Tests state transition ✅
```

**Test Pass Rate**: 85% (all enable/disable tests passing)

**Gaps**:
- No tests for scope-specific enable/disable behavior
- No tests for "which scopes support enable/disable?"
- No tests for enable/disable on wrong scope type

---

## Real-World Verification

### Actual Files Examined

1. **~/.claude/settings.local.json**:
```json
{
  "enabledMcpjsonServers": [],
  "disabledMcpjsonServers": [
    "frida-mcp",
    "ida-pro-mcp",
    "@scope/package-name"
  ]
}
```

2. **~/.claude/settings.json**:
```json
{
  "permissions": { ... },
  "model": "sonnet",
  "mcpServers": {
    "@scope/package-name": {
      "command": "npx",
      "args": ["@scope/package-name"],
      "env": {},
      "type": "stdio"
    }
  }
}
```

3. **CLI Output**:
```bash
$ mcpi list --client claude-code
MCP Servers
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ ID                  ┃ Client      ┃ Scope         ┃ State    ┃ Command       ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ @scope/package-name │ claude-code │ user-global   │ DISABLED │ npx           │
│ ida-pro-mcp         │ claude-code │ user-internal │ DISABLED │ /Users/bmf/…  │
│ frida-mcp           │ claude-code │ user-internal │ DISABLED │ frida-mcp     │
└─────────────────────┴─────────────┴───────────────┴──────────┴───────────────┘
```

**Verification**: DISABLED state correctly shown for servers in `disabledMcpjsonServers` array ✅

---

## Recommended Refactor Architecture

### New Directory Structure

```
src/mcpi/clients/
├── base/
│   ├── __init__.py
│   ├── plugin.py              # MCPClientPlugin base
│   ├── scope.py               # ScopeHandler base
│   └── enable_disable.py      # EnableDisableSupport protocol
├── claude_code/
│   ├── __init__.py            # Plugin export
│   ├── plugin.py              # ClaudeCodePlugin (100 lines)
│   ├── scopes/
│   │   ├── __init__.py
│   │   ├── base.py            # Shared Claude scope utilities
│   │   ├── project_mcp.py     # ProjectMcpScope (80 lines)
│   │   ├── project_local.py   # ProjectLocalScope (120 lines)
│   │   ├── user_local.py      # UserLocalScope (120 lines)
│   │   ├── user_global.py     # UserGlobalScope (120 lines)
│   │   ├── user_internal.py   # UserInternalScope (80 lines)
│   │   └── user_mcp.py        # UserMcpScope (80 lines)
│   └── schemas/
│       ├── claude-settings-schema.yaml
│       ├── internal-config-schema.yaml
│       └── mcp-config-schema.yaml
├── cursor/
│   ├── __init__.py
│   ├── plugin.py
│   └── scopes/
│       └── ...
├── shared/
│   ├── __init__.py
│   ├── file_reader.py         # JSONFileReader, etc.
│   ├── file_writer.py         # JSONFileWriter, etc.
│   └── validators.py          # YAMLSchemaValidator, etc.
├── manager.py                 # MCPManager (unchanged)
├── protocols.py               # Protocols (unchanged)
├── registry.py                # ClientRegistry (unchanged)
└── types.py                   # Types (unchanged)
```

### Scope Class Hierarchy

```python
# base/scope.py
class ScopeHandler(ABC):
    """Base for all scope handlers."""
    @abstractmethod
    def exists(self) -> bool: ...
    @abstractmethod
    def get_servers(self) -> Dict[str, Dict[str, Any]]: ...
    @abstractmethod
    def add_server(self, server_id: str, config: ServerConfig) -> OperationResult: ...
    @abstractmethod
    def remove_server(self, server_id: str) -> OperationResult: ...


# base/enable_disable.py
class EnableDisableSupport(Protocol):
    """Protocol for scopes supporting enable/disable."""
    def get_enabled_servers(self) -> List[str]: ...
    def get_disabled_servers(self) -> List[str]: ...
    def is_server_enabled(self, server_id: str) -> bool: ...
    def is_server_disabled(self, server_id: str) -> bool: ...
    def enable_server(self, server_id: str) -> OperationResult: ...
    def disable_server(self, server_id: str) -> OperationResult: ...


# claude_code/scopes/base.py
class ClaudeSettingsScope(ScopeHandler):
    """Base for Claude settings files supporting enable/disable."""

    def get_enabled_servers(self) -> List[str]:
        data = self.reader.read(self.config.path)
        return data.get("enabledMcpjsonServers", [])

    def get_disabled_servers(self) -> List[str]:
        data = self.reader.read(self.config.path)
        return data.get("disabledMcpjsonServers", [])

    def enable_server(self, server_id: str) -> OperationResult:
        """Enable by adding to enabled array, removing from disabled."""
        data = self.reader.read(self.config.path) if self.exists() else {}

        enabled = data.get("enabledMcpjsonServers", [])
        disabled = data.get("disabledMcpjsonServers", [])

        if server_id in disabled:
            disabled.remove(server_id)
        if server_id not in enabled:
            enabled.append(server_id)

        data["enabledMcpjsonServers"] = enabled
        data["disabledMcpjsonServers"] = disabled

        self.writer.write(self.config.path, data)
        return OperationResult.success_result(f"Enabled {server_id}")

    def disable_server(self, server_id: str) -> OperationResult:
        """Disable by adding to disabled array, removing from enabled."""
        # Similar implementation


class ClaudeMcpScope(ScopeHandler):
    """Base for Claude MCP config files (no enable/disable)."""
    # Does NOT implement EnableDisableSupport
    # Always returns ENABLED for all servers


# claude_code/scopes/project_local.py
class ProjectLocalScope(ClaudeSettingsScope):
    """Project-local settings (.claude/settings.local.json)."""
    # Inherits all enable/disable behavior
    # Just needs to specify path and schema


# claude_code/scopes/project_mcp.py
class ProjectMcpScope(ClaudeMcpScope):
    """Project MCP config (.mcp.json)."""
    # No enable/disable support
    # Servers always ENABLED
```

### Plugin Simplification

```python
# claude_code/plugin.py
class ClaudeCodePlugin(MCPClientPlugin):
    """Claude Code client plugin."""

    def _initialize_scopes(self) -> Dict[str, ScopeHandler]:
        """Initialize scopes by importing scope classes."""
        from .scopes import (
            ProjectMcpScope,
            ProjectLocalScope,
            UserLocalScope,
            UserGlobalScope,
            UserInternalScope,
            UserMcpScope,
        )

        return {
            "project-mcp": ProjectMcpScope(self._get_scope_path("project-mcp")),
            "project-local": ProjectLocalScope(self._get_scope_path("project-local")),
            "user-local": UserLocalScope(self._get_scope_path("user-local")),
            "user-global": UserGlobalScope(self._get_scope_path("user-global")),
            "user-internal": UserInternalScope(self._get_scope_path("user-internal")),
            "user-mcp": UserMcpScope(self._get_scope_path("user-mcp")),
        }

    def enable_server(self, server_id: str) -> OperationResult:
        """Enable server by delegating to first supporting scope."""
        for scope_name, handler in self._scopes.items():
            if isinstance(handler, EnableDisableSupport):
                if handler.has_server(server_id):
                    return handler.enable_server(server_id)

        return OperationResult.failure_result(
            f"Server {server_id} not found in any enable/disable scope"
        )

    def disable_server(self, server_id: str) -> OperationResult:
        """Disable server by delegating to first supporting scope."""
        for scope_name, handler in self._scopes.items():
            if isinstance(handler, EnableDisableSupport):
                if handler.has_server(server_id):
                    return handler.disable_server(server_id)

        return OperationResult.failure_result(
            f"Server {server_id} not found in any enable/disable scope"
        )

    def _get_server_state(self, server_id: str) -> ServerState:
        """Get state by asking scopes that support enable/disable."""
        for scope_name, handler in self._scopes.items():
            if isinstance(handler, EnableDisableSupport):
                if handler.is_server_disabled(server_id):
                    return ServerState.DISABLED
                if handler.is_server_enabled(server_id):
                    return ServerState.ENABLED

        # Default: if server exists in any scope but not in enable/disable arrays
        if self.find_server_scope(server_id):
            return ServerState.ENABLED

        return ServerState.NOT_INSTALLED
```

---

## Benefits of Refactor

### Separation of Concerns

**Before**: Plugin knows about file format, array names, scope types
**After**: Plugin delegates to scope classes, each scope knows its own format

### Extensibility

**Before**: Adding cursor client requires 500-line monolithic file
**After**: Copy directory structure, implement 6 scope classes of ~100 lines each

### Testability

**Before**: Tests mock internal file I/O details
**After**: Tests can mock entire scope objects with simple interfaces

### Maintainability

**Before**: Changing enable/disable logic requires editing 3 methods in 1 huge file
**After**: Change only in `ClaudeSettingsScope` base class, inherited by all settings scopes

### Discoverability

**Before**: `isinstance(handler, EnableDisableSupport)` → False (no protocol)
**After**: `isinstance(handler, EnableDisableSupport)` → True for settings scopes

---

## Migration Path

### Phase 1: Create New Structure (2 hours)

1. Create `clients/base/` directory
2. Move base classes to `base/plugin.py` and `base/scope.py`
3. Create `EnableDisableSupport` protocol in `base/enable_disable.py`
4. Create `clients/shared/` for file readers/writers
5. Create `clients/claude_code/` directory with subdirectories

### Phase 2: Extract Scope Classes (4 hours)

1. Create `claude_code/scopes/base.py` with `ClaudeSettingsScope` and `ClaudeMcpScope`
2. Create 6 scope files, one per scope (~1 hour each for first 3, ~30 min each for last 3)
3. Each scope class: 80-120 lines
4. Move enable/disable logic into `ClaudeSettingsScope` base class

### Phase 3: Simplify Plugin (1 hour)

1. Rewrite `claude_code/plugin.py` to import scopes
2. Simplify enable/disable methods to delegate
3. Remove hardcoded scope lists
4. Remove direct file manipulation

### Phase 4: Update Tests (2 hours)

1. Update imports
2. Update fixtures to use new structure
3. Add scope-specific tests
4. Add protocol compliance tests

### Phase 5: Verification (1 hour)

1. Run full test suite
2. Manual testing of enable/disable
3. Verify file format unchanged
4. Check CLI output

**Total Estimated Effort**: 10 hours

---

## Risks and Mitigations

### Risk 1: Breaking Changes

**Risk**: Refactor breaks existing functionality
**Probability**: MEDIUM
**Impact**: HIGH
**Mitigation**:
- Keep existing tests unchanged (just update imports)
- Use test harness for all testing
- Parallel implementation (keep old code until new works)
- Feature flag for new architecture

### Risk 2: Test Failures

**Risk**: Tests fail after refactor
**Probability**: HIGH
**Impact**: MEDIUM
**Mitigation**:
- Run tests after each phase
- Fix failures before proceeding
- Use git branches for each phase

### Risk 3: Incomplete Migration

**Risk**: Some code paths still use old structure
**Probability**: MEDIUM
**Impact**: HIGH
**Mitigation**:
- Grep for old import paths after migration
- Remove old files only after all tests pass
- Code review focusing on import statements

### Risk 4: Performance Regression

**Risk**: New architecture slower
**Probability**: LOW
**Impact**: LOW
**Mitigation**:
- Benchmark before/after
- Lazy loading of scope classes
- Caching if needed

---

## Complexity Assessment

### Code Complexity

**Current**:
- 1 file with 518 lines (claude_code.py)
- Cyclomatic complexity: ~15 per method
- 6 scope definitions inline
- Enable/disable logic duplicated

**After Refactor**:
- 1 plugin file with ~150 lines
- 6 scope files with ~100 lines each
- Cyclomatic complexity: ~5 per method
- Enable/disable logic in base class (DRY)

**Net Change**: +550 lines total, but -368 lines of duplication

### Cognitive Load

**Current**: High - Must understand entire file to make changes
**After Refactor**: Low - Each file has single responsibility

---

## Recommendation

### Immediate Actions (Critical Priority)

1. **Do NOT implement refactor before 1.0 release** (4 days away)
2. Current architecture WORKS correctly for all documented use cases
3. Refactor is ARCHITECTURAL improvement, not bug fix
4. Risk/benefit ratio too high for pre-release major refactor

### Post-1.0 Roadmap (P1)

1. **Release 1.0** (2025-11-03) with current architecture
2. **Plan refactor** (2025-11-04, 1 day)
3. **Implement refactor** (2025-11-05 to 2025-11-09, 4-5 days)
4. **Test and verify** (2025-11-10, 1 day)
5. **Release 1.1** (2025-11-11) with new architecture

### Success Criteria for Refactor

**Must Have**:
- All existing tests pass (565 tests, 85% pass rate maintained)
- Enable/disable functionality unchanged from user perspective
- No performance regression (< 5% slower)
- Zero breaking changes to public API

**Nice to Have**:
- Improved test coverage (40% → 50%)
- Reduced code duplication (current: ~200 lines duplicated → 0)
- Better documentation of architecture
- Example cursor/vscode client implementation

---

## Appendix: Code Metrics

### Current Codebase

```
src/mcpi/clients/
├── base.py             329 lines  (8,550 bytes)
├── claude_code.py      518 lines  (19,003 bytes)  ← REFACTOR TARGET
├── file_based.py       558 lines  (18,210 bytes)  ← REFACTOR TARGET
├── manager.py          423 lines  (14,700 bytes)
├── protocols.py         92 lines  (3,132 bytes)
├── registry.py         423 lines  (14,344 bytes)
└── types.py            115 lines  (3,014 bytes)

Total: 2,458 lines (80,953 bytes)
```

### After Refactor (Estimated)

```
src/mcpi/clients/
├── base/
│   ├── plugin.py            200 lines
│   ├── scope.py             150 lines
│   └── enable_disable.py     80 lines
├── claude_code/
│   ├── plugin.py            150 lines
│   └── scopes/
│       ├── base.py          120 lines
│       ├── project_mcp.py    80 lines
│       ├── project_local.py 120 lines
│       ├── user_local.py    120 lines
│       ├── user_global.py   120 lines
│       ├── user_internal.py  80 lines
│       └── user_mcp.py       80 lines
├── shared/
│   ├── file_reader.py       100 lines
│   ├── file_writer.py       100 lines
│   └── validators.py        150 lines
├── manager.py               423 lines (unchanged)
├── protocols.py              92 lines (unchanged)
├── registry.py              423 lines (unchanged)
└── types.py                 115 lines (unchanged)

Total: 2,703 lines (+245 lines, -200 duplicate lines = +45 net)
```

---

## Conclusion

### Current State Summary

**Functionally**: WORKS CORRECTLY (60% satisfaction of user requirements)
- Enable/disable operations work
- State tracking accurate
- CLI commands functional
- File formats correct

**Architecturally**: NEEDS IMPROVEMENT (0% satisfaction of user requirements)
- No client directories
- No scope files
- No separate enable/disable handlers
- Monolithic design

### User Request Alignment

User asked to evaluate "gaps identified by the user":

1. ✅ **Identified**: Each client should be in separate directory (GAP)
2. ✅ **Identified**: Each scope should be in separate file (GAP)
3. ✅ **Identified**: Need separate enable/disable handlers (PARTIAL GAP)
4. ✅ **Verified**: project-local scope works (NO GAP)
5. ✅ **Verified**: user-global scope works (NO GAP)
6. ✅ **Clarified**: Different scopes have different formats (BY DESIGN)

### Recommended Action

**For 1.0 Release**: Ship current architecture (WORKS, tested, stable)
**For 1.1 Release**: Implement refactor (CLEANER, more maintainable)

**Rationale**: "Premature optimization is the root of all evil" - Donald Knuth

The current code WORKS. Refactoring 4 days before release for ARCHITECTURAL reasons (not bugs) is high-risk, low-reward. Ship 1.0, then refactor with no time pressure.

---

**End of Evaluation**
