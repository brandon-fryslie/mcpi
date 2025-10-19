"""Targeted test for missing line in installer/claude_code.py to reach 100% coverage."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.registry.catalog import MCPServer, ServerInstallation, InstallationMethod


class TestMissingClaudeCodeCoverage:
    """Tests specifically targeting missing line 199 in installer/claude_code.py."""
    
    def test_create_claude_code_config_with_none_package_details(self):
        """Test create_claude_code_config with None package_details.
        
        This test specifically targets line 199:
        if package_details is None:
            package_details = {}
        """
        installer = ClaudeCodeInstaller()
        
        # Create a mock server
        mock_server = Mock(spec=MCPServer)
        mock_server.installation = Mock(spec=ServerInstallation)
        mock_server.installation.method = InstallationMethod.NPM
        mock_server.installation.package = "test-package"
        
        # Call with package_details=None to trigger line 199
        config = installer.create_claude_code_config(mock_server, package_details=None)
        
        # Should not raise an error and should create valid config
        assert isinstance(config, dict)
        assert "command" in config  # Should have NPM command
        assert config["command"] == "npx"
    
    def test_create_claude_code_config_with_provided_package_details(self):
        """Test create_claude_code_config with provided package_details."""
        installer = ClaudeCodeInstaller()
        
        mock_server = Mock(spec=MCPServer)
        mock_server.installation = Mock(spec=ServerInstallation)
        mock_server.installation.method = InstallationMethod.NPM
        mock_server.installation.package = "test-package"
        
        # Provide package_details (should not hit line 199)
        package_details = {"version": "1.0.0"}
        config = installer.create_claude_code_config(mock_server, package_details=package_details)
        
        assert isinstance(config, dict)
        assert "command" in config
        assert config["command"] == "npx"
    
    def test_create_claude_code_config_pip_method_none_package_details(self):
        """Test create_claude_code_config with PIP method and None package_details."""
        installer = ClaudeCodeInstaller()
        
        mock_server = Mock(spec=MCPServer)
        mock_server.installation = Mock(spec=ServerInstallation)
        mock_server.installation.method = InstallationMethod.PIP
        mock_server.installation.package = "test-package"
        
        # Call with package_details=None for PIP method
        config = installer.create_claude_code_config(mock_server, package_details=None)
        
        assert isinstance(config, dict)
        # Should handle PIP method appropriately
        
    def test_create_claude_code_config_git_method_none_package_details(self):
        """Test create_claude_code_config with GIT method and None package_details."""
        installer = ClaudeCodeInstaller()
        
        mock_server = Mock(spec=MCPServer)
        mock_server.installation = Mock(spec=ServerInstallation)
        mock_server.installation.method = InstallationMethod.GIT
        mock_server.installation.package = "https://github.com/test/repo"
        
        # Call with package_details=None for GIT method
        config = installer.create_claude_code_config(mock_server, package_details=None)
        
        assert isinstance(config, dict)
        # Should handle GIT method appropriately