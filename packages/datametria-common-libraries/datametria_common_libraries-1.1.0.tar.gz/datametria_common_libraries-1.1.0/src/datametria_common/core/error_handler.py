"""
DATAMETRIA ErrorHandlerMixin - Universal Error Handling Pattern

Standardized error handling with logging integration, LGPD compliance,
and retry logic for all DATAMETRIA components.
"""

import asyncio
import traceback
from abc import ABC
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, Type, Union
from enum import Enum
from functools import wraps


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"


class ErrorHandlerMixin(ABC):
    """Universal error handling mixin for all DATAMETRIA components.
    
    Provides standardized error handling with:
    - Automatic logging integration
    - LGPD compliance hooks
    - Retry logic
    - Error categorization
    - Stack trace sanitization
    
    Example:
        >>> class MyService(ErrorHandlerMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self._logger = EnterpriseLogger("my-service")
        >>> 
        >>> service = MyService()
        >>> result = service.handle_error(ValueError("Invalid input"), "validation")
    """
    
    def __init__(self):
        """Initialize error handler mixin."""
        self._error_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, datetime] = {}
    
    def handle_error(
        self,
        error: Exception,
        category: Union[ErrorCategory, str] = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle error with logging and compliance.
        
        Args:
            error: Exception to handle
            category: Error category for classification
            severity: Error severity level
            context: Additional context information
            user_id: User ID for LGPD compliance
            
        Returns:
            Standardized error response
        """
        error_id = self._generate_error_id()
        timestamp = datetime.now(timezone.utc)
        
        # Convert category to enum if string
        if isinstance(category, str):
            try:
                category = ErrorCategory(category)
            except ValueError:
                category = ErrorCategory.SYSTEM
        
        # Sanitize stack trace for security
        stack_trace = self._sanitize_stack_trace(error)
        
        # Build error response
        error_response = {
            "error_id": error_id,
            "timestamp": timestamp.isoformat(),
            "type": error.__class__.__name__,
            "message": str(error),
            "category": category.value,
            "severity": severity.value,
            "service": getattr(self, 'service_name', self.__class__.__name__)
        }
        
        # Add context if provided
        if context:
            error_response["context"] = context
        
        # Log error if logger available
        if hasattr(self, '_logger'):
            self._logger.log_error(
                error_type=error.__class__.__name__,
                error_message=str(error),
                component=self.__class__.__name__,
                user_id=user_id,
                stack_trace=stack_trace if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
            )
        
        # LGPD compliance logging if user involved
        if user_id and hasattr(self, '_lgpd_compliance'):
            self._lgpd_compliance.log_error_event(
                user_id=user_id,
                error_type=error.__class__.__name__,
                category=category.value
            )
        
        # Update error tracking
        self._track_error(category.value)
        
        return error_response
    
    def with_error_handling(
        self,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retry_count: int = 0,
        retry_delay: float = 1.0
    ):
        """Decorator for automatic error handling.
        
        Args:
            category: Error category
            severity: Error severity
            retry_count: Number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Example:
            >>> @service.with_error_handling(
            ...     category=ErrorCategory.DATABASE,
            ...     retry_count=3
            ... )
            ... async def database_operation(self):
            ...     # Database operation that might fail
            ...     pass
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_error = None
                current_delay = retry_delay
                
                for attempt in range(retry_count + 1):
                    try:
                        if asyncio.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        
                        if attempt < retry_count:
                            # Log retry attempt
                            if hasattr(self, '_logger'):
                                self._logger.log_system_event(
                                    "retry_attempt",
                                    self.__class__.__name__,
                                    f"attempt_{attempt + 1}",
                                    {"error": str(e), "retry_delay": current_delay}
                                )
                            
                            await asyncio.sleep(current_delay)
                            current_delay *= 2  # Exponential backoff
                        else:
                            # Final failure - handle error
                            return self.handle_error(e, category, severity)
                
                return self.handle_error(last_error, category, severity)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(retry_count + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        
                        if attempt < retry_count:
                            # Log retry attempt
                            if hasattr(self, '_logger'):
                                self._logger.log_system_event(
                                    "retry_attempt",
                                    self.__class__.__name__,
                                    f"attempt_{attempt + 1}",
                                    {"error": str(e)}
                                )
                        else:
                            # Final failure - handle error
                            return self.handle_error(e, category, severity)
                
                return self.handle_error(last_error, category, severity)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        timestamp = datetime.now(timezone.utc)
        import random
        return f"err_{timestamp.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999):04d}"
    
    def _sanitize_stack_trace(self, error: Exception) -> str:
        """Sanitize stack trace for security and privacy.
        
        Args:
            error: Exception to get stack trace from
            
        Returns:
            Sanitized stack trace string
        """
        try:
            stack_trace = traceback.format_exc()
            
            # Remove sensitive information
            sensitive_patterns = [
                r'password=\w+',
                r'token=\w+',
                r'key=\w+',
                r'secret=\w+'
            ]
            
            import re
            for pattern in sensitive_patterns:
                stack_trace = re.sub(pattern, 'password=***', stack_trace, flags=re.IGNORECASE)
            
            return stack_trace
        except Exception:
            return f"{error.__class__.__name__}: {str(error)}"
    
    def _track_error(self, category: str) -> None:
        """Track error occurrence for monitoring."""
        self._error_counts[category] = self._error_counts.get(category, 0) + 1
        self._last_errors[category] = datetime.now(timezone.utc)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring.
        
        Returns:
            Dictionary with error statistics
        """
        return {
            "error_counts": self._error_counts.copy(),
            "last_errors": {
                category: timestamp.isoformat()
                for category, timestamp in self._last_errors.items()
            },
            "total_errors": sum(self._error_counts.values())
        }
    
    def reset_error_stats(self) -> None:
        """Reset error statistics."""
        self._error_counts.clear()
        self._last_errors.clear()
