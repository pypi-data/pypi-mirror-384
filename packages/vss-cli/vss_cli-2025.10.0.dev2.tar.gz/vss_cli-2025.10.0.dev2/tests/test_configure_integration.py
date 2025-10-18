"""Integration tests for configure commands with backend integration."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from vss_cli.config import Configuration
from vss_cli.credentials.base import CredentialType
from vss_cli.plugins.configure import cli


class TestConfigureIntegration(unittest.TestCase):
    """Integration tests for configure ls and mk commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
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
    def test_mk_then_ls_with_keychain_backend(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test full workflow: mk creates endpoint, ls displays it from backend."""  # noqa
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

        # Step 2: List endpoints with ls and verify backend retrieval
        with patch('vss_cli.const.DEFAULT_CONFIG', str(self.config_file)):
            ctx_ls = Configuration()
            result_ls = self.runner.invoke(cli, ['ls'], obj=ctx_ls)

            self.assertEqual(result_ls.exit_code, 0)
            # Verify username from backend appears in output
            self.assertIn('testuser', result_ls.output)
            # Verify source shows KeychainBackend
            self.assertIn('KeychainBackend', result_ls.output)

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

        # List endpoints - should show both legacy and backend
        with patch('vss_cli.const.DEFAULT_CONFIG', str(self.config_file)):
            ctx_ls = Configuration()
            result_ls = self.runner.invoke(cli, ['ls'], obj=ctx_ls)

            self.assertEqual(result_ls.exit_code, 0)
            # Legacy endpoint
            self.assertIn('legacyuser', result_ls.output)
            self.assertIn('config file (legacy)', result_ls.output)
            # Backend endpoint
            self.assertIn('newuser', result_ls.output)
            self.assertIn('KeychainBackend', result_ls.output)

    @patch('vss_cli.credentials.base.detect_backend')
    def test_ls_with_environment_variables(self, mock_detect_backend):
        """Test ls displays environment variable credentials correctly."""
        # Mock backend
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        mock_backend.retrieve_credential.return_value = None
        mock_detect_backend.return_value = mock_backend

        # Set environment variables
        env_vars = {
            'VSS_USER': 'envuser',
            'VSS_USER_PASS': 'envpass123',
            'VSS_TOKEN': 'env_token_1234567890abcdef1234567890abcdef',
            'VSS_ENDPOINT': 'https://cloud-env.eis.utoronto.ca',
        }

        with patch.dict(os.environ, env_vars):
            with patch('vss_cli.const.DEFAULT_CONFIG', str(self.config_file)):
                ctx = Configuration()
                result = self.runner.invoke(cli, ['ls'], obj=ctx)

                self.assertEqual(result.exit_code, 0)
                # Verify env credentials appear
                self.assertIn('envuser', result.output)
                self.assertIn('env', result.output)

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

                # List and verify
                with patch(
                    'vss_cli.const.DEFAULT_CONFIG', str(self.config_file)
                ):
                    ctx_ls = Configuration()
                    result_ls = self.runner.invoke(cli, ['ls'], obj=ctx_ls)

                    self.assertEqual(result_ls.exit_code, 0)
                    self.assertIn(f'{backend_name}_user', result_ls.output)
                    self.assertIn(backend_name, result_ls.output)

    @patch('jwt.decode')
    @patch('vss_cli.credentials.base.detect_backend')
    @patch('vss_cli.config.Configuration._get_token_with_mfa')
    def test_backend_unavailable_fallback_workflow(
        self, mock_get_token, mock_detect_backend, mock_jwt_decode
    ):
        """Test workflow when backend becomes unavailable after creation."""
        mock_get_token.return_value = self.mock_token
        mock_jwt_decode.return_value = self.mock_jwt_payload

        # Step 1: Backend available - create endpoint
        mock_backend_available = Mock()
        mock_backend_available.__class__.__name__ = 'KeychainBackend'
        mock_backend_available.is_available.return_value = True
        mock_backend_available.store_credential.return_value = None
        mock_detect_backend.return_value = mock_backend_available

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

        # Verify no auth field (stored in backend)
        config = ctx.load_config_file()
        endpoint = config.get_endpoint('vss-api')
        self.assertIsNone(endpoint[0].auth)

        # Step 2: Backend becomes unavailable - ls should handle gracefully
        mock_backend_unavailable = Mock()
        mock_backend_unavailable.__class__.__name__ = 'KeychainBackend'
        mock_backend_unavailable.is_available.return_value = False
        mock_detect_backend.return_value = mock_backend_unavailable

        with patch('vss_cli.const.DEFAULT_CONFIG', str(self.config_file)):
            ctx_ls = Configuration()
            result_ls = self.runner.invoke(cli, ['ls'], obj=ctx_ls)

            # Should not crash, but username might not display
            self.assertEqual(result_ls.exit_code, 0)
            self.assertIn('vss-api', result_ls.output)

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

        # List all endpoints
        with patch('vss_cli.const.DEFAULT_CONFIG', str(self.config_file)):
            ctx_ls = Configuration()
            result_ls = self.runner.invoke(cli, ['ls'], obj=ctx_ls)

            self.assertEqual(result_ls.exit_code, 0)

            # Verify all endpoints appear
            for ep_name, username, _ in endpoints:
                self.assertIn(username, result_ls.output)
                self.assertIn('KeychainBackend', result_ls.output)

            # Verify no auth fields in config (all in backend)
            config = ctx_ls.load_config_file()
            for ep_name, _, _ in endpoints:
                endpoint = config.get_endpoint(ep_name)
                self.assertIsNone(endpoint[0].auth)


if __name__ == '__main__':
    unittest.main()
