"""
Centralized Logger - Logger Enterprise com Configuração Centralizada

Sistema de logging enterprise com configuração única do structlog,
eliminando reconfiguração em sub-loggers e garantindo consistência.

Autor: DATAMETRIA Team
Versão: 2.0.0
"""

from typing import Optional, Dict, Any

import structlog

from .config import LoggingConfig
from .enterprise_logging import (
    ComplianceLogger,
    PerformanceLogger,
    SecurityAuditLogger,
)
from .handlers import (
    BaseLogHandler,
    CloudLoggingHandler,
    CloudWatchLogHandler,
    ConsoleLogHandler,
    DatabaseLogHandler,
    FileLogHandler,
)
from .processors import ComplianceProcessor, DataMaskingProcessor


class CentralizedEnterpriseLogger:
    """Logger enterprise com configuração centralizada do structlog.
    
    Configura structlog uma única vez e compartilha entre todos os sub-loggers,
    eliminando conflitos e garantindo consistência.
    
    Attributes:
        config (LoggingConfig): Configuração centralizada
        logger: Logger principal do structlog
        security_logger: Logger de segurança e auditoria
        compliance_logger: Logger de compliance LGPD/GDPR
        performance_logger: Logger de performance
        handlers (list): Lista de handlers configurados
        
    Example:
        >>> config = LoggingConfig(
        ...     service_name="my-api",
        ...     handlers=[
        ...         HandlerConfig(type="console", level="INFO"),
        ...         HandlerConfig(type="database", config={"connection_string": "..."})
        ...     ]
        ... )
        >>> logger = CentralizedEnterpriseLogger(config)
        >>> logger.info("Application started")
    """
    
    _structlog_configured = False
    
    def __init__(self, config: LoggingConfig):
        """Inicializa logger com configuração centralizada.
        
        Args:
            config (LoggingConfig): Configuração do sistema de logging
        """
        self.config = config
        self.handlers = []
        
        # Configurar structlog uma única vez
        if not CentralizedEnterpriseLogger._structlog_configured:
            self._configure_structlog()
            CentralizedEnterpriseLogger._structlog_configured = True
        
        # Criar logger principal
        self.logger = structlog.get_logger(config.service_name)
        
        # Criar sub-loggers (sem reconfiguração)
        self.security_logger = SecurityAuditLogger(f"{config.service_name}_security")
        self.compliance_logger = ComplianceLogger(f"{config.service_name}_compliance")
        self.performance_logger = PerformanceLogger(f"{config.service_name}_performance")
        
        # Configurar handlers
        self._setup_handlers()
    
    def _configure_structlog(self) -> None:
        """Configura structlog uma única vez com processadores modulares."""
        import logging
        import sys
        
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
        ]
        
        # Adicionar processadores opcionais
        if self.config.enable_data_masking:
            processors.append(
                DataMaskingProcessor(
                    custom_patterns=self.config.custom_masking_patterns,
                    preserve_length=self.config.preserve_length,
                )
            )
        
        if self.config.enable_compliance_metadata:
            processors.append(
                ComplianceProcessor(
                    default_classification=self.config.data_classification,
                    legal_basis=self.config.legal_basis,
                    processing_purpose=self.config.processing_purpose,
                )
            )
        
        # Processadores finais
        processors.extend([
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ])
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Configura stdlib logging para capturar logs do structlog
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, self.config.log_level)
        )
    
    def _setup_handlers(self) -> None:
        """Configura handlers baseado na configuração."""
        for handler_config in self.config.handlers:
            if not handler_config.enabled:
                continue
            
            handler = self._create_handler(handler_config)
            if handler:
                self.handlers.append(handler)
    
    def _create_handler(self, handler_config) -> Optional[BaseLogHandler]:
        """Cria handler baseado na configuração.
        
        Args:
            handler_config: Configuração do handler
            
        Returns:
            BaseLogHandler ou None se tipo inválido
        """
        handler_type = handler_config.type
        level = handler_config.level
        config = handler_config.config
        
        if handler_type == "console":
            return ConsoleLogHandler(
                level=level,
                use_stderr=config.get("use_stderr", False)
            )
        
        elif handler_type == "file":
            return FileLogHandler(
                level=level,
                file_path=config.get("file_path", "/var/log/app.log")
            )
        
        elif handler_type == "database":
            return DatabaseLogHandler(
                level=level,
                connection_string=config.get("connection_string"),
                batch_size=config.get("batch_size", 100)
            )
        
        elif handler_type == "cloudwatch":
            return CloudWatchLogHandler(
                level=level,
                log_group=config.get("log_group"),
                log_stream=config.get("log_stream"),
                region=config.get("region", "us-east-1")
            )
        
        elif handler_type == "cloudlogging":
            return CloudLoggingHandler(
                level=level,
                project_id=config.get("project_id"),
                log_name=config.get("log_name")
            )
        
        return None
    
    def info(self, message: str, **kwargs) -> None:
        """Log nível INFO."""
        self.logger.info(message, **kwargs)
        self._write_to_handlers("INFO", message, kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log nível DEBUG."""
        self.logger.debug(message, **kwargs)
        self._write_to_handlers("DEBUG", message, kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log nível WARNING."""
        self.logger.warning(message, **kwargs)
        self._write_to_handlers("WARNING", message, kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log nível ERROR."""
        self.logger.error(message, **kwargs)
        self._write_to_handlers("ERROR", message, kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log nível CRITICAL."""
        self.logger.critical(message, **kwargs)
        self._write_to_handlers("CRITICAL", message, kwargs)
    
    def _write_to_handlers(self, level: str, message: str, context: dict) -> None:
        """Escreve log em todos os handlers configurados.
        
        Args:
            level (str): Nível do log
            message (str): Mensagem
            context (dict): Contexto adicional
        """
        if not self.handlers:
            return
            
        from datetime import datetime, timezone
        from .enterprise_logging import LogEntry
        import inspect
        
        # Obtém informações do caller
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back if frame and frame.f_back else None
        
        # Cria LogEntry com assinatura correta
        log_entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            event_type="system_event",
            message=message,
            logger_name=self.config.service_name,
            module=caller_frame.f_code.co_filename if caller_frame else "unknown",
            function=caller_frame.f_code.co_name if caller_frame else "unknown",
            line_number=caller_frame.f_lineno if caller_frame else 0,
            additional_data=context
        )
        
        # Distribui para todos os handlers
        for handler in self.handlers:
            try:
                handler.handle(log_entry)
                handler.flush()  # Força flush imediato
            except Exception as e:
                import sys
                sys.stderr.write(f"Handler error: {e}\n")  # Debug
    
    def flush(self) -> None:
        """Força escrita de logs pendentes em todos os handlers."""
        for handler in self.handlers:
            handler.flush()
    
    def close(self) -> None:
        """Fecha todos os handlers."""
        for handler in self.handlers:
            handler.close()
    
    def bind(self, **context):
        """Cria logger com contexto adicional usando bind nativo.
        
        Args:
            **context: Pares chave-valor de contexto
            
        Returns:
            BoundLogger: Logger com contexto vinculado
            
        Example:
            >>> logger = CentralizedEnterpriseLogger(config)
            >>> bound = logger.bind(request_id="req_123", user_id="user456")
            >>> bound.info("Processing request")  # Inclui request_id e user_id
        """
        return self.logger.bind(**context)
