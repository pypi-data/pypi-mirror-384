"""
Status Badge Component DATAMETRIA

Badge com estados semânticos para status de processos, serviços e entidades.
"""

from dataclasses import dataclass
from enum import Enum


class StatusType(Enum):
    """Tipos de status"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class BadgeSize(Enum):
    """Tamanhos do badge"""
    XS = "xs"
    SM = "sm"
    MD = "md"


@dataclass
class DatametriaStatusBadge:
    """Componente de Status Badge"""
    status: StatusType = StatusType.INFO
    size: BadgeSize = BadgeSize.SM
    show_icon: bool = True
    
    STATUS_CONFIG = {
        StatusType.SUCCESS: {"label": "Sucesso", "icon": "check_circle", "color": "green"},
        StatusType.ERROR: {"label": "Erro", "icon": "error", "color": "red"},
        StatusType.WARNING: {"label": "Aviso", "icon": "warning", "color": "yellow"},
        StatusType.INFO: {"label": "Info", "icon": "info", "color": "blue"},
        StatusType.PENDING: {"label": "Pendente", "icon": "schedule", "color": "gray"},
        StatusType.RUNNING: {"label": "Executando", "icon": "play_circle", "color": "blue"},
        StatusType.STOPPED: {"label": "Parado", "icon": "stop_circle", "color": "gray"},
        StatusType.HEALTHY: {"label": "Saudável", "icon": "check_circle", "color": "green"},
        StatusType.UNHEALTHY: {"label": "Problema", "icon": "error", "color": "red"},
    }
    
    def get_label(self) -> str:
        """Retorna label do status"""
        return self.STATUS_CONFIG[self.status]["label"]
    
    def get_icon(self) -> str:
        """Retorna ícone do status"""
        return self.STATUS_CONFIG[self.status]["icon"]
    
    def get_color(self) -> str:
        """Retorna cor do status"""
        return self.STATUS_CONFIG[self.status]["color"]
    
    def get_classes(self) -> str:
        """Retorna classes CSS"""
        return f"dm-status-badge dm-status-badge--{self.status.value} dm-status-badge--{self.size.value}"
    
    def get_css(self) -> str:
        """Retorna CSS do componente"""
        return """
/* Status Badge */
.dm-status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Sizes */
.dm-status-badge--xs { padding: 0.125rem 0.5rem; font-size: 0.625rem; }
.dm-status-badge--sm { padding: 0.125rem 0.625rem; font-size: 0.75rem; }
.dm-status-badge--md { padding: 0.25rem 0.75rem; font-size: 0.875rem; }

/* Colors */
.dm-status-badge--success { background-color: #dcfce7; color: #166534; }
.dm-status-badge--error { background-color: #fee2e2; color: #991b1b; }
.dm-status-badge--warning { background-color: #fef3c7; color: #92400e; }
.dm-status-badge--info { background-color: #dbeafe; color: #1e40af; }
.dm-status-badge--pending { background-color: #f3f4f6; color: #374151; }
.dm-status-badge--running { background-color: #dbeafe; color: #1e40af; }
.dm-status-badge--stopped { background-color: #f3f4f6; color: #374151; }
.dm-status-badge--healthy { background-color: #dcfce7; color: #166534; }
.dm-status-badge--unhealthy { background-color: #fee2e2; color: #991b1b; }

.dm-status-badge i { font-size: 0.75rem; margin-right: 0.25rem; }
"""
    
    def to_html(self) -> str:
        """Gera HTML do badge"""
        icon_html = f'<i class="material-icons">{self.get_icon()}</i>' if self.show_icon else ''
        return f'<span class="{self.get_classes()}">{icon_html}{self.get_label()}</span>'


__all__ = ["DatametriaStatusBadge", "StatusType", "BadgeSize"]
