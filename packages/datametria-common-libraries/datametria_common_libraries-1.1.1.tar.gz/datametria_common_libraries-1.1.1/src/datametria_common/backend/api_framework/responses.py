"""
🔧 Response Handlers - DATAMETRIA API Framework

Handlers padronizados para respostas com integração aos componentes DATAMETRIA.
"""

from typing import Any, Optional, Dict, List, Union
from pydantic import BaseModel
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
import structlog

from datametria_common.core import BaseConfig

logger = structlog.get_logger(__name__)


class DatametriaResponse(BaseModel):
    """Modelo padrão de resposta DATAMETRIA."""
    
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    request_id: Optional[str] = None
    
    class Config:
        """Configuração do modelo."""
        json_encoders = {
            # Adicionar encoders customizados se necessário
        }
    
    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str = "Success",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> "DatametriaResponse":
        """
        Cria resposta de sucesso.
        
        Args:
            data: Dados da resposta
            message: Mensagem de sucesso
            metadata: Metadados adicionais
            request_id: ID da requisição
            
        Returns:
            DatametriaResponse: Resposta padronizada
        """
        config = BaseConfig()
        
        return cls(
            success=True,
            message=message,
            data=data,
            metadata=metadata,
            timestamp=config.get_current_timestamp(),
            request_id=request_id
        )
    
    @classmethod
    def error(
        cls,
        message: str = "Error",
        errors: Optional[List[str]] = None,
        data: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> "DatametriaResponse":
        """
        Cria resposta de erro.
        
        Args:
            message: Mensagem de erro
            errors: Lista de erros específicos
            data: Dados adicionais (opcional)
            metadata: Metadados adicionais
            request_id: ID da requisição
            
        Returns:
            DatametriaResponse: Resposta padronizada
        """
        config = BaseConfig()
        
        return cls(
            success=False,
            message=message,
            data=data,
            errors=errors or [],
            metadata=metadata,
            timestamp=config.get_current_timestamp(),
            request_id=request_id
        )
    
    @classmethod
    def paginated(
        cls,
        data: List[Any],
        total: int,
        page: int,
        per_page: int,
        message: str = "Success",
        request_id: Optional[str] = None
    ) -> "DatametriaResponse":
        """
        Cria resposta paginada.
        
        Args:
            data: Lista de dados
            total: Total de registros
            page: Página atual
            per_page: Registros por página
            message: Mensagem de sucesso
            request_id: ID da requisição
            
        Returns:
            DatametriaResponse: Resposta paginada
        """
        pages = (total + per_page - 1) // per_page
        
        metadata = {
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1
            }
        }
        
        return cls.success(
            data=data,
            message=message,
            metadata=metadata,
            request_id=request_id
        )


class ErrorResponse(BaseModel):
    """Modelo específico para respostas de erro."""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    request_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        error: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> "ErrorResponse":
        """
        Cria resposta de erro específica.
        
        Args:
            error: Tipo do erro
            message: Mensagem do erro
            details: Detalhes adicionais
            request_id: ID da requisição
            
        Returns:
            ErrorResponse: Resposta de erro
        """
        config = BaseConfig()
        
        return cls(
            error=error,
            message=message,
            details=details,
            timestamp=config.get_current_timestamp(),
            request_id=request_id
        )


class ResponseHandler:
    """Handler centralizado para respostas DATAMETRIA."""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        """
        Retorna resposta de sucesso padronizada.
        
        Args:
            data: Dados da resposta
            message: Mensagem de sucesso
            status_code: Código HTTP
            headers: Headers adicionais
            
        Returns:
            JSONResponse: Resposta JSON padronizada
        """
        response_data = DatametriaResponse.success(data=data, message=message)
        
        logger.info(
            "Success response created",
            message=message,
            status_code=status_code,
            has_data=data is not None
        )
        
        return JSONResponse(
            content=response_data.dict(),
            status_code=status_code,
            headers=headers
        )
    
    @staticmethod
    def error(
        message: str = "Error",
        errors: Optional[List[str]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        """
        Retorna resposta de erro padronizada.
        
        Args:
            message: Mensagem de erro
            errors: Lista de erros específicos
            status_code: Código HTTP
            headers: Headers adicionais
            
        Returns:
            JSONResponse: Resposta JSON de erro
        """
        response_data = DatametriaResponse.error(message=message, errors=errors)
        
        logger.error(
            "Error response created",
            message=message,
            status_code=status_code,
            errors=errors
        )
        
        return JSONResponse(
            content=response_data.dict(),
            status_code=status_code,
            headers=headers
        )
    
    @staticmethod
    def validation_error(
        errors: List[str],
        message: str = "Validation failed",
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    ) -> JSONResponse:
        """
        Retorna resposta de erro de validação.
        
        Args:
            errors: Lista de erros de validação
            message: Mensagem principal
            status_code: Código HTTP
            
        Returns:
            JSONResponse: Resposta de erro de validação
        """
        return ResponseHandler.error(
            message=message,
            errors=errors,
            status_code=status_code
        )
    
    @staticmethod
    def not_found(
        message: str = "Resource not found",
        resource: Optional[str] = None
    ) -> JSONResponse:
        """
        Retorna resposta de recurso não encontrado.
        
        Args:
            message: Mensagem de erro
            resource: Nome do recurso não encontrado
            
        Returns:
            JSONResponse: Resposta 404
        """
        if resource:
            message = f"{resource} not found"
        
        return ResponseHandler.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Unauthorized access"
    ) -> JSONResponse:
        """
        Retorna resposta de acesso não autorizado.
        
        Args:
            message: Mensagem de erro
            
        Returns:
            JSONResponse: Resposta 401
        """
        return ResponseHandler.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(
        message: str = "Access forbidden"
    ) -> JSONResponse:
        """
        Retorna resposta de acesso proibido.
        
        Args:
            message: Mensagem de erro
            
        Returns:
            JSONResponse: Resposta 403
        """
        return ResponseHandler.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def internal_error(
        message: str = "Internal server error",
        error_id: Optional[str] = None
    ) -> JSONResponse:
        """
        Retorna resposta de erro interno.
        
        Args:
            message: Mensagem de erro
            error_id: ID do erro para tracking
            
        Returns:
            JSONResponse: Resposta 500
        """
        metadata = {"error_id": error_id} if error_id else None
        
        response_data = DatametriaResponse.error(
            message=message,
            metadata=metadata
        )
        
        logger.error(
            "Internal server error",
            message=message,
            error_id=error_id
        )
        
        return JSONResponse(
            content=response_data.dict(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def paginated(
        data: List[Any],
        total: int,
        page: int,
        per_page: int,
        message: str = "Success"
    ) -> JSONResponse:
        """
        Retorna resposta paginada.
        
        Args:
            data: Lista de dados
            total: Total de registros
            page: Página atual
            per_page: Registros por página
            message: Mensagem de sucesso
            
        Returns:
            JSONResponse: Resposta paginada
        """
        response_data = DatametriaResponse.paginated(
            data=data,
            total=total,
            page=page,
            per_page=per_page,
            message=message
        )
        
        logger.info(
            "Paginated response created",
            total=total,
            page=page,
            per_page=per_page,
            items_count=len(data)
        )
        
        return JSONResponse(
            content=response_data.dict(),
            status_code=status.HTTP_200_OK
        )
