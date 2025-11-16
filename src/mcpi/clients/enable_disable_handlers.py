"""Enable/disable handler implementations for different scope types."""

from pathlib import Path
from typing import Any, Dict

from .disabled_tracker import DisabledServersTracker
from .protocols import ConfigReader, ConfigWriter, EnableDisableHandler


class ArrayBasedEnableDisableHandler:
    """Enable/disable handler using enabledMcpjsonServers/disabledMcpjsonServers arrays.

    This handler is used for scopes like project-local and user-local that support
    the enabledMcpjsonServers and disabledMcpjsonServers arrays in their settings file.
    """

    def __init__(
        self, config_path: Path, reader: ConfigReader, writer: ConfigWriter
    ) -> None:
        """Initialize the array-based handler.

        Args:
            config_path: Path to the configuration file
            reader: Configuration file reader
            writer: Configuration file writer
        """
        self.config_path = config_path
        self.reader = reader
        self.writer = writer

    def is_disabled(self, server_id: str) -> bool:
        """Check if a server is disabled.

        Args:
            server_id: Server identifier

        Returns:
            True if server is in disabledMcpjsonServers array
        """
        if not self.config_path.exists():
            return False

        try:
            data = self.reader.read(self.config_path)
            disabled_servers = data.get("disabledMcpjsonServers", [])
            return server_id in disabled_servers
        except Exception:
            return False

    def disable_server(self, server_id: str) -> bool:
        """Mark a server as disabled by adding to disabledMcpjsonServers array.

        Args:
            server_id: Server identifier

        Returns:
            True if operation succeeded
        """
        try:
            # Read current data
            if self.config_path.exists():
                data = self.reader.read(self.config_path)
            else:
                data = {}

            # Initialize arrays if needed
            enabled_servers = data.get("enabledMcpjsonServers", [])
            disabled_servers = data.get("disabledMcpjsonServers", [])

            # Remove from enabled if present
            if server_id in enabled_servers:
                enabled_servers.remove(server_id)

            # Add to disabled if not already there
            if server_id not in disabled_servers:
                disabled_servers.append(server_id)

            # Update data
            data["enabledMcpjsonServers"] = enabled_servers
            data["disabledMcpjsonServers"] = disabled_servers

            # Write back
            self.writer.write(self.config_path, data)
            return True

        except Exception:
            return False

    def enable_server(self, server_id: str) -> bool:
        """Mark a server as enabled by adding to enabledMcpjsonServers array.

        Args:
            server_id: Server identifier

        Returns:
            True if operation succeeded
        """
        try:
            # Read current data
            if self.config_path.exists():
                data = self.reader.read(self.config_path)
            else:
                data = {}

            # Initialize arrays if needed
            enabled_servers = data.get("enabledMcpjsonServers", [])
            disabled_servers = data.get("disabledMcpjsonServers", [])

            # Remove from disabled if present
            if server_id in disabled_servers:
                disabled_servers.remove(server_id)

            # Add to enabled if not already there
            if server_id not in enabled_servers:
                enabled_servers.append(server_id)

            # Update data
            data["enabledMcpjsonServers"] = enabled_servers
            data["disabledMcpjsonServers"] = disabled_servers

            # Write back
            self.writer.write(self.config_path, data)
            return True

        except Exception:
            return False


class FileTrackedEnableDisableHandler:
    """Enable/disable handler using a separate disabled tracking file.

    This handler is used for scopes like user-global that don't support
    enabledMcpjsonServers/disabledMcpjsonServers arrays in their configuration format.
    Instead, disabled servers are tracked in a separate JSON file.
    """

    def __init__(self, tracker: DisabledServersTracker) -> None:
        """Initialize the file-tracked handler.

        Args:
            tracker: Disabled servers tracker instance
        """
        self.tracker = tracker

    def is_disabled(self, server_id: str) -> bool:
        """Check if a server is disabled.

        Args:
            server_id: Server identifier

        Returns:
            True if server is in disabled tracking file
        """
        return self.tracker.is_disabled(server_id)

    def disable_server(self, server_id: str) -> bool:
        """Mark a server as disabled by adding to tracking file.

        Args:
            server_id: Server identifier

        Returns:
            True if operation succeeded
        """
        return self.tracker.disable(server_id)

    def enable_server(self, server_id: str) -> bool:
        """Mark a server as enabled by removing from tracking file.

        Args:
            server_id: Server identifier

        Returns:
            True if operation succeeded
        """
        return self.tracker.enable(server_id)


class InlineEnableDisableHandler:
    """Enable/disable handler using inline 'disabled' field in server config.

    This handler is used for scopes like project-mcp that use .mcp.json format,
    which doesn't support enabledMcpjsonServers/disabledMcpjsonServers arrays.
    Instead, each server can have a 'disabled' field directly in its configuration.
    """

    def __init__(
        self, config_path: Path, reader: ConfigReader, writer: ConfigWriter
    ) -> None:
        """Initialize the inline handler.

        Args:
            config_path: Path to the configuration file
            reader: Configuration file reader
            writer: Configuration file writer
        """
        self.config_path = config_path
        self.reader = reader
        self.writer = writer

    def is_disabled(self, server_id: str) -> bool:
        """Check if a server is disabled.

        Args:
            server_id: Server identifier

        Returns:
            True if server has 'disabled' field set to true
        """
        if not self.config_path.exists():
            return False

        try:
            data = self.reader.read(self.config_path)
            servers = data.get("mcpServers", {})
            server_config = servers.get(server_id, {})
            return server_config.get("disabled") is True
        except Exception:
            return False

    def disable_server(self, server_id: str) -> bool:
        """Mark a server as disabled by setting 'disabled': true in config.

        Args:
            server_id: Server identifier

        Returns:
            True if operation succeeded
        """
        try:
            # Read current data
            if not self.config_path.exists():
                return False  # Can't disable if config doesn't exist

            data = self.reader.read(self.config_path)

            # Get servers
            servers = data.get("mcpServers", {})
            if server_id not in servers:
                return False  # Can't disable if server doesn't exist

            # Set disabled flag
            servers[server_id]["disabled"] = True

            # Write back
            self.writer.write(self.config_path, data)
            return True

        except Exception:
            return False

    def enable_server(self, server_id: str) -> bool:
        """Mark a server as enabled by removing 'disabled' field from config.

        Args:
            server_id: Server identifier

        Returns:
            True if operation succeeded
        """
        try:
            # Read current data
            if not self.config_path.exists():
                return False  # Can't enable if config doesn't exist

            data = self.reader.read(self.config_path)

            # Get servers
            servers = data.get("mcpServers", {})
            if server_id not in servers:
                return False  # Can't enable if server doesn't exist

            # Remove disabled flag if present
            if "disabled" in servers[server_id]:
                del servers[server_id]["disabled"]

            # Write back
            self.writer.write(self.config_path, data)
            return True

        except Exception:
            return False
