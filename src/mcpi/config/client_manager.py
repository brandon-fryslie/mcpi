"""Default client configuration management."""

import os
import json
from pathlib import Path
from typing import Optional
from platformdirs import user_config_dir


class ClientManager:
    """Manages default client configuration for MCPI."""
    
    def __init__(self):
        """Initialize client manager."""
        # Try environment variable first
        self._default_client = os.environ.get("MCPI_DEFAULT_CLIENT")
        
        # Fall back to config file
        self.config_path = Path(user_config_dir("mcpi", "mcpi")) / "client.json"
        
        if self._default_client is None:
            self._default_client = self._load_default_client()
    
    def _load_default_client(self) -> Optional[str]:
        """Load default client from configuration file.
        
        Returns:
            Default client name or None if not configured
        """
        if not self.config_path.exists():
            return None
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("default_client")
        except (json.JSONDecodeError, IOError):
            return None
    
    def _save_default_client(self, client: str) -> bool:
        """Save default client to configuration file.
        
        Args:
            client: Client name to save as default
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config = {"default_client": client}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
        except (IOError, OSError):
            return False
    
    def get_default_client(self) -> str:
        """Get the default client.
        
        Returns:
            Default client name (defaults to "claude-code" if not configured)
        """
        return self._default_client or "claude-code"
    
    def set_default_client(self, client: str) -> bool:
        """Set the default client.
        
        Args:
            client: Client name to set as default
            
        Returns:
            True if successful, False otherwise
        """
        # Validate client name
        valid_clients = ["claude-code", "generic"]
        if client not in valid_clients:
            raise ValueError(f"Invalid client '{client}'. Valid clients: {', '.join(valid_clients)}")
        
        # Save to file
        if self._save_default_client(client):
            self._default_client = client
            return True
        return False
    
    def is_client_supported(self, client: str) -> bool:
        """Check if a client is supported.
        
        Args:
            client: Client name to check
            
        Returns:
            True if supported, False otherwise
        """
        return client in ["claude-code", "generic"]
    
    def get_supported_clients(self) -> list[str]:
        """Get list of supported clients.
        
        Returns:
            List of supported client names
        """
        return ["claude-code", "generic"]