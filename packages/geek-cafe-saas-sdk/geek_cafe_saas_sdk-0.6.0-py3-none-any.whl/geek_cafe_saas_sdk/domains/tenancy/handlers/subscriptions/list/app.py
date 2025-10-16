# src/geek_cafe_saas_sdk/lambda_handlers/subscriptions/list/app.py

from typing import Dict, Any

from geek_cafe_saas_sdk.services import SubscriptionService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

subscription_service_pool = ServicePool(SubscriptionService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for listing subscription history for a tenant.
    
    Returns all subscriptions (current and past) sorted by date descending.
    
    Query parameters:
    - limit: Maximum number of results (default: 50)
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional SubscriptionService for testing
    """
    try:
        subscription_service = injected_service if injected_service else subscription_service_pool.get()
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        query_params = event.get('queryStringParameters', {}) or {}
        
        # Get limit from query params (default 50)
        limit = int(query_params.get('limit', 50))
        
        result = subscription_service.list_subscription_history(
            tenant_id=tenant_id,
            user_id=user_id,
            limit=limit
        )
        
        return service_result_to_response(result)
    
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
