# Test Gap Documentation

**Last Updated**: 2025-12-12
**Test Suite Stats**: 67 test files | 1,333 tests | ~39,410 lines of test code

This document explicitly states what is **NOT** validated by the test suite to set realistic expectations and guide future test improvements.

---

## Critical Gaps (Known Blind Spots)

### Real Package Installation

| Gap | Impact | Reason |
|-----|--------|--------|
| npm packages never actually installed | Tests can't detect wrong npm commands | All installer tests use `dry_run=True` |
| pip packages never actually installed | Tests can't detect pip failures | All installer tests use `dry_run=True` |
| git clone never actually runs | Tests can't detect clone failures | All installer tests use `dry_run=True` |
| Post-install scripts never run | Install hooks untested | dry_run bypasses execution |

**Evidence**: 147 test files use `dry_run=True`. When `dry_run=True`, installers always return success (returncode=0) without executing any commands.

### Production File Formats

| Gap | Impact | Discovered Via |
|-----|--------|----------------|
| Claude Code installed_plugins.json array format | Bug reached production | User report |
| Cursor globalStorage format variations | Unknown | Not tested |
| VS Code settings format edge cases | Unknown | Not tested |

**The Bug That Exposed This**: `plugin_based.py` assumed dict format, but production uses array format. 1,333 tests passed. Bug still reached production.

### MCP Server Execution

| Gap | Impact |
|-----|--------|
| MCP servers never actually started | Protocol compliance untested |
| MCP handshake never validated | Initialization failures untested |
| Server stdio communication | Protocol errors untested |
| Server crash recovery | Restart logic untested |

### External Tool Integration

| Gap | Impact |
|-----|--------|
| fzf never actually runs | TUI behavior assumed correct |
| Claude CLI never actually runs | Discovery mode uses mocked responses |
| Real file permissions | Permission denied scenarios untested |

---

## What IS Tested (Validated)

These areas have good test coverage with real operations:

- **File I/O operations** - Scope handlers read/write actual files
- **Catalog parsing** - CUE validation against real catalog.json
- **Scope priority** - Multiple scopes, conflict resolution
- **Template YAML parsing** - Real template files loaded
- **CLI argument parsing** - Click integration, option validation
- **Server state transitions** - NOT_INSTALLED -> INSTALLED -> ENABLED -> DISABLED
- **Rescoping** - Moving servers between scopes with file updates
- **Bundle installation logic** - Server grouping and resolution

---

## What Is PARTIALLY Tested

These areas are tested but with mocked external dependencies:

| Area | What's Real | What's Mocked |
|------|-------------|---------------|
| Discovery mode | File operations, cache logic | Claude CLI responses |
| TUI interactions | Data building, selection logic | fzf subprocess |
| Approval workflows | State machine, file writes | User approval responses |
| Bundle resolution | Server lookup, dependency checks | Actual installation |

---

## Error Scenarios NOT Tested

| Scenario | Expected User Experience |
|----------|-------------------------|
| npm not installed | Raw error, no guidance |
| pip not installed | Raw error, no guidance |
| Network timeout during install | Raw error, no retry |
| Disk full during write | Raw error, no cleanup |
| Permission denied on scope file | Raw error, no suggestions |
| Invalid JSON in config file | Varies by code path |
| Catalog server unreachable | Not applicable (local catalog) |

---

## Scale & Performance NOT Tested

| Scenario | Impact |
|----------|--------|
| Catalog with 500+ servers | Unknown load time |
| 100+ installed servers | Unknown list performance |
| Deeply nested scope hierarchies | Unknown resolution time |
| Large plugin directories | Unknown discovery time |
| Concurrent access from multiple clients | Unknown race conditions |

---

## Edge Cases NOT Tested

| Edge Case | Risk |
|-----------|------|
| Server IDs with unicode characters | Display/parsing issues |
| Very long server descriptions | TUI layout breaks |
| Deeply nested env var references | Resolution depth limits |
| Circular template dependencies | Infinite loops |
| Symlinked config files | Path resolution issues |

---

## Test Quality Issues

### Excessive Duplication

Plugin client tests contain significant duplication:
- `test_claude_desktop_plugin.py` - 904 lines
- `test_cursor_plugin.py` - 1002 lines
- `test_vscode_plugin.py` - 1032 lines
- `test_cline_plugin.py` - 957 lines
- `test_windsurf_plugin.py` - 892 lines
- `test_roo_code_plugin.py` - 1272 lines

**Total**: 6,059 lines testing nearly identical base class logic.

### Tests That Pass When They Shouldn't

Any test using `dry_run=True` for installers will pass even if:
- The npm/pip command is wrong
- The package doesn't exist
- The installation would fail in production

---

## Recommendations for Test Authors

1. **Never use production data formats without validation** - Always verify fixtures match real-world formats
2. **Add regression tests for every bug found** - Include the exact conditions that caused the bug
3. **Document what mocks hide** - When mocking, note what real behavior is bypassed
4. **Prefer real operations when feasible** - Use `dry_run=False` for at least some tests
5. **Test error messages, not just success paths** - Users see errors, validate they're helpful

---

## Maintenance

This document should be updated:
- When new gaps are discovered (bugs reaching production)
- When gaps are closed (new tests added)
- During quarterly test audits
- Before major releases
