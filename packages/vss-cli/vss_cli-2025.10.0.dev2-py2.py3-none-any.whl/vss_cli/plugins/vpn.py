"""VPN related commands."""
import logging
import sys
from datetime import datetime, timedelta, timezone

import click
import pytz

from vss_cli import const
from vss_cli.cli import pass_context
from vss_cli.config import Configuration
from vss_cli.utils.emoji import EMOJI_UNICODE

_LOGGING = logging.getLogger(__name__)
ej_rkt = EMOJI_UNICODE.get(':rocket:')
ej_warn = EMOJI_UNICODE.get(':alien:')


@click.group('vpn', short_help='Manage your VSS VPN account.')
@pass_context
def cli(ctx: Configuration):
    """Manage your VSS vpn account."""
    with ctx.spinner(disable=ctx.debug) as spinner_cls:
        ctx.load_config(spinner_cls=spinner_cls, validate=False)


@cli.group('gw', short_help='manage vpn MFA gateway')
@pass_context
def gateway(ctx: Configuration):
    """Manage vpn via mfa."""
    # TODO: check for vpn status
    pass


@gateway.command('on', short_help='enable vpn via mfa')
@click.option(
    '--otp', '-o', prompt='Provide Timed One-Time Password', help='OTP string'
)
@pass_context
def gateway_on(ctx: Configuration, otp):
    """Enable vpn via mfa."""
    click.echo(f'Attempting to enable VPN GW: {ctx.vpn_server}')
    status = ctx.get_vss_vpn_status()
    _LOGGING.debug(f'{status=}')
    if status:
        if not status.get('usages'):
            _LOGGING.error(
                f'VPN GW {ctx.vpn_server} has MFA disabled. '
                f'Enable VPN GW MFA via {ctx.vss_vpn_otp_svc_endpoint}'
            )
            sys.exit(1)
        _LOGGING.info(
            f'VPN GW {ctx.vpn_server} MFA enabled on: '
            f'{status["usages"]} via {status["method"]}'
        )
    with ctx.spinner(disable=ctx.debug) as spinner_cls:
        ctx.totp = otp
        try:
            rv = ctx.enable_vss_vpn()
            _LOGGING.debug(f'{rv}')
            spinner_cls.stop()
            # _LOGGING.warning(rv['log'])
            click.echo(
                f'Successfully enabled. '
                f'Ready to connect to {ctx.vpn_server} {ej_rkt}'
            )
            spinner_cls.start()
        except Exception as e:
            _LOGGING.error(f'An error occurred {ej_warn}: {e}')


@gateway.command('off', short_help='disable vpn via mfa')
@pass_context
def gateway_off(ctx: Configuration):
    """Disable vpn via mfa."""
    click.echo(f'Attempting to disable VPN GW: {ctx.vpn_server}')
    with ctx.spinner(disable=ctx.debug) as spinner_cls:
        try:
            rv = ctx.disable_vss_vpn()
            _LOGGING.debug(f'{rv}')
            spinner_cls.stop()
            click.echo('Successfully disabled VPN GW. ')
            spinner_cls.start()
        except Exception as e:
            _LOGGING.error(f'An error occurred {ej_warn}: {e}')


@gateway.command('log', short_help='get vpn logs')
@click.option(
    '-t',
    '--timestamp',
    type=click.DateTime(formats=[const.DEFAULT_DATETIME_FMT]),
    default=datetime.strftime(
        datetime.now() - timedelta(hours=1), const.DEFAULT_DATETIME_FMT
    ),
    required=False,
    show_default=True,
    help='Timestamp to retrieve logs from.',
)
@pass_context
def gateway_log(ctx: Configuration, timestamp):
    """Get logs from VPN GW."""
    with ctx.spinner(disable=ctx.debug):
        try:
            local_dt = pytz.timezone('America/Toronto').localize(
                timestamp, is_dst=None
            )
            _LOGGING.debug(f'{local_dt=}')
            utc_dt = local_dt.astimezone(pytz.utc)
            _LOGGING.debug(f'{utc_dt=}')
            rv = ctx.monitor_vss_vpn(stamp=utc_dt)
            _LOGGING.debug(f'{rv}')
        except Exception as e:
            _LOGGING.error(f'An error occurred {ej_warn}: {e}')
            sys.exit(1)
        # iterate through log
        for log in rv['log']:
            click.echo(log)


@cli.command('la', short_help='launch ui')
@click.argument(
    'ui_type',
    type=click.Choice(
        ['ui', 'otp-svc', 'otp-enable', 'otp-disable', 'otp-monitor']
    ),
    required=True,
    default='ui',
)
@pass_context
def stor_launch(ctx: Configuration, ui_type):
    """Launch web ui."""
    _ = ctx.init_vss_vpn(ctx.vpn_server)
    lookup = {
        'ui': ctx.vss_vpn_endpoint,
        'otp-svc': ctx.vss_vpn_otp_svc_endpoint,
        'otp-enable': ctx.vss_vpn_otp_enable_endpoint,
        'otp-disable': ctx.vss_vpn_otp_disable_endpoint,
        'otp-monitor': ctx.vss_vpn_otp_monitor_endpoint,
    }
    url = lookup[ui_type]
    click.echo(f'Launching {EMOJI_UNICODE[":globe_showing_Americas:"]}: {url}')
    click.launch(
        url,
    )
