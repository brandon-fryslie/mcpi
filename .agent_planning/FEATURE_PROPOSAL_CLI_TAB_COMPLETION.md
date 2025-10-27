# FEATURE PROPOSAL: CLI Tab Completion Support for MCPI

## Executive Summary

This proposal outlines the addition of intelligent tab completion support for the mcpi CLI tool, leveraging Click 8.x's built-in shell completion capabilities. The feature will provide context-aware completions for commands, options, and dynamic values (clients, scopes, server names), significantly improving developer efficiency when interacting with MCP server management. The implementation will be pragmatic, maintainable, and deliver immediate value to users with minimal setup friction.

## User Value Proposition

### The Problem
Developers using mcpi currently must:
- Memorize or look up exact command names and options
- Remember available clients and their scope names
- Type full server IDs without assistance
- Check documentation or use `--help` frequently

### The Solution
Tab completion transforms the mcpi experience:
- **Faster Command Entry**: Press TAB to complete commands instead of typing fully
- **Discovery Through Exploration**: Learn available options by pressing TAB
- **Reduced Errors**: Avoid typos in server IDs, scope names, and client names
- **Context-Aware Help**: Get relevant completions based on current command context
- **No Mental Load**: Don't need to remember exact names, just the first few letters

### Real-World Impact
```bash
# Before: Must remember exact syntax
$ mcpi add @modelcontextprotocol/server-puppeteer --client claude-code --scope project-mcp

# After: Tab-guided entry
$ mcpi a<TAB>               # completes to "add"
$ mcpi add @mode<TAB>        # shows matching servers
$ mcpi add @modelcontextprotocol/server-puppeteer --cl<TAB>  # completes to "--client"
$ mcpi add @modelcontextprotocol/server-puppeteer --client cl<TAB>  # shows "claude-code"
$ mcpi add @modelcontextprotocol/server-puppeteer --client claude-code --sc<TAB>  # completes to "--scope"
$ mcpi add @modelcontextprotocol/server-puppeteer --client claude-code --scope pr<TAB>  # shows "project", "project-mcp"
```

## Technical Design

### Architecture Overview

The implementation leverages Click 8.x's native shell completion system, which provides:
1. **Built-in Shell Support**: Native bash, zsh, fish, and PowerShell support
2. **Dynamic Completion**: Runtime evaluation of available completions
3. **Context Preservation**: Access to parsed parameters during completion
4. **Custom Completers**: Ability to provide custom completion functions

### Core Components

#### 1. Click's Shell Completion System
```python
# Click 8.x provides these key APIs:
- click.shell_completion.add_completion_class()  # Register custom completion
- CompletionItem(value, help=None, type="plain")  # Completion suggestions
- shell_complete() method on ParamType classes     # Custom parameter completion
```

#### 2. Dynamic Completions Already Implemented

The codebase ALREADY includes sophisticated completion support in `DynamicScopeType`:

```python
class DynamicScopeType(click.ParamType):
    def shell_complete(self, ctx, param, incomplete):
        """Provide shell completion for scopes."""
        from click.shell_completion import CompletionItem

        # Context-aware scope completion based on selected client
        manager = ctx.obj.get('mcp_manager')
        client_name = ctx.params.get('client')
        scopes_info = manager.get_scopes_for_client(client_name)

        return [
            CompletionItem(scope['name'])
            for scope in scopes_info
            if scope['name'].startswith(incomplete)
        ]
```

This demonstrates the pattern is already established and working!

#### 3. Additional Completers Needed

**ClientCompleter**: Complete available client names
```python
def complete_client_names(ctx, param, incomplete):
    """Complete MCP client names."""
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

**ServerCompleter**: Complete server IDs from registry
```python
def complete_server_ids(ctx, param, incomplete):
    """Complete server IDs from registry."""
    if ctx.obj and 'catalog' in ctx.obj:
        catalog = ctx.obj['catalog']
        servers = catalog.list_servers()
        return [
            CompletionItem(
                server_id,
                help=server.description[:50]
            )
            for server_id, server in servers
            if server_id.startswith(incomplete)
        ][:50]  # Limit to prevent overwhelming output
    return []
```

**StateCompleter**: Complete server states
```python
def complete_server_states(ctx, param, incomplete):
    """Complete server state options."""
    states = ['enabled', 'disabled', 'not_installed']
    return [
        CompletionItem(state)
        for state in states
        if state.startswith(incomplete)
    ]
```

### Implementation Strategy

#### Phase 1: Enable Click's Built-in Completion (Immediate)

1. **Add completion setup command**:
```python
@main.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']),
              help='Shell type (auto-detect if not specified)')
def completion(shell):
    """Generate shell completion script."""
    import click.shell_completion

    if not shell:
        shell = detect_shell()

    completion_class = click.shell_completion.get_completion_class(shell)
    source = completion_class(main, {}, "mcpi").source()
    click.echo(source)

    # Provide installation instructions
    if shell == 'bash':
        click.echo("\n# Add to ~/.bashrc:")
        click.echo("# eval \"$(_MCPI_COMPLETE=bash_source mcpi)\"")
    elif shell == 'zsh':
        click.echo("\n# Add to ~/.zshrc:")
        click.echo("# eval \"$(_MCPI_COMPLETE=zsh_source mcpi)\"")
```

2. **Wire up existing completers**:
```python
# Update CLI decorators with shell_complete parameter
@click.option('--client', shell_complete=complete_client_names,
              help='Target client (uses default if not specified)')

@click.argument('server_id', shell_complete=complete_server_ids)

@click.option('--state', type=click.Choice(['enabled', 'disabled', 'not_installed']),
              shell_complete=complete_server_states)
```

#### Phase 2: Smart Context-Aware Completions (Week 2)

1. **Command-specific server filtering**:
   - `remove` command only shows installed servers
   - `enable` command only shows disabled servers
   - `disable` command only shows enabled servers

2. **Partial match support**:
   - Match anywhere in server ID, not just prefix
   - Fuzzy matching for common typos

3. **Caching for performance**:
   - Cache registry data for completion session
   - Refresh cache on registry commands

### Scope Coverage

#### What Will Be Completable

1. **Commands**: All main and sub-commands
   - `list`, `add`, `remove`, `enable`, `disable`, `info`, `status`
   - `client list`, `client info`, `client set-default`
   - `scope list`
   - `registry list`, `registry search`, `registry info`

2. **Options**: All option flags with descriptions
   - `--client` (with available client names)
   - `--scope` (context-aware based on selected client)
   - `--state` (enabled/disabled/not_installed)
   - `--verbose`, `--dry-run`, `--help`

3. **Arguments**: Dynamic value completion
   - Server IDs from registry (for add/info commands)
   - Installed server IDs (for remove/enable/disable)
   - Client names (for client commands)

4. **Smart Filtering**:
   - Scope values filtered by selected client
   - Server IDs filtered by current command context

### Installation Experience

#### Automatic Setup (Recommended)

```bash
# Install completion for current shell
$ mcpi completion --install

✓ Detected shell: zsh
✓ Added completion to ~/.zshrc
✓ Completion will be active in new shell sessions

To activate in current session, run:
  source ~/.zshrc
```

#### Manual Setup

```bash
# Generate completion script
$ mcpi completion --shell bash > mcpi-completion.bash

# For bash - add to ~/.bashrc:
eval "$(_MCPI_COMPLETE=bash_source mcpi)"

# For zsh - add to ~/.zshrc:
eval "$(_MCPI_COMPLETE=zsh_source mcpi)"

# For fish - add to ~/.config/fish/completions/mcpi.fish:
_MCPI_COMPLETE=fish_source mcpi | source
```

#### Verification

```bash
# Test completion is working
$ mcpi <TAB><TAB>
add       client    disable   enable    info      list      registry  remove    scope     status

$ mcpi add @model<TAB>
@modelcontextprotocol/server-anthropic
@modelcontextprotocol/server-aws-bedrock
@modelcontextprotocol/server-playwright
@modelcontextprotocol/server-puppeteer
```

## Testing & Validation

### Automated Testing

1. **Unit Tests**: Test completion functions in isolation
```python
def test_complete_client_names():
    """Test client name completion."""
    ctx = create_mock_context(clients=['claude-code', 'cursor', 'vscode'])
    completions = complete_client_names(ctx, None, 'cl')
    assert len(completions) == 1
    assert completions[0].value == 'claude-code'
```

2. **Integration Tests**: Test full completion flow
```python
def test_scope_completion_with_client_context():
    """Test scope completion respects client selection."""
    result = runner.invoke(main, ['add', 'test-server', '--client', 'claude-code', '--scope'],
                          input='\t\t')  # Simulate TAB TAB
    assert 'project' in result.output
    assert 'project-mcp' in result.output
```

3. **Shell Script Tests**: Validate actual shell integration
```bash
#!/bin/bash
# test_completion.sh
eval "$(_MCPI_COMPLETE=bash_source mcpi)"
COMPREPLY=()
_mcpi_completion "mcpi add @model"
[[ "${COMPREPLY[@]}" == *"@modelcontextprotocol"* ]] || exit 1
```

### Manual Testing Checklist

- [ ] Commands complete correctly
- [ ] Options complete with `--` prefix
- [ ] Client names complete from detected clients
- [ ] Scopes complete based on selected client
- [ ] Server IDs complete from registry
- [ ] Partial matches work correctly
- [ ] Performance is acceptable (<100ms for completion)
- [ ] Works in bash, zsh, fish
- [ ] Installation instructions are clear

### Edge Cases

1. **No MCP Manager Available**: Gracefully fallback to static completions
2. **Large Registry**: Limit results to prevent overwhelming output
3. **Slow Registry Load**: Use cached data for completions
4. **Multiple Clients**: Show all available clients
5. **Invalid Context**: Return empty completion list
6. **Permission Errors**: Silent failure with no completions

## Documentation Requirements

### README.md Addition

```markdown
## Tab Completion

MCPI supports intelligent tab completion for bash, zsh, and fish shells.

### Quick Setup

```bash
# Automatic installation
mcpi completion --install

# Manual installation for bash
echo 'eval "$(_MCPI_COMPLETE=bash_source mcpi)"' >> ~/.bashrc

# Manual installation for zsh
echo 'eval "$(_MCPI_COMPLETE=zsh_source mcpi)"' >> ~/.zshrc
```

### Features

- Complete command names and options
- Context-aware scope completion based on selected client
- Server ID completion from registry
- Smart filtering based on command context
```

### Help Text Updates

```python
@main.command()
def completion():
    """Setup shell tab completion for mcpi.

    Tab completion provides intelligent suggestions for:
    - Command names (list, add, remove, etc.)
    - Option flags (--client, --scope, --help)
    - Client names (based on detected MCP clients)
    - Scope names (filtered by selected client)
    - Server IDs (from the registry)

    Examples:
      mcpi completion --install       # Auto-detect and install
      mcpi completion --shell bash    # Generate bash completion
      mcpi completion --shell zsh     # Generate zsh completion
    """
```

## Future Enhancements

### Near-term (v1.1)
1. **PowerShell Support**: Add Windows PowerShell completion
2. **Fuzzy Matching**: Support fzf-style fuzzy completion
3. **Alias Support**: Complete common server aliases
4. **Description Display**: Show server descriptions in completion

### Long-term (v2.0)
1. **AI-Powered Suggestions**: ML-based command prediction
2. **History-Based Completion**: Prioritize frequently used items
3. **Multi-Select Completion**: Select multiple servers at once
4. **Inline Documentation**: Show help text during completion

## Success Metrics

### Quantitative Metrics
- **Completion Performance**: <100ms response time
- **Coverage**: 100% of commands/options completable
- **Adoption**: 50% of users enable completion within 3 months
- **Error Reduction**: 30% fewer command errors

### Qualitative Metrics
- **User Satisfaction**: Positive feedback in issues/discussions
- **Discoverability**: Users find features without documentation
- **Learning Curve**: New users productive within 5 minutes
- **Developer Happiness**: "This makes mcpi a joy to use"

## Implementation Plan

### Week 1: Foundation
- [ ] Add completion command to CLI
- [ ] Implement basic command/option completion
- [ ] Test with bash and zsh
- [ ] Update documentation

### Week 2: Dynamic Completions
- [ ] Add client name completion
- [ ] Enhance existing scope completion
- [ ] Add server ID completion
- [ ] Add context-aware filtering

### Week 3: Polish & Release
- [ ] Add fish shell support
- [ ] Optimize performance
- [ ] Write comprehensive tests
- [ ] Create demo video
- [ ] Release v0.2.0 with completion support

## Risk Mitigation

1. **Performance Issues**: Pre-load and cache registry data
2. **Shell Compatibility**: Test on multiple shell versions
3. **Breaking Changes**: Maintain backward compatibility
4. **User Confusion**: Provide clear setup instructions
5. **Maintenance Burden**: Keep implementation simple and testable

## Conclusion

Tab completion is a high-impact, low-complexity feature that will significantly improve the mcpi user experience. By leveraging Click's built-in capabilities and following established patterns already in the codebase, we can deliver a robust solution with minimal maintenance overhead. The feature directly addresses daily developer friction, making mcpi faster and more enjoyable to use.

The implementation is achievable in 2-3 weeks, with immediate value delivered in the first week. This positions mcpi as a professional-grade tool that respects developer time and workflow efficiency.