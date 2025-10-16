"""
DATAMETRIA SecurityMixin - Universal SecurityManager Integration

Universal security mixin that integrates SecurityManager into all DATAMETRIA
components, providing consistent security features across the entire stack.
"""

from abc import ABC
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone

from ..security.security_manager import SecurityManager, SecurityContext, DataClassification
from ..security.enterprise_logging import EnterpriseLogger


class SecurityMixin(ABC):
    """Universal security mixin for all DATAMETRIA components.
    
    Provides standardized SecurityManager integration with:
    - Automatic security context management
    - Data encryption/decryption
    - Access control validation
    - Security event logging
    - LGPD/GDPR compliance hooks
    
    Example:
        >>> class MyService(SecurityMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self._init_security()
        >>> 
        >>> service = MyService()
        >>> encrypted = service.encrypt_data("sensitive data")
        >>> authorized = service.check_authorization(context, "resource", "action")
    """
    
    def __init__(self):
        """Initialize security mixin."""
        self._security_manager: Optional[SecurityManager] = None
        self._security_context: Optional[SecurityContext] = None
        self._security_enabled: bool = True
    
    def _init_security(
        self,
        encryption_key: Optional[bytes] = None,
        logger: Optional[EnterpriseLogger] = None
    ) -> None:
        """Initialize SecurityManager for the component.
        
        Args:
            encryption_key: Optional encryption key for data protection
            logger: Optional logger instance for security events
        """
        if not hasattr(self, '_logger') and logger:
            self._logger = logger
        
        self._security_manager = SecurityManager(
            encryption_key=encryption_key,
            logger=getattr(self, '_logger', None)
        )
    
    def set_security_context(self, context: SecurityContext) -> None:
        """Set security context for operations.
        
        Args:
            context: Security context from authentication
        """
        self._security_context = context
    
    def get_security_context(self) -> Optional[SecurityContext]:
        """Get current security context."""
        return self._security_context
    
    def encrypt_data(
        self,
        data: str,
        classification: DataClassification = DataClassification.CONFIDENTIAL
    ) -> str:
        """Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            classification: Data classification level
            
        Returns:
            Encrypted data string
        """
        if not self._security_enabled or not self._security_manager:
            return data
        
        return self._security_manager.encrypt_sensitive_data(data, classification)
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data to decrypt
            
        Returns:
            Decrypted data string
        """
        if not self._security_enabled or not self._security_manager:
            return encrypted_data
        
        return self._security_manager.decrypt_sensitive_data(encrypted_data)
    
    def mask_data(self, data: str, data_type: str = "general") -> str:
        """Mask personal data for display.
        
        Args:
            data: Data to mask
            data_type: Type of data (email, cpf, phone, etc.)
            
        Returns:
            Masked data string
        """
        if not self._security_manager:
            return "***"
        
        return self._security_manager.mask_personal_data(data, data_type)
    
    def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[SecurityContext]:
        """Authenticate user and create security context.
        
        Args:
            username: Username
            password: Password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Security context if authentication successful
        """
        if not self._security_manager:
            return None
        
        context = self._security_manager.authenticate_user(
            username, password, ip_address, user_agent
        )
        
        if context:
            self.set_security_context(context)
        
        return context
    
    def check_authorization(
        self,
        resource: str,
        action: str,
        context: Optional[SecurityContext] = None
    ) -> bool:
        """Check if current user is authorized for action.
        
        Args:
            resource: Resource being accessed
            action: Action being performed
            context: Optional security context (uses current if not provided)
            
        Returns:
            True if authorized
        """
        if not self._security_enabled or not self._security_manager:
            return True
        
        auth_context = context or self._security_context
        if not auth_context:
            return False
        
        return self._security_manager.authorize_action(auth_context, resource, action)
    
    def require_authorization(
        self,
        resource: str,
        action: str,
        context: Optional[SecurityContext] = None
    ) -> None:
        """Require authorization or raise exception.
        
        Args:
            resource: Resource being accessed
            action: Action being performed
            context: Optional security context
            
        Raises:
            SecurityError: If not authorized
        """
        if not self.check_authorization(resource, action, context):
            from ..security.exceptions import SecurityError
            raise SecurityError(f"Access denied for {resource}:{action}")
    
    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """Log security event.
        
        Args:
            event_type: Type of security event
            details: Event details
            user_id: Optional user ID
        """
        if hasattr(self, '_logger'):
            self._logger.log_security_event(event_type, details)
        
        # Add to security context if available
        if self._security_context and not user_id:
            user_id = self._security_context.user_id
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Validation result dictionary
        """
        if not self._security_manager:
            return {"valid": True, "score": 0, "issues": []}
        
        return self._security_manager.validate_password_strength(password)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure token.
        
        Args:
            length: Token length
            
        Returns:
            Secure token string
        """
        if not self._security_manager:
            import secrets
            return secrets.token_urlsafe(length)
        
        return self._security_manager.generate_secure_token(length)
    
    def hash_password(self, password: str) -> str:
        """Hash password securely.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        if not self._security_manager:
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()
        
        return self._security_manager.hash_password(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Plain password
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        if not self._security_manager:
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest() == hashed
        
        return self._security_manager.verify_password(password, hashed)
    
    def create_jwt_token(
        self,
        payload: Dict[str, Any],
        secret_key: str,
        expiry_hours: int = 24
    ) -> str:
        """Create JWT token.
        
        Args:
            payload: Token payload
            secret_key: Secret key for signing
            expiry_hours: Token expiry in hours
            
        Returns:
            JWT token string
        """
        if not self._security_manager:
            raise RuntimeError("SecurityManager not initialized")
        
        return self._security_manager.create_jwt_token(payload, secret_key, expiry_hours)
    
    def verify_jwt_token(self, token: str, secret_key: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token.
        
        Args:
            token: JWT token to verify
            secret_key: Secret key for verification
            
        Returns:
            Token payload if valid, None otherwise
        """
        if not self._security_manager:
            return None
        
        return self._security_manager.verify_jwt_token(token, secret_key)
    
    def is_security_enabled(self) -> bool:
        """Check if security is enabled."""
        return self._security_enabled and self._security_manager is not None
    
    def disable_security(self) -> None:
        """Disable security (for testing only)."""
        self._security_enabled = False
    
    def enable_security(self) -> None:
        """Enable security."""
        self._security_enabled = True
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration.
        
        Returns:
            Security configuration dictionary
        """
        if not self._security_manager:
            return {}
        
        return {
            "security_enabled": self._security_enabled,
            "has_context": self._security_context is not None,
            "context_user": self._security_context.user_id if self._security_context else None,
            "context_expired": (
                self._security_context.is_expired() 
                if self._security_context else None
            )
        }
