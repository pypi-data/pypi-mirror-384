"""Base credential backend implementation."""
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Tuple

_LOGGING = logging.getLogger(__name__)


class CredentialType(Enum):
    """Credential type enumeration."""

    USERNAME = 'username'
    PASSWORD = 'password'
    TOKEN = 'token'
    MFA_SECRET = 'mfa_secret'
    API_KEY = 'api_key'


@dataclass
class CredentialData:
    """Credential data model.

    Represents a credential with its type, value, and associated metadata.
    """

    credential_type: CredentialType
    value: str
    endpoint: str
    metadata: Optional[Dict[str, str]] = field(default=None)


def get_namespace(endpoint: str) -> str:
    """Generate namespace for credential storage.

    Args:
        endpoint: The endpoint name

    Returns:
        Namespace string in format 'vss-cli_endpoint-name'
    """
    if not endpoint:
        endpoint = 'default'

    # Sanitize endpoint name - remove special characters
    # and replace with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', endpoint)

    return f'vss-cli_{sanitized}'


class CredentialCache:
    """In-memory cache for credentials with TTL support.

    Provides temporary caching of credentials to reduce backend access.
    Cache entries expire after a configurable TTL.
    """

    def __init__(self, ttl_seconds: int = 300):
        """Initialize credential cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
                         (default: 300 = 5 minutes)
        """
        self._cache: Dict[Tuple[str, CredentialType], Tuple[str, float]] = {}
        self._ttl = ttl_seconds
        _LOGGING.debug(f'Initialized credential cache with TTL={ttl_seconds}s')

    def get(
        self, endpoint: str, credential_type: CredentialType
    ) -> Optional[str]:
        """Retrieve credential from cache.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential

        Returns:
            Cached credential value or None if not found or expired
        """
        key = (endpoint, credential_type)
        if key not in self._cache:
            _LOGGING.debug(f'Cache miss: {endpoint}/{credential_type.value}')
            return None

        value, timestamp = self._cache[key]
        # Check if cache entry is expired
        if time.time() - timestamp > self._ttl:
            _LOGGING.debug(
                f'Cache expired: {endpoint}/{credential_type.value}'
            )
            del self._cache[key]
            return None

        _LOGGING.debug(f'Cache hit: {endpoint}/{credential_type.value}')
        return value

    def set(
        self, endpoint: str, credential_type: CredentialType, value: str
    ) -> None:
        """Store credential in cache.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential
            value: Credential value to cache
        """
        key = (endpoint, credential_type)
        self._cache[key] = (value, time.time())
        _LOGGING.debug(
            f'Cached credential: {endpoint}/{credential_type.value}'
        )

    def delete(self, endpoint: str, credential_type: CredentialType) -> None:
        """Delete credential from cache.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential
        """
        key = (endpoint, credential_type)
        if key in self._cache:
            del self._cache[key]
            _LOGGING.debug(
                f'Deleted cache entry: {endpoint}/{credential_type.value}'
            )

    def clear(self) -> None:
        """Clear all cached credentials."""
        self._cache.clear()
        _LOGGING.debug('Cleared credential cache')


class CredentialBackend(ABC):
    """Abstract base class for credential backends.

    Defines the interface that all credential backends must implement.
    Provides common functionality like caching and validation.
    """

    def __init__(self, enable_cache: bool = True, cache_ttl: int = 300):
        """Initialize credential backend.

        Args:
            enable_cache: Enable credential caching (default: True)
            cache_ttl: Cache time-to-live in seconds (default: 300)
        """
        self._enable_cache = enable_cache
        if enable_cache:
            self._cache = CredentialCache(ttl_seconds=cache_ttl)
        else:
            self._cache = None
        _LOGGING.debug(
            f'Initialized {self.__class__.__name__} '
            f'(cache={enable_cache}, ttl={cache_ttl})'
        )

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on the current system.

        Returns:
            True if backend is available, False otherwise
        """
        pass

    @abstractmethod
    def _store_credential(self, credential: CredentialData) -> bool:
        """Store a credential in the backend.

        Implementation-specific method for storing credentials.
        Must be implemented by concrete backend classes.

        Args:
            credential: Credential data to store

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def _retrieve_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> Optional[str]:
        """Retrieve a credential from the backend.

        Implementation-specific method for retrieving credentials.
        Must be implemented by concrete backend classes.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential to retrieve

        Returns:
            Credential value or None if not found
        """
        pass

    @abstractmethod
    def _delete_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> bool:
        """Delete a credential from the backend.

        Implementation-specific method for deleting credentials.
        Must be implemented by concrete backend classes.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def _list_endpoints(self) -> list:
        """List all endpoints with stored credentials.

        Implementation-specific method for listing endpoints.
        Must be implemented by concrete backend classes.

        Returns:
            List of endpoint names
        """
        pass

    def store_credential(self, credential: CredentialData) -> bool:
        """Store a credential (public interface).

        Stores credential and invalidates cache.

        Args:
            credential: Credential data to store

        Returns:
            True if successful, False otherwise
        """
        _LOGGING.info(
            f'Storing credential: '
            f'{credential.endpoint}/{credential.credential_type.value}'
        )

        result = self._store_credential(credential)

        if result and self._cache:
            # Invalidate cache entry
            self._cache.delete(credential.endpoint, credential.credential_type)

        return result

    def retrieve_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> Optional[str]:
        """Retrieve a credential (public interface).

        Checks cache first, then backend storage.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential to retrieve

        Returns:
            Credential value or None if not found
        """
        _LOGGING.debug(
            f'Retrieving credential: {endpoint}/{credential_type.value}'
        )

        # Check cache first
        if self._cache:
            cached_value = self._cache.get(endpoint, credential_type)
            if cached_value is not None:
                return cached_value

        # Retrieve from backend
        value = self._retrieve_credential(endpoint, credential_type)

        # Cache the value
        if value and self._cache:
            self._cache.set(endpoint, credential_type, value)

        return value

    def delete_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> bool:
        """Delete a credential (public interface).

        Deletes from backend and invalidates cache.

        Args:
            endpoint: The endpoint name
            credential_type: Type of credential to delete

        Returns:
            True if deleted, False if not found
        """
        _LOGGING.info(
            f'Deleting credential: {endpoint}/{credential_type.value}'
        )

        result = self._delete_credential(endpoint, credential_type)

        if result and self._cache:
            # Invalidate cache entry
            self._cache.delete(endpoint, credential_type)

        return result

    def list_endpoints(self) -> list:
        """List all endpoints with stored credentials (public interface).

        Returns:
            List of endpoint names
        """
        return self._list_endpoints()


def detect_backend(
    prefer_keychain: bool = True,
    prefer_1password: bool = False,
    enable_cache: bool = True,
) -> CredentialBackend:
    """Auto-detect and return the best available credential backend.

    Detection order:
    1. If prefer_1password: Try 1Password CLI
    2. If prefer_keychain and on macOS: Try Keychain
    3. Fall back to encrypted file storage

    Args:
        prefer_keychain: Prefer macOS Keychain if available
        prefer_1password: Prefer 1Password if available
        enable_cache: Enable credential caching

    Returns:
        Best available credential backend instance
    """
    import platform

    system = platform.system()
    _LOGGING.debug(f'Detecting credential backend for {system}')

    # Try 1Password first if preferred
    if prefer_1password:
        try:
            from vss_cli.credentials.backends.onepassword import (
                OnePasswordBackend)

            backend = OnePasswordBackend(enable_cache=enable_cache)
            if backend.is_available():
                _LOGGING.info('Using 1Password credential backend')
                return backend
        except ImportError:
            _LOGGING.debug('1Password backend not available')

    # Try Keychain on macOS
    if prefer_keychain and system == 'Darwin':
        try:
            from vss_cli.credentials.backends.keychain import KeychainBackend

            backend = KeychainBackend(enable_cache=enable_cache)
            if backend.is_available():
                _LOGGING.info('Using macOS Keychain credential backend')
                return backend
        except ImportError:
            _LOGGING.debug('Keychain backend not available')

    # Fall back to encrypted storage
    _LOGGING.info('Using encrypted file storage credential backend')
    from vss_cli.credentials.backends.encrypted import EncryptedFileBackend

    return EncryptedFileBackend(enable_cache=enable_cache)
