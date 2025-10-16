"""
Google Meet Manager - Enterprise Integration

Provides conferencing operations with:
- ErrorHandlerMixin for retry logic
- CacheMixin for conference caching
- Rate limiting (100 requests per 100 seconds)
- LGPD/GDPR compliance with data masking
- Enterprise logging with audit trail
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from googleapiclient.discovery import build

from ...core.error_handler import ErrorHandlerMixin
from ...caching.cache_mixin import CacheMixin
from ...security.centralized_enterprise_logger import CentralizedEnterpriseLogger
from .config import WorkspaceConfig
from .oauth2 import WorkspaceOAuth2Manager
from .rate_limiter import WorkspaceRateLimiter


class MeetManager(ErrorHandlerMixin, CacheMixin):
    """Google Meet Manager with enterprise features"""

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
        """Lazy initialization of Meet service"""
        if self._service is None:
            credentials = self.oauth_manager.get_credentials()
            self._service = build('meet', 'v2', credentials=credentials)
        return self._service

    def _mask_email(self, email: str) -> str:
        """Mask email for LGPD/GDPR compliance"""
        if '@' not in email:
            return '***'
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"

    async def create_meeting(
        self,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new meeting space

        Args:
            title: Meeting title/name

        Returns:
            Conference space metadata with meetingUri and meetingCode
        """
        await self.rate_limiter.check_and_wait('meet')

        space = {}
        if title:
            space['config'] = {'entryPointAccess': {'accessCode': title}}

        def _create():
            return self.service.spaces().create(body=space).execute()

        result = await self.execute_with_retry(_create, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Meeting created",
                extra={
                    'space_name': result['name'],
                    'meeting_code': result.get('meetingCode', 'N/A'),
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def get_meeting_details(
        self,
        space_name: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get meeting space details

        Args:
            space_name: Space resource name (spaces/*)
            use_cache: Use cache if available

        Returns:
            Space metadata with configuration
        """
        if use_cache:
            cached = await self.cache_get(f"meet:space:{space_name}")
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('meet')

        def _get():
            return self.service.spaces().get(name=space_name).execute()

        space = await self.execute_with_retry(_get, max_retries=2)

        if use_cache:
            await self.cache_set(
                f"meet:space:{space_name}",
                space,
                ttl=self.config.cache_ttl
            )

        return space

    async def end_meeting(
        self,
        space_name: str
    ) -> bool:
        """
        End active meeting

        Args:
            space_name: Space resource name

        Returns:
            True if ended successfully
        """
        await self.rate_limiter.check_and_wait('meet')

        def _end():
            return self.service.spaces().endActiveConference(
                name=space_name
            ).execute()

        result = await self.execute_with_retry(_end, max_retries=2)

        if self.logger:
            self.logger.log_info(
                f"Meeting ended",
                extra={
                    'space_name': space_name,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return True

    async def list_participants(
        self,
        conference_name: str,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List conference participants

        Args:
            conference_name: Conference resource name (conferenceRecords/*)
            page_size: Maximum results per page

        Returns:
            List of participants
        """
        await self.rate_limiter.check_and_wait('meet')

        def _list():
            return self.service.conferenceRecords().participants().list(
                parent=conference_name,
                pageSize=page_size
            ).execute()

        result = await self.execute_with_retry(_list, max_retries=2)
        
        participants = result.get('participants', [])

        if self.logger:
            masked_count = len(participants)
            self.logger.log_info(
                f"Participants listed",
                extra={
                    'conference': conference_name,
                    'participant_count': masked_count,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return participants

    async def list_recordings(
        self,
        conference_name: str,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List conference recordings

        Args:
            conference_name: Conference resource name
            page_size: Maximum results per page

        Returns:
            List of recordings
        """
        await self.rate_limiter.check_and_wait('meet')

        def _list():
            return self.service.conferenceRecords().recordings().list(
                parent=conference_name,
                pageSize=page_size
            ).execute()

        result = await self.execute_with_retry(_list, max_retries=2)
        recordings = result.get('recordings', [])

        if self.logger:
            self.logger.log_info(
                f"Recordings listed",
                extra={
                    'conference': conference_name,
                    'recording_count': len(recordings),
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return recordings

    async def get_recording(
        self,
        recording_name: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get recording details

        Args:
            recording_name: Recording resource name
            use_cache: Use cache if available

        Returns:
            Recording metadata
        """
        if use_cache:
            cached = await self.cache_get(f"meet:recording:{recording_name}")
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('meet')

        def _get():
            return self.service.conferenceRecords().recordings().get(
                name=recording_name
            ).execute()

        recording = await self.execute_with_retry(_get, max_retries=2)

        if use_cache:
            await self.cache_set(
                f"meet:recording:{recording_name}",
                recording,
                ttl=self.config.cache_ttl
            )

        return recording

    async def test_connection(self) -> bool:
        """Test Meet API connection"""
        try:
            await self.rate_limiter.check_and_wait('meet')
            # Test by attempting to create a minimal space
            space = self.service.spaces().create(body={}).execute()
            # Clean up test space if needed
            return True
        except Exception:
            return False
