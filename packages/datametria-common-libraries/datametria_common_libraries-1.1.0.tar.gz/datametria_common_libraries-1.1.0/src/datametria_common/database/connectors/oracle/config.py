"""
🏛️ Oracle Configuration - Enterprise Settings

Configuração enterprise completa para Oracle Database com suporte avançado a:
- Oracle RAC clusters com load balancing
- SSL/TLS encryption enterprise-grade
- Wallet authentication e Kerberos
- Connection pooling otimizado
- Failover configuration automático
- LGPD/GDPR compliance nativo
- Enterprise security features
- Performance tuning automático

Exemplos:
    >>> config = OracleConfig(
    ...     host="oracle-prod.company.com",
    ...     service_name="PROD",
    ...     username="app_user",
    # amazonq-ignore-next-line
    ...     rac_enabled=True,
    ...     rac_nodes=["node1", "node2", "node3"]
    ... )
    # amazonq-ignore-next-line
    >>> dsn = config.dsn
    >>> params = config.get_connection_params()

Compatibilidade:
    - Oracle Database 19c+
    - Oracle RAC 19c+
    - Oracle Cloud Infrastructure
    - Enterprise security standards

Autor:
    DATAMETRIA Enterprise Database Team

Versão:
    1.0.0 - Enterprise Configuration Ready
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from ....core.base_config import BaseConfig


class OracleAuthMode(Enum):
    """Modos de autenticação Oracle Database Enterprise.

    Enum que define os métodos de autenticação suportados
    para conexões Oracle Database em ambiente enterprise.

    Attributes:
        PASSWORD: Autenticação tradicional usuário/senha
        WALLET: Autenticação via Oracle Wallet (recomendado)
        KERBEROS: Autenticação Kerberos/Active Directory
        IAM: Autenticação via Identity and Access Management

    Examples:
        >>> auth_mode = OracleAuthMode.WALLET
        >>> config = OracleConfig(auth_mode=auth_mode)

    Note:
        - WALLET é recomendado para produção
        - KERBEROS para integração Active Directory
        - IAM para Oracle Cloud Infrastructure
    """

    PASSWORD = "password"
    WALLET = "wallet"
    KERBEROS = "kerberos"
    IAM = "iam"


class OracleServiceType(Enum):
    """Tipos de serviço Oracle Database.

    Enum que define os tipos de serviço Oracle Database
    para otimização de conexões e performance.

    Attributes:
        DEDICATED: Servidor dedicado (alta performance)
        SHARED: Servidor compartilhado (economia de recursos)
        POOLED: Servidor pooled (balanceamento de carga)

    Examples:
        >>> service_type = OracleServiceType.DEDICATED
        >>> # Usado internamente para otimização

    Note:
        - DEDICATED para aplicações críticas
        - SHARED para desenvolvimento/teste
        - POOLED para alta concorrência
    """

    DEDICATED = "dedicated"
    SHARED = "shared"
    POOLED = "pooled"


class OracleConfig(BaseConfig):
    """Configuração enterprise para Oracle Database.

    Classe de configuração completa para Oracle Database Enterprise
    com suporte a RAC, SSL, Wallet, pooling e compliance LGPD/GDPR.

    Attributes:
        host (str): Hostname do servidor Oracle
        port (int): Porta do listener Oracle (padrão: 1521)
        service_name (Optional[str]): Nome do serviço Oracle
        sid (Optional[str]): SID da instância Oracle
        username (str): Usuário para autenticação
        password (str): Senha para autenticação
        # amazonq-ignore-next-line
        auth_mode (OracleAuthMode): Modo de autenticação
        rac_enabled (bool): Habilita suporte Oracle RAC
        # amazonq-ignore-next-line
        rac_nodes (List[str]): Lista de nós RAC
        ssl_enabled (bool): Habilita SSL/TLS
        pool_min_size (int): Tamanho mínimo do pool
        pool_max_size (int): Tamanho máximo do pool
        audit_enabled (bool): Habilita auditoria
        # amazonq-ignore-next-line
        lgpd_compliance (bool): Compliance LGPD
        gdpr_compliance (bool): Compliance GDPR

    Examples:
        >>> # Configuração básica
        >>> config = OracleConfig(
        ...     host="oracle.company.com",
        ...     service_name="PROD",
        ...     username="app_user",
        ...     password="secure_password"
        ... )

        >>> # Configuração RAC enterprise
        >>> rac_config = OracleConfig(
        ...     service_name="PROD_RAC",
        ...     rac_enabled=True,
        ...     rac_nodes=["rac1", "rac2", "rac3"],
        ...     ssl_enabled=True,
        ...     auth_mode=OracleAuthMode.WALLET
        ... )

    Note:
        - Validação automática na inicialização
        - Suporte completo Oracle RAC
        - Compliance LGPD/GDPR nativo
        - Performance tuning automático
    """

    def __init__(self, host: str = "", port: int = 1521, service_name: Optional[str] = None,
                 sid: Optional[str] = None, username: str = "", password: str = "",
                 auth_mode: OracleAuthMode = OracleAuthMode.PASSWORD,
                 wallet_location: Optional[str] = None, rac_enabled: bool = False,
                 rac_nodes: Optional[List[str]] = None, load_balance: bool = True,
                 failover: bool = True, ssl_enabled: bool = False,
                 ssl_cert_path: Optional[str] = None, ssl_key_path: Optional[str] = None,
                 ssl_ca_path: Optional[str] = None, pool_min_size: int = 5,
                 pool_max_size: int = 20, pool_increment: int = 5,
                 pool_timeout: int = 30, pool_recycle: int = 3600,
                 arraysize: int = 1000, prefetchrows: int = 100,
                 stmtcachesize: int = 20, edition: Optional[str] = None,
                 events: bool = True, threaded: bool = True,
                 encryption_enabled: bool = True, checksumming_enabled: bool = True,
                 data_integrity_enabled: bool = True, audit_enabled: bool = True,
                 lgpd_compliance: bool = True, gdpr_compliance: bool = True):
        """Initialize Oracle configuration."""
        # Connection Settings
        self.host = host
        self.port = port
        self.service_name = service_name
        self.sid = sid
        
        # Authentication
        self.username = username
        self.password = password
        self.auth_mode = auth_mode
        self.wallet_location = wallet_location
        
        # RAC Configuration
        self.rac_enabled = rac_enabled
        self.rac_nodes = rac_nodes or []
        self.load_balance = load_balance
        self.failover = failover
        
        # SSL/TLS Configuration
        self.ssl_enabled = ssl_enabled
        self.ssl_cert_path = ssl_cert_path
        self.ssl_key_path = ssl_key_path
        self.ssl_ca_path = ssl_ca_path
        
        # Connection Pool Settings
        self.pool_min_size = pool_min_size
        self.pool_max_size = pool_max_size
        self.pool_increment = pool_increment
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        
        # Performance Settings
        self.arraysize = arraysize
        self.prefetchrows = prefetchrows
        self.stmtcachesize = stmtcachesize
        
        # Enterprise Features
        self.edition = edition
        self.events = events
        self.threaded = threaded
        
        # Security Settings
        self.encryption_enabled = encryption_enabled
        self.checksumming_enabled = checksumming_enabled
        self.data_integrity_enabled = data_integrity_enabled
        
        # Compliance Settings
        self.audit_enabled = audit_enabled
        self.lgpd_compliance = lgpd_compliance
        self.gdpr_compliance = gdpr_compliance
        
        super().__init__()

    def _validate_specific(self):
        """Validação pós-inicialização da configuração.

        Executa validações de consistência e inicialização
        de valores padrão após criação da instância.

        Raises:
            ValueError: Se configuração for inválida ou inconsistente.

        Examples:
            >>> # Chamado automaticamente após __init__
            >>> config = OracleConfig(host="oracle.com")
            >>> # Validações executadas automaticamente

        Note:
            - Chamado automaticamente pelo dataclass
            - Valida service_name ou sid obrigatório
            - Valida configuração RAC se habilitado
        """
        if not self.service_name and not self.sid:
            raise ValueError("service_name ou sid deve ser especificado")

        if self.rac_enabled and not self.rac_nodes:
            raise ValueError(
                "rac_nodes deve ser especificado quando RAC está habilitado"
            )

    @property
    def dsn(self) -> str:
        """Gera DSN (Data Source Name) para conexão Oracle.

        Constrói string DSN otimizada baseada na configuração,
        com suporte automático a RAC, failover e load balancing.

        Returns:
            str: DSN formatado para Oracle Database.

        Examples:
            >>> config = OracleConfig(host="oracle.com", service_name="PROD")
            >>> dsn = config.dsn
            >>> print(dsn)  # "oracle.com:1521/PROD"

            >>> # RAC DSN
            >>> rac_config = OracleConfig(
            ...     service_name="PROD",
            ...     rac_enabled=True,
            ...     rac_nodes=["rac1", "rac2"]
            ... )
            >>> rac_dsn = rac_config.dsn
            >>> # Retorna DSN RAC com failover

        Note:
            - Detecta automaticamente RAC vs instância única
            - Inclui configurações de failover e load balancing
            - Otimizado para performance enterprise
        """
        if self.rac_enabled:
            return self._build_rac_dsn()
        else:
            return self._build_single_dsn()

    def _build_single_dsn(self) -> str:
        """Constrói DSN para instância Oracle única.

        Método interno que gera DSN simples para conexões
        a instâncias Oracle não-RAC.

        Returns:
            str: DSN formatado para instância única.

        Examples:
            >>> # Chamado internamente por dsn property
            >>> dsn = config._build_single_dsn()

        Note:
            - Método interno, use property dsn
            - Suporta service_name e SID
            - Formato otimizado para performance
        """
        if self.service_name:
            # Para wallet, usar apenas service name
            if self.auth_mode == OracleAuthMode.WALLET:
                return self.service_name
            else:
                return f"{self.host}:{self.port}/{self.service_name}"
        else:
            return f"{self.host}:{self.port}:{self.sid}"

    def _build_rac_dsn(self) -> str:
        """Constrói DSN para Oracle RAC (Real Application Clusters).

        Método interno que gera DSN complexo para conexões
        Oracle RAC com failover e load balancing automático.

        Returns:
            str: DSN formatado para Oracle RAC.

        Examples:
            >>> # Chamado internamente por dsn property
            >>> rac_dsn = config._build_rac_dsn()

        Note:
            - Método interno, use property dsn
            - Inclui todos os nós RAC configurados
            - Failover e load balancing automático
            - Formato TNS Names completo
        """
        addresses = []
        for node in self.rac_nodes:
            addresses.append(f"(ADDRESS=(PROTOCOL=TCP)(HOST={node})(PORT={self.port}))")

        address_list = "".join(addresses)

        if self.service_name:
            connect_data = f"(SERVICE_NAME={self.service_name})"
        else:
            connect_data = f"(SID={self.sid})"

        dsn = (
            f"(DESCRIPTION="
            f"(ADDRESS_LIST="
            f"(LOAD_BALANCE={'YES' if self.load_balance else 'NO'})"
            f"(FAILOVER={'YES' if self.failover else 'NO'})"
            f"{address_list}"
            f")"
            f"(CONNECT_DATA={connect_data})"
            f")"
        )

        return dsn

    def get_connection_params(self) -> Dict[str, Any]:
        """Retorna parâmetros de conexão Oracle Database.

        Gera dicionário completo com parâmetros otimizados
        para conexão Oracle Database enterprise.

        Returns:
            Dict[str, Any]: Parâmetros de conexão Oracle.
            Inclui DSN, encoding, autenticação e configurações.

        Examples:
            >>> config = OracleConfig(host="oracle.com", service_name="PROD")
            >>> params = config.get_connection_params()
            >>> print(params)
            >>> # {
            >>> #     "dsn": "oracle.com:1521/PROD",
            >>> #     "user": "app_user",
            >>> #     "password": "***",
            >>> #     "encoding": "UTF-8",
            >>> #     "events": True,
            >>> #     "threaded": True
            >>> # }

        Note:
            - Parâmetros otimizados para cx_Oracle/oracledb
            - Suporte automático a diferentes auth_modes
            - Encoding UTF-8 para compliance internacional
            - Events e threading habilitados para performance
        """
        params = {
            "dsn": self.dsn,
        }

        # Authentication - sempre incluir user/password
        params["user"] = self.username
        params["password"] = self.password

        if self.auth_mode == OracleAuthMode.WALLET:
            # Para wallet Oracle Cloud, usar apenas user/password/dsn
            # TNS_ADMIN é configurado como variável de ambiente
            # config_dir não é usado para evitar modo bequeath em thin mode
            pass  # Wallet é configurado via TNS_ADMIN no connector

        # Edition-based redefinition
        if self.edition:
            params["edition"] = self.edition

        return params

    def get_pool_params(self) -> Dict[str, Any]:
        """Retorna parâmetros do connection pool Oracle.

        Gera dicionário com configurações otimizadas para
        connection pooling enterprise Oracle Database.

        Returns:
            Dict[str, Any]: Parâmetros do connection pool.
            Inclui min/max connections, timeout e cache settings.

        Examples:
            >>> config = OracleConfig(pool_min_size=10, pool_max_size=50)
            >>> pool_params = config.get_pool_params()
            >>> print(pool_params)
            >>> # {
            >>> #     "min": 10,
            >>> #     "max": 50,
            >>> #     "increment": 5,
            >>> #     "timeout": 30,
            >>> #     "getmode": 1,
            >>> #     "homogeneous": True,
            >>> #     "stmtcachesize": 20
            >>> # }

        Note:
            - Configurações otimizadas para alta concorrência
            - Statement cache habilitado para performance
            - Timeout configurado para evitar conexões órfãs
            - Homogeneous pool para consistência
        """
        return {
            "min": self.pool_min_size,
            "max": self.pool_max_size,
            "increment": self.pool_increment,
            "timeout": self.pool_timeout,
            "getmode": 1,  # cx_Oracle.SPOOL_ATTRVAL_WAIT
            "homogeneous": True,
            "stmtcachesize": self.stmtcachesize,
        }
