"""Tests for registry manager functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import toml
import json

from mcpi.registry.manager import RegistryManager
from mcpi.registry.catalog import MCPServer


@pytest.fixture
def temp_registry_path():
    """Create a temporary registry file path."""
    with tempfile.NamedTemporaryFile(suffix='.toml', delete=False) as tmp:
        yield Path(tmp.name)
    Path(tmp.name).unlink(missing_ok=True)


@pytest.fixture
def registry_manager(temp_registry_path):
    """Create a registry manager with temporary file."""
    return RegistryManager(registry_path=temp_registry_path)


@pytest.fixture
def sample_server_info():
    """Sample server information for testing."""
    return {
        "id": "test-server",
        "name": "Test Server",
        "description": "A test MCP server",
        "author": "Test Author",
        "license": "MIT",
        "category": ["test", "utilities"],
        "capabilities": ["testing", "demo"],
        "platforms": ["linux", "darwin", "windows"],
        "installation": {
            "method": "npm",
            "package": "@test/mcp-server",
            "system_dependencies": []
        },
        "versions": {
            "latest": "1.0.0",
            "supported": ["1.0.0"]
        },
        "configuration": {
            "required_params": [],
            "optional_params": []
        }
    }


class TestRegistryManager:
    """Test suite for RegistryManager."""
    
    def test_init_default_path(self):
        """Test initialization with default path."""
        manager = RegistryManager()
        assert manager.registry_path.name == "registry.toml"
        assert manager.registry_path.suffix == ".toml"
    
    def test_init_custom_path(self, temp_registry_path):
        """Test initialization with custom path."""
        manager = RegistryManager(registry_path=temp_registry_path)
        assert manager.registry_path == temp_registry_path
    
    @pytest.mark.asyncio
    async def test_add_server_from_url_invalid_url(self, registry_manager):
        """Test adding server with invalid URL."""
        success, errors = await registry_manager.add_server_from_url("not-a-url")
        assert not success
        assert "Invalid URL format" in errors[0]
    
    @pytest.mark.asyncio
    async def test_add_server_from_url_extraction_failure(self, registry_manager):
        """Test adding server when URL extraction fails."""
        with patch.object(registry_manager.doc_parser, 'parse_documentation_url', 
                         return_value=None):
            success, errors = await registry_manager.add_server_from_url("https://example.com")
            assert not success
            assert "Failed to extract server information" in errors[0]
    
    @pytest.mark.asyncio
    async def test_add_server_from_url_non_interactive_success(self, registry_manager, sample_server_info):
        """Test adding server in non-interactive mode with valid data."""
        with patch.object(registry_manager.doc_parser, 'parse_documentation_url', 
                         return_value=sample_server_info):
            with patch.object(registry_manager.doc_parser, 'validate_server_info', 
                             return_value=(True, [])):
                success, errors = await registry_manager.add_server_from_url(
                    "https://example.com", interactive=False
                )
                assert success
                assert not errors
    
    @pytest.mark.asyncio
    async def test_add_server_from_url_non_interactive_invalid_data(self, registry_manager):
        """Test adding server in non-interactive mode with invalid data."""
        invalid_server_info = {"name": "Test"}  # Missing required fields
        validation_errors = ["Missing required field: id"]
        
        with patch.object(registry_manager.doc_parser, 'parse_documentation_url', 
                         return_value=invalid_server_info):
            with patch.object(registry_manager.doc_parser, 'validate_server_info', 
                             return_value=(False, validation_errors)):
                success, errors = await registry_manager.add_server_from_url(
                    "https://example.com", interactive=False
                )
                assert not success
                assert "Extracted information is incomplete" in errors[0]
    
    @pytest.mark.asyncio
    async def test_add_server_from_url_interactive_success(self, registry_manager, sample_server_info):
        """Test adding server in interactive mode."""
        with patch.object(registry_manager.doc_parser, 'parse_documentation_url', 
                         return_value=sample_server_info):
            with patch.object(registry_manager.doc_parser, 'validate_server_info', 
                             return_value=(True, [])):
                with patch.object(registry_manager, '_interactive_completion', 
                                 return_value=sample_server_info):
                    success, errors = await registry_manager.add_server_from_url(
                        "https://example.com", interactive=True
                    )
                    assert success
                    assert not errors
    
    @pytest.mark.asyncio
    async def test_add_server_from_url_interactive_cancelled(self, registry_manager, sample_server_info):
        """Test adding server when user cancels interactive mode."""
        with patch.object(registry_manager.doc_parser, 'parse_documentation_url', 
                         return_value=sample_server_info):
            with patch.object(registry_manager, '_interactive_completion', 
                             return_value=None):  # User cancelled
                success, errors = await registry_manager.add_server_from_url(
                    "https://example.com", interactive=True
                )
                assert not success
                assert "User cancelled operation" in errors[0]
    
    @pytest.mark.asyncio
    async def test_add_server_duplicate_id(self, registry_manager, sample_server_info):
        """Test adding server with duplicate ID."""
        # First add a server
        with patch.object(registry_manager.doc_parser, 'parse_documentation_url', 
                         return_value=sample_server_info):
            with patch.object(registry_manager.doc_parser, 'validate_server_info', 
                             return_value=(True, [])):
                success, errors = await registry_manager.add_server_from_url(
                    "https://example.com", interactive=False
                )
                assert success
        
        # Try to add the same server again
        with patch.object(registry_manager.doc_parser, 'parse_documentation_url', 
                         return_value=sample_server_info):
            with patch.object(registry_manager.doc_parser, 'validate_server_info', 
                             return_value=(True, [])):
                success, errors = await registry_manager.add_server_from_url(
                    "https://example.com", interactive=False
                )
                assert not success
                assert "already exists" in errors[0]
    
    def test_save_registry_toml(self, registry_manager, sample_server_info):
        """Test saving registry in TOML format."""
        # Add a server to the catalog
        server = MCPServer(**sample_server_info)
        registry_manager.catalog._servers[server.id] = server
        registry_manager.catalog._loaded = True
        
        # Save registry
        success = registry_manager._save_registry_toml()
        assert success
        assert registry_manager.registry_path.exists()
        
        # Verify TOML content
        with open(registry_manager.registry_path, 'r') as f:
            data = toml.load(f)
        
        assert "metadata" in data
        assert "servers" in data
        assert "test-server" in data["servers"]
        assert data["servers"]["test-server"]["name"] == "Test Server"
    
    def test_load_registry_toml(self, registry_manager, sample_server_info):
        """Test loading registry from TOML format."""
        # Create TOML registry file
        registry_data = {
            "metadata": {
                "version": "1.0.0",
                "description": "Test registry"
            },
            "servers": {
                "test-server": {
                    key: value for key, value in sample_server_info.items() 
                    if key != "id"  # ID is used as key
                }
            }
        }
        
        with open(registry_manager.registry_path, 'w') as f:
            toml.dump(registry_data, f)
        
        # Load registry
        success = registry_manager.load_registry_toml()
        assert success
        assert "test-server" in registry_manager.catalog._servers
        
        server = registry_manager.catalog._servers["test-server"]
        assert server.id == "test-server"
        assert server.name == "Test Server"
    
    def test_load_registry_toml_missing_file(self):
        """Test loading registry when file doesn't exist."""
        # Create a manager with a non-existent file path
        non_existent_path = Path("/tmp/non_existent_registry.toml")
        manager = RegistryManager(registry_path=non_existent_path)
        success = manager.load_registry_toml()
        assert not success
    
    def test_save_registry_toml_error(self, registry_manager):
        """Test saving registry when an error occurs."""
        # Remove the file first if it exists
        if registry_manager.registry_path.exists():
            registry_manager.registry_path.unlink()
        
        # Make the registry path a directory to cause an error
        registry_manager.registry_path.mkdir(parents=True, exist_ok=True)
        
        success = registry_manager._save_registry_toml()
        assert not success
        
        # Clean up - remove the directory
        registry_manager.registry_path.rmdir()
    
    @pytest.mark.asyncio
    async def test_interactive_completion_flow(self, registry_manager):
        """Test the interactive completion flow."""
        incomplete_info = {
            "id": "",  # Missing
            "name": "Test Server",
            "description": "",  # Missing
            "installation": {"method": "", "package": ""}  # Missing
        }
        validation_errors = ["Missing ID", "Missing description"]
        
        # Mock the interactive prompts
        with patch('mcpi.registry.manager.console.print'):
            with patch.object(registry_manager, '_display_server_info'):
                with patch.object(registry_manager, '_prompt_basic_info', 
                                 return_value={**incomplete_info, "id": "test-id", "description": "Test desc"}):
                    with patch.object(registry_manager, '_prompt_installation_info', 
                                     return_value={**incomplete_info, "installation": {"method": "npm", "package": "test-pkg"}}):
                        with patch.object(registry_manager, '_prompt_metadata', 
                                         return_value={**incomplete_info, "license": "MIT"}):
                            with patch('mcpi.registry.manager.MCPServer', 
                                      side_effect=Exception("Validation failed")):
                                with patch('mcpi.registry.manager.Confirm.ask', return_value=False):
                                    result = await registry_manager._interactive_completion(
                                        incomplete_info, validation_errors
                                    )
                                    assert result is None
    
    def test_display_server_info(self, registry_manager, sample_server_info):
        """Test displaying server information."""
        with patch('mcpi.registry.manager.console.print') as mock_print:
            registry_manager._display_server_info(sample_server_info)
            mock_print.assert_called()
    
    @pytest.mark.asyncio
    async def test_prompt_basic_info(self, registry_manager):
        """Test prompting for basic server information."""
        server_info = {"id": "old-id", "name": "Old Name"}
        
        with patch('mcpi.registry.manager.Prompt.ask', side_effect=["new-id", "New Name", "New Description", "New Author"]):
            with patch('mcpi.utils.validation.validate_server_id', return_value=True):
                result = await registry_manager._prompt_basic_info(server_info)
                
                assert result["id"] == "new-id"
                assert result["name"] == "New Name"
                assert result["description"] == "New Description"
                assert result["author"] == "New Author"
    
    @pytest.mark.asyncio
    async def test_prompt_installation_info(self, registry_manager):
        """Test prompting for installation information."""
        server_info = {"installation": {"method": "npm", "package": "old-package"}}
        
        with patch('mcpi.registry.manager.IntPrompt.ask', return_value=1):  # npm
            with patch('mcpi.registry.manager.Prompt.ask', side_effect=["new-package", "node, npm"]):
                with patch('mcpi.utils.validation.validate_package_name', return_value=True):
                    result = await registry_manager._prompt_installation_info(server_info)
                    
                    assert result["installation"]["method"] == "npm"
                    assert result["installation"]["package"] == "new-package"
                    assert "node" in result["installation"]["system_dependencies"]
    
    @pytest.mark.asyncio
    async def test_prompt_metadata(self, registry_manager):
        """Test prompting for metadata information."""
        server_info = {}
        
        with patch('mcpi.registry.manager.Prompt.ask', 
                  side_effect=["MIT", "2.0.0", "test, utilities", "general", "linux, darwin", 
                              "https://github.com/test/repo", "https://docs.test.com"]):
            with patch('mcpi.utils.validation.validate_license', return_value=True):
                with patch('mcpi.utils.validation.validate_version', return_value=True):
                    with patch('mcpi.utils.validation.validate_url', return_value=True):
                        result = await registry_manager._prompt_metadata(server_info)
                        
                        assert result["license"] == "MIT"
                        assert result["versions"]["latest"] == "2.0.0"
                        assert "test" in result["category"]
                        assert "general" in result["capabilities"]
                        assert "linux" in result["platforms"]


class TestRegistryManagerIntegration:
    """Integration tests for RegistryManager."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_registry_path):
        """Test the complete workflow from URL to saved registry."""
        manager = RegistryManager(registry_path=temp_registry_path)
        
        # Mock the documentation parser to return valid server info
        sample_info = {
            "id": "integration-test",
            "name": "Integration Test Server",
            "description": "A server for integration testing",
            "author": "Test Author",
            "license": "MIT",
            "category": ["test"],
            "capabilities": ["integration"],
            "platforms": ["linux", "darwin", "windows"],
            "installation": {
                "method": "npm",
                "package": "@test/integration-server",
                "system_dependencies": []
            },
            "versions": {
                "latest": "1.0.0",
                "supported": ["1.0.0"]
            },
            "configuration": {
                "required_params": [],
                "optional_params": []
            }
        }
        
        with patch.object(manager.doc_parser, 'parse_documentation_url', 
                         return_value=sample_info):
            with patch.object(manager.doc_parser, 'validate_server_info', 
                             return_value=(True, [])):
                # Add server
                success, errors = await manager.add_server_from_url(
                    "https://example.com/integration-test", interactive=False
                )
                
                assert success
                assert not errors
                assert temp_registry_path.exists()
                
                # Verify the saved TOML file
                with open(temp_registry_path, 'r') as f:
                    data = toml.load(f)
                
                assert "servers" in data
                assert "integration-test" in data["servers"]
                
                server_data = data["servers"]["integration-test"]
                assert server_data["name"] == "Integration Test Server"
                assert server_data["installation"]["method"] == "npm"
                
                # Test loading the registry back
                new_manager = RegistryManager(registry_path=temp_registry_path)
                load_success = new_manager.load_registry_toml()
                assert load_success
                
                loaded_server = new_manager.catalog.get_server("integration-test")
                assert loaded_server is not None
                assert loaded_server.name == "Integration Test Server"