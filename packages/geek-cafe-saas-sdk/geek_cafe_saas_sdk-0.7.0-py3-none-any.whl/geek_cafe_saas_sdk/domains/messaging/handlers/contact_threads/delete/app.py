"""
Lambda handler for deleting (soft delete) contact threads.

Requires authentication and appropriate access permissions.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.messaging.services import ContactThreadService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ContactThreadService,
    require_body=False
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Delete (soft delete) a contact thread.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ContactThreadService for testing
    
    Path parameters:
        id: Contact thread ID
    
    Returns 200 with success boolean
    """
    return handler_wrapper.execute(event, context, delete_contact_thread, injected_service)


def delete_contact_thread(
    event: Dict[str, Any],
    service: ContactThreadService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for deleting a contact thread.
    
    Performs soft delete (sets deleted timestamp).
    """
    # Extract path parameter
    path_params = event.get("pathParameters") or {}
    thread_id = path_params.get("id")
    
    if not thread_id:
        from geek_cafe_saas_sdk.core.service_result import ServiceResult
        from geek_cafe_saas_sdk.core.service_errors import ValidationError
        return ServiceResult.exception_result(
            ValidationError("Thread ID is required in path")
        )
    
    user_id = user_context.get("user_id")
    tenant_id = user_context.get("tenant_id")
    user_inboxes = user_context.get("inboxes", [])
    
    # Delete the contact thread
    return service.delete(
        resource_id=thread_id,
        tenant_id=tenant_id,
        user_id=user_id,
        user_inboxes=user_inboxes
    )
