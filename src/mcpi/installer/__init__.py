"""Installation module for MCP servers."""

from mcpi.installer.base import BaseInstaller, InstallationResult
from mcpi.installer.claude_code import ClaudeCodeInstaller
from mcpi.installer.npm import NPMInstaller
from mcpi.installer.python import PythonInstaller
from mcpi.installer.git import GitInstaller

__all__ = [
    "BaseInstaller", 
    "InstallationResult",
    "ClaudeCodeInstaller", 
    "NPMInstaller", 
    "PythonInstaller", 
    "GitInstaller"
]