"""Credential backend implementations."""
from vss_cli.credentials.backends.encrypted import (  # noqa: F401
    EncryptedFileBackend)

try:
    from vss_cli.credentials.backends.keychain import (  # noqa: F401
        KeychainBackend)
except ImportError:
    KeychainBackend = None

try:
    from vss_cli.credentials.backends.onepassword import (  # noqa: F401
        OnePasswordBackend)
except ImportError:
    OnePasswordBackend = None

__all__ = ['EncryptedFileBackend', 'KeychainBackend', 'OnePasswordBackend']
