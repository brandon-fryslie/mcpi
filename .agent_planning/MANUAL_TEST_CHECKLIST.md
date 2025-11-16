# Manual Testing Checklist: fzf TUI Adapter

**Date**: 2025-11-06
**Priority**: P0 (Critical)
**Feature**: fzf TUI with scope cycling and --plain preview
**Tester**: _______________

## Pre-Test Verification

- [x] fzf is installed: `fzf --version` → 0.66.1 (brew)
- [x] mcpi fzf command exists: `mcpi fzf --help` works
- [x] Adapter pattern is integrated in CLI
- [x] --plain flag implemented for info command

## Test Environment

```bash
# Working directory
cd /Users/bmf/icode/mcpi

# Verify installation
mcpi --version
fzf --version

# Check available scopes
mcpi scope list
```

## Testing Checklist

### 1. Basic Launch ✓/✗

**Test**: Launch fzf interface without errors

**Steps**:
```bash
mcpi fzf
```

**Expected**:
- [ ] fzf interface opens successfully
- [ ] Header displays: "MCPI | Scope: [scope-name]"
- [ ] Server list displays with status indicators:
  - Green [✓] for enabled servers
  - Yellow [✗] for disabled servers
  - White [ ] for not-installed servers
- [ ] Preview pane shows placeholder: "Select a server to view details"

**Actual**: _______________

---

### 2. Scope Display and Cycling (ctrl-s) ✓/✗

**Test**: Verify scope cycling with ctrl-s

**Steps**:
1. Note current scope in header (Line 1: "MCPI | Scope: X")
2. Press `ctrl-s`
3. Observe header update
4. Press `ctrl-s` multiple times
5. Verify cycling through all available scopes

**Expected**:
- [ ] Header shows current scope name
- [ ] ctrl-s cycles to next scope
- [ ] Cycling wraps around (last → first)
- [ ] Terminal shows message: "Switched to scope: [name]"
- [ ] Server list reloads after scope change
- [ ] Query clears after scope change

**Actual**: _______________

**Available Scopes** (verify all appear):
- project-mcp
- project-local
- user-global
- (others from `mcpi scope list`)

---

### 3. Preview Pane with --plain Flag ✓/✗

**Test**: Verify preview pane uses plain text formatting

**Steps**:
1. Navigate to any server in the list (use arrow keys)
2. Observe preview pane on the right

**Expected**:
- [ ] Preview shows server information
- [ ] NO box-drawing characters (╭─╮│╯╰)
- [ ] Plain text format with clear sections:
  - Registry Information:
  - ID: [server-id]
  - Description: [description]
  - Command: [command]
  - Local Installation:
  - Status: [status]
- [ ] Text wraps properly in narrow pane
- [ ] NO errors while typing in search

**Test Edge Case**: Type random letters (e.g., "asdf")
- [ ] Preview shows: "Select a server to view details"
- [ ] NO error messages about server not found

**Actual**: _______________

---

### 4. Server Operations with Scope Respect ✓/✗

**Test**: Verify operations use displayed scope

#### 4a. Add Server (ctrl-a)

**Steps**:
1. Set scope to "project-mcp" (use ctrl-s)
2. Select a not-installed server [ ]
3. Press `ctrl-a`
4. Wait for operation to complete

**Expected**:
- [ ] Server is added to "project-mcp" scope
- [ ] Server list reloads automatically
- [ ] Server now shows as enabled [✓] or disabled [✗]
- [ ] Verify with: `mcpi list --scope project-mcp`

**Actual**: _______________

#### 4b. Enable Server (ctrl-e)

**Steps**:
1. Set scope to "project-local" (use ctrl-s)
2. Select a disabled server [✗]
3. Press `ctrl-e`

**Expected**:
- [ ] Server enabled in "project-local" scope
- [ ] Server list reloads
- [ ] Server shows green [✓]
- [ ] Verify with: `mcpi list --scope project-local`

**Actual**: _______________

#### 4c. Disable Server (ctrl-d)

**Steps**:
1. Set scope to current displayed scope
2. Select an enabled server [✓]
3. Press `ctrl-d`

**Expected**:
- [ ] Server disabled in displayed scope
- [ ] Server list reloads
- [ ] Server shows yellow [✗]

**Actual**: _______________

#### 4d. Remove Server (ctrl-r)

**Steps**:
1. Select an installed server
2. Press `ctrl-r`

**Expected**:
- [ ] Server removed from configuration
- [ ] Server list reloads
- [ ] Server shows white [ ]

**Actual**: _______________

---

### 5. Info Display (ctrl-i / Enter) ✓/✗

**Test**: Verify detailed info display

**Steps**:
1. Select any server
2. Press `Enter` (or `ctrl-i`)

**Expected**:
- [ ] Opens `less` pager with server details
- [ ] Info displayed with Rich formatting (boxes allowed here)
- [ ] All sections present:
  - Server Information
  - Registry Information
  - Local Installation
  - Status
- [ ] Can exit with `q`
- [ ] Returns to fzf interface after exit

**Actual**: _______________

---

### 6. Search and Fuzzy Finding ✓/✗

**Test**: Verify fuzzy search works

**Steps**:
1. Type "file" in search
2. Type "sys" in search
3. Type "git" in search

**Expected**:
- [ ] List filters to matching servers
- [ ] Fuzzy matching works (e.g., "fs" matches "filesystem")
- [ ] Preview updates as selection changes
- [ ] NO errors during typing

**Actual**: _______________

---

### 7. Header Readability ✓/✗

**Test**: Verify header fits in narrow terminals

**Steps**:
1. Resize terminal to 60 columns wide
2. Launch `mcpi fzf`
3. Check header display

**Expected**:
- [ ] All 4 header lines visible and complete
- [ ] NO truncation ("...Esc:E...")
- [ ] All shortcuts readable:
  - Line 1: "MCPI | Scope: [name]"
  - Line 2: "^S:Chg-Scope ^A:Add ^R:Remove"
  - Line 3: "^E:Enable ^D:Disable"
  - Line 4: "^I/Enter:Info  Esc:Exit"

**Actual**: _______________

---

### 8. Exit and Cancellation ✓/✗

**Test**: Verify clean exit

**Steps**:
1. Press `Esc` to exit
2. Press `Ctrl-C` to cancel

**Expected**:
- [ ] Esc: Clean exit, returns to shell prompt
- [ ] Ctrl-C: Shows "[dim]Cancelled[/dim]", returns to shell
- [ ] NO Python tracebacks
- [ ] NO error messages

**Actual**: _______________

---

## Edge Cases and Error Handling

### 9. Empty Registry ✓/✗

**Test**: Behavior with no servers

**Steps**: (Skip if not easily reproducible)
- [ ] Empty registry shows message: "No servers found in registry"

---

### 10. No Available Scopes ✓/✗

**Test**: Behavior when no scopes configured

**Expected**:
- [ ] Uses default scope: "project-mcp"
- [ ] ctrl-s cycles through detected scopes

---

### 11. Terminal Resize ✓/✗

**Test**: Dynamic resizing

**Steps**:
1. Launch `mcpi fzf`
2. Resize terminal (wider, narrower, taller, shorter)

**Expected**:
- [ ] fzf adjusts layout dynamically
- [ ] Preview pane resizes proportionally
- [ ] NO visual corruption
- [ ] Header remains readable

**Actual**: _______________

---

## Regression Tests

### 12. Backward Compatibility ✓/✗

**Test**: Old tests still pass

**Command**:
```bash
pytest tests/test_tui_fzf.py tests/test_tui_reload.py tests/test_tui_scope_cycling.py -v
```

**Expected**:
- [ ] Core functionality tests pass
- [ ] Some header tests may fail (expected - 3-line → 4-line format change)
- [ ] At least 38/61 tests pass (current baseline)

**Actual**: _______________

---

## Performance Tests

### 13. Large Registry ✓/✗

**Test**: Performance with many servers

**Expected**:
- [ ] List loads in < 1 second
- [ ] Scroll is smooth
- [ ] Search is responsive (< 100ms)

**Actual**: _______________

---

## Summary

**Date Tested**: _______________
**Total Tests**: 13 sections
**Passed**: _____/13
**Failed**: _____/13
**Blocked**: _____/13

**Critical Issues**:
1. _______________
2. _______________
3. _______________

**Non-Critical Issues**:
1. _______________
2. _______________

**Overall Assessment**: PASS / FAIL / NEEDS WORK

**Tester Signature**: _______________
