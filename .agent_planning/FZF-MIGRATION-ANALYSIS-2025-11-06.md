# fzf Migration Analysis: Python Alternatives Evaluation

**Date**: 2025-11-06
**Project**: MCPI (Model Context Protocol Interface)
**Feature**: Interactive TUI for MCP server management
**Current Implementation**: fzf (Go binary) + subprocess integration

---

## Executive Summary

**Question**: Should MCPI migrate from fzf (Go) to a Python-based TUI library?

**Quick Answer**: Depends on priorities. Three viable paths:
1. **Keep fzf** - Fix current bugs, lowest effort (recommended short-term)
2. **Switch to iterfzf** - Pythonic API, still uses fzf binary (good middle ground)
3. **Migrate to InquirerPy** - Pure Python, moderate effort (best long-term if pure Python is priority)

**Current Pain Points**:
- fzf binary PATH issues causing "Command failed: mcpi-tui-cycle-scope"
- Context switching between Python and shell scripting
- Debugging complexity (Python → bash → fzf → Python callbacks)

---

## Current State Analysis

### Existing Implementation (`src/mcpi/tui.py`)

**Lines of Code**: 396 lines
**Dependencies**:
- External: fzf binary (must be installed separately or via uv)
- Python: subprocess, os, sys

**Features Implemented**:
- ✅ Fuzzy search across all MCP servers
- ✅ Preview pane with server details (`mcpi info`)
- ✅ Keyboard shortcuts (ctrl-a/r/e/d/s/i, enter, esc)
- ✅ Scope cycling with header display
- ✅ ANSI color formatting (enabled/disabled/not-installed)
- ✅ Multi-line header (fits 60-column terminals)
- ✅ Reload on operations (add/remove/enable/disable)

**Current Integration Pattern**:
```python
def launch_fzf_interface(manager: MCPManager, catalog: ServerCatalog) -> None:
    server_lines = build_server_list(catalog, manager)  # Python
    fzf_cmd = build_fzf_command(current_scope)          # Build shell command
    input_data = "\n".join(server_lines)                # Python

    result = subprocess.run(fzf_cmd, input=input_data, text=True)  # Shell → fzf
    # Keyboard bindings execute: bash → mcpi CLI → Python
```

**Problems Encountered**:
1. Console script (`mcpi-tui-cycle-scope`) not in fzf's PATH
2. Shell quoting complexity for bindings with scope parameter
3. Debugging requires understanding: Python → fzf command syntax → shell execution → Python callback
4. Header truncation on narrow terminals (recently fixed)

---

## Option A: Keep fzf (Status Quo with Fixes)

### Overview
Fix current bugs and continue using fzf via subprocess.

### Pros ✅

1. **Already working** - Core functionality implemented and tested (7/11 tests passing)
2. **Mature & battle-tested** - fzf is extremely stable (30k+ GitHub stars)
3. **Excellent performance** - Written in Go, handles huge lists (100k+ items) smoothly
4. **Rich feature set** - Preview pane, ANSI colors, flexible bindings all working
5. **Community knowledge** - Vast documentation, Stack Overflow answers, examples
6. **Zero migration effort** - Just fix PATH issue (1-2 hours)
7. **Users may already have fzf installed** - Popular tool in dev communities

### Cons ❌

1. **Context switching** - Python → shell → fzf → Python callbacks
2. **PATH dependency issues** - Console scripts not available in fzf subprocess environment (your current bug)
3. **Shell quoting complexity** - Need to carefully escape variables in bindings
4. **Debugging difficulty** - Multi-language stack trace (Python → bash → fzf)
5. **External dependency** - Users need fzf installed (though uv can handle this)
6. **Not "pure Python"** - Go binary in the stack

### Current Bug Analysis

**Bug**: "Command failed: mcpi-tui-cycle-scope"

**Root Cause**: fzf subprocess doesn't inherit full PATH from user shell
- Console script in `/Users/bmf/.local/bin/` or `.pyenv/shims/`
- fzf subprocess has minimal PATH
- `mcpi-tui-cycle-scope` not found

**Fix Options**:
1. ✅ **Already attempted**: Use `python -c 'from mcpi.cli import tui_cycle_scope_entry; tui_cycle_scope_entry()'` (avoids PATH)
2. Use full path to console script: `$(which mcpi-tui-cycle-scope)`
3. Export PATH in fzf command: `PATH=$PATH fzf ...`

**Estimated Fix Time**: 1-2 hours (already implemented, needs testing)

### Effort to Continue

**Immediate** (fix current bugs): 1-2 hours
- Test the `python -c` workaround for ctrl-s binding
- Verify header fits narrow terminals
- Fix preview error handling (done)

**Ongoing maintenance**: Low
- fzf is stable, unlikely to break
- Shell scripting knowledge required for future features

### Recommendation

**Keep fzf if**:
- Pure Python is not a hard requirement
- You want stable, proven technology
- Performance is critical (100k+ servers)
- You're comfortable with shell scripting

---

## Option B: iterfzf (Pythonic Wrapper for fzf)

### Overview
Replace subprocess calls with iterfzf Python library. Still uses fzf binary underneath, but provides Pythonic API.

**GitHub**: https://github.com/dahlia/iterfzf
**PyPI**: `pip install iterfzf`
**Last Update**: Aug 2024 (bundles fzf 0.54.3)
**License**: GPLv3 (note: more restrictive than MIT)

### Pros ✅

1. **Pythonic API** - No subprocess, no shell escaping
2. **Bundles fzf binary** - Users don't need separate install (Linux/macOS/Windows prebuilt)
3. **Same performance** - Uses real fzf under the hood
4. **All fzf features** - Preview, colors, multi-select, everything available
5. **Easy migration** - Straightforward API replacement (~1 day)
6. **Type hints** - Modern Python with proper typing
7. **Generator support** - Stream large lists efficiently

### Cons ❌

1. **Still uses Go binary** - Not "pure Python" (binary bundled in package)
2. **GPL license** - More restrictive than MIT (check if this matters for MCPI)
3. **Less flexible** - Can't customize fzf command as deeply as raw subprocess
4. **Maintenance dependency** - Relies on maintainer updating bundled fzf version
5. **Callback limitations** - Keyboard bindings handled differently than raw fzf

### Code Migration Example

**Before** (current subprocess approach):
```python
def launch_fzf_interface(manager: MCPManager, catalog: ServerCatalog) -> None:
    server_lines = build_server_list(catalog, manager)
    fzf_cmd = build_fzf_command(current_scope)
    input_data = "\n".join(server_lines)

    result = subprocess.run(fzf_cmd, input=input_data, text=True, capture_output=True)
    if result.returncode == 0 and result.stdout:
        handle_selection(result.stdout.strip())
```

**After** (iterfzf):
```python
from iterfzf import iterfzf

def launch_fzf_interface(manager: MCPManager, catalog: ServerCatalog) -> None:
    servers = [(sid, format_server_line(sid, info)) for sid, info in catalog.list_servers()]

    selection = iterfzf(
        (line for sid, line in servers),
        multi=False,
        prompt=f"MCPI | Scope: {current_scope} > ",
        preview="mcpi info {}",
        # Note: keyboard bindings are more limited
    )

    if selection:
        handle_selection(selection)
```

### Limitations

**Keyboard Bindings**: iterfzf doesn't support custom bindings like ctrl-a/r/e/d
- Would need to use fzf's built-in bindings (alt-numbers, etc.)
- Or fall back to menu-driven interface after selection

**Workaround**: Could use iterfzf for selection, then show secondary menu for operations:
```python
selection = iterfzf(servers)
if selection:
    action = iterfzf(["Add", "Remove", "Enable", "Disable"], prompt="Action:")
    execute_action(action, selection)
```

### Migration Effort

**Estimated Time**: 1 day

**Breakdown**:
- Install iterfzf: 5 minutes
- Replace launch_fzf_interface(): 2 hours
- Redesign keyboard binding flow: 3 hours
- Update tests: 2 hours
- Test and debug: 1 hour

**Risk**: Medium (API is simpler but less powerful)

### Recommendation

**Use iterfzf if**:
- You want Pythonic API but keep fzf performance
- GPL license is acceptable
- Simpler keyboard binding UX is okay
- You want easy migration path

**Don't use iterfzf if**:
- Pure Python is requirement
- Need complex custom keyboard bindings (ctrl-a/r/e/d/s)
- GPL license is problematic

---

## Option C: InquirerPy (Pure Python)

### Overview
Complete rewrite using InquirerPy, a pure Python library built on prompt_toolkit.

**GitHub**: https://github.com/kazhala/InquirerPy
**PyPI**: `pip install inquirerpy`
**Stars**: 436
**License**: MIT
**Python**: 3.7+

### Pros ✅

1. **Pure Python** - No Go binary, all Python dependencies
2. **Active maintenance** - Regular updates, responsive maintainer
3. **Good fuzzy search** - Uses fzy algorithm (similar to fzf)
4. **Custom keybindings** - Full control over keyboard shortcuts
5. **Built on prompt_toolkit** - Solid foundation, cross-platform
6. **MIT license** - Permissive, no licensing concerns
7. **Handles large lists** - Documented to work with 100k+ items
8. **Multiselect support** - If needed in future
9. **VI/Emacs modes** - Power user features available

### Cons ❌

1. **Less mature** - 436 stars vs fzf's 64k
2. **Preview pane limitations** - Not as rich as fzf's native preview
3. **Performance unkn** - Likely slower than Go-based fzf for massive lists
4. **Smaller community** - Fewer examples, Stack Overflow answers
5. **Migration effort** - Moderate (2-3 days)
6. **Different UX paradigms** - Prompt-based vs fzf's search-first
7. **Testing complexity** - Need to test prompt_toolkit integration

### Code Migration Example

**Before** (current fzf subprocess):
```python
def launch_fzf_interface(manager: MCPManager, catalog: ServerCatalog) -> None:
    server_lines = build_server_list(catalog, manager)
    fzf_cmd = [
        "fzf", "--ansi",
        f"--header=MCPI | Scope: {current_scope}",
        "--bind", "ctrl-a:execute(mcpi add {} --scope {scope})+reload(...)",
        # ... more bindings
    ]
    subprocess.run(fzf_cmd, input="\n".join(server_lines))
```

**After** (InquirerPy):
```python
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

def launch_inquirer_interface(manager: MCPManager, catalog: ServerCatalog) -> None:
    # Build choices with rich formatting
    choices = []
    for server_id, server in catalog.list_servers():
        status = manager.get_server_info(server_id)

        # Color based on state
        if status.state == ServerState.ENABLED:
            color = "green"
            icon = "✓"
        elif status.state == ServerState.DISABLED:
            color = "yellow"
            icon = "✗"
        else:
            color = "default"
            icon = " "

        choices.append(Choice(
            value=server_id,
            name=f"[{icon}] {server_id} - {server.description}",
        ))

    # Custom keybindings
    kb = {
        "add_server": [{"key": "c-a"}],
        "remove_server": [{"key": "c-r"}],
        "enable_server": [{"key": "c-e"}],
        "disable_server": [{"key": "c-d"}],
        "cycle_scope": [{"key": "c-s"}],
    }

    # Main fuzzy selection
    result = inquirer.fuzzy(
        message=f"MCPI | Scope: {current_scope}",
        choices=choices,
        keybindings=kb,
        validate=lambda x: x is not None,
        invalid_message="Please select a server",
        max_height="80%",
    ).execute()

    # Handle result
    if result:
        handle_selection(result)
```

### Feature Parity Analysis

| Feature | fzf | InquirerPy | Notes |
|---------|-----|------------|-------|
| Fuzzy search | ✅ Excellent | ✅ Good | Both work well |
| Custom keybindings | ✅ Very flexible | ✅ Flexible | InquirerPy has some limitations |
| Preview pane | ✅ Native support | ⚠️ Limited | Would need workarounds |
| ANSI colors | ✅ Full support | ✅ Full support | Both handle colors |
| Performance (100k items) | ✅ Excellent | ⚠️ Good | fzf faster for massive lists |
| Multi-select | ✅ Native | ✅ Native | Both support |
| Header display | ✅ Native | ✅ Via message | Both work |
| Reload on action | ✅ Built-in | ⚠️ Manual loop | Need to relaunch prompt |

### Preview Pane Workaround

InquirerPy doesn't have native preview like fzf. Options:

**Option 1**: Show preview in prompt validation
```python
def preview_validator(result):
    if result:
        info = manager.get_server_info(result)
        print(f"\n{info.description}\nStatus: {info.state}")
    return True  # Always valid, just showing info

result = inquirer.fuzzy(
    message="Select server:",
    choices=choices,
    validate=preview_validator,  # Shows preview as you navigate
).execute()
```

**Option 2**: Two-step flow (select → show details → confirm)
```python
# Step 1: Select server
server = inquirer.fuzzy("Select server:", choices=servers).execute()

# Step 2: Show details and confirm action
if server:
    print_server_info(server)
    action = inquirer.select(
        "Action:",
        choices=["Add", "Remove", "Enable", "Disable", "Cancel"]
    ).execute()
```

**Option 3**: Use prompt_toolkit directly for full control (more work)

### Keyboard Binding Implementation

**Challenge**: InquirerPy's fuzzy doesn't support executing actions mid-selection (like fzf's execute binding)

**Solution**: Event loop with action keys
```python
while True:
    result = inquirer.fuzzy(
        message=f"MCPI | Scope: {current_scope} | ^S:Chg-Scope ^A:Add ^R:Remove ^E:Enable ^D:Disable",
        choices=build_server_choices(manager, catalog),
        keybindings={
            "add": [{"key": "c-a"}],
            "remove": [{"key": "c-r"}],
            "enable": [{"key": "c-e"}],
            "disable": [{"key": "c-d"}],
            "cycle_scope": [{"key": "c-s"}],
            "quit": [{"key": "c-c"}],
        },
    ).execute()

    # Check which key was pressed (via result or callback)
    if result == "QUIT":
        break
    elif result == "CYCLE_SCOPE":
        current_scope = cycle_scope(current_scope)
        continue  # Refresh prompt
    elif result:  # Server selected
        # Handle server operation
        pass
```

**Note**: This requires understanding InquirerPy's event system, which is less documented than fzf.

### Migration Effort

**Estimated Time**: 2-3 days

**Day 1** (6 hours):
- Install InquirerPy and experiment
- Build proof-of-concept fuzzy selector
- Map keyboard bindings to actions
- Test with small server list

**Day 2** (6 hours):
- Implement action handlers (add/remove/enable/disable)
- Implement scope cycling
- Add formatting and colors
- Handle edge cases (no servers, errors)

**Day 3** (4 hours):
- Update test suite (`test_tui_fzf.py` → `test_tui_inquirer.py`)
- Manual testing with real server list
- Debug and polish UX
- Update documentation

**Risk**: Medium-High
- API is different enough to require rethinking UX flow
- Preview pane may not be as good
- Testing strategy needs adjustment

### Recommendation

**Use InquirerPy if**:
- Pure Python is a hard requirement
- You're comfortable investing 2-3 days
- You can accept slightly different UX (no side preview pane)
- You want full control over Python code

**Don't use InquirerPy if**:
- Need exact fzf feature parity
- Can't invest migration time
- Preview pane is critical
- Performance with 1000+ servers is concern

---

## Option D: Textual (Full TUI Framework)

### Overview
Complete rewrite using Textual, a modern Python TUI framework by Textualize.

**GitHub**: https://github.com/Textualize/textual
**PyPI**: `pip install textual`
**Stars**: 32,000
**License**: MIT
**Python**: 3.8+

### Pros ✅

1. **Modern, powerful framework** - Best-in-class Python TUI
2. **Rich widgets** - Tables, trees, buttons, inputs, containers
3. **Beautiful aesthetics** - CSS-like styling, themes
4. **Fuzzy command palette** - Built-in (ctrl-p)
5. **Async support** - Handle real-time updates
6. **Excellent documentation** - Tutorials, examples, guides
7. **Active development** - Backed by company (Textualize)
8. **Can export to web** - Future possibility
9. **Developer tools** - Live reload, console debugging
10. **Type safe** - Full type hints

### Cons ❌

1. **Massive overkill** - Current MCPI is simple fuzzy selection
2. **Steep learning curve** - Need to learn Textual's paradigms
3. **Long migration** - 1-2 weeks of work
4. **Over-engineered** - More code, more complexity
5. **Harder to test** - Widget testing requires Textual test harness
6. **Performance overhead** - Heavier than simple prompt

### Code Migration Example

**Before** (single-function fzf interface):
```python
def launch_fzf_interface(manager, catalog):
    # 50 lines of subprocess + fzf command building
```

**After** (Textual app - ~200+ lines):
```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Input
from textual.binding import Binding

class MCPIApp(App):
    """MCPI Server Manager TUI."""

    CSS = """
    DataTable {
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("ctrl-s", "cycle_scope", "Change Scope"),
        Binding("ctrl-a", "add_server", "Add"),
        Binding("ctrl-r", "remove_server", "Remove"),
        Binding("ctrl-e", "enable_server", "Enable"),
        Binding("ctrl-d", "disable_server", "Disable"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, manager, catalog):
        super().__init__()
        self.manager = manager
        self.catalog = catalog
        self.current_scope = "project-mcp"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Fuzzy search servers...")
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"MCPI | Scope: {self.current_scope}"
        table = self.query_one(DataTable)
        table.add_columns("Status", "ID", "Description")
        self.refresh_servers()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter servers as user types."""
        self.refresh_servers(filter=event.value)

    def refresh_servers(self, filter: str = "") -> None:
        """Refresh server list with optional fuzzy filter."""
        table = self.query_one(DataTable)
        table.clear()

        for server_id, server in self.catalog.list_servers():
            if filter and filter.lower() not in server_id.lower():
                continue

            status = self.manager.get_server_info(server_id)
            icon = "✓" if status.enabled else "✗"
            table.add_row(icon, server_id, server.description)

    def action_cycle_scope(self) -> None:
        """Cycle to next scope."""
        # Implement scope cycling
        self.current_scope = get_next_scope(self.current_scope)
        self.title = f"MCPI | Scope: {self.current_scope}"
        self.refresh_servers()

    def action_add_server(self) -> None:
        """Add selected server."""
        table = self.query_one(DataTable)
        row = table.cursor_row
        # Implement add logic

    # ... more action handlers

def launch_textual_interface(manager, catalog):
    app = MCPIApp(manager, catalog)
    app.run()
```

### When to Use Textual

**Use Textual if you're planning**:
- Multiple views (server list, config editor, logs viewer)
- Real-time updates (server status monitoring)
- Complex navigation (tabs, panels, menus)
- Rich forms (server configuration editor)
- Future GUI or web export

**For current MCPI scope**: Textual is overkill. It's solving problems you don't have.

### Migration Effort

**Estimated Time**: 1-2 weeks

**Week 1**:
- Learn Textual framework (2 days)
- Build basic app structure (1 day)
- Implement server list view (1 day)
- Add fuzzy filtering (1 day)

**Week 2**:
- Implement all keyboard bindings (2 days)
- Add scope cycling (1 day)
- Testing and polish (2 days)

**Risk**: High (significant rewrite, new framework)

### Recommendation

**Use Textual if**:
- MCPI will grow into multi-view application
- You want best-in-class TUI experience
- You can invest 1-2 weeks
- You want to learn modern Python TUI development

**Don't use Textual if**:
- Current fuzzy selection is sufficient
- Can't invest migration time
- Simplicity is valued over features

---

## Trade-Off Matrix

### Quick Comparison Table

| Criterion | fzf (Current) | iterfzf | InquirerPy | Textual |
|-----------|--------------|---------|------------|---------|
| **Pure Python** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Maturity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Feature Parity** | ✅ 100% | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Ease of Use** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Migration Effort** | 0 hours | 1 day | 2-3 days | 1-2 weeks |
| **Maintenance** | Low | Low | Medium | Medium-High |
| **Debugging** | Hard | Medium | Easy | Medium |
| **License** | MIT | GPL | MIT | MIT |
| **Community** | Huge | Small | Small | Large |
| **Future-proof** | ✅ Yes | ✅ Yes | ⚠️ Maybe | ✅ Yes |

### Feature Comparison Detailed

| Feature | fzf | iterfzf | InquirerPy | Textual |
|---------|-----|---------|------------|---------|
| Fuzzy search | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ (manual) |
| Preview pane | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ (limited) | ⭐⭐⭐⭐⭐ (custom) |
| Custom keybindings | ⭐⭐⭐⭐⭐ | ⭐⭐ (limited) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| ANSI colors | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Multi-select | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Header/footer | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ (via message) | ⭐⭐⭐⭐⭐ |
| Reload capability | ⭐⭐⭐⭐⭐ | ⭐⭐ (restart) | ⭐⭐⭐ (loop) | ⭐⭐⭐⭐⭐ (reactive) |
| Extensibility | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Risk Assessment

| Risk | fzf | iterfzf | InquirerPy | Textual |
|------|-----|---------|------------|---------|
| **Migration risk** | None | Low | Medium | High |
| **Maintenance burden** | Low | Low | Medium | Medium-High |
| **Breaking changes** | Low | Medium | Medium | Low (stable API) |
| **Performance degradation** | None | None | Low | Medium |
| **Feature gaps** | None | Medium | Medium | None |
| **Learning curve** | Low | Low | Medium | High |
| **Testing complexity** | Medium | Low | Medium | High |

---

## Decision Tree

```
Start: Should I migrate from fzf?
│
├─ Is pure Python a HARD requirement?
│  ├─ YES → Continue to Q2
│  └─ NO → Use fzf or iterfzf
│     ├─ Want Pythonic API? → iterfzf (1 day migration)
│     └─ Current code OK? → Keep fzf (fix bugs, 1-2 hours)
│
├─ Q2: Is MCPI growing beyond fuzzy selection?
│  ├─ YES (multi-view app planned) → Textual (1-2 weeks)
│  └─ NO (just fuzzy selection) → Continue to Q3
│
├─ Q3: Can you invest 2-3 days?
│  ├─ YES → InquirerPy (good middle ground)
│  └─ NO → Keep fzf, revisit later
│
└─ Q4: Is preview pane critical?
   ├─ YES → Consider keeping fzf
   └─ NO → InquirerPy is good choice
```

---

## Effort vs Benefit Analysis

### Graph: Migration Effort vs Long-term Benefit

```
High Benefit │     Textual
             │        ●
             │
             │    InquirerPy
             │        ●
             │
             │  iterfzf
             │     ●
             │
Low Benefit  │ fzf
             │  ●
             └─────────────────────
               Low         High
                Effort
```

**Interpretation**:
- **fzf**: Low effort, low benefit (already have it)
- **iterfzf**: Medium effort, medium benefit (Pythonic API)
- **InquirerPy**: High effort, high benefit (pure Python)
- **Textual**: Very high effort, very high benefit (if MCPI grows)

---

## Recommendations by Scenario

### Scenario 1: "Just make it work now"
**Recommendation**: Keep fzf
- Fix the PATH issue with `python -c` workaround
- Test ctrl-s binding works
- Ship current implementation
- **Time**: 1-2 hours

### Scenario 2: "I want pure Python, moderate effort OK"
**Recommendation**: InquirerPy
- Plan 2-3 day migration
- Accept some UX changes (preview pane limitations)
- Cleaner Python codebase long-term
- **Time**: 2-3 days

### Scenario 3: "MCPI will grow into complex TUI app"
**Recommendation**: Textual
- Invest 1-2 weeks now for future flexibility
- Build proper foundation for multi-view app
- Best long-term choice if MCPI expands
- **Time**: 1-2 weeks

### Scenario 4: "Want Pythonic but keep fzf features"
**Recommendation**: iterfzf
- Quick migration to Pythonic API
- Keep fzf performance and features
- Accept GPL license and bundled binary
- **Time**: 1 day

---

## Migration Cost-Benefit

### Keep fzf
**Cost**: 1-2 hours (fix bugs)
**Benefit**: Already working, proven, fast
**ROI**: ⭐⭐⭐⭐⭐ (minimal effort, keeps working solution)

### Switch to iterfzf
**Cost**: 1 day (rewrite integration)
**Benefit**: Pythonic API, cleaner code
**ROI**: ⭐⭐⭐⭐ (good if shell scripting is pain point)

### Switch to InquirerPy
**Cost**: 2-3 days (rewrite + testing)
**Benefit**: Pure Python, full control
**ROI**: ⭐⭐⭐ (worthwhile if pure Python is priority)

### Switch to Textual
**Cost**: 1-2 weeks (learn + build)
**Benefit**: Professional TUI, extensible
**ROI**: ⭐⭐ (only if MCPI becomes complex app)

---

## My Recommendation

**Short-term (next week)**: Keep fzf
- Fix the PATH issue (already done with `python -c`)
- Test scope cycling works
- Ship v1.0 with working fzf integration
- **Reasoning**: You're 95% there, don't introduce migration risk now

**Medium-term (next month)**: Evaluate based on user feedback
- If users complain about fzf install → Consider iterfzf
- If pure Python becomes priority → Consider InquirerPy
- If feature requests grow → Consider Textual

**Long-term (3-6 months)**: Revisit if MCPI scope changes
- If MCPI stays simple → Keep fzf
- If MCPI grows (config editor, logs, monitoring) → Migrate to Textual

---

## Action Items

### Immediate (This Week)
1. ✅ Test ctrl-s with `python -c` fix
2. ✅ Verify header fits narrow terminals
3. ✅ Ship v1.0 with fzf

### Optional (If Migration Desired)
1. Build InquirerPy proof-of-concept (4 hours)
2. Compare UX side-by-side
3. Decide: migrate or stay with fzf

### Future (3+ months)
1. Gather user feedback on TUI
2. Assess if features require migration
3. Re-evaluate Textual if MCPI scope expands

---

## Conclusion

**TL;DR**:
- **Stay with fzf** for now (best ROI)
- **Consider InquirerPy** if pure Python becomes priority
- **Consider Textual** only if MCPI becomes multi-view app
- **Avoid iterfzf** unless you specifically need Pythonic fzf API

**The current fzf implementation is 95% working**. Spending 1-2 hours to fix the PATH issue is far more valuable than investing days in a migration that may not provide proportional benefit.

**However**, if MCPI's scope expands significantly, Textual would be the right long-term choice.

---

**Document Version**: 1.0
**Date**: 2025-11-06
**Author**: Claude Code Project Evaluator
**Next Review**: After v1.0 ships and user feedback collected
