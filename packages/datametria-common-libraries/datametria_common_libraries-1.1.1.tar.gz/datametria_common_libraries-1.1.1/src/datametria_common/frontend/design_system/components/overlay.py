"""
Componentes de Overlay do Design System DATAMETRIA

Componentes de sobreposição: Dropdown, Menu, Drawer, Popover, etc.
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum


class DropdownAlign(Enum):
    """Alinhamento do dropdown"""
    START = "start"
    CENTER = "center"
    END = "end"


@dataclass
class DatametriaDropdown:
    """Componente Dropdown/Menu DATAMETRIA"""
    
    align: DropdownAlign = DropdownAlign.START
    offset: int = 4
    
    def get_classes(self) -> str:
        return f"dm-dropdown dm-dropdown--{self.align.value}"
    
    def get_css(self) -> str:
        return """
        .dm-dropdown {
            position: relative;
        }
        
        .dm-dropdown-trigger {
            cursor: pointer;
        }
        
        .dm-dropdown-content {
            position: absolute;
            top: 100%;
            margin-top: var(--dm-spacing-sm);
            min-width: 12rem;
            padding: var(--dm-spacing-sm);
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            box-shadow: var(--dm-shadow-lg);
            z-index: 50;
        }
        
        .dm-dropdown--start .dm-dropdown-content {
            left: 0;
        }
        
        .dm-dropdown--center .dm-dropdown-content {
            left: 50%;
            transform: translateX(-50%);
        }
        
        .dm-dropdown--end .dm-dropdown-content {
            right: 0;
        }
        
        .dm-dropdown-item {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-md);
            padding: var(--dm-spacing-md) var(--dm-spacing-lg);
            border-radius: var(--dm-border-radius-sm);
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .dm-dropdown-item:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-dropdown-item--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .dm-dropdown-separator {
            height: 1px;
            margin: var(--dm-spacing-sm) 0;
            background-color: var(--dm-border);
        }
        """


class DrawerSide(Enum):
    """Lado do drawer"""
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class DatametriaDrawer:
    """Componente Drawer/Sheet DATAMETRIA"""
    
    side: DrawerSide = DrawerSide.RIGHT
    overlay: bool = True
    
    def get_classes(self) -> str:
        classes = ["dm-drawer", f"dm-drawer--{self.side.value}"]
        if self.overlay:
            classes.append("dm-drawer--overlay")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-drawer-overlay {
            position: fixed;
            inset: 0;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 50;
            animation: dm-fade-in 0.2s ease;
        }
        
        @keyframes dm-fade-in {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .dm-drawer {
            position: fixed;
            background-color: var(--dm-background);
            box-shadow: var(--dm-shadow-xl);
            z-index: 51;
            animation: dm-slide-in 0.3s ease;
        }
        
        .dm-drawer--left {
            top: 0;
            bottom: 0;
            left: 0;
            width: 20rem;
        }
        
        .dm-drawer--right {
            top: 0;
            bottom: 0;
            right: 0;
            width: 20rem;
        }
        
        .dm-drawer--top {
            top: 0;
            left: 0;
            right: 0;
            height: 20rem;
        }
        
        .dm-drawer--bottom {
            bottom: 0;
            left: 0;
            right: 0;
            height: 20rem;
        }
        
        @keyframes dm-slide-in {
            from {
                transform: translateX(-100%);
            }
            to {
                transform: translateX(0);
            }
        }
        
        .dm-drawer-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--dm-spacing-xl);
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-drawer-title {
            font-size: var(--dm-font-size-lg);
            font-weight: 600;
        }
        
        .dm-drawer-close {
            padding: var(--dm-spacing-sm);
            border: none;
            background: transparent;
            cursor: pointer;
        }
        
        .dm-drawer-content {
            padding: var(--dm-spacing-xl);
            overflow-y: auto;
        }
        """


class PopoverSide(Enum):
    """Lado do popover"""
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"


@dataclass
class DatametriaPopover:
    """Componente Popover DATAMETRIA"""
    
    side: PopoverSide = PopoverSide.BOTTOM
    align: str = "center"
    
    def get_classes(self) -> str:
        return f"dm-popover dm-popover--{self.side.value} dm-popover--{self.align}"
    
    def get_css(self) -> str:
        return """
        .dm-popover {
            position: relative;
        }
        
        .dm-popover-trigger {
            cursor: pointer;
        }
        
        .dm-popover-content {
            position: absolute;
            padding: var(--dm-spacing-lg);
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            box-shadow: var(--dm-shadow-lg);
            z-index: 50;
            max-width: 20rem;
        }
        
        .dm-popover--top .dm-popover-content {
            bottom: 100%;
            margin-bottom: var(--dm-spacing-sm);
        }
        
        .dm-popover--bottom .dm-popover-content {
            top: 100%;
            margin-top: var(--dm-spacing-sm);
        }
        
        .dm-popover--left .dm-popover-content {
            right: 100%;
            margin-right: var(--dm-spacing-sm);
        }
        
        .dm-popover--right .dm-popover-content {
            left: 100%;
            margin-left: var(--dm-spacing-sm);
        }
        
        .dm-popover-arrow {
            position: absolute;
            width: 0.5rem;
            height: 0.5rem;
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            transform: rotate(45deg);
        }
        """


class StepperOrientation(Enum):
    """Orientação do stepper"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass
class DatametriaStepper:
    """Componente Stepper/Wizard DATAMETRIA"""
    
    orientation: StepperOrientation = StepperOrientation.HORIZONTAL
    current_step: int = 0
    
    def get_classes(self) -> str:
        return f"dm-stepper dm-stepper--{self.orientation.value}"
    
    def get_css(self) -> str:
        return """
        .dm-stepper {
            display: flex;
        }
        
        .dm-stepper--horizontal {
            flex-direction: row;
            align-items: center;
        }
        
        .dm-stepper--vertical {
            flex-direction: column;
        }
        
        .dm-stepper-step {
            display: flex;
            align-items: center;
            flex: 1;
        }
        
        .dm-stepper-step-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            background-color: var(--dm-muted);
            color: var(--dm-muted-foreground);
            font-weight: 600;
            border: 2px solid var(--dm-border);
        }
        
        .dm-stepper-step--active .dm-stepper-step-indicator {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
            border-color: var(--dm-primary);
        }
        
        .dm-stepper-step--completed .dm-stepper-step-indicator {
            background-color: var(--dm-success);
            color: var(--dm-success-foreground);
            border-color: var(--dm-success);
        }
        
        .dm-stepper-step-content {
            margin-left: var(--dm-spacing-md);
        }
        
        .dm-stepper-step-title {
            font-weight: 600;
        }
        
        .dm-stepper-step-description {
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
        }
        
        .dm-stepper-connector {
            flex: 1;
            height: 2px;
            background-color: var(--dm-border);
            margin: 0 var(--dm-spacing-md);
        }
        
        .dm-stepper-step--completed + .dm-stepper-step .dm-stepper-connector {
            background-color: var(--dm-success);
        }
        """


@dataclass
class DatametriaCommandPalette:
    """Componente Command Palette DATAMETRIA"""
    
    placeholder: str = "Type a command..."
    
    def get_classes(self) -> str:
        return "dm-command-palette"
    
    def get_css(self) -> str:
        return """
        .dm-command-palette-overlay {
            position: fixed;
            inset: 0;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 100;
        }
        
        .dm-command-palette {
            position: fixed;
            top: 20%;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 40rem;
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-lg);
            box-shadow: var(--dm-shadow-2xl);
            z-index: 101;
        }
        
        .dm-command-palette-input {
            width: 100%;
            padding: var(--dm-spacing-xl);
            border: none;
            border-bottom: 1px solid var(--dm-border);
            background: transparent;
            font-size: var(--dm-font-size-lg);
            outline: none;
        }
        
        .dm-command-palette-list {
            max-height: 20rem;
            overflow-y: auto;
            padding: var(--dm-spacing-sm);
        }
        
        .dm-command-palette-item {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-md);
            padding: var(--dm-spacing-md) var(--dm-spacing-lg);
            border-radius: var(--dm-border-radius-sm);
            cursor: pointer;
        }
        
        .dm-command-palette-item:hover,
        .dm-command-palette-item--selected {
            background-color: var(--dm-accent);
        }
        
        .dm-command-palette-item-icon {
            width: 1.25rem;
            height: 1.25rem;
            color: var(--dm-muted-foreground);
        }
        
        .dm-command-palette-item-text {
            flex: 1;
        }
        
        .dm-command-palette-item-shortcut {
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
        }
        """


__all__ = [
    "DropdownAlign",
    "DatametriaDropdown",
    "DrawerSide",
    "DatametriaDrawer",
    "PopoverSide",
    "DatametriaPopover",
    "StepperOrientation",
    "DatametriaStepper",
    "DatametriaCommandPalette",
]
