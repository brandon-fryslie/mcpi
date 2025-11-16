# Planning Summary - Design Patterns MCP Server Fix

**Date**: 2025-11-09 05:25:00
**Plan File**: PLAN-2025-11-09-052500.md
**Issue**: design-patterns MCP server connection failure
**Impact**: Server completely non-functional, requires immediate fix

---

## Overview

This planning session addresses a critical issue where the design-patterns MCP server fails to connect to Claude Code due to missing environment variable configuration. The plan splits the solution into two parts:

1. **Immediate Fix (P0)**: Manual configuration update (outside MCPI scope)
2. **Future Enhancement (P1)**: Add environment variable support to MCPI registry

---

## Problem Summary

**Root Cause**: Missing `PATTERNS_DIR` environment variable in Claude Code configuration

**Symptoms**:
- `claude mcp list` shows "✗ Failed to connect" for design-patterns
- Server exits on startup with "Patterns directory not found: corpus/patterns"
- All 6 MCP tools unavailable

**Evidence**:
- Server works when run manually from its directory ✅
- Server fails when run from wrong directory ❌
- Server works with `PATTERNS_DIR` env var set ✅
- Documented in server's README as required configuration

**Impact**: CRITICAL - Server completely unusable

---

## Solution Architecture

### Part 1: Immediate Fix (P0-1)

**What**: Update `~/.claude.json` to add missing environment variable

**Where**: User's Claude Code configuration file (outside MCPI codebase)

**How**: Add single line to server config:
```json
"env": {
  "PATTERNS_DIR": "/Users/bmf/icode/design-pattern-mcp/corpus"
}
```

**Effort**: 2 minutes

**Risk**: Very low (trivial config change, easily reverted)

**Outcome**: Server connects immediately, all tools available

### Part 2: MCPI Enhancement (P1-1)

**What**: Add first-class environment variable support to MCPI registry schema

**Why**: Prevent this issue for all future server installations

**Components**:
1. Schema: Add `env` field to `MCPServer` Pydantic model
2. Registry: Update `data/registry.json` with design-patterns env var
3. Installation: Update client plugins to include env vars in generated configs
4. Testing: Unit + integration tests for env var support
5. Documentation: Update CLAUDE.md, README, CHANGELOG

**Effort**: 3-5 days

**Risk**: Low-medium (backward compatible, well-scoped feature)

**Outcome**: `mcpi add <server-with-env-vars>` creates complete, working configuration

---

## Work Breakdown

### P0 (CRITICAL) - Ship Today

**P0-1: Update Claude Code Configuration**
- Effort: 2 minutes
- Action: Edit `~/.claude.json` to add `PATTERNS_DIR` environment variable
- Testing: `claude mcp list` shows "✓ Connected"
- Blocker: None (ready to execute immediately)

### P1 (HIGH) - Next 2 Weeks

**P1-1: Add Environment Variable Support to MCPI**
- Effort: 3-5 days
- Components: Schema, registry, installation logic, tests, docs
- Dependencies: P0-1 (validates design approach)
- Testing: Test-driven development (write tests first)
- Success: Future installations include env vars automatically

### P2 (MEDIUM) - Next Month (Optional)

**P2-1: Add Path Interpolation**
- Effort: 1-2 days
- Feature: Support `${HOME}`, `~`, `$VAR` in environment variable values
- Dependencies: P1-1 (builds on env var foundation)
- Why Optional: Not critical for MVP, adds complexity

### P3 (LOW) - Next Quarter (Optional)

**P3-1: Add Environment Variable Validation**
- Effort: 3-5 days
- Feature: Schema-based validation of env vars per server
- Dependencies: P1-1 (builds on env var foundation)
- Why Optional: Nice-to-have, may be overkill

---

## Sprint Recommendations

### Sprint 1: Immediate Fix + Design (1 day)

**Goals**:
1. Fix server connection NOW
2. Design env var schema changes
3. Write tests FIRST for P1-1

**Tasks**:
- [ ] P0-1: Update `~/.claude.json` (2 min)
- [ ] Verify server connects (5 min)
- [ ] Design env var schema (2-3 hours)
- [ ] Write tests for env var support (3-4 hours)

**Deliverable**: Working server + test-driven design

### Sprint 2: Environment Variable Support (3-5 days)

**Goals**:
1. Implement env var support in MCPI
2. Pass all tests
3. Update documentation

**Tasks**:
- [ ] Add `env` field to Pydantic model (2 hours)
- [ ] Update registry with design-patterns env (1 hour)
- [ ] Update installation logic in client plugins (3-4 hours)
- [ ] Integration tests (3-4 hours)
- [ ] Documentation updates (2-3 hours)
- [ ] End-to-end validation (1 hour)

**Deliverable**: Full env var support merged and tested

---

## Success Criteria

### P0-1 Success (Immediate)

- [ ] `claude mcp list` shows "✓ Connected" for design-patterns
- [ ] `claude mcp tools design-patterns` lists 6 tools
- [ ] Zero errors in Claude Code logs
- [ ] User can query pattern documentation

### P1-1 Success (Future)

- [ ] `mcpi add design-patterns` creates working config (no manual edits)
- [ ] Test pass rate ≥92% (no regressions)
- [ ] All existing servers continue working (backward compatibility)
- [ ] Documentation explains env var usage clearly
- [ ] At least 2 registry entries use env vars

---

## Risk Assessment

### P0-1 Risks: VERY LOW

- Config syntax error → Validate JSON, keep backup
- Wrong path → Use exact path from evaluation report
- Claude fails to reload → Restart Claude Code

### P1-1 Risks: LOW-MEDIUM

- Breaking backward compatibility → Make `env` field optional, extensive regression tests
- Schema validation failure → Update all validators together
- Cross-platform path issues → Document best practices, test on multiple OS
- Security (env var injection) → Validate env var names, document security

---

## Dependencies

```
P0-1: Update Claude Config
  └─> [ENABLES] P1-1: Add Env Var Support

P1-1: Add Env Var Support
  ├─> [ENABLES] P2-1: Path Interpolation
  └─> [ENABLES] P3-1: Env Var Validation
```

**Critical Path**: P0-1 → P1-1

**Parallel Work**: P2-1 and P3-1 can be done in any order after P1-1

---

## Technical Highlights

### Backward Compatibility

**Design Principle**: Additive, not breaking

- `env` field is optional (default `None`)
- Existing registry entries without `env` continue working
- Existing installed servers unaffected
- No re-installation required

### Test-Driven Development

**Approach**: Write tests FIRST (Sprint 1)

```python
def test_mcpserver_accepts_env_field():
    """MCPServer model should accept env field."""
    server = MCPServer(
        description="Test",
        command="node",
        args=["server.js"],
        env={"VAR": "value"}
    )
    assert server.env == {"VAR": "value"}
```

**Why**: Clarifies requirements, ensures testable design, fast feedback

### File Changes (P1-1)

**Estimated LOC**: ~200-250 lines total

**Files Modified**: 10 files
- Core: `catalog.py`, client plugins (3 files), `registry.json`
- Tests: `test_registry.py`, `test_cli_integration.py`, new test file
- Docs: `CLAUDE.md`, `README.md`, `CHANGELOG.md`

**Files Created**: 1 file
- `tests/test_env_var_support.py` (dedicated test suite)

---

## Comparison to Current MCPI State

**From STATUS-2025-11-07-051344.md**:
- MCPI: 93% complete, production-ready, ready to ship v2.0
- Test Pass Rate: 92% (589/640)
- All 13 CLI commands functional
- Zero blockers for MCPI itself

**This Plan**:
- Does NOT block MCPI v2.0 ship (P0 is outside MCPI)
- P1 is future enhancement (v2.1 or v2.0.1)
- Aligns with MCPI's "universal installation" goal
- Improves user experience for env-dependent servers

**Ship Decision**: MCPI v2.0 can ship immediately, P0-1 is independent, P1-1 is future work

---

## Key Insights

1. **Immediate vs Strategic**: P0 fixes the problem NOW, P1 prevents it FOREVER

2. **Scope Split**: P0 is a manual config edit (outside MCPI), P1 is feature addition (inside MCPI)

3. **Evidence-Based**: Evaluation report provides 100% confidence in root cause

4. **Low Risk**: Both P0 and P1 are low-risk (P0 trivial, P1 backward compatible)

5. **High Value**: Env var support significantly improves MCPI's value proposition

6. **Test-First**: TDD approach ensures quality implementation

7. **Incremental**: P2-P3 optional enhancements based on user feedback

---

## Next Actions

### Immediate (Today)

1. **Execute P0-1**: Update `~/.claude.json` configuration (2 minutes)
2. **Verify**: Test server connection (5 minutes)
3. **Confirm**: Document fix in issue tracker or planning notes

### This Week

1. **Design P1-1**: Schema changes and test strategy (2-3 hours)
2. **Write Tests**: Test-driven development for env var support (3-4 hours)
3. **Review**: Get feedback on design before implementation

### Next 2 Weeks

1. **Implement P1-1**: Add env var support to MCPI (3-5 days)
2. **Test**: Validate all tests pass, no regressions
3. **Document**: Update all docs with env var usage
4. **Ship**: Merge and release as v2.0.1 or v2.1

---

## Confidence Level

**P0-1**: 100% confidence
- Root cause confirmed through testing
- Fix documented in server's README
- Trivial config change
- Easily reverted if issues

**P1-1**: High confidence (9/10)
- Well-scoped feature (additive, backward compatible)
- Clear acceptance criteria
- Test-driven approach reduces risk
- Similar patterns exist in codebase

**Overall**: High confidence in plan quality and execution path

---

## File Management

**PLAN Files** (current count: 3):
- PLAN-2025-10-30-062544.md (Oct 30)
- PLAN-2025-11-07-052005.md (Nov 7)
- PLAN-2025-11-09-052500.md (Nov 9) ← THIS PLAN

**Action**: No cleanup required (3 < 4 file limit)

**PLANNING-SUMMARY Files** (current count: 5):
- PLANNING-SUMMARY-2025-10-30.md
- PLANNING-SUMMARY-2025-11-05.md
- PLANNING-SUMMARY-2025-11-06.md
- PLANNING-SUMMARY-DIP-2025-11-07-010528.md
- PLANNING-SUMMARY-2025-11-07-052005.md
- PLANNING-SUMMARY-2025-11-09-052500.md ← THIS FILE

**Action**: Delete oldest (PLANNING-SUMMARY-2025-10-30.md) to maintain 4-file limit

---

**END OF PLANNING SUMMARY**

Generated: 2025-11-09 05:25:00
Author: Claude Code (Project Planner)
Project: MCPI - Design Patterns MCP Server Fix
Status: Ready for execution (P0-1 can start immediately)
