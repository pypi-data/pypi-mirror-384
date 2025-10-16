"""
Componentes de Layout do Design System DATAMETRIA

Card, Container, Grid, Stack, Divider
"""

from typing import Optional, Union, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum


class CardVariant(Enum):
    """Variantes do card"""
    DEFAULT = "default"
    OUTLINED = "outlined"
    ELEVATED = "elevated"


@dataclass
class DatametriaCard:
    """Componente Card DATAMETRIA"""
    
    variant: CardVariant = CardVariant.DEFAULT
    padding: bool = True
    
    def get_classes(self) -> str:
        """Gera classes CSS do card"""
        classes = ["dm-card"]
        
        variant_classes = {
            CardVariant.DEFAULT: "dm-card--default",
            CardVariant.OUTLINED: "dm-card--outlined",
            CardVariant.ELEVATED: "dm-card--elevated",
        }
        classes.append(variant_classes[self.variant])
        
        if self.padding:
            classes.append("dm-card--padded")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-card {
            border-radius: var(--dm-border-radius-lg);
            background-color: var(--dm-card);
            color: var(--dm-card-foreground);
            overflow: hidden;
        }
        
        .dm-card--default {
            border: 1px solid var(--dm-border);
        }
        
        .dm-card--outlined {
            border: 2px solid var(--dm-border);
        }
        
        .dm-card--elevated {
            border: 1px solid var(--dm-border);
            box-shadow: var(--dm-shadow-md);
        }
        
        .dm-card--padded {
            padding: var(--dm-spacing-6xl);
        }
        
        .dm-card-header {
            padding: var(--dm-spacing-6xl) var(--dm-spacing-6xl) 0;
        }
        
        .dm-card-content {
            padding: var(--dm-spacing-6xl);
        }
        
        .dm-card-footer {
            padding: 0 var(--dm-spacing-6xl) var(--dm-spacing-6xl);
        }
        
        .dm-card-title {
            font-size: var(--dm-font-size-lg);
            font-weight: 600;
            line-height: var(--dm-line-height-tight);
            margin-bottom: var(--dm-spacing-sm);
        }
        
        .dm-card-description {
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
        }
        """


class ContainerSize(Enum):
    """Tamanhos do container"""
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"
    FULL = "full"


@dataclass
class DatametriaContainer:
    """Componente Container DATAMETRIA"""
    
    size: ContainerSize = ContainerSize.LG
    centered: bool = True
    
    def get_classes(self) -> str:
        """Gera classes CSS do container"""
        classes = ["dm-container"]
        
        size_classes = {
            ContainerSize.SM: "dm-container--sm",
            ContainerSize.MD: "dm-container--md",
            ContainerSize.LG: "dm-container--lg",
            ContainerSize.XL: "dm-container--xl",
            ContainerSize.FULL: "dm-container--full",
        }
        classes.append(size_classes[self.size])
        
        if self.centered:
            classes.append("dm-container--centered")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-container {
            width: 100%;
            padding-left: var(--dm-spacing-xl);
            padding-right: var(--dm-spacing-xl);
        }
        
        .dm-container--centered {
            margin-left: auto;
            margin-right: auto;
        }
        
        .dm-container--sm { max-width: 640px; }
        .dm-container--md { max-width: 768px; }
        .dm-container--lg { max-width: 1024px; }
        .dm-container--xl { max-width: 1280px; }
        .dm-container--full { max-width: none; }
        
        @media (min-width: 640px) {
            .dm-container {
                padding-left: var(--dm-spacing-2xl);
                padding-right: var(--dm-spacing-2xl);
            }
        }
        """


class GridCols(Enum):
    """Colunas do grid"""
    COL_1 = "1"
    COL_2 = "2"
    COL_3 = "3"
    COL_4 = "4"
    COL_5 = "5"
    COL_6 = "6"
    COL_12 = "12"


@dataclass
class DatametriaGrid:
    """Componente Grid DATAMETRIA"""
    
    cols: GridCols = GridCols.COL_1
    gap: str = "md"
    
    def get_classes(self) -> str:
        """Gera classes CSS do grid"""
        classes = ["dm-grid"]
        
        col_classes = {
            GridCols.COL_1: "dm-grid--cols-1",
            GridCols.COL_2: "dm-grid--cols-2",
            GridCols.COL_3: "dm-grid--cols-3",
            GridCols.COL_4: "dm-grid--cols-4",
            GridCols.COL_5: "dm-grid--cols-5",
            GridCols.COL_6: "dm-grid--cols-6",
            GridCols.COL_12: "dm-grid--cols-12",
        }
        classes.append(col_classes[self.cols])
        classes.append(f"dm-grid--gap-{self.gap}")
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-grid {
            display: grid;
        }
        
        .dm-grid--cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
        .dm-grid--cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .dm-grid--cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .dm-grid--cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        .dm-grid--cols-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
        .dm-grid--cols-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
        .dm-grid--cols-12 { grid-template-columns: repeat(12, minmax(0, 1fr)); }
        
        .dm-grid--gap-xs { gap: var(--dm-spacing-xs); }
        .dm-grid--gap-sm { gap: var(--dm-spacing-sm); }
        .dm-grid--gap-md { gap: var(--dm-spacing-md); }
        .dm-grid--gap-lg { gap: var(--dm-spacing-lg); }
        .dm-grid--gap-xl { gap: var(--dm-spacing-xl); }
        .dm-grid--gap-2xl { gap: var(--dm-spacing-2xl); }
        """


class StackDirection(Enum):
    """Direção do stack"""
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class StackAlign(Enum):
    """Alinhamento do stack"""
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


@dataclass
class DatametriaStack:
    """Componente Stack DATAMETRIA"""
    
    direction: StackDirection = StackDirection.VERTICAL
    gap: str = "md"
    align: StackAlign = StackAlign.STRETCH
    
    def get_classes(self) -> str:
        """Gera classes CSS do stack"""
        classes = ["dm-stack"]
        
        direction_classes = {
            StackDirection.VERTICAL: "dm-stack--vertical",
            StackDirection.HORIZONTAL: "dm-stack--horizontal",
        }
        classes.append(direction_classes[self.direction])
        
        align_classes = {
            StackAlign.START: "dm-stack--align-start",
            StackAlign.CENTER: "dm-stack--align-center",
            StackAlign.END: "dm-stack--align-end",
            StackAlign.STRETCH: "dm-stack--align-stretch",
        }
        classes.append(align_classes[self.align])
        
        classes.append(f"dm-stack--gap-{self.gap}")
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-stack {
            display: flex;
        }
        
        .dm-stack--vertical {
            flex-direction: column;
        }
        
        .dm-stack--horizontal {
            flex-direction: row;
        }
        
        .dm-stack--align-start {
            align-items: flex-start;
        }
        
        .dm-stack--align-center {
            align-items: center;
        }
        
        .dm-stack--align-end {
            align-items: flex-end;
        }
        
        .dm-stack--align-stretch {
            align-items: stretch;
        }
        
        .dm-stack--gap-xs { gap: var(--dm-spacing-xs); }
        .dm-stack--gap-sm { gap: var(--dm-spacing-sm); }
        .dm-stack--gap-md { gap: var(--dm-spacing-md); }
        .dm-stack--gap-lg { gap: var(--dm-spacing-lg); }
        .dm-stack--gap-xl { gap: var(--dm-spacing-xl); }
        .dm-stack--gap-2xl { gap: var(--dm-spacing-2xl); }
        """


class DividerOrientation(Enum):
    """Orientação do divider"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass
class DatametriaDivider:
    """Componente Divider DATAMETRIA"""
    
    orientation: DividerOrientation = DividerOrientation.HORIZONTAL
    
    def get_classes(self) -> str:
        """Gera classes CSS do divider"""
        classes = ["dm-divider"]
        
        orientation_classes = {
            DividerOrientation.HORIZONTAL: "dm-divider--horizontal",
            DividerOrientation.VERTICAL: "dm-divider--vertical",
        }
        classes.append(orientation_classes[self.orientation])
        
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-divider {
            border: none;
            background-color: var(--dm-border);
        }
        
        .dm-divider--horizontal {
            width: 100%;
            height: 1px;
            margin: var(--dm-spacing-xl) 0;
        }
        
        .dm-divider--vertical {
            width: 1px;
            height: 100%;
            margin: 0 var(--dm-spacing-xl);
        }
        """


# Export
__all__ = [
    "CardVariant",
    "DatametriaCard",
    "ContainerSize",
    "DatametriaContainer",
    "GridCols",
    "DatametriaGrid",
    "StackDirection",
    "StackAlign", 
    "DatametriaStack",
    "DividerOrientation",
    "DatametriaDivider",
]
