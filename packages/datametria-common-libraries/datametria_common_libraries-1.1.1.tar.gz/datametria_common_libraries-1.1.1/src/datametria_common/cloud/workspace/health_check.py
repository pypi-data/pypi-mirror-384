"""
Workspace Health Check - Comprehensive health monitoring for Google Workspace APIs

Provides:
- Individual API health checks
- Aggregated health status
- Dependency checks (OAuth2, Rate Limiter, Cache)
- Health check endpoints for monitoring systems
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from ...core.health_check import HealthCheckMixin
from .config import WorkspaceConfig
from .oauth2 import WorkspaceOAuth2Manager
from .rate_limiter import WorkspaceRateLimiter
from .cache_integration import WorkspaceCacheManager


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class WorkspaceHealthCheck(HealthCheckMixin):
    """Comprehensive health check for Workspace APIs"""
    
    def __init__(
        self,
        config: WorkspaceConfig,
        oauth_manager: WorkspaceOAuth2Manager,
        rate_limiter: WorkspaceRateLimiter,
        cache_manager: Optional[WorkspaceCacheManager] = None
    ):
        super().__init__()
        self.config = config
        self.oauth_manager = oauth_manager
        self.rate_limiter = rate_limiter
        self.cache_manager = cache_manager
        self._api_managers = {}
    
    def register_api_manager(self, api_name: str, manager):
        """Register API manager for health checks"""
        self._api_managers[api_name] = manager
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        checks = {}
        
        # Check configuration
        checks['config'] = await self._check_config()
        
        # Check OAuth2
        checks['oauth2'] = await self._check_oauth2()
        
        # Check rate limiter
        checks['rate_limiter'] = await self._check_rate_limiter()
        
        # Check cache
        if self.cache_manager:
            checks['cache'] = await self._check_cache()
        
        # Check each API
        for api_name, manager in self._api_managers.items():
            checks[f'api_{api_name}'] = await self._check_api(api_name, manager)
        
        # Determine overall status
        overall_status = self._determine_overall_status(checks)
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
            'summary': self._generate_summary(checks)
        }
    
    async def _check_config(self) -> Dict[str, Any]:
        """Check configuration validity"""
        try:
            self.config.validate()
            return {
                'status': HealthStatus.HEALTHY.value,
                'message': 'Configuration valid',
                'details': {
                    'scopes': len(self.config.scopes),
                    'cache_enabled': self.config.cache_enabled,
                    'rate_limit_enabled': self.config.rate_limit_enabled
                }
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'Configuration invalid: {str(e)}'
            }
    
    async def _check_oauth2(self) -> Dict[str, Any]:
        """Check OAuth2 credentials"""
        try:
            credentials = self.oauth_manager.get_credentials()
            if credentials and not credentials.expired:
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'OAuth2 credentials valid',
                    'details': {
                        'expired': False,
                        'scopes': len(self.config.scopes)
                    }
                }
            elif credentials and credentials.expired:
                return {
                    'status': HealthStatus.DEGRADED.value,
                    'message': 'OAuth2 credentials expired',
                    'details': {'expired': True}
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'message': 'No OAuth2 credentials found'
                }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'OAuth2 check failed: {str(e)}'
            }
    
    async def _check_rate_limiter(self) -> Dict[str, Any]:
        """Check rate limiter status"""
        try:
            status = self.rate_limiter.get_status()
            return {
                'status': HealthStatus.HEALTHY.value,
                'message': 'Rate limiter operational',
                'details': status
            }
        except Exception as e:
            return {
                'status': HealthStatus.DEGRADED.value,
                'message': f'Rate limiter check failed: {str(e)}'
            }
    
    async def _check_cache(self) -> Dict[str, Any]:
        """Check cache status"""
        try:
            if not self.cache_manager.is_enabled():
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'Cache disabled',
                    'details': {'enabled': False}
                }
            
            stats = self.cache_manager.get_stats()
            hit_rate = stats.get('hit_rate', 0)
            
            if hit_rate >= 60:
                status = HealthStatus.HEALTHY
            elif hit_rate >= 40:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.DEGRADED
            
            return {
                'status': status.value,
                'message': f'Cache operational (hit rate: {hit_rate}%)',
                'details': stats
            }
        except Exception as e:
            return {
                'status': HealthStatus.DEGRADED.value,
                'message': f'Cache check failed: {str(e)}'
            }
    
    async def _check_api(self, api_name: str, manager) -> Dict[str, Any]:
        """Check individual API health"""
        try:
            if hasattr(manager, 'test_connection'):
                is_healthy = await manager.test_connection()
                if is_healthy:
                    return {
                        'status': HealthStatus.HEALTHY.value,
                        'message': f'{api_name} API operational',
                        'details': {'connected': True}
                    }
                else:
                    return {
                        'status': HealthStatus.UNHEALTHY.value,
                        'message': f'{api_name} API connection failed',
                        'details': {'connected': False}
                    }
            else:
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': f'{api_name} API registered',
                    'details': {'test_connection_available': False}
                }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'{api_name} API check failed: {str(e)}'
            }
    
    def _determine_overall_status(self, checks: Dict[str, Any]) -> HealthStatus:
        """Determine overall health status"""
        statuses = [check.get('status') for check in checks.values()]
        
        if any(s == HealthStatus.UNHEALTHY.value for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED.value for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _generate_summary(self, checks: Dict[str, Any]) -> Dict[str, int]:
        """Generate health check summary"""
        summary = {
            'total': len(checks),
            'healthy': 0,
            'degraded': 0,
            'unhealthy': 0
        }
        
        for check in checks.values():
            status = check.get('status')
            if status == HealthStatus.HEALTHY.value:
                summary['healthy'] += 1
            elif status == HealthStatus.DEGRADED.value:
                summary['degraded'] += 1
            elif status == HealthStatus.UNHEALTHY.value:
                summary['unhealthy'] += 1
        
        return summary
    
    async def get_readiness(self) -> Dict[str, Any]:
        """Check if system is ready to serve requests"""
        health = await self.health_check()
        
        is_ready = (
            health['status'] != HealthStatus.UNHEALTHY.value and
            health['checks'].get('config', {}).get('status') == HealthStatus.HEALTHY.value and
            health['checks'].get('oauth2', {}).get('status') != HealthStatus.UNHEALTHY.value
        )
        
        return {
            'ready': is_ready,
            'status': health['status'],
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """Check if system is alive"""
        return {
            'alive': True,
            'timestamp': datetime.now().isoformat()
        }
