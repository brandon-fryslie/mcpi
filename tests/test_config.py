"""Tests for the config module."""

import json
import pytest
import toml
from pathlib import Path
from unittest.mock import patch

from mcpi.config.manager import ConfigManager, MCPIConfig, ProfileConfig
from mcpi.config.profiles import ProfileManager
from mcpi.config.templates import TemplateManager


class TestConfigManager:
    """Tests for ConfigManager class."""
    
    def test_init_with_default_path(self):
        """Test initialization with default config path."""
        manager = ConfigManager()
        assert manager.config_path.name == "config.toml"
        assert "mcpi" in str(manager.config_path)
    
    def test_init_with_custom_path(self, tmp_path):
        """Test initialization with custom config path."""
        config_path = tmp_path / "custom_config.toml"
        manager = ConfigManager(config_path=config_path)
        assert manager.config_path == config_path
    
    def test_load_config_creates_default(self, tmp_path):
        """Test loading config creates default when file doesn't exist."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        config = manager.load_config()
        
        assert isinstance(config, MCPIConfig)
        assert config.general.default_profile == "default"
        assert "default" in config.profiles
    
    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading configuration."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        # Create test configuration
        config = MCPIConfig()
        config.general.registry_url = "https://test.example.com/registry.json"
        config.profiles["test"] = ProfileConfig(target="claude-code")
        
        # Save configuration
        success = manager.save_config(config)
        assert success is True
        assert config_path.exists()
        
        # Load configuration
        loaded_config = manager.load_config()
        assert loaded_config.general.registry_url == "https://test.example.com/registry.json"
        assert "test" in loaded_config.profiles
    
    def test_initialize_config(self, tmp_path):
        """Test configuration initialization."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        success = manager.initialize()
        assert success is True
        assert config_path.exists()
        
        # Load and verify
        config = manager.load_config()
        assert "default" in config.profiles
        assert config.general.default_profile == "default"
    
    def test_initialize_with_custom_profile(self, tmp_path):
        """Test initialization with custom profile."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        
        success = manager.initialize(profile="development")
        assert success is True
        
        config = manager.load_config()
        assert "default" in config.profiles
        assert "development" in config.profiles
        assert config.general.default_profile == "development"
    
    def test_get_profile(self, tmp_path):
        """Test getting profile configuration."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Get default profile
        profile = manager.get_profile()
        assert isinstance(profile, ProfileConfig)
        assert profile.target == "claude-code"
        
        # Get specific profile
        profile = manager.get_profile("default")
        assert isinstance(profile, ProfileConfig)
        
        # Test non-existent profile
        with pytest.raises(ValueError):
            manager.get_profile("nonexistent")
    
    def test_create_profile(self, tmp_path):
        """Test creating new profiles."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Create new profile
        success = manager.create_profile("test_profile", target="generic")
        assert success is True
        
        # Verify profile was created
        profile = manager.get_profile("test_profile")
        assert profile.target == "generic"
        
        # Test creating duplicate profile
        success = manager.create_profile("test_profile", target="claude-code")
        assert success is False  # Should fail for duplicate
    
    def test_delete_profile(self, tmp_path):
        """Test deleting profiles."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Create profile to delete
        manager.create_profile("to_delete", target="generic")
        
        # Delete profile
        success = manager.delete_profile("to_delete")
        assert success is True
        
        # Verify deletion
        with pytest.raises(ValueError):
            manager.get_profile("to_delete")
        
        # Test deleting default profile (should fail)
        success = manager.delete_profile("default")
        assert success is False
    
    def test_list_profiles(self, tmp_path):
        """Test listing profiles."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Initially should have default profile
        profiles = manager.list_profiles()
        assert "default" in profiles
        
        # Add more profiles
        manager.create_profile("test1", target="generic")
        manager.create_profile("test2", target="claude-code")
        
        profiles = manager.list_profiles()
        assert len(profiles) == 3
        assert "test1" in profiles
        assert "test2" in profiles
    
    def test_switch_profile(self, tmp_path):
        """Test switching default profile."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Create new profile
        manager.create_profile("new_default", target="generic")
        
        # Switch to new profile
        success = manager.switch_profile("new_default")
        assert success is True
        
        config = manager.get_config()
        assert config.general.default_profile == "new_default"
        
        # Test switching to non-existent profile
        success = manager.switch_profile("nonexistent")
        assert success is False
    
    def test_validate_config(self, tmp_path):
        """Test configuration validation."""
        config_path = tmp_path / "config.toml"
        manager = ConfigManager(config_path=config_path)
        manager.initialize()
        
        # Valid configuration should have no errors
        errors = manager.validate_config()
        assert len(errors) == 0


class TestProfileManager:
    """Tests for ProfileManager class."""
    
    def test_init(self, tmp_path):
        """Test ProfileManager initialization."""
        config_path = tmp_path / "config.toml"
        config_manager = ConfigManager(config_path=config_path)
        profile_manager = ProfileManager(config_manager)
        
        assert profile_manager.config_manager == config_manager
    
    def test_create_claude_code_profile(self, tmp_path):
        """Test creating Claude Code profile."""
        config_path = tmp_path / "config.toml"
        config_manager = ConfigManager(config_path=config_path)
        config_manager.initialize()
        profile_manager = ProfileManager(config_manager)
        
        success = profile_manager.create_claude_code_profile("claude_test")
        assert success is True
        
        profile = config_manager.get_profile("claude_test")
        assert profile.target == "claude-code"
        assert profile.install_global is True
        assert profile.use_uv is True
    
    def test_create_development_profile(self, tmp_path):
        """Test creating development profile."""
        config_path = tmp_path / "config.toml"
        config_manager = ConfigManager(config_path=config_path)
        config_manager.initialize()
        profile_manager = ProfileManager(config_manager)
        
        project_path = "/path/to/project"
        success = profile_manager.create_development_profile("dev_test", project_path)
        assert success is True
        
        profile = config_manager.get_profile("dev_test")
        assert profile.target == "generic"
        assert profile.install_global is False
        assert profile.use_uv is True
        assert project_path in profile.config_path
    
    def test_clone_profile(self, tmp_path):
        """Test cloning profiles."""
        config_path = tmp_path / "config.toml"
        config_manager = ConfigManager(config_path=config_path)
        config_manager.initialize()
        profile_manager = ProfileManager(config_manager)
        
        # Create source profile
        config_manager.create_profile("source", target="claude-code", install_global=True)
        
        # Clone profile with modifications
        success = profile_manager.clone_profile(
            "source", 
            "cloned", 
            modifications={"install_global": False}
        )
        assert success is True
        
        # Verify cloned profile
        cloned_profile = config_manager.get_profile("cloned")
        assert cloned_profile.target == "claude-code"  # Inherited
        assert cloned_profile.install_global is False  # Modified
    
    def test_export_import_profile(self, tmp_path):
        """Test exporting and importing profiles."""
        config_path = tmp_path / "config.toml"
        config_manager = ConfigManager(config_path=config_path)
        config_manager.initialize()
        profile_manager = ProfileManager(config_manager)
        
        # Create profile to export
        config_manager.create_profile("export_test", target="generic", install_global=False)
        
        # Export profile
        export_path = tmp_path / "exported_profile.json"
        success = profile_manager.export_profile("export_test", export_path)
        assert success is True
        assert export_path.exists()
        
        # Delete original profile
        config_manager.delete_profile("export_test")
        
        # Import profile
        success = profile_manager.import_profile(export_path, "imported_test")
        assert success is True
        
        # Verify imported profile
        imported_profile = config_manager.get_profile("imported_test")
        assert imported_profile.target == "generic"
        assert imported_profile.install_global is False


class TestTemplateManager:
    """Tests for TemplateManager class."""
    
    def test_init_with_default_path(self):
        """Test initialization with default templates directory."""
        manager = TemplateManager()
        assert "templates" in str(manager.templates_dir)
    
    def test_init_with_custom_path(self, tmp_path):
        """Test initialization with custom templates directory."""
        templates_dir = tmp_path / "custom_templates"
        manager = TemplateManager(templates_dir=templates_dir)
        assert manager.templates_dir == templates_dir
    
    def test_get_template(self, tmp_path):
        """Test getting configuration template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Create test template
        template_data = {"test": "template", "command": "test_cmd", "args": []}
        template_path = templates_dir / "test_template.json"
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        manager = TemplateManager(templates_dir=templates_dir)
        
        # Get existing template
        template = manager.get_template("test_template")
        assert template == template_data
        
        # Get non-existent template
        template = manager.get_template("nonexistent")
        assert template is None
    
    def test_list_templates(self, tmp_path):
        """Test listing available templates."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Create test templates
        (templates_dir / "template1.json").write_text('{}')
        (templates_dir / "template2.json").write_text('{}')
        
        manager = TemplateManager(templates_dir=templates_dir)
        templates = manager.list_templates()
        
        assert len(templates) == 2
        assert "template1" in templates
        assert "template2" in templates
        assert templates == sorted(templates)  # Should be sorted
    
    def test_create_template(self, tmp_path):
        """Test creating new template."""
        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir=templates_dir)
        
        template_data = {"command": "test", "args": ["arg1", "arg2"]}
        success = manager.create_template("new_template", template_data)
        assert success is True
        
        # Verify template was created
        template_path = templates_dir / "new_template.json"
        assert template_path.exists()
        
        with open(template_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == template_data
    
    def test_delete_template(self, tmp_path):
        """Test deleting template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Create template to delete
        template_path = templates_dir / "to_delete.json"
        template_path.write_text('{}')
        
        manager = TemplateManager(templates_dir=templates_dir)
        
        # Delete template
        success = manager.delete_template("to_delete")
        assert success is True
        assert not template_path.exists()
        
        # Try deleting non-existent template
        success = manager.delete_template("nonexistent")
        assert success is False
    
    def test_validate_template(self):
        """Test template validation."""
        manager = TemplateManager()
        
        # Valid template
        valid_template = {"command": "test", "args": ["arg1"]}
        errors = manager.validate_template(valid_template)
        assert len(errors) == 0
        
        # Invalid template - missing command
        invalid_template = {"args": ["arg1"]}
        errors = manager.validate_template(invalid_template)
        assert len(errors) > 0
        assert any("command" in error for error in errors)
        
        # Invalid template - args not a list
        invalid_template2 = {"command": "test", "args": "not_a_list"}
        errors = manager.validate_template(invalid_template2)
        assert len(errors) > 0
        assert any("args" in error for error in errors)
    
    def test_generate_default_templates(self, tmp_path):
        """Test generating default templates."""
        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir=templates_dir)
        
        success = manager.generate_default_templates()
        assert success is True
        
        # Verify some default templates were created
        templates = manager.list_templates()
        assert len(templates) > 0
        assert "filesystem_template" in templates
        assert "sqlite_template" in templates
        
        # Verify template content
        filesystem_template = manager.get_template("filesystem_template")
        assert filesystem_template is not None
        assert "description" in filesystem_template