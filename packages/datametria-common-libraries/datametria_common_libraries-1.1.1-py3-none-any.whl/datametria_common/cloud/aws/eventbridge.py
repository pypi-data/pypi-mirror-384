"""
🎯 EventBridge Manager - DATAMETRIA AWS Services

Gerenciador EventBridge integrado aos componentes DATAMETRIA.
"""

import json
import time
from typing import List, Dict, Any, Optional
import boto3
import structlog
from botocore.exceptions import ClientError

from .config import AWSConfig
from .models import EventBridgeEvent, EventBridgeResult, EventBridgeRuleConfig

logger = structlog.get_logger(__name__)


class EventBridgeManager:
    """
    Gerenciador EventBridge DATAMETRIA.
    
    Integra event-driven architecture com logging e monitoramento.
    """
    
    def __init__(self, session: boto3.Session, config: AWSConfig):
        """
        Inicializa EventBridgeManager.
        
        Args:
            session: Sessão boto3
            config: Configuração AWS
        """
        self.session = session
        self.config = config
        self.client = session.client('events')
        
        logger.info(
            "EventBridgeManager initialized",
            region=config.region,
            default_bus=config.eventbridge_default_bus
        )
    
    async def put_events(self, events: List[EventBridgeEvent]) -> EventBridgeResult:
        """
        Enviar eventos para EventBridge.
        
        Args:
            events: Lista de eventos para enviar
            
        Returns:
            EventBridgeResult: Resultado da operação
        """
        start_time = time.time()
        
        try:
            # Preparar entries
            entries = []
            for event in events:
                entry = {
                    'Source': event.source,
                    'DetailType': event.detail_type,
                    'Detail': json.dumps(event.detail),
                    'EventBusName': event.event_bus_name or self.config.eventbridge_default_bus
                }
                
                if event.resources:
                    entry['Resources'] = event.resources
                
                entries.append(entry)
            
            # Enviar eventos
            response = self.client.put_events(Entries=entries)
            
            # Analisar resultado
            failed_entries = [
                entry for entry in response.get('Entries', []) 
                if 'ErrorCode' in entry
            ]
            
            successful_count = len(entries) - len(failed_entries)
            processing_time = time.time() - start_time
            
            # Log da operação
            logger.info(
                "EventBridge events sent",
                total_events=len(entries),
                successful=successful_count,
                failed=len(failed_entries),
                processing_time=processing_time
            )
            
            return EventBridgeResult(
                success=len(failed_entries) == 0,
                operation="put_events",
                successful_entries=successful_count,
                failed_entries=len(failed_entries),
                failed_entry_details=failed_entries,
                metadata={
                    'processing_time': processing_time,
                    'total_events': len(entries)
                }
            )
            
        except ClientError as e:
            logger.error(
                "EventBridge put_events failed",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return EventBridgeResult(
                success=False,
                operation="put_events",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
        except Exception as e:
            logger.error("Unexpected error in put_events", error=str(e))
            
            return EventBridgeResult(
                success=False,
                operation="put_events",
                error=str(e)
            )
    
    async def create_rule(self, rule_config: EventBridgeRuleConfig) -> EventBridgeResult:
        """
        Criar regra EventBridge.
        
        Args:
            rule_config: Configuração da regra
            
        Returns:
            EventBridgeResult: Resultado da operação
        """
        try:
            # Criar regra
            response = self.client.put_rule(
                Name=rule_config.name,
                EventPattern=json.dumps(rule_config.event_pattern),
                State=rule_config.state,
                Description=rule_config.description or f"Rule created by DATAMETRIA - {rule_config.name}",
                EventBusName=rule_config.event_bus_name or self.config.eventbridge_default_bus
            )
            
            # Adicionar targets se fornecidos
            if rule_config.targets:
                await self._add_targets_to_rule(rule_config.name, rule_config.targets)
            
            logger.info(
                "EventBridge rule created",
                rule_name=rule_config.name,
                rule_arn=response['RuleArn'],
                targets_count=len(rule_config.targets or [])
            )
            
            return EventBridgeResult(
                success=True,
                operation="create_rule",
                metadata={
                    'rule_arn': response['RuleArn'],
                    'rule_name': rule_config.name,
                    'targets_count': len(rule_config.targets or [])
                }
            )
            
        except ClientError as e:
            logger.error(
                "EventBridge create_rule failed",
                rule_name=rule_config.name,
                error=str(e),
                error_code=e.response['Error']['Code']
            )
            
            return EventBridgeResult(
                success=False,
                operation="create_rule",
                error=str(e),
                error_code=e.response['Error']['Code']
            )
    
    async def _add_targets_to_rule(self, rule_name: str, targets: List[Dict]) -> None:
        """Adicionar targets à regra EventBridge."""
        try:
            target_entries = []
            for i, target in enumerate(targets):
                entry = {
                    'Id': str(i + 1),
                    'Arn': target['arn'],
                }
                
                if 'role_arn' in target:
                    entry['RoleArn'] = target['role_arn']
                
                if 'input_transformer' in target:
                    entry['InputTransformer'] = target['input_transformer']
                elif 'input_path' in target:
                    entry['InputPath'] = target['input_path']
                
                target_entries.append(entry)
            
            self.client.put_targets(
                Rule=rule_name,
                Targets=target_entries
            )
            
            logger.info(
                "EventBridge targets added",
                rule_name=rule_name,
                targets_count=len(target_entries)
            )
            
        except Exception as e:
            logger.error(
                "Failed to add targets to rule",
                rule_name=rule_name,
                error=str(e)
            )
            raise
    
    def list_rules(self, event_bus_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Listar regras EventBridge."""
        try:
            bus_name = event_bus_name or self.config.eventbridge_default_bus
            
            response = self.client.list_rules(EventBusName=bus_name)
            rules = response.get('Rules', [])
            
            logger.info(
                "EventBridge rules listed",
                event_bus=bus_name,
                rules_count=len(rules)
            )
            
            return rules
            
        except Exception as e:
            logger.error("Failed to list EventBridge rules", error=str(e))
            return []
    
    def delete_rule(self, rule_name: str, event_bus_name: Optional[str] = None) -> bool:
        """Deletar regra EventBridge."""
        try:
            bus_name = event_bus_name or self.config.eventbridge_default_bus
            
            # Remover targets primeiro
            targets_response = self.client.list_targets_by_rule(
                Rule=rule_name,
                EventBusName=bus_name
            )
            
            if targets_response.get('Targets'):
                target_ids = [target['Id'] for target in targets_response['Targets']]
                self.client.remove_targets(
                    Rule=rule_name,
                    EventBusName=bus_name,
                    Ids=target_ids
                )
            
            # Deletar regra
            self.client.delete_rule(
                Name=rule_name,
                EventBusName=bus_name
            )
            
            logger.info(
                "EventBridge rule deleted",
                rule_name=rule_name,
                event_bus=bus_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete EventBridge rule",
                rule_name=rule_name,
                error=str(e)
            )
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do EventBridge."""
        try:
            # Testar listagem de regras
            self.client.list_rules(Limit=1)
            
            return {
                'available': True,
                'default_bus': self.config.eventbridge_default_bus,
                'region': self.config.region
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do EventBridge."""
        try:
            rules = self.list_rules()
            
            return {
                'rules_count': len(rules),
                'default_bus': self.config.eventbridge_default_bus,
                'replay_enabled': self.config.eventbridge_enable_replay
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
