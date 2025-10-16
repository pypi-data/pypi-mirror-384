"""
Sistema de Temas DATAMETRIA

Implementação completa dos temas Light, Dark e High Contrast
seguindo os padrões DATAMETRIA com suporte a customização.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from .tokens import DatametriaColors, DatametriaTypography, DatametriaSpacing


@dataclass
class ThemeColors:
    """Cores do tema"""
    # Brand
    primary: str
    primaryForeground: str
    secondary: str
    secondaryForeground: str
    
    # Semantic
    success: str
    successForeground: str
    warning: str
    warningForeground: str
    error: str
    errorForeground: str
    info: str
    infoForeground: str
    
    # Surface
    background: str
    foreground: str
    muted: str
    mutedForeground: str
    accent: str
    accentForeground: str
    
    # Interactive
    border: str
    input: str
    ring: str
    
    # Card
    card: str
    cardForeground: str
    
    # Popover
    popover: str
    popoverForeground: str


@dataclass
class DatametriaTheme:
    """Tema completo DATAMETRIA"""
    name: str
    colors: ThemeColors
    typography: Dict[str, Any]
    spacing: Dict[str, str]
    
    def to_css_variables(self) -> Dict[str, str]:
        """Converte tema para CSS custom properties"""
        css_vars = {}
        
        # Colors
        for key, value in asdict(self.colors).items():
            css_vars[f"--dm-{key.replace('_', '-')}"] = value
            
        # Typography
        for key, value in self.typography.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    css_vars[f"--dm-{key}-{subkey.replace('_', '-')}"] = subvalue
            else:
                css_vars[f"--dm-{key.replace('_', '-')}"] = value
                
        # Spacing
        for key, value in self.spacing.items():
            css_vars[f"--dm-spacing-{key}"] = value
            
        return css_vars
    
    def to_json(self) -> Dict[str, Any]:
        """Converte tema para JSON"""
        return {
            "name": self.name,
            "colors": asdict(self.colors),
            "typography": self.typography,
            "spacing": self.spacing
        }


class LightTheme:
    """Tema claro DATAMETRIA"""
    
    @staticmethod
    def create() -> DatametriaTheme:
        colors = ThemeColors(
            # Brand
            primary=DatametriaColors.PRIMARY.c500,
            primaryForeground=DatametriaColors.PRIMARY.c50,
            secondary=DatametriaColors.SECONDARY.c500,
            secondaryForeground=DatametriaColors.SECONDARY.c50,
            
            # Semantic
            success=DatametriaColors.SUCCESS.c500,
            successForeground=DatametriaColors.SUCCESS.c50,
            warning=DatametriaColors.WARNING.c500,
            warningForeground=DatametriaColors.WARNING.c50,
            error=DatametriaColors.ERROR.c500,
            errorForeground=DatametriaColors.ERROR.c50,
            info=DatametriaColors.INFO.c500,
            infoForeground=DatametriaColors.INFO.c50,
            
            # Surface
            background=DatametriaColors.GRAY.c50,
            foreground=DatametriaColors.GRAY.c900,
            muted=DatametriaColors.GRAY.c100,
            mutedForeground=DatametriaColors.GRAY.c600,
            accent=DatametriaColors.GRAY.c100,
            accentForeground=DatametriaColors.GRAY.c900,
            
            # Interactive
            border=DatametriaColors.GRAY.c200,
            input=DatametriaColors.GRAY.c200,
            ring=DatametriaColors.PRIMARY.c500,
            
            # Card
            card=DatametriaColors.GRAY.c50,
            cardForeground=DatametriaColors.GRAY.c900,
            
            # Popover
            popover=DatametriaColors.GRAY.c50,
            popoverForeground=DatametriaColors.GRAY.c900,
        )
        
        typography = {
            "fontFamily": {
                "sans": DatametriaTypography.FONT_SANS,
                "serif": DatametriaTypography.FONT_SERIF,
                "mono": DatametriaTypography.FONT_MONO,
            },
            "fontSize": {
                "xs": DatametriaTypography.BODY_XS.fontSize,
                "sm": DatametriaTypography.BODY_SM.fontSize,
                "base": DatametriaTypography.BODY_MD.fontSize,
                "lg": DatametriaTypography.BODY_LG.fontSize,
                "xl": DatametriaTypography.BODY_XL.fontSize,
                "2xl": DatametriaTypography.HEADING_SM.fontSize,
                "3xl": DatametriaTypography.HEADING_MD.fontSize,
                "4xl": DatametriaTypography.HEADING_LG.fontSize,
                "5xl": DatametriaTypography.HEADING_XL.fontSize,
            },
            "lineHeight": {
                "tight": "1.25",
                "snug": "1.375",
                "normal": "1.5",
                "relaxed": "1.625",
                "loose": "2",
            }
        }
        
        spacing = {
            "xs": DatametriaSpacing.XS,
            "sm": DatametriaSpacing.SM,
            "md": DatametriaSpacing.MD,
            "lg": DatametriaSpacing.LG,
            "xl": DatametriaSpacing.XL,
            "2xl": DatametriaSpacing.XL2,
            "3xl": DatametriaSpacing.XL3,
            "4xl": DatametriaSpacing.XL4,
            "5xl": DatametriaSpacing.XL5,
            "6xl": DatametriaSpacing.XL6,
        }
        
        return DatametriaTheme(
            name="light",
            colors=colors,
            typography=typography,
            spacing=spacing
        )


class DarkTheme:
    """Tema escuro DATAMETRIA"""
    
    @staticmethod
    def create() -> DatametriaTheme:
        colors = ThemeColors(
            # Brand
            primary=DatametriaColors.PRIMARY.c400,
            primaryForeground=DatametriaColors.PRIMARY.c950,
            secondary=DatametriaColors.SECONDARY.c400,
            secondaryForeground=DatametriaColors.SECONDARY.c950,
            
            # Semantic
            success=DatametriaColors.SUCCESS.c400,
            successForeground=DatametriaColors.SUCCESS.c950,
            warning=DatametriaColors.WARNING.c400,
            warningForeground=DatametriaColors.WARNING.c950,
            error=DatametriaColors.ERROR.c400,
            errorForeground=DatametriaColors.ERROR.c950,
            info=DatametriaColors.INFO.c400,
            infoForeground=DatametriaColors.INFO.c950,
            
            # Surface
            background=DatametriaColors.GRAY.c950,
            foreground=DatametriaColors.GRAY.c50,
            muted=DatametriaColors.GRAY.c900,
            mutedForeground=DatametriaColors.GRAY.c400,
            accent=DatametriaColors.GRAY.c900,
            accentForeground=DatametriaColors.GRAY.c50,
            
            # Interactive
            border=DatametriaColors.GRAY.c800,
            input=DatametriaColors.GRAY.c800,
            ring=DatametriaColors.PRIMARY.c400,
            
            # Card
            card=DatametriaColors.GRAY.c900,
            cardForeground=DatametriaColors.GRAY.c50,
            
            # Popover
            popover=DatametriaColors.GRAY.c900,
            popoverForeground=DatametriaColors.GRAY.c50,
        )
        
        # Reutiliza typography e spacing do tema claro
        light_theme = LightTheme.create()
        
        return DatametriaTheme(
            name="dark",
            colors=colors,
            typography=light_theme.typography,
            spacing=light_theme.spacing
        )


class HighContrastTheme:
    """Tema alto contraste DATAMETRIA (WCAG AAA)"""
    
    @staticmethod
    def create() -> DatametriaTheme:
        colors = ThemeColors(
            # Brand - Alto contraste
            primary="#000000",
            primaryForeground="#FFFFFF",
            secondary="#000000",
            secondaryForeground="#FFFFFF",
            
            # Semantic - Alto contraste
            success="#006600",
            successForeground="#FFFFFF",
            warning="#CC6600",
            warningForeground="#FFFFFF",
            error="#CC0000",
            errorForeground="#FFFFFF",
            info="#0066CC",
            infoForeground="#FFFFFF",
            
            # Surface - Alto contraste
            background="#FFFFFF",
            foreground="#000000",
            muted="#F0F0F0",
            mutedForeground="#000000",
            accent="#F0F0F0",
            accentForeground="#000000",
            
            # Interactive - Alto contraste
            border="#000000",
            input="#FFFFFF",
            ring="#000000",
            
            # Card - Alto contraste
            card="#FFFFFF",
            cardForeground="#000000",
            
            # Popover - Alto contraste
            popover="#FFFFFF",
            popoverForeground="#000000",
        )
        
        # Typography com pesos mais fortes para melhor legibilidade
        typography = {
            "fontFamily": {
                "sans": DatametriaTypography.FONT_SANS,
                "serif": DatametriaTypography.FONT_SERIF,
                "mono": DatametriaTypography.FONT_MONO,
            },
            "fontSize": {
                "xs": "0.875rem",  # Tamanhos maiores para melhor legibilidade
                "sm": "1rem",
                "base": "1.125rem",
                "lg": "1.25rem",
                "xl": "1.5rem",
                "2xl": "1.75rem",
                "3xl": "2rem",
                "4xl": "2.5rem",
                "5xl": "3rem",
            },
            "lineHeight": {
                "tight": "1.375",   # Line heights maiores
                "snug": "1.5",
                "normal": "1.625",
                "relaxed": "1.75",
                "loose": "2.25",
            }
        }
        
        # Spacing igual ao tema padrão
        light_theme = LightTheme.create()
        
        return DatametriaTheme(
            name="high-contrast",
            colors=colors,
            typography=typography,
            spacing=light_theme.spacing
        )


class ThemeManager:
    """Gerenciador de temas DATAMETRIA"""
    
    def __init__(self):
        self._themes = {
            "light": LightTheme.create(),
            "dark": DarkTheme.create(),
            "high-contrast": HighContrastTheme.create(),
        }
        self._current_theme = "light"
    
    def get_theme(self, name: str) -> Optional[DatametriaTheme]:
        """Obtém tema por nome"""
        return self._themes.get(name)
    
    def set_current_theme(self, name: str) -> bool:
        """Define tema atual"""
        if name in self._themes:
            self._current_theme = name
            return True
        return False
    
    def get_current_theme(self) -> DatametriaTheme:
        """Obtém tema atual"""
        return self._themes[self._current_theme]
    
    def register_theme(self, theme: DatametriaTheme) -> None:
        """Registra novo tema customizado"""
        self._themes[theme.name] = theme
    
    def list_themes(self) -> list[str]:
        """Lista todos os temas disponíveis"""
        return list(self._themes.keys())
    
    def generate_css(self, theme_name: Optional[str] = None) -> str:
        """Gera CSS com variáveis do tema"""
        theme = self.get_theme(theme_name) if theme_name else self.get_current_theme()
        if not theme:
            return ""
        
        css_vars = theme.to_css_variables()
        css_rules = []
        
        # Root variables
        css_rules.append(":root {")
        for var_name, var_value in css_vars.items():
            css_rules.append(f"  {var_name}: {var_value};")
        css_rules.append("}")
        
        # Dark theme media query
        if theme.name == "dark":
            css_rules.append("")
            css_rules.append("@media (prefers-color-scheme: dark) {")
            css_rules.append("  :root {")
            for var_name, var_value in css_vars.items():
                css_rules.append(f"    {var_name}: {var_value};")
            css_rules.append("  }")
            css_rules.append("}")
        
        return "\n".join(css_rules)


# Instância global do gerenciador de temas
theme_manager = ThemeManager()

# Export
__all__ = [
    "ThemeColors",
    "DatametriaTheme", 
    "LightTheme",
    "DarkTheme",
    "HighContrastTheme",
    "ThemeManager",
    "theme_manager",
]
