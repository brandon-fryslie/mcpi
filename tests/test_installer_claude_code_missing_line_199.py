"""Targeted test for missing line 199 in installer/claude_code.py to reach 100% coverage."""

import pytest
from unittest.mock import Mock
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.registry.catalog import MCPServer, InstallationMethod


class TestClaudeCodeInstallerMissingLine199:
    """Test specifically targeting missing line 199 in installer/claude_code.py."""
    
    def test_generate_server_config_with_none_package_details(self):
        """Test _generate_server_config with package_details=None.
        
        This targets line 199: if package_details is None: package_details = {}
        """
        installer = ClaudeCodeInstaller()
        
        # Create mock server
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test-server"
        mock_server.installation = Mock()
        mock_server.installation.method = InstallationMethod.NPM
        mock_server.installation.package = "test-package"
        mock_server.configuration = Mock()
        mock_server.configuration.required_params = []
        mock_server.configuration.optional_params = []
        
        # Create config_params
        config_params = {"test": "value"}
        
        # Call _generate_server_config with package_details=None
        # This should trigger line 199: package_details = {}
        config = installer._generate_server_config(mock_server, config_params, package_details=None)
        
        # Verify that the method handled None properly and returned a config
        assert isinstance(config, dict)
        
    def test_generate_server_config_with_provided_package_details(self):
        """Test _generate_server_config with provided package_details (for comparison)."""
        installer = ClaudeCodeInstaller()
        
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test-server-2"
        mock_server.installation = Mock()
        mock_server.installation.method = InstallationMethod.PIP
        mock_server.installation.package = "test-package-pip"
        mock_server.configuration = Mock()
        mock_server.configuration.required_params = ["param1"]
        mock_server.configuration.optional_params = ["param2"]
        
        # Create config_params and package_details
        config_params = {"config": "value"}
        package_details = {"param1": "value1", "param2": "value2"}
        
        # Call with actual package_details
        config = installer._generate_server_config(mock_server, config_params, package_details=package_details)
        
        # Verify configuration was created
        assert isinstance(config, dict)
        
    def test_generate_server_config_git_method_none_package_details(self):
        """Test _generate_server_config with Git method and None package_details."""
        installer = ClaudeCodeInstaller()
        
        mock_server = Mock(spec=MCPServer)
        mock_server.id = "test-git-server"
        mock_server.installation = Mock()
        mock_server.installation.method = InstallationMethod.GIT
        mock_server.installation.package = "https://github.com/test/repo.git"
        mock_server.configuration = Mock()
        mock_server.configuration.required_params = []
        mock_server.configuration.optional_params = []
        
        # Create config_params
        config_params = {"git": "config"}
        
        # This should also trigger line 199
        config = installer._generate_server_config(mock_server, config_params, package_details=None)
        
        assert isinstance(config, dict)