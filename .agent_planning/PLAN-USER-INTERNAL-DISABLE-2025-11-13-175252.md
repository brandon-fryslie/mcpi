# Implementation Plan: Enable/Disable Support for user-internal Scope

**Date**: 2025-11-13 17:52:52
**Planner**: Claude Code (Product Backlog Specialist)
**Source STATUS**: STATUS-2025-11-13-DISABLE-EVALUATION.md
**Source Spec**: CLAUDE.md (Dependency Inversion Principle section)
**Priority**: P1 (HIGH) - User-requested feature
**Total Effort**: 2-3 hours
**Risk Level**: LOW

---

## Provenance

**Generated From**:
- STATUS File: `.agent_planning/STATUS-2025-11-13-DISABLE-EVALUATION.md`
- User Request: "Fix mcpi disable command for user-internal scope"
- Spec Version: CLAUDE.md (DIP Phase 1 complete)
- Generation Time: 2025-11-13 17:52:52

**Architectural Decision**: Option D (Hybrid) - Add FileTrackedEnableDisableHandler to user-internal scope AND improve documentation

---

## Executive Summary

**Problem**: The `user-internal` scope (~/.claude.json) currently does NOT support enable/disable operations, returning an error when users attempt to disable servers in this scope.

**Root Cause**: Design decision - `enable_disable_handler=None` explicitly set for user-internal scope (line 178 in `src/mcpi/clients/claude_code.py`)

**Solution**: Implement FileTrackedEnableDisableHandler for user-internal scope (same pattern as user-global), using separate tracking file `~/.claude/.mcpi-disabled-servers-internal.json`

**User Impact**:
- ✅ Users can now disable servers in user-internal scope
- ✅ No breaking changes (additive only)
- ✅ Consistent behavior across all user-level scopes
- ✅ No migration required

**Success Metrics**:
- `mcpi disable <server>` works for user-internal servers
- State correctly tracked in separate file
- All tests pass (existing + new)
- Documentation explains all scope mechanisms

---

## Work Items

### P1-1: Add FileTrackedEnableDisableHandler to user-internal Scope

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: None
**Spec Reference**: CLAUDE.md § Enable/Disable Mechanisms • **Status Reference**: STATUS-2025-11-13-DISABLE-EVALUATION.md § 7.2 Implementation Steps

#### Description

Modify the user-internal scope initialization in `ClaudeCodePlugin` to use `FileTrackedEnableDisableHandler` instead of `None`. This will enable enable/disable operations for servers in ~/.claude.json by tracking disabled state in a separate file.

#### Acceptance Criteria

- [ ] user-internal scope initialized with FileTrackedEnableDisableHandler
- [ ] Tracking file path: `~/.claude/.mcpi-disabled-servers-internal.json`
- [ ] Path override support maintained for testing (path_overrides["user-internal-disabled"])
- [ ] Code comment updated to explain "supports enable/disable via tracking file"
- [ ] No changes to ~/.claude.json file format
- [ ] Pattern identical to user-global implementation

#### Technical Notes

**File**: `src/mcpi/clients/claude_code.py`
**Lines to modify**: 162-179 (user-internal scope definition)

**Implementation**:
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
    enable_disable_handler=FileTrackedEnableDisableHandler(  # CHANGED from None
        DisabledServersTracker(user_internal_disabled_tracker_path)
    ),
)
```

**Key Changes**:
1. Add `user_internal_disabled_tracker_path` variable
2. Use `self._get_scope_path("user-internal-disabled", ...)` for override support
3. Replace `enable_disable_handler=None` with `FileTrackedEnableDisableHandler(...)`
4. Update comment from "doesn't support enable/disable" to "supports enable/disable via tracking file"

**Reuses**: Existing FileTrackedEnableDisableHandler and DisabledServersTracker classes (no new code needed)

---

### P1-2: Add Functional Tests for user-internal Enable/Disable

**Status**: Not Started
**Effort**: Medium (1 hour)
**Dependencies**: P1-1
**Spec Reference**: CLAUDE.md § Testing Strategy • **Status Reference**: STATUS-2025-11-13-DISABLE-EVALUATION.md § 7.2 Step 2

#### Description

Create comprehensive functional tests for user-internal scope enable/disable operations following the established testing pattern from `test_enable_disable_bugs.py`. Tests must be un-gameable (real file I/O, no mocks) and verify actual behavior.

#### Acceptance Criteria

- [ ] Test class `TestUserInternalEnableDisable` created
- [ ] Minimum 3 tests implemented:
  - [ ] test_user_internal_disable_server_creates_tracking_file
  - [ ] test_user_internal_enable_server_removes_from_tracking_file
  - [ ] test_user_internal_disabled_server_shows_correct_state
- [ ] All tests use MCPTestHarness (no mocks)
- [ ] Tests verify actual file contents
- [ ] Tests verify ServerState values
- [ ] All new tests pass (100%)
- [ ] No regressions in existing tests

#### Technical Notes

**File**: `tests/test_enable_disable_bugs.py`
**Location**: Add at end of file (after existing test classes)

**Test Pattern** (copy from user-global tests):

```python
class TestUserInternalEnableDisable:
    """Test enable/disable for user-internal scope using file tracking.

    user-internal scope uses FileTrackedEnableDisableHandler with tracking file
    at ~/.claude/.mcpi-disabled-servers-internal.json (separate from config file).
    """

    @pytest.fixture
    def plugin(self, mcp_harness):
        """Create a ClaudeCodePlugin with test harness."""
        return ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)

    def test_user_internal_disable_server_creates_tracking_file(
        self, plugin, mcp_harness
    ):
        """Test that disabling user-internal server creates tracking file.

        Why this test is un-gameable:
        - Creates actual config file in temp directory
        - Verifies tracking file is created on disable
        - Checks actual JSON content of tracking file
        - Uses real plugin.disable_server() method
        """
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

        # Verify setup
        config_data = mcp_harness.read_scope_file("user-internal")
        assert "test-server" in config_data["mcpServers"]

        # Execute: Disable the server
        result = plugin.disable_server("test-server")

        # Verify: Operation succeeded
        assert result.success, f"Failed to disable server: {result.message}"

        # Verify: Tracking file was created
        tracking_path = mcp_harness.path_overrides["user-internal-disabled"]
        assert tracking_path.exists(), "Tracking file was not created"

        # Verify: Server is in tracking file
        import json
        with tracking_path.open("r") as f:
            disabled = json.load(f)
        assert "test-server" in disabled, "Server not in tracking file"

        # Verify: Original config unchanged
        config_data = mcp_harness.read_scope_file("user-internal")
        assert "test-server" in config_data["mcpServers"], "Server removed from config"

    def test_user_internal_enable_server_removes_from_tracking_file(
        self, plugin, mcp_harness
    ):
        """Test that enabling user-internal server removes from tracking file."""
        # Setup: Install server and mark as disabled
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

        # Disable first
        result = plugin.disable_server("test-server")
        assert result.success

        # Verify server is disabled
        tracking_path = mcp_harness.path_overrides["user-internal-disabled"]
        assert tracking_path.exists()

        import json
        with tracking_path.open("r") as f:
            disabled = json.load(f)
        assert "test-server" in disabled

        # Execute: Enable the server
        result = plugin.enable_server("test-server")

        # Verify: Operation succeeded
        assert result.success, f"Failed to enable server: {result.message}"

        # Verify: Server removed from tracking file
        with tracking_path.open("r") as f:
            disabled = json.load(f)
        assert "test-server" not in disabled, "Server still in tracking file"

    def test_user_internal_disabled_server_shows_correct_state(
        self, plugin, mcp_harness
    ):
        """Test that list_servers shows correct state for disabled user-internal server."""
        # Setup: Install server
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

        # Verify: Initially ENABLED
        servers = plugin.list_servers(scope="user-internal")
        qualified_id = "claude-code:user-internal:test-server"
        assert qualified_id in servers
        assert servers[qualified_id].state == ServerState.ENABLED

        # Execute: Disable the server
        result = plugin.disable_server("test-server")
        assert result.success

        # Verify: Now shows as DISABLED
        servers = plugin.list_servers(scope="user-internal")
        assert qualified_id in servers
        assert servers[qualified_id].state == ServerState.DISABLED, (
            f"Expected DISABLED, got {servers[qualified_id].state}"
        )

        # Execute: Enable the server
        result = plugin.enable_server("test-server")
        assert result.success

        # Verify: Back to ENABLED
        servers = plugin.list_servers(scope="user-internal")
        assert qualified_id in servers
        assert servers[qualified_id].state == ServerState.ENABLED
```

**Test Quality Criteria**:
- ✅ USEFUL: Tests real functionality users care about
- ✅ COMPLETE: Covers disable, enable, and state checking
- ✅ FLEXIBLE: Uses test harness, not tied to implementation details
- ✅ AUTOMATED: Fully automated, no manual steps

**Additional Tests** (optional, time permitting):
- test_user_internal_idempotent_disable (disable twice = same result)
- test_user_internal_idempotent_enable (enable twice = same result)
- test_user_internal_scope_isolation (doesn't affect other scopes)

---

### P1-3: Update Documentation for Enable/Disable Mechanisms

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: P1-1, P1-2
**Spec Reference**: CLAUDE.md § Enable/Disable Mechanisms • **Status Reference**: STATUS-2025-11-13-DISABLE-EVALUATION.md § 7.2 Step 3

#### Description

Add comprehensive documentation to CLAUDE.md explaining the enable/disable mechanisms used by different scopes. This helps users understand which scopes support enable/disable and how they work.

#### Acceptance Criteria

- [ ] New section added to CLAUDE.md: "Enable/Disable Mechanisms by Scope"
- [ ] Documents array-based mechanism (project-local, user-local)
- [ ] Documents file-tracked mechanism (user-global, user-internal)
- [ ] Documents scopes without support (project-mcp, user-mcp)
- [ ] Includes code examples for each mechanism
- [ ] Provides guidance on choosing the right scope
- [ ] Mentions tracking file locations
- [ ] Clear explanation of when to use which scope

#### Technical Notes

**File**: `CLAUDE.md`
**Location**: Add new section under "## Project Architecture" (after "Scope-Based Configuration")

**Content Structure**:
1. **Introduction**: Brief overview of enable/disable feature
2. **Array-Based Scopes**: project-local, user-local (with example)
3. **File-Tracked Scopes**: user-global, user-internal (with example)
4. **No Support Scopes**: project-mcp, user-mcp (with reason)
5. **Choosing a Scope**: Guidance table
6. **Tracking Files**: List of all tracking files and their purposes

**Example Section** (see STATUS § 7.2 Step 3 for full content):
```markdown
### Enable/Disable Mechanisms by Scope

MCPI supports enabling and disabling MCP servers to control which ones are active
without removing their configurations. Different scopes use different mechanisms:

#### Scopes with Array-Based Enable/Disable

**Scopes**: project-local, user-local
...
```

**Quality Standard**: Documentation should be clear enough that a new user can understand which scope to use and how enable/disable works without reading code.

---

### P1-4: Manual Verification and CLI Testing

**Status**: Not Started
**Effort**: Small (20 minutes)
**Dependencies**: P1-1, P1-2
**Spec Reference**: None • **Status Reference**: STATUS-2025-11-13-DISABLE-EVALUATION.md § 7.2 Step 5

#### Description

Perform manual end-to-end testing of the enable/disable functionality for user-internal scope to verify it works in a real user environment. This catches integration issues that automated tests might miss.

#### Acceptance Criteria

- [ ] Install a server in user-internal scope
- [ ] Verify server shows as ENABLED in `mcpi list`
- [ ] Disable server using `mcpi disable`
- [ ] Verify server shows as DISABLED in `mcpi list`
- [ ] Verify tracking file created at correct path
- [ ] Verify tracking file contains server ID
- [ ] Enable server using `mcpi enable`
- [ ] Verify server shows as ENABLED again
- [ ] Verify tracking file updated (server removed)
- [ ] Verify ~/.claude.json unchanged throughout

#### Technical Notes

**Test Procedure**:
```bash
# 1. Install server in user-internal
mcpi add test-server --scope user-internal --command npx --args "-y,test-server"

# 2. Verify initial state
mcpi list --scope user-internal
# Expected: test-server shows as ENABLED

# 3. Disable server
mcpi disable test-server

# 4. Verify disabled state
mcpi list --scope user-internal
# Expected: test-server shows as DISABLED

# 5. Check tracking file
cat ~/.claude/.mcpi-disabled-servers-internal.json
# Expected: ["test-server"]

# 6. Verify config unchanged
cat ~/.claude.json | jq '.mcpServers."test-server"'
# Expected: Server config still present

# 7. Enable server
mcpi enable test-server

# 8. Verify enabled state
mcpi list --scope user-internal
# Expected: test-server shows as ENABLED

# 9. Check tracking file updated
cat ~/.claude/.mcpi-disabled-servers-internal.json
# Expected: [] or file empty/deleted

# 10. Cleanup
mcpi remove test-server --scope user-internal
```

**Why Manual Testing**:
- Validates real CLI user experience
- Catches issues with argument parsing
- Verifies file permissions work correctly
- Tests actual user workflow
- Confirms output formatting is correct

**If Issues Found**: Fix and retest before considering work complete

---

## Dependency Graph

```
P1-1 (Code Change)
  ↓
P1-2 (Tests) ← depends on P1-1
  ↓
P1-3 (Docs) ← depends on P1-1, P1-2
  ↓
P1-4 (Manual Verification) ← depends on P1-1, P1-2
```

**Execution Order**:
1. P1-1: Implement code change (30 min)
2. P1-2: Write and run tests (1 hour)
3. P1-3: Update documentation (30 min)
4. P1-4: Manual verification (20 min)

**Parallel Opportunities**: None (all items are sequential)

---

## Risk Assessment

### Technical Risks

**Risk 1: Handler Instantiation Failure**
- **Likelihood**: Very Low
- **Impact**: High (feature won't work)
- **Mitigation**: Reusing proven FileTrackedEnableDisableHandler pattern
- **Detection**: Tests will fail immediately
- **Contingency**: Roll back change, investigate why pattern doesn't work

**Risk 2: Path Override Not Working in Tests**
- **Likelihood**: Low
- **Impact**: Medium (tests fail but feature works)
- **Mitigation**: Follow exact pattern from user-global scope
- **Detection**: Tests fail with file permission errors or wrong paths
- **Contingency**: Debug path_overrides dictionary in test harness

**Risk 3: Tracking File Conflicts**
- **Likelihood**: Very Low
- **Impact**: Low (multiple tracking files)
- **Mitigation**: Use unique filename (.mcpi-disabled-servers-internal.json)
- **Detection**: Manual inspection of ~/.claude/ directory
- **Contingency**: Document all tracking files in docs

### User Impact Risks

**Risk 4: Existing user-internal Servers Break**
- **Likelihood**: None (not a breaking change)
- **Impact**: N/A
- **Mitigation**: Additive change only, no file format changes
- **Detection**: N/A
- **Contingency**: N/A

**Risk 5: User Confusion About Tracking Files**
- **Likelihood**: Low
- **Impact**: Low (users ask questions)
- **Mitigation**: Clear documentation explaining mechanism
- **Detection**: User complaints or questions
- **Contingency**: Add FAQ section to docs

### Maintenance Risks

**Risk 6: Extra Tracking File to Maintain**
- **Likelihood**: Certain (inherent to solution)
- **Impact**: Very Low (one more file)
- **Mitigation**: Document file purpose, add to .gitignore patterns
- **Detection**: N/A (expected)
- **Contingency**: Could consolidate in future if needed

**Overall Risk Level**: **LOW**

All risks are low probability or low impact. The highest risk (handler instantiation failure) is very unlikely because we're reusing a proven pattern.

---

## Testing Strategy

### Test Coverage Requirements

**Functional Test Coverage**:
- ✅ Disable operation creates tracking file
- ✅ Disable operation adds server to tracking file
- ✅ Disable operation doesn't modify config file
- ✅ Enable operation removes server from tracking file
- ✅ Enable operation doesn't modify config file
- ✅ list_servers shows correct state (ENABLED/DISABLED)
- ✅ Idempotent operations (disable twice, enable twice)

**Integration Test Coverage**:
- ✅ Works with MCPTestHarness
- ✅ Works with path_overrides for testing
- ✅ Works with real file system
- ✅ Works through CLI commands

**Regression Test Coverage**:
- ✅ Existing enable/disable tests still pass
- ✅ Other scopes unaffected
- ✅ No cross-scope pollution

### Test Quality Criteria (from CLAUDE.md)

**USEFUL**: ✅ Tests verify actual user-facing behavior (disable/enable/list)
**COMPLETE**: ✅ Covers all critical paths (disable, enable, state checking)
**FLEXIBLE**: ✅ Uses test harness, not tied to implementation
**AUTOMATED**: ✅ Fully automated, runs in CI/CD

### Test Execution Plan

**Development**:
```bash
# Run new tests only (fast feedback)
pytest tests/test_enable_disable_bugs.py::TestUserInternalEnableDisable -v

# Run all enable/disable tests (verify no regressions)
pytest tests/test_enable_disable_bugs.py -v

# Run full test suite
pytest -v
```

**CI/CD**: Existing GitHub Actions workflow will automatically run all tests

**Success Criteria**:
- All new tests pass (100%)
- All existing tests still pass (no regressions)
- Test coverage for user-internal scope matches user-global scope

---

## Success Criteria

### Feature Success

**Primary Goals**:
- [ ] `mcpi disable <server>` works for user-internal servers (no error)
- [ ] `mcpi enable <server>` works for user-internal servers (no error)
- [ ] `mcpi list --scope user-internal` shows correct state (ENABLED/DISABLED)
- [ ] Tracking file created at `~/.claude/.mcpi-disabled-servers-internal.json`
- [ ] ~/.claude.json file format unchanged

**User Experience**:
- [ ] Error message "Scope 'user-internal' does not support enable/disable operations" is gone
- [ ] Consistent behavior across all user-level scopes (user-local, user-global, user-internal)
- [ ] Documentation explains how enable/disable works for each scope

### Code Quality

- [ ] Implementation follows existing patterns (FileTrackedEnableDisableHandler)
- [ ] Code is DRY (no duplication)
- [ ] Code is well-commented
- [ ] No new technical debt introduced
- [ ] Type hints maintained

### Test Quality

- [ ] 100% test pass rate (new tests)
- [ ] Zero test regressions
- [ ] Tests follow un-gameable pattern
- [ ] Test coverage equivalent to user-global scope

### Documentation Quality

- [ ] User can understand which scope to use
- [ ] User can understand how enable/disable works
- [ ] Developer can understand the architecture
- [ ] Examples are clear and complete

### Overall Success

**Definition of Done**:
1. All acceptance criteria met (P1-1 through P1-4)
2. All tests passing (new + existing)
3. Manual verification completed successfully
4. Documentation updated and reviewed
5. No regressions introduced
6. User's original problem solved

**Measurement**:
- User can disable servers in user-internal scope
- `mcpi disable` returns success (not error)
- State correctly reflected in `mcpi list`
- Tracking file exists and contains correct data

---

## Timeline and Effort

### Estimated Effort Breakdown

| Work Item | Effort | Time |
|-----------|--------|------|
| P1-1: Code Change | Small | 30 min |
| P1-2: Tests | Medium | 1 hour |
| P1-3: Documentation | Small | 30 min |
| P1-4: Manual Verification | Small | 20 min |
| **Total** | | **2h 20min** |

### Execution Timeline

**Sprint**: Single session (2-3 hours)

**Day 1** (Complete all work):
- Hour 1: P1-1 (code) + P1-2 (tests, first pass)
- Hour 2: P1-2 (tests, complete) + P1-3 (docs)
- Hour 3: P1-4 (manual verification) + cleanup

**Checkpoints**:
- After P1-1: Code compiles, no syntax errors
- After P1-2: All tests passing (new + existing)
- After P1-3: Documentation reviewed
- After P1-4: Manual verification successful

**Blocker Response**:
- If tests fail: Debug immediately, don't proceed to next item
- If manual verification fails: Fix code, re-run tests, re-verify
- If documentation unclear: Revise until clear

---

## Edge Cases and Considerations

### Edge Case 1: Tracking File Already Exists

**Scenario**: `~/.claude/.mcpi-disabled-servers-internal.json` already exists with other servers

**Expected Behavior**:
- Disable operation adds to existing list
- Enable operation removes only target server
- Other servers in list remain unchanged

**Test Coverage**: Covered by idempotent tests

**Risk**: Low (DisabledServersTracker handles this)

---

### Edge Case 2: Server Doesn't Exist in Config

**Scenario**: User tries to disable server that's not in ~/.claude.json

**Expected Behavior**:
- Operation fails with "Server 'X' not found in any scope"
- No tracking file modification

**Test Coverage**: Existing tests cover this (plugin-level validation)

**Risk**: None (already handled)

---

### Edge Case 3: Tracking File Corrupted

**Scenario**: Tracking file contains invalid JSON

**Expected Behavior**:
- DisabledServersTracker._read_disabled_servers returns empty set
- Operations proceed as if file doesn't exist
- Next write overwrites corrupted file

**Test Coverage**: Not explicitly tested (error handling in DisabledServersTracker)

**Risk**: Very Low (file is simple JSON array)

---

### Edge Case 4: Multiple Processes Modifying Tracking File

**Scenario**: Two `mcpi` processes try to disable different servers simultaneously

**Expected Behavior**:
- Last write wins (no file locking)
- One server might not be saved

**Test Coverage**: Not tested (race condition)

**Risk**: Very Low (rare scenario, user can re-run command)

**Future Improvement**: Add file locking if this becomes an issue

---

### Edge Case 5: User Manually Edits Tracking File

**Scenario**: User manually adds/removes server IDs from tracking file

**Expected Behavior**:
- MCPI respects manual edits
- list_servers shows state based on file contents
- Operations work correctly

**Test Coverage**: Not explicitly tested

**Risk**: None (supported use case - file is for manual editing)

---

## Post-Implementation Checklist

After completing all work items:

### Code Review
- [ ] Code follows project style (Black, Ruff, mypy)
- [ ] No hardcoded paths (uses path_overrides)
- [ ] Comments are clear and accurate
- [ ] Type hints are complete
- [ ] No dead code introduced

### Testing
- [ ] All new tests pass locally
- [ ] All existing tests still pass
- [ ] Manual verification completed
- [ ] CI/CD pipeline passes

### Documentation
- [ ] CLAUDE.md updated
- [ ] Code comments accurate
- [ ] Docstrings complete
- [ ] README unchanged (no user-facing changes needed)

### Git Hygiene
- [ ] Commit message follows convention
- [ ] One logical commit (or meaningful breakdown)
- [ ] No unrelated changes included
- [ ] Branch from master/main

### User Communication
- [ ] User informed of completion
- [ ] User provided with usage instructions
- [ ] Any caveats or limitations explained

---

## Future Enhancements (Out of Scope)

These are NOT part of this plan but could be considered later:

### FE-1: Consolidate Tracking Files
**Description**: Merge all tracking files into one with scope prefixes
**Benefit**: Fewer files to manage
**Effort**: 4-6 hours
**Risk**: Medium (migration needed)

### FE-2: Add `mcpi doctor` Command
**Description**: Detect and fix tracking file sync issues
**Benefit**: Better error recovery
**Effort**: 2-3 hours
**Risk**: Low

### FE-3: File Locking for Concurrent Access
**Description**: Add file locking to prevent race conditions
**Benefit**: Safer concurrent operations
**Effort**: 3-4 hours
**Risk**: Medium (OS compatibility)

### FE-4: Tracking File Garbage Collection
**Description**: Auto-remove disabled servers that no longer exist in config
**Benefit**: Cleaner tracking files
**Effort**: 2 hours
**Risk**: Low

---

## Alternatives Considered

### Alternative A: File-Movement-Based Handler

**Description**: Move server configs between enabled and disabled files

**Pros**: Matches user's original mental model exactly

**Cons**:
- Much more complex (4-8 hours vs 2-3 hours)
- Higher risk (file moves can fail)
- Harder to test (more error cases)
- Breaking change (existing configs would need migration)
- Two config files per scope to manage

**Decision**: REJECTED - Complexity and risk not justified when proven pattern exists

---

### Alternative B: No Implementation (Document Only)

**Description**: Keep user-internal without enable/disable, improve docs

**Pros**:
- Zero code changes
- Zero risk
- 1 hour effort (docs only)

**Cons**:
- Doesn't solve user's problem
- User confusion remains
- Need to migrate servers to different scope

**Decision**: REJECTED - User explicitly requested this feature

---

### Alternative C: Array-Based Handler for user-internal

**Description**: Add enabledMcpjsonServers/disabledMcpjsonServers arrays to ~/.claude.json

**Pros**:
- One file (no tracking file)
- Simpler than file tracking

**Cons**:
- Modifies official Claude config format
- May break Claude Code if it doesn't expect these arrays
- Higher risk of breaking official client

**Decision**: REJECTED - Don't modify official Claude formats (same reason user-global uses tracking file)

---

## Related Work

### Completed Work
- ✅ BUG-1: Cross-scope state pollution fixed
- ✅ BUG-3: Wrong scope modification fixed
- ✅ FileTrackedEnableDisableHandler implemented for user-global
- ✅ ArrayBasedEnableDisableHandler implemented for user-local/project-local
- ✅ Test harness supports path_overrides
- ✅ DIP Phase 1 complete

### Concurrent Work
- None (no conflicts)

### Blocked Work
- None (no dependencies)

---

## References

### Source Documents
- `.agent_planning/STATUS-2025-11-13-DISABLE-EVALUATION.md` - Complete evaluation
- `CLAUDE.md` - Project architecture and DIP implementation
- `src/mcpi/clients/claude_code.py` - Scope definitions
- `src/mcpi/clients/enable_disable_handlers.py` - Handler implementations
- `tests/test_enable_disable_bugs.py` - Test patterns

### Key Code Locations
- Scope initialization: `src/mcpi/clients/claude_code.py` lines 62-199
- user-internal scope: `src/mcpi/clients/claude_code.py` lines 162-179
- FileTrackedEnableDisableHandler: `src/mcpi/clients/enable_disable_handlers.py` lines 129-177
- DisabledServersTracker: `src/mcpi/clients/disabled_tracker.py` lines 13-119
- Test pattern: `tests/test_enable_disable_bugs.py` (all test classes)

### External References
- None (internal implementation only)

---

## Appendix: Implementation Checklist

Use this checklist during implementation:

### Before Starting
- [ ] Read STATUS-2025-11-13-DISABLE-EVALUATION.md completely
- [ ] Understand FileTrackedEnableDisableHandler pattern
- [ ] Review user-global scope implementation
- [ ] Set up test environment

### During P1-1 (Code Change)
- [ ] Open src/mcpi/clients/claude_code.py
- [ ] Locate user-internal scope (lines 162-179)
- [ ] Add user_internal_disabled_tracker_path variable
- [ ] Use self._get_scope_path("user-internal-disabled", ...)
- [ ] Replace enable_disable_handler=None with FileTrackedEnableDisableHandler(...)
- [ ] Update code comment
- [ ] Save file
- [ ] Run `black src/mcpi/clients/claude_code.py`
- [ ] Run `ruff check src/mcpi/clients/claude_code.py`
- [ ] Verify no syntax errors

### During P1-2 (Tests)
- [ ] Open tests/test_enable_disable_bugs.py
- [ ] Add TestUserInternalEnableDisable class at end
- [ ] Implement test_user_internal_disable_server_creates_tracking_file
- [ ] Implement test_user_internal_enable_server_removes_from_tracking_file
- [ ] Implement test_user_internal_disabled_server_shows_correct_state
- [ ] Run new tests: `pytest tests/test_enable_disable_bugs.py::TestUserInternalEnableDisable -v`
- [ ] Verify all new tests pass
- [ ] Run all tests: `pytest tests/test_enable_disable_bugs.py -v`
- [ ] Verify no regressions
- [ ] Run full suite: `pytest -v`
- [ ] Verify overall pass rate maintained

### During P1-3 (Documentation)
- [ ] Open CLAUDE.md
- [ ] Locate "## Project Architecture" section
- [ ] Add new subsection "### Enable/Disable Mechanisms by Scope"
- [ ] Document array-based mechanism
- [ ] Document file-tracked mechanism
- [ ] Document no-support scopes
- [ ] Add scope selection guidance
- [ ] Include code examples
- [ ] Save file
- [ ] Run `black CLAUDE.md` (if applicable)
- [ ] Read through docs as if you're a new user
- [ ] Verify clarity and completeness

### During P1-4 (Manual Verification)
- [ ] Install test server in user-internal
- [ ] Verify shows as ENABLED
- [ ] Run disable command
- [ ] Verify shows as DISABLED
- [ ] Check tracking file exists and contains server
- [ ] Run enable command
- [ ] Verify shows as ENABLED
- [ ] Check tracking file updated
- [ ] Verify config file unchanged
- [ ] Remove test server
- [ ] Document any issues found

### After All Work
- [ ] All tests passing
- [ ] Manual verification successful
- [ ] Documentation complete
- [ ] Code formatted and linted
- [ ] Ready to commit

---

**END OF IMPLEMENTATION PLAN**

Generated: 2025-11-13 17:52:52
Author: Claude Code (Product Backlog Specialist)
Project: MCPI (Model Context Protocol Interface)
Priority: P1 (HIGH)
Estimated Effort: 2-3 hours
Risk Level: LOW
Status: READY FOR IMPLEMENTATION
