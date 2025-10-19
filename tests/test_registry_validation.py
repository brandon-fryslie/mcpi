"""Comprehensive tests for the registry validation module."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from typing import Dict, Any, List

from pydantic import ValidationError

from mcpi.registry.validation import RegistryValidator
from mcpi.registry.catalog import MCPServer, ServerVersions, ServerInstallation, ServerConfiguration


class TestRegistryValidator:
    """Tests for RegistryValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = RegistryValidator()
    
    def test_init(self):
        """Test validator initialization."""
        validator = RegistryValidator()
        assert validator.errors == []
        assert validator.warnings == []
    
    # File validation tests
    def test_validate_registry_file_nonexistent(self, tmp_path):
        """Test validation of non-existent registry file."""
        nonexistent_path = tmp_path / "nonexistent.json"
        result = self.validator.validate_registry_file(nonexistent_path)
        
        assert result is False
        assert len(self.validator.errors) == 1
        assert "Registry file does not exist" in self.validator.errors[0]
        assert len(self.validator.warnings) == 0
    
    def test_validate_registry_file_invalid_json(self, tmp_path):
        """Test validation of invalid JSON file."""
        invalid_json_path = tmp_path / "invalid.json"
        invalid_json_path.write_text("{ invalid json }")
        
        result = self.validator.validate_registry_file(invalid_json_path)
        
        assert result is False
        assert len(self.validator.errors) == 1
        assert "Invalid JSON format" in self.validator.errors[0]
    
    def test_validate_registry_file_read_error(self, tmp_path):
        """Test validation when file read error occurs."""
        registry_path = tmp_path / "registry.json"
        
        # Create the file first so it exists
        registry_path.write_text('{"servers": []}')
        
        # Mock the open function to raise a permission error during reading
        with patch('mcpi.registry.validation.open', mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")
            
            result = self.validator.validate_registry_file(registry_path)
            
            assert result is False
            assert len(self.validator.errors) == 1
            assert "Error reading registry file" in self.validator.errors[0]
    
    def test_validate_registry_file_valid(self, tmp_path):
        """Test validation of valid registry file."""
        registry_path = tmp_path / "registry.json"
        valid_data = {
            "servers": [
                {
                    "id": "test-server",
                    "name": "Test Server",
                    "description": "Test description",
                    "category": ["test"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "test-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["test_operations"],
                    "platforms": ["linux", "darwin", "windows"],
                    "license": "MIT"
                }
            ]
        }
        
        registry_path.write_text(json.dumps(valid_data))
        
        result = self.validator.validate_registry_file(registry_path)
        
        assert result is True
        assert len(self.validator.errors) == 0
    
    def test_validate_registry_file_clears_previous_results(self, tmp_path):
        """Test that file validation clears previous errors and warnings."""
        # Add some initial errors and warnings
        self.validator.errors.append("Previous error")
        self.validator.warnings.append("Previous warning")
        
        registry_path = tmp_path / "registry.json"
        valid_data = {"servers": []}
        registry_path.write_text(json.dumps(valid_data))
        
        result = self.validator.validate_registry_file(registry_path)
        
        assert result is True
        assert len(self.validator.errors) == 0
        assert len(self.validator.warnings) == 1  # Only the empty servers warning
        assert "Previous error" not in self.validator.errors
        assert "Previous warning" not in self.validator.warnings
    
    # Data structure validation tests
    def test_validate_registry_data_not_dict(self):
        """Test validation when data is not a dictionary."""
        result = self.validator.validate_registry_data("not a dict")
        
        assert result is False
        assert len(self.validator.errors) == 1
        assert "Registry must be a JSON object" in self.validator.errors[0]
    
    def test_validate_registry_data_no_servers(self):
        """Test validation when servers key is missing."""
        data = {"version": "1.0.0"}
        result = self.validator.validate_registry_data(data)
        
        assert result is False
        assert len(self.validator.errors) == 1
        assert "Registry must contain 'servers' array" in self.validator.errors[0]
    
    def test_validate_registry_data_servers_not_list(self):
        """Test validation when servers is not a list."""
        data = {"servers": "not a list"}
        result = self.validator.validate_registry_data(data)
        
        assert result is False
        assert len(self.validator.errors) == 1
        assert "'servers' must be an array" in self.validator.errors[0]
    
    def test_validate_registry_data_version_not_string(self):
        """Test validation when version is not a string."""
        data = {"servers": [], "version": 123}
        result = self.validator.validate_registry_data(data)
        
        assert result is True  # Should still validate successfully
        assert len(self.validator.warnings) == 2  # Empty servers + version warning
        assert any("Registry version should be a string" in w for w in self.validator.warnings)
    
    def test_validate_registry_data_valid_with_version(self):
        """Test validation with valid data including version."""
        data = {"servers": [], "version": "1.0.0"}
        result = self.validator.validate_registry_data(data)
        
        assert result is True
        assert len(self.validator.errors) == 0
        assert len(self.validator.warnings) == 1  # Only empty servers warning
    
    # Server array validation tests
    def test_validate_servers_empty_array(self):
        """Test validation of empty servers array."""
        result = self.validator.validate_servers([])
        
        assert result is True
        assert len(self.validator.errors) == 0
        assert len(self.validator.warnings) == 1
        assert "Registry contains no servers" in self.validator.warnings[0]
    
    def test_validate_servers_duplicate_ids(self):
        """Test validation with duplicate server IDs."""
        servers_data = [
            {
                "id": "duplicate-server",
                "name": "Server 1",
                "description": "First server",
                "category": ["test"],
                "author": "Test Author",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "npm", "package": "server1"},
                "configuration": {"required_params": [], "optional_params": []},
                "capabilities": ["operations"],
                "platforms": ["linux"],
                "license": "MIT"
            },
            {
                "id": "duplicate-server",  # Duplicate ID
                "name": "Server 2",
                "description": "Second server",
                "category": ["test"],
                "author": "Test Author",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "npm", "package": "server2"},
                "configuration": {"required_params": [], "optional_params": []},
                "capabilities": ["operations"],
                "platforms": ["linux"],
                "license": "MIT"
            }
        ]
        
        result = self.validator.validate_servers(servers_data)
        
        assert result is False
        assert len(self.validator.errors) >= 1
        assert any("Duplicate server ID: duplicate-server" in error for error in self.validator.errors)
    
    def test_validate_servers_valid_unique_ids(self):
        """Test validation with valid servers having unique IDs."""
        servers_data = [
            {
                "id": "server1",
                "name": "Server 1",
                "description": "First server",
                "category": ["test"],
                "author": "Test Author",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "npm", "package": "server1"},
                "configuration": {"required_params": [], "optional_params": []},
                "capabilities": ["operations"],
                "platforms": ["linux"],
                "license": "MIT"
            },
            {
                "id": "server2",
                "name": "Server 2",
                "description": "Second server",
                "category": ["test"],
                "author": "Test Author",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "npm", "package": "server2"},
                "configuration": {"required_params": [], "optional_params": []},
                "capabilities": ["operations"],
                "platforms": ["linux"],
                "license": "MIT"
            }
        ]
        
        result = self.validator.validate_servers(servers_data)
        
        assert result is True
        assert len(self.validator.errors) == 0
    
    # Single server validation tests
    def test_validate_single_server_valid(self):
        """Test validation of a single valid server."""
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux", "darwin", "windows"],
            "license": "MIT"
        }
        
        result = self.validator.validate_single_server(server_data, 0)
        
        assert result is True
        assert len(self.validator.errors) == 0
    
    def test_validate_single_server_pydantic_validation_error(self):
        """Test single server validation with Pydantic validation error."""
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "invalid-version", "supported": ["1.0.0"]},  # Invalid version
            "installation": {"method": "invalid-method", "package": "test-server"},  # Invalid method
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["invalid-platform"],  # Invalid platform
            "license": "MIT"
        }
        
        result = self.validator.validate_single_server(server_data, 0)
        
        assert result is False
        assert len(self.validator.errors) == 1
        assert "Server 0: Validation error" in self.validator.errors[0]
    
    def test_validate_single_server_unexpected_error(self):
        """Test single server validation with unexpected error."""
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        # Mock MCPServer to raise an unexpected error
        with patch('mcpi.registry.validation.MCPServer') as mock_mcpserver:
            mock_mcpserver.side_effect = RuntimeError("Unexpected error")
            
            result = self.validator.validate_single_server(server_data, 1)
            
            assert result is False
            assert len(self.validator.errors) == 1
            assert "Server 1: Unexpected error" in self.validator.errors[0]
    
    # Semantic validation tests
    def test_validate_server_semantics_latest_not_in_supported(self):
        """Test semantic validation when latest version is not in supported versions."""
        server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test description",
            category=["test"],
            author="Test Author",
            versions=ServerVersions(latest="2.0.0", supported=["1.0.0", "1.1.0"]),
            installation=ServerInstallation(method="npm", package="test-server"),
            configuration=ServerConfiguration(),
            capabilities=["operations"],
            platforms=["linux"],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server, 0)
        
        assert len(self.validator.warnings) == 1
        assert "Latest version not in supported versions" in self.validator.warnings[0]
    
    def test_validate_server_semantics_pip_package_with_at_symbol(self):
        """Test semantic validation for PIP package starting with @."""
        server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test description",
            category=["test"],
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            installation=ServerInstallation(method="pip", package="@invalid/package"),
            configuration=ServerConfiguration(),
            capabilities=["operations"],
            platforms=["linux"],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server, 0)
        
        assert len(self.validator.warnings) == 1
        assert "PIP package should not start with '@'" in self.validator.warnings[0]
    
    def test_validate_server_semantics_many_required_params(self):
        """Test semantic validation for many required parameters."""
        server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test description",
            category=["test"],
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            installation=ServerInstallation(method="npm", package="test-server"),
            configuration=ServerConfiguration(required_params=[f"param{i}" for i in range(15)]),
            capabilities=["operations"],
            platforms=["linux"],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server, 0)
        
        assert len(self.validator.warnings) == 1
        assert "Many required parameters (15)" in self.validator.warnings[0]
    
    def test_validate_server_semantics_many_categories(self):
        """Test semantic validation for many categories."""
        server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test description",
            category=["cat1", "cat2", "cat3", "cat4", "cat5", "cat6", "cat7"],
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            installation=ServerInstallation(method="npm", package="test-server"),
            configuration=ServerConfiguration(),
            capabilities=["operations"],
            platforms=["linux"],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server, 0)
        
        assert len(self.validator.warnings) == 1
        assert "Many categories (7)" in self.validator.warnings[0]
    
    def test_validate_server_semantics_no_categories(self):
        """Test semantic validation for no categories."""
        server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test description",
            category=[],
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            installation=ServerInstallation(method="npm", package="test-server"),
            configuration=ServerConfiguration(),
            capabilities=["operations"],
            platforms=["linux"],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server, 0)
        
        assert len(self.validator.warnings) == 1
        assert "No categories specified" in self.validator.warnings[0]
    
    def test_validate_server_semantics_many_capabilities(self):
        """Test semantic validation for many capabilities."""
        capabilities = [f"capability{i}" for i in range(25)]
        server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test description",
            category=["test"],
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            installation=ServerInstallation(method="npm", package="test-server"),
            configuration=ServerConfiguration(),
            capabilities=capabilities,
            platforms=["linux"],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server, 0)
        
        assert len(self.validator.warnings) == 1
        assert "Many capabilities (25)" in self.validator.warnings[0]
    
    def test_validate_server_semantics_no_platforms(self):
        """Test semantic validation for no platforms."""
        server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test description",
            category=["test"],
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            installation=ServerInstallation(method="npm", package="test-server"),
            configuration=ServerConfiguration(),
            capabilities=["operations"],
            platforms=[],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server, 0)
        
        assert len(self.validator.warnings) == 1
        assert "No platforms specified" in self.validator.warnings[0]
    
    def test_validate_server_semantics_multiple_warnings(self):
        """Test semantic validation with multiple warnings."""
        server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test description",
            category=[],  # No categories
            author="Test Author",
            versions=ServerVersions(latest="2.0.0", supported=["1.0.0"]),  # Latest not in supported
            installation=ServerInstallation(method="npm", package="test-server"),
            configuration=ServerConfiguration(),
            capabilities=["operations"],
            platforms=[],  # No platforms
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server, 0)
        
        assert len(self.validator.warnings) == 3
        warning_text = " ".join(self.validator.warnings)
        assert "Latest version not in supported versions" in warning_text
        assert "No categories specified" in warning_text
        assert "No platforms specified" in warning_text
    
    # Validation report tests
    def test_get_validation_report_no_issues(self):
        """Test validation report with no errors or warnings."""
        report = self.validator.get_validation_report()
        
        assert report["valid"] is True
        assert report["error_count"] == 0
        assert report["warning_count"] == 0
        assert report["errors"] == []
        assert report["warnings"] == []
    
    def test_get_validation_report_with_errors(self):
        """Test validation report with errors."""
        self.validator.errors = ["Error 1", "Error 2"]
        self.validator.warnings = ["Warning 1"]
        
        report = self.validator.get_validation_report()
        
        assert report["valid"] is False
        assert report["error_count"] == 2
        assert report["warning_count"] == 1
        assert report["errors"] == ["Error 1", "Error 2"]
        assert report["warnings"] == ["Warning 1"]
    
    def test_get_validation_report_with_warnings_only(self):
        """Test validation report with warnings only."""
        self.validator.warnings = ["Warning 1", "Warning 2"]
        
        report = self.validator.get_validation_report()
        
        assert report["valid"] is True  # Warnings don't make it invalid
        assert report["error_count"] == 0
        assert report["warning_count"] == 2
        assert report["errors"] == []
        assert report["warnings"] == ["Warning 1", "Warning 2"]
    
    def test_get_validation_report_creates_copy(self):
        """Test that validation report creates copies of error/warning lists."""
        self.validator.errors = ["Error 1"]
        self.validator.warnings = ["Warning 1"]
        
        report = self.validator.get_validation_report()
        
        # Modify original lists
        self.validator.errors.append("Error 2")
        self.validator.warnings.append("Warning 2")
        
        # Report should not be affected
        assert report["errors"] == ["Error 1"]
        assert report["warnings"] == ["Warning 1"]
    
    # Print validation report tests (using capsys)
    def test_print_validation_report_no_issues(self, capsys):
        """Test printing validation report with no issues."""
        self.validator.print_validation_report()
        
        captured = capsys.readouterr()
        assert "✅ Registry validation passed with no issues" in captured.out
    
    def test_print_validation_report_with_errors(self, capsys):
        """Test printing validation report with errors."""
        self.validator.errors = ["Error 1", "Error 2"]
        
        self.validator.print_validation_report()
        
        captured = capsys.readouterr()
        assert "❌ Registry validation failed with 2 errors:" in captured.out
        assert "• Error 1" in captured.out
        assert "• Error 2" in captured.out
    
    def test_print_validation_report_with_warnings(self, capsys):
        """Test printing validation report with warnings."""
        self.validator.warnings = ["Warning 1", "Warning 2"]
        
        self.validator.print_validation_report()
        
        captured = capsys.readouterr()
        assert "⚠️  Registry validation has 2 warnings:" in captured.out
        assert "• Warning 1" in captured.out
        assert "• Warning 2" in captured.out
        assert "✅ Registry is valid despite warnings" in captured.out
    
    def test_print_validation_report_with_errors_and_warnings(self, capsys):
        """Test printing validation report with both errors and warnings."""
        self.validator.errors = ["Error 1"]
        self.validator.warnings = ["Warning 1"]
        
        self.validator.print_validation_report()
        
        captured = capsys.readouterr()
        assert "❌ Registry validation failed with 1 errors:" in captured.out
        assert "⚠️  Registry validation has 1 warnings:" in captured.out
        assert "• Error 1" in captured.out
        assert "• Warning 1" in captured.out
        assert "✅ Registry is valid despite warnings" not in captured.out  # Shouldn't show this with errors
    
    # Class method tests
    def test_validate_server_dict_valid(self):
        """Test classmethod for validating server dictionary - valid case."""
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux", "darwin", "windows"],
            "license": "MIT"
        }
        
        result = RegistryValidator.validate_server_dict(server_data)
        
        assert result is True
    
    def test_validate_server_dict_validation_error(self):
        """Test classmethod for validating server dictionary - ValidationError case."""
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "invalid-method", "package": "test-server"},  # Invalid method
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        result = RegistryValidator.validate_server_dict(server_data)
        
        assert result is False
    
    def test_validate_server_dict_type_error(self):
        """Test classmethod for validating server dictionary - TypeError case."""
        server_data = {
            "id": 123,  # Should be string, will cause TypeError
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        result = RegistryValidator.validate_server_dict(server_data)
        
        assert result is False
    
    def test_validate_server_dict_value_error(self):
        """Test classmethod for validating server dictionary - ValueError case."""
        # Simulate a case that might cause ValueError
        with patch('mcpi.registry.validation.MCPServer') as mock_mcpserver:
            mock_mcpserver.side_effect = ValueError("Invalid value")
            
            result = RegistryValidator.validate_server_dict({})
            
            assert result is False
    
    def test_get_server_validation_errors_no_errors(self):
        """Test classmethod for getting server validation errors - no errors."""
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "npm", "package": "test-server"},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux", "darwin", "windows"],
            "license": "MIT"
        }
        
        errors = RegistryValidator.get_server_validation_errors(server_data)
        
        assert errors == []
    
    def test_get_server_validation_errors_with_validation_error(self):
        """Test classmethod for getting server validation errors - with ValidationError."""
        server_data = {
            "id": "test-server",
            "name": "Test Server",
            "description": "Test description",
            "category": ["test"],
            "author": "Test Author",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "installation": {"method": "invalid-method", "package": "test-server"},  # Invalid method
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["test_operations"],
            "platforms": ["linux"],
            "license": "MIT"
        }
        
        errors = RegistryValidator.get_server_validation_errors(server_data)
        
        assert len(errors) > 0
        assert isinstance(errors, list)
        assert all(isinstance(error, str) for error in errors)
    
    def test_get_server_validation_errors_with_exception(self):
        """Test classmethod for getting server validation errors - with general Exception."""
        # Mock to raise a general exception
        with patch('mcpi.registry.validation.MCPServer') as mock_mcpserver:
            mock_mcpserver.side_effect = RuntimeError("Unexpected error")
            
            errors = RegistryValidator.get_server_validation_errors({})
            
            assert len(errors) == 1
            assert "Unexpected error" in errors[0]
    
    # Edge cases and integration tests
    def test_validation_workflow_complete(self, tmp_path):
        """Test complete validation workflow from file to report."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "version": "1.0.0",
            "servers": [
                {
                    "id": "valid-server",
                    "name": "Valid Server",
                    "description": "A valid server",
                    "category": ["test"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "valid-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["operations"],
                    "platforms": ["linux"],
                    "license": "MIT"
                },
                {
                    "id": "warning-server",
                    "name": "Warning Server",
                    "description": "Server with warnings",
                    "category": [],  # Will generate warning
                    "author": "Test Author",
                    "versions": {"latest": "2.0.0", "supported": ["1.0.0"]},  # Will generate warning
                    "installation": {"method": "npm", "package": "warning-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["operations"],
                    "platforms": [],  # Will generate warning
                    "license": "MIT"
                }
            ]
        }
        
        registry_path.write_text(json.dumps(registry_data))
        
        # Validate file
        result = self.validator.validate_registry_file(registry_path)
        
        assert result is True
        assert len(self.validator.errors) == 0
        assert len(self.validator.warnings) > 0  # Should have warnings from semantic validation
        
        # Check report
        report = self.validator.get_validation_report()
        assert report["valid"] is True
        assert report["error_count"] == 0
        assert report["warning_count"] > 0
    
    def test_validation_with_mixed_results(self, tmp_path):
        """Test validation with mixed valid/invalid servers."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "servers": [
                {
                    "id": "valid-server",
                    "name": "Valid Server",
                    "description": "A valid server",
                    "category": ["test"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "valid-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["operations"],
                    "platforms": ["linux"],
                    "license": "MIT"
                },
                {
                    "id": "invalid-server",
                    "name": "Invalid Server",
                    "description": "An invalid server",
                    "category": ["test"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "invalid-method", "package": "invalid-server"},  # Invalid
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["operations"],
                    "platforms": ["linux"],
                    "license": "MIT"
                }
            ]
        }
        
        registry_path.write_text(json.dumps(registry_data))
        
        result = self.validator.validate_registry_file(registry_path)
        
        assert result is False  # Should fail due to invalid server
        assert len(self.validator.errors) > 0
        
        # Check that the error mentions the invalid server
        error_text = " ".join(self.validator.errors)
        assert "Server 1" in error_text or "invalid-server" in error_text
    
    def test_server_continues_after_failure(self):
        """Test that validation continues with other servers after one fails."""
        servers_data = [
            {
                "id": "server1",
                "name": "Server 1",
                "description": "First server",
                "category": ["test"],
                "author": "Test Author",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "invalid-method", "package": "server1"},  # Invalid
                "configuration": {"required_params": [], "optional_params": []},
                "capabilities": ["operations"],
                "platforms": ["linux"],
                "license": "MIT"
            },
            {
                "id": "server2",
                "name": "Server 2",
                "description": "Second server",
                "category": ["test"],
                "author": "Test Author",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "npm", "package": "server2"},  # Valid
                "configuration": {"required_params": [], "optional_params": []},
                "capabilities": ["operations"],
                "platforms": ["linux"],
                "license": "MIT"
            },
            {
                "id": "server2",  # Duplicate ID should be caught
                "name": "Server 3",
                "description": "Third server",
                "category": ["test"],
                "author": "Test Author",
                "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                "installation": {"method": "npm", "package": "server3"},
                "configuration": {"required_params": [], "optional_params": []},
                "capabilities": ["operations"],
                "platforms": ["linux"],
                "license": "MIT"
            }
        ]
        
        result = self.validator.validate_servers(servers_data)
        
        assert result is False
        assert len(self.validator.errors) >= 2  # At least validation error + duplicate ID
        
        # Check that both types of errors are present
        error_text = " ".join(self.validator.errors)
        assert "Server 0" in error_text  # First server validation error
        assert "Duplicate server ID: server2" in error_text  # Duplicate ID error
    
    def test_empty_registry_edge_cases(self):
        """Test edge cases with empty or minimal data."""
        # Test completely empty data
        result1 = self.validator.validate_registry_data({})
        assert result1 is False
        assert "Registry must contain 'servers' array" in self.validator.errors[0]
        
        # Reset validator
        self.validator.errors.clear()
        self.validator.warnings.clear()
        
        # Test with empty servers
        result2 = self.validator.validate_registry_data({"servers": []})
        assert result2 is True
        assert len(self.validator.warnings) == 1
        assert "Registry contains no servers" in self.validator.warnings[0]
    
    def test_npm_package_validation_edge_cases(self):
        """Test NPM package validation edge cases in semantic validation."""
        # Test NPM package that doesn't start with @ (should be fine)
        server1 = MCPServer(
            id="test-server1",
            name="Test Server 1",
            description="Test description",
            category=["test"],
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            installation=ServerInstallation(method="npm", package="regular-package"),
            configuration=ServerConfiguration(),
            capabilities=["operations"],
            platforms=["linux"],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server1, 0)
        # Should have no warnings about NPM package format
        npm_warnings = [w for w in self.validator.warnings if "NPM" in w or "npm" in w]
        assert len(npm_warnings) == 0
        
        # Reset warnings
        self.validator.warnings.clear()
        
        # Test NPM package with npm: prefix (should be fine)
        server2 = MCPServer(
            id="test-server2",
            name="Test Server 2",
            description="Test description",
            category=["test"],
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            installation=ServerInstallation(method="npm", package="npm:package-name"),
            configuration=ServerConfiguration(),
            capabilities=["operations"],
            platforms=["linux"],
            license="MIT"
        )
        
        self.validator._validate_server_semantics(server2, 0)
        # Should have no warnings about NPM package format
        npm_warnings = [w for w in self.validator.warnings if "NPM" in w or "npm" in w]
        assert len(npm_warnings) == 0


# Additional test fixtures and helper functions
@pytest.fixture
def valid_server_data():
    """Fixture providing valid server data."""
    return {
        "id": "test-server",
        "name": "Test Server",
        "description": "A test server for validation",
        "category": ["test", "validation"],
        "author": "Test Author",
        "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
        "installation": {"method": "npm", "package": "test-server"},
        "configuration": {"required_params": [], "optional_params": []},
        "capabilities": ["test_operations"],
        "platforms": ["linux", "darwin", "windows"],
        "license": "MIT"
    }


@pytest.fixture
def invalid_server_data():
    """Fixture providing invalid server data."""
    return {
        "id": "invalid-server",
        "name": "",  # Empty name
        "description": "",  # Empty description
        "category": [],  # Empty categories
        "author": "",  # Empty author
        "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
        "installation": {"method": "invalid-method", "package": ""},  # Invalid method, empty package
        "configuration": {"required_params": [], "optional_params": []},
        "capabilities": [],
        "platforms": [],  # Empty platforms
        "license": ""  # Empty license
    }


class TestRegistryValidatorIntegration:
    """Integration tests combining multiple validation aspects."""
    
    def test_full_registry_validation_cycle(self, tmp_path, valid_server_data):
        """Test complete validation cycle with file I/O."""
        registry_path = tmp_path / "test_registry.json"
        registry_data = {
            "version": "1.0.0",
            "description": "Test registry",
            "servers": [valid_server_data]
        }
        
        registry_path.write_text(json.dumps(registry_data))
        
        validator = RegistryValidator()
        result = validator.validate_registry_file(registry_path)
        
        assert result is True
        assert len(validator.errors) == 0
        
        report = validator.get_validation_report()
        assert report["valid"] is True
        assert report["error_count"] == 0
    
    def test_complex_validation_scenarios(self, tmp_path):
        """Test complex validation scenarios with multiple edge cases."""
        registry_path = tmp_path / "complex_registry.json"
        
        # Create a registry with various scenarios
        registry_data = {
            "version": 123,  # Wrong type - should warn
            "servers": [
                # Valid server
                {
                    "id": "valid-server",
                    "name": "Valid Server",
                    "description": "A completely valid server",
                    "category": ["test", "validation"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "@scope/valid-server"},
                    "configuration": {"required_params": ["config1"], "optional_params": ["config2"]},
                    "capabilities": ["operations", "validation"],
                    "platforms": ["linux", "darwin", "windows"],
                    "license": "MIT"
                },
                # Server with semantic warnings
                {
                    "id": "warning-server",
                    "name": "Warning Server",
                    "description": "Server that generates warnings",
                    "category": [],  # No categories warning
                    "author": "Test Author",
                    "versions": {"latest": "2.0.0", "supported": ["1.0.0", "1.5.0"]},  # Latest not in supported
                    "installation": {"method": "pip", "package": "@invalid/pip-package"},  # Invalid pip package format
                    "configuration": {"required_params": [f"param{i}" for i in range(12)], "optional_params": []},  # Too many params
                    "capabilities": [f"cap{i}" for i in range(25)],  # Too many capabilities
                    "platforms": [],  # No platforms
                    "license": "MIT"
                },
                # Duplicate ID (should error)
                {
                    "id": "valid-server",  # Duplicate!
                    "name": "Duplicate Server",
                    "description": "This has a duplicate ID",
                    "category": ["duplicate"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "npm", "package": "duplicate-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["operations"],
                    "platforms": ["linux"],
                    "license": "MIT"
                },
                # Invalid server (should error)
                {
                    "id": "invalid-server",
                    "name": "Invalid Server",
                    "description": "This server has invalid installation method",
                    "category": ["invalid"],
                    "author": "Test Author",
                    "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
                    "installation": {"method": "nonexistent-method", "package": "invalid-server"},
                    "configuration": {"required_params": [], "optional_params": []},
                    "capabilities": ["operations"],
                    "platforms": ["linux"],
                    "license": "MIT"
                }
            ]
        }
        
        registry_path.write_text(json.dumps(registry_data))
        
        validator = RegistryValidator()
        result = validator.validate_registry_file(registry_path)
        
        # Should fail due to duplicate ID and invalid method
        assert result is False
        assert len(validator.errors) >= 2  # At least duplicate ID and validation error
        assert len(validator.warnings) >= 5  # Version warning + multiple semantic warnings
        
        # Verify specific errors and warnings
        error_text = " ".join(validator.errors)
        warning_text = " ".join(validator.warnings)
        
        assert "Duplicate server ID: valid-server" in error_text
        assert "Registry version should be a string" in warning_text
        assert "No categories specified" in warning_text
        assert "Latest version not in supported versions" in warning_text
        assert "PIP package should not start with '@'" in warning_text
        assert "Many required parameters" in warning_text
        assert "Many capabilities" in warning_text
        assert "No platforms specified" in warning_text
        
        # Test report
        report = validator.get_validation_report()
        assert report["valid"] is False
        assert report["error_count"] >= 2
        assert report["warning_count"] >= 5