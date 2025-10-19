"""Comprehensive tests for the config profiles module."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from mcpi.config.profiles import ProfileManager
from mcpi.config.manager import ConfigManager, ProfileConfig, MCPIConfig


class TestProfileManagerInit:
    """Tests for ProfileManager initialization."""
    
    def test_profile_manager_init(self):
        """Test ProfileManager initialization."""
        config_manager = Mock(spec=ConfigManager)
        profile_manager = ProfileManager(config_manager)
        
        assert profile_manager.config_manager is config_manager


class TestCreateClaudeCodeProfile:
    """Tests for creating Claude Code profiles."""
    
    def test_create_claude_code_profile_basic(self):
        """Test creating basic Claude Code profile."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.create_profile.return_value = True
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.create_claude_code_profile("claude_test")
        
        assert result is True
        config_manager.create_profile.assert_called_once_with(
            "claude_test",
            target="claude-code",
            install_global=True,
            use_uv=True
        )
    
    def test_create_claude_code_profile_with_config_path(self):
        """Test creating Claude Code profile with config path."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.create_profile.return_value = True
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.create_claude_code_profile("claude_test", "/path/to/config")
        
        assert result is True
        config_manager.create_profile.assert_called_once_with(
            "claude_test",
            target="claude-code",
            install_global=True,
            use_uv=True,
            config_path="/path/to/config"
        )
    
    def test_create_claude_code_profile_failure(self):
        """Test Claude Code profile creation failure."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.create_profile.return_value = False
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.create_claude_code_profile("claude_test")
        
        assert result is False


class TestCreateDevelopmentProfile:
    """Tests for creating development profiles."""
    
    def test_create_development_profile_basic(self):
        """Test creating basic development profile."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.create_profile.return_value = True
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.create_development_profile("dev_test", "/project/path")
        
        assert result is True
        config_manager.create_profile.assert_called_once_with(
            "dev_test",
            target="generic",
            config_path="/project/path/mcp_servers.json",
            install_global=False,
            use_uv=True
        )
    
    def test_create_development_profile_failure(self):
        """Test development profile creation failure."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.create_profile.return_value = False
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.create_development_profile("dev_test", "/project/path")
        
        assert result is False


class TestCreateProductionProfile:
    """Tests for creating production profiles."""
    
    def test_create_production_profile_basic(self):
        """Test creating basic production profile."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.create_profile.return_value = True
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.create_production_profile("prod_test", "/config/path")
        
        assert result is True
        config_manager.create_profile.assert_called_once_with(
            "prod_test",
            target="generic",
            config_path="/config/path",
            install_global=True,
            use_uv=False
        )
    
    def test_create_production_profile_failure(self):
        """Test production profile creation failure."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.create_profile.return_value = False
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.create_production_profile("prod_test", "/config/path")
        
        assert result is False


class TestCloneProfile:
    """Tests for cloning profiles."""
    
    def test_clone_profile_basic(self):
        """Test basic profile cloning."""
        source_profile = Mock(spec=ProfileConfig)
        source_profile.model_dump.return_value = {
            "target": "claude-code",
            "config_path": "/original/config",
            "install_global": True,
            "use_uv": True
        }
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"source": source_profile}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager.save_config.return_value = True
        
        with patch('mcpi.config.profiles.ProfileConfig') as mock_profile_config:
            mock_target_profile = Mock(spec=ProfileConfig)
            mock_profile_config.return_value = mock_target_profile
            
            profile_manager = ProfileManager(config_manager)
            result = profile_manager.clone_profile("source", "target")
        
        assert result is True
        mock_profile_config.assert_called_once()
        assert config.profiles["target"] is mock_target_profile
        config_manager.save_config.assert_called_once_with(config)
    
    def test_clone_profile_with_modifications(self):
        """Test profile cloning with modifications."""
        source_profile = Mock(spec=ProfileConfig)
        source_profile.model_dump.return_value = {
            "target": "claude-code",
            "config_path": "/original/config",
            "install_global": True,
            "use_uv": True
        }
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"source": source_profile}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager.save_config.return_value = True
        
        modifications = {"target": "generic", "use_uv": False}
        
        with patch('mcpi.config.profiles.ProfileConfig') as mock_profile_config:
            mock_target_profile = Mock(spec=ProfileConfig)
            mock_profile_config.return_value = mock_target_profile
            
            profile_manager = ProfileManager(config_manager)
            result = profile_manager.clone_profile("source", "target", modifications)
        
        assert result is True
        expected_data = {
            "target": "generic",
            "config_path": "/original/config",
            "install_global": True,
            "use_uv": False
        }
        mock_profile_config.assert_called_once_with(**expected_data)
    
    def test_clone_profile_source_not_found(self):
        """Test cloning when source profile doesn't exist."""
        config = Mock(spec=MCPIConfig)
        config.profiles = {}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.clone_profile("nonexistent", "target")
        
        assert result is False
    
    def test_clone_profile_target_exists(self):
        """Test cloning when target profile already exists."""
        source_profile = Mock(spec=ProfileConfig)
        target_profile = Mock(spec=ProfileConfig)
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {
            "source": source_profile,
            "target": target_profile
        }
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.clone_profile("source", "target")
        
        assert result is False
    
    def test_clone_profile_exception(self):
        """Test profile cloning with exception."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.side_effect = Exception("Test error")
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.clone_profile("source", "target")
        
        assert result is False


class TestExportProfile:
    """Tests for exporting profiles."""
    
    def test_export_profile_success(self):
        """Test successful profile export."""
        profile = Mock(spec=ProfileConfig)
        profile.model_dump.return_value = {
            "target": "claude-code",
            "config_path": "/test/config",
            "install_global": True,
            "use_uv": True
        }
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"test_profile": profile}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            export_path = Path(temp_file.name)
            
            result = profile_manager.export_profile("test_profile", export_path)
            
            assert result is True
            
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            expected_data = {
                "profile_name": "test_profile",
                "profile_config": {
                    "target": "claude-code",
                    "config_path": "/test/config",
                    "install_global": True,
                    "use_uv": True
                }
            }
            
            assert exported_data == expected_data
            
            export_path.unlink()  # Clean up
    
    def test_export_profile_not_found(self):
        """Test exporting non-existent profile."""
        config = Mock(spec=MCPIConfig)
        config.profiles = {}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        export_path = Path("/tmp/test_export.json")
        
        result = profile_manager.export_profile("nonexistent", export_path)
        
        assert result is False
    
    def test_export_profile_exception(self):
        """Test profile export with exception."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.side_effect = Exception("Test error")
        
        profile_manager = ProfileManager(config_manager)
        export_path = Path("/tmp/test_export.json")
        
        result = profile_manager.export_profile("test_profile", export_path)
        
        assert result is False


class TestImportProfile:
    """Tests for importing profiles."""
    
    def test_import_profile_success(self):
        """Test successful profile import."""
        profile_data = {
            "profile_name": "imported_profile",
            "profile_config": {
                "target": "claude-code",
                "config_path": "/imported/config",
                "install_global": True,
                "use_uv": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(profile_data, temp_file)
            import_path = Path(temp_file.name)
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager.save_config.return_value = True
        
        with patch('mcpi.config.profiles.ProfileConfig') as mock_profile_config:
            mock_imported_profile = Mock(spec=ProfileConfig)
            mock_profile_config.return_value = mock_imported_profile
            
            profile_manager = ProfileManager(config_manager)
            result = profile_manager.import_profile(import_path)
        
        assert result is True
        mock_profile_config.assert_called_once_with(**profile_data["profile_config"])
        assert config.profiles["imported_profile"] is mock_imported_profile
        config_manager.save_config.assert_called_once_with(config)
        
        import_path.unlink()  # Clean up
    
    def test_import_profile_with_custom_name(self):
        """Test profile import with custom name."""
        profile_data = {
            "profile_name": "original_name",
            "profile_config": {
                "target": "claude-code",
                "config_path": "/imported/config",
                "install_global": True,
                "use_uv": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(profile_data, temp_file)
            import_path = Path(temp_file.name)
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager.save_config.return_value = True
        
        with patch('mcpi.config.profiles.ProfileConfig') as mock_profile_config:
            mock_imported_profile = Mock(spec=ProfileConfig)
            mock_profile_config.return_value = mock_imported_profile
            
            profile_manager = ProfileManager(config_manager)
            result = profile_manager.import_profile(import_path, "custom_name")
        
        assert result is True
        assert config.profiles["custom_name"] is mock_imported_profile
        
        import_path.unlink()  # Clean up
    
    def test_import_profile_file_not_found(self):
        """Test importing from non-existent file."""
        profile_manager = ProfileManager(Mock(spec=ConfigManager))
        import_path = Path("/nonexistent/file.json")
        
        result = profile_manager.import_profile(import_path)
        
        assert result is False
    
    def test_import_profile_invalid_json(self):
        """Test importing invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write("invalid json content")
            import_path = Path(temp_file.name)
        
        profile_manager = ProfileManager(Mock(spec=ConfigManager))
        result = profile_manager.import_profile(import_path)
        
        assert result is False
        
        import_path.unlink()  # Clean up
    
    def test_import_profile_exception(self):
        """Test profile import with exception."""
        profile_data = {
            "profile_name": "test",
            "profile_config": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(profile_data, temp_file)
            import_path = Path(temp_file.name)
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.side_effect = Exception("Test error")
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.import_profile(import_path)
        
        assert result is False
        
        import_path.unlink()  # Clean up


class TestGetProfileSummary:
    """Tests for getting profile summaries."""
    
    def test_get_profile_summary_success(self):
        """Test successful profile summary retrieval."""
        profile = Mock(spec=ProfileConfig)
        profile.target = "claude-code"
        profile.config_path = "/test/config"
        profile.install_global = True
        profile.use_uv = True
        profile.python_path = "/usr/bin/python3"
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_profile.return_value = profile
        
        profile_manager = ProfileManager(config_manager)
        summary = profile_manager.get_profile_summary("test_profile")
        
        expected_summary = {
            "name": "test_profile",
            "target": "claude-code",
            "config_path": "/test/config",
            "install_global": True,
            "use_uv": True,
            "python_path": "/usr/bin/python3"
        }
        
        assert summary == expected_summary
    
    def test_get_profile_summary_not_found(self):
        """Test profile summary for non-existent profile."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_profile.side_effect = ValueError("Profile not found")
        
        profile_manager = ProfileManager(config_manager)
        summary = profile_manager.get_profile_summary("nonexistent")
        
        assert summary is None


class TestListProfilesDetailed:
    """Tests for listing profiles with details."""
    
    def test_list_profiles_detailed_success(self):
        """Test successful detailed profiles listing."""
        config = Mock(spec=MCPIConfig)
        config.general = Mock(); config.general.default_profile = "default_profile"
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.list_profiles.return_value = ["default_profile", "other_profile"]
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        
        def mock_get_summary(name):
            if name == "default_profile":
                return {
                    "name": "default_profile",
                    "target": "claude-code",
                    "config_path": "/existing/config.json",
                    "install_global": True,
                    "use_uv": True,
                    "python_path": None
                }
            elif name == "other_profile":
                return {
                    "name": "other_profile",
                    "target": "generic",
                    "config_path": None,
                    "install_global": False,
                    "use_uv": False,
                    "python_path": "/usr/bin/python3"
                }
            return None
        
        profile_manager.get_profile_summary = Mock(side_effect=mock_get_summary)
        
        with patch('mcpi.config.profiles.Path') as mock_path:
            mock_path.return_value.expanduser.return_value.exists.return_value = True
            
            profiles = profile_manager.list_profiles_detailed()
        
        assert len(profiles) == 2
        
        # Check default profile
        default_prof = next(p for p in profiles if p["name"] == "default_profile")
        assert default_prof["is_default"] is True
        assert default_prof["config_exists"] is True
        
        # Check other profile
        other_prof = next(p for p in profiles if p["name"] == "other_profile")
        assert other_prof["is_default"] is False
        assert other_prof["config_exists"] is None
    
    def test_list_profiles_detailed_empty(self):
        """Test detailed listing with no profiles."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.list_profiles.return_value = []
        
        profile_manager = ProfileManager(config_manager)
        profiles = profile_manager.list_profiles_detailed()
        
        assert profiles == []
    
    def test_list_profiles_detailed_with_missing_config(self):
        """Test detailed listing with missing config file."""
        config = Mock(spec=MCPIConfig)
        config.general = Mock(); config.general.default_profile = "test_profile"
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.list_profiles.return_value = ["test_profile"]
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        profile_manager.get_profile_summary = Mock(return_value={
            "name": "test_profile",
            "target": "claude-code",
            "config_path": "/nonexistent/config.json",
            "install_global": True,
            "use_uv": True,
            "python_path": None
        })
        
        with patch('mcpi.config.profiles.Path') as mock_path:
            mock_path.return_value.expanduser.return_value.exists.return_value = False
            
            profiles = profile_manager.list_profiles_detailed()
        
        assert len(profiles) == 1
        assert profiles[0]["config_exists"] is False


class TestValidateAllProfiles:
    """Tests for validating all profiles."""
    
    def test_validate_all_profiles_success(self):
        """Test validating all profiles successfully."""
        profile1 = Mock(spec=ProfileConfig)
        profile2 = Mock(spec=ProfileConfig)
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {
            "profile1": profile1,
            "profile2": profile2
        }
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager._validate_profile.side_effect = [
            ["Error 1", "Error 2"],  # profile1 has errors
            []  # profile2 has no errors
        ]
        
        profile_manager = ProfileManager(config_manager)
        validation_results = profile_manager.validate_all_profiles()
        
        expected_results = {
            "profile1": ["Error 1", "Error 2"]
        }
        
        assert validation_results == expected_results
    
    def test_validate_all_profiles_no_errors(self):
        """Test validating profiles with no errors."""
        profile1 = Mock(spec=ProfileConfig)
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"profile1": profile1}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager._validate_profile.return_value = []
        
        profile_manager = ProfileManager(config_manager)
        validation_results = profile_manager.validate_all_profiles()
        
        assert validation_results == {}


class TestSuggestProfileName:
    """Tests for suggesting profile names."""
    
    def test_suggest_profile_name_available(self):
        """Test suggesting name when original is available."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.list_profiles.return_value = ["existing1", "existing2"]
        
        profile_manager = ProfileManager(config_manager)
        suggested = profile_manager.suggest_profile_name("new_profile")
        
        assert suggested == "new_profile"
    
    def test_suggest_profile_name_exists(self):
        """Test suggesting name when original exists."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.list_profiles.return_value = ["existing_profile", "other"]
        
        profile_manager = ProfileManager(config_manager)
        suggested = profile_manager.suggest_profile_name("existing_profile")
        
        assert suggested == "existing_profile_1"
    
    def test_suggest_profile_name_multiple_conflicts(self):
        """Test suggesting name when original exists."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.list_profiles.return_value = [
            "test_profile", 
            "test_profile_1", 
            "test_profile_2"
        ]
        
        profile_manager = ProfileManager(config_manager)
        suggested = profile_manager.suggest_profile_name("test_profile")
        
        assert suggested == "test_profile_3"


class TestGetCompatibleProfiles:
    """Tests for getting compatible profiles."""
    
    def test_get_compatible_profiles_found(self):
        """Test finding compatible profiles."""
        profile1 = Mock(spec=ProfileConfig)
        profile1.target = "claude-code"
        
        profile2 = Mock(spec=ProfileConfig)
        profile2.target = "generic"
        
        profile3 = Mock(spec=ProfileConfig)
        profile3.target = "claude-code"
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {
            "profile1": profile1,
            "profile2": profile2,
            "profile3": profile3
        }
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        compatible = profile_manager.get_compatible_profiles("claude-code")
        
        assert set(compatible) == {"profile1", "profile3"}
    
    def test_get_compatible_profiles_none_found(self):
        """Test when no compatible profiles found."""
        profile1 = Mock(spec=ProfileConfig)
        profile1.target = "generic"
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"profile1": profile1}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        compatible = profile_manager.get_compatible_profiles("claude-code")
        
        assert compatible == []


class TestMigrateProfile:
    """Tests for migrating profiles."""
    
    def test_migrate_profile_success(self):
        """Test successful profile migration."""
        profile = Mock(spec=ProfileConfig)
        profile.target = "generic"
        profile.config_path = "/original/config"
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"test_profile": profile}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager.save_config.return_value = True
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.migrate_profile("test_profile", "claude-code")
        
        assert result is True
        assert profile.target == "claude-code"
        config_manager.save_config.assert_called_once_with(config)
    
    def test_migrate_profile_with_kwargs(self):
        """Test profile migration with additional kwargs."""
        # Create a proper mock with the required attributes
        profile = Mock()
        profile.target = "generic"
        profile.use_uv = False
        profile.install_global = False
        profile.config_path = "/original/config"
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"test_profile": profile}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager.save_config.return_value = True
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.migrate_profile(
            "test_profile", 
            "claude-code", 
            use_uv=True, 
            install_global=True
        )
        
        assert result is True
        assert profile.target == "claude-code"
        assert profile.use_uv is True
        assert profile.install_global is True
    
    def test_migrate_profile_not_found(self):
        """Test migrating non-existent profile."""
        config = Mock(spec=MCPIConfig)
        config.profiles = {}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.migrate_profile("nonexistent", "claude-code")
        
        assert result is False
    
    def test_migrate_profile_exception(self):
        """Test profile migration with exception."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.side_effect = Exception("Test error")
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.migrate_profile("test_profile", "claude-code")
        
        assert result is False
    
    def test_migrate_profile_claude_code_with_existing_config(self):
        """Test migrating to Claude Code with existing config path."""
        profile = Mock(spec=ProfileConfig)
        profile.target = "generic"
        profile.config_path = "/existing/config"
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"test_profile": profile}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager.save_config.return_value = True
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.migrate_profile("test_profile", "claude-code")
        
        assert result is True
        assert profile.target == "claude-code"
        assert profile.config_path == "/existing/config"  # Should not be overridden
    
    def test_migrate_profile_claude_code_without_config(self):
        """Test migrating to Claude Code without existing config path."""
        profile = Mock(spec=ProfileConfig)
        profile.target = "generic"
        profile.config_path = None
        
        config = Mock(spec=MCPIConfig)
        config.profiles = {"test_profile": profile}
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_config.return_value = config
        config_manager.save_config.return_value = True
        config_manager._get_claude_code_config_path.return_value = Path("/claude/config")
        
        profile_manager = ProfileManager(config_manager)
        result = profile_manager.migrate_profile("test_profile", "claude-code")
        
        assert result is True
        assert profile.target == "claude-code"
        assert profile.config_path == "/claude/config"