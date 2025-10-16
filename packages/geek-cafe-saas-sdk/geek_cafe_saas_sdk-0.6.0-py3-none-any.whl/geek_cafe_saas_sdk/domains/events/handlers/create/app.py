# src/geek_cafe_saas_sdk/lambda_handlers/events/create/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.domains.events.services.event_service import EventService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility
from geek_cafe_saas_sdk.domains.events.models.event import Event

event_service_pool = ServicePool(EventService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for creating a new event.
    
    Supports both timestamp-based and ISO8601 datetime formats.
    Automatically creates EventAttendee record for owner as organizer.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional EventService for testing (Moto)
        
    Expected body (all optional except title and start time):
    {
        "title": "Python Meetup",
        "start_utc_ts": 1731717600.0,  // OR use start_datetime
        "start_datetime": "2025-11-15T18:00:00-08:00",  // Auto-converts to timestamp
        "end_utc_ts": 1731728400.0,  // OR use end_datetime
        "end_datetime": "2025-11-15T21:00:00-08:00",
        "timezone": "America/Los_Angeles",
        "description": "Monthly Python meetup",
        "event_type": "meetup",
        "status": "draft",  // or "published"
        "visibility": "public",
        
        // Location
        "location_type": "physical",  // physical, virtual, hybrid
        "location_name": "Tech Hub SF",
        "location_address": "123 Main St",
        "location_city": "San Francisco",
        "location_state": "CA",
        "location_country": "US",
        "location_latitude": 37.7749,
        "location_longitude": -122.4194,
        "virtual_link": "https://zoom.us/...",
        
        // Capacity
        "max_attendees": 50,
        "allow_waitlist": true,
        "requires_approval": false,
        "allow_guest_plus_one": true,
        "registration_deadline_utc_ts": 1731600000.0,
        
        // Other
        "group_id": "group_123",
        "tags": ["python", "networking"],
        "custom_fields": {"dietary": "text", "experience": "select"}
    }
    """
    try:
        # Use injected service (testing) or pool (production)
        event_service = injected_service if injected_service else event_service_pool.get()
        body = LambdaEventUtility.get_body_from_event(event)
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)

        # Convert ISO8601 datetime strings to timestamps if provided
        if 'start_datetime' in body and 'start_utc_ts' not in body:
            body['start_utc_ts'] = Event.datetime_to_utc_ts(body['start_datetime'])
        if 'end_datetime' in body and 'end_utc_ts' not in body:
            body['end_utc_ts'] = Event.datetime_to_utc_ts(body['end_datetime'])
        if 'registration_deadline_datetime' in body and 'registration_deadline_utc_ts' not in body:
            body['registration_deadline_utc_ts'] = Event.datetime_to_utc_ts(body['registration_deadline_datetime'])

        # Pass all body parameters to the service
        # Service will auto-create EventAttendee for owner
        result = event_service.create(
            tenant_id=tenant_id,
            user_id=user_id,
            create_organizer_attendee=True,  # Auto-create attendee record
            **body
        )

        return service_result_to_response(result, success_status=201)

    except json.JSONDecodeError:
        return error_response("Invalid JSON format in request body.", "VALIDATION_ERROR", 400)
    except Exception as e:
        # In a production environment, log the exception e
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
