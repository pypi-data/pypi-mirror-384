"""
Vue.js 3 Components DATAMETRIA

Componentes Vue.js 3 enterprise-ready integrados com o Design System DATAMETRIA.
Todos os componentes utilizam os tokens, temas e estilos do Design System.
"""

from .base import *
from .forms import *
from .layout import *
from .navigation import *
from .feedback import *
from .composables import *

__version__ = "1.0.0"
__all__ = [
    # Base Components
    "DatametriaButton",
    "DatametriaIcon", 
    "DatametriaAvatar",
    "DatametriaBadge",
    
    # Form Components
    "DatametriaInput",
    "DatametriaSelect",
    "DatametriaTextarea",
    "DatametriaCheckbox",
    "DatametriaRadio",
    "DatametriaSwitch",
    "DatametriaForm",
    
    # Layout Components
    "DatametriaCard",
    "DatametriaContainer",
    "DatametriaGrid",
    "DatametriaStack",
    
    # Navigation Components
    "DatametriaNavbar",
    "DatametriaTabs",
    "DatametriaBreadcrumb",
    
    # Feedback Components
    "DatametriaModal",
    "DatametriaToast",
    "DatametriaAlert",
    
    # Composables
    "useTheme",
    "useValidation",
    "useAPI",
    "useI18n",
]
