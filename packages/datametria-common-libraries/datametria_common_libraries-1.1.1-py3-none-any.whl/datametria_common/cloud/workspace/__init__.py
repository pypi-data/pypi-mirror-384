"""
Google Workspace APIs Integration - DATAMETRIA Common Libraries

Integração enterprise-ready com Gmail, Drive, Calendar, Chat, Meet, Tasks e Vault
com compliance LGPD/GDPR, rate limiting automático e observabilidade completa.
"""

from .config import WorkspaceConfig
from .manager import EnterpriseWorkspaceManager
from .oauth2 import WorkspaceOAuth2Manager
from .rate_limiter import WorkspaceRateLimiter
from .gmail_manager import GmailManager
from .drive_manager import DriveManager
from .calendar_manager import CalendarManager
from .chat_manager import ChatManager
from .meet_manager import MeetManager
from .tasks_manager import TasksManager
from .vault_manager import VaultManager
from .cache_integration import WorkspaceCacheManager
from .performance_integration import WorkspacePerformanceMonitor
from .health_check import WorkspaceHealthCheck, HealthStatus
from .compliance_automation import WorkspaceComplianceAutomation, DataOperation, ComplianceRegulation

__all__ = [
    'WorkspaceConfig',
    'EnterpriseWorkspaceManager',
    'WorkspaceOAuth2Manager',
    'WorkspaceRateLimiter',
    'GmailManager',
    'DriveManager',
    'CalendarManager',
    'ChatManager',
    'MeetManager',
    'TasksManager',
    'VaultManager',
    'WorkspaceCacheManager',
    'WorkspacePerformanceMonitor',
    'WorkspaceHealthCheck',
    'HealthStatus',
    'WorkspaceComplianceAutomation',
    'DataOperation',
    'ComplianceRegulation'
]

__version__ = '1.0.0'
