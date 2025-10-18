"""Tests for configure mk command backend integration."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from vss_cli.config import Configuration
from vss_cli.credentials.base import CredentialType


class TestConfigureMkBackendIntegration(unittest.TestCase):
    """Test configure mk command with credential backends."""

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
    def test_mk_stores_credentials_in_keychain_backend(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test mk stores credentials in KeychainBackend when available."""
        # Mock JWT token and decode
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        stored_credentials = {}

        def store_side_effect(cred_data):
            key = f"{cred_data.endpoint}:{cred_data.credential_type.value}"
            stored_credentials[key] = cred_data.value

        mock_backend.store_credential.side_effect = store_side_effect
        mock_detect_backend.return_value = mock_backend

        # Create configuration and configure endpoint
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-api'

        result = ctx.configure(
            username='testuser',
            password='testpass123',
            endpoint='https://cloud.eis.utoronto.ca',
            endpoint_name='vss-api',
        )

        # Verify configuration succeeded
        self.assertTrue(result)

        # Verify backend.store_credential was called 3 times
        # (username, password, token)
        self.assertEqual(mock_backend.store_credential.call_count, 3)

        # Verify credentials were stored
        self.assertIn('vss-api:username', stored_credentials)
        self.assertIn('vss-api:password', stored_credentials)
        self.assertIn('vss-api:token', stored_credentials)
        self.assertEqual(stored_credentials['vss-api:username'], 'testuser')
        self.assertEqual(stored_credentials['vss-api:password'], 'testpass123')

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_mk_config_no_auth_field_when_backend_available(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test mk creates config without auth field when backend available."""
        # Mock JWT token and decode
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = None
        mock_detect_backend.return_value = mock_backend

        # Create configuration
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-api'

        result = ctx.configure(
            username='testuser',
            password='testpass123',
            endpoint='https://cloud.eis.utoronto.ca',
            endpoint_name='vss-api',
        )

        # Verify configuration succeeded
        self.assertTrue(result)

        # Load config file and verify no auth field
        config_file = ctx.load_config_file()
        endpoint = config_file.get_endpoint('vss-api')

        self.assertIsNotNone(endpoint)
        self.assertEqual(endpoint[0].name, 'vss-api')
        # Verify NO auth field in config (stored in backend instead)
        self.assertIsNone(endpoint[0].auth)

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_mk_config_has_auth_field_when_backend_unavailable(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test mk creates config with auth field when backend unavailable."""
        # Mock JWT token and decode
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend that is unavailable
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = False
        mock_detect_backend.return_value = mock_backend

        # Create configuration
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-api'

        result = ctx.configure(
            username='testuser',
            password='testpass123',
            endpoint='https://cloud.eis.utoronto.ca',
            endpoint_name='vss-api',
        )

        # Verify configuration succeeded
        self.assertTrue(result)

        # Load config file and verify auth field exists
        config_file = ctx.load_config_file()
        endpoint = config_file.get_endpoint('vss-api')

        self.assertIsNotNone(endpoint)
        self.assertEqual(endpoint[0].name, 'vss-api')
        # Verify auth field exists (legacy fallback)
        self.assertIsNotNone(endpoint[0].auth)

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_mk_handles_backend_storage_exception(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test mk falls back to legacy auth when backend storage fails."""
        # Mock JWT token and decode
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend that throws exception
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.side_effect = Exception(
            'Backend storage error'
        )
        mock_detect_backend.return_value = mock_backend

        # Create configuration
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-api'

        result = ctx.configure(
            username='testuser',
            password='testpass123',
            endpoint='https://cloud.eis.utoronto.ca',
            endpoint_name='vss-api',
        )

        # Verify configuration still succeeded (fell back to legacy)
        self.assertTrue(result)

        # Load config file and verify auth field exists (fallback)
        config_file = ctx.load_config_file()
        endpoint = config_file.get_endpoint('vss-api')

        self.assertIsNotNone(endpoint)
        # Verify auth field exists (fallback to legacy)
        self.assertIsNotNone(endpoint[0].auth)

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_mk_stores_in_encrypted_backend(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test mk stores credentials in EncryptedFileBackend."""
        # Mock JWT token and decode
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'EncryptedFileBackend'
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = None
        mock_detect_backend.return_value = mock_backend

        # Create configuration
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-dev'

        result = ctx.configure(
            username='devuser',
            password='devpass456',
            endpoint='https://cloud.eis.utoronto.ca',
            endpoint_name='vss-dev',
        )

        # Verify configuration succeeded
        self.assertTrue(result)

        # Verify backend.store_credential was called
        self.assertGreater(mock_backend.store_credential.call_count, 0)

        # Load config and verify no auth field
        config_file = ctx.load_config_file()
        endpoint = config_file.get_endpoint('vss-dev')
        self.assertIsNone(endpoint[0].auth)

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_mk_stores_in_onepassword_backend(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test mk stores credentials in OnePasswordBackend."""
        # Mock JWT token and decode
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Mock backend
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'OnePasswordBackend'
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = None
        mock_detect_backend.return_value = mock_backend

        # Create configuration
        ctx = Configuration()
        ctx.config_path = str(self.config_file)
        ctx.endpoint = 'https://cloud.eis.utoronto.ca'
        ctx.endpoint_name = 'vss-prod'

        result = ctx.configure(
            username='produser',
            password='prodpass789',
            endpoint='https://cloud.eis.utoronto.ca',
            endpoint_name='vss-prod',
        )

        # Verify configuration succeeded
        self.assertTrue(result)

        # Verify backend.store_credential was called
        self.assertGreater(mock_backend.store_credential.call_count, 0)

        # Load config and verify no auth field
        config_file = ctx.load_config_file()
        endpoint = config_file.get_endpoint('vss-prod')
        self.assertIsNone(endpoint[0].auth)


if __name__ == '__main__':
    unittest.main()
