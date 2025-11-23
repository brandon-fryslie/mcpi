# Implementation Plan: Fix Project-MCP Approval Bug

**Generated**: 2025-11-16 17:37:14
**Source STATUS**: STATUS-2025-11-16-PROJECT-MCP-APPROVAL-BUG.md
**Spec Reference**: CLAUDE.md § User-Global Disable Mechanism (lines 406-467)
**Severity**: CRITICAL
**Priority**: P0 (IMMEDIATE)

---

## Executive Summary

**Bug Description**: Servers in the `project-mcp` scope show as `ENABLED` in `mcpi list` but do NOT appear in `claude mcp list` output because MCPI does not check Claude Code's approval mechanism.

**Root Cause**: MCPI's `InlineEnableDisableHandler` for project-mcp scope only checks for inline `"disabled": true` field but does NOT check if the server is approved via the `enabledMcpjsonServers` array in `.claude/settings.local.json`.

**Impact**: Users cannot use servers that MCPI reports as enabled, breaking the fundamental contract that "ENABLED servers should work in Claude Code."

**Solution**: Create `ApprovalRequiredEnableDisableHandler` that checks both inline disabled field AND approval arrays in `.claude/settings.local.json`.

**Estimated Effort**: 6-9 hours (full implementation + comprehensive testing + validation)

**Confidence Level**: VERY HIGH (10/10) - Clear root cause, clear solution, clear validation path

---

## Implementation Breakdown

### Phase 1: Handler Implementation (2-3 hours)

#### ITEM-1: Create ApprovalRequiredEnableDisableHandler Class

**File**: `src/mcpi/clients/enable_disable_handlers.py`
**Effort**: 1.5 hours
**Dependencies**: None

**Description**: Create new handler class that implements approval-aware state detection for project-mcp scope.

**Implementation Details**:

```python
class ApprovalRequiredEnableDisableHandler:
    """Enable/disable handler for .mcp.json files requiring approval.

    This handler is used for project-mcp scope where servers require
    explicit approval via enabledMcpjsonServers in .claude/settings.local.json.

    State detection logic:
    1. If server has "disabled": true → DISABLED
    2. If server in disabledMcpjsonServers → DISABLED
    3. If server in enabledMcpjsonServers → ENABLED
    4. If server in neither array → DISABLED (not approved)
    """

    def __init__(
        self,
        mcp_json_path: Path,
        settings_local_path: Path,
        reader: ConfigReader,
        writer: ConfigWriter
    ) -> None:
        """Initialize the approval-required handler."""
        self.mcp_json_path = mcp_json_path
        self.settings_local_path = settings_local_path
        self.reader = reader
        self.writer = writer

    def is_disabled(self, server_id: str) -> bool:
        """Check if a server is disabled or not approved.

        Returns True if:
        - Server has inline "disabled": true field
        - Server is in disabledMcpjsonServers array
        - Server is NOT in enabledMcpjsonServers array (not approved)
        """
        # Check inline disabled field (highest priority)
        if self.mcp_json_path.exists():
            try:
                data = self.reader.read(self.mcp_json_path)
                servers = data.get("mcpServers", {})
                server_config = servers.get(server_id, {})
                if server_config.get("disabled") is True:
                    return True
            except Exception:
                pass

        # Check approval arrays in settings.local.json
        if self.settings_local_path.exists():
            try:
                settings = self.reader.read(self.settings_local_path)

                # If in disabledMcpjsonServers → disabled
                disabled_servers = settings.get("disabledMcpjsonServers", [])
                if server_id in disabled_servers:
                    return True

                # If in enabledMcpjsonServers → enabled (not disabled)
                enabled_servers = settings.get("enabledMcpjsonServers", [])
                if server_id in enabled_servers:
                    return False

                # If in neither array → not approved → treat as disabled
                return True
            except Exception:
                pass

        # Default: If no settings file, server is not approved
        return True

    def disable_server(self, server_id: str) -> bool:
        """Disable a server by adding to disabledMcpjsonServers.

        Also removes from enabledMcpjsonServers if present.
        """
        try:
            # Read current settings
            if self.settings_local_path.exists():
                settings = self.reader.read(self.settings_local_path)
            else:
                settings = {}

            # Initialize arrays if needed
            enabled_servers = settings.get("enabledMcpjsonServers", [])
            disabled_servers = settings.get("disabledMcpjsonServers", [])

            # Remove from enabled if present
            if server_id in enabled_servers:
                enabled_servers.remove(server_id)

            # Add to disabled if not already there
            if server_id not in disabled_servers:
                disabled_servers.append(server_id)

            # Update settings
            settings["enabledMcpjsonServers"] = enabled_servers
            settings["disabledMcpjsonServers"] = disabled_servers

            # Write back
            self.writer.write(self.settings_local_path, settings)
            return True
        except Exception:
            return False

    def enable_server(self, server_id: str) -> bool:
        """Enable a server by adding to enabledMcpjsonServers.

        Also removes from disabledMcpjsonServers if present.
        """
        try:
            # Read current settings
            if self.settings_local_path.exists():
                settings = self.reader.read(self.settings_local_path)
            else:
                settings = {}

            # Initialize arrays if needed
            enabled_servers = settings.get("enabledMcpjsonServers", [])
            disabled_servers = settings.get("disabledMcpjsonServers", [])

            # Remove from disabled if present
            if server_id in disabled_servers:
                disabled_servers.remove(server_id)

            # Add to enabled if not already there
            if server_id not in enabled_servers:
                enabled_servers.append(server_id)

            # Update settings
            settings["enabledMcpjsonServers"] = enabled_servers
            settings["disabledMcpjsonServers"] = disabled_servers

            # Write back
            self.writer.write(self.settings_local_path, settings)
            return True
        except Exception:
            return False
```

**Acceptance Criteria**:
- [ ] Class created with proper docstrings
- [ ] `is_disabled()` implements full approval logic
- [ ] `enable_server()` adds to enabledMcpjsonServers
- [ ] `disable_server()` adds to disabledMcpjsonServers
- [ ] No inline `disabled` field manipulation (use arrays only)
- [ ] Proper error handling (try/except blocks)

**Technical Notes**:
- Handler must check BOTH inline disabled field AND approval arrays
- Inline disabled field takes precedence (backward compatibility)
- Default behavior: unapproved servers are DISABLED
- Settings file created automatically if doesn't exist

---

#### ITEM-2: Update ClaudeCodePlugin to Use New Handler

**File**: `src/mcpi/clients/claude_code.py` (lines 74-92)
**Effort**: 30 minutes
**Dependencies**: ITEM-1

**Description**: Replace `InlineEnableDisableHandler` with `ApprovalRequiredEnableDisableHandler` for project-mcp scope.

**Implementation Details**:

```python
# Line 8: Add import
from .enable_disable_handlers import (
    ArrayBasedEnableDisableHandler,
    InlineEnableDisableHandler,
    ApprovalRequiredEnableDisableHandler,  # NEW
)

# Lines 74-92: Update project-mcp scope configuration
# Project-level MCP configuration (.mcp.json)
# CRITICAL: Servers in .mcp.json require approval via enabledMcpjsonServers
project_mcp_path = self._get_scope_path("project-mcp", Path.cwd() / ".mcp.json")
project_local_path = self._get_scope_path(
    "project-local", Path.cwd() / ".claude" / "settings.local.json"
)
scopes["project-mcp"] = FileBasedScope(
    config=ScopeConfig(
        name="project-mcp",
        description="Project-level MCP configuration (.mcp.json)",
        priority=1,
        path=project_mcp_path,
        is_project_level=True,
    ),
    reader=json_reader,
    writer=json_writer,
    validator=YAMLSchemaValidator(),
    schema_path=schemas_dir / "mcp-config-schema.yaml",
    enable_disable_handler=ApprovalRequiredEnableDisableHandler(
        mcp_json_path=project_mcp_path,
        settings_local_path=project_local_path,
        reader=json_reader,
        writer=json_writer,
    ),
)
```

**Acceptance Criteria**:
- [ ] Import statement added
- [ ] Handler instantiation updated
- [ ] Both file paths passed to handler
- [ ] Comment updated to reflect approval mechanism
- [ ] No other scopes affected

**Technical Notes**:
- Settings file path is reused from project-local scope
- Both paths come from `_get_scope_path()` for testing support
- Comment should clarify approval requirement

---

### Phase 2: Unit Testing (2-3 hours)

#### ITEM-3: Write Unit Tests for ApprovalRequiredEnableDisableHandler

**File**: `tests/test_approval_required_handler.py` (NEW)
**Effort**: 2 hours
**Dependencies**: ITEM-1

**Description**: Comprehensive unit tests for new handler class covering all state combinations.

**Test Cases**:

1. **test_is_disabled_inline_disabled_field**
   - Given: Server has `"disabled": true` in .mcp.json
   - When: `is_disabled(server_id)` called
   - Then: Returns `True`

2. **test_is_disabled_in_disabled_array**
   - Given: Server in `disabledMcpjsonServers` array
   - When: `is_disabled(server_id)` called
   - Then: Returns `True`

3. **test_is_disabled_in_enabled_array**
   - Given: Server in `enabledMcpjsonServers` array
   - When: `is_disabled(server_id)` called
   - Then: Returns `False`

4. **test_is_disabled_not_approved**
   - Given: Server in .mcp.json but NOT in either array
   - When: `is_disabled(server_id)` called
   - Then: Returns `True` (not approved)

5. **test_is_disabled_no_settings_file**
   - Given: .claude/settings.local.json doesn't exist
   - When: `is_disabled(server_id)` called
   - Then: Returns `True` (not approved)

6. **test_enable_server_adds_to_array**
   - Given: Server exists in .mcp.json
   - When: `enable_server(server_id)` called
   - Then: Server added to `enabledMcpjsonServers`

7. **test_enable_server_removes_from_disabled**
   - Given: Server in `disabledMcpjsonServers`
   - When: `enable_server(server_id)` called
   - Then: Server removed from disabled, added to enabled

8. **test_disable_server_adds_to_array**
   - Given: Server exists in .mcp.json
   - When: `disable_server(server_id)` called
   - Then: Server added to `disabledMcpjsonServers`

9. **test_disable_server_removes_from_enabled**
   - Given: Server in `enabledMcpjsonServers`
   - When: `disable_server(server_id)` called
   - Then: Server removed from enabled, added to disabled

10. **test_inline_disabled_overrides_approval**
    - Given: Server has `"disabled": true` AND in `enabledMcpjsonServers`
    - When: `is_disabled(server_id)` called
    - Then: Returns `True` (inline field wins)

11. **test_enable_server_creates_settings_file**
    - Given: .claude/settings.local.json doesn't exist
    - When: `enable_server(server_id)` called
    - Then: File created with proper arrays

**Acceptance Criteria**:
- [ ] All 11 test cases implemented
- [ ] Tests use temp directories (pytest tmp_path)
- [ ] Tests verify file contents after operations
- [ ] Tests check both return values and state changes
- [ ] 100% code coverage for new handler
- [ ] All tests pass

**Technical Notes**:
- Use `tmp_path` fixture for file isolation
- Create helper functions for setting up test files
- Verify both return values AND file contents
- Test edge cases (missing files, malformed JSON)

---

### Phase 3: Integration Testing (1.5-2 hours)

#### ITEM-4: Write Integration Tests for Project-MCP Scope

**File**: `tests/test_project_mcp_approval_integration.py` (NEW)
**Effort**: 1.5 hours
**Dependencies**: ITEM-2, ITEM-3

**Description**: Integration tests verifying the full workflow with FileBasedScope and ClaudeCodePlugin.

**Test Cases**:

1. **test_add_server_shows_disabled_not_approved**
   - Given: Empty .mcp.json and .claude/settings.local.json
   - When: `mcpi add <server> --scope project-mcp`
   - Then: Server added to .mcp.json, shows DISABLED in list (not approved)

2. **test_enable_server_adds_to_approval_array**
   - Given: Server in .mcp.json but not approved
   - When: `mcpi enable <server> --scope project-mcp`
   - Then: Server added to enabledMcpjsonServers, shows ENABLED

3. **test_disable_server_adds_to_disabled_array**
   - Given: Server in .mcp.json and approved
   - When: `mcpi disable <server> --scope project-mcp`
   - Then: Server added to disabledMcpjsonServers, shows DISABLED

4. **test_list_servers_shows_correct_state**
   - Given: Multiple servers (approved, unapproved, disabled)
   - When: `mcpi list --scope project-mcp`
   - Then: Each server shows correct state

5. **test_inline_disabled_field_still_works**
   - Given: Server with `"disabled": true` in .mcp.json
   - When: `mcpi list --scope project-mcp`
   - Then: Server shows DISABLED regardless of approval

**Acceptance Criteria**:
- [ ] All 5 test cases implemented
- [ ] Tests use MCPTestHarness for realistic setup
- [ ] Tests verify both MCPI state and file contents
- [ ] Tests check integration with ClaudeCodePlugin
- [ ] All tests pass
- [ ] No regressions in existing tests

**Technical Notes**:
- Use `MCPTestHarness` for realistic file structures
- Verify both `list_servers()` output and file contents
- Test with ClaudeCodePlugin instance
- Check path_overrides mechanism works correctly

---

### Phase 4: End-to-End Validation (2-3 hours)

#### ITEM-5: Write E2E Tests Validating Against Claude MCP List

**File**: `tests/test_project_mcp_claude_validation.py` (NEW)
**Effort**: 2 hours
**Dependencies**: ITEM-4

**Description**: End-to-end tests that validate MCPI state matches actual `claude mcp list` output.

**Test Cases**:

1. **test_unapproved_server_not_in_claude_list**
   - Given: Server added to .mcp.json (not approved)
   - When: Run `claude mcp list`
   - Then: Server does NOT appear in output
   - And: `mcpi list` shows server as DISABLED

2. **test_approved_server_appears_in_claude_list**
   - Given: Server approved via `mcpi enable`
   - When: Run `claude mcp list`
   - Then: Server appears in output
   - And: `mcpi list` shows server as ENABLED

3. **test_disabled_server_not_in_claude_list**
   - Given: Server approved then disabled
   - When: Run `claude mcp list`
   - Then: Server does NOT appear in output
   - And: `mcpi list` shows server as DISABLED

4. **test_mcpi_state_matches_claude_state**
   - Given: Multiple servers in various states
   - When: Compare `mcpi list` and `claude mcp list`
   - Then: States match exactly

**Acceptance Criteria**:
- [ ] All 4 test cases implemented
- [ ] Tests run actual `claude mcp list` command
- [ ] Tests verify state consistency
- [ ] Tests clean up after themselves
- [ ] All tests pass
- [ ] Tests can run in CI (if Claude CLI available)

**Technical Notes**:
- Use `subprocess.run()` to invoke `claude mcp list`
- Parse Claude CLI output to extract server names
- Compare with MCPI's `list_servers()` output
- Clean up test files after completion
- Skip tests if `claude` CLI not available

---

#### ITEM-6: Manual Testing Checklist

**Effort**: 1 hour
**Dependencies**: ITEM-1, ITEM-2

**Description**: Manual testing to validate real-world workflows with actual Claude Code.

**Test Procedure**:

1. **Setup Test Project**:
   ```bash
   mkdir /tmp/mcpi-approval-test
   cd /tmp/mcpi-approval-test
   ```

2. **Add Server to Project-MCP**:
   ```bash
   mcpi add filesystem --scope project-mcp
   mcpi list --scope project-mcp
   # Expect: filesystem shows as DISABLED

   claude mcp list
   # Expect: filesystem does NOT appear
   ```

3. **Enable Server (Approve)**:
   ```bash
   mcpi enable filesystem --scope project-mcp
   mcpi list --scope project-mcp
   # Expect: filesystem shows as ENABLED

   claude mcp list
   # Expect: filesystem APPEARS
   ```

4. **Disable Server**:
   ```bash
   mcpi disable filesystem --scope project-mcp
   mcpi list --scope project-mcp
   # Expect: filesystem shows as DISABLED

   claude mcp list
   # Expect: filesystem does NOT appear
   ```

5. **Verify File Contents**:
   ```bash
   cat .mcp.json
   # Expect: filesystem config present

   cat .claude/settings.local.json
   # Expect: disabledMcpjsonServers contains "filesystem"
   ```

**Acceptance Criteria**:
- [ ] All manual tests pass
- [ ] MCPI state matches Claude Code behavior
- [ ] Files contain expected data
- [ ] No errors or exceptions
- [ ] User experience is intuitive

---

### Phase 5: Documentation and Cleanup (1 hour)

#### ITEM-7: Update CLAUDE.md Documentation

**File**: `CLAUDE.md`
**Effort**: 30 minutes
**Dependencies**: ITEM-6

**Description**: Update documentation to explain project-mcp approval mechanism.

**Changes Required**:

1. **Add Section on Project-MCP Approval** (after User-Global Disable Mechanism section):

```markdown
## Project-MCP Approval Mechanism

### Overview

For project-scoped MCP servers in `.mcp.json`, Claude Code requires **explicit approval** before loading servers. This is a security feature to prevent malicious projects from automatically loading untrusted servers.

### Implementation Design

**Files**:
- `.mcp.json`: Server configurations (project-level)
- `.claude/settings.local.json`: Approval tracking (project-level settings)

**Behavior**:
1. **Unapproved servers**: Server in .mcp.json but NOT in approval arrays → DISABLED (won't load)
2. **Approved servers**: Server in `enabledMcpjsonServers` array → ENABLED (will load)
3. **Disabled servers**: Server in `disabledMcpjsonServers` array → DISABLED (won't load)

### Operations

**Add a server** (`mcpi add <server-name> --scope project-mcp`):
1. Add server configuration to `.mcp.json`
2. Server shows as DISABLED in `mcpi list` (not approved)
3. Server does NOT appear in `claude mcp list` output

**Enable a server** (`mcpi enable <server-name> --scope project-mcp`):
1. Add server to `enabledMcpjsonServers` array in `.claude/settings.local.json`
2. Remove from `disabledMcpjsonServers` if present
3. Server shows as ENABLED in `mcpi list`
4. Server appears in `claude mcp list` output

**Disable a server** (`mcpi disable <server-name> --scope project-mcp`):
1. Add server to `disabledMcpjsonServers` array in `.claude/settings.local.json`
2. Remove from `enabledMcpjsonServers` if present
3. Server shows as DISABLED in `mcpi list`
4. Server removed from `claude mcp list` output

### Validation Requirements

**Critical validation**:
- Running `claude mcp list` shows only ENABLED servers
- Running `mcpi list --scope project-mcp` shows ALL servers with correct state
- Servers show as DISABLED until explicitly enabled
- Enabled servers appear in `claude mcp list` output

### Implementation Files

- `src/mcpi/clients/enable_disable_handlers.py`: ApprovalRequiredEnableDisableHandler
- `src/mcpi/clients/claude_code.py`: Integration with project-mcp scope
- `tests/test_approval_required_handler.py`: Unit tests
- `tests/test_project_mcp_approval_integration.py`: Integration tests
- `tests/test_project_mcp_claude_validation.py`: E2E validation tests
```

**Acceptance Criteria**:
- [ ] New section added to CLAUDE.md
- [ ] Mechanism explained clearly
- [ ] Examples provided
- [ ] Files referenced
- [ ] Validation requirements documented

---

#### ITEM-8: Update Code Comments and Docstrings

**Files**: Multiple
**Effort**: 30 minutes
**Dependencies**: ITEM-7

**Description**: Ensure all code has clear comments explaining approval mechanism.

**Changes Required**:

1. **enable_disable_handlers.py**: Update class docstring to explain approval logic
2. **claude_code.py**: Update comment on project-mcp scope to mention approval
3. **Test files**: Add module docstrings explaining what's being tested

**Acceptance Criteria**:
- [ ] All new code has docstrings
- [ ] Comments explain WHY not just WHAT
- [ ] Approval mechanism clearly documented
- [ ] Examples provided where helpful

---

## Acceptance Criteria for Complete Fix

### Functional Requirements

- [x] **FR1**: Server in `.mcp.json` WITHOUT approval shows as DISABLED in `mcpi list`
- [x] **FR2**: Server in `.mcp.json` WITH approval shows as ENABLED in `mcpi list`
- [x] **FR3**: `mcpi enable --scope project-mcp <server>` adds to `enabledMcpjsonServers`
- [x] **FR4**: `mcpi disable --scope project-mcp <server>` adds to `disabledMcpjsonServers`
- [x] **FR5**: ENABLED server appears in `claude mcp list` output
- [x] **FR6**: DISABLED server does NOT appear in `claude mcp list` output

### Validation Requirements

- [x] **VR1**: `mcpi list` output matches `claude mcp list` output (state accuracy)
- [x] **VR2**: Inline `"disabled": true` still works (backward compatibility)
- [x] **VR3**: Other scopes unaffected (regression prevention)
- [x] **VR4**: All unit tests pass (11 new tests)
- [x] **VR5**: All integration tests pass (5 new tests)
- [x] **VR6**: All E2E tests pass (4 new tests)

### Quality Requirements

- [x] **QR1**: 100% test coverage for new handler
- [x] **QR2**: No exceptions or errors during enable/disable operations
- [x] **QR3**: Settings file created with proper permissions if doesn't exist
- [x] **QR4**: Atomic writes to settings file (no partial updates)
- [x] **QR5**: Clear error messages if operations fail

---

## Dependency Graph

```
ITEM-1: Create ApprovalRequiredEnableDisableHandler (1.5 hours)
  └─> Base implementation

ITEM-2: Update ClaudeCodePlugin (30 min)
  ├─> Depends on: ITEM-1
  └─> Integrates handler into scope

ITEM-3: Unit Tests (2 hours)
  ├─> Depends on: ITEM-1
  └─> 11 test cases for handler

ITEM-4: Integration Tests (1.5 hours)
  ├─> Depends on: ITEM-2, ITEM-3
  └─> 5 test cases for full workflow

ITEM-5: E2E Tests (2 hours)
  ├─> Depends on: ITEM-4
  └─> 4 test cases validating against Claude

ITEM-6: Manual Testing (1 hour)
  ├─> Depends on: ITEM-1, ITEM-2
  └─> Real-world validation

ITEM-7: Update Documentation (30 min)
  ├─> Depends on: ITEM-6
  └─> CLAUDE.md updates

ITEM-8: Code Comments (30 min)
  ├─> Depends on: ITEM-7
  └─> Docstrings and comments
```

**Critical Path**: ITEM-1 → ITEM-2 → ITEM-3 → ITEM-4 → ITEM-5 → ITEM-6 → ITEM-7 → ITEM-8

**Total Time**: 6-9 hours

---

## Testing Strategy

### Unit Tests (2 hours)

**Coverage Target**: 100% for ApprovalRequiredEnableDisableHandler

**Test Isolation**: Use temp directories, no real files

**Test Categories**:
1. State detection (5 tests)
2. Enable operations (3 tests)
3. Disable operations (3 tests)

**Total Tests**: 11 unit tests

---

### Integration Tests (1.5 hours)

**Coverage Target**: Full workflow from add → enable → disable

**Test Setup**: Use MCPTestHarness for realistic file structures

**Test Categories**:
1. Add server workflow (1 test)
2. Enable server workflow (1 test)
3. Disable server workflow (1 test)
4. List servers (1 test)
5. Backward compatibility (1 test)

**Total Tests**: 5 integration tests

---

### E2E Tests (2 hours)

**Coverage Target**: Validate against actual Claude Code behavior

**Test Setup**: Real project with .mcp.json and .claude/settings.local.json

**Test Categories**:
1. Unapproved server validation (1 test)
2. Approved server validation (1 test)
3. Disabled server validation (1 test)
4. State consistency check (1 test)

**Total Tests**: 4 E2E tests

---

### Manual Testing (1 hour)

**Coverage Target**: Real-world user workflows

**Test Setup**: Temporary project directory

**Test Procedure**: 5-step workflow (add → verify → enable → verify → disable → verify)

**Validation**: Compare `mcpi list` and `claude mcp list` outputs

---

## Risk Assessment

### Implementation Risk: VERY LOW

**Confidence**: VERY HIGH (10/10)

**Why Low Risk**:
- Clear root cause identified
- Solution is straightforward
- Follows existing patterns (ArrayBasedEnableDisableHandler)
- No architectural changes required
- Only affects project-mcp scope
- Backward compatible (inline disabled field still works)

**Mitigation**:
- Comprehensive test suite (20 tests)
- E2E validation against Claude Code
- Manual testing checklist
- Clear documentation

---

### Regression Risk: VERY LOW

**Why Low Risk**:
- Only project-mcp scope affected
- Other scopes unchanged
- Existing tests should all pass
- New handler is isolated

**Mitigation**:
- Run full test suite after changes
- Verify other scopes unaffected
- Check existing integration tests

---

### User Impact Risk: LOW

**Why Low Risk**:
- Bug currently prevents servers from working
- Fix makes behavior match expectations
- Users already expect approval mechanism

**Potential Issues**:
- Servers that were showing ENABLED will now show DISABLED (correct behavior)
- Users will need to run `mcpi enable` to approve servers

**Mitigation**:
- Clear documentation of approval mechanism
- Helpful error messages
- CLI help text explains approval

---

## Migration Considerations

### Breaking Changes: NONE

**Behavioral Changes**:
- Servers in `.mcp.json` will NOW show as DISABLED if not approved
- This matches Claude Code's actual behavior (fixing the lie)
- Users will need to run `mcpi enable` to approve project-mcp servers

### Upgrade Path

**For Users**:
1. Update MCPI to new version
2. Run `mcpi list --scope project-mcp`
3. Servers show DISABLED if not approved
4. Run `mcpi enable <server> --scope project-mcp` to approve
5. Verify server appears in `claude mcp list`

**For Developers**:
1. Pull latest changes
2. Run test suite to verify
3. No code changes required

### Communication Plan

**Release Notes**:
```markdown
## Bug Fix: Project-MCP Approval Detection

**Issue**: Servers in `.mcp.json` were incorrectly showing as ENABLED even when not approved by Claude Code.

**Fix**: MCPI now correctly detects Claude's approval mechanism and shows servers as DISABLED until approved via `mcpi enable`.

**Impact**:
- Servers in `.mcp.json` without approval will now show as DISABLED (correct state)
- Run `mcpi enable <server> --scope project-mcp` to approve servers
- ENABLED servers will now correctly appear in `claude mcp list`

**Migration**: No action required. Existing servers continue to work as before.
```

---

## Success Metrics

### Definition of Done

- [ ] All 8 work items completed
- [ ] 20 new tests written and passing
- [ ] 100% test coverage for new handler
- [ ] All existing tests still pass
- [ ] Manual testing checklist complete
- [ ] Documentation updated
- [ ] No regressions detected

### Validation Criteria

- [ ] `mcpi list --scope project-mcp` shows correct states
- [ ] `claude mcp list` output matches MCPI states
- [ ] Unapproved servers show as DISABLED
- [ ] Approved servers show as ENABLED
- [ ] Enable/disable operations work correctly

### Quality Metrics

- [ ] Zero exceptions during normal operations
- [ ] Zero test failures
- [ ] 100% handler code coverage
- [ ] Clear, helpful error messages
- [ ] Documentation complete and accurate

---

## Implementation Timeline

### Session 1: Core Implementation (3-4 hours)

**Tasks**:
1. ITEM-1: Create ApprovalRequiredEnableDisableHandler (1.5 hours)
2. ITEM-2: Update ClaudeCodePlugin (30 min)
3. ITEM-3: Unit Tests (2 hours)

**Goal**: Handler implemented and unit tested

**Validation**: All unit tests pass

---

### Session 2: Integration and E2E Testing (4-5 hours)

**Tasks**:
1. ITEM-4: Integration Tests (1.5 hours)
2. ITEM-5: E2E Tests (2 hours)
3. ITEM-6: Manual Testing (1 hour)

**Goal**: Full workflow validated against Claude Code

**Validation**:
- All integration tests pass
- All E2E tests pass
- Manual testing checklist complete

---

### Session 3: Documentation and Polish (1 hour)

**Tasks**:
1. ITEM-7: Update CLAUDE.md (30 min)
2. ITEM-8: Code Comments (30 min)

**Goal**: Complete documentation

**Validation**: Documentation accurate and helpful

---

## Recommended Next Steps

### IMMEDIATE (This Session)

1. **START**: ITEM-1 - Create ApprovalRequiredEnableDisableHandler
2. **VERIFY**: Unit tests pass for handler
3. **INTEGRATE**: ITEM-2 - Update ClaudeCodePlugin

### NEXT SESSION

1. **TEST**: ITEM-3, ITEM-4, ITEM-5 - Write comprehensive tests
2. **VALIDATE**: ITEM-6 - Manual testing against real Claude Code
3. **DOCUMENT**: ITEM-7, ITEM-8 - Update docs and comments

### COMPLETION CRITERIA

**Before Marking as Complete**:
- All 8 work items finished
- All 20 tests passing
- Manual testing checklist verified
- Documentation updated
- `claude mcp list` validation successful

---

## Appendix: Code Locations

### Files to Create (3 new files)

1. `tests/test_approval_required_handler.py` - Unit tests (11 tests)
2. `tests/test_project_mcp_approval_integration.py` - Integration tests (5 tests)
3. `tests/test_project_mcp_claude_validation.py` - E2E tests (4 tests)

### Files to Modify (3 files)

1. `src/mcpi/clients/enable_disable_handlers.py` - Add ApprovalRequiredEnableDisableHandler class (~150 lines)
2. `src/mcpi/clients/claude_code.py` - Update project-mcp scope (lines 8, 74-92)
3. `CLAUDE.md` - Add Project-MCP Approval Mechanism section (~50 lines)

### Files to Reference (2 files)

1. `STATUS-2025-11-16-PROJECT-MCP-APPROVAL-BUG.md` - Root cause analysis
2. `src/mcpi/clients/enable_disable_handlers.py` - Existing handler patterns

---

**END OF IMPLEMENTATION PLAN**

Generated: 2025-11-16 17:37:14
Total Work Items: 8
Total Effort: 6-9 hours
Critical Path: ITEM-1 → ITEM-2 → ITEM-3 → ITEM-4 → ITEM-5 → ITEM-6 → ITEM-7 → ITEM-8
First Action: Create ApprovalRequiredEnableDisableHandler class
