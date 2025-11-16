"""FzfAdapter - fzf-based TUI implementation.

This adapter uses fzf (fuzzy finder) to provide an interactive terminal UI
for managing MCP servers. It supports fuzzy search, keyboard shortcuts,
server preview, and scope cycling.
"""

import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

from rich.console import Console

from mcpi.clients.manager import MCPManager, create_default_manager
from mcpi.clients.types import ServerState
from mcpi.registry.catalog import (
    MCPServer,
    ServerCatalog,
    ServerRegistry,
    create_default_catalog,
)

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

    Environment Variables:
    - MCPI_FZF_SCOPE: Current target scope for operations
    """

    def __init__(self):
        """Initialize the fzf adapter."""
        pass

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
        # Check if fzf is installed
        if not self._check_fzf_installed():
            raise RuntimeError(
                "fzf is not installed. Please install it first:\n"
                "  macOS: brew install fzf\n"
                "  Linux: apt install fzf / yum install fzf\n"
                "  Or visit: https://github.com/junegunn/fzf#installation"
            )

        # Initialize scope
        if initial_scope:
            os.environ["MCPI_FZF_SCOPE"] = initial_scope
        else:
            # Set to first available scope
            available_scopes = self._get_available_scopes(manager)
            if available_scopes:
                initial_scope = available_scopes[0]
                os.environ["MCPI_FZF_SCOPE"] = initial_scope
            else:
                initial_scope = "project-mcp"

        # Build server list
        server_lines = self._build_server_list(catalog, manager)

        if not server_lines:
            console.print("[yellow]No servers found in registry[/yellow]")
            return

        # Build fzf command with current scope
        fzf_cmd = self._build_fzf_command(initial_scope)

        # Prepare input for fzf
        input_data = "\n".join(server_lines)

        try:
            # Launch fzf
            result = subprocess.run(
                fzf_cmd,
                input=input_data,
                text=True,
                capture_output=True,
            )

            # Exit code 0 = selection made
            # Exit code 1 = no match
            # Exit code 130 = interrupted (Ctrl-C)
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
        """Return human-readable name of this TUI adapter.

        Returns:
            "fzf"
        """
        return "fzf"

    def get_version(self) -> str:
        """Return version of fzf.

        Returns:
            Version string like "0.54.3" or "unknown" if fzf not available
        """
        try:
            result = subprocess.run(
                ["fzf", "--version"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                # fzf --version outputs like "0.54.3" (homebrew)"
                # Extract just the version number
                version = result.stdout.strip().split()[0]
                return version
            return "unknown"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return "unknown"

    # =========================================================================
    # Private methods - extracted from original tui.py functions
    # =========================================================================

    def _check_fzf_installed(self) -> bool:
        """Check if fzf is installed and available.

        Returns:
            True if fzf is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ["fzf", "--version"],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_server_status(
        self, manager: MCPManager, server_id: str, client: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the current status of a server.

        Args:
            manager: MCP manager instance
            server_id: Server identifier
            client: Optional client name

        Returns:
            Dictionary with installation status and state information
        """
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

        Args:
            server_id: Server identifier
            server: Server catalog entry
            status: Server status dictionary from _get_server_status

        Returns:
            Formatted line with ANSI color codes
        """
        # ANSI color codes
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        # Truncate description if too long
        max_desc_length = 120
        description = server.description
        if len(description) > max_desc_length:
            description = description[:max_desc_length] + "..."

        # Format based on status
        if status["state"] == ServerState.ENABLED:
            # Green + bold for enabled
            icon = "✓"
            return f"{GREEN}{BOLD}[{icon}] {server_id}{RESET} - {description}"
        elif status["state"] == ServerState.DISABLED:
            # Yellow + bold for disabled
            icon = "✗"
            return f"{YELLOW}{BOLD}[{icon}] {server_id}{RESET} - {description}"
        else:
            # Normal for not installed
            icon = " "
            return f"[{icon}] {server_id} - {description}"

    def _build_server_list(
        self, catalog: ServerCatalog, manager: MCPManager
    ) -> List[str]:
        """Build the complete server list for fzf.

        Servers are sorted with:
        1. Enabled servers first (green)
        2. Disabled servers second (yellow)
        3. Not-installed servers last (normal)

        Args:
            catalog: Server catalog
            manager: MCP manager

        Returns:
            List of formatted server lines
        """
        servers = catalog.list_servers()

        # Build list with status
        server_lines = []
        for server_id, server in servers:
            status = self._get_server_status(manager, server_id)
            line = self._format_server_line(server_id, server, status)
            server_lines.append((status["state"], line))

        # Sort by state (enabled=1, disabled=2, not_installed=3)
        def sort_key(item):
            state, line = item
            if state == ServerState.ENABLED:
                return (1, line)
            elif state == ServerState.DISABLED:
                return (2, line)
            else:
                return (3, line)

        server_lines.sort(key=sort_key)

        # Return just the formatted lines
        return [line for _, line in server_lines]

    def _get_current_scope(self) -> str:
        """Get current scope from environment or return default.

        Returns:
            Current scope name (defaults to first available scope)
        """
        return os.environ.get("MCPI_FZF_SCOPE", "project-mcp")

    def _get_available_scopes(self, manager: MCPManager) -> List[str]:
        """Get list of available scope names for cycling.

        Args:
            manager: MCPManager instance

        Returns:
            List of scope names in cycling order
        """
        scopes_info = manager.get_scopes_for_client(manager.default_client)
        return [scope["name"] for scope in scopes_info]

    def _set_next_scope(self, current_scope: str, available_scopes: List[str]) -> str:
        """Cycle to next scope in the list.

        Args:
            current_scope: Current scope name
            available_scopes: List of all available scopes

        Returns:
            Next scope name in the cycle
        """
        try:
            idx = available_scopes.index(current_scope)
            next_scope = available_scopes[(idx + 1) % len(available_scopes)]
        except (ValueError, IndexError):
            # If current scope not found or list empty, use first scope
            next_scope = available_scopes[0] if available_scopes else "project-mcp"

        # Store in environment for next reload
        os.environ["MCPI_FZF_SCOPE"] = next_scope
        return next_scope

    def _build_fzf_command(self, current_scope: Optional[str] = None) -> List[str]:
        """Build the fzf command with all options and bindings.

        Args:
            current_scope: Current target scope to display in header (optional)

        Returns:
            List of command arguments for subprocess
        """
        # Get current scope if not provided
        if current_scope is None:
            current_scope = self._get_current_scope()

        # Extract server ID from fzf selection
        # Format is "[X] server-id - description"
        # We use awk to extract the server-id (field 2)
        extract_id = "awk '{print $2}'"

        # Multi-line header with scope indicator
        # Line 1: Title with current scope (dynamic width)
        # Line 2: Scope cycling and operation shortcuts
        # Line 3: Info/Exit shortcuts
        # Compact header that fits in 60 columns (safe for narrow terminals)
        # Line 1: Title + scope (max 60 chars with longest scope name)
        # Line 2: Scope change + server ops (47 chars)
        # Line 3: State ops (37 chars)
        # Line 4: Info/exit (25 chars)
        header = (
            f"MCPI | Scope: {current_scope}\n"
            "^S:Chg-Scope ^A:Add ^R:Remove\n"
            "^E:Enable ^D:Disable\n"
            "^I/Enter:Info  Esc:Exit"
        )

        return [
            "fzf",
            "--ansi",  # Enable ANSI color codes
            f"--header={header}",
            "--header-lines=0",
            "--layout=reverse",
            "--border",
            "--preview",
            # Validate server ID before running info to avoid errors during typing
            # Use --plain flag to avoid box-drawing characters in narrow preview pane
            f'id=$(echo {{}} | {extract_id}); [ -n "$id" ] && mcpi info "$id" --plain 2>/dev/null || echo \'Select a server to view details\'',
            "--preview-window=right:50%:wrap",
            # Scope cycling binding (ctrl-s)
            # Use Python module execution to avoid PATH issues
            "--bind",
            f"ctrl-s:reload(python -c 'from mcpi.cli import tui_cycle_scope_entry; tui_cycle_scope_entry()')+clear-query",
            # Operation bindings with --scope parameter
            "--bind",
            f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi add {{}} --scope {current_scope})+reload(mcpi-tui-reload)",
            "--bind",
            f"ctrl-r:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi remove {{}})+reload(mcpi-tui-reload)",
            "--bind",
            f"ctrl-e:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi enable {{}} --scope {current_scope})+reload(mcpi-tui-reload)",
            "--bind",
            f"ctrl-d:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi disable {{}} --scope {current_scope})+reload(mcpi-tui-reload)",
            # Info bindings (no scope needed for read-only operations)
            "--bind",
            f"ctrl-i:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi info {{}} | less)",
            "--bind",
            f"enter:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi info {{}} | less)",
        ]


# =============================================================================
# Standalone functions for console scripts and backward compatibility
# These are called by mcpi-tui-reload and mcpi-tui-cycle-scope console scripts
# =============================================================================


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
        # Create instances if not provided (allows for dependency injection in tests)
        if catalog is None:
            catalog = create_default_catalog()
            catalog.load_catalog()
        else:
            # Catalog was provided (e.g., by tests) - ensure it's marked as loaded
            # to prevent auto-loading from production file in list_servers()
            # Tests may set catalog._servers directly (old pattern) or _registry (new pattern)
            # Handle both cases to maintain test compatibility
            if hasattr(catalog, "_loaded") and not catalog._loaded:
                # Case 1: Test set _servers directly on catalog (old pattern, wrong but happens)
                if (
                    hasattr(catalog, "_servers")
                    and catalog._servers
                    and not catalog._registry
                ):
                    # Initialize registry from the servers dict
                    catalog._registry = ServerRegistry(servers=catalog._servers)
                    catalog._loaded = True
                # Case 2: Test properly set _registry with data
                elif hasattr(catalog, "_registry") and catalog._registry is not None:
                    # Mark as loaded to prevent auto-load
                    catalog._loaded = True

        if manager is None:
            manager = create_default_manager()

        # Use adapter to build server list
        adapter = FzfAdapter()
        lines = adapter._build_server_list(catalog, manager)
        for line in lines:
            print(line)
    except Exception as e:
        # Log error but don't crash - fzf needs output
        print(f"Error reloading server list: {e}", file=sys.stderr)
        # Output empty list rather than crashing
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
        # Create manager if not provided
        if manager is None:
            manager = create_default_manager()

        # Use adapter for scope cycling
        adapter = FzfAdapter()
        current = adapter._get_current_scope()
        available = adapter._get_available_scopes(manager)

        # Cycle to next scope
        next_scope = adapter._set_next_scope(current, available)

        # Output scope change to stderr for user feedback
        print(f"Switched to scope: {next_scope}", file=sys.stderr)

        # Reload server list
        reload_server_list(catalog, manager)

    except Exception as e:
        print(f"Error cycling scope: {e}", file=sys.stderr)
        # Fall back to regular reload
        reload_server_list(catalog, manager)
