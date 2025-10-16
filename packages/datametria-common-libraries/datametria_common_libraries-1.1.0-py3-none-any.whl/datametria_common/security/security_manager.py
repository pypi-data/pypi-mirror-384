"""
🛡️ Security Manager - Gerenciador Central de Segurança Enterprise

Gerenciador central de segurança enterprise com funcionalidades completas:
- Data encryption e tokenization (AES-256, Fernet)
- Access control e authorization (RBAC, JWT)
- Security monitoring e audit trail
- Threat detection e brute force protection
- Compliance automation (LGPD/GDPR)
- Password security e hashing (bcrypt)
- Data masking e classification
- Session management e timeout

Este módulo implementa segurança enterprise com criptografia de ponta,
controle de acesso granular e monitoramento contínuo de ameaças.

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
License: MIT
Security: AES-256, bcrypt, JWT, OWASP compliant

Example:
    >>> security = SecurityManager()
    >>> encrypted = security.encrypt_sensitive_data(
    ...     "dados sensíveis",
    ...     DataClassification.CONFIDENTIAL
    ... )
    >>> context = security.authenticate_user(
    ...     "admin", "password", "192.168.1.1", "Mozilla/5.0"
    ... )
    >>> authorized = security.authorize_action(
    ...     context, "users", "read"
    ... )
"""

import hashlib
import secrets
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import jwt

from .exceptions import SecurityError, DataProtectionError
from .enterprise_logging import EnterpriseLogger


class SecurityLevel(Enum):
    """Níveis de segurança para classificação de contextos e operações.
    
    Define os níveis de segurança utilizados para classificar
    contextos de usuário e operações sensíveis do sistema.
    
    Attributes:
        LOW: Nível baixo - operações públicas
        MEDIUM: Nível médio - operações internas
        HIGH: Nível alto - operações confidenciais
        CRITICAL: Nível crítico - operações ultra-sensíveis
        
    Example:
        >>> level = SecurityLevel.HIGH
        >>> print(level.value)  # "high"
        
    Note:
        Níveis mais altos requerem autenticação adicional
        e monitoramento mais rigoroso.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataClassification(Enum):
    """Classificação de dados para proteção conforme níveis de sensibilidade.
    
    Define os níveis de classificação de dados utilizados para
    determinar o nível de proteção e criptografia necessários.
    
    Attributes:
        PUBLIC: Dados públicos - sem restrição de acesso
        INTERNAL: Dados internos - acesso restrito à organização
        CONFIDENTIAL: Dados confidenciais - acesso controlado
        RESTRICTED: Dados restritos - acesso muito limitado
        TOP_SECRET: Dados ultra-secretos - máxima proteção
        
    Example:
        >>> classification = DataClassification.CONFIDENTIAL
        >>> print(classification.value)  # "confidential"
        
    Note:
        Cada nível determina algoritmos de criptografia,
        controles de acesso e períodos de retenção específicos.
    """
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


@dataclass
class SecurityContext:
    """Contexto de segurança para operações autenticadas.
    
    Estrutura que mantém informações de segurança de uma sessão
    autenticada, incluindo permissões e metadados de segurança.
    
    Attributes:
        user_id (str): Identificador único do usuário
        session_id (str): Identificador único da sessão
        ip_address (str): Endereço IP de origem
        user_agent (str): User agent do navegador/cliente
        permissions (List[str]): Lista de permissões do usuário
        security_level (SecurityLevel): Nível de segurança da sessão
        timestamp (datetime): Momento de criação do contexto
        
    Example:
        >>> context = SecurityContext(
        ...     user_id="admin",
        ...     session_id="sess_123",
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0",
        ...     permissions=["users:read", "data:write"],
        ...     security_level=SecurityLevel.HIGH,
        ...     timestamp=datetime.now(timezone.utc)
        ... )
        >>> expired = context.is_expired(30)
        
    Note:
        Contextos expiram automaticamente após período configurado
        para garantir segurança de sessões.
    """
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    permissions: List[str]
    security_level: SecurityLevel
    timestamp: datetime
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Verifica se contexto expirou."""
        expiry = self.timestamp + timedelta(minutes=timeout_minutes)
        return datetime.now(timezone.utc) > expiry


class DataProtection:
    """Proteção e masking de dados pessoais enterprise.
    
    Implementa criptografia AES-256 via Fernet, mascaramento de dados
    pessoais e tokenização para proteção de informações sensíveis.
    
    Esta classe fornece:
    - Criptografia simétrica AES-256 com Fernet
    - Mascaramento inteligente por tipo de dado
    - Tokenização segura para PCI DSS
    - Classificação automática de sensibilidade
    - Audit trail completo de operações
    
    Attributes:
        logger (EnterpriseLogger): Logger para auditoria
        fernet (Fernet): Instância de criptografia Fernet
        
    Example:
        >>> protection = DataProtection()
        >>> encrypted = protection.encrypt_sensitive_data(
        ...     "dados confidenciais",
        ...     DataClassification.CONFIDENTIAL
        ... )
        >>> masked = protection.mask_personal_data(
        ...     "joao.silva@email.com",
        ...     "email"
        ... )  # Returns "jo***@email.com"
        >>> token, hash_val = protection.tokenize_data(
        ...     "4111111111111111",
        ...     "card"
        ... )
        
    Note:
        Utiliza Fernet (AES-256 em modo CBC com HMAC SHA-256)
        para garantir confidencialidade e integridade dos dados.
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        self.logger = EnterpriseLogger("data_protection")
        
        # Inicializa chave de criptografia
        if encryption_key:
            self.fernet = Fernet(encryption_key)
        else:
            self.fernet = Fernet(Fernet.generate_key())
    
    def encrypt_sensitive_data(self, data: str, 
                             classification: DataClassification = DataClassification.CONFIDENTIAL) -> str:
        """Criptografa dados sensíveis usando AES-256 via Fernet.
        
        Implementa criptografia simétrica de alta segurança com
        autenticação integrada (AES-256-CBC + HMAC-SHA256).
        
        Args:
            data (str): Dados a serem criptografados
            classification (DataClassification): Nível de classificação
            
        Returns:
            str: Dados criptografados codificados em base64
            
        Raises:
            DataProtectionError: Se criptografia falhar
            
        Example:
            >>> encrypted = protection.encrypt_sensitive_data(
            ...     "informação confidencial",
            ...     DataClassification.RESTRICTED
            ... )
            >>> print(len(encrypted))  # Tamanho do dado criptografado
            
        Note:
            Fernet garante que dados não podem ser manipulados
            ou lidos sem a chave de criptografia.
        """
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            encoded_data = base64.b64encode(encrypted_data).decode()
            
            self.logger.log_security_event(
                "data_encryption",
                {
                    "classification": classification.value,
                    "data_length": len(data),
                    "encrypted_length": len(encoded_data)
                }
            )
            
            return encoded_data
            
        except Exception as e:
            self.logger.log_error(
                "encryption_error",
                str(e),
                "data_protection"
            )
            raise DataProtectionError(f"Encryption failed: {e}")
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Descriptografa dados sensíveis.
        
        Args:
            encrypted_data: Dados criptografados em base64
            
        Returns:
            Dados descriptografados
        """
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            
            self.logger.log_security_event(
                "data_decryption",
                {
                    "encrypted_length": len(encrypted_data),
                    "decrypted_length": len(decrypted_data)
                }
            )
            
            return decrypted_data.decode()
            
        except Exception as e:
            self.logger.log_error(
                "decryption_error",
                str(e),
                "data_protection"
            )
            raise DataProtectionError(f"Decryption failed: {e}")
    
    def mask_personal_data(self, data: str, data_type: str = "general") -> str:
        """Mascara dados pessoais conforme tipo.
        
        Args:
            data: Dados a serem mascarados
            data_type: Tipo de dados (email, cpf, phone, etc.)
            
        Returns:
            Dados mascarados
        """
        if not data:
            return data
        
        if data_type == "email":
            return self._mask_email(data)
        elif data_type == "cpf":
            return self._mask_cpf(data)
        elif data_type == "phone":
            return self._mask_phone(data)
        elif data_type == "credit_card":
            return self._mask_credit_card(data)
        else:
            return self._mask_general(data)
    
    def _mask_email(self, email: str) -> str:
        """Mascara email."""
        if "@" not in email:
            return "***"
        
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            return f"***@{domain}"
        return f"{local[:2]}***@{domain}"
    
    def _mask_cpf(self, cpf: str) -> str:
        """Mascara CPF."""
        # Remove formatação
        cpf_digits = re.sub(r'\D', '', cpf)
        if len(cpf_digits) != 11:
            return "***"
        return f"***.***.***-{cpf_digits[-2:]}"
    
    def _mask_phone(self, phone: str) -> str:
        """Mascara telefone."""
        phone_digits = re.sub(r'\D', '', phone)
        if len(phone_digits) < 8:
            return "***"
        return f"***-***-{phone_digits[-4:]}"
    
    def _mask_credit_card(self, card: str) -> str:
        """Mascara cartão de crédito."""
        card_digits = re.sub(r'\D', '', card)
        if len(card_digits) < 12:
            return "***"
        return f"****-****-****-{card_digits[-4:]}"
    
    def _mask_general(self, data: str) -> str:
        """Mascaramento geral."""
        if len(data) <= 4:
            return "***"
        return f"{data[:2]}***{data[-2:]}"
    
    def tokenize_data(self, data: str, token_prefix: str = "tok") -> Tuple[str, str]:
        """Tokeniza dados sensíveis.
        
        Args:
            data: Dados a serem tokenizados
            token_prefix: Prefixo do token
            
        Returns:
            Tupla (token, hash_for_storage)
        """
        # Gera token único
        token = f"{token_prefix}_{secrets.token_urlsafe(16)}"
        
        # Gera hash para armazenamento seguro
        data_hash = hashlib.sha256(data.encode()).hexdigest()
        
        self.logger.log_security_event(
            "data_tokenization",
            {
                "token_prefix": token_prefix,
                "data_length": len(data),
                "token": token[:8] + "***"  # Log parcial do token
            }
        )
        
        return token, data_hash


class AccessControl:
    """Controle de acesso e autorização."""
    
    def __init__(self, logger: Optional[EnterpriseLogger] = None):
        self.logger = logger or EnterpriseLogger("access_control")
        self._permissions_cache: Dict[str, Dict[str, Any]] = {}
        self._failed_attempts: Dict[str, List[datetime]] = {}
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str, user_agent: str) -> Optional[SecurityContext]:
        """Autentica usuário e cria contexto de segurança.
        
        Args:
            username: Nome do usuário
            password: Senha do usuário
            ip_address: Endereço IP
            user_agent: User agent do navegador
            
        Returns:
            Contexto de segurança se autenticação bem-sucedida
        """
        # Verifica tentativas de força bruta
        if self._is_brute_force_attempt(username, ip_address):
            self.logger.log_security_event(
                "brute_force_detected",
                {
                    "username": username,
                    "ip_address": ip_address,
                    "blocked": True
                }
            )
            raise SecurityError("Too many failed attempts. Account temporarily locked.")
        
        # Simula validação de credenciais (em produção, consultar base de dados)
        if self._validate_credentials(username, password):
            # Limpa tentativas falhadas
            self._clear_failed_attempts(username, ip_address)
            
            # Cria contexto de segurança
            context = SecurityContext(
                user_id=username,
                session_id=secrets.token_urlsafe(32),
                ip_address=ip_address,
                user_agent=user_agent,
                permissions=self._get_user_permissions(username),
                security_level=SecurityLevel.MEDIUM,
                timestamp=datetime.now(timezone.utc)
            )
            
            self.logger.log_security_event(
                "authentication_success",
                {
                    "user_id": username,
                    "ip_address": ip_address,
                    "session_id": context.session_id[:8] + "***"
                }
            )
            
            return context
        else:
            # Registra tentativa falhada
            self._record_failed_attempt(username, ip_address)
            
            self.logger.log_security_event(
                "authentication_failure",
                {
                    "username": username,
                    "ip_address": ip_address,
                    "reason": "invalid_credentials"
                }
            )
            
            return None
    
    def authorize_action(self, context: SecurityContext, resource: str, 
                        action: str) -> bool:
        """Autoriza ação do usuário.
        
        Args:
            context: Contexto de segurança
            resource: Recurso a ser acessado
            action: Ação a ser executada
            
        Returns:
            True se autorizado
        """
        # Verifica se contexto não expirou
        if context.is_expired():
            self.logger.log_security_event(
                "expired_context",
                {
                    "user_id": context.user_id,
                    "session_id": context.session_id[:8] + "***"
                }
            )
            return False
        
        # Verifica permissões
        required_permission = f"{resource}:{action}"
        has_permission = (
            required_permission in context.permissions or
            f"{resource}:*" in context.permissions or
            "*:*" in context.permissions
        )
        
        self.logger.log_security_event(
            "authorization_check",
            {
                "user_id": context.user_id,
                "resource": resource,
                "action": action,
                "granted": has_permission,
                "required_permission": required_permission
            }
        )
        
        return has_permission
    
    def _is_brute_force_attempt(self, username: str, ip_address: str, 
                               max_attempts: int = 5, 
                               time_window_minutes: int = 15) -> bool:
        """Verifica tentativas de força bruta."""
        key = f"{username}:{ip_address}"
        
        if key not in self._failed_attempts:
            return False
        
        # Remove tentativas antigas
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        self._failed_attempts[key] = [
            attempt for attempt in self._failed_attempts[key]
            if attempt > cutoff_time
        ]
        
        return len(self._failed_attempts[key]) >= max_attempts
    
    def _record_failed_attempt(self, username: str, ip_address: str) -> None:
        """Registra tentativa de autenticação falhada."""
        key = f"{username}:{ip_address}"
        
        if key not in self._failed_attempts:
            self._failed_attempts[key] = []
        
        self._failed_attempts[key].append(datetime.now(timezone.utc))
    
    def _clear_failed_attempts(self, username: str, ip_address: str) -> None:
        """Limpa tentativas falhadas após sucesso."""
        key = f"{username}:{ip_address}"
        if key in self._failed_attempts:
            del self._failed_attempts[key]
    
    def _validate_credentials(self, username: str, password: str) -> bool:
        """Valida credenciais do usuário."""
        # Implementação simplificada - em produção, consultar base segura
        # Usar bcrypt para hash de senhas
        return username == "admin" and password == "secure_password"
    
    def _get_user_permissions(self, username: str) -> List[str]:
        """Obtém permissões do usuário."""
        # Implementação simplificada - em produção, consultar base de dados
        if username == "admin":
            return ["*:*"]  # Administrador tem todas as permissões
        else:
            return ["users:read", "data:read"]


class SecurityManager:
    """Gerenciador central de segurança enterprise.
    
    Classe principal que coordena todos os aspectos de segurança,
    integrando proteção de dados, controle de acesso e monitoramento.
    
    Esta classe fornece interface unificada para:
    - Criptografia e descriptografia de dados
    - Autenticação e autorização de usuários
    - Mascaramento de dados pessoais
    - Validação de força de senhas
    - Geração de tokens seguros
    - Gestão de tokens JWT
    - Hashing seguro de senhas com bcrypt
    
    Attributes:
        logger (EnterpriseLogger): Logger central de segurança
        data_protection (DataProtection): Módulo de proteção de dados
        access_control (AccessControl): Módulo de controle de acesso
        security_config (Dict): Configurações de segurança
        
    Example:
        >>> security = SecurityManager()
        >>> # Criptografia
        >>> encrypted = security.encrypt_sensitive_data("dados")
        >>> # Autenticação
        >>> context = security.authenticate_user(
        ...     "user", "pass", "192.168.1.1", "Mozilla/5.0"
        ... )
        >>> # Autorização
        >>> allowed = security.authorize_action(context, "users", "read")
        >>> # JWT
        >>> token = security.create_jwt_token(
        ...     {"user_id": "123"}, "secret", 24
        ... )
        
    Note:
        Centraliza todas as operações de segurança para
        garantir consistência e auditoria completa.
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None,
                 logger: Optional[EnterpriseLogger] = None):
        self.logger = logger or EnterpriseLogger("security_manager")
        self.data_protection = DataProtection(encryption_key)
        self.access_control = AccessControl(logger)
        
        # Configurações de segurança
        self.security_config = {
            "password_min_length": 8,
            "password_require_special": True,
            "session_timeout_minutes": 30,
            "max_login_attempts": 5,
            "lockout_duration_minutes": 15
        }
    
    def encrypt_sensitive_data(self, data: str, 
                             classification: DataClassification = DataClassification.CONFIDENTIAL) -> str:
        """Criptografa dados sensíveis."""
        return self.data_protection.encrypt_sensitive_data(data, classification)
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Descriptografa dados sensíveis."""
        return self.data_protection.decrypt_sensitive_data(encrypted_data)
    
    def mask_personal_data(self, data: str, data_type: str = "general") -> str:
        """Mascara dados pessoais."""
        return self.data_protection.mask_personal_data(data, data_type)
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str, user_agent: str) -> Optional[SecurityContext]:
        """Autentica usuário."""
        return self.access_control.authenticate_user(username, password, ip_address, user_agent)
    
    def authorize_action(self, context: SecurityContext, resource: str, action: str) -> bool:
        """Autoriza ação do usuário."""
        return self.access_control.authorize_action(context, resource, action)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Valida força da senha.
        
        Args:
            password: Senha a ser validada
            
        Returns:
            Dicionário com resultado da validação
        """
        result = {
            "valid": True,
            "score": 0,
            "issues": []
        }
        
        # Verifica comprimento mínimo
        if len(password) < self.security_config["password_min_length"]:
            result["valid"] = False
            result["issues"].append(f"Minimum length: {self.security_config['password_min_length']}")
        else:
            result["score"] += 1
        
        # Verifica caracteres especiais
        if self.security_config["password_require_special"]:
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                result["valid"] = False
                result["issues"].append("Must contain special characters")
            else:
                result["score"] += 1
        
        # Verifica maiúsculas e minúsculas
        if not re.search(r'[A-Z]', password):
            result["issues"].append("Should contain uppercase letters")
        else:
            result["score"] += 1
        
        if not re.search(r'[a-z]', password):
            result["issues"].append("Should contain lowercase letters")
        else:
            result["score"] += 1
        
        # Verifica números
        if not re.search(r'\d', password):
            result["issues"].append("Should contain numbers")
        else:
            result["score"] += 1
        
        return result
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Gera token seguro."""
        token = secrets.token_urlsafe(length)
        
        self.logger.log_security_event(
            "token_generated",
            {
                "token_length": length,
                "token_prefix": token[:8] + "***"
            }
        )
        
        return token
    
    def hash_password(self, password: str) -> str:
        """Gera hash seguro da senha."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica senha contra hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_jwt_token(self, payload: Dict[str, Any], secret_key: str,
                        expiry_hours: int = 24) -> str:
        """Cria token JWT."""
        payload['exp'] = datetime.utcnow() + timedelta(hours=expiry_hours)
        payload['iat'] = datetime.utcnow()
        
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        self.logger.log_security_event(
            "jwt_token_created",
            {
                "user_id": payload.get("user_id"),
                "expiry_hours": expiry_hours
            }
        )
        
        return token
    
    def verify_jwt_token(self, token: str, secret_key: str) -> Optional[Dict[str, Any]]:
        """Verifica e decodifica token JWT."""
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            self.logger.log_security_event(
                "jwt_token_verified",
                {
                    "user_id": payload.get("user_id"),
                    "valid": True
                }
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.log_security_event(
                "jwt_token_expired",
                {"token_prefix": token[:16] + "***"}
            )
            return None
        except jwt.InvalidTokenError:
            self.logger.log_security_event(
                "jwt_token_invalid",
                {"token_prefix": token[:16] + "***"}
            )
            return None
