"""MCP Server Registry Catalog and Models."""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


class InstallationMethod(str, Enum):
    """Supported installation methods."""
    NPX = "npx"  # For npm packages that can be run with npx
    NPM = "npm"  # For npm packages that need global install
    PIP = "pip"  # For Python packages
    UV = "uv"   # For Python packages with uv
    GIT = "git"  # For git repositories
    DOCKER = "docker"  # For docker-based servers


class MCPServer(BaseModel):
    """MCP server registry entry focused on Claude Code usage."""
    model_config = ConfigDict(use_enum_values=True)
    
    # Essential identification
    id: str = Field(..., description="Unique server identifier")
    name: str = Field(..., description="Human-readable server name")
    description: str = Field(..., description="Brief description of server functionality")
    
    # Installation details - exactly what we need to run the server
    command: str = Field(..., description="Base command to run the server (e.g., 'npx', 'python', 'node')")
    package: str = Field(..., description="Package name or path to execute")
    args: List[str] = Field(default_factory=list, description="Default arguments for the command")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables required")
    
    # Installation metadata
    install_method: InstallationMethod = Field(..., description="How to install this server")
    install_package: Optional[str] = Field(None, description="Package name for installation (if different from execution package)")
    install_args: List[str] = Field(default_factory=list, description="Additional args for installation command")
    
    # Configuration
    required_config: List[str] = Field(default_factory=list, description="Required configuration parameters")
    optional_config: Dict[str, Any] = Field(default_factory=dict, description="Optional config with defaults")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for configuration validation")
    
    # Metadata for discovery and management
    categories: List[str] = Field(default_factory=list, description="Categories for grouping")
    keywords: List[str] = Field(default_factory=list, description="Keywords for search")
    
    # Source and documentation
    repository: Optional[str] = Field(None, description="Git repository URL")
    homepage: Optional[str] = Field(None, description="Project homepage")
    documentation: Optional[str] = Field(None, description="Documentation URL")
    
    # Versioning
    version: Optional[str] = Field(None, description="Current/recommended version")
    min_version: Optional[str] = Field(None, description="Minimum supported version")
    
    # Additional metadata
    author: Optional[str] = Field(None, description="Author or organization")
    license: Optional[str] = Field(None, description="License type")
    verified: bool = Field(False, description="Whether this server has been verified to work")
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Ensure command is not empty."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()
    
    @field_validator('package')
    @classmethod
    def validate_package(cls, v: str) -> str:
        """Ensure package is not empty."""
        if not v or not v.strip():
            raise ValueError("Package cannot be empty")
        return v.strip()
    
    def get_install_command(self) -> List[str]:
        """Get the full installation command."""
        if self.install_method == InstallationMethod.NPX:
            # npx can run directly, no install needed
            return []
        elif self.install_method == InstallationMethod.NPM:
            package = self.install_package or self.package
            return ["npm", "install", "-g", package] + self.install_args
        elif self.install_method == InstallationMethod.PIP:
            package = self.install_package or self.package
            return ["pip", "install", package] + self.install_args
        elif self.install_method == InstallationMethod.UV:
            package = self.install_package or self.package
            return ["uv", "pip", "install", package] + self.install_args
        elif self.install_method == InstallationMethod.GIT:
            return ["git", "clone", self.repository or self.package] + self.install_args
        elif self.install_method == InstallationMethod.DOCKER:
            return ["docker", "pull", self.package] + self.install_args
        return []
    
    def get_run_command(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get the full run configuration for Claude Code.
        
        Args:
            config: User configuration parameters
            
        Returns:
            Dict with 'command', 'args', and optionally 'env' keys
        """
        if config is None:
            config = {}
        
        # Start with base command and args
        run_config = {
            "command": self.command,
            "args": [self.package] + self.args.copy()
        }
        
        # Add required config parameters
        for param in self.required_config:
            if param in config:
                run_config["args"].append(str(config[param]))
            else:
                raise ValueError(f"Required configuration parameter '{param}' not provided")
        
        # Add optional config parameters with defaults
        for param, default in self.optional_config.items():
            value = config.get(param, default)
            if value is not None:
                run_config["args"].extend([f"--{param}", str(value)])
        
        # Add environment variables
        if self.env or config.get("env"):
            run_config["env"] = {**self.env, **config.get("env", {})}
        
        return run_config


class ServerRegistry(BaseModel):
    """Complete server registry."""
    model_config = ConfigDict(use_enum_values=True)
    
    version: str = Field(default="2.0.0", description="Registry format version")
    servers: Dict[str, MCPServer] = Field(default_factory=dict, description="Server definitions")
    
    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get a server by ID."""
        return self.servers.get(server_id)
    
    def list_servers(self, category: Optional[str] = None, verified_only: bool = False) -> List[MCPServer]:
        """List servers with optional filters."""
        servers = list(self.servers.values())
        
        if category:
            servers = [s for s in servers if category in s.categories]
        
        if verified_only:
            servers = [s for s in servers if s.verified]
        
        return sorted(servers, key=lambda x: x.name)
    
    def search_servers(self, query: str) -> List[MCPServer]:
        """Search servers by query."""
        query_lower = query.lower()
        results = []
        
        for server in self.servers.values():
            # Check various fields for matches
            if (query_lower in server.id.lower() or
                query_lower in server.name.lower() or
                query_lower in server.description.lower() or
                any(query_lower in cat.lower() for cat in server.categories) or
                any(query_lower in kw.lower() for kw in server.keywords)):
                results.append(server)
        
        return sorted(results, key=lambda x: x.name)


class ServerCatalog:
    """Central catalog for MCP servers."""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize the catalog with optional custom registry path."""
        if registry_path is None:
            # Default to package data directory
            package_dir = Path(__file__).parent.parent.parent.parent
            registry_path = package_dir / "data" / "registry.json"
        
        self.registry_path = registry_path
        self._registry: Optional[ServerRegistry] = None
        self._loaded = False
    
    def load_registry(self) -> None:
        """Load servers from registry file."""
        if not self.registry_path.exists():
            # Start with empty registry if file doesn't exist
            self._registry = ServerRegistry()
        else:
            # Load based on file extension
            if self.registry_path.suffix.lower() in ['.yaml', '.yml']:
                self._load_yaml_registry()
            else:
                # Default to JSON
                self._load_json_registry()
        
        self._loaded = True
    
    def _load_json_registry(self) -> None:
        """Load registry from JSON format."""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._registry = ServerRegistry(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to load registry from {self.registry_path}: {e}")
    
    def _load_yaml_registry(self) -> None:
        """Load registry from YAML format."""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self._registry = ServerRegistry(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to load YAML registry from {self.registry_path}: {e}")
    
    def save_registry(self, format_type: str = "json") -> bool:
        """Save registry to file."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == "yaml":
                return self._save_yaml_registry()
            else:
                return self._save_json_registry()
        except Exception as e:
            print(f"Error saving registry: {e}")
            return False
    
    def _save_json_registry(self) -> bool:
        """Save registry in JSON format."""
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self._registry.model_dump(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving JSON registry: {e}")
            return False
    
    def _save_yaml_registry(self) -> bool:
        """Save registry in YAML format."""
        try:
            yaml_path = self.registry_path.with_suffix('.yaml')
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._registry.model_dump(), f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"Error saving YAML registry: {e}")
            return False
    
    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID."""
        if not self._loaded:
            self.load_registry()
        return self._registry.get_server(server_id)
    
    def list_servers(self, category: Optional[str] = None, verified_only: bool = False) -> List[MCPServer]:
        """List all servers with optional filters."""
        if not self._loaded:
            self.load_registry()
        return self._registry.list_servers(category, verified_only)
    
    def search_servers(self, query: str) -> List[MCPServer]:
        """Search servers by query string."""
        if not self._loaded:
            self.load_registry()
        return self._registry.search_servers(query)
    
    def add_server(self, server: MCPServer) -> bool:
        """Add a server to the catalog."""
        if not self._loaded:
            self.load_registry()
        
        if server.id in self._registry.servers:
            return False
        
        self._registry.servers[server.id] = server
        return True
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the catalog."""
        if not self._loaded:
            self.load_registry()
        
        if server_id not in self._registry.servers:
            return False
        
        del self._registry.servers[server_id]
        return True
    
    def update_server(self, server: MCPServer) -> bool:
        """Update an existing server."""
        if not self._loaded:
            self.load_registry()
        
        if server.id not in self._registry.servers:
            return False
        
        self._registry.servers[server.id] = server
        return True