"""
Base Log Handler - Interface Abstrata para Handlers de Log

Autor: DATAMETRIA Team
Versão: 2.0.0
Compliance: LGPD/GDPR
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..enterprise_logging import LogEntry, LogLevel


class BaseLogHandler(ABC):
    """Interface base para handlers de log enterprise.
    
    Todos os handlers customizados devem herdar desta classe e implementar
    os métodos abstratos handle(), flush() e close().
    
    Attributes:
        level (LogLevel): Nível mínimo de log para processar
        config (Dict[str, Any]): Configuração específica do handler
        enabled (bool): Se o handler está ativo
        
    Example:
        >>> class CustomHandler(BaseLogHandler):
        ...     def handle(self, log_entry: LogEntry) -> None:
        ...         print(log_entry.to_json())
        ...     def flush(self) -> None:
        ...         pass
        ...     def close(self) -> None:
        ...         pass
    """
    
    def __init__(self, level = LogLevel.INFO, enabled: bool = True, **config):
        """Inicializa handler base.
        
        Args:
            level: Nível mínimo de log (LogLevel enum ou string)
            enabled (bool): Se o handler está ativo
            **config: Configurações adicionais específicas do handler
        """
        # Converte string para LogLevel se necessário
        if isinstance(level, str):
            self.level = LogLevel[level.upper()]
        else:
            self.level = level
        self.enabled = enabled
        self.config = config
        self._closed = False
    
    def should_handle(self, log_entry: LogEntry) -> bool:
        """Verifica se o log deve ser processado por este handler.
        
        Args:
            log_entry (LogEntry): Entrada de log a verificar
            
        Returns:
            bool: True se deve processar, False caso contrário
        """
        if not self.enabled or self._closed:
            return False
        
        # Comparar níveis de log
        log_levels = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
            "AUDIT": 45,
            "SECURITY": 45,
            "COMPLIANCE": 45,
        }
        
        entry_level = log_levels.get(log_entry.level, 20)
        handler_level = log_levels.get(self.level.value, 20)
        
        return entry_level >= handler_level
    
    @abstractmethod
    def handle(self, log_entry: LogEntry) -> None:
        """Processa entrada de log.
        
        Args:
            log_entry (LogEntry): Entrada de log a processar
            
        Raises:
            NotImplementedError: Deve ser implementado por subclasses
        """
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Força escrita de logs pendentes.
        
        Deve garantir que todos os logs em buffer sejam persistidos.
        
        Raises:
            NotImplementedError: Deve ser implementado por subclasses
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Fecha recursos do handler.
        
        Deve liberar todos os recursos (arquivos, conexões, etc.) e
        garantir que logs pendentes sejam escritos.
        
        Raises:
            NotImplementedError: Deve ser implementado por subclasses
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
