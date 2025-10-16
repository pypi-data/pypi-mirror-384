"""
🔐 Authentication Models - DATAMETRIA Authentication

Modelos Pydantic para autenticação integrados ao API Framework.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from enum import Enum

from datametria_common.backend.api_framework.models import DatametriaBaseModel


class AuthProvider(str, Enum):
    """Provedores de autenticação suportados."""
    LOCAL = "local"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"


class UserRole(str, Enum):
    """Roles de usuário."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    MODERATOR = "moderator"


class LoginRequest(DatametriaBaseModel):
    """Requisição de login."""
    
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., min_length=1, description="Senha do usuário")
    remember_me: bool = Field(False, description="Manter login ativo")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Informações do dispositivo")
    
    @validator('email')
    def validate_email(cls, v):
        """Normaliza email."""
        return v.lower().strip()


class LoginResponse(DatametriaBaseModel):
    """Resposta de login bem-sucedido."""
    
    access_token: str = Field(..., description="Token de acesso")
    refresh_token: str = Field(..., description="Token de refresh")
    token_type: str = Field("bearer", description="Tipo do token")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")
    user: Dict[str, Any] = Field(..., description="Dados do usuário")
    requires_mfa: bool = Field(False, description="Requer autenticação multi-fator")
    mfa_methods: Optional[List[str]] = Field(None, description="Métodos MFA disponíveis")


class RefreshTokenRequest(DatametriaBaseModel):
    """Requisição de refresh token."""
    
    refresh_token: str = Field(..., description="Token de refresh")


class RegisterRequest(DatametriaBaseModel):
    """Requisição de registro de usuário."""
    
    name: str = Field(..., min_length=2, max_length=100, description="Nome completo")
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., min_length=8, max_length=128, description="Senha")
    confirm_password: str = Field(..., description="Confirmação da senha")
    role: UserRole = Field(UserRole.USER, description="Role do usuário")
    terms_accepted: bool = Field(..., description="Aceite dos termos de uso")
    
    @validator('email')
    def validate_email(cls, v):
        """Normaliza email."""
        return v.lower().strip()
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Valida se senhas coincidem."""
        if 'password' in values and v != values['password']:
            raise ValueError('Senhas não coincidem')
        return v
    
    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        """Valida aceite dos termos."""
        if not v:
            raise ValueError('Termos de uso devem ser aceitos')
        return v


class ChangePasswordRequest(DatametriaBaseModel):
    """Requisição de mudança de senha."""
    
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., min_length=8, max_length=128, description="Nova senha")
    confirm_new_password: str = Field(..., description="Confirmação da nova senha")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        """Valida se senhas coincidem."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Senhas não coincidem')
        return v


class ForgotPasswordRequest(DatametriaBaseModel):
    """Requisição de esqueci minha senha."""
    
    email: EmailStr = Field(..., description="Email do usuário")
    
    @validator('email')
    def validate_email(cls, v):
        """Normaliza email."""
        return v.lower().strip()


class ResetPasswordRequest(DatametriaBaseModel):
    """Requisição de reset de senha."""
    
    token: str = Field(..., description="Token de reset")
    new_password: str = Field(..., min_length=8, max_length=128, description="Nova senha")
    confirm_new_password: str = Field(..., description="Confirmação da nova senha")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        """Valida se senhas coincidem."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Senhas não coincidem')
        return v


class MFASetupRequest(DatametriaBaseModel):
    """Requisição de configuração MFA."""
    
    method: str = Field(..., description="Método MFA (totp, sms)")
    phone_number: Optional[str] = Field(None, description="Número de telefone para SMS")
    
    @validator('method')
    def validate_method(cls, v):
        """Valida método MFA."""
        allowed_methods = ['totp', 'sms']
        if v not in allowed_methods:
            raise ValueError(f'Método deve ser um de: {", ".join(allowed_methods)}')
        return v
    
    @validator('phone_number')
    def validate_phone_for_sms(cls, v, values):
        """Valida telefone para SMS."""
        if values.get('method') == 'sms' and not v:
            raise ValueError('Número de telefone é obrigatório para SMS')
        return v


class MFASetupResponse(DatametriaBaseModel):
    """Resposta de configuração MFA."""
    
    method: str = Field(..., description="Método MFA configurado")
    secret_key: Optional[str] = Field(None, description="Chave secreta TOTP")
    qr_code_url: Optional[str] = Field(None, description="URL do QR code")
    backup_codes: List[str] = Field(..., description="Códigos de backup")


class MFAVerifyRequest(DatametriaBaseModel):
    """Requisição de verificação MFA."""
    
    code: str = Field(..., min_length=6, max_length=8, description="Código MFA")
    method: str = Field(..., description="Método MFA usado")
    
    @validator('code')
    def validate_code(cls, v):
        """Valida código MFA."""
        if not v.isdigit():
            raise ValueError('Código deve conter apenas números')
        return v


class OAuth2LoginRequest(DatametriaBaseModel):
    """Requisição de login OAuth2."""
    
    provider: AuthProvider = Field(..., description="Provedor OAuth2")
    code: str = Field(..., description="Código de autorização")
    state: Optional[str] = Field(None, description="State parameter")
    redirect_uri: str = Field(..., description="URI de redirecionamento")


class OAuth2CallbackRequest(DatametriaBaseModel):
    """Callback OAuth2."""
    
    code: str = Field(..., description="Código de autorização")
    state: Optional[str] = Field(None, description="State parameter")
    error: Optional[str] = Field(None, description="Erro OAuth2")
    error_description: Optional[str] = Field(None, description="Descrição do erro")


class SessionInfo(DatametriaBaseModel):
    """Informações de sessão."""
    
    session_id: str = Field(..., description="ID da sessão")
    user_id: int = Field(..., description="ID do usuário")
    device_info: Dict[str, Any] = Field(..., description="Informações do dispositivo")
    ip_address: str = Field(..., description="Endereço IP")
    user_agent: str = Field(..., description="User agent")
    created_at: datetime = Field(..., description="Data de criação")
    last_activity: datetime = Field(..., description="Última atividade")
    expires_at: datetime = Field(..., description="Data de expiração")
    is_active: bool = Field(True, description="Sessão ativa")


class UserProfile(DatametriaBaseModel):
    """Perfil do usuário autenticado."""
    
    id: int = Field(..., description="ID do usuário")
    name: str = Field(..., description="Nome completo")
    email: EmailStr = Field(..., description="Email")
    role: UserRole = Field(..., description="Role do usuário")
    avatar_url: Optional[str] = Field(None, description="URL do avatar")
    is_active: bool = Field(..., description="Usuário ativo")
    is_verified: bool = Field(..., description="Email verificado")
    mfa_enabled: bool = Field(..., description="MFA habilitado")
    last_login: Optional[datetime] = Field(None, description="Último login")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: Optional[datetime] = Field(None, description="Última atualização")


class AuthAuditLog(DatametriaBaseModel):
    """Log de auditoria de autenticação."""
    
    user_id: Optional[int] = Field(None, description="ID do usuário")
    email: Optional[str] = Field(None, description="Email do usuário")
    action: str = Field(..., description="Ação realizada")
    success: bool = Field(..., description="Sucesso da ação")
    ip_address: str = Field(..., description="Endereço IP")
    user_agent: str = Field(..., description="User agent")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Informações do dispositivo")
    error_message: Optional[str] = Field(None, description="Mensagem de erro")
    timestamp: datetime = Field(..., description="Timestamp da ação")
    session_id: Optional[str] = Field(None, description="ID da sessão")


class TokenInfo(DatametriaBaseModel):
    """Informações do token."""
    
    token_type: str = Field(..., description="Tipo do token")
    user_id: int = Field(..., description="ID do usuário")
    email: str = Field(..., description="Email do usuário")
    role: UserRole = Field(..., description="Role do usuário")
    issued_at: datetime = Field(..., description="Data de emissão")
    expires_at: datetime = Field(..., description="Data de expiração")
    jti: str = Field(..., description="JWT ID")
    is_valid: bool = Field(..., description="Token válido")
    is_blacklisted: bool = Field(False, description="Token na blacklist")


class PasswordPolicy(DatametriaBaseModel):
    """Política de senhas."""
    
    min_length: int = Field(8, description="Comprimento mínimo")
    require_uppercase: bool = Field(True, description="Requer maiúscula")
    require_lowercase: bool = Field(True, description="Requer minúscula")
    require_numbers: bool = Field(True, description="Requer números")
    require_symbols: bool = Field(False, description="Requer símbolos")
    max_age_days: Optional[int] = Field(None, description="Idade máxima em dias")
    history_count: int = Field(5, description="Histórico de senhas")


class SecuritySettings(DatametriaBaseModel):
    """Configurações de segurança."""
    
    password_policy: PasswordPolicy = Field(..., description="Política de senhas")
    max_login_attempts: int = Field(5, description="Máximo de tentativas de login")
    lockout_duration_minutes: int = Field(15, description="Duração do bloqueio")
    session_timeout_minutes: int = Field(60, description="Timeout da sessão")
    require_mfa: bool = Field(False, description="MFA obrigatório")
    allowed_domains: Optional[List[str]] = Field(None, description="Domínios permitidos")
    ip_whitelist: Optional[List[str]] = Field(None, description="IPs permitidos")
