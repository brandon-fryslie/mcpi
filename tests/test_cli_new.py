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
        # Add model_dump method for JSON serialization
        mock_server.model_dump.return_value = {
            "id": "test_server",
            "name": "Test Server",
            "description": "A test server",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0"},
            "license": "MIT",
            "installation": {"method": "npm"}
        }
        
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