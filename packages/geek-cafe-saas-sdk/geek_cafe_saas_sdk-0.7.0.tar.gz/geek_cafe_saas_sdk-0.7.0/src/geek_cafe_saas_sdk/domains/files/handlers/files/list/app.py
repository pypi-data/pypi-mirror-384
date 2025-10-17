"""
Lambda handler for listing files.

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
    List files.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Query parameters:
        directoryId: Filter by directory (optional)
        ownerId: Filter by owner (optional)
        limit: Max results (optional, default: 100)
    
    Returns 200 with list of files
    """
    return handler_wrapper.execute(event, context, list_files, injected_service)


def list_files(
    event: Dict[str, Any],
    service: FileSystemService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for listing files.
    """
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Get query parameters
    query_params = event.get("queryStringParameters", {}) or {}
    directory_id = query_params.get("directoryId")
    owner_id = query_params.get("ownerId") or user_id  # Default to current user
    limit = int(query_params.get("limit", "100"))
    
    # List files by directory or owner
    if directory_id:
        result = service.list_files_by_directory(
            tenant_id=tenant_id,
            directory_id=directory_id,
            user_id=user_id,
            limit=limit
        )
    else:
        result = service.list_files_by_owner(
            tenant_id=tenant_id,
            owner_id=owner_id,
            user_id=user_id,
            limit=limit
        )
    
    return result
