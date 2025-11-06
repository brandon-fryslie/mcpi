# FZF TUI Implementation Fix - Backlog

**Generated**: 2025-11-05 16:26:36
**Source STATUS**: STATUS-2025-11-05-162258.md
**Spec Reference**: CLAUDE.md Project Architecture
**Current State**: 65% complete - UI works, reload mechanism broken
**Critical Blocker**: Missing `mcpi-tui-reload` command

---

## Executive Summary

The fzf interactive TUI is **partially implemented** with excellent UI/UX but a **critical missing component** that breaks the core workflow. Users can browse and view server information, but after performing operations (add/remove/enable/disable), the list does NOT refresh. The missing `mcpi-tui-reload` command prevents the real-time update mechanism from working.

**Overall Completion**: 65%
- Display & Formatting: 100% ✅
- Preview Pane: 100% ✅
- Error Handling: 100% ✅
- Keyboard Shortcuts: 50% 🔶 (bindings exist but reload broken)
- Real-time Refresh: 0% ❌ (completely non-functional)

**Effort to Ship**: 2-4 hours for minimum viable fix, 9-15 hours for production-quality

---

## Work Items

### Priority 0: Critical Blockers (MUST FIX TO SHIP)

---

## P0-1: Implement mcpi-tui-reload Command

**Status**: Not Started
**Effort**: 1-2 hours
**Dependencies**: None
**Spec Reference**: STATUS-2025-11-05-162258.md lines 192-217 • tui.py:159-165

### Description

The fzf bindings reference a `mcpi-tui-reload` command that does not exist. This command must output a fresh server list to stdout for fzf's `reload()` action to work. Without it, operations execute successfully but the UI doesn't refresh, forcing users to exit and re-launch.

**Current State**:
- `tui.py:159-165` - All operation bindings call `+reload(mcpi-tui-reload)`
- `pyproject.toml:42-43` - Only `mcpi` script defined, no `mcpi-tui-reload`
- `cli.py` - No `tui-reload` command exists
- `which mcpi-tui-reload` - Returns "not found"

**Root Cause**: The reload command was designed but never implemented.

### Acceptance Criteria

- [ ] `mcpi tui-reload` command exists in CLI
- [ ] Command outputs properly formatted server list to stdout
- [ ] Command uses ANSI colors (same as fzf launcher)
- [ ] Command works when called from fzf `execute()` context
- [ ] pyproject.toml defines `mcpi-tui-reload` console script entry point
- [ ] `which mcpi-tui-reload` returns valid path
- [ ] Manual test: launch fzf, press ctrl-a to add server, verify list refreshes
- [ ] Manual test: press ctrl-r to remove server, verify list refreshes
- [ ] Manual test: press ctrl-e/ctrl-d, verify enable/disable refreshes list

### Technical Notes

**Implementation Approach**:

```python
# Option A: Add CLI command (recommended)
# In cli.py - add new command

@main.command("tui-reload", hidden=True)
@click.pass_context
def tui_reload_command(ctx: click.Context) -> None:
    """Internal command for fzf reload (not for direct use).

    Outputs a fresh list of servers in fzf format to stdout.
    Used by fzf bindings to refresh the list after operations.
    """
    manager = get_mcp_manager(ctx)
    catalog = get_catalog(ctx)

    from mcpi.tui import build_server_list

    lines = build_server_list(catalog, manager)
    for line in lines:
        click.echo(line)
```

**pyproject.toml Change**:

```toml
[project.scripts]
mcpi = "mcpi.cli:main"
mcpi-tui-reload = "mcpi.cli:main"  # Same entry point, uses subcommand
```

**Why this works**:
- `mcpi-tui-reload` becomes an alias for `mcpi`
- fzf calls `mcpi-tui-reload` which is actually `mcpi tui-reload`
- Wait, that won't work. Need separate entry point.

**Corrected Approach**:

```python
# In tui.py - add module-level function

def reload_server_list() -> None:
    """Entry point for mcpi-tui-reload command.

    Used by fzf bindings to refresh the server list after operations.
    Outputs formatted server list to stdout.
    """
    from mcpi.cli import create_mcp_manager, create_catalog

    manager = create_mcp_manager()
    catalog = create_catalog()

    lines = build_server_list(catalog, manager)
    for line in lines:
        print(line)
```

```toml
# In pyproject.toml
[project.scripts]
mcpi = "mcpi.cli:main"
mcpi-tui-reload = "mcpi.tui:reload_server_list"
```

**Why this is better**:
- Direct entry point, no CLI parsing overhead
- Faster execution (critical for UX)
- Clear separation of concerns
- Doesn't pollute CLI help output

**Edge Cases to Handle**:
1. **No default client** - `create_mcp_manager()` might fail
   - Solution: Use same client detection as main CLI
2. **Import errors** - Missing dependencies
   - Solution: Same error handling as `launch_fzf_interface()`
3. **Empty registry** - No servers to list
   - Solution: Output empty (fzf handles gracefully)

### Testing Requirements

**Unit Tests** (`tests/test_tui_fzf.py`):
```python
def test_reload_server_list_command_exists():
    """Verify mcpi-tui-reload command is installed."""
    result = subprocess.run(
        ["which", "mcpi-tui-reload"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

def test_reload_outputs_formatted_list(monkeypatch, tmp_path):
    """Verify reload command outputs correct format."""
    # Setup: Mock manager and catalog
    # Execute: Call reload_server_list()
    # Assert: Output matches build_server_list() format

def test_reload_handles_no_servers(monkeypatch):
    """Verify reload works with empty registry."""
    # Assert: Outputs empty string or graceful message
```

**Integration Tests** (`tests/test_tui_integration.py` - NEW FILE):
```python
def test_fzf_reload_after_add(tmp_path):
    """Test that ctrl-a adds server and refreshes list."""
    # Launch fzf, simulate ctrl-a, verify server appears
    # This tests the full reload workflow

def test_fzf_reload_command_works_in_subprocess():
    """Test mcpi-tui-reload works when called as subprocess."""
    result = subprocess.run(
        ["mcpi-tui-reload"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert len(result.stdout.split("\n")) > 0
```

**Manual Testing Checklist**:
- [ ] Install with `uv tool install --editable .`
- [ ] Verify `which mcpi-tui-reload` returns path
- [ ] Run `mcpi-tui-reload` directly, verify output
- [ ] Launch `mcpi fzf`
- [ ] Select a server, press ctrl-a (add)
- [ ] Verify server list refreshes with new status
- [ ] Press ctrl-e (enable), verify green checkmark appears immediately
- [ ] Press ctrl-d (disable), verify yellow X appears immediately

---

## P0-2: Add Integration Tests for Reload Mechanism

**Status**: Not Started
**Effort**: 2-3 hours
**Dependencies**: P0-1 (reload command must exist)
**Spec Reference**: STATUS-2025-11-05-162258.md lines 297-332

### Description

The current test suite has excellent unit test coverage (91%) but **zero integration tests** for the actual fzf workflow. The missing reload command went undetected because there are no tests that verify the end-to-end operation→reload→refresh workflow.

**Testing Gap**: No tests for:
- Actual fzf subprocess interaction
- Real operations (add/remove/enable/disable) via fzf bindings
- Reload mechanism (couldn't test since it didn't exist)
- Error propagation from operations to UI
- Keyboard shortcut functionality

### Acceptance Criteria

- [ ] New file: `tests/test_tui_integration.py` created
- [ ] Test: `test_fzf_launch_basic()` - Verify fzf launches successfully
- [ ] Test: `test_fzf_reload_command_standalone()` - Verify reload works alone
- [ ] Test: `test_fzf_add_operation_triggers_reload()` - Verify ctrl-a refreshes
- [ ] Test: `test_fzf_remove_operation_triggers_reload()` - Verify ctrl-r refreshes
- [ ] Test: `test_fzf_enable_operation_updates_status()` - Verify green checkmark
- [ ] Test: `test_fzf_disable_operation_updates_status()` - Verify yellow X
- [ ] Test: `test_fzf_scope_selection_prompt()` - Verify scope prompts work
- [ ] All tests pass (100% pass rate)
- [ ] Coverage for reload workflow >= 80%

### Technical Notes

**Testing Strategy**:

Integration tests will:
1. **Mock fzf subprocess** - Use pytest monkeypatch to intercept subprocess calls
2. **Verify command structure** - Check that bindings include correct reload syntax
3. **Test reload output** - Call `mcpi-tui-reload` and verify format matches expectations
4. **Simulate operations** - Test that operations complete and trigger reload

**Example Test**:
```python
def test_fzf_add_operation_includes_reload_binding(tmp_path):
    """Verify ctrl-a binding includes reload command."""
    # Setup
    manager = create_test_manager()
    catalog = create_test_catalog()

    # Build fzf command
    from mcpi.tui import build_fzf_command
    fzf_cmd = build_fzf_command()

    # Find ctrl-a binding
    ctrl_a_bind = next(
        (arg for arg in fzf_cmd if "ctrl-a" in arg),
        None
    )

    assert ctrl_a_bind is not None
    assert "reload(mcpi-tui-reload)" in ctrl_a_bind
    assert "mcpi add" in ctrl_a_bind

def test_reload_command_matches_build_server_list_output():
    """Verify reload outputs same format as build_server_list."""
    # Call reload_server_list() and build_server_list()
    # Assert outputs are identical
```

**Mock Strategy for fzf**:
- Use `unittest.mock.patch` to intercept `subprocess.run`
- Verify fzf command structure without actually launching fzf
- Test would fail in CI without fzf installed otherwise

**Edge Cases to Cover**:
1. fzf not installed - Should raise clear error
2. No servers in registry - Should show warning
3. Scope selection in non-TTY context - Should handle gracefully
4. Multiple rapid operations - Should queue properly
5. Operation errors - Should not break fzf session

### Testing Requirements

**New Test File Structure**:
```python
# tests/test_tui_integration.py

import pytest
import subprocess
from unittest.mock import patch, MagicMock

class TestFzfReloadMechanism:
    """Integration tests for fzf reload workflow."""

    def test_reload_command_exists(self):
        """Verify mcpi-tui-reload is installed."""
        ...

    def test_reload_outputs_correct_format(self):
        """Verify reload output matches expected format."""
        ...

    def test_fzf_bindings_include_reload(self):
        """Verify all operation bindings call reload."""
        ...

class TestFzfOperations:
    """Integration tests for fzf operations."""

    def test_add_operation_structure(self):
        """Verify ctrl-a binding is correct."""
        ...

    def test_remove_operation_structure(self):
        """Verify ctrl-r binding is correct."""
        ...

    # etc.
```

**Coverage Target**: 80% for reload workflow paths

---

### Priority 1: High-Value Improvements (SHOULD FIX)

---

## P1-1: Fix Documentation - Remove False "Real-time Updates" Claim

**Status**: Not Started
**Effort**: 30 minutes
**Dependencies**: None (can do immediately)
**Spec Reference**: STATUS-2025-11-05-162258.md lines 338-393

### Description

The README claims "Real-time status updates after operations" which is currently **FALSE** because the reload mechanism is broken. This misleads users about functionality and creates negative user experience when the feature doesn't work as advertised.

**Location**: README.md line 168

**Current Text**: "Real-time status updates after operations"

**Issue**: This is a lie. Updates don't happen until P0-1 is implemented.

### Acceptance Criteria

- [ ] README.md updated to remove/qualify "real-time" claim
- [ ] Add "Known Limitations" section documenting reload requirement
- [ ] Add troubleshooting for "list doesn't refresh"
- [ ] Document fzf installation requirement prominently
- [ ] Add note that reload requires `mcpi-tui-reload` command (after P0-1 ships)
- [ ] Consider adding screenshot or animated GIF of working UI (after fixes)

### Technical Notes

**Recommended Changes**:

```markdown
<!-- README.md - BEFORE (WRONG) -->
## Interactive TUI (fzf)

Launches an fzf-based TUI that allows you to:
- Browse all available MCP servers
- View installed servers (highlighted in green/yellow)
- Add, remove, enable, disable servers with keyboard shortcuts
- View detailed server information
- Real-time status updates after operations  ← REMOVE THIS

<!-- README.md - AFTER (HONEST) -->
## Interactive TUI (fzf)

Launches an fzf-based TUI that allows you to:
- Browse all available MCP servers
- View installed servers (highlighted in green/yellow)
- Add, remove, enable, disable servers with keyboard shortcuts
- View detailed server information in preview pane
- Multi-operation workflow without exiting

**Requirements**:
- fzf must be installed (`brew install fzf` on macOS)

**Known Limitations**:
- After operations, you must exit and re-launch to see status changes
  (automatic refresh planned for v1.1)

### Troubleshooting

**Server list doesn't refresh after add/remove**
This is expected in v1.0. Exit fzf (press ESC) and run `mcpi fzf` again
to see updated status.
```

**After P0-1 ships**, update to:
```markdown
- Automatic list refresh after operations (requires mcpi-tui-reload)
```

### Testing Requirements

**Validation**:
- [ ] README.md passes markdown lint
- [ ] Claims are accurate and verifiable
- [ ] No false or aspirational claims
- [ ] Known issues documented honestly

---

## P1-2: Add Requirements Section to README

**Status**: Not Started
**Effort**: 15 minutes
**Dependencies**: None
**Spec Reference**: STATUS-2025-11-05-162258.md lines 152-170

### Description

The README doesn't clearly state that fzf is a **required dependency** for the TUI feature. Users discover this only when they get a runtime error. A clear requirements section improves UX.

### Acceptance Criteria

- [ ] Add "Requirements" section to README
- [ ] List fzf as required for TUI feature
- [ ] Provide installation commands for macOS, Linux, Windows
- [ ] Link to official fzf installation guide
- [ ] Note that core `mcpi` commands work without fzf

### Technical Notes

```markdown
## Requirements

### Core CLI
- Python 3.12+
- pip or uv package manager

### Interactive TUI (Optional)
The `mcpi fzf` command requires fzf to be installed:

**macOS**:
```bash
brew install fzf
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt install fzf

# RHEL/Fedora
sudo yum install fzf
```

**Windows**:
```powershell
# Using Chocolatey
choco install fzf

# Using Scoop
scoop install fzf
```

**Or install from source**: https://github.com/junegunn/fzf#installation

All other `mcpi` commands work without fzf.
```

---

### Priority 2: Code Quality Improvements (NICE TO HAVE)

---

## P2-1: Use Python API Instead of Subprocess for Operations

**Status**: Not Started
**Effort**: 2-3 hours
**Dependencies**: None
**Spec Reference**: STATUS-2025-11-05-162258.md lines 240-260

### Description

The current implementation uses subprocess to call `mcpi add`, `mcpi remove`, etc. This is slow (200-500ms per operation) due to CLI initialization overhead. Using the Python API directly would be 5-10x faster and more robust.

**Current Approach**:
```python
# tui.py:159
f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi add {{}})+reload(...)"
```

**Performance Impact**:
- Subprocess spawn: ~50ms
- CLI initialization: ~100ms
- Lazy loading: ~50ms
- Actual operation: ~50ms
- **Total**: 250ms per operation

**Better Approach**:
```python
# Use Python API directly
execute-silent(python -c "from mcpi import add_server; add_server('server-id')")
# Or create thin wrapper script
```

**Estimated Speed**: 25-50ms (5-10x faster)

### Acceptance Criteria

- [ ] Replace `mcpi add` calls with direct Python API
- [ ] Replace `mcpi remove` calls with direct Python API
- [ ] Replace `mcpi enable` calls with direct Python API
- [ ] Replace `mcpi disable` calls with direct Python API
- [ ] Keep `mcpi info` for preview pane (works fine, consistent)
- [ ] Benchmark: operation completion < 100ms
- [ ] All integration tests still pass
- [ ] Manual testing confirms operations work correctly

### Technical Notes

**Implementation Options**:

**Option A: Python one-liner**
```python
extract_id = "awk '{print $2}'"
python_add = "python -c 'from mcpi.cli import get_mcp_manager; m=get_mcp_manager(); m.add_server({})'"

f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} {python_add})+reload(...)"
```

**Issues**:
- Ugly, hard to read
- Quoting nightmares
- Hard to debug

**Option B: Helper script** (recommended)
```python
# Create src/mcpi/_fzf_helpers.py

def fzf_add_server(server_id: str) -> None:
    """Add server from fzf context."""
    from mcpi.cli import create_mcp_manager
    manager = create_mcp_manager()
    manager.add_server(server_id)
    # Print status for user feedback
    print(f"Added {server_id}")

# Add entry points in pyproject.toml
[project.scripts]
mcpi-fzf-add = "mcpi._fzf_helpers:fzf_add_server"
mcpi-fzf-remove = "mcpi._fzf_helpers:fzf_remove_server"
# etc.
```

**Benefits**:
- Clean, testable code
- Fast execution (no CLI parsing)
- Easy to add error handling
- Can provide user feedback

**Challenges**:
- Scope selection - how to handle interactive prompts in non-TTY?
- Error handling - how to show errors in fzf context?
- State management - need to create manager instance efficiently

### Testing Requirements

**Performance Tests**:
```python
def test_fzf_operation_performance():
    """Verify operations complete in < 100ms."""
    import time
    start = time.time()
    # Call fzf_add_server()
    elapsed = time.time() - start
    assert elapsed < 0.1  # 100ms
```

**Benchmark Results** (to document):
- Before: 250ms average
- After: < 100ms average
- Improvement: 60% faster

---

## P2-2: Reduce Code Duplication in Bindings

**Status**: Not Started
**Effort**: 1 hour
**Dependencies**: None
**Spec Reference**: STATUS-2025-11-05-162258.md lines 227-235

### Description

Lines 159-165 of tui.py repeat the same pattern 4 times for different operations. This violates DRY (Don't Repeat Yourself) and makes maintenance harder.

**Current Code**:
```python
f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi add {{}})+reload(mcpi-tui-reload)",
f"ctrl-r:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi remove {{}})+reload(mcpi-tui-reload)",
f"ctrl-e:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi enable {{}})+reload(mcpi-tui-reload)",
f"ctrl-d:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi disable {{}})+reload(mcpi-tui-reload)",
```

### Acceptance Criteria

- [ ] Create helper function `build_operation_binding(key, operation)`
- [ ] Replace 4 duplicate lines with function calls
- [ ] Maintain exact same functionality
- [ ] Code is more readable and maintainable
- [ ] Tests still pass

### Technical Notes

**Refactored Code**:
```python
def build_operation_binding(key: str, operation: str, extract_id: str) -> str:
    """Build an fzf key binding for an operation with reload.

    Args:
        key: Keyboard shortcut (e.g., "ctrl-a")
        operation: mcpi command (e.g., "add", "remove")
        extract_id: Shell command to extract server ID

    Returns:
        fzf binding string
    """
    return (
        f"{key}:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi {operation} {{}})"
        f"+reload(mcpi-tui-reload)"
    )

# Then in build_fzf_command():
extract_id = "awk '{print $2}'"

bindings = [
    build_operation_binding("ctrl-a", "add", extract_id),
    build_operation_binding("ctrl-r", "remove", extract_id),
    build_operation_binding("ctrl-e", "enable", extract_id),
    build_operation_binding("ctrl-d", "disable", extract_id),
]

# Add to fzf_cmd with --bind flags
for binding in bindings:
    fzf_cmd.extend(["--bind", binding])
```

**Benefits**:
- Single source of truth for binding structure
- Easy to add new operations
- Easy to change reload mechanism
- More testable

---

## P2-3: Improve Server ID Extraction Robustness

**Status**: Not Started
**Effort**: 1-2 hours
**Dependencies**: None
**Spec Reference**: STATUS-2025-11-05-162258.md lines 219-226

### Description

The current ID extraction uses `awk '{print $2}'` which assumes the format `[X] server-id - description` never changes. If formatting changes (e.g., longer status indicators, different bracket style), all operations silently break.

**Risk**: Format changes → extraction breaks → operations fail silently

### Acceptance Criteria

- [ ] Replace fragile awk parsing with structured data approach
- [ ] Use delimiter or JSON encoding for reliable parsing
- [ ] Add format validation in tests
- [ ] Document expected format in code comments
- [ ] Consider fzf's field indexing features (`{2}` instead of awk)

### Technical Notes

**Option A: Use fzf field syntax** (simplest)
```python
# fzf can extract fields directly with {n} syntax
# No need for awk at all!

# Format: "[X] server-id - description"
# Field 1: [X]
# Field 2: server-id
# Field 3: -
# Field 4+: description

# In bindings, use {2} to get server-id directly:
f"ctrl-a:execute(mcpi add {{2}})+reload(...)"
```

**Benefits**:
- No subprocess (awk) needed
- Faster execution
- More reliable
- Simpler code

**Option B: Use delimiter**
```python
# Format: "[X] server-id|description"
# Use | as delimiter, extract with cut

extract_id = "cut -d'|' -f1 | awk '{print $2}'"
```

**Option C: JSON encoding** (most robust, complex)
```python
# Format: {"id": "server-id", "status": "✓", "desc": "..."}
# Parse with jq

extract_id = "jq -r '.id'"
```

**Recommendation**: Option A (fzf field syntax) - simplest and fastest

---

## P2-4: Add Error Handling for Reload Failures

**Status**: Not Started
**Effort**: 1 hour
**Dependencies**: P0-1 (reload command must exist)
**Spec Reference**: STATUS-2025-11-05-162258.md lines 189-217

### Description

If `mcpi-tui-reload` fails (e.g., client not detected, registry error), fzf will show an empty list or cryptic error. Add graceful error handling with user-friendly messages.

### Acceptance Criteria

- [ ] reload_server_list() catches all exceptions
- [ ] On error, output clear error message to stderr
- [ ] On error, output current list to stdout (best effort)
- [ ] Log errors for debugging
- [ ] Test error scenarios (no client, empty registry, permission errors)

### Technical Notes

```python
def reload_server_list() -> None:
    """Entry point for mcpi-tui-reload command."""
    try:
        manager = create_mcp_manager()
        catalog = create_catalog()
        lines = build_server_list(catalog, manager)

        for line in lines:
            print(line)

    except Exception as e:
        # Log error for debugging
        import sys
        print(f"ERROR: Failed to reload server list: {e}", file=sys.stderr)

        # Output empty list (fzf will show "no matches")
        # This is better than crashing fzf
        sys.exit(0)  # Exit cleanly
```

---

### Priority 3: Future Enhancements (DEFER TO v1.1)

---

## P3-1: Add Progress Indicators for Long-Running Operations

**Status**: Deferred
**Effort**: 2-3 hours
**Dependencies**: P0-1
**Spec Reference**: STATUS-2025-11-05-162258.md lines 281-287

### Description

Some operations (e.g., `npm install` for servers) can take 5+ seconds. During this time, fzf appears frozen with no feedback. Add progress indicators or notifications.

**Defer Reason**: Low priority - most operations are fast (< 1s)

---

## P3-2: Handle Concurrent Operations

**Status**: Deferred
**Effort**: 3-4 hours
**Dependencies**: P0-1
**Spec Reference**: STATUS-2025-11-05-162258.md lines 275-279

### Description

If a user rapidly presses ctrl-a multiple times, multiple `mcpi add` processes run concurrently, potentially causing file conflicts. Add operation queuing or locking.

**Defer Reason**: Edge case - unlikely to occur in practice

---

## P3-3: Use pyfzf Library for Better Integration

**Status**: Deferred
**Effort**: 4-6 hours
**Dependencies**: None
**Spec Reference**: STATUS-2025-11-05-162258.md lines 479

### Description

Instead of subprocess + shell commands, use a Python fzf library for tighter integration. This would allow:
- In-process operation execution (faster)
- Better error handling
- Richer UI (custom rendering)
- No shell quoting issues

**Defer Reason**: Current approach works fine, this is optimization

---

## Timeline and Effort Summary

### Quick Fix to Ship v1.0 (Minimum Viable)

**Total Effort**: 2-4 hours
**Confidence**: High (80%)

**Work Items**:
1. P0-1: Implement reload command (1-2 hours)
2. P0-2: Add integration tests (1 hour minimum coverage)
3. P1-1: Fix documentation (30 min)
4. Manual testing (30 min)

**Deliverable**: Functional fzf TUI with real-time refresh

---

### Full Fix to Production Quality (Recommended)

**Total Effort**: 9-15 hours
**Confidence**: Medium (60%)

**Work Items**:
1. P0-1: Implement reload command (1-2 hours)
2. P0-2: Add integration tests (2-3 hours)
3. P1-1: Fix documentation (30 min)
4. P1-2: Add requirements section (15 min)
5. P2-1: Use Python API for operations (2-3 hours)
6. P2-2: Reduce code duplication (1 hour)
7. P2-3: Improve ID extraction (1-2 hours)
8. P2-4: Add error handling (1 hour)
9. Manual testing and QA (1 hour)

**Deliverable**: Production-quality fzf TUI with excellent UX

---

## Testing Strategy

### Unit Tests
- **Current**: 18 tests, 91% coverage, 100% pass ✅
- **Needed**: Add 3 tests for reload command
- **Target**: 95% coverage

### Integration Tests
- **Current**: 0 tests ❌
- **Needed**: Create `test_tui_integration.py` with 5-7 tests
- **Target**: Cover reload workflow, operations, error cases

### Manual Testing
- **Current**: No evidence (reload bug went undetected) ❌
- **Needed**: Checklist for all operations + reload
- **Checklist**:
  - [ ] fzf launches
  - [ ] Preview pane shows info
  - [ ] ctrl-a adds server and refreshes list
  - [ ] ctrl-r removes server and refreshes list
  - [ ] ctrl-e enables server (green checkmark appears)
  - [ ] ctrl-d disables server (yellow X appears)
  - [ ] ctrl-i shows info in less
  - [ ] enter shows info in less
  - [ ] esc exits cleanly

---

## Risk Assessment

### High Risk Items

**Risk**: Reload command fails in non-TTY context
**Likelihood**: Medium (30%)
**Impact**: High (breaks TUI)
**Mitigation**: Test in CI environment, add fallback

**Risk**: Scope selection prompts break in fzf execute context
**Likelihood**: High (60%)
**Impact**: Medium (operations fail)
**Mitigation**: Pre-select scope or use default, test thoroughly

### Medium Risk Items

**Risk**: Performance regression from Python API
**Likelihood**: Low (20%)
**Impact**: Medium (slower UX)
**Mitigation**: Benchmark before/after, optimize if needed

### Low Risk Items

**Risk**: Breaking existing unit tests
**Likelihood**: Low (10%)
**Impact**: Low (easy to fix)
**Mitigation**: Run tests frequently

---

## Dependencies and Blockers

### External Dependencies
- fzf must be installed (documented in README)
- No new Python dependencies needed

### Internal Blockers
- None - all P0 items are independent
- P0-2 requires P0-1 to complete

### Critical Path
1. P0-1 (reload command) - BLOCKS everything else
2. P0-2 (integration tests) - BLOCKS confident ship
3. P1-1 (docs) - BLOCKS honest README

Parallel work possible on P2 items while P0 is in progress.

---

## Success Criteria for Shipping

### Must Have (Blocking)
- [ ] P0-1: Reload command implemented and working
- [ ] P0-2: Basic integration tests pass
- [ ] P1-1: Documentation accurate (no false claims)
- [ ] Manual test checklist 100% complete
- [ ] No regressions in existing unit tests

### Should Have (Strongly Recommended)
- [ ] P1-2: Requirements documented
- [ ] P2-1: Python API for faster operations
- [ ] P2-2: Code duplication removed
- [ ] Integration tests cover all operations

### Nice to Have (Defer to v1.1)
- [ ] P2-3: Robust ID extraction
- [ ] P2-4: Error handling for reload
- [ ] P3 items (progress, concurrency, pyfzf)

---

## Commit Strategy

### Commits for P0-1
1. `feat(tui): add mcpi-tui-reload command for fzf integration`
2. `test(tui): add tests for reload command`
3. `build: add mcpi-tui-reload to console scripts`

### Commits for P0-2
1. `test(tui): add integration tests for fzf reload workflow`

### Commits for Documentation
1. `docs(readme): remove false real-time updates claim`
2. `docs(readme): add fzf requirements section`

### Commits for P2 Improvements
1. `refactor(tui): use Python API for operations (5-10x faster)`
2. `refactor(tui): reduce code duplication in bindings`
3. `fix(tui): improve server ID extraction robustness`
4. `fix(tui): add error handling for reload failures`

---

## Appendix: File Inventory

### Files to Create
- `tests/test_tui_integration.py` - Integration tests (P0-2)
- `src/mcpi/_fzf_helpers.py` - Optional helper for P2-1

### Files to Modify
- `src/mcpi/tui.py` - Add reload function (P0-1), refactoring (P2)
- `pyproject.toml` - Add console script entry point (P0-1)
- `README.md` - Fix docs (P1-1), add requirements (P1-2)
- `tests/test_tui_fzf.py` - Add reload tests (P0-1)

### Files That Are New and Untracked
Based on git status, these files need to be committed:
- `src/mcpi/tui.py` - New file
- `tests/test_tui_fzf.py` - New file

**Action Required**: After implementing P0-1, commit these files:
```bash
git add src/mcpi/tui.py tests/test_tui_fzf.py
git commit -m "feat(tui): add fzf interactive interface with reload support"
```

---

## Conclusion

The fzf TUI implementation is **65% complete** with excellent foundation but a critical missing piece. The reload mechanism is the only blocker to shipping a functional feature.

**Recommended Path**:
1. **Sprint 1 (2-4 hours)**: P0-1 + P0-2 + P1-1 → Ship v1.0 with working TUI
2. **Sprint 2 (5-11 hours)**: P2 items → Polish to production quality
3. **Sprint 3 (future)**: P3 items → Advanced features for v1.1

**Immediate Next Action**: Start P0-1 (implement reload command)

---

**For detailed planning and progress tracking, see:**
- This backlog for work items
- `STATUS-2025-11-05-162258.md` for current state assessment
- `tests/test_tui_fzf.py` for existing test coverage
- `src/mcpi/tui.py` for implementation
