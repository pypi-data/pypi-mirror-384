"""
🏗️ Datametria Provider - React Native Components

Provider principal integrado aos componentes DATAMETRIA existentes.
"""

from typing import Dict, Any, Optional
import structlog

from datametria_common.core import BaseConfig
from datametria_common.frontend.dark_mode_manager import DarkModeManager
from datametria_common.frontend.design_system import DesignSystemManager

logger = structlog.get_logger(__name__)


class ReactNativeConfig(BaseConfig):
    """Configuração React Native integrada ao BaseConfig."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Theme Configuration
        self.theme_mode = kwargs.get('theme_mode', 'auto')  # 'light' | 'dark' | 'auto'
        self.design_tokens = kwargs.get('design_tokens', 'datametria')
        
        # Responsive Configuration
        self.breakpoints = kwargs.get('breakpoints', {
            'phone': 0,
            'tablet': 768,
            'desktop': 1024
        })
        
        # Accessibility Configuration
        self.accessibility = kwargs.get('accessibility', {
            'announceChanges': True,
            'reduceMotion': False,
            'highContrast': False,
            'focusManagement': True
        })
        
        # Performance Configuration
        self.animations = kwargs.get('animations', True)
        self.haptic_feedback = kwargs.get('haptic_feedback', True)
        
        # Localization
        self.locale = kwargs.get('locale', 'pt-BR')
        
        logger.info(
            "ReactNativeConfig initialized",
            theme_mode=self.theme_mode,
            locale=self.locale,
            animations=self.animations
        )


class DatametriaProvider:
    """
    Provider principal React Native DATAMETRIA.
    
    Integra Design System, Dark Mode e configurações centralizadas.
    """
    
    def __init__(self, config: Optional[ReactNativeConfig] = None):
        """
        Inicializa DatametriaProvider.
        
        Args:
            config: Configuração React Native
        """
        self.config = config or ReactNativeConfig()
        
        # Integrar com componentes DATAMETRIA existentes
        self.dark_mode_manager = DarkModeManager()
        self.design_system = DesignSystemManager()
        
        # Estado do provider
        self._theme_state = {
            'mode': self.config.theme_mode,
            'tokens': self._load_design_tokens(),
            'responsive': self._setup_responsive_config()
        }
        
        logger.info(
            "DatametriaProvider initialized",
            theme_mode=self.config.theme_mode,
            design_tokens=self.config.design_tokens,
            locale=self.config.locale
        )
    
    def _load_design_tokens(self) -> Dict[str, Any]:
        """Carregar tokens do Design System."""
        try:
            # Integrar com DesignSystemManager existente
            tokens = self.design_system.get_tokens()
            
            # Adicionar tokens específicos do React Native
            mobile_tokens = {
                'spacing': {
                    'xs': 4,
                    'sm': 8,
                    'md': 16,
                    'lg': 24,
                    'xl': 32,
                    '2xl': 48
                },
                'typography': {
                    'fontSize': {
                        'xs': 12,
                        'sm': 14,
                        'base': 16,
                        'lg': 18,
                        'xl': 20,
                        '2xl': 24,
                        '3xl': 30
                    },
                    'lineHeight': {
                        'tight': 1.2,
                        'normal': 1.5,
                        'relaxed': 1.75
                    }
                },
                'borderRadius': {
                    'none': 0,
                    'sm': 4,
                    'md': 8,
                    'lg': 12,
                    'xl': 16,
                    'full': 9999
                },
                'shadows': {
                    'sm': {
                        'shadowOffset': {'width': 0, 'height': 1},
                        'shadowOpacity': 0.1,
                        'shadowRadius': 2,
                        'elevation': 2
                    },
                    'md': {
                        'shadowOffset': {'width': 0, 'height': 2},
                        'shadowOpacity': 0.15,
                        'shadowRadius': 4,
                        'elevation': 4
                    },
                    'lg': {
                        'shadowOffset': {'width': 0, 'height': 4},
                        'shadowOpacity': 0.2,
                        'shadowRadius': 8,
                        'elevation': 8
                    }
                }
            }
            
            # Mesclar tokens
            return {**tokens, **mobile_tokens}
            
        except Exception as e:
            logger.warning("Failed to load design tokens", error=str(e))
            return self._get_default_tokens()
    
    def _get_default_tokens(self) -> Dict[str, Any]:
        """Tokens padrão caso não consiga carregar do Design System."""
        return {
            'colors': {
                'primary': '#2196F3',
                'secondary': '#9C27B0',
                'success': '#4CAF50',
                'warning': '#FF9800',
                'error': '#F44336',
                'background': '#FFFFFF',
                'surface': '#F5F5F5',
                'text': '#212121',
                'textSecondary': '#757575'
            },
            'spacing': {
                'xs': 4, 'sm': 8, 'md': 16, 'lg': 24, 'xl': 32
            },
            'typography': {
                'fontSize': {
                    'xs': 12, 'sm': 14, 'base': 16, 'lg': 18, 'xl': 20
                }
            }
        }
    
    def _setup_responsive_config(self) -> Dict[str, Any]:
        """Configurar responsividade."""
        return {
            'breakpoints': self.config.breakpoints,
            'fluidTypography': True,
            'adaptiveSpacing': True,
            'deviceTypes': {
                'phone': {'maxWidth': 767},
                'tablet': {'minWidth': 768, 'maxWidth': 1023},
                'desktop': {'minWidth': 1024}
            }
        }
    
    def get_theme(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Obter tema atual.
        
        Args:
            mode: Modo específico ('light' | 'dark')
            
        Returns:
            Dict: Configuração do tema
        """
        current_mode = mode or self._theme_state['mode']
        
        # Integrar com DarkModeManager
        if current_mode == 'auto':
            current_mode = 'dark' if self.dark_mode_manager.is_dark_mode() else 'light'
        
        base_tokens = self._theme_state['tokens']
        
        # Aplicar variações de tema
        if current_mode == 'dark':
            theme_colors = self._get_dark_theme_colors(base_tokens.get('colors', {}))
        else:
            theme_colors = base_tokens.get('colors', {})
        
        return {
            'mode': current_mode,
            'colors': theme_colors,
            'spacing': base_tokens.get('spacing', {}),
            'typography': base_tokens.get('typography', {}),
            'borderRadius': base_tokens.get('borderRadius', {}),
            'shadows': base_tokens.get('shadows', {}),
            'responsive': self._theme_state['responsive']
        }
    
    def _get_dark_theme_colors(self, base_colors: Dict[str, str]) -> Dict[str, str]:
        """Gerar cores para tema escuro."""
        return {
            **base_colors,
            'background': '#121212',
            'surface': '#1E1E1E',
            'text': '#FFFFFF',
            'textSecondary': '#B3B3B3',
            'border': '#333333'
        }
    
    def toggle_theme(self) -> str:
        """
        Alternar tema.
        
        Returns:
            str: Novo modo do tema
        """
        current_mode = self._theme_state['mode']
        
        if current_mode == 'light':
            new_mode = 'dark'
        elif current_mode == 'dark':
            new_mode = 'light'
        else:  # auto
            # Se auto, alternar baseado no estado atual
            is_dark = self.dark_mode_manager.is_dark_mode()
            new_mode = 'light' if is_dark else 'dark'
        
        self._theme_state['mode'] = new_mode
        
        # Sincronizar com DarkModeManager
        self.dark_mode_manager.set_dark_mode(new_mode == 'dark')
        
        logger.info("Theme toggled", old_mode=current_mode, new_mode=new_mode)
        
        return new_mode
    
    def set_theme(self, mode: str) -> None:
        """
        Definir tema específico.
        
        Args:
            mode: Modo do tema ('light' | 'dark' | 'auto')
        """
        if mode not in ['light', 'dark', 'auto']:
            raise ValueError("Theme mode must be 'light', 'dark', or 'auto'")
        
        old_mode = self._theme_state['mode']
        self._theme_state['mode'] = mode
        
        # Sincronizar com DarkModeManager
        if mode != 'auto':
            self.dark_mode_manager.set_dark_mode(mode == 'dark')
        
        logger.info("Theme set", old_mode=old_mode, new_mode=mode)
    
    def get_responsive_config(self) -> Dict[str, Any]:
        """Obter configuração de responsividade."""
        return self._theme_state['responsive']
    
    def update_config(self, new_config: ReactNativeConfig) -> None:
        """
        Atualizar configuração.
        
        Args:
            new_config: Nova configuração
        """
        self.config = new_config
        
        # Recarregar tokens e configurações
        self._theme_state = {
            'mode': new_config.theme_mode,
            'tokens': self._load_design_tokens(),
            'responsive': self._setup_responsive_config()
        }
        
        logger.info("Provider config updated")
    
    def get_accessibility_config(self) -> Dict[str, Any]:
        """Obter configuração de acessibilidade."""
        return self.config.accessibility
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do provider."""
        return {
            'provider_ready': True,
            'theme_mode': self._theme_state['mode'],
            'design_system_loaded': bool(self._theme_state['tokens']),
            'dark_mode_manager': self.dark_mode_manager is not None,
            'responsive_config': bool(self._theme_state['responsive']),
            'locale': self.config.locale
        }
