"""MCP Server Registry Catalog and Models."""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .cue_validator import CUEValidator


class InstallationMethod(str, Enum):
    """Supported installation methods."""

    NPX = "npx"  # For npm packages that can be run with npx
    NPM = "npm"  # For npm packages that need global install
    PIP = "pip"  # For Python packages
    UV = "uv"  # For Python packages with uv
    GIT = "git"  # For git repositories
    DOCKER = "docker"  # For docker-based servers


class MCPServer(BaseModel):
    """MCP server registry entry."""

    model_config = ConfigDict(use_enum_values=True)

    # Core fields
    description: str = Field(
        ..., description="Brief description of server functionality"
    )
    command: str = Field(
        ...,
        description="Base command to run the server (e.g., 'npx', 'python', 'node')",
    )
    args: List[str] = Field(
        default_factory=list, description="Arguments for the command"
    )
    repository: Optional[str] = Field(None, description="Git repository URL")
    categories: List[str] = Field(
        default_factory=list, description="Server categories for classification"
    )

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Ensure command is not empty."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()

    def get_install_command(self) -> List[str]:
        """Get the full installation command."""
        # For now, installation is handled by the command and args directly
        # This method may be expanded in the future if needed
        return []

    def get_run_command(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get the full run configuration for Claude Code.

        Args:
            config: User configuration parameters

        Returns:
            Dict with 'command', 'args', and optionally 'env' keys
        """
        if config is None:
            config = {}

        # Start with base command and args
        run_config = {"command": self.command, "args": self.args.copy()}

        # Add environment variables from config if provided
        if config.get("env"):
            run_config["env"] = config["env"]

        return run_config


class ServerRegistry(BaseModel):
    """Complete server registry."""

    model_config = ConfigDict(use_enum_values=True)

    # Direct mapping of server_id -> MCPServer (root model)
    servers: Dict[str, MCPServer] = Field(
        default_factory=dict, description="Server definitions"
    )

    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get a server by ID."""
        return self.servers.get(server_id)

    def list_servers(self) -> List[tuple[str, MCPServer]]:
        """List all servers."""
        return sorted(self.servers.items(), key=lambda x: x[0])

    def search_servers(self, query: str) -> List[tuple[str, MCPServer]]:
        """Search servers by query."""
        query_lower = query.lower()
        results = []

        for server_id, server in self.servers.items():
            # Check ID and description for matches
            if (
                query_lower in server_id.lower()
                or query_lower in server.description.lower()
            ):
                results.append((server_id, server))

        return results

    def list_categories(self) -> Dict[str, int]:
        """List all categories with server counts.

        Returns:
            Dictionary mapping category name to count of servers in that category
        """
        category_counts = {}
        for server_id, server in self.servers.items():
            for category in server.categories:
                category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts


class ServerCatalog:
    """Central catalog for MCP servers."""

    def __init__(
        self, registry_path: Optional[Path] = None, validate_with_cue: bool = True
    ):
        """Initialize the catalog with optional custom registry path.

        Args:
            registry_path: Path to registry file
            validate_with_cue: Whether to validate with CUE schema
        """
        if registry_path is None:
            # Default to package data directory
            package_dir = Path(__file__).parent.parent.parent.parent
            registry_path = package_dir / "data" / "registry.json"

        self.registry_path = registry_path
        self._registry: Optional[ServerRegistry] = None
        self._loaded = False
        self.validate_with_cue = validate_with_cue

        # Initialize CUE validator if validation is enabled
        if self.validate_with_cue:
            try:
                self.cue_validator = CUEValidator()
            except RuntimeError as e:
                print(f"Warning: CUE validation disabled - {e}")
                self.validate_with_cue = False

    def load_registry(self) -> None:
        """Load servers from registry file."""
        if not self.registry_path.exists():
            # Start with empty registry if file doesn't exist
            self._registry = ServerRegistry()
        else:
            # Load based on file extension
            if self.registry_path.suffix.lower() in [".yaml", ".yml"]:
                self._load_yaml_registry()
            else:
                # Default to JSON
                self._load_json_registry()

        self._loaded = True

    def _load_json_registry(self) -> None:
        """Load registry from JSON format."""
        try:
            # Validate with CUE before loading if enabled
            if self.validate_with_cue:
                is_valid, error = self.cue_validator.validate_file(self.registry_path)
                if not is_valid:
                    raise RuntimeError(f"Registry validation failed: {error}")

            with open(self.registry_path, encoding="utf-8") as f:
                data = json.load(f)
            # Convert flat dictionary to ServerRegistry format
            servers = {k: MCPServer(**v) for k, v in data.items()}
            self._registry = ServerRegistry(servers=servers)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load registry from {self.registry_path}: {e}"
            )

    def _load_yaml_registry(self) -> None:
        """Load registry from YAML format."""
        try:
            with open(self.registry_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            # Convert flat dictionary to ServerRegistry format
            servers = {k: MCPServer(**v) for k, v in data.items()}
            self._registry = ServerRegistry(servers=servers)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load YAML registry from {self.registry_path}: {e}"
            )

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
            # Prepare data as flat dictionary
            data = {k: v.model_dump() for k, v in self._registry.servers.items()}

            # Validate with CUE before writing if enabled
            if self.validate_with_cue:
                is_valid, error = self.cue_validator.validate(data)
                if not is_valid:
                    raise RuntimeError(
                        f"Registry validation failed before save: {error}"
                    )

            # Write to file
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Validate file after writing if enabled
            if self.validate_with_cue:
                is_valid, error = self.cue_validator.validate_file(self.registry_path)
                if not is_valid:
                    raise RuntimeError(
                        f"Registry validation failed after save: {error}"
                    )

            return True
        except Exception as e:
            print(f"Error saving JSON registry: {e}")
            return False

    def _save_yaml_registry(self) -> bool:
        """Save registry in YAML format."""
        try:
            yaml_path = self.registry_path.with_suffix(".yaml")
            with open(yaml_path, "w", encoding="utf-8") as f:
                # Export as flat dictionary
                data = {k: v.model_dump() for k, v in self._registry.servers.items()}
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"Error saving YAML registry: {e}")
            return False

    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID."""
        if not self._loaded:
            self.load_registry()
        return self._registry.get_server(server_id)

    def list_servers(self) -> List[tuple[str, MCPServer]]:
        """List all servers."""
        if not self._loaded:
            self.load_registry()
        return self._registry.list_servers()

    def search_servers(self, query: str) -> List[tuple[str, MCPServer]]:
        """Search servers by query string."""
        if not self._loaded:
            self.load_registry()
        return self._registry.search_servers(query)

    def list_categories(self) -> Dict[str, int]:
        """List all categories with server counts.

        Returns:
            Dictionary mapping category name to count of servers in that category
        """
        if not self._loaded:
            self.load_registry()
        return self._registry.list_categories()

    def add_server(self, server_id: str, server: MCPServer) -> bool:
        """Add a server to the catalog."""
        if not self._loaded:
            self.load_registry()

        if server_id in self._registry.servers:
            return False

        self._registry.servers[server_id] = server
        return True

    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the catalog."""
        if not self._loaded:
            self.load_registry()

        if server_id not in self._registry.servers:
            return False

        del self._registry.servers[server_id]
        return True

    def update_server(self, server_id: str, server: MCPServer) -> bool:
        """Update an existing server."""
        if not self._loaded:
            self.load_registry()

        if server_id not in self._registry.servers:
            return False

        self._registry.servers[server_id] = server
        return True
