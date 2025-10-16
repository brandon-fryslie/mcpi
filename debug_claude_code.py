#!/usr/bin/env python3
"""Debug Claude Code installer configuration saving."""

import sys
import tempfile
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.registry.catalog import MCPServer, ServerInstallation, InstallationMethod


def debug_config_saving():
    """Debug configuration saving in Claude Code installer."""
    
    # Create temporary config file
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "mcp_servers.json"
        initial_config = {"mcpServers": {}}
        config_file.write_text(json.dumps(initial_config, indent=2))
        
        print(f"Config file: {config_file}")
        print(f"Initial content: {config_file.read_text()}")
        
        # Create installer in dry run mode first
        installer = ClaudeCodeInstaller(config_path=config_file, dry_run=True)
        print(f"Installer dry_run: {installer.dry_run}")
        
        # Test config loading
        loaded_config = installer._load_config()
        print(f"Loaded config: {loaded_config}")
        
        # Test config saving in dry run mode
        test_config = {"mcpServers": {"test-server": {"command": "test", "args": []}}}
        save_result = installer._save_config(test_config)
        print(f"Save result (dry run): {save_result}")
        print(f"File content after dry run save: {config_file.read_text()}")
        
        # Test config saving in real mode
        real_installer = ClaudeCodeInstaller(config_path=config_file, dry_run=False)
        real_save_result = real_installer._save_config(test_config)
        print(f"Save result (real): {real_save_result}")
        print(f"File content after real save: {config_file.read_text()}")
        
        # Test full installation workflow
        server = MCPServer(
            id="debug-server",
            name="Debug Server", 
            description="Server for debugging",
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
        
        print("\n--- Testing full installation workflow ---")
        
        # Reset config
        config_file.write_text(json.dumps(initial_config, indent=2))
        print(f"Reset config: {config_file.read_text()}")
        
        # Test installation with non-dry-run mode
        result = real_installer.install(server)
        print(f"Installation result: {result.status} - {result.message}")
        print(f"Config after install: {config_file.read_text()}")
        
        # Check if server is tracked
        is_installed = real_installer.is_installed(server.id)
        print(f"Is installed: {is_installed}")
        
        installed_servers = real_installer.get_installed_servers()
        print(f"Installed servers: {installed_servers}")


if __name__ == "__main__":
    debug_config_saving()