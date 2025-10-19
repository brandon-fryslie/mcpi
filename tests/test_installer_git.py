"""Tests for Git installer."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call
from mcpi.installer.git import GitInstaller
from mcpi.installer.base import InstallationResult, InstallationStatus
from mcpi.registry.catalog import MCPServer, InstallationMethod, ServerInstallation, ServerVersions


class TestGitInstaller:
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.install_dir = self.temp_dir / "servers"
        self.installer = GitInstaller(install_dir=self.install_dir, dry_run=False)
        
        # Test server configuration
        self.test_server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test Git server",
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            license="MIT",
            installation=ServerInstallation(
                method=InstallationMethod.GIT,
                package="https://github.com/test/test-server.git"
            ),
            repository="https://github.com/test/test-server"
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # Basic Installation Tests
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    def test_install_git_not_available(self, mock_git_available):
        """Test installation when Git is not available."""
        mock_git_available.return_value = False
        
        result = self.installer.install(self.test_server)
        
        assert result.failed
        assert "git is not available" in result.message
    
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    def test_install_wrong_method(self, mock_git_available):
        """Test installation with wrong installation method."""
        mock_git_available.return_value = True
        wrong_server = MCPServer(
            id="wrong-server",
            name="Wrong Server",
            description="Server with wrong method",
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            license="MIT",
            installation=ServerInstallation(
                method=InstallationMethod.NPM,
                package="some-package"
            )
        )
        
        result = self.installer.install(wrong_server)
        
        assert result.failed
        assert "not a Git repository" in result.message
    
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    @patch('pathlib.Path.exists')
    def test_install_already_exists(self, mock_path_exists, mock_git_available):
        """Test installation when server already exists."""
        mock_git_available.return_value = True
        mock_path_exists.return_value = True
        
        result = self.installer.install(self.test_server)
        
        assert result.failed
        assert "already installed" in result.message
    
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    @patch('mcpi.installer.git.GitInstaller._clone_repository')
    @patch('mcpi.installer.git.GitInstaller._install_repository_dependencies')
    @patch('mcpi.installer.git.GitInstaller._find_executable_script')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_install_success(self, mock_mkdir, mock_path_exists, mock_find_script, mock_install_deps, mock_clone, mock_git_available):
        """Test successful installation."""
        mock_git_available.return_value = True
        mock_path_exists.return_value = False
        mock_clone.return_value = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Cloned successfully",
            server_id="git_clone"
        )
        mock_install_deps.return_value = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Dependencies installed",
            server_id=self.test_server.id
        )
        mock_find_script.return_value = Path("/fake/script.py")
        
        result = self.installer.install(self.test_server)
        
        assert result.success
        assert "Successfully installed Test Server from Git" in result.message
        assert result.details["repository_url"] == "https://github.com/test/test-server.git"
        mock_mkdir.assert_called_once()
    
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    @patch('mcpi.installer.git.GitInstaller._clone_repository')
    @patch('mcpi.installer.git.GitInstaller._install_repository_dependencies')
    @patch('mcpi.installer.git.GitInstaller._find_executable_script')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_install_with_branch(self, mock_mkdir, mock_path_exists, mock_find_script, mock_install_deps, mock_clone, mock_git_available):
        """Test installation with specific branch."""
        mock_git_available.return_value = True
        mock_path_exists.return_value = False
        mock_clone.return_value = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Cloned successfully",
            server_id="git_clone"
        )
        mock_install_deps.return_value = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Dependencies installed",
            server_id=self.test_server.id
        )
        mock_find_script.return_value = Path("/fake/script.py")
        
        result = self.installer.install(self.test_server, {"branch": "develop"})
        
        assert result.success
        assert result.details["branch"] == "develop"
    
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    @patch('mcpi.installer.git.GitInstaller._clone_repository')
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_install_clone_failure(self, mock_mkdir, mock_path_exists, mock_rmtree, mock_clone, mock_git_available):
        """Test installation cleanup when clone fails."""
        mock_git_available.return_value = True
        mock_path_exists.side_effect = lambda: False  # Not already installed
        mock_clone.return_value = InstallationResult(
            status=InstallationStatus.FAILED,
            message="Clone failed",
            server_id="git_clone"
        )
        
        result = self.installer.install(self.test_server)
        
        assert result.failed
        assert result.message == "Clone failed"
    
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    @patch('mcpi.installer.git.GitInstaller._clone_repository')
    @patch('mcpi.installer.git.GitInstaller._install_repository_dependencies')
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_install_deps_failure_cleanup(self, mock_mkdir, mock_path_exists, mock_rmtree, mock_install_deps, mock_clone, mock_git_available):
        """Test installation cleanup when dependency installation fails."""
        mock_git_available.return_value = True
        mock_path_exists.side_effect = lambda: False  # Not already installed
        mock_clone.return_value = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Cloned successfully",
            server_id="git_clone"
        )
        mock_install_deps.return_value = InstallationResult(
            status=InstallationStatus.FAILED,
            message="Dependencies failed",
            server_id=self.test_server.id
        )
        
        # Mock install_path.exists() to return True for cleanup
        with patch.object(Path, '__truediv__', return_value=Mock(exists=Mock(return_value=True))):
            result = self.installer.install(self.test_server)
        
        assert result.failed
        assert result.message == "Dependencies failed"
        mock_rmtree.assert_called_once()
    
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_install_exception_cleanup(self, mock_mkdir, mock_path_exists, mock_rmtree, mock_git_available):
        """Test installation cleanup on exception."""
        mock_git_available.return_value = True
        mock_path_exists.side_effect = lambda: False  # Not already installed
        
        # Mock install_path.exists() to return True for cleanup
        mock_install_path = Mock()
        mock_install_path.exists.return_value = True
        
        with patch.object(Path, '__truediv__', return_value=mock_install_path), \
             patch.object(self.installer, '_clone_repository', side_effect=Exception("Test error")):
            result = self.installer.install(self.test_server)
        
        assert result.failed
        assert "Git installation error" in result.message
        mock_rmtree.assert_called_once()
    
    # URL Resolution Tests
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    @patch('mcpi.installer.git.GitInstaller._clone_repository')
    @patch('mcpi.installer.git.GitInstaller._install_repository_dependencies')
    @patch('mcpi.installer.git.GitInstaller._find_executable_script')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_install_with_repository_field(self, mock_mkdir, mock_path_exists, mock_find_script, mock_install_deps, mock_clone, mock_git_available):
        """Test installation using server.repository field."""
        mock_git_available.return_value = True
        mock_path_exists.return_value = False
        mock_clone.return_value = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Cloned successfully",
            server_id="git_clone"
        )
        mock_install_deps.return_value = InstallationResult(
            status=InstallationStatus.SUCCESS,
            message="Dependencies installed",
            server_id=self.test_server.id
        )
        mock_find_script.return_value = Path("/fake/script.py")
        
        # Test server with invalid package but valid repository
        test_server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test Git server",
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            license="MIT",
            installation=ServerInstallation(
                method=InstallationMethod.GIT,
                package="invalid-package"
            ),
            repository="https://github.com/test/test-server"
        )
        
        result = self.installer.install(test_server)
        
        assert result.success
        mock_clone.assert_called_once()
        # Verify repository URL was used
        call_args = mock_clone.call_args[0]
        assert call_args[0] == "https://github.com/test/test-server"
    
    @patch('mcpi.installer.git.GitInstaller._check_git_available')
    def test_install_invalid_url(self, mock_git_available):
        """Test installation with invalid repository URL."""
        mock_git_available.return_value = True
        
        # Test server with invalid package and no repository
        test_server = MCPServer(
            id="test-server",
            name="Test Server",
            description="Test Git server",
            author="Test Author",
            versions=ServerVersions(latest="1.0.0", supported=["1.0.0"]),
            license="MIT",
            installation=ServerInstallation(
                method=InstallationMethod.GIT,
                package="invalid-package"
            )
        )
        
        result = self.installer.install(test_server)
        
        assert result.failed
        assert "Invalid repository URL" in result.message
    
    # Dry Run Tests
    def test_install_dry_run(self):
        """Test dry run installation."""
        dry_installer = GitInstaller(install_dir=self.install_dir, dry_run=True)
        
        result = dry_installer.install(self.test_server)
        
        assert result.success
        assert "[DRY RUN]" in result.message
    
    # Uninstall Tests
    @patch('pathlib.Path.exists')
    def test_uninstall_not_installed(self, mock_path_exists):
        """Test uninstalling server that's not installed."""
        mock_path_exists.return_value = False
        
        result = self.installer.uninstall("nonexistent-server")
        
        assert result.failed
        assert "not installed" in result.message
    
    @patch('pathlib.Path.exists')
    @patch('shutil.rmtree')
    def test_uninstall_success(self, mock_rmtree, mock_path_exists):
        """Test successful uninstallation."""
        mock_path_exists.return_value = True
        
        result = self.installer.uninstall("test-server")
        
        assert result.success
        assert "Successfully uninstalled test-server" in result.message
        mock_rmtree.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('shutil.rmtree')
    def test_uninstall_exception(self, mock_rmtree, mock_path_exists):
        """Test uninstall exception handling."""
        mock_path_exists.return_value = True
        mock_rmtree.side_effect = Exception("Permission denied")
        
        result = self.installer.uninstall("test-server")
        
        assert result.failed
        assert "Git uninstallation error" in result.message
    
    def test_uninstall_dry_run(self):
        """Test dry run uninstallation."""
        dry_installer = GitInstaller(install_dir=self.install_dir, dry_run=True)
        
        # Create mock install path that exists
        mock_install_path = Mock()
        mock_install_path.exists.return_value = True
        
        with patch.object(Path, '__truediv__', return_value=mock_install_path):
            result = dry_installer.uninstall("test-server")
        
        assert result.success
    
    # Installation Check Tests
    @patch('pathlib.Path.exists')
    def test_is_installed_true(self, mock_path_exists):
        """Test is_installed returns True when server is installed."""
        server_id = "installed-server"
        
        def exists_side_effect(path_obj):
            path_str = str(path_obj)
            if path_str.endswith("installed-server"):
                return True
            elif path_str.endswith(".git"):
                return True
            return False
        
        mock_path_exists.side_effect = exists_side_effect
        
        assert self.installer.is_installed(server_id) is True
    
    @patch('pathlib.Path.exists')
    def test_is_installed_false_no_directory(self, mock_path_exists):
        """Test is_installed returns False when directory doesn't exist."""
        server_id = "nonexistent-server"
        mock_path_exists.return_value = False
        
        assert self.installer.is_installed(server_id) is False
    
    @patch('pathlib.Path.exists')
    def test_is_installed_false_no_git_dir(self, mock_path_exists):
        """Test is_installed returns False when .git directory doesn't exist."""
        server_id = "not-git-server"
        
        def exists_side_effect(path_obj):
            path_str = str(path_obj)
            if path_str.endswith("not-git-server"):
                return True
            elif path_str.endswith(".git"):
                return False
            return False
        
        mock_path_exists.side_effect = exists_side_effect
        
        assert self.installer.is_installed(server_id) is False
    
    # Installed Servers List Tests
    @patch('pathlib.Path.exists')
    def test_get_installed_servers_empty(self, mock_path_exists):
        """Test get_installed_servers returns empty list when no servers installed."""
        mock_path_exists.return_value = False
        
        result = self.installer.get_installed_servers()
        assert result == []
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_get_installed_servers_with_servers(self, mock_iterdir, mock_path_exists):
        """Test get_installed_servers returns list of installed servers."""
        # Mock install_dir.exists() to return True
        mock_path_exists.return_value = True
        
        # Create mock directory entries with proper .git checking
        server1_path = Mock()
        server1_path.name = "server1"
        server1_path.is_dir.return_value = True
        server1_path.__truediv__ = Mock(return_value=Mock(exists=Mock(return_value=True)))
        
        server2_path = Mock()
        server2_path.name = "server2"
        server2_path.is_dir.return_value = True
        server2_path.__truediv__ = Mock(return_value=Mock(exists=Mock(return_value=True)))
        
        not_git_path = Mock()
        not_git_path.name = "not_git"
        not_git_path.is_dir.return_value = True
        not_git_path.__truediv__ = Mock(return_value=Mock(exists=Mock(return_value=False)))
        
        file_path = Mock()
        file_path.is_dir.return_value = False
        
        mock_iterdir.return_value = [server1_path, server2_path, not_git_path, file_path]
        
        result = self.installer.get_installed_servers()
        assert sorted(result) == ["server1", "server2"]
    
    # Update Server Tests
    @patch('pathlib.Path.exists')
    def test_update_server_not_installed(self, mock_path_exists):
        """Test updating server that's not installed."""
        mock_path_exists.return_value = False
        
        result = self.installer.update_server("nonexistent-server")
        
        assert result.failed
        assert "not installed" in result.message
    
    @patch('mcpi.installer.git.GitInstaller.is_installed')
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_update_server_success(self, mock_git_command, mock_is_installed):
        """Test successful server update."""
        mock_is_installed.return_value = True
        mock_git_command.return_value = subprocess.CompletedProcess(
            args=["git", "pull"],
            returncode=0,
            stdout="Already up to date.",
            stderr=""
        )
        
        result = self.installer.update_server("test-server")
        
        assert result.success
        assert "Successfully updated test-server" in result.message
    
    @patch('mcpi.installer.git.GitInstaller.is_installed')
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_update_server_with_branch(self, mock_git_command, mock_is_installed):
        """Test server update with branch checkout."""
        mock_is_installed.return_value = True
        
        # Mock successful checkout and pull
        mock_git_command.side_effect = [
            subprocess.CompletedProcess(
                args=["git", "checkout", "develop"],
                returncode=0,
                stdout="Switched to branch 'develop'",
                stderr=""
            ),
            subprocess.CompletedProcess(
                args=["git", "pull"],
                returncode=0,
                stdout="Already up to date.",
                stderr=""
            )
        ]
        
        result = self.installer.update_server("test-server", branch="develop")
        
        assert result.success
        assert mock_git_command.call_count == 2
    
    @patch('mcpi.installer.git.GitInstaller.is_installed')
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_update_server_checkout_failed(self, mock_git_command, mock_is_installed):
        """Test server update with failed branch checkout."""
        mock_is_installed.return_value = True
        mock_git_command.return_value = subprocess.CompletedProcess(
            args=["git", "checkout", "nonexistent"],
            returncode=1,
            stdout="",
            stderr="error: pathspec 'nonexistent' did not match any file(s) known to git"
        )
        
        result = self.installer.update_server("test-server", branch="nonexistent")
        
        assert result.failed
        assert "Failed to checkout branch" in result.message
    
    @patch('mcpi.installer.git.GitInstaller.is_installed')
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_update_server_pull_failed(self, mock_git_command, mock_is_installed):
        """Test server update with failed pull."""
        mock_is_installed.return_value = True
        mock_git_command.return_value = subprocess.CompletedProcess(
            args=["git", "pull"],
            returncode=1,
            stdout="",
            stderr="error: Your local changes to the following files would be overwritten by merge"
        )
        
        result = self.installer.update_server("test-server")
        
        assert result.failed
        assert "Git pull failed" in result.message
    
    @patch('mcpi.installer.git.GitInstaller.is_installed')
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_update_server_exception(self, mock_git_command, mock_is_installed):
        """Test server update exception handling."""
        mock_is_installed.return_value = True
        mock_git_command.side_effect = Exception("Git command failed")
        
        result = self.installer.update_server("test-server")
        
        assert result.failed
        assert "Git update error" in result.message
    
    # Server Info Tests
    @patch('pathlib.Path.exists')
    def test_get_server_info_not_installed(self, mock_path_exists):
        """Test get_server_info for non-installed server."""
        mock_path_exists.return_value = False
        
        result = self.installer.get_server_info("nonexistent-server")
        
        assert result is None
    
    @patch('mcpi.installer.git.GitInstaller.is_installed')
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_get_server_info_success(self, mock_git_command, mock_is_installed):
        """Test successful server info retrieval."""
        mock_is_installed.return_value = True
        
        # Mock git commands for branch, remote, and commit info
        mock_git_command.side_effect = [
            subprocess.CompletedProcess(
                args=["git", "branch", "--show-current"],
                returncode=0,
                stdout="main\n",
                stderr=""
            ),
            subprocess.CompletedProcess(
                args=["git", "remote", "get-url", "origin"],
                returncode=0,
                stdout="https://github.com/test/test-server.git\n",
                stderr=""
            ),
            subprocess.CompletedProcess(
                args=["git", "log", "-1", "--format=%H %s"],
                returncode=0,
                stdout="abc123 Latest commit message\n",
                stderr=""
            )
        ]
        
        result = self.installer.get_server_info("test-server")
        
        assert result is not None
        assert result["current_branch"] == "main"
        assert result["remote_url"] == "https://github.com/test/test-server.git"
        assert result["latest_commit"] == "abc123 Latest commit message"
    
    @patch('mcpi.installer.git.GitInstaller.is_installed')
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_get_server_info_git_errors(self, mock_git_command, mock_is_installed):
        """Test server info with git command errors."""
        mock_is_installed.return_value = True
        
        # Mock git commands with errors
        mock_git_command.side_effect = [
            subprocess.CompletedProcess(
                args=["git", "branch", "--show-current"],
                returncode=1,
                stdout="",
                stderr="not a git repository"
            ),
            subprocess.CompletedProcess(
                args=["git", "remote", "get-url", "origin"],
                returncode=1,
                stdout="",
                stderr="no such remote"
            ),
            subprocess.CompletedProcess(
                args=["git", "log", "-1", "--format=%H %s"],
                returncode=1,
                stdout="",
                stderr="bad revision"
            )
        ]
        
        result = self.installer.get_server_info("test-server")
        
        assert result is not None
        assert result["current_branch"] == "unknown"
        assert result["remote_url"] == "unknown"
        assert result["latest_commit"] == "unknown"
    
    @patch('mcpi.installer.git.GitInstaller.is_installed')
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_get_server_info_exception(self, mock_git_command, mock_is_installed):
        """Test server info exception handling."""
        mock_is_installed.return_value = True
        mock_git_command.side_effect = Exception("Git command failed")
        
        result = self.installer.get_server_info("test-server")
        
        assert result is None
    
    # Clone Repository Tests
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_clone_repository_success(self, mock_git_command):
        """Test successful repository cloning."""
        mock_git_command.return_value = subprocess.CompletedProcess(
            args=["git", "clone", "https://github.com/test/repo.git", "/path/to/repo"],
            returncode=0,
            stdout="Cloning into '/path/to/repo'...",
            stderr=""
        )
        
        result = self.installer._clone_repository(
            "https://github.com/test/repo.git",
            Path("/path/to/repo")
        )
        
        assert result.success
        assert "Successfully cloned" in result.message
    
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_clone_repository_with_branch(self, mock_git_command):
        """Test repository cloning with specific branch."""
        mock_git_command.return_value = subprocess.CompletedProcess(
            args=["git", "clone", "-b", "develop", "https://github.com/test/repo.git", "/path/to/repo"],
            returncode=0,
            stdout="Cloning into '/path/to/repo'...",
            stderr=""
        )
        
        result = self.installer._clone_repository(
            "https://github.com/test/repo.git",
            Path("/path/to/repo"),
            branch="develop"
        )
        
        assert result.success
        mock_git_command.assert_called_with([
            "clone", "-b", "develop", 
            "https://github.com/test/repo.git", 
            "/path/to/repo"
        ])
    
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_clone_repository_failed(self, mock_git_command):
        """Test failed repository cloning."""
        mock_git_command.return_value = subprocess.CompletedProcess(
            args=["git", "clone", "https://github.com/test/nonexistent.git", "/path/to/repo"],
            returncode=1,
            stdout="",
            stderr="Repository not found"
        )
        
        result = self.installer._clone_repository(
            "https://github.com/test/nonexistent.git",
            Path("/path/to/repo")
        )
        
        assert result.failed
        assert "Git clone failed" in result.message
    
    @patch('mcpi.installer.git.GitInstaller._run_git_command')
    def test_clone_repository_exception(self, mock_git_command):
        """Test clone repository exception handling."""
        mock_git_command.side_effect = Exception("Network error")
        
        result = self.installer._clone_repository(
            "https://github.com/test/repo.git",
            Path("/path/to/repo")
        )
        
        assert result.failed
        assert "Git clone error" in result.message
    
    # Dependencies Installation Tests
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    def test_install_repository_dependencies_python(self, mock_subprocess, mock_path_exists):
        """Test Python dependencies installation."""
        install_path = Path("/fake/path")
        
        def exists_side_effect(path_obj):
            return str(path_obj).endswith("requirements.txt")
        
        mock_path_exists.side_effect = exists_side_effect
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=["pip", "install", "-r", "requirements.txt"],
            returncode=0,
            stdout="Successfully installed packages",
            stderr=""
        )
        
        result = self.installer._install_repository_dependencies(install_path, self.test_server)
        
        assert result.success
        assert "Python dependencies" in result.message
    
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    def test_install_repository_dependencies_nodejs(self, mock_subprocess, mock_path_exists):
        """Test Node.js dependencies installation."""
        install_path = Path("/fake/path")
        
        def exists_side_effect(path_obj):
            return str(path_obj).endswith("package.json")
        
        mock_path_exists.side_effect = exists_side_effect
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=["npm", "install"],
            returncode=0,
            stdout="added 42 packages",
            stderr=""
        )
        
        result = self.installer._install_repository_dependencies(install_path, self.test_server)
        
        assert result.success
        assert "Node.js dependencies" in result.message
    
    @patch('pathlib.Path.exists')
    def test_install_repository_dependencies_none(self, mock_path_exists):
        """Test no dependencies to install."""
        mock_path_exists.return_value = False
        install_path = Path("/fake/path")
        
        result = self.installer._install_repository_dependencies(install_path, self.test_server)
        
        assert result.success
        assert "No dependencies to install" in result.message
    
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    def test_install_repository_dependencies_python_failed(self, mock_subprocess, mock_path_exists):
        """Test failed Python dependencies installation."""
        install_path = Path("/fake/path")
        
        def exists_side_effect(path_obj):
            return str(path_obj).endswith("requirements.txt")
        
        mock_path_exists.side_effect = exists_side_effect
        mock_subprocess.side_effect = subprocess.SubprocessError("pip failed")
        
        result = self.installer._install_repository_dependencies(install_path, self.test_server)
        
        assert result.failed
        assert "Failed to install Python dependencies" in result.message
    
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    def test_install_repository_dependencies_nodejs_failed(self, mock_subprocess, mock_path_exists):
        """Test failed Node.js dependencies installation."""
        install_path = Path("/fake/path")
        
        def exists_side_effect(path_obj):
            return str(path_obj).endswith("package.json")
        
        mock_path_exists.side_effect = exists_side_effect
        mock_subprocess.side_effect = subprocess.SubprocessError("npm failed")
        
        result = self.installer._install_repository_dependencies(install_path, self.test_server)
        
        assert result.failed
        assert "Failed to install Node.js dependencies" in result.message
    
    def test_install_repository_dependencies_dry_run(self):
        """Test dependencies installation in dry run mode."""
        dry_installer = GitInstaller(install_dir=self.install_dir, dry_run=True)
        install_path = Path("/fake/path")
        
        with patch('pathlib.Path.exists', return_value=True):
            result = dry_installer._install_repository_dependencies(install_path, self.test_server)
        
        assert result.success
        assert "Python dependencies" in result.message
    
    # Find Executable Script Tests
    def test_find_executable_script_main_py(self):
        """Test finding main.py executable script."""
        install_path = self.temp_dir / "test-repo"
        install_path.mkdir()
        
        script = install_path / "main.py"
        script.touch()
        
        result = self.installer._find_executable_script(install_path)
        
        assert result == script
    
    def test_find_executable_script_in_src(self):
        """Test finding executable script in src directory."""
        install_path = self.temp_dir / "test-repo"
        install_path.mkdir()
        
        src_dir = install_path / "src"
        src_dir.mkdir()
        script = src_dir / "server.py"
        script.touch()
        
        result = self.installer._find_executable_script(install_path)
        
        assert result == script
    
    def test_find_executable_script_not_found(self):
        """Test when no executable script is found."""
        install_path = self.temp_dir / "test-repo"
        install_path.mkdir()
        
        result = self.installer._find_executable_script(install_path)
        
        assert result is None
    
    def test_find_executable_script_multiple_candidates(self):
        """Test finding executable script when multiple candidates exist."""
        install_path = self.temp_dir / "test-repo"
        install_path.mkdir()
        
        # Create multiple scripts - should find the first one in priority order
        (install_path / "app.py").touch()
        (install_path / "main.py").touch()  # This should be found first
        
        result = self.installer._find_executable_script(install_path)
        
        assert result == install_path / "main.py"
    
    # Git Availability Check Tests
    @patch('subprocess.run')
    def test_check_git_available_true(self, mock_subprocess):
        """Test Git availability check when Git is available."""
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=["git", "--version"],
            returncode=0,
            stdout="git version 2.39.0",
            stderr=""
        )
        
        assert self.installer._check_git_available() is True
    
    @patch('subprocess.run')
    def test_check_git_available_false_not_found(self, mock_subprocess):
        """Test Git availability check when Git is not found."""
        mock_subprocess.side_effect = FileNotFoundError("git command not found")
        
        assert self.installer._check_git_available() is False
    
    @patch('subprocess.run')
    def test_check_git_available_false_error(self, mock_subprocess):
        """Test Git availability check when Git returns error."""
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=["git", "--version"],
            returncode=1,
            stdout="",
            stderr="git: command not found"
        )
        
        assert self.installer._check_git_available() is False
    
    @patch('subprocess.run')
    def test_check_git_available_timeout(self, mock_subprocess):
        """Test Git availability check timeout."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired("git", 10)
        
        assert self.installer._check_git_available() is False
    
    # Git Command Execution Tests
    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_subprocess):
        """Test successful git command execution."""
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=["git", "status"],
            returncode=0,
            stdout="On branch main",
            stderr=""
        )
        
        result = self.installer._run_git_command(["status"])
        
        assert result.returncode == 0
        assert "On branch main" in result.stdout
    
    @patch('subprocess.run')
    def test_run_git_command_with_cwd(self, mock_subprocess):
        """Test git command execution with working directory."""
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=["git", "status"],
            returncode=0,
            stdout="On branch main",
            stderr=""
        )
        
        cwd = Path("/fake/path")
        result = self.installer._run_git_command(["status"], cwd=cwd)
        
        mock_subprocess.assert_called_with(
            ["git", "status"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
    
    def test_run_git_command_dry_run(self):
        """Test git command in dry run mode."""
        dry_installer = GitInstaller(install_dir=self.install_dir, dry_run=True)
        
        result = dry_installer._run_git_command(["status"])
        
        assert result.returncode == 0
        assert "[DRY RUN]" in result.stdout
        assert "git status" in result.stdout
    
    # Method Support Tests
    def test_supports_method_git(self):
        """Test that installer supports Git method."""
        assert self.installer._supports_method(InstallationMethod.GIT) is True
    
    def test_supports_method_other(self):
        """Test that installer doesn't support non-Git methods."""
        assert self.installer._supports_method(InstallationMethod.NPM) is False
        assert self.installer._supports_method(InstallationMethod.PYTHON) is False