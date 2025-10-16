"""
📱 React Native Components - DATAMETRIA Common Libraries

Biblioteca cross-platform React Native + TypeScript seguindo padrões DATAMETRIA.

Features:
    - Design System: Componentes com 500+ tokens
    - Cross-platform UI: iOS e Android nativos
    - Responsive Design: Phone, Tablet, Foldable
    - Dark Mode: Suporte completo com transições
    - Navigation: Stack, tab, drawer integrada
    - State Management: Zustand integration
    - Offline Support: Persistência de dados
    - Push Notifications: Firebase + native
    - Biometric Auth: Fingerprint + Face ID
    - TypeScript: Type safety completo

Integration:
    - Design System: Tokens e componentes unificados
    - Dark Mode Manager: Sincronização automática
    - Configuration: BaseConfig para configurações
    - Security: Integração com SecurityManager
    - Logging: Logging enterprise estruturado

Author: DATAMETRIA Enterprise Team
Version: 1.0.0
"""

from .provider import DatametriaProvider, ReactNativeConfig
from .components import *
from .hooks import *
from .navigation import *
from .theme import *
from .utils import *

__all__ = [
    # Core
    "DatametriaProvider",
    "ReactNativeConfig",
    
    # Components
    "DatametriaScreen",
    "DatametriaButton", 
    "DatametriaInput",
    "DatametriaCard",
    "DatametriaList",
    "DatametriaModal",
    "DatametriaForm",
    "DatametriaHeader",
    
    # Component Factories
    "create_screen",
    "create_button",
    "create_input",
    "create_card",
    "create_list",
    "create_modal",
    "create_form",
    "create_header",
    
    # Hooks
    "useResponsive",
    "useDarkMode",
    "useTheme",
    "useNavigation",
    "useValidation",
    "useAPI",
    
    # Hook Factories
    "create_responsive_hook",
    "create_dark_mode_hook",
    "create_theme_hook",
    "create_navigation_hook",
    "create_validation_hook",
    "create_api_hook",
    
    # Navigation
    "DatametriaNavigator",
    "StackNavigator",
    "TabNavigator",
    "DrawerNavigator",
    "NavigationService",
    "navigation_service",
    "RouteConfig",
    "NavigationType",
    
    # Navigation Factories
    "create_stack_navigator",
    "create_tab_navigator",
    "create_drawer_navigator",
    "create_route_config",
    
    # Theme
    "DatametriaTheme",
    "ThemeProvider",
    "ThemeMode",
    "ColorPalette",
    "theme_provider",
    
    # Theme Factories
    "create_theme",
    "create_light_theme",
    "create_dark_theme",
    "get_current_theme",
    "set_global_theme",
    
    # Utils
    "DeviceUtils",
    "ValidationUtils",
    "FormatUtils",
    "StorageUtils",
    "PerformanceUtils",
    "storage_utils",
    "performance_utils",
    "measure_performance",
    
    # Enums
    "DeviceType",
    "Platform"
]
