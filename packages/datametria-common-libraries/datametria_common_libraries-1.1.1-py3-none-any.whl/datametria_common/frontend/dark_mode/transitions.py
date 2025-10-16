"""
Theme Transition Manager

Sistema de transições suaves entre temas usando CSS e animações.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from ..design_system import css_generator


class TransitionType(Enum):
    """Tipos de transição disponíveis"""
    INSTANT = "instant"
    FADE = "fade"
    SLIDE = "slide"
    SCALE = "scale"
    CUSTOM = "custom"


@dataclass
class TransitionConfig:
    """Configuração de transições"""
    type: TransitionType = TransitionType.FADE
    duration: int = 300  # milliseconds
    easing: str = "ease-in-out"
    delay: int = 0
    reduce_motion: bool = True  # Respeitar prefers-reduced-motion


class ThemeTransitionManager:
    """
    Gerenciador de transições suaves entre temas
    
    Integra com o CSS Generator do Design System para criar
    transições fluidas sem flickering.
    """
    
    def __init__(self, config: TransitionConfig = None):
        self.config = config or TransitionConfig()
        self._css_generator = css_generator
        self._transition_active = False
    
    def apply_transition(self, from_theme: str, to_theme: str) -> str:
        """
        Aplica transição entre temas
        
        Args:
            from_theme: Tema de origem
            to_theme: Tema de destino
            
        Returns:
            CSS para a transição
        """
        if self.config.type == TransitionType.INSTANT:
            return self._generate_instant_transition(to_theme)
        
        return self._generate_animated_transition(from_theme, to_theme)
    
    def _generate_instant_transition(self, theme: str) -> str:
        """Gera CSS para transição instantânea"""
        return self._css_generator.generate_theme_css(theme)
    
    def _generate_animated_transition(self, from_theme: str, to_theme: str) -> str:
        """Gera CSS para transição animada"""
        base_css = self._css_generator.generate_theme_css(to_theme)
        transition_css = self._generate_transition_css()
        
        return f"{base_css}\n\n{transition_css}"
    
    def _generate_transition_css(self) -> str:
        """Gera CSS das transições"""
        duration = f"{self.config.duration}ms"
        easing = self.config.easing
        delay = f"{self.config.delay}ms"
        
        css = f"""
        /* Theme Transition Styles */
        :root {{
            --dm-transition-duration: {duration};
            --dm-transition-easing: {easing};
            --dm-transition-delay: {delay};
        }}
        
        /* Transições para elementos principais */
        body,
        .dm-theme-transition {{
            transition: 
                background-color var(--dm-transition-duration) var(--dm-transition-easing) var(--dm-transition-delay),
                color var(--dm-transition-duration) var(--dm-transition-easing) var(--dm-transition-delay);
        }}
        
        /* Transições para componentes */
        .dm-button,
        .dm-input,
        .dm-card,
        .dm-navbar,
        .dm-modal,
        .dm-alert {{
            transition: 
                background-color var(--dm-transition-duration) var(--dm-transition-easing),
                border-color var(--dm-transition-duration) var(--dm-transition-easing),
                color var(--dm-transition-duration) var(--dm-transition-easing),
                box-shadow var(--dm-transition-duration) var(--dm-transition-easing);
        }}
        
        /* Transições específicas por tipo */
        """
        
        if self.config.type == TransitionType.FADE:
            css += self._generate_fade_transition()
        elif self.config.type == TransitionType.SLIDE:
            css += self._generate_slide_transition()
        elif self.config.type == TransitionType.SCALE:
            css += self._generate_scale_transition()
        
        # Respeitar prefers-reduced-motion
        if self.config.reduce_motion:
            css += """
        
        /* Reduzir animações para usuários que preferem */
        @media (prefers-reduced-motion: reduce) {
            :root {
                --dm-transition-duration: 0ms;
            }
            
            .dm-theme-transition,
            .dm-button,
            .dm-input,
            .dm-card,
            .dm-navbar,
            .dm-modal,
            .dm-alert {
                transition: none !important;
                animation: none !important;
            }
        }
        """
        
        return css
    
    def _generate_fade_transition(self) -> str:
        """Gera CSS para transição fade"""
        return """
        .dm-fade-transition {
            opacity: 0;
            animation: dm-fade-in var(--dm-transition-duration) var(--dm-transition-easing) var(--dm-transition-delay) forwards;
        }
        
        @keyframes dm-fade-in {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .dm-fade-out {
            animation: dm-fade-out var(--dm-transition-duration) var(--dm-transition-easing) forwards;
        }
        
        @keyframes dm-fade-out {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        """
    
    def _generate_slide_transition(self) -> str:
        """Gera CSS para transição slide"""
        return """
        .dm-slide-transition {
            transform: translateX(-100%);
            animation: dm-slide-in var(--dm-transition-duration) var(--dm-transition-easing) var(--dm-transition-delay) forwards;
        }
        
        @keyframes dm-slide-in {
            from { transform: translateX(-100%); }
            to { transform: translateX(0); }
        }
        
        .dm-slide-out {
            animation: dm-slide-out var(--dm-transition-duration) var(--dm-transition-easing) forwards;
        }
        
        @keyframes dm-slide-out {
            from { transform: translateX(0); }
            to { transform: translateX(100%); }
        }
        """
    
    def _generate_scale_transition(self) -> str:
        """Gera CSS para transição scale"""
        return """
        .dm-scale-transition {
            transform: scale(0.95);
            opacity: 0;
            animation: dm-scale-in var(--dm-transition-duration) var(--dm-transition-easing) var(--dm-transition-delay) forwards;
        }
        
        @keyframes dm-scale-in {
            from { 
                transform: scale(0.95);
                opacity: 0;
            }
            to { 
                transform: scale(1);
                opacity: 1;
            }
        }
        
        .dm-scale-out {
            animation: dm-scale-out var(--dm-transition-duration) var(--dm-transition-easing) forwards;
        }
        
        @keyframes dm-scale-out {
            from { 
                transform: scale(1);
                opacity: 1;
            }
            to { 
                transform: scale(1.05);
                opacity: 0;
            }
        }
        """
    
    def create_transition_overlay(self) -> str:
        """
        Cria overlay para transição suave
        
        Returns:
            CSS para overlay de transição
        """
        return """
        .dm-theme-transition-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: var(--dm-background);
            z-index: 9999;
            opacity: 0;
            pointer-events: none;
            transition: opacity var(--dm-transition-duration) var(--dm-transition-easing);
        }
        
        .dm-theme-transition-overlay.active {
            opacity: 1;
            pointer-events: all;
        }
        
        .dm-theme-transition-spinner {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 2rem;
            height: 2rem;
            border: 2px solid var(--dm-muted);
            border-top-color: var(--dm-primary);
            border-radius: 50%;
            animation: dm-spin 1s linear infinite;
        }
        
        @keyframes dm-spin {
            to { transform: translate(-50%, -50%) rotate(360deg); }
        }
        """
    
    def get_transition_javascript(self) -> str:
        """
        Retorna JavaScript para controlar transições
        
        Returns:
            Código JavaScript para transições
        """
        return """
        class DatametriaThemeTransition {
            constructor(config = {}) {
                this.config = {
                    duration: 300,
                    showOverlay: true,
                    ...config
                };
                this.overlay = null;
            }
            
            async transition(fromTheme, toTheme, applyThemeCallback) {
                if (this.config.showOverlay) {
                    this.showOverlay();
                }
                
                // Pequeno delay para suavizar
                await this.delay(50);
                
                // Aplicar novo tema
                if (applyThemeCallback) {
                    applyThemeCallback(toTheme);
                }
                
                // Aguardar transição completar
                await this.delay(this.config.duration);
                
                if (this.config.showOverlay) {
                    this.hideOverlay();
                }
            }
            
            showOverlay() {
                if (!this.overlay) {
                    this.overlay = document.createElement('div');
                    this.overlay.className = 'dm-theme-transition-overlay';
                    this.overlay.innerHTML = '<div class="dm-theme-transition-spinner"></div>';
                    document.body.appendChild(this.overlay);
                }
                
                // Force reflow
                this.overlay.offsetHeight;
                this.overlay.classList.add('active');
            }
            
            hideOverlay() {
                if (this.overlay) {
                    this.overlay.classList.remove('active');
                    setTimeout(() => {
                        if (this.overlay && this.overlay.parentNode) {
                            this.overlay.parentNode.removeChild(this.overlay);
                            this.overlay = null;
                        }
                    }, this.config.duration);
                }
            }
            
            delay(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }
        }
        
        // Instância global
        window.datametriaThemeTransition = new DatametriaThemeTransition();
        """
    
    def generate_complete_transition_css(self, theme: str) -> str:
        """
        Gera CSS completo com transições para um tema
        
        Args:
            theme: Nome do tema
            
        Returns:
            CSS completo com transições
        """
        base_css = self._css_generator.generate_full_css(theme)
        transition_css = self._generate_transition_css()
        overlay_css = self.create_transition_overlay()
        
        return f"""
        /* DATAMETRIA Theme with Transitions */
        {base_css}
        
        /* Transition Styles */
        {transition_css}
        
        /* Transition Overlay */
        {overlay_css}
        """
    
    def is_transition_active(self) -> bool:
        """Verifica se há transição ativa"""
        return self._transition_active
    
    def set_transition_active(self, active: bool) -> None:
        """Define estado da transição"""
        self._transition_active = active


# Export
__all__ = [
    "TransitionType",
    "TransitionConfig",
    "ThemeTransitionManager",
]
