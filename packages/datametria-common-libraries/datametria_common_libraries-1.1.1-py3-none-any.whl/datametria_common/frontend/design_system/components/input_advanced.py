"""
Componentes de Input Avançado do Design System DATAMETRIA

Componentes avançados de entrada: DatePicker, FileUpload, ColorPicker, etc.
"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


@dataclass
class DatametriaDatePicker:
    """Componente DatePicker DATAMETRIA"""
    
    format: str = "YYYY-MM-DD"
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    disabled_dates: List[str] = None
    
    def get_classes(self) -> str:
        return "dm-datepicker"
    
    def get_css(self) -> str:
        return """
        .dm-datepicker {
            position: relative;
        }
        
        .dm-datepicker-input {
            width: 100%;
            padding: var(--dm-spacing-lg) var(--dm-spacing-xl);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            background-color: var(--dm-background);
        }
        
        .dm-datepicker-calendar {
            position: absolute;
            top: 100%;
            left: 0;
            margin-top: var(--dm-spacing-sm);
            padding: var(--dm-spacing-lg);
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            box-shadow: var(--dm-shadow-lg);
            z-index: 50;
        }
        
        .dm-datepicker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--dm-spacing-lg);
        }
        
        .dm-datepicker-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: var(--dm-spacing-xs);
        }
        
        .dm-datepicker-day {
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--dm-border-radius-sm);
            cursor: pointer;
        }
        
        .dm-datepicker-day:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-datepicker-day--selected {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
        }
        
        .dm-datepicker-day--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        """


@dataclass
class DatametriaTimePicker:
    """Componente TimePicker DATAMETRIA"""
    
    format: str = "HH:mm"
    step: int = 1
    
    def get_classes(self) -> str:
        return "dm-timepicker"
    
    def get_css(self) -> str:
        return """
        .dm-timepicker {
            position: relative;
        }
        
        .dm-timepicker-input {
            width: 100%;
            padding: var(--dm-spacing-lg) var(--dm-spacing-xl);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
        }
        
        .dm-timepicker-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            margin-top: var(--dm-spacing-sm);
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            box-shadow: var(--dm-shadow-lg);
            max-height: 16rem;
            overflow-y: auto;
            z-index: 50;
        }
        
        .dm-timepicker-option {
            padding: var(--dm-spacing-md) var(--dm-spacing-lg);
            cursor: pointer;
        }
        
        .dm-timepicker-option:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-timepicker-option--selected {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
        }
        """


@dataclass
class DatametriaFileUpload:
    """Componente FileUpload DATAMETRIA"""
    
    accept: Optional[str] = None
    multiple: bool = False
    max_size: Optional[int] = None
    drag_drop: bool = True
    
    def get_classes(self) -> str:
        classes = ["dm-file-upload"]
        if self.drag_drop:
            classes.append("dm-file-upload--drag-drop")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-file-upload {
            border: 2px dashed var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            padding: var(--dm-spacing-3xl);
            text-align: center;
            cursor: pointer;
            transition: border-color 0.2s;
        }
        
        .dm-file-upload:hover {
            border-color: var(--dm-primary);
        }
        
        .dm-file-upload--drag-over {
            border-color: var(--dm-primary);
            background-color: var(--dm-accent);
        }
        
        .dm-file-upload-icon {
            width: 3rem;
            height: 3rem;
            margin: 0 auto var(--dm-spacing-lg);
            color: var(--dm-muted-foreground);
        }
        
        .dm-file-upload-text {
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
        }
        
        .dm-file-upload-list {
            margin-top: var(--dm-spacing-xl);
        }
        
        .dm-file-upload-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--dm-spacing-md);
            background-color: var(--dm-muted);
            border-radius: var(--dm-border-radius-sm);
            margin-bottom: var(--dm-spacing-sm);
        }
        """


@dataclass
class DatametriaColorPicker:
    """Componente ColorPicker DATAMETRIA"""
    
    format: str = "hex"
    show_alpha: bool = False
    presets: Optional[List[str]] = None
    
    def get_classes(self) -> str:
        return "dm-color-picker"
    
    def get_css(self) -> str:
        return """
        .dm-color-picker {
            position: relative;
        }
        
        .dm-color-picker-trigger {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-md);
            padding: var(--dm-spacing-lg);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            cursor: pointer;
        }
        
        .dm-color-picker-swatch {
            width: 2rem;
            height: 2rem;
            border-radius: var(--dm-border-radius-sm);
            border: 1px solid var(--dm-border);
        }
        
        .dm-color-picker-popover {
            position: absolute;
            top: 100%;
            left: 0;
            margin-top: var(--dm-spacing-sm);
            padding: var(--dm-spacing-lg);
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            box-shadow: var(--dm-shadow-lg);
            z-index: 50;
        }
        
        .dm-color-picker-canvas {
            width: 16rem;
            height: 10rem;
            border-radius: var(--dm-border-radius-sm);
            margin-bottom: var(--dm-spacing-lg);
        }
        
        .dm-color-picker-presets {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: var(--dm-spacing-sm);
        }
        
        .dm-color-picker-preset {
            aspect-ratio: 1;
            border-radius: var(--dm-border-radius-sm);
            border: 1px solid var(--dm-border);
            cursor: pointer;
        }
        """


@dataclass
class DatametriaAutocomplete:
    """Componente Autocomplete DATAMETRIA"""
    
    placeholder: str = "Search..."
    min_chars: int = 1
    max_results: int = 10
    
    def get_classes(self) -> str:
        return "dm-autocomplete"
    
    def get_css(self) -> str:
        return """
        .dm-autocomplete {
            position: relative;
        }
        
        .dm-autocomplete-input {
            width: 100%;
            padding: var(--dm-spacing-lg) var(--dm-spacing-xl);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
        }
        
        .dm-autocomplete-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            margin-top: var(--dm-spacing-sm);
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            box-shadow: var(--dm-shadow-lg);
            max-height: 20rem;
            overflow-y: auto;
            z-index: 50;
        }
        
        .dm-autocomplete-option {
            padding: var(--dm-spacing-md) var(--dm-spacing-lg);
            cursor: pointer;
        }
        
        .dm-autocomplete-option:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-autocomplete-option--selected {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
        }
        
        .dm-autocomplete-option--highlighted {
            background-color: var(--dm-accent);
        }
        """


@dataclass
class DatametriaRichTextEditor:
    """Componente RichTextEditor DATAMETRIA"""
    
    toolbar: bool = True
    min_height: str = "10rem"
    max_height: Optional[str] = None
    
    def get_classes(self) -> str:
        return "dm-rich-text-editor"
    
    def get_css(self) -> str:
        return """
        .dm-rich-text-editor {
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            overflow: hidden;
        }
        
        .dm-rich-text-toolbar {
            display: flex;
            gap: var(--dm-spacing-xs);
            padding: var(--dm-spacing-md);
            background-color: var(--dm-muted);
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-rich-text-toolbar-button {
            padding: var(--dm-spacing-sm);
            border: none;
            background: transparent;
            border-radius: var(--dm-border-radius-sm);
            cursor: pointer;
        }
        
        .dm-rich-text-toolbar-button:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-rich-text-toolbar-button--active {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
        }
        
        .dm-rich-text-content {
            padding: var(--dm-spacing-lg);
            min-height: 10rem;
            outline: none;
        }
        
        .dm-rich-text-content:focus {
            outline: 2px solid var(--dm-ring);
            outline-offset: -2px;
        }
        """


__all__ = [
    "DatametriaDatePicker",
    "DatametriaTimePicker",
    "DatametriaFileUpload",
    "DatametriaColorPicker",
    "DatametriaAutocomplete",
    "DatametriaRichTextEditor",
]
