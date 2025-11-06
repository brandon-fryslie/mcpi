# Rescope Command Auto-Detection Evaluation

**Date**: 2025-11-05
**Evaluator**: Claude Code (Ruthlessly Honest Assessment)
**Subject**: Automatic scope detection for `mcpi rescope` command

---

## Executive Summary

**Overall Complexity**: MODERATE (2-4 hours implementation + 1-2 hours testing)
**Risk Level**: LOW (well-defined problem, existing code patterns to follow)
**Recommendation**: APPROVE with caveats (handle multi-scope case properly)

### Critical Finding
The current implementation REQUIRES `--from` parameter. The new requirement would:
1. Auto-detect the source scope containing the server
2. Remove server from ALL scopes where it exists (not just one)
3. Add to target scope only

**Major Design Decision Required**: What happens when server exists in MULTIPLE scopes?
- Option A: Remove from ALL scopes, add to target (RECOMMENDED - clean state)
- Option B: Error and require user to specify --from (CONSERVATIVE - prevents surprises)
- Option C: Interactive prompt asking which scopes to remove from (USER-FRIENDLY but complex)

---

## 1. Current Implementation Analysis

### 1.1 Current Rescope Command (cli.py lines 1231-1423)

**Current Signature**:
```python
@main.command()
@click.argument("server_name", shell_complete=complete_rescope_server_name)
@click.option("--from", "from_scope", required=True, type=DynamicScopeType(), help="Source scope to move from")
@click.option("--to", "to_scope", required=True, type=DynamicScopeType(), help="Destination scope to move to")
@click.option("--client", default=None, shell_complete=complete_client_names, help="MCP client to use (auto-detected if not specified)")
@click.option("--dry-run", is_flag=True, help="Show what would happen without making changes")
def rescope(ctx, server_name, from_scope, to_scope, client, dry_run):
```

**Current Behavior** (lines 1284-1410):
1. Validates `from_scope != to_scope` (line 1296-1300)
2. Gets scope handlers for both scopes (lines 1312-1321)
3. Checks server exists in `from_scope` (lines 1323-1339)
4. Checks server DOESN'T exist in `to_scope` (lines 1341-1350)
5. Reads server config from source (line 1353)
6. Executes transaction:
   - Add to destination (lines 1368-1374)
   - Remove from source with rollback on failure (lines 1376-1396)

**Transaction Safety**: EXCELLENT
- Rollback mechanism exists (lines 1377-1396)
- Atomic operation (add then remove, rollback if remove fails)
- Error messages clear

**State Validation**: PARTIAL
- Only checks ONE scope (`from_scope`)
- Does NOT search for server in other scopes
- Assumes user knows which scope contains server

### 1.2 Helper Methods Available

**MCPManager.find_server_location()** (manager.py lines 313-332):
```python
def find_server_location(self, server_id: str) -> Optional[Dict[str, str]]:
    """Find where a server is located across all clients and scopes.

    Returns:
        Dictionary with client and scope information if found
    """
    all_servers = self.registry.list_all_servers()

    for qualified_id, info in all_servers.items():
        if info.id == server_id:
            return {
                "client": info.client,
                "scope": info.scope,
                "qualified_id": qualified_id,
            }

    return None
```

**LIMITATION**: Returns FIRST match only (not all matches)
**STATUS**: Exists but insufficient for multi-scope detection

**MCPClientPlugin.find_server_scope()** (base.py lines 261-274):
```python
def find_server_scope(self, server_id: str) -> Optional[str]:
    """Find which scope contains a specific server.

    Returns:
        Scope name if found, None otherwise
    """
    for scope_name, handler in self._scopes.items():
        if handler.has_server(server_id):
            return scope_name

    return None
```

**LIMITATION**: Returns FIRST matching scope only
**STATUS**: Exists but insufficient for multi-scope detection

**CRITICAL GAP**: No existing method returns ALL scopes containing a server

### 1.3 Server Listing Infrastructure

**MCPManager.list_servers()** (manager.py lines 114-157):
```python
def list_servers(
    self,
    client_name: Optional[str] = None,
    scope: Optional[str] = None,
    state_filter: Optional[ServerState] = None,
) -> Dict[str, ServerInfo]:
```

**Usage Pattern**:
- Without `scope`: Returns servers from ALL scopes
- With `scope`: Returns servers from ONE scope only

**Current Usage in Rescope** (cli.py lines 1324-1326):
```python
servers_in_source = manager.list_servers(
    client_name=client_name, scope=from_scope
)
```

**Implication**: Current code only checks ONE scope, not all scopes

---

## 2. Gap Analysis: Current vs. Desired State

### 2.1 Current State (As-Built)

**Command Pattern**:
```bash
mcpi rescope my-server --from project-mcp --to user-global
```

**User Mental Model**:
- "I know my server is in project-mcp"
- "I want to move it to user-global"
- "I explicitly specify both scopes"

**Failure Modes**:
- User specifies wrong --from scope → Error "server not found"
- Server exists in multiple scopes → Only moves from specified scope
- User doesn't know which scope → Must run `mcpi list` first

### 2.2 Desired State (Requirement)

**Command Pattern**:
```bash
mcpi rescope my-server --to user-global
# Auto-detects that my-server is in project-mcp (or wherever)
```

**User Mental Model**:
- "I have a server named my-server somewhere"
- "I want it in user-global"
- "System figures out where it currently is"

**Expected Behaviors**:
1. **Single Scope Case** (most common):
   - Server exists in ONE scope only
   - Auto-detect that scope
   - Remove from detected scope, add to target

2. **Multiple Scope Case** (edge case):
   - Server exists in MULTIPLE scopes
   - **DECISION REQUIRED**: What to do?
     - A) Remove from ALL scopes, add to target (CLEAN)
     - B) Error with message listing all scopes (SAFE)
     - C) Interactive prompt (USER-FRIENDLY)

3. **No Scope Case** (error):
   - Server doesn't exist anywhere
   - Error: "Server 'my-server' not found"

### 2.3 Behavioral Changes

| Scenario | Current Behavior | New Behavior | Breaking Change? |
|----------|------------------|--------------|------------------|
| Server in 1 scope, --from correct | Moves server | Same | NO |
| Server in 1 scope, --from wrong | Error | N/A (no --from) | YES (but better UX) |
| Server in 1 scope, no --from | Error (required) | Auto-detects, moves | YES (new capability) |
| Server in 2+ scopes, --from specified | Moves from specified only | N/A (no --from) | YES |
| Server in 2+ scopes, no --from | Error (required) | Remove from ALL or Error | YES (needs decision) |
| Server nowhere | Error | Error (same message) | NO |

**BACKWARD COMPATIBILITY**: BREAKING
- `--from` changes from `required=True` to `required=False`
- Existing scripts using `--from` will still work (optional parameter)
- Users who rely on explicit scope control may be surprised

---

## 3. Technical Implementation Plan

### 3.1 New Helper Method (MCPManager)

**Add to manager.py** (after line 332):
```python
def find_all_server_scopes(
    self, server_id: str, client_name: Optional[str] = None
) -> List[Dict[str, str]]:
    """Find ALL scopes containing a specific server.

    Args:
        server_id: Server identifier
        client_name: Optional client name (uses default if not specified)

    Returns:
        List of dicts with {client, scope, qualified_id} for each match
    """
    # Use default client if none specified
    if client_name is None:
        client_name = self._default_client

    if not client_name or not self.registry.has_client(client_name):
        return []

    try:
        client = self.registry.get_client(client_name)
        servers = client.list_servers()  # All scopes

        matches = []
        for qualified_id, info in servers.items():
            if info.id == server_id:
                matches.append({
                    "client": info.client,
                    "scope": info.scope,
                    "qualified_id": qualified_id,
                })

        return matches
    except Exception as e:
        logger.error(f"Error finding server scopes: {e}")
        return []
```

**Complexity**: LOW (10 lines, follows existing patterns)
**Testing**: 3 test cases (0 scopes, 1 scope, 2+ scopes)

### 3.2 Modified Rescope Command (cli.py)

**Change 1: Make --from optional**:
```python
@click.option(
    "--from",
    "from_scope",
    required=False,  # CHANGED from True
    type=DynamicScopeType(),
    help="Source scope to move from (auto-detected if not specified)",
)
```

**Change 2: Auto-detection logic** (insert after line 1300):
```python
# Step 2.5: Auto-detect source scope if not specified
if not from_scope:
    # Find all scopes containing the server
    matching_scopes = manager.find_all_server_scopes(server_name, client_name)

    if not matching_scopes:
        console.print(
            f"[red]Error: Server '{server_name}' not found in any scope[/red]"
        )
        ctx.exit(1)

    # DECISION POINT: How to handle multiple scopes?
    # OPTION A: Remove from all scopes
    if len(matching_scopes) > 1:
        console.print(
            f"[yellow]Warning: Server '{server_name}' found in {len(matching_scopes)} scopes:[/yellow]"
        )
        for match in matching_scopes:
            console.print(f"  - {match['scope']}")
        console.print(f"[yellow]Will remove from ALL scopes and add to '{to_scope}'[/yellow]")

        if not ctx.obj.get("dry_run", False):
            # Prompt for confirmation
            from rich.prompt import Confirm
            if not Confirm.ask("Continue?", default=False):
                console.print("[yellow]Cancelled[/yellow]")
                ctx.exit(0)

    # Single scope case (most common)
    from_scopes = [m['scope'] for m in matching_scopes]
else:
    # Explicit --from provided (backward compatibility)
    from_scopes = [from_scope]
```

**Change 3: Multi-scope removal loop** (replace lines 1323-1396):
```python
# Step 5-9: Execute rescope for each source scope
for source_scope in from_scopes:
    # Check server exists in this scope
    servers_in_source = manager.list_servers(
        client_name=client_name, scope=source_scope
    )

    source_server_info = None
    for qualified_id, server_info in servers_in_source.items():
        if server_info.id == server_name:
            source_server_info = server_info
            break

    if source_server_info is None:
        # Should never happen (we just found it)
        console.print(
            f"[red]Error: Server '{server_name}' not found in scope '{source_scope}'[/red]"
        )
        continue

    # Get scope handlers
    source_handler = client_plugin.get_scope_handler(source_scope)
    dest_handler = client_plugin.get_scope_handler(to_scope)

    # Get server config
    server_config = ServerConfig.from_dict(source_server_info.config)

    # Dry-run mode
    if ctx.obj.get("dry_run", False):
        console.print(
            f"[cyan]Would remove '{server_name}' from '{source_scope}'[/cyan]"
        )
        continue

    # Remove from source
    try:
        remove_result = source_handler.remove_server(server_name)
        if not remove_result.success:
            console.print(
                f"[red]Warning: Failed to remove from '{source_scope}': {remove_result.message}[/red]"
            )
    except Exception as e:
        console.print(
            f"[red]Error removing from '{source_scope}': {str(e)}[/red]"
        )

# Add to destination ONCE (after all removals)
if not ctx.obj.get("dry_run", False):
    try:
        # Check destination doesn't already have it
        servers_in_dest = manager.list_servers(client_name=client_name, scope=to_scope)
        for qualified_id, server_info in servers_in_dest.items():
            if server_info.id == server_name:
                console.print(
                    f"[yellow]Server '{server_name}' already exists in '{to_scope}'[/yellow]"
                )
                ctx.exit(0)

        # Add to destination
        add_result = dest_handler.add_server(server_name, server_config)
        if not add_result.success:
            console.print(
                f"[red]Error: Failed to add to '{to_scope}': {add_result.message}[/red]"
            )
            ctx.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        ctx.exit(1)

# Success output
console.print(f"[green]✓[/green] Successfully rescoped server '{server_name}'")
if len(from_scopes) == 1:
    console.print(f"  From: {from_scopes[0]}")
else:
    console.print(f"  Removed from: {', '.join(from_scopes)}")
console.print(f"  To: {to_scope}")
console.print(f"  Client: {client_name}")
```

**Complexity**: MODERATE (50 lines, careful transaction handling needed)

### 3.3 Alternative: OPTION B - Error on Multiple Scopes

**Simpler Implementation** (less risky):
```python
if not from_scope:
    matching_scopes = manager.find_all_server_scopes(server_name, client_name)

    if not matching_scopes:
        console.print(
            f"[red]Error: Server '{server_name}' not found in any scope[/red]"
        )
        ctx.exit(1)

    if len(matching_scopes) > 1:
        console.print(
            f"[red]Error: Server '{server_name}' exists in multiple scopes:[/red]"
        )
        for match in matching_scopes:
            console.print(f"  - {match['scope']}")
        console.print(
            "[yellow]Please specify --from to indicate which scope to move from[/yellow]"
        )
        ctx.exit(1)

    # Single scope - auto-detected
    from_scope = matching_scopes[0]['scope']
    console.print(f"[dim]Auto-detected source scope: {from_scope}[/dim]")

# Continue with existing single-scope logic (lines 1302-1410)
```

**Complexity**: LOW (15 lines, minimal change to existing code)
**Safety**: HIGH (conservative, no surprises)
**UX**: MODERATE (user must specify --from for multi-scope case)

---

## 4. Test Coverage Analysis

### 4.1 Existing Tests (test_cli_rescope.py)

**Coverage**: EXCELLENT
- 34 test cases covering all aspects
- Transaction safety validated
- Error handling tested
- Configuration preservation verified
- Dry-run mode tested
- Edge cases covered

**Tests to Modify** (if implementing):
1. **test_rescope_server_not_in_source** (line 229): Update error message check
2. **test_rescope_invalid_source_scope** (line 308): Make conditional on --from
3. Add new tests for auto-detection

**Tests to Add**:
1. `test_rescope_auto_detect_single_scope` - Server in 1 scope, no --from
2. `test_rescope_auto_detect_multiple_scopes` - Server in 2+ scopes, behavior depends on option
3. `test_rescope_auto_detect_not_found` - Server not found anywhere
4. `test_rescope_backward_compat_explicit_from` - Ensure --from still works

### 4.2 Test Implementation Effort

**New Tests**: 4 test cases
**Modified Tests**: 2 test cases
**Estimated Time**: 1-2 hours (includes implementation and verification)

---

## 5. Files Requiring Modification

### 5.1 Core Implementation

| File | Lines Changed | Type | Complexity |
|------|---------------|------|------------|
| `src/mcpi/clients/manager.py` | +20 | New method | LOW |
| `src/mcpi/cli.py` | +30-80 | Modified command | MODERATE |
| **Total** | **50-100** | **2 files** | **LOW-MODERATE** |

### 5.2 Tests

| File | Lines Changed | Type | Complexity |
|------|---------------|------|------------|
| `tests/test_cli_rescope.py` | +80-120 | New tests | LOW |
| **Total** | **80-120** | **1 file** | **LOW** |

### 5.3 Documentation

| File | Lines Changed | Type | Complexity |
|------|---------------|------|------------|
| `CLAUDE.md` | +5-10 | Command example | LOW |
| `README.md` | +5-10 | Command example | LOW |
| **Total** | **10-20** | **2 files** | **LOW** |

**Grand Total**: 140-240 lines across 5 files

---

## 6. Risk Assessment

### 6.1 Technical Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| **Multi-scope edge case** | MEDIUM | LOW | Clear error message or user confirmation |
| **Transaction rollback failure** | MEDIUM | VERY LOW | Existing rollback logic is tested |
| **Backward compatibility break** | LOW | NONE | --from still works (optional) |
| **Performance degradation** | LOW | VERY LOW | list_servers() already called |
| **Test coverage gaps** | LOW | LOW | Add comprehensive auto-detect tests |

### 6.2 User Experience Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| **Unexpected multi-scope removal** | HIGH | LOW | Confirmation prompt or error |
| **Confusion about auto-detection** | LOW | MEDIUM | Clear console output showing detected scope |
| **Loss of explicit control** | MEDIUM | LOW | Keep --from optional (power users can still specify) |

### 6.3 Quality Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| **Inadequate testing** | MEDIUM | LOW | Add 4+ new test cases |
| **Regression in existing tests** | LOW | VERY LOW | All existing tests should still pass |
| **Documentation gap** | LOW | MEDIUM | Update docs with examples |

---

## 7. Backward Compatibility Analysis

### 7.1 Breaking Changes

**NONE** - This is a backward-compatible enhancement:
- `--from` remains a valid option (changes from required to optional)
- Existing scripts using `--from` will continue to work
- No changes to command output format
- No changes to error codes

### 7.2 Behavioral Changes

**Visible to Users**:
1. `--from` now optional (less typing for common case)
2. Auto-detection messages appear in output
3. Multi-scope case may prompt for confirmation (if OPTION A)

**Not Visible to Users**:
- Internal scope detection logic
- Manager method additions

### 7.3 Migration Path

**For Users**:
- No migration needed
- Existing commands continue to work
- Can start using new syntax immediately

**For Scripts**:
- No changes required
- Can simplify scripts by removing `--from` in single-scope cases

---

## 8. Recommendations

### 8.1 Implementation Approach

**RECOMMEND: OPTION B - Error on Multi-Scope (Conservative)**

**Rationale**:
1. **Lowest Risk**: Minimal code changes, clear error message
2. **Prevents Surprises**: User explicitly controls multi-scope behavior
3. **Fastest Implementation**: 2-3 hours vs. 4-6 hours for OPTION A
4. **Best UX for 95% Case**: Auto-detects single scope (most common)
5. **Safe Fallback**: Multi-scope case requires explicit --from (rare)

**Alternative: OPTION A - Remove from All (Aggressive)**
- Better UX for power users
- More complex implementation
- Requires confirmation prompt
- Higher risk of user surprise

### 8.2 Phased Rollout

**Phase 1: Core Implementation** (2-3 hours)
1. Add `find_all_server_scopes()` to manager.py
2. Make `--from` optional in cli.py
3. Add auto-detection logic (OPTION B)
4. Update error messages

**Phase 2: Testing** (1-2 hours)
1. Add 4 new test cases
2. Modify 2 existing test cases
3. Run full test suite
4. Manual testing of edge cases

**Phase 3: Documentation** (30 min)
1. Update CLAUDE.md with new command syntax
2. Update README.md with examples
3. Add note about multi-scope behavior

**Total Estimated Time**: 3.5-5.5 hours

### 8.3 Success Criteria

**Must Have**:
- [ ] Auto-detects source scope when server in ONE scope
- [ ] Clear error when server not found
- [ ] Clear error (or prompt) when server in MULTIPLE scopes
- [ ] `--from` still works (backward compatibility)
- [ ] All existing tests pass
- [ ] 4 new tests added and passing
- [ ] Documentation updated

**Should Have**:
- [ ] Dry-run mode shows detected scope
- [ ] Console output indicates auto-detection occurred
- [ ] Help text updated

**Nice to Have**:
- [ ] Interactive mode for multi-scope case (OPTION A)
- [ ] `--all-scopes` flag to explicitly remove from all

---

## 9. Concerns and Open Questions

### 9.1 Critical Questions

**Q1: What is the expected behavior for multi-scope case?**
- Current answer: OPTION B (error with message)
- Alternative: OPTION A (remove from all with confirmation)
- Alternative: OPTION C (interactive selection)

**Q2: Should --from remain available for power users?**
- Recommendation: YES (optional, for explicit control)

**Q3: Should we show detected scope in output?**
- Recommendation: YES (transparency, debugging)

**Q4: What about servers with same name in different clients?**
- Current: `--client` parameter handles this
- Auto-detection respects client parameter

### 9.2 Future Enhancements

**Out of Scope for Initial Implementation**:
1. `--all-scopes` flag to remove from all scopes explicitly
2. `--interactive` mode for multi-scope selection
3. `--show-scopes` to preview where server exists before rescoping
4. Transaction log for complex multi-scope operations

---

## 10. Conclusion

### 10.1 Summary

**Recommendation**: APPROVE with OPTION B implementation

**Complexity**: MODERATE (2-4 hours implementation, 1-2 hours testing)

**Risk**: LOW (conservative approach, backward compatible)

**Value**: HIGH (better UX for 95% of users, no downside for power users)

### 10.2 Decision Required

**Before proceeding, need user decision on**:
- [ ] Accept OPTION B (error on multi-scope) - RECOMMENDED
- [ ] Or implement OPTION A (remove from all) - More complex
- [ ] Or defer this feature - Not recommended (low risk, high value)

### 10.3 Next Steps

**If Approved**:
1. Confirm OPTION B vs. OPTION A with user
2. Implement `find_all_server_scopes()` method
3. Modify rescope command with auto-detection
4. Add test coverage
5. Update documentation
6. Manual testing
7. Create PR with detailed description

**Estimated Delivery**: Same day (3.5-5.5 hours total)

---

## Appendix A: Code Snippets

### A.1 find_all_server_scopes() Implementation

```python
def find_all_server_scopes(
    self, server_id: str, client_name: Optional[str] = None
) -> List[Dict[str, str]]:
    """Find ALL scopes containing a specific server.

    Unlike find_server_location() which returns first match,
    this returns all matches for handling multi-scope scenarios.

    Args:
        server_id: Server identifier to search for
        client_name: Optional client name (uses default if not specified)

    Returns:
        List of dicts, each with {client, scope, qualified_id}
        Empty list if server not found

    Example:
        >>> manager.find_all_server_scopes("my-server")
        [
            {"client": "claude-code", "scope": "project-mcp", "qualified_id": "..."},
            {"client": "claude-code", "scope": "user-global", "qualified_id": "..."}
        ]
    """
    # Use default client if none specified
    if client_name is None:
        client_name = self._default_client

    if not client_name or not self.registry.has_client(client_name):
        logger.warning(f"No valid client available for finding server scopes")
        return []

    try:
        client = self.registry.get_client(client_name)
        servers = client.list_servers()  # Gets all servers from all scopes

        matches = []
        for qualified_id, info in servers.items():
            if info.id == server_id:
                matches.append({
                    "client": info.client,
                    "scope": info.scope,
                    "qualified_id": qualified_id,
                })

        logger.debug(f"Found {len(matches)} scope(s) containing server '{server_id}'")
        return matches
    except Exception as e:
        logger.error(f"Error finding server scopes for '{server_id}': {e}")
        return []
```

### A.2 Auto-Detection Logic (OPTION B)

```python
# Step 2.5: Auto-detect source scope if not specified
source_scopes = []

if not from_scope:
    # Find all scopes containing the server
    matching_scopes = manager.find_all_server_scopes(server_name, client_name)

    if not matching_scopes:
        console.print(
            f"[red]Error: Server '{server_name}' not found in any scope for client '{client_name}'[/red]"
        )
        console.print("[dim]Tip: Run 'mcpi list' to see all installed servers[/dim]")
        ctx.exit(1)

    if len(matching_scopes) == 1:
        # Common case: server in exactly one scope
        from_scope = matching_scopes[0]['scope']
        console.print(f"[dim]Auto-detected source scope: {from_scope}[/dim]")
        source_scopes = [from_scope]
    else:
        # Edge case: server in multiple scopes
        console.print(
            f"[red]Error: Server '{server_name}' exists in {len(matching_scopes)} scopes:[/red]"
        )
        for i, match in enumerate(matching_scopes, 1):
            console.print(f"  {i}. {match['scope']}")
        console.print(
            "\n[yellow]Please specify which scope to move from using --from:[/yellow]"
        )
        console.print(f"  mcpi rescope {server_name} --from <scope> --to {to_scope}")
        ctx.exit(1)
else:
    # Explicit --from provided (backward compatibility path)
    source_scopes = [from_scope]

# Rest of rescope logic continues with from_scope variable...
```

---

**END OF EVALUATION**
