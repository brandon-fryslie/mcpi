"""Refactored CLI tests with improved structure and maintainability."""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from mcpi.cli import main, get_method_string
from mcpi.registry.catalog import InstallationMethod


@pytest.fixture
def cli_runner():
    """Provide a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_cli_components():
    """Mock all CLI components with proper structure."""
    with patch('mcpi.cli.ServerCatalog') as mock_catalog_class, \
         patch('mcpi.cli.ConfigManager') as mock_config_class, \
         patch('mcpi.cli.ClaudeCodeInstaller') as mock_installer_class:
        
        # Set up mocks with sensible defaults
        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = []
        mock_catalog.get_server.return_value = None
        mock_catalog.search_servers.return_value = []
        mock_catalog.validate_registry.return_value = True
        mock_catalog_class.return_value = mock_catalog
        
        mock_config = Mock()
        mock_config.get_config.return_value = Mock()
        mock_config.validate_config.return_value = []
        mock_config_class.return_value = mock_config
        
        mock_installer = Mock()
        mock_installer.install_server.return_value = True
        mock_installer.uninstall_server.return_value = True
        mock_installer.get_installed_servers.return_value = []
        mock_installer_class.return_value = mock_installer
        
        yield {
            'catalog': mock_catalog,
            'config': mock_config,
            'installer': mock_installer
        }


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_get_method_string_variations(self):
        """Test get_method_string with different input types."""
        # Test with enum
        assert get_method_string(InstallationMethod.NPM) == "InstallationMethod.NPM"
        
        # Test with string
        assert get_method_string("pip") == "pip"
        
        # Test with None
        assert get_method_string(None) == "None"


class TestMainCommand:
    """Tests for main command functionality."""
    
    def test_help_display(self, cli_runner):
        """Test that help is displayed correctly."""
        result = cli_runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'MCPI - MCP Server Package Installer' in result.output
        assert '--verbose' in result.output
        assert '--dry-run' in result.output
    
    def test_global_options(self, cli_runner, mock_cli_components):
        """Test global options are processed correctly."""
        result = cli_runner.invoke(main, ['--verbose', '--dry-run', 'registry', 'list'])
        assert result.exit_code == 0
    
    def test_initialization_error_handling(self, cli_runner):
        """Test graceful handling of initialization errors."""
        with patch('mcpi.cli.ServerCatalog', side_effect=Exception("Init failed")):
            result = cli_runner.invoke(main, ['registry', 'list'])
            assert result.exit_code != 0
            assert 'Failed to initialize MCPI' in result.output


class TestRegistryCommands:
    """Tests for registry-related commands."""
    
    def test_registry_list_basic(self, cli_runner, mock_cli_components):
        """Test basic registry list functionality."""
        # Set up mock server
        mock_server = Mock()
        mock_server.id = "test-server"
        mock_server.name = "Test Server"
        mock_server.description = "Test description"
        mock_server.category = "database"
        
        mock_cli_components['catalog'].list_servers.return_value = [mock_server]
        
        result = cli_runner.invoke(main, ['registry', 'list'])
        
        assert result.exit_code == 0
        assert 'test-server' in result.output
    
    def test_registry_show_not_found(self, cli_runner, mock_cli_components):
        """Test registry show with non-existent server."""
        mock_cli_components['catalog'].get_server.return_value = None
        
        result = cli_runner.invoke(main, ['registry', 'show', 'nonexistent'])
        
        assert result.exit_code != 0


class TestInstallCommands:
    """Tests for install/uninstall commands."""
    
    def test_install_success(self, cli_runner, mock_cli_components):
        """Test successful server installation."""
        result = cli_runner.invoke(main, ['install', 'test-server'])
        
        assert result.exit_code == 0
        mock_cli_components['installer'].install_server.assert_called_once_with('test-server')
    
    def test_install_failure(self, cli_runner, mock_cli_components):
        """Test installation failure handling."""
        mock_cli_components['installer'].install_server.return_value = False
        
        result = cli_runner.invoke(main, ['install', 'test-server'])
        
        assert result.exit_code != 0
    
    def test_uninstall_success(self, cli_runner, mock_cli_components):
        """Test successful server uninstallation."""
        result = cli_runner.invoke(main, ['uninstall', 'test-server'])
        
        assert result.exit_code == 0
        mock_cli_components['installer'].uninstall_server.assert_called_once_with('test-server')


class TestConfigCommands:
    """Tests for configuration commands."""
    
    def test_config_show(self, cli_runner, mock_cli_components):
        """Test config show command."""
        # Set up mock config
        mock_config_obj = Mock()
        mock_config_obj.general = Mock()
        mock_config_obj.general.registry_url = "test-url"
        mock_config_obj.general.default_profile = "default"
        mock_config_obj.profiles = {}
        
        mock_cli_components['config'].get_config.return_value = mock_config_obj
        
        result = cli_runner.invoke(main, ['config', 'show'])
        
        assert result.exit_code == 0
        assert 'test-url' in result.output
    
    def test_config_validate_success(self, cli_runner, mock_cli_components):
        """Test config validation success."""
        result = cli_runner.invoke(main, ['config', 'validate'])
        
        assert result.exit_code == 0
        mock_cli_components['config'].validate_config.assert_called_once()
    
    def test_config_validate_errors(self, cli_runner, mock_cli_components):
        """Test config validation with errors."""
        mock_cli_components['config'].validate_config.return_value = ["Error 1"]
        
        result = cli_runner.invoke(main, ['config', 'validate'])
        
        assert result.exit_code != 0
        assert 'Error 1' in result.output


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_exception_handling(self, cli_runner, mock_cli_components):
        """Test graceful exception handling."""
        mock_cli_components['catalog'].list_servers.side_effect = Exception("Test error")
        
        result = cli_runner.invoke(main, ['registry', 'list'])
        
        # Should not crash, should exit with error code
        assert result.exit_code != 0
    
    def test_keyboard_interrupt(self, cli_runner, mock_cli_components):
        """Test keyboard interrupt handling."""
        mock_cli_components['catalog'].list_servers.side_effect = KeyboardInterrupt()
        
        result = cli_runner.invoke(main, ['registry', 'list'])
        
        assert result.exit_code != 0