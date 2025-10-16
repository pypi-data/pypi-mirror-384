"""
DATAMETRIA Component Factory - Cross-Platform Component Generation

Factory for generating consistent UI components across Vue.js, React Native, and Flutter.
"""

from typing import Dict, Any, Optional
from enum import Enum
from .design_tokens import DesignTokens


class Platform(Enum):
    """Supported platforms."""
    VUE = "vue"
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"


class ComponentFactory:
    """Factory for generating cross-platform UI components."""
    
    def __init__(self, platform: Platform):
        self.platform = platform
        self.tokens = DesignTokens()
    
    def generate_button(self, variant: str = "primary", size: str = "base") -> Dict[str, Any]:
        """Generate button component definition."""
        if self.platform == Platform.VUE:
            return self._generate_vue_button(variant, size)
        elif self.platform == Platform.REACT_NATIVE:
            return self._generate_rn_button(variant, size)
        elif self.platform == Platform.FLUTTER:
            return self._generate_flutter_button(variant, size)
    
    def generate_input(self, type: str = "text") -> Dict[str, Any]:
        """Generate input component definition."""
        if self.platform == Platform.VUE:
            return self._generate_vue_input(type)
        elif self.platform == Platform.REACT_NATIVE:
            return self._generate_rn_input(type)
        elif self.platform == Platform.FLUTTER:
            return self._generate_flutter_input(type)
    
    def _generate_vue_button(self, variant: str, size: str) -> Dict[str, Any]:
        """Generate Vue.js button component."""
        return {
            "template": f"""
<button 
  :class="buttonClasses" 
  @click="$emit('click')"
>
  <slot />
</button>""",
            "style": f"""
.btn-{variant} {{
  background-color: {self.tokens.get_color(variant)};
  color: white;
  padding: {self.tokens.SPACING['4']};
  border: none;
  border-radius: 4px;
  font-size: {self.tokens.TYPOGRAPHY['fontSize'][size]};
}}"""
        }
    
    def _generate_rn_button(self, variant: str, size: str) -> Dict[str, Any]:
        """Generate React Native button component."""
        return {
            "component": "TouchableOpacity",
            "style": {
                "backgroundColor": self.tokens.get_color(variant),
                "padding": int(self.tokens.SPACING['4'].replace('px', '')),
                "borderRadius": 4
            },
            "textStyle": {
                "color": "white",
                "fontSize": int(self.tokens.TYPOGRAPHY['fontSize'][size].replace('px', ''))
            }
        }
    
    def _generate_flutter_button(self, variant: str, size: str) -> Dict[str, Any]:
        """Generate Flutter button component."""
        return {
            "widget": "ElevatedButton",
            "style": {
                "backgroundColor": self.tokens.get_color(variant),
                "padding": f"EdgeInsets.all({self.tokens.SPACING['4'].replace('px', '')})",
                "shape": "RoundedRectangleBorder(borderRadius: BorderRadius.circular(4))"
            },
            "textStyle": {
                "fontSize": float(self.tokens.TYPOGRAPHY['fontSize'][size].replace('px', ''))
            }
        }
    
    def _generate_vue_input(self, type: str) -> Dict[str, Any]:
        """Generate Vue.js input component."""
        return {
            "template": f"""
<input 
  type="{type}"
  :value="modelValue"
  @input="$emit('update:modelValue', $event.target.value)"
  class="datametria-input"
/>""",
            "style": """
.datametria-input {
  border: 1px solid #E0E0E0;
  padding: 12px;
  border-radius: 4px;
  font-size: 16px;
}"""
        }
    
    def _generate_rn_input(self, type: str) -> Dict[str, Any]:
        """Generate React Native input component."""
        return {
            "component": "TextInput",
            "style": {
                "borderWidth": 1,
                "borderColor": "#E0E0E0",
                "padding": 12,
                "borderRadius": 4,
                "fontSize": 16
            },
            "props": {
                "secureTextEntry": type == "password"
            }
        }
    
    def _generate_flutter_input(self, type: str) -> Dict[str, Any]:
        """Generate Flutter input component."""
        return {
            "widget": "TextField",
            "decoration": {
                "border": "OutlineInputBorder()",
                "contentPadding": "EdgeInsets.all(12)"
            },
            "style": {
                "fontSize": 16.0
            },
            "obscureText": type == "password"
        }
