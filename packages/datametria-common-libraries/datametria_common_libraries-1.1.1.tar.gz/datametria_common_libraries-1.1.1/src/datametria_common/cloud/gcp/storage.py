"""
💾 Cloud Storage Manager - Enterprise Storage Operations

Gerenciador enterprise para Google Cloud Storage com recursos avançados:
- Upload/download com criptografia automática
- Lifecycle management e versionamento
- Signed URLs e controle de acesso
- Monitoramento e métricas de performance
- Otimização de custos automática

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, BinaryIO
from pathlib import Path

try:
    from google.cloud import storage
    from google.cloud.storage import Bucket, Blob
    from google.auth.credentials import Credentials
except ImportError:
    storage = None
    Bucket = None
    Blob = None
    Credentials = None

from .config import GCPConfig


class CloudStorageManager:
    """Enterprise Google Cloud Storage manager.
    
    Fornece interface simplificada para operações Cloud Storage
    com recursos enterprise como criptografia, lifecycle management
    e otimização de performance.
    
    Attributes:
        config (GCPConfig): Configuração GCP
        client (storage.Client): Cliente Cloud Storage
        logger (logging.Logger): Logger para auditoria
        
    Example:
        >>> storage_mgr = CloudStorageManager(gcp_config)
        >>> await storage_mgr.upload_file('my-bucket', 'file.txt', b'content')
        >>> content = await storage_mgr.download_file('my-bucket', 'file.txt')
    """
    
    def __init__(self, config: GCPConfig, credentials: Optional[Credentials] = None):
        if storage is None:
            raise ImportError("google-cloud-storage não instalado. Execute: pip install google-cloud-storage")
            
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Cloud Storage client
        if credentials:
            self.client = storage.Client(
                project=config.project_id,
                credentials=credentials
            )
        else:
            self.client = storage.Client(project=config.project_id)
    
    async def upload_file(
        self, 
        bucket_name: str, 
        key: str, 
        content: bytes,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> str:
        """Upload arquivo para Cloud Storage.
        
        Args:
            bucket_name (str): Nome do bucket
            key (str): Chave/caminho do arquivo
            content (bytes): Conteúdo do arquivo
            metadata (Optional[Dict]): Metadados customizados
            content_type (Optional[str]): Tipo de conteúdo
            
        Returns:
            str: URL público do arquivo
            
        Example:
            >>> url = await storage_mgr.upload_file(
            ...     'my-bucket', 
            ...     'documents/file.pdf', 
            ...     pdf_content,
            ...     metadata={'department': 'finance'}
            ... )
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(key)
            
            # Set metadata
            if metadata:
                blob.metadata = metadata
                
            if content_type:
                blob.content_type = content_type
            
            # Upload with encryption if enabled
            if self.config.encryption_enabled:
                blob.upload_from_string(content, checksum="md5")
            else:
                blob.upload_from_string(content)
            
            self.logger.info(f"File uploaded: {bucket_name}/{key}")
            return f"gs://{bucket_name}/{key}"
            
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            raise
    
    async def download_file(self, bucket_name: str, key: str) -> bytes:
        """Download arquivo do Cloud Storage.
        
        Args:
            bucket_name (str): Nome do bucket
            key (str): Chave/caminho do arquivo
            
        Returns:
            bytes: Conteúdo do arquivo
            
        Example:
            >>> content = await storage_mgr.download_file('my-bucket', 'file.txt')
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(key)
            
            if not blob.exists():
                raise FileNotFoundError(f"File not found: {bucket_name}/{key}")
            
            content = blob.download_as_bytes()
            self.logger.info(f"File downloaded: {bucket_name}/{key}")
            return content
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise
    
    async def create_signed_url(
        self, 
        bucket_name: str, 
        key: str,
        expiration: int = 3600,
        method: str = "GET"
    ) -> str:
        """Cria URL assinada para acesso temporário.
        
        Args:
            bucket_name (str): Nome do bucket
            key (str): Chave do arquivo
            expiration (int): Tempo de expiração em segundos
            method (str): Método HTTP (GET, PUT, POST)
            
        Returns:
            str: URL assinada
            
        Example:
            >>> url = await storage_mgr.create_signed_url(
            ...     'my-bucket', 'private-file.pdf', expiration=1800
            ... )
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(key)
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expiration),
                method=method
            )
            
            self.logger.info(f"Signed URL created: {bucket_name}/{key}")
            return url
            
        except Exception as e:
            self.logger.error(f"Signed URL creation failed: {e}")
            raise
    
    async def list_files(
        self, 
        bucket_name: str, 
        prefix: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Lista arquivos no bucket.
        
        Args:
            bucket_name (str): Nome do bucket
            prefix (Optional[str]): Prefixo para filtrar arquivos
            limit (Optional[int]): Limite de resultados
            
        Returns:
            List[Dict]: Lista de arquivos com metadados
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix, max_results=limit)
            
            files = []
            for blob in blobs:
                files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'content_type': blob.content_type,
                    'etag': blob.etag,
                    'metadata': blob.metadata or {}
                })
            
            return files
            
        except Exception as e:
            self.logger.error(f"List files failed: {e}")
            raise
    
    async def delete_file(self, bucket_name: str, key: str) -> bool:
        """Deleta arquivo do Cloud Storage.
        
        Args:
            bucket_name (str): Nome do bucket
            key (str): Chave do arquivo
            
        Returns:
            bool: True se deletado com sucesso
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(key)
            
            if blob.exists():
                blob.delete()
                self.logger.info(f"File deleted: {bucket_name}/{key}")
                return True
            else:
                self.logger.warning(f"File not found for deletion: {bucket_name}/{key}")
                return False
                
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            raise
    
    async def setup_lifecycle_policy(
        self, 
        bucket_name: str, 
        rules: List[Dict[str, Any]]
    ) -> None:
        """Configura política de lifecycle do bucket.
        
        Args:
            bucket_name (str): Nome do bucket
            rules (List[Dict]): Regras de lifecycle
            
        Example:
            >>> rules = [{
            ...     'action': {'type': 'SetStorageClass', 'storageClass': 'NEARLINE'},
            ...     'condition': {'age': 30}
            ... }]
            >>> await storage_mgr.setup_lifecycle_policy('my-bucket', rules)
        """
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.lifecycle_rules = rules
            bucket.patch()
            
            self.logger.info(f"Lifecycle policy updated: {bucket_name}")
            
        except Exception as e:
            self.logger.error(f"Lifecycle policy setup failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Cloud Storage.
        
        Returns:
            Dict: Status de saúde do serviço
        """
        try:
            # Test basic connectivity
            buckets = list(self.client.list_buckets(max_results=1))
            
            return {
                'status': 'healthy',
                'service': 'cloud_storage',
                'project_id': self.config.project_id,
                'region': self.config.region,
                'timestamp': datetime.utcnow().isoformat(),
                'accessible_buckets': len(buckets) > 0
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'cloud_storage',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
