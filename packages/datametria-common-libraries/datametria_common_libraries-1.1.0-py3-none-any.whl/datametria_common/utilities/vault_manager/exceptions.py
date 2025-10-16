"""
DATAMETRIA Vault Manager Exceptions

Custom exceptions for vault operations with detailed error handling.
"""

from typing import Optional, Dict, Any


class VaultException(Exception):
    """Base exception for vault operations."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class VaultSecurityException(VaultException):
    """Exception for security-related vault operations."""
    pass


class VaultSyncException(VaultException):
    """Exception for multi-cloud sync operations."""
    pass


class VaultEncryptionException(VaultSecurityException):
    """Exception for encryption/decryption operations."""
    pass


class VaultAccessException(VaultSecurityException):
    """Exception for access control violations."""
    pass
