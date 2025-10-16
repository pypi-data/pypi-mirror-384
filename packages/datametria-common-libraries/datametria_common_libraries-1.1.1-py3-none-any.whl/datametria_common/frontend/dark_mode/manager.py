"""
Dark Mode Manager Core

Gerenciador principal de temas integrado com o Design System DATAMETRIA.
"""

from typing import Callable, Optional, Set, Dict, Any
from enum import Enum
from dataclasses import dataclass
from ..design_system import theme_manager, LightTheme, DarkTheme, HighContrastTheme


class ThemeMode(Enum):
    """Modos de tema disponíveis"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    HIGH_CONTRAST = "high-contrast"


@dataclass
class ThemeChangeEvent:
    """Evento de mudança de tema"""
    previous_theme: ThemeMode
    current_theme: ThemeMode
    effective_theme: ThemeMode
    timestamp: float


class DarkModeManager:
    """
    Gerenciador principal de Dark Mode integrado com Design System DATAMETRIA
    
    Aproveita os temas existentes (LightTheme, DarkTheme, HighContrastTheme)
    e adiciona funcionalidades de detecção automática e persistência.
    """
    
    def __init__(self):
        self._current_mode = ThemeMode.AUTO
        self._system_theme = ThemeMode.LIGHT
        self._listeners: Set[Callable[[ThemeChangeEvent], None]] = set()
        self._storage_key = "datametria-theme-mode"
        
        # Integração com Design System existente
        self._theme_manager = theme_manager
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Inicializa o gerenciador"""
        # Detectar tema do sistema
        self._detect_system_theme()
        
        # Carregar preferência salva
        saved_mode = self._load_saved_mode()
        if saved_mode:
            self._current_mode = saved_mode
        
        # Aplicar tema inicial
        self._apply_current_theme()
        
        # Configurar listener do sistema
        self._setup_system_listener()
    
    def _detect_system_theme(self) -> None:
        """Detecta tema do sistema operacional"""
        try:
            # Simula detecção (em implementação real usaria media query)
            # window.matchMedia('(prefers-color-scheme: dark)')
            import os
            if os.environ.get('DATAMETRIA_DARK_MODE') == 'true':
                self._system_theme = ThemeMode.DARK
            else:
                self._system_theme = ThemeMode.LIGHT
        except Exception:
            self._system_theme = ThemeMode.LIGHT
    
    def _setup_system_listener(self) -> None:
        """Configura listener para mudanças do sistema"""
        # Em implementação real, configuraria media query listener
        pass
    
    def _load_saved_mode(self) -> Optional[ThemeMode]:
        """Carrega modo salvo do storage"""
        try:
            # Simula localStorage (em implementação real usaria storage real)
            import os
            saved = os.environ.get(self._storage_key)
            if saved:
                return ThemeMode(saved)
        except Exception:
            pass
        return None
    
    def _save_mode(self, mode: ThemeMode) -> None:
        """Salva modo no storage"""
        try:
            # Simula localStorage (em implementação real usaria storage real)
            import os
            os.environ[self._storage_key] = mode.value
        except Exception:
            pass
    
    def _apply_current_theme(self) -> None:
        """Aplica o tema atual usando o Design System"""
        effective_theme = self.get_effective_theme()
        
        # Mapear para temas do Design System
        theme_mapping = {
            ThemeMode.LIGHT: "light",
            ThemeMode.DARK: "dark", 
            ThemeMode.HIGH_CONTRAST: "high-contrast"
        }
        
        design_system_theme = theme_mapping.get(effective_theme, "light")
        
        # Usar theme_manager existente
        self._theme_manager.set_current_theme(design_system_theme)
    
    def set_theme(self, mode: ThemeMode) -> None:
        """
        Define o modo de tema
        
        Args:
            mode: Modo de tema a ser aplicado
        """
        previous_mode = self._current_mode
        self._current_mode = mode
        
        # Aplicar tema
        self._apply_current_theme()
        
        # Salvar preferência
        self._save_mode(mode)
        
        # Notificar listeners
        event = ThemeChangeEvent(
            previous_theme=previous_mode,
            current_theme=mode,
            effective_theme=self.get_effective_theme(),
            timestamp=self._get_timestamp()
        )
        self._notify_listeners(event)
    
    def get_theme(self) -> ThemeMode:
        """Retorna o modo de tema atual"""
        return self._current_mode
    
    def get_effective_theme(self) -> ThemeMode:
        """
        Retorna o tema efetivo (resolve AUTO para LIGHT/DARK)
        
        Returns:
            Tema efetivo sendo usado
        """
        if self._current_mode == ThemeMode.AUTO:
            return self._system_theme
        return self._current_mode
    
    def is_dark_mode(self) -> bool:
        """Verifica se está em modo escuro"""
        effective = self.get_effective_theme()
        return effective in (ThemeMode.DARK, ThemeMode.HIGH_CONTRAST)
    
    def toggle_theme(self) -> None:
        """Alterna entre tema claro e escuro"""
        if self.is_dark_mode():
            self.set_theme(ThemeMode.LIGHT)
        else:
            self.set_theme(ThemeMode.DARK)
    
    def add_listener(self, listener: Callable[[ThemeChangeEvent], None]) -> None:
        """
        Adiciona listener para mudanças de tema
        
        Args:
            listener: Função callback para mudanças
        """
        self._listeners.add(listener)
    
    def remove_listener(self, listener: Callable[[ThemeChangeEvent], None]) -> None:
        """
        Remove listener de mudanças de tema
        
        Args:
            listener: Função callback a ser removida
        """
        self._listeners.discard(listener)
    
    def _notify_listeners(self, event: ThemeChangeEvent) -> None:
        """Notifica todos os listeners sobre mudança de tema"""
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                # Log error but don't break other listeners
                print(f"Error in theme change listener: {e}")
    
    def _get_timestamp(self) -> float:
        """Retorna timestamp atual"""
        import time
        return time.time()
    
    def get_theme_config(self) -> Dict[str, Any]:
        """
        Retorna configuração atual do tema
        
        Returns:
            Dicionário com configuração do tema
        """
        current_theme = self._theme_manager.get_current_theme()
        
        return {
            "mode": self._current_mode.value,
            "effective_theme": self.get_effective_theme().value,
            "system_theme": self._system_theme.value,
            "is_dark": self.is_dark_mode(),
            "theme_name": current_theme.name,
            "colors": current_theme.colors.__dict__ if hasattr(current_theme.colors, '__dict__') else {},
            "css_variables": current_theme.to_css_variables()
        }
    
    def generate_css(self) -> str:
        """
        Gera CSS completo para o tema atual
        
        Returns:
            CSS string com variáveis do tema
        """
        return self._theme_manager.generate_css()
    
    def apply_system_theme_change(self, is_dark: bool) -> None:
        """
        Aplica mudança de tema do sistema (chamado por listeners externos)
        
        Args:
            is_dark: Se o sistema está em modo escuro
        """
        previous_system = self._system_theme
        self._system_theme = ThemeMode.DARK if is_dark else ThemeMode.LIGHT
        
        # Se está em modo AUTO, aplicar mudança
        if self._current_mode == ThemeMode.AUTO and previous_system != self._system_theme:
            self._apply_current_theme()
            
            event = ThemeChangeEvent(
                previous_theme=self._current_mode,
                current_theme=self._current_mode,
                effective_theme=self.get_effective_theme(),
                timestamp=self._get_timestamp()
            )
            self._notify_listeners(event)


# Instância global do gerenciador
dark_mode_manager = DarkModeManager()

# Export
__all__ = [
    "ThemeMode",
    "ThemeChangeEvent", 
    "DarkModeManager",
    "dark_mode_manager",
]
