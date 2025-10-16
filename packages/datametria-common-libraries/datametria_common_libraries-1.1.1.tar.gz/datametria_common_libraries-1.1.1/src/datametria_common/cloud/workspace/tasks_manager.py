"""
Google Tasks Manager - Enterprise Integration

Provides task management operations with:
- ErrorHandlerMixin for retry logic
- CacheMixin for task/tasklist caching
- Rate limiting (50 requests per second)
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


class TasksManager(ErrorHandlerMixin, CacheMixin):
    """Google Tasks Manager with enterprise features"""

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
        """Lazy initialization of Tasks service"""
        if self._service is None:
            credentials = self.oauth_manager.get_credentials()
            self._service = build('tasks', 'v1', credentials=credentials)
        return self._service

    async def create_tasklist(
        self,
        title: str
    ) -> Dict[str, Any]:
        """
        Create new task list

        Args:
            title: Task list title

        Returns:
            Task list metadata with id and title
        """
        await self.rate_limiter.check_and_wait('tasks')

        tasklist = {'title': title}

        def _create():
            return self.service.tasklists().insert(body=tasklist).execute()

        result = await self.execute_with_retry(_create, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Task list created: {title}",
                extra={
                    'tasklist_id': result['id'],
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def list_tasklists(
        self,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all task lists

        Args:
            use_cache: Use cache if available

        Returns:
            List of task lists
        """
        cache_key = "tasks:tasklists"
        if use_cache:
            cached = await self.cache_get(cache_key)
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('tasks')

        def _list():
            return self.service.tasklists().list().execute()

        result = await self.execute_with_retry(_list, max_retries=2)
        tasklists = result.get('items', [])

        if use_cache:
            await self.cache_set(cache_key, tasklists, ttl=self.config.cache_ttl)

        return tasklists

    async def create_task(
        self,
        tasklist_id: str,
        title: str,
        notes: Optional[str] = None,
        due: Optional[datetime] = None,
        parent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new task

        Args:
            tasklist_id: Task list ID
            title: Task title
            notes: Task notes/description
            due: Due date
            parent: Parent task ID for subtasks

        Returns:
            Task metadata with id and title
        """
        await self.rate_limiter.check_and_wait('tasks')

        task = {'title': title}
        if notes:
            task['notes'] = notes
        if due:
            task['due'] = due.isoformat() + 'Z'

        params = {'tasklist': tasklist_id, 'body': task}
        if parent:
            params['parent'] = parent

        def _create():
            return self.service.tasks().insert(**params).execute()

        result = await self.execute_with_retry(_create, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Task created: {title}",
                extra={
                    'task_id': result['id'],
                    'tasklist_id': tasklist_id,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def list_tasks(
        self,
        tasklist_id: str,
        show_completed: bool = False,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List tasks in task list

        Args:
            tasklist_id: Task list ID
            show_completed: Include completed tasks
            use_cache: Use cache if available

        Returns:
            List of tasks
        """
        cache_key = f"tasks:list:{tasklist_id}:{show_completed}"
        if use_cache:
            cached = await self.cache_get(cache_key)
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('tasks')

        def _list():
            return self.service.tasks().list(
                tasklist=tasklist_id,
                showCompleted=show_completed
            ).execute()

        result = await self.execute_with_retry(_list, max_retries=2)
        tasks = result.get('items', [])

        if use_cache:
            await self.cache_set(cache_key, tasks, ttl=self.config.cache_ttl)

        return tasks

    async def update_task(
        self,
        tasklist_id: str,
        task_id: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        status: Optional[str] = None,
        due: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Update task

        Args:
            tasklist_id: Task list ID
            task_id: Task ID
            title: New title
            notes: New notes
            status: New status (needsAction, completed)
            due: New due date

        Returns:
            Updated task metadata
        """
        await self.rate_limiter.check_and_wait('tasks')

        def _get():
            return self.service.tasks().get(
                tasklist=tasklist_id,
                task=task_id
            ).execute()

        task = await self.execute_with_retry(_get, max_retries=2)

        if title:
            task['title'] = title
        if notes:
            task['notes'] = notes
        if status:
            task['status'] = status
        if due:
            task['due'] = due.isoformat() + 'Z'

        def _update():
            return self.service.tasks().update(
                tasklist=tasklist_id,
                task=task_id,
                body=task
            ).execute()

        result = await self.execute_with_retry(_update, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"Task updated: {task_id}",
                extra={
                    'task_id': task_id,
                    'tasklist_id': tasklist_id,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def delete_task(
        self,
        tasklist_id: str,
        task_id: str
    ) -> bool:
        """
        Delete task

        Args:
            tasklist_id: Task list ID
            task_id: Task ID

        Returns:
            True if deleted successfully
        """
        await self.rate_limiter.check_and_wait('tasks')

        def _delete():
            self.service.tasks().delete(
                tasklist=tasklist_id,
                task=task_id
            ).execute()
            return True

        result = await self.execute_with_retry(_delete, max_retries=2)

        if self.logger:
            self.logger.log_info(
                f"Task deleted: {task_id}",
                extra={
                    'task_id': task_id,
                    'tasklist_id': tasklist_id,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def complete_task(
        self,
        tasklist_id: str,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Mark task as completed

        Args:
            tasklist_id: Task list ID
            task_id: Task ID

        Returns:
            Updated task metadata
        """
        return await self.update_task(
            tasklist_id=tasklist_id,
            task_id=task_id,
            status='completed'
        )

    async def test_connection(self) -> bool:
        """Test Tasks API connection"""
        try:
            await self.rate_limiter.check_and_wait('tasks')
            self.service.tasklists().list(maxResults=1).execute()
            return True
        except Exception:
            return False
