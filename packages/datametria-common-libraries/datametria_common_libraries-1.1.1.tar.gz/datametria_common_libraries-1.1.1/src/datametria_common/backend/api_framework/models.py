"""
🔧 Models - DATAMETRIA API Framework

Modelos Pydantic base e utilitários para APIs DATAMETRIA.
"""

from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

# Type variable para modelos genéricos
T = TypeVar('T')


class DatametriaBaseModel(BaseModel):
    """Modelo base DATAMETRIA com configurações padrão."""
    
    class Config:
        """Configuração padrão para modelos DATAMETRIA."""
        # Permitir uso de atributos de ORM (SQLAlchemy)
        from_attributes = True
        
        # Validar atribuições
        validate_assignment = True
        
        # Usar enum values
        use_enum_values = True
        
        # Configurações de JSON
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        
        # Permitir campos extras em modo de desenvolvimento
        extra = "forbid"  # Mudar para "allow" em desenvolvimento se necessário


class TimestampMixin(BaseModel):
    """Mixin para campos de timestamp."""
    
    created_at: Optional[datetime] = Field(None, description="Data de criação")
    updated_at: Optional[datetime] = Field(None, description="Data de atualização")


class PaginationParams(BaseModel):
    """Parâmetros de paginação padrão."""
    
    page: int = Field(1, ge=1, description="Número da página")
    per_page: int = Field(10, ge=1, le=100, description="Itens por página")
    
    @property
    def offset(self) -> int:
        """Calcula offset para query."""
        return (self.page - 1) * self.per_page


class SortParams(BaseModel):
    """Parâmetros de ordenação."""
    
    sort_by: Optional[str] = Field(None, description="Campo para ordenação")
    sort_order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="Ordem (asc/desc)")


class FilterParams(BaseModel):
    """Parâmetros base para filtros."""
    
    search: Optional[str] = Field(None, description="Termo de busca")
    active: Optional[bool] = Field(None, description="Filtrar por status ativo")


class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica."""
    
    items: List[T] = Field(description="Lista de itens")
    total: int = Field(description="Total de registros")
    page: int = Field(description="Página atual")
    per_page: int = Field(description="Itens por página")
    pages: int = Field(description="Total de páginas")
    has_next: bool = Field(description="Tem próxima página")
    has_prev: bool = Field(description="Tem página anterior")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        per_page: int
    ) -> "PaginatedResponse[T]":
        """
        Cria resposta paginada.
        
        Args:
            items: Lista de itens
            total: Total de registros
            page: Página atual
            per_page: Itens por página
            
        Returns:
            PaginatedResponse: Resposta paginada
        """
        pages = (total + per_page - 1) // per_page
        
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class HealthCheckResponse(DatametriaBaseModel):
    """Resposta de health check."""
    
    status: str = Field(description="Status do serviço")
    service: str = Field(description="Nome do serviço")
    version: str = Field(description="Versão do serviço")
    timestamp: datetime = Field(description="Timestamp da verificação")
    components: Optional[Dict[str, str]] = Field(None, description="Status dos componentes")


class ErrorDetail(DatametriaBaseModel):
    """Detalhe de erro."""
    
    field: str = Field(description="Campo com erro")
    message: str = Field(description="Mensagem de erro")
    code: Optional[str] = Field(None, description="Código do erro")


class ValidationErrorResponse(DatametriaBaseModel):
    """Resposta de erro de validação."""
    
    message: str = Field(description="Mensagem principal")
    errors: List[ErrorDetail] = Field(description="Lista de erros")


# Enums comuns

class StatusEnum(str, Enum):
    """Status padrão para entidades."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"


class SortOrderEnum(str, Enum):
    """Ordem de classificação."""
    ASC = "asc"
    DESC = "desc"


class OperationEnum(str, Enum):
    """Tipos de operação."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


# Modelos de exemplo para usuários (podem ser customizados)

class UserRole(str, Enum):
    """Roles de usuário."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserBase(DatametriaBaseModel):
    """Modelo base de usuário."""
    
    name: str = Field(..., min_length=2, max_length=100, description="Nome do usuário")
    email: str = Field(..., description="Email do usuário")
    role: UserRole = Field(UserRole.USER, description="Role do usuário")
    active: bool = Field(True, description="Status ativo")
    
    @validator('email')
    def validate_email(cls, v):
        """Valida formato do email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()


class UserCreate(UserBase):
    """Modelo para criação de usuário."""
    
    password: str = Field(..., min_length=8, max_length=128, description="Senha do usuário")
    
    @validator('password')
    def validate_password(cls, v):
        """Valida força da senha."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        # Verificar se tem pelo menos uma letra maiúscula, minúscula e número
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v


class UserUpdate(DatametriaBaseModel):
    """Modelo para atualização de usuário."""
    
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None)
    role: Optional[UserRole] = Field(None)
    active: Optional[bool] = Field(None)
    
    @validator('email')
    def validate_email(cls, v):
        """Valida formato do email."""
        if v is not None:
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError('Invalid email format')
            return v.lower()
        return v


class UserResponse(UserBase, TimestampMixin):
    """Modelo de resposta de usuário."""
    
    id: int = Field(description="ID do usuário")


class UserListParams(PaginationParams, SortParams, FilterParams):
    """Parâmetros para listagem de usuários."""
    
    role: Optional[UserRole] = Field(None, description="Filtrar por role")


# Modelos de autenticação

class LoginRequest(DatametriaBaseModel):
    """Requisição de login."""
    
    email: str = Field(..., description="Email do usuário")
    password: str = Field(..., description="Senha do usuário")


class TokenResponse(DatametriaBaseModel):
    """Resposta de token."""
    
    access_token: str = Field(description="Token de acesso")
    token_type: str = Field("bearer", description="Tipo do token")
    expires_in: int = Field(description="Tempo de expiração em segundos")
    refresh_token: Optional[str] = Field(None, description="Token de refresh")


class RefreshTokenRequest(DatametriaBaseModel):
    """Requisição de refresh token."""
    
    refresh_token: str = Field(..., description="Token de refresh")


# Modelos de configuração

class APIConfigResponse(DatametriaBaseModel):
    """Resposta de configuração da API."""
    
    title: str = Field(description="Título da API")
    version: str = Field(description="Versão da API")
    description: str = Field(description="Descrição da API")
    environment: str = Field(description="Ambiente (dev/staging/prod)")
    features: Dict[str, bool] = Field(description="Features habilitadas")


# Utilitários para criação de modelos

def create_list_response_model(item_model: type, name: str = None) -> type:
    """
    Cria modelo de resposta de lista para um tipo específico.
    
    Args:
        item_model: Modelo do item
        name: Nome do modelo (opcional)
        
    Returns:
        type: Classe do modelo de lista
    """
    if name is None:
        name = f"{item_model.__name__}ListResponse"
    
    return type(name, (PaginatedResponse[item_model],), {})


def create_filter_params_model(base_filters: Dict[str, Any], name: str = None) -> type:
    """
    Cria modelo de parâmetros de filtro customizado.
    
    Args:
        base_filters: Dicionário com filtros base
        name: Nome do modelo (opcional)
        
    Returns:
        type: Classe do modelo de filtros
    """
    if name is None:
        name = "CustomFilterParams"
    
    # Combinar com filtros padrão
    fields = {
        **FilterParams.__fields__,
        **PaginationParams.__fields__,
        **SortParams.__fields__,
        **base_filters
    }
    
    return type(name, (DatametriaBaseModel,), {"__annotations__": fields})
