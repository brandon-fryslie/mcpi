"""Protocol definitions for type-safe interfaces."""

from typing import Protocol, runtime_checkable, Dict, Any, List
from pathlib import Path


@runtime_checkable
class ConfigReader(Protocol):
    """Protocol for configuration readers."""
    
    def read(self, source: Path) -> Dict[str, Any]:
        """Read configuration from source.
        
        Args:
            source: Path to configuration source
            
        Returns:
            Configuration data
            
        Raises:
            ValueError: If source cannot be read
        """
        ...


@runtime_checkable
class ConfigWriter(Protocol):
    """Protocol for configuration writers."""
    
    def write(self, target: Path, data: Dict[str, Any]) -> bool:
        """Write configuration to target.
        
        Args:
            target: Path to configuration target
            data: Configuration data to write
            
        Returns:
            True if write successful, False otherwise
            
        Raises:
            ValueError: If target cannot be written
        """
        ...


@runtime_checkable
class SchemaValidator(Protocol):
    """Protocol for schema validators."""
    
    def validate(self, data: Dict[str, Any], schema_path: Path) -> bool:
        """Validate data against schema.
        
        Args:
            data: Data to validate
            schema_path: Path to schema file
            
        Returns:
            True if validation passes, False otherwise
        """
        ...
    
    def get_errors(self) -> List[str]:
        """Get validation errors from last validation attempt.
        
        Returns:
            List of error messages
        """
        ...


@runtime_checkable
class CommandExecutor(Protocol):
    """Protocol for executing commands."""
    
    def execute(self, command: str, args: List[str]) -> Dict[str, Any]:
        """Execute command with arguments.
        
        Args:
            command: Command to execute
            args: Command arguments
            
        Returns:
            Command result data
            
        Raises:
            ValueError: If command execution fails
        """
        ...


@runtime_checkable
class APIClient(Protocol):
    """Protocol for API-based configuration clients."""
    
    def get(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make GET request to API endpoint.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            API response data
        """
        ...
    
    def post(self, endpoint: str, data: Dict[str, Any], **kwargs: Any) -> bool:
        """Make POST request to API endpoint.
        
        Args:
            endpoint: API endpoint path
            data: Data to send in request
            **kwargs: Additional request parameters
            
        Returns:
            True if request successful, False otherwise
        """
        ...
    
    def delete(self, endpoint: str, **kwargs: Any) -> bool:
        """Make DELETE request to API endpoint.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            True if request successful, False otherwise
        """
        ...