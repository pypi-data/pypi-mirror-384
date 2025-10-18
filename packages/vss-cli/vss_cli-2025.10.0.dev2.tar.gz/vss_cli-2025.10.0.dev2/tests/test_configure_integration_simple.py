"""Simplified integration tests for configure commands with backend integration."""  # noqa
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from vss_cli.config import Configuration
from vss_cli.credentials.base import CredentialType


class TestConfigureIntegrationSimple(unittest.TestCase):
    """Simplified integration tests for configure ls and mk commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'config.yaml'

        # Standard mocks for JWT handling
        self.mock_token = 'test_token_abc123'
        self.mock_jwt_payload = {'otp': False}

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_mk_then_retrieve_with_keychain_backend(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test mk creates endpoint and credentials are retrievable from backend."""  # noqa
        # Mock JWT and backend
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend that stores and retrieves
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True

        stored_credentials = {}

        def store_side_effect(cred_data):
            key = f"{cred_data.endpoint}:{cred_data.credential_type.value}"
            stored_credentials[key] = cred_data.value

        def retrieve_side_effect(endpoint, cred_type):
            key = f"{endpoint}:{cred_type.value}"
            return stored_credentials.get(key)

        mock_backend.store_credential.side_effect = store_side_effect
        mock_backend.retrieve_credential.side_effect = retrieve_side_effect
        mock_detect_backend.return_value = mock_backend

        # Step 1: Create endpoint with mk
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-api'

        result_mk = ctx.configure(
            username='testuser',
            password='testpass123',
            endpoint='https://cloud.eis.utoronto.ca',
            endpoint_name='vss-api',
        )

        self.assertTrue(result_mk)

        # Verify credentials were stored in backend
        self.assertIn('vss-api:username', stored_credentials)
        self.assertEqual(stored_credentials['vss-api:username'], 'testuser')
        self.assertIn('vss-api:password', stored_credentials)
        self.assertEqual(stored_credentials['vss-api:password'], 'testpass123')

        # Step 2: Retrieve credentials from backend (simulates ls command)
        retrieved_username = mock_backend.retrieve_credential(
            'vss-api', CredentialType.USERNAME
        )
        self.assertEqual(retrieved_username, 'testuser')

        # Verify config file has NO auth field (credentials in backend)
        config = ctx.load_config_file()
        endpoint = config.get_endpoint('vss-api')
        self.assertIsNone(endpoint[0].auth)

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_mixed_environment_backend_and_legacy(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test mixed environment with both backend and legacy credentials."""
        # Mock JWT
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Create config with one legacy endpoint
        config_content = """
general:
  default_endpoint_name: vss-legacy
  output: auto

endpoints:
  - name: vss-legacy
    url: https://cloud-legacy.eis.utoronto.ca
    auth: bGVnYWN5dXNlcjpsZWdhY3lwYXNz
    token: legacy_token_1234567890abcdef1234567890abcdef
    tf_enabled: false
"""
        self.config_file.write_text(config_content)

        # Mock backend
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True

        stored_credentials = {}

        def store_side_effect(cred_data):
            key = f"{cred_data.endpoint}:{cred_data.credential_type.value}"
            stored_credentials[key] = cred_data.value

        def retrieve_side_effect(endpoint, cred_type):
            key = f"{endpoint}:{cred_type.value}"
            return stored_credentials.get(key)

        mock_backend.store_credential.side_effect = store_side_effect
        mock_backend.retrieve_credential.side_effect = retrieve_side_effect
        mock_detect_backend.return_value = mock_backend

        # Add a new endpoint using backend
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud-new.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-new'

        result_mk = ctx.configure(
            username='newuser',
            password='newpass456',
            endpoint='https://cloud-new.eis.utoronto.ca',
            endpoint_name='vss-new',
        )

        self.assertTrue(result_mk)

        # Verify new endpoint stored in backend
        self.assertIn('vss-new:username', stored_credentials)
        self.assertEqual(stored_credentials['vss-new:username'], 'newuser')

        # Verify new endpoint has NO auth field
        config = ctx.load_config_file()
        new_endpoint = config.get_endpoint('vss-new')
        self.assertIsNone(new_endpoint[0].auth)

        # Verify legacy endpoint still has auth field
        legacy_endpoint = config.get_endpoint('vss-legacy')
        self.assertIsNotNone(legacy_endpoint[0].auth)
        self.assertEqual(
            legacy_endpoint[0].auth, 'bGVnYWN5dXNlcjpsZWdhY3lwYXNz'
        )

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_all_three_backend_types(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test all three backend types work correctly."""
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        backend_types = [
            'KeychainBackend',
            'OnePasswordBackend',
            'EncryptedFileBackend',
        ]

        for backend_name in backend_types:
            with self.subTest(backend=backend_name):
                # Clean up for each test
                if self.config_file.exists():
                    self.config_file.unlink()

                # Mock specific backend
                mock_backend = Mock()
                mock_backend.__class__.__name__ = backend_name
                mock_backend.is_available.return_value = True

                stored_creds = {}

                def store(cred_data):
                    key = f"{cred_data.endpoint}:{cred_data.credential_type.value}"  # noqa
                    stored_creds[key] = cred_data.value

                def retrieve(endpoint, cred_type):
                    key = f"{endpoint}:{cred_type.value}"
                    return stored_creds.get(key)

                mock_backend.store_credential.side_effect = store
                mock_backend.retrieve_credential.side_effect = retrieve
                mock_detect_backend.return_value = mock_backend

                # Create endpoint
                ctx = Configuration()
                ctx.config_path = str(self.config_file)
                ctx.endpoint = 'https://cloud.eis.utoronto.ca'
                ctx.endpoint_name = f'vss-{backend_name.lower()}'

                result_mk = ctx.configure(
                    username=f'{backend_name}_user',
                    password='testpass',
                    endpoint='https://cloud.eis.utoronto.ca',
                    endpoint_name=f'vss-{backend_name.lower()}',
                )

                self.assertTrue(result_mk)

                # Verify credentials stored
                self.assertIn(
                    f'vss-{backend_name.lower()}:username', stored_creds
                )
                self.assertEqual(
                    stored_creds[f'vss-{backend_name.lower()}:username'],
                    f'{backend_name}_user',
                )

                # Verify retrievable
                retrieved = mock_backend.retrieve_credential(
                    f'vss-{backend_name.lower()}', CredentialType.USERNAME
                )
                self.assertEqual(retrieved, f'{backend_name}_user')

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_end_to_end_user_workflow(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test complete end-to-end user workflow."""
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True

        stored = {}

        def store(cred_data):
            key = f"{cred_data.endpoint}:{cred_data.credential_type.value}"
            stored[key] = cred_data.value

        def retrieve(endpoint, cred_type):
            key = f"{endpoint}:{cred_type.value}"
            return stored.get(key)

        mock_backend.store_credential.side_effect = store
        mock_backend.retrieve_credential.side_effect = retrieve
        mock_detect_backend.return_value = mock_backend

        # Workflow: User creates multiple endpoints
        endpoints = [
            ('vss-prod', 'produser', 'https://cloud.eis.utoronto.ca'),
            ('vss-dev', 'devuser', 'https://cloud-dev.eis.utoronto.ca'),
            ('vss-test', 'testuser', 'https://cloud-test.eis.utoronto.ca'),
        ]

        for ep_name, username, url in endpoints:
            ctx = Configuration()
            ctx.config_path = str(self.config_file)
            ctx.endpoint = url
            ctx.endpoint_name = ep_name

            result = ctx.configure(
                username=username,
                password='password123',
                endpoint=url,
                endpoint_name=ep_name,
            )

            self.assertTrue(result)

        # Verify all stored in backend
        self.assertEqual(
            len([k for k in stored.keys() if ':username' in k]), 3
        )

        # Verify all retrievable
        for ep_name, username, _ in endpoints:
            retrieved = mock_backend.retrieve_credential(
                ep_name, CredentialType.USERNAME
            )
            self.assertEqual(retrieved, username)

        # Verify no auth fields in config (all in backend)
        config = ctx.load_config_file()
        for ep_name, _, _ in endpoints:
            endpoint = config.get_endpoint(ep_name)
            self.assertIsNone(endpoint[0].auth)

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_backend_unavailable_uses_legacy_fallback(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test backend unavailable falls back to legacy config storage."""
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend that is unavailable
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = False
        mock_detect_backend.return_value = mock_backend

        # Create endpoint when backend unavailable
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-fallback'

        result = ctx.configure(
            username='fallbackuser',
            password='fallbackpass',
            endpoint='https://cloud.eis.utoronto.ca',
            endpoint_name='vss-fallback',
        )

        self.assertTrue(result)

        # Verify config has auth field (legacy fallback)
        config = ctx.load_config_file()
        endpoint = config.get_endpoint('vss-fallback')
        self.assertIsNotNone(endpoint[0].auth)

        # Verify auth field contains base64 encoded credentials
        import base64

        decoded = base64.b64decode(endpoint[0].auth).decode('utf-8')
        self.assertIn('fallbackuser', decoded)


if __name__ == '__main__':
    unittest.main()
