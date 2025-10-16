"""
WorkspaceConfig - Configuração para Google Workspace APIs

Configuração enterprise com validação automática, suporte a environment variables
e integração com BaseConfig DATAMETRIA.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from datametria_common.core.base_config import BaseConfig, ConfigValidationError


@dataclass
class WorkspaceConfig(BaseConfig):
    """Configuração para Google Workspace APIs.
    
    Herda de BaseConfig para garantir padrão DATAMETRIA com:
    - Validação automática
    - Suporte a environment variables
    - Security config integrado
    - Compliance mode
    
    Example:
        >>> config = WorkspaceConfig(
        ...     credentials_path='/path/to/credentials.json',
        ...     scopes=['https://www.googleapis.com/auth/gmail.modify']
        ... )
        >>> config.validate()
        
        >>> # Ou via environment variables
        >>> config = WorkspaceConfig.from_env(prefix='WORKSPACE_')
    """
    
    # Workspace-specific fields
    credentials_path: str = field(
        default_factory=lambda: os.getenv('WORKSPACE_CREDENTIALS_PATH', '')
    )
    token_path: str = field(
        default_factory=lambda: os.getenv('WORKSPACE_TOKEN_PATH', 'token.json')
    )
    scopes: List[str] = field(default_factory=list)
    
    # Service configuration
    service_account_email: Optional[str] = field(
        default_factory=lambda: os.getenv('WORKSPACE_SERVICE_ACCOUNT_EMAIL')
    )
    delegated_user_email: Optional[str] = field(
        default_factory=lambda: os.getenv('WORKSPACE_DELEGATED_USER_EMAIL')
    )
    
    # Rate limiting
    rate_limit_enabled: bool = field(
        default_factory=lambda: os.getenv('WORKSPACE_RATE_LIMIT', 'true').lower() == 'true'
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv('WORKSPACE_MAX_RETRIES', '3'))
    )
    retry_delay: float = field(
        default_factory=lambda: float(os.getenv('WORKSPACE_RETRY_DELAY', '1.0'))
    )
    
    # Cache configuration
    cache_enabled: bool = field(
        default_factory=lambda: os.getenv('WORKSPACE_CACHE_ENABLED', 'true').lower() == 'true'
    )
    cache_ttl: int = field(
        default_factory=lambda: int(os.getenv('WORKSPACE_CACHE_TTL', '300'))
    )
    cache_backend: str = field(
        default_factory=lambda: os.getenv('WORKSPACE_CACHE_BACKEND', 'memory')
    )
    cache_max_size: int = field(
        default_factory=lambda: int(os.getenv('WORKSPACE_CACHE_MAX_SIZE', '1000'))
    )
    cache_compression: bool = field(
        default_factory=lambda: os.getenv('WORKSPACE_CACHE_COMPRESSION', 'false').lower() == 'true'
    )
    redis_url: Optional[str] = field(
        default_factory=lambda: os.getenv('WORKSPACE_REDIS_URL')
    )
    
    # Compliance
    compliance_mode: bool = field(
        default_factory=lambda: os.getenv('WORKSPACE_COMPLIANCE', 'true').lower() == 'true'
    )
    data_masking_enabled: bool = field(
        default_factory=lambda: os.getenv('WORKSPACE_DATA_MASKING', 'true').lower() == 'true'
    )
    audit_enabled: bool = field(
        default_factory=lambda: os.getenv('WORKSPACE_AUDIT', 'true').lower() == 'true'
    )
    
    # Performance
    timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv('WORKSPACE_TIMEOUT', '30'))
    )
    max_concurrent_requests: int = field(
        default_factory=lambda: int(os.getenv('WORKSPACE_MAX_CONCURRENT', '10'))
    )
    
    def _validate_specific(self) -> None:
        """Validação específica do Workspace.
        
        Raises:
            ConfigValidationError: Se configuração inválida
        """
        # Validar credentials_path
        if not self.credentials_path:
            raise ConfigValidationError("credentials_path is required")
        
        credentials_file = Path(self.credentials_path)
        if not credentials_file.exists():
            raise ConfigValidationError(
                f"credentials file not found: {self.credentials_path}"
            )
        
        if not credentials_file.is_file():
            raise ConfigValidationError(
                f"credentials_path must be a file: {self.credentials_path}"
            )
        
        # Validar scopes
        if not self.scopes:
            raise ConfigValidationError("at least one scope is required")
        
        # Validar scopes format
        for scope in self.scopes:
            if not scope.startswith('https://www.googleapis.com/auth/'):
                raise ConfigValidationError(
                    f"invalid scope format: {scope}. "
                    "Must start with 'https://www.googleapis.com/auth/'"
                )
        
        # Validar retry configuration
        if self.max_retries < 0:
            raise ConfigValidationError("max_retries must be >= 0")
        
        if self.retry_delay < 0:
            raise ConfigValidationError("retry_delay must be >= 0")
        
        # Validar cache configuration
        if self.cache_ttl < 0:
            raise ConfigValidationError("cache_ttl must be >= 0")
        
        if self.cache_backend not in ['memory', 'redis', 'file']:
            raise ConfigValidationError("cache_backend must be 'memory', 'redis', or 'file'")
        
        if self.cache_max_size <= 0:
            raise ConfigValidationError("cache_max_size must be > 0")
        
        if self.cache_backend == 'redis' and not self.redis_url:
            raise ConfigValidationError("redis_url required when cache_backend is 'redis'")
        
        # Validar timeout
        if self.timeout_seconds <= 0:
            raise ConfigValidationError("timeout_seconds must be > 0")
        
        # Validar concurrent requests
        if self.max_concurrent_requests <= 0:
            raise ConfigValidationError("max_concurrent_requests must be > 0")
    
    @classmethod
    def from_env(cls, prefix: str = 'WORKSPACE_') -> 'WorkspaceConfig':
        """Criar configuração a partir de environment variables.
        
        Args:
            prefix: Prefixo das variáveis de ambiente
            
        Returns:
            WorkspaceConfig configurado
            
        Example:
            >>> # Com variáveis de ambiente:
            >>> # WORKSPACE_CREDENTIALS_PATH=/path/to/creds.json
            >>> # WORKSPACE_SCOPES=gmail,drive
            >>> config = WorkspaceConfig.from_env()
        """
        config_dict = {}
        
        # Processar scopes especialmente (pode ser string separada por vírgula)
        scopes_env = os.getenv(f'{prefix}SCOPES', '')
        if scopes_env:
            # Mapear nomes curtos para URLs completas
            scope_mapping = {
                'gmail': 'https://www.googleapis.com/auth/gmail.modify',
                'gmail.readonly': 'https://www.googleapis.com/auth/gmail.readonly',
                'drive': 'https://www.googleapis.com/auth/drive',
                'drive.readonly': 'https://www.googleapis.com/auth/drive.readonly',
                'calendar': 'https://www.googleapis.com/auth/calendar',
                'calendar.readonly': 'https://www.googleapis.com/auth/calendar.readonly',
                'chat': 'https://www.googleapis.com/auth/chat.bot',
                'meet': 'https://www.googleapis.com/auth/meetings.space.created',
                'tasks': 'https://www.googleapis.com/auth/tasks',
                'vault': 'https://www.googleapis.com/auth/ediscovery'
            }
            
            scopes = []
            for scope in scopes_env.split(','):
                scope = scope.strip()
                # Se for nome curto, mapear para URL completa
                if scope in scope_mapping:
                    scopes.append(scope_mapping[scope])
                else:
                    scopes.append(scope)
            
            config_dict['scopes'] = scopes
        
        # Usar método pai para processar outras variáveis
        base_config = super().from_env(prefix)
        
        # Mesclar configurações
        for key, value in base_config.__dict__.items():
            if key not in config_dict and not key.startswith('_'):
                config_dict[key] = value
        
        return cls(**config_dict)
    
    def get_api_scopes(self, api_name: str) -> List[str]:
        """Obter scopes específicos de uma API.
        
        Args:
            api_name: Nome da API (gmail, drive, calendar, etc)
            
        Returns:
            Lista de scopes da API
        """
        api_patterns = {
            'gmail': 'gmail',
            'drive': 'drive',
            'calendar': 'calendar',
            'chat': 'chat',
            'meet': 'meetings',
            'tasks': 'tasks',
            'vault': 'ediscovery'
        }
        
        pattern = api_patterns.get(api_name.lower())
        if not pattern:
            return []
        
        return [s for s in self.scopes if pattern in s]
    
    def has_api_access(self, api_name: str) -> bool:
        """Verificar se tem acesso a uma API específica.
        
        Args:
            api_name: Nome da API
            
        Returns:
            True se tem scopes para a API
        """
        return len(self.get_api_scopes(api_name)) > 0
    
    def to_dict(self) -> dict:
        """Converter para dicionário (override para incluir campos específicos)."""
        base_dict = super().to_dict()
        base_dict.update({
            'credentials_path': self.credentials_path,
            'token_path': self.token_path,
            'scopes': self.scopes,
            'rate_limit_enabled': self.rate_limit_enabled,
            'cache_enabled': self.cache_enabled,
            'cache_backend': self.cache_backend,
            'cache_max_size': self.cache_max_size,
            'compliance_mode': self.compliance_mode
        })
        return base_dict
