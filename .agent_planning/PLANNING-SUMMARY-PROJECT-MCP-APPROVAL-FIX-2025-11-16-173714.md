# Planning Summary: Fix Project-MCP Approval Bug

**Generated**: 2025-11-16 17:37:14
**Source STATUS**: STATUS-2025-11-16-PROJECT-MCP-APPROVAL-BUG.md
**Detailed Plan**: PLAN-PROJECT-MCP-APPROVAL-FIX-2025-11-16-173714.md

---

## Executive Summary

**CRITICAL BUG**: Servers in `project-mcp` scope show as ENABLED in `mcpi list` but do NOT appear in `claude mcp list` output, breaking the fundamental contract that "ENABLED servers should work in Claude Code."

**Root Cause**: MCPI's `InlineEnableDisableHandler` only checks inline `"disabled": true` field but does NOT check Claude Code's required approval mechanism (`enabledMcpjsonServers` array).

**Solution**: Create `ApprovalRequiredEnableDisableHandler` that checks approval arrays in `.claude/settings.local.json`.

**Effort**: 6-9 hours (full implementation + comprehensive testing + validation)

**Confidence**: VERY HIGH (10/10) - Clear root cause, clear solution, clear validation path

---

## Implementation Plan

### Total Work Items: 8

**Phase 1: Handler Implementation (2-3 hours)**
1. APPROVAL-001: Create ApprovalRequiredEnableDisableHandler class (1.5 hours)
2. APPROVAL-002: Update ClaudeCodePlugin to use new handler (30 minutes)

**Phase 2: Unit Testing (2 hours)**
3. APPROVAL-003: Write 11 unit tests for handler (2 hours)

**Phase 3: Integration Testing (1.5 hours)**
4. APPROVAL-004: Write 5 integration tests for workflow (1.5 hours)

**Phase 4: E2E Validation (3 hours)**
5. APPROVAL-005: Write 4 E2E tests validating against Claude (2 hours)
6. APPROVAL-006: Manual testing checklist (1 hour)

**Phase 5: Documentation (1 hour)**
7. APPROVAL-007: Update CLAUDE.md with approval mechanism (30 minutes)
8. APPROVAL-008: Update code comments and docstrings (30 minutes)

---

## Critical Path

```
APPROVAL-001 (Create Handler)
    ↓
APPROVAL-002 (Integrate Handler)
    ↓
APPROVAL-003 (Unit Tests)
    ↓
APPROVAL-004 (Integration Tests)
    ↓
APPROVAL-005 (E2E Tests)
    ↓
APPROVAL-006 (Manual Testing)
    ↓
APPROVAL-007 (Documentation)
    ↓
APPROVAL-008 (Code Comments)
```

**Total Effort**: 6-9 hours

---

## Acceptance Criteria

### Functional Requirements
- ✅ Server in `.mcp.json` WITHOUT approval shows as DISABLED
- ✅ Server in `.mcp.json` WITH approval shows as ENABLED
- ✅ `mcpi enable` adds to `enabledMcpjsonServers` array
- ✅ `mcpi disable` adds to `disabledMcpjsonServers` array
- ✅ ENABLED server appears in `claude mcp list` output
- ✅ DISABLED server does NOT appear in `claude mcp list` output

### Quality Requirements
- ✅ 20 new tests written and passing (11 unit + 5 integration + 4 E2E)
- ✅ 100% test coverage for ApprovalRequiredEnableDisableHandler
- ✅ All existing tests still pass
- ✅ Manual validation against `claude mcp list` successful
- ✅ Documentation updated
- ✅ No regressions in other scopes

---

## Files to Create (3)

1. `tests/test_approval_required_handler.py` - Unit tests (11 tests)
2. `tests/test_project_mcp_approval_integration.py` - Integration tests (5 tests)
3. `tests/test_project_mcp_claude_validation.py` - E2E tests (4 tests)

---

## Files to Modify (3)

1. `src/mcpi/clients/enable_disable_handlers.py` - Add ApprovalRequiredEnableDisableHandler (~150 lines)
2. `src/mcpi/clients/claude_code.py` - Update project-mcp scope (lines 8, 74-92)
3. `CLAUDE.md` - Add approval mechanism documentation (~50 lines)

---

## Risk Assessment

**Implementation Risk**: VERY LOW
- Clear root cause identified
- Solution follows existing patterns
- No architectural changes required
- Only affects project-mcp scope

**Regression Risk**: VERY LOW
- Only project-mcp scope affected
- Other scopes unchanged
- Comprehensive test suite

**User Impact Risk**: LOW
- Bug currently prevents servers from working
- Fix makes behavior match expectations
- Clear documentation of approval mechanism

**Overall Confidence**: VERY HIGH (10/10)

---

## First Action

**START**: APPROVAL-001 - Create ApprovalRequiredEnableDisableHandler class

**Location**: `src/mcpi/clients/enable_disable_handlers.py`

**Task**: Implement new handler class with approval-aware state detection:
1. Check inline `"disabled": true` field (highest priority)
2. Check `disabledMcpjsonServers` array → DISABLED
3. Check `enabledMcpjsonServers` array → ENABLED
4. Default: Not approved → DISABLED

**Estimated Time**: 1.5 hours

---

## Success Metrics

**Definition of Done**:
- [ ] All 8 work items completed
- [ ] 20 new tests written and passing
- [ ] 100% test coverage for new handler
- [ ] All existing tests still pass
- [ ] Manual testing checklist complete
- [ ] Documentation updated
- [ ] `claude mcp list` validation successful

**Validation Criteria**:
- [ ] `mcpi list --scope project-mcp` shows correct states
- [ ] `claude mcp list` output matches MCPI states
- [ ] Unapproved servers show as DISABLED
- [ ] Approved servers show as ENABLED
- [ ] Enable/disable operations work correctly

---

## Next Steps

### IMMEDIATE (This Session - 3-4 hours)
1. Create ApprovalRequiredEnableDisableHandler class
2. Update ClaudeCodePlugin to use new handler
3. Write 11 unit tests for handler
4. Verify all unit tests pass

### NEXT SESSION (5-6 hours)
1. Write 5 integration tests for workflow
2. Write 4 E2E tests validating against Claude
3. Complete manual testing checklist
4. Update documentation
5. Final validation

### COMPLETION
- All 20 tests passing
- Manual validation against `claude mcp list` successful
- Documentation complete
- Ready to commit and ship fix

---

**END OF PLANNING SUMMARY**

**Critical Message**: This bug MUST be fixed before any new features. It breaks the fundamental contract that "ENABLED servers should work in Claude Code."
