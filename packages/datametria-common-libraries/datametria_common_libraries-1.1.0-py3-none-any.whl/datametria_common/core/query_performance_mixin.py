"""
DATAMETRIA QueryPerformanceMixin - Universal Query Performance Monitoring

Universal query performance monitoring mixin for all DATAMETRIA database components.
"""

import time
from abc import ABC
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query: str
    duration_ms: float
    rows_affected: int
    timestamp: datetime
    table_name: Optional[str] = None
    operation_type: Optional[str] = None


class QueryPerformanceMixin(ABC):
    """Universal query performance monitoring mixin.
    
    Provides standardized performance monitoring:
    - Query execution timing
    - Performance metrics collection
    - Slow query detection
    - Performance statistics
    
    Example:
        >>> class MyDBService(QueryPerformanceMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self._init_performance_monitoring()
        >>> 
        >>> service = MyDBService()
        >>> with service.monitor_query("SELECT * FROM users") as monitor:
        ...     result = execute_query()
        >>> metrics = service.get_performance_stats()
    """
    
    def __init__(self):
        """Initialize query performance monitoring."""
        self._query_metrics: List[QueryMetrics] = []
        self._slow_query_threshold_ms: float = 1000.0
        self._max_metrics_history: int = 1000
    
    def _init_performance_monitoring(self, slow_query_threshold_ms: float = 1000.0) -> None:
        """Initialize performance monitoring configuration."""
        self._slow_query_threshold_ms = slow_query_threshold_ms
    
    def monitor_query(self, query: str, table_name: Optional[str] = None):
        """Context manager for query performance monitoring."""
        return QueryMonitor(self, query, table_name)
    
    def record_query_metrics(self, query: str, duration_ms: float, 
                           rows_affected: int = 0, table_name: Optional[str] = None) -> None:
        """Record query performance metrics."""
        operation_type = self._extract_operation_type(query)
        
        metrics = QueryMetrics(
            query=query[:100] + "..." if len(query) > 100 else query,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            timestamp=datetime.now(timezone.utc),
            table_name=table_name,
            operation_type=operation_type
        )
        
        self._query_metrics.append(metrics)
        
        # Keep only recent metrics
        if len(self._query_metrics) > self._max_metrics_history:
            self._query_metrics = self._query_metrics[-self._max_metrics_history:]
        
        # Log slow queries
        if duration_ms > self._slow_query_threshold_ms:
            self._log_slow_query(metrics)
    
    def _extract_operation_type(self, query: str) -> str:
        """Extract operation type from query."""
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _log_slow_query(self, metrics: QueryMetrics) -> None:
        """Log slow query for analysis."""
        if hasattr(self, 'log_security_event'):
            self.log_security_event("slow_query_detected", {
                "query": metrics.query,
                "duration_ms": metrics.duration_ms,
                "table": metrics.table_name,
                "operation": metrics.operation_type
            })
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if not self._query_metrics:
            return {"total_queries": 0}
        
        durations = [m.duration_ms for m in self._query_metrics]
        operations = {}
        slow_queries = 0
        
        for metrics in self._query_metrics:
            op_type = metrics.operation_type or 'OTHER'
            operations[op_type] = operations.get(op_type, 0) + 1
            
            if metrics.duration_ms > self._slow_query_threshold_ms:
                slow_queries += 1
        
        return {
            "total_queries": len(self._query_metrics),
            "avg_duration_ms": sum(durations) / len(durations),
            "max_duration_ms": max(durations),
            "min_duration_ms": min(durations),
            "slow_queries": slow_queries,
            "operations_by_type": operations,
            "slow_query_threshold_ms": self._slow_query_threshold_ms
        }
    
    def get_slow_queries(self) -> List[QueryMetrics]:
        """Get list of slow queries."""
        return [
            m for m in self._query_metrics 
            if m.duration_ms > self._slow_query_threshold_ms
        ]
    
    def reset_performance_stats(self) -> None:
        """Reset performance statistics."""
        self._query_metrics.clear()


class QueryMonitor:
    """Context manager for query performance monitoring."""
    
    def __init__(self, performance_mixin: QueryPerformanceMixin, 
                 query: str, table_name: Optional[str] = None):
        self.performance_mixin = performance_mixin
        self.query = query
        self.table_name = table_name
        self.start_time = 0.0
        self.rows_affected = 0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.performance_mixin.record_query_metrics(
            self.query, duration_ms, self.rows_affected, self.table_name
        )
    
    def set_rows_affected(self, rows: int) -> None:
        """Set number of rows affected by the query."""
        self.rows_affected = rows
