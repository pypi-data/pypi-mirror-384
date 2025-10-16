"""
📊 AWS Models - DATAMETRIA AWS Services

Modelos Pydantic para serviços AWS integrados ao framework DATAMETRIA.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class AWSServiceType(str, Enum):
    """Tipos de serviços AWS."""
    S3 = "s3"
    RDS = "rds"
    LAMBDA = "lambda"
    EVENTBRIDGE = "eventbridge"
    STEPFUNCTIONS = "stepfunctions"
    SCHEDULER = "scheduler"
    CLOUDWATCH = "cloudwatch"
    SECRETS = "secrets"


class AWSResult(BaseModel):
    """Resultado base para operações AWS."""
    success: bool
    service: AWSServiceType
    operation: str
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# S3 Models
class S3UploadResult(AWSResult):
    """Resultado de upload S3."""
    service: AWSServiceType = AWSServiceType.S3
    operation: str = "upload"
    bucket: Optional[str] = None
    key: Optional[str] = None
    file_size: Optional[int] = None
    upload_time: Optional[float] = None
    presigned_url: Optional[str] = None
    etag: Optional[str] = None


class S3DownloadResult(AWSResult):
    """Resultado de download S3."""
    service: AWSServiceType = AWSServiceType.S3
    operation: str = "download"
    bucket: Optional[str] = None
    key: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_time: Optional[float] = None


# EventBridge Models
class EventBridgeEvent(BaseModel):
    """Evento EventBridge."""
    source: str
    detail_type: str
    detail: Dict[str, Any]
    event_bus_name: Optional[str] = None
    resources: Optional[List[str]] = None


class EventBridgeResult(AWSResult):
    """Resultado de operação EventBridge."""
    service: AWSServiceType = AWSServiceType.EVENTBRIDGE
    successful_entries: Optional[int] = None
    failed_entries: Optional[int] = None
    failed_entry_details: Optional[List[Dict]] = None


class EventBridgeRuleConfig(BaseModel):
    """Configuração de regra EventBridge."""
    name: str
    event_pattern: Dict[str, Any]
    state: str = "ENABLED"
    description: Optional[str] = None
    event_bus_name: Optional[str] = None
    targets: Optional[List[Dict]] = None


# Step Functions Models
class StateMachineType(str, Enum):
    """Tipos de state machine."""
    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"


class StateMachineConfig(BaseModel):
    """Configuração de state machine."""
    name: str
    definition: Dict[str, Any]
    role_arn: str
    type: StateMachineType = StateMachineType.STANDARD
    logging_enabled: bool = True
    tracing_enabled: bool = True


class ExecutionConfig(BaseModel):
    """Configuração de execução."""
    state_machine_arn: str
    name: str
    input_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(AWSResult):
    """Resultado de execução Step Functions."""
    service: AWSServiceType = AWSServiceType.STEPFUNCTIONS
    operation: str = "start_execution"
    execution_arn: Optional[str] = None
    start_date: Optional[datetime] = None


class ExecutionStatus(str, Enum):
    """Status de execução."""
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    ABORTED = "ABORTED"


class ExecutionStatusResult(AWSResult):
    """Resultado de status de execução."""
    service: AWSServiceType = AWSServiceType.STEPFUNCTIONS
    operation: str = "get_execution_status"
    status: Optional[ExecutionStatus] = None
    start_date: Optional[datetime] = None
    stop_date: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None


# Scheduler Models
class ScheduleConfig(BaseModel):
    """Configuração de schedule."""
    name: str
    schedule_expression: str
    target_arn: str
    role_arn: str
    input_data: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    timezone: Optional[str] = None
    flexible_time_window_mode: str = "OFF"
    maximum_window_minutes: Optional[int] = None


class ScheduleResult(AWSResult):
    """Resultado de operação Scheduler."""
    service: AWSServiceType = AWSServiceType.SCHEDULER
    schedule_arn: Optional[str] = None


# Lambda Models
class LambdaInvokeResult(AWSResult):
    """Resultado de invocação Lambda."""
    service: AWSServiceType = AWSServiceType.LAMBDA
    operation: str = "invoke"
    function_name: Optional[str] = None
    status_code: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    log_result: Optional[str] = None


# CloudWatch Models
class MetricData(BaseModel):
    """Dados de métrica CloudWatch."""
    metric_name: str
    value: Union[int, float]
    unit: str = "Count"
    dimensions: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None


class CloudWatchResult(AWSResult):
    """Resultado de operação CloudWatch."""
    service: AWSServiceType = AWSServiceType.CLOUDWATCH
    metric_data_id: Optional[str] = None


# Secrets Manager Models
class SecretResult(AWSResult):
    """Resultado de operação Secrets Manager."""
    service: AWSServiceType = AWSServiceType.SECRETS
    secret_arn: Optional[str] = None
    secret_value: Optional[Dict[str, Any]] = None
    version_id: Optional[str] = None


# RDS Models
class RDSResult(AWSResult):
    """Resultado de operação RDS."""
    service: AWSServiceType = AWSServiceType.RDS
    instance_id: Optional[str] = None
    endpoint: Optional[str] = None
    status: Optional[str] = None
