"""MCP server catalog management."""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
import httpx
import asyncio

from mcpi.utils.validation import (
    validate_url, validate_server_id, validate_package_name, 
    validate_version, validate_license
)


class InstallationMethod(str, Enum):
    """Supported installation methods."""
    NPM = "npm"
    PIP = "pip"
    GIT = "git"
    BINARY = "binary"


class Platform(str, Enum):
    """Supported platforms."""
    LINUX = "linux"
    DARWIN = "darwin"
    WINDOWS = "windows"


class ServerInstallation(BaseModel):
    """Installation configuration for an MCP server."""
    method: InstallationMethod
    package: str
    system_dependencies: List[str] = Field(default_factory=list)
    python_dependencies: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class ServerConfiguration(BaseModel):
    """Configuration template information for an MCP server."""
    template: Optional[str] = None
    required_params: List[str] = Field(default_factory=list)
    optional_params: List[str] = Field(default_factory=list)


class ServerVersions(BaseModel):
    """Version information for an MCP server."""
    latest: str
    supported: List[str] = Field(default_factory=list)


class MCPServer(BaseModel):
    """Complete MCP server registry entry."""
    id: str = Field(description="Unique identifier for the server")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="Brief description of functionality")
    category: List[str] = Field(default_factory=list, description="Server categories")
    author: str = Field(description="Author or organization")
    repository: Optional[HttpUrl] = Field(default=None, description="Source repository URL")
    documentation: Optional[HttpUrl] = Field(default=None, description="Documentation URL")
    versions: ServerVersions = Field(description="Version information")
    installation: ServerInstallation = Field(description="Installation configuration")
    configuration: ServerConfiguration = Field(default_factory=ServerConfiguration)
    capabilities: List[str] = Field(default_factory=list, description="Server capabilities")
    platforms: List[Platform] = Field(default_factory=list, description="Supported platforms")
    license: str = Field(description="Software license")
    
    class Config:
        use_enum_values = True


class ServerCatalog:
    """Manages the MCP server catalog and registry operations."""
    
    DEFAULT_REGISTRY_URL = "https://registry.mcpi.dev/v1/servers.yaml"
    
    def __init__(self, registry_path: Optional[Path] = None, registry_url: Optional[str] = None):
        """Initialize the server catalog.
        
        Args:
            registry_path: Local path to registry file. If None, uses default data directory.
            registry_url: URL for remote registry updates. If None, uses default.
        """
        self.registry_url = registry_url or self.DEFAULT_REGISTRY_URL
        
        if registry_path is None:
            # Get data directory relative to package
            package_dir = Path(__file__).parent.parent.parent.parent
            # Try YAML first, then JSON for backward compatibility
            yaml_path = package_dir / "data" / "registry.yaml"
            json_path = package_dir / "data" / "registry.json"
            
            if yaml_path.exists():
                self.registry_path = yaml_path
            else:
                self.registry_path = json_path
        else:
            self.registry_path = registry_path
            
        self._servers: Dict[str, MCPServer] = {}
        self._categories: Dict[str, List[str]] = {}
        self._loaded = False
    
    def load_registry(self) -> None:
        """Load the registry from local file."""
        if not self.registry_path.exists():
            self._create_default_registry()
            
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                if self.registry_path.suffix.lower() == '.yaml' or self.registry_path.suffix.lower() == '.yml':
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                
            self._servers = {}
            
            # Handle both new YAML format (dict of servers) and old JSON format (list of servers)
            if 'servers' in data:
                servers_data = data['servers']
                if isinstance(servers_data, dict):
                    # New YAML format: servers is a dict with server_id as keys
                    for server_id, server_data in servers_data.items():
                        server_data['id'] = server_id  # Ensure ID is set
                        server = MCPServer(**server_data)
                        self._servers[server.id] = server
                elif isinstance(servers_data, list):
                    # Old JSON format: servers is a list
                    for server_data in servers_data:
                        server = MCPServer(**server_data)
                        self._servers[server.id] = server
            
            self._build_category_index()
            self._loaded = True
            
        except (json.JSONDecodeError, yaml.YAMLError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid registry format: {e}")
    
    def save_registry(self) -> bool:
        """Save the current registry to file.
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Build registry data structure
            servers_dict = {}
            for server_id, server in self._servers.items():
                server_data = server.model_dump()
                # Remove the ID from the data since it's the key
                server_data.pop('id', None)
                servers_dict[server_id] = server_data
            
            registry_data = {
                "version": "1.0.0",
                "updated": "2025-01-01T00:00:00Z",
                "description": "MCP Server Registry - Comprehensive catalog of Model Context Protocol servers",
                "servers": servers_dict
            }
            
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                if self.registry_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(registry_data, f, default_flow_style=False, sort_keys=False, indent=2)
                else:
                    json.dump(registry_data, f, indent=2, default=str)
            
            return True
            
        except Exception:
            return False
    
    def add_server(self, server: Union[MCPServer, Dict[str, Any]], validate: bool = True) -> Tuple[bool, List[str]]:
        """Add a server to the registry.
        
        Args:
            server: MCPServer instance or dictionary with server data
            validate: Whether to validate the server before adding
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        try:
            if isinstance(server, dict):
                server = MCPServer(**server)
            
            if server.id in self._servers:
                return False, [f"Server with ID '{server.id}' already exists"]
            
            # Validate server if requested
            if validate:
                is_valid, validation_errors = self.validate_server(server)
                if not is_valid:
                    return False, validation_errors
            
            self._servers[server.id] = server
            self._build_category_index()
            
            return True, []
            
        except Exception as e:
            return False, [f"Failed to add server: {str(e)}"]
    
    def update_server(self, server_id: str, server: Union[MCPServer, Dict[str, Any]], validate: bool = True) -> Tuple[bool, List[str]]:
        """Update an existing server in the registry.
        
        Args:
            server_id: ID of server to update
            server: Updated server data
            validate: Whether to validate the server before updating
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        try:
            if isinstance(server, dict):
                server = MCPServer(**server)
            
            if server_id not in self._servers:
                return False, [f"Server with ID '{server_id}' does not exist"]
            
            # Ensure ID matches
            if server.id != server_id:
                return False, [f"Server ID mismatch: {server_id} != {server.id}"]
            
            # Validate server if requested
            if validate:
                is_valid, validation_errors = self.validate_server(server)
                if not is_valid:
                    return False, validation_errors
            
            self._servers[server_id] = server
            self._build_category_index()
            
            return True, []
            
        except Exception as e:
            return False, [f"Failed to update server: {str(e)}"]
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the registry.
        
        Args:
            server_id: ID of server to remove
            
        Returns:
            True if server was removed successfully, False otherwise
        """
        if server_id not in self._servers:
            return False
        
        del self._servers[server_id]
        self._build_category_index()
        return True
    
    def _create_default_registry(self) -> None:
        """Create default registry with core servers."""
        default_servers = {
            "filesystem": {
                "name": "Filesystem MCP Server",
                "description": "Access local filesystem operations",
                "category": ["filesystem", "local", "core"],
                "author": "Anthropic",
                "repository": "https://github.com/anthropics/mcp-server-filesystem",
                "documentation": "https://docs.anthropic.com/mcp/servers/filesystem",
                "versions": {
                    "latest": "1.0.0",
                    "supported": ["1.0.0"]
                },
                "installation": {
                    "method": "npm",
                    "package": "@anthropic/mcp-server-filesystem",
                    "system_dependencies": [],
                    "python_dependencies": []
                },
                "configuration": {
                    "template": "filesystem_template.json",
                    "required_params": ["root_path"],
                    "optional_params": ["allowed_extensions"]
                },
                "capabilities": ["file_operations", "directory_listing"],
                "platforms": ["linux", "darwin", "windows"],
                "license": "MIT"
            },
            "sqlite": {
                "name": "SQLite MCP Server",
                "description": "SQLite database operations",
                "category": ["database", "sqlite", "core"],
                "author": "Anthropic",
                "repository": "https://github.com/anthropics/mcp-server-sqlite",
                "documentation": "https://docs.anthropic.com/mcp/servers/sqlite",
                "versions": {
                    "latest": "1.0.0",
                    "supported": ["1.0.0"]
                },
                "installation": {
                    "method": "npm",
                    "package": "@anthropic/mcp-server-sqlite",
                    "system_dependencies": [],
                    "python_dependencies": []
                },
                "configuration": {
                    "template": "sqlite_template.json",
                    "required_params": ["database_path"],
                    "optional_params": ["readonly"]
                },
                "capabilities": ["database_operations", "sql_queries"],
                "platforms": ["linux", "darwin", "windows"],
                "license": "MIT"
            }
        }
        
        registry_data = {
            "version": "1.0.0",
            "updated": "2025-01-01T00:00:00Z",
            "servers": default_servers
        }
        
        # Ensure directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            if self.registry_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(registry_data, f, default_flow_style=False, sort_keys=False, indent=2)
            else:
                json.dump(registry_data, f, indent=2, default=str)
    
    def _build_category_index(self) -> None:
        """Build category index for faster lookups."""
        self._categories = {}
        for server in self._servers.values():
            for category in server.category:
                if category not in self._categories:
                    self._categories[category] = []
                self._categories[category].append(server.id)
    
    def _ensure_loaded(self) -> None:
        """Ensure registry is loaded."""
        if not self._loaded:
            self.load_registry()
    
    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID.
        
        Args:
            server_id: Server identifier
            
        Returns:
            MCPServer instance or None if not found
        """
        self._ensure_loaded()
        return self._servers.get(server_id)
    
    def list_servers(self, category: Optional[str] = None, platform: Optional[str] = None) -> List[MCPServer]:
        """List available servers with optional filtering.
        
        Args:
            category: Filter by category
            platform: Filter by platform
            
        Returns:
            List of matching servers
        """
        self._ensure_loaded()
        servers = list(self._servers.values())
        
        if category:
            servers = [s for s in servers if category in s.category]
            
        if platform:
            servers = [s for s in servers if platform in s.platforms]
            
        return sorted(servers, key=lambda x: x.name)
    
    def search_servers(self, query: str) -> List[MCPServer]:
        """Search servers by name, description, or capabilities.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching servers
        """
        self._ensure_loaded()
        query_lower = query.lower()
        matches = []
        
        for server in self._servers.values():
            # Check name
            if query_lower in server.name.lower():
                matches.append((server, 3))  # High priority for name matches
                continue
                
            # Check description
            if query_lower in server.description.lower():
                matches.append((server, 2))  # Medium priority for description
                continue
                
            # Check capabilities
            if any(query_lower in cap.lower() for cap in server.capabilities):
                matches.append((server, 1))  # Lower priority for capability matches
                continue
                
            # Check categories
            if any(query_lower in cat.lower() for cat in server.category):
                matches.append((server, 1))
        
        # Sort by relevance (priority) and then by name
        matches.sort(key=lambda x: (-x[1], x[0].name))
        return [match[0] for match in matches]
    
    def get_categories(self) -> List[str]:
        """Get all available categories.
        
        Returns:
            Sorted list of category names
        """
        self._ensure_loaded()
        return sorted(self._categories.keys())
    
    def get_servers_by_category(self, category: str) -> List[MCPServer]:
        """Get all servers in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of servers in the category
        """
        self._ensure_loaded()
        if category not in self._categories:
            return []
            
        server_ids = self._categories[category]
        return [self._servers[sid] for sid in server_ids]
    
    async def update_registry(self) -> bool:
        """Update registry from remote source.
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.registry_url, timeout=30.0)
                response.raise_for_status()
                
                # Determine format from URL or content type
                content_type = response.headers.get('content-type', '')
                if 'yaml' in content_type or self.registry_url.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(response.text)
                else:
                    data = response.json()
                
                # Validate the downloaded registry
                if 'servers' in data:
                    servers_data = data['servers']
                    if isinstance(servers_data, dict):
                        for server_id, server_data in servers_data.items():
                            server_data['id'] = server_id
                            MCPServer(**server_data)  # Validate
                    elif isinstance(servers_data, list):
                        for server_data in servers_data:
                            MCPServer(**server_data)  # Validate
                
                # Backup current registry
                backup_path = self.registry_path.with_suffix('.backup')
                if self.registry_path.exists():
                    import shutil
                    shutil.copy2(self.registry_path, backup_path)
                
                # Write new registry
                with open(self.registry_path, 'w', encoding='utf-8') as f:
                    if self.registry_path.suffix.lower() in ['.yaml', '.yml']:
                        yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
                    else:
                        json.dump(data, f, indent=2, default=str)
                
                # Reload the registry
                self.load_registry()
                return True
                
        except (httpx.RequestError, httpx.HTTPStatusError, json.JSONDecodeError, yaml.YAMLError, ValueError):
            return False
    
    def validate_server(self, server: MCPServer) -> Tuple[bool, List[str]]:
        """Validate a single server for comprehensive correctness.
        
        Args:
            server: Server to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate server ID
        if not validate_server_id(server.id):
            errors.append(f"Invalid server ID format: '{server.id}'. Must be lowercase alphanumeric with hyphens/underscores.")
        
        # Validate required fields are not empty/None
        if not server.name or not server.name.strip():
            errors.append("Server name cannot be empty")
        elif len(server.name) > 100:
            errors.append("Server name too long (max 100 characters)")
        
        if not server.description or not server.description.strip():
            errors.append("Server description cannot be empty")
        elif len(server.description) > 500:
            errors.append("Server description too long (max 500 characters)")
        
        if not server.author or not server.author.strip():
            errors.append("Server author cannot be empty")
        elif len(server.author) > 100:
            errors.append("Server author too long (max 100 characters)")
        
        # Validate installation configuration
        if not server.installation.package or not server.installation.package.strip():
            errors.append("Installation package cannot be empty")
        elif not validate_package_name(server.installation.package, server.installation.method):
            errors.append(f"Invalid package name '{server.installation.package}' for method '{server.installation.method}'")
        
        # Validate installation method
        valid_methods = ["npm", "pip", "git"]
        if server.installation.method not in valid_methods:
            errors.append(f"Invalid installation method '{server.installation.method}'. Must be one of: {', '.join(valid_methods)}")
        
        # Validate version information
        if not validate_version(server.versions.latest):
            errors.append(f"Invalid latest version format: '{server.versions.latest}'")
        
        for version in server.versions.supported:
            if not validate_version(version):
                errors.append(f"Invalid supported version format: '{version}'")
        
        # Validate platforms
        valid_platforms = ["linux", "darwin", "windows"]
        if not server.platforms:
            errors.append("At least one platform must be specified")
        else:
            invalid_platforms = [p for p in server.platforms if p not in valid_platforms]
            if invalid_platforms:
                errors.append(f"Invalid platforms: {', '.join(invalid_platforms)}. Valid platforms: {', '.join(valid_platforms)}")
        
        # Validate license
        if not validate_license(server.license):
            errors.append(f"Invalid license format: '{server.license}'")
        
        # Validate URLs if present
        if server.repository and not validate_url(str(server.repository)):
            errors.append(f"Invalid repository URL: '{server.repository}'")
        
        if server.documentation and not validate_url(str(server.documentation)):
            errors.append(f"Invalid documentation URL: '{server.documentation}'")
        
        # Validate categories
        if not server.category:
            errors.append("At least one category must be specified")
        else:
            for category in server.category:
                if not category or not category.strip():
                    errors.append("Category names cannot be empty")
                elif len(category) > 50:
                    errors.append(f"Category name too long: '{category}' (max 50 characters)")
        
        # Validate capabilities
        for capability in server.capabilities:
            if not capability or not capability.strip():
                errors.append("Capability names cannot be empty")
            elif len(capability) > 100:
                errors.append(f"Capability name too long: '{capability}' (max 100 characters)")
        
        # Validate system dependencies
        for dep in server.installation.system_dependencies:
            if not dep or not dep.strip():
                errors.append("System dependency names cannot be empty")
            elif len(dep) > 100:
                errors.append(f"System dependency name too long: '{dep}' (max 100 characters)")
        
        # Validate python dependencies
        for dep in server.installation.python_dependencies:
            if not dep or not dep.strip():
                errors.append("Python dependency names cannot be empty")
            elif not validate_package_name(dep, "pip"):
                errors.append(f"Invalid Python dependency name: '{dep}'")
        
        # Validate configuration parameters
        for param in server.configuration.required_params:
            if not param or not param.strip():
                errors.append("Required parameter names cannot be empty")
            elif len(param) > 100:
                errors.append(f"Required parameter name too long: '{param}' (max 100 characters)")
        
        for param in server.configuration.optional_params:
            if not param or not param.strip():
                errors.append("Optional parameter names cannot be empty")
            elif len(param) > 100:
                errors.append(f"Optional parameter name too long: '{param}' (max 100 characters)")
        
        return len(errors) == 0, errors
    
    def validate_registry(self) -> List[str]:
        """Validate the current registry for errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        self._ensure_loaded()
        
        for server_id, server in self._servers.items():
            # Check for duplicate IDs (shouldn't happen with dict, but good to verify)
            if server.id != server_id:
                errors.append(f"Server ID mismatch: {server_id} != {server.id}")
            
            # Validate each server comprehensively
            is_valid, server_errors = self.validate_server(server)
            if not is_valid:
                for error in server_errors:
                    errors.append(f"Server {server_id}: {error}")
        
        return errors