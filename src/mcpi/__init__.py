"""MCP Manager (mcpi) - A comprehensive tool for managing Model Context Protocol servers."""

__version__ = "0.1.0"
__author__ = "Brandon Fryslie"
__email__ = "nunya@hotmail.com"

from mcpi.registry.catalog import ServerCatalog
from mcpi.config.manager import ConfigManager

__all__ = ["ServerCatalog", "ConfigManager"]