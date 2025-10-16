"""
Gerador de Componentes Vue.js DATAMETRIA

Utilitário para gerar componentes Vue.js completos integrados
com o Design System DATAMETRIA.
"""

from typing import Dict, List, Optional
from pathlib import Path
from ..design_system import css_generator, theme_manager
from .base import VueComponentGenerator
from .composables import VueComposablesGenerator


class VueProjectGenerator:
    """Gerador completo de projeto Vue.js com Design System"""
    
    def __init__(self):
        self.components = VueComponentGenerator()
        self.composables = VueComposablesGenerator()
    
    def generate_package_json(self) -> str:
        """Gera package.json para projeto Vue.js"""
        return '''
{
  "name": "@datametria/vue-components",
  "version": "1.0.0",
  "description": "DATAMETRIA Vue.js 3 Component Library with Design System",
  "main": "dist/index.js",
  "module": "dist/index.esm.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist"
  ],
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
    "type-check": "vue-tsc --noEmit"
  },
  "dependencies": {
    "vue": "^3.4.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "@vue/eslint-config-prettier": "^9.0.0",
    "@vue/eslint-config-typescript": "^12.0.0",
    "@vue/test-utils": "^2.4.0",
    "@vue/tsconfig": "^0.5.0",
    "eslint": "^8.57.0",
    "eslint-plugin-vue": "^9.20.0",
    "jsdom": "^24.0.0",
    "prettier": "^3.2.0",
    "typescript": "~5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.2.0",
    "vue-tsc": "^1.8.27"
  },
  "peerDependencies": {
    "vue": "^3.4.0"
  },
  "keywords": [
    "vue",
    "vue3",
    "components",
    "design-system",
    "datametria",
    "typescript",
    "enterprise"
  ],
  "author": "DATAMETRIA Team",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/datametria/DATAMETRIA-common-libraries"
  }
}
'''
    
    def generate_vite_config(self) -> str:
        """Gera configuração do Vite"""
        return '''
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'DatametriaVueComponents',
      fileName: (format) => `index.${format}.js`
    },
    rollupOptions: {
      external: ['vue'],
      output: {
        globals: {
          vue: 'Vue'
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "@/styles/variables.scss";`
      }
    }
  }
})
'''
    
    def generate_tsconfig(self) -> str:
        """Gera configuração TypeScript"""
        return '''
{
  "extends": "@vue/tsconfig/tsconfig.dom.json",
  "include": [
    "env.d.ts",
    "src/**/*",
    "src/**/*.vue"
  ],
  "exclude": [
    "src/**/__tests__/*"
  ],
  "compilerOptions": {
    "composite": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },
    "declaration": true,
    "declarationDir": "dist",
    "emitDeclarationOnly": false,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "skipLibCheck": true
  }
}
'''
    
    def generate_main_index(self) -> str:
        """Gera index.ts principal"""
        return '''
import type { App } from 'vue'

// Components
export { default as DatametriaButton } from './components/DatametriaButton.vue'
export { default as DatametriaInput } from './components/DatametriaInput.vue'
export { default as DatametriaCard } from './components/DatametriaCard.vue'
export { default as DatametriaSelect } from './components/DatametriaSelect.vue'
export { default as DatametriaTextarea } from './components/DatametriaTextarea.vue'
export { default as DatametriaCheckbox } from './components/DatametriaCheckbox.vue'
export { default as DatametriaRadio } from './components/DatametriaRadio.vue'
export { default as DatametriaSwitch } from './components/DatametriaSwitch.vue'
export { default as DatametriaModal } from './components/DatametriaModal.vue'
export { default as DatametriaToast } from './components/DatametriaToast.vue'
export { default as DatametriaAlert } from './components/DatametriaAlert.vue'
export { default as DatametriaNavbar } from './components/DatametriaNavbar.vue'
export { default as DatametriaTabs } from './components/DatametriaTabs.vue'
export { default as DatametriaTable } from './components/DatametriaTable.vue'

// Composables
export { useTheme } from './composables/useTheme'
export { useValidation } from './composables/useValidation'
export { useAPI } from './composables/useAPI'
export { useI18n } from './composables/useI18n'

// Types
export * from './types'

// Design System Integration
export { css_generator, theme_manager } from './design-system'

// Plugin
import DatametriaButton from './components/DatametriaButton.vue'
import DatametriaInput from './components/DatametriaInput.vue'
import DatametriaCard from './components/DatametriaCard.vue'
// ... outros componentes

const components = {
  DatametriaButton,
  DatametriaInput,
  DatametriaCard,
  // ... outros componentes
}

export default {
  install(app: App) {
    // Registrar todos os componentes globalmente
    Object.entries(components).forEach(([name, component]) => {
      app.component(name, component)
    })
    
    // Injetar CSS do Design System
    if (typeof document !== 'undefined') {
      const style = document.createElement('style')
      style.textContent = css_generator.generate_full_css('light')
      document.head.appendChild(style)
    }
  }
}
'''
    
    def generate_types_file(self) -> str:
        """Gera arquivo de tipos TypeScript"""
        return '''
// Design System Types
export enum ButtonVariant {
  PRIMARY = 'primary',
  SECONDARY = 'secondary',
  OUTLINE = 'outline',
  GHOST = 'ghost',
  LINK = 'link',
  DESTRUCTIVE = 'destructive'
}

export enum ButtonSize {
  SM = 'sm',
  MD = 'md',
  LG = 'lg',
  XL = 'xl'
}

export enum InputType {
  TEXT = 'text',
  EMAIL = 'email',
  PASSWORD = 'password',
  NUMBER = 'number',
  TEL = 'tel',
  URL = 'url',
  SEARCH = 'search'
}

export enum InputSize {
  SM = 'sm',
  MD = 'md',
  LG = 'lg'
}

export enum CardVariant {
  DEFAULT = 'default',
  OUTLINED = 'outlined',
  ELEVATED = 'elevated'
}

// Component Props
export interface ButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
  iconLeft?: string
  iconRight?: string
  text?: string
  type?: 'button' | 'submit' | 'reset'
}

export interface InputProps {
  modelValue?: string | number
  type?: InputType
  size?: InputSize
  label?: string
  placeholder?: string
  helpText?: string
  errorMessage?: string
  disabled?: boolean
  readonly?: boolean
  required?: boolean
  iconLeft?: string
  iconRight?: string
}

export interface CardProps {
  variant?: CardVariant
  padding?: boolean
  title?: string
  description?: string
}

// Theme Types
export interface ThemeConfig {
  name: string
  colors: Record<string, string>
  typography: Record<string, any>
  spacing: Record<string, string>
}

// Validation Types
export interface ValidationRule {
  validator: (value: any) => boolean | string
  message?: string
}

export interface FieldValidation {
  value: any
  rules: ValidationRule[]
  error: string | null
  touched: boolean
  valid: boolean
}

// API Types
export interface ApiConfig {
  baseURL?: string
  timeout?: number
  headers?: Record<string, string>
}

export interface ApiResponse<T = any> {
  data: T
  status: number
  statusText: string
  headers: Record<string, string>
}

// I18n Types
export interface I18nMessages {
  [key: string]: string | I18nMessages
}

export interface I18nConfig {
  locale: string
  fallbackLocale: string
  messages: Record<string, I18nMessages>
}
'''
    
    def generate_example_app(self) -> str:
        """Gera aplicação de exemplo"""
        return '''
<template>
  <div id="app">
    <!-- Theme Toggle -->
    <div class="theme-controls">
      <DatametriaButton @click="toggleTheme" variant="outline" size="sm">
        {{ isDark ? '☀️' : '🌙' }} {{ isDark ? 'Light' : 'Dark' }}
      </DatametriaButton>
    </div>
    
    <!-- Header -->
    <DatametriaNavbar>
      <template #brand>
        <h1>DATAMETRIA Vue Components</h1>
      </template>
      <template #nav>
        <a href="#components">Componentes</a>
        <a href="#forms">Formulários</a>
        <a href="#examples">Exemplos</a>
      </template>
    </DatametriaNavbar>
    
    <!-- Main Content -->
    <div class="container">
      <DatametriaCard title="Exemplo de Formulário" padding>
        <form @submit.prevent="handleSubmit" class="form-example">
          <DatametriaInput
            v-model="form.name"
            label="Nome Completo"
            placeholder="Digite seu nome"
            :error-message="getFieldError('name')"
            required
          />
          
          <DatametriaInput
            v-model="form.email"
            type="email"
            label="Email"
            placeholder="seu@email.com"
            :error-message="getFieldError('email')"
            required
          />
          
          <DatametriaTextarea
            v-model="form.message"
            label="Mensagem"
            placeholder="Sua mensagem..."
            :error-message="getFieldError('message')"
            rows="4"
          />
          
          <div class="form-actions">
            <DatametriaButton type="button" variant="outline" @click="resetForm">
              Limpar
            </DatametriaButton>
            <DatametriaButton type="submit" :loading="loading">
              Enviar
            </DatametriaButton>
          </div>
        </form>
      </DatametriaCard>
      
      <!-- Components Showcase -->
      <DatametriaCard title="Showcase de Componentes" padding>
        <div class="components-grid">
          <!-- Buttons -->
          <div class="component-section">
            <h3>Buttons</h3>
            <div class="button-group">
              <DatametriaButton variant="primary">Primary</DatametriaButton>
              <DatametriaButton variant="secondary">Secondary</DatametriaButton>
              <DatametriaButton variant="outline">Outline</DatametriaButton>
              <DatametriaButton variant="ghost">Ghost</DatametriaButton>
            </div>
          </div>
          
          <!-- Alerts -->
          <div class="component-section">
            <h3>Alerts</h3>
            <DatametriaAlert variant="success" title="Sucesso!">
              Operação realizada com sucesso.
            </DatametriaAlert>
            <DatametriaAlert variant="warning" title="Atenção">
              Verifique os dados antes de continuar.
            </DatametriaAlert>
          </div>
        </div>
      </DatametriaCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTheme, useValidation } from '@datametria/vue-components'

// Theme
const { isDark, toggleTheme } = useTheme()

// Form
const form = ref({
  name: '',
  email: '',
  message: ''
})

const loading = ref(false)

// Validation
const { addField, validateAll, getFieldError, resetAll, rules } = useValidation()

// Setup validation
addField('name', '', [rules.required()])
addField('email', '', [rules.required(), rules.email()])
addField('message', '', [rules.required(), rules.minLength(10)])

const handleSubmit = async () => {
  if (!validateAll()) return
  
  loading.value = true
  
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    alert('Formulário enviado com sucesso!')
    resetForm()
  } catch (error) {
    alert('Erro ao enviar formulário')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = { name: '', email: '', message: '' }
  resetAll()
}
</script>

<style scoped>
.theme-controls {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-example {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.components-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.component-section h3 {
  margin-bottom: 1rem;
  color: var(--dm-foreground);
}

.button-group {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
'''
    
    def generate_project_structure(self, output_dir: str) -> Dict[str, str]:
        """Gera estrutura completa do projeto Vue.js"""
        files = {
            "package.json": self.generate_package_json(),
            "vite.config.ts": self.generate_vite_config(),
            "tsconfig.json": self.generate_tsconfig(),
            "src/index.ts": self.generate_main_index(),
            "src/types/index.ts": self.generate_types_file(),
            "src/App.vue": self.generate_example_app(),
            
            # Componentes
            "src/components/DatametriaButton.vue": self.components.generate_button_component(),
            "src/components/DatametriaInput.vue": self.components.generate_input_component(),
            "src/components/DatametriaCard.vue": self.components.generate_card_component(),
            
            # Composables
            "src/composables/useTheme.ts": self.composables.generate_use_theme(),
            "src/composables/useValidation.ts": self.composables.generate_use_validation(),
            "src/composables/useAPI.ts": self.composables.generate_use_api(),
            "src/composables/useI18n.ts": self.composables.generate_use_i18n(),
            
            # CSS do Design System
            "src/styles/datametria.css": css_generator.generate_full_css("light"),
            "src/styles/datametria-dark.css": css_generator.generate_full_css("dark"),
        }
        
        return files
    
    def save_project(self, output_dir: str) -> None:
        """Salva projeto Vue.js completo"""
        files = self.generate_project_structure(output_dir)
        output_path = Path(output_dir)
        
        for file_path, content in files.items():
            full_path = output_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)


# Instância global
vue_generator = VueProjectGenerator()

# Export
__all__ = [
    "VueProjectGenerator",
    "vue_generator",
]
