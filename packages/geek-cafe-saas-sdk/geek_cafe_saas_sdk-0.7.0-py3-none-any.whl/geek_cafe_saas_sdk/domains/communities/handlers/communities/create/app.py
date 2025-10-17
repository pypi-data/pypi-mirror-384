# src/geek_cafe_saas_sdk/lambda_handlers/communities/create/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.services import CommunityService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

community_service_pool = ServicePool(CommunityService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for creating a new community.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional CommunityService for testing
    """
    try:
        # Use injected service (testing) or pool (production)
        community_service = injected_service if injected_service else community_service_pool.get()
        body = LambdaEventUtility.get_body_from_event(event)
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)

        # Pass all body parameters to the service
        result = community_service.create(
            tenant_id=tenant_id,
            user_id=user_id,
            **body
        )

        return service_result_to_response(result, success_status=201)

    except json.JSONDecodeError:
        return error_response("Invalid JSON in request body.", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
