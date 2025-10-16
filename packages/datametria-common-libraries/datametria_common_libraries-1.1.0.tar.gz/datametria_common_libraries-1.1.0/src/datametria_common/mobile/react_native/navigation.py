"""
🧭 React Native Navigation - DATAMETRIA

Sistema de navegação integrado aos padrões DATAMETRIA.
"""

from typing import Dict, Any, Optional, List, Callable, Union
import structlog
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger(__name__)


class NavigationType(Enum):
    """Tipos de navegação."""
    STACK = "stack"
    TAB = "tab"
    DRAWER = "drawer"
    MODAL = "modal"


@dataclass
class RouteConfig:
    """Configuração de rota."""
    name: str
    component: str
    title: Optional[str] = None
    icon: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    auth_required: bool = False
    header_shown: bool = True


@dataclass
class NavigationOptions:
    """Opções de navegação."""
    header_title: Optional[str] = None
    header_shown: bool = True
    header_back_title: Optional[str] = None
    header_style: Optional[Dict[str, Any]] = None
    tab_bar_icon: Optional[str] = None
    tab_bar_label: Optional[str] = None
    drawer_icon: Optional[str] = None
    drawer_label: Optional[str] = None


class DatametriaNavigator:
    """
    Navegador principal DATAMETRIA.
    
    Abstração para React Navigation com padrões DATAMETRIA.
    """
    
    def __init__(
        self,
        navigation_type: NavigationType,
        routes: List[RouteConfig],
        initial_route: str,
        theme_aware: bool = True,
        **options
    ):
        self.navigation_type = navigation_type
        self.routes = {route.name: route for route in routes}
        self.initial_route = initial_route
        self.theme_aware = theme_aware
        self.options = options
        
        # Estado da navegação
        self._current_route = initial_route
        self._navigation_stack: List[str] = [initial_route]
        self._route_params: Dict[str, Dict[str, Any]] = {}
        
        logger.info(
            "DatametriaNavigator initialized",
            type=navigation_type.value,
            routes_count=len(routes),
            initial_route=initial_route
        )
    
    def get_navigation_config(self) -> Dict[str, Any]:
        """Obter configuração de navegação para React Native."""
        base_config = {
            'type': self.navigation_type.value,
            'initialRouteName': self.initial_route,
            'routes': self._build_routes_config(),
            'themeAware': self.theme_aware
        }
        
        # Configurações específicas por tipo
        if self.navigation_type == NavigationType.STACK:
            base_config.update(self._get_stack_config())
        elif self.navigation_type == NavigationType.TAB:
            base_config.update(self._get_tab_config())
        elif self.navigation_type == NavigationType.DRAWER:
            base_config.update(self._get_drawer_config())
        
        return {**base_config, **self.options}
    
    def _build_routes_config(self) -> List[Dict[str, Any]]:
        """Construir configuração das rotas."""
        routes_config = []
        
        for route in self.routes.values():
            route_config = {
                'name': route.name,
                'component': route.component,
                'options': self._build_route_options(route)
            }
            
            if route.params:
                route_config['initialParams'] = route.params
            
            routes_config.append(route_config)
        
        return routes_config
    
    def _build_route_options(self, route: RouteConfig) -> Dict[str, Any]:
        """Construir opções da rota."""
        options = {
            'headerShown': route.header_shown,
            'authRequired': route.auth_required
        }
        
        if route.title:
            options['title'] = route.title
            options['headerTitle'] = route.title
        
        if route.icon:
            options['tabBarIcon'] = route.icon
            options['drawerIcon'] = route.icon
        
        return options
    
    def _get_stack_config(self) -> Dict[str, Any]:
        """Configuração para Stack Navigator."""
        return {
            'screenOptions': {
                'headerStyle': {
                    'backgroundColor': '#2196F3'
                },
                'headerTintColor': '#FFFFFF',
                'headerTitleStyle': {
                    'fontWeight': 'bold'
                },
                'cardStyle': {
                    'backgroundColor': '#FFFFFF'
                },
                'animationEnabled': True,
                'gestureEnabled': True
            }
        }
    
    def _get_tab_config(self) -> Dict[str, Any]:
        """Configuração para Tab Navigator."""
        return {
            'screenOptions': {
                'tabBarStyle': {
                    'backgroundColor': '#FFFFFF',
                    'borderTopColor': '#E0E0E0',
                    'height': 60
                },
                'tabBarActiveTintColor': '#2196F3',
                'tabBarInactiveTintColor': '#757575',
                'tabBarLabelStyle': {
                    'fontSize': 12,
                    'fontWeight': '500'
                },
                'headerShown': False
            },
            'tabBarPosition': 'bottom'
        }
    
    def _get_drawer_config(self) -> Dict[str, Any]:
        """Configuração para Drawer Navigator."""
        return {
            'screenOptions': {
                'drawerStyle': {
                    'backgroundColor': '#FFFFFF',
                    'width': 280
                },
                'drawerActiveTintColor': '#2196F3',
                'drawerInactiveTintColor': '#757575',
                'drawerLabelStyle': {
                    'fontSize': 16,
                    'fontWeight': '500'
                }
            },
            'drawerPosition': 'left'
        }
    
    def navigate(self, route_name: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Navegar para uma rota.
        
        Args:
            route_name: Nome da rota
            params: Parâmetros da navegação
            
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        if route_name not in self.routes:
            logger.error("Route not found", route_name=route_name)
            return False
        
        route = self.routes[route_name]
        
        # Verificar autenticação se necessário
        if route.auth_required and not self._is_authenticated():
            logger.warning("Navigation blocked - authentication required", route=route_name)
            return False
        
        # Atualizar estado
        self._navigation_stack.append(self._current_route)
        self._current_route = route_name
        
        if params:
            self._route_params[route_name] = params
        
        logger.info("Navigation", to=route_name, params=params)
        return True
    
    def go_back(self) -> bool:
        """
        Voltar para rota anterior.
        
        Returns:
            bool: True se conseguiu voltar
        """
        if len(self._navigation_stack) <= 1:
            return False
        
        previous_route = self._navigation_stack.pop()
        self._current_route = previous_route
        
        logger.info("Navigation back", to=previous_route)
        return True
    
    def reset(self, route_name: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Resetar navegação para uma rota.
        
        Args:
            route_name: Nome da rota
            params: Parâmetros da navegação
            
        Returns:
            bool: True se reset foi bem-sucedido
        """
        if route_name not in self.routes:
            logger.error("Route not found for reset", route_name=route_name)
            return False
        
        self._navigation_stack = [route_name]
        self._current_route = route_name
        
        if params:
            self._route_params[route_name] = params
        
        logger.info("Navigation reset", to=route_name)
        return True
    
    def get_current_route(self) -> str:
        """Obter rota atual."""
        return self._current_route
    
    def get_route_params(self, route_name: Optional[str] = None) -> Dict[str, Any]:
        """Obter parâmetros da rota."""
        target_route = route_name or self._current_route
        return self._route_params.get(target_route, {})
    
    def can_go_back(self) -> bool:
        """Verificar se pode voltar."""
        return len(self._navigation_stack) > 1
    
    def _is_authenticated(self) -> bool:
        """Verificar se usuário está autenticado."""
        # Integrar com AuthManager quando disponível
        return True  # Placeholder
    
    def add_route(self, route: RouteConfig) -> None:
        """Adicionar nova rota."""
        self.routes[route.name] = route
        logger.info("Route added", route_name=route.name)
    
    def remove_route(self, route_name: str) -> bool:
        """Remover rota."""
        if route_name in self.routes:
            del self.routes[route_name]
            logger.info("Route removed", route_name=route_name)
            return True
        return False
    
    def get_navigation_state(self) -> Dict[str, Any]:
        """Obter estado atual da navegação."""
        return {
            'current_route': self._current_route,
            'navigation_stack': self._navigation_stack.copy(),
            'route_params': self._route_params.copy(),
            'can_go_back': self.can_go_back()
        }


class StackNavigator(DatametriaNavigator):
    """Navigator específico para Stack."""
    
    def __init__(self, routes: List[RouteConfig], initial_route: str, **options):
        super().__init__(NavigationType.STACK, routes, initial_route, **options)


class TabNavigator(DatametriaNavigator):
    """Navigator específico para Tabs."""
    
    def __init__(self, routes: List[RouteConfig], initial_route: str, **options):
        super().__init__(NavigationType.TAB, routes, initial_route, **options)
    
    def switch_tab(self, tab_name: str) -> bool:
        """
        Trocar de aba.
        
        Args:
            tab_name: Nome da aba
            
        Returns:
            bool: True se troca foi bem-sucedida
        """
        if tab_name not in self.routes:
            return False
        
        self._current_route = tab_name
        logger.info("Tab switched", to=tab_name)
        return True


class DrawerNavigator(DatametriaNavigator):
    """Navigator específico para Drawer."""
    
    def __init__(self, routes: List[RouteConfig], initial_route: str, **options):
        super().__init__(NavigationType.DRAWER, routes, initial_route, **options)
        self._drawer_open = False
    
    def toggle_drawer(self) -> bool:
        """Alternar drawer."""
        self._drawer_open = not self._drawer_open
        logger.info("Drawer toggled", open=self._drawer_open)
        return self._drawer_open
    
    def open_drawer(self) -> None:
        """Abrir drawer."""
        self._drawer_open = True
        logger.info("Drawer opened")
    
    def close_drawer(self) -> None:
        """Fechar drawer."""
        self._drawer_open = False
        logger.info("Drawer closed")
    
    def is_drawer_open(self) -> bool:
        """Verificar se drawer está aberto."""
        return self._drawer_open


class NavigationService:
    """
    Serviço de navegação global DATAMETRIA.
    
    Permite navegação de qualquer lugar da aplicação.
    """
    
    def __init__(self):
        self._navigator: Optional[DatametriaNavigator] = None
        self._navigation_listeners: List[Callable[[str, str], None]] = []
        
        logger.debug("NavigationService initialized")
    
    def set_navigator(self, navigator: DatametriaNavigator) -> None:
        """Definir navigator principal."""
        self._navigator = navigator
        logger.info("Navigator set", type=navigator.navigation_type.value)
    
    def navigate(self, route_name: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Navegar usando o navigator principal."""
        if not self._navigator:
            logger.error("No navigator set")
            return False
        
        old_route = self._navigator.get_current_route()
        success = self._navigator.navigate(route_name, params)
        
        if success:
            self._notify_listeners(old_route, route_name)
        
        return success
    
    def go_back(self) -> bool:
        """Voltar usando o navigator principal."""
        if not self._navigator:
            return False
        
        old_route = self._navigator.get_current_route()
        success = self._navigator.go_back()
        
        if success:
            new_route = self._navigator.get_current_route()
            self._notify_listeners(old_route, new_route)
        
        return success
    
    def reset(self, route_name: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Resetar navegação."""
        if not self._navigator:
            return False
        
        old_route = self._navigator.get_current_route()
        success = self._navigator.reset(route_name, params)
        
        if success:
            self._notify_listeners(old_route, route_name)
        
        return success
    
    def get_current_route(self) -> Optional[str]:
        """Obter rota atual."""
        return self._navigator.get_current_route() if self._navigator else None
    
    def add_navigation_listener(self, listener: Callable[[str, str], None]) -> None:
        """
        Adicionar listener de navegação.
        
        Args:
            listener: Função que recebe (from_route, to_route)
        """
        self._navigation_listeners.append(listener)
        logger.debug("Navigation listener added")
    
    def remove_navigation_listener(self, listener: Callable[[str, str], None]) -> None:
        """Remover listener de navegação."""
        if listener in self._navigation_listeners:
            self._navigation_listeners.remove(listener)
            logger.debug("Navigation listener removed")
    
    def _notify_listeners(self, from_route: str, to_route: str) -> None:
        """Notificar listeners sobre mudança de rota."""
        for listener in self._navigation_listeners:
            try:
                listener(from_route, to_route)
            except Exception as e:
                logger.error("Navigation listener error", error=str(e))


# Instância global do serviço de navegação
navigation_service = NavigationService()


# Factory functions
def create_stack_navigator(routes: List[RouteConfig], initial_route: str, **options) -> StackNavigator:
    """Criar Stack Navigator."""
    return StackNavigator(routes, initial_route, **options)

def create_tab_navigator(routes: List[RouteConfig], initial_route: str, **options) -> TabNavigator:
    """Criar Tab Navigator."""
    return TabNavigator(routes, initial_route, **options)

def create_drawer_navigator(routes: List[RouteConfig], initial_route: str, **options) -> DrawerNavigator:
    """Criar Drawer Navigator."""
    return DrawerNavigator(routes, initial_route, **options)

def create_route_config(
    name: str,
    component: str,
    title: Optional[str] = None,
    icon: Optional[str] = None,
    **kwargs
) -> RouteConfig:
    """Criar configuração de rota."""
    return RouteConfig(name=name, component=component, title=title, icon=icon, **kwargs)
