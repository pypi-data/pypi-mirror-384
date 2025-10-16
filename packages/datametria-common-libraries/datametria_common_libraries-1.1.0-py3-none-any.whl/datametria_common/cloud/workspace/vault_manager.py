"""
Google Vault Manager - Enterprise Integration

Provides eDiscovery and compliance operations with:
- ErrorHandlerMixin for retry logic
- CacheMixin for matter/export caching
- Rate limiting (10 requests per second)
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


class VaultManager(ErrorHandlerMixin, CacheMixin):
    """Google Vault Manager with enterprise features"""

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
        """Lazy initialization of Vault service"""
        if self._service is None:
            credentials = self.oauth_manager.get_credentials()
            self._service = build('vault', 'v1', credentials=credentials)
        return self._service

    def _mask_email(self, email: str) -> str:
        """Mask email for LGPD/GDPR compliance"""
        if '@' not in email:
            return '***'
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"

    async def create_matter(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new matter for eDiscovery

        Args:
            name: Matter name
            description: Matter description

        Returns:
            Matter metadata with matterId and name
        """
        await self.rate_limiter.check_and_wait('vault')

        matter = {'name': name}
        if description:
            matter['description'] = description

        def _create():
            return self.service.matters().create(body=matter).execute()

        result = await self.execute_with_retry(_create, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Matter created: {name}",
                extra={
                    'matter_id': result['matterId'],
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT', 'EDISCOVERY']
                }
            )

        return result

    async def list_matters(
        self,
        state: str = 'OPEN',
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List matters

        Args:
            state: Matter state (OPEN, CLOSED, DELETED)
            use_cache: Use cache if available

        Returns:
            List of matters
        """
        cache_key = f"vault:matters:{state}"
        if use_cache:
            cached = await self.cache_get(cache_key)
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('vault')

        def _list():
            return self.service.matters().list(state=state).execute()

        result = await self.execute_with_retry(_list, max_retries=2)
        matters = result.get('matters', [])

        if use_cache:
            await self.cache_set(cache_key, matters, ttl=self.config.cache_ttl)

        return matters

    async def create_hold(
        self,
        matter_id: str,
        name: str,
        corpus: str,
        accounts: List[str]
    ) -> Dict[str, Any]:
        """
        Create legal hold

        Args:
            matter_id: Matter ID
            name: Hold name
            corpus: Data corpus (MAIL, DRIVE, GROUPS, HANGOUTS_CHAT)
            accounts: List of account emails to hold

        Returns:
            Hold metadata with holdId
        """
        await self.rate_limiter.check_and_wait('vault')

        hold = {
            'name': name,
            'corpus': corpus,
            'accounts': [{'accountId': email} for email in accounts]
        }

        def _create():
            return self.service.matters().holds().create(
                matterId=matter_id,
                body=hold
            ).execute()

        result = await self.execute_with_retry(_create, max_retries=3)

        if self.logger:
            masked_accounts = [self._mask_email(e) for e in accounts]
            self.logger.log_info(
                f"Hold created: {name}",
                extra={
                    'hold_id': result['holdId'],
                    'matter_id': matter_id,
                    'accounts_masked': masked_accounts,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT', 'EDISCOVERY']
                }
            )

        return result

    async def search_mail(
        self,
        matter_id: str,
        query: str,
        accounts: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search mail for eDiscovery

        Args:
            matter_id: Matter ID
            query: Search query
            accounts: List of account emails to search
            start_time: Start time (RFC 3339)
            end_time: End time (RFC 3339)

        Returns:
            Search query metadata
        """
        await self.rate_limiter.check_and_wait('vault')

        search_query = {
            'corpus': 'MAIL',
            'dataScope': 'ALL_DATA',
            'searchMethod': 'ENTIRE_ORG',
            'terms': query
        }

        if accounts:
            search_query['accountInfo'] = {
                'emails': accounts
            }

        if start_time or end_time:
            search_query['mailOptions'] = {}
            if start_time:
                search_query['mailOptions']['startTime'] = start_time
            if end_time:
                search_query['mailOptions']['endTime'] = end_time

        query_body = {
            'name': f'Search: {query[:50]}',
            'query': search_query
        }

        def _search():
            return self.service.matters().savedQueries().create(
                matterId=matter_id,
                body=query_body
            ).execute()

        result = await self.execute_with_retry(_search, max_retries=2)

        if self.logger:
            self.logger.log_info(
                f"Mail search created",
                extra={
                    'saved_query_id': result['savedQueryId'],
                    'matter_id': matter_id,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT', 'EDISCOVERY']
                }
            )

        return result

    async def create_export(
        self,
        matter_id: str,
        name: str,
        query: Dict[str, Any],
        export_format: str = 'MBOX'
    ) -> Dict[str, Any]:
        """
        Create export for eDiscovery

        Args:
            matter_id: Matter ID
            name: Export name
            query: Search query configuration
            export_format: Export format (MBOX, PST)

        Returns:
            Export metadata with exportId
        """
        await self.rate_limiter.check_and_wait('vault')

        export = {
            'name': name,
            'query': query,
            'exportOptions': {
                'mailOptions': {
                    'exportFormat': export_format
                }
            }
        }

        def _create():
            return self.service.matters().exports().create(
                matterId=matter_id,
                body=export
            ).execute()

        result = await self.execute_with_retry(_create, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Export created: {name}",
                extra={
                    'export_id': result['id'],
                    'matter_id': matter_id,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT', 'EDISCOVERY']
                }
            )

        return result

    async def get_export_status(
        self,
        matter_id: str,
        export_id: str,
        use_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Get export status

        Args:
            matter_id: Matter ID
            export_id: Export ID
            use_cache: Use cache if available

        Returns:
            Export metadata with status
        """
        if use_cache:
            cached = await self.cache_get(f"vault:export:{export_id}")
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('vault')

        def _get():
            return self.service.matters().exports().get(
                matterId=matter_id,
                exportId=export_id
            ).execute()

        export = await self.execute_with_retry(_get, max_retries=2)

        if use_cache and export.get('status') == 'COMPLETED':
            await self.cache_set(
                f"vault:export:{export_id}",
                export,
                ttl=self.config.cache_ttl
            )

        return export

    async def list_exports(
        self,
        matter_id: str
    ) -> List[Dict[str, Any]]:
        """
        List exports for matter

        Args:
            matter_id: Matter ID

        Returns:
            List of exports
        """
        await self.rate_limiter.check_and_wait('vault')

        def _list():
            return self.service.matters().exports().list(
                matterId=matter_id
            ).execute()

        result = await self.execute_with_retry(_list, max_retries=2)
        return result.get('exports', [])

    async def test_connection(self) -> bool:
        """Test Vault API connection"""
        try:
            await self.rate_limiter.check_and_wait('vault')
            self.service.matters().list(pageSize=1).execute()
            return True
        except Exception:
            return False
