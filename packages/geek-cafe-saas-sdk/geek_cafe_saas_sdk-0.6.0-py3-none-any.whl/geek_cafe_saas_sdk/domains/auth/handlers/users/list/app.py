# src/geek_cafe_saas_sdk/lambda_handlers/users/list/app.py

from typing import Dict, Any

from geek_cafe_saas_sdk.services import UserService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

user_service_pool = ServicePool(UserService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for listing users with optional filters.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional UserService for testing
    """
    try:
        user_service = injected_service if injected_service else user_service_pool.get()
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        query_params = event.get('queryStringParameters', {}) or {}

        # UserService has list_by_tenant method
        result = user_service.list_by_tenant(
            tenant_id=tenant_id,
            user_id=user_id
        )

        return service_result_to_response(result)

    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
