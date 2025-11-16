# MCPI Disable Command Evaluation

**Date**: 2025-11-13
**Evaluator**: Claude Code
**Focus**: Enable/Disable Command Implementation Analysis
**User Requirement**: Fix disable command for user-internal scope using per-scope enable/disable handlers

---

## Executive Summary

**Current State**: The enable/disable functionality is **PARTIALLY IMPLEMENTED** with a sophisticated architecture BUT **user-internal scope explicitly does NOT support enable/disable operations**.

**User Request Conflict**: User wants enable/disable to work in user-internal scope (~/.claude.json), but:
1. Current implementation explicitly sets `enable_disable_handler=None` for user-internal
2. Architecture comment states: "user-internal doesn't support enable/disable"
3. The ~/.claude.json file format has no enable/disable array support

**Critical Finding**: The user's understanding that "servers are stored in ~/.claude.json" and "if servers are in that file, they are enabled" suggests they want to use user-internal scope, but **the current architecture intentionally does not support enable/disable for this scope**.

**Architectural Gap**: User wants a different behavior than currently implemented.

---

## 1. Current Implementation Analysis

### 1.1 Architecture Overview

The codebase has a **well-designed plugin-based enable/disable system**:

**File**: `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/claude_code.py`

**Scope Configuration** (lines 62-199):
```python
# 6 scopes defined with different enable/disable support:

# Scopes WITH enable/disable support:
1. project-local (~/.claude/settings.local.json) - ArrayBasedEnableDisableHandler
2. user-local (~/.claude/settings.local.json) - ArrayBasedEnableDisableHandler
3. user-global (~/.claude/settings.json) - FileTrackedEnableDisableHandler

# Scopes WITHOUT enable/disable support:
4. project-mcp (.mcp.json) - enable_disable_handler=None
5. user-internal (~/.claude.json) - enable_disable_handler=None ⚠️ USER WANTS THIS
6. user-mcp (~/.claude/mcp_servers.json) - enable_disable_handler=None
```

### 1.2 Enable/Disable Handler Protocols

**File**: `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/protocols.py` (lines 133-175)

**Protocol Definition**:
```python
class EnableDisableHandler(Protocol):
    """Protocol for handling enable/disable operations on servers."""

    def is_disabled(self, server_id: str) -> bool: ...
    def disable(self, server_id: str) -> bool: ...
    def enable(self, server_id: str) -> bool: ...
```

**Two Implementations**:

#### 1.2.1 ArrayBasedEnableDisableHandler

**File**: `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/enable_disable_handlers.py` (lines 10-127)

**Mechanism**:
- Uses `enabledMcpjsonServers` and `disabledMcpjsonServers` arrays in config file
- Modifies these arrays in-place within the configuration JSON
- Used by: project-local, user-local scopes

**How it works**:
- **Enable**: Adds server to `enabledMcpjsonServers`, removes from `disabledMcpjsonServers`
- **Disable**: Adds server to `disabledMcpjsonServers`, removes from `enabledMcpjsonServers`
- **State check**: Server is disabled if in `disabledMcpjsonServers` array

#### 1.2.2 FileTrackedEnableDisableHandler

**File**: `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/enable_disable_handlers.py` (lines 129-177)

**Mechanism**:
- Uses a **separate tracking file** to store disabled server IDs
- Used for scopes where the config format doesn't support enable/disable arrays
- Used by: user-global scope (~/.claude/settings.json)

**How it works**:
- **Tracking file**: `~/.claude/.mcpi-disabled-servers.json` (separate from config)
- **Enable**: Removes server from tracking file
- **Disable**: Adds server to tracking file
- **State check**: Server is disabled if in tracking file

**DisabledServersTracker** (`disabled_tracker.py` lines 13-119):
- Stores disabled servers as JSON array: `["server-1", "server-2"]`
- File location: Passed to constructor (e.g., `~/.claude/.mcpi-disabled-servers.json`)

### 1.3 Current Scope Support Matrix

| Scope | Path | Enable/Disable Handler | Notes |
|-------|------|----------------------|-------|
| project-mcp | `.mcp.json` | **None** | Format doesn't support arrays |
| project-local | `.claude/settings.local.json` | ArrayBased | Has enable/disable arrays |
| user-local | `~/.claude/settings.local.json` | ArrayBased | Has enable/disable arrays |
| user-global | `~/.claude/settings.json` | **FileTracked** | Uses separate tracking file |
| **user-internal** | **~/.claude.json** | **None** ⚠️ | **User wants this** |
| user-mcp | `~/.claude/mcp_servers.json` | **None** | Format doesn't support arrays |

### 1.4 CLI Command Implementation

**File**: `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/cli.py`

**disable command** (lines 1174-1229):
```python
@main.command()
@click.argument("server_id", shell_complete=complete_server_ids)
@click.option("--client", ...)
@click.option("--dry-run", ...)
def disable(ctx: click.Context, server_id: str, client: Optional[str], dry_run: bool):
    """Disable an enabled MCP server."""
    manager = get_mcp_manager(ctx)

    # Check current state
    current_state = manager.get_server_state(server_id, client)
    if current_state == ServerState.NOT_INSTALLED:
        console.print(f"[red]Server '{server_id}' is not installed[/red]")
        return

    if current_state == ServerState.DISABLED:
        console.print(f"[yellow]Server '{server_id}' is already disabled[/yellow]")
        return

    # Disable the server
    result = manager.disable_server(server_id, client)
    # ... handle result
```

**Flow**:
1. CLI command → MCPManager → ClientRegistry → ClaudeCodePlugin
2. Plugin finds server's scope
3. Plugin calls scope handler's `enable_disable_handler.disable(server_id)`
4. If handler is None, operation fails

### 1.5 Plugin Enable/Disable Implementation

**File**: `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/claude_code.py` (lines 406-452)

**disable_server** method:
```python
def disable_server(self, server_id: str) -> OperationResult:
    """Disable a server in its current scope."""

    # Find the server's actual scope
    server_scope = None
    for scope_name, handler in self._scopes.items():
        if handler.has_server(server_id):
            server_scope = scope_name
            break

    if not server_scope:
        return OperationResult.failure_result(
            f"Server '{server_id}' not found in any scope"
        )

    # Get the scope handler
    handler = self._scopes[server_scope]

    # Check if this scope supports enable/disable
    if (not hasattr(handler, "enable_disable_handler")
        or not handler.enable_disable_handler):
        return OperationResult.failure_result(
            f"Scope '{server_scope}' does not support enable/disable operations"
        )

    # Use the scope's enable/disable handler
    if handler.enable_disable_handler.disable(server_id):
        return OperationResult.success_result(...)
    else:
        return OperationResult.failure_result(...)
```

**Key behavior**:
- Finds server's scope automatically
- Returns error if scope doesn't support enable/disable
- Uses scope-specific handler if available

---

## 2. Identified Problems

### 2.1 Critical Issue: User-Internal Scope Lacks Enable/Disable Support

**Location**: `src/mcpi/clients/claude_code.py` line 178
**Code**: `enable_disable_handler=None`
**Comment**: "# user-internal doesn't support enable/disable"

**Problem**: User wants to disable servers in user-internal scope (~/.claude.json), but:
1. Scope is explicitly configured without enable/disable handler
2. The ~/.claude.json file format may not have enable/disable arrays
3. No mechanism exists to track disabled state for this scope

**User Impact**: Running `mcpi disable <server>` on a server in user-internal scope results in error:
```
Scope 'user-internal' does not support enable/disable operations
```

### 2.2 Architectural Confusion: Which File is "The" Claude Settings?

**User's Understanding**:
> "Servers are stored in ~/.claude.json"
> "If servers are in that file, they are enabled"
> "To disable them, copy the config to a different file"

**Reality**: Claude Code has **multiple** configuration files:
- `~/.claude.json` (user-internal) - Internal config, no enable/disable
- `~/.claude/settings.json` (user-global) - Has enable/disable via tracking file
- `~/.claude/settings.local.json` (user-local) - Has enable/disable via arrays

**Confusion Source**: User thinks ~/.claude.json is the "primary" file where servers live, but:
- Current implementation doesn't prioritize it (priority=5, higher number = lower priority)
- It's marked as "internal" configuration
- User-global and user-local have better enable/disable support

### 2.3 Design Pattern Not Clear: When to Use Which Scope?

**No Clear Guidance**: Neither code nor docs explain:
1. Which scope users should prefer for their servers
2. Why user-internal exists if it has fewer features
3. When to use user-internal vs user-global vs user-local

**Discovered via inspection**:
- **Priority ranking**: project-mcp(1) > project-local(2) > user-local(3) > user-global(4) > **user-internal(5)** > user-mcp(6)
- Lower number = higher priority = overrides others
- user-internal has **lowest priority** among non-mcp scopes

### 2.4 Test Coverage Gap: User-Internal Disable Not Tested

**File**: `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/tests/test_enable_disable_bugs.py`

**Extensive test coverage exists**, but:
- Tests cover project-local, user-local, user-global
- **No tests for user-internal enable/disable** (because it's not supported)
- Tests verify "scope does not support enable/disable" error case (line 309-380)
- Tests explicitly verify user-global scope behavior with tracking file

**This is CORRECT**: Tests reflect current architecture decision.

---

## 3. User Requirements vs Current Architecture

### 3.1 What User Wants

Based on user's description:
1. Servers stored in ~/.claude.json (user-internal scope)
2. If server is in that file → it's enabled
3. To disable → move/copy config to a different file for that scope
4. Each scope has custom Enabler & Disabler functions

### 3.2 Current Architecture Approach

**For scopes with array support**:
- Servers stay in `mcpServers` object
- State tracked via `enabledMcpjsonServers` / `disabledMcpjsonServers` arrays
- No file movement

**For user-global (no array support)**:
- Servers stay in `mcpServers` object in ~/.claude/settings.json
- Disabled state tracked in separate file: `~/.claude/.mcpi-disabled-servers.json`
- No file movement

**For user-internal (no support)**:
- Servers in `mcpServers` object in ~/.claude.json
- **No enable/disable mechanism at all**

### 3.3 Architectural Gap Analysis

**User's mental model**:
```
~/.claude.json (enabled servers)
~/.claude/.disabled/<scope>/server-name.json (disabled servers)
```

**Current implementation model**:
```
~/.claude.json (all servers, no state tracking)
~/.claude/settings.json (all servers + separate disabled tracking file)
~/.claude/settings.local.json (all servers + enable/disable arrays)
```

**Key Difference**: User expects file-based enable/disable (move config to different file), but current implementation uses:
- In-file arrays (for settings.local.json)
- Separate tracking file (for settings.json)
- Nothing (for .claude.json)

---

## 4. Existing Enable/Disable Patterns in Codebase

### 4.1 Pattern 1: Array-Based (In-Config Arrays)

**Used by**: project-local, user-local

**Implementation**: `ArrayBasedEnableDisableHandler`

**How it works**:
```json
// File: ~/.claude/settings.local.json
{
  "mcpServers": {
    "server-1": { "command": "npx", "args": ["-y", "server-1"] },
    "server-2": { "command": "npx", "args": ["-y", "server-2"] }
  },
  "enabledMcpjsonServers": ["server-1"],
  "disabledMcpjsonServers": ["server-2"]
}
```

**Pros**:
- All state in one file
- Atomic updates
- Easy to inspect

**Cons**:
- Requires file format support (has these arrays)
- Modifies official Claude config format

### 4.2 Pattern 2: File-Tracked (Separate Tracking File)

**Used by**: user-global

**Implementation**: `FileTrackedEnableDisableHandler` + `DisabledServersTracker`

**How it works**:
```json
// File 1: ~/.claude/settings.json (official format)
{
  "mcpServers": {
    "server-1": { "command": "npx", "args": ["-y", "server-1"] },
    "server-2": { "command": "npx", "args": ["-y", "server-2"] }
  }
}

// File 2: ~/.claude/.mcpi-disabled-servers.json (MCPI's tracking)
["server-2"]
```

**Pros**:
- Doesn't modify official Claude config format
- Can work with any config format
- Clean separation of concerns

**Cons**:
- Two files to keep in sync
- Potential for drift
- Extra file to manage

### 4.3 Pattern 3: No Support

**Used by**: project-mcp, user-internal, user-mcp

**Implementation**: `enable_disable_handler=None`

**How it works**: Returns error when enable/disable attempted

**Reason**: Config format doesn't support enable/disable, or scope is "internal"

---

## 5. Recommended Approach to Implement User's Requirements

### 5.1 Option A: Extend user-internal with FileTrackedEnableDisableHandler

**Approach**: Same as user-global, use a separate tracking file

**Implementation**:
```python
# In claude_code.py _initialize_scopes():

# User internal configuration (~/.claude.json)
user_internal_path = self._get_scope_path(
    "user-internal", Path.home() / ".claude.json"
)
user_internal_disabled_tracker_path = self._get_scope_path(
    "user-internal-disabled",
    Path.home() / ".claude" / ".mcpi-disabled-servers-internal.json",
)
scopes["user-internal"] = FileBasedScope(
    config=ScopeConfig(
        name="user-internal",
        description="User internal Claude configuration (~/.claude.json)",
        priority=5,
        path=user_internal_path,
        is_user_level=True,
    ),
    reader=json_reader,
    writer=json_writer,
    validator=YAMLSchemaValidator(),
    schema_path=schemas_dir / "internal-config-schema.yaml",
    enable_disable_handler=FileTrackedEnableDisableHandler(
        DisabledServersTracker(user_internal_disabled_tracker_path)
    ),  # NEW: Now supports enable/disable
)
```

**Files created**:
- `~/.claude/.mcpi-disabled-servers-internal.json` - Tracks disabled servers for user-internal scope

**Pros**:
- Consistent with user-global approach
- Minimal code changes (reuse existing handler)
- Doesn't modify ~/.claude.json format
- Clear separation of MCPI state from Claude state

**Cons**:
- Creates another tracking file
- Doesn't match user's "move config to different file" mental model

**Effort**: 30 minutes (1 file change, tests)

**Risk**: Low (reusing proven pattern)

### 5.2 Option B: Create File-Movement-Based Handler

**Approach**: Implement user's exact mental model - move config to different file

**Implementation**:
```python
# New handler: FileMoveBasedEnableDisableHandler

class FileMoveBasedEnableDisableHandler:
    """Enable/disable by moving server config between files."""

    def __init__(
        self,
        enabled_config_path: Path,  # ~/.claude.json
        disabled_config_path: Path,  # ~/.claude/.disabled-servers.json
        reader: ConfigReader,
        writer: ConfigWriter,
    ):
        self.enabled_path = enabled_config_path
        self.disabled_path = disabled_config_path
        self.reader = reader
        self.writer = writer

    def is_disabled(self, server_id: str) -> bool:
        """Check if server is in disabled file."""
        disabled_data = self.reader.read(self.disabled_path)
        return server_id in disabled_data.get("mcpServers", {})

    def disable(self, server_id: str) -> bool:
        """Move server from enabled file to disabled file."""
        # Read both files
        enabled_data = self.reader.read(self.enabled_path)
        disabled_data = self.reader.read(self.disabled_path) if self.disabled_path.exists() else {"mcpServers": {}}

        # Move server config
        if server_id in enabled_data.get("mcpServers", {}):
            disabled_data.setdefault("mcpServers", {})[server_id] = enabled_data["mcpServers"][server_id]
            del enabled_data["mcpServers"][server_id]

            # Write both files
            self.writer.write(self.enabled_path, enabled_data)
            self.writer.write(self.disabled_path, disabled_data)
            return True
        return False

    def enable(self, server_id: str) -> bool:
        """Move server from disabled file to enabled file."""
        # Similar logic, opposite direction
        ...
```

**Pros**:
- Matches user's mental model exactly
- Server configs physically separated by state
- Easy to inspect (look at files to see enabled vs disabled)
- Could support per-scope disabled files

**Cons**:
- More complex than tracking file (manages two config files)
- Risk of data loss during move
- Need transaction-like behavior (move is not atomic)
- Need to handle errors gracefully (what if enabled file has server but disabled file also has it?)
- Breaking change if server configs are already in ~/.claude.json

**Effort**: 4-8 hours (new handler class, extensive testing, error handling)

**Risk**: Medium-High (file management complexity, data loss risk)

### 5.3 Option C: Document that user-internal doesn't support enable/disable

**Approach**: Keep current architecture, improve documentation

**Implementation**:
- Update README to explain scope differences
- Add guidance on which scope to use
- Clarify that user-internal is "internal" and has limited features
- Recommend using user-global or user-local for user-level servers

**Pros**:
- Zero code changes
- Zero risk
- Preserves intentional design decision

**Cons**:
- Doesn't solve user's problem
- User confusion remains
- Need to migrate existing servers from user-internal to supported scope

**Effort**: 1 hour (docs only)

**Risk**: None

### 5.4 Option D: Hybrid - Add enable/disable to user-internal AND improve docs

**Approach**: Option A + Option C

**Implementation**:
1. Add FileTrackedEnableDisableHandler to user-internal (like user-global)
2. Update docs to explain:
   - All user-level scopes now support enable/disable
   - user-global and user-internal use separate tracking files
   - user-local uses in-config arrays
3. Add migration guide if needed

**Pros**:
- Solves user's immediate problem
- Low risk (reuses proven pattern)
- Provides clear guidance
- Consistent behavior across user-level scopes

**Cons**:
- Another tracking file to manage
- Still doesn't match user's "file movement" mental model exactly

**Effort**: 2 hours (code + tests + docs)

**Risk**: Low

---

## 6. Test Coverage Analysis

### 6.1 Existing Test Suite

**File**: `tests/test_enable_disable_bugs.py`

**Coverage**: Excellent (752 lines, 11 functional tests)

**What's tested**:
✅ Cross-scope state isolation (BUG-1)
✅ Wrong scope modification prevention (BUG-3)
✅ Array-based enable/disable (user-local, project-local)
✅ File-tracked enable/disable (user-global)
✅ Idempotency of enable/disable operations
✅ Error handling for unsupported scopes
✅ Multi-scope state independence

**What's NOT tested**:
❌ Enable/disable for user-internal (because it's not supported)
❌ File-movement-based enable/disable (doesn't exist)

### 6.2 Test Gaps if We Add Support

**If implementing Option A** (FileTracked for user-internal):
- Need 3-5 new tests for user-internal scope
- Test pattern already exists (copy from user-global tests)
- Estimated effort: 1 hour

**If implementing Option B** (File-movement based):
- Need 8-12 new tests for file movement logic
- Test error cases (concurrent access, missing files, etc.)
- Estimated effort: 3-4 hours

### 6.3 Test Framework Readiness

**MCPTestHarness** (`tests/test_harness.py`):
- ✅ Supports path overrides for all scopes
- ✅ Handles temporary file management
- ✅ Provides scope file read/write utilities
- ✅ Ready to test any scope configuration

**No gaps**: Test framework fully supports testing new enable/disable handlers

---

## 7. Recommended Implementation Plan

### 7.1 Recommended Option: **Option D (Hybrid)**

**Rationale**:
1. **Solves user's problem**: user-internal will support enable/disable
2. **Low risk**: Reuses proven FileTrackedEnableDisableHandler pattern
3. **Minimal effort**: 2 hours vs 4-8 hours for custom solution
4. **Maintainable**: One pattern (FileTracked) for all "no array support" scopes
5. **Tested**: Can copy test patterns from user-global tests

### 7.2 Implementation Steps

#### Step 1: Add Enable/Disable Handler to user-internal (30 min)

**File**: `src/mcpi/clients/claude_code.py`

**Change** (lines 162-179):
```python
# User internal configuration (~/.claude.json)
# NOW supports enable/disable via separate tracking file
user_internal_path = self._get_scope_path(
    "user-internal", Path.home() / ".claude.json"
)
user_internal_disabled_tracker_path = self._get_scope_path(
    "user-internal-disabled",
    Path.home() / ".claude" / ".mcpi-disabled-servers-internal.json",
)
scopes["user-internal"] = FileBasedScope(
    config=ScopeConfig(
        name="user-internal",
        description="User internal Claude configuration (~/.claude.json)",
        priority=5,
        path=user_internal_path,
        is_user_level=True,
    ),
    reader=json_reader,
    writer=json_writer,
    validator=YAMLSchemaValidator(),
    schema_path=schemas_dir / "internal-config-schema.yaml",
    enable_disable_handler=FileTrackedEnableDisableHandler(  # CHANGED
        DisabledServersTracker(user_internal_disabled_tracker_path)
    ),
)
```

#### Step 2: Add Tests for user-internal Enable/Disable (1 hour)

**File**: `tests/test_enable_disable_bugs.py`

**New test class**:
```python
class TestUserInternalEnableDisable:
    """Test enable/disable for user-internal scope using file tracking."""

    @pytest.fixture
    def plugin(self, mcp_harness):
        """Create a ClaudeCodePlugin with test harness."""
        return ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)

    def test_user_internal_disable_server_creates_tracking_file(self, plugin, mcp_harness):
        """Test that disabling user-internal server creates tracking file."""
        # Setup: Install server in user-internal
        mcp_harness.prepopulate_file(
            "user-internal",
            {
                "mcpServers": {
                    "test-server": {
                        "command": "npx",
                        "args": ["-y", "test-server"],
                        "type": "stdio",
                    }
                },
            },
        )

        # Execute: Disable the server
        result = plugin.disable_server("test-server")

        # Verify: Operation succeeded
        assert result.success, f"Failed to disable server: {result.message}"

        # Verify: Tracking file was created
        tracking_path = Path(mcp_harness.path_overrides["user-internal-disabled"])
        assert tracking_path.exists(), "Tracking file was not created"

        # Verify: Server is in tracking file
        import json
        with tracking_path.open("r") as f:
            disabled = json.load(f)
        assert "test-server" in disabled

    def test_user_internal_enable_server_removes_from_tracking_file(self, ...):
        """Test that enabling user-internal server removes from tracking file."""
        # Similar pattern to above
        ...

    def test_user_internal_disabled_server_shows_correct_state(self, ...):
        """Test that list shows correct state for disabled user-internal server."""
        # Similar to user-global tests
        ...
```

**Estimated**: 3-5 tests, copy pattern from `TestListServersWithCorrectState`

#### Step 3: Update Documentation (30 min)

**File**: `CLAUDE.md`

**Add section** under "## Project Architecture":

```markdown
### Enable/Disable Mechanisms by Scope

MCPI supports enabling and disabling MCP servers to control which ones are active
without removing their configurations. Different scopes use different mechanisms:

#### Scopes with Array-Based Enable/Disable

**Scopes**: project-local, user-local

**Files**:
- `~/.claude/settings.local.json` (user-local)
- `.claude/settings.local.json` (project-local)

**Mechanism**: Uses `enabledMcpjsonServers` and `disabledMcpjsonServers` arrays
within the configuration file.

**Example**:
```json
{
  "mcpServers": {
    "server-1": { "command": "npx", "args": ["-y", "server-1"] },
    "server-2": { "command": "npx", "args": ["-y", "server-2"] }
  },
  "enabledMcpjsonServers": ["server-1"],
  "disabledMcpjsonServers": ["server-2"]
}
```

#### Scopes with File-Tracked Enable/Disable

**Scopes**: user-global, user-internal

**Files**:
- `~/.claude/settings.json` (user-global)
- `~/.claude.json` (user-internal)

**Mechanism**: Server configurations remain in the config file. Disabled servers
are tracked in a separate MCPI-managed file that doesn't modify Claude's official
configuration format.

**Tracking Files**:
- `~/.claude/.mcpi-disabled-servers.json` (for user-global)
- `~/.claude/.mcpi-disabled-servers-internal.json` (for user-internal)

**Example**:
```json
// ~/.claude.json (all servers)
{
  "mcpServers": {
    "server-1": { ... },
    "server-2": { ... }
  }
}

// ~/.claude/.mcpi-disabled-servers-internal.json (disabled list)
["server-2"]
```

#### Scopes Without Enable/Disable Support

**Scopes**: project-mcp, user-mcp

**Reason**: These scopes use the `.mcp.json` format which doesn't support
enable/disable arrays. If you need enable/disable functionality, use a scope
that supports it (see above).

#### Choosing the Right Scope

For user-level servers that you want to enable/disable:
- **user-local**: Best for local development, supports array-based enable/disable
- **user-global**: Best for permanent user-wide settings, uses tracking file
- **user-internal**: Internal Claude config, uses tracking file (less common)

For project-level servers:
- **project-local**: Best choice, supports array-based enable/disable
- **project-mcp**: Doesn't support enable/disable
```

#### Step 4: Run Tests (10 min)

```bash
# Run enable/disable tests
pytest tests/test_enable_disable_bugs.py -v

# Run full test suite
pytest -v
```

#### Step 5: Manual Verification (10 min)

```bash
# Test user-internal enable/disable
mcpi add <some-server> --scope user-internal
mcpi list --scope user-internal  # Should show ENABLED
mcpi disable <server>
mcpi list --scope user-internal  # Should show DISABLED
cat ~/.claude/.mcpi-disabled-servers-internal.json  # Should contain server
mcpi enable <server>
mcpi list --scope user-internal  # Should show ENABLED
cat ~/.claude/.mcpi-disabled-servers-internal.json  # Should be empty or not contain server
```

### 7.3 Total Effort Estimate

- Code changes: 30 minutes
- Test implementation: 1 hour
- Documentation: 30 minutes
- Testing & verification: 20 minutes
- **Total: 2 hours 20 minutes**

### 7.4 Risk Assessment

**Technical Risk**: **LOW**
- Reusing proven FileTrackedEnableDisableHandler
- Same pattern as user-global (already tested and working)
- No changes to file formats
- No data migration needed

**User Impact Risk**: **LOW**
- Additive change (adds feature, doesn't break existing)
- Users with servers in user-internal can now disable them
- No breaking changes

**Maintenance Risk**: **LOW**
- One additional tracking file to manage
- Pattern already exists and is maintained
- Test coverage ensures behavior is correct

---

## 8. Alternative Considerations

### 8.1 Why Not File-Movement Pattern?

User's original description suggests moving configs between files:
> "To disable them, copy the config to a different file that represents all disabled plugins for that scope"

**Analysis**: While this matches user's mental model, it has significant drawbacks:

1. **Complexity**: Managing two config files per scope (enabled + disabled)
2. **Risk**: File moves can fail, leading to data loss
3. **Atomicity**: No atomic move operation in Python (multiple writes)
4. **Testing**: Harder to test (more error cases)
5. **User Confusion**: Now users have to know about two files per scope
6. **Breaking Change**: What if servers already exist in ~/.claude.json?

**Recommendation**: Stick with tracking file pattern. It's:
- Simpler to implement
- Safer (original config never moves)
- Easier to test
- Proven in production (user-global uses it)
- Non-breaking (doesn't touch existing configs)

### 8.2 Why Not Just Use user-global Instead?

**Could tell user**: "Use user-global scope instead of user-internal"

**Problems**:
1. User specifically mentioned ~/.claude.json (user-internal)
2. Moving servers between scopes requires manual migration
3. User may have reasons for using user-internal we don't know
4. Doesn't solve the architecture question "why does user-internal exist?"

**Better**: Support both, document the difference clearly

### 8.3 Should We Remove user-internal Scope Entirely?

**Analysis**: user-internal has lowest priority (5) and fewest features. Why does it exist?

**Possible reasons**:
- Claude Code internal configuration (not user-facing)
- Historical/legacy scope
- Separation of "internal" vs "user" config

**Recommendation**: Keep it but add enable/disable support. Removing it could break existing users.

---

## 9. Risks and Concerns

### 9.1 Breaking Changes

**Current change is NOT breaking**:
- Additive only (adds enable/disable where it didn't exist)
- Existing user-internal servers remain enabled by default
- No file format changes
- No migration required

### 9.2 Tracking File Proliferation

**Concern**: We're adding more hidden files

**Current tracking files**:
- `~/.claude/.mcpi-disabled-servers.json` (user-global)
- `~/.claude/.mcpi-disabled-servers-internal.json` (user-internal - NEW)

**Mitigation**:
- Both in same directory (`~/.claude/`)
- Both follow same naming convention (`.mcpi-disabled-servers-*.json`)
- Both are JSON (easy to inspect/edit)
- Both are gitignored by default (shouldn't commit)
- Could consolidate into one file with scope prefixes in future

### 9.3 State Synchronization

**Concern**: Tracking files can get out of sync with config files

**Scenarios**:
1. User manually edits ~/.claude.json to remove server
2. Tracking file still has server marked as disabled
3. Server is "disabled" but doesn't exist

**Current behavior**: This is fine, no-op (can't disable non-existent server)

**Could improve**: Add `mcpi doctor` command to detect and fix sync issues

### 9.4 Performance

**Concern**: Reading extra tracking files on every operation

**Analysis**:
- Tracking files are tiny (just array of server names)
- Cached by OS after first read
- Only read when listing servers or checking state
- Minimal performance impact

**Measurement needed**: No, this is not a performance-critical path

---

## 10. Long-Term Architectural Considerations

### 10.1 Unified Enable/Disable Storage

**Future possibility**: Consolidate all scope tracking into one file

**Example**:
```json
// ~/.claude/.mcpi-disabled-servers.json
{
  "user-global": ["server-1", "server-3"],
  "user-internal": ["server-2"],
  "project-local": []  // Uses arrays, empty
}
```

**Pros**:
- One file instead of multiple
- Easier to inspect all disabled state
- Centralized management

**Cons**:
- More complex to maintain
- Coupling between scopes
- Harder to test in isolation

**Recommendation**: Keep separate files for now, revisit if users complain about file proliferation

### 10.2 Future Scope Additions

**Pattern established**: For scopes without array support, use FileTrackedEnableDisableHandler

**Template for adding new scopes**:
1. Does scope's file format support enable/disable arrays?
   - **Yes** → Use ArrayBasedEnableDisableHandler
   - **No** → Use FileTrackedEnableDisableHandler with unique tracking file
2. Add tests following established pattern
3. Document the mechanism

### 10.3 Enable/Disable State Migration

**Not needed now**, but if we ever change mechanisms:
- Could provide migration command
- Could auto-detect old format and convert
- Could support both formats temporarily

---

## 11. Summary of Findings

### 11.1 Current State

**Architecture**: SOPHISTICATED and WELL-DESIGNED
- Plugin-based enable/disable system
- Two handler implementations (array-based, file-tracked)
- Clear protocol definition (EnableDisableHandler)
- Extensive test coverage (11 functional tests, 752 lines)
- Per-scope configuration flexibility

**Problem**: user-internal scope **INTENTIONALLY** doesn't support enable/disable
- Explicitly set `enable_disable_handler=None`
- Documented in code comment
- No tests for it (correctly, since it's not supported)

### 11.2 Gap Analysis

**User Expectation**: Can enable/disable servers in ~/.claude.json (user-internal)

**Current Reality**: user-internal doesn't support enable/disable

**Root Cause**: Design decision, not a bug

**Solution Complexity**: LOW (reuse existing pattern)

### 11.3 Recommended Action

**Implement Option D (Hybrid)**:
1. Add FileTrackedEnableDisableHandler to user-internal scope
2. Create tests for user-internal enable/disable
3. Update documentation to explain all scope mechanisms
4. Total effort: **2 hours 20 minutes**
5. Risk: **LOW**

### 11.4 What Success Looks Like

**After implementation**:
```bash
# User can now do this:
mcpi add my-server --scope user-internal
mcpi disable my-server
# Server still in ~/.claude.json, marked as disabled in tracking file

mcpi list --scope user-internal
# Shows: my-server (DISABLED)

mcpi enable my-server
# Tracking file updated, server now enabled

# All existing functionality preserved
# No breaking changes
# Consistent with user-global scope behavior
```

---

## 12. Appendix: Code References

### 12.1 Key Files

**Core Implementation**:
- `src/mcpi/clients/claude_code.py` - Scope definitions (lines 62-199)
- `src/mcpi/clients/enable_disable_handlers.py` - Handler implementations
- `src/mcpi/clients/disabled_tracker.py` - Tracking file management
- `src/mcpi/clients/protocols.py` - Protocol definitions
- `src/mcpi/clients/base.py` - Base plugin interface
- `src/mcpi/clients/manager.py` - Manager enable/disable methods

**CLI**:
- `src/mcpi/cli.py` - disable command (lines 1174-1229)
- `src/mcpi/cli.py` - enable command (lines 1116-1172)

**Tests**:
- `tests/test_enable_disable_bugs.py` - Comprehensive test suite (752 lines)
- `tests/test_harness.py` - Test harness for scope testing

**Documentation**:
- `CLAUDE.md` - Project documentation
- `.agent_planning/BUG-FIX-PLAN-ENABLE-DISABLE.md` - Previous bug fix plan
- `.agent_planning/SUMMARY-ENABLE-DISABLE-BUGS.md` - Bug summary

### 12.2 Scope Configuration Locations

```python
# src/mcpi/clients/claude_code.py

# Line 74-89: project-mcp (no enable/disable)
# Line 91-111: project-local (ArrayBased)
# Line 113-133: user-local (ArrayBased)
# Line 135-160: user-global (FileTracked)
# Line 162-179: user-internal (None) ← CHANGE HERE
# Line 181-199: user-mcp (no enable/disable)
```

### 12.3 Handler Implementation References

**ArrayBasedEnableDisableHandler**:
- File: `src/mcpi/clients/enable_disable_handlers.py` (lines 10-127)
- Used by: project-local, user-local
- Mechanism: In-config arrays

**FileTrackedEnableDisableHandler**:
- File: `src/mcpi/clients/enable_disable_handlers.py` (lines 129-177)
- Used by: user-global
- Mechanism: Separate tracking file
- **WILL BE USED BY**: user-internal (after implementation)

**DisabledServersTracker**:
- File: `src/mcpi/clients/disabled_tracker.py` (lines 13-119)
- Manages tracking file I/O
- JSON format: Simple array of server IDs

---

## 13. Next Steps

1. **Get user confirmation**: Does Option D (FileTracked handler for user-internal) solve their problem?
2. **Implement if approved**: Follow implementation plan (Section 7.2)
3. **Test thoroughly**: Run test suite + manual verification
4. **Update docs**: Ensure users understand scope differences
5. **Ship**: Deploy change with clear release notes

**Estimated Timeline**: Same day (2-3 hours total work)

**Confidence**: HIGH (reusing proven pattern, low risk, clear implementation path)
