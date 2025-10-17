"""
Lambda handler for creating/uploading files.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.files.services import FileSystemService
import base64


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=True,
    convert_case=True
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Upload a new file.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Expected body (camelCase from frontend):
    {
        "fileName": "document.pdf",
        "fileData": "base64_encoded_content",
        "mimeType": "application/pdf",
        "directoryId": "dir-123",  # Optional
        "versioningStrategy": "explicit",  # Optional: "s3_native" or "explicit"
        "description": "Q1 Report",  # Optional
        "tags": ["report", "2024"],  # Optional
        
        # Optional lineage fields:
        "fileRole": "original",  # "standalone", "original", "main", "derived"
        "parentFileId": "file-parent",  # For lineage tracking
        "originalFileId": "file-original",  # For lineage tracking
        "transformationType": "convert",  # "convert", "clean", "process"
        "transformationOperation": "xls_to_csv",  # Operation name
        "transformationMetadata": {  # Operation details
            "source_format": "xls",
            "target_format": "csv"
        }
    }
    
    Returns 201 with created file metadata
    """
    return handler_wrapper.execute(event, context, upload_file, injected_service)


def upload_file(
    event: Dict[str, Any],
    service: FileSystemService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for uploading files.
    """
    payload = event["parsed_body"]
    
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Extract required fields
    file_name = payload.get("file_name")
    file_data_b64 = payload.get("file_data")
    mime_type = payload.get("mime_type")
    
    if not file_name:
        raise ValueError("file_name is required")
    if not file_data_b64:
        raise ValueError("file_data is required")
    if not mime_type:
        raise ValueError("mime_type is required")
    
    # Decode base64 file data
    try:
        file_data = base64.b64decode(file_data_b64)
    except Exception as e:
        raise ValueError(f"Invalid base64 file_data: {str(e)}")
    
    # Extract optional fields
    directory_id = payload.get("directory_id")
    versioning_strategy = payload.get("versioning_strategy", "explicit")
    description = payload.get("description")
    tags = payload.get("tags", [])
    
    # Extract lineage fields
    file_role = payload.get("file_role")
    parent_file_id = payload.get("parent_file_id")
    original_file_id = payload.get("original_file_id")
    transformation_type = payload.get("transformation_type")
    transformation_operation = payload.get("transformation_operation")
    transformation_metadata = payload.get("transformation_metadata")
    
    # Upload file
    result = service.create(
        tenant_id=tenant_id,
        user_id=user_id,
        file_name=file_name,
        file_data=file_data,
        mime_type=mime_type,
        directory_id=directory_id,
        versioning_strategy=versioning_strategy,
        description=description,
        tags=tags,
        file_role=file_role,
        parent_file_id=parent_file_id,
        original_file_id=original_file_id,
        transformation_type=transformation_type,
        transformation_operation=transformation_operation,
        transformation_metadata=transformation_metadata
    )
    
    return result
