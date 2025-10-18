"""Configuration for VSS CLI (vss-cli)."""
import functools
import json
import logging
import os
import platform
import sys
import time
import warnings
from base64 import b64decode, b64encode
from pathlib import Path
from time import sleep
from typing import (  # noqa: F401
    Any, Callable, Dict, List, Optional, Tuple, Union, cast)

import click
import jwt
import requests
from click_spinner import Spinner, spinner
from pick import pick
from pyvss.const import __version__ as pyvss_version
from pyvss.enums import RequestStatus
from pyvss.exceptions import VssError
from pyvss.manager import VssManager
from ruamel.yaml import YAML

import vss_cli.const as const
import vss_cli.yaml as yaml
from vss_cli.data_types import ConfigEndpoint, ConfigFile, ConfigFileGeneral
from vss_cli.exceptions import VssCliError
from vss_cli.helper import (
    bytes_to_str, debug_requests_on, format_output, get_hostname_from_url)
from vss_cli.utils.emoji import EMOJI_UNICODE
from vss_cli.utils.threading import WorkerQueue
from vss_cli.validators import (
    validate_email, validate_json_file_or_type, validate_phone_number,
    validate_uuid, validate_vm_moref)

_LOGGING = logging.getLogger(__name__)


class Configuration(VssManager):
    """The configuration context for the VSS CLI."""

    def __init__(self, tk: str = '') -> None:
        """Initialize the configuration."""
        super().__init__(tk)
        self.user_agent = self._default_user_agent(
            extensions=f'pyvss/{pyvss_version}'
        )
        self.verbose = False  # type: bool
        self.default_endpoint_name = None  # type: Optional[str]
        # start of endpoint settings
        self._endpoint = const.DEFAULT_ENDPOINT  # type: str
        self.base_endpoint = self.endpoint  # type: str
        self.endpoint_name = const.DEFAULT_ENDPOINT_NAME
        # end of endpoint settings
        self.history = const.DEFAULT_HISTORY  # type: str
        self.s3_server = None  # type: Optional[str]
        self._s3_server = const.DEFAULT_S3_SERVER  # type: str
        self.vpn_server = None  # type: Optional[str]
        self._vpn_server = const.DEFAULT_VPN_SERVER
        self.gpt_token = None  # type: Optional[str]
        self._gpt_token = const.DEFAULT_GPT_TOKEN
        self.gpt_server = None  # type: Optional[str]
        self._gpt_server = const.DEFAULT_GPT_SERVER
        self.gpt_persona = None  # type: Optional[int]
        self._gpt_persona = const.DEFAULT_GPT_PERSONA
        self.username = None  # type: Optional[str]
        self.password = None  # type: Optional[str]
        self.totp = None  # type: Optional[str]
        self.token = None  # type: Optional[str]
        self.timeout = None  # type: Optional[int]
        self._debug = False  # type: Optional[bool]
        self.showexceptions = False  # type: bool
        self.columns = None  # type: Optional[List[Tuple[str, str]]]
        self.columns_width = None  # type: Optional[int]
        self.no_headers = False  # type: Optional[bool]
        self.table_format = None  # type: Optional[str]
        self.sort_by = None  # type: Optional[str]
        self.output = None  # type: Optional[str]
        self.config_path = None  # type: Optional[str]
        self.check_for_updates = None  # type: Optional[bool]
        self.check_for_messages = None  # type: Optional[bool]
        self.wait_for_requests = None  # type: Optional[bool]
        self.config_file = None  # type: Optional[ConfigFile]
        self.spinner = spinner
        self.wait = None  # type: Optional[bool]
        self.moref = None  # type: Optional[str]
        self.unit = None  # type: Optional[str, int]
        self.payload_options = {}  # type: Optional[Dict]
        self.tmp = None  # type: Optional[Any]
        self.root_path = None  # type: Optional[bool]

    def set_dry_run(self, val: bool) -> None:
        """Set dry_run value."""
        if val is True:
            if self.output not in ['json', 'yaml']:
                self.output = 'json'
            self.wait = not bool(val)
            self.dry_run = bool(val)

    @property
    def debug(self) -> bool:
        """Return debug status."""
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        """Set on debug_requests if True."""
        if value:
            debug_requests_on()
        self._debug = value

    @property
    def endpoint(self) -> str:
        """Return endpoint value."""
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value: str) -> None:
        """Rebuild API endpoints."""
        self._endpoint = value
        self.base_endpoint = value
        self.api_endpoint = f'{value}/v2'
        self.token_endpoint = f'{value}/auth/request-token'
        self.tf_endpoint = f'{value}/tf'
        if value:
            self.endpoint_name = get_hostname_from_url(
                value, const.DEFAULT_HOST_REGEX
            )

    def set_defaults(self) -> None:
        """Set default configuration settings."""
        _LOGGING.debug('Setting default configuration.')
        for setting, default in const.DEFAULT_SETTINGS.items():
            if getattr(self, setting) is None:
                setattr(self, setting, default)
        _LOGGING.debug(self)

    def get_token(
        self,
        user: Optional[str] = '',
        password: Optional[str] = '',
        otp: Optional[str] = None,
    ) -> str:
        """Generate token and returns value."""
        self.api_token = super().get_token(user, password, otp)
        _LOGGING.debug(f'Token generated successfully: {self.api_token}')
        return self.api_token

    def update_endpoints(self, endpoint: str = '') -> None:
        """Rebuild API endpoints."""
        self.base_endpoint = endpoint
        self.api_endpoint = f'{endpoint}/v2'
        self.token_endpoint = f'{endpoint}/auth/request-token'
        self.tf_endpoint = f'{endpoint}/tf'

    def echo(self, msg: str, *args: Optional[Any]) -> None:
        """Put content message to stdout."""
        self.log(msg, *args)

    def log(  # pylint: disable=no-self-use
        self, msg: str, *args: Optional[str]
    ) -> None:  # pylint: disable=no-self-use
        """Log a message to stdout."""
        if args:
            msg %= args
        click.echo(msg, file=sys.stdout)

    def secho(self, msg: str, *args: Optional[Any], **kwargs) -> None:
        """Put content message to stdout with style."""
        self.slog(msg, *args, **kwargs)

    def slog(  # pylint: disable=no-self-use
        self, msg: str, *args: Optional[str], **kwargs
    ) -> None:  # pylint: disable=no-self-use
        """Log a message to stdout with style."""
        file = sys.stdout
        if args:
            msg %= args
        if 'file' in kwargs:
            file = kwargs['file']
            del kwargs['file']
        click.secho(msg, file=file, **kwargs)

    def vlog(self, msg: str, *args: Optional[str]) -> None:
        """Log a message only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)

    def __repr__(self) -> str:
        """Return the representation of the Configuration."""
        view = {
            "endpoint": self.endpoint,
            "default_endpoint_name": self.default_endpoint_name,
            "endpoint_name": self.endpoint_name,
            "access_token": 'yes' if self.token is not None else 'no',
            "user": 'yes' if self.username is not None else 'no',
            "user_password": 'yes' if self.password is not None else 'no',
            "tf_enabled": 'yes' if self.tf_enabled is not None else 'no',
            "output": self.output,
            "timeout": self.timeout,
            "debug": self.debug,
            "verbose": self.verbose,
            "wait": self.wait,
            "dry_run": self.dry_run,
            "s3_server": self.s3_server,
            "vpn_server": self.vpn_server,
            "gpt_server": self.gpt_server,
            "gpt_persona": self.gpt_persona,
            "gpt_token": 'yes' if self.gpt_token is not None else 'no',
        }

        return f"<Configuration({view})"

    def auto_output(self, auto_output: str) -> str:
        """Configure output format."""
        if self.output == "auto":
            if auto_output == 'data':
                auto_output = const.DEFAULT_RAW_OUTPUT
            _LOGGING.debug(f"Setting auto-output to: {auto_output}")
            self.output = auto_output
        return self.output

    @staticmethod
    def _default_user_agent(
        name: str = const.PACKAGE_NAME,
        version: str = const.__version__,
        extensions: str = '',
    ) -> str:
        """Set default user agent."""
        # User-Agent:
        # <product>/<version> (<system-information>)
        # <platform> (<platform-details>) <extensions>
        user_agent = (
            f'{name}/{version} '
            f'({platform.system()}/{platform.release()}) '
            f'Python/{platform.python_version()} '
            f'({platform.platform()}) {extensions}'
        )
        return user_agent

    def set_credentials(
        self,
        username: str,
        password: str,
        token: str,
        endpoint: str,
        name: str,
    ) -> None:
        """Set credentials.

        Username, password, Token, endpoint name.
        Useful for configuration purposes.
        """
        self.username = username
        self.password = password
        self.api_token = token
        self.token = token
        self.endpoint = endpoint
        self.endpoint_name = name
        return

    def load_profile(
        self, endpoint: str = None
    ) -> Tuple[Optional[ConfigEndpoint], Optional[str], Optional[str]]:
        """Load profile from configuration file.

        Uses new credential backend system with fallback to legacy base64 auth.
        """
        username, password = None, None
        # load from
        config_endpoint = self.config_file.get_endpoint(endpoint)
        if config_endpoint:
            endpoint_name = config_endpoint[0].name

            # Try loading from new credential backend first
            try:
                from vss_cli.credentials.base import (
                    CredentialType, detect_backend)

                backend = detect_backend()

                if backend.is_available():
                    # Try to retrieve credentials from backend
                    username_value = backend.retrieve_credential(
                        endpoint_name, CredentialType.USERNAME
                    )
                    password_value = backend.retrieve_credential(
                        endpoint_name, CredentialType.PASSWORD
                    )

                    if username_value and password_value:
                        _LOGGING.debug(
                            f'Loaded credentials from backend: '
                            f'{backend.__class__.__name__}'
                        )
                        username = username_value.encode()
                        password = password_value.encode()
                        return (
                            config_endpoint[0],
                            bytes_to_str(username),
                            bytes_to_str(password),
                        )
                    else:
                        _LOGGING.debug(
                            f'No credentials found in '
                            f'backend for: {endpoint_name}'
                        )
            except Exception as e:
                _LOGGING.debug(
                    f'Could not load ' f'credentials from backend: {e}'
                )

            # Fallback to legacy base64 auth
            auth = config_endpoint[0].auth
            token = config_endpoint[0].token

            if auth and token:
                try:
                    auth_enc = auth.encode()
                    credentials_decoded = b64decode(auth_enc)
                    # get user/pass
                    username, password = credentials_decoded.split(b':')
                    _LOGGING.debug(
                        f'Loaded credentials from '
                        f'legacy base64 auth for: '
                        f'{endpoint_name}'
                    )
                except Exception as e:
                    _LOGGING.warning(f'Error decoding legacy credentials: {e}')
            elif not (username and password):
                _LOGGING.warning('Invalid configuration endpoint found.')

            return (
                config_endpoint[0],
                bytes_to_str(username),
                bytes_to_str(password),
            )
        else:
            return None, bytes_to_str(username), bytes_to_str(password)

    def load_config_file(
        self, config: Union[Path, str] = None
    ) -> Optional[ConfigFile]:
        """Load raw configuration file and return ConfigFile object."""
        raw_config = self.load_raw_config_file(config=config)
        self.config_file = ConfigFile.from_json(raw_config)
        return self.config_file

    def load_raw_config_file(
        self, config: Optional[Union[Path, str]] = None
    ) -> Optional[str]:
        """Load raw configuration file from path."""
        config_file = config or self.config_path
        try:
            if isinstance(config_file, str):
                config_file = Path(config_file)
            cfg_dict = self.yaml_load(config_file)
            return json.dumps(cfg_dict)
        except ValueError as ex:
            _LOGGING.error(f'Error loading configuration file: {ex}')
            raise VssCliError(
                'Invalid configuration file.'
                'Run "vss-cli configure mk" or '
                '"vss-cli configure upgrade" to upgrade '
                'legacy configuration.'
            )

    def load_config(
        self, validate: bool = True, spinner_cls: Optional[Spinner] = None
    ) -> Optional[Tuple[str, str, str]]:
        """Load configuration and validate.

        Load configuration either from previously set
        ``username`` and ``password`` or ``token``.
        """
        try:
            # input configuration check
            if self.token or (self.username and self.password):
                # setting defaults if required
                self.set_defaults()
                _LOGGING.debug('Loading from input')
                # don't load config_path file
                if self.token:
                    _LOGGING.debug('Checking token')
                    # set api token
                    self.api_token = self.token
                    return self.username, self.password, self.api_token
                elif self.username and self.password:
                    _LOGGING.debug('Checking user/pass to generate token')
                    # generate a new token - won't save
                    _LOGGING.warning(
                        'A new token will be generated but not persisted. '
                        'Consider running command "configure mk" to save your '
                        'credentials.'
                    )
                    self.get_token(self.username, self.password, self.totp)
                    return self.username, self.password, self.api_token
                else:
                    raise VssCliError(
                        'Environment variables error. Please, verify '
                        'VSS_TOKEN or VSS_USER and VSS_USER_PASS'
                    )
            else:
                cfg_path = Path(self.config_path)
                _LOGGING.debug(
                    f'Loading configuration file: {self.config_path}'
                )
                if cfg_path.is_file():
                    # load the configuration file from json string into class
                    self.config_file = self.load_config_file(config=cfg_path)
                    # general area
                    if self.config_file.general:
                        _LOGGING.debug(
                            f'Loading general settings from {self.config_path}'
                        )
                        # enforce new gpt server
                        if (
                            self.config_file.general.gpt_server
                            != self._gpt_server
                        ):
                            # add a deprecation warning for
                            # config_file.general.gpt_server
                            _LOGGING.warning(
                                f'Found legacy gpt_server. '
                                f'Updating to: {self._gpt_server}.'
                            )
                            _LOGGING.warning(
                                f'Run '
                                f'"vss-cli configure set '
                                f'gpt_server {self._gpt_server}" '
                                f'to fix this warning.'
                            )
                            self.config_file.general.gpt_server = (
                                self._gpt_server
                            )
                        # set config_path defaults
                        for setting in const.GENERAL_SETTINGS:
                            try:
                                # check if a setting hasn't been set
                                # by input or env
                                # which overrides a configuration file
                                setting_val = getattr(self, setting)
                                if setting_val is None:
                                    setattr(
                                        self,
                                        setting,
                                        getattr(
                                            self.config_file.general, setting
                                        ),
                                    )
                                else:
                                    _LOGGING.debug(
                                        f'Prioritizing {setting} from '
                                        f'command line input.'
                                    )
                            except KeyError as ex:
                                _LOGGING.warning(
                                    f'Could not load general setting'
                                    f' {setting}: {ex}'
                                )
                        # printing out
                        _LOGGING.debug(f"General settings loaded: {self}")

                    # load preferred endpoint from file if any
                    if self.config_file.endpoints:
                        _LOGGING.debug(
                            f'Loading endpoint settings from '
                            f'{self.config_path}'
                        )
                        _LOGGING.debug(
                            f'Looking for endpoint={self.endpoint},'
                            f' default_endpoint_name='
                            f'{self.default_endpoint_name}'
                        )
                        # 1. provided by input
                        if self.endpoint:
                            msg = (
                                f'Cloud not find endpoint provided by '
                                f'input {self.endpoint}. \n'
                            )
                            # load endpoint from endpoints
                            ep, usr, pwd = self.load_profile(self.endpoint)
                        # 2. provided by configuration file
                        #    (default_endpoint_name)
                        elif self.default_endpoint_name:
                            msg = (
                                f'Could not find default endpoint '
                                f'{self.default_endpoint_name}. \n'
                            )
                            # load endpoint from endpoints
                            ep, usr, pwd = self.load_profile(
                                self.default_endpoint_name
                            )
                        # 3. fallback to default settings
                        else:
                            msg = (
                                f"Invalid endpoint {self.endpoint_name} "
                                f"configuration. \n"
                            )
                            ep, usr, pwd = self.load_profile(
                                self.endpoint_name
                            )
                        # check valid creds
                        if not (usr and pwd or getattr(ep, 'token', None)):
                            _LOGGING.warning(msg)
                            default_endpoint = const.DEFAULT_ENDPOINT_NAME
                            _LOGGING.warning(
                                f'Falling back to {default_endpoint}'
                            )
                            (
                                ep,
                                usr,
                                pwd,
                            ) = self.load_profile(  # NOQA: E501
                                endpoint=const.DEFAULT_ENDPOINT_NAME
                            )
                        # set config_path data
                        self.set_credentials(
                            usr,
                            pwd,
                            ep.token,
                            ep.url,
                            ep.name,
                        )
                        if validate:
                            # last check cred
                            creds = self.username and self.password
                            if not (creds or self.api_token):
                                raise VssCliError(
                                    'Run "vss-cli configure mk" to add '
                                    'endpoint to configuration file or '
                                    '"vss-cli configure upgrade" to upgrade '
                                    'legacy configuration.'
                                )
                            _LOGGING.debug(
                                f'Loaded from file: {self.endpoint_name}: '
                                f'{self.endpoint}:'
                                f': {self.username}'
                            )
                            try:
                                self.whoami()
                                _LOGGING.debug('Token validated successfully.')
                            except Exception as ex:
                                self.vlog(str(ex))
                                _LOGGING.debug('Generating a new token')
                                self.api_token = self._get_token_with_mfa(
                                    spinner_cls=spinner_cls
                                )
                                endpoint = self._create_endpoint_config(
                                    token=self.api_token
                                )
                                self.write_config_file(new_endpoint=endpoint)
                                # check for motd
                                self.check_motd()
                                # check for updates
                                if self.check_for_updates:
                                    self.check_available_updates()
                                # check for unread messages
                                if self.check_for_messages:
                                    self.check_unread_messages()
                        return self.username, self.password, self.api_token
                else:
                    self.set_defaults()
            raise VssCliError(
                'Invalid configuration. Please, run '
                '"vss-cli configure mk" to initialize configuration, or '
                '"vss-cli configure upgrade" to upgrade legacy '
                'configuration.'
            )
        except Exception as ex:
            raise VssCliError(str(ex))

    def check_motd(self) -> None:
        """Check available motd."""
        try:
            data = self.get_session_motd()
            if data and data.get("motd"):
                em = EMOJI_UNICODE.get(":loudspeaker:")
                self.secho(
                    f'\n{em}'
                    f' Message of the day: {data.get("motd")} '
                    f'{em}.\n',
                    file=sys.stderr,
                    fg='red',
                    nl=True,
                    blink=True,
                )
        except Exception as ex:
            _LOGGING.error(f'Could not check for MOTD: {ex}')

    def check_available_updates(self) -> None:
        """Check available update from PyPI."""
        try:
            _LOGGING.debug('Checking for available updates.')
            cmd_bin = sys.executable
            # create command with the right exec
            pip_cmd = f'{cmd_bin} -m pip list --outdated'.split(None)
            from subprocess import PIPE, Popen

            p = Popen(pip_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            out_decoded = out.decode('utf-8')
            # verify if package name is in outdated string
            pkg_name = const.PACKAGE_NAME.replace('_', '-')
            if pkg_name in out_decoded:
                lines = out_decoded.split('\n')
                pkg_line = [line for line in lines if pkg_name in line]
                if pkg_line:
                    pkg_line = pkg_line.pop()
                    pkg, current, latest, pkgn = pkg_line.split(None)
                    self.secho(
                        f'Update available {current} -> {latest} '
                        f'{EMOJI_UNICODE.get(":upwards_button:")}.',
                        file=sys.stderr,
                        fg='green',
                        nl=False,
                    )
                    self.secho(' Run ', file=sys.stderr, fg='green', nl=False)
                    self.secho(
                        'vss-cli upgrade', file=sys.stderr, fg='red', nl=False
                    )
                    self.secho(
                        ' to install latest. \n', file=sys.stderr, fg='green'
                    )
            else:
                self.secho(
                    f'Running latest version {const.__version__} '
                    f'{EMOJI_UNICODE.get(":white_heavy_check_mark:")}\n',
                    file=sys.stderr,
                    fg='green',
                )
        except Exception as ex:
            _LOGGING.error(f'Could not check for updates: {ex}')

    def check_unread_messages(self) -> None:
        """Check unread API messages."""
        try:
            _LOGGING.debug('Checking for unread messages')
            messages = self.get_user_messages(
                filter='status,eq,Created', per_page=100
            )
            n_messages = len(messages)
            if messages:
                self.secho(
                    f'You have {n_messages} unread messages '
                    f'{EMOJI_UNICODE.get(":envelope_with_arrow:")} ',
                    file=sys.stderr,
                    fg='green',
                    nl=False,
                )
                self.secho('Run ', file=sys.stderr, fg='green', nl=False)
                self.secho(
                    'vss-cli message ls -f status=Created',
                    file=sys.stderr,
                    fg='red',
                    nl=False,
                )
                self.secho(
                    ' to list unread messages.', file=sys.stderr, fg='green'
                )
            else:
                _LOGGING.debug('No messages with Created status')
        except Exception as ex:
            _LOGGING.error(f'Could not check for messages: {ex}')

    def _get_token_with_mfa(
        self,
        token: Optional[str] = None,
        spinner_cls: Optional[Spinner] = None,
    ):
        """Get token with MFA."""
        try:
            token = token or self.get_token(
                self.username, self.password, self.totp
            )
        except VssError as ex:
            if 500 > ex.http_code > 399:
                if 'InvalidParameterValue: otp' in ex.message:
                    # try MFA Auth
                    try:
                        _LOGGING.debug(
                            'Requesting a new timed one-time password'
                        )
                        _ = self.request_totp(self.username, self.password)
                    except Exception as exc:
                        _LOGGING.warning(f'Requesting totp: {exc}')
                        pass
                    if spinner_cls is not None:
                        spinner_cls.stop()
                    self.totp = click.prompt(
                        'MFA enabled. Provide Timed One-Time Password'
                    )
                    if spinner_cls is not None:
                        spinner_cls.start()
                    try:
                        token = token or self.get_token(
                            self.username, self.password, self.totp
                        )
                    except Exception as exc:
                        _LOGGING.warning(
                            f'Could not generate new token: {exc}'
                        )
                        raise exc
                elif 'TotpEnforcement: Must enable TOTP' in ex.message:
                    if spinner_cls is not None:
                        spinner_cls.stop()
                    _LOGGING.error(ex)
                    self.echo('')
                    self.secho('Run ', file=sys.stderr, fg='green', nl=False)
                    self.secho(
                        'vss-cli account --no-load set mfa mk '
                        '{EMAIL|AUTHENTICATOR|SMS}',
                        file=sys.stderr,
                        fg='red',
                        nl=False,
                    )
                    self.secho(' to enable MFA.', file=sys.stderr, fg='green')
                    if spinner_cls is not None:
                        spinner_cls.start()
                    sys.exit(1)
                else:
                    raise ex
            else:
                raise ex
        return token

    def _create_endpoint_config(self, token: str = None) -> ConfigEndpoint:
        """Create endpoint configuration for a given token.

        Token might be ``None`` and will generate a new one
        using ``username`` and ``password``.

        Also stores credentials in secure backend if available.
        """
        token = self._get_token_with_mfa(token=token)
        # encode or save
        username = (
            self.username
            if isinstance(self.username, bytes)
            else self.username.encode()
        )
        password = (
            self.password
            if isinstance(self.password, bytes)
            else self.password.encode()
        )
        credentials = b':'.join([username, password])
        auth = b64encode(credentials).strip().decode('utf-8')
        # decode jwt to verify if otp is enabled.
        payload = jwt.decode(
            self.api_token, options=dict(verify_signature=False)
        )

        # Try to store credentials in secure backend
        try:
            from vss_cli.credentials.base import (
                CredentialData, CredentialType, detect_backend)

            backend = detect_backend()

            if backend.is_available():
                # Store username
                username_cred = CredentialData(
                    credential_type=CredentialType.USERNAME,
                    value=bytes_to_str(username),
                    endpoint=self.endpoint_name,
                )
                backend.store_credential(username_cred)

                # Store password
                password_cred = CredentialData(
                    credential_type=CredentialType.PASSWORD,
                    value=bytes_to_str(password),
                    endpoint=self.endpoint_name,
                )
                backend.store_credential(password_cred)

                # Store token
                token_cred = CredentialData(
                    credential_type=CredentialType.TOKEN,
                    value=self.api_token,
                    endpoint=self.endpoint_name,
                )
                backend.store_credential(token_cred)

                _LOGGING.info(
                    f'Stored credentials in backend: '
                    f'{backend.__class__.__name__}'
                )

                # Don't include auth in config if stored in backend
                endpoint_cfg = {
                    'url': self.base_endpoint,
                    'name': self.endpoint_name,
                    'token': self.api_token,
                    'tf_enabled': payload.get('otp', False),
                }
            else:
                # Fallback to legacy auth storage
                endpoint_cfg = {
                    'url': self.base_endpoint,
                    'name': self.endpoint_name,
                    'auth': auth,
                    'token': self.api_token,
                    'tf_enabled': payload.get('otp', False),
                }
        except Exception as e:
            _LOGGING.warning(
                f'Could not store credentials in backend: {e}. '
                f'Using legacy auth storage.'
            )
            # Fallback to legacy auth storage
            endpoint_cfg = {
                'url': self.base_endpoint,
                'name': self.endpoint_name,
                'auth': auth,
                'token': self.api_token,
                'tf_enabled': payload.get('otp', False),
            }

        ep_cfg = ConfigEndpoint.from_json(json.dumps(endpoint_cfg))
        _LOGGING.debug(f'Configuration endpoint created: {ep_cfg}')
        return ep_cfg

    def load_config_template(self) -> ConfigFile:
        """Load configuration from template."""
        # load template in case it fails
        cfg_default_path = Path(const.DEFAULT_CONFIG_TMPL)
        with cfg_default_path.open() as f:
            config_tmpl = yaml.load_yaml(self.yaml(), f)
            raw_config_tmpl = json.dumps(config_tmpl)
            config_file_tmpl = ConfigFile.from_json(raw_config_tmpl)
        return config_file_tmpl

    def write_config_file(
        self,
        new_config_file: Optional[ConfigFile] = None,
        new_endpoint: Optional[ConfigEndpoint] = None,
        config_general: Optional[ConfigFileGeneral] = None,
    ) -> bool:
        """Create or update configuration endpoint section."""
        # load template in case it fails
        config_file_tmpl = self.load_config_template()
        try:
            _LOGGING.debug(f'Writing configuration file: {self.config_path}')
            cfg_path = Path(self.config_path)
            # validate if file exists
            if cfg_path.is_file():
                with cfg_path.open(mode='r+') as fp:
                    try:
                        _conf_dict = yaml.load_yaml(self.yaml(), fp)
                        raw_config = json.dumps(_conf_dict)
                        config_file = ConfigFile.from_json(raw_config)
                    except (ValueError, TypeError) as ex:
                        _LOGGING.warning(f'Invalid config_path file: {ex}')
                        if click.confirm(
                            'An error occurred loading the '
                            'configuration file. '
                            'Would you like to recreate it?',
                            err=True,
                        ):
                            config_file = config_file_tmpl
                        else:
                            return False
                    if new_config_file:
                        config_file.general = new_config_file.general
                        config_file.update_endpoints(
                            *new_config_file.endpoints
                        )
                    # update general config_path if required
                    if config_general:
                        config_file.general = config_general
                    # update endpoint if required
                    if new_endpoint:
                        # update endpoint
                        config_file.update_endpoint(new_endpoint)
                    # dumping and loading
                    _conf_dict = json.loads(config_file.to_json())
                    fp.seek(0)
                    yaml.dump_yaml(self.yaml(), _conf_dict, stream=fp)
                    fp.truncate()
                _LOGGING.debug(
                    f'Configuration file {self.config_path} has been updated'
                )
            else:
                if new_config_file:
                    f_type = 'Config file'
                    config_file_dict = json.loads(new_config_file.to_json())
                else:
                    # New configuration file. A new endpoint must be configured
                    f_type = 'Default template'
                    config_endpoint = (
                        new_endpoint or self._create_endpoint_config()
                    )
                    config_file_tmpl.update_endpoint(config_endpoint)
                    # load and dump
                    config_file_dict = json.loads(config_file_tmpl.to_json())
                # write file
                with cfg_path.open(mode='w') as fp:
                    yaml.dump_yaml(self.yaml(), config_file_dict, stream=fp)
                _LOGGING.debug(
                    f'New {f_type} has been written to {self.config_path}.'
                )
        except OSError as e:
            raise Exception(
                f'An error occurred writing ' f'configuration file: {e}'
            )
        return True

    def configure(
        self,
        username: str,
        password: str,
        endpoint: str,
        replace: Optional[bool] = False,
        endpoint_name: Optional[str] = None,
    ) -> bool:
        """Configure endpoint with provided settings."""
        self.username = username
        self.password = password
        # update instance endpoints if provided
        self.endpoint = endpoint
        if endpoint_name:
            self.endpoint_name = endpoint_name
        # directory available
        cfg_path = Path(self.config_path)
        if not cfg_path.parent.is_dir():
            cfg_path.parent.mkdir()
        # config_path file
        if cfg_path.is_file():
            try:
                self.config_file = self.load_config_file()
                # load credentials by endpoint_name
                (
                    config_endpoint,
                    e_username,
                    e_password,
                ) = self.load_profile(  # NOQA: E501c
                    endpoint=self.endpoint_name
                )
                # profile does not exist
                if not (e_username and e_password and config_endpoint.token):
                    self.echo(
                        f'Endpoint {self.endpoint_name} not found. '
                        f'Creating...'
                    )
                    endpoint_cfg = self._create_endpoint_config()
                    self.write_config_file(new_endpoint=endpoint_cfg)
                # profile exists
                elif e_username and e_password and config_endpoint.token:
                    username = bytes_to_str(e_username) if e_username else ''
                    confirm = replace or click.confirm(
                        f"Would you like to replace existing configuration?\n "
                        f"{self.endpoint_name}:"
                        f"{username}: {config_endpoint.url}",
                        err=True,
                    )
                    if confirm:
                        endpoint_cfg = self._create_endpoint_config()
                        self.write_config_file(new_endpoint=endpoint_cfg)
                    else:
                        return False
            except Exception as ex:
                _LOGGING.warning(f'Invalid config_path file: {ex}')
                confirm = click.confirm(
                    'An error occurred loading the '
                    'configuration file. '
                    'Would you like to recreate it?',
                    err=True,
                )
                if confirm:
                    endpoint_cfg = self._create_endpoint_config()
                    return self.write_config_file(new_endpoint=endpoint_cfg)
                else:
                    return False
            # feedback
            self.echo(
                f'Successfully configured credentials for ' f'{self.endpoint}.'
            )
        else:
            endpoint_cfg = self._create_endpoint_config()
            self.write_config_file(new_endpoint=endpoint_cfg)
        return True

    @staticmethod
    def _filter_objects_by_attrs(
        value: str, objects: List[dict], attrs: List[Tuple[Any, Any]]
    ) -> List[Any]:
        """Filter objects by a given `value` based on attributes.

        Attributes may be a list of tuples with attribute name, type.

        :param value: value to filter
        :param objects: list of dictionaries
        :param attrs: list of tuple of attribute name, type
        :return:
        """
        _objs = []
        for attr in attrs:
            attr_name = attr[0]
            attr_type = attr[1]
            try:
                if attr_type in [str]:
                    if attr_name in ['moref', 'uuid']:
                        f = filter(
                            lambda i: attr_type(value).lower()
                            == i[attr_name].lower(),
                            objects,
                        )
                    else:
                        f = filter(
                            lambda i: attr_type(value).lower()
                            in i[attr_name].lower(),
                            objects,
                        )
                elif attr_type in [int]:
                    f = filter(
                        lambda i: attr_type(value) == i[attr_name], objects
                    )
                else:
                    f = filter(
                        lambda i: attr_type(value) in i[attr_name], objects
                    )
                # cast list
                _objs = list(f)
            except ValueError as ex:
                _LOGGING.debug(f'{value} ({type(value)}) error: {ex}')

            if _objs:
                break
        return _objs

    @staticmethod
    def pick(objects: List[Dict], options=None, indicator='=>'):
        """Show a ``picker`` for a list of dicts."""
        count = len(objects)
        msg = f"Found {count} matches. Please select one:"
        sel, index = pick(
            title=msg, indicator=indicator, options=options or objects
        )
        return [objects[index]]

    def get_vskey_stor(self, **kwargs) -> bool:
        """Create s3 client to interact with remote minIO."""
        try:
            from minio import Minio
        except ImportError:
            raise VssCliError(
                'minio dependency not found. '
                'try running "pip install vss-cli[stor]"'
            )

        super().get_vskey_stor(
            user=self.username,
            password=self.password,
            s3_endpoint=self.s3_server,
        )
        _LOGGING.debug(
            f's3_endpoint={self.vskey_stor_s3api} '
            f'vskey_stor_s3_gui={self.vskey_stor_s3_gui}'
        )
        return self.vskey_stor

    def enable_vss_vpn(self, **kwargs):
        """Enable VPN."""
        self.init_vss_vpn(self.vpn_server)
        _LOGGING.debug(f'{self.totp=} {self.username=} -> {self.vpn_server=}')
        rv = super().enable_vss_vpn(
            user=self.username, password=self.password, otp=self.totp
        )
        return rv

    def get_vss_vpn_status(self, **kwargs) -> Dict:
        """Get status of VPN."""
        self.init_vss_vpn(self.vpn_server)
        _LOGGING.debug(f'{self.username=} -> {self.vpn_server=}')
        rv = super().get_vss_vpn_status(
            user=self.username,
            password=self.password,
        )
        return rv

    def monitor_vss_vpn(self, **kwargs):
        """Monitor VPN."""
        self.init_vss_vpn(self.vpn_server)
        _LOGGING.debug(f'{self.username=} -> {self.vpn_server=}')
        rv = super().monitor_vss_vpn(
            user=self.username,
            password=self.password,
            stamp=kwargs.get('stamp'),
        )
        return rv

    def disable_vss_vpn(self, **kwargs):
        """Disable VPN."""
        self.init_vss_vpn(self.vpn_server)
        _LOGGING.debug(f'{self.username=} -> {self.vpn_server=}')
        rv = super().disable_vss_vpn(
            user=self.username,
            password=self.password,
        )
        return rv

    def get_vm_by_id_or_name(
        self, vm_id: str, silent=False, instance_type: str = 'vm'
    ) -> Optional[List[Dict[str, Any]]]:
        """Get VM by ID or Name.

        This new implementation uses instance_type to distinct between
        vm and template to either one instead of looking for both.

        :param vm_id: VM ID (moref, uuid) or Name
        :param silent: Silent mode
        :param instance_type: Instance type
        :return: Single object or None
        """
        is_moref = validate_vm_moref('', '', vm_id)
        is_uuid = validate_uuid('', '', vm_id)
        _LOGGING.debug(f'{is_moref=} {is_uuid=} {vm_id=} {instance_type=}')
        # instance_type lookup dictionary
        lookup = {'vm': self.get_vms, 'template': self.get_templates}
        try:
            lookup_f = lookup[instance_type]
        except KeyError:
            raise click.BadArgumentUsage(
                f'instance_type {instance_type} not supported'
            )
        # If it's a moref or uuid, then we can use the filter
        if is_moref or is_uuid:
            if is_moref:
                attr = 'moref'
            else:
                attr = 'uuid'
            filters = f'{attr},eq,{vm_id}'
            v = lookup_f(filter=filters)
            _LOGGING.debug(f'Using {lookup_f=} {attr=} {filters=}')
            if not v:
                if silent:
                    return None
                else:
                    raise click.BadArgumentUsage(
                        f'{instance_type} id {vm_id} could not be found'
                    )
            return v
        else:
            _LOGGING.debug(f'not a moref or uuid {vm_id}')
            # If it's a value error, then the string
            # is not a valid hex code for a UUID.
            # get vm by name
            g_vms = lookup_f(per_page=3000)
            vm_id = vm_id.lower()
            v = list(filter(lambda i: vm_id in i['name'].lower(), g_vms))
            if not v:
                if not v:
                    raise click.BadParameter(f'{vm_id} could not be found')
            v_count = len(v)
            if v_count > 1:
                msg = f"Found {v_count} matches. Please select one:"
                sel, index = pick(
                    title=msg,
                    indicator='=>',
                    options=[
                        f"({i['moref']}) {i['folder']['path']} > {i['name']}"
                        for i in v
                    ],
                )
                return [v[index]]
            return v

    def get_vm_snapshot_by_id_name_or_desc(
        self, vm_id: str, id_name_or_desc: str
    ) -> List[Dict]:
        """Get vm snapshot by id name or description."""
        snapshots = self.get_vm_snapshots(vm_id)
        attributes = [('id', int), ('name', str), ('description', str)]
        objs = self._filter_objects_by_attrs(
            id_name_or_desc, snapshots, attributes
        )
        if not objs:
            raise click.BadParameter(f'{id_name_or_desc} could not be found')
        d_count = len(objs)
        if d_count > 1:
            return self.pick(
                objs,
                options=[f"{i['name']} ({i['description']})" for i in objs],
            )
        return objs

    def get_vm_restore_points_by_id_or_timestamp(
        self, vm_id: str, id_or_timestamp: str
    ) -> List[Dict]:
        """Get vm restore points by id or timestamp."""
        rps = self.get_vm_restore_points(vm_id)
        attributes = [('id', int), ('timestamp', str)]
        objs = self._filter_objects_by_attrs(id_or_timestamp, rps, attributes)
        if not objs:
            raise click.BadParameter(f'{id_or_timestamp} could not be found')
        d_count = len(objs)
        if d_count > 1:
            return self.pick(
                objs,
                options=[f"{i['id']} ({i['timestamp']})" for i in objs],
            )
        return objs

    def get_domain_by_name_or_moref(self, name_or_moref: str) -> List[Dict]:
        """Get domain by name or mo reference."""
        g_domains = self.get_domains()
        attributes = [('name', str), ('moref', str)]
        objs = self._filter_objects_by_attrs(
            name_or_moref, g_domains, attributes
        )
        if not objs:
            raise click.BadParameter(f'{name_or_moref} could not be found')
        d_count = len(objs)
        if d_count > 1:
            return self.pick(
                objs, options=[f"{i['name']} ({i['moref']})" for i in objs]
            )
        return objs

    def get_network_by_name_or_moref(self, name_or_moref: str) -> List[Dict]:
        """Get network by name or mo reference."""
        g_networks = self.get_networks(
            sort='name,desc', show_all=True, per_page=500
        )
        attributes = [('name', str), ('moref', str)]
        objs = self._filter_objects_by_attrs(
            name_or_moref, g_networks, attributes
        )
        if not objs:
            raise click.BadParameter(f'{name_or_moref} could not be found')
        net_count = len(objs)
        if net_count > 1:
            return self.pick(
                objs, options=[f"{i['name']} ({i['moref']})" for i in objs]
            )
        return objs

    def get_folder_by_name_or_moref_path(
        self, name_moref_path: str, silent: bool = False
    ) -> List[Dict]:
        """Get domain by name or mo reference."""
        g_folders = self.get_folders(
            sort='path,desc', show_all=True, per_page=500
        )
        # search by name or moref
        attributes = [('name', str), ('path', str), ('moref', str)]
        objs = self._filter_objects_by_attrs(
            name_moref_path, g_folders, attributes
        )
        if not objs and not silent:
            raise click.BadParameter(f'{name_moref_path} could not be found')
        obj_count = len(objs)
        if obj_count > 1:
            return self.pick(
                objs, options=[f"{i['path']} ({i['moref']})" for i in objs]
            )
        return objs

    def get_os_by_name_or_guest(self, name_or_guest: str) -> List[Dict]:
        """Get operating system by name, ``guest_id`` or ``full_name``."""
        g_os = self.get_os(
            sort='guestFullName,desc', show_all=True, per_page=500
        )
        attributes = [('id', int), ('guest_id', str), ('full_name', str)]
        objs = self._filter_objects_by_attrs(name_or_guest, g_os, attributes)
        if not objs:
            raise click.BadParameter(f'{name_or_guest} could not be found')
        o_count = len(objs)
        if o_count > 1:
            return self.pick(
                objs,
                options=[f"{i['full_name']} ({i['guest_id']})" for i in objs],
            )
        return objs

    def get_vss_service_by_name_label_or_id(
        self, name_label_or_id: Union[str, int]
    ) -> List[Dict]:
        """Get service by name label or identifier."""
        vss_services = self.get_vss_services(
            sort='label,desc', show_all=True, per_page=200
        )
        attributes = [('id', int), ('label', str), ('name', str)]
        objs = self._filter_objects_by_attrs(
            name_label_or_id, vss_services, attributes
        )
        # check if there's no ref
        if not objs:
            raise click.BadParameter(f'{name_label_or_id} could not be found')
        # count for dup results
        o_count = len(objs)
        if o_count > 1:
            return self.pick(objs, options=[f"{i['label']}" for i in objs])
        return objs

    def get_vss_groups_by_name_desc_or_id(
        self, name_desc_or_id: Union[str, int]
    ) -> List[Dict]:
        """Get groups by name, description or identifier."""
        vss_groups = self.get_user_groups(
            sort='name,desc', show_all=True, per_page=100
        )
        attributes = [('id', int), ('name', str), ('description', str)]
        objs = self._filter_objects_by_attrs(
            name_desc_or_id, vss_groups, attributes
        )
        # check if there's no ref
        if not objs:
            raise click.BadParameter(f'{name_desc_or_id} could not be found')
        # count for dup results
        o_count = len(objs)
        if o_count > 1:
            return self.pick(
                objs,
                options=[
                    f"{i['name']} ({i['id']}): {i['description'][:40]}... "
                    for i in objs
                ],
            )
        return objs

    def _get_images_by_name_path_or_id(
        self, f: Callable, name_or_path_or_id: Union[int, str]
    ) -> List[Dict]:
        """Get images by name path or identifier."""
        g_img = f(show_all=True, per_page=500)
        attributes = [('id', int), ('name', str), ('path', str)]
        objs = self._filter_objects_by_attrs(
            name_or_path_or_id, g_img, attributes
        )
        # check if there's no ref
        if not objs:
            raise click.BadParameter(
                f'{name_or_path_or_id} could not be found'
            )
        # count for dup results
        o_count = len(objs)
        if o_count > 1:
            return self.pick(objs, options=[f"{i['name']}" for i in objs])
        return objs

    def get_vmdk_by_name_path_or_id(
        self, name_or_path_or_id: Union[str, int]
    ) -> List[Any]:
        """Get vmdk by name, path or id."""
        return self._get_images_by_name_path_or_id(
            self.get_user_vmdks, name_or_path_or_id
        )

    def get_floppy_by_name_or_path(
        self, name_or_path_or_id: Union[str, int]
    ) -> List[Dict]:
        """Get Floppy image by name, path or identifier."""
        return self._get_images_by_name_path_or_id(
            self.get_floppies, name_or_path_or_id
        )

    def get_iso_by_name_or_path(
        self, name_or_path_or_id: Union[str, int]
    ) -> List[Any]:
        """Get ISO image by name, path or identifier."""
        return self._get_images_by_name_path_or_id(
            self.get_isos, name_or_path_or_id
        )

    def get_clib_deployable_item_by_name_or_id_path(
        self, name_or_id_or_path: Union[str, int]
    ):
        """Get content library deployable items."""
        items = self.get_content_library_items(
            show_all=True,
            sort='path,desc',
            per_page=500,
            filter="type,in,OVF,VM_TEMPLATE",
        )
        attrs = [('id', int), ('name', str)]
        objs = self._filter_objects_by_attrs(name_or_id_or_path, items, attrs)
        # check if there's no ref
        if not objs:
            raise click.BadParameter(
                f'{name_or_id_or_path} could not be found'
            )
        # count for dup results
        o_count = len(objs)
        if o_count > 1:
            return self.pick(objs, options=[f"{i['name']}" for i in objs])
        return objs

    def get_vm_image_by_name_or_id_path(
        self, name_or_path_or_id: Union[str, int]
    ) -> List[Any]:
        """Get VM image by name, path or identifier."""
        return self._get_images_by_name_path_or_id(
            self.get_images, name_or_path_or_id
        )

    def _get_types_by_name(self, name: Union[str, int], types_f, attrs=None):
        g_types = types_f(only_type=False)
        attributes = attrs or [('type', str)]
        objs = self._filter_objects_by_attrs(str(name), g_types, attributes)
        # check if there's no ref
        if not objs:
            raise click.BadParameter(f'{name} could not be found')
        # count for dup results
        o_count = len(objs)
        if o_count > 1:
            return self.pick(
                objs,
                options=[
                    f"{i['type']} - {i['description'][:100]}..." for i in objs
                ],
            )
        return objs

    def get_vm_scsi_type_by_name(self, name: Union[str, int]):
        """Get SCSI type by name."""
        return self._get_types_by_name(
            name, self.get_supported_scsi_controllers
        )

    def get_vm_scsi_sharing_by_name(self, name: Union[str, int]):
        """Get SCSI sharing by name."""
        return self._get_types_by_name(name, self.get_supported_scsi_sharing)

    def get_vm_disk_backing_mode_by_name(self, name: Union[str, int]):
        """Get Disk Backing Mode by name."""
        return self._get_types_by_name(
            name, self.get_supported_disk_backing_modes
        )

    def get_vm_disk_backing_sharing_by_name(self, name: Union[str, int]):
        """Get Disk Sharing Mode by name."""
        return self._get_types_by_name(name, self.get_supported_disk_sharing)

    def get_vm_firmware_by_type_or_desc(self, name: Union[str, int]):
        """Get VM firmware by name."""
        return self._get_types_by_name(
            name,
            self.get_supported_firmware_types,
            attrs=[('type', str), ('description', str)],
        )

    def get_vm_gpu_profiles_by_name_or_desc(self, name: Union[str, int]):
        """Get VM gpu by name or desc."""
        return self._get_types_by_name(
            name,
            self.get_supported_gpu_types,
            attrs=[('type', str), ('description', str)],
        )

    def get_vm_storage_type_by_type_or_desc(self, name: Union[str, int]):
        """Get VM supported storage types by name."""
        return self._get_types_by_name(
            name,
            self.get_supported_storage_types,
            attrs=[('type', str), ('description', str)],
        )

    def get_vm_nic_type_by_name(self, name: Union[str, int]):
        """Get VM NIC type by name."""
        g_types = self.get_supported_nic_types(only_type=False)
        attributes = [('type', str)]
        objs = self._filter_objects_by_attrs(name, g_types, attributes)
        # check if there's no ref
        if not objs:
            raise click.BadParameter(f'{name} could not be found')
        # count for dup results
        o_count = len(objs)
        if o_count > 1:
            return self.pick(
                objs,
                options=[
                    f"{i['type']} - {i['description'][:100]}..." for i in objs
                ],
            )
        return objs

    def get_cli_spec_from_api_spec(
        self, payload: dict, template: dict
    ) -> Dict:
        """Get CLI specification from API specification."""
        os_q = self.get_os(filter=f"guest_id,eq,{payload.get('os')}")
        machine_os = os_q[0]['full_name'] if os_q else payload.get('os')
        fo_q = self.get_folder(payload.get('folder'))
        machine_folder = fo_q['path'] if fo_q else payload.get('folder')
        template['built'] = payload.get('built_from')
        template['machine']['name'] = payload.get('name')
        template['machine']['os'] = machine_os
        template['machine']['cpu'] = payload.get('cpu')
        template['machine']['memory'] = payload.get('memory')
        template['machine']['folder'] = machine_folder
        template['machine']['disks'] = payload.get('disks')
        template['machine']['scsi'] = payload.get('scsi')
        template['machine']['storage-type'] = payload.get('storage_type')
        template['machine']['iso'] = payload.get('iso')
        template['networking']['interfaces'] = [
            {
                'network': self.get_network(v['network'])['name'],
                'type': v['type'],
            }
            for v in payload.get('networks')
        ]
        template['metadata']['client'] = payload.get('client')
        template['metadata']['description'] = payload.get('description')
        template['metadata']['usage'] = payload.get('usage')
        template['metadata']['inform'] = payload.get('inform')
        template['metadata']['admin'] = {
            'name': payload.get('admin_name'),
            'email': payload.get('admin_email'),
            'phone': payload.get('admin_phone'),
        }
        template['metadata']['vss_service'] = payload.get('vss_service')
        template['metadata']['vss_options'] = payload.get('vss_options')
        return template

    @staticmethod
    def parse_ova_or_ovf(file_path: Union[Path, str]) -> Dict:
        """Parse ova or ovf."""
        file = Path(file_path)
        ovf_str = ''
        if file.suffix.lower() == '.ovf':
            ovf_str = file.read_text()
        elif file.suffix.lower() in ['.ova', '.zip', '.tar']:
            import tarfile

            tar = tarfile.open(str(file))
            ovf_member = list(
                filter(lambda x: '.ovf' in x.name.lower(), tar.getmembers())
            )
            if ovf_member:
                f = tar.extractfile(ovf_member[0])
                ovf_str = f.read()
                tar.close()
        else:
            raise VssCliError('Invalid OVA/OVF format.')
        # proceed to parsing
        import xmltodict

        xpars = xmltodict.parse(ovf_str)
        data = json.dumps(xpars)
        data_dict = json.loads(data)
        _LOGGING.debug(f'Parsed OVF and found keys: {data_dict.keys()}')
        if 'Envelope' not in data_dict and 'ovf:Envelope' not in data_dict:
            raise VssCliError('Invalid OVF format: missing ovf:Envelope')
        ovf_dict = data_dict.get('Envelope') or data_dict.get('ovf:Envelope')
        output = {}
        # process first Strings or ovf:Strings for reference
        ovf_strings = {}
        has_strings = ovf_dict.get('Strings') or ovf_dict.get('ovf:Strings')
        if has_strings:
            msgs = has_strings.get('Msg', [])
            for msg in msgs:
                _key = msg.get('@ovf:msgid')
                _val = msg.get('#text')
                ovf_strings[_key] = _val
        for key, value in ovf_dict.items():
            # ovf:References
            if key in ['References', 'ovf:References']:
                files_ref = value.get('File') or value.get('ovf:File', [])
                if isinstance(files_ref, dict):
                    files_ref = [files_ref]
                files = [
                    {
                        'href': x['@ovf:href'],
                        'id': x['@ovf:id'],
                        'size': x['@ovf:size'],
                    }
                    for x in files_ref
                ]
                output['Files'] = files
            # ovf:DiskSection
            elif key in ['DiskSection', 'ovf:DiskSection']:
                disks_ref = value.get('Disk') or value.get('ovf:Disk', [])
                _LOGGING.debug(
                    f'Found Disks: {disks_ref}: type: {type(disks_ref)}'
                )
                if isinstance(disks_ref, dict):
                    disks_ref = [disks_ref]
                disks = [
                    {
                        'capacity': x['@ovf:capacity'],
                        'capacityAllocationUnits': x[
                            '@ovf:capacityAllocationUnits'
                        ],
                        'diskId': x['@ovf:diskId'],
                        'fileRef': x.get('@ovf:fileRef'),
                    }
                    for x in disks_ref
                ]
                output['Disks'] = disks
            # ovf:NetworkSection
            elif key in ['NetworkSection', 'ovf:NetworkSection']:
                nets = value.get('Network') or value.get('ovf:Network', [])
                _LOGGING.debug(f'Found Networks: {nets}: type: {type(nets)}')
                if isinstance(nets, dict):
                    nets = [nets]
                networks = [
                    {
                        'name': x['@ovf:name'],
                        'description': x.get('Description')
                        or x.get('ovf:Description'),
                    }
                    for x in nets
                ]
                output['Networks'] = networks
            # ovf:DeploymentOptionSection
            elif key in [
                'DeploymentOptionSection',
                'ovf:DeploymentOptionSection',
            ]:
                raw_dparams = value.get('Configuration') or value.get(
                    'ovf:Configuration', []
                )
                dparams = []
                for x in raw_dparams:
                    _desc = x.get('Description') or x.get('ovf:Description')
                    _label = x.get('Label') or x.get('ovf:Label')
                    label = ''
                    description = _desc
                    if isinstance(_desc, dict):
                        if '@ovf:msgid' in _desc or 'msgid' in _desc:
                            description = ovf_strings.get(
                                _desc.get('@ovf:msgid') or _desc.get('msgid')
                            )
                    if isinstance(_label, dict):
                        if '@ovf:msgid' in _desc or 'msgid' in _label:
                            label = ovf_strings.get(
                                _label.get('@ovf:msgid') or _label.get('msgid')
                            )
                    obj = {
                        'id': x['@ovf:id'],
                        'description': description,
                        'label': label,
                    }
                    dparams.append(obj)

                output['DeploymentOptionParams'] = dparams
            # ovf:VirtualSystem
            elif key in ['VirtualSystem', 'ovf:VirtualSystem']:
                output['Name'] = value.get('ovf:Name') or value.get('Name')
                if 'ovf:ProductSection' in value or 'ProductSection' in value:
                    prod_sect = value.get('ProductSection') or value.get(
                        'ovf:ProductSection'
                    )
                    prod_props = []
                    if isinstance(prod_sect, list):
                        for item in prod_sect:
                            if 'Product' in item:
                                output['Product'] = item.get('Product')
                            if 'Vendor' in item:
                                output['Vendor'] = item.get('Vendor')
                            if 'Property' in item:
                                prod_props.extend(item.get('Property', []))
                    elif isinstance(prod_sect, dict):
                        output['Product'] = prod_sect.get(
                            'Product'
                        ) or prod_sect.get('ovf:FullVersion')
                        output['Version'] = prod_sect.get(
                            'Version'
                        ) or prod_sect.get('ovf:Version')
                    if (
                        'Property' in prod_sect
                        or 'ovf:Property' in prod_sect
                        or prod_props
                    ):
                        pparams = []
                        properties = (
                            prod_props
                            or prod_sect.get('Property')
                            or prod_sect.get('ovf:Property', [])
                        )
                        for prop in properties:
                            if (
                                prop.get('@ovf:userConfigurable', None)
                                == 'true'
                            ):
                                prop = {
                                    'key': prop['@ovf:key'],
                                    'type': prop['@ovf:type'],
                                    'description': prop.get('Description')
                                    or prop.get('ovf:Description')
                                    or prop.get('Label')
                                    or prop.get('ovf:Label'),
                                    'default': prop.get('@ovf:value'),
                                }
                                pparams.append(prop)
                        output['PropertyParams'] = pparams
        return output

    def yaml(self) -> YAML:
        """Create default yaml parser."""
        if self:
            return yaml.yaml()

    def yaml_load(self, source: str) -> Any:
        """Load YAML from source."""
        return self.yaml().load(source)

    def yaml_dump(self, source: Any) -> str:
        """Dump dictionary to YAML string."""
        return cast(str, yaml.dump_yaml(self.yaml(), source))

    def yaml_dump_stream(
        self, data: Any, stream: Any = None, **kw: Any
    ) -> Optional[str]:
        """Dump yaml to stream."""
        return yaml.dump_yaml(self.yaml(), data, stream, **kw)

    def download_inventory_file(
        self, request_id: int, directory: str = ''
    ) -> Dict:
        """Download inventory file to a given directory."""
        with self.spinner(disable=self.debug):
            file_path = self.download_inventory_result(
                request_id=request_id, directory=directory
            )
        obj = {'file': file_path}

        self.echo(
            format_output(self, [obj], columns=[('FILE', 'file')], single=True)
        )
        return obj

    def wait_for_requests_to(
        self,
        obj,
        required: List[str] = (
            RequestStatus.PROCESSED.name,
            RequestStatus.SCHEDULED.name,
        ),
        wait: int = 5,
        max_tries: int = 720,
        in_multiple: bool = False,
    ):
        """Wait for multiple requests to complete."""
        if not in_multiple:
            objs = [
                dict(
                    _links=dict(request=r_url),
                    status=obj['status'],
                    request=dict(id=os.path.basename(r_url)),
                )
                for r_url in obj['_links']['request']
            ]
        else:
            objs = obj
        wq = WorkerQueue(max_workers=len(objs))

        with wq.join(debug=self.debug):
            for obj in objs:
                wq.put(
                    functools.partial(
                        self.wait_for_request_to,
                        obj=obj,
                        required=required,
                        wait=wait,
                        max_tries=max_tries,
                        threaded=True,
                    )
                )
                wq.spawn_worker()

    def wait_for_request_to(
        self,
        obj: dict,
        required: List[str] = (
            RequestStatus.PROCESSED.name,
            RequestStatus.SCHEDULED.name,
        ),
        wait: int = 5,
        max_tries: int = 720,
        threaded: bool = False,
    ) -> Optional[bool]:
        """Wait for request to given status."""
        # wait
        request_message = {}
        err_status = [
            RequestStatus.ERROR.name,
            RequestStatus.ERROR_RETRY.name,
            RequestStatus.CANCELLED.name,
        ]
        wait_status = [
            RequestStatus.PENDING.name,
            RequestStatus.IN_PROGRESS.name,
            RequestStatus.APPROVAL_REQUIRED.name,
        ]
        _LOGGING.debug(
            f'max tries={max_tries}, wait={wait}, '
            f'required status={",".join(required)}'
        )
        request_id = obj["request"]["id"]
        self.secho(
            f'{EMOJI_UNICODE.get(":hourglass_not_done:")} '
            f'Waiting for request {request_id} to complete... ',
            fg='green',
            nl=True,
        )
        # check for request status
        if 199 < obj['status'] < 300:
            pass
        else:
            raise VssCliError('Invalid response from the API.')
        with self.spinner(disable=self.debug or threaded):
            r_url = obj['_links']['request']
            tries = 0
            while True:
                request = self.request(r_url)
                if 'data' in request:
                    status = request['data']['status']
                    request_message = request['data']['message']
                    if status in required:
                        request_status = True
                        break
                    if status in err_status:
                        request_status = False
                        break
                    elif status in wait_status:
                        pass
                else:
                    request_status = False
                    break
                if tries >= max_tries:
                    raise VssCliError(
                        f'Wait for request timed out after '
                        f'{max_tries * wait} seconds.'
                    )
                tries += 1
                sleep(wait)
        # check result status
        request_message_str = format_output(
            self,
            [request_message],
            columns=const.COLUMNS_REQUEST_WAIT,
            single=True,
        )
        sys.stdout.flush()
        if request_status:
            self.secho(
                f'{EMOJI_UNICODE.get(":party_popper:")} '
                f'Request {request_id} completed successfully:',
                fg='green',
            )
            self.echo(f'{request_message_str}')
        else:
            self.secho(
                f'{EMOJI_UNICODE.get(":worried_face:")} '
                f'Request {request_id} completed with errors:',
                err=True,
                fg='red',
            )
            self.echo(f'{request_message_str}')
            return False
        return True

    @staticmethod
    def smooth_print(text: str, delay=0.001):
        """Print text with smooth line breaks."""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)

    @staticmethod
    def clear_console():
        """Clear console."""
        # For Windows
        if os.name == 'nt':
            os.system('cls')
        # For macOS and Linux
        else:
            os.system('clear')

    def _get_client_ip(self) -> str:
        """Get the client's IP address."""
        import socket

        try:
            # Try to get the IP by connecting to a public DNS server
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            # Connect to Google's public DNS
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # Fallback to localhost if unable to determine
            return '127.0.0.1'

    def _generate_assistant_api_key(self) -> str:
        """Generate a new API key for the assistant."""
        ip_address = self._get_client_ip()
        client_name = f'{self.user_agent}/{ip_address}'

        auth_endpoint = f'{self.gpt_server}/api/generate-key'
        payload = {'client_name': client_name}

        with requests.post(auth_endpoint, json=payload) as response:
            if response.status_code not in [200, 201]:
                raise VssCliError(
                    f'Failed to generate API key. '
                    f'Status: {response.status_code}'
                )
            data = response.json()
            return data.get('api_key')

    def get_new_chat_id(
        self,
        chat_endpoint: str,
        persona_id: int,
        description: str,
        headers: Dict[str, str],
    ) -> Optional[int]:
        """Get the new chat id."""
        payload = {"persona_id": persona_id, "description": description}
        with requests.post(
            chat_endpoint, headers=headers, json=payload
        ) as response:
            if response.status_code in [401, 403, 500, 502, 503, 504]:
                raise VssCliError(
                    'Invalid response from the API. '
                    'Failed to create chat session.'
                )
            rv = response.json()
            chat_id = rv['chat_session_id']
            return chat_id

    def ask_assistant(
        self,
        message: str,
        spinner_cls: Optional[Spinner] = None,
        final_message: str = None,
    ) -> Tuple[str, str]:
        """Ask assistant."""
        # Generate a new API key for this session
        api_key = self._generate_assistant_api_key()

        headers = {
            'api-key': f'{api_key}',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
        }
        top_documents = []
        chat_id = self.get_new_chat_id(
            chat_endpoint=f'{self.gpt_server}/api/chat/create-chat-session',
            persona_id=self.gpt_persona or self._gpt_persona,
            description=message[:20],
            headers=headers,
        )
        # chat payload
        payload = {
            "chat_session_id": chat_id,
            "message": message,
            "parent_message_id": None,
        }
        _LOGGING.debug(f'User data payload {payload}')
        answer_text = ''
        with requests.post(
            f'{self.gpt_server}/api/chat/send-message',
            json=payload,
            stream=True,
            headers=headers,
        ) as response:
            if spinner_cls is not None:
                spinner_cls.stop()
            reasoning_text = ''
            message_content = ''
            internal_search_queries = []
            internal_search_docs = []
            final_documents = []
            citations = []
            assistant_message_id = None

            for line in response.iter_lines():
                _LOGGING.debug(f"{line=}")
                if line:
                    data = json.loads(line)

                    # Handle initial message IDs
                    if (
                        'user_message_id' in data
                        and 'reserved_assistant_message_id' in data
                    ):
                        assistant_message_id = data[
                            'reserved_assistant_message_id'
                        ]
                        _LOGGING.debug(
                            f"Message IDs - User: {data['user_message_id']},"
                            f" Assistant: {assistant_message_id}"
                        )
                        continue

                    # Handle indexed objects
                    if 'ind' in data and 'obj' in data:
                        obj = data['obj']
                        obj_type = obj.get('type')

                        # Handle reasoning streaming
                        if obj_type == 'reasoning_start':
                            _LOGGING.debug("Reasoning started")
                        elif obj_type == 'reasoning_delta':
                            reasoning_chunk = obj.get('reasoning', '')
                            reasoning_text += reasoning_chunk
                            # Optionally display reasoning to user
                            # (you might want to hide this)
                            self.smooth_print(reasoning_chunk)

                        # Handle message content streaming
                        elif obj_type == 'message_start':
                            if 'final_documents' in obj:
                                final_documents = obj['final_documents']
                            _LOGGING.debug("Message started")
                        elif obj_type == 'message_delta':
                            content_chunk = obj.get('content', '')
                            message_content += content_chunk
                            answer_text += content_chunk
                            self.smooth_print(content_chunk)

                        # Handle internal search tool
                        elif obj_type == 'internal_search_tool_start':
                            _LOGGING.debug(
                                f"Internal search started - Internet: "
                                f"{obj.get('is_internet_search', False)}"
                            )
                        elif obj_type == 'internal_search_tool_delta':
                            if 'queries' in obj and obj['queries']:
                                internal_search_queries.extend(obj['queries'])
                            if 'documents' in obj and obj['documents']:
                                internal_search_docs.extend(obj['documents'])
                                # Update top_documents for backward
                                # compatibility
                                top_documents = obj['documents']

                        # Handle citations
                        elif obj_type == 'citation_start':
                            _LOGGING.debug("Citations started")
                        elif obj_type == 'citation_delta':
                            if 'citations' in obj:
                                citations.extend(obj['citations'])

                        # Handle section end and stop
                        elif obj_type == 'section_end':
                            _LOGGING.debug(
                                f"Section ended for index {data['ind']}"
                            )
                        elif obj_type == 'stop':
                            _LOGGING.debug(
                                f"Stream stopped for index {data['ind']}"
                            )

                    # Handle legacy format (backward compatibility)
                    elif 'top_documents' in data:
                        top_documents = data['top_documents']
                    elif 'answer_piece' in data:
                        answer_piece = data['answer_piece']
                        if answer_piece is not None:
                            answer_text = answer_text + answer_piece
                            self.smooth_print(answer_piece)
        # Use final_documents if available, otherwise fall
        # back to top_documents
        docs_to_display = final_documents if final_documents else top_documents

        docs = []
        n = 1
        for doc in docs_to_display:
            # Handle both document_id and link fields
            doc_url = doc.get("link") or doc.get("document_id", "")
            doc_title = doc.get("semantic_identifier", "Unknown Document")
            docs.append(f'[{n}] [{doc_title}]({doc_url})')
            n += 1
        # make docs
        docs_text = '\n'.join(docs[:5])
        answer_text = answer_text + '\n\n' + docs_text
        # clear console for formatting
        if not self.debug:
            self.clear_console()
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()
        markdown = Markdown(answer_text)
        console.print(markdown)
        console.print()
        console.print(Markdown(f'**Note: {final_message}**'))

        # Return the assistant message ID and API key
        # for potential feedback
        return assistant_message_id, api_key

    def provide_assistant_feedback(
        self,
        chat_message_id: str,
        api_key: str,
        is_positive: bool,
        feedback_text: Optional[str] = None,
    ) -> bool:
        """Provide feedback for an assistant response.

        Args:
            chat_message_id: The ID of the assistant message
            to provide feedback for
            api_key: The API key generated for this session
            is_positive: True for thumbs up, False for thumbs down
            feedback_text: Optional feedback text (defaults to
            'Helpful' or 'Not helpful')

        Returns:
            bool: True if feedback was submitted successfully, False otherwise
        """
        if feedback_text is None:
            feedback_text = 'Helpful' if is_positive else 'Not helpful'

        headers = {
            'api-key': f'{api_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            "chat_message_id": chat_message_id,
            "is_positive": is_positive,
            "feedback_text": feedback_text,
            "predefined_feedback": None,
        }

        feedback_endpoint = f'{self.gpt_server}/api/chat/create-chat-feedback'

        try:
            with requests.post(
                feedback_endpoint, headers=headers, json=payload
            ) as response:
                if response.status_code in [200, 201]:
                    _LOGGING.debug(
                        f'Feedback submitted successfully '
                        f'for message {chat_message_id}'
                    )
                    return True
                else:
                    _LOGGING.warning(
                        f'Failed to submit feedback. '
                        f'Status: {response.status_code}, '
                        f'Response: {response.text}'
                    )
                    return False
        except Exception as e:
            _LOGGING.error(f'Error submitting feedback: {e}')
            return False
