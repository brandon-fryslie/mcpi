"""Enhanced command-line interface for MCPI with server state management."""

import asyncio
import json
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt

from mcpi.registry.catalog import ServerCatalog, get_method_string
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.installer.stateful_installer import StatefulInstaller
from mcpi.config.manager import ConfigManager
from mcpi.config.client_manager import ClientManager
from mcpi.config.server_state import ServerState
from mcpi.registry.doc_parser import DocumentationParser
from mcpi.registry.manager import RegistryManager

console = Console()


def get_catalog(ctx: click.Context) -> ServerCatalog:
    """Lazy initialization of ServerCatalog."""
    if 'catalog' not in ctx.obj:
        try:
            # Use the same path logic as RegistryManager
            # cli.py is at src/mcpi/cli.py, so 3 levels up gives us the project root
            package_dir = Path(__file__).parent.parent.parent
            toml_registry_path = package_dir / "data" / "registry.toml"
            ctx.obj['catalog'] = ServerCatalog(registry_path=toml_registry_path)
        except Exception as e:
            if ctx.obj.get('verbose', False):
                console.print(f"[red]Catalog initialization error: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to initialize server catalog: {e}[/red]")
            sys.exit(1)
    return ctx.obj['catalog']


def get_config_manager(ctx: click.Context) -> ConfigManager:
    """Lazy initialization of ConfigManager."""
    if 'config_manager' not in ctx.obj:
        try:
            ctx.obj['config_manager'] = ConfigManager()
        except Exception as e:
            if ctx.obj.get('verbose', False):
                console.print(f"[red]Config manager initialization error: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to initialize configuration manager: {e}[/red]")
            sys.exit(1)
    return ctx.obj['config_manager']


def get_client_manager(ctx: click.Context) -> ClientManager:
    """Lazy initialization of ClientManager."""
    if 'client_manager' not in ctx.obj:
        try:
            ctx.obj['client_manager'] = ClientManager()
        except Exception as e:
            if ctx.obj.get('verbose', False):
                console.print(f"[red]Client manager initialization error: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to initialize client manager: {e}[/red]")
            sys.exit(1)
    return ctx.obj['client_manager']


def get_stateful_installer(ctx: click.Context, client: Optional[str] = None) -> StatefulInstaller:
    """Get stateful installer for the specified client."""
    if client is None:
        client_manager = get_client_manager(ctx)
        client = client_manager.get_default_client()
    
    cache_key = f'stateful_installer_{client}'
    if cache_key not in ctx.obj:
        try:
            dry_run = ctx.obj.get('dry_run', False)
            ctx.obj[cache_key] = StatefulInstaller(client=client, dry_run=dry_run)
        except Exception as e:
            if ctx.obj.get('verbose', False):
                console.print(f"[red]Stateful installer initialization error: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to initialize stateful installer: {e}[/red]")
            sys.exit(1)
    return ctx.obj[cache_key]


def get_installer(ctx: click.Context) -> ClaudeCodeInstaller:
    """Lazy initialization of ClaudeCodeInstaller."""
    if 'installer' not in ctx.obj:
        try:
            dry_run = ctx.obj.get('dry_run', False)
            ctx.obj['installer'] = ClaudeCodeInstaller(dry_run=dry_run)
        except Exception as e:
            if ctx.obj.get('verbose', False):
                console.print(f"[red]Installer initialization error: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to initialize installer: {e}[/red]")
            sys.exit(1)
    return ctx.obj['installer']


def get_registry_manager(ctx: click.Context) -> RegistryManager:
    """Lazy initialization of RegistryManager."""
    if 'registry_manager' not in ctx.obj:
        try:
            ctx.obj['registry_manager'] = RegistryManager()
        except Exception as e:
            if ctx.obj.get('verbose', False):
                console.print(f"[red]Registry manager initialization error: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to initialize registry manager: {e}[/red]")
            sys.exit(1)
    return ctx.obj['registry_manager']


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.version_option()
@click.pass_context
def main(ctx: click.Context, verbose: bool, dry_run: bool) -> None:
    """MCPI - MCP Server Package Installer."""
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store options in context (lightweight initialization only)
    ctx.obj['verbose'] = verbose
    ctx.obj['dry_run'] = dry_run
    
    # Components are now initialized lazily when first accessed


# NEW SERVER MANAGEMENT COMMANDS

@main.command()
@click.argument('server_id')
@click.option('--client', help='Target client (overrides default)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def add(ctx: click.Context, server_id: str, client: Optional[str], dry_run: bool) -> None:
    """Add an MCP server from the registry (installs and enables)."""
    verbose = ctx.obj.get('verbose', False)
    
    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True
    
    # Get components
    catalog = get_catalog(ctx)
    stateful_installer = get_stateful_installer(ctx, client)
    
    if verbose:
        console.print(f"[blue]Adding server: {server_id} for client: {stateful_installer.client}[/blue]")
    
    try:
        # Get server info from catalog
        server = catalog.get_server(server_id)
        if not server:
            console.print(f"[red]Server '{server_id}' not found in registry[/red]")
            return
        
        # Check current state
        current_state = stateful_installer.get_server_state(server_id)
        if current_state != ServerState.NOT_INSTALLED:
            console.print(f"[yellow]Server '{server_id}' is already added (state: {current_state.value})[/yellow]")
            return
        
        # Show server info and ask for confirmation (unless dry-run)
        if not ctx.obj.get('dry_run', False):
            console.print(f"\n[bold]Server:[/bold] {server.name}")
            console.print(f"[bold]Description:[/bold] {server.description}")
            console.print(f"[bold]Installation Method:[/bold] {get_method_string(server.installation.method)}")
            
            if not Confirm.ask("Do you want to add this server?", default=True):
                console.print(f"[yellow]Cancelled adding {server_id}[/yellow]")
                return
        
        # Add the server
        if ctx.obj.get('dry_run', False):
            console.print(f"[blue]Would add: {server.name} ({server_id}) for {stateful_installer.client}[/blue]")
            console.print(f"  Method: {get_method_string(server.installation.method)}")
            console.print(f"  Package: {server.installation.package}")
        else:
            console.print(f"[blue]Adding {server.name}...[/blue]")
            result = stateful_installer.add_server(server)
            
            if result.success:
                console.print(f"[green]✓ Successfully added {server_id} (enabled)[/green]")
            else:
                console.print(f"[red]✗ Failed to add {server_id}: {result.message}[/red]")
                
    except Exception as e:
        if verbose:
            console.print(f"[red]Error adding {server_id}: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to add {server_id}: {e}[/red]")


@main.command()
@click.argument('server_id')
@click.option('--client', help='Target client (overrides default)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def disable(ctx: click.Context, server_id: str, client: Optional[str], dry_run: bool) -> None:
    """Disable an MCP server (keeps it installed but inactive)."""
    verbose = ctx.obj.get('verbose', False)
    
    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True
    
    # Get components
    stateful_installer = get_stateful_installer(ctx, client)
    
    if verbose:
        console.print(f"[blue]Disabling server: {server_id} for client: {stateful_installer.client}[/blue]")
    
    try:
        # Check current state
        current_state = stateful_installer.get_server_state(server_id)
        if current_state == ServerState.NOT_INSTALLED:
            console.print(f"[red]Server '{server_id}' is not installed[/red]")
            return
        
        if current_state == ServerState.DISABLED:
            console.print(f"[yellow]Server '{server_id}' is already disabled[/yellow]")
            return
        
        # Ask for confirmation (unless dry-run)
        if not ctx.obj.get('dry_run', False):
            if not Confirm.ask(f"Are you sure you want to disable '{server_id}'?", default=True):
                console.print(f"[yellow]Cancelled disabling {server_id}[/yellow]")
                return
        
        # Disable the server
        if ctx.obj.get('dry_run', False):
            console.print(f"[blue]Would disable: {server_id}[/blue]")
        else:
            console.print(f"[blue]Disabling {server_id}...[/blue]")
            result = stateful_installer.disable_server(server_id)
            
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
@click.argument('server_id')
@click.option('--client', help='Target client (overrides default)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def enable(ctx: click.Context, server_id: str, client: Optional[str], dry_run: bool) -> None:
    """Enable a disabled MCP server."""
    verbose = ctx.obj.get('verbose', False)
    
    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True
    
    # Get components
    stateful_installer = get_stateful_installer(ctx, client)
    
    if verbose:
        console.print(f"[blue]Enabling server: {server_id} for client: {stateful_installer.client}[/blue]")
    
    try:
        # Check current state
        current_state = stateful_installer.get_server_state(server_id)
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
            result = stateful_installer.enable_server(server_id)
            
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
@click.argument('server_id')
@click.option('--client', help='Target client (overrides default)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def remove(ctx: click.Context, server_id: str, client: Optional[str], dry_run: bool) -> None:
    """Remove an MCP server completely (from both enabled and disabled)."""
    verbose = ctx.obj.get('verbose', False)
    
    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True
    
    # Get components
    stateful_installer = get_stateful_installer(ctx, client)
    
    if verbose:
        console.print(f"[blue]Removing server: {server_id} for client: {stateful_installer.client}[/blue]")
    
    try:
        # Check current state
        current_state = stateful_installer.get_server_state(server_id)
        if current_state == ServerState.NOT_INSTALLED:
            console.print(f"[red]Server '{server_id}' is not installed[/red]")
            return
        
        # Ask for confirmation (unless dry-run)
        if not ctx.obj.get('dry_run', False):
            if not Confirm.ask(f"Are you sure you want to completely remove '{server_id}'?", default=False):
                console.print(f"[yellow]Cancelled removing {server_id}[/yellow]")
                return
        
        # Remove the server
        if ctx.obj.get('dry_run', False):
            console.print(f"[blue]Would remove: {server_id}[/blue]")
        else:
            console.print(f"[blue]Removing {server_id}...[/blue]")
            result = stateful_installer.remove_server(server_id)
            
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


@main.group()
@click.pass_context
def set(ctx: click.Context) -> None:
    """Set configuration options."""
    pass


@set.command('default-client')
@click.argument('client')
@click.pass_context
def set_default_client(ctx: click.Context, client: str) -> None:
    """Set the default client for MCPI operations."""
    verbose = ctx.obj.get('verbose', False)
    
    try:
        client_manager = get_client_manager(ctx)
        
        # Validate client
        if not client_manager.is_client_supported(client):
            console.print(f"[red]Unsupported client '{client}'[/red]")
            console.print(f"[yellow]Supported clients: {', '.join(client_manager.get_supported_clients())}[/yellow]")
            return
        
        # Set default client
        if client_manager.set_default_client(client):
            console.print(f"[green]✓ Default client set to '{client}'[/green]")
            if verbose:
                console.print(f"[dim]Config saved to: {client_manager.config_path}[/dim]")
        else:
            console.print(f"[red]Failed to set default client[/red]")
            
    except Exception as e:
        if verbose:
            console.print(f"[red]Error setting default client: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to set default client: {e}[/red]")


# ENHANCED STATUS COMMANDS

@main.command()
@click.option('--client', help='Target client (overrides default)')
@click.option('--state', type=click.Choice(['enabled', 'disabled', 'all']), default='all', 
              help='Filter by server state')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def list(ctx: click.Context, client: Optional[str], state: str, output_json: bool) -> None:
    """List MCP servers with their states."""
    verbose = ctx.obj.get('verbose', False)
    
    # Get components
    stateful_installer = get_stateful_installer(ctx, client)
    
    try:
        all_servers = stateful_installer.list_servers()
        
        # Filter by state if specified
        if state != 'all':
            filtered_servers = {
                server_id: info for server_id, info in all_servers.items() 
                if info['state'].value == state
            }
        else:
            filtered_servers = all_servers
        
        if output_json:
            output_data = {
                "client": stateful_installer.client,
                "servers": {
                    server_id: {
                        "state": info['state'].value,
                        "config": info['config']
                    }
                    for server_id, info in filtered_servers.items()
                }
            }
            console.print(json.dumps(output_data, indent=2))
        else:
            if not filtered_servers:
                console.print(f"[yellow]No servers found with state '{state}' for client '{stateful_installer.client}'[/yellow]")
                return
            
            console.print(f"[bold]MCP Servers for {stateful_installer.client}:[/bold]\n")
            
            table = Table(title=f"Server Status ({state})")
            table.add_column("Server ID", style="cyan")
            table.add_column("State", style="green")
            table.add_column("Command", style="magenta")
            table.add_column("Args")
            
            for server_id, info in filtered_servers.items():
                state_color = "green" if info['state'] == ServerState.ENABLED else "yellow"
                state_text = f"[{state_color}]{info['state'].value}[/{state_color}]"
                
                config = info['config']
                command = config.get('command', 'N/A')
                args = ' '.join(config.get('args', []))
                
                table.add_row(server_id, state_text, command, args)
            
            console.print(table)
            
    except Exception as e:
        if verbose:
            console.print(f"[red]Error listing servers: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to list servers: {e}[/red]")


@main.command()
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def status(ctx: click.Context, output_json: bool) -> None:
    """Show overall MCPI status and configuration."""
    verbose = ctx.obj.get('verbose', False)
    
    try:
        client_manager = get_client_manager(ctx)
        default_client = client_manager.get_default_client()
        stateful_installer = get_stateful_installer(ctx)
        
        all_servers = stateful_installer.list_servers()
        enabled_count = len([s for s in all_servers.values() if s['state'] == ServerState.ENABLED])
        disabled_count = len([s for s in all_servers.values() if s['state'] == ServerState.DISABLED])
        
        if output_json:
            output_data = {
                "default_client": default_client,
                "server_counts": {
                    "enabled": enabled_count,
                    "disabled": disabled_count,
                    "total": enabled_count + disabled_count
                },
                "supported_clients": client_manager.get_supported_clients()
            }
            console.print(json.dumps(output_data, indent=2))
        else:
            console.print(f"[bold]MCPI Status:[/bold]")
            console.print(f"  Default Client: [cyan]{default_client}[/cyan]")
            console.print(f"  Enabled Servers: [green]{enabled_count}[/green]")
            console.print(f"  Disabled Servers: [yellow]{disabled_count}[/yellow]")
            console.print(f"  Total Servers: {enabled_count + disabled_count}")
            console.print(f"  Supported Clients: {', '.join(client_manager.get_supported_clients())}")
            
            if verbose:
                console.print(f"  Client Config: {client_manager.config_path}")
                console.print(f"  Enabled Config: {stateful_installer.state_manager.enabled_config_path}")
                console.print(f"  Disabled Config: {stateful_installer.state_manager.disabled_config_path}")
                
    except Exception as e:
        if verbose:
            console.print(f"[red]Error getting status: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to get status: {e}[/red]")


# KEEP ORIGINAL COMMANDS (for backward compatibility)

@main.command()
@click.argument('server_ids', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Show what would be installed without making changes')
@click.option('--force', is_flag=True, help='Force installation even if already installed')
@click.pass_context
def install(ctx: click.Context, server_ids: tuple, dry_run: bool, force: bool) -> None:
    """Install MCP servers (legacy command - use 'add' instead)."""
    verbose = ctx.obj.get('verbose', False)
    
    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True
    
    # Lazy initialization - only get components when needed
    catalog = get_catalog(ctx)
    installer = get_installer(ctx)
    
    if verbose:
        console.print(f"[blue]Installing servers: {', '.join(server_ids)}[/blue]")
    
    for server_id in server_ids:
        try:
            # Get server info from catalog
            server = catalog.get_server(server_id)
            if not server:
                console.print(f"[yellow]Server '{server_id}' not found in registry[/yellow]")
                continue
            
            # Check if already installed (unless force is True)
            if not force and installer.is_installed(server_id):
                console.print(f"[yellow]Server '{server_id}' is already installed (use --force to reinstall)[/yellow]")
                continue
            
            # Show server info and ask for confirmation (unless dry-run or force)
            if not ctx.obj.get('dry_run', False) and not force:
                console.print(f"\n[bold]Server:[/bold] {server.name}")
                console.print(f"[bold]Description:[/bold] {server.description}")
                console.print(f"[bold]Installation Method:[/bold] {get_method_string(server.installation.method)}")
                
                if not Confirm.ask("Do you want to install this server?", default=True):
                    console.print(f"[yellow]Skipping {server_id}[/yellow]")
                    continue
            
            # Install the server
            if ctx.obj.get('dry_run', False):
                console.print(f"[blue]Would install: {server.name} ({server_id})[/blue]")
                console.print(f"  Method: {get_method_string(server.installation.method)}")
                console.print(f"  Package: {server.installation.package}")
            else:
                console.print(f"[blue]Installing {server.name}...[/blue]")
                result = installer.install(server)
                
                if result.success:
                    console.print(f"[green]✓ Successfully installed {server_id}[/green]")
                else:
                    console.print(f"[red]✗ Failed to install {server_id}: {result.message}[/red]")
                    
        except Exception as e:
            if verbose:
                console.print(f"[red]Error installing {server_id}: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to install {server_id}: {e}[/red]")


@main.command()
@click.argument('server_ids', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Show what would be uninstalled without making changes')
@click.pass_context
def uninstall(ctx: click.Context, server_ids: tuple, dry_run: bool) -> None:
    """Uninstall MCP servers (legacy command - use 'remove' instead)."""
    verbose = ctx.obj.get('verbose', False)
    
    # Update dry_run if passed as command option
    if dry_run:
        ctx.obj['dry_run'] = True
    
    # Lazy initialization
    installer = get_installer(ctx)
    
    if verbose:
        console.print(f"[blue]Uninstalling servers: {', '.join(server_ids)}[/blue]")
    
    for server_id in server_ids:
        try:
            # Check if installed
            if not installer.is_installed(server_id):
                console.print(f"[yellow]Server '{server_id}' is not installed[/yellow]")
                continue
            
            # Ask for confirmation (unless dry-run)
            if not ctx.obj.get('dry_run', False):
                if not Confirm.ask(f"Are you sure you want to uninstall '{server_id}'?", default=False):
                    console.print(f"[yellow]Skipping {server_id}[/yellow]")
                    continue
            
            # Uninstall the server
            if ctx.obj.get('dry_run', False):
                console.print(f"[blue]Would uninstall: {server_id}[/blue]")
            else:
                console.print(f"[blue]Uninstalling {server_id}...[/blue]")
                result = installer.uninstall(server_id)
                
                if result.success:
                    console.print(f"[green]✓ Successfully uninstalled {server_id}[/green]")
                else:
                    console.print(f"[red]✗ Failed to uninstall {server_id}: {result.message}[/red]")
                    
        except Exception as e:
            if verbose:
                console.print(f"[red]Error uninstalling {server_id}: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]Failed to uninstall {server_id}: {e}[/red]")


@main.command()
@click.pass_context
def update(ctx: click.Context) -> None:
    """Update registry from remote source."""
    verbose = ctx.obj.get('verbose', False)
    
    # Lazy initialization - only catalog needed
    catalog = get_catalog(ctx)
    
    try:
        console.print("[blue]Updating server registry...[/blue]")
        
        if catalog.update_registry():
            console.print("[green]✓ Registry updated successfully[/green]")
        else:
            console.print("[yellow]Registry update completed with warnings[/yellow]")
            
    except Exception as e:
        if verbose:
            console.print(f"[red]Update error: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to update registry: {e}[/red]")


@main.group()
@click.pass_context
def registry(ctx: click.Context) -> None:
    """Registry management commands."""
    pass


@registry.command('list')
@click.option('--category', help='Filter by category')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def list_servers(ctx: click.Context, category: Optional[str], output_json: bool) -> None:
    """List available MCP servers."""
    verbose = ctx.obj.get('verbose', False)
    
    # Lazy initialization
    catalog = get_catalog(ctx)
    
    try:
        servers = catalog.list_servers()
        
        if category:
            servers = [s for s in servers if category.lower() in [c.lower() for c in s.category]]
        
        if output_json:
            server_data = [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "category": s.category,
                    "method": get_method_string(s.installation.method),
                    "package": s.installation.package
                }
                for s in servers
            ]
            console.print(json.dumps(server_data, indent=2))
        else:
            if not servers:
                console.print("[yellow]No servers found[/yellow]")
                return
                
            table = Table(title="Available MCP Servers")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description")
            table.add_column("Method", style="magenta")
            table.add_column("Categories", style="yellow")
            
            for server in servers:
                table.add_row(
                    server.id,
                    server.name,
                    server.description[:50] + "..." if len(server.description) > 50 else server.description,
                    get_method_string(server.installation.method),
                    ", ".join(server.category)
                )
            
            console.print(table)
            
    except Exception as e:
        if verbose:
            console.print(f"[red]Error listing servers: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to list servers: {e}[/red]")


@registry.command('search')
@click.argument('query')
@click.option('--limit', default=10, help='Maximum number of results')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def search_servers(ctx: click.Context, query: str, limit: int, output_json: bool) -> None:
    """Search for MCP servers."""
    verbose = ctx.obj.get('verbose', False)
    
    # Lazy initialization
    catalog = get_catalog(ctx)
    
    try:
        results = catalog.search_servers(query)[:limit]
        
        if output_json:
            search_data = [
                {
                    "id": server.id,
                    "name": server.name,
                    "description": server.description,
                    "score": score,
                    "method": get_method_string(server.installation.method),
                    "package": server.installation.package
                }
                for server, score in results
            ]
            console.print(json.dumps(search_data, indent=2))
        else:
            if not results:
                console.print(f"[yellow]No servers found matching '{query}'[/yellow]")
                return
                
            console.print(f"[bold]Search results for '{query}':[/bold]\n")
            
            for server, score in results:
                console.print(f"[cyan]{server.id}[/cyan] - [green]{server.name}[/green]")
                console.print(f"  {server.description}")
                console.print(f"  Method: [magenta]{get_method_string(server.installation.method)}[/magenta] | Package: {server.installation.package}")
                console.print(f"  Score: {score:.2f}")
                console.print()
                
    except Exception as e:
        if verbose:
            console.print(f"[red]Search error: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to search: {e}[/red]")


@registry.command('show')
@click.argument('server_id')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def show_server(ctx: click.Context, server_id: str, output_json: bool) -> None:
    """Show detailed information about a specific server."""
    verbose = ctx.obj.get('verbose', False)
    
    # Lazy initialization
    catalog = get_catalog(ctx)
    
    try:
        server = catalog.get_server(server_id)
        if not server:
            console.print(f"[red]Server '{server_id}' not found[/red]")
            return
        
        if output_json:
            server_data = server.model_dump()
            console.print(json.dumps(server_data, indent=2))
        else:
            console.print(f"[bold cyan]{server.name}[/bold cyan]")
            console.print(f"[bold]ID:[/bold] {server.id}")
            console.print(f"[bold]Description:[/bold] {server.description}")
            console.print(f"[bold]Author:[/bold] {server.author}")
            console.print(f"[bold]Categories:[/bold] {', '.join(server.category)}")
            console.print(f"[bold]License:[/bold] {server.license}")
            console.print(f"[bold]Platforms:[/bold] {', '.join(server.platforms)}")
            
            console.print(f"\n[bold magenta]Installation:[/bold magenta]")
            console.print(f"  Method: {get_method_string(server.installation.method)}")
            console.print(f"  Package: {server.installation.package}")
            
            if server.installation.system_dependencies:
                console.print(f"  System Dependencies: {', '.join(server.installation.system_dependencies)}")
            
            console.print(f"\n[bold yellow]Configuration:[/bold yellow]")
            if server.configuration.required_params:
                console.print(f"  Required Parameters: {', '.join(server.configuration.required_params)}")
            if server.configuration.optional_params:
                console.print(f"  Optional Parameters: {', '.join(server.configuration.optional_params)}")
            
            if server.capabilities:
                console.print(f"\n[bold green]Capabilities:[/bold green] {', '.join(server.capabilities)}")
            
            console.print(f"\n[bold blue]Version Info:[/bold blue]")
            console.print(f"  Latest: {server.versions.latest}")
            console.print(f"  Supported: {', '.join(server.versions.supported)}")
            
            if server.run_config:
                console.print(f"\n[bold red]Run Configuration:[/bold red]")
                console.print(f"  Command: {server.run_config.command}")
                if server.run_config.args:
                    console.print(f"  Args: {', '.join(server.run_config.args)}")
                if server.run_config.env:
                    console.print(f"  Environment: {', '.join([f'{k}={v}' for k, v in server.run_config.env.items()])}")
            
    except Exception as e:
        if verbose:
            console.print(f"[red]Error showing server: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to show server details: {e}[/red]")


@registry.command('add')
@click.argument('url')
@click.option('--non-interactive', is_flag=True, help='Run in non-interactive mode (no prompts)')
@click.pass_context
def add_server(ctx: click.Context, url: str, non_interactive: bool) -> None:
    """Add a server to the registry from a documentation URL."""
    verbose = ctx.obj.get('verbose', False)
    
    # Lazy initialization
    registry_manager = get_registry_manager(ctx)
    
    try:
        # Run the async function
        success, errors = asyncio.run(
            registry_manager.add_server_from_url(url, interactive=not non_interactive)
        )
        
        if success:
            console.print(f"[green]✓ Server successfully added to registry[/green]")
            if verbose:
                console.print(f"[dim]Registry saved to: {registry_manager.registry_path}[/dim]")
        else:
            console.print(f"[red]Failed to add server:[/red]")
            for error in errors:
                console.print(f"  • {error}")
                
    except Exception as e:
        if verbose:
            console.print(f"[red]Error adding server: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to add server: {e}[/red]")


@main.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Configuration management commands."""
    pass


@config.command('init')
@click.option('--profile', default='default', help='Profile name to initialize')
@click.option('--template', help='Configuration template to use')
@click.pass_context
def init_config(ctx: click.Context, profile: str, template: Optional[str]) -> None:
    """Initialize MCPI configuration."""
    verbose = ctx.obj.get('verbose', False)
    
    # Lazy initialization
    config_manager = get_config_manager(ctx)
    
    try:
        if config_manager.initialize(profile=profile, template=template):
            console.print(f"[green]✓ Configuration initialized for profile '{profile}'[/green]")
            if verbose:
                console.print(f"[dim]Config path: {config_manager.config_path}[/dim]")
        else:
            console.print(f"[yellow]Configuration for profile '{profile}' already exists[/yellow]")
            
    except Exception as e:
        if verbose:
            console.print(f"[red]Config initialization error: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to initialize configuration: {e}[/red]")


@config.command('show')
@click.option('--profile', help='Show specific profile')
@click.pass_context
def show_config(ctx: click.Context, profile: Optional[str]) -> None:
    """Show current configuration."""
    verbose = ctx.obj.get('verbose', False)
    
    # Lazy initialization
    config_manager = get_config_manager(ctx)
    
    try:
        config = config_manager.get_config()
        
        console.print(f"[bold]Configuration:[/bold]")
        console.print(f"  Config Path: {config_manager.config_path}")
        console.print(f"  Registry URL: {config.general.registry_url}")
        console.print(f"  Default Profile: {config.general.default_profile}")
        console.print(f"  Auto Update: {config.general.auto_update_registry}")
        
        if hasattr(config, 'profiles') and config.profiles:
            console.print(f"\n[bold]Profiles:[/bold]")
            for name, prof in config.profiles.items():
                if profile and name != profile:
                    continue
                console.print(f"  {name}: target={prof.target}")
                
    except Exception as e:
        if verbose:
            console.print(f"[red]Config show error: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to show configuration: {e}[/red]")


@main.command()
@click.option('--docs-dir', type=click.Path(exists=True), help='Directory containing documentation files')
@click.pass_context
def parse_docs(ctx: click.Context, docs_dir: Optional[str]) -> None:
    """Parse documentation to extract MCP server information."""
    verbose = ctx.obj.get('verbose', False)
    
    try:
        parser = DocumentationParser()
        
        if docs_dir:
            console.print(f"[blue]Parsing documentation from {docs_dir}...[/blue]")
            # This would be implemented to parse from specific directory
            console.print("[yellow]Directory parsing not yet implemented[/yellow]")
        else:
            console.print("[blue]Parsing documentation from default sources...[/blue]")
            # This would parse from configured documentation sources
            console.print("[yellow]Default parsing not yet implemented[/yellow]")
            
    except Exception as e:
        if verbose:
            console.print(f"[red]Documentation parsing error: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to parse documentation: {e}[/red]")


if __name__ == '__main__':
    main()