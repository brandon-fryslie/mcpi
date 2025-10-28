"""Configuration templates for MCP servers."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcpi.registry.catalog import MCPServer


class TemplateManager:
    """Manages configuration templates for MCP servers."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize template manager.

        Args:
            templates_dir: Directory containing template files
        """
        if templates_dir is None:
            # Get templates directory relative to package
            package_dir = Path(__file__).parent.parent.parent.parent
            self.templates_dir = package_dir / "data" / "templates"
        else:
            self.templates_dir = templates_dir

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration template by name.

        Args:
            template_name: Name of template file (without .json extension)

        Returns:
            Template data or None if not found
        """
        template_path = self.templates_dir / f"{template_name}.json"

        if not template_path.exists():
            return None

        try:
            with open(template_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def create_server_config(
        self, server: MCPServer, user_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create configuration for MCP server using template.

        Args:
            server: MCP server information
            user_params: User-provided parameters

        Returns:
            Generated configuration
        """
        if user_params is None:
            user_params = {}

        # Start with base configuration
        config = {
            "command": self._get_command_for_server(server),
            "args": self._get_args_for_server(server, user_params),
        }

        # Load server-specific template if available
        if server.configuration.template:
            template = self.get_template(
                server.configuration.template.replace(".json", "")
            )
            if template:
                config.update(template)

        # Add environment variables if specified
        if "env" in user_params:
            config["env"] = user_params["env"]

        return config

    def _get_command_for_server(self, server: MCPServer) -> str:
        """Get command for MCP server based on installation method.

        Args:
            server: MCP server information

        Returns:
            Command string
        """
        if server.installation.method == "npm":
            return "npx"
        elif server.installation.method == "pip":
            return "python3"
        elif server.installation.method == "git":
            return "python3"  # Default for Git installations
        else:
            return server.installation.package

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
        if server.installation.method == "npm":
            args.append(server.installation.package)
        elif server.installation.method == "pip":
            args.extend(["-m", server.installation.package])
        elif server.installation.method == "git":
            # For Git installations, assume main script in root
            args.append("main.py")  # This could be made configurable

        # Add required parameters
        for param in server.configuration.required_params:
            if param in user_params:
                args.append(str(user_params[param]))
            else:
                # Add placeholder or default
                default = self._get_default_value(param)
                if default:
                    args.append(default)

        # Add optional parameters
        for param in server.configuration.optional_params:
            if param in user_params:
                args.extend([f"--{param}", str(user_params[param])])

        return args

    def _get_default_value(self, param_name: str) -> Optional[str]:
        """Get default value for parameter.

        Args:
            param_name: Parameter name

        Returns:
            Default value or None
        """
        defaults = {
            "root_path": str(Path.home()),
            "database_path": "./database.db",
            "repository_path": ".",
            "host": "localhost",
            "port": "5432",
            "timeout": "30",
        }
        return defaults.get(param_name)

    def list_templates(self) -> List[str]:
        """List available template names.

        Returns:
            List of template names (without .json extension)
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        for template_file in self.templates_dir.glob("*.json"):
            templates.append(template_file.stem)

        return sorted(templates)

    def create_template(self, name: str, template_data: Dict[str, Any]) -> bool:
        """Create a new configuration template.

        Args:
            name: Template name
            template_data: Template configuration data

        Returns:
            True if creation successful, False otherwise
        """
        try:
            self.templates_dir.mkdir(parents=True, exist_ok=True)

            template_path = self.templates_dir / f"{name}.json"

            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(template_data, f, indent=2)

            return True

        except Exception:
            return False

    def delete_template(self, name: str) -> bool:
        """Delete a configuration template.

        Args:
            name: Template name to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            template_path = self.templates_dir / f"{name}.json"

            if template_path.exists():
                template_path.unlink()
                return True

            return False

        except Exception:
            return False

    def validate_template(self, template_data: Dict[str, Any]) -> List[str]:
        """Validate template configuration.

        Args:
            template_data: Template data to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check required fields
        if "command" not in template_data:
            errors.append("Template missing 'command' field")

        if "args" not in template_data:
            errors.append("Template missing 'args' field")
        elif not isinstance(template_data["args"], list):
            errors.append("Template 'args' must be a list")

        # Check optional fields
        if "env" in template_data and not isinstance(template_data["env"], dict):
            errors.append("Template 'env' must be a dictionary")

        return errors

    def generate_default_templates(self) -> bool:
        """Generate default configuration templates.

        Returns:
            True if generation successful, False otherwise
        """
        default_templates = {
            "filesystem_template": {
                "description": "Template for filesystem MCP server",
                "env": {"FILESYSTEM_ROOT": "{root_path}"},
            },
            "sqlite_template": {
                "description": "Template for SQLite MCP server",
                "env": {"SQLITE_DATABASE": "{database_path}"},
            },
            "git_template": {
                "description": "Template for Git MCP server",
                "env": {"GIT_REPOSITORY": "{repository_path}"},
            },
            "postgres_template": {
                "description": "Template for PostgreSQL MCP server",
                "env": {
                    "POSTGRES_CONNECTION": "postgresql://{user}:{password}@{host}:{port}/{database}"
                },
            },
            "redis_template": {
                "description": "Template for Redis MCP server",
                "env": {
                    "REDIS_HOST": "{host}",
                    "REDIS_PORT": "{port}",
                    "REDIS_PASSWORD": "{password}",
                },
            },
            "github_template": {
                "description": "Template for GitHub MCP server",
                "env": {"GITHUB_ACCESS_TOKEN": "{access_token}"},
            },
            "brave_search_template": {
                "description": "Template for Brave Search MCP server",
                "env": {"BRAVE_API_KEY": "{api_key}"},
            },
            "slack_template": {
                "description": "Template for Slack MCP server",
                "env": {"SLACK_BOT_TOKEN": "{bot_token}"},
            },
            "aws_s3_template": {
                "description": "Template for AWS S3 MCP server",
                "env": {
                    "AWS_ACCESS_KEY_ID": "{access_key_id}",
                    "AWS_SECRET_ACCESS_KEY": "{secret_access_key}",
                    "AWS_DEFAULT_REGION": "{region}",
                    "S3_BUCKET_NAME": "{bucket_name}",
                },
            },
            "docker_template": {
                "description": "Template for Docker MCP server",
                "env": {"DOCKER_HOST": "unix:///var/run/docker.sock"},
            },
        }

        try:
            self.templates_dir.mkdir(parents=True, exist_ok=True)

            for name, template in default_templates.items():
                if not self.create_template(name, template):
                    return False

            return True

        except Exception:
            return False
