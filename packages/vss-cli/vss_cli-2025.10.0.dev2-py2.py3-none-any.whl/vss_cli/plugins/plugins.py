"""Plugins plugin for VSS CLI (vss-cli)."""
import logging

import click
from click_plugins import with_plugins

try:
    import importlib_metadata as ilm
except ImportError:
    import importlib.metadata as ilm

from vss_cli.cli import pass_context
from vss_cli.config import Configuration

_LOGGING = logging.getLogger(__name__)


@with_plugins(ilm.entry_points(group='vss_cli.contrib.plugins'))
@click.group('plugins', short_help='External plugins.')
@pass_context
def cli(ctx: Configuration):
    """Load External CLI plugins."""
    with ctx.spinner(disable=ctx.debug):
        ctx.load_config()
