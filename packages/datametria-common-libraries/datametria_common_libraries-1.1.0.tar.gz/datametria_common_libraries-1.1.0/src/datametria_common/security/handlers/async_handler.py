"""
Async Log Handler - Handler Assíncrono para Alta Performance

Handler que processa logs em background thread com queue e batch processing.

Autor: DATAMETRIA Team
Versão: 2.0.0
"""

import time
from queue import Empty, Full, Queue
from threading import Event, Thread
from typing import Dict, List

from .base_handler import BaseLogHandler


class AsyncLogHandler(BaseLogHandler):
    """Handler assíncrono para alta performance.
    
    Processa logs em background thread usando queue, com batch processing
    e backpressure handling.
    
    Attributes:
        target_handler (BaseLogHandler): Handler alvo para processar logs
        queue_size (int): Tamanho máximo da queue
        batch_size (int): Tamanho do batch para processamento
        queue (Queue): Queue thread-safe para logs
        worker_thread (Thread): Thread de processamento
        metrics (Dict): Métricas de performance
        
    Example:
        >>> file_handler = FileLogHandler(file_path="/var/log/app.log")
        >>> async_handler = AsyncLogHandler(file_handler, queue_size=10000)
        >>> async_handler.handle(log_entry)  # Non-blocking
    """
    
    def __init__(
        self,
        target_handler: BaseLogHandler,
        queue_size: int = 10000,
        batch_size: int = 100,
        level: str = "INFO"
    ):
        """Inicializa handler assíncrono.
        
        Args:
            target_handler: Handler alvo
            queue_size: Tamanho da queue
            batch_size: Tamanho do batch
            level: Nível de log
        """
        super().__init__(level=level)
        self.target_handler = target_handler
        self.queue_size = queue_size
        self.batch_size = batch_size
        self.queue = Queue(maxsize=queue_size)
        self.running = True
        self.shutdown_event = Event()
        
        # Métricas
        self.metrics = {
            'total_logs': 0,
            'dropped_logs': 0,
            'batches_processed': 0,
            'total_processing_time': 0.0
        }
        
        # Iniciar worker thread
        self.worker_thread = Thread(target=self._worker, daemon=False)
        self.worker_thread.start()
    
    def should_handle(self, log_entry) -> bool:
        """Verifica se deve processar log."""
        return True
    
    def handle(self, log_entry) -> None:
        """Adiciona log à queue (non-blocking).
        
        Args:
            log_entry: Entrada de log
        """
        try:
            self.queue.put_nowait(log_entry)
            self.metrics['total_logs'] += 1
        except Full:
            # Backpressure: log descartado
            self.metrics['dropped_logs'] += 1
    
    def _worker(self) -> None:
        """Worker thread para processar logs em batch."""
        batch = []
        
        while self.running or not self.queue.empty():
            try:
                # Tentar obter log da queue
                log_entry = self.queue.get(timeout=0.1)
                batch.append(log_entry)
                
                # Processar batch quando atingir tamanho
                if len(batch) >= self.batch_size:
                    self._process_batch(batch)
                    batch = []
                    
            except Empty:
                # Queue vazia, processar batch pendente
                if batch:
                    self._process_batch(batch)
                    batch = []
        
        # Processar logs restantes
        if batch:
            self._process_batch(batch)
        
        self.shutdown_event.set()
    
    def _process_batch(self, batch: List) -> None:
        """Processa batch de logs.
        
        Args:
            batch: Lista de logs
        """
        start_time = time.time()
        
        for log_entry in batch:
            self.target_handler.handle(log_entry)
        
        self.target_handler.flush()
        
        processing_time = time.time() - start_time
        self.metrics['batches_processed'] += 1
        self.metrics['total_processing_time'] += processing_time
    
    def flush(self) -> None:
        """Força processamento de logs pendentes."""
        # Aguardar queue esvaziar
        self.queue.join()
        self.target_handler.flush()
    
    def close(self) -> None:
        """Fecha handler e aguarda processamento completo."""
        self.running = False
        
        # Aguardar worker thread finalizar
        self.worker_thread.join(timeout=5.0)
        
        # Aguardar shutdown
        self.shutdown_event.wait(timeout=5.0)
        
        # Fechar handler alvo
        self.target_handler.close()
    
    def get_metrics(self) -> Dict:
        """Retorna métricas de performance.
        
        Returns:
            Dict com métricas
        """
        metrics = self.metrics.copy()
        
        # Calcular métricas derivadas
        if metrics['batches_processed'] > 0:
            metrics['avg_batch_time'] = (
                metrics['total_processing_time'] / metrics['batches_processed']
            )
        else:
            metrics['avg_batch_time'] = 0.0
        
        metrics['queue_size'] = self.queue.qsize()
        metrics['drop_rate'] = (
            metrics['dropped_logs'] / max(metrics['total_logs'], 1)
        )
        
        return metrics
