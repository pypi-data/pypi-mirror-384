"""
📊 CloudWatch Manager - DATAMETRIA AWS Services

Gerenciador CloudWatch integrado aos componentes DATAMETRIA.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import boto3
import structlog
from botocore.exceptions import ClientError

from .config import AWSConfig
from .models import MetricData, CloudWatchResult

logger = structlog.get_logger(__name__)


class CloudWatchManager:
    """
    Gerenciador CloudWatch DATAMETRIA.
    
    Integra monitoring e logging com componentes existentes.
    """
    
    def __init__(self, session: boto3.Session, config: AWSConfig):
        """
        Inicializa CloudWatchManager.
        
        Args:
            session: Sessão boto3
            config: Configuração AWS
        """
        self.session = session
        self.config = config
        self.client = session.client('cloudwatch')
        self.logs_client = session.client('logs')
        
        # Namespace padrão para métricas DATAMETRIA
        self.namespace = "DATAMETRIA/CommonLibraries"
        
        logger.info(
            "CloudWatchManager initialized",
            region=config.region,
            namespace=self.namespace
        )
    
    async def put_metric_data(self, metrics: List[MetricData]) -> CloudWatchResult:
        """
        Enviar métricas para CloudWatch.
        
        Args:
            metrics: Lista de métricas
            
        Returns:
            CloudWatchResult: Resultado da operação
        """
        try:
            # Preparar dados das métricas
            metric_data = []
            for metric in metrics:
                data = {
                    'MetricName': metric.metric_name,
                    'Value': metric.value,
                    'Unit': metric.unit
                }
                
                if metric.dimensions:
                    data['Dimensions'] = [
                        {'Name': k, 'Value': v} 
                        for k, v in metric.dimensions.items()
                    ]
                
                if metric.timestamp:
                    data['Timestamp'] = metric.timestamp
                else:
                    data['Timestamp'] = datetime.now()
                
                metric_data.append(data)
            
            # Enviar métricas (máximo 20 por vez)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                
                self.client.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
            
            logger.info(
                "CloudWatch metrics sent",
                namespace=self.namespace,
                metrics_count=len(metrics)
            )
            
            return CloudWatchResult(
                success=True,
                operation="put_metric_data",
                metadata={
                    'namespace': self.namespace,
                    'metrics_count': len(metrics)
                }
            )
            
        except ClientError as e:
            logger.error(
                "CloudWatch put_metric_data failed",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return CloudWatchResult(
                success=False,
                operation="put_metric_data",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    def create_log_group(self, log_group_name: str, retention_days: int = 30) -> bool:
        """
        Criar log group.
        
        Args:
            log_group_name: Nome do log group
            retention_days: Dias de retenção
            
        Returns:
            bool: True se sucesso
        """
        try:
            # Criar log group
            self.logs_client.create_log_group(logGroupName=log_group_name)
            
            # Configurar retenção
            self.logs_client.put_retention_policy(
                logGroupName=log_group_name,
                retentionInDays=retention_days
            )
            
            # Adicionar tags
            if self.config.default_tags:
                tags = {k: v for k, v in self.config.default_tags.items()}
                self.logs_client.tag_log_group(
                    logGroupName=log_group_name,
                    tags=tags
                )
            
            logger.info(
                "CloudWatch log group created",
                log_group=log_group_name,
                retention_days=retention_days
            )
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                logger.info("Log group already exists", log_group=log_group_name)
                return True
            else:
                logger.error(
                    "Failed to create log group",
                    log_group=log_group_name,
                    error=str(e)
                )
                return False
    
    def put_log_events(
        self, 
        log_group_name: str, 
        log_stream_name: str, 
        events: List[Dict[str, Any]]
    ) -> bool:
        """
        Enviar eventos de log.
        
        Args:
            log_group_name: Nome do log group
            log_stream_name: Nome do log stream
            events: Lista de eventos
            
        Returns:
            bool: True se sucesso
        """
        try:
            # Criar log stream se não existir
            try:
                self.logs_client.create_log_stream(
                    logGroupName=log_group_name,
                    logStreamName=log_stream_name
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
            
            # Preparar eventos
            log_events = []
            for event in events:
                log_event = {
                    'timestamp': int(event.get('timestamp', time.time() * 1000)),
                    'message': json.dumps(event) if isinstance(event, dict) else str(event)
                }
                log_events.append(log_event)
            
            # Ordenar por timestamp
            log_events.sort(key=lambda x: x['timestamp'])
            
            # Obter sequence token se necessário
            sequence_token = None
            try:
                response = self.logs_client.describe_log_streams(
                    logGroupName=log_group_name,
                    logStreamNamePrefix=log_stream_name
                )
                
                for stream in response.get('logStreams', []):
                    if stream['logStreamName'] == log_stream_name:
                        sequence_token = stream.get('uploadSequenceToken')
                        break
            except Exception:
                pass
            
            # Enviar eventos
            params = {
                'logGroupName': log_group_name,
                'logStreamName': log_stream_name,
                'logEvents': log_events
            }
            
            if sequence_token:
                params['sequenceToken'] = sequence_token
            
            self.logs_client.put_log_events(**params)
            
            logger.info(
                "CloudWatch log events sent",
                log_group=log_group_name,
                log_stream=log_stream_name,
                events_count=len(events)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to put log events",
                log_group=log_group_name,
                log_stream=log_stream_name,
                error=str(e)
            )
            return False
    
    def create_alarm(
        self,
        alarm_name: str,
        metric_name: str,
        threshold: float,
        comparison_operator: str = 'GreaterThanThreshold',
        evaluation_periods: int = 2,
        period: int = 300,
        statistic: str = 'Average',
        alarm_actions: Optional[List[str]] = None
    ) -> bool:
        """
        Criar alarme CloudWatch.
        
        Args:
            alarm_name: Nome do alarme
            metric_name: Nome da métrica
            threshold: Valor limite
            comparison_operator: Operador de comparação
            evaluation_periods: Períodos de avaliação
            period: Período em segundos
            statistic: Estatística
            alarm_actions: Ações do alarme
            
        Returns:
            bool: True se sucesso
        """
        try:
            params = {
                'AlarmName': alarm_name,
                'ComparisonOperator': comparison_operator,
                'EvaluationPeriods': evaluation_periods,
                'MetricName': metric_name,
                'Namespace': self.namespace,
                'Period': period,
                'Statistic': statistic,
                'Threshold': threshold,
                'ActionsEnabled': True,
                'AlarmDescription': f'DATAMETRIA alarm for {metric_name}',
                'Unit': 'Count'
            }
            
            if alarm_actions:
                params['AlarmActions'] = alarm_actions
            
            self.client.put_metric_alarm(**params)
            
            logger.info(
                "CloudWatch alarm created",
                alarm_name=alarm_name,
                metric_name=metric_name,
                threshold=threshold
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to create alarm",
                alarm_name=alarm_name,
                error=str(e)
            )
            return False
    
    def get_metric_statistics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics: List[str] = None,
        dimensions: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obter estatísticas de métrica.
        
        Args:
            metric_name: Nome da métrica
            start_time: Tempo inicial
            end_time: Tempo final
            period: Período em segundos
            statistics: Lista de estatísticas
            dimensions: Dimensões da métrica
            
        Returns:
            List: Dados da métrica
        """
        try:
            params = {
                'Namespace': self.namespace,
                'MetricName': metric_name,
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'Statistics': statistics or ['Average']
            }
            
            if dimensions:
                params['Dimensions'] = [
                    {'Name': k, 'Value': v} 
                    for k, v in dimensions.items()
                ]
            
            response = self.client.get_metric_statistics(**params)
            datapoints = response.get('Datapoints', [])
            
            # Ordenar por timestamp
            datapoints.sort(key=lambda x: x['Timestamp'])
            
            logger.info(
                "CloudWatch metric statistics retrieved",
                metric_name=metric_name,
                datapoints_count=len(datapoints)
            )
            
            return datapoints
            
        except Exception as e:
            logger.error(
                "Failed to get metric statistics",
                metric_name=metric_name,
                error=str(e)
            )
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do CloudWatch."""
        try:
            # Testar listagem de métricas
            self.client.list_metrics(Namespace=self.namespace, MaxRecords=1)
            
            return {
                'available': True,
                'namespace': self.namespace
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do CloudWatch."""
        try:
            # Listar métricas do namespace
            response = self.client.list_metrics(Namespace=self.namespace)
            metrics_count = len(response.get('Metrics', []))
            
            return {
                'namespace': self.namespace,
                'metrics_count': metrics_count
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
