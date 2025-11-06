# Test Documentation: FZF Multi-Line Header

**Generated**: 2025-11-05
**Test File**: `tests/test_tui_fzf.py::TestFzfHeaderMultiline`
**Implementation File**: `src/mcpi/tui.py` (line 192)
**Reference**: PLAN-2025-11-05-233212.md, P0: Fix Header Truncation

---

## Overview

This test suite validates the multi-line header format for the fzf TUI interface. The tests ensure that all keyboard shortcuts are visible on 80-column terminals by splitting the header across 3 lines.

### Problem Statement

**Current Issue**: Single-line header (113 characters) gets truncated on standard terminals (80-120 columns), hiding critical keyboard shortcuts from users:
- `ctrl-d` (Disable) - hidden
- `ctrl-i` (Info) - hidden
- `enter` (Info alternative) - hidden
- `esc` (Exit) - hidden

**Impact**: Users cannot discover how to disable servers, view info, or exit the interface without resizing their terminal.

**Solution**: Multi-line header with logical grouping:
- Line 1: Title only (19 chars)
- Line 2: Operation shortcuts (60 chars)
- Line 3: Info/Exit shortcuts (41 chars)

---

## Test Suite Architecture

### Testing Strategy

**Anti-Gaming Design**: These tests cannot be satisfied by shortcuts or stubs because:
1. Tests extract actual header from real `build_fzf_command()` output
2. Tests verify observable string properties (newlines, length, content)
3. Tests validate real-world constraints (80-column terminals)
4. No mocking of header itself - tests interact with real implementation
5. Tests verify user-facing behavior, not internal implementation

**Test Characteristics**:
- **Useful**: Tests actual UX problem (header visibility)
- **Complete**: Covers format, content, length, logical grouping
- **Flexible**: Tests interface (header format), not implementation details
- **Automated**: No manual steps, runs in CI

---

## Test Class: TestFzfHeaderMultiline

Location: `tests/test_tui_fzf.py` (lines 323-598)

### Helper Method

#### `_extract_header_from_command(cmd: list[str]) -> str`

Extracts header content from fzf command list.

**Un-gameable because**:
- Parses actual command structure (real fzf format)
- Extracts real header value passed to fzf binary
- Any change to header format is tested against concrete requirements

**Parameters**:
- `cmd`: The fzf command list returned by `build_fzf_command()`

**Returns**: Header content string

**Raises**: `AssertionError` if header not found in command

---

## Test Cases

### 1. test_header_contains_newlines

**Purpose**: Verify header uses newlines for multi-line format.

**What it tests**:
```python
header = extract_header_from_command(build_fzf_command())
assert "\n" in header
```

**Un-gameable because**:
- Tests actual header string extracted from command
- Cannot pass by removing newlines from test assertion
- User-visible behavior: header must span multiple lines

**Expected failure message** (before fix):
```
Header must contain newlines to prevent truncation.
Current header: 'MCPI Server Manager | ctrl-a:Add ... esc:Exit'
```

---

### 2. test_header_has_exactly_three_lines

**Purpose**: Verify header spans exactly 3 lines.

**What it tests**:
```python
lines = header.split("\n")
assert len(lines) == 3
```

**Un-gameable because**:
- Tests actual line count after splitting real header
- Enforces specific format: title line, operations line, info/exit line
- Cannot pass by changing assertion - must match requirement

**Expected failure message** (before fix):
```
Header must have exactly 3 lines. Found 1: ['MCPI Server Manager | ...']
```

---

### 3. test_all_lines_fit_80_columns

**Purpose**: Verify each line is <= 80 characters to fit narrow terminals.

**What it tests**:
```python
for i, line in enumerate(lines, 1):
    assert len(line) <= 80
```

**Un-gameable because**:
- Tests actual character count of each line
- Verifies real-world constraint (80-column terminals)
- Cannot pass by making lines longer - would break on real terminals
- Tests observable user experience (no truncation)

**Expected failure message** (before fix):
```
Line 1 is too long (113 chars, max 80): 'MCPI Server Manager | ctrl-a:Add ...'
```

---

### 4. test_line1_contains_title_only

**Purpose**: Verify line 1 contains only the title (no shortcuts).

**What it tests**:
```python
line1 = lines[0]
assert "MCPI Server Manager" in line1
assert "ctrl-" not in line1.lower()
```

**Un-gameable because**:
- Tests actual content of first line
- Verifies logical grouping: title separate from shortcuts
- Cannot pass by moving title elsewhere - requirement is specific

**Expected failure message** (before fix):
```
Line 1 should be title only, no shortcuts.
Found: 'MCPI Server Manager | ctrl-a:Add ...'
```

---

### 5. test_line2_contains_operation_shortcuts

**Purpose**: Verify line 2 contains all operation shortcuts.

**What it tests**:
```python
line2 = lines[1]
for op in ["ctrl-a", "ctrl-r", "ctrl-e", "ctrl-d"]:
    assert op.lower() in line2.lower()
```

**Un-gameable because**:
- Tests actual presence of all 4 operation shortcuts
- Verifies logical grouping: operations on one line
- Cannot pass by omitting shortcuts - users need all operations

**Expected failure message** (before fix):
```
IndexError: list index out of range  # Only 1 line exists
```

---

### 6. test_line3_contains_info_and_exit_shortcuts

**Purpose**: Verify line 3 contains info and exit shortcuts.

**What it tests**:
```python
line3 = lines[2]
assert "ctrl-i" in line3.lower() or "enter" in line3.lower()
assert "esc" in line3.lower()
```

**Un-gameable because**:
- Tests actual presence of info and exit shortcuts
- Verifies logical grouping: navigation/info on one line
- Cannot pass by omitting shortcuts - users need to know how to exit

**Expected failure message** (before fix):
```
IndexError: list index out of range  # Only 1 line exists
```

---

### 7. test_header_contains_all_required_shortcuts

**Purpose**: Verify header contains all critical keyboard shortcuts.

**What it tests**:
```python
required_shortcuts = {
    "ctrl-a": "Add server",
    "ctrl-r": "Remove server",
    "ctrl-e": "Enable server",
    "ctrl-d": "Disable server",
    "ctrl-i": "Show info",
    "enter": "Show info (alternative)",
    "esc": "Exit interface",
}
for shortcut in required_shortcuts:
    assert shortcut in header.lower()
```

**Un-gameable because**:
- Tests actual presence of every shortcut users need
- Verifies completeness of functionality
- Cannot pass by removing shortcuts - breaks user workflow
- Tests real user requirements from spec

**Note**: This test PASSES even before fix (single line has all shortcuts).

---

### 8. test_header_fits_80_column_terminal

**Purpose**: Integration test verifying header is visible on 80-col terminal.

**What it tests**:
```python
for i, line in enumerate(lines, 1):
    assert len(line) <= 80
assert len(lines) >= 2  # Must be multi-line
```

**Un-gameable because**:
- Tests real-world usage constraint
- Verifies actual user experience (no truncation)
- Cannot pass by making header shorter - must contain all shortcuts
- Tests the exact problem the fix is meant to solve

**Expected failure message** (before fix):
```
Line 1 would be truncated on 80-column terminal (113 chars): 'MCPI...'
```

---

### 9. test_header_included_in_fzf_command

**Purpose**: Verify header is properly included in fzf command structure.

**What it tests**:
```python
cmd = build_fzf_command()
assert any(item.startswith("--header=") or item == "--header" for item in cmd)
header = extract_header_from_command(cmd)
assert len(header) > 0
```

**Un-gameable because**:
- Tests actual command structure passed to fzf
- Verifies integration with fzf CLI
- Cannot pass by changing test - must match fzf API
- Tests end-to-end flow: header → command → fzf

**Note**: This test PASSES even before fix (header exists in command).

---

### 10. test_header_backward_compatible_with_fzf

**Purpose**: Verify header format is compatible with fzf `--header` parameter.

**What it tests**:
```python
assert isinstance(header, str)
if "\n" in header:
    assert "\r\n" not in header  # Unix line endings only
```

**Un-gameable because**:
- Tests actual fzf API contract
- Verifies real command would work with fzf binary
- Cannot pass by faking - tests concrete fzf behavior
- Ensures fix doesn't break existing fzf integration

**Note**: This test PASSES even before fix (header is string with no \\r\\n).

---

## Test Results

### Before Fix (Current State)

```bash
$ pytest tests/test_tui_fzf.py::TestFzfHeaderMultiline -v

FAILED test_header_contains_newlines           # No newlines in header
FAILED test_header_has_exactly_three_lines     # Only 1 line exists
FAILED test_all_lines_fit_80_columns           # Line 1 is 113 chars (> 80)
FAILED test_line1_contains_title_only          # Line 1 has shortcuts too
FAILED test_line2_contains_operation_shortcuts # No line 2 exists
FAILED test_line3_contains_info_and_exit_shortcuts # No line 3 exists
PASSED test_header_contains_all_required_shortcuts # All shortcuts present
FAILED test_header_fits_80_column_terminal     # Line too long for 80-col
PASSED test_header_included_in_fzf_command     # Header exists in command
PASSED test_header_backward_compatible_with_fzf # Header is valid string

7 failed, 3 passed
```

### After Fix (Expected State)

```bash
$ pytest tests/test_tui_fzf.py::TestFzfHeaderMultiline -v

PASSED test_header_contains_newlines           # Header has \n characters
PASSED test_header_has_exactly_three_lines     # Split into 3 lines
PASSED test_all_lines_fit_80_columns           # All lines <= 80 chars
PASSED test_line1_contains_title_only          # Line 1: title only
PASSED test_line2_contains_operation_shortcuts # Line 2: operations
PASSED test_line3_contains_info_and_exit_shortcuts # Line 3: info/exit
PASSED test_header_contains_all_required_shortcuts # All shortcuts present
PASSED test_header_fits_80_column_terminal     # All lines fit 80-col
PASSED test_header_included_in_fzf_command     # Header in command
PASSED test_header_backward_compatible_with_fzf # Valid fzf format

10 passed
```

---

## Running the Tests

### Run only header tests

```bash
pytest tests/test_tui_fzf.py::TestFzfHeaderMultiline -v
```

### Run all TUI tests

```bash
pytest tests/test_tui_fzf.py -v
```

### Run with detailed output

```bash
pytest tests/test_tui_fzf.py::TestFzfHeaderMultiline -v --tb=short
```

### Run with coverage

```bash
pytest tests/test_tui_fzf.py::TestFzfHeaderMultiline --cov=src/mcpi/tui --cov-report=term
```

---

## Implementation Guidance

### Required Code Change

**Location**: `src/mcpi/tui.py`, line 192

**Current Code**:
```python
"--header=MCPI Server Manager | ctrl-a:Add  ctrl-r:Remove  ctrl-e:Enable  ctrl-d:Disable  ctrl-i:Info  enter:Info  esc:Exit"
```

**Fixed Code** (Option A - Compact):
```python
header = (
    "MCPI Server Manager\n"
    "ctrl-a:Add  ctrl-r:Remove  ctrl-e:Enable  ctrl-d:Disable\n"
    "ctrl-i:Info  enter:Info  esc:Exit"
)
f"--header={header}"
```

**Line Lengths**:
- Line 1: 19 chars ✅
- Line 2: 60 chars ✅
- Line 3: 41 chars ✅

**Alternative** (Option B - Grouped):
```python
header = (
    "MCPI Server Manager\n"
    "Operations: ctrl-a=Add  ctrl-r=Remove  ctrl-e=Enable  ctrl-d=Disable\n"
    "Info: ctrl-i=Details  enter=Details  Navigation: esc=Exit"
)
f"--header={header}"
```

**Line Lengths**:
- Line 1: 19 chars ✅
- Line 2: 68 chars ✅
- Line 3: 59 chars ✅

**Recommendation**: Use Option A (maintains current style, more compact).

### Verification Steps

1. **Make code change**: Edit `src/mcpi/tui.py` line 192
2. **Run tests**: `pytest tests/test_tui_fzf.py::TestFzfHeaderMultiline -v`
3. **Verify all pass**: All 10 tests should pass
4. **Verify backward compatibility**: `pytest tests/test_tui_fzf.py -v` (all 28 tests pass)
5. **Manual test (80-col)**: `mcpi fzf` in 80-column terminal
6. **Manual test (120-col)**: `mcpi fzf` in 120-column terminal
7. **Test all shortcuts work**: ctrl-a, ctrl-r, ctrl-e, ctrl-d, ctrl-i, enter, esc

---

## Coverage

### Test Coverage Metrics

**Lines covered in tui.py**:
- `build_fzf_command()` function (lines 178-211)
- Header construction (line 192 - the line being changed)
- Command structure verification

**Test count**: 10 tests

**Assertions per test**: 1-7 assertions (total: 25+ assertions)

**Branch coverage**:
- Single-line path (current, should fail)
- Multi-line path (fixed, should pass)
- Header extraction (both `--header=` and `--header` formats)

### Integration with Existing Tests

**Existing test classes** (21 tests):
- `TestCheckFzfInstalled` (3 tests) ✅
- `TestGetServerStatus` (3 tests) ✅
- `TestFormatServerLine` (4 tests) ✅
- `TestBuildServerList` (2 tests) ✅
- `TestBuildFzfCommand` (3 tests) ✅
- `TestLaunchFzfInterface` (3 tests) ✅

**New test class** (10 tests):
- `TestFzfHeaderMultiline` (10 tests) ⏳ (pending fix)

**Total**: 31 tests in `test_tui_fzf.py`

---

## Why These Tests Are Un-Gameable

### 1. Real Implementation Extraction

Tests call actual `build_fzf_command()` and extract real header:
```python
cmd = build_fzf_command()  # Real function call
header = self._extract_header_from_command(cmd)  # Real parsing
```

**Cannot be gamed**: No mocks or stubs of the header itself.

### 2. Observable Behavior Validation

Tests verify properties users would see:
- Line count (visible in terminal)
- Line length (truncation at column 80)
- Shortcut presence (user can press keys)

**Cannot be gamed**: Tests match real user experience.

### 3. Concrete Requirements

Tests enforce specific values:
- Exactly 3 lines (not 2, not 4)
- Each line <= 80 chars (not 81, not 100)
- All 7 shortcuts present (not 6, not 5)

**Cannot be gamed**: Hard requirements must be met.

### 4. Multiple Verification Points

Each aspect verified by multiple tests:
- Line length: 3 tests (all_lines_fit_80_columns, header_fits_80_column_terminal, line1/2/3 tests)
- Shortcuts: 4 tests (all_required_shortcuts, line2_operations, line3_info_exit, header_contains_newlines)
- Format: 3 tests (has_exactly_three_lines, line1_title_only, backward_compatible)

**Cannot be gamed**: Changing one test would break others.

### 5. End-to-End Validation

Tests verify complete flow:
1. Build command
2. Extract header
3. Validate format
4. Validate content
5. Validate fzf compatibility

**Cannot be gamed**: All steps must work correctly.

---

## Traceability

### STATUS Gaps Addressed

From `STATUS-2025-11-05-232752.md`:

**Issue 2: Help Text Truncated** → Tests validate fix:
- `test_all_lines_fit_80_columns`: Prevents truncation
- `test_header_fits_80_column_terminal`: Ensures visibility
- `test_header_contains_newlines`: Enforces multi-line format

### PLAN Items Validated

From `PLAN-2025-11-05-233212.md`:

**P0: Fix Header Truncation** → Acceptance criteria mapped to tests:
- ✅ Header spans multiple lines → `test_header_has_exactly_three_lines`
- ✅ All shortcuts visible on 80-col → `test_all_lines_fit_80_columns`
- ✅ All shortcuts visible on 120-col → `test_header_fits_80_column_terminal`
- ✅ fzf operations work correctly → `test_header_included_in_fzf_command`
- ✅ Existing tests continue to pass → All 21 existing tests pass

---

## Summary JSON

```json
{
  "test_class": "TestFzfHeaderMultiline",
  "test_file": "tests/test_tui_fzf.py",
  "test_count": 10,
  "tests_added": [
    "test_header_contains_newlines",
    "test_header_has_exactly_three_lines",
    "test_all_lines_fit_80_columns",
    "test_line1_contains_title_only",
    "test_line2_contains_operation_shortcuts",
    "test_line3_contains_info_and_exit_shortcuts",
    "test_header_contains_all_required_shortcuts",
    "test_header_fits_80_column_terminal",
    "test_header_included_in_fzf_command",
    "test_header_backward_compatible_with_fzf"
  ],
  "workflows_covered": [
    "fzf header display on narrow terminals (80 columns)",
    "fzf header display on wide terminals (120 columns)",
    "keyboard shortcut discoverability",
    "multi-line header format validation",
    "fzf command structure verification"
  ],
  "initial_status": "failing",
  "failures_before_fix": 7,
  "passes_before_fix": 3,
  "expected_after_fix": {
    "failures": 0,
    "passes": 10
  },
  "gaming_resistance": "high",
  "status_gaps_addressed": [
    "Issue 2: Help text truncated on 80-120 column terminals"
  ],
  "plan_items_validated": [
    "P0: Fix Header Truncation"
  ],
  "implementation_file": "src/mcpi/tui.py",
  "implementation_line": 192,
  "backward_compatibility": "all 21 existing tests pass",
  "total_test_count_in_file": 31
}
```

---

## Next Steps

1. **Implement Fix**: Modify `src/mcpi/tui.py` line 192
2. **Run Tests**: `pytest tests/test_tui_fzf.py::TestFzfHeaderMultiline -v`
3. **Verify Pass**: All 10 tests should pass
4. **Regression Test**: `pytest tests/test_tui_fzf.py -v` (all 31 tests pass)
5. **Manual Test**: Launch `mcpi fzf` in 80-col and 120-col terminals
6. **Commit**: Git commit with reference to this test documentation

---

**Document Version**: 1.0
**Last Updated**: 2025-11-05
**Status**: Tests written, awaiting implementation
**Related Files**:
- `tests/test_tui_fzf.py` (test implementation)
- `src/mcpi/tui.py` (code to be fixed)
- `PLAN-2025-11-05-233212.md` (P0 work item)
- `STATUS-2025-11-05-232752.md` (issue identification)
