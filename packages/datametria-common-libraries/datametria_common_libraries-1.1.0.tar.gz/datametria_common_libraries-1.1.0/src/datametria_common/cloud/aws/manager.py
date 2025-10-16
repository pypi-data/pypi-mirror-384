"""
🏗️ AWS Manager - DATAMETRIA AWS Services

Gerenciador principal de serviços AWS integrado aos componentes DATAMETRIA.
"""

import boto3
from typing import Optional, Dict, Any
import time

from datametria_common.core import BaseConfig
from datametria_common.core.security import SecurityManager
from datametria_common.security.logging import EnterpriseLogger
from .config import AWSConfig
from .s3 import S3Manager
from .eventbridge import EventBridgeManager
from .stepfunctions import StepFunctionsManager
from .scheduler import SchedulerManager
from .cloudwatch import CloudWatchManager
from .secrets import SecretsManager


class AWSManager:
    """
    Gerenciador principal de serviços AWS DATAMETRIA.
    
    Integra todos os serviços AWS com componentes existentes DATAMETRIA.
    """
    
    def __init__(self, config: Optional[AWSConfig] = None, logger: Optional[EnterpriseLogger] = None):
        """
        Inicializa AWSManager.
        
        Args:
            config: Configuração AWS (usa padrão se None)
            logger: EnterpriseLogger para logs estruturados com compliance LGPD/GDPR
        """
        self.config = config or AWSConfig.from_env()
        self.security_manager = SecurityManager()
        self.logger = logger or EnterpriseLogger(
            service_name="aws-services",
            environment=getattr(self.config, 'environment', 'production'),
            compliance_mode=True
        )
        
        # Criar sessão boto3
        self.session = self._create_session()
        
        # Inicializar managers de serviços
        self.s3 = S3Manager(self.session, self.config)
        self.eventbridge = EventBridgeManager(self.session, self.config)
        self.stepfunctions = StepFunctionsManager(self.session, self.config)
        self.scheduler = SchedulerManager(self.session, self.config)
        self.cloudwatch = CloudWatchManager(self.session, self.config)
        self.secrets = SecretsManager(self.session, self.config, self.security_manager)
        
        self.logger.info(
            "AWSManager initialized",
            extra={
                "region": self.config.region,
                "use_iam_role": self.config.use_iam_role,
                "services": ["s3", "eventbridge", "stepfunctions", "scheduler", "cloudwatch", "secrets"],
                "compliance_tags": ["AUDIT"]
            }
        )
    
    def _create_session(self) -> boto3.Session:
        """Criar sessão boto3 com configuração adequada."""
        start_time = time.time()
        try:
            boto3_config = self.config.get_boto3_config()
            
            if self.config.use_iam_role:
                # Usar IAM role
                session = boto3.Session(region_name=self.config.region)
            else:
                # Usar access keys
                session = boto3.Session(**boto3_config)
            
            # Testar conexão
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.info(
                "AWS session created successfully",
                extra={
                    "account": identity.get('Account'),
                    "user_id": "***MASKED***",
                    "execution_time_ms": round(execution_time, 2),
                    "compliance_tags": ["LGPD", "GDPR", "AUDIT"]
                }
            )
            
            return session
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to create AWS session",
                extra={
                    "error": str(e),
                    "execution_time_ms": round(execution_time, 2),
                    "compliance_tags": ["AUDIT"]
                }
            )
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """Obter informações da conta AWS."""
        start_time = time.time()
        try:
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.info(
                "Account info retrieved",
                extra={
                    "account_id": identity.get('Account'),
                    "execution_time_ms": round(execution_time, 2),
                    "compliance_tags": ["AUDIT"]
                }
            )
            
            return {
                'account_id': identity.get('Account'),
                'user_id': identity.get('UserId'),
                'arn': identity.get('Arn'),
                'region': self.config.region
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to get account info",
                extra={
                    "error": str(e),
                    "execution_time_ms": round(execution_time, 2),
                    "compliance_tags": ["AUDIT"]
                }
            )
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde dos serviços AWS."""
        health_status = {
            'overall': True,
            'services': {},
            'timestamp': structlog.get_logger().info.__globals__.get('time', lambda: 0)()
        }
        
        # Verificar cada serviço
        services = {
            's3': self.s3,
            'eventbridge': self.eventbridge,
            'stepfunctions': self.stepfunctions,
            'scheduler': self.scheduler,
            'cloudwatch': self.cloudwatch,
            'secrets': self.secrets
        }
        
        for service_name, service_manager in services.items():
            try:
                if hasattr(service_manager, 'health_check'):
                    service_health = service_manager.health_check()
                else:
                    # Health check básico
                    service_health = {'available': True}
                
                health_status['services'][service_name] = service_health
                
            except Exception as e:
                self.logger.warning(
                    f"Health check failed for {service_name}",
                    extra={"error": str(e), "compliance_tags": ["AUDIT"]}
                )
                health_status['services'][service_name] = {
                    'available': False,
                    'error': str(e)
                }
                health_status['overall'] = False
        
        return health_status
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas consolidadas de todos os serviços."""
        metrics = {
            'aws_manager': {
                'region': self.config.region,
                'services_count': 6,
                'config_valid': True
            }
        }
        
        # Coletar métricas de cada serviço
        services = {
            's3': self.s3,
            'eventbridge': self.eventbridge,
            'stepfunctions': self.stepfunctions,
            'scheduler': self.scheduler,
            'cloudwatch': self.cloudwatch,
            'secrets': self.secrets
        }
        
        for service_name, service_manager in services.items():
            try:
                if hasattr(service_manager, 'get_metrics'):
                    service_metrics = service_manager.get_metrics()
                    metrics[service_name] = service_metrics
                    
            except Exception as e:
                self.logger.warning(
                    f"Failed to get metrics for {service_name}",
                    extra={"error": str(e), "compliance_tags": ["AUDIT"]}
                )
                metrics[service_name] = {'error': str(e)}
        
        return metrics
    
    def update_config(self, new_config: AWSConfig) -> None:
        """Atualizar configuração e reinicializar serviços."""
        self.logger.info(
            "Updating AWS configuration",
            extra={"compliance_tags": ["AUDIT"]}
        )
        
        self.config = new_config
        
        # Recriar sessão
        self.session = self._create_session()
        
        # Reinicializar managers
        self.s3 = S3Manager(self.session, self.config)
        self.eventbridge = EventBridgeManager(self.session, self.config)
        self.stepfunctions = StepFunctionsManager(self.session, self.config)
        self.scheduler = SchedulerManager(self.session, self.config)
        self.cloudwatch = CloudWatchManager(self.session, self.config)
        self.secrets = SecretsManager(self.session, self.config, self.security_manager)
        
        self.logger.info(
            "AWS configuration updated successfully",
            extra={"compliance_tags": ["AUDIT"]}
        )
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Cleanup se necessário
        self.logger.info(
            "AWSManager context closed",
            extra={"compliance_tags": ["AUDIT"]}
        )
        return False
