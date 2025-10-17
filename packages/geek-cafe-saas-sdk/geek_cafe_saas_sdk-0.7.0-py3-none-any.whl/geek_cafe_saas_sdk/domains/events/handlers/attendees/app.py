# src/geek_cafe_saas_sdk/lambda_handlers/events/attendees/app.py

from typing import Dict, Any

from geek_cafe_saas_sdk.domains.events.services.event_attendee_service import EventAttendeeService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

attendee_service_pool = ServicePool(EventAttendeeService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for listing event attendees.
    
    Supports filtering by RSVP status and role.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional EventAttendeeService for testing
        
    Query Parameters:
        event_id: Event ID (required)
        rsvp_status: Filter by status (accepted, declined, tentative, invited, waitlist)
        role: Filter by role (organizer, co_host, attendee, speaker, volunteer)
        limit: Max results (default 100)
        
    Examples:
        /events/attendees?event_id=evt_123
        /events/attendees?event_id=evt_123&rsvp_status=accepted
        /events/attendees?event_id=evt_123&role=organizer
        /events/attendees?event_id=evt_123&rsvp_status=accepted&role=speaker
    
    Returns 200 with list of attendees
    """
    try:
        attendee_service = injected_service if injected_service else attendee_service_pool.get()
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        query_params = event.get('queryStringParameters', {}) or {}

        # Validate required param
        event_id = query_params.get('event_id')
        if not event_id:
            return error_response("event_id query parameter is required", "VALIDATION_ERROR", 400)

        # Extract optional filters
        rsvp_status = query_params.get('rsvp_status')
        role = query_params.get('role')
        limit = int(query_params.get('limit', 100))

        # Get attendees
        result = attendee_service.list_by_event(
            event_id=event_id,
            tenant_id=tenant_id,
            rsvp_status=rsvp_status,
            role=role,
            limit=limit
        )

        return service_result_to_response(result)

    except ValueError as e:
        return error_response(f"Invalid parameter value: {str(e)}", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
