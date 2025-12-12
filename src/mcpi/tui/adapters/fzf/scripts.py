"""Console script entry points for fzf TUI.

These functions are called by mcpi-tui-reload and mcpi-tui-cycle-scope
console scripts defined in pyproject.toml.
"""

import sys
from typing import Optional

from mcpi.clients.manager import MCPManager, create_default_manager
from mcpi.registry.catalog import ServerCatalog
from mcpi.registry.catalog_manager import create_default_catalog_manager

from .adapter import FzfAdapter


def reload_server_list(
    catalog: Optional[ServerCatalog] = None, manager: Optional[MCPManager] = None
) -> None:
    """Reload and output server list for fzf.

    Used by fzf bindings to refresh the list after operations.
    Outputs formatted server list to stdout.

    Args:
        catalog: ServerCatalog instance (created if not provided)
        manager: MCPManager instance (created if not provided)
    """
    try:
        if catalog is None:
            catalog_manager = create_default_catalog_manager()
            catalog = catalog_manager.get_catalog("official")

        if manager is None:
            manager = create_default_manager()

        adapter = FzfAdapter()
        lines = adapter._build_server_list(catalog, manager)
        for line in lines:
            print(line)
    except Exception as e:
        print(f"Error reloading server list: {e}", file=sys.stderr)
        print("[ ] error - Failed to reload server list")


def cycle_scope_and_reload(
    catalog: Optional[ServerCatalog] = None, manager: Optional[MCPManager] = None
) -> None:
    """Cycle to next scope and reload server list.

    Used by fzf ctrl-s binding to cycle through scopes.
    Outputs formatted server list to stdout with updated scope.

    Args:
        catalog: ServerCatalog instance (created if not provided)
        manager: MCPManager instance (created if not provided)
    """
    try:
        if manager is None:
            manager = create_default_manager()

        adapter = FzfAdapter()
        current = adapter._get_current_scope()
        available = adapter._get_available_scopes(manager)

        next_scope = adapter._set_next_scope(current, available)
        print(f"Switched to scope: {next_scope}", file=sys.stderr)

        reload_server_list(catalog, manager)

    except Exception as e:
        print(f"Error cycling scope: {e}", file=sys.stderr)
        reload_server_list(catalog, manager)
