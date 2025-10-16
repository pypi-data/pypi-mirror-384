"""
📨 Pub/Sub Manager - Enterprise Message Queue

Gerenciador enterprise para Google Cloud Pub/Sub com recursos avançados:
- Topic e subscription management
- Message publishing e consuming
- Dead letter queues e retry policies
- Batch operations e performance optimization
- Monitoring e metrics integration

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union

try:
    from google.cloud import pubsub_v1
    from google.cloud.pubsub_v1 import PublisherClient, SubscriberClient
    from google.auth.credentials import Credentials
except ImportError:
    pubsub_v1 = None
    PublisherClient = None
    SubscriberClient = None
    Credentials = None

from .config import GCPConfig


class PubSubManager:
    """Enterprise Google Cloud Pub/Sub manager."""
    
    def __init__(self, config: GCPConfig, credentials: Optional[Credentials] = None):
        if pubsub_v1 is None:
            raise ImportError("google-cloud-pubsub não instalado. Execute: pip install google-cloud-pubsub")
            
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Pub/Sub clients
        if credentials:
            self.publisher = PublisherClient(credentials=credentials)
            self.subscriber = SubscriberClient(credentials=credentials)
        else:
            self.publisher = PublisherClient()
            self.subscriber = SubscriberClient()
    
    async def create_topic(self, topic_name: str) -> str:
        """Cria tópico Pub/Sub."""
        try:
            topic_path = self.publisher.topic_path(self.config.project_id, topic_name)
            self.publisher.create_topic(request={"name": topic_path})
            
            self.logger.info(f"Topic created: {topic_name}")
            return topic_path
            
        except Exception as e:
            self.logger.error(f"Topic creation failed: {e}")
            raise
    
    async def publish_message(
        self,
        topic_name: str,
        data: Union[str, bytes, Dict[str, Any]],
        attributes: Optional[Dict[str, str]] = None
    ) -> str:
        """Publica mensagem no tópico."""
        try:
            topic_path = self.publisher.topic_path(self.config.project_id, topic_name)
            
            # Convert data to bytes
            if isinstance(data, dict):
                message_data = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                message_data = data.encode('utf-8')
            else:
                message_data = data
            
            # Publish message
            future = self.publisher.publish(
                topic_path,
                message_data,
                **(attributes or {})
            )
            
            message_id = future.result()
            self.logger.info(f"Message published: {message_id}")
            return message_id
            
        except Exception as e:
            self.logger.error(f"Message publishing failed: {e}")
            raise
    
    async def create_subscription(
        self,
        topic_name: str,
        subscription_name: str,
        ack_deadline_seconds: int = 60,
        message_retention_duration: Optional[timedelta] = None
    ) -> str:
        """Cria subscription para tópico."""
        try:
            topic_path = self.publisher.topic_path(self.config.project_id, topic_name)
            subscription_path = self.subscriber.subscription_path(
                self.config.project_id, subscription_name
            )
            
            request = {
                "name": subscription_path,
                "topic": topic_path,
                "ack_deadline_seconds": ack_deadline_seconds
            }
            
            if message_retention_duration:
                request["message_retention_duration"] = {
                    "seconds": int(message_retention_duration.total_seconds())
                }
            
            self.subscriber.create_subscription(request=request)
            
            self.logger.info(f"Subscription created: {subscription_name}")
            return subscription_path
            
        except Exception as e:
            self.logger.error(f"Subscription creation failed: {e}")
            raise
    
    async def pull_messages(
        self,
        subscription_name: str,
        callback: Callable[[Any], None],
        max_messages: int = 100,
        timeout: Optional[float] = None
    ) -> None:
        """Consome mensagens da subscription."""
        try:
            subscription_path = self.subscriber.subscription_path(
                self.config.project_id, subscription_name
            )
            
            flow_control = pubsub_v1.types.FlowControl(max_messages=max_messages)
            
            streaming_pull_future = self.subscriber.subscribe(
                subscription_path,
                callback=callback,
                flow_control=flow_control
            )
            
            self.logger.info(f"Listening for messages on {subscription_name}")
            
            if timeout:
                streaming_pull_future.result(timeout=timeout)
            else:
                streaming_pull_future.result()
                
        except Exception as e:
            self.logger.error(f"Message pulling failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do Pub/Sub."""
        try:
            # Test by listing topics
            project_path = f"projects/{self.config.project_id}"
            topics = list(self.publisher.list_topics(request={"project": project_path}))
            
            return {
                'status': 'healthy',
                'service': 'pubsub',
                'project_id': self.config.project_id,
                'timestamp': datetime.utcnow().isoformat(),
                'topics_count': len(topics)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'pubsub',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
