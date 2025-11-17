# Critical Bug: Project-MCP Servers Show ENABLED But Don't Appear in Claude Code

**Report Date**: 2025-11-16
**Severity**: CRITICAL
**Status**: ROOT CAUSE IDENTIFIED

## Executive Summary

**Bug Description**: Servers in the `project-mcp` scope show as `ENABLED` in `mcpi list` but do NOT appear in `claude mcp list` output.

**Root Cause**: MCPI's state detection logic for `project-mcp` scope is incomplete. Servers in `.mcp.json` require EXPLICIT APPROVAL via the `enabledMcpjsonServers` array in `.claude/settings.local.json` to be loaded by Claude Code, but MCPI does not check this approval mechanism.

**Impact**: Users cannot use servers that MCPI reports as enabled, breaking the fundamental contract that "ENABLED servers should work in Claude Code."

**Recommendation**: Implement approval-aware state detection for `project-mcp` scope IMMEDIATELY.

## Root Cause Analysis

### What Is Happening

1. **MCPI's Perspective**:
   - MCPI reads `.mcp.json` and finds `example-name` server configuration
   - MCPI uses `InlineEnableDisableHandler` which only checks for `"disabled": true` field
   - Since there's no `"disabled": true` field, MCPI reports state as `ENABLED`
   - `mcpi list` shows: `example-name | claude-code | project-mcp | ENABLED`

2. **Claude Code's Perspective**:
   - Claude Code reads `.mcp.json` and finds `example-name` server configuration
   - Claude Code checks `.claude/settings.local.json` for `enabledMcpjsonServers` array
   - Since `example-name` is NOT in `enabledMcpjsonServers` array, Claude Code REJECTS the server
   - `claude mcp list` shows: (server does not appear - NOT loaded)

3. **The Mismatch**:
   - MCPI thinks: "Server exists in config and not explicitly disabled → ENABLED"
   - Claude Code thinks: "Server exists in .mcp.json but not approved → NOT LOADED"
   - Result: CRITICAL state detection failure

### Why It's Happening

**Code Location**: `src/mcpi/clients/claude_code.py:74-92`

The `project-mcp` scope is configured with `InlineEnableDisableHandler`:

```python
# Project-level MCP configuration (.mcp.json)
# This scope DOES support enable/disable via inline 'disabled' field
project_mcp_path = self._get_scope_path("project-mcp", Path.cwd() / ".mcp.json")
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
    enable_disable_handler=InlineEnableDisableHandler(
        project_mcp_path, json_reader, json_writer
    ),
)
```

**Code Location**: `src/mcpi/clients/enable_disable_handlers.py:201-219`

The `InlineEnableDisableHandler.is_disabled()` method only checks for inline `"disabled": true` field:

```python
def is_disabled(self, server_id: str) -> bool:
    """Check if a server is disabled.

    Args:
        server_id: Server identifier

    Returns:
        True if server has 'disabled' field set to true
    """
    if not self.config_path.exists():
        return False

    try:
        data = self.reader.read(self.config_path)
        servers = data.get("mcpServers", {})
        server_config = servers.get(server_id, {})
        return server_config.get("disabled") is True
    except Exception:
        return False
```

**The Missing Logic**: This handler does NOT check if the server is in the `enabledMcpjsonServers` array in `.claude/settings.local.json`, which is Claude Code's REQUIRED approval mechanism for `.mcp.json` servers.

### Claude Code's Approval Mechanism

Based on web research and testing:

1. **Security Requirement**: Claude Code requires explicit approval for project-scoped servers (security feature)
2. **Approval Storage**: `.claude/settings.local.json` (project-level settings file)
3. **Approval Array**: `enabledMcpjsonServers: ["server-name", ...]`
4. **Rejection Array**: `disabledMcpjsonServers: ["server-name", ...]` (optional)
5. **Default Behavior**: If server NOT in either array → NOT LOADED (security default)

**Evidence**:
- Before adding to `enabledMcpjsonServers`: `claude mcp list` does NOT show `example-name`
- After adding to `enabledMcpjsonServers`: `claude mcp list` shows `example-name`
- After removing from `enabledMcpjsonServers`: `claude mcp list` does NOT show `example-name`

## Impact Assessment

### Affected Scopes

**CRITICAL**: `project-mcp` scope (`.mcp.json` files)

**NOT AFFECTED**:
- `project-local` scope (already uses `ArrayBasedEnableDisableHandler`)
- `user-local` scope (already uses `ArrayBasedEnableDisableHandler`)
- `user-global` scope (uses `FileMoveEnableDisableHandler`)
- `user-internal` scope (uses `FileMoveEnableDisableHandler`)
- `user-mcp` scope (no enable/disable handler)

### User Impact

**Who Is Affected**: ALL users adding project-scoped servers to `.mcp.json` files

**What Breaks**:
1. Users add server via `mcpi add --scope project-mcp`
2. MCPI reports server as ENABLED
3. User expects server to work in Claude Code
4. Server does NOT appear in `claude mcp list`
5. User cannot use the server (tools not available)

**Data Loss Risk**: NONE (configuration files not corrupted)

**Workaround Available**: YES (manually add server to `enabledMcpjsonServers` array)

### Severity Justification

**CRITICAL** because:
1. Breaks fundamental contract: "ENABLED servers should work"
2. Affects core functionality (server management)
3. User-facing bug with no clear error message
4. Confusing user experience (status lies)
5. Undermines trust in MCPI

## Proposed Solution

### High-Level Design

Create a new `ApprovalRequiredEnableDisableHandler` that:

1. **Checks inline `"disabled": true` field** (backward compatibility)
2. **Checks `.claude/settings.local.json` for approval arrays**:
   - If server in `disabledMcpjsonServers` → DISABLED
   - If server in `enabledMcpjsonServers` → ENABLED
   - If server in neither array → NOT_APPROVED (new state OR treat as DISABLED)

### Implementation Details

**New Handler Class** (`src/mcpi/clients/enable_disable_handlers.py`):

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
        """Initialize the approval-required handler.

        Args:
            mcp_json_path: Path to .mcp.json file
            settings_local_path: Path to .claude/settings.local.json file
            reader: Configuration file reader
            writer: Configuration file writer
        """
        self.mcp_json_path = mcp_json_path
        self.settings_local_path = settings_local_path
        self.reader = reader
        self.writer = writer

    def is_disabled(self, server_id: str) -> bool:
        """Check if a server is disabled or not approved.

        Args:
            server_id: Server identifier

        Returns:
            True if server is disabled OR not in enabledMcpjsonServers
        """
        # Check inline disabled field
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
        # Implementation similar to ArrayBasedEnableDisableHandler
        ...

    def enable_server(self, server_id: str) -> bool:
        """Enable a server by adding to enabledMcpjsonServers.

        Also removes from disabledMcpjsonServers if present.
        """
        # Implementation similar to ArrayBasedEnableDisableHandler
        ...
```

**Update ClaudeCodePlugin** (`src/mcpi/clients/claude_code.py:74-92`):

```python
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

### Test Strategy

**Unit Tests** (`tests/test_approval_required_handler.py`):
1. Test `is_disabled()` with inline `"disabled": true` field
2. Test `is_disabled()` with server in `disabledMcpjsonServers`
3. Test `is_disabled()` with server in `enabledMcpjsonServers` (should return False)
4. Test `is_disabled()` with server in neither array (should return True - not approved)
5. Test `enable_server()` adds to `enabledMcpjsonServers`
6. Test `disable_server()` adds to `disabledMcpjsonServers`

**Integration Tests** (`tests/test_project_mcp_approval.py`):
1. Add server to `.mcp.json` via `mcpi add`
2. Verify `mcpi list` shows server as DISABLED (not approved)
3. Run `mcpi enable` to approve server
4. Verify `mcpi list` shows server as ENABLED
5. Verify `.claude/settings.local.json` contains server in `enabledMcpjsonServers`

**End-to-End Tests** (`tests/test_claude_mcp_list_validation.py`):
1. Add server via `mcpi add --scope project-mcp`
2. Run `mcpi enable --scope project-mcp <server-name>`
3. Run `claude mcp list` and verify server appears
4. Run `mcpi disable --scope project-mcp <server-name>`
5. Run `claude mcp list` and verify server does NOT appear

**Edge Cases**:
1. Settings file doesn't exist → create it on first enable
2. Settings file exists but no arrays → add arrays on enable/disable
3. Server in both enabled and disabled arrays → disabled wins (defensive)
4. Inline `"disabled": true` overrides approval arrays (backward compatibility)

### Migration Considerations

**Breaking Changes**: NONE

**Behavioral Changes**:
- Servers in `.mcp.json` will NOW show as DISABLED if not approved
- Users will need to run `mcpi enable` to approve project-mcp servers
- This matches Claude Code's actual behavior (fixing the lie)

**Upgrade Path**:
1. Update handler implementation
2. Update tests
3. Release as patch (bug fix, not feature)
4. Document in release notes
5. Add warning in CLI when server needs approval

## Acceptance Criteria for Fix

### Functional Requirements

✅ **FR1**: Server in `.mcp.json` WITHOUT approval shows as DISABLED in `mcpi list`
✅ **FR2**: Server in `.mcp.json` WITH approval shows as ENABLED in `mcpi list`
✅ **FR3**: `mcpi enable --scope project-mcp <server>` adds to `enabledMcpjsonServers`
✅ **FR4**: `mcpi disable --scope project-mcp <server>` adds to `disabledMcpjsonServers`
✅ **FR5**: ENABLED server appears in `claude mcp list` output
✅ **FR6**: DISABLED server does NOT appear in `claude mcp list` output

### Validation Requirements

✅ **VR1**: `mcpi list` output matches `claude mcp list` output (state accuracy)
✅ **VR2**: Inline `"disabled": true` still works (backward compatibility)
✅ **VR3**: Other scopes unaffected (regression prevention)
✅ **VR4**: All unit tests pass
✅ **VR5**: All integration tests pass
✅ **VR6**: All E2E tests pass

### Quality Requirements

✅ **QR1**: 100% test coverage for new handler
✅ **QR2**: No exceptions or errors during enable/disable operations
✅ **QR3**: Settings file created with proper permissions if doesn't exist
✅ **QR4**: Atomic writes to settings file (no partial updates)
✅ **QR5**: Clear error messages if operations fail

## Implementation Plan

### Phase 1: Handler Implementation (2-3 hours)

1. Create `ApprovalRequiredEnableDisableHandler` class
2. Implement `is_disabled()` method with approval logic
3. Implement `enable_server()` method
4. Implement `disable_server()` method
5. Write unit tests for all methods
6. Verify 100% test coverage

### Phase 2: Integration (1-2 hours)

1. Update `ClaudeCodePlugin._initialize_scopes()` to use new handler
2. Write integration tests for project-mcp scope
3. Run all existing tests to check for regressions
4. Fix any breaking changes

### Phase 3: Validation (2-3 hours)

1. Write E2E tests validating against `claude mcp list`
2. Test with real `.mcp.json` files
3. Test approval workflow (add → enable → verify)
4. Test disable workflow (disable → verify)
5. Test edge cases (missing files, malformed JSON, etc.)

### Phase 4: Documentation (1 hour)

1. Update CLAUDE.md with approval mechanism details
2. Add inline documentation for new handler
3. Update CLI help text for enable/disable commands
4. Create migration guide for existing users

**Total Estimated Time**: 6-9 hours

## Concise Summary

1. **Root Cause**: MCPI uses `InlineEnableDisableHandler` for `project-mcp` scope, which only checks for `"disabled": true` field and ignores Claude Code's required `enabledMcpjsonServers` approval mechanism.

2. **Affected Scopes**: `project-mcp` scope ONLY (`.mcp.json` files)

3. **Fix Location**:
   - `src/mcpi/clients/enable_disable_handlers.py` (new handler class)
   - `src/mcpi/clients/claude_code.py:74-92` (use new handler)

4. **Severity**: CRITICAL (breaks fundamental contract, user-facing bug)

5. **Ready for Implementation**: YES

## Recommended Next Steps

1. **PAUSE ALL OTHER WORK** - This is a critical bug affecting core functionality
2. **Implement `ApprovalRequiredEnableDisableHandler`** following the design above
3. **Write comprehensive tests** (unit, integration, E2E)
4. **Validate against `claude mcp list`** to ensure state accuracy
5. **Update documentation** explaining approval mechanism
6. **Release as patch** (0.3.1) with clear release notes

This bug MUST be fixed before any new features are added. The current behavior violates user trust and breaks the fundamental promise that "ENABLED servers work in Claude Code."
