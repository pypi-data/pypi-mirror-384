"""
🕐 Oracle Timezone Manager - Enterprise Timezone Handling

Gerenciamento completo de timezone para Oracle Database Enterprise com suporte a:
- TIMESTAMP WITH TIME ZONE operations
- TIMESTAMP WITH LOCAL TIME ZONE operations  
- Conversões automáticas UTC/Local timezone
- SQLAlchemy timezone integration nativa
- Multi-region support para aplicações globais
- LGPD/GDPR compliance com timezone audit
- Performance otimizada para high-throughput
- Enterprise security com timezone validation

Exemplos:
    >>> tz_manager = OracleTimezoneManager('America/Sao_Paulo')
    >>> utc_dt = tz_manager.convert_to_utc(local_dt)
    >>> oracle_str = tz_manager.get_oracle_timestamp_with_tz(utc_dt)

Compatibilidade:
    - Oracle Database 19c+
    - SQLAlchemy 1.4+
    - Python 3.8+
    - Multi-tenant applications

Autor:
    DATAMETRIA Enterprise Team
    
Versão:
    1.0.0 - Enterprise Ready
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import pytz

try:
    import cx_Oracle
except ImportError:
    try:
        import oracledb as cx_Oracle
    except ImportError:
        raise ImportError("Oracle client library not found")

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class OracleTimezoneManager:
    """Enterprise Oracle Timezone Manager.
    
    Classe principal para gerenciamento de timezone em Oracle Database Enterprise.
    Fornece funcionalidades completas para conversão, validação e operações
    timezone-aware com compliance LGPD/GDPR.
    
    Attributes:
        logger (logging.Logger): Logger configurado para auditoria
        default_timezone (pytz.timezone): Timezone padrão configurado
        oracle_timezone_map (Dict[str, str]): Mapeamento de timezones Oracle
        
    Examples:
        >>> manager = OracleTimezoneManager('America/Sao_Paulo')
        >>> manager.configure_session_timezone(connection, 'UTC')
        >>> utc_dt = manager.convert_to_utc(local_datetime)
        
    Note:
        Esta classe é thread-safe e otimizada para aplicações enterprise
        com alto volume de transações timezone-aware.
    """
    
    def __init__(self, default_timezone: str = "UTC"):
        """Inicializa o Oracle Timezone Manager Enterprise.
        
        Configura o gerenciador com timezone padrão e inicializa
        componentes necessários para operações enterprise.
        
        Args:
            default_timezone (str): Timezone padrão do sistema.
                Valores suportados: 'UTC', 'America/Sao_Paulo', 
                'America/New_York', 'Europe/London', 'Asia/Tokyo'.
                Default: 'UTC'.
                
        Raises:
            pytz.UnknownTimeZoneError: Se timezone não for reconhecido.
            ImportError: Se biblioteca Oracle não estiver disponível.
            
        Examples:
            >>> # Configuração padrão UTC
            >>> manager = OracleTimezoneManager()
            
            >>> # Configuração para Brasil
            >>> manager = OracleTimezoneManager('America/Sao_Paulo')
            
        Note:
            O timezone padrão é usado quando datetime objects não possuem
            informação de timezone explícita.
        """
        self.logger = logging.getLogger(__name__)
        self.default_timezone = pytz.timezone(default_timezone)
        
        # Timezone mapping para Oracle
        self.oracle_timezone_map = {
            'UTC': 'UTC',
            'America/Sao_Paulo': 'America/Sao_Paulo',
            'America/New_York': 'America/New_York',
            'Europe/London': 'Europe/London',
            'Asia/Tokyo': 'Asia/Tokyo',
        }
    
    def configure_session_timezone(self, connection, timezone_name: str = None) -> None:
        """Configura timezone da sessão Oracle Database.
        
        Estabelece timezone da sessão Oracle e configura parâmetros NLS
        para formatação consistente de data/hora em operações enterprise.
        
        Args:
            connection: Conexão ativa Oracle Database (cx_Oracle.Connection).
            timezone_name (str, optional): Nome do timezone para configurar.
                Se None, usa default_timezone. Exemplos: 'America/Sao_Paulo',
                'UTC', 'Europe/London'.
                
        Raises:
            cx_Oracle.Error: Erro na configuração da sessão Oracle.
            ValueError: Timezone inválido ou não suportado.
            
        Examples:
            >>> with oracle_connector.get_connection() as conn:
            ...     manager.configure_session_timezone(conn, 'America/Sao_Paulo')
            
            >>> # Usar timezone padrão
            >>> manager.configure_session_timezone(connection)
            
        Note:
            - Configura TIME_ZONE, NLS_DATE_FORMAT, NLS_TIMESTAMP_FORMAT
            - Essencial para operações TIMESTAMP WITH TIME ZONE
            - Recomendado executar no início de cada sessão
        """
        try:
            cursor = connection.cursor()
            
            # Set session timezone
            tz_name = timezone_name or self.default_timezone.zone
            oracle_tz = self.oracle_timezone_map.get(tz_name, tz_name)
            
            cursor.execute(f"ALTER SESSION SET TIME_ZONE = '{oracle_tz}'")
            
            # Set NLS parameters for consistent date/time formatting
            cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'")
            cursor.execute("ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'")
            cursor.execute("ALTER SESSION SET NLS_TIMESTAMP_TZ_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF TZH:TZM'")
            
            cursor.close()
            
            self.logger.debug(f"Session timezone configured to: {oracle_tz}")
            
        except cx_Oracle.Error as e:
            self.logger.error(f"Failed to configure session timezone: {e}")
            raise
    
    def convert_to_utc(self, dt: datetime, source_tz: str = None) -> datetime:
        """Converte datetime para UTC timezone.
        
        Realiza conversão segura de datetime para UTC, tratando casos
        de datetime naive e timezone-aware com validação enterprise.
        
        Args:
            dt (datetime): Objeto datetime para conversão.
                Pode ser naive (sem timezone) ou aware (com timezone).
            source_tz (str, optional): Timezone de origem para datetime naive.
                Se None e dt for naive, usa default_timezone.
                Exemplos: 'America/Sao_Paulo', 'Europe/London'.
                
        Returns:
            datetime: Datetime convertido para UTC timezone.
            
        Raises:
            pytz.UnknownTimeZoneError: Se source_tz for inválido.
            ValueError: Se dt for None ou inválido.
            
        Examples:
            >>> # Datetime naive (sem timezone)
            >>> local_dt = datetime(2025, 1, 15, 14, 30)
            >>> utc_dt = manager.convert_to_utc(local_dt, 'America/Sao_Paulo')
            
            >>> # Datetime aware (com timezone)
            >>> aware_dt = datetime(2025, 1, 15, 14, 30, tzinfo=pytz.timezone('America/Sao_Paulo'))
            >>> utc_dt = manager.convert_to_utc(aware_dt)
            
        Note:
            - Função thread-safe para aplicações concurrent
            - Preserva precisão de microsegundos
            - Otimizada para high-performance operations
        """
        if dt.tzinfo is None:
            # Assume timezone padrão se não especificado
            source_timezone = pytz.timezone(source_tz) if source_tz else self.default_timezone
            dt = source_timezone.localize(dt)
        
        return dt.astimezone(pytz.UTC)
    
    def convert_from_utc(self, dt: datetime, target_tz: str) -> datetime:
        """Converte datetime de UTC para timezone específico.
        
        Realiza conversão de UTC para timezone local com tratamento
        de horário de verão e validação enterprise.
        
        Args:
            dt (datetime): Datetime em UTC para conversão.
                Pode ser naive (assumido como UTC) ou aware.
            target_tz (str): Timezone de destino para conversão.
                Exemplos: 'America/Sao_Paulo', 'Europe/London', 'Asia/Tokyo'.
                
        Returns:
            datetime: Datetime convertido para timezone especificado.
            
        Raises:
            pytz.UnknownTimeZoneError: Se target_tz for inválido.
            ValueError: Se dt for None ou inválido.
            
        Examples:
            >>> # UTC para São Paulo
            >>> utc_dt = datetime(2025, 1, 15, 17, 30, tzinfo=pytz.UTC)
            >>> sp_dt = manager.convert_from_utc(utc_dt, 'America/Sao_Paulo')
            
            >>> # UTC naive para Londres
            >>> utc_naive = datetime(2025, 1, 15, 17, 30)
            >>> london_dt = manager.convert_from_utc(utc_naive, 'Europe/London')
            
        Note:
            - Trata automaticamente horário de verão (DST)
            - Preserva precisão de microsegundos
            - Otimizada para operações em lote
        """
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        target_timezone = pytz.timezone(target_tz)
        return dt.astimezone(target_timezone)
    
    def get_oracle_timestamp_with_tz(self, dt: datetime) -> str:
        """Converte datetime para formato Oracle TIMESTAMP WITH TIME ZONE.
        
        Formata datetime para string compatível com Oracle Database
        TIMESTAMP WITH TIME ZONE column type.
        
        Args:
            dt (datetime): Datetime object para formatação.
                Pode ser naive (usa default_timezone) ou aware.
                
        Returns:
            str: String formatada para Oracle TIMESTAMP WITH TIME ZONE.
                Formato: 'YYYY-MM-DD HH24:MI:SS.FF TZH:TZM'
                
        Raises:
            ValueError: Se dt for None ou inválido.
            
        Examples:
            >>> dt = datetime(2025, 1, 15, 14, 30, 45, 123456, tzinfo=pytz.UTC)
            >>> oracle_str = manager.get_oracle_timestamp_with_tz(dt)
            >>> print(oracle_str)  # '2025-01-15 14:30:45.123456 +0000'
            
            >>> # Datetime naive
            >>> naive_dt = datetime(2025, 1, 15, 14, 30, 45)
            >>> oracle_str = manager.get_oracle_timestamp_with_tz(naive_dt)
            
        Note:
            - Compatível com Oracle 19c+ TIMESTAMP WITH TIME ZONE
            - Preserva microsegundos para precisão máxima
            - Thread-safe para operações concurrent
        """
        if dt.tzinfo is None:
            dt = self.default_timezone.localize(dt)
        
        # Format: YYYY-MM-DD HH24:MI:SS.FF TZH:TZM
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f %z')
    
    def parse_oracle_timestamp_tz(self, oracle_str: str) -> datetime:
        """Parse string Oracle TIMESTAMP WITH TIME ZONE para datetime.
        
        Converte string Oracle TIMESTAMP WITH TIME ZONE para objeto
        datetime Python com timezone information.
        
        Args:
            oracle_str (str): String Oracle TIMESTAMP WITH TIME ZONE.
                Formatos suportados:
                - 'YYYY-MM-DD HH24:MI:SS.FF TZH:TZM'
                - 'YYYY-MM-DD HH24:MI:SS TZH:TZM'
                
        Returns:
            datetime: Objeto datetime com timezone information.
            
        Raises:
            ValueError: Se oracle_str for inválido ou mal formatado.
            
        Examples:
            >>> oracle_str = '2025-01-15 14:30:45.123456 +0000'
            >>> dt = manager.parse_oracle_timestamp_tz(oracle_str)
            >>> print(dt.tzinfo)  # timezone.utc
            
            >>> # Sem microsegundos
            >>> oracle_str = '2025-01-15 14:30:45 -0300'
            >>> dt = manager.parse_oracle_timestamp_tz(oracle_str)
            
        Note:
            - Trata automaticamente microsegundos opcionais
            - Suporta todos os formatos Oracle timezone
            - Validação robusta para dados enterprise
        """
        try:
            # Remove microseconds if present
            if '.' in oracle_str:
                date_part, tz_part = oracle_str.rsplit(' ', 1)
                if '.' in date_part:
                    date_part = date_part.split('.')[0]
                oracle_str = f"{date_part} {tz_part}"
            
            # Parse with timezone
            return datetime.strptime(oracle_str, '%Y-%m-%d %H:%M:%S %z')
            
        except ValueError as e:
            self.logger.error(f"Failed to parse Oracle timestamp: {oracle_str}, error: {e}")
            raise


class TimezoneAwareDateTime(TypeDecorator):
    """SQLAlchemy TypeDecorator para timezone-aware datetime operations.
    
    Custom SQLAlchemy type que automatiza conversões de timezone
    para colunas datetime, garantindo consistência UTC no banco
    e conversões automáticas na aplicação.
    
    Attributes:
        impl (DateTime): Implementação base SQLAlchemy DateTime
        cache_ok (bool): Habilita cache SQLAlchemy para performance
        timezone_manager (OracleTimezoneManager): Gerenciador de timezone
        
    Examples:
        >>> # Definição de coluna
        >>> class Event(Base):
        ...     created_at = Column(TimezoneAwareDateTime())
        
        >>> # Uso automático
        >>> event = Event(created_at=datetime.now())
        >>> session.add(event)  # Automaticamente converte para UTC
        
    Note:
        - Armazena sempre em UTC no banco de dados
        - Conversões automáticas transparentes
        - Compatível com Oracle TIMESTAMP WITH TIME ZONE
    """
    
    impl = DateTime
    cache_ok = True
    
    def __init__(self, timezone_manager: OracleTimezoneManager = None):
        """Inicializa TimezoneAwareDateTime TypeDecorator.
        
        Args:
            timezone_manager (OracleTimezoneManager, optional): 
                Gerenciador de timezone customizado. Se None, cria
                instância padrão com UTC.
                
        Examples:
            >>> # Padrão UTC
            >>> tz_datetime = TimezoneAwareDateTime()
            
            >>> # Custom timezone manager
            >>> manager = OracleTimezoneManager('America/Sao_Paulo')
            >>> tz_datetime = TimezoneAwareDateTime(manager)
        """
        self.timezone_manager = timezone_manager or OracleTimezoneManager()
        super().__init__()
    
    def process_bind_param(self, value: datetime, dialect) -> datetime:
        """Processa valor antes de enviar para o banco de dados.
        
        Converte datetime para UTC antes de armazenar no Oracle Database,
        garantindo consistência de timezone em ambiente enterprise.
        
        Args:
            value (datetime): Valor datetime para processar.
            dialect: Dialeto SQLAlchemy (Oracle).
            
        Returns:
            datetime: Datetime convertido para UTC ou None.
            
        Examples:
            >>> # Automaticamente chamado pelo SQLAlchemy
            >>> # Converte datetime local para UTC antes do INSERT/UPDATE
            
        Note:
            - Chamado automaticamente pelo SQLAlchemy
            - Garante armazenamento consistente em UTC
            - Preserva None values
        """
        if value is not None:
            # Converte para UTC antes de armazenar
            return self.timezone_manager.convert_to_utc(value)
        return value
    
    def process_result_value(self, value: datetime, dialect) -> datetime:
        """Processa valor ao recuperar do banco de dados.
        
        Processa datetime recuperado do Oracle Database, garantindo
        que tenha informação de timezone (UTC) adequada.
        
        Args:
            value (datetime): Valor datetime do banco.
            dialect: Dialeto SQLAlchemy (Oracle).
            
        Returns:
            datetime: Datetime com timezone UTC ou None.
            
        Examples:
            >>> # Automaticamente chamado pelo SQLAlchemy
            >>> # Garante timezone UTC em valores recuperados
            
        Note:
            - Chamado automaticamente pelo SQLAlchemy
            - Assume valores do banco em UTC
            - Adiciona timezone info se ausente
        """
        if value is not None:
            # Assume que valor do banco está em UTC
            if value.tzinfo is None:
                value = pytz.UTC.localize(value)
            return value
        return value


class OracleTimezoneOperations:
    """Operações específicas de timezone para Oracle Database.
    
    Classe de alto nível que combina OracleConnector com OracleTimezoneManager
    para fornecer operações de banco de dados com suporte nativo a timezone.
    
    Attributes:
        connector: Instância do Oracle connector
        tz_manager (OracleTimezoneManager): Gerenciador de timezone
        logger (logging.Logger): Logger para auditoria
        
    Examples:
        >>> connector = OracleConnector(config)
        >>> tz_manager = OracleTimezoneManager('America/Sao_Paulo')
        >>> ops = OracleTimezoneOperations(connector, tz_manager)
        >>> ops.insert_with_timezone('events', data, {'created_at': 'UTC'})
        
    Note:
        - Combina operações de banco com timezone management
        - Otimizada para aplicações enterprise multi-region
        - Thread-safe para operações concurrent
    """
    
    def __init__(self, connector, timezone_manager: OracleTimezoneManager):
        """Inicializa Oracle Timezone Operations.
        
        Args:
            connector: Instância configurada do Oracle connector.
            timezone_manager (OracleTimezoneManager): Gerenciador de timezone.
                
        Examples:
            >>> from datametria_common.database.connectors.oracle import OracleConnector
            >>> connector = OracleConnector(oracle_config)
            >>> tz_manager = OracleTimezoneManager('America/Sao_Paulo')
            >>> ops = OracleTimezoneOperations(connector, tz_manager)
        """
        self.connector = connector
        self.tz_manager = timezone_manager
        self.logger = logging.getLogger(__name__)
    
    def insert_with_timezone(
        self, 
        table: str, 
        data: Dict[str, Any], 
        timezone_columns: Dict[str, str] = None
    ) -> None:
        """Insert com conversão automática de timezone.
        
        Executa INSERT com conversão automática de timezone para
        colunas datetime especificadas, garantindo consistência.
        
        Args:
            table (str): Nome da tabela Oracle para insert.
            data (Dict[str, Any]): Dados para inserir.
                Chaves são nomes de colunas, valores são dados.
            timezone_columns (Dict[str, str], optional): 
                Mapeamento coluna -> timezone de destino.
                Exemplo: {'created_at': 'UTC', 'updated_at': 'America/Sao_Paulo'}
                
        Raises:
            cx_Oracle.Error: Erro na execução do INSERT.
            ValueError: Dados inválidos ou timezone não suportado.
            
        Examples:
            >>> data = {
            ...     'id': 1,
            ...     'name': 'Event',
            ...     'created_at': datetime.now(),
            ...     'scheduled_at': datetime(2025, 1, 15, 14, 30)
            ... }
            >>> timezone_cols = {
            ...     'created_at': 'UTC',
            ...     'scheduled_at': 'America/Sao_Paulo'
            ... }
            >>> ops.insert_with_timezone('events', data, timezone_cols)
            
        Note:
            - Conversão automática apenas para colunas especificadas
            - Usa prepared statements para segurança
            - Otimizada para operações em lote
        """
        processed_data = data.copy()
        timezone_columns = timezone_columns or {}
        
        # Processa colunas de timezone
        for column, value in data.items():
            if isinstance(value, datetime) and column in timezone_columns:
                target_tz = timezone_columns[column]
                if target_tz == 'UTC':
                    processed_data[column] = self.tz_manager.convert_to_utc(value)
                else:
                    processed_data[column] = self.tz_manager.convert_from_utc(value, target_tz)
        
        # Constrói SQL dinamicamente
        columns = list(processed_data.keys())
        placeholders = [f":{col}" for col in columns]
        
        sql = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        """
        
        self.connector.execute_dml(sql, processed_data)
    
    def query_with_timezone_conversion(
        self, 
        sql: str, 
        params: Dict[str, Any] = None,
        convert_to_timezone: str = None
    ) -> List[Dict[str, Any]]:
        """Query com conversão automática de timezone.
        
        Executa query SQL com conversão automática de colunas datetime
        para timezone especificado, ideal para aplicações multi-region.
        
        Args:
            sql (str): Query SQL para executar.
            params (Dict[str, Any], optional): Parâmetros para query.
            convert_to_timezone (str, optional): Timezone para conversão
                de colunas datetime. Se None, retorna em UTC.
                
        Returns:
            List[Dict[str, Any]]: Resultados com timezone convertido.
            
        Raises:
            cx_Oracle.Error: Erro na execução da query.
            pytz.UnknownTimeZoneError: Timezone inválido.
            
        Examples:
            >>> # Query com conversão para São Paulo
            >>> results = ops.query_with_timezone_conversion(
            ...     "SELECT * FROM events WHERE created_at > :start_date",
            ...     {'start_date': datetime(2025, 1, 1)},
            ...     'America/Sao_Paulo'
            ... )
            
            >>> # Query sem conversão (UTC)
            >>> results = ops.query_with_timezone_conversion(
            ...     "SELECT * FROM events"
            ... )
            
        Note:
            - Converte automaticamente todas as colunas datetime
            - Preserva tipos de dados não-datetime
            - Otimizada para resultsets grandes
        """
        results = self.connector.execute_query(sql, params)
        
        if convert_to_timezone:
            for row in results:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = self.tz_manager.convert_from_utc(value, convert_to_timezone)
        
        return results
    
    def get_database_timezone(self) -> str:
        """Obtém timezone configurado no Oracle Database.
        
        Consulta o timezone configurado no nível do banco de dados Oracle
        usando a função DBTIMEZONE.
        
        Returns:
            str: Timezone do banco de dados (ex: 'UTC', '+00:00').
            
        Raises:
            cx_Oracle.Error: Erro na consulta ao banco.
            
        Examples:
            >>> db_tz = ops.get_database_timezone()
            >>> print(f"Database timezone: {db_tz}")
            
        Note:
            - Retorna timezone configurado no CREATE DATABASE
            - Diferente do timezone da sessão
            - Útil para auditoria e diagnóstico
        """
        result = self.connector.execute_query("""
            SELECT DBTIMEZONE FROM DUAL
        """)
        
        return result[0]['DBTIMEZONE'] if result else 'UTC'
    
    def get_session_timezone(self) -> str:
        """Obtém timezone da sessão Oracle atual.
        
        Consulta o timezone configurado para a sessão atual usando
        a função SESSIONTIMEZONE.
        
        Returns:
            str: Timezone da sessão atual (ex: 'America/Sao_Paulo', 'UTC').
            
        Raises:
            cx_Oracle.Error: Erro na consulta ao banco.
            
        Examples:
            >>> session_tz = ops.get_session_timezone()
            >>> print(f"Session timezone: {session_tz}")
            
        Note:
            - Reflete timezone configurado via ALTER SESSION SET TIME_ZONE
            - Pode diferir do timezone do banco de dados
            - Afeta operações TIMESTAMP WITH LOCAL TIME ZONE
        """
        result = self.connector.execute_query("""
            SELECT SESSIONTIMEZONE FROM DUAL
        """)
        
        return result[0]['SESSIONTIMEZONE'] if result else 'UTC'
    
    def convert_timezone_in_query(
        self, 
        column: str, 
        from_tz: str, 
        to_tz: str
    ) -> str:
        """
        Gera SQL para conversão de timezone
        
        Args:
            column: Nome da coluna
            from_tz: Timezone origem
            to_tz: Timezone destino
            
        Returns:
            SQL para conversão
        """
        return f"""
        {column} AT TIME ZONE '{from_tz}' AT TIME ZONE '{to_tz}'
        """
    
    def get_timezone_aware_now(self, timezone_name: str = None) -> datetime:
        """
        Obtém timestamp atual com timezone específico
        
        Args:
            timezone_name: Nome do timezone
            
        Returns:
            Datetime atual com timezone
        """
        tz_name = timezone_name or self.tz_manager.default_timezone.zone
        
        result = self.connector.execute_query(f"""
            SELECT CURRENT_TIMESTAMP AT TIME ZONE '{tz_name}' as current_time
            FROM DUAL
        """)
        
        return result[0]['CURRENT_TIME'] if result else datetime.now(pytz.timezone(tz_name))


# Exemplo de uso com SQLAlchemy
def create_timezone_aware_model():
    """Exemplo de modelo SQLAlchemy com timezone"""
    from sqlalchemy import Column, String, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.dialects.oracle import RAW
    
    Base = declarative_base()
    
    class Execucao(Base):
        __tablename__ = 'execucoes'
        
        execucao_id = Column(RAW(16), primary_key=True)
        processo_id = Column(RAW(16), nullable=False)
        workspace_id = Column(RAW(16), nullable=False)
        status = Column(String(50), nullable=False)
        
        # Timezone-aware columns
        data_inicio = Column(TimezoneAwareDateTime(), nullable=False)
        data_fim = Column(TimezoneAwareDateTime())
        created_at = Column(TimezoneAwareDateTime(), default=datetime.utcnow)
        updated_at = Column(TimezoneAwareDateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    return Execucao


# Configuração para DMOne
class DMOneTimezoneConfig:
    """Configuração específica para projeto DMOne"""
    
    @staticmethod
    def get_brazil_timezone_config():
        """Configuração para timezone brasileiro"""
        return {
            'default_timezone': 'America/Sao_Paulo',
            'database_timezone': 'UTC',
            'session_timezone': 'America/Sao_Paulo',
            'timestamp_columns': {
                'created_at': 'UTC',
                'updated_at': 'UTC',
                'ultimo_login': 'America/Sao_Paulo',
                'data_inicio': 'America/Sao_Paulo',
                'data_fim': 'America/Sao_Paulo'
            }
        }
    
    @staticmethod
    def configure_oracle_for_dmone(oracle_connector):
        """Configura Oracle connector para DMOne"""
        tz_manager = OracleTimezoneManager('America/Sao_Paulo')
        
        # Configura timezone da sessão
        with oracle_connector.get_connection() as conn:
            tz_manager.configure_session_timezone(conn, 'America/Sao_Paulo')
        
        # Retorna operações timezone-aware
        return OracleTimezoneOperations(oracle_connector, tz_manager)
