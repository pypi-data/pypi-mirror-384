"""
JSON utility functions for MCP configuration management.

Provides JSON merging, validation, and variable expansion for MCP configs.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JSONConfigError(Exception):
    """Raised when JSON configuration operations fail."""

    pass


def expand_variables(
    config: dict[str, Any], variables: dict[str, str]
) -> dict[str, Any]:
    """
    Expand variables in JSON configuration.

    Recursively replaces ${VARIABLE_NAME} with actual values.

    Args:
        config: Configuration dictionary
        variables: Variable mappings {name: value}

    Returns:
        Configuration with variables expanded
    """

    def expand_value(value: Any) -> Any:
        """Recursively expand variables in value."""
        if isinstance(value, str):
            # Replace all ${VAR} patterns
            result = value
            for var_name, var_value in variables.items():
                result = result.replace(f"${{{var_name}}}", var_value)
            return result
        elif isinstance(value, dict):
            return {k: expand_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [expand_value(item) for item in value]
        return value

    return expand_value(config)


def merge_json_configs(
    existing: dict[str, Any], new: dict[str, Any], preserve_existing: bool = True
) -> dict[str, Any]:
    """
    Merge two JSON configurations, preserving existing MCP servers.

    Args:
        existing: Existing configuration
        new: New configuration to merge
        preserve_existing: If True, existing values take precedence

    Returns:
        Merged configuration

    Example:
        >>> existing = {"mcpServers": {"server1": {...}}}
        >>> new = {"mcpServers": {"server2": {...}}}
        >>> merged = merge_json_configs(existing, new)
        >>> # Result: {"mcpServers": {"server1": {...}, "server2": {...}}}
    """
    if not isinstance(existing, dict) or not isinstance(new, dict):
        return new if not preserve_existing else existing

    result = existing.copy()

    for key, new_value in new.items():
        if key not in result:
            # Key doesn't exist, add it
            result[key] = new_value
        elif isinstance(result[key], dict) and isinstance(new_value, dict):
            # Both are dicts, merge recursively
            result[key] = merge_json_configs(result[key], new_value, preserve_existing)
        elif preserve_existing:
            # Preserve existing value
            logger.debug(f"Preserving existing value for key: {key}")
        else:
            # Overwrite with new value
            result[key] = new_value

    return result


def load_json_config(file_path: Path) -> dict[str, Any]:
    """
    Load JSON configuration from file.

    Args:
        file_path: Path to JSON file

    Returns:
        Configuration dictionary

    Raises:
        JSONConfigError: If file cannot be loaded or parsed
    """
    try:
        if not file_path.exists():
            return {}

        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise JSONConfigError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise JSONConfigError(f"Failed to load {file_path}: {e}")


def save_json_config(file_path: Path, config: dict[str, Any], indent: int = 2) -> None:
    """
    Save JSON configuration to file.

    Args:
        file_path: Path to save to
        config: Configuration dictionary
        indent: JSON indentation level

    Raises:
        JSONConfigError: If file cannot be saved
    """
    try:
        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with pretty formatting
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=indent, ensure_ascii=False)
            f.write("\n")  # Add trailing newline

        logger.info(f"Saved JSON configuration to {file_path}")
    except Exception as e:
        raise JSONConfigError(f"Failed to save {file_path}: {e}")


def validate_mcp_config(config: dict[str, Any]) -> list[str]:
    """
    Validate MCP server configuration.

    Args:
        config: MCP configuration dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check for mcpServers key (most common) or servers (VS Code variant)
    if "mcpServers" not in config and "servers" not in config:
        errors.append("Missing 'mcpServers' or 'servers' key in configuration")
        return errors

    # Validate each server
    servers_key = "mcpServers" if "mcpServers" in config else "servers"
    servers = config.get(servers_key, {})

    if not isinstance(servers, dict):
        errors.append(f"'{servers_key}' must be a dictionary")
        return errors

    for server_name, server_config in servers.items():
        if not isinstance(server_config, dict):
            errors.append(f"Server '{server_name}' configuration must be a dictionary")
            continue

        # Check required fields
        if "command" not in server_config:
            errors.append(f"Server '{server_name}' missing required 'command' field")

    return errors


def get_standard_variables(project_root: Path | None = None) -> dict[str, str]:
    """
    Get standard variable mappings for MCP configurations.

    Args:
        project_root: Project root directory (optional)

    Returns:
        Dictionary of variable mappings
    """
    variables = {
        "HOME": str(Path.home()),
        "USER": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
    }

    if project_root:
        variables["PROJECT_ROOT"] = str(project_root.resolve())

    return variables


def create_mcp_server_config(
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Create a standard MCP server configuration.

    Args:
        command: Command to run the MCP server
        args: Command arguments (optional)
        env: Environment variables (optional)

    Returns:
        MCP server configuration dictionary
    """
    config: dict[str, Any] = {"command": command}

    if args:
        config["args"] = args

    if env:
        config["env"] = env

    return config
