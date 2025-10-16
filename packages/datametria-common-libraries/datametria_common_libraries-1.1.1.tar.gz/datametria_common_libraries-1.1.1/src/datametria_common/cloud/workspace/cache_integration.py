"""
Workspace Cache Integration - Unified Cache for Google Workspace APIs

Provides centralized cache management with:
- Automatic cache initialization from WorkspaceConfig
- Cache key namespacing per API
- Performance metrics tracking
- Cache invalidation strategies
"""

from typing import Optional, Any
from ...caching.unified_cache import UnifiedCache, CacheConfig, CacheBackend, CompressionType
from .config import WorkspaceConfig


class WorkspaceCacheManager:
    """Centralized cache manager for Workspace APIs"""
    
    _instance: Optional['WorkspaceCacheManager'] = None
    
    def __init__(self, config: WorkspaceConfig):
        self.config = config
        self._cache: Optional[UnifiedCache] = None
        self._initialize_cache()
    
    @classmethod
    def get_instance(cls, config: WorkspaceConfig) -> 'WorkspaceCacheManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def _initialize_cache(self):
        """Initialize Unified Cache from config"""
        if not self.config.cache_enabled:
            return
        
        # Map string backend to enum
        backend_map = {
            'memory': CacheBackend.MEMORY,
            'redis': CacheBackend.REDIS,
            'file': CacheBackend.FILE
        }
        
        backend = backend_map.get(self.config.cache_backend, CacheBackend.MEMORY)
        
        # Map compression
        compression = CompressionType.GZIP if self.config.cache_compression else CompressionType.NONE
        
        cache_config = CacheConfig(
            backend=backend,
            default_ttl=self.config.cache_ttl,
            max_size=self.config.cache_max_size,
            compression=compression,
            redis_url=self.config.redis_url
        )
        
        self._cache = UnifiedCache(cache_config)
    
    def get_cache(self) -> Optional[UnifiedCache]:
        """Get cache instance"""
        return self._cache
    
    def is_enabled(self) -> bool:
        """Check if cache is enabled"""
        return self._cache is not None
    
    def get_namespaced_key(self, api: str, key: str) -> str:
        """Get namespaced cache key"""
        return f"workspace:{api}:{key}"
    
    async def get(self, api: str, key: str) -> Optional[Any]:
        """Get value from cache with API namespace"""
        if not self.is_enabled():
            return None
        
        namespaced_key = self.get_namespaced_key(api, key)
        return await self._cache.get(namespaced_key)
    
    async def set(self, api: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with API namespace"""
        if not self.is_enabled():
            return False
        
        namespaced_key = self.get_namespaced_key(api, key)
        return await self._cache.set(namespaced_key, value, ttl)
    
    async def delete(self, api: str, key: str) -> bool:
        """Delete value from cache"""
        if not self.is_enabled():
            return False
        
        namespaced_key = self.get_namespaced_key(api, key)
        return await self._cache.delete(namespaced_key)
    
    async def clear_api(self, api: str):
        """Clear all cache entries for an API (not implemented in base cache)"""
        # Note: This would require pattern matching which is not in base UnifiedCache
        # For now, just document that full clear is available
        pass
    
    async def clear_all(self) -> bool:
        """Clear all cache"""
        if not self.is_enabled():
            return False
        
        return await self._cache.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.is_enabled():
            return {
                'enabled': False,
                'backend': self.config.cache_backend,
                'hits': 0,
                'misses': 0,
                'hit_rate': 0
            }
        
        stats = self._cache.get_stats()
        stats['enabled'] = True
        stats['backend'] = self.config.cache_backend
        return stats
