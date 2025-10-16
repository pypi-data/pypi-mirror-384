"""
File Log Handler - Output para Arquivo

Autor: DATAMETRIA Team
Versão: 2.0.0
"""

from pathlib import Path
from typing import Optional

from .base_handler import BaseLogHandler, LogEntry, LogLevel


class FileLogHandler(BaseLogHandler):
    """Handler para persistência de logs em arquivo.
    
    Escreve logs em formato JSON em arquivo, com suporte a rotação.
    
    Attributes:
        file_path (Path): Caminho do arquivo de log
        file_handle: Handle do arquivo aberto
        
    Example:
        >>> handler = FileLogHandler(
        ...     file_path="/var/log/app.log",
        ...     level=LogLevel.INFO
        ... )
        >>> handler.handle(log_entry)
    """
    
    def __init__(
        self,
        file_path: str,
        level: LogLevel = LogLevel.INFO,
        encoding: str = "utf-8",
        **config
    ):
        """Inicializa file handler.
        
        Args:
            file_path (str): Caminho do arquivo de log
            level (LogLevel): Nível mínimo de log
            encoding (str): Encoding do arquivo
            **config: Configurações adicionais
        """
        super().__init__(level=level, **config)
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.file_handle: Optional[object] = None
        self._open_file()
    
    def _open_file(self) -> None:
        """Abre arquivo para escrita."""
        # Criar diretório se não existir
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Abrir arquivo em modo append
        self.file_handle = open(
            self.file_path,
            mode="a",
            encoding=self.encoding,
            buffering=1  # Line buffering
        )
    
    def handle(self, log_entry: LogEntry) -> None:
        """Escreve log no arquivo.
        
        Args:
            log_entry (LogEntry): Entrada de log a escrever
        """
        if not self.should_handle(log_entry):
            return
        
        if self.file_handle is None or self.file_handle.closed:
            self._open_file()
        
        try:
            self.file_handle.write(log_entry.to_json() + "\n")
        except Exception as e:
            # Log error mas não falhar
            import sys
            sys.stderr.write(f"File handler error: {e}\n")
    
    def flush(self) -> None:
        """Força flush do arquivo."""
        if self.file_handle and not self.file_handle.closed:
            try:
                self.file_handle.flush()
            except Exception:
                pass
    
    def close(self) -> None:
        """Fecha arquivo."""
        self._closed = True
        if self.file_handle and not self.file_handle.closed:
            try:
                self.file_handle.flush()
                self.file_handle.close()
            except Exception:
                pass
