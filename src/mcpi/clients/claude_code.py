"""Claude Code MCP client plugin implementation."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from .base import MCPClientPlugin, ScopeHandler
from .file_based import FileBasedScope, JSONFileReader, JSONFileWriter, YAMLSchemaValidator
from .types import ServerInfo, ServerConfig, ServerState, ScopeConfig, OperationResult


class ClaudeCodePlugin(MCPClientPlugin):
    """Claude Code MCP client plugin."""
    
    def _get_name(self) -> str:
        """Return the client name."""
        return "claude-code"
    
    def _initialize_scopes(self) -> Dict[str, ScopeHandler]:
        """Initialize and return scope handlers for Claude Code."""
        scopes = {}
        
        # Get the schemas directory path
        schemas_dir = Path(__file__).parent / "schemas"
        
        # Project-level MCP configuration (.mcp.json)
        scopes["project-mcp"] = FileBasedScope(
            config=ScopeConfig(
                name="project-mcp",
                description="Project-level MCP configuration (.mcp.json)",
                priority=1,
                path=Path.cwd() / ".mcp.json",
                is_project_level=True
            ),
            reader=JSONFileReader(),
            writer=JSONFileWriter(),
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "mcp-config-schema.yaml"
        )
        
        # Project-local Claude settings (.claude/settings.local.json)
        scopes["project-local"] = FileBasedScope(
            config=ScopeConfig(
                name="project-local",
                description="Project-local Claude settings (.claude/settings.local.json)",
                priority=2,
                path=Path.cwd() / ".claude" / "settings.local.json",
                is_project_level=True
            ),
            reader=JSONFileReader(),
            writer=JSONFileWriter(),
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "claude-settings-schema.yaml"
        )
        
        # User-local Claude settings (~/.claude/settings.local.json)
        scopes["user-local"] = FileBasedScope(
            config=ScopeConfig(
                name="user-local",
                description="User-local Claude settings (~/.claude/settings.local.json)",
                priority=3,
                path=Path.home() / ".claude" / "settings.local.json",
                is_user_level=True
            ),
            reader=JSONFileReader(),
            writer=JSONFileWriter(),
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "claude-settings-schema.yaml"
        )
        
        # User-global Claude settings (~/.claude/settings.json)
        scopes["user-global"] = FileBasedScope(
            config=ScopeConfig(
                name="user-global",
                description="User-global Claude settings (~/.claude/settings.json)",
                priority=4,
                path=Path.home() / ".claude" / "settings.json",
                is_user_level=True
            ),
            reader=JSONFileReader(),
            writer=JSONFileWriter(),
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "claude-settings-schema.yaml"
        )
        
        # User internal configuration (~/.claude.json)
        scopes["user-internal"] = FileBasedScope(
            config=ScopeConfig(
                name="user-internal",
                description="User internal Claude configuration (~/.claude.json)",
                priority=5,
                path=Path.home() / ".claude.json",
                is_user_level=True
            ),
            reader=JSONFileReader(),
            writer=JSONFileWriter(),
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "internal-config-schema.yaml"
        )
        
        # User MCP servers configuration (~/.claude/mcp_servers.json)
        scopes["user-mcp"] = FileBasedScope(
            config=ScopeConfig(
                name="user-mcp",
                description="User MCP servers configuration (~/.claude/mcp_servers.json)",
                priority=6,
                path=Path.home() / ".claude" / "mcp_servers.json",
                is_user_level=True
            ),
            reader=JSONFileReader(),
            writer=JSONFileWriter(),
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "mcp-config-schema.yaml"
        )
        
        return scopes
    
    def list_servers(self, scope: Optional[str] = None) -> Dict[str, ServerInfo]:
        """List all servers, optionally filtered by scope.
        
        Args:
            scope: Optional scope filter
            
        Returns:
            Dictionary mapping qualified server IDs to server information
        """
        servers = {}
        
        # Determine which scopes to check
        if scope:
            if not self.has_scope(scope):
                return {}
            scope_handlers = {scope: self._scopes[scope]}
        else:
            scope_handlers = self._scopes
        
        # Collect servers from all requested scopes
        for scope_name, handler in scope_handlers.items():
            if not handler.exists():
                continue
                
            scope_servers = handler.get_servers()
            for server_id, config_dict in scope_servers.items():
                # Create qualified server ID
                qualified_id = f"{self.name}:{scope_name}:{server_id}"
                
                # Determine server state
                state = ServerState.DISABLED if config_dict.get("disabled", False) else ServerState.ENABLED
                
                # Create ServerInfo object
                servers[qualified_id] = ServerInfo(
                    id=server_id,
                    client=self.name,
                    scope=scope_name,
                    config=config_dict,
                    state=state,
                    priority=handler.config.priority
                )
        
        return servers
    
    def add_server(
        self, 
        server_id: str, 
        config: ServerConfig, 
        scope: str
    ) -> OperationResult:
        """Add a server to the specified scope.
        
        Args:
            server_id: Unique server identifier
            config: Server configuration
            scope: Target scope name
            
        Returns:
            Operation result
        """
        if not self.has_scope(scope):
            available = ", ".join(self.get_scope_names())
            return OperationResult.failure_result(
                f"Unknown scope '{scope}' for client '{self.name}'. Available: {available}"
            )
        
        # Validate server configuration
        validation_errors = self.validate_server_config(config)
        if validation_errors:
            return OperationResult.failure_result(
                f"Invalid server configuration: {'; '.join(validation_errors)}",
                errors=validation_errors
            )
        
        # Add server to the specified scope
        handler = self._scopes[scope]
        return handler.add_server(server_id, config)
    
    def remove_server(self, server_id: str, scope: str) -> OperationResult:
        """Remove a server from the specified scope.
        
        Args:
            server_id: Server identifier
            scope: Source scope name
            
        Returns:
            Operation result
        """
        if not self.has_scope(scope):
            available = ", ".join(self.get_scope_names())
            return OperationResult.failure_result(
                f"Unknown scope '{scope}' for client '{self.name}'. Available: {available}"
            )
        
        handler = self._scopes[scope]
        return handler.remove_server(server_id)
    
    def get_server_state(self, server_id: str) -> ServerState:
        """Get the current state of a server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Current server state
        """
        # Find server across all scopes
        for handler in self._scopes.values():
            if handler.has_server(server_id):
                servers = handler.get_servers()
                server_config = servers.get(server_id, {})
                
                # Check if server is disabled
                if server_config.get("disabled", False):
                    return ServerState.DISABLED
                else:
                    return ServerState.ENABLED
        
        return ServerState.NOT_INSTALLED
    
    def enable_server(self, server_id: str) -> OperationResult:
        """Enable a disabled server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Operation result
        """
        # Find server across all scopes
        for scope_name, handler in self._scopes.items():
            if handler.has_server(server_id):
                # Get current configuration
                servers = handler.get_servers()
                server_config = servers.get(server_id, {})
                
                if not server_config.get("disabled", False):
                    return OperationResult.success_result(
                        f"Server '{server_id}' is already enabled in scope '{scope_name}'"
                    )
                
                # Create updated configuration without disabled flag
                updated_config = server_config.copy()
                updated_config.pop("disabled", None)
                
                # Update server configuration
                server_cfg = ServerConfig.from_dict(updated_config)
                result = handler.update_server(server_id, server_cfg)
                
                if result.success:
                    result.message = f"Enabled server '{server_id}' in scope '{scope_name}'"
                
                return result
        
        return OperationResult.failure_result(
            f"Server '{server_id}' not found in any scope"
        )
    
    def disable_server(self, server_id: str) -> OperationResult:
        """Disable an enabled server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Operation result
        """
        # Find server across all scopes
        for scope_name, handler in self._scopes.items():
            if handler.has_server(server_id):
                # Get current configuration
                servers = handler.get_servers()
                server_config = servers.get(server_id, {})
                
                if server_config.get("disabled", False):
                    return OperationResult.success_result(
                        f"Server '{server_id}' is already disabled in scope '{scope_name}'"
                    )
                
                # Create updated configuration with disabled flag
                updated_config = server_config.copy()
                updated_config["disabled"] = True
                
                # Update server configuration
                server_cfg = ServerConfig.from_dict(updated_config)
                result = handler.update_server(server_id, server_cfg)
                
                if result.success:
                    result.message = f"Disabled server '{server_id}' in scope '{scope_name}'"
                
                return result
        
        return OperationResult.failure_result(
            f"Server '{server_id}' not found in any scope"
        )
    
    def validate_server_config(self, config: ServerConfig) -> List[str]:
        """Validate server configuration for Claude Code.
        
        Args:
            config: Server configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = super().validate_server_config(config)
        
        # Claude Code specific validations
        if config.type and config.type not in ["stdio", "websocket", "http"]:
            errors.append(f"Invalid server type '{config.type}'. Must be one of: stdio, websocket, http")
        
        # Validate command accessibility
        if config.command:
            # Check for common Claude Code MCP server patterns
            if config.command.startswith("npx") and not config.args:
                errors.append("NPX commands should specify a package in args")
            
            if config.command == "python" and not any(arg.startswith("-m") for arg in config.args):
                errors.append("Python commands should use module syntax (-m package)")
        
        return errors
    
    def get_primary_scope(self) -> str:
        """Get the primary scope for this client.
        
        Returns:
            Primary scope name (user-mcp for Claude Code)
        """
        return "user-mcp"
    
    def get_project_scopes(self) -> List[str]:
        """Get all project-level scopes.
        
        Returns:
            List of project-level scope names
        """
        return [
            scope.name for scope in self.get_scopes() 
            if scope.is_project_level
        ]
    
    def get_user_scopes(self) -> List[str]:
        """Get all user-level scopes.
        
        Returns:
            List of user-level scope names
        """
        return [
            scope.name for scope in self.get_scopes() 
            if scope.is_user_level
        ]
    
    def is_installed(self) -> bool:
        """Check if Claude Code is installed.
        
        Returns:
            True if Claude Code appears to be installed
        """
        # Check for Claude Code installation by looking for config directory
        claude_dir = Path.home() / ".claude"
        return claude_dir.exists()
    
    def get_installation_info(self) -> Dict[str, Any]:
        """Get information about Claude Code installation.
        
        Returns:
            Dictionary with installation information
        """
        info = {
            "client": self.name,
            "installed": self.is_installed(),
            "config_dir": str(Path.home() / ".claude"),
            "scopes": {}
        }
        
        # Check each scope's existence
        for scope_name, handler in self._scopes.items():
            info["scopes"][scope_name] = {
                "path": str(handler.config.path),
                "exists": handler.exists(),
                "description": handler.config.description,
                "priority": handler.config.priority,
                "is_user_level": handler.config.is_user_level,
                "is_project_level": handler.config.is_project_level
            }
        
        return info