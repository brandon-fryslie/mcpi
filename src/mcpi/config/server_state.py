"""Server state management for tracking enabled/disabled MCP servers."""

import json
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from enum import Enum


class ServerState(str, Enum):
    """Server installation states."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    NOT_INSTALLED = "not_installed"


class ServerStateManager:
    """Manages MCP server states (enabled/disabled) across different clients."""
    
    def __init__(self, client: str = "claude-code"):
        """Initialize server state manager.
        
        Args:
            client: Target client (e.g., "claude-code")
        """
        self.client = client
        self.enabled_config_path = self._get_enabled_config_path()
        self.disabled_config_path = self._get_disabled_config_path()
    
    def _get_enabled_config_path(self) -> Path:
        """Get path to enabled servers configuration file."""
        if self.client == "claude-code":
            system = platform.system()
            if system == "Darwin":  # macOS
                return Path.home() / ".claude" / "mcp_servers.json"
            elif system == "Linux":
                return Path.home() / ".config" / "claude" / "mcp_servers.json"
            elif system == "Windows":
                import os
                appdata = Path(os.environ.get("APPDATA", str(Path.home())))
                return appdata / "claude" / "mcp_servers.json"
            else:
                return Path.home() / ".claude" / "mcp_servers.json"
        else:
            # For other clients, use a generic path
            return Path.home() / f".{self.client}" / "mcp_servers.json"
    
    def _get_disabled_config_path(self) -> Path:
        """Get path to disabled servers configuration file."""
        if self.client == "claude-code":
            return Path.home() / ".claude" / "mcpi-disabled-servers.json"
        else:
            return Path.home() / f".{self.client}" / "mcpi-disabled-servers.json"
    
    def _load_enabled_config(self) -> Dict[str, Any]:
        """Load enabled servers configuration."""
        if not self.enabled_config_path.exists():
            return {"mcpServers": {}}
        
        try:
            with open(self.enabled_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Ensure mcpServers key exists
                if "mcpServers" not in config:
                    config["mcpServers"] = {}
                return config
        except (json.JSONDecodeError, IOError):
            return {"mcpServers": {}}
    
    def _save_enabled_config(self, config: Dict[str, Any]) -> bool:
        """Save enabled servers configuration."""
        try:
            self.enabled_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.enabled_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except (IOError, OSError):
            return False
    
    def _load_disabled_config(self) -> Dict[str, Any]:
        """Load disabled servers configuration."""
        if not self.disabled_config_path.exists():
            return {"mcpServers": {}}
        
        try:
            with open(self.disabled_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "mcpServers" not in config:
                    config["mcpServers"] = {}
                return config
        except (json.JSONDecodeError, IOError):
            return {"mcpServers": {}}
    
    def _save_disabled_config(self, config: Dict[str, Any]) -> bool:
        """Save disabled servers configuration."""
        try:
            self.disabled_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.disabled_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except (IOError, OSError):
            return False
    
    def get_server_state(self, server_id: str) -> ServerState:
        """Get the current state of a server.
        
        Args:
            server_id: Server ID to check
            
        Returns:
            Current server state
        """
        enabled_config = self._load_enabled_config()
        disabled_config = self._load_disabled_config()
        
        if server_id in enabled_config.get("mcpServers", {}):
            return ServerState.ENABLED
        elif server_id in disabled_config.get("mcpServers", {}):
            return ServerState.DISABLED
        else:
            return ServerState.NOT_INSTALLED
    
    def get_enabled_servers(self) -> Dict[str, Any]:
        """Get all enabled servers and their configurations.
        
        Returns:
            Dictionary of enabled server configurations
        """
        config = self._load_enabled_config()
        return config.get("mcpServers", {})
    
    def get_disabled_servers(self) -> Dict[str, Any]:
        """Get all disabled servers and their configurations.
        
        Returns:
            Dictionary of disabled server configurations
        """
        config = self._load_disabled_config()
        return config.get("mcpServers", {})
    
    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get all servers with their states.
        
        Returns:
            Dictionary with server IDs as keys and state info as values
        """
        enabled = self.get_enabled_servers()
        disabled = self.get_disabled_servers()
        
        result = {}
        
        for server_id, config in enabled.items():
            result[server_id] = {
                "state": ServerState.ENABLED,
                "config": config
            }
        
        for server_id, config in disabled.items():
            result[server_id] = {
                "state": ServerState.DISABLED,
                "config": config
            }
        
        return result
    
    def add_server(self, server_id: str, server_config: Dict[str, Any]) -> bool:
        """Add a server in enabled state.
        
        Args:
            server_id: Server ID
            server_config: Server configuration
            
        Returns:
            True if successful, False otherwise
        """
        # Remove from disabled if it exists there
        self.remove_from_disabled(server_id)
        
        # Add to enabled
        enabled_config = self._load_enabled_config()
        enabled_config["mcpServers"][server_id] = server_config
        
        return self._save_enabled_config(enabled_config)
    
    def disable_server(self, server_id: str) -> bool:
        """Disable a server (move from enabled to disabled).
        
        Args:
            server_id: Server ID to disable
            
        Returns:
            True if successful, False otherwise
        """
        enabled_config = self._load_enabled_config()
        disabled_config = self._load_disabled_config()
        
        # Check if server is enabled
        if server_id not in enabled_config.get("mcpServers", {}):
            return False  # Server not enabled
        
        # Move server config from enabled to disabled
        server_config = enabled_config["mcpServers"][server_id]
        disabled_config["mcpServers"][server_id] = server_config
        del enabled_config["mcpServers"][server_id]
        
        # Save both configurations
        return (self._save_enabled_config(enabled_config) and 
                self._save_disabled_config(disabled_config))
    
    def enable_server(self, server_id: str) -> bool:
        """Enable a server (move from disabled to enabled).
        
        Args:
            server_id: Server ID to enable
            
        Returns:
            True if successful, False otherwise
        """
        enabled_config = self._load_enabled_config()
        disabled_config = self._load_disabled_config()
        
        # Check if server is disabled
        if server_id not in disabled_config.get("mcpServers", {}):
            return False  # Server not disabled
        
        # Move server config from disabled to enabled
        server_config = disabled_config["mcpServers"][server_id]
        enabled_config["mcpServers"][server_id] = server_config
        del disabled_config["mcpServers"][server_id]
        
        # Save both configurations
        return (self._save_enabled_config(enabled_config) and 
                self._save_disabled_config(disabled_config))
    
    def remove_server(self, server_id: str) -> bool:
        """Completely remove a server from both enabled and disabled.
        
        Args:
            server_id: Server ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        success = True
        
        # Remove from enabled
        enabled_config = self._load_enabled_config()
        if server_id in enabled_config.get("mcpServers", {}):
            del enabled_config["mcpServers"][server_id]
            success &= self._save_enabled_config(enabled_config)
        
        # Remove from disabled
        disabled_config = self._load_disabled_config()
        if server_id in disabled_config.get("mcpServers", {}):
            del disabled_config["mcpServers"][server_id]
            success &= self._save_disabled_config(disabled_config)
        
        return success
    
    def remove_from_disabled(self, server_id: str) -> bool:
        """Remove a server from disabled state only.
        
        Args:
            server_id: Server ID to remove from disabled
            
        Returns:
            True if successful, False otherwise
        """
        disabled_config = self._load_disabled_config()
        if server_id in disabled_config.get("mcpServers", {}):
            del disabled_config["mcpServers"][server_id]
            return self._save_disabled_config(disabled_config)
        return True  # Not in disabled, so success
    
    def is_server_managed(self, server_id: str) -> bool:
        """Check if a server is managed (either enabled or disabled).
        
        Args:
            server_id: Server ID to check
            
        Returns:
            True if server is managed, False otherwise
        """
        return self.get_server_state(server_id) != ServerState.NOT_INSTALLED
    
    def get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get server configuration regardless of state.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server configuration or None if not found
        """
        enabled_config = self._load_enabled_config()
        if server_id in enabled_config.get("mcpServers", {}):
            return enabled_config["mcpServers"][server_id]
        
        disabled_config = self._load_disabled_config()
        if server_id in disabled_config.get("mcpServers", {}):
            return disabled_config["mcpServers"][server_id]
        
        return None
    
    def update_server_config(self, server_id: str, new_config: Dict[str, Any]) -> bool:
        """Update server configuration while preserving its state.
        
        Args:
            server_id: Server ID
            new_config: New configuration
            
        Returns:
            True if successful, False otherwise
        """
        state = self.get_server_state(server_id)
        
        if state == ServerState.ENABLED:
            enabled_config = self._load_enabled_config()
            enabled_config["mcpServers"][server_id] = new_config
            return self._save_enabled_config(enabled_config)
        elif state == ServerState.DISABLED:
            disabled_config = self._load_disabled_config()
            disabled_config["mcpServers"][server_id] = new_config
            return self._save_disabled_config(disabled_config)
        else:
            return False  # Server not managed