"""
Lambda handler for getting file lineage.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.files.services import FileLineageService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileLineageService,
    require_body=False,
    convert_case=True
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get complete lineage for a file.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileLineageService for testing
    
    Path parameters:
        fileId: File ID
    
    Returns 200 with lineage information:
    {
        "selected": {file object},
        "main": {file object or null},
        "original": {file object or null},
        "allDerived": [{file objects}]  # If viewing main file
    }
    """
    return handler_wrapper.execute(event, context, get_file_lineage, injected_service)


def get_file_lineage(
    event: Dict[str, Any],
    service: FileLineageService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for getting file lineage.
    """
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Get file ID from path parameters
    path_params = event.get("pathParameters", {})
    file_id = path_params.get("fileId") or path_params.get("id")
    
    if not file_id:
        raise ValueError("fileId path parameter is required")
    
    # Get lineage
    result = service.get_lineage(
        file_id=file_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    return result
