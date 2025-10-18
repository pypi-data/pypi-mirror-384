"""VM Restore Request Management plugin for VSS CLI (vss-cli)."""
import logging

import click

from vss_cli import autocompletion, const
from vss_cli import rel_opts as so
from vss_cli.cli import pass_context
from vss_cli.config import Configuration
from vss_cli.helper import format_output
from vss_cli.plugins.request import cli

_LOGGING = logging.getLogger(__name__)


@cli.group('restore', short_help='Manage virtual machine restore requests')
@pass_context
def request_mgmt_restore(ctx: Configuration):
    """Manage virtual machine restore requests."""
    pass


@request_mgmt_restore.command('ls', short_help='list vm restore requests')
@so.filter_opt
@so.all_opt
@so.count_opt
@so.page_opt
@so.sort_opt
@pass_context
def request_mgmt_res_ls(
    ctx: Configuration, filter_by, page, sort, show_all, count
):
    """List requests.

    Filter list in the following format <field_name> <operator>,<value>
    where operator is eq, ne, lt, le, gt, ge, like, in.
    For example: status=eq,PROCESSED

    vss-cli request restore ls -f status=eq,SUBMITTED

    Sort list in the following format <field_name>=<asc|desc>. For example:

    vss-cli request retire ls -s created_on=desc
    """
    columns = ctx.columns or const.COLUMNS_REQUEST_RESTORE
    _LOGGING.debug(f'Columns {columns}')
    params = dict(expand=1, sort='created_on,desc', groups=1)
    if all(filter_by):
        params['filter'] = ';'.join(filter_by)
    if all(sort):
        params['sort'] = ';'.join(sort)
    # make request
    with ctx.spinner(disable=ctx.debug):
        _requests = ctx.get_restore_requests(
            show_all=show_all, per_page=count, **params
        )

    output = format_output(ctx, _requests, columns=columns)
    # page results
    if page:
        click.echo_via_pager(output)
    else:
        ctx.echo(output)


@request_mgmt_restore.command('get', short_help='Restore request info')
@click.argument(
    'rid',
    type=click.INT,
    required=True,
    shell_complete=autocompletion.restore_requests,
)
@pass_context
def request_mgmt_res_get(ctx: Configuration, rid):
    """Get Retirement Request info."""
    # make request
    with ctx.spinner(disable=ctx.debug):
        obj = ctx.request(f'/request/restore/{rid}')
        obj = obj.get('data')
    columns = ctx.columns or const.COLUMNS_REQUEST_RESTORE
    ctx.echo(format_output(ctx, [obj], columns=columns, single=True))
