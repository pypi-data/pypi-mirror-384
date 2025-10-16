"""
Database Log Handler - Persistência em Banco de Dados

Suporta PostgreSQL, Oracle e SQL Server com batch insert e retry logic.

Autor: DATAMETRIA Team
Versão: 2.0.0
Compliance: LGPD/GDPR
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    JSON,
)
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from .base_handler import BaseLogHandler, LogEntry, LogLevel

Base = declarative_base()


class LogEntryModel(Base):
    """Modelo SQLAlchemy para log entries."""
    
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    logger_name = Column(String(100), nullable=False, index=True)
    module = Column(String(200))
    function = Column(String(200))
    line_number = Column(Integer)
    user_id = Column(String(100), index=True)
    session_id = Column(String(100), index=True)
    request_id = Column(String(100), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    additional_data = Column(JSON)


class DatabaseLogHandler(BaseLogHandler):
    """Handler para persistência de logs em banco de dados.
    
    Suporta PostgreSQL, Oracle e SQL Server com:
    - Batch insert para performance
    - Retry logic para resiliência
    - Connection pooling
    - Auto-criação de schema
    
    Attributes:
        connection_string (str): String de conexão SQLAlchemy
        batch_size (int): Tamanho do batch para insert
        buffer (List[LogEntry]): Buffer de logs pendentes
        
    Example:
        >>> handler = DatabaseLogHandler(
        ...     connection_string="postgresql://user:pass@localhost/logs",
        ...     batch_size=100,
        ...     level=LogLevel.INFO
        ... )
        >>> handler.handle(log_entry)
    """
    
    def __init__(
        self,
        connection_string: str,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        pool_size: int = 5,
        max_overflow: int = 10,
        **config
    ):
        """Inicializa database handler.
        
        Args:
            connection_string (str): SQLAlchemy connection string
            batch_size (int): Número de logs para batch insert
            max_retries (int): Máximo de tentativas em caso de falha
            retry_delay (float): Delay entre retries em segundos
            pool_size (int): Tamanho do connection pool
            max_overflow (int): Máximo de conexões extras
            **config: Configurações adicionais
        """
        super().__init__(**config)
        self.connection_string = connection_string
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.buffer: List[LogEntry] = []
        
        # Criar engine com connection pooling
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verifica conexão antes de usar
        )
        
        # Criar session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Criar tabelas
        self._setup_database()
    
    def _setup_database(self) -> None:
        """Cria tabelas e índices no banco de dados."""
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            import sys
            sys.stderr.write(f"Database setup error: {e}\n")
    
    def handle(self, log_entry: LogEntry) -> None:
        """Adiciona log ao buffer e persiste em batch.
        
        Args:
            log_entry (LogEntry): Entrada de log a processar
        """
        if not self.should_handle(log_entry):
            return
        
        self.buffer.append(log_entry)
        
        if len(self.buffer) >= self.batch_size:
            self.flush()
    
    def flush(self) -> None:
        """Persiste logs em batch com retry logic."""
        if not self.buffer:
            return
        
        for attempt in range(self.max_retries):
            try:
                self._persist_batch()
                self.buffer.clear()
                return
            except OperationalError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    import sys
                    sys.stderr.write(f"Database flush failed after {self.max_retries} attempts: {e}\n")
                    self.buffer.clear()
            except Exception as e:
                import sys
                sys.stderr.write(f"Database flush error: {e}\n")
                self.buffer.clear()
                return
    
    def _persist_batch(self) -> None:
        """Persiste batch de logs no banco."""
        session = self.SessionLocal()
        
        try:
            # Converter LogEntry para LogEntryModel
            models = []
            for log_entry in self.buffer:
                model = LogEntryModel(
                    timestamp=datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00')),
                    level=log_entry.level,
                    event_type=log_entry.event_type,
                    message=log_entry.message,
                    logger_name=log_entry.logger_name,
                    module=log_entry.module,
                    function=log_entry.function,
                    line_number=log_entry.line_number,
                    user_id=log_entry.user_id,
                    session_id=log_entry.session_id,
                    request_id=log_entry.request_id,
                    ip_address=log_entry.ip_address,
                    user_agent=log_entry.user_agent,
                    additional_data=log_entry.additional_data,
                )
                models.append(model)
            
            # Batch insert
            session.bulk_save_objects(models)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def close(self) -> None:
        """Fecha handler e persiste logs pendentes."""
        self._closed = True
        self.flush()
        
        # Fechar engine
        if self.engine:
            self.engine.dispose()


class LogQueryService:
    """Serviço para consulta de logs no banco de dados.
    
    Fornece interface para buscar e analisar logs históricos.
    
    Example:
        >>> query_service = LogQueryService(connection_string)
        >>> logs = query_service.search_logs(
        ...     level="ERROR",
        ...     start_time=datetime(2025, 1, 1),
        ...     limit=100
        ... )
    """
    
    def __init__(self, connection_string: str):
        """Inicializa query service.
        
        Args:
            connection_string (str): SQLAlchemy connection string
        """
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def search_logs(
        self,
        logger_name: Optional[str] = None,
        level: Optional[str] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Busca logs com filtros.
        
        Args:
            logger_name (Optional[str]): Filtrar por nome do logger
            level (Optional[str]): Filtrar por nível de log
            event_type (Optional[str]): Filtrar por tipo de evento
            user_id (Optional[str]): Filtrar por ID do usuário
            request_id (Optional[str]): Filtrar por ID da requisição
            start_time (Optional[datetime]): Data/hora inicial
            end_time (Optional[datetime]): Data/hora final
            limit (int): Máximo de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de logs encontrados
        """
        session = self.SessionLocal()
        
        try:
            query = session.query(LogEntryModel)
            
            if logger_name:
                query = query.filter(LogEntryModel.logger_name == logger_name)
            
            if level:
                query = query.filter(LogEntryModel.level == level)
            
            if event_type:
                query = query.filter(LogEntryModel.event_type == event_type)
            
            if user_id:
                query = query.filter(LogEntryModel.user_id == user_id)
            
            if request_id:
                query = query.filter(LogEntryModel.request_id == request_id)
            
            if start_time:
                query = query.filter(LogEntryModel.timestamp >= start_time)
            
            if end_time:
                query = query.filter(LogEntryModel.timestamp <= end_time)
            
            # Ordenar por timestamp desc
            query = query.order_by(LogEntryModel.timestamp.desc())
            
            # Aplicar limit
            results = query.limit(limit).all()
            
            # Converter para dict
            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "level": r.level,
                    "event_type": r.event_type,
                    "message": r.message,
                    "logger_name": r.logger_name,
                    "module": r.module,
                    "function": r.function,
                    "line_number": r.line_number,
                    "user_id": r.user_id,
                    "session_id": r.session_id,
                    "request_id": r.request_id,
                    "ip_address": r.ip_address,
                    "additional_data": r.additional_data,
                }
                for r in results
            ]
            
        finally:
            session.close()
    
    def count_logs(
        self,
        logger_name: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Conta logs com filtros.
        
        Args:
            logger_name (Optional[str]): Filtrar por nome do logger
            level (Optional[str]): Filtrar por nível de log
            start_time (Optional[datetime]): Data/hora inicial
            end_time (Optional[datetime]): Data/hora final
            
        Returns:
            int: Número de logs encontrados
        """
        session = self.SessionLocal()
        
        try:
            query = session.query(LogEntryModel)
            
            if logger_name:
                query = query.filter(LogEntryModel.logger_name == logger_name)
            
            if level:
                query = query.filter(LogEntryModel.level == level)
            
            if start_time:
                query = query.filter(LogEntryModel.timestamp >= start_time)
            
            if end_time:
                query = query.filter(LogEntryModel.timestamp <= end_time)
            
            return query.count()
            
        finally:
            session.close()
