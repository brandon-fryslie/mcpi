"""Core type definitions for MCP client system."""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional


class ServerState(Enum):
    """Server state enumeration.

    States:
        ENABLED: Server is approved and enabled
        DISABLED: Server is explicitly disabled by user
        UNAPPROVED: Server exists but hasn't been approved yet (project-mcp only)
        NOT_INSTALLED: Server is not installed in any scope
    """

    ENABLED = auto()
    DISABLED = auto()
    UNAPPROVED = auto()  # For project-mcp servers not yet approved
    NOT_INSTALLED = auto()


@dataclass(frozen=True)
class ScopeConfig:
    """Configuration for a single scope."""

    name: str
    description: str
    priority: int
    path: Optional[Path] = None
    is_user_level: bool = False
    is_project_level: bool = False
    readonly: bool = False

    def __post_init__(self) -> None:
        """Validate scope configuration."""
        if self.is_user_level and self.is_project_level:
            raise ValueError("Scope cannot be both user-level and project-level")


@dataclass
class ServerInfo:
    """Complete information about an MCP server."""

    id: str
    client: str
    scope: str
    config: Dict[str, Any]
    state: ServerState = ServerState.ENABLED
    priority: int = 0

    @property
    def qualified_id(self) -> str:
        """Get fully qualified server ID."""
        return f"{self.client}:{self.scope}:{self.id}"

    @property
    def command(self) -> Optional[str]:
        """Get server command."""
        return self.config.get("command")

    @property
    def args(self) -> List[str]:
        """Get server arguments."""
        return self.config.get("args", [])

    @property
    def env(self) -> Dict[str, str]:
        """Get server environment variables."""
        return self.config.get("env", {})


@dataclass
class ServerConfigBase:
    """Base class for MCP server configurations.

    This defines the common interface for server configurations.
    Subclasses implement specific transport types (stdio, http).
    """

    type: str = field(default="stdio")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        raise NotImplementedError("Subclasses must implement to_dict()")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerConfigBase":
        """Create ServerConfig from dictionary."""
        raise NotImplementedError("Subclasses must implement from_dict()")


@dataclass
class StdioServerConfig(ServerConfigBase):
    """MCP server configuration for stdio transport (local subprocess)."""

    command: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    type: str = field(default="stdio")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "command": self.command,
            "args": self.args,
            "env": self.env,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StdioServerConfig":
        """Create StdioServerConfig from dictionary."""
        return cls(
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env", {}),
            type=data.get("type", "stdio"),
        )


@dataclass
class HttpServerConfig(ServerConfigBase):
    """MCP server configuration for HTTP transport (remote server)."""

    url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    type: str = field(default="http")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "type": self.type,
            "url": self.url,
        }
        if self.headers:
            result["headers"] = self.headers
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HttpServerConfig":
        """Create HttpServerConfig from dictionary."""
        return cls(
            url=data["url"],
            headers=data.get("headers", {}),
            type=data.get("type", "http"),
        )


# Type alias for backwards compatibility
ServerConfig = StdioServerConfig


def parse_server_config(data: Dict[str, Any]) -> ServerConfigBase:
    """Parse a dictionary into the appropriate ServerConfig subclass.

    Args:
        data: Dictionary with server configuration

    Returns:
        StdioServerConfig or HttpServerConfig based on the 'type' field
    """
    server_type = data.get("type", "stdio")
    if server_type == "http":
        return HttpServerConfig.from_dict(data)
    return StdioServerConfig.from_dict(data)


@dataclass
class OperationResult:
    """Result of an operation."""

    success: bool
    message: str
    errors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(cls, message: str, **details: Any) -> "OperationResult":
        """Create a success result."""
        return cls(success=True, message=message, details=details)

    @classmethod
    def failure_result(
        cls, message: str, errors: Optional[List[str]] = None
    ) -> "OperationResult":
        """Create a failure result."""
        return cls(success=False, message=message, errors=errors or [])
