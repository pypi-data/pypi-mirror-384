"""
DATAMETRIA Design System

Sistema completo de design tokens, componentes e guidelines para garantir
consistência visual e experiência unificada em todas as plataformas DATAMETRIA.
"""

from .tokens import *
from .themes import *
from .components import *

__version__ = "1.0.0"
__all__ = [
    # Tokens
    "ColorSystem",
    "TypographySystem", 
    "SpacingSystem",
    "BorderSystem",
    "ShadowSystem",
    "MotionSystem",
    
    # Themes
    "DatametriaTheme",
    "LightTheme",
    "DarkTheme",
    "HighContrastTheme",
    
    # Components
    "DatametriaButton",
    "DatametriaInput",
    "DatametriaCard",
    "DatametriaModal",
    "DatametriaForm",
]
