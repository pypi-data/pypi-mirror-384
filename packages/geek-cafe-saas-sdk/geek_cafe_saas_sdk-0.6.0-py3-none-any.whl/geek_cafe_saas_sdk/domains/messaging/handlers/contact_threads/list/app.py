"""
Lambda handler for listing contact threads.

Supports multiple query patterns via query parameters:
- inbox + status (default): List threads in an inbox by status
- assigned: List threads assigned to current user
- sender_email: List all threads from a specific email
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
    List contact threads based on query parameters.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ContactThreadService for testing
    
    Query parameters:
        inbox_id: Inbox ID (support, sales, billing)
        status: Status filter (open, in_progress, resolved, closed)
        assigned: "me" to get threads assigned to current user
        sender_email: Email address to find all threads from sender
        limit: Maximum number of results (default 50)
    
    Examples:
        GET /contact-threads?inbox_id=support&status=open
        GET /contact-threads?assigned=me
        GET /contact-threads?sender_email=guest@example.com
    
    Returns 200 with list of contact threads
    """
    return handler_wrapper.execute(event, context, list_contact_threads, injected_service)


def list_contact_threads(
    event: Dict[str, Any],
    service: ContactThreadService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for listing contact threads.
    
    Routes to different service methods based on query parameters.
    """
    query_params = event.get("queryStringParameters") or {}
    
    user_id = user_context.get("user_id")
    tenant_id = user_context.get("tenant_id")
    limit = int(query_params.get("limit", "50"))
    
    # Route to appropriate service method
    
    # Pattern 1: List by assigned user
    if query_params.get("assigned") == "me":
        status = query_params.get("status")
        return service.list_by_assigned_user(
            assigned_to=user_id,
            tenant_id=tenant_id,
            status=status,
            limit=limit
        )
    
    # Pattern 2: List by sender email
    if "sender_email" in query_params:
        sender_email = query_params.get("sender_email")
        return service.list_by_sender_email(
            sender_email=sender_email,
            tenant_id=tenant_id,
            limit=limit
        )
    
    # Pattern 3: List by inbox and status (default)
    inbox_id = query_params.get("inbox_id", "support")
    status = query_params.get("status", "open")
    priority = query_params.get("priority")
    
    return service.list_by_inbox_and_status(
        inbox_id=inbox_id,
        status=status,
        tenant_id=tenant_id,
        priority=priority,
        limit=limit
    )
