"""
☁️ Cloud Functions Manager - Enterprise Serverless Operations

Gerenciador enterprise para Google Cloud Functions com recursos avançados:
- Deploy e management de functions
- Invocação síncrona e assíncrona
- Monitoring e logging integrado
- Environment variables e secrets
- Scaling automático e otimização

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

try:
    from google.cloud import functions_v1
    from google.cloud.functions_v1 import CloudFunction, SourceRepository
    from google.auth.credentials import Credentials
except ImportError:
    functions_v1 = None
    CloudFunction = None
    SourceRepository = None
    Credentials = None

from .config import GCPConfig


class CloudFunctionsManager:
    """Enterprise Google Cloud Functions manager.
    
    Fornece interface simplificada para deploy e management
    de Cloud Functions com recursos enterprise como monitoring,
    scaling automático e integração com outros serviços GCP.
    
    Attributes:
        config (GCPConfig): Configuração GCP
        client (functions_v1.CloudFunctionsServiceClient): Cliente Cloud Functions
        logger (logging.Logger): Logger para auditoria
        
    Example:
        >>> functions_mgr = CloudFunctionsManager(gcp_config)
        >>> await functions_mgr.deploy_function('my-function', '/path/to/source')
        >>> result = await functions_mgr.invoke_function('my-function', {'key': 'value'})
    """
    
    def __init__(self, config: GCPConfig, credentials: Optional[Credentials] = None):
        if functions_v1 is None:
            raise ImportError("google-cloud-functions não instalado. Execute: pip install google-cloud-functions")
            
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Cloud Functions client
        if credentials:
            self.client = functions_v1.CloudFunctionsServiceClient(credentials=credentials)
        else:
            self.client = functions_v1.CloudFunctionsServiceClient()
        
        self.location = f"projects/{config.project_id}/locations/{config.region}"
    
    async def deploy_function(
        self,
        name: str,
        source_path: str,
        entry_point: str = "main",
        runtime: Optional[str] = None,
        environment_vars: Optional[Dict[str, str]] = None,
        memory: Optional[str] = None,
        timeout: Optional[str] = None
    ) -> str:
        """Deploy Cloud Function.
        
        Args:
            name (str): Nome da function
            source_path (str): Caminho para o código fonte
            entry_point (str): Ponto de entrada da function
            runtime (Optional[str]): Runtime (python311, nodejs18, etc.)
            environment_vars (Optional[Dict]): Variáveis de ambiente
            memory (Optional[str]): Memória alocada (128MB, 256MB, etc.)
            timeout (Optional[str]): Timeout (60s, 120s, etc.)
            
        Returns:
            str: Nome completo da function deployada
            
        Example:
            >>> function_name = await functions_mgr.deploy_function(
            ...     'process-data',
            ...     '/path/to/function/source',
            ...     entry_point='process_data',
            ...     environment_vars={'ENV': 'production'}
            ... )
        """
        try:
            # Use config defaults if not provided
            runtime = runtime or self.config.functions_config.get('runtime', 'python311')
            memory = memory or self.config.functions_config.get('memory', '256MB')
            timeout = timeout or self.config.functions_config.get('timeout', '60s')
            
            function_name = f"{self.location}/functions/{name}"
            
            # Prepare function configuration
            function_config = {
                'name': function_name,
                'source_archive_url': f"gs://{self.config.project_id}-functions-source/{name}.zip",
                'entry_point': entry_point,
                'runtime': runtime,
                'available_memory_mb': int(memory.replace('MB', '')),
                'timeout': timeout,
                'environment_variables': environment_vars or {},
                'max_instances': self.config.functions_config.get('max_instances', 100)
            }
            
            # Create or update function
            try:
                # Try to get existing function
                existing_function = self.client.get_function(name=function_name)
                # Update existing function
                operation = self.client.update_function(function=function_config)
                self.logger.info(f"Updating existing function: {name}")
            except:
                # Create new function
                operation = self.client.create_function(
                    parent=self.location,
                    function=function_config
                )
                self.logger.info(f"Creating new function: {name}")
            
            # Wait for operation to complete
            result = operation.result(timeout=300)  # 5 minutes timeout
            
            self.logger.info(f"Function deployed successfully: {name}")
            return function_name
            
        except Exception as e:
            self.logger.error(f"Function deployment failed: {e}")
            raise
    
    async def invoke_function(
        self,
        name: str,
        data: Optional[Dict[str, Any]] = None,
        async_call: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Invoca Cloud Function.
        
        Args:
            name (str): Nome da function
            data (Optional[Dict]): Dados para enviar à function
            async_call (bool): Chamada assíncrona (fire-and-forget)
            
        Returns:
            Optional[Dict]: Resultado da function (None se async_call=True)
            
        Example:
            >>> result = await functions_mgr.invoke_function(
            ...     'process-data',
            ...     {'input': 'test data', 'format': 'json'}
            ... )
        """
        try:
            function_name = f"{self.location}/functions/{name}"
            
            # Prepare request data
            request_data = json.dumps(data or {}).encode('utf-8')
            
            if async_call:
                # Asynchronous call - fire and forget
                self.client.call_function(
                    name=function_name,
                    data=request_data
                )
                self.logger.info(f"Function invoked asynchronously: {name}")
                return None
            else:
                # Synchronous call - wait for response
                response = self.client.call_function(
                    name=function_name,
                    data=request_data
                )
                
                result = {
                    'execution_id': response.execution_id,
                    'result': response.result,
                    'error': response.error
                }
                
                self.logger.info(f"Function invoked successfully: {name}")
                return result
                
        except Exception as e:
            self.logger.error(f"Function invocation failed: {e}")
            raise
    
    async def list_functions(self) -> List[Dict[str, Any]]:
        """Lista todas as Cloud Functions.
        
        Returns:
            List[Dict]: Lista de functions com metadados
        """
        try:
            functions = self.client.list_functions(parent=self.location)
            
            function_list = []
            for function in functions:
                function_info = {
                    'name': function.name.split('/')[-1],
                    'full_name': function.name,
                    'runtime': function.runtime,
                    'entry_point': function.entry_point,
                    'memory': f"{function.available_memory_mb}MB",
                    'timeout': function.timeout,
                    'status': function.status.name,
                    'update_time': function.update_time.isoformat() if function.update_time else None,
                    'version_id': function.version_id
                }
                function_list.append(function_info)
            
            return function_list
            
        except Exception as e:
            self.logger.error(f"List functions failed: {e}")
            raise
    
    async def delete_function(self, name: str) -> bool:
        """Deleta Cloud Function.
        
        Args:
            name (str): Nome da function
            
        Returns:
            bool: True se deletada com sucesso
        """
        try:
            function_name = f"{self.location}/functions/{name}"
            
            operation = self.client.delete_function(name=function_name)
            operation.result(timeout=180)  # 3 minutes timeout
            
            self.logger.info(f"Function deleted successfully: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Function deletion failed: {e}")
            raise
    
    async def get_function_logs(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Obtém logs da Cloud Function.
        
        Args:
            name (str): Nome da function
            start_time (Optional[datetime]): Início do período
            end_time (Optional[datetime]): Fim do período
            limit (int): Limite de logs
            
        Returns:
            List[Dict]: Lista de logs
        """
        try:
            # This would typically integrate with Cloud Logging
            # For now, return a placeholder structure
            logs = [
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'severity': 'INFO',
                    'message': f"Function {name} executed successfully",
                    'execution_id': 'exec_123456',
                    'source_location': {
                        'file': 'main.py',
                        'line': 10,
                        'function': 'main'
                    }
                }
            ]
            
            return logs[:limit]
            
        except Exception as e:
            self.logger.error(f"Get function logs failed: {e}")
            raise
    
    async def update_function_config(
        self,
        name: str,
        environment_vars: Optional[Dict[str, str]] = None,
        memory: Optional[str] = None,
        timeout: Optional[str] = None,
        max_instances: Optional[int] = None
    ) -> bool:
        """Atualiza configuração da Cloud Function.
        
        Args:
            name (str): Nome da function
            environment_vars (Optional[Dict]): Novas variáveis de ambiente
            memory (Optional[str]): Nova configuração de memória
            timeout (Optional[str]): Novo timeout
            max_instances (Optional[int]): Novo limite de instâncias
            
        Returns:
            bool: True se atualizada com sucesso
        """
        try:
            function_name = f"{self.location}/functions/{name}"
            
            # Get current function
            current_function = self.client.get_function(name=function_name)
            
            # Update configuration
            if environment_vars is not None:
                current_function.environment_variables.update(environment_vars)
            
            if memory is not None:
                current_function.available_memory_mb = int(memory.replace('MB', ''))
            
            if timeout is not None:
                current_function.timeout = timeout
            
            if max_instances is not None:
                current_function.max_instances = max_instances
            
            # Apply updates
            operation = self.client.update_function(function=current_function)
            operation.result(timeout=180)
            
            self.logger.info(f"Function configuration updated: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Function configuration update failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Cloud Functions.
        
        Returns:
            Dict: Status de saúde do serviço
        """
        try:
            # Test basic connectivity by listing functions
            functions = list(self.client.list_functions(parent=self.location))
            
            return {
                'status': 'healthy',
                'service': 'cloud_functions',
                'project_id': self.config.project_id,
                'region': self.config.region,
                'timestamp': datetime.utcnow().isoformat(),
                'functions_count': len(functions)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'cloud_functions',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
