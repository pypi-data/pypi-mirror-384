"""
DATAMETRIA Monitoring Mixins

Mixins for integrating performance monitoring into existing components
with automatic metrics collection and alerting.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from functools import wraps
from .performance_monitor import PerformanceMonitor, PerformanceTimer, get_default_monitor


class MonitoringMixin:
    """Base mixin for adding monitoring capabilities to any class."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._monitor = kwargs.get('performance_monitor', get_default_monitor())
        self._component_name = self.__class__.__name__.lower()
    
    def increment_metric(self, metric_name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        full_name = f"{self._component_name}.{metric_name}"
        self._monitor.collector.increment_counter(full_name, value, labels)
    
    def set_metric(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric."""
        full_name = f"{self._component_name}.{metric_name}"
        self._monitor.collector.set_gauge(full_name, value, labels)
    
    def time_operation(self, operation_name: str, labels: Dict[str, str] = None):
        """Get timer context manager for operation."""
        full_name = f"{self._component_name}.{operation_name}.duration"
        return PerformanceTimer(self._monitor, full_name, labels)
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics for this component."""
        component_metrics = {}
        
        for metric in self._monitor.collector.get_metrics():
            if metric.name.startswith(self._component_name):
                component_metrics[metric.name] = {
                    'value': metric.value,
                    'type': metric.metric_type.value,
                    'timestamp': metric.timestamp.isoformat()
                }
        
        return component_metrics


class DatabaseMonitoringMixin(MonitoringMixin):
    """Specialized monitoring mixin for database operations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set database-specific thresholds
        self._monitor.alert_manager.set_threshold(
            f"{self._component_name}.query.duration", 
            self._monitor.alert_manager.AlertLevel.WARNING, 
            1.0  # 1 second
        )
        self._monitor.alert_manager.set_threshold(
            f"{self._component_name}.query.duration", 
            self._monitor.alert_manager.AlertLevel.CRITICAL, 
            5.0  # 5 seconds
        )
    
    def monitor_query(self, query: str, params: tuple = ()):
        """Monitor database query execution."""
        labels = {
            'query_type': self._get_query_type(query),
            'table': self._extract_table_name(query)
        }
        return self.time_operation("query", labels)
    
    def record_connection_event(self, event_type: str):
        """Record database connection events."""
        self.increment_metric(f"connection.{event_type}")
    
    def record_query_result(self, row_count: int, execution_time: float):
        """Record query execution results."""
        self.set_metric("query.last_row_count", row_count)
        self.increment_metric("query.total_rows", row_count)
        
        # Record execution time
        self._monitor.collector.record_timer(
            f"{self._component_name}.query.duration", 
            execution_time
        )
    
    def _get_query_type(self, query: str) -> str:
        """Extract query type from SQL."""
        query_upper = query.strip().upper()
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
    
    def _extract_table_name(self, query: str) -> str:
        """Extract table name from SQL query."""
        # Simplified table extraction
        words = query.split()
        try:
            if 'FROM' in [w.upper() for w in words]:
                from_index = next(i for i, w in enumerate(words) if w.upper() == 'FROM')
                return words[from_index + 1].strip('`"[]')
            elif 'INTO' in [w.upper() for w in words]:
                into_index = next(i for i, w in enumerate(words) if w.upper() == 'INTO')
                return words[into_index + 1].strip('`"[]')
            elif 'UPDATE' in [w.upper() for w in words]:
                return words[1].strip('`"[]')
        except (IndexError, StopIteration):
            pass
        
        return 'unknown'


class APIMonitoringMixin(MonitoringMixin):
    """Specialized monitoring mixin for API operations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set API-specific thresholds
        self._monitor.alert_manager.set_threshold(
            f"{self._component_name}.request.duration", 
            self._monitor.alert_manager.AlertLevel.WARNING, 
            2.0  # 2 seconds
        )
        self._monitor.alert_manager.set_threshold(
            f"{self._component_name}.request.duration", 
            self._monitor.alert_manager.AlertLevel.CRITICAL, 
            10.0  # 10 seconds
        )
    
    def monitor_request(self, method: str, endpoint: str):
        """Monitor API request execution."""
        labels = {
            'method': method.upper(),
            'endpoint': endpoint
        }
        return self.time_operation("request", labels)
    
    def record_response(self, status_code: int, response_size: int = 0):
        """Record API response metrics."""
        self.increment_metric(f"response.status_{status_code}")
        
        if 200 <= status_code < 300:
            self.increment_metric("response.success")
        elif 400 <= status_code < 500:
            self.increment_metric("response.client_error")
        elif 500 <= status_code < 600:
            self.increment_metric("response.server_error")
        
        if response_size > 0:
            self.set_metric("response.last_size_bytes", response_size)
    
    def record_rate_limit(self, limit: int, remaining: int):
        """Record rate limiting metrics."""
        self.set_metric("rate_limit.limit", limit)
        self.set_metric("rate_limit.remaining", remaining)
        self.set_metric("rate_limit.usage_percent", ((limit - remaining) / limit) * 100)


class CacheMonitoringMixin(MonitoringMixin):
    """Specialized monitoring mixin for cache operations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def record_cache_hit(self, cache_name: str = "default"):
        """Record cache hit."""
        self.increment_metric("cache.hits", labels={'cache': cache_name})
    
    def record_cache_miss(self, cache_name: str = "default"):
        """Record cache miss."""
        self.increment_metric("cache.misses", labels={'cache': cache_name})
    
    def record_cache_set(self, cache_name: str = "default", size_bytes: int = 0):
        """Record cache set operation."""
        self.increment_metric("cache.sets", labels={'cache': cache_name})
        if size_bytes > 0:
            self.set_metric("cache.last_entry_size", size_bytes)
    
    def update_cache_stats(self, hit_rate: float, total_entries: int, cache_name: str = "default"):
        """Update cache statistics."""
        self.set_metric("cache.hit_rate", hit_rate, labels={'cache': cache_name})
        self.set_metric("cache.total_entries", total_entries, labels={'cache': cache_name})


def monitored_method(operation_name: str = None, monitor: PerformanceMonitor = None):
    """Decorator for monitoring method execution."""
    def decorator(method):
        @wraps(method)
        async def async_wrapper(self, *args, **kwargs):
            nonlocal monitor, operation_name
            
            if monitor is None and hasattr(self, '_monitor'):
                monitor = self._monitor
            elif monitor is None:
                monitor = get_default_monitor()
            
            if operation_name is None:
                operation_name = method.__name__
            
            component_name = self.__class__.__name__.lower()
            metric_name = f"{component_name}.{operation_name}.duration"
            
            with PerformanceTimer(monitor, metric_name):
                result = await method(self, *args, **kwargs)
            
            # Record success
            monitor.collector.increment_counter(f"{component_name}.{operation_name}.success")
            
            return result
        
        @wraps(method)
        def sync_wrapper(self, *args, **kwargs):
            nonlocal monitor, operation_name
            
            if monitor is None and hasattr(self, '_monitor'):
                monitor = self._monitor
            elif monitor is None:
                monitor = get_default_monitor()
            
            if operation_name is None:
                operation_name = method.__name__
            
            component_name = self.__class__.__name__.lower()
            metric_name = f"{component_name}.{operation_name}.duration"
            
            with PerformanceTimer(monitor, metric_name):
                result = method(self, *args, **kwargs)
            
            # Record success
            monitor.collector.increment_counter(f"{component_name}.{operation_name}.success")
            
            return result
        
        if asyncio.iscoroutinefunction(method):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def monitor_errors(monitor: PerformanceMonitor = None):
    """Decorator for monitoring method errors."""
    def decorator(method):
        @wraps(method)
        async def async_wrapper(self, *args, **kwargs):
            nonlocal monitor
            
            if monitor is None and hasattr(self, '_monitor'):
                monitor = self._monitor
            elif monitor is None:
                monitor = get_default_monitor()
            
            component_name = self.__class__.__name__.lower()
            operation_name = method.__name__
            
            try:
                return await method(self, *args, **kwargs)
            except Exception as e:
                # Record error
                error_type = e.__class__.__name__
                monitor.collector.increment_counter(
                    f"{component_name}.{operation_name}.errors",
                    labels={'error_type': error_type}
                )
                raise
        
        @wraps(method)
        def sync_wrapper(self, *args, **kwargs):
            nonlocal monitor
            
            if monitor is None and hasattr(self, '_monitor'):
                monitor = self._monitor
            elif monitor is None:
                monitor = get_default_monitor()
            
            component_name = self.__class__.__name__.lower()
            operation_name = method.__name__
            
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                # Record error
                error_type = e.__class__.__name__
                monitor.collector.increment_counter(
                    f"{component_name}.{operation_name}.errors",
                    labels={'error_type': error_type}
                )
                raise
        
        if asyncio.iscoroutinefunction(method):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
