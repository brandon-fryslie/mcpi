"""Comprehensive tests for the CLI module."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from pathlib import Path

from mcpi.cli import main, get_method_string
from mcpi.registry.catalog import ServerCatalog, MCPServer, InstallationMethod
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.config.manager import ConfigManager
from tests.conftest import create_mock_server


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_get_method_string_with_enum(self):
        """Test get_method_string with enum value."""
        method = InstallationMethod.NPM
        result = get_method_string(method)
        assert result == "npm"
    
    def test_get_method_string_with_string(self):
        """Test get_method_string with string value."""
        method = "pip"
        result = get_method_string(method)
        assert result == "pip"
    
    def test_get_method_string_with_none(self):
        """Test get_method_string with None value."""
        method = None
        result = get_method_string(method)
        assert result == "None"


class TestMainCommand:
    """Tests for main command and global options."""
    
    def test_main_command_help(self):
        """Test main command displays help."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'MCPI - MCP Server Package Installer' in result.output
        assert '--verbose' in result.output
        assert '--dry-run' in result.output
    
    def test_main_command_verbose_flag(self):
        """Test main command with verbose flag."""
        runner = CliRunner()
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            result = runner.invoke(main, ['--verbose', 'registry', 'list'])
            
            # Should not error on initialization
            assert result.exit_code == 0
    
    def test_main_command_dry_run_flag(self):
        """Test main command with dry-run flag."""
        runner = CliRunner()
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            result = runner.invoke(main, ['--dry-run', 'registry', 'list'])
            
            # Should pass dry_run=True to installer
            mock_installer_class.assert_called_once_with(dry_run=True)
    
    def test_main_command_initialization_error(self):
        """Test main command handling initialization errors."""
        runner = CliRunner()
        with patch('mcpi.cli.ServerCatalog', side_effect=Exception("Init failed")):
            result = runner.invoke(main, ['registry', 'list'])
            
            assert result.exit_code != 0
            assert 'Failed to initialize MCPI' in result.output
    
    def test_main_command_initialization_error_verbose(self):
        """Test main command handling initialization errors with verbose."""
        runner = CliRunner()
        with patch('mcpi.cli.ServerCatalog', side_effect=Exception("Init failed")):
            result = runner.invoke(main, ['--verbose', 'registry', 'list'])
            
            assert 'Initialization error: Init failed' in result.output


class TestRegistryCommands:
    """Tests for registry management commands."""
    
    def test_registry_list_basic(self):
        """Test basic registry list command."""
        runner = CliRunner()
        
        mock_server = create_mock_server()
        mock_server.id = "test-server"
        mock_server.name = "Test Server" 
        mock_server.description = "Test description"
        mock_server.category = "database"
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.list_servers.return_value = [mock_server]
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'list'])
            
            assert result.exit_code == 0
            assert 'test-server' in result.output
            assert 'Test Server' in result.output
    
    def test_registry_list_with_search(self):
        """Test registry list with search filter."""
        runner = CliRunner()
        
        mock_server = create_mock_server()
        mock_server.id = "database-server"
        mock_server.name = "Database Server"
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.list_servers.return_value = [mock_server]
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'list', '--search', 'database'])
            
            assert result.exit_code == 0
            mock_catalog.list_servers.assert_called_once_with(
                search='database', 
                category=None, 
                installation_method=None
            )
    
    def test_registry_list_with_category(self):
        """Test registry list with category filter."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.list_servers.return_value = []
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'list', '--category', 'database'])
            
            assert result.exit_code == 0
            mock_catalog.list_servers.assert_called_once_with(
                search=None, 
                category='database', 
                installation_method=None
            )
    
    def test_registry_list_json_output(self):
        """Test registry list with JSON output."""
        runner = CliRunner()
        
        mock_server = create_mock_server()
        mock_server.id = "test-server"
        mock_server.model_dump.return_value = {"id": "test-server", "name": "Test"}
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.list_servers.return_value = [mock_server]
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'list', '--json'])
            
            assert result.exit_code == 0
            # Should contain JSON output
            assert '{"id": "test-server"' in result.output.replace(' ', '').replace('\n', '')
    
    def test_registry_show_success(self):
        """Test registry show command success."""
        runner = CliRunner()
        
        mock_server = create_mock_server()
        mock_server.id = "test-server"
        mock_server.name = "Test Server"
        mock_server.description = "Test description"
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.get_server.return_value = mock_server
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'show', 'test-server'])
            
            assert result.exit_code == 0
            assert 'Test Server' in result.output
            assert 'Test description' in result.output
    
    def test_registry_show_not_found(self):
        """Test registry show command with server not found."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.get_server.return_value = None
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'show', 'nonexistent'])
            
            assert result.exit_code != 0
            assert 'Server not found' in result.output or 'not found' in result.output
    
    def test_registry_search_success(self):
        """Test registry search command."""
        runner = CliRunner()
        
        mock_server = create_mock_server()
        mock_server.id = "search-result"
        mock_server.name = "Search Result"
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.search_servers.return_value = [mock_server]
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'search', 'test'])
            
            assert result.exit_code == 0
            assert 'search-result' in result.output
            mock_catalog.search_servers.assert_called_once_with('test')
    
    def test_registry_validate_success(self):
        """Test registry validate command success."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.validate_registry.return_value = True
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'validate'])
            
            assert result.exit_code == 0
            assert 'valid' in result.output.lower()
    
    def test_registry_validate_failure(self):
        """Test registry validate command failure."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager'), \
             patch('mcpi.cli.ClaudeCodeInstaller'):
            
            mock_catalog = Mock()
            mock_catalog.validate_registry.return_value = False
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'validate'])
            
            assert result.exit_code != 0
            assert 'invalid' in result.output.lower() or 'failed' in result.output.lower()


class TestInstallCommands:
    """Tests for install/uninstall commands."""
    
    def test_install_single_server(self):
        """Test installing a single server."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.install_server.return_value = True
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['install', 'test-server'])
            
            assert result.exit_code == 0
            mock_installer.install_server.assert_called_once_with('test-server')
    
    def test_install_multiple_servers(self):
        """Test installing multiple servers."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.install_server.return_value = True
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['install', 'server1', 'server2'])
            
            assert result.exit_code == 0
            assert mock_installer.install_server.call_count == 2
            mock_installer.install_server.assert_any_call('server1')
            mock_installer.install_server.assert_any_call('server2')
    
    def test_install_with_force(self):
        """Test install with force flag."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.install_server.return_value = True
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['install', '--force', 'test-server'])
            
            assert result.exit_code == 0
            mock_installer.install_server.assert_called_once_with('test-server')
    
    def test_install_failure(self):
        """Test install command failure."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.install_server.return_value = False
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['install', 'test-server'])
            
            assert result.exit_code != 0
    
    def test_uninstall_single_server(self):
        """Test uninstalling a single server."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.uninstall_server.return_value = True
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['uninstall', 'test-server'])
            
            assert result.exit_code == 0
            mock_installer.uninstall_server.assert_called_once_with('test-server')
    
    def test_uninstall_multiple_servers(self):
        """Test uninstalling multiple servers."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.uninstall_server.return_value = True
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['uninstall', 'server1', 'server2'])
            
            assert result.exit_code == 0
            assert mock_installer.uninstall_server.call_count == 2
            mock_installer.uninstall_server.assert_any_call('server1')
            mock_installer.uninstall_server.assert_any_call('server2')


class TestStatusCommand:
    """Tests for status command."""
    
    def test_status_basic(self):
        """Test basic status command."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.get_installed_servers.return_value = ['server1', 'server2']
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['status'])
            
            assert result.exit_code == 0
            assert 'server1' in result.output
            assert 'server2' in result.output
    
    def test_status_with_profile(self):
        """Test status command with profile filter."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.get_installed_servers.return_value = []
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['status', '--profile', 'test-profile'])
            
            assert result.exit_code == 0
    
    def test_status_json_output(self):
        """Test status command with JSON output."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_installer = Mock()
            mock_installer.get_installed_servers.return_value = ['server1']
            mock_installer_class.return_value = mock_installer
            
            result = runner.invoke(main, ['status', '--json'])
            
            assert result.exit_code == 0
            # Should contain JSON-like output
            assert '[' in result.output or '{' in result.output


class TestConfigCommands:
    """Tests for config management commands."""
    
    def test_config_init_basic(self):
        """Test basic config init command."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_config = Mock()
            mock_config.initialize_config.return_value = True
            mock_config_class.return_value = mock_config
            
            result = runner.invoke(main, ['config', 'init'])
            
            assert result.exit_code == 0
            mock_config.initialize_config.assert_called_once()
    
    def test_config_init_with_profile(self):
        """Test config init with profile."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_config = Mock()
            mock_config.initialize_config.return_value = True
            mock_config_class.return_value = mock_config
            
            result = runner.invoke(main, ['config', 'init', '--profile', 'test-profile'])
            
            assert result.exit_code == 0
    
    def test_config_show_basic(self):
        """Test basic config show command."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_config_obj = Mock()
            mock_config_obj.general = Mock()
            mock_config_obj.general.registry_url = "test-url"
            mock_config_obj.general.default_profile = "default"
            mock_config_obj.profiles = {}
            
            mock_config = Mock()
            mock_config.get_config.return_value = mock_config_obj
            mock_config_class.return_value = mock_config
            
            result = runner.invoke(main, ['config', 'show'])
            
            assert result.exit_code == 0
            assert 'test-url' in result.output
    
    def test_config_show_json(self):
        """Test config show with JSON output."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_config_obj = Mock()
            mock_config_obj.model_dump.return_value = {"test": "config"}
            
            mock_config = Mock()
            mock_config.get_config.return_value = mock_config_obj
            mock_config_class.return_value = mock_config
            
            result = runner.invoke(main, ['config', 'show', '--json'])
            
            assert result.exit_code == 0
            assert '"test": "config"' in result.output.replace(' ', '')
    
    def test_config_validate_success(self):
        """Test config validate command success."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_config = Mock()
            mock_config.validate_config.return_value = []  # No errors
            mock_config_class.return_value = mock_config
            
            result = runner.invoke(main, ['config', 'validate'])
            
            assert result.exit_code == 0
            assert 'valid' in result.output.lower()
    
    def test_config_validate_with_errors(self):
        """Test config validate command with validation errors."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_config = Mock()
            mock_config.validate_config.return_value = ["Error 1", "Error 2"]
            mock_config_class.return_value = mock_config
            
            result = runner.invoke(main, ['config', 'validate'])
            
            assert result.exit_code != 0
            assert 'Error 1' in result.output
            assert 'Error 2' in result.output


class TestUpdateCommands:
    """Tests for update commands."""
    
    def test_update_success(self):
        """Test update command success."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_catalog = Mock()
            mock_catalog.update_registry.return_value = True
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['update'])
            
            assert result.exit_code == 0
            mock_catalog.update_registry.assert_called_once()
    
    def test_update_failure(self):
        """Test update command failure."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_catalog = Mock()
            mock_catalog.update_registry.return_value = False
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['update'])
            
            assert result.exit_code != 0
    
    def test_registry_add_success(self):
        """Test registry add command success."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_catalog = Mock()
            mock_catalog.add_registry_url.return_value = True
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'add', 'https://example.com/registry.json'])
            
            assert result.exit_code == 0
            mock_catalog.add_registry_url.assert_called_once_with(
                'https://example.com/registry.json'
            )
    
    def test_registry_add_with_flags(self):
        """Test registry add with various flags."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_catalog = Mock()
            mock_catalog.add_registry_url.return_value = True
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, [
                'registry', 'add', 
                '--dry-run', 
                '--force', 
                '--interactive',
                'https://example.com/registry.json'
            ])
            
            assert result.exit_code == 0


class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    def test_command_with_exception(self):
        """Test command behavior when an unexpected exception occurs."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_catalog = Mock()
            mock_catalog.list_servers.side_effect = Exception("Unexpected error")
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'list'])
            
            # Should handle the exception gracefully
            assert result.exit_code != 0
    
    def test_command_keyboard_interrupt(self):
        """Test command behavior on keyboard interrupt."""
        runner = CliRunner()
        
        with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
             patch('mcpi.cli.ConfigManager') as mock_config_class, \
             patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
            
            mock_catalog = Mock()
            mock_catalog.list_servers.side_effect = KeyboardInterrupt()
            mock_catalog_class.return_value = mock_catalog
            
            result = runner.invoke(main, ['registry', 'list'])
            
            # Should handle keyboard interrupt gracefully
            assert result.exit_code != 0