"""
Lambda handler for creating a derived file from a main file.

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
    Create a derived file from a main file (e.g., data cleaning).
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileLineageService for testing
    
    Expected body (camelCase from frontend):
    {
        "mainFileId": "file-456",  # Main file ID
        "fileName": "data_clean_v1.csv",
        "fileData": "base64_encoded_content",
        "transformationOperation": "data_cleaning_v1",
        "transformationMetadata": {
            "cleaning_version": 1,
            "operations": ["remove_nulls", "normalize_units"],
            "rows_processed": 1000
        },
        "directoryId": "dir-789"  # Optional
    }
    
    Returns 201 with created derived file
    """
    return handler_wrapper.execute(event, context, create_derived_file, injected_service)


def create_derived_file(
    event: Dict[str, Any],
    service: FileLineageService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for creating derived file.
    """
    payload = event["parsed_body"]
    
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Extract required fields
    main_file_id = payload.get("main_file_id")
    file_name = payload.get("file_name")
    file_data_b64 = payload.get("file_data")
    transformation_operation = payload.get("transformation_operation")
    
    if not main_file_id:
        raise ValueError("main_file_id is required")
    if not file_name:
        raise ValueError("file_name is required")
    if not file_data_b64:
        raise ValueError("file_data is required")
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
    
    # Create derived file
    result = service.create_derived_file(
        tenant_id=tenant_id,
        user_id=user_id,
        main_file_id=main_file_id,
        file_name=file_name,
        file_data=file_data,
        transformation_operation=transformation_operation,
        transformation_metadata=transformation_metadata,
        directory_id=directory_id
    )
    
    return result
