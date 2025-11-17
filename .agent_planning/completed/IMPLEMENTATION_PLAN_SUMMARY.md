# User-Global Disable/Enable Fix - Implementation Plan Summary

**Date**: 2025-11-16-15:55:08
**Priority**: P0 - CRITICAL BUG FIX - SHIP BLOCKER
**Status**: READY FOR IMPLEMENTATION

---

## Critical Bug Summary

**The Problem**: User-global and user-internal MCP server disable/enable is **completely broken**.

**Evidence**:
```bash
# After running "mcpi disable frida-mcp"
$ mcpi list --scope user-internal | grep frida-mcp
│ frida-mcp │ DISABLED │  # MCPI shows DISABLED

$ claude mcp list | grep frida-mcp
frida-mcp: frida-mcp - ✓ Connected  # Claude shows CONNECTED (BUG!)
```

**Root Cause**: MCPI uses a tracking file (`~/.claude/.mcpi-disabled-servers.json`) that Claude Code never reads. Result: servers marked "disabled" by MCPI still run in Claude.

**User Impact**: Feature doesn't work. Users can't actually disable servers, just change MCPI's UI state.

---

## The Solution

**Replace** broken tracking file approach **with** config file movement approach:

**Current (BROKEN)**:
```
Disable: Add server ID to tracking file (Claude ignores this)
Enable: Remove server ID from tracking file
```

**New (CORRECT)**:
```
Disable: MOVE server config FROM settings.json TO .disabled-mcp.json
Enable: MOVE server config FROM .disabled-mcp.json TO settings.json
```

**Why This Works**: Claude only reads `settings.json`. Servers in `.disabled-mcp.json` are invisible to Claude, achieving actual disable functionality.

---

## Planning Documents Created

I've created three comprehensive planning documents in `.agent_planning/`:

### 1. PLAN-USER-GLOBAL-DISABLE-FIX-2025-11-16-155508.md
**Purpose**: Detailed technical implementation plan

**Contents**:
- Complete architecture redesign (ConfigFileMovingHandler)
- Implementation steps (4 phases, broken down into subtasks)
- Testing strategy (34 tests: 13 unit + 12 integration + 9 E2E)
- Edge case handling (corrupted files, permissions, concurrent access, etc.)
- Risk assessment and mitigation
- Success criteria and validation requirements
- Backward compatibility migration
- File structure diagrams
- Error handling matrix

**Size**: ~1200 lines, comprehensive technical reference

---

### 2. SPRINT-USER-GLOBAL-DISABLE-FIX-2025-11-16-155508.md
**Purpose**: Executable sprint plan with task-by-task breakdown

**Contents**:
- Task breakdown (4 phases, ~20 tasks total)
- Time estimates per task (15 min to 2 hours)
- Acceptance criteria for each task
- Daily schedule (Day 1: implementation + testing, Day 2: validation + cleanup)
- Quality gates and success metrics
- Rollback plan if issues found
- Test coverage tracking

**Size**: ~800 lines, actionable task list

---

### 3. PLANNING-SUMMARY-USER-GLOBAL-DISABLE-FIX-2025-11-16-155508.md
**Purpose**: High-level overview and quick reference

**Contents**:
- Executive summary (problem, solution, effort)
- Current state analysis (what's broken, why)
- Required changes (architecture, testing, validation)
- Decision log (E2E strategy, migration timing, file format)
- Timeline and effort estimates
- Success criteria
- Related documents index

**Size**: ~600 lines, planning overview

---

## Implementation Effort

**Total Time**: 7-10 hours (1.5 work days)

**Breakdown**:
- Phase 1: Core Implementation (2-3 hours)
- Phase 2: Comprehensive Testing (3-4 hours)
- Phase 3: Manual Validation (1-2 hours)
- Phase 4: Code Cleanup (1 hour)

**Critical Path**: Sequential (each phase depends on previous)

---

## Key Components

### New Handler: ConfigFileMovingHandler

**Location**: `src/mcpi/clients/enable_disable_handlers.py`

**Key Methods**:
```python
class ConfigFileMovingHandler:
    def __init__(self, active_path, disabled_path, reader, writer):
        # Store paths to active and disabled config files

    def disable_server(self, server_id: str) -> bool:
        # MOVE server config from active to disabled file
        # Returns True if successful

    def enable_server(self, server_id: str) -> bool:
        # MOVE server config from disabled to active file
        # Returns True if successful

    def is_disabled(self, server_id: str) -> bool:
        # Check if server exists in disabled file
```

### Updated Files

1. **src/mcpi/clients/enable_disable_handlers.py**
   - Add `ConfigFileMovingHandler` class (~200 lines)

2. **src/mcpi/clients/claude_code.py**
   - Update user-global scope initialization (lines ~142-164)
   - Update user-internal scope initialization (lines ~167-190)
   - Update `list_servers()` to read both active and disabled files

### New Files

**Disabled Configuration Files**:
- `~/.claude/.disabled-mcp.json` (user-global disabled servers)
- `~/.claude/.disabled-internal.json` (user-internal disabled servers)

**Test Files**:
- `tests/test_config_file_moving_handler.py` (unit tests)
- `tests/test_e2e_claude_integration.py` (E2E tests)
- `tests/test_migration_tracking_to_config.py` (migration tests)

**Documentation Files**:
- `.agent_planning/MANUAL_TEST_CHECKLIST_DISABLE_FIX.md` (test procedures)
- `.agent_planning/MANUAL_TEST_RESULTS_DISABLE_FIX.md` (test results)

---

## Testing Strategy (CRITICAL)

### Why Comprehensive Testing Is Essential

The current bug exists because tests only verified MCPI's internal state, not Claude Code's actual behavior. The new testing strategy fixes this.

### Test Breakdown (34 Tests)

**Unit Tests (13 tests)**: Test ConfigFileMovingHandler in isolation
- Config movement (disable/enable)
- Edge cases (missing server, corrupted JSON, etc.)
- Idempotency
- Error handling

**Integration Tests (12 tests)**: Test scope-level operations
- User-global disable/enable
- User-internal disable/enable
- List combined servers
- Scope isolation

**E2E Tests (9 tests)**: Verify Claude Code behavior (CRITICAL!)
- `test_disabled_server_not_in_claude_mcp_list` - Runs `claude mcp list`, verifies disabled server NOT shown
- `test_enabled_server_appears_in_claude_mcp_list` - Runs `claude mcp list`, verifies enabled server IS shown
- `test_disable_enable_roundtrip` - Full workflow verification

**Why E2E Tests Matter**: These tests run actual `claude mcp list` commands and verify output. This is the ONLY way to ensure the fix actually works.

### Manual Validation (MANDATORY)

**Before merge**: Human tester must execute 4 manual tests and document results with screenshots:

1. Disable server, verify `claude mcp list` doesn't show it
2. Enable server, verify `claude mcp list` shows it
3. MCPI list shows combined enabled + disabled servers
4. Migration from old tracking file works

**Success Criteria**: All 4 tests PASS with photographic evidence

---

## Critical Validation Requirement

**THE TEST THAT MATTERS**:

```bash
# Before disable (server should be running)
$ claude mcp list | grep test-server
test-server: npx -y test-package - ✓ Connected

# Disable the server
$ mcpi disable test-server --scope user-global
Server 'test-server' disabled in scope 'user-global'

# CRITICAL: Verify server is GONE from Claude
$ claude mcp list | grep test-server
(no output)  # ← MUST BE EMPTY OR FIX IS BROKEN

# Enable the server
$ mcpi enable test-server --scope user-global
Server 'test-server' enabled in scope 'user-global'

# CRITICAL: Verify server is BACK in Claude
$ claude mcp list | grep test-server
test-server: npx -y test-package - ✓ Connected  # ← MUST APPEAR
```

**If this test fails**: Implementation is broken, DO NOT MERGE

---

## Success Criteria (Ship Checklist)

**ALL of these must be TRUE before merging**:

- [ ] ConfigFileMovingHandler implemented and tested
- [ ] User-global and user-internal scopes updated
- [ ] list_servers() reads both active and disabled files
- [ ] 34 automated tests passing (100%)
- [ ] Manual validation complete (4/4 tests pass)
- [ ] E2E verification: `claude mcp list` does NOT show disabled servers
- [ ] E2E verification: `claude mcp list` DOES show enabled servers
- [ ] Migration from old tracking file works
- [ ] Zero test regressions (all existing tests still pass)
- [ ] Documentation updated (CLAUDE.md, README.md, CHANGELOG.md)
- [ ] Code review approved
- [ ] Manual demonstration video/screenshots provided

**If ANY fail**: DO NOT MERGE, fix the issue first

---

## Backward Compatibility

### Migration from Old Tracking File Format

**Automatic Migration**: On first disable/enable operation after upgrade

**Old Format**:
```json
~/.claude/.mcpi-disabled-servers.json:
["server-1", "server-2"]
```

**New Format**:
```json
~/.claude/.disabled-mcp.json:
{
  "mcpServers": {
    "server-1": {"command": "...", "args": [...], "type": "stdio"},
    "server-2": {"command": "...", "args": [...], "type": "stdio"}
  }
}
```

**Migration Process**:
1. Detect old tracking file
2. Read server IDs
3. Extract full configs from active file
4. Write configs to new disabled file
5. Rename old file to `.migrated` (backup)

**Safety**: Old file preserved, can rollback if needed

---

## Risks and Mitigation

### Top 3 Risks

**Risk 1: Tests pass but Claude still loads disabled servers**
- **Impact**: CRITICAL (bug still exists)
- **Mitigation**: E2E tests run actual `claude mcp list` commands
- **Validation**: Manual testing on real Claude installation required

**Risk 2: Migration corrupts user server configs**
- **Impact**: HIGH (user data loss)
- **Mitigation**: Keep old file as `.migrated` backup
- **Validation**: Extensive migration testing

**Risk 3: Breaking changes affect existing user workflows**
- **Impact**: MEDIUM (user scripts break)
- **Mitigation**: Version bump to v3.0, comprehensive CHANGELOG
- **Communication**: Document breaking changes clearly

---

## Next Steps

### Immediate (For Implementation Agent)

1. **Read Planning Documents** (30 min)
   - Review PLAN document for technical details
   - Review SPRINT document for task breakdown
   - Clarify any questions before starting

2. **Execute Phase 1: Core Implementation** (2-3 hours)
   - Create ConfigFileMovingHandler
   - Update scope initialization
   - Update list_servers()
   - Add migration logic

3. **Execute Phase 2: Testing** (3-4 hours)
   - Write 13 unit tests
   - Write 12 integration tests
   - Write 9 E2E tests (run `claude mcp list`)
   - Verify 100% test coverage

4. **Execute Phase 3: Manual Validation** (1-2 hours)
   - Create manual test checklist
   - Execute manual tests on real Claude
   - Document results with screenshots

5. **Execute Phase 4: Cleanup** (1 hour)
   - Mark old code as deprecated
   - Update documentation
   - Create CHANGELOG entry

### After Implementation

1. **Create Pull Request**
   - Include all tests
   - Include documentation updates
   - Include manual test results

2. **Code Review**
   - Focus on test quality
   - Verify E2E tests run `claude mcp list`
   - Verify manual validation evidence

3. **Merge and Ship**
   - Tag v3.0.0
   - Update release notes
   - Monitor for issues

---

## File Reference Quick Links

**Planning Documents**:
- `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/.agent_planning/PLAN-USER-GLOBAL-DISABLE-FIX-2025-11-16-155508.md`
- `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/.agent_planning/SPRINT-USER-GLOBAL-DISABLE-FIX-2025-11-16-155508.md`
- `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/.agent_planning/PLANNING-SUMMARY-USER-GLOBAL-DISABLE-FIX-2025-11-16-155508.md`

**Background Analysis**:
- `/Users/bmf/Library/Mobile Documents/com~apple~CloudDocs/_mine/icode/mcpi/.agent_planning/STATUS-2025-11-16-USER-GLOBAL-DISABLE-CRITICAL-BUG.md`

**Implementation Files** (to be modified):
- `src/mcpi/clients/enable_disable_handlers.py`
- `src/mcpi/clients/claude_code.py`

**Test Files** (to be created):
- `tests/test_config_file_moving_handler.py`
- `tests/test_e2e_claude_integration.py`
- `tests/test_migration_tracking_to_config.py`

---

## Questions or Clarifications?

**Before starting implementation**, review the detailed planning documents and ask any questions about:

1. **Architecture**: Is the ConfigFileMovingHandler approach clear?
2. **Testing**: Do you understand the E2E testing strategy?
3. **Validation**: Are the manual testing requirements clear?
4. **Timeline**: Is the 1.5-day estimate reasonable?
5. **Risks**: Are there any concerns about the approach?

**Important**: This is a critical bug fix that blocks v2.0 ship. The implementation must be done right the first time with comprehensive testing.

---

## Summary

**Problem**: Disable/enable broken (Claude ignores MCPI's tracking file)

**Solution**: Move server configs between active and disabled files

**Effort**: 7-10 hours (1.5 work days)

**Testing**: 34 automated tests + 4 manual tests

**Critical Test**: `claude mcp list` must NOT show disabled servers

**Ship Criteria**: ALL tests pass + manual validation complete + zero regressions

**Version**: v3.0.0 (breaking change)

**Priority**: P0 - CRITICAL - NO OTHER WORK UNTIL COMPLETE

---

**Planning Complete**: 2025-11-16-15:55:08
**Planner**: Claude Code (Implementation Planner)
**Status**: READY FOR IMPLEMENTATION
**Next Action**: Review plans → Start Phase 1
