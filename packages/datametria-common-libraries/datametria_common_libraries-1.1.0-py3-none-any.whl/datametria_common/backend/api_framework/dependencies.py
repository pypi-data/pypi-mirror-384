"""
🔧 Dependencies - DATAMETRIA API Framework

Sistema de injeção de dependência com integração aos componentes DATAMETRIA.
"""

from functools import lru_cache
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import structlog

from datametria_common.core import BaseConfig
from datametria_common.security.security_manager import SecurityManager

logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


@lru_cache()
def get_settings() -> BaseConfig:
    """
    Dependency para obter configurações DATAMETRIA.
    
    Returns:
        BaseConfig: Instância de configuração
    """
    return BaseConfig()


@lru_cache()
def get_security_manager() -> SecurityManager:
    """
    Dependency para obter SecurityManager DATAMETRIA.
    
    Returns:
        SecurityManager: Instância do security manager
    """
    try:
        return SecurityManager()
    except Exception as e:
        logger.error("Failed to initialize SecurityManager", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security manager initialization failed"
        )


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco de dados.
    
    Yields:
        Session: Sessão SQLAlchemy
    """
    try:
        # Importação dinâmica para evitar dependência circular
        from datametria_common.database.connectors.multi_sgbd_orm import MultiSGBDORM
        
        # Obter configuração
        config = get_settings()
        
        # Criar ORM manager
        orm_manager = MultiSGBDORM({
            "default": {
                "url": config.DATABASE_URL,
                "echo": config.DATABASE_ECHO
            }
        })
        
        # Obter sessão
        db = orm_manager.get_session("default")
        
        try:
            yield db
        finally:
            db.close()
            
    except ImportError:
        logger.warning("Database components not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available"
        )
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )


def get_cache():
    """
    Dependency para obter instância do cache Redis.
    
    Returns:
        Cache instance ou None se não disponível
    """
    try:
        # Importação dinâmica
        from datametria_common.utilities.cache_manager import CacheManager
        
        config = get_settings()
        
        return CacheManager(
            host=getattr(config, 'REDIS_HOST', 'localhost'),
            port=getattr(config, 'REDIS_PORT', 6379),
            db=getattr(config, 'REDIS_DB', 0)
        )
        
    except ImportError:
        logger.warning("Cache components not available")
        return None
    except Exception as e:
        logger.error("Cache connection failed", error=str(e))
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    security_manager: SecurityManager = Depends(get_security_manager),
    db: Session = Depends(get_db)
):
    """
    Dependency para obter usuário atual autenticado.
    
    Args:
        credentials: Credenciais HTTP Bearer
        security_manager: Instância do SecurityManager
        db: Sessão do banco de dados
        
    Returns:
        User: Usuário autenticado
        
    Raises:
        HTTPException: Se autenticação falhar
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Decodificar token JWT
        payload = security_manager.decode_jwt_token(credentials.credentials)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Buscar usuário no banco (implementação específica do projeto)
        # Esta parte deve ser customizada conforme o modelo de usuário
        try:
            from datametria_common.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if not user.active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
            
            return user
            
        except ImportError:
            # Se modelo User não estiver disponível, retornar payload do token
            logger.warning("User model not available, returning token payload")
            return payload
        
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Dependency para obter usuário ativo atual.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        User: Usuário ativo
        
    Raises:
        HTTPException: Se usuário não estiver ativo
    """
    # Se for um dict (payload do token), verificar se tem flag active
    if isinstance(current_user, dict):
        if not current_user.get("active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        return current_user
    
    # Se for objeto User, verificar atributo active
    if hasattr(current_user, 'active') and not current_user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return current_user


async def get_admin_user(
    current_user = Depends(get_current_active_user)
):
    """
    Dependency para obter usuário com privilégios de admin.
    
    Args:
        current_user: Usuário atual ativo
        
    Returns:
        User: Usuário admin
        
    Raises:
        HTTPException: Se usuário não for admin
    """
    # Verificar se é admin (implementação específica do projeto)
    is_admin = False
    
    if isinstance(current_user, dict):
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
    else:
        is_admin = (
            getattr(current_user, 'role', None) == "admin" or
            getattr(current_user, 'is_admin', False)
        )
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def get_vault_manager():
    """
    Dependency para obter VaultManager DATAMETRIA.
    
    Returns:
        VaultManager ou None se não disponível
    """
    try:
        from datametria_common.utilities.vault_manager import VaultManager
        
        config = get_settings()
        
        return VaultManager(
            vault_url=getattr(config, 'VAULT_URL', None),
            vault_token=getattr(config, 'VAULT_TOKEN', None)
        )
        
    except ImportError:
        logger.warning("Vault components not available")
        return None
    except Exception as e:
        logger.error("Vault connection failed", error=str(e))
        return None


def get_rate_limiter():
    """
    Dependency para obter rate limiter.
    
    Returns:
        RateLimiter ou None se não disponível
    """
    try:
        from datametria_common.backend.rate_limiting import RateLimiter
        
        cache = get_cache()
        if not cache:
            logger.warning("Cache not available for rate limiting")
            return None
        
        return RateLimiter(cache_backend=cache)
        
    except ImportError:
        logger.warning("Rate limiting components not available")
        return None
    except Exception as e:
        logger.error("Rate limiter initialization failed", error=str(e))
        return None


# Aliases para compatibilidade
get_config = get_settings
get_security = get_security_manager
