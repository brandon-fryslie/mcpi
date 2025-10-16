"""Registry management operations for adding servers from URLs."""

import asyncio
import re
import sys
import toml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

# Handle tomllib import for Python 3.11+ or fallback to tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        # Fallback to using toml for reading as well
        tomllib = None

from mcpi.registry.catalog import ServerCatalog, MCPServer, InstallationMethod, Platform
from mcpi.registry.doc_parser import DocumentationParser
from mcpi.utils.validation import validate_url, validate_server_id, validate_package_name, validate_version, validate_license

console = Console()


class RegistryManager:
    """Manages registry operations including adding servers from URLs."""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize registry manager.
        
        Args:
            registry_path: Path to registry file. If None, uses default location.
        """
        if registry_path is None:
            # Default to TOML format in data directory
            # manager.py is at src/mcpi/registry/manager.py, so 4 levels up gives us the project root
            package_dir = Path(__file__).parent.parent.parent.parent
            self.registry_path = package_dir / "data" / "registry.toml"
        else:
            self.registry_path = registry_path
            
        self.catalog = ServerCatalog(registry_path=self.registry_path)
        self.doc_parser = DocumentationParser()
    
    async def add_server_from_url(self, url: str, interactive: bool = True) -> Tuple[bool, List[str]]:
        """Add a server to the registry from a documentation URL.
        
        Args:
            url: URL to documentation page
            interactive: Whether to prompt user for missing information
            
        Returns:
            Tuple of (success, error_messages)
        """
        if not validate_url(url):
            return False, [f"Invalid URL format: {url}"]
        
        console.print(f"[blue]Fetching content from {url}...[/blue]")
        
        # Parse documentation URL to extract server information
        server_info = await self.doc_parser.parse_documentation_url(url)
        if not server_info:
            return False, [f"Failed to extract server information from {url}"]
        
        console.print("[green]✓ Successfully extracted basic server information[/green]")
        
        # Always prompt for name for mcpmarket.com URLs
        if 'mcpmarket.com' in url and interactive:
            current_name = server_info.get("name", "")
            new_name = Prompt.ask("Server Name", default=current_name) if current_name else Prompt.ask("Server Name")
            if new_name:
                server_info["name"] = new_name
        
        # Validate extracted information
        is_valid, validation_errors = self.doc_parser.validate_server_info(server_info)
        
        if interactive:
            # Show extracted information and prompt for missing/invalid fields
            server_info = await self._interactive_completion(server_info, validation_errors)
            if not server_info:
                return False, ["User cancelled operation"]
        elif not is_valid:
            return False, ["Extracted information is incomplete: " + ", ".join(validation_errors)]
        
        # Create MCPServer instance
        try:
            server = MCPServer(**server_info)
        except Exception as e:
            return False, [f"Failed to create server entry: {str(e)}"]
        
        # Load existing registry if it exists
        if self.registry_path.exists():
            # Try to load TOML format first, then fall back to catalog loading
            if not self.load_registry_toml():
                try:
                    self.catalog.load_registry()
                except Exception:
                    # If both fail, start with empty registry
                    pass
        
        # Add server to catalog
        success, errors = self.catalog.add_server(server, validate=True)
        if not success:
            return False, errors
        
        # Save registry to TOML format
        if not self._save_registry_toml():
            return False, ["Failed to save registry"]
        
        console.print(f"[green]✓ Successfully added server '{server.id}' to registry[/green]")
        return True, []
    
    async def _interactive_completion(self, server_info: Dict[str, Any], validation_errors: List[str]) -> Optional[Dict[str, Any]]:
        """Interactively complete missing server information.
        
        Args:
            server_info: Partially extracted server information
            validation_errors: List of validation errors to address
            
        Returns:
            Completed server information or None if cancelled
        """
        console.print("\n[bold]Extracted Server Information:[/bold]")
        
        # Display current information
        self._display_server_info(server_info)
        
        if validation_errors:
            console.print(f"\n[yellow]Issues found: {len(validation_errors)}[/yellow]")
            for error in validation_errors:
                console.print(f"  • {error}")
        
        console.print("\n[bold]Please provide missing or correct invalid information:[/bold]\n")
        
        # Prompt for required fields
        server_info = await self._prompt_basic_info(server_info)
        server_info = await self._prompt_installation_info(server_info)
        server_info = await self._prompt_metadata(server_info)
        
        # Final validation
        try:
            MCPServer(**server_info)
            console.print("\n[green]✓ All required information provided[/green]")
            return server_info
        except Exception as e:
            console.print(f"\n[red]Validation failed: {e}[/red]")
            if Confirm.ask("Would you like to try again?"):
                return await self._interactive_completion(server_info, [str(e)])
            return None
    
    def _display_server_info(self, server_info: Dict[str, Any]) -> None:
        """Display extracted server information in a table."""
        table = Table(title="Extracted Information")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")
        
        # Basic info
        table.add_row("ID", server_info.get("id", ""), "✓" if server_info.get("id") else "Missing")
        table.add_row("Name", server_info.get("name", ""), "✓" if server_info.get("name") else "Missing")
        table.add_row("Description", server_info.get("description", "")[:50] + "..." if len(server_info.get("description", "")) > 50 else server_info.get("description", ""), "✓" if server_info.get("description") else "Missing")
        table.add_row("Author", server_info.get("author", ""), "✓" if server_info.get("author") else "Missing")
        table.add_row("License", server_info.get("license", ""), "✓" if server_info.get("license") else "Missing")
        
        # Installation info
        installation = server_info.get("installation", {})
        table.add_row("Install Method", installation.get("method", ""), "✓" if installation.get("method") else "Missing")
        table.add_row("Package", installation.get("package", ""), "✓" if installation.get("package") else "Missing")
        
        # RunConfig info
        run_config = server_info.get("run_config", {})
        if run_config:
            table.add_row("RunConfig Command", run_config.get("command", ""), "✓" if run_config.get("command") else "Missing")
            args_str = ", ".join(run_config.get("args", [])) if run_config.get("args") else ""
            table.add_row("RunConfig Args", args_str, "✓" if run_config.get("args") else "Optional")
            env_str = ", ".join([f"{k}={v}" for k, v in run_config.get("env", {}).items()]) if run_config.get("env") else ""
            table.add_row("RunConfig Env", env_str, "✓" if run_config.get("env") else "Optional")
        else:
            table.add_row("RunConfig", "Not found", "Missing")
        
        # Optional info
        table.add_row("Repository", server_info.get("repository", ""), "✓" if server_info.get("repository") else "Optional")
        table.add_row("Documentation", server_info.get("documentation", ""), "✓" if server_info.get("documentation") else "Optional")
        table.add_row("Categories", ", ".join(server_info.get("category", [])), "✓" if server_info.get("category") else "Default")
        table.add_row("Capabilities", ", ".join(server_info.get("capabilities", [])), "✓" if server_info.get("capabilities") else "Default")
        
        console.print(table)
    
    async def _prompt_basic_info(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt for basic server information."""
        # Server ID
        while True:
            current_id = server_info.get("id", "")
            server_id = Prompt.ask("Server ID", default=current_id) if current_id else Prompt.ask("Server ID")
            
            if validate_server_id(server_id):
                server_info["id"] = server_id
                break
            else:
                console.print("[red]Invalid server ID. Use lowercase letters, numbers, hyphens, and underscores only.[/red]")
        
        # Server name - always prompt if not provided
        current_name = server_info.get("name", "")
        if not current_name:
            name = Prompt.ask("Server Name")
            if name:
                server_info["name"] = name
        
        # Description
        current_desc = server_info.get("description", "")
        description = Prompt.ask("Description", default=current_desc) if current_desc else Prompt.ask("Description")
        if description:
            server_info["description"] = description
        
        # Author
        current_author = server_info.get("author", "")
        author = Prompt.ask("Author", default=current_author) if current_author else Prompt.ask("Author")
        if author:
            server_info["author"] = author
        
        return server_info
    
    async def _prompt_installation_info(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt for installation information."""
        installation = server_info.get("installation", {})
        
        # Installation method
        current_method = installation.get("method", "")
        if not current_method or current_method not in ["npm", "pip", "git"]:
            method_choices = ["npm", "pip", "git"]
            console.print("Installation methods:")
            for i, method in enumerate(method_choices, 1):
                console.print(f"  {i}. {method}")
            
            while True:
                choice = IntPrompt.ask("Select installation method", choices=[1, 2, 3])
                method = method_choices[choice - 1]
                installation["method"] = method
                break
        
        # Package name
        current_package = installation.get("package", "")
        while True:
            package = Prompt.ask("Package name", default=current_package) if current_package else Prompt.ask("Package name")
            
            if validate_package_name(package, installation["method"]):
                installation["package"] = package
                break
            else:
                console.print(f"[red]Invalid package name for {installation['method']}.[/red]")
        
        # System dependencies (optional)
        current_deps = installation.get("system_dependencies", [])
        if current_deps:
            deps_str = ", ".join(current_deps)
            new_deps = Prompt.ask("System dependencies (comma-separated)", default=deps_str)
        else:
            new_deps = Prompt.ask("System dependencies (comma-separated)", default="")
        
        if new_deps:
            installation["system_dependencies"] = [dep.strip() for dep in new_deps.split(",") if dep.strip()]
        else:
            installation["system_dependencies"] = []
        
        server_info["installation"] = installation
        return server_info
    
    async def _prompt_metadata(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt for metadata information."""
        # License
        current_license = server_info.get("license", "")
        while True:
            license_name = Prompt.ask("License", default=current_license) if current_license else Prompt.ask("License", default="MIT")
            
            if validate_license(license_name):
                server_info["license"] = license_name
                break
            else:
                console.print("[red]Invalid license format.[/red]")
        
        # Version information
        versions = server_info.get("versions", {})
        current_version = versions.get("latest", "1.0.0")
        
        while True:
            version = Prompt.ask("Latest version", default=current_version)
            if validate_version(version):
                server_info["versions"] = {
                    "latest": version,
                    "supported": [version]
                }
                break
            else:
                console.print("[red]Invalid version format. Use semantic versioning (e.g., 1.0.0).[/red]")
        
        # Categories
        current_categories = server_info.get("category", [])
        if current_categories:
            cats_str = ", ".join(current_categories)
            new_cats = Prompt.ask("Categories (comma-separated)", default=cats_str)
        else:
            new_cats = Prompt.ask("Categories (comma-separated)", default="utilities")
        
        if new_cats:
            server_info["category"] = [cat.strip() for cat in new_cats.split(",") if cat.strip()]
        
        # Capabilities
        current_capabilities = server_info.get("capabilities", [])
        if current_capabilities:
            caps_str = ", ".join(current_capabilities)
            new_caps = Prompt.ask("Capabilities (comma-separated)", default=caps_str)
        else:
            new_caps = Prompt.ask("Capabilities (comma-separated)", default="general")
        
        if new_caps:
            server_info["capabilities"] = [cap.strip() for cap in new_caps.split(",") if cap.strip()]
        
        # Platforms
        current_platforms = server_info.get("platforms", ["linux", "darwin", "windows"])
        platforms_str = ", ".join(current_platforms)
        new_platforms = Prompt.ask("Supported platforms (comma-separated)", default=platforms_str)
        
        if new_platforms:
            server_info["platforms"] = [platform.strip() for platform in new_platforms.split(",") if platform.strip()]
        
        # Optional URLs
        current_repo = server_info.get("repository", "")
        if current_repo:
            repository = Prompt.ask("Repository URL", default=current_repo)
        else:
            repository = Prompt.ask("Repository URL (optional)", default="")
        
        if repository and validate_url(repository):
            server_info["repository"] = repository
        elif repository:
            console.print("[yellow]Invalid repository URL, skipping.[/yellow]")
        
        current_docs = server_info.get("documentation", "")
        if current_docs:
            documentation = Prompt.ask("Documentation URL", default=current_docs)
        else:
            documentation = Prompt.ask("Documentation URL (optional)", default="")
        
        if documentation and validate_url(documentation):
            server_info["documentation"] = documentation
        elif documentation:
            console.print("[yellow]Invalid documentation URL, skipping.[/yellow]")
        
        return server_info
    
    def _save_registry_toml(self) -> bool:
        """Save registry in TOML format.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build TOML structure
            registry_data = {
                "metadata": {
                    "version": "1.0.0",
                    "description": "MCP Server Registry - Comprehensive catalog of Model Context Protocol servers",
                    "updated": "2025-01-01T00:00:00Z"
                },
                "servers": {}
            }
            
            # Add all servers
            for server_id, server in self.catalog._servers.items():
                server_data = server.model_dump()
                # Remove the ID from the data since it's the key
                server_data.pop('id', None)
                registry_data["servers"][server_id] = server_data
            
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write TOML file
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                toml.dump(registry_data, f)
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error saving registry: {e}[/red]")
            return False
    
    def load_registry_toml(self) -> bool:
        """Load registry from TOML format.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.registry_path.exists():
            return False
        
        try:
            if tomllib is not None:
                # Use tomllib for Python 3.11+ or tomli for older versions
                with open(self.registry_path, 'rb') as f:
                    data = tomllib.load(f)
            else:
                # Fallback to toml library
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = toml.load(f)
            
            # Clear existing servers
            self.catalog._servers = {}
            
            # Load servers from TOML format
            servers_data = data.get('servers', {})
            for server_id, server_data in servers_data.items():
                server_data['id'] = server_id  # Add ID back
                server = MCPServer(**server_data)
                self.catalog._servers[server.id] = server
            
            self.catalog._build_category_index()
            self.catalog._loaded = True
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error loading TOML registry: {e}[/red]")
            return False
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """List all servers in the registry.
        
        Returns:
            List of server dictionaries
        """
        try:
            # Ensure catalog is loaded
            if not self.catalog._loaded:
                self.load_registry_toml() or self.catalog.load_registry()
            
            servers = []
            for server_id, server in self.catalog._servers.items():
                # Convert to dictionary format
                if hasattr(server, 'model_dump'):
                    server_dict = server.model_dump()
                else:
                    # Fallback for objects without model_dump
                    server_dict = {
                        'id': getattr(server, 'id', server_id),
                        'name': getattr(server, 'name', 'Unknown'),
                        'description': getattr(server, 'description', ''),
                        'author': getattr(server, 'author', 'Unknown'),
                        'installation': {
                            'method': getattr(getattr(server, 'installation', None), 'method', 'unknown'),
                            'package': getattr(getattr(server, 'installation', None), 'package', '')
                        }
                    }
                servers.append(server_dict)
            
            return servers
            
        except Exception as e:
            console.print(f"[red]Error listing servers: {e}[/red]")
            return []
    
    def search_servers(self, query: str) -> List[Dict[str, Any]]:
        """Search servers by query string.
        
        Args:
            query: Search query
            
        Returns:
            List of matching server dictionaries
        """
        try:
            all_servers = self.list_servers()
            
            if not query:
                return all_servers
            
            query_lower = query.lower()
            matching_servers = []
            
            for server in all_servers:
                # Search in name, description, and tags
                name_match = query_lower in server.get('name', '').lower()
                desc_match = query_lower in server.get('description', '').lower()
                
                # Search in categories/tags
                categories = server.get('category', [])
                if isinstance(categories, str):
                    categories = [categories]
                tag_match = any(query_lower in tag.lower() for tag in categories)
                
                if name_match or desc_match or tag_match:
                    matching_servers.append(server)
            
            return matching_servers
            
        except Exception as e:
            console.print(f"[red]Error searching servers: {e}[/red]")
            return []
    
    def get_server_info(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Server information dictionary or None if not found
        """
        try:
            # Ensure catalog is loaded
            if not self.catalog._loaded:
                self.load_registry_toml() or self.catalog.load_registry()
            
            server = self.catalog._servers.get(server_id)
            if not server:
                return None
            
            # Convert to dictionary format
            if hasattr(server, 'model_dump'):
                return server.model_dump()
            else:
                # Fallback for objects without model_dump
                return {
                    'id': getattr(server, 'id', server_id),
                    'name': getattr(server, 'name', 'Unknown'),
                    'description': getattr(server, 'description', ''),
                    'author': getattr(server, 'author', 'Unknown'),
                    'installation': {
                        'method': getattr(getattr(server, 'installation', None), 'method', 'unknown'),
                        'package': getattr(getattr(server, 'installation', None), 'package', '')
                    },
                    'versions': getattr(server, 'versions', {}),
                    'category': getattr(server, 'category', []),
                    'license': getattr(server, 'license', 'Unknown')
                }
                
        except Exception as e:
            console.print(f"[red]Error getting server info: {e}[/red]")
            return None