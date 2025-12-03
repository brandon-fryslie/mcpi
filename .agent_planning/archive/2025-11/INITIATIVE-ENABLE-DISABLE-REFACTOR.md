# INITIATIVE: Enable/Disable Architectural Refactor (1.1)

**Initiative ID**: 1.1-ARCH-REFACTOR
**Target Release**: 1.1 (2025-11-11, ~1 week after 1.0)
**Effort**: 10-15 hours (5-7 days, 2-3 hours/day)
**Priority**: P1 (Important, not blocking)
**Status**: PLANNED (starts after 1.0 ships)
**Dependencies**: 1.0 release complete (2025-11-03)

**Source Documents**:
- EVALUATION-ENABLE-DISABLE-2025-10-28.md (technical assessment)
- DECISION-ENABLE-DISABLE-REFACTOR.md (decision rationale)
- User requirements from project discussion

---

## Executive Summary

### Problem Statement

Current architecture violates user requirements and maintainability principles:
- All client code in single monolithic file (`claude_code.py`, 518 lines)
- All scope handlers in shared file (`file_based.py`, 558 lines)
- Enable/disable logic hardcoded in client plugin
- No separation between scope-specific behaviors
- Adding new clients (cursor, vscode) requires duplicating 500-line files

### Solution Overview

Refactor to modular, scope-based architecture:
- Each client in separate directory with subdirectories for scopes
- Each scope in separate file (~100 lines each)
- Enable/disable handlers separated by scope type
- Protocol-based design for scope capabilities
- Reduced code duplication (~200 lines → 0)

### User Requirements Alignment

**Before Refactor**:
1. ❌ Each client in separate directory: 0%
2. ❌ Each scope in separate file: 0%
3. ⚠️ Separate enable/disable handlers: 40%
4. ✅ Tracking disabled servers: 100%
5. ✅ Display in `mcpi list`: 100%
**Overall**: 48% satisfaction

**After Refactor**:
1. ✅ Each client in separate directory: 100%
2. ✅ Each scope in separate file: 100%
3. ✅ Separate enable/disable handlers: 100%
4. ✅ Tracking disabled servers: 100%
5. ✅ Display in `mcpi list`: 100%
**Overall**: 100% satisfaction

### Success Criteria

**Must Have**:
- [ ] All existing tests pass (474/556 maintained or improved)
- [ ] Enable/disable functionality unchanged from user perspective
- [ ] Zero breaking changes to public API
- [ ] No performance regression (< 5% slower)
- [ ] Test pass rate maintained (85.3%+)

**Should Have**:
- [ ] Improved test coverage (40% → 50%+)
- [ ] Reduced code duplication (200 lines → 0)
- [ ] Better documentation of architecture
- [ ] All user requirements met (100%)

**Nice to Have**:
- [ ] Example cursor/vscode client implementation
- [ ] Architecture documentation (ARCHITECTURE.md)
- [ ] Contributor guide updates

---

## Current Architecture Analysis

### Directory Structure (Before)

```
src/mcpi/clients/
├── __init__.py             # 500 bytes
├── base.py                 # 8,550 bytes (329 lines)
├── claude_code.py          # 19,003 bytes (518 lines) ← REFACTOR
├── file_based.py           # 18,210 bytes (558 lines) ← REFACTOR
├── manager.py              # 14,700 bytes (423 lines)
├── protocols.py            # 3,132 bytes (92 lines)
├── registry.py             # 14,344 bytes (423 lines)
├── types.py                # 3,014 bytes (115 lines)
└── schemas/
    ├── claude-settings-schema.yaml
    ├── internal-config-schema.yaml
    └── mcp-config-schema.yaml

Total: 2,458 lines (80,953 bytes)
```

### Problems Identified

**1. Monolithic Client Files** (518 lines in `claude_code.py`):
- Hard to navigate (518 lines)
- Multiple responsibilities mixed
- Violates single responsibility principle
- Example responsibilities:
  - Scope initialization (90 lines)
  - State determination (40 lines)
  - Enable/disable operations (104 lines)
  - List servers logic (44 lines)
  - Add/remove delegation (40 lines)
  - Validation (30 lines)
  - Installation detection (35 lines)

**2. No Scope-Specific Handlers**:
- `FileBasedScope` is generic (knows nothing about enable/disable)
- Enable/disable logic lives in CLIENT, not SCOPE
- Different scopes have different formats, but use same handler
- No way to extend per-scope behavior

**3. Hardcoded Scope Lists**:
- `settings_scopes = ["project-local", "user-local", "user-global"]` appears 3 times
- Adding new scope requires updating 3 locations
- DRY violation

**4. No Enable/Disable Protocols**:
- No way to query "which scopes support enable/disable?"
- Client has to know implementation details
- Cannot use `isinstance(scope, EnableDisableSupport)`

**5. Code Duplication**:
- `enable_server()` and `disable_server()` are 95% identical (100+ lines duplicated)
- Array manipulation logic repeated
- File I/O logic repeated

---

## Target Architecture

### Directory Structure (After)

```
src/mcpi/clients/
├── base/
│   ├── __init__.py             # Exports
│   ├── plugin.py               # MCPClientPlugin base (200 lines)
│   ├── scope.py                # ScopeHandler base (150 lines)
│   └── enable_disable.py       # EnableDisableSupport protocol (80 lines)
├── claude_code/
│   ├── __init__.py             # Plugin export
│   ├── plugin.py               # ClaudeCodePlugin (150 lines)
│   ├── scopes/
│   │   ├── __init__.py         # Scope exports
│   │   ├── base.py             # Shared utilities (120 lines)
│   │   ├── project_mcp.py      # ProjectMcpScope (80 lines)
│   │   ├── project_local.py    # ProjectLocalScope (120 lines)
│   │   ├── user_local.py       # UserLocalScope (120 lines)
│   │   ├── user_global.py      # UserGlobalScope (120 lines)
│   │   ├── user_internal.py    # UserInternalScope (80 lines)
│   │   └── user_mcp.py         # UserMcpScope (80 lines)
│   └── schemas/
│       ├── claude-settings-schema.yaml
│       ├── internal-config-schema.yaml
│       └── mcp-config-schema.yaml
├── cursor/                     # Future: Cursor client
│   ├── __init__.py
│   ├── plugin.py
│   └── scopes/
│       └── ...
├── shared/
│   ├── __init__.py
│   ├── file_reader.py          # JSONFileReader (100 lines)
│   ├── file_writer.py          # JSONFileWriter (100 lines)
│   └── validators.py           # YAMLSchemaValidator (150 lines)
├── manager.py                  # MCPManager (unchanged)
├── protocols.py                # Protocols (unchanged)
├── registry.py                 # ClientRegistry (unchanged)
└── types.py                    # Types (unchanged)

Total: 2,703 lines (+245 lines, -200 duplicate = +45 net)
```

### Key Design Changes

**1. Client Directories**: Each client in own directory
- `claude_code/` contains all Claude Code logic
- `cursor/` (future) contains all Cursor logic
- Clear separation, no mixing

**2. Scope Files**: Each scope in separate file
- `project_mcp.py` = project MCP scope (80 lines)
- `project_local.py` = project settings scope (120 lines)
- Single responsibility per file
- Easy to understand and modify

**3. Scope Class Hierarchy**: Inheritance for shared behavior
- `ScopeHandler` = base for all scopes
- `ClaudeSettingsScope` = base for settings files (with enable/disable)
- `ClaudeMcpScope` = base for MCP config files (no enable/disable)
- `ProjectLocalScope extends ClaudeSettingsScope` = inherits enable/disable

**4. Protocol-Based Design**: Capability detection
- `EnableDisableSupport` protocol
- `isinstance(scope, EnableDisableSupport)` = True for settings scopes
- Plugin delegates to scopes, doesn't know implementation

**5. Shared Utilities**: Eliminate duplication
- `file_reader.py` = JSON/YAML reading
- `file_writer.py` = JSON/YAML writing
- `validators.py` = schema validation
- Used by all scopes, no duplication

---

## Implementation Plan

### Phase 1: Create New Structure (2 hours)

**Goal**: Set up directory structure, move base classes

**Tasks**:
1. Create `clients/base/` directory (5 min)
2. Create `clients/base/plugin.py` (move base classes) (30 min)
3. Create `clients/base/scope.py` (move base classes) (30 min)
4. Create `clients/base/enable_disable.py` (new protocol) (30 min)
5. Create `clients/shared/` directory (5 min)
6. Create `clients/shared/file_reader.py` (extract from file_based.py) (20 min)
7. Create `clients/shared/file_writer.py` (extract from file_based.py) (20 min)
8. Create `clients/shared/validators.py` (extract from file_based.py) (20 min)
9. Create `clients/claude_code/` directory structure (5 min)
10. Create `clients/claude_code/scopes/` directory (5 min)

**Deliverables**:
- [ ] `clients/base/` with 3 files
- [ ] `clients/shared/` with 3 files
- [ ] `clients/claude_code/scopes/` directory
- [ ] All imports updated in existing files

**Acceptance Criteria**:
- [ ] Directory structure matches target
- [ ] Base classes compile without errors
- [ ] No import errors in existing code
- [ ] All tests still run (may fail, but run)

**Risk**: LOW (directory creation, code movement)

---

### Phase 2: Extract Scope Classes (4 hours)

**Goal**: Create scope classes for each of 6 Claude Code scopes

**Tasks**:

**2.1: Create Base Scope Classes** (1 hour)
1. Create `claude_code/scopes/base.py` (30 min)
   - `ClaudeSettingsScope` class with enable/disable methods
   - `ClaudeMcpScope` class without enable/disable
2. Implement `EnableDisableSupport` protocol compliance (30 min)
   - `get_enabled_servers()`
   - `get_disabled_servers()`
   - `is_server_enabled()`
   - `is_server_disabled()`
   - `enable_server()`
   - `disable_server()`

**2.2: Create Settings Scope Files** (2 hours)
1. Create `project_local.py` - ProjectLocalScope (40 min)
   - Extends `ClaudeSettingsScope`
   - Path: `{cwd}/.claude/settings.local.json`
   - Schema: `claude-settings-schema.yaml`
   - Priority: 2
2. Create `user_local.py` - UserLocalScope (40 min)
   - Extends `ClaudeSettingsScope`
   - Path: `~/.claude/settings.local.json`
   - Priority: 3
3. Create `user_global.py` - UserGlobalScope (40 min)
   - Extends `ClaudeSettingsScope`
   - Path: `~/.claude/settings.json`
   - Priority: 4

**2.3: Create MCP Scope Files** (1 hour)
1. Create `project_mcp.py` - ProjectMcpScope (30 min)
   - Extends `ClaudeMcpScope`
   - Path: `{cwd}/.mcp.json`
   - Priority: 1
2. Create `user_mcp.py` - UserMcpScope (30 min)
   - Extends `ClaudeMcpScope`
   - Path: `~/.claude/mcp_servers.json`
   - Priority: 6
3. Create `user_internal.py` - UserInternalScope (30 min)
   - Special case (internal format)
   - Path: `~/.claude.json`
   - Priority: 5

**Deliverables**:
- [ ] `claude_code/scopes/base.py` (120 lines)
- [ ] 6 scope files (80-120 lines each)
- [ ] All scopes implement required abstract methods
- [ ] Settings scopes implement `EnableDisableSupport` protocol

**Acceptance Criteria**:
- [ ] All scope classes compile
- [ ] All scope classes pass isinstance checks
- [ ] Settings scopes have enable/disable methods
- [ ] MCP scopes do NOT have enable/disable methods
- [ ] Code duplication eliminated (enable/disable logic in base class)

**Risk**: MEDIUM (complex logic extraction, but well-understood)

---

### Phase 3: Simplify Plugin (1 hour)

**Goal**: Rewrite `claude_code/plugin.py` to use new scope classes

**Tasks**:
1. Rewrite `_initialize_scopes()` to import scope classes (20 min)
2. Simplify `enable_server()` to delegate to scope (10 min)
3. Simplify `disable_server()` to delegate to scope (10 min)
4. Simplify `_get_server_state()` to query scopes (10 min)
5. Remove hardcoded scope lists (5 min)
6. Remove direct file manipulation (5 min)

**Before** (100+ lines of enable/disable logic):
```python
def enable_server(self, server_id: str) -> OperationResult:
    settings_scopes = ["project-local", "user-local", "user-global"]
    for scope_name in settings_scopes:
        handler = self._scopes[scope_name]
        # 50+ lines of array manipulation, file I/O
```

**After** (10 lines of delegation):
```python
def enable_server(self, server_id: str) -> OperationResult:
    for scope_name, handler in self._scopes.items():
        if isinstance(handler, EnableDisableSupport):
            if handler.has_server(server_id):
                return handler.enable_server(server_id)
    return OperationResult.failure_result(f"Server {server_id} not found")
```

**Deliverables**:
- [ ] `claude_code/plugin.py` reduced to ~150 lines (from 518)
- [ ] All logic delegated to scopes
- [ ] No hardcoded scope lists
- [ ] No direct file manipulation

**Acceptance Criteria**:
- [ ] Plugin compiles
- [ ] Plugin passes type checking
- [ ] Plugin initializes all 6 scopes
- [ ] Plugin delegates enable/disable to scopes
- [ ] Code reduced by ~70% (518 → 150 lines)

**Risk**: MEDIUM (significant code changes, but straightforward delegation)

---

### Phase 4: Update Tests (2 hours)

**Goal**: Update all tests to use new structure, add new tests

**Tasks**:

**4.1: Update Imports** (30 min)
1. Find all `from mcpi.clients.claude_code import ...` (10 min)
2. Update to `from mcpi.clients.claude_code.plugin import ...` (10 min)
3. Find all `from mcpi.clients.file_based import ...` (10 min)
4. Update to `from mcpi.clients.shared.file_reader import ...` (10 min)

**4.2: Update Fixtures** (30 min)
1. Update `conftest.py` to use new imports (15 min)
2. Update `test_clients_claude_code.py` fixtures (15 min)

**4.3: Add Scope-Specific Tests** (45 min)
1. Test `ClaudeSettingsScope` enable/disable (15 min)
2. Test `ClaudeMcpScope` no enable/disable (15 min)
3. Test protocol compliance (`isinstance`) (15 min)

**4.4: Add Protocol Compliance Tests** (15 min)
1. Test `EnableDisableSupport` detection (10 min)
2. Test scope capability queries (5 min)

**Deliverables**:
- [ ] All imports updated
- [ ] All fixtures updated
- [ ] 10+ new scope-specific tests
- [ ] 5+ new protocol tests

**Acceptance Criteria**:
- [ ] All existing tests run (may fail, but run)
- [ ] Import errors eliminated
- [ ] Fixture errors eliminated
- [ ] New tests pass

**Risk**: MEDIUM (test updates can reveal issues, but we have good test harness)

---

### Phase 5: Verification & Cleanup (1 hour)

**Goal**: Ensure refactor is complete, functional, and clean

**Tasks**:

**5.1: Run Full Test Suite** (20 min)
1. `pytest --tb=short -v` (10 min)
2. Review failures (5 min)
3. Fix obvious issues (5 min)

**5.2: Manual Testing** (20 min)
1. Test enable/disable for `project-local` (5 min)
   ```bash
   mcpi install test-server --scope project-local
   mcpi disable test-server
   mcpi list  # Should show DISABLED
   mcpi enable test-server
   mcpi list  # Should show ENABLED
   ```
2. Test enable/disable for `user-global` (5 min)
3. Test `project-mcp` (no enable/disable) (5 min)
4. Test CLI output unchanged (5 min)

**5.3: Verify File Formats** (10 min)
1. Check `.claude/settings.local.json` format (5 min)
   - `enabledMcpjsonServers` array correct
   - `disabledMcpjsonServers` array correct
2. Check `.mcp.json` format (5 min)
   - No enable/disable arrays

**5.4: Clean Up Old Files** (10 min)
1. Delete `clients/file_based.py` (old version) (2 min)
2. Delete `clients/base.py` (moved to `clients/base/plugin.py`) (2 min)
3. Update `clients/__init__.py` exports (3 min)
4. Grep for old import paths (3 min)

**Deliverables**:
- [ ] Test suite passing (85.3%+ maintained)
- [ ] Manual testing confirms enable/disable works
- [ ] File formats verified unchanged
- [ ] Old files deleted
- [ ] Import paths verified

**Acceptance Criteria**:
- [ ] Test pass rate ≥ 85.3%
- [ ] Enable/disable functional (manual test)
- [ ] No old import paths remain
- [ ] No orphaned files

**Risk**: LOW (verification and cleanup, minimal changes)

---

## Test Strategy

### Regression Prevention

**Goal**: Ensure refactor doesn't break existing functionality

**Approach**:
1. **Run tests after each phase** (not just at end)
2. **Fix failures immediately** (don't accumulate)
3. **Use git branches** (easy rollback if needed)
4. **Manual testing** (CLI commands after each phase)

**Test Checkpoints**:
- After Phase 1: Tests run (may fail, but no import errors)
- After Phase 2: Scope classes pass basic tests
- After Phase 3: Plugin tests pass
- After Phase 4: All tests updated and passing
- After Phase 5: Full manual + automated testing

### New Tests to Add

**Protocol Compliance Tests**:
```python
def test_settings_scopes_support_enable_disable():
    """Settings scopes should implement EnableDisableSupport."""
    from mcpi.clients.base.enable_disable import EnableDisableSupport
    from mcpi.clients.claude_code.scopes import (
        ProjectLocalScope, UserLocalScope, UserGlobalScope
    )

    assert isinstance(ProjectLocalScope(), EnableDisableSupport)
    assert isinstance(UserLocalScope(), EnableDisableSupport)
    assert isinstance(UserGlobalScope(), EnableDisableSupport)

def test_mcp_scopes_do_not_support_enable_disable():
    """MCP scopes should NOT implement EnableDisableSupport."""
    from mcpi.clients.base.enable_disable import EnableDisableSupport
    from mcpi.clients.claude_code.scopes import ProjectMcpScope, UserMcpScope

    assert not isinstance(ProjectMcpScope(), EnableDisableSupport)
    assert not isinstance(UserMcpScope(), EnableDisableSupport)
```

**Scope-Specific Tests**:
```python
def test_project_local_scope_enable_server(scope_harness):
    """ProjectLocalScope should enable server using arrays."""
    scope = ProjectLocalScope(path=scope_harness.project_local_path)
    scope.add_server("test-server", {"command": "test", "args": []})
    scope.disable_server("test-server")

    result = scope.enable_server("test-server")

    assert result.success
    assert scope.is_server_enabled("test-server")
    assert not scope.is_server_disabled("test-server")

    # Verify file format
    data = scope.reader.read(scope.config.path)
    assert "test-server" in data["enabledMcpjsonServers"]
    assert "test-server" not in data["disabledMcpjsonServers"]
```

### Coverage Goals

**Current**: 40%
**Target for 1.1**: 50%+

**Areas to Add Coverage**:
1. Scope class methods (get_servers, add_server, remove_server)
2. Enable/disable protocol compliance
3. Plugin delegation logic
4. Error handling in scopes

---

## Migration Path

### Backwards Compatibility

**Public API**: ZERO breaking changes
- `mcpi enable <server>` - unchanged
- `mcpi disable <server>` - unchanged
- `mcpi list` - unchanged
- File formats - unchanged

**Internal API**: Breaking changes OK (internal only)
- `ClaudeCodePlugin._initialize_scopes()` - changed (private method)
- `FileBasedScope` - moved/deleted (internal class)
- Import paths - changed (internal imports)

### User-Facing Changes

**NONE** - This is purely internal refactor

Users will NOT notice:
- ✅ Same CLI commands
- ✅ Same file formats
- ✅ Same behavior
- ✅ Same output

Only contributors will notice:
- ✅ Cleaner directory structure
- ✅ Smaller files (easier to understand)
- ✅ Clear scope responsibilities

### Configuration Migration

**NONE NEEDED** - File formats unchanged

- `.claude/settings.local.json` - format unchanged
- `.mcp.json` - format unchanged
- `~/.claude/settings.json` - format unchanged

---

## Risk Assessment & Mitigation

### Risk 1: Breaking Changes (Probability: 30%, Impact: HIGH)

**Description**: Refactor breaks enable/disable functionality

**Mitigation**:
1. Keep existing tests unchanged (just update imports)
2. Run tests after each phase
3. Manual testing after each phase
4. Use test harness for all testing
5. Git branches for easy rollback

**Contingency**:
- If break detected: Roll back to previous phase
- Fix issue before proceeding
- Don't accumulate technical debt

**Success Indicator**: All 474 passing tests still pass (or more)

---

### Risk 2: Test Failures (Probability: 60%, Impact: MEDIUM)

**Description**: Tests fail after refactor due to import/fixture issues

**Mitigation**:
1. Update imports systematically (grep for old paths)
2. Update fixtures before scope changes
3. Run tests frequently (after each file change)
4. Fix failures immediately (don't batch)

**Contingency**:
- Budget 2 hours for test fixes (included in Phase 4)
- If > 2 hours needed: Pause, reassess approach
- Ask for help if stuck

**Success Indicator**: Test pass rate ≥ 85.3%

---

### Risk 3: Incomplete Migration (Probability: 40%, Impact: HIGH)

**Description**: Some code paths still use old structure

**Mitigation**:
1. Grep for old import paths after migration
2. Delete old files only after all tests pass
3. Code review focusing on import statements
4. Search for `from mcpi.clients.file_based` (should be 0 results)

**Contingency**:
- If found: Update immediately
- Run full test suite after each fix

**Success Indicator**: 0 references to old import paths

---

### Risk 4: Performance Regression (Probability: 10%, Impact: LOW)

**Description**: New architecture is slower

**Mitigation**:
1. Benchmark before refactor (time `mcpi list`)
2. Benchmark after refactor
3. Compare (should be < 5% difference)
4. Use lazy loading of scope classes

**Contingency**:
- If > 5% slower: Profile and optimize
- Consider caching if needed

**Success Indicator**: < 5% performance change

---

## Success Criteria

### Must Have (Blocking 1.1)

- [ ] All existing tests pass (474/556 maintained or improved)
- [ ] Enable/disable functionality unchanged from user perspective
- [ ] Zero breaking changes to public API
- [ ] No performance regression (< 5% slower)
- [ ] Test pass rate maintained (85.3%+)
- [ ] All 6 scopes in separate files
- [ ] All clients in separate directories
- [ ] Enable/disable handlers separated by scope type

### Should Have (Important for 1.1)

- [ ] Improved test coverage (40% → 50%+)
- [ ] Reduced code duplication (200 lines → 0)
- [ ] Better documentation of architecture
- [ ] All user requirements met (100%)
- [ ] Protocol-based enable/disable detection
- [ ] Cleaner plugin code (518 → 150 lines)

### Nice to Have (Optional for 1.1)

- [ ] Example cursor/vscode client implementation
- [ ] Architecture documentation (ARCHITECTURE.md)
- [ ] Contributor guide updates
- [ ] Performance improvements (lazy loading)

---

## Timeline & Milestones

### Post-1.0 Schedule

**1.0 Release**: 2025-11-03 (Day 6)

**1.1 Planning**: 2025-11-04 (Day 7)
- Review this initiative document
- Confirm approach
- Create git branch `refactor/enable-disable-1.1`

**1.1 Implementation**: 2025-11-05 to 2025-11-09 (Days 8-12)
- Day 8: Phase 1 (Create structure, 2 hours)
- Day 9: Phase 2 (Extract scopes, 4 hours)
- Day 10: Phase 3 (Simplify plugin, 1 hour) + Phase 4 start (Update tests, 1 hour)
- Day 11: Phase 4 complete (Update tests, 1 hour) + Phase 5 (Verification, 1 hour)
- Day 12: Buffer day (fix any issues, 2-4 hours)

**1.1 Testing**: 2025-11-10 (Day 13)
- Full test suite (1 hour)
- Manual testing (1 hour)
- Performance benchmarking (30 min)
- Documentation updates (30 min)

**1.1 Release**: 2025-11-11 (Day 14)
- Version bump to 1.1.0
- CHANGELOG update
- Release notes
- Tag and ship

**Total Timeline**: 8 days (1 planning + 5 implementation + 1 testing + 1 release)
**Total Effort**: 10-15 hours over 8 days (1.25-2 hours/day average)

---

## Metrics & Tracking

### Code Metrics

**Before Refactor**:
- Total lines: 2,458
- Files: 8
- Largest file: 558 lines (`file_based.py`)
- Code duplication: ~200 lines
- Cyclomatic complexity: ~15 per method

**After Refactor**:
- Total lines: 2,703 (+245, -200 duplicate = +45 net)
- Files: 18 (+10 scope files, +3 base files, +3 shared files, -2 old files)
- Largest file: 200 lines (`base/plugin.py`)
- Code duplication: 0 lines
- Cyclomatic complexity: ~5 per method

**Improvement**:
- Files: +10 (better separation)
- Largest file: -65% (558 → 200)
- Duplication: -100% (200 → 0)
- Complexity: -67% (15 → 5)

### Test Metrics

**Before Refactor**:
- Pass rate: 85.3% (474/556)
- Coverage: 40%
- Scope-specific tests: 0
- Protocol tests: 0

**After Refactor** (Target):
- Pass rate: ≥ 85.3% (maintained or improved)
- Coverage: ≥ 50% (+10 percentage points)
- Scope-specific tests: 10+ (new)
- Protocol tests: 5+ (new)

### User Requirements Metrics

**Before Refactor**: 48% satisfaction
1. Client directories: 0%
2. Scope files: 0%
3. Enable/disable handlers: 40%
4. Tracking disabled: 100%
5. Display in list: 100%

**After Refactor** (Target): 100% satisfaction
1. Client directories: 100%
2. Scope files: 100%
3. Enable/disable handlers: 100%
4. Tracking disabled: 100%
5. Display in list: 100%

---

## Communication Plan

### Before Refactor (Post-1.0)

**Announce in CHANGELOG.md** (1.0 release):
```markdown
### Known Issues
- Monolithic client architecture (will be refactored in 1.1)

### Planned for 1.1
- Modular client/scope architecture
- Each client in separate directory
- Each scope in separate file
- Improved code maintainability
```

**Announce in Release Notes** (1.0):
> MCPI 1.0 ships with a functional, tested architecture. Version 1.1 (planned for ~1 week post-release) will include an architectural refactor to improve code maintainability and modularity. This refactor will not change any user-facing functionality.

### During Refactor

**Git Commits**:
- `refactor(clients): create base/ and shared/ directories`
- `refactor(claude_code): extract scope classes`
- `refactor(claude_code): simplify plugin to delegate to scopes`
- `test(clients): update tests for new structure`
- `chore: delete old client files`

**Progress Updates** (in git branch):
- Phase 1 complete: Structure created
- Phase 2 complete: Scopes extracted
- Phase 3 complete: Plugin simplified
- Phase 4 complete: Tests updated
- Phase 5 complete: Verification done

### After Refactor (1.1 Release)

**Announce in CHANGELOG.md** (1.1 release):
```markdown
### Changed
- **BREAKING (Internal API Only)**: Refactored client architecture
  - Each client now in separate directory
  - Each scope in separate file
  - Enable/disable handlers separated by scope type
  - Reduced code duplication by 200 lines
  - No user-facing changes

### Improved
- Code maintainability (largest file reduced from 558 to 200 lines)
- Separation of concerns (18 files vs 8, better organization)
- Test coverage (40% → 50%)
```

**Announce in Release Notes** (1.1):
> MCPI 1.1 includes a major architectural refactor that improves code maintainability and modularity. **This refactor does not change any user-facing functionality** - all CLI commands, file formats, and behaviors remain identical. Contributors will find the codebase easier to navigate with each client in its own directory and each scope in its own file.

---

## Dependencies & Prerequisites

### Before Starting Refactor

**Prerequisites**:
- [ ] 1.0 released successfully (2025-11-03)
- [ ] Test pass rate at 85.3%+ in 1.0
- [ ] Enable/disable functionality verified working in 1.0
- [ ] This initiative document reviewed and approved

### External Dependencies

**NONE** - Internal refactor, no external dependencies

### Blocker Risks

**NONE** - Can start immediately after 1.0 ships

---

## Rollback Plan

### If Refactor Fails

**Scenario**: Refactor introduces regressions, tests fail, timeline slips

**Rollback Steps**:
1. Revert git branch to `main`
2. Delete `refactor/enable-disable-1.1` branch
3. Ship 1.1 with other improvements (if any)
4. Defer refactor to 1.2 or later

**Decision Points**:
- If Phase 1-2 fail: Rollback immediately (low cost)
- If Phase 3 fails: Rollback and reassess (medium cost)
- If Phase 4-5 fail: Fix issues, don't rollback (high cost)

**Rollback Threshold**: If > 2 days behind schedule OR test pass rate drops below 80%

---

## Appendix: Code Examples

### Example: ClaudeSettingsScope Base Class

```python
# claude_code/scopes/base.py

from typing import Dict, List, Any
from mcpi.clients.base.scope import ScopeHandler
from mcpi.clients.base.enable_disable import EnableDisableSupport
from mcpi.clients.shared.file_reader import JSONFileReader
from mcpi.clients.shared.file_writer import JSONFileWriter
from mcpi.clients.types import OperationResult


class ClaudeSettingsScope(ScopeHandler):
    """Base class for Claude settings files supporting enable/disable."""

    def __init__(self, path: str, schema_path: str, priority: int):
        self.path = path
        self.schema_path = schema_path
        self.priority = priority
        self.reader = JSONFileReader()
        self.writer = JSONFileWriter()

    def get_enabled_servers(self) -> List[str]:
        """Get list of explicitly enabled servers."""
        if not self.exists():
            return []
        data = self.reader.read(self.path)
        return data.get("enabledMcpjsonServers", [])

    def get_disabled_servers(self) -> List[str]:
        """Get list of explicitly disabled servers."""
        if not self.exists():
            return []
        data = self.reader.read(self.path)
        return data.get("disabledMcpjsonServers", [])

    def is_server_enabled(self, server_id: str) -> bool:
        """Check if server is explicitly enabled."""
        return server_id in self.get_enabled_servers()

    def is_server_disabled(self, server_id: str) -> bool:
        """Check if server is explicitly disabled."""
        return server_id in self.get_disabled_servers()

    def enable_server(self, server_id: str) -> OperationResult:
        """Enable a server by adding to enabled array, removing from disabled."""
        data = self.reader.read(self.path) if self.exists() else {}

        enabled = data.get("enabledMcpjsonServers", [])
        disabled = data.get("disabledMcpjsonServers", [])

        # Remove from disabled if present
        if server_id in disabled:
            disabled.remove(server_id)

        # Add to enabled if not already there
        if server_id not in enabled:
            enabled.append(server_id)

        # Update data
        data["enabledMcpjsonServers"] = enabled
        data["disabledMcpjsonServers"] = disabled

        # Write to file
        self.writer.write(self.path, data)
        return OperationResult.success_result(f"Enabled {server_id} in {self.path}")

    def disable_server(self, server_id: str) -> OperationResult:
        """Disable a server by adding to disabled array, removing from enabled."""
        data = self.reader.read(self.path) if self.exists() else {}

        enabled = data.get("enabledMcpjsonServers", [])
        disabled = data.get("disabledMcpjsonServers", [])

        # Remove from enabled if present
        if server_id in enabled:
            enabled.remove(server_id)

        # Add to disabled if not already there
        if server_id not in disabled:
            disabled.append(server_id)

        # Update data
        data["enabledMcpjsonServers"] = enabled
        data["disabledMcpjsonServers"] = disabled

        # Write to file
        self.writer.write(self.path, data)
        return OperationResult.success_result(f"Disabled {server_id} in {self.path}")
```

### Example: ProjectLocalScope

```python
# claude_code/scopes/project_local.py

from pathlib import Path
from .base import ClaudeSettingsScope


class ProjectLocalScope(ClaudeSettingsScope):
    """Project-local settings scope (.claude/settings.local.json)."""

    def __init__(self, cwd: str):
        path = str(Path(cwd) / ".claude" / "settings.local.json")
        schema_path = "claude_code/schemas/claude-settings-schema.yaml"
        super().__init__(path=path, schema_path=schema_path, priority=2)

    def exists(self) -> bool:
        """Check if project-local settings file exists."""
        return Path(self.path).exists()

    # All other methods inherited from ClaudeSettingsScope
    # get_enabled_servers(), get_disabled_servers(),
    # enable_server(), disable_server(), etc.
```

### Example: Simplified Plugin

```python
# claude_code/plugin.py

from mcpi.clients.base.plugin import MCPClientPlugin
from mcpi.clients.base.enable_disable import EnableDisableSupport
from mcpi.clients.types import OperationResult, ServerState


class ClaudeCodePlugin(MCPClientPlugin):
    """Claude Code client plugin."""

    def _initialize_scopes(self) -> Dict[str, ScopeHandler]:
        """Initialize scopes by importing scope classes."""
        from .scopes import (
            ProjectMcpScope,
            ProjectLocalScope,
            UserLocalScope,
            UserGlobalScope,
            UserInternalScope,
            UserMcpScope,
        )

        cwd = os.getcwd()
        return {
            "project-mcp": ProjectMcpScope(cwd),
            "project-local": ProjectLocalScope(cwd),
            "user-local": UserLocalScope(),
            "user-global": UserGlobalScope(),
            "user-internal": UserInternalScope(),
            "user-mcp": UserMcpScope(),
        }

    def enable_server(self, server_id: str) -> OperationResult:
        """Enable server by delegating to first supporting scope."""
        for scope_name, handler in self._scopes.items():
            if isinstance(handler, EnableDisableSupport):
                if handler.has_server(server_id):
                    return handler.enable_server(server_id)

        return OperationResult.failure_result(
            f"Server {server_id} not found in any enable/disable scope"
        )

    def disable_server(self, server_id: str) -> OperationResult:
        """Disable server by delegating to first supporting scope."""
        for scope_name, handler in self._scopes.items():
            if isinstance(handler, EnableDisableSupport):
                if handler.has_server(server_id):
                    return handler.disable_server(server_id)

        return OperationResult.failure_result(
            f"Server {server_id} not found in any enable/disable scope"
        )

    def _get_server_state(self, server_id: str) -> ServerState:
        """Get state by asking scopes that support enable/disable."""
        for scope_name, handler in self._scopes.items():
            if isinstance(handler, EnableDisableSupport):
                if handler.is_server_disabled(server_id):
                    return ServerState.DISABLED
                if handler.is_server_enabled(server_id):
                    return ServerState.ENABLED

        # Default: if server exists in any scope but not in enable/disable arrays
        if self.find_server_scope(server_id):
            return ServerState.ENABLED

        return ServerState.NOT_INSTALLED
```

---

## Conclusion

This refactor represents a significant architectural improvement that:
- ✅ Meets 100% of user requirements (up from 48%)
- ✅ Improves code maintainability (largest file -65%)
- ✅ Eliminates code duplication (-100%, 200 lines)
- ✅ Maintains all user-facing functionality (zero breaking changes)
- ✅ Reduces complexity (cyclomatic complexity -67%)

**Estimated Effort**: 10-15 hours over 5-7 days
**Risk Level**: MEDIUM (mitigated by phased approach and good tests)
**Timeline**: 1.1 release ~2025-11-11 (1 week after 1.0)

**Recommendation**: Proceed with refactor in 1.1 after successful 1.0 release.

---

**END OF INITIATIVE DOCUMENT**
