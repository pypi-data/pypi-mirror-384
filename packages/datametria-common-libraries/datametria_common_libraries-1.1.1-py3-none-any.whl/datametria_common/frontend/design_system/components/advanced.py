"""
Componentes Avançados do Design System DATAMETRIA

Componentes complexos: Calendar, Advanced Table, etc.
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class CalendarView(Enum):
    """Visualização do calendário"""
    MONTH = "month"
    WEEK = "week"
    DAY = "day"
    YEAR = "year"


@dataclass
class DatametriaCalendar:
    """Componente Calendar DATAMETRIA - Calendário completo com eventos"""
    
    view: CalendarView = CalendarView.MONTH
    selectable: bool = True
    multiple: bool = False
    range: bool = False
    show_week_numbers: bool = False
    first_day_of_week: int = 0  # 0 = Sunday, 1 = Monday
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    disabled_dates: List[str] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_classes(self) -> str:
        classes = ["dm-calendar", f"dm-calendar--{self.view.value}"]
        if self.selectable:
            classes.append("dm-calendar--selectable")
        if self.show_week_numbers:
            classes.append("dm-calendar--week-numbers")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-calendar {
            background-color: var(--dm-card);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-lg);
            padding: var(--dm-spacing-lg);
        }
        
        /* Header */
        .dm-calendar-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--dm-spacing-xl);
        }
        
        .dm-calendar-title {
            font-size: var(--dm-font-size-lg);
            font-weight: 600;
        }
        
        .dm-calendar-nav {
            display: flex;
            gap: var(--dm-spacing-sm);
        }
        
        .dm-calendar-nav-button {
            padding: var(--dm-spacing-sm);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-sm);
            background: transparent;
            cursor: pointer;
        }
        
        .dm-calendar-nav-button:hover {
            background-color: var(--dm-accent);
        }
        
        /* Month View */
        .dm-calendar--month .dm-calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: var(--dm-spacing-xs);
        }
        
        .dm-calendar--week-numbers .dm-calendar-grid {
            grid-template-columns: auto repeat(7, 1fr);
        }
        
        .dm-calendar-weekday {
            padding: var(--dm-spacing-md);
            text-align: center;
            font-size: var(--dm-font-size-sm);
            font-weight: 600;
            color: var(--dm-muted-foreground);
        }
        
        .dm-calendar-week-number {
            padding: var(--dm-spacing-md);
            text-align: center;
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
        }
        
        .dm-calendar-day {
            position: relative;
            aspect-ratio: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            padding: var(--dm-spacing-sm);
            border-radius: var(--dm-border-radius-sm);
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .dm-calendar-day:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-calendar-day-number {
            font-size: var(--dm-font-size-sm);
            font-weight: 500;
        }
        
        .dm-calendar-day--today {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
        }
        
        .dm-calendar-day--selected {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
            font-weight: 600;
        }
        
        .dm-calendar-day--disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }
        
        .dm-calendar-day--other-month {
            opacity: 0.5;
        }
        
        .dm-calendar-day--range-start,
        .dm-calendar-day--range-end {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
        }
        
        .dm-calendar-day--in-range {
            background-color: var(--dm-accent);
        }
        
        /* Events */
        .dm-calendar-events {
            display: flex;
            flex-direction: column;
            gap: 2px;
            margin-top: var(--dm-spacing-xs);
            width: 100%;
        }
        
        .dm-calendar-event {
            height: 4px;
            border-radius: 2px;
            background-color: var(--dm-primary);
        }
        
        .dm-calendar-event--success {
            background-color: var(--dm-success);
        }
        
        .dm-calendar-event--warning {
            background-color: var(--dm-warning);
        }
        
        .dm-calendar-event--error {
            background-color: var(--dm-error);
        }
        
        /* Week View */
        .dm-calendar--week .dm-calendar-grid {
            display: grid;
            grid-template-columns: auto repeat(7, 1fr);
            gap: 1px;
            background-color: var(--dm-border);
        }
        
        .dm-calendar-time-slot {
            background-color: var(--dm-background);
            padding: var(--dm-spacing-sm);
            min-height: 3rem;
            position: relative;
        }
        
        .dm-calendar-time-label {
            font-size: var(--dm-font-size-xs);
            color: var(--dm-muted-foreground);
        }
        
        /* Day View */
        .dm-calendar--day .dm-calendar-grid {
            display: flex;
            flex-direction: column;
        }
        
        .dm-calendar-hour {
            display: grid;
            grid-template-columns: auto 1fr;
            border-bottom: 1px solid var(--dm-border);
            min-height: 4rem;
        }
        
        /* Year View */
        .dm-calendar--year .dm-calendar-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: var(--dm-spacing-lg);
        }
        
        .dm-calendar-month {
            padding: var(--dm-spacing-md);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            cursor: pointer;
        }
        
        .dm-calendar-month:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-calendar-month-name {
            font-weight: 600;
            margin-bottom: var(--dm-spacing-sm);
            text-align: center;
        }
        
        .dm-calendar-month-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 2px;
        }
        
        .dm-calendar-month-day {
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: var(--dm-font-size-xs);
        }
        """


class TableSortDirection(Enum):
    """Direção de ordenação"""
    ASC = "asc"
    DESC = "desc"
    NONE = "none"


@dataclass
class TableColumn:
    """Definição de coluna da tabela"""
    key: str
    label: str
    sortable: bool = False
    editable: bool = False
    width: Optional[str] = None
    align: str = "left"
    formatter: Optional[Callable] = None


@dataclass
class DatametriaAdvancedTable:
    """Componente Advanced Table DATAMETRIA - Tabela com recursos avançados"""
    
    columns: List[TableColumn] = field(default_factory=list)
    data: List[Dict[str, Any]] = field(default_factory=list)
    
    # Virtual Scrolling
    virtual_scroll: bool = True
    row_height: int = 48
    buffer_size: int = 5
    
    # Sorting
    sortable: bool = True
    sort_column: Optional[str] = None
    sort_direction: TableSortDirection = TableSortDirection.NONE
    
    # Selection
    selectable: bool = False
    multiple_selection: bool = False
    selected_rows: List[int] = field(default_factory=list)
    
    # Inline Editing
    inline_edit: bool = False
    edit_mode: str = "cell"  # cell, row
    
    # Pagination
    paginated: bool = False
    page_size: int = 50
    current_page: int = 1
    
    # Filtering
    filterable: bool = False
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # Resizing
    resizable_columns: bool = True
    
    # Row Actions
    row_actions: bool = False
    
    def get_classes(self) -> str:
        classes = ["dm-advanced-table"]
        if self.virtual_scroll:
            classes.append("dm-advanced-table--virtual")
        if self.selectable:
            classes.append("dm-advanced-table--selectable")
        if self.inline_edit:
            classes.append("dm-advanced-table--editable")
        return " ".join(classes)
    
    def get_css(self) -> str:
        return """
        .dm-advanced-table {
            position: relative;
            width: 100%;
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-md);
            overflow: hidden;
        }
        
        /* Virtual Scroll Container */
        .dm-advanced-table-viewport {
            overflow: auto;
            height: 600px;
            position: relative;
        }
        
        .dm-advanced-table-spacer {
            position: absolute;
            top: 0;
            left: 0;
            width: 1px;
            pointer-events: none;
        }
        
        /* Header */
        .dm-advanced-table-header {
            position: sticky;
            top: 0;
            z-index: 10;
            background-color: var(--dm-muted);
            border-bottom: 2px solid var(--dm-border);
        }
        
        .dm-advanced-table-header-row {
            display: flex;
        }
        
        .dm-advanced-table-header-cell {
            display: flex;
            align-items: center;
            gap: var(--dm-spacing-sm);
            padding: var(--dm-spacing-lg) var(--dm-spacing-xl);
            font-weight: 600;
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
            border-right: 1px solid var(--dm-border);
            position: relative;
            user-select: none;
        }
        
        .dm-advanced-table-header-cell:last-child {
            border-right: none;
        }
        
        .dm-advanced-table-header-cell--sortable {
            cursor: pointer;
        }
        
        .dm-advanced-table-header-cell--sortable:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-advanced-table-sort-icon {
            width: 1rem;
            height: 1rem;
            opacity: 0.5;
        }
        
        .dm-advanced-table-header-cell--sorted .dm-advanced-table-sort-icon {
            opacity: 1;
            color: var(--dm-primary);
        }
        
        /* Column Resizer */
        .dm-advanced-table-resizer {
            position: absolute;
            right: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            cursor: col-resize;
            user-select: none;
        }
        
        .dm-advanced-table-resizer:hover,
        .dm-advanced-table-resizer--active {
            background-color: var(--dm-primary);
        }
        
        /* Body */
        .dm-advanced-table-body {
            position: relative;
        }
        
        .dm-advanced-table-row {
            display: flex;
            border-bottom: 1px solid var(--dm-border);
            transition: background-color 0.2s;
        }
        
        .dm-advanced-table-row:hover {
            background-color: var(--dm-accent);
        }
        
        .dm-advanced-table-row--selected {
            background-color: var(--dm-primary);
            color: var(--dm-primary-foreground);
        }
        
        .dm-advanced-table-row--editing {
            background-color: var(--dm-warning);
            outline: 2px solid var(--dm-warning);
        }
        
        .dm-advanced-table-cell {
            display: flex;
            align-items: center;
            padding: var(--dm-spacing-lg) var(--dm-spacing-xl);
            font-size: var(--dm-font-size-sm);
            border-right: 1px solid var(--dm-border);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .dm-advanced-table-cell:last-child {
            border-right: none;
        }
        
        .dm-advanced-table-cell--align-center {
            justify-content: center;
        }
        
        .dm-advanced-table-cell--align-right {
            justify-content: flex-end;
        }
        
        /* Selection Checkbox */
        .dm-advanced-table-checkbox {
            width: 3rem;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* Inline Editing */
        .dm-advanced-table-cell--editable {
            cursor: pointer;
            position: relative;
        }
        
        .dm-advanced-table-cell--editable:hover::after {
            content: "";
            position: absolute;
            inset: 0;
            border: 2px solid var(--dm-primary);
            pointer-events: none;
        }
        
        .dm-advanced-table-cell-input {
            width: 100%;
            padding: var(--dm-spacing-sm);
            border: 2px solid var(--dm-primary);
            border-radius: var(--dm-border-radius-sm);
            background-color: var(--dm-background);
            font-size: var(--dm-font-size-sm);
        }
        
        .dm-advanced-table-cell-input:focus {
            outline: none;
            border-color: var(--dm-ring);
        }
        
        /* Row Actions */
        .dm-advanced-table-actions {
            display: flex;
            gap: var(--dm-spacing-sm);
            opacity: 0;
            transition: opacity 0.2s;
        }
        
        .dm-advanced-table-row:hover .dm-advanced-table-actions {
            opacity: 1;
        }
        
        .dm-advanced-table-action-button {
            padding: var(--dm-spacing-xs);
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: var(--dm-border-radius-sm);
        }
        
        .dm-advanced-table-action-button:hover {
            background-color: var(--dm-accent);
        }
        
        /* Filter Row */
        .dm-advanced-table-filter-row {
            display: flex;
            background-color: var(--dm-background);
            border-bottom: 1px solid var(--dm-border);
        }
        
        .dm-advanced-table-filter-cell {
            padding: var(--dm-spacing-sm) var(--dm-spacing-md);
            border-right: 1px solid var(--dm-border);
        }
        
        .dm-advanced-table-filter-input {
            width: 100%;
            padding: var(--dm-spacing-sm);
            border: 1px solid var(--dm-border);
            border-radius: var(--dm-border-radius-sm);
            font-size: var(--dm-font-size-sm);
        }
        
        /* Pagination */
        .dm-advanced-table-pagination {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--dm-spacing-lg);
            border-top: 1px solid var(--dm-border);
            background-color: var(--dm-muted);
        }
        
        .dm-advanced-table-pagination-info {
            font-size: var(--dm-font-size-sm);
            color: var(--dm-muted-foreground);
        }
        
        .dm-advanced-table-pagination-controls {
            display: flex;
            gap: var(--dm-spacing-sm);
        }
        
        /* Loading State */
        .dm-advanced-table--loading {
            opacity: 0.6;
            pointer-events: none;
        }
        
        .dm-advanced-table-loading-overlay {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: rgba(255, 255, 255, 0.8);
            z-index: 20;
        }
        
        /* Empty State */
        .dm-advanced-table-empty {
            padding: var(--dm-spacing-6xl);
            text-align: center;
            color: var(--dm-muted-foreground);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .dm-advanced-table-viewport {
                height: 400px;
            }
            
            .dm-advanced-table-cell,
            .dm-advanced-table-header-cell {
                padding: var(--dm-spacing-md);
                font-size: var(--dm-font-size-xs);
            }
        }
        """


__all__ = [
    "CalendarView",
    "DatametriaCalendar",
    "TableSortDirection",
    "TableColumn",
    "DatametriaAdvancedTable",
]
