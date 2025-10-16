"""
🎨 React Native Theme - DATAMETRIA

Sistema de tema integrado ao Design System DATAMETRIA.
"""

from typing import Dict, Any, Optional, Union, List
import structlog
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger(__name__)


class ThemeMode(Enum):
    """Modos de tema."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass
class ColorPalette:
    """Paleta de cores."""
    primary: str
    secondary: str
    success: str
    warning: str
    error: str
    info: str
    background: str
    surface: str
    text: str
    text_secondary: str
    border: str
    disabled: str


@dataclass
class Typography:
    """Configuração de tipografia."""
    font_family: str
    font_sizes: Dict[str, int]
    line_heights: Dict[str, float]
    font_weights: Dict[str, Union[str, int]]
    letter_spacing: Dict[str, float]


@dataclass
class Spacing:
    """Sistema de espaçamento."""
    base: int
    scale: List[int]
    
    def get(self, size: str) -> int:
        """Obter espaçamento por nome."""
        size_map = {
            'xs': self.scale[0] if self.scale else self.base // 2,
            'sm': self.scale[1] if len(self.scale) > 1 else self.base,
            'md': self.scale[2] if len(self.scale) > 2 else self.base * 2,
            'lg': self.scale[3] if len(self.scale) > 3 else self.base * 3,
            'xl': self.scale[4] if len(self.scale) > 4 else self.base * 4,
            '2xl': self.scale[5] if len(self.scale) > 5 else self.base * 6
        }
        return size_map.get(size, self.base)


@dataclass
class BorderRadius:
    """Sistema de border radius."""
    none: int = 0
    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 16
    full: int = 9999


@dataclass
class Shadows:
    """Sistema de sombras."""
    sm: Dict[str, Any]
    md: Dict[str, Any]
    lg: Dict[str, Any]
    xl: Dict[str, Any]


class DatametriaTheme:
    """
    Tema principal DATAMETRIA para React Native.
    
    Integra Design System com tokens responsivos e dark mode.
    """
    
    def __init__(
        self,
        mode: ThemeMode = ThemeMode.LIGHT,
        colors: Optional[ColorPalette] = None,
        typography: Optional[Typography] = None,
        spacing: Optional[Spacing] = None,
        border_radius: Optional[BorderRadius] = None,
        shadows: Optional[Shadows] = None,
        custom_tokens: Optional[Dict[str, Any]] = None
    ):
        self.mode = mode
        self.colors = colors or self._get_default_colors()
        self.typography = typography or self._get_default_typography()
        self.spacing = spacing or self._get_default_spacing()
        self.border_radius = border_radius or BorderRadius()
        self.shadows = shadows or self._get_default_shadows()
        self.custom_tokens = custom_tokens or {}
        
        logger.info("DatametriaTheme initialized", mode=mode.value)
    
    def _get_default_colors(self) -> ColorPalette:
        """Cores padrão DATAMETRIA."""
        if self.mode == ThemeMode.DARK:
            return ColorPalette(
                primary="#2196F3",
                secondary="#9C27B0",
                success="#4CAF50",
                warning="#FF9800",
                error="#F44336",
                info="#2196F3",
                background="#121212",
                surface="#1E1E1E",
                text="#FFFFFF",
                text_secondary="#B3B3B3",
                border="#333333",
                disabled="#666666"
            )
        else:
            return ColorPalette(
                primary="#2196F3",
                secondary="#9C27B0",
                success="#4CAF50",
                warning="#FF9800",
                error="#F44336",
                info="#2196F3",
                background="#FFFFFF",
                surface="#F5F5F5",
                text="#212121",
                text_secondary="#757575",
                border="#E0E0E0",
                disabled="#BDBDBD"
            )
    
    def _get_default_typography(self) -> Typography:
        """Tipografia padrão DATAMETRIA."""
        return Typography(
            font_family="System",
            font_sizes={
                'xs': 12,
                'sm': 14,
                'base': 16,
                'lg': 18,
                'xl': 20,
                '2xl': 24,
                '3xl': 30,
                '4xl': 36
            },
            line_heights={
                'tight': 1.2,
                'normal': 1.5,
                'relaxed': 1.75,
                'loose': 2.0
            },
            font_weights={
                'light': '300',
                'normal': '400',
                'medium': '500',
                'semibold': '600',
                'bold': '700',
                'extrabold': '800'
            },
            letter_spacing={
                'tight': -0.5,
                'normal': 0,
                'wide': 0.5,
                'wider': 1.0
            }
        )
    
    def _get_default_spacing(self) -> Spacing:
        """Espaçamento padrão DATAMETRIA."""
        return Spacing(
            base=16,
            scale=[4, 8, 16, 24, 32, 48, 64, 96]
        )
    
    def _get_default_shadows(self) -> Shadows:
        """Sombras padrão DATAMETRIA."""
        return Shadows(
            sm={
                'shadowOffset': {'width': 0, 'height': 1},
                'shadowOpacity': 0.1,
                'shadowRadius': 2,
                'elevation': 2
            },
            md={
                'shadowOffset': {'width': 0, 'height': 2},
                'shadowOpacity': 0.15,
                'shadowRadius': 4,
                'elevation': 4
            },
            lg={
                'shadowOffset': {'width': 0, 'height': 4},
                'shadowOpacity': 0.2,
                'shadowRadius': 8,
                'elevation': 8
            },
            xl={
                'shadowOffset': {'width': 0, 'height': 8},
                'shadowOpacity': 0.25,
                'shadowRadius': 16,
                'elevation': 16
            }
        )
    
    def get_color(self, color_name: str) -> str:
        """
        Obter cor do tema.
        
        Args:
            color_name: Nome da cor
            
        Returns:
            str: Valor da cor em hex
        """
        if hasattr(self.colors, color_name):
            return getattr(self.colors, color_name)
        
        # Buscar em custom tokens
        if color_name in self.custom_tokens.get('colors', {}):
            return self.custom_tokens['colors'][color_name]
        
        logger.warning("Color not found", color_name=color_name)
        return self.colors.text
    
    def get_font_size(self, size: str) -> int:
        """
        Obter tamanho de fonte.
        
        Args:
            size: Tamanho da fonte
            
        Returns:
            int: Tamanho em pixels
        """
        return self.typography.font_sizes.get(size, self.typography.font_sizes['base'])
    
    def get_spacing(self, size: str) -> int:
        """
        Obter espaçamento.
        
        Args:
            size: Tamanho do espaçamento
            
        Returns:
            int: Espaçamento em pixels
        """
        return self.spacing.get(size)
    
    def get_shadow(self, size: str) -> Dict[str, Any]:
        """
        Obter sombra.
        
        Args:
            size: Tamanho da sombra
            
        Returns:
            Dict[str, Any]: Configuração da sombra
        """
        if hasattr(self.shadows, size):
            return getattr(self.shadows, size)
        return self.shadows.sm
    
    def get_border_radius(self, size: str) -> int:
        """
        Obter border radius.
        
        Args:
            size: Tamanho do border radius
            
        Returns:
            int: Border radius em pixels
        """
        if hasattr(self.border_radius, size):
            return getattr(self.border_radius, size)
        return self.border_radius.md
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter tema para dicionário."""
        return {
            'mode': self.mode.value,
            'colors': {
                'primary': self.colors.primary,
                'secondary': self.colors.secondary,
                'success': self.colors.success,
                'warning': self.colors.warning,
                'error': self.colors.error,
                'info': self.colors.info,
                'background': self.colors.background,
                'surface': self.colors.surface,
                'text': self.colors.text,
                'textSecondary': self.colors.text_secondary,
                'border': self.colors.border,
                'disabled': self.colors.disabled
            },
            'typography': {
                'fontFamily': self.typography.font_family,
                'fontSize': self.typography.font_sizes,
                'lineHeight': self.typography.line_heights,
                'fontWeight': self.typography.font_weights,
                'letterSpacing': self.typography.letter_spacing
            },
            'spacing': {
                'base': self.spacing.base,
                'scale': self.spacing.scale
            },
            'borderRadius': {
                'none': self.border_radius.none,
                'sm': self.border_radius.sm,
                'md': self.border_radius.md,
                'lg': self.border_radius.lg,
                'xl': self.border_radius.xl,
                'full': self.border_radius.full
            },
            'shadows': {
                'sm': self.shadows.sm,
                'md': self.shadows.md,
                'lg': self.shadows.lg,
                'xl': self.shadows.xl
            },
            'custom': self.custom_tokens
        }
    
    def switch_mode(self, new_mode: ThemeMode) -> None:
        """
        Trocar modo do tema.
        
        Args:
            new_mode: Novo modo do tema
        """
        old_mode = self.mode
        self.mode = new_mode
        
        # Recarregar cores para o novo modo
        self.colors = self._get_default_colors()
        
        logger.info("Theme mode switched", old_mode=old_mode.value, new_mode=new_mode.value)
    
    def extend_colors(self, new_colors: Dict[str, str]) -> None:
        """
        Estender paleta de cores.
        
        Args:
            new_colors: Novas cores a adicionar
        """
        if 'colors' not in self.custom_tokens:
            self.custom_tokens['colors'] = {}
        
        self.custom_tokens['colors'].update(new_colors)
        logger.info("Colors extended", new_colors=list(new_colors.keys()))
    
    def create_variant(self, variant_name: str, overrides: Dict[str, Any]) -> 'DatametriaTheme':
        """
        Criar variante do tema.
        
        Args:
            variant_name: Nome da variante
            overrides: Sobrescritas do tema
            
        Returns:
            DatametriaTheme: Nova instância do tema
        """
        # Criar cópia do tema atual
        theme_dict = self.to_dict()
        
        # Aplicar sobrescritas
        for key, value in overrides.items():
            if key in theme_dict:
                if isinstance(theme_dict[key], dict) and isinstance(value, dict):
                    theme_dict[key].update(value)
                else:
                    theme_dict[key] = value
        
        # Criar nova instância
        variant = DatametriaTheme(
            mode=ThemeMode(theme_dict['mode']),
            custom_tokens=theme_dict.get('custom', {})
        )
        
        logger.info("Theme variant created", variant_name=variant_name)
        return variant


class ThemeProvider:
    """
    Provider de tema DATAMETRIA.
    
    Gerencia tema global e notifica mudanças.
    """
    
    def __init__(self, initial_theme: Optional[DatametriaTheme] = None):
        self._theme = initial_theme or DatametriaTheme()
        self._listeners: List[Callable[[DatametriaTheme], None]] = []
        
        logger.info("ThemeProvider initialized", mode=self._theme.mode.value)
    
    def get_theme(self) -> DatametriaTheme:
        """Obter tema atual."""
        return self._theme
    
    def set_theme(self, theme: DatametriaTheme) -> None:
        """
        Definir novo tema.
        
        Args:
            theme: Novo tema
        """
        old_mode = self._theme.mode
        self._theme = theme
        
        # Notificar listeners
        self._notify_listeners()
        
        logger.info("Theme changed", old_mode=old_mode.value, new_mode=theme.mode.value)
    
    def switch_mode(self, mode: ThemeMode) -> None:
        """
        Trocar modo do tema.
        
        Args:
            mode: Novo modo
        """
        self._theme.switch_mode(mode)
        self._notify_listeners()
    
    def toggle_dark_mode(self) -> ThemeMode:
        """
        Alternar entre light e dark mode.
        
        Returns:
            ThemeMode: Novo modo
        """
        if self._theme.mode == ThemeMode.LIGHT:
            new_mode = ThemeMode.DARK
        elif self._theme.mode == ThemeMode.DARK:
            new_mode = ThemeMode.LIGHT
        else:  # AUTO
            # Se auto, definir explicitamente como dark ou light
            new_mode = ThemeMode.DARK
        
        self.switch_mode(new_mode)
        return new_mode
    
    def add_listener(self, listener: Callable[[DatametriaTheme], None]) -> None:
        """
        Adicionar listener de mudança de tema.
        
        Args:
            listener: Função que recebe o novo tema
        """
        self._listeners.append(listener)
        logger.debug("Theme listener added")
    
    def remove_listener(self, listener: Callable[[DatametriaTheme], None]) -> None:
        """Remover listener de mudança de tema."""
        if listener in self._listeners:
            self._listeners.remove(listener)
            logger.debug("Theme listener removed")
    
    def _notify_listeners(self) -> None:
        """Notificar listeners sobre mudança de tema."""
        for listener in self._listeners:
            try:
                listener(self._theme)
            except Exception as e:
                logger.error("Theme listener error", error=str(e))
    
    def create_responsive_theme(self, breakpoint: str) -> Dict[str, Any]:
        """
        Criar tema responsivo para breakpoint específico.
        
        Args:
            breakpoint: Breakpoint ('phone', 'tablet', 'desktop')
            
        Returns:
            Dict[str, Any]: Tema adaptado para o breakpoint
        """
        base_theme = self._theme.to_dict()
        
        # Ajustes responsivos
        if breakpoint == 'phone':
            # Fontes menores para telefone
            base_theme['typography']['fontSize'] = {
                k: max(v - 2, 10) for k, v in base_theme['typography']['fontSize'].items()
            }
            # Espaçamentos menores
            base_theme['spacing']['scale'] = [x * 0.8 for x in base_theme['spacing']['scale']]
        
        elif breakpoint == 'tablet':
            # Ajustes moderados para tablet
            base_theme['typography']['fontSize'] = {
                k: v + 1 for k, v in base_theme['typography']['fontSize'].items()
            }
        
        elif breakpoint == 'desktop':
            # Fontes maiores para desktop
            base_theme['typography']['fontSize'] = {
                k: v + 2 for k, v in base_theme['typography']['fontSize'].items()
            }
            # Espaçamentos maiores
            base_theme['spacing']['scale'] = [x * 1.2 for x in base_theme['spacing']['scale']]
        
        return base_theme


# Instância global do provider de tema
theme_provider = ThemeProvider()


# Factory functions
def create_theme(
    mode: ThemeMode = ThemeMode.LIGHT,
    custom_colors: Optional[Dict[str, str]] = None,
    **kwargs
) -> DatametriaTheme:
    """
    Criar tema DATAMETRIA.
    
    Args:
        mode: Modo do tema
        custom_colors: Cores customizadas
        **kwargs: Outras configurações
        
    Returns:
        DatametriaTheme: Instância do tema
    """
    theme = DatametriaTheme(mode=mode, **kwargs)
    
    if custom_colors:
        theme.extend_colors(custom_colors)
    
    return theme

def create_light_theme(**kwargs) -> DatametriaTheme:
    """Criar tema claro."""
    return create_theme(ThemeMode.LIGHT, **kwargs)

def create_dark_theme(**kwargs) -> DatametriaTheme:
    """Criar tema escuro."""
    return create_theme(ThemeMode.DARK, **kwargs)

def get_current_theme() -> DatametriaTheme:
    """Obter tema atual do provider global."""
    return theme_provider.get_theme()

def set_global_theme(theme: DatametriaTheme) -> None:
    """Definir tema global."""
    theme_provider.set_theme(theme)
