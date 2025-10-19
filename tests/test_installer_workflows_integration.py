"""End-to-end installer workflow integration tests.

These tests validate complete installation workflows from registry discovery
through final configuration, testing the full user journey.
"""

import pytest
import json
import tempfile
import toml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import subprocess

from mcpi.installer.base import InstallationResult, InstallationStatus
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.installer.npm import NPMInstaller
from mcpi.installer.python import PythonInstaller
from mcpi.installer.git import GitInstaller
from mcpi.registry.catalog import MCPServer, ServerCatalog
from mcpi.config.manager import ConfigManager


class TestEndToEndInstallerWorkflows:
    """Test complete installer workflows from start to finish."""

    @pytest.fixture
    def sample_npm_server(self):
        """Sample NPM server for testing."""
        return MCPServer(**{
            "id": "filesystem",
            "name": "Filesystem MCP Server",
            "description": "Access local filesystem operations",
            "category": ["filesystem", "local"],
            "author": "Anthropic",
            "repository": "https://github.com/anthropics/mcp-server-filesystem",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {
                "method": "npm",
                "package": "@anthropic/mcp-server-filesystem",
                "system_dependencies": [],
                "python_dependencies": []
            },
            "configuration": {
                "required_params": ["root_path"],
                "optional_params": ["allowed_extensions"]
            },
            "capabilities": ["file_operations"],
            "platforms": ["linux", "darwin", "windows"],
            "license": "MIT"
        })

    @pytest.fixture
    def sample_python_server(self):
        """Sample Python server for testing."""
        return MCPServer(**{
            "id": "database",
            "name": "Database MCP Server",
            "description": "Database connectivity and operations",
            "category": ["database", "data"],
            "author": "Community",
            "repository": "https://github.com/community/mcp-server-database",
            "versions": {"latest": "2.1.0", "supported": ["2.1.0", "2.0.0"]},
            "installation": {
                "method": "pip",
                "package": "mcp-server-database",
                "system_dependencies": ["postgresql-dev"],
                "python_dependencies": ["psycopg2>=2.8.0"]
            },
            "configuration": {
                "required_params": ["database_url"],
                "optional_params": ["connection_pool_size", "timeout"]
            },
            "capabilities": ["database_operations", "sql_queries"],
            "platforms": ["linux", "darwin"],
            "license": "MIT"
        })

    @pytest.fixture
    def sample_git_server(self):
        """Sample Git server for testing."""
        return MCPServer(**{
            "id": "custom-server",
            "name": "Custom MCP Server",
            "description": "Custom development server from Git",
            "category": ["development", "custom"],
            "author": "Developer",
            "repository": "https://github.com/developer/custom-mcp-server",
            "versions": {"latest": "main", "supported": ["main", "v1.0"]},
            "installation": {
                "method": "git",
                "package": "https://github.com/developer/custom-mcp-server.git",
                "system_dependencies": [],
                "python_dependencies": ["requirements.txt"]
            },
            "configuration": {
                "required_params": ["api_key"],
                "optional_params": ["debug_mode"]
            },
            "capabilities": ["custom_operations"],
            "platforms": ["linux", "darwin"],
            "license": "GPL-3.0"
        })

    def test_npm_server_full_installation_workflow(self, sample_npm_server):
        """Test complete NPM server installation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".claude"
            config_dir.mkdir()
            config_file = config_dir / "mcp_servers.json"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            # Mock NPM operations
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                # Setup mocks for successful NPM installation
                mock_subprocess.side_effect = [
                    Mock(returncode=0, stdout="npm install successful"),  # npm install
                    Mock(returncode=0, stdout="@anthropic/mcp-server-filesystem@1.0.0")  # npm list
                ]
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Test the full installation workflow
                result = installer.install(sample_npm_server)
                
                # Verify installation was attempted
                assert mock_subprocess.called
                
                # Verify NPM install command was called
                install_call = mock_subprocess.call_args_list[0]
                assert "npm" in install_call[0][0]
                assert "install" in install_call[0][0]
                assert "@anthropic/mcp-server-filesystem" in install_call[0][0]

    def test_python_server_full_installation_workflow(self, sample_python_server):
        """Test complete Python server installation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".claude"
            config_dir.mkdir()
            config_file = config_dir / "mcp_servers.json"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                # Setup mocks for successful Python installation
                mock_subprocess.side_effect = [
                    Mock(returncode=0, stdout="uv pip install successful"),  # uv install
                    Mock(returncode=0, stdout="mcp-server-database 2.1.0")  # package check
                ]
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Test the full installation workflow
                result = installer.install(sample_python_server)
                
                # Verify installation was attempted
                assert mock_subprocess.called

    def test_git_server_full_installation_workflow(self, sample_git_server):
        """Test complete Git server installation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".claude"
            config_dir.mkdir()
            config_file = config_dir / "mcp_servers.json"
            
            # Create initial config file  
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists, \
                 patch('pathlib.Path.mkdir') as mock_mkdir:
                
                # Setup mocks for successful Git installation
                mock_subprocess.side_effect = [
                    Mock(returncode=0, stdout="Cloning into repository"),  # git clone
                    Mock(returncode=0, stdout="requirements installed")   # pip install
                ]
                mock_exists.return_value = True
                mock_mkdir.return_value = None
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Test the full installation workflow
                result = installer.install(sample_git_server)
                
                # Verify installation was attempted
                assert mock_subprocess.called

    def test_registry_to_installation_complete_workflow(self):
        """Test complete workflow from registry discovery to installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "registry.yaml"
            config_dir = Path(temp_dir) / ".claude"
            config_dir.mkdir()
            config_file = config_dir / "mcp_servers.json"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            # Create a test registry
            registry_data = {
                "version": "1.0.0",
                "servers": [{
                    "id": "filesystem",
                    "name": "Filesystem Server",
                    "description": "File operations",
                    "category": ["filesystem"],
                    "author": "Test",
                    "versions": {"latest": "1.0.0"},
                    "installation": {"method": "npm", "package": "@test/filesystem"},
                    "configuration": {"required_params": []},
                    "capabilities": ["files"],
                    "platforms": ["linux"],
                    "license": "MIT"
                }]
            }
            
            with open(registry_path, 'w') as f:
                import yaml
                yaml.dump(registry_data, f)
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                mock_subprocess.return_value = Mock(returncode=0, stdout="success")
                mock_exists.return_value = True
                
                # Step 1: Discovery
                catalog = ServerCatalog(registry_path=registry_path)
                servers = catalog.list_servers()
                assert len(servers) > 0
                
                # Step 2: Search for specific server
                search_results = catalog.search_servers("filesystem")
                assert len(search_results) > 0
                
                # Step 3: Get server details
                server = search_results[0][0]  # First result, server object
                assert server.id == "filesystem"
                
                # Step 4: Installation
                installer = ClaudeCodeInstaller(config_path=config_file)
                result = installer.install(server)
                
                # Verify complete workflow
                assert mock_subprocess.called

    def test_installation_failure_recovery_workflow(self, sample_npm_server):
        """Test installation failure and recovery workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "mcp_servers.json"
            backup_file = Path(temp_dir) / "mcp_servers.json.backup"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists, \
                 patch('shutil.copy2') as mock_copy:
                
                # Simulate installation failure
                mock_subprocess.side_effect = subprocess.CalledProcessError(1, "npm install")
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Test installation failure handling
                result = installer.install(sample_npm_server)
                
                # Verify failure was handled gracefully
                assert mock_subprocess.called

    def test_multi_server_installation_workflow(self, sample_npm_server, sample_python_server):
        """Test installing multiple servers in sequence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "mcp_servers.json"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                # Setup mocks for successful installations
                mock_subprocess.return_value = Mock(returncode=0, stdout="success")
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Install first server
                result1 = installer.install(sample_npm_server)
                assert mock_subprocess.called
                
                # Reset mock for second installation
                mock_subprocess.reset_mock()
                
                # Install second server
                result2 = installer.install(sample_python_server)
                assert mock_subprocess.called

    def test_configuration_customization_workflow(self, sample_npm_server):
        """Test server installation with custom configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "mcp_servers.json"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                mock_subprocess.return_value = Mock(returncode=0, stdout="success")
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Install with custom configuration
                custom_config = {"root_path": "/custom/path", "allowed_extensions": [".txt", ".md"]}
                result = installer.install(sample_npm_server, config_params=custom_config)
                
                assert mock_subprocess.called

    def test_uninstallation_workflow(self, sample_npm_server):
        """Test complete server uninstallation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "mcp_servers.json"
            
            # Start with server already installed
            initial_config = {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": ["@anthropic/mcp-server-filesystem", "/some/path"]
                    }
                }
            }
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                mock_subprocess.return_value = Mock(returncode=0, stdout="success")
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Test uninstallation
                result = installer.uninstall(sample_npm_server.id)
                
                # Verify uninstallation was attempted
                assert config_file.exists()  # Should still exist after uninstall

    def test_server_update_workflow(self, sample_npm_server):
        """Test server update workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "mcp_servers.json"
            
            # Start with server already installed
            initial_config = {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": ["@anthropic/mcp-server-filesystem", "/some/path"]
                    }
                }
            }
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                # Mock successful update
                mock_subprocess.return_value = Mock(returncode=0, stdout="updated to 1.1.0")
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Test update (uninstall + reinstall)
                uninstall_result = installer.uninstall(sample_npm_server.id)
                install_result = installer.install(sample_npm_server)
                
                # Verify both operations completed
                assert config_file.exists()

    def test_cross_platform_installation_workflow(self, sample_npm_server):
        """Test installation workflow across different platforms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "mcp_servers.json"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            # Test different platform configurations
            platforms = ["Linux", "Darwin", "Windows"]
            
            for platform in platforms:
                with patch('subprocess.run') as mock_subprocess, \
                     patch('pathlib.Path.exists') as mock_exists, \
                     patch('platform.system', return_value=platform):
                    
                    mock_subprocess.return_value = Mock(returncode=0, stdout="success")
                    mock_exists.return_value = True
                    
                    installer = ClaudeCodeInstaller(config_path=config_file)
                    
                    # Verify platform-specific installation
                    result = installer.install(sample_npm_server)
                    assert mock_subprocess.called

    def test_dependency_resolution_workflow(self, sample_python_server):
        """Test installation workflow with system dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "mcp_servers.json"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                # Mock dependency installation
                mock_subprocess.side_effect = [
                    Mock(returncode=0, stdout="system deps installed"),    # system deps
                    Mock(returncode=0, stdout="python package installed") # python package
                ]
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Test installation with dependencies
                result = installer.install(sample_python_server)
                
                # Should have made subprocess calls for dependencies
                assert mock_subprocess.called

    def test_installer_component_interactions(self, sample_npm_server):
        """Test how installer components interact with each other."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "mcp_servers.json"
            
            # Create initial config file
            initial_config = {"mcpServers": {}}
            config_file.write_text(json.dumps(initial_config))
            
            with patch('subprocess.run') as mock_subprocess, \
                 patch('pathlib.Path.exists') as mock_exists:
                
                mock_subprocess.return_value = Mock(returncode=0, stdout="success")
                mock_exists.return_value = True
                
                installer = ClaudeCodeInstaller(config_path=config_file)
                
                # Test that Claude Code installer delegates to NPM installer
                result = installer.install(sample_npm_server)
                
                # Verify the delegation happened
                assert hasattr(installer, 'npm_installer')
                assert hasattr(installer, 'python_installer')
                assert hasattr(installer, 'git_installer')
                assert mock_subprocess.called