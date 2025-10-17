"""
FileShareService for permission-based file sharing.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from boto3.dynamodb.conditions import Key
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.domains.files.models.file_share import FileShare
from geek_cafe_saas_sdk.domains.files.models.file import File
import datetime as dt


class FileShareService(DatabaseService[FileShare]):
    """
    File share service for permission-based file sharing.
    
    Handles:
    - Creating file shares with permissions
    - Access validation
    - Share expiration
    - Share revocation
    - Permission management (view, download, edit)
    """
    
    def create(
        self,
        tenant_id: str,
        user_id: str,
        file_id: str,
        shared_with_user_id: str,
        permission: str = "view",
        expires_at: Optional[float] = None,
        message: Optional[str] = None,
        **kwargs
    ) -> ServiceResult[FileShare]:
        """
        Create a file share.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID (file owner creating the share)
            file_id: File ID to share
            shared_with_user_id: User ID to share with
            permission: Permission level (view, download, edit)
            expires_at: Optional expiration timestamp
            message: Optional message for recipient
            
        Returns:
            ServiceResult with FileShare model
        """
        try:
            # Validate permission
            valid_permissions = ["view", "download", "edit"]
            if permission not in valid_permissions:
                raise ValidationError(
                    f"Invalid permission: {permission}. Must be one of {valid_permissions}",
                    "permission"
                )
            
            # Cannot share with self
            if shared_with_user_id == user_id:
                raise ValidationError(
                    "Cannot share file with yourself",
                    "shared_with_user_id"
                )
            
            # Get the file to verify ownership
            file_result = self._get_file(tenant_id, file_id, user_id)
            if not file_result.success:
                return ServiceResult.error_result(
                    message="File not found or you do not have permission to share it",
                    error_code=ErrorCode.ACCESS_DENIED
                )
            
            file = file_result.data
            
            # Only owner can share
            if file.owner_id != user_id:
                raise AccessDeniedError("Only the file owner can share this file")
            
            # Check for existing share
            existing_share = self._get_existing_share(
                tenant_id, file_id, shared_with_user_id
            )
            if existing_share:
                raise ValidationError(
                    "File is already shared with this user",
                    "shared_with_user_id"
                )
            
            # Create FileShare model
            share = FileShare()
            share.prep_for_save()
            share.tenant_id = tenant_id
            share.file_id = file_id
            share.shared_by = user_id
            share.shared_with_user_id = shared_with_user_id
            share.permission_level = permission
            share.expires_at = expires_at
            share.message = message
            share.status = "active"
            share.access_count = 0
            
            # Save to DynamoDB
            pk = f"FILE#{tenant_id}#{file_id}"
            sk = f"SHARE#{share.share_id}"
            
            item = share.to_dictionary()
            item["pk"] = pk
            item["sk"] = sk
            
            # GSI1: Shares by file
            item["gsi1_pk"] = f"FILE#{tenant_id}#{file_id}"
            item["gsi1_sk"] = f"USER#{shared_with_user_id}"
            
            # GSI2: Shares with user
            item["gsi2_pk"] = f"TENANT#{tenant_id}#USER#{shared_with_user_id}"
            item["gsi2_sk"] = f"FILE#{file_id}#{share.created_utc_ts}"
            
            self.dynamodb.save(
                item=item,
                table_name=self.table_name
            )
            
            return ServiceResult.success_result(share)
            
        except (ValidationError, AccessDeniedError) as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.VALIDATION_ERROR if isinstance(e, ValidationError) else ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileShareService.create"
            )
    
    def get_by_id(
        self,
        resource_id: str,
        tenant_id: str,
        user_id: str,
        file_id: Optional[str] = None
    ) -> ServiceResult[FileShare]:
        """
        Get share by ID.
        
        Args:
            resource_id: Share ID
            tenant_id: Tenant ID
            user_id: User ID (for access control)
            file_id: File ID (required)
            
        Returns:
            ServiceResult with FileShare model
        """
        try:
            if not file_id:
                raise ValidationError("file_id is required", "file_id")
            
            pk = f"FILE#{tenant_id}#{file_id}"
            sk = f"SHARE#{resource_id}"
            
            result = self.dynamodb.get(
                table_name=self.table_name,
                key={"pk": pk, "sk": sk}
            )
            
            if not result or 'Item' not in result:
                raise NotFoundError(f"Share not found: {resource_id}")
            
            share = FileShare()
            share.map(result['Item'])
            
            # Access control: user must be sharer or sharee
            if share.shared_by != user_id and share.shared_with_user_id != user_id:
                raise AccessDeniedError("You do not have access to this share")
            
            return ServiceResult.success_result(share)
            
        except (NotFoundError, ValidationError) as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.NOT_FOUND if isinstance(e, NotFoundError) else ErrorCode.VALIDATION_ERROR
            )
        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileShareService.get_by_id"
            )
    
    def update(
        self,
        resource_id: str,
        tenant_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> ServiceResult[FileShare]:
        """
        Update share (permission or expiration).
        
        Args:
            resource_id: Share ID
            tenant_id: Tenant ID
            user_id: User ID (must be sharer)
            updates: Dictionary of fields to update
            
        Returns:
            ServiceResult with updated FileShare model
        """
        try:
            file_id = updates.get('file_id')
            if not file_id:
                raise ValidationError("file_id is required in updates", "file_id")
            
            # Get existing share
            get_result = self.get_by_id(resource_id, tenant_id, user_id, file_id=file_id)
            if not get_result.success:
                return get_result
            
            share = get_result.data
            
            # Only sharer can update
            if share.shared_by != user_id:
                raise AccessDeniedError("Only the person who shared can update this share")
            
            # Apply updates (only allowed fields)
            allowed_fields = ["permission_level", "expires_at", "message"]
            
            for field, value in updates.items():
                if field == "permission_level":
                    valid_permissions = ["view", "download", "edit"]
                    if value not in valid_permissions:
                        raise ValidationError(
                            f"Invalid permission: {value}",
                            "permission_level"
                        )
                
                if field in allowed_fields:
                    setattr(share, field, value)
            
            share.updated_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            # Save to DynamoDB
            pk = f"FILE#{tenant_id}#{file_id}"
            sk = f"SHARE#{resource_id}"
            
            item = share.to_dictionary()
            item["pk"] = pk
            item["sk"] = sk
            
            # Preserve GSI keys
            item["gsi1_pk"] = f"FILE#{tenant_id}#{file_id}"
            item["gsi1_sk"] = f"USER#{share.shared_with_user_id}"
            item["gsi2_pk"] = f"TENANT#{tenant_id}#USER#{share.shared_with_user_id}"
            item["gsi2_sk"] = f"FILE#{file_id}#{share.created_utc_ts}"
            
            self.dynamodb.save(
                item=item,
                table_name=self.table_name
            )
            
            return ServiceResult.success_result(share)
            
        except (ValidationError, AccessDeniedError) as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.VALIDATION_ERROR if isinstance(e, ValidationError) else ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileShareService.update"
            )
    
    def delete(
        self,
        resource_id: str,
        tenant_id: str,
        user_id: str,
        file_id: str
    ) -> ServiceResult[bool]:
        """
        Revoke a share.
        
        Args:
            resource_id: Share ID
            tenant_id: Tenant ID
            user_id: User ID (must be sharer)
            file_id: File ID
            
        Returns:
            ServiceResult with success boolean
        """
        try:
            # Get existing share
            get_result = self.get_by_id(resource_id, tenant_id, user_id, file_id=file_id)
            if not get_result.success:
                return get_result
            
            share = get_result.data
            
            # Only sharer can revoke
            if share.shared_by != user_id:
                raise AccessDeniedError("Only the person who shared can revoke this share")
            
            # Mark as revoked
            share.status = "revoked"
            share.revoked_at = dt.datetime.now(dt.UTC).timestamp()
            
            pk = f"FILE#{tenant_id}#{file_id}"
            sk = f"SHARE#{resource_id}"
            
            item = share.to_dictionary()
            item["pk"] = pk
            item["sk"] = sk
            
            # Preserve GSI keys
            item["gsi1_pk"] = f"FILE#{tenant_id}#{file_id}"
            item["gsi1_sk"] = f"USER#{share.shared_with_user_id}"
            item["gsi2_pk"] = f"TENANT#{tenant_id}#USER#{share.shared_with_user_id}"
            item["gsi2_sk"] = f"FILE#{file_id}#{share.created_utc_ts}"
            
            self.dynamodb.save(
                item=item,
                table_name=self.table_name
            )
            
            return ServiceResult.success_result(True)
            
        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileShareService.delete"
            )
    
    def list_shares_by_file(
        self,
        tenant_id: str,
        file_id: str,
        user_id: str,
        limit: int = 50
    ) -> ServiceResult[List[FileShare]]:
        """
        List all shares for a file.
        
        Args:
            tenant_id: Tenant ID
            file_id: File ID
            user_id: User ID (must be file owner)
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of FileShare models
        """
        try:
            # Verify user owns the file
            file_result = self._get_file(tenant_id, file_id, user_id)
            if not file_result.success:
                return ServiceResult.error_result(
                    message="File not found or access denied",
                    error_code=ErrorCode.ACCESS_DENIED
                )
            
            # Query GSI1
            gsi1_pk = f"FILE#{tenant_id}#{file_id}"
            
            results = self.dynamodb.query(
                key=Key('gsi1_pk').eq(gsi1_pk) & Key('gsi1_sk').begins_with("USER#"),
                table_name=self.table_name,
                index_name="gsi1",
                limit=limit
            )
            
            shares = []
            for item in results.get('Items', []):
                share = FileShare()
                share.map(item)
                
                # Include active and expired shares, exclude revoked
                if share.status != "revoked":
                    shares.append(share)
            
            return ServiceResult.success_result(shares)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileShareService.list_shares_by_file"
            )
    
    def list_shares_with_user(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 50
    ) -> ServiceResult[List[FileShare]]:
        """
        List all files shared with a user.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of FileShare models
        """
        try:
            # Query GSI2
            gsi2_pk = f"TENANT#{tenant_id}#USER#{user_id}"
            
            results = self.dynamodb.query(
                key=Key('gsi2_pk').eq(gsi2_pk) & Key('gsi2_sk').begins_with("FILE#"),
                table_name=self.table_name,
                index_name="gsi2",
                limit=limit
            )
            
            shares = []
            for item in results.get('Items', []):
                share = FileShare()
                share.map(item)
                
                # Only include active, non-expired shares
                if share.is_active:
                    shares.append(share)
            
            return ServiceResult.success_result(shares)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileShareService.list_shares_with_user"
            )
    
    def check_access(
        self,
        tenant_id: str,
        file_id: str,
        user_id: str,
        required_permission: str = "view"
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Check if user has access to a file.
        
        Args:
            tenant_id: Tenant ID
            file_id: File ID
            user_id: User ID
            required_permission: Required permission level
            
        Returns:
            ServiceResult with access info (has_access, permission, reason)
        """
        try:
            # Get file
            file_result = self._get_file_any_user(tenant_id, file_id)
            if not file_result.success:
                return ServiceResult.success_result({
                    "has_access": False,
                    "permission": None,
                    "reason": "file_not_found"
                })
            
            file = file_result.data
            
            # Check if user is owner
            if file.owner_id == user_id:
                return ServiceResult.success_result({
                    "has_access": True,
                    "permission": "owner",
                    "reason": "owner"
                })
            
            # Check for active share
            share = self._get_existing_share(tenant_id, file_id, user_id)
            if not share:
                return ServiceResult.success_result({
                    "has_access": False,
                    "permission": None,
                    "reason": "no_share"
                })
            
            # Check if share is active
            if not share.is_active:
                reason = "expired" if share.is_expired else "revoked"
                return ServiceResult.success_result({
                    "has_access": False,
                    "permission": None,
                    "reason": reason
                })
            
            # Check permission level
            permission_levels = {"view": 1, "download": 2, "edit": 3}
            user_level = permission_levels.get(share.permission_level, 0)
            required_level = permission_levels.get(required_permission, 1)
            
            has_access = user_level >= required_level
            
            # Increment access count if accessing
            if has_access:
                self._increment_access_count(tenant_id, file_id, share.share_id)
            
            return ServiceResult.success_result({
                "has_access": has_access,
                "permission": share.permission_level,
                "reason": "granted" if has_access else "insufficient_permission"
            })
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileShareService.check_access"
            )
    
    # Helper methods
    
    def _get_file(self, tenant_id: str, file_id: str, user_id: str) -> ServiceResult[File]:
        """Get file with access control."""
        try:
            pk = f"FILE#{tenant_id}#{file_id}"
            sk = "METADATA"
            
            result = self.dynamodb.get(
                table_name=self.table_name,
                key={"pk": pk, "sk": sk}
            )
            
            if not result or 'Item' not in result:
                raise NotFoundError(f"File not found: {file_id}")
            
            file = File()
            file.map(result['Item'])
            
            if file.owner_id != user_id:
                raise AccessDeniedError("You do not have access to this file")
            
            return ServiceResult.success_result(file)
            
        except (NotFoundError, AccessDeniedError) as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.NOT_FOUND if isinstance(e, NotFoundError) else ErrorCode.ACCESS_DENIED
            )
    
    def _get_file_any_user(self, tenant_id: str, file_id: str) -> ServiceResult[File]:
        """Get file without access control (for internal use)."""
        try:
            pk = f"FILE#{tenant_id}#{file_id}"
            sk = "METADATA"
            
            result = self.dynamodb.get(
                table_name=self.table_name,
                key={"pk": pk, "sk": sk}
            )
            
            if not result or 'Item' not in result:
                raise NotFoundError(f"File not found: {file_id}")
            
            file = File()
            file.map(result['Item'])
            
            return ServiceResult.success_result(file)
            
        except NotFoundError as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.NOT_FOUND
            )
    
    def _get_existing_share(
        self,
        tenant_id: str,
        file_id: str,
        shared_with_user_id: str
    ) -> Optional[FileShare]:
        """Check if share already exists."""
        try:
            gsi1_pk = f"FILE#{tenant_id}#{file_id}"
            gsi1_sk = f"USER#{shared_with_user_id}"
            
            results = self.dynamodb.query(
                key=Key('gsi1_pk').eq(gsi1_pk) & Key('gsi1_sk').eq(gsi1_sk),
                table_name=self.table_name,
                index_name="gsi1",
                limit=1
            )
            
            items = results.get('Items', [])
            if items:
                share = FileShare()
                share.map(items[0])
                return share
            
            return None
            
        except Exception:
            return None
    
    def _increment_access_count(
        self,
        tenant_id: str,
        file_id: str,
        share_id: str
    ) -> None:
        """Increment share access count."""
        try:
            pk = f"FILE#{tenant_id}#{file_id}"
            sk = f"SHARE#{share_id}"
            
            result = self.dynamodb.get(
                table_name=self.table_name,
                key={"pk": pk, "sk": sk}
            )
            
            if result and 'Item' in result:
                share = FileShare()
                share.map(result['Item'])
                
                share.access_count += 1
                share.last_accessed_at = dt.datetime.now(dt.UTC).timestamp()
                
                item = share.to_dictionary()
                item["pk"] = pk
                item["sk"] = sk
                
                # Preserve GSI keys
                item["gsi1_pk"] = result['Item'].get('gsi1_pk')
                item["gsi1_sk"] = result['Item'].get('gsi1_sk')
                item["gsi2_pk"] = result['Item'].get('gsi2_pk')
                item["gsi2_sk"] = result['Item'].get('gsi2_sk')
                
                self.dynamodb.save(
                    item=item,
                    table_name=self.table_name
                )
        except Exception:
            pass  # Best effort
