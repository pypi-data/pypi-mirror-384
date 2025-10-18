"""Request Management plugin for VSS CLI (vss-cli)."""
import click

from vss_cli.cli import pass_context
from vss_cli.config import Configuration


@click.group('request', short_help='Manage various requests')
@pass_context
def cli(ctx: Configuration):
    """Track request status and details."""
    with ctx.spinner(disable=ctx.debug) as spinner_cls:
        ctx.load_config(spinner_cls=spinner_cls)


from vss_cli.plugins.request_plugins import (  # isort:skip
    change,
    export,
    folder,
    image,
    inventory,
    new,
    snapshot,
    vmdk,
    restore,
)  # pylint: disable=unused-import
