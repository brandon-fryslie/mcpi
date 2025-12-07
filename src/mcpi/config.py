"""MCPI configuration management.

Handles loading and syncing mcpi.toml configuration files.

Config file locations (in order of precedence, later overrides earlier):
    1. ~/.config/mcpi/mcpi.toml (global/user-scope servers)
    2. ./mcpi.toml (project-specific servers)

Example mcpi.toml:

    default_scope = "project-mcp"
    default_client = "claude-code"

    # Servers tracked in this project
    [servers]
    "@anthropic/filesystem" = {}
    "@anthropic/fetch" = { env = { FETCH_TIMEOUT = "30" } }

    # Disabled servers (tracked but not active)
    [disabled]
    "github" = { reason = "API rate limits" }

    # Per-client server lists
    [clients.cursor.servers]
    "@anthropic/sqlite" = {}

When you run 'mcpi add', servers are tracked in mcpi.toml.
When you run 'mcpi remove', servers are removed from mcpi.toml.
When you run 'mcpi disable', servers move to the [disabled] section.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import toml
from rich.console import Console

console = Console()


# =============================================================================
# Config file path helpers
# =============================================================================


def get_project_config_path() -> Path:
    """Get the project-level config file path.

    Returns:
        Path to ./mcpi.toml
    """
    return Path.cwd() / "mcpi.toml"


def get_global_config_path() -> Path:
    """Get the global/user-level config file path.

    Returns:
        Path to ~/.config/mcpi/mcpi.toml
    """
    return Path.home() / ".config" / "mcpi" / "mcpi.toml"


def get_config_path_for_scope(scope: str) -> Path:
    """Determine which config file to use based on scope.

    Args:
        scope: Scope name (e.g., "project-mcp", "user-global")

    Returns:
        Path to the appropriate mcpi.toml file
    """
    if scope.startswith("project"):
        return get_project_config_path()
    else:
        return get_global_config_path()


def load_config_file(config_path: Path) -> Dict[str, Any]:
    """Load a single config file (not merged).

    Args:
        config_path: Path to the config file

    Returns:
        Config dict, or empty dict if file doesn't exist
    """
    if not config_path.exists():
        return {}

    try:
        return toml.load(config_path)
    except Exception:
        return {}


def save_config_file(config_path: Path, config: Dict[str, Any]) -> None:
    """Save config to a file.

    Args:
        config_path: Path to write to
        config: Config dict to save
    """
    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config
    with open(config_path, "w") as f:
        toml.dump(config, f)


# =============================================================================
# Server tracking in mcpi.toml
# =============================================================================


def add_server_to_config(
    server_id: str,
    scope: str,
    client: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    args: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """Add a server to mcpi.toml for tracking.

    Args:
        server_id: Server identifier
        scope: Target scope (determines project vs global config)
        client: Optional client name for per-client tracking
        env: Optional environment variables
        args: Optional arguments

    Returns:
        Tuple of (success, message)
    """
    config_path = get_config_path_for_scope(scope)
    config = load_config_file(config_path)

    # Build server entry
    server_entry: Dict[str, Any] = {}
    if env:
        server_entry["env"] = env
    if args:
        server_entry["args"] = args

    if client:
        # Per-client tracking
        if "clients" not in config:
            config["clients"] = {}
        if client not in config["clients"]:
            config["clients"][client] = {}
        if "servers" not in config["clients"][client]:
            config["clients"][client]["servers"] = {}

        # Check if already tracked
        if server_id in config["clients"][client]["servers"]:
            return False, f"{server_id} already tracked for {client}"

        config["clients"][client]["servers"][server_id] = server_entry
    else:
        # Top-level tracking
        if "servers" not in config:
            config["servers"] = {}

        # Convert list to dict if needed
        if isinstance(config["servers"], list):
            config["servers"] = {sid: {} for sid in config["servers"]}

        # Check if already tracked
        if server_id in config["servers"]:
            return False, f"{server_id} already tracked"

        config["servers"][server_id] = server_entry

    # Remove from disabled if present
    if "disabled" in config and server_id in config.get("disabled", {}):
        del config["disabled"][server_id]
        if not config["disabled"]:
            del config["disabled"]

    save_config_file(config_path, config)
    return True, f"Added {server_id} to {config_path.name}"


def remove_server_from_config(
    server_id: str,
    scope: str,
    client: Optional[str] = None,
) -> Tuple[bool, str]:
    """Remove a server from mcpi.toml tracking.

    Args:
        server_id: Server identifier
        scope: Target scope (determines project vs global config)
        client: Optional client name

    Returns:
        Tuple of (success, message)
    """
    config_path = get_config_path_for_scope(scope)
    config = load_config_file(config_path)

    removed = False

    if client:
        # Per-client removal
        clients_config = config.get("clients", {})
        client_config = clients_config.get(client, {})
        servers = client_config.get("servers", {})

        if isinstance(servers, dict) and server_id in servers:
            del config["clients"][client]["servers"][server_id]
            removed = True

            # Clean up empty structures
            if not config["clients"][client]["servers"]:
                del config["clients"][client]["servers"]
            if not config["clients"][client]:
                del config["clients"][client]
            if not config["clients"]:
                del config["clients"]
    else:
        # Top-level removal
        servers = config.get("servers", {})

        if isinstance(servers, list) and server_id in servers:
            config["servers"].remove(server_id)
            removed = True
        elif isinstance(servers, dict) and server_id in servers:
            del config["servers"][server_id]
            removed = True

        # Clean up empty servers
        if "servers" in config and not config["servers"]:
            del config["servers"]

    # Also remove from disabled
    if "disabled" in config and server_id in config.get("disabled", {}):
        del config["disabled"][server_id]
        removed = True
        if not config["disabled"]:
            del config["disabled"]

    if removed:
        save_config_file(config_path, config)
        return True, f"Removed {server_id} from {config_path.name}"
    else:
        return False, f"{server_id} not found in {config_path.name}"


def disable_server_in_config(
    server_id: str,
    scope: str,
    reason: Optional[str] = None,
) -> Tuple[bool, str]:
    """Mark a server as disabled in mcpi.toml.

    Moves the server from [servers] to [disabled].

    Args:
        server_id: Server identifier
        scope: Target scope
        reason: Optional reason for disabling

    Returns:
        Tuple of (success, message)
    """
    config_path = get_config_path_for_scope(scope)
    config = load_config_file(config_path)

    # Find and remove from servers section
    server_entry: Dict[str, Any] = {}
    found = False

    servers = config.get("servers", {})
    if isinstance(servers, list) and server_id in servers:
        config["servers"].remove(server_id)
        found = True
    elif isinstance(servers, dict) and server_id in servers:
        server_entry = config["servers"].pop(server_id)
        found = True

    # Clean up empty servers
    if "servers" in config and not config["servers"]:
        del config["servers"]

    if not found:
        # Check if already disabled
        if "disabled" in config and server_id in config.get("disabled", {}):
            return False, f"{server_id} already disabled"
        return False, f"{server_id} not found in {config_path.name}"

    # Add to disabled section
    if "disabled" not in config:
        config["disabled"] = {}

    if reason:
        server_entry["reason"] = reason
    config["disabled"][server_id] = server_entry

    save_config_file(config_path, config)
    return True, f"Disabled {server_id} in {config_path.name}"


def enable_server_in_config(
    server_id: str,
    scope: str,
) -> Tuple[bool, str]:
    """Re-enable a disabled server in mcpi.toml.

    Moves the server from [disabled] back to [servers].

    Args:
        server_id: Server identifier
        scope: Target scope

    Returns:
        Tuple of (success, message)
    """
    config_path = get_config_path_for_scope(scope)
    config = load_config_file(config_path)

    # Check if in disabled section
    if "disabled" not in config or server_id not in config.get("disabled", {}):
        return False, f"{server_id} not in disabled list"

    # Move from disabled to servers
    server_entry = config["disabled"].pop(server_id)

    # Remove reason field if present
    server_entry.pop("reason", None)

    # Clean up empty disabled
    if not config["disabled"]:
        del config["disabled"]

    # Add to servers section
    if "servers" not in config:
        config["servers"] = {}
    if isinstance(config["servers"], list):
        config["servers"] = {sid: {} for sid in config["servers"]}

    config["servers"][server_id] = server_entry

    save_config_file(config_path, config)
    return True, f"Enabled {server_id} in {config_path.name}"


def is_server_tracked(
    server_id: str,
    scope: str,
    client: Optional[str] = None,
) -> bool:
    """Check if a server is tracked in mcpi.toml.

    Args:
        server_id: Server identifier
        scope: Target scope
        client: Optional client name

    Returns:
        True if server is tracked (in servers or disabled)
    """
    config_path = get_config_path_for_scope(scope)
    config = load_config_file(config_path)

    # Check disabled
    if server_id in config.get("disabled", {}):
        return True

    if client:
        servers = config.get("clients", {}).get(client, {}).get("servers", {})
    else:
        servers = config.get("servers", {})

    if isinstance(servers, list):
        return server_id in servers
    elif isinstance(servers, dict):
        return server_id in servers

    return False


def load_mcpi_config(project_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load mcpi config from global and project files.

    Args:
        project_path: Project directory (defaults to cwd)

    Returns:
        Merged config dict
    """
    config: Dict[str, Any] = {}

    # Global config
    global_config = Path.home() / ".config" / "mcpi" / "mcpi.toml"
    if global_config.exists():
        try:
            config.update(toml.load(global_config))
        except Exception:
            pass

    # Project config (overrides global)
    project_dir = project_path or Path.cwd()
    project_config = project_dir / "mcpi.toml"
    if project_config.exists():
        try:
            project_data = toml.load(project_config)
            # Deep merge servers if both have them
            if "servers" in config and "servers" in project_data:
                if isinstance(config["servers"], dict) and isinstance(
                    project_data["servers"], dict
                ):
                    config["servers"].update(project_data["servers"])
                    project_data = {
                        k: v for k, v in project_data.items() if k != "servers"
                    }
            # Deep merge clients if both have them
            if "clients" in config and "clients" in project_data:
                for client_name, client_config in project_data["clients"].items():
                    if client_name in config["clients"]:
                        config["clients"][client_name].update(client_config)
                    else:
                        config["clients"][client_name] = client_config
                project_data = {k: v for k, v in project_data.items() if k != "clients"}
            config.update(project_data)
        except Exception:
            pass

    return config


def get_servers_from_config(
    config: Dict[str, Any], client: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """Extract server configurations from config.

    Handles multiple formats:
        # Simple list (all clients)
        servers = ["filesystem", "time"]

        # Dict format (all clients)
        [servers.filesystem]
        env = { ... }

        # Per-client list
        [clients.claude-code]
        servers = ["filesystem"]

        # Per-client with overrides
        [clients.claude-code.servers.github]
        env = { GITHUB_TOKEN = "xxx" }

    Args:
        config: Loaded config dict
        client: If provided, get servers for this specific client only.
                If None, returns servers from the top-level 'servers' key.

    Returns:
        Dict mapping server_id to server config overrides
    """
    result: Dict[str, Dict[str, Any]] = {}

    if client:
        # Get per-client servers
        clients_config = config.get("clients", {})
        client_config = clients_config.get(client, {})

        servers_config = client_config.get("servers", {})
        if isinstance(servers_config, list):
            result = {server_id: {} for server_id in servers_config}
        elif isinstance(servers_config, dict):
            result = dict(servers_config)
    else:
        # Get top-level servers (legacy/shared format)
        servers_config = config.get("servers", {})
        if isinstance(servers_config, list):
            result = {server_id: {} for server_id in servers_config}
        elif isinstance(servers_config, dict):
            result = dict(servers_config)

    return result


def get_configured_clients(config: Dict[str, Any]) -> List[str]:
    """Get list of clients that have server configurations.

    Args:
        config: Loaded config dict

    Returns:
        List of client names with server configs
    """
    clients_config = config.get("clients", {})
    return [
        name for name, cfg in clients_config.items() if cfg.get("servers")
    ]


def get_client_scope(config: Dict[str, Any], client: str) -> str:
    """Get the scope to use for a specific client.

    Checks client-specific scope override, then falls back to default_scope.

    Args:
        config: Loaded config dict
        client: Client name

    Returns:
        Scope name to use
    """
    clients_config = config.get("clients", {})
    client_config = clients_config.get(client, {})

    # Client-specific scope overrides default
    return client_config.get("scope", config.get("default_scope", "project-mcp"))


def sync_servers(
    manager: Any,
    catalog: Any,
    config: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    client: Optional[str] = None,
) -> Dict[str, Any]:
    """Sync servers from mcpi.toml config.

    Installs servers listed in config that aren't already installed.

    Args:
        manager: MCPManager instance
        catalog: ServerCatalog instance
        config: Config dict (loads from files if not provided)
        dry_run: If True, only report what would be done
        client: If provided, only sync servers for this client.
                If None, syncs top-level servers AND all per-client servers.

    Returns:
        Dict with 'added', 'skipped', 'errors' lists, and optionally 'by_client'
    """
    from mcpi.clients.types import ServerConfig, ServerState

    if config is None:
        config = load_mcpi_config()

    results: Dict[str, Any] = {"added": [], "skipped": [], "errors": []}

    def sync_server_list(
        servers: Dict[str, Dict[str, Any]],
        target_scope: str,
        target_client: Optional[str],
    ) -> None:
        """Sync a dict of servers."""
        for server_id, overrides in servers.items():
            # Check if already installed
            state = manager.get_server_state(server_id, target_client)

            if state != ServerState.NOT_INSTALLED:
                results["skipped"].append(server_id)
                continue

            # Get server from catalog
            server = catalog.get_server(server_id)
            if not server:
                results["errors"].append(f"{server_id}: not found in catalog")
                continue

            if not server.command:
                results["errors"].append(f"{server_id}: no command in catalog")
                continue

            if dry_run:
                results["added"].append(server_id)
                continue

            # Build config with overrides
            env = dict(overrides.get("env", {}))
            args = overrides.get("args", server.args or [])

            server_config = ServerConfig(
                command=overrides.get("command", server.command),
                args=args,
                env=env,
            )

            # Install
            result = manager.add_server(
                server_id, server_config, target_scope, target_client
            )
            if result.success:
                results["added"].append(server_id)
            else:
                results["errors"].append(f"{server_id}: {result.message}")

    if client:
        # Sync only for specified client
        servers = get_servers_from_config(config, client)
        if servers:
            scope = get_client_scope(config, client)
            sync_server_list(servers, scope, client)
    else:
        # Sync top-level servers (with default client)
        top_level_servers = get_servers_from_config(config, client=None)
        if top_level_servers:
            default_scope = config.get("default_scope", "project-mcp")
            default_client = config.get("default_client")
            sync_server_list(top_level_servers, default_scope, default_client)

        # Sync per-client servers
        configured_clients = get_configured_clients(config)
        for configured_client in configured_clients:
            servers = get_servers_from_config(config, configured_client)
            if servers:
                scope = get_client_scope(config, configured_client)
                sync_server_list(servers, scope, configured_client)

    return results
