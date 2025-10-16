"""
🔐 Auth Manager - DATAMETRIA Authentication

Gerenciador principal de autenticação integrando todos os componentes.
"""

from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import structlog

from datametria_common.core import BaseConfig
from datametria_common.security.security_manager import SecurityManager
from .jwt_manager import JWTManager

logger = structlog.get_logger(__name__)


class AuthManager:
    """
    Gerenciador principal de autenticação DATAMETRIA.
    
    Integra JWT, OAuth2, MFA e políticas de segurança.
    Reutiliza SecurityManager para operações criptográficas.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa AuthManager.
        
        Args:
            config: Configurações de autenticação
        """
        self.config = BaseConfig()
        self.security_manager = SecurityManager()
        
        # Configurações padrão
        auth_config = config or {}
        self.jwt_secret = auth_config.get('jwt_secret_key') or self.security_manager.get_encryption_key()
        self.jwt_algorithm = auth_config.get('jwt_algorithm', 'HS256')
        self.access_token_expire_minutes = auth_config.get('access_token_expire_minutes', 30)
        self.refresh_token_expire_days = auth_config.get('refresh_token_expire_days', 7)
        
        # Políticas de senha
        self.password_min_length = auth_config.get('password_min_length', 8)
        self.password_require_uppercase = auth_config.get('password_require_uppercase', True)
        self.password_require_lowercase = auth_config.get('password_require_lowercase', True)
        self.password_require_numbers = auth_config.get('password_require_numbers', True)
        self.password_require_symbols = auth_config.get('password_require_symbols', False)
        
        # Políticas de segurança
        self.max_login_attempts = auth_config.get('max_login_attempts', 5)
        self.lockout_duration_minutes = auth_config.get('lockout_duration_minutes', 15)
        
        # Inicializar JWT Manager
        self.jwt_manager = JWTManager(
            secret_key=self.jwt_secret,
            algorithm=self.jwt_algorithm,
            access_token_expire_minutes=self.access_token_expire_minutes,
            refresh_token_expire_days=self.refresh_token_expire_days
        )
        
        # Cache para tentativas de login falhadas
        self._failed_login_attempts = {}
        self._locked_accounts = {}
        
        logger.info(
            "AuthManager initialized",
            jwt_algorithm=self.jwt_algorithm,
            access_expire_minutes=self.access_token_expire_minutes,
            max_login_attempts=self.max_login_attempts
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash da senha usando SecurityManager.
        
        Args:
            password: Senha em texto plano
            
        Returns:
            str: Hash da senha
        """
        return self.security_manager.hash_password(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica senha usando SecurityManager.
        
        Args:
            plain_password: Senha em texto plano
            hashed_password: Hash da senha
            
        Returns:
            bool: True se senha correta
        """
        return self.security_manager.verify_password(plain_password, hashed_password)
    
    def validate_password_policy(self, password: str) -> List[str]:
        """
        Valida senha contra políticas de segurança.
        
        Args:
            password: Senha para validar
            
        Returns:
            List[str]: Lista de erros (vazia se válida)
        """
        errors = []
        
        if len(password) < self.password_min_length:
            errors.append(f"Senha deve ter pelo menos {self.password_min_length} caracteres")
        
        if self.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Senha deve conter pelo menos uma letra maiúscula")
        
        if self.password_require_lowercase and not any(c.islower() for c in password):
            errors.append("Senha deve conter pelo menos uma letra minúscula")
        
        if self.password_require_numbers and not any(c.isdigit() for c in password):
            errors.append("Senha deve conter pelo menos um número")
        
        if self.password_require_symbols:
            symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in symbols for c in password):
                errors.append("Senha deve conter pelo menos um símbolo especial")
        
        return errors
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria access token JWT.
        
        Args:
            data: Dados do usuário
            expires_delta: Tempo de expiração customizado
            
        Returns:
            str: Access token
        """
        return self.jwt_manager.create_access_token(data, expires_delta)
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria refresh token JWT.
        
        Args:
            data: Dados do usuário
            expires_delta: Tempo de expiração customizado
            
        Returns:
            str: Refresh token
        """
        return self.jwt_manager.create_refresh_token(data, expires_delta)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica token JWT.
        
        Args:
            token: Token para verificar
            
        Returns:
            Dict: Payload do token ou None se inválido
        """
        return self.jwt_manager.verify_token(token)
    
    def blacklist_token(self, token: str) -> None:
        """
        Adiciona token à blacklist.
        
        Args:
            token: Token para blacklistar
        """
        self.jwt_manager.blacklist_token(token)
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Renova access token usando refresh token.
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            str: Novo access token ou None se inválido
        """
        return self.jwt_manager.refresh_access_token(refresh_token)
    
    def record_failed_login(self, identifier: str) -> None:
        """
        Registra tentativa de login falhada.
        
        Args:
            identifier: Email ou username do usuário
        """
        now = datetime.utcnow()
        
        if identifier not in self._failed_login_attempts:
            self._failed_login_attempts[identifier] = []
        
        # Adicionar tentativa atual
        self._failed_login_attempts[identifier].append(now)
        
        # Remover tentativas antigas (últimas 24h)
        cutoff = now - timedelta(hours=24)
        self._failed_login_attempts[identifier] = [
            attempt for attempt in self._failed_login_attempts[identifier]
            if attempt > cutoff
        ]
        
        # Verificar se deve bloquear conta
        if len(self._failed_login_attempts[identifier]) >= self.max_login_attempts:
            self._locked_accounts[identifier] = now + timedelta(minutes=self.lockout_duration_minutes)
            
            logger.warning(
                "Account locked due to failed login attempts",
                identifier=identifier,
                attempts=len(self._failed_login_attempts[identifier]),
                locked_until=self._locked_accounts[identifier].isoformat()
            )
        
        logger.info(
            "Failed login attempt recorded",
            identifier=identifier,
            total_attempts=len(self._failed_login_attempts[identifier])
        )
    
    def clear_failed_login_attempts(self, identifier: str) -> None:
        """
        Limpa tentativas de login falhadas após login bem-sucedido.
        
        Args:
            identifier: Email ou username do usuário
        """
        if identifier in self._failed_login_attempts:
            del self._failed_login_attempts[identifier]
        
        if identifier in self._locked_accounts:
            del self._locked_accounts[identifier]
        
        logger.info("Failed login attempts cleared", identifier=identifier)
    
    def is_account_locked(self, identifier: str) -> bool:
        """
        Verifica se conta está bloqueada.
        
        Args:
            identifier: Email ou username do usuário
            
        Returns:
            bool: True se conta bloqueada
        """
        if identifier not in self._locked_accounts:
            return False
        
        lockout_until = self._locked_accounts[identifier]
        
        # Verificar se lockout expirou
        if datetime.utcnow() > lockout_until:
            del self._locked_accounts[identifier]
            if identifier in self._failed_login_attempts:
                del self._failed_login_attempts[identifier]
            
            logger.info("Account lockout expired", identifier=identifier)
            return False
        
        return True
    
    def get_failed_login_attempts(self, identifier: str) -> int:
        """
        Obtém número de tentativas de login falhadas.
        
        Args:
            identifier: Email ou username do usuário
            
        Returns:
            int: Número de tentativas
        """
        if identifier not in self._failed_login_attempts:
            return 0
        
        # Limpar tentativas antigas
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=24)
        self._failed_login_attempts[identifier] = [
            attempt for attempt in self._failed_login_attempts[identifier]
            if attempt > cutoff
        ]
        
        return len(self._failed_login_attempts[identifier])
    
    def generate_password_reset_token(self, user_id: int) -> str:
        """
        Gera token para reset de senha.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            str: Token de reset
        """
        data = {
            "user_id": user_id,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)  # Expira em 1 hora
        }
        
        token = self.security_manager.generate_secure_token(str(data))
        
        logger.info("Password reset token generated", user_id=user_id)
        
        return token
    
    def verify_password_reset_token(self, token: str) -> Optional[int]:
        """
        Verifica token de reset de senha.
        
        Args:
            token: Token de reset
            
        Returns:
            int: User ID se válido, None se inválido
        """
        try:
            # Implementação simplificada - em produção usar JWT
            # Por ora, usar SecurityManager para validação básica
            if self.security_manager.validate_token(token):
                # Extrair user_id do token (implementação específica)
                # Por simplicidade, retornar None - implementar conforme necessário
                return None
            
        except Exception as e:
            logger.error("Failed to verify password reset token", error=str(e))
        
        return None
    
    def create_session_token(self, user_id: int, device_info: Optional[Dict] = None) -> str:
        """
        Cria token de sessão para dispositivo específico.
        
        Args:
            user_id: ID do usuário
            device_info: Informações do dispositivo
            
        Returns:
            str: Token de sessão
        """
        session_data = {
            "user_id": user_id,
            "type": "session",
            "device_info": device_info or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        return self.security_manager.generate_secure_token(str(session_data))
    
    def get_security_manager(self) -> SecurityManager:
        """
        Retorna instância do SecurityManager.
        
        Returns:
            SecurityManager: Instância do security manager
        """
        return self.security_manager
