"""
Workspace Performance Integration - Performance Monitor for Google Workspace APIs

Provides comprehensive performance monitoring with:
- Operation timing and latency tracking
- Success/error rate metrics
- Rate limit monitoring
- Cache performance metrics
- Alert management
"""

from typing import Optional, Dict, Any
import time
from ...monitoring.performance_monitor import PerformanceMonitor, PerformanceTimer, AlertLevel
from .config import WorkspaceConfig


class WorkspacePerformanceMonitor:
    """Performance monitor for Workspace APIs"""
    
    _instance: Optional['WorkspacePerformanceMonitor'] = None
    
    def __init__(self, config: WorkspaceConfig):
        self.config = config
        self.monitor = PerformanceMonitor(collection_interval=60)
        self._setup_thresholds()
        self.monitor.start_monitoring()
    
    @classmethod
    def get_instance(cls, config: WorkspaceConfig) -> 'WorkspacePerformanceMonitor':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def _setup_thresholds(self):
        """Setup Workspace-specific thresholds"""
        # API latency thresholds (ms)
        for api in ['gmail', 'drive', 'calendar', 'chat', 'meet', 'tasks', 'vault']:
            self.monitor.alert_manager.set_threshold(
                f"workspace.{api}.latency_ms",
                AlertLevel.WARNING,
                1000.0
            )
            self.monitor.alert_manager.set_threshold(
                f"workspace.{api}.latency_ms",
                AlertLevel.CRITICAL,
                3000.0
            )
            
            # Error rate thresholds (%)
            self.monitor.alert_manager.set_threshold(
                f"workspace.{api}.error_rate",
                AlertLevel.WARNING,
                5.0
            )
            self.monitor.alert_manager.set_threshold(
                f"workspace.{api}.error_rate",
                AlertLevel.CRITICAL,
                10.0
            )
        
        # Cache hit rate threshold
        self.monitor.alert_manager.set_threshold(
            "workspace.cache.hit_rate",
            AlertLevel.WARNING,
            60.0  # Alert if below 60%
        )
    
    def record_operation(
        self,
        api: str,
        operation: str,
        duration_ms: float,
        success: bool = True,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record API operation metrics"""
        labels = labels or {}
        labels.update({'api': api, 'operation': operation})
        
        # Record latency
        metric_name = f"workspace.{api}.{operation}.latency_ms"
        self.monitor.collector.record_timer(metric_name, duration_ms, labels)
        
        # Record success/error
        if success:
            self.monitor.collector.increment_counter(
                f"workspace.{api}.{operation}.success",
                labels=labels
            )
        else:
            self.monitor.collector.increment_counter(
                f"workspace.{api}.{operation}.error",
                labels=labels
            )
        
        # Update aggregated metrics
        self._update_aggregated_metrics(api)
    
    def _update_aggregated_metrics(self, api: str):
        """Update aggregated API metrics"""
        # Calculate error rate
        success_metrics = self.monitor.collector.get_metrics(f"workspace.{api}.*.success")
        error_metrics = self.monitor.collector.get_metrics(f"workspace.{api}.*.error")
        
        total = len(success_metrics) + len(error_metrics)
        if total > 0:
            error_rate = (len(error_metrics) / total) * 100
            self.monitor.collector.set_gauge(f"workspace.{api}.error_rate", error_rate)
    
    def record_rate_limit(self, api: str, remaining: int, exceeded: bool = False):
        """Record rate limit metrics"""
        self.monitor.collector.set_gauge(
            f"workspace.{api}.rate_limit.remaining",
            remaining
        )
        
        if exceeded:
            self.monitor.collector.increment_counter(
                f"workspace.{api}.rate_limit.exceeded"
            )
    
    def record_cache_metrics(self, hits: int, misses: int, hit_rate: float):
        """Record cache performance metrics"""
        self.monitor.collector.set_gauge("workspace.cache.hits", hits)
        self.monitor.collector.set_gauge("workspace.cache.misses", misses)
        self.monitor.collector.set_gauge("workspace.cache.hit_rate", hit_rate)
    
    def get_api_metrics(self, api: str) -> Dict[str, Any]:
        """Get metrics for specific API"""
        metrics = {}
        
        # Get latency metrics
        latency_metrics = self.monitor.collector.get_metrics(f"workspace.{api}.*.latency_ms")
        if latency_metrics:
            latencies = [m.value for m in latency_metrics[-100:]]  # Last 100
            metrics['avg_latency_ms'] = sum(latencies) / len(latencies)
            metrics['max_latency_ms'] = max(latencies)
            metrics['min_latency_ms'] = min(latencies)
        
        # Get error rate
        error_rate_metrics = self.monitor.collector.get_metrics(f"workspace.{api}.error_rate")
        if error_rate_metrics:
            metrics['error_rate'] = error_rate_metrics[-1].value
        
        # Get rate limit status
        rate_limit_metrics = self.monitor.collector.get_metrics(f"workspace.{api}.rate_limit.remaining")
        if rate_limit_metrics:
            metrics['rate_limit_remaining'] = rate_limit_metrics[-1].value
        
        return metrics
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        dashboard = self.monitor.get_dashboard_data()
        
        # Add Workspace-specific metrics
        workspace_metrics = {}
        for api in ['gmail', 'drive', 'calendar', 'chat', 'meet', 'tasks', 'vault']:
            api_metrics = self.get_api_metrics(api)
            if api_metrics:
                workspace_metrics[api] = api_metrics
        
        dashboard['workspace_apis'] = workspace_metrics
        
        # Add cache metrics
        cache_metrics = {}
        for metric_name in ['workspace.cache.hits', 'workspace.cache.misses', 'workspace.cache.hit_rate']:
            metrics = self.monitor.collector.get_metrics(metric_name)
            if metrics:
                cache_metrics[metric_name.split('.')[-1]] = metrics[-1].value
        
        dashboard['cache'] = cache_metrics
        
        return dashboard
    
    def timer(self, api: str, operation: str) -> PerformanceTimer:
        """Get performance timer for operation"""
        metric_name = f"workspace.{api}.{operation}.latency_ms"
        return PerformanceTimer(self.monitor, metric_name, {'api': api, 'operation': operation})
    
    def stop(self):
        """Stop monitoring"""
        self.monitor.stop_monitoring()
