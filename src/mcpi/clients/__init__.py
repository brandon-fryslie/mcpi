"""MCP client plugin system."""

from .types import ServerInfo, ServerConfig, ServerState, ScopeConfig, OperationResult
from .base import MCPClientPlugin, ScopeHandler
from .claude_code import ClaudeCodePlugin
from .registry import ClientRegistry
from .manager import MCPManager

__all__ = [
    "ServerInfo",
    "ServerConfig", 
    "ServerState",
    "ScopeConfig",
    "OperationResult",
    "MCPClientPlugin",
    "ScopeHandler",
    "ClaudeCodePlugin",
    "ClientRegistry",
    "MCPManager"
]