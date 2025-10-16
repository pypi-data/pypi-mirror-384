"""
DATAMETRIA ConfigFactory - Universal Configuration Factory Pattern

Universal configuration factory that provides consistent configuration
creation and management across all DATAMETRIA services.
"""

from typing import Dict, Any, Type, Optional
from enum import Enum

from .base_config import BaseConfig


class ServiceType(Enum):
    """Supported service types for configuration."""
    DATABASE = "database"
    API = "api"
    CLOUD = "cloud"
    SECURITY = "security"
    MOBILE = "mobile"
    FRONTEND = "frontend"


class ConfigFactory:
    """Universal configuration factory for all DATAMETRIA services.
    
    Provides standardized configuration creation with:
    - Service-specific configuration templates
    - Environment-based configuration
    - Validation and defaults
    - Configuration inheritance
    
    Example:
        >>> factory = ConfigFactory()
        >>> db_config = factory.create_config(ServiceType.DATABASE, "postgresql")
        >>> api_config = factory.create_config(ServiceType.API, environment="production")
    """
    
    def __init__(self):
        """Initialize configuration factory."""
        self._config_templates: Dict[str, Dict[str, Any]] = {}
        self._registered_configs: Dict[str, Type[BaseConfig]] = {}
        self._setup_default_templates()
    
    def _setup_default_templates(self) -> None:
        """Setup default configuration templates."""
        self._config_templates = {
            "database": {
                "max_connections": 10,
                "connection_timeout": 30,
                "retry_attempts": 3,
                "pool_size": 5
            },
            "api": {
                "port": 8000,
                "rate_limit": 100,
                "cors_origins": ["*"],
                "jwt_expiry_hours": 24
            },
            "cloud": {
                "region": "us-east-1",
                "auto_scaling": True,
                "backup_enabled": True,
                "monitoring_enabled": True
            },
            "security": {
                "encryption_enabled": True,
                "audit_enabled": True,
                "session_timeout": 30,
                "password_min_length": 8
            },
            "mobile": {
                "push_notifications": True,
                "offline_mode": True,
                "biometric_auth": False,
                "auto_update": True
            },
            "frontend": {
                "theme": "light",
                "language": "en",
                "cache_enabled": True,
                "analytics_enabled": True
            }
        }
    
    def register_config_class(self, service_type: str, config_class: Type[BaseConfig]) -> None:
        """Register a custom configuration class."""
        self._registered_configs[service_type] = config_class
    
    def create_config(self, service_type: ServiceType, 
                     config_name: Optional[str] = None,
                     environment: str = "production",
                     **overrides) -> BaseConfig:
        """Create configuration for specified service type.
        
        Args:
            service_type: Type of service (database, api, etc.)
            config_name: Specific configuration name
            environment: Environment (dev, staging, production)
            **overrides: Configuration overrides
            
        Returns:
            Configured BaseConfig instance
        """
        service_key = service_type.value
        
        # Get base template
        base_config = self._config_templates.get(service_key, {}).copy()
        
        # Apply environment-specific overrides
        env_config = self._get_environment_config(environment)
        base_config.update(env_config)
        
        # Apply custom overrides
        base_config.update(overrides)
        
        # Create configuration instance
        if service_key in self._registered_configs:
            config_class = self._registered_configs[service_key]
            return config_class(**base_config)
        else:
            # Create dynamic config class
            return self._create_dynamic_config(service_key, base_config)
    
    def _get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get environment-specific configuration overrides."""
        env_configs = {
            "dev": {
                "debug": True,
                "log_level": "DEBUG",
                "encryption_enabled": False
            },
            "staging": {
                "debug": False,
                "log_level": "INFO",
                "encryption_enabled": True
            },
            "production": {
                "debug": False,
                "log_level": "WARNING",
                "encryption_enabled": True
            }
        }
        
        return env_configs.get(environment, {})
    
    def _create_dynamic_config(self, service_type: str, config_data: Dict[str, Any]) -> BaseConfig:
        """Create dynamic configuration class."""
        class DynamicConfig(BaseConfig):
            def __init__(self, **kwargs):
                # Set attributes from config_data
                for key, value in config_data.items():
                    setattr(self, key, value)
                
                # Override with any provided kwargs
                for key, value in kwargs.items():
                    setattr(self, key, value)
                
                super().__init__()
            
            def _validate_specific(self):
                # Basic validation for dynamic configs
                pass
        
        return DynamicConfig()
    
    def get_template(self, service_type: ServiceType) -> Dict[str, Any]:
        """Get configuration template for service type."""
        return self._config_templates.get(service_type.value, {}).copy()
    
    def update_template(self, service_type: ServiceType, updates: Dict[str, Any]) -> None:
        """Update configuration template."""
        service_key = service_type.value
        if service_key not in self._config_templates:
            self._config_templates[service_key] = {}
        
        self._config_templates[service_key].update(updates)
    
    def create_database_config(self, db_type: str = "postgresql", **overrides) -> BaseConfig:
        """Create database-specific configuration."""
        db_defaults = {
            "postgresql": {"port": 5432, "ssl_mode": "require"},
            "oracle": {"port": 1521, "service_name": "xe"},
            "sqlserver": {"port": 1433, "encrypt": True},
            "sqlite": {"file_path": ":memory:", "timeout": 20}
        }
        
        db_config = db_defaults.get(db_type, {})
        db_config.update(overrides)
        
        return self.create_config(ServiceType.DATABASE, db_type, **db_config)
    
    def create_api_config(self, api_type: str = "rest", **overrides) -> BaseConfig:
        """Create API-specific configuration."""
        api_defaults = {
            "rest": {"openapi_enabled": True, "docs_url": "/docs"},
            "graphql": {"playground_enabled": True, "introspection": True},
            "grpc": {"reflection_enabled": False, "compression": True}
        }
        
        api_config = api_defaults.get(api_type, {})
        api_config.update(overrides)
        
        return self.create_config(ServiceType.API, api_type, **api_config)
    
    def create_cloud_config(self, provider: str = "aws", **overrides) -> BaseConfig:
        """Create cloud provider-specific configuration."""
        cloud_defaults = {
            "aws": {"region": "us-east-1", "use_iam_roles": True},
            "gcp": {"region": "us-central1", "use_service_account": True},
            "azure": {"region": "eastus", "use_managed_identity": True}
        }
        
        cloud_config = cloud_defaults.get(provider, {})
        cloud_config.update(overrides)
        
        return self.create_config(ServiceType.CLOUD, provider, **cloud_config)
