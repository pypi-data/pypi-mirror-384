"""
File Lineage Service

Helper service for managing file lineage and transformations.
Works on top of FileSystemService.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, List, Optional
from geek_cafe_saas_sdk.domains.files.services.file_system_service import FileSystemService
from geek_cafe_saas_sdk.domains.files.services.s3_file_service import S3FileService
from geek_cafe_saas_sdk.domains.files.models.file import File
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError
import datetime as dt


class FileLineageService:
    """Service for managing file lineage and transformations."""
    
    def __init__(self, file_service: FileSystemService, s3_service: S3FileService):
        """
        Initialize lineage service.
        
        Args:
            file_service: FileSystemService instance
            s3_service: S3FileService instance
        """
        self.file_service = file_service
        self.s3_service = s3_service
    
    def create_main_file(
        self,
        tenant_id: str,
        user_id: str,
        original_file_id: str,
        file_name: str,
        file_data: bytes,
        mime_type: str,
        transformation_operation: str,
        transformation_metadata: Optional[Dict[str, Any]] = None,
        directory_id: Optional[str] = None
    ) -> ServiceResult[File]:
        """
        Create a main file from an original file.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            original_file_id: Original file ID
            file_name: New file name (e.g., "data.csv")
            file_data: Converted file data
            mime_type: MIME type
            transformation_operation: Operation name (e.g., "xls_to_csv")
            transformation_metadata: Additional metadata
            directory_id: Optional directory ID (inherits from original if not provided)
        
        Returns:
            ServiceResult with main File
        """
        try:
            # Get original file
            original_result = self.file_service.get_by_id(
                resource_id=original_file_id,
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            if not original_result.success:
                return original_result
            
            original_file = original_result.data
            
            # Validate original is actually an original
            if original_file.file_role != "original":
                return ServiceResult.error_result(
                    message="Source file must have role 'original'",
                    error_code="INVALID_FILE_ROLE"
                )
            
            # Use original's directory if not specified
            target_directory_id = directory_id if directory_id is not None else original_file.directory_id
            
            # Create main file
            result = self.file_service.create(
                tenant_id=tenant_id,
                user_id=user_id,
                file_name=file_name,
                file_data=file_data,
                mime_type=mime_type,
                directory_id=target_directory_id,
                file_role="main",
                parent_file_id=original_file_id,
                original_file_id=original_file_id,
                transformation_type="convert",
                transformation_operation=transformation_operation,
                transformation_metadata=transformation_metadata or {}
            )
            
            if result.success:
                # Update original file's derived count
                self.file_service.update(
                    resource_id=original_file_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    updates={'derived_file_count': 1}
                )
            
            return result
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to create main file: {str(e)}",
                error_code="CREATE_MAIN_FILE_FAILED",
                error=e
            )
    
    def create_derived_file(
        self,
        tenant_id: str,
        user_id: str,
        main_file_id: str,
        file_name: str,
        file_data: bytes,
        transformation_operation: str,
        transformation_metadata: Optional[Dict[str, Any]] = None,
        directory_id: Optional[str] = None
    ) -> ServiceResult[File]:
        """
        Create a derived file from a main file.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            main_file_id: Main file ID (parent)
            file_name: New file name (e.g., "data_clean_v1.csv")
            file_data: Processed file data
            transformation_operation: Operation name (e.g., "data_cleaning_v1")
            transformation_metadata: Additional metadata
            directory_id: Optional directory ID (inherits from main if not provided)
        
        Returns:
            ServiceResult with derived File
        """
        try:
            # Get main file
            main_result = self.file_service.get_by_id(
                resource_id=main_file_id,
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            if not main_result.success:
                return main_result
            
            main_file = main_result.data
            
            # Validate main is actually a main file
            if main_file.file_role != "main":
                return ServiceResult.error_result(
                    message="Source file must have role 'main'",
                    error_code="INVALID_FILE_ROLE"
                )
            
            # Use main's directory if not specified
            target_directory_id = directory_id if directory_id is not None else main_file.directory_id
            
            # Create derived file
            result = self.file_service.create(
                tenant_id=tenant_id,
                user_id=user_id,
                file_name=file_name,
                file_data=file_data,
                mime_type=main_file.mime_type,
                directory_id=target_directory_id,
                file_role="derived",
                parent_file_id=main_file_id,
                original_file_id=main_file.original_file_id,
                transformation_type="clean",
                transformation_operation=transformation_operation,
                transformation_metadata=transformation_metadata or {}
            )
            
            if result.success:
                # Atomically increment main file's derived count
                # Re-fetch to get current count and avoid race conditions
                fresh_main = self.file_service.get_by_id(
                    resource_id=main_file_id,
                    tenant_id=tenant_id,
                    user_id=user_id
                )
                
                if fresh_main.success:
                    new_count = fresh_main.data.derived_file_count + 1
                    self.file_service.update(
                        resource_id=main_file_id,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        updates={'derived_file_count': new_count}
                    )
            
            return result
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to create derived file: {str(e)}",
                error_code="CREATE_DERIVED_FILE_FAILED",
                error=e
            )
    
    def get_lineage(
        self,
        file_id: str,
        tenant_id: str,
        user_id: str
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Get complete lineage for a file.
        
        Returns:
            ServiceResult with lineage dict containing:
            - selected: The selected file
            - main: Main file (if exists)
            - original: Original file (if exists)
            - all_derived: List of all derived files (if viewing main)
        """
        try:
            # Get selected file
            selected_result = self.file_service.get_by_id(
                resource_id=file_id,
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            if not selected_result.success:
                return selected_result
            
            selected_file = selected_result.data
            
            lineage = {
                'selected': selected_file,
                'main': None,
                'original': None,
                'all_derived': []
            }
            
            # Get original file
            if selected_file.original_file_id:
                original_result = self.file_service.get_by_id(
                    resource_id=selected_file.original_file_id,
                    tenant_id=tenant_id,
                    user_id=user_id
                )
                if original_result.success:
                    lineage['original'] = original_result.data
            
            # Get main file
            if selected_file.is_derived() and selected_file.parent_file_id:
                main_result = self.file_service.get_by_id(
                    resource_id=selected_file.parent_file_id,
                    tenant_id=tenant_id,
                    user_id=user_id
                )
                if main_result.success:
                    lineage['main'] = main_result.data
            elif selected_file.is_main():
                lineage['main'] = selected_file
            
            # Get all derived files if viewing main
            if selected_file.is_main():
                derived = self.list_derived_files(
                    main_file_id=file_id,
                    tenant_id=tenant_id,
                    user_id=user_id
                )
                if derived.success:
                    lineage['all_derived'] = derived.data
            
            return ServiceResult.success_result(lineage)
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to get lineage: {str(e)}",
                error_code="GET_LINEAGE_FAILED",
                error=e
            )
    
    def list_derived_files(
        self,
        main_file_id: str,
        tenant_id: str,
        user_id: str,
        limit: int = 100
    ) -> ServiceResult[List[File]]:
        """
        List all files derived from a main file.
        
        Returns:
            ServiceResult with list of derived Files
        """
        try:
            # Get all user's files
            all_files_result = self.file_service.list_files_by_owner(
                tenant_id=tenant_id,
                owner_id=user_id,
                user_id=user_id,
                limit=limit
            )
            
            if not all_files_result.success:
                return all_files_result
            
            # Filter to derived files from this main file
            derived_files = [
                f for f in all_files_result.data
                if f.parent_file_id == main_file_id and f.is_derived()
            ]
            
            # Sort by creation date
            derived_files.sort(key=lambda f: f.created_utc_ts)
            
            return ServiceResult.success_result(derived_files)
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to list derived files: {str(e)}",
                error_code="LIST_DERIVED_FAILED",
                error=e
            )
    
    def prepare_lineage_bundle(
        self,
        selected_file_id: str,
        tenant_id: str,
        user_id: str
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Prepare bundle of files for lineage.
        
        Returns:
            ServiceResult with bundle dict containing:
            - selected_file: Selected file
            - main_file: Main file
            - original_file: Original file
            - metadata: Transformation chain info
        """
        try:
            lineage_result = self.get_lineage(
                file_id=selected_file_id,
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            if not lineage_result.success:
                return lineage_result
            
            lineage = lineage_result.data
            
            bundle = {
                'selected_file': lineage['selected'],
                'main_file': lineage['main'],
                'original_file': lineage['original'],
                'metadata': {
                    'selected_file_id': selected_file_id,
                    'selected_file_name': lineage['selected'].file_name,
                    'transformation_chain': []
                }
            }
            
            # Build transformation chain
            if lineage['original']:
                bundle['metadata']['transformation_chain'].append({
                    'step': 1,
                    'type': 'original',
                    'file_id': lineage['original'].file_id,
                    'file_name': lineage['original'].file_name
                })
            
            if lineage['main']:
                bundle['metadata']['transformation_chain'].append({
                    'step': 2,
                    'type': 'convert',
                    'file_id': lineage['main'].file_id,
                    'file_name': lineage['main'].file_name,
                    'operation': lineage['main'].transformation_operation
                })
            
            if lineage['selected'].is_derived():
                bundle['metadata']['transformation_chain'].append({
                    'step': 3,
                    'type': 'clean',
                    'file_id': lineage['selected'].file_id,
                    'file_name': lineage['selected'].file_name,
                    'operation': lineage['selected'].transformation_operation
                })
            
            return ServiceResult.success_result(bundle)
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to prepare bundle: {str(e)}",
                error_code="PREPARE_BUNDLE_FAILED",
                error=e
            )
    
    def download_lineage_bundle(
        self,
        selected_file_id: str,
        tenant_id: str,
        user_id: str
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Download all files in lineage chain.
        
        Returns:
            ServiceResult with dict containing:
            - selected: {'file': File, 'data': bytes}
            - main: {'file': File, 'data': bytes}
            - original: {'file': File, 'data': bytes}
            - metadata: Transformation chain info
        """
        try:
            bundle_result = self.prepare_lineage_bundle(
                selected_file_id=selected_file_id,
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            if not bundle_result.success:
                return bundle_result
            
            bundle = bundle_result.data
            download_bundle = {
                'selected': None,
                'main': None,
                'original': None,
                'metadata': bundle['metadata']
            }
            
            # Download selected file
            selected_download = self.file_service.download_file(
                tenant_id=tenant_id,
                file_id=selected_file_id,
                user_id=user_id
            )
            if selected_download.success:
                download_bundle['selected'] = {
                    'file': selected_download.data['file'],
                    'data': selected_download.data['data']
                }
            
            # Download main file
            if bundle['main_file']:
                main_download = self.file_service.download_file(
                    tenant_id=tenant_id,
                    file_id=bundle['main_file'].file_id,
                    user_id=user_id
                )
                if main_download.success:
                    download_bundle['main'] = {
                        'file': main_download.data['file'],
                        'data': main_download.data['data']
                    }
            
            # Download original file
            if bundle['original_file']:
                original_download = self.file_service.download_file(
                    tenant_id=tenant_id,
                    file_id=bundle['original_file'].file_id,
                    user_id=user_id
                )
                if original_download.success:
                    download_bundle['original'] = {
                        'file': original_download.data['file'],
                        'data': original_download.data['data']
                    }
            
            return ServiceResult.success_result(download_bundle)
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to download bundle: {str(e)}",
                error_code="DOWNLOAD_BUNDLE_FAILED",
                error=e
            )
