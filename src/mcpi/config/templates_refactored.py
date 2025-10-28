"""Refactored version of templates.py showing improved structure."""

from typing import Any, Dict, List, Optional

from mcpi.registry.catalog import MCPServer


class TemplateManager:
    """Example of refactored TemplateManager with simplified methods."""

    def _get_args_for_server(
        self, server: MCPServer, user_params: Dict[str, Any]
    ) -> List[str]:
        """Get arguments for MCP server.

        Args:
            server: MCP server information
            user_params: User-provided parameters

        Returns:
            List of command arguments
        """
        args = []

        # Add package/module specification
        args.extend(self._get_package_args(server))

        # Add required and optional parameters
        args.extend(self._get_required_param_args(server, user_params))
        args.extend(self._get_optional_param_args(server, user_params))

        return args

    def _get_package_args(self, server: MCPServer) -> List[str]:
        """Get package/module arguments based on installation method."""
        method = server.installation.method
        package = server.installation.package

        if method == "npm":
            return [package]
        elif method == "pip":
            return ["-m", package]
        elif method == "git":
            return ["main.py"]  # Could be made configurable
        else:
            return []

    def _get_required_param_args(
        self, server: MCPServer, user_params: Dict[str, Any]
    ) -> List[str]:
        """Get arguments for required parameters."""
        args = []
        for param in server.configuration.required_params:
            if param in user_params:
                args.append(str(user_params[param]))
            else:
                default = self._get_default_value(param)
                if default:
                    args.append(default)
        return args

    def _get_optional_param_args(
        self, server: MCPServer, user_params: Dict[str, Any]
    ) -> List[str]:
        """Get arguments for optional parameters."""
        args = []
        for param in server.configuration.optional_params:
            if param in user_params:
                args.extend([f"--{param}", str(user_params[param])])
        return args

    def _get_default_value(self, param_name: str) -> Optional[str]:
        """Get default value for parameter."""
        defaults = {
            "root_path": str(Path.home()),
            "database_path": "./database.db",
            "repository_path": ".",
            "host": "localhost",
            "port": "5432",
            "timeout": "30",
        }
        return defaults.get(param_name)
