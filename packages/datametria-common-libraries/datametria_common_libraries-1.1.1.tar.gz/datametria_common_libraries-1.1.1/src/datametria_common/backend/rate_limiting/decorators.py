"""
🚦 Rate Limiting Decorators - DATAMETRIA Rate Limiting

Decorators para rate limiting integrados ao API Framework.
"""

from functools import wraps
from typing import Optional, Callable, Any, Dict
from fastapi import HTTPException, status, Request
import structlog

from .models import RateLimit, RateLimitStrategy
from .rate_limiter import RateLimiter

logger = structlog.get_logger(__name__)


def rate_limit(
    requests: int,
    window: int,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    key_func: Optional[Callable] = None,
    per_user: bool = True,
    burst_requests: Optional[int] = None,
    burst_window: Optional[int] = None
):
    """
    Decorator para rate limiting de endpoints específicos.
    
    Args:
        requests: Número de requests permitidos
        window: Janela de tempo em segundos
        strategy: Estratégia de rate limiting
        key_func: Função para gerar chave customizada
        per_user: Rate limit por usuário (se autenticado)
        burst_requests: Requests de burst permitidos
        burst_window: Janela de burst em segundos
        
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
                logger.warning("No request object found, skipping rate limit")
                return await func(*args, **kwargs)
            
            try:
                # Obter rate limiter (integração com componentes existentes)
                rate_limiter = _get_rate_limiter()
                
                if not rate_limiter:
                    logger.warning("Rate limiter not available")
                    return await func(*args, **kwargs)
                
                # Gerar chave de rate limiting
                if key_func:
                    key = key_func(request, *args, **kwargs)
                else:
                    key = _generate_default_key(request, per_user, func.__name__)
                
                # Obter informações do usuário se disponível
                current_user = kwargs.get('current_user')
                user_id = None
                user_role = None
                
                if current_user:
                    if isinstance(current_user, dict):
                        user_id = current_user.get('user_id')
                        user_role = current_user.get('role')
                    else:
                        user_id = getattr(current_user, 'id', None)
                        user_role = getattr(current_user, 'role', None)
                
                # Verificar rate limit
                allowed, info = rate_limiter.is_allowed(
                    key=key,
                    endpoint=f"{request.method}:{request.url.path}",
                    user_id=user_id,
                    user_role=user_role
                )
                
                if not allowed:
                    logger.warning(
                        "Rate limit exceeded",
                        key=key,
                        endpoint=func.__name__,
                        user_id=user_id,
                        remaining=info.get('remaining', 0)
                    )
                    
                    # Criar resposta de rate limit excedido
                    detail = {
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {requests} per {window} seconds.",
                        "limit": requests,
                        "remaining": info.get('remaining', 0),
                        "reset_time": info.get('reset_time'),
                        "retry_after": info.get('retry_after', window)
                    }
                    
                    headers = {}
                    if info.get('retry_after'):
                        headers["Retry-After"] = str(info['retry_after'])
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=detail,
                        headers=headers
                    )
                
                # Log de sucesso
                logger.debug(
                    "Rate limit check passed",
                    key=key,
                    endpoint=func.__name__,
                    remaining=info.get('remaining')
                )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                # Re-raise HTTP exceptions (rate limit exceeded)
                raise
            except Exception as e:
                logger.error("Rate limit check failed", endpoint=func.__name__, error=str(e))
                # Continuar sem rate limiting em caso de erro
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def adaptive_rate_limit(
    base_requests: int,
    window: int,
    max_requests: Optional[int] = None,
    min_requests: Optional[int] = None,
    adjustment_factor: float = 0.1,
    key_func: Optional[Callable] = None
):
    """
    Decorator para rate limiting adaptativo baseado na carga.
    
    Args:
        base_requests: Número base de requests
        window: Janela de tempo em segundos
        max_requests: Máximo de requests (padrão: base_requests * 2)
        min_requests: Mínimo de requests (padrão: base_requests / 2)
        adjustment_factor: Fator de ajuste (0.0 a 1.0)
        key_func: Função para gerar chave customizada
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if hasattr(arg, 'client'):
                    request = arg
                    break
            
            if not request:
                return await func(*args, **kwargs)
            
            try:
                rate_limiter = _get_rate_limiter()
                if not rate_limiter:
                    return await func(*args, **kwargs)
                
                # Calcular limite adaptativo
                current_load = _get_system_load()  # Implementar baseado em métricas
                
                # Ajustar limite baseado na carga
                if current_load > 0.8:  # Alta carga
                    adjusted_requests = max(
                        min_requests or base_requests // 2,
                        int(base_requests * (1 - adjustment_factor))
                    )
                elif current_load < 0.3:  # Baixa carga
                    adjusted_requests = min(
                        max_requests or base_requests * 2,
                        int(base_requests * (1 + adjustment_factor))
                    )
                else:
                    adjusted_requests = base_requests
                
                # Gerar chave
                if key_func:
                    key = key_func(request, *args, **kwargs)
                else:
                    key = _generate_default_key(request, True, func.__name__)
                
                # Verificar rate limit adaptativo
                allowed, info = rate_limiter.is_allowed(key=key)
                
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Adaptive rate limit exceeded",
                            "current_limit": adjusted_requests,
                            "system_load": current_load,
                            "retry_after": info.get('retry_after', window)
                        }
                    )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Adaptive rate limit failed", error=str(e))
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def burst_protection(
    normal_requests: int,
    normal_window: int,
    burst_requests: int,
    burst_window: int,
    recovery_time: int = 300
):
    """
    Decorator para proteção contra burst de requests.
    
    Args:
        normal_requests: Requests normais permitidos
        normal_window: Janela normal em segundos
        burst_requests: Requests de burst permitidos
        burst_window: Janela de burst em segundos
        recovery_time: Tempo de recuperação em segundos
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if hasattr(arg, 'client'):
                    request = arg
                    break
            
            if not request:
                return await func(*args, **kwargs)
            
            try:
                rate_limiter = _get_rate_limiter()
                if not rate_limiter:
                    return await func(*args, **kwargs)
                
                key = _generate_default_key(request, True, func.__name__)
                
                # Verificar limite normal
                normal_allowed, normal_info = rate_limiter.is_allowed(
                    key=f"normal:{key}"
                )
                
                # Verificar limite de burst
                burst_allowed, burst_info = rate_limiter.is_allowed(
                    key=f"burst:{key}"
                )
                
                if not normal_allowed and not burst_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Burst protection activated",
                            "normal_limit_exceeded": not normal_allowed,
                            "burst_limit_exceeded": not burst_allowed,
                            "recovery_time": recovery_time
                        }
                    )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Burst protection failed", error=str(e))
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def _get_rate_limiter() -> Optional[RateLimiter]:
    """
    Obtém instância do rate limiter (integração com componentes existentes).
    
    Returns:
        RateLimiter: Instância ou None se não disponível
    """
    try:
        # Tentar obter do cache de aplicação ou criar nova instância
        return RateLimiter()
    except Exception as e:
        logger.error("Failed to get rate limiter", error=str(e))
        return None


def _generate_default_key(request: Request, per_user: bool, endpoint: str) -> str:
    """
    Gera chave padrão de rate limiting.
    
    Args:
        request: Request FastAPI
        per_user: Rate limit por usuário
        endpoint: Nome do endpoint
        
    Returns:
        str: Chave de rate limiting
    """
    # Priorizar usuário se autenticado e per_user=True
    if per_user and hasattr(request.state, 'user_id'):
        return f"user:{request.state.user_id}:{endpoint}"
    
    # Fallback para IP
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get('X-Forwarded-For')
    
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    
    return f"ip:{client_ip}:{endpoint}"


def _get_system_load() -> float:
    """
    Obtém carga atual do sistema (implementação simplificada).
    
    Returns:
        float: Carga do sistema (0.0 a 1.0)
    """
    try:
        # Implementação básica - expandir com métricas reais
        import psutil
        return psutil.cpu_percent(interval=1) / 100.0
    except ImportError:
        # Fallback se psutil não disponível
        return 0.5  # Carga média assumida


# Aliases para compatibilidade
limit_requests = rate_limit
protect_endpoint = burst_protection
