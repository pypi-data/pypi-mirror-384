"""
Directory model for virtual directory structure.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
import datetime as dt
from typing import Optional, Dict, Any
from geek_cafe_saas_sdk.models.base_model import BaseModel


class Directory(BaseModel):
    """
    Virtual directory in the file system.
    
    Represents a logical directory structure. Files reference directories
    via directory_id, but are physically stored in S3 with their own keys.
    Moving a file updates its directory_id, not its S3 location.
    
    Access Patterns (DynamoDB Keys):
    - pk: DIRECTORY#{tenant_id}#{directory_id}
    - sk: METADATA
    - gsi1_pk: TENANT#{tenant_id}
    - gsi1_sk: PATH#{full_path}
    - gsi2_pk: DIRECTORY#{tenant_id}#{parent_id}
    - gsi2_sk: NAME#{directory_name}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._directory_id: str | None = None  # Unique directory ID
        
        # Ownership
        self._owner_id: str | None = None  # User who created directory
        
        # Directory Information
        self._directory_name: str | None = None  # Display name (e.g., "Projects")
        self._full_path: str | None = None  # Complete path (/root/projects/2024)
        
        # Hierarchy
        self._parent_id: str | None = None  # Parent directory (null = root)
        self._depth: int = 0  # Depth in tree (0 = root level)
        
        # Contents Tracking
        self._file_count: int = 0  # Number of files in this directory
        self._subdirectory_count: int = 0  # Number of subdirectories
        self._total_size: int = 0  # Total size of all files (bytes)
        
        # Metadata
        self._description: str | None = None
        self._color: str | None = None  # UI color code (e.g., "#FF5733")
        self._icon: str | None = None  # UI icon identifier
        
        # State
        self._status: str = "active"  # "active", "archived", "deleted"
        
        # Timestamps (inherited from BaseModel)
        # created_utc_ts, updated_utc_ts
    
    # Properties - Identity
    @property
    def directory_id(self) -> str | None:
        """Unique directory ID."""
        return self._directory_id or self.id
    
    @directory_id.setter
    def directory_id(self, value: str | None):
        self._directory_id = value
        if value:
            self.id = value
    
    # Properties - Ownership
    @property
    def owner_id(self) -> str | None:
        """User who created directory."""
        return self._owner_id
    
    @owner_id.setter
    def owner_id(self, value: str | None):
        self._owner_id = value
    
    # Properties - Directory Information
    @property
    def directory_name(self) -> str | None:
        """Directory display name."""
        return self._directory_name
    
    @directory_name.setter
    def directory_name(self, value: str | None):
        self._directory_name = value
    
    @property
    def full_path(self) -> str | None:
        """Complete path from root."""
        return self._full_path
    
    @full_path.setter
    def full_path(self, value: str | None):
        self._full_path = value
    
    # Properties - Hierarchy
    @property
    def parent_id(self) -> str | None:
        """Parent directory ID (null = root)."""
        return self._parent_id
    
    @parent_id.setter
    def parent_id(self, value: str | None):
        self._parent_id = value
    
    @property
    def depth(self) -> int:
        """Depth in directory tree."""
        return self._depth
    
    @depth.setter
    def depth(self, value: int):
        self._depth = value if value is not None else 0
    
    # Properties - Contents Tracking
    @property
    def file_count(self) -> int:
        """Number of files in this directory."""
        return self._file_count
    
    @file_count.setter
    def file_count(self, value: int):
        self._file_count = value if value is not None else 0
    
    @property
    def subdirectory_count(self) -> int:
        """Number of subdirectories."""
        return self._subdirectory_count
    
    @subdirectory_count.setter
    def subdirectory_count(self, value: int):
        self._subdirectory_count = value if value is not None else 0
    
    @property
    def total_size(self) -> int:
        """Total size of all files in bytes."""
        return self._total_size
    
    @total_size.setter
    def total_size(self, value: int):
        self._total_size = value if value is not None else 0
    
    # Properties - Metadata
    @property
    def description(self) -> str | None:
        """Directory description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    @property
    def color(self) -> str | None:
        """UI color code."""
        return self._color
    
    @color.setter
    def color(self, value: str | None):
        self._color = value
    
    @property
    def icon(self) -> str | None:
        """UI icon identifier."""
        return self._icon
    
    @icon.setter
    def icon(self, value: str | None):
        self._icon = value
    
    # Properties - State
    @property
    def status(self) -> str:
        """Directory status: 'active', 'archived', 'deleted'."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value not in ["active", "archived", "deleted"]:
            raise ValueError(f"Invalid status: {value}. Must be 'active', 'archived', or 'deleted'")
        self._status = value
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if directory is active."""
        return self._status == "active"
    
    def is_archived(self) -> bool:
        """Check if directory is archived."""
        return self._status == "archived"
    
    def is_root(self) -> bool:
        """Check if this is a root directory."""
        return self._parent_id is None or self._parent_id == ""
    
    def is_empty(self) -> bool:
        """Check if directory has no files or subdirectories."""
        return self._file_count == 0 and self._subdirectory_count == 0
    
    def has_files(self) -> bool:
        """Check if directory contains files."""
        return self._file_count > 0
    
    def has_subdirectories(self) -> bool:
        """Check if directory contains subdirectories."""
        return self._subdirectory_count > 0
    
    def get_total_size_mb(self) -> float:
        """Get total size in megabytes."""
        return self._total_size / (1024 * 1024) if self._total_size else 0.0
    
    def get_total_size_gb(self) -> float:
        """Get total size in gigabytes."""
        return self._total_size / (1024 * 1024 * 1024) if self._total_size else 0.0
    
    def increment_file_count(self, count: int = 1):
        """Increment the file count."""
        self._file_count += count
    
    def decrement_file_count(self, count: int = 1):
        """Decrement the file count."""
        self._file_count = max(0, self._file_count - count)
    
    def increment_subdirectory_count(self, count: int = 1):
        """Increment the subdirectory count."""
        self._subdirectory_count += count
    
    def decrement_subdirectory_count(self, count: int = 1):
        """Decrement the subdirectory count."""
        self._subdirectory_count = max(0, self._subdirectory_count - count)
    
    def add_to_total_size(self, size: int):
        """Add to total size."""
        self._total_size += size
    
    def subtract_from_total_size(self, size: int):
        """Subtract from total size."""
        self._total_size = max(0, self._total_size - size)
    
    def get_path_parts(self) -> list:
        """Get path as list of parts (e.g., '/a/b/c' -> ['a', 'b', 'c'])."""
        if not self._full_path:
            return []
        return [p for p in self._full_path.split('/') if p]
    
    def get_path_depth(self) -> int:
        """Calculate depth from path."""
        return len(self.get_path_parts())
