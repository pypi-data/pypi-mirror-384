"""
Compliance Metadata Processor - Metadados de Compliance LGPD/GDPR

Adiciona metadados de compliance a cada log entry:
- Classificação de dados (public, internal, confidential, restricted)
- Período de retenção baseado em classificação
- Detecção de PII (Personally Identifiable Information)
- Base legal e finalidade de processamento

Autor: DATAMETRIA Team
Versão: 2.0.0
Compliance: LGPD Art. 6, 46, 48 | GDPR Art. 5, 32
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class DataClassification(str, Enum):
    """Classificação de dados conforme sensibilidade."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class ComplianceMetadata:
    """Metadados de compliance para logs.
    
    Attributes:
        data_classification (str): Classificação do dado
        retention_period_days (int): Período de retenção em dias
        contains_pii (bool): Se contém dados pessoais
        legal_basis (Optional[str]): Base legal LGPD/GDPR
        processing_purpose (Optional[str]): Finalidade do processamento
        timestamp (str): Timestamp da classificação
    """
    data_classification: str
    retention_period_days: int
    contains_pii: bool
    legal_basis: Optional[str] = None
    processing_purpose: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        """Inicializa timestamp se não fornecido."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)


class ComplianceProcessor:
    """Processador structlog para adicionar metadados de compliance.
    
    Adiciona automaticamente:
    - Classificação de dados baseada em conteúdo
    - Período de retenção conforme política
    - Detecção de PII
    - Metadados LGPD/GDPR
    
    Attributes:
        RETENTION_POLICIES (Dict): Políticas de retenção por classificação
        PII_INDICATORS (Set): Indicadores de dados pessoais
        
    Example:
        >>> processor = ComplianceProcessor()
        >>> event_dict = {"message": "User login", "user_id": "123"}
        >>> result = processor(None, None, event_dict)
        >>> print(result["compliance"]["contains_pii"])  # True
    """
    
    # Políticas de retenção (em dias) conforme LGPD/GDPR
    RETENTION_POLICIES = {
        DataClassification.PUBLIC: 365,        # 1 ano
        DataClassification.INTERNAL: 1095,     # 3 anos
        DataClassification.CONFIDENTIAL: 2555, # 7 anos
        DataClassification.RESTRICTED: 2555,   # 7 anos
    }
    
    # Indicadores de PII (Personally Identifiable Information)
    PII_INDICATORS: Set[str] = {
        'user_id', 'username', 'email', 'name', 'nome',
        'cpf', 'cnpj', 'rg', 'passport', 'ssn',
        'phone', 'telefone', 'address', 'endereco',
        'birth_date', 'data_nascimento', 'age', 'idade',
        'ip_address', 'location', 'localizacao',
        'biometric', 'biometria', 'photo', 'foto',
    }
    
    # Palavras-chave que indicam dados sensíveis
    SENSITIVE_KEYWORDS: Set[str] = {
        'password', 'senha', 'secret', 'token', 'key',
        'credential', 'auth', 'security', 'seguranca',
        'confidential', 'confidencial', 'restricted', 'restrito',
    }
    
    def __init__(
        self,
        default_classification: DataClassification = DataClassification.INTERNAL,
        legal_basis: Optional[str] = None,
        processing_purpose: Optional[str] = None,
    ):
        """Inicializa compliance processor.
        
        Args:
            default_classification (DataClassification): Classificação padrão
            legal_basis (Optional[str]): Base legal padrão (ex: "LGPD Art. 7, I")
            processing_purpose (Optional[str]): Finalidade padrão
        """
        self.default_classification = default_classification
        self.default_legal_basis = legal_basis
        self.default_processing_purpose = processing_purpose
    
    def __call__(self, logger, method_name, event_dict):
        """Adiciona metadados de compliance ao event dict.
        
        Args:
            logger: Logger instance (não usado)
            method_name: Nome do método (não usado)
            event_dict (Dict): Dicionário de evento a processar
            
        Returns:
            Dict: Event dict com metadados de compliance
        """
        # Classificar dados
        classification = self._classify_data(event_dict)
        
        # Detectar PII
        contains_pii = self._contains_pii(event_dict)
        
        # Criar metadados
        metadata = ComplianceMetadata(
            data_classification=classification.value,
            retention_period_days=self.RETENTION_POLICIES[classification],
            contains_pii=contains_pii,
            legal_basis=self._determine_legal_basis(event_dict, contains_pii),
            processing_purpose=self._determine_purpose(event_dict),
        )
        
        # Adicionar ao event dict
        event_dict['compliance'] = metadata.to_dict()
        
        return event_dict
    
    def _classify_data(self, event_dict: Dict[str, Any]) -> DataClassification:
        """Classifica dados baseado em conteúdo.
        
        Args:
            event_dict (Dict): Dicionário de evento
            
        Returns:
            DataClassification: Classificação determinada
        """
        # Verificar se há palavras-chave sensíveis
        event_str = str(event_dict).lower()
        
        # RESTRICTED: contém credenciais ou dados muito sensíveis
        if any(keyword in event_str for keyword in ['password', 'secret', 'credential', 'token']):
            return DataClassification.RESTRICTED
        
        # CONFIDENTIAL: contém dados pessoais sensíveis
        if any(keyword in event_str for keyword in ['cpf', 'cnpj', 'ssn', 'credit_card', 'biometric']):
            return DataClassification.CONFIDENTIAL
        
        # INTERNAL: contém PII ou dados internos
        if self._contains_pii(event_dict):
            return DataClassification.INTERNAL
        
        # Verificar nível de log
        level = event_dict.get('level', '').upper()
        if level in ['ERROR', 'CRITICAL', 'SECURITY']:
            return DataClassification.CONFIDENTIAL
        
        # PUBLIC: dados não sensíveis
        return self.default_classification
    
    def _contains_pii(self, event_dict: Dict[str, Any]) -> bool:
        """Detecta se event dict contém PII.
        
        Args:
            event_dict (Dict): Dicionário de evento
            
        Returns:
            bool: True se contém PII
        """
        # Verificar chaves do dicionário
        for key in event_dict.keys():
            key_lower = key.lower()
            if any(indicator in key_lower for indicator in self.PII_INDICATORS):
                return True
        
        # Verificar valores recursivamente
        return self._check_pii_recursive(event_dict)
    
    def _check_pii_recursive(self, data: Any) -> bool:
        """Verifica PII recursivamente em estruturas aninhadas.
        
        Args:
            data (Any): Dados a verificar
            
        Returns:
            bool: True se encontrou PII
        """
        if isinstance(data, dict):
            for key, value in data.items():
                key_lower = key.lower()
                if any(indicator in key_lower for indicator in self.PII_INDICATORS):
                    return True
                if self._check_pii_recursive(value):
                    return True
        
        elif isinstance(data, (list, tuple)):
            for item in data:
                if self._check_pii_recursive(item):
                    return True
        
        return False
    
    def _determine_legal_basis(self, event_dict: Dict[str, Any], contains_pii: bool) -> Optional[str]:
        """Determina base legal para processamento.
        
        Args:
            event_dict (Dict): Dicionário de evento
            contains_pii (bool): Se contém PII
            
        Returns:
            Optional[str]: Base legal determinada
        """
        # Usar base legal padrão se fornecida
        if self.default_legal_basis:
            return self.default_legal_basis
        
        # Determinar base legal baseado em contexto
        if not contains_pii:
            return None
        
        event_type = event_dict.get('event_type', '').lower()
        
        # Mapeamento de tipos de evento para base legal
        if 'security' in event_type or 'audit' in event_type:
            return "LGPD Art. 7, II - Cumprimento de obrigação legal"
        
        if 'authentication' in event_type or 'authorization' in event_type:
            return "LGPD Art. 7, V - Execução de contrato"
        
        if 'performance' in event_type or 'monitoring' in event_type:
            return "LGPD Art. 7, IX - Legítimo interesse"
        
        # Base legal genérica
        return "LGPD Art. 7, I - Consentimento"
    
    def _determine_purpose(self, event_dict: Dict[str, Any]) -> Optional[str]:
        """Determina finalidade do processamento.
        
        Args:
            event_dict (Dict): Dicionário de evento
            
        Returns:
            Optional[str]: Finalidade determinada
        """
        # Usar finalidade padrão se fornecida
        if self.default_processing_purpose:
            return self.default_processing_purpose
        
        # Determinar finalidade baseado em tipo de evento
        event_type = event_dict.get('event_type', '').lower()
        
        purpose_map = {
            'security': 'Segurança da informação',
            'audit': 'Auditoria e compliance',
            'authentication': 'Autenticação de usuários',
            'authorization': 'Controle de acesso',
            'performance': 'Monitoramento de performance',
            'error': 'Diagnóstico e correção de erros',
            'user_action': 'Registro de atividades',
        }
        
        for key, purpose in purpose_map.items():
            if key in event_type:
                return purpose
        
        return "Operação do sistema"


class ComplianceReportGenerator:
    """Gerador de relatórios de compliance.
    
    Gera relatórios baseados em logs com metadados de compliance.
    
    Example:
        >>> generator = ComplianceReportGenerator()
        >>> report = generator.generate_summary(logs)
    """
    
    def generate_summary(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gera resumo de compliance dos logs.
        
        Args:
            logs (List[Dict]): Lista de logs com metadados
            
        Returns:
            Dict: Resumo de compliance
        """
        total_logs = len(logs)
        
        # Contadores
        classification_counts = {
            DataClassification.PUBLIC.value: 0,
            DataClassification.INTERNAL.value: 0,
            DataClassification.CONFIDENTIAL.value: 0,
            DataClassification.RESTRICTED.value: 0,
        }
        
        pii_count = 0
        legal_basis_counts = {}
        
        for log in logs:
            compliance = log.get('compliance', {})
            
            # Contar classificações
            classification = compliance.get('data_classification')
            if classification in classification_counts:
                classification_counts[classification] += 1
            
            # Contar PII
            if compliance.get('contains_pii'):
                pii_count += 1
            
            # Contar bases legais
            legal_basis = compliance.get('legal_basis')
            if legal_basis:
                legal_basis_counts[legal_basis] = legal_basis_counts.get(legal_basis, 0) + 1
        
        return {
            'total_logs': total_logs,
            'classification_distribution': classification_counts,
            'pii_percentage': (pii_count / total_logs * 100) if total_logs > 0 else 0,
            'legal_basis_distribution': legal_basis_counts,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }
    
    def check_retention_compliance(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifica compliance de retenção de dados.
        
        Args:
            logs (List[Dict]): Lista de logs com metadados
            
        Returns:
            Dict: Status de compliance de retenção
        """
        now = datetime.now(timezone.utc)
        expired_logs = []
        
        for log in logs:
            compliance = log.get('compliance', {})
            timestamp_str = compliance.get('timestamp')
            retention_days = compliance.get('retention_period_days', 0)
            
            if timestamp_str and retention_days:
                try:
                    log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    age_days = (now - log_time).days
                    
                    if age_days > retention_days:
                        expired_logs.append({
                            'log_id': log.get('id'),
                            'age_days': age_days,
                            'retention_days': retention_days,
                            'classification': compliance.get('data_classification'),
                        })
                except:
                    pass
        
        return {
            'total_logs': len(logs),
            'expired_logs': len(expired_logs),
            'compliance_rate': ((len(logs) - len(expired_logs)) / len(logs) * 100) if logs else 100,
            'expired_details': expired_logs[:10],  # Primeiros 10
            'checked_at': now.isoformat(),
        }
