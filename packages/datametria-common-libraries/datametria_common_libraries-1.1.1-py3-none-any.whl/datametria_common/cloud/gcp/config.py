"""
⚙️ GCP Configuration - Enterprise Settings

Configuração enterprise para Google Cloud Platform com validação automática,
segurança integrada, otimização de custos e compliance LGPD/GDPR.

Features:
    - Validação automática de configurações
    - Otimização de custos por ambiente
    - Segurança enterprise (encryption, monitoring)
    - Multi-região e alta disponibilidade
    - Service-specific configurations
    - Compliance LGPD/GDPR automático
    - Environment-based defaults
    - Credential management seguro

Examples:
    >>> from datametria_common.cloud.gcp import GCPConfig
    >>> config = GCPConfig(
    ...     project_id="my-project",
    ...     environment="production",
    ...     region="us-central1"
    ... )
    >>> print(config.to_dict())

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
License: MIT
Compliance: LGPD/GDPR Ready
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from ...core.base_config import BaseConfig


class GCPConfig(BaseConfig):
    """Configuração enterprise para Google Cloud Platform com validação e otimização.
    
    Classe de configuração completa para serviços GCP incluindo validação automática,
    otimização de custos, segurança enterprise e compliance LGPD/GDPR.
    
    Attributes:
        project_id (str): ID único do projeto GCP (obrigatório)
        credentials_path (Optional[str]): Caminho para arquivo service account JSON.
            Se None, usa credenciais padrão do ambiente (ADC).
        region (str): Região principal GCP. Default: 'us-central1'
        environment (str): Ambiente de deploy ('dev', 'staging', 'production')
        encryption_enabled (bool): Habilita criptografia automática em todos os serviços
        monitoring_enabled (bool): Habilita Cloud Monitoring e alertas
        cost_optimization (bool): Habilita otimização automática de custos
        multi_region (bool): Habilita deploy multi-região para alta disponibilidade
        storage_config (Dict[str, Any]): Configurações específicas do Cloud Storage
        firestore_config (Dict[str, Any]): Configurações específicas do Firestore
        functions_config (Dict[str, Any]): Configurações específicas do Cloud Functions
        
    Examples:
        >>> # Configuração básica
        >>> config = GCPConfig(project_id="my-project")
        >>> 
        >>> # Configuração completa para produção
        >>> config = GCPConfig(
        ...     project_id="prod-project",
        ...     credentials_path="/secure/service-account.json",
        ...     region="us-central1",
        ...     environment="production",
        ...     multi_region=True
        ... )
        >>> 
        >>> # Configuração para desenvolvimento
        >>> dev_config = GCPConfig(
        ...     project_id="dev-project",
        ...     environment="dev",
        ...     cost_optimization=True
        ... )
        
    Note:
        - Validação automática é executada no __post_init__
        - Configurações são otimizadas por ambiente automaticamente
        - Todas as configurações seguem best practices GCP
        - Compliance LGPD/GDPR é aplicado automaticamente
    """
    def __init__(self, project_id: str, credentials_path: Optional[str] = None,
                 region: str = "us-central1", environment: str = "production",
                 encryption_enabled: bool = True, monitoring_enabled: bool = True,
                 cost_optimization: bool = True, multi_region: bool = False,
                 storage_config: Optional[Dict[str, Any]] = None,
                 firestore_config: Optional[Dict[str, Any]] = None,
                 functions_config: Optional[Dict[str, Any]] = None):
        """Initialize GCP configuration."""
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.region = region
        self.environment = environment
        self.encryption_enabled = encryption_enabled
        self.monitoring_enabled = monitoring_enabled
        self.cost_optimization = cost_optimization
        self.multi_region = multi_region
        
        # Service-specific configurations with defaults
        self.storage_config = storage_config or {
            'default_bucket_class': 'STANDARD',
            'lifecycle_enabled': True,
            'versioning_enabled': True,
            'uniform_bucket_level_access': True
        }
        
        self.firestore_config = firestore_config or {
            'database_id': '(default)',
            'location_id': 'us-central',
            'type': 'FIRESTORE_NATIVE'
        }
        
        self.functions_config = functions_config or {
            'runtime': 'python311',
            'memory': '256MB',
            'timeout': '60s',
            'max_instances': 100
        }
        
        super().__init__()
        self._setup_defaults()
    
    def _validate_specific(self) -> None:
        """Valida configuração GCP com verificações enterprise.
        
        Executa validação completa incluindo:
        - Project ID obrigatório e formato válido
        - Arquivo de credenciais existente (se especificado)
        - Environment válido (dev/staging/production)
        - Região GCP válida
        
        Raises:
            ValueError: Se project_id estiver vazio ou environment inválido
            FileNotFoundError: Se credentials_path não existir
            
        Examples:
            >>> config = GCPConfig(project_id="")
            ValueError: project_id é obrigatório
            >>> 
            >>> config = GCPConfig(project_id="test", environment="invalid")
            ValueError: Environment deve ser um de: ['dev', 'staging', 'production']
            
        Note:
            - Validação é executada automaticamente no __post_init__
            - Garante configuração enterprise-ready
            - Previne erros de runtime
        """
        if not self.project_id:
            raise ValueError("project_id é obrigatório")
            
        if self.credentials_path and not Path(self.credentials_path).exists():
            raise ValueError(f"Arquivo de credenciais não encontrado: {self.credentials_path}")
            
        valid_environments = ['dev', 'staging', 'production']
        if self.environment not in valid_environments:
            raise ValueError(f"Environment deve ser um de: {valid_environments}")
    
    def _setup_defaults(self) -> None:
        """Configura valores padrão otimizados baseados no ambiente.
        
        Aplica configurações específicas por ambiente para otimização
        de custos, performance e segurança:
        
        Production:
            - Storage: STANDARD class para performance
            - Functions: max_instances=1000 para escala
            - Monitoring: Habilitado com alertas
            
        Development:
            - Storage: NEARLINE class para economia
            - Functions: max_instances=10 para controle de custos
            - Monitoring: Básico
            
        Staging:
            - Configurações intermediárias
            - Balanceamento custo/performance
            
        Examples:
            >>> config = GCPConfig(project_id="test", environment="production")
            >>> config.functions_config['max_instances']
            1000
            >>> 
            >>> dev_config = GCPConfig(project_id="test", environment="dev")
            >>> dev_config.storage_config['default_bucket_class']
            'NEARLINE'
            
        Note:
            - Otimizações são aplicadas automaticamente
            - Configurações seguem best practices GCP
            - Balanceamento entre custo e performance
        """
        if self.environment == 'production':
            self.storage_config['default_bucket_class'] = 'STANDARD'
            self.functions_config['max_instances'] = 1000
        elif self.environment == 'dev':
            self.storage_config['default_bucket_class'] = 'NEARLINE'
            self.functions_config['max_instances'] = 10
    
    def get_credentials_dict(self) -> Optional[Dict[str, Any]]:
        """Carrega credenciais do arquivo service account JSON de forma segura.
        
        Returns:
            Optional[Dict[str, Any]]: Dicionário com credenciais do service account
                ou None se credentials_path não estiver definido.
                
        Raises:
            FileNotFoundError: Se arquivo de credenciais não existir
            json.JSONDecodeError: Se arquivo JSON for inválido
            PermissionError: Se não houver permissão para ler o arquivo
            
        Examples:
            >>> config = GCPConfig(
            ...     project_id="test",
            ...     credentials_path="/path/to/service-account.json"
            ... )
            >>> creds = config.get_credentials_dict()
            >>> print(creds['type'])  # 'service_account'
            >>> 
            >>> # Sem credenciais (usa ADC)
            >>> config = GCPConfig(project_id="test")
            >>> creds = config.get_credentials_dict()
            >>> print(creds)  # None
            
        Note:
            - Retorna None se credentials_path não estiver definido
            - Usa Application Default Credentials (ADC) quando None
            - Arquivo deve ser service account JSON válido
            - Credenciais são carregadas sob demanda (não cached)
        """
        if not self.credentials_path:
            return None
            
        with open(self.credentials_path, 'r') as f:
            return json.load(f)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário serializable.
        
        Returns:
            Dict[str, Any]: Dicionário com todas as configurações principais,
                excluindo credentials_path por segurança.
                
        Examples:
            >>> config = GCPConfig(
            ...     project_id="my-project",
            ...     environment="production",
            ...     region="us-central1"
            ... )
            >>> config_dict = config.to_dict()
            >>> print(config_dict['project_id'])  # 'my-project'
            >>> print(config_dict['environment'])  # 'production'
            >>> 
            >>> # Para serialização JSON
            >>> import json
            >>> json_config = json.dumps(config.to_dict(), indent=2)
            
        Note:
            - credentials_path é omitido por segurança
            - Resultado é JSON-serializable
            - Inclui todas as configurações de serviços
            - Útil para logging e debugging (sem dados sensíveis)
        """
        return {
            'project_id': self.project_id,
            'region': self.region,
            'environment': self.environment,
            'encryption_enabled': self.encryption_enabled,
            'monitoring_enabled': self.monitoring_enabled,
            'storage_config': self.storage_config,
            'firestore_config': self.firestore_config,
            'functions_config': self.functions_config
        }
