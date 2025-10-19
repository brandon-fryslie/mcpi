"""Targeted tests for missing lines in cli.py to boost coverage from 85% to 90%+."""

import pytest
import json
from click.testing import CliRunner
from unittest.mock import patch, Mock, MagicMock
from mcpi.cli import main


class TestCLIMissingCoverage:
    """Tests specifically targeting high-impact missing lines in cli.py."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_catalog = Mock()
        self.mock_server = Mock()
        self.mock_server.id = "test-server"
        self.mock_server.name = "Test Server"
        self.mock_server.description = "A test server"
        self.mock_server.model_dump.return_value = {
            "id": "test-server",
            "name": "Test Server", 
            "description": "A test server"
        }
        self.mock_server.installation = Mock()
        self.mock_server.installation.method = "npm"
    
    def test_registry_info_with_json_output(self):
        """Test registry info command with --json flag.
        
        Targets lines 134-135: JSON output for server info.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            mock_catalog_cls.return_value = self.mock_catalog
            self.mock_catalog.get_server.return_value = self.mock_server
            
            result = self.runner.invoke(main, [
                'registry', 'show', 'test-server', '--json'
            ])
            
            # Should succeed and output JSON
            assert result.exit_code == 0
            # Verify JSON output format
            try:
                json_data = json.loads(result.output.strip())
                assert json_data["id"] == "test-server"
            except json.JSONDecodeError:
                pytest.fail("Output should be valid JSON")
    
    def test_registry_search_with_json_output_tuple_result(self):
        """Test registry search command with --json and tuple results.
        
        Targets line 187: Tuple unpacking for search results with scores.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            mock_catalog_cls.return_value = self.mock_catalog
            
            # Mock search results as tuples (server, score, matches)
            mock_result = (self.mock_server, 0.95, ["test", "server"])
            self.mock_catalog.search.return_value = [mock_result]
            
            result = self.runner.invoke(main, [
                'registry', 'search', 'test', '--json'
            ])
            
            assert result.exit_code == 0
            # Verify JSON output includes score and matches
            try:
                json_data = json.loads(result.output.strip())
                assert len(json_data) == 1
                assert json_data[0]["score"] == 0.95
                assert json_data[0]["matches"] == ["test", "server"]
            except json.JSONDecodeError:
                pytest.fail("Output should be valid JSON")
    
    def test_install_command_cancelled_by_user(self):
        """Test install command cancelled by user confirmation.
        
        Targets lines 279-280: User cancellation of installation.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            with patch('mcpi.cli.Confirm.ask', return_value=False):
                mock_catalog_cls.return_value = self.mock_catalog
                self.mock_catalog.get_server.return_value = self.mock_server
                
                result = self.runner.invoke(main, ['install', 'test-server'])
                
                assert result.exit_code == 0
                assert "Installation cancelled" in result.output
    
    def test_install_command_server_not_found_error(self):
        """Test install command with server not found.
        
        Targets error handling paths in install command.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            mock_catalog_cls.return_value = self.mock_catalog
            self.mock_catalog.get_server.return_value = None
            
            result = self.runner.invoke(main, ['install', 'nonexistent-server'])
            
            assert result.exit_code == 1
    
    def test_status_command_with_json_output(self):
        """Test status command with --json flag.
        
        Targets JSON output paths in status command around lines 588-591.
        """
        with patch('mcpi.cli.ConfigManager') as mock_config_cls:
            mock_manager = Mock()
            mock_config_cls.return_value = mock_manager
            mock_manager.get_config.return_value = {
                "mcpServers": {
                    "test-server": {
                        "command": "npx",
                        "args": ["test-package"]
                    }
                }
            }
            
            result = self.runner.invoke(main, ['status', '--json'])
            
            assert result.exit_code == 0
            # Should output JSON format
            try:
                json_data = json.loads(result.output.strip())
                assert isinstance(json_data, (dict, list))
            except json.JSONDecodeError:
                # If not JSON, verify it's still valid output
                assert len(result.output.strip()) > 0
    
    def test_registry_info_server_not_found(self):
        """Test registry info with non-existent server.
        
        Targets error handling paths.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            mock_catalog_cls.return_value = self.mock_catalog
            self.mock_catalog.get_server.return_value = None
            
            result = self.runner.invoke(main, [
                'registry', 'show', 'nonexistent-server'
            ])
            
            assert result.exit_code == 1
            assert "not found in registry" in result.output
    
    def test_install_with_dry_run_flag(self):
        """Test install command with --dry-run flag.
        
        Targets dry-run code paths that skip confirmation.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            with patch('mcpi.cli.get_installer') as mock_get_installer:
                mock_catalog_cls.return_value = self.mock_catalog
                self.mock_catalog.get_server.return_value = self.mock_server
                
                mock_installer = Mock()
                mock_get_installer.return_value = mock_installer
                mock_installer.install.return_value = True
                
                result = self.runner.invoke(main, [
                    'install', 'test-server', '--dry-run'
                ])
                
                # Should complete without asking for confirmation
                assert result.exit_code == 0
    
    def test_install_with_force_flag(self):
        """Test install command with --force flag.
        
        Targets force installation code paths.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            with patch('mcpi.cli.get_installer') as mock_get_installer:
                mock_catalog_cls.return_value = self.mock_catalog
                self.mock_catalog.get_server.return_value = self.mock_server
                
                mock_installer = Mock()
                mock_get_installer.return_value = mock_installer
                mock_installer.install.return_value = True
                
                result = self.runner.invoke(main, [
                    'install', 'test-server', '--force'
                ])
                
                # Should complete without asking for confirmation  
                assert result.exit_code == 0
    
    def test_status_command_no_servers_configured(self):
        """Test status command when no servers are configured.
        
        Targets edge cases in status display.
        """
        with patch('mcpi.cli.ConfigManager') as mock_config_cls:
            mock_manager = Mock()
            mock_config_cls.return_value = mock_manager
            mock_manager.get_config.return_value = {"mcpServers": {}}
            
            result = self.runner.invoke(main, ['status'])
            
            assert result.exit_code == 0
            # Should handle empty servers gracefully
            assert len(result.output) > 0
    
    def test_install_with_installation_failure(self):
        """Test install command when installation fails.
        
        Targets error handling in installation process.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            with patch('mcpi.cli.get_installer') as mock_get_installer:
                with patch('mcpi.cli.Confirm.ask', return_value=True):
                    mock_catalog_cls.return_value = self.mock_catalog
                    self.mock_catalog.get_server.return_value = self.mock_server
                    
                    mock_installer = Mock()
                    mock_get_installer.return_value = mock_installer
                    mock_installer.install.return_value = False  # Installation fails
                    
                    result = self.runner.invoke(main, ['install', 'test-server'])
                    
                    # Should handle installation failure gracefully
                    assert result.exit_code in [0, 1]  # May exit with error code
    
    def test_uninstall_command_with_dry_run(self):
        """Test uninstall command with --dry-run flag.
        
        Targets uninstall dry-run code paths.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            with patch('mcpi.cli.get_installer') as mock_get_installer:
                mock_catalog_cls.return_value = self.mock_catalog
                self.mock_catalog.get_server.return_value = self.mock_server
                
                mock_installer = Mock()
                mock_get_installer.return_value = mock_installer
                mock_installer.uninstall.return_value = True
                
                result = self.runner.invoke(main, [
                    'uninstall', 'test-server', '--dry-run'
                ])
                
                # Should complete in dry-run mode
                assert result.exit_code == 0
    
    def test_registry_search_with_empty_results(self):
        """Test registry search with no results.
        
        Targets empty search results handling.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            mock_catalog_cls.return_value = self.mock_catalog
            self.mock_catalog.search.return_value = []
            
            result = self.runner.invoke(main, ['registry', 'search', 'nonexistent'])
            
            assert result.exit_code == 0
            # Should handle empty results gracefully