"""Tests for configure ls command backend integration."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

from vss_cli.config import Configuration
from vss_cli.credentials.base import CredentialType
from vss_cli.plugins.configure import cli


class TestConfigureLsBackendIntegration(unittest.TestCase):
    """Test configure ls command with credential backends."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'config.yaml'

        # Create a sample config with endpoint
        config_content = """
general:
  default_endpoint_name: vss-api
  output: auto

endpoints:
  - name: vss-api
    url: https://cloud.eis.utoronto.ca
    token: test_token_1234567890abcdef1234567890abcdef
    tf_enabled: true
"""
        self.config_file.write_text(config_content)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_retrieves_username_from_keychain_backend(
        self, mock_detect_backend
    ):
        """Test ls retrieves username from KeychainBackend."""
        # Mock backend
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        mock_backend.retrieve_credential.side_effect = lambda ep, ct: (
            'testuser' if ct == CredentialType.USERNAME else None
        )
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('testuser', result.output)
        self.assertIn('KeychainBackend', result.output)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_retrieves_username_from_encrypted_backend(
        self, mock_detect_backend
    ):
        """Test ls retrieves username from EncryptedFileBackend."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'EncryptedFileBackend'
        mock_backend.is_available.return_value = True
        mock_backend.retrieve_credential.side_effect = lambda ep, ct: (
            'admin' if ct == CredentialType.USERNAME else None
        )
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('admin', result.output)
        self.assertIn('EncryptedFileBackend', result.output)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_retrieves_username_from_onepassword_backend(
        self, mock_detect_backend
    ):
        """Test ls retrieves username from OnePasswordBackend."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'OnePasswordBackend'
        mock_backend.is_available.return_value = True
        mock_backend.retrieve_credential.side_effect = lambda ep, ct: (
            'cloudadmin' if ct == CredentialType.USERNAME else None
        )
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('cloudadmin', result.output)
        self.assertIn('OnePasswordBackend', result.output)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_falls_back_to_legacy_base64_auth(self, mock_detect_backend):
        """Test ls falls back to legacy base64 auth when backend returns None."""  # noqa
        # Add legacy auth to config
        config_content = """
general:
  default_endpoint_name: vss-api
  output: auto

endpoints:
  - name: vss-api
    url: https://cloud.eis.utoronto.ca
    auth: bGVnYWN5dXNlcjpsZWdhY3lwYXNz
    token: test_token_1234567890abcdef1234567890abcdef
    tf_enabled: false
"""
        self.config_file.write_text(config_content)

        # Mock backend that returns None (no credentials stored)
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        mock_backend.retrieve_credential.return_value = None
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('legacyuser', result.output)
        self.assertIn('config file (legacy)', result.output)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_handles_backend_unavailable(self, mock_detect_backend):
        """Test ls handles backend unavailable gracefully."""
        # Add legacy auth to config
        config_content = """
general:
  default_endpoint_name: vss-api
  output: auto

endpoints:
  - name: vss-api
    url: https://cloud.eis.utoronto.ca
    auth: YmFja3VwdXNlcjpiYWNrdXBwYXNz
    token: test_token_1234567890abcdef1234567890abcdef
    tf_enabled: true
"""
        self.config_file.write_text(config_content)

        # Mock backend that is unavailable
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = False
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('backupuser', result.output)
        self.assertIn('config file (legacy)', result.output)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_handles_backend_retrieval_exception(self, mock_detect_backend):
        """Test ls handles backend retrieval exceptions gracefully."""
        # Add legacy auth to config
        config_content = """
general:
  default_endpoint_name: vss-api
  output: auto

endpoints:
  - name: vss-api
    url: https://cloud.eis.utoronto.ca
    auth: ZXJyb3J1c2VyOmVycm9ycGFzcw==
    token: test_token_1234567890abcdef1234567890abcdef
    tf_enabled: false
"""
        self.config_file.write_text(config_content)

        # Mock backend that raises exception
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        mock_backend.retrieve_credential.side_effect = Exception(
            'Backend error'
        )
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        # Should not fail, should fall back to legacy
        self.assertEqual(result.exit_code, 0)
        self.assertIn('erroruser', result.output)
        self.assertIn('config file (legacy)', result.output)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_displays_correct_source_labels(self, mock_detect_backend):
        """Test ls displays correct SOURCE column labels."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        mock_backend.retrieve_credential.side_effect = lambda ep, ct: (
            'backenduser' if ct == CredentialType.USERNAME else None
        )
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        self.assertEqual(result.exit_code, 0)
        # Should show backend class name as source
        self.assertIn('SOURCE', result.output)
        self.assertIn('KeychainBackend', result.output)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_mixed_backends_and_legacy(self, mock_detect_backend):
        """Test ls with mixed backends and legacy credentials."""
        # Config with multiple endpoints
        config_content = """
general:
  default_endpoint_name: vss-api
  output: auto

endpoints:
  - name: vss-api
    url: https://cloud.eis.utoronto.ca
    token: test_token_1234567890abcdef1234567890abcdef
    tf_enabled: true
  - name: vss-dev
    url: https://cloud-dev.eis.utoronto.ca
    auth: ZGV2dXNlcjpkZXZwYXNz
    token: dev_token_1234567890abcdef1234567890abcdef
    tf_enabled: false
"""
        self.config_file.write_text(config_content)

        # Mock backend - returns username for vss-api, None for vss-dev
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True

        def retrieve_side_effect(endpoint, cred_type):
            if endpoint == 'vss-api' and cred_type == CredentialType.USERNAME:
                return 'apiuser'
            return None

        mock_backend.retrieve_credential.side_effect = retrieve_side_effect
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        self.assertEqual(result.exit_code, 0)
        # vss-api from backend
        self.assertIn('apiuser', result.output)
        self.assertIn('KeychainBackend', result.output)
        # vss-dev from legacy
        self.assertIn('devuser', result.output)
        self.assertIn('config file (legacy)', result.output)

    @patch('vss_cli.plugins.configure.detect_backend')
    def test_ls_without_credentials(self, mock_detect_backend):
        """Test ls when endpoint has no credentials in backend or config."""
        # Config without auth field
        config_content = """
general:
  default_endpoint_name: vss-api
  output: auto

endpoints:
  - name: vss-api
    url: https://cloud.eis.utoronto.ca
    token: test_token_1234567890abcdef1234567890abcdef
    tf_enabled: false
"""
        self.config_file.write_text(config_content)

        # Mock backend that returns None
        mock_backend = Mock()
        mock_backend.__class__.__name__ = 'KeychainBackend'
        mock_backend.is_available.return_value = True
        mock_backend.retrieve_credential.return_value = None
        mock_detect_backend.return_value = mock_backend

        # Create configuration object and set config_path
        ctx = Configuration()
        ctx.config_path = str(self.config_file)

        result = self.runner.invoke(cli, ['ls'], obj=ctx)

        self.assertEqual(result.exit_code, 0)
        # Should show endpoint even without username
        self.assertIn('vss-api', result.output)


if __name__ == '__main__':
    unittest.main()
