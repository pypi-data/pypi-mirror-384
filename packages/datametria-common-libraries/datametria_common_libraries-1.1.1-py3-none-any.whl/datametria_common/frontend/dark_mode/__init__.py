"""
Dark Mode Manager DATAMETRIA

Sistema completo de gerenciamento de tema escuro integrado com o Design System,
oferecendo detecção automática, persistência e transições suaves.
"""

from .manager import *
from .storage import *
from .sync import *
from .transitions import *

__version__ = "1.0.0"
__all__ = [
    # Core Manager
    "DarkModeManager",
    "ThemeMode",
    "ThemeChangeEvent",
    
    # Storage
    "ThemeStorage",
    "LocalThemeStorage",
    "SecureThemeStorage",
    
    # Sync
    "ThemeSyncManager",
    "CloudThemeSync",
    
    # Transitions
    "ThemeTransitionManager",
    "TransitionConfig",
]
