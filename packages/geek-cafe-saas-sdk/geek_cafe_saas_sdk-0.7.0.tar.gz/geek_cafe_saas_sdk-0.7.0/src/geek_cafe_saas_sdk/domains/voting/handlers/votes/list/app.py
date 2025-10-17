# src/geek_cafe_saas_sdk/lambda_handlers/votes/list/app.py

from typing import Dict, Any

from geek_cafe_saas_sdk.services import VoteService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

vote_service_pool = ServicePool(VoteService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for listing votes with optional filters.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional VoteService for testing
    """
    try:
        vote_service = injected_service if injected_service else vote_service_pool.get()
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        query_params = event.get('queryStringParameters', {}) or {}

        # Check for target_id in query params
        target_id = query_params.get('target_id')
        if target_id:
            result = vote_service.list_by_target(target_id=target_id)
        else:
            # Default to listing by user
            result = vote_service.list_by_user(user_id=user_id)

        return service_result_to_response(result)

    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
