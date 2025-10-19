"""Tests for the CLI module."""

import json
import pytest
import asyncio
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from mcpi.cli import main
from mcpi.registry.catalog import MCPServer


class TestCLICommands:
    """Tests for all CLI commands and subcommands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    # Core command tests
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_list_command_basic(self, mock_installer, mock_config, mock_catalog):
        """Test basic list command."""
        # Setup mocks
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test_server"
        mock_server.name = "Test Server"
        mock_server.description = "A test server"
        mock_server.category = ["test"]
        mock_server.author = "Test Author"
        mock_server.versions = Mock()
        mock_server.versions.latest = "1.0.0"
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.list_servers.return_value = [mock_server]
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        # Run command
        result = self.runner.invoke(main, ['registry', 'list'])
        
        assert result.exit_code == 0
        assert "Test Server" in result.output
        assert "test_server" in result.output
        assert mock_catalog_instance.list_servers.called
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_list_command_with_filters(self, mock_installer, mock_config, mock_catalog):
        """Test list command with category and platform filters."""
        mock_catalog_instance = Mock()
        mock_catalog_instance.list_servers.return_value = []
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        # Test with category filter
        result = self.runner.invoke(main, ['registry', 'list', '--category', 'filesystem'])
        assert result.exit_code == 0
        mock_catalog_instance.list_servers.assert_called_with()
        
        # Test with platform filter
        result = self.runner.invoke(main, ['registry', 'list', '--method', 'npm'])
        assert result.exit_code == 0
        
        # Test with both filters
        result = self.runner.invoke(main, ['registry', 'list', '--category', 'database', '--method', 'pip'])
        assert result.exit_code == 0
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_list_command_json_output(self, mock_installer, mock_config, mock_catalog):
        """Test list command with JSON output."""
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test_server"
        mock_server.name = "Test Server"
        mock_server.description = "A test server"
        mock_server.category = ["test"]
        mock_server.author = "Test Author"
        mock_server.versions = Mock()
        mock_server.versions.latest = "1.0.0"
        mock_server.license = "MIT"
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        mock_server.model_dump = Mock(return_value={
            "id": "test_server",
            "name": "Test Server",
            "description": "A test server",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0"},
            "license": "MIT",
            "installation": {"method": "npm"}
        })
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.list_servers.return_value = [mock_server]
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'list', '--json'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]['id'] == 'test_server'
        assert output_data[0]['name'] == 'Test Server'
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_search_command(self, mock_installer, mock_config, mock_catalog):
        """Test search command."""
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "filesystem_server"
        mock_server.name = "Filesystem Server"
        mock_server.description = "Handles filesystem operations"
        mock_server.category = ["filesystem"]
        mock_server.author = "Test Author"
        mock_server.versions = Mock()
        mock_server.versions.latest = "1.0.0"
        mock_server.capabilities = ["file_operations"]
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        
        mock_catalog_instance = Mock()
        # search_servers returns (server, score) tuples
        mock_catalog_instance.search_servers.return_value = [(mock_server, 0.95)]
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'search', 'filesystem'])
        
        assert result.exit_code == 0
        assert "Filesystem Server" in result.output
        mock_catalog_instance.search_servers.assert_called_once_with('filesystem')
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_search_command_json_output(self, mock_installer, mock_config, mock_catalog):
        """Test search command with JSON output."""
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test_server"
        mock_server.name = "Test Server"
        mock_server.description = "A test server"
        mock_server.category = ["test"]
        mock_server.capabilities = ["test_ops"]
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        # Add model_dump method for JSON serialization
        mock_server.model_dump.return_value = {
            "id": "test_server",
            "name": "Test Server",
            "description": "A test server",
            "category": ["test"],
            "capabilities": ["test_ops"],
            "installation": {"method": "npm"}
        }
        
        mock_catalog_instance = Mock()
        # search_servers returns (server, score) tuples for JSON output
        mock_catalog_instance.search_servers.return_value = [(mock_server, 0.88)]
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'search', 'test', '--json'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]['server']['id'] == 'test_server'
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_search_command_no_results(self, mock_installer, mock_config, mock_catalog):
        """Test search command with no results."""
        mock_catalog_instance = Mock()
        mock_catalog_instance.search_servers.return_value = []
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'search', 'nonexistent'])
        
        assert result.exit_code == 0
        assert "No servers found" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_info_command(self, mock_installer, mock_config, mock_catalog):
        """Test info command."""
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test_server"
        mock_server.name = "Test Server"
        mock_server.description = "A test server"
        mock_server.author = "Test Author"
        mock_server.license = "MIT"
        mock_server.category = ["test"]
        mock_server.platforms = ["linux", "darwin"]
        mock_server.capabilities = ["test_capability"]
        mock_server.versions = Mock()
        mock_server.versions.latest = "1.0.0"
        mock_server.versions.supported = ["1.0.0", "0.9.0"]
        mock_server.versions.minimum = None
        mock_server.repository = "https://github.com/test/server"
        mock_server.documentation = "https://docs.test.com"
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        mock_server.installation.package = "test-server"
        mock_server.installation.system_dependencies = ["nodejs"]
        mock_server.installation.python_dependencies = []
        mock_server.configuration = Mock()
        mock_server.configuration.required_params = ["param1"]
        mock_server.configuration.optional_params = ["param2"]
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = mock_server
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'show', 'test_server'])
        
        assert result.exit_code == 0
        assert "Test Server" in result.output
        assert "A test server" in result.output
        assert "1.0.0" in result.output
        assert "npm" in result.output  # Installation Method: npm
        assert "test-server" in result.output  # Package: test-server
        assert "test" in result.output  # Categories: test
        assert "param1" in result.output  # Required Parameters: param1
        assert "param2" in result.output  # Optional Parameters: param2
        assert "https://docs.test.com" in result.output  # Documentation
        assert "https://github.com/test/server" in result.output  # Source Code
        mock_catalog_instance.get_server.assert_called_once_with('test_server')
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_info_command_not_found(self, mock_installer, mock_config, mock_catalog):
        """Test info command for non-existent server."""
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = None
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'show', 'nonexistent'])
        
        assert result.exit_code == 1
        assert "not found" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_install_command_single_server(self, mock_installer, mock_config, mock_catalog):
        """Test install command for single server."""
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test_server"
        mock_server.name = "Test Server"
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        mock_server.installation.package = "test-server"
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = mock_server
        mock_catalog.return_value = mock_catalog_instance
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = "Installation successful"
        
        mock_installer_instance = Mock()
        mock_installer_instance.install.return_value = mock_result
        mock_installer.return_value = mock_installer_instance
        
        mock_config.return_value = Mock()
        
        # Test with confirmation
        result = self.runner.invoke(main, ['install', 'test_server'], input='y\n')
        
        assert result.exit_code == 0
        assert "Installation successful" in result.output
        mock_installer_instance.install.assert_called_once_with(mock_server)
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_install_command_multiple_servers(self, mock_installer, mock_config, mock_catalog):
        """Test install command for multiple servers."""
        mock_server1 = Mock(spec=MCPServer)
        mock_server1.id = "server1"
        mock_server1.name = "Server 1"
        mock_server1.installation = Mock()
        mock_server1.installation.method = "npm"
        mock_server1.installation.package = "server1"
        
        mock_server2 = Mock(spec=MCPServer)
        mock_server2.id = "server2"
        mock_server2.name = "Server 2"
        mock_server2.installation = Mock()
        mock_server2.installation.method = "pip"
        mock_server2.installation.package = "server2"
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.side_effect = lambda sid: mock_server1 if sid == "server1" else mock_server2
        mock_catalog.return_value = mock_catalog_instance
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = "Installation successful"
        
        mock_installer_instance = Mock()
        mock_installer_instance.install.return_value = mock_result
        mock_installer.return_value = mock_installer_instance
        
        mock_config.return_value = Mock()
        
        result = self.runner.invoke(main, ['install', 'server1', 'server2'], input='y\n')
        
        assert result.exit_code == 0
        assert mock_installer_instance.install.call_count == 2
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_install_command_dry_run(self, mock_installer, mock_config, mock_catalog):
        """Test install command with dry run."""
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test_server"
        mock_server.name = "Test Server"
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        mock_server.installation.package = "test-server"
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = mock_server
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['install', 'test_server', '--dry-run'])
        
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "No actual changes will be made" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_install_command_server_not_found(self, mock_installer, mock_config, mock_catalog):
        """Test install command for non-existent server."""
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = None
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['install', 'nonexistent'])
        
        assert result.exit_code == 1
        assert "not found" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_uninstall_command(self, mock_installer, mock_config, mock_catalog):
        """Test uninstall command."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = "Uninstallation successful"
        
        mock_installer_instance = Mock()
        mock_installer_instance.get_installed_servers.return_value = ["test_server"]
        mock_installer_instance.uninstall.return_value = mock_result
        mock_installer.return_value = mock_installer_instance
        
        mock_catalog.return_value = Mock()
        mock_config.return_value = Mock()
        
        result = self.runner.invoke(main, ['uninstall', 'test_server'], input='y\n')
        
        assert result.exit_code == 0
        assert "Uninstallation successful" in result.output
        mock_installer_instance.uninstall.assert_called_once_with('test_server')
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_uninstall_command_dry_run(self, mock_installer, mock_config, mock_catalog):
        """Test uninstall command with dry run."""
        mock_installer_instance = Mock()
        mock_installer_instance.get_installed_servers.return_value = ["test_server"]
        mock_installer.return_value = mock_installer_instance
        
        mock_catalog.return_value = Mock()
        mock_config.return_value = Mock()
        
        result = self.runner.invoke(main, ['uninstall', 'test_server', '--dry-run'])
        
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_status_command_with_servers(self, mock_installer, mock_config, mock_catalog):
        """Test status command with installed servers."""
        mock_server = Mock(spec=MCPServer)
        mock_server.name = "Test Server"
        mock_server.versions = Mock()
        mock_server.versions.latest = "1.0.0"
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = mock_server
        mock_catalog.return_value = mock_catalog_instance
        
        mock_installer_instance = Mock()
        mock_installer_instance.get_installed_servers.return_value = ["test_server"]
        mock_installer.return_value = mock_installer_instance
        
        mock_config.return_value = Mock()
        
        result = self.runner.invoke(main, ['status'])
        
        assert result.exit_code == 0
        assert "test_server" in result.output
        assert "Test Server" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_status_command_no_servers(self, mock_installer, mock_config, mock_catalog):
        """Test status command with no installed servers."""
        mock_catalog.return_value = Mock()
        mock_config.return_value = Mock()
        
        mock_installer_instance = Mock()
        mock_installer_instance.get_installed_servers.return_value = []
        mock_installer.return_value = mock_installer_instance
        
        result = self.runner.invoke(main, ['status'])
        
        assert result.exit_code == 0
        assert "No MCP servers installed" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_status_command_json_output(self, mock_installer, mock_config, mock_catalog):
        """Test status command with JSON output."""
        mock_server = Mock(spec=MCPServer)
        mock_server.name = "Test Server"
        mock_server.versions = Mock()
        mock_server.versions.latest = "1.0.0"
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = mock_server
        mock_catalog.return_value = mock_catalog_instance
        
        mock_installer_instance = Mock()
        mock_installer_instance.get_installed_servers.return_value = ["test_server"]
        mock_installer.return_value = mock_installer_instance
        
        mock_config.return_value = Mock()
        
        result = self.runner.invoke(main, ['status', '--json'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]['id'] == 'test_server'
        assert output_data[0]['installed'] is True
    
    # Config subcommands tests
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_config_init_command(self, mock_installer, mock_config, mock_catalog):
        """Test config init command."""
        mock_catalog.return_value = Mock()
        mock_installer.return_value = Mock()
        
        mock_config_instance = Mock()
        mock_config_instance.initialize.return_value = True
        mock_config.return_value = mock_config_instance
        
        result = self.runner.invoke(main, ['config', 'init'])
        
        assert result.exit_code == 0
        assert "Configuration initialized successfully" in result.output
        mock_config_instance.initialize.assert_called_once_with(profile=None, template=None)
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_config_init_command_with_options(self, mock_installer, mock_config, mock_catalog):
        """Test config init command with profile and template options."""
        mock_catalog.return_value = Mock()
        mock_installer.return_value = Mock()
        
        mock_config_instance = Mock()
        mock_config_instance.initialize.return_value = True
        mock_config.return_value = mock_config_instance
        
        result = self.runner.invoke(main, ['config', 'init', '--profile', 'test', '--template', 'development'])
        
        assert result.exit_code == 0
        mock_config_instance.initialize.assert_called_once_with(profile='test', template='development')
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_config_init_command_failure(self, mock_installer, mock_config, mock_catalog):
        """Test config init command failure."""
        mock_catalog.return_value = Mock()
        mock_installer.return_value = Mock()
        
        mock_config_instance = Mock()
        mock_config_instance.initialize.return_value = False
        mock_config.return_value = mock_config_instance
        
        result = self.runner.invoke(main, ['config', 'init'])
        
        assert result.exit_code == 1
        assert "Failed to initialize configuration" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_config_show_command(self, mock_installer, mock_config, mock_catalog):
        """Test config show command."""
        mock_catalog.return_value = Mock()
        mock_installer.return_value = Mock()
        
        mock_config_obj = Mock()
        mock_config_obj.model_dump.return_value = {"setting1": "value1", "setting2": "value2"}
        
        mock_config_instance = Mock()
        mock_config_instance.get_config.return_value = mock_config_obj
        mock_config.return_value = mock_config_instance
        
        result = self.runner.invoke(main, ['config', 'show', '--json'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["setting1"] == "value1"
        assert output_data["setting2"] == "value2"
        mock_config_instance.get_config.assert_called_once()
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_config_show_command_with_profile(self, mock_installer, mock_config, mock_catalog):
        """Test config show command with profile option."""
        mock_catalog.return_value = Mock()
        mock_installer.return_value = Mock()
        
        mock_config_obj = Mock()
        mock_config_obj.model_dump.return_value = {"profile": "test_profile"}
        
        mock_config_instance = Mock()
        mock_config_instance.get_config.return_value = mock_config_obj
        mock_config.return_value = mock_config_instance
        
        result = self.runner.invoke(main, ['config', 'show', '--json'])
        
        assert result.exit_code == 0
        mock_config_instance.get_config.assert_called_once()
    
    # Registry subcommands tests
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_registry_update_command(self, mock_installer, mock_config, mock_catalog):
        """Test registry update command."""
        mock_catalog_instance = Mock()
        mock_catalog_instance.update_registry = AsyncMock(return_value=True)
        mock_catalog_instance.list_servers.return_value = [Mock(), Mock()]  # 2 servers
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['update'])
        
        assert result.exit_code == 0
        assert "Registry updated successfully" in result.output
        assert "Registry now contains 2 servers" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_registry_update_command_failure(self, mock_installer, mock_config, mock_catalog):
        """Test registry update command failure."""
        mock_catalog_instance = Mock()
        mock_catalog_instance.update_registry = AsyncMock(return_value=False)
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['update'])
        
        assert result.exit_code == 1
        assert "Failed to update registry" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    @patch('mcpi.cli.DocumentationParser')
    def test_registry_add_command(self, mock_parser_class, mock_installer, mock_config, mock_catalog):
        """Test registry-add command."""
        # Setup mock server info
        mock_server_info = {
            "id": "test-server",
            "name": "Test Server",
            "description": "A test server",
            "author": "Test Author",
            "category": ["test"],
            "installation": {
                "method": "npm",
                "package": "test-server"
            },
            "license": "MIT",
            "capabilities": ["test_operations"]
        }
        
        # Setup mock parser
        mock_parser_instance = Mock()
        mock_parser_instance.parse_documentation_url = AsyncMock(return_value=mock_server_info)
        mock_parser_instance.validate_extracted_info.return_value = (True, [])
        mock_parser_class.return_value = mock_parser_instance
        
        # Setup mock catalog
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = None  # Server doesn't exist
        mock_catalog_instance.add_server.return_value = (True, [])
        mock_catalog_instance.save_registry.return_value = True
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'add', 'https://github.com/test/server'])
        
        assert result.exit_code == 0
        assert "Successfully added 'test-server' to registry" in result.output
        mock_parser_instance.parse_documentation_url.assert_called_once()
        mock_catalog_instance.add_server.assert_called_once()
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    @patch('mcpi.cli.DocumentationParser')
    def test_registry_add_command_dry_run(self, mock_parser_class, mock_installer, mock_config, mock_catalog):
        """Test registry-add command with dry run."""
        mock_server_info = {
            "id": "test-server",
            "name": "Test Server",
            "description": "A test server",
            "author": "Test Author",
            "category": ["test"],
            "installation": {"method": "npm", "package": "test-server"},
            "license": "MIT",
            "capabilities": []
        }
        
        mock_parser_instance = Mock()
        mock_parser_instance.parse_documentation_url = AsyncMock(return_value=mock_server_info)
        mock_parser_instance.validate_extracted_info.return_value = (True, [])
        mock_parser_class.return_value = mock_parser_instance
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = None
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'add', 'https://github.com/test/server', '--dry-run'])
        
        assert result.exit_code == 0
        assert "DRY RUN: Server would be added with the following information" in result.output
        # Ensure we don't actually add the server in dry run
        mock_catalog_instance.add_server.assert_not_called()
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    @patch('mcpi.cli.DocumentationParser')
    def test_registry_add_command_interactive(self, mock_parser_class, mock_installer, mock_config, mock_catalog):
        """Test registry-add command with interactive mode."""
        mock_server_info = {
            "id": "test-server",
            "name": "Test Server",
            "description": "A test server",
            "author": "Test Author",
            "category": ["test"],
            "installation": {"method": "npm", "package": "test-server"},
            "license": "MIT",
            "capabilities": []
        }
        
        mock_parser_instance = Mock()
        mock_parser_instance.parse_documentation_url = AsyncMock(return_value=mock_server_info)
        mock_parser_instance.validate_extracted_info.return_value = (True, [])
        mock_parser_class.return_value = mock_parser_instance
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = None
        mock_catalog_instance.add_server.return_value = (True, [])
        mock_catalog_instance.save_registry.return_value = True
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        # Simulate user confirming and accepting defaults
        user_input = "test-server\nTest Server\nA test server\ny\n"
        result = self.runner.invoke(main, ['registry', 'add', 'https://github.com/test/server', '--interactive'], input=user_input)
        
        assert result.exit_code == 0
        assert "Review and edit information" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    @patch('mcpi.cli.DocumentationParser')
    def test_registry_add_command_force_overwrite(self, mock_parser_class, mock_installer, mock_config, mock_catalog):
        """Test registry-add command with force overwrite."""
        mock_server_info = {
            "id": "existing-server",
            "name": "Existing Server",
            "description": "An existing server",
            "author": "Test Author",
            "category": ["test"],
            "installation": {"method": "npm", "package": "existing-server"},
            "license": "MIT",
            "capabilities": []
        }
        
        mock_parser_instance = Mock()
        mock_parser_instance.parse_documentation_url = AsyncMock(return_value=mock_server_info)
        mock_parser_instance.validate_extracted_info.return_value = (True, [])
        mock_parser_class.return_value = mock_parser_instance
        
        # Mock existing server
        mock_existing_server = Mock()
        mock_catalog_instance = Mock()
        mock_catalog_instance.get_server.return_value = mock_existing_server
        mock_catalog_instance.add_server.return_value = (True, [])
        mock_catalog_instance.save_registry.return_value = True
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'add', 'https://github.com/test/server', '--force'])
        
        assert result.exit_code == 0
        assert "Successfully added 'existing-server' to registry" in result.output
        mock_catalog_instance.add_server.assert_called_once()
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    @patch('mcpi.cli.DocumentationParser')
    def test_registry_add_command_parse_failure(self, mock_parser_class, mock_installer, mock_config, mock_catalog):
        """Test registry-add command when parsing fails."""
        mock_parser_instance = Mock()
        mock_parser_instance.parse_documentation_url = AsyncMock(return_value=None)
        mock_parser_class.return_value = mock_parser_instance
        
        mock_catalog.return_value = Mock()
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'add', 'https://invalid-url.com'])
        
        assert result.exit_code == 1
        assert "Failed to extract server information" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    @patch('mcpi.cli.DocumentationParser')
    def test_registry_add_command_validation_failure(self, mock_parser_class, mock_installer, mock_config, mock_catalog):
        """Test registry-add command when validation fails."""
        mock_server_info = {
            "id": "",  # Invalid empty ID
            "name": "",  # Invalid empty name
        }
        
        mock_parser_instance = Mock()
        mock_parser_instance.parse_documentation_url = AsyncMock(return_value=mock_server_info)
        mock_parser_instance.validate_extracted_info.return_value = (False, ["Invalid server ID", "Invalid server name"])
        mock_parser_class.return_value = mock_parser_instance
        
        mock_catalog.return_value = Mock()
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['registry', 'add', 'https://github.com/test/invalid'])
        
        assert result.exit_code == 1
        assert "Extracted server information is invalid" in result.output
        assert "Invalid server ID" in result.output
    
    # Global option tests
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_verbose_flag(self, mock_installer, mock_config, mock_catalog):
        """Test verbose flag."""
        mock_catalog.return_value = Mock()
        mock_config.return_value = Mock()
        
        mock_installer_instance = Mock()
        mock_installer_instance.get_installed_servers.return_value = []
        mock_installer.return_value = mock_installer_instance
        
        result = self.runner.invoke(main, ['--verbose', 'status'])
        
        assert result.exit_code == 0
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_dry_run_flag(self, mock_installer, mock_config, mock_catalog):
        """Test global dry-run flag."""
        mock_catalog_instance = Mock()
        mock_catalog_instance.list_servers.return_value = []
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = self.runner.invoke(main, ['--dry-run', 'registry', 'list'])
        
        assert result.exit_code == 0
    
    # Error handling tests
    
    def test_main_help(self):
        """Test main help command."""
        result = self.runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "MCPI - MCP Server Package Installer" in result.output
        assert "registry" in result.output
        assert "install" in result.output
        assert "status" in result.output
    
    def test_invalid_command(self):
        """Test invalid command."""
        result = self.runner.invoke(main, ['invalid_command'])
        
        assert result.exit_code != 0
    
    def test_missing_required_argument(self):
        """Test missing required argument."""
        result = self.runner.invoke(main, ['registry', 'show'])  # Missing server_id argument
        
        assert result.exit_code != 0
    
    def test_install_command_no_servers(self):
        """Test install command with no server arguments."""
        result = self.runner.invoke(main, ['install'])
        
        assert result.exit_code == 2
        assert "Missing argument" in result.output
    
    def test_uninstall_command_no_servers(self):
        """Test uninstall command with no server arguments."""
        result = self.runner.invoke(main, ['uninstall'])
        
        assert result.exit_code == 2
        assert "Missing argument" in result.output
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def test_exception_handling(self, mock_installer, mock_config, mock_catalog):
        """Test exception handling in commands."""
        # Make catalog initialization raise an exception
        mock_catalog.side_effect = Exception("Test exception")
        
        result = self.runner.invoke(main, ['registry', 'list'])
        
        assert result.exit_code == 1
        assert "Failed to initialize MCPI" in result.output