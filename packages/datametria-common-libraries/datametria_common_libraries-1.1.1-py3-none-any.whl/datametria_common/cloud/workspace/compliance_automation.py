"""
Workspace Compliance Automation - LGPD/GDPR compliance for Google Workspace APIs

Provides:
- Automatic data access logging
- Data deletion tracking
- Consent management
- Data portability
- Breach notification
- Compliance reporting
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from ...security.centralized_enterprise_logger import CentralizedEnterpriseLogger
from .config import WorkspaceConfig


class DataOperation(Enum):
    ACCESS = "access"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    SHARE = "share"


class ComplianceRegulation(Enum):
    LGPD = "LGPD"
    GDPR = "GDPR"
    CCPA = "CCPA"


class WorkspaceComplianceAutomation:
    """Automated compliance management for Workspace APIs"""
    
    def __init__(
        self,
        config: WorkspaceConfig,
        logger: Optional[CentralizedEnterpriseLogger] = None
    ):
        self.config = config
        self.logger = logger
        self._data_access_log = []
        self._consent_records = {}
        self._deletion_requests = []
        self._breach_incidents = []
    
    def log_data_access(
        self,
        api: str,
        operation: DataOperation,
        user_id: str,
        data_type: str,
        data_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log data access for compliance"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'api': api,
            'operation': operation.value,
            'user_id': self._mask_user_id(user_id),
            'data_type': data_type,
            'data_id': data_id,
            'metadata': metadata or {},
            'regulations': [ComplianceRegulation.LGPD.value, ComplianceRegulation.GDPR.value]
        }
        
        self._data_access_log.append(record)
        
        if self.logger:
            self.logger.log_info(
                f"Data {operation.value}: {data_type}",
                extra={
                    'api': api,
                    'user_id_masked': self._mask_user_id(user_id),
                    'data_type': data_type,
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT', 'DATA_ACCESS']
                }
            )
    
    def record_consent(
        self,
        user_id: str,
        purpose: str,
        granted: bool,
        scope: List[str],
        expiry: Optional[datetime] = None
    ):
        """Record user consent"""
        consent = {
            'user_id': self._mask_user_id(user_id),
            'purpose': purpose,
            'granted': granted,
            'scope': scope,
            'timestamp': datetime.now().isoformat(),
            'expiry': expiry.isoformat() if expiry else None,
            'regulations': [ComplianceRegulation.LGPD.value, ComplianceRegulation.GDPR.value]
        }
        
        self._consent_records[user_id] = consent
        
        if self.logger:
            self.logger.log_info(
                f"Consent {'granted' if granted else 'revoked'}: {purpose}",
                extra={
                    'user_id_masked': self._mask_user_id(user_id),
                    'purpose': purpose,
                    'scope': scope,
                    'compliance_tags': ['LGPD', 'GDPR', 'CONSENT']
                }
            )
    
    def check_consent(self, user_id: str, purpose: str) -> bool:
        """Check if user has granted consent"""
        consent = self._consent_records.get(user_id)
        if not consent:
            return False
        
        # Check if consent is still valid
        if consent.get('expiry'):
            expiry = datetime.fromisoformat(consent['expiry'])
            if datetime.now() > expiry:
                return False
        
        return consent.get('granted', False) and purpose in consent.get('scope', [])
    
    def request_data_deletion(
        self,
        user_id: str,
        data_types: List[str],
        reason: str
    ) -> str:
        """Request data deletion (Right to Erasure)"""
        request_id = f"DEL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id[:8]}"
        
        deletion_request = {
            'request_id': request_id,
            'user_id': self._mask_user_id(user_id),
            'data_types': data_types,
            'reason': reason,
            'status': 'pending',
            'requested_at': datetime.now().isoformat(),
            'deadline': (datetime.now() + timedelta(days=30)).isoformat(),
            'regulations': [ComplianceRegulation.LGPD.value, ComplianceRegulation.GDPR.value]
        }
        
        self._deletion_requests.append(deletion_request)
        
        if self.logger:
            self.logger.log_info(
                f"Data deletion requested: {request_id}",
                extra={
                    'request_id': request_id,
                    'user_id_masked': self._mask_user_id(user_id),
                    'data_types': data_types,
                    'compliance_tags': ['LGPD', 'GDPR', 'RIGHT_TO_ERASURE']
                }
            )
        
        return request_id
    
    def complete_data_deletion(self, request_id: str):
        """Mark data deletion as complete"""
        for request in self._deletion_requests:
            if request['request_id'] == request_id:
                request['status'] = 'completed'
                request['completed_at'] = datetime.now().isoformat()
                
                if self.logger:
                    self.logger.log_info(
                        f"Data deletion completed: {request_id}",
                        extra={
                            'request_id': request_id,
                            'compliance_tags': ['LGPD', 'GDPR', 'DATA_DELETION']
                        }
                    )
                break
    
    def export_user_data(
        self,
        user_id: str,
        data_types: List[str]
    ) -> Dict[str, Any]:
        """Export user data (Data Portability)"""
        export_id = f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id[:8]}"
        
        export_record = {
            'export_id': export_id,
            'user_id': self._mask_user_id(user_id),
            'data_types': data_types,
            'exported_at': datetime.now().isoformat(),
            'format': 'JSON',
            'regulations': [ComplianceRegulation.LGPD.value, ComplianceRegulation.GDPR.value]
        }
        
        if self.logger:
            self.logger.log_info(
                f"Data export: {export_id}",
                extra={
                    'export_id': export_id,
                    'user_id_masked': self._mask_user_id(user_id),
                    'data_types': data_types,
                    'compliance_tags': ['LGPD', 'GDPR', 'DATA_PORTABILITY']
                }
            )
        
        return export_record
    
    def report_breach(
        self,
        description: str,
        affected_users: int,
        data_types: List[str],
        severity: str
    ) -> str:
        """Report data breach"""
        breach_id = f"BREACH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        breach = {
            'breach_id': breach_id,
            'description': description,
            'affected_users': affected_users,
            'data_types': data_types,
            'severity': severity,
            'detected_at': datetime.now().isoformat(),
            'notification_deadline': (datetime.now() + timedelta(hours=72)).isoformat(),
            'status': 'reported',
            'regulations': [ComplianceRegulation.LGPD.value, ComplianceRegulation.GDPR.value]
        }
        
        self._breach_incidents.append(breach)
        
        if self.logger:
            self.logger.log_error(
                f"Data breach reported: {breach_id}",
                extra={
                    'breach_id': breach_id,
                    'affected_users': affected_users,
                    'severity': severity,
                    'compliance_tags': ['LGPD', 'GDPR', 'BREACH', 'CRITICAL']
                }
            )
        
        return breach_id
    
    def get_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Filter logs by date range
        filtered_access = [
            log for log in self._data_access_log
            if start_date <= datetime.fromisoformat(log['timestamp']) <= end_date
        ]
        
        filtered_deletions = [
            req for req in self._deletion_requests
            if start_date <= datetime.fromisoformat(req['requested_at']) <= end_date
        ]
        
        filtered_breaches = [
            breach for breach in self._breach_incidents
            if start_date <= datetime.fromisoformat(breach['detected_at']) <= end_date
        ]
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'data_access': {
                'total': len(filtered_access),
                'by_operation': self._count_by_field(filtered_access, 'operation'),
                'by_api': self._count_by_field(filtered_access, 'api')
            },
            'consent': {
                'total_records': len(self._consent_records),
                'granted': sum(1 for c in self._consent_records.values() if c['granted']),
                'revoked': sum(1 for c in self._consent_records.values() if not c['granted'])
            },
            'deletion_requests': {
                'total': len(filtered_deletions),
                'pending': sum(1 for r in filtered_deletions if r['status'] == 'pending'),
                'completed': sum(1 for r in filtered_deletions if r['status'] == 'completed')
            },
            'breaches': {
                'total': len(filtered_breaches),
                'by_severity': self._count_by_field(filtered_breaches, 'severity')
            },
            'regulations': [ComplianceRegulation.LGPD.value, ComplianceRegulation.GDPR.value],
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _mask_user_id(self, user_id: str) -> str:
        """Mask user ID for privacy"""
        if len(user_id) <= 4:
            return f"{user_id[0]}***"
        return f"{user_id[:2]}***{user_id[-2:]}"
    
    def _count_by_field(self, records: List[Dict], field: str) -> Dict[str, int]:
        """Count records by field value"""
        counts = {}
        for record in records:
            value = record.get(field, 'unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def get_metrics(self) -> Dict[str, int]:
        """Get compliance metrics"""
        return {
            'total_data_access': len(self._data_access_log),
            'total_consents': len(self._consent_records),
            'active_consents': sum(1 for c in self._consent_records.values() if c['granted']),
            'deletion_requests': len(self._deletion_requests),
            'pending_deletions': sum(1 for r in self._deletion_requests if r['status'] == 'pending'),
            'breach_incidents': len(self._breach_incidents)
        }
