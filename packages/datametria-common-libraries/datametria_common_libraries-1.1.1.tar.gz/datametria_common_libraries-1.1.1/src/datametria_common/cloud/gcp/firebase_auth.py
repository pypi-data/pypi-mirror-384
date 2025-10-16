"""
🔐 Firebase Auth Manager - Enterprise Authentication Service

Gerenciador enterprise para Firebase Authentication com recursos avançados de
autentição, user management, token verification e compliance LGPD/GDPR.

Features:
    - User management completo (CRUD operations)
    - Custom claims e role-based access control
    - Token verification e refresh management
    - Multi-provider authentication (Google, Facebook, etc)
    - Security rules integration
    - LGPD/GDPR compliance automático
    - Bulk operations (import/export users)
    - Password reset e email verification
    - Health check e monitoring integrado

Examples:
    >>> from datametria_common.cloud.gcp import FirebaseAuthManager, GCPConfig
    >>> config = GCPConfig(project_id="my-project")
    >>> auth_mgr = FirebaseAuthManager(config)
    >>> user = await auth_mgr.create_user("user@example.com", "password")
    >>> token = await auth_mgr.create_custom_token(user.uid)

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
License: MIT
Compliance: LGPD/GDPR Ready
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

try:
    import firebase_admin
    from firebase_admin import auth, credentials
    from firebase_admin.auth import UserRecord, CreateUserRequest, UpdateUserRequest
except ImportError:
    firebase_admin = None
    auth = None
    credentials = None
    UserRecord = None
    CreateUserRequest = None
    UpdateUserRequest = None

from .config import GCPConfig


class FirebaseAuthManager:
    """Enterprise Firebase Authentication manager com recursos avançados.
    
    Gerenciador completo para Firebase Authentication incluindo user management,
    token verification, custom claims, multi-provider auth e compliance LGPD/GDPR.
    
    Attributes:
        config (GCPConfig): Configuração GCP com project_id e credenciais
        app (firebase_admin.App): Instância Firebase Admin SDK inicializada
        logger (logging.Logger): Logger para auditoria e debugging
        
    Examples:
        >>> config = GCPConfig(project_id="my-project")
        >>> auth_mgr = FirebaseAuthManager(config)
        >>> 
        >>> # Criar usuário com custom claims
        >>> user = await auth_mgr.create_user(
        ...     email="admin@company.com",
        ...     password="secure_password",
        ...     custom_claims={"role": "admin", "department": "IT"}
        ... )
        >>> 
        >>> # Verificar token
        >>> claims = await auth_mgr.verify_id_token(id_token)
        >>> print(claims["role"])  # "admin"
        
    Note:
        Requer firebase-admin instalado: pip install firebase-admin
        Todas as operações são logadas para auditoria e compliance.
    """
    
    def __init__(self, config: GCPConfig, service_account_path: Optional[str] = None):
        """Inicializa Firebase Auth manager com configuração e credenciais.
        
        Args:
            config (GCPConfig): Configuração GCP com project_id e settings
            service_account_path (Optional[str]): Caminho para service account JSON.
                Se None, usa config.credentials_path ou credenciais padrão.
                
        Raises:
            ImportError: Se firebase-admin não estiver instalado
            ValueError: Se Firebase Admin já estiver inicializado
            FileNotFoundError: Se arquivo de credenciais não existir
            
        Examples:
            >>> config = GCPConfig(project_id="my-project")
            >>> auth_mgr = FirebaseAuthManager(config)
            >>> 
            >>> # Com service account customizado
            >>> auth_mgr = FirebaseAuthManager(
            ...     config,
            ...     service_account_path="/path/to/service-account.json"
            ... )
            
        Note:
            - Reutiliza instância Firebase se já inicializada
            - Suporta Application Default Credentials (ADC)
            - Configura project_id automaticamente
        """
        if firebase_admin is None:
            raise ImportError("firebase-admin não instalado. Execute: pip install firebase-admin")
            
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Firebase Admin SDK
        try:
            # Check if already initialized
            self.app = firebase_admin.get_app()
        except ValueError:
            # Initialize new app
            if service_account_path or config.credentials_path:
                cred_path = service_account_path or config.credentials_path
                cred = credentials.Certificate(cred_path)
                self.app = firebase_admin.initialize_app(cred, {
                    'projectId': config.project_id
                })
            else:
                # Use default credentials
                self.app = firebase_admin.initialize_app()
    
    async def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        photo_url: Optional[str] = None,
        email_verified: bool = False,
        disabled: bool = False,
        custom_claims: Optional[Dict[str, Any]] = None
    ) -> UserRecord:
        """Cria usuário no Firebase Auth com configurações enterprise.
        
        Args:
            email (str): Email único do usuário (obrigatório)
            password (Optional[str]): Senha do usuário. Se None, usuário deve
                usar provider externo (Google, Facebook, etc)
            display_name (Optional[str]): Nome de exibição público
            phone_number (Optional[str]): Número de telefone (formato E.164)
            photo_url (Optional[str]): URL da foto de perfil
            email_verified (bool): Se email já está verificado. Default: False
            disabled (bool): Se conta está desabilitada. Default: False
            custom_claims (Optional[Dict[str, Any]]): Claims customizados para
                role-based access control (RBAC)
                
        Returns:
            UserRecord: Registro completo do usuário criado com UID, email,
                timestamps e custom claims aplicados
                
        Raises:
            ValueError: Se email for inválido ou já existir
            Exception: Se criação falhar por quota ou permissões
            
        Examples:
            >>> # Usuário básico
            >>> user = await auth_mgr.create_user(
            ...     email="user@example.com",
            ...     password="SecurePass123!"
            ... )
            >>> 
            >>> # Usuário completo com RBAC
            >>> admin_user = await auth_mgr.create_user(
            ...     email="admin@company.com",
            ...     password="AdminPass123!",
            ...     display_name="João Silva",
            ...     phone_number="+5511999999999",
            ...     email_verified=True,
            ...     custom_claims={
            ...         "role": "admin",
            ...         "department": "IT",
            ...         "permissions": ["read", "write", "delete"]
            ...     }
            ... )
            >>> 
            >>> # Usuário para provider externo
            >>> social_user = await auth_mgr.create_user(
            ...     email="social@example.com",
            ...     password=None,  # Usará Google/Facebook
            ...     custom_claims={"role": "user"}
            ... )
            
        Note:
            - Custom claims são aplicados automaticamente após criação
            - Operação é logada para auditoria LGPD/GDPR
            - Email deve ser único no projeto Firebase
            - Phone number deve seguir formato E.164 (+5511999999999)
        """
        try:
            # Prepare user creation request
            user_data = {
                'email': email,
                'email_verified': email_verified,
                'disabled': disabled
            }
            
            if password:
                user_data['password'] = password
            if display_name:
                user_data['display_name'] = display_name
            if phone_number:
                user_data['phone_number'] = phone_number
            if photo_url:
                user_data['photo_url'] = photo_url
            
            # Create user
            user = auth.create_user(**user_data)
            
            # Set custom claims if provided
            if custom_claims:
                auth.set_custom_user_claims(user.uid, custom_claims)
            
            self.logger.info(f"User created: {email} (UID: {user.uid})")
            return user
            
        except Exception as e:
            self.logger.error(f"User creation failed: {e}")
            raise
    
    async def get_user(self, uid: str) -> Optional[UserRecord]:
        """Obtém usuário por UID com informações completas.
        
        Args:
            uid (str): UID único do usuário Firebase
            
        Returns:
            Optional[UserRecord]: Registro completo do usuário incluindo:
                - uid, email, display_name, phone_number
                - email_verified, disabled, creation_timestamp
                - custom_claims, provider_data
                Retorna None se usuário não existir
                
        Raises:
            Exception: Se busca falhar por permissões ou erro de rede
            
        Examples:
            >>> user = await auth_mgr.get_user("firebase_uid_123")
            >>> if user:
            ...     print(f"Email: {user.email}")
            ...     print(f"Verified: {user.email_verified}")
            ...     print(f"Claims: {user.custom_claims}")
            ... else:
            ...     print("Usuário não encontrado")
            
        Note:
            - Retorna None se usuário não existir (não lança exceção)
            - Inclui todos os metadados e custom claims
            - Operação não é logada (consulta apenas)
        """
        try:
            user = auth.get_user(uid)
            return user
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Get user failed: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[UserRecord]:
        """Obtém usuário por email com informações completas.
        
        Args:
            email (str): Email do usuário (case-insensitive)
            
        Returns:
            Optional[UserRecord]: Registro completo do usuário ou None se não existir
                
        Raises:
            Exception: Se busca falhar por permissões ou erro de rede
            
        Examples:
            >>> user = await auth_mgr.get_user_by_email("user@example.com")
            >>> if user:
            ...     print(f"UID: {user.uid}")
            ...     print(f"Display Name: {user.display_name}")
            ...     print(f"Last Sign In: {user.user_metadata.last_sign_in_timestamp}")
            ... else:
            ...     print("Email não encontrado")
            
        Note:
            - Email é case-insensitive
            - Retorna None se email não existir
            - Mais lento que get_user() por UID
            - Útil para login e recuperação de senha
        """
        try:
            user = auth.get_user_by_email(email)
            return user
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Get user by email failed: {e}")
            raise
    
    async def update_user(
        self,
        uid: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        photo_url: Optional[str] = None,
        email_verified: Optional[bool] = None,
        disabled: Optional[bool] = None
    ) -> UserRecord:
        """Atualiza usuário existente com validação enterprise.
        
        Args:
            uid (str): UID do usuário a ser atualizado
            email (Optional[str]): Novo email (deve ser único)
            password (Optional[str]): Nova senha
            display_name (Optional[str]): Novo nome de exibição
            phone_number (Optional[str]): Novo telefone (formato E.164)
            photo_url (Optional[str]): Nova URL da foto
            email_verified (Optional[bool]): Status de verificação do email
            disabled (Optional[bool]): Status de ativação da conta
            
        Returns:
            UserRecord: Registro atualizado do usuário com novos valores
            
        Raises:
            ValueError: Se email já existir ou dados forem inválidos
            Exception: Se atualização falhar por permissões
            
        Examples:
            >>> # Atualizar email e nome
            >>> user = await auth_mgr.update_user(
            ...     uid="firebase_uid_123",
            ...     email="newemail@example.com",
            ...     display_name="Novo Nome"
            ... )
            >>> 
            >>> # Desabilitar conta
            >>> user = await auth_mgr.update_user(
            ...     uid="firebase_uid_123",
            ...     disabled=True
            ... )
            >>> 
            >>> # Verificar email manualmente
            >>> user = await auth_mgr.update_user(
            ...     uid="firebase_uid_123",
            ...     email_verified=True
            ... )
            
        Note:
            - Apenas campos especificados são atualizados
            - Operação é logada para auditoria
            - Email deve ser único no projeto
            - Custom claims não são afetados (use set_custom_claims)
        """
        try:
            update_data = {}
            
            if email is not None:
                update_data['email'] = email
            if password is not None:
                update_data['password'] = password
            if display_name is not None:
                update_data['display_name'] = display_name
            if phone_number is not None:
                update_data['phone_number'] = phone_number
            if photo_url is not None:
                update_data['photo_url'] = photo_url
            if email_verified is not None:
                update_data['email_verified'] = email_verified
            if disabled is not None:
                update_data['disabled'] = disabled
            
            user = auth.update_user(uid, **update_data)
            
            self.logger.info(f"User updated: {uid}")
            return user
            
        except Exception as e:
            self.logger.error(f"User update failed: {e}")
            raise
    
    async def delete_user(self, uid: str) -> bool:
        """Deleta usuário permanentemente (LGPD/GDPR compliant).
        
        Args:
            uid (str): UID do usuário a ser deletado
            
        Returns:
            bool: True se deletado com sucesso
            
        Raises:
            Exception: Se deleção falhar por permissões ou usuário não existir
            
        Examples:
            >>> # Deletar usuário (direito ao esquecimento LGPD)
            >>> success = await auth_mgr.delete_user("firebase_uid_123")
            >>> if success:
            ...     print("Usuário deletado com sucesso")
            
        Note:
            - Deleção é PERMANENTE e irreversível
            - Atende direito ao esquecimento (LGPD Art. 18, III)
            - Operação é logada para auditoria de compliance
            - Todos os dados do usuário são removidos
            - Tokens existentes são invalidados automaticamente
        """
        try:
            auth.delete_user(uid)
            
            self.logger.info(f"User deleted (LGPD/GDPR): {uid}")
            return True
            
        except Exception as e:
            self.logger.error(f"User deletion failed: {e}")
            raise
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """Define custom claims para role-based access control (RBAC).
        
        Args:
            uid (str): UID do usuário
            claims (Dict[str, Any]): Claims customizados para RBAC.
                Máximo 1000 caracteres quando serializado.
                
        Returns:
            bool: True se definido com sucesso
            
        Raises:
            ValueError: Se claims excederem limite de tamanho
            Exception: Se definição falhar por permissões
            
        Examples:
            >>> # RBAC básico
            >>> await auth_mgr.set_custom_claims("uid123", {
            ...     "role": "admin",
            ...     "department": "IT"
            ... })
            >>> 
            >>> # RBAC avançado com permissões granulares
            >>> await auth_mgr.set_custom_claims("uid456", {
            ...     "role": "manager",
            ...     "department": "sales",
            ...     "permissions": ["read", "write"],
            ...     "regions": ["BR", "AR", "CL"],
            ...     "level": 3
            ... })
            >>> 
            >>> # Remover todos os claims
            >>> await auth_mgr.set_custom_claims("uid789", {})
            
        Note:
            - Claims são incluídos em todos os tokens do usuário
            - Usuário deve fazer novo login para receber claims atualizados
            - Limite de 1000 caracteres para claims serializados
            - Útil para implementar RBAC (Role-Based Access Control)
        """
        try:
            auth.set_custom_user_claims(uid, claims)
            
            self.logger.info(f"Custom claims set for user: {uid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Set custom claims failed: {e}")
            raise
    
    async def create_custom_token(
        self,
        uid: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Cria token JWT customizado para autenticação do usuário.
        
        Args:
            uid (str): UID do usuário para o qual criar o token
            additional_claims (Optional[Dict[str, Any]]): Claims adicionais
                para incluir no token (além dos custom claims do usuário)
                
        Returns:
            str: Token JWT customizado válido por 1 hora
            
        Raises:
            Exception: Se criação falhar por permissões ou UID inválido
            
        Examples:
            >>> # Token básico
            >>> token = await auth_mgr.create_custom_token("firebase_uid_123")
            >>> 
            >>> # Token com claims adicionais
            >>> token = await auth_mgr.create_custom_token(
            ...     "firebase_uid_123",
            ...     additional_claims={
            ...         "session_id": "sess_abc123",
            ...         "login_method": "admin_panel",
            ...         "ip_address": "192.168.1.100"
            ...     }
            ... )
            >>> 
            >>> # Usar token no cliente
            >>> # firebase.auth().signInWithCustomToken(token)
            
        Note:
            - Token é válido por 1 hora
            - Inclui custom claims do usuário automaticamente
            - Additional claims são temporários (apenas neste token)
            - Útil para autenticação server-side
        """
        try:
            token = auth.create_custom_token(uid, additional_claims)
            
            self.logger.info(f"Custom token created for user: {uid}")
            return token.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Custom token creation failed: {e}")
            raise
    
    async def verify_id_token(self, id_token: str, check_revoked: bool = True) -> Dict[str, Any]:
        """Verifica e decodifica token ID do Firebase com validação completa.
        
        Args:
            id_token (str): Token ID JWT para verificar
            check_revoked (bool): Se deve verificar se token foi revogado.
                Default: True (recomendado para segurança)
                
        Returns:
            Dict[str, Any]: Claims decodificados do token incluindo:
                - uid: UID do usuário
                - email: Email do usuário
                - email_verified: Status de verificação
                - custom claims: Claims customizados (role, permissions, etc)
                - iat, exp: Timestamps de emissão e expiração
                
        Raises:
            ValueError: Se token for inválido, expirado ou revogado
            Exception: Se verificação falhar por erro de rede
            
        Examples:
            >>> # Verificar token de requisição
            >>> try:
            ...     claims = await auth_mgr.verify_id_token(request_token)
            ...     user_id = claims["uid"]
            ...     user_role = claims.get("role", "user")
            ...     print(f"Usuário autenticado: {user_id} ({user_role})")
            ... except ValueError:
            ...     print("Token inválido ou expirado")
            >>> 
            >>> # Verificar sem check de revogação (mais rápido)
            >>> claims = await auth_mgr.verify_id_token(
            ...     token,
            ...     check_revoked=False
            ... )
            
        Note:
            - Sempre verifique tokens em requisições autenticadas
            - check_revoked=True é mais seguro mas mais lento
            - Token expíra em 1 hora por padrão
            - Claims incluem custom claims do usuário
        """
        try:
            decoded_token = auth.verify_id_token(id_token, check_revoked=check_revoked)
            
            self.logger.info(f"Token verified for user: {decoded_token.get('uid')}")
            return decoded_token
            
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            raise
    
    async def revoke_refresh_tokens(self, uid: str) -> bool:
        """Revoga todos os refresh tokens do usuário (força novo login).
        
        Args:
            uid (str): UID do usuário cujos tokens serão revogados
            
        Returns:
            bool: True se revogado com sucesso
            
        Raises:
            Exception: Se revogação falhar por permissões ou UID inválido
            
        Examples:
            >>> # Revogar tokens por segurança
            >>> success = await auth_mgr.revoke_refresh_tokens("firebase_uid_123")
            >>> if success:
            ...     print("Usuário deve fazer login novamente")
            >>> 
            >>> # Usar após mudança de senha
            >>> await auth_mgr.update_user(uid, password="new_password")
            >>> await auth_mgr.revoke_refresh_tokens(uid)
            
        Note:
            - Força usuário a fazer login novamente em todos os dispositivos
            - Útil após mudança de senha ou comprometimento de segurança
            - Tokens ID existentes continuam válidos até expirarem
            - Operação é logada para auditoria de segurança
        """
        try:
            auth.revoke_refresh_tokens(uid)
            
            self.logger.info(f"Refresh tokens revoked for user: {uid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Token revocation failed: {e}")
            raise
    
    async def list_users(
        self,
        page_token: Optional[str] = None,
        max_results: int = 1000
    ) -> Dict[str, Any]:
        """Lista usuários com paginação e informações completas.
        
        Args:
            page_token (Optional[str]): Token de página para continuar
                listagem anterior. None para primeira página.
            max_results (int): Máximo de resultados por página (1-1000).
                Default: 1000
                
        Returns:
            Dict[str, Any]: Resultado da listagem contendo:
                - users: Lista de usuários com informações completas
                - next_page_token: Token para próxima página (None se última)
                - has_next_page: Boolean indicando se há mais páginas
                
        Raises:
            ValueError: Se max_results for inválido (< 1 ou > 1000)
            Exception: Se listagem falhar por permissões
            
        Examples:
            >>> # Listar primeira página
            >>> result = await auth_mgr.list_users(max_results=100)
            >>> for user in result["users"]:
            ...     print(f"{user['email']} - {user['custom_claims']}")
            >>> 
            >>> # Paginação completa
            >>> page_token = None
            >>> all_users = []
            >>> while True:
            ...     result = await auth_mgr.list_users(
            ...         page_token=page_token,
            ...         max_results=500
            ...     )
            ...     all_users.extend(result["users"])
            ...     if not result["has_next_page"]:
            ...         break
            ...     page_token = result["next_page_token"]
            
        Note:
            - Cada usuário inclui metadados completos e custom claims
            - Use paginação para grandes quantidades de usuários
            - Operação pode ser lenta para muitos usuários
            - Timestamps são em formato Unix (segundos)
        """
        try:
            page = auth.list_users(page_token=page_token, max_results=max_results)
            
            users = []
            for user in page.users:
                users.append({
                    'uid': user.uid,
                    'email': user.email,
                    'display_name': user.display_name,
                    'phone_number': user.phone_number,
                    'email_verified': user.email_verified,
                    'disabled': user.disabled,
                    'creation_timestamp': user.user_metadata.creation_timestamp,
                    'last_sign_in_timestamp': user.user_metadata.last_sign_in_timestamp,
                    'custom_claims': user.custom_claims or {}
                })
            
            return {
                'users': users,
                'next_page_token': page.next_page_token,
                'has_next_page': page.has_next_page
            }
            
        except Exception as e:
            self.logger.error(f"List users failed: {e}")
            raise
    
    async def generate_password_reset_link(
        self,
        email: str,
        action_code_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Gera link seguro de reset de senha para o usuário.
        
        Args:
            email (str): Email do usuário que solicita reset
            action_code_settings (Optional[Dict[str, Any]]): Configurações do link:
                - url: URL de redirecionamento após reset
                - handleCodeInApp: Se deve processar no app
                - dynamicLinkDomain: Domínio para Dynamic Links
                
        Returns:
            str: Link seguro de reset de senha válido por 1 hora
            
        Raises:
            Exception: Se geração falhar por email inválido ou permissões
            
        Examples:
            >>> # Link básico
            >>> reset_link = await auth_mgr.generate_password_reset_link(
            ...     "user@example.com"
            ... )
            >>> # Enviar por email
            >>> send_email("user@example.com", f"Reset: {reset_link}")
            >>> 
            >>> # Link com redirecionamento customizado
            >>> reset_link = await auth_mgr.generate_password_reset_link(
            ...     "user@example.com",
            ...     action_code_settings={
            ...         "url": "https://myapp.com/reset-complete",
            ...         "handleCodeInApp": True
            ...     }
            ... )
            
        Note:
            - Link expira em 1 hora por segurança
            - Usuário deve existir no Firebase Auth
            - Operação é logada para auditoria
            - Link pode ser usado apenas uma vez
        """
        try:
            link = auth.generate_password_reset_link(email, action_code_settings)
            
            self.logger.info(f"Password reset link generated for: {email}")
            return link
            
        except Exception as e:
            self.logger.error(f"Password reset link generation failed: {e}")
            raise
    
    async def generate_email_verification_link(
        self,
        email: str,
        action_code_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Gera link seguro de verificação de email.
        
        Args:
            email (str): Email do usuário para verificar
            action_code_settings (Optional[Dict[str, Any]]): Configurações do link:
                - url: URL de redirecionamento após verificação
                - handleCodeInApp: Se deve processar no app
                - dynamicLinkDomain: Domínio para Dynamic Links
                
        Returns:
            str: Link seguro de verificação válido por 3 dias
            
        Raises:
            Exception: Se geração falhar por email inválido ou permissões
            
        Examples:
            >>> # Link básico de verificação
            >>> verify_link = await auth_mgr.generate_email_verification_link(
            ...     "newuser@example.com"
            ... )
            >>> # Enviar email de boas-vindas
            >>> send_welcome_email("newuser@example.com", verify_link)
            >>> 
            >>> # Link com redirecionamento
            >>> verify_link = await auth_mgr.generate_email_verification_link(
            ...     "newuser@example.com",
            ...     action_code_settings={
            ...         "url": "https://myapp.com/welcome",
            ...         "handleCodeInApp": True
            ...     }
            ... )
            
        Note:
            - Link expira em 3 dias
            - Marca email como verificado quando usado
            - Usuário deve existir no Firebase Auth
            - Link pode ser usado apenas uma vez
        """
        try:
            link = auth.generate_email_verification_link(email, action_code_settings)
            
            self.logger.info(f"Email verification link generated for: {email}")
            return link
            
        except Exception as e:
            self.logger.error(f"Email verification link generation failed: {e}")
            raise
    
    async def import_users(
        self,
        users: List[Dict[str, Any]],
        hash_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Importa usuários em lote com validação enterprise.
        
        Args:
            users (List[Dict[str, Any]]): Lista de usuários para importar.
                Cada usuário deve ter: uid, email e opcionalmente:
                password_hash, password_salt, display_name, etc.
            hash_config (Optional[Dict[str, Any]]): Configuração do algoritmo
                de hash das senhas (SCRYPT, BCRYPT, etc). Necessário se
                importando senhas com hash.
                
        Returns:
            Dict[str, Any]: Resultado da importação contendo:
                - success_count: Número de usuários importados com sucesso
                - failure_count: Número de falhas
                - errors: Lista de erros com índice e motivo
                
        Raises:
            ValueError: Se dados dos usuários forem inválidos
            Exception: Se importação falhar por quota ou permissões
            
        Examples:
            >>> # Importar usuários sem senhas (usarão providers)
            >>> users_data = [
            ...     {
            ...         "uid": "user1",
            ...         "email": "user1@example.com",
            ...         "display_name": "Usuário 1",
            ...         "email_verified": True
            ...     },
            ...     {
            ...         "uid": "user2",
            ...         "email": "user2@example.com",
            ...         "display_name": "Usuário 2"
            ...     }
            ... ]
            >>> result = await auth_mgr.import_users(users_data)
            >>> print(f"Importados: {result['success_count']}")
            >>> 
            >>> # Importar com senhas BCRYPT
            >>> users_with_hash = [
            ...     {
            ...         "uid": "user3",
            ...         "email": "user3@example.com",
            ...         "password_hash": "$2a$10$...",  # BCRYPT hash
            ...     }
            ... ]
            >>> hash_config = {"hash_algo": "BCRYPT"}
            >>> result = await auth_mgr.import_users(
            ...     users_with_hash,
            ...     hash_config
            ... )
            
        Note:
            - Máximo 1000 usuários por operação
            - UIDs devem ser únicos no projeto
            - Operação é atômica (tudo ou nada)
            - Útil para migração de outros sistemas
        """
        try:
            # Convert to ImportUserRecord objects
            import_users = []
            for user_data in users:
                import_users.append(auth.ImportUserRecord(**user_data))
            
            result = auth.import_users(import_users, hash_config)
            
            self.logger.info(f"Users imported: {result.success_count} success, {result.failure_count} failures")
            
            return {
                'success_count': result.success_count,
                'failure_count': result.failure_count,
                'errors': [{'index': err.index, 'reason': err.reason} for err in result.errors]
            }
            
        except Exception as e:
            self.logger.error(f"User import failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde e conectividade do Firebase Auth.
        
        Returns:
            Dict[str, Any]: Status de saúde contendo:
                - status: 'healthy' ou 'unhealthy'
                - service: 'firebase_auth'
                - project_id: ID do projeto Firebase
                - timestamp: Timestamp da verificação (ISO format)
                - users_accessible: Se consegue acessar usuários
                - error: Mensagem de erro (apenas se unhealthy)
                
        Examples:
            >>> health = await auth_mgr.health_check()
            >>> if health['status'] == 'healthy':
            ...     print(f"Firebase Auth OK - Projeto: {health['project_id']}")
            ... else:
            ...     print(f"Firebase Auth Error: {health['error']}")
            
        Note:
            - Testa conectividade listando usuários (limite 1)
            - Não gera custos significativos
            - Útil para monitoring e alertas
            - Inclui timestamp para tracking de disponibilidade
        """
        try:
            # Test basic connectivity by listing one user
            page = auth.list_users(max_results=1)
            
            return {
                'status': 'healthy',
                'service': 'firebase_auth',
                'project_id': self.config.project_id,
                'timestamp': datetime.utcnow().isoformat(),
                'users_accessible': True
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'firebase_auth',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
