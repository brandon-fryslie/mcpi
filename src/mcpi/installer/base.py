"""Base installer interface and common utilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from mcpi.registry.catalog import MCPServer


class InstallationStatus(str, Enum):
    """Installation status enumeration."""
    SUCCESS = "success"
    FAILED = "failed" 
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class InstallationResult:
    """Result of an installation operation."""
    status: InstallationStatus
    message: str
    server_id: str
    config_path: Optional[Path] = None
    backup_path: Optional[Path] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Initialize details if not provided."""
        if self.details is None:
            self.details = {}
    
    @property
    def success(self) -> bool:
        """Check if installation was successful."""
        return self.status == InstallationStatus.SUCCESS
    
    @property
    def failed(self) -> bool:
        """Check if installation failed."""
        return self.status == InstallationStatus.FAILED


class BaseInstaller(ABC):
    """Base class for MCP server installers."""
    
    def __init__(self, config_path: Optional[Path] = None, dry_run: bool = False):
        """Initialize the installer.
        
        Args:
            config_path: Path to configuration file
            dry_run: If True, simulate installation without making changes
        """
        self.config_path = config_path
        self.dry_run = dry_run
        self._backup_paths: List[Path] = []
    
    @abstractmethod
    def install(self, server: MCPServer, config_params: Optional[Dict[str, Any]] = None) -> InstallationResult:
        """Install an MCP server.
        
        Args:
            server: MCP server to install
            config_params: Configuration parameters
            
        Returns:
            Installation result
        """
        pass
    
    @abstractmethod
    def uninstall(self, server_id: str) -> InstallationResult:
        """Uninstall an MCP server.
        
        Args:
            server_id: ID of server to uninstall
            
        Returns:
            Installation result
        """
        pass
    
    @abstractmethod
    def is_installed(self, server_id: str) -> bool:
        """Check if server is installed.
        
        Args:
            server_id: Server ID to check
            
        Returns:
            True if installed, False otherwise
        """
        pass
    
    @abstractmethod
    def get_installed_servers(self) -> List[str]:
        """Get list of installed server IDs.
        
        Returns:
            List of installed server IDs
        """
        pass
    
    def validate_installation(self, server: MCPServer) -> List[str]:
        """Validate installation requirements.
        
        Args:
            server: Server to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check system dependencies
        for dep in server.installation.system_dependencies:
            if not self._check_system_dependency(dep):
                errors.append(f"Missing system dependency: {dep}")
        
        # Check if installer can handle this installation method
        if not self._supports_method(server.installation.method):
            errors.append(f"Installation method not supported: {server.installation.method}")
        
        return errors
    
    def _check_system_dependency(self, dependency: str) -> bool:
        """Check if system dependency is available.
        
        Args:
            dependency: System dependency to check
            
        Returns:
            True if available, False otherwise
        """
        import shutil
        return shutil.which(dependency) is not None
    
    @abstractmethod
    def _supports_method(self, method: str) -> bool:
        """Check if installer supports the given method.
        
        Args:
            method: Installation method
            
        Returns:
            True if supported, False otherwise
        """
        pass
    
    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of configuration file.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file or None if backup failed
        """
        if not file_path.exists():
            return None
        
        import datetime
        import shutil
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup_{timestamp}")
        
        try:
            shutil.copy2(file_path, backup_path)
            self._backup_paths.append(backup_path)
            return backup_path
        except Exception:
            return None
    
    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restore from backup.
        
        Args:
            backup_path: Path to backup file
            target_path: Path to restore to
            
        Returns:
            True if restore successful, False otherwise
        """
        if not backup_path.exists():
            return False
        
        try:
            import shutil
            shutil.copy2(backup_path, target_path)
            return True
        except Exception:
            return False
    
    def cleanup_backups(self) -> None:
        """Clean up created backup files."""
        for backup_path in self._backup_paths:
            try:
                if backup_path.exists():
                    backup_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors
        self._backup_paths.clear()
    
    def _create_success_result(
        self, 
        server_id: str, 
        message: str, 
        config_path: Optional[Path] = None,
        **details: Any
    ) -> InstallationResult:
        """Create a success result.
        
        Args:
            server_id: Server ID
            message: Success message
            config_path: Path to configuration file
            **details: Additional details
            
        Returns:
            Success installation result
        """
        return InstallationResult(
            status=InstallationStatus.SUCCESS,
            message=message,
            server_id=server_id,
            config_path=config_path,
            details=details
        )
    
    def _create_failure_result(
        self, 
        server_id: str, 
        message: str, 
        **details: Any
    ) -> InstallationResult:
        """Create a failure result.
        
        Args:
            server_id: Server ID
            message: Error message
            **details: Additional details
            
        Returns:
            Failure installation result
        """
        return InstallationResult(
            status=InstallationStatus.FAILED,
            message=message,
            server_id=server_id,
            details=details
        )