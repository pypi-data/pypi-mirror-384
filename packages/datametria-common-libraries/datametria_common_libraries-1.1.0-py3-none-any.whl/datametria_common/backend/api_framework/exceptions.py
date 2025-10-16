"""
🔧 Exceptions - DATAMETRIA API Framework

Exceções customizadas e handlers para tratamento centralizado de erros.
"""

from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

from .responses import DatametriaResponse, ErrorResponse

logger = structlog.get_logger(__name__)


class DatametriaAPIException(Exception):
    """Exceção base para API DATAMETRIA."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class ValidationException(DatametriaAPIException):
    """Exceção para erros de validação."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.errors = errors or []
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            error_code="VALIDATION_ERROR"
        )


class AuthenticationException(DatametriaAPIException):
    """Exceção para erros de autenticação."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(DatametriaAPIException):
    """Exceção para erros de autorização."""
    
    def __init__(
        self,
        message: str = "Access forbidden",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            error_code="AUTHORIZATION_ERROR"
        )


class RateLimitException(DatametriaAPIException):
    """Exceção para rate limiting."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.retry_after = retry_after
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            error_code="RATE_LIMIT_ERROR"
        )


class ResourceNotFoundException(DatametriaAPIException):
    """Exceção para recursos não encontrados."""
    
    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            error_code="RESOURCE_NOT_FOUND"
        )


class BusinessLogicException(DatametriaAPIException):
    """Exceção para erros de lógica de negócio."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            error_code="BUSINESS_LOGIC_ERROR"
        )


class ExternalServiceException(DatametriaAPIException):
    """Exceção para erros de serviços externos."""
    
    def __init__(
        self,
        service: str,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
            error_code="EXTERNAL_SERVICE_ERROR"
        )


class DatabaseException(DatametriaAPIException):
    """Exceção para erros de banco de dados."""
    
    def __init__(
        self,
        message: str = "Database error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            error_code="DATABASE_ERROR"
        )


class ConfigurationException(DatametriaAPIException):
    """Exceção para erros de configuração."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            error_code="CONFIGURATION_ERROR"
        )


# Exception Handlers

async def datametria_exception_handler(
    request: Request,
    exc: DatametriaAPIException
) -> JSONResponse:
    """
    Handler para exceções DATAMETRIA.
    
    Args:
        request: Request FastAPI
        exc: Exceção DATAMETRIA
        
    Returns:
        JSONResponse: Resposta de erro padronizada
    """
    logger.error(
        "DATAMETRIA exception occurred",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method
    )
    
    # Criar resposta de erro
    error_response = ErrorResponse.create(
        error=exc.error_code,
        message=exc.message,
        details=exc.details
    )
    
    # Headers adicionais para alguns tipos de erro
    headers = {}
    if isinstance(exc, RateLimitException) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict(),
        headers=headers
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler para erros de validação do FastAPI.
    
    Args:
        request: Request FastAPI
        exc: Erro de validação
        
    Returns:
        JSONResponse: Resposta de erro de validação
    """
    # Formatar erros de validação
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    logger.error(
        "Validation error occurred",
        errors=errors,
        path=request.url.path,
        method=request.method
    )
    
    # Criar resposta usando DatametriaResponse
    response_data = DatametriaResponse.error(
        message="Validation failed",
        errors=errors
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data.dict()
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Handler para HTTPException padrão.
    
    Args:
        request: Request FastAPI
        exc: HTTPException
        
    Returns:
        JSONResponse: Resposta de erro HTTP
    """
    logger.error(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    
    # Criar resposta usando DatametriaResponse
    response_data = DatametriaResponse.error(
        message=str(exc.detail) if exc.detail else "HTTP error"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data.dict(),
        headers=getattr(exc, 'headers', None)
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handler para exceções gerais não tratadas.
    
    Args:
        request: Request FastAPI
        exc: Exceção geral
        
    Returns:
        JSONResponse: Resposta de erro interno
    """
    logger.error(
        "Unhandled exception occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    # Criar resposta de erro interno
    response_data = DatametriaResponse.error(
        message="Internal server error"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data.dict()
    )


def setup_exception_handlers(app) -> None:
    """
    Configura handlers de exceção para a aplicação.
    
    Args:
        app: Instância FastAPI
    """
    # Handlers específicos DATAMETRIA
    app.add_exception_handler(DatametriaAPIException, datametria_exception_handler)
    app.add_exception_handler(ValidationException, datametria_exception_handler)
    app.add_exception_handler(AuthenticationException, datametria_exception_handler)
    app.add_exception_handler(AuthorizationException, datametria_exception_handler)
    app.add_exception_handler(RateLimitException, datametria_exception_handler)
    app.add_exception_handler(ResourceNotFoundException, datametria_exception_handler)
    app.add_exception_handler(BusinessLogicException, datametria_exception_handler)
    app.add_exception_handler(ExternalServiceException, datametria_exception_handler)
    app.add_exception_handler(DatabaseException, datametria_exception_handler)
    app.add_exception_handler(ConfigurationException, datametria_exception_handler)
    
    # Handlers padrão FastAPI
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Handler geral para exceções não tratadas
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers configured successfully")
