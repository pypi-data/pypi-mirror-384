# src/geek_cafe_saas_sdk/lambda_handlers/events/check_in/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.domains.events.services.event_attendee_service import EventAttendeeService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

attendee_service_pool = ServicePool(EventAttendeeService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for checking in attendees.
    
    Allows hosts/organizers to check in attendees at the event.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional EventAttendeeService for testing
        
    Expected body:
    {
        "event_id": "evt_123",
        "attendee_user_id": "user_456"  // User to check in
    }
    
    Returns 200 with updated attendee record (check_in = true)
    """
    try:
        attendee_service = injected_service if injected_service else attendee_service_pool.get()
        body = LambdaEventUtility.get_body_from_event(event)
        user_id = LambdaEventUtility.get_authenticated_user_id(event)  # Who is checking them in
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)

        # Validate required fields
        event_id = body.get('event_id')
        attendee_user_id = body.get('attendee_user_id')

        if not event_id:
            return error_response("event_id is required", "VALIDATION_ERROR", 400)
        if not attendee_user_id:
            return error_response("attendee_user_id is required", "VALIDATION_ERROR", 400)

        # Check in the attendee
        result = attendee_service.check_in(
            event_id=event_id,
            user_id=attendee_user_id,
            tenant_id=tenant_id,
            checked_in_by_user_id=user_id
        )

        return service_result_to_response(result)

    except json.JSONDecodeError:
        return error_response("Invalid JSON format in request body.", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
