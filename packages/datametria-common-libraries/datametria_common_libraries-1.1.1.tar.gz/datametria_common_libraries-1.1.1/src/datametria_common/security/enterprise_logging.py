"""
📊 Enterprise Logging - Sistema de Logging Estruturado Enterprise

Sistema completo de logging enterprise com:
- Structured logging com JSON
- Audit trail completo
- Security event logging
- Compliance logging (LGPD/GDPR)
- Performance monitoring
- Centralized log management
"""

import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog


class LogLevel(Enum):
    """Níveis de log enterprise."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"
    SECURITY = "SECURITY"
    COMPLIANCE = "COMPLIANCE"


class EventType(Enum):
    """Tipos de eventos para logging estruturado."""

    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    PERFORMANCE_EVENT = "performance_event"
    ERROR_EVENT = "error_event"
    AUDIT_EVENT = "audit_event"
    DATA_ACCESS = "data_access"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"


@dataclass
class LogEntry:
    """Entrada de log estruturada."""

    timestamp: str
    level: str
    event_type: str
    message: str
    logger_name: str
    module: str
    function: str
    line_number: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)

    def to_json(self) -> str:
        """Converte para JSON."""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)


class SecurityAuditLogger:
    """Logger específico para eventos de segurança e auditoria."""

    def __init__(self, logger_name: str = "security_audit"):
        self.logger = structlog.get_logger(logger_name)
        self._setup_security_logger()

    def _setup_security_logger(self) -> None:
        """Configura logger de segurança com formatação específica.
        
        Configura o structlog com processadores específicos para logs de segurança,
        incluindo formatação JSON, timestamps ISO e renderização de stack traces.
        
        Returns:
            None
            
        Note:
            Esta configuração é específica para auditoria de segurança e compliance.
        """
        # Configuração específica para logs de segurança
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    def log_authentication_attempt(
        self,
        user_id: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        failure_reason: Optional[str] = None,
    ) -> None:
        """Registra tentativa de autenticação no sistema.
        
        Registra todas as tentativas de autenticação, bem-sucedidas ou falhadas,
        para auditoria de segurança e detecção de ataques.
        
        Args:
            user_id (str): Identificador único do usuário
            success (bool): Se a autenticação foi bem-sucedida
            ip_address (str): Endereço IP de origem da tentativa
            user_agent (str): User agent do cliente
            failure_reason (Optional[str]): Motivo da falha, se aplicável
            
        Returns:
            None
            
        Example:
            >>> logger.log_authentication_attempt(
            ...     user_id="user123",
            ...     success=True,
            ...     ip_address="192.168.1.100",
            ...     user_agent="Mozilla/5.0..."
            ... )
        """
        self.logger.info(
            "authentication_attempt",
            event_type=EventType.AUTHENTICATION.value,
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_authorization_check(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        reason: Optional[str] = None,
    ) -> None:
        """Registra verificação de autorização de acesso.
        
        Registra todas as verificações de autorização para recursos protegidos,
        permitindo auditoria de acessos e detecção de tentativas não autorizadas.
        
        Args:
            user_id (str): Identificador único do usuário
            resource (str): Recurso sendo acessado
            action (str): Ação sendo executada no recurso
            granted (bool): Se o acesso foi concedido
            reason (Optional[str]): Motivo da decisão de autorização
            
        Returns:
            None
            
        Example:
            >>> logger.log_authorization_check(
            ...     user_id="user123",
            ...     resource="/api/users",
            ...     action="READ",
            ...     granted=True
            ... )
        """
        self.logger.info(
            "authorization_check",
            event_type=EventType.AUTHORIZATION.value,
            user_id=user_id,
            resource=resource,
            action=action,
            granted=granted,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,
        record_count: int,
        sensitive_data: bool = False,
    ) -> None:
        """Registra acesso a dados."""
        self.logger.info(
            "data_access",
            event_type=EventType.DATA_ACCESS.value,
            user_id=user_id,
            data_type=data_type,
            operation=operation,
            record_count=record_count,
            sensitive_data=sensitive_data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_security_incident(
        self,
        incident_type: str,
        severity: str,
        description: str,
        affected_systems: List[str],
        user_id: Optional[str] = None,
    ) -> None:
        """Registra incidente de segurança."""
        self.logger.error(
            "security_incident",
            event_type=EventType.SECURITY_EVENT.value,
            incident_type=incident_type,
            severity=severity,
            description=description,
            affected_systems=affected_systems,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_privilege_escalation(
        self,
        user_id: str,
        from_role: str,
        to_role: str,
        authorized_by: str,
        reason: str,
    ) -> None:
        """Registra escalação de privilégios."""
        self.logger.warning(
            "privilege_escalation",
            event_type=EventType.SECURITY_EVENT.value,
            user_id=user_id,
            from_role=from_role,
            to_role=to_role,
            authorized_by=authorized_by,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class ComplianceLogger:
    """Logger específico para eventos de compliance LGPD/GDPR.
    
    Gerencia logs específicos para compliance com regulamentações de proteção
    de dados como LGPD e GDPR, incluindo consentimentos, retenção e violações.
    
    Attributes:
        logger: Logger estruturado do structlog
        
    Example:
        >>> compliance_logger = ComplianceLogger("my_compliance")
        >>> compliance_logger.log_lgpd_event(
        ...     event_type="data_processing",
        ...     data_subject_id="subject123",
        ...     operation="read",
        ...     legal_basis="consent",
        ...     purpose="marketing"
        ... )
    """

    def __init__(self, logger_name: str = "compliance"):
        self.logger = structlog.get_logger(logger_name)

    def log_lgpd_event(
        self,
        event_type: str,
        data_subject_id: str,
        operation: str,
        legal_basis: str,
        purpose: str,
        **kwargs: Any,
    ) -> None:
        """Registra evento de compliance LGPD.
        
        Registra eventos relacionados ao processamento de dados pessoais
        conforme a Lei Geral de Proteção de Dados (LGPD).
        
        Args:
            event_type (str): Tipo do evento LGPD
            data_subject_id (str): Identificador do titular dos dados
            operation (str): Operação realizada nos dados
            legal_basis (str): Base legal para o processamento
            purpose (str): Finalidade do processamento
            **kwargs (Any): Dados adicionais específicos do evento
            
        Returns:
            None
            
        Example:
            >>> logger.log_lgpd_event(
            ...     event_type="data_processing",
            ...     data_subject_id="subject123",
            ...     operation="read",
            ...     legal_basis="consent",
            ...     purpose="marketing",
            ...     controller="company_xyz"
            ... )
        """
        self.logger.info(
            "lgpd_event",
            event_type=EventType.COMPLIANCE_EVENT.value,
            regulation="LGPD",
            lgpd_event_type=event_type,
            data_subject_id=data_subject_id,
            operation=operation,
            legal_basis=legal_basis,
            purpose=purpose,
            timestamp=datetime.now(timezone.utc).isoformat(),
            **kwargs,
        )

    def log_gdpr_event(
        self,
        event_type: str,
        data_subject_id: str,
        operation: str,
        lawful_basis: str,
        purpose: str,
        **kwargs: Any,
    ) -> None:
        """Registra evento GDPR."""
        self.logger.info(
            "gdpr_event",
            event_type=EventType.COMPLIANCE_EVENT.value,
            regulation="GDPR",
            gdpr_event_type=event_type,
            data_subject_id=data_subject_id,
            operation=operation,
            lawful_basis=lawful_basis,
            purpose=purpose,
            timestamp=datetime.now(timezone.utc).isoformat(),
            **kwargs,
        )

    def log_consent_change(
        self,
        data_subject_id: str,
        consent_type: str,
        granted: bool,
        previous_state: bool,
        user_id: str,
    ) -> None:
        """Registra mudança de consentimento."""
        self.logger.info(
            "consent_change",
            event_type=EventType.COMPLIANCE_EVENT.value,
            data_subject_id=data_subject_id,
            consent_type=consent_type,
            granted=granted,
            previous_state=previous_state,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_data_retention_action(
        self,
        data_type: str,
        action: str,
        record_count: int,
        retention_policy: str,
        reason: str,
    ) -> None:
        """Registra ação de retenção de dados."""
        self.logger.info(
            "data_retention_action",
            event_type=EventType.COMPLIANCE_EVENT.value,
            data_type=data_type,
            action=action,
            record_count=record_count,
            retention_policy=retention_policy,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_breach_notification(
        self,
        breach_id: str,
        notification_type: str,
        recipient: str,
        sent_at: datetime,
        regulation: str,
    ) -> None:
        """Registra notificação de violação de dados."""
        self.logger.critical(
            "breach_notification",
            event_type=EventType.COMPLIANCE_EVENT.value,
            breach_id=breach_id,
            notification_type=notification_type,
            recipient=recipient,
            sent_at=sent_at.isoformat(),
            regulation=regulation,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class PerformanceLogger:
    """Logger para eventos de performance."""

    def __init__(self, logger_name: str = "performance"):
        self.logger = structlog.get_logger(logger_name)

    def log_query_performance(
        self,
        query_type: str,
        execution_time: float,
        record_count: int,
        database: str,
        slow_query_threshold: float = 1.0,
    ) -> None:
        """Registra performance de queries."""
        is_slow = execution_time > slow_query_threshold

        if is_slow:
            self.logger.warning(
                "query_performance",
                event_type=EventType.PERFORMANCE_EVENT.value,
                query_type=query_type,
                execution_time=execution_time,
                record_count=record_count,
                database=database,
                is_slow_query=is_slow,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        else:
            self.logger.info(
                "query_performance",
                event_type=EventType.PERFORMANCE_EVENT.value,
                query_type=query_type,
                execution_time=execution_time,
                record_count=record_count,
                database=database,
                is_slow_query=is_slow,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def log_api_performance(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        user_id: Optional[str] = None,
    ) -> None:
        """Registra performance de APIs."""
        self.logger.info(
            "api_performance",
            event_type=EventType.PERFORMANCE_EVENT.value,
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_system_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
        active_connections: int,
    ) -> None:
        """Registra métricas do sistema."""
        self.logger.info(
            "system_metrics",
            event_type=EventType.PERFORMANCE_EVENT.value,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            active_connections=active_connections,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class EnterpriseLogger:
    """Logger enterprise principal com múltiplos canais."""

    def __init__(
        self,
        logger_name: str = "datametria_enterprise",
        log_level: LogLevel = LogLevel.INFO,
        log_file: Optional[str] = None,
        enable_console: bool = True,
    ):
        self.logger_name = logger_name
        self.log_level = log_level
        self.log_file = log_file
        self.enable_console = enable_console

        # Inicializa loggers especializados
        self.security_logger = SecurityAuditLogger(f"{logger_name}_security")
        self.compliance_logger = ComplianceLogger(f"{logger_name}_compliance")
        self.performance_logger = PerformanceLogger(f"{logger_name}_performance")

        # Configura logger principal
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configura logger enterprise."""
        # Configuração do structlog
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]

        # Adiciona processador JSON para produção
        if self.log_file:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())

        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configura handlers
        self.logger = structlog.get_logger(self.logger_name)

        # Configura arquivo de log se especificado
        if self.log_file:
            self._setup_file_handler()

    def _setup_file_handler(self) -> None:
        """Configura handler para arquivo de log."""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configuração do logging padrão para arquivo
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, self.log_level.value))

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Adiciona handler ao logger raiz
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.setLevel(getattr(logging, self.log_level.value))

    def log_user_action(
        self,
        action: str,
        user_id: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registra ação do usuário."""
        self.logger.info(
            "user_action",
            event_type=EventType.USER_ACTION.value,
            action=action,
            user_id=user_id,
            resource=resource,
            details=details or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_system_event(
        self,
        event: str,
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registra evento do sistema."""
        self.logger.info(
            "system_event",
            event_type=EventType.SYSTEM_EVENT.value,
            event=event,
            component=component,
            status=status,
            details=details or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_error(
        self,
        error_type: str,
        error_message: str,
        component: str,
        user_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Registra erro."""
        self.logger.error(
            "error_event",
            event_type=EventType.ERROR_EVENT.value,
            error_type=error_type,
            error_message=error_message,
            component=component,
            user_id=user_id,
            stack_trace=stack_trace,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_audit_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Registra evento de auditoria."""
        self.logger.info(
            "audit_event",
            event_type=EventType.AUDIT_EVENT.value,
            audit_event_type=event_type,
            details=details,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Registra evento de segurança."""
        self.security_logger.log_security_incident(
            incident_type=event_type,
            severity="medium",
            description=str(details),
            affected_systems=["application"],
            user_id=details.get("user_id"),
        )

    def log_compliance_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Registra evento de compliance."""
        regulation = details.get("regulation", "LGPD")

        if regulation == "LGPD":
            self.compliance_logger.log_lgpd_event(
                event_type=event_type,
                data_subject_id=details.get("data_subject_id", "unknown"),
                operation=details.get("operation", "unknown"),
                legal_basis=details.get("legal_basis", "unknown"),
                purpose=details.get("purpose", "unknown"),
                **{
                    k: v
                    for k, v in details.items()
                    if k
                    not in [
                        "regulation",
                        "data_subject_id",
                        "operation",
                        "legal_basis",
                        "purpose",
                    ]
                },
            )
        elif regulation == "GDPR":
            self.compliance_logger.log_gdpr_event(
                event_type=event_type,
                data_subject_id=details.get("data_subject_id", "unknown"),
                operation=details.get("operation", "unknown"),
                lawful_basis=details.get("lawful_basis", "unknown"),
                purpose=details.get("purpose", "unknown"),
                **{
                    k: v
                    for k, v in details.items()
                    if k
                    not in [
                        "regulation",
                        "data_subject_id",
                        "operation",
                        "lawful_basis",
                        "purpose",
                    ]
                },
            )

    def log_performance_event(self, event_type: str, metrics: Dict[str, Any]) -> None:
        """Registra evento de performance."""
        if event_type == "query_performance":
            self.performance_logger.log_query_performance(
                query_type=metrics.get("query_type", "unknown"),
                execution_time=metrics.get("execution_time", 0.0),
                record_count=metrics.get("record_count", 0),
                database=metrics.get("database", "unknown"),
            )
        elif event_type == "api_performance":
            self.performance_logger.log_api_performance(
                endpoint=metrics.get("endpoint", "unknown"),
                method=metrics.get("method", "GET"),
                response_time=metrics.get("response_time", 0.0),
                status_code=metrics.get("status_code", 200),
                user_id=metrics.get("user_id"),
            )

    def create_context_logger(self, **context) -> "EnterpriseLogger":
        """Cria logger com contexto específico."""
        bound_logger = self.logger.bind(**context)

        # Cria nova instância com contexto
        context_logger = EnterpriseLogger(
            logger_name=f"{self.logger_name}_context",
            log_level=self.log_level,
            log_file=self.log_file,
            enable_console=self.enable_console,
        )
        context_logger.logger = bound_logger

        return context_logger
