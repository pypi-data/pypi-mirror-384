"""
🔧 Decorators - DATAMETRIA API Framework

Decorators para validação, autenticação e rate limiting com integração DATAMETRIA.
"""

from functools import wraps
from typing import Type, Optional, Callable, Any, List
from fastapi import HTTPException, status, Depends, Request
from pydantic import BaseModel, ValidationError
import structlog

from .dependencies import get_current_user, get_rate_limiter, get_security_manager

logger = structlog.get_logger(__name__)


def authenticate(required: bool = True, roles: Optional[List[str]] = None):
    """
    Decorator para autenticação de endpoints.
    
    Args:
        required: Se autenticação é obrigatória
        roles: Lista de roles permitidos
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Verificar se current_user está nos kwargs (injetado por dependency)
            current_user = kwargs.get('current_user')
            
            if required and not current_user:
                logger.warning("Authentication required but no user provided", endpoint=func.__name__)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Verificar roles se especificados
            if current_user and roles:
                user_role = None
                
                if isinstance(current_user, dict):
                    user_role = current_user.get("role")
                else:
                    user_role = getattr(current_user, 'role', None)
                
                if user_role not in roles:
                    logger.warning(
                        "Insufficient privileges",
                        endpoint=func.__name__,
                        user_role=user_role,
                        required_roles=roles
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role must be one of: {', '.join(roles)}"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate(schema: Type[BaseModel], field_name: str = "data"):
    """
    Decorator para validação de dados com Pydantic.
    
    Args:
        schema: Classe Pydantic para validação
        field_name: Nome do campo nos kwargs que contém os dados
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obter dados para validação
            data = kwargs.get(field_name)
            
            if data is None:
                logger.error("No data provided for validation", endpoint=func.__name__)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field '{field_name}' is required"
                )
            
            try:
                # Validar dados com schema Pydantic
                if isinstance(data, dict):
                    validated_data = schema(**data)
                elif isinstance(data, BaseModel):
                    validated_data = schema(**data.dict())
                else:
                    validated_data = schema(data)
                
                # Substituir dados originais pelos validados
                kwargs[field_name] = validated_data
                
                logger.info("Data validation successful", endpoint=func.__name__)
                
            except ValidationError as e:
                logger.error(
                    "Data validation failed",
                    endpoint=func.__name__,
                    errors=e.errors()
                )
                
                # Formatar erros para resposta
                error_messages = []
                for error in e.errors():
                    field = " -> ".join(str(loc) for loc in error["loc"])
                    message = error["msg"]
                    error_messages.append(f"{field}: {message}")
                
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": "Validation failed",
                        "errors": error_messages
                    }
                )
            
            except Exception as e:
                logger.error("Unexpected validation error", endpoint=func.__name__, error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Validation error"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(
    requests: int = 100,
    window: int = 60,
    key_func: Optional[Callable] = None,
    skip_if_authenticated: bool = False
):
    """
    Decorator para rate limiting.
    
    Args:
        requests: Número máximo de requests
        window: Janela de tempo em segundos
        key_func: Função para gerar chave do rate limit
        skip_if_authenticated: Pular rate limit para usuários autenticados
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obter request object
            request = None
            for arg in args:
                if hasattr(arg, 'client'):  # FastAPI Request object
                    request = arg
                    break
            
            if not request:
                # Se não há request, pular rate limiting
                logger.warning("No request object found, skipping rate limit")
                return await func(*args, **kwargs)
            
            # Verificar se deve pular para usuários autenticados
            if skip_if_authenticated:
                current_user = kwargs.get('current_user')
                if current_user:
                    return await func(*args, **kwargs)
            
            # Gerar chave para rate limiting
            if key_func:
                rate_limit_key = key_func(request)
            else:
                # Usar IP do cliente como chave padrão
                client_ip = request.client.host if request.client else "unknown"
                rate_limit_key = f"rate_limit:{client_ip}:{func.__name__}"
            
            try:
                # Obter rate limiter (pode ser None se não disponível)
                rate_limiter = get_rate_limiter()
                
                if rate_limiter:
                    # Verificar rate limit
                    allowed = await rate_limiter.is_allowed(
                        key=rate_limit_key,
                        limit=requests,
                        window=window
                    )
                    
                    if not allowed:
                        logger.warning(
                            "Rate limit exceeded",
                            endpoint=func.__name__,
                            key=rate_limit_key,
                            limit=requests,
                            window=window
                        )
                        
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=f"Rate limit exceeded: {requests} requests per {window} seconds",
                            headers={"Retry-After": str(window)}
                        )
                    
                    logger.debug("Rate limit check passed", endpoint=func.__name__)
                else:
                    logger.warning("Rate limiter not available, skipping check")
                
            except HTTPException:
                # Re-raise HTTP exceptions (rate limit exceeded)
                raise
            except Exception as e:
                logger.error("Rate limit check failed", endpoint=func.__name__, error=str(e))
                # Continuar sem rate limiting em caso de erro
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_endpoint(
    log_request: bool = True,
    log_response: bool = False,
    log_level: str = "info"
):
    """
    Decorator para logging de endpoints.
    
    Args:
        log_request: Log dados da requisição
        log_response: Log dados da resposta
        log_level: Nível de log (info, debug, warning, error)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            endpoint_name = func.__name__
            
            # Log request
            if log_request:
                log_data = {
                    "endpoint": endpoint_name,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
                
                getattr(logger, log_level)("Endpoint called", **log_data)
            
            try:
                # Executar função
                result = await func(*args, **kwargs)
                
                # Log response
                if log_response:
                    log_data = {
                        "endpoint": endpoint_name,
                        "success": True,
                        "result_type": type(result).__name__
                    }
                    
                    getattr(logger, log_level)("Endpoint completed", **log_data)
                
                return result
                
            except Exception as e:
                # Log error
                logger.error(
                    "Endpoint failed",
                    endpoint=endpoint_name,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator


def cache_response(
    ttl: int = 300,
    key_func: Optional[Callable] = None,
    vary_on_user: bool = False
):
    """
    Decorator para cache de respostas.
    
    Args:
        ttl: Time to live em segundos
        key_func: Função para gerar chave do cache
        vary_on_user: Incluir usuário na chave do cache
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                from datametria_common.utilities.cache_manager import CacheManager
                cache = CacheManager()
                
                # Gerar chave do cache
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"endpoint_cache:{func.__name__}"
                    
                    # Incluir usuário na chave se solicitado
                    if vary_on_user:
                        current_user = kwargs.get('current_user')
                        if current_user:
                            user_id = None
                            if isinstance(current_user, dict):
                                user_id = current_user.get('user_id') or current_user.get('id')
                            else:
                                user_id = getattr(current_user, 'id', None)
                            
                            if user_id:
                                cache_key += f":user_{user_id}"
                
                # Tentar obter do cache
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    logger.debug("Cache hit", endpoint=func.__name__, cache_key=cache_key)
                    return cached_result
                
                # Executar função e cachear resultado
                result = await func(*args, **kwargs)
                await cache.set(cache_key, result, ttl=ttl)
                
                logger.debug("Cache miss, result cached", endpoint=func.__name__, cache_key=cache_key)
                return result
                
            except ImportError:
                logger.warning("Cache not available, executing without cache")
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error("Cache operation failed", error=str(e))
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
