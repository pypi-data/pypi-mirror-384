"""
🔒 DATAMETRIA Security Framework - Enterprise Security & Compliance

Framework completo de segurança enterprise com compliance automático
LGPD/GDPR, logging estruturado e proteção de dados pessoais.

Features:
    - LGPD Compliance automático com data masking
    - GDPR Compliance com right to erasure e portability
    - Enterprise Logging com audit trail completo
    - Data encryption e tokenization
    - Access control e authorization
    - Security monitoring e alerting

Components:
    LGPDCompliance: Gerenciamento automático de compliance LGPD
    GDPRCompliance: Gerenciamento automático de compliance GDPR
    EnterpriseLogger: Sistema de logging estruturado enterprise
    SecurityManager: Gerenciador central de segurança
    DataProtection: Proteção e masking de dados pessoais

Example:
    >>> from datametria_common.security import SecurityManager, LGPDCompliance
    >>> security = SecurityManager()
    >>> lgpd = LGPDCompliance()
    >>> 
    >>> # Encrypt sensitive data
    >>> encrypted = security.encrypt_sensitive_data(user_data)
    >>> 
    >>> # LGPD compliance check
    >>> lgpd.validate_data_processing(operation="READ", data_type="personal")

Version:
    Added in: DATAMETRIA Common Libraries v1.0.0
    Last modified: 2025-01-08
    Stability: Production Ready

Author:
    DATAMETRIA Enterprise Team <suporte@datametria.io>

License:
    MIT License - Copyright (c) 2025 DATAMETRIA LTDA
"""

from .lgpd_compliance import LGPDCompliance, LGPDDataProcessor, LGPDAuditLogger
from .gdpr_compliance import GDPRCompliance, GDPRDataProcessor, GDPRRightsManager
from .enterprise_logging import EnterpriseLogger, SecurityAuditLogger, ComplianceLogger
from .centralized_logger import CentralizedEnterpriseLogger
from .config import LoggingConfig, HandlerConfig
from .context_binding import (
    with_logging_context,
    bind_context,
    get_current_logger,
    set_current_logger,
)
from .security_manager import SecurityManager, DataProtection, AccessControl
from .exceptions import (
    SecurityError,
    ComplianceError,
    LGPDViolationError,
    GDPRViolationError,
    DataProtectionError,
    AuditError
)

# Package metadata
__version__ = "1.0.0"
__author__ = "DATAMETRIA Enterprise Team <suporte@datametria.io>"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 DATAMETRIA LTDA"

__all__ = [
    # LGPD Compliance
    "LGPDCompliance",
    "LGPDDataProcessor", 
    "LGPDAuditLogger",
    # GDPR Compliance
    "GDPRCompliance",
    "GDPRDataProcessor",
    "GDPRRightsManager",
    # Enterprise Logging
    "EnterpriseLogger",
    "SecurityAuditLogger",
    "ComplianceLogger",
    "CentralizedEnterpriseLogger",
    "LoggingConfig",
    "HandlerConfig",
    # Context Binding
    "with_logging_context",
    "bind_context",
    "get_current_logger",
    "set_current_logger",
    # Security Management
    "SecurityManager",
    "DataProtection",
    "AccessControl",
    # Exceptions
    "SecurityError",
    "ComplianceError",
    "LGPDViolationError",
    "GDPRViolationError",
    "DataProtectionError",
    "AuditError"
]
