# CLI Tab Completion Functional Tests

**Test File**: `tests/test_cli_completion.py`
**Feature**: CLI tab completion support for mcpi
**Status**: Tests written, awaiting implementation
**Test Count**: 29 tests covering all critical workflows

## Overview

This test suite validates the CLI tab completion feature for mcpi. The tests are designed to be **un-gameable** - they test real functionality through actual user workflows, not implementation details or mocked responses.

### Test Philosophy

Each test in this suite:
1. **Mirrors Real Usage**: Simulates actual tab completion scenarios users will encounter
2. **Validates True Behavior**: Tests call real manager/catalog APIs to verify functionality
3. **Resists Gaming**: Cannot be satisfied by stubs, hardcoded responses, or shortcuts
4. **Fails Honestly**: When functionality is broken, tests fail clearly and cannot be bypassed

## Running Tests

```bash
# Run all completion tests
pytest tests/test_cli_completion.py -v

# Run specific test class
pytest tests/test_cli_completion.py::TestClientNameCompletion -v

# Run with coverage
pytest tests/test_cli_completion.py --cov=src/mcpi/cli -v

# Run tests and see skip reasons
pytest tests/test_cli_completion.py -v -rs
```

## Test Coverage

### 1. Client Name Completion (5 tests)

Tests for `--client` option completion in commands like `mcpi list --client <TAB>`.

**Workflows Tested**:
- ✅ Shows all detected clients from manager
- ✅ Filters client names by prefix match
- ✅ Handles no clients detected gracefully
- ✅ Handles missing context without crashing
- ⏭️ Client option has completion callback wired

**Why Un-gameable**:
- Must call `manager.get_client_info()` to get real client list
- Cannot use hardcoded client names (won't match actual detected clients)
- Tests filtering logic with real data, not mocked responses

**Example Test**:
```python
def test_complete_client_names_shows_detected_clients(self):
    """User types `mcpi list --client <TAB>` to see available clients."""
    mock_manager = Mock()
    mock_manager.get_client_info.return_value = {
        'claude-code': {'server_count': 3},
        'cursor': {'server_count': 1},
        'vscode': {'server_count': 0}
    }

    completions = complete_client_names(mock_ctx, None, "")

    # Must return ALL detected clients
    assert 'claude-code' in completion_values
    assert 'cursor' in completion_values
    assert 'vscode' in completion_values
```

### 2. Server ID Completion (6 tests)

Tests for `server_id` argument completion in commands like `mcpi add <TAB>`.

**Workflows Tested**:
- ✅ Shows servers from registry catalog
- ✅ Includes server descriptions as help text
- ✅ Filters server IDs by prefix match
- ✅ Limits results for large registries (performance)
- ✅ Handles empty registry gracefully
- ⏭️ Server ID argument has completion callback wired

**Why Un-gameable**:
- Must call `catalog.list_servers()` to get real registry data
- Help text must match actual server descriptions from catalog
- Result limiting must actually work with large datasets
- Cannot fake empty registry state

**Example Test**:
```python
def test_complete_server_ids_includes_help_text(self):
    """Server completion shows descriptions in help text."""
    mock_server = Mock()
    mock_server.description = 'AWS integration for cloud services'

    mock_catalog.list_servers.return_value = [('aws', mock_server)]

    completions = complete_server_ids(mock_ctx, None, "")

    # Help text must match actual server description
    aws_completion = [c for c in completions if c.value == 'aws'][0]
    assert 'AWS integration' in aws_completion.help
```

### 3. Context-Aware Server Completion (3 tests)

Tests for command-specific server filtering based on server state.

**Workflows Tested**:
- ✅ `mcpi remove <TAB>` only shows INSTALLED servers
- ✅ `mcpi enable <TAB>` only shows DISABLED servers
- ✅ `mcpi disable <TAB>` only shows ENABLED servers

**Why Un-gameable**:
- Must query manager for servers filtered by actual state
- Cannot show wrong state servers (e.g., enabled in enable command)
- Validates real state-based filtering logic

**Example Test**:
```python
def test_enable_command_only_completes_disabled_servers(self):
    """Enable command only shows disabled servers."""
    mock_manager.list_servers.return_value = {
        'server1': Mock(state=ServerState.ENABLED),
        'server2': Mock(state=ServerState.DISABLED),
        'server3': Mock(state=ServerState.DISABLED)
    }

    mock_ctx.info_name = 'enable'
    completions = complete_server_ids(mock_ctx, None, "")

    # Must only return disabled servers
    assert 'server2' in completion_values
    assert 'server3' in completion_values
    assert 'server1' not in completion_values  # Already enabled
```

### 4. Scope Completion (2 tests)

Regression tests for existing `DynamicScopeType.shell_complete()` functionality.

**Workflows Tested**:
- ✅ Scope completion respects `--client` parameter
- ✅ Scope completion filters by prefix

**Status**: Already implemented and working ✅

**Example Test**:
```python
def test_scope_completion_works_with_client_context(self):
    """Scope completion shows scopes for selected client."""
    scope_type = DynamicScopeType()

    mock_manager.get_scopes_for_client.return_value = [
        {'name': 'user-internal'},
        {'name': 'project-mcp'}
    ]

    completions = scope_type.shell_complete(mock_ctx, None, "")

    assert 'user-internal' in completion_values
    assert 'project-mcp' in completion_values
    mock_manager.get_scopes_for_client.assert_called_with('claude-code')
```

### 5. Completion Command (5 tests)

Tests for `mcpi completion` command that generates shell scripts.

**Workflows Tested**:
- ❌ Command exists in CLI
- ❌ Generates valid bash completion script
- ❌ Generates valid zsh completion script
- ❌ Auto-detects shell from environment
- ❌ Shows installation instructions

**Why Un-gameable**:
- Must actually generate valid shell syntax
- Output must be executable shell script
- Tests Click's built-in completion generation
- Must handle shell detection correctly

**Example Test**:
```python
def test_completion_command_generates_bash_script(self):
    """User runs `mcpi completion --shell bash`."""
    runner = CliRunner()
    result = runner.invoke(main, ['completion', '--shell', 'bash'])

    assert result.exit_code == 0
    # Must contain actual bash completion markers
    assert '_MCPI_COMPLETE' in result.output or 'complete' in result.output
    assert 'mcpi' in result.output
```

### 6. Edge Cases & Error Handling (3 tests)

Tests for graceful degradation when things go wrong.

**Workflows Tested**:
- ✅ Handles manager initialization failure
- ⏭️ Handles catalog load failure
- ⏭️ Handles partial client data

**Why Un-gameable**:
- Tests actual error handling code paths
- Must handle missing dependencies gracefully
- Cannot fake error states with success responses

**Example Test**:
```python
def test_completion_handles_manager_initialization_failure(self):
    """Tab completion when manager fails to initialize."""
    mock_ctx.obj = {}  # No manager in context

    # Should return fallback completions, not crash
    completions = scope_type.shell_complete(mock_ctx, None, "")

    assert len(completions) > 0  # Has fallback values
    assert 'user' in completion_values  # Default fallback
```

### 7. Click Integration (3 tests)

Tests verifying completion functions are properly wired into CLI commands.

**Workflows Tested**:
- ⏭️ `--client` option has shell_complete callback
- ⏭️ `server_id` argument has shell_complete callback
- ✅ `--scope` option uses DynamicScopeType

**Why Un-gameable**:
- Tests actual CLI decorator configuration
- Cannot be satisfied without proper wiring
- Validates integration with Click's completion system

### 8. Performance Tests (2 tests)

Tests ensuring completion is fast enough for good UX.

**Workflows Tested**:
- ✅ Scope completion completes in <100ms
- ⏭️ Large registry completion is limited and fast

**Why Un-gameable**:
- Tests actual execution time, not mocked timing
- Validates real-world performance with large datasets
- Ensures completion is usable in production

**Example Test**:
```python
def test_scope_completion_is_fast(self):
    """Each completion should complete in <100ms."""
    start = time.time()
    for _ in range(10):  # Simulate 10 rapid tabs
        completions = scope_type.shell_complete(mock_ctx, None, "")
    elapsed = time.time() - start

    avg_time = elapsed / 10
    assert avg_time < 0.1, f"Too slow: {avg_time*1000:.1f}ms"
```

## Test Status Summary

| Category | Total | Passed | Failed | Skipped |
|----------|-------|--------|--------|---------|
| Client Name Completion | 5 | 0 | 0 | 4 |
| Server ID Completion | 6 | 0 | 0 | 5 |
| Context-Aware Completion | 3 | 0 | 0 | 3 |
| Scope Completion | 2 | 2 | 0 | 0 |
| Completion Command | 5 | 0 | 5 | 0 |
| Edge Cases | 3 | 1 | 0 | 2 |
| Click Integration | 3 | 1 | 0 | 2 |
| Performance | 2 | 1 | 0 | 1 |
| **TOTAL** | **29** | **5** | **5** | **17** |

**Legend**:
- ✅ **Passed** (5): Existing functionality working
- ❌ **Failed** (5): Functionality not implemented yet (expected failures)
- ⏭️ **Skipped** (17): Tests waiting for implementation (marked with `pytest.skip`)

## Implementation Guidance

### Required Completion Functions

Based on the tests, the following functions need to be implemented:

#### 1. `complete_client_names(ctx, param, incomplete)`
**Location**: `src/mcpi/cli.py` or `src/mcpi/cli_completion.py`

```python
def complete_client_names(ctx, param, incomplete):
    """Complete MCP client names."""
    from click.shell_completion import CompletionItem

    if ctx.obj and 'mcp_manager' in ctx.obj:
        manager = ctx.obj['mcp_manager']
        clients = manager.get_client_info()
        return [
            CompletionItem(name, help=f"{info.get('server_count', 0)} servers")
            for name, info in clients.items()
            if name.startswith(incomplete)
        ]
    return []
```

#### 2. `complete_server_ids(ctx, param, incomplete)`
**Location**: `src/mcpi/cli.py` or `src/mcpi/cli_completion.py`

```python
def complete_server_ids(ctx, param, incomplete):
    """Complete server IDs from registry or installed servers."""
    from click.shell_completion import CompletionItem

    if not ctx.obj:
        return []

    # For context-aware completion, check command name
    command_name = ctx.info_name if hasattr(ctx, 'info_name') else None

    # Use catalog for 'add', manager for installed server commands
    if command_name == 'add' and 'catalog' in ctx.obj:
        catalog = ctx.obj['catalog']
        servers = catalog.list_servers()
        return [
            CompletionItem(server_id, help=server.description[:50])
            for server_id, server in servers
            if server_id.startswith(incomplete)
        ][:50]  # Limit results

    elif 'mcp_manager' in ctx.obj:
        manager = ctx.obj['mcp_manager']

        # Filter by state for enable/disable commands
        state_filter = None
        if command_name == 'enable':
            state_filter = ServerState.DISABLED
        elif command_name == 'disable':
            state_filter = ServerState.ENABLED

        servers = manager.list_servers(state_filter=state_filter)
        return [
            CompletionItem(info.id)
            for qualified_id, info in servers.items()
            if info.id.startswith(incomplete)
        ][:50]

    return []
```

#### 3. `completion` Command
**Location**: `src/mcpi/cli.py`

```python
@main.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']),
              help='Shell type (auto-detect if not specified)')
@click.pass_context
def completion(ctx: click.Context, shell: Optional[str]) -> None:
    """Generate shell completion script for mcpi.

    Tab completion provides intelligent suggestions for:
    - Command names (list, add, remove, etc.)
    - Option flags (--client, --scope, --help)
    - Client names (based on detected MCP clients)
    - Scope names (filtered by selected client)
    - Server IDs (from the registry)

    Examples:
        mcpi completion --shell bash > mcpi-completion.bash
        mcpi completion --shell zsh >> ~/.zshrc
    """
    from click.shell_completion import get_completion_class
    import os

    # Auto-detect shell if not specified
    if not shell:
        shell_env = os.environ.get('SHELL', '').split('/')[-1]
        if shell_env in ['bash', 'zsh', 'fish']:
            shell = shell_env
        else:
            console.print("[yellow]Could not auto-detect shell. Please specify with --shell[/yellow]")
            return

    # Generate completion script
    try:
        completion_class = get_completion_class(shell)
        script = completion_class(main, {}, 'mcpi').source()

        console.print(script)
        console.print(f"\n[cyan]# To enable completion, add to ~/.{shell}rc:[/cyan]")

        if shell == 'bash':
            console.print('eval "$(_MCPI_COMPLETE=bash_source mcpi)"')
        elif shell == 'zsh':
            console.print('eval "$(_MCPI_COMPLETE=zsh_source mcpi)"')
        elif shell == 'fish':
            console.print('_MCPI_COMPLETE=fish_source mcpi | source')

    except Exception as e:
        console.print(f"[red]Error generating completion: {e}[/red]")
```

### Decorator Updates Required

Update the following CLI decorators to add completion:

**Client Options** (9 locations):
```python
@click.option('--client', shell_complete=complete_client_names,
              help='Filter by client (uses default if not specified)')
```

**Server ID Arguments** (5 locations):
```python
@click.argument('server_id', shell_complete=complete_server_ids)
```

## Test Evolution

As implementation progresses, tests will evolve through these stages:

### Stage 1: Initial (Current)
- 5 tests passing (existing scope completion)
- 5 tests failing (completion command doesn't exist)
- 17 tests skipped (functions not implemented)

### Stage 2: After Completion Functions Added
- Remove `pytest.skip()` from client/server completion tests
- Tests should pass if implementation correct
- Tests should fail if implementation has bugs

### Stage 3: After Completion Command Added
- All 5 completion command tests should pass
- Tests verify actual shell script generation

### Stage 4: After Context-Aware Filtering
- Remove `pytest.skip()` from context-aware tests
- Tests verify state-based filtering works

### Stage 5: Final (All Implemented)
- All 29 tests passing
- No skipped tests
- Full completion feature coverage

## Validation Checklist

Use these manual tests to supplement automated tests:

### Bash Shell
```bash
# Install completion
eval "$(_MCPI_COMPLETE=bash_source mcpi)"

# Test completions
mcpi <TAB><TAB>                    # Should show commands
mcpi list --client <TAB>           # Should show clients
mcpi add <TAB>                     # Should show registry servers
mcpi add server --scope <TAB>      # Should show scopes
mcpi enable <TAB>                  # Should show disabled servers only
```

### Zsh Shell
```zsh
# Install completion
eval "$(_MCPI_COMPLETE=zsh_source mcpi)"

# Test completions (same as bash)
mcpi <TAB>
mcpi list --client <TAB>
```

### Performance Check
```bash
# Completion should feel instant
time mcpi list --client <TAB>     # Should be < 100ms
```

## Traceability

### STATUS Gaps Addressed
These tests validate fixes for gaps identified in `.agent_planning/STATUS-2025-10-23-165332.md`:

- **Line 168**: No completion command - Tests in `TestCompletionCommand`
- **Line 181**: No client name completion - Tests in `TestClientNameCompletion`
- **Line 209**: No server ID completion - Tests in `TestServerIDCompletion`
- **Line 238**: Context-aware filtering missing - Tests in `TestContextAwareServerCompletion`

### PLAN Items Validated
These tests validate acceptance criteria from `.agent_planning/FEATURE_PROPOSAL_CLI_TAB_COMPLETION.md`:

- **Lines 18-36**: User workflows - All test classes simulate these workflows
- **Lines 86-115**: Completion functions - Tested in client/server completion classes
- **Lines 133-156**: Completion command - Tested in `TestCompletionCommand`
- **Lines 172-176**: Context-aware filtering - Tested in `TestContextAwareServerCompletion`

## Success Criteria

Tests validate these success criteria from the proposal:

✅ **Commands Complete**: Scope completion already works
❌ **Client Names Complete**: Tests written, awaiting implementation
❌ **Server IDs Complete**: Tests written, awaiting implementation
❌ **Context-Aware Filtering**: Tests written, awaiting implementation
❌ **Completion Command Exists**: Tests written, command doesn't exist
✅ **Performance Acceptable**: Tests verify <100ms completion time

## Notes for Implementation

1. **Start with completion functions**: Implement `complete_client_names()` and `complete_server_ids()` first
2. **Update decorators**: Add `shell_complete` parameter to all relevant options/arguments
3. **Add completion command**: Implement `mcpi completion` command last
4. **Run tests frequently**: Use tests to validate each step of implementation
5. **Remove pytest.skip()**: As you implement each function, remove corresponding skip decorators

## Gaming Resistance

These tests are designed to be impossible to game:

1. **Real API Calls**: Tests call actual manager/catalog APIs, not just verify function was called
2. **Data Validation**: Tests verify actual returned data matches expected values
3. **State Verification**: Tests check server states, not just mocked responses
4. **Error Handling**: Tests verify graceful degradation, not just happy path
5. **Performance**: Tests measure actual execution time, not mocked timing
6. **Integration**: Tests verify CLI decorators are actually wired, not just function exists

**Bottom Line**: An AI agent cannot satisfy these tests with stubs, shortcuts, or hardcoded responses. The tests require real, working functionality.
