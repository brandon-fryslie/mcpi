"""TUI Package - Interactive terminal UI for MCPI.

This package provides interactive terminal user interfaces for managing MCP servers.
It uses a plugin architecture to support multiple TUI backends (fzf, InquirerPy, etc.).

Public API:
- get_tui_adapter(): Factory function to create TUI adapter instances
- launch_fzf_interface(): Launch the fzf TUI interface
"""

from typing import Optional

from mcpi.clients import MCPManager
from mcpi.registry.catalog import ServerCatalog
from mcpi.tui.factory import get_tui_adapter

# Re-export standalone functions for console scripts
from mcpi.tui.adapters.fzf import cycle_scope_and_reload, reload_server_list

__all__ = [
    "get_tui_adapter",
    "launch_fzf_interface",
    "reload_server_list",
    "cycle_scope_and_reload",
]


def launch_fzf_interface(
    manager: MCPManager,
    catalog: ServerCatalog,
    initial_scope: Optional[str] = None,
) -> None:
    """Launch the interactive fzf interface.

    Args:
        manager: MCP manager instance
        catalog: Server catalog instance
        initial_scope: Starting scope (optional)

    Raises:
        RuntimeError: If fzf is not installed
    """
    adapter = get_tui_adapter("fzf")
    adapter.launch(manager, catalog, initial_scope)
