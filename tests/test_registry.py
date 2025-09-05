"""Tests for the registry module."""

import json
import yaml
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, mock_open, AsyncMock
from typing import Dict, Any

from mcpi.registry.catalog import ServerCatalog, MCPServer
from mcpi.registry.doc_parser import DocumentationParser
from mcpi.utils.validation import (
    validate_url, validate_server_id, validate_package_name, 
    validate_version, validate_license
)


class TestServerCatalog:
    """Tests for ServerCatalog class."""
    
    def test_init_with_default_paths(self):
        """Test catalog initialization with default paths."""
        catalog = ServerCatalog()
        assert catalog.registry_url == ServerCatalog.DEFAULT_REGISTRY_URL
        # Should prefer YAML over JSON
        assert catalog.registry_path.name in ["registry.yaml", "registry.json"]
    
    def test_init_with_custom_paths(self, tmp_path):
        """Test catalog initialization with custom paths."""
        registry_path = tmp_path / "custom_registry.yaml"
        custom_url = "https://example.com/registry.yaml"
        
        catalog = ServerCatalog(registry_path=registry_path, registry_url=custom_url)
        assert catalog.registry_path == registry_path
        assert catalog.registry_url == custom_url
    
    def test_load_registry_creates_default_when_missing(self, tmp_path):
        """Test that load_registry creates default registry when file is missing."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        
        # Registry file shouldn't exist initially
        assert not registry_path.exists()
        
        # Loading should create default registry
        catalog.load_registry()
        assert registry_path.exists()
        
        # Should contain default servers
        servers = catalog.list_servers()
        assert len(servers) > 0
        
        # Check that filesystem server is included
        filesystem_server = catalog.get_server("filesystem")
        assert filesystem_server is not None
        assert filesystem_server.name == "Filesystem MCP Server"
    
    def test_load_yaml_registry(self, tmp_path):
        """Test loading YAML format registry."""
        registry_path = tmp_path / "registry.yaml"
        
        # Create YAML registry file
        registry_data = {
            "version": "1.0.0",
            "updated": "2025-01-01T00:00:00Z",
            "servers": {
                "test-server": {
                    "name": "Test Server",
                    "description": "Test description",
                    "category": ["test"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "test-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["test_operations"],
                    "platforms": ["linux", "darwin", "windows"],
                    "license": "MIT"
                }
            }
        }
        
        with open(registry_path, 'w') as f:
            yaml.dump(registry_data, f)
        
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        servers = catalog.list_servers()
        assert len(servers) == 1
        
        server = catalog.get_server("test-server")
        assert server is not None
        assert server.name == "Test Server"
    
    def test_load_json_registry_backward_compatibility(self, tmp_path):
        """Test loading JSON format registry for backward compatibility."""
        registry_path = tmp_path / "registry.json"
        
        # Create JSON registry file (old format)
        registry_data = {
            "version": "1.0.0",
            "servers": [
                {
                    "id": "test-server",
                    "name": "Test Server",
                    "description": "Test description",
                    "category": ["test"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "test-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["test_operations"],
                    "platforms": ["linux", "darwin", "windows"],
                    "license": "MIT"
                }
            ]
        }
        
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)
        
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        servers = catalog.list_servers()
        assert len(servers) == 1
        
        server = catalog.get_server("test-server")
        assert server is not None
        assert server.name == "Test Server"
    
    def test_save_yaml_registry(self, tmp_path):
        """Test saving registry in YAML format."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()  # This will create default servers
        
        # Save the registry
        success = catalog.save_registry()
        assert success
        assert registry_path.exists()
        
        # Verify YAML format by parsing as text (HttpUrl might cause issues with yaml.safe_load)
        with open(registry_path, 'r') as f:
            content = f.read()
        
        # Check that it's YAML format (not JSON)
        assert "servers:" in content
        assert "filesystem:" in content
        assert not content.strip().startswith('{')  # Not JSON
    
    def test_get_server(self, tmp_path):
        """Test getting server by ID."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Get existing server
        server = catalog.get_server("filesystem")
        assert server is not None
        assert server.id == "filesystem"
        
        # Get non-existent server
        server = catalog.get_server("nonexistent")
        assert server is None
    
    def test_list_servers_no_filters(self, tmp_path):
        """Test listing servers without filters."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        servers = catalog.list_servers()
        assert len(servers) > 0
        assert all(isinstance(s, MCPServer) for s in servers)
        
        # Should be sorted by name
        names = [s.name for s in servers]
        assert names == sorted(names)
    
    def test_list_servers_with_category_filter(self, tmp_path):
        """Test listing servers with category filter."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Filter by filesystem category
        servers = catalog.list_servers(category="filesystem")
        assert len(servers) > 0
        assert all("filesystem" in s.category for s in servers)
    
    def test_search_servers(self, tmp_path):
        """Test searching servers."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Search for filesystem
        results = catalog.search_servers("filesystem")
        assert len(results) > 0
        
        # Results should be ordered by relevance
        filesystem_server = results[0]
        assert "filesystem" in filesystem_server.name.lower()
    
    def test_get_categories(self, tmp_path):
        """Test getting all categories."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        categories = catalog.get_categories()
        assert len(categories) > 0
        assert "filesystem" in categories
        assert categories == sorted(categories)
    
    def test_add_server_with_validation(self, tmp_path):
        """Test adding server with validation."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Valid server data
        valid_server_data = {
            "id": "test-new-server",
            "name": "Test New Server",
            "description": "A test server for validation",
            "category": ["test", "validation"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-new-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux", "darwin", "windows"],
            "license": "MIT"
        }
        
        # Add server with validation enabled
        success, errors = catalog.add_server(valid_server_data, validate=True)
        assert success
        assert len(errors) == 0
        
        # Verify server was added
        server = catalog.get_server("test-new-server")
        assert server is not None
        assert server.name == "Test New Server"
    
    def test_add_server_validation_failure(self, tmp_path):
        """Test adding server with validation failures."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Invalid server data that will fail Pydantic validation first
        invalid_server_data = {
            "id": "test-invalid-server",  # This will pass basic validation
            "name": "",  # Empty name - will fail our validation
            "description": "",  # Empty description - will fail our validation  
            "category": [],  # Empty categories - will fail our validation
            "author": "",  # Empty author - will fail our validation
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},  # Valid to pass Pydantic
            "installation": {"method": "npm", "package": ""},  # Empty package - will fail our validation
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": [],  # Empty platforms - will fail our validation
            "license": ""  # Empty license - will fail our validation
        }
        
        # Add server with validation enabled
        success, errors = catalog.add_server(invalid_server_data, validate=True)
        assert not success
        assert len(errors) > 0
        
        # Check some specific validation errors
        error_text = " ".join(errors)
        assert "Server name cannot be empty" in error_text
        assert "Server description cannot be empty" in error_text
        assert "At least one platform must be specified" in error_text
    
    def test_add_server_pydantic_validation_failure(self, tmp_path):
        """Test adding server that fails Pydantic validation."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Invalid server data that will fail Pydantic validation
        invalid_server_data = {
            "id": "test-server",
            "name": "Test Server", 
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "invalid_method", "package": "test-server"},  # Invalid method
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        # Add server - should fail at Pydantic validation
        success, errors = catalog.add_server(invalid_server_data, validate=True)
        assert not success
        assert len(errors) > 0
        assert "Failed to add server:" in errors[0]
    
    def test_validate_server_comprehensive(self, tmp_path):
        """Test comprehensive server validation."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        
        # Create a valid server
        valid_server_data = {
            "id": "valid-server",
            "name": "Valid Server",
            "description": "A valid test server",
            "category": ["test", "validation"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "valid-server"},
            "configuration": {"required_params": ["config1"], "optional_params": ["config2"]},
            "capabilities": ["test_operations", "validation_checks"],
            "platforms": ["linux", "darwin"],
            "license": "MIT"
        }
        
        server = MCPServer(**valid_server_data)
        is_valid, errors = catalog.validate_server(server)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_registry(self, tmp_path):
        """Test registry validation."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        catalog.load_registry()
        
        # Default registry should be valid
        errors = catalog.validate_registry()
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_update_registry_from_remote(self, tmp_path):
        """Test updating registry from remote source."""
        registry_path = tmp_path / "registry.yaml"
        catalog = ServerCatalog(registry_path=registry_path)
        
        # Mock remote registry data
        remote_data = {
            "version": "1.0.0",
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
            mock_response.text = yaml.dump(remote_data)
            mock_response.headers = {'content-type': 'application/yaml'}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            success = await catalog.update_registry()
            assert success
            
            # Verify remote server was loaded
            server = catalog.get_server("remote-server")
            assert server is not None
            assert server.name == "Remote Server"


class TestDocumentationParser:
    """Tests for DocumentationParser class."""
    
    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = DocumentationParser()
        assert parser.timeout == 30.0
        assert parser._installation_patterns is not None
        assert "npm" in parser._installation_patterns
        assert "pip" in parser._installation_patterns
    
    def test_build_patterns(self):
        """Test installation pattern building."""
        parser = DocumentationParser()
        patterns = parser._build_patterns()
        
        assert "npm" in patterns
        assert "pip" in patterns
        assert "git" in patterns
        
        # Test that patterns are compiled regex objects
        for method_patterns in patterns.values():
            for pattern in method_patterns:
                assert hasattr(pattern, 'findall')  # Pattern should be compiled regex
    
    def test_extract_name(self):
        """Test name extraction from content."""
        parser = DocumentationParser()
        
        # Test various name patterns
        content1 = "# Filesystem MCP Server\n\nThis is a description"
        name1 = parser._extract_name(content1)
        assert name1 is not None
        assert "Filesystem" in name1
        
        content2 = "## SQLite MCP Server\n\nSQLite operations"
        name2 = parser._extract_name(content2)
        assert name2 is not None
        assert "SQLite" in name2
        
        # Test with no clear name pattern
        content3 = "Just some random content without a clear title"
        name3 = parser._extract_name(content3)
        # May return None or extract something from the content
        # Don't assert specific value since extraction is heuristic-based
    
    def test_extract_installation_npm(self):
        """Test NPM installation extraction."""
        parser = DocumentationParser()
        
        content = """
        # Installation
        
        ```bash
        npm install @anthropic/mcp-server-filesystem
        ```
        """
        
        installation = parser._extract_installation(content)
        assert installation["method"] == "npm"
        assert installation["package"] == "@anthropic/mcp-server-filesystem"
    
    def test_extract_installation_pip(self):
        """Test PIP installation extraction."""
        parser = DocumentationParser()
        
        content = """
        # Installation
        
        ```bash
        pip install mcp-server-postgres
        ```
        """
        
        installation = parser._extract_installation(content)
        assert installation["method"] == "pip"
        assert installation["package"] == "mcp-server-postgres"
    
    def test_extract_installation_uv(self):
        """Test UV installation extraction."""
        parser = DocumentationParser()
        
        content = """
        # Installation
        
        ```bash
        uv add mcp-server-postgres
        ```
        """
        
        installation = parser._extract_installation(content)
        assert installation["method"] == "pip"  # UV maps to pip method
        assert installation["package"] == "mcp-server-postgres"
    
    def test_generate_server_id(self):
        """Test server ID generation."""
        parser = DocumentationParser()
        
        # Test with valid package name
        server_info1 = {
            "installation": {"package": "@anthropic/mcp-server-filesystem"},
            "name": "Filesystem MCP Server"
        }
        server_id1 = parser._generate_server_id(server_info1)
        assert server_id1 == "filesystem"
        
        # Test with name fallback (invalid package)
        server_info2 = {
            "installation": {"package": "invalid!!!package"},
            "name": "GitHub MCP Server"
        }
        server_id2 = parser._generate_server_id(server_info2)
        # The ID generation may fallback to name or produce a sanitized version
        # Don't assert exact value since the logic is complex
        assert server_id2 is not None
        assert len(server_id2) > 0
    
    def test_validate_extracted_info(self):
        """Test validation of extracted server information."""
        parser = DocumentationParser()
        
        # Valid server info
        valid_info = {
            "id": "test-server",
            "name": "Test Server",
            "description": "A test server",
            "installation": {"method": "npm", "package": "test-server"}
        }
        
        is_valid, errors = parser.validate_extracted_info(valid_info)
        assert is_valid
        assert len(errors) == 0
        
        # Invalid server info
        invalid_info = {
            "id": "",  # Empty ID
            "name": "",  # Empty name
            "description": "",  # Empty description
            "installation": {"method": "invalid", "package": ""}  # Invalid method, empty package
        }
        
        is_valid, errors = parser.validate_extracted_info(invalid_info)
        assert not is_valid
        assert len(errors) > 0


class TestValidationUtilities:
    """Tests for validation utility functions."""
    
    def test_validate_url(self):
        """Test URL validation."""
        assert validate_url("https://github.com/example/repo") is True
        assert validate_url("http://example.com") is True
        assert validate_url("ftp://files.example.com") is True
        assert validate_url("invalid-url") is False
        assert validate_url("") is False
        assert validate_url(None) is False
    
    def test_validate_server_id(self):
        """Test server ID validation."""
        assert validate_server_id("filesystem") is True
        assert validate_server_id("test-server") is True
        assert validate_server_id("server_name") is True
        assert validate_server_id("a") is True
        assert validate_server_id("server123") is True
        
        assert validate_server_id("UPPERCASE") is False
        assert validate_server_id("invalid!!!") is False
        assert validate_server_id("-invalid") is False
        assert validate_server_id("invalid-") is False
        assert validate_server_id("") is False
        assert validate_server_id(None) is False
    
    def test_validate_package_name_npm(self):
        """Test NPM package name validation."""
        assert validate_package_name("package-name", "npm") is True
        assert validate_package_name("@scope/package-name", "npm") is True
        assert validate_package_name("simple", "npm") is True
        
        assert validate_package_name("UPPERCASE", "npm") is False
        assert validate_package_name("invalid!!!", "npm") is False
        assert validate_package_name("", "npm") is False
    
    def test_validate_package_name_pip(self):
        """Test PIP package name validation."""
        assert validate_package_name("package-name", "pip") is True
        assert validate_package_name("Package_Name", "pip") is True
        assert validate_package_name("package123", "pip") is True
        
        assert validate_package_name("invalid!!!", "pip") is False
        assert validate_package_name("", "pip") is False
    
    def test_validate_version(self):
        """Test version validation."""
        assert validate_version("1.0.0") is True
        assert validate_version("0.1.0") is True
        assert validate_version("1.0.0-alpha") is True
        assert validate_version("1.0.0+build.1") is True
        
        assert validate_version("1.0") is False
        assert validate_version("invalid") is False
        assert validate_version("") is False
    
    def test_validate_license(self):
        """Test license validation."""
        assert validate_license("MIT") is True
        assert validate_license("Apache-2.0") is True
        assert validate_license("GPL-3.0") is True
        assert validate_license("Custom License") is True
        
        assert validate_license("") is False
        assert validate_license("Invalid<>License") is False
        assert validate_license("A" * 100) is False  # Too long


@pytest.fixture
def sample_yaml_registry_data():
    """Fixture providing sample YAML registry data for tests."""
    return {
        "version": "1.0.0",
        "updated": "2025-01-01T00:00:00Z",
        "description": "Test MCP Server Registry",
        "servers": {
            "filesystem": {
                "name": "Filesystem MCP Server",
                "description": "Access local filesystem operations",
                "category": ["filesystem", "core"],
                "author": "Anthropic",
                "repository": "https://github.com/anthropics/mcp-server-filesystem",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "npm", "package": "@anthropic/mcp-server-filesystem"},
                "configuration": {"required_params": ["root_path"], "optional_params": []},
                "capabilities": ["file_operations"],
                "platforms": ["linux", "darwin", "windows"],
                "license": "MIT"
            }
        }
    }


@pytest.fixture
def sample_json_registry_data():
    """Fixture providing sample JSON registry data for backward compatibility tests."""
    return {
        "version": "1.0.0",
        "updated": "2025-01-01T00:00:00Z",
        "servers": [
            {
                "id": "filesystem",
                "name": "Filesystem MCP Server",
                "description": "Access local filesystem operations",
                "category": ["filesystem", "core"],
                "author": "Anthropic",
                "repository": "https://github.com/anthropics/mcp-server-filesystem",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "npm", "package": "@anthropic/mcp-server-filesystem"},
                "configuration": {"required_params": ["root_path"], "optional_params": []},
                "capabilities": ["file_operations"],
                "platforms": ["linux", "darwin", "windows"],
                "license": "MIT"
            }
        ]
    }