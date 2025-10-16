"""
DATAMETRIA ComplianceMixin - Automatic LGPD/GDPR Compliance Hooks

Universal compliance mixin that provides automatic LGPD/GDPR compliance
hooks for all DATAMETRIA components.
"""

from abc import ABC
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum

from ..security.lgpd_compliance import LGPDCompliance
from ..security.gdpr_compliance import GDPRCompliance


class ComplianceEvent(Enum):
    """Compliance event types."""
    DATA_ACCESS = "data_access"
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    DATA_DELETION = "data_deletion"
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"


class ComplianceMixin(ABC):
    """Universal compliance mixin for automatic LGPD/GDPR compliance.
    
    Provides automatic compliance hooks that can be integrated into any
    DATAMETRIA component for seamless compliance automation.
    
    Example:
        >>> class MyService(ComplianceMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self._init_compliance()
        >>> 
        >>> service = MyService()
        >>> service.log_data_access("user123", "email", "marketing")
    """
    
    def __init__(self):
        """Initialize compliance mixin."""
        self._lgpd_compliance: Optional[LGPDCompliance] = None
        self._gdpr_compliance: Optional[GDPRCompliance] = None
        self._compliance_enabled: bool = True
    
    def _init_compliance(self, logger=None) -> None:
        """Initialize compliance managers."""
        self._lgpd_compliance = LGPDCompliance(logger=logger)
        self._gdpr_compliance = GDPRCompliance(logger=logger)
    
    def log_data_access(self, user_id: str, data_type: str, purpose: str) -> None:
        """Log data access for compliance."""
        if not self._compliance_enabled:
            return
        
        event_data = {
            "user_id": user_id,
            "data_type": data_type,
            "purpose": purpose,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if self._lgpd_compliance:
            self._lgpd_compliance.log_data_access(user_id, data_type, purpose)
        
        if self._gdpr_compliance:
            self._gdpr_compliance.log_data_access(user_id, data_type, purpose)
    
    def log_data_collection(self, user_id: str, data_fields: List[str], 
                           consent_id: Optional[str] = None) -> None:
        """Log data collection with consent tracking."""
        if not self._compliance_enabled:
            return
        
        if self._lgpd_compliance:
            self._lgpd_compliance.log_data_collection(user_id, data_fields, consent_id)
        
        if self._gdpr_compliance:
            self._gdpr_compliance.log_data_collection(user_id, data_fields, consent_id)
    
    def log_data_processing(self, user_id: str, processing_type: str, 
                           legal_basis: str) -> None:
        """Log data processing activity."""
        if not self._compliance_enabled:
            return
        
        if self._lgpd_compliance:
            self._lgpd_compliance.log_data_processing(user_id, processing_type, legal_basis)
        
        if self._gdpr_compliance:
            self._gdpr_compliance.log_data_processing(user_id, processing_type, legal_basis)
    
    def check_consent(self, user_id: str, purpose: str) -> bool:
        """Check if user has given consent for specific purpose."""
        if not self._compliance_enabled:
            return True
        
        # Check LGPD consent
        if self._lgpd_compliance:
            lgpd_consent = self._lgpd_compliance.check_consent(user_id, purpose)
            if not lgpd_consent:
                return False
        
        # Check GDPR consent
        if self._gdpr_compliance:
            gdpr_consent = self._gdpr_compliance.check_consent(user_id, purpose)
            if not gdpr_consent:
                return False
        
        return True
    
    def require_consent(self, user_id: str, purpose: str) -> None:
        """Require consent or raise compliance error."""
        if not self.check_consent(user_id, purpose):
            raise ValueError(f"Missing consent for {purpose}")
    
    def auto_compliance_hook(self, event: ComplianceEvent, **kwargs) -> None:
        """Automatic compliance hook for common operations."""
        if not self._compliance_enabled:
            return
        
        user_id = kwargs.get("user_id")
        if not user_id:
            return
        
        if event == ComplianceEvent.DATA_ACCESS:
            self.log_data_access(
                user_id, 
                kwargs.get("data_type", "unknown"),
                kwargs.get("purpose", "system")
            )
        elif event == ComplianceEvent.DATA_COLLECTION:
            self.log_data_collection(
                user_id,
                kwargs.get("data_fields", []),
                kwargs.get("consent_id")
            )
        elif event == ComplianceEvent.DATA_PROCESSING:
            self.log_data_processing(
                user_id,
                kwargs.get("processing_type", "automated"),
                kwargs.get("legal_basis", "legitimate_interest")
            )
    
    def is_compliance_enabled(self) -> bool:
        """Check if compliance is enabled."""
        return self._compliance_enabled
    
    def disable_compliance(self) -> None:
        """Disable compliance (for testing only)."""
        self._compliance_enabled = False
    
    def enable_compliance(self) -> None:
        """Enable compliance."""
        self._compliance_enabled = True
