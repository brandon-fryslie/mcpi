"""Command-line interface for MCPI."""

import asyncio
import json
import sys
from typing import Optional, List, Dict, Any
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt

from mcpi.registry.catalog import ServerCatalog
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.config.manager import ConfigManager
from mcpi.registry.doc_parser import DocumentationParser

console = Console()


def get_method_string(method):
    """Get method as string, handling both enum and string values."""
    return str(method)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.version_option()
@click.pass_context
def main(ctx: click.Context, verbose: bool, dry_run: bool) -> None:
    """MCPI - MCP Server Package Installer."""
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store options in context
    ctx.obj['verbose'] = verbose
    ctx.obj['dry_run'] = dry_run
    
    # Initialize components
    try:
        ctx.obj['catalog'] = ServerCatalog()
        ctx.obj['config_manager'] = ConfigManager()
        ctx.obj['installer'] = ClaudeCodeInstaller(dry_run=dry_run)
    except Exception as e:
        if verbose:
            console.print(f"[red]Initialization error: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Failed to initialize MCPI: {e}[/red]")
        sys.exit(1)


@main.group()
def registry() -> None:
    """Registry management commands."""
    pass


@registry.command('list')
@click.option('--search', '-s', help='Search for servers by name or description')
@click.option('--category', '-c', help='Filter by category')
@click.option('--method', '-m', type=click.Choice(['npm', 'pip', 'git']), help='Filter by installation method')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def registry_list(ctx: click.Context, search: Optional[str], category: Optional[str], 
                 method: Optional[str], output_json: bool) -> None:
    """List available MCP servers in the registry."""
    catalog = ctx.obj['catalog']
    
    try:
        servers = catalog.list_servers()
        
        # Apply filters
        if search:
            search_lower = search.lower()
            servers = [s for s in servers if search_lower in s.name.lower() or 
                      search_lower in s.description.lower()]
        
        if category:
            servers = [s for s in servers if category.lower() in [c.lower() for c in s.category]]
        
        if method:
            servers = [s for s in servers if get_method_string(s.installation.method) == method]
        
        if output_json:
            server_data = [s.model_dump() for s in servers]
            click.echo(json.dumps(server_data, indent=2, default=str))
            return
        
        if not servers:
            console.print("[yellow]No servers found matching criteria[/yellow]")
            return
        
        table = Table(title="Available MCP Servers")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="bold blue")
        table.add_column("Description")
        table.add_column("Method", style="magenta")
        table.add_column("Categories", style="green")
        
        for server in servers:
            table.add_row(
                server.id,
                server.name,
                server.description,
                get_method_string(server.installation.method),
                ", ".join(server.category)
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(servers)} servers[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error listing servers: {e}[/red]")
        sys.exit(1)


@registry.command('show')
@click.argument('server_id')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def registry_show(ctx: click.Context, server_id: str, output_json: bool) -> None:
    """Show detailed information about a specific MCP server."""
    catalog = ctx.obj['catalog']
    
    try:
        server = catalog.get_server(server_id)
        if not server:
            console.print(f"[red]Server '{server_id}' not found in registry[/red]")
            sys.exit(1)
        
        if output_json:
            click.echo(json.dumps(server.model_dump(), indent=2, default=str))
            return
        
        # Display server information in a formatted way
        console.print(f"[bold cyan]{server.name}[/bold cyan] ({server.id})")
        console.print(f"[dim]{server.description}[/dim]\n")
        
        console.print(f"[bold]Version:[/bold] {server.versions.latest}")
        if server.versions.minimum:
            console.print(f"[bold]Minimum Version:[/bold] {server.versions.minimum}")
        
        console.print(f"[bold]Installation Method:[/bold] {get_method_string(server.installation.method)}")
        console.print(f"[bold]Package:[/bold] {server.installation.package}")
        
        if server.category:
            console.print(f"[bold]Categories:[/bold] {', '.join(server.category)}")
        
        if server.configuration.required_params:
            console.print(f"[bold]Required Parameters:[/bold] {', '.join(server.configuration.required_params)}")
        
        if server.configuration.optional_params:
            console.print(f"[bold]Optional Parameters:[/bold] {', '.join(server.configuration.optional_params)}")
        
        if server.documentation:
            console.print(f"[bold]Documentation:[/bold] {server.documentation}")
        
        if server.repository:
            console.print(f"[bold]Source Code:[/bold] {server.repository}")
        
    except Exception as e:
        console.print(f"[red]Error showing server: {e}[/red]")
        sys.exit(1)


@registry.command('search')
@click.argument('query')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def registry_search(ctx: click.Context, query: str, output_json: bool) -> None:
    """Search for MCP servers by name or description."""
    catalog = ctx.obj['catalog']
    
    try:
        results = catalog.search_servers(query)
        
        if output_json:
            # Handle both tuple formats
            result_data = []
            for result in results:
                if len(result) == 2:  # (server, score)
                    s, score = result
                    matches = []
                else:  # (server, score, matches)
                    s, score, matches = result
                result_data.append({
                    "server": s.model_dump(),
                    "score": score,
                    "matches": matches
                })
            click.echo(json.dumps(result_data, indent=2, default=str))
            return
        
        if not results:
            console.print(f"[yellow]No servers found matching '{query}'[/yellow]")
            return
        
        console.print(f"[bold]Search Results for '{query}':[/bold]\n")
        
        for result in results:
            if len(result) == 2:  # (server, score)
                server, score = result
                matches = []
            else:  # (server, score, matches)
                server, score, matches = result
                
            console.print(f"[bold cyan]{server.name}[/bold cyan] ({server.id}) - Score: {score:.2f}")
            console.print(f"[dim]{server.description}[/dim]")
            
            if matches:
                console.print(f"[green]Matches:[/green] {', '.join(matches)}")
            
            console.print(f"[magenta]Method:[/magenta] {get_method_string(server.installation.method)}")
            console.print()
        
    except Exception as e:
        console.print(f"[red]Error searching servers: {e}[/red]")
        sys.exit(1)


@registry.command('validate')
@click.pass_context
def registry_validate(ctx: click.Context) -> None:
    """Validate the registry file."""
    catalog = ctx.obj['catalog']
    
    try:
        errors = catalog.validate_registry()
        
        if not errors:
            console.print("[green]✓ Registry is valid[/green]")
        else:
            console.print(f"[red]Registry validation failed with {len(errors)} errors:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error validating registry: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument('server_ids', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Show what would be installed without making changes')
@click.option('--force', is_flag=True, help='Force installation even if already installed')
@click.pass_context
def install(ctx: click.Context, server_ids: tuple, dry_run: bool, force: bool) -> None:
    """Install one or more MCP servers."""
    if not server_ids:
        console.print("[red]Please specify at least one server ID to install[/red]")
        sys.exit(1)
    
    catalog = ctx.obj['catalog']
    installer = ctx.obj['installer']
    dry_run = dry_run or ctx.obj.get('dry_run', False)
    
    try:
        # Validate all server IDs first
        for server_id in server_ids:
            server = catalog.get_server(server_id)
            if not server:
                console.print(f"[red]Server '{server_id}' not found in registry[/red]")
                sys.exit(1)
        
        # Show installation plan
        console.print("[bold]Installation Plan:[/bold]")
        if dry_run:
            console.print("[yellow]DRY RUN: No actual changes will be made[/yellow]")
        
        for server_id in server_ids:
            server = catalog.get_server(server_id)
            console.print(f"  • {server.name} ({server_id}) via {get_method_string(server.installation.method)}")
        
        if not dry_run and not force:
            if not Confirm.ask("\nProceed with installation?"):
                console.print("Installation cancelled")
                return
        
        # Install each server
        for server_id in server_ids:
            server = catalog.get_server(server_id)
            console.print(f"\n[bold]Installing {server.name} ({server_id})...[/bold]")
            
            with console.status(f"[bold green]Installing {server_id}...") as status:
                result = installer.install(server)
            
            if result.success:
                console.print(f"[green]✓ {result.message}[/green]")
            else:
                console.print(f"[red]✗ {result.message}[/red]")
                sys.exit(1)
        
        console.print(f"\n[bold green]Successfully installed {len(server_ids)} server(s)[/bold green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Installation cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during installation: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument('server_ids', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Show what would be uninstalled without making changes')
@click.pass_context
def uninstall(ctx: click.Context, server_ids: tuple, dry_run: bool) -> None:
    """Uninstall one or more MCP servers."""
    if not server_ids:
        console.print("[red]Please specify at least one server ID to uninstall[/red]")
        sys.exit(1)
    
    installer = ctx.obj['installer']
    dry_run = dry_run or ctx.obj.get('dry_run', False)
    
    try:
        # Show what will be uninstalled
        console.print("[bold]Uninstallation Plan:[/bold]")
        installed = installer.get_installed_servers()
        
        for server_id in server_ids:
            if server_id in installed:
                console.print(f"  • {server_id} [green](installed)[/green]")
            else:
                console.print(f"  • {server_id} [yellow](not installed)[/yellow]")
        
        if dry_run:
            console.print("[yellow]DRY RUN: No actual changes will be made[/yellow]")
            return
        
        if not Confirm.ask("\nProceed with uninstallation?"):
            console.print("Uninstallation cancelled")
            return
        
        console.print(f"[bold]Uninstalling servers...[/bold]")
        if dry_run:
            console.print("[yellow]DRY RUN: No actual changes will be made[/yellow]")
        
        for server_id in server_ids:
            with console.status(f"[bold red]Uninstalling {server_id}...") as status:
                result = installer.uninstall(server_id)
            
            if result.success:
                console.print(f"[green]✓ {result.message}[/green]")
            else:
                console.print(f"[red]✗ {result.message}[/red]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Uninstallation cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during uninstallation: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option('--profile', help='Show status for specific profile')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def status(ctx: click.Context, profile: Optional[str], output_json: bool) -> None:
    """Show status of installed MCP servers."""
    installer = ctx.obj['installer']
    catalog = ctx.obj['catalog']
    
    try:
        installed_servers = installer.get_installed_servers()
        
        if output_json:
            status_data = []
            for server_id in installed_servers:
                server = catalog.get_server(server_id)
                status_data.append({
                    'id': server_id,
                    'name': server.name if server else server_id,
                    'installed': True,
                    'version': server.versions.latest if server else 'unknown'
                })
            click.echo(json.dumps(status_data, indent=2))
            return
        
        if not installed_servers:
            console.print("[yellow]No MCP servers installed[/yellow]")
            return
        
        table = Table(title="Installed MCP Servers")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="bold blue")
        table.add_column("Version", style="magenta")
        table.add_column("Status", style="green")
        
        for server_id in installed_servers:
            server = catalog.get_server(server_id)
            name = server.name if server else server_id
            version = server.versions.latest if server else "unknown"
            status_text = "✓ Installed"
            
            table.add_row(server_id, name, version, status_text)
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(installed_servers)} servers[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        sys.exit(1)


@main.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command('init')
@click.option('--profile', help='Profile name to initialize')
@click.option('--template', type=click.Choice(['development', 'production']), help='Configuration template')
@click.pass_context
def config_init(ctx: click.Context, profile: Optional[str], template: Optional[str]) -> None:
    """Initialize MCPI configuration."""
    config_manager = ctx.obj['config_manager']
    
    try:
        success = config_manager.initialize(profile=profile, template=template)
        if success:
            console.print("[green]✓ Configuration initialized successfully[/green]")
            if profile:
                console.print(f"Created profile: {profile}")
        else:
            console.print("[red]✗ Failed to initialize configuration[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error initializing configuration: {e}[/red]")
        sys.exit(1)


@config.command('show')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def config_show(ctx: click.Context, output_json: bool) -> None:
    """Show current configuration."""
    config_manager = ctx.obj['config_manager']
    
    try:
        config = config_manager.get_config()
        
        if output_json:
            click.echo(json.dumps(config.model_dump(), indent=2, default=str))
            return
        
        console.print("[bold]MCPI Configuration:[/bold]\n")
        
        # General settings
        console.print("[bold cyan]General Settings:[/bold cyan]")
        console.print(f"Registry URL: {config.general.registry_url}")
        console.print(f"Auto-update Registry: {config.general.auto_update_registry}")
        console.print(f"Default Profile: {config.general.default_profile}")
        console.print(f"Cache Directory: {config.general.cache_directory or 'default'}")
        
        # Profiles
        console.print("\n[bold cyan]Profiles:[/bold cyan]")
        for name, profile in config.profiles.items():
            is_default = name == config.general.default_profile
            default_marker = " [bold green](default)[/bold green]" if is_default else ""
            console.print(f"\n[bold]{name}{default_marker}:[/bold]")
            console.print(f"  Target: {profile.target}")
            console.print(f"  Config Path: {profile.config_path or 'auto-detect'}")
            console.print(f"  Install Global: {profile.install_global}")
            console.print(f"  Python Path: {profile.python_path or 'auto-detect'}")
            console.print(f"  Use UV: {profile.use_uv}")
        
        # Logging
        console.print("\n[bold cyan]Logging:[/bold cyan]")
        console.print(f"Level: {config.logging.level}")
        console.print(f"File: {config.logging.file or 'none'}")
        console.print(f"Console: {config.logging.console}")
        
    except Exception as e:
        console.print(f"[red]Error showing configuration: {e}[/red]")
        sys.exit(1)


@config.command('validate')
@click.pass_context
def config_validate(ctx: click.Context) -> None:
    """Validate configuration."""
    config_manager = ctx.obj['config_manager']
    
    try:
        errors = config_manager.validate_config()
        
        if not errors:
            console.print("[green]✓ Configuration is valid[/green]")
        else:
            console.print(f"[red]Configuration validation failed with {len(errors)} errors:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error validating configuration: {e}[/red]")
        sys.exit(1)


@main.command()
@click.pass_context
def update(ctx: click.Context) -> None:
    """Update registry from remote source."""
    catalog = ctx.obj['catalog']
    
    try:
        console.print("[bold]Updating registry from remote source...[/bold]")
        
        with console.status("[bold blue]Downloading registry...") as status:
            success = asyncio.run(catalog.update_registry())
        
        if success:
            servers = catalog.list_servers()
            console.print(f"[green]✓ Registry updated successfully[/green]")
            console.print(f"Registry now contains {len(servers)} servers")
        else:
            console.print("[red]✗ Failed to update registry[/red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Update cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]Error updating registry: {e}[/red]")
        sys.exit(1)


@registry.command('add')
@click.argument('url')
@click.option('--dry-run', is_flag=True, help='Preview extraction without adding to registry')
@click.option('--interactive', '-i', is_flag=True, help='Interactively confirm extracted information')
@click.option('--force', is_flag=True, help='Force add even if server already exists')
@click.pass_context
def registry_add(ctx: click.Context, url: str, dry_run: bool, interactive: bool, force: bool) -> None:
    """Add MCP server to registry by parsing documentation URL.
    
    Extracts server information and installation instructions from documentation URLs 
    (like GitHub README files) and adds them to the local registry.
    """
    catalog = ctx.obj['catalog']
    
    try:
        console.print(f"[bold]Parsing documentation from:[/bold] {url}")
        
        # Parse documentation
        parser = DocumentationParser()
        
        with console.status("[bold blue]Fetching and parsing documentation...") as status:
            server_info = asyncio.run(parser.parse_documentation_url(url))
        
        if not server_info:
            console.print("[red]✗ Failed to extract server information from URL[/red]")
            console.print("Make sure the URL contains MCP server installation instructions")
            sys.exit(1)
        
        # Validate extracted information using the parser's validation
        is_valid, validation_errors = parser.validate_extracted_info(server_info)
        if not is_valid:
            console.print("[red]✗ Extracted server information is invalid:[/red]")
            for error in validation_errors:
                console.print(f"  • {error}")
            
            if not interactive:
                console.print("Use --interactive to manually correct the information")
                sys.exit(1)
        
        # Display extracted information
        console.print(f"\n[bold green]✓ Successfully extracted server information:[/bold green]")
        console.print(f"ID: [cyan]{server_info['id']}[/cyan]")
        console.print(f"Name: [bold]{server_info['name']}[/bold]")
        console.print(f"Description: {server_info['description']}")
        console.print(f"Installation Method: [magenta]{server_info['installation']['method']}[/magenta]")
        console.print(f"Package: {server_info['installation']['package']}")
        
        if server_info.get('documentation_url'):
            console.print(f"Documentation: {server_info['documentation_url']}")
        
        if server_info.get('categories'):
            console.print(f"Categories: {', '.join(server_info['categories'])}")
        
        # Check if server already exists
        existing_server = catalog.get_server(server_info['id'])
        if existing_server and not force:
            console.print(f"[yellow]Server '{server_info['id']}' already exists in registry[/yellow]")
            if not interactive or not Confirm.ask("Do you want to replace it?"):
                console.print("Operation cancelled")
                return
        
        # Interactive mode for corrections
        if interactive:
            console.print("\n[bold]Review and edit information:[/bold]")
            
            # Allow editing of key fields
            server_info['id'] = Prompt.ask("Server ID", default=server_info['id'])
            server_info['name'] = Prompt.ask("Server Name", default=server_info['name'])
            server_info['description'] = Prompt.ask("Description", default=server_info['description'])
            
            # Confirm installation details
            console.print(f"\nInstallation method: {server_info['installation']['method']}")
            console.print(f"Package: {server_info['installation']['package']}")
            
            if not Confirm.ask("Are the installation details correct?"):
                method = Prompt.ask("Installation method", 
                                  choices=['npm', 'pip', 'git'], 
                                  default=server_info['installation']['method'])
                package = Prompt.ask("Package name", default=server_info['installation']['package'])
                server_info['installation']['method'] = method
                server_info['installation']['package'] = package
        
        # Dry run mode
        if dry_run:
            console.print("\n[yellow]DRY RUN: Server would be added with the following information:[/yellow]")
            console.print(json.dumps(server_info, indent=2))
            return
        
        # Add to registry
        success, errors = catalog.add_server(server_info)
        
        if success:
            # Save the updated registry
            if catalog.save_registry():
                console.print(f"\n[green]✓ Successfully added '{server_info['id']}' to registry[/green]")
            else:
                console.print("[red]✗ Failed to save registry file[/red]")
                sys.exit(1)
        else:
            console.print("[red]✗ Failed to add server to registry:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]Error adding server to registry: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()