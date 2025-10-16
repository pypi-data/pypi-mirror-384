"""
File model for file storage system.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
import datetime as dt
from typing import List, Optional, Dict, Any
from geek_cafe_saas_sdk.models.base_model import BaseModel


class File(BaseModel):
    """
    File metadata and references.
    
    Represents a file in the system with metadata, virtual path, and S3 location.
    Does not contain file data (stored in S3) - only metadata and references.
    
    Access Patterns (DynamoDB Keys):
    - pk: FILE#{tenant_id}#{file_id}
    - sk: METADATA
    - gsi1_pk: TENANT#{tenant_id}
    - gsi1_sk: DIRECTORY#{directory_id}#{file_name}
    - gsi2_pk: TENANT#{tenant_id}#USER#{owner_id}
    - gsi2_sk: FILE#{created_utc_ts}
    
    Versioning Strategies:
    - "s3_native": Same S3 key, S3 manages versions
    - "explicit": Unique S3 key per version, we manage versions
    """

    def __init__(self):
        super().__init__()
        
        # File Identity
        self._file_id: str | None = None  # Unique file ID (same as self.id)
        
        # Ownership (inherited tenant_id from BaseModel)
        self._owner_id: str | None = None  # User who owns the file
        
        # File Information
        self._file_name: str | None = None  # Display name (e.g., "report.pdf")
        self._file_extension: str | None = None  # Extension (e.g., ".pdf")
        self._mime_type: str | None = None  # MIME type (e.g., "application/pdf")
        self._file_size: int = 0  # Size in bytes
        self._checksum: str | None = None  # MD5/SHA256 checksum
        
        # Virtual Location (logical structure in DynamoDB)
        self._directory_id: str | None = None  # Parent directory ID (null = root)
        self._virtual_path: str | None = None  # Full virtual path (/docs/reports/Q1.pdf)
        
        # S3 Physical Location
        self._s3_bucket: str | None = None  # S3 bucket name
        self._s3_key: str | None = None  # S3 object key (physical location)
        self._s3_version_id: str | None = None  # S3 version ID (for s3_native strategy)
        
        # Versioning Strategy
        self._versioning_strategy: str = "explicit"  # "s3_native" or "explicit"
        self._current_version_id: str | None = None  # Current version identifier
        self._version_count: int = 0  # Total number of versions
        
        # Metadata
        self._description: str | None = None  # Optional description
        self._tags: List[str] = []  # Searchable tags
        
        # State
        self._status: str = "active"  # "active", "archived", "deleted"
        self._is_shared: bool = False  # Has active shares
        
        # Timestamps (inherited from BaseModel)
        # created_utc_ts, updated_utc_ts, deleted_utc_ts
    
    # Properties - File Identity
    @property
    def file_id(self) -> str | None:
        """Unique file ID."""
        return self._file_id or self.id
    
    @file_id.setter
    def file_id(self, value: str | None):
        self._file_id = value
        if value:
            self.id = value
    
    # Properties - Ownership
    @property
    def owner_id(self) -> str | None:
        """User who owns the file."""
        return self._owner_id
    
    @owner_id.setter
    def owner_id(self, value: str | None):
        self._owner_id = value
    
    # Properties - File Information
    @property
    def file_name(self) -> str | None:
        """Display file name."""
        return self._file_name
    
    @file_name.setter
    def file_name(self, value: str | None):
        self._file_name = value
    
    @property
    def file_extension(self) -> str | None:
        """File extension (e.g., '.pdf')."""
        return self._file_extension
    
    @file_extension.setter
    def file_extension(self, value: str | None):
        self._file_extension = value
    
    @property
    def mime_type(self) -> str | None:
        """MIME type (e.g., 'application/pdf')."""
        return self._mime_type
    
    @mime_type.setter
    def mime_type(self, value: str | None):
        self._mime_type = value
    
    @property
    def file_size(self) -> int:
        """File size in bytes."""
        return self._file_size
    
    @file_size.setter
    def file_size(self, value: int):
        self._file_size = value if value is not None else 0
    
    @property
    def checksum(self) -> str | None:
        """File checksum (MD5/SHA256)."""
        return self._checksum
    
    @checksum.setter
    def checksum(self, value: str | None):
        self._checksum = value
    
    # Properties - Virtual Location
    @property
    def directory_id(self) -> str | None:
        """Parent directory ID (null = root)."""
        return self._directory_id
    
    @directory_id.setter
    def directory_id(self, value: str | None):
        self._directory_id = value
    
    @property
    def virtual_path(self) -> str | None:
        """Full virtual path (e.g., /docs/reports/Q1.pdf)."""
        return self._virtual_path
    
    @virtual_path.setter
    def virtual_path(self, value: str | None):
        self._virtual_path = value
    
    # Properties - S3 Physical Location
    @property
    def s3_bucket(self) -> str | None:
        """S3 bucket name."""
        return self._s3_bucket
    
    @s3_bucket.setter
    def s3_bucket(self, value: str | None):
        self._s3_bucket = value
    
    @property
    def s3_key(self) -> str | None:
        """S3 object key (physical location)."""
        return self._s3_key
    
    @s3_key.setter
    def s3_key(self, value: str | None):
        self._s3_key = value
    
    @property
    def s3_version_id(self) -> str | None:
        """S3 version ID (for s3_native versioning)."""
        return self._s3_version_id
    
    @s3_version_id.setter
    def s3_version_id(self, value: str | None):
        self._s3_version_id = value
    
    # Properties - Versioning
    @property
    def versioning_strategy(self) -> str:
        """Versioning strategy: 's3_native' or 'explicit'."""
        return self._versioning_strategy
    
    @versioning_strategy.setter
    def versioning_strategy(self, value: str):
        if value not in ["s3_native", "explicit"]:
            raise ValueError(f"Invalid versioning strategy: {value}. Must be 's3_native' or 'explicit'")
        self._versioning_strategy = value
    
    @property
    def current_version_id(self) -> str | None:
        """Current version identifier."""
        return self._current_version_id
    
    @current_version_id.setter
    def current_version_id(self, value: str | None):
        self._current_version_id = value
    
    @property
    def version_count(self) -> int:
        """Total number of versions."""
        return self._version_count
    
    @version_count.setter
    def version_count(self, value: int):
        self._version_count = value if value is not None else 0
    
    # Properties - Metadata
    @property
    def description(self) -> str | None:
        """File description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    @property
    def tags(self) -> List[str]:
        """Searchable tags."""
        return self._tags
    
    @tags.setter
    def tags(self, value: List[str] | None):
        self._tags = value if isinstance(value, list) else []
    
    # Properties - State
    @property
    def status(self) -> str:
        """File status: 'active', 'archived', 'deleted'."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value not in ["active", "archived", "deleted"]:
            raise ValueError(f"Invalid status: {value}. Must be 'active', 'archived', or 'deleted'")
        self._status = value
    
    @property
    def is_shared(self) -> bool:
        """Has active shares."""
        return self._is_shared
    
    @is_shared.setter
    def is_shared(self, value: bool):
        self._is_shared = bool(value)
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if file is active."""
        return self._status == "active"
    
    def is_archived(self) -> bool:
        """Check if file is archived."""
        return self._status == "archived"
    
    def is_in_root(self) -> bool:
        """Check if file is in root directory."""
        return self._directory_id is None or self._directory_id == ""
    
    def uses_s3_native_versioning(self) -> bool:
        """Check if using S3 native versioning."""
        return self._versioning_strategy == "s3_native"
    
    def uses_explicit_versioning(self) -> bool:
        """Check if using explicit versioning."""
        return self._versioning_strategy == "explicit"
    
    def get_file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self._file_size / (1024 * 1024) if self._file_size else 0.0
    
    def get_file_size_kb(self) -> float:
        """Get file size in kilobytes."""
        return self._file_size / 1024 if self._file_size else 0.0
    
    def add_tag(self, tag: str):
        """Add a tag to the file."""
        if tag and tag not in self._tags:
            self._tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the file."""
        if tag in self._tags:
            self._tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if file has a specific tag."""
        return tag in self._tags
    
    def increment_version_count(self):
        """Increment the version count."""
        self._version_count += 1
    
    def get_s3_uri(self) -> str | None:
        """Get full S3 URI (s3://bucket/key)."""
        if self._s3_bucket and self._s3_key:
            return f"s3://{self._s3_bucket}/{self._s3_key}"
        return None
