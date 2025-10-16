"""
🔧 DatametriaAPI - Classe Principal FastAPI Enterprise

Classe FastAPI customizada com integração completa aos componentes DATAMETRIA.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import Optional, Dict, Any, List
import structlog

from datametria_common.core import BaseConfig
from datametria_common.security.security_manager import SecurityManager
from datametria_common.security.config import setup_logging

logger = structlog.get_logger(__name__)


class DatametriaAPI(FastAPI):
    """
    Classe FastAPI customizada com recursos enterprise DATAMETRIA.
    
    Integra automaticamente:
    - Logging estruturado
    - Security manager
    - Configuration management
    - Health checks
    - Metrics collection
    """
    
    def __init__(
        self,
        title: str = "DATAMETRIA API",
        description: str = "Enterprise API built with DATAMETRIA Common Libraries",
        version: str = "1.0.0",
        docs_url: str = "/docs",
        redoc_url: str = "/redoc",
        openapi_url: str = "/openapi.json",
        enable_security: bool = True,
        enable_logging: bool = True,
        enable_metrics: bool = True,
        **kwargs
    ):
        """
        Inicializa DatametriaAPI com configurações enterprise.
        
        Args:
            title: Título da API
            description: Descrição da API
            version: Versão da API
            docs_url: URL da documentação Swagger
            redoc_url: URL da documentação ReDoc
            openapi_url: URL do schema OpenAPI
            enable_security: Habilitar security manager
            enable_logging: Habilitar logging estruturado
            enable_metrics: Habilitar coleta de métricas
            **kwargs: Argumentos adicionais para FastAPI
        """
        super().__init__(
            title=title,
            description=description,
            version=version,
            docs_url=docs_url,
            redoc_url=redoc_url,
            openapi_url=openapi_url,
            **kwargs
        )
        
        # Configurações DATAMETRIA
        self.config = BaseConfig()
        self.security_manager = None
        self.enable_security = enable_security
        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics
        
        # Setup inicial
        self._setup_logging()
        self._setup_security()
        self._setup_health_checks()
        
        logger.info(
            "DatametriaAPI initialized",
            title=title,
            version=version,
            security_enabled=enable_security,
            logging_enabled=enable_logging,
            metrics_enabled=enable_metrics
        )
    
    def _setup_logging(self) -> None:
        """Configura logging estruturado DATAMETRIA."""
        if self.enable_logging:
            setup_logging(
                level=self.config.LOG_LEVEL,
                format=self.config.LOG_FORMAT,
                enable_json=True
            )
            logger.info("Structured logging configured")
    
    def _setup_security(self) -> None:
        """Configura security manager DATAMETRIA."""
        if self.enable_security:
            try:
                self.security_manager = SecurityManager()
                logger.info("Security manager initialized")
            except Exception as e:
                logger.warning("Failed to initialize security manager", error=str(e))
    
    def _setup_health_checks(self) -> None:
        """Configura health checks padrão."""
        @self.get("/health", tags=["Health"])
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": self.title,
                "version": self.version,
                "timestamp": self.config.get_current_timestamp()
            }
        
        @self.get("/health/detailed", tags=["Health"])
        async def detailed_health_check():
            """Detailed health check with component status."""
            health_status = {
                "status": "healthy",
                "service": self.title,
                "version": self.version,
                "timestamp": self.config.get_current_timestamp(),
                "components": {
                    "api": "healthy",
                    "logging": "healthy" if self.enable_logging else "disabled",
                    "security": "healthy" if self.security_manager else "disabled",
                    "metrics": "healthy" if self.enable_metrics else "disabled"
                }
            }
            
            # Verificar componentes opcionais
            try:
                from datametria_common.database import get_database_url
                health_status["components"]["database"] = "configured"
            except:
                health_status["components"]["database"] = "not_configured"
            
            try:
                from datametria_common.utilities.vault_manager import VaultManager
                health_status["components"]["vault"] = "available"
            except:
                health_status["components"]["vault"] = "not_available"
            
            return health_status
    
    def add_datametria_middleware(
        self,
        enable_cors: bool = True,
        enable_compression: bool = True,
        cors_origins: List[str] = None,
        compression_minimum_size: int = 1000
    ) -> None:
        """
        Adiciona middleware stack DATAMETRIA.
        
        Args:
            enable_cors: Habilitar CORS middleware
            enable_compression: Habilitar compressão GZIP
            cors_origins: Lista de origens permitidas para CORS
            compression_minimum_size: Tamanho mínimo para compressão
        """
        if enable_compression:
            self.add_middleware(
                GZipMiddleware,
                minimum_size=compression_minimum_size
            )
            logger.info("Compression middleware added", minimum_size=compression_minimum_size)
        
        if enable_cors:
            origins = cors_origins or ["*"]
            self.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )
            logger.info("CORS middleware added", origins=origins)
    
    def get_security_manager(self) -> Optional[SecurityManager]:
        """Retorna o security manager configurado."""
        return self.security_manager
    
    def get_config(self) -> BaseConfig:
        """Retorna a configuração DATAMETRIA."""
        return self.config
