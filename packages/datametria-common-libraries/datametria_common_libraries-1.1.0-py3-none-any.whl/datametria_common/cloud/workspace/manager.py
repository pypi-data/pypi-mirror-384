"""
EnterpriseWorkspaceManager - Gerenciador principal para Google Workspace APIs

Coordena todos os serviços Workspace com enterprise logging, health checks
e integração completa com componentes DATAMETRIA.
"""

from typing import Optional
from datetime import datetime, timezone

from datametria_common.cloud.workspace.config import WorkspaceConfig
from datametria_common.core.health_check import HealthCheckMixin
from datametria_common.security.config import LoggingConfig
from datametria_common.security.centralized_logger import CentralizedEnterpriseLogger


class EnterpriseWorkspaceManager(HealthCheckMixin):
    """Gerenciador enterprise para Google Workspace APIs.
    
    Coordena acesso a 7 APIs do Google Workspace:
    - Gmail API
    - Drive API
    - Calendar API
    - Chat API
    - Meet API
    - Tasks API
    - Vault API
    
    Integra componentes DATAMETRIA:
    - Enterprise Logging (LGPD/GDPR)
    - Health Check
    - Rate Limiting
    - Security & Compliance
    
    Example:
        >>> config = WorkspaceConfig.from_env()
        >>> workspace = EnterpriseWorkspaceManager(config)
        >>> 
        >>> # Obter manager específico
        >>> gmail = workspace.get_gmail_manager()
        >>> 
        >>> # Health check
        >>> health = await workspace.health_check()
    """
    
    def __init__(self, config: WorkspaceConfig):
        """Inicializar Workspace Manager.
        
        Args:
            config: Configuração do Workspace
        """
        super().__init__()
        self.config = config
        
        # Enterprise Logging
        logging_config = LoggingConfig.from_env()
        logging_config.service_name = "workspace-manager"
        self._logger = CentralizedEnterpriseLogger(logging_config)
        
        # Managers (lazy initialization)
        self._gmail_manager: Optional['GmailManager'] = None
        self._drive_manager: Optional['DriveManager'] = None
        self._calendar_manager: Optional['CalendarManager'] = None
        self._chat_manager: Optional['ChatManager'] = None
        self._meet_manager: Optional['MeetManager'] = None
        self._tasks_manager: Optional['TasksManager'] = None
        self._vault_manager: Optional['VaultManager'] = None
        
        # Log inicialização
        self._logger.info(
            "WorkspaceManager initialized",
            scopes_count=len(config.scopes),
            compliance_mode=config.compliance_mode,
            rate_limit_enabled=config.rate_limit_enabled,
            cache_enabled=config.cache_enabled,
            compliance_tags=["AUDIT", "INITIALIZATION"]
        )
    
    def get_gmail_manager(self) -> 'GmailManager':
        """Obter Gmail Manager (lazy initialization).
        
        Returns:
            GmailManager instance
            
        Raises:
            ValueError: Se não tem scopes para Gmail
        """
        if not self.config.has_api_access('gmail'):
            raise ValueError("No Gmail scopes configured")
        
        if not self._gmail_manager:
            from datametria_common.cloud.workspace.gmail_manager import GmailManager
            self._gmail_manager = GmailManager(self.config, self._logger)
            self._logger.info("GmailManager initialized", compliance_tags=["AUDIT"])
        
        return self._gmail_manager
    
    def get_drive_manager(self) -> 'DriveManager':
        """Obter Drive Manager (lazy initialization).
        
        Returns:
            DriveManager instance
            
        Raises:
            ValueError: Se não tem scopes para Drive
        """
        if not self.config.has_api_access('drive'):
            raise ValueError("No Drive scopes configured")
        
        if not self._drive_manager:
            from datametria_common.cloud.workspace.drive_manager import DriveManager
            self._drive_manager = DriveManager(self.config, self._logger)
            self._logger.info("DriveManager initialized", compliance_tags=["AUDIT"])
        
        return self._drive_manager
    
    def get_calendar_manager(self) -> 'CalendarManager':
        """Obter Calendar Manager (lazy initialization).
        
        Returns:
            CalendarManager instance
            
        Raises:
            ValueError: Se não tem scopes para Calendar
        """
        if not self.config.has_api_access('calendar'):
            raise ValueError("No Calendar scopes configured")
        
        if not self._calendar_manager:
            from datametria_common.cloud.workspace.calendar_manager import CalendarManager
            self._calendar_manager = CalendarManager(self.config, self._logger)
            self._logger.info("CalendarManager initialized", compliance_tags=["AUDIT"])
        
        return self._calendar_manager
    
    def get_chat_manager(self) -> 'ChatManager':
        """Obter Chat Manager (lazy initialization).
        
        Returns:
            ChatManager instance
            
        Raises:
            ValueError: Se não tem scopes para Chat
        """
        if not self.config.has_api_access('chat'):
            raise ValueError("No Chat scopes configured")
        
        if not self._chat_manager:
            from datametria_common.cloud.workspace.chat_manager import ChatManager
            self._chat_manager = ChatManager(self.config, self._logger)
            self._logger.info("ChatManager initialized", compliance_tags=["AUDIT"])
        
        return self._chat_manager
    
    def get_meet_manager(self) -> 'MeetManager':
        """Obter Meet Manager (lazy initialization).
        
        Returns:
            MeetManager instance
            
        Raises:
            ValueError: Se não tem scopes para Meet
        """
        if not self.config.has_api_access('meet'):
            raise ValueError("No Meet scopes configured")
        
        if not self._meet_manager:
            from datametria_common.cloud.workspace.meet_manager import MeetManager
            self._meet_manager = MeetManager(self.config, self._logger)
            self._logger.info("MeetManager initialized", compliance_tags=["AUDIT"])
        
        return self._meet_manager
    
    def get_tasks_manager(self) -> 'TasksManager':
        """Obter Tasks Manager (lazy initialization).
        
        Returns:
            TasksManager instance
            
        Raises:
            ValueError: Se não tem scopes para Tasks
        """
        if not self.config.has_api_access('tasks'):
            raise ValueError("No Tasks scopes configured")
        
        if not self._tasks_manager:
            from datametria_common.cloud.workspace.tasks_manager import TasksManager
            self._tasks_manager = TasksManager(self.config, self._logger)
            self._logger.info("TasksManager initialized", compliance_tags=["AUDIT"])
        
        return self._tasks_manager
    
    def get_vault_manager(self) -> 'VaultManager':
        """Obter Vault Manager (lazy initialization).
        
        Returns:
            VaultManager instance
            
        Raises:
            ValueError: Se não tem scopes para Vault
        """
        if not self.config.has_api_access('vault'):
            raise ValueError("No Vault scopes configured")
        
        if not self._vault_manager:
            from datametria_common.cloud.workspace.vault_manager import VaultManager
            self._vault_manager = VaultManager(self.config, self._logger)
            self._logger.info("VaultManager initialized", compliance_tags=["AUDIT"])
        
        return self._vault_manager
    
    async def health_check(self) -> dict:
        """Health check completo de todos os serviços.
        
        Verifica disponibilidade e latência de cada API configurada.
        
        Returns:
            dict: Status de saúde com:
                - overall_status: 'healthy', 'degraded' ou 'unhealthy'
                - services: dict com status de cada serviço
                - timestamp: timestamp do check
                
        Example:
            >>> health = await workspace.health_check()
            >>> print(health['overall_status'])
            'healthy'
            >>> print(health['services']['gmail']['status'])
            'healthy'
        """
        import time
        
        health_status = {
            'overall_status': 'healthy',
            'services': {},
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'config': {
                'compliance_mode': self.config.compliance_mode,
                'rate_limit_enabled': self.config.rate_limit_enabled,
                'cache_enabled': self.config.cache_enabled
            }
        }
        
        # Mapear APIs disponíveis
        api_mapping = {
            'gmail': (self.config.has_api_access('gmail'), self._gmail_manager),
            'drive': (self.config.has_api_access('drive'), self._drive_manager),
            'calendar': (self.config.has_api_access('calendar'), self._calendar_manager),
            'chat': (self.config.has_api_access('chat'), self._chat_manager),
            'meet': (self.config.has_api_access('meet'), self._meet_manager),
            'tasks': (self.config.has_api_access('tasks'), self._tasks_manager),
            'vault': (self.config.has_api_access('vault'), self._vault_manager)
        }
        
        for service_name, (has_access, manager) in api_mapping.items():
            if not has_access:
                health_status['services'][service_name] = {
                    'status': 'not_configured',
                    'message': 'No scopes configured for this API'
                }
                continue
            
            try:
                start_time = time.time()
                
                # Se manager já foi inicializado, testar conectividade
                if manager is not None:
                    # Teste básico (será implementado em cada manager)
                    await manager.test_connection()
                    latency_ms = (time.time() - start_time) * 1000
                    
                    health_status['services'][service_name] = {
                        'status': 'healthy',
                        'latency_ms': round(latency_ms, 2)
                    }
                else:
                    health_status['services'][service_name] = {
                        'status': 'not_initialized',
                        'message': 'Manager not yet initialized (lazy loading)'
                    }
                
            except Exception as e:
                health_status['services'][service_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['overall_status'] = 'degraded'
                
                self._logger.error(
                    f"Health check failed for {service_name}",
                    service=service_name,
                    error=str(e),
                    compliance_tags=["AUDIT", "ERROR"]
                )
        
        # Log health check
        self._logger.info(
            "Health check completed",
            overall_status=health_status['overall_status'],
            services_checked=len(health_status['services']),
            compliance_tags=["AUDIT", "HEALTH_CHECK"]
        )
        
        return health_status
    
    def get_available_apis(self) -> list:
        """Obter lista de APIs disponíveis (com scopes configurados).
        
        Returns:
            list: Lista de nomes de APIs disponíveis
        """
        apis = []
        for api_name in ['gmail', 'drive', 'calendar', 'chat', 'meet', 'tasks', 'vault']:
            if self.config.has_api_access(api_name):
                apis.append(api_name)
        return apis
    
    def get_initialized_managers(self) -> dict:
        """Obter managers já inicializados.
        
        Returns:
            dict: Mapeamento de API → manager instance
        """
        managers = {}
        
        if self._gmail_manager:
            managers['gmail'] = self._gmail_manager
        if self._drive_manager:
            managers['drive'] = self._drive_manager
        if self._calendar_manager:
            managers['calendar'] = self._calendar_manager
        if self._chat_manager:
            managers['chat'] = self._chat_manager
        if self._meet_manager:
            managers['meet'] = self._meet_manager
        if self._tasks_manager:
            managers['tasks'] = self._tasks_manager
        if self._vault_manager:
            managers['vault'] = self._vault_manager
        
        return managers
    
    def __repr__(self) -> str:
        """Representação string do manager."""
        available = ', '.join(self.get_available_apis())
        return f"<EnterpriseWorkspaceManager(apis=[{available}])>"
