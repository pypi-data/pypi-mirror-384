"""1Password credential backend using CLI integration."""
import json
import logging
import shutil
import subprocess
from typing import Dict, List, Optional

from vss_cli.credentials.base import (
    CredentialBackend, CredentialData, CredentialType)

_LOGGING = logging.getLogger(__name__)


class OnePasswordError(Exception):
    """Base exception for 1Password errors."""

    pass


class OnePasswordNotInstalledError(OnePasswordError):
    """1Password CLI is not installed."""

    pass


class OnePasswordNotSignedInError(OnePasswordError):
    """Not signed in to 1Password."""

    pass


class OnePasswordCLIError(OnePasswordError):
    """1Password CLI command failed."""

    pass


class OnePasswordVaultNotFoundError(OnePasswordError):
    """Vault not found in 1Password."""

    pass


class OnePasswordBackend(CredentialBackend):
    """1Password credential storage backend.

    Uses the 1Password CLI (op) to store and retrieve credentials.
    Supports both personal and team accounts with vault management.
    """

    SERVICE_PREFIX = 'vss-cli'

    def __init__(
        self,
        vault: Optional[str] = None,
        account: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 300,
    ):
        """Initialize 1Password backend.

        Args:
            vault: Vault name to use (default: Primary vault)
            account: Account identifier for team accounts
            enable_cache: Enable credential caching
            cache_ttl: Cache TTL in seconds
        """
        super().__init__(enable_cache=enable_cache, cache_ttl=cache_ttl)
        self.vault = vault
        self.account = account

        _LOGGING.debug(
            f'Initialized OnePasswordBackend: '
            f'vault={vault}, account={account}'
        )

    def is_available(self) -> bool:
        """Check if 1Password CLI is available.

        Returns:
            True if op CLI is installed, False otherwise
        """
        op_path = shutil.which('op')
        available = op_path is not None

        _LOGGING.debug(f'1Password CLI available: {available}')
        return available

    def _check_signed_in(self) -> bool:
        """Check if signed in to 1Password.

        Returns:
            True if signed in, False otherwise
        """
        try:
            result = self._run_op_command(['whoami'], check_signin=False)
            return result.returncode == 0
        except Exception as e:
            _LOGGING.debug(f'Sign-in check failed: {e}')
            return False

    def _run_op_command(
        self,
        args: List[str],
        check_signin: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run 1Password CLI command.

        Args:
            args: Command arguments (without 'op' prefix)
            check_signin: Check if signed in before running
            capture_output: Capture stdout/stderr

        Returns:
            CompletedProcess result

        Raises:
            OnePasswordNotInstalledError: If op CLI not installed
            OnePasswordNotSignedInError: If not signed in
        """
        if not self.is_available():
            raise OnePasswordNotInstalledError(
                '1Password CLI (op) is not installed. '
                'Install from: https://1password.com/downloads/command-line/'
            )

        # Check sign-in status if required
        if check_signin and not self._check_signed_in():
            raise OnePasswordNotSignedInError(
                'Not signed in to 1Password. Run: op signin'
            )

        # Build command
        cmd = ['op'] + args

        # Add account flag if specified
        if self.account:
            cmd.extend(['--account', self.account])

        # Add vault flag if specified and command supports it
        if self.vault and args[0] in ['item']:
            cmd.extend(['--vault', self.vault])

        _LOGGING.debug(f'Running 1Password command: {" ".join(cmd)}')

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                _LOGGING.debug(f'1Password command failed: {result.stderr}')

            return result

        except Exception as e:
            _LOGGING.error(f'Error running 1Password command: {e}')
            raise OnePasswordCLIError(f'Command failed: {e}')

    def _build_item_title(
        self, endpoint: str, credential_type: CredentialType
    ) -> str:
        """Build 1Password item title from endpoint and type.

        Args:
            endpoint: Endpoint name
            credential_type: Type of credential

        Returns:
            Item title in format: vss-cli_endpoint_type
        """
        return f'{self.SERVICE_PREFIX}_{endpoint}_{credential_type.value}'

    def _parse_item_title(self, title: str) -> tuple[str, CredentialType]:
        """Parse endpoint and credential type from item title.

        Args:
            title: Item title

        Returns:
            Tuple of (endpoint, credential_type)

        Raises:
            ValueError: If title format is invalid
        """
        parts = title.split('_')
        if len(parts) < 3 or parts[0] != self.SERVICE_PREFIX:
            raise ValueError(f'Invalid item title format: {title}')

        endpoint = parts[1]
        cred_type_str = parts[2]

        try:
            cred_type = CredentialType(cred_type_str)
        except ValueError:
            raise ValueError(f'Unknown credential type: {cred_type_str}')

        return endpoint, cred_type

    def _build_item_json(self, credential: CredentialData) -> Dict:
        """Build 1Password item JSON structure.

        Args:
            credential: Credential data

        Returns:
            Item JSON structure
        """
        title = self._build_item_title(
            credential.endpoint, credential.credential_type
        )

        # Determine field type based on credential type
        field_type = (
            'CONCEALED'
            if credential.credential_type
            in [
                CredentialType.PASSWORD,
                CredentialType.TOKEN,
                CredentialType.API_KEY,
                CredentialType.MFA_SECRET,
            ]
            else 'STRING'
        )

        item = {
            'title': title,
            'category': 'LOGIN',
            'fields': [
                {
                    'id': credential.credential_type.value,
                    'type': field_type,
                    'label': credential.credential_type.value,
                    'value': credential.value,
                }
            ],
        }

        # Add tags for easier organization
        item['tags'] = ['vss-cli', credential.endpoint]

        return item

    def _extract_field_value(self, item: Dict, field_id: str) -> Optional[str]:
        """Extract field value from 1Password item.

        Args:
            item: Item JSON
            field_id: Field identifier

        Returns:
            Field value or None if not found
        """
        fields = item.get('fields', [])
        for field in fields:
            if field.get('id') == field_id:
                return field.get('value')
        return None

    def _get_item(
        self, endpoint: str, credential_type: CredentialType
    ) -> Optional[Dict]:
        """Get 1Password item by title.

        Args:
            endpoint: Endpoint name
            credential_type: Credential type

        Returns:
            Item JSON or None if not found
        """
        title = self._build_item_title(endpoint, credential_type)

        try:
            result = self._run_op_command(
                ['item', 'get', title, '--format', 'json']
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return None

        except Exception as e:
            _LOGGING.debug(f'Error getting item {title}: {e}')
            return None

    def _create_item(self, credential: CredentialData) -> bool:
        """Create new 1Password item.

        Args:
            credential: Credential data

        Returns:
            True if created successfully
        """
        title = self._build_item_title(
            credential.endpoint, credential.credential_type
        )

        # Determine field type
        field_type = (
            'concealed'
            if credential.credential_type
            in [
                CredentialType.PASSWORD,
                CredentialType.TOKEN,
                CredentialType.API_KEY,
                CredentialType.MFA_SECRET,
            ]
            else 'text'
        )

        # Build create command with field assignment
        field_name = credential.credential_type.value
        cmd_args = [
            'item',
            'create',
            '--category=login',
            f'--title={title}',
            f'{field_name}[{field_type}]={credential.value}',
            f'--tags=vss-cli,{credential.endpoint}',
        ]

        try:
            result = self._run_op_command(cmd_args)

            if result.returncode != 0:
                # Check for vault not found error
                if (
                    'vault' in result.stderr.lower()
                    and 'not found' in result.stderr.lower()
                ):
                    raise OnePasswordVaultNotFoundError(
                        f'Vault not found: {self.vault}'
                    )

                _LOGGING.error(f'Error creating item: {result.stderr}')
                return False

            _LOGGING.debug(f'Created 1Password item: {title}')
            return True

        except (
            OnePasswordVaultNotFoundError,
            OnePasswordNotSignedInError,
            OnePasswordNotInstalledError,
        ):
            raise
        except Exception as e:
            _LOGGING.error(f'Error creating 1Password item: {e}')
            return False

    def _update_item(self, item_id: str, credential: CredentialData) -> bool:
        """Update existing 1Password item.

        Args:
            item_id: Item ID
            credential: New credential data

        Returns:
            True if updated successfully
        """
        field_assignment = (
            f'{credential.credential_type.value}={credential.value}'
        )

        try:
            result = self._run_op_command(
                ['item', 'edit', item_id, field_assignment]
            )

            if result.returncode == 0:
                _LOGGING.debug(f'Updated 1Password item: {item_id}')
                return True
            else:
                _LOGGING.error(f'Error updating item: {result.stderr}')
                return False

        except Exception as e:
            _LOGGING.error(f'Error updating 1Password item: {e}')
            return False

    def _store_credential(self, credential: CredentialData) -> bool:
        """Store credential in 1Password.

        Args:
            credential: Credential to store

        Returns:
            True if stored successfully
        """
        # Check if item already exists
        existing_item = self._get_item(
            credential.endpoint, credential.credential_type
        )

        if existing_item:
            # Update existing item
            return self._update_item(existing_item['id'], credential)
        else:
            # Create new item
            return self._create_item(credential)

    def _retrieve_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> Optional[str]:
        """Retrieve credential from 1Password.

        Args:
            endpoint: Endpoint name
            credential_type: Type of credential

        Returns:
            Credential value or None if not found
        """
        item = self._get_item(endpoint, credential_type)

        if item:
            return self._extract_field_value(item, credential_type.value)

        return None

    def _delete_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> bool:
        """Delete credential from 1Password.

        Args:
            endpoint: Endpoint name
            credential_type: Type of credential

        Returns:
            True if deleted successfully
        """
        title = self._build_item_title(endpoint, credential_type)

        try:
            result = self._run_op_command(['item', 'delete', title])

            if result.returncode == 0:
                _LOGGING.debug(f'Deleted 1Password item: {title}')
                return True
            else:
                _LOGGING.debug(f'Item not found for deletion: {title}')
                return False

        except Exception as e:
            _LOGGING.error(f'Error deleting 1Password item: {e}')
            return False

    def _list_endpoints(self) -> List[str]:
        """List all endpoints with stored credentials.

        Returns:
            List of endpoint names
        """
        try:
            result = self._run_op_command(
                ['item', 'list', '--format', 'json', '--tags', 'vss-cli']
            )

            if result.returncode != 0:
                _LOGGING.debug('No items found')
                return []

            items = json.loads(result.stdout)
            endpoints = set()

            for item in items:
                title = item.get('title', '')
                try:
                    endpoint, _ = self._parse_item_title(title)
                    endpoints.add(endpoint)
                except ValueError:
                    # Skip items with invalid title format
                    continue

            return sorted(list(endpoints))

        except Exception as e:
            _LOGGING.error(f'Error listing endpoints: {e}')
            return []

    def _get_accounts(self) -> List[Dict]:
        """Get list of 1Password accounts.

        Returns:
            List of account dictionaries
        """
        try:
            result = self._run_op_command(
                ['account', 'list', '--format', 'json'], check_signin=False
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return []

        except Exception as e:
            _LOGGING.debug(f'Error listing accounts: {e}')
            return []

    def _list_vaults(self) -> List[Dict]:
        """List available vaults.

        Returns:
            List of vault dictionaries
        """
        try:
            result = self._run_op_command(
                ['vault', 'list', '--format', 'json']
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return []

        except Exception as e:
            _LOGGING.debug(f'Error listing vaults: {e}')
            return []
