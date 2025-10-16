"""
Composables Vue.js DATAMETRIA

Composables reutilizáveis integrados com o Design System:
useTheme, useValidation, useAPI, useI18n
"""

from typing import Dict, Any, Optional, List, Callable
from ..design_system import theme_manager, ThemeManager


class VueComposablesGenerator:
    """Gerador de composables Vue.js integrados com Design System"""
    
    @staticmethod
    def generate_use_theme() -> str:
        """Gera composable useTheme integrado com Design System"""
        return '''
import { ref, computed, watch, onMounted } from 'vue'
import { theme_manager } from '../design_system'

export interface ThemeConfig {
  name: string
  colors: Record<string, string>
  typography: Record<string, any>
  spacing: Record<string, string>
}

export function useTheme() {
  const currentTheme = ref<string>('light')
  const isDark = computed(() => currentTheme.value === 'dark')
  const isHighContrast = computed(() => currentTheme.value === 'high-contrast')
  
  // Integração com Design System Python
  const setTheme = (themeName: string) => {
    if (theme_manager.set_current_theme(themeName)) {
      currentTheme.value = themeName
      updateCSSVariables()
      localStorage.setItem('datametria-theme', themeName)
    }
  }
  
  const toggleTheme = () => {
    const newTheme = isDark.value ? 'light' : 'dark'
    setTheme(newTheme)
  }
  
  const updateCSSVariables = () => {
    const theme = theme_manager.get_current_theme()
    const cssVars = theme.to_css_variables()
    
    Object.entries(cssVars).forEach(([key, value]) => {
      document.documentElement.style.setProperty(key, value)
    })
  }
  
  const getThemeConfig = (): ThemeConfig => {
    const theme = theme_manager.get_current_theme()
    return {
      name: theme.name,
      colors: theme.colors,
      typography: theme.typography,
      spacing: theme.spacing
    }
  }
  
  // Auto-detect system theme
  const detectSystemTheme = () => {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
    return 'light'
  }
  
  // Initialize theme
  onMounted(() => {
    const savedTheme = localStorage.getItem('datametria-theme')
    const initialTheme = savedTheme || detectSystemTheme()
    setTheme(initialTheme)
    
    // Listen for system theme changes
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', (e) => {
        if (!localStorage.getItem('datametria-theme')) {
          setTheme(e.matches ? 'dark' : 'light')
        }
      })
    }
  })
  
  return {
    currentTheme: computed(() => currentTheme.value),
    isDark,
    isHighContrast,
    setTheme,
    toggleTheme,
    getThemeConfig,
    availableThemes: computed(() => theme_manager.list_themes())
  }
}
'''
    
    @staticmethod
    def generate_use_validation() -> str:
        """Gera composable useValidation"""
        return '''
import { ref, computed, reactive } from 'vue'

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

export function useValidation() {
  const fields = reactive<Record<string, FieldValidation>>({})
  
  const addField = (name: string, initialValue: any = '', rules: ValidationRule[] = []) => {
    fields[name] = {
      value: initialValue,
      rules,
      error: null,
      touched: false,
      valid: true
    }
  }
  
  const validateField = (name: string): boolean => {
    const field = fields[name]
    if (!field) return true
    
    field.touched = true
    
    for (const rule of field.rules) {
      const result = rule.validator(field.value)
      if (result !== true) {
        field.error = typeof result === 'string' ? result : rule.message || 'Invalid value'
        field.valid = false
        return false
      }
    }
    
    field.error = null
    field.valid = true
    return true
  }
  
  const validateAll = (): boolean => {
    let allValid = true
    Object.keys(fields).forEach(name => {
      if (!validateField(name)) {
        allValid = false
      }
    })
    return allValid
  }
  
  const resetField = (name: string) => {
    const field = fields[name]
    if (field) {
      field.error = null
      field.touched = false
      field.valid = true
    }
  }
  
  const resetAll = () => {
    Object.keys(fields).forEach(resetField)
  }
  
  const setFieldValue = (name: string, value: any) => {
    const field = fields[name]
    if (field) {
      field.value = value
      if (field.touched) {
        validateField(name)
      }
    }
  }
  
  const getFieldError = (name: string): string | null => {
    return fields[name]?.error || null
  }
  
  const isFieldValid = (name: string): boolean => {
    return fields[name]?.valid ?? true
  }
  
  const isFormValid = computed(() => {
    return Object.values(fields).every(field => field.valid)
  })
  
  const hasErrors = computed(() => {
    return Object.values(fields).some(field => field.error)
  })
  
  // Validation rules
  const rules = {
    required: (message = 'Campo obrigatório'): ValidationRule => ({
      validator: (value) => {
        if (value === null || value === undefined || value === '') {
          return false
        }
        if (Array.isArray(value) && value.length === 0) {
          return false
        }
        return true
      },
      message
    }),
    
    email: (message = 'Email inválido'): ValidationRule => ({
      validator: (value) => {
        if (!value) return true
        const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/
        return emailRegex.test(value)
      },
      message
    }),
    
    minLength: (min: number, message?: string): ValidationRule => ({
      validator: (value) => {
        if (!value) return true
        return value.length >= min
      },
      message: message || `Mínimo ${min} caracteres`
    }),
    
    maxLength: (max: number, message?: string): ValidationRule => ({
      validator: (value) => {
        if (!value) return true
        return value.length <= max
      },
      message: message || `Máximo ${max} caracteres`
    }),
    
    pattern: (regex: RegExp, message = 'Formato inválido'): ValidationRule => ({
      validator: (value) => {
        if (!value) return true
        return regex.test(value)
      },
      message
    })
  }
  
  return {
    fields,
    addField,
    validateField,
    validateAll,
    resetField,
    resetAll,
    setFieldValue,
    getFieldError,
    isFieldValid,
    isFormValid,
    hasErrors,
    rules
  }
}
'''
    
    @staticmethod
    def generate_use_api() -> str:
        """Gera composable useAPI"""
        return '''
import { ref, computed } from 'vue'

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

export function useAPI(config: ApiConfig = {}) {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const data = ref<any>(null)
  
  const defaultConfig: ApiConfig = {
    baseURL: '',
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json'
    },
    ...config
  }
  
  const request = async <T = any>(
    url: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> => {
    loading.value = true
    error.value = null
    
    try {
      const fullUrl = defaultConfig.baseURL + url
      const response = await fetch(fullUrl, {
        ...options,
        headers: {
          ...defaultConfig.headers,
          ...options.headers
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const responseData = await response.json()
      data.value = responseData
      
      return {
        data: responseData,
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }
  
  const get = <T = any>(url: string, params?: Record<string, any>) => {
    const searchParams = params ? new URLSearchParams(params).toString() : ''
    const fullUrl = searchParams ? `${url}?${searchParams}` : url
    return request<T>(fullUrl, { method: 'GET' })
  }
  
  const post = <T = any>(url: string, body?: any) => {
    return request<T>(url, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined
    })
  }
  
  const put = <T = any>(url: string, body?: any) => {
    return request<T>(url, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined
    })
  }
  
  const del = <T = any>(url: string) => {
    return request<T>(url, { method: 'DELETE' })
  }
  
  return {
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    data: computed(() => data.value),
    request,
    get,
    post,
    put,
    delete: del
  }
}
'''
    
    @staticmethod
    def generate_use_i18n() -> str:
        """Gera composable useI18n"""
        return '''
import { ref, computed } from 'vue'

export interface I18nMessages {
  [key: string]: string | I18nMessages
}

export interface I18nConfig {
  locale: string
  fallbackLocale: string
  messages: Record<string, I18nMessages>
}

export function useI18n(config: I18nConfig) {
  const currentLocale = ref(config.locale)
  const messages = ref(config.messages)
  
  const t = (key: string, params?: Record<string, any>): string => {
    const keys = key.split('.')
    let message: any = messages.value[currentLocale.value]
    
    for (const k of keys) {
      if (message && typeof message === 'object' && k in message) {
        message = message[k]
      } else {
        // Fallback to fallback locale
        message = messages.value[config.fallbackLocale]
        for (const k of keys) {
          if (message && typeof message === 'object' && k in message) {
            message = message[k]
          } else {
            return key // Return key if not found
          }
        }
        break
      }
    }
    
    if (typeof message !== 'string') {
      return key
    }
    
    // Replace parameters
    if (params) {
      return message.replace(/\\{(\\w+)\\}/g, (match, param) => {
        return params[param] || match
      })
    }
    
    return message
  }
  
  const setLocale = (locale: string) => {
    if (locale in messages.value) {
      currentLocale.value = locale
      localStorage.setItem('datametria-locale', locale)
    }
  }
  
  const addMessages = (locale: string, newMessages: I18nMessages) => {
    if (!messages.value[locale]) {
      messages.value[locale] = {}
    }
    messages.value[locale] = { ...messages.value[locale], ...newMessages }
  }
  
  return {
    locale: computed(() => currentLocale.value),
    t,
    setLocale,
    addMessages,
    availableLocales: computed(() => Object.keys(messages.value))
  }
}
'''


# Classes Python para os composables
class UseTheme:
    """Wrapper Python para composable useTheme"""
    
    def __init__(self):
        self.composable_code = VueComposablesGenerator.generate_use_theme()
    
    def get_composable(self) -> str:
        return self.composable_code


class UseValidation:
    """Wrapper Python para composable useValidation"""
    
    def __init__(self):
        self.composable_code = VueComposablesGenerator.generate_use_validation()
    
    def get_composable(self) -> str:
        return self.composable_code


class UseAPI:
    """Wrapper Python para composable useAPI"""
    
    def __init__(self):
        self.composable_code = VueComposablesGenerator.generate_use_api()
    
    def get_composable(self) -> str:
        return self.composable_code


class UseI18n:
    """Wrapper Python para composable useI18n"""
    
    def __init__(self):
        self.composable_code = VueComposablesGenerator.generate_use_i18n()
    
    def get_composable(self) -> str:
        return self.composable_code


# Export
__all__ = [
    "VueComposablesGenerator",
    "UseTheme",
    "UseValidation", 
    "UseAPI",
    "UseI18n",
]
