"""MCP Server Registry Catalog and Models."""

import json
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .cue_validator import CUEValidator
from mcpi.utils.env_substitution import substitute_headers


class InstallationMethod(str, Enum):
    """Supported installation methods."""

    NPX = "npx"  # For npm packages that can be run with npx
    NPM = "npm"  # For npm packages that need global install
    PIP = "pip"  # For Python packages
    UV = "uv"  # For Python packages with uv
    GIT = "git"  # For git repositories
    DOCKER = "docker"  # For docker-based servers


class TransportType(str, Enum):
    """MCP transport types."""

    STDIO = "stdio"  # Local server spawned as subprocess
    HTTP = "http"  # Remote server accessed via HTTP/SSE


class MCPServerBase(BaseModel):
    """Base class for all MCP server types.

    This defines the common interface and shared fields for MCP servers.
    Subclasses implement specific transport types (stdio, http).
    """

    model_config = ConfigDict(use_enum_values=True)

    # Common fields for all server types
    type: str = Field(..., description="Transport type (stdio, http)")
    description: str = Field(
        ..., description="Brief description of server functionality"
    )
    repository: Optional[str] = Field(None, description="Git repository URL")
    categories: List[str] = Field(
        default_factory=list, description="Server categories for classification"
    )

    def get_install_command(self) -> List[str]:
        """Get the full installation command.

        Override in subclasses that require installation.
        """
        return []

    def get_run_command(
        self, config: Optional[Dict[str, Any]] = None, resolve_env: bool = False
    ) -> Dict[str, Any]:
        """Get the full run configuration for Claude Code.

        Args:
            config: Optional user configuration to merge
            resolve_env: If True, substitute ${ENV_VAR} patterns in values
                        (primarily relevant for HTTP headers with credentials)

        Returns:
            Dict with transport-specific configuration

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError("Subclasses must implement get_run_command()")


class StdioServer(MCPServerBase):
    """MCP server using stdio transport (local subprocess)."""

    type: Literal["stdio"] = Field(
        default="stdio", description="Transport type: stdio for local subprocess"
    )
    command: str = Field(
        ...,
        description="Base command to run the server (e.g., 'npx', 'python', 'node')",
    )
    args: List[str] = Field(
        default_factory=list, description="Arguments for the command"
    )
    env: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Ensure command is not empty."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()

    def get_run_command(
        self, config: Optional[Dict[str, Any]] = None, resolve_env: bool = False
    ) -> Dict[str, Any]:
        """Get the full run configuration for Claude Code.

        Args:
            config: Optional user configuration to merge
            resolve_env: Unused for stdio (no credential patterns to resolve)
        """
        if config is None:
            config = {}

        run_config: Dict[str, Any] = {
            "type": "stdio",
            "command": self.command,
            "args": self.args.copy(),
        }

        # Merge environment variables
        env = {**self.env}
        if config.get("env"):
            env.update(config["env"])
        if env:
            run_config["env"] = env

        return run_config


class HttpServer(MCPServerBase):
    """MCP server using HTTP transport (remote server)."""

    type: Literal["http"] = Field(
        default="http", description="Transport type: http for remote server"
    )
    url: str = Field(..., description="HTTP endpoint URL for the MCP server")
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP headers (e.g., Authorization). Values can use ${ENV_VAR} syntax.",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is not empty and looks like a URL."""
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    def get_run_command(
        self, config: Optional[Dict[str, Any]] = None, resolve_env: bool = False
    ) -> Dict[str, Any]:
        """Get the full run configuration for Claude Code.

        Args:
            config: Optional user configuration to merge
            resolve_env: If True, substitute ${ENV_VAR} patterns in headers
                        with actual environment variable values

        Returns:
            Dict with http transport configuration
        """
        result: Dict[str, Any] = {
            "type": "http",
            "url": self.url,
        }
        if self.headers:
            if resolve_env:
                result["headers"] = substitute_headers(self.headers)
            else:
                result["headers"] = self.headers.copy()
        return result


# Type alias for backwards compatibility and type hints
# Use MCPServerBase for isinstance() checks
MCPServer = MCPServerBase

# Discriminated union type for Pydantic parsing
MCPServerUnion = Annotated[Union[StdioServer, HttpServer], Field(discriminator="type")]


def parse_mcp_server(data: Dict[str, Any]) -> MCPServerBase:
    """Parse a dictionary into the appropriate MCPServer subclass.

    Args:
        data: Dictionary with server configuration

    Returns:
        StdioServer or HttpServer based on the 'type' field
    """
    server_type = data.get("type", "stdio")  # Default to stdio for backwards compat
    if server_type == "http":
        return HttpServer(**data)
    return StdioServer(**data)


class ServerRegistry(BaseModel):
    """Complete server registry."""

    model_config = ConfigDict(use_enum_values=True)

    # Direct mapping of server_id -> MCPServer (uses discriminated union for parsing)
    servers: Dict[str, MCPServerUnion] = Field(
        default_factory=dict, description="Server definitions"
    )

    def get_server(self, server_id: str) -> Optional[MCPServerBase]:
        """Get a server by ID."""
        return self.servers.get(server_id)

    def list_servers(self) -> List[tuple[str, MCPServerBase]]:
        """List all servers."""
        return sorted(self.servers.items(), key=lambda x: x[0])

    def search_servers(self, query: str) -> List[tuple[str, MCPServerBase]]:
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

    def __init__(self, catalog_path: Path, validate_with_cue: bool = True):
        """Initialize the catalog with catalog path.

        Args:
            catalog_path: Path to catalog file (required for DI/testability)
            validate_with_cue: Whether to validate with CUE schema
        """
        self.catalog_path = catalog_path
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

    def load_catalog(self) -> None:
        """Load servers from catalog file."""
        if not self.catalog_path.exists():
            # Start with empty registry if file doesn't exist
            self._registry = ServerRegistry()
        else:
            # Load based on file extension
            if self.catalog_path.suffix.lower() in [".yaml", ".yml"]:
                self._load_yaml_catalog()
            else:
                # Default to JSON
                self._load_json_catalog()

        self._loaded = True

    def _load_json_catalog(self) -> None:
        """Load catalog from JSON format."""
        # Check for JSON decode errors from CUE validation first
        if self.validate_with_cue:
            is_valid, error = self.cue_validator.validate_file(self.catalog_path)
            if not is_valid:
                # Check if it's a JSON decode error from CUE
                if "invalid JSON" in error or "invalid character" in error:
                    # Re-parse with json.load to get proper JSONDecodeError
                    # This preserves the specific exception type for testing
                    try:
                        with open(self.catalog_path, encoding="utf-8") as f:
                            json.load(f)  # This will raise JSONDecodeError
                    except json.JSONDecodeError:
                        # Let JSONDecodeError propagate as-is (don't wrap it)
                        raise
                raise RuntimeError(f"Catalog validation failed: {error}")

        try:
            with open(self.catalog_path, encoding="utf-8") as f:
                data = json.load(f)
            # Convert flat dictionary to ServerRegistry format using discriminated parser
            servers = {k: parse_mcp_server(v) for k, v in data.items()}
            self._registry = ServerRegistry(servers=servers)
        except Exception as e:
            raise RuntimeError(f"Failed to load catalog from {self.catalog_path}: {e}")

    def _load_yaml_catalog(self) -> None:
        """Load catalog from YAML format."""
        try:
            with open(self.catalog_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            # Convert flat dictionary to ServerRegistry format using discriminated parser
            servers = {k: parse_mcp_server(v) for k, v in data.items()}
            self._registry = ServerRegistry(servers=servers)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load YAML catalog from {self.catalog_path}: {e}"
            )

    def save_catalog(self, format_type: str = "json") -> bool:
        """Save catalog to file."""
        try:
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)

            if format_type == "yaml":
                return self._save_yaml_catalog()
            else:
                return self._save_json_catalog()
        except Exception as e:
            print(f"Error saving catalog: {e}")
            return False

    def _save_json_catalog(self) -> bool:
        """Save catalog in JSON format."""
        try:
            # Prepare data as flat dictionary
            data = {k: v.model_dump() for k, v in self._registry.servers.items()}

            # Validate with CUE before writing if enabled
            if self.validate_with_cue:
                is_valid, error = self.cue_validator.validate(data)
                if not is_valid:
                    raise RuntimeError(
                        f"Catalog validation failed before save: {error}"
                    )

            # Write to file
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Validate file after writing if enabled
            if self.validate_with_cue:
                is_valid, error = self.cue_validator.validate_file(self.catalog_path)
                if not is_valid:
                    raise RuntimeError(f"Catalog validation failed after save: {error}")

            return True
        except Exception as e:
            print(f"Error saving JSON catalog: {e}")
            return False

    def _save_yaml_catalog(self) -> bool:
        """Save catalog in YAML format."""
        try:
            yaml_path = self.catalog_path.with_suffix(".yaml")
            with open(yaml_path, "w", encoding="utf-8") as f:
                # Export as flat dictionary
                data = {k: v.model_dump() for k, v in self._registry.servers.items()}
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"Error saving YAML catalog: {e}")
            return False

    def get_server(self, server_id: str) -> Optional[MCPServerBase]:
        """Get server by ID."""
        if not self._loaded:
            self.load_catalog()
        return self._registry.get_server(server_id)

    def list_servers(self) -> List[tuple[str, MCPServerBase]]:
        """List all servers."""
        if not self._loaded:
            self.load_catalog()
        return self._registry.list_servers()

    def search_servers(self, query: str) -> List[tuple[str, MCPServerBase]]:
        """Search servers by query string."""
        if not self._loaded:
            self.load_catalog()
        return self._registry.search_servers(query)

    def list_categories(self) -> Dict[str, int]:
        """List all categories with server counts.

        Returns:
            Dictionary mapping category name to count of servers in that category
        """
        if not self._loaded:
            self.load_catalog()
        return self._registry.list_categories()

    def add_server(self, server_id: str, server: MCPServerBase) -> bool:
        """Add a server to the catalog."""
        if not self._loaded:
            self.load_catalog()

        if server_id in self._registry.servers:
            return False

        self._registry.servers[server_id] = server
        return True

    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the catalog."""
        if not self._loaded:
            self.load_catalog()

        if server_id not in self._registry.servers:
            return False

        del self._registry.servers[server_id]
        return True

    def update_server(self, server_id: str, server: MCPServerBase) -> bool:
        """Update an existing server."""
        if not self._loaded:
            self.load_catalog()

        if server_id not in self._registry.servers:
            return False

        self._registry.servers[server_id] = server
        return True


# Factory Functions for DIP Compliance


def create_default_catalog(validate_with_cue: bool = True) -> ServerCatalog:
    """Create ServerCatalog with default production catalog path.

    .. deprecated::
        Use :func:`create_default_catalog_manager` for multi-catalog support.
        This function is maintained for backward compatibility only.

    This factory function provides the default behavior that was previously
    in ServerCatalog.__init__. Use this for production code that needs
    the standard catalog location.

    Args:
        validate_with_cue: Whether to validate with CUE schema

    Returns:
        ServerCatalog instance configured with production catalog path
    """
    import warnings

    warnings.warn(
        "create_default_catalog() is deprecated. "
        "Use create_default_catalog_manager() from mcpi.registry.catalog_manager for multi-catalog support.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Calculate production catalog path - now inside the package
    package_dir = Path(__file__).parent.parent
    catalog_path = package_dir / "data" / "catalog.json"

    return ServerCatalog(catalog_path=catalog_path, validate_with_cue=validate_with_cue)


def create_test_catalog(
    test_data_path: Path, validate_with_cue: bool = False
) -> ServerCatalog:
    """Create ServerCatalog with custom test data path.

    This factory function makes it easy to create test catalogs with
    isolated test data. Validation is disabled by default for tests.

    Args:
        test_data_path: Path to test catalog file
        validate_with_cue: Whether to validate with CUE schema (default False for tests)

    Returns:
        ServerCatalog instance configured with test data path
    """
    return ServerCatalog(
        catalog_path=test_data_path, validate_with_cue=validate_with_cue
    )


def create_in_memory_catalog(servers: Dict[str, MCPServerBase]) -> ServerCatalog:
    """Create a ServerCatalog with in-memory test data (no file required).

    This is the preferred way to create test catalogs when you don't need
    file persistence. It properly initializes the internal registry structure.

    Args:
        servers: Dictionary mapping server_id to MCPServerBase subclass instances

    Returns:
        ServerCatalog instance with test data loaded

    Example:
        catalog = create_in_memory_catalog({
            "test-server": StdioServer(description="Test", command="npx"),
        })
    """
    # Use a dummy path since we won't be loading from file
    catalog = ServerCatalog(catalog_path=Path("/dev/null"), validate_with_cue=False)
    # Properly initialize the registry with test data
    catalog._registry = ServerRegistry(servers=servers)
    catalog._loaded = True
    return catalog
