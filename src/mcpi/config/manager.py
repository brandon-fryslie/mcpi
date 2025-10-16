"""Configuration management for mcpi."""

import datetime
import os
import platform
import shutil
import toml
from pathlib import Path
from typing import Dict, Any, Optional, List
from platformdirs import user_config_dir, user_cache_dir
from pydantic import BaseModel, Field, ValidationError


# Constants
DEFAULT_REGISTRY_URL = "https://registry.mcpi.dev/v1/servers.json"
DEFAULT_PROFILE_NAME = "default"
VALID_TARGETS = ["claude-code", "generic"]
CLAUDE_CONFIG_FILENAME = "mcp_servers.json"

# Platform-specific Claude Code config paths
CLAUDE_PATHS = {
    "Darwin": Path.home() / ".claude" / CLAUDE_CONFIG_FILENAME,  # macOS
    "Linux": Path.home() / ".config" / "claude" / CLAUDE_CONFIG_FILENAME,
    "Windows": lambda: Path(os.environ.get("APPDATA", "")) / "claude" / CLAUDE_CONFIG_FILENAME,
}

# Configuration templates
CONFIG_TEMPLATES = {
    "development": {
        "auto_update_registry": False,
        "logging_level": "DEBUG"
    },
    "production": {
        "auto_update_registry": True,
        "logging_level": "INFO"
    }
}


class GeneralConfig(BaseModel):
    """General configuration settings."""
    registry_url: str = Field(default=DEFAULT_REGISTRY_URL)
    auto_update_registry: bool = Field(default=True)
    default_profile: str = Field(default=DEFAULT_PROFILE_NAME)
    cache_directory: Optional[str] = Field(default=None)


class ProfileConfig(BaseModel):
    """Profile-specific configuration."""
    target: str = Field(description="Installation target (claude-code, generic, etc.)")
    config_path: Optional[str] = Field(default=None, description="Path to target config file")
    install_global: bool = Field(default=True, description="Install packages globally")
    python_path: Optional[str] = Field(default=None, description="Python executable path")
    use_uv: bool = Field(default=True, description="Prefer uv over pip for Python packages")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    file: Optional[str] = Field(default=None)
    console: bool = Field(default=True)


class MCPIConfig(BaseModel):
    """Complete mcpi configuration."""
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    profiles: Dict[str, ProfileConfig] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class ConfigManager:
    """Manages mcpi configuration files and profiles."""

    def __init__(self, config_path: Optional[Path] = None, config_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file. If None, uses default location.
            config_dir: Directory for configuration files. If provided, config_path is relative to this.
        """
        if config_path is None:
            if config_dir is not None:
                self.config_path = config_dir / "config.toml"
            else:
                config_dir = Path(user_config_dir("mcpi", "mcpi"))
                self.config_path = config_dir / "config.toml"
        else:
            if config_dir is not None and not config_path.is_absolute():
                self.config_path = config_dir / config_path
            else:
                self.config_path = config_path

        self._config: Optional[MCPIConfig] = None

    def load_config(self) -> MCPIConfig:
        """Load configuration from file.

        Returns:
            Loaded configuration

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config_path.exists():
            self._config = MCPIConfig()
            self._ensure_default_profile()
            return self._config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)

            self._config = MCPIConfig(**data)
            self._ensure_default_profile()
            return self._config

        except (toml.TomlDecodeError, ValidationError, IOError) as e:
            raise ValueError(f"Invalid configuration file: {e}")

    def save_config(self, config: Optional[MCPIConfig] = None) -> bool:
        """Save configuration to file.

        Args:
            config: Configuration to save. If None, uses current config.

        Returns:
            True if save successful, False otherwise
        """
        if config is None:
            config = self._config

        if config is None:
            return False

        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary and save
            data = config.model_dump()

            with open(self.config_path, 'w', encoding='utf-8') as f:
                toml.dump(data, f)

            self._config = config
            return True

        except (IOError, OSError):
            return False

    def get_config(self) -> MCPIConfig:
        """Get current configuration, loading if necessary.

        Returns:
            Current configuration
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def initialize(self, profile: Optional[str] = None, template: Optional[str] = None) -> bool:
        """Initialize configuration with defaults.

        Args:
            profile: Profile name to initialize
            template: Configuration template to use

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            config = MCPIConfig()

            # Create default profile
            default_profile = self._create_default_profile()
            config.profiles[DEFAULT_PROFILE_NAME] = default_profile

            # Create additional profile if specified
            if profile and profile != DEFAULT_PROFILE_NAME:
                config.profiles[profile] = self._create_default_profile()
                config.general.default_profile = profile

            # Apply template if specified
            if template:
                self._apply_template(config, template)

            return self.save_config(config)

        except Exception:
            return False

    def get_profile(self, profile_name: Optional[str] = None) -> ProfileConfig:
        """Get profile configuration.

        Args:
            profile_name: Profile name. If None, uses default profile.

        Returns:
            Profile configuration

        Raises:
            ValueError: If profile not found
        """
        config = self.get_config()

        if profile_name is None:
            profile_name = config.general.default_profile

        if profile_name not in config.profiles:
            raise ValueError(f"Profile '{profile_name}' not found")

        return config.profiles[profile_name]

    def create_profile(self, name: str, target: str = "claude-code", **kwargs: Any) -> bool:
        """Create new profile.

        Args:
            name: Profile name
            target: Installation target
            **kwargs: Additional profile settings

        Returns:
            True if creation successful, False otherwise
        """
        try:
            config = self.get_config()

            if name in config.profiles:
                return False  # Profile already exists

            profile_config = ProfileConfig(target=target, **kwargs)

            # Set target-specific defaults
            if target == "claude-code":
                profile_config.config_path = str(self._get_claude_code_config_path())

            config.profiles[name] = profile_config
            return self.save_config(config)

        except (ValidationError, Exception):
            return False

    def delete_profile(self, name: str) -> bool:
        """Delete profile.

        Args:
            name: Profile name to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            config = self.get_config()

            if name not in config.profiles:
                return False  # Profile doesn't exist

            if name == config.general.default_profile:
                return False  # Cannot delete default profile

            del config.profiles[name]
            return self.save_config(config)

        except Exception:
            return False

    def list_profiles(self) -> List[str]:
        """Get list of profile names.

        Returns:
            List of profile names
        """
        config = self.get_config()
        return list(config.profiles.keys())

    def switch_profile(self, name: str) -> bool:
        """Switch default profile.

        Args:
            name: Profile name to switch to

        Returns:
            True if switch successful, False otherwise
        """
        try:
            config = self.get_config()

            if name not in config.profiles:
                return False

            config.general.default_profile = name
            return self.save_config(config)

        except Exception:
            return False

    def update_profile(self, name: str, **kwargs: Any) -> bool:
        """Update profile settings.

        Args:
            name: Profile name
            **kwargs: Settings to update

        Returns:
            True if update successful, False otherwise
        """
        try:
            config = self.get_config()

            if name not in config.profiles:
                return False

            profile = config.profiles[name]

            # Update settings
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            return self.save_config(config)

        except Exception:
            return False

    def validate_config(self) -> List[str]:
        """Validate current configuration.

        Returns:
            List of validation error messages
        """
        errors = []

        try:
            config = self.get_config()

            # Check profiles
            if not config.profiles:
                errors.append("No profiles defined")
            else:
                # Check default profile exists
                if config.general.default_profile not in config.profiles:
                    errors.append(f"Default profile '{config.general.default_profile}' not found")

                # Validate each profile
                for name, profile in config.profiles.items():
                    profile_errors = self._validate_profile(name, profile)
                    errors.extend(profile_errors)

            # Check general settings
            if not config.general.registry_url:
                errors.append("Registry URL not configured")

        except Exception as e:
            errors.append(f"Configuration error: {e}")

        return errors

    def _validate_profile(self, name: str, profile: ProfileConfig) -> List[str]:
        """Validate profile configuration.

        Args:
            name: Profile name
            profile: Profile configuration

        Returns:
            List of validation errors
        """
        errors = []

        # Check target
        if profile.target not in VALID_TARGETS:
            errors.append(f"Profile {name}: Invalid target '{profile.target}'")

        # Check config path exists for specific targets
        if profile.target == "claude-code" and profile.config_path:
            config_path = Path(profile.config_path).expanduser()
            if not config_path.parent.exists():
                errors.append(f"Profile {name}: Config directory does not exist: {config_path.parent}")

        # Check Python path if specified
        if profile.python_path:
            python_path = Path(profile.python_path)
            if not python_path.exists():
                errors.append(f"Profile {name}: Python executable not found: {python_path}")

        return errors

    def _ensure_default_profile(self) -> None:
        """Ensure default profile exists."""
        if self._config and not self._config.profiles:
            default_profile = self._create_default_profile()
            self._config.profiles[DEFAULT_PROFILE_NAME] = default_profile

    def _create_default_profile(self) -> ProfileConfig:
        """Create default profile configuration.

        Returns:
            Default profile configuration
        """
        # Detect Claude Code installation
        claude_code_path = self._get_claude_code_config_path()

        return ProfileConfig(
            target="claude-code",
            config_path=str(claude_code_path),
            install_global=True,
            use_uv=True
        )

    def _get_claude_code_config_path(self) -> Path:
        """Get Claude Code configuration path for current platform.

        Returns:
            Path to Claude Code MCP configuration
        """
        system = platform.system()

        if os.getenv("MCPI_TESTING", None) is not None:
            return Path.home() / ".claude" / "settings.mcpi-test.json"

        # Use mapping for cleaner platform detection
        if system in CLAUDE_PATHS:
            path = CLAUDE_PATHS[system]
            # Handle Windows callable
            if callable(path):
                return path()
            return path

        # Fallback for unknown platforms
        return Path.home() / ".claude" / CLAUDE_CONFIG_FILENAME

    def _apply_template(self, config: MCPIConfig, template: str) -> None:
        """Apply configuration template.

        Args:
            config: Configuration to modify
            template: Template name
        """
        if template not in CONFIG_TEMPLATES:
            return

        template_config = CONFIG_TEMPLATES[template]

        # Apply general settings
        if "auto_update_registry" in template_config:
            config.general.auto_update_registry = template_config["auto_update_registry"]

        # Apply logging settings
        if "logging_level" in template_config:
            config.logging.level = template_config["logging_level"]

    def get_cache_directory(self) -> Path:
        """Get cache directory path.

        Returns:
            Path to cache directory
        """
        config = self.get_config()

        if config.general.cache_directory:
            return Path(config.general.cache_directory).expanduser()
        else:
            return Path(user_cache_dir("mcpi", "mcpi"))

    def backup_config(self, backup_path: Optional[Path] = None) -> Optional[Path]:
        """Create backup of current configuration.

        Args:
            backup_path: Path for backup file. If None, generates automatic name.

        Returns:
            Path to backup file or None if backup failed
        """
        if not self.config_path.exists():
            return None

        if backup_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.with_suffix(f".backup_{timestamp}")

        try:
            shutil.copy2(self.config_path, backup_path)
            return backup_path
        except Exception:
            return None

    def restore_config(self, backup_path: Path) -> bool:
        """Restore configuration from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if restore successful, False otherwise
        """
        if not backup_path.exists():
            return False

        try:
            shutil.copy2(backup_path, self.config_path)
            self._config = None  # Force reload
            return True
        except Exception:
            return False
    
    def get_active_profile(self) -> str:
        """Get the name of the currently active profile.
        
        Returns:
            Active profile name
        """
        config = self.get_config()
        return config.general.default_profile
    
    def add_server_config(self, server_id: str, server_config: Dict[str, Any]) -> bool:
        """Add a server configuration.
        
        Args:
            server_id: Server identifier
            server_config: Server configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # For now, store server configs in a simple way
            # This could be enhanced to store in profile-specific locations
            config = self.get_config()
            
            # Store server configs in a custom section
            if not hasattr(config, '_server_configs'):
                config._server_configs = {}
            
            config._server_configs[server_id] = server_config
            return self.save_config(config)
            
        except Exception:
            return False
    
    def get_server_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all server configurations.
        
        Returns:
            Dictionary of server configurations
        """
        try:
            config = self.get_config()
            
            # Return server configs if they exist
            if hasattr(config, '_server_configs'):
                return config._server_configs
            else:
                return {}
                
        except Exception:
            return {}
    
    def get_config_path(self) -> Path:
        """Get the configuration file path.
        
        Returns:
            Path to configuration file
        """
        return self.config_path
