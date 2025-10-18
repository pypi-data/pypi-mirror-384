"""Tests for macOS Keychain credential backend."""
import platform
import unittest
from unittest.mock import MagicMock, call, patch

from vss_cli.credentials.backends.keychain import (
    KeychainBackend, KeychainError, KeychainLockedError)
from vss_cli.credentials.base import CredentialData, CredentialType


@unittest.skipUnless(
    platform.system() == 'Darwin', 'Keychain tests only run on macOS'
)
class TestKeychainBackend(unittest.TestCase):
    """Test KeychainBackend implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = KeychainBackend(enable_cache=False)

    @patch('keyring.get_keyring')
    def test_is_available_on_macos(self, mock_get_keyring):
        """Test that backend is available on macOS with keyring."""
        mock_get_keyring.return_value = MagicMock()
        self.assertTrue(self.backend.is_available())

    @patch('keyring.set_password')
    def test_store_credential(self, mock_set_password):
        """Test storing credential in Keychain."""
        cred = CredentialData(
            credential_type=CredentialType.USERNAME,
            value='testuser',
            endpoint='vss-api',
        )
        result = self.backend.store_credential(cred)
        self.assertTrue(result)
        mock_set_password.assert_called_once()

    @patch('keyring.get_password')
    def test_retrieve_credential(self, mock_get_password):
        """Test retrieving credential from Keychain."""
        mock_get_password.return_value = 'testpassword'
        value = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertEqual(value, 'testpassword')
        mock_get_password.assert_called_once()

    @patch('keyring.get_password')
    def test_retrieve_nonexistent_credential(self, mock_get_password):
        """Test retrieving non-existent credential returns None."""
        mock_get_password.return_value = None
        value = self.backend.retrieve_credential(
            'nonexistent', CredentialType.USERNAME
        )
        self.assertIsNone(value)

    @patch('keyring.delete_password')
    def test_delete_credential(self, mock_delete_password):
        """Test deleting credential from Keychain."""
        mock_delete_password.return_value = None
        result = self.backend.delete_credential(
            'vss-api', CredentialType.USERNAME
        )
        self.assertTrue(result)
        mock_delete_password.assert_called_once()

    @patch('keyring.delete_password')
    def test_delete_nonexistent_credential(self, mock_delete_password):
        """Test deleting non-existent credential."""
        from keyring.errors import PasswordDeleteError

        mock_delete_password.side_effect = PasswordDeleteError('Not found')
        result = self.backend.delete_credential(
            'nonexistent', CredentialType.USERNAME
        )
        self.assertFalse(result)

    @patch('keyring.set_password')
    def test_handle_keychain_locked_error(self, mock_set_password):
        """Test handling Keychain locked error."""
        from keyring.errors import KeyringLocked

        mock_set_password.side_effect = KeyringLocked('Keychain is locked')

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )

        with self.assertRaises(KeychainLockedError) as context:
            self.backend.store_credential(cred)

        self.assertIn('locked', str(context.exception).lower())

    @patch('keyring.get_password')
    def test_handle_keychain_error(self, mock_get_password):
        """Test handling generic Keychain errors."""
        from keyring.errors import KeyringError

        mock_get_password.side_effect = KeyringError('Generic error')

        with self.assertRaises(KeychainError) as context:
            self.backend.retrieve_credential(
                'vss-api', CredentialType.PASSWORD
            )

        self.assertIn('error', str(context.exception).lower())

    @patch('keyring.set_password')
    @patch('keyring.get_password')
    def test_store_multiple_credential_types(
        self, mock_get_password, mock_set_password
    ):
        """Test storing multiple credential types for same endpoint."""
        endpoint = 'vss-api'

        # Store username
        cred_user = CredentialData(
            credential_type=CredentialType.USERNAME,
            value='testuser',
            endpoint=endpoint,
        )
        self.backend.store_credential(cred_user)

        # Store password
        cred_pass = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='testpass',
            endpoint=endpoint,
        )
        self.backend.store_credential(cred_pass)

        # Store token
        cred_token = CredentialData(
            credential_type=CredentialType.TOKEN,
            value='testtoken',
            endpoint=endpoint,
        )
        self.backend.store_credential(cred_token)

        # Verify all three were stored
        self.assertEqual(mock_set_password.call_count, 3)

    @patch('subprocess.run')
    def test_list_endpoints_using_security_command(self, mock_run):
        """Test listing endpoints using macOS security command."""
        # Mock security command output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                b'keychain: "/Users/test/Library/Keychains/login.keychain-db"\n'  # noqa
                b'class: "genp"\n'
                b'attributes:\n'
                b'    "acct"<blob>="vss-cli_vss-api_username"\n'
                b'    "svce"<blob>="vss-cli"\n'
                b'---\n'
                b'keychain: "/Users/test/Library/Keychains/login.keychain-db"\n'  # noqa
                b'class: "genp"\n'
                b'attributes:\n'
                b'    "acct"<blob>="vss-cli_vss-dev_password"\n'
                b'    "svce"<blob>="vss-cli"\n'
            ),
        )

        endpoints = self.backend.list_endpoints()
        self.assertIn('vss-api', endpoints)
        self.assertIn('vss-dev', endpoints)

    def test_service_name_generation(self):
        """Test service name generation for Keychain."""
        service_name = self.backend._get_service_name()
        self.assertEqual(service_name, 'vss-cli')

    def test_account_name_generation(self):
        """Test account name generation for Keychain entries."""
        account = self.backend._get_account_name(
            'vss-api', CredentialType.USERNAME
        )
        self.assertEqual(account, 'vss-cli_vss-api_username')

    @patch('keyring.set_password')
    def test_store_with_metadata(self, mock_set_password):
        """Test storing credential with metadata."""
        metadata = {'description': 'Production API credentials'}
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
            metadata=metadata,
        )
        result = self.backend.store_credential(cred)
        self.assertTrue(result)


class TestKeychainBackendErrors(unittest.TestCase):
    """Test Keychain backend error handling."""

    def test_keychain_error_message(self):
        """Test KeychainError exception."""
        error = KeychainError('Test error message')
        self.assertIn('Test error message', str(error))

    def test_keychain_locked_error_message(self):
        """Test KeychainLockedError exception."""
        error = KeychainLockedError()
        self.assertIn('locked', str(error).lower())
        self.assertIn('unlock', str(error).lower())


@unittest.skipIf(
    platform.system() != 'Darwin', 'Keychain integration tests for macOS only'
)
class TestKeychainBackendIntegration(unittest.TestCase):
    """Integration tests for KeychainBackend (requires actual Keychain)."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = KeychainBackend(enable_cache=False)
        self.test_endpoint = 'vss-cli-test'

    def tearDown(self):
        """Clean up test credentials."""
        # Clean up any test credentials
        for cred_type in CredentialType:
            try:
                self.backend.delete_credential(self.test_endpoint, cred_type)
            except Exception:
                pass

    @unittest.skip('Requires user interaction - run manually')
    def test_real_keychain_store_and_retrieve(self):
        """Test actual Keychain storage (requires user authentication)."""
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='test-password-value',
            endpoint=self.test_endpoint,
        )

        # Store
        result = self.backend.store_credential(cred)
        self.assertTrue(result)

        # Retrieve
        value = self.backend.retrieve_credential(
            self.test_endpoint, CredentialType.PASSWORD
        )
        self.assertEqual(value, 'test-password-value')

        # Delete
        deleted = self.backend.delete_credential(
            self.test_endpoint, CredentialType.PASSWORD
        )
        self.assertTrue(deleted)

        # Verify deleted
        value_after_delete = self.backend.retrieve_credential(
            self.test_endpoint, CredentialType.PASSWORD
        )
        self.assertIsNone(value_after_delete)


if __name__ == '__main__':
    unittest.main()
