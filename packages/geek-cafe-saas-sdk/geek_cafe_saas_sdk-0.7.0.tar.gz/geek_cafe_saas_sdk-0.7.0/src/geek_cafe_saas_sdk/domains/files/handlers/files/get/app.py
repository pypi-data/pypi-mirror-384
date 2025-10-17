"""
Lambda handler for getting file metadata.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.files.services import FileSystemService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=False,
    convert_case=True
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get file metadata by ID.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Path parameters:
        fileId: File ID
    
    Returns 200 with file metadata
    """
    return handler_wrapper.execute(event, context, get_file, injected_service)


def get_file(
    event: Dict[str, Any],
    service: FileSystemService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for getting file metadata.
    """
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Get file ID from path parameters
    path_params = event.get("pathParameters", {})
    file_id = path_params.get("fileId") or path_params.get("id")
    
    if not file_id:
        raise ValueError("fileId path parameter is required")
    
    # Get file metadata
    result = service.get_by_id(
        resource_id=file_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    return result
