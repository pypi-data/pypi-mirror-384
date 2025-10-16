"""
Design Tokens DATAMETRIA

Sistema completo de tokens de design para cores, tipografia, espaçamento,
bordas, sombras e animações seguindo os padrões DATAMETRIA.
"""

from typing import Dict, Any, Union
from dataclasses import dataclass
from enum import Enum


class ColorScale(Enum):
    """Escala de cores padrão (50-950)"""
    LIGHTEST = "50"
    LIGHTER = "100"
    LIGHT = "200"
    LIGHT_MEDIUM = "300"
    MEDIUM_LIGHT = "400"
    BASE = "500"
    MEDIUM_DARK = "600"
    DARK = "700"
    DARKER = "800"
    DARKEST = "900"
    ULTRA_DARK = "950"


@dataclass
class ColorPalette:
    """Paleta de cores com escala completa"""
    c50: str   # Mais claro
    c100: str
    c200: str
    c300: str
    c400: str
    c500: str  # Base
    c600: str
    c700: str
    c800: str
    c900: str
    c950: str  # Mais escuro
    
    def get(self, scale: Union[str, ColorScale]) -> str:
        """Obtém cor por escala"""
        if isinstance(scale, ColorScale):
            scale = scale.value
        return getattr(self, f"c{scale}")


class DatametriaColors:
    """Sistema de cores DATAMETRIA"""
    
    # Brand Colors - DATAMETRIA Official
    PRIMARY = ColorPalette(
        c50='#E3F2FD',
        c100='#BBDEFB',
        c200='#90CAF9',
        c300='#64B5F6',
        c400='#42A5F5',
        c500='#0072CE',  # Azul oficial do logo
        c600='#1565C0',
        c700='#0D47A1',
        c800='#0A3D8C',
        c900='#073370',
        c950='#042a71'
    )
    
    SECONDARY = ColorPalette(
        c50='#F3E5F5',
        c100='#E1BEE7',
        c200='#CE93D8',
        c300='#BA68C8',
        c400='#AB47BC',
        c500='#4B0078',  # Roxo oficial do logo
        c600='#7B1FA2',
        c700='#6A1B9A',
        c800='#4A148C',
        c900='#38006B',
        c950='#1f0033'
    )
    
    # Gradient Colors - DATAMETRIA Official
    GRADIENT_BLUE = ColorPalette(
        c50='#e6f8fd',
        c100='#b3ecfa',
        c200='#80e0f7',
        c300='#4dd4f4',
        c400='#26cbf1',
        c500='#00AEEF',  # Gradiente azul
        c600='#009dd7',
        c700='#008bbf',
        c800='#0079a7',
        c900='#00678f',
        c950='#005577'
    )
    
    GRADIENT_PURPLE = ColorPalette(
        c50='#f3e9f8',
        c100='#dac2ec',
        c200='#c19be0',
        c300='#a874d4',
        c400='#8f4dc8',
        c500='#6C1E9F',  # Gradiente roxo
        c600='#611b8f',
        c700='#56187f',
        c800='#4b156f',
        c900='#40125f',
        c950='#350f4f'
    )
    
    # Semantic Colors
    SUCCESS = ColorPalette(
        c50='#f0fdf4',
        c100='#dcfce7',
        c200='#bbf7d0',
        c300='#86efac',
        c400='#4ade80',
        c500='#22c55e',  # Base
        c600='#16a34a',
        c700='#15803d',
        c800='#166534',
        c900='#14532d',
        c950='#0f3f23'
    )
    
    WARNING = ColorPalette(
        c50='#fffbeb',
        c100='#fef3c7',
        c200='#fde68a',
        c300='#fcd34d',
        c400='#fbbf24',
        c500='#f59e0b',  # Base
        c600='#d97706',
        c700='#b45309',
        c800='#92400e',
        c900='#78350f',
        c950='#5c2a0c'
    )
    
    ERROR = ColorPalette(
        c50='#fef2f2',
        c100='#fee2e2',
        c200='#fecaca',
        c300='#fca5a5',
        c400='#f87171',
        c500='#ef4444',  # Base
        c600='#dc2626',
        c700='#b91c1c',
        c800='#991b1b',
        c900='#7f1d1d',
        c950='#651818'
    )
    
    INFO = ColorPalette(
        c50='#eff6ff',
        c100='#dbeafe',
        c200='#bfdbfe',
        c300='#93c5fd',
        c400='#60a5fa',
        c500='#3b82f6',  # Base
        c600='#2563eb',
        c700='#1d4ed8',
        c800='#1e40af',
        c900='#1e3a8a',
        c950='#172e78'
    )
    
    # Neutral Colors
    GRAY = ColorPalette(
        c50='#f9fafb',
        c100='#f3f4f6',
        c200='#e5e7eb',
        c300='#d1d5db',
        c400='#9ca3af',
        c500='#6b7280',  # Base
        c600='#4b5563',
        c700='#374151',
        c800='#1f2937',
        c900='#111827',
        c950='#0a0e1a'
    )


@dataclass
class TypographyScale:
    """Escala tipográfica responsiva"""
    fontSize: str
    lineHeight: str
    letterSpacing: str
    fontWeight: str


class DatametriaTypography:
    """Sistema tipográfico DATAMETRIA"""
    
    # Font Families
    FONT_SANS = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    FONT_SERIF = "'Merriweather', Georgia, serif"
    FONT_MONO = "'JetBrains Mono', 'Fira Code', Consolas, monospace"
    
    # Typography Scales
    DISPLAY_2XL = TypographyScale("4.5rem", "1", "-0.025em", "800")
    DISPLAY_XL = TypographyScale("3.75rem", "1", "-0.025em", "800")
    DISPLAY_LG = TypographyScale("3rem", "1.1", "-0.025em", "700")
    DISPLAY_MD = TypographyScale("2.25rem", "1.2", "-0.025em", "700")
    DISPLAY_SM = TypographyScale("1.875rem", "1.3", "-0.025em", "600")
    DISPLAY_XS = TypographyScale("1.5rem", "1.4", "-0.025em", "600")
    
    HEADING_XL = TypographyScale("1.25rem", "1.5", "-0.025em", "600")
    HEADING_LG = TypographyScale("1.125rem", "1.5", "-0.025em", "600")
    HEADING_MD = TypographyScale("1rem", "1.5", "-0.025em", "600")
    HEADING_SM = TypographyScale("0.875rem", "1.5", "-0.025em", "600")
    
    BODY_XL = TypographyScale("1.25rem", "1.6", "0", "400")
    BODY_LG = TypographyScale("1.125rem", "1.6", "0", "400")
    BODY_MD = TypographyScale("1rem", "1.6", "0", "400")
    BODY_SM = TypographyScale("0.875rem", "1.6", "0", "400")
    BODY_XS = TypographyScale("0.75rem", "1.6", "0", "400")


class DatametriaSpacing:
    """Sistema de espaçamento DATAMETRIA"""
    
    # Base spacing unit (0.25rem = 4px)
    UNIT = "0.25rem"
    
    # Spacing scale
    XS = "0.125rem"    # 2px
    SM = "0.25rem"     # 4px
    MD = "0.5rem"      # 8px
    LG = "0.75rem"     # 12px
    XL = "1rem"        # 16px
    XL2 = "1.25rem"    # 20px
    XL3 = "1.5rem"     # 24px
    XL4 = "2rem"       # 32px
    XL5 = "2.5rem"     # 40px
    XL6 = "3rem"       # 48px
    XL7 = "3.5rem"     # 56px
    XL8 = "4rem"       # 64px
    XL9 = "5rem"       # 80px
    XL10 = "6rem"      # 96px
    XL11 = "8rem"      # 128px
    XL12 = "10rem"     # 160px
    XL13 = "12rem"     # 192px
    XL14 = "14rem"     # 224px
    XL15 = "16rem"     # 256px
    XL16 = "20rem"     # 320px
    XL17 = "24rem"     # 384px
    XL18 = "28rem"     # 448px
    XL19 = "32rem"     # 512px


class DatametriaBorders:
    """Sistema de bordas DATAMETRIA"""
    
    # Border widths
    WIDTH_0 = "0"
    WIDTH_1 = "1px"
    WIDTH_2 = "2px"
    WIDTH_4 = "4px"
    WIDTH_8 = "8px"
    
    # Border radius
    RADIUS_NONE = "0"
    RADIUS_SM = "0.125rem"
    RADIUS_MD = "0.25rem"
    RADIUS_LG = "0.375rem"
    RADIUS_XL = "0.5rem"
    RADIUS_2XL = "1rem"
    RADIUS_3XL = "1.5rem"
    RADIUS_FULL = "9999px"


class DatametriaShadows:
    """Sistema de sombras DATAMETRIA"""
    
    NONE = "none"
    SM = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    MD = "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"
    LG = "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"
    XL = "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"
    XL2 = "0 25px 50px -12px rgb(0 0 0 / 0.25)"
    INNER = "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)"


class DatametriaMotion:
    """Sistema de animações DATAMETRIA"""
    
    # Durations
    DURATION_75 = "75ms"
    DURATION_100 = "100ms"
    DURATION_150 = "150ms"
    DURATION_200 = "200ms"
    DURATION_300 = "300ms"
    DURATION_500 = "500ms"
    DURATION_700 = "700ms"
    DURATION_1000 = "1000ms"
    
    # Easing functions
    EASE_LINEAR = "linear"
    EASE_IN = "cubic-bezier(0.4, 0, 1, 1)"
    EASE_OUT = "cubic-bezier(0, 0, 0.2, 1)"
    EASE_IN_OUT = "cubic-bezier(0.4, 0, 0.2, 1)"
    
    # Common transitions
    TRANSITION_ALL = f"all {DURATION_150} {EASE_IN_OUT}"
    TRANSITION_COLORS = f"color {DURATION_150} {EASE_IN_OUT}, background-color {DURATION_150} {EASE_IN_OUT}, border-color {DURATION_150} {EASE_IN_OUT}"
    TRANSITION_OPACITY = f"opacity {DURATION_150} {EASE_IN_OUT}"
    TRANSITION_SHADOW = f"box-shadow {DURATION_150} {EASE_IN_OUT}"
    TRANSITION_TRANSFORM = f"transform {DURATION_150} {EASE_IN_OUT}"


class DatametriaBreakpoints:
    """Sistema de breakpoints responsivos DATAMETRIA"""
    
    XS = "0px"      # Mobile portrait
    SM = "640px"    # Mobile landscape
    MD = "768px"    # Tablet portrait
    LG = "1024px"   # Tablet landscape / Desktop small
    XL = "1280px"   # Desktop medium
    XL2 = "1536px"  # Desktop large
    XL3 = "1920px"  # Desktop extra large
    XL4 = "2560px"  # 4K displays


# Export all token systems
__all__ = [
    "ColorScale",
    "ColorPalette", 
    "DatametriaColors",
    "TypographyScale",
    "DatametriaTypography",
    "DatametriaSpacing",
    "DatametriaBorders",
    "DatametriaShadows",
    "DatametriaMotion",
    "DatametriaBreakpoints",
]

# CSS Variables for Brand Colors
BRAND_CSS_VARIABLES = {
    "--dm-brand-primary-500": "#0072CE",
    "--dm-brand-secondary-500": "#4B0078",
    "--dm-brand-gradient-blue": "#00AEEF",
    "--dm-brand-gradient-purple": "#6C1E9F",
}
