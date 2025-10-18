"""Tests for credential migration logic."""
import json
import tempfile
import unittest
from base64 import b64encode
from pathlib import Path
from unittest.mock import MagicMock, patch

from vss_cli.credentials.base import CredentialType
from vss_cli.credentials.migration import (
    CredentialMigration, MigrationError, detect_legacy_credentials,
    has_legacy_credentials)


class TestLegacyCredentialDetection(unittest.TestCase):
    """Test detection of legacy base64 credentials."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = Path(self.test_dir) / 'config.yaml'

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_detect_legacy_credentials_with_auth(self):
        """Test detecting legacy credentials with base64 auth field."""
        # Create config with legacy credentials
        username = 'testuser'
        password = 'testpass'
        credentials = b':'.join([username.encode(), password.encode()])
        auth = b64encode(credentials).strip().decode('utf-8')

        config_data = {
            'general': {'default_endpoint_name': 'vss-api'},
            'endpoints': [
                {
                    'name': 'vss-api',
                    'url': 'https://vss-api.eis.utoronto.ca',
                    'auth': auth,
                    'token': 'some-jwt-token',
                }
            ],
        }

        # Write config file
        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('w') as f:
            yaml.dump(config_data, f)

        # Detect legacy credentials
        legacy_creds = detect_legacy_credentials(self.config_file)

        self.assertEqual(len(legacy_creds), 1)
        self.assertEqual(legacy_creds[0]['endpoint'], 'vss-api')
        self.assertEqual(legacy_creds[0]['username'], username)
        self.assertEqual(legacy_creds[0]['password'], password)
        self.assertEqual(legacy_creds[0]['token'], 'some-jwt-token')

    def test_detect_legacy_credentials_multiple_endpoints(self):
        """Test detecting credentials from multiple endpoints."""
        endpoints = []
        for i in range(3):
            username = f'user{i}'
            password = f'pass{i}'
            credentials = b':'.join([username.encode(), password.encode()])
            auth = b64encode(credentials).strip().decode('utf-8')

            endpoints.append(
                {
                    'name': f'endpoint-{i}',
                    'url': f'https://endpoint-{i}.example.com',
                    'auth': auth,
                    'token': f'token-{i}',
                }
            )

        config_data = {
            'general': {'default_endpoint_name': 'endpoint-0'},
            'endpoints': endpoints,
        }

        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('w') as f:
            yaml.dump(config_data, f)

        legacy_creds = detect_legacy_credentials(self.config_file)

        self.assertEqual(len(legacy_creds), 3)
        for i, cred in enumerate(legacy_creds):
            self.assertEqual(cred['endpoint'], f'endpoint-{i}')
            self.assertEqual(cred['username'], f'user{i}')
            self.assertEqual(cred['password'], f'pass{i}')

    def test_detect_no_legacy_credentials(self):
        """Test detecting config with no legacy credentials."""
        config_data = {
            'general': {'default_endpoint_name': 'vss-api'},
            'endpoints': [
                {
                    'name': 'vss-api',
                    'url': 'https://vss-api.eis.utoronto.ca',
                    'auth': None,
                    'token': None,
                }
            ],
        }

        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('w') as f:
            yaml.dump(config_data, f)

        legacy_creds = detect_legacy_credentials(self.config_file)

        self.assertEqual(len(legacy_creds), 0)

    def test_has_legacy_credentials_returns_true(self):
        """Test has_legacy_credentials returns True when auth exists."""
        username = 'testuser'
        password = 'testpass'
        credentials = b':'.join([username.encode(), password.encode()])
        auth = b64encode(credentials).strip().decode('utf-8')

        config_data = {
            'endpoints': [
                {
                    'name': 'vss-api',
                    'url': 'https://vss-api.eis.utoronto.ca',
                    'auth': auth,
                    'token': 'token',
                }
            ]
        }

        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('w') as f:
            yaml.dump(config_data, f)

        self.assertTrue(has_legacy_credentials(self.config_file))

    def test_has_legacy_credentials_returns_false(self):
        """Test has_legacy_credentials returns False when no auth."""
        config_data = {
            'endpoints': [
                {
                    'name': 'vss-api',
                    'url': 'https://vss-api.eis.utoronto.ca',
                }
            ]
        }

        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('w') as f:
            yaml.dump(config_data, f)

        self.assertFalse(has_legacy_credentials(self.config_file))

    def test_detect_handles_missing_config_file(self):
        """Test detection handles missing config file gracefully."""
        nonexistent_file = Path(self.test_dir) / 'nonexistent.yaml'
        legacy_creds = detect_legacy_credentials(nonexistent_file)
        self.assertEqual(len(legacy_creds), 0)


class TestCredentialMigration(unittest.TestCase):
    """Test credential migration logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = Path(self.test_dir) / 'config.yaml'
        self.backup_file = Path(self.test_dir) / 'config.yaml.backup'

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def _create_legacy_config(self, endpoints_count=1):
        """Create helper to create legacy config file."""
        endpoints = []
        for i in range(endpoints_count):
            username = f'user{i}'
            password = f'pass{i}'
            credentials = b':'.join([username.encode(), password.encode()])
            auth = b64encode(credentials).strip().decode('utf-8')

            endpoints.append(
                {
                    'name': f'endpoint-{i}',
                    'url': f'https://endpoint-{i}.example.com',
                    'auth': auth,
                    'token': f'token-{i}',
                }
            )

        config_data = {
            'general': {'default_endpoint_name': 'endpoint-0'},
            'endpoints': endpoints,
        }

        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('w') as f:
            yaml.dump(config_data, f)

        return config_data

    def test_migration_creates_backup(self):
        """Test that migration creates a backup file."""
        self._create_legacy_config()

        # Create mock backend
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        migration.migrate()

        # Verify backup was created
        self.assertTrue(self.backup_file.exists())

    def test_migration_stores_credentials_in_backend(self):
        """Test that migration stores credentials in backend."""
        self._create_legacy_config(endpoints_count=2)

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        migration.migrate()

        # Should have called store_credential for each endpoint
        # (username, password, token) = 3 calls per endpoint * 2 endpoints
        self.assertEqual(mock_backend.store_credential.call_count, 6)

    def test_migration_removes_auth_from_config(self):
        """Test that migration removes auth field from config."""
        self._create_legacy_config()

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        migration.migrate()

        # Read updated config
        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('r') as f:
            updated_config = yaml.load(f)

        # Verify auth field is removed
        for endpoint in updated_config['endpoints']:
            self.assertNotIn('auth', endpoint)

    def test_migration_preserves_token_field(self):
        """Test that migration preserves token field in config."""
        self._create_legacy_config()

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        migration.migrate()

        # Read updated config
        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('r') as f:
            updated_config = yaml.load(f)

        # Verify token field is preserved
        for endpoint in updated_config['endpoints']:
            self.assertIn('token', endpoint)

    def test_rollback_restores_backup(self):
        """Test that rollback restores the backup file."""
        original_config = self._create_legacy_config()

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        migration.migrate()

        # Perform rollback
        migration.rollback()

        # Verify original config is restored
        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('r') as f:
            restored_config = yaml.load(f)

        self.assertEqual(
            restored_config['endpoints'][0]['auth'],
            original_config['endpoints'][0]['auth'],
        )

    def test_rollback_deletes_migrated_credentials(self):
        """Test that rollback deletes credentials from backend."""
        self._create_legacy_config(endpoints_count=2)

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True
        mock_backend.delete_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        migration.migrate()
        migration.rollback()

        # Should have called delete_credential for each stored credential
        self.assertGreater(mock_backend.delete_credential.call_count, 0)

    def test_migration_error_on_backend_unavailable(self):
        """Test that migration fails when backend is unavailable."""
        self._create_legacy_config()

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = False

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        with self.assertRaises(MigrationError) as context:
            migration.migrate()

        self.assertIn('unavailable', str(context.exception).lower())

    def test_migration_error_on_store_failure(self):
        """Test that migration handles store failures."""
        self._create_legacy_config()

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.side_effect = Exception('Store failed')

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        with self.assertRaises(MigrationError):
            migration.migrate()

    def test_migration_dry_run_mode(self):
        """Test migration in dry-run mode doesn't modify files."""
        original_config = self._create_legacy_config()

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend, dry_run=True
        )

        result = migration.migrate()

        # Verify no backup was created
        self.assertFalse(self.backup_file.exists())

        # Verify config wasn't modified
        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('r') as f:
            current_config = yaml.load(f)

        self.assertEqual(
            current_config['endpoints'][0]['auth'],
            original_config['endpoints'][0]['auth'],
        )

        # Verify dry-run result contains migration plan
        self.assertIn('endpoints', result)
        self.assertGreater(len(result['endpoints']), 0)

    def test_migration_with_totp_secret(self):
        """Test migration handles TOTP secrets if present."""
        username = 'testuser'
        password = 'testpass'
        credentials = b':'.join([username.encode(), password.encode()])
        auth = b64encode(credentials).strip().decode('utf-8')

        config_data = {
            'general': {'default_endpoint_name': 'vss-api'},
            'endpoints': [
                {
                    'name': 'vss-api',
                    'url': 'https://vss-api.eis.utoronto.ca',
                    'auth': auth,
                    'token': 'token',
                    'totp_secret': 'JBSWY3DPEHPK3PXP',
                }
            ],
        }

        from ruamel.yaml import YAML

        yaml = YAML()
        with self.config_file.open('w') as f:
            yaml.dump(config_data, f)

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        migration.migrate()

        # Verify TOTP secret was stored
        calls = mock_backend.store_credential.call_args_list
        totp_calls = [
            call
            for call in calls
            if call[0][0].credential_type == CredentialType.MFA_SECRET
        ]
        self.assertEqual(len(totp_calls), 1)

    def test_migration_status(self):
        """Test getting migration status."""
        self._create_legacy_config()

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        status = migration.get_status()

        self.assertIn('has_legacy_credentials', status)
        self.assertIn('backend_available', status)
        self.assertIn('endpoints_count', status)
        self.assertTrue(status['has_legacy_credentials'])
        self.assertEqual(status['endpoints_count'], 1)

    def test_migration_validation(self):
        """Test migration validation after completion."""
        self._create_legacy_config()

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True
        mock_backend.retrieve_credential.return_value = 'stored_value'

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        migration.migrate()

        # Validate migration
        validation_result = migration.validate()

        self.assertTrue(validation_result['success'])
        self.assertEqual(len(validation_result['errors']), 0)

    def test_migration_handles_corrupted_backup(self):
        """Test migration handles corrupted backup file."""
        self._create_legacy_config()

        # Create corrupted backup
        with self.backup_file.open('w') as f:
            f.write('invalid yaml content {{{')

        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.store_credential.return_value = True

        migration = CredentialMigration(
            config_file=self.config_file, backend=mock_backend
        )

        # Migration should handle corrupted backup
        migration.migrate()

        # New backup should be created
        self.assertTrue(self.backup_file.exists())


class TestMigrationHelpers(unittest.TestCase):
    """Test migration helper functions."""

    def test_parse_legacy_auth_valid(self):
        """Test parsing valid base64 auth string."""
        from vss_cli.credentials.migration import parse_legacy_auth

        username = 'testuser'
        password = 'testpass'
        credentials = b':'.join([username.encode(), password.encode()])
        auth = b64encode(credentials).strip().decode('utf-8')

        parsed_user, parsed_pass = parse_legacy_auth(auth)

        self.assertEqual(parsed_user, username)
        self.assertEqual(parsed_pass, password)

    def test_parse_legacy_auth_invalid(self):
        """Test parsing invalid auth string."""
        from vss_cli.credentials.migration import parse_legacy_auth

        invalid_auth = 'not-base64-content'

        with self.assertRaises(ValueError):
            parse_legacy_auth(invalid_auth)

    def test_parse_legacy_auth_no_separator(self):
        """Test parsing auth string without colon separator."""
        from vss_cli.credentials.migration import parse_legacy_auth

        # Create auth without colon
        invalid_creds = b'usernamepassword'
        auth = b64encode(invalid_creds).strip().decode('utf-8')

        with self.assertRaises(ValueError):
            parse_legacy_auth(auth)


if __name__ == '__main__':
    unittest.main()
