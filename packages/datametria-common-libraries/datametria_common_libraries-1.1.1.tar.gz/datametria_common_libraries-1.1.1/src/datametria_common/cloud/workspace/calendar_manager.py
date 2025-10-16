"""
Google Calendar Manager - Enterprise Integration

Provides event management and scheduling with:
- ErrorHandlerMixin for retry logic
- CacheMixin for event caching
- Rate limiting (500 requests per 100 seconds)
- LGPD/GDPR compliance with data masking
- Enterprise logging with audit trail
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from googleapiclient.discovery import build

from ...core.error_handler import ErrorHandlerMixin
from ...caching.cache_mixin import CacheMixin
from ...security.centralized_enterprise_logger import CentralizedEnterpriseLogger
from .config import WorkspaceConfig
from .oauth2 import WorkspaceOAuth2Manager
from .rate_limiter import WorkspaceRateLimiter


class CalendarManager(ErrorHandlerMixin, CacheMixin):
    """Google Calendar Manager with enterprise features"""

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
        """Lazy initialization of Calendar service"""
        if self._service is None:
            credentials = self.oauth_manager.get_credentials()
            self._service = build('calendar', 'v3', credentials=credentials)
        return self._service

    def _mask_email(self, email: str) -> str:
        """Mask email for LGPD/GDPR compliance"""
        if '@' not in email:
            return '***'
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"

    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        Create calendar event

        Args:
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime
            description: Event description
            location: Event location
            attendees: List of attendee emails
            calendar_id: Calendar ID (default: 'primary')

        Returns:
            Event metadata with id and htmlLink
        """
        await self.rate_limiter.check_and_wait('calendar')

        event = {
            'summary': summary,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'}
        }

        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        def _create():
            return self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()

        result = await self.execute_with_retry(_create, max_retries=3)

        if self.logger:
            masked_attendees = [self._mask_email(e) for e in (attendees or [])]
            self.logger.log_info(
                f"Event created: {summary}",
                extra={
                    'event_id': result['id'],
                    'attendees_masked': masked_attendees,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
        calendar_id: str = 'primary',
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List calendar events

        Args:
            time_min: Start of time range
            time_max: End of time range
            max_results: Maximum results
            calendar_id: Calendar ID
            use_cache: Use cache if available

        Returns:
            List of events
        """
        cache_key = f"calendar:events:{calendar_id}:{time_min}:{time_max}"
        if use_cache:
            cached = await self.cache_get(cache_key)
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('calendar')

        params = {
            'calendarId': calendar_id,
            'maxResults': min(max_results, 2500),
            'singleEvents': True,
            'orderBy': 'startTime'
        }

        if time_min:
            params['timeMin'] = time_min.isoformat() + 'Z'
        if time_max:
            params['timeMax'] = time_max.isoformat() + 'Z'

        def _list():
            return self.service.events().list(**params).execute()

        result = await self.execute_with_retry(_list, max_retries=2)
        events = result.get('items', [])

        if use_cache:
            await self.cache_set(cache_key, events, ttl=self.config.cache_ttl)

        return events

    async def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        Update calendar event

        Args:
            event_id: Event ID to update
            summary: New event title
            start_time: New start datetime
            end_time: New end datetime
            description: New description
            location: New location
            calendar_id: Calendar ID

        Returns:
            Updated event metadata
        """
        await self.rate_limiter.check_and_wait('calendar')

        def _get():
            return self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

        event = await self.execute_with_retry(_get, max_retries=2)

        if summary:
            event['summary'] = summary
        if start_time:
            event['start'] = {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'}
        if end_time:
            event['end'] = {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'}
        if description:
            event['description'] = description
        if location:
            event['location'] = location

        def _update():
            return self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()

        result = await self.execute_with_retry(_update, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Event updated: {event_id}",
                extra={
                    'event_id': event_id,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> bool:
        """
        Delete calendar event

        Args:
            event_id: Event ID to delete
            calendar_id: Calendar ID

        Returns:
            True if deleted successfully
        """
        await self.rate_limiter.check_and_wait('calendar')

        def _delete():
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True

        result = await self.execute_with_retry(_delete, max_retries=2)

        if self.logger:
            self.logger.log_info(
                f"Event deleted: {event_id}",
                extra={
                    'event_id': event_id,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def get_free_busy(
        self,
        time_min: datetime,
        time_max: datetime,
        calendars: List[str],
        timezone: str = 'UTC'
    ) -> Dict[str, Any]:
        """
        Get free/busy information

        Args:
            time_min: Start of time range
            time_max: End of time range
            calendars: List of calendar IDs
            timezone: Timezone

        Returns:
            Free/busy information
        """
        await self.rate_limiter.check_and_wait('calendar')

        body = {
            'timeMin': time_min.isoformat() + 'Z',
            'timeMax': time_max.isoformat() + 'Z',
            'timeZone': timezone,
            'items': [{'id': cal_id} for cal_id in calendars]
        }

        def _query():
            return self.service.freebusy().query(body=body).execute()

        return await self.execute_with_retry(_query, max_retries=2)

    async def test_connection(self) -> bool:
        """Test Calendar API connection"""
        try:
            await self.rate_limiter.check_and_wait('calendar')
            self.service.calendarList().list(maxResults=1).execute()
            return True
        except Exception:
            return False
