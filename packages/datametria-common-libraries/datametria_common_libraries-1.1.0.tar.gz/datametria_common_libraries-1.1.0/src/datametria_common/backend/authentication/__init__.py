"""
🔐 Authentication - DATAMETRIA Common Libraries

Sistema de autenticação enterprise com JWT, OAuth2, MFA e integração completa.

Features:
    - JWT Token Management: Access e refresh tokens seguros
    - OAuth2 Integration: Google, Microsoft, GitHub
    - Multi-Factor Authentication: TOTP, SMS
    - Role-Based Access Control: Granular permissions
    - Session Management: Secure session handling
    - Password Security: Bcrypt + policies
    - Account Security: Lockout, rate limiting

Components:
    jwt_manager: Gerenciamento de tokens JWT
    oauth2_manager: Integração OAuth2 multi-provider
    mfa_manager: Multi-factor authentication
    password_manager: Políticas e validação de senhas
    session_manager: Gerenciamento de sessões
    auth_middleware: Middleware de autenticação

Integration:
    - Security Framework: SecurityManager integrado
    - API Framework: Dependencies e decorators
    - Database Layer: Modelos de usuário e sessão
    - Logging Enterprise: Auditoria de autenticação
    - Rate Limiting: Proteção contra ataques

Author: DATAMETRIA Enterprise Team
Version: 1.0.0
"""

from .jwt_manager import JWTManager
from .oauth2_manager import OAuth2Manager
from .mfa_manager import MFAManager
from .password_manager import PasswordManager
from .session_manager import SessionManager
from .auth_manager import AuthManager
from .models import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ChangePasswordRequest,
    MFASetupRequest,
    MFAVerifyRequest
)
from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    require_role,
    require_permissions
)
from .decorators import (
    require_auth,
    require_mfa,
    require_admin,
    audit_login
)

__all__ = [
    # Core managers
    "JWTManager",
    "OAuth2Manager", 
    "MFAManager",
    "PasswordManager",
    "SessionManager",
    "AuthManager",
    
    # Models
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RegisterRequest",
    "ChangePasswordRequest",
    "MFASetupRequest",
    "MFAVerifyRequest",
    
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_admin_user",
    "require_role",
    "require_permissions",
    
    # Decorators
    "require_auth",
    "require_mfa",
    "require_admin",
    "audit_login"
]
