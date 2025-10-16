"""
Componentes de Data Display do Design System DATAMETRIA

Componentes para exibição de dados: Table, List, Accordion, Timeline, etc.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class TableVariant(Enum):
    """Variantes da tabela"""
    DEFAULT = "default"
    STRIPED = "striped"
    BORDERED = "bordered"
    HOVERABLE = "hoverable"


@dataclass
class DatametriaTable:
    """Componente Table DATAMETRIA"""
    
    variant: TableVariant = TableVariant.DEFAULT
    sticky_header: bool = False
    sortable: bool = False
    selectable: bool = False
    
    def get_classes(self) -> str:
        classes = ["dm-table"]
        variant_map = {
            TableVariant.DEFAULT: "dm-table--default",
            TableVariant.STRIPED: "dm-table--striped",
            TableVariant.BORDERED: "dm-table--bordered",
            TableVariant.HOVERABLE: "dm-table--hoverable",
        }
        classes.append(variant_map[self.variant])
        if self.sticky_header:
            classes.append("dm-table--sticky-header")
        if self.sortable:
            classes.append("dm-table--sortable")
        if self.selectable:
            classes.append("dm-table--selectable")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-table {
            width: 100%;
            border-collapse: collapse;
            font-size: var(--dm-font-size-sm);
        }
        
        .dm-table th,
        .dm-table td {
            padding: var(--dm-spacing-lg) var(--dm-spacing-xl);
            text-align: left;
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-table th {
            font-weight: 600;
            color: var(--dm-muted-foreground);
            background-color: var(--dm-muted);
        }
        
        .dm-table--striped tbody tr:nth-child(even) {
            background-color: var(--dm-muted);
        }
        
        .dm-table--bordered {
            border: 1px solid var(--dm-border);
        }
        
        .dm-table--bordered th,
        .dm-table--bordered td {
            border: 1px solid var(--dm-border);
        }
        
        .dm-table--hoverable tbody tr:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-table--sticky-header thead {
            position: sticky;
            top: 0;
            z-index: 10;
        }
        """


@dataclass
class DatametriaList:
    """Componente List DATAMETRIA"""
    
    ordered: bool = False
    spacing: str = "md"
    
    def get_classes(self) -> str:
        classes = ["dm-list"]
        if self.ordered:
            classes.append("dm-list--ordered")
        classes.append(f"dm-list--spacing-{self.spacing}")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .dm-list-item {
            padding: var(--dm-spacing-lg);
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-list-item:last-child {
            border-bottom: none;
        }
        
        .dm-list--ordered {
            counter-reset: list-counter;
        }
        
        .dm-list--ordered .dm-list-item::before {
            counter-increment: list-counter;
            content: counter(list-counter) ". ";
            font-weight: 600;
            margin-right: var(--dm-spacing-md);
        }
        """


@dataclass
class DatametriaAccordion:
    """Componente Accordion DATAMETRIA"""
    
    multiple: bool = False
    collapsible: bool = True
    
    def get_classes(self) -> str:
        classes = ["dm-accordion"]
        if self.multiple:
            classes.append("dm-accordion--multiple")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-accordion {
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
        }
        
        .dm-accordion-item {
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-accordion-item:last-child {
            border-bottom: none;
        }
        
        .dm-accordion-trigger {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            padding: var(--dm-spacing-xl);
            background: transparent;
            border: none;
            cursor: pointer;
            font-weight: 500;
            text-align: left;
        }
        
        .dm-accordion-trigger:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-accordion-content {
            padding: 0 var(--dm-spacing-xl) var(--dm-spacing-xl);
            overflow: hidden;
            transition: height 0.2s ease;
        }
        
        .dm-accordion-content[data-state="closed"] {
            display: none;
        }
        """


@dataclass
class DatametriaTimeline:
    """Componente Timeline DATAMETRIA"""
    
    position: str = "left"
    
    def get_classes(self) -> str:
        return f"dm-timeline dm-timeline--{self.position}"
    
    def get_css(self) -> str:
        return """
        .dm-timeline {
            position: relative;
            padding-left: var(--dm-spacing-3xl);
        }
        
        .dm-timeline::before {
            content: "";
            position: absolute;
            left: var(--dm-spacing-lg);
            top: 0;
            bottom: 0;
            width: 2px;
            background-color: var(--dm-border);
        }
        
        .dm-timeline-item {
            position: relative;
            padding-bottom: var(--dm-spacing-2xl);
        }
        
        .dm-timeline-marker {
            position: absolute;
            left: calc(-1 * var(--dm-spacing-3xl) + var(--dm-spacing-md));
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: var(--dm-primary);
            border: 2px solid var(--dm-background);
        }
        
        .dm-timeline-content {
            padding: var(--dm-spacing-lg);
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
        }
        """


@dataclass
class DatametriaCarousel:
    """Componente Carousel DATAMETRIA"""
    
    autoplay: bool = False
    loop: bool = True
    show_controls: bool = True
    show_indicators: bool = True
    
    def get_classes(self) -> str:
        classes = ["dm-carousel"]
        if self.autoplay:
            classes.append("dm-carousel--autoplay")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-carousel {
            position: relative;
            overflow: hidden;
        }
        
        .dm-carousel-viewport {
            overflow: hidden;
        }
        
        .dm-carousel-container {
            display: flex;
            transition: transform 0.3s ease;
        }
        
        .dm-carousel-item {
            flex: 0 0 100%;
            min-width: 0;
        }
        
        .dm-carousel-controls {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 100%;
            display: flex;
            justify-content: space-between;
            padding: 0 var(--dm-spacing-lg);
            pointer-events: none;
        }
        
        .dm-carousel-button {
            pointer-events: all;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            background-color: var(--dm-background);
            border: 1px solid var(--dm-border);
            cursor: pointer;
        }
        
        .dm-carousel-indicators {
            display: flex;
            justify-content: center;
            gap: var(--dm-spacing-sm);
            padding: var(--dm-spacing-lg);
        }
        
        .dm-carousel-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--dm-muted);
            cursor: pointer;
        }
        
        .dm-carousel-indicator--active {
            background-color: var(--dm-primary);
        }
        """


@dataclass
class DatametriaImage:
    """Componente Image DATAMETRIA"""
    
    aspect_ratio: str = "auto"
    object_fit: str = "cover"
    rounded: bool = False
    
    def get_classes(self) -> str:
        classes = ["dm-image"]
        if self.rounded:
            classes.append("dm-image--rounded")
        classes.append(f"dm-image--{self.object_fit}")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-image {
            display: block;
            max-width: 100%;
            height: auto;
        }
        
        .dm-image--cover {
            object-fit: cover;
        }
        
        .dm-image--contain {
            object-fit: contain;
        }
        
        .dm-image--rounded {
            border-radius: var(--dm-border-radius-md);
        }
        """


@dataclass
class DatametriaSkeleton:
    """Componente Skeleton Loader DATAMETRIA"""
    
    variant: str = "text"
    width: str = "100%"
    height: str = "1rem"
    
    def get_classes(self) -> str:
        return f"dm-skeleton dm-skeleton--{self.variant}"
    
    def get_css(self) -> str:
        return """
        .dm-skeleton {
            background: linear-gradient(
                90deg,
                var(--dm-muted) 0%,
                var(--dm-accent) 50%,
                var(--dm-muted) 100%
            );
            background-size: 200% 100%;
            animation: dm-skeleton-loading 1.5s ease-in-out infinite;
            border-radius: var(--dm-border-radius-sm);
        }
        
        @keyframes dm-skeleton-loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        .dm-skeleton--text {
            height: 1rem;
            margin-bottom: var(--dm-spacing-sm);
        }
        
        .dm-skeleton--circle {
            border-radius: 50%;
            width: 3rem;
            height: 3rem;
        }
        
        .dm-skeleton--rectangle {
            width: 100%;
            height: 10rem;
        }
        """


@dataclass
class DatametriaEmptyState:
    """Componente Empty State DATAMETRIA"""
    
    icon: Optional[str] = None
    title: str = "No data"
    description: Optional[str] = None
    
    def get_classes(self) -> str:
        return "dm-empty-state"
    
    def get_css(self) -> str:
        return """
        .dm-empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: var(--dm-spacing-6xl);
            text-align: center;
        }
        
        .dm-empty-state-icon {
            width: 4rem;
            height: 4rem;
            margin-bottom: var(--dm-spacing-xl);
            color: var(--dm-muted-foreground);
        }
        
        .dm-empty-state-title {
            font-size: var(--dm-font-size-lg);
            font-weight: 600;
            margin-bottom: var(--dm-spacing-md);
        }
        
        .dm-empty-state-description {
            color: var(--dm-muted-foreground);
            max-width: 32rem;
        }
        """


__all__ = [
    "TableVariant",
    "DatametriaTable",
    "DatametriaList",
    "DatametriaAccordion",
    "DatametriaTimeline",
    "DatametriaCarousel",
    "DatametriaImage",
    "DatametriaSkeleton",
    "DatametriaEmptyState",
]
