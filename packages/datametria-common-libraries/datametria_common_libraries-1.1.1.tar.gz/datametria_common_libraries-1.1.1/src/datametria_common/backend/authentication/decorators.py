"""
🔐 Authentication Decorators - DATAMETRIA Authentication

Decorators para autenticação integrados ao API Framework.
"""

from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import HTTPException, status, Request
import structlog

from .models import UserRole
from .dependencies import get_auth_manager

logger = structlog.get_logger(__name__)


def require_auth(
    roles: Optional[List[UserRole]] = None,
    permissions: Optional[List[str]] = None,
    allow_inactive: bool = False
):
    """
    Decorator para requerer autenticação com roles/permissões opcionais.
    
    Args:
        roles: Lista de roles permitidos
        permissions: Lista de permissões necessárias
        allow_inactive: Permitir usuários inativos
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obter usuário atual dos kwargs (injetado por dependency)
            current_user = kwargs.get('current_user')
            
            if not current_user:
                logger.warning("Authentication required but no user provided", endpoint=func.__name__)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Verificar se usuário está ativo
            if not allow_inactive:
                is_active = current_user.get("active", True)  # Assumir ativo se não especificado
                if not is_active:
                    logger.warning(
                        "Inactive user access denied",
                        user_id=current_user.get("user_id"),
                        endpoint=func.__name__
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Account is inactive"
                    )
            
            # Verificar roles se especificados
            if roles:
                user_role = current_user.get("role")
                if user_role not in roles:
                    logger.warning(
                        "Role access denied",
                        user_id=current_user.get("user_id"),
                        user_role=user_role,
                        required_roles=roles,
                        endpoint=func.__name__
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"One of these roles required: {', '.join(roles)}"
                    )
            
            # Verificar permissões se especificadas
            if permissions:
                user_role = current_user.get("role")
                
                # Admin tem todas as permissões
                if user_role != UserRole.ADMIN:
                    # Implementar lógica de permissões específica
                    logger.warning(
                        "Permissions access denied",
                        user_id=current_user.get("user_id"),
                        user_role=user_role,
                        required_permissions=permissions,
                        endpoint=func.__name__
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permissions required: {', '.join(permissions)}"
                    )
            
            logger.debug(
                "Authentication check passed",
                user_id=current_user.get("user_id"),
                endpoint=func.__name__
            )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_mfa(mfa_methods: Optional[List[str]] = None):
    """
    Decorator para requerer multi-factor authentication.
    
    Args:
        mfa_methods: Métodos MFA aceitos (totp, sms, etc.)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Verificar se MFA foi validado na sessão atual
            mfa_verified = current_user.get("mfa_verified", False)
            
            if not mfa_verified:
                logger.warning(
                    "MFA verification required",
                    user_id=current_user.get("user_id"),
                    endpoint=func.__name__
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Multi-factor authentication required",
                    headers={"X-MFA-Required": "true"}
                )
            
            # Verificar métodos MFA se especificados
            if mfa_methods:
                user_mfa_method = current_user.get("mfa_method")
                if user_mfa_method not in mfa_methods:
                    logger.warning(
                        "MFA method not allowed",
                        user_id=current_user.get("user_id"),
                        user_method=user_mfa_method,
                        allowed_methods=mfa_methods,
                        endpoint=func.__name__
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"MFA method must be one of: {', '.join(mfa_methods)}"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin(func: Callable) -> Callable:
    """
    Decorator para requerer privilégios de admin.
    
    Args:
        func: Função a ser decorada
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_role = current_user.get("role")
        if user_role != UserRole.ADMIN:
            logger.warning(
                "Admin access denied",
                user_id=current_user.get("user_id"),
                user_role=user_role,
                endpoint=func.__name__
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def audit_login(
    action: str = "login",
    include_device_info: bool = True,
    log_success: bool = True,
    log_failure: bool = True
):
    """
    Decorator para auditoria de ações de autenticação.
    
    Args:
        action: Ação sendo auditada
        include_device_info: Incluir informações do dispositivo
        log_success: Logar sucessos
        log_failure: Logar falhas
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obter informações da requisição
            request = None
            for arg in args:
                if hasattr(arg, 'client'):  # FastAPI Request object
                    request = arg
                    break
            
            # Informações básicas de auditoria
            audit_data = {
                "action": action,
                "endpoint": func.__name__,
                "ip_address": request.client.host if request and request.client else "unknown",
                "user_agent": request.headers.get("user-agent") if request else "unknown"
            }
            
            # Incluir informações do dispositivo se solicitado
            if include_device_info and request:
                audit_data["device_info"] = {
                    "user_agent": request.headers.get("user-agent"),
                    "accept_language": request.headers.get("accept-language"),
                    "x_forwarded_for": request.headers.get("x-forwarded-for")
                }
            
            try:
                # Executar função
                result = await func(*args, **kwargs)
                
                # Log de sucesso
                if log_success:
                    # Tentar extrair user_id do resultado ou kwargs
                    user_id = None
                    if isinstance(result, dict):
                        user_data = result.get("user", {})
                        user_id = user_data.get("id")
                    
                    current_user = kwargs.get('current_user')
                    if current_user:
                        user_id = current_user.get("user_id")
                    
                    logger.info(
                        "Authentication action successful",
                        user_id=user_id,
                        success=True,
                        **audit_data
                    )
                
                return result
                
            except Exception as e:
                # Log de falha
                if log_failure:
                    # Tentar extrair informações do erro
                    error_info = {
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                    
                    logger.warning(
                        "Authentication action failed",
                        success=False,
                        error_info=error_info,
                        **audit_data
                    )
                
                # Re-raise a exceção
                raise
        
        return wrapper
    return decorator


def rate_limit_auth(
    max_attempts: int = 5,
    window_minutes: int = 15,
    key_func: Optional[Callable] = None
):
    """
    Decorator para rate limiting específico de autenticação.
    
    Args:
        max_attempts: Máximo de tentativas
        window_minutes: Janela de tempo em minutos
        key_func: Função para gerar chave do rate limit
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obter request object
            request = None
            for arg in args:
                if hasattr(arg, 'client'):
                    request = arg
                    break
            
            if not request:
                # Se não há request, pular rate limiting
                return await func(*args, **kwargs)
            
            # Gerar chave para rate limiting
            if key_func:
                rate_limit_key = key_func(request, *args, **kwargs)
            else:
                # Usar IP + endpoint como chave padrão
                client_ip = request.client.host if request.client else "unknown"
                rate_limit_key = f"auth_rate_limit:{client_ip}:{func.__name__}"
            
            try:
                # Obter auth manager para verificar tentativas
                auth_manager = get_auth_manager()
                
                # Verificar se IP/usuário está bloqueado
                # Implementação simplificada - expandir conforme necessário
                
                # Executar função
                result = await func(*args, **kwargs)
                
                # Limpar contador de tentativas em caso de sucesso
                # auth_manager.clear_failed_attempts(rate_limit_key)
                
                return result
                
            except HTTPException as e:
                # Registrar tentativa falhada para rate limiting
                # auth_manager.record_failed_attempt(rate_limit_key)
                
                # Verificar se deve bloquear
                # if auth_manager.should_block(rate_limit_key, max_attempts):
                #     raise HTTPException(
                #         status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                #         detail=f"Too many failed attempts. Try again in {window_minutes} minutes."
                #     )
                
                raise
            
            except Exception as e:
                logger.error("Rate limit check failed", error=str(e))
                # Continuar sem rate limiting em caso de erro
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def session_required(
    allow_expired: bool = False,
    refresh_on_access: bool = True
):
    """
    Decorator para requerer sessão válida.
    
    Args:
        allow_expired: Permitir sessões expiradas
        refresh_on_access: Atualizar timestamp da sessão no acesso
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Valid session required"
                )
            
            # Verificar se sessão está válida
            session_id = current_user.get("session_id")
            if not session_id:
                logger.warning(
                    "No session ID in token",
                    user_id=current_user.get("user_id"),
                    endpoint=func.__name__
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session"
                )
            
            # TODO: Implementar verificação de sessão no banco/cache
            # session_manager = get_session_manager()
            # session = session_manager.get_session(session_id)
            # 
            # if not session or (not allow_expired and session.is_expired()):
            #     raise HTTPException(
            #         status_code=status.HTTP_401_UNAUTHORIZED,
            #         detail="Session expired"
            #     )
            # 
            # if refresh_on_access:
            #     session_manager.refresh_session(session_id)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
