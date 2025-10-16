"""
DATAMETRIA HealthCheckMixin - Universal Health Check Interface

Standardized health check interface for all DATAMETRIA components with
async support, metrics collection, and EnterpriseLogger integration.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum


class HealthStatus(Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckMixin(ABC):
    """Universal health check mixin for all DATAMETRIA components.
    
    Provides standardized health check interface with:
    - Async/await support
    - Metrics collection
    - EnterpriseLogger integration
    - Consistent response format
    
    Example:
        >>> class MyService(HealthCheckMixin):
        ...     async def _check_component_health(self):
        ...         return {"database": True, "cache": True}
        >>> 
        >>> service = MyService()
        >>> health = await service.health_check()
        >>> print(health["status"])  # "healthy"
    """
    
    def __init__(self):
        """Initialize health check mixin."""
        self._health_checks: List[str] = []
        self._last_check: Optional[datetime] = None
        self._last_status: Optional[HealthStatus] = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check.
        
        Returns:
            Dict containing health status, timestamp, and component details
            
        Example:
            >>> health = await service.health_check()
            >>> {
            ...     "status": "healthy",
            ...     "timestamp": "2025-01-08T10:30:00Z",
            ...     "service": "my-service",
            ...     "components": {"database": True},
            ...     "uptime_seconds": 3600,
            ...     "version": "1.0.0"
            ... }
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get component-specific health checks
            components = await self._check_component_health()
            
            # Determine overall status
            status = self._determine_status(components)
            
            # Update internal state
            self._last_check = start_time
            self._last_status = status
            
            # Build response
            response = {
                "status": status.value,
                "timestamp": start_time.isoformat(),
                "service": getattr(self, 'service_name', self.__class__.__name__),
                "components": components,
                "check_duration_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            }
            
            # Add optional fields if available
            if hasattr(self, 'version'):
                response["version"] = self.version
            
            # Log health check if logger available
            if hasattr(self, '_logger'):
                self._logger.log_system_event(
                    "health_check",
                    self.__class__.__name__,
                    status.value,
                    {"duration_ms": response["check_duration_ms"]}
                )
            
            return response
            
        except Exception as e:
            # Handle health check failures
            error_response = {
                "status": HealthStatus.UNHEALTHY.value,
                "timestamp": start_time.isoformat(),
                "service": getattr(self, 'service_name', self.__class__.__name__),
                "error": str(e),
                "check_duration_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            }
            
            if hasattr(self, '_logger'):
                self._logger.log_error(
                    "health_check_error",
                    str(e),
                    self.__class__.__name__
                )
            
            return error_response
    
    @abstractmethod
    async def _check_component_health(self) -> Dict[str, Any]:
        """Check component-specific health.
        
        Must be implemented by subclasses to check their specific dependencies.
        
        Returns:
            Dict with component health status (True/False or detailed info)
            
        Example:
            >>> async def _check_component_health(self):
            ...     return {
            ...         "database": await self._check_database(),
            ...         "cache": await self._check_cache(),
            ...         "external_api": await self._check_external_api()
            ...     }
        """
        pass
    
    def _determine_status(self, components: Dict[str, Any]) -> HealthStatus:
        """Determine overall health status from component checks.
        
        Args:
            components: Dictionary of component health results
            
        Returns:
            Overall health status
        """
        if not components:
            return HealthStatus.HEALTHY
        
        # Count healthy vs unhealthy components
        total_components = len(components)
        healthy_components = 0
        
        for component, status in components.items():
            if isinstance(status, bool):
                if status:
                    healthy_components += 1
            elif isinstance(status, dict):
                if status.get('healthy', False):
                    healthy_components += 1
            else:
                # Assume healthy if not explicitly unhealthy
                healthy_components += 1
        
        # Determine status based on healthy ratio
        healthy_ratio = healthy_components / total_components
        
        if healthy_ratio == 1.0:
            return HealthStatus.HEALTHY
        elif healthy_ratio >= 0.5:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY
    
    def get_last_health_status(self) -> Optional[Dict[str, Any]]:
        """Get last health check result without performing new check.
        
        Returns:
            Last health check result or None if no check performed
        """
        if self._last_check and self._last_status:
            return {
                "status": self._last_status.value,
                "timestamp": self._last_check.isoformat(),
                "service": getattr(self, 'service_name', self.__class__.__name__)
            }
        return None
    
    def is_healthy(self) -> bool:
        """Quick health status check.
        
        Returns:
            True if last status was healthy, False otherwise
        """
        return self._last_status == HealthStatus.HEALTHY if self._last_status else False
