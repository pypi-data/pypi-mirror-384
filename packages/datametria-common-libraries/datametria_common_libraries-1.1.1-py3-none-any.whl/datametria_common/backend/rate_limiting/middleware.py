"""
🚦 Rate Limit Middleware - DATAMETRIA Rate Limiting

Middleware FastAPI para rate limiting automático integrado aos componentes DATAMETRIA.
"""

from typing import Callable, Optional, Dict, Any
import time
import structlog
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .rate_limiter import RateLimiter
from .models import RateLimitConfig

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware FastAPI para rate limiting automático.
    
    Integra com sistema de autenticação e logging DATAMETRIA.
    """
    
    def __init__(
        self,
        app,
        rate_limiter: Optional[RateLimiter] = None,
        config: Optional[RateLimitConfig] = None,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        """
        Inicializa middleware de rate limiting.
        
        Args:
            app: Aplicação FastAPI
            rate_limiter: Instância do RateLimiter
            config: Configuração de rate limiting
            key_func: Função para gerar chave de rate limiting
        """
        super().__init__(app)
        
        self.rate_limiter = rate_limiter or RateLimiter(config=config)
        self.key_func = key_func or self._default_key_func
        
        logger.info(
            "RateLimitMiddleware initialized",
            enabled=self.rate_limiter.config.enabled
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa request com rate limiting.
        
        Args:
            request: Request FastAPI
            call_next: Próximo middleware/handler
            
        Returns:
            Response: Resposta processada
        """
        start_time = time.time()
        
        try:
            # Gerar chave de rate limiting
            key = self.key_func(request)
            
            # Extrair informações do usuário (se autenticado)
            user_id = getattr(request.state, 'user_id', None)
            user_role = getattr(request.state, 'user_role', None)
            
            # Verificar rate limit
            allowed, info = self.rate_limiter.is_allowed(
                key=key,
                endpoint=str(request.url.path),
                user_id=user_id,
                user_role=user_role
            )
            
            if not allowed:
                # Rate limit excedido
                logger.warning(
                    "Rate limit exceeded",
                    key=key,
                    endpoint=request.url.path,
                    user_id=user_id,
                    info=info
                )
                
                # Criar resposta de rate limit
                response = self._create_rate_limit_response(info)
                
                # Adicionar headers de rate limiting
                if self.rate_limiter.config.headers_enabled:
                    self._add_rate_limit_headers(response, info)
                
                return response
            
            # Processar request normalmente
            response = await call_next(request)
            
            # Adicionar headers de rate limiting na resposta
            if self.rate_limiter.config.headers_enabled:
                self._add_rate_limit_headers(response, info)
            
            # Log de sucesso
            processing_time = time.time() - start_time
            logger.info(
                "Request processed with rate limiting",
                key=key,
                endpoint=request.url.path,
                user_id=user_id,
                remaining=info.get('remaining'),
                processing_time=processing_time
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Rate limiting middleware error",
                endpoint=request.url.path,
                error=str(e)
            )
            
            # Continuar processamento em caso de erro
            return await call_next(request)
    
    def _default_key_func(self, request: Request) -> str:
        """
        Função padrão para gerar chave de rate limiting.
        
        Args:
            request: Request FastAPI
            
        Returns:
            str: Chave de rate limiting
        """
        # Tentar obter IP real do cliente
        client_ip = self._get_client_ip(request)
        
        # Se usuário autenticado, usar ID do usuário
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Usar IP do cliente
        return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Obtém IP real do cliente considerando proxies.
        
        Args:
            request: Request FastAPI
            
        Returns:
            str: IP do cliente
        """
        # Headers comuns de proxy
        forwarded_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'CF-Connecting-IP',  # Cloudflare
            'X-Client-IP'
        ]
        
        for header in forwarded_headers:
            if header in request.headers:
                ip = request.headers[header].split(',')[0].strip()
                if ip:
                    return ip
        
        # Fallback para IP direto
        return request.client.host if request.client else "unknown"
    
    def _create_rate_limit_response(self, info: Dict[str, Any]) -> Response:
        """
        Cria resposta de rate limit excedido.
        
        Args:
            info: Informações do rate limiting
            
        Returns:
            Response: Resposta HTTP 429
        """
        error_detail = {
            "error": "rate_limit_exceeded",
            "message": "Too many requests",
            "retry_after": info.get('retry_after', 60),
            "limit": info.get('limit'),
            "remaining": info.get('remaining', 0),
            "reset_time": info.get('reset_time')
        }
        
        response = Response(
            content=str(error_detail),
            status_code=429,
            media_type="application/json"
        )
        
        return response
    
    def _add_rate_limit_headers(self, response: Response, info: Dict[str, Any]) -> None:
        """
        Adiciona headers de rate limiting na resposta.
        
        Args:
            response: Resposta HTTP
            info: Informações do rate limiting
        """
        headers = {
            'X-RateLimit-Limit': str(info.get('limit', 0)),
            'X-RateLimit-Remaining': str(info.get('remaining', 0)),
            'X-RateLimit-Reset': str(info.get('reset_time', 0))
        }
        
        # Adicionar retry-after se rate limit excedido
        if not info.get('allowed', True):
            headers['Retry-After'] = str(info.get('retry_after', 60))
        
        for header, value in headers.items():
            response.headers[header] = value


def create_rate_limit_middleware(
    rate_limiter: Optional[RateLimiter] = None,
    config: Optional[RateLimitConfig] = None,
    key_func: Optional[Callable[[Request], str]] = None
) -> Callable:
    """
    Factory function para criar middleware de rate limiting.
    
    Args:
        rate_limiter: Instância do RateLimiter
        config: Configuração de rate limiting
        key_func: Função para gerar chave
        
    Returns:
        Callable: Middleware configurado
    """
    def middleware_factory(app):
        return RateLimitMiddleware(
            app=app,
            rate_limiter=rate_limiter,
            config=config,
            key_func=key_func
        )
    
    return middleware_factory
