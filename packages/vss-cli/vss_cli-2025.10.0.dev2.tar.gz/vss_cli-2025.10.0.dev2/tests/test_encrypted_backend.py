"""Tests for encrypted file-based credential backend."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vss_cli.credentials.backends.encrypted import (
    EncryptedFileBackend, EncryptionError)
from vss_cli.credentials.base import CredentialData, CredentialType


class TestEncryptedFileBackend(unittest.TestCase):
    """Test EncryptedFileBackend implementation."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test credentials
        self.test_dir = tempfile.mkdtemp()
        self.cred_file = Path(self.test_dir) / 'credentials.enc'
        self.backend = EncryptedFileBackend(
            credential_file=self.cred_file, enable_cache=False
        )

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test directory
        import shutil

        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_is_available(self):
        """Test that encrypted backend is always available."""
        self.assertTrue(self.backend.is_available())

    def test_store_and_retrieve_credential(self):
        """Test storing and retrieving encrypted credentials."""
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='supersecret',
            endpoint='vss-api',
        )
        result = self.backend.store_credential(cred)
        self.assertTrue(result)

        # Verify file was created
        self.assertTrue(self.cred_file.exists())

        # Retrieve credential
        value = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertEqual(value, 'supersecret')

    def test_file_permissions(self):
        """Test that credential file has correct permissions (0600)."""
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred)

        # Check file permissions (owner read/write only)
        stat_info = os.stat(self.cred_file)
        permissions = oct(stat_info.st_mode)[-3:]
        self.assertEqual(permissions, '600')

    def test_encryption_integrity(self):
        """Test that stored data is actually encrypted."""
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='plaintext_password',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred)

        # Read raw file content
        with open(self.cred_file, 'rb') as f:
            raw_content = f.read()

        # Password should NOT appear in plaintext
        self.assertNotIn(b'plaintext_password', raw_content)

    def test_multiple_credentials(self):
        """Test storing multiple credentials for different endpoints."""
        creds = [
            CredentialData(
                credential_type=CredentialType.USERNAME,
                value='user1',
                endpoint='vss-api',
            ),
            CredentialData(
                credential_type=CredentialType.PASSWORD,
                value='pass1',
                endpoint='vss-api',
            ),
            CredentialData(
                credential_type=CredentialType.USERNAME,
                value='user2',
                endpoint='vss-dev',
            ),
        ]

        for cred in creds:
            self.backend.store_credential(cred)

        # Verify all can be retrieved
        self.assertEqual(
            self.backend.retrieve_credential(
                'vss-api', CredentialType.USERNAME
            ),
            'user1',
        )
        self.assertEqual(
            self.backend.retrieve_credential(
                'vss-api', CredentialType.PASSWORD
            ),
            'pass1',
        )
        self.assertEqual(
            self.backend.retrieve_credential(
                'vss-dev', CredentialType.USERNAME
            ),
            'user2',
        )

    def test_delete_credential(self):
        """Test deleting credentials."""
        cred = CredentialData(
            credential_type=CredentialType.TOKEN,
            value='token123',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred)

        # Delete credential
        result = self.backend.delete_credential(
            'vss-api', CredentialType.TOKEN
        )
        self.assertTrue(result)

        # Verify it's deleted
        value = self.backend.retrieve_credential(
            'vss-api', CredentialType.TOKEN
        )
        self.assertIsNone(value)

    def test_delete_nonexistent_credential(self):
        """Test deleting non-existent credential."""
        result = self.backend.delete_credential(
            'nonexistent', CredentialType.PASSWORD
        )
        self.assertFalse(result)

    def test_list_endpoints(self):
        """Test listing endpoints with credentials."""
        creds = [
            CredentialData(
                credential_type=CredentialType.USERNAME,
                value='user1',
                endpoint='vss-api',
            ),
            CredentialData(
                credential_type=CredentialType.USERNAME,
                value='user2',
                endpoint='vss-dev',
            ),
            CredentialData(
                credential_type=CredentialType.USERNAME,
                value='user3',
                endpoint='vss-prod',
            ),
        ]

        for cred in creds:
            self.backend.store_credential(cred)

        endpoints = self.backend.list_endpoints()
        self.assertIn('vss-api', endpoints)
        self.assertIn('vss-dev', endpoints)
        self.assertIn('vss-prod', endpoints)

    def test_update_credential(self):
        """Test updating existing credential."""
        cred1 = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='oldpassword',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred1)

        # Update with new value
        cred2 = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='newpassword',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred2)

        # Verify updated value
        value = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertEqual(value, 'newpassword')

    def test_data_versioning(self):
        """Test that stored data includes version information."""
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred)

        # Read encrypted file and verify version exists
        decrypted_data = self.backend._read_encrypted_file()
        self.assertIn('version', decrypted_data)
        self.assertEqual(decrypted_data['version'], 1)

    def test_hmac_integrity_check(self):
        """Test HMAC integrity verification."""
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )
        self.backend.store_credential(cred)

        # Tamper with the HMAC specifically
        with open(self.cred_file, 'rb') as f:
            data = f.read()

        # Parse JSON and tamper with HMAC
        package = json.loads(data.decode())
        package['hmac'] = 'tampered_hmac_value'

        with open(self.cred_file, 'wb') as f:
            f.write(json.dumps(package).encode())

        # Attempt to read should raise error
        with self.assertRaises(EncryptionError) as context:
            self.backend.retrieve_credential(
                'vss-api', CredentialType.PASSWORD
            )

        self.assertIn('integrity', str(context.exception).lower())

    def test_key_derivation(self):
        """Test that encryption key is properly derived."""
        # Create backend with custom passphrase
        backend_with_pass = EncryptedFileBackend(
            credential_file=self.cred_file,
            passphrase='custom-passphrase',
            enable_cache=False,
        )

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )
        backend_with_pass.store_credential(cred)

        # Try to read with wrong passphrase
        backend_wrong_pass = EncryptedFileBackend(
            credential_file=self.cred_file,
            passphrase='wrong-passphrase',
            enable_cache=False,
        )

        with self.assertRaises(EncryptionError):
            backend_wrong_pass.retrieve_credential(
                'vss-api', CredentialType.PASSWORD
            )

    def test_system_entropy_used(self):
        """Test that system entropy is used in key derivation."""
        # Two backends without passphrase should use system entropy
        backend1 = EncryptedFileBackend(
            credential_file=self.cred_file, enable_cache=False
        )

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )
        backend1.store_credential(cred)

        # New backend instance should be able to read
        backend2 = EncryptedFileBackend(
            credential_file=self.cred_file, enable_cache=False
        )

        value = backend2.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertEqual(value, 'secret')

    def test_empty_credential_file(self):
        """Test handling of empty/missing credential file."""
        # Try to retrieve from non-existent file
        value = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertIsNone(value)

        # List endpoints from empty file
        endpoints = self.backend.list_endpoints()
        self.assertEqual(endpoints, [])

    def test_concurrent_access(self):
        """Test concurrent read/write access without corruption."""
        import threading

        errors = []

        def store_credential(endpoint, value):
            try:
                cred = CredentialData(
                    credential_type=CredentialType.PASSWORD,
                    value=value,
                    endpoint=endpoint,
                )
                self.backend.store_credential(cred)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            t = threading.Thread(
                target=store_credential, args=(f'endpoint-{i}', f'pass-{i}')
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Primary test: no errors or corruption should occur
        self.assertEqual(len(errors), 0, f'Errors occurred: {errors}')

        # Verify file integrity (at least one credential should be readable)
        endpoints = self.backend.list_endpoints()
        self.assertGreater(
            len(endpoints), 0, 'No credentials stored after concurrent writes'
        )

        # Verify we can read at least some credentials without errors
        for endpoint in endpoints:
            value = self.backend.retrieve_credential(
                endpoint, CredentialType.PASSWORD
            )
            self.assertIsNotNone(value, f'Failed to read {endpoint}')


class TestEncryptionSecurity(unittest.TestCase):
    """Test encryption security features."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.cred_file = Path(self.test_dir) / 'credentials.enc'

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_aes_256_encryption(self):
        """Test that AES-256 encryption is used."""
        backend = EncryptedFileBackend(
            credential_file=self.cred_file, enable_cache=False
        )

        # Verify encryption algorithm
        self.assertEqual(backend._get_encryption_algorithm(), 'AES-256-GCM')

    def test_salt_uniqueness(self):
        """Test that each encryption uses unique salt."""
        backend = EncryptedFileBackend(
            credential_file=self.cred_file, enable_cache=False
        )

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )
        backend.store_credential(cred)

        # Read raw encrypted file to get salt
        with open(self.cred_file, 'rb') as f:
            raw_data1 = f.read()

        package1 = json.loads(raw_data1.decode())
        salt1 = package1['data']['salt']

        # Update credential (this will generate a new salt)
        cred2 = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='newsecret',
            endpoint='vss-api',
        )
        backend.store_credential(cred2)

        # Read raw file again
        with open(self.cred_file, 'rb') as f:
            raw_data2 = f.read()

        package2 = json.loads(raw_data2.decode())
        salt2 = package2['data']['salt']

        # Salts should be different
        self.assertNotEqual(salt1, salt2)

    @patch('warnings.warn')
    def test_security_warning_on_init(self, mock_warn):
        """Test that security warning is issued when using fallback storage."""
        backend = EncryptedFileBackend(
            credential_file=self.cred_file, enable_cache=False
        )
        print(backend)
        # Should have warned about using fallback storage
        mock_warn.assert_called()
        warning_msg = mock_warn.call_args[0][0]
        self.assertIn('encrypted file storage', warning_msg.lower())
        self.assertIn('keychain', warning_msg.lower())


if __name__ == '__main__':
    unittest.main()
