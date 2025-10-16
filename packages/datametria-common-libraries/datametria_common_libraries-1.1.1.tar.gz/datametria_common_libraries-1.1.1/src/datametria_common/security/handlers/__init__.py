"""
🔧 Logging Handlers - Sistema Extensível de Handlers

Handlers para múltiplos backends de logging:
- BaseLogHandler: Interface abstrata
- ConsoleLogHandler: Output para console
- FileLogHandler: Output para arquivo
- DatabaseLogHandler: Persistência em banco de dados
- CloudWatchLogHandler: AWS CloudWatch Logs
- CloudLoggingHandler: GCP Cloud Logging
"""

from .base_handler import BaseLogHandler
from .console_handler import ConsoleLogHandler
from .file_handler import FileLogHandler
from .database_handler import DatabaseLogHandler, LogQueryService
from .cloud_handlers import CloudWatchLogHandler, CloudLoggingHandler
from .async_handler import AsyncLogHandler

__all__ = [
    "BaseLogHandler",
    "ConsoleLogHandler",
    "FileLogHandler",
    "DatabaseLogHandler",
    "LogQueryService",
    "CloudWatchLogHandler",
    "CloudLoggingHandler",
    "AsyncLogHandler",
]
