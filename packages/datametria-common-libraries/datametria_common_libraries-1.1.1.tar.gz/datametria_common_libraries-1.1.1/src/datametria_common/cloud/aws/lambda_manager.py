"""
⚡ Lambda Manager - DATAMETRIA AWS Services

Gerenciador Lambda integrado aos componentes DATAMETRIA.
"""

import json
import base64
from typing import Dict, Any, Optional, List
import boto3
import structlog
from botocore.exceptions import ClientError

from .config import AWSConfig
from .models import LambdaInvokeResult

logger = structlog.get_logger(__name__)


class LambdaManager:
    """
    Gerenciador Lambda DATAMETRIA.
    
    Integra serverless functions com logging e monitoramento.
    """
    
    def __init__(self, session: boto3.Session, config: AWSConfig):
        """
        Inicializa LambdaManager.
        
        Args:
            session: Sessão boto3
            config: Configuração AWS
        """
        self.session = session
        self.config = config
        self.client = session.client('lambda')
        
        logger.info(
            "LambdaManager initialized",
            region=config.region
        )
    
    async def invoke_function(
        self, 
        function_name: str, 
        payload: Dict[str, Any], 
        invocation_type: str = 'RequestResponse'
    ) -> LambdaInvokeResult:
        """
        Invocar função Lambda.
        
        Args:
            function_name: Nome da função
            payload: Dados de entrada
            invocation_type: Tipo de invocação (RequestResponse, Event, DryRun)
            
        Returns:
            LambdaInvokeResult: Resultado da invocação
        """
        try:
            # Preparar payload
            payload_json = json.dumps(payload)
            
            # Invocar função
            response = self.client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=payload_json
            )
            
            status_code = response['StatusCode']
            
            # Processar resposta
            result_payload = {}
            log_result = None
            
            if 'Payload' in response:
                payload_data = response['Payload'].read()
                if payload_data:
                    try:
                        result_payload = json.loads(payload_data.decode('utf-8'))
                    except json.JSONDecodeError:
                        result_payload = {'raw_response': payload_data.decode('utf-8')}
            
            if 'LogResult' in response:
                log_result = base64.b64decode(response['LogResult']).decode('utf-8')
            
            # Verificar se houve erro na função
            function_error = response.get('FunctionError')
            success = status_code == 200 and not function_error
            
            logger.info(
                "Lambda function invoked",
                function_name=function_name,
                status_code=status_code,
                invocation_type=invocation_type,
                success=success,
                function_error=function_error
            )
            
            return LambdaInvokeResult(
                success=success,
                function_name=function_name,
                status_code=status_code,
                payload=result_payload,
                log_result=log_result,
                error=function_error,
                metadata={
                    'invocation_type': invocation_type,
                    'executed_version': response.get('ExecutedVersion'),
                    'payload_size': len(payload_json)
                }
            )
            
        except ClientError as e:
            logger.error(
                "Lambda invoke failed",
                function_name=function_name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return LambdaInvokeResult(
                success=False,
                function_name=function_name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    def list_functions(self, function_version: str = 'ALL') -> List[Dict[str, Any]]:
        """
        Listar funções Lambda.
        
        Args:
            function_version: Versão das funções
            
        Returns:
            List: Lista de funções
        """
        try:
            response = self.client.list_functions(FunctionVersion=function_version)
            functions = response.get('Functions', [])
            
            logger.info(
                "Lambda functions listed",
                count=len(functions),
                function_version=function_version
            )
            
            return functions
            
        except Exception as e:
            logger.error(
                "Failed to list Lambda functions",
                error=str(e)
            )
            return []
    
    def get_function(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Obter detalhes de uma função Lambda.
        
        Args:
            function_name: Nome da função
            
        Returns:
            Dict: Detalhes da função ou None
        """
        try:
            response = self.client.get_function(FunctionName=function_name)
            
            logger.info(
                "Lambda function details retrieved",
                function_name=function_name,
                runtime=response['Configuration'].get('Runtime'),
                memory=response['Configuration'].get('MemorySize')
            )
            
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning("Lambda function not found", function_name=function_name)
                return None
            else:
                logger.error(
                    "Failed to get Lambda function",
                    function_name=function_name,
                    error=str(e)
                )
                return None
    
    def update_function_code(self, function_name: str, zip_file: bytes) -> bool:
        """
        Atualizar código da função Lambda.
        
        Args:
            function_name: Nome da função
            zip_file: Arquivo ZIP com o código
            
        Returns:
            bool: True se sucesso
        """
        try:
            response = self.client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_file
            )
            
            logger.info(
                "Lambda function code updated",
                function_name=function_name,
                code_size=response.get('CodeSize'),
                last_modified=response.get('LastModified')
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update Lambda function code",
                function_name=function_name,
                error=str(e)
            )
            return False
    
    def update_function_configuration(
        self, 
        function_name: str, 
        **kwargs
    ) -> bool:
        """
        Atualizar configuração da função Lambda.
        
        Args:
            function_name: Nome da função
            **kwargs: Parâmetros de configuração
            
        Returns:
            bool: True se sucesso
        """
        try:
            # Filtrar parâmetros válidos
            valid_params = [
                'Runtime', 'Role', 'Handler', 'Description', 'Timeout',
                'MemorySize', 'Environment', 'DeadLetterConfig', 'KMSKeyArn',
                'TracingConfig', 'RevisionId', 'Layers', 'FileSystemConfigs',
                'ImageConfig', 'EphemeralStorage'
            ]
            
            params = {'FunctionName': function_name}
            for key, value in kwargs.items():
                if key in valid_params:
                    params[key] = value
            
            response = self.client.update_function_configuration(**params)
            
            logger.info(
                "Lambda function configuration updated",
                function_name=function_name,
                updated_params=list(kwargs.keys())
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update Lambda function configuration",
                function_name=function_name,
                error=str(e)
            )
            return False
    
    def create_alias(self, function_name: str, alias_name: str, function_version: str) -> bool:
        """
        Criar alias para função Lambda.
        
        Args:
            function_name: Nome da função
            alias_name: Nome do alias
            function_version: Versão da função
            
        Returns:
            bool: True se sucesso
        """
        try:
            response = self.client.create_alias(
                FunctionName=function_name,
                Name=alias_name,
                FunctionVersion=function_version,
                Description=f"Alias created by DATAMETRIA for {function_name}"
            )
            
            logger.info(
                "Lambda alias created",
                function_name=function_name,
                alias_name=alias_name,
                function_version=function_version,
                alias_arn=response.get('AliasArn')
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to create Lambda alias",
                function_name=function_name,
                alias_name=alias_name,
                error=str(e)
            )
            return False
    
    def get_function_metrics(
        self, 
        function_name: str, 
        start_time, 
        end_time
    ) -> Dict[str, Any]:
        """
        Obter métricas da função Lambda.
        
        Args:
            function_name: Nome da função
            start_time: Tempo inicial
            end_time: Tempo final
            
        Returns:
            Dict: Métricas da função
        """
        try:
            cloudwatch = self.session.client('cloudwatch')
            
            metrics = {}
            metric_names = ['Invocations', 'Errors', 'Duration', 'Throttles']
            
            for metric_name in metric_names:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName=metric_name,
                    Dimensions=[
                        {
                            'Name': 'FunctionName',
                            'Value': function_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5 minutos
                    Statistics=['Sum', 'Average'] if metric_name != 'Duration' else ['Average', 'Maximum']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    if metric_name == 'Duration':
                        metrics[metric_name] = {
                            'average_ms': sum(d.get('Average', 0) for d in datapoints) / len(datapoints),
                            'max_ms': max(d.get('Maximum', 0) for d in datapoints)
                        }
                    else:
                        metrics[metric_name] = {
                            'total': sum(d.get('Sum', 0) for d in datapoints),
                            'average': sum(d.get('Average', 0) for d in datapoints) / len(datapoints)
                        }
            
            logger.info(
                "Lambda function metrics retrieved",
                function_name=function_name,
                metrics_count=len(metrics)
            )
            
            return metrics
            
        except Exception as e:
            logger.error(
                "Failed to get Lambda function metrics",
                function_name=function_name,
                error=str(e)
            )
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do Lambda."""
        try:
            # Testar listagem de funções
            self.client.list_functions(MaxItems=1)
            
            return {
                'available': True
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do Lambda."""
        try:
            functions = self.list_functions()
            
            return {
                'functions_count': len(functions)
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
