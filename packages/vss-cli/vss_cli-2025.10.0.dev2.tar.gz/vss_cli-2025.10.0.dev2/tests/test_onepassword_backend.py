"""Tests for 1Password credential backend."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

from vss_cli.credentials.backends.onepassword import (
    OnePasswordBackend, OnePasswordCLIError, OnePasswordNotInstalledError,
    OnePasswordNotSignedInError, OnePasswordVaultNotFoundError)
from vss_cli.credentials.base import CredentialData, CredentialType


class TestOnePasswordBackend(unittest.TestCase):
    """Test OnePasswordBackend implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = OnePasswordBackend(enable_cache=False)

    @patch('shutil.which')
    def test_is_available_with_cli(self, mock_which):
        """Test backend availability when op CLI is installed."""
        mock_which.return_value = '/usr/local/bin/op'
        self.assertTrue(self.backend.is_available())
        mock_which.assert_called_with('op')

    @patch('shutil.which')
    def test_is_available_without_cli(self, mock_which):
        """Test backend unavailable when op CLI is missing."""
        mock_which.return_value = None
        self.assertFalse(self.backend.is_available())

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_check_signed_in_success(self, mock_which, mock_run):
        """Test checking sign-in status when signed in."""
        mock_which.return_value = '/usr/local/bin/op'
        mock_run.return_value = Mock(
            returncode=0, stdout='{"user": "test@example.com"}'
        )

        result = self.backend._check_signed_in()
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_check_signed_in_failure(self, mock_which, mock_run):
        """Test checking sign-in status when not signed in."""
        mock_which.return_value = '/usr/local/bin/op'
        mock_run.return_value = Mock(returncode=1, stderr='not signed in')

        result = self.backend._check_signed_in()
        self.assertFalse(result)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_store_credential_basic(self, mock_which, mock_run):
        """Test storing credential in 1Password."""
        mock_which.return_value = '/usr/local/bin/op'

        # Mock call sequence: _get_item (whoami + get fails) t
        # hen _create_item (whoami + create)
        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": ' '"test@example.com"}'
            ),  # whoami in _get_item
            Mock(
                returncode=1, stderr='item not found'
            ),  # item get (not exists)
            Mock(
                returncode=0, stdout='{"user": ' '"test@example.com"}'
            ),  # whoami in _create_item
            Mock(returncode=0, stdout='{"id": "item123"}'),  # item create
        ]

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='supersecret',
            endpoint='vss-api',
        )

        result = self.backend.store_credential(cred)
        self.assertTrue(result)

        # Verify all mocked calls were made
        self.assertEqual(mock_run.call_count, 4)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_retrieve_credential_success(self, mock_which, mock_run):
        """Test retrieving credential from 1Password."""
        mock_which.return_value = '/usr/local/bin/op'

        item_json = {
            'id': 'item123',
            'title': 'vss-cli_vss-api',
            'fields': [
                {
                    'id': 'password',
                    'type': 'CONCEALED',
                    'label': 'password',
                    'value': 'supersecret',
                }
            ],
        }

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami
            Mock(returncode=0, stdout=json.dumps(item_json)),  # item get
        ]

        value = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertEqual(value, 'supersecret')

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_retrieve_credential_not_found(self, mock_which, mock_run):
        """Test retrieving non-existent credential."""
        mock_which.return_value = '/usr/local/bin/op'

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami
            Mock(returncode=1, stderr='item not found'),  # item get
        ]

        value = self.backend.retrieve_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertIsNone(value)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_delete_credential_success(self, mock_which, mock_run):
        """Test deleting credential from 1Password."""
        mock_which.return_value = '/usr/local/bin/op'

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami
            Mock(returncode=0, stdout='{"id": "item123"}'),  # item delete
        ]

        result = self.backend.delete_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertTrue(result)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_delete_credential_not_found(self, mock_which, mock_run):
        """Test deleting non-existent credential."""
        mock_which.return_value = '/usr/local/bin/op'

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami
            Mock(returncode=1, stderr='item not found'),  # item delete
        ]

        result = self.backend.delete_credential(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertFalse(result)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_list_endpoints(self, mock_which, mock_run):
        """Test listing endpoints with stored credentials."""
        mock_which.return_value = '/usr/local/bin/op'

        items_json = [
            {'id': 'item1', 'title': 'vss-cli_vss-api_password'},
            {'id': 'item2', 'title': 'vss-cli_vss-dev_username'},
            {'id': 'item3', 'title': 'other-app_endpoint_token'},
        ]

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami
            Mock(returncode=0, stdout=json.dumps(items_json)),  # item list
        ]

        endpoints = self.backend.list_endpoints()
        self.assertIn('vss-api', endpoints)
        self.assertIn('vss-dev', endpoints)
        self.assertNotIn('endpoint', endpoints)  # Different app prefix

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_custom_vault(self, mock_which, mock_run):
        """Test using custom vault instead of default."""
        mock_which.return_value = '/usr/local/bin/op'
        backend = OnePasswordBackend(vault='work', enable_cache=False)

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _get_item
            Mock(returncode=1, stderr='item not found'),  # item get
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _create_item
            Mock(returncode=0, stdout='{"id": "item123"}'),  # create in vault
        ]

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )

        backend.store_credential(cred)

        # Verify --vault flag was used in item get and create calls
        get_call = mock_run.call_args_list[1]
        self.assertIn('--vault', get_call[0][0])
        self.assertIn('work', get_call[0][0])

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_vault_not_found_error(self, mock_which, mock_run):
        """Test error when vault doesn't exist."""
        mock_which.return_value = '/usr/local/bin/op'
        backend = OnePasswordBackend(vault='nonexistent', enable_cache=False)

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _get_item
            Mock(returncode=1, stderr='item not found'),  # item get
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _create_item
            Mock(returncode=1, stderr='vault not found'),  # create fails
        ]

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )

        with self.assertRaises(OnePasswordVaultNotFoundError):
            backend.store_credential(cred)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_not_signed_in_error(self, mock_which, mock_run):
        """Test error when not signed in to 1Password."""
        mock_which.return_value = '/usr/local/bin/op'

        # whoami check in _get_item will fail
        mock_run.return_value = Mock(returncode=1, stderr='not signed in')

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )

        with self.assertRaises(OnePasswordNotSignedInError):
            self.backend.store_credential(cred)

    @patch('shutil.which')
    def test_not_installed_error(self, mock_which):
        """Test error when op CLI not installed."""
        mock_which.return_value = None

        with self.assertRaises(OnePasswordNotInstalledError):
            self.backend._run_op_command(['whoami'])

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_multiple_credential_types(self, mock_which, mock_run):
        """Test storing multiple credential types for same endpoint."""
        mock_which.return_value = '/usr/local/bin/op'

        # Mock all calls: each store does _get_item (whoami + get)
        # then _create_item (whoami + create)
        mock_run.side_effect = [
            # First credential (username)
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _get_item
            Mock(returncode=1, stderr='item not found'),  # item get
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _create_item
            Mock(returncode=0, stdout='{"id": "item1"}'),  # create
            # Second credential (password)
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _get_item
            Mock(returncode=1, stderr='item not found'),  # item get
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _create_item
            Mock(returncode=0, stdout='{"id": "item2"}'),  # create
            # Third credential (token)
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _get_item
            Mock(returncode=1, stderr='item not found'),  # item get
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _create_item
            Mock(returncode=0, stdout='{"id": "item3"}'),  # create
        ]

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
                credential_type=CredentialType.TOKEN,
                value='token1',
                endpoint='vss-api',
            ),
        ]

        for cred in creds:
            result = self.backend.store_credential(cred)
            self.assertTrue(result)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_item_update_on_duplicate(self, mock_which, mock_run):
        """Test updating existing item when storing duplicate."""
        mock_which.return_value = '/usr/local/bin/op'

        existing_item = {
            'id': 'existing123',
            'title': 'vss-cli_vss-api_password',
        }

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _get_item
            Mock(
                returncode=0, stdout=json.dumps(existing_item)
            ),  # item get (exists)
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _update_item
            Mock(returncode=0, stdout='{"id": "existing123"}'),  # item edit
        ]

        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='newsecret',
            endpoint='vss-api',
        )

        result = self.backend.store_credential(cred)
        self.assertTrue(result)

        # Verify edit was called instead of create
        edit_call = mock_run.call_args_list[3]
        self.assertIn('item', edit_call[0][0])
        self.assertIn('edit', edit_call[0][0])

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_account_detection(self, mock_which, mock_run):
        """Test detection of 1Password account type."""
        mock_which.return_value = '/usr/local/bin/op'

        # Mock account list response
        accounts_json = [
            {
                'url': 'https://my.1password.com',
                'user_uuid': 'USER123',
                'email': 'test@example.com',
            },
            {
                'url': 'https://team.1password.com',
                'user_uuid': 'USER456',
                'email': 'test@team.com',
            },
        ]

        mock_run.return_value = Mock(
            returncode=0, stdout=json.dumps(accounts_json)
        )

        accounts = self.backend._get_accounts()
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0]['email'], 'test@example.com')

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_session_management(self, mock_which, mock_run):
        """Test session token management."""
        mock_which.return_value = '/usr/local/bin/op'

        # Mock signin response
        mock_run.return_value = Mock(
            returncode=0,
            stdout='',
            env={'OP_SESSION_my': 'session_token_123'},
        )

        # Note: Session management is implicit in CLI v2
        # This test verifies the backend handles sessions correctly
        result = self.backend._check_signed_in()
        self.assertTrue(result)


class TestOnePasswordItemStructure(unittest.TestCase):
    """Test 1Password item structure creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = OnePasswordBackend(enable_cache=False)

    def test_build_item_title(self):
        """Test building item title from namespace."""
        title = self.backend._build_item_title(
            'vss-api', CredentialType.PASSWORD
        )
        self.assertEqual(title, 'vss-cli_vss-api_password')

    def test_parse_item_title(self):
        """Test parsing endpoint from item title."""
        endpoint, cred_type = self.backend._parse_item_title(
            'vss-cli_vss-api_password'
        )
        self.assertEqual(endpoint, 'vss-api')
        self.assertEqual(cred_type, CredentialType.PASSWORD)

    def test_build_item_json(self):
        """Test building 1Password item JSON structure."""
        cred = CredentialData(
            credential_type=CredentialType.PASSWORD,
            value='secret',
            endpoint='vss-api',
        )

        item_json = self.backend._build_item_json(cred)

        self.assertEqual(item_json['title'], 'vss-cli_vss-api_password')
        self.assertIn('fields', item_json)
        self.assertEqual(item_json['fields'][0]['value'], 'secret')
        self.assertEqual(item_json['fields'][0]['type'], 'CONCEALED')

    def test_extract_field_value(self):
        """Test extracting field value from item JSON."""
        item = {
            'fields': [
                {'id': 'username', 'value': 'user1'},
                {'id': 'password', 'value': 'pass1', 'type': 'CONCEALED'},
            ]
        }

        value = self.backend._extract_field_value(item, 'password')
        self.assertEqual(value, 'pass1')

    def test_extract_field_value_not_found(self):
        """Test extracting non-existent field returns None."""
        item = {'fields': [{'id': 'username', 'value': 'user1'}]}

        value = self.backend._extract_field_value(item, 'password')
        self.assertIsNone(value)


class TestOnePasswordTeamSupport(unittest.TestCase):
    """Test 1Password team and shared vault features."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = OnePasswordBackend(enable_cache=False)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_shared_vault_access(self, mock_which, mock_run):
        """Test accessing shared team vault."""
        mock_which.return_value = '/usr/local/bin/op'
        backend = OnePasswordBackend(vault='Engineering', enable_cache=False)

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _get_item
            Mock(
                returncode=1, stderr='item not found'
            ),  # item get (not exists)
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami in _create_item
            Mock(returncode=0, stdout='{"id": "item123"}'),  # item create
        ]

        cred = CredentialData(
            credential_type=CredentialType.API_KEY,
            value='api_key_123',
            endpoint='vss-api',
        )

        result = backend.store_credential(cred)
        self.assertTrue(result)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_list_vaults(self, mock_which, mock_run):
        """Test listing available vaults."""
        mock_which.return_value = '/usr/local/bin/op'

        vaults_json = [
            {'id': 'vault1', 'name': 'Private'},
            {'id': 'vault2', 'name': 'Engineering'},
            {'id': 'vault3', 'name': 'DevOps'},
        ]

        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"user": "test@example.com"}'
            ),  # whoami
            Mock(returncode=0, stdout=json.dumps(vaults_json)),  # vault list
        ]

        vaults = self.backend._list_vaults()
        self.assertEqual(len(vaults), 3)
        self.assertIn('Engineering', [v['name'] for v in vaults])


if __name__ == '__main__':
    unittest.main()
