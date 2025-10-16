"""
⚙️ Configuration - Sistema de Configuração Centralizada

Configuração centralizada para logging enterprise:
- LoggingConfig com Pydantic
- Suporte a YAML/JSON
- Variáveis de ambiente
- Validação automática
"""

from .logging_config import HandlerConfig, LoggingConfig

__all__ = [
    "LoggingConfig",
    "HandlerConfig",
]
