"""
DATAMETRIA BaseConfig - Universal Configuration Pattern

Universal configuration pattern with validation, environment support,
and SecurityManager integration for all DATAMETRIA components.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""
    pass


@dataclass
class BaseConfig(ABC):
    """Universal base configuration for all DATAMETRIA components.
    
    Provides standardized configuration pattern with:
    - Environment variable support
    - Automatic validation
    - SecurityManager integration
    - Consistent defaults
    
    Example:
        >>> class MyConfig(BaseConfig):
        ...     service_name: str = "my-service"
        ...     
        ...     def _validate_specific(self):
        ...         if not self.service_name:
        ...             raise ConfigValidationError("service_name required")
        >>> 
        >>> config = MyConfig()
        >>> config.validate()
    """
    
    # Common configuration fields
    environment: str = field(default_factory=lambda: os.getenv('DATAMETRIA_ENV', 'production'))
    debug: bool = field(default_factory=lambda: os.getenv('DATAMETRIA_DEBUG', 'false').lower() == 'true')
    log_level: str = field(default_factory=lambda: os.getenv('DATAMETRIA_LOG_LEVEL', 'INFO'))
    
    # Security configuration
    encryption_enabled: bool = field(default_factory=lambda: os.getenv('DATAMETRIA_ENCRYPTION', 'true').lower() == 'true')
    audit_enabled: bool = field(default_factory=lambda: os.getenv('DATAMETRIA_AUDIT', 'true').lower() == 'true')
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate configuration with common and specific checks.
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        self._validate_common()
        self._validate_specific()
    
    def _validate_common(self) -> None:
        """Validate common configuration fields."""
        valid_environments = ['dev', 'staging', 'production']
        if self.environment not in valid_environments:
            raise ConfigValidationError(f"environment must be one of: {valid_environments}")
        
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_log_levels:
            raise ConfigValidationError(f"log_level must be one of: {valid_log_levels}")
    
    @abstractmethod
    def _validate_specific(self) -> None:
        """Validate component-specific configuration.
        
        Must be implemented by subclasses to validate their specific fields.
        """
        pass
    
    @classmethod
    def from_env(cls, prefix: str = '') -> 'BaseConfig':
        """Create configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (e.g., 'MYSERVICE_')
            
        Returns:
            Configuration instance with values from environment
        """
        # Get all environment variables with prefix
        env_vars = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                # Basic type conversion for common types
                if value.isdigit():
                    env_vars[config_key] = int(value)
                elif value.lower() in ('true', 'false'):
                    env_vars[config_key] = value.lower() == 'true'
                else:
                    env_vars[config_key] = value
        
        return cls(**env_vars)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security-related configuration.
        
        Returns:
            Dictionary with security configuration
        """
        return {
            'encryption_enabled': self.encryption_enabled,
            'audit_enabled': self.audit_enabled,
            'environment': self.environment,
            'debug': self.debug
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == 'dev'
