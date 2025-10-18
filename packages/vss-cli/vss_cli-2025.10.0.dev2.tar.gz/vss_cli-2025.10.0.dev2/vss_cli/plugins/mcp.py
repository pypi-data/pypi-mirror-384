"""MCP server module."""
import logging
import shutil
import sys

import click

from vss_cli.cli import pass_context
from vss_cli.config import Configuration
from vss_cli.exceptions import VssCliError
from vss_cli.utils.mcp import update_claude_config

_LOGGING = logging.getLogger(__name__)


@click.group('mcp', short_help='Manage the Model Context Protocol Server.')
@pass_context
def cli(ctx: Configuration):
    """Manage the Model Context Protocol Server."""
    with ctx.spinner(disable=ctx.debug) as spinner_cls:
        ctx.load_config(spinner_cls=spinner_cls)


@cli.command('install')
@click.option('--name', help='MCP server name', default='its-private-cloud')
@click.option(
    "--transport",
    type=click.Choice(['stdio', 'sse', 'http']),
    default='stdio',
    help="Transport protocol to use (stdio, sse, or http)",
)
@click.option(
    "--host",
    default="localhost",
    help="Host to bind to for HTTP/SSE transport (default: localhost)",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to bind to for HTTP/SSE transport (default: 8000)",
)
@pass_context
def install(
    ctx: Configuration, name: str, transport: str, port: int, host: str
):
    """Install in claude client."""
    try:
        from fastmcp.cli import claude
    except ImportError:
        raise VssCliError(
            'mcp-vss dependency not found. '
            'try running "pip install vss-cli[mcp]"'
        )
    claude_path = claude.get_claude_config_path()
    if not claude_path:
        _LOGGING.error("Claude app not found")
        sys.exit(1)
    # Claude
    path = shutil.which("vss-cli")
    _LOGGING.debug(f"Found claude in: {claude_path}. Will install {path}")
    args = ['mcp', 'run', '--transport', transport]
    if transport in ['http', 'sse']:
        if host:
            args.extend(['--host', host])
        if port:
            args.extend(['--port', port])
    # get current
    if update_claude_config(command_spec=path, server_name=name, args=args):
        _LOGGING.info(f"Successfully installed {name} in Claude app")
    else:
        _LOGGING.error(f"Failed to install {name} in Claude app")
        sys.exit(1)


@cli.command('run')
@click.option(
    "--transport",
    type=click.Choice(['stdio', 'sse', 'http']),
    default='stdio',
    help="Transport protocol to use (stdio, sse, or http)",
)
@click.option(
    "--host",
    default="localhost",
    help="Host to bind to for HTTP/SSE transport (default: localhost)",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to bind to for HTTP/SSE transport (default: 8000)",
)
@pass_context
def run(ctx: Configuration, transport, host, port):
    """Run the MCP server."""
    try:
        from mcp_server_vss.server import create_app
    except ImportError:
        raise VssCliError(
            'mcp-vss dependency not found. '
            'try running "pip install vss-cli[mcp]"'
        )
    _LOGGING.info(f"Starting VSS MCP server with endpoint: {ctx.api_endpoint}")
    _LOGGING.info(f"Using transport: {transport}")
    # Create the FastMCP application
    try:
        mcp_server = create_app(ctx.api_token, ctx.base_endpoint)
    except Exception as e:
        _LOGGING.error(f"Failed to create MCP app: {e}")
        raise
    # Run with the specified transport
    if transport == 'stdio':
        _LOGGING.info("Starting stdio transport...")
        mcp_server.run()
    elif transport == 'sse':
        _LOGGING.info(f"Starting SSE transport on {host}:{port}...")
        mcp_server.run(host=host, port=port, transport='sse')
    elif transport == 'http':
        _LOGGING.info(f"Starting HTTP transport on {host}:{port}...")
        import uvicorn

        http_app = mcp_server.http_app()
        uvicorn.run(http_app, host=host, port=port)
    else:
        raise ValueError(f"Unsupported transport: {transport}")
