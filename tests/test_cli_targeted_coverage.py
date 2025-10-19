"""Targeted tests for highest-impact missing lines in CLI module."""

import pytest
import json
from click.testing import CliRunner
from unittest.mock import patch, Mock
from mcpi.cli import main


class TestCLIHighImpactCoverage:
    """Focused tests targeting the most impactful missing CLI lines."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_server = Mock()
        self.mock_server.id = "test-server"
        self.mock_server.name = "Test Server"
        self.mock_server.description = "A test server"
        self.mock_server.model_dump.return_value = {
            "id": "test-server",
            "name": "Test Server", 
            "description": "A test server"
        }
    
    def test_registry_show_json_output(self):
        """Test registry show with --json flag.
        
        Targets lines 134-135: JSON output functionality.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            mock_catalog = Mock()
            mock_catalog_cls.return_value = mock_catalog
            mock_catalog.get_server.return_value = self.mock_server
            
            result = self.runner.invoke(main, [
                'registry', 'show', 'test-server', '--json'
            ])
            
            assert result.exit_code == 0
            # Should output JSON
            try:
                json_data = json.loads(result.output.strip())
                assert json_data["id"] == "test-server"
            except json.JSONDecodeError:
                pytest.fail("Should output valid JSON")
    
    def test_install_cancelled_by_user(self):
        """Test install command when user cancels.
        
        Targets lines 279-280: Installation cancelled message.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            with patch('mcpi.cli.Confirm.ask', return_value=False):
                mock_catalog = Mock()
                mock_catalog_cls.return_value = mock_catalog
                mock_catalog.get_server.return_value = self.mock_server
                
                result = self.runner.invoke(main, ['install', 'test-server'])
                
                assert result.exit_code == 0
                assert "Installation cancelled" in result.output
    
    def test_registry_show_server_not_found(self):
        """Test registry show with non-existent server.
        
        Targets error handling paths.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            mock_catalog = Mock()
            mock_catalog_cls.return_value = mock_catalog
            mock_catalog.get_server.return_value = None
            
            result = self.runner.invoke(main, [
                'registry', 'show', 'nonexistent-server'
            ])
            
            assert result.exit_code == 1
            assert "not found in registry" in result.output
    
    def test_status_with_json_flag(self):
        """Test status command with --json flag.
        
        Targets JSON output paths in status command.
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
            # Should produce JSON output or handle gracefully
            assert len(result.output.strip()) > 0
    
    def test_status_no_servers_configured(self):
        """Test status when no servers configured.
        
        Targets empty server state handling.
        """
        with patch('mcpi.cli.ConfigManager') as mock_config_cls:
            mock_manager = Mock()
            mock_config_cls.return_value = mock_manager
            mock_manager.get_config.return_value = {"mcpServers": {}}
            
            result = self.runner.invoke(main, ['status'])
            
            assert result.exit_code == 0
            assert len(result.output) > 0
    
    def test_install_server_not_found(self):
        """Test install with non-existent server.
        
        Targets install error handling.
        """
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_cls:
            mock_catalog = Mock()
            mock_catalog_cls.return_value = mock_catalog
            mock_catalog.get_server.return_value = None
            
            result = self.runner.invoke(main, ['install', 'nonexistent'])
            
            assert result.exit_code == 1