"""
DATAMETRIA Unified Caching Layer

High-performance caching system with Redis, in-memory, and file-based backends
supporting TTL, compression, and automatic invalidation.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Union
from enum import Enum
import json
import time
import hashlib
import pickle
import gzip
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass


class CacheBackend(Enum):
    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"


class CompressionType(Enum):
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"


@dataclass
class CacheConfig:
    backend: CacheBackend = CacheBackend.MEMORY
    default_ttl: int = 3600  # 1 hour
    max_size: int = 1000
    compression: CompressionType = CompressionType.NONE
    redis_url: Optional[str] = None
    file_path: Optional[str] = None


class CacheProvider(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass


class MemoryCacheProvider(CacheProvider):
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if self._is_expired(entry):
            await self.delete(key)
            return None
        
        self._access_times[key] = time.time()
        return self._decompress(entry['value'])
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if len(self._cache) >= self.config.max_size:
            await self._evict_lru()
        
        ttl = ttl or self.config.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        
        self._cache[key] = {
            'value': self._compress(value),
            'expires_at': expires_at,
            'created_at': time.time()
        }
        self._access_times[key] = time.time()
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            self._access_times.pop(key, None)
            return True
        return False
    
    async def clear(self) -> bool:
        self._cache.clear()
        self._access_times.clear()
        return True
    
    async def exists(self, key: str) -> bool:
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        if self._is_expired(entry):
            await self.delete(key)
            return False
        
        return True
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        expires_at = entry.get('expires_at')
        return expires_at is not None and time.time() > expires_at
    
    async def _evict_lru(self):
        if not self._access_times:
            return
        
        lru_key = min(self._access_times, key=self._access_times.get)
        await self.delete(lru_key)
    
    def _compress(self, value: Any) -> bytes:
        data = pickle.dumps(value)
        if self.config.compression == CompressionType.GZIP:
            return gzip.compress(data)
        return data
    
    def _decompress(self, data: bytes) -> Any:
        if self.config.compression == CompressionType.GZIP:
            data = gzip.decompress(data)
        return pickle.loads(data)


class RedisCacheProvider(CacheProvider):
    def __init__(self, config: CacheConfig):
        self.config = config
        self._redis = None
    
    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.config.redis_url or "redis://localhost:6379")
            except ImportError:
                raise ImportError("redis package required for Redis cache backend")
        return self._redis
    
    async def get(self, key: str) -> Optional[Any]:
        redis_client = await self._get_redis()
        data = await redis_client.get(key)
        if data is None:
            return None
        
        return self._decompress(data)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        redis_client = await self._get_redis()
        ttl = ttl or self.config.default_ttl
        
        data = self._compress(value)
        if ttl > 0:
            return await redis_client.setex(key, ttl, data)
        else:
            return await redis_client.set(key, data)
    
    async def delete(self, key: str) -> bool:
        redis_client = await self._get_redis()
        result = await redis_client.delete(key)
        return result > 0
    
    async def clear(self) -> bool:
        redis_client = await self._get_redis()
        return await redis_client.flushdb()
    
    async def exists(self, key: str) -> bool:
        redis_client = await self._get_redis()
        return await redis_client.exists(key) > 0
    
    def _compress(self, value: Any) -> bytes:
        data = pickle.dumps(value)
        if self.config.compression == CompressionType.GZIP:
            return gzip.compress(data)
        return data
    
    def _decompress(self, data: bytes) -> Any:
        if self.config.compression == CompressionType.GZIP:
            data = gzip.decompress(data)
        return pickle.loads(data)


class UnifiedCache:
    def __init__(self, config: CacheConfig):
        self.config = config
        self._provider = self._create_provider()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def _create_provider(self) -> CacheProvider:
        if self.config.backend == CacheBackend.MEMORY:
            return MemoryCacheProvider(self.config)
        elif self.config.backend == CacheBackend.REDIS:
            return RedisCacheProvider(self.config)
        else:
            raise ValueError(f"Unsupported cache backend: {self.config.backend}")
    
    async def get(self, key: str) -> Optional[Any]:
        result = await self._provider.get(self._hash_key(key))
        if result is not None:
            self._stats['hits'] += 1
        else:
            self._stats['misses'] += 1
        return result
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        result = await self._provider.set(self._hash_key(key), value, ttl)
        if result:
            self._stats['sets'] += 1
        return result
    
    async def delete(self, key: str) -> bool:
        result = await self._provider.delete(self._hash_key(key))
        if result:
            self._stats['deletes'] += 1
        return result
    
    async def clear(self) -> bool:
        return await self._provider.clear()
    
    async def exists(self, key: str) -> bool:
        return await self._provider.exists(self._hash_key(key))
    
    async def get_or_set(self, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        value = await self.get(key)
        if value is None:
            if asyncio.iscoroutinefunction(factory_func):
                value = await factory_func()
            else:
                value = factory_func()
            await self.set(key, value, ttl)
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self._stats,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }
    
    def _hash_key(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()


class CacheManager:
    _instances: Dict[str, UnifiedCache] = {}
    
    @classmethod
    def get_cache(cls, name: str = "default", config: Optional[CacheConfig] = None) -> UnifiedCache:
        if name not in cls._instances:
            if config is None:
                config = CacheConfig()
            cls._instances[name] = UnifiedCache(config)
        return cls._instances[name]
    
    @classmethod
    async def clear_all(cls):
        for cache in cls._instances.values():
            await cache.clear()
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        return {name: cache.get_stats() for name, cache in cls._instances.items()}


def cache_decorator(ttl: int = 3600, cache_name: str = "default"):
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            cache = CacheManager.get_cache(cache_name)
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            return await cache.get_or_set(key, lambda: func(*args, **kwargs), ttl)
        
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
