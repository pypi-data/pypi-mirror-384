"""
🪝 React Native Hooks - DATAMETRIA

Hooks customizados integrados ao ecossistema DATAMETRIA.
"""

from typing import Dict, Any, Optional, Callable, Tuple, List
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class ResponsiveBreakpoint:
    """Breakpoint responsivo."""
    name: str
    min_width: int
    max_width: Optional[int] = None


@dataclass
class ValidationRule:
    """Regra de validação."""
    type: str
    value: Any
    message: str


class useResponsive:
    """
    Hook para responsividade integrado ao Design System.
    
    Detecta tamanho de tela e aplica estilos responsivos.
    """
    
    def __init__(self, breakpoints: Optional[Dict[str, int]] = None):
        self.breakpoints = breakpoints or {
            'phone': 0,
            'tablet': 768,
            'desktop': 1024
        }
        self._current_breakpoint = 'phone'
        self._screen_dimensions = {'width': 375, 'height': 812}  # Default iPhone
        
        logger.debug("useResponsive initialized", breakpoints=self.breakpoints)
    
    def get_current_breakpoint(self) -> str:
        """Obter breakpoint atual."""
        width = self._screen_dimensions['width']
        
        if width >= self.breakpoints['desktop']:
            return 'desktop'
        elif width >= self.breakpoints['tablet']:
            return 'tablet'
        else:
            return 'phone'
    
    def is_phone(self) -> bool:
        """Verificar se é telefone."""
        return self.get_current_breakpoint() == 'phone'
    
    def is_tablet(self) -> bool:
        """Verificar se é tablet."""
        return self.get_current_breakpoint() == 'tablet'
    
    def is_desktop(self) -> bool:
        """Verificar se é desktop."""
        return self.get_current_breakpoint() == 'desktop'
    
    def get_responsive_value(self, values: Dict[str, Any]) -> Any:
        """
        Obter valor responsivo baseado no breakpoint atual.
        
        Args:
            values: Valores por breakpoint {'phone': 16, 'tablet': 20, 'desktop': 24}
            
        Returns:
            Any: Valor para o breakpoint atual
        """
        current = self.get_current_breakpoint()
        
        # Fallback hierarchy: current -> phone -> first available
        if current in values:
            return values[current]
        elif 'phone' in values:
            return values['phone']
        else:
            return next(iter(values.values()))
    
    def get_screen_dimensions(self) -> Dict[str, int]:
        """Obter dimensões da tela."""
        return self._screen_dimensions.copy()
    
    def update_dimensions(self, width: int, height: int) -> None:
        """Atualizar dimensões da tela."""
        self._screen_dimensions = {'width': width, 'height': height}
        logger.debug("Screen dimensions updated", width=width, height=height)


class useDarkMode:
    """
    Hook para Dark Mode integrado ao DarkModeManager.
    
    Gerencia estado do tema escuro com persistência.
    """
    
    def __init__(self, initial_mode: str = 'auto'):
        self._mode = initial_mode
        self._is_dark = False
        self._system_dark = False
        
        logger.debug("useDarkMode initialized", initial_mode=initial_mode)
    
    def is_dark_mode(self) -> bool:
        """Verificar se está em modo escuro."""
        if self._mode == 'auto':
            return self._system_dark
        return self._mode == 'dark'
    
    def toggle_dark_mode(self) -> bool:
        """Alternar modo escuro."""
        if self._mode == 'auto':
            # Se auto, definir explicitamente o oposto do sistema
            self._mode = 'light' if self._system_dark else 'dark'
        else:
            # Alternar entre light e dark
            self._mode = 'dark' if self._mode == 'light' else 'light'
        
        new_state = self.is_dark_mode()
        logger.info("Dark mode toggled", mode=self._mode, is_dark=new_state)
        return new_state
    
    def set_mode(self, mode: str) -> None:
        """Definir modo específico."""
        if mode not in ['light', 'dark', 'auto']:
            raise ValueError("Mode must be 'light', 'dark', or 'auto'")
        
        self._mode = mode
        logger.info("Dark mode set", mode=mode)
    
    def get_mode(self) -> str:
        """Obter modo atual."""
        return self._mode
    
    def update_system_preference(self, is_dark: bool) -> None:
        """Atualizar preferência do sistema."""
        self._system_dark = is_dark
        logger.debug("System dark mode preference updated", is_dark=is_dark)


class useTheme:
    """
    Hook para tema integrado ao Design System DATAMETRIA.
    
    Fornece tokens de design e utilitários de tema.
    """
    
    def __init__(self, provider_theme: Optional[Dict[str, Any]] = None):
        self._theme = provider_theme or self._get_default_theme()
        
        logger.debug("useTheme initialized")
    
    def _get_default_theme(self) -> Dict[str, Any]:
        """Tema padrão."""
        return {
            'colors': {
                'primary': '#2196F3',
                'secondary': '#9C27B0',
                'success': '#4CAF50',
                'warning': '#FF9800',
                'error': '#F44336',
                'background': '#FFFFFF',
                'surface': '#F5F5F5',
                'text': '#212121'
            },
            'spacing': {'xs': 4, 'sm': 8, 'md': 16, 'lg': 24, 'xl': 32},
            'typography': {
                'fontSize': {'xs': 12, 'sm': 14, 'base': 16, 'lg': 18, 'xl': 20}
            }
        }
    
    def get_color(self, color_name: str) -> str:
        """Obter cor do tema."""
        return self._theme.get('colors', {}).get(color_name, '#000000')
    
    def get_spacing(self, size: str) -> int:
        """Obter espaçamento do tema."""
        return self._theme.get('spacing', {}).get(size, 16)
    
    def get_font_size(self, size: str) -> int:
        """Obter tamanho de fonte do tema."""
        return self._theme.get('typography', {}).get('fontSize', {}).get(size, 16)
    
    def get_theme(self) -> Dict[str, Any]:
        """Obter tema completo."""
        return self._theme.copy()
    
    def update_theme(self, new_theme: Dict[str, Any]) -> None:
        """Atualizar tema."""
        self._theme = {**self._theme, **new_theme}
        logger.info("Theme updated")


class useNavigation:
    """
    Hook para navegação React Native.
    
    Abstração para navegação entre telas.
    """
    
    def __init__(self):
        self._navigation_stack: List[str] = []
        self._current_route = 'Home'
        
        logger.debug("useNavigation initialized")
    
    def navigate(self, route_name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Navegar para uma tela.
        
        Args:
            route_name: Nome da rota
            params: Parâmetros da navegação
        """
        self._navigation_stack.append(self._current_route)
        self._current_route = route_name
        
        logger.info("Navigation", to=route_name, params=params)
    
    def go_back(self) -> bool:
        """
        Voltar para tela anterior.
        
        Returns:
            bool: True se conseguiu voltar
        """
        if self._navigation_stack:
            previous_route = self._navigation_stack.pop()
            self._current_route = previous_route
            logger.info("Navigation back", to=previous_route)
            return True
        return False
    
    def reset(self, route_name: str) -> None:
        """Resetar stack de navegação."""
        self._navigation_stack.clear()
        self._current_route = route_name
        logger.info("Navigation reset", to=route_name)
    
    def get_current_route(self) -> str:
        """Obter rota atual."""
        return self._current_route
    
    def can_go_back(self) -> bool:
        """Verificar se pode voltar."""
        return len(self._navigation_stack) > 0


class useValidation:
    """
    Hook para validação de formulários.
    
    Sistema de validação integrado aos componentes DATAMETRIA.
    """
    
    def __init__(self, schema: Optional[Dict[str, List[ValidationRule]]] = None):
        self.schema = schema or {}
        self._errors: Dict[str, str] = {}
        self._touched: Dict[str, bool] = {}
        
        logger.debug("useValidation initialized", fields=list(self.schema.keys()))
    
    def validate_field(self, field_name: str, value: Any) -> Optional[str]:
        """
        Validar campo específico.
        
        Args:
            field_name: Nome do campo
            value: Valor a validar
            
        Returns:
            Optional[str]: Mensagem de erro ou None
        """
        if field_name not in self.schema:
            return None
        
        rules = self.schema[field_name]
        
        for rule in rules:
            error = self._apply_rule(rule, value)
            if error:
                self._errors[field_name] = error
                return error
        
        # Remove erro se validação passou
        if field_name in self._errors:
            del self._errors[field_name]
        
        return None
    
    def _apply_rule(self, rule: ValidationRule, value: Any) -> Optional[str]:
        """Aplicar regra de validação."""
        if rule.type == 'required':
            if not value or (isinstance(value, str) and not value.strip()):
                return rule.message
        
        elif rule.type == 'min_length':
            if isinstance(value, str) and len(value) < rule.value:
                return rule.message
        
        elif rule.type == 'max_length':
            if isinstance(value, str) and len(value) > rule.value:
                return rule.message
        
        elif rule.type == 'email':
            if isinstance(value, str) and '@' not in value:
                return rule.message
        
        elif rule.type == 'pattern':
            import re
            if isinstance(value, str) and not re.match(rule.value, value):
                return rule.message
        
        return None
    
    def validate_all(self, values: Dict[str, Any]) -> Dict[str, str]:
        """
        Validar todos os campos.
        
        Args:
            values: Valores dos campos
            
        Returns:
            Dict[str, str]: Erros por campo
        """
        errors = {}
        
        for field_name, field_value in values.items():
            error = self.validate_field(field_name, field_value)
            if error:
                errors[field_name] = error
        
        return errors
    
    def get_errors(self) -> Dict[str, str]:
        """Obter todos os erros."""
        return self._errors.copy()
    
    def get_error(self, field_name: str) -> Optional[str]:
        """Obter erro de campo específico."""
        return self._errors.get(field_name)
    
    def has_errors(self) -> bool:
        """Verificar se há erros."""
        return len(self._errors) > 0
    
    def clear_errors(self) -> None:
        """Limpar todos os erros."""
        self._errors.clear()
        logger.debug("Validation errors cleared")
    
    def set_touched(self, field_name: str, touched: bool = True) -> None:
        """Marcar campo como tocado."""
        self._touched[field_name] = touched
    
    def is_touched(self, field_name: str) -> bool:
        """Verificar se campo foi tocado."""
        return self._touched.get(field_name, False)


class useAPI:
    """
    Hook para chamadas de API integrado ao sistema DATAMETRIA.
    
    Gerencia estado de loading, erro e cache.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or 'https://api.datametria.io'
        self._loading = False
        self._error: Optional[str] = None
        self._cache: Dict[str, Any] = {}
        
        logger.debug("useAPI initialized", base_url=self.base_url)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fazer requisição GET.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da query
            
        Returns:
            Dict[str, Any]: Resposta da API
        """
        cache_key = f"GET:{endpoint}:{str(params)}"
        
        if cache_key in self._cache:
            logger.debug("API cache hit", endpoint=endpoint)
            return self._cache[cache_key]
        
        self._loading = True
        self._error = None
        
        try:
            # Simular chamada de API
            response = {'data': f'Mock data for {endpoint}', 'success': True}
            self._cache[cache_key] = response
            
            logger.info("API GET success", endpoint=endpoint)
            return response
            
        except Exception as e:
            self._error = str(e)
            logger.error("API GET error", endpoint=endpoint, error=str(e))
            return {'error': str(e), 'success': False}
        
        finally:
            self._loading = False
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fazer requisição POST.
        
        Args:
            endpoint: Endpoint da API
            data: Dados a enviar
            
        Returns:
            Dict[str, Any]: Resposta da API
        """
        self._loading = True
        self._error = None
        
        try:
            # Simular chamada de API
            response = {'data': f'Created via {endpoint}', 'success': True}
            
            # Invalidar cache relacionado
            self._invalidate_cache(endpoint)
            
            logger.info("API POST success", endpoint=endpoint)
            return response
            
        except Exception as e:
            self._error = str(e)
            logger.error("API POST error", endpoint=endpoint, error=str(e))
            return {'error': str(e), 'success': False}
        
        finally:
            self._loading = False
    
    def _invalidate_cache(self, endpoint: str) -> None:
        """Invalidar cache relacionado ao endpoint."""
        keys_to_remove = [key for key in self._cache.keys() if endpoint in key]
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.debug("Cache invalidated", endpoint=endpoint, keys_removed=len(keys_to_remove))
    
    def is_loading(self) -> bool:
        """Verificar se está carregando."""
        return self._loading
    
    def get_error(self) -> Optional[str]:
        """Obter erro atual."""
        return self._error
    
    def clear_error(self) -> None:
        """Limpar erro."""
        self._error = None
    
    def clear_cache(self) -> None:
        """Limpar cache."""
        self._cache.clear()
        logger.info("API cache cleared")


# Factory functions para hooks
def create_responsive_hook(**kwargs) -> useResponsive:
    """Criar hook de responsividade."""
    return useResponsive(**kwargs)

def create_dark_mode_hook(**kwargs) -> useDarkMode:
    """Criar hook de dark mode."""
    return useDarkMode(**kwargs)

def create_theme_hook(**kwargs) -> useTheme:
    """Criar hook de tema."""
    return useTheme(**kwargs)

def create_navigation_hook(**kwargs) -> useNavigation:
    """Criar hook de navegação."""
    return useNavigation(**kwargs)

def create_validation_hook(**kwargs) -> useValidation:
    """Criar hook de validação."""
    return useValidation(**kwargs)

def create_api_hook(**kwargs) -> useAPI:
    """Criar hook de API."""
    return useAPI(**kwargs)
