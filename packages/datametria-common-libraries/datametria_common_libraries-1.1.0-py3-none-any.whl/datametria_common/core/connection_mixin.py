"""
DATAMETRIA ConnectionMixin - Universal Connection Manager Pattern

Universal connection management pattern for all DATAMETRIA database components.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone

from .health_check import HealthCheckMixin
from .error_handler import ErrorHandlerMixin, ErrorCategory


class ConnectionMixin(ABC):
    """Universal connection manager mixin for all DATAMETRIA database components.
    
    Provides standardized connection management with:
    - Connection pooling
    - Health monitoring
    - Error handling
    - Retry logic
    
    Example:
        >>> class MyDBService(ConnectionMixin):
        ...     async def _create_connection(self):
        ...         return await connect_to_db()
        >>> 
        >>> service = MyDBService()
        >>> async with service.get_connection() as conn:
        ...     result = await conn.execute("SELECT 1")
    """
    
    def __init__(self):
        """Initialize connection mixin."""
        self._connection_pool: Dict[str, Any] = {}
        self._connection_config: Dict[str, Any] = {}
        self._max_connections: int = 10
        self._connection_timeout: int = 30
    
    @abstractmethod
    async def _create_connection(self) -> Any:
        """Create a new database connection.
        
        Must be implemented by subclasses to create database-specific connections.
        
        Returns:
            Database connection object
        """
        pass
    
    @abstractmethod
    async def _close_connection(self, connection: Any) -> None:
        """Close a database connection.
        
        Args:
            connection: Connection to close
        """
        pass
    
    @abstractmethod
    async def _validate_connection(self, connection: Any) -> bool:
        """Validate if connection is still active.
        
        Args:
            connection: Connection to validate
            
        Returns:
            True if connection is valid
        """
        pass
    
    async def get_connection(self) -> Any:
        """Get a connection from the pool."""
        try:
            # Try to get existing connection
            for conn_id, conn in self._connection_pool.items():
                if await self._validate_connection(conn):
                    return conn
            
            # Create new connection if pool is empty or all invalid
            if len(self._connection_pool) < self._max_connections:
                conn = await self._create_connection()
                conn_id = f"conn_{len(self._connection_pool)}"
                self._connection_pool[conn_id] = conn
                return conn
            
            raise RuntimeError("Connection pool exhausted")
            
        except Exception as e:
            if hasattr(self, 'handle_error'):
                self.handle_error(e, ErrorCategory.DATABASE)
            raise
    
    @asynccontextmanager
    async def connection_context(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = await self.get_connection()
            yield conn
        finally:
            if conn:
                await self._release_connection(conn)
    
    async def _release_connection(self, connection: Any) -> None:
        """Release connection back to pool."""
        # In a real implementation, this would return connection to pool
        # For now, we keep it simple
        pass
    
    async def close_all_connections(self) -> None:
        """Close all connections in the pool."""
        for conn in self._connection_pool.values():
            try:
                await self._close_connection(conn)
            except Exception:
                pass  # Ignore errors when closing
        
        self._connection_pool.clear()
    
    def configure_connection(self, **config) -> None:
        """Configure connection parameters."""
        self._connection_config.update(config)
        self._max_connections = config.get('max_connections', 10)
        self._connection_timeout = config.get('timeout', 30)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            'active_connections': len(self._connection_pool),
            'max_connections': self._max_connections,
            'connection_timeout': self._connection_timeout
        }
