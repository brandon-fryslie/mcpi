#!/usr/bin/env python3
"""Test script for real installation workflows.

This script tests actual installation functionality to validate
that the installers work with real packages and dependencies.
"""

import sys
import tempfile
import shutil
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcpi.installer.npm import NPMInstaller
from mcpi.installer.python import PythonInstaller
from mcpi.installer.git import GitInstaller
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.registry.catalog import MCPServer, ServerInstallation, InstallationMethod


def test_npm_installer():
    """Test NPM installer with a real package."""
    print("\n=== Testing NPM Installer ===")
    
    # Create test server for a real, lightweight npm package
    server = MCPServer(
        id="test-npm-server",
        name="Test NPM Server",
        description="Test server for NPM installation",
        installation=ServerInstallation(
            method=InstallationMethod.NPM,
            package="lodash",  # Well-known, lightweight package
            system_dependencies=[],
            python_dependencies=[]
        ),
        category=["test"],
        author="test-author",
        license="MIT",
        versions={"latest": "1.0.0"},
        configuration={"required_params": [], "optional_params": []},
        capabilities=["general"],
        platforms=["linux", "darwin", "windows"],
        repository="https://github.com/lodash/lodash",
        tags=[]
    )
    
    # Test with dry run first
    installer = NPMInstaller(global_install=False, dry_run=True)
    print(f"NPM Available: {installer._check_npm_available()}")
    
    # Test validation
    validation_errors = installer.validate_installation(server)
    print(f"Validation errors: {validation_errors}")
    
    # Test dry run installation
    result = installer.install(server)
    print(f"Dry run result: {result.status} - {result.message}")
    print(f"Details: {result.details}")
    
    # Test real installation (be careful!)
    print("\n--- Testing REAL installation (local only) ---")
    real_installer = NPMInstaller(global_install=False, dry_run=False)
    
    # Create temporary directory for local install
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_cwd = Path.cwd()
        
        try:
            # Change to temp directory for local install
            import os
            os.chdir(temp_path)
            
            # Initialize npm project
            package_json = {"name": "test-mcpi", "version": "1.0.0", "private": True}
            (temp_path / "package.json").write_text(json.dumps(package_json))
            
            # Test real installation
            real_result = real_installer.install(server)
            print(f"Real install result: {real_result.status} - {real_result.message}")
            
            # Check if package was actually installed
            node_modules = temp_path / "node_modules" / "lodash"
            print(f"Package installed: {node_modules.exists()}")
            
            if real_result.success:
                # Test uninstallation
                uninstall_result = real_installer.uninstall(server.installation.package)
                print(f"Uninstall result: {uninstall_result.status} - {uninstall_result.message}")
                print(f"Package removed: {not node_modules.exists()}")
        
        finally:
            os.chdir(original_cwd)


def test_python_installer():
    """Test Python installer with a real package."""
    print("\n=== Testing Python Installer ===")
    
    # Use a lightweight Python package
    server = MCPServer(
        id="test-python-server",
        name="Test Python Server",
        description="Test server for Python installation",
        installation=ServerInstallation(
            method=InstallationMethod.PIP,
            package="requests",  # Well-known, commonly used package
            system_dependencies=[],
            python_dependencies=[]
        ),
        category=["test"],
        author="test-author",
        license="MIT",
        versions={"latest": "1.0.0"},
        configuration={"required_params": [], "optional_params": []},
        capabilities=["general"],
        platforms=["linux", "darwin", "windows"],
        repository="https://github.com/psf/requests",
        tags=[]
    )
    
    # Test installer detection
    installer = PythonInstaller(dry_run=True)
    print(f"Python Available: {installer._check_python_available()}")
    print(f"UV Available: {installer._check_uv_available()}")
    print(f"Package Manager: {installer._package_manager}")
    
    # Test validation
    validation_errors = installer.validate_installation(server)
    print(f"Validation errors: {validation_errors}")
    
    # Test dry run
    result = installer.install(server)
    print(f"Dry run result: {result.status} - {result.message}")
    
    # For Python, we'll skip real installation since it could affect the system
    print("Skipping real Python installation to avoid system changes")


def test_git_installer():
    """Test Git installer with a real repository."""
    print("\n=== Testing Git Installer ===")
    
    # Use a small public repository
    server = MCPServer(
        id="test-git-server",
        name="Test Git Server",
        description="Test server for Git installation",
        installation=ServerInstallation(
            method=InstallationMethod.GIT,
            package="https://github.com/octocat/Hello-World.git",  # Simple test repo
            system_dependencies=["git"],
            python_dependencies=[]
        ),
        category=["test"],
        author="test-author",
        license="MIT",
        versions={"latest": "main"},
        configuration={"required_params": [], "optional_params": []},
        capabilities=["general"],
        platforms=["linux", "darwin", "windows"],
        repository="https://github.com/octocat/Hello-World.git",
        tags=[]
    )
    
    # Create temporary install directory
    with tempfile.TemporaryDirectory() as temp_dir:
        install_dir = Path(temp_dir) / "git_installs"
        
        installer = GitInstaller(install_dir=install_dir, dry_run=True)
        print(f"Git Available: {installer._check_git_available()}")
        
        # Test validation
        validation_errors = installer.validate_installation(server)
        print(f"Validation errors: {validation_errors}")
        
        # Test dry run
        result = installer.install(server)
        print(f"Dry run result: {result.status} - {result.message}")
        
        # Test real git clone
        print("\n--- Testing REAL git installation ---")
        real_installer = GitInstaller(install_dir=install_dir, dry_run=False)
        
        real_result = real_installer.install(server)
        print(f"Real install result: {real_result.status} - {real_result.message}")
        
        # Check if repo was cloned
        repo_path = install_dir / server.id
        print(f"Repository cloned: {repo_path.exists()}")
        print(f"Git directory exists: {(repo_path / '.git').exists()}")
        
        if real_result.success:
            # Test uninstallation
            uninstall_result = real_installer.uninstall(server.id)
            print(f"Uninstall result: {uninstall_result.status} - {uninstall_result.message}")
            print(f"Repository removed: {not repo_path.exists()}")


def test_claude_code_installer():
    """Test Claude Code installer integration."""
    print("\n=== Testing Claude Code Installer ===")
    
    # Create temporary config file
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "mcp_servers.json"
        config_file.write_text('{"mcpServers": {}}')
        
        installer = ClaudeCodeInstaller(config_path=config_file, dry_run=True)
        print(f"Config path: {installer.config_path}")
        
        # Test configuration loading
        config = installer._load_config()
        print(f"Initial config: {config}")
        
        # Test with git server (safest for testing)
        server = MCPServer(
            id="test-integration-server",
            name="Test Integration Server",
            description="Test server for Claude Code integration",
            installation=ServerInstallation(
                method=InstallationMethod.GIT,
                package="https://github.com/octocat/Hello-World.git",
                system_dependencies=["git"],
                python_dependencies=[]
            ),
            category=["test"],
            author="test-author",
            license="MIT",
            versions={"latest": "main"},
            configuration={"required_params": [], "optional_params": []},
            capabilities=["general"],
            platforms=["linux", "darwin", "windows"],
            repository="https://github.com/octocat/Hello-World.git",
            tags=[]
        )
        
        # Test validation
        validation_errors = installer.validate_installation(server)
        print(f"Validation errors: {validation_errors}")
        
        # Test installation
        result = installer.install(server)
        print(f"Install result: {result.status} - {result.message}")
        
        # Check configuration was updated
        updated_config = installer._load_config()
        print(f"Updated config: {updated_config}")
        
        # Test installed servers list
        installed = installer.get_installed_servers()
        print(f"Installed servers: {installed}")


def main():
    """Run all installation tests."""
    print("Testing MCPI Installation Workflows")
    print("=" * 50)
    
    try:
        test_npm_installer()
        test_python_installer()
        test_git_installer()
        test_claude_code_installer()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())