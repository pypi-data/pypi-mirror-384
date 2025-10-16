"""
🔐 Secret Manager - Enterprise Credential Management

Gerenciador enterprise para Google Cloud Secret Manager com recursos avançados:
- Secret creation, retrieval e rotation
- Version management e access control
- Encryption at rest e in transit
- Audit logging e compliance
- Integration com IAM e security policies

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

try:
    from google.cloud import secretmanager
    from google.auth.credentials import Credentials
except ImportError:
    secretmanager = None
    Credentials = None

from .config import GCPConfig


class SecretManager:
    """Enterprise Google Cloud Secret Manager."""
    
    def __init__(self, config: GCPConfig, credentials: Optional[Credentials] = None):
        if secretmanager is None:
            raise ImportError("google-cloud-secret-manager não instalado. Execute: pip install google-cloud-secret-manager")
            
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Secret Manager client
        if credentials:
            self.client = secretmanager.SecretManagerServiceClient(credentials=credentials)
        else:
            self.client = secretmanager.SecretManagerServiceClient()
    
    async def create_secret(
        self,
        secret_id: str,
        data: Union[str, bytes],
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """Cria secret no Secret Manager."""
        try:
            parent = f"projects/{self.config.project_id}"
            
            # Create secret
            secret = {
                "replication": {"automatic": {}},
                "labels": labels or {}
            }
            
            response = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": secret
                }
            )
            
            # Add secret version with data
            if isinstance(data, str):
                payload_data = data.encode('utf-8')
            else:
                payload_data = data
            
            version_response = self.client.add_secret_version(
                request={
                    "parent": response.name,
                    "payload": {"data": payload_data}
                }
            )
            
            self.logger.info(f"Secret created: {secret_id}")
            return version_response.name
            
        except Exception as e:
            self.logger.error(f"Secret creation failed: {e}")
            raise
    
    async def get_secret(
        self,
        secret_id: str,
        version: str = "latest"
    ) -> str:
        """Obtém secret do Secret Manager."""
        try:
            name = f"projects/{self.config.project_id}/secrets/{secret_id}/versions/{version}"
            
            response = self.client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode('utf-8')
            
            self.logger.info(f"Secret retrieved: {secret_id}")
            return payload
            
        except Exception as e:
            self.logger.error(f"Secret retrieval failed: {e}")
            raise
    
    async def update_secret(
        self,
        secret_id: str,
        data: Union[str, bytes]
    ) -> str:
        """Atualiza secret (cria nova versão)."""
        try:
            parent = f"projects/{self.config.project_id}/secrets/{secret_id}"
            
            if isinstance(data, str):
                payload_data = data.encode('utf-8')
            else:
                payload_data = data
            
            response = self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": payload_data}
                }
            )
            
            self.logger.info(f"Secret updated: {secret_id}")
            return response.name
            
        except Exception as e:
            self.logger.error(f"Secret update failed: {e}")
            raise
    
    async def delete_secret(self, secret_id: str) -> bool:
        """Deleta secret do Secret Manager."""
        try:
            name = f"projects/{self.config.project_id}/secrets/{secret_id}"
            
            self.client.delete_secret(request={"name": name})
            
            self.logger.info(f"Secret deleted: {secret_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Secret deletion failed: {e}")
            raise
    
    async def list_secrets(self) -> List[Dict[str, Any]]:
        """Lista todos os secrets."""
        try:
            parent = f"projects/{self.config.project_id}"
            
            secrets = []
            for secret in self.client.list_secrets(request={"parent": parent}):
                secrets.append({
                    'name': secret.name.split('/')[-1],
                    'full_name': secret.name,
                    'create_time': secret.create_time.isoformat() if secret.create_time else None,
                    'labels': dict(secret.labels) if secret.labels else {}
                })
            
            return secrets
            
        except Exception as e:
            self.logger.error(f"List secrets failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do Secret Manager."""
        try:
            # Test by listing secrets
            secrets = await self.list_secrets()
            
            return {
                'status': 'healthy',
                'service': 'secret_manager',
                'project_id': self.config.project_id,
                'timestamp': datetime.utcnow().isoformat(),
                'secrets_count': len(secrets)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'secret_manager',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
