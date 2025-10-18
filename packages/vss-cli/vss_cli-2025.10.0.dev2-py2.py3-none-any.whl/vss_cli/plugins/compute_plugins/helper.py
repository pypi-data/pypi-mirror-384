"""Helper module for the vss-cli compute plugins."""
from typing import Dict, Optional, Tuple, Union

import click


def get_restore_user_confirmation(
    ctx, _vm, _rp, reason
) -> Tuple[str, str, Dict[str, str]]:
    """Get restore user confirmation."""
    from vss_cli import const

    c_str = const.DEFAULT_VM_RESTORE_MSG.format(vm=_vm[0], rp=_rp[0])
    storage_type = _vm[0]['storage_type']
    if storage_type not in const.VM_RESTORE_PRICE_GB.keys():
        raise click.BadParameter(
            f"Unsupported Storage type: {storage_type}. "
            f"Please reach out to us for more information."
        )

    confirmation = click.confirm(c_str)
    # provide reason
    restore_reason = reason or click.prompt(
        'Please provide a restore reason',
    )
    if not restore_reason:
        raise click.BadArgumentUsage('Reason for restore is required.')
    reason_payload = {'restore_reason': restore_reason}
    # provisioned_gb,
    c2_fmt = const.VM_RESTORE_PRICE_GB.copy()
    c2_fmt['provisioned_gb'] = _vm[0]['provisioned_gb']
    c2_fmt['total_gb'] = (
        const.VM_RESTORE_PRICE_GB[storage_type]
        * _vm[0]['provisioned_gb']
    )
    c2_str = const.CONFIRM_VM_RESTORE_MSG.format(**c2_fmt)
    confirmation_2 = click.confirm(c2_str)
    return confirmation, confirmation_2, reason_payload


def process_retirement_new(
    retire_type: str,
    retire_value: Union[Tuple[int, int, int], str],
    retire_warning: Optional[int] = None,
) -> Dict:
    """Process retirement for new vm commands."""
    if not all([retire_type, retire_value]):
        raise click.BadParameter(
            'Retirement settings require at least: '
            '--retire-type and --retire-value'
        )
    if retire_type == 'timedelta':
        retire = {
            'value': {
                'type': retire_type,
                'hours': retire_value[0],
                'days': retire_value[1],
                'months': retire_value[2],
            }
        }
    else:
        retire = {'value': {'type': retire_type, 'datetime': retire_value}}
    if retire_warning:
        retire['warning'] = {'days': retire_warning}
    else:
        confirmation = click.confirm(
            'No warning will be sent for confirmation or cancellation. \n'
            'Retirement request will proceed when specified. \n'
            'Are you sure?'
        )
        if not confirmation:
            raise click.ClickException('Cancelled by user.')
    return retire
