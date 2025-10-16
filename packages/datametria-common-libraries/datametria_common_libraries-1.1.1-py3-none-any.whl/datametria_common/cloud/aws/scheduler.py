"""
⏰ Scheduler Manager - DATAMETRIA AWS Services

Gerenciador EventBridge Scheduler integrado aos componentes DATAMETRIA.
"""

import json
import time
from typing import Dict, Any, Optional, List
import boto3
import structlog
from botocore.exceptions import ClientError

from .config import AWSConfig
from .models import ScheduleConfig, ScheduleResult

logger = structlog.get_logger(__name__)


class SchedulerManager:
    """
    Gerenciador EventBridge Scheduler DATAMETRIA.
    
    Integra task scheduling com logging e monitoramento.
    """
    
    def __init__(self, session: boto3.Session, config: AWSConfig):
        """
        Inicializa SchedulerManager.
        
        Args:
            session: Sessão boto3
            config: Configuração AWS
        """
        self.session = session
        self.config = config
        self.client = session.client('scheduler')
        
        logger.info(
            "SchedulerManager initialized",
            region=config.region,
            default_timezone=config.scheduler_default_timezone,
            default_role=config.scheduler_default_role
        )
    
    async def create_schedule(self, schedule_config: ScheduleConfig) -> ScheduleResult:
        """
        Criar schedule.
        
        Args:
            schedule_config: Configuração do schedule
            
        Returns:
            ScheduleResult: Resultado da operação
        """
        try:
            # Preparar parâmetros
            params = {
                'Name': schedule_config.name,
                'ScheduleExpression': schedule_config.schedule_expression,
                'Target': {
                    'Arn': schedule_config.target_arn,
                    'RoleArn': schedule_config.role_arn or self.config.scheduler_default_role
                },
                'FlexibleTimeWindow': {
                    'Mode': schedule_config.flexible_time_window_mode
                }
            }
            
            # Adicionar input se fornecido
            if schedule_config.input_data:
                params['Target']['Input'] = json.dumps(schedule_config.input_data)
            
            # Adicionar descrição
            if schedule_config.description:
                params['Description'] = schedule_config.description
            else:
                params['Description'] = f"Schedule created by DATAMETRIA - {schedule_config.name}"
            
            # Adicionar timezone
            if schedule_config.timezone:
                params['ScheduleExpressionTimezone'] = schedule_config.timezone
            else:
                params['ScheduleExpressionTimezone'] = self.config.scheduler_default_timezone
            
            # Configurar flexible time window
            if schedule_config.flexible_time_window_mode == 'FLEXIBLE':
                if schedule_config.maximum_window_minutes:
                    params['FlexibleTimeWindow']['MaximumWindowInMinutes'] = schedule_config.maximum_window_minutes
                else:
                    params['FlexibleTimeWindow']['MaximumWindowInMinutes'] = 60  # Default 1 hour
            
            # Criar schedule
            response = self.client.create_schedule(**params)
            
            logger.info(
                "EventBridge Schedule created",
                name=schedule_config.name,
                arn=response['ScheduleArn'],
                expression=schedule_config.schedule_expression,
                target=schedule_config.target_arn
            )
            
            return ScheduleResult(
                success=True,
                operation="create_schedule",
                schedule_arn=response['ScheduleArn'],
                metadata={
                    'name': schedule_config.name,
                    'expression': schedule_config.schedule_expression,
                    'target_arn': schedule_config.target_arn,
                    'timezone': params.get('ScheduleExpressionTimezone')
                }
            )
            
        except ClientError as e:
            logger.error(
                "EventBridge Scheduler create_schedule failed",
                name=schedule_config.name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return ScheduleResult(
                success=False,
                operation="create_schedule",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    async def update_schedule(self, schedule_name: str, schedule_config: ScheduleConfig) -> ScheduleResult:
        """
        Atualizar schedule existente.
        
        Args:
            schedule_name: Nome do schedule
            schedule_config: Nova configuração
            
        Returns:
            ScheduleResult: Resultado da operação
        """
        try:
            # Preparar parâmetros de atualização
            params = {
                'Name': schedule_name,
                'ScheduleExpression': schedule_config.schedule_expression,
                'Target': {
                    'Arn': schedule_config.target_arn,
                    'RoleArn': schedule_config.role_arn or self.config.scheduler_default_role
                },
                'FlexibleTimeWindow': {
                    'Mode': schedule_config.flexible_time_window_mode
                }
            }
            
            # Adicionar configurações opcionais
            if schedule_config.input_data:
                params['Target']['Input'] = json.dumps(schedule_config.input_data)
            
            if schedule_config.description:
                params['Description'] = schedule_config.description
            
            if schedule_config.timezone:
                params['ScheduleExpressionTimezone'] = schedule_config.timezone
            
            if schedule_config.flexible_time_window_mode == 'FLEXIBLE':
                params['FlexibleTimeWindow']['MaximumWindowInMinutes'] = (
                    schedule_config.maximum_window_minutes or 60
                )
            
            # Atualizar schedule
            response = self.client.update_schedule(**params)
            
            logger.info(
                "EventBridge Schedule updated",
                name=schedule_name,
                expression=schedule_config.schedule_expression
            )
            
            return ScheduleResult(
                success=True,
                operation="update_schedule",
                metadata={
                    'name': schedule_name,
                    'expression': schedule_config.schedule_expression
                }
            )
            
        except ClientError as e:
            logger.error(
                "EventBridge Scheduler update_schedule failed",
                name=schedule_name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return ScheduleResult(
                success=False,
                operation="update_schedule",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    def get_schedule(self, schedule_name: str) -> Optional[Dict[str, Any]]:
        """
        Obter detalhes de um schedule.
        
        Args:
            schedule_name: Nome do schedule
            
        Returns:
            Dict: Detalhes do schedule ou None
        """
        try:
            response = self.client.get_schedule(Name=schedule_name)
            
            logger.info(
                "EventBridge Schedule retrieved",
                name=schedule_name,
                state=response.get('State', 'UNKNOWN')
            )
            
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning("Schedule not found", name=schedule_name)
                return None
            else:
                logger.error(
                    "Failed to get schedule",
                    name=schedule_name,
                    error=str(e)
                )
                return None
    
    def list_schedules(self, name_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar schedules.
        
        Args:
            name_prefix: Prefixo para filtrar schedules
            
        Returns:
            List: Lista de schedules
        """
        try:
            params = {}
            if name_prefix:
                params['NamePrefix'] = name_prefix
            
            response = self.client.list_schedules(**params)
            schedules = response.get('Schedules', [])
            
            logger.info(
                "EventBridge Schedules listed",
                count=len(schedules),
                name_prefix=name_prefix
            )
            
            return schedules
            
        except Exception as e:
            logger.error("Failed to list schedules", error=str(e))
            return []
    
    def delete_schedule(self, schedule_name: str) -> bool:
        """
        Deletar schedule.
        
        Args:
            schedule_name: Nome do schedule
            
        Returns:
            bool: True se sucesso
        """
        try:
            self.client.delete_schedule(Name=schedule_name)
            
            logger.info(
                "EventBridge Schedule deleted",
                name=schedule_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete schedule",
                name=schedule_name,
                error=str(e)
            )
            return False
    
    def pause_schedule(self, schedule_name: str) -> bool:
        """
        Pausar schedule (desabilitar).
        
        Args:
            schedule_name: Nome do schedule
            
        Returns:
            bool: True se sucesso
        """
        try:
            # Obter configuração atual
            current_schedule = self.get_schedule(schedule_name)
            if not current_schedule:
                return False
            
            # Atualizar para DISABLED
            self.client.update_schedule(
                Name=schedule_name,
                ScheduleExpression=current_schedule['ScheduleExpression'],
                Target=current_schedule['Target'],
                FlexibleTimeWindow=current_schedule['FlexibleTimeWindow'],
                State='DISABLED'
            )
            
            logger.info(
                "EventBridge Schedule paused",
                name=schedule_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to pause schedule",
                name=schedule_name,
                error=str(e)
            )
            return False
    
    def resume_schedule(self, schedule_name: str) -> bool:
        """
        Retomar schedule (habilitar).
        
        Args:
            schedule_name: Nome do schedule
            
        Returns:
            bool: True se sucesso
        """
        try:
            # Obter configuração atual
            current_schedule = self.get_schedule(schedule_name)
            if not current_schedule:
                return False
            
            # Atualizar para ENABLED
            self.client.update_schedule(
                Name=schedule_name,
                ScheduleExpression=current_schedule['ScheduleExpression'],
                Target=current_schedule['Target'],
                FlexibleTimeWindow=current_schedule['FlexibleTimeWindow'],
                State='ENABLED'
            )
            
            logger.info(
                "EventBridge Schedule resumed",
                name=schedule_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to resume schedule",
                name=schedule_name,
                error=str(e)
            )
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do Scheduler."""
        try:
            # Testar listagem de schedules
            self.client.list_schedules(MaxResults=1)
            
            return {
                'available': True,
                'default_timezone': self.config.scheduler_default_timezone,
                'default_role': self.config.scheduler_default_role
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do Scheduler."""
        try:
            schedules = self.list_schedules()
            
            # Contar por estado
            enabled_count = sum(1 for s in schedules if s.get('State') == 'ENABLED')
            disabled_count = sum(1 for s in schedules if s.get('State') == 'DISABLED')
            
            return {
                'total_schedules': len(schedules),
                'enabled_schedules': enabled_count,
                'disabled_schedules': disabled_count,
                'default_timezone': self.config.scheduler_default_timezone
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
