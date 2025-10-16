"""
DATAMETRIA Design Tokens - Cross-Platform Design System

Universal design tokens for consistent visual identity across
Vue.js, React Native, and Flutter platforms.
"""

from typing import Dict, Any
from enum import Enum


class ColorScheme(Enum):
    """Color scheme variants."""
    LIGHT = "light"
    DARK = "dark"


class DesignTokens:
    """Universal design tokens for DATAMETRIA platforms."""
    
    # Color Palette
    COLORS = {
        "primary": {
            "500": "#2196F3",
            "600": "#1976D2"
        },
        "secondary": {
            "500": "#9C27B0", 
            "600": "#7B1FA2"
        },
        "success": {"500": "#4CAF50"},
        "warning": {"500": "#FF9800"},
        "error": {"500": "#F44336"},
        "neutral": {
            "0": "#FFFFFF",
            "50": "#FAFAFA",
            "500": "#9E9E9E",
            "900": "#212121"
        }
    }
    
    # Typography
    TYPOGRAPHY = {
        "fontSize": {
            "sm": "14px", 
            "base": "16px",
            "lg": "18px",
            "xl": "24px"
        },
        "fontWeight": {
            "normal": "400",
            "semibold": "600",
            "bold": "700"
        }
    }
    
    # Spacing
    SPACING = {
        "2": "8px", 
        "4": "16px",
        "6": "24px",
        "8": "32px"
    }
    
    @classmethod
    def get_color(cls, color: str, shade: str = "500", scheme: ColorScheme = ColorScheme.LIGHT) -> str:
        """Get color value."""
        return cls.COLORS.get(color, {}).get(shade, "#000000")
    
    @classmethod
    def to_css_variables(cls) -> str:
        """Generate CSS custom properties."""
        css_vars = []
        for color_name, shades in cls.COLORS.items():
            for shade, value in shades.items():
                css_vars.append(f"  --color-{color_name}-{shade}: {value};")
        return ":root {\n" + "\n".join(css_vars) + "\n}"
    
    @classmethod
    def to_flutter_theme(cls) -> Dict[str, Any]:
        """Generate Flutter theme data."""
        return {
            "colorScheme": {
                "primary": cls.get_color("primary"),
                "secondary": cls.get_color("secondary"),
                "surface": cls.get_color("neutral", "0"),
                "error": cls.get_color("error")
            },
            "spacing": cls.SPACING
        }
    
    @classmethod
    def to_react_native_theme(cls) -> Dict[str, Any]:
        """Generate React Native theme object."""
        return {
            "colors": {
                "primary": cls.get_color("primary"),
                "secondary": cls.get_color("secondary"),
                "background": cls.get_color("neutral", "0"),
                "text": cls.get_color("neutral", "900")
            },
            "spacing": {k: int(v.replace("px", "")) for k, v in cls.SPACING.items()}
        }
