"""
Lambda handler for creating chat channels.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.messaging.services import ChatChannelService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatChannelService,
    require_body=True,
    convert_case=True
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a new chat channel.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatChannelService for testing
    
    Expected body (camelCase from frontend):
    {
        "name": "general",
        "description": "General discussion",
        "channelType": "public" | "private" | "direct",
        "ownerId": "user_456",  # Optional: For admins creating channels for others
        "members": ["user_123", "user_456"],
        "topic": "Channel topic",
        "isDefault": false,
        "isAnnouncement": false
    }
    
    Note: 
    - ownerId: Who the channel belongs to (defaults to authenticated user)
    - createdBy: Always set to authenticated user (audit trail)
    
    Returns 201 with created chat channel
    """
    return handler_wrapper.execute(event, context, create_chat_channel, injected_service)


def create_chat_channel(
    event: Dict[str, Any],
    service: ChatChannelService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for creating chat channels.
    
    Owner is automatically added as a member.
    Supports admin scenario (Rule #1):
    - ownerId in payload: who the channel belongs to
    - createdById: authenticated admin (for audit trail - Rule #2)
    
    Owner validation (Rule #3):
    - Missing ownerId: defaults to authenticated user (self-service)
    - Present ownerId: uses specified owner (admin-on-behalf)
    - Empty ownerId: ERROR (fail fast)
    """
    payload = event["parsed_body"]
    
    authenticated_user_id = user_context.get("user_id")
    tenant_id = user_context.get("tenant_id")
    
    # Validate and resolve owner (Rule #3)
    # Will raise ValidationError if explicitly empty
    owner_user_id = service._validate_owner_field(payload, authenticated_user_id, "owner_id")
    
    # Set audit trail to authenticated user (Rule #2)
    payload["created_by_id"] = authenticated_user_id
    
    # Create the chat channel with owner
    result = service.create(
        tenant_id=tenant_id,
        user_id=owner_user_id,  # Resource owner
        payload=payload
    )
    
    return result
