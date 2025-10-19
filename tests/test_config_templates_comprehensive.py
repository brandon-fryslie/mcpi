"""Comprehensive tests for the config templates module."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from mcpi.config.templates import TemplateManager
from mcpi.registry.catalog import MCPServer, ServerInstallation, ServerConfiguration, InstallationMethod


class TestTemplateManagerInit:
    """Tests for TemplateManager initialization."""
    
    def test_template_manager_init_default(self):
        """Test TemplateManager initialization with default path."""
        with patch('pathlib.Path') as mock_path:
            manager = TemplateManager()
            
            # Check that default path calculation was attempted
            mock_path.assert_called()
    
    def test_template_manager_init_custom_path(self, tmp_path):
        """Test TemplateManager initialization with custom path."""
        custom_path = tmp_path / "custom_templates"
        manager = TemplateManager(templates_dir=custom_path)
        
        assert manager.templates_dir == custom_path


class TestGetTemplate:
    """Tests for getting templates."""
    
    def test_get_template_exists(self, tmp_path):
        """Test getting existing template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        template_data = {
            "description": "Test template",
            "env": {"TEST_VAR": "test_value"}
        }
        
        template_path = templates_dir / "test_template.json"
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.get_template("test_template")
        
        assert result == template_data
    
    def test_get_template_not_exists(self, tmp_path):
        """Test getting non-existent template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.get_template("nonexistent")
        
        assert result is None
    
    def test_get_template_invalid_json(self, tmp_path):
        """Test getting template with invalid JSON."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        template_path = templates_dir / "invalid.json"
        with open(template_path, 'w') as f:
            f.write("invalid json")
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.get_template("invalid")
        
        assert result is None
    
    def test_get_template_io_error(self, tmp_path):
        """Test getting template with IO error."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        manager = TemplateManager(templates_dir=templates_dir)
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = manager.get_template("test_template")
        
        assert result is None


class TestCreateServerConfig:
    """Tests for creating server configurations."""
    
    def create_mock_server(self, method=InstallationMethod.NPM, package="test-package", 
                          template=None, required_params=None, optional_params=None):
        """Create a mock MCP server for testing."""
        server = Mock(spec=MCPServer)
        
        # Mock installation
        installation = Mock(spec=ServerInstallation)
        installation.method = method
        installation.package = package
        server.installation = installation
        
        # Mock configuration
        configuration = Mock(spec=ServerConfiguration)
        configuration.template = template
        configuration.required_params = required_params or []
        configuration.optional_params = optional_params or []
        server.configuration = configuration
        
        return server
    
    def test_create_server_config_npm_basic(self):
        """Test creating configuration for NPM server."""
        server = self.create_mock_server(InstallationMethod.NPM, "test-npm-package")
        
        manager = TemplateManager()
        config = manager.create_server_config(server)
        
        expected = {
            "command": "npx",
            "args": ["test-npm-package"]
        }
        
        assert config == expected
    
    def test_create_server_config_pip_basic(self):
        """Test creating configuration for PIP server."""
        server = self.create_mock_server(InstallationMethod.PIP, "test_pip_package")
        
        manager = TemplateManager()
        config = manager.create_server_config(server)
        
        expected = {
            "command": "python3",
            "args": ["-m", "test_pip_package"]
        }
        
        assert config == expected
    
    def test_create_server_config_git_basic(self):
        """Test creating configuration for Git server."""
        server = self.create_mock_server(InstallationMethod.GIT, "https://github.com/user/repo.git")
        
        manager = TemplateManager()
        config = manager.create_server_config(server)
        
        expected = {
            "command": "python3",
            "args": ["main.py"]
        }
        
        assert config == expected
    
    def test_create_server_config_binary_method(self):
        """Test creating configuration for binary installation."""
        server = self.create_mock_server("binary", "/path/to/binary")
        
        manager = TemplateManager()
        config = manager.create_server_config(server)
        
        expected = {
            "command": "/path/to/binary",
            "args": []
        }
        
        assert config == expected
    
    def test_create_server_config_with_template(self, tmp_path):
        """Test creating configuration with server template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        template_data = {
            "custom_field": "custom_value",
            "env": {"TEMPLATE_VAR": "template_value"}
        }
        
        template_path = templates_dir / "server_template.json"
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        server = self.create_mock_server(template="server_template.json")
        
        manager = TemplateManager(templates_dir=templates_dir)
        config = manager.create_server_config(server)
        
        assert config["custom_field"] == "custom_value"
        assert config["env"]["TEMPLATE_VAR"] == "template_value"
    
    def test_create_server_config_with_user_params(self):
        """Test creating configuration with user parameters."""
        server = self.create_mock_server(
            required_params=["database_url", "api_key"],
            optional_params=["timeout", "debug"]
        )
        
        user_params = {
            "database_url": "postgresql://localhost:5432/test",
            "api_key": "secret_key",
            "timeout": "60",
            "env": {"CUSTOM_VAR": "custom_value"}
        }
        
        manager = TemplateManager()
        config = manager.create_server_config(server, user_params)
        
        assert "postgresql://localhost:5432/test" in config["args"]
        assert "secret_key" in config["args"]
        assert "--timeout" in config["args"]
        assert "60" in config["args"]
        assert config["env"]["CUSTOM_VAR"] == "custom_value"
    
    def test_create_server_config_missing_required_params(self):
        """Test creating configuration with missing required parameters."""
        server = self.create_mock_server(required_params=["database_url"])
        
        manager = TemplateManager()
        config = manager.create_server_config(server)
        
        # Should include default value for database_url
        assert "./database.db" in config["args"]
    
    def test_create_server_config_no_user_params(self):
        """Test creating configuration with None user parameters."""
        server = self.create_mock_server()
        
        manager = TemplateManager()
        config = manager.create_server_config(server, None)
        
        assert config is not None
        assert "command" in config
        assert "args" in config


class TestGetCommandForServer:
    """Tests for getting commands for servers."""
    
    def test_get_command_npm(self):
        """Test getting command for NPM server."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.NPM
        
        manager = TemplateManager()
        command = manager._get_command_for_server(server)
        
        assert command == "npx"
    
    def test_get_command_pip(self):
        """Test getting command for PIP server."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.PIP
        
        manager = TemplateManager()
        command = manager._get_command_for_server(server)
        
        assert command == "python3"
    
    def test_get_command_git(self):
        """Test getting command for Git server."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.GIT
        
        manager = TemplateManager()
        command = manager._get_command_for_server(server)
        
        assert command == "python3"
    
    def test_get_command_other(self):
        """Test getting command for other installation method."""
        server = Mock(spec=MCPServer)
        server.installation.method = "custom"
        server.installation.package = "custom_command"
        
        manager = TemplateManager()
        command = manager._get_command_for_server(server)
        
        assert command == "custom_command"


class TestGetArgsForServer:
    """Tests for getting arguments for servers."""
    
    def test_get_args_npm(self):
        """Test getting args for NPM server."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.NPM
        server.installation.package = "test-package"
        server.configuration.required_params = []
        server.configuration.optional_params = []
        
        manager = TemplateManager()
        args = manager._get_args_for_server(server, {})
        
        assert args == ["test-package"]
    
    def test_get_args_pip(self):
        """Test getting args for PIP server."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.PIP
        server.installation.package = "test_package"
        server.configuration.required_params = []
        server.configuration.optional_params = []
        
        manager = TemplateManager()
        args = manager._get_args_for_server(server, {})
        
        assert args == ["-m", "test_package"]
    
    def test_get_args_git(self):
        """Test getting args for Git server."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.GIT
        server.configuration.required_params = []
        server.configuration.optional_params = []
        
        manager = TemplateManager()
        args = manager._get_args_for_server(server, {})
        
        assert args == ["main.py"]
    
    def test_get_args_with_required_params_provided(self):
        """Test getting args with required parameters provided."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.NPM
        server.installation.package = "test-package"
        server.configuration.required_params = ["database_url", "api_key"]
        server.configuration.optional_params = []
        
        user_params = {
            "database_url": "postgresql://localhost/test",
            "api_key": "secret123"
        }
        
        manager = TemplateManager()
        args = manager._get_args_for_server(server, user_params)
        
        assert args == ["test-package", "postgresql://localhost/test", "secret123"]
    
    def test_get_args_with_required_params_missing(self):
        """Test getting args with missing required parameters."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.NPM
        server.installation.package = "test-package"
        server.configuration.required_params = ["database_path", "unknown_param"]
        server.configuration.optional_params = []
        
        manager = TemplateManager()
        args = manager._get_args_for_server(server, {})
        
        assert args == ["test-package", "./database.db"]  # Default for database_path, nothing for unknown
    
    def test_get_args_with_optional_params(self):
        """Test getting args with optional parameters."""
        server = Mock(spec=MCPServer)
        server.installation.method = InstallationMethod.NPM
        server.installation.package = "test-package"
        server.configuration.required_params = []
        server.configuration.optional_params = ["timeout", "debug"]
        
        user_params = {
            "timeout": "60",
            "debug": "true"
        }
        
        manager = TemplateManager()
        args = manager._get_args_for_server(server, user_params)
        
        assert args == ["test-package", "--timeout", "60", "--debug", "true"]


class TestGetDefaultValue:
    """Tests for getting default parameter values."""
    
    def test_get_default_value_known_params(self):
        """Test getting default values for known parameters."""
        manager = TemplateManager()
        
        test_cases = [
            ("root_path", str(Path.home())),
            ("database_path", "./database.db"),
            ("repository_path", "."),
            ("host", "localhost"),
            ("port", "5432"),
            ("timeout", "30")
        ]
        
        for param, expected in test_cases:
            result = manager._get_default_value(param)
            assert result == expected
    
    def test_get_default_value_unknown_param(self):
        """Test getting default value for unknown parameter."""
        manager = TemplateManager()
        result = manager._get_default_value("unknown_parameter")
        
        assert result is None


class TestListTemplates:
    """Tests for listing templates."""
    
    def test_list_templates_success(self, tmp_path):
        """Test listing templates successfully."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Create test template files
        (templates_dir / "template1.json").write_text("{}")
        (templates_dir / "template2.json").write_text("{}")
        (templates_dir / "template3.json").write_text("{}")
        
        manager = TemplateManager(templates_dir=templates_dir)
        templates = manager.list_templates()
        
        assert len(templates) == 3
        assert "template1" in templates
        assert "template2" in templates
        assert "template3" in templates
        assert templates == sorted(templates)  # Should be sorted
    
    def test_list_templates_empty_directory(self, tmp_path):
        """Test listing templates from empty directory."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        manager = TemplateManager(templates_dir=templates_dir)
        templates = manager.list_templates()
        
        assert templates == []
    
    def test_list_templates_directory_not_exists(self, tmp_path):
        """Test listing templates when directory doesn't exist."""
        templates_dir = tmp_path / "nonexistent"
        
        manager = TemplateManager(templates_dir=templates_dir)
        templates = manager.list_templates()
        
        assert templates == []
    
    def test_list_templates_filters_non_json(self, tmp_path):
        """Test listing templates filters non-JSON files."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        (templates_dir / "template.json").write_text("{}")
        (templates_dir / "not_template.txt").write_text("text")
        (templates_dir / "another.py").write_text("code")
        
        manager = TemplateManager(templates_dir=templates_dir)
        templates = manager.list_templates()
        
        assert templates == ["template"]


class TestCreateTemplate:
    """Tests for creating templates."""
    
    def test_create_template_success(self, tmp_path):
        """Test successful template creation."""
        templates_dir = tmp_path / "templates"
        
        template_data = {
            "description": "Test template",
            "env": {"TEST_VAR": "test_value"}
        }
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.create_template("test_template", template_data)
        
        assert result is True
        
        # Verify template was created
        template_path = templates_dir / "test_template.json"
        assert template_path.exists()
        
        with open(template_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == template_data
    
    def test_create_template_creates_directory(self, tmp_path):
        """Test template creation creates directory if needed."""
        templates_dir = tmp_path / "nonexistent" / "templates"
        
        template_data = {"test": "data"}
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.create_template("test_template", template_data)
        
        assert result is True
        assert templates_dir.exists()
    
    def test_create_template_exception(self, tmp_path):
        """Test template creation with exception."""
        templates_dir = tmp_path / "templates"
        
        manager = TemplateManager(templates_dir=templates_dir)
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = manager.create_template("test_template", {})
        
        assert result is False


class TestDeleteTemplate:
    """Tests for deleting templates."""
    
    def test_delete_template_success(self, tmp_path):
        """Test successful template deletion."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        template_path = templates_dir / "test_template.json"
        template_path.write_text("{}")
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.delete_template("test_template")
        
        assert result is True
        assert not template_path.exists()
    
    def test_delete_template_not_exists(self, tmp_path):
        """Test deleting non-existent template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.delete_template("nonexistent")
        
        assert result is False
    
    def test_delete_template_exception(self, tmp_path):
        """Test template deletion with exception."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        template_path = templates_dir / "test_template.json"
        template_path.write_text("{}")
        
        manager = TemplateManager(templates_dir=templates_dir)
        
        with patch.object(Path, 'unlink', side_effect=OSError("Permission denied")):
            result = manager.delete_template("test_template")
        
        assert result is False


class TestValidateTemplate:
    """Tests for template validation."""
    
    def test_validate_template_valid(self):
        """Test validating valid template."""
        template_data = {
            "command": "python3",
            "args": ["-m", "test_package"],
            "env": {"TEST_VAR": "test_value"}
        }
        
        manager = TemplateManager()
        errors = manager.validate_template(template_data)
        
        assert errors == []
    
    def test_validate_template_missing_command(self):
        """Test validating template missing command."""
        template_data = {
            "args": ["-m", "test_package"]
        }
        
        manager = TemplateManager()
        errors = manager.validate_template(template_data)
        
        assert len(errors) == 1
        assert "command" in errors[0]
    
    def test_validate_template_missing_args(self):
        """Test validating template missing args."""
        template_data = {
            "command": "python3"
        }
        
        manager = TemplateManager()
        errors = manager.validate_template(template_data)
        
        assert len(errors) == 1
        assert "args" in errors[0]
    
    def test_validate_template_invalid_args_type(self):
        """Test validating template with invalid args type."""
        template_data = {
            "command": "python3",
            "args": "not_a_list"
        }
        
        manager = TemplateManager()
        errors = manager.validate_template(template_data)
        
        assert len(errors) == 1
        assert "args" in errors[0] and "list" in errors[0]
    
    def test_validate_template_invalid_env_type(self):
        """Test validating template with invalid env type."""
        template_data = {
            "command": "python3",
            "args": [],
            "env": "not_a_dict"
        }
        
        manager = TemplateManager()
        errors = manager.validate_template(template_data)
        
        assert len(errors) == 1
        assert "env" in errors[0] and "dictionary" in errors[0]
    
    def test_validate_template_multiple_errors(self):
        """Test validating template with multiple errors."""
        template_data = {
            "args": "not_a_list",
            "env": "not_a_dict"
        }
        
        manager = TemplateManager()
        errors = manager.validate_template(template_data)
        
        assert len(errors) == 3  # Missing command, invalid args, invalid env


class TestGenerateDefaultTemplates:
    """Tests for generating default templates."""
    
    def test_generate_default_templates_success(self, tmp_path):
        """Test successful default template generation."""
        templates_dir = tmp_path / "templates"
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.generate_default_templates()
        
        assert result is True
        assert templates_dir.exists()
        
        # Check that templates were created
        templates = manager.list_templates()
        assert len(templates) > 0
        assert "filesystem_template" in templates
        assert "sqlite_template" in templates
        assert "postgres_template" in templates
        assert "github_template" in templates
    
    def test_generate_default_templates_content(self, tmp_path):
        """Test default template content is correct."""
        templates_dir = tmp_path / "templates"
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.generate_default_templates()
        
        assert result is True
        
        # Check specific template content
        filesystem_template = manager.get_template("filesystem_template")
        assert filesystem_template is not None
        assert "description" in filesystem_template
        assert "env" in filesystem_template
        assert "FILESYSTEM_ROOT" in filesystem_template["env"]
        
        postgres_template = manager.get_template("postgres_template")
        assert postgres_template is not None
        assert "POSTGRES_CONNECTION" in postgres_template["env"]
    
    def test_generate_default_templates_exception(self, tmp_path):
        """Test default template generation with exception."""
        templates_dir = tmp_path / "templates"
        
        manager = TemplateManager(templates_dir=templates_dir)
        
        # Mock create_template to fail
        manager.create_template = Mock(return_value=False)
        
        result = manager.generate_default_templates()
        
        assert result is False
    
    def test_generate_default_templates_creates_directory(self, tmp_path):
        """Test default template generation creates directory."""
        templates_dir = tmp_path / "nonexistent" / "templates"
        
        manager = TemplateManager(templates_dir=templates_dir)
        result = manager.generate_default_templates()
        
        assert result is True
        assert templates_dir.exists()
    
    def test_generate_default_templates_exception_during_generation(self, tmp_path):
        """Test exception during default template generation."""
        templates_dir = tmp_path / "templates"
        
        manager = TemplateManager(templates_dir=templates_dir)
        
        with patch.object(manager.templates_dir, 'mkdir', side_effect=OSError("Permission denied")):
            result = manager.generate_default_templates()
        
        assert result is False