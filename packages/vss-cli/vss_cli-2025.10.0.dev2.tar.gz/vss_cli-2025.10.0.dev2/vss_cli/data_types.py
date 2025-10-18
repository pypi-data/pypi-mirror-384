"""Data types definitions."""
import json
import logging
import re
from dataclasses import dataclass, field
from ipaddress import (
    AddressValueError, IPv4Address, IPv4Network, NetmaskValueError)
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from click import BadArgumentUsage, BadParameter
from dataclasses_json import config as dc_config
from dataclasses_json import dataclass_json
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from validators import domain as is_domain
from validators import email as is_email_address
from validators import url as is_url

import vss_cli.const as const
from vss_cli.exceptions import ValidationError
from vss_cli.validators import validate_email

_LOGGING = logging.getLogger(__name__)


class Url(str):
    """URL data class."""

    def __new__(cls, val):
        """Create new class method."""
        if is_url(val):
            return str.__new__(cls, val)
        else:
            raise ValidationError(f'{val} is not a valid URL')


@dataclass_json
@dataclass
class ConfigFileGeneral:
    """Configuration General section class."""

    check_for_updates: bool = const.DEFAULT_CHECK_UPDATES
    check_for_messages: bool = const.DEFAULT_CHECK_MESSAGES
    default_endpoint_name: str = const.DEFAULT_ENDPOINT_NAME
    s3_server: str = const.DEFAULT_S3_SERVER
    vpn_server: str = const.DEFAULT_VPN_SERVER
    gpt_server: str = const.DEFAULT_GPT_SERVER
    gpt_persona: int = const.DEFAULT_GPT_PERSONA
    gpt_token: str = const.DEFAULT_GPT_TOKEN
    debug: bool = const.DEFAULT_DEBUG
    output: str = const.DEFAULT_RAW_OUTPUT
    table_format: str = const.DEFAULT_TABLE_FORMAT
    timeout: int = const.DEFAULT_TIMEOUT
    verbose: bool = const.DEFAULT_VERBOSE
    columns_width: int = const.DEFAULT_COLUMNS_WIDTH
    wait_for_requests: bool = const.DEFAULT_WAIT_FOR_REQUESTS


@dataclass_json
@dataclass
class ConfigEndpoint:
    """Configuration endpoint class."""

    url: Url
    name: Optional[str] = None
    auth: Optional[str] = None
    token: Optional[str] = None
    tf_enabled: Optional[bool] = False

    def __post_init__(self):
        """Post init method."""

        def get_hostname_from_url(
            url: str, hostname_regex: str = const.DEFAULT_HOST_REGEX
        ) -> str:
            """Parse hostname from URL."""
            re_search = re.search(hostname_regex, url)
            _, _hostname = re_search.groups() if re_search else ('', '')
            _host = _hostname.split('.')[0] if _hostname.split('.') else ''
            return _host

        if not self.name:
            self.name = get_hostname_from_url(self.url)


@dataclass_json
@dataclass
class ConfigFile:
    """Configuration file data class."""

    general: ConfigFileGeneral
    endpoints: Optional[Union[List[ConfigEndpoint]]] = field(
        default_factory=lambda: []
    )

    def get_endpoint(self, ep_name_or_url: str) -> List[ConfigEndpoint]:
        """Get an endpoint by name or url."""
        if self.endpoints:
            ep = list(
                filter(lambda i: ep_name_or_url == i.name, self.endpoints)
            ) or list(
                filter(lambda i: ep_name_or_url == i.url, self.endpoints)
            )
            return ep
        else:
            return []

    def update_endpoint(
        self, endpoint: ConfigEndpoint
    ) -> List[ConfigEndpoint]:
        """Update single endpoint."""
        if self.endpoints:
            for idx, val in enumerate(self.endpoints):
                if val.name == endpoint.name:
                    self.endpoints[idx] = endpoint
                    return self.endpoints
        else:
            self.endpoints = []
        # adding
        self.endpoints.append(endpoint)
        return self.endpoints

    def update_endpoints(
        self, *endpoints: List[ConfigEndpoint]
    ) -> List[ConfigEndpoint]:
        """Update multiple endpoints."""
        for endpoint in endpoints:
            self.update_endpoint(endpoint)
        return self.endpoints


class Email(str):
    """Email address."""

    def __new__(cls, val):
        """Create new."""
        if is_email_address(val):
            return str.__new__(cls, val)
        else:
            raise ValidationError(f'{val} is not a valid email address')


class IP(str):
    """Class IP address."""

    def __new__(cls, val):
        """Create new instance."""
        try:
            IPv4Address(val)
            return str.__new__(cls, val)
        except AddressValueError as e:
            raise ValidationError(
                f'{val} is not a valid IP address. Hint: {e.args[0]}'
            )


class Domain(str):
    """Domain."""

    def __new__(cls, val):
        """Create instance."""
        if is_domain(val):
            return str.__new__(cls, val)
        else:
            raise ValidationError(f'{val} is not a valid domain name')


class NetMask(str):
    """Net mask."""

    def __new__(cls, val):
        """Create instance."""
        try:
            IPv4Network('0.0.0.0/' + val)
            return str.__new__(cls, val)
        except NetmaskValueError as e:
            raise ValidationError(
                f'{val} is not a valid IP network mask. Hint: {e.args[0]}'
            )


@dataclass_json
@dataclass
class VmDisk:
    """Vm Disk spec."""

    capacity_gb: int
    backing_mode: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    backing_sharing: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    scsi: Optional[int] = field(
        default=0, metadata=dc_config(exclude=lambda x: x is None)
    )


@dataclass_json
@dataclass
class VmScsi:
    """Vm SCSI."""

    bus: int
    sharing: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    type: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )


@dataclass_json
@dataclass
class VmMachine:
    """Vm Machine."""

    name: str
    folder: Optional[str] = None
    os: Optional[str] = None
    source: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    domain: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    iso: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    power_on: Optional[bool] = field(default_factory=lambda: False)
    template: Optional[bool] = field(default_factory=lambda: False)
    tpm: Optional[bool] = field(default_factory=lambda: False)
    vbs: Optional[bool] = field(default_factory=lambda: False)
    disks: Optional[List[VmDisk]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    scsi: Optional[List[VmScsi]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    cpu: Optional[int] = field(default_factory=lambda: 1)
    memory: Optional[int] = field(default_factory=lambda: 1)
    firmware: Optional[str] = field(default_factory=lambda: 'efi')
    storage_type: Optional[str] = field(
        default='hdd',
        metadata=dc_config(
            exclude=lambda x: x is None, field_name="storage-type"
        ),
    )
    version: Optional[str] = field(default_factory=lambda: 'vmx-19')
    source_snapshot: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    item: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )


@dataclass_json
@dataclass
class VmNetwork:
    """Vm network."""

    network: str
    network_id: Optional[str] = field(
        default=None,
        metadata=dc_config(
            exclude=lambda x: x is None,
        ),
    )
    type: Optional[str] = field(default_factory=lambda x: 'vmxnet3')


@dataclass_json
@dataclass
class VmNetworking:
    """Vm networking."""

    interfaces: List[VmNetwork]


@dataclass_json
@dataclass
class VmMetaAdmin:
    """VM meta admin."""

    name: Optional[str]
    email: Optional[Email]
    phone: Optional[str]


@dataclass_json
@dataclass
class VmMeta:
    """Vm meta."""

    description: str
    usage: str
    client: str
    inform: Optional[List[str]] = None
    admin: Optional[VmMetaAdmin] = None
    vss_service: Optional[str] = None
    notes: Optional[List[Dict]] = None
    vss_options: Optional[List[str]] = None


@dataclass_json
@dataclass
class VmAdditionalParams:
    """Vm add params."""

    additional_parameters: Union[Path]


@dataclass_json
@dataclass
class VmDayZero:
    """Vm Day Zero."""

    config_file: Path = field(
        default=None,
        metadata=dc_config(
            exclude=lambda x: x is None, field_name="config-file"
        ),
    )
    config: Optional[str] = field(default=None)
    config_name: Optional[str] = field(
        default='day0-config',
        metadata=dc_config(
            exclude=lambda x: x is None, field_name="config-name"
        ),
    )

    id_token_file: Optional[Path] = field(
        default=None, metadata=dc_config(exclude=lambda x: True)
    )
    id_token_name: Optional[str] = field(
        default=None,
        metadata=dc_config(
            exclude=lambda x: x is None, field_name="id-token-name"
        ),
    )
    config_encoding: Optional[str] = field(
        default=None,
        metadata=dc_config(
            exclude=lambda x: x is None, field_name="config-encoding"
        ),
    )
    idtoken: Optional[str] = field(
        default=None,
        metadata=dc_config(exclude=lambda x: x is None, field_name="idtoken"),
    )
    idtoken_encoding: Optional[str] = field(
        default=None,
        metadata=dc_config(
            exclude=lambda x: x is None, field_name="idtoken-encoding"
        ),
    )
    idtoken_name: Optional[str] = field(
        default=None,
        metadata=dc_config(
            exclude=lambda x: x is None, field_name="id-token-name"
        ),
    )

    @staticmethod
    def _load_file(path: Path, attr: str) -> Tuple[str, str]:
        """Load file."""
        from pyvss.helper import compress_encode_string

        try:
            fp = Path(path)
            txt = fp.read_text()
            return (
                compress_encode_string(txt),
                'gzip+base64',
            )
        except FileNotFoundError as ex:
            raise BadArgumentUsage(f'{attr} must a valid file path: {ex}')

    def __post_init__(self):
        """Run post initializing."""
        self.config, self.config_encoding = self._load_file(
            self.config_file, 'config_file'
        )

        if self.id_token_file is not None:
            self.idtoken, self.idtoken_encoding = self._load_file(
                self.id_token, 'id_token_file'
            )


@dataclass_json
@dataclass
class VmCloudInit:
    """Vm Cloud init."""

    user_data: Union[Path]
    userdata: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    userdata_encoding: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    network_data: Optional[Path] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    networkconfig: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    networkconfig_encoding: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )

    @staticmethod
    def _load_yaml_file(path: Path, attr: str) -> Tuple[str, str]:
        """Load Yaml."""
        from pyvss.helper import compress_encode_string

        try:
            fp = Path(path)
            txt = fp.read_text()
            _ = YAML().load(txt)
            return (
                compress_encode_string(txt),
                'gzip+base64',
            )
        except FileNotFoundError:
            raise BadArgumentUsage(f'{attr} must a valid file path.')
        except ScannerError as ex:
            raise BadParameter(f'Invalid yaml provided: {str(ex)}')

    def __post_init__(self):
        """Run post initializing."""
        self.userdata, self.userdata_encoding = self._load_yaml_file(
            self.user_data, 'user_data'
        )

        if self.network_data is not None:
            (
                self.networkconfig,
                self.networkconfig_encoding,
            ) = self._load_yaml_file(self.network_data, 'network_data')


@dataclass_json
@dataclass
class VmCustomSpecIface:
    """Vm Custom Spec."""

    dhcp: Optional[bool] = False
    ip: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    gateway: Optional[List[IPv4Address]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    mask: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )

    def __post_init__(self):
        """Run post init."""
        if not self.dhcp:
            if self.ip:
                ip = IPv4Network(self.ip, False)
                self.ip = str(self.ip).partition('/')[0]
                self.mask = str(ip.netmask)
            else:
                raise ValidationError('Either set dhcp=true or ip and gateway')
        else:
            pass


@dataclass_json
@dataclass
class VmCustomSpec:
    """Vm Custom Sepc."""

    hostname: str
    domain: Domain
    interfaces: List[VmCustomSpecIface]
    dns: Optional[List[IP]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    time_zone: Optional[Union[str, int]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )

    def __post_init__(self):
        """Run post init."""
        self.hostname = self.hostname.lower()


@dataclass_json
@dataclass
class VmCliSpec:
    """Vm Cli spec."""

    built: str
    machine: VmMachine
    metadata: VmMeta
    networking: Optional[VmNetworking] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    iso: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    custom_spec: Optional[VmCustomSpec] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    cloud_init: Optional[VmCloudInit] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    extra_config: Optional[Union[List[str], List[Dict]]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    day_zero: Optional[VmDayZero] = field(
        default=None,
        metadata=dc_config(exclude=lambda x: x is None, field_name="day-zero"),
    )
    additional_parameters: Optional[Union[Path, Dict]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )

    @staticmethod
    def _process_extra_config(value: List[str]) -> List[Dict[str, str]]:
        """Process extra configuration."""
        from vss_cli.helper import to_tuples

        _options = to_tuples(','.join(value))
        return [{opt[0]: opt[1]} for opt in _options]

    @staticmethod
    def _process_json_file_or_type(value: Union[str, Path], attr: str):
        """Process json file or type."""
        val = None
        try:
            if value is not None:
                p = Path(value)
                with p.open(encoding="UTF-8") as source:
                    val = YAML().load(source.read())
                    return val
        except (FileNotFoundError, OSError) as ex:
            _LOGGING.debug(f'Not file: {ex}')
            val = None

        # any string will be loaded properly
        try:
            if value is not None:
                val = YAML().load(value)
                return val
        except ValueError as ex:
            _LOGGING.debug(f'Not string: {ex}')
            val = None

        if value and val is None:
            raise BadParameter(
                f'{attr} should be a file or JSON parameter input.'
            )

    def __post_init__(self):
        """Process and rewrite."""
        if self.extra_config is not None:
            self.extra_config = self._process_extra_config(self.extra_config)
        if self.additional_parameters:
            self.additional_parameters = self._process_json_file_or_type(
                self.additional_parameters, 'additional_parameters'
            )


@dataclass_json
@dataclass
class UserData:
    """User data."""

    userdata: str
    userdata_encoding: str
    networkconfig: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    networkconfig_encoding: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )


@dataclass_json
@dataclass
class VmApiSpec:
    """Vm api spec."""

    built_from: str

    usage: str
    client: str
    cpu: int
    description: str
    disks: List[VmDisk]
    firmware: str
    folder: str
    inform: List[str]
    memory_gb: int
    memoryGB: Optional[int]
    name: str
    networks: List[VmNetwork]
    os: str
    version: str
    storage_type: Optional[str] = field(
        default='hdd', metadata=dc_config(exclude=lambda x: x is None)
    )
    tpm: Optional[bool] = False
    vbs: Optional[bool] = False
    power_on: Optional[bool] = False
    template: Optional[bool] = False
    built: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    domain: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    iso: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    scsi: Optional[List[VmScsi]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    vss_options: Optional[List[str]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    vss_service: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    custom_spec: Optional[VmCustomSpec] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    extra_config: Optional[List[Dict[str, Any]]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    user_data: Optional[UserData] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    admin_email: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    admin_name: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    admin_phone: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    notes: Optional[List[Dict]] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    source: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    source_template: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    source_snap_id: Optional[int] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    day_zero: Optional[VmDayZero] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    item_id: Optional[str] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )
    additional_parameters: Optional[Dict] = field(
        default=None, metadata=dc_config(exclude=lambda x: x is None)
    )

    @classmethod
    def from_cli_spec(cls, cli_spec: VmCliSpec, session=None):
        """Create from cli spec."""
        data = dict(built_from=cli_spec.built)
        name = cli_spec.machine.name
        # machine
        if cli_spec.built in ['clib', 'clone', 'image', 'template']:
            if cli_spec.built in ['clib']:
                item_id = session.get_clib_deployable_item_by_name_or_id_path(
                    cli_spec.machine.item
                )[0]['id']
                data['item_id'] = item_id
                data['built_from'] = 'contentlib'
            if cli_spec.built in ['clone', 'template']:
                source_id = session.get_vm_by_id_or_name(
                    cli_spec.machine.source
                )[0]['moref']
                data['source'] = source_id
                source_spec = session.get_vm_spec(source_id)
                del source_spec['built_from']
                if source_spec['extra_config']:
                    del source_spec['extra_config']
                data.update(source_spec)
                name = f"{source_spec['name']}-f{cli_spec.built}"
                if cli_spec.machine.firmware != source_spec['firmware']:
                    _LOGGING.warning(
                        f'{cli_spec.machine.firmware} differs from source.'
                        f'Overriding with {source_spec["firmware"]} to avoid '
                        f'issues...'
                    )
                    cli_spec.machine.firmware = source_spec['firmware']
                if cli_spec.built in ['template']:
                    data['source_template'] = source_id
                if (
                    cli_spec.built in ['clone']
                    and cli_spec.machine.source_snapshot
                ):
                    data[
                        'source_snap_id'
                    ] = session.get_vm_snapshot_by_id_name_or_desc(
                        source_id, cli_spec.machine.source_snapshot
                    )[
                        0
                    ][
                        'id'
                    ]
        if cli_spec.built in ['os_install']:
            data['iso'] = session.get_iso_by_name_or_path(
                cli_spec.machine.iso
            )[0]['path']
            data['built'] = cli_spec.built
        if cli_spec.machine.folder:
            data['folder'] = session.get_folder_by_name_or_moref_path(
                cli_spec.machine.folder
            )[0]['moref']
        if cli_spec.machine.domain:
            data['domain'] = session.get_domain_by_name_or_moref(
                cli_spec.machine.domain
            )[0]['moref']
        if cli_spec.networking:
            networks = []
            for iface in cli_spec.networking.interfaces:
                net_id = session.get_network_by_name_or_moref(
                    iface.network_id or iface.network
                )[0]['moref']
                networks.append({'network': net_id, 'type': iface.type})
            data['networks'] = networks
        if cli_spec.machine.disks:
            data['disks'] = [disk.to_dict() for disk in cli_spec.machine.disks]
        if cli_spec.machine.scsi:
            data['scsi'] = [scsi.to_dict() for scsi in cli_spec.machine.scsi]
        if cli_spec.custom_spec:
            data['custom_spec'] = cli_spec.custom_spec
        if cli_spec.machine.memory:
            # TODO: move from camel case `memoryGB` to `memory_gb`.
            #       change must be performed in pyvss first.
            data['memoryGB'] = cli_spec.machine.memory
            data['memory_gb'] = cli_spec.machine.memory
        data['name'] = cli_spec.machine.name or name
        if cli_spec.machine.cpu:
            data['cpu'] = cli_spec.machine.cpu
        if cli_spec.machine.firmware:
            data['firmware'] = session.get_vm_firmware_by_type_or_desc(
                cli_spec.machine.firmware
            )[0]['type']
        if cli_spec.machine.os:
            data['os'] = session.get_os_by_name_or_guest(cli_spec.machine.os)[
                0
            ]['guest_id']
        if cli_spec.machine.version:
            data['version'] = cli_spec.machine.version
        if cli_spec.machine.storage_type:
            data['storage_type'] = session.get_vm_storage_type_by_type_or_desc(
                cli_spec.machine.storage_type
            )[0]['type']
        if cli_spec.machine.tpm:
            data['tpm'] = cli_spec.machine.tpm
        if cli_spec.machine.vbs:
            data['vbs'] = cli_spec.machine.vbs
        if cli_spec.machine.power_on:
            data['power_on'] = cli_spec.machine.power_on
        if cli_spec.machine.template:
            data['template'] = cli_spec.machine.template
        # metadata
        if cli_spec.metadata.usage:
            data['usage'] = cli_spec.metadata.usage
        if cli_spec.metadata.client:
            data['client'] = cli_spec.metadata.client
        data['description'] = cli_spec.metadata.description
        if cli_spec.metadata.admin:
            if cli_spec.metadata.admin.name:
                data['admin_name'] = cli_spec.metadata.admin.name
            if cli_spec.metadata.admin.email:
                data['admin_email'] = validate_email(
                    None, 'admin_email', cli_spec.metadata.admin.email
                )
            if cli_spec.metadata.admin.phone:
                data['admin_phone'] = cli_spec.metadata.admin.phone
        if cli_spec.metadata.inform:
            data['inform'] = [
                validate_email(None, 'inform', i)
                for i in cli_spec.metadata.inform
            ]
        if cli_spec.metadata.vss_service:
            data['vss_service'] = session.get_vss_service_by_name_label_or_id(
                cli_spec.metadata.vss_service
            )[0]['id']
        if cli_spec.metadata.vss_options:
            data['vss_options'] = cli_spec.metadata.vss_options
        if cli_spec.cloud_init:
            data['user_data'] = cli_spec.cloud_init.to_dict()
        if cli_spec.day_zero:
            data['day_zero'] = cli_spec.day_zero.to_dict()
        if cli_spec.extra_config:
            _LOGGING.debug(
                f'{cli_spec.extra_config=}={type(cli_spec.extra_config)}'
            )
            data['extra_config'] = cli_spec.extra_config
        if cli_spec.metadata.notes:
            data['notes'] = cli_spec.metadata.notes
        if cli_spec.additional_parameters:
            data['additional_parameters'] = cli_spec.additional_parameters
        return cls.from_dict(data)
