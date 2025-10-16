"""
Cloud Log Handlers - AWS CloudWatch e GCP Cloud Logging

Handlers para envio de logs para serviços cloud com retry e métricas.

Autor: DATAMETRIA Team
Versão: 2.0.0
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_handler import BaseLogHandler, LogEntry, LogLevel


class CloudWatchLogHandler(BaseLogHandler):
    """Handler para AWS CloudWatch Logs.
    
    Envia logs para AWS CloudWatch com:
    - Autenticação via IAM
    - Buffer e batch sending
    - Retry logic
    - Sequence token management
    
    Example:
        >>> handler = CloudWatchLogHandler(
        ...     log_group="/aws/datametria/app",
        ...     log_stream="production",
        ...     level=LogLevel.INFO
        ... )
    """
    
    def __init__(
        self,
        log_group: str,
        log_stream: str,
        region_name: str = "us-east-1",
        batch_size: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **config
    ):
        """Inicializa CloudWatch handler.
        
        Args:
            log_group (str): Nome do log group
            log_stream (str): Nome do log stream
            region_name (str): Região AWS
            batch_size (int): Tamanho do batch
            max_retries (int): Máximo de retries
            retry_delay (float): Delay entre retries
            **config: Configurações adicionais
        """
        super().__init__(**config)
        
        try:
            import boto3
            self.boto3 = boto3
        except ImportError:
            raise ImportError("boto3 is required for CloudWatch handler. Install with: pip install boto3")
        
        self.log_group = log_group
        self.log_stream = log_stream
        self.region_name = region_name
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.client = self.boto3.client('logs', region_name=region_name)
        self.sequence_token: Optional[str] = None
        self.buffer: List[LogEntry] = []
        self.metrics = {"sent": 0, "failed": 0, "retries": 0}
        
        self._ensure_log_stream()
    
    def _ensure_log_stream(self) -> None:
        """Garante que log group e stream existem."""
        try:
            # Criar log group se não existir
            try:
                self.client.create_log_group(logGroupName=self.log_group)
            except self.client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Criar log stream se não existir
            try:
                self.client.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream
                )
            except self.client.exceptions.ResourceAlreadyExistsException:
                # Obter sequence token existente
                response = self.client.describe_log_streams(
                    logGroupName=self.log_group,
                    logStreamNamePrefix=self.log_stream,
                    limit=1
                )
                if response['logStreams']:
                    self.sequence_token = response['logStreams'][0].get('uploadSequenceToken')
        
        except Exception as e:
            import sys
            sys.stderr.write(f"CloudWatch setup error: {e}\n")
    
    def handle(self, log_entry: LogEntry) -> None:
        """Adiciona log ao buffer.
        
        Args:
            log_entry (LogEntry): Entrada de log
        """
        if not self.should_handle(log_entry):
            return
        
        self.buffer.append(log_entry)
        
        if len(self.buffer) >= self.batch_size:
            self.flush()
    
    def flush(self) -> None:
        """Envia logs para CloudWatch em batch."""
        if not self.buffer:
            return
        
        for attempt in range(self.max_retries):
            try:
                self._send_batch()
                self.metrics["sent"] += len(self.buffer)
                self.buffer.clear()
                return
            
            except self.client.exceptions.InvalidSequenceTokenException as e:
                # Atualizar sequence token e tentar novamente
                self.sequence_token = e.response['Error']['Message'].split('is: ')[-1]
                self.metrics["retries"] += 1
                continue
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    self.metrics["retries"] += 1
                else:
                    import sys
                    sys.stderr.write(f"CloudWatch send failed: {e}\n")
                    self.metrics["failed"] += len(self.buffer)
                    self.buffer.clear()
                    return
    
    def _send_batch(self) -> None:
        """Envia batch de logs para CloudWatch."""
        log_events = []
        
        for log_entry in self.buffer:
            # Converter timestamp para milliseconds
            try:
                dt = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
                timestamp_ms = int(dt.timestamp() * 1000)
            except:
                timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            log_events.append({
                'timestamp': timestamp_ms,
                'message': log_entry.to_json()
            })
        
        # Ordenar por timestamp (requerido pelo CloudWatch)
        log_events.sort(key=lambda x: x['timestamp'])
        
        # Enviar para CloudWatch
        kwargs = {
            'logGroupName': self.log_group,
            'logStreamName': self.log_stream,
            'logEvents': log_events
        }
        
        if self.sequence_token:
            kwargs['sequenceToken'] = self.sequence_token
        
        response = self.client.put_log_events(**kwargs)
        self.sequence_token = response.get('nextSequenceToken')
    
    def get_metrics(self) -> Dict[str, int]:
        """Retorna métricas de envio.
        
        Returns:
            Dict[str, int]: Métricas (sent, failed, retries)
        """
        return self.metrics.copy()
    
    def close(self) -> None:
        """Fecha handler e envia logs pendentes."""
        self._closed = True
        self.flush()


class CloudLoggingHandler(BaseLogHandler):
    """Handler para GCP Cloud Logging.
    
    Envia logs para GCP Cloud Logging com:
    - Autenticação via Service Account
    - Buffer e batch sending
    - Retry logic
    - Structured logging
    
    Example:
        >>> handler = CloudLoggingHandler(
        ...     project_id="my-project",
        ...     log_name="datametria-app",
        ...     level=LogLevel.INFO
        ... )
    """
    
    def __init__(
        self,
        project_id: str,
        log_name: str,
        batch_size: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **config
    ):
        """Inicializa Cloud Logging handler.
        
        Args:
            project_id (str): ID do projeto GCP
            log_name (str): Nome do log
            batch_size (int): Tamanho do batch
            max_retries (int): Máximo de retries
            retry_delay (float): Delay entre retries
            **config: Configurações adicionais
        """
        super().__init__(**config)
        
        try:
            from google.cloud import logging as cloud_logging
            self.cloud_logging = cloud_logging
        except ImportError:
            raise ImportError(
                "google-cloud-logging is required for Cloud Logging handler. "
                "Install with: pip install google-cloud-logging"
            )
        
        self.project_id = project_id
        self.log_name = log_name
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.client = self.cloud_logging.Client(project=project_id)
        self.logger = self.client.logger(log_name)
        self.buffer: List[LogEntry] = []
        self.metrics = {"sent": 0, "failed": 0, "retries": 0}
    
    def handle(self, log_entry: LogEntry) -> None:
        """Adiciona log ao buffer.
        
        Args:
            log_entry (LogEntry): Entrada de log
        """
        if not self.should_handle(log_entry):
            return
        
        self.buffer.append(log_entry)
        
        if len(self.buffer) >= self.batch_size:
            self.flush()
    
    def flush(self) -> None:
        """Envia logs para Cloud Logging em batch."""
        if not self.buffer:
            return
        
        for attempt in range(self.max_retries):
            try:
                self._send_batch()
                self.metrics["sent"] += len(self.buffer)
                self.buffer.clear()
                return
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    self.metrics["retries"] += 1
                else:
                    import sys
                    sys.stderr.write(f"Cloud Logging send failed: {e}\n")
                    self.metrics["failed"] += len(self.buffer)
                    self.buffer.clear()
                    return
    
    def _send_batch(self) -> None:
        """Envia batch de logs para Cloud Logging."""
        # Mapear níveis de log
        severity_map = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
            "AUDIT": "NOTICE",
            "SECURITY": "ALERT",
            "COMPLIANCE": "NOTICE",
        }
        
        for log_entry in self.buffer:
            severity = severity_map.get(log_entry.level, "INFO")
            
            # Estruturar dados do log
            struct_data = {
                "message": log_entry.message,
                "level": log_entry.level,
                "event_type": log_entry.event_type,
                "logger_name": log_entry.logger_name,
                "module": log_entry.module,
                "function": log_entry.function,
                "line_number": log_entry.line_number,
            }
            
            # Adicionar campos opcionais
            if log_entry.user_id:
                struct_data["user_id"] = log_entry.user_id
            if log_entry.session_id:
                struct_data["session_id"] = log_entry.session_id
            if log_entry.request_id:
                struct_data["request_id"] = log_entry.request_id
            if log_entry.ip_address:
                struct_data["ip_address"] = log_entry.ip_address
            if log_entry.additional_data:
                struct_data["additional_data"] = log_entry.additional_data
            
            # Enviar log estruturado
            self.logger.log_struct(struct_data, severity=severity)
    
    def get_metrics(self) -> Dict[str, int]:
        """Retorna métricas de envio.
        
        Returns:
            Dict[str, int]: Métricas (sent, failed, retries)
        """
        return self.metrics.copy()
    
    def close(self) -> None:
        """Fecha handler e envia logs pendentes."""
        self._closed = True
        self.flush()
