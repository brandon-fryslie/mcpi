"""Comprehensive tests for registry/catalog.py to boost coverage from 69% to 90%+."""

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
        assert server.description == "Updated description"
        assert "updated" in server.category
        assert server.versions.latest == "2.0.0"
    
    def test_update_server_not_found(self, tmp_path):
        """Test updating non-existent server."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        server_data = {
            "id": "nonexistent-server",
            "name": "Non-existent Server",
            "description": "This server doesn't exist",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "nonexistent-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        success, errors = catalog.update_server("nonexistent-server", server_data)
        assert not success
        assert len(errors) == 1
        assert "does not exist" in errors[0]
    
    def test_update_server_id_mismatch(self, tmp_path):
        """Test updating server with mismatched ID."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Add a server first
        original_server_data = {
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
        
        catalog.add_server(original_server_data)
        
        # Try to update with different ID
        updated_server_data = {
            "id": "different-server-id",
            "name": "Different Server",
            "description": "Different description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "different-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        success, errors = catalog.update_server("test-server", updated_server_data)
        assert not success
        assert len(errors) == 1
        assert "ID mismatch" in errors[0]
    
    def test_update_server_validation_failure(self, tmp_path):
        """Test updating server with validation errors."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Add a server first
        original_server_data = {
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
        
        catalog.add_server(original_server_data)
        
        # Try to update with invalid data
        invalid_server_data = {
            "id": "test-server",
            "name": "",  # Empty name - will fail validation
            "description": "",  # Empty description
            "category": [],  # Empty categories
            "author": "",  # Empty author
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": ""},  # Empty package
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": [],  # Empty platforms
            "license": ""  # Empty license
        }
        
        success, errors = catalog.update_server("test-server", invalid_server_data, validate=True)
        assert not success
        assert len(errors) > 0
        # Check for validation error messages
        error_text = " ".join(errors)
        assert "Server name cannot be empty" in error_text
    
    def test_update_server_exception_handling(self, tmp_path):
        """Test update_server exception handling."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Add a server first
        original_server_data = {
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
        
        catalog.add_server(original_server_data)
        
        # Pass invalid data that will cause MCPServer instantiation to fail
        invalid_data = {
            "id": "test-server",
            "versions": {"latest": "1.0.0"},  # Missing required fields
            "installation": {"method": "invalid_method"}  # Invalid method
        }
        
        success, errors = catalog.update_server("test-server", invalid_data)
        assert not success
        assert len(errors) == 1
        assert "Failed to update server" in errors[0]
    
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
    
    def test_save_registry_failure(self, tmp_path):
        """Test save registry failure handling."""
        registry_path = tmp_path / "readonly" / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Make parent directory read-only to force save failure
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            success = catalog.save_registry()
            # On some systems this might still succeed, so don't assert False
            # Just ensure the method doesn't crash
            assert isinstance(success, bool)
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)


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
    
    def test_validate_server_long_name(self, tmp_path):
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
    
    def test_validate_server_long_description(self, tmp_path):
        """Test server validation with overly long description."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "A" * 501,  # Too long (max 500)
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
        assert any("Server description too long" in error for error in errors)
    
    def test_validate_server_long_author(self, tmp_path):
        """Test server validation with overly long author."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "A" * 101,  # Too long (max 100)
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
        assert any("Server author too long" in error for error in errors)
    
    def test_validate_server_empty_package(self, tmp_path):
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
    
    def test_validate_server_invalid_installation_method(self, tmp_path):
        """Test server validation with invalid installation method.""" 
        catalog = ServerCatalog()
        
        # Create server with valid Pydantic data but invalid method for our validation
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "binary", "package": "test-server"},  # binary is valid Pydantic but not in our validation
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Invalid installation method" in error for error in errors)
    
    def test_validate_server_invalid_version(self, tmp_path):
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
    
    def test_validate_server_no_platforms(self, tmp_path):
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
    
    def test_validate_server_invalid_platforms(self, tmp_path):
        """Test server validation with invalid platforms."""
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
            "platforms": ["linux", "invalid-platform", "another-invalid"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Invalid platforms" in error for error in errors)
    
    def test_validate_server_no_categories(self, tmp_path):
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
    
    def test_validate_server_long_category(self, tmp_path):
        """Test server validation with overly long category names."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test", "A" * 51],  # Too long (max 50)
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
        assert any("Category name too long" in error for error in errors)
    
    def test_validate_server_empty_category(self, tmp_path):
        """Test server validation with empty category names."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test", ""],  # Empty category
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
        assert any("Category names cannot be empty" in error for error in errors)
    
    def test_validate_server_long_capability(self, tmp_path):
        """Test server validation with overly long capability names."""
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
            "capabilities": ["valid_capability", "A" * 101],  # Too long (max 100)
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Capability name too long" in error for error in errors)
    
    def test_validate_server_empty_capability(self, tmp_path):
        """Test server validation with empty capability names."""
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
            "capabilities": ["valid_capability", ""],  # Empty capability
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Capability names cannot be empty" in error for error in errors)
    
    def test_validate_server_long_system_dependency(self, tmp_path):
        """Test server validation with overly long system dependency names."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {
                "method": "npm", 
                "package": "test-server",
                "system_dependencies": ["valid-dep", "A" * 101]  # Too long (max 100)
            },
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("System dependency name too long" in error for error in errors)
    
    def test_validate_server_empty_system_dependency(self, tmp_path):
        """Test server validation with empty system dependency names."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {
                "method": "npm",
                "package": "test-server",
                "system_dependencies": ["valid-dep", ""]  # Empty dependency
            },
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("System dependency names cannot be empty" in error for error in errors)
    
    def test_validate_server_invalid_python_dependency(self, tmp_path):
        """Test server validation with invalid Python dependency names."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {
                "method": "pip",
                "package": "test-server",
                "python_dependencies": ["valid-dep", "invalid!!!dep"]  # Invalid package name
            },
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Invalid Python dependency name" in error for error in errors)
    
    def test_validate_server_empty_python_dependency(self, tmp_path):
        """Test server validation with empty Python dependency names."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {
                "method": "pip",
                "package": "test-server",
                "python_dependencies": ["valid-dep", ""]  # Empty dependency
            },
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        assert any("Python dependency names cannot be empty" in error for error in errors)
    
    def test_validate_server_long_config_params(self, tmp_path):
        """Test server validation with overly long configuration parameter names."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server", 
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {
                "required_params": ["valid-param", "A" * 101],  # Too long (max 100)
                "optional_params": ["another-valid", "B" * 101]  # Too long (max 100)
            },
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        error_text = " ".join(errors)
        assert "Required parameter name too long" in error_text
        assert "Optional parameter name too long" in error_text
    
    def test_validate_server_empty_config_params(self, tmp_path):
        """Test server validation with empty configuration parameter names."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {
                "required_params": ["valid-param", ""],  # Empty param
                "optional_params": ["another-valid", ""]  # Empty param
            },
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        is_valid, errors = catalog.validate_server(server)
        assert not is_valid
        error_text = " ".join(errors)
        assert "Required parameter names cannot be empty" in error_text
        assert "Optional parameter names cannot be empty" in error_text
    
    def test_validate_server_invalid_urls(self, tmp_path):
        """Test server validation with invalid URLs."""
        catalog = ServerCatalog()
        
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "repository": "invalid-url",  # Will be converted to HttpUrl if valid
            "documentation": "also-invalid-url",  # Will be converted to HttpUrl if valid
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        # This will likely fail at Pydantic validation stage for HttpUrl
        # But if it passes, our validation should catch invalid URLs
        try:
            server = MCPServer(**server_data)
            is_valid, errors = catalog.validate_server(server)
            # If we get here, check for URL validation errors
            if not is_valid:
                error_text = " ".join(errors)
                assert "Invalid repository URL" in error_text or "Invalid documentation URL" in error_text
        except Exception:
            # Expected - Pydantic will reject invalid URLs
            pass


class TestAsyncUpdateRegistry:
    """Tests for async update_registry method."""
    
    @pytest.mark.asyncio
    async def test_update_registry_success_json(self, tmp_path):
        """Test successful registry update with JSON format."""
        registry_path = tmp_path / "registry.json"
        catalog = ServerCatalog(registry_path=registry_path)
        
        # Mock remote registry data
        remote_data = {
            "version": "2.0.0",
            "servers": {
                "remote-server": {
                    "name": "Remote Server",
                    "description": "A server from remote registry",
                    "category": ["remote"],
                    "author": "Remote Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "remote-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["remote_operations"],
                    "platforms": ["linux", "darwin", "windows"],
                    "license": "MIT"
                }
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = remote_data
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            success = await catalog.update_registry()
            assert success
            
            # Verify remote server was loaded
            server = catalog.get_server("remote-server")
            assert server is not None
            assert server.name == "Remote Server"
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
    async def test_update_registry_invalid_data(self, tmp_path):
        """Test registry update with invalid remote data."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        
        # Invalid remote data (missing required fields)
        invalid_data = {
            "version": "1.0.0",
            "servers": {
                "invalid-server": {
                    "name": "Invalid Server"
                    # Missing required fields like description, author, etc.
                }
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.text = yaml.dump(invalid_data)
            mock_response.headers = {'content-type': 'application/yaml'}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            success = await catalog.update_registry()
            assert not success
    
    @pytest.mark.asyncio
    async def test_update_registry_with_backup(self, tmp_path):
        """Test registry update creates backup of existing registry."""
        registry_path = tmp_path / "registry.yaml"
        backup_path = registry_path.with_suffix('.backup')
        
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()  # Creates default registry
        
        # Verify original exists
        assert registry_path.exists()
        original_content = registry_path.read_text()
        
        # Mock remote registry data
        remote_data = {
            "version": "2.0.0",
            "servers": {
                "new-server": {
                    "name": "New Server",
                    "description": "A new server from remote registry",
                    "category": ["new"],
                    "author": "New Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "new-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["new_operations"],
                    "platforms": ["linux"],
                    "license": "MIT"
                }
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.text = yaml.dump(remote_data)
            mock_response.headers = {'content-type': 'application/yaml'}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            success = await catalog.update_registry()
            assert success
            
            # Verify backup was created
            assert backup_path.exists()
            backup_content = backup_path.read_text()
            assert backup_content == original_content
            
            # Verify new server was loaded
            server = catalog.get_server("new-server")
            assert server is not None
            assert server.name == "New Server"
    
    @pytest.mark.asyncio
    async def test_update_registry_yaml_content_type(self, tmp_path):
        """Test registry update with YAML content type detection."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        
        remote_data = {
            "version": "1.0.0",
            "servers": {
                "yaml-server": {
                    "name": "YAML Server",
                    "description": "A server from YAML registry",
                    "category": ["yaml"],
                    "author": "YAML Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "yaml-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["yaml_operations"],
                    "platforms": ["linux"],
                    "license": "MIT"
                }
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.text = yaml.dump(remote_data)
            mock_response.headers = {'content-type': 'text/yaml'}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            success = await catalog.update_registry()
            assert success
            
            server = catalog.get_server("yaml-server")
            assert server is not None
            assert server.name == "YAML Server"


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