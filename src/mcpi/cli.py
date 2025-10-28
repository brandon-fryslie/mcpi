"""New CLI implementation using the plugin architecture."""

import asyncio
import json
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.text import Text
from rich import box

from mcpi.clients import MCPManager, ServerConfig, ServerState
from mcpi.registry.catalog import ServerCatalog

console = Console()


def shorten_path(path: Optional[str]) -> str:
    """Shorten a path for display by replacing home and current directory.

    Args:
        path: The path to shorten

    Returns:
        Shortened path with ~ for home and . for current directory
    """
    if not path:
        return "N/A"

    path_obj = Path(path)
    home = Path.home()
    cwd = Path.cwd()

    try:
        # Try to make it relative to current directory first
        relative_to_cwd = path_obj.relative_to(cwd)
        # If it's the current directory itself, return "."
        if str(relative_to_cwd) == ".":
            return "."
        return f"./{relative_to_cwd}"
    except ValueError:
        # Not relative to cwd, try home directory
        try:
            relative_to_home = path_obj.relative_to(home)
            return f"~/{relative_to_home}"
        except ValueError:
            # Not relative to home either, return as-is
            return str(path)


def get_mcp_manager(ctx: click.Context) -> MCPManager:
    """Lazy initialization of MCPManager."""
    if 'mcp_manager' not in ctx.obj:
        try:
            ctx.obj['mcp_manager'] = MCPManager()
        except Exception as e:
            if ctx.obj.get('verbose', False):
                console.print(f"[red]MCP manager initialization error: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to initialize MCP manager: {e}[/red]")
            sys.exit(1)
    return ctx.obj['mcp_manager']


def get_catalog(ctx: click.Context) -> ServerCatalog:
    """Lazy initialization of ServerCatalog."""
    if 'catalog' not in ctx.obj:
        try:
            # Use the default registry path
            ctx.obj['catalog'] = ServerCatalog()
            ctx.obj['catalog'].load_registry()
        except Exception as e:
            if ctx.obj.get('verbose', False):
                console.print(f"[red]Catalog initialization error: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to initialize server catalog: {e}[/red]")
            sys.exit(1)
    return ctx.obj['catalog']


def get_registry_manager(ctx: click.Context) -> ServerCatalog:
    """Get the server catalog (backward compat alias)."""
    return get_catalog(ctx)


def get_available_scopes(ctx: click.Context, client_name: Optional[str] = None) -> List[str]:
    """Get available scope names for a client.

    Args:
        ctx: Click context
        client_name: Optional client name (uses default if not specified)

    Returns:
        List of available scope names
    """
    try:
        manager = get_mcp_manager(ctx)
        scopes_info = manager.get_scopes_for_client(client_name)
        return [scope['name'] for scope in scopes_info]
    except Exception:
        # Return common default scopes if we can't get them dynamically
        return ['user', 'user-internal', 'project', 'project-mcp']


class DynamicScopeType(click.ParamType):
    """Dynamic parameter type for scopes that validates based on the client."""

    name = "scope"

    def get_metavar(self, param, ctx=None):
        """Get metavar for help text."""
        # Show common examples, but indicate it varies by client
        return '[varies by client: e.g., user|project|workspace]'

    def convert(self, value, param, ctx):
        """Convert and validate the scope value."""
        if value is None:
            return None

        # Try to get the client from context or command parameters
        client_name = None
        if ctx and ctx.params:
            client_name = ctx.params.get('client')

        # If we have a client, validate against its available scopes
        if ctx and ctx.obj:
            try:
                # Try to get available scopes for validation
                manager = ctx.obj.get('mcp_manager')
                if manager:
                    # If no client specified, use the default
                    if not client_name:
                        client_name = manager.default_client

                    scopes_info = manager.get_scopes_for_client(client_name)
                    available_scopes = [scope['name'] for scope in scopes_info]

                    if available_scopes and value not in available_scopes:
                        self.fail(
                            f"'{value}' is not a valid scope for client '{client_name}'. "
                            f"Available scopes: {', '.join(available_scopes)}",
                            param,
                            ctx
                        )
            except click.exceptions.BadParameter:
                # Re-raise validation errors
                raise
            except Exception:
                # If we can't validate due to other errors, just accept the value
                pass

        return value

    def shell_complete(self, ctx, param, incomplete):
        """Provide shell completion for scopes."""
        from click.shell_completion import CompletionItem

        completions = []

        # Try to get available scopes for the current client
        if ctx and ctx.obj:
            try:
                # Initialize manager if not present
                if 'mcp_manager' not in ctx.obj:
                    ctx.obj['mcp_manager'] = MCPManager()

                manager = ctx.obj.get('mcp_manager')
                client_name = ctx.params.get('client') if ctx.params else None

                if manager:
                    scopes_info = manager.get_scopes_for_client(client_name)

                    # For rescope command: filter out the --from scope when completing --to
                    exclude_scope = None
                    if param and param.name == 'to_scope' and ctx.params:
                        # If completing --to parameter, exclude the --from scope
                        exclude_scope = ctx.params.get('from_scope')
                    elif param and param.name == 'from_scope' and ctx.params:
                        # If completing --from parameter, exclude the --to scope (if already set)
                        exclude_scope = ctx.params.get('to_scope')

                    # Show file paths for each scope
                    completions = [
                        CompletionItem(
                            scope['name'],
                            help=scope.get('path', 'No path')
                        )
                        for scope in scopes_info
                        if scope['name'].startswith(incomplete) and scope['name'] != exclude_scope
                    ]
            except Exception:
                # If we can't get scopes from manager, use defaults
                default_scopes = ['user', 'user-internal', 'project', 'project-mcp', 'workspace', 'global']
                completions = [
                    CompletionItem(scope)
                    for scope in default_scopes
                    if scope.startswith(incomplete)
                ]
        else:
            # No context available, use default scopes
            default_scopes = ['user', 'user-internal', 'project', 'project-mcp', 'workspace', 'global']
            completions = [
                CompletionItem(scope)
                for scope in default_scopes
                if scope.startswith(incomplete)
            ]

        return completions


# Tab completion functions

def complete_client_names(ctx: click.Context, param: click.Parameter, incomplete: str) -> List:
    """Complete MCP client names from available clients.

    Args:
        ctx: Click context with mcp_manager in obj
        param: Parameter being completed
        incomplete: Partial text entered by user

    Returns:
        List of CompletionItem objects matching the prefix
    """
    from click.shell_completion import CompletionItem

    if not ctx or not ctx.obj:
        return []

    try:
        # Initialize manager if not present
        if 'mcp_manager' not in ctx.obj:
            ctx.obj['mcp_manager'] = MCPManager()

        manager = ctx.obj['mcp_manager']

        # Check if we need to filter by scope
        scope_param = ctx.params.get('scope') if hasattr(ctx, 'params') and ctx.params else None

        client_info = manager.get_client_info()

        # If scope is specified, filter clients that support that scope
        if scope_param:
            filtered_clients = {}
            for name, info in client_info.items():
                scopes_info = manager.get_scopes_for_client(name)
                scope_names = [s['name'] for s in scopes_info]
                if scope_param in scope_names:
                    filtered_clients[name] = info
            client_info = filtered_clients if filtered_clients else client_info

        return [
            CompletionItem(
                name,
                help=f"{info.get('server_count', 0)} servers"
            )
            for name, info in client_info.items()
            if name.startswith(incomplete)
        ]
    except Exception as e:
        # Fallback to common client names if initialization fails
        default_clients = ['claude-code', 'cursor', 'vscode']
        return [
            CompletionItem(name)
            for name in default_clients
            if name.startswith(incomplete)
        ]


def complete_server_ids(ctx: click.Context, param: click.Parameter, incomplete: str) -> List:
    """Complete server IDs from registry or installed servers.

    This function provides context-aware completion:
    - For 'add' command: shows servers from registry
    - For 'remove', 'enable', 'disable' commands: shows installed servers filtered by state
    - Other commands: shows all registry servers

    Args:
        ctx: Click context with catalog/mcp_manager in obj
        param: Parameter being completed
        incomplete: Partial text entered by user

    Returns:
        List of CompletionItem objects matching the prefix (max 50)
    """
    from click.shell_completion import CompletionItem

    if not ctx or not ctx.obj:
        return []

    try:
        # Get command name for context-aware filtering
        # Try multiple methods to get the command name
        command_name = None
        if hasattr(ctx, 'info_name'):
            command_name = ctx.info_name
        elif hasattr(ctx, 'command') and hasattr(ctx.command, 'name'):
            command_name = ctx.command.name
        # Also check parent context for command groups
        if not command_name and ctx.parent and hasattr(ctx.parent, 'info_name'):
            command_name = ctx.parent.info_name

        # For remove/enable/disable commands, show only installed servers
        if command_name in ['remove', 'enable', 'disable']:
            # Initialize manager if not present
            if 'mcp_manager' not in ctx.obj:
                ctx.obj['mcp_manager'] = MCPManager()

            manager = ctx.obj['mcp_manager']

            # Filter by state for enable/disable
            state_filter = None
            if command_name == 'enable':
                state_filter = ServerState.DISABLED
            elif command_name == 'disable':
                state_filter = ServerState.ENABLED

            servers = manager.list_servers(state_filter=state_filter)

            # Extract unique server IDs from installed servers
            server_ids = set()
            for qualified_id, info in servers.items():
                server_ids.add(info.id)

            return [
                CompletionItem(server_id)
                for server_id in sorted(server_ids)
                if server_id.startswith(incomplete)
            ][:50]

        # For add and other commands, show servers from registry
        # Initialize catalog if not present
        if 'catalog' not in ctx.obj:
            ctx.obj['catalog'] = ServerCatalog()
            ctx.obj['catalog'].load_registry()

        catalog = ctx.obj['catalog']
        servers = catalog.list_servers()

        # Filter and limit results
        matches = [
            CompletionItem(
                server_id,
                help=server.description[:50] + "..." if len(server.description) > 50
                     else server.description
            )
            for server_id, server in servers
            if server_id.startswith(incomplete)
        ]

        # Limit to 50 results to avoid overwhelming user
        return matches[:50]
    except Exception as e:
        # Fallback to empty list if we can't load servers
        # In development/testing, you might want to see the error:
        # import sys
        # print(f"Server completion error: {e}", file=sys.stderr)
        # import traceback
        # traceback.print_exc(file=sys.stderr)
        return []


def complete_rescope_server_name(ctx: click.Context, param: click.Parameter, incomplete: str) -> List:
    """Complete server names for rescope command.

    Shows all installed MCP servers. If --from scope is specified, filters to only
    servers in that scope. Otherwise shows all installed servers across all scopes.

    Args:
        ctx: Click context with mcp_manager
        param: Parameter being completed
        incomplete: Partial text entered by user

    Returns:
        List of CompletionItem objects for installed servers
    """
    from click.shell_completion import CompletionItem

    if not ctx or not ctx.obj:
        return []

    try:
        # Initialize manager if needed
        if 'mcp_manager' not in ctx.obj:
            manager = get_mcp_manager(ctx)
        else:
            manager = ctx.obj['mcp_manager']

        # Get client (use default if not specified)
        client_name = ctx.params.get('client')
        if not client_name:
            client_name = manager.get_default_client()

        # Get the --from scope if specified
        from_scope = ctx.params.get('from_scope')

        if from_scope:
            # List servers from the specified source scope only
            servers = manager.list_servers(client=client_name, scope=from_scope)
        else:
            # No scope specified - show all installed servers across all scopes
            servers = manager.list_servers(client=client_name)

        # Return matching server IDs
        return [
            CompletionItem(server_id)
            for server_id in sorted(servers.keys())
            if server_id.startswith(incomplete)
        ][:50]

    except Exception as e:
        # Log error for debugging
        import traceback
        from pathlib import Path
        log_file = Path.home() / '.mcpi_completion_debug.log'
        with open(log_file, 'a') as f:
            f.write(f"\n=== complete_rescope_server_name error ===\n")
            f.write(f"Error: {e}\n")
            f.write(traceback.format_exc())
            f.write("\n")
        return []


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.version_option()
@click.pass_context
def main(ctx: click.Context, verbose: bool, dry_run: bool) -> None:
    """MCPI - MCP Server Package Installer (New Plugin Architecture)."""
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store options in context
    ctx.obj['verbose'] = verbose
    ctx.obj['dry_run'] = dry_run


# CLIENT MANAGEMENT COMMANDS

@main.group()
@click.pass_context
def client(ctx: click.Context) -> None:
    """Manage MCP clients and their configurations."""
    pass


@client.command('list')
@click.pass_context
def list_clients(ctx: click.Context) -> None:
    """List available MCP clients."""
    try:
        manager = get_mcp_manager(ctx)
        client_info = manager.get_client_info()

        if not client_info:
            console.print("[yellow]No MCP clients available[/yellow]")
            return

        table = Table(title="Available MCP Clients")
        table.add_column("Client", style="cyan", no_wrap=True)
        table.add_column("Default", style="green")
        table.add_column("Scopes", style="blue")
        table.add_column("Servers", style="magenta")
        table.add_column("Status", style="yellow")

        for name, info in client_info.items():
            is_default = "✓" if name == manager.default_client else ""
            scope_count = str(len(info.get('scopes', [])))
            server_count = str(info.get('server_count', 0))

            # Determine status
            if 'error' in info:
                status = f"Error: {info['error']}"
            elif info.get('installed', False):
                status = "Installed"
            else:
                status = "Available"

            table.add_row(name, is_default, scope_count, server_count, status)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing clients: {e}[/red]")


@client.command('info')
@click.argument('client_name', required=False, shell_complete=complete_client_names)
@click.pass_context
def client_info(ctx: click.Context, client_name: Optional[str]) -> None:
    """Show detailed information about a client."""
    try:
        manager = get_mcp_manager(ctx)

        if client_name is None:
            client_name = manager.default_client
            if not client_name:
                console.print("[red]No default client set and no client specified[/red]")
                return

        info = manager.get_client_info(client_name)
        if not info or client_name not in info:
            console.print(f"[red]Client '{client_name}' not found[/red]")
            return

        client_data = info[client_name]

        # Create info panel
        info_text = f"[bold]Client:[/bold] {client_name}\n"
        if client_name == manager.default_client:
            info_text += "[bold]Default:[/bold] Yes\n"

        if 'error' in client_data:
            info_text += f"[bold]Error:[/bold] {client_data['error']}\n"
        else:
            info_text += f"[bold]Servers:[/bold] {client_data.get('server_count', 0)}\n"

            # Show scopes
            scopes = client_data.get('scopes', [])
            if scopes:
                info_text += f"[bold]Scopes:[/bold]\n"
                for scope in scopes:
                    scope_type = "User" if scope.get('is_user_level') else "Project"
                    info_text += f"  • {scope['name']} ({scope_type}) - {scope['description']}\n"
                    if scope.get('path'):
                        info_text += f"    Path: {scope['path']}\n"

        console.print(Panel(info_text, title=f"Client Information: {client_name}"))

    except Exception as e:
        console.print(f"[red]Error getting client info: {e}[/red]")


@client.command('set-default')
@click.argument('client_name', shell_complete=complete_client_names)
@click.pass_context
def set_default_client(ctx: click.Context, client_name: str) -> None:
    """Set the default client for MCPI operations."""
    try:
        manager = get_mcp_manager(ctx)
        result = manager.set_default_client(client_name)

        if result.success:
            console.print(f"[green]✓ {result.message}[/green]")
        else:
            console.print(f"[red]✗ {result.message}[/red]")

    except Exception as e:
        console.print(f"[red]Error setting default client: {e}[/red]")


# SCOPE MANAGEMENT COMMANDS

@main.group()
@click.pass_context
def scope(ctx: click.Context) -> None:
    """Manage configuration scopes."""
    pass


@scope.command('list')
@click.option('--client', shell_complete=complete_client_names, help='Filter by client (uses default if not specified)')
@click.pass_context
def list_scopes(ctx: click.Context, client: Optional[str]) -> None:
    """List available configuration scopes."""
    try:
        manager = get_mcp_manager(ctx)
        scopes = manager.get_scopes_for_client(client)

        if not scopes:
            client_name = client or manager.default_client
            console.print(f"[yellow]No scopes available for client '{client_name}'[/yellow]")
            return

        # Build caption with current directory
        cwd = Path.cwd()
        caption_text = Text()
        caption_text.append("Current Directory: ", style="cyan bold")
        caption_text.append(str(cwd), style="yellow")

        table = Table(
            title=f"Configuration Scopes: {client or manager.default_client}",
            caption=caption_text,
            caption_justify="left"
        )
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="blue")
        table.add_column("Priority", style="magenta")
        table.add_column("Path", style="yellow")
        table.add_column("Exists", style="green")
        table.add_column("Description", style="white")

        for scope in scopes:
            scope_type = "User" if scope['is_user_level'] else "Project"
            exists = "✓" if scope['exists'] else "✗"
            path = shorten_path(scope['path'])

            table.add_row(
                scope['name'],
                scope_type,
                str(scope['priority']),
                path,
                exists,
                scope['description']
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing scopes: {e}[/red]")


# SERVER MANAGEMENT COMMANDS

@main.command()
@click.option('--client', shell_complete=complete_client_names, help='Filter by client (uses default if not specified)')
@click.option('--scope', type=DynamicScopeType(), help='Filter by scope (available scopes depend on client)')
@click.option('--state', type=click.Choice(['enabled', 'disabled', 'not_installed']), help='Filter by state')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
@click.pass_context
def list(ctx: click.Context, client: Optional[str], scope: Optional[str], state: Optional[str], verbose: bool) -> None:
    """List MCP servers with optional filtering."""
    try:
        manager = get_mcp_manager(ctx)

        # Convert state string to enum
        state_filter = None
        if state:
            state_filter = ServerState[state.upper()]

        servers = manager.list_servers(
            client_name=client,
            scope=scope,
            state_filter=state_filter
        )

        if not servers:
            console.print("[yellow]No servers found[/yellow]")
            return

        if verbose:
            # Detailed view
            for qualified_id, info in servers.items():
                server_text = f"[bold]ID:[/bold] {info.id}\n"
                server_text += f"[bold]Client:[/bold] {info.client}\n"
                server_text += f"[bold]Scope:[/bold] {info.scope}\n"
                server_text += f"[bold]State:[/bold] {info.state.name}\n"
                server_text += f"[bold]Command:[/bold] {info.command}\n"
                if info.args:
                    server_text += f"[bold]Args:[/bold] {' '.join(info.args)}\n"
                if info.env:
                    server_text += f"[bold]Environment:[/bold] {len(info.env)} variables\n"

                console.print(Panel(server_text, title=qualified_id))
        else:
            # Table view
            table = Table(title="MCP Servers")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Client", style="blue")
            table.add_column("Scope", style="magenta")
            table.add_column("State", style="green")
            table.add_column("Command", style="yellow")

            for qualified_id, info in servers.items():
                state_color = {
                    ServerState.ENABLED: "green",
                    ServerState.DISABLED: "yellow",
                    ServerState.NOT_INSTALLED: "red"
                }.get(info.state, "white")

                table.add_row(
                    info.id,
                    info.client,
                    info.scope,
                    f"[{state_color}]{info.state.name}[/{state_color}]",
                    info.command or "N/A"
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing servers: {e}[/red]")


@main.command()
@click.argument('server_id', shell_complete=complete_server_ids)
@click.option('--client', shell_complete=complete_client_names, help='Target client (uses default if not specified)')
@click.option('--scope', type=DynamicScopeType(), help='Target scope (available scopes depend on client, uses primary scope if not specified)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def add(ctx: click.Context, server_id: str, client: Optional[str], scope: Optional[str], dry_run: bool) -> None:
    """Add an MCP server from the registry."""
    verbose = ctx.obj.get('verbose', False)

    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True

    try:
        # Get components
        manager = get_mcp_manager(ctx)
        catalog = get_catalog(ctx)

        # Get server info from catalog
        server = catalog.get_server(server_id)
        if not server:
            console.print(f"[red]Server '{server_id}' not found in registry[/red]")
            return

        # If no scope specified, show interactive menu (unless in dry-run mode)
        if not scope:
            # Get available scopes for the target client
            target_client = client or manager.default_client
            scopes_info = manager.get_scopes_for_client(target_client)

            if not scopes_info:
                console.print(f"[red]No scopes available for client '{target_client}'[/red]")
                ctx.exit(1)

            # In dry-run mode, just use the first available scope
            if ctx.obj.get('dry_run', False):
                scope = scopes_info[0]['name']
                console.print(f"[dim]Dry-run: Would use scope '{scope}'[/dim]")
            else:
                # Build a list of scope choices with descriptions
                console.print(f"\n[bold cyan]Select a scope for '{server_id}':[/bold cyan]")
                console.print(f"[dim]Client: {target_client}[/dim]\n")

                # Display scope options
                scope_choices = []
                for i, scope_info in enumerate(scopes_info, 1):
                    scope_name = scope_info['name']
                    scope_desc = scope_info['description']
                    scope_type = "User" if scope_info['is_user_level'] else "Project"
                    exists = "✓" if scope_info['exists'] else "✗"

                    # Show the option
                    console.print(f"  [{i}] [cyan]{scope_name}[/cyan] - {scope_type} scope {exists}")
                    console.print(f"      [dim]{scope_desc}[/dim]")
                    scope_choices.append(scope_name)

                # Get user's choice
                console.print()
                choice = Prompt.ask(
                    "Enter the number of your choice",
                    choices=[str(i) for i in range(1, len(scope_choices) + 1)],
                    default="1"
                )

                scope = scope_choices[int(choice) - 1]
                console.print(f"[green]Selected scope: {scope}[/green]\n")

        # Check if server already exists
        existing_info = manager.get_server_info(server_id, client)
        if existing_info:
            console.print(f"[yellow]Server '{server_id}' already exists (state: {existing_info.state.name})[/yellow]")
            return

        # Create server configuration from the new structure
        config = ServerConfig(
            command=server.command,
            args=server.args,
            env={},
            type="stdio"
        )

        # Show server info and ask for confirmation
        if not ctx.obj.get('dry_run', False):
            console.print(f"\n[bold]Server ID:[/bold] {server_id}")
            console.print(f"[bold]Description:[/bold] {server.description}")
            console.print(f"[bold]Command:[/bold] {server.command}")
            console.print(f"[bold]Target Client:[/bold] {client or manager.default_client}")
            console.print(f"[bold]Target Scope:[/bold] {scope}")

            if not Confirm.ask("Do you want to add this server?", default=True):
                console.print(f"[yellow]Cancelled adding {server_id}[/yellow]")
                return

        # Add the server
        if ctx.obj.get('dry_run', False):
            console.print(f"[blue]Would add: {server_id}[/blue]")
            console.print(f"  Client: {client or manager.default_client}")
            console.print(f"  Scope: {scope}")
            console.print(f"  Command: {config.command}")
        else:
            console.print(f"[blue]Adding {server_id} to {scope}...[/blue]")
            result = manager.add_server(server_id, config, scope, client)

            if result.success:
                console.print(f"[green]✓ Successfully added {server_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to add {server_id}: {result.message}[/red]")
                if result.errors and verbose:
                    for error in result.errors:
                        console.print(f"  [red]{error}[/red]")

    except (SystemExit, click.exceptions.Exit):
        # Re-raise exit exceptions to preserve exit codes
        raise
    except Exception as e:
        if verbose:
            console.print(f"[red]Error adding {server_id}: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to add {server_id}: {e}[/red]")


@main.command()
@click.argument('server_id', shell_complete=complete_server_ids)
@click.option('--client', shell_complete=complete_client_names, help='Target client (uses default if not specified)')
@click.option('--scope', type=DynamicScopeType(), help='Source scope (available scopes depend on client, auto-detected if not specified)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def remove(ctx: click.Context, server_id: str, client: Optional[str], scope: Optional[str], dry_run: bool) -> None:
    """Remove an MCP server completely."""
    verbose = ctx.obj.get('verbose', False)

    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True

    try:
        manager = get_mcp_manager(ctx)

        # Find server if scope not specified
        if not scope:
            server_info = manager.get_server_info(server_id, client)
            if server_info:
                scope = server_info.scope
            else:
                console.print(f"[red]Server '{server_id}' not found[/red]")
                return

        # Ask for confirmation
        if not ctx.obj.get('dry_run', False):
            if not Confirm.ask(f"Are you sure you want to remove '{server_id}' from {scope}?", default=False):
                console.print(f"[yellow]Cancelled removing {server_id}[/yellow]")
                return

        # Remove the server
        if ctx.obj.get('dry_run', False):
            console.print(f"[blue]Would remove: {server_id} from {scope}[/blue]")
        else:
            console.print(f"[blue]Removing {server_id} from {scope}...[/blue]")
            result = manager.remove_server(server_id, scope, client)

            if result.success:
                console.print(f"[green]✓ Successfully removed {server_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to remove {server_id}: {result.message}[/red]")

    except Exception as e:
        if verbose:
            console.print(f"[red]Error removing {server_id}: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to remove {server_id}: {e}[/red]")


@main.command()
@click.argument('server_id', shell_complete=complete_server_ids)
@click.option('--client', shell_complete=complete_client_names, help='Target client (uses default if not specified)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def enable(ctx: click.Context, server_id: str, client: Optional[str], dry_run: bool) -> None:
    """Enable a disabled MCP server."""
    verbose = ctx.obj.get('verbose', False)

    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True

    try:
        manager = get_mcp_manager(ctx)

        # Check current state
        current_state = manager.get_server_state(server_id, client)
        if current_state == ServerState.NOT_INSTALLED:
            console.print(f"[red]Server '{server_id}' is not installed[/red]")
            return

        if current_state == ServerState.ENABLED:
            console.print(f"[yellow]Server '{server_id}' is already enabled[/yellow]")
            return

        # Enable the server
        if ctx.obj.get('dry_run', False):
            console.print(f"[blue]Would enable: {server_id}[/blue]")
        else:
            console.print(f"[blue]Enabling {server_id}...[/blue]")
            result = manager.enable_server(server_id, client)

            if result.success:
                console.print(f"[green]✓ Successfully enabled {server_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to enable {server_id}: {result.message}[/red]")

    except Exception as e:
        if verbose:
            console.print(f"[red]Error enabling {server_id}: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to enable {server_id}: {e}[/red]")


@main.command()
@click.argument('server_id', shell_complete=complete_server_ids)
@click.option('--client', shell_complete=complete_client_names, help='Target client (uses default if not specified)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def disable(ctx: click.Context, server_id: str, client: Optional[str], dry_run: bool) -> None:
    """Disable an enabled MCP server."""
    verbose = ctx.obj.get('verbose', False)

    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True

    try:
        manager = get_mcp_manager(ctx)

        # Check current state
        current_state = manager.get_server_state(server_id, client)
        if current_state == ServerState.NOT_INSTALLED:
            console.print(f"[red]Server '{server_id}' is not installed[/red]")
            return

        if current_state == ServerState.DISABLED:
            console.print(f"[yellow]Server '{server_id}' is already disabled[/yellow]")
            return

        # Ask for confirmation
        if not ctx.obj.get('dry_run', False):
            if not Confirm.ask(f"Are you sure you want to disable '{server_id}'?", default=True):
                console.print(f"[yellow]Cancelled disabling {server_id}[/yellow]")
                return

        # Disable the server
        if ctx.obj.get('dry_run', False):
            console.print(f"[blue]Would disable: {server_id}[/blue]")
        else:
            console.print(f"[blue]Disabling {server_id}...[/blue]")
            result = manager.disable_server(server_id, client)

            if result.success:
                console.print(f"[green]✓ Successfully disabled {server_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to disable {server_id}: {result.message}[/red]")

    except Exception as e:
        if verbose:
            console.print(f"[red]Error disabling {server_id}: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to disable {server_id}: {e}[/red]")


@main.command()
@click.argument('server_name', shell_complete=complete_rescope_server_name)
@click.option('--from', 'from_scope', required=True,
              type=DynamicScopeType(),
              help='Source scope to move from')
@click.option('--to', 'to_scope', required=True,
              type=DynamicScopeType(),
              help='Destination scope to move to')
@click.option('--client', default=None,
              shell_complete=complete_client_names,
              help='MCP client to use (auto-detected if not specified)')
@click.option('--dry-run', is_flag=True,
              help='Show what would happen without making changes')
@click.pass_context
def rescope(ctx: click.Context, server_name: str, from_scope: str, to_scope: str, client: Optional[str], dry_run: bool) -> None:
    """Move an MCP server configuration from one scope to another.

    This command allows you to move a server configuration between different
    scopes (e.g., from project-level to user-level). The operation is atomic
    and will rollback if any errors occur.

    Examples:
        mcpi rescope my-server --from project-mcp --to user-global

        mcpi rescope --from project-mcp --to user-internal my-server

        mcpi rescope my-server --from user-global --to project-mcp --dry-run
    """
    verbose = ctx.obj.get('verbose', False)

    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True

    try:
        # Step 1: Get manager and determine client
        manager = get_mcp_manager(ctx)
        client_name = client or manager.default_client

        if not client_name:
            console.print("[red]Error: No client specified and no default client available[/red]")
            ctx.exit(1)

        # Step 2: Validate scopes are different
        if from_scope == to_scope:
            console.print("[red]Error: Source and destination scopes cannot be the same[/red]")
            ctx.exit(1)

        # Step 3: Get client plugin to access scope handlers
        try:
            client_plugin = manager.registry.get_client(client_name)
        except Exception as e:
            console.print(f"[red]Error: Failed to get client '{client_name}': {e}[/red]")
            ctx.exit(1)

        # Step 4: Get scope handlers
        try:
            source_handler = client_plugin.get_scope_handler(from_scope)
            dest_handler = client_plugin.get_scope_handler(to_scope)
        except Exception as e:
            console.print(f"[red]Error: Failed to get scope handlers: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            ctx.exit(1)

        # Step 5: Check server exists in source
        servers_in_source = manager.list_servers(client_name=client_name, scope=from_scope)

        # Find server by checking .id property instead of dictionary keys
        source_server_info = None
        for qualified_id, server_info in servers_in_source.items():
            if server_info.id == server_name:
                source_server_info = server_info
                break

        if source_server_info is None:
            console.print(f"[red]Error: Server '{server_name}' not found in scope '{from_scope}'[/red]")
            ctx.exit(1)

        # Step 6: Check server doesn't exist in destination
        servers_in_dest = manager.list_servers(client_name=client_name, scope=to_scope)

        # Check if server exists in destination
        for qualified_id, server_info in servers_in_dest.items():
            if server_info.id == server_name:
                console.print(f"[red]Error: Server '{server_name}' already exists in scope '{to_scope}'[/red]")
                ctx.exit(1)

        # Step 7: Get server config from source
        server_config = ServerConfig.from_dict(source_server_info.config)

        # Step 8: Dry-run mode
        if ctx.obj.get('dry_run', False):
            console.print(f"[cyan]Dry-run mode: Would rescope server '{server_name}'[/cyan]")
            console.print(f"  From: {from_scope}")
            console.print(f"  To: {to_scope}")
            console.print(f"  Client: {client_name}")
            console.print(f"\n[yellow]No changes made (dry-run mode)[/yellow]")
            ctx.exit(0)

        # Step 9: Execute rescope with transaction safety
        try:
            # Write to destination
            add_result = dest_handler.add_server(server_name, server_config)
            if not add_result.success:
                console.print(f"[red]Error: Failed to add server to destination: {add_result.message}[/red]")
                ctx.exit(1)

            # Remove from source (with rollback on failure)
            try:
                remove_result = source_handler.remove_server(server_name)
                if not remove_result.success:
                    # Rollback: remove from destination
                    dest_handler.remove_server(server_name)
                    console.print(f"[red]Error: Failed to remove from source (rolled back): {remove_result.message}[/red]")
                    ctx.exit(1)
            except Exception as e:
                # Rollback: remove from destination
                dest_handler.remove_server(server_name)
                console.print(f"[red]Error during rescope (rolled back): {str(e)}[/red]")
                if verbose:
                    import traceback
                    console.print(traceback.format_exc())
                ctx.exit(1)
        except Exception as e:
            # If we failed during add, try to clean up if possible
            console.print(f"[red]Error during rescope: {str(e)}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            ctx.exit(1)

        # Step 10: Success output
        console.print(f"[green]✓[/green] Successfully Rescoped server '{server_name}'")
        console.print(f"  From: {from_scope}")
        console.print(f"  To: {to_scope}")
        console.print(f"  Client: {client_name}")

    except (SystemExit, click.exceptions.Exit):
        # Re-raise exit exceptions to preserve exit codes
        raise
    except Exception as e:
        if verbose:
            console.print(f"[red]Error rescoping {server_name}: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to rescope {server_name}: {e}[/red]")
        ctx.exit(1)


@main.command()
@click.argument('server_id', required=False, shell_complete=complete_server_ids)
@click.option('--client', shell_complete=complete_client_names, help='Target client (uses default if not specified)')
@click.pass_context
def info(ctx: click.Context, server_id: Optional[str], client: Optional[str]) -> None:
    """Show detailed information about a server or system status."""
    try:
        manager = get_mcp_manager(ctx)

        if server_id:
            # Show server info
            server_info = manager.get_server_info(server_id, client)
            if not server_info:
                console.print(f"[red]Server '{server_id}' not found[/red]")
                return

            info_text = f"[bold]Server ID:[/bold] {server_info.id}\n"
            info_text += f"[bold]Client:[/bold] {server_info.client}\n"
            info_text += f"[bold]Scope:[/bold] {server_info.scope}\n"
            info_text += f"[bold]State:[/bold] {server_info.state.name}\n"
            info_text += f"[bold]Command:[/bold] {server_info.command}\n"

            if server_info.args:
                info_text += f"[bold]Arguments:[/bold] {' '.join(server_info.args)}\n"

            if server_info.env:
                info_text += f"[bold]Environment Variables:[/bold]\n"
                for key, value in server_info.env.items():
                    info_text += f"  {key}={value}\n"

            console.print(Panel(info_text, title=f"Server Information: {server_id}"))
        else:
            # Show system status
            status = manager.get_status_summary()

            status_text = f"[bold]Default Client:[/bold] {status.get('default_client', 'None')}\n"
            status_text += f"[bold]Available Clients:[/bold] {', '.join(status.get('available_clients', []))}\n"
            status_text += f"[bold]Total Servers:[/bold] {status.get('total_servers', 0)}\n"

            # Server states
            states = status.get('server_states', {})
            if states:
                status_text += f"[bold]Server States:[/bold]\n"
                for state, count in states.items():
                    if count > 0:
                        status_text += f"  {state}: {count}\n"

            # Registry stats
            registry_stats = status.get('registry_stats', {})
            if registry_stats:
                status_text += f"[bold]Registry:[/bold]\n"
                status_text += f"  Clients: {registry_stats.get('total_clients', 0)}\n"
                status_text += f"  Loaded: {registry_stats.get('loaded_instances', 0)}\n"

            console.print(Panel(status_text, title="MCPI Status"))

    except Exception as e:
        console.print(f"[red]Error getting information: {e}[/red]")


# REGISTRY COMMANDS (keep existing ones from old CLI)

@main.group()
@click.pass_context
def registry(ctx: click.Context) -> None:
    """Manage server registry."""
    pass


@registry.command('list')
@click.pass_context
def list_registry(ctx: click.Context) -> None:
    """List all servers in the registry."""
    try:
        registry_manager = get_registry_manager(ctx)
        servers = registry_manager.list_servers()  # Returns list of (server_id, MCPServer) tuples

        if not servers:
            console.print("[yellow]No servers found in registry[/yellow]")
            return

        table = Table(title="Registry Servers")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Command", style="magenta")
        table.add_column("Description", style="white")

        for server_id, server in servers:
            table.add_row(
                server_id,
                server.command,
                server.description[:80] + "..." if len(server.description) > 80 else server.description
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing registry: {e}[/red]")


@registry.command('search')
@click.argument('query', required=False)
@click.option('--limit', default=20, help='Maximum number of results to show')
@click.pass_context
def search(ctx: click.Context, query: Optional[str], limit: int) -> None:
    """Search for MCP servers in the registry."""
    try:
        catalog = get_catalog(ctx)

        # Search servers (returns list of (server_id, MCPServer) tuples)
        if query:
            servers = catalog.search_servers(query)
        else:
            servers = catalog.list_servers()

        # Limit results
        servers = servers[:limit]

        if not servers:
            console.print("[yellow]No servers found matching criteria[/yellow]")
            return

        table = Table(title=f"Registry Search Results ({len(servers)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Command", style="magenta")
        table.add_column("Description", style="white")

        for server_id, server in servers:
            table.add_row(
                server_id,
                server.command,
                server.description[:80] + "..." if len(server.description) > 80 else server.description
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error searching registry: {e}[/red]")


@registry.command('info')
@click.argument('server_id', shell_complete=complete_server_ids)
@click.pass_context
def registry_info(ctx: click.Context, server_id: str) -> None:
    """Show detailed information about a server from the registry."""
    try:
        registry_manager = get_registry_manager(ctx)
        server_info = registry_manager.get_server(server_id)

        if not server_info:
            console.print(f"[red]Server '{server_id}' not found in registry[/red]")
            return

        # Display MCPServer object information (simplified model)
        info_text = f"[bold]ID:[/bold] {server_id}\n"
        info_text += f"[bold]Description:[/bold] {server_info.description}\n"
        info_text += f"[bold]Command:[/bold] {server_info.command}\n"

        if server_info.args:
            info_text += f"[bold]Arguments:[/bold] {' '.join(server_info.args)}\n"

        if server_info.repository:
            info_text += f"[bold]Repository:[/bold] {server_info.repository}\n"

        console.print(Panel(info_text, title=f"Registry Information: {server_id}"))

    except Exception as e:
        console.print(f"[red]Error getting server info: {e}[/red]")


@registry.command('categories')
@click.pass_context
def list_categories(ctx: click.Context) -> None:
    """List all MCP server categories from the registry."""
    try:
        catalog = get_catalog(ctx)
        category_counts = catalog.list_categories()

        if not category_counts:
            console.print("[yellow]No categories found in registry[/yellow]")
            console.print("[dim]Tip: Categories are currently empty. Add category data to servers in registry.json[/dim]")
            return

        table = Table(title="MCP Server Categories")
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Server Count", style="green", justify="right")

        for category, count in sorted(category_counts.items()):
            table.add_row(category, str(count))

        console.print(table)
        console.print(f"\n[dim]Total categories: {len(category_counts)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing categories: {e}[/red]")

# STATUS COMMAND

@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show system status and summary information."""
    try:
        manager = get_mcp_manager(ctx)

        # Get system status
        status_summary = manager.get_status_summary()

        status_text = f"[bold]Default Client:[/bold] {status_summary.get('default_client', 'None')}\n"
        status_text += f"[bold]Available Clients:[/bold] {', '.join(status_summary.get('available_clients', []))}\n"
        status_text += f"[bold]Total Servers:[/bold] {status_summary.get('total_servers', 0)}\n"

        # Server states
        states = status_summary.get('server_states', {})
        if states:
            status_text += f"[bold]Server States:[/bold]\n"
            for state, count in states.items():
                if count > 0:
                    status_text += f"  {state}: {count}\n"

        # Registry stats
        registry_stats = status_summary.get('registry_stats', {})
        if registry_stats:
            status_text += f"[bold]Registry:[/bold]\n"
            status_text += f"  Clients: {registry_stats.get('total_clients', 0)}\n"
            status_text += f"  Loaded: {registry_stats.get('loaded_instances', 0)}\n"

        console.print(Panel(status_text, title="MCPI Status"))

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")


# COMPLETION COMMAND

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
    import os

    # Auto-detect shell if not specified
    if not shell:
        shell_env = os.environ.get('SHELL', '').split('/')[-1]
        if shell_env in ['bash', 'zsh', 'fish']:
            shell = shell_env
        else:
            console.print("[yellow]Could not auto-detect shell. Please specify with --shell[/yellow]")
            console.print("[dim]Examples:[/dim]")
            console.print("  mcpi completion --shell bash")
            console.print("  mcpi completion --shell zsh")
            console.print("  mcpi completion --shell fish")
            ctx.exit(1)

    # Show installation instructions
    console.print(f"\n[cyan]# Tab completion setup for {shell}[/cyan]\n")

    if shell == 'bash':
        console.print("[bold]To enable completion, add to ~/.bashrc:[/bold]")
        console.print('[yellow]eval "$(_MCPI_COMPLETE=bash_source mcpi)"[/yellow]\n')
        console.print("[dim]Then run: source ~/.bashrc[/dim]\n")
    elif shell == 'zsh':
        console.print("[bold]To enable completion, add to ~/.zshrc:[/bold]")
        console.print('[yellow]eval "$(_MCPI_COMPLETE=zsh_source mcpi)"[/yellow]\n')
        console.print("[dim]Then run: source ~/.zshrc[/dim]\n")
    elif shell == 'fish':
        console.print("[bold]To enable completion, add to ~/.config/fish/config.fish:[/bold]")
        console.print('[yellow]eval (env _MCPI_COMPLETE=fish_source mcpi)[/yellow]\n')
        console.print("[dim]Then restart your shell[/dim]\n")


if __name__ == "__main__":
    main()
