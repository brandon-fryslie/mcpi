#!/usr/bin/env python3

"""Fix for the search test to understand the actual return format."""

from click.testing import CliRunner
from unittest.mock import Mock, patch
from mcpi.cli import main
from mcpi.registry.catalog import MCPServer

def test_search_fix():
    runner = CliRunner()
    
    @patch('mcpi.cli.ServerCatalog')
    @patch('mcpi.cli.ConfigManager')
    @patch('mcpi.cli.ClaudeCodeInstaller')
    def run_test(mock_installer, mock_config, mock_catalog):
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
        # search_servers returns (server, score) tuples, not just servers
        mock_catalog_instance.search_servers.return_value = [(mock_server, 0.95)]
        mock_catalog.return_value = mock_catalog_instance
        
        mock_config.return_value = Mock()
        mock_installer.return_value = Mock()
        
        result = runner.invoke(main, ['registry', 'search', 'filesystem'])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    run_test()

if __name__ == '__main__':
    test_search_fix()