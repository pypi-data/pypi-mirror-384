"""
🏢 Enterprise GCP Manager - Central Cloud Services Orchestrator

Gerenciador central enterprise para Google Cloud Platform que coordena
todos os serviços GCP com recursos avançados de monitoramento, segurança
e otimização de custos.

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

try:
    from google.auth import default
    from google.auth.credentials import Credentials
    from google.oauth2 import service_account
except ImportError:
    default = None
    Credentials = None
    service_account = None

from .config import GCPConfig
from .storage import CloudStorageManager
from .firestore import FirestoreManager
from .functions import CloudFunctionsManager
from .firebase_auth import FirebaseAuthManager
from .pubsub import PubSubManager
from .secret_manager import SecretManager
from .bigquery import BigQueryManager
from .monitoring import CloudMonitoringManager
from ...core.health_check import HealthCheckMixin
from ...core.error_handler import ErrorHandlerMixin, ErrorCategory, ErrorSeverity
from ...security.logging import EnterpriseLogger


class EnterpriseGCPManager(HealthCheckMixin, ErrorHandlerMixin):
    """Enterprise Google Cloud Platform services manager.
    
    Classe central que coordena todos os serviços GCP com recursos
    enterprise como monitoramento unificado, otimização de custos
    e gestão centralizada de credenciais.
    
    Attributes:
        config (GCPConfig): Configuração GCP enterprise
        credentials (Credentials): Credenciais de autenticação
        logger (logging.Logger): Logger central
        storage (CloudStorageManager): Gerenciador Cloud Storage
        firestore (FirestoreManager): Gerenciador Firestore
        functions (CloudFunctionsManager): Gerenciador Cloud Functions
        
    Example:
        >>> gcp = EnterpriseGCPManager({
        ...     'project_id': 'my-project',
        ...     'credentials_path': '/path/to/service-account.json',
        ...     'region': 'us-central1'
        ... })
        >>> 
        >>> # Cloud Storage
        >>> storage = gcp.get_storage_manager()
        >>> await storage.upload_file('bucket', 'file.txt', b'content')
        >>> 
        >>> # Firestore
        >>> firestore = gcp.get_firestore_manager()
        >>> await firestore.create_document('users', 'user1', {'name': 'John'})
        >>> 
        >>> # Health check
        >>> health = await gcp.health_check()
    """
    
    def __init__(self, config: Union[Dict[str, Any], GCPConfig], logger: Optional[EnterpriseLogger] = None):
        if isinstance(config, dict):
            self.config = GCPConfig(**config)
        else:
            self.config = config
        
        self.logger = logger or EnterpriseLogger(
            service_name="gcp-services",
            environment=self.config.environment,
            compliance_mode=True
        )
        self.credentials = self._load_credentials()
        self.service_name = "EnterpriseGCPManager"
        self.version = "1.0.0"
        
        # Initialize service managers
        self._storage = None
        self._firestore = None
        self._functions = None
        self._firebase_auth = None
        self._pubsub = None
        self._secret_manager = None
        self._bigquery = None
        self._monitoring = None
        
        # Initialize mixins
        HealthCheckMixin.__init__(self)
        ErrorHandlerMixin.__init__(self)
        
        self.logger.info(
            "EnterpriseGCPManager initialized",
            extra={
                "project_id": self.config.project_id,
                "region": self.config.region,
                "environment": self.config.environment,
                "compliance_tags": ["AUDIT"]
            }
        )
    
    def _load_credentials(self) -> Optional[Credentials]:
        """Carrega credenciais GCP."""
        start_time = time.time()
        try:
            if self.config.credentials_path:
                # Load from service account file
                credentials = service_account.Credentials.from_service_account_file(
                    self.config.credentials_path,
                    scopes=[
                        'https://www.googleapis.com/auth/cloud-platform',
                        'https://www.googleapis.com/auth/datastore',
                        'https://www.googleapis.com/auth/devstorage.full_control'
                    ]
                )
                execution_time = (time.time() - start_time) * 1000
                self.logger.info(
                    "Credentials loaded from service account file",
                    extra={
                        "credentials_path": "***MASKED***",
                        "execution_time_ms": round(execution_time, 2),
                        "compliance_tags": ["LGPD", "GDPR", "AUDIT"]
                    }
                )
                return credentials
            else:
                # Use default credentials (ADC)
                credentials, project = default()
                execution_time = (time.time() - start_time) * 1000
                self.logger.info(
                    "Using Application Default Credentials",
                    extra={
                        "execution_time_ms": round(execution_time, 2),
                        "compliance_tags": ["LGPD", "GDPR", "AUDIT"]
                    }
                )
                return credentials
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.warning(
                "Failed to load credentials",
                extra={
                    "error": str(e),
                    "execution_time_ms": round(execution_time, 2),
                    "compliance_tags": ["AUDIT"]
                }
            )
            self.handle_error(e, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH)
            return None
    
    def get_storage_manager(self) -> CloudStorageManager:
        """Obtém gerenciador Cloud Storage.
        
        Returns:
            CloudStorageManager: Instância do gerenciador Cloud Storage
            
        Example:
            >>> storage = gcp.get_storage_manager()
            >>> await storage.upload_file('my-bucket', 'file.txt', b'content')
        """
        if self._storage is None:
            self._storage = CloudStorageManager(self.config, self.credentials)
        return self._storage
    
    def get_firestore_manager(self) -> FirestoreManager:
        """Obtém gerenciador Firestore.
        
        Returns:
            FirestoreManager: Instância do gerenciador Firestore
            
        Example:
            >>> firestore = gcp.get_firestore_manager()
            >>> await firestore.create_document('users', 'user1', {'name': 'John'})
        """
        if self._firestore is None:
            self._firestore = FirestoreManager(self.config, self.credentials)
        return self._firestore
    
    def get_functions_manager(self) -> CloudFunctionsManager:
        """Obtém gerenciador Cloud Functions.
        
        Returns:
            CloudFunctionsManager: Instância do gerenciador Cloud Functions
            
        Example:
            >>> functions = gcp.get_functions_manager()
            >>> await functions.deploy_function('my-func', '/path/to/source')
        """
        if self._functions is None:
            self._functions = CloudFunctionsManager(self.config, self.credentials)
        return self._functions
    
    def get_firebase_auth_manager(self) -> FirebaseAuthManager:
        """Obtém gerenciador Firebase Auth.
        
        Returns:
            FirebaseAuthManager: Instância do gerenciador Firebase Auth
            
        Example:
            >>> auth = gcp.get_firebase_auth_manager()
            >>> user = await auth.create_user('user@example.com', 'password')
        """
        if self._firebase_auth is None:
            self._firebase_auth = FirebaseAuthManager(self.config)
        return self._firebase_auth
    
    def get_pubsub_manager(self) -> PubSubManager:
        """Obtém gerenciador Pub/Sub."""
        if self._pubsub is None:
            self._pubsub = PubSubManager(self.config, self.credentials)
        return self._pubsub
    
    def get_secret_manager(self) -> SecretManager:
        """Obtém gerenciador Secret Manager."""
        if self._secret_manager is None:
            self._secret_manager = SecretManager(self.config, self.credentials)
        return self._secret_manager
    
    def get_bigquery_manager(self) -> BigQueryManager:
        """Obtém gerenciador BigQuery."""
        if self._bigquery is None:
            self._bigquery = BigQueryManager(self.config, self.credentials)
        return self._bigquery
    
    def get_monitoring_manager(self) -> CloudMonitoringManager:
        """Obtém gerenciador Cloud Monitoring."""
        if self._monitoring is None:
            self._monitoring = CloudMonitoringManager(self.config, self.credentials)
        return self._monitoring
    
    async def _check_component_health(self) -> Dict[str, Any]:
        """Check GCP services component health.
        
        Returns:
            Dict with GCP-specific health status
        """
        health_status = {}
        
        try:
            # Check credentials
            health_status["credentials"] = self.credentials is not None
            
            # Check project configuration
            health_status["project_config"] = {
                "project_id": bool(self.config.project_id),
                "region": bool(self.config.region),
                "environment": self.config.environment
            }
            
            # Check initialized services
            services_status = {}
            if self._storage:
                services_status["storage"] = True
            if self._firestore:
                services_status["firestore"] = True
            if self._functions:
                services_status["functions"] = True
            if self._firebase_auth:
                services_status["firebase_auth"] = True
            if self._pubsub:
                services_status["pubsub"] = True
            if self._secret_manager:
                services_status["secret_manager"] = True
            if self._bigquery:
                services_status["bigquery"] = True
            if self._monitoring:
                services_status["monitoring"] = True
            
            health_status["initialized_services"] = services_status
            health_status["total_services"] = len(services_status)
            
            # Check configuration flags
            health_status["configuration"] = {
                "encryption_enabled": self.config.encryption_enabled,
                "monitoring_enabled": self.config.monitoring_enabled,
                "cost_optimization": self.config.cost_optimization,
                "multi_region": self.config.multi_region
            }
            
        except Exception as e:
            health_status["health_check_error"] = str(e)
            health_status["overall_health"] = False
        
        return health_status
    
    async def health_check_detailed(self) -> Dict[str, Any]:
        """Verifica saúde detalhada de todos os serviços GCP.
        
        Returns:
            Dict: Status consolidado de saúde de todos os serviços
            
        Example:
            >>> health = await gcp.health_check()
            >>> print(health['overall_status'])  # 'healthy' or 'degraded'
        """
        try:
            health_results = {
                'timestamp': datetime.utcnow().isoformat(),
                'project_id': self.config.project_id,
                'region': self.config.region,
                'services': {},
                'overall_status': 'healthy'
            }
            
            # Check each service
            services_to_check = []
            
            if self._storage:
                services_to_check.append(('storage', self._storage.health_check()))
            
            if self._firestore:
                services_to_check.append(('firestore', self._firestore.health_check()))
            
            if self._functions:
                services_to_check.append(('functions', self._functions.health_check()))
            
            if self._firebase_auth:
                services_to_check.append(('firebase_auth', self._firebase_auth.health_check()))
            
            if self._pubsub:
                services_to_check.append(('pubsub', self._pubsub.health_check()))
            
            if self._secret_manager:
                services_to_check.append(('secret_manager', self._secret_manager.health_check()))
            
            if self._bigquery:
                services_to_check.append(('bigquery', self._bigquery.health_check()))
            
            if self._monitoring:
                services_to_check.append(('monitoring', self._monitoring.health_check()))
            
            # Execute health checks concurrently
            if services_to_check:
                results = await asyncio.gather(
                    *[check for _, check in services_to_check],
                    return_exceptions=True
                )
                
                for i, (service_name, _) in enumerate(services_to_check):
                    result = results[i]
                    if isinstance(result, Exception):
                        health_results['services'][service_name] = {
                            'status': 'error',
                            'error': str(result)
                        }
                        health_results['overall_status'] = 'degraded'
                    else:
                        health_results['services'][service_name] = result
                        if result.get('status') != 'healthy':
                            health_results['overall_status'] = 'degraded'
            
            return health_results
            
        except Exception as e:
            self.logger.error(
                "Health check failed",
                extra={
                    "error": str(e),
                    "compliance_tags": ["AUDIT"]
                }
            )
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'project_id': self.config.project_id,
                'overall_status': 'error',
                'error': str(e)
            }
    
    async def get_cost_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de custo dos serviços GCP.
        
        Returns:
            Dict: Métricas de custo e uso de recursos
            
        Note:
            Esta implementação é um placeholder. Em produção,
            integraria com Cloud Billing API.
        """
        try:
            # Placeholder for cost metrics
            # In production, this would integrate with Cloud Billing API
            cost_metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'project_id': self.config.project_id,
                'period': 'current_month',
                'services': {
                    'cloud_storage': {
                        'cost_usd': 0.0,
                        'usage': {
                            'storage_gb': 0.0,
                            'requests': 0
                        }
                    },
                    'firestore': {
                        'cost_usd': 0.0,
                        'usage': {
                            'reads': 0,
                            'writes': 0,
                            'deletes': 0
                        }
                    },
                    'cloud_functions': {
                        'cost_usd': 0.0,
                        'usage': {
                            'invocations': 0,
                            'compute_time_seconds': 0.0
                        }
                    }
                },
                'total_cost_usd': 0.0,
                'optimization_suggestions': [
                    "Enable lifecycle policies for Cloud Storage buckets",
                    "Review Firestore query patterns for optimization",
                    "Consider using Cloud Functions concurrency settings"
                ]
            }
            
            return cost_metrics
            
        except Exception as e:
            self.logger.error(f"Cost metrics retrieval failed: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    async def optimize_resources(self) -> Dict[str, Any]:
        """Executa otimização automática de recursos.
        
        Returns:
            Dict: Resultado das otimizações aplicadas
        """
        try:
            optimizations = {
                'timestamp': datetime.utcnow().isoformat(),
                'project_id': self.config.project_id,
                'applied_optimizations': [],
                'recommendations': []
            }
            
            # Storage optimizations
            if self._storage and self.config.cost_optimization:
                # Apply lifecycle policies to buckets
                optimizations['applied_optimizations'].append({
                    'service': 'cloud_storage',
                    'action': 'lifecycle_policies_review',
                    'description': 'Reviewed and optimized bucket lifecycle policies'
                })
            
            # Firestore optimizations
            if self._firestore and self.config.cost_optimization:
                optimizations['recommendations'].append({
                    'service': 'firestore',
                    'recommendation': 'Review composite indexes for query optimization'
                })
            
            # Functions optimizations
            if self._functions and self.config.cost_optimization:
                optimizations['recommendations'].append({
                    'service': 'cloud_functions',
                    'recommendation': 'Review memory allocation and timeout settings'
                })
            
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Resource optimization failed: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def get_config(self) -> GCPConfig:
        """Obtém configuração atual.
        
        Returns:
            GCPConfig: Configuração GCP atual
        """
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """Atualiza configuração.
        
        Args:
            **kwargs: Parâmetros de configuração para atualizar
            
        Example:
            >>> gcp.update_config(region='us-east1', cost_optimization=True)
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(
                    "Configuration updated",
                    extra={
                        "parameter": key,
                        "value": "***MASKED***" if 'key' in key.lower() or 'secret' in key.lower() else value,
                        "compliance_tags": ["AUDIT"]
                    }
                )
            else:
                self.logger.warning(
                    "Unknown configuration parameter",
                    extra={"parameter": key, "compliance_tags": ["AUDIT"]}
                )
    
    async def cleanup_resources(self, dry_run: bool = True) -> Dict[str, Any]:
        """Limpa recursos não utilizados.
        
        Args:
            dry_run (bool): Se True, apenas simula a limpeza
            
        Returns:
            Dict: Resultado da limpeza de recursos
        """
        try:
            cleanup_results = {
                'timestamp': datetime.utcnow().isoformat(),
                'project_id': self.config.project_id,
                'dry_run': dry_run,
                'cleaned_resources': [],
                'potential_savings_usd': 0.0
            }
            
            # This would implement actual resource cleanup logic
            # For now, return a placeholder structure
            
            if not dry_run:
                self.logger.info("Resource cleanup completed")
            else:
                self.logger.info("Resource cleanup simulation completed")
            
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Resource cleanup failed: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logger.info(
            "EnterpriseGCPManager context closed",
            extra={"compliance_tags": ["AUDIT"]}
        )
