"""SimpleMenuAdapter - simple-term-menu based TUI implementation.

Pure Python interactive menu for managing MCP servers.
Uses simple-term-menu for fuzzy search and selection.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console
from simple_term_menu import TerminalMenu

from mcpi.clients.manager import MCPManager
from mcpi.clients.types import ServerState
from mcpi.config import load_mcpi_config
from mcpi.registry.catalog import MCPServer, ServerCatalog

console = Console()


class SimpleMenuAdapter:
    """Simple terminal menu adapter for MCPI.

    Provides a straightforward flow:
    1. Select scope
    2. Select server (with fuzzy search)
    3. Select action
    4. Execute
    """

    def __init__(self, manager: MCPManager, catalog: ServerCatalog):
        """Initialize adapter.

        Args:
            manager: MCPManager instance
            catalog: ServerCatalog instance
        """
        self.manager = manager
        self.catalog = catalog

    def launch(self, initial_scope: Optional[str] = None) -> None:
        """Launch interactive menu.

        Args:
            initial_scope: Starting scope (prompts if not provided)
        """
        # Get writable scopes
        scopes = self._get_writable_scopes()
        if not scopes:
            console.print("[red]No writable scopes available[/red]")
            return

        scope_names = [s["name"] for s in scopes]

        # Try to find a scope: CLI arg > .mcpi config > prompt
        scope = None
        if initial_scope and initial_scope in scope_names:
            scope = initial_scope
        else:
            # Check for project default
            default_scope = self._get_default_scope()
            if default_scope and default_scope in scope_names:
                scope = default_scope
                console.print(f"[dim]Using default scope from mcpi.toml: {scope}[/dim]")

        # Still no scope? Prompt user
        if scope is None:
            scope = self._select_scope(scopes)
            if scope is None:
                return

        # Main loop
        while True:
            result = self._main_menu(scope)
            if result == "quit":
                break
            elif result == "change_scope":
                new_scope = self._select_scope(scopes)
                if new_scope:
                    scope = new_scope

    def _get_writable_scopes(self) -> List[dict]:
        """Get list of writable scopes with their info."""
        scopes_info = self.manager.get_scopes_for_client(self.manager.default_client)
        return [s for s in scopes_info if not s.get("readonly", False)]

    def _get_default_scope(self) -> Optional[str]:
        """Get default scope from config.

        Returns:
            Default scope name or None
        """
        config = load_mcpi_config()
        return config.get("default_scope")

    def _select_scope(self, scopes: List[dict]) -> Optional[str]:
        """Prompt user to select a scope.

        Args:
            scopes: Available scope info dicts

        Returns:
            Selected scope name or None if cancelled
        """
        # Format: "scope-name (path)"
        menu_items = []
        home = str(Path.home())
        for s in scopes:
            path = s.get("path", "")
            if path:
                # Shorten home directory
                path = path.replace(home, "~")
                menu_items.append(f"{s['name']} ({path})")
            else:
                menu_items.append(s["name"])

        menu = TerminalMenu(
            menu_items,
            title="Select target scope:",
            search_key="/",
            show_search_hint=True,
        )
        index = menu.show()
        return scopes[index]["name"] if index is not None else None

    def _main_menu(self, scope: str) -> str:
        """Show main menu and handle selection.

        Args:
            scope: Current target scope

        Returns:
            "quit", "change_scope", or "continue"
        """
        # Build server list with status indicators
        servers = self._get_servers_with_status()
        if not servers:
            console.print("[yellow]No servers in catalog[/yellow]")
            return "quit"

        # Format for display
        menu_items = []
        for server_id, server, state in servers:
            if state == ServerState.ENABLED:
                prefix = "[✓]"
            elif state == ServerState.DISABLED:
                prefix = "[✗]"
            else:
                prefix = "[ ]"
            menu_items.append(f"{prefix} {server_id} - {server.description[:60]}")

        # Add navigation options at the end
        menu_items.extend([
            "─" * 40,  # Separator
            "⚙ Change scope",
            "✕ Quit",
        ])

        menu = TerminalMenu(
            menu_items,
            title=f"MCP Servers (scope: {scope}) - Press / to search",
            search_key="/",
            show_search_hint=True,
        )
        index = menu.show()

        if index is None:
            return "quit"

        # Handle navigation options
        if index == len(menu_items) - 1:  # Quit
            return "quit"
        if index == len(menu_items) - 2:  # Change scope
            return "change_scope"
        if index == len(menu_items) - 3:  # Separator
            return "continue"

        # Handle server selection
        server_id, server, state = servers[index]
        return self._handle_server_action(server_id, server, state, scope)

    def _get_servers_with_status(self) -> List[Tuple[str, MCPServer, ServerState]]:
        """Get all servers with their current state.

        Returns:
            List of (server_id, server, state) tuples, sorted by state
        """
        servers = self.catalog.list_servers()
        result = []

        for server_id, server in servers:
            state = self.manager.get_server_state(server_id)
            result.append((server_id, server, state))

        # Sort: enabled first, then disabled, then not installed
        def sort_key(item):
            _, _, state = item
            if state == ServerState.ENABLED:
                return 0
            elif state == ServerState.DISABLED:
                return 1
            return 2

        result.sort(key=sort_key)
        return result

    def _handle_server_action(
        self, server_id: str, server: MCPServer, state: ServerState, scope: str
    ) -> str:
        """Show action menu for selected server.

        Args:
            server_id: Server identifier
            server: Server catalog entry
            state: Current server state
            scope: Target scope

        Returns:
            "continue" to keep looping
        """
        # Build available actions based on state
        actions = []
        action_map = {}

        if state == ServerState.NOT_INSTALLED:
            actions.append("Install")
            action_map["Install"] = "add"
        elif state == ServerState.ENABLED:
            actions.append("Disable")
            action_map["Disable"] = "disable"
            actions.append("Remove")
            action_map["Remove"] = "remove"
        elif state == ServerState.DISABLED:
            actions.append("Enable")
            action_map["Enable"] = "enable"
            actions.append("Remove")
            action_map["Remove"] = "remove"

        actions.append("Show info")
        action_map["Show info"] = "info"
        actions.append("← Back")

        menu = TerminalMenu(
            actions,
            title=f"{server_id}\n{server.description[:80]}",
        )
        index = menu.show()

        if index is None or actions[index] == "← Back":
            return "continue"

        action = action_map[actions[index]]
        self._execute_action(action, server_id, scope)
        return "continue"

    def _execute_action(self, action: str, server_id: str, scope: str) -> None:
        """Execute the selected action.

        Args:
            action: Action to execute (add, remove, enable, disable, info)
            server_id: Target server
            scope: Target scope
        """
        if action == "info":
            self._show_info(server_id)
            return

        console.print(f"\n[dim]Executing: {action} {server_id} in {scope}[/dim]")

        try:
            if action == "add":
                # Get server config from catalog
                server = self.catalog.get_server(server_id)
                if server and server.command:
                    from mcpi.clients.types import ServerConfig
                    config = ServerConfig(
                        command=server.command,
                        args=server.args or [],
                        env={},  # MCPServer doesn't have env, user must provide via config
                    )
                    result = self.manager.add_server(server_id, config, scope)
                else:
                    console.print(f"[red]No config found for {server_id}[/red]")
                    return
            elif action == "remove":
                result = self.manager.remove_server(server_id, scope)
            elif action == "enable":
                result = self.manager.enable_server(server_id)
            elif action == "disable":
                result = self.manager.disable_server(server_id)
            else:
                console.print(f"[red]Unknown action: {action}[/red]")
                return

            if result.success:
                console.print(f"[green]✓ {result.message}[/green]")
            else:
                console.print(f"[red]✗ {result.message}[/red]")
                for error in result.errors:
                    console.print(f"  [red]{error}[/red]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        # Pause to let user see result
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()

    def _show_info(self, server_id: str) -> None:
        """Display server information.

        Args:
            server_id: Server to show info for
        """
        server = self.catalog.get_server(server_id)
        if not server:
            console.print(f"[red]Server not found: {server_id}[/red]")
            return

        console.print(f"\n[bold]{server_id}[/bold]")
        console.print(f"[dim]{server.description}[/dim]\n")

        if server.command:
            console.print("[bold]Configuration:[/bold]")
            console.print(f"  Command: {server.command}")
            if server.args:
                console.print(f"  Args: {' '.join(server.args)}")

        if server.repository:
            console.print(f"\n[link={server.repository}]{server.repository}[/link]")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()


def launch_menu(
    manager: Optional[MCPManager] = None,
    catalog: Optional[ServerCatalog] = None,
    scope: Optional[str] = None,
) -> None:
    """Convenience function to launch the menu.

    Args:
        manager: MCPManager instance (created if not provided)
        catalog: ServerCatalog instance (created if not provided)
        scope: Initial scope (prompts if not provided)
    """
    from mcpi.clients.manager import create_default_manager
    from mcpi.registry.catalog_manager import create_default_catalog_manager

    if manager is None:
        manager = create_default_manager()
    if catalog is None:
        catalog_manager = create_default_catalog_manager()
        catalog = catalog_manager.get_catalog("official")

    adapter = SimpleMenuAdapter(manager, catalog)
    adapter.launch(initial_scope=scope)
