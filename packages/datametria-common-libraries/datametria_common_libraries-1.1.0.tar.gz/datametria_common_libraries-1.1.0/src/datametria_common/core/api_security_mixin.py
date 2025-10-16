"""
DATAMETRIA APISecurityMixin - Integrated API Framework Security

Universal API security mixin that provides automatic security integration
for all DATAMETRIA API frameworks.
"""

from abc import ABC
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timezone

from .security_mixin import SecurityMixin
from .compliance_mixin import ComplianceMixin, ComplianceEvent
from ..security.exceptions import SecurityError


class APISecurityMixin(SecurityMixin, ComplianceMixin, ABC):
    """Universal API security mixin for all DATAMETRIA API frameworks.
    
    Provides automatic security integration:
    - JWT token validation
    - Rate limiting
    - Request/response logging
    - CORS protection
    - Input validation
    
    Example:
        >>> class MyAPIService(APISecurityMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self._init_api_security()
        >>> 
        >>> @service.secure_endpoint("users", "read")
        >>> async def get_users():
        ...     return await fetch_users()
    """
    
    def __init__(self):
        """Initialize API security mixin."""
        SecurityMixin.__init__(self)
        ComplianceMixin.__init__(self)
        self._rate_limits: Dict[str, Dict] = {}
        self._cors_origins: list = ["*"]
    
    def _init_api_security(self, jwt_secret: str = None, 
                          rate_limit_default: int = 100) -> None:
        """Initialize API security components."""
        self._init_security()
        self._init_compliance()
        self.jwt_secret = jwt_secret or "default_secret"
        self.rate_limit_default = rate_limit_default
    
    def secure_endpoint(self, resource: str, action: str, 
                       rate_limit: Optional[int] = None):
        """Decorator for securing API endpoints."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request info (simplified)
                request_info = self._extract_request_info(kwargs)
                
                # Validate JWT token
                token = request_info.get("authorization")
                if token:
                    payload = self._validate_jwt_token(token)
                    if payload:
                        # Set security context from token
                        self._set_context_from_token(payload, request_info)
                
                # Check authorization
                self.require_authorization(resource, action)
                
                # Apply rate limiting
                self._check_rate_limit(
                    request_info.get("client_ip", "unknown"),
                    rate_limit or self.rate_limit_default
                )
                
                # Log API access
                self._log_api_access(resource, action, request_info)
                
                # Execute endpoint
                try:
                    result = await func(*args, **kwargs)
                    
                    # Log successful response
                    self._log_api_response(resource, action, True, request_info)
                    
                    return result
                    
                except Exception as e:
                    # Log error response
                    self._log_api_response(resource, action, False, request_info, str(e))
                    raise
            
            return wrapper
        return decorator
    
    def _extract_request_info(self, kwargs: Dict) -> Dict[str, Any]:
        """Extract request information from kwargs."""
        # Simplified request info extraction
        return {
            "authorization": kwargs.get("authorization"),
            "client_ip": kwargs.get("client_ip", "127.0.0.1"),
            "user_agent": kwargs.get("user_agent", "unknown"),
            "method": kwargs.get("method", "GET"),
            "path": kwargs.get("path", "/")
        }
    
    def _validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload."""
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]
            
            return self.verify_jwt_token(token, self.jwt_secret)
        except Exception:
            return None
    
    def _set_context_from_token(self, payload: Dict[str, Any], 
                               request_info: Dict[str, Any]) -> None:
        """Set security context from JWT payload."""
        from ..security.security_manager import SecurityContext, SecurityLevel
        
        context = SecurityContext(
            user_id=payload.get("user_id", "unknown"),
            session_id=payload.get("session_id", "api_session"),
            ip_address=request_info.get("client_ip", "unknown"),
            user_agent=request_info.get("user_agent", "unknown"),
            permissions=payload.get("permissions", []),
            security_level=SecurityLevel.MEDIUM,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.set_security_context(context)
    
    def _check_rate_limit(self, client_ip: str, limit: int) -> None:
        """Check rate limiting for client."""
        current_time = datetime.now(timezone.utc)
        
        if client_ip not in self._rate_limits:
            self._rate_limits[client_ip] = {
                "count": 0,
                "window_start": current_time
            }
        
        client_data = self._rate_limits[client_ip]
        
        # Reset window if more than 1 minute passed
        if (current_time - client_data["window_start"]).seconds >= 60:
            client_data["count"] = 0
            client_data["window_start"] = current_time
        
        client_data["count"] += 1
        
        if client_data["count"] > limit:
            raise SecurityError(f"Rate limit exceeded for {client_ip}")
    
    def _log_api_access(self, resource: str, action: str, 
                       request_info: Dict[str, Any]) -> None:
        """Log API access for security and compliance."""
        context = self.get_security_context()
        
        # Security logging
        self.log_security_event("api_access", {
            "resource": resource,
            "action": action,
            "method": request_info.get("method"),
            "path": request_info.get("path"),
            "client_ip": request_info.get("client_ip"),
            "user_id": context.user_id if context else "anonymous"
        })
        
        # Compliance logging for data access
        if context and resource in ["users", "personal_data", "payments"]:
            self.auto_compliance_hook(
                ComplianceEvent.DATA_ACCESS,
                user_id=context.user_id,
                data_type=resource,
                purpose="api_request"
            )
    
    def _log_api_response(self, resource: str, action: str, success: bool,
                         request_info: Dict[str, Any], error: str = None) -> None:
        """Log API response."""
        context = self.get_security_context()
        
        self.log_security_event("api_response", {
            "resource": resource,
            "action": action,
            "success": success,
            "error": error,
            "user_id": context.user_id if context else "anonymous",
            "client_ip": request_info.get("client_ip")
        })
    
    def validate_cors(self, origin: str) -> bool:
        """Validate CORS origin."""
        if "*" in self._cors_origins:
            return True
        return origin in self._cors_origins
    
    def configure_cors(self, origins: list) -> None:
        """Configure allowed CORS origins."""
        self._cors_origins = origins
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data to prevent injection attacks."""
        if isinstance(data, str):
            # Basic XSS prevention
            dangerous_chars = ["<", ">", "&", "\"", "'"]
            for char in dangerous_chars:
                data = data.replace(char, "")
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        
        return data
    
    def get_api_security_stats(self) -> Dict[str, Any]:
        """Get API security statistics."""
        total_requests = sum(
            client_data["count"] 
            for client_data in self._rate_limits.values()
        )
        
        return {
            "total_clients": len(self._rate_limits),
            "total_requests": total_requests,
            "cors_origins": len(self._cors_origins),
            "security_enabled": self.is_security_enabled(),
            "compliance_enabled": self.is_compliance_enabled()
        }
