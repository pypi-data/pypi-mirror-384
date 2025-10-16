"""
WorkspaceRateLimiter - Rate limiting para Google Workspace APIs

Configuração de rate limiting baseada nas quotas oficiais do Google
com integração ao RateLimiter DATAMETRIA.
"""

import asyncio
from typing import Optional

from datametria_common.backend.rate_limiting import RateLimiter, RateLimit, RateLimitStrategy
from datametria_common.security.centralized_logger import CentralizedEnterpriseLogger


class WorkspaceRateLimiter:
    """Rate limiter configurado para quotas do Google Workspace.
    
    Implementa rate limiting baseado nas quotas oficiais:
    - Gmail: 250 quota units/user/second
    - Drive: 1000 queries/100 seconds/user
    - Calendar: 500 queries/100 seconds/user
    - Chat: 60 requests/60 seconds/user
    - Meet: 100 requests/100 seconds/user
    - Tasks: 50 requests/1 second/user
    - Vault: 10 requests/1 second/user
    
    Integra RateLimiter DATAMETRIA com:
    - Múltiplas estratégias (Token Bucket, Sliding Window, Fixed Window)
    - Backoff automático
    - Métricas de uso
    - Enterprise Logging
    
    Example:
        >>> limiter = WorkspaceRateLimiter(logger)
        >>> 
        >>> # Verificar e aguardar se necessário
        >>> await limiter.check_and_wait('gmail', 'user123')
        >>> 
        >>> # Obter status
        >>> status = limiter.get_status('gmail', 'user123')
    """
    
    # Quotas oficiais do Google Workspace
    API_QUOTAS = {
        'gmail': {
            'requests': 250,
            'window': 1,
            'strategy': RateLimitStrategy.TOKEN_BUCKET
        },
        'drive': {
            'requests': 1000,
            'window': 100,
            'strategy': RateLimitStrategy.SLIDING_WINDOW
        },
        'calendar': {
            'requests': 500,
            'window': 100,
            'strategy': RateLimitStrategy.SLIDING_WINDOW
        },
        'chat': {
            'requests': 60,
            'window': 60,
            'strategy': RateLimitStrategy.FIXED_WINDOW
        },
        'meet': {
            'requests': 100,
            'window': 100,
            'strategy': RateLimitStrategy.SLIDING_WINDOW
        },
        'tasks': {
            'requests': 50,
            'window': 1,
            'strategy': RateLimitStrategy.TOKEN_BUCKET
        },
        'vault': {
            'requests': 10,
            'window': 1,
            'strategy': RateLimitStrategy.TOKEN_BUCKET
        }
    }
    
    def __init__(
        self,
        logger: CentralizedEnterpriseLogger,
        redis_client=None,
        enabled: bool = True
    ):
        """Inicializar Workspace Rate Limiter.
        
        Args:
            logger: Enterprise logger
            redis_client: Cliente Redis (opcional)
            enabled: Se False, desabilita rate limiting
        """
        self._logger = logger
        self.enabled = enabled
        
        if not enabled:
            self._logger.warning(
                "Rate limiting disabled",
                compliance_tags=["WARNING", "CONFIGURATION"]
            )
            self.rate_limiter = None
            return
        
        # Inicializar RateLimiter DATAMETRIA
        self.rate_limiter = RateLimiter(
            redis_client=redis_client,
            default_strategy=RateLimitStrategy.TOKEN_BUCKET
        )
        
        # Configurar limites por API
        self._configure_limits()
        
        self._logger.info(
            "WorkspaceRateLimiter initialized",
            apis_configured=len(self.API_QUOTAS),
            enabled=enabled,
            compliance_tags=["AUDIT", "INITIALIZATION"]
        )
    
    def _configure_limits(self) -> None:
        """Configurar limites baseados nas quotas do Google."""
        for api_name, quota in self.API_QUOTAS.items():
            rate_limit = RateLimit(
                requests=quota['requests'],
                window=quota['window'],
                strategy=quota['strategy']
            )
            
            # Adicionar limite para padrão de endpoint
            self.rate_limiter.add_endpoint_limit(
                endpoint_pattern=f'^{api_name}\\..*',
                rate_limit=rate_limit
            )
            
            self._logger.debug(
                f"Rate limit configured for {api_name}",
                api=api_name,
                requests=quota['requests'],
                window=quota['window'],
                strategy=quota['strategy'].value
            )
    
    async def check_and_wait(
        self,
        api_name: str,
        user_id: str,
        operation: Optional[str] = None
    ) -> bool:
        """Verificar rate limit e aguardar se necessário.
        
        Args:
            api_name: Nome da API (gmail, drive, etc)
            user_id: ID do usuário
            operation: Nome da operação (opcional)
            
        Returns:
            True quando permitido
            
        Example:
            >>> await limiter.check_and_wait('gmail', 'user123', 'send_email')
        """
        if not self.enabled or not self.rate_limiter:
            return True
        
        key = f"workspace:{api_name}:{user_id}"
        endpoint = f"{api_name}.{operation}" if operation else api_name
        
        allowed, info = self.rate_limiter.is_allowed(
            key=key,
            endpoint=endpoint,
            user_id=user_id
        )
        
        if not allowed:
            wait_time = info.get('retry_after', 1.0)
            
            self._logger.warning(
                "Rate limit exceeded, waiting",
                api=api_name,
                user_id=user_id,
                operation=operation,
                wait_time=wait_time,
                remaining=info.get('remaining', 0),
                compliance_tags=["RATE_LIMIT", "THROTTLING"]
            )
            
            await asyncio.sleep(wait_time)
            
            # Tentar novamente após aguardar
            return await self.check_and_wait(api_name, user_id, operation)
        
        # Log apenas se próximo do limite
        remaining = info.get('remaining', 0)
        limit = info.get('limit', 0)
        
        if limit > 0 and remaining < (limit * 0.2):  # < 20% restante
            self._logger.warning(
                "Rate limit approaching",
                api=api_name,
                user_id=user_id,
                remaining=remaining,
                limit=limit,
                compliance_tags=["RATE_LIMIT", "WARNING"]
            )
        
        return True
    
    def get_status(self, api_name: str, user_id: str) -> dict:
        """Obter status atual de rate limiting.
        
        Args:
            api_name: Nome da API
            user_id: ID do usuário
            
        Returns:
            dict: Status com remaining, limit, reset_time
            
        Example:
            >>> status = limiter.get_status('gmail', 'user123')
            >>> print(f"Remaining: {status['remaining']}/{status['limit']}")
        """
        if not self.enabled or not self.rate_limiter:
            return {
                'enabled': False,
                'remaining': float('inf'),
                'limit': float('inf')
            }
        
        key = f"workspace:{api_name}:{user_id}"
        
        try:
            status = self.rate_limiter.get_status(key)
            
            # Obter informações da API específica
            if api_name in self.API_QUOTAS:
                quota = self.API_QUOTAS[api_name]
                api_status = status.get(quota['strategy'].value, {})
                
                return {
                    'enabled': True,
                    'api': api_name,
                    'user_id': user_id,
                    'remaining': api_status.get('remaining', 0),
                    'limit': api_status.get('limit', quota['requests']),
                    'reset_time': api_status.get('reset_time', 0),
                    'strategy': quota['strategy'].value
                }
            
            return {
                'enabled': True,
                'api': api_name,
                'user_id': user_id,
                'status': status
            }
            
        except Exception as e:
            self._logger.error(
                "Failed to get rate limit status",
                api=api_name,
                user_id=user_id,
                error=str(e),
                compliance_tags=["ERROR", "RATE_LIMIT"]
            )
            
            return {
                'enabled': True,
                'error': str(e)
            }
    
    def reset(self, api_name: str, user_id: str) -> None:
        """Reset rate limit para usuário específico.
        
        Args:
            api_name: Nome da API
            user_id: ID do usuário
            
        Example:
            >>> limiter.reset('gmail', 'user123')
        """
        if not self.enabled or not self.rate_limiter:
            return
        
        key = f"workspace:{api_name}:{user_id}"
        
        try:
            self.rate_limiter.reset_key(key)
            
            self._logger.info(
                "Rate limit reset",
                api=api_name,
                user_id=user_id,
                compliance_tags=["AUDIT", "RATE_LIMIT"]
            )
            
        except Exception as e:
            self._logger.error(
                "Failed to reset rate limit",
                api=api_name,
                user_id=user_id,
                error=str(e),
                compliance_tags=["ERROR", "RATE_LIMIT"]
            )
    
    def get_metrics(self) -> dict:
        """Obter métricas de rate limiting.
        
        Returns:
            dict: Métricas agregadas
            
        Example:
            >>> metrics = limiter.get_metrics()
            >>> print(f"Total keys: {metrics['total_keys']}")
        """
        if not self.enabled or not self.rate_limiter:
            return {'enabled': False}
        
        try:
            metrics = self.rate_limiter.get_metrics()
            
            # Adicionar informações específicas do Workspace
            metrics['workspace'] = {
                'apis_configured': len(self.API_QUOTAS),
                'quotas': {
                    api: {
                        'requests': quota['requests'],
                        'window': quota['window'],
                        'strategy': quota['strategy'].value
                    }
                    for api, quota in self.API_QUOTAS.items()
                }
            }
            
            return metrics
            
        except Exception as e:
            self._logger.error(
                "Failed to get rate limit metrics",
                error=str(e),
                compliance_tags=["ERROR", "RATE_LIMIT"]
            )
            
            return {'enabled': True, 'error': str(e)}
    
    def update_quota(
        self,
        api_name: str,
        requests: int,
        window: int,
        strategy: Optional[RateLimitStrategy] = None
    ) -> None:
        """Atualizar quota de uma API específica.
        
        Args:
            api_name: Nome da API
            requests: Número de requests permitidos
            window: Janela de tempo em segundos
            strategy: Estratégia de rate limiting
            
        Example:
            >>> # Aumentar quota do Gmail
            >>> limiter.update_quota('gmail', 500, 1)
        """
        if not self.enabled or not self.rate_limiter:
            return
        
        if strategy is None:
            strategy = self.API_QUOTAS.get(api_name, {}).get(
                'strategy',
                RateLimitStrategy.TOKEN_BUCKET
            )
        
        rate_limit = RateLimit(
            requests=requests,
            window=window,
            strategy=strategy
        )
        
        self.rate_limiter.add_endpoint_limit(
            endpoint_pattern=f'^{api_name}\\..*',
            rate_limit=rate_limit
        )
        
        # Atualizar cache local
        self.API_QUOTAS[api_name] = {
            'requests': requests,
            'window': window,
            'strategy': strategy
        }
        
        self._logger.info(
            "Rate limit quota updated",
            api=api_name,
            requests=requests,
            window=window,
            strategy=strategy.value,
            compliance_tags=["AUDIT", "CONFIGURATION"]
        )
