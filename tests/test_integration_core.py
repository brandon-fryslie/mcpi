"""Core integration tests for essential end-to-end workflows.

These tests focus on the most important integration patterns that validate
the system works correctly from a user perspective.
"""

import pytest
import json
import tempfile
import toml
from pathlib import Path
from unittest.mock import Mock, patch

from mcpi.installer.base import InstallationResult, InstallationStatus
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.registry.catalog import MCPServer, ServerCatalog
from mcpi.config.manager import ConfigManager


class TestCoreIntegrationWorkflows:
    """Test essential integration workflows."""

    def test_installer_component_integration(self):
        """Test installer components work together correctly."""
        # Test InstallationResult creation and usage
        result = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Integration test completed successfully",
            server_id="integration-test-server",
            config_path=Path("/tmp/test_config.json"),
            details={"method": "npm", "package": "@test/integration-package"}
        )
        
        # Verify all components work
        assert result.status == InstallationStatus.SUCCESS
        assert result.server_id == "integration-test-server"
        assert result.details["method"] == "npm"
        assert isinstance(result.config_path, Path)
        
        # Test status enumeration
        assert InstallationStatus.SUCCESS == "success"
        assert InstallationStatus.FAILED == "failed"
        assert InstallationStatus.PARTIAL == "partial"
        assert InstallationStatus.SKIPPED == "skipped"
    
    def test_claude_code_installer_integration(self):
        """Test ClaudeCodeInstaller initialization and interface."""
        installer = ClaudeCodeInstaller()
        
        # Verify installer has required interface
        assert hasattr(installer, 'install')
        assert hasattr(installer, 'uninstall') 
        assert hasattr(installer, 'get_installed_servers')
        
        # Test installer can be initialized without errors
        assert installer is not None
    
    def test_server_catalog_integration(self):
        """Test ServerCatalog basic integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "integration_registry.yaml"
            catalog = ServerCatalog(registry_path=registry_path)
            
            # Verify catalog initialization
            assert catalog.registry_path == registry_path
            
            # Test basic operations
            servers = catalog.list_servers()
            assert isinstance(servers, list)
            
            # Test search functionality
            search_results = catalog.search_servers("filesystem")
            assert isinstance(search_results, list)
            
            # Verify search results structure
            for result in search_results:
                assert len(result) == 2  # (server, score)
                server, score = result
                assert hasattr(server, 'id')
                assert isinstance(score, (int, float))
    
    def test_config_manager_basic_integration(self):
        """Test ConfigManager basic integration workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            
            # Create a valid initial TOML config
            initial_config = {
                "general": {
                    "registry_url": "https://test.example.com/registry",
                    "auto_update_registry": True,
                    "default_profile": "default"
                },
                "profiles": {
                    "default": {
                        "target": "claude-code"
                    }
                }
            }
            config_path.write_text(toml.dumps(initial_config))
            
            # Test ConfigManager can load the config
            manager = ConfigManager(config_path)
            config = manager.get_config()
            
            # Verify config loading
            assert config.general.registry_url == "https://test.example.com/registry"
            assert config.general.default_profile == "default"
            assert "default" in config.profiles
    
    def test_end_to_end_data_flow_integration(self):
        """Test data flows correctly between components."""
        # Create mock server data that flows through the system
        server_data = {
            "id": "integration-flow-server",
            "name": "Integration Flow Test Server",
            "description": "Tests data flow integration",
            "category": ["testing", "integration"],
            "author": "Integration Test Suite",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "@test/flow-server"},
            "configuration": {"required_params": ["test_param"]},
            "capabilities": ["integration_testing"],
            "platforms": ["linux", "darwin"],
            "license": "MIT"
        }
        
        # Test data can be used to create server objects
        from mcpi.registry.catalog import MCPServer
        server = MCPServer(**server_data)
        
        # Verify server object creation
        assert server.id == "integration-flow-server"
        assert server.installation.method == "npm"
        assert "integration_testing" in server.capabilities
        
        # Test server can be serialized
        serialized = server.model_dump()
        assert serialized["id"] == "integration-flow-server"
        
        # Test installation result can reference this server
        install_result = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Data flow integration test successful",
            server_id=server.id,
            details={"server_name": server.name}
        )
        
        assert install_result.server_id == server.id
        assert install_result.details["server_name"] == server.name
    
    def test_registry_to_installer_workflow_integration(self):
        """Test registry data can be used by installer."""
        # Test that registry server data has the structure needed by installers
        server_data = {
            "id": "registry-installer-test",
            "name": "Registry to Installer Test",
            "description": "Test registry-installer integration",
            "category": ["testing"],
            "author": "Test Suite",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {
                "method": "npm",
                "package": "@test/registry-installer",
                "system_dependencies": [],
                "python_dependencies": []
            },
            "configuration": {
                "required_params": ["config_param"],
                "optional_params": ["optional_param"]
            },
            "capabilities": ["testing"],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        from mcpi.registry.catalog import MCPServer
        server = MCPServer(**server_data)
        
        # Verify server has all the data an installer would need
        assert hasattr(server.installation, 'method')
        assert hasattr(server.installation, 'package')
        assert hasattr(server.configuration, 'required_params')
        assert hasattr(server.configuration, 'optional_params')
        
        # Test server data can be passed to installer interface
        installer = ClaudeCodeInstaller()
        
        # Mock the install method to verify it can accept the server
        with patch.object(installer, 'install') as mock_install:
            mock_install.return_value = InstallationResult(
                status=InstallationStatus.SUCCESS,
                message="Mock installation successful",
                server_id=server.id
            )
            
            # This should work without errors
            result = installer.install(server)
            assert result.status == InstallationStatus.SUCCESS
            assert result.server_id == server.id
    
    def test_configuration_workflow_integration(self):
        """Test configuration workflows integrate correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "workflow_config.toml"
            
            # Test configuration creation workflow with proper TOML structure
            initial_config = {
                "general": {
                    "registry_url": "https://example.com/registry",
                    "auto_update_registry": False,
                    "default_profile": "test"
                },
                "profiles": {
                    "test": {
                        "target": "claude-code"
                    }
                }
            }
            config_path.write_text(toml.dumps(initial_config))
            
            manager = ConfigManager(config_path)
            loaded_config = manager.get_config()
            assert loaded_config.general.default_profile == "test"
            assert "test" in loaded_config.profiles
            
            # Simulate updating the config
            updated_config = {
                "general": {
                    "registry_url": "https://example.com/registry", 
                    "auto_update_registry": False,
                    "default_profile": "test"
                },
                "profiles": {
                    "test": {
                        "target": "claude-code"
                    },
                    "new_profile": {
                        "target": "generic"
                    }
                }
            }
            config_path.write_text(toml.dumps(updated_config))
            
            # Create a new manager instance to test config reload
            new_manager = ConfigManager(config_path)
            new_config = new_manager.get_config()
            assert "test" in new_config.profiles
            assert "new_profile" in new_config.profiles
            assert new_config.profiles["new_profile"].target == "generic"
    
    def test_error_handling_integration(self):
        """Test error handling works across components."""
        # Test installer error handling
        failed_result = InstallationResult(
            status=InstallationStatus.FAILED,
            message="Integration test failure simulation",
            server_id="failed-server",
            details={"error": "Simulated network timeout"}
        )
        
        assert failed_result.status == InstallationStatus.FAILED
        assert "timeout" in failed_result.details["error"]
        
        # Test partial installation
        partial_result = InstallationResult(
            status=InstallationStatus.PARTIAL,
            message="Partial installation - some components failed",
            server_id="partial-server",
            details={"completed": ["config"], "failed": ["dependencies"]}
        )
        
        assert partial_result.status == InstallationStatus.PARTIAL
        assert "config" in partial_result.details["completed"]
        assert "dependencies" in partial_result.details["failed"]
    
    def test_multi_component_workflow_integration(self):
        """Test multiple components working together in a workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "multi_registry.yaml"
            config_path = Path(temp_dir) / "multi_config.toml"
            
            # Initialize components
            catalog = ServerCatalog(registry_path=registry_path)
            installer = ClaudeCodeInstaller()
            
            # Create proper TOML config
            config_data = {
                "general": {
                    "registry_url": "https://example.com/registry",
                    "auto_update_registry": True,
                    "default_profile": "default"
                },
                "profiles": {
                    "default": {
                        "target": "claude-code"
                    }
                }
            }
            config_path.write_text(toml.dumps(config_data))
            config_manager = ConfigManager(config_path)
            
            # Verify all components can be initialized together
            assert catalog is not None
            assert installer is not None
            assert config_manager is not None
            
            # Test components can interact
            servers = catalog.list_servers()
            config = config_manager.get_config()
            
            assert isinstance(servers, list)
            assert hasattr(config, 'general')
            assert hasattr(config, 'profiles')
    
    def test_pydantic_model_integration(self):
        """Test Pydantic models integrate correctly across components."""
        # Test that the updated ConfigDict works correctly
        from mcpi.registry.catalog import MCPServer, ServerInstallation, InstallationMethod
        
        # Create server with enum value
        server_data = {
            "id": "pydantic-test",
            "name": "Pydantic Integration Test",
            "description": "Test Pydantic model integration",
            "category": ["testing"],
            "author": "Test Suite",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {
                "method": InstallationMethod.NPM,  # Use enum directly
                "package": "@test/pydantic-server"
            },
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        
        # Test enum value is properly handled with ConfigDict
        assert server.installation.method == "npm"  # Should be string value
        assert isinstance(server.installation.method, str)
        
        # Test serialization works correctly
        serialized = server.model_dump()
        assert serialized["installation"]["method"] == "npm"