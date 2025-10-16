"""Claude Code specific MCP server installer."""

import json
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any
from mcpi.installer.base import BaseInstaller, InstallationResult, InstallationStatus
from mcpi.installer.npm import NPMInstaller
from mcpi.installer.python import PythonInstaller
from mcpi.installer.git import GitInstaller
from mcpi.registry.catalog import MCPServer, InstallationMethod


# Configuration constants
MCP_SERVERS_KEY = "mcpServers"


class ClaudeCodeInstaller(BaseInstaller):
    """Installer for Claude Code MCP server integration."""
    
    def __init__(self, config_path: Optional[Path] = None, dry_run: bool = False):
        """Initialize Claude Code installer.
        
        Args:
            config_path: Path to Claude Code MCP configuration file
            dry_run: If True, simulate installation without making changes
        """
        if config_path is None:
            config_path = self._find_claude_code_config()
        
        super().__init__(config_path=config_path, dry_run=dry_run)
        
        # Initialize method-specific installers
        self.npm_installer = NPMInstaller(dry_run=dry_run)
        self.python_installer = PythonInstaller(dry_run=dry_run)
        self.git_installer = GitInstaller(dry_run=dry_run)
    
    def _find_claude_code_config(self) -> Path:
        """Find Claude Code MCP configuration file.
        
        Returns:
            Path to Claude Code MCP configuration file
        """
        system = platform.system()
        
        if system == "Darwin":  # macOS
            config_path = Path.home() / ".claude" / "mcp_servers.json"
        elif system == "Linux":
            config_path = Path.home() / ".config" / "claude" / "mcp_servers.json"
        elif system == "Windows":
            appdata = Path(os.environ.get("APPDATA", str(Path.home())))
            config_path = appdata / "claude" / "mcp_servers.json"
        else:
            # Fallback to home directory
            config_path = Path.home() / ".claude" / "mcp_servers.json"
        
        return config_path
    
    def _load_config(self) -> Dict[str, Any]:
        """Load Claude Code MCP configuration.
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            return {MCP_SERVERS_KEY: {}}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {MCP_SERVERS_KEY: {}}
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save Claude Code MCP configuration.
        
        Args:
            config: Configuration to save
            
        Returns:
            True if save successful, False otherwise
        """
        if self.dry_run:
            return True
        
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except (IOError, OSError):
            return False
    
    def install(self, server: MCPServer, config_params: Optional[Dict[str, Any]] = None) -> InstallationResult:
        """Install MCP server for Claude Code.
        
        Args:
            server: MCP server to install
            config_params: Configuration parameters
            
        Returns:
            Installation result
        """
        if config_params is None:
            config_params = {}
        
        # Validate installation requirements
        validation_errors = self.validate_installation(server)
        if validation_errors:
            return self._create_failure_result(
                server.id,
                f"Validation failed: {'; '.join(validation_errors)}",
                validation_errors=validation_errors
            )
        
        # Check if already installed
        if self.is_installed(server.id):
            return self._create_failure_result(
                server.id,
                f"Server {server.id} is already installed",
                already_installed=True
            )
        
        # Install the server package using appropriate method
        package_result = self._install_package(server)
        if not package_result.success:
            return package_result
        
        # Create backup of existing configuration
        backup_path = self.create_backup(self.config_path)
        
        # Load current configuration
        config = self._load_config()
        
        # Generate server configuration
        server_config = self._generate_server_config(server, config_params, package_result.details)
        
        # Add server to configuration
        config[MCP_SERVERS_KEY][server.id] = server_config
        
        # Save updated configuration
        if not self._save_config(config):
            return self._create_failure_result(
                server.id,
                "Failed to save Claude Code configuration",
                backup_path=backup_path
            )
        
        return self._create_success_result(
            server.id,
            f"Successfully installed {server.name} for Claude Code",
            config_path=self.config_path,
            backup_path=backup_path,
            server_config=server_config,
            package_details=package_result.details
        )
    
    def _install_package(self, server: MCPServer) -> InstallationResult:
        """Install the server package using appropriate method.
        
        Args:
            server: Server to install
            
        Returns:
            Installation result
        """
        if server.installation.method == InstallationMethod.NPM:
            return self.npm_installer.install(server)
        elif server.installation.method == InstallationMethod.PIP:
            return self.python_installer.install(server)
        elif server.installation.method == InstallationMethod.GIT:
            return self.git_installer.install(server)
        else:
            return self._create_failure_result(
                server.id,
                f"Unsupported installation method: {server.installation.method}"
            )
    
    def _generate_server_config(
        self, 
        server: MCPServer, 
        config_params: Dict[str, Any],
        package_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate Claude Code server configuration.
        
        Args:
            server: MCP server
            config_params: User-provided configuration parameters
            package_details: Details from package installation
            
        Returns:
            Claude Code server configuration
        """
        if package_details is None:
            package_details = {}
        
        config = {}
        
        if server.installation.method == InstallationMethod.NPM:
            config["command"] = "npx"
            config["args"] = [server.installation.package]
        elif server.installation.method == InstallationMethod.PIP:
            # For Python packages, we need to determine the executable path
            python_path = package_details.get("python_path", "python3")
            module_path = package_details.get("module_path", server.installation.package)
            config["command"] = python_path
            config["args"] = ["-m", module_path]
        elif server.installation.method == InstallationMethod.GIT:
            # For Git installations, use the installed script
            script_path = package_details.get("script_path")
            if script_path:
                config["command"] = str(script_path)
                config["args"] = []
            else:
                config["command"] = "python3"
                config["args"] = [str(package_details.get("install_path", ""))]
        
        # Add configuration parameters as arguments
        for param in server.configuration.required_params:
            if param in config_params:
                config["args"].append(str(config_params[param]))
            else:
                # Use default values or prompt user
                default_value = self._get_default_param_value(param)
                if default_value:
                    config["args"].append(default_value)
        
        # Add optional parameters
        for param in server.configuration.optional_params:
            if param in config_params:
                config["args"].extend([f"--{param}", str(config_params[param])])
        
        # Add environment variables if needed
        if "env" in config_params:
            config["env"] = config_params["env"]
        
        return config
    
    def _get_default_param_value(self, param: str) -> Optional[str]:
        """Get default value for a configuration parameter.
        
        Args:
            param: Parameter name
            
        Returns:
            Default value or None
        """
        defaults = {
            "root_path": str(Path.home()),
            "database_path": "./database.db",
            "repository_path": ".",
        }
        return defaults.get(param)
    
    def uninstall(self, server_id: str) -> InstallationResult:
        """Uninstall MCP server from Claude Code.
        
        Args:
            server_id: ID of server to uninstall
            
        Returns:
            Installation result
        """
        if not self.is_installed(server_id):
            return self._create_failure_result(
                server_id,
                f"Server {server_id} is not installed"
            )
        
        # Create backup
        backup_path = self.create_backup(self.config_path)
        
        # Load configuration
        config = self._load_config()
        
        # Remove server from configuration
        if server_id in config.get(MCP_SERVERS_KEY, {}):
            del config[MCP_SERVERS_KEY][server_id]
        
        # Save updated configuration
        if not self._save_config(config):
            return self._create_failure_result(
                server_id,
                "Failed to save Claude Code configuration",
                backup_path=backup_path
            )
        
        return self._create_success_result(
            server_id,
            f"Successfully uninstalled {server_id} from Claude Code",
            config_path=self.config_path,
            backup_path=backup_path
        )
    
    def is_installed(self, server_id: str) -> bool:
        """Check if server is installed in Claude Code.
        
        Args:
            server_id: Server ID to check
            
        Returns:
            True if installed, False otherwise
        """
        config = self._load_config()
        return server_id in config.get(MCP_SERVERS_KEY, {})
    
    def get_installed_servers(self) -> List[str]:
        """Get list of installed server IDs.
        
        Returns:
            List of installed server IDs
        """
        config = self._load_config()
        return list(config.get(MCP_SERVERS_KEY, {}).keys())
    
    def get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for installed server.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server configuration or None if not found
        """
        config = self._load_config()
        return config.get(MCP_SERVERS_KEY, {}).get(server_id)
    
    def update_server_config(self, server_id: str, new_config: Dict[str, Any]) -> bool:
        """Update configuration for installed server.
        
        Args:
            server_id: Server ID
            new_config: New configuration
            
        Returns:
            True if update successful, False otherwise
        """
        if not self.is_installed(server_id):
            return False
        
        config = self._load_config()
        config[MCP_SERVERS_KEY][server_id] = new_config
        
        return self._save_config(config)
    
    def validate_config(self) -> List[str]:
        """Validate Claude Code MCP configuration.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        if not self.config_path.exists():
            errors.append(f"Configuration file does not exist: {self.config_path}")
            return errors
        
        config = self._load_config()
        
        if MCP_SERVERS_KEY not in config:
            errors.append(f"Configuration missing '{MCP_SERVERS_KEY}' section")
            return errors
        
        for server_id, server_config in config[MCP_SERVERS_KEY].items():
            if not isinstance(server_config, dict):
                errors.append(f"Server {server_id}: Configuration must be an object")
                continue
            
            if "command" not in server_config:
                errors.append(f"Server {server_id}: Missing 'command' field")
            
            if "args" not in server_config:
                errors.append(f"Server {server_id}: Missing 'args' field")
            elif not isinstance(server_config["args"], list):
                errors.append(f"Server {server_id}: 'args' must be an array")
        
        return errors
    
    def _supports_method(self, method: str) -> bool:
        """Check if installer supports the given method.
        
        Args:
            method: Installation method
            
        Returns:
            True if supported, False otherwise
        """
        return method in [InstallationMethod.NPM, InstallationMethod.PIP, InstallationMethod.GIT]