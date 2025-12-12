"""FzfAdapter - fzf-based TUI implementation.

This adapter uses fzf (fuzzy finder) to provide an interactive terminal UI
for managing MCP servers. It supports fuzzy search, keyboard shortcuts,
server preview, and scope cycling.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from mcpi.clients.manager import MCPManager
from mcpi.clients.types import ServerState
from mcpi.registry.catalog import MCPServer, ServerCatalog

# File to store current scope (needed because fzf subprocesses don't share env vars)
SCOPE_FILE = Path.home() / ".mcpi_fzf_scope"

console = Console()


class FzfAdapter:
    """fzf-based TUI adapter for MCPI.

    This adapter implements the TUIAdapter protocol using fzf as the backend.
    It provides an interactive fuzzy-searchable list of MCP servers with
    keyboard shortcuts for common operations.

    Features:
    - Fuzzy search through available servers
    - Visual status indicators (enabled/disabled/not-installed)
    - Server preview with detailed information
    - Keyboard shortcuts for operations (add, remove, enable, disable)
    - Scope cycling (ctrl-s)
    - Automatic reload after operations
    """

    def launch(
        self,
        manager: MCPManager,
        catalog: ServerCatalog,
        initial_scope: Optional[str] = None,
    ) -> None:
        """Launch interactive fzf interface for managing MCP servers.

        Args:
            manager: MCPManager instance for server operations
            catalog: ServerCatalog instance for server registry
            initial_scope: Starting scope (defaults to first available)

        Raises:
            RuntimeError: If fzf is not installed
        """
        if not self._check_fzf_installed():
            raise RuntimeError(
                "fzf is not installed. Please install it first:\n"
                "  macOS: brew install fzf\n"
                "  Linux: apt install fzf / yum install fzf\n"
                "  Or visit: https://github.com/junegunn/fzf#installation"
            )

        # Initialize scope
        if initial_scope:
            self._write_scope(initial_scope)
        else:
            available_scopes = self._get_available_scopes(manager)
            if available_scopes:
                initial_scope = available_scopes[0]
                self._write_scope(initial_scope)
            else:
                initial_scope = "project-mcp"
                self._write_scope(initial_scope)

        # Build server list
        server_lines = self._build_server_list(catalog, manager)

        if not server_lines:
            console.print("[yellow]No servers found in registry[/yellow]")
            return

        # Build fzf command with current scope
        fzf_cmd = self._build_fzf_command(initial_scope)
        input_data = "\n".join(server_lines)

        try:
            result = subprocess.run(
                fzf_cmd,
                input=input_data,
                text=True,
                capture_output=True,
            )

            # Exit code 0 = selection made, 1 = no match, 130 = interrupted
            if result.returncode == 130:
                console.print("\n[dim]Cancelled[/dim]")
            elif result.returncode not in [0, 1]:
                console.print(f"[red]fzf exited with code {result.returncode}[/red]")

        except KeyboardInterrupt:
            console.print("\n[dim]Cancelled[/dim]")
        except Exception as e:
            console.print(f"[red]Error launching fzf: {e}[/red]")
            raise

    def get_name(self) -> str:
        """Return human-readable name of this TUI adapter."""
        return "fzf"

    def get_version(self) -> str:
        """Return version of fzf."""
        try:
            result = subprocess.run(
                ["fzf", "--version"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip().split()[0]
            return "unknown"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return "unknown"

    # =========================================================================
    # fzf detection
    # =========================================================================

    def _check_fzf_installed(self) -> bool:
        """Check if fzf is installed and available."""
        try:
            result = subprocess.run(
                ["fzf", "--version"],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    # =========================================================================
    # Server list building
    # =========================================================================

    def _get_server_status(
        self, manager: MCPManager, server_id: str, client: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the current status of a server."""
        state = manager.get_server_state(server_id, client)
        info = manager.get_server_info(server_id, client)
        return {
            "installed": state != ServerState.NOT_INSTALLED,
            "state": state,
            "info": info,
        }

    def _format_server_line(
        self, server_id: str, server: MCPServer, status: Dict[str, Any]
    ) -> str:
        """Format a server as a line for fzf display.

        Format: server-id<TAB>display_text
        """
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        max_desc_length = 120
        description = server.description
        if len(description) > max_desc_length:
            description = description[:max_desc_length] + "..."

        if status["state"] == ServerState.ENABLED:
            icon = "✓"
            display = f"{GREEN}{BOLD}[{icon}] {server_id}{RESET} - {description}"
        elif status["state"] == ServerState.DISABLED:
            icon = "✗"
            display = f"{YELLOW}{BOLD}[{icon}] {server_id}{RESET} - {description}"
        else:
            icon = " "
            display = f"[{icon}] {server_id} - {description}"

        return f"{server_id}\t{display}"

    def _build_server_list(
        self, catalog: ServerCatalog, manager: MCPManager
    ) -> List[str]:
        """Build the complete server list for fzf, sorted by status."""
        servers = catalog.list_servers()

        server_lines = []
        for server_id, server in servers:
            status = self._get_server_status(manager, server_id)
            line = self._format_server_line(server_id, server, status)
            server_lines.append((status["state"], line))

        def sort_key(item):
            state, line = item
            if state == ServerState.ENABLED:
                return (1, line)
            elif state == ServerState.DISABLED:
                return (2, line)
            else:
                return (3, line)

        server_lines.sort(key=sort_key)
        return [line for _, line in server_lines]

    # =========================================================================
    # Scope management
    # =========================================================================

    def _write_scope(self, scope: str) -> None:
        """Write current scope to file for fzf subprocess access."""
        try:
            SCOPE_FILE.write_text(scope)
        except OSError:
            pass

    def _get_current_scope(self) -> str:
        """Get current scope from file or return default."""
        try:
            if SCOPE_FILE.exists():
                return SCOPE_FILE.read_text().strip()
        except OSError:
            pass
        return "project-mcp"

    def _get_available_scopes(self, manager: MCPManager) -> List[str]:
        """Get list of available writable scope names for cycling."""
        scopes_info = manager.get_scopes_for_client(manager.default_client)
        return [
            scope["name"] for scope in scopes_info if not scope.get("readonly", False)
        ]

    def _set_next_scope(self, current_scope: str, available_scopes: List[str]) -> str:
        """Cycle to next scope in the list."""
        try:
            idx = available_scopes.index(current_scope)
            next_scope = available_scopes[(idx + 1) % len(available_scopes)]
        except (ValueError, IndexError):
            next_scope = available_scopes[0] if available_scopes else "project-mcp"

        self._write_scope(next_scope)
        return next_scope

    # =========================================================================
    # fzf command building
    # =========================================================================

    def _build_fzf_command(self, current_scope: Optional[str] = None) -> List[str]:
        """Build the fzf command with all options and bindings."""
        if current_scope is None:
            current_scope = self._get_current_scope()

        header = (
            f"MCPI | Scope: {current_scope}\n"
            "^S:Chg-Scope ^A:Add ^R:Remove\n"
            "^E:Enable ^D:Disable\n"
            "^I/Enter:Info  Esc:Exit"
        )

        return [
            "fzf",
            "--ansi",
            "--delimiter=\t",
            "--with-nth=2",
            f"--header={header}",
            "--header-lines=0",
            "--layout=reverse",
            "--border",
            "--preview",
            'id={1}; [ -n "$id" ] && mcpi info "$id" --plain 2>/dev/null || echo \'Select a server to view details\'',
            "--preview-window=right:50%:wrap",
            "--bind",
            "ctrl-s:reload(mcpi-tui-cycle-scope)+clear-query",
            "--bind",
            'ctrl-a:execute(mcpi add {1} --scope "$(cat ~/.mcpi_fzf_scope)")+reload(mcpi-tui-reload)',
            "--bind",
            "ctrl-r:execute(mcpi remove {1})+reload(mcpi-tui-reload)",
            "--bind",
            "ctrl-e:execute(mcpi enable {1})+reload(mcpi-tui-reload)",
            "--bind",
            "ctrl-d:execute(mcpi disable {1})+reload(mcpi-tui-reload)",
            "--bind",
            "ctrl-i:execute(mcpi info {1} | less)",
            "--bind",
            "enter:execute(mcpi info {1} | less)",
        ]
