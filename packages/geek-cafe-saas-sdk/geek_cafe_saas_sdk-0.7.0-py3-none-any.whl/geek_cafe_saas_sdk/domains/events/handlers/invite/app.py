# src/geek_cafe_saas_sdk/lambda_handlers/events/invite/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.domains.events.services.event_attendee_service import EventAttendeeService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

attendee_service_pool = ServicePool(EventAttendeeService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for inviting user(s) to an event.
    
    Supports single and bulk invitations.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional EventAttendeeService for testing
        
    Expected body:
    {
        "event_id": "evt_123",
        "user_id": "user_456",  // For single invite
        "user_ids": ["user_1", "user_2"],  // For bulk invite
        "role": "attendee",  // or "co_host", "speaker", "volunteer"
        "registration_data": {"dietary": "vegetarian"},
        "registration_notes": "Looking forward to it!"
    }
    
    Returns 201 with invitation record(s)
    """
    try:
        attendee_service = injected_service if injected_service else attendee_service_pool.get()
        body = LambdaEventUtility.get_body_from_event(event)
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)

        # Validate required fields
        event_id = body.get('event_id')
        if not event_id:
            return error_response("event_id is required", "VALIDATION_ERROR", 400)

        # Check for bulk invite
        if 'user_ids' in body:
            # Bulk invite
            user_ids = body.get('user_ids', [])
            if not user_ids:
                return error_response("user_ids must be a non-empty list", "VALIDATION_ERROR", 400)

            # Extract optional params
            kwargs = {}
            if 'role' in body:
                kwargs['role'] = body['role']
            if 'registration_data' in body:
                kwargs['registration_data'] = body['registration_data']
            if 'registration_notes' in body:
                kwargs['registration_notes'] = body['registration_notes']

            result = attendee_service.bulk_invite(
                event_id=event_id,
                user_ids=user_ids,
                tenant_id=tenant_id,
                invited_by_user_id=user_id,
                **kwargs
            )
        else:
            # Single invite
            invitee_user_id = body.get('user_id')
            if not invitee_user_id:
                return error_response("user_id or user_ids is required", "VALIDATION_ERROR", 400)

            # Extract optional params
            kwargs = {}
            if 'role' in body:
                kwargs['role'] = body['role']
            if 'registration_data' in body:
                kwargs['registration_data'] = body['registration_data']
            if 'registration_notes' in body:
                kwargs['registration_notes'] = body['registration_notes']

            result = attendee_service.invite(
                event_id=event_id,
                user_id=invitee_user_id,
                tenant_id=tenant_id,
                invited_by_user_id=user_id,
                **kwargs
            )

        return service_result_to_response(result, success_status=201)

    except json.JSONDecodeError:
        return error_response("Invalid JSON format in request body.", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
