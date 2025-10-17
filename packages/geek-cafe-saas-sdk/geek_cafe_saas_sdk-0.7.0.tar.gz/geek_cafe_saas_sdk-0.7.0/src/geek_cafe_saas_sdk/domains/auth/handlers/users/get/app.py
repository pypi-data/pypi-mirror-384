# src/geek_cafe_saas_sdk/lambda_handlers/users/get/app.py

from typing import Dict, Any

from geek_cafe_saas_sdk.services import UserService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

user_service_pool = ServicePool(UserService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for retrieving a single user by its ID.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional UserService for testing
    """
    try:
        user_service = injected_service if injected_service else user_service_pool.get()
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        resource_id = LambdaEventUtility.get_value_from_path_parameters(event, 'id')

        if not resource_id:
            return error_response("User ID is required in the path.", "VALIDATION_ERROR", 400)

        result = user_service.get_by_id(
            resource_id=resource_id,
            tenant_id=tenant_id,
            user_id=user_id
        )

        return service_result_to_response(result)

    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
