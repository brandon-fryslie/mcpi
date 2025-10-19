"""Tests for Python installer module."""

import pytest
import subprocess
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from mcpi.installer.python import PythonInstaller
from mcpi.installer.base import InstallationResult
from mcpi.registry.catalog import MCPServer, ServerInstallation, ServerVersions, ServerConfiguration, InstallationMethod


class TestPythonInstaller:
    """Test suite for PythonInstaller class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.installer = PythonInstaller()
        self.installer_with_custom_python = PythonInstaller(python_path="/usr/bin/python3")
        self.installer_no_uv = PythonInstaller(use_uv=False)
        self.dry_run_installer = PythonInstaller(dry_run=True)
        
    def create_mock_server(self, server_id="test_server", package="test-package", dependencies=None):
        """Create mock MCP server for testing."""
        installation = ServerInstallation(
            method=InstallationMethod.PIP,
            package=package,
            python_dependencies=dependencies or []
        )
        versions = ServerVersions(latest="1.0.0")
        configuration = ServerConfiguration()
        
        return MCPServer(
            id=server_id,
            name="Test Server",
            description="Test server description",
            author="Test Author",
            license="MIT",
            versions=versions,
            installation=installation,
            configuration=configuration
        )

    def test_init_default(self):
        """Test default initialization."""
        installer = PythonInstaller()
        assert installer.python_path == sys.executable
        assert installer.use_uv is True
        assert installer.dry_run is False
        assert installer._package_manager in ["uv", "pip"]

    def test_init_custom_python_path(self):
        """Test initialization with custom Python path."""
        custom_path = "/usr/bin/python3.9"
        installer = PythonInstaller(python_path=custom_path)
        assert installer.python_path == custom_path

    def test_init_no_uv(self):
        """Test initialization without uv preference."""
        installer = PythonInstaller(use_uv=False)
        assert installer.use_uv is False

    def test_init_dry_run(self):
        """Test initialization with dry run mode."""
        installer = PythonInstaller(dry_run=True)
        assert installer.dry_run is True

    @patch.object(PythonInstaller, '_check_uv_available')
    def test_detect_package_manager_uv_available(self, mock_check_uv):
        """Test package manager detection when uv is available."""
        mock_check_uv.return_value = True
        installer = PythonInstaller(use_uv=True)
        assert installer._package_manager == "uv"

    @patch.object(PythonInstaller, '_check_uv_available')
    def test_detect_package_manager_uv_not_available(self, mock_check_uv):
        """Test package manager detection when uv is not available."""
        mock_check_uv.return_value = False
        installer = PythonInstaller(use_uv=True)
        assert installer._package_manager == "pip"

    def test_detect_package_manager_uv_disabled(self):
        """Test package manager detection when uv is disabled."""
        installer = PythonInstaller(use_uv=False)
        assert installer._package_manager == "pip"

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_install_dependencies')
    @patch.object(PythonInstaller, '_run_uv_command')
    @patch.object(PythonInstaller, '_get_install_details')
    def test_install_success_uv(self, mock_get_details, mock_run_uv, mock_install_deps, mock_check_python):
        """Test successful package installation with uv."""
        server = self.create_mock_server()
        mock_check_python.return_value = True
        
        # Mock dependency installation
        deps_result = InstallationResult(status="success", message="Dependencies installed", server_id="deps")
        mock_install_deps.return_value = deps_result
        
        # Mock uv command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "package installed successfully"
        mock_result.stderr = ""
        mock_run_uv.return_value = mock_result
        
        # Mock install details
        mock_get_details.return_value = {"version": "1.0.0", "location": "/path/to/package"}
        
        # Set package manager to uv
        installer = PythonInstaller(use_uv=True)
        with patch.object(installer, '_package_manager', 'uv'):
            result = installer.install(server)
        
        assert result.success is True
        assert result.server_id == "test_server"
        assert "Successfully installed test-package" in result.message
        assert result.details["package_name"] == "test-package"
        assert result.details["install_method"] == "uv"
        assert result.details["version"] == "1.0.0"

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_install_dependencies')
    @patch.object(PythonInstaller, '_run_pip_command')
    @patch.object(PythonInstaller, '_get_install_details')
    def test_install_success_pip(self, mock_get_details, mock_run_pip, mock_install_deps, mock_check_python):
        """Test successful package installation with pip."""
        server = self.create_mock_server()
        mock_check_python.return_value = True
        
        # Mock dependency installation
        deps_result = InstallationResult(status="success", message="Dependencies installed", server_id="deps")
        mock_install_deps.return_value = deps_result
        
        # Mock pip command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "package installed successfully"
        mock_result.stderr = ""
        mock_run_pip.return_value = mock_result
        
        # Mock install details
        mock_get_details.return_value = {"version": "1.0.0"}
        
        # Set package manager to pip
        installer = PythonInstaller(use_uv=False)
        result = installer.install(server)
        
        assert result.success is True
        assert result.server_id == "test_server"
        assert "Successfully installed test-package" in result.message

    def test_install_wrong_method(self):
        """Test installation with wrong method."""
        installation = ServerInstallation(method=InstallationMethod.NPM, package="test-package")
        versions = ServerVersions(latest="1.0.0")
        server = MCPServer(
            id="test", 
            name="Test", 
            description="Test server", 
            author="Test Author",
            license="MIT",
            versions=versions,
            installation=installation
        )
        
        result = self.installer.install(server)
        
        assert result.success is False
        assert "is not a Python package" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    def test_install_python_not_available(self, mock_check_python):
        """Test installation when Python is not available."""
        server = self.create_mock_server()
        mock_check_python.return_value = False
        
        result = self.installer.install(server)
        
        assert result.success is False
        assert "Python is not available" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_install_dependencies')
    def test_install_dependency_failure(self, mock_install_deps, mock_check_python):
        """Test installation when dependency installation fails."""
        server = self.create_mock_server(dependencies=["dep1", "dep2"])
        mock_check_python.return_value = True
        
        # Mock dependency installation failure
        deps_result = InstallationResult(status="failed", message="Dependency error", server_id="deps")
        mock_install_deps.return_value = deps_result
        
        result = self.installer.install(server)
        
        assert result.success is False
        assert "Failed to install Python dependencies" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_install_dependencies')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_install_package_failure(self, mock_run_pip, mock_install_deps, mock_check_python):
        """Test installation when package installation fails."""
        server = self.create_mock_server()
        mock_check_python.return_value = True
        
        # Mock successful dependency installation
        deps_result = InstallationResult(status="success", message="Dependencies installed", server_id="deps")
        mock_install_deps.return_value = deps_result
        
        # Mock pip command failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Package not found"
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.install(server)
        
        assert result.success is False
        assert "Python installation failed" in result.message
        assert result.details["install_error"] == "Package not found"

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_install_dependencies')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_install_exception(self, mock_run_pip, mock_install_deps, mock_check_python):
        """Test installation with exception."""
        server = self.create_mock_server()
        mock_check_python.return_value = True
        
        # Mock successful dependency installation
        deps_result = InstallationResult(status="success", message="Dependencies installed", server_id="deps")
        mock_install_deps.return_value = deps_result
        
        # Mock exception
        mock_run_pip.side_effect = Exception("Network error")
        
        result = self.installer_no_uv.install(server)
        
        assert result.success is False
        assert "Python installation error" in result.message
        assert "Network error" in result.details["exception"]

    @patch.object(PythonInstaller, '_run_uv_command')
    def test_install_dependencies_uv_success(self, mock_run_uv):
        """Test successful dependency installation with uv."""
        dependencies = ["dep1", "dep2"]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "dependencies installed"
        mock_result.stderr = ""
        mock_run_uv.return_value = mock_result
        
        installer = PythonInstaller(use_uv=True)
        with patch.object(installer, '_package_manager', 'uv'):
            result = installer._install_dependencies(dependencies)
        
        assert result.success is True
        assert "Successfully installed dependencies" in result.message
        mock_run_uv.assert_called_once_with(["add"] + dependencies)

    @patch.object(PythonInstaller, '_run_pip_command')
    def test_install_dependencies_pip_success(self, mock_run_pip):
        """Test successful dependency installation with pip."""
        dependencies = ["dep1", "dep2"]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "dependencies installed"
        mock_result.stderr = ""
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv._install_dependencies(dependencies)
        
        assert result.success is True
        assert "Successfully installed dependencies" in result.message
        mock_run_pip.assert_called_once_with(["install"] + dependencies)

    @patch.object(PythonInstaller, '_run_pip_command')
    def test_install_dependencies_failure(self, mock_run_pip):
        """Test dependency installation failure."""
        dependencies = ["dep1", "dep2"]
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Package not found"
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv._install_dependencies(dependencies)
        
        assert result.success is False
        assert "Failed to install dependencies" in result.message

    @patch.object(PythonInstaller, '_run_pip_command')
    def test_install_dependencies_exception(self, mock_run_pip):
        """Test dependency installation with exception."""
        dependencies = ["dep1", "dep2"]
        
        mock_run_pip.side_effect = Exception("Network error")
        
        result = self.installer_no_uv._install_dependencies(dependencies)
        
        assert result.success is False
        assert "Error installing dependencies" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_uv_command')
    def test_uninstall_success_uv(self, mock_run_uv, mock_check_python):
        """Test successful package uninstallation with uv."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "package uninstalled"
        mock_result.stderr = ""
        mock_run_uv.return_value = mock_result
        
        installer = PythonInstaller(use_uv=True)
        with patch.object(installer, '_package_manager', 'uv'):
            result = installer.uninstall("test-package")
        
        assert result.success is True
        assert "Successfully uninstalled test-package" in result.message
        mock_run_uv.assert_called_once_with(["remove", "test-package"])

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_uninstall_success_pip(self, mock_run_pip, mock_check_python):
        """Test successful package uninstallation with pip."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "package uninstalled"
        mock_result.stderr = ""
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.uninstall("test-package")
        
        assert result.success is True
        assert "Successfully uninstalled test-package" in result.message
        mock_run_pip.assert_called_once_with(["uninstall", "-y", "test-package"])

    @patch.object(PythonInstaller, '_check_python_available')
    def test_uninstall_python_not_available(self, mock_check_python):
        """Test uninstallation when Python is not available."""
        mock_check_python.return_value = False
        
        result = self.installer.uninstall("test-package")
        
        assert result.success is False
        assert "Python is not available" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_uninstall_failure(self, mock_run_pip, mock_check_python):
        """Test package uninstallation failure."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Package not installed"
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.uninstall("test-package")
        
        assert result.success is False
        assert "Python uninstallation failed" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_uninstall_exception(self, mock_run_pip, mock_check_python):
        """Test package uninstallation with exception."""
        mock_check_python.return_value = True
        
        mock_run_pip.side_effect = Exception("Network error")
        
        result = self.installer_no_uv.uninstall("test-package")
        
        assert result.success is False
        assert "Python uninstallation error" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_uv_command')
    def test_is_installed_uv_true(self, mock_run_uv, mock_check_python):
        """Test package installation check with uv - installed."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.stdout = "test-package    1.0.0"
        mock_run_uv.return_value = mock_result
        
        installer = PythonInstaller(use_uv=True)
        with patch.object(installer, '_package_manager', 'uv'):
            result = installer.is_installed("test-package")
        
        assert result is True
        mock_run_uv.assert_called_once_with(["pip", "list"])

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_uv_command')
    def test_is_installed_uv_false(self, mock_run_uv, mock_check_python):
        """Test package installation check with uv - not installed."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.stdout = "other-package    1.0.0"
        mock_run_uv.return_value = mock_result
        
        installer = PythonInstaller(use_uv=True)
        with patch.object(installer, '_package_manager', 'uv'):
            result = installer.is_installed("test-package")
        
        assert result is False

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_is_installed_pip_true(self, mock_run_pip, mock_check_python):
        """Test package installation check with pip - installed."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.is_installed("test-package")
        
        assert result is True
        mock_run_pip.assert_called_once_with(["show", "test-package"])

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_is_installed_pip_false(self, mock_run_pip, mock_check_python):
        """Test package installation check with pip - not installed."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.is_installed("test-package")
        
        assert result is False

    @patch.object(PythonInstaller, '_check_python_available')
    def test_is_installed_python_not_available(self, mock_check_python):
        """Test package installation check when Python is not available."""
        mock_check_python.return_value = False
        
        result = self.installer.is_installed("test-package")
        
        assert result is False

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_is_installed_exception(self, mock_run_pip, mock_check_python):
        """Test package installation check with exception."""
        mock_check_python.return_value = True
        
        mock_run_pip.side_effect = Exception("Network error")
        
        result = self.installer_no_uv.is_installed("test-package")
        
        assert result is False

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_uv_command')
    def test_get_installed_servers_uv_success(self, mock_run_uv, mock_check_python):
        """Test getting installed packages with uv."""
        mock_check_python.return_value = True
        
        packages_data = [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.0.0"}
        ]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(packages_data)
        mock_run_uv.return_value = mock_result
        
        installer = PythonInstaller(use_uv=True)
        with patch.object(installer, '_package_manager', 'uv'):
            result = installer.get_installed_servers()
        
        assert result == ["package1", "package2"]
        mock_run_uv.assert_called_once_with(["pip", "list", "--format=json"])

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_get_installed_servers_pip_success(self, mock_run_pip, mock_check_python):
        """Test getting installed packages with pip."""
        mock_check_python.return_value = True
        
        packages_data = [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.0.0"}
        ]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(packages_data)
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.get_installed_servers()
        
        assert result == ["package1", "package2"]
        mock_run_pip.assert_called_once_with(["list", "--format=json"])

    @patch.object(PythonInstaller, '_check_python_available')
    def test_get_installed_servers_python_not_available(self, mock_check_python):
        """Test getting installed packages when Python is not available."""
        mock_check_python.return_value = False
        
        result = self.installer.get_installed_servers()
        
        assert result == []

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_get_installed_servers_command_failure(self, mock_run_pip, mock_check_python):
        """Test getting installed packages when command fails."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.get_installed_servers()
        
        assert result == []

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_get_installed_servers_exception(self, mock_run_pip, mock_check_python):
        """Test getting installed packages with exception."""
        mock_check_python.return_value = True
        
        mock_run_pip.side_effect = Exception("Network error")
        
        result = self.installer_no_uv.get_installed_servers()
        
        assert result == []

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_uv_command')
    def test_get_package_info_uv_success(self, mock_run_uv, mock_check_python):
        """Test getting package information with uv."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Name: test-package\nVersion: 1.0.0\nLocation: /path/to/package"
        mock_run_uv.return_value = mock_result
        
        installer = PythonInstaller(use_uv=True)
        with patch.object(installer, '_package_manager', 'uv'):
            result = installer.get_package_info("test-package")
        
        expected = {
            "name": "test-package",
            "version": "1.0.0",
            "location": "/path/to/package"
        }
        assert result == expected
        mock_run_uv.assert_called_once_with(["pip", "show", "test-package"])

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_get_package_info_pip_success(self, mock_run_pip, mock_check_python):
        """Test getting package information with pip."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Name: test-package\nVersion: 1.0.0\nLocation: /path/to/package"
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.get_package_info("test-package")
        
        expected = {
            "name": "test-package",
            "version": "1.0.0",
            "location": "/path/to/package"
        }
        assert result == expected
        mock_run_pip.assert_called_once_with(["show", "test-package"])

    @patch.object(PythonInstaller, '_check_python_available')
    def test_get_package_info_python_not_available(self, mock_check_python):
        """Test getting package information when Python is not available."""
        mock_check_python.return_value = False
        
        result = self.installer.get_package_info("test-package")
        
        assert result is None

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_get_package_info_package_not_found(self, mock_run_pip, mock_check_python):
        """Test getting package information for non-existent package."""
        mock_check_python.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.get_package_info("non-existent-package")
        
        assert result is None

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_get_package_info_exception(self, mock_run_pip, mock_check_python):
        """Test getting package information with exception."""
        mock_check_python.return_value = True
        
        mock_run_pip.side_effect = Exception("Network error")
        
        result = self.installer_no_uv.get_package_info("test-package")
        
        assert result is None

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, 'is_installed')
    @patch.object(PythonInstaller, '_run_uv_command')
    def test_update_package_uv_success(self, mock_run_uv, mock_is_installed, mock_check_python):
        """Test successful package update with uv."""
        mock_check_python.return_value = True
        mock_is_installed.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "package updated"
        mock_result.stderr = ""
        mock_run_uv.return_value = mock_result
        
        installer = PythonInstaller(use_uv=True)
        with patch.object(installer, '_package_manager', 'uv'):
            result = installer.update_package("test-package")
        
        assert result.success is True
        assert "Successfully updated test-package" in result.message
        mock_run_uv.assert_called_once_with(["add", "test-package@latest"])

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, 'is_installed')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_update_package_pip_success(self, mock_run_pip, mock_is_installed, mock_check_python):
        """Test successful package update with pip."""
        mock_check_python.return_value = True
        mock_is_installed.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "package updated"
        mock_result.stderr = ""
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.update_package("test-package")
        
        assert result.success is True
        assert "Successfully updated test-package" in result.message
        mock_run_pip.assert_called_once_with(["install", "--upgrade", "test-package"])

    @patch.object(PythonInstaller, '_check_python_available')
    def test_update_package_python_not_available(self, mock_check_python):
        """Test package update when Python is not available."""
        mock_check_python.return_value = False
        
        result = self.installer.update_package("test-package")
        
        assert result.success is False
        assert "Python is not available" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, 'is_installed')
    def test_update_package_not_installed(self, mock_is_installed, mock_check_python):
        """Test package update when package is not installed."""
        mock_check_python.return_value = True
        mock_is_installed.return_value = False
        
        result = self.installer.update_package("test-package")
        
        assert result.success is False
        assert "is not installed" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, 'is_installed')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_update_package_failure(self, mock_run_pip, mock_is_installed, mock_check_python):
        """Test package update failure."""
        mock_check_python.return_value = True
        mock_is_installed.return_value = True
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Update failed"
        mock_run_pip.return_value = mock_result
        
        result = self.installer_no_uv.update_package("test-package")
        
        assert result.success is False
        assert "Python update failed" in result.message

    @patch.object(PythonInstaller, '_check_python_available')
    @patch.object(PythonInstaller, 'is_installed')
    @patch.object(PythonInstaller, '_run_pip_command')
    def test_update_package_exception(self, mock_run_pip, mock_is_installed, mock_check_python):
        """Test package update with exception."""
        mock_check_python.return_value = True
        mock_is_installed.return_value = True
        
        mock_run_pip.side_effect = Exception("Network error")
        
        result = self.installer_no_uv.update_package("test-package")
        
        assert result.success is False
        assert "Python update error" in result.message

    @patch.object(PythonInstaller, 'get_package_info')
    def test_get_install_details_with_info(self, mock_get_info):
        """Test getting install details when package info is available."""
        mock_get_info.return_value = {
            "version": "1.0.0",
            "location": "/path/to/package"
        }
        
        result = self.installer._get_install_details("test-package")
        
        expected = {
            "version": "1.0.0",
            "location": "/path/to/package"
        }
        assert result == expected

    @patch.object(PythonInstaller, 'get_package_info')
    def test_get_install_details_no_info(self, mock_get_info):
        """Test getting install details when package info is not available."""
        mock_get_info.return_value = None
        
        result = self.installer._get_install_details("test-package")
        
        assert result == {}

    @patch.object(PythonInstaller, 'get_package_info')
    def test_get_install_details_partial_info(self, mock_get_info):
        """Test getting install details with partial package info."""
        mock_get_info.return_value = {
            "version": "1.0.0"
            # Missing location
        }
        
        result = self.installer._get_install_details("test-package")
        
        expected = {
            "version": "1.0.0",
            "location": ""
        }
        assert result == expected

    @patch('subprocess.run')
    def test_check_python_available_success(self, mock_run):
        """Test Python availability check success."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.installer._check_python_available()
        
        assert result is True
        mock_run.assert_called_once_with(
            [self.installer.python_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

    @patch('subprocess.run')
    def test_check_python_available_failure(self, mock_run):
        """Test Python availability check failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = self.installer._check_python_available()
        
        assert result is False

    @patch('subprocess.run')
    def test_check_python_available_exception(self, mock_run):
        """Test Python availability check with exception."""
        mock_run.side_effect = subprocess.SubprocessError("Command failed")
        
        result = self.installer._check_python_available()
        
        assert result is False

    @patch('subprocess.run')
    def test_check_python_available_file_not_found(self, mock_run):
        """Test Python availability check with file not found."""
        mock_run.side_effect = FileNotFoundError("Python not found")
        
        result = self.installer._check_python_available()
        
        assert result is False

    @patch('subprocess.run')
    def test_check_uv_available_success(self, mock_run):
        """Test uv availability check success."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.installer._check_uv_available()
        
        assert result is True
        mock_run.assert_called_once_with(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

    @patch('subprocess.run')
    def test_check_uv_available_failure(self, mock_run):
        """Test uv availability check failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = self.installer._check_uv_available()
        
        assert result is False

    @patch('subprocess.run')
    def test_check_uv_available_exception(self, mock_run):
        """Test uv availability check with exception."""
        mock_run.side_effect = subprocess.SubprocessError("Command failed")
        
        result = self.installer._check_uv_available()
        
        assert result is False

    @patch('subprocess.run')
    def test_check_uv_available_file_not_found(self, mock_run):
        """Test uv availability check with file not found."""
        mock_run.side_effect = FileNotFoundError("uv not found")
        
        result = self.installer._check_uv_available()
        
        assert result is False

    def test_run_pip_command_dry_run(self):
        """Test running pip command in dry run mode."""
        args = ["install", "test-package"]
        
        result = self.dry_run_installer._run_pip_command(args)
        
        assert result.returncode == 0
        assert "[DRY RUN]" in result.stdout
        assert "pip install test-package" in result.stdout

    @patch('subprocess.run')
    def test_run_pip_command_normal(self, mock_run):
        """Test running pip command in normal mode."""
        args = ["install", "test-package"]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "package installed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.installer._run_pip_command(args)
        
        assert result == mock_result
        mock_run.assert_called_once_with(
            [self.installer.python_path, "-m", "pip"] + args,
            capture_output=True,
            text=True,
            timeout=300
        )

    def test_run_uv_command_dry_run(self):
        """Test running uv command in dry run mode."""
        args = ["add", "test-package"]
        
        result = self.dry_run_installer._run_uv_command(args)
        
        assert result.returncode == 0
        assert "[DRY RUN]" in result.stdout
        assert "uv add test-package" in result.stdout

    @patch('subprocess.run')
    def test_run_uv_command_normal(self, mock_run):
        """Test running uv command in normal mode."""
        args = ["add", "test-package"]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "package added"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.installer._run_uv_command(args)
        
        assert result == mock_result
        mock_run.assert_called_once_with(
            ["uv"] + args,
            capture_output=True,
            text=True,
            timeout=300
        )

    def test_supports_method_pip(self):
        """Test installer supports PIP method."""
        assert self.installer._supports_method(InstallationMethod.PIP) is True

    def test_supports_method_other(self):
        """Test installer does not support other methods."""
        assert self.installer._supports_method(InstallationMethod.NPM) is False
        assert self.installer._supports_method(InstallationMethod.GIT) is False
        assert self.installer._supports_method("unknown") is False

    def test_install_with_config_params(self):
        """Test installation with config parameters (should be ignored)."""
        server = self.create_mock_server()
        config_params = {"some_param": "value"}
        
        with patch.object(self.installer, '_check_python_available', return_value=False):
            result = self.installer.install(server, config_params)
        
        # Should fail because Python not available, but config_params should not cause issues
        assert result.success is False