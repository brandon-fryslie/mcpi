"""Tests for client manager."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mcpi.config.client_manager import ClientManager


class TestClientManager:
    """Test cases for ClientManager."""
    
    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict('os.environ', {'MCPI_DEFAULT_CLIENT': 'generic'}):
            manager = ClientManager()
            assert manager.get_default_client() == "generic"
    
    def test_init_without_env_var(self):
        """Test initialization without environment variable."""
        with patch.dict('os.environ', {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "client.json"
                with patch.object(ClientManager, '__init__') as mock_init:
                    mock_init.return_value = None
                    manager = ClientManager()
                    manager._default_client = None
                    manager.config_path = config_path
                    
                    # Should default to claude-code
                    assert manager.get_default_client() == "claude-code"
    
    def test_init_with_config_file(self):
        """Test initialization with existing config file."""
        with patch.dict('os.environ', {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "client.json"
                config_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create config file
                config_data = {"default_client": "generic"}
                with open(config_path, 'w') as f:
                    json.dump(config_data, f)
                
                with patch.object(ClientManager, '__init__') as mock_init:
                    mock_init.return_value = None
                    manager = ClientManager()
                    manager._default_client = None
                    manager.config_path = config_path
                    
                    # Should load from config file
                    assert manager._load_default_client() == "generic"
    
    def test_set_default_client_valid(self):
        """Test setting a valid default client."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "client.json"
            
            with patch.object(ClientManager, '__init__') as mock_init:
                mock_init.return_value = None
                manager = ClientManager()
                manager._default_client = "claude-code"
                manager.config_path = config_path
                
                # Set valid client
                success = manager.set_default_client("generic")
                assert success
                assert manager.get_default_client() == "generic"
                
                # Check file was created
                assert config_path.exists()
                with open(config_path) as f:
                    data = json.load(f)
                    assert data["default_client"] == "generic"
    
    def test_set_default_client_invalid(self):
        """Test setting an invalid default client."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "client.json"
            
            with patch.object(ClientManager, '__init__') as mock_init:
                mock_init.return_value = None
                manager = ClientManager()
                manager._default_client = "claude-code"
                manager.config_path = config_path
                
                # Set invalid client
                with pytest.raises(ValueError, match="Invalid client"):
                    manager.set_default_client("invalid-client")
    
    def test_is_client_supported(self):
        """Test client support checking."""
        manager = ClientManager()
        
        assert manager.is_client_supported("claude-code")
        assert manager.is_client_supported("generic")
        assert not manager.is_client_supported("invalid-client")
    
    def test_get_supported_clients(self):
        """Test getting supported clients list."""
        manager = ClientManager()
        
        supported = manager.get_supported_clients()
        assert "claude-code" in supported
        assert "generic" in supported
        assert len(supported) == 2
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "client.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create invalid JSON
            with open(config_path, 'w') as f:
                f.write("invalid json")
            
            with patch.object(ClientManager, '__init__') as mock_init:
                mock_init.return_value = None
                manager = ClientManager()
                manager._default_client = None
                manager.config_path = config_path
                
                # Should return None for invalid JSON
                assert manager._load_default_client() is None
    
    def test_save_config_io_error(self):
        """Test handling I/O errors when saving config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory where the file should be (to cause permission error)
            config_path = Path(temp_dir) / "readonly" / "client.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.parent.chmod(0o444)  # Read-only
            
            with patch.object(ClientManager, '__init__') as mock_init:
                mock_init.return_value = None
                manager = ClientManager()
                manager._default_client = "claude-code"
                manager.config_path = config_path
                
                try:
                    # Should handle permission error gracefully
                    success = manager.set_default_client("generic")
                    assert not success
                finally:
                    # Restore permissions for cleanup
                    config_path.parent.chmod(0o755)