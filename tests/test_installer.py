"""Tests for the installer module."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, call

from mcpi.installer.base import BaseInstaller, InstallationResult, InstallationStatus
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.installer.npm import NPMInstaller
from mcpi.registry.catalog import MCPServer


class MockInstaller(BaseInstaller):
    """Mock installer for testing base functionality."""
    
    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run=dry_run)
        self.installed_servers = set()
    
    def install(self, server, config_params=None):
        if server.id in self.installed_servers:
            return self._create_failure_result(server.id, "Already installed")
        
        self.installed_servers.add(server.id)
        return self._create_success_result(server.id, "Installed successfully")
    
    def uninstall(self, server_id):
        if server_id not in self.installed_servers:
            return self._create_failure_result(server_id, "Not installed")
        
        self.installed_servers.remove(server_id)
        return self._create_success_result(server_id, "Uninstalled successfully")
    
    def is_installed(self, server_id):
        return server_id in self.installed_servers
    
    def get_installed_servers(self):
        return list(self.installed_servers)
    
    def _supports_method(self, method):
        return True


class TestBaseInstaller:
    """Tests for BaseInstaller class."""
    
    def test_installation_result_properties(self):
        """Test InstallationResult properties."""
        success_result = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Success",
            server_id="test"
        )
        assert success_result.success is True
        assert success_result.failed is False
        
        failure_result = InstallationResult(
            status=InstallationStatus.FAILED,
            message="Failed",
            server_id="test"
        )
        assert failure_result.success is False
        assert failure_result.failed is True
    
    def test_create_success_result(self):
        """Test creating success results."""
        installer = MockInstaller()
        result = installer._create_success_result("test_server", "Test message")
        
        assert result.status == InstallationStatus.SUCCESS
        assert result.message == "Test message"
        assert result.server_id == "test_server"
        assert result.success is True
    
    def test_create_failure_result(self):
        """Test creating failure results."""
        installer = MockInstaller()
        result = installer._create_failure_result("test_server", "Error message")
        
        assert result.status == InstallationStatus.FAILED
        assert result.message == "Error message"
        assert result.server_id == "test_server"
        assert result.failed is True
    
    def test_backup_and_restore(self, tmp_path):
        """Test configuration backup and restore functionality."""
        installer = MockInstaller()
        
        # Create test file
        test_file = tmp_path / "test_config.json"
        test_content = {"test": "data"}
        with open(test_file, 'w') as f:
            json.dump(test_content, f)
        
        # Create backup
        backup_path = installer.create_backup(test_file)
        assert backup_path is not None
        assert backup_path.exists()
        
        # Modify original file
        with open(test_file, 'w') as f:
            json.dump({"modified": "data"}, f)
        
        # Restore from backup
        success = installer.restore_backup(backup_path, test_file)
        assert success is True
        
        # Verify restoration
        with open(test_file, 'r') as f:
            restored_content = json.load(f)
        assert restored_content == test_content
    
    def test_validate_installation(self):
        """Test installation validation."""
        installer = MockInstaller()
        
        # Create test server with system dependency
        server_data = {
            "id": "test_server",
            "name": "Test Server",
            "description": "Test",
            "category": ["test"],
            "author": "Test",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {
                "method": "npm",
                "package": "test-package",
                "system_dependencies": ["nonexistent-dependency"],
                "python_dependencies": []
            },
            "configuration": {},
            "capabilities": [],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        server = MCPServer(**server_data)
        errors = installer.validate_installation(server)
        
        # Should have error for missing system dependency
        assert len(errors) > 0
        assert any("nonexistent-dependency" in error for error in errors)


class TestClaudeCodeInstaller:
    """Tests for ClaudeCodeInstaller class."""
    
    def test_find_claude_code_config_paths(self):
        """Test Claude Code config path detection."""
        with patch('platform.system') as mock_system:
            # Test macOS
            mock_system.return_value = "Darwin"
            installer = ClaudeCodeInstaller()
            expected_path = Path.home() / ".claude" / "mcp_servers.json"
            assert installer.config_path == expected_path
            
            # Test Linux
            mock_system.return_value = "Linux"
            installer = ClaudeCodeInstaller()
            expected_path = Path.home() / ".config" / "claude" / "mcp_servers.json"
            assert installer.config_path == expected_path
    
    def test_load_empty_config(self, tmp_path):
        """Test loading empty or non-existent config."""
        config_path = tmp_path / "mcp_servers.json"
        installer = ClaudeCodeInstaller(config_path=config_path, dry_run=True)
        
        config = installer._load_config()
        assert config == {"mcpServers": {}}
    
    def test_load_existing_config(self, tmp_path):
        """Test loading existing config file."""
        config_path = tmp_path / "mcp_servers.json"
        test_config = {
            "mcpServers": {
                "existing_server": {
                    "command": "npx",
                    "args": ["existing-package"]
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        installer = ClaudeCodeInstaller(config_path=config_path, dry_run=True)
        config = installer._load_config()
        
        assert config == test_config
        assert "existing_server" in config["mcpServers"]
    
    def test_is_installed(self, tmp_path):
        """Test checking if server is installed."""
        config_path = tmp_path / "mcp_servers.json"
        test_config = {
            "mcpServers": {
                "installed_server": {
                    "command": "npx",
                    "args": ["installed-package"]
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        installer = ClaudeCodeInstaller(config_path=config_path, dry_run=True)
        
        assert installer.is_installed("installed_server") is True
        assert installer.is_installed("not_installed") is False
    
    def test_get_installed_servers(self, tmp_path):
        """Test getting list of installed servers."""
        config_path = tmp_path / "mcp_servers.json"
        test_config = {
            "mcpServers": {
                "server1": {"command": "npx", "args": ["package1"]},
                "server2": {"command": "python3", "args": ["-m", "package2"]}
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        installer = ClaudeCodeInstaller(config_path=config_path, dry_run=True)
        installed = installer.get_installed_servers()
        
        assert len(installed) == 2
        assert "server1" in installed
        assert "server2" in installed
    
    def test_validate_config(self, tmp_path):
        """Test configuration validation."""
        config_path = tmp_path / "mcp_servers.json"
        
        # Test valid config
        valid_config = {
            "mcpServers": {
                "valid_server": {
                    "command": "npx",
                    "args": ["valid-package"]
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(valid_config, f)
        
        installer = ClaudeCodeInstaller(config_path=config_path, dry_run=True)
        errors = installer.validate_config()
        assert len(errors) == 0
        
        # Test invalid config
        invalid_config = {
            "mcpServers": {
                "invalid_server": {
                    "command": "npx"
                    # Missing 'args' field
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        errors = installer.validate_config()
        assert len(errors) > 0
        assert any("Missing 'args' field" in error for error in errors)


class TestNPMInstaller:
    """Tests for NPMInstaller class."""
    
    @patch('mcpi.installer.npm.subprocess.run')
    def test_check_npm_available(self, mock_run):
        """Test npm availability check."""
        installer = NPMInstaller(dry_run=True)
        
        # Test npm available
        mock_run.return_value.returncode = 0
        assert installer._check_npm_available() is True
        
        # Test npm not available
        mock_run.side_effect = FileNotFoundError()
        assert installer._check_npm_available() is False
    
    @patch('mcpi.installer.npm.subprocess.run')
    def test_is_installed(self, mock_run):
        """Test checking if npm package is installed."""
        installer = NPMInstaller(global_install=True, dry_run=True)
        
        # Test package installed
        mock_run.return_value.returncode = 0
        assert installer.is_installed("test-package") is True
        
        # Test package not installed
        mock_run.return_value.returncode = 1
        assert installer.is_installed("test-package") is False
    
    def test_get_install_flags(self):
        """Test getting npm install flags."""
        # Test global installation
        installer = NPMInstaller(global_install=True, dry_run=True)
        flags = installer._get_install_flags()
        assert "-g" in flags
        
        # Test local installation
        installer = NPMInstaller(global_install=False, dry_run=True)
        flags = installer._get_install_flags()
        assert "-g" not in flags
    
    def test_dry_run_commands(self):
        """Test dry run mode for npm commands."""
        installer = NPMInstaller(dry_run=True)
        
        result = installer._run_npm_command(["install", "test-package"])
        
        assert result.returncode == 0
        assert "[DRY RUN]" in result.stdout
        assert "npm install test-package" in result.stdout
    
    def test_supports_method(self):
        """Test installation method support."""
        installer = NPMInstaller(dry_run=True)
        
        assert installer._supports_method("npm") is True
        assert installer._supports_method("pip") is False
        assert installer._supports_method("git") is False


@pytest.fixture
def sample_server():
    """Fixture providing a sample MCP server for testing."""
    return MCPServer(**{
        "id": "test_server",
        "name": "Test Server",
        "description": "A test MCP server",
        "category": ["test"],
        "author": "Test Author",
        "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
        "installation": {
            "method": "npm",
            "package": "test-mcp-server",
            "system_dependencies": [],
            "python_dependencies": []
        },
        "configuration": {
            "required_params": ["test_param"],
            "optional_params": ["optional_param"]
        },
        "capabilities": ["test_capability"],
        "platforms": ["linux", "darwin", "windows"],
        "license": "MIT"
    })


@pytest.fixture
def npm_server():
    """Fixture providing an npm-based MCP server for testing."""
    return MCPServer(**{
        "id": "npm_server",
        "name": "NPM Test Server",
        "description": "NPM-based test server",
        "category": ["test"],
        "author": "Test",
        "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
        "installation": {
            "method": "npm",
            "package": "@test/mcp-server",
            "system_dependencies": [],
            "python_dependencies": []
        },
        "configuration": {},
        "capabilities": [],
        "platforms": ["linux", "darwin", "windows"],
        "license": "MIT"
    })