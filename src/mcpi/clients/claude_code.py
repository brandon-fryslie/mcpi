"""Claude Code MCP client plugin implementation."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import MCPClientPlugin, ScopeHandler
from .disabled_tracker import DisabledServersTracker
from .enable_disable_handlers import (
    ArrayBasedEnableDisableHandler,
    FileTrackedEnableDisableHandler,
    InlineEnableDisableHandler,
)
from .file_based import (
    FileBasedScope,
    JSONFileReader,
    JSONFileWriter,
    YAMLSchemaValidator,
)
from .types import OperationResult, ScopeConfig, ServerConfig, ServerInfo, ServerState


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
        if os.environ.get("MCPI_TEST_MODE") == "1":
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

        # Create readers/writers (reused across scopes)
        json_reader = JSONFileReader()
        json_writer = JSONFileWriter()

        # Project-level MCP configuration (.mcp.json)
        # This scope DOES support enable/disable via inline 'disabled' field
        project_mcp_path = self._get_scope_path("project-mcp", Path.cwd() / ".mcp.json")
        scopes["project-mcp"] = FileBasedScope(
            config=ScopeConfig(
                name="project-mcp",
                description="Project-level MCP configuration (.mcp.json)",
                priority=1,
                path=project_mcp_path,
                is_project_level=True,
            ),
            reader=json_reader,
            writer=json_writer,
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "mcp-config-schema.yaml",
            enable_disable_handler=InlineEnableDisableHandler(
                project_mcp_path, json_reader, json_writer
            ),
        )

        # Project-local Claude settings (.claude/settings.local.json)
        # This scope DOES support enable/disable via arrays
        project_local_path = self._get_scope_path(
            "project-local", Path.cwd() / ".claude" / "settings.local.json"
        )
        scopes["project-local"] = FileBasedScope(
            config=ScopeConfig(
                name="project-local",
                description="Project-local Claude settings (.claude/settings.local.json)",
                priority=2,
                path=project_local_path,
                is_project_level=True,
            ),
            reader=json_reader,
            writer=json_writer,
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "claude-settings-schema.yaml",
            enable_disable_handler=ArrayBasedEnableDisableHandler(
                project_local_path, json_reader, json_writer
            ),
        )

        # User-local Claude settings (~/.claude/settings.local.json)
        # This scope DOES support enable/disable via arrays
        user_local_path = self._get_scope_path(
            "user-local", Path.home() / ".claude" / "settings.local.json"
        )
        scopes["user-local"] = FileBasedScope(
            config=ScopeConfig(
                name="user-local",
                description="User-local Claude settings (~/.claude/settings.local.json)",
                priority=3,
                path=user_local_path,
                is_user_level=True,
            ),
            reader=json_reader,
            writer=json_writer,
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "claude-settings-schema.yaml",
            enable_disable_handler=ArrayBasedEnableDisableHandler(
                user_local_path, json_reader, json_writer
            ),
        )

        # User-global Claude settings (~/.claude/settings.json)
        # This scope does NOT support enable/disable arrays in settings.json format
        # Instead, use a separate disabled tracking file
        user_global_path = self._get_scope_path(
            "user-global", Path.home() / ".claude" / "settings.json"
        )
        disabled_tracker_path = self._get_scope_path(
            "user-global-disabled",
            Path.home() / ".claude" / ".mcpi-disabled-servers.json",
        )
        scopes["user-global"] = FileBasedScope(
            config=ScopeConfig(
                name="user-global",
                description="User-global Claude settings (~/.claude/settings.json)",
                priority=4,
                path=user_global_path,
                is_user_level=True,
            ),
            reader=json_reader,
            writer=json_writer,
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "claude-settings-schema.yaml",
            enable_disable_handler=FileTrackedEnableDisableHandler(
                DisabledServersTracker(disabled_tracker_path)
            ),
        )

        # User internal configuration (~/.claude.json)
        # This scope NOW supports enable/disable via separate tracking file
        user_internal_path = self._get_scope_path(
            "user-internal", Path.home() / ".claude.json"
        )
        user_internal_disabled_tracker_path = self._get_scope_path(
            "user-internal-disabled",
            Path.home() / ".claude" / ".mcpi-disabled-servers-internal.json",
        )
        scopes["user-internal"] = FileBasedScope(
            config=ScopeConfig(
                name="user-internal",
                description="User internal Claude configuration (~/.claude.json)",
                priority=5,
                path=user_internal_path,
                is_user_level=True,
            ),
            reader=json_reader,
            writer=json_writer,
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "internal-config-schema.yaml",
            enable_disable_handler=FileTrackedEnableDisableHandler(
                DisabledServersTracker(user_internal_disabled_tracker_path)
            ),
        )

        # User MCP servers configuration (~/.claude/mcp_servers.json)
        # This scope does NOT support enable/disable (no arrays in .mcp.json format)
        scopes["user-mcp"] = FileBasedScope(
            config=ScopeConfig(
                name="user-mcp",
                description="User MCP servers configuration (~/.claude/mcp_servers.json)",
                priority=6,
                path=self._get_scope_path(
                    "user-mcp", Path.home() / ".claude" / "mcp_servers.json"
                ),
                is_user_level=True,
            ),
            reader=json_reader,
            writer=json_writer,
            validator=YAMLSchemaValidator(),
            schema_path=schemas_dir / "mcp-config-schema.yaml",
            enable_disable_handler=None,  # user-mcp doesn't support enable/disable
        )

        return scopes

    def _get_server_state(
        self, server_id: str, scope: str, config_dict: Optional[Dict[str, Any]] = None
    ) -> ServerState:
        """Get the actual state of a server in a specific scope.

        Uses the scope's enable/disable handler to determine state. Different scopes
        have different mechanisms:
        - project-mcp: Use inline 'disabled' field in server config
        - project-local, user-local: Use enabledMcpjsonServers/disabledMcpjsonServers arrays
        - user-global, user-internal: Use separate disabled tracking files
        - Other scopes: Don't support enable/disable (always ENABLED)

        Additionally checks for inline "disabled" field in config for backward compatibility.

        Args:
            server_id: Server identifier
            scope: The scope where the server exists (ONLY check this scope)
            config_dict: Optional server configuration to check for inline disabled field

        Returns:
            Server state (ENABLED, DISABLED, or NOT_INSTALLED)
        """
        if scope not in self._scopes:
            return ServerState.ENABLED

        handler = self._scopes[scope]

        # First check if the config itself has a "disabled" field set to True
        # This handles legacy/inline disabled flags
        if config_dict and config_dict.get("disabled") is True:
            return ServerState.DISABLED

        # If this scope has an enable/disable handler, use it
        if (
            hasattr(handler, "enable_disable_handler")
            and handler.enable_disable_handler
        ):
            if handler.enable_disable_handler.is_disabled(server_id):
                return ServerState.DISABLED
            else:
                return ServerState.ENABLED

        # No enable/disable handler means servers are always enabled
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

                # Determine server state using ONLY the server's own scope
                # Pass config_dict to check for inline "disabled" field
                state = self._get_server_state(server_id, scope_name, config_dict)

                # Create ServerInfo object
                servers[qualified_id] = ServerInfo(
                    id=server_id,
                    client=self.name,
                    scope=scope_name,
                    config=config_dict,
                    state=state,
                    priority=handler.config.priority,
                )

        return servers

    def add_server(
        self, server_id: str, config: ServerConfig, scope: str
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
            return OperationResult(success=False, message=f"Unknown scope: {scope}")

        handler = self._scopes[scope]

        # Add the server to the scope
        result = handler.add_server(server_id, config)

        if result:
            return OperationResult(
                success=True, message=f"Server '{server_id}' added to scope '{scope}'"
            )
        else:
            return OperationResult(
                success=False,
                message=f"Failed to add server '{server_id}' to scope '{scope}'",
            )

    def update_server(
        self, server_id: str, config: ServerConfig, scope: str
    ) -> OperationResult:
        """Update a server in the specified scope.

        Args:
            server_id: Server identifier
            config: New server configuration
            scope: Target scope name

        Returns:
            Operation result
        """
        if not self.has_scope(scope):
            return OperationResult(success=False, message=f"Unknown scope: {scope}")

        handler = self._scopes[scope]

        # Update the server
        result = handler.update_server(server_id, config)

        if result:
            return OperationResult(
                success=True,
                message=f"Server '{server_id}' updated in scope '{scope}'",
            )
        else:
            return OperationResult(
                success=False,
                message=f"Failed to update server '{server_id}' in scope '{scope}'",
            )

    def remove_server(self, server_id: str, scope: str) -> OperationResult:
        """Remove a server from the specified scope.

        Args:
            server_id: Server identifier
            scope: Target scope name

        Returns:
            Operation result
        """
        if not self.has_scope(scope):
            return OperationResult(success=False, message=f"Unknown scope: {scope}")

        handler = self._scopes[scope]

        # Remove the server
        result = handler.remove_server(server_id)

        if result:
            return OperationResult(
                success=True,
                message=f"Server '{server_id}' removed from scope '{scope}'",
            )
        else:
            return OperationResult(
                success=False,
                message=f"Failed to remove server '{server_id}' from scope '{scope}'",
            )

    def enable_server(
        self, server_id: str, scope: Optional[str] = None
    ) -> OperationResult:
        """Enable a disabled server in the specified scope.

        Args:
            server_id: Server identifier
            scope: Optional target scope name. If not provided, auto-detects scope.

        Returns:
            Operation result
        """
        # Auto-detect scope if not provided
        if scope is None:
            info = self.get_server_info(server_id)
            if not info:
                return OperationResult(
                    success=False,
                    message=f"Server '{server_id}' not found in any scope",
                )
            scope = info.scope

        if not self.has_scope(scope):
            return OperationResult(success=False, message=f"Unknown scope: {scope}")

        handler = self._scopes[scope]

        # Check if this scope supports enable/disable
        if (
            not hasattr(handler, "enable_disable_handler")
            or not handler.enable_disable_handler
        ):
            return OperationResult(
                success=False,
                message=f"Scope '{scope}' does not support enable/disable operations",
            )

        # Enable the server
        result = handler.enable_disable_handler.enable_server(server_id)

        if result:
            return OperationResult(
                success=True, message=f"Server '{server_id}' enabled in scope '{scope}'"
            )
        else:
            return OperationResult(
                success=False,
                message=f"Failed to enable server '{server_id}' in scope '{scope}'",
            )

    def disable_server(
        self, server_id: str, scope: Optional[str] = None
    ) -> OperationResult:
        """Disable an enabled server in the specified scope.

        Args:
            server_id: Server identifier
            scope: Optional target scope name. If not provided, auto-detects scope.

        Returns:
            Operation result
        """
        # Auto-detect scope if not provided
        if scope is None:
            info = self.get_server_info(server_id)
            if not info:
                return OperationResult(
                    success=False,
                    message=f"Server '{server_id}' not found in any scope",
                )
            scope = info.scope

        if not self.has_scope(scope):
            return OperationResult(success=False, message=f"Unknown scope: {scope}")

        handler = self._scopes[scope]

        # Check if this scope supports enable/disable
        if (
            not hasattr(handler, "enable_disable_handler")
            or not handler.enable_disable_handler
        ):
            return OperationResult(
                success=False,
                message=f"Scope '{scope}' does not support enable/disable operations",
            )

        # Disable the server
        result = handler.enable_disable_handler.disable_server(server_id)

        if result:
            return OperationResult(
                success=True,
                message=f"Server '{server_id}' disabled in scope '{scope}'",
            )
        else:
            return OperationResult(
                success=False,
                message=f"Failed to disable server '{server_id}' in scope '{scope}'",
            )

    def get_server_state(self, server_id: str) -> ServerState:
        """Get the current state of a server.

        Searches all scopes to find the server and returns its state.
        Uses highest priority scope if server exists in multiple scopes.

        Args:
            server_id: Server identifier

        Returns:
            Current server state
        """
        # Get server info from all scopes (will use highest priority)
        info = self.get_server_info(server_id)

        if info:
            return info.state
        else:
            return ServerState.NOT_INSTALLED

    def get_server_info(
        self, server_id: str, scope: Optional[str] = None
    ) -> Optional[ServerInfo]:
        """Get information about a specific server.

        Args:
            server_id: Server identifier
            scope: Optional scope to search in

        Returns:
            Server information if found, None otherwise
        """
        servers = self.list_servers(scope)

        # Look for the server in the results
        for qualified_id, info in servers.items():
            if info.id == server_id:
                # If scope specified, must match
                if scope and info.scope != scope:
                    continue
                return info

        return None

    def get_scope_handler(self, scope: str) -> Optional[ScopeHandler]:
        """Get a specific scope handler.

        Args:
            scope: Scope name

        Returns:
            Scope handler if found, None otherwise
        """
        return self._scopes.get(scope)
