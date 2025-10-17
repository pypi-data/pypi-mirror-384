"""
Lambda handler for creating a main file from an original file.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.files.services import FileLineageService
import base64


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileLineageService,
    require_body=True,
    convert_case=True
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a main file from an original file (e.g., XLS → CSV conversion).
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileLineageService for testing
    
    Expected body (camelCase from frontend):
    {
        "originalFileId": "file-123",  # Original file ID
        "fileName": "data.csv",
        "fileData": "base64_encoded_content",
        "mimeType": "text/csv",
        "transformationOperation": "xls_to_csv",
        "transformationMetadata": {
            "source_format": "xls",
            "target_format": "csv",
            "converter_version": "1.0"
        },
        "directoryId": "dir-456"  # Optional
    }
    
    Returns 201 with created main file
    """
    return handler_wrapper.execute(event, context, create_main_file, injected_service)


def create_main_file(
    event: Dict[str, Any],
    service: FileLineageService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for creating main file.
    """
    payload = event["parsed_body"]
    
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Extract required fields
    original_file_id = payload.get("original_file_id")
    file_name = payload.get("file_name")
    file_data_b64 = payload.get("file_data")
    mime_type = payload.get("mime_type")
    transformation_operation = payload.get("transformation_operation")
    
    if not original_file_id:
        raise ValueError("original_file_id is required")
    if not file_name:
        raise ValueError("file_name is required")
    if not file_data_b64:
        raise ValueError("file_data is required")
    if not mime_type:
        raise ValueError("mime_type is required")
    if not transformation_operation:
        raise ValueError("transformation_operation is required")
    
    # Decode base64 file data
    try:
        file_data = base64.b64decode(file_data_b64)
    except Exception as e:
        raise ValueError(f"Invalid base64 file_data: {str(e)}")
    
    # Extract optional fields
    transformation_metadata = payload.get("transformation_metadata", {})
    directory_id = payload.get("directory_id")
    
    # Create main file
    result = service.create_main_file(
        tenant_id=tenant_id,
        user_id=user_id,
        original_file_id=original_file_id,
        file_name=file_name,
        file_data=file_data,
        mime_type=mime_type,
        transformation_operation=transformation_operation,
        transformation_metadata=transformation_metadata,
        directory_id=directory_id
    )
    
    return result
