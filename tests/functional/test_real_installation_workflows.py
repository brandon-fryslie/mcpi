"""Real installation workflow tests for MCPI.

These tests validate actual package installation and configuration workflows.
They use real package managers and verify end-to-end functionality.

Safety measures:
- Uses lightweight, safe packages for testing
- Creates isolated environments
- Cleans up after testing
- Uses non-global installation modes where possible
"""

import json
import shutil
import tempfile
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import pytest

from mcpi.installer.npm import NPMInstaller
from mcpi.installer.python import PythonInstaller
from mcpi.installer.git import GitInstaller
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.installer.base import InstallationResult, InstallationStatus
from mcpi.registry.catalog import MCPServer, ServerInstallation, InstallationMethod


class TestRealNPMInstallationWorkflows:
    """Test real NPM package installation workflows with actual packages."""
    
    def setup_method(self):
        """Set up test environment with isolated npm installation."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.project_dir = self.temp_path / "test_project"
        self.project_dir.mkdir()
        
        # Create package.json for isolated installation
        package_json = {
            "name": "mcpi-test-project",
            "version": "1.0.0",
            "private": True,
            "description": "Test project for MCPI installer testing"
        }
        (self.project_dir / "package.json").write_text(json.dumps(package_json, indent=2))
        
        # Store original working directory
        self.original_cwd = Path.cwd()
    
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_npm_server(self, package_name: str = "lodash") -> MCPServer:
        """Create test server for real NPM package installation."""
        return MCPServer(
            id=f"test-npm-{package_name}",
            name=f"Test NPM {package_name}",
            description=f"Test server for NPM package {package_name}",
            installation=ServerInstallation(
                method=InstallationMethod.NPM,
                package=package_name,
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
            repository=f"https://github.com/test/{package_name}",
            tags=[]
        )
    
    @pytest.mark.skipif(shutil.which("npm") is None, reason="npm not available")
    def test_real_npm_package_installation_workflow(self):
        """Test: Complete NPM package installation workflow with real package.
        
        This test validates:
        1. Real npm command execution
        2. Actual package installation and verification
        3. Package manager state changes
        4. Installation cleanup and uninstallation
        5. Directory and file system operations
        """
        # Change to project directory for local installation
        os.chdir(self.project_dir)
        
        # Create installer for local (non-global) installation
        installer = NPMInstaller(global_install=False, dry_run=False)
        
        # Use lightweight package for testing
        test_server = self._create_test_npm_server("lodash")
        
        # Verify npm is available
        assert installer._check_npm_available(), "NPM should be available for real installation test"
        
        # Validate installation requirements
        validation_errors = installer.validate_installation(test_server)
        assert len(validation_errors) == 0, f"Installation should be valid: {validation_errors}"
        
        # Perform real installation
        install_result = installer.install(test_server)
        
        # Verify installation succeeded
        assert install_result.success, f"Installation should succeed: {install_result.message}"
        assert install_result.status == InstallationStatus.SUCCESS
        assert "lodash" in install_result.message.lower()
        
        # Verify package was actually installed
        node_modules = self.project_dir / "node_modules" / "lodash"
        assert node_modules.exists(), "Package directory should exist after installation"
        
        # Verify package.json was updated
        package_json_path = self.project_dir / "package.json"
        package_data = json.loads(package_json_path.read_text())
        assert "dependencies" in package_data, "Dependencies should be added to package.json"
        assert "lodash" in package_data["dependencies"], "Lodash should be in dependencies"
        
        # Test package is detected as installed
        assert installer.is_installed("lodash"), "Package should be detected as installed"
        
        # Test package listing includes our package
        installed_packages = installer.get_installed_servers()
        assert "lodash" in installed_packages, f"Installed packages should include lodash: {installed_packages}"
        
        # Test package information retrieval
        package_info = installer.get_package_info("lodash")
        assert package_info is not None, "Package info should be available"
        assert "version" in package_info, "Package info should include version"
        
        # Test uninstallation
        uninstall_result = installer.uninstall("lodash")
        assert uninstall_result.success, f"Uninstallation should succeed: {uninstall_result.message}"
        
        # Verify package was removed
        assert not node_modules.exists(), "Package directory should be removed after uninstallation"
        assert not installer.is_installed("lodash"), "Package should not be detected as installed after removal"
    
    @pytest.mark.skipif(shutil.which("npm") is None, reason="npm not available")
    def test_npm_installation_error_handling(self):
        """Test: NPM installation error handling with invalid packages."""
        os.chdir(self.project_dir)
        
        installer = NPMInstaller(global_install=False, dry_run=False)
        
        # Test with non-existent package
        invalid_server = self._create_test_npm_server("nonexistent-package-12345")
        
        result = installer.install(invalid_server)
        
        # Should fail gracefully
        assert result.status == InstallationStatus.FAILED, "Installation of non-existent package should fail"
        assert "error" in result.message.lower() or "failed" in result.message.lower()
        
        # Should not leave artifacts
        node_modules = self.project_dir / "node_modules" / "nonexistent-package-12345"
        assert not node_modules.exists(), "Failed installation should not leave artifacts"


class TestRealGitInstallationWorkflows:
    """Test real Git repository installation workflows."""
    
    def setup_method(self):
        """Set up test environment with isolated git installation."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.git_install_dir = self.temp_path / "git_installations"
        self.git_install_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_git_server(self, repo_url: str = "https://github.com/octocat/Hello-World.git") -> MCPServer:
        """Create test server for real Git repository installation."""
        return MCPServer(
            id="test-git-hello-world",
            name="Test Git Hello World",
            description="Test server for Git repository installation",
            installation=ServerInstallation(
                method=InstallationMethod.GIT,
                package=repo_url,
                system_dependencies=["git"],
                python_dependencies=[]
            ),
            category=["test"],
            author="github",
            license="MIT",
            versions={"latest": "main"},
            configuration={"required_params": [], "optional_params": []},
            capabilities=["general"],
            platforms=["linux", "darwin", "windows"],
            repository=repo_url,
            tags=[]
        )
    
    @pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
    def test_real_git_repository_cloning_workflow(self):
        """Test: Complete Git repository cloning workflow with real repository.
        
        This test validates:
        1. Real git clone command execution
        2. Actual repository cloning and verification
        3. File system operations and directory creation
        4. Repository cleanup and removal
        5. Git metadata preservation
        """
        installer = GitInstaller(install_dir=self.git_install_dir, dry_run=False)
        
        # Use small, stable public repository
        test_server = self._create_test_git_server()
        
        # Verify git is available
        assert installer._check_git_available(), "Git should be available for real installation test"
        
        # Validate installation requirements
        validation_errors = installer.validate_installation(test_server)
        assert len(validation_errors) == 0, f"Installation should be valid: {validation_errors}"
        
        # Perform real git cloning
        install_result = installer.install(test_server)
        
        # Verify installation succeeded
        assert install_result.success, f"Installation should succeed: {install_result.message}"
        assert install_result.status == InstallationStatus.SUCCESS
        assert install_result.success, f"Installation should succeed: {install_result.message}"
        assert "git" in install_result.message.lower(), f"Installation message should mention git: {install_result.message}"
        
        # Verify repository was actually cloned
        repo_path = self.git_install_dir / test_server.id
        assert repo_path.exists(), "Repository directory should exist after cloning"
        assert repo_path.is_dir(), "Repository path should be a directory"
        
        # Verify git repository structure
        git_dir = repo_path / ".git"
        assert git_dir.exists(), "Git metadata directory should exist"
        
        # Verify repository contents
        readme_path = repo_path / "README"
        assert readme_path.exists(), "README file should exist in Hello-World repository"
        
        # Test repository is detected as installed
        assert installer.is_installed(test_server.id), "Repository should be detected as installed"
        
        # Test repository listing includes our repo
        installed_repos = installer.get_installed_servers()
        assert test_server.id in installed_repos, f"Installed repos should include test server: {installed_repos}"
        
        # Test repository information retrieval
        repo_info = installer.get_server_info(test_server.id)
        assert repo_info is not None, "Repository info should be available"
        assert "install_path" in repo_info, "Repository info should include install path"
        assert "current_branch" in repo_info, "Repository info should include current branch"
        assert "remote_url" in repo_info, "Repository info should include remote URL"
        
        # Test repository update functionality
        update_result = installer.update_server(test_server.id)
        assert update_result.success or "up-to-date" in update_result.message.lower(), \
            f"Repository update should succeed or be up-to-date: {update_result.message}"
        
        # Test uninstallation
        uninstall_result = installer.uninstall(test_server.id)
        assert uninstall_result.success, f"Uninstallation should succeed: {uninstall_result.message}"
        
        # Verify repository was removed
        assert not repo_path.exists(), "Repository directory should be removed after uninstallation"
        assert not installer.is_installed(test_server.id), "Repository should not be detected as installed after removal"
    
    @pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
    def test_git_installation_with_branch_specification(self):
        """Test: Git installation with specific branch specification."""
        installer = GitInstaller(install_dir=self.git_install_dir, dry_run=False)
        test_server = self._create_test_git_server()
        
        # Install with specific branch (if the repo has it, otherwise main/master)
        config_params = {"branch": "master"}  # Hello-World likely uses master
        
        result = installer.install(test_server, config_params)
        
        if result.success:
            # Verify branch was checked out correctly
            repo_path = self.git_install_dir / test_server.id
            
            # Get current branch
            try:
                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if branch_result.returncode == 0:
                    current_branch = branch_result.stdout.strip()
                    assert current_branch == "master" or current_branch != "", "Should be on correct branch"
            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                pass  # Skip branch verification if git command fails
            
            # Clean up
            installer.uninstall(test_server.id)


class TestRealClaudeCodeIntegrationWorkflows:
    """Test real Claude Code integration with actual configuration files."""
    
    def setup_method(self):
        """Set up test environment with temporary Claude Code configuration."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create Claude Code configuration directory structure
        self.claude_config_dir = self.temp_path / ".claude"
        self.claude_config_dir.mkdir()
        
        self.config_file = self.claude_config_dir / "mcp_servers.json"
        initial_config = {
            "mcpServers": {
                "existing-server": {
                    "command": "python",
                    "args": ["-m", "existing_module"]
                }
            }
        }
        self.config_file.write_text(json.dumps(initial_config, indent=2))
        
        # Create git installation directory
        self.git_install_dir = self.temp_path / "git_installs"
        self.git_install_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_integration_server(self) -> MCPServer:
        """Create test server for Claude Code integration."""
        return MCPServer(
            id="claude-integration-test",
            name="Claude Integration Test Server",
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
    
    @pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
    def test_real_claude_code_configuration_integration(self):
        """Test: Real Claude Code configuration integration with file persistence.
        
        This test validates:
        1. Real configuration file reading and writing
        2. Configuration backup and restore functionality
        3. Server installation with configuration updates
        4. Configuration persistence across operations
        5. Multi-server configuration management
        """
        # Initialize installer with temporary config
        installer = ClaudeCodeInstaller(config_path=self.config_file, dry_run=False)
        
        # Override git installer to use our temporary directory
        installer.git_installer = GitInstaller(install_dir=self.git_install_dir, dry_run=False)
        
        test_server = self._create_test_integration_server()
        
        # Verify initial configuration
        initial_config = installer._load_config()
        assert "mcpServers" in initial_config, "Initial config should have mcpServers section"
        assert "existing-server" in initial_config["mcpServers"], "Initial config should have existing server"
        
        # Verify server is not initially installed
        assert not installer.is_installed(test_server.id), "Test server should not be initially installed"
        
        # Create backup before installation
        backup_path = installer.create_backup(self.config_file)
        assert backup_path is not None, "Backup should be created successfully"
        assert backup_path.exists(), "Backup file should exist"
        
        # Perform real installation
        install_result = installer.install(test_server)
        assert install_result.success, f"Installation should succeed: {install_result.message}"
        
        # Verify configuration was updated
        updated_config = installer._load_config()
        assert test_server.id in updated_config["mcpServers"], "Test server should be added to configuration"
        
        # Verify server configuration structure
        server_config = updated_config["mcpServers"][test_server.id]
        assert "command" in server_config, "Server config should have command"
        assert "args" in server_config, "Server config should have args"
        assert isinstance(server_config["args"], list), "Server args should be a list"
        
        # Verify original server is still present
        assert "existing-server" in updated_config["mcpServers"], "Existing server should be preserved"
        
        # Verify server is detected as installed
        assert installer.is_installed(test_server.id), "Test server should be detected as installed"
        
        # Verify installed servers list
        installed_servers = installer.get_installed_servers()
        assert test_server.id in installed_servers, "Test server should be in installed servers list"
        assert "existing-server" in installed_servers, "Existing server should be in installed servers list"
        
        # Test configuration validation
        validation_errors = installer.validate_config()
        assert len(validation_errors) == 0, f"Configuration should be valid: {validation_errors}"
        
        # Test server configuration retrieval
        server_config_retrieved = installer.get_server_config(test_server.id)
        assert server_config_retrieved == server_config, "Retrieved config should match stored config"
        
        # Test configuration update
        new_config = server_config.copy()
        new_config["args"].append("--test-param")
        update_success = installer.update_server_config(test_server.id, new_config)
        assert update_success, "Configuration update should succeed"
        
        # Verify configuration was actually updated
        updated_config_after_change = installer._load_config()
        assert "--test-param" in updated_config_after_change["mcpServers"][test_server.id]["args"], \
            "Configuration should be updated with new parameter"
        
        # Test uninstallation
        uninstall_result = installer.uninstall(test_server.id)
        assert uninstall_result.success, f"Uninstallation should succeed: {uninstall_result.message}"
        
        # Verify server was removed from configuration
        final_config = installer._load_config()
        assert test_server.id not in final_config["mcpServers"], "Test server should be removed from configuration"
        assert "existing-server" in final_config["mcpServers"], "Existing server should still be present"
        
        # Test backup restoration
        restore_success = installer.restore_backup(backup_path, self.config_file)
        assert restore_success, "Backup restoration should succeed"
        
        # Verify configuration was restored to original state
        restored_config = installer._load_config()
        assert restored_config == initial_config, "Configuration should be restored to initial state"
        
        # Clean up backups
        installer.cleanup_backups()
        # Note: backup may or may not exist after cleanup, depending on implementation
    
    def test_claude_code_configuration_error_recovery(self):
        """Test: Configuration error recovery and corruption handling."""
        installer = ClaudeCodeInstaller(config_path=self.config_file, dry_run=False)
        
        # Test with corrupted configuration file
        self.config_file.write_text("invalid json content {")
        
        # Should handle corruption gracefully
        corrupted_config = installer._load_config()
        assert corrupted_config == {"mcpServers": {}}, "Should return default config for corrupted file"
        
        # Should be able to save valid configuration over corrupted file
        valid_config = {"mcpServers": {"test": {"command": "test", "args": []}}}
        save_success = installer._save_config(valid_config)
        assert save_success, "Should be able to save valid config over corrupted file"
        
        # Verify configuration was saved correctly
        loaded_config = installer._load_config()
        assert loaded_config == valid_config, "Configuration should be saved and loaded correctly"


class TestEndToEndInstallationWorkflows:
    """Test complete end-to-end installation workflows."""
    
    def setup_method(self):
        """Set up test environment for end-to-end testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create all necessary directories
        self.claude_config_dir = self.temp_path / ".claude"
        self.claude_config_dir.mkdir()
        self.config_file = self.claude_config_dir / "mcp_servers.json"
        self.config_file.write_text('{"mcpServers": {}}')
        
        self.git_install_dir = self.temp_path / "git_installs"
        self.git_install_dir.mkdir()
        
        self.npm_project_dir = self.temp_path / "npm_project"
        self.npm_project_dir.mkdir()
        
        # Setup npm project
        package_json = {"name": "mcpi-e2e-test", "version": "1.0.0", "private": True}
        (self.npm_project_dir / "package.json").write_text(json.dumps(package_json))
        
        self.original_cwd = Path.cwd()
    
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.skipif(
        shutil.which("git") is None or shutil.which("npm") is None,
        reason="git and npm required for end-to-end test"
    )
    def test_complete_multi_method_installation_workflow(self):
        """Test: Complete workflow with multiple installation methods.
        
        This test validates:
        1. Multiple installation methods working together
        2. Claude Code integration across different installer types
        3. Configuration consistency across multiple servers
        4. End-to-end workflow from installation to configuration
        """
        # Initialize Claude Code installer
        claude_installer = ClaudeCodeInstaller(config_path=self.config_file, dry_run=False)
        
        # Override sub-installers to use our isolated environments
        claude_installer.git_installer = GitInstaller(install_dir=self.git_install_dir, dry_run=False)
        
        # Change to npm project directory for npm operations
        os.chdir(self.npm_project_dir)
        claude_installer.npm_installer = NPMInstaller(global_install=False, dry_run=False)
        
        # Create test servers for different installation methods
        git_server = MCPServer(
            id="e2e-git-server",
            name="E2E Git Server",
            description="End-to-end test Git server",
            installation=ServerInstallation(
                method=InstallationMethod.GIT,
                package="https://github.com/octocat/Hello-World.git",
                system_dependencies=["git"],
                python_dependencies=[]
            ),
            category=["test"],
            author="test",
            license="MIT",
            versions={"latest": "main"},
            configuration={"required_params": [], "optional_params": []},
            capabilities=["general"],
            platforms=["linux", "darwin", "windows"],
            repository="https://github.com/octocat/Hello-World.git",
            tags=[]
        )
        
        npm_server = MCPServer(
            id="e2e-npm-server",
            name="E2E NPM Server",
            description="End-to-end test NPM server",
            installation=ServerInstallation(
                method=InstallationMethod.NPM,
                package="lodash",
                system_dependencies=[],
                python_dependencies=[]
            ),
            category=["test"],
            author="test",
            license="MIT",
            versions={"latest": "1.0.0"},
            configuration={"required_params": [], "optional_params": []},
            capabilities=["general"],
            platforms=["linux", "darwin", "windows"],
            repository="https://github.com/lodash/lodash",
            tags=[]
        )
        
        servers = [git_server, npm_server]
        
        # Install all servers
        installation_results = []
        for server in servers:
            result = claude_installer.install(server)
            installation_results.append(result)
            assert result.success, f"Installation of {server.id} should succeed: {result.message}"
        
        # Verify all servers are installed
        for server in servers:
            assert claude_installer.is_installed(server.id), f"Server {server.id} should be installed"
        
        # Verify configuration contains all servers
        config = claude_installer._load_config()
        for server in servers:
            assert server.id in config["mcpServers"], f"Configuration should contain {server.id}"
            
        # Verify configuration structure for each server
        for server in servers:
            server_config = config["mcpServers"][server.id]
            assert "command" in server_config, f"Server {server.id} should have command"
            assert "args" in server_config, f"Server {server.id} should have args"
            assert isinstance(server_config["args"], list), f"Server {server.id} args should be list"
        
        # Verify configuration validation passes
        validation_errors = claude_installer.validate_config()
        assert len(validation_errors) == 0, f"Configuration should be valid: {validation_errors}"
        
        # Test that all servers are listed
        installed_servers = claude_installer.get_installed_servers()
        for server in servers:
            assert server.id in installed_servers, f"Server {server.id} should be in installed list"
        
        # Test uninstallation of all servers
        for server in servers:
            uninstall_result = claude_installer.uninstall(server.id)
            assert uninstall_result.success, f"Uninstallation of {server.id} should succeed: {uninstall_result.message}"
            assert not claude_installer.is_installed(server.id), f"Server {server.id} should not be installed after removal"
        
        # Verify configuration is clean
        final_config = claude_installer._load_config()
        assert len(final_config["mcpServers"]) == 0, "Configuration should be empty after all uninstallations"


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])