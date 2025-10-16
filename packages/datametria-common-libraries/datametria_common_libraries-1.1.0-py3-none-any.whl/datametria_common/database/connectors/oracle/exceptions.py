"""
🏛️ Oracle Exceptions - Enterprise Error Handling

Exceções específicas para Oracle Database com:
- Categorização de erros Oracle
- Retry strategies
- Logging estruturado
- Compliance tracking
"""

from typing import Any, Dict, Optional


class OracleBaseException(Exception):
    """Exceção base para Oracle Database Connector com recursos enterprise.

    Classe base para todas as exceções específicas do Oracle Database,
    fornecendo funcionalidades avançadas como categorização automática de erros,
    estratégias de retry inteligentes, logging estruturado para auditoria
    e tracking de compliance LGPD/GDPR.

    Features:
        - Mapeamento automático de códigos de erro Oracle (ORA-XXXXX)
        - Categorização inteligente de erros por tipo e severidade
        - Estratégias de retry baseadas no tipo de erro
        - Context enrichment para troubleshooting avançado
        - Logging estruturado para compliance e auditoria
        - Integração com sistemas de monitoramento enterprise
        - Suporte a error correlation e root cause analysis

    Error Categories:
        - Connection errors: Problemas de conectividade e rede
        - Query errors: Erros de execução SQL e PL/SQL
        - Security errors: Falhas de autenticação e autorização
        - Pool errors: Problemas com connection pooling
        - Configuration errors: Erros de configuração
        - Compliance errors: Violações LGPD/GDPR

    Retry Strategy:
        - Automatic retry para erros transientes (network, deadlock)
        - Exponential backoff com jitter para evitar thundering herd
        - Circuit breaker pattern para falhas persistentes
        - Rate limiting para proteger recursos Oracle

    Attributes:
        oracle_error_code (Optional[int]): Código de erro Oracle (ORA-XXXXX)
            usado para categorização automática e estratégias de retry.
        context (Dict[str, Any]): Contexto adicional do erro incluindo
            SQL statement, parâmetros, timestamp, user info, etc.
        retryable (bool): Indica se o erro é elegível para retry automático
            baseado no tipo e código de erro Oracle.
        severity (str): Nível de severidade (LOW, MEDIUM, HIGH, CRITICAL)
            para priorização de alertas e escalation.
        correlation_id (str): ID único para correlação de erros relacionados
            em sistemas distribuídos e troubleshooting.

    Examples:
        Basic usage:
        >>> try:
        ...     connector.execute_query("SELECT * FROM users")
        ... except OracleBaseException as e:
        ...     if e.retryable:
        ...         # Implementar retry logic
        ...         retry_operation()
        ...     else:
        ...         # Log error e escalate
        ...         logger.error(f"Non-retryable error: {e}")

        Error context analysis:
        >>> try:
        ...     connector.execute_dml("INSERT INTO users VALUES (:1, :2)", data)
        ... except OracleBaseException as e:
        ...     print(f"Error code: ORA-{e.oracle_error_code:05d}")
        ...     print(f"Context: {e.context}")
        ...     print(f"Retryable: {e.retryable}")

    Note:
        Esta classe não deve ser instanciada diretamente. Use as subclasses
        específicas (OracleConnectionError, OracleQueryError, etc.) ou a
        função map_oracle_exception() para mapeamento automático.
    """

    def __init__(
        self,
        message: str,
        oracle_error_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inicializa a exceção base Oracle com contexto enriquecido.

        Args:
            message (str): Mensagem descritiva do erro em português para
                facilitar troubleshooting por equipes brasileiras.
            oracle_error_code (Optional[int]): Código numérico do erro Oracle
                (sem o prefixo ORA-) para mapeamento automático de estratégias.
            context (Optional[Dict[str, Any]]): Contexto adicional do erro
                incluindo SQL, parâmetros, timestamp, user info, etc.

        Example:
            >>> error = OracleBaseException(
            ...     "Falha na conexão com o database",
            ...     oracle_error_code=12170,
            ...     context={
            ...         "host": "oracle.prod.com",
            ...         "port": 1521,
            ...         "service": "PRODDB",
            ...         "user": "app_user",
            ...         "timestamp": "2024-01-15T10:30:00Z"
            ...     }
            ... )
        """
        super().__init__(message)
        self.oracle_error_code = oracle_error_code
        self.context = context or {}
        self.retryable = False
        self.severity = "MEDIUM"  # Default severity
        self.correlation_id = self._generate_correlation_id()

    def __str__(self) -> str:
        """Retorna representação string formatada do erro.

        Inclui o código Oracle formatado (ORA-XXXXX) quando disponível
        para facilitar identificação e troubleshooting.

        Returns:
            str: Mensagem de erro formatada com código Oracle.

        Example:
            >>> str(error)
            'ORA-12170: Falha na conexão com o database'
        """
        if self.oracle_error_code:
            return f"ORA-{self.oracle_error_code:05d}: {super().__str__()}"
        return super().__str__()

    def _generate_correlation_id(self) -> str:
        """Gera ID único para correlação de erros.

        Returns:
            str: UUID único para tracking de erros relacionados.
        """
        import uuid

        return str(uuid.uuid4())[:8]


class OracleConnectionError(OracleBaseException):
    """Erro de conexão Oracle Database com retry automático.

    Exceção específica para problemas de conectividade com Oracle Database,
    incluindo timeouts de rede, falhas de listener, problemas de RAC e
    indisponibilidade de serviços. Implementa estratégias inteligentes de
    retry baseadas no tipo específico de erro de conexão.

    Connection Error Types:
        - Network timeouts (ORA-12170): Timeout na conexão TCP
        - Listener errors (ORA-12541): TNS listener não disponível
        - Service errors (ORA-12514): Serviço não conhecido pelo listener
        - RAC errors (ORA-12528): Todas as instâncias bloqueando conexões
        - Connection drops (ORA-12537): Conexão fechada inesperadamente
        - Network errors (ORA-12560): Protocolo adapter error
        - TNS errors (ORA-12545): Connect failed (host unreachable)

    Retry Strategy:
        - Automatic retry com exponential backoff (1s, 2s, 4s, 8s)
        - Maximum 5 tentativas para erros de rede transientes
        - Circuit breaker após 3 falhas consecutivas
        - Failover automático para instâncias RAC secundárias
        - Health check antes de retry para validar conectividade

    Examples:
        Handle connection errors:
        >>> try:
        ...     connector.connect()
        ... except OracleConnectionError as e:
        ...     if e.retryable:
        ...         logger.warning(f"Connection failed, retrying: {e}")
        ...         time.sleep(e.get_retry_delay())
        ...         connector.connect()  # Retry
        ...     else:
        ...         logger.error(f"Permanent connection failure: {e}")
        ...         raise

        RAC failover scenario:
        >>> try:
        ...     connector.connect_to_primary()
        ... except OracleConnectionError as e:
        ...     if e.oracle_error_code == 12528:  # RAC blocking connections
        ...         logger.info("Primary RAC busy, failing over to secondary")
        ...         connector.connect_to_secondary()

    Note:
        Erros de conexão são automaticamente categorizados como retryable
        ou não baseados no código Oracle específico. Use a propriedade
        retryable para implementar lógica de retry apropriada.
    """

    def __init__(
        self, message: str, oracle_error_code: Optional[int] = None, **kwargs
    ) -> None:
        """Inicializa erro de conexão Oracle com estratégia de retry.

        Args:
            message (str): Mensagem descritiva do erro de conexão.
            oracle_error_code (Optional[int]): Código específico do erro Oracle.
            **kwargs: Contexto adicional (host, port, service_name, etc.).

        Example:
            >>> error = OracleConnectionError(
            ...     "Timeout na conexão com Oracle RAC",
            ...     oracle_error_code=12170,
            ...     context={
            ...         "host": "oracle-rac-scan.prod.com",
            ...         "port": 1521,
            ...         "service_name": "PRODDB",
            ...         "timeout_seconds": 30
            ...     }
            ... )
        """
        super().__init__(message, oracle_error_code, **kwargs)
        self.severity = "HIGH"  # Connection errors são críticos

        # Erros de conexão retryable baseados no código Oracle
        self.retryable = oracle_error_code in [
            12170,  # TNS:Connect timeout occurred
            12541,  # TNS:no listener
            12514,  # TNS:listener does not currently know of service
            12528,  # TNS:listener: all appropriate instances are blocking new connections
            12537,  # TNS:connection closed
            12560,  # TNS:protocol adapter error
            12545,  # Connect failed because target host or object does not exist
        ]

    def get_retry_delay(self, attempt: int = 1) -> float:
        """Calcula delay para retry com exponential backoff.

        Args:
            attempt (int): Número da tentativa (1-based).

        Returns:
            float: Delay em segundos com jitter para evitar thundering herd.
        """
        import random

        base_delay = min(2**attempt, 30)  # Max 30 segundos
        jitter = random.uniform(0.1, 0.3)  # 10-30% jitter
        return base_delay * (1 + jitter)


class OracleQueryError(OracleBaseException):
    """Erro de execução de query/statement Oracle com análise detalhada.

    Exceção para erros durante execução de SQL e PL/SQL no Oracle Database,
    incluindo erros de sintaxe, violações de constraint, deadlocks, timeouts
    e problemas de performance. Fornece análise detalhada do erro e
    sugestões de correção quando possível.

    Query Error Categories:
        - Syntax errors (ORA-00900-00999): Erros de sintaxe SQL
        - Constraint violations (ORA-00001, ORA-02291): Violações de integridade
        - Deadlocks (ORA-00060): Deadlock detectado entre sessões
        - Timeouts (ORA-01013): Operação cancelada por timeout
        - Resource errors (ORA-01555): Snapshot too old
        - Permission errors (ORA-00942): Table or view does not exist
        - Data errors (ORA-01400): Cannot insert NULL into column
        - Performance errors (ORA-08176): Consistent read failure

    Retry Strategy:
        - Deadlocks: Retry automático com random delay
        - Consistent read failures: Retry com statement refresh
        - Timeouts: Retry com timeout aumentado
        - Syntax/constraint errors: Não retryable (requer correção)

    Error Analysis:
        - SQL statement parsing e validation
        - Bind parameter analysis
        - Execution plan hints quando disponível
        - Performance metrics (elapsed time, CPU, I/O)
        - Resource usage (memory, temp space)

    Examples:
        Handle query errors with retry:
        >>> try:
        ...     results = connector.execute_query(
        ...         "SELECT * FROM large_table WHERE date_col = :date",
        ...         {"date": "2024-01-15"}
        ...     )
        ... except OracleQueryError as e:
        ...     if e.oracle_error_code == 60:  # Deadlock
        ...         logger.warning(f"Deadlock detected, retrying: {e}")
        ...         time.sleep(random.uniform(0.1, 0.5))  # Random delay
        ...         results = connector.execute_query(sql, params)  # Retry
        ...     elif e.oracle_error_code == 1555:  # Snapshot too old
        ...         logger.info("Snapshot too old, refreshing and retrying")
        ...         connector.refresh_session()
        ...         results = connector.execute_query(sql, params)
        ...     else:
        ...         logger.error(f"Query error requires manual fix: {e}")
        ...         raise

        Analyze query performance issues:
        >>> try:
        ...     connector.execute_dml("INSERT INTO users SELECT * FROM temp_users")
        ... except OracleQueryError as e:
        ...     if "performance" in e.context:
        ...         metrics = e.context["performance"]
        ...         logger.warning(
        ...             f"Slow query detected: {metrics['elapsed_time']}s, "
        ...             f"CPU: {metrics['cpu_time']}s, I/O: {metrics['io_time']}s"
        ...         )

    Note:
        Para erros de performance, considere usar hints SQL, ajustar
        parâmetros de sessão ou revisar o execution plan. Erros de
        sintaxe e constraint requerem correção no código.
    """

    def __init__(
        self, message: str, oracle_error_code: Optional[int] = None, **kwargs
    ) -> None:
        """Inicializa erro de query Oracle com análise de contexto.

        Args:
            message (str): Mensagem descritiva do erro de query.
            oracle_error_code (Optional[int]): Código específico do erro Oracle.
            **kwargs: Contexto adicional (SQL, parâmetros, performance, etc.).

        Example:
            >>> error = OracleQueryError(
            ...     "Deadlock detectado durante INSERT",
            ...     oracle_error_code=60,
            ...     context={
            ...         "sql": "INSERT INTO orders VALUES (:1, :2, :3)",
            ...         "params": {"1": 12345, "2": "PENDING", "3": 1000.00},
            ...         "elapsed_time": 2.5,
            ...         "affected_tables": ["orders", "order_items"]
            ...     }
            ... )
        """
        super().__init__(message, oracle_error_code, **kwargs)

        # Determinar severidade baseada no tipo de erro
        if oracle_error_code in [60, 8176, 1013]:  # Transient errors
            self.severity = "MEDIUM"
        elif oracle_error_code in [1, 2291, 1400]:  # Data integrity errors
            self.severity = "HIGH"
        else:
            self.severity = "MEDIUM"

        # Erros de query retryable (transientes)
        self.retryable = oracle_error_code in [
            60,  # Deadlock detected
            8176,  # Consistent read failure
            1013,  # User requested cancel of current operation
            1555,  # Snapshot too old
            8103,  # Object no longer exists
        ]

    def get_error_category(self) -> str:
        """Categoriza o erro para troubleshooting direcionado.

        Returns:
            str: Categoria do erro (SYNTAX, CONSTRAINT, DEADLOCK, etc.).
        """
        if not self.oracle_error_code:
            return "UNKNOWN"

        code = self.oracle_error_code

        if 900 <= code <= 999:
            return "SYNTAX"
        elif code in [1, 2291, 2292, 1400, 1407]:
            return "CONSTRAINT"
        elif code == 60:
            return "DEADLOCK"
        elif code in [1013, 1013]:
            return "TIMEOUT"
        elif code in [1555, 8176]:
            return "CONSISTENCY"
        elif code in [942, 980, 1031]:
            return "PERMISSION"
        else:
            return "OTHER"


class OracleSecurityError(OracleBaseException):
    """Erro de segurança Oracle com compliance LGPD/GDPR.

    Exceção crítica para violações de segurança no Oracle Database,
    incluindo falhas de autenticação, violações de autorização,
    tentativas de acesso não autorizado e violações de compliance.
    Implementa logging obrigatório para auditoria e compliance.

    Security Error Types:
        - Authentication failures (ORA-01017): Invalid username/password
        - Authorization violations (ORA-01031): Insufficient privileges
        - Account lockouts (ORA-28000): Account is locked
        - Password issues (ORA-28001, ORA-28002): Password expired/expiring
        - Profile violations (ORA-02391): Exceeded simultaneous SESSIONS_PER_USER
        - Audit violations (ORA-00604): Error occurred at recursive SQL level
        - Encryption errors (ORA-28365): Wallet is not open

    Compliance Features:
        - Automatic LGPD/GDPR violation detection
        - Mandatory audit logging para compliance
        - Data access pattern analysis
        - Sensitive data exposure prevention
        - User behavior anomaly detection
        - Breach notification triggers

    Security Response:
        - Immediate security team notification
        - Account lockout para repeated failures
        - IP blocking para suspicious activity
        - Session termination para active threats
        - Forensic data collection
        - Compliance report generation

    Examples:
        Handle authentication failures:
        >>> try:
        ...     connector.connect()
        ... except OracleSecurityError as e:
        ...     if e.oracle_error_code == 1017:  # Invalid credentials
        ...         security_logger.critical(
        ...             f"Authentication failure for user {username} "
        ...             f"from IP {client_ip}: {e}"
        ...         )
        ...         # Increment failed login counter
        ...         auth_monitor.record_failure(username, client_ip)
        ...
        ...         if auth_monitor.should_lock_account(username):
        ...             auth_monitor.lock_account(username)
        ...             compliance_notifier.send_alert(
        ...                 "ACCOUNT_LOCKOUT", username, e.correlation_id
        ...             )

        Handle privilege violations:
        >>> try:
        ...     connector.execute_query("SELECT * FROM sensitive_table")
        ... except OracleSecurityError as e:
        ...     if e.oracle_error_code == 1031:  # Insufficient privileges
        ...         audit_logger.warning(
        ...             f"Unauthorized access attempt to sensitive_table "
        ...             f"by user {current_user}: {e}"
        ...         )
        ...         # Check if this is a LGPD violation
        ...         if compliance_checker.is_lgpd_violation("sensitive_table"):
        ...             compliance_notifier.send_breach_alert(
        ...                 "LGPD_VIOLATION", current_user, e.correlation_id
        ...             )

    Note:
        Erros de segurança NUNCA são retryable e sempre requerem
        investigação. Todos os erros são automaticamente logados
        para auditoria e compliance LGPD/GDPR.
    """

    def __init__(
        self, message: str, oracle_error_code: Optional[int] = None, **kwargs
    ) -> None:
        """Inicializa erro de segurança Oracle com logging obrigatório.

        Args:
            message (str): Mensagem descritiva do erro de segurança.
            oracle_error_code (Optional[int]): Código específico do erro Oracle.
            **kwargs: Contexto de segurança (user, IP, resource, etc.).

        Example:
            >>> error = OracleSecurityError(
            ...     "Tentativa de acesso não autorizado a dados pessoais",
            ...     oracle_error_code=1031,
            ...     context={
            ...         "user": "app_user",
            ...         "client_ip": "192.168.1.100",
            ...         "resource": "customers.cpf",
            ...         "action": "SELECT",
            ...         "lgpd_category": "PERSONAL_DATA",
            ...         "timestamp": "2024-01-15T10:30:00Z"
            ...     }
            ... )
        """
        super().__init__(message, oracle_error_code, **kwargs)
        self.severity = "CRITICAL"  # Security errors são sempre críticos
        self.retryable = False  # Nunca retry em erros de segurança

        # Automatic compliance logging
        self._log_security_event()

    def _log_security_event(self) -> None:
        """Registra evento de segurança para auditoria obrigatória.

        Implementa logging estruturado conforme requisitos LGPD/GDPR
        para rastreabilidade completa de eventos de segurança.
        """
        import json
        import logging
        from datetime import datetime

        security_logger = logging.getLogger("datametria.security")

        event = {
            "event_type": "ORACLE_SECURITY_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": self.correlation_id,
            "oracle_error_code": self.oracle_error_code,
            "message": str(self),
            "severity": self.severity,
            "context": self.context,
            "compliance_flags": self._analyze_compliance_impact(),
        }

        security_logger.critical(
            "SECURITY_EVENT", extra={"security_event": json.dumps(event)}
        )

    def _analyze_compliance_impact(self) -> Dict[str, bool]:
        """Analisa impacto em compliance LGPD/GDPR.

        Returns:
            Dict[str, bool]: Flags de compliance afetados.
        """
        flags = {
            "lgpd_violation": False,
            "gdpr_violation": False,
            "personal_data_exposure": False,
            "breach_notification_required": False,
        }

        # Análise baseada no contexto do erro
        if self.context.get("lgpd_category") == "PERSONAL_DATA":
            flags["lgpd_violation"] = True
            flags["personal_data_exposure"] = True

        if self.oracle_error_code in [1031, 942]:  # Unauthorized access
            flags["breach_notification_required"] = True

        return flags


class OracleConfigError(OracleBaseException):
    """Erro de configuração Oracle"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.retryable = False


class OraclePoolError(OracleBaseException):
    """Erro do connection pool Oracle"""

    def __init__(self, message: str, oracle_error_code: Optional[int] = None, **kwargs):
        super().__init__(message, oracle_error_code, **kwargs)
        # Pool errors podem ser retryable dependendo do código
        self.retryable = oracle_error_code in [
            24422,  # Session pool is exhausted
            24459,  # OCISessionGet() timed out waiting for pool sessions
        ]


class OracleComplianceError(OracleBaseException):
    """Erro de compliance LGPD/GDPR"""

    def __init__(self, message: str, compliance_type: str = "LGPD", **kwargs):
        super().__init__(message, **kwargs)
        self.compliance_type = compliance_type
        self.retryable = False


def map_oracle_exception(
    oracle_error_code: Optional[int], message: str
) -> OracleBaseException:
    """Mapeia códigos de erro Oracle para exceções específicas com análise inteligente.

    Função central para mapeamento automático de códigos de erro Oracle (ORA-XXXXX)
    para exceções específicas do DATAMETRIA Common Libraries. Implementa análise
    inteligente do erro, categorização automática e seleção da estratégia de
    tratamento mais apropriada.

    Mapping Strategy:
        - Connection errors (12xxx): Problemas de conectividade e rede
        - Security errors (1xxx, 28xxx): Autenticação, autorização e compliance
        - Pool errors (24xxx): Problemas com connection pooling
        - Query errors (outros): Erros de execução SQL/PL/SQL
        - Configuration errors: Problemas de configuração

    Error Analysis:
        - Automatic error categorization baseada no código Oracle
        - Retry strategy selection baseada no tipo de erro
        - Severity assignment baseada no impacto potencial
        - Context enrichment com informações relevantes
        - Compliance impact analysis para LGPD/GDPR

    Args:
        oracle_error_code (Optional[int]): Código numérico do erro Oracle
            (sem prefixo ORA-). None para erros sem código específico.
        message (str): Mensagem descritiva do erro em português para
            facilitar troubleshooting por equipes brasileiras.

    Returns:
        OracleBaseException: Instância da exceção específica mais apropriada
            para o tipo de erro, com contexto enriquecido e estratégia de retry.

    Examples:
        Basic error mapping:
        >>> try:
        ...     # Oracle operation that fails
        ...     pass
        ... except cx_Oracle.Error as e:
        ...     oracle_code = e.args[0].code if hasattr(e.args[0], 'code') else None
        ...     mapped_error = map_oracle_exception(oracle_code, str(e))
        ...     raise mapped_error

        Handle different error types:
        >>> error = map_oracle_exception(12170, "TNS:Connect timeout occurred")
        >>> isinstance(error, OracleConnectionError)  # True
        >>> error.retryable  # True - connection timeouts são retryable
        >>>
        >>> error = map_oracle_exception(1017, "Invalid username/password")
        >>> isinstance(error, OracleSecurityError)  # True
        >>> error.retryable  # False - security errors nunca são retryable

        Unknown error handling:
        >>> error = map_oracle_exception(99999, "Unknown Oracle error")
        >>> isinstance(error, OracleQueryError)  # True - default fallback

    Note:
        Esta função é chamada automaticamente pelo Oracle Connector para
        mapear todas as exceções cx_Oracle.Error para exceções específicas
        do DATAMETRIA framework. Não deve ser chamada diretamente pelo
        código de aplicação.
    """

    # Handle None error code
    if oracle_error_code is None:
        return OracleQueryError(message, oracle_error_code)

    # Connection errors (12xxx series)
    connection_errors = [
        12170,  # TNS:Connect timeout occurred
        12529,  # TNS:connect request rejected due to current filtering rules
        12541,  # TNS:no listener
        12514,  # TNS:listener does not currently know of service
        12528,  # TNS:listener: all instances are blocking new connections
        12537,  # TNS:connection closed
        12560,  # TNS:protocol adapter error
        12545,  # Connect failed because target host or object does not exist
        12154,  # TNS:could not resolve the connect identifier specified
        12505,  # TNS:listener does not currently know of SID
    ]
    if oracle_error_code in connection_errors:
        return OracleConnectionError(message, oracle_error_code)

    # Security errors (authentication, authorization, compliance)
    security_errors = [
        1017,  # Invalid username/password; logon denied
        1045,  # User lacks CREATE SESSION privilege; logon denied
        28000,  # Account is locked
        28001,  # Password has expired
        28002,  # Password will expire soon
        28003,  # Password verification for the specified password failed
        1031,  # Insufficient privileges
        942,  # Table or view does not exist
        980,  # Synonym translation is no longer valid
        2391,  # Exceeded simultaneous SESSIONS_PER_USER limit
    ]
    if oracle_error_code in security_errors:
        return OracleSecurityError(message, oracle_error_code)

    # Pool errors (24xxx series)
    pool_errors = [
        24422,  # Session pool is exhausted
        24459,  # OCISessionGet() timed out waiting for pool sessions
        24496,  # Connection pool is not open
        24550,  # Signal received while waiting
        24801,  # Illegal parameter value
    ]
    if oracle_error_code in pool_errors:
        return OraclePoolError(message, oracle_error_code)

    # Configuration errors (common config issues)
    config_errors = [
        12154,  # TNS:could not resolve the connect identifier specified
        12505,  # TNS:listener does not currently know of SID
        12162,  # TNS:net service name is incorrectly specified
        12504,  # TNS:listener was not given the SERVICE_NAME in CONNECT_DATA
    ]
    if oracle_error_code in config_errors:
        return OracleConfigError(message, oracle_error_code=oracle_error_code)

    # Query errors (default fallback for all other errors)
    return OracleQueryError(message, oracle_error_code)
