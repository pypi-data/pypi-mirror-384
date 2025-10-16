"""
Metric Card Component DATAMETRIA

Card de métricas com ícone, valor, mudança percentual e trend.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MetricColor(Enum):
    """Cores do ícone"""
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    PURPLE = "purple"
    INDIGO = "indigo"
    PINK = "pink"
    EMERALD = "emerald"


@dataclass
class DatametriaMetricCard:
    """Componente de Metric Card"""
    title: str
    value: str
    icon: str
    color: MetricColor = MetricColor.BLUE
    change: Optional[float] = None
    trend_label: str = ""
    loading: bool = False
    clickable: bool = False
    
    COLOR_MAP = {
        MetricColor.BLUE: "#0072CE",
        MetricColor.GREEN: "#22c55e",
        MetricColor.YELLOW: "#f59e0b",
        MetricColor.RED: "#ef4444",
        MetricColor.PURPLE: "#4B0078",
        MetricColor.INDIGO: "#6366f1",
        MetricColor.PINK: "#ec4899",
        MetricColor.EMERALD: "#10b981",
    }
    
    def get_display_value(self) -> str:
        """Retorna valor formatado"""
        return "..." if self.loading else self.value
    
    def get_change_class(self) -> str:
        """Retorna classe CSS da mudança"""
        if not self.change:
            return ""
        return "positive" if self.change > 0 else "negative"
    
    def get_change_icon(self) -> str:
        """Retorna ícone da mudança"""
        if not self.change:
            return ""
        return "trending_up" if self.change > 0 else "trending_down"
    
    def get_classes(self) -> str:
        """Retorna classes CSS"""
        classes = ["dm-metric-card"]
        if self.clickable:
            classes.append("dm-metric-card--clickable")
        if self.loading:
            classes.append("dm-metric-card--loading")
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Retorna CSS do componente"""
        return """
/* Metric Card */
.dm-metric-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  border: 1px solid #e5e7eb;
}

.dm-metric-card--clickable {
  cursor: pointer;
  transition: all 0.2s;
}

.dm-metric-card--clickable:hover {
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  transform: translateY(-2px);
}

.dm-metric-card--loading {
  opacity: 0.6;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.dm-metric-card__header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.dm-metric-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 0.5rem;
  color: white;
}

.dm-metric-card__content {
  flex: 1;
}

.dm-metric-card__title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.dm-metric-card__value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
}

.dm-metric-card__change {
  display: inline-flex;
  align-items: center;
  margin-left: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.dm-metric-card__change.positive { color: #16a34a; }
.dm-metric-card__change.negative { color: #dc2626; }

.dm-metric-card__trend {
  margin-top: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
"""
    
    def to_html(self) -> str:
        """Gera HTML do card"""
        change_html = ""
        if self.change:
            change_html = f'''
            <span class="dm-metric-card__change {self.get_change_class()}">
              <i class="material-icons">{self.get_change_icon()}</i>
              {abs(self.change)}%
            </span>
            '''
        
        trend_html = ""
        if self.trend_label:
            trend_html = f'<div class="dm-metric-card__trend">{self.trend_label}</div>'
        
        return f'''
        <div class="{self.get_classes()}">
          <div class="dm-metric-card__header">
            <div class="dm-metric-card__icon" style="background-color: {self.COLOR_MAP[self.color]}">
              <i class="material-icons">{self.icon}</i>
            </div>
            <div class="dm-metric-card__content">
              <div class="dm-metric-card__title">{self.title}</div>
              <div class="dm-metric-card__value">
                {self.get_display_value()}
                {change_html}
              </div>
            </div>
          </div>
          {trend_html}
        </div>
        '''


__all__ = ["DatametriaMetricCard", "MetricColor"]
