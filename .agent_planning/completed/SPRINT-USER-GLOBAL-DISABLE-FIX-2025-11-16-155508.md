# Sprint: User-Global Disable/Enable Fix

**Generated**: 2025-11-16-15:55:08
**Plan Reference**: PLAN-USER-GLOBAL-DISABLE-FIX-2025-11-16-155508.md
**Status Source**: STATUS-2025-11-16-USER-GLOBAL-DISABLE-CRITICAL-BUG.md
**Sprint Duration**: 1.5 days (7-10 hours)
**Priority**: P0 - CRITICAL BUG FIX

---

## Sprint Goal

Fix the critical bug where user-global and user-internal MCP server disable/enable functionality doesn't actually disable servers in Claude Code. Replace the broken tracking file approach with a working config file movement approach, validated through E2E tests.

**Definition of Done**:
- Config movement implementation complete
- 34 new tests passing (13 unit, 12 integration, 9 E2E)
- Manual validation checklist 100% complete
- `claude mcp list` verification: disabled servers DO NOT appear
- Zero test regressions
- Documentation updated

---

## Task Breakdown

### PHASE 1: Core Implementation (2-3 hours)

#### Task 1.1: Create ConfigFileMovingHandler [2 hours]
**Priority**: P0 - BLOCKING
**Assignee**: Implementation Agent
**File**: `src/mcpi/clients/enable_disable_handlers.py`

**Subtasks**:
1. [ ] Add class definition and `__init__` method
   - Accept: `active_path`, `disabled_path`, `reader`, `writer`
   - Store paths and I/O dependencies
   - **Time**: 15 min

2. [ ] Implement `_read_file(path) -> Optional[dict]`
   - Handle missing file (return empty structure)
   - Handle JSON errors (return None)
   - **Time**: 15 min

3. [ ] Implement `_write_file(path, data) -> bool`
   - Use atomic writes (temp file + rename)
   - Handle permission errors
   - **Time**: 20 min

4. [ ] Implement `is_disabled(server_id) -> bool`
   - Read disabled file
   - Check if server exists in mcpServers
   - **Time**: 10 min

5. [ ] Implement `disable_server(server_id) -> bool`
   - Read active file
   - Extract server config
   - Read disabled file
   - Add server to disabled file
   - Remove server from active file
   - Write both files atomically
   - **Time**: 30 min

6. [ ] Implement `enable_server(server_id) -> bool`
   - Read disabled file
   - Extract server config
   - Read active file
   - Add server to active file
   - Remove server from disabled file
   - Write both files atomically
   - **Time**: 30 min

**Acceptance Criteria**:
- Class compiles without errors
- All methods have type hints
- Docstrings complete
- Error handling for all edge cases

**Dependencies**: None

---

#### Task 1.2: Update ClaudeCodePlugin Scope Initialization [30 min]
**Priority**: P0 - BLOCKING
**Assignee**: Implementation Agent
**File**: `src/mcpi/clients/claude_code.py`

**Subtasks**:
1. [ ] Update user-global scope (lines ~142-164)
   - Replace `FileTrackedEnableDisableHandler` with `ConfigFileMovingHandler`
   - Update disabled file path: `~/.claude/.disabled-mcp.json`
   - Pass `active_path`, `disabled_path`, `reader`, `writer`
   - **Time**: 15 min

2. [ ] Update user-internal scope (lines ~167-190)
   - Replace `FileTrackedEnableDisableHandler` with `ConfigFileMovingHandler`
   - Update disabled file path: `~/.claude/.disabled-internal.json`
   - Pass `active_path`, `disabled_path`, `reader`, `writer`
   - **Time**: 15 min

**Acceptance Criteria**:
- Both scopes use `ConfigFileMovingHandler`
- Path overrides still work for testing
- No compilation errors

**Dependencies**: Task 1.1 complete

---

#### Task 1.3: Update list_servers() Method [45 min]
**Priority**: P0 - BLOCKING
**Assignee**: Implementation Agent
**File**: `src/mcpi/clients/claude_code.py`

**Subtasks**:
1. [ ] Add method to ConfigFileMovingHandler: `get_disabled_servers_with_configs() -> Dict[str, dict]`
   - Read disabled file
   - Return mcpServers dict
   - **Time**: 15 min

2. [ ] Update `list_servers()` logic
   - After collecting active servers, check if handler has disabled servers method
   - Read disabled servers
   - Add to result with `state=ServerState.DISABLED`
   - **Time**: 20 min

3. [ ] Test manually with print statements
   - Add server to disabled file manually
   - Run `mcpi list`
   - Verify shows as DISABLED
   - **Time**: 10 min

**Acceptance Criteria**:
- `mcpi list` shows enabled servers (from active file)
- `mcpi list` shows disabled servers (from disabled file)
- States are correct

**Dependencies**: Task 1.2 complete

---

#### Task 1.4: Backward Compatibility Migration [30 min]
**Priority**: P1 - HIGH (can defer if time constrained)
**Assignee**: Implementation Agent
**File**: `src/mcpi/clients/enable_disable_handlers.py`

**Subtasks**:
1. [ ] Add `_check_migration_needed() -> bool` to ConfigFileMovingHandler
   - Check if old tracking file exists (`.mcpi-disabled-servers.json`)
   - Return True if exists and not yet migrated
   - **Time**: 10 min

2. [ ] Add `_migrate_from_tracking_file() -> None`
   - Read old tracking file (list of server IDs)
   - For each ID: extract config from active file, add to disabled file
   - Rename old file to `.migrated`
   - Log migration completion
   - **Time**: 15 min

3. [ ] Call migration in `__init__` or first `disable_server()` call
   - Check if migration needed
   - If yes, run migration
   - Continue with operation
   - **Time**: 5 min

**Acceptance Criteria**:
- Old tracking file detected
- Servers migrated to new format
- Old file renamed to `.migrated`
- Migration logged

**Dependencies**: Task 1.1 complete

---

### PHASE 2: Testing (3-4 hours)

#### Task 2.1: Unit Tests for ConfigFileMovingHandler [2 hours]
**Priority**: P0 - BLOCKING
**Assignee**: Implementation Agent
**File**: `tests/test_config_file_moving_handler.py` (NEW)

**Subtasks**:
1. [ ] Setup test fixtures
   - Create temp directory
   - Create active and disabled file paths
   - Create handler instance
   - **Time**: 15 min

2. [ ] Test `test_disable_moves_config_to_disabled_file`
   - Setup: Server in active file
   - Action: `disable_server()`
   - Assert: Config in disabled file, not in active file
   - **Time**: 10 min

3. [ ] Test `test_enable_moves_config_to_active_file`
   - Setup: Server in disabled file
   - Action: `enable_server()`
   - Assert: Config in active file, not in disabled file
   - **Time**: 10 min

4. [ ] Test `test_is_disabled_returns_true_for_disabled_server`
   - Setup: Server in disabled file
   - Action: `is_disabled()`
   - Assert: Returns True
   - **Time**: 5 min

5. [ ] Test `test_is_disabled_returns_false_for_enabled_server`
   - Setup: Server in active file only
   - Action: `is_disabled()`
   - Assert: Returns False
   - **Time**: 5 min

6. [ ] Test `test_disable_idempotent`
   - Setup: Server already disabled
   - Action: `disable_server()` twice
   - Assert: No error, state unchanged
   - **Time**: 10 min

7. [ ] Test `test_enable_idempotent`
   - Setup: Server already enabled
   - Action: `enable_server()` twice
   - Assert: No error, state unchanged
   - **Time**: 10 min

8. [ ] Test `test_disable_missing_server_returns_false`
   - Setup: Server doesn't exist
   - Action: `disable_server()`
   - Assert: Returns False
   - **Time**: 5 min

9. [ ] Test `test_enable_missing_server_returns_false`
   - Setup: Server not in disabled file
   - Action: `enable_server()`
   - Assert: Returns False
   - **Time**: 5 min

10. [ ] Test `test_creates_disabled_file_if_missing`
    - Setup: No disabled file
    - Action: `disable_server()`
    - Assert: Disabled file created
    - **Time**: 10 min

11. [ ] Test `test_handles_empty_active_file`
    - Setup: Empty active file
    - Action: `disable_server()`
    - Assert: Handles gracefully
    - **Time**: 10 min

12. [ ] Test `test_atomic_writes_prevent_corruption`
    - Setup: Server in active file
    - Action: Simulate crash during write
    - Assert: Files not corrupted
    - **Time**: 15 min

13. [ ] Test `test_server_in_both_files_resolves_to_enabled`
    - Setup: Server in both files (corrupt state)
    - Action: `is_disabled()`
    - Assert: Returns False (active wins)
    - **Time**: 10 min

**Acceptance Criteria**:
- All 13 tests pass
- 100% code coverage for ConfigFileMovingHandler
- Tests use temp directories (no real file access)

**Dependencies**: Task 1.1 complete

---

#### Task 2.2: Integration Tests [1.5 hours]
**Priority**: P0 - BLOCKING
**Assignee**: Implementation Agent
**File**: `tests/test_enable_disable_integration.py` (UPDATE or NEW)

**Subtasks**:
1. [ ] Setup integration test harness
   - Use MCPTestHarness
   - Create ClaudeCodePlugin with path overrides
   - **Time**: 15 min

2. [ ] Test `test_user_global_disable_removes_from_settings_json`
   - Setup: Server in settings.json
   - Action: `plugin.disable_server("server", "user-global")`
   - Assert: Server NOT in settings.json, IS in .disabled-mcp.json
   - **Time**: 15 min

3. [ ] Test `test_user_global_enable_restores_to_settings_json`
   - Setup: Server in .disabled-mcp.json
   - Action: `plugin.enable_server("server", "user-global")`
   - Assert: Server IS in settings.json, NOT in .disabled-mcp.json
   - **Time**: 15 min

4. [ ] Test `test_user_internal_disable_removes_from_claude_json`
   - Setup: Server in .claude.json
   - Action: `plugin.disable_server("server", "user-internal")`
   - Assert: Server NOT in .claude.json, IS in .disabled-internal.json
   - **Time**: 15 min

5. [ ] Test `test_user_internal_enable_restores_to_claude_json`
   - Setup: Server in .disabled-internal.json
   - Action: `plugin.enable_server("server", "user-internal")`
   - Assert: Server IS in .claude.json, NOT in .disabled-internal.json
   - **Time**: 15 min

6. [ ] Test `test_list_shows_combined_enabled_and_disabled`
   - Setup: 2 servers in active, 1 in disabled
   - Action: `plugin.list_servers("user-global")`
   - Assert: Returns 3 servers, correct states
   - **Time**: 15 min

7. [ ] Additional integration tests
   - Test scope isolation (disable in user-global doesn't affect user-internal)
   - Test multiple servers
   - Test error cases
   - **Time**: 15 min

**Acceptance Criteria**:
- All integration tests pass
- Tests verify actual file changes (not mocks)
- MCPTestHarness prevents touching real user files

**Dependencies**: Task 1.3 complete

---

#### Task 2.3: E2E Tests with Claude CLI [1 hour]
**Priority**: P0 - CRITICAL
**Assignee**: Implementation Agent
**File**: `tests/test_e2e_claude_integration.py` (NEW)

**Subtasks**:
1. [ ] Check if `claude` CLI is available
   - Run `which claude` in setup
   - Skip tests if not installed
   - **Time**: 5 min

2. [ ] Test `test_disabled_server_not_in_claude_mcp_list`
   - Setup: Add server to active file
   - Verify: `claude mcp list` shows server
   - Action: Disable server via MCPI
   - Verify: `claude mcp list` does NOT show server (CRITICAL!)
   - Cleanup: Enable server
   - **Time**: 20 min

3. [ ] Test `test_enabled_server_appears_in_claude_mcp_list`
   - Setup: Add server to disabled file
   - Verify: `claude mcp list` does NOT show server
   - Action: Enable server via MCPI
   - Verify: `claude mcp list` shows server (CRITICAL!)
   - **Time**: 15 min

4. [ ] Test `test_disable_enable_roundtrip`
   - Setup: Server enabled
   - Action: Disable, verify gone, enable, verify back
   - Assert: All state transitions work
   - **Time**: 15 min

5. [ ] Helper function: `_parse_claude_mcp_list() -> List[str]`
   - Run `claude mcp list` subprocess
   - Parse output
   - Return list of server names
   - **Time**: 5 min

**Acceptance Criteria**:
- E2E tests actually run `claude mcp list` (not mocked)
- Tests verify Claude's behavior, not just MCPI state
- Tests use path overrides to avoid touching real user files
- Tests skip gracefully if Claude not installed

**Dependencies**: Task 1.3 complete, Claude CLI installed

---

#### Task 2.4: Migration Tests [30 min]
**Priority**: P1 - HIGH
**Assignee**: Implementation Agent
**File**: `tests/test_migration_tracking_to_config.py` (NEW)

**Subtasks**:
1. [ ] Test `test_migrates_old_tracking_file_on_first_use`
   - Setup: Old tracking file with server IDs, servers in active file
   - Action: Initialize handler
   - Assert: Servers migrated to disabled file
   - **Time**: 15 min

2. [ ] Test `test_migration_preserves_server_configs`
   - Setup: Old tracking file with 3 servers
   - Action: Trigger migration
   - Assert: All configs intact in disabled file
   - **Time**: 10 min

3. [ ] Test `test_migration_creates_backup`
   - Setup: Old tracking file
   - Action: Trigger migration
   - Assert: Old file renamed to `.migrated`
   - **Time**: 5 min

**Acceptance Criteria**:
- Migration tests pass
- Configs preserved during migration
- Backup file created

**Dependencies**: Task 1.4 complete

---

### PHASE 3: Manual Validation (1-2 hours)

#### Task 3.1: Create Manual Test Checklist [15 min]
**Priority**: P0 - BLOCKING
**Assignee**: Implementation Agent
**File**: `.agent_planning/MANUAL_TEST_CHECKLIST_DISABLE_FIX.md` (NEW)

**Subtasks**:
1. [ ] Document test procedures
   - Fresh install test
   - Migration test
   - Multi-server test
   - Edge case tests
   - **Time**: 15 min

**Acceptance Criteria**:
- Checklist is clear and actionable
- Includes verification steps
- Includes expected results

**Dependencies**: None

---

#### Task 3.2: Execute Manual Tests [1 hour]
**Priority**: P0 - CRITICAL
**Assignee**: Human Tester
**Environment**: Real Claude Code installation

**Test Procedures**:

**Test 1: Disable Verification** [15 min]
1. [ ] Start: Run `claude mcp list`, note which servers appear
2. [ ] Pick one server from the list
3. [ ] Run `mcpi disable <server> --scope user-global`
4. [ ] Run `claude mcp list` again
5. [ ] **VERIFY**: Server does NOT appear in list
6. [ ] **RESULT**: PASS / FAIL

**Test 2: Enable Verification** [15 min]
1. [ ] Start: Server should still be disabled from Test 1
2. [ ] Run `mcpi enable <server> --scope user-global`
3. [ ] Run `claude mcp list`
4. [ ] **VERIFY**: Server DOES appear in list
5. [ ] **RESULT**: PASS / FAIL

**Test 3: MCPI List Shows Combined State** [10 min]
1. [ ] Setup: Have 2 enabled, 1 disabled server
2. [ ] Run `mcpi list --scope user-global`
3. [ ] **VERIFY**: Shows 3 servers total
4. [ ] **VERIFY**: States are correct (2 enabled, 1 disabled)
5. [ ] **RESULT**: PASS / FAIL

**Test 4: Migration from Old Format** [20 min]
1. [ ] Setup: Create old tracking file manually
2. [ ] Add 2 server IDs to tracking file
3. [ ] Ensure those servers exist in active file
4. [ ] Run `mcpi disable <different-server>`
5. [ ] **VERIFY**: Old tracking file migrated
6. [ ] **VERIFY**: 2 servers from old file now in disabled file
7. [ ] **VERIFY**: Old file renamed to `.migrated`
8. [ ] **RESULT**: PASS / FAIL

**Acceptance Criteria**:
- All 4 tests pass
- Screenshots captured
- Results documented

**Dependencies**: All automated tests passing

---

#### Task 3.3: Document Validation Results [15 min]
**Priority**: P0 - BLOCKING
**Assignee**: Tester
**File**: `.agent_planning/MANUAL_TEST_RESULTS_DISABLE_FIX.md` (NEW)

**Subtasks**:
1. [ ] Document each test result
   - Test name
   - Pass/Fail
   - Screenshots
   - Terminal output
   - **Time**: 10 min

2. [ ] Sign off on validation
   - Date
   - Tester name
   - Overall result
   - **Time**: 5 min

**Acceptance Criteria**:
- All tests documented
- Clear pass/fail status
- Evidence provided (screenshots)

**Dependencies**: Task 3.2 complete

---

### PHASE 4: Code Cleanup (1 hour)

#### Task 4.1: Remove Old Implementation [30 min]
**Priority**: P2 - MEDIUM (can defer)
**Assignee**: Implementation Agent

**Subtasks**:
1. [ ] Mark `DisabledServersTracker` as deprecated
   - Add deprecation warning in docstring
   - Add comment: "Will be removed in v4.0"
   - **Time**: 5 min

2. [ ] Mark `FileTrackedEnableDisableHandler` as deprecated
   - Add deprecation warning
   - Add comment explaining why
   - **Time**: 5 min

3. [ ] Remove unused imports
   - Run `ruff check --select F401`
   - Remove any unused imports
   - **Time**: 10 min

4. [ ] Plan for full removal in future release
   - Create GitHub issue for v4.0
   - Document what to remove
   - **Time**: 10 min

**Acceptance Criteria**:
- Old code marked deprecated (not deleted yet)
- No unused imports
- Future removal planned

**Dependencies**: All tests passing

---

#### Task 4.2: Update Documentation [30 min]
**Priority**: P0 - BLOCKING
**Assignee**: Implementation Agent

**Subtasks**:
1. [ ] Update `CLAUDE.md`
   - Update lines 406-410 (disable mechanism description)
   - Document new approach
   - Add migration notes
   - **Time**: 15 min

2. [ ] Update `README.md` (if needed)
   - Check if disable/enable is documented
   - Update if necessary
   - **Time**: 5 min

3. [ ] Create `CHANGELOG.md` entry
   - Version: v3.0.0
   - Section: BREAKING CHANGES
   - Describe bug fix and migration
   - **Time**: 10 min

**Acceptance Criteria**:
- CLAUDE.md updated
- README.md updated if needed
- CHANGELOG.md entry added

**Dependencies**: Manual validation complete

---

## Sprint Metrics

### Estimated vs Actual

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Phase 1: Implementation | 2-3 hours | _TBD_ | |
| Phase 2: Testing | 3-4 hours | _TBD_ | |
| Phase 3: Manual Validation | 1-2 hours | _TBD_ | |
| Phase 4: Cleanup | 1 hour | _TBD_ | |
| **TOTAL** | **7-10 hours** | **_TBD_** | |

### Test Coverage

| Test Type | Count | Pass Rate | Coverage |
|-----------|-------|-----------|----------|
| Unit Tests | 13 | _TBD_ | _TBD_ |
| Integration Tests | 12 | _TBD_ | _TBD_ |
| E2E Tests | 9 | _TBD_ | _TBD_ |
| Manual Tests | 4 | _TBD_ | N/A |
| **TOTAL** | **38** | **_TBD_** | **_TBD_** |

### Quality Gates

- [ ] All unit tests pass (13/13)
- [ ] All integration tests pass (12/12)
- [ ] All E2E tests pass (9/9)
- [ ] All manual tests pass (4/4)
- [ ] Code coverage 100% for new code
- [ ] No test regressions
- [ ] Code review complete
- [ ] Documentation updated

---

## Daily Schedule

### Day 1 (5-6 hours)

**Morning Session (3 hours)**:
- 9:00 - 11:00: Task 1.1 - Create ConfigFileMovingHandler
- 11:00 - 11:30: Task 1.2 - Update scope initialization
- 11:30 - 12:15: Task 1.3 - Update list_servers()

**Afternoon Session (2-3 hours)**:
- 1:00 - 3:00: Task 2.1 - Unit tests
- 3:00 - 4:00: Task 2.2 - Integration tests (start)

**End of Day 1**:
- Phase 1 complete (100%)
- Phase 2 in progress (50%)

---

### Day 2 (2-4 hours)

**Morning Session (2 hours)**:
- 9:00 - 10:00: Task 2.2 - Integration tests (finish)
- 10:00 - 11:00: Task 2.3 - E2E tests

**Afternoon Session (2 hours)**:
- 1:00 - 2:00: Task 3.2 - Manual validation
- 2:00 - 2:30: Task 4.2 - Documentation
- 2:30 - 3:00: Final verification

**End of Day 2**:
- All phases complete (100%)
- Ready to merge

---

## Risks and Blockers

### Critical Risks

**Risk 1: E2E Tests Can't Run `claude mcp list`**
- **Impact**: Can't verify Claude behavior
- **Probability**: MEDIUM
- **Mitigation**: Provide fallback mock implementation
- **Owner**: Implementation Agent

**Risk 2: Migration Corrupts User Data**
- **Impact**: HIGH - User loses server configs
- **Probability**: LOW (with proper testing)
- **Mitigation**: Create backup before migration
- **Owner**: Implementation Agent

**Risk 3: Manual Tests Fail**
- **Impact**: Can't ship until fixed
- **Probability**: MEDIUM (new implementation)
- **Mitigation**: Extensive automated testing first
- **Owner**: Tester

### Blockers

**Current Blockers**: None

**Potential Blockers**:
1. Claude CLI not installed for E2E tests
   - Resolution: Skip E2E tests, document requirement
2. Test harness doesn't support new handler
   - Resolution: Update test harness
3. Merge conflicts during implementation
   - Resolution: Rebase frequently

---

## Success Criteria

### Sprint Success = ALL of the following

- [x] **Implementation Complete**: All 4 tasks in Phase 1 done
- [x] **Tests Pass**: 34/34 automated tests passing
- [x] **Manual Validation**: 4/4 manual tests pass
- [x] **E2E Verification**: `claude mcp list` respects disabled state
- [x] **Zero Regressions**: All existing tests still pass
- [x] **Documentation Updated**: CLAUDE.md, README.md, CHANGELOG.md
- [x] **Code Quality**: Black, Ruff, mypy pass
- [x] **Review Approved**: Code review complete

### Feature Success = MUST VERIFY

**CRITICAL**: After implementation, the following MUST be true:

1. **Disable Test**:
   ```bash
   # Before disable
   $ claude mcp list | grep test-server
   test-server: npx -y test-package - ✓ Connected

   # After disable
   $ mcpi disable test-server --scope user-global
   $ claude mcp list | grep test-server
   (no output)  # ← SERVER MUST NOT APPEAR
   ```

2. **Enable Test**:
   ```bash
   # Before enable
   $ claude mcp list | grep test-server
   (no output)

   # After enable
   $ mcpi enable test-server --scope user-global
   $ claude mcp list | grep test-server
   test-server: npx -y test-package - ✓ Connected  # ← SERVER MUST APPEAR
   ```

**If either test fails**: Implementation is BROKEN, DO NOT SHIP

---

## Rollback Plan

**If Critical Issue Found**:

1. **Immediate** (< 1 hour):
   - Revert all changes in Phase 1
   - Restore old `FileTrackedEnableDisableHandler` (even though broken)
   - Ship hotfix

2. **Investigation** (< 1 day):
   - Reproduce issue
   - Identify root cause
   - Create fix with test

3. **Fix Release** (< 2 days):
   - Ship v3.0.1 with fix
   - Document issue

---

## Next Steps After Sprint

**Immediate**:
1. Merge PR
2. Tag v3.0.0
3. Update release notes
4. Ship to production

**Follow-up** (v3.0.1+):
1. Monitor for bug reports
2. Gather user feedback
3. Consider adding `mcpi doctor` command
4. Plan removal of deprecated code (v4.0)

---

**Sprint Created**: 2025-11-16-15:55:08
**Sprint Owner**: Implementation Agent
**Status**: READY TO START
**Estimated Completion**: 1.5 days from start
