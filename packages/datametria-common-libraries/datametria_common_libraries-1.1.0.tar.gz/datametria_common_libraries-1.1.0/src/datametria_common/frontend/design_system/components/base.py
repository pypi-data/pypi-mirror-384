"""
Componentes Base do Design System DATAMETRIA

Componentes fundamentais: Button, Icon, Avatar, Badge
"""

from typing import Optional, Union, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum


class ButtonVariant(Enum):
    """Variantes do botão"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    OUTLINE = "outline"
    GHOST = "ghost"
    LINK = "link"
    DESTRUCTIVE = "destructive"


class ButtonSize(Enum):
    """Tamanhos do botão"""
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"


@dataclass
class DatametriaButton:
    """Componente Button DATAMETRIA"""
    
    # Props
    variant: ButtonVariant = ButtonVariant.PRIMARY
    size: ButtonSize = ButtonSize.MD
    disabled: bool = False
    loading: bool = False
    full_width: bool = False
    icon_left: Optional[str] = None
    icon_right: Optional[str] = None
    
    def get_classes(self) -> str:
        """Gera classes CSS do botão"""
        classes = ["dm-button"]
        
        # Variant classes
        variant_classes = {
            ButtonVariant.PRIMARY: "dm-button--primary",
            ButtonVariant.SECONDARY: "dm-button--secondary", 
            ButtonVariant.OUTLINE: "dm-button--outline",
            ButtonVariant.GHOST: "dm-button--ghost",
            ButtonVariant.LINK: "dm-button--link",
            ButtonVariant.DESTRUCTIVE: "dm-button--destructive",
        }
        classes.append(variant_classes[self.variant])
        
        # Size classes
        size_classes = {
            ButtonSize.SM: "dm-button--sm",
            ButtonSize.MD: "dm-button--md",
            ButtonSize.LG: "dm-button--lg", 
            ButtonSize.XL: "dm-button--xl",
        }
        classes.append(size_classes[self.size])
        
        # State classes
        if self.disabled:
            classes.append("dm-button--disabled")
        if self.loading:
            classes.append("dm-button--loading")
        if self.full_width:
            classes.append("dm-button--full-width")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: var(--dm-spacing-sm);
            border-radius: var(--dm-border-radius-md);
            font-weight: 500;
            transition: var(--dm-transition-colors);
            cursor: pointer;
            border: 1px solid transparent;
            text-decoration: none;
            outline: none;
            position: relative;
        }
        
        .dm-button:focus-visible {
            outline: 2px solid var(--dm-ring);
            outline-offset: 2px;
        }
        
        /* Variants */
        .dm-button--primary {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
            border-color: var(--dm-primary);
        }
        
        .dm-button--primary:hover:not(.dm-button--disabled) {
            opacity: 0.9;
        }
        
        .dm-button--secondary {
            background-color: var(--dm-secondary);
            color: var(--dm-secondary-foreground);
            border-color: var(--dm-secondary);
        }
        
        .dm-button--outline {
            background-color: transparent;
            color: var(--dm-foreground);
            border-color: var(--dm-border);
        }
        
        .dm-button--outline:hover:not(.dm-button--disabled) {
            background-color: var(--dm-accent);
        }
        
        .dm-button--ghost {
            background-color: transparent;
            color: var(--dm-foreground);
            border-color: transparent;
        }
        
        .dm-button--ghost:hover:not(.dm-button--disabled) {
            background-color: var(--dm-accent);
        }
        
        .dm-button--link {
            background-color: transparent;
            color: var(--dm-primary);
            border-color: transparent;
            text-decoration: underline;
        }
        
        .dm-button--destructive {
            background-color: var(--dm-error);
            color: var(--dm-error-foreground);
            border-color: var(--dm-error);
        }
        
        /* Sizes */
        .dm-button--sm {
            height: 2rem;
            padding: 0 var(--dm-spacing-lg);
            font-size: var(--dm-font-size-sm);
        }
        
        .dm-button--md {
            height: 2.5rem;
            padding: 0 var(--dm-spacing-xl);
            font-size: var(--dm-font-size-base);
        }
        
        .dm-button--lg {
            height: 3rem;
            padding: 0 var(--dm-spacing-2xl);
            font-size: var(--dm-font-size-lg);
        }
        
        .dm-button--xl {
            height: 3.5rem;
            padding: 0 var(--dm-spacing-3xl);
            font-size: var(--dm-font-size-xl);
        }
        
        /* States */
        .dm-button--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .dm-button--loading {
            cursor: wait;
        }
        
        .dm-button--full-width {
            width: 100%;
        }
        """


class IconSize(Enum):
    """Tamanhos do ícone"""
    XS = "xs"
    SM = "sm" 
    MD = "md"
    LG = "lg"
    XL = "xl"


@dataclass
class DatametriaIcon:
    """Componente Icon DATAMETRIA"""
    
    name: str
    size: IconSize = IconSize.MD
    color: Optional[str] = None
    
    def get_classes(self) -> str:
        """Gera classes CSS do ícone"""
        classes = ["dm-icon"]
        
        size_classes = {
            IconSize.XS: "dm-icon--xs",
            IconSize.SM: "dm-icon--sm",
            IconSize.MD: "dm-icon--md", 
            IconSize.LG: "dm-icon--lg",
            IconSize.XL: "dm-icon--xl",
        }
        classes.append(size_classes[self.size])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-icon {
            display: inline-block;
            vertical-align: middle;
            flex-shrink: 0;
        }
        
        .dm-icon--xs { width: 0.75rem; height: 0.75rem; }
        .dm-icon--sm { width: 1rem; height: 1rem; }
        .dm-icon--md { width: 1.25rem; height: 1.25rem; }
        .dm-icon--lg { width: 1.5rem; height: 1.5rem; }
        .dm-icon--xl { width: 2rem; height: 2rem; }
        """


class AvatarSize(Enum):
    """Tamanhos do avatar"""
    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"


@dataclass
class DatametriaAvatar:
    """Componente Avatar DATAMETRIA"""
    
    src: Optional[str] = None
    alt: str = ""
    fallback: str = ""
    size: AvatarSize = AvatarSize.MD
    
    def get_classes(self) -> str:
        """Gera classes CSS do avatar"""
        classes = ["dm-avatar"]
        
        size_classes = {
            AvatarSize.XS: "dm-avatar--xs",
            AvatarSize.SM: "dm-avatar--sm",
            AvatarSize.MD: "dm-avatar--md",
            AvatarSize.LG: "dm-avatar--lg", 
            AvatarSize.XL: "dm-avatar--xl",
        }
        classes.append(size_classes[self.size])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-avatar {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background-color: var(--dm-muted);
            color: var(--dm-muted-foreground);
            font-weight: 500;
            overflow: hidden;
        }
        
        .dm-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .dm-avatar--xs { width: 1.5rem; height: 1.5rem; font-size: 0.625rem; }
        .dm-avatar--sm { width: 2rem; height: 2rem; font-size: 0.75rem; }
        .dm-avatar--md { width: 2.5rem; height: 2.5rem; font-size: 0.875rem; }
        .dm-avatar--lg { width: 3rem; height: 3rem; font-size: 1rem; }
        .dm-avatar--xl { width: 4rem; height: 4rem; font-size: 1.25rem; }
        """


class BadgeVariant(Enum):
    """Variantes do badge"""
    DEFAULT = "default"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    OUTLINE = "outline"


@dataclass
class DatametriaBadge:
    """Componente Badge DATAMETRIA"""
    
    variant: BadgeVariant = BadgeVariant.DEFAULT
    
    def get_classes(self) -> str:
        """Gera classes CSS do badge"""
        classes = ["dm-badge"]
        
        variant_classes = {
            BadgeVariant.DEFAULT: "dm-badge--default",
            BadgeVariant.SUCCESS: "dm-badge--success",
            BadgeVariant.WARNING: "dm-badge--warning",
            BadgeVariant.ERROR: "dm-badge--error",
            BadgeVariant.INFO: "dm-badge--info",
            BadgeVariant.OUTLINE: "dm-badge--outline",
        }
        classes.append(variant_classes[self.variant])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.125rem 0.5rem;
            border-radius: var(--dm-border-radius-full);
            font-size: 0.75rem;
            font-weight: 500;
            line-height: 1;
            border: 1px solid transparent;
        }
        
        .dm-badge--default {
            background-color: var(--dm-muted);
            color: var(--dm-muted-foreground);
        }
        
        .dm-badge--success {
            background-color: var(--dm-success);
            color: var(--dm-success-foreground);
        }
        
        .dm-badge--warning {
            background-color: var(--dm-warning);
            color: var(--dm-warning-foreground);
        }
        
        .dm-badge--error {
            background-color: var(--dm-error);
            color: var(--dm-error-foreground);
        }
        
        .dm-badge--info {
            background-color: var(--dm-info);
            color: var(--dm-info-foreground);
        }
        
        .dm-badge--outline {
            background-color: transparent;
            color: var(--dm-foreground);
            border-color: var(--dm-border);
        }
        """


# Export
__all__ = [
    "ButtonVariant",
    "ButtonSize", 
    "DatametriaButton",
    "IconSize",
    "DatametriaIcon",
    "AvatarSize",
    "DatametriaAvatar",
    "BadgeVariant",
    "DatametriaBadge",
]
