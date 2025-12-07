"""Claude Desktop MCP client plugin implementation."""

import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional

from .base import MCPClientPlugin, ScopeHandler
from .file_based import FileBasedScope, JSONFileReader, JSONFileWriter
from .file_move_enable_disable_handler import FileMoveEnableDisableHandler
from .types import OperationResult, ScopeConfig, ServerConfig, ServerInfo, ServerState


class ClaudeDesktopPlugin(MCPClientPlugin):
    """Claude Desktop MCP client plugin.

    Claude Desktop has a simpler configuration model than Claude Code:
    - Single user-level configuration file
    - No project-level scopes
    - Platform-specific config paths

    Config locations by platform:
    - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
    - Windows: %APPDATA%\Claude\claude_desktop_config.json
    - Linux: ~/.config/Claude/claude_desktop_config.json (community builds only)

    Enable/Disable mechanism:
    Claude Desktop has no built-in disable functionality, so we use the
    FileMoveEnableDisableHandler pattern:
    - Active file: claude_desktop_config.json (ENABLED servers)
    - Disabled file: claude_desktop_disabled.json (DISABLED servers)
    - disable: MOVE server config from active to disabled file
    - enable: MOVE server config from disabled to active file
    """

    def __init__(self, path_overrides: Optional[Dict[str, Path]] = None):
        """Initialize Claude Desktop plugin.

        Args:
            path_overrides: Optional dictionary to override default paths for testing.
                           Keys: "user" (active config), "user-disabled" (disabled config)

        Raises:
            RuntimeError: If instantiated in test mode without path_overrides
        """
        # SAFETY: In test mode, REQUIRE path_overrides to prevent touching real files
        if os.environ.get("MCPI_TEST_MODE") == "1":
            if not path_overrides:
                raise RuntimeError(
                    "SAFETY VIOLATION: ClaudeDesktopPlugin instantiated in test mode without path_overrides!\n"
                    "Tests MUST provide path_overrides to prevent modifying real user files.\n"
                    "Example: ClaudeDesktopPlugin(path_overrides={'user': tmp_path / 'config.json'})"
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

    def _get_default_config_path(self) -> Path:
        """Get the default config path for current platform.

        Returns:
            Platform-specific default config path

        Raises:
            RuntimeError: If platform is not supported
        """
        system = platform.system()

        if system == "Darwin":
            # macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        elif system == "Windows":
            # Windows: %APPDATA%\Claude\claude_desktop_config.json
            appdata = os.environ.get("APPDATA")
            if not appdata:
                raise RuntimeError("APPDATA environment variable not set on Windows")
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
        elif system == "Linux":
            # Linux: ~/.config/Claude/claude_desktop_config.json
            # NOTE: Claude Desktop is not officially supported on Linux
            # This is for community builds (debian, AUR, etc.)
            return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

    def _get_name(self) -> str:
        """Return the client name."""
        return "claude-desktop"

    def _initialize_scopes(self) -> Dict[str, ScopeHandler]:
        """Initialize and return scope handlers for Claude Desktop.

        Claude Desktop has only ONE scope:
        - user: User-level configuration file

        Returns:
            Dictionary mapping scope names to handlers
        """
        scopes = {}

        # Get default paths
        default_config_path = self._get_default_config_path()
        default_disabled_path = default_config_path.parent / "claude_desktop_disabled.json"

        # Apply path overrides
        config_path = self._get_scope_path("user", default_config_path)
        disabled_path = self._get_scope_path("user-disabled", default_disabled_path)

        # Create readers/writers
        json_reader = JSONFileReader()
        json_writer = JSONFileWriter()

        # Create the single user scope with FileMoveEnableDisableHandler
        scopes["user"] = FileBasedScope(
            config=ScopeConfig(
                name="user",
                description="User-level Claude Desktop configuration",
                priority=50,  # User-level priority (40-60 range)
                path=config_path,
                is_user_level=True,
                readonly=False,
            ),
            reader=json_reader,
            writer=json_writer,
            validator=None,  # No schema validation for now
            schema_path=None,
            enable_disable_handler=FileMoveEnableDisableHandler(
                active_file_path=config_path,
                disabled_file_path=disabled_path,
                reader=json_reader,
                writer=json_writer,
            ),
        )

        return scopes

    def _get_server_state(
        self, server_id: str, scope: str, config_dict: Optional[Dict[str, Any]] = None
    ) -> ServerState:
        """Get the actual state of a server in a specific scope.

        Uses the scope's enable/disable handler to determine state.

        Args:
            server_id: Server identifier
            scope: The scope where the server exists
            config_dict: Optional server configuration to check for inline disabled field

        Returns:
            Server state (ENABLED, DISABLED, or NOT_INSTALLED)
        """
        if scope not in self._scopes:
            return ServerState.ENABLED

        handler = self._scopes[scope]

        # First check if the config itself has a "disabled" field set to True
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

                # Determine server state
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

        # Validate the config
        validation_errors = self.validate_server_config(config)
        if validation_errors:
            return OperationResult(
                success=False,
                message=f"Invalid server configuration: {'; '.join(validation_errors)}",
                errors=validation_errors,
            )

        # Add the server to the scope
        result = handler.add_server(server_id, config)

        if result.success:
            return OperationResult(
                success=True, message=f"Server '{server_id}' added to scope '{scope}'"
            )
        else:
            return result

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

        if result.success:
            return OperationResult(
                success=True,
                message=f"Server '{server_id}' updated in scope '{scope}'",
            )
        else:
            return result

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

        if result.success:
            return OperationResult(
                success=True,
                message=f"Server '{server_id}' removed from scope '{scope}'",
            )
        else:
            return result

    def enable_server(
        self, server_id: str, scope: Optional[str] = None
    ) -> OperationResult:
        """Enable a disabled server.

        This operation is idempotent - enabling an already enabled server succeeds.

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

        # Check current state for idempotency
        current_state = self._get_server_state(server_id, scope)

        # If already enabled, return success (idempotent)
        if current_state == ServerState.ENABLED:
            return OperationResult(
                success=True,
                message=f"Server '{server_id}' is already enabled in scope '{scope}'",
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
        """Disable an enabled server.

        This operation is idempotent - disabling an already disabled server succeeds.

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

        # Check current state for idempotency
        current_state = self._get_server_state(server_id, scope)

        # If already disabled, return success (idempotent)
        if current_state == ServerState.DISABLED:
            return OperationResult(
                success=True,
                message=f"Server '{server_id}' is already disabled in scope '{scope}'",
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

        Args:
            server_id: Server identifier

        Returns:
            Current server state
        """
        # Get server info from all scopes
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
