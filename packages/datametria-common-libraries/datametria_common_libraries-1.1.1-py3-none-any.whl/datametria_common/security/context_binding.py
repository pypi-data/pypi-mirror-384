"""
Context Binding - Decoradores e Utilitários para Context Binding

Utilitários para adicionar contexto automaticamente aos logs usando
bind nativo do structlog.

Autor: DATAMETRIA Team
Versão: 2.0.0
"""

import functools
from contextvars import ContextVar
from typing import Any, Callable, Optional

import structlog

# ContextVar para armazenar logger atual
_current_logger: ContextVar[Optional[Any]] = ContextVar('current_logger', default=None)


def set_current_logger(logger) -> None:
    """Define logger atual no contexto.
    
    Args:
        logger: Logger a ser definido como atual
    """
    _current_logger.set(logger)


def get_current_logger():
    """Obtém logger atual do contexto.
    
    Returns:
        Logger atual ou logger padrão do structlog
    """
    logger = _current_logger.get()
    if logger is None:
        return structlog.get_logger()
    return logger


def with_logging_context(**context):
    """Decorador para adicionar contexto automaticamente aos logs.
    
    Args:
        **context: Pares chave-valor de contexto
        
    Returns:
        Decorator function
        
    Example:
        >>> @with_logging_context(request_id="req_123")
        ... def process_request():
        ...     logger = get_current_logger()
        ...     logger.info("Processing")  # Inclui request_id automaticamente
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_current_logger()
            bound_logger = logger.bind(**context)
            
            # Salvar logger anterior
            previous_logger = _current_logger.get()
            
            try:
                # Definir logger com contexto
                set_current_logger(bound_logger)
                return func(*args, **kwargs)
            finally:
                # Restaurar logger anterior
                set_current_logger(previous_logger)
        
        return wrapper
    return decorator


def bind_context(**context):
    """Context manager para adicionar contexto temporário.
    
    Args:
        **context: Pares chave-valor de contexto
        
    Yields:
        Logger com contexto vinculado
        
    Example:
        >>> logger = get_current_logger()
        >>> with bind_context(user_id="user123"):
        ...     logger.info("User action")  # Inclui user_id
    """
    class ContextBinder:
        def __enter__(self):
            self.logger = get_current_logger()
            self.bound_logger = self.logger.bind(**context)
            self.previous_logger = _current_logger.get()
            set_current_logger(self.bound_logger)
            return self.bound_logger
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            set_current_logger(self.previous_logger)
            return False
    
    return ContextBinder()
