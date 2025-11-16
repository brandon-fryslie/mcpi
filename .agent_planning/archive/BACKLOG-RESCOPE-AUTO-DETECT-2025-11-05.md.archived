# Rescope Auto-Detect Implementation Backlog

**Date**: 2025-11-05
**Status Source**: STATUS-2025-10-30-062049.md (Emergency Assessment - CLI BROKEN but now fixed)
**Spec Source**: RESCOPE-AUTO-DETECT-EVALUATION.md (2025-11-05 evaluation)
**Generation Time**: 2025-11-05
**Approach**: OPTION B (CONSERVATIVE) - Auto-detect single scope, error on multiple

---

## Executive Summary

This backlog implements automatic scope detection for the `mcpi rescope` command, making the `--from` parameter optional. When omitted, the system will auto-detect which scope contains the server and move it to the destination scope.

**Key Decision**: Using OPTION B (Conservative approach) which:
- Auto-detects source scope when server exists in exactly ONE scope
- Errors with clear message if server exists in MULTIPLE scopes (requires explicit --from)
- Keeps --from parameter as optional override for power users
- Provides backward compatibility with existing scripts

**Total Estimated Effort**: 3.5-5.5 hours
- Implementation: 2-3 hours
- Testing: 1-2 hours
- Documentation: 0.5 hour

**Dependencies**: None (implementation is self-contained)

**Risk Level**: LOW (conservative approach, backward compatible, well-tested existing code)

---

## Prioritized Backlog

### P0: Core Implementation (3.5-5.5 hours total)

These items must be completed in order as they have sequential dependencies.

---

## [P0-1] Add find_all_server_scopes() Method to MCPManager

**Status**: Not Started
**Effort**: Small (30-45 minutes)
**Dependencies**: None
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 3.1 • **Status Reference**: STATUS-2025-10-30-062049.md (CLI now functional)

### Description

Add a new helper method to `MCPManager` that finds ALL scopes containing a specific server, unlike the existing `find_server_location()` which returns only the first match. This is critical for handling the case where a server exists in multiple scopes.

The method should:
- Accept `server_id` (required) and `client_name` (optional)
- Use default client if none specified
- Return a list of dictionaries with `{client, scope, qualified_id}` for each match
- Return empty list if no matches found
- Handle errors gracefully with logging

### Acceptance Criteria

- [ ] Method signature matches: `find_all_server_scopes(self, server_id: str, client_name: Optional[str] = None) -> List[Dict[str, str]]`
- [ ] Returns empty list when server not found in any scope
- [ ] Returns single-item list when server found in exactly one scope
- [ ] Returns multi-item list when server found in multiple scopes
- [ ] Uses default client when client_name is None
- [ ] Logs debug message indicating how many scopes found
- [ ] Logs error and returns empty list on exceptions
- [ ] Each returned dict contains keys: `client`, `scope`, `qualified_id`
- [ ] Method has comprehensive docstring with example usage
- [ ] Type hints are complete and accurate

### Technical Notes

**File**: `src/mcpi/clients/manager.py`
**Location**: After line 332 (after existing `find_server_location()` method)
**Pattern**: Follow existing `find_server_location()` but collect ALL matches instead of returning first

**Implementation approach**:
```python
def find_all_server_scopes(
    self, server_id: str, client_name: Optional[str] = None
) -> List[Dict[str, str]]:
    """Find ALL scopes containing a specific server.

    Unlike find_server_location() which returns first match,
    this returns all matches for handling multi-scope scenarios.
    ...
    """
    if client_name is None:
        client_name = self._default_client

    if not client_name or not self.registry.has_client(client_name):
        logger.warning(f"No valid client available")
        return []

    try:
        client = self.registry.get_client(client_name)
        servers = client.list_servers()  # All scopes

        matches = []
        for qualified_id, info in servers.items():
            if info.id == server_id:
                matches.append({
                    "client": info.client,
                    "scope": info.scope,
                    "qualified_id": qualified_id,
                })

        logger.debug(f"Found {len(matches)} scope(s) containing '{server_id}'")
        return matches
    except Exception as e:
        logger.error(f"Error finding server scopes: {e}")
        return []
```

**Verification**:
- Manual test: Add method, run pytest on manager tests
- Import check: Verify no circular imports
- Type check: Run mypy on manager.py

---

## [P0-2] Make --from Parameter Optional in Rescope Command

**Status**: Not Started
**Effort**: Small (15 minutes)
**Dependencies**: None (can be done independently)
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 3.2 Change 1 • **Status Reference**: STATUS-2025-10-30-062049.md

### Description

Change the `--from` parameter in the `rescope` command from `required=True` to `required=False`, and update the help text to indicate it's optional and will be auto-detected if not specified.

This enables the auto-detection feature while maintaining backward compatibility for existing scripts that explicitly specify `--from`.

### Acceptance Criteria

- [ ] `required=False` on --from parameter
- [ ] Help text updated to: "Source scope to move from (auto-detected if not specified)"
- [ ] Command still accepts --from when explicitly provided
- [ ] Command runs without error when --from omitted (will fail later if auto-detect logic not added)
- [ ] Help output shows --from as optional (not required)
- [ ] Existing tests that use --from still pass

### Technical Notes

**File**: `src/mcpi/cli.py`
**Location**: Line ~1240 (in the rescope command decorator)
**Current code**:
```python
@click.option("--from", "from_scope", required=True, type=DynamicScopeType(), help="Source scope to move from")
```

**New code**:
```python
@click.option(
    "--from",
    "from_scope",
    required=False,
    type=DynamicScopeType(),
    help="Source scope to move from (auto-detected if not specified)"
)
```

**Verification**:
- Run: `mcpi rescope --help` and verify --from shows as optional
- Existing tests with --from should still pass
- Tests without --from will fail until P0-3 is implemented

---

## [P0-3] Implement Auto-Detection Logic with Multi-Scope Handling

**Status**: Not Started
**Effort**: Medium (1-1.5 hours)
**Dependencies**: P0-1 (requires find_all_server_scopes method)
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 3.3 (OPTION B) • **Status Reference**: STATUS-2025-10-30-062049.md

### Description

Add auto-detection logic to the rescope command that:
1. Calls `find_all_server_scopes()` when --from is not provided
2. Handles three cases:
   - **Server not found**: Error with helpful message
   - **Server in one scope**: Auto-detect and proceed (most common case - 95%)
   - **Server in multiple scopes**: Error listing all scopes and requiring explicit --from (edge case - 5%)

This implements OPTION B (Conservative) which prevents surprises by requiring explicit control for the multi-scope edge case.

### Acceptance Criteria

**Auto-Detection Logic**:
- [ ] When --from is None, calls `manager.find_all_server_scopes(server_name, client_name)`
- [ ] When --from is provided, uses explicit value (backward compatibility)

**Case 1: Server Not Found (0 scopes)**:
- [ ] Shows error: "Error: Server 'X' not found in any scope for client 'Y'"
- [ ] Shows tip: "Tip: Run 'mcpi list' to see all installed servers"
- [ ] Exits with code 1
- [ ] Works correctly with --dry-run

**Case 2: Server in One Scope (single match)**:
- [ ] Auto-detects the scope
- [ ] Shows message: "Auto-detected source scope: {scope}" (dim style)
- [ ] Proceeds with rescope operation
- [ ] Existing rescope logic works unchanged
- [ ] Success message shows detected scope

**Case 3: Server in Multiple Scopes (2+ matches)**:
- [ ] Shows error: "Error: Server 'X' exists in N scopes:"
- [ ] Lists all matching scopes with numbering (1. scope1, 2. scope2, ...)
- [ ] Shows guidance: "Please specify which scope to move from using --from:"
- [ ] Shows example command: `mcpi rescope X --from <scope> --to Y`
- [ ] Exits with code 1
- [ ] Works correctly with --dry-run

**General**:
- [ ] from_scope variable is set correctly for all paths through the logic
- [ ] Existing rescope transaction logic (lines 1323-1410) works unchanged
- [ ] Dry-run mode shows detected scope but doesn't execute
- [ ] All error messages are user-friendly and actionable

### Technical Notes

**File**: `src/mcpi/cli.py`
**Location**: Insert after line ~1300 (after validation that from_scope != to_scope, but before scope handler retrieval)

**Key Implementation Points**:
1. Insert auto-detection logic early, before scope handlers are retrieved
2. Set `from_scope` variable so existing code path works unchanged
3. Use rich console styling for output (`[red]`, `[yellow]`, `[dim]`)
4. Respect --dry-run flag (don't show interactive prompts in dry-run)
5. Provide helpful error messages with actionable next steps

**Code Structure** (see evaluation doc Section 3.3 for full implementation):
```python
# After validation that to_scope != from_scope (line ~1300)

# Step 2.5: Auto-detect source scope if not specified
if not from_scope:
    # Find all scopes containing the server
    matching_scopes = manager.find_all_server_scopes(server_name, client_name)

    if not matching_scopes:
        # Case 1: Not found
        console.print(f"[red]Error: Server '{server_name}' not found...")
        ctx.exit(1)

    if len(matching_scopes) == 1:
        # Case 2: Single scope (COMMON - 95%)
        from_scope = matching_scopes[0]['scope']
        console.print(f"[dim]Auto-detected source scope: {from_scope}[/dim]")
    else:
        # Case 3: Multiple scopes (EDGE CASE - 5%)
        console.print(f"[red]Error: Server '{server_name}' exists in {len(matching_scopes)} scopes:[/red]")
        for i, match in enumerate(matching_scopes, 1):
            console.print(f"  {i}. {match['scope']}")
        console.print("\n[yellow]Please specify which scope to move from using --from:[/yellow]")
        console.print(f"  mcpi rescope {server_name} --from <scope> --to {to_scope}")
        ctx.exit(1)

# Continue with existing logic - from_scope is now set
# (lines 1302-1410 work unchanged)
```

**Verification Steps**:
1. Test server not found: `mcpi rescope nonexistent --to user-global`
2. Test single scope: Install server in one scope, rescope without --from
3. Test multiple scopes: Install same server in two scopes, try rescope without --from
4. Test backward compat: Rescope with explicit --from still works
5. Test dry-run: All cases work with --dry-run flag

---

## [P0-4] Add Unit Tests for find_all_server_scopes()

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: P0-1 (method must exist to test)
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 4.2 • **Status Reference**: STATUS-2025-10-30-062049.md

### Description

Add comprehensive unit tests for the new `find_all_server_scopes()` method to cover:
- Server not found (empty list)
- Server found in one scope (single-item list)
- Server found in multiple scopes (multi-item list)
- Client parameter handling (explicit vs. default)
- Error handling (invalid client, exceptions)

These tests validate the method in isolation before integration testing the full rescope command.

### Acceptance Criteria

- [ ] Test: `test_find_all_server_scopes_not_found` - Returns empty list when server doesn't exist
- [ ] Test: `test_find_all_server_scopes_single_match` - Returns single-item list with correct data
- [ ] Test: `test_find_all_server_scopes_multiple_matches` - Returns multi-item list for server in 2+ scopes
- [ ] Test: `test_find_all_server_scopes_uses_default_client` - Uses default client when client_name is None
- [ ] Test: `test_find_all_server_scopes_explicit_client` - Uses specified client when provided
- [ ] Test: `test_find_all_server_scopes_invalid_client` - Returns empty list for invalid client
- [ ] Test: `test_find_all_server_scopes_error_handling` - Returns empty list on exception, logs error
- [ ] All tests use proper mocking (don't require real client)
- [ ] All tests verify returned dict structure (client, scope, qualified_id keys)
- [ ] All tests pass with pytest -v

### Technical Notes

**File**: `tests/test_manager.py` (or create new file `tests/test_manager_find_scopes.py`)
**Test Framework**: pytest with unittest.mock
**Mocking Strategy**: Mock `self.registry.get_client()` and `client.list_servers()`

**Test Structure Example**:
```python
def test_find_all_server_scopes_single_match(self, mock_manager):
    """Test auto-detection with server in exactly one scope."""
    # Setup
    mock_client = MagicMock()
    mock_client.list_servers.return_value = {
        "claude-code:project-mcp:my-server": ServerInfo(
            id="my-server",
            client="claude-code",
            scope="project-mcp",
            config={"command": "node", "args": ["server.js"]},
            state=ServerState.ENABLED
        )
    }
    mock_manager.registry.get_client.return_value = mock_client

    # Execute
    result = mock_manager.find_all_server_scopes("my-server", "claude-code")

    # Verify
    assert len(result) == 1
    assert result[0]["client"] == "claude-code"
    assert result[0]["scope"] == "project-mcp"
    assert "qualified_id" in result[0]
```

**Coverage Target**: 100% of find_all_server_scopes() method

---

## [P0-5] Add Integration Tests for Auto-Detection

**Status**: Not Started
**Effort**: Medium (1-1.5 hours)
**Dependencies**: P0-1, P0-2, P0-3 (full implementation must be complete)
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 4.2 • **Status Reference**: STATUS-2025-10-30-062049.md

### Description

Add integration tests for the rescope command's auto-detection feature. These tests verify the end-to-end behavior of the CLI command with the new auto-detection logic, covering all three cases (not found, single scope, multiple scopes) plus backward compatibility.

These are the critical tests that prove the feature works correctly from the user's perspective.

### Acceptance Criteria

**Test 1: Auto-detect Single Scope** (`test_rescope_auto_detect_single_scope`)
- [ ] Server installed in project-mcp scope only
- [ ] Command: `mcpi rescope my-server --to user-global` (no --from)
- [ ] Auto-detects project-mcp as source
- [ ] Shows message: "Auto-detected source scope: project-mcp"
- [ ] Successfully moves server to user-global
- [ ] Server no longer in project-mcp, now in user-global
- [ ] Success message shows correct source and destination

**Test 2: Auto-detect Not Found** (`test_rescope_auto_detect_not_found`)
- [ ] Server doesn't exist in any scope
- [ ] Command: `mcpi rescope nonexistent --to user-global`
- [ ] Shows error: "Server 'nonexistent' not found in any scope"
- [ ] Shows tip about running `mcpi list`
- [ ] Exits with code 1
- [ ] No configuration files modified

**Test 3: Auto-detect Multiple Scopes** (`test_rescope_auto_detect_multiple_scopes`)
- [ ] Server installed in both project-mcp AND project-local scopes
- [ ] Command: `mcpi rescope my-server --to user-global` (no --from)
- [ ] Shows error: "Server 'my-server' exists in 2 scopes:"
- [ ] Lists both scopes (numbered)
- [ ] Shows guidance to use --from
- [ ] Shows example command
- [ ] Exits with code 1
- [ ] No configuration files modified

**Test 4: Backward Compatibility** (`test_rescope_backward_compat_explicit_from`)
- [ ] Server installed in project-mcp scope
- [ ] Command: `mcpi rescope my-server --from project-mcp --to user-global` (explicit --from)
- [ ] Works exactly as before (no auto-detection messages)
- [ ] Successfully moves server
- [ ] Output shows source as project-mcp

**Test 5: Dry-Run with Auto-detect** (`test_rescope_auto_detect_dry_run`)
- [ ] Server in project-mcp scope
- [ ] Command: `mcpi rescope my-server --to user-global --dry-run`
- [ ] Shows auto-detected scope
- [ ] Shows "Would move..." message
- [ ] No configuration files modified
- [ ] Exits successfully

**General Requirements**:
- [ ] All tests use test harness pattern (isolated config files)
- [ ] All tests verify file system state (config files modified/not modified)
- [ ] All tests verify console output (messages match expected)
- [ ] All tests clean up after themselves
- [ ] All tests pass in CI/CD environment

### Technical Notes

**File**: `tests/test_cli_rescope.py` (add to existing file)
**Test Framework**: pytest with test harness (mcp_harness fixture)
**Pattern**: Follow existing rescope tests structure

**Existing Tests to Verify Still Pass**:
- Lines 229-260: `test_rescope_server_not_in_source` (may need adjustment)
- Lines 308-340: `test_rescope_invalid_source_scope` (conditional on --from)
- All 34 existing rescope tests should still pass

**Test Harness Usage**:
```python
def test_rescope_auto_detect_single_scope(mcp_harness):
    """Test auto-detection with server in exactly one scope."""
    # Setup: Add server to project-mcp
    mcp_harness.add_server(
        "my-server",
        scope="project-mcp",
        config={"command": "node", "args": ["server.js"]}
    )

    # Execute: Rescope without --from
    result = mcp_harness.run_cli(
        ["rescope", "my-server", "--to", "user-global"]
    )

    # Verify: Auto-detected and moved
    assert result.exit_code == 0
    assert "Auto-detected source scope: project-mcp" in result.output
    assert mcp_harness.server_exists("my-server", "user-global")
    assert not mcp_harness.server_exists("my-server", "project-mcp")
```

**Coverage Target**: 100% of new auto-detection code paths

---

## [P0-6] Update Existing Tests for Optional --from

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: P0-2, P0-3 (implementation changes that affect tests)
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 4.1 • **Status Reference**: STATUS-2025-10-30-062049.md

### Description

Update 2 existing rescope tests that are affected by making --from optional:
1. `test_rescope_server_not_in_source` - Error message changes when auto-detect finds no servers
2. `test_rescope_invalid_source_scope` - Only relevant when --from is explicitly provided

These tests may need updated assertions or may need to be split into separate cases for explicit --from vs. auto-detect.

### Acceptance Criteria

- [ ] `test_rescope_server_not_in_source` updated for auto-detect error message
  - If test uses --from: Still works, verifies "not found in source" error
  - If test omits --from: Updated to verify "not found in any scope" error
- [ ] `test_rescope_invalid_source_scope` still works with explicit --from
- [ ] All 34 existing rescope tests still pass after changes
- [ ] No tests are unnecessarily duplicated
- [ ] Test names accurately reflect what they test

### Technical Notes

**File**: `tests/test_cli_rescope.py`
**Lines to Review**:
- Line 229: `test_rescope_server_not_in_source`
- Line 308: `test_rescope_invalid_source_scope`

**Strategy**:
1. Run existing tests after P0-3 implementation
2. Identify which tests fail
3. Update assertions to match new behavior
4. Consider if test should be split (explicit --from vs. auto-detect paths)

**Example Update**:
```python
# Before
def test_rescope_server_not_in_source(mcp_harness):
    result = mcp_harness.run_cli(
        ["rescope", "nonexistent", "--from", "project-mcp", "--to", "user-global"]
    )
    assert "Server 'nonexistent' not found in scope 'project-mcp'" in result.output

# After (if test uses explicit --from)
def test_rescope_server_not_in_source_explicit_from(mcp_harness):
    result = mcp_harness.run_cli(
        ["rescope", "nonexistent", "--from", "project-mcp", "--to", "user-global"]
    )
    assert "Server 'nonexistent' not found in scope 'project-mcp'" in result.output

# New test for auto-detect path
def test_rescope_server_not_found_auto_detect(mcp_harness):
    result = mcp_harness.run_cli(
        ["rescope", "nonexistent", "--to", "user-global"]
    )
    assert "Server 'nonexistent' not found in any scope" in result.output
```

---

## [P0-7] Update Documentation

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: P0-1, P0-2, P0-3 (implementation must be complete)
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 5.3 • **Status Reference**: STATUS-2025-10-30-062049.md

### Description

Update project documentation to reflect the new auto-detection capability:
1. **CLAUDE.md**: Add command examples showing auto-detection
2. **README.md**: Update rescope command examples with both explicit and auto-detect syntax
3. **Inline help**: Already updated by P0-2 (--from help text)

Documentation should clearly show:
- New simpler syntax (without --from)
- When --from is still needed (multi-scope case)
- Backward compatibility (--from still works)

### Acceptance Criteria

**CLAUDE.md Updates**:
- [ ] Add section showing rescope auto-detection example
- [ ] Show both explicit --from and auto-detect syntax
- [ ] Note about multi-scope edge case
- [ ] Example commands are accurate and tested

**README.md Updates**:
- [ ] Update rescope command section (likely around line 95-96)
- [ ] Show simple case: `mcpi rescope my-server --to user-global`
- [ ] Show explicit case: `mcpi rescope my-server --from project-mcp --to user-global`
- [ ] Note that --from is optional (auto-detected when possible)
- [ ] Mention multi-scope case requires explicit --from

**General**:
- [ ] All example commands are syntactically correct
- [ ] All example commands have been manually tested
- [ ] Formatting is consistent with existing docs
- [ ] No typos or grammar errors

### Technical Notes

**Files to Update**:
1. `/Users/bmf/icode/mcpi/CLAUDE.md` (lines 115-120, add new examples)
2. `/Users/bmf/icode/mcpi/README.md` (lines 95-96, update existing examples)

**Example Documentation Text**:

For CLAUDE.md:
```markdown
### Rescope Command

Move servers between scopes (user-global, project-mcp, etc.):

```bash
# Auto-detect source scope (most common usage)
mcpi rescope my-server --to user-global

# Explicitly specify source scope (for multi-scope cases)
mcpi rescope my-server --from project-mcp --to user-global

# Dry-run to preview changes
mcpi rescope my-server --to user-global --dry-run
```

**Note**: When a server exists in multiple scopes, you must explicitly specify
`--from` to indicate which scope to move from.
```

For README.md (update existing section):
```markdown
### Move Servers Between Scopes

```bash
# Auto-detect source scope
mcpi rescope my-server --to user-global

# Explicitly specify source (if server exists in multiple scopes)
mcpi rescope my-server --from project-mcp --to user-global
```
```

---

## [P0-8] Manual Testing and Verification

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: P0-1 through P0-7 (all work must be complete)
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 8.2 • **Status Reference**: STATUS-2025-10-30-062049.md

### Description

Perform comprehensive manual testing of the rescope auto-detection feature to verify:
1. All three auto-detection cases work correctly (not found, single, multiple)
2. Backward compatibility with explicit --from
3. Dry-run mode works correctly
4. Error messages are clear and helpful
5. Success messages show correct information

This is the final verification before considering the feature complete.

### Acceptance Criteria

**Scenario 1: Single Scope Auto-Detect (Happy Path)**
- [ ] Install test server in project-mcp: `mcpi add test-server --scope project-mcp`
- [ ] Rescope without --from: `mcpi rescope test-server --to user-global`
- [ ] Verify shows "Auto-detected source scope: project-mcp"
- [ ] Verify success message
- [ ] Verify `mcpi list` shows server in user-global, not in project-mcp

**Scenario 2: Not Found Error**
- [ ] Try to rescope nonexistent server: `mcpi rescope nonexistent --to user-global`
- [ ] Verify error: "Server 'nonexistent' not found in any scope"
- [ ] Verify tip shown
- [ ] Verify exit code is 1

**Scenario 3: Multiple Scopes Error**
- [ ] Install same server in two scopes:
  - `mcpi add dup-server --scope project-mcp`
  - `mcpi add dup-server --scope project-local`
- [ ] Try to rescope: `mcpi rescope dup-server --to user-global`
- [ ] Verify error: "Server 'dup-server' exists in 2 scopes:"
- [ ] Verify both scopes listed
- [ ] Verify guidance shown with example command
- [ ] Verify exit code is 1

**Scenario 4: Multiple Scopes with Explicit --from (Backward Compat)**
- [ ] With server in two scopes from Scenario 3
- [ ] Rescope with explicit --from: `mcpi rescope dup-server --from project-mcp --to user-global`
- [ ] Verify no auto-detect message (uses explicit source)
- [ ] Verify success
- [ ] Verify server still exists in project-local (not removed from there)

**Scenario 5: Dry-Run Mode**
- [ ] Install server in project-mcp
- [ ] Dry-run rescope: `mcpi rescope test-server --to user-global --dry-run`
- [ ] Verify shows auto-detected scope
- [ ] Verify shows "Would move..." message
- [ ] Verify no actual changes made (run `mcpi list`)

**Scenario 6: Help Text**
- [ ] Run: `mcpi rescope --help`
- [ ] Verify --from shown as optional (not required)
- [ ] Verify help text: "auto-detected if not specified"

**Documentation Verification**:
- [ ] All examples in README.md are accurate
- [ ] All examples in CLAUDE.md are accurate
- [ ] All documented commands work as shown

**Final Checklist**:
- [ ] All manual tests pass
- [ ] No unexpected errors or warnings
- [ ] Console output is clear and professional
- [ ] Performance is acceptable (no noticeable delays)

### Technical Notes

**Test Environment**: Use development installation (`uv tool install --editable .`)

**Cleanup Between Tests**:
```bash
# Remove test servers
mcpi remove test-server --scope project-mcp
mcpi remove test-server --scope user-global
mcpi remove dup-server --scope project-mcp
mcpi remove dup-server --scope project-local
```

**Success Criteria**: All scenarios work as expected with no issues.

---

## P1: Nice-to-Have Enhancements (Defer to Future)

These items improve the feature but are not required for the initial implementation.

---

## [P1-1] Add --all-scopes Flag for Multi-Scope Removal

**Status**: Deferred
**Effort**: Medium (2-3 hours)
**Dependencies**: P0-1 through P0-8 complete
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 9.2

### Description

Add an optional `--all-scopes` flag that explicitly removes the server from ALL scopes and adds it to the target scope. This provides a way to clean up duplicates without requiring manual removal.

**Command syntax**: `mcpi rescope my-server --all-scopes --to user-global`

This is deferred because:
- OPTION B (Conservative) handles the common case (single scope)
- Multi-scope duplication is rare (5% of cases)
- Users can manually remove from extra scopes if needed
- Adds complexity without significant value

---

## [P1-2] Add Interactive Selection for Multi-Scope Case

**Status**: Deferred
**Effort**: Large (4-6 hours)
**Dependencies**: P0-1 through P0-8 complete
**Spec Reference**: RESCOPE-AUTO-DETECT-EVALUATION.md Section 3.1 OPTION C

### Description

Instead of erroring on multi-scope case, show an interactive prompt allowing the user to select which scope(s) to remove from. This provides better UX but adds significant complexity.

**Example interaction**:
```
Server 'my-server' exists in multiple scopes:
  1. project-mcp
  2. project-local

Which scope do you want to move from?
[1-2, or 'a' for all]:
```

This is deferred because:
- Requires rich interactive prompts
- Adds complexity to CLI (not all terminals support interactivity)
- Conflicts with --dry-run and scripting use cases
- OPTION B is simpler and safer
- Low value for rare edge case

---

## Dependency Graph

```
P0-1: Add find_all_server_scopes()
  └─> P0-3: Implement auto-detection (depends on P0-1)
      └─> P0-5: Integration tests (depends on P0-3)
      └─> P0-6: Update existing tests (depends on P0-3)
  └─> P0-4: Unit tests (depends on P0-1)

P0-2: Make --from optional
  └─> P0-3: Implement auto-detection (uses optional --from)

P0-3: Implement auto-detection
  └─> P0-7: Documentation (depends on implementation)
  └─> P0-8: Manual testing (depends on everything)

P0-4, P0-5, P0-6: All tests
  └─> P0-8: Manual testing (verify all tests pass)

P0-7: Documentation
  └─> P0-8: Manual testing (verify examples work)
```

**Critical Path**: P0-1 → P0-3 → P0-5 → P0-8 (3.5 hours minimum)

**Parallelization Opportunities**:
- P0-2 can be done independently early
- P0-4 and P0-5 can be done in parallel if P0-1 and P0-3 are complete
- P0-7 can be written in parallel with P0-5/P0-6

---

## Recommended Sprint Planning

### Sprint 1: Implementation and Core Testing (3-4 hours)

**Session 1: Core Implementation** (1.5 hours)
1. P0-1: Add find_all_server_scopes() method (30 min)
2. P0-2: Make --from optional (15 min)
3. P0-3: Implement auto-detection logic (1-1.5 hours)
4. Quick smoke test: Verify basic functionality works

**Session 2: Testing** (1.5-2 hours)
1. P0-4: Unit tests for find_all_server_scopes() (30 min)
2. P0-5: Integration tests for auto-detection (1-1.5 hours)
3. P0-6: Update existing tests (30 min)
4. Run full test suite: `pytest tests/test_cli_rescope.py -v`

### Sprint 2: Documentation and Verification (0.5-1 hour)

**Session 3: Finalization** (0.5-1 hour)
1. P0-7: Update documentation (30 min)
2. P0-8: Manual testing and verification (30 min)
3. Code quality: `black src/ tests/ && ruff check src/ tests/`
4. Final test run: `pytest -v`

**Total Time**: 3.5-5 hours over 1-2 sessions

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Multi-scope edge case surprises users | Low | Medium | Clear error message, require --from | Mitigated by OPTION B |
| Backward compatibility break | Very Low | High | Keep --from optional, test existing scripts | No break - additive change |
| Transaction rollback fails | Very Low | Medium | Existing rollback logic tested | Low risk - reuses proven code |
| Performance degradation | Very Low | Low | list_servers() already called | No new bottlenecks |
| Test coverage gaps | Low | Medium | Comprehensive test plan (6 new tests) | Addressed in P0-4, P0-5, P0-6 |

### User Experience Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Confusion about auto-detection | Medium | Low | Clear console output showing detected scope | Addressed in P0-3 |
| Unexpected behavior with duplicates | Low | High | Error on multi-scope, require explicit --from | Mitigated by OPTION B |
| Loss of explicit control | Low | Medium | Keep --from available for power users | Addressed - still optional |

### Quality Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Inadequate testing | Low | High | 6 new tests + 2 updated tests | Addressed in testing tasks |
| Regression in existing tests | Very Low | Medium | Run full test suite, verify 34 tests pass | Addressed in P0-6 |
| Documentation outdated | Medium | Low | Update docs as part of implementation | Addressed in P0-7 |

**Overall Risk Level**: **LOW** - Conservative approach, well-tested, backward compatible

---

## Success Criteria

### Must Have (Required for Completion)

- [ ] `find_all_server_scopes()` method implemented and tested
- [ ] Auto-detection works for single-scope case (95% of usage)
- [ ] Clear error for multi-scope case (5% edge case)
- [ ] Clear error for not-found case
- [ ] `--from` remains optional for backward compatibility
- [ ] All 34 existing rescope tests still pass
- [ ] 6 new tests added and passing (4 integration + 2+ unit)
- [ ] Documentation updated (CLAUDE.md, README.md)
- [ ] Manual testing complete with all scenarios verified
- [ ] No regressions in existing functionality

### Should Have (Strong Recommendations)

- [ ] Console output clearly indicates auto-detection occurred
- [ ] Dry-run mode shows detected scope
- [ ] Help text accurately describes new behavior
- [ ] Error messages are actionable with examples
- [ ] Code follows existing patterns and style
- [ ] Type hints are complete and accurate

### Nice to Have (Future Enhancements)

- [ ] `--all-scopes` flag for removing from multiple scopes (P1-1)
- [ ] Interactive selection for multi-scope case (P1-2)
- [ ] Metrics/telemetry for auto-detection usage

---

## Quality Standards

### Code Quality

- **Style**: Follow Black formatting (run `black src/ tests/`)
- **Linting**: Pass Ruff checks (run `ruff check src/ tests/`)
- **Type Hints**: Complete type annotations, pass mypy (run `mypy src/`)
- **Documentation**: Comprehensive docstrings with examples
- **Error Handling**: Graceful error handling with logging
- **Consistency**: Follow existing patterns in codebase

### Testing Quality

- **Coverage**: 100% coverage of new code paths
- **Test Types**: Both unit tests (isolated) and integration tests (end-to-end)
- **Test Quality**: Tests verify real functionality, not tautological
- **Edge Cases**: All three auto-detection cases covered
- **Backward Compat**: Existing tests verify --from still works
- **CI/CD**: All tests pass in automated environment

### Documentation Quality

- **Accuracy**: All examples tested and verified
- **Completeness**: Both simple and advanced usage documented
- **Clarity**: Clear explanation of when auto-detection applies
- **Examples**: Multiple examples showing different scenarios

---

## File Checklist

### Files to Modify

- [ ] `src/mcpi/clients/manager.py` - Add find_all_server_scopes() method
- [ ] `src/mcpi/cli.py` - Make --from optional, add auto-detection logic
- [ ] `tests/test_cli_rescope.py` - Add integration tests, update existing tests
- [ ] `tests/test_manager.py` - Add unit tests for new method
- [ ] `CLAUDE.md` - Add command examples
- [ ] `README.md` - Update rescope examples

### Files to Verify (No Changes Expected)

- [ ] `src/mcpi/clients/base.py` - No changes (uses existing methods)
- [ ] `src/mcpi/clients/protocols.py` - No changes
- [ ] `pyproject.toml` - No changes
- [ ] `.github/workflows/test.yml` - No changes (tests run automatically)

---

## Acceptance Testing Checklist

Before marking this feature complete, verify:

### Functional Testing

- [ ] Auto-detect works when server in one scope
- [ ] Error shown when server not found
- [ ] Error shown when server in multiple scopes
- [ ] Explicit --from still works (backward compatibility)
- [ ] Dry-run mode works with auto-detection
- [ ] All scope types work (project-mcp, project-local, user-global, user-app-specific)
- [ ] Multi-client scenarios work (when using --client)

### Quality Testing

- [ ] All 40+ rescope tests pass (34 existing + 6 new)
- [ ] Code coverage for rescope command > 90%
- [ ] Black, Ruff, mypy all pass
- [ ] No TODO or FIXME comments left
- [ ] No debugging print statements left

### Documentation Testing

- [ ] README.md examples work as shown
- [ ] CLAUDE.md examples work as shown
- [ ] Help text accurate: `mcpi rescope --help`
- [ ] Error messages are helpful and actionable

### User Experience Testing

- [ ] Console output is clear and professional
- [ ] Auto-detection message is visible but not intrusive
- [ ] Error messages guide user to solution
- [ ] Success messages show correct information
- [ ] No confusing or ambiguous output

---

## Lessons from Previous Work

Based on STATUS-2025-10-30-062049.md findings:

### What to Avoid

1. **Don't assume tests passing = feature working**
   - Manual test all scenarios after implementation
   - Verify end-to-end functionality, not just unit tests

2. **Don't skip documentation updates**
   - Update docs as part of feature, not after
   - Test all documented examples

3. **Don't dismiss edge cases**
   - Multi-scope case is rare but must be handled correctly
   - Test error paths thoroughly

4. **Don't leave test harness issues**
   - Ensure tests don't mask real failures
   - Verify tests actually exercise the feature

### What to Do

1. **Manual testing is critical**
   - P0-8 is not optional
   - Verify all scenarios work as expected

2. **Comprehensive test coverage**
   - Both unit and integration tests
   - Test happy path AND error cases

3. **Clear, actionable error messages**
   - Show user what went wrong
   - Show user how to fix it

4. **Documentation accuracy**
   - Keep docs aligned with implementation
   - Verify examples work before publishing

---

## Next Actions

1. **Review this backlog** with stakeholders
2. **Confirm OPTION B approach** (error on multi-scope) vs. OPTION A (remove from all)
3. **Start with P0-1**: Implement find_all_server_scopes() method
4. **Follow dependency order**: Complete P0-1 before P0-3, etc.
5. **Don't skip P0-8**: Manual testing is required before completion

---

## Notes

- **Estimated Total Time**: 3.5-5.5 hours (implementation + testing + docs)
- **Confidence**: High (85%) - well-understood problem, existing patterns to follow
- **Risk**: Low - conservative approach, backward compatible
- **Value**: High - better UX for 95% of users, no downside for power users

**This is a well-scoped, low-risk enhancement with clear acceptance criteria and a proven implementation path.**
