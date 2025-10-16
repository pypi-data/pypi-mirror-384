"""
Gerador de CSS do Design System DATAMETRIA

Utilitário para gerar CSS completo do Design System com temas,
componentes e utilitários responsivos.
"""

from typing import Dict, List, Optional
from .themes import ThemeManager, theme_manager
from .components import *


class CSSGenerator:
    """Gerador de CSS do Design System"""
    
    def __init__(self, theme_manager: ThemeManager = theme_manager):
        self.theme_manager = theme_manager
        self.components = self._get_all_components()
    
    def _get_all_components(self) -> List:
        """Obtém todos os componentes disponíveis"""
        return [
            # Base Components
            DatametriaButton(),
            DatametriaIcon("example"),
            DatametriaAvatar(),
            DatametriaBadge(),
            
            # Form Components
            DatametriaInput(),
            DatametriaTextarea(),
            DatametriaSelect([]),
            DatametriaCheckbox(),
            DatametriaRadio("example", "value"),
            DatametriaSwitch(),
            DatametriaForm(),
            
            # Layout Components
            DatametriaCard(),
            DatametriaContainer(),
            DatametriaGrid(),
            DatametriaStack(),
            DatametriaDivider(),
            
            # Navigation Components
            DatametriaNavbar(),
            DatametriaSidebar(),
            DatametriaBreadcrumb([]),
            DatametriaTabs([]),
            DatametriaPagination(),
            
            # Feedback Components
            DatametriaModal(),
            DatametriaToast(),
            DatametriaAlert(),
            DatametriaProgress(),
            DatametriaSpinner(),
            DatametriaTooltip(),
        ]
    
    def generate_theme_css(self, theme_name: Optional[str] = None) -> str:
        """Gera CSS das variáveis do tema"""
        return self.theme_manager.generate_css(theme_name)
    
    def generate_components_css(self) -> str:
        """Gera CSS de todos os componentes"""
        css_parts = []
        
        for component in self.components:
            if hasattr(component, 'get_css'):
                css_parts.append(component.get_css())
        
        return "\n\n".join(css_parts)
    
    def generate_utilities_css(self) -> str:
        """Gera CSS das classes utilitárias"""
        return """
        /* Reset básico */
        *, *::before, *::after {
            box-sizing: border-box;
        }
        
        * {
            margin: 0;
        }
        
        body {
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }
        
        img, picture, video, canvas, svg {
            display: block;
            max-width: 100%;
        }
        
        input, button, textarea, select {
            font: inherit;
        }
        
        p, h1, h2, h3, h4, h5, h6 {
            overflow-wrap: break-word;
        }
        
        /* Utilitários de display */
        .dm-hidden { display: none !important; }
        .dm-block { display: block !important; }
        .dm-inline { display: inline !important; }
        .dm-inline-block { display: inline-block !important; }
        .dm-flex { display: flex !important; }
        .dm-inline-flex { display: inline-flex !important; }
        .dm-grid { display: grid !important; }
        
        /* Utilitários de posição */
        .dm-static { position: static !important; }
        .dm-fixed { position: fixed !important; }
        .dm-absolute { position: absolute !important; }
        .dm-relative { position: relative !important; }
        .dm-sticky { position: sticky !important; }
        
        /* Utilitários de texto */
        .dm-text-left { text-align: left !important; }
        .dm-text-center { text-align: center !important; }
        .dm-text-right { text-align: right !important; }
        .dm-text-justify { text-align: justify !important; }
        
        .dm-font-thin { font-weight: 100 !important; }
        .dm-font-light { font-weight: 300 !important; }
        .dm-font-normal { font-weight: 400 !important; }
        .dm-font-medium { font-weight: 500 !important; }
        .dm-font-semibold { font-weight: 600 !important; }
        .dm-font-bold { font-weight: 700 !important; }
        .dm-font-extrabold { font-weight: 800 !important; }
        .dm-font-black { font-weight: 900 !important; }
        
        /* Utilitários de espaçamento */
        .dm-m-0 { margin: 0 !important; }
        .dm-m-1 { margin: var(--dm-spacing-sm) !important; }
        .dm-m-2 { margin: var(--dm-spacing-md) !important; }
        .dm-m-3 { margin: var(--dm-spacing-lg) !important; }
        .dm-m-4 { margin: var(--dm-spacing-xl) !important; }
        .dm-m-5 { margin: var(--dm-spacing-2xl) !important; }
        .dm-m-6 { margin: var(--dm-spacing-3xl) !important; }
        
        .dm-p-0 { padding: 0 !important; }
        .dm-p-1 { padding: var(--dm-spacing-sm) !important; }
        .dm-p-2 { padding: var(--dm-spacing-md) !important; }
        .dm-p-3 { padding: var(--dm-spacing-lg) !important; }
        .dm-p-4 { padding: var(--dm-spacing-xl) !important; }
        .dm-p-5 { padding: var(--dm-spacing-2xl) !important; }
        .dm-p-6 { padding: var(--dm-spacing-3xl) !important; }
        
        /* Utilitários de largura */
        .dm-w-auto { width: auto !important; }
        .dm-w-full { width: 100% !important; }
        .dm-w-screen { width: 100vw !important; }
        .dm-w-fit { width: fit-content !important; }
        
        /* Utilitários de altura */
        .dm-h-auto { height: auto !important; }
        .dm-h-full { height: 100% !important; }
        .dm-h-screen { height: 100vh !important; }
        .dm-h-fit { height: fit-content !important; }
        
        /* Utilitários de flex */
        .dm-flex-row { flex-direction: row !important; }
        .dm-flex-col { flex-direction: column !important; }
        .dm-flex-wrap { flex-wrap: wrap !important; }
        .dm-flex-nowrap { flex-wrap: nowrap !important; }
        
        .dm-items-start { align-items: flex-start !important; }
        .dm-items-center { align-items: center !important; }
        .dm-items-end { align-items: flex-end !important; }
        .dm-items-stretch { align-items: stretch !important; }
        
        .dm-justify-start { justify-content: flex-start !important; }
        .dm-justify-center { justify-content: center !important; }
        .dm-justify-end { justify-content: flex-end !important; }
        .dm-justify-between { justify-content: space-between !important; }
        .dm-justify-around { justify-content: space-around !important; }
        .dm-justify-evenly { justify-content: space-evenly !important; }
        
        .dm-flex-1 { flex: 1 1 0% !important; }
        .dm-flex-auto { flex: 1 1 auto !important; }
        .dm-flex-initial { flex: 0 1 auto !important; }
        .dm-flex-none { flex: none !important; }
        
        /* Utilitários de gap */
        .dm-gap-0 { gap: 0 !important; }
        .dm-gap-1 { gap: var(--dm-spacing-sm) !important; }
        .dm-gap-2 { gap: var(--dm-spacing-md) !important; }
        .dm-gap-3 { gap: var(--dm-spacing-lg) !important; }
        .dm-gap-4 { gap: var(--dm-spacing-xl) !important; }
        .dm-gap-5 { gap: var(--dm-spacing-2xl) !important; }
        .dm-gap-6 { gap: var(--dm-spacing-3xl) !important; }
        
        /* Utilitários de border radius */
        .dm-rounded-none { border-radius: 0 !important; }
        .dm-rounded-sm { border-radius: var(--dm-border-radius-sm) !important; }
        .dm-rounded { border-radius: var(--dm-border-radius-md) !important; }
        .dm-rounded-lg { border-radius: var(--dm-border-radius-lg) !important; }
        .dm-rounded-xl { border-radius: var(--dm-border-radius-xl) !important; }
        .dm-rounded-full { border-radius: var(--dm-border-radius-full) !important; }
        
        /* Utilitários de shadow */
        .dm-shadow-none { box-shadow: none !important; }
        .dm-shadow-sm { box-shadow: var(--dm-shadow-sm) !important; }
        .dm-shadow { box-shadow: var(--dm-shadow-md) !important; }
        .dm-shadow-lg { box-shadow: var(--dm-shadow-lg) !important; }
        .dm-shadow-xl { box-shadow: var(--dm-shadow-xl) !important; }
        
        /* Utilitários responsivos */
        @media (min-width: 640px) {
            .dm-sm\\:block { display: block !important; }
            .dm-sm\\:hidden { display: none !important; }
            .dm-sm\\:flex { display: flex !important; }
        }
        
        @media (min-width: 768px) {
            .dm-md\\:block { display: block !important; }
            .dm-md\\:hidden { display: none !important; }
            .dm-md\\:flex { display: flex !important; }
        }
        
        @media (min-width: 1024px) {
            .dm-lg\\:block { display: block !important; }
            .dm-lg\\:hidden { display: none !important; }
            .dm-lg\\:flex { display: flex !important; }
        }
        
        @media (min-width: 1280px) {
            .dm-xl\\:block { display: block !important; }
            .dm-xl\\:hidden { display: none !important; }
            .dm-xl\\:flex { display: flex !important; }
        }
        
        /* Dark mode utilities */
        @media (prefers-color-scheme: dark) {
            .dm-dark\\:block { display: block !important; }
            .dm-dark\\:hidden { display: none !important; }
        }
        """
    
    def generate_full_css(self, theme_name: Optional[str] = None) -> str:
        """Gera CSS completo do Design System"""
        css_parts = [
            "/* DATAMETRIA Design System v1.0.0 */",
            "/* Generated CSS - Do not edit manually */",
            "",
            "/* Theme Variables */",
            self.generate_theme_css(theme_name),
            "",
            "/* Utility Classes */", 
            self.generate_utilities_css(),
            "",
            "/* Components */",
            self.generate_components_css(),
        ]
        
        return "\n".join(css_parts)
    
    def save_css_file(self, filepath: str, theme_name: Optional[str] = None) -> None:
        """Salva CSS completo em arquivo"""
        css_content = self.generate_full_css(theme_name)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(css_content)


# Instância global do gerador
css_generator = CSSGenerator()

# Export
__all__ = [
    "CSSGenerator",
    "css_generator",
]
