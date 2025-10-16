"""
DATAMETRIA Cache Mixins

Mixins for integrating caching capabilities into existing components
with automatic cache key generation and invalidation strategies.
"""

from typing import Any, Optional, Dict, Callable
import asyncio
import inspect
from functools import wraps
from .unified_cache import CacheManager, CacheConfig, CacheBackend


class CacheMixin:
    """Mixin to add caching capabilities to any class."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_config = kwargs.get('cache_config', CacheConfig())
        self._cache_name = f"{self.__class__.__name__.lower()}_cache"
        self._cache = CacheManager.get_cache(self._cache_name, self._cache_config)
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return await self._cache.get(self._generate_cache_key(key))
    
    async def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        return await self._cache.set(self._generate_cache_key(key), value, ttl)
    
    async def cache_delete(self, key: str) -> bool:
        """Delete value from cache."""
        return await self._cache.delete(self._generate_cache_key(key))
    
    async def cache_clear(self) -> bool:
        """Clear all cache entries."""
        return await self._cache.clear()
    
    async def cache_get_or_set(self, key: str, factory_func: Callable, ttl: Optional[int] = None) -> Any:
        """Get from cache or set using factory function."""
        return await self._cache.get_or_set(self._generate_cache_key(key), factory_func, ttl)
    
    def _generate_cache_key(self, key: str) -> str:
        """Generate cache key with class prefix."""
        return f"{self.__class__.__name__}:{key}"
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_stats()


class DatabaseCacheMixin(CacheMixin):
    """Specialized caching mixin for database operations."""
    
    def __init__(self, *args, **kwargs):
        cache_config = kwargs.get('cache_config', CacheConfig(
            backend=CacheBackend.REDIS,
            default_ttl=1800,  # 30 minutes
            max_size=5000
        ))
        kwargs['cache_config'] = cache_config
        super().__init__(*args, **kwargs)
    
    async def cache_query(self, query: str, params: tuple = (), ttl: Optional[int] = None) -> Optional[Any]:
        """Cache database query results."""
        key = f"query:{hash(query + str(params))}"
        return await self.cache_get(key)
    
    async def cache_query_result(self, query: str, params: tuple, result: Any, ttl: Optional[int] = None) -> bool:
        """Cache database query result."""
        key = f"query:{hash(query + str(params))}"
        return await self.cache_set(key, result, ttl)
    
    async def invalidate_table_cache(self, table_name: str) -> int:
        """Invalidate all cache entries for a specific table."""
        # Simplified implementation - would use pattern matching in production
        await self.cache_clear()
        return 1


class APICacheMixin(CacheMixin):
    """Specialized caching mixin for API responses."""
    
    def __init__(self, *args, **kwargs):
        cache_config = kwargs.get('cache_config', CacheConfig(
            backend=CacheBackend.MEMORY,
            default_ttl=600,  # 10 minutes
            max_size=1000
        ))
        kwargs['cache_config'] = cache_config
        super().__init__(*args, **kwargs)
    
    async def cache_api_response(self, endpoint: str, params: Dict[str, Any] = None, ttl: Optional[int] = None) -> Optional[Any]:
        """Get cached API response."""
        key = f"api:{endpoint}:{hash(str(params or {}))}"
        return await self.cache_get(key)
    
    async def cache_api_result(self, endpoint: str, params: Dict[str, Any], result: Any, ttl: Optional[int] = None) -> bool:
        """Cache API response."""
        key = f"api:{endpoint}:{hash(str(params or {}))}"
        return await self.cache_set(key, result, ttl)


def cached_method(ttl: int = 3600, key_func: Optional[Callable] = None):
    """Decorator for caching method results."""
    def decorator(method):
        @wraps(method)
        async def async_wrapper(self, *args, **kwargs):
            if not hasattr(self, '_cache'):
                # Initialize cache if not present
                self._cache = CacheManager.get_cache(f"{self.__class__.__name__.lower()}_method_cache")
            
            # Generate cache key
            if key_func:
                cache_key = key_func(self, *args, **kwargs)
            else:
                cache_key = f"{method.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = await self._cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute method and cache result
            if asyncio.iscoroutinefunction(method):
                result = await method(self, *args, **kwargs)
            else:
                result = method(self, *args, **kwargs)
            
            await self._cache.set(cache_key, result, ttl)
            return result
        
        def sync_wrapper(self, *args, **kwargs):
            return asyncio.run(async_wrapper(self, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(method):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_invalidate(pattern: str = None):
    """Decorator to invalidate cache after method execution."""
    def decorator(method):
        @wraps(method)
        async def async_wrapper(self, *args, **kwargs):
            result = await method(self, *args, **kwargs) if asyncio.iscoroutinefunction(method) else method(self, *args, **kwargs)
            
            if hasattr(self, '_cache'):
                if pattern:
                    # Would implement pattern-based invalidation
                    await self._cache.clear()
                else:
                    await self._cache.clear()
            
            return result
        
        def sync_wrapper(self, *args, **kwargs):
            return asyncio.run(async_wrapper(self, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(method):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
