# src/geek_cafe_saas_sdk/lambda_handlers/events/cancel/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.domains.events.services.event_service import EventService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

event_service_pool = ServicePool(EventService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for cancelling an event.
    
    Changes status to 'cancelled' with optional reason.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional EventService for testing
        
    Path Parameters:
        id: Event ID
        
    Expected body (optional):
    {
        "cancellation_reason": "Weather concerns"
    }
        
    Example:
        POST /events/{id}/cancel
    
    Returns 200 with cancelled event
    """
    try:
        event_service = injected_service if injected_service else event_service_pool.get()
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        resource_id = LambdaEventUtility.get_value_from_path_parameters(event, 'id')

        if not resource_id:
            return error_response("Event ID is required in the path.", "VALIDATION_ERROR", 400)

        # Get optional cancellation reason
        cancellation_reason = None
        try:
            body = LambdaEventUtility.get_body_from_event(event)
            cancellation_reason = body.get('cancellation_reason')
        except:
            pass  # Body is optional

        result = event_service.cancel(
            resource_id=resource_id,
            tenant_id=tenant_id,
            user_id=user_id,
            cancellation_reason=cancellation_reason
        )

        return service_result_to_response(result)

    except json.JSONDecodeError:
        return error_response("Invalid JSON format in request body.", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
