"""
Componentes de Feedback do Design System DATAMETRIA

Modal, Toast, Alert, Progress, Spinner, Tooltip
"""

from typing import Optional, Union, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum


class ModalSize(Enum):
    """Tamanhos do modal"""
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"
    FULL = "full"


@dataclass
class DatametriaModal:
    """Componente Modal DATAMETRIA"""
    
    size: ModalSize = ModalSize.MD
    closable: bool = True
    backdrop_close: bool = True
    
    def get_classes(self) -> str:
        """Gera classes CSS do modal"""
        classes = ["dm-modal"]
        
        size_classes = {
            ModalSize.SM: "dm-modal--sm",
            ModalSize.MD: "dm-modal--md",
            ModalSize.LG: "dm-modal--lg",
            ModalSize.XL: "dm-modal--xl",
            ModalSize.FULL: "dm-modal--full",
        }
        classes.append(size_classes[self.size])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 50;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: var(--dm-spacing-xl);
        }
        
        .dm-modal-backdrop {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
        }
        
        .dm-modal-content {
            position: relative;
            background-color: var(--dm-card);
            border-radius: var(--dm-border-radius-lg);
            box-shadow: var(--dm-shadow-xl);
            max-height: calc(100vh - 2 * var(--dm-spacing-xl));
            overflow-y: auto;
        }
        
        .dm-modal--sm .dm-modal-content { width: 100%; max-width: 24rem; }
        .dm-modal--md .dm-modal-content { width: 100%; max-width: 32rem; }
        .dm-modal--lg .dm-modal-content { width: 100%; max-width: 48rem; }
        .dm-modal--xl .dm-modal-content { width: 100%; max-width: 64rem; }
        .dm-modal--full .dm-modal-content { width: 100%; height: 100%; max-width: none; max-height: none; }
        
        .dm-modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--dm-spacing-6xl);
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-modal-title {
            font-size: var(--dm-font-size-lg);
            font-weight: 600;
        }
        
        .dm-modal-close {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border: none;
            background: transparent;
            border-radius: var(--dm-border-radius-md);
            cursor: pointer;
            color: var(--dm-muted-foreground);
            transition: var(--dm-transition-colors);
        }
        
        .dm-modal-close:hover {
            color: var(--dm-foreground);
            background-color: var(--dm-accent);
        }
        
        .dm-modal-body {
            padding: var(--dm-spacing-6xl);
        }
        
        .dm-modal-footer {
            display: flex;
            gap: var(--dm-spacing-md);
            justify-content: flex-end;
            padding: var(--dm-spacing-6xl);
            border-top: 1px solid var(--dm-border);
        }
        """


class ToastVariant(Enum):
    """Variantes do toast"""
    DEFAULT = "default"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class ToastPosition(Enum):
    """Posições do toast"""
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"
    BOTTOM_RIGHT = "bottom-right"


@dataclass
class DatametriaToast:
    """Componente Toast DATAMETRIA"""
    
    variant: ToastVariant = ToastVariant.DEFAULT
    position: ToastPosition = ToastPosition.TOP_RIGHT
    duration: int = 5000
    closable: bool = True
    
    def get_classes(self) -> str:
        """Gera classes CSS do toast"""
        classes = ["dm-toast"]
        
        variant_classes = {
            ToastVariant.DEFAULT: "dm-toast--default",
            ToastVariant.SUCCESS: "dm-toast--success",
            ToastVariant.WARNING: "dm-toast--warning",
            ToastVariant.ERROR: "dm-toast--error",
            ToastVariant.INFO: "dm-toast--info",
        }
        classes.append(variant_classes[self.variant])
        
        position_classes = {
            ToastPosition.TOP_LEFT: "dm-toast--top-left",
            ToastPosition.TOP_CENTER: "dm-toast--top-center",
            ToastPosition.TOP_RIGHT: "dm-toast--top-right",
            ToastPosition.BOTTOM_LEFT: "dm-toast--bottom-left",
            ToastPosition.BOTTOM_CENTER: "dm-toast--bottom-center",
            ToastPosition.BOTTOM_RIGHT: "dm-toast--bottom-right",
        }
        classes.append(position_classes[self.position])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-toast {
            position: fixed;
            z-index: 100;
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-md);
            min-width: 20rem;
            max-width: 24rem;
            padding: var(--dm-spacing-xl);
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-lg);
            box-shadow: var(--dm-shadow-lg);
            animation: dm-toast-slide-in 0.3s ease-out;
        }
        
        .dm-toast--top-left { top: var(--dm-spacing-xl); left: var(--dm-spacing-xl); }
        .dm-toast--top-center { top: var(--dm-spacing-xl); left: 50%; transform: translateX(-50%); }
        .dm-toast--top-right { top: var(--dm-spacing-xl); right: var(--dm-spacing-xl); }
        .dm-toast--bottom-left { bottom: var(--dm-spacing-xl); left: var(--dm-spacing-xl); }
        .dm-toast--bottom-center { bottom: var(--dm-spacing-xl); left: 50%; transform: translateX(-50%); }
        .dm-toast--bottom-right { bottom: var(--dm-spacing-xl); right: var(--dm-spacing-xl); }
        
        .dm-toast--success { border-left: 4px solid var(--dm-success); }
        .dm-toast--warning { border-left: 4px solid var(--dm-warning); }
        .dm-toast--error { border-left: 4px solid var(--dm-error); }
        .dm-toast--info { border-left: 4px solid var(--dm-info); }
        
        .dm-toast-content {
            flex: 1;
        }
        
        .dm-toast-title {
            font-weight: 600;
            margin-bottom: var(--dm-spacing-xs);
        }
        
        .dm-toast-description {
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
        }
        
        .dm-toast-close {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 1.5rem;
            height: 1.5rem;
            border: none;
            background: transparent;
            border-radius: var(--dm-border-radius-sm);
            cursor: pointer;
            color: var(--dm-muted-foreground);
            transition: var(--dm-transition-colors);
        }
        
        .dm-toast-close:hover {
            color: var(--dm-foreground);
            background-color: var(--dm-accent);
        }
        
        @keyframes dm-toast-slide-in {
            from {
                opacity: 0;
                transform: translateY(-1rem);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        """


class AlertVariant(Enum):
    """Variantes do alert"""
    DEFAULT = "default"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


@dataclass
class DatametriaAlert:
    """Componente Alert DATAMETRIA"""
    
    variant: AlertVariant = AlertVariant.DEFAULT
    closable: bool = False
    
    def get_classes(self) -> str:
        """Gera classes CSS do alert"""
        classes = ["dm-alert"]
        
        variant_classes = {
            AlertVariant.DEFAULT: "dm-alert--default",
            AlertVariant.SUCCESS: "dm-alert--success",
            AlertVariant.WARNING: "dm-alert--warning",
            AlertVariant.ERROR: "dm-alert--error",
            AlertVariant.INFO: "dm-alert--info",
        }
        classes.append(variant_classes[self.variant])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-alert {
            display: flex;
            align-items: flex-start;
            gap: var(--dm-spacing-md);
            padding: var(--dm-spacing-xl);
            border-radius: var(--dm-border-radius-lg);
            border: 1px solid var(--dm-border);
        }
        
        .dm-alert--default {
            background-color: var(--dm-muted);
            color: var(--dm-foreground);
        }
        
        .dm-alert--success {
            background-color: var(--dm-success);
            color: var(--dm-success-foreground);
            border-color: var(--dm-success);
        }
        
        .dm-alert--warning {
            background-color: var(--dm-warning);
            color: var(--dm-warning-foreground);
            border-color: var(--dm-warning);
        }
        
        .dm-alert--error {
            background-color: var(--dm-error);
            color: var(--dm-error-foreground);
            border-color: var(--dm-error);
        }
        
        .dm-alert--info {
            background-color: var(--dm-info);
            color: var(--dm-info-foreground);
            border-color: var(--dm-info);
        }
        
        .dm-alert-content {
            flex: 1;
        }
        
        .dm-alert-title {
            font-weight: 600;
            margin-bottom: var(--dm-spacing-xs);
        }
        
        .dm-alert-description {
            font-size: var(--dm-font-size-sm);
            opacity: 0.9;
        }
        """


@dataclass
class DatametriaProgress:
    """Componente Progress DATAMETRIA"""
    
    value: float = 0
    max_value: float = 100
    show_label: bool = False
    
    def get_percentage(self) -> float:
        """Calcula porcentagem"""
        return min(100, max(0, (self.value / self.max_value) * 100))
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-progress {
            width: 100%;
        }
        
        .dm-progress-track {
            width: 100%;
            height: 0.5rem;
            background-color: var(--dm-muted);
            border-radius: var(--dm-border-radius-full);
            overflow: hidden;
        }
        
        .dm-progress-fill {
            height: 100%;
            background-color: var(--dm-primary);
            border-radius: var(--dm-border-radius-full);
            transition: width 0.3s ease;
        }
        
        .dm-progress-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: var(--dm-spacing-sm);
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
        }
        """


class SpinnerSize(Enum):
    """Tamanhos do spinner"""
    SM = "sm"
    MD = "md"
    LG = "lg"


@dataclass
class DatametriaSpinner:
    """Componente Spinner DATAMETRIA"""
    
    size: SpinnerSize = SpinnerSize.MD
    
    def get_classes(self) -> str:
        """Gera classes CSS do spinner"""
        classes = ["dm-spinner"]
        
        size_classes = {
            SpinnerSize.SM: "dm-spinner--sm",
            SpinnerSize.MD: "dm-spinner--md",
            SpinnerSize.LG: "dm-spinner--lg",
        }
        classes.append(size_classes[self.size])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-spinner {
            display: inline-block;
            border-radius: 50%;
            border: 2px solid var(--dm-muted);
            border-top-color: var(--dm-primary);
            animation: dm-spinner-spin 1s linear infinite;
        }
        
        .dm-spinner--sm { width: 1rem; height: 1rem; }
        .dm-spinner--md { width: 1.5rem; height: 1.5rem; }
        .dm-spinner--lg { width: 2rem; height: 2rem; }
        
        @keyframes dm-spinner-spin {
            to {
                transform: rotate(360deg);
            }
        }
        """


class TooltipPosition(Enum):
    """Posições do tooltip"""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class DatametriaTooltip:
    """Componente Tooltip DATAMETRIA"""
    
    position: TooltipPosition = TooltipPosition.TOP
    
    def get_classes(self) -> str:
        """Gera classes CSS do tooltip"""
        classes = ["dm-tooltip"]
        
        position_classes = {
            TooltipPosition.TOP: "dm-tooltip--top",
            TooltipPosition.BOTTOM: "dm-tooltip--bottom",
            TooltipPosition.LEFT: "dm-tooltip--left",
            TooltipPosition.RIGHT: "dm-tooltip--right",
        }
        classes.append(position_classes[self.position])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-tooltip {
            position: relative;
            display: inline-block;
        }
        
        .dm-tooltip-content {
            position: absolute;
            z-index: 50;
            padding: var(--dm-spacing-sm) var(--dm-spacing-md);
            background-color: var(--dm-popover);
            color: var(--dm-popover-foreground);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            box-shadow: var(--dm-shadow-md);
            font-size: var(--dm-font-size-sm);
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.2s, visibility 0.2s;
        }
        
        .dm-tooltip:hover .dm-tooltip-content {
            opacity: 1;
            visibility: visible;
        }
        
        .dm-tooltip--top .dm-tooltip-content {
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            margin-bottom: var(--dm-spacing-sm);
        }
        
        .dm-tooltip--bottom .dm-tooltip-content {
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            margin-top: var(--dm-spacing-sm);
        }
        
        .dm-tooltip--left .dm-tooltip-content {
            right: 100%;
            top: 50%;
            transform: translateY(-50%);
            margin-right: var(--dm-spacing-sm);
        }
        
        .dm-tooltip--right .dm-tooltip-content {
            left: 100%;
            top: 50%;
            transform: translateY(-50%);
            margin-left: var(--dm-spacing-sm);
        }
        """


# Export
__all__ = [
    "ModalSize",
    "DatametriaModal",
    "ToastVariant",
    "ToastPosition",
    "DatametriaToast",
    "AlertVariant",
    "DatametriaAlert",
    "DatametriaProgress",
    "SpinnerSize",
    "DatametriaSpinner",
    "TooltipPosition",
    "DatametriaTooltip",
]
