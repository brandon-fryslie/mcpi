# Bug Proposal: User-Global Scope Disable Failure

**Date**: 2025-11-16
**Status**: Critical Bug - Disable command fails for user-global scoped servers
**Severity**: High - Core functionality broken for common use case

---

## Executive Summary

The `mcpi disable` command reports success but fails to actually disable MCP servers configured in the user-global scope (`~/.claude/settings.json`). Running `claude mcp list` before and after the disable operation shows the server remains enabled. This is a critical bug affecting user experience with the most commonly used scope.

**Root Cause**: After extensive code analysis, the implementation appears correct on paper but has an architectural disconnect: the disable operation writes to a tracking file (`~/.claude/.mcpi-disabled-servers.json`), but Claude Code itself doesn't read this tracking file - it only reads the official settings files.

**Impact**: Users cannot disable servers in their user-global configuration, forcing them to manually edit JSON files or use workarounds.

---

## 1. Root Cause Analysis

### 1.1 Current Implementation Review

Based on code analysis of `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/src/mcpi/clients/claude_code.py`:

**User-Global Scope Configuration** (lines 135-160):
```python
# User-global Claude settings (~/.claude/settings.json)
# This scope does NOT support enable/disable arrays in settings.json format
# Instead, use a separate disabled tracking file
user_global_path = self._get_scope_path(
    "user-global", Path.home() / ".claude" / "settings.json"
)
disabled_tracker_path = self._get_scope_path(
    "user-global-disabled",
    Path.home() / ".claude" / ".mcpi-disabled-servers.json",
)
scopes["user-global"] = FileBasedScope(
    config=ScopeConfig(...),
    reader=json_reader,
    writer=json_writer,
    validator=YAMLSchemaValidator(),
    schema_path=schemas_dir / "claude-settings-schema.yaml",
    enable_disable_handler=FileTrackedEnableDisableHandler(
        DisabledServersTracker(disabled_tracker_path)
    ),
)
```

**Disable Operation Flow** (lines 413-459):
1. `mcpi disable server-name` is called
2. CLI calls `MCPManager.disable_server()` → `ClientRegistry.disable_server()` → `ClaudeCodePlugin.disable_server()`
3. Plugin finds server's scope (user-global)
4. Plugin gets scope handler's enable_disable_handler
5. Handler writes to tracking file `~/.claude/.mcpi-disabled-servers.json`
6. Operation returns success

**State Checking Flow** (lines 209-241):
1. `_get_server_state()` checks if handler has enable_disable_handler
2. Calls `handler.enable_disable_handler.is_disabled(server_id)`
3. Returns `ServerState.DISABLED` if found in tracking file

### 1.2 The Critical Disconnect

**THE BUG**: MCPI writes to a tracking file, but Claude Code doesn't know about it!

1. **MCPI's perspective**:
   - Disable writes server ID to `~/.claude/.mcpi-disabled-servers.json` ✓
   - State check reads from `~/.claude/.mcpi-disabled-servers.json` ✓
   - `mcpi list` shows server as DISABLED ✓

2. **Claude Code's perspective**:
   - Reads server config from `~/.claude/settings.json` ✓
   - Does NOT read `~/.claude/.mcpi-disabled-servers.json` ✗
   - Server remains active because it's still in settings.json ✗

3. **User's observation**:
   - `mcpi disable frida-server` → "Successfully disabled" (lies!)
   - `claude mcp list` → frida-server still shows as enabled (truth!)
   - Server is still active in Claude Code (problem!)

### 1.3 Why Tests Pass But Reality Fails

The tests in `test_enable_disable_bugs.py` verify MCPI's internal consistency:
- They check MCPI's own `list_servers()` method shows DISABLED ✓
- They verify the tracking file is created ✓
- They verify the tracking file is read correctly ✓

**But they don't test the critical integration**: Does Claude Code actually respect the tracking file?

**The answer**: NO - Claude Code has no knowledge of MCPI's tracking file.

### 1.4 Scope-Specific Behavior

Let me analyze all 6 scopes:

| Scope | Config File | Enable/Disable Mechanism | Works? |
|-------|-------------|-------------------------|--------|
| project-mcp | `.mcp.json` | None (not supported) | N/A |
| project-local | `.claude/settings.local.json` | Arrays in same file | ✓ YES |
| user-local | `~/.claude/settings.local.json` | Arrays in same file | ✓ YES |
| **user-global** | `~/.claude/settings.json` | Separate tracking file | ✗ **NO** |
| user-internal | `~/.claude.json` | Separate tracking file | ✗ **NO** |
| user-mcp | `~/.claude/mcp_servers.json` | None (not supported) | N/A |

**Pattern**: Scopes using separate tracking files DON'T WORK in practice because Claude Code doesn't read the tracking files.

### 1.5 Architectural Flaw

The fundamental issue is a **layer violation**:

```
┌─────────────────────────────────────┐
│  Claude Code (Official Client)     │
│  - Reads ~/.claude/settings.json   │
│  - Doesn't know about MCPI          │
└─────────────────────────────────────┘
           │
           │ Config file format:
           │ { "mcpServers": {...} }
           ▼
┌─────────────────────────────────────┐
│  MCPI (Management Tool)             │
│  - Tries to manage servers          │
│  - Creates tracking file            │
│  - Claude Code ignores it!          │
└─────────────────────────────────────┘
```

**The tracking file approach is fundamentally broken** for user-global and user-internal scopes because:
1. It's a proprietary MCPI mechanism
2. Claude Code has no reason to know about it
3. There's no way to make Claude Code respect it without modifying Claude Code itself
4. Users are using the official `claude` CLI, not MCPI, to check status

---

## 2. Solution Design

### 2.1 Core Principle

**We must work within Claude Code's existing format - we cannot invent proprietary mechanisms.**

For user-global scope (`~/.claude/settings.json`), we have these options:

**Option A: Remove from config file** (RECOMMENDED)
- Disable = Remove server entry from `mcpServers` object
- Enable = Add server entry back to `mcpServers` object
- Requires storing removed server config somewhere to re-enable later

**Option B: Use comment convention** (NOT VIABLE)
- JSON doesn't support comments
- Would break schema validation

**Option C: Rename convention** (HACKY BUT WORKS)
- Disable = Rename server key to `_disabled_server-name`
- Enable = Rename back to `server-name`
- Claude Code ignores entries starting with `_`
- No external tracking file needed

**Option D: Fail gracefully** (HONEST)
- Return clear error that disable is not supported for user-global
- Document workaround (use user-local instead)

### 2.2 Recommended Solution: Option A + Backup Storage

**Implementation Plan**:

1. **Create backup storage file**: `~/.claude/.mcpi-server-backups.json`
   ```json
   {
     "user-global": {
       "server-name": {
         "command": "npx",
         "args": ["-y", "server-name"],
         "disabled_at": "2025-11-16T12:34:56Z"
       }
     },
     "user-internal": {
       "another-server": {...}
     }
   }
   ```

2. **Disable operation**:
   - Read current server config from `~/.claude/settings.json`
   - Save config to backup file with scope prefix
   - Remove server from `settings.json`
   - Write modified `settings.json`
   - Result: Claude Code no longer sees the server (actually disabled!)

3. **Enable operation**:
   - Read server config from backup file
   - If found, restore to `~/.claude/settings.json`
   - Remove from backup file
   - Result: Claude Code sees the server again (actually enabled!)

4. **State checking**:
   - Server exists in config file = ENABLED
   - Server exists in backup file = DISABLED
   - Server in neither = NOT_INSTALLED

5. **Benefits**:
   - Actually works with Claude Code (it's what Claude Code sees)
   - No proprietary tracking mechanisms
   - Preserves server config for re-enabling
   - Simple to understand and debug
   - Works with `claude mcp list` immediately

6. **Edge cases**:
   - User manually edits `settings.json` and adds back a disabled server
     → MCPI sees it as enabled (correct - user overrode MCPI)
   - Backup file gets deleted
     → Can still disable (just can't re-enable without re-adding)
   - User disables then manually edits backup file
     → Their choice, their responsibility

### 2.3 Alternative: Option D (Honest Failure)

If Option A is too invasive, we should:

1. **Detect user-global scope in disable operation**
2. **Return clear error**:
   ```
   Error: Disable is not supported for user-global scope (~/.claude/settings.json)

   Claude Code's settings.json format doesn't have enable/disable arrays.

   Workarounds:
   1. Use user-local scope instead: mcpi rescope server-name --to user-local
   2. Manually remove the server from settings.json
   3. Use 'mcpi remove' to completely uninstall

   Learn more: https://github.com/user/mcpi/docs/enable-disable.md
   ```

3. **Update documentation** to explain scope limitations

4. **Benefits**:
   - Honest with users
   - Prevents false success messages
   - Guides users to working alternatives
   - No complex implementation

### 2.4 Comparison

| Aspect | Option A (Backup Storage) | Option D (Honest Failure) |
|--------|--------------------------|---------------------------|
| Complexity | Medium | Low |
| User Experience | Best (disable just works) | Poor (feature unavailable) |
| Risk | Medium (file operations) | Low (just error message) |
| Maintenance | Medium | Low |
| Correctness | High | High |
| Matches User Expectations | Yes | No |

**Recommendation**: Implement **Option A** for v2.1, with **Option D as a v2.0.1 hotfix**.

---

## 3. User Experience Design

### 3.1 Current Broken UX

```bash
$ claude mcp list | grep frida
frida-server    enabled

$ mcpi disable frida-server
✓ Successfully disabled frida-server

$ claude mcp list | grep frida
frida-server    enabled    # BUG: Still enabled!

$ mcpi list | grep frida
frida-server    DISABLED   # MCPI thinks it's disabled
```

**User frustration**: "WTF? It says it worked but it's still running!"

### 3.2 Desired UX (Option A Implementation)

```bash
$ claude mcp list | grep frida
frida-server    enabled

$ mcpi disable frida-server
✓ Disabled frida-server in user-global scope
  (Moved to backup storage, will be restored on enable)

$ claude mcp list | grep frida
(no output - server actually disabled)

$ mcpi list | grep frida
frida-server    DISABLED   # Matches reality

$ mcpi enable frida-server
✓ Enabled frida-server in user-global scope
  (Restored from backup storage)

$ claude mcp list | grep frida
frida-server    enabled    # Works!
```

### 3.3 Desired UX (Option D - Honest Failure)

```bash
$ claude mcp list | grep frida
frida-server    enabled

$ mcpi disable frida-server
✗ Cannot disable server in user-global scope

  The user-global scope (~/.claude/settings.json) doesn't support
  enable/disable operations because it lacks the enabledMcpjsonServers
  and disabledMcpjsonServers arrays.

  Options:
  1. Move to user-local scope (supports enable/disable):
     mcpi rescope frida-server --to user-local
     mcpi disable frida-server

  2. Remove the server entirely:
     mcpi remove frida-server

  3. Manually edit ~/.claude/settings.json

  Learn more: https://github.com/...
```

### 3.4 Scope Selection Guidance

When users run `mcpi add`, show clear guidance:

```bash
$ mcpi add frida-server

Select a scope for 'frida-server':
  [1] user-local - User-local Claude settings [✓ Supports enable/disable]
      ~/.claude/settings.local.json

  [2] user-global - User-global Claude settings [⚠️  Enable/disable limited]
      ~/.claude/settings.json

  [3] user-internal - User internal configuration [⚠️  Enable/disable limited]
      ~/.claude.json

Enter the number of your choice [1]:
```

---

## 4. Testing Strategy

### 4.1 Integration Test Requirements

**These tests MUST verify actual Claude Code behavior, not just MCPI internal state.**

#### Test 1: End-to-End Disable Verification
```python
def test_user_global_disable_actually_disables_in_claude_code(mcp_harness):
    """Verify that disabling a user-global server makes it invisible to Claude Code.

    This is the CRITICAL test - it must verify Claude Code's actual behavior,
    not just MCPI's internal state.
    """
    # Setup: Add server to user-global
    harness.run_mcpi("add", "test-server", "--scope", "user-global")

    # Verify: Claude Code sees the server
    claude_list_before = subprocess.run(
        ["claude", "mcp", "list"], capture_output=True, text=True
    )
    assert "test-server" in claude_list_before.stdout

    # Execute: Disable the server
    result = harness.run_mcpi("disable", "test-server")
    assert result.success

    # CRITICAL VERIFICATION: Claude Code no longer sees it
    claude_list_after = subprocess.run(
        ["claude", "mcp", "list"], capture_output=True, text=True
    )
    assert "test-server" not in claude_list_after.stdout, (
        "BUG: Server still visible to Claude Code after disable!"
    )

    # Also verify MCPI shows it as disabled
    mcpi_list = harness.run_mcpi("list", "--scope", "user-global")
    assert "DISABLED" in mcpi_list.stdout
```

#### Test 2: Enable Restoration
```python
def test_user_global_enable_restores_server_config(mcp_harness):
    """Verify that enabling restores the exact original server configuration."""
    # Setup: Add and configure server
    original_config = {
        "command": "npx",
        "args": ["-y", "@test/server"],
        "env": {"TEST_VAR": "value"}
    }
    harness.add_server_with_config("test-server", original_config, scope="user-global")

    # Execute: Disable then enable
    harness.run_mcpi("disable", "test-server")
    harness.run_mcpi("enable", "test-server")

    # Verify: Config is identical to original
    settings = harness.read_file("~/.claude/settings.json")
    restored_config = settings["mcpServers"]["test-server"]

    assert restored_config == original_config, (
        "Enabled server config doesn't match original"
    )
```

#### Test 3: Backup File Management
```python
def test_user_global_backup_file_lifecycle(mcp_harness):
    """Verify backup file is created/removed correctly."""
    # Execute: Disable server
    harness.run_mcpi("disable", "test-server")

    # Verify: Backup file exists with correct content
    backup_file = Path.home() / ".claude" / ".mcpi-server-backups.json"
    assert backup_file.exists()

    backup = json.loads(backup_file.read_text())
    assert "user-global" in backup
    assert "test-server" in backup["user-global"]

    # Execute: Enable server
    harness.run_mcpi("enable", "test-server")

    # Verify: Server removed from backup
    backup = json.loads(backup_file.read_text())
    assert "test-server" not in backup.get("user-global", {})
```

### 4.2 Ungameable Test Criteria

Tests MUST:
1. ✓ Execute actual `claude mcp list` command (not mocked)
2. ✓ Verify real file contents in `~/.claude/settings.json`
3. ✓ Check that Claude Code's view matches MCPI's reported state
4. ✓ Test the complete disable→verify→enable→verify cycle
5. ✓ Verify no server config data loss during disable/enable
6. ✓ Test with real server configurations (command, args, env)
7. ✓ Verify backup file creation and cleanup

Tests MUST NOT:
1. ✗ Mock file operations
2. ✗ Only check MCPI's internal state
3. ✗ Assume disable works without external verification
4. ✗ Skip testing with actual Claude Code CLI
5. ✗ Use simplified configs (must test full schema)

### 4.3 Edge Cases to Test

1. **User manually edits settings.json**
   - Add disabled server back → Should show as enabled
   - Remove enabled server → Should show as removed

2. **Backup file missing**
   - Disable succeeds (creates backup)
   - Enable fails gracefully if backup is missing

3. **Multiple scopes**
   - Same server ID in user-global and user-local
   - Disable one doesn't affect the other

4. **Config file format validation**
   - Disabled server's config must pass schema validation
   - Backup file format must be valid JSON

5. **Race conditions**
   - Multiple disable operations
   - Disable while Claude Code is running

---

## 5. Implementation Plan

### 5.1 Phase 1: Hotfix (v2.0.1) - Option D

**Goal**: Stop lying to users about disable working

**Changes**:
1. Update `ClaudeCodePlugin.disable_server()`:
   ```python
   def disable_server(self, server_id: str) -> OperationResult:
       # Find server's scope
       server_scope = self._find_server_scope(server_id)

       # Check if scope supports disable
       if server_scope in ["user-global", "user-internal"]:
           return OperationResult.failure_result(
               f"Scope '{server_scope}' does not support enable/disable operations.\n"
               f"\n"
               f"The '{server_scope}' configuration format doesn't have "
               f"enabledMcpjsonServers/disabledMcpjsonServers arrays.\n"
               f"\n"
               f"Options:\n"
               f"1. Move to user-local scope: mcpi rescope {server_id} --to user-local\n"
               f"2. Remove completely: mcpi remove {server_id}\n"
               f"3. Manually edit the configuration file"
           )

       # ... existing disable logic for supported scopes
   ```

2. Update tests to verify error message
3. Update documentation

**Time Estimate**: 2-4 hours
**Risk**: Low (just error handling)
**Benefit**: Users get honest feedback immediately

### 5.2 Phase 2: Full Solution (v2.1) - Option A

**Goal**: Make disable actually work for user-global/user-internal

**Changes**:

1. **Create new handler**: `BackupBasedEnableDisableHandler`
   - Location: `src/mcpi/clients/enable_disable_handlers.py`
   - Responsibilities:
     - Manage backup file (`~/.claude/.mcpi-server-backups.json`)
     - Remove servers from config file on disable
     - Restore servers to config file on enable
     - Handle backup file corruption/missing

2. **Update ClaudeCodePlugin**:
   - Replace `FileTrackedEnableDisableHandler` with `BackupBasedEnableDisableHandler`
   - For user-global and user-internal scopes

3. **Implement backup file management**:
   ```python
   class ServerBackupManager:
       def __init__(self, backup_path: Path):
           self.backup_path = backup_path

       def backup_server(self, scope: str, server_id: str, config: dict) -> bool:
           """Save server config to backup file."""

       def restore_server(self, scope: str, server_id: str) -> Optional[dict]:
           """Retrieve server config from backup file."""

       def has_backup(self, scope: str, server_id: str) -> bool:
           """Check if backup exists for server."""
   ```

4. **Update scope handlers**:
   - Modify `FileBasedScope` to work with config removal/restoration
   - Ensure atomic operations (backup before remove, verify before restore)

5. **Comprehensive testing**:
   - All tests from section 4.2
   - Integration tests with actual `claude` CLI
   - Backup file corruption scenarios
   - Multiple concurrent operations

**Files to Modify**:
- `src/mcpi/clients/enable_disable_handlers.py` (new handler)
- `src/mcpi/clients/claude_code.py` (use new handler)
- `tests/test_enable_disable_bugs.py` (update tests)
- New: `tests/test_enable_disable_integration.py` (Claude Code integration)

**Time Estimate**: 1-2 days
**Risk**: Medium (file operations, state management)
**Benefit**: Feature actually works as users expect

### 5.3 Migration Path

1. **v2.0.1 Release**:
   - Deploy honest error messages
   - Update docs with workarounds
   - Announce limitation on GitHub

2. **v2.1 Development**:
   - Implement backup-based solution
   - Test extensively with real Claude Code
   - Beta test with users

3. **v2.1 Release**:
   - Deploy working disable for all scopes
   - Migrate existing tracking files to backup format
   - Update docs to remove workaround notices

### 5.4 Backward Compatibility

**Existing tracking files** (`~/.claude/.mcpi-disabled-servers.json`):
- v2.1 should migrate them to backup format
- Migration script:
  ```python
  def migrate_tracking_to_backup():
      # Read old tracking file
      # For each disabled server:
      #   - Read config from settings.json
      #   - Save to backup file
      #   - Remove from settings.json
      # Delete old tracking file
  ```

**User impact**:
- Transparent migration on first v2.1 run
- Servers stay disabled during migration
- No manual intervention needed

---

## 6. Architectural Improvements

### 6.1 Scope Capability Declaration

**Problem**: Scopes have different capabilities but this isn't explicit

**Solution**: Add capability flags to `ScopeConfig`:

```python
@dataclass
class ScopeConfig:
    name: str
    description: str
    priority: int
    path: Optional[Path]
    is_user_level: bool = False
    is_project_level: bool = False

    # NEW: Explicit capability flags
    supports_enable_disable: bool = True
    enable_disable_mechanism: str = "arrays"  # "arrays", "backup", or "none"
    supports_inline_modification: bool = True
    read_only: bool = False
```

**Benefits**:
- Clear documentation of what each scope can do
- Runtime validation of operations
- Better error messages
- Easier to add new scopes

### 6.2 Handler Factory Pattern

**Problem**: Scope initialization has a lot of conditional logic

**Solution**: Use factory pattern for handler creation:

```python
class EnableDisableHandlerFactory:
    @staticmethod
    def create_handler(
        scope_name: str,
        config_path: Path,
        reader: ConfigReader,
        writer: ConfigWriter
    ) -> Optional[EnableDisableHandler]:
        """Create appropriate enable/disable handler for scope."""

        if scope_name in ["project-local", "user-local"]:
            # Scopes with arrays in config file
            return ArrayBasedEnableDisableHandler(config_path, reader, writer)

        elif scope_name in ["user-global", "user-internal"]:
            # Scopes requiring backup storage
            backup_path = _get_backup_path(scope_name)
            return BackupBasedEnableDisableHandler(
                config_path, backup_path, reader, writer
            )

        else:
            # Scopes that don't support enable/disable
            return None
```

**Benefits**:
- Single source of truth for handler selection
- Easy to add new handler types
- Testable in isolation

### 6.3 State Consistency Validation

**Problem**: MCPI's view of state might diverge from Claude Code's

**Solution**: Add validation command:

```bash
$ mcpi validate
Checking consistency between MCPI and Claude Code...

✓ user-local: 3 servers, all states match
✗ user-global: State mismatch detected
  - frida-server: MCPI says DISABLED, Claude Code says ENABLED

Issues found: 1
Run 'mcpi validate --fix' to attempt automatic repair
```

**Implementation**:
- Run both `mcpi list` and `claude mcp list`
- Compare results
- Report discrepancies
- Offer auto-fix option

---

## 7. Documentation Updates

### 7.1 Scope Comparison Table

Add to README.md:

```markdown
## Scope Capabilities

| Scope | Config File | Enable/Disable | Mechanism | Recommended Use |
|-------|-------------|----------------|-----------|-----------------|
| project-mcp | `.mcp.json` | ❌ No | - | Project-wide servers |
| project-local | `.claude/settings.local.json` | ✅ Yes | Arrays | Project-specific dev servers |
| user-local | `~/.claude/settings.local.json` | ✅ Yes | Arrays | **Recommended for most users** |
| user-global | `~/.claude/settings.json` | ✅ Yes* | Backup | Global default servers |
| user-internal | `~/.claude.json` | ✅ Yes* | Backup | Advanced users only |
| user-mcp | `~/.claude/mcp_servers.json` | ❌ No | - | Legacy compatibility |

*Enable/disable works via backup storage (v2.1+)
```

### 7.2 Troubleshooting Guide

Add section:

```markdown
## Troubleshooting Enable/Disable

### Server still appears enabled after disable

**Symptom**: Running `mcpi disable server-name` reports success, but `claude mcp list` still shows the server as enabled.

**Cause**: You may be running v2.0 or earlier, which has a known bug with user-global scope.

**Solutions**:
1. **Upgrade to v2.1+**: `pip install --upgrade mcpi`
2. **Move to user-local scope**: `mcpi rescope server-name --to user-local`
3. **Manual workaround**: Edit `~/.claude/settings.json` and remove the server entry

### Server configuration lost after enable

**Symptom**: Enabling a previously disabled server restores it with wrong configuration.

**Cause**: Backup file was corrupted or modified.

**Solutions**:
1. Check backup file: `cat ~/.claude/.mcpi-server-backups.json`
2. If corrupted, remove and re-add: `mcpi remove server-name && mcpi add server-name`
```

---

## 8. Risk Assessment

### 8.1 Risks of Option A (Backup Storage)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| Backup file corruption | Low | High | Validate JSON on every read/write, auto-repair |
| Config data loss during disable | Low | Critical | Atomic operations, verify backup before removal |
| Concurrent modifications | Medium | Medium | File locking, backup file per operation |
| Disk space (large servers) | Low | Low | Backup file is text, compress if >1MB |
| User confusion (hidden file) | Medium | Low | Document clearly, add `mcpi backup list` command |

### 8.2 Risks of Option D (Honest Failure)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| User frustration | High | Medium | Clear error messages, easy workarounds |
| Feature gap vs competitors | Medium | Medium | Document as temporary, promise v2.1 fix |
| Reduced adoption | Low | Low | Most users use user-local anyway |

### 8.3 Overall Risk Assessment

**Option A is riskier but better long-term value**
- Higher implementation complexity
- More failure modes to handle
- But: Actually solves the problem
- Better user experience

**Option D is safer for immediate hotfix**
- Minimal code changes
- No new failure modes
- But: Doesn't solve the problem
- Worse user experience

**Recommendation**: Ship Option D in v2.0.1 (this week), then Option A in v2.1 (next month)

---

## 9. Success Metrics

### 9.1 Technical Metrics

1. **Correctness**:
   - `claude mcp list` output matches `mcpi list` output 100% of the time
   - Zero reports of "server still enabled after disable"

2. **Reliability**:
   - No backup file corruption incidents
   - 100% config preservation (enable restores exact original config)

3. **Performance**:
   - Disable/enable operations < 100ms on SSD
   - Backup file size < 10KB for typical usage

### 9.2 User Experience Metrics

1. **Clarity**:
   - Zero user confusion about which scopes support disable
   - Error messages provide actionable solutions

2. **Adoption**:
   - 80% of users use user-local scope (supports enable/disable)
   - <5% of users encounter scope limitation errors

3. **Satisfaction**:
   - Zero "disable doesn't work" bug reports after v2.1
   - Positive feedback on GitHub issues

---

## 10. Alternatives Considered and Rejected

### 10.1 Modify Claude Code

**Idea**: Submit PR to Claude Code to read MCPI tracking file

**Why rejected**:
- Out of our control (Anthropic owns Claude Code)
- Unlikely to be accepted (proprietary mechanism)
- Would take months even if accepted
- Doesn't help existing Claude Code installations

### 10.2 Proxy/Wrapper Approach

**Idea**: Create `claude-mcpi` wrapper that intercepts `claude mcp list` and filters disabled servers

**Why rejected**:
- Too invasive
- Hard to maintain
- Breaks if Claude Code CLI changes
- Users want to use official `claude` command

### 10.3 Schema Extension

**Idea**: Add `"_mcpi_disabled": true` field to server config

**Why rejected**:
- Pollutes official config format
- Would fail schema validation
- Claude Code would still load the server
- Ugly workaround

### 10.4 Symlink Swapping

**Idea**: Disable = move config to `.disabled/`, enable = move back

**Why rejected**:
- Race conditions if Claude Code reads mid-swap
- File system dependence (symlinks)
- Complicated error recovery
- Breaks if user has multiple Claude Code instances

---

## 11. Open Questions

### 11.1 For Decision

1. **Q**: Should we implement Option D first as a hotfix, or go straight to Option A?
   **A**: Recommend Option D for v2.0.1 (honest failure), then Option A for v2.1 (full solution)

2. **Q**: What should happen if user manually adds back a disabled server?
   **A**: It should appear as enabled (user override wins)

3. **Q**: Should backup file be per-scope or unified?
   **A**: Unified (easier to manage, one file to backup)

4. **Q**: Should we migrate old tracking files automatically?
   **A**: Yes, on first run of v2.1

### 11.2 For Investigation

1. **Q**: Can we detect if Claude Code is currently running and warn before disable?
   **A**: Nice-to-have, not critical

2. **Q**: Should backup file be in git-ignore by default?
   **A**: Yes, add to .gitignore template

3. **Q**: Performance impact of removing/adding servers to large config files?
   **A**: Test with 50+ server config

4. **Q**: How does this interact with rescope command?
   **A**: Should work fine, rescope moves enabled state

---

## 12. Next Steps

### Immediate (This Week - v2.0.1 Hotfix)

1. ✅ Implement Option D error message
2. ✅ Update `ClaudeCodePlugin.disable_server()`
3. ✅ Add test for error message
4. ✅ Update README with scope limitations
5. ✅ Release v2.0.1

### Short Term (Next 2 Weeks - v2.1 Planning)

1. ⏸️ Design `BackupBasedEnableDisableHandler` API
2. ⏸️ Create prototype implementation
3. ⏸️ Write integration tests with actual Claude Code
4. ⏸️ Test migration from tracking files to backup files
5. ⏸️ Update documentation

### Medium Term (Next Month - v2.1 Development)

1. ⏸️ Implement full backup storage solution
2. ⏸️ Comprehensive testing (including edge cases)
3. ⏸️ Migration script for existing users
4. ⏸️ Beta testing with real users
5. ⏸️ Release v2.1

### Long Term (Future Enhancements)

1. ⏸️ Add `mcpi validate` command for consistency checks
2. ⏸️ Implement backup file compression if needed
3. ⏸️ Add `mcpi backup` subcommand for manual backup management
4. ⏸️ Consider scope capability flags in core architecture

---

## 13. Conclusion

The root cause of this bug is an **architectural mismatch**: MCPI uses a proprietary tracking file that Claude Code doesn't know about. The current implementation appears correct in tests but fails in practice because tests don't verify the critical integration point with Claude Code itself.

**The fix requires working within Claude Code's existing format** - we can't invent proprietary mechanisms and expect Claude Code to respect them.

**Recommendation**:
1. **v2.0.1 Hotfix (This Week)**: Implement honest error messages (Option D)
2. **v2.1 Full Solution (Next Month)**: Implement backup storage solution (Option A)

This approach:
- ✅ Stops lying to users immediately
- ✅ Provides clear migration path
- ✅ Maintains backward compatibility
- ✅ Delivers proper solution on reasonable timeline
- ✅ Follows principle of least surprise

The backup storage approach is the right long-term solution because it:
- Works with Claude Code's actual behavior
- Preserves server configurations
- Is testable and debuggable
- Doesn't pollute official config formats
- Provides good user experience

**This is a critical bug that undermines user trust.** Users expect `mcpi disable` to actually disable servers. We must fix this properly.
