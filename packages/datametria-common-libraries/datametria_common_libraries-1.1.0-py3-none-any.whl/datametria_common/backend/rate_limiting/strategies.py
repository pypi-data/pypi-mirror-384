"""
🚦 Rate Limiting Strategies - DATAMETRIA Rate Limiting

Diferentes estratégias de rate limiting com Redis backend.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class RateLimitStrategy(ABC):
    """Classe base para estratégias de rate limiting."""
    
    def __init__(self, redis_client):
        """
        Inicializa estratégia.
        
        Args:
            redis_client: Cliente Redis
        """
        self.redis = redis_client
    
    @abstractmethod
    def is_allowed(self, key: str, limit: int, window: int, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica se request é permitido.
        
        Args:
            key: Chave de rate limiting
            limit: Limite de requests
            window: Janela de tempo em segundos
            **kwargs: Argumentos adicionais
            
        Returns:
            Tuple[bool, Dict]: (permitido, informações)
        """
        pass
    
    @abstractmethod
    def reset(self, key: str) -> None:
        """
        Reset do rate limit para uma chave.
        
        Args:
            key: Chave para reset
        """
        pass


class SlidingWindowStrategy(RateLimitStrategy):
    """Estratégia de janela deslizante usando Redis sorted sets."""
    
    def __init__(self, redis_client):
        super().__init__(redis_client)
        
        # Script Lua para operação atômica
        self.script = self.redis.register_script("""
            local key = KEYS[1]
            local window = tonumber(ARGV[1])
            local limit = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            local identifier = ARGV[4]
            
            -- Remove entradas expiradas
            redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
            
            -- Conta requests atuais
            local current = redis.call('ZCARD', key)
            
            if current < limit then
                -- Adiciona request atual
                redis.call('ZADD', key, now, identifier)
                redis.call('EXPIRE', key, window)
                return {1, limit - current - 1, now + window}
            else
                -- Calcula tempo para próximo slot disponível
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                local retry_after = 0
                if #oldest > 0 then
                    retry_after = math.ceil(tonumber(oldest[2]) + window - now)
                end
                return {0, 0, now + retry_after}
            end
        """)
    
    def is_allowed(self, key: str, limit: int, window: int, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica se request é permitido usando sliding window.
        
        Args:
            key: Chave de rate limiting
            limit: Limite de requests
            window: Janela de tempo em segundos
            
        Returns:
            Tuple[bool, Dict]: (permitido, informações)
        """
        now = time.time()
        identifier = f"{now}:{kwargs.get('request_id', 'req')}"
        
        try:
            result = self.script(
                keys=[f"sliding:{key}"],
                args=[window, limit, now, identifier]
            )
            
            allowed = bool(result[0])
            remaining = result[1]
            reset_time = result[2]
            
            info = {
                'allowed': allowed,
                'remaining': remaining,
                'limit': limit,
                'reset_time': reset_time,
                'window': window,
                'strategy': 'sliding_window'
            }
            
            if not allowed:
                info['retry_after'] = max(1, int(reset_time - now))
            
            logger.debug(
                "Sliding window rate limit check",
                key=key,
                allowed=allowed,
                remaining=remaining,
                limit=limit
            )
            
            return allowed, info
            
        except Exception as e:
            logger.error("Sliding window rate limit error", key=key, error=str(e))
            # Em caso de erro, permitir request (fail open)
            return True, {
                'allowed': True,
                'remaining': limit,
                'limit': limit,
                'reset_time': now + window,
                'strategy': 'sliding_window',
                'error': str(e)
            }
    
    def reset(self, key: str) -> None:
        """Reset do sliding window para uma chave."""
        try:
            self.redis.delete(f"sliding:{key}")
            logger.info("Sliding window reset", key=key)
        except Exception as e:
            logger.error("Failed to reset sliding window", key=key, error=str(e))


class TokenBucketStrategy(RateLimitStrategy):
    """Estratégia de token bucket para controle de burst."""
    
    def __init__(self, redis_client):
        super().__init__(redis_client)
        
        # Script Lua para token bucket
        self.script = self.redis.register_script("""
            local key = KEYS[1]
            local capacity = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local requested = tonumber(ARGV[3])
            local now = tonumber(ARGV[4])
            
            local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
            local tokens = tonumber(bucket[1]) or capacity
            local last_refill = tonumber(bucket[2]) or now
            
            -- Calcula tokens para adicionar
            local time_passed = now - last_refill
            local tokens_to_add = math.floor(time_passed * refill_rate)
            tokens = math.min(capacity, tokens + tokens_to_add)
            
            if tokens >= requested then
                tokens = tokens - requested
                redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
                redis.call('EXPIRE', key, 3600)
                return {1, tokens, capacity}
            else
                redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
                redis.call('EXPIRE', key, 3600)
                -- Calcula tempo para ter tokens suficientes
                local needed_tokens = requested - tokens
                local wait_time = math.ceil(needed_tokens / refill_rate)
                return {0, tokens, capacity, wait_time}
            end
        """)
    
    def is_allowed(self, key: str, limit: int, window: int, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica se request é permitido usando token bucket.
        
        Args:
            key: Chave de rate limiting
            limit: Capacidade do bucket (tokens)
            window: Não usado diretamente (refill rate calculado)
            
        Returns:
            Tuple[bool, Dict]: (permitido, informações)
        """
        now = time.time()
        capacity = limit
        refill_rate = limit / window  # tokens por segundo
        requested = kwargs.get('tokens', 1)
        
        try:
            result = self.script(
                keys=[f"bucket:{key}"],
                args=[capacity, refill_rate, requested, now]
            )
            
            allowed = bool(result[0])
            remaining_tokens = result[1]
            bucket_capacity = result[2]
            
            info = {
                'allowed': allowed,
                'remaining': remaining_tokens,
                'limit': capacity,
                'reset_time': now + window,
                'strategy': 'token_bucket',
                'refill_rate': refill_rate
            }
            
            if not allowed and len(result) > 3:
                info['retry_after'] = result[3]
            
            logger.debug(
                "Token bucket rate limit check",
                key=key,
                allowed=allowed,
                remaining=remaining_tokens,
                capacity=capacity
            )
            
            return allowed, info
            
        except Exception as e:
            logger.error("Token bucket rate limit error", key=key, error=str(e))
            return True, {
                'allowed': True,
                'remaining': limit,
                'limit': limit,
                'reset_time': now + window,
                'strategy': 'token_bucket',
                'error': str(e)
            }
    
    def reset(self, key: str) -> None:
        """Reset do token bucket para uma chave."""
        try:
            self.redis.delete(f"bucket:{key}")
            logger.info("Token bucket reset", key=key)
        except Exception as e:
            logger.error("Failed to reset token bucket", key=key, error=str(e))


class FixedWindowStrategy(RateLimitStrategy):
    """Estratégia de janela fixa simples."""
    
    def __init__(self, redis_client):
        super().__init__(redis_client)
        
        # Script Lua para janela fixa
        self.script = self.redis.register_script("""
            local key = KEYS[1]
            local limit = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            
            -- Calcula início da janela atual
            local window_start = math.floor(now / window) * window
            local window_key = key .. ':' .. window_start
            
            -- Incrementa contador
            local current = redis.call('INCR', window_key)
            
            if current == 1 then
                -- Primeira request na janela, define expiração
                redis.call('EXPIRE', window_key, window)
            end
            
            if current <= limit then
                local reset_time = window_start + window
                return {1, limit - current, reset_time}
            else
                local reset_time = window_start + window
                local retry_after = reset_time - now
                return {0, 0, reset_time, retry_after}
            end
        """)
    
    def is_allowed(self, key: str, limit: int, window: int, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica se request é permitido usando janela fixa.
        
        Args:
            key: Chave de rate limiting
            limit: Limite de requests
            window: Janela de tempo em segundos
            
        Returns:
            Tuple[bool, Dict]: (permitido, informações)
        """
        now = time.time()
        
        try:
            result = self.script(
                keys=[f"fixed:{key}"],
                args=[limit, window, now]
            )
            
            allowed = bool(result[0])
            remaining = result[1]
            reset_time = result[2]
            
            info = {
                'allowed': allowed,
                'remaining': remaining,
                'limit': limit,
                'reset_time': reset_time,
                'window': window,
                'strategy': 'fixed_window'
            }
            
            if not allowed and len(result) > 3:
                info['retry_after'] = max(1, int(result[3]))
            
            logger.debug(
                "Fixed window rate limit check",
                key=key,
                allowed=allowed,
                remaining=remaining,
                limit=limit
            )
            
            return allowed, info
            
        except Exception as e:
            logger.error("Fixed window rate limit error", key=key, error=str(e))
            return True, {
                'allowed': True,
                'remaining': limit,
                'limit': limit,
                'reset_time': now + window,
                'strategy': 'fixed_window',
                'error': str(e)
            }
    
    def reset(self, key: str) -> None:
        """Reset da janela fixa para uma chave."""
        try:
            # Remove todas as janelas para a chave
            pattern = f"fixed:{key}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
            logger.info("Fixed window reset", key=key, keys_removed=len(keys))
        except Exception as e:
            logger.error("Failed to reset fixed window", key=key, error=str(e))
