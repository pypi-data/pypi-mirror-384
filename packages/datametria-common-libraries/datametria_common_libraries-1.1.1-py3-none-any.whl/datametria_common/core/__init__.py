"""
DATAMETRIA Core - Foundation Components

Core abstractions and patterns for DATAMETRIA Common Libraries.
"""

from .base_config import BaseConfig, ConfigValidationError
from .health_check import HealthCheckMixin, HealthStatus
from .error_handler import ErrorHandlerMixin, ErrorCategory, ErrorSeverity
from .security_mixin import SecurityMixin
from .compliance_mixin import ComplianceMixin, ComplianceEvent
from .connection_mixin import ConnectionMixin
from .database_security_mixin import DatabaseSecurityMixin
from .query_performance_mixin import QueryPerformanceMixin, QueryMetrics
from .api_security_mixin import APISecurityMixin
from .config_factory import ConfigFactory, ServiceType

__all__ = [
    'BaseConfig',
    'ConfigValidationError',
    'HealthCheckMixin',
    'HealthStatus',
    'ErrorHandlerMixin',
    'ErrorCategory',
    'ErrorSeverity',
    'SecurityMixin',
    'ComplianceMixin',
    'ComplianceEvent',
    'ConnectionMixin',
    'DatabaseSecurityMixin',
    'QueryPerformanceMixin',
    'QueryMetrics',
    'APISecurityMixin',
    'ConfigFactory',
    'ServiceType'
]

__version__ = '1.0.0'
