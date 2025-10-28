"""Claude Code MCP client plugin implementation."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from .base import MCPClientPlugin, ScopeHandler
from .file_based import FileBasedScope, JSONFileReader, JSONFileWriter, YAMLSchemaValidator
from .types import ServerInfo, ServerConfig, ServerState, ScopeConfig, OperationResult


class ClaudeCodePlugin(MCPClientPlugin):
    """Claude Code MCP client plugin."""
    
    def __init__(self, path_overrides: Optional[Dict[str, Path]] = None):
        """Initialize Claude Code plugin.

        Args:
            path_overrides: Optional dictionary to override default paths for testing

        Raises:
            RuntimeError: If instantiated in test mode without path_overrides
        """
        # SAFETY: In test mode, REQUIRE path_overrides to prevent touching real files
        if os.environ.get('MCPI_TEST_MODE') == '1':
            if not path_overrides:
                raise RuntimeError(
                    "SAFETY VIOLATION: ClaudeCodePlugin instantiated in test mode without path_overrides!\n"
                    "Tests MUST provide path_overrides to prevent modifying real user files.\n"
                    "Use the mcp_harness or mcp_manager_with_harness fixtures.\n"
                    "Example: ClaudeCodePlugin(path_overrides=harness.path_overrides)"
                )

        self._path_overrides = path_overrides or {}
        super().__init__()
    
    def _get_scope_path(self, scope_name: str, default_path: Path) -> Path:
        """Get the path for a scope, with override support.
        
        Args:
            scope_name: Name of the scope
            default_path: Default path if not overridden
            
        Returns:
            Path to use for the scope
        """
        return self._path_overrides.get(scope_name, default_path)
    
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
                path=self._get_scope_path("project-mcp", Path.cwd() / ".mcp.json"),
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
                path=self._get_scope_path("project-local", Path.cwd() / ".claude" / "settings.local.json"),
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
                path=self._get_scope_path("user-local", Path.home() / ".claude" / "settings.local.json"),
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
                path=self._get_scope_path("user-global", Path.home() / ".claude" / "settings.json"),
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
                path=self._get_scope_path("user-internal", Path.home() / ".claude.json"),
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
                path=self._get_scope_path("user-mcp", Path.home() / ".claude" / "mcp_servers.json"),
                is_user_level=True
            ),
            reader=JSONFileReader(),
            writer=JSONFileWriter(),
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "mcp-config-schema.yaml"
        )
        
        return scopes
    
    def _get_server_state(self, server_id: str) -> ServerState:
        """Get the actual state of a server using Claude's enable/disable arrays.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Server state (ENABLED, DISABLED, or NOT_INSTALLED)
        """
        # Check Claude settings scopes for enabled/disabled arrays
        settings_scopes = ["project-local", "user-local", "user-global"]
        
        for scope_name in settings_scopes:
            if scope_name in self._scopes:
                handler = self._scopes[scope_name]
                
                if handler.exists():
                    try:
                        current_data = handler.reader.read(handler.config.path)
                        enabled_servers = current_data.get("enabledMcpjsonServers", [])
                        disabled_servers = current_data.get("disabledMcpjsonServers", [])
                        
                        # If explicitly disabled, return DISABLED
                        if server_id in disabled_servers:
                            return ServerState.DISABLED
                        
                        # If explicitly enabled, return ENABLED
                        if server_id in enabled_servers:
                            return ServerState.ENABLED
                        
                    except Exception:
                        # If we can't read the settings file, continue to next scope
                        continue
        
        # If server exists in config but not in any enable/disable array, default to ENABLED
        # (This matches Claude's behavior where servers are enabled by default)
        return ServerState.ENABLED
    
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
                
                # Determine server state using Claude's actual format
                state = self._get_server_state(server_id)
                
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
        # Find server across all scopes first
        server_exists = False
        for handler in self._scopes.values():
            if handler.has_server(server_id):
                server_exists = True
                break
        
        if not server_exists:
            return ServerState.NOT_INSTALLED
        
        # Use the same logic as _get_server_state to check enabled/disabled arrays
        return self._get_server_state(server_id)
    
    def enable_server(self, server_id: str) -> OperationResult:
        """Enable a server using Claude's actual format.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Operation result
        """
        # Find a Claude settings scope that can handle enable/disable
        settings_scopes = ["project-local", "user-local", "user-global"]
        
        for scope_name in settings_scopes:
            if scope_name in self._scopes:
                handler = self._scopes[scope_name]
                
                # Read current settings file
                if handler.exists():
                    current_data = handler.reader.read(handler.config.path)
                else:
                    current_data = {}
                
                # Initialize arrays if they don't exist
                enabled_servers = current_data.get("enabledMcpjsonServers", [])
                disabled_servers = current_data.get("disabledMcpjsonServers", [])
                
                # Remove from disabled array if present
                if server_id in disabled_servers:
                    disabled_servers.remove(server_id)
                
                # Add to enabled array if not already there
                if server_id not in enabled_servers:
                    enabled_servers.append(server_id)
                
                # Update the data
                current_data["enabledMcpjsonServers"] = enabled_servers
                current_data["disabledMcpjsonServers"] = disabled_servers
                
                # Write back to file
                try:
                    handler.writer.write(handler.config.path, current_data)
                    return OperationResult.success_result(
                        f"Enabled server '{server_id}' in scope '{scope_name}'"
                    )
                except Exception as e:
                    return OperationResult.failure_result(
                        f"Failed to enable server '{server_id}': {e}"
                    )
        
        return OperationResult.failure_result(
            "No suitable Claude settings scope found for enable/disable operations"
        )
    
    def disable_server(self, server_id: str) -> OperationResult:
        """Disable a server using Claude's actual format.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Operation result
        """
        # Find a Claude settings scope that can handle enable/disable
        settings_scopes = ["project-local", "user-local", "user-global"]
        
        for scope_name in settings_scopes:
            if scope_name in self._scopes:
                handler = self._scopes[scope_name]
                
                # Read current settings file
                if handler.exists():
                    current_data = handler.reader.read(handler.config.path)
                else:
                    current_data = {}
                
                # Initialize arrays if they don't exist
                enabled_servers = current_data.get("enabledMcpjsonServers", [])
                disabled_servers = current_data.get("disabledMcpjsonServers", [])
                
                # Remove from enabled array if present
                if server_id in enabled_servers:
                    enabled_servers.remove(server_id)
                
                # Add to disabled array if not already there
                if server_id not in disabled_servers:
                    disabled_servers.append(server_id)
                
                # Update the data
                current_data["enabledMcpjsonServers"] = enabled_servers
                current_data["disabledMcpjsonServers"] = disabled_servers
                
                # Write back to file
                try:
                    handler.writer.write(handler.config.path, current_data)
                    return OperationResult.success_result(
                        f"Disabled server '{server_id}' in scope '{scope_name}'"
                    )
                except Exception as e:
                    return OperationResult.failure_result(
                        f"Failed to disable server '{server_id}': {e}"
                    )
        
        return OperationResult.failure_result(
            "No suitable Claude settings scope found for enable/disable operations"
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