# src/geek_cafe_saas_sdk/lambda_handlers/events/rsvp/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.domains.events.services.event_attendee_service import EventAttendeeService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

attendee_service_pool = ServicePool(EventAttendeeService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for updating RSVP status.
    
    Allows users to accept, decline, or mark as tentative.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional EventAttendeeService for testing
        
    Expected body:
    {
        "event_id": "evt_123",
        "rsvp_status": "accepted",  // accepted, declined, tentative
        "plus_one_count": 1,  // Optional
        "plus_one_names": ["Jane Doe"],  // Optional
        "registration_data": {"dietary": "vegetarian", "experience": "beginner"},  // Optional
        "registration_notes": "Excited to attend!"  // Optional
    }
    
    Returns 200 with updated attendee record
    """
    try:
        attendee_service = injected_service if injected_service else attendee_service_pool.get()
        body = LambdaEventUtility.get_body_from_event(event)
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)

        # Validate required fields
        event_id = body.get('event_id')
        rsvp_status = body.get('rsvp_status')

        if not event_id:
            return error_response("event_id is required", "VALIDATION_ERROR", 400)
        if not rsvp_status:
            return error_response("rsvp_status is required", "VALIDATION_ERROR", 400)
        if rsvp_status not in ['accepted', 'declined', 'tentative']:
            return error_response(
                "rsvp_status must be one of: accepted, declined, tentative",
                "VALIDATION_ERROR",
                400
            )

        # Extract optional params
        kwargs = {}
        if 'plus_one_count' in body:
            kwargs['plus_one_count'] = int(body['plus_one_count'])
        if 'plus_one_names' in body:
            kwargs['plus_one_names'] = body['plus_one_names']
        if 'registration_data' in body:
            kwargs['registration_data'] = body['registration_data']
        if 'registration_notes' in body:
            kwargs['registration_notes'] = body['registration_notes']

        result = attendee_service.update_rsvp(
            event_id=event_id,
            user_id=user_id,
            tenant_id=tenant_id,
            rsvp_status=rsvp_status,
            **kwargs
        )

        return service_result_to_response(result)

    except json.JSONDecodeError:
        return error_response("Invalid JSON format in request body.", "VALIDATION_ERROR", 400)
    except ValueError as e:
        return error_response(f"Invalid parameter value: {str(e)}", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
