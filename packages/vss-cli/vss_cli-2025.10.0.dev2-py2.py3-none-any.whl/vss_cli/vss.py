"""VSS check vpn status."""
import logging
from typing import Dict, List

import requests

from vss_cli.utils.emoji import EMOJI_UNICODE
from vss_cli.vssconst import VSS_VPN_ENDPOINT

_LOGGING = logging.getLogger(__name__)


def check_vpn_status() -> List[Dict]:
    """Check vpn status."""
    icon = EMOJI_UNICODE.get(':question_mark:')
    result = []
    try:
        r = requests.get(VSS_VPN_ENDPOINT)
        _status = r.json()

        vpn_instances = _status.get('vpn')
        for instance in vpn_instances:
            status = instance.get('stat', 'unknown')
            iid = instance['id']
            if status in ['up']:
                status = 'operational'
                icon = EMOJI_UNICODE.get(':white_heavy_check_mark:')
            elif status in ['down']:
                icon = EMOJI_UNICODE.get(':cross_mark:')
            vpn_instance = {
                "name": f"ITS Private Cloud VPN {iid.upper()}",
                "status": status,
                "icon": icon,
            }
            result.append(vpn_instance)
    except Exception as ex:
        _LOGGING.warning(f'VSS VPN lookup failed: {ex}')
    return result


def check_stor_status():
    """TODO: Check stor status."""
    return
