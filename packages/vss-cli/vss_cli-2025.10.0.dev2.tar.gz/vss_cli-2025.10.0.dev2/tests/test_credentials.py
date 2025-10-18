"""Tests for credential backend module."""
import unittest
from abc import ABC
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import MagicMock, patch

from vss_cli.credentials.base import (
    CredentialBackend, CredentialCache, CredentialData, CredentialType,
    detect_backend, get_namespace)


class TestCredentialType(unittest.TestCase):
    """Test CredentialType enum."""

    def test_credential_types(self):
        """Test that all credential types are defined."""
        self.assertEqual(CredentialType.USERNAME.value, 'username')
        self.assertEqual(CredentialType.PASSWORD.value, 'password')
        self.assertEqual(CredentialType.TOKEN.value, 'token')
        self.assertEqual(CredentialType.MFA_SECRET.value, 'mfa_secret')
        self.assertEqual(CredentialType.API_KEY.value, 'api_key')


class TestCredentialData(unittest.TestCase):
    """Test CredentialData model."""

    def test_create_credential_data(self):
        """Test creating credential data."""
        cred = CredentialData(
            credential_type=CredentialType.USERNAME,
            value='testuser',
            endpoint='vss-api',
        )
        self.assertEqual(cred.credential_type, CredentialType.USERNAME)
        self.assertEqual(cred.value, 'testuser')
        self.assertEqual(cred.endpoint, 'vss-api')
        self.assertIsNone(cred.metadata)

    def test_credential_data_with_metadata(self):
        """Test credential data with metadata."""
        metadata = {'description': 'Test account'}
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secretpass',
            endpoint='vss-api',
            metadata=metadata,
        )
        self.assertEqual(cred.metadata, metadata)


class TestNamespaceManagement(unittest.TestCase):
    """Test namespace management utilities."""

    def test_get_namespace(self):
        """Test namespace generation."""
        namespace = get_namespace('vss-api')
        self.assertEqual(namespace, 'vss-cli_vss-api')

    def test_get_namespace_with_special_chars(self):
        """Test namespace with special characters."""
        namespace = get_namespace('vss-api.example.com')
        # Should sanitize special characters
        self.assertIn('vss-cli_', namespace)
        self.assertNotIn('/', namespace)

    def test_get_namespace_empty_endpoint(self):
        """Test namespace with empty endpoint."""
        namespace = get_namespace('')
        self.assertEqual(namespace, 'vss-cli_default')


class ConcreteCredentialBackend(CredentialBackend):
    """Concrete implementation for testing."""

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)
        self._storage = {}

    def is_available(self) -> bool:
        """Check if backend is available."""
        return True

    def _store_credential(self, credential: CredentialData) -> bool:
        """Store a credential."""
        key = self._get_storage_key(
            credential.endpoint, credential.credential_type
        )
        self._storage[key] = credential.value
        return True

    def _retrieve_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> Optional[str]:
        """Retrieve a credential."""
        key = self._get_storage_key(endpoint, credential_type)
        return self._storage.get(key)

    def _delete_credential(
        self, endpoint: str, credential_type: CredentialType
    ) -> bool:
        """Delete a credential."""
        key = self._get_storage_key(endpoint, credential_type)
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    def _list_endpoints(self) -> list:
        """List all endpoints with credentials."""
        endpoints = set()
        for key in self._storage.keys():
            # Extract endpoint from key (format: vss-cli_endpoint_type)
            parts = key.split('_')
            if len(parts) >= 2:
                endpoints.add(parts[1])
        return list(endpoints)

    def _get_storage_key(
        self, endpoint: str, credential_type: CredentialType
    ) -> str:
        """Get storage key for credential."""
        namespace = get_namespace(endpoint)
        return f'{namespace}_{credential_type.value}'


class TestCredentialBackend(unittest.TestCase):
    """Test CredentialBackend abstract base class."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = ConcreteCredentialBackend()

    def test_is_abstract(self):
        """Test that CredentialBackend is abstract."""
        self.assertTrue(issubclass(CredentialBackend, ABC))

    def test_store_and_retrieve_credential(self):
        """Test storing and retrieving credentials."""
        cred = CredentialData(
            credential_type=CredentialType.USERNAME,
            value='testuser',
            endpoint='vss-api',
        )
        result = self.backend.store_credential(cred)
        self.assertTrue(result)

        retrieved = self.backend.retrieve_credential(
            'vss-api', CredentialType.USERNAME
        )
        self.assertEqual(retrieved, 'testuser')

    def test_retrieve_nonexistent_credential(self):
        """Test retrieving non-existent credential."""
        retrieved = self.backend.retrieve_credential(
            'nonexistent', CredentialType.USERNAME
        )
        self.assertIsNone(retrieved)

    def test_delete_credential(self):
        """Test deleting credential."""
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred)
        result = self.backend.delete_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertTrue(result)

        # Verify it's deleted
        retrieved = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertIsNone(retrieved)

    def test_delete_nonexistent_credential(self):
        """Test deleting non-existent credential."""
        result = self.backend.delete_credential(
            'nonexistent', CredentialType.USERNAME
        )
        self.assertFalse(result)

    def test_list_endpoints(self):
        """Test listing endpoints."""
        # Store credentials for multiple endpoints
        cred1 = CredentialData(
            credential_type=CredentialType.USERNAME,
            value='user1',
            endpoint='vss-api',
        )
        cred2 = CredentialData(
            credential_type=CredentialType.USERNAME,
            value='user2',
            endpoint='vss-dev',
        )
        self.backend.store_credential(cred1)
        self.backend.store_credential(cred2)

        endpoints = self.backend.list_endpoints()
        self.assertIn('vss-api', endpoints)
        self.assertIn('vss-dev', endpoints)

    def test_update_credential(self):
        """Test updating existing credential."""
        cred1 = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='oldpass',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred1)

        # Update with new value
        cred2 = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='newpass',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred2)

        retrieved = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertEqual(retrieved, 'newpass')


class TestCredentialCache(unittest.TestCase):
    """Test credential caching layer."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a very short TTL for testing
        self.cache = CredentialCache(ttl_seconds=1)

    def test_cache_set_and_get(self):
        """Test setting and getting cached credentials."""
        self.cache.set('vss-api', CredentialType.USERNAME, 'testuser')
        value = self.cache.get('vss-api', CredentialType.USERNAME)
        self.assertEqual(value, 'testuser')

    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        import time

        self.cache.set('vss-api', CredentialType.PASSWORD, 'secret')
        # Wait for cache to expire
        time.sleep(1.1)
        value = self.cache.get('vss-api', CredentialType.PASSWORD)
        self.assertIsNone(value)

    def test_cache_clear(self):
        """Test clearing cache."""
        self.cache.set('vss-api', CredentialType.USERNAME, 'testuser')
        self.cache.set('vss-api', CredentialType.PASSWORD, 'secret')
        self.cache.clear()

        value1 = self.cache.get('vss-api', CredentialType.USERNAME)
        value2 = self.cache.get('vss-api', CredentialType.PASSWORD)
        self.assertIsNone(value1)
        self.assertIsNone(value2)

    def test_cache_delete(self):
        """Test deleting specific cache entry."""
        self.cache.set('vss-api', CredentialType.USERNAME, 'testuser')
        self.cache.set('vss-api', CredentialType.PASSWORD, 'secret')

        self.cache.delete('vss-api', CredentialType.USERNAME)

        value1 = self.cache.get('vss-api', CredentialType.USERNAME)
        value2 = self.cache.get('vss-api', CredentialType.PASSWORD)
        self.assertIsNone(value1)
        self.assertEqual(value2, 'secret')


class TestBackendWithCache(unittest.TestCase):
    """Test backend with caching enabled."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = ConcreteCredentialBackend(enable_cache=True)

    def test_cache_is_used_on_retrieve(self):
        """Test that cache is used when retrieving credentials."""
        cred = CredentialData(
            credential_type=CredentialType.USERNAME,
            value='testuser',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred)

        # First retrieval - should populate cache
        value1 = self.backend.retrieve_credential(
            'vss-api', CredentialType.USERNAME
        )
        self.assertEqual(value1, 'testuser')

        # Clear backend storage but keep cache
        self.backend._storage.clear()

        # Second retrieval - should come from cache
        value2 = self.backend.retrieve_credential(
            'vss-api', CredentialType.USERNAME
        )
        self.assertEqual(value2, 'testuser')

    def test_cache_invalidated_on_store(self):
        """Test that cache is invalidated when storing new credential."""
        cred1 = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='oldpass',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred1)

        # Retrieve to populate cache
        self.backend.retrieve_credential('vss-api', CredentialType.PASSWORD)

        # Update credential
        cred2 = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='newpass',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred2)

        # Should get new value, not cached old value
        value = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertEqual(value, 'newpass')


class TestBackendDetection(unittest.TestCase):
    """Test backend auto-detection logic."""

    @patch('platform.system')
    @patch(
        'vss_cli.credentials.backends.keychain.KeychainBackend.is_available'
    )
    def test_detect_macos_keychain(self, mock_is_available, mock_system):
        """Test detection of macOS Keychain backend."""
        mock_system.return_value = 'Darwin'
        mock_is_available.return_value = True

        backend = detect_backend()
        self.assertIsNotNone(backend)
        # Backend class name should contain 'Keychain'
        self.assertIn('Keychain', backend.__class__.__name__)

    @patch('platform.system')
    @patch(
        'vss_cli.credentials.backends.keychain.KeychainBackend.is_available'
    )
    def test_detect_fallback_when_keychain_unavailable(
        self, mock_is_available, mock_system
    ):
        """Test fallback to encrypted storage when Keychain unavailable."""
        mock_system.return_value = 'Darwin'
        mock_is_available.return_value = False

        backend = detect_backend()
        self.assertIsNotNone(backend)
        # Should fall back to encrypted storage
        self.assertIn('Encrypted', backend.__class__.__name__)

    @patch('platform.system')
    def test_detect_linux_fallback(self, mock_system):
        """Test Linux falls back to encrypted storage."""
        mock_system.return_value = 'Linux'

        backend = detect_backend()
        self.assertIsNotNone(backend)
        # Should use encrypted storage on Linux (not yet implemented)
        self.assertIn('Encrypted', backend.__class__.__name__)


if __name__ == '__main__':
    unittest.main()
