"""
Componentes do Design System DATAMETRIA

Biblioteca completa de 48 componentes reutilizáveis seguindo os padrões
DATAMETRIA com suporte a temas, acessibilidade e responsividade.

Total: 56 componentes
- Base: 5 componentes (Button, Icon, Avatar, Badge, Logo)
- Brazilian Inputs: 4 componentes (CEP, CNPJ, Phone, CPF)
- Status & Metrics: 2 componentes (StatusBadge, MetricCard)
- Entity: 1 componente (EntityCard)
- Forms: 7 componentes
- Layout: 5 componentes
- Navigation: 5 componentes
- Feedback: 6 componentes
- Data Display: 8 componentes
- Advanced Input: 6 componentes
- Overlay: 5 componentes
- Advanced: 2 componentes (Calendar, Advanced Table)
"""

from .base import *
from .logo import DatametriaLogo, LogoVariant, LogoSize
from .forms import *
from .layout import *
from .navigation import *
from .feedback import *
from .data_display import *
from .input_advanced import *
from .overlay import *
from .advanced import *
from .status_badge import DatametriaStatusBadge, StatusType, BadgeSize
from .metric_card import DatametriaMetricCard, MetricColor
from .br_inputs import (
    DatametriaCEPInput,
    DatametriaCNPJInput,
    DatametriaPhoneInput,
    DatametriaCPFInput,
)
from .entity_card import DatametriaEntityCard, EntityType

__all__ = [
    # Base Components (5)
    "DatametriaButton",
    "DatametriaIcon",
    "DatametriaAvatar",
    "DatametriaBadge",
    "DatametriaLogo",
    "LogoVariant",
    "LogoSize",
    
    # Form Components (7)
    "DatametriaInput",
    "DatametriaTextarea",
    "DatametriaSelect",
    "DatametriaCheckbox",
    "DatametriaRadio",
    "DatametriaSwitch",
    "DatametriaForm",
    
    # Layout Components (5)
    "DatametriaCard",
    "DatametriaContainer",
    "DatametriaGrid",
    "DatametriaStack",
    "DatametriaDivider",
    
    # Navigation Components (5)
    "DatametriaNavbar",
    "DatametriaSidebar", 
    "DatametriaBreadcrumb",
    "DatametriaTabs",
    "DatametriaPagination",
    
    # Feedback Components (6)
    "DatametriaModal",
    "DatametriaToast",
    "DatametriaAlert",
    "DatametriaProgress",
    "DatametriaSpinner",
    "DatametriaTooltip",
    
    # Data Display Components (8)
    "DatametriaTable",
    "DatametriaList",
    "DatametriaAccordion",
    "DatametriaTimeline",
    "DatametriaCarousel",
    "DatametriaImage",
    "DatametriaSkeleton",
    "DatametriaEmptyState",
    
    # Advanced Input Components (6)
    "DatametriaDatePicker",
    "DatametriaTimePicker",
    "DatametriaFileUpload",
    "DatametriaColorPicker",
    "DatametriaAutocomplete",
    "DatametriaRichTextEditor",
    
    # Overlay Components (5)
    "DatametriaDropdown",
    "DatametriaDrawer",
    "DatametriaPopover",
    "DatametriaStepper",
    "DatametriaCommandPalette",
    
    # Advanced Components (2)
    "DatametriaCalendar",
    "DatametriaAdvancedTable",
    
    # Status & Metrics (2)
    "DatametriaStatusBadge",
    "StatusType",
    "BadgeSize",
    "DatametriaMetricCard",
    "MetricColor",
    
    # Brazilian Inputs (4)
    "DatametriaCEPInput",
    "DatametriaCNPJInput",
    "DatametriaPhoneInput",
    "DatametriaCPFInput",
    
    # Entity (1)
    "DatametriaEntityCard",
    "EntityType",
]
