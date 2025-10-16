"""
DATAMETRIA Vault Manager Configuration

Configuration management for vault operations with validation and security.
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from ...core.base_config import BaseConfig


class VaultConfig(BaseConfig):
    """Configuration for DATAMETRIA Vault Manager.
    
    Attributes:
        vault_path: Local vault storage path
        encryption_key: Master encryption key (base64)
        cloud_providers: List of enabled cloud providers
        sync_enabled: Enable multi-cloud synchronization
        backup_enabled: Enable automatic backups
        audit_enabled: Enable audit logging
        compression_enabled: Enable data compression
        max_secret_size: Maximum secret size in bytes
        sync_interval: Sync interval in seconds
        backup_retention: Backup retention in days
    """
    
    def __init__(self, vault_path: Optional[str] = None, encryption_key: Optional[str] = None,
                 cloud_providers: Optional[List[str]] = None, sync_enabled: bool = True,
                 backup_enabled: bool = True, audit_enabled: bool = True,
                 compression_enabled: bool = True, max_secret_size: int = 1024 * 1024,
                 sync_interval: int = 300, backup_retention: int = 30):
        """Initialize Vault configuration."""
        self.vault_path = vault_path or str(Path.home() / '.datametria' / 'vault')
        self.encryption_key = encryption_key
        self.cloud_providers = cloud_providers or ['aws', 'gcp']
        self.sync_enabled = sync_enabled
        self.backup_enabled = backup_enabled
        self.audit_enabled = audit_enabled
        self.compression_enabled = compression_enabled
        self.max_secret_size = max_secret_size
        self.sync_interval = sync_interval
        self.backup_retention = backup_retention
        
        super().__init__()
        self._ensure_vault_directory()
    
    def _validate_specific(self) -> None:
        """Validate configuration parameters.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if self.max_secret_size <= 0:
            raise ValueError("max_secret_size must be positive")
        
        if self.sync_interval < 60:
            raise ValueError("sync_interval must be at least 60 seconds")
        
        if self.backup_retention < 1:
            raise ValueError("backup_retention must be at least 1 day")
        
        valid_providers = {'aws', 'gcp', 'azure', 'local'}
        invalid_providers = set(self.cloud_providers) - valid_providers
        if invalid_providers:
            raise ValueError(f"Invalid cloud providers: {invalid_providers}")
    
    def _ensure_vault_directory(self) -> None:
        """Ensure vault directory exists with proper permissions."""
        vault_dir = Path(self.vault_path)
        vault_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions (owner only)
        if os.name != 'nt':  # Unix-like systems
            vault_dir.chmod(0o700)
    
    @classmethod
    def from_env(cls) -> 'VaultConfig':
        """Create configuration from environment variables.
        
        Returns:
            VaultConfig: Configuration instance
        """
        return cls(
            vault_path=os.getenv('DATAMETRIA_VAULT_PATH', cls().vault_path),
            encryption_key=os.getenv('DATAMETRIA_VAULT_KEY'),
            cloud_providers=os.getenv('DATAMETRIA_VAULT_PROVIDERS', 'aws,gcp').split(','),
            sync_enabled=os.getenv('DATAMETRIA_VAULT_SYNC', 'true').lower() == 'true',
            backup_enabled=os.getenv('DATAMETRIA_VAULT_BACKUP', 'true').lower() == 'true',
            audit_enabled=os.getenv('DATAMETRIA_VAULT_AUDIT', 'true').lower() == 'true'
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            'vault_path': self.vault_path,
            'cloud_providers': self.cloud_providers,
            'sync_enabled': self.sync_enabled,
            'backup_enabled': self.backup_enabled,
            'audit_enabled': self.audit_enabled,
            'compression_enabled': self.compression_enabled,
            'max_secret_size': self.max_secret_size,
            'sync_interval': self.sync_interval,
            'backup_retention': self.backup_retention
        }
