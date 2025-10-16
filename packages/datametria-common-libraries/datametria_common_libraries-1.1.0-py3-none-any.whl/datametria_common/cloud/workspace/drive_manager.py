"""
Google Drive Manager - Enterprise Integration

Provides upload, download, and share operations with:
- ErrorHandlerMixin for retry logic
- CacheMixin for file metadata caching
- Rate limiting (1000 requests per 100 seconds)
- LGPD/GDPR compliance with data masking
- Enterprise logging with audit trail
"""

from typing import Optional, Dict, Any, List, BinaryIO
import io
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError

from ...core.error_handler import ErrorHandlerMixin
from ...caching.cache_mixin import CacheMixin
from ...security.centralized_enterprise_logger import CentralizedEnterpriseLogger
from .config import WorkspaceConfig
from .oauth2 import WorkspaceOAuth2Manager
from .rate_limiter import WorkspaceRateLimiter


class DriveManager(ErrorHandlerMixin, CacheMixin):
    """Google Drive Manager with enterprise features"""

    def __init__(
        self,
        config: WorkspaceConfig,
        oauth_manager: WorkspaceOAuth2Manager,
        rate_limiter: WorkspaceRateLimiter,
        logger: Optional[CentralizedEnterpriseLogger] = None
    ):
        self.config = config
        self.oauth_manager = oauth_manager
        self.rate_limiter = rate_limiter
        self.logger = logger
        self._service = None

    @property
    def service(self):
        """Lazy initialization of Drive service"""
        if self._service is None:
            credentials = self.oauth_manager.get_credentials()
            self._service = build('drive', 'v3', credentials=credentials)
        return self._service

    def _mask_filename(self, filename: str) -> str:
        """Mask filename for LGPD/GDPR compliance"""
        if len(filename) <= 4:
            return f"{filename[0]}***"
        return f"{filename[:2]}***{filename[-2:]}"

    async def upload_file(
        self,
        file_path: str,
        name: Optional[str] = None,
        mime_type: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload file to Google Drive

        Args:
            file_path: Path to file to upload
            name: File name in Drive (defaults to original filename)
            mime_type: MIME type (auto-detected if not provided)
            parent_folder_id: Parent folder ID
            description: File description

        Returns:
            Dict with file metadata (id, name, webViewLink, webContentLink)
        """
        await self.rate_limiter.check_and_wait('drive')

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = name or file_path_obj.name
        file_metadata = {'name': file_name}
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        if description:
            file_metadata['description'] = description

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

        def _upload():
            return self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType,webViewLink,webContentLink,createdTime,size'
            ).execute()

        result = await self.execute_with_retry(_upload, max_retries=3)

        if self.logger:
            self.logger.log_info(
                f"File uploaded: {self._mask_filename(file_name)}",
                extra={
                    'file_id': result['id'],
                    'size_bytes': result.get('size', 0),
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def download_file(
        self,
        file_id: str,
        destination_path: Optional[str] = None
    ) -> bytes:
        """
        Download file from Google Drive

        Args:
            file_id: Drive file ID
            destination_path: Optional path to save file

        Returns:
            File content as bytes
        """
        await self.rate_limiter.check_and_wait('drive')

        def _download():
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            return fh.getvalue()

        content = await self.execute_with_retry(_download, max_retries=2)

        if destination_path:
            Path(destination_path).write_bytes(content)

        if self.logger:
            self.logger.log_info(
                f"File downloaded: {file_id}",
                extra={
                    'file_id': file_id,
                    'size_bytes': len(content),
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return content

    async def share_file(
        self,
        file_id: str,
        email: str,
        role: str = 'reader',
        notify: bool = True,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share file with user

        Args:
            file_id: Drive file ID
            email: User email to share with
            role: Permission role (reader, writer, commenter, owner)
            notify: Send notification email
            message: Custom message in notification

        Returns:
            Permission metadata
        """
        await self.rate_limiter.check_and_wait('drive')

        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }

        def _share():
            return self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=notify,
                emailMessage=message,
                fields='id,type,role,emailAddress'
            ).execute()

        result = await self.execute_with_retry(_share, max_retries=2)

        if self.logger:
            self.logger.log_info(
                f"File shared: {file_id} with {self._mask_email(email)}",
                extra={
                    'file_id': file_id,
                    'role': role,
                    'email_masked': self._mask_email(email),
                    'compliance_tags': ['LGPD', 'GDPR', 'AUDIT']
                }
            )

        return result

    async def get_file_metadata(
        self,
        file_id: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get file metadata with caching

        Args:
            file_id: Drive file ID
            use_cache: Use cache if available

        Returns:
            File metadata
        """
        if use_cache:
            cached = await self.cache_get(f"drive:file:{file_id}")
            if cached:
                return cached

        await self.rate_limiter.check_and_wait('drive')

        def _get_metadata():
            return self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,createdTime,modifiedTime,owners,permissions,webViewLink'
            ).execute()

        metadata = await self.execute_with_retry(_get_metadata, max_retries=2)

        if use_cache:
            await self.cache_set(
                f"drive:file:{file_id}",
                metadata,
                ttl=self.config.cache_ttl
            )

        return metadata

    async def list_files(
        self,
        query: Optional[str] = None,
        max_results: int = 100,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files with optional query

        Args:
            query: Drive query string (e.g., "name contains 'report'")
            max_results: Maximum results per page
            page_token: Page token for pagination

        Returns:
            Dict with files list and nextPageToken
        """
        await self.rate_limiter.check_and_wait('drive')

        def _list():
            return self.service.files().list(
                q=query,
                pageSize=min(max_results, 1000),
                pageToken=page_token,
                fields='nextPageToken,files(id,name,mimeType,size,createdTime,modifiedTime)'
            ).execute()

        return await self.execute_with_retry(_list, max_retries=2)

    def _mask_email(self, email: str) -> str:
        """Mask email for LGPD/GDPR compliance"""
        if '@' not in email:
            return '***'
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"

    async def test_connection(self) -> bool:
        """Test Drive API connection"""
        try:
            await self.rate_limiter.check_and_wait('drive')
            self.service.about().get(fields='user').execute()
            return True
        except Exception:
            return False
