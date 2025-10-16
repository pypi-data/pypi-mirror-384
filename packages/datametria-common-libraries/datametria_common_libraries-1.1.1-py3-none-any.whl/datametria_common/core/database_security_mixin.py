"""
DATAMETRIA DatabaseSecurityMixin - Standardized Database Security

Universal database security mixin that provides consistent security
across all SGBD implementations.
"""

from abc import ABC
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .security_mixin import SecurityMixin
from .compliance_mixin import ComplianceMixin, ComplianceEvent
from ..security.security_manager import DataClassification


class DatabaseSecurityMixin(SecurityMixin, ComplianceMixin, ABC):
    """Universal database security mixin for all DATAMETRIA database components.
    
    Provides standardized security features:
    - Query sanitization
    - Data encryption at rest
    - Access logging
    - Compliance tracking
    
    Example:
        >>> class MyDBService(DatabaseSecurityMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self._init_database_security()
        >>> 
        >>> service = MyDBService()
        >>> result = service.secure_query("SELECT * FROM users WHERE id = ?", [123])
    """
    
    def __init__(self):
        """Initialize database security mixin."""
        SecurityMixin.__init__(self)
        ComplianceMixin.__init__(self)
        self._sensitive_tables: List[str] = []
        self._encrypted_fields: Dict[str, DataClassification] = {}
    
    def _init_database_security(self) -> None:
        """Initialize database security components."""
        self._init_security()
        self._init_compliance()
    
    def configure_sensitive_data(self, tables: List[str], 
                               encrypted_fields: Dict[str, str]) -> None:
        """Configure sensitive tables and encrypted fields."""
        self._sensitive_tables = tables
        self._encrypted_fields = {
            field: DataClassification(classification) 
            for field, classification in encrypted_fields.items()
        }
    
    def sanitize_query(self, query: str, params: Optional[List] = None) -> str:
        """Sanitize SQL query to prevent injection."""
        # Basic SQL injection prevention
        dangerous_patterns = [';--', 'DROP', 'DELETE', 'TRUNCATE', 'ALTER']
        
        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if pattern in query_upper and not self._is_authorized_operation(pattern):
                raise ValueError(f"Potentially dangerous SQL pattern detected: {pattern}")
        
        return query
    
    def _is_authorized_operation(self, operation: str) -> bool:
        """Check if user is authorized for dangerous operations."""
        context = self.get_security_context()
        if not context:
            return False
        
        return self.check_authorization("database", "admin")
    
    def secure_query(self, query: str, params: Optional[List] = None, 
                    table_name: Optional[str] = None) -> str:
        """Execute secure query with logging and compliance."""
        # Require database access authorization
        self.require_authorization("database", "read")
        
        # Sanitize query
        safe_query = self.sanitize_query(query, params)
        
        # Log data access for compliance
        if table_name and table_name in self._sensitive_tables:
            context = self.get_security_context()
            if context:
                self.log_data_access(
                    context.user_id, 
                    table_name, 
                    "database_query"
                )
        
        # Log security event
        self.log_security_event("database_query", {
            "query_type": "SELECT" if "SELECT" in query.upper() else "OTHER",
            "table": table_name,
            "has_params": params is not None
        })
        
        return safe_query
    
    def encrypt_field_data(self, field_name: str, data: str) -> str:
        """Encrypt field data based on classification."""
        if field_name in self._encrypted_fields:
            classification = self._encrypted_fields[field_name]
            return self.encrypt_data(data, classification)
        return data
    
    def decrypt_field_data(self, field_name: str, encrypted_data: str) -> str:
        """Decrypt field data."""
        if field_name in self._encrypted_fields:
            return self.decrypt_data(encrypted_data)
        return encrypted_data
    
    def secure_insert(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Secure data insertion with encryption and compliance."""
        # Require write authorization
        self.require_authorization("database", "write")
        
        # Encrypt sensitive fields
        secure_data = {}
        for field, value in data.items():
            secure_data[field] = self.encrypt_field_data(field, str(value))
        
        # Log data collection for compliance
        if table_name in self._sensitive_tables:
            context = self.get_security_context()
            if context:
                self.log_data_collection(
                    context.user_id,
                    list(data.keys())
                )
        
        return secure_data
    
    def mask_sensitive_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mask sensitive data in query results."""
        masked_results = []
        
        for row in results:
            masked_row = {}
            for field, value in row.items():
                if field in self._encrypted_fields:
                    # Determine data type for masking
                    if '@' in str(value):
                        masked_row[field] = self.mask_data(str(value), "email")
                    elif len(str(value)) == 11:
                        masked_row[field] = self.mask_data(str(value), "cpf")
                    else:
                        masked_row[field] = self.mask_data(str(value), "general")
                else:
                    masked_row[field] = value
            masked_results.append(masked_row)
        
        return masked_results
    
    def audit_database_access(self, operation: str, table_name: str, 
                            affected_rows: int = 0) -> None:
        """Audit database access for compliance."""
        context = self.get_security_context()
        
        self.log_security_event("database_audit", {
            "operation": operation,
            "table": table_name,
            "affected_rows": affected_rows,
            "user_id": context.user_id if context else "system",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Compliance logging for sensitive tables
        if table_name in self._sensitive_tables and context:
            if operation.upper() in ['SELECT', 'READ']:
                self.auto_compliance_hook(
                    ComplianceEvent.DATA_ACCESS,
                    user_id=context.user_id,
                    data_type=table_name,
                    purpose="database_operation"
                )
            elif operation.upper() in ['INSERT', 'UPDATE']:
                self.auto_compliance_hook(
                    ComplianceEvent.DATA_PROCESSING,
                    user_id=context.user_id,
                    processing_type=operation.lower(),
                    legal_basis="legitimate_interest"
                )
