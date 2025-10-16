"""
⚙️ AWS Configuration - DATAMETRIA AWS Services

Configuração centralizada para serviços AWS integrada ao BaseConfig.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import structlog

from datametria_common.core import BaseConfig

logger = structlog.get_logger(__name__)


@dataclass
class AWSConfig(BaseConfig):
    """Configuração principal para serviços AWS."""
    
    # Authentication
    region: str = "us-east-1"
    use_iam_role: bool = True
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    
    # S3 Configuration
    s3_default_bucket: str = "datametria-storage"
    s3_kms_key_id: Optional[str] = None
    s3_storage_class: str = "STANDARD"
    
    # EventBridge Configuration
    eventbridge_default_bus: str = "default"
    eventbridge_enable_replay: bool = True
    
    # Step Functions Configuration
    stepfunctions_log_group: str = "/aws/stepfunctions/datametria"
    stepfunctions_enable_tracing: bool = True
    
    # Scheduler Configuration
    scheduler_default_timezone: str = "UTC"
    scheduler_default_role: Optional[str] = None
    
    # Global Settings
    enable_cost_optimization: bool = True
    enable_security_monitoring: bool = True
    
    # Default Tags
    default_tags: Dict[str, str] = field(default_factory=lambda: {
        "Project": "DATAMETRIA",
        "Environment": "production",
        "ManagedBy": "datametria-common-libraries"
    })
    
    def __post_init__(self):
        """Validação e configuração pós-inicialização."""
        super().__post_init__()
        
        # Validar configurações obrigatórias
        if not self.use_iam_role and (not self.access_key or not self.secret_key):
            raise ValueError("Access key and secret key required when not using IAM role")
        
        logger.info(
            "AWS configuration initialized",
            region=self.region,
            use_iam_role=self.use_iam_role,
            s3_bucket=self.s3_default_bucket
        )
    
    @classmethod
    def from_env(cls) -> "AWSConfig":
        """Criar configuração a partir de variáveis de ambiente."""
        import os
        
        return cls(
            region=os.getenv("AWS_REGION", "us-east-1"),
            use_iam_role=os.getenv("AWS_USE_IAM_ROLE", "true").lower() == "true",
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            s3_default_bucket=os.getenv("AWS_S3_DEFAULT_BUCKET", "datametria-storage"),
            s3_kms_key_id=os.getenv("AWS_S3_KMS_KEY_ID"),
            eventbridge_default_bus=os.getenv("AWS_EVENTBRIDGE_DEFAULT_BUS", "default"),
            stepfunctions_log_group=os.getenv("AWS_STEPFUNCTIONS_LOG_GROUP", "/aws/stepfunctions/datametria"),
            scheduler_default_role=os.getenv("AWS_SCHEDULER_DEFAULT_ROLE")
        )
    
    def get_boto3_config(self) -> Dict:
        """Obter configuração para boto3."""
        config = {
            "region_name": self.region
        }
        
        if not self.use_iam_role:
            config.update({
                "aws_access_key_id": self.access_key,
                "aws_secret_access_key": self.secret_key
            })
        
        return config
