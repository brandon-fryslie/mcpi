#!/usr/bin/env python3

"""Debug script to test CLI command structure with exact test setup."""

from click.testing import CliRunner
from unittest.mock import Mock, patch
from mcpi.cli import main
from mcpi.registry.catalog import MCPServer

def test_debug_exact():
    runner = CliRunner()
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def run_test(mock_installer, mock_config, mock_catalog):
        """Test basic list command."""
        # Setup mocks - exact copy from test
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test_server"
        mock_server.name = "Test Server"
        mock_server.description = "A test server"
        mock_server.category = ["test"]
        mock_server.author = "Test Author"
        mock_server.versions = Mock()
        mock_server.versions.latest = "1.0.0"
        
        # Missing installation mock! This is the issue
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        
        mock_catalog_instance = Mock()
        mock_catalog_instance.list_servers.return_value = [mock_server]
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        # Run command
        result = runner.invoke(main, ['registry', 'list'])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    run_test()

if __name__ == '__main__':
    test_debug_exact()