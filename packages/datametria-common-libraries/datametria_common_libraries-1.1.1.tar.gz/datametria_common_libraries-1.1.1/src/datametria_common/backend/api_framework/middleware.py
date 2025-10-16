"""
🔧 Middleware Stack - DATAMETRIA API Framework

Stack de middleware enterprise com integração aos componentes DATAMETRIA.
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, List, Optional
import time
import structlog

from datametria_common.security.security_manager import SecurityManager

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging estruturado de requests/responses."""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa request com logging estruturado."""
        start_time = time.time()
        
        # Log request
        if self.log_requests:
            logger.info(
                "Request started",
                method=request.method,
                url=str(request.url),
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        
        # Processar request
        response = await call_next(request)
        
        # Calcular tempo de processamento
        process_time = time.time() - start_time
        
        # Log response
        if self.log_responses:
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=f"{process_time:.4f}s"
            )
        
        # Adicionar header de tempo de processamento
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware para headers de segurança DATAMETRIA."""
    
    def __init__(self, app, security_manager: Optional[SecurityManager] = None):
        super().__init__(app)
        self.security_manager = security_manager or SecurityManager()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Adiciona headers de segurança."""
        response = await call_next(request)
        
        # Headers de segurança padrão
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "X-Powered-By": "DATAMETRIA-API-Framework"
        }
        
        # Aplicar headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class CompressionMiddleware(GZipMiddleware):
    """Middleware de compressão customizado DATAMETRIA."""
    
    def __init__(self, app, minimum_size: int = 1000, exclude_paths: List[str] = None):
        super().__init__(app, minimum_size=minimum_size)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Aplica compressão com exclusões configuráveis."""
        # Verificar se path deve ser excluído
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        return await super().dispatch(request, call_next)


class CORSMiddleware(FastAPICORSMiddleware):
    """Middleware CORS customizado DATAMETRIA."""
    
    def __init__(
        self,
        app,
        allow_origins: List[str] = None,
        allow_credentials: bool = True,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        expose_headers: List[str] = None
    ):
        # Configurações padrão DATAMETRIA
        origins = allow_origins or ["*"]
        methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        headers = allow_headers or ["*"]
        expose_headers = expose_headers or ["X-Process-Time", "X-Request-ID"]
        
        super().__init__(
            app,
            allow_origins=origins,
            allow_credentials=allow_credentials,
            allow_methods=methods,
            allow_headers=headers,
            expose_headers=expose_headers
        )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para coleta de métricas."""
    
    def __init__(self, app, enable_metrics: bool = True):
        super().__init__(app)
        self.enable_metrics = enable_metrics
        self.request_count = 0
        self.response_times = []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Coleta métricas de performance."""
        if not self.enable_metrics:
            return await call_next(request)
        
        start_time = time.time()
        
        # Incrementar contador
        self.request_count += 1
        
        # Processar request
        response = await call_next(request)
        
        # Calcular tempo de resposta
        response_time = time.time() - start_time
        self.response_times.append(response_time)
        
        # Manter apenas últimas 1000 medições
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        # Adicionar métricas ao header
        response.headers["X-Request-Count"] = str(self.request_count)
        
        return response
    
    def get_metrics(self) -> dict:
        """Retorna métricas coletadas."""
        if not self.response_times:
            return {"request_count": self.request_count, "avg_response_time": 0}
        
        avg_response_time = sum(self.response_times) / len(self.response_times)
        
        return {
            "request_count": self.request_count,
            "avg_response_time": avg_response_time,
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times)
        }


def setup_middleware(
    app,
    enable_cors: bool = True,
    enable_logging: bool = True,
    enable_security: bool = True,
    enable_compression: bool = True,
    enable_metrics: bool = True,
    cors_origins: List[str] = None,
    compression_minimum_size: int = 1000,
    security_manager: Optional[SecurityManager] = None
) -> None:
    """
    Configura stack completo de middleware DATAMETRIA.
    
    Args:
        app: Instância FastAPI
        enable_cors: Habilitar CORS
        enable_logging: Habilitar logging
        enable_security: Habilitar headers de segurança
        enable_compression: Habilitar compressão
        enable_metrics: Habilitar coleta de métricas
        cors_origins: Origens permitidas para CORS
        compression_minimum_size: Tamanho mínimo para compressão
        security_manager: Instância do SecurityManager
    """
    # Ordem importante: do mais externo para o mais interno
    
    if enable_metrics:
        metrics_middleware = MetricsMiddleware(app, enable_metrics=True)
        app.add_middleware(MetricsMiddleware, enable_metrics=True)
        app.state.metrics_middleware = metrics_middleware
        logger.info("Metrics middleware added")
    
    if enable_logging:
        app.add_middleware(LoggingMiddleware, log_requests=True, log_responses=True)
        logger.info("Logging middleware added")
    
    if enable_security:
        app.add_middleware(SecurityMiddleware, security_manager=security_manager)
        logger.info("Security middleware added")
    
    if enable_compression:
        app.add_middleware(
            CompressionMiddleware,
            minimum_size=compression_minimum_size
        )
        logger.info("Compression middleware added", minimum_size=compression_minimum_size)
    
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        logger.info("CORS middleware added", origins=cors_origins or ["*"])
    
    logger.info("Middleware stack configured successfully")
