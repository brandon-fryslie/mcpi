"""Interactive TUI for managing MCP servers using fzf."""

import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

from rich.console import Console

from mcpi.clients import MCPManager
from mcpi.clients.types import ServerState
from mcpi.registry.catalog import MCPServer, ServerCatalog

console = Console()


def check_fzf_installed() -> bool:
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


def get_server_status(
    manager: MCPManager, server_id: str, client: Optional[str] = None
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


def format_server_line(
    server_id: str, server: MCPServer, status: Dict[str, Any]
) -> str:
    """Format a server as a line for fzf display.

    Args:
        server_id: Server identifier
        server: Server catalog entry
        status: Server status dictionary from get_server_status

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


def build_server_list(catalog: ServerCatalog, manager: MCPManager) -> List[str]:
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
        status = get_server_status(manager, server_id)
        line = format_server_line(server_id, server, status)
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
        # Create instances if not provided (allows for mocking in tests)
        if catalog is None:
            catalog = ServerCatalog()
            # Load registry if it hasn't been loaded (empty _servers dict)
            # Tests will provide pre-populated catalog via mocking
            # Check if catalog has data (either mocked via _servers or loaded via _loaded)
            # Tests may set _servers directly without setting _loaded
            has_data = getattr(catalog, '_loaded', False) or hasattr(catalog, '_servers')
            if not has_data:
                catalog.load_registry()
            # Mark as loaded to prevent auto-reload in list_servers()
            if hasattr(catalog, '_loaded') and not catalog._loaded:
                catalog._loaded = True


        if manager is None:
            manager = MCPManager()

        lines = build_server_list(catalog, manager)
        for line in lines:
            print(line)
    except Exception as e:
        # Log error but don't crash - fzf needs output
        print(f"Error reloading server list: {e}", file=sys.stderr)
        # Output empty list rather than crashing
        print("[ ] error - Failed to reload server list")


def build_fzf_command() -> List[str]:
    """Build the fzf command with all options and bindings.

    Returns:
        List of command arguments for subprocess
    """
    # Extract server ID from fzf selection
    # Format is "[X] server-id - description"
    # We use awk to extract the server-id (field 2)
    extract_id = "awk '{print $2}'"

    return [
        "fzf",
        "--ansi",  # Enable ANSI color codes
        "--header=MCPI Server Manager | ctrl-a:Add  ctrl-r:Remove  ctrl-e:Enable  ctrl-d:Disable  ctrl-i:Info  enter:Info  esc:Exit",
        "--header-lines=0",
        "--layout=reverse",
        "--border",
        "--preview",
        f"echo {{}} | {extract_id} | xargs -I {{}} mcpi info {{}}",
        "--preview-window=right:50%:wrap",
        "--bind",
        f"ctrl-a:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi add {{}})+reload(mcpi-tui-reload)",
        "--bind",
        f"ctrl-r:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi remove {{}})+reload(mcpi-tui-reload)",
        "--bind",
        f"ctrl-e:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi enable {{}})+reload(mcpi-tui-reload)",
        "--bind",
        f"ctrl-d:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi disable {{}})+reload(mcpi-tui-reload)",
        "--bind",
        f"ctrl-i:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi info {{}} | less)",
        "--bind",
        f"enter:execute(echo {{}} | {extract_id} | xargs -I {{}} mcpi info {{}} | less)",
    ]


def launch_fzf_interface(manager: MCPManager, catalog: ServerCatalog) -> None:
    """Launch the interactive fzf interface.

    Args:
        manager: MCP manager instance
        catalog: Server catalog instance

    Raises:
        RuntimeError: If fzf is not installed
    """
    # Check if fzf is installed
    if not check_fzf_installed():
        raise RuntimeError(
            "fzf is not installed. Please install it first:\n"
            "  macOS: brew install fzf\n"
            "  Linux: apt install fzf / yum install fzf\n"
            "  Or visit: https://github.com/junegunn/fzf#installation"
        )

    # Build server list
    server_lines = build_server_list(catalog, manager)

    if not server_lines:
        console.print("[yellow]No servers found in registry[/yellow]")
        return

    # Build fzf command
    fzf_cmd = build_fzf_command()

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
