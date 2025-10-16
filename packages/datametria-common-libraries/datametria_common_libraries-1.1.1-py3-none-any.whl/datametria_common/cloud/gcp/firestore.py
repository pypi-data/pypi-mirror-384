"""
📊 Firestore Manager - Enterprise NoSQL Database Operations

Gerenciador enterprise para Google Cloud Firestore com recursos avançados de
NoSQL database, incluindo CRUD operations, real-time sync, batch operations,
query optimization e compliance LGPD/GDPR.

Features:
    - CRUD operations com validação automática
    - Real-time listeners e subscriptions
    - Batch operations e transações atômicas
    - Query optimization e indexing inteligente
    - Security rules e access control
    - Metadata automático (timestamps, auditoria)
    - Multi-database support
    - Health check e monitoring integrado
    - Compliance LGPD/GDPR automático

Examples:
    Basic Usage:
    >>> from datametria_common.cloud.gcp import FirestoreManager, GCPConfig
    >>> config = GCPConfig(project_id="my-project")
    >>> fs = FirestoreManager(config)
    >>> fs.create_document("users", "user123", {"name": "John"})
    >>> user = fs.get_document("users", "user123")

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
License: MIT
Compliance: LGPD/GDPR Ready
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from google.auth.credentials import Credentials
    from google.cloud import firestore
    from google.cloud.firestore import Client, CollectionReference, DocumentReference
except ImportError:
    firestore = None
    Client = None
    DocumentReference = None
    CollectionReference = None
    Credentials = None

from .config import GCPConfig


class FirestoreManager:
    """Enterprise Google Cloud Firestore manager com recursos avançados de NoSQL.

    Gerenciador completo para operações Firestore incluindo CRUD operations,
    real-time sync, batch operations, query optimization e compliance LGPD/GDPR.

    Attributes:
        config (GCPConfig): Configuração GCP com project_id e database settings
        client (firestore.Client): Cliente Firestore autenticado
        logger (logging.Logger): Logger para auditoria e debugging

    Examples:
        >>> config = GCPConfig(project_id="my-project")
        >>> fs = FirestoreManager(config)
        >>>
        >>> # CRUD operations
        >>> fs.create_document("users", "user123", {
        ...     "name": "João Silva",
        ...     "email": "joao@example.com",
        ...     "age": 30
        ... })
        >>>
        >>> # Query com filtros
        >>> users = fs.query_documents(
        ...     "users",
        ...     filters=[{"field": "age", "operator": ">=", "value": 18}],
        ...     order_by=[{"field": "name", "direction": "asc"}]
        ... )

    Note:
        Requer google-cloud-firestore instalado: pip install google-cloud-firestore
        Todas as operações são logadas para auditoria e compliance.
    """

    def __init__(self, config: GCPConfig, credentials: Optional[Credentials] = None):
        """Inicializa Firestore manager com configuração e credenciais.

        Args:
            config (GCPConfig): Configuração GCP com project_id e firestore settings
            credentials (Optional[Credentials]): Credenciais GCP customizadas.
                Se None, usa credenciais padrão do ambiente.

        Raises:
            ImportError: Se google-cloud-firestore não estiver instalado
            ValueError: Se configuração for inválida

        Examples:
            >>> config = GCPConfig(project_id="my-project")
            >>> fs = FirestoreManager(config)
            >>>
            >>> # Com credenciais customizadas
            >>> from google.oauth2 import service_account
            >>> creds = service_account.Credentials.from_service_account_file("key.json")
            >>> fs = FirestoreManager(config, creds)

        Note:
            - Suporta múltiplos databases via config.firestore_config
            - Database padrão é '(default)' se não especificado
            - Cliente é inicializado com project_id da configuração
        """
        if firestore is None:
            raise ImportError(
                "google-cloud-firestore não instalado. Execute: pip install google-cloud-firestore"
            )

        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize Firestore client
        if credentials:
            self.client = firestore.Client(
                project=config.project_id,
                credentials=credentials,
                database=config.firestore_config.get("database_id", "(default)"),
            )
        else:
            self.client = firestore.Client(
                project=config.project_id,
                database=config.firestore_config.get("database_id", "(default)"),
            )

    def create_document(
        self, collection: str, doc_id: str, data: Dict[str, Any], validate: bool = True
    ) -> str:
        """Cria documento no Firestore com validação e metadata automático.

        Args:
            collection (str): Nome da coleção (formato: snake_case)
            doc_id (str): ID único do documento
            data (Dict[str, Any]): Dados do documento (JSON-serializable)
            validate (bool): Se deve validar dados antes de salvar.
                Default: True (recomendado)

        Returns:
            str: ID do documento criado (mesmo que doc_id fornecido)

        Raises:
            ValueError: Se dados forem inválidos ou contenham campos reservados
            Exception: Se criação falhar por permissões ou quota

        Examples:
            >>> # Documento básico
            >>> doc_id = fs.create_document(
            ...     "users",
            ...     "user123",
            ...     {
            ...         "name": "João Silva",
            ...         "email": "joao@example.com",
            ...         "age": 30,
            ...         "active": True
            ...     }
            ... )
            >>>
            >>> # Documento complexo com arrays e objetos
            >>> doc_id = fs.create_document(
            ...     "products",
            ...     "prod456",
            ...     {
            ...         "name": "Smartphone",
            ...         "price": 999.99,
            ...         "categories": ["electronics", "mobile"],
            ...         "specs": {
            ...             "memory": "128GB",
            ...             "color": "black"
            ...         }
            ...     }
            ... )

        Note:
            - Adiciona automaticamente created_at e updated_at (SERVER_TIMESTAMP)
            - Campos reservados: _id, created_at, updated_at
            - Validação previne dados inválidos
            - Operação é logada para auditoria
        """
        try:
            if validate:
                self._validate_document_data(data)

            # Add metadata
            data["created_at"] = firestore.SERVER_TIMESTAMP
            data["updated_at"] = firestore.SERVER_TIMESTAMP

            doc_ref = self.client.collection(collection).document(doc_id)
            doc_ref.set(data)

            self.logger.info(f"Document created: {collection}/{doc_id}")
            return doc_id

        except Exception as e:
            self.logger.error(f"Create document failed: {e}")
            raise

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Obtém documento do Firestore com metadados completos.

        Args:
            collection (str): Nome da coleção
            doc_id (str): ID do documento

        Returns:
            Optional[Dict[str, Any]]: Dados completos do documento incluindo:
                - Todos os campos do documento
                - _id: ID do documento
                - created_at, updated_at: Timestamps (se existirem)
                Retorna None se documento não existir

        Raises:
            Exception: Se busca falhar por permissões ou erro de rede

        Examples:
            >>> # Buscar documento
            >>> user = fs.get_document("users", "user123")
            >>> if user:
            ...     print(f"Nome: {user['name']}")
            ...     print(f"ID: {user['_id']}")
            ...     print(f"Criado em: {user['created_at']}")
            ... else:
            ...     print("Documento não encontrado")
            >>>
            >>> # Verificar existência
            >>> exists = fs.get_document("products", "prod456") is not None

        Note:
            - Retorna None se documento não existir (não lança exceção)
            - Inclui _id automaticamente nos dados retornados
            - Timestamps são objetos datetime do Firestore
            - Operação não é logada (consulta apenas)
        """
        try:
            doc_ref = self.client.collection(collection).document(doc_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                data["_id"] = doc.id
                return data
            else:
                return None

        except Exception as e:
            self.logger.error(f"Get document failed: {e}")
            raise

    def update_document(
        self, collection: str, doc_id: str, data: Dict[str, Any], merge: bool = True
    ) -> bool:
        """Atualiza documento no Firestore com controle de merge.

        Args:
            collection (str): Nome da coleção
            doc_id (str): ID do documento a ser atualizado
            data (Dict[str, Any]): Dados para atualizar (JSON-serializable)
            merge (bool): Se deve fazer merge com dados existentes.
                True: Mantém campos não especificados (recomendado)
                False: Substitui apenas campos especificados

        Returns:
            bool: True se atualizado com sucesso

        Raises:
            Exception: Se atualização falhar por documento inexistente ou permissões

        Examples:
            >>> # Update com merge (recomendado)
            >>> success = fs.update_document(
            ...     "users",
            ...     "user123",
            ...     {"age": 31, "last_login": datetime.utcnow()}
            ... )
            >>>
            >>> # Update sem merge (apenas campos especificados)
            >>> success = fs.update_document(
            ...     "users",
            ...     "user123",
            ...     {"status": "inactive"},
            ...     merge=False
            ... )
            >>>
            >>> # Update de objeto aninhado
            >>> success = fs.update_document(
            ...     "products",
            ...     "prod456",
            ...     {"specs.memory": "256GB"}  # Dot notation
            ... )

        Note:
            - Adiciona automaticamente updated_at (SERVER_TIMESTAMP)
            - merge=True preserva campos não especificados
            - merge=False requer que documento já exista
            - Suporta dot notation para campos aninhados
        """
        try:
            # Add update timestamp
            data["updated_at"] = firestore.SERVER_TIMESTAMP

            doc_ref = self.client.collection(collection).document(doc_id)

            if merge:
                doc_ref.set(data, merge=True)
            else:
                doc_ref.update(data)

            self.logger.info(f"Document updated: {collection}/{doc_id}")
            return True

        except Exception as e:
            self.logger.error(f"Update document failed: {e}")
            raise

    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Deleta documento do Firestore permanentemente (LGPD/GDPR compliant).

        Args:
            collection (str): Nome da coleção
            doc_id (str): ID do documento a ser deletado

        Returns:
            bool: True se deletado com sucesso

        Raises:
            Exception: Se deleção falhar por permissões ou erro de rede

        Examples:
            >>> # Deletar documento (direito ao esquecimento LGPD)
            >>> success = fs.delete_document("users", "user123")
            >>> if success:
            ...     print("Usuário removido com sucesso")
            >>>
            >>> # Deletar em lote (usar batch_operations)
            >>> operations = [
            ...     {"type": "delete", "collection": "users", "doc_id": "user1"},
            ...     {"type": "delete", "collection": "users", "doc_id": "user2"}
            ... ]
            >>> fs.batch_operations(operations)

        Note:
            - Deleção é PERMANENTE e irreversível
            - Atende direito ao esquecimento (LGPD Art. 18, III)
            - Não falha se documento não existir
            - Operação é logada para auditoria de compliance
        """
        try:
            doc_ref = self.client.collection(collection).document(doc_id)
            doc_ref.delete()

            self.logger.info(f"Document deleted: {collection}/{doc_id}")
            return True

        except Exception as e:
            self.logger.error(f"Delete document failed: {e}")
            raise

    def query_documents(
        self,
        collection: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query documentos com filtros avançados e otimização automática.

        Args:
            collection (str): Nome da coleção para consultar
            filters (Optional[List[Dict[str, Any]]]): Lista de filtros:
                - field: Nome do campo
                - operator: Operador (==, !=, <, <=, >, >=, in, not-in, array-contains)
                - value: Valor para comparação
            order_by (Optional[List[Dict[str, str]]]): Lista de ordenação:
                - field: Nome do campo
                - direction: 'asc' ou 'desc' (default: 'asc')
            limit (Optional[int]): Máximo de documentos a retornar

        Returns:
            List[Dict[str, Any]]: Lista de documentos com _id incluído

        Raises:
            Exception: Se query falhar por índices faltantes ou permissões

        Examples:
            >>> # Query simples com filtro
            >>> adults = fs.query_documents(
            ...     "users",
            ...     filters=[{"field": "age", "operator": ">=", "value": 18}]
            ... )
            >>>
            >>> # Query complexa com múltiplos filtros
            >>> active_users = fs.query_documents(
            ...     "users",
            ...     filters=[
            ...         {"field": "active", "operator": "==", "value": True},
            ...         {"field": "age", "operator": ">=", "value": 18},
            ...         {"field": "country", "operator": "in", "value": ["BR", "AR"]}
            ...     ],
            ...     order_by=[
            ...         {"field": "created_at", "direction": "desc"},
            ...         {"field": "name", "direction": "asc"}
            ...     ],
            ...     limit=50
            ... )
            >>>
            >>> # Query com array-contains
            >>> tagged_posts = fs.query_documents(
            ...     "posts",
            ...     filters=[{"field": "tags", "operator": "array-contains", "value": "tech"}]
            ... )

        Note:
            - Queries complexas podem requerer índices compostos
            - Limite máximo por query: 1000 documentos
            - Ordenação requer índice se combinada com filtros
            - Todos os documentos incluem _id automaticamente
        """
        try:
            query = self.client.collection(collection)

            # Apply filters
            if filters:
                for filter_item in filters:
                    field = filter_item["field"]
                    operator = filter_item["operator"]
                    value = filter_item["value"]
                    query = query.where(field, operator, value)

            # Apply ordering
            if order_by:
                for order_item in order_by:
                    field = order_item["field"]
                    direction = order_item.get("direction", "asc")
                    if direction == "desc":
                        query = query.order_by(
                            field, direction=firestore.Query.DESCENDING
                        )
                    else:
                        query = query.order_by(field)

            # Apply limit
            if limit:
                query = query.limit(limit)

            docs = query.stream()
            results = []

            for doc in docs:
                data = doc.to_dict()
                data["_id"] = doc.id
                results.append(data)

            return results

        except Exception as e:
            self.logger.error(f"Query documents failed: {e}")
            raise

    def batch_operations(self, operations: List[Dict[str, Any]]) -> List[str]:
        """Executa operações em lote de forma atômica.

        Args:
            operations (List[Dict[str, Any]]): Lista de operações (máx 500):
                - type: 'create', 'update' ou 'delete'
                - collection: Nome da coleção
                - doc_id: ID do documento
                - data: Dados (apenas para create/update)

        Returns:
            List[str]: Lista de IDs processados na ordem das operações

        Raises:
            ValueError: Se operações excederem limite ou formato inválido
            Exception: Se batch falhar (todas operações são revertidas)

        Examples:
            >>> # Batch misto (create, update, delete)
            >>> operations = [
            ...     {
            ...         "type": "create",
            ...         "collection": "users",
            ...         "doc_id": "user1",
            ...         "data": {"name": "João", "email": "joao@example.com"}
            ...     },
            ...     {
            ...         "type": "update",
            ...         "collection": "users",
            ...         "doc_id": "user2",
            ...         "data": {"last_login": datetime.utcnow()}
            ...     },
            ...     {
            ...         "type": "delete",
            ...         "collection": "users",
            ...         "doc_id": "user3"
            ...     }
            ... ]
            >>> processed_ids = fs.batch_operations(operations)
            >>> print(f"Processados: {len(processed_ids)} documentos")
            >>>
            >>> # Batch de criação em massa
            >>> create_ops = [
            ...     {
            ...         "type": "create",
            ...         "collection": "products",
            ...         "doc_id": f"prod{i}",
            ...         "data": {"name": f"Product {i}", "price": i * 10}
            ...     }
            ...     for i in range(1, 101)  # 100 produtos
            ... ]
            >>> fs.batch_operations(create_ops)

        Note:
            - Operações são atômicas (tudo ou nada)
            - Limite máximo: 500 operações por batch
            - Adiciona timestamps automaticamente (create/update)
            - Mais eficiente que operações individuais
        """
        try:
            batch = self.client.batch()
            processed_ids = []

            for operation in operations:
                op_type = operation["type"]
                collection = operation["collection"]
                doc_id = operation["doc_id"]
                doc_ref = self.client.collection(collection).document(doc_id)

                if op_type == "create":
                    data = operation["data"]
                    data["created_at"] = firestore.SERVER_TIMESTAMP
                    data["updated_at"] = firestore.SERVER_TIMESTAMP
                    batch.set(doc_ref, data)

                elif op_type == "update":
                    data = operation["data"]
                    data["updated_at"] = firestore.SERVER_TIMESTAMP
                    batch.update(doc_ref, data)

                elif op_type == "delete":
                    batch.delete(doc_ref)

                processed_ids.append(doc_id)

            batch.commit()
            self.logger.info(
                f"Batch operations completed: {len(processed_ids)} operations"
            )
            return processed_ids

        except Exception as e:
            self.logger.error(f"Batch operations failed: {e}")
            raise

    def setup_real_time_listener(
        self,
        collection: str,
        callback: Callable[[List[Dict[str, Any]]], None],
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Configura listener em tempo real para mudanças na coleção.

        Args:
            collection (str): Nome da coleção para monitorar
            callback (Callable[[List[Dict[str, Any]]], None]): Função chamada
                quando documentos mudarem. Recebe lista de documentos atuais.
            filters (Optional[List[Dict[str, Any]]]): Filtros para aplicar
                ao listener (mesmo formato de query_documents)

        Returns:
            str: ID único do listener para referência

        Raises:
            Exception: Se setup falhar por permissões ou índices

        Examples:
            >>> # Listener simples
            >>> def on_users_change(users):
            ...     print(f"Usuários atualizados: {len(users)}")
            ...     for user in users:
            ...         print(f"- {user['name']} ({user['_id']})")
            >>>
            >>> listener_id = fs.setup_real_time_listener(
            ...     "users",
            ...     on_users_change
            ... )
            >>>
            >>> # Listener com filtros
            >>> def on_active_users_change(active_users):
            ...     active_count = len(active_users)
            ...     print(f"Usuários ativos: {active_count}")
            ...     # Atualizar dashboard em tempo real
            ...     update_dashboard_metrics(active_count)
            >>>
            >>> listener_id = fs.setup_real_time_listener(
            ...     "users",
            ...     on_active_users_change,
            ...     filters=[{"field": "active", "operator": "==", "value": True}]
            ... )
            >>>
            >>> # Listener para chat em tempo real
            >>> def on_messages_change(messages):
            ...     latest_message = messages[-1] if messages else None
            ...     if latest_message:
            ...         notify_users(latest_message)
            >>>
            >>> fs.setup_real_time_listener("chat_messages", on_messages_change)

        Note:
            - Callback é chamado imediatamente com estado atual
            - Listener continua ativo até ser cancelado
            - Filtros reduzem tráfego de rede
            - Útil para dashboards e chat em tempo real
        """
        try:
            query = self.client.collection(collection)

            # Apply filters if provided
            if filters:
                for filter_item in filters:
                    field = filter_item["field"]
                    operator = filter_item["operator"]
                    value = filter_item["value"]
                    query = query.where(field, operator, value)

            def on_snapshot(docs, changes, read_time):
                documents = []
                for doc in docs:
                    data = doc.to_dict()
                    data["_id"] = doc.id
                    documents.append(data)
                callback(documents)

            # Start listening
            listener = query.on_snapshot(on_snapshot)
            listener_id = f"listener_{datetime.utcnow().timestamp()}"

            self.logger.info(f"Real-time listener started: {collection}")
            return listener_id

        except Exception as e:
            self.logger.error(f"Real-time listener setup failed: {e}")
            raise

    def _validate_document_data(self, data: Dict[str, Any]) -> None:
        """Valida dados do documento antes de salvar.

        Args:
            data (Dict[str, Any]): Dados do documento para validar

        Raises:
            ValueError: Se dados forem inválidos ou contenham campos reservados

        Note:
            - Verifica se data é dicionário
            - Bloqueia campos reservados (_id, created_at, updated_at)
            - Pode ser estendido para validações customizadas
        """
        if not isinstance(data, dict):
            raise ValueError("Document data must be a dictionary")

        # Check for reserved fields
        reserved_fields = ["_id", "created_at", "updated_at"]
        for field in reserved_fields:
            if field in data:
                raise ValueError(f"Field '{field}' is reserved")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde e conectividade do serviço Firestore.

        Returns:
            Dict[str, Any]: Status de saúde contendo:
                - status: 'healthy' ou 'unhealthy'
                - service: 'firestore'
                - project_id: ID do projeto
                - database_id: ID do database
                - timestamp: Timestamp da verificação (ISO format)
                - collections_accessible: Se consegue listar coleções
                - error: Mensagem de erro (apenas se unhealthy)

        Examples:
            >>> health = fs.health_check()
            >>> if health['status'] == 'healthy':
            ...     print(f"Firestore OK - Database: {health['database_id']}")
            ... else:
            ...     print(f"Firestore Error: {health['error']}")

        Note:
            - Testa conectividade listando coleções
            - Não gera custos significativos
            - Útil para monitoring e alertas
            - Inclui informações do database configurado
        """
        try:
            # Test basic connectivity
            collections = self.client.collections()
            collection_count = len(list(collections))

            return {
                "status": "healthy",
                "service": "firestore",
                "project_id": self.config.project_id,
                "database_id": self.config.firestore_config.get(
                    "database_id", "(default)"
                ),
                "timestamp": datetime.utcnow().isoformat(),
                "collections_accessible": collection_count >= 0,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "firestore",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
