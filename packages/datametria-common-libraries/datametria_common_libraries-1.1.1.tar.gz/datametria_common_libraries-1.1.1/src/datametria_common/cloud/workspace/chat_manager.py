"""
Google Chat Manager - Enterprise Integration

Provides messaging and bot operations with:
- ErrorHandlerMixin for retry logic
- CacheMixin for space/message caching
- Rate limiting (60 requests per 60 seconds)
- LGPD/GDPR compliance with data masking
- Enterprise logging with audit trail
"""

from typing import Optional, Dict, Any, List

from googleapiclient.discovery import build

from ...core.error_handler import ErrorHandlerMixin
from ...caching.cache_mixin import CacheMixin
from ...security.centralized_enterprise_logger import CentralizedEnterpriseLogger
from .config import WorkspaceConfig
from .oauth2 import WorkspaceOAuth2Manager
from .rate_limiter import WorkspaceRateLimiter


class ChatManager(ErrorHandlerMixin, CacheMixin):
    """Google Chat Manager with enterprise features"""

    def __init__(
        self,
        config: WorkspaceConfig,
        oauth_manager: WorkspaceOAuth2Manager,
        rate_limiter: WorkspaceRateLimiter,
        logger: Optional[CentralizedEnterpriseLogger] = None
    ):
        self.config = config
        self.oauth_manager = oauth_manager
        self.rate_limiter = rate_limiter
        self.logger = logger
        self._service = None

    @property
    def service(self):
        """Lazy initialization of Chat service"""
        if self._service is None:
            credentials = self.oauth_manager.get_credentials()
            self._service = build('chat', 'v1', credentials=credentials)
        return self._service

    def _mask_email(self, email: str) -> str:
        """Mask email for LGPD/GDPR compliance"""
        if '@' not in email:
            return '***'
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"

    async def send_message(
        self,
        space_name: str,
        text: str,
        thread_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send text message to space

        Args:
            space_name: Space resource name (spaces/*)
            text: Message text
            thread_key: Thread key for threading messages

        Returns:
            Message metadata with name and createTime
        """
        await self.rate_limiter.check_and_wait('chat')

        message = {'text': text}
        params = {'parent': space_name, 'body': message}
        
        if thread_key:
            params['threadKey'] = thread_key

        def _send():
            return self.service.spaces().messages().create(**params).execute()

        result = await self.execute_with_retry(_send, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Message sent to space",
                extra={
                    'message_name': result['name'],
                    'space': space_name,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def send_card_message(
        self,
        space_name: str,
        header_title: str,
        sections: List[Dict[str, Any]],
        thread_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send card message with rich formatting

        Args:
            space_name: Space resource name
            header_title: Card header title
            sections: List of card sections with widgets
            thread_key: Thread key for threading

        Returns:
            Message metadata
        """
        await self.rate_limiter.check_and_wait('chat')

        card = {
            'header': {'title': header_title},
            'sections': sections
        }
        
        message = {'cardsV2': [{'card': card}]}
        params = {'parent': space_name, 'body': message}
        
        if thread_key:
            params['threadKey'] = thread_key

        def _send():
            return self.service.spaces().messages().create(**params).execute()

        result = await self.execute_with_retry(_send, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Card message sent to space",
                extra={
                    'message_name': result['name'],
                    'space': space_name,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def create_space(
        self,
        display_name: str,
        space_type: str = 'SPACE'
    ) -> Dict[str, Any]:
        """
        Create new space

        Args:
            display_name: Space display name
            space_type: Type (SPACE or DM)

        Returns:
            Space metadata with name
        """
        await self.rate_limiter.check_and_wait('chat')

        space = {
            'displayName': display_name,
            'spaceType': space_type
        }

        def _create():
            return self.service.spaces().create(body=space).execute()

        result = await self.execute_with_retry(_create, max_retries=2)

        if self.logger:
            self.logger.log_info(
                f"Space created: {display_name}",
                extra={
                    'space_name': result['name'],
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def add_member(
        self,
        space_name: str,
        member_email: str,
        member_type: str = 'HUMAN'
    ) -> Dict[str, Any]:
        """
        Add member to space

        Args:
            space_name: Space resource name
            member_email: Member email
            member_type: Type (HUMAN or BOT)

        Returns:
            Membership metadata
        """
        await self.rate_limiter.check_and_wait('chat')

        membership = {
            'member': {
                'name': f'users/{member_email}',
                'type': member_type
            }
        }

        def _add():
            return self.service.spaces().members().create(
                parent=space_name,
                body=membership
            ).execute()

        result = await self.execute_with_retry(_add, max_retries=2)

        if self.logger:
            self.logger.log_info(
                f"Member added to space",
                extra={
                    'space': space_name,
                    'member_masked': self._mask_email(member_email),
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def list_spaces(
        self,
        page_size: int = 100,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List spaces

        Args:
            page_size: Maximum results per page
            use_cache: Use cache if available

        Returns:
            List of spaces
        """
        cache_key = f"chat:spaces:{page_size}"
        if use_cache:
            cached = await self.cache_get(cache_key)
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('chat')

        def _list():
            return self.service.spaces().list(pageSize=page_size).execute()

        result = await self.execute_with_retry(_list, max_retries=2)
        spaces = result.get('spaces', [])

        if use_cache:
            await self.cache_set(cache_key, spaces, ttl=self.config.cache_ttl)

        return spaces

    async def get_message(
        self,
        message_name: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get message details

        Args:
            message_name: Message resource name
            use_cache: Use cache if available

        Returns:
            Message metadata
        """
        if use_cache:
            cached = await self.cache_get(f"chat:message:{message_name}")
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('chat')

        def _get():
            return self.service.spaces().messages().get(name=message_name).execute()

        message = await self.execute_with_retry(_get, max_retries=2)

        if use_cache:
            await self.cache_set(
                f"chat:message:{message_name}",
                message,
                ttl=self.config.cache_ttl
            )

        return message

    async def delete_message(
        self,
        message_name: str
    ) -> bool:
        """
        Delete message

        Args:
            message_name: Message resource name

        Returns:
            True if deleted successfully
        """
        await self.rate_limiter.check_and_wait('chat')

        def _delete():
            self.service.spaces().messages().delete(name=message_name).execute()
            return True

        result = await self.execute_with_retry(_delete, max_retries=2)

        if self.logger:
            self.logger.log_info(
                f"Message deleted",
                extra={
                    'message_name': message_name,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def test_connection(self) -> bool:
        """Test Chat API connection"""
        try:
            await self.rate_limiter.check_and_wait('chat')
            self.service.spaces().list(pageSize=1).execute()
            return True
        except Exception:
            return False
