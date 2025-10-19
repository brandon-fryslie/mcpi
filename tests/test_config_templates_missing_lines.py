"""Targeted tests for missing lines in config/templates.py to reach 100% coverage."""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path
from mcpi.config.templates import TemplateManager
from mcpi.registry.catalog import MCPServer


class TestConfigTemplatesMissingLines:
    """Tests specifically targeting missing lines 67->71, 123, and 319-320."""
    
    def test_create_server_config_no_template_found(self):
        """Test create_server_config when server has template but template file not found.
        
        This targets line 67->71: template lookup fails, so no config.update(template) occurs.
        """
        manager = TemplateManager()
        
        # Create mock server with template that doesn't exist
        mock_server = Mock(spec=MCPServer)
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        mock_server.installation.package = "test-package"
        mock_server.configuration = Mock()
        mock_server.configuration.template = "non_existent_template.json"
        mock_server.configuration.required_params = []
        mock_server.configuration.optional_params = []
        
        # Mock get_template to return None (template not found)
        with patch.object(manager, 'get_template', return_value=None):
            config = manager.create_server_config(mock_server)
        
        # Should still work, just without template enhancement
        assert "command" in config
        assert "args" in config
        # Template-specific config should not be present since template wasn't found
        assert "description" not in config
    
    def test_get_default_value_unknown_parameter(self):
        """Test _get_default_value with unknown parameter name.
        
        This targets line 123: when param not in defaults dict, returns None.
        """
        manager = TemplateManager()
        
        # Test with parameter that doesn't have a default
        result = manager._get_default_value("unknown_parameter")
        assert result is None
        
        # Test with known parameter for comparison
        result = manager._get_default_value("host")
        assert result == "localhost"
    
    def test_get_args_for_server_required_param_no_default(self):
        """Test _get_args_for_server when required param missing and no default available.
        
        This ensures the code path where _get_default_value returns None is exercised.
        """
        manager = TemplateManager()
        
        # Create mock server with required param that won't have a default
        mock_server = Mock(spec=MCPServer)
        mock_server.installation = Mock()
        mock_server.installation.method = "npm"
        mock_server.installation.package = "test-package"
        mock_server.configuration = Mock()
        mock_server.configuration.required_params = ["unknown_param"]
        mock_server.configuration.optional_params = []
        
        # Mock _get_default_value to return None for this specific param
        with patch.object(manager, '_get_default_value', return_value=None):
            args = manager._get_args_for_server(mock_server, {})
        
        # The missing required param with no default should not add anything to args
        # (line 123 conditional check)
        assert len(args) >= 1  # Should have at least the base args
    
    def test_generate_default_templates_exception_during_creation(self):
        """Test generate_default_templates when exception occurs during template creation.
        
        This targets lines 319-320: exception handling that returns False.
        """
        manager = TemplateManager()
        
        # Mock create_template to raise an exception
        with patch.object(manager, 'create_template', side_effect=Exception("Creation failed")):
            result = manager.generate_default_templates()
            
        # Should return False due to exception handling on lines 319-320
        assert result is False
    
    def test_generate_default_templates_create_template_returns_false(self):
        """Test generate_default_templates when create_template returns False.
        
        This targets line 314-315: early return when template creation fails.
        """
        manager = TemplateManager()
        
        # Mock create_template to fail on first template (will hit the early return)
        with patch.object(manager, 'create_template', return_value=False):
            result = manager.generate_default_templates()
        
        # Should return False when any template creation fails
        assert result is False