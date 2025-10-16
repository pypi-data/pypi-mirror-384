"""
Componentes de Navegação do Design System DATAMETRIA

Navbar, Sidebar, Breadcrumb, Tabs, Pagination
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


@dataclass
class NavItem:
    """Item de navegação"""
    label: str
    href: str
    active: bool = False
    disabled: bool = False
    icon: Optional[str] = None


@dataclass
class DatametriaNavbar:
    """Componente Navbar DATAMETRIA"""
    
    brand: Optional[str] = None
    items: List[NavItem] = None
    sticky: bool = False
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
    
    def get_classes(self) -> str:
        """Gera classes CSS do navbar"""
        classes = ["dm-navbar"]
        
        if self.sticky:
            classes.append("dm-navbar--sticky")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-navbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--dm-spacing-xl) var(--dm-spacing-2xl);
            background-color: var(--dm-background);
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-navbar--sticky {
            position: sticky;
            top: 0;
            z-index: 50;
        }
        
        .dm-navbar-brand {
            font-size: var(--dm-font-size-lg);
            font-weight: 600;
            color: var(--dm-foreground);
            text-decoration: none;
        }
        
        .dm-navbar-nav {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-2xl);
        }
        
        .dm-navbar-item {
            color: var(--dm-muted-foreground);
            text-decoration: none;
            font-weight: 500;
            transition: var(--dm-transition-colors);
            padding: var(--dm-spacing-sm) var(--dm-spacing-md);
            border-radius: var(--dm-border-radius-md);
        }
        
        .dm-navbar-item:hover {
            color: var(--dm-foreground);
            background-color: var(--dm-accent);
        }
        
        .dm-navbar-item--active {
            color: var(--dm-primary);
            background-color: var(--dm-accent);
        }
        
        .dm-navbar-item--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        """


class SidebarVariant(Enum):
    """Variantes do sidebar"""
    DEFAULT = "default"
    FLOATING = "floating"
    OVERLAY = "overlay"


@dataclass
class DatametriaSidebar:
    """Componente Sidebar DATAMETRIA"""
    
    variant: SidebarVariant = SidebarVariant.DEFAULT
    collapsible: bool = True
    collapsed: bool = False
    
    def get_classes(self) -> str:
        """Gera classes CSS do sidebar"""
        classes = ["dm-sidebar"]
        
        variant_classes = {
            SidebarVariant.DEFAULT: "dm-sidebar--default",
            SidebarVariant.FLOATING: "dm-sidebar--floating",
            SidebarVariant.OVERLAY: "dm-sidebar--overlay",
        }
        classes.append(variant_classes[self.variant])
        
        if self.collapsible:
            classes.append("dm-sidebar--collapsible")
        if self.collapsed:
            classes.append("dm-sidebar--collapsed")
            
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-sidebar {
            display: flex;
            flex-direction: column;
            width: 16rem;
            height: 100vh;
            background-color: var(--dm-card);
            border-right: 1px solid var(--dm-border);
            transition: var(--dm-transition-all);
        }
        
        .dm-sidebar--floating {
            margin: var(--dm-spacing-xl);
            height: calc(100vh - 2 * var(--dm-spacing-xl));
            border-radius: var(--dm-border-radius-lg);
            border: 1px solid var(--dm-border);
        }
        
        .dm-sidebar--overlay {
            position: fixed;
            top: 0;
            left: 0;
            z-index: 50;
            box-shadow: var(--dm-shadow-lg);
        }
        
        .dm-sidebar--collapsed {
            width: 4rem;
        }
        
        .dm-sidebar-header {
            padding: var(--dm-spacing-xl);
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-sidebar-content {
            flex: 1;
            padding: var(--dm-spacing-xl);
            overflow-y: auto;
        }
        
        .dm-sidebar-nav {
            display: flex;
            flex-direction: column;
            gap: var(--dm-spacing-sm);
        }
        
        .dm-sidebar-item {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-md);
            padding: var(--dm-spacing-md);
            color: var(--dm-muted-foreground);
            text-decoration: none;
            border-radius: var(--dm-border-radius-md);
            transition: var(--dm-transition-colors);
        }
        
        .dm-sidebar-item:hover {
            color: var(--dm-foreground);
            background-color: var(--dm-accent);
        }
        
        .dm-sidebar-item--active {
            color: var(--dm-primary);
            background-color: var(--dm-accent);
        }
        """


@dataclass
class BreadcrumbItem:
    """Item do breadcrumb"""
    label: str
    href: Optional[str] = None
    active: bool = False


@dataclass
class DatametriaBreadcrumb:
    """Componente Breadcrumb DATAMETRIA"""
    
    items: List[BreadcrumbItem]
    separator: str = "/"
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-breadcrumb {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-sm);
            font-size: var(--dm-font-size-sm);
        }
        
        .dm-breadcrumb-item {
            color: var(--dm-muted-foreground);
            text-decoration: none;
            transition: var(--dm-transition-colors);
        }
        
        .dm-breadcrumb-item:hover {
            color: var(--dm-foreground);
        }
        
        .dm-breadcrumb-item--active {
            color: var(--dm-foreground);
            font-weight: 500;
        }
        
        .dm-breadcrumb-separator {
            color: var(--dm-muted-foreground);
        }
        """


@dataclass
class TabItem:
    """Item da tab"""
    label: str
    value: str
    disabled: bool = False
    icon: Optional[str] = None


@dataclass
class DatametriaTabs:
    """Componente Tabs DATAMETRIA"""
    
    items: List[TabItem]
    active_tab: str = ""
    
    def __post_init__(self):
        if not self.active_tab and self.items:
            self.active_tab = self.items[0].value
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-tabs {
            display: flex;
            flex-direction: column;
        }
        
        .dm-tabs-list {
            display: flex;
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-tabs-trigger {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-sm);
            padding: var(--dm-spacing-md) var(--dm-spacing-xl);
            color: var(--dm-muted-foreground);
            background: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            cursor: pointer;
            transition: var(--dm-transition-colors);
            font-size: var(--dm-font-size-sm);
            font-weight: 500;
        }
        
        .dm-tabs-trigger:hover:not(.dm-tabs-trigger--disabled) {
            color: var(--dm-foreground);
        }
        
        .dm-tabs-trigger--active {
            color: var(--dm-primary);
            border-bottom-color: var(--dm-primary);
        }
        
        .dm-tabs-trigger--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .dm-tabs-content {
            padding: var(--dm-spacing-xl);
        }
        """


@dataclass
class DatametriaPagination:
    """Componente Pagination DATAMETRIA"""
    
    current_page: int = 1
    total_pages: int = 1
    show_first_last: bool = True
    show_prev_next: bool = True
    
    def get_css(self) -> str:
        """Gera CSS do componente"""
        return """
        .dm-pagination {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-sm);
        }
        
        .dm-pagination-item {
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 2.5rem;
            height: 2.5rem;
            padding: 0 var(--dm-spacing-md);
            color: var(--dm-muted-foreground);
            background: transparent;
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            cursor: pointer;
            transition: var(--dm-transition-colors);
            text-decoration: none;
            font-size: var(--dm-font-size-sm);
        }
        
        .dm-pagination-item:hover:not(.dm-pagination-item--disabled) {
            color: var(--dm-foreground);
            background-color: var(--dm-accent);
        }
        
        .dm-pagination-item--active {
            color: var(--dm-primary-foreground);
            background-color: var(--dm-primary);
            border-color: var(--dm-primary);
        }
        
        .dm-pagination-item--disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .dm-pagination-ellipsis {
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 2.5rem;
            height: 2.5rem;
            color: var(--dm-muted-foreground);
        }
        """


# Export
__all__ = [
    "NavItem",
    "DatametriaNavbar",
    "SidebarVariant",
    "DatametriaSidebar",
    "BreadcrumbItem",
    "DatametriaBreadcrumb",
    "TabItem",
    "DatametriaTabs",
    "DatametriaPagination",
]
