"""
🔧 API Framework - DATAMETRIA Common Libraries

Framework FastAPI Enterprise-Ready com integração completa aos componentes DATAMETRIA.

Features:
    - DatametriaAPI: Classe principal FastAPI customizada
    - Middleware Stack: CORS, logging, compression, security
    - Response Handlers: Padronização de respostas
    - Dependency Injection: Database, cache, settings
    - Error Handling: Tratamento centralizado de erros
    - Validation: Decorators para validação automática
    - Authentication: Integração com sistema de auth
    - Rate Limiting: Controle de taxa integrado

Components:
    app: Classe principal DatametriaAPI
    middleware: Stack de middleware enterprise
    responses: Handlers de resposta padronizados
    dependencies: Sistema de injeção de dependência
    decorators: Decorators para validação e auth
    exceptions: Tratamento de exceções customizado

Integration:
    - Database Layer: Conectores Oracle, PostgreSQL, SQL Server
    - Security Framework: LGPD/GDPR compliance automático
    - Logging Enterprise: Structured logging integrado
    - Configuration Manager: Configurações centralizadas
    - Authentication System: JWT, OAuth2, MFA
    - Rate Limiting: Redis-based rate limiting

Example:
    Basic API setup:
    >>> from datametria_common.backend.api_framework import DatametriaAPI
    >>> from datametria_common.backend.api_framework.middleware import setup_middleware
    >>> 
    >>> app = DatametriaAPI(
    ...     title="My Enterprise API",
    ...     version="1.0.0"
    ... )
    >>> setup_middleware(app)
    >>> 
    >>> @app.get("/health")
    >>> async def health_check():
    ...     return {"status": "healthy"}

Author: DATAMETRIA Enterprise Team
Version: 1.0.0
"""

from .app import DatametriaAPI
from .middleware import (
    setup_middleware,
    CORSMiddleware,
    LoggingMiddleware,
    CompressionMiddleware,
    SecurityMiddleware
)
from .responses import DatametriaResponse, ErrorResponse
from .dependencies import (
    get_db,
    get_cache,
    get_settings,
    get_current_user,
    get_security_manager
)
from .decorators import authenticate, validate, rate_limit
from .exceptions import (
    DatametriaAPIException,
    ValidationException,
    AuthenticationException,
    RateLimitException
)

__all__ = [
    # Core
    "DatametriaAPI",
    
    # Middleware
    "setup_middleware",
    "CORSMiddleware",
    "LoggingMiddleware", 
    "CompressionMiddleware",
    "SecurityMiddleware",
    
    # Responses
    "DatametriaResponse",
    "ErrorResponse",
    
    # Dependencies
    "get_db",
    "get_cache",
    "get_settings",
    "get_current_user",
    "get_security_manager",
    
    # Decorators
    "authenticate",
    "validate",
    "rate_limit",
    
    # Exceptions
    "DatametriaAPIException",
    "ValidationException",
    "AuthenticationException",
    "RateLimitException"
]
