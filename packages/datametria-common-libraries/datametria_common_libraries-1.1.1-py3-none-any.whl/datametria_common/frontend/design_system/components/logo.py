"""
Logo Component DATAMETRIA

Componente reutilizável para exibir o logo da marca em diferentes variantes.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LogoVariant(Enum):
    """Variantes do logo"""
    COMPLETA = "completa"
    LOGOTIPO = "logotipo"
    SIMBOLO = "simbolo"
    ICON = "icon"


class LogoSize(Enum):
    """Tamanhos do logo"""
    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"


@dataclass
class DatametriaLogo:
    """Componente de Logo DATAMETRIA"""
    variant: LogoVariant = LogoVariant.COMPLETA
    size: LogoSize = LogoSize.MD
    theme: str = "light"
    
    def get_path(self, format: str = "svg") -> str:
        """Retorna o path do logo"""
        return f"/assets/logo/datametria-{self.variant.value}.{format}"
    
    def get_classes(self) -> str:
        """Retorna classes CSS do logo"""
        return f"dm-logo dm-logo--{self.variant.value} dm-logo--{self.size.value}"
    
    def get_css(self) -> str:
        """Retorna CSS do componente"""
        return """
/* Logo Component */
.dm-logo {
  display: inline-block;
  vertical-align: middle;
}

.dm-logo img {
  display: block;
  width: 100%;
  height: auto;
}

/* Sizes */
.dm-logo--xs { width: 2rem; height: auto; }
.dm-logo--sm { width: 4rem; height: auto; }
.dm-logo--md { width: 8rem; height: auto; }
.dm-logo--lg { width: 12rem; height: auto; }
.dm-logo--xl { width: 16rem; height: auto; }

/* Variants */
.dm-logo--completa { aspect-ratio: 4 / 1; }
.dm-logo--logotipo { aspect-ratio: 3 / 1; }
.dm-logo--simbolo { aspect-ratio: 1 / 1; }
.dm-logo--icon { aspect-ratio: 1 / 1; }
"""
    
    def to_html(self) -> str:
        """Gera HTML do logo"""
        return f'<img src="{self.get_path()}" alt="DATAMETRIA Logo" class="{self.get_classes()}" />'
    
    def to_vue(self) -> str:
        """Gera template Vue.js"""
        return f'''<template>
  <img 
    :src="logoSrc" 
    alt="DATAMETRIA Logo" 
    :class="logoClasses"
  />
</template>

<script setup>
import {{ computed }} from 'vue'

const props = defineProps({{
  variant: {{
    type: String,
    default: '{self.variant.value}',
    validator: (v) => ['completa', 'logotipo', 'simbolo', 'icon'].includes(v)
  }},
  size: {{
    type: String,
    default: '{self.size.value}',
    validator: (v) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(v)
  }}
}})

const logoSrc = computed(() => `/assets/logo/datametria-${{props.variant}}.svg`)
const logoClasses = computed(() => `dm-logo dm-logo--${{props.variant}} dm-logo--${{props.size}}`)
</script>'''


__all__ = ["DatametriaLogo", "LogoVariant", "LogoSize"]
