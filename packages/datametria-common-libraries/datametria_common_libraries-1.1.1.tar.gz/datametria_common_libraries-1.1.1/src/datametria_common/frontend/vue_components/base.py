"""
Componentes Base Vue.js DATAMETRIA

Componentes fundamentais que integram com o Design System:
Button, Icon, Avatar, Badge
"""

from typing import Dict, Any, Optional, List
from ..design_system import (
    DatametriaButton as DSButton,
    DatametriaIcon as DSIcon,
    DatametriaAvatar as DSAvatar,
    DatametriaBadge as DSBadge,
    ButtonVariant,
    ButtonSize,
    IconSize,
    AvatarSize,
    BadgeVariant,
)


class VueComponentGenerator:
    """Gerador de componentes Vue.js baseados no Design System"""
    
    @staticmethod
    def generate_button_component() -> str:
        """Gera componente Vue Button integrado com Design System"""
        return '''
<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || loading"
    :type="type"
    @click="handleClick"
    v-bind="$attrs"
  >
    <DatametriaIcon
      v-if="iconLeft && !loading"
      :name="iconLeft"
      :size="iconSize"
    />
    
    <DatametriaSpinner
      v-if="loading"
      :size="spinnerSize"
    />
    
    <span v-if="$slots.default || text" class="dm-button-text">
      <slot>{{ text }}</slot>
    </span>
    
    <DatametriaIcon
      v-if="iconRight && !loading"
      :name="iconRight"
      :size="iconSize"
    />
  </button>
</template>

<script setup lang="ts">
import { computed, defineEmits, defineProps } from 'vue'
import { ButtonVariant, ButtonSize } from '../design_system'
import DatametriaIcon from './DatametriaIcon.vue'
import DatametriaSpinner from './DatametriaSpinner.vue'

interface Props {
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

const props = withDefaults(defineProps<Props>(), {
  variant: ButtonVariant.PRIMARY,
  size: ButtonSize.MD,
  disabled: false,
  loading: false,
  fullWidth: false,
  type: 'button'
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

// Integração com Design System
const buttonClasses = computed(() => {
  const dsButton = new DSButton({
    variant: props.variant,
    size: props.size,
    disabled: props.disabled,
    loading: props.loading,
    full_width: props.fullWidth,
    icon_left: props.iconLeft,
    icon_right: props.iconRight
  })
  return dsButton.get_classes()
})

const iconSize = computed(() => {
  switch (props.size) {
    case ButtonSize.SM: return IconSize.SM
    case ButtonSize.LG: return IconSize.LG
    case ButtonSize.XL: return IconSize.XL
    default: return IconSize.MD
  }
})

const spinnerSize = computed(() => {
  switch (props.size) {
    case ButtonSize.SM: return 'sm'
    case ButtonSize.LG: return 'lg'
    case ButtonSize.XL: return 'lg'
    default: return 'md'
  }
})

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>
'''
    
    @staticmethod
    def generate_input_component() -> str:
        """Gera componente Vue Input integrado com Design System"""
        return '''
<template>
  <div class="dm-input-wrapper">
    <label v-if="label" :for="inputId" class="dm-form-label" :class="labelClasses">
      {{ label }}
    </label>
    
    <div class="dm-input-container" :class="containerClasses">
      <DatametriaIcon
        v-if="iconLeft"
        :name="iconLeft"
        class="dm-input-icon dm-input-icon--left"
      />
      
      <input
        :id="inputId"
        ref="inputRef"
        :class="inputClasses"
        :type="type"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :value="modelValue"
        v-bind="$attrs"
        @input="handleInput"
        @blur="handleBlur"
        @focus="handleFocus"
      />
      
      <DatametriaIcon
        v-if="iconRight"
        :name="iconRight"
        class="dm-input-icon dm-input-icon--right"
      />
    </div>
    
    <div v-if="helpText || errorMessage" class="dm-input-help">
      <span v-if="errorMessage" class="dm-form-error">{{ errorMessage }}</span>
      <span v-else-if="helpText" class="dm-form-help">{{ helpText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, defineEmits, defineProps } from 'vue'
import { InputType, InputSize } from '../design_system'
import DatametriaIcon from './DatametriaIcon.vue'

interface Props {
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

const props = withDefaults(defineProps<Props>(), {
  type: InputType.TEXT,
  size: InputSize.MD,
  disabled: false,
  readonly: false,
  required: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  blur: [event: FocusEvent]
  focus: [event: FocusEvent]
}>()

const inputRef = ref<HTMLInputElement>()
const inputId = computed(() => `dm-input-${Math.random().toString(36).substr(2, 9)}`)

// Integração com Design System
const inputClasses = computed(() => {
  const dsInput = new DSInput({
    type: props.type,
    size: props.size,
    disabled: props.disabled,
    error: !!props.errorMessage,
    icon_left: props.iconLeft,
    icon_right: props.iconRight
  })
  return dsInput.get_classes()
})

const labelClasses = computed(() => ({
  'dm-form-label--required': props.required
}))

const containerClasses = computed(() => ({
  'dm-input-container--with-icon-left': props.iconLeft,
  'dm-input-container--with-icon-right': props.iconRight
}))

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

// Métodos públicos
defineExpose({
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur(),
  select: () => inputRef.value?.select()
})
</script>
'''
    
    @staticmethod
    def generate_card_component() -> str:
        """Gera componente Vue Card integrado com Design System"""
        return '''
<template>
  <div :class="cardClasses">
    <header v-if="$slots.header || title" class="dm-card-header">
      <slot name="header">
        <h3 v-if="title" class="dm-card-title">{{ title }}</h3>
        <p v-if="description" class="dm-card-description">{{ description }}</p>
      </slot>
    </header>
    
    <div v-if="$slots.default" class="dm-card-content">
      <slot />
    </div>
    
    <footer v-if="$slots.footer" class="dm-card-footer">
      <slot name="footer" />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps } from 'vue'
import { CardVariant } from '../design_system'

interface Props {
  variant?: CardVariant
  padding?: boolean
  title?: string
  description?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: CardVariant.DEFAULT,
  padding: true
})

// Integração com Design System
const cardClasses = computed(() => {
  const dsCard = new DSCard({
    variant: props.variant,
    padding: props.padding
  })
  return dsCard.get_classes()
})
</script>
'''


class DatametriaButton:
    """Wrapper Python para componente Vue Button"""
    
    def __init__(self):
        self.component_code = VueComponentGenerator.generate_button_component()
    
    def get_vue_component(self) -> str:
        return self.component_code
    
    def get_typescript_types(self) -> str:
        return '''
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

export interface ButtonEmits {
  click: [event: MouseEvent]
}
'''


class DatametriaInput:
    """Wrapper Python para componente Vue Input"""
    
    def __init__(self):
        self.component_code = VueComponentGenerator.generate_input_component()
    
    def get_vue_component(self) -> str:
        return self.component_code
    
    def get_typescript_types(self) -> str:
        return '''
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

export interface InputEmits {
  'update:modelValue': [value: string | number]
  blur: [event: FocusEvent]
  focus: [event: FocusEvent]
}
'''


class DatametriaCard:
    """Wrapper Python para componente Vue Card"""
    
    def __init__(self):
        self.component_code = VueComponentGenerator.generate_card_component()
    
    def get_vue_component(self) -> str:
        return self.component_code


# Export
__all__ = [
    "VueComponentGenerator",
    "DatametriaButton",
    "DatametriaInput", 
    "DatametriaCard",
]
