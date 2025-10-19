"""MCP Server Registry Catalog and Models."""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

# Handle tomllib import for Python 3.11+ or fallback to tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        # Fallback to using toml for reading as well
        tomllib = None

import toml

from mcpi.utils.validation import (
    validate_server_id,
    validate_package_name,
    validate_url,
    validate_license,
    validate_version
)


class InstallationMethod(str, Enum):
    """Supported installation methods."""
    NPM = "npm"
    PIP = "pip"
    GIT = "git"
    BINARY = "binary"
    UNKNOWN = "unknown"


class Platform(str, Enum):
    """Supported platforms."""
    LINUX = "linux"
    DARWIN = "darwin"
    WINDOWS = "windows"


class ServerInstallation(BaseModel):
    """Installation configuration for an MCP server."""
    model_config = ConfigDict(use_enum_values=True)
    
    method: InstallationMethod
    package: str
    system_dependencies: List[str] = Field(default_factory=list)
    python_dependencies: List[str] = Field(default_factory=list)


class ServerConfiguration(BaseModel):
    """Configuration template information for an MCP server."""
    template: Optional[str] = None
    required_params: List[str] = Field(default_factory=list)
    optional_params: List[str] = Field(default_factory=list)


class ServerVersions(BaseModel):
    """Version information for an MCP server."""
    latest: str
    supported: List[str] = Field(default_factory=list)


class RunConfig(BaseModel):
    """Runtime configuration for MCP server execution."""
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)


class MCPServer(BaseModel):
    """Complete MCP server registry entry."""
    model_config = ConfigDict(use_enum_values=True)
    
    id: str
    name: str
    description: str
    author: str
    license: str = "Unknown"
    category: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    
    installation: ServerInstallation
    configuration: ServerConfiguration = Field(default_factory=ServerConfiguration)
    platforms: List[str] = Field(default_factory=lambda: ["linux", "darwin", "windows"])
    versions: ServerVersions = Field(default_factory=lambda: ServerVersions(latest="1.0.0", supported=["1.0.0"]))
    
    repository: Optional[str] = None
    documentation: Optional[str] = None
    homepage: Optional[str] = None
    
    # New RunConfig field for MCP server execution
    run_config: Optional[RunConfig] = None
    
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


def get_method_string(method):
    """Get method as string, handling both enum and string values."""
    if hasattr(method, 'value'):
        return method.value
    return str(method)


class ServerCatalog:
    """Central catalog for MCP servers with search and filtering capabilities."""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize the catalog with optional custom registry path."""
        if registry_path is None:
            # Default to package data directory
            package_dir = Path(__file__).parent.parent.parent.parent
            registry_path = package_dir / "data" / "mcp_servers.json"
        
        self.registry_path = registry_path
        self._servers: Dict[str, MCPServer] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._loaded = False
        
    def load_registry(self) -> None:
        """Load servers from registry file."""
        if not self.registry_path.exists():
            # Try alternative formats if specified file doesn't exist
            if self.registry_path.suffix == '.json':
                # Try TOML and YAML alternatives
                toml_path = self.registry_path.with_suffix('.toml')
                yaml_path = self.registry_path.with_suffix('.yaml')
                
                if toml_path.exists():
                    self._load_toml_registry(toml_path)
                elif yaml_path.exists():
                    self._load_yaml_registry(yaml_path)
                else:
                    # Start with empty registry if no file exists
                    pass
            else:
                # Start with empty registry if specified file doesn't exist
                pass
        else:
            # Load based on file extension
            if self.registry_path.suffix.lower() == '.toml':
                self._load_toml_registry(self.registry_path)
            elif self.registry_path.suffix.lower() in ['.yaml', '.yml']:
                self._load_yaml_registry(self.registry_path)
            else:
                # Default to JSON
                self._load_json_registry()
        
        self._build_category_index()
        self._loaded = True
    
    def _load_json_registry(self) -> None:
        """Load registry from JSON format."""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear existing servers
            self._servers = {}
            
            # Load servers from different possible structures
            if "servers" in data:
                # New structured format
                for server_id, server_data in data["servers"].items():
                    server_data["id"] = server_id
                    server = MCPServer(**server_data)
                    self._servers[server.id] = server
            else:
                # Legacy format - assume data is direct server list
                if isinstance(data, list):
                    for server_data in data:
                        server = MCPServer(**server_data)
                        self._servers[server.id] = server
                elif isinstance(data, dict):
                    # Assume it's server_id -> server_data mapping
                    for server_id, server_data in data.items():
                        server_data["id"] = server_id
                        server = MCPServer(**server_data)
                        self._servers[server.id] = server
                        
        except (json.JSONDecodeError, FileNotFoundError, KeyError, TypeError) as e:
            raise RuntimeError(f"Failed to load registry from {self.registry_path}: {e}")
    
    def _load_toml_registry(self, toml_path: Path) -> None:
        """Load registry from TOML format."""
        try:
            if tomllib is not None:
                # Use tomllib for Python 3.11+ or tomli for older versions
                with open(toml_path, 'rb') as f:
                    data = tomllib.load(f)
            else:
                # Fallback to toml library
                with open(toml_path, 'r', encoding='utf-8') as f:
                    data = toml.load(f)
            
            # Clear existing servers
            self._servers = {}
            
            # Load servers from TOML format
            servers_data = data.get('servers', {})
            for server_id, server_data in servers_data.items():
                server_data['id'] = server_id  # Add ID back
                server = MCPServer(**server_data)
                self._servers[server.id] = server
                
        except Exception as e:
            raise RuntimeError(f"Failed to load TOML registry from {toml_path}: {e}")
    
    def _load_yaml_registry(self, yaml_path: Path) -> None:
        """Load registry from YAML format."""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Clear existing servers
            self._servers = {}
            
            # Load servers from YAML format
            servers_data = data.get('servers', {})
            for server_id, server_data in servers_data.items():
                server_data['id'] = server_id
                server = MCPServer(**server_data)
                self._servers[server.id] = server
                
        except Exception as e:
            raise RuntimeError(f"Failed to load YAML registry from {yaml_path}: {e}")
    
    def _build_category_index(self) -> None:
        """Build category index for faster filtering."""
        self._category_index = {}
        for server_id, server in self._servers.items():
            for category in server.category:
                if category not in self._category_index:
                    self._category_index[category] = []
                self._category_index[category].append(server_id)
    
    def list_servers(self, category: Optional[str] = None) -> List[MCPServer]:
        """List all servers, optionally filtered by category."""
        if not self._loaded:
            self.load_registry()
        
        servers = list(self._servers.values())
        
        if category:
            servers = [s for s in servers if category.lower() in [c.lower() for c in s.category]]
        
        return sorted(servers, key=lambda x: x.name)
    
    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID."""
        if not self._loaded:
            self.load_registry()
        
        return self._servers.get(server_id)
    
    def search_servers(self, query: str) -> List[Tuple[MCPServer, float]]:
        """Search servers by query string with relevance scoring."""
        if not self._loaded:
            self.load_registry()
        
        query_lower = query.lower()
        results = []
        
        for server in self._servers.values():
            score = 0.0
            
            # Exact name match gets highest score
            if query_lower == server.name.lower():
                score = 100.0
            # Name contains query
            elif query_lower in server.name.lower():
                score = 80.0
            # ID contains query
            elif query_lower in server.id.lower():
                score = 70.0
            # Description contains query
            elif query_lower in server.description.lower():
                score = 50.0
            # Category match
            elif any(query_lower in cat.lower() for cat in server.category):
                score = 60.0
            # Capability match
            elif any(query_lower in cap.lower() for cap in server.capabilities):
                score = 40.0
            # Author match
            elif query_lower in server.author.lower():
                score = 30.0
            
            if score > 0:
                results.append((server, score))
        
        # Sort by score descending, then by name
        results.sort(key=lambda x: (-x[1], x[0].name))
        return results
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        if not self._loaded:
            self.load_registry()
        
        return sorted(self._category_index.keys())
    
    def add_server(self, server: MCPServer, validate: bool = True) -> Tuple[bool, List[str]]:
        """Add a server to the catalog.
        
        Args:
            server: Server to add
            validate: Whether to validate the server data
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        if validate:
            # Validate server ID format
            if not validate_server_id(server.id):
                errors.append(f"Invalid server ID format: {server.id}")
            
            # Check for duplicate ID
            if server.id in self._servers:
                errors.append(f"Server with ID '{server.id}' already exists")
            
            # Validate package name if installation method is known
            method_str = get_method_string(server.installation.method)
            if (method_str != "unknown" and
                not validate_package_name(server.installation.package, method_str)):
                errors.append(f"Invalid package name for {method_str}: {server.installation.package}")
            
            # Validate URLs
            if server.repository and not validate_url(server.repository):
                errors.append(f"Invalid repository URL: {server.repository}")
            
            if server.documentation and not validate_url(server.documentation):
                errors.append(f"Invalid documentation URL: {server.documentation}")
            
            if server.homepage and not validate_url(server.homepage):
                errors.append(f"Invalid homepage URL: {server.homepage}")
            
            # Validate license format
            if not validate_license(server.license):
                errors.append(f"Invalid license format: {server.license}")
            
            # Validate version format
            if not validate_version(server.versions.latest):
                errors.append(f"Invalid version format: {server.versions.latest}")
        
        if errors:
            return False, errors
        
        # Add to catalog
        self._servers[server.id] = server
        
        # Update category index
        for category in server.category:
            if category not in self._category_index:
                self._category_index[category] = []
            if server.id not in self._category_index[category]:
                self._category_index[category].append(server.id)
        
        return True, []
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the catalog.
        
        Args:
            server_id: ID of server to remove
            
        Returns:
            True if server was removed, False if not found
        """
        if server_id not in self._servers:
            return False
        
        server = self._servers[server_id]
        
        # Remove from category index
        for category in server.category:
            if category in self._category_index and server_id in self._category_index[category]:
                self._category_index[category].remove(server_id)
                if not self._category_index[category]:
                    del self._category_index[category]
        
        # Remove from servers
        del self._servers[server_id]
        return True
    
    def save_registry(self, format_type: str = "json") -> bool:
        """Save registry to file.
        
        Args:
            format_type: Format to save in ("json", "toml", "yaml")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == "toml":
                return self._save_toml_registry()
            elif format_type == "yaml":
                return self._save_yaml_registry()
            else:
                return self._save_json_registry()
        except Exception as e:
            print(f"Error saving registry: {e}")
            return False
    
    def _save_json_registry(self) -> bool:
        """Save registry in JSON format."""
        try:
            registry_data = {
                "metadata": {
                    "version": "1.0.0",
                    "description": "MCP Server Registry - Comprehensive catalog of Model Context Protocol servers"
                },
                "servers": {}
            }
            
            for server_id, server in self._servers.items():
                server_data = server.model_dump()
                # Remove the ID from the data since it's the key
                server_data.pop('id', None)
                registry_data["servers"][server_id] = server_data
            
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving JSON registry: {e}")
            return False
    
    def _save_toml_registry(self) -> bool:
        """Save registry in TOML format."""
        try:
            registry_data = {
                "metadata": {
                    "version": "1.0.0",
                    "description": "MCP Server Registry - Comprehensive catalog of Model Context Protocol servers"
                },
                "servers": {}
            }
            
            for server_id, server in self._servers.items():
                server_data = server.model_dump()
                # Remove the ID from the data since it's the key
                server_data.pop('id', None)
                registry_data["servers"][server_id] = server_data
            
            toml_path = self.registry_path.with_suffix('.toml')
            with open(toml_path, 'w', encoding='utf-8') as f:
                toml.dump(registry_data, f)
            
            return True
        except Exception as e:
            print(f"Error saving TOML registry: {e}")
            return False
    
    def _save_yaml_registry(self) -> bool:
        """Save registry in YAML format."""
        try:
            registry_data = {
                "metadata": {
                    "version": "1.0.0",
                    "description": "MCP Server Registry - Comprehensive catalog of Model Context Protocol servers"
                },
                "servers": {}
            }
            
            for server_id, server in self._servers.items():
                server_data = server.model_dump()
                # Remove the ID from the data since it's the key
                server_data.pop('id', None)
                registry_data["servers"][server_id] = server_data
            
            yaml_path = self.registry_path.with_suffix('.yaml')
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(registry_data, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            print(f"Error saving YAML registry: {e}")
            return False
    
    def update_registry(self) -> bool:
        """Update registry from remote source (placeholder for future implementation)."""
        # This would fetch updates from a remote registry
        # For now, just return True as a no-op
        return True