"""Stateful MCP server installer that tracks enabled/disabled states."""

from typing import Dict, List, Optional, Any
from mcpi.installer.base import BaseInstaller, InstallationResult
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.registry.catalog import MCPServer
from mcpi.config.server_state import ServerStateManager, ServerState


class GenericInstaller:
    """A minimal installer for generic clients that just tracks state."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
    
    def install(self, server: MCPServer, config_params: Optional[Dict[str, Any]] = None) -> InstallationResult:
        """Simulate installation for generic client."""
        from mcpi.installer.base import InstallationResult, InstallationStatus
        
        # For generic clients, we just simulate successful installation
        server_config = {
            "command": "echo",
            "args": [f"Generic server {server.id} not actually installed"]
        }
        
        return InstallationResult(
            status=InstallationStatus.SUCCESS,
            server_id=server.id,
            message=f"Simulated installation of {server.id}",
            details={"server_config": server_config}
        )
    
    def uninstall(self, server_id: str) -> InstallationResult:
        """Simulate uninstallation for generic client."""
        from mcpi.installer.base import InstallationResult, InstallationStatus
        
        return InstallationResult(
            status=InstallationStatus.SUCCESS,
            server_id=server_id,
            message=f"Simulated uninstallation of {server_id}"
        )


class StatefulInstaller:
    """Installer that manages server states across different clients."""
    
    def __init__(self, client: str = "claude-code", dry_run: bool = False):
        """Initialize stateful installer.
        
        Args:
            client: Target client (e.g., "claude-code", "generic")
            dry_run: If True, simulate operations without making changes
        """
        self.client = client
        self.dry_run = dry_run
        self.state_manager = ServerStateManager(client)
        
        # Initialize client-specific installer
        if client == "claude-code":
            self.installer = ClaudeCodeInstaller(dry_run=dry_run)
        elif client == "generic":
            self.installer = GenericInstaller(dry_run=dry_run)
        else:
            raise ValueError(f"Unsupported client: {client}")
    
    def add_server(self, server: MCPServer, config_params: Optional[Dict[str, Any]] = None) -> InstallationResult:
        """Add a server (install package and enable).
        
        Args:
            server: MCP server to add
            config_params: Configuration parameters
            
        Returns:
            Installation result
        """
        if config_params is None:
            config_params = {}
        
        # Check if server is already managed
        current_state = self.state_manager.get_server_state(server.id)
        if current_state != ServerState.NOT_INSTALLED:
            return self._create_failure_result(
                server.id,
                f"Server {server.id} is already added (current state: {current_state.value})"
            )
        
        # Install the server package using the underlying installer
        install_result = self.installer.install(server, config_params)
        if not install_result.success:
            return install_result
        
        # Get the generated server configuration
        server_config = install_result.details.get("server_config")
        if not server_config:
            # Fall back to generating config ourselves
            server_config = self._generate_server_config(server, config_params, install_result.details)
        
        # For Claude Code, remove from underlying installer (we'll manage state ourselves)
        # For generic, we don't need to do this since it's just simulated
        if self.client == "claude-code" and not self.dry_run:
            self.installer.uninstall(server.id)
        
        # Add to our state management (enabled by default)
        if not self.dry_run:
            success = self.state_manager.add_server(server.id, server_config)
            if not success:
                return self._create_failure_result(
                    server.id,
                    "Failed to add server to state management"
                )
        
        return self._create_success_result(
            server.id,
            f"Successfully added {server.name} (enabled)",
            server_config=server_config,
            state=ServerState.ENABLED
        )
    
    def disable_server(self, server_id: str) -> InstallationResult:
        """Disable a server (move from enabled to disabled).
        
        Args:
            server_id: Server ID to disable
            
        Returns:
            Installation result
        """
        current_state = self.state_manager.get_server_state(server_id)
        
        if current_state == ServerState.NOT_INSTALLED:
            return self._create_failure_result(
                server_id,
                f"Server {server_id} is not installed"
            )
        
        if current_state == ServerState.DISABLED:
            return self._create_failure_result(
                server_id,
                f"Server {server_id} is already disabled"
            )
        
        # Disable the server
        if not self.dry_run:
            success = self.state_manager.disable_server(server_id)
            if not success:
                return self._create_failure_result(
                    server_id,
                    "Failed to disable server"
                )
        
        return self._create_success_result(
            server_id,
            f"Successfully disabled {server_id}",
            state=ServerState.DISABLED
        )
    
    def enable_server(self, server_id: str) -> InstallationResult:
        """Enable a server (move from disabled to enabled).
        
        Args:
            server_id: Server ID to enable
            
        Returns:
            Installation result
        """
        current_state = self.state_manager.get_server_state(server_id)
        
        if current_state == ServerState.NOT_INSTALLED:
            return self._create_failure_result(
                server_id,
                f"Server {server_id} is not installed"
            )
        
        if current_state == ServerState.ENABLED:
            return self._create_failure_result(
                server_id,
                f"Server {server_id} is already enabled"
            )
        
        # Enable the server
        if not self.dry_run:
            success = self.state_manager.enable_server(server_id)
            if not success:
                return self._create_failure_result(
                    server_id,
                    "Failed to enable server"
                )
        
        return self._create_success_result(
            server_id,
            f"Successfully enabled {server_id}",
            state=ServerState.ENABLED
        )
    
    def remove_server(self, server_id: str) -> InstallationResult:
        """Remove a server completely (from both enabled and disabled).
        
        Args:
            server_id: Server ID to remove
            
        Returns:
            Installation result
        """
        current_state = self.state_manager.get_server_state(server_id)
        
        if current_state == ServerState.NOT_INSTALLED:
            return self._create_failure_result(
                server_id,
                f"Server {server_id} is not installed"
            )
        
        # Remove the server completely
        if not self.dry_run:
            success = self.state_manager.remove_server(server_id)
            if not success:
                return self._create_failure_result(
                    server_id,
                    "Failed to remove server"
                )
        
        return self._create_success_result(
            server_id,
            f"Successfully removed {server_id}",
            state=ServerState.NOT_INSTALLED
        )
    
    def get_server_state(self, server_id: str) -> ServerState:
        """Get current state of a server.
        
        Args:
            server_id: Server ID to check
            
        Returns:
            Current server state
        """
        return self.state_manager.get_server_state(server_id)
    
    def list_servers(self) -> Dict[str, Dict[str, Any]]:
        """List all managed servers with their states.
        
        Returns:
            Dictionary of server info with states
        """
        return self.state_manager.get_all_servers()
    
    def get_enabled_servers(self) -> List[str]:
        """Get list of enabled server IDs.
        
        Returns:
            List of enabled server IDs
        """
        return list(self.state_manager.get_enabled_servers().keys())
    
    def get_disabled_servers(self) -> List[str]:
        """Get list of disabled server IDs.
        
        Returns:
            List of disabled server IDs
        """
        return list(self.state_manager.get_disabled_servers().keys())
    
    def get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get server configuration.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server configuration or None if not found
        """
        return self.state_manager.get_server_config(server_id)
    
    def update_server_config(self, server_id: str, new_config: Dict[str, Any]) -> bool:
        """Update server configuration while preserving state.
        
        Args:
            server_id: Server ID
            new_config: New configuration
            
        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            return True
        return self.state_manager.update_server_config(server_id, new_config)
    
    def _generate_server_config(
        self, 
        server: MCPServer, 
        config_params: Dict[str, Any],
        package_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate server configuration from server metadata.
        
        Args:
            server: MCP server
            config_params: User-provided configuration parameters
            package_details: Details from package installation
            
        Returns:
            Server configuration
        """
        # Use the underlying installer's config generation logic if available
        if hasattr(self.installer, '_generate_server_config'):
            return self.installer._generate_server_config(server, config_params, package_details)
        
        # Fallback basic config generation
        config = {
            "command": "python3",
            "args": ["-m", server.installation.package]
        }
        
        # Add required parameters
        for param in server.configuration.required_params:
            if param in config_params:
                config["args"].append(str(config_params[param]))
        
        # Add optional parameters
        for param in server.configuration.optional_params:
            if param in config_params:
                config["args"].extend([f"--{param}", str(config_params[param])])
        
        return config
    
    def _create_success_result(self, server_id: str, message: str, **details) -> InstallationResult:
        """Create a success installation result.
        
        Args:
            server_id: Server ID
            message: Success message
            **details: Additional result details
            
        Returns:
            Success installation result
        """
        from mcpi.installer.base import InstallationResult, InstallationStatus
        
        return InstallationResult(
            status=InstallationStatus.SUCCESS,
            server_id=server_id,
            message=message,
            details=details
        )
    
    def _create_failure_result(self, server_id: str, message: str, **details) -> InstallationResult:
        """Create a failure installation result.
        
        Args:
            server_id: Server ID
            message: Failure message
            **details: Additional result details
            
        Returns:
            Failure installation result
        """
        from mcpi.installer.base import InstallationResult, InstallationStatus
        
        return InstallationResult(
            status=InstallationStatus.FAILED,
            server_id=server_id,
            message=message,
            details=details
        )