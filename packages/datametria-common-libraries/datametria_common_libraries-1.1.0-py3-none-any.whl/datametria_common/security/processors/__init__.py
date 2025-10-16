"""
🔒 Security Processors - Processadores de Segurança e Compliance

Processadores structlog para:
- Data masking automático (LGPD/GDPR)
- Compliance metadata
- Security context
"""

from .data_masking import DataMaskingProcessor
from .compliance_metadata import (
    ComplianceProcessor,
    ComplianceMetadata,
    ComplianceReportGenerator,
    DataClassification,
)

__all__ = [
    "DataMaskingProcessor",
    "ComplianceProcessor",
    "ComplianceMetadata",
    "ComplianceReportGenerator",
    "DataClassification",
]
