"""
Console Log Handler - Output para Console

Autor: DATAMETRIA Team
Versão: 2.0.0
"""

import sys
from typing import TextIO

from .base_handler import BaseLogHandler, LogEntry, LogLevel


class ConsoleLogHandler(BaseLogHandler):
    """Handler para output de logs no console.
    
    Escreve logs formatados em JSON para stdout ou stderr.
    
    Attributes:
        stream (TextIO): Stream de saída (stdout ou stderr)
        
    Example:
        >>> handler = ConsoleLogHandler(level=LogLevel.INFO)
        >>> handler.handle(log_entry)
    """
    
    def __init__(self, level: LogLevel = LogLevel.INFO, use_stderr: bool = False, **config):
        """Inicializa console handler.
        
        Args:
            level (LogLevel): Nível mínimo de log
            use_stderr (bool): Se True, usa stderr; caso contrário, stdout
            **config: Configurações adicionais
        """
        super().__init__(level=level, **config)
        self.stream: TextIO = sys.stderr if use_stderr else sys.stdout
    
    def handle(self, log_entry: LogEntry) -> None:
        """Escreve log no console.
        
        Args:
            log_entry (LogEntry): Entrada de log a escrever
        """
        if not self.should_handle(log_entry):
            return
        
        try:
            self.stream.write(log_entry.to_json() + "\n")
            self.stream.flush()
        except Exception as e:
            # Não falhar se console output falhar
            sys.stderr.write(f"Console handler error: {e}\n")
    
    def flush(self) -> None:
        """Força flush do stream."""
        try:
            self.stream.flush()
        except Exception:
            pass
    
    def close(self) -> None:
        """Fecha handler (não fecha stdout/stderr)."""
        self._closed = True
        self.flush()
