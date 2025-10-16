"""
OAuth2 Authentication Manager - Google Workspace APIs

Gerenciamento de autenticação OAuth2 com armazenamento seguro de tokens,
refresh automático e integração com Vault Manager DATAMETRIA.
"""

import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from datametria_common.cloud.workspace.config import WorkspaceConfig
from datametria_common.core.security_mixin import SecurityMixin
from datametria_common.security.centralized_logger import CentralizedEnterpriseLogger


class WorkspaceOAuth2Manager(SecurityMixin):
    """Gerenciador de autenticação OAuth2 para Workspace APIs.
    
    Integra componentes DATAMETRIA:
    - SecurityMixin para criptografia de tokens
    - Enterprise Logging para audit trail
    - Vault Manager para armazenamento seguro (opcional)
    
    Example:
        >>> config = WorkspaceConfig.from_env()
        >>> oauth = WorkspaceOAuth2Manager(config, logger)
        >>> 
        >>> # Obter URL de autorização
        >>> auth_url = oauth.get_authorization_url()
        >>> 
        >>> # Trocar código por token
        >>> credentials = oauth.exchange_code(code)
        >>> 
        >>> # Obter credentials válidas
        >>> creds = oauth.get_credentials()
    """
    
    def __init__(
        self,
        config: WorkspaceConfig,
        logger: CentralizedEnterpriseLogger,
        use_vault: bool = False
    ):
        """Inicializar OAuth2 Manager.
        
        Args:
            config: Configuração do Workspace
            logger: Enterprise logger
            use_vault: Se True, usa Vault Manager para armazenar tokens
        """
        super().__init__()
        self.config = config
        self._logger = logger
        self.use_vault = use_vault
        
        self._credentials: Optional[Credentials] = None
        self._vault_manager = None
        
        if use_vault:
            try:
                from datametria_common.utilities.vault_manager import VaultManager
                self._vault_manager = VaultManager()
            except ImportError:
                self._logger.warning(
                    "Vault Manager not available, using file storage",
                    compliance_tags=["SECURITY", "WARNING"]
                )
                self.use_vault = False
        
        self._logger.info(
            "OAuth2Manager initialized",
            use_vault=self.use_vault,
            scopes_count=len(config.scopes),
            compliance_tags=["AUDIT", "INITIALIZATION"]
        )
    
    def get_authorization_url(self, redirect_uri: str = 'urn:ietf:wg:oauth:2.0:oob') -> str:
        """Obter URL de autorização OAuth2.
        
        Args:
            redirect_uri: URI de redirecionamento
            
        Returns:
            URL de autorização
            
        Example:
            >>> url = oauth.get_authorization_url()
            >>> print(f"Authorize at: {url}")
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            self.config.credentials_path,
            scopes=self.config.scopes,
            redirect_uri=redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        self._logger.info(
            "Authorization URL generated",
            redirect_uri=redirect_uri,
            compliance_tags=["AUDIT", "AUTHENTICATION"]
        )
        
        return auth_url
    
    def exchange_code(
        self,
        code: str,
        user_id: Optional[str] = None,
        redirect_uri: str = 'urn:ietf:wg:oauth:2.0:oob'
    ) -> Credentials:
        """Trocar código de autorização por token.
        
        Args:
            code: Código de autorização
            user_id: ID do usuário (para armazenamento)
            redirect_uri: URI de redirecionamento
            
        Returns:
            Credentials do Google
            
        Example:
            >>> creds = oauth.exchange_code('authorization_code')
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            self.config.credentials_path,
            scopes=self.config.scopes,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(code=code)
        self._credentials = flow.credentials
        
        # Armazenar token
        self._store_credentials(user_id)
        
        self._logger.info(
            "OAuth2 token exchanged",
            user_id=user_id or "default",
            has_refresh_token=bool(self._credentials.refresh_token),
            compliance_tags=["AUDIT", "AUTHENTICATION"]
        )
        
        return self._credentials
    
    def get_credentials(self, user_id: Optional[str] = None) -> Optional[Credentials]:
        """Obter credentials válidas (com refresh automático).
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Credentials válidas ou None
            
        Example:
            >>> creds = oauth.get_credentials()
            >>> if creds and creds.valid:
            ...     # Usar credentials
        """
        # Se já tem credentials em memória
        if self._credentials:
            if self._credentials.valid:
                return self._credentials
            
            # Tentar refresh
            if self._credentials.refresh_token:
                try:
                    self._credentials.refresh(Request())
                    self._store_credentials(user_id)
                    
                    self._logger.info(
                        "OAuth2 token refreshed",
                        user_id=user_id or "default",
                        compliance_tags=["AUDIT", "AUTHENTICATION"]
                    )
                    
                    return self._credentials
                except Exception as e:
                    self._logger.error(
                        "Failed to refresh token",
                        error=str(e),
                        user_id=user_id or "default",
                        compliance_tags=["ERROR", "AUTHENTICATION"]
                    )
        
        # Tentar carregar do storage
        self._credentials = self._load_credentials(user_id)
        
        if self._credentials:
            # Verificar validade e refresh se necessário
            if not self._credentials.valid and self._credentials.refresh_token:
                try:
                    self._credentials.refresh(Request())
                    self._store_credentials(user_id)
                except Exception as e:
                    self._logger.error(
                        "Failed to refresh loaded token",
                        error=str(e),
                        compliance_tags=["ERROR", "AUTHENTICATION"]
                    )
                    return None
        
        return self._credentials
    
    def revoke_credentials(self, user_id: Optional[str] = None) -> bool:
        """Revogar credentials.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se revogado com sucesso
        """
        if not self._credentials:
            self._credentials = self._load_credentials(user_id)
        
        if not self._credentials:
            return False
        
        try:
            self._credentials.revoke(Request())
            
            # Remover do storage
            self._delete_credentials(user_id)
            self._credentials = None
            
            self._logger.info(
                "OAuth2 credentials revoked",
                user_id=user_id or "default",
                compliance_tags=["AUDIT", "AUTHENTICATION", "REVOCATION"]
            )
            
            return True
            
        except Exception as e:
            self._logger.error(
                "Failed to revoke credentials",
                error=str(e),
                compliance_tags=["ERROR", "AUTHENTICATION"]
            )
            return False
    
    def _store_credentials(self, user_id: Optional[str] = None) -> None:
        """Armazenar credentials de forma segura."""
        if not self._credentials:
            return
        
        creds_data = {
            'token': self._credentials.token,
            'refresh_token': self._credentials.refresh_token,
            'token_uri': self._credentials.token_uri,
            'client_id': self._credentials.client_id,
            'client_secret': self._credentials.client_secret,
            'scopes': self._credentials.scopes,
            'expiry': self._credentials.expiry.isoformat() if self._credentials.expiry else None
        }
        
        if self.use_vault and self._vault_manager:
            # Armazenar no Vault
            try:
                path = f"workspace/oauth/{user_id or 'default'}"
                self._vault_manager.write_secret(
                    path=path,
                    data=creds_data,
                    metadata={
                        'user_id': user_id or 'default',
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                )
                
                self._logger.debug(
                    "Credentials stored in Vault",
                    user_id=user_id or "default"
                )
                
            except Exception as e:
                self._logger.error(
                    "Failed to store credentials in Vault",
                    error=str(e),
                    compliance_tags=["ERROR", "SECURITY"]
                )
                # Fallback para file storage
                self._store_credentials_file(creds_data, user_id)
        else:
            # Armazenar em arquivo
            self._store_credentials_file(creds_data, user_id)
    
    def _store_credentials_file(self, creds_data: dict, user_id: Optional[str] = None) -> None:
        """Armazenar credentials em arquivo (criptografado)."""
        token_path = Path(self.config.token_path)
        
        if user_id:
            token_path = token_path.parent / f"token_{user_id}.json"
        
        # Criptografar dados sensíveis
        if self.config.encryption_enabled:
            creds_data['token'] = self.encrypt_data(creds_data['token'])
            if creds_data['refresh_token']:
                creds_data['refresh_token'] = self.encrypt_data(creds_data['refresh_token'])
        
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(json.dumps(creds_data, indent=2))
        
        self._logger.debug(
            "Credentials stored in file",
            path=str(token_path),
            encrypted=self.config.encryption_enabled
        )
    
    def _load_credentials(self, user_id: Optional[str] = None) -> Optional[Credentials]:
        """Carregar credentials do storage."""
        if self.use_vault and self._vault_manager:
            try:
                path = f"workspace/oauth/{user_id or 'default'}"
                secret = self._vault_manager.read_secret(path)
                creds_data = secret['data']
                
                self._logger.debug(
                    "Credentials loaded from Vault",
                    user_id=user_id or "default"
                )
                
                return self._credentials_from_dict(creds_data)
                
            except Exception as e:
                self._logger.warning(
                    "Failed to load credentials from Vault",
                    error=str(e)
                )
        
        # Tentar carregar de arquivo
        return self._load_credentials_file(user_id)
    
    def _load_credentials_file(self, user_id: Optional[str] = None) -> Optional[Credentials]:
        """Carregar credentials de arquivo."""
        token_path = Path(self.config.token_path)
        
        if user_id:
            token_path = token_path.parent / f"token_{user_id}.json"
        
        if not token_path.exists():
            return None
        
        try:
            creds_data = json.loads(token_path.read_text())
            
            # Descriptografar se necessário
            if self.config.encryption_enabled:
                creds_data['token'] = self.decrypt_data(creds_data['token'])
                if creds_data['refresh_token']:
                    creds_data['refresh_token'] = self.decrypt_data(creds_data['refresh_token'])
            
            self._logger.debug(
                "Credentials loaded from file",
                path=str(token_path)
            )
            
            return self._credentials_from_dict(creds_data)
            
        except Exception as e:
            self._logger.error(
                "Failed to load credentials from file",
                error=str(e),
                path=str(token_path),
                compliance_tags=["ERROR", "SECURITY"]
            )
            return None
    
    def _credentials_from_dict(self, data: dict) -> Credentials:
        """Criar Credentials a partir de dicionário."""
        expiry = None
        if data.get('expiry'):
            expiry = datetime.fromisoformat(data['expiry'])
        
        return Credentials(
            token=data['token'],
            refresh_token=data.get('refresh_token'),
            token_uri=data['token_uri'],
            client_id=data['client_id'],
            client_secret=data['client_secret'],
            scopes=data['scopes'],
            expiry=expiry
        )
    
    def _delete_credentials(self, user_id: Optional[str] = None) -> None:
        """Deletar credentials do storage."""
        if self.use_vault and self._vault_manager:
            try:
                path = f"workspace/oauth/{user_id or 'default'}"
                self._vault_manager.delete_secret(path)
            except Exception:
                pass
        
        # Deletar arquivo
        token_path = Path(self.config.token_path)
        if user_id:
            token_path = token_path.parent / f"token_{user_id}.json"
        
        if token_path.exists():
            token_path.unlink()
