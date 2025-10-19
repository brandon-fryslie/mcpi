"""Refactored tests for the config profiles module showing improved patterns."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from mcpi.config.profiles import ProfileManager
from mcpi.config.manager import ConfigManager, ProfileConfig, MCPIConfig
from tests.conftest import create_mock_profile


class TestProfileManagerInit:
    """Tests for ProfileManager initialization."""
    
    def test_profile_manager_init(self, mock_config_manager):
        """Test ProfileManager initialization."""
        profile_manager = ProfileManager(mock_config_manager)
        assert profile_manager.config_manager is mock_config_manager


class TestCreateClaudeCodeProfile:
    """Tests for creating Claude Code profiles."""
    
    def test_create_claude_code_profile_basic(self, mock_config_manager):
        """Test creating basic Claude Code profile."""
        mock_config_manager.create_profile.return_value = True
        
        profile_manager = ProfileManager(mock_config_manager)
        result = profile_manager.create_claude_code_profile("claude_test")
        
        assert result is True
        mock_config_manager.create_profile.assert_called_once_with(
            "claude_test",
            target="claude-code",
            install_global=True,
            use_uv=True
        )
    
    def test_create_claude_code_profile_with_config_path(self, mock_config_manager):
        """Test creating Claude Code profile with config path."""
        mock_config_manager.create_profile.return_value = True
        
        profile_manager = ProfileManager(mock_config_manager)
        result = profile_manager.create_claude_code_profile("claude_test", "/path/to/config")
        
        assert result is True
        mock_config_manager.create_profile.assert_called_once_with(
            "claude_test",
            target="claude-code",
            install_global=True,
            use_uv=True,
            config_path="/path/to/config"
        )
    
    def test_create_claude_code_profile_failure(self, mock_config_manager):
        """Test Claude Code profile creation failure."""
        mock_config_manager.create_profile.return_value = False
        
        profile_manager = ProfileManager(mock_config_manager)
        result = profile_manager.create_claude_code_profile("claude_test")
        
        assert result is False


class TestGetProfileSummary:
    """Tests for getting profile summaries."""
    
    def test_get_profile_summary_success(self, mock_config_manager):
        """Test successful profile summary retrieval."""
        profile = create_mock_profile(
            target="claude-code",
            config_path="/test/config",
            install_global=True,
            use_uv=True,
            python_path="/usr/bin/python3"
        )
        
        mock_config_manager.get_profile.return_value = profile
        
        profile_manager = ProfileManager(mock_config_manager)
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
    
    def test_get_profile_summary_not_found(self, mock_config_manager):
        """Test profile summary for non-existent profile."""
        mock_config_manager.get_profile.side_effect = ValueError("Profile not found")
        
        profile_manager = ProfileManager(mock_config_manager)
        summary = profile_manager.get_profile_summary("nonexistent")
        
        assert summary is None


class TestMigrateProfile:
    """Tests for migrating profiles."""
    
    def test_migrate_profile_success(self, mock_config_manager, mock_mcpi_config):
        """Test successful profile migration."""
        profile = create_mock_profile(
            target="generic",
            config_path="/original/config"
        )
        
        mock_mcpi_config.profiles = {"test_profile": profile}
        mock_config_manager.get_config.return_value = mock_mcpi_config
        mock_config_manager.save_config.return_value = True
        
        profile_manager = ProfileManager(mock_config_manager)
        result = profile_manager.migrate_profile("test_profile", "claude-code")
        
        assert result is True
        assert profile.target == "claude-code"
        mock_config_manager.save_config.assert_called_once_with(mock_mcpi_config)
    
    def test_migrate_profile_with_kwargs(self, mock_config_manager, mock_mcpi_config):
        """Test profile migration with additional kwargs."""
        profile = create_mock_profile(
            target="generic",
            use_uv=False,
            install_global=False,
            config_path="/original/config"
        )
        
        mock_mcpi_config.profiles = {"test_profile": profile}
        mock_config_manager.get_config.return_value = mock_mcpi_config
        mock_config_manager.save_config.return_value = True
        
        profile_manager = ProfileManager(mock_config_manager)
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