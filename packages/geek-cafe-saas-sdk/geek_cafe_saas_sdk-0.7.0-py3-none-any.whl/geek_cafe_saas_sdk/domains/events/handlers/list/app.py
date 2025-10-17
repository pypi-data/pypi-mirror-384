# src/geek_cafe_saas_sdk/lambda_handlers/events/list/app.py

from typing import Dict, Any

from geek_cafe_saas_sdk.domains.events.services.event_service import EventService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

event_service_pool = ServicePool(EventService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for listing events with location-based and other filters.
    
    Supports multiple query patterns:
    - By city: ?city=San Francisco&state=CA&country=US
    - By state: ?state=CA&country=US
    - Nearby: ?latitude=37.7749&longitude=-122.4194&radius=25
    - By owner: ?owner_id=user_123
    - By type: ?event_type=meetup&status=published
    - By group: ?group_id=group_123
    - Public discovery: ?visibility=public&status=published
    - All for tenant: (no params)
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional EventService for testing
        
    Query Parameters:
        city: City name
        state: State/Province/Region
        country: Country code
        latitude: Latitude for nearby search
        longitude: Longitude for nearby search
        radius: Radius in km (default 25)
        owner_id: Owner user ID
        event_type: Event type (meetup, conference, etc.)
        group_id: Group ID
        visibility: public, private, members_only
        status: draft, published, cancelled, completed
        limit: Max results (default 50)
    """
    try:
        event_service = injected_service if injected_service else event_service_pool.get()
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        query_params = event.get('queryStringParameters', {}) or {}

        # Extract common parameters
        limit = int(query_params.get('limit', 50))

        # Route to appropriate service method based on query params
        if 'latitude' in query_params and 'longitude' in query_params:
            # Nearby search (geo-location)
            result = event_service.list_nearby(
                latitude=float(query_params['latitude']),
                longitude=float(query_params['longitude']),
                radius_km=float(query_params.get('radius', 25)),
                tenant_id=tenant_id,
                limit=limit
            )
        elif 'city' in query_params:
            # City search
            result = event_service.list_by_city(
                city=query_params['city'],
                state=query_params.get('state'),
                country=query_params.get('country'),
                tenant_id=tenant_id,
                limit=limit
            )
        elif 'state' in query_params:
            # State/region search
            result = event_service.list_by_state(
                state=query_params['state'],
                country=query_params.get('country'),
                tenant_id=tenant_id,
                limit=limit
            )
        elif 'owner_id' in query_params:
            # Events by owner
            result = event_service.list_by_owner(
                owner_id=query_params['owner_id'],
                tenant_id=tenant_id,
                limit=limit
            )
        elif 'event_type' in query_params:
            # Events by type
            status = query_params.get('status', 'published')
            result = event_service.list_by_type(
                event_type=query_params['event_type'],
                tenant_id=tenant_id,
                status=status,
                limit=limit
            )
        elif 'group_id' in query_params:
            # Events by group
            result = event_service.list_by_group(
                group_id=query_params['group_id'],
                tenant_id=tenant_id,
                limit=limit
            )
        elif 'visibility' in query_params:
            # Public discovery
            status = query_params.get('status', 'published')
            result = event_service.list_public_events(
                tenant_id=tenant_id,
                visibility=query_params['visibility'],
                status=status,
                limit=limit
            )
        else:
            # All events for tenant
            result = event_service.list_by_tenant(
                tenant_id=tenant_id,
                limit=limit
            )

        return service_result_to_response(result)

    except ValueError as e:
        return error_response(f"Invalid parameter value: {str(e)}", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
