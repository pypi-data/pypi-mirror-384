"""
🔐 Secrets Manager - DATAMETRIA AWS Services

Gerenciador Secrets Manager integrado ao SecurityManager DATAMETRIA.
"""

import json
import time
from typing import Dict, Any, Optional, Union
import boto3
import structlog
from botocore.exceptions import ClientError

from datametria_common.core.security import SecurityManager
from .config import AWSConfig
from .models import SecretResult

logger = structlog.get_logger(__name__)


class SecretsManager:
    """
    Gerenciador Secrets Manager DATAMETRIA.
    
    Integra gerenciamento de secrets com SecurityManager para dupla proteção.
    """
    
    def __init__(self, session: boto3.Session, config: AWSConfig, security_manager: SecurityManager):
        """
        Inicializa SecretsManager.
        
        Args:
            session: Sessão boto3
            config: Configuração AWS
            security_manager: SecurityManager DATAMETRIA
        """
        self.session = session
        self.config = config
        self.client = session.client('secretsmanager')
        self.security_manager = security_manager
        
        logger.info(
            "SecretsManager initialized",
            region=config.region,
            security_integration=True
        )
    
    async def create_secret(
        self, 
        name: str, 
        secret_value: Union[str, Dict[str, Any]], 
        description: Optional[str] = None,
        encrypt_locally: bool = True
    ) -> SecretResult:
        """
        Criar secret no AWS Secrets Manager.
        
        Args:
            name: Nome do secret
            secret_value: Valor do secret
            description: Descrição do secret
            encrypt_locally: Se deve criptografar localmente antes de enviar
            
        Returns:
            SecretResult: Resultado da operação
        """
        try:
            # Preparar valor do secret
            if isinstance(secret_value, dict):
                secret_string = json.dumps(secret_value)
            else:
                secret_string = str(secret_value)
            
            # Criptografia local adicional se solicitada
            if encrypt_locally:
                secret_string = self.security_manager.encrypt_data(secret_string)
                logger.info("Secret encrypted locally before AWS storage", name=name)
            
            # Preparar parâmetros
            params = {
                'Name': name,
                'SecretString': secret_string,
                'Description': description or f"Secret managed by DATAMETRIA - {name}"
            }
            
            # Adicionar KMS key se configurada
            if self.config.s3_kms_key_id:  # Reutilizar KMS key do S3
                params['KmsKeyId'] = self.config.s3_kms_key_id
            
            # Adicionar tags padrão
            if self.config.default_tags:
                tags = [
                    {'Key': k, 'Value': v} 
                    for k, v in self.config.default_tags.items()
                ]
                tags.append({'Key': 'DatametriaEncrypted', 'Value': str(encrypt_locally)})
                params['Tags'] = tags
            
            # Criar secret
            response = self.client.create_secret(**params)
            
            logger.info(
                "AWS Secret created successfully",
                name=name,
                arn=response['ARN'],
                version_id=response['VersionId'],
                locally_encrypted=encrypt_locally
            )
            
            return SecretResult(
                success=True,
                operation="create_secret",
                secret_arn=response['ARN'],
                version_id=response['VersionId'],
                metadata={
                    'name': name,
                    'locally_encrypted': encrypt_locally,
                    'kms_encrypted': bool(self.config.s3_kms_key_id)
                }
            )
            
        except ClientError as e:
            logger.error(
                "AWS Secrets Manager create_secret failed",
                name=name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return SecretResult(
                success=False,
                operation="create_secret",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    async def get_secret_value(
        self, 
        secret_name: str, 
        version_id: Optional[str] = None,
        decrypt_locally: bool = True
    ) -> SecretResult:
        """
        Obter valor do secret.
        
        Args:
            secret_name: Nome ou ARN do secret
            version_id: ID da versão específica
            decrypt_locally: Se deve descriptografar localmente
            
        Returns:
            SecretResult: Resultado com valor do secret
        """
        try:
            # Preparar parâmetros
            params = {'SecretId': secret_name}
            if version_id:
                params['VersionId'] = version_id
            
            # Obter secret
            response = self.client.get_secret_value(**params)
            
            secret_string = response['SecretString']
            
            # Descriptografia local se necessária
            if decrypt_locally:
                try:
                    decrypted_string = self.security_manager.decrypt_data(secret_string)
                    secret_string = decrypted_string
                    logger.info("Secret decrypted locally", name=secret_name)
                except Exception as e:
                    logger.warning(
                        "Local decryption failed, using raw value",
                        name=secret_name,
                        error=str(e)
                    )
            
            # Tentar parsear como JSON
            secret_value = secret_string
            try:
                secret_value = json.loads(secret_string)
            except json.JSONDecodeError:
                pass  # Manter como string se não for JSON válido
            
            logger.info(
                "AWS Secret retrieved successfully",
                name=secret_name,
                version_id=response.get('VersionId'),
                locally_decrypted=decrypt_locally
            )
            
            return SecretResult(
                success=True,
                operation="get_secret_value",
                secret_arn=response['ARN'],
                secret_value=secret_value,
                version_id=response.get('VersionId'),
                metadata={
                    'name': secret_name,
                    'locally_decrypted': decrypt_locally,
                    'creation_date': response.get('CreatedDate')
                }
            )
            
        except ClientError as e:
            logger.error(
                "AWS Secrets Manager get_secret_value failed",
                name=secret_name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return SecretResult(
                success=False,
                operation="get_secret_value",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    async def update_secret(
        self, 
        secret_name: str, 
        secret_value: Union[str, Dict[str, Any]],
        encrypt_locally: bool = True
    ) -> SecretResult:
        """
        Atualizar valor do secret.
        
        Args:
            secret_name: Nome ou ARN do secret
            secret_value: Novo valor do secret
            encrypt_locally: Se deve criptografar localmente
            
        Returns:
            SecretResult: Resultado da operação
        """
        try:
            # Preparar valor do secret
            if isinstance(secret_value, dict):
                secret_string = json.dumps(secret_value)
            else:
                secret_string = str(secret_value)
            
            # Criptografia local se solicitada
            if encrypt_locally:
                secret_string = self.security_manager.encrypt_data(secret_string)
            
            # Atualizar secret
            response = self.client.update_secret(
                SecretId=secret_name,
                SecretString=secret_string
            )
            
            logger.info(
                "AWS Secret updated successfully",
                name=secret_name,
                arn=response['ARN'],
                version_id=response['VersionId'],
                locally_encrypted=encrypt_locally
            )
            
            return SecretResult(
                success=True,
                operation="update_secret",
                secret_arn=response['ARN'],
                version_id=response['VersionId'],
                metadata={
                    'name': secret_name,
                    'locally_encrypted': encrypt_locally
                }
            )
            
        except ClientError as e:
            logger.error(
                "AWS Secrets Manager update_secret failed",
                name=secret_name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return SecretResult(
                success=False,
                operation="update_secret",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    def delete_secret(
        self, 
        secret_name: str, 
        force_delete: bool = False,
        recovery_window_days: int = 30
    ) -> bool:
        """
        Deletar secret.
        
        Args:
            secret_name: Nome ou ARN do secret
            force_delete: Se deve forçar deleção imediata
            recovery_window_days: Dias para recuperação
            
        Returns:
            bool: True se sucesso
        """
        try:
            params = {'SecretId': secret_name}
            
            if force_delete:
                params['ForceDeleteWithoutRecovery'] = True
            else:
                params['RecoveryWindowInDays'] = recovery_window_days
            
            response = self.client.delete_secret(**params)
            
            logger.info(
                "AWS Secret deleted",
                name=secret_name,
                arn=response['ARN'],
                force_delete=force_delete,
                recovery_window=recovery_window_days if not force_delete else 0
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete secret",
                name=secret_name,
                error=str(e)
            )
            return False
    
    def list_secrets(self, name_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar secrets.
        
        Args:
            name_prefix: Prefixo para filtrar secrets
            
        Returns:
            List: Lista de secrets
        """
        try:
            params = {}
            if name_prefix:
                params['Filters'] = [
                    {
                        'Key': 'name',
                        'Values': [name_prefix]
                    }
                ]
            
            response = self.client.list_secrets(**params)
            secrets = response.get('SecretList', [])
            
            logger.info(
                "AWS Secrets listed",
                count=len(secrets),
                name_prefix=name_prefix
            )
            
            return secrets
            
        except Exception as e:
            logger.error("Failed to list secrets", error=str(e))
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do Secrets Manager."""
        try:
            # Testar listagem de secrets
            self.client.list_secrets(MaxResults=1)
            
            return {
                'available': True,
                'security_integration': True,
                'kms_enabled': bool(self.config.s3_kms_key_id)
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do Secrets Manager."""
        try:
            secrets = self.list_secrets()
            
            return {
                'total_secrets': len(secrets),
                'security_integration': True,
                'kms_enabled': bool(self.config.s3_kms_key_id)
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
