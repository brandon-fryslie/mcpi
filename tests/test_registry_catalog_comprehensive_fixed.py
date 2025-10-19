"""Fixed comprehensive tests for registry/catalog.py coverage boost."""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import patch, AsyncMock, Mock
import httpx

from mcpi.registry.catalog import (
    ServerCatalog, MCPServer, ServerInstallation, ServerConfiguration, 
    ServerVersions, InstallationMethod, Platform
)


class TestServerCatalogCoverageBoost:
    """Tests targeting missing coverage areas in ServerCatalog."""
    
    def test_update_server_success(self, tmp_path):
        """Test successful server update."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Add a server first
        original_server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Original description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        success, errors = catalog.add_server(original_server_data)
        assert success
        
        # Now update the server
        updated_server_data = {
            "id": "test-server",
            "name": "Updated Test Server",
            "description": "Updated description",
            "category": ["test", "updated"],
            "author": "Updated Author",
            "versions": {"latest": "2.0.0", "supported": ["1.0.0", "2.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": ["config1"], "optional_params": ["config2"]},
            "capabilities": ["test_operations", "updated_operations"],
            "platforms": ["linux", "darwin"],
            "license": "Apache-2.0"
        }
        
        success, errors = catalog.update_server("test-server", updated_server_data, validate=True)
        assert success
        assert len(errors) == 0
        
        # Verify update
        server = catalog.get_server("test-server")
        assert server.name == "Updated Test Server"
    
    def test_remove_server_success(self, tmp_path):
        """Test successful server removal."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Add a server first
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        catalog.add_server(server_data)
        assert catalog.get_server("test-server") is not None
        
        # Remove the server
        success = catalog.remove_server("test-server")
        assert success
        assert catalog.get_server("test-server") is None
    
    def test_remove_server_not_found(self, tmp_path):
        """Test removing non-existent server."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        success = catalog.remove_server("nonexistent-server")
        assert not success
    
    def test_get_servers_by_category_not_found(self, tmp_path):
        """Test getting servers by non-existent category."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        servers = catalog.get_servers_by_category("nonexistent-category")
        assert servers == []


class TestServerValidationComprehensive:
    """Comprehensive tests for server validation to boost coverage."""
    
    def test_validate_server_invalid_id(self, tmp_path):
        """Test server validation with invalid server ID."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "INVALID-ID!!!",  # Invalid characters
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Invalid server ID format" in error for error in errors)
    
    def test_validate_server_empty_name(self):
        """Test server validation with empty name."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "",  # Empty name
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Server name cannot be empty" in error for error in errors)
    
    def test_validate_server_long_name(self):
        """Test server validation with overly long name."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "A" * 101,  # Too long (max 100)
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Server name too long" in error for error in errors)
    
    def test_validate_server_empty_package(self):
        """Test server validation with empty installation package."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": ""},  # Empty package
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Installation package cannot be empty" in error for error in errors)
    
    def test_validate_server_invalid_version(self):
        """Test server validation with invalid version format."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "invalid-version", "supported": ["1.0", "invalid-version2"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        error_text = " ".join(errors)
        assert "Invalid latest version format" in error_text
        assert "Invalid supported version format" in error_text
    
    def test_validate_server_no_platforms(self):
        """Test server validation with no platforms specified."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": [],  # No platforms
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("At least one platform must be specified" in error for error in errors)
    
    def test_validate_server_no_categories(self):
        """Test server validation with no categories."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": [],  # No categories
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("At least one category must be specified" in error for error in errors)


@pytest.mark.asyncio
class TestAsyncUpdateRegistry:
    """Tests for async update_registry method."""
    
    async def test_update_registry_http_error(self, tmp_path):
        """Test registry update with HTTP error."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock HTTP error
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=Mock()
            )
            
            success = await catalog.update_registry()
            assert not success
    
    async def test_update_registry_request_error(self, tmp_path):
        """Test registry update with request error."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock request error
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError(
                "Connection failed", request=Mock()
            )
            
            success = await catalog.update_registry()
            assert not success


class TestValidateRegistryComprehensive:
    """Tests for validate_registry method with server ID mismatches."""
    
    def test_validate_registry_with_id_mismatch(self, tmp_path):
        """Test validate_registry detecting server ID mismatches."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        
        # Create a server and manually mess with its ID to create mismatch
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        catalog.load_registry()
        server = MCPServer(**server_data)
        
        # Manually add server with different key than its ID to create mismatch
        catalog._servers["wrong-key"] = server
        catalog._loaded = True
        
        errors = catalog.validate_registry()
        assert len(errors) > 0
        assert any("Server ID mismatch" in error for error in errors)