# MCPI Post-v2.0 Roadmap

**Generated**: 2025-11-16 07:36:37
**Source STATUS**: STATUS-2025-11-16-184500.md (v2.0 SHIP-READY)
**Source PLAN**: PLAN-2025-11-16-070237.md (Deferred Work)
**Current State**: v2.0 Ready to Ship (93% test pass rate, all features working)
**Planning Horizon**: 3 months post-ship

---

## Executive Summary

MCPI v2.0 is **fully operational and ready to ship**. This roadmap organizes the remaining work into three post-ship releases:

- **v2.0.1** (1 week): Test quality improvements → 98%+ pass rate
- **v2.1** (1 month): DIP Phase 2 architecture refactoring
- **v2.2+** (Future): DIP Phases 3-4 and additional features

### Current State (v2.0)
- ✅ All CLI commands working
- ✅ All core features implemented
- ✅ 93% test pass rate (644/692 passing)
- ✅ Zero production bugs identified
- ⚠️ 33 failing tests are test quality issues (not production bugs)

### Post-Ship Strategy
1. **Ship v2.0 NOW** - All critical functionality complete
2. **Quick fix in v2.0.1** - Improve test quality to 98%+
3. **Architecture improvements in v2.1** - DIP Phase 2 for better testability
4. **Future enhancements in v2.2+** - Complete DIP implementation

---

## Version 2.0.1 - Test Quality Improvements

**Timeline**: 1 week post-ship
**Effort**: 4-5 hours total
**Goal**: Achieve 98%+ test pass rate by fixing test implementation issues

### Scope

All 33 failing tests are **test quality issues**, not production bugs. They fall into three categories:

1. **Safety Check Violations** (25 tests) - Tests not using `mcp_harness` fixture properly
2. **Assertion Mismatches** (7 tests) - Tests expecting old CLI output format
3. **Test Data Schema Issues** (1 test) - Test data not updated to match current schema

### Work Items

#### [P0] Fix Safety Check Violations in Tests

**Status**: Not Started
**Effort**: Medium (3 hours)
**Dependencies**: None
**Test Count**: 25 tests

**Description**:

Update 25 tests that fail with "SAFETY VIOLATION: ClaudeCodePlugin instantiated in test mode without path_overrides!" to properly use the `mcp_harness` fixture.

**Root Cause**: These tests create ClaudeCodePlugin or MCPManager instances without path overrides, which triggers the safety check introduced to prevent test pollution. The safety checks are **working correctly** - the tests just need to use the proper test harness.

**Affected Test Files**:
- `tests/test_cli_integration.py` (3 tests)
- `tests/test_cli_missing_coverage.py` (5 tests)
- `tests/test_cli_scope_features.py` (2 tests)
- `tests/test_cli_targeted_coverage.py` (4 tests)
- `tests/test_functional_*.py` (7 tests)
- `tests/test_tui_reload.py` (4 tests)

**Acceptance Criteria**:
- [ ] All 25 tests use `mcp_harness` fixture properly
- [ ] All tests pass without safety violations
- [ ] No real file system access in tests
- [ ] Test coverage maintained or improved
- [ ] Changes committed with clear message

**Technical Notes**:

**Pattern to Use**:
```python
def test_something(mcp_harness):
    # harness provides path overrides and prepopulated config
    plugin = ClaudeCodePlugin(path_overrides=mcp_harness.path_overrides)

    # Or use prepopulated harness with data
    harness = mcp_harness.setup_scope_files()
    manager = MCPManager(...)
```

**Testing Verification**:
```bash
# Test each file individually
pytest tests/test_cli_integration.py -v
pytest tests/test_cli_missing_coverage.py -v
pytest tests/test_cli_scope_features.py -v
pytest tests/test_cli_targeted_coverage.py -v
pytest tests/test_functional_*.py -v
pytest tests/test_tui_reload.py -v

# Verify all pass
pytest --override-ini="addopts=" --tb=short -q
```

**Risk**: LOW - Known pattern, clear fix strategy

---

#### [P0] Update CLI Output Assertions

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: None
**Test Count**: 7 tests

**Description**:

Update 7 tests that fail due to mismatched CLI output expectations. These tests expect specific text that has changed due to Rich console formatting.

**Examples**:
- `test_status_command_no_servers` expects "No MCP servers installed"
- Actual output uses Rich console formatting with different text

**Root Cause**: CLI was improved with Rich console output, but test assertions weren't updated to match.

**Affected Tests**:
- `tests/test_cli_integration.py::test_status_command_no_servers`
- `tests/test_cli_integration.py::test_status_json_no_servers`
- `tests/test_cli_integration.py::test_info_nonexistent`
- `tests/test_cli_missing_coverage.py` (various status/info tests)
- `tests/test_cli_targeted_coverage.py` (various output tests)
- `tests/test_cli_smoke.py::test_info_nonexistent`

**Acceptance Criteria**:
- [ ] All 7 tests updated to match current CLI output
- [ ] Tests verify correct functionality, not exact string match
- [ ] Consider using regex or substring matching for flexibility
- [ ] All tests pass
- [ ] Changes committed

**Technical Notes**:

**Approach**:
1. Run each failing test to see actual vs expected output
2. Update assertions to match current Rich console format
3. Consider more flexible matching (contains, regex) instead of exact equals
4. Verify CLI behavior is correct

**Testing Verification**:
```bash
# See actual output
pytest tests/test_cli_integration.py::test_status_command_no_servers -vv

# Update assertions
# Re-run to verify
pytest tests/test_cli_integration.py -v
```

**Risk**: MINIMAL - Simple assertion updates

---

#### [P0] Fix Test Data Schema

**Status**: Not Started
**Effort**: Small (10 minutes)
**Dependencies**: None
**Test Count**: 1 test

**Description**:

Fix `tests/test_installer.py::TestBaseInstaller::test_validate_installation` which fails because test data is missing the required `command` field in MCPServer schema.

**Root Cause**: MCPServer schema was updated to require `command` field, but test data wasn't updated.

**Acceptance Criteria**:
- [ ] Test data includes required `command` field
- [ ] Test passes
- [ ] Schema validation succeeds
- [ ] Changes committed

**Technical Notes**:

**Fix**:
```python
# In test_installer.py, update test data:
test_server = MCPServer(
    name="test-server",
    description="Test server",
    command="npx",  # ADD THIS
    # ... other fields
)
```

**Testing Verification**:
```bash
pytest tests/test_installer.py::TestBaseInstaller::test_validate_installation -v
```

**Risk**: TRIVIAL - Add one field

---

#### [P1] Add Enable/Disable Documentation

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: None

**Description**:

Add comprehensive documentation to CLAUDE.md explaining the enable/disable mechanisms by scope. This feature was implemented in v2.0 but never documented.

**Source**: SHIP-CHECKLIST-v2.0-USER-INTERNAL-DISABLE-2025-11-13.md (lines 169-214)

**Acceptance Criteria**:
- [ ] New section "Enable/Disable Mechanisms by Scope" added to CLAUDE.md
- [ ] Documents ArrayBased handler (user-internal, user-mcp scopes)
- [ ] Documents FileTracked handler (user-global, user-local scopes)
- [ ] Includes examples of enable/disable commands for each scope
- [ ] Explains tracking file format (`.mcpi-disabled-servers-*.json`)
- [ ] Links to relevant test files for reference
- [ ] Section placed logically in document structure
- [ ] Markdown formatting consistent with rest of CLAUDE.md
- [ ] Changes committed to git

**Technical Notes**:

**Section Outline**:
```markdown
### Enable/Disable Mechanisms by Scope

MCPI supports enabling and disabling servers on a per-scope basis with two different mechanisms:

**ArrayBased Handler** (user-internal, user-mcp):
- Scopes where servers are defined as JSON arrays
- Enable: Server present in array
- Disable: Server removed from array
- Example: `~/.claude/settings.json` (user-internal)

**FileTracked Handler** (user-global, user-local):
- Scopes where servers are defined as JSON objects
- Enable: Remove from tracking file
- Disable: Add to tracking file
- Tracking file: `.mcpi-disabled-servers-{scope}.json`
- Example: `.claude/.mcpi-disabled-servers-global.json`

**Examples**:
[Include command examples from ship checklist]

**Implementation Details**:
[Link to relevant code and tests]
```

**Target Location**: After "Scope-Based Configuration" section in CLAUDE.md

**Risk**: MINIMAL - Documentation only

---

### Success Metrics

**Target Outcomes**:
- [ ] Test pass rate ≥ 98% (680+ tests passing)
- [ ] All safety check violations resolved
- [ ] All CLI output tests match current format
- [ ] Test data schemas up to date
- [ ] Enable/disable mechanism documented
- [ ] Zero production bugs identified
- [ ] v2.0.1 tagged and released

**Quality Gates**:
- All tests pass (except known skips)
- No new test failures introduced
- Black formatting clean
- Documentation complete

**Timeline**: 1 week from v2.0 ship date

---

## Version 2.1 - DIP Phase 2 Architecture Improvements

**Timeline**: 1 month post-ship (starting after v2.0.1)
**Effort**: 2-3 weeks total
**Goal**: Improve testability and SOLID compliance through dependency injection

### Scope

Implement Phase 2 of the DIP (Dependency Inversion Principle) audit. This refactoring improves testability by injecting dependencies rather than hardcoding them, enabling true unit tests without file system access.

**DIP Phase 2 Components** (from DIP_AUDIT-2025-11-07-010149.md):
1. ClaudeCodePlugin - Inject readers/writers/validators
2. FileBasedScope - Make reader/writer required parameters
3. ClientRegistry - Support plugin injection
4. CLI Factory Pattern - Inject manager/catalog factories
5. TUI Factory - Inject adapter factory

### Work Items

#### [P1] DIP Phase 2 - ClaudeCodePlugin Refactoring

**Status**: Not Started
**Effort**: Large (1-2 weeks)
**Dependencies**: v2.0.1 Complete
**Spec Reference**: DIP_AUDIT-2025-11-07-010149.md section 1.5

**Description**:

Refactor ClaudeCodePlugin to use dependency injection for readers, writers, and validators. This is the largest and most impactful Phase 2 item.

**Current Problem** (from DIP Audit):
```python
# WRONG - hardcoded dependencies
def _initialize_scopes(self):
    json_reader = JSONFileReader()      # Hardcoded
    json_writer = JSONFileWriter()      # Hardcoded
    validator = YAMLSchemaValidator()   # Hardcoded
```

**Target Design**:
```python
# CORRECT - injected dependencies
def __init__(
    self,
    path_overrides: Optional[Dict[str, Path]] = None,
    reader: ConfigReader,                      # Injected
    writer: ConfigWriter,                      # Injected
    validator: SchemaValidator,                # Injected
):
```

**Components to Refactor**:
1. ClaudeCodePlugin constructor
2. FileBasedScope class
3. JSONFileReader/Writer abstractions
4. YAMLSchemaValidator abstraction
5. EnableDisableHandler implementations

**Acceptance Criteria**:
- [ ] ClaudeCodePlugin constructor accepts reader/writer/validator
- [ ] FileBasedScope reader/writer are required parameters
- [ ] All protocols (ConfigReader, ConfigWriter, SchemaValidator) properly used
- [ ] Factory functions created for production and test instances
- [ ] All existing tests updated to use new constructors
- [ ] New unit tests created with mocked dependencies
- [ ] No file I/O in true unit tests
- [ ] Test coverage for plugin operations >80%
- [ ] Documentation updated to reflect new patterns
- [ ] All tests pass (no regressions)
- [ ] Black formatting passes
- [ ] Changes committed with descriptive messages

**Technical Notes**:

**Implementation Steps**:
1. Update ClaudeCodePlugin constructor to accept dependencies
2. Update FileBasedScope to require dependencies
3. Create factory functions for production use
4. Create test factories for testing use
5. Update all test files to use new patterns
6. Write new unit tests with mocks
7. Update documentation

**Files to Modify**:
- `src/mcpi/clients/claude_code.py`
- `src/mcpi/clients/file_based.py`
- `src/mcpi/clients/protocols.py` (if needed)
- `tests/test_claude_code_plugin.py`
- `tests/test_file_based_scope.py`
- `CLAUDE.md` (update DIP section)

**Estimated Effort Breakdown**:
- Design and planning: 2 days
- Implementation: 5 days
- Testing: 2 days
- Documentation: 1 day
- **Total: 10 days (2 weeks)**

**Risk**: MEDIUM - Significant refactoring, but well-documented plan exists

---

#### [P1] DIP Phase 2 - ClientRegistry Refactoring

**Status**: Not Started
**Effort**: Medium (3-5 days)
**Dependencies**: None (can be done in parallel)
**Spec Reference**: DIP_AUDIT-2025-11-07-010149.md section 1.3

**Description**:

Refactor ClientRegistry to support dependency injection for plugin discovery. Allow pre-loaded plugins for testing while maintaining auto-discovery for production.

**Current Problem**:
```python
class ClientRegistry:
    def __init__(self) -> None:
        self._plugins = {}
        self._instances = {}
        self._discover_plugins()  # Hardcoded - cannot inject plugins
```

**Target Design**:
```python
class ClientRegistry:
    def __init__(self, plugin_classes: Optional[List[Type[MCPClientPlugin]]] = None):
        self._plugins = {}
        self._instances = {}

        if plugin_classes:
            for plugin_class in plugin_classes:
                self._register_plugin_class(plugin_class)
        else:
            self._discover_plugins()
```

**Acceptance Criteria**:
- [ ] ClientRegistry accepts optional plugin_classes parameter
- [ ] Auto-discovery still works when no plugins provided
- [ ] Can inject mock plugins for testing
- [ ] PluginDiscovery protocol defined (if needed)
- [ ] Factory functions created for production and test instances
- [ ] All existing tests updated
- [ ] New unit tests with injected mock plugins
- [ ] Test coverage for registry operations >80%
- [ ] Documentation updated
- [ ] All tests pass (no regressions)
- [ ] Changes committed

**Technical Notes**:

**Implementation Approach**:
1. Add plugin_classes parameter to __init__
2. Conditional logic: inject or auto-discover
3. Create _register_plugin_class helper method
4. Create factory functions
5. Update MCPManager to use factory
6. Update tests to inject mock plugins

**Files to Modify**:
- `src/mcpi/clients/registry.py`
- `src/mcpi/clients/manager.py` (update usage)
- `tests/test_client_registry.py`
- `tests/test_mcp_manager.py`

**Benefits**:
- True unit tests without file system access
- Faster test execution
- Easier mocking in tests
- Better SOLID compliance

**Estimated Effort**: 3-5 days

**Risk**: MEDIUM - Changes core discovery mechanism

---

#### [P1] DIP Phase 2 - CLI Factory Pattern

**Status**: Not Started
**Effort**: Small (1-2 days)
**Dependencies**: P1-2 (ClientRegistry Refactored)
**Spec Reference**: DIP_AUDIT-2025-11-07-010149.md section 1.4

**Description**:

Refactor CLI helper functions to accept factory functions for creating MCPManager and ServerCatalog. This enables testing CLI commands without touching the file system.

**Current Problem**:
```python
def get_mcp_manager(ctx: click.Context) -> MCPManager:
    if "mcp_manager" not in ctx.obj:
        ctx.obj["mcp_manager"] = MCPManager()  # Hardcoded
```

**Target Design**:
```python
def get_mcp_manager(ctx: click.Context, factory=None) -> MCPManager:
    if "mcp_manager" not in ctx.obj:
        if factory is None:
            factory = create_default_manager
        ctx.obj["mcp_manager"] = factory()
```

**Acceptance Criteria**:
- [ ] get_mcp_manager accepts optional factory parameter
- [ ] get_catalog accepts optional factory parameter
- [ ] Default factories used in production
- [ ] Test factories can be injected for testing
- [ ] All CLI commands updated to use new pattern
- [ ] CLI tests updated to inject test factories
- [ ] CLI tests run without file system access
- [ ] Test coverage for CLI commands >70%
- [ ] Documentation updated
- [ ] All tests pass (no regressions)
- [ ] Changes committed

**Technical Notes**:

**Implementation Steps**:
1. Add factory parameter to get_mcp_manager
2. Add factory parameter to get_catalog
3. Update all CLI commands to accept factories via ctx.obj
4. Create CLI test fixtures with test factories
5. Update all CLI tests to use injection

**Files to Modify**:
- `src/mcpi/cli.py`
- `tests/test_cli.py`
- `tests/test_cli_scope_features.py`
- `tests/conftest.py` (add CLI test fixtures)

**Testing Pattern**:
```python
def test_list_command():
    def test_manager_factory():
        return MockMCPManager()

    def test_catalog_factory():
        return MockServerCatalog()

    result = runner.invoke(
        cli,
        ["list"],
        obj={
            "manager_factory": test_manager_factory,
            "catalog_factory": test_catalog_factory
        }
    )
```

**Estimated Effort**: 1-2 days

**Risk**: LOW - Well-documented pattern, minimal changes

---

#### [P2] DIP Phase 2 - Registry Abstraction

**Status**: Not Started
**Effort**: Medium (3-5 days)
**Dependencies**: None (can be done in parallel)
**Spec Reference**: DIP_AUDIT-2025-11-07-010149.md section 3.1

**Description**:

Create RegistryDataSource protocol and implementations to abstract catalog data source. This allows testing with in-memory data and supports future extensibility (database, remote API).

**Target Design**:
```python
class RegistryDataSource(Protocol):
    """Protocol for registry data sources."""

    def load(self) -> Dict[str, MCPServer]:
        """Load all servers from data source."""
        ...

    def save(self, servers: Dict[str, MCPServer]) -> bool:
        """Save servers to data source."""
        ...

class FileRegistryDataSource:
    """File-based registry data source."""
    def __init__(self, catalog_path: Path, validator: Optional[CUEValidator] = None):
        ...

class InMemoryRegistryDataSource:
    """In-memory registry data source for testing."""
    def __init__(self, servers: Dict[str, MCPServer]):
        ...
```

**Acceptance Criteria**:
- [ ] RegistryDataSource protocol defined
- [ ] FileRegistryDataSource implemented
- [ ] InMemoryRegistryDataSource implemented for testing
- [ ] ServerCatalog refactored to use RegistryDataSource
- [ ] Factory functions updated to create appropriate data sources
- [ ] All existing tests updated
- [ ] New unit tests with InMemoryRegistryDataSource
- [ ] Test coverage for catalog operations >80%
- [ ] Documentation updated
- [ ] All tests pass (no regressions)
- [ ] Changes committed

**Technical Notes**:

**Implementation Steps**:
1. Define RegistryDataSource protocol
2. Implement FileRegistryDataSource
3. Implement InMemoryRegistryDataSource
4. Refactor ServerCatalog to accept data source
5. Update factory functions
6. Update all tests
7. Add documentation

**Files to Create/Modify**:
- `src/mcpi/registry/data_sources.py` (new file)
- `src/mcpi/registry/catalog.py` (refactor)
- `src/mcpi/registry/protocols.py` (add protocol)
- `tests/test_registry_data_sources.py` (new file)
- `tests/test_server_catalog.py` (update)

**Benefits**:
- True unit tests without file I/O
- Supports future extensibility (database backend)
- Better separation of concerns
- Easier testing

**Estimated Effort**: 3-5 days

**Risk**: MEDIUM - Significant refactoring of catalog logic

---

#### [P3] DIP Phase 2 - TUI Factory Refactoring

**Status**: Not Started
**Effort**: Small (1 day)
**Dependencies**: None (independent)
**Spec Reference**: DIP_AUDIT-2025-11-07-010149.md section 1.7

**Description**:

Refactor TUI factory to accept adapter factory for testing. This is a low-priority item but completes the DIP implementation for Phase 2.

**Current Problem**:
```python
def get_tui_adapter(backend: Optional[str] = None) -> TUIAdapter:
    if backend == "fzf":
        return FzfAdapter()  # Hardcoded
```

**Target Design**:
```python
def get_tui_adapter(
    backend: Optional[str] = None,
    adapter_factory: Optional[Callable[[], TUIAdapter]] = None
) -> TUIAdapter:
    if adapter_factory:
        return adapter_factory()
    # ... existing logic
```

**Acceptance Criteria**:
- [ ] get_tui_adapter accepts optional adapter_factory parameter
- [ ] Default behavior unchanged (uses FzfAdapter)
- [ ] Test factory can be injected
- [ ] TUI tests updated to use injection
- [ ] TUI tests run without external dependencies
- [ ] Test coverage for TUI operations >70%
- [ ] Documentation updated
- [ ] All tests pass (no regressions)
- [ ] Changes committed

**Technical Notes**:

**Implementation Steps**:
1. Add adapter_factory parameter to get_tui_adapter
2. Create MockTUIAdapter for testing
3. Update TUI tests to inject mock adapter
4. Add documentation

**Files to Modify**:
- `src/mcpi/tui/factory.py`
- `tests/test_tui.py`
- `tests/mocks/tui.py` (new file)

**Estimated Effort**: 1 day

**Risk**: LOW - Minimal changes, independent of other work

---

### Success Metrics

**Target Outcomes**:
- [ ] DIP Phase 2 complete (5 components refactored)
- [ ] Test coverage >80% for all refactored components
- [ ] No file I/O in unit tests
- [ ] All tests passing
- [ ] Factory pattern consistent across codebase
- [ ] Documentation updated with DIP patterns
- [ ] v2.1 tagged and released

**Quality Gates**:
- All DIP Phase 2 components use dependency injection
- Unit tests run without file system access
- Test execution time improved (faster without I/O)
- All existing tests still pass
- Code coverage maintained or improved

**Timeline**: 2-3 weeks starting after v2.0.1

---

## Version 2.2+ - Future Enhancements

**Timeline**: 2+ months post-ship
**Effort**: 2-3 weeks for DIP Phases 3-4, TBD for new features
**Goal**: Complete DIP implementation and add new features as needed

### Scope

This release includes long-term improvements and new features that aren't blocking but add value.

### Work Items

#### [P2] DIP Phases 3-4 - Remaining Components

**Status**: Not Started
**Effort**: Large (2-3 weeks)
**Dependencies**: v2.1 Complete (DIP Phase 2)
**Spec Reference**: DIP_AUDIT-2025-11-07-010149.md sections 2-4

**Description**:

Complete the DIP audit by implementing dependency injection for the remaining 6 components identified in the audit. This is non-critical work that provides incremental improvements.

**Components** (from DIP Audit):
- **Phase 3 (P2)**: 4 components - 1-2 weeks
  - PluginDiscovery abstraction
  - SchemaValidator injection
  - EnableDisableHandler refactoring
  - PathResolver abstraction
- **Phase 4 (P3)**: 2 components - 1 week
  - Factory pattern consistency
  - Code organization cleanup

**Acceptance Criteria**:
- [ ] All Phase 3 components refactored with DIP
- [ ] All Phase 4 components refactored with DIP
- [ ] All protocols defined and used consistently
- [ ] All factory functions follow consistent pattern
- [ ] Test coverage >80% for all refactored components
- [ ] Documentation updated throughout
- [ ] All tests pass (no regressions)
- [ ] DIP audit marked as complete
- [ ] Changes committed with detailed messages

**Technical Notes**:

**Approach**:
1. Follow same pattern as Phase 2
2. Define protocols first
3. Implement concrete classes
4. Refactor constructors
5. Create factory functions
6. Update tests
7. Update documentation

**Reference**: DIP_AUDIT-2025-11-07-010149.md sections 2.2, 2.3, 3.2, 3.3

**Estimated Effort**: 2-3 weeks (10-15 days)

**Risk**: LOW - Non-critical, can be deferred

---

#### [P3] Planning Document Cleanup

**Status**: Not Started
**Effort**: Small (30 minutes)
**Dependencies**: None

**Description**:

Clean up the `.agent_planning` directory by archiving completed work and superseded documents. The STATUS report indicates 59 markdown files exist, which is excessive.

**Cleanup Strategy**:
1. Move completed work to `.agent_planning/completed/`
2. Move superseded documents to `.agent_planning/archive/2025-11/`
3. Keep only 4 most recent STATUS files
4. Keep only active planning documents

**Acceptance Criteria**:
- [ ] Directory `.agent_planning/completed/` organized
- [ ] Directory `.agent_planning/archive/2025-11/` organized
- [ ] Completed work moved to `completed/`
- [ ] Superseded documents moved to `archive/2025-11/`
- [ ] Only 4 most recent STATUS files remain in root
- [ ] Only active planning documents remain in root
- [ ] README.md added to each subdirectory explaining contents
- [ ] Changes committed to git

**Files to Keep**:
- `DIP_AUDIT-2025-11-07-010149.md` (ongoing work)
- 4 most recent STATUS files
- This roadmap document
- Active sprint documents

**Risk**: MINIMAL - Housekeeping only

---

#### [Future] New Features TBD

**Status**: Not Planned
**Effort**: TBD
**Dependencies**: User feedback post-v2.0

**Description**:

New features will be identified based on user feedback and usage patterns after v2.0 ships. Potential areas:

- Additional MCP client support (beyond Claude Code, Cursor, VS Code)
- Enhanced catalog search and filtering
- Server dependency management
- Configuration migration tools
- Performance optimizations
- Additional installation methods
- Enhanced TUI features

**Acceptance Criteria**: TBD based on feature proposals

---

### Success Metrics

**Target Outcomes**:
- [ ] DIP Phases 3-4 complete (6 components)
- [ ] 100% DIP compliance across codebase
- [ ] Planning documents organized and clean
- [ ] New features identified and prioritized based on user feedback
- [ ] v2.2 (or multiple point releases) tagged and released

**Quality Gates**:
- All DIP work complete
- Test coverage >80% across codebase
- Documentation comprehensive and up-to-date
- Repository well-organized

**Timeline**: Flexible - based on priorities and user needs

---

## Release Timeline

```
NOW ──────► v2.0 SHIP
           │
           │ 1 week
           ▼
           v2.0.1 (Test Quality)
           │
           │ 1 month
           ▼
           v2.1 (DIP Phase 2)
           │
           │ 2+ months
           ▼
           v2.2+ (DIP Phases 3-4 + Features)
```

### Milestones

**Week 1 (Post-Ship)**:
- v2.0 ships
- v2.0.1 development starts
- Fix 33 test failures
- Add enable/disable documentation
- v2.0.1 ships with 98%+ test pass rate

**Week 2-5 (Month 1)**:
- v2.1 development starts
- DIP Phase 2 implementation
- 5 components refactored with dependency injection
- v2.1 ships with improved testability

**Week 6+ (Month 2+)**:
- v2.2 development starts
- DIP Phases 3-4 implementation
- Planning cleanup
- New features as identified
- v2.2+ ships when ready

---

## Risk Assessment

### Overall Risk: LOW

All planned work is well-defined with clear acceptance criteria and known patterns.

### Per-Release Risk

**v2.0.1 Risk: MINIMAL**
- Known test fixes with clear patterns
- No production code changes
- Quick turnaround (1 week)

**v2.1 Risk: LOW-MEDIUM**
- Well-documented DIP patterns
- Incremental refactoring approach
- Comprehensive test suite catches regressions
- 2-3 week timeline allows for careful work

**v2.2+ Risk: LOW**
- Non-critical enhancements
- Flexible timeline
- Can be deferred if needed

### Mitigation Strategies

1. **Test Coverage**: Maintain >80% coverage throughout
2. **Incremental Changes**: Small, focused commits
3. **Continuous Testing**: Run tests after every change
4. **Documentation**: Update docs alongside code
5. **Review**: Self-review before committing
6. **Flexibility**: Adjust timeline based on progress

---

## Dependencies and Blockers

### Current Blockers: NONE

All work is unblocked and ready to proceed after v2.0 ships.

### Dependencies Between Releases

- v2.0.1 has no dependencies (can start immediately)
- v2.1 should wait for v2.0.1 to avoid merge conflicts
- v2.2+ should wait for v2.1 DIP Phase 2 completion

### External Dependencies: NONE

No external dependencies or third-party blockers identified.

---

## Success Criteria

### v2.0.1 Success
- [ ] Test pass rate ≥ 98%
- [ ] All safety check violations resolved
- [ ] Enable/disable mechanism documented
- [ ] Tagged and released

### v2.1 Success
- [ ] DIP Phase 2 complete (5 components)
- [ ] Test coverage >80% for refactored components
- [ ] Unit tests run without file I/O
- [ ] Tagged and released

### v2.2+ Success
- [ ] DIP Phases 3-4 complete
- [ ] 100% DIP compliance
- [ ] Planning documents organized
- [ ] Tagged and released

### Overall Project Success
- [ ] Users can install and use MCPI easily
- [ ] Codebase is maintainable and testable
- [ ] Documentation is comprehensive
- [ ] Test suite is reliable and fast
- [ ] Development velocity is high

---

## Conclusion

MCPI v2.0 is **ready to ship**. This roadmap provides a clear path for post-ship improvements:

1. **v2.0.1** (1 week): Quick wins - fix test quality to 98%+
2. **v2.1** (1 month): Architecture - DIP Phase 2 for better testability
3. **v2.2+** (Future): Completeness - DIP Phases 3-4 and new features

The remaining work is **valuable but not blocking**. Ship now, iterate later.

**Next Steps**:
1. Tag and release v2.0
2. Start v2.0.1 development (1 week sprint)
3. Plan v2.1 development (1 month timeline)
4. Gather user feedback for v2.2+ features

---

**Roadmap Date**: 2025-11-16 07:36:37
**Source**: STATUS-2025-11-16-184500.md + PLAN-2025-11-16-070237.md
**Planning Horizon**: 3 months
**Confidence**: HIGH - All work is well-defined and actionable
