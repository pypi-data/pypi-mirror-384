"""
Logging Configuration - Configuração Centralizada de Logging

Sistema de configuração centralizada com:
- Pydantic para validação
- Suporte a YAML/JSON
- Variáveis de ambiente
- Configuração de handlers
- Processadores opcionais

Autor: DATAMETRIA Team
Versão: 2.0.0
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from ..enterprise_logging import LogLevel


class HandlerConfig(BaseModel):
    """Configuração de um handler de log.
    
    Attributes:
        type (str): Tipo do handler (console, file, database, cloudwatch, cloudlogging)
        level (str): Nível mínimo de log
        enabled (bool): Se o handler está ativo
        config (Dict): Configurações específicas do handler
        
    Example:
        >>> handler = HandlerConfig(
        ...     type="file",
        ...     level="INFO",
        ...     config={"file_path": "/var/log/app.log"}
        ... )
    """
    type: str
    level: str = "INFO"
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Valida tipo de handler."""
        valid_types = ['console', 'file', 'database', 'cloudwatch', 'cloudlogging']
        if v not in valid_types:
            raise ValueError(f"Handler type must be one of {valid_types}")
        return v
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        """Valida nível de log."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'AUDIT', 'SECURITY', 'COMPLIANCE']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


class LoggingConfig(BaseModel):
    """Configuração centralizada do sistema de logging.
    
    Attributes:
        service_name (str): Nome do serviço
        environment (str): Ambiente (development, staging, production)
        version (str): Versão do serviço
        log_level (str): Nível de log global
        handlers (List[HandlerConfig]): Lista de handlers
        enable_data_masking (bool): Habilitar mascaramento de dados
        custom_masking_patterns (List[str]): Padrões customizados de mascaramento
        enable_compliance_metadata (bool): Habilitar metadados de compliance
        data_classification (str): Classificação padrão de dados
        legal_basis (Optional[str]): Base legal padrão
        processing_purpose (Optional[str]): Finalidade padrão
        
    Example:
        >>> config = LoggingConfig(
        ...     service_name="my-api",
        ...     environment="production",
        ...     handlers=[
        ...         HandlerConfig(type="console", level="INFO"),
        ...         HandlerConfig(type="file", config={"file_path": "/var/log/app.log"})
        ...     ]
        ... )
    """
    
    # Identificação do serviço
    service_name: str
    environment: str = "production"
    version: str = "1.0.0"
    
    # Configuração de logging
    log_level: str = "INFO"
    handlers: List[HandlerConfig] = Field(default_factory=list)
    
    # Data masking
    enable_data_masking: bool = True
    custom_masking_patterns: List[str] = Field(default_factory=list)
    preserve_length: bool = False
    
    # Compliance
    enable_compliance_metadata: bool = True
    data_classification: str = "internal"
    legal_basis: Optional[str] = None
    processing_purpose: Optional[str] = None
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Valida ambiente."""
        valid_envs = ['development', 'staging', 'production', 'test']
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Valida nível de log."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator('data_classification')
    @classmethod
    def validate_classification(cls, v):
        """Valida classificação de dados."""
        valid_classifications = ['public', 'internal', 'confidential', 'restricted']
        if v not in valid_classifications:
            raise ValueError(f"Data classification must be one of {valid_classifications}")
        return v
    
    @classmethod
    def from_yaml(cls, path: str) -> "LoggingConfig":
        """Carrega configuração de arquivo YAML.
        
        Args:
            path (str): Caminho do arquivo YAML
            
        Returns:
            LoggingConfig: Configuração carregada
            
        Example:
            >>> config = LoggingConfig.from_yaml("config/logging.yaml")
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, path: str) -> "LoggingConfig":
        """Carrega configuração de arquivo JSON.
        
        Args:
            path (str): Caminho do arquivo JSON
            
        Returns:
            LoggingConfig: Configuração carregada
            
        Example:
            >>> config = LoggingConfig.from_json("config/logging.json")
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(**data)
    
    @classmethod
    def from_env(cls, prefix: str = "LOG_") -> "LoggingConfig":
        """Carrega configuração de variáveis de ambiente (Enterprise-Grade).
        
        Implementa padrão de configuração enterprise com:
        - Validação automática de variáveis
        - Fallback para valores padrão seguros
        - Suporte a múltiplos handlers simultâneos
        - Criação automática de diretórios
        - Configuração baseada em ambiente (dev/staging/prod)
        
        Args:
            prefix (str): Prefixo das variáveis de ambiente
            
        Returns:
            LoggingConfig: Configuração carregada e validada
            
        Example:
            >>> # Com variáveis: LOG_SERVICE_NAME=my-api, LOG_ENVIRONMENT=production
            >>> config = LoggingConfig.from_env()
        """
        # Detecta ambiente para defaults inteligentes
        environment = os.getenv(f'{prefix}ENVIRONMENT', 
                               os.getenv('ENVIRONMENT', 'production'))
        
        # Configuração base
        config_data = {
            'service_name': os.getenv(f'{prefix}SERVICE_NAME', 'app'),
            'environment': environment,
            'version': os.getenv(f'{prefix}VERSION', '1.0.0'),
            'log_level': os.getenv(f'{prefix}LEVEL', 'INFO'),
            'enable_data_masking': os.getenv(f'{prefix}ENABLE_DATA_MASKING', 'true').lower() == 'true',
            'enable_compliance_metadata': os.getenv(f'{prefix}ENABLE_COMPLIANCE', 'true').lower() == 'true',
            'data_classification': os.getenv(f'{prefix}DATA_CLASSIFICATION', 'internal'),
        }
        
        # Handlers enterprise com auto-discovery
        handlers = cls._discover_handlers_from_env(prefix, environment)
        
        # Garante pelo menos console handler em desenvolvimento
        if not handlers and environment == 'development':
            handlers.append(HandlerConfig(
                type='console',
                level='DEBUG',
                config={'use_stderr': False}
            ))
        
        config_data['handlers'] = handlers
        
        return cls(**config_data)
    
    @staticmethod
    def _discover_handlers_from_env(prefix: str, environment: str) -> List[HandlerConfig]:
        """Descobre e configura handlers baseado em variáveis de ambiente.
        
        Implementa auto-discovery enterprise de handlers com:
        - Validação de pré-requisitos
        - Criação automática de recursos
        - Configuração adaptativa por ambiente
        
        Args:
            prefix (str): Prefixo das variáveis
            environment (str): Ambiente atual
            
        Returns:
            List[HandlerConfig]: Lista de handlers configurados
        """
        handlers = []
        
        # Console Handler - Sempre habilitado em desenvolvimento
        console_enabled = os.getenv(f'{prefix}CONSOLE_ENABLED', 
                                   'true' if environment == 'development' else 'false')
        if console_enabled.lower() == 'true':
            handlers.append(HandlerConfig(
                type='console',
                level=os.getenv(f'{prefix}CONSOLE_LEVEL', 'DEBUG' if environment == 'development' else 'INFO'),
                config={'use_stderr': os.getenv(f'{prefix}CONSOLE_STDERR', 'false').lower() == 'true'}
            ))
        
        # File Handler - Enterprise file logging
        file_enabled = os.getenv(f'{prefix}FILE_ENABLED', 'false')
        if file_enabled.lower() == 'true':
            file_path = os.getenv(f'{prefix}FILE_PATH', 'logs/app.log')
            
            # Cria diretório de logs se não existir (enterprise pattern)
            log_dir = Path(file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            handlers.append(HandlerConfig(
                type='file',
                level=os.getenv(f'{prefix}FILE_LEVEL', 'INFO'),
                config={
                    'file_path': file_path,
                    'max_bytes': int(os.getenv(f'{prefix}FILE_MAX_BYTES', '10485760')),  # 10MB
                    'backup_count': int(os.getenv(f'{prefix}FILE_BACKUP_COUNT', '5')),
                    'encoding': os.getenv(f'{prefix}FILE_ENCODING', 'utf-8')
                }
            ))
        
        # Database Handler - Enterprise audit trail
        db_enabled = os.getenv(f'{prefix}DB_ENABLED', 'false')
        if db_enabled.lower() == 'true':
            connection_string = os.getenv(f'{prefix}DB_CONNECTION_STRING')
            if connection_string:  # Valida pré-requisito
                handlers.append(HandlerConfig(
                    type='database',
                    level=os.getenv(f'{prefix}DB_LEVEL', 'INFO'),
                    config={
                        'connection_string': connection_string,
                        'batch_size': int(os.getenv(f'{prefix}DB_BATCH_SIZE', '100')),
                        'table_name': os.getenv(f'{prefix}DB_TABLE', 'audit_logs'),
                        'async_mode': os.getenv(f'{prefix}DB_ASYNC', 'true').lower() == 'true'
                    }
                ))
        
        # CloudWatch Handler - AWS enterprise logging
        cloudwatch_enabled = os.getenv(f'{prefix}CLOUDWATCH_ENABLED', 'false')
        if cloudwatch_enabled.lower() == 'true':
            log_group = os.getenv(f'{prefix}CLOUDWATCH_LOG_GROUP')
            if log_group:  # Valida pré-requisito
                handlers.append(HandlerConfig(
                    type='cloudwatch',
                    level=os.getenv(f'{prefix}CLOUDWATCH_LEVEL', 'INFO'),
                    config={
                        'log_group': log_group,
                        'log_stream': os.getenv(f'{prefix}CLOUDWATCH_LOG_STREAM', f'{environment}-stream'),
                        'region': os.getenv(f'{prefix}CLOUDWATCH_REGION', os.getenv('AWS_REGION', 'us-east-1')),
                        'retention_days': int(os.getenv(f'{prefix}CLOUDWATCH_RETENTION', '30'))
                    }
                ))
        
        # Cloud Logging Handler - GCP enterprise logging
        cloudlogging_enabled = os.getenv(f'{prefix}CLOUDLOGGING_ENABLED', 'false')
        if cloudlogging_enabled.lower() == 'true':
            project_id = os.getenv(f'{prefix}CLOUDLOGGING_PROJECT_ID', os.getenv('GCP_PROJECT_ID'))
            if project_id:  # Valida pré-requisito
                handlers.append(HandlerConfig(
                    type='cloudlogging',
                    level=os.getenv(f'{prefix}CLOUDLOGGING_LEVEL', 'INFO'),
                    config={
                        'project_id': project_id,
                        'log_name': os.getenv(f'{prefix}CLOUDLOGGING_LOG_NAME', f'{environment}-logs'),
                        'resource_type': os.getenv(f'{prefix}CLOUDLOGGING_RESOURCE_TYPE', 'global')
                    }
                ))
        
        return handlers
    
    def to_yaml(self, path: str) -> None:
        """Salva configuração em arquivo YAML.
        
        Args:
            path (str): Caminho do arquivo YAML
            
        Example:
            >>> config.to_yaml("config/logging.yaml")
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")
        
        # Criar diretório se não existir
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, allow_unicode=True)
    
    def to_json(self, path: str) -> None:
        """Salva configuração em arquivo JSON.
        
        Args:
            path (str): Caminho do arquivo JSON
            
        Example:
            >>> config.to_json("config/logging.json")
        """
        # Criar diretório se não existir
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
    
    def get_handler_config(self, handler_type: str) -> Optional[HandlerConfig]:
        """Obtém configuração de um handler específico.
        
        Args:
            handler_type (str): Tipo do handler
            
        Returns:
            Optional[HandlerConfig]: Configuração do handler ou None
        """
        for handler in self.handlers:
            if handler.type == handler_type:
                return handler
        return None
    
    def add_handler(self, handler: HandlerConfig) -> None:
        """Adiciona handler à configuração.
        
        Args:
            handler (HandlerConfig): Handler a adicionar
        """
        self.handlers.append(handler)
    
    def remove_handler(self, handler_type: str) -> bool:
        """Remove handler da configuração.
        
        Args:
            handler_type (str): Tipo do handler a remover
            
        Returns:
            bool: True se removido, False se não encontrado
        """
        for i, handler in enumerate(self.handlers):
            if handler.type == handler_type:
                self.handlers.pop(i)
                return True
        return False
