"""
📊 Cloud Monitoring Manager - Enterprise Observability

Gerenciador enterprise para Google Cloud Monitoring com recursos avançados:
- Metrics collection e custom metrics
- Alerting policies e notification channels
- Dashboards e visualization
- Log-based metrics e SLI/SLO monitoring
- Performance optimization e cost tracking

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

try:
    from google.cloud import monitoring_v3
    from google.cloud.monitoring_v3 import MetricServiceClient, AlertPolicyServiceClient
    from google.auth.credentials import Credentials
except ImportError:
    monitoring_v3 = None
    MetricServiceClient = None
    AlertPolicyServiceClient = None
    Credentials = None

from .config import GCPConfig


class CloudMonitoringManager:
    """Enterprise Google Cloud Monitoring manager."""
    
    def __init__(self, config: GCPConfig, credentials: Optional[Credentials] = None):
        if monitoring_v3 is None:
            raise ImportError("google-cloud-monitoring não instalado. Execute: pip install google-cloud-monitoring")
            
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Monitoring clients
        if credentials:
            self.metric_client = MetricServiceClient(credentials=credentials)
            self.alert_client = AlertPolicyServiceClient(credentials=credentials)
        else:
            self.metric_client = MetricServiceClient()
            self.alert_client = AlertPolicyServiceClient()
    
    async def create_custom_metric(
        self,
        metric_type: str,
        display_name: str,
        description: str,
        metric_kind: str = "GAUGE",
        value_type: str = "DOUBLE"
    ) -> str:
        """Cria métrica customizada."""
        try:
            project_name = f"projects/{self.config.project_id}"
            
            descriptor = monitoring_v3.MetricDescriptor()
            descriptor.type = f"custom.googleapis.com/{metric_type}"
            descriptor.metric_kind = getattr(monitoring_v3.MetricDescriptor.MetricKind, metric_kind)
            descriptor.value_type = getattr(monitoring_v3.MetricDescriptor.ValueType, value_type)
            descriptor.display_name = display_name
            descriptor.description = description
            
            created_descriptor = self.metric_client.create_metric_descriptor(
                name=project_name, metric_descriptor=descriptor
            )
            
            self.logger.info(f"Custom metric created: {metric_type}")
            return created_descriptor.name
            
        except Exception as e:
            self.logger.error(f"Custom metric creation failed: {e}")
            raise
    
    async def write_time_series(
        self,
        metric_type: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Escreve dados de série temporal."""
        try:
            project_name = f"projects/{self.config.project_id}"
            
            # Create time series data
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{metric_type}"
            
            if labels:
                for key, value in labels.items():
                    series.metric.labels[key] = value
            
            # Set resource labels
            series.resource.type = "global"
            
            # Create data point
            point = monitoring_v3.Point()
            point.value.double_value = float(value)
            
            if timestamp:
                point.interval.end_time.seconds = int(timestamp.timestamp())
            else:
                now = datetime.utcnow()
                point.interval.end_time.seconds = int(now.timestamp())
            
            series.points = [point]
            
            self.metric_client.create_time_series(
                name=project_name, time_series=[series]
            )
            
            self.logger.info(f"Time series written: {metric_type}")
            
        except Exception as e:
            self.logger.error(f"Time series write failed: {e}")
            raise
    
    async def create_alert_policy(
        self,
        display_name: str,
        conditions: List[Dict[str, Any]],
        notification_channels: Optional[List[str]] = None
    ) -> str:
        """Cria política de alerta."""
        try:
            project_name = f"projects/{self.config.project_id}"
            
            policy = monitoring_v3.AlertPolicy()
            policy.display_name = display_name
            
            # Add conditions
            for condition_config in conditions:
                condition = monitoring_v3.AlertPolicy.Condition()
                condition.display_name = condition_config.get('display_name', 'Condition')
                
                # Configure condition threshold
                threshold = monitoring_v3.AlertPolicy.Condition.MetricThreshold()
                threshold.filter = condition_config.get('filter', '')
                threshold.comparison = getattr(
                    monitoring_v3.ComparisonType,
                    condition_config.get('comparison', 'COMPARISON_GREATER_THAN')
                )
                threshold.threshold_value.double_value = condition_config.get('threshold', 0.0)
                
                condition.condition_threshold = threshold
                policy.conditions.append(condition)
            
            # Add notification channels
            if notification_channels:
                policy.notification_channels.extend(notification_channels)
            
            created_policy = self.alert_client.create_alert_policy(
                name=project_name, alert_policy=policy
            )
            
            self.logger.info(f"Alert policy created: {display_name}")
            return created_policy.name
            
        except Exception as e:
            self.logger.error(f"Alert policy creation failed: {e}")
            raise
    
    async def get_metrics(
        self,
        metric_filter: str,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Obtém métricas do período especificado."""
        try:
            project_name = f"projects/{self.config.project_id}"
            
            if end_time is None:
                end_time = datetime.utcnow()
            
            # Create time interval
            interval = monitoring_v3.TimeInterval()
            interval.start_time.seconds = int(start_time.timestamp())
            interval.end_time.seconds = int(end_time.timestamp())
            
            # List time series
            results = self.metric_client.list_time_series(
                request={
                    "name": project_name,
                    "filter": metric_filter,
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
                }
            )
            
            metrics = []
            for result in results:
                metric_data = {
                    'metric_type': result.metric.type,
                    'labels': dict(result.metric.labels),
                    'resource': {
                        'type': result.resource.type,
                        'labels': dict(result.resource.labels)
                    },
                    'points': []
                }
                
                for point in result.points:
                    metric_data['points'].append({
                        'timestamp': datetime.fromtimestamp(point.interval.end_time.seconds),
                        'value': point.value.double_value or point.value.int64_value
                    })
                
                metrics.append(metric_data)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Get metrics failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do Cloud Monitoring."""
        try:
            project_name = f"projects/{self.config.project_id}"
            
            # Test by listing metric descriptors
            descriptors = list(self.metric_client.list_metric_descriptors(
                name=project_name
            ))
            
            return {
                'status': 'healthy',
                'service': 'cloud_monitoring',
                'project_id': self.config.project_id,
                'timestamp': datetime.utcnow().isoformat(),
                'metric_descriptors_count': len(descriptors)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'cloud_monitoring',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
