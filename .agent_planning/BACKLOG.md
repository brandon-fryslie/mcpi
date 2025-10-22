# MCPI Feature Backlog

This file contains feature requests and enhancements for the MCPI project.

## Backlog Items

### [FEATURE] MCP Server Rescope Command

**Priority**: Medium
**Status**: Planned
**Estimated Effort**: Medium (2-4 hours)

#### Description

Add a `rescope` command that allows users to move an MCP server configuration from one scope to another within the same client. This enables workflows like testing a server at the project level and then promoting it to the user level for reuse across projects, or vice versa.

#### User Stories

1. **As a developer**, I want to move a project-level MCP server to my user-level configuration so I can use it across multiple projects without duplicating the configuration.

2. **As a developer**, I want to move a user-level MCP server to project-level so I can test project-specific customizations without affecting my global configuration.

3. **As a developer**, I want the command to fail gracefully if the server doesn't exist in the source scope or already exists in the destination scope.

#### Command Syntax

```bash
# Standard syntax
mcpi rescope <server_name> --from <source_scope> --to <dest_scope>

# Position-independent variations (all should work)
mcpi rescope my-server --from project-mcp --to user-internal
mcpi rescope --from project-mcp --to user-internal my-server
mcpi rescope --from project-mcp my-server --to user-internal
mcpi rescope --to user-internal --from project-mcp my-server

# With client specification
mcpi rescope my-server --from project-mcp --to user-internal --client claude-code

# Dry-run mode
mcpi rescope my-server --from project-mcp --to user-internal --dry-run
```

#### Technical Design

**Integration with Plugin System**

The rescope command must work with the existing plugin architecture:

1. **Client Selection**: Use the same client detection logic as other commands
   - Auto-detect default client via `MCPManager`
   - Allow override with `--client` flag
   - Validate client exists in registry

2. **Scope Validation**: Validate scopes against the selected client's available scopes
   - Use `MCPManager.get_scopes_for_client(client_name)` to get valid scopes
   - Provide clear error messages if invalid scopes are specified
   - Use the existing `DynamicScopeType` for scope parameter validation

3. **Operation Flow**:
   ```python
   # Pseudo-code
   def rescope(server_name, from_scope, to_scope, client=None, dry_run=False):
       # 1. Get the client plugin
       manager = get_mcp_manager()
       client_plugin = manager.get_client(client)

       # 2. Validate scopes exist for this client
       validate_scope(client_plugin, from_scope)
       validate_scope(client_plugin, to_scope)

       # 3. Get source scope handler
       source_handler = client_plugin.get_scope_handler(from_scope)
       if not source_handler.has_server(server_name):
           raise ServerNotFoundError(...)

       # 4. Get destination scope handler
       dest_handler = client_plugin.get_scope_handler(to_scope)
       if dest_handler.has_server(server_name):
           raise ServerExistsError(...)

       # 5. Read config from source
       server_config = source_handler.get_server_config(server_name)

       # 6. If dry-run, show what would happen and exit
       if dry_run:
           print_dry_run_summary(...)
           return

       # 7. Write to destination
       result = dest_handler.add_server(server_name, server_config)
       if not result.success:
           raise WriteError(...)

       # 8. Remove from source (with rollback on failure)
       try:
           result = source_handler.remove_server(server_name)
           if not result.success:
               # Rollback: remove from destination
               dest_handler.remove_server(server_name)
               raise RemoveError(...)
       except Exception as e:
           # Rollback: remove from destination
           dest_handler.remove_server(server_name)
           raise

       # 9. Return success
       return OperationResult.success(...)
   ```

**CLI Implementation** (in `mcpi/cli.py`):

```python
@main.command()
@click.argument('server_name')
@click.option('--from', 'from_scope', required=True,
              type=DynamicScopeType(),
              help='Source scope to move from')
@click.option('--to', 'to_scope', required=True,
              type=DynamicScopeType(),
              help='Destination scope to move to')
@click.option('--client', default=None,
              help='MCP client to use (auto-detected if not specified)')
@click.option('--dry-run', is_flag=True,
              help='Show what would happen without making changes')
@click.pass_context
def rescope(ctx, server_name, from_scope, to_scope, client, dry_run):
    """Move an MCP server configuration from one scope to another.

    Examples:
        mcpi rescope my-server --from project-mcp --to user-internal
        mcpi rescope --from project-mcp --to user-internal my-server
    """
    # Implementation here
```

**New Methods Required**:

1. `ScopeHandler.get_server_config(server_id: str) -> ServerConfig`
   - Returns the full configuration for a specific server
   - Raises error if server doesn't exist

2. Update `MCPManager` or add helper function for rescope operation
   - Could be a new method: `manager.rescope_server(server_name, from_scope, to_scope, client)`

#### Edge Cases & Error Handling

1. **Server doesn't exist in source scope**
   - Error: `"Server 'my-server' not found in scope '{from_scope}' for client '{client}'"`
   - Suggest: List available servers in that scope

2. **Server already exists in destination scope**
   - Error: `"Server 'my-server' already exists in scope '{to_scope}' for client '{client}'"`
   - Options:
     - Suggest using `--force` flag to overwrite (future enhancement)
     - Suggest different destination scope

3. **Invalid scope names**
   - Error: `"Invalid scope '{scope}' for client '{client}'. Available scopes: {scopes}"`
   - Use existing `DynamicScopeType` validation

4. **Source and destination are the same**
   - Error: `"Source and destination scopes cannot be the same"`

5. **Write succeeds but remove fails**
   - Implement rollback: remove from destination
   - Error: `"Failed to remove from source scope after copying. Server remains in both scopes."`
   - Provide recovery command suggestion

6. **Scope doesn't exist (file not found)**
   - For source: Error as "server not found"
   - For destination: Create the scope file if it doesn't exist (standard behavior)

7. **Client not found/installed**
   - Error: `"Client '{client}' not found. Available clients: {clients}"`

#### Testing Requirements

**Unit Tests** (`tests/test_cli_rescope.py`):

```python
class TestRescopeCommand:
    """Tests for the rescope command."""

    def test_rescope_basic_flow(self):
        """Test basic rescope from project to user scope."""

    def test_rescope_position_independent_args(self):
        """Test that arguments can be in any order."""

    def test_rescope_server_not_in_source(self):
        """Test error when server doesn't exist in source scope."""

    def test_rescope_server_exists_in_dest(self):
        """Test error when server already exists in destination."""

    def test_rescope_invalid_source_scope(self):
        """Test error with invalid source scope name."""

    def test_rescope_invalid_dest_scope(self):
        """Test error with invalid destination scope name."""

    def test_rescope_same_scope(self):
        """Test error when from and to are the same."""

    def test_rescope_dry_run(self):
        """Test dry-run mode doesn't make changes."""

    def test_rescope_rollback_on_remove_failure(self):
        """Test rollback when remove from source fails."""

    def test_rescope_with_explicit_client(self):
        """Test rescope with --client flag."""

    def test_rescope_multi_client_scopes(self):
        """Test that scopes are validated per client."""
```

**Integration Tests** (`tests/test_rescope_integration.py`):

```python
def test_rescope_filesystem_server_project_to_user():
    """Full integration test: rescope filesystem server from project to user."""

def test_rescope_preserves_all_config(self):
    """Verify all configuration fields are preserved during rescope."""

def test_rescope_updates_both_files():
    """Verify source file loses server and dest file gains server."""
```

**Functional Tests**:

```python
def test_rescope_real_mcp_config():
    """Use actual .mcp.json and settings files (not mocked)."""
```

#### Implementation Tasks

- [ ] Add `get_server_config()` method to `ScopeHandler` base class
- [ ] Implement `get_server_config()` in `FileBasedScope`
- [ ] Add rescope logic to `MCPManager` (or create helper module)
- [ ] Add `rescope` command to CLI with Click
- [ ] Implement position-independent argument handling
- [ ] Add dry-run functionality
- [ ] Implement rollback logic for transaction safety
- [ ] Add comprehensive error messages for all edge cases
- [ ] Write unit tests (target: 100% coverage of rescope logic)
- [ ] Write integration tests
- [ ] Write functional tests with real config files
- [ ] Update CLI help documentation
- [ ] Add examples to README.md
- [ ] Add entry to CHANGELOG.md

#### Future Enhancements

1. **Batch Rescope**: `mcpi rescope --all --from project-mcp --to user-internal`
   - Move all servers from one scope to another

2. **Force/Merge Flag**: `mcpi rescope my-server --from X --to Y --force`
   - Overwrite if server exists in destination

3. **Interactive Mode**: `mcpi rescope my-server --interactive`
   - Prompt for source/destination scopes with selection menu

4. **Copy Mode**: `mcpi rescope my-server --from X --to Y --copy`
   - Copy instead of move (leave in source scope)

#### Acceptance Criteria

- [ ] Command works with all documented argument orders
- [ ] Works with all clients that have multiple scopes (Claude Code, etc.)
- [ ] Gracefully handles all documented error cases
- [ ] Provides clear, actionable error messages
- [ ] Dry-run mode accurately shows what would happen
- [ ] Rollback works if operation fails midway
- [ ] All configuration fields are preserved during rescope
- [ ] Test coverage ≥ 95%
- [ ] Documentation updated in README and CLI help
