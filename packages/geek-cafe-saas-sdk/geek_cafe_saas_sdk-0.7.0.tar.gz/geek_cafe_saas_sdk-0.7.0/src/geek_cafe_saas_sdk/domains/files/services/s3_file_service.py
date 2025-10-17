"""
S3 file operations service using boto3-assist.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional, Dict, Any
from boto3_assist.s3.s3_object import S3Object
from boto3_assist.s3.s3_bucket import S3Bucket
from boto3_assist.s3.s3_connection import S3Connection
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
import os


class S3FileService:
    """
    S3 file operations using boto3-assist.
    
    Handles all S3 operations including upload, download, delete,
    presigned URLs, and versioning. Supports dependency injection
    for testing with Moto.
    
    Configuration (Environment Variables):
    - FILE_UPLOAD_MAX_SIZE: Maximum file size in bytes (default: 104857600 = 100MB)
    - FILE_PRESIGNED_URL_EXPIRY: Presigned URL expiration in seconds (default: 300)
    - S3_FILE_BUCKET: Default S3 bucket name
    """
    
    def __init__(
        self, 
        s3_object: Optional[S3Object] = None,
        s3_bucket: Optional[S3Bucket] = None,
        default_bucket: Optional[str] = None
    ):
        """
        Initialize S3 service.
        
        Args:
            s3_object: S3Object instance (inject for testing with Moto)
            s3_bucket: S3Bucket instance (inject for testing)
            default_bucket: Default bucket name (from env or parameter)
        """
        if s3_object is None:
            # Create connection and S3Object if not provided
            self.connection = S3Connection()
            self.s3_object = S3Object(connection=self.connection)
            self.s3_bucket = s3_bucket or S3Bucket(connection=self.connection)
        else:
            self.s3_object = s3_object
            # If bucket not provided, need to create connection
            if s3_bucket is None:
                self.connection = S3Connection()
                self.s3_bucket = S3Bucket(connection=self.connection)
            else:
                self.s3_bucket = s3_bucket
                # Try to get connection from s3_object
                self.connection = getattr(s3_object, 'connection', S3Connection())
            
        self.default_bucket = default_bucket or os.getenv("S3_FILE_BUCKET")
        
        # Configuration
        self.max_file_size = int(os.getenv("FILE_UPLOAD_MAX_SIZE", "104857600"))  # 100MB
        self.presigned_url_expiry = int(os.getenv("FILE_PRESIGNED_URL_EXPIRY", "300"))  # 5 minutes
    
    def upload_file(
        self,
        file_data: bytes,
        key: str,
        bucket: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> ServiceResult:
        """
        Upload file to S3.
        
        Args:
            file_data: File content as bytes
            key: S3 object key
            bucket: Bucket name (uses default if not provided)
            metadata: Custom metadata
            content_type: MIME type
            
        Returns:
            ServiceResult with upload details
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Validate file size
            if len(file_data) > self.max_file_size:
                return ServiceResult.error_result(
                    message=f"File size exceeds maximum allowed size of {self.max_file_size} bytes",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Upload to S3
            self.s3_object.put(
                bucket=bucket_name,
                key=key,
                data=file_data
            )
            
            # Note: boto3-assist S3Object.put doesn't support metadata/content_type directly
            # For production, you may need to use boto3 client directly or extend S3Object
            
            return ServiceResult.success_result({
                "bucket": bucket_name,
                "key": key,
                "size": len(file_data),
                "s3_uri": f"s3://{bucket_name}/{key}"
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to upload file to S3: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    def download_file(
        self,
        key: str,
        bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        Download file from S3.
        
        Args:
            key: S3 object key
            bucket: Bucket name
            
        Returns:
            ServiceResult with file data
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            response = self.s3_object.get_object(
                bucket_name=bucket_name,
                key=key
            )
            
            file_data = response['Body'].read()
            
            return ServiceResult.success_result({
                "data": file_data,
                "content_type": response.get('ContentType'),
                "size": response.get('ContentLength'),
                "metadata": response.get('Metadata', {}),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag')
            })
            
        except Exception as e:
            # Check if it's a NoSuchKey error
            if 'NoSuchKey' in str(e) or 'Not Found' in str(e) or '404' in str(e):
                return ServiceResult.error_result(
                    message=f"File not found: {key}",
                    error_code=ErrorCode.NOT_FOUND
                )
            return ServiceResult.error_result(
                message=f"Failed to download file from S3: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    def delete_file(
        self,
        key: str,
        bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        Delete file from S3.
        
        Args:
            key: S3 object key
            bucket: Bucket name
            
        Returns:
            ServiceResult with deletion details
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            self.s3_object.delete(
                bucket_name=bucket_name,
                key=key
            )
            
            return ServiceResult.success_result({
                "deleted": key,
                "bucket": bucket_name
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to delete file from S3: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    def generate_presigned_upload_url(
        self,
        key: str,
        file_name: str,
        bucket: Optional[str] = None,
        expires_in: Optional[int] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> ServiceResult:
        """
        Generate presigned URL for file upload.
        
        Args:
            key: S3 object key
            file_name: Original file name
            bucket: Bucket name
            expires_in: Expiration time in seconds
            content_type: MIME type
            metadata: Custom metadata
            
        Returns:
            ServiceResult with presigned URL
        """
        try:
            bucket_name = bucket or self.default_bucket
            expiry = expires_in or self.presigned_url_expiry
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            url_data = self.s3_object.generate_presigned_url(
                bucket_name=bucket_name,
                key_path=key,
                file_name=file_name,
                meta_data=metadata,
                expiration=expiry,
                method_type='POST'
            )
            
            return ServiceResult.success_result({
                "url": url_data.get('url'),
                "fields": url_data.get('fields', {}),
                "expires_in": expiry,
                "key": key
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to generate presigned upload URL: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    def generate_presigned_download_url(
        self,
        key: str,
        bucket: Optional[str] = None,
        expires_in: Optional[int] = None,
        file_name: Optional[str] = None
    ) -> ServiceResult:
        """
        Generate presigned URL for file download.
        
        Args:
            key: S3 object key
            bucket: Bucket name
            expires_in: Expiration time in seconds
            file_name: Optional filename for download
            
        Returns:
            ServiceResult with presigned URL
        """
        try:
            bucket_name = bucket or self.default_bucket
            expiry = expires_in or self.presigned_url_expiry
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Use file_name or extract from key
            download_name = file_name or key.split('/')[-1]
            
            url_data = self.s3_object.generate_presigned_url(
                bucket_name=bucket_name,
                key_path=key,
                file_name=download_name,
                expiration=expiry,
                method_type='GET'
            )
            
            return ServiceResult.success_result({
                "url": url_data.get('url'),
                "expires_in": expiry,
                "key": key
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to generate presigned download URL: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    def list_object_versions(
        self,
        key: str,
        bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        List all versions of an object (for S3 native versioning).
        
        Args:
            key: S3 object key
            bucket: Bucket name
            
        Returns:
            ServiceResult with versions list
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            versions = self.s3_object.list_versions(
                bucket=bucket_name,
                prefix=key
            )
            
            return ServiceResult.success_result({
                "versions": versions,
                "key": key,
                "bucket": bucket_name
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to list object versions: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    def copy_object(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: Optional[str] = None,
        dest_bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        Copy object within S3.
        
        Args:
            source_key: Source S3 key
            dest_key: Destination S3 key
            source_bucket: Source bucket (default bucket if not provided)
            dest_bucket: Destination bucket (default bucket if not provided)
            
        Returns:
            ServiceResult with copy details
        """
        try:
            src_bucket = source_bucket or self.default_bucket
            dst_bucket = dest_bucket or self.default_bucket
            
            if not src_bucket or not dst_bucket:
                return ServiceResult.error_result(
                    message="S3 bucket names are required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            self.s3_object.copy(
                source_bucket=src_bucket,
                source_key=source_key,
                destination_bucket=dst_bucket,
                destination_key=dest_key
            )
            
            return ServiceResult.success_result({
                "source": f"s3://{src_bucket}/{source_key}",
                "destination": f"s3://{dst_bucket}/{dest_key}"
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to copy object: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    def enable_bucket_versioning(
        self,
        bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        Enable versioning on S3 bucket.
        
        Args:
            bucket: Bucket name
            
        Returns:
            ServiceResult with status
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            self.s3_bucket.enable_versioning(
                bucket_name=bucket_name
            )
            
            return ServiceResult.success_result({
                "versioning_enabled": True,
                "bucket": bucket_name
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to enable bucket versioning: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    def get_object_metadata(
        self,
        key: str,
        bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        Get S3 object metadata without downloading file.
        
        Args:
            key: S3 object key
            bucket: Bucket name
            
        Returns:
            ServiceResult with metadata
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Use head_object to get metadata without downloading
            response = self.connection.client.head_object(
                Bucket=bucket_name,
                Key=key
            )
            
            return ServiceResult.success_result({
                "content_type": response.get('ContentType'),
                "size": response.get('ContentLength'),
                "metadata": response.get('Metadata', {}),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag'),
                "version_id": response.get('VersionId'),
                "storage_class": response.get('StorageClass')
            })
            
        except Exception as e:
            # Check if it's a NoSuchKey error
            if '404' in str(e) or 'NoSuchKey' in str(e) or 'Not Found' in str(e):
                return ServiceResult.error_result(
                    message=f"File not found: {key}",
                    error_code=ErrorCode.NOT_FOUND
                )
            return ServiceResult.error_result(
                message=f"Failed to get object metadata: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
