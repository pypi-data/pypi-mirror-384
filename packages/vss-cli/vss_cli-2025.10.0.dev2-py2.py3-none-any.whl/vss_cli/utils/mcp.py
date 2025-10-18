"""MCP utils."""
import json
import logging
from pathlib import Path
from typing import Any

from vss_cli.exceptions import VssCliError

_LOGGING = logging.getLogger(__name__)


def update_claude_config(
    command_spec: str | Path,
    server_name: str,
    *,
    args: list[str] | None = None,
    env_vars: dict[str, str] | None = None,
) -> bool:
    """Add or update a FastMCP server in Claude's configuration.

    Based on mcp.cli.claude.update_claude_config.

    Args:
        command_spec: Path to the server file, optionally with :object suffix
        server_name: Name for the server in Claude's config
        args: Optional list of arguments to pass to the server.
        env_vars: Optional dictionary of environment variables.
            These are merged with any existing variables,
            with new values taking precedence.

    Raises:
        RuntimeError: If Claude Desktop's config directory
            is not found, indicating Claude Desktop may not be installed
            or properly set up.
    """
    try:
        from fastmcp.cli import claude
    except ImportError:
        raise VssCliError(
            'mcp-vss dependency not found. '
            'try running "pip install vss-cli[mcp]"'
        )
    config_dir = claude.get_claude_config_path()
    if not config_dir:
        raise RuntimeError(
            "Claude Desktop config directory not found. "
            "Please ensure Claude Desktop"
            " is installed and has been run at least "
            "once to initialize its config."
        )

    config_file = Path(config_dir).joinpath("claude_desktop_config.json")

    if not config_file.exists():
        try:
            config_file.write_text("{}")
        except Exception as e:
            _LOGGING.error(
                "Failed to create Claude config file",
                extra={
                    "error": str(e),
                    "config_file": str(config_file),
                },
            )
            return False

    try:
        config = json.loads(config_file.read_text())
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Always preserve existing env vars and merge with new ones
        if (
            server_name in config["mcpServers"]
            and "env" in config["mcpServers"][server_name]
        ):
            existing_env = config["mcpServers"][server_name]["env"]
            if env_vars:
                # New vars take precedence over existing ones
                env_vars = {**existing_env, **env_vars}
            else:
                env_vars = existing_env
        # Convert file path to absolute before adding to command
        # Split off any :object suffix first
        if ":" in command_spec:
            file_path, server_object = command_spec.rsplit(":", 1)
            command_spec = f"{Path(file_path).resolve()}:{server_object}"
        else:
            command_spec = str(Path(command_spec).resolve())

        server_config: dict[str, Any] = {"command": command_spec, "args": args}

        # Add environment variables if specified
        if env_vars:
            server_config["env"] = env_vars

        config["mcpServers"][server_name] = server_config

        config_file.write_text(json.dumps(config, indent=2))
        _LOGGING.info(
            f"Added server '{server_name}' to Claude config",
            extra={"config_file": str(config_file)},
        )
        return True
    except Exception as e:
        _LOGGING.error(
            "Failed to update Claude config",
            extra={
                "error": str(e),
                "config_file": str(config_file),
            },
        )
        return False
