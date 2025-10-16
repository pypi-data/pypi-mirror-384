"""
🔐 JWT Manager - DATAMETRIA Authentication

Gerenciamento de tokens JWT com integração ao SecurityManager DATAMETRIA.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from jose import JWTError, jwt
import structlog

from datametria_common.core import BaseConfig
from datametria_common.security.security_manager import SecurityManager

logger = structlog.get_logger(__name__)


class JWTManager:
    """
    Gerenciador de tokens JWT integrado ao SecurityManager DATAMETRIA.
    
    Reutiliza o SecurityManager existente para operações criptográficas
    e adiciona funcionalidades específicas de JWT.
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        """
        Inicializa JWT Manager.
        
        Args:
            secret_key: Chave secreta (usa SecurityManager se None)
            algorithm: Algoritmo JWT
            access_token_expire_minutes: Expiração do access token
            refresh_token_expire_days: Expiração do refresh token
        """
        self.config = BaseConfig()
        self.security_manager = SecurityManager()
        
        # Usar SecurityManager para chave se não fornecida
        self.secret_key = secret_key or self.security_manager.get_encryption_key()
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # Cache para tokens blacklistados (integração com Redis se disponível)
        self._blacklisted_tokens = set()
        
        logger.info(
            "JWT Manager initialized",
            algorithm=algorithm,
            access_expire_minutes=access_token_expire_minutes,
            refresh_expire_days=refresh_token_expire_days
        )
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria access token JWT.
        
        Args:
            data: Dados do payload
            expires_delta: Tempo de expiração customizado
            
        Returns:
            str: Token JWT codificado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Payload padrão DATAMETRIA
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": self.security_manager.generate_token(),  # JWT ID único
            "iss": "datametria-api",  # Issuer
            "aud": "datametria-client"  # Audience
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            logger.info(
                "Access token created",
                user_id=data.get("user_id"),
                expires_at=expire.isoformat(),
                jti=to_encode["jti"]
            )
            
            return encoded_jwt
            
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria refresh token JWT.
        
        Args:
            data: Dados do payload
            expires_delta: Tempo de expiração customizado
            
        Returns:
            str: Refresh token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        # Payload para refresh token
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": self.security_manager.generate_token(),
            "iss": "datametria-api",
            "aud": "datametria-client"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            logger.info(
                "Refresh token created",
                user_id=data.get("user_id"),
                expires_at=expire.isoformat(),
                jti=to_encode["jti"]
            )
            
            return encoded_jwt
            
        except Exception as e:
            logger.error("Failed to create refresh token", error=str(e))
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica e decodifica token JWT.
        
        Args:
            token: Token JWT para verificar
            
        Returns:
            Dict: Payload decodificado ou None se inválido
        """
        try:
            # Verificar se token está na blacklist
            if self.is_token_blacklisted(token):
                logger.warning("Attempted to use blacklisted token")
                return None
            
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="datametria-client",
                issuer="datametria-api"
            )
            
            # Verificar se token não expirou
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                logger.warning("Token expired", exp=exp)
                return None
            
            logger.debug(
                "Token verified successfully",
                user_id=payload.get("user_id"),
                token_type=payload.get("type"),
                jti=payload.get("jti")
            )
            
            return payload
            
        except JWTError as e:
            logger.warning("JWT verification failed", error=str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error verifying token", error=str(e))
            return None
    
    def blacklist_token(self, token: str) -> None:
        """
        Adiciona token à blacklist.
        
        Args:
            token: Token para blacklistar
        """
        try:
            # Decodificar para obter JTI
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Não verificar expiração
            )
            
            jti = payload.get("jti")
            if jti:
                self._blacklisted_tokens.add(jti)
                
                # TODO: Integrar com Redis para persistência
                # if self.redis_client:
                #     self.redis_client.sadd("blacklisted_tokens", jti)
                
                logger.info("Token blacklisted", jti=jti)
            
        except Exception as e:
            logger.error("Failed to blacklist token", error=str(e))
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Verifica se token está na blacklist.
        
        Args:
            token: Token para verificar
            
        Returns:
            bool: True se blacklistado
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            
            jti = payload.get("jti")
            if jti:
                is_blacklisted = jti in self._blacklisted_tokens
                
                # TODO: Verificar também no Redis
                # if self.redis_client:
                #     is_blacklisted = is_blacklisted or self.redis_client.sismember("blacklisted_tokens", jti)
                
                return is_blacklisted
            
            return False
            
        except Exception:
            return True  # Se não conseguir decodificar, considerar blacklistado
    
    def get_token_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtém payload do token sem verificar assinatura (para debug).
        
        Args:
            token: Token JWT
            
        Returns:
            Dict: Payload ou None
        """
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        except Exception:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Gera novo access token usando refresh token.
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            str: Novo access token ou None se inválido
        """
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            logger.warning("Invalid refresh token provided")
            return None
        
        # Criar novo access token com dados do refresh token
        access_data = {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
        
        new_access_token = self.create_access_token(access_data)
        
        logger.info(
            "Access token refreshed",
            user_id=payload.get("user_id"),
            refresh_jti=payload.get("jti")
        )
        
        return new_access_token
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Obtém data de expiração do token.
        
        Args:
            token: Token JWT
            
        Returns:
            datetime: Data de expiração ou None
        """
        payload = self.get_token_payload(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"])
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Verifica se token está expirado.
        
        Args:
            token: Token JWT
            
        Returns:
            bool: True se expirado
        """
        expiry = self.get_token_expiry(token)
        if expiry:
            return expiry < datetime.utcnow()
        return True
