"""
Lambda handler for getting a chat message by ID.

Requires authentication and channel access.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.messaging.services import ChatMessageService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatMessageService,
    require_body=False
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get a chat message by ID.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatMessageService for testing
    
    Path parameters:
        id: Chat message ID
    
    Returns 200 with chat message details
    """
    return handler_wrapper.execute(event, context, get_chat_message, injected_service)


def get_chat_message(
    event: Dict[str, Any],
    service: ChatMessageService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for getting a chat message.
    
    Verifies user has access to the channel before returning message.
    """
    # Extract path parameter
    path_params = event.get("pathParameters") or {}
    message_id = path_params.get("id")
    
    if not message_id:
        from geek_cafe_saas_sdk.core.service_result import ServiceResult
        from geek_cafe_saas_sdk.core.service_errors import ValidationError
        return ServiceResult.exception_result(
            ValidationError("Message ID is required in path")
        )
    
    user_id = user_context.get("user_id")
    tenant_id = user_context.get("tenant_id")
    
    # Get the chat message with access control
    return service.get_by_id(
        resource_id=message_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
