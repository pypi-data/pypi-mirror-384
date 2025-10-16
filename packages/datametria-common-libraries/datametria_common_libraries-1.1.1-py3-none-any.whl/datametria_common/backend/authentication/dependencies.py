"""
🔐 Authentication Dependencies - DATAMETRIA Authentication

Dependencies para autenticação integradas ao API Framework.
"""

from functools import lru_cache
from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from datametria_common.backend.api_framework.dependencies import get_db, get_security_manager
from .auth_manager import AuthManager
from .models import UserRole, UserProfile

logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


@lru_cache()
def get_auth_manager() -> AuthManager:
    """
    Dependency para obter AuthManager DATAMETRIA.
    
    Returns:
        AuthManager: Instância do auth manager
    """
    try:
        return AuthManager()
    except Exception as e:
        logger.error("Failed to initialize AuthManager", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_manager: AuthManager = Depends(get_auth_manager),
    request: Optional[Request] = None
) -> Optional[dict]:
    """
    Dependency para obter usuário atual (opcional).
    
    Args:
        credentials: Credenciais HTTP Bearer
        auth_manager: Instância do AuthManager
        request: Request FastAPI (para logging)
        
    Returns:
        dict: Dados do usuário ou None se não autenticado
    """
    if not credentials:
        return None
    
    try:
        # Verificar token
        payload = auth_manager.verify_token(credentials.credentials)
        
        if not payload:
            logger.warning(
                "Invalid token provided",
                ip_address=request.client.host if request and request.client else None
            )
            return None
        
        # Extrair dados do usuário
        user_data = {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "token_type": payload.get("type"),
            "jti": payload.get("jti")
        }
        
        logger.debug(
            "User authenticated successfully",
            user_id=user_data["user_id"],
            email=user_data["email"]
        )
        
        return user_data
        
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        return None


async def get_current_active_user(
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """
    Dependency para obter usuário ativo atual (obrigatório).
    
    Args:
        current_user: Usuário atual
        
    Returns:
        dict: Dados do usuário ativo
        
    Raises:
        HTTPException: Se usuário não autenticado ou inativo
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verificar se usuário está ativo (implementação específica do projeto)
    # Por ora, assumir que todos os usuários com token válido estão ativos
    
    return current_user


async def get_admin_user(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Dependency para obter usuário admin.
    
    Args:
        current_user: Usuário atual ativo
        
    Returns:
        dict: Dados do usuário admin
        
    Raises:
        HTTPException: Se usuário não for admin
    """
    user_role = current_user.get("role")
    
    if user_role != UserRole.ADMIN:
        logger.warning(
            "Admin access denied",
            user_id=current_user.get("user_id"),
            role=user_role
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def require_role(required_role: UserRole) -> Callable:
    """
    Factory para criar dependency que requer role específico.
    
    Args:
        required_role: Role necessário
        
    Returns:
        Callable: Dependency function
    """
    async def role_checker(
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        user_role = current_user.get("role")
        
        if user_role != required_role:
            logger.warning(
                "Role access denied",
                user_id=current_user.get("user_id"),
                user_role=user_role,
                required_role=required_role
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        
        return current_user
    
    return role_checker


def require_roles(required_roles: List[UserRole]) -> Callable:
    """
    Factory para criar dependency que requer um dos roles especificados.
    
    Args:
        required_roles: Lista de roles aceitos
        
    Returns:
        Callable: Dependency function
    """
    async def roles_checker(
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        user_role = current_user.get("role")
        
        if user_role not in required_roles:
            logger.warning(
                "Roles access denied",
                user_id=current_user.get("user_id"),
                user_role=user_role,
                required_roles=required_roles
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return roles_checker


def require_permissions(required_permissions: List[str]) -> Callable:
    """
    Factory para criar dependency que requer permissões específicas.
    
    Args:
        required_permissions: Lista de permissões necessárias
        
    Returns:
        Callable: Dependency function
    """
    async def permissions_checker(
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        # Implementação básica - expandir conforme necessário
        user_role = current_user.get("role")
        
        # Admin tem todas as permissões
        if user_role == UserRole.ADMIN:
            return current_user
        
        # Implementar lógica de permissões específica do projeto
        # Por ora, apenas verificar se usuário tem role adequado
        
        logger.warning(
            "Permissions access denied",
            user_id=current_user.get("user_id"),
            user_role=user_role,
            required_permissions=required_permissions
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permissions required: {', '.join(required_permissions)}"
        )
    
    return permissions_checker


async def get_optional_user(
    current_user: Optional[dict] = Depends(get_current_user)
) -> Optional[dict]:
    """
    Dependency para obter usuário opcional (não levanta exceção se não autenticado).
    
    Args:
        current_user: Usuário atual (pode ser None)
        
    Returns:
        dict: Dados do usuário ou None
    """
    return current_user


async def verify_token_validity(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: AuthManager = Depends(get_auth_manager)
) -> dict:
    """
    Dependency para verificar apenas validade do token (sem buscar usuário).
    
    Args:
        credentials: Credenciais HTTP Bearer
        auth_manager: Instância do AuthManager
        
    Returns:
        dict: Payload do token
        
    Raises:
        HTTPException: Se token inválido
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = auth_manager.verify_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload


async def get_session_info(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """
    Dependency para obter informações da sessão atual.
    
    Args:
        request: Request FastAPI
        current_user: Usuário atual
        
    Returns:
        dict: Informações da sessão
    """
    session_info = {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "is_authenticated": current_user is not None,
        "user_id": current_user.get("user_id") if current_user else None,
        "timestamp": logger._context.get("timestamp") if hasattr(logger, '_context') else None
    }
    
    return session_info


# Aliases para compatibilidade com API Framework
get_current_authenticated_user = get_current_active_user
require_admin = lambda: require_role(UserRole.ADMIN)
require_user = lambda: require_role(UserRole.USER)
require_moderator = lambda: require_role(UserRole.MODERATOR)
