"""
🗄️ RDS Manager - DATAMETRIA AWS Services

Gerenciador RDS integrado aos componentes DATAMETRIA.
"""

from typing import Dict, Any, List, Optional
import boto3
import structlog
from botocore.exceptions import ClientError

from .config import AWSConfig
from .models import RDSResult

logger = structlog.get_logger(__name__)


class RDSManager:
    """
    Gerenciador RDS DATAMETRIA.
    
    Integra database management com logging e monitoramento.
    """
    
    def __init__(self, session: boto3.Session, config: AWSConfig):
        """
        Inicializa RDSManager.
        
        Args:
            session: Sessão boto3
            config: Configuração AWS
        """
        self.session = session
        self.config = config
        self.client = session.client('rds')
        
        logger.info(
            "RDSManager initialized",
            region=config.region
        )
    
    def describe_instances(self, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar instâncias RDS.
        
        Args:
            instance_id: ID específico da instância
            
        Returns:
            List: Lista de instâncias
        """
        try:
            params = {}
            if instance_id:
                params['DBInstanceIdentifier'] = instance_id
            
            response = self.client.describe_db_instances(**params)
            instances = response.get('DBInstances', [])
            
            logger.info(
                "RDS instances described",
                count=len(instances),
                instance_id=instance_id
            )
            
            return instances
            
        except Exception as e:
            logger.error(
                "Failed to describe RDS instances",
                instance_id=instance_id,
                error=str(e)
            )
            return []
    
    def create_snapshot(self, instance_id: str, snapshot_id: str) -> RDSResult:
        """
        Criar snapshot de instância RDS.
        
        Args:
            instance_id: ID da instância
            snapshot_id: ID do snapshot
            
        Returns:
            RDSResult: Resultado da operação
        """
        try:
            response = self.client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_id,
                DBInstanceIdentifier=instance_id,
                Tags=[
                    {'Key': k, 'Value': v} 
                    for k, v in self.config.default_tags.items()
                ]
            )
            
            logger.info(
                "RDS snapshot created",
                instance_id=instance_id,
                snapshot_id=snapshot_id,
                status=response['DBSnapshot']['Status']
            )
            
            return RDSResult(
                success=True,
                operation="create_snapshot",
                instance_id=instance_id,
                metadata={
                    'snapshot_id': snapshot_id,
                    'status': response['DBSnapshot']['Status'],
                    'creation_time': response['DBSnapshot']['SnapshotCreateTime']
                }
            )
            
        except ClientError as e:
            logger.error(
                "RDS create_snapshot failed",
                instance_id=instance_id,
                snapshot_id=snapshot_id,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return RDSResult(
                success=False,
                operation="create_snapshot",
                instance_id=instance_id,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    def get_performance_metrics(
        self, 
        instance_id: str, 
        start_time, 
        end_time, 
        metrics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Obter métricas de performance RDS.
        
        Args:
            instance_id: ID da instância
            start_time: Tempo inicial
            end_time: Tempo final
            metrics: Lista de métricas
            
        Returns:
            List: Dados das métricas
        """
        try:
            cloudwatch = self.session.client('cloudwatch')
            
            all_metrics = []
            
            for metric_name in metrics:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName=metric_name,
                    Dimensions=[
                        {
                            'Name': 'DBInstanceIdentifier',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5 minutos
                    Statistics=['Average', 'Maximum']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    # Ordenar por timestamp
                    datapoints.sort(key=lambda x: x['Timestamp'])
                    
                    all_metrics.append({
                        'MetricName': metric_name,
                        'Datapoints': datapoints,
                        'Average': sum(d.get('Average', 0) for d in datapoints) / len(datapoints),
                        'Maximum': max(d.get('Maximum', 0) for d in datapoints)
                    })
            
            logger.info(
                "RDS performance metrics retrieved",
                instance_id=instance_id,
                metrics_count=len(all_metrics)
            )
            
            return all_metrics
            
        except Exception as e:
            logger.error(
                "Failed to get RDS performance metrics",
                instance_id=instance_id,
                error=str(e)
            )
            return []
    
    def download_log_file(self, instance_id: str, log_file_name: str) -> Optional[str]:
        """
        Download de arquivo de log RDS.
        
        Args:
            instance_id: ID da instância
            log_file_name: Nome do arquivo de log
            
        Returns:
            str: Conteúdo do log ou None
        """
        try:
            response = self.client.download_db_log_file_portion(
                DBInstanceIdentifier=instance_id,
                LogFileName=log_file_name
            )
            
            log_data = response.get('LogFileData', '')
            
            logger.info(
                "RDS log file downloaded",
                instance_id=instance_id,
                log_file=log_file_name,
                size=len(log_data)
            )
            
            return log_data
            
        except Exception as e:
            logger.error(
                "Failed to download RDS log file",
                instance_id=instance_id,
                log_file=log_file_name,
                error=str(e)
            )
            return None
    
    def list_snapshots(self, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar snapshots RDS.
        
        Args:
            instance_id: ID da instância (opcional)
            
        Returns:
            List: Lista de snapshots
        """
        try:
            params = {'SnapshotType': 'manual'}
            if instance_id:
                params['DBInstanceIdentifier'] = instance_id
            
            response = self.client.describe_db_snapshots(**params)
            snapshots = response.get('DBSnapshots', [])
            
            logger.info(
                "RDS snapshots listed",
                count=len(snapshots),
                instance_id=instance_id
            )
            
            return snapshots
            
        except Exception as e:
            logger.error(
                "Failed to list RDS snapshots",
                instance_id=instance_id,
                error=str(e)
            )
            return []
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Deletar snapshot RDS.
        
        Args:
            snapshot_id: ID do snapshot
            
        Returns:
            bool: True se sucesso
        """
        try:
            self.client.delete_db_snapshot(DBSnapshotIdentifier=snapshot_id)
            
            logger.info(
                "RDS snapshot deleted",
                snapshot_id=snapshot_id
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete RDS snapshot",
                snapshot_id=snapshot_id,
                error=str(e)
            )
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do RDS."""
        try:
            # Testar listagem de instâncias
            self.client.describe_db_instances(MaxRecords=1)
            
            return {
                'available': True
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do RDS."""
        try:
            instances = self.describe_instances()
            snapshots = self.list_snapshots()
            
            return {
                'instances_count': len(instances),
                'snapshots_count': len(snapshots)
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
