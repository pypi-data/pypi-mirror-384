"""Credential migration from legacy base64 storage to secure backends."""
import logging
import shutil
from base64 import b64decode
from pathlib import Path
from typing import Dict, List, Optional

from ruamel.yaml import YAML

from vss_cli.credentials.base import (
    CredentialBackend, CredentialData, CredentialType)

_LOGGING = logging.getLogger(__name__)


class MigrationError(Exception):
    """Exception raised for migration errors."""

    pass


def parse_legacy_auth(auth: str) -> tuple[str, str]:
    """Parse legacy base64-encoded auth string.

    Args:
        auth: Base64-encoded string in format "username:password"

    Returns:
        Tuple of (username, password)

    Raises:
        ValueError: If auth string is invalid
    """
    try:
        auth_enc = auth.encode()
        credentials_decoded = b64decode(auth_enc)

        # Decode bytes to string and split
        credentials_str = credentials_decoded.decode('utf-8')

        if ':' not in credentials_str:
            raise ValueError('Invalid auth format: missing colon separator')

        username, password = credentials_str.split(':', 1)
        return username, password

    except Exception as e:
        _LOGGING.error(f'Error parsing legacy auth: {e}')
        raise ValueError(f'Invalid auth string: {e}')


def detect_legacy_credentials(
    config_file: Path,
) -> List[Dict[str, Optional[str]]]:
    """Detect legacy base64-encoded credentials in config file.

    Args:
        config_file: Path to configuration file

    Returns:
        List of dictionaries containing endpoint credentials
    """
    legacy_creds = []

    try:
        if not config_file.exists():
            _LOGGING.debug(f'Config file not found: {config_file}')
            return legacy_creds

        yaml = YAML()
        with config_file.open('r') as f:
            config_data = yaml.load(f)

        if not config_data or 'endpoints' not in config_data:
            return legacy_creds

        for endpoint in config_data['endpoints']:
            # Check if endpoint has legacy auth field
            if 'auth' in endpoint and endpoint['auth']:
                try:
                    username, password = parse_legacy_auth(endpoint['auth'])

                    cred_info = {
                        'endpoint': endpoint.get('name'),
                        'url': endpoint.get('url'),
                        'username': username,
                        'password': password,
                        'token': endpoint.get('token'),
                        'totp_secret': endpoint.get('totp_secret'),
                    }

                    legacy_creds.append(cred_info)
                    _LOGGING.debug(
                        f"Found legacy credentials for endpoint: "
                        f"{endpoint.get('name')}"
                    )
                except ValueError as e:
                    _LOGGING.warning(
                        f"Invalid auth format in endpoint "
                        f"{endpoint.get('name')}: {e}"
                    )

    except Exception as e:
        _LOGGING.error(f'Error detecting legacy credentials: {e}')

    return legacy_creds


def has_legacy_credentials(config_file: Path) -> bool:
    """Check if config file has legacy credentials.

    Args:
        config_file: Path to configuration file

    Returns:
        True if legacy credentials exist, False otherwise
    """
    legacy_creds = detect_legacy_credentials(config_file)
    return len(legacy_creds) > 0


class CredentialMigration:
    """Credential migration manager.

    Handles migration of credentials from legacy base64 storage
    to secure credential backends.
    """

    def __init__(
        self,
        config_file: Path,
        backend: CredentialBackend,
        dry_run: bool = False,
    ):
        """Initialize migration manager.

        Args:
            config_file: Path to configuration file
            backend: Credential backend to migrate to
            dry_run: If True, perform dry-run without making changes
        """
        self.config_file = Path(config_file)
        self.backup_file = Path(str(config_file) + '.backup')
        self.backend = backend
        self.dry_run = dry_run
        self._migrated_credentials: List[Dict] = []

        _LOGGING.debug(
            f'Initialized CredentialMigration: '
            f'config={self.config_file}, '
            f'backend={backend.__class__.__name__}, '
            f'dry_run={dry_run}'
        )

    def get_status(self) -> Dict:
        """Get migration status.

        Returns:
            Dictionary with migration status information
        """
        legacy_creds = detect_legacy_credentials(self.config_file)

        status = {
            'has_legacy_credentials': len(legacy_creds) > 0,
            'backend_available': self.backend.is_available(),
            'endpoints_count': len(legacy_creds),
            'backup_exists': self.backup_file.exists(),
            'config_file': str(self.config_file),
        }

        _LOGGING.debug(f'Migration status: {status}')
        return status

    def migrate(self) -> Dict:
        """Migrate credentials from legacy storage to backend.

        Returns:
            Dictionary with migration results

        Raises:
            MigrationError: If migration fails
        """
        # Check backend availability
        if not self.backend.is_available():
            raise MigrationError(
                f'Backend {self.backend.__class__.__name__} is unavailable'
            )

        # Detect legacy credentials
        legacy_creds = detect_legacy_credentials(self.config_file)

        if not legacy_creds:
            _LOGGING.info('No legacy credentials found')
            return {'endpoints': [], 'migrated': False}

        _LOGGING.info(
            f'Found {len(legacy_creds)} endpoints with legacy credentials'
        )

        # Dry-run mode - return migration plan without making changes
        if self.dry_run:
            _LOGGING.info('Dry-run mode: no changes will be made')
            return {
                'endpoints': [
                    {
                        'name': cred['endpoint'],
                        'credentials_to_migrate': [
                            'username',
                            'password',
                            'token',
                        ]
                        + (['totp_secret'] if cred.get('totp_secret') else []),
                    }
                    for cred in legacy_creds
                ],
                'migrated': False,
                'dry_run': True,
            }

        try:
            # Create backup
            self._create_backup()

            # Migrate each endpoint
            for cred_info in legacy_creds:
                self._migrate_endpoint(cred_info)

            # Update config file (remove auth fields)
            self._update_config_file(legacy_creds)

            _LOGGING.info('Migration completed successfully')

            return {
                'endpoints': [
                    cred['endpoint'] for cred in self._migrated_credentials
                ],
                'migrated': True,
            }

        except Exception as e:
            _LOGGING.error(f'Migration failed: {e}')
            raise MigrationError(f'Migration failed: {e}')

    def _create_backup(self) -> None:
        """Create backup of configuration file.

        Raises:
            MigrationError: If backup creation fails
        """
        try:
            # Remove existing backup if corrupted or exists
            if self.backup_file.exists():
                _LOGGING.warning('Removing existing backup file')
                self.backup_file.unlink()

            shutil.copy2(self.config_file, self.backup_file)
            _LOGGING.info(f'Created backup: {self.backup_file}')

        except Exception as e:
            raise MigrationError(f'Failed to create backup: {e}')

    def _migrate_endpoint(self, cred_info: Dict) -> None:
        """Migrate credentials for a single endpoint.

        Args:
            cred_info: Dictionary with credential information

        Raises:
            MigrationError: If migration fails
        """
        endpoint = cred_info['endpoint']
        _LOGGING.info(f'Migrating credentials for endpoint: {endpoint}')

        try:
            # Store username
            if cred_info.get('username'):
                username_cred = CredentialData(
                    credential_type=CredentialType.USERNAME,
                    value=cred_info['username'],
                    endpoint=endpoint,
                )
                self.backend.store_credential(username_cred)

            # Store password
            if cred_info.get('password'):
                password_cred = CredentialData(
                    credential_type=CredentialType.PASSWORD,
                    value=cred_info['password'],
                    endpoint=endpoint,
                )
                self.backend.store_credential(password_cred)

            # Store token
            if cred_info.get('token'):
                token_cred = CredentialData(
                    credential_type=CredentialType.TOKEN,
                    value=cred_info['token'],
                    endpoint=endpoint,
                )
                self.backend.store_credential(token_cred)

            # Store TOTP secret if present
            if cred_info.get('totp_secret'):
                totp_cred = CredentialData(
                    credential_type=CredentialType.MFA_SECRET,
                    value=cred_info['totp_secret'],
                    endpoint=endpoint,
                )
                self.backend.store_credential(totp_cred)

            # Track migrated credentials
            self._migrated_credentials.append(
                {
                    'endpoint': endpoint,
                    'username': cred_info.get('username'),
                    'password': cred_info.get('password'),
                    'token': cred_info.get('token'),
                    'totp_secret': cred_info.get('totp_secret'),
                }
            )

            _LOGGING.info(f'Successfully migrated credentials for: {endpoint}')

        except Exception as e:
            raise MigrationError(f'Failed to migrate endpoint {endpoint}: {e}')

    def _update_config_file(self, legacy_creds: List[Dict]) -> None:
        """Update config file to remove auth fields.

        Args:
            legacy_creds: List of legacy credentials

        Raises:
            MigrationError: If config update fails
        """
        try:
            yaml = YAML()
            with self.config_file.open('r') as f:
                config_data = yaml.load(f)

            # Get list of migrated endpoint names
            migrated_endpoints = {cred['endpoint'] for cred in legacy_creds}

            # Remove auth field from migrated endpoints
            for endpoint in config_data.get('endpoints', []):
                if endpoint.get('name') in migrated_endpoints:
                    if 'auth' in endpoint:
                        del endpoint['auth']
                        _LOGGING.debug(
                            f"Removed auth field from {endpoint.get('name')}"
                        )

            # Write updated config
            with self.config_file.open('w') as f:
                yaml.dump(config_data, f)

            _LOGGING.info('Updated configuration file')

        except Exception as e:
            raise MigrationError(f'Failed to update config file: {e}')

    def rollback(self) -> bool:
        """Rollback migration by restoring backup.

        Returns:
            True if rollback succeeded

        Raises:
            MigrationError: If rollback fails
        """
        try:
            if not self.backup_file.exists():
                raise MigrationError('Backup file not found')

            # Delete migrated credentials from backend
            for cred in self._migrated_credentials:
                endpoint = cred['endpoint']

                try:
                    # Delete each credential type
                    for cred_type in [
                        CredentialType.USERNAME,
                        CredentialType.PASSWORD,
                        CredentialType.TOKEN,
                        CredentialType.MFA_SECRET,
                    ]:
                        self.backend.delete_credential(endpoint, cred_type)

                except Exception as e:
                    _LOGGING.warning(
                        f'Error deleting credential for {endpoint}: {e}'
                    )

            # Restore backup
            shutil.copy2(self.backup_file, self.config_file)
            _LOGGING.info('Restored configuration from backup')

            return True

        except Exception as e:
            raise MigrationError(f'Rollback failed: {e}')

    def validate(self) -> Dict:
        """Validate migration by checking stored credentials.

        Returns:
            Dictionary with validation results
        """
        errors = []
        validated_count = 0

        for cred in self._migrated_credentials:
            endpoint = cred['endpoint']

            # Validate username
            if cred.get('username'):
                try:
                    value = self.backend.retrieve_credential(
                        endpoint, CredentialType.USERNAME
                    )
                    if value is None:
                        errors.append(
                            f'{endpoint}: username not found in backend'
                        )
                    else:
                        validated_count += 1
                except Exception as e:
                    errors.append(f'{endpoint}: username retrieval error: {e}')

            # Validate password
            if cred.get('password'):
                try:
                    value = self.backend.retrieve_credential(
                        endpoint, CredentialType.PASSWORD
                    )
                    if value is None:
                        errors.append(
                            f'{endpoint}: password not found in backend'
                        )
                    else:
                        validated_count += 1
                except Exception as e:
                    errors.append(f'{endpoint}: password retrieval error: {e}')

            # Validate token
            if cred.get('token'):
                try:
                    value = self.backend.retrieve_credential(
                        endpoint, CredentialType.TOKEN
                    )
                    if value is None:
                        errors.append(
                            f'{endpoint}: token not found in backend'
                        )
                    else:
                        validated_count += 1
                except Exception as e:
                    errors.append(f'{endpoint}: token retrieval error: {e}')

        result = {
            'success': len(errors) == 0,
            'validated_count': validated_count,
            'errors': errors,
        }

        _LOGGING.debug(f'Validation result: {result}')
        return result
