"""
Entity Card Component DATAMETRIA

Card rico para exibição de entidades com múltiplas informações e ações.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum


class EntityType(Enum):
    """Tipos de entidade"""
    ORGANIZATION = "organization"
    USER = "user"
    PROJECT = "project"
    PRODUCT = "product"
    SERVICE = "service"


@dataclass
class DatametriaEntityCard:
    """Componente de Entity Card"""
    title: str
    subtitle: Optional[str] = None
    entity_type: EntityType = EntityType.ORGANIZATION
    status: str = "active"
    icon: str = "domain"
    avatar_color: str = "#0072CE"
    fields: Optional[List[Dict[str, str]]] = None
    description: Optional[str] = None
    show_actions: bool = True
    clickable: bool = True
    created_at: Optional[str] = None
    
    STATUS_COLORS = {
        "active": "#22c55e",
        "inactive": "#f59e0b",
        "suspended": "#ef4444",
        "pending": "#3b82f6",
    }
    
    STATUS_LABELS = {
        "active": "Ativo",
        "inactive": "Inativo",
        "suspended": "Suspenso",
        "pending": "Pendente",
    }
    
    def get_status_color(self) -> str:
        """Retorna cor do status"""
        return self.STATUS_COLORS.get(self.status.lower(), "#6b7280")
    
    def get_status_label(self) -> str:
        """Retorna label do status"""
        return self.STATUS_LABELS.get(self.status.lower(), self.status)
    
    def get_classes(self) -> str:
        """Retorna classes CSS"""
        classes = ["dm-entity-card"]
        if self.clickable:
            classes.append("dm-entity-card--clickable")
        return " ".join(classes)
    
    def get_css(self) -> str:
        """Retorna CSS do componente"""
        return """
/* Entity Card */
.dm-entity-card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: all 0.3s ease;
}

.dm-entity-card--clickable {
  cursor: pointer;
}

.dm-entity-card--clickable:hover {
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  transform: translateY(-2px);
}

.dm-entity-card__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.dm-entity-card__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  color: white;
  flex-shrink: 0;
}

.dm-entity-card__title-group {
  flex: 1;
  min-width: 0;
}

.dm-entity-card__title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dm-entity-card__subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.125rem;
}

.dm-entity-card__status {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dm-entity-card__body {
  padding: 1.5rem;
}

.dm-entity-card__fields {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dm-entity-card__field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.dm-entity-card__field-icon {
  color: #6b7280;
  font-size: 1rem;
}

.dm-entity-card__field-value {
  color: #374151;
}

.dm-entity-card__description {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.dm-entity-card__actions {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.dm-entity-card__action {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0.375rem;
  border: none;
  background: transparent;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.2s;
}

.dm-entity-card__action:hover {
  background: #e5e7eb;
}

.dm-entity-card__action--danger {
  color: #dc2626;
}

.dm-entity-card__action--danger:hover {
  background: #fee2e2;
}

.dm-entity-card__footer {
  padding: 0.75rem 1.5rem;
  font-size: 0.75rem;
  color: #9ca3af;
  border-top: 1px solid #e5e7eb;
}
"""
    
    def to_html(self) -> str:
        """Gera HTML do card"""
        # Status badge
        status_html = f'''
        <span class="dm-entity-card__status" style="background-color: {self.get_status_color()}20; color: {self.get_status_color()}">
          {self.get_status_label()}
        </span>
        '''
        
        # Fields
        fields_html = ""
        if self.fields:
            fields_items = []
            for field in self.fields:
                fields_items.append(f'''
                <div class="dm-entity-card__field">
                  <i class="material-icons dm-entity-card__field-icon">{field.get("icon", "info")}</i>
                  <span class="dm-entity-card__field-value">{field.get("value", "")}</span>
                </div>
                ''')
            fields_html = f'<div class="dm-entity-card__fields">{"".join(fields_items)}</div>'
        
        # Description
        description_html = ""
        if self.description:
            description_html = f'<div class="dm-entity-card__description">{self.description}</div>'
        
        # Actions
        actions_html = ""
        if self.show_actions:
            actions_html = '''
            <div class="dm-entity-card__actions">
              <button class="dm-entity-card__action">
                <i class="material-icons">visibility</i>
                Visualizar
              </button>
              <button class="dm-entity-card__action">
                <i class="material-icons">edit</i>
                Editar
              </button>
              <button class="dm-entity-card__action dm-entity-card__action--danger">
                <i class="material-icons">delete</i>
                Excluir
              </button>
            </div>
            '''
        
        # Footer
        footer_html = ""
        if self.created_at:
            footer_html = f'<div class="dm-entity-card__footer">Criado em {self.created_at}</div>'
        
        return f'''
        <div class="{self.get_classes()}">
          <div class="dm-entity-card__header">
            <div class="dm-entity-card__avatar" style="background-color: {self.avatar_color}">
              <i class="material-icons">{self.icon}</i>
            </div>
            <div class="dm-entity-card__title-group">
              <div class="dm-entity-card__title">{self.title}</div>
              {f'<div class="dm-entity-card__subtitle">{self.subtitle}</div>' if self.subtitle else ''}
            </div>
            {status_html}
          </div>
          <div class="dm-entity-card__body">
            {fields_html}
            {description_html}
          </div>
          {actions_html}
          {footer_html}
        </div>
        '''


__all__ = ["DatametriaEntityCard", "EntityType"]
