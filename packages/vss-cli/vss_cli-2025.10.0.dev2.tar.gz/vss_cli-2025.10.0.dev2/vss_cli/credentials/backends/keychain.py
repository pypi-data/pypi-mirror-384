"""macOS Keychain credential backend."""
import logging
import re
import subprocess
from typing import List, Optional

from vss_cli.credentials.base import (
    CredentialBackend, CredentialData, CredentialType, get_namespace)

_LOGGING = logging.getLogger(__name__)


class KeychainError(Exception):
    """Base exception for Keychain operations."""

    pass


class KeychainLockedError(KeychainError):
    """Exception raised when Keychain is locked."""

    def __init__(self, message: str = None):
        """Initialize KeychainLockedError."""
        if message is None:
            message = (
                'The Keychain is locked. Please unlock your Keychain '
                'and try again.'
            )
        super().__init__(message)


class KeychainBackend(CredentialBackend):
    """macOS Keychain credential storage backend.

    Uses the macOS Keychain to securely store credentials.
    Credentials are stored using the keyring library which provides
    a cross-platform interface to native credential storage.
    """

    SERVICE_NAME = 'vss-cli'

    def __init__(self, *args, **kwargs):
        """Initialize Keychain backend."""
        super().__init__(*args, **kwargs)
        _LOGGING.debug('Initialized KeychainBackend')

    def is_available(self) -> bool:
        """Check if Keychain is available.

        Returns True on macOS systems with keyring library installed.
        """
        try:
            import platform

            if platform.system() != 'Darwin':
                _LOGGING.debug('Not on macOS, Keychain unavailable')
                return False

            # Try to import keyring
            import keyring

            # Verify we can get a keyring backend
            kr = keyring.get_keyring()
            if kr is None:
                _LOGGING.debug('No keyring backend available')
                return False

            _LOGGING.debug(f'Keychain available: {kr.__class__.__name__}')
            return True
        except ImportError as e:
            _LOGGING.debug(f'Keyring library not available: {e}')
            return False
        except Exception as e:
            _LOGGING.warning(f'Error checking Keychain availability: {e}')
            return False

    def _get_service_name(self) -> str:
        """Get the service name for Keychain entries.

        Returns:
            Service name constant
        """
        return self.SERVICE_NAME

    def _get_account_name(
        self, endpoint: str, credential_type: CredentialType
    ) -> str:
        """Get the account name for Keychain entry.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential

        Returns:
            Account name in format: vss-cli_endpoint_type
        """
        namespace = get_namespace(endpoint)
        return f'{namespace}_{credential_type.value}'

    def _store_credential(self, credential: CredentialData) -> bool:
        """Store credential in Keychain.

        Args:
            credential: Credential data to store

        Returns:
            True if successful

        Raises:
            KeychainLockedError: If Keychain is locked
            KeychainError: For other Keychain errors
        """
        import keyring
        from keyring.errors import KeyringError, KeyringLocked

        try:
            service = self._get_service_name()
            account = self._get_account_name(
                credential.endpoint, credential.credential_type
            )

            _LOGGING.debug(
                f'Storing credential in Keychain: '
                f'service={service}, account={account}'
            )

            keyring.set_password(service, account, credential.value)
            _LOGGING.info(
                f'Successfully stored credential: '
                f'{credential.endpoint}/{credential.credential_type.value}'
            )
            return True

        except KeyringLocked as e:
            _LOGGING.error(f'Keychain is locked: {e}')
            raise KeychainLockedError(str(e))
        except KeyringError as e:
            _LOGGING.error(f'Keychain error storing credential: {e}')
            raise KeychainError(f'Failed to store credential: {e}')
        except Exception as e:
            _LOGGING.error(f'Unexpected error storing credential: {e}')
            raise KeychainError(f'Unexpected error storing credential: {e}')

    def _retrieve_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> Optional[str]:
        """Retrieve credential from Keychain.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential to retrieve

        Returns:
            Credential value or None if not found

        Raises:
            KeychainLockedError: If Keychain is locked
            KeychainError: For other Keychain errors
        """
        import keyring
        from keyring.errors import KeyringError, KeyringLocked

        try:
            service = self._get_service_name()
            account = self._get_account_name(endpoint, credential_type)

            _LOGGING.debug(
                f'Retrieving credential from Keychain: '
                f'service={service}, account={account}'
            )

            value = keyring.get_password(service, account)

            if value:
                _LOGGING.debug(
                    f'Successfully retrieved credential: '
                    f'{endpoint}/{credential_type.value}'
                )
            else:
                _LOGGING.debug(
                    f'Credential not found: '
                    f'{endpoint}/{credential_type.value}'
                )

            return value

        except KeyringLocked as e:
            _LOGGING.error(f'Keychain is locked: {e}')
            raise KeychainLockedError(str(e))
        except KeyringError as e:
            _LOGGING.error(f'Keychain error retrieving credential: {e}')
            raise KeychainError(f'Failed to retrieve credential: {e}')
        except Exception as e:
            _LOGGING.error(f'Unexpected error retrieving credential: {e}')
            raise KeychainError(f'Unexpected error retrieving credential: {e}')

    def _delete_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> bool:
        """Delete credential from Keychain.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential to delete

        Returns:
            True if deleted, False if not found

        Raises:
            KeychainLockedError: If Keychain is locked
            KeychainError: For other Keychain errors
        """
        import keyring
        from keyring.errors import (
            KeyringError, KeyringLocked, PasswordDeleteError)

        try:
            service = self._get_service_name()
            account = self._get_account_name(endpoint, credential_type)

            _LOGGING.debug(
                f'Deleting credential from Keychain: '
                f'service={service}, account={account}'
            )

            keyring.delete_password(service, account)
            _LOGGING.info(
                f'Successfully deleted credential: '
                f'{endpoint}/{credential_type.value}'
            )
            return True

        except PasswordDeleteError as e:
            _LOGGING.debug(
                f'Credential not found for deletion: '
                f'{endpoint}/{credential_type.value}'
            )
            _LOGGING.error(f'Credential not found for deletion: {e}')
            return False
        except KeyringLocked as e:
            _LOGGING.error(f'Keychain is locked: {e}')
            raise KeychainLockedError(str(e))
        except KeyringError as e:
            _LOGGING.error(f'Keychain error deleting credential: {e}')
            raise KeychainError(f'Failed to delete credential: {e}')
        except Exception as e:
            _LOGGING.error(f'Unexpected error deleting credential: {e}')
            raise KeychainError(f'Unexpected error deleting credential: {e}')

    def _list_endpoints(self) -> List[str]:
        """List all endpoints with stored credentials.

        Uses the macOS security command to query Keychain entries.

        Returns:
            List of endpoint names
        """
        endpoints = set()

        try:
            # Use macOS security command to list Keychain items
            # This is more reliable than keyring's API for listing
            result = subprocess.run(
                [
                    'security',
                    'find-generic-password',
                    '-s',
                    self.SERVICE_NAME,
                    '-a',
                    '',
                    '-g',
                ],
                capture_output=True,
                text=False,
            )

            # Parse output to extract account names
            output = result.stdout.decode('utf-8', errors='ignore')

            # Pattern to match account names: vss-cli_endpoint_type
            pattern = r'"acct"<blob>="vss-cli_([^_]+)_'
            matches = re.findall(pattern, output)

            for endpoint in matches:
                endpoints.add(endpoint)

            _LOGGING.debug(f'Found {len(endpoints)} endpoints in Keychain')
            return list(endpoints)

        except FileNotFoundError:
            _LOGGING.warning(
                'security command not found - cannot list endpoints'
            )
            return []
        except Exception as e:
            _LOGGING.warning(f'Error listing Keychain entries: {e}')
            return []
