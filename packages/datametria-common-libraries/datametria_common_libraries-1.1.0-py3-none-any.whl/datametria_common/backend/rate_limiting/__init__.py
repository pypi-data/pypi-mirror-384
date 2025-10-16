"""
🚦 Rate Limiting - DATAMETRIA Common Libraries

Sistema de rate limiting enterprise com múltiplas estratégias e integração completa.

Features:
    - Sliding Window: Rate limiting baseado em janela deslizante
    - Token Bucket: Controle de burst com refill automático
    - Fixed Window: Janela fixa para casos simples
    - Per-User Limits: Quotas individuais por usuário
    - Redis Backend: Rate limiting distribuído
    - Custom Rules: Regras flexíveis por endpoint
    - Real-time Monitoring: Métricas em tempo real

Components:
    rate_limiter: Gerenciador principal de rate limiting
    strategies: Diferentes estratégias (sliding window, token bucket)
    middleware: Middleware FastAPI integrado
    decorators: Decorators para endpoints específicos
    models: Modelos para configuração e métricas

Integration:
    - API Framework: Middleware e decorators integrados
    - Authentication: Rate limiting por usuário autenticado
    - Logging Enterprise: Auditoria de rate limiting
    - Configuration: Configurações centralizadas
    - Redis Cache: Backend distribuído

Author: DATAMETRIA Enterprise Team
Version: 1.0.0
"""

from .rate_limiter import RateLimiter
from .strategies import (
    SlidingWindowStrategy,
    TokenBucketStrategy,
    FixedWindowStrategy
)
from .middleware import RateLimitMiddleware
from .decorators import rate_limit, adaptive_rate_limit
from .models import (
    RateLimit,
    RateLimitConfig,
    RateLimitResult,
    RateLimitMetrics
)

__all__ = [
    # Core
    "RateLimiter",
    
    # Strategies
    "SlidingWindowStrategy",
    "TokenBucketStrategy", 
    "FixedWindowStrategy",
    
    # Middleware
    "RateLimitMiddleware",
    
    # Decorators
    "rate_limit",
    "adaptive_rate_limit",
    
    # Models
    "RateLimit",
    "RateLimitConfig",
    "RateLimitResult",
    "RateLimitMetrics"
]
