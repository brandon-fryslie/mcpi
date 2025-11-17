# Implementation Plan: User-Global MCP Server Disable/Enable Fix

**Generated**: 2025-11-16-15:55:08
**Source STATUS**: STATUS-2025-11-16-USER-GLOBAL-DISABLE-CRITICAL-BUG.md
**Spec Version**: CLAUDE.md (lines 406-410)
**Priority**: P0 - CRITICAL BLOCKER
**Type**: BUG FIX (Complete redesign of broken feature)

---

## Executive Summary

**Current State**: The user-global and user-internal MCP server disable/enable functionality is **completely broken**. It uses a tracking file approach that has **zero effect** on Claude Code's actual behavior.

**Problem**:
- MCPI tracks disabled servers in `~/.claude/.mcpi-disabled-servers.json`
- Claude Code **never reads this file**
- Result: Servers marked "disabled" by MCPI still run in Claude Code
- Validation: `claude mcp list` shows servers as connected that MCPI claims are disabled

**Root Cause**: Implementation uses wrong approach (ID tracking) instead of required approach (config file movement).

**Required Fix**: Implement **config file movement** approach as originally specified:
1. Create `~/.claude/.disabled-mcp.json` to store disabled server **configurations**
2. `mcpi disable`: **MOVE** config from `settings.json` **TO** `.disabled-mcp.json`
3. `mcpi enable`: **MOVE** config from `.disabled-mcp.json` **TO** `settings.json`
4. Result: Claude only sees servers in `settings.json` (enabled servers)

**Validation Requirement**: After fix, `claude mcp list` MUST NOT show disabled servers.

**Effort Estimate**: 6-8 hours (implementation + comprehensive testing)

---

## Problem Analysis

### Current Implementation (BROKEN)

**Files**:
- `src/mcpi/clients/disabled_tracker.py` - Tracks server IDs only
- `src/mcpi/clients/enable_disable_handlers.py` - `FileTrackedEnableDisableHandler`
- Tracking files: `~/.claude/.mcpi-disabled-servers.json`, `~/.claude/.mcpi-disabled-servers-internal.json`

**What It Does**:
```python
# Disable operation (WRONG)
disable_server("frida-mcp"):
    1. Add "frida-mcp" to ~/.claude/.mcpi-disabled-servers-internal.json
    2. Server config STAYS in ~/.claude.json
    3. MCPI shows server as DISABLED
    4. Claude Code STILL LOADS the server (config still in .claude.json)
```

**Evidence of Failure**:
```bash
# After "mcpi disable frida-mcp"
$ cat ~/.claude/.mcpi-disabled-servers-internal.json
["frida-mcp"]

$ cat ~/.claude.json | jq '.mcpServers | keys[]'
frida-mcp  # ← STILL HERE (Claude loads it)

$ claude mcp list | grep frida-mcp
frida-mcp: frida-mcp - ✓ Connected  # ← STILL CONNECTED

$ mcpi list --scope user-internal | grep frida-mcp
│ frida-mcp │ DISABLED │  # ← MCPI LIES (server is actually enabled)
```

### Required Implementation (CORRECT)

**New Approach**: Move configuration objects between files

**Files Involved**:
- **User-global scope**:
  - Active: `~/.claude/settings.json` (enabled servers)
  - Disabled: `~/.claude/.disabled-mcp.json` (disabled servers)
- **User-internal scope**:
  - Active: `~/.claude.json` (enabled servers)
  - Disabled: `~/.claude/.disabled-internal.json` (disabled servers)

**How It Works**:
```python
# Disable operation (CORRECT)
disable_server("frida-mcp"):
    1. Read ~/.claude.json
    2. Extract config: {"command": "frida-mcp", ...}
    3. Write config to ~/.claude/.disabled-internal.json under "mcpServers.frida-mcp"
    4. DELETE "frida-mcp" from ~/.claude.json
    5. Result: Claude doesn't see frida-mcp (not in .claude.json)

# Enable operation (CORRECT)
enable_server("frida-mcp"):
    1. Read ~/.claude/.disabled-internal.json
    2. Extract config: {"command": "frida-mcp", ...}
    3. Write config to ~/.claude.json under "mcpServers.frida-mcp"
    4. DELETE "frida-mcp" from ~/.claude/.disabled-internal.json
    5. Result: Claude sees frida-mcp (now in .claude.json)
```

**Why This Works**:
- Claude Code only reads servers from official config files (`settings.json`, `.claude.json`)
- Servers in `.disabled-*.json` are invisible to Claude
- No need for Claude to check tracking files
- Actual file-based isolation achieves the goal

---

## Architecture Changes

### 1. New Handler: `ConfigFileMovingHandler`

**Location**: `src/mcpi/clients/enable_disable_handlers.py`

**Purpose**: Enable/disable by moving server configurations between active and disabled files

**Interface**:
```python
class ConfigFileMovingHandler:
    """Enable/disable by moving configs between active and disabled files.

    This handler solves the user-global/user-internal disable problem by
    physically moving server configurations between two files:
    - Active file: Where Claude Code reads servers (e.g., settings.json)
    - Disabled file: Where MCPI stores disabled servers (e.g., .disabled-mcp.json)

    Claude Code only sees servers in the active file, so moving a server to
    the disabled file effectively disables it without needing Claude to check
    any tracking files.
    """

    def __init__(
        self,
        active_path: Path,      # e.g., ~/.claude/settings.json
        disabled_path: Path,    # e.g., ~/.claude/.disabled-mcp.json
        reader: ConfigReader,
        writer: ConfigWriter,
    ):
        """Initialize the config-moving handler."""
        self.active_path = active_path
        self.disabled_path = disabled_path
        self.reader = reader
        self.writer = writer

    def is_disabled(self, server_id: str) -> bool:
        """Check if server is in the disabled file."""
        # Read disabled file
        # Check if server_id exists in mcpServers
        # Return true if found

    def disable_server(self, server_id: str) -> bool:
        """Move server config from active to disabled file."""
        # 1. Read active file
        # 2. Extract server config (if not found, return False)
        # 3. Read disabled file (or create if missing)
        # 4. Add server config to disabled file
        # 5. Remove server from active file
        # 6. Write both files atomically
        # 7. Return True on success

    def enable_server(self, server_id: str) -> bool:
        """Move server config from disabled to active file."""
        # 1. Read disabled file
        # 2. Extract server config (if not found, return False)
        # 3. Read active file
        # 4. Add server config to active file
        # 5. Remove server from disabled file
        # 6. Write both files atomically
        # 7. Return True on success

    def list_disabled_servers(self) -> List[str]:
        """Get list of all disabled servers (from disabled file)."""
        # Read disabled file
        # Return list of server IDs in mcpServers
```

### 2. Updated `list_servers()` Method

**Location**: `src/mcpi/clients/claude_code.py`

**Change**: Must also read disabled file to show **combined** list

**Current Behavior**:
```python
def list_servers(self, scope: Optional[str] = None):
    # Only reads active file (settings.json)
    # Returns servers found in active file
```

**New Behavior**:
```python
def list_servers(self, scope: Optional[str] = None):
    # 1. Read servers from active file (state = ENABLED)
    # 2. Read servers from disabled file (state = DISABLED)
    # 3. Return COMBINED list with correct states
```

**Why**: User requirement states `mcpi list` must show **all** servers (enabled + disabled).

### 3. File Structure

**User-Global Scope** (`~/.claude/` directory):
```
~/.claude/
├── settings.json              # Claude reads this (enabled servers)
└── .disabled-mcp.json         # MCPI managed (disabled servers)
```

**Format** (both files use same structure):
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package"],
      "type": "stdio"
    }
  }
}
```

**User-Internal Scope** (`~/.claude.json` + disabled file):
```
~/
├── .claude.json               # Claude reads this (enabled servers)
└── .claude/
    └── .disabled-internal.json  # MCPI managed (disabled servers)
```

### 4. Updated Scope Initialization

**Location**: `src/mcpi/clients/claude_code.py:_initialize_scopes()`

**Change**: Replace `FileTrackedEnableDisableHandler` with `ConfigFileMovingHandler`

**Before (BROKEN)**:
```python
# User-global scope (line 142-164)
scopes["user-global"] = FileBasedScope(
    # ...
    enable_disable_handler=FileTrackedEnableDisableHandler(
        DisabledServersTracker(disabled_tracker_path)
    ),
)

# User-internal scope (line 167-190)
scopes["user-internal"] = FileBasedScope(
    # ...
    enable_disable_handler=FileTrackedEnableDisableHandler(
        DisabledServersTracker(user_internal_disabled_tracker_path)
    ),
)
```

**After (CORRECT)**:
```python
# User-global scope
user_global_path = self._get_scope_path(
    "user-global", Path.home() / ".claude" / "settings.json"
)
user_global_disabled_path = self._get_scope_path(
    "user-global-disabled", Path.home() / ".claude" / ".disabled-mcp.json"
)
scopes["user-global"] = FileBasedScope(
    config=ScopeConfig(
        name="user-global",
        description="User-global Claude settings (~/.claude/settings.json)",
        priority=4,
        path=user_global_path,
        is_user_level=True,
    ),
    reader=json_reader,
    writer=json_writer,
    validator=YAMLSchemaValidator(),
    schema_path=schemas_dir / "claude-settings-schema.yaml",
    enable_disable_handler=ConfigFileMovingHandler(
        active_path=user_global_path,
        disabled_path=user_global_disabled_path,
        reader=json_reader,
        writer=json_writer,
    ),
)

# User-internal scope
user_internal_path = self._get_scope_path(
    "user-internal", Path.home() / ".claude.json"
)
user_internal_disabled_path = self._get_scope_path(
    "user-internal-disabled",
    Path.home() / ".claude" / ".disabled-internal.json",
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
    enable_disable_handler=ConfigFileMovingHandler(
        active_path=user_internal_path,
        disabled_path=user_internal_disabled_path,
        reader=json_reader,
        writer=json_writer,
    ),
)
```

### 5. Backward Compatibility (Migration)

**Problem**: Existing users may have servers in old tracking files

**Solution**: Auto-migrate on first use

**Migration Logic**:
```python
def _migrate_tracking_file_to_disabled_file(self) -> None:
    """Migrate from old tracking file format to new disabled config file format.

    Old format: ~/.claude/.mcpi-disabled-servers.json = ["server-id", ...]
    New format: ~/.claude/.disabled-mcp.json = {"mcpServers": {"server-id": {...}}}

    This runs once on first disable/enable operation after upgrade.
    """
    # 1. Check if old tracking file exists
    # 2. If yes, read server IDs
    # 3. For each server ID:
    #    a. Read config from active file
    #    b. Write to new disabled file
    #    c. Remove from active file
    # 4. Rename old tracking file to .migrated (for backup)
    # 5. Log migration completion
```

**Where to run**: First call to `disable_server()` or `enable_server()` checks for migration

**Safety**: Keep old file as `.mcpi-disabled-servers.json.migrated` for rollback

---

## Implementation Steps

### Phase 1: Core Handler Implementation (2-3 hours)

**Task 1.1: Create `ConfigFileMovingHandler` class**
- **File**: `src/mcpi/clients/enable_disable_handlers.py`
- **What**: Add new handler class (see architecture section)
- **Methods**:
  - `__init__(active_path, disabled_path, reader, writer)`
  - `is_disabled(server_id) -> bool`
  - `disable_server(server_id) -> bool`
  - `enable_server(server_id) -> bool`
  - `list_disabled_servers() -> List[str]`
  - `_read_file(path) -> dict`
  - `_write_file(path, data) -> None`
- **Error Handling**:
  - Handle missing files (create with empty structure)
  - Handle JSON parse errors (return False)
  - Handle permission errors (return False)
  - Handle missing server (return False)
- **Edge Cases**:
  - Server already in target file (idempotent)
  - Server not in source file (return False)
  - Empty files (create mcpServers key)
  - Concurrent access (atomic writes)

**Task 1.2: Update `ClaudeCodePlugin._initialize_scopes()`**
- **File**: `src/mcpi/clients/claude_code.py`
- **What**: Replace `FileTrackedEnableDisableHandler` with `ConfigFileMovingHandler`
- **Lines**: ~142-190
- **Changes**:
  - User-global scope: Use new handler
  - User-internal scope: Use new handler
  - Update disabled file paths (new names)

**Task 1.3: Update `ClaudeCodePlugin.list_servers()`**
- **File**: `src/mcpi/clients/claude_code.py`
- **What**: Read both active and disabled files
- **Logic**:
  ```python
  def list_servers(self, scope: Optional[str] = None):
      servers = {}

      for scope_name, handler in scope_handlers.items():
          # 1. Read active file servers (state = ENABLED)
          active_servers = handler.get_servers()
          for server_id, config in active_servers.items():
              servers[f"{self.name}:{scope_name}:{server_id}"] = ServerInfo(
                  id=server_id,
                  client=self.name,
                  scope=scope_name,
                  config=config,
                  state=ServerState.ENABLED,
                  priority=handler.config.priority,
              )

          # 2. Read disabled file servers (state = DISABLED)
          if handler.enable_disable_handler:
              if hasattr(handler.enable_disable_handler, 'list_disabled_servers'):
                  disabled = handler.enable_disable_handler.list_disabled_servers()
                  for server_id in disabled:
                      # Read config from disabled file
                      config = handler.enable_disable_handler._read_disabled_config(server_id)
                      servers[f"{self.name}:{scope_name}:{server_id}"] = ServerInfo(
                          id=server_id,
                          client=self.name,
                          scope=scope_name,
                          config=config,
                          state=ServerState.DISABLED,
                          priority=handler.config.priority,
                      )

      return servers
  ```

**Task 1.4: Backward compatibility migration**
- **File**: `src/mcpi/clients/enable_disable_handlers.py`
- **What**: Add migration logic to `ConfigFileMovingHandler.__init__()`
- **When**: Check on initialization if old tracking file exists
- **What to migrate**:
  - Old file: `~/.claude/.mcpi-disabled-servers.json`
  - New file: `~/.claude/.disabled-mcp.json`
  - Process: Read IDs from old file, extract configs from active file, write to disabled file
- **Safety**: Rename old file to `.migrated` (don't delete)

### Phase 2: Comprehensive Testing (3-4 hours)

**Task 2.1: Unit Tests for `ConfigFileMovingHandler`**
- **File**: `tests/test_config_file_moving_handler.py` (NEW)
- **Coverage**: 100% of handler methods
- **Test Cases**:
  1. `test_disable_moves_config_to_disabled_file`
     - Setup: Server in active file
     - Action: Call `disable_server()`
     - Assert: Config moved to disabled file, removed from active file
  2. `test_enable_moves_config_to_active_file`
     - Setup: Server in disabled file
     - Action: Call `enable_server()`
     - Assert: Config moved to active file, removed from disabled file
  3. `test_is_disabled_checks_disabled_file`
     - Setup: Server in disabled file
     - Action: Call `is_disabled()`
     - Assert: Returns True
  4. `test_is_disabled_checks_active_file`
     - Setup: Server in active file only
     - Action: Call `is_disabled()`
     - Assert: Returns False
  5. `test_disable_idempotent`
     - Setup: Server already in disabled file
     - Action: Call `disable_server()` twice
     - Assert: No error, state unchanged
  6. `test_enable_idempotent`
     - Setup: Server already in active file
     - Action: Call `enable_server()` twice
     - Assert: No error, state unchanged
  7. `test_disable_missing_server_returns_false`
     - Setup: Server doesn't exist
     - Action: Call `disable_server()`
     - Assert: Returns False, files unchanged
  8. `test_enable_missing_server_returns_false`
     - Setup: Server doesn't exist in disabled file
     - Action: Call `enable_server()`
     - Assert: Returns False, files unchanged
  9. `test_creates_disabled_file_if_missing`
     - Setup: No disabled file exists
     - Action: Call `disable_server()`
     - Assert: Disabled file created with correct structure
  10. `test_handles_empty_files`
      - Setup: Empty active and disabled files
      - Action: Call `disable_server()`
      - Assert: Handles gracefully or creates structure

**Task 2.2: Integration Tests (Scope-Level)**
- **File**: `tests/test_enable_disable_integration.py` (UPDATE existing or NEW)
- **Test Cases**:
  1. `test_user_global_disable_removes_from_settings_json`
     - Setup: Server in `~/.claude/settings.json`
     - Action: `mcpi disable <server> --scope user-global`
     - Assert: Server NOT in `settings.json`, IS in `.disabled-mcp.json`
  2. `test_user_global_enable_restores_to_settings_json`
     - Setup: Server in `.disabled-mcp.json`
     - Action: `mcpi enable <server> --scope user-global`
     - Assert: Server IS in `settings.json`, NOT in `.disabled-mcp.json`
  3. `test_user_internal_disable_removes_from_claude_json`
     - Setup: Server in `~/.claude.json`
     - Action: `mcpi disable <server> --scope user-internal`
     - Assert: Server NOT in `.claude.json`, IS in `.disabled-internal.json`
  4. `test_user_internal_enable_restores_to_claude_json`
     - Setup: Server in `.disabled-internal.json`
     - Action: `mcpi enable <server> --scope user-internal`
     - Assert: Server IS in `.claude.json`, NOT in `.disabled-internal.json`
  5. `test_list_shows_combined_enabled_and_disabled`
     - Setup: 2 servers in active, 1 server in disabled
     - Action: `mcpi list`
     - Assert: Shows 3 servers total, correct states

**Task 2.3: End-to-End Validation Tests**
- **File**: `tests/test_e2e_claude_integration.py` (NEW)
- **Purpose**: Verify Claude Code actually respects disabled state
- **CRITICAL**: These tests validate REAL functionality, not just MCPI state
- **Test Cases**:
  1. `test_disabled_server_not_in_claude_mcp_list`
     - Setup: Server enabled in Claude
     - Verify: `claude mcp list` shows server
     - Action: `mcpi disable <server>`
     - Verify: `claude mcp list` does NOT show server (critical!)
     - Cleanup: `mcpi enable <server>`
  2. `test_enabled_server_appears_in_claude_mcp_list`
     - Setup: Server disabled
     - Verify: `claude mcp list` does NOT show server
     - Action: `mcpi enable <server>`
     - Verify: `claude mcp list` shows server (critical!)
  3. `test_disable_enable_roundtrip_works`
     - Setup: Server enabled
     - Action: Disable, verify gone, enable, verify back
     - Assert: All state transitions work correctly
  4. `test_multiple_servers_disable_independently`
     - Setup: 3 servers enabled
     - Action: Disable server1, disable server3
     - Verify: `claude mcp list` shows only server2
     - Action: Enable server1
     - Verify: `claude mcp list` shows server1 and server2

**Implementation Notes for E2E Tests**:
- **Challenge**: Need to run `claude mcp list` as subprocess
- **Solution**: Use `subprocess.run()` to execute Claude CLI
- **Validation**: Parse output to verify server presence/absence
- **Safety**: Use test harness with path overrides to avoid touching real user files
- **Alternative**: Mock/simulate Claude's file reading behavior in test

**Task 2.4: Backward Compatibility Tests**
- **File**: `tests/test_migration_tracking_to_config.py` (NEW)
- **Purpose**: Verify migration from old tracking file format
- **Test Cases**:
  1. `test_migrates_old_tracking_file_on_first_use`
     - Setup: Old tracking file with server IDs, servers in active file
     - Action: Call `disable_server()` on different server
     - Assert: Old tracking file migrated, servers in disabled file
  2. `test_migration_preserves_server_configs`
     - Setup: Old tracking file with 3 servers
     - Action: Trigger migration
     - Assert: All 3 server configs in disabled file, configs intact
  3. `test_migration_keeps_backup`
     - Setup: Old tracking file
     - Action: Trigger migration
     - Assert: Old file renamed to `.migrated`, still exists

### Phase 3: Manual Validation (1-2 hours)

**Task 3.1: Create manual test checklist**
- **File**: `.agent_planning/MANUAL_TEST_CHECKLIST_DISABLE_FIX.md`
- **Content**: Step-by-step procedures for human verification
- **Procedures**:
  1. Fresh install test
  2. Upgrade migration test
  3. Multi-server test
  4. Edge case test (empty files, missing files, etc.)

**Task 3.2: Execute manual tests**
- **Tester**: Developer or QA
- **Environment**: Real Claude Code installation (not test harness)
- **Critical Validation**: Run `claude mcp list` after each disable/enable
- **Success Criteria**: All checklist items pass

**Task 3.3: Document validation results**
- **File**: `.agent_planning/MANUAL_TEST_RESULTS_DISABLE_FIX.md`
- **Content**: Pass/fail for each test, screenshots, logs
- **Required**: Evidence that `claude mcp list` respects disabled state

### Phase 4: Code Cleanup (1 hour)

**Task 4.1: Remove old implementation**
- **Files to modify/remove**:
  - `src/mcpi/clients/disabled_tracker.py` - DELETE (replaced by ConfigFileMovingHandler)
  - `src/mcpi/clients/enable_disable_handlers.py` - REMOVE `FileTrackedEnableDisableHandler` class
- **Reason**: Dead code removal (old tracker approach doesn't work)
- **Safety**: Keep one release cycle before deleting (mark as deprecated first)

**Task 4.2: Update imports**
- **Files affected**: Any file importing `DisabledServersTracker` or `FileTrackedEnableDisableHandler`
- **Action**: Remove unused imports
- **Verification**: Run `ruff check` to find unused imports

**Task 4.3: Update documentation**
- **Files**:
  - `CLAUDE.md` - Update disable/enable mechanism description
  - `README.md` - Update examples if affected
  - `.agent_planning/STATUS-*.md` - Create new status file with fix verification
- **Content**: Document new approach, migration notes, validation results

---

## Testing Strategy

### Test Coverage Targets

| Component | Unit Tests | Integration Tests | E2E Tests | Coverage Target |
|-----------|-----------|-------------------|-----------|-----------------|
| `ConfigFileMovingHandler` | 10 tests | 5 tests | 4 tests | 100% |
| `ClaudeCodePlugin` updates | N/A | 5 tests | 4 tests | 100% |
| Migration logic | 3 tests | 2 tests | 1 test | 100% |
| **TOTAL** | **13 tests** | **12 tests** | **9 tests** | **100%** |

### Un-gameable Test Requirements

**Critical Principle**: Tests must verify REAL functionality, not just internal state

**Anti-Patterns to Avoid**:
- ❌ Only checking MCPI's internal state
- ❌ Only verifying file contents without validating Claude behavior
- ❌ Mocking everything so tests can't fail
- ❌ Tests that pass when feature is broken

**Required Patterns**:
- ✅ E2E tests run `claude mcp list` and parse output
- ✅ Integration tests verify actual file changes (read files, not mocks)
- ✅ Tests fail if Claude still loads disabled servers
- ✅ Manual validation checklist required before ship

### Test Execution Order

1. **Unit Tests First** (fast, isolated)
   - Run: `pytest tests/test_config_file_moving_handler.py -v`
   - Must pass 100% before proceeding

2. **Integration Tests Second** (file I/O)
   - Run: `pytest tests/test_enable_disable_integration.py -v`
   - Must pass 100% before proceeding

3. **E2E Tests Third** (subprocess calls)
   - Run: `pytest tests/test_e2e_claude_integration.py -v`
   - Must pass 100% before manual testing

4. **Manual Validation Last** (human verification)
   - Follow checklist in `.agent_planning/MANUAL_TEST_CHECKLIST_DISABLE_FIX.md`
   - Document results
   - Required before merge

### Success Criteria

**All of these must be true**:
- ✅ All unit tests pass (13/13)
- ✅ All integration tests pass (12/12)
- ✅ All E2E tests pass (9/9)
- ✅ Manual validation checklist complete (100%)
- ✅ `claude mcp list` verification: Disabled servers do NOT appear
- ✅ `claude mcp list` verification: Enabled servers DO appear
- ✅ Code coverage 100% for new code
- ✅ No regression in other scopes (project-mcp, project-local, user-local)
- ✅ Migration from old tracking file works

---

## Edge Cases and Error Handling

### Edge Case 1: Server in Both Files

**Scenario**: Server config exists in both active and disabled files (corrupt state)

**Cause**: Crash during disable/enable operation, manual file editing

**Detection**: Check both files before operations

**Resolution**:
```python
def _resolve_dual_presence(self, server_id: str) -> None:
    """Resolve server existing in both active and disabled files.

    Resolution strategy: Active file wins (server is considered enabled).
    """
    # 1. Read both files
    # 2. If server in both:
    #    a. Remove from disabled file
    #    b. Log warning
    #    c. Return True (enabled state)
```

### Edge Case 2: Missing Server

**Scenario**: User tries to disable/enable server that doesn't exist

**Expected Behavior**: Return `OperationResult(success=False, message="Server not found")`

**Implementation**:
```python
def disable_server(self, server_id: str) -> bool:
    # 1. Check if server in active file
    # 2. If not found, return False
    # 3. Otherwise, proceed with move
```

### Edge Case 3: Corrupted JSON

**Scenario**: Config file has invalid JSON syntax

**Expected Behavior**: Return `OperationResult(success=False, message="Invalid JSON")`

**Implementation**:
```python
def _read_file(self, path: Path) -> Optional[dict]:
    try:
        with path.open("r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {path}")
        return None
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return None
```

### Edge Case 4: Permission Denied

**Scenario**: User doesn't have write permission to config files

**Expected Behavior**: Return `OperationResult(success=False, message="Permission denied")`

**Implementation**:
```python
def _write_file(self, path: Path, data: dict) -> bool:
    try:
        with path.open("w") as f:
            json.dump(data, f, indent=2)
        return True
    except PermissionError:
        logger.error(f"Permission denied: {path}")
        return False
    except Exception as e:
        logger.error(f"Error writing {path}: {e}")
        return False
```

### Edge Case 5: Concurrent Access

**Scenario**: Two `mcpi` processes try to modify same file simultaneously

**Expected Behavior**: Use file locking or atomic writes

**Implementation**:
```python
import tempfile
import shutil

def _atomic_write(self, path: Path, data: dict) -> bool:
    """Write file atomically to prevent corruption from concurrent access."""
    # 1. Write to temporary file
    # 2. Atomically rename to target path
    # 3. This prevents partial writes
    try:
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            dir=path.parent,
            delete=False,
            suffix=".tmp"
        )
        json.dump(data, tmp, indent=2)
        tmp.close()
        shutil.move(tmp.name, path)
        return True
    except Exception as e:
        logger.error(f"Atomic write failed for {path}: {e}")
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
        return False
```

### Edge Case 6: Empty Files

**Scenario**: Config file exists but is empty or missing `mcpServers` key

**Expected Behavior**: Create structure if missing

**Implementation**:
```python
def _ensure_structure(self, data: dict) -> dict:
    """Ensure config has proper mcpServers structure."""
    if data is None:
        data = {}
    if "mcpServers" not in data:
        data["mcpServers"] = {}
    return data
```

---

## Risks and Mitigation

### Risk 1: Data Loss During Migration

**Risk**: Migration from old tracking file fails, users lose disabled server list

**Impact**: HIGH - Users lose track of which servers they disabled

**Probability**: MEDIUM

**Mitigation**:
1. Keep old tracking file as `.migrated` backup
2. Log all migration actions
3. Provide rollback command: `mcpi migrate rollback`
4. Test migration extensively before ship

**Rollback Plan**:
```bash
# If migration goes wrong
mcpi migrate rollback
# Restores: .mcpi-disabled-servers.json from .migrated backup
# Reverts: .disabled-mcp.json changes
```

### Risk 2: File Corruption During Config Move

**Risk**: Crash during move operation leaves files in inconsistent state

**Impact**: HIGH - Server configs lost or duplicated

**Probability**: LOW (with atomic writes)

**Mitigation**:
1. Use atomic writes (write to temp, then rename)
2. Validate JSON before writing
3. Read-after-write verification
4. Provide repair command: `mcpi doctor`

**Doctor Command**:
```bash
# Detect and fix inconsistencies
mcpi doctor
# Checks:
# - Servers in both active and disabled files (remove from disabled)
# - Corrupted JSON (attempt repair or warn)
# - Missing keys (add default structure)
```

### Risk 3: Claude Code Doesn't Respect Disabled File

**Risk**: Even with config movement, Claude still loads disabled servers

**Impact**: CRITICAL - Feature still doesn't work

**Probability**: LOW (Claude only reads active file)

**Mitigation**:
1. **MANDATORY**: E2E test verifies `claude mcp list` output
2. **MANDATORY**: Manual validation before ship
3. Document verification procedure
4. Provide user validation command

**Verification Command**:
```bash
# User can validate themselves
mcpi validate-disable <server-id>
# Steps:
# 1. Run 'claude mcp list'
# 2. Check if <server-id> appears
# 3. Compare with MCPI state
# 4. Report discrepancies
```

### Risk 4: Breaking Existing User Workflows

**Risk**: Users have scripts/automation that rely on old tracking file

**Impact**: MEDIUM - User scripts break

**Probability**: LOW (tracking file was internal implementation detail)

**Mitigation**:
1. Keep old files as `.migrated` for one release
2. Log deprecation warnings
3. Provide migration guide in CHANGELOG
4. Version bump to v3.0 (breaking change)

**Communication**:
```markdown
# CHANGELOG v3.0

## BREAKING CHANGES

### Disable/Enable Mechanism Redesign

The user-global and user-internal disable mechanism has been completely redesigned to fix a critical bug where disabled servers were still loaded by Claude Code.

**What Changed**:
- Old: Tracking file `~/.claude/.mcpi-disabled-servers.json`
- New: Disabled config file `~/.claude/.disabled-mcp.json`

**Migration**: Automatic on first use. Old tracking file backed up as `.migrated`.

**Impact**: If you have scripts parsing `.mcpi-disabled-servers.json`, update them to read `.disabled-mcp.json` (same format as settings.json).
```

### Risk 5: Test Suite False Positives

**Risk**: Tests pass but feature still broken (like current state)

**Impact**: CRITICAL - Ship broken feature again

**Probability**: MEDIUM (without E2E tests)

**Mitigation**:
1. **MANDATORY**: E2E tests that run `claude mcp list`
2. **MANDATORY**: Manual validation checklist
3. Review test coverage for gaming
4. Require demonstration video of feature working

**Quality Gate**:
- At least 3 E2E tests that call `claude mcp list` and verify output
- Manual validation documented with screenshots
- Code review focusing on test quality

---

## Timeline Estimate

### Breakdown by Phase

| Phase | Tasks | Estimated Time | Dependencies |
|-------|-------|---------------|-------------|
| **Phase 1: Core Implementation** | Handler + scope updates | 2-3 hours | None |
| **Phase 2: Comprehensive Testing** | Unit + Integration + E2E | 3-4 hours | Phase 1 complete |
| **Phase 3: Manual Validation** | Checklist execution | 1-2 hours | Phase 2 complete |
| **Phase 4: Code Cleanup** | Remove old code, docs | 1 hour | Phase 3 complete |
| **TOTAL** | | **7-10 hours** | Sequential |

### Critical Path

```
Phase 1 → Phase 2 → Phase 3 → Phase 4
(3h)      (4h)       (2h)       (1h)
└─────────────────────────────────┘
         7-10 hours total
```

### Parallel Work Opportunities

**CAN'T parallelize**: All phases are sequential (each depends on previous)

**CAN parallelize within Phase 2**:
- Unit tests + Integration tests (run independently)
- E2E test creation + Manual test checklist creation

**Recommendation**: Execute in order, don't parallelize (high risk of rework)

### Daily Breakdown (Assuming 1 developer)

**Day 1** (5-6 hours):
- Morning: Phase 1 (Core implementation)
- Afternoon: Phase 2 (Unit + Integration tests)

**Day 2** (2-4 hours):
- Morning: Phase 2 continued (E2E tests)
- Afternoon: Phase 3 (Manual validation)
- Evening: Phase 4 (Cleanup and docs)

**Total**: 1.5 days (assuming 6-hour work days)

---

## Dependencies

### Internal Dependencies

| Component | Depends On | Reason |
|-----------|-----------|--------|
| `ConfigFileMovingHandler` | `ConfigReader`, `ConfigWriter` protocols | File I/O abstraction |
| E2E tests | `claude` CLI installed | Need to run `claude mcp list` |
| Manual validation | Real Claude Code instance | Verify actual behavior |
| Migration logic | Old tracking files | Backward compatibility |

### External Dependencies

| Dependency | Purpose | Risk Level |
|------------|---------|------------|
| Claude Code CLI | E2E validation | LOW (required tool) |
| File system access | Read/write config files | LOW (standard) |
| JSON library | Parse/write JSON | NONE (stdlib) |
| Path library | File path manipulation | NONE (stdlib) |

### Test Harness Dependencies

| Test Type | Harness Requirement |
|-----------|-------------------|
| Unit tests | `MCPTestHarness` with path overrides |
| Integration tests | `MCPTestHarness` with temp directories |
| E2E tests | Real `~/.claude/` directory OR mocked `claude` CLI |

**Safety for E2E Tests**: Use `MCPI_TEST_MODE=1` and path overrides to avoid touching real user files

---

## Validation Criteria (CRITICAL)

### Automated Test Pass Criteria

**All tests must pass 100%**:
- ✅ Unit tests: 13/13 passing
- ✅ Integration tests: 12/12 passing
- ✅ E2E tests: 9/9 passing
- ✅ Existing tests: No regressions
- ✅ Code coverage: 100% for new code

### Manual Validation Pass Criteria

**Human verification required before merge**:

1. ✅ **Test 1: Disable removes from `claude mcp list`**
   - Start: `claude mcp list | grep test-server` shows server
   - Action: `mcpi disable test-server --scope user-global`
   - Verify: `claude mcp list | grep test-server` shows nothing
   - Result: PASS/FAIL

2. ✅ **Test 2: Enable adds to `claude mcp list`**
   - Start: `claude mcp list | grep test-server` shows nothing
   - Action: `mcpi enable test-server --scope user-global`
   - Verify: `claude mcp list | grep test-server` shows server
   - Result: PASS/FAIL

3. ✅ **Test 3: MCPI list shows combined state**
   - Setup: 2 enabled servers, 1 disabled server
   - Action: `mcpi list --scope user-global`
   - Verify: Shows 3 servers, correct states
   - Result: PASS/FAIL

4. ✅ **Test 4: Migration preserves configs**
   - Setup: Old tracking file with 2 servers
   - Action: First disable operation
   - Verify: Servers moved to `.disabled-mcp.json` with full configs
   - Result: PASS/FAIL

**Documentation Required**:
- Screenshots of each test
- Terminal output logs
- Pass/fail for each test
- Any issues encountered

### Success Definition (SHIP CRITERIA)

**ALL of the following must be TRUE before merging**:

- ✅ All automated tests pass (34/34)
- ✅ All manual validation tests pass (4/4)
- ✅ E2E tests verify `claude mcp list` respects disable
- ✅ Migration tested with real tracking files
- ✅ Code review complete (focus on test quality)
- ✅ Documentation updated (CLAUDE.md, README.md)
- ✅ CHANGELOG entry created
- ✅ No regressions in other scopes

**If ANY of these fail**: DO NOT MERGE, fix the issue first

---

## Rollback Plan

### If Critical Bug Found After Ship

**Scenario**: v3.0 ships, users report disabled servers still loading

**Immediate Response** (< 1 hour):
1. Revert `ConfigFileMovingHandler` changes
2. Restore `FileTrackedEnableDisableHandler` (even though broken)
3. Ship hotfix v3.0.1 with revert
4. Notify users via CHANGELOG

**Why Revert**:
- Known broken state better than unknown broken state
- Users expect old behavior (even if broken)
- Time to investigate without pressure

**Investigation** (< 1 day):
1. Reproduce issue in test environment
2. Identify root cause
3. Create fix
4. Add test that catches the bug
5. Manual validation of fix

**Fix Release** (< 2 days):
1. Ship v3.0.2 with fix
2. Document what went wrong
3. Apologize to users

### If Migration Corrupts User Data

**Scenario**: Migration deletes or corrupts server configs

**Immediate Response** (< 30 minutes):
1. Ship emergency hotfix that disables migration
2. Provide recovery script:
   ```bash
   # Restore from .migrated backup
   cp ~/.claude/.mcpi-disabled-servers.json.migrated \
      ~/.claude/.mcpi-disabled-servers.json
   ```

**Recovery Assistance**:
1. Create GitHub issue template for data loss reports
2. Manually help affected users recover
3. Document recovery procedure

**Prevention**:
- Migration creates `.migrated` backup (recoverable)
- Migration logs all actions (audit trail)
- Extensive migration testing before ship

---

## Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | 100% | `pytest --cov` |
| Test pass rate | 100% | `pytest` exit code |
| E2E validation | 4/4 pass | Manual checklist |
| Code review approval | 1+ approver | GitHub PR |
| Zero regressions | 0 | Run full test suite |
| Performance | < 100ms per op | Time disable/enable operations |

### Qualitative Metrics

| Metric | Target | Validation |
|--------|--------|-----------|
| User trust | Feature works as documented | `claude mcp list` verification |
| Code quality | Clean, maintainable | Code review feedback |
| Documentation | Complete, accurate | Review by non-author |
| Error handling | Graceful failure | Test edge cases |

### Post-Ship Validation

**1 Week After Ship**:
- Monitor GitHub issues for bug reports
- Check user feedback (if public project)
- Review error logs (if telemetry exists)

**Success Definition**: Zero bug reports related to disable/enable functionality

---

## Open Questions

### Question 1: E2E Test Implementation Strategy

**Question**: Should E2E tests run `claude mcp list` as subprocess or mock Claude's behavior?

**Option A - Real Claude CLI**:
- Pros: Tests real behavior, catches integration issues
- Cons: Requires Claude Code installed, slower, flaky if Claude changes

**Option B - Mock Claude's File Reading**:
- Pros: Fast, reliable, no external dependency
- Cons: Doesn't test actual Claude behavior (could miss bugs)

**Recommendation**: **Option A** (real Claude CLI) with fallback to Option B if Claude not installed

**Rationale**: Critical bug was missed because tests didn't verify Claude's behavior. Real E2E tests are essential.

### Question 2: Migration Timing

**Question**: When should migration from old tracking file run?

**Option A - On Plugin Initialization**:
- Pros: Automatic, user doesn't need to do anything
- Cons: Runs on every `mcpi` command (slow)

**Option B - On First Disable/Enable Operation**:
- Pros: Only runs when needed
- Cons: User might not notice migration happened

**Option C - Explicit Command (`mcpi migrate`)**:
- Pros: User control, explicit
- Cons: User might forget, old format persists

**Recommendation**: **Option B** (on first operation) with logging

**Rationale**: Automatic but lazy, balances UX and performance

### Question 3: Disabled File Format

**Question**: Should disabled file use same format as active file or different format?

**Option A - Same Format** (recommended):
```json
{
  "mcpServers": {
    "server-id": {"command": "...", ...}
  }
}
```
- Pros: Consistent, easy to understand, can copy-paste between files
- Cons: None

**Option B - Different Format**:
```json
{
  "disabled": {
    "server-id": {"command": "...", ...}
  }
}
```
- Pros: Clear distinction
- Cons: Inconsistent, confusing

**Recommendation**: **Option A** (same format as active file)

**Rationale**: Consistency reduces cognitive load, easier for users to manually edit if needed

---

## Appendices

### Appendix A: File Structure Diagram

```
User-Global Scope:
~/.claude/
├── settings.json           # Claude reads this (enabled servers)
│   └── mcpServers
│       ├── server-1        # ENABLED
│       └── server-2        # ENABLED
└── .disabled-mcp.json      # MCPI manages this (disabled servers)
    └── mcpServers
        └── server-3        # DISABLED

User-Internal Scope:
~/
├── .claude.json            # Claude reads this (enabled servers)
│   └── mcpServers
│       ├── server-4        # ENABLED
│       └── server-5        # ENABLED
└── .claude/
    └── .disabled-internal.json  # MCPI manages this (disabled servers)
        └── mcpServers
            └── server-6    # DISABLED
```

### Appendix B: State Transition Diagram

```
ENABLED (in active file)
    |
    | mcpi disable
    ↓
DISABLED (in disabled file)
    |
    | mcpi enable
    ↓
ENABLED (in active file)
```

### Appendix C: Error Handling Matrix

| Error Condition | Detection | Recovery | User Message |
|----------------|-----------|----------|-------------|
| Missing server | Check active + disabled files | Return False | "Server not found" |
| Corrupted JSON | JSON parse exception | Return None | "Invalid JSON in config file" |
| Permission denied | OS permission error | Return False | "Permission denied writing to config" |
| Server in both files | Check both files | Remove from disabled | "Resolved duplicate server entry" |
| Empty file | Read returns empty | Create structure | "Created config structure" |
| Concurrent write | File lock timeout | Retry 3 times | "Config file busy, please retry" |

### Appendix D: Testing Checklist

**Before Merge**:
- [ ] All unit tests pass (13/13)
- [ ] All integration tests pass (12/12)
- [ ] All E2E tests pass (9/9)
- [ ] Manual validation complete (4/4)
- [ ] Code review approved
- [ ] Documentation updated
- [ ] CHANGELOG entry added
- [ ] No test regressions
- [ ] Migration tested
- [ ] Edge cases tested

**Before Ship**:
- [ ] Final manual validation on clean environment
- [ ] Version bumped to v3.0
- [ ] Git tag created
- [ ] Release notes written
- [ ] Rollback plan documented

---

## Summary

**This plan provides**:
1. ✅ Complete architecture redesign (config file movement)
2. ✅ Comprehensive testing strategy (34 tests, 100% coverage)
3. ✅ E2E validation of Claude Code behavior
4. ✅ Edge case handling and error recovery
5. ✅ Backward compatibility migration
6. ✅ Risk assessment and mitigation
7. ✅ Clear success criteria and validation

**Implementation Effort**: 7-10 hours (1.5 work days)

**Critical Success Factor**: E2E tests that verify `claude mcp list` output

**Ship Criteria**: ALL tests pass + manual validation complete + zero regressions

**Next Steps**:
1. Review this plan
2. Get approval to proceed
3. Execute Phase 1 (core implementation)
4. Execute Phase 2 (testing)
5. Execute Phase 3 (validation)
6. Execute Phase 4 (cleanup)
7. Ship v3.0

---

**Plan Generated**: 2025-11-16-15:55:08
**Plan Author**: Claude Code (Implementation Planner)
**Status**: READY FOR REVIEW
**Approval Required**: YES (critical bug fix)
