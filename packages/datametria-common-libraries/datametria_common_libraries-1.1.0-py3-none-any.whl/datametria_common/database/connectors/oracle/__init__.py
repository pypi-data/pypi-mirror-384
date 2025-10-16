"""
🏛️ DATAMETRIA Oracle Connector - Enterprise Oracle 19c+ Support

Conector enterprise para Oracle Database com suporte completo a recursos avançados,
segurança, compliance e alta disponibilidade para ambientes de produção críticos.

Features:
    - Oracle 19c+ (incluindo 21c, 23c, 23ai)
    - Oracle RAC (Real Application Clusters) com load balancing
    - Advanced Security (TDE, Data Redaction, VPD)
    - PL/SQL procedures, packages e functions
    - Connection pooling otimizado com health checks
    - Failover automático e circuit breaker pattern
    - LGPD/GDPR compliance nativo com data masking
    - Timezone management avançado
    - Audit trail completo
    - Performance monitoring e métricas

Components:
    OracleConnector: Classe principal para conexões Oracle
    OracleConfig: Configuração enterprise com validação
    OracleConnectionPool: Pool de conexões com alta disponibilidade
    OracleSecurityManager: Gerenciamento de segurança e compliance
    OracleTimezoneManager: Gestão avançada de timezones
    
Exceptions:
    OracleConnectionError: Erros de conectividade
    OracleQueryError: Erros de execução de queries
    OracleSecurityError: Violações de segurança
    OracleConfigError: Erros de configuração

Example:
    Basic usage:
    >>> from datametria_common.database.connectors.oracle import OracleConnector, OracleConfig
    >>> config = OracleConfig(
    ...     host="oracle.prod.com",
    ...     port=1521,
    ...     service_name="PRODDB",
    ...     username="app_user",
    ...     password="secure_password"
    ... )
    >>> connector = OracleConnector(config)
    >>> with connector.get_connection() as conn:
    ...     result = conn.execute("SELECT COUNT(*) FROM users")
    ...     print(f"Total users: {result.fetchone()[0]}")

Note:
    Este módulo requer Oracle Instant Client 19c+ ou superior.
    Para ambientes de produção, sempre use variáveis de ambiente
    ou HashiCorp Vault para credenciais.

Version:
    Added in: DATAMETRIA Common Libraries v1.0.0
    Last modified: 2025-01-08
    Stability: Stable - Production Ready
    
Author:
    Equipe DATAMETRIA <suporte@datametria.io>
    
License:
    MIT License - Copyright (c) 2025 DATAMETRIA LTDA
"""

from .connector import OracleConnector
from .config import OracleConfig, OracleAuthMode
from .pool import OracleConnectionPool
from .security import OracleSecurityManager
from .timezone_manager import (
    OracleTimezoneManager,
    OracleTimezoneOperations,
    TimezoneAwareDateTime,
    DMOneTimezoneConfig
)
from .exceptions import (
    OracleConnectionError,
    OracleQueryError,
    OracleSecurityError,
    OracleConfigError
)

# Package metadata
__version__ = "1.0.0"
__author__ = "Equipe DATAMETRIA <suporte@datametria.io>"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 DATAMETRIA LTDA"
__status__ = "Production"
__maintainer__ = "DATAMETRIA Enterprise Team"
__email__ = "suporte@datametria.io"
__url__ = "https://github.com/datametria/DATAMETRIA-common-libraries"

__all__ = [
    "OracleConnector",
    "OracleConfig",
    "OracleAuthMode",
    "OracleConnectionPool",
    "OracleSecurityManager",
    "OracleTimezoneManager",
    "OracleTimezoneOperations",
    "TimezoneAwareDateTime",
    "DMOneTimezoneConfig",
    "OracleConnectionError",
    "OracleQueryError", 
    "OracleSecurityError",
    "OracleConfigError"
]
