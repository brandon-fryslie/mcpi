"""Comprehensive tests for ConfigManager functionality."""

import json
import os
import platform
import shutil
import tempfile
import toml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import pytest
from pydantic import ValidationError

from mcpi.config.manager import ConfigManager, MCPIConfig, ProfileConfig, GeneralConfig, LoggingConfig


class TestConfigManagerErrorHandling:
    """Test error handling scenarios in ConfigManager."""
    
    def test_load_config_toml_decode_error(self, tmp_path):
        """Test loading config with invalid TOML."""
        config_path = tmp_path / "config.toml"
        
        # Create invalid TOML file
        config_path.write_text("[invalid toml content\nmissing closing bracket")
        
        manager = ConfigManager(config_path=config_path)
        
        with pytest.raises(ValueError, match="Invalid configuration file"):
            manager.load_config()
    
    def test_load_config_validation_error(self, tmp_path):
        """Test loading config with invalid data structure."""
        config_path = tmp_path / "config.toml"
        
        # Create TOML with invalid structure
        invalid_data = {"general": {"registry_url": 123}}  # Should be string
        with open(config_path, 'w') as f:
            toml.dump(invalid_data, f)
        
        manager = ConfigManager(config_path=config_path)
        
        with pytest.raises(ValueError, match="Invalid configuration file"):
            manager.load_config()
    
    def test_load_config_io_error(self, tmp_path):
        """Test loading config with I/O error."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("valid = true")
        config_path.chmod(0o000)  # Make unreadable
        
        manager = ConfigManager(config_path=config_path)
        
        try:
            with pytest.raises(ValueError, match="Invalid configuration file"):
                manager.load_config()
        finally:
            config_path.chmod(0o644)  # Restore permissions for cleanup
    
    def test_save_config_none(self, tmp_path):
        """Test saving None config."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        result = manager.save_config(None)
        assert result is False
    
    def test_save_config_io_error(self, tmp_path):
        """Test saving config with I/O error."""
        config_path = tmp_path / "readonly_dir" / "config.toml"
        readonly_dir = config_path.parent
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Make read-only
        
        manager = ConfigManager(config_path=config_path)
        config = MCPIConfig()
        
        try:
            result = manager.save_config(config)
            assert result is False
        finally:
            readonly_dir.chmod(0o755)  # Restore permissions for cleanup
    
    def test_save_config_os_error(self, tmp_path):
        """Test saving config with OS error."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        config = MCPIConfig()
        
        # Mock OSError during file write
        with patch("builtins.open", side_effect=OSError("Disk full")):
            result = manager.save_config(config)
            assert result is False


class TestConfigManagerTemplateLogic:
    """Test template application logic."""
    
    def test_initialize_with_development_template(self, tmp_path):
        """Test initialization with development template."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        result = manager.initialize(template="development")
        assert result is True
        
        config = manager.get_config()
        assert config.general.auto_update_registry is False
        assert config.logging.level == "DEBUG"
    
    def test_initialize_with_production_template(self, tmp_path):
        """Test initialization with production template."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        result = manager.initialize(template="production")
        assert result is True
        
        config = manager.get_config()
        assert config.general.auto_update_registry is True
        assert config.logging.level == "INFO"
    
    def test_initialize_with_unknown_template(self, tmp_path):
        """Test initialization with unknown template."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        result = manager.initialize(template="unknown")
        assert result is True  # Should still succeed, just ignore unknown template
        
        config = manager.get_config()
        # Should have default values
        assert config.general.auto_update_registry is True
        assert config.logging.level == "INFO"
    
    def test_initialize_exception_handling(self, tmp_path):
        """Test initialization exception handling."""
        config_path = tmp_path / "readonly_dir" / "config.toml"
        readonly_dir = config_path.parent
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Make read-only
        
        manager = ConfigManager(config_path=config_path)
        
        try:
            result = manager.initialize()
            assert result is False
        finally:
            readonly_dir.chmod(0o755)  # Restore permissions for cleanup


class TestConfigManagerProfileValidation:
    """Test profile validation functionality."""
    
    def test_validate_config_no_profiles(self, tmp_path):
        """Test validation with no profiles."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        # Create config with no profiles
        config = MCPIConfig()
        config.profiles = {}
        manager._config = config
        
        errors = manager.validate_config()
        assert len(errors) > 0
        assert any("No profiles defined" in error for error in errors)
    
    def test_validate_config_default_profile_missing(self, tmp_path):
        """Test validation when default profile is missing."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        # Create config with profiles but default not found
        config = MCPIConfig()
        config.general.default_profile = "missing"
        config.profiles = {"other": ProfileConfig(target="claude-code")}
        manager._config = config
        
        errors = manager.validate_config()
        assert len(errors) > 0
        assert any("Default profile 'missing' not found" in error for error in errors)
    
    def test_validate_config_invalid_target(self, tmp_path):
        """Test validation with invalid profile target."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Add profile with invalid target
        config = manager.get_config()
        config.profiles["invalid"] = ProfileConfig(target="invalid-target")
        
        errors = manager.validate_config()
        assert len(errors) > 0
        assert any("Invalid target 'invalid-target'" in error for error in errors)
    
    def test_validate_config_missing_config_directory(self, tmp_path):
        """Test validation with missing config directory."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Add profile with non-existent config path
        config = manager.get_config()
        config.profiles["test"] = ProfileConfig(
            target="claude-code",
            config_path="/nonexistent/path/config.json"
        )
        
        errors = manager.validate_config()
        assert len(errors) > 0
        assert any("Config directory does not exist" in error for error in errors)
    
    def test_validate_config_missing_python_executable(self, tmp_path):
        """Test validation with missing Python executable."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Add profile with non-existent Python path
        config = manager.get_config()
        config.profiles["test"] = ProfileConfig(
            target="claude-code",
            python_path="/nonexistent/python"
        )
        
        errors = manager.validate_config()
        assert len(errors) > 0
        assert any("Python executable not found" in error for error in errors)
    
    def test_validate_config_empty_registry_url(self, tmp_path):
        """Test validation with empty registry URL."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Set empty registry URL
        config = manager.get_config()
        config.general.registry_url = ""
        
        errors = manager.validate_config()
        assert len(errors) > 0
        assert any("Registry URL not configured" in error for error in errors)
    
    def test_validate_config_exception_handling(self, tmp_path):
        """Test validation exception handling."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        # Mock get_config to raise exception
        with patch.object(manager, 'get_config', side_effect=Exception("Test error")):
            errors = manager.validate_config()
            assert len(errors) > 0
            assert any("Configuration error: Test error" in error for error in errors)


class TestConfigManagerPlatformPaths:
    """Test platform-specific path detection."""
    
    @patch('platform.system')
    def test_get_claude_code_config_path_macos(self, mock_system, tmp_path):
        """Test getting Claude Code config path on macOS."""
        mock_system.return_value = "Darwin"
        
        manager = ConfigManager()
        path = manager._get_claude_code_config_path()
        
        expected = Path.home() / ".claude" / "mcp_servers.json"
        assert path == expected
    
    @patch('platform.system')
    def test_get_claude_code_config_path_linux(self, mock_system, tmp_path):
        """Test getting Claude Code config path on Linux."""
        mock_system.return_value = "Linux"
        
        manager = ConfigManager()
        path = manager._get_claude_code_config_path()
        
        expected = Path.home() / ".config" / "claude" / "mcp_servers.json"
        assert path == expected
    
    @patch('platform.system')
    @patch.dict(os.environ, {'APPDATA': '/fake/appdata'})
    def test_get_claude_code_config_path_windows(self, mock_system, tmp_path):
        """Test getting Claude Code config path on Windows."""
        mock_system.return_value = "Windows"
        
        manager = ConfigManager()
        path = manager._get_claude_code_config_path()
        
        expected = Path("/fake/appdata") / "claude" / "mcp_servers.json"
        assert path == expected
    
    @patch('platform.system')
    @patch.dict(os.environ, {}, clear=True)  # Clear APPDATA
    def test_get_claude_code_config_path_windows_no_appdata(self, mock_system, tmp_path):
        """Test getting Claude Code config path on Windows without APPDATA."""
        mock_system.return_value = "Windows"
        
        manager = ConfigManager()
        path = manager._get_claude_code_config_path()
        
        expected = Path("") / "claude" / "mcp_servers.json"  # Empty APPDATA fallback
        assert path == expected
    
    @patch('platform.system')
    def test_get_claude_code_config_path_unknown_os(self, mock_system, tmp_path):
        """Test getting Claude Code config path on unknown OS."""
        mock_system.return_value = "UnknownOS"
        
        manager = ConfigManager()
        path = manager._get_claude_code_config_path()
        
        expected = Path.home() / ".claude" / "mcp_servers.json"  # Fallback
        assert path == expected


class TestConfigManagerCacheDirectory:
    """Test cache directory functionality."""
    
    def test_get_cache_directory_configured(self, tmp_path):
        """Test getting cache directory when configured."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Set custom cache directory
        custom_cache = tmp_path / "custom_cache"
        config = manager.get_config()
        config.general.cache_directory = str(custom_cache)
        manager.save_config(config)
        
        cache_dir = manager.get_cache_directory()
        assert cache_dir == custom_cache.expanduser()
    
    def test_get_cache_directory_default(self, tmp_path):
        """Test getting default cache directory."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        cache_dir = manager.get_cache_directory()
        
        # Should use platformdirs default
        assert "mcpi" in str(cache_dir)
    
    def test_get_cache_directory_expanduser(self, tmp_path):
        """Test cache directory with user expansion."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Set cache directory with ~ 
        config = manager.get_config()
        config.general.cache_directory = "~/custom_cache"
        manager.save_config(config)
        
        cache_dir = manager.get_cache_directory()
        assert str(cache_dir).startswith(str(Path.home()))
        assert "custom_cache" in str(cache_dir)


class TestConfigManagerBackupRestore:
    """Test backup and restore functionality."""
    
    def test_backup_config_success(self, tmp_path):
        """Test successful config backup."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        backup_path = manager.backup_config()
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.suffix.startswith(".backup_")
        
        # Verify content is the same
        original_content = config_path.read_text()
        backup_content = backup_path.read_text()
        assert original_content == backup_content
    
    def test_backup_config_custom_path(self, tmp_path):
        """Test config backup with custom path."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        custom_backup = tmp_path / "custom_backup.toml"
        backup_path = manager.backup_config(custom_backup)
        
        assert backup_path == custom_backup
        assert custom_backup.exists()
        
        # Verify content is the same
        original_content = config_path.read_text()
        backup_content = custom_backup.read_text()
        assert original_content == backup_content
    
    def test_backup_config_no_file(self, tmp_path):
        """Test backup when config file doesn't exist."""
        config_path = tmp_path / "nonexistent.toml"
        manager = ConfigManager(config_path=config_path)
        
        backup_path = manager.backup_config()
        
        assert backup_path is None
    
    def test_backup_config_copy_error(self, tmp_path):
        """Test backup with copy error."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Mock shutil.copy2 to raise exception
        with patch('shutil.copy2', side_effect=Exception("Copy failed")):
            backup_path = manager.backup_config()
            
            assert backup_path is None
    
    def test_restore_config_success(self, tmp_path):
        """Test successful config restoration."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Modify config
        config = manager.get_config()
        config.general.registry_url = "https://modified.example.com"
        manager.save_config(config)
        modified_content = config_path.read_text()
        
        # Create backup with original content
        backup_path = tmp_path / "backup.toml"
        original_config = MCPIConfig()
        with open(backup_path, 'w') as f:
            toml.dump(original_config.model_dump(), f)
        
        result = manager.restore_config(backup_path)
        assert result is True
        
        # Verify content was restored
        restored_content = config_path.read_text()
        assert restored_content != modified_content
        
        # Config should be reloaded
        assert manager._config is None
    
    def test_restore_config_nonexistent_backup(self, tmp_path):
        """Test restore with nonexistent backup file."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        nonexistent_backup = tmp_path / "nonexistent.toml"
        result = manager.restore_config(nonexistent_backup)
        
        assert result is False
    
    def test_restore_config_copy_error(self, tmp_path):
        """Test restore with copy error."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        backup_path = tmp_path / "backup.toml"
        backup_path.write_text("test = true")
        
        # Mock shutil.copy2 to raise exception
        with patch('shutil.copy2', side_effect=Exception("Copy failed")):
            result = manager.restore_config(backup_path)
            
            assert result is False


class TestConfigManagerProfileOperations:
    """Test profile operations error handling."""
    
    def test_create_profile_exception_handling(self, tmp_path):
        """Test create profile with generic exception."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Mock get_config to raise exception  
        with patch.object(manager, 'get_config', side_effect=Exception("Test error")):
            result = manager.create_profile("test", target="claude-code")
            
            assert result is False
    
    def test_create_profile_save_error(self, tmp_path):
        """Test create profile with save error."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Mock save_config to fail
        with patch.object(manager, 'save_config', return_value=False):
            result = manager.create_profile("test", target="claude-code")
            
            assert result is False
    
    def test_delete_profile_nonexistent(self, tmp_path):
        """Test deleting nonexistent profile."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        result = manager.delete_profile("nonexistent")
        assert result is False
    
    def test_delete_profile_save_error(self, tmp_path):
        """Test delete profile with save error."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Create profile to delete
        manager.create_profile("to_delete", target="generic")
        
        # Mock save_config to fail
        with patch.object(manager, 'save_config', return_value=False):
            result = manager.delete_profile("to_delete")
            
            assert result is False
    
    def test_switch_profile_nonexistent(self, tmp_path):
        """Test switching to nonexistent profile."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        result = manager.switch_profile("nonexistent")
        assert result is False
    
    def test_switch_profile_save_error(self, tmp_path):
        """Test switch profile with save error."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Create profile to switch to
        manager.create_profile("test", target="generic")
        
        # Mock save_config to fail
        with patch.object(manager, 'save_config', return_value=False):
            result = manager.switch_profile("test")
            
            assert result is False
    
    def test_switch_profile_exception(self, tmp_path):
        """Test switch profile with exception."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Mock get_config to raise exception
        with patch.object(manager, 'get_config', side_effect=Exception("Test error")):
            result = manager.switch_profile("test")
            
            assert result is False
    
    def test_update_profile_nonexistent(self, tmp_path):
        """Test updating nonexistent profile."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        result = manager.update_profile("nonexistent", target="generic")
        assert result is False
    
    def test_update_profile_success(self, tmp_path):
        """Test successful profile update."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Create profile to update
        manager.create_profile("test", target="claude-code", install_global=True)
        
        result = manager.update_profile("test", install_global=False, use_uv=False)
        assert result is True
        
        # Verify updates
        profile = manager.get_profile("test")
        assert profile.install_global is False
        assert profile.use_uv is False
        assert profile.target == "claude-code"  # Should remain unchanged
    
    def test_update_profile_invalid_attribute(self, tmp_path):
        """Test updating profile with invalid attribute."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Create profile to update
        manager.create_profile("test", target="claude-code")
        
        # Should still succeed but ignore invalid attributes
        result = manager.update_profile("test", invalid_attr="value", target="generic")
        assert result is True
        
        # Verify valid update was applied, invalid ignored
        profile = manager.get_profile("test")
        assert profile.target == "generic"
        assert not hasattr(profile, "invalid_attr")
    
    def test_update_profile_save_error(self, tmp_path):
        """Test update profile with save error."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Create profile to update
        manager.create_profile("test", target="claude-code")
        
        # Mock save_config to fail
        with patch.object(manager, 'save_config', return_value=False):
            result = manager.update_profile("test", target="generic")
            
            assert result is False
    
    def test_update_profile_exception(self, tmp_path):
        """Test update profile with exception."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Mock get_config to raise exception
        with patch.object(manager, 'get_config', side_effect=Exception("Test error")):
            result = manager.update_profile("test", target="generic")
            
            assert result is False


class TestConfigManagerEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_get_config_lazy_loading(self, tmp_path):
        """Test config lazy loading behavior."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        # Initially no config loaded
        assert manager._config is None
        
        # First call should load config
        config1 = manager.get_config()
        assert manager._config is not None
        assert config1 is manager._config
        
        # Second call should return cached config
        config2 = manager.get_config()
        assert config2 is config1
    
    def test_ensure_default_profile_called(self, tmp_path):
        """Test that _ensure_default_profile is called during load."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        # Load config should create default profile
        config = manager.load_config()
        
        assert "default" in config.profiles
        assert config.general.default_profile == "default"
    
    def test_create_profile_claude_code_path_detection(self, tmp_path):
        """Test that claude-code target gets config path set automatically."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        result = manager.create_profile("claude_test", target="claude-code")
        assert result is True
        
        profile = manager.get_profile("claude_test")
        assert profile.config_path is not None
        assert "claude" in profile.config_path
        assert "mcp_servers.json" in profile.config_path