"""Configuration plugin for VSS CLI (vss-cli)."""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import click
from ruamel.yaml.parser import ParserError

from vss_cli import const
from vss_cli.cli import pass_context
from vss_cli.config import Configuration
from vss_cli.credentials.base import CredentialType, detect_backend
from vss_cli.data_types import ConfigEndpoint
from vss_cli.helper import format_output, str2bool
from vss_cli.utils.emoji import EMOJI_UNICODE

_LOGGING = logging.getLogger(__name__)


ej_warn = EMOJI_UNICODE.get(':alien:')
ej_rkt = EMOJI_UNICODE.get(':rocket:')
ej_tada = EMOJI_UNICODE.get(':party_popper:')
ej_save = EMOJI_UNICODE.get(':floppy_disk:')
ej_check = EMOJI_UNICODE.get(':white_heavy_check_mark:')


@click.group('configure')
@pass_context
def cli(ctx: Configuration):
    """Configure VSS-CLI options."""
    ctx.auto_output('table')


@cli.command('upgrade', short_help='Upgrade legacy configuration.')
@click.argument(
    'legacy_config',
    envvar='VSS_CONFIG',
    type=click.Path(exists=True),
    default=const.LEGACY_CONFIG,
)
@click.option(
    '-c',
    '--confirm',
    is_flag=True,
    default=False,
    help='Proceed with migration without prompting confirmation.',
)
@click.option(
    '-o',
    '--overwrite',
    is_flag=True,
    default=False,
    help='Overwrite if target file exists.',
)
@pass_context
def upgrade(ctx: Configuration, legacy_config, confirm, overwrite):
    """Upgrade legacy configuration (config.json) to current (config.yaml)."""
    cfg_exc = False
    try:
        cfg_legacy = Path(legacy_config)
        with cfg_legacy.open(mode='r') as f:
            legacy_endpoints = ctx.yaml_load(f)
        endpoints = []
        if legacy_endpoints:
            n_ep = len(legacy_endpoints)
            ctx.echo(
                f'Found {n_ep} endpoints. Migrating to new configuration file.'
            )
            for ep_k, ep_v in legacy_endpoints.items():
                t_ep = {
                    'url': ep_k,
                    'auth': ep_v['auth'],
                    'token': ep_v['token'],
                }
                ep = ConfigEndpoint.from_json(json.dumps(t_ep))
                endpoints.append(ep)
            ep = len(endpoints)
            _LOGGING.debug(
                f'Successfully loaded {ep} endpoints '
                f'from legacy configuration.'
            )
            confirmation = confirm or click.confirm(
                f'\nWould you like to upgrade {ep} endpoint(s)? '
                f'This action will \n'
                f'create a new configuration file {ctx.config_path} \n'
                f'with your endpoints in it'
            )
            if confirmation:
                # load new configuration file
                config_file = ctx.load_config_template()
                config_file.update_endpoints(*endpoints)
                # check if target exists
                cfg_path = Path(ctx.config_path)
                if cfg_path.is_file():
                    if not (
                        overwrite
                        or click.confirm(f'\nOverwrite {ctx.config_path}?')
                    ):
                        raise click.Abort('Cancelled by user')
                # all ok
                ctx.write_config_file(new_config_file=config_file)
                ctx.secho(
                    f'\nSuccessfully migrated {legacy_config} {ej_tada}',
                    fg='green',
                    nl=True,
                )
            else:
                raise click.Abort('Cancelled by user')
        else:
            _LOGGING.warning('No endpoints found in configuration file.')
            cfg_exc = True
    except KeyError as ex:
        _LOGGING.warning(f'Missing {str(ex)} in endpoint configuration.')
        cfg_exc = True
    except (TypeError, ParserError) as ex:
        _LOGGING.warning(f'{str(ex)}')
        cfg_exc = True
    finally:
        if cfg_exc:
            _LOGGING.warning(
                'Try running "vss-cli configure mk" '
                'to create a new configuration file.'
            )


@cli.command('mk', short_help='Create new endpoint configuration.')
@click.option(
    '-r',
    '--replace',
    is_flag=True,
    default=False,
    help='Replace existing configuration',
)
@click.option(
    '-e',
    '--endpoint-name',
    type=click.STRING,
    help='Custom endpoint name. Default to endpoint hostname.',
    required=False,
)
@pass_context
def mk(ctx: Configuration, replace: bool, endpoint_name: str):
    """Create new configuration or add profile to config file."""
    new_endpoint = ctx.endpoint or click.prompt(
        'Endpoint',
        default=const.DEFAULT_ENDPOINT,
        type=click.STRING,
        show_default=True,
        err=True,
    )
    endpoint_name = endpoint_name or click.prompt(
        'Endpoint Name',
        default=ctx.endpoint_name,
        type=click.STRING,
        show_default=True,
        err=True,
    )
    username = ctx.username or click.prompt(
        'Username',
        default=ctx.username,
        show_default=True,
        type=click.STRING,
        err=True,
    )
    password = ctx.password or click.prompt(
        'Password',
        default=ctx.password,
        show_default=False,
        hide_input=True,
        type=click.STRING,
        confirmation_prompt=True,
        err=True,
    )
    is_configured = ctx.configure(
        username=username,
        password=password,
        endpoint=new_endpoint,
        replace=replace,
        endpoint_name=endpoint_name,
    )
    if is_configured:
        # feedback message
        ctx.secho(
            f'You are ready to use the vss-cli {ej_rkt}',
            file=sys.stderr,
            fg='green',
        )
    else:
        _LOGGING.warning(
            f'Houston, we have a problem {ej_warn}. '
            f'Could not create configuration.'
        )


COLUMNS_DETAILS = [
    ("NAME", "name"),
    ("ENDPOINT", "endpoint"),
    ("USER", "user"),
    ("PASS", "pass"),
    ("MFA", "mfa"),
    ("TOKEN", "token"),
    ("SOURCE", "source"),
    ('DEFAULT', 'default'),
]


@cli.command('set', short_help='Update general settings attribute.')
@click.argument('setting', type=click.Choice(const.GENERAL_SETTINGS.keys()))
@click.argument('value', type=click.STRING)
@pass_context
def set_cfg(ctx: Configuration, setting: str, value: Any):
    """Set the configuration attribute in the general section."""
    ctx.load_config(validate=False)
    data_type = const.GENERAL_SETTINGS[setting]
    was = None
    to = None
    try:
        was = getattr(ctx.config_file.general, setting)
        f = str2bool if data_type == bool else data_type
        to = f(value)
        if setting == 'default_endpoint_name':
            is_ok = ctx.config_file.get_endpoint(value)
            if not is_ok:
                raise click.BadArgumentUsage(
                    f'Endpoint {value} does not exist. '
                    f'Run "vss-cli configure mk -e {value}" '
                    f'to create endpoint first.'
                )
        setattr(ctx.config_file.general, setting, to)
    except ValueError:
        _LOGGING.warning(f'{setting} value must be {data_type}')
    ctx.secho(
        f"Updating {setting} from {was} -> {to}.",
        file=sys.stderr,
    )
    ctx.write_config_file(config_general=ctx.config_file.general)
    ctx.secho(
        f"{ctx.config_path} updated {ej_save}", file=sys.stderr, fg='green'
    )
    return


@cli.command('ls', short_help='List existing endpoint configuration')
@pass_context
def ls(ctx: Configuration):
    """List existing configuration."""
    from base64 import b64decode

    cfg_endpoints = list()
    try:
        config_file = ctx.load_config_file()
        ctx.set_defaults()
        default_endpoint = config_file.general.default_endpoint_name
        endpoints = config_file.endpoints or []

        # Detect credential backend for secure storage
        backend = detect_backend()

        # checking profiles
        for endpoint in endpoints:
            is_default = ej_check if default_endpoint == endpoint.name else ''
            token = ''
            user = ''
            pwd = ''
            source = 'config file (legacy)'  # default source
            url = endpoint.url

            # Try loading from backend first
            try:
                if backend and backend.is_available():
                    username_value = backend.retrieve_credential(
                        endpoint.name, CredentialType.USERNAME
                    )
                    if username_value:
                        user = username_value
                        source = backend.__class__.__name__
                        # For display purposes, we show masked password
                        # even though it's not retrieved from backend
                        pwd = '********'
                    else:
                        # Fallback to legacy base64 auth
                        if endpoint.auth:
                            auth_enc = endpoint.auth.encode()
                            user, pwd = b64decode(auth_enc).split(b':')
                            user = user.decode()
                else:
                    # Backend unavailable, use legacy
                    if endpoint.auth:
                        auth_enc = endpoint.auth.encode()
                        user, pwd = b64decode(auth_enc).split(b':')
                        user = user.decode()
            except Exception as e:
                _LOGGING.debug(
                    f'Could not load credentials from backend for '
                    f'{endpoint.name}: {e}'
                )
                # Fall back to legacy
                if endpoint.auth:
                    auth_enc = endpoint.auth.encode()
                    user, pwd = b64decode(auth_enc).split(b':')
                    user = user.decode()

            masked_pwd = ''.join(['*' for i in range(len(pwd))])
            if endpoint.token:
                token = f"{endpoint.token[:10]}...{endpoint.token[-10:]}"

            cfg_endpoints.append(
                {
                    'default': is_default,
                    'name': endpoint.name,
                    'endpoint': url,
                    'user': user,
                    'mfa': 'Yes' if endpoint.tf_enabled else 'No',
                    'pass': masked_pwd[:8],
                    'token': token,
                    'source': source,
                }
            )
    except FileNotFoundError as ex:
        _LOGGING.error(f'{str(ex)}')
        ctx.secho(
            'Have you run "vss-cli configure mk"?', file=sys.stderr, fg='green'
        )

    # checking env vars
    envs = [e for e in os.environ if 'VSS_' in e]
    if envs:
        user = os.environ.get('VSS_USER', '')
        pwd = os.environ.get('VSS_USER_PASS', '')
        masked_pwd = ''.join(['*' for i in range(len(pwd))])
        tk = os.environ.get('VSS_TOKEN', '')
        endpoint = os.environ.get('VSS_ENDPOINT', const.DEFAULT_ENDPOINT)
        mfa = os.environ.get('VSS_API_USER_OTP', const.DEFAULT_TOTP)
        source = 'env'
        cfg_endpoints.append(
            {
                'endpoint': endpoint,
                'user': user,
                'pass': masked_pwd,
                'mfa': 'Yes' if mfa else 'No',
                'token': f'{tk[:10]}...{tk[-10:]}',
                'source': source,
            }
        )
    if cfg_endpoints:
        ctx.echo(format_output(ctx, cfg_endpoints, columns=COLUMNS_DETAILS))
    else:
        ctx.echo('No configuration was found')


@cli.command('edit', short_help='Edit configuration file.')
@click.option(
    '-l', '--launch', is_flag=True, help='Open config file with default editor'
)
@pass_context
def edit(ctx: Configuration, launch):
    """Edit configuration file."""
    # either launch or edit in
    if launch:
        click.launch(ctx.config_path, locate=True)
    else:
        cfg_path = Path(ctx.config_path)
        # proceed to load file
        raw = cfg_path.read_text()
        # launch editor
        new_raw = click.edit(raw, extension='.yaml')
        if new_raw is not None:
            ctx.secho(f"Updating {ctx.config_path} {ej_save}", fg='green')
            new_obj = ctx.yaml_load(new_raw)
            with cfg_path.open(mode='w') as fp:
                ctx.yaml_dump_stream(new_obj, stream=fp)
        else:
            ctx.echo("No edits/changes returned from editor.")
            return


@cli.command(
    'migrate-credentials',
    short_help='Migrate credentials to secure storage backend.',
)
@click.option(
    '-y',
    '--yes',
    is_flag=True,
    default=False,
    help='Proceed without confirmation prompts.',
)
@click.option(
    '--dry-run',
    is_flag=True,
    default=False,
    help='Show migration plan without making changes.',
)
@click.option(
    '--rollback',
    is_flag=True,
    default=False,
    help='Rollback previous migration and restore backup.',
)
@click.option(
    '--validate',
    is_flag=True,
    default=False,
    help='Validate migrated credentials.',
)
@pass_context
def migrate_credentials(
    ctx: Configuration,
    yes: bool,
    dry_run: bool,
    rollback: bool,
    validate: bool,
):
    """Migrate credentials from base64 storage to secure backends.

    This command migrates your credentials from the legacy base64-encoded
    format in config.yaml to OS-native secure storage backends like
    macOS Keychain or encrypted file storage.

    Security benefits:
    - Credentials stored in OS-native keystores (macOS Keychain, etc.)
    - Industry-standard AES-256-GCM encryption for fallback storage
    - No plaintext credentials in configuration files
    - Protection against casual file access

    The migration process:
    1. Detects existing base64-encoded credentials
    2. Creates a backup of your configuration file
    3. Stores credentials in the secure backend
    4. Removes base64 auth field from config (keeps tokens)
    5. Validates successful migration
    """
    from vss_cli.credentials.base import detect_backend
    from vss_cli.credentials.migration import (
        CredentialMigration, MigrationError, has_legacy_credentials)

    ej_lock = EMOJI_UNICODE.get(':locked:')
    ej_key = EMOJI_UNICODE.get(':key:')
    ej_warn = EMOJI_UNICODE.get(':warning:')

    config_file = Path(ctx.config_path)

    # Check if config file exists
    if not config_file.exists():
        ctx.secho(
            f'{ej_warn} Configuration file not found: {config_file}',
            fg='red',
            err=True,
        )
        ctx.secho(
            'Run "vss-cli configure mk" to create a configuration file.',
            fg='yellow',
            err=True,
        )
        sys.exit(1)

    # Detect available backend
    backend = detect_backend()
    migration = CredentialMigration(
        config_file=config_file, backend=backend, dry_run=dry_run
    )

    # Handle rollback request
    if rollback:
        ctx.secho(
            f'\n{ej_warn} Rolling back credential migration...\n',
            fg='yellow',
            bold=True,
        )

        if not migration.backup_file.exists():
            ctx.secho(
                f'{ej_warn} No backup file found. Cannot rollback.',
                fg='red',
                err=True,
            )
            sys.exit(1)

        if not yes:
            confirm = click.confirm(
                'This will restore your '
                'configuration from backup\n'
                'and delete migrated credentials. Continue?',
                default=False,
            )
            if not confirm:
                ctx.echo('Rollback cancelled.')
                sys.exit(0)

        try:
            migration.rollback()
            ctx.secho(
                f'\n{ej_check} Successfully rolled back migration {ej_tada}',
                fg='green',
            )
            ctx.secho('Configuration restored from backup.', fg='green')
        except MigrationError as e:
            ctx.secho(f'\n{ej_warn} Rollback failed: {e}', fg='red', err=True)
            sys.exit(1)

        sys.exit(0)

    # Handle validation request
    if validate:
        ctx.secho(
            f'\n{ej_key} Validating migrated credentials...\n',
            fg='cyan',
            bold=True,
        )

        result = migration.validate()

        if result['success']:
            ctx.secho(
                f'{ej_check} Validation successful! '
                f'All {result["validated_count"]} credentials verified.',
                fg='green',
            )
        else:
            ctx.secho(
                f'{ej_warn} Validation found issues:', fg='yellow', err=True
            )
            for error in result['errors']:
                ctx.secho(f'  - {error}', fg='red', err=True)
            sys.exit(1)

        sys.exit(0)

    # Get migration status
    status = migration.get_status()

    # Display header
    ctx.secho(
        f'\n{ej_lock} Credential Migration to Secure Storage {ej_lock}\n',
        fg='cyan',
        bold=True,
    )

    # Check if migration is needed
    if not status['has_legacy_credentials']:
        ctx.secho(
            f'{ej_check} No legacy credentials found. '
            f'Your credentials are already secure!',
            fg='green',
        )
        sys.exit(0)

    # Check backend availability
    if not status['backend_available']:
        ctx.secho(
            f'{ej_warn} Secure storage backend is not available.',
            fg='red',
            err=True,
        )
        ctx.secho(
            f'Backend: {backend.__class__.__name__}',
            fg='yellow',
            err=True,
        )
        sys.exit(1)

    # Display migration info
    ctx.secho(f'Configuration file: {status["config_file"]}', fg='white')
    ctx.secho(f'Backend: {backend.__class__.__name__}', fg='white')
    ctx.secho(f'Endpoints to migrate: {status["endpoints_count"]}', fg='white')

    if status['backup_exists']:
        ctx.secho(
            f'\n{ej_warn} Existing backup found: {migration.backup_file}',
            fg='yellow',
        )

    # Dry-run mode
    if dry_run:
        ctx.secho(
            f'\n{ej_key} DRY-RUN MODE - No changes will be made\n',
            fg='yellow',
            bold=True,
        )

        result = migration.migrate()

        ctx.secho('Migration plan:', fg='cyan', bold=True)
        for ep_info in result['endpoints']:
            ctx.secho(f"\n  Endpoint: {ep_info['name']}", fg='white')
            ctx.secho(
                f"  Credentials to migrate: "
                f"{', '.join(ep_info['credentials_to_migrate'])}",
                fg='white',
            )

        ctx.secho(
            f'\n{ej_rkt} Run without --dry-run to perform migration.',
            fg='green',
        )
        sys.exit(0)

    # User education
    ctx.secho('\nWhy migrate?', fg='cyan', bold=True)
    ctx.secho(
        '  - Credentials will be stored in OS-native secure storage',
        fg='white',
    )
    ctx.secho(
        '  - No more plaintext base64-encoded passwords in config files',
        fg='white',
    )
    ctx.secho(
        '  - Protection with AES-256-GCM encryption (encrypted fallback)',
        fg='white',
    )
    ctx.secho('  - Backup will be created automatically', fg='white')

    # Confirmation prompt
    if not yes:
        ctx.secho('\nWhat will happen:', fg='cyan', bold=True)
        ctx.secho(f'  1. Backup created: {config_file}.backup', fg='white')
        ctx.secho(
            f'  2. Credentials stored in: {backend.__class__.__name__}',
            fg='white',
        )
        ctx.secho('  3. Base64 auth field removed from config', fg='white')
        ctx.secho(
            '  4. Tokens preserved in config for quick access', fg='white'
        )

        confirm = click.confirm(
            f'\n{ej_key} Proceed with migration?',
            default=True,
        )

        if not confirm:
            ctx.echo('Migration cancelled.')
            sys.exit(0)

    # Perform migration
    ctx.secho(f'\n{ej_key} Migrating credentials...\n', fg='cyan', bold=True)

    try:
        result = migration.migrate()

        if result['migrated']:
            ctx.secho(
                f'\n{ej_check} Migration successful! {ej_tada}\n',
                fg='green',
                bold=True,
            )
            ctx.secho(
                f'Migrated {len(result["endpoints"])} endpoint(s):',
                fg='green',
            )
            for endpoint in result['endpoints']:
                ctx.secho(f'  - {endpoint}', fg='white')

            ctx.secho(
                f'\nBackup saved to: {migration.backup_file}',
                fg='cyan',
            )
            ctx.secho(
                '\nTo rollback: vss-cli configure '
                'migrate-credentials --rollback',
                fg='yellow',
            )
            ctx.secho(
                'To validate: vss-cli configure '
                'migrate-credentials --validate',
                fg='yellow',
            )

    except MigrationError as e:
        ctx.secho(
            f'\n{ej_warn} Migration failed: {e}',
            fg='red',
            err=True,
        )
        ctx.secho(
            '\nYour configuration has not been modified.',
            fg='yellow',
            err=True,
        )
        sys.exit(1)
