"""Tests for Claude Code installer module."""

import json
import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.installer.base import InstallationResult
from mcpi.registry.catalog import MCPServer, ServerInstallation, ServerVersions, ServerConfiguration, InstallationMethod


class TestClaudeCodeInstaller:
    """Test suite for ClaudeCodeInstaller class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "mcp_servers.json"
        self.installer = ClaudeCodeInstaller(config_path=self.config_path)
        self.dry_run_installer = ClaudeCodeInstaller(config_path=self.config_path, dry_run=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_mock_server(self, server_id="test_server", method=InstallationMethod.NPM, package="test-package"):
        """Create mock MCP server for testing."""
        installation = ServerInstallation(method=method, package=package)
        versions = ServerVersions(latest="1.0.0")
        configuration = ServerConfiguration()
        
        return MCPServer(
            id=server_id,
            name="Test Server",
            description="Test server description",
            author="Test Author",
            license="MIT",
            versions=versions,
            installation=installation,
            configuration=configuration
        )

    def test_init_default(self):
        """Test default initialization."""
        with patch.object(ClaudeCodeInstaller, '_find_claude_code_config') as mock_find:
            mock_find.return_value = Path("/mock/config.json")
            installer = ClaudeCodeInstaller()
            assert installer.config_path == Path("/mock/config.json")
            assert installer.dry_run is False
            assert installer.npm_installer is not None
            assert installer.python_installer is not None
            assert installer.git_installer is not None
    
    def test_init_with_config_path(self):
        """Test initialization with custom config path."""
        config_path = Path("/custom/config.json")
        installer = ClaudeCodeInstaller(config_path=config_path)
        assert installer.config_path == config_path

    def test_init_dry_run(self):
        """Test initialization with dry run mode."""
        installer = ClaudeCodeInstaller(config_path=self.config_path, dry_run=True)
        assert installer.dry_run is True
        assert installer.npm_installer.dry_run is True
        assert installer.python_installer.dry_run is True
        assert installer.git_installer.dry_run is True

    @patch('platform.system')
    def test_find_claude_code_config_macos(self, mock_system):
        """Test finding Claude Code config on macOS."""
        mock_system.return_value = "Darwin"
        installer = ClaudeCodeInstaller()
        expected_path = Path.home() / ".claude" / "mcp_servers.json"
        assert installer._find_claude_code_config() == expected_path

    @patch('platform.system')
    def test_find_claude_code_config_linux(self, mock_system):
        """Test finding Claude Code config on Linux."""
        mock_system.return_value = "Linux"
        installer = ClaudeCodeInstaller()
        expected_path = Path.home() / ".config" / "claude" / "mcp_servers.json"
        assert installer._find_claude_code_config() == expected_path

    @patch('platform.system')
    @patch.dict(os.environ, {'APPDATA': '/test/appdata'})
    def test_find_claude_code_config_windows(self, mock_system):
        """Test finding Claude Code config on Windows."""
        mock_system.return_value = "Windows"
        installer = ClaudeCodeInstaller()
        expected_path = Path("/test/appdata/claude/mcp_servers.json")
        assert installer._find_claude_code_config() == expected_path

    @patch('platform.system')
    def test_find_claude_code_config_unknown_os(self, mock_system):
        """Test finding Claude Code config on unknown OS."""
        mock_system.return_value = "Unknown"
        installer = ClaudeCodeInstaller()
        expected_path = Path.home() / ".claude" / "mcp_servers.json"
        assert installer._find_claude_code_config() == expected_path

    def test_load_config_nonexistent_file(self):
        """Test loading config when file doesn't exist."""
        config = self.installer._load_config()
        assert config == {"mcpServers": {}}

    def test_load_config_valid_file(self):
        """Test loading valid config file."""
        config_data = {"mcpServers": {"test": {"command": "test", "args": []}}}
        self.config_path.write_text(json.dumps(config_data))
        
        config = self.installer._load_config()
        assert config == config_data

    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        self.config_path.write_text("invalid json")
        
        config = self.installer._load_config()
        assert config == {"mcpServers": {}}

    def test_load_config_io_error(self):
        """Test loading config with IO error."""
        # Create a directory with same name to cause IO error
        self.config_path.mkdir()
        
        config = self.installer._load_config()
        assert config == {"mcpServers": {}}

    def test_save_config_success(self):
        """Test successful config save."""
        config = {"mcpServers": {"test": {"command": "test", "args": []}}}
        
        result = self.installer._save_config(config)
        
        assert result is True
        assert self.config_path.exists()
        saved_config = json.loads(self.config_path.read_text())
        assert saved_config == config

    def test_save_config_dry_run(self):
        """Test config save in dry run mode."""
        config = {"mcpServers": {"test": {"command": "test", "args": []}}}
        
        result = self.dry_run_installer._save_config(config)
        
        assert result is True
        assert not self.config_path.exists()

    def test_save_config_io_error(self):
        """Test config save with IO error."""
        config = {"mcpServers": {"test": {"command": "test", "args": []}}}
        
        # Make directory read-only to cause IO error
        self.temp_dir.chmod(0o444)
        
        result = self.installer._save_config(config)
        
        assert result is False
        
        # Restore permissions for cleanup
        self.temp_dir.chmod(0o755)

    @patch.object(ClaudeCodeInstaller, 'validate_installation')
    @patch.object(ClaudeCodeInstaller, 'is_installed')
    @patch.object(ClaudeCodeInstaller, '_install_package')
    @patch.object(ClaudeCodeInstaller, 'create_backup')
    @patch.object(ClaudeCodeInstaller, '_load_config')
    @patch.object(ClaudeCodeInstaller, '_generate_server_config')
    @patch.object(ClaudeCodeInstaller, '_save_config')
    def test_install_success(self, mock_save_config, mock_generate_config, mock_load_config,
                           mock_create_backup, mock_install_package, mock_is_installed, 
                           mock_validate):
        """Test successful server installation."""
        server = self.create_mock_server()
        config_params = {"param1": "value1"}
        
        # Setup mocks
        mock_validate.return_value = []
        mock_is_installed.return_value = False
        package_result = InstallationResult(
            status="success", 
            message="Package installed", 
            server_id="test_server",
            details={"install_path": "/path/to/package"}
        )
        mock_install_package.return_value = package_result
        mock_create_backup.return_value = Path("/backup/path")
        mock_load_config.return_value = {"mcpServers": {}}
        mock_generate_config.return_value = {"command": "test", "args": []}
        mock_save_config.return_value = True
        
        result = self.installer.install(server, config_params)
        
        assert result.success is True
        assert "Successfully installed Test Server for Claude Code" in result.message
        assert result.config_path == self.config_path
        assert result.details["backup_path"] == Path("/backup/path")

    def test_install_validation_failure(self):
        """Test installation with validation failure."""
        server = self.create_mock_server()
        
        with patch.object(self.installer, 'validate_installation') as mock_validate:
            mock_validate.return_value = ["Validation error 1", "Validation error 2"]
            
            result = self.installer.install(server)
            
            assert result.success is False
            assert "Validation failed" in result.message
            assert "validation_errors" in result.details

    def test_install_already_installed(self):
        """Test installation when server already installed."""
        server = self.create_mock_server()
        
        with patch.object(self.installer, 'validate_installation') as mock_validate:
            with patch.object(self.installer, 'is_installed') as mock_is_installed:
                mock_validate.return_value = []
                mock_is_installed.return_value = True
                
                result = self.installer.install(server)
                
                assert result.success is False
                assert "is already installed" in result.message
                assert result.details.get("already_installed") is True

    @patch.object(ClaudeCodeInstaller, 'validate_installation')
    @patch.object(ClaudeCodeInstaller, 'is_installed')
    @patch.object(ClaudeCodeInstaller, '_install_package')
    def test_install_package_failure(self, mock_install_package, mock_is_installed, mock_validate):
        """Test installation when package installation fails."""
        server = self.create_mock_server()
        
        mock_validate.return_value = []
        mock_is_installed.return_value = False
        mock_install_package.return_value = InstallationResult(
            status="failed", 
            message="Package installation failed", 
            server_id="test_server"
        )
        
        result = self.installer.install(server)
        
        assert result.success is False
        assert "Package installation failed" in result.message

    @patch.object(ClaudeCodeInstaller, 'validate_installation')
    @patch.object(ClaudeCodeInstaller, 'is_installed')
    @patch.object(ClaudeCodeInstaller, '_install_package')
    @patch.object(ClaudeCodeInstaller, 'create_backup')
    @patch.object(ClaudeCodeInstaller, '_load_config')
    @patch.object(ClaudeCodeInstaller, '_generate_server_config')
    @patch.object(ClaudeCodeInstaller, '_save_config')
    def test_install_save_failure(self, mock_save_config, mock_generate_config, mock_load_config,
                                mock_create_backup, mock_install_package, mock_is_installed,
                                mock_validate):
        """Test installation when config save fails."""
        server = self.create_mock_server()
        
        # Setup mocks
        mock_validate.return_value = []
        mock_is_installed.return_value = False
        mock_install_package.return_value = InstallationResult(
            status="success", message="Package installed", server_id="test_server"
        )
        mock_create_backup.return_value = Path("/backup/path")
        mock_load_config.return_value = {"mcpServers": {}}
        mock_generate_config.return_value = {"command": "test", "args": []}
        mock_save_config.return_value = False
        
        result = self.installer.install(server)
        
        assert result.success is False
        assert "Failed to save Claude Code configuration" in result.message

    def test_install_package_npm(self):
        """Test package installation with NPM method."""
        server = self.create_mock_server(method=InstallationMethod.NPM)
        
        with patch.object(self.installer.npm_installer, 'install') as mock_install:
            mock_install.return_value = InstallationResult(
                status="success", message="NPM installed", server_id="test_server"
            )
            
            result = self.installer._install_package(server)
            
            assert result.success is True
            mock_install.assert_called_once_with(server)

    def test_install_package_pip(self):
        """Test package installation with PIP method."""
        server = self.create_mock_server(method=InstallationMethod.PIP)
        
        with patch.object(self.installer.python_installer, 'install') as mock_install:
            mock_install.return_value = InstallationResult(
                status="success", message="PIP installed", server_id="test_server"
            )
            
            result = self.installer._install_package(server)
            
            assert result.success is True
            mock_install.assert_called_once_with(server)

    def test_install_package_git(self):
        """Test package installation with GIT method."""
        server = self.create_mock_server(method=InstallationMethod.GIT)
        
        with patch.object(self.installer.git_installer, 'install') as mock_install:
            mock_install.return_value = InstallationResult(
                status="success", message="GIT installed", server_id="test_server"
            )
            
            result = self.installer._install_package(server)
            
            assert result.success is True
            mock_install.assert_called_once_with(server)

    def test_install_package_unsupported_method(self):
        """Test package installation with unsupported method."""
        server = self.create_mock_server(method=InstallationMethod.BINARY)
        
        result = self.installer._install_package(server)
        
        assert result.success is False
        assert "Unsupported installation method" in result.message

    def test_generate_server_config_npm(self):
        """Test server config generation for NPM."""
        server = self.create_mock_server(method=InstallationMethod.NPM, package="test-npm-package")
        config_params = {}
        package_details = {}
        
        config = self.installer._generate_server_config(server, config_params, package_details)
        
        assert config["command"] == "npx"
        assert config["args"] == ["test-npm-package"]

    def test_generate_server_config_pip(self):
        """Test server config generation for PIP."""
        server = self.create_mock_server(method=InstallationMethod.PIP, package="test-pip-package")
        config_params = {}
        package_details = {"python_path": "/usr/bin/python3", "module_path": "test.module"}
        
        config = self.installer._generate_server_config(server, config_params, package_details)
        
        assert config["command"] == "/usr/bin/python3"
        assert config["args"] == ["-m", "test.module"]

    def test_generate_server_config_pip_defaults(self):
        """Test server config generation for PIP with defaults."""
        server = self.create_mock_server(method=InstallationMethod.PIP, package="test-pip-package")
        config_params = {}
        package_details = {}
        
        config = self.installer._generate_server_config(server, config_params, package_details)
        
        assert config["command"] == "python3"
        assert config["args"] == ["-m", "test-pip-package"]

    def test_generate_server_config_git_with_script(self):
        """Test server config generation for GIT with script path."""
        server = self.create_mock_server(method=InstallationMethod.GIT)
        config_params = {}
        package_details = {"script_path": "/path/to/script.py", "install_path": "/path/to/repo"}
        
        config = self.installer._generate_server_config(server, config_params, package_details)
        
        assert config["command"] == "/path/to/script.py"
        assert config["args"] == []

    def test_generate_server_config_git_without_script(self):
        """Test server config generation for GIT without script path."""
        server = self.create_mock_server(method=InstallationMethod.GIT)
        config_params = {}
        package_details = {"install_path": "/path/to/repo"}
        
        config = self.installer._generate_server_config(server, config_params, package_details)
        
        assert config["command"] == "python3"
        assert config["args"] == ["/path/to/repo"]

    def test_generate_server_config_with_required_params(self):
        """Test server config generation with required parameters."""
        configuration = ServerConfiguration(
            required_params=["root_path", "database_path"],
            optional_params=[]
        )
        installation = ServerInstallation(method=InstallationMethod.NPM, package="test-package")
        versions = ServerVersions(latest="1.0.0")
        server = MCPServer(
            id="test_server",
            name="Test Server",
            description="Test description",
            author="Test Author",
            license="MIT",
            versions=versions,
            installation=installation,
            configuration=configuration
        )
        
        config_params = {"root_path": "/custom/path", "database_path": "/custom/db.sqlite"}
        
        config = self.installer._generate_server_config(server, config_params, {})
        
        assert config["args"] == ["test-package", "/custom/path", "/custom/db.sqlite"]

    def test_generate_server_config_with_missing_required_params(self):
        """Test server config generation with missing required parameters (uses defaults)."""
        configuration = ServerConfiguration(
            required_params=["root_path", "database_path"],
            optional_params=[]
        )
        installation = ServerInstallation(method=InstallationMethod.NPM, package="test-package")
        versions = ServerVersions(latest="1.0.0")
        server = MCPServer(
            id="test_server",
            name="Test Server", 
            description="Test description",
            author="Test Author",
            license="MIT",
            versions=versions,
            installation=installation,
            configuration=configuration
        )
        
        config_params = {}
        
        config = self.installer._generate_server_config(server, config_params, {})
        
        # Should use default values
        expected_args = ["test-package", str(Path.home()), "./database.db"]
        assert config["args"] == expected_args

    def test_generate_server_config_with_optional_params(self):
        """Test server config generation with optional parameters."""
        configuration = ServerConfiguration(
            required_params=[],
            optional_params=["verbose", "port"]
        )
        installation = ServerInstallation(method=InstallationMethod.NPM, package="test-package")
        versions = ServerVersions(latest="1.0.0")
        server = MCPServer(
            id="test_server",
            name="Test Server",
            description="Test description", 
            author="Test Author",
            license="MIT",
            versions=versions,
            installation=installation,
            configuration=configuration
        )
        
        config_params = {"verbose": "true", "port": "8080"}
        
        config = self.installer._generate_server_config(server, config_params, {})
        
        assert "--verbose" in config["args"]
        assert "true" in config["args"]
        assert "--port" in config["args"]
        assert "8080" in config["args"]

    def test_generate_server_config_with_env_vars(self):
        """Test server config generation with environment variables."""
        server = self.create_mock_server()
        config_params = {"env": {"API_KEY": "secret123", "DEBUG": "true"}}
        
        config = self.installer._generate_server_config(server, config_params, {})
        
        assert config["env"] == {"API_KEY": "secret123", "DEBUG": "true"}

    def test_get_default_param_value(self):
        """Test getting default parameter values."""
        assert self.installer._get_default_param_value("root_path") == str(Path.home())
        assert self.installer._get_default_param_value("database_path") == "./database.db"
        assert self.installer._get_default_param_value("repository_path") == "."
        assert self.installer._get_default_param_value("unknown_param") is None

    def test_uninstall_success(self):
        """Test successful server uninstallation."""
        # Setup initial config
        config = {"mcpServers": {"test_server": {"command": "test", "args": []}}}
        self.config_path.write_text(json.dumps(config))
        
        with patch.object(self.installer, 'create_backup') as mock_backup:
            mock_backup.return_value = Path("/backup/path")
            
            result = self.installer.uninstall("test_server")
            
            assert result.success is True
            assert "Successfully uninstalled test_server from Claude Code" in result.message
            
            # Verify server was removed from config
            updated_config = json.loads(self.config_path.read_text())
            assert "test_server" not in updated_config["mcpServers"]

    def test_uninstall_not_installed(self):
        """Test uninstallation of non-installed server."""
        result = self.installer.uninstall("nonexistent_server")
        
        assert result.success is False
        assert "is not installed" in result.message

    def test_uninstall_save_failure(self):
        """Test uninstallation when config save fails."""
        # Setup initial config
        config = {"mcpServers": {"test_server": {"command": "test", "args": []}}}
        self.config_path.write_text(json.dumps(config))
        
        with patch.object(self.installer, 'create_backup') as mock_backup:
            with patch.object(self.installer, '_save_config') as mock_save:
                mock_backup.return_value = Path("/backup/path")
                mock_save.return_value = False
                
                result = self.installer.uninstall("test_server")
                
                assert result.success is False
                assert "Failed to save Claude Code configuration" in result.message

    def test_is_installed_true(self):
        """Test is_installed when server is installed."""
        config = {"mcpServers": {"test_server": {"command": "test", "args": []}}}
        self.config_path.write_text(json.dumps(config))
        
        assert self.installer.is_installed("test_server") is True

    def test_is_installed_false(self):
        """Test is_installed when server is not installed."""
        config = {"mcpServers": {}}
        self.config_path.write_text(json.dumps(config))
        
        assert self.installer.is_installed("test_server") is False

    def test_is_installed_no_config(self):
        """Test is_installed when config file doesn't exist."""
        assert self.installer.is_installed("test_server") is False

    def test_get_installed_servers(self):
        """Test getting list of installed servers."""
        config = {
            "mcpServers": {
                "server1": {"command": "test1", "args": []},
                "server2": {"command": "test2", "args": []}
            }
        }
        self.config_path.write_text(json.dumps(config))
        
        servers = self.installer.get_installed_servers()
        
        assert set(servers) == {"server1", "server2"}

    def test_get_installed_servers_empty(self):
        """Test getting installed servers when none exist."""
        servers = self.installer.get_installed_servers()
        
        assert servers == []

    def test_get_server_config(self):
        """Test getting server configuration."""
        config = {
            "mcpServers": {
                "test_server": {"command": "test", "args": ["--verbose"]}
            }
        }
        self.config_path.write_text(json.dumps(config))
        
        server_config = self.installer.get_server_config("test_server")
        
        assert server_config == {"command": "test", "args": ["--verbose"]}

    def test_get_server_config_not_found(self):
        """Test getting server configuration for non-existent server."""
        server_config = self.installer.get_server_config("nonexistent")
        
        assert server_config is None

    def test_update_server_config_success(self):
        """Test successful server configuration update."""
        config = {"mcpServers": {"test_server": {"command": "old", "args": []}}}
        self.config_path.write_text(json.dumps(config))
        
        new_config = {"command": "new", "args": ["--verbose"]}
        result = self.installer.update_server_config("test_server", new_config)
        
        assert result is True
        
        # Verify config was updated
        updated_config = json.loads(self.config_path.read_text())
        assert updated_config["mcpServers"]["test_server"] == new_config

    def test_update_server_config_not_installed(self):
        """Test updating configuration for non-installed server."""
        new_config = {"command": "test", "args": []}
        result = self.installer.update_server_config("nonexistent", new_config)
        
        assert result is False

    def test_update_server_config_save_failure(self):
        """Test updating configuration when save fails."""
        config = {"mcpServers": {"test_server": {"command": "old", "args": []}}}
        self.config_path.write_text(json.dumps(config))
        
        with patch.object(self.installer, '_save_config') as mock_save:
            mock_save.return_value = False
            
            new_config = {"command": "new", "args": []}
            result = self.installer.update_server_config("test_server", new_config)
            
            assert result is False

    def test_validate_config_no_file(self):
        """Test config validation when file doesn't exist."""
        errors = self.installer.validate_config()
        
        assert len(errors) == 1
        assert "Configuration file does not exist" in errors[0]

    def test_validate_config_missing_mcp_servers(self):
        """Test config validation when mcpServers section is missing."""
        config = {"otherSection": {}}
        self.config_path.write_text(json.dumps(config))
        
        errors = self.installer.validate_config()
        
        assert len(errors) == 1
        assert "Configuration missing 'mcpServers' section" in errors[0]

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = {
            "mcpServers": {
                "server1": {"command": "test1", "args": []},
                "server2": {"command": "test2", "args": ["--verbose"]}
            }
        }
        self.config_path.write_text(json.dumps(config))
        
        errors = self.installer.validate_config()
        
        assert errors == []

    def test_validate_config_invalid_server_config(self):
        """Test validation with invalid server configuration."""
        config = {
            "mcpServers": {
                "server1": "invalid_string_instead_of_object",
                "server2": {"command": "test2"},  # Missing args
                "server3": {"args": []},  # Missing command
                "server4": {"command": "test4", "args": "invalid_string"}  # args not array
            }
        }
        self.config_path.write_text(json.dumps(config))
        
        errors = self.installer.validate_config()
        
        assert len(errors) == 4
        assert any("Configuration must be an object" in error for error in errors)
        assert any("Missing 'args' field" in error for error in errors)
        assert any("Missing 'command' field" in error for error in errors)
        assert any("'args' must be an array" in error for error in errors)

    def test_supports_method_supported(self):
        """Test that installer supports NPM, PIP, and GIT methods."""
        assert self.installer._supports_method(InstallationMethod.NPM) is True
        assert self.installer._supports_method(InstallationMethod.PIP) is True
        assert self.installer._supports_method(InstallationMethod.GIT) is True

    def test_supports_method_unsupported(self):
        """Test that installer doesn't support BINARY method."""
        assert self.installer._supports_method(InstallationMethod.BINARY) is False
        assert self.installer._supports_method("unknown") is False