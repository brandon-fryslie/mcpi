"""Registry validation utilities."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from pydantic import ValidationError
from mcpi.registry.catalog import MCPServer


class RegistryValidator:
    """Validates MCP server registry data."""
    
    def __init__(self):
        """Initialize the validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_registry_file(self, registry_path: Path) -> bool:
        """Validate a registry file.
        
        Args:
            registry_path: Path to registry JSON file
            
        Returns:
            True if valid, False otherwise
        """
        self.errors.clear()
        self.warnings.clear()
        
        if not registry_path.exists():
            self.errors.append(f"Registry file does not exist: {registry_path}")
            return False
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON format: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading registry file: {e}")
            return False
        
        return self.validate_registry_data(data)
    
    def validate_registry_data(self, data: Dict[str, Any]) -> bool:
        """Validate registry data structure.
        
        Args:
            data: Registry data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check top-level structure
        if not isinstance(data, dict):
            self.errors.append("Registry must be a JSON object")
            return False
        
        if 'servers' not in data:
            self.errors.append("Registry must contain 'servers' array")
            return False
        
        if not isinstance(data['servers'], list):
            self.errors.append("'servers' must be an array")
            return False
        
        # Validate version if present
        if 'version' in data and not isinstance(data['version'], str):
            self.warnings.append("Registry version should be a string")
        
        # Validate servers
        return self.validate_servers(data['servers'])
    
    def validate_servers(self, servers_data: List[Dict[str, Any]]) -> bool:
        """Validate servers array.
        
        Args:
            servers_data: List of server data dictionaries
            
        Returns:
            True if valid, False otherwise
        """
        if not servers_data:
            self.warnings.append("Registry contains no servers")
            return True
        
        server_ids: Set[str] = set()
        valid = True
        
        for i, server_data in enumerate(servers_data):
            if not self.validate_single_server(server_data, i):
                valid = False
                continue
            
            # Check for duplicate IDs
            server_id = server_data.get('id')
            if server_id in server_ids:
                self.errors.append(f"Duplicate server ID: {server_id}")
                valid = False
            else:
                server_ids.add(server_id)
        
        return valid
    
    def validate_single_server(self, server_data: Dict[str, Any], index: int) -> bool:
        """Validate a single server entry.
        
        Args:
            server_data: Server data dictionary
            index: Server index in array (for error reporting)
            
        Returns:
            True if valid, False otherwise
        """
        try:
            server = MCPServer(**server_data)
            
            # Additional semantic validation
            self._validate_server_semantics(server, index)
            
            return True
            
        except ValidationError as e:
            self.errors.append(f"Server {index}: Validation error - {e}")
            return False
        except Exception as e:
            self.errors.append(f"Server {index}: Unexpected error - {e}")
            return False
    
    def _validate_server_semantics(self, server: MCPServer, index: int) -> None:
        """Perform semantic validation on a server.
        
        Args:
            server: Validated MCPServer instance
            index: Server index for error reporting
        """
        server_ref = f"Server {index} ({server.id})"
        
        # Check that version info is consistent
        if server.versions.latest not in server.versions.supported:
            self.warnings.append(f"{server_ref}: Latest version not in supported versions")
        
        # Check that installation method matches package format
        if server.installation.method == "npm" and not server.installation.package.startswith(('@', 'npm:')):
            # NPM packages often start with @ or are simple names
            pass  # This is actually fine, many npm packages don't start with @
        
        if server.installation.method == "pip" and server.installation.package.startswith('@'):
            self.warnings.append(f"{server_ref}: PIP package should not start with '@'")
        
        # Check that required configuration parameters are reasonable
        if len(server.configuration.required_params) > 10:
            self.warnings.append(f"{server_ref}: Many required parameters ({len(server.configuration.required_params)})")
        
        # Check that categories are reasonable
        if len(server.category) > 5:
            self.warnings.append(f"{server_ref}: Many categories ({len(server.category)})")
        
        if not server.category:
            self.warnings.append(f"{server_ref}: No categories specified")
        
        # Check capabilities
        if len(server.capabilities) > 20:
            self.warnings.append(f"{server_ref}: Many capabilities ({len(server.capabilities)})")
        
        # Check platform support
        if not server.platforms:
            self.warnings.append(f"{server_ref}: No platforms specified")
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report.
        
        Returns:
            Dictionary containing validation results
        """
        return {
            "valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy()
        }
    
    def print_validation_report(self) -> None:
        """Print validation report to console."""
        if not self.errors and not self.warnings:
            print("✅ Registry validation passed with no issues")
            return
        
        if self.errors:
            print(f"❌ Registry validation failed with {len(self.errors)} errors:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"⚠️  Registry validation has {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors:
            print("✅ Registry is valid despite warnings")
    
    @classmethod
    def validate_server_dict(cls, server_data: Dict[str, Any]) -> bool:
        """Quick validation of a server dictionary.
        
        Args:
            server_data: Server data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            MCPServer(**server_data)
            return True
        except (ValidationError, TypeError, ValueError):
            return False
    
    @classmethod
    def get_server_validation_errors(cls, server_data: Dict[str, Any]) -> List[str]:
        """Get validation errors for a server dictionary.
        
        Args:
            server_data: Server data dictionary
            
        Returns:
            List of error messages
        """
        try:
            MCPServer(**server_data)
            return []
        except ValidationError as e:
            return [str(error) for error in e.errors()]
        except Exception as e:
            return [str(e)]