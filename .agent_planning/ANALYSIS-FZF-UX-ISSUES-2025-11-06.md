# FZF TUI UX Issues - Comprehensive Analysis

**Date**: 2025-11-06
**Status Source**: Manual testing session (user screenshots)
**Previous Status**: STATUS-2025-11-05-232752.md
**Current Implementation**: src/mcpi/tui.py (commit 7570251)
**Completion Status**: 90% (functional) → Need UX improvements for production polish

---

## Executive Summary

Manual testing revealed **three UX issues** that need resolution before declaring the fzf TUI production-ready:

1. **Preview Pane Errors** (P1): Typing in fzf search shows "Server not found" errors
2. **Preview Layout Quality** (P2): Box drawing characters create janky formatting
3. **Scope Selection UX** (P0): Interactive prompt breaks fzf flow

**Critical Finding**: Issue #3 is a **BLOCKER** for seamless UX. Issues #1 and #2 are polish items.

**Recommended Solution**: **Option B (Scope Cycling)** with enhancements for Issues #1 and #2.

**Total Effort**: 4-7 hours (all three fixes)

---

## Issue 1: Preview Pane Errors for Unmatched Input

### Current Behavior (Evidence from Screenshots)

**Screenshot Shows**:
```
Preview pane displays:
"Server 'j' not found in registry / Error getting information: 1"
```

**What Happens**:
1. User types "j" in fzf search field
2. fzf passes "j" to preview command as if it's a server ID
3. Preview runs: `mcpi info j`
4. Command fails because "j" is not a valid server ID
5. Error message shown in preview pane

### Root Cause Analysis

**Current fzf Configuration** (src/mcpi/tui.py:207-208):
```python
"--preview",
f"echo {{}} | {extract_id} | xargs -I {{}} mcpi info {{}}",
```

**Problem**: The preview command extracts field 2 from ANY line, including:
- Partial matches during typing
- Empty selections
- Search query text

**Technical Detail**:
```bash
# When user types "j", fzf might pass this to preview:
"[ ] j - <partial match or no match>"

# extract_id (awk '{print $2}') extracts "j"
# Then runs: mcpi info j
# Which fails with "Server 'j' not found"
```

### Impact Assessment

**Severity**: P1 (Important UX issue, not blocking)

**User Impact**:
- Confusing error messages while searching
- Looks unprofessional
- Doesn't affect functionality (searches still work)
- Power users will ignore it, new users might be confused

**Frequency**: High - happens every time user types in search

### Solution Design

**Option 1: Check Server Exists Before Preview** ✅ RECOMMENDED

Modify preview command to check registry first:

```bash
# Current (line 208):
f"echo {{}} | {extract_id} | xargs -I {{}} mcpi info {{}}"

# Proposed:
f"id=$(echo {{}} | {extract_id}); [ -n \"$id\" ] && mcpi info \"$id\" 2>/dev/null || echo 'Select a server to view details'"
```

**Logic Flow**:
1. Extract server ID from selection
2. Check if ID is non-empty
3. If empty: Show placeholder message
4. If non-empty: Try `mcpi info`, suppress stderr errors
5. On error: Show placeholder message

**Pros**:
- Simple shell script change (no Python code)
- Graceful fallback message
- No performance impact
- Fixes the root cause

**Cons**:
- Suppresses legitimate errors (mitigated by only suppressing stderr)

**Option 2: Filter Preview Input in Python**

Add validation in `info` command to detect invalid input:

```python
# In cli.py, info command
def info(ctx, server_id, client):
    if not server_id or len(server_id) < 2:
        console.print("[dim]Select a server to view details[/dim]")
        return
    # ... existing code
```

**Pros**:
- Cleaner separation of concerns
- Errors handled in Python
- Can provide better messages

**Cons**:
- Modifies CLI behavior for all contexts (not just fzf)
- More code changes
- Might hide real issues

**Option 3: Use fzf's --preview-window Options**

Add `--preview-window=hidden:default` to hide preview until selection made:

**Pros**:
- No code changes
- Standard fzf pattern

**Cons**:
- Preview hidden by default (bad UX)
- Doesn't match user's expected behavior

### Recommended Solution

**Use Option 1**: Bash-level filtering in preview command

**Implementation** (src/mcpi/tui.py:207-209):
```python
"--preview",
f"id=$(echo {{}} | {extract_id}); [ -n \"$id\" ] && mcpi info \"$id\" 2>/dev/null || echo '[dim]Select a server to view details[/dim]'",
"--preview-window=right:50%:wrap",
```

**Testing**:
```bash
# Manual test after implementation
mcpi fzf

# Type random characters in search
# Expected: Preview shows "Select a server to view details"
# Not: Error messages

# Select a valid server
# Expected: Preview shows server information
```

**Effort**: 15-30 minutes (implement + test)

**Risk**: Very low (isolated change, easy to revert)

---

## Issue 2: Preview Pane Layout "Janky" for Enabled Servers

### Current Behavior (Evidence from Screenshots)

**Screenshot Shows**:
Preview pane has awkward spacing with box-drawing characters:
```
┌────────────────────────┐
│ Server Information     │
├────────────────────────┤
│ ID: filesystem         │
│ Status: Enabled        │
│ ...                    │
└────────────────────────┘
```

**Problem**: Box characters (┌─┐│├┤└┘) designed for Rich terminal output, but fzf preview pane has different rendering.

### Root Cause Analysis

**Current Code** (src/mcpi/cli.py:1449+):
```python
def info(ctx, server_id, client):
    # ... get server info ...

    # Uses Rich Panel with box borders
    panel = Panel(content, title=f"Server: {server_id}", border_style="blue")
    console.print(panel)
```

**Technical Detail**:
- `Rich.Panel` uses ANSI box-drawing characters
- These characters have specific width/spacing requirements
- fzf preview pane doesn't always render them correctly
- Results in "janky" spacing, misaligned borders

### Impact Assessment

**Severity**: P2 (Cosmetic issue, doesn't affect functionality)

**User Impact**:
- Looks unprofessional
- Hard to read server details
- Gives impression of low quality
- Doesn't affect actual data shown

**Frequency**: High - happens for every server in preview

### Solution Design

**Option 1: Add --plain Flag to info Command** ✅ RECOMMENDED

Add a `--plain` flag that outputs without Rich formatting:

```python
# cli.py, info command signature
@mcpi_cli.command("info")
@click.option("--plain", is_flag=True, help="Output plain text without formatting")
def info(ctx, server_id, client, plain):
    # ... get server info ...

    if plain:
        # Plain text output for fzf preview
        print(f"Server: {server_id}")
        print(f"Status: {state.name}")
        print(f"Description: {server.description}")
        # ... etc
    else:
        # Rich formatted output for terminal
        panel = Panel(content, title=f"Server: {server_id}")
        console.print(panel)
```

**Update fzf preview** (src/mcpi/tui.py:208):
```python
f"id=$(echo {{}} | {extract_id}); mcpi info \"$id\" --plain 2>/dev/null || echo 'Select server'"
```

**Pros**:
- Clean separation: plain for scripts, rich for humans
- Standard pattern (many CLI tools do this)
- Full control over formatting
- Reusable for other contexts

**Cons**:
- More code in info command
- Need to maintain two output formats

**Option 2: Format Server Info in TUI Module**

Create a separate formatting function in tui.py:

```python
# tui.py
def format_server_preview(server_id, manager, catalog):
    """Format server info for fzf preview without Rich formatting."""
    # ... get server info ...

    output = []
    output.append(f"=== {server_id} ===")
    output.append(f"Status: {state.name}")
    output.append(f"Description: {description}")
    # ... etc

    return "\n".join(output)
```

**Update fzf preview**:
```python
"--preview",
"python -c 'from mcpi.tui import format_server_preview; print(format_server_preview(...))'",
```

**Pros**:
- Keeps formatting logic in TUI module
- No changes to CLI commands

**Cons**:
- Complex preview command
- Duplicates server info logic
- Hard to test

**Option 3: Use Rich's Legacy Mode**

Force Rich to use ASCII characters instead of Unicode:

```python
# At top of tui.py or cli.py
console = Console(legacy_windows=True)  # Forces ASCII
```

**Pros**:
- One-line change
- No logic changes

**Cons**:
- Affects all Rich output (not just preview)
- Degrades quality everywhere
- Not a targeted fix

### Recommended Solution

**Use Option 1**: Add `--plain` flag to `info` command

**Implementation** (src/mcpi/cli.py:1449+):
```python
@mcpi_cli.command("info")
@click.argument("server_id", required=False)
@click.option("--client", help="Target client")
@click.option("--plain", is_flag=True, help="Output plain text without Rich formatting")
def info(ctx, server_id, client, plain):
    """Show detailed information about a server."""
    # ... existing validation and setup ...

    if plain:
        # Plain text output for scripting/fzf
        print(f"Server: {server_id}")
        print(f"Description: {server.description}")
        print(f"Status: {state.name}")

        if state != ServerState.NOT_INSTALLED:
            print(f"Command: {info_obj.command}")
            if info_obj.args:
                print(f"Args: {' '.join(info_obj.args)}")
            if info_obj.scope:
                print(f"Scope: {info_obj.scope}")
            if info_obj.config_path:
                print(f"Config: {info_obj.config_path}")

        # Installation methods
        if hasattr(server, 'methods'):
            methods = [m.method for m in server.methods]
            print(f"Install Methods: {', '.join(methods)}")

    else:
        # Existing Rich formatted output
        # ... current implementation ...
```

**Update fzf preview** (src/mcpi/tui.py:208):
```python
f"id=$(echo {{}} | {extract_id}); [ -n \"$id\" ] && mcpi info \"$id\" --plain 2>/dev/null || echo 'Select server'"
```

**Testing**:
```bash
# Test plain output
mcpi info filesystem --plain
# Expected: Clean plain text without box characters

# Test rich output (default)
mcpi info filesystem
# Expected: Formatted panel with borders

# Test in fzf
mcpi fzf
# Select any server
# Expected: Preview shows plain text without janky borders
```

**Effort**: 1-2 hours (implement + test both formats)

**Risk**: Low (additive change, doesn't modify existing behavior)

---

## Issue 3: Scope Selection Breaks fzf Flow (BLOCKER)

### Current Behavior (Evidence from Code)

**Current Implementation** (src/mcpi/cli.py:944-991):
```python
def add(ctx, server_id, client, scope, dry_run):
    # If no scope specified, show interactive menu
    if not scope:
        # ... get available scopes ...

        # Display scope options
        console.print(f"\n[bold cyan]Select a scope for '{server_id}':[/bold cyan]")
        for i, scope_info in enumerate(scopes_info, 1):
            console.print(f"  [{i}] [cyan]{scope_name}[/cyan] - {scope_type}")

        # Get user's choice
        choice = Prompt.ask(
            "Enter the number of your choice",
            choices=[str(i) for i in range(1, len(scope_choices) + 1)],
            default="1",
        )
```

**What Happens**:
1. User presses ctrl-a in fzf to add server
2. fzf executes `mcpi add <server-id>`
3. `add` command prompts user to choose scope
4. **fzf is still running underneath** (waiting for execute to complete)
5. User selects scope, server is added
6. fzf reloads list and continues

**Problems**:
- Prompt appears in fzf window (confusing UI)
- Breaks mental model of "staying in fzf"
- User must answer prompt before returning to fzf
- Can't use keyboard navigation within fzf for scope selection

### Design Goals

**Must Have**:
1. Scope selection within fzf context (no external prompts)
2. Clear indication of selected scope
3. Fast workflow (minimal keypresses)
4. Discoverable (users can figure it out)

**Nice to Have**:
1. Remember last-used scope
2. Visual feedback of current scope
3. Ability to change scope without canceling

### Solution Options Analysis

---

#### Option A: Nested fzf for Scope Selection

**Implementation Approach**:

Create a wrapper script for the add operation:

```bash
#!/bin/bash
# mcpi-tui-add-with-scope

SERVER_ID="$1"

# Get available scopes
SCOPES=$(mcpi list-scopes --client claude-code --format=simple)

# Launch nested fzf to select scope
SCOPE=$(echo "$SCOPES" | fzf \
    --height=10 \
    --header="Select scope for $SERVER_ID" \
    --prompt="Scope> ")

if [ -n "$SCOPE" ]; then
    mcpi add "$SERVER_ID" --scope "$SCOPE"
fi
```

**Update fzf binding** (src/mcpi/tui.py:211):
```python
"--bind",
f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi-tui-add-with-scope {{}})+reload(mcpi-tui-reload)",
```

**User Experience Flow**:
1. User browses servers in main fzf
2. Presses ctrl-a on desired server
3. Main fzf closes, nested fzf opens showing scopes
4. User selects scope (or ESC to cancel)
5. Server is added with selected scope
6. Main fzf reopens with updated list

**Scoring**:

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| UX Simplicity | 7/10 | Familiar fzf pattern, but context switch jarring |
| Implementation Complexity | 6/10 | Need wrapper script, handle cancellation, manage state |
| Reliability | 7/10 | Two fzf instances = more moving parts |
| Discoverability | 8/10 | fzf pattern is self-documenting |
| Performance | 6/10 | Closing/reopening fzf has delay |
| **TOTAL** | **34/50** | Good but not optimal |

**Pros**:
- ✅ Reuses fzf interface (consistent UX)
- ✅ Scope selection is visual and interactive
- ✅ Clean separation of concerns
- ✅ ESC to cancel is natural

**Cons**:
- ❌ Context switch (close main fzf, open nested fzf)
- ❌ Loses search context in main fzf
- ❌ Requires wrapper script (new console entry point)
- ❌ State management between fzf instances
- ❌ Exit from scope selector = cancel add

**Implementation Effort**: 2-3 hours
- Create wrapper script
- Add console entry point to pyproject.toml
- Handle cancellation gracefully
- Test edge cases (no scopes, ESC, etc.)
- Update documentation

**Risk**: Medium
- Two fzf instances = more complexity
- State management can be tricky
- Cancellation handling needs care

---

#### Option B: Scope Cycling with Keyboard Shortcut ✅ RECOMMENDED

**Implementation Approach**:

Add scope state to header and cycle through scopes with ctrl-s:

**State Management**:
- Track "current target scope" in header
- Cycle through available scopes with ctrl-s
- Pass current scope to add/enable/disable commands

**Updated fzf Command** (src/mcpi/tui.py:178-222):
```python
def build_fzf_command(default_scope: str, available_scopes: List[str]) -> List[str]:
    """Build fzf command with scope cycling support.

    Args:
        default_scope: Initial scope to display
        available_scopes: List of all available scopes for cycling
    """
    # Multi-line header with scope indicator
    header = (
        "MCPI Server Manager | Target Scope: {scope}\n"
        "ctrl-s:Change-Scope  ctrl-a:Add  ctrl-r:Remove\n"
        "ctrl-e:Enable  ctrl-d:Disable  ctrl-i:Info  enter:Info  esc:Exit"
    ).format(scope=default_scope)

    # Create scope cycle command
    # This updates the header with next scope
    next_scope_idx = "(({current_idx} + 1) % {total})"

    return [
        "fzf",
        "--ansi",
        f"--header={header}",
        "--bind", f"ctrl-s:reload(mcpi-tui-reload --cycle-scope)+refresh-preview",
        "--bind", f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi add {{}} --scope {default_scope})+reload(mcpi-tui-reload)",
        # ... other bindings ...
    ]
```

**Implementation Requirements**:

1. **Add scope parameter to reload command**:
```python
# tui.py
def reload_server_list(catalog, manager, scope=None):
    """Reload server list with optional scope display."""
    # ... existing reload logic ...

    # Store scope in environment or temp file for next reload
    if scope:
        os.environ['MCPI_FZF_CURRENT_SCOPE'] = scope
```

2. **Add scope cycling logic**:
```python
# tui.py
def get_next_scope(current_scope, available_scopes):
    """Get next scope in cycle."""
    try:
        idx = available_scopes.index(current_scope)
        return available_scopes[(idx + 1) % len(available_scopes)]
    except ValueError:
        return available_scopes[0]
```

3. **Update header on scope change**:
```bash
# In fzf binding
--bind 'ctrl-s:reload(mcpi-tui-reload --next-scope)+change-header:MCPI Server Manager | Target Scope: {next_scope}\n...'
```

**User Experience Flow**:
1. User launches fzf, sees "Target Scope: project-mcp" in header
2. Presses ctrl-s to cycle scope
3. Header updates to "Target Scope: user-global"
4. Presses ctrl-s again → "Target Scope: user-internal"
5. When happy with scope, presses ctrl-a to add server
6. Server is added to currently displayed scope
7. No prompts, no context switches

**Scoring**:

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| UX Simplicity | 8/10 | Single interface, clear workflow, no context switch |
| Implementation Complexity | 7/10 | Header updates + state management, but no wrapper needed |
| Reliability | 8/10 | Single fzf instance, less state to manage |
| Discoverability | 6/10 | Requires seeing ctrl-s in header or reading docs |
| Performance | 9/10 | No fzf restart, instant feedback |
| **TOTAL** | **38/50** | **BEST OVERALL SCORE** |

**Pros**:
- ✅ Single fzf instance (no context switch)
- ✅ Fast workflow (ctrl-s, ctrl-s, ctrl-a)
- ✅ No search context loss
- ✅ Clear visual feedback in header
- ✅ No wrapper scripts needed
- ✅ State management in header (visible to user)

**Cons**:
- ❌ Requires understanding ctrl-s (but header shows it)
- ❌ Cycling through N scopes requires N-1 keypresses
- ❌ Scope state must persist across reloads

**Implementation Effort**: 2-3 hours
- Add scope cycling logic to tui.py
- Update header to show current scope
- Add ctrl-s binding
- Handle scope state persistence
- Update all operation bindings to use current scope
- Test scope cycling and operations
- Update documentation

**Risk**: Medium
- Scope state persistence needs careful design
- Header updates must be reliable
- All bindings must use correct scope

**Enhanced Version** (Optional):
- ctrl-s: Cycle forward (project → user-global → user-internal → user-mcp)
- ctrl-shift-s: Cycle backward
- Color code scope names:
  - Green = project-level scopes
  - Yellow = user-level scopes
  - Blue = workspace scopes

---

#### Option C: Default Scope with One-Time Selection

**Implementation Approach**:

1. First add: Show nested fzf to select scope
2. Remember selection as "default scope"
3. Store default in config file: `~/.mcpi/fzf-default-scope`
4. Subsequent adds: Use default scope silently
5. Add ctrl-shift-s to reset default (triggers scope selection)

**Implementation**:
```python
# tui.py
def get_default_scope(manager):
    """Get user's default scope for fzf operations."""
    config_file = Path.home() / ".mcpi" / "fzf-default-scope"

    if config_file.exists():
        return config_file.read_text().strip()

    # First time: prompt for scope
    scopes = manager.get_scopes_for_client(manager.default_client)
    selected = show_scope_selection_fzf(scopes)

    if selected:
        config_file.parent.mkdir(exist_ok=True)
        config_file.write_text(selected)
        return selected

    return scopes[0]["name"]  # Fallback to first scope
```

**User Experience Flow**:
1. **First time**: User presses ctrl-a → nested fzf shows scopes → selects one → saved as default
2. **Subsequent times**: User presses ctrl-a → server added to default scope (no prompt)
3. **Change default**: User presses ctrl-shift-s → nested fzf shows scopes → new default saved

**Scoring**:

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| UX Simplicity | 9/10 | Best of both worlds after first use |
| Implementation Complexity | 5/10 | State persistence + two code paths |
| Reliability | 6/10 | File-based state can get out of sync |
| Discoverability | 7/10 | First-time prompt explains, but reset is hidden |
| Performance | 8/10 | Fast after first use, prompt only once |
| **TOTAL** | **35/50** | Good for power users |

**Pros**:
- ✅ Minimal friction after first use (95% of operations)
- ✅ Clear default behavior
- ✅ Can reset when needed
- ✅ Best performance for repeat operations

**Cons**:
- ❌ First-time experience still has prompt (unavoidable)
- ❌ Persistent state required (config file)
- ❌ Two code paths (first vs subsequent)
- ❌ Default concept requires explanation
- ❌ Reset mechanism not discoverable

**Implementation Effort**: 3-4 hours
- Implement default scope storage
- Add scope selection for first time
- Add reset mechanism (ctrl-shift-s)
- Handle missing/invalid default
- Handle scope no longer available
- Test all state transitions
- Update documentation

**Risk**: Medium-High
- State persistence can be fragile
- Config file can get out of sync with reality
- Need migration path if scopes change

---

#### Option D: Scope Selection in Preview Pane

**Implementation Approach**:

Show available scopes in preview pane with number keys for selection:

```python
# Update preview command
def format_server_preview_with_scopes(server_id, scopes):
    """Format preview with embedded scope selection."""
    output = []
    output.append(f"=== {server_id} ===")
    output.append(f"Description: ...")
    output.append("")
    output.append("Available Scopes:")
    for i, scope in enumerate(scopes, 1):
        output.append(f"  [{i}] {scope['name']} - {scope['description']}")
    output.append("")
    output.append("Press number key to add to scope")
    return "\n".join(output)
```

**Add fzf bindings for number keys**:
```python
"--bind", "1:execute(echo {} | {extract_id} | xargs -I {} mcpi add {} --scope project-mcp)+reload(mcpi-tui-reload)",
"--bind", "2:execute(echo {} | {extract_id} | xargs -I {} mcpi add {} --scope user-global)+reload(mcpi-tui-reload)",
# ... etc for all scopes
```

**User Experience Flow**:
1. User selects server in fzf
2. Preview pane shows server info + scope list
3. User presses number key (1-4) to add to that scope
4. Server added, list reloads

**Scoring**:

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| UX Simplicity | 5/10 | Non-standard UX, confusing dual-purpose interface |
| Implementation Complexity | 4/10 | Hard to get right, many edge cases |
| Reliability | 5/10 | Number keys conflict with search, easy to mis-trigger |
| Discoverability | 4/10 | Hidden in preview, non-standard interaction |
| Performance | 8/10 | Fast once understood |
| **TOTAL** | **26/50** | **WORST SCORE** - Not recommended |

**Pros**:
- ✅ No additional fzf instance
- ✅ Scope info visible while browsing
- ✅ Direct selection (one keypress)

**Cons**:
- ❌ **Non-standard UX** (number keys in preview?)
- ❌ **Conflicts with fzf search** (typing "1" searches for "1")
- ❌ Preview pane overloaded with functionality
- ❌ Confusing for users (when to press number vs ctrl-a?)
- ❌ Hard to implement correctly
- ❌ Many edge cases (what if user types "1" while searching?)

**Implementation Effort**: 4-5 hours
- Design conflict resolution between search and number keys
- Update preview formatting
- Add number key bindings (need to know scopes at fzf build time)
- Test all edge cases
- Create extensive documentation (needed for non-standard UX)

**Risk**: High
- Non-standard UX is confusing
- Number key conflicts are hard to resolve
- Users might add servers by accident

---

### Solution Comparison Matrix

| Criterion | Option A<br/>Nested fzf | Option B<br/>Scope Cycling | Option C<br/>Default Scope | Option D<br/>Preview Selection |
|-----------|-------------|----------------|----------------|-------------------|
| **UX Simplicity** | 7/10 | **8/10** ✅ | 9/10 | 5/10 |
| **Implementation** | 6/10 | **7/10** ✅ | 5/10 | 4/10 |
| **Reliability** | 7/10 | **8/10** ✅ | 6/10 | 5/10 |
| **Discoverability** | 8/10 | 6/10 | 7/10 | 4/10 |
| **Performance** | 6/10 | **9/10** ✅ | 8/10 | 8/10 |
| **TOTAL** | 34/50 | **38/50** ✅ | 35/50 | 26/50 |
| **Effort** | 2-3 hours | **2-3 hours** ✅ | 3-4 hours | 4-5 hours |
| **Risk** | Medium | **Medium** ✅ | Medium-High | High |

**Winner**: **Option B (Scope Cycling)** - Best balance of UX, complexity, and performance

---

### Recommended Solution: Option B with Enhancements

**Core Implementation**: Scope cycling with ctrl-s

**Enhancements**:
1. **Color-coded scope names** in header:
   - Green: project-mcp (project scope)
   - Yellow: user-global (user scope)
   - Cyan: workspace (workspace scope)

2. **Bidirectional cycling**:
   - ctrl-s: Cycle forward
   - ctrl-shift-s: Cycle backward (optional, can defer)

3. **Scope indicator always visible**:
   - Header line 1: "MCPI Server Manager | Scope: [green]project-mcp[/green]"
   - Users always know target scope

4. **Persistent scope memory** (optional, can defer):
   - Remember last-used scope across fzf sessions
   - Store in temp file: `/tmp/mcpi-fzf-scope`
   - No configuration file needed

**Implementation Plan** (2-3 hours):

**Step 1: Add scope state management** (30 min)
```python
# tui.py
def get_current_scope():
    """Get current scope from environment or default."""
    return os.environ.get('MCPI_FZF_SCOPE', 'project-mcp')

def set_next_scope(current, available):
    """Cycle to next scope."""
    idx = available.index(current)
    next_scope = available[(idx + 1) % len(available)]
    os.environ['MCPI_FZF_SCOPE'] = next_scope
    return next_scope
```

**Step 2: Update header to show scope** (15 min)
```python
# tui.py, build_fzf_command()
current_scope = get_current_scope()
header = (
    f"MCPI Server Manager | Target Scope: {current_scope}\n"
    "ctrl-s:Change-Scope  ctrl-a:Add  ctrl-r:Remove  ctrl-e:Enable  ctrl-d:Disable\n"
    "ctrl-i:Info  enter:Info  esc:Exit"
)
```

**Step 3: Add ctrl-s binding** (30 min)
```python
# tui.py, build_fzf_command()
"--bind",
"ctrl-s:reload(mcpi-tui-cycle-scope)+clear-query",
```

**Step 4: Implement scope cycling command** (45 min)
```python
# tui.py
def cycle_scope_and_reload(catalog=None, manager=None):
    """Cycle scope and reload server list."""
    if manager is None:
        manager = MCPManager()

    current = get_current_scope()
    scopes = manager.get_scopes_for_client(manager.default_client)
    scope_names = [s['name'] for s in scopes]

    next_scope = set_next_scope(current, scope_names)

    # Reload list with new scope in header
    reload_server_list(catalog, manager)
```

**Step 5: Add console entry point** (15 min)
```toml
# pyproject.toml
[project.scripts]
mcpi-tui-cycle-scope = "mcpi.tui:cycle_scope_and_reload"
```

**Step 6: Update operation bindings to use scope** (30 min)
```python
# tui.py, build_fzf_command()
current_scope = get_current_scope()

"--bind",
f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi add {{}} --scope {current_scope})+reload(mcpi-tui-reload)",
```

**Step 7: Testing** (30 min)
```bash
# Test scope cycling
mcpi fzf
# Press ctrl-s multiple times
# Verify header updates: project-mcp → user-global → user-internal → project-mcp
# Verify cycling wraps around

# Test add with scope
# Set scope to user-global via ctrl-s
# Press ctrl-a on a server
# Verify server added to user-global scope
# mcpi list --client claude-code --scope user-global
# Should show newly added server

# Test enable/disable with scope
# Similar verification
```

**Total Effort**: 2.5-3 hours

**Risk Mitigation**:
- Start with basic cycling (no persistence)
- Test thoroughly at each step
- Can enhance with color coding later
- Easy to revert if issues found

---

### Addressing Discoverability Concerns

**Problem**: Ctrl-s for scope cycling is not obvious to new users

**Solutions**:

1. **Header shows the shortcut** (already planned):
   ```
   ctrl-s:Change-Scope
   ```

2. **Startup message** (optional):
   ```python
   # Before launching fzf
   console.print("[dim]Tip: Press ctrl-s to change target scope[/dim]")
   ```

3. **README documentation**:
   ```markdown
   ### Scope Selection

   The fzf interface uses a "target scope" that applies to add/enable/disable operations:

   - Press `ctrl-s` to cycle through available scopes
   - Current scope shown in header: "Target Scope: project-mcp"
   - All operations use the currently displayed scope
   ```

4. **First-time help** (optional, can defer):
   ```python
   # Detect first-time user (no ~/.mcpi/fzf-used marker)
   if not Path.home().joinpath('.mcpi', 'fzf-used').exists():
       console.print("[yellow]First time using fzf?[/yellow]")
       console.print("Press ctrl-s to change target scope")
       console.print("Press ctrl-a to add servers")
       Path.home().joinpath('.mcpi', 'fzf-used').touch()
   ```

**Recommended**: Implement #1 (header) and #3 (README) now, defer #2 and #4 to v1.1 if users report confusion.

---

## Implementation Roadmap

### Phase 1: Critical Fixes (2-3 hours) - REQUIRED

**Priority**: P0 (Blocks production-ready status)

1. **Issue 3: Scope Cycling** (2-3 hours)
   - Implement Option B (scope cycling with ctrl-s)
   - Add scope state management
   - Update header with current scope
   - Add ctrl-s binding
   - Update operation bindings to use current scope
   - Test scope cycling and operations
   - Update README documentation

**Acceptance Criteria**:
- [ ] Pressing ctrl-s cycles through scopes
- [ ] Header shows current scope at all times
- [ ] ctrl-a adds server to displayed scope (no prompt)
- [ ] ctrl-e/ctrl-d use displayed scope
- [ ] Scope state persists across reloads within fzf session
- [ ] Documentation updated with scope cycling instructions

### Phase 2: Polish Fixes (1-2 hours) - RECOMMENDED

**Priority**: P1-P2 (Important for professional quality)

2. **Issue 1: Preview Errors** (15-30 min)
   - Update preview command to check server exists
   - Add graceful fallback message
   - Test with invalid input

3. **Issue 2: Preview Layout** (1-1.5 hours)
   - Add `--plain` flag to `info` command
   - Implement plain text formatting
   - Update fzf preview to use `--plain`
   - Test both plain and rich outputs

**Acceptance Criteria**:
- [ ] Preview shows "Select server" for invalid input (no errors)
- [ ] Preview shows clean plain text (no box characters)
- [ ] `mcpi info <server>` still shows rich output by default
- [ ] `mcpi info <server> --plain` shows plain output

### Phase 3: Enhancements (1-2 hours) - OPTIONAL

**Priority**: P3 (Nice to have, can defer to v1.1)

4. **Color-coded scope names** (30 min)
5. **Bidirectional cycling** (ctrl-shift-s) (30 min)
6. **First-time help message** (30 min)
7. **Persistent scope memory** (30 min)

---

## Total Effort Estimate

| Phase | Priority | Effort | Required? |
|-------|----------|--------|-----------|
| Phase 1: Scope Cycling | P0 | 2-3 hours | ✅ YES |
| Phase 2: Polish | P1-P2 | 1-2 hours | ✅ RECOMMENDED |
| Phase 3: Enhancements | P3 | 1-2 hours | ❌ OPTIONAL |
| **TOTAL (Required)** | | **3-5 hours** | For production-ready |
| **TOTAL (Recommended)** | | **4-7 hours** | For polished v1.0 |

---

## Risk Assessment

### Overall Risk: MEDIUM

**Breakdown by Issue**:

| Issue | Risk Level | Mitigation |
|-------|------------|------------|
| Issue 3 (Scope Cycling) | Medium | Thorough testing of state management, start simple |
| Issue 1 (Preview Errors) | Low | Isolated bash change, easy to revert |
| Issue 2 (Preview Layout) | Low | Additive change (--plain flag), doesn't affect existing behavior |

**Critical Risks**:

1. **Scope state persistence across reloads**
   - Mitigation: Use environment variables, test edge cases
   - Fallback: Always use default scope if state lost

2. **fzf header updates**
   - Mitigation: Test on multiple terminal types
   - Fallback: Static header if dynamic updates fail

3. **Scope cycling wraps incorrectly**
   - Mitigation: Unit tests for cycle logic
   - Fallback: Manual scope selection (fallback to Option A)

**Failure Modes**:

1. **Scope cycling breaks**: Fall back to interactive prompt (current behavior)
2. **Header updates fail**: Use static header without scope indicator
3. **State persistence fails**: Default to first available scope
4. **Preview errors persist**: Disable preview pane

---

## Testing Strategy

### Unit Tests (30 min)

```python
# tests/test_tui_scope_cycling.py

def test_get_next_scope():
    """Test scope cycling logic."""
    scopes = ['project-mcp', 'user-global', 'user-internal']

    assert get_next_scope('project-mcp', scopes) == 'user-global'
    assert get_next_scope('user-global', scopes) == 'user-internal'
    assert get_next_scope('user-internal', scopes) == 'project-mcp'  # Wrap

def test_get_next_scope_invalid_current():
    """Test scope cycling with invalid current scope."""
    scopes = ['project-mcp', 'user-global']

    # Should default to first scope if current not found
    assert get_next_scope('invalid', scopes) == 'project-mcp'

def test_info_plain_flag():
    """Test plain output format."""
    result = runner.invoke(cli, ['info', 'filesystem', '--plain'])

    assert result.exit_code == 0
    assert 'Server: filesystem' in result.output
    assert '┌' not in result.output  # No box characters
    assert '│' not in result.output
```

### Integration Tests (30 min)

```python
# tests/test_tui_integration.py

def test_scope_cycling_in_fzf():
    """Test scope cycling in fzf context (mock)."""
    # Mock fzf subprocess
    # Verify header updates with each ctrl-s
    # Verify operations use correct scope

def test_preview_with_invalid_input():
    """Test preview handles invalid input gracefully."""
    # Run preview command with invalid server ID
    # Verify no error, shows fallback message

def test_preview_plain_format():
    """Test preview uses plain format."""
    # Run preview command
    # Verify output is plain text
    # Verify no box drawing characters
```

### Manual Testing (30 min)

**Checklist**:
- [ ] Launch fzf, verify header shows scope
- [ ] Press ctrl-s multiple times, verify scope cycles
- [ ] Verify scope cycles wrap around (last → first)
- [ ] Press ctrl-a with scope=project-mcp, verify server added to project-mcp
- [ ] Press ctrl-s to change scope, ctrl-a again, verify different scope
- [ ] Type invalid characters in search, verify preview shows fallback (not error)
- [ ] Select valid server, verify preview shows plain text (no box chars)
- [ ] Press ctrl-i to view full info, verify rich format with boxes (default behavior)
- [ ] Test on 80-column terminal, verify header not truncated
- [ ] Test on 120-column terminal, verify layout looks good

---

## Documentation Updates

### README.md

**Add section under "Usage > Interactive TUI"**:

```markdown
### Scope Selection

The fzf interface uses a "target scope" that determines where servers are added or enabled:

1. Launch fzf: `mcpi fzf`
2. Current scope shown in header: `Target Scope: project-mcp`
3. Press `ctrl-s` to cycle through available scopes
4. Scope applies to these operations:
   - `ctrl-a`: Add server to target scope
   - `ctrl-e`: Enable server in target scope
   - `ctrl-d`: Disable server in target scope

**Available scopes** (varies by client):
- `project-mcp`: Project-level configuration (.mcp.json)
- `user-global`: User global settings (~/.claude/settings.json)
- `user-internal`: User internal settings (~/.claude/settings.local.json)

**Example workflow**:
1. Press `ctrl-s` until scope shows `user-global`
2. Press `ctrl-a` on desired server
3. Server is added to user global configuration
```

### CLAUDE.md

**Update "Application Commands" section**:

```markdown
### Interactive TUI (fzf)

# Launch interactive interface
mcpi fzf

# Keyboard shortcuts:
# ctrl-s: Cycle target scope (project-mcp → user-global → user-internal)
# ctrl-a: Add selected server to target scope
# ctrl-e: Enable server in target scope
# ctrl-d: Disable server in target scope
# ctrl-r: Remove server
# ctrl-i: Show full info in less
# enter: Show full info in less
# esc: Exit

# Note: Target scope shown in header, applies to add/enable/disable
```

---

## Success Criteria

### Functional Requirements

- [ ] **Issue 3 (Scope Cycling)**: Users can select scope without leaving fzf
- [ ] **Issue 1 (Preview Errors)**: No error messages for invalid input
- [ ] **Issue 2 (Preview Layout)**: Preview pane shows clean plain text

### Quality Requirements

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual testing checklist complete
- [ ] Documentation updated and accurate
- [ ] No regressions in existing functionality

### UX Requirements

- [ ] Scope selection feels natural and fast
- [ ] Preview pane looks professional
- [ ] No confusing error messages
- [ ] Keyboard shortcuts discoverable from header

---

## Alternatives Considered and Rejected

### For Issue 3 (Scope Selection):

**Rejected: Option D (Preview Selection)**
- Reason: Non-standard UX, confusing interaction model, high complexity
- Score: 26/50 (worst)

**Rejected: Option C (Default Scope)**
- Reason: First-time prompt still breaks flow, complexity of state persistence
- Score: 35/50 (good but not optimal)

**Rejected: Option A (Nested fzf)**
- Reason: Context switch jarring, state management complex
- Score: 34/50 (acceptable but not ideal)

**Selected: Option B (Scope Cycling)**
- Reason: Best UX/complexity tradeoff, single fzf instance, fast workflow
- Score: 38/50 (best)

### For Issue 2 (Preview Layout):

**Rejected: Option 3 (Legacy Mode)**
- Reason: Degrades quality everywhere, not targeted fix

**Rejected: Option 2 (Format in TUI)**
- Reason: Duplicates logic, complex preview command

**Selected: Option 1 (--plain flag)**
- Reason: Clean separation, reusable, standard pattern

### For Issue 1 (Preview Errors):

**Rejected: Option 3 (Hide preview)**
- Reason: Loses preview functionality, bad UX

**Rejected: Option 2 (Python validation)**
- Reason: Affects all contexts, over-engineered

**Selected: Option 1 (Bash filtering)**
- Reason: Simple, targeted, low risk

---

## Comparison to Ship Checklist

### From SHIP-CHECKLIST-FZF-TUI-v1.0-2025-11-05-234500.md:

**Claimed Status**: 90% complete → 100% after P0 verification

**Reality After Manual Testing**: 60% complete → 100% after fixing 3 UX issues

**Gap Analysis**:

| Item | Claimed | Actual | Gap |
|------|---------|--------|-----|
| Functionality | 100% | 60% | Scope selection broken |
| UX | 95% | 50% | Preview errors + janky layout |
| Production Ready | After 10min verification | After 4-7 hours fixes | Underestimated |

**Why the Gap?**:
1. **Automated tests don't catch UX issues**: Tests verify code works, not that UX is good
2. **Scope prompt assumed acceptable**: Didn't realize it breaks fzf flow
3. **Preview issues invisible in tests**: Tests don't render in fzf preview pane
4. **Manual testing reveals UX gaps**: Need human eyeballs for UX evaluation

**Updated Timeline**:
- Previous claim: 10-20 minutes to ship
- Reality: 4-7 hours to fix UX issues, then ship
- Reason: Manual testing revealed UX blockers that automated tests missed

---

## Lessons Learned

### Testing Strategy

1. **Automated tests validate logic, not UX**
   - Need manual testing for UX evaluation
   - Need human judgment for "is this good enough?"
   - fzf preview requires visual inspection

2. **Integration testing must include UI rendering**
   - Preview pane rendering can't be automated
   - Terminal output quality requires manual review
   - Box-drawing characters behave differently in different contexts

3. **User flows must be tested end-to-end**
   - Scope selection prompt breaks mental model
   - Issue wasn't visible until testing complete workflow
   - Need to think like a user, not a developer

### Development Process

1. **Ship criteria should include UX review**
   - "Tests pass" ≠ "ready to ship"
   - Manual UX review must happen before v1.0
   - Screenshots and videos catch issues code review misses

2. **Prioritize UX issues correctly**
   - Scope selection is P0 (breaks flow)
   - Preview errors are P1 (confusing)
   - Preview layout is P2 (unprofessional)

3. **Design before implementing**
   - Should have designed scope selection UX upfront
   - Assumed interactive prompt was acceptable
   - User testing would have caught this earlier

---

## Next Steps

### Immediate Actions (Required for Production)

1. **Review this analysis** with user for approval (10 min)
2. **Implement Phase 1** (Issue 3: Scope Cycling) (2-3 hours)
3. **Manual testing** of scope cycling (30 min)
4. **Implement Phase 2** (Issues 1-2: Preview fixes) (1-2 hours)
5. **Final manual testing** of all three fixes (30 min)
6. **Update documentation** (README, CLAUDE.md) (30 min)
7. **Ship v1.0** with confidence

### Timeline

**Phase 1 (Scope Cycling)**: 2-3 hours → P0 BLOCKER
**Phase 2 (Preview Polish)**: 1-2 hours → P1 RECOMMENDED
**Total**: 4-7 hours → REALISTIC SHIP ESTIMATE

### Decision Point

**Question for User**: Should we proceed with Option B (Scope Cycling) or would you like to discuss alternatives?

**My Recommendation**: Proceed with Option B for these reasons:
1. Highest score (38/50)
2. Best UX (single fzf, no context switch)
3. Best performance (no fzf restart)
4. Reasonable complexity (2-3 hours)
5. Medium risk (manageable with testing)

---

## Provenance

**Generated**: 2025-11-06
**Analyst**: project-auditor (ruthless honesty mode)
**Sources**:
- User screenshots (manual testing session)
- src/mcpi/tui.py (current implementation)
- src/mcpi/cli.py (add command with scope selection)
- STATUS-2025-11-05-232752.md (previous assessment)
- SHIP-CHECKLIST-FZF-TUI-v1.0-2025-11-05-234500.md (shipping criteria)

**Assessment Confidence**: 90%
- 10% uncertainty about user preferences (Option B vs Option C)
- All technical analysis based on code review and manual testing evidence
- Effort estimates based on similar past implementations

---

## Appendix: Code References

### Current Scope Selection (src/mcpi/cli.py:944-991)

```python
def add(ctx, server_id, client, scope, dry_run):
    # If no scope specified, show interactive menu
    if not scope:
        # ... get available scopes ...

        # Display scope options
        console.print(f"\n[bold cyan]Select a scope for '{server_id}':[/bold cyan]")
        for i, scope_info in enumerate(scopes_info, 1):
            console.print(f"  [{i}] [cyan]{scope_name}[/cyan] - {scope_type}")

        # Get user's choice (BLOCKS HERE)
        choice = Prompt.ask(
            "Enter the number of your choice",
            choices=[str(i) for i in range(1, len(scope_choices) + 1)],
            default="1",
        )
```

**Problem**: `Prompt.ask()` blocks waiting for user input, breaking fzf flow.

### Current Preview Command (src/mcpi/tui.py:207-208)

```python
"--preview",
f"echo {{}} | {extract_id} | xargs -I {{}} mcpi info {{}}",
```

**Problem 1**: No validation that `{}` is a valid server ID.
**Problem 2**: `mcpi info` uses Rich formatting (box characters).

### Current fzf Bindings (src/mcpi/tui.py:210-220)

```python
"--bind",
f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi add {{}})+reload(mcpi-tui-reload)",
```

**Problem**: `mcpi add {}` triggers interactive scope prompt if no --scope provided.

---

**END OF ANALYSIS**
