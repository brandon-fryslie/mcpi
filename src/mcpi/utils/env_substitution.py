"""Environment variable substitution utilities.

Provides functions to substitute ${ENV_VAR} patterns with actual
environment variable values, allowing config files to reference
secrets without embedding them directly.
"""

import os
import re
from typing import Any, Dict


# Pattern matches ${VAR_NAME} or ${VAR_NAME:-default}
ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def substitute_env_vars(value: str) -> str:
    """Substitute environment variable references in a string.

    Supports two formats:
    - ${VAR_NAME}: Replaced with env var value, empty string if not set
    - ${VAR_NAME:-default}: Replaced with env var value, or default if not set

    Args:
        value: String potentially containing ${VAR} patterns

    Returns:
        String with all ${VAR} patterns replaced with actual values

    Examples:
        >>> os.environ["API_KEY"] = "secret123"
        >>> substitute_env_vars("Bearer ${API_KEY}")
        'Bearer secret123'
        >>> substitute_env_vars("${MISSING:-fallback}")
        'fallback'
    """

    def replace_match(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default_value = match.group(2)  # None if no default specified
        env_value = os.environ.get(var_name)

        if env_value is not None:
            return env_value
        if default_value is not None:
            return default_value
        return ""

    return ENV_VAR_PATTERN.sub(replace_match, value)


def substitute_env_vars_in_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively substitute environment variables in a dictionary.

    Only string values are processed; nested dicts are recursed into.
    Lists of strings are also processed.

    Args:
        data: Dictionary potentially containing ${VAR} patterns in values

    Returns:
        New dictionary with all string values having ${VAR} patterns replaced
    """
    result: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = substitute_env_vars(value)
        elif isinstance(value, dict):
            result[key] = substitute_env_vars_in_dict(value)
        elif isinstance(value, list):
            result[key] = [
                substitute_env_vars(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def substitute_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Substitute environment variables in HTTP headers.

    This is the primary entry point for processing header values
    that may contain credential references.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        New dictionary with env vars substituted in values

    Example:
        >>> os.environ["ZAI_API_KEY"] = "sk-12345"
        >>> substitute_headers({"Authorization": "Bearer ${ZAI_API_KEY}"})
        {'Authorization': 'Bearer sk-12345'}
    """
    return {key: substitute_env_vars(value) for key, value in headers.items()}


def has_env_var_reference(value: str) -> bool:
    """Check if a string contains any ${VAR} references.

    Useful for validation or displaying warnings when env vars
    are referenced but not set.

    Args:
        value: String to check

    Returns:
        True if the string contains ${VAR} patterns
    """
    return bool(ENV_VAR_PATTERN.search(value))


def get_referenced_env_vars(value: str) -> list[str]:
    """Extract all environment variable names referenced in a string.

    Args:
        value: String potentially containing ${VAR} patterns

    Returns:
        List of variable names referenced (without ${} wrapper)

    Example:
        >>> get_referenced_env_vars("${API_KEY} and ${SECRET}")
        ['API_KEY', 'SECRET']
    """
    return [match.group(1) for match in ENV_VAR_PATTERN.finditer(value)]


def check_missing_env_vars(headers: Dict[str, str]) -> list[str]:
    """Check for any missing environment variables in headers.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        List of environment variable names that are referenced but not set

    Example:
        >>> # Assuming MISSING_VAR is not set
        >>> check_missing_env_vars({"Auth": "Bearer ${MISSING_VAR}"})
        ['MISSING_VAR']
    """
    missing = []
    for value in headers.values():
        for var_name in get_referenced_env_vars(value):
            if var_name not in os.environ and var_name not in missing:
                missing.append(var_name)
    return missing
