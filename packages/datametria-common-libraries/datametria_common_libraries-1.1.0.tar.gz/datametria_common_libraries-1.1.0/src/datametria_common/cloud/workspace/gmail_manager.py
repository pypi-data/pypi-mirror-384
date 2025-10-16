"""
GmailManager - Gerenciador para Gmail API

Operações de email com enterprise logging, rate limiting, retry automático
e compliance LGPD/GDPR integrado.
"""

import base64
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datametria_common.cloud.workspace.config import WorkspaceConfig
from datametria_common.cloud.workspace.oauth2 import WorkspaceOAuth2Manager
from datametria_common.cloud.workspace.rate_limiter import WorkspaceRateLimiter
from datametria_common.core.error_handler import ErrorHandlerMixin, ErrorCategory, ErrorSeverity
from datametria_common.caching import CacheMixin
from datametria_common.security.centralized_logger import CentralizedEnterpriseLogger


class GmailManager(ErrorHandlerMixin, CacheMixin):
    """Gmail API Manager com enterprise features.
    
    Integra componentes DATAMETRIA:
    - ErrorHandlerMixin: Retry automático com exponential backoff
    - CacheMixin: Cache de mensagens lidas
    - Enterprise Logging: Audit trail completo
    - Rate Limiter: Respeito às quotas do Google
    - Data Masking: LGPD/GDPR compliance
    
    Example:
        >>> config = WorkspaceConfig.from_env()
        >>> oauth = WorkspaceOAuth2Manager(config, logger)
        >>> gmail = GmailManager(config, logger, oauth)
        >>> 
        >>> # Enviar email
        >>> msg_id = await gmail.send_email(
        ...     to='user@example.com',
        ...     subject='Test',
        ...     body='Hello!'
        ... )
    """
    
    def __init__(
        self,
        config: WorkspaceConfig,
        logger: CentralizedEnterpriseLogger,
        oauth_manager: Optional[WorkspaceOAuth2Manager] = None,
        rate_limiter: Optional[WorkspaceRateLimiter] = None
    ):
        """Inicializar Gmail Manager.
        
        Args:
            config: Configuração do Workspace
            logger: Enterprise logger
            oauth_manager: OAuth2 manager (opcional)
            rate_limiter: Rate limiter (opcional)
        """
        super().__init__()
        self.config = config
        self._logger = logger
        
        # OAuth2
        self._oauth = oauth_manager or WorkspaceOAuth2Manager(config, logger)
        
        # Rate Limiter
        self._rate_limiter = rate_limiter or WorkspaceRateLimiter(
            logger,
            enabled=config.rate_limit_enabled
        )
        
        # Gmail service (lazy initialization)
        self._service = None
        
        self._logger.info(
            "GmailManager initialized",
            rate_limit_enabled=config.rate_limit_enabled,
            cache_enabled=config.cache_enabled,
            compliance_tags=["AUDIT", "INITIALIZATION"]
        )
    
    def _get_service(self):
        """Obter Gmail service (lazy initialization)."""
        if not self._service:
            credentials = self._oauth.get_credentials()
            if not credentials:
                raise ValueError("No valid credentials available")
            
            self._service = build('gmail', 'v1', credentials=credentials)
        
        return self._service
    
    def _mask_email(self, email: str) -> str:
        """Mascarar email para LGPD/GDPR."""
        if '@' not in email:
            return email
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            return f"{'*' * len(local)}@{domain}"
        return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"
    
    @ErrorHandlerMixin.with_error_handling(
        category=ErrorCategory.EXTERNAL_API,
        severity=ErrorSeverity.MEDIUM,
        retry_count=3,
        retry_delay=1.0
    )
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        user_id: str = 'me'
    ) -> str:
        """Enviar email com retry e logging.
        
        Args:
            to: Destinatário
            subject: Assunto
            body: Corpo do email
            html: Se True, corpo é HTML
            cc: Lista de CC
            bcc: Lista de BCC
            attachments: Lista de caminhos de arquivos
            user_id: ID do usuário (default: 'me')
            
        Returns:
            ID da mensagem enviada
            
        Example:
            >>> msg_id = await gmail.send_email(
            ...     to='user@example.com',
            ...     subject='Welcome',
            ...     body='<h1>Hello!</h1>',
            ...     html=True
            ... )
        """
        # Rate limiting
        await self._rate_limiter.check_and_wait('gmail', user_id, 'send_email')
        
        start_time = time.time()
        
        # Log início
        self._logger.info(
            "Sending email",
            to=self._mask_email(to),
            subject=subject,
            has_attachments=bool(attachments),
            compliance_tags=["LGPD", "GDPR", "AUDIT", "EMAIL_SEND"]
        )
        
        try:
            # Criar mensagem
            message = self._create_message(to, subject, body, html, cc, bcc, attachments)
            
            # Enviar
            service = self._get_service()
            result = service.users().messages().send(
                userId=user_id,
                body=message
            ).execute()
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log sucesso
            self._logger.info(
                "Email sent successfully",
                message_id=result['id'],
                to=self._mask_email(to),
                execution_time_ms=round(execution_time, 2),
                compliance_tags=["AUDIT", "EMAIL_SEND"]
            )
            
            return result['id']
            
        except HttpError as e:
            execution_time = (time.time() - start_time) * 1000
            
            self._logger.error(
                "Failed to send email",
                error=str(e),
                error_code=e.resp.status,
                to=self._mask_email(to),
                execution_time_ms=round(execution_time, 2),
                compliance_tags=["ERROR", "EMAIL_SEND"]
            )
            raise
    
    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Criar mensagem MIME."""
        if attachments:
            message = MIMEMultipart()
        else:
            message = MIMEText(body, 'html' if html else 'plain')
        
        message['to'] = to
        message['subject'] = subject
        
        if cc:
            message['cc'] = ', '.join(cc)
        if bcc:
            message['bcc'] = ', '.join(bcc)
        
        # Adicionar corpo se multipart
        if attachments:
            message.attach(MIMEText(body, 'html' if html else 'plain'))
            
            # Adicionar anexos
            for file_path in attachments:
                self._attach_file(message, file_path)
        
        # Codificar
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw}
    
    def _attach_file(self, message: MIMEMultipart, file_path: str) -> None:
        """Anexar arquivo à mensagem."""
        path = Path(file_path)
        
        with open(path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={path.name}')
        message.attach(part)
    
    @ErrorHandlerMixin.with_error_handling(
        category=ErrorCategory.EXTERNAL_API,
        severity=ErrorSeverity.LOW,
        retry_count=2
    )
    async def get_message(
        self,
        message_id: str,
        user_id: str = 'me',
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Obter mensagem por ID com cache.
        
        Args:
            message_id: ID da mensagem
            user_id: ID do usuário
            use_cache: Se True, usa cache
            
        Returns:
            Dados da mensagem
            
        Example:
            >>> message = await gmail.get_message('msg_123')
            >>> print(message['subject'])
        """
        # Rate limiting
        await self._rate_limiter.check_and_wait('gmail', user_id, 'get_message')
        
        # Tentar cache
        if use_cache and self.config.cache_enabled:
            cache_key = f"gmail:message:{message_id}"
            cached = await self.cache_get(cache_key)
            if cached:
                self._logger.debug(
                    "Cache hit for message",
                    message_id=message_id
                )
                return cached
        
        start_time = time.time()
        
        try:
            service = self._get_service()
            result = service.users().messages().get(
                userId=user_id,
                id=message_id,
                format='full'
            ).execute()
            
            # Parsear mensagem
            parsed = self._parse_message(result)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Cache
            if use_cache and self.config.cache_enabled:
                await self.cache_set(
                    f"gmail:message:{message_id}",
                    parsed,
                    ttl=self.config.cache_ttl
                )
            
            # Log
            self._logger.info(
                "Message retrieved",
                message_id=message_id,
                from_email=self._mask_email(parsed.get('from', '')),
                execution_time_ms=round(execution_time, 2),
                compliance_tags=["AUDIT", "EMAIL_READ"]
            )
            
            return parsed
            
        except HttpError as e:
            self._logger.error(
                "Failed to get message",
                message_id=message_id,
                error=str(e),
                compliance_tags=["ERROR", "EMAIL_READ"]
            )
            raise
    
    def _parse_message(self, message: Dict) -> Dict[str, Any]:
        """Parsear mensagem do Gmail."""
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'subject': headers.get('Subject', ''),
            'date': headers.get('Date', ''),
            'snippet': message.get('snippet', ''),
            'body': self._get_body(message['payload']),
            'labels': message.get('labelIds', [])
        }
    
    def _get_body(self, payload: Dict) -> str:
        """Extrair corpo da mensagem."""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode()
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if part['body'].get('data'):
                        return base64.urlsafe_b64decode(part['body']['data']).decode()
        
        return ''
    
    @ErrorHandlerMixin.with_error_handling(
        category=ErrorCategory.EXTERNAL_API,
        severity=ErrorSeverity.LOW,
        retry_count=2
    )
    async def search_messages(
        self,
        query: str,
        max_results: int = 100,
        user_id: str = 'me'
    ) -> List[Dict[str, Any]]:
        """Buscar mensagens com query.
        
        Args:
            query: Query de busca (formato Gmail)
            max_results: Máximo de resultados
            user_id: ID do usuário
            
        Returns:
            Lista de mensagens
            
        Example:
            >>> messages = await gmail.search_messages(
            ...     query='from:noreply@github.com is:unread',
            ...     max_results=50
            ... )
        """
        # Rate limiting
        await self._rate_limiter.check_and_wait('gmail', user_id, 'search_messages')
        
        start_time = time.time()
        
        self._logger.info(
            "Searching messages",
            query=query,
            max_results=max_results,
            compliance_tags=["AUDIT", "EMAIL_SEARCH"]
        )
        
        try:
            service = self._get_service()
            results = []
            page_token = None
            
            while len(results) < max_results:
                response = service.users().messages().list(
                    userId=user_id,
                    q=query,
                    maxResults=min(max_results - len(results), 500),
                    pageToken=page_token
                ).execute()
                
                messages = response.get('messages', [])
                if not messages:
                    break
                
                results.extend(messages)
                page_token = response.get('nextPageToken')
                
                if not page_token:
                    break
            
            execution_time = (time.time() - start_time) * 1000
            
            self._logger.info(
                "Messages search completed",
                query=query,
                results_count=len(results),
                execution_time_ms=round(execution_time, 2),
                compliance_tags=["AUDIT", "EMAIL_SEARCH"]
            )
            
            return results[:max_results]
            
        except HttpError as e:
            self._logger.error(
                "Failed to search messages",
                query=query,
                error=str(e),
                compliance_tags=["ERROR", "EMAIL_SEARCH"]
            )
            raise
    
    async def test_connection(self) -> bool:
        """Testar conectividade (para health check)."""
        try:
            service = self._get_service()
            service.users().getProfile(userId='me').execute()
            return True
        except Exception:
            return False
