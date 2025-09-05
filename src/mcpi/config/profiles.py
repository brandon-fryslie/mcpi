"""Profile management utilities."""

from typing import Dict, List, Optional, Any
from pathlib import Path
from mcpi.config.manager import ConfigManager, ProfileConfig


class ProfileManager:
    """Manages configuration profiles for different environments and tools."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize profile manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
    
    def create_claude_code_profile(self, name: str, config_path: Optional[str] = None) -> bool:
        """Create a profile for Claude Code integration.
        
        Args:
            name: Profile name
            config_path: Path to Claude Code config file (optional)
            
        Returns:
            True if creation successful, False otherwise
        """
        profile_config = {
            "target": "claude-code",
            "install_global": True,
            "use_uv": True
        }
        
        if config_path:
            profile_config["config_path"] = config_path
        
        return self.config_manager.create_profile(name, **profile_config)
    
    def create_development_profile(self, name: str, project_path: str) -> bool:
        """Create a profile for development environment.
        
        Args:
            name: Profile name
            project_path: Path to development project
            
        Returns:
            True if creation successful, False otherwise
        """
        config_path = str(Path(project_path) / "mcp_servers.json")
        
        return self.config_manager.create_profile(
            name,
            target="generic",
            config_path=config_path,
            install_global=False,
            use_uv=True
        )
    
    def create_production_profile(self, name: str, config_path: str) -> bool:
        """Create a profile for production environment.
        
        Args:
            name: Profile name
            config_path: Path to production config file
            
        Returns:
            True if creation successful, False otherwise
        """
        return self.config_manager.create_profile(
            name,
            target="generic",
            config_path=config_path,
            install_global=True,
            use_uv=False  # Use pip for production stability
        )
    
    def clone_profile(self, source: str, target: str, modifications: Optional[Dict[str, Any]] = None) -> bool:
        """Clone an existing profile with optional modifications.
        
        Args:
            source: Source profile name
            target: Target profile name
            modifications: Optional modifications to apply
            
        Returns:
            True if cloning successful, False otherwise
        """
        try:
            config = self.config_manager.get_config()
            
            if source not in config.profiles:
                return False
            
            if target in config.profiles:
                return False  # Target already exists
            
            # Clone source profile
            source_profile = config.profiles[source]
            target_profile_data = source_profile.model_dump()
            
            # Apply modifications
            if modifications:
                target_profile_data.update(modifications)
            
            # Create new profile
            target_profile = ProfileConfig(**target_profile_data)
            config.profiles[target] = target_profile
            
            return self.config_manager.save_config(config)
            
        except Exception:
            return False
    
    def export_profile(self, name: str, export_path: Path) -> bool:
        """Export profile to file.
        
        Args:
            name: Profile name to export
            export_path: Path to export file
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            config = self.config_manager.get_config()
            
            if name not in config.profiles:
                return False
            
            profile = config.profiles[name]
            profile_data = {
                "profile_name": name,
                "profile_config": profile.model_dump()
            }
            
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            
            return True
            
        except Exception:
            return False
    
    def import_profile(self, import_path: Path, name: Optional[str] = None) -> bool:
        """Import profile from file.
        
        Args:
            import_path: Path to import file
            name: Optional name for imported profile (overrides file name)
            
        Returns:
            True if import successful, False otherwise
        """
        try:
            if not import_path.exists():
                return False
            
            import json
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile_name = name or data.get("profile_name", "imported")
            profile_config_data = data.get("profile_config", {})
            
            # Validate profile configuration
            profile_config = ProfileConfig(**profile_config_data)
            
            # Add to configuration
            config = self.config_manager.get_config()
            config.profiles[profile_name] = profile_config
            
            return self.config_manager.save_config(config)
            
        except Exception:
            return False
    
    def get_profile_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a profile.
        
        Args:
            name: Profile name
            
        Returns:
            Profile summary or None if not found
        """
        try:
            profile = self.config_manager.get_profile(name)
            
            return {
                "name": name,
                "target": profile.target,
                "config_path": profile.config_path,
                "install_global": profile.install_global,
                "use_uv": profile.use_uv,
                "python_path": profile.python_path
            }
            
        except ValueError:
            return None
    
    def list_profiles_detailed(self) -> List[Dict[str, Any]]:
        """Get detailed information about all profiles.
        
        Returns:
            List of profile summaries
        """
        profiles = []
        
        for name in self.config_manager.list_profiles():
            summary = self.get_profile_summary(name)
            if summary:
                # Add status information
                summary["is_default"] = (
                    name == self.config_manager.get_config().general.default_profile
                )
                
                # Check if config path exists
                if summary["config_path"]:
                    config_path = Path(summary["config_path"]).expanduser()
                    summary["config_exists"] = config_path.exists()
                else:
                    summary["config_exists"] = None
                
                profiles.append(summary)
        
        return profiles
    
    def validate_all_profiles(self) -> Dict[str, List[str]]:
        """Validate all profiles and return errors by profile name.
        
        Returns:
            Dictionary mapping profile names to lists of error messages
        """
        config = self.config_manager.get_config()
        validation_results = {}
        
        for name, profile in config.profiles.items():
            errors = self.config_manager._validate_profile(name, profile)
            if errors:
                validation_results[name] = errors
        
        return validation_results
    
    def suggest_profile_name(self, base_name: str) -> str:
        """Suggest an available profile name based on base name.
        
        Args:
            base_name: Base name to use
            
        Returns:
            Available profile name
        """
        existing_names = set(self.config_manager.list_profiles())
        
        if base_name not in existing_names:
            return base_name
        
        # Try numbered variations
        counter = 1
        while True:
            candidate = f"{base_name}_{counter}"
            if candidate not in existing_names:
                return candidate
            counter += 1
    
    def get_compatible_profiles(self, target: str) -> List[str]:
        """Get profiles compatible with a specific target.
        
        Args:
            target: Target type (e.g., 'claude-code', 'generic')
            
        Returns:
            List of compatible profile names
        """
        compatible = []
        config = self.config_manager.get_config()
        
        for name, profile in config.profiles.items():
            if profile.target == target:
                compatible.append(name)
        
        return compatible
    
    def migrate_profile(self, name: str, new_target: str, **kwargs: Any) -> bool:
        """Migrate a profile to a different target.
        
        Args:
            name: Profile name to migrate
            new_target: New target type
            **kwargs: Additional configuration changes
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            config = self.config_manager.get_config()
            
            if name not in config.profiles:
                return False
            
            profile = config.profiles[name]
            
            # Update target
            profile.target = new_target
            
            # Apply target-specific defaults
            if new_target == "claude-code":
                if not profile.config_path:
                    profile.config_path = str(self.config_manager._get_claude_code_config_path())
            
            # Apply additional changes
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            return self.config_manager.save_config(config)
            
        except Exception:
            return False