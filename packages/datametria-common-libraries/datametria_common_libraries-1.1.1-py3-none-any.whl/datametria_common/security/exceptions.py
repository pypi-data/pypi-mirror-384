"""
🚨 Security Exceptions - DATAMETRIA Security Framework

Exceções específicas para o framework de segurança enterprise com hierarquia
estruturada e compliance automático LGPD/GDPR.

Este módulo fornece uma hierarquia completa de exceções para o sistema de
segurança da DATAMETRIA, permitindo tratamento granular de erros e
rastreamento automático para compliance.

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
License: MIT

Example:
    >>> try:
    ...     # Operação que pode violar LGPD
    ...     process_personal_data()
    ... except LGPDViolationError as e:
    ...     logger.log_compliance_violation(e)
    ...     notify_dpo(e)
"""

from typing import Optional, Dict, Any


class SecurityError(Exception):
    """Exceção base para todos os erros de segurança do sistema.
    
    Classe base para todas as exceções relacionadas à segurança,
    fornecendo estrutura comum para rastreamento e auditoria.
    
    Attributes:
        message (str): Mensagem descritiva do erro
        error_code (Optional[str]): Código único do erro para catalogação
        details (Dict[str, Any]): Detalhes adicionais do erro
        
    Example:
        >>> raise SecurityError(
        ...     message="Acesso negado ao recurso",
        ...     error_code="SEC001",
        ...     details={"resource": "/admin", "user_id": "user123"}
        ... )
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Inicializa exceção de segurança.
        
        Args:
            message (str): Mensagem descritiva do erro
            error_code (Optional[str]): Código único para catalogação
            details (Optional[Dict[str, Any]]): Detalhes adicionais
        """
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class ComplianceError(SecurityError):
    """Exceção base para violações de compliance regulatório.
    
    Classe especializada para violações de regulamentações como
    LGPD, GDPR e outras normas de proteção de dados.
    
    Attributes:
        regulation (str): Regulamentação violada (LGPD, GDPR, etc.)
        violation_type (str): Tipo específico da violação
        
    Example:
        >>> raise ComplianceError(
        ...     message="Processamento sem base legal",
        ...     regulation="LGPD",
        ...     violation_type="unlawful_processing",
        ...     error_code="COMP001"
        ... )
    """
    
    def __init__(self, message: str, regulation: str, violation_type: str, **kwargs):
        """Inicializa exceção de compliance.
        
        Args:
            message (str): Mensagem descritiva da violação
            regulation (str): Regulamentação violada
            violation_type (str): Tipo específico da violação
            **kwargs: Argumentos adicionais para SecurityError
        """
        super().__init__(message, **kwargs)
        self.regulation = regulation
        self.violation_type = violation_type


class LGPDViolationError(ComplianceError):
    """Exceção específica para violações da Lei Geral de Proteção de Dados.
    
    Classe especializada para violações da LGPD (Lei 13.709/2018),
    incluindo processamento ilegal, falta de consentimento, etc.
    
    Common violation_types:
        - unlawful_processing: Processamento sem base legal
        - missing_consent: Falta de consentimento
        - data_breach: Violação de dados pessoais
        - retention_violation: Violação de retenção
        - transfer_violation: Transferência irregular
        
    Example:
        >>> raise LGPDViolationError(
        ...     message="Dados processados sem consentimento",
        ...     violation_type="missing_consent",
        ...     error_code="LGPD001",
        ...     details={"data_subject": "user123", "purpose": "marketing"}
        ... )
    """
    
    def __init__(self, message: str, violation_type: str, **kwargs):
        """Inicializa exceção de violação LGPD.
        
        Args:
            message (str): Mensagem descritiva da violação
            violation_type (str): Tipo específico da violação LGPD
            **kwargs: Argumentos adicionais para ComplianceError
        """
        super().__init__(message, regulation="LGPD", violation_type=violation_type, **kwargs)


class GDPRViolationError(ComplianceError):
    """Exceção específica para violações do General Data Protection Regulation.
    
    Classe especializada para violações do GDPR (Regulamento UE 2016/679),
    incluindo processamento ilegal, violação de direitos dos titulares, etc.
    
    Common violation_types:
        - unlawful_processing: Processamento sem base legal
        - consent_violation: Violação de consentimento
        - data_breach: Violação de dados pessoais
        - subject_rights_violation: Violação de direitos do titular
        - cross_border_violation: Violação de transferência internacional
        
    Example:
        >>> raise GDPRViolationError(
        ...     message="Transferência internacional sem adequação",
        ...     violation_type="cross_border_violation",
        ...     error_code="GDPR001",
        ...     details={"destination": "US", "mechanism": "none"}
        ... )
    """
    
    def __init__(self, message: str, violation_type: str, **kwargs):
        """Inicializa exceção de violação GDPR.
        
        Args:
            message (str): Mensagem descritiva da violação
            violation_type (str): Tipo específico da violação GDPR
            **kwargs: Argumentos adicionais para ComplianceError
        """
        super().__init__(message, regulation="GDPR", violation_type=violation_type, **kwargs)


class DataProtectionError(SecurityError):
    """Exceção para erros gerais de proteção de dados.
    
    Classe para erros relacionados à proteção de dados que não se
    enquadram especificamente em violações regulatórias.
    
    Common scenarios:
        - Falha na criptografia de dados
        - Erro na anonimização/pseudonimização
        - Falha na implementação de controles de acesso
        - Erro na classificação de dados
        
    Example:
        >>> raise DataProtectionError(
        ...     message="Falha na criptografia de dados sensíveis",
        ...     error_code="DP001",
        ...     details={"algorithm": "AES-256", "key_status": "expired"}
        ... )
    """
    
    def __init__(self, message: str, protection_type: Optional[str] = None, **kwargs):
        """Inicializa exceção de proteção de dados.
        
        Args:
            message (str): Mensagem descritiva do erro
            protection_type (Optional[str]): Tipo de proteção que falhou
            **kwargs: Argumentos adicionais para SecurityError
        """
        super().__init__(message, **kwargs)
        self.protection_type = protection_type


class AuditError(SecurityError):
    """Exceção para erros no sistema de auditoria e logging.
    
    Classe para erros relacionados ao sistema de auditoria,
    logging de segurança e rastreamento de compliance.
    
    Common scenarios:
        - Falha na gravação de logs de auditoria
        - Erro na integridade do trail de auditoria
        - Falha na retenção de logs
        - Erro na exportação de relatórios
        
    Example:
        >>> raise AuditError(
        ...     message="Falha na gravação do log de auditoria",
        ...     error_code="AUD001",
        ...     details={"log_type": "security", "storage": "database"}
        ... )
    """
    
    def __init__(self, message: str, audit_component: Optional[str] = None, **kwargs):
        """Inicializa exceção de auditoria.
        
        Args:
            message (str): Mensagem descritiva do erro
            audit_component (Optional[str]): Componente de auditoria que falhou
            **kwargs: Argumentos adicionais para SecurityError
        """
        super().__init__(message, **kwargs)
        self.audit_component = audit_component
