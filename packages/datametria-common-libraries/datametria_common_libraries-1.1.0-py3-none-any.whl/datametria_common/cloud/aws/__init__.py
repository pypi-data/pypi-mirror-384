"""
☁️ AWS Services - DATAMETRIA Common Libraries

Integração completa com Amazon Web Services seguindo padrões DATAMETRIA.

Features:
    - S3: Object storage com lifecycle management
    - RDS: Multi-AZ databases com read replicas
    - Lambda: Serverless functions com layers
    - EventBridge: Event-driven architecture
    - Step Functions: Workflow orchestration
    - Scheduler: Cron-based task scheduling
    - CloudWatch: Monitoring e logging
    - Secrets Manager: Credential management

Integration:
    - Configuration: BaseConfig para configurações centralizadas
    - Security: SecurityManager para criptografia
    - Logging: Logging enterprise com structlog
    - Cache: CacheManager para otimizações
    - Monitoring: Métricas integradas

Author: DATAMETRIA Enterprise Team
Version: 1.0.0
"""

from .manager import AWSManager
from .config import AWSConfig
from .s3 import S3Manager
from .rds import RDSManager
from .lambda_manager import LambdaManager
from .eventbridge import EventBridgeManager
from .stepfunctions import StepFunctionsManager
from .scheduler import SchedulerManager
from .cloudwatch import CloudWatchManager
from .secrets import SecretsManager
from .models import *

__all__ = [
    # Core
    "AWSManager",
    "AWSConfig",
    
    # Service Managers
    "S3Manager",
    "RDSManager", 
    "LambdaManager",
    "EventBridgeManager",
    "StepFunctionsManager",
    "SchedulerManager",
    "CloudWatchManager",
    "SecretsManager",
    
    # Models
    "AWSResult",
    "S3UploadResult",
    "EventBridgeEvent",
    "StateMachineConfig",
    "ScheduleConfig"
]
