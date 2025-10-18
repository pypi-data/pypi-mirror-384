"""Encrypted file-based credential backend (fallback)."""
import hashlib
import hmac
import json
import logging
import os
import threading
import warnings
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from vss_cli.credentials.base import (
    CredentialBackend, CredentialData, CredentialType, get_namespace)

_LOGGING = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Exception raised for encryption/decryption errors."""

    pass


class EncryptedFileBackend(CredentialBackend):
    """Encrypted file-based credential storage (fallback).

    This backend stores credentials in an encrypted file when
    OS-native keystores are not available. Uses AES-256-GCM
    encryption with PBKDF2 key derivation.

    Security features:
    - AES-256-GCM authenticated encryption
    - PBKDF2-HMAC-SHA256 key derivation (600,000 iterations)
    - Unique salt per encryption operation
    - HMAC integrity verification
    - File permissions restricted to 0600 (owner read/write only)
    - Versioning for future compatibility
    """

    VERSION = 1
    ENCRYPTION_ALGORITHM = 'AES-256-GCM'
    KDF_ITERATIONS = 600000  # OWASP recommendation for PBKDF2-SHA256
    SALT_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits (GCM standard)
    KEY_SIZE = 32  # 256 bits

    def __init__(
        self,
        credential_file: Optional[Path] = None,
        passphrase: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize encrypted file backend.

        Args:
            credential_file: Path to encrypted credential file
                            (default: ~/.vss-cli/credentials.enc)
            passphrase: Optional custom passphrase for encryption.
                       If not provided, system entropy is used.
        """
        super().__init__(*args, **kwargs)

        # Default credential file location
        if credential_file is None:
            config_dir = Path.home() / '.vss-cli'
            config_dir.mkdir(exist_ok=True, mode=0o700)
            credential_file = config_dir / 'credentials.enc'

        self._credential_file = Path(credential_file)
        self._passphrase = passphrase
        self._file_lock = threading.Lock()

        # Issue security warning
        warnings.warn(
            'Using encrypted file storage for credentials. '
            'For better security, consider using your system\'s '
            'native keystore (macOS Keychain, 1Password, etc.)',
            UserWarning,
            stacklevel=2,
        )

        _LOGGING.debug(
            f'Initialized EncryptedFileBackend: {self._credential_file}'
        )

    def is_available(self) -> bool:
        """Check if encrypted file backend is available.

        Always returns True as this is the fallback backend.
        """
        return True

    def _get_encryption_algorithm(self) -> str:
        """Get encryption algorithm name.

        Returns:
            Encryption algorithm identifier
        """
        return self.ENCRYPTION_ALGORITHM

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from passphrase and salt.

        Uses PBKDF2-HMAC-SHA256 with high iteration count.

        Args:
            salt: Cryptographic salt

        Returns:
            Derived encryption key
        """
        # Use passphrase or system entropy
        if self._passphrase:
            password = self._passphrase.encode()
        else:
            # Use machine-specific entropy
            password = self._get_system_entropy()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.KDF_ITERATIONS,
            backend=default_backend(),
        )

        key = kdf.derive(password)
        return key

    def _get_system_entropy(self) -> bytes:
        """Get system-specific entropy for key derivation.

        Combines multiple sources of machine-specific data.

        Returns:
            System entropy bytes
        """
        import platform
        import socket

        # Combine multiple sources of system-specific data
        entropy_sources = [
            platform.node(),  # Hostname
            str(Path.home()),  # Home directory
            socket.gethostname(),  # Network hostname
        ]

        entropy_str = '|'.join(entropy_sources)
        entropy_hash = hashlib.sha256(entropy_str.encode()).digest()
        return entropy_hash

    def _encrypt_data(self, data: Dict) -> bytes:
        """Encrypt credential data.

        Args:
            data: Data dictionary to encrypt

        Returns:
            Encrypted data bytes

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Generate unique salt and nonce
            salt = os.urandom(self.SALT_SIZE)
            nonce = os.urandom(self.NONCE_SIZE)

            # Derive encryption key
            key = self._derive_key(salt)

            # Serialize data
            plaintext = json.dumps(data).encode()

            # Encrypt with AES-256-GCM
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            # Create encrypted package
            package = {
                'version': self.VERSION,
                'algorithm': self.ENCRYPTION_ALGORITHM,
                'salt': salt.hex(),
                'nonce': nonce.hex(),
                'ciphertext': ciphertext.hex(),
            }

            # Add HMAC for additional integrity check
            package_bytes = json.dumps(package).encode()
            hmac_key = self._derive_key(salt + b'_hmac')
            package_hmac = hmac.new(
                hmac_key, package_bytes, hashlib.sha256
            ).hexdigest()

            final_package = {
                'hmac': package_hmac,
                'data': package,
            }

            return json.dumps(final_package).encode()

        except Exception as e:
            _LOGGING.error(f'Encryption error: {e}')
            raise EncryptionError(f'Failed to encrypt data: {e}')

    def _decrypt_data(self, encrypted_bytes: bytes) -> Dict:
        """Decrypt credential data.

        Args:
            encrypted_bytes: Encrypted data bytes

        Returns:
            Decrypted data dictionary

        Raises:
            EncryptionError: If decryption or integrity check fails
        """
        try:
            # Parse encrypted package
            final_package = json.loads(encrypted_bytes.decode())
            stored_hmac = final_package['hmac']
            package = final_package['data']

            # Verify HMAC integrity
            salt = bytes.fromhex(package['salt'])
            hmac_key = self._derive_key(salt + b'_hmac')
            package_bytes = json.dumps(package).encode()
            computed_hmac = hmac.new(
                hmac_key, package_bytes, hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(stored_hmac, computed_hmac):
                raise EncryptionError(
                    'HMAC integrity check failed - data may be corrupted '
                    'or tampered with'
                )

            # Extract encryption parameters
            nonce = bytes.fromhex(package['nonce'])
            ciphertext = bytes.fromhex(package['ciphertext'])

            # Derive decryption key
            key = self._derive_key(salt)

            # Decrypt with AES-256-GCM
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            # Deserialize data
            data = json.loads(plaintext.decode())
            return data

        except EncryptionError:
            raise
        except Exception as e:
            _LOGGING.error(f'Decryption error: {e}')
            raise EncryptionError(f'Failed to decrypt data: {e}')

    def _read_encrypted_file(self) -> Dict:
        """Read and decrypt credential file.

        Returns:
            Decrypted data dictionary

        Raises:
            EncryptionError: If file read or decryption fails
        """
        with self._file_lock:
            if not self._credential_file.exists():
                return {'version': self.VERSION, 'credentials': {}}

            try:
                with open(self._credential_file, 'rb') as f:
                    encrypted_data = f.read()

                if not encrypted_data:
                    return {'version': self.VERSION, 'credentials': {}}

                return self._decrypt_data(encrypted_data)

            except Exception as e:
                _LOGGING.error(f'Error reading credential file: {e}')
                raise EncryptionError(f'Failed to read credential file: {e}')

    def _write_encrypted_file(self, data: Dict) -> None:
        """Encrypt and write credential file.

        Args:
            data: Data dictionary to encrypt and write

        Raises:
            EncryptionError: If encryption or file write fails
        """
        with self._file_lock:
            try:
                # Encrypt data
                encrypted_bytes = self._encrypt_data(data)

                # Write to file
                with open(self._credential_file, 'wb') as f:
                    f.write(encrypted_bytes)

                # Set file permissions to 0600 (owner read/write only)
                os.chmod(self._credential_file, 0o600)

                _LOGGING.debug(
                    f'Credential file written: {self._credential_file}'
                )

            except Exception as e:
                _LOGGING.error(f'Error writing credential file: {e}')
                raise EncryptionError(f'Failed to write credential file: {e}')

    def _get_credential_key(
        self, endpoint: str, credential_type: CredentialType
    ) -> str:
        """Get storage key for credential.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential

        Returns:
            Storage key
        """
        namespace = get_namespace(endpoint)
        return f'{namespace}_{credential_type.value}'

    def _store_credential(self, credential: CredentialData) -> bool:
        """Store credential in encrypted file.

        Args:
            credential: Credential data to store

        Returns:
            True if successful

        Raises:
            EncryptionError: If storage fails
        """
        try:
            # Read existing data
            data = self._read_encrypted_file()

            # Update credentials
            key = self._get_credential_key(
                credential.endpoint, credential.credential_type
            )
            data['credentials'][key] = {
                'value': credential.value,
                'type': credential.credential_type.value,
                'endpoint': credential.endpoint,
                'metadata': credential.metadata,
            }

            # Write updated data
            self._write_encrypted_file(data)

            _LOGGING.info(
                f'Stored credential: '
                f'{credential.endpoint}/{credential.credential_type.value}'
            )
            return True

        except Exception as e:
            _LOGGING.error(f'Failed to store credential: {e}')
            raise EncryptionError(f'Failed to store credential: {e}')

    def _retrieve_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> Optional[str]:
        """Retrieve credential from encrypted file.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential to retrieve

        Returns:
            Credential value or None if not found

        Raises:
            EncryptionError: If retrieval fails
        """
        try:
            # Read data
            data = self._read_encrypted_file()

            # Get credential
            key = self._get_credential_key(endpoint, credential_type)
            cred_data = data['credentials'].get(key)

            if cred_data:
                _LOGGING.debug(
                    f'Retrieved credential: {endpoint}/{credential_type.value}'
                )
                return cred_data['value']

            return None

        except Exception as e:
            _LOGGING.error(f'Failed to retrieve credential: {e}')
            raise EncryptionError(f'Failed to retrieve credential: {e}')

    def _delete_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> bool:
        """Delete credential from encrypted file.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential to delete

        Returns:
            True if deleted, False if not found

        Raises:
            EncryptionError: If deletion fails
        """
        try:
            # Read existing data
            data = self._read_encrypted_file()

            # Delete credential
            key = self._get_credential_key(endpoint, credential_type)
            if key in data['credentials']:
                del data['credentials'][key]

                # Write updated data
                self._write_encrypted_file(data)

                _LOGGING.info(
                    f'Deleted credential: {endpoint}/{credential_type.value}'
                )
                return True

            return False

        except Exception as e:
            _LOGGING.error(f'Failed to delete credential: {e}')
            raise EncryptionError(f'Failed to delete credential: {e}')

    def _list_endpoints(self) -> List[str]:
        """List all endpoints with stored credentials.

        Returns:
            List of endpoint names

        Raises:
            EncryptionError: If listing fails
        """
        try:
            # Read data
            data = self._read_encrypted_file()

            # Extract unique endpoints
            endpoints = set()
            for cred_data in data['credentials'].values():
                endpoints.add(cred_data['endpoint'])

            _LOGGING.debug(f'Found {len(endpoints)} endpoints')
            return list(endpoints)

        except Exception as e:
            _LOGGING.error(f'Failed to list endpoints: {e}')
            raise EncryptionError(f'Failed to list endpoints: {e}')
