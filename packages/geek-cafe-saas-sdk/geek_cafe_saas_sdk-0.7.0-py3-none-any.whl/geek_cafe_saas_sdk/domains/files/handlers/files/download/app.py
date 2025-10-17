"""
Lambda handler for downloading file content.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.files.services import FileSystemService
import base64


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=False,
    convert_case=True
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Download file content.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Path parameters:
        fileId: File ID
    
    Returns 200 with file content (base64 encoded for binary files)
    """
    return handler_wrapper.execute(event, context, download_file, injected_service)


def download_file(
    event: Dict[str, Any],
    service: FileSystemService,
    user_context: Dict[str, str]
) -> Dict[str, Any]:
    """
    Business logic for downloading file content.
    """
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Get file ID from path parameters
    path_params = event.get("pathParameters", {})
    file_id = path_params.get("fileId") or path_params.get("id")
    
    if not file_id:
        raise ValueError("fileId path parameter is required")
    
    # Download file
    result = service.download_file(
        tenant_id=tenant_id,
        file_id=file_id,
        user_id=user_id
    )
    
    if result.success:
        file_data = result.data['data']
        file_info = result.data['file']
        
        # Encode binary data as base64 for JSON response
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        
        # Return with metadata
        return {
            'file_id': file_info.file_id,
            'file_name': file_info.file_name,
            'mime_type': file_info.mime_type,
            'file_size': file_info.file_size,
            'file_data': encoded_data,
            'content_type': file_info.mime_type
        }
    
    return result
