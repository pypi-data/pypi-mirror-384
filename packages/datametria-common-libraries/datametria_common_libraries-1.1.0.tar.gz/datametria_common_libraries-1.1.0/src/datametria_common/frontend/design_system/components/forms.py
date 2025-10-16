"""
Componentes de Formulário do Design System DATAMETRIA

Input, Textarea, Select, Checkbox, Radio, Switch, Form
"""

from typing import Optional, Union, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class InputSize(Enum):
    """Tamanhos do input"""
    SM = "sm"
    MD = "md"
    LG = "lg"


class InputType(Enum):
    """Tipos de input"""
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    TEL = "tel"
    URL = "url"
    SEARCH = "search"


@dataclass
class DatametriaInput:
    """Componente Input DATAMETRIA"""
    
    type: InputType = InputType.TEXT
    size: InputSize = InputSize.MD
    placeholder: str = ""
    disabled: bool = False
    required: bool = False
    error: bool = False
    success: bool = False
    icon_left: Optional[str] = None
    icon_right: Optional[str] = None
    
    def get_classes(self) -> str:
        """Gera classes CSS do input"""
        classes = ["dm-input"]
        
        size_classes = {
            InputSize.SM: "dm-input--sm",
            InputSize.MD: "dm-input--md",
            InputSize.LG: "dm-input--lg",
        }
        classes.append(size_classes[self.size])
        
        if self.disabled:
            classes.append("dm-input--disabled")
        if self.error:
            classes.append("dm-input--error")
        if self.success:
            classes.append("dm-input--success")
        if self.icon_left:
            classes.append("dm-input--with-icon-left")
        if self.icon_right:
            classes.append("dm-input--with-icon-right")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-input {
            display: flex;
            width: 100%;
            border-radius: var(--dm-border-radius-md);
            border: 1px solid var(--dm-border);
            background-color: var(--dm-background);
            color: var(--dm-foreground);
            transition: var(--dm-transition-colors);
            outline: none;
        }
        
        .dm-input:focus {
            border-color: var(--dm-ring);
            box-shadow: 0 0 0 2px var(--dm-ring);
        }
        
        .dm-input::placeholder {
            color: var(--dm-muted-foreground);
        }
        
        /* Sizes */
        .dm-input--sm {
            height: 2rem;
            padding: 0 var(--dm-spacing-lg);
            font-size: var(--dm-font-size-sm);
        }
        
        .dm-input--md {
            height: 2.5rem;
            padding: 0 var(--dm-spacing-xl);
            font-size: var(--dm-font-size-base);
        }
        
        .dm-input--lg {
            height: 3rem;
            padding: 0 var(--dm-spacing-2xl);
            font-size: var(--dm-font-size-lg);
        }
        
        /* States */
        .dm-input--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .dm-input--error {
            border-color: var(--dm-error);
        }
        
        .dm-input--error:focus {
            border-color: var(--dm-error);
            box-shadow: 0 0 0 2px var(--dm-error);
        }
        
        .dm-input--success {
            border-color: var(--dm-success);
        }
        
        .dm-input--success:focus {
            border-color: var(--dm-success);
            box-shadow: 0 0 0 2px var(--dm-success);
        }
        """


@dataclass
class DatametriaTextarea:
    """Componente Textarea DATAMETRIA"""
    
    placeholder: str = ""
    disabled: bool = False
    required: bool = False
    error: bool = False
    success: bool = False
    rows: int = 3
    resize: bool = True
    
    def get_classes(self) -> str:
        """Gera classes CSS do textarea"""
        classes = ["dm-textarea"]
        
        if self.disabled:
            classes.append("dm-textarea--disabled")
        if self.error:
            classes.append("dm-textarea--error")
        if self.success:
            classes.append("dm-textarea--success")
        if not self.resize:
            classes.append("dm-textarea--no-resize")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-textarea {
            display: flex;
            width: 100%;
            min-height: 4rem;
            padding: var(--dm-spacing-lg);
            border-radius: var(--dm-border-radius-md);
            border: 1px solid var(--dm-border);
            background-color: var(--dm-background);
            color: var(--dm-foreground);
            font-size: var(--dm-font-size-base);
            transition: var(--dm-transition-colors);
            outline: none;
            resize: vertical;
        }
        
        .dm-textarea:focus {
            border-color: var(--dm-ring);
            box-shadow: 0 0 0 2px var(--dm-ring);
        }
        
        .dm-textarea::placeholder {
            color: var(--dm-muted-foreground);
        }
        
        .dm-textarea--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .dm-textarea--error {
            border-color: var(--dm-error);
        }
        
        .dm-textarea--success {
            border-color: var(--dm-success);
        }
        
        .dm-textarea--no-resize {
            resize: none;
        }
        """


@dataclass
class SelectOption:
    """Opção do select"""
    value: str
    label: str
    disabled: bool = False


@dataclass
class DatametriaSelect:
    """Componente Select DATAMETRIA"""
    
    options: List[SelectOption]
    placeholder: str = "Selecione uma opção"
    disabled: bool = False
    required: bool = False
    error: bool = False
    success: bool = False
    size: InputSize = InputSize.MD
    
    def get_classes(self) -> str:
        """Gera classes CSS do select"""
        classes = ["dm-select"]
        
        size_classes = {
            InputSize.SM: "dm-select--sm",
            InputSize.MD: "dm-select--md", 
            InputSize.LG: "dm-select--lg",
        }
        classes.append(size_classes[self.size])
        
        if self.disabled:
            classes.append("dm-select--disabled")
        if self.error:
            classes.append("dm-select--error")
        if self.success:
            classes.append("dm-select--success")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-select {
            position: relative;
            display: flex;
            width: 100%;
        }
        
        .dm-select select {
            width: 100%;
            border-radius: var(--dm-border-radius-md);
            border: 1px solid var(--dm-border);
            background-color: var(--dm-background);
            color: var(--dm-foreground);
            transition: var(--dm-transition-colors);
            outline: none;
            appearance: none;
            cursor: pointer;
        }
        
        .dm-select select:focus {
            border-color: var(--dm-ring);
            box-shadow: 0 0 0 2px var(--dm-ring);
        }
        
        /* Sizes */
        .dm-select--sm select {
            height: 2rem;
            padding: 0 2rem 0 var(--dm-spacing-lg);
            font-size: var(--dm-font-size-sm);
        }
        
        .dm-select--md select {
            height: 2.5rem;
            padding: 0 2rem 0 var(--dm-spacing-xl);
            font-size: var(--dm-font-size-base);
        }
        
        .dm-select--lg select {
            height: 3rem;
            padding: 0 2rem 0 var(--dm-spacing-2xl);
            font-size: var(--dm-font-size-lg);
        }
        
        /* Arrow icon */
        .dm-select::after {
            content: '';
            position: absolute;
            right: var(--dm-spacing-lg);
            top: 50%;
            transform: translateY(-50%);
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid var(--dm-muted-foreground);
            pointer-events: none;
        }
        
        /* States */
        .dm-select--disabled select {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .dm-select--error select {
            border-color: var(--dm-error);
        }
        
        .dm-select--success select {
            border-color: var(--dm-success);
        }
        """


@dataclass
class DatametriaCheckbox:
    """Componente Checkbox DATAMETRIA"""
    
    checked: bool = False
    disabled: bool = False
    required: bool = False
    
    def get_classes(self) -> str:
        """Gera classes CSS do checkbox"""
        classes = ["dm-checkbox"]
        
        if self.checked:
            classes.append("dm-checkbox--checked")
        if self.disabled:
            classes.append("dm-checkbox--disabled")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-checkbox {
            display: inline-flex;
            align-items: center;
            gap: var(--dm-spacing-md);
            cursor: pointer;
        }
        
        .dm-checkbox input {
            width: 1rem;
            height: 1rem;
            border-radius: var(--dm-border-radius-sm);
            border: 1px solid var(--dm-border);
            background-color: var(--dm-background);
            cursor: pointer;
            outline: none;
            appearance: none;
            position: relative;
        }
        
        .dm-checkbox input:focus {
            box-shadow: 0 0 0 2px var(--dm-ring);
        }
        
        .dm-checkbox input:checked {
            background-color: var(--dm-primary);
            border-color: var(--dm-primary);
        }
        
        .dm-checkbox input:checked::after {
            content: '✓';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: var(--dm-primary-foreground);
            font-size: 0.75rem;
            font-weight: bold;
        }
        
        .dm-checkbox--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .dm-checkbox--disabled input {
            cursor: not-allowed;
        }
        """


@dataclass
class DatametriaRadio:
    """Componente Radio DATAMETRIA"""
    
    name: str
    value: str
    checked: bool = False
    disabled: bool = False
    required: bool = False
    
    def get_classes(self) -> str:
        """Gera classes CSS do radio"""
        classes = ["dm-radio"]
        
        if self.checked:
            classes.append("dm-radio--checked")
        if self.disabled:
            classes.append("dm-radio--disabled")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-radio {
            display: inline-flex;
            align-items: center;
            gap: var(--dm-spacing-md);
            cursor: pointer;
        }
        
        .dm-radio input {
            width: 1rem;
            height: 1rem;
            border-radius: 50%;
            border: 1px solid var(--dm-border);
            background-color: var(--dm-background);
            cursor: pointer;
            outline: none;
            appearance: none;
            position: relative;
        }
        
        .dm-radio input:focus {
            box-shadow: 0 0 0 2px var(--dm-ring);
        }
        
        .dm-radio input:checked {
            border-color: var(--dm-primary);
        }
        
        .dm-radio input:checked::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            background-color: var(--dm-primary);
        }
        
        .dm-radio--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        """


@dataclass
class DatametriaSwitch:
    """Componente Switch DATAMETRIA"""
    
    checked: bool = False
    disabled: bool = False
    
    def get_classes(self) -> str:
        """Gera classes CSS do switch"""
        classes = ["dm-switch"]
        
        if self.checked:
            classes.append("dm-switch--checked")
        if self.disabled:
            classes.append("dm-switch--disabled")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-switch {
            display: inline-flex;
            align-items: center;
            cursor: pointer;
        }
        
        .dm-switch input {
            width: 2.5rem;
            height: 1.25rem;
            border-radius: var(--dm-border-radius-full);
            border: 1px solid var(--dm-border);
            background-color: var(--dm-muted);
            cursor: pointer;
            outline: none;
            appearance: none;
            position: relative;
            transition: var(--dm-transition-colors);
        }
        
        .dm-switch input::after {
            content: '';
            position: absolute;
            top: 1px;
            left: 1px;
            width: 1rem;
            height: 1rem;
            border-radius: 50%;
            background-color: var(--dm-background);
            transition: var(--dm-transition-transform);
        }
        
        .dm-switch input:focus {
            box-shadow: 0 0 0 2px var(--dm-ring);
        }
        
        .dm-switch input:checked {
            background-color: var(--dm-primary);
        }
        
        .dm-switch input:checked::after {
            transform: translateX(1.25rem);
        }
        
        .dm-switch--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        """


@dataclass
class DatametriaForm:
    """Componente Form DATAMETRIA"""
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-form {
            display: flex;
            flex-direction: column;
            gap: var(--dm-spacing-xl);
        }
        
        .dm-form-group {
            display: flex;
            flex-direction: column;
            gap: var(--dm-spacing-sm);
        }
        
        .dm-form-label {
            font-size: var(--dm-font-size-sm);
            font-weight: 500;
            color: var(--dm-foreground);
        }
        
        .dm-form-label--required::after {
            content: ' *';
            color: var(--dm-error);
        }
        
        .dm-form-help {
            font-size: var(--dm-font-size-xs);
            color: var(--dm-muted-foreground);
        }
        
        .dm-form-error {
            font-size: var(--dm-font-size-xs);
            color: var(--dm-error);
        }
        
        .dm-form-actions {
            display: flex;
            gap: var(--dm-spacing-md);
            justify-content: flex-end;
        }
        """


# Export
__all__ = [
    "InputSize",
    "InputType",
    "DatametriaInput",
    "DatametriaTextarea", 
    "SelectOption",
    "DatametriaSelect",
    "DatametriaCheckbox",
    "DatametriaRadio",
    "DatametriaSwitch",
    "DatametriaForm",
]
