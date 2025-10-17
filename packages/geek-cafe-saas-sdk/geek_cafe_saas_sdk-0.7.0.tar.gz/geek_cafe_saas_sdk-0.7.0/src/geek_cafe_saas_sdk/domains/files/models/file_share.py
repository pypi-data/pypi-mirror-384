"""
FileShare model for file sharing and permissions.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
import datetime as dt
from typing import Optional, Dict, Any
from geek_cafe_saas_sdk.models.base_model import BaseModel


class FileShare(BaseModel):
    """
    File sharing record with permissions.
    
    Manages access control for files. Users can share files with other users
    with specific permission levels and optional expiration.
    
    Access Patterns (DynamoDB Keys):
    - pk: FILE#{tenant_id}#{file_id}
    - sk: SHARE#{share_id}
    - gsi1_pk: SHARE#{tenant_id}#{shared_with_user_id}
    - gsi1_sk: FILE#{file_id}
    - gsi2_pk: FILE#{tenant_id}#{file_id}
    - gsi2_sk: SHARE#{created_utc_ts}
    
    Permission Levels:
    - "view": Can view metadata only
    - "download": Can view and download
    - "edit": Can view, download, and modify metadata
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._share_id: str | None = None  # Unique share ID
        self._file_id: str | None = None  # Shared file
        
        # Sharing Information
        self._shared_by: str | None = None  # User who shared the file
        self._shared_with_user_id: str | None = None  # Recipient user ID
        self._shared_with_email: str | None = None  # Recipient email (for external shares)
        
        # Permissions
        self._permission_level: str = "view"  # "view", "download", "edit"
        self._can_reshare: bool = False  # Can recipient share with others?
        
        # Access Control
        self._access_token: str | None = None  # Token for external/unauthenticated access
        self._expires_at_ts: float | None = None  # Expiration timestamp
        
        # Usage Tracking
        self._access_count: int = 0  # Number of times accessed
        self._last_accessed_at_ts: float | None = None  # Last access timestamp
        
        # State
        self._status: str = "active"  # "active", "revoked", "expired"
        self._revoked_at_ts: float | None = None  # When revoked
        
        # Timestamps (inherited from BaseModel)
        # created_utc_ts
    
    # Properties - Identity
    @property
    def share_id(self) -> str | None:
        """Unique share ID."""
        return self._share_id or self.id
    
    @share_id.setter
    def share_id(self, value: str | None):
        self._share_id = value
        if value:
            self.id = value
    
    @property
    def file_id(self) -> str | None:
        """Shared file ID."""
        return self._file_id
    
    @file_id.setter
    def file_id(self, value: str | None):
        self._file_id = value
    
    # Properties - Sharing Information
    @property
    def shared_by(self) -> str | None:
        """User who shared the file."""
        return self._shared_by
    
    @shared_by.setter
    def shared_by(self, value: str | None):
        self._shared_by = value
    
    @property
    def shared_with_user_id(self) -> str | None:
        """Recipient user ID."""
        return self._shared_with_user_id
    
    @shared_with_user_id.setter
    def shared_with_user_id(self, value: str | None):
        self._shared_with_user_id = value
    
    @property
    def shared_with_email(self) -> str | None:
        """Recipient email (for external shares)."""
        return self._shared_with_email
    
    @shared_with_email.setter
    def shared_with_email(self, value: str | None):
        self._shared_with_email = value
    
    # Properties - Permissions
    @property
    def permission_level(self) -> str:
        """Permission level: 'view', 'download', 'edit'."""
        return self._permission_level
    
    @permission_level.setter
    def permission_level(self, value: str):
        if value not in ["view", "download", "edit"]:
            raise ValueError(f"Invalid permission level: {value}. Must be 'view', 'download', or 'edit'")
        self._permission_level = value
    
    @property
    def can_reshare(self) -> bool:
        """Can recipient share with others?"""
        return self._can_reshare
    
    @can_reshare.setter
    def can_reshare(self, value: bool):
        self._can_reshare = bool(value)
    
    # Properties - Access Control
    @property
    def access_token(self) -> str | None:
        """Access token for public links."""
        return self._access_token
    
    @access_token.setter
    def access_token(self, value: str | None):
        self._access_token = value
    
    @property
    def expires_at_ts(self) -> float | None:
        """Expiration timestamp."""
        return self._expires_at_ts
    
    @expires_at_ts.setter
    def expires_at_ts(self, value: float | None):
        self._expires_at_ts = value
    
    # Properties - Usage Tracking
    @property
    def access_count(self) -> int:
        """Number of times accessed."""
        return self._access_count
    
    @access_count.setter
    def access_count(self, value: int):
        self._access_count = value if value is not None else 0
    
    @property
    def last_accessed_at_ts(self) -> float | None:
        """Last access timestamp."""
        return self._last_accessed_at_ts
    
    @last_accessed_at_ts.setter
    def last_accessed_at_ts(self, value: float | None):
        self._last_accessed_at_ts = value
    
    # Properties - State
    @property
    def status(self) -> str:
        """Share status: 'active', 'revoked', 'expired'."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value not in ["active", "revoked", "expired"]:
            raise ValueError(f"Invalid status: {value}. Must be 'active', 'revoked', or 'expired'")
        self._status = value
    
    @property
    def revoked_at_ts(self) -> float | None:
        """When share was revoked."""
        return self._revoked_at_ts
    
    @revoked_at_ts.setter
    def revoked_at_ts(self, value: float | None):
        self._revoked_at_ts = value
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if share is active."""
        return self._status == "active"
    
    def is_revoked(self) -> bool:
        """Check if share is revoked."""
        return self._status == "revoked"
    
    def is_expired(self) -> bool:
        """Check if share is expired (by status or timestamp)."""
        if self._status == "expired":
            return True
        if self._expires_at_ts:
            return dt.datetime.now(dt.UTC).timestamp() > self._expires_at_ts
        return False
    
    def is_public_link(self) -> bool:
        """Check if this is a public link (has access token)."""
        return self._access_token is not None and self._access_token != ""
    
    def is_internal_share(self) -> bool:
        """Check if shared with another user (not public)."""
        return self._shared_with_user_id is not None and self._shared_with_user_id != ""
    
    def can_view(self) -> bool:
        """Check if share allows viewing."""
        return self._permission_level in ["view", "download", "edit"]
    
    def can_download(self) -> bool:
        """Check if share allows downloading."""
        return self._permission_level in ["download", "edit"]
    
    def can_edit(self) -> bool:
        """Check if share allows editing."""
        return self._permission_level == "edit"
    
    def increment_access_count(self):
        """Increment access count and update last accessed time."""
        self._access_count += 1
        self._last_accessed_at_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def revoke(self):
        """Revoke the share."""
        self._status = "revoked"
        self._revoked_at_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def mark_as_expired(self):
        """Mark share as expired."""
        self._status = "expired"
    
    def has_permission(self, required_level: str) -> bool:
        """
        Check if share has required permission level.
        
        Permission hierarchy: edit > download > view
        """
        hierarchy = {"view": 1, "download": 2, "edit": 3}
        current = hierarchy.get(self._permission_level, 0)
        required = hierarchy.get(required_level, 0)
        return current >= required
    
    def get_expires_at_datetime(self) -> dt.datetime | None:
        """Get expiration as datetime object."""
        if self._expires_at_ts:
            return dt.datetime.fromtimestamp(self._expires_at_ts, tz=dt.UTC)
        return None
    
    def get_revoked_at_datetime(self) -> dt.datetime | None:
        """Get revocation time as datetime object."""
        if self._revoked_at_ts:
            return dt.datetime.fromtimestamp(self._revoked_at_ts, tz=dt.UTC)
        return None
