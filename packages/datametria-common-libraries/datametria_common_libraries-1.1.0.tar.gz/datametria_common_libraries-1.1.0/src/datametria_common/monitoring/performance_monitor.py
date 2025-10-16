"""
DATAMETRIA Performance Monitoring Integration

Comprehensive performance monitoring system with metrics collection,
alerting, and integration with existing components.
"""

import time
import asyncio
import psutil
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from collections import defaultdict, deque


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    name: str
    level: AlertLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metric_name: str = ""
    threshold: float = 0.0


class PerformanceCollector:
    """Collects system and application performance metrics."""
    
    def __init__(self):
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._timers: Dict[str, List[float]] = defaultdict(list)
        
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        self._counters[name] += value
        self._add_metric(name, self._counters[name], MetricType.COUNTER, labels)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value."""
        self._gauges[name] = value
        self._add_metric(name, value, MetricType.GAUGE, labels)
    
    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Record a timer metric."""
        self._timers[name].append(duration)
        if len(self._timers[name]) > 100:  # Keep last 100 measurements
            self._timers[name] = self._timers[name][-100:]
        
        avg_duration = sum(self._timers[name]) / len(self._timers[name])
        self._add_metric(name, avg_duration, MetricType.TIMER, labels)
    
    def _add_metric(self, name: str, value: float, metric_type: MetricType, labels: Dict[str, str] = None):
        """Add metric to collection."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {}
        )
        self._metrics[name].append(metric)
    
    def get_metrics(self, name: str = None) -> List[Metric]:
        """Get collected metrics."""
        if name:
            return list(self._metrics.get(name, []))
        
        all_metrics = []
        for metrics in self._metrics.values():
            all_metrics.extend(metrics)
        return all_metrics
    
    def collect_system_metrics(self):
        """Collect system performance metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.set_gauge("system.cpu.usage_percent", cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.set_gauge("system.memory.usage_percent", memory.percent)
        self.set_gauge("system.memory.available_mb", memory.available / 1024 / 1024)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.set_gauge("system.disk.usage_percent", (disk.used / disk.total) * 100)
        
        # Network I/O
        network = psutil.net_io_counters()
        self.increment_counter("system.network.bytes_sent", network.bytes_sent)
        self.increment_counter("system.network.bytes_recv", network.bytes_recv)


class AlertManager:
    """Manages performance alerts and thresholds."""
    
    def __init__(self):
        self._thresholds: Dict[str, Dict[AlertLevel, float]] = {}
        self._alerts: deque = deque(maxlen=1000)
        self._alert_callbacks: List[Callable[[Alert], None]] = []
    
    def set_threshold(self, metric_name: str, level: AlertLevel, threshold: float):
        """Set alert threshold for a metric."""
        if metric_name not in self._thresholds:
            self._thresholds[metric_name] = {}
        self._thresholds[metric_name][level] = threshold
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback for alert notifications."""
        self._alert_callbacks.append(callback)
    
    def check_metric(self, metric: Metric):
        """Check metric against thresholds and trigger alerts."""
        if metric.name not in self._thresholds:
            return
        
        thresholds = self._thresholds[metric.name]
        
        for level, threshold in thresholds.items():
            if self._should_alert(metric.value, threshold, level):
                alert = Alert(
                    name=f"{metric.name}_{level.value}",
                    level=level,
                    message=f"{metric.name} is {metric.value}, threshold: {threshold}",
                    metric_name=metric.name,
                    threshold=threshold
                )
                self._trigger_alert(alert)
    
    def _should_alert(self, value: float, threshold: float, level: AlertLevel) -> bool:
        """Determine if alert should be triggered."""
        if level in [AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]:
            return value >= threshold
        return False
    
    def _trigger_alert(self, alert: Alert):
        """Trigger alert and notify callbacks."""
        self._alerts.append(alert)
        
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Alert callback error: {e}")
    
    def get_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """Get triggered alerts."""
        if level:
            return [alert for alert in self._alerts if alert.level == level]
        return list(self._alerts)


class PerformanceMonitor:
    """Main performance monitoring system."""
    
    def __init__(self, collection_interval: int = 60):
        self.collector = PerformanceCollector()
        self.alert_manager = AlertManager()
        self.collection_interval = collection_interval
        self._running = False
        self._monitor_thread = None
        
        # Set default thresholds
        self._set_default_thresholds()
    
    def _set_default_thresholds(self):
        """Set default performance thresholds."""
        # CPU thresholds
        self.alert_manager.set_threshold("system.cpu.usage_percent", AlertLevel.WARNING, 80.0)
        self.alert_manager.set_threshold("system.cpu.usage_percent", AlertLevel.CRITICAL, 95.0)
        
        # Memory thresholds
        self.alert_manager.set_threshold("system.memory.usage_percent", AlertLevel.WARNING, 85.0)
        self.alert_manager.set_threshold("system.memory.usage_percent", AlertLevel.CRITICAL, 95.0)
        
        # Disk thresholds
        self.alert_manager.set_threshold("system.disk.usage_percent", AlertLevel.WARNING, 80.0)
        self.alert_manager.set_threshold("system.disk.usage_percent", AlertLevel.CRITICAL, 90.0)
    
    def start_monitoring(self):
        """Start performance monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # Collect system metrics
                self.collector.collect_system_metrics()
                
                # Check all metrics for alerts
                for metric in self.collector.get_metrics():
                    self.alert_manager.check_metric(metric)
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for monitoring UI."""
        recent_metrics = {}
        
        # Get latest metrics
        for name in ["system.cpu.usage_percent", "system.memory.usage_percent", "system.disk.usage_percent"]:
            metrics = self.collector.get_metrics(name)
            if metrics:
                recent_metrics[name] = metrics[-1].value
        
        # Get recent alerts
        recent_alerts = self.alert_manager.get_alerts()[-10:]  # Last 10 alerts
        
        return {
            "metrics": recent_metrics,
            "alerts": [
                {
                    "name": alert.name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in recent_alerts
            ],
            "status": "healthy" if not any(a.level == AlertLevel.CRITICAL for a in recent_alerts) else "critical"
        }


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: PerformanceMonitor, metric_name: str, labels: Dict[str, str] = None):
        self.monitor = monitor
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.collector.record_timer(self.metric_name, duration, self.labels)


def performance_timer(metric_name: str, monitor: PerformanceMonitor = None):
    """Decorator for timing function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal monitor
            if monitor is None:
                monitor = _get_default_monitor()
            
            with PerformanceTimer(monitor, metric_name):
                return func(*args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            nonlocal monitor
            if monitor is None:
                monitor = _get_default_monitor()
            
            with PerformanceTimer(monitor, metric_name):
                return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


# Global monitor instance
_default_monitor = None

def get_default_monitor() -> PerformanceMonitor:
    """Get or create default monitor instance."""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = PerformanceMonitor()
        _default_monitor.start_monitoring()
    return _default_monitor

def _get_default_monitor() -> PerformanceMonitor:
    """Internal function to get default monitor."""
    return get_default_monitor()
