"""
DATAMETRIA Vault Manager - Secure Secret Management

Enterprise-grade secret management with AES-256 encryption, multi-cloud sync,
and LGPD/GDPR compliance.
"""

from .vault_manager import VaultManager
from .config import VaultConfig
from .exceptions import VaultException, VaultSecurityException, VaultSyncException

__all__ = [
    'VaultManager',
    'VaultConfig', 
    'VaultException',
    'VaultSecurityException',
    'VaultSyncException'
]

__version__ = '1.0.0'
