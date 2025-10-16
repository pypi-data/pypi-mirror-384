# src/geek_cafe_saas_sdk/lambda_handlers/communities/list/app.py

from typing import Dict, Any

from geek_cafe_saas_sdk.services import CommunityService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

community_service_pool = ServicePool(CommunityService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for listing communities.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional CommunityService for testing
    """
    try:
        community_service = injected_service if injected_service else community_service_pool.get()
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        query_params = event.get('queryStringParameters', {}) or {}

        # CommunityService has list_by_tenant method
        result = community_service.list_by_tenant(
            tenant_id=tenant_id,
            user_id=user_id
        )

        return service_result_to_response(result)

    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
