"""
FileSystemService for file CRUD operations with S3 and DynamoDB.

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
from geek_cafe_saas_sdk.domains.files.models.file import File
from geek_cafe_saas_sdk.domains.files.services.s3_file_service import S3FileService
import os
from pathlib import Path


class FileSystemService(DatabaseService[File]):
    """
    File system service for managing files with S3 storage and DynamoDB metadata.
    
    Handles:
    - File uploads with metadata storage
    - File downloads with access control
    - File metadata CRUD operations
    - Directory assignment
    - Versioning strategy management
    """
    
    def __init__(
        self,
        *,
        dynamodb: Optional[DynamoDB] = None,
        table_name: Optional[str] = None,
        s3_service: Optional[S3FileService] = None,
        default_bucket: Optional[str] = None
    ):
        """
        Initialize FileSystemService.
        
        Args:
            dynamodb: DynamoDB instance
            table_name: DynamoDB table name
            s3_service: S3FileService instance
            default_bucket: Default S3 bucket
        """
        super().__init__(dynamodb=dynamodb, table_name=table_name)
        self.s3_service = s3_service or S3FileService(default_bucket=default_bucket)
        self.default_bucket = default_bucket or os.getenv("S3_FILE_BUCKET")
    
    def create(
        self,
        tenant_id: str,
        user_id: str,
        file_name: str,
        file_data: bytes,
        mime_type: str,
        directory_id: Optional[str] = None,
        versioning_strategy: str = "explicit",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> ServiceResult[File]:
        """
        Upload a file with metadata.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID (file owner)
            file_name: File name
            file_data: File content bytes
            mime_type: MIME type
            directory_id: Optional parent directory ID
            versioning_strategy: "s3_native" or "explicit"
            description: Optional description
            tags: Optional tags
            
        Returns:
            ServiceResult with File model
        """
        try:
            # Validate inputs
            if not file_name:
                raise ValidationError("File name is required", "file_name")
            
            if not file_data:
                raise ValidationError("File data is required", "file_data")
            
            if versioning_strategy not in ["s3_native", "explicit"]:
                raise ValidationError(
                    "Versioning strategy must be 's3_native' or 'explicit'",
                    "versioning_strategy"
                )
            
            # Create File model
            file = File()
            file.prep_for_save()
            file.tenant_id = tenant_id
            file.owner_id = user_id
            file.file_name = file_name
            file.mime_type = mime_type
            file.file_size = len(file_data)
            file.directory_id = directory_id
            file.versioning_strategy = versioning_strategy
            file.description = description
            file.tags = tags or []
            file.status = "active"
            
            # Extract file extension
            file_path = Path(file_name)
            file.file_extension = file_path.suffix if file_path.suffix else None
            
            # Build S3 key based on versioning strategy
            if versioning_strategy == "s3_native":
                # Same key for all versions - S3 handles versioning
                s3_key = f"{tenant_id}/files/{file.file_id}/{file_name}"
            else:
                # Explicit versioning - unique key per version
                version_id = file.id  # Use file ID as first version ID
                s3_key = f"{tenant_id}/files/{file.file_id}/versions/{version_id}/{file_name}"
                file.current_version_id = version_id
            
            file.s3_bucket = self.default_bucket
            file.s3_key = s3_key
            file.version_count = 1
            
            # Build virtual path
            if directory_id:
                # TODO: Get directory path from DirectoryService
                file.virtual_path = f"/{file_name}"
            else:
                file.virtual_path = f"/{file_name}"
            
            # Upload to S3
            upload_result = self.s3_service.upload_file(
                file_data=file_data,
                key=s3_key,
                bucket=self.default_bucket
            )
            
            if not upload_result.success:
                return ServiceResult.error_result(
                    message=f"Failed to upload file to S3: {upload_result.message}",
                    error_code=upload_result.error_code
                )
            
            # Save metadata to DynamoDB
            pk = f"FILE#{tenant_id}#{file.file_id}"
            sk = "METADATA"
            
            item = file.to_dictionary()
            item["pk"] = pk
            item["sk"] = sk
            
            # GSI1: Files by directory
            item["gsi1_pk"] = f"TENANT#{tenant_id}"
            if directory_id:
                item["gsi1_sk"] = f"DIRECTORY#{directory_id}#{file_name}"
            else:
                item["gsi1_sk"] = f"DIRECTORY#ROOT#{file_name}"
            
            # GSI2: Files by owner
            item["gsi2_pk"] = f"TENANT#{tenant_id}#USER#{user_id}"
            item["gsi2_sk"] = f"FILE#{file.created_utc_ts}"
            
            self.dynamodb.save(
                table_name=self.table_name,
                item=item
            )
            
            return ServiceResult.success_result(file)
            
        except ValidationError as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.VALIDATION_ERROR
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.create"
            )
    
    def get_by_id(
        self,
        resource_id: str,
        tenant_id: str,
        user_id: str
    ) -> ServiceResult[File]:
        """
        Get file by ID with access control.
        
        Args:
            resource_id: File ID
            tenant_id: Tenant ID
            user_id: User ID (for access control)
            
        Returns:
            ServiceResult with File model
        """
        try:
            pk = f"FILE#{tenant_id}#{resource_id}"
            sk = "METADATA"
            
            result = self.dynamodb.get(
                table_name=self.table_name,
                key={"pk": pk, "sk": sk}
            )
            
            # Check if file exists first (before checking ownership)
            # DynamoDB.get returns {'Item': {...}} or {'ResponseMetadata': {...}}
            if not result or 'Item' not in result:
                raise NotFoundError(f"File not found: {resource_id}")
            
            # Convert to File model
            file = File()
            file.map(result['Item'])
            
            # Access control: Check if user is owner or has share access
            if file.owner_id != user_id:
                # TODO: Check FileShare for access
                raise AccessDeniedError("You do not have access to this file")
            
            return ServiceResult.success_result(file)
            
        except NotFoundError as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.NOT_FOUND
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
                context="FileSystemService.get_by_id"
            )
    
    def update(
        self,
        resource_id: str,
        tenant_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> ServiceResult[File]:
        """
        Update file metadata.
        
        Args:
            resource_id: File ID
            tenant_id: Tenant ID
            user_id: User ID (for access control)
            updates: Dictionary of fields to update
            
        Returns:
            ServiceResult with updated File model
        """
        try:
            # Get existing file
            get_result = self.get_by_id(resource_id, tenant_id, user_id)
            if not get_result.success:
                return get_result
            
            file = get_result.data
            
            # Only owner can update
            if file.owner_id != user_id:
                raise AccessDeniedError("Only the owner can update this file")
            
            # Apply updates (only allowed fields)
            allowed_fields = [
                "file_name", "description", "tags", "directory_id",
                "status"
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(file, field, value)
            
            # Update timestamp
            import datetime as dt
            file.updated_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            # Save to DynamoDB
            pk = f"FILE#{tenant_id}#{resource_id}"
            sk = "METADATA"
            
            item = file.to_dictionary()
            item["pk"] = pk
            item["sk"] = sk
            
            # Update GSI keys if directory changed
            if "directory_id" in updates:
                item["gsi1_pk"] = f"TENANT#{tenant_id}"
                if updates["directory_id"]:
                    item["gsi1_sk"] = f"DIRECTORY#{updates['directory_id']}#{file.file_name}"
                else:
                    item["gsi1_sk"] = f"DIRECTORY#ROOT#{file.file_name}"
            
            self.dynamodb.save(
                table_name=self.table_name,
                item=item
            )
            
            return ServiceResult.success_result(file)
            
        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.update"
            )
    
    def delete(
        self,
        resource_id: str,
        tenant_id: str,
        user_id: str,
        hard_delete: bool = False
    ) -> ServiceResult[bool]:
        """
        Delete file (soft or hard delete).
        
        Args:
            resource_id: File ID
            tenant_id: Tenant ID
            user_id: User ID (for access control)
            hard_delete: If True, delete from S3 and DynamoDB. If False, mark as deleted.
            
        Returns:
            ServiceResult with success boolean
        """
        try:
            # Get existing file
            get_result = self.get_by_id(resource_id, tenant_id, user_id)
            if not get_result.success:
                return get_result
            
            file = get_result.data
            
            # Only owner can delete
            if file.owner_id != user_id:
                raise AccessDeniedError("Only the owner can delete this file")
            
            if hard_delete:
                # Delete from S3
                if file.s3_key:
                    delete_result = self.s3_service.delete_file(
                        key=file.s3_key,
                        bucket=file.s3_bucket
                    )
                    
                    if not delete_result.success:
                        return ServiceResult.error_result(
                            message=f"Failed to delete file from S3: {delete_result.message}",
                            error_code=delete_result.error_code
                        )
                
                # Delete from DynamoDB
                pk = f"FILE#{tenant_id}#{resource_id}"
                sk = "METADATA"
                
                self.dynamodb.delete(
                    primary_key={"pk": pk, "sk": sk},
                    table_name=self.table_name
                )
            else:
                # Soft delete - update status
                import datetime as dt
                file.status = "deleted"
                file.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
                
                pk = f"FILE#{tenant_id}#{resource_id}"
                sk = "METADATA"
                
                item = file.to_dictionary()
                item["pk"] = pk
                item["sk"] = sk
                
                self.dynamodb.save(
                    table_name=self.table_name,
                    item=item
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
                context="FileSystemService.delete"
            )
    
    def download_file(
        self,
        file_id: str,
        tenant_id: str,
        user_id: str
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Download file with access control.
        
        Args:
            file_id: File ID
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            ServiceResult with file data and metadata
        """
        try:
            # Get file metadata
            get_result = self.get_by_id(file_id, tenant_id, user_id)
            if not get_result.success:
                return get_result
            
            file = get_result.data
            
            # Download from S3
            download_result = self.s3_service.download_file(
                key=file.s3_key,
                bucket=file.s3_bucket
            )
            
            if not download_result.success:
                return ServiceResult.error_result(
                    message=f"Failed to download file from S3: {download_result.message}",
                    error_code=download_result.error_code
                )
            
            # Combine file data with metadata
            return ServiceResult.success_result({
                "file": file,
                "data": download_result.data["data"],
                "content_type": download_result.data.get("content_type", file.mime_type),
                "size": download_result.data.get("size", file.file_size)
            })
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.download_file"
            )
    
    def list_files_by_directory(
        self,
        tenant_id: str,
        directory_id: Optional[str],
        user_id: str,
        limit: int = 50
    ) -> ServiceResult[List[File]]:
        """
        List files in a directory.
        
        Args:
            tenant_id: Tenant ID
            directory_id: Directory ID (None for root)
            user_id: User ID (for access control)
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of File models
        """
        try:
            gsi1_pk = f"TENANT#{tenant_id}"
            
            if directory_id:
                gsi1_sk_prefix = f"DIRECTORY#{directory_id}#"
            else:
                gsi1_sk_prefix = "DIRECTORY#ROOT#"
            
            # Query GSI1
            results = self.dynamodb.query(
                key=Key('gsi1_pk').eq(gsi1_pk) & Key('gsi1_sk').begins_with(gsi1_sk_prefix),
                table_name=self.table_name,
                index_name="gsi1",
                limit=limit
            )
            
            files = []
            for item in results.get('Items', []):
                file = File()
                file.map(item)
                
                # Filter out deleted files
                if file.status != "deleted":
                    # Basic access control: show only owned files or shared files
                    # TODO: Check FileShare for shared access
                    if file.owner_id == user_id:
                        files.append(file)
            
            return ServiceResult.success_result(files)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.list_files_by_directory"
            )
    
    def list_files_by_owner(
        self,
        tenant_id: str,
        owner_id: str,
        user_id: str,
        limit: int = 50
    ) -> ServiceResult[List[File]]:
        """
        List files owned by a user.
        
        Args:
            tenant_id: Tenant ID
            owner_id: Owner user ID
            user_id: Requesting user ID (for access control)
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of File models
        """
        try:
            # Can only list own files
            if owner_id != user_id:
                raise AccessDeniedError("You can only list your own files")
            
            gsi2_pk = f"TENANT#{tenant_id}#USER#{owner_id}"
            
            # Query GSI2
            results = self.dynamodb.query(
                key=Key('gsi2_pk').eq(gsi2_pk) & Key('gsi2_sk').begins_with("FILE#"),
                table_name=self.table_name,
                index_name="gsi2",
                limit=limit
            )
            
            files = []
            for item in results.get('Items', []):
                file = File()
                file.map(item)
                
                # Filter out deleted files
                if file.status != "deleted":
                    files.append(file)
            
            return ServiceResult.success_result(files)
            
        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.list_files_by_owner"
            )
