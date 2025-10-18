"""OVF plugin for VSS CLI (vss-cli)."""
import logging
from pathlib import Path

import click

from vss_cli import const, rel_opts as so
from vss_cli.cli import pass_context
from vss_cli.config import Configuration
from vss_cli.helper import format_output, raw_format_output

_LOGGING = logging.getLogger(__name__)


@click.group('ovf', short_help='OVF Tool')
@pass_context
def cli(ctx: Configuration):
    """Manage OVF and OVA."""
    ctx.set_defaults()


@cli.group(
    'get',
    short_help='Load and analyze OVA or OVF.',
    invoke_without_command=True,
)
@click.argument('file_path', type=click.Path(exists=True), required=True)
@pass_context
def get_ovf(ctx: Configuration, file_path):
    """Load and analyze OVA or OVF."""
    ctx.ova_or_ovf = file_path
    obj = ctx.parse_ova_or_ovf(file_path)
    ctx.ovf_dict = obj
    if click.get_current_context().invoked_subcommand is None:
        columns = ctx.columns or const.COLUMNS_OVF
        click.echo(format_output(ctx, [obj], columns=columns, single=True))


@get_ovf.command('property-params', short_help='Get Property parameters.')
@so.page_opt
@pass_context
def get_ovf_property_params(ctx: Configuration, page):
    """Get OVF property params (if any)."""
    objs = ctx.ovf_dict.get('PropertyParams', [])
    # including additional attributes?
    columns = ctx.columns or const.COLUMNS_OVF_PP
    # format output
    output = format_output(ctx, objs, columns=columns)
    # page
    if page:
        click.echo_via_pager(output)
    else:
        ctx.echo(output)


@get_ovf.command(
    'deployment-params', short_help='Get Deployment Option parameters'
)
@so.page_opt
@pass_context
def get_ovf_deployment_params(ctx: Configuration, page):
    """Get OVF deployment params (if any)."""
    objs = ctx.ovf_dict.get('DeploymentOptionParams', [])
    # including additional attributes?
    columns = ctx.columns or const.COLUMNS_OVF_DP
    # format output
    output = format_output(ctx, objs, columns=columns)
    # page
    if page:
        click.echo_via_pager(output)
    else:
        ctx.echo(output)


@get_ovf.command('params-spec', short_help='Generate additional-params spec')
@click.option(
    '--edit/--no-edit',
    is_flag=True,
    required=False,
    help='Edit before writing',
)
@pass_context
def get_ovf_additional_params_spec(ctx: Configuration, edit):
    """Generate additional params file spec."""
    new_raw = None
    if ctx.output in ['auto', 'table']:
        _LOGGING.warning(f'Input set to {ctx.output}. Falling back to yaml')
        ctx.output = 'yaml'
    source_name = Path(ctx.ova_or_ovf).stem
    deployment_params_comment = ''
    property_params_comment = ''
    f_name = f'{source_name}-additional-params.{ctx.output}'
    obj = ctx.ovf_dict

    n_obj = {}
    if obj.get('PropertyParams'):
        property_params = {
            x.get('key'): x.get('default')
            for x in obj.get('PropertyParams', [{}])
        }
        property_params_comment = '\n'.join(
            [
                f'# {x["key"]} ({x["type"]}): {x["description"]}'.replace(
                    '\n', ''
                )
                for x in obj.get('PropertyParams', [{}])
            ]
        )
        property_params_comment = (
            f'# PropertyParams:\n{property_params_comment}'
        )
        n_obj['PropertyParams'] = property_params
    if obj.get('DeploymentOptionParams'):
        deployment_params_comment = '\n'.join(
            [
                f'# {x["id"]}: {x["description"]}'
                for x in obj.get('DeploymentOptionParams', [{}])
            ]
        )
        deployment_params_comment = (
            f'# DeploymentOptionParams:\n{deployment_params_comment}'
        )
        deploy_params = {'selected_key': ''}
        n_obj['DeploymentOptionParams'] = deploy_params

    if edit:
        obj_raw = raw_format_output(
            ctx.output, n_obj, ctx.yaml(), highlighted=False
        )
        obj_raw = '\n'.join(
            [obj_raw, deployment_params_comment, property_params_comment]
        )
        new_raw = click.edit(obj_raw, extension=f'.{ctx.output}')

    if new_raw:
        n_obj = ctx.yaml_load(new_raw)
    # writing objects
    with open(f_name, 'w') as fp:
        ctx.yaml_dump_stream(n_obj, stream=fp)
    ctx.echo(f'Written to {f_name}')
