"""
🗄️ S3 Manager - DATAMETRIA AWS Services

Gerenciador S3 integrado aos componentes DATAMETRIA.
"""

import os
import time
from typing import Dict, Any, Optional, Callable
import boto3
import structlog
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig

from datametria_common.core.security import SecurityManager
from .config import AWSConfig
from .models import S3UploadResult, S3DownloadResult

logger = structlog.get_logger(__name__)


class S3Manager:
    """
    Gerenciador S3 DATAMETRIA.
    
    Integra object storage com security manager e logging.
    """
    
    def __init__(self, session: boto3.Session, config: AWSConfig):
        """
        Inicializa S3Manager.
        
        Args:
            session: Sessão boto3
            config: Configuração AWS
        """
        self.session = session
        self.config = config
        self.client = session.client('s3')
        self.resource = session.resource('s3')
        self.security_manager = SecurityManager()
        
        # Configuração de transfer otimizada
        self.transfer_config = TransferConfig(
            multipart_threshold=1024 * 25,  # 25MB
            max_concurrency=10,
            multipart_chunksize=1024 * 25,
            use_threads=True
        )
        
        logger.info(
            "S3Manager initialized",
            region=config.region,
            default_bucket=config.s3_default_bucket,
            storage_class=config.s3_storage_class
        )
    
    async def upload_file(
        self, 
        file_path: str, 
        key: str, 
        bucket: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable] = None,
        encrypt: bool = True
    ) -> S3UploadResult:
        """
        Upload de arquivo para S3.
        
        Args:
            file_path: Caminho do arquivo local
            key: Chave S3
            bucket: Bucket S3 (usa padrão se None)
            metadata: Metadados do arquivo
            progress_callback: Callback de progresso
            encrypt: Se deve criptografar o arquivo
            
        Returns:
            S3UploadResult: Resultado do upload
        """
        start_time = time.time()
        bucket_name = bucket or self.config.s3_default_bucket
        
        try:
            # Verificar se arquivo existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            
            # Preparar extra args
            extra_args = {
                'StorageClass': self.config.s3_storage_class,
                'Metadata': metadata or {}
            }
            
            # Adicionar criptografia se configurada
            if encrypt and self.config.s3_kms_key_id:
                extra_args.update({
                    'ServerSideEncryption': 'aws:kms',
                    'SSEKMSKeyId': self.config.s3_kms_key_id
                })
            
            # Adicionar tags padrão
            tags = "&".join([f"{k}={v}" for k, v in self.config.default_tags.items()])
            if tags:
                extra_args['Tagging'] = tags
            
            # Upload do arquivo
            self.client.upload_file(
                file_path,
                bucket_name,
                key,
                ExtraArgs=extra_args,
                Config=self.transfer_config,
                Callback=progress_callback
            )
            
            upload_time = time.time() - start_time
            
            # Obter ETag
            etag = self._get_object_etag(bucket_name, key)
            
            logger.info(
                "S3 file uploaded successfully",
                bucket=bucket_name,
                key=key,
                file_size=file_size,
                upload_time=upload_time,
                etag=etag
            )
            
            return S3UploadResult(
                success=True,
                bucket=bucket_name,
                key=key,
                file_size=file_size,
                upload_time=upload_time,
                etag=etag,
                metadata={
                    'storage_class': self.config.s3_storage_class,
                    'encrypted': encrypt and bool(self.config.s3_kms_key_id)
                }
            )
            
        except ClientError as e:
            logger.error(
                "S3 upload failed",
                bucket=bucket_name,
                key=key,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return S3UploadResult(
                success=False,
                bucket=bucket_name,
                key=key,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
        except Exception as e:
            logger.error(
                "S3 upload failed with unexpected error",
                bucket=bucket_name,
                key=key,
                error=str(e)
            )
            
            return S3UploadResult(
                success=False,
                bucket=bucket_name,
                key=key,
                error=str(e)
            )
    
    async def download_file(
        self, 
        key: str, 
        file_path: str, 
        bucket: Optional[str] = None
    ) -> S3DownloadResult:
        """
        Download de arquivo do S3.
        
        Args:
            key: Chave S3
            file_path: Caminho do arquivo local
            bucket: Bucket S3 (usa padrão se None)
            
        Returns:
            S3DownloadResult: Resultado do download
        """
        start_time = time.time()
        bucket_name = bucket or self.config.s3_default_bucket
        
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Download do arquivo
            self.client.download_file(
                bucket_name,
                key,
                file_path,
                Config=self.transfer_config
            )
            
            download_time = time.time() - start_time
            file_size = os.path.getsize(file_path)
            
            logger.info(
                "S3 file downloaded successfully",
                bucket=bucket_name,
                key=key,
                file_path=file_path,
                file_size=file_size,
                download_time=download_time
            )
            
            return S3DownloadResult(
                success=True,
                bucket=bucket_name,
                key=key,
                file_path=file_path,
                file_size=file_size,
                download_time=download_time
            )
            
        except ClientError as e:
            logger.error(
                "S3 download failed",
                bucket=bucket_name,
                key=key,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return S3DownloadResult(
                success=False,
                bucket=bucket_name,
                key=key,
                file_path=file_path,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    def _get_object_etag(self, bucket: str, key: str) -> Optional[str]:
        """Obter ETag do objeto S3."""
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return response.get('ETag', '').strip('"')
        except Exception:
            return None
    
    def generate_presigned_url(
        self, 
        key: str, 
        bucket: Optional[str] = None,
        expiration: int = 3600,
        method: str = 'get_object'
    ) -> Optional[str]:
        """
        Gerar URL pré-assinada.
        
        Args:
            key: Chave S3
            bucket: Bucket S3
            expiration: Tempo de expiração em segundos
            method: Método HTTP
            
        Returns:
            str: URL pré-assinada ou None
        """
        try:
            bucket_name = bucket or self.config.s3_default_bucket
            
            url = self.client.generate_presigned_url(
                method,
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            
            logger.info(
                "S3 presigned URL generated",
                bucket=bucket_name,
                key=key,
                expiration=expiration,
                method=method
            )
            
            return url
            
        except Exception as e:
            logger.error(
                "Failed to generate presigned URL",
                bucket=bucket_name,
                key=key,
                error=str(e)
            )
            return None
    
    def delete_object(self, key: str, bucket: Optional[str] = None) -> bool:
        """
        Deletar objeto S3.
        
        Args:
            key: Chave S3
            bucket: Bucket S3
            
        Returns:
            bool: True se sucesso
        """
        try:
            bucket_name = bucket or self.config.s3_default_bucket
            
            self.client.delete_object(Bucket=bucket_name, Key=key)
            
            logger.info(
                "S3 object deleted",
                bucket=bucket_name,
                key=key
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete S3 object",
                bucket=bucket_name,
                key=key,
                error=str(e)
            )
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do S3."""
        try:
            # Testar acesso ao bucket padrão
            self.client.head_bucket(Bucket=self.config.s3_default_bucket)
            
            return {
                'available': True,
                'default_bucket': self.config.s3_default_bucket,
                'storage_class': self.config.s3_storage_class,
                'kms_enabled': bool(self.config.s3_kms_key_id)
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do S3."""
        try:
            return {
                'default_bucket': self.config.s3_default_bucket,
                'storage_class': self.config.s3_storage_class,
                'kms_key_id': self.config.s3_kms_key_id,
                'multipart_threshold': self.transfer_config.multipart_threshold,
                'max_concurrency': self.transfer_config.max_concurrency
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
