"""
🏛️ Oracle Connector - Enterprise Oracle Database Connector

Conector enterprise para Oracle Database 19c+ com recursos avançados,
segurança, compliance e alta disponibilidade para ambientes de produção críticos.

Features:
    - Oracle 19c+ (incluindo 21c, 23c, 23ai)
    - Oracle Cloud Infrastructure (OCI) Autonomous Database
    - Oracle Wallet authentication para conexões seguras
    - Connection pooling otimizado com health checks
    - Failover automático e circuit breaker pattern
    - LGPD/GDPR compliance nativo com data masking
    - Timezone management avançado
    - Audit trail completo
    - Performance monitoring e métricas
    - Thin mode otimizado para Oracle Cloud

Components:
    OracleConnector: Classe principal para conexões Oracle
    
Exceptions:
    OracleConnectionError: Erros de conectividade
    OracleQueryError: Erros de execução de queries
    OracleSecurityError: Violações de segurança

Example:
    Basic usage:
    >>> from datametria_common.database.connectors.oracle import OracleConnector, OracleConfig
    >>> config = OracleConfig(
    ...     service_name="PRODDB",
    ...     username="app_user",
    ...     password="secure_password",
    ...     wallet_location="/path/to/wallet"
    ... )
    >>> connector = OracleConnector(config)
    >>> with connector.get_connection() as conn:
    ...     cursor = conn.cursor()
    ...     cursor.execute("SELECT COUNT(*) FROM users")
    ...     result = cursor.fetchone()
    ...     print(f"Total users: {result[0]}")

Note:
    Este módulo requer Oracle Instant Client 19c+ ou superior.
    Para ambientes de produção, sempre use variáveis de ambiente
    ou HashiCorp Vault para credenciais.

Version:
    Added in: DATAMETRIA Common Libraries v1.0.0
    Last modified: 2025-01-08
    Stability: Stable - Production Ready
    
Author:
    Equipe DATAMETRIA <suporte@datametria.io>
    
License:
    MIT License - Copyright (c) 2025 DATAMETRIA LTDA
"""

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import oracledb
except ImportError:
    raise ImportError(
        "Oracle client library not found. Install oracledb: pip install oracledb"
    ) from None

from .config import OracleConfig
from .exceptions import OracleConnectionError, map_oracle_exception
from .pool import OracleConnectionPool
from .security import OracleSecurityManager
from ....core.health_check import HealthCheckMixin
from ....core.error_handler import ErrorHandlerMixin, ErrorCategory, ErrorSeverity
from ....security.centralized_logger import CentralizedEnterpriseLogger
from ....security.config import LoggingConfig


class OracleConnector(HealthCheckMixin, ErrorHandlerMixin):
    """Enterprise Oracle Database Connector com recursos avançados.

    Conector enterprise para Oracle Database 19c+ otimizado para ambientes
    de produção com alta disponibilidade, performance e segurança. Suporta
    Oracle Cloud, wallet authentication, failover automático e compliance LGPD/GDPR.

    Features:
        - Connection pooling otimizado com suporte a Oracle RAC
        - Failover automático e load balancing entre instâncias
        - Execução segura de queries com validação automática
        - Validação automática de segurança e prevenção SQL injection
        - Compliance LGPD/GDPR com auditoria e data masking
        - Logging enterprise com métricas de performance
        - Suporte a Oracle Cloud com wallet authentication
        - Configuração automática de sessão para performance
        - Monitoramento em tempo real de conexões e queries
        - Thin mode otimizado para Oracle Cloud

    Supported Oracle Versions:
        - Oracle Database 19c (19.3+)
        - Oracle Database 21c
        - Oracle Database 23c
        - Oracle Autonomous Database (OCI)
        - Oracle Cloud Infrastructure

    Performance Features:
        - Thin mode para melhor performance em Oracle Cloud
        - Statement caching automático
        - Connection reuse para reduzir overhead
        - Result set streaming
        - Automatic session configuration

    Security Features:
        - Oracle Wallet support para conexões seguras
        - Fine-grained access control
        - Data masking para dados sensíveis
        - Audit trail completo
        - SQL injection prevention

    Examples:
        Basic usage:
        >>> config = OracleConfig(
        ...     service_name="PRODDB",
        ...     username="app_user",
        ...     password="secure_password"
        ... )
        >>> connector = OracleConnector(config)
        >>> connector.connect()
        >>> 
        >>> # Query com bind variables
        >>> results = connector.execute_query(
        ...     "SELECT user_id, username FROM users WHERE active = :active",
        ...     {"active": 1}
        ... )
        >>> 
        >>> # Context manager usage
        >>> with connector.get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT COUNT(*) FROM users")
        ...     result = cursor.fetchone()

    Attributes:
        config (OracleConfig): Configuração completa do Oracle Database
            incluindo parâmetros de conexão, pool, segurança e performance.
        logger (logging.Logger): Logger configurado para auditoria enterprise
            com níveis DEBUG, INFO, WARNING, ERROR e CRITICAL.
        security_manager (OracleSecurityManager): Gerenciador de segurança
            responsável por validação de queries, data masking e compliance.
        pool (Optional[OracleConnectionPool]): Pool de conexões otimizado
            com suporte a RAC, failover e load balancing automático.
        connection_count (int): Contador total de conexões estabelecidas
            desde a inicialização do conector.
        query_count (int): Contador total de queries executadas com
            métricas de performance e tempo de execução.
        error_count (int): Contador de erros ocorridos para monitoramento
            e alertas de saúde do sistema.

    Note:
        Este conector é otimizado para ambientes enterprise e requer
        Oracle Client 19c+ instalado. Para máxima performance, configure
        adequadamente baseado na carga esperada.
    """

    def __init__(self, config: OracleConfig) -> None:
        """Inicializa o conector Oracle Database.

        Configura o conector com parâmetros de conexão, segurança e pool.
        Inicializa métricas de monitoramento e logging enterprise.

        Args:
            config (OracleConfig): Configuração completa do Oracle Database
                contendo service_name, credenciais e parâmetros
                de pool e segurança.

        Raises:
            OracleConfigError: Se a configuração for inválida
            ImportError: Se o driver Oracle não estiver instalado

        Example:
            >>> config = OracleConfig(
            ...     service_name="PRODDB",
            ...     username="app_user",
            ...     password="secure_pass",
            ...     pool_max_size=20
            ... )
            >>> connector = OracleConnector(config)
        """
        self.config = config
        
        # Initialize Enterprise Logger with environment-based configuration
        # Uses LoggingConfig.from_env() for enterprise-grade configuration management
        logging_config = LoggingConfig.from_env(prefix="LOG_")
        logging_config.service_name = "OracleConnector"
        
        self.logger = CentralizedEnterpriseLogger(logging_config)
        
        self.security_manager = OracleSecurityManager(config)
        self.pool: Optional[OracleConnectionPool] = None
        self._connection = None
        self.service_name = "OracleConnector"
        self.version = "1.0.0"

        # Metrics
        self.connection_count = 0
        self.query_count = 0
        self.error_count = 0
        
        # Initialize mixins
        HealthCheckMixin.__init__(self)
        ErrorHandlerMixin.__init__(self)

    def connect(self) -> None:
        """Estabelece conexão com Oracle Database.

        Conecta ao Oracle Database usando pool de conexões (se configurado)
        ou conexão direta. Detecta automaticamente Oracle Wallet e configura
        parâmetros de sessão para performance otimizada.

        Connection Strategy:
            1. Detecta se Oracle Wallet está disponível
            2. Para wallet: usa conexão direta (pool não suportado)
            3. Para conexões normais: usa pool se configurado
            4. Configura Oracle Client e ambiente automaticamente
            5. Aplica configurações de sessão otimizadas

        Raises:
            OracleConnectionError: Se não conseguir conectar ao database
            OracleSecurityError: Se falhar na validação de segurança
            OracleConfigError: Se a configuração for inválida

        Example:
            >>> connector = OracleConnector(config)
            >>> connector.connect()
            >>> # Conexão estabelecida com sucesso
        """
        try:
            # Verifica se wallet está configurado
            wallet_location = self.config.wallet_location or os.getenv(
                "ORACLE_WALLET_LOCATION"
            )

            # Para wallet, sempre usar conexão direta (pool não suportado)
            if wallet_location and os.path.exists(wallet_location):
                self.logger.info(
                    "Wallet detectado - usando conexão direta",
                    wallet_location=wallet_location,
                    compliance_tags=["LGPD", "GDPR", "SECURITY"]
                )
                self._connect_direct()
            elif self.config.pool_max_size > 1:
                self._connect_with_pool()
            else:
                self._connect_direct()

            self.connection_count += 1
            self.logger.info(
                "Connected to Oracle Database",
                dsn=self.config.dsn,
                service_name=self.config.service_name,
                connection_type="wallet" if wallet_location else "standard",
                pool_enabled=self.pool is not None,
                compliance_tags=["LGPD", "GDPR", "AUDIT"]
            )

        except oracledb.Error as e:
            error_code = e.args[0].code if hasattr(e.args[0], "code") else None
            mapped_exception = map_oracle_exception(error_code, str(e))
            self.handle_error(mapped_exception, ErrorCategory.DATABASE, ErrorSeverity.HIGH)
            raise mapped_exception from e

    def _connect_with_pool(self) -> None:
        """Conecta usando connection pool otimizado.

        Cria e configura um pool de conexões Oracle com suporte a RAC,
        failover automático e load balancing. O pool é otimizado para
        alta concorrência e performance enterprise.

        Raises:
            OracleConnectionError: Se falhar ao criar o pool
            OracleConfigError: Se os parâmetros do pool forem inválidos
        """
        self.pool = OracleConnectionPool(self.config)
        self.pool.create_pool()

    def _connect_direct(self) -> None:
        """Conecta diretamente sem pool de conexões.

        Estabelece uma conexão direta ao Oracle Database para cenários
        de baixa concorrência, testes ou quando wallet está configurado.
        Configura automaticamente Oracle Client e ambiente.

        Process:
            1. Configura Oracle Instant Client se disponível
            2. Detecta e configura Oracle Wallet se presente
            3. Estabelece conexão usando thin mode (recomendado)
            4. Aplica configurações de sessão otimizadas

        Raises:
            OracleConnectionError: Se falhar ao conectar diretamente
            OracleSecurityError: Se falhar na autenticação
        """
        import os

        # Obtém configurações do ambiente ou usa padrões
        # ORACLE_CLIENT_PATH: Caminho para Oracle Instant Client
        oracle_client_path = os.getenv(
            "ORACLE_CLIENT_PATH", r"D:\Tools\Oracle_Client\instantclient_23_8"
        )

        # ORACLE_WALLET_LOCATION: Caminho para Oracle Wallet (OCI)
        wallet_location = self.config.wallet_location or os.getenv(
            "ORACLE_WALLET_LOCATION"
        )

        # Configura Oracle Client se necessário
        if oracle_client_path and os.path.exists(oracle_client_path):
            self._setup_oracle_client(oracle_client_path)

        # Configura wallet se disponível
        if wallet_location and os.path.exists(wallet_location):
            self._setup_wallet_connection(wallet_location)
        else:
            self._setup_standard_connection()

    def _setup_oracle_client(self, client_path: str) -> None:
        """Configura Oracle Instant Client.

        Configura o ambiente para Oracle Instant Client, adicionando
        o caminho ao PATH do sistema e preparando para thin mode.

        Args:
            client_path (str): Caminho para Oracle Instant Client

        Note:
            Thin mode é preferido para Oracle Cloud por ser mais confiável
            e não requerer bibliotecas nativas complexas.
        """
        import os

        try:
            # Adiciona ao PATH se necessário
            current_path = os.environ.get("PATH", "")
            if client_path not in current_path:
                os.environ["PATH"] = f"{client_path};{current_path}"

            # Para Oracle Cloud, usar thin mode é mais confiável
            # Thick mode será usado apenas se thin mode não funcionar
            self.logger.info(
                "Configurado para usar Oracle thin mode (recomendado para Oracle Cloud)"
            )

        except Exception as e:
            self.logger.warning(f"Erro ao configurar Oracle Client: {e}")

    def _setup_wallet_connection(self, wallet_location: str) -> None:
        """Configura conexão usando Oracle Wallet.

        Estabelece conexão segura usando Oracle Wallet para autenticação
        sem expor credenciais. Usado principalmente para Oracle Cloud.

        Args:
            wallet_location (str): Caminho para o diretório do wallet

        Process:
            1. Configura TNS_ADMIN para o wallet
            2. Usa credenciais do config com service name do wallet
            3. Estabelece conexão usando thin mode com config_dir
            4. Fallback para conexão padrão se falhar

        Raises:
            OracleConnectionError: Se falhar na conexão com wallet

        Note:
            Wallet deve conter sqlnet.ora e tnsnames.ora válidos.
        """
        import os

        try:
            # Configura TNS_ADMIN para o wallet
            os.environ["TNS_ADMIN"] = wallet_location
            self.logger.info(f"Wallet configurado: {wallet_location}")

            # Para wallet, usar config_dir para especificar o diretório
            self._connection = oracledb.connect(
                user=self.config.username,
                password=self.config.password,
                dsn=self.config.dsn,
                config_dir=wallet_location
            )

            self.logger.info(
                "Conexão com wallet estabelecida",
                wallet_location=wallet_location,
                dsn=self.config.dsn,
                compliance_tags=["LGPD", "GDPR", "SECURITY"]
            )

        except oracledb.Error as e:
            self.logger.error(f"Erro na conexão com wallet: {e}")
            raise

    def _setup_standard_connection(self) -> None:
        """Configura conexão padrão sem wallet.

        Estabelece conexão Oracle usando credenciais tradicionais
        (usuário/senha) sem wallet authentication.

        Process:
            1. Obtém parâmetros de conexão da configuração
            2. Remove parâmetros de wallet se existirem
            3. Estabelece conexão usando oracledb.connect()
            4. Configura sessão com parâmetros otimizados

        Raises:
            OracleConnectionError: Se falhar na conexão padrão
        """
        try:
            params = self.config.get_connection_params()

            # Remove parâmetros de wallet se existirem
            wallet_params = ["config_dir", "wallet_location", "wallet_password"]
            for param in wallet_params:
                params.pop(param, None)

            self._connection = oracledb.connect(**params)
            self.logger.info(
                "Conexão padrão estabelecida",
                dsn=self.config.dsn,
                compliance_tags=["LGPD", "GDPR", "AUDIT"]
            )

        except oracledb.Error as e:
            self.logger.error(f"Erro na conexão padrão: {e}")
            raise

        # Configure session parameters
        self._configure_session(self._connection)

    def _configure_session(self, connection) -> None:
        """Configura parâmetros otimizados da sessão Oracle.

        Aplica configurações de sessão otimizadas para performance,
        compliance e funcionalidade em conexões Oracle.

        Configuration Applied:
            - NLS_DATE_FORMAT: Formato ISO padrão para consistência
            - NLS_TIMESTAMP_FORMAT: Formato timestamp com frações
            - SQL_TRACE: Habilitado se auditoria estiver ativa
            - arraysize: Otimizado para operações batch

        Args:
            connection: Conexão Oracle válida para configuração

        Note:
            Falhas na configuração são logadas como warning mas não
            interrompem o processo de conexão.
        """
        cursor = connection.cursor()

        try:
            # Set session parameters for performance
            cursor.execute(
                "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'"
            )
            cursor.execute(
                "ALTER SESSION SET NLS_TIMESTAMP_FORMAT = " "'YYYY-MM-DD HH24:MI:SS.FF'"
            )

            # Enable SQL trace if needed
            if self.config.audit_enabled:
                cursor.execute("ALTER SESSION SET SQL_TRACE = TRUE")

            # Set arraysize for better performance
            cursor.arraysize = self.config.arraysize

        except oracledb.Error as e:
            self.logger.warning("Failed to configure session: %s", e)
        finally:
            cursor.close()

    @contextmanager
    def get_connection(self):
        """Context manager para obter conexão Oracle.

        Fornece uma conexão Oracle de forma segura, garantindo que seja
        retornada ao pool após o uso. Trata automaticamente erros de
        conexão e mapeia exceções Oracle para exceções customizadas.

        Yields:
            oracledb.Connection: Conexão Oracle ativa e configurada

        Raises:
            OracleConnectionError: Se não houver conexão disponível
            OracleTimeoutError: Se timeout na aquisição da conexão

        Example:
            >>> with connector.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT 1 FROM dual")
        """
        connection = None
        try:
            if self.pool:
                connection = self.pool.acquire()
            else:
                connection = self._connection

            if not connection:
                raise OracleConnectionError("No connection available")

            yield connection

        except oracledb.Error as e:
            error_code = e.args[0].code if hasattr(e.args[0], "code") else None
            self.error_count += 1
            raise map_oracle_exception(error_code, str(e)) from e
        finally:
            if self.pool and connection:
                self.pool.release(connection)

    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        fetch_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Executa query SELECT com validação de segurança.

        Executa uma query SELECT no Oracle Database com validação automática
        de segurança, prevenção de SQL injection e logging de auditoria.
        Retorna resultados em formato de dicionário para facilitar o uso.

        Args:
            sql (str): Query SQL SELECT a ser executada. Deve usar bind
                variables (:param) para parâmetros dinâmicos.
            params (Optional[Dict[str, Any]]): Dicionário com parâmetros
                nomeados para bind variables. Defaults to None.
            fetch_size (Optional[int]): Tamanho do array fetch para
                otimização de performance. Defaults to None (usa config).

        Returns:
            List[Dict[str, Any]]: Lista de dicionários onde cada dicionário
                representa uma linha com colunas como chaves.

        Raises:
            OracleSecurityError: Se a query falhar na validação de segurança
            OracleQueryError: Se houver erro na execução da query
            OracleConnectionError: Se não houver conexão disponível

        Example:
            >>> results = connector.execute_query(
            ...     "SELECT id, name FROM users WHERE active = :active",
            ...     {"active": 1},
            ...     fetch_size=1000
            ... )
            >>> for row in results:
            ...     print(f"ID: {row['ID']}, Name: {row['NAME']}")
        """
        start_time = time.time()

        try:
            # Security validation
            self.security_manager.validate_query(sql, params)

            with self.get_connection() as conn:
                cursor = conn.cursor()

                if fetch_size:
                    cursor.arraysize = fetch_size

                # Execute query
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                # Fetch results
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # Convert to dict format
                results = [dict(zip(columns, row)) for row in rows]

                cursor.close()

                self.query_count += 1
                execution_time = time.time() - start_time

                self.logger.info(
                    "Query executed successfully",
                    query_type="SELECT",
                    rows_returned=len(results),
                    execution_time_ms=round(execution_time * 1000, 2),
                    has_params=params is not None,
                    compliance_tags=["LGPD", "GDPR", "AUDIT"]
                )

                return results

        except oracledb.Error as e:
            error_code = e.args[0].code if hasattr(e.args[0], "code") else None
            self.error_count += 1
            mapped_exception = map_oracle_exception(error_code, str(e))
            self.handle_error(mapped_exception, ErrorCategory.DATABASE, ErrorSeverity.MEDIUM)
            raise mapped_exception from e

    def execute_dml(
        self,
        sql: str,
        params: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        commit: bool = True,
    ) -> int:
        """Executa operações DML (INSERT, UPDATE, DELETE) com segurança.

        Executa statements DML no Oracle Database com validação de segurança,
        suporte a operações batch e controle transacional. Inclui logging
        de auditoria para compliance LGPD/GDPR.

        Args:
            sql (str): Statement DML a ser executado. Deve usar bind
                variables (:param) para parâmetros dinâmicos.
            params (Optional[Union[Dict[str, Any], List[Dict[str, Any]]]):
                Parâmetros para o statement. Dict para operação única,
                List[Dict] para operações batch. Defaults to None.
            commit (bool): Se deve fazer commit automático da transação.
                Defaults to True.

        Returns:
            int: Número total de linhas afetadas pela operação.

        Raises:
            OracleSecurityError: Se o DML falhar na validação de segurança
            OracleQueryError: Se houver erro na execução do statement
            OracleConnectionError: Se não houver conexão disponível

        Example:
            >>> # Operação única
            >>> affected = connector.execute_dml(
            ...     "UPDATE users SET last_login = :login_time WHERE id = :user_id",
            ...     {"login_time": datetime.now(), "user_id": 123}
            ... )
            >>>
            >>> # Operação batch
            >>> users_data = [
            ...     {"name": "João", "email": "joao@example.com"},
            ...     {"name": "Maria", "email": "maria@example.com"}
            ... ]
            >>> affected = connector.execute_dml(
            ...     "INSERT INTO users (name, email) VALUES (:name, :email)",
            ...     users_data
            ... )
        """
        start_time = time.time()

        try:
            # Security validation
            self.security_manager.validate_dml(sql, params)

            with self.get_connection() as conn:
                cursor = conn.cursor()

                if isinstance(params, list):
                    # Batch execution
                    cursor.executemany(sql, params)
                    affected_rows = cursor.rowcount
                elif params:
                    cursor.execute(sql, params)
                    affected_rows = cursor.rowcount
                else:
                    cursor.execute(sql)
                    affected_rows = cursor.rowcount

                if commit:
                    conn.commit()

                cursor.close()

                self.query_count += 1
                execution_time = time.time() - start_time

                self.logger.info(
                    "DML executed successfully",
                    operation_type="DML",
                    affected_rows=affected_rows,
                    execution_time_ms=round(execution_time * 1000, 2),
                    is_batch=isinstance(params, list),
                    committed=commit,
                    compliance_tags=["LGPD", "GDPR", "AUDIT", "DATA_MODIFICATION"]
                )

                return affected_rows

        except oracledb.Error as e:
            error_code = e.args[0].code if hasattr(e.args[0], "code") else None
            self.error_count += 1
            raise map_oracle_exception(error_code, str(e)) from e

    def execute_plsql(
        self, plsql: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executa PL/SQL procedures ou functions com segurança.

        Executa código PL/SQL (procedures, functions, blocos anônimos) no
        Oracle Database com validação de segurança e tratamento automático
        de parâmetros de entrada e saída.

        Args:
            plsql (str): Código PL/SQL a ser executado. Pode ser uma chamada
                de procedure, function ou bloco anônimo completo.
            params (Optional[Dict[str, Any]]): Dicionário com parâmetros de
                entrada e saída. Use oracledb.Cursor.var() para parâmetros
                de saída. Defaults to None.

        Returns:
            Dict[str, Any]: Dicionário com os valores dos parâmetros de saída
                após a execução do PL/SQL.

        Raises:
            OracleSecurityError: Se o PL/SQL falhar na validação de segurança
            OracleQueryError: Se houver erro na execução do PL/SQL
            OracleConnectionError: Se não houver conexão disponível

        Example:
            >>> # Chamada de procedure com parâmetros de saída
            >>> cursor = connector.get_connection().cursor()
            >>> out_param = cursor.var(oracledb.NUMBER)
            >>> result = connector.execute_plsql(
            ...     "BEGIN calculate_total(:input_val, :output_val); END;",
            ...     {"input_val": 100, "output_val": out_param}
            ... )
            >>> total = result["output_val"]
        """
        try:
            # Security validation
            self.security_manager.validate_plsql(plsql, params)

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Execute PL/SQL
                if params:
                    cursor.execute(plsql, params)
                else:
                    cursor.execute(plsql)

                # Get output parameters
                output_params = {}
                if params:
                    for key, value in params.items():
                        if hasattr(value, "getvalue"):
                            output_params[key] = value.getvalue()

                cursor.close()

                return output_params

        except oracledb.Error as e:
            error_code = e.args[0].code if hasattr(e.args[0], "code") else None
            self.error_count += 1
            raise map_oracle_exception(error_code, str(e)) from e

    def disconnect(self) -> None:
        """Desconecta do Oracle Database.

        Fecha todas as conexões ativas e libera recursos do pool.
        Executa cleanup gracioso garantindo que não há vazamentos.

        Process:
            1. Fecha connection pool se ativo
            2. Fecha conexão direta se ativa
            3. Limpa recursos e métricas
            4. Loga operações para auditoria

        Example:
            >>> connector = OracleConnector(config)
            >>> connector.connect()
            >>> # ... usar o conector ...
            >>> connector.disconnect()
        """
        try:
            if self.pool:
                self.pool.close()
                self.pool = None
                self.logger.info(
                    "Connection pool closed",
                    total_connections=self.connection_count,
                    total_queries=self.query_count,
                    total_errors=self.error_count,
                    compliance_tags=["LGPD", "GDPR", "AUDIT"]
                )

            if self._connection:
                self._connection.close()
                self._connection = None
                self.logger.info(
                    "Direct connection closed",
                    total_connections=self.connection_count,
                    total_queries=self.query_count,
                    total_errors=self.error_count,
                    compliance_tags=["LGPD", "GDPR", "AUDIT"]
                )

        except Exception as e:
            self.logger.warning(f"Warning during disconnect: {e}")

    def close(self) -> None:
        """Fecha conexões e limpa recursos.

        Fecha todas as conexões ativas e libera recursos do pool.
        Deve ser chamado ao finalizar o uso do conector.

        Example:
            >>> connector = OracleConnector(config)
            >>> connector.connect()
            >>> # ... usar o conector ...
            >>> connector.close()
        """
        self.disconnect()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    async def _check_component_health(self) -> Dict[str, Any]:
        """Check Oracle Database component health.
        
        Returns:
            Dict with Oracle-specific health status (boolean values for HealthCheckMixin)
        """
        health_status = {}
        
        try:
            # Check database connection (return boolean)
            if self.pool:
                health_status["connection_pool"] = True
            elif self._connection:
                health_status["direct_connection"] = True
            else:
                health_status["connection"] = False
                return health_status
            
            # Test database connectivity with simple query (return boolean)
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 FROM dual")
                    result = cursor.fetchone()
                    cursor.close()
                    health_status["database_query"] = result is not None
            except Exception as e:
                health_status["database_query"] = False
            
            # Check security manager (return boolean)
            health_status["security_manager"] = self.security_manager is not None
            
            # Check error rate (return boolean - healthy if < 10% errors)
            error_rate = self.error_count / max(self.query_count, 1)
            health_status["low_error_rate"] = error_rate < 0.1
            
        except Exception as e:
            health_status["health_check"] = False
        
        return health_status
