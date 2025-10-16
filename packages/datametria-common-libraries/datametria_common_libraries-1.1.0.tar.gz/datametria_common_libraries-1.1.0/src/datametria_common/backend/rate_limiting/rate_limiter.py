"""
🚦 Rate Limiter - DATAMETRIA Rate Limiting

Gerenciador principal de rate limiting integrado aos componentes DATAMETRIA.
"""

from typing import Dict, Any, Optional, Tuple, List
import re
import structlog

from datametria_common.core import BaseConfig
from .strategies import SlidingWindowStrategy, TokenBucketStrategy, FixedWindowStrategy
from .models import RateLimit, RateLimitConfig, RateLimitResult, RateLimitStrategy

logger = structlog.get_logger(__name__)


class RateLimiter:
    """
    Gerenciador principal de rate limiting DATAMETRIA.
    
    Integra múltiplas estratégias e reutiliza componentes existentes.
    """
    
    def __init__(
        self,
        redis_client=None,
        config: Optional[RateLimitConfig] = None,
        default_strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    ):
        """
        Inicializa RateLimiter.
        
        Args:
            redis_client: Cliente Redis (usa cache existente se None)
            config: Configuração de rate limiting
            default_strategy: Estratégia padrão
        """
        self.config_manager = BaseConfig()
        
        # Usar cache Redis existente se não fornecido
        if redis_client is None:
            try:
                from datametria_common.utilities.cache_manager import CacheManager
                cache_manager = CacheManager()
                self.redis = cache_manager.redis_client
            except ImportError:
                logger.warning("Redis client not available, rate limiting disabled")
                self.redis = None
        else:
            self.redis = redis_client
        
        # Configuração padrão
        self.config = config or self._get_default_config()
        self.default_strategy = default_strategy
        
        # Inicializar estratégias
        self.strategies = {}
        if self.redis:
            self.strategies[RateLimitStrategy.SLIDING_WINDOW] = SlidingWindowStrategy(self.redis)
            self.strategies[RateLimitStrategy.TOKEN_BUCKET] = TokenBucketStrategy(self.redis)
            self.strategies[RateLimitStrategy.FIXED_WINDOW] = FixedWindowStrategy(self.redis)
        
        # Cache para regras compiladas
        self._compiled_rules = {}
        
        logger.info(
            "RateLimiter initialized",
            enabled=self.config.enabled,
            redis_available=self.redis is not None,
            default_strategy=default_strategy
        )
    
    def _get_default_config(self) -> RateLimitConfig:
        """Obtém configuração padrão de rate limiting."""
        return RateLimitConfig(
            enabled=True,
            default_limits={
                'global': RateLimit(requests=1000, window=60),
                'authenticated': RateLimit(requests=100, window=60),
                'anonymous': RateLimit(requests=20, window=60)
            },
            headers_enabled=True
        )
    
    def is_allowed(
        self,
        key: str,
        endpoint: Optional[str] = None,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        **kwargs
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica se request é permitido.
        
        Args:
            key: Chave base de rate limiting
            endpoint: Endpoint sendo acessado
            user_id: ID do usuário (se autenticado)
            user_role: Role do usuário
            **kwargs: Argumentos adicionais
            
        Returns:
            Tuple[bool, Dict]: (permitido, informações)
        """
        if not self.config.enabled or not self.redis:
            return True, {'allowed': True, 'reason': 'rate_limiting_disabled'}
        
        try:
            # Verificar whitelist/blacklist
            ip = self._extract_ip_from_key(key)
            if ip:
                if ip in self.config.blacklist_ips:
                    return False, {
                        'allowed': False,
                        'reason': 'ip_blacklisted',
                        'ip': ip
                    }
                
                if ip in self.config.whitelist_ips:
                    return True, {
                        'allowed': True,
                        'reason': 'ip_whitelisted',
                        'ip': ip
                    }
            
            # Determinar rate limit aplicável
            rate_limit = self._get_applicable_rate_limit(
                key=key,
                endpoint=endpoint,
                user_id=user_id,
                user_role=user_role
            )
            
            # Obter estratégia
            strategy = self.strategies.get(
                rate_limit.strategy,
                self.strategies.get(self.default_strategy)
            )
            
            if not strategy:
                logger.warning("No strategy available", strategy=rate_limit.strategy)
                return True, {'allowed': True, 'reason': 'no_strategy'}
            
            # Verificar rate limit
            allowed, info = strategy.is_allowed(
                key=key,
                limit=rate_limit.requests,
                window=rate_limit.window,
                **kwargs
            )
            
            # Adicionar informações extras
            info.update({
                'key': key,
                'endpoint': endpoint,
                'user_id': user_id,
                'rate_limit_config': rate_limit.dict()
            })
            
            # Log da verificação
            logger.info(
                "Rate limit check completed",
                key=key,
                endpoint=endpoint,
                allowed=allowed,
                remaining=info.get('remaining'),
                strategy=rate_limit.strategy
            )
            
            return allowed, info
            
        except Exception as e:
            logger.error("Rate limit check failed", key=key, error=str(e))
            # Fail open em caso de erro
            return True, {
                'allowed': True,
                'reason': 'error',
                'error': str(e)
            }
    
    def _get_applicable_rate_limit(
        self,
        key: str,
        endpoint: Optional[str] = None,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None
    ) -> RateLimit:
        """
        Determina o rate limit aplicável baseado em prioridades.
        
        Args:
            key: Chave de rate limiting
            endpoint: Endpoint sendo acessado
            user_id: ID do usuário
            user_role: Role do usuário
            
        Returns:
            RateLimit: Configuração aplicável
        """
        # 1. Verificar limites por usuário específico
        if user_id and self.config.per_user_limits:
            user_key = f"user:{user_id}"
            if user_key in self.config.per_user_limits:
                return self.config.per_user_limits[user_key]
        
        # 2. Verificar limites por endpoint
        if endpoint and self.config.per_endpoint_limits:
            if endpoint in self.config.per_endpoint_limits:
                return self.config.per_endpoint_limits[endpoint]
            
            # Verificar padrões de endpoint
            for pattern, rate_limit in self.config.per_endpoint_limits.items():
                if self._match_endpoint_pattern(endpoint, pattern):
                    return rate_limit
        
        # 3. Usar limites padrão baseado no tipo de usuário
        if user_id:
            return self.config.default_limits.get(
                'authenticated',
                self.config.default_limits['global']
            )
        else:
            return self.config.default_limits.get(
                'anonymous',
                self.config.default_limits['global']
            )
    
    def _match_endpoint_pattern(self, endpoint: str, pattern: str) -> bool:
        """
        Verifica se endpoint corresponde ao padrão.
        
        Args:
            endpoint: Endpoint a verificar
            pattern: Padrão (regex ou glob)
            
        Returns:
            bool: True se corresponde
        """
        if pattern not in self._compiled_rules:
            try:
                self._compiled_rules[pattern] = re.compile(pattern)
            except re.error:
                logger.warning("Invalid regex pattern", pattern=pattern)
                return False
        
        return bool(self._compiled_rules[pattern].match(endpoint))
    
    def _extract_ip_from_key(self, key: str) -> Optional[str]:
        """
        Extrai IP da chave de rate limiting.
        
        Args:
            key: Chave de rate limiting
            
        Returns:
            str: IP extraído ou None
        """
        if key.startswith('ip:'):
            return key[3:]
        return None
    
    def reset_key(self, key: str, strategy: Optional[RateLimitStrategy] = None) -> None:
        """
        Reset do rate limit para uma chave específica.
        
        Args:
            key: Chave para reset
            strategy: Estratégia específica (todas se None)
        """
        if not self.redis:
            return
        
        try:
            if strategy:
                strategy_obj = self.strategies.get(strategy)
                if strategy_obj:
                    strategy_obj.reset(key)
            else:
                # Reset em todas as estratégias
                for strategy_obj in self.strategies.values():
                    strategy_obj.reset(key)
            
            logger.info("Rate limit reset", key=key, strategy=strategy)
            
        except Exception as e:
            logger.error("Failed to reset rate limit", key=key, error=str(e))
    
    def get_status(self, key: str) -> Dict[str, Any]:
        """
        Obtém status atual de rate limiting para uma chave.
        
        Args:
            key: Chave para verificar
            
        Returns:
            Dict: Status atual
        """
        if not self.redis:
            return {'available': False, 'reason': 'redis_not_available'}
        
        try:
            status = {}
            
            # Verificar status em cada estratégia
            for strategy_name, strategy_obj in self.strategies.items():
                # Fazer verificação sem consumir quota
                allowed, info = strategy_obj.is_allowed(key, 1000, 60)
                status[strategy_name.value] = {
                    'remaining': info.get('remaining', 0),
                    'limit': info.get('limit', 0),
                    'reset_time': info.get('reset_time', 0)
                }
            
            return status
            
        except Exception as e:
            logger.error("Failed to get rate limit status", key=key, error=str(e))
            return {'error': str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtém métricas de rate limiting.
        
        Returns:
            Dict: Métricas coletadas
        """
        if not self.redis:
            return {'available': False}
        
        try:
            metrics = {
                'total_keys': 0,
                'strategies': {},
                'config': {
                    'enabled': self.config.enabled,
                    'default_limits': len(self.config.default_limits),
                    'per_user_limits': len(self.config.per_user_limits or {}),
                    'per_endpoint_limits': len(self.config.per_endpoint_limits or {}),
                    'whitelist_ips': len(self.config.whitelist_ips),
                    'blacklist_ips': len(self.config.blacklist_ips)
                }
            }
            
            # Contar chaves por estratégia
            for strategy_name in self.strategies.keys():
                pattern = f"{strategy_name.value}:*"
                keys = self.redis.keys(pattern)
                metrics['strategies'][strategy_name.value] = len(keys)
                metrics['total_keys'] += len(keys)
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to get rate limit metrics", error=str(e))
            return {'error': str(e)}
    
    def update_config(self, config: RateLimitConfig) -> None:
        """
        Atualiza configuração de rate limiting.
        
        Args:
            config: Nova configuração
        """
        self.config = config
        self._compiled_rules.clear()  # Limpar cache de regras
        
        logger.info("Rate limit config updated", enabled=config.enabled)
    
    def add_user_limit(self, user_id: int, rate_limit: RateLimit) -> None:
        """
        Adiciona limite específico para usuário.
        
        Args:
            user_id: ID do usuário
            rate_limit: Configuração de rate limit
        """
        if not self.config.per_user_limits:
            self.config.per_user_limits = {}
        
        self.config.per_user_limits[f"user:{user_id}"] = rate_limit
        
        logger.info("User rate limit added", user_id=user_id, rate_limit=rate_limit.dict())
    
    def add_endpoint_limit(self, endpoint_pattern: str, rate_limit: RateLimit) -> None:
        """
        Adiciona limite específico para endpoint.
        
        Args:
            endpoint_pattern: Padrão do endpoint (regex)
            rate_limit: Configuração de rate limit
        """
        if not self.config.per_endpoint_limits:
            self.config.per_endpoint_limits = {}
        
        self.config.per_endpoint_limits[endpoint_pattern] = rate_limit
        
        # Limpar cache de regras compiladas
        if endpoint_pattern in self._compiled_rules:
            del self._compiled_rules[endpoint_pattern]
        
        logger.info("Endpoint rate limit added", pattern=endpoint_pattern, rate_limit=rate_limit.dict())
