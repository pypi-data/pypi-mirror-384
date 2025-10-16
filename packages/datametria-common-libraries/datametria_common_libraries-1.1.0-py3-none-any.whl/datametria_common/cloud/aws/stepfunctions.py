"""
🔄 Step Functions Manager - DATAMETRIA AWS Services

Gerenciador Step Functions integrado aos componentes DATAMETRIA.
"""

import json
import time
from typing import Dict, Any, Optional
import boto3
import structlog
from botocore.exceptions import ClientError

from .config import AWSConfig
from .models import (
    StateMachineConfig, ExecutionConfig, ExecutionResult, 
    ExecutionStatusResult, ExecutionStatus, AWSResult
)

logger = structlog.get_logger(__name__)


class StepFunctionsManager:
    """
    Gerenciador Step Functions DATAMETRIA.
    
    Integra workflow orchestration com logging e monitoramento.
    """
    
    def __init__(self, session: boto3.Session, config: AWSConfig):
        """
        Inicializa StepFunctionsManager.
        
        Args:
            session: Sessão boto3
            config: Configuração AWS
        """
        self.session = session
        self.config = config
        self.client = session.client('stepfunctions')
        
        logger.info(
            "StepFunctionsManager initialized",
            region=config.region,
            log_group=config.stepfunctions_log_group,
            tracing_enabled=config.stepfunctions_enable_tracing
        )
    
    async def create_state_machine(self, state_machine_config: StateMachineConfig) -> AWSResult:
        """
        Criar state machine.
        
        Args:
            state_machine_config: Configuração da state machine
            
        Returns:
            AWSResult: Resultado da operação
        """
        try:
            # Preparar configuração de logging
            logging_config = {}
            if state_machine_config.logging_enabled:
                logging_config = {
                    'level': 'ALL',
                    'includeExecutionData': True,
                    'destinations': [{
                        'cloudWatchLogsLogGroup': {
                            'logGroupArn': f"arn:aws:logs:{self.config.region}:*:log-group:{self.config.stepfunctions_log_group}:*"
                        }
                    }]
                }
            
            # Preparar configuração de tracing
            tracing_config = {}
            if state_machine_config.tracing_enabled:
                tracing_config = {'enabled': True}
            
            # Criar state machine
            params = {
                'name': state_machine_config.name,
                'definition': json.dumps(state_machine_config.definition),
                'roleArn': state_machine_config.role_arn,
                'type': state_machine_config.type.value
            }
            
            if logging_config:
                params['loggingConfiguration'] = logging_config
            
            if tracing_config:
                params['tracingConfiguration'] = tracing_config
            
            # Adicionar tags padrão
            params['tags'] = [
                {'key': k, 'value': v} 
                for k, v in self.config.default_tags.items()
            ]
            
            response = self.client.create_state_machine(**params)
            
            logger.info(
                "Step Functions state machine created",
                name=state_machine_config.name,
                arn=response['stateMachineArn'],
                type=state_machine_config.type.value
            )
            
            return AWSResult(
                success=True,
                service="stepfunctions",
                operation="create_state_machine",
                metadata={
                    'state_machine_arn': response['stateMachineArn'],
                    'creation_date': response['creationDate'].isoformat(),
                    'name': state_machine_config.name,
                    'type': state_machine_config.type.value
                }
            )
            
        except ClientError as e:
            logger.error(
                "Step Functions create_state_machine failed",
                name=state_machine_config.name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return AWSResult(
                success=False,
                service="stepfunctions",
                operation="create_state_machine",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    async def start_execution(self, execution_config: ExecutionConfig) -> ExecutionResult:
        """
        Iniciar execução de state machine.
        
        Args:
            execution_config: Configuração da execução
            
        Returns:
            ExecutionResult: Resultado da operação
        """
        try:
            response = self.client.start_execution(
                stateMachineArn=execution_config.state_machine_arn,
                name=execution_config.name,
                input=json.dumps(execution_config.input_data)
            )
            
            logger.info(
                "Step Functions execution started",
                execution_arn=response['executionArn'],
                name=execution_config.name,
                state_machine=execution_config.state_machine_arn
            )
            
            return ExecutionResult(
                success=True,
                execution_arn=response['executionArn'],
                start_date=response['startDate'],
                metadata={
                    'name': execution_config.name,
                    'state_machine_arn': execution_config.state_machine_arn
                }
            )
            
        except ClientError as e:
            logger.error(
                "Step Functions start_execution failed",
                name=execution_config.name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return ExecutionResult(
                success=False,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    async def get_execution_status(self, execution_arn: str) -> ExecutionStatusResult:
        """
        Obter status de execução.
        
        Args:
            execution_arn: ARN da execução
            
        Returns:
            ExecutionStatusResult: Status da execução
        """
        try:
            response = self.client.describe_execution(executionArn=execution_arn)
            
            # Converter status
            status = ExecutionStatus(response['status'])
            
            # Processar dados de entrada e saída
            input_data = {}
            output_data = {}
            
            try:
                input_data = json.loads(response.get('input', '{}'))
            except json.JSONDecodeError:
                pass
            
            try:
                output_data = json.loads(response.get('output', '{}'))
            except json.JSONDecodeError:
                pass
            
            logger.info(
                "Step Functions execution status retrieved",
                execution_arn=execution_arn,
                status=status.value
            )
            
            return ExecutionStatusResult(
                success=True,
                status=status,
                start_date=response['startDate'],
                stop_date=response.get('stopDate'),
                input_data=input_data,
                output_data=output_data,
                error=response.get('error'),
                metadata={
                    'execution_arn': execution_arn,
                    'state_machine_arn': response['stateMachineArn']
                }
            )
            
        except ClientError as e:
            logger.error(
                "Step Functions get_execution_status failed",
                execution_arn=execution_arn,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return ExecutionStatusResult(
                success=False,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    def stop_execution(self, execution_arn: str, error: str = "UserRequested", cause: str = "Execution stopped by user") -> bool:
        """
        Parar execução de state machine.
        
        Args:
            execution_arn: ARN da execução
            error: Código de erro
            cause: Causa da parada
            
        Returns:
            bool: True se sucesso
        """
        try:
            self.client.stop_execution(
                executionArn=execution_arn,
                error=error,
                cause=cause
            )
            
            logger.info(
                "Step Functions execution stopped",
                execution_arn=execution_arn,
                error=error,
                cause=cause
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to stop Step Functions execution",
                execution_arn=execution_arn,
                error=str(e)
            )
            return False
    
    def list_state_machines(self) -> List[Dict[str, Any]]:
        """Listar state machines."""
        try:
            response = self.client.list_state_machines()
            state_machines = response.get('stateMachines', [])
            
            logger.info(
                "Step Functions state machines listed",
                count=len(state_machines)
            )
            
            return state_machines
            
        except Exception as e:
            logger.error("Failed to list state machines", error=str(e))
            return []
    
    def delete_state_machine(self, state_machine_arn: str) -> bool:
        """Deletar state machine."""
        try:
            self.client.delete_state_machine(stateMachineArn=state_machine_arn)
            
            logger.info(
                "Step Functions state machine deleted",
                arn=state_machine_arn
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete state machine",
                arn=state_machine_arn,
                error=str(e)
            )
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do Step Functions."""
        try:
            # Testar listagem de state machines
            self.client.list_state_machines(maxResults=1)
            
            return {
                'available': True,
                'log_group': self.config.stepfunctions_log_group,
                'tracing_enabled': self.config.stepfunctions_enable_tracing
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do Step Functions."""
        try:
            state_machines = self.list_state_machines()
            
            return {
                'state_machines_count': len(state_machines),
                'log_group': self.config.stepfunctions_log_group,
                'tracing_enabled': self.config.stepfunctions_enable_tracing
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
