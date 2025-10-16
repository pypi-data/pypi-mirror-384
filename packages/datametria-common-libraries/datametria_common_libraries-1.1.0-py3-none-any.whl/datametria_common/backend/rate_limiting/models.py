"""
🚦 Rate Limiting Models - DATAMETRIA Rate Limiting

Modelos para configuração e métricas de rate limiting.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from datametria_common.backend.api_framework.models import DatametriaBaseModel


class RateLimitStrategy(str, Enum):
    """Estratégias de rate limiting."""
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"


class RateLimit(DatametriaBaseModel):
    """Configuração de rate limit."""
    
    requests: int = Field(..., gt=0, description="Número de requests permitidos")
    window: int = Field(..., gt=0, description="Janela de tempo em segundos")
    strategy: RateLimitStrategy = Field(RateLimitStrategy.SLIDING_WINDOW, description="Estratégia de rate limiting")
    burst_requests: Optional[int] = Field(None, description="Requests de burst permitidos")
    burst_window: Optional[int] = Field(None, description="Janela de burst em segundos")
    
    @validator('burst_requests')
    def validate_burst_requests(cls, v, values):
        """Valida burst requests."""
        if v is not None and v <= values.get('requests', 0):
            raise ValueError('Burst requests deve ser maior que requests normais')
        return v


class RateLimitConfig(DatametriaBaseModel):
    """Configuração completa de rate limiting."""
    
    enabled: bool = Field(True, description="Rate limiting habilitado")
    default_limits: Dict[str, RateLimit] = Field(..., description="Limites padrão")
    per_user_limits: Optional[Dict[str, RateLimit]] = Field(None, description="Limites por usuário")
    per_endpoint_limits: Optional[Dict[str, RateLimit]] = Field(None, description="Limites por endpoint")
    whitelist_ips: List[str] = Field(default_factory=list, description="IPs na whitelist")
    blacklist_ips: List[str] = Field(default_factory=list, description="IPs na blacklist")
    headers_enabled: bool = Field(True, description="Headers de rate limit habilitados")
    
    @validator('default_limits')
    def validate_default_limits(cls, v):
        """Valida limites padrão."""
        required_keys = ['global', 'authenticated', 'anonymous']
        for key in required_keys:
            if key not in v:
                raise ValueError(f'Limite padrão "{key}" é obrigatório')
        return v


class RateLimitResult(DatametriaBaseModel):
    """Resultado de verificação de rate limit."""
    
    allowed: bool = Field(..., description="Request permitido")
    remaining: int = Field(..., description="Requests restantes")
    limit: int = Field(..., description="Limite total")
    reset_time: datetime = Field(..., description="Tempo de reset")
    retry_after: Optional[int] = Field(None, description="Tempo para retry em segundos")
    strategy_used: RateLimitStrategy = Field(..., description="Estratégia utilizada")
    key: str = Field(..., description="Chave de rate limiting")
    
    @property
    def reset_timestamp(self) -> int:
        """Timestamp de reset."""
        return int(self.reset_time.timestamp())


class RateLimitMetrics(DatametriaBaseModel):
    """Métricas de rate limiting."""
    
    total_requests: int = Field(0, description="Total de requests")
    allowed_requests: int = Field(0, description="Requests permitidos")
    blocked_requests: int = Field(0, description="Requests bloqueados")
    unique_keys: int = Field(0, description="Chaves únicas")
    top_keys: List[Dict[str, Any]] = Field(default_factory=list, description="Top chaves por volume")
    blocked_ips: List[str] = Field(default_factory=list, description="IPs bloqueados")
    
    @property
    def block_rate(self) -> float:
        """Taxa de bloqueio."""
        if self.total_requests == 0:
            return 0.0
        return (self.blocked_requests / self.total_requests) * 100
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso."""
        return 100.0 - self.block_rate


class RateLimitRule(DatametriaBaseModel):
    """Regra de rate limiting."""
    
    name: str = Field(..., description="Nome da regra")
    pattern: str = Field(..., description="Padrão de matching (regex)")
    rate_limit: RateLimit = Field(..., description="Configuração de rate limit")
    priority: int = Field(0, description="Prioridade da regra")
    enabled: bool = Field(True, description="Regra habilitada")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Condições adicionais")
    
    class Config:
        """Configuração do modelo."""
        schema_extra = {
            "example": {
                "name": "API Heavy Endpoints",
                "pattern": "^/api/v1/(upload|export|report)",
                "rate_limit": {
                    "requests": 10,
                    "window": 60,
                    "strategy": "sliding_window"
                },
                "priority": 10,
                "enabled": True,
                "conditions": {
                    "methods": ["POST", "PUT"],
                    "user_roles": ["user", "guest"]
                }
            }
        }


class RateLimitStatus(DatametriaBaseModel):
    """Status atual de rate limiting para uma chave."""
    
    key: str = Field(..., description="Chave de rate limiting")
    current_requests: int = Field(..., description="Requests atuais na janela")
    limit: int = Field(..., description="Limite configurado")
    window_start: datetime = Field(..., description="Início da janela atual")
    window_end: datetime = Field(..., description="Fim da janela atual")
    is_blocked: bool = Field(..., description="Chave bloqueada")
    last_request: Optional[datetime] = Field(None, description="Última request")
    
    @property
    def usage_percentage(self) -> float:
        """Percentual de uso do limite."""
        if self.limit == 0:
            return 0.0
        return (self.current_requests / self.limit) * 100


class RateLimitAlert(DatametriaBaseModel):
    """Alerta de rate limiting."""
    
    alert_type: str = Field(..., description="Tipo do alerta")
    key: str = Field(..., description="Chave afetada")
    threshold: float = Field(..., description="Threshold atingido")
    current_value: float = Field(..., description="Valor atual")
    timestamp: datetime = Field(..., description="Timestamp do alerta")
    severity: str = Field(..., description="Severidade (low, medium, high, critical)")
    message: str = Field(..., description="Mensagem do alerta")
    
    class Config:
        """Configuração do modelo."""
        schema_extra = {
            "example": {
                "alert_type": "high_usage",
                "key": "user:123",
                "threshold": 80.0,
                "current_value": 85.5,
                "timestamp": "2025-01-08T10:00:00Z",
                "severity": "medium",
                "message": "User 123 atingiu 85.5% do limite de rate limiting"
            }
        }


class BurstConfig(DatametriaBaseModel):
    """Configuração de burst protection."""
    
    enabled: bool = Field(True, description="Burst protection habilitado")
    max_burst_requests: int = Field(..., gt=0, description="Máximo de requests em burst")
    burst_window: int = Field(..., gt=0, description="Janela de burst em segundos")
    recovery_time: int = Field(..., gt=0, description="Tempo de recuperação em segundos")
    penalty_multiplier: float = Field(1.5, gt=1.0, description="Multiplicador de penalidade")


class AdaptiveConfig(DatametriaBaseModel):
    """Configuração de rate limiting adaptativo."""
    
    enabled: bool = Field(False, description="Rate limiting adaptativo habilitado")
    base_limit: int = Field(..., gt=0, description="Limite base")
    max_limit: int = Field(..., gt=0, description="Limite máximo")
    min_limit: int = Field(..., gt=0, description="Limite mínimo")
    adjustment_factor: float = Field(0.1, gt=0, le=1, description="Fator de ajuste")
    monitoring_window: int = Field(300, gt=0, description="Janela de monitoramento em segundos")
    
    @validator('max_limit')
    def validate_max_limit(cls, v, values):
        """Valida limite máximo."""
        base_limit = values.get('base_limit', 0)
        if v <= base_limit:
            raise ValueError('Limite máximo deve ser maior que limite base')
        return v
    
    @validator('min_limit')
    def validate_min_limit(cls, v, values):
        """Valida limite mínimo."""
        base_limit = values.get('base_limit', 0)
        if v >= base_limit:
            raise ValueError('Limite mínimo deve ser menor que limite base')
        return v
