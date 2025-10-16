# src/geek_cafe_saas_sdk/lambda_handlers/subscriptions/activate/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.services import SubscriptionService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

subscription_service_pool = ServicePool(SubscriptionService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for activating a subscription (upgrade/downgrade).
    
    This creates a new subscription and sets it as the tenant's active subscription.
    Updates the tenant's plan_tier automatically.
    
    Expected body:
    {
        "plan_code": "pro_monthly",
        "plan_name": "Pro Plan",
        "price_cents": 2999,
        "seat_count": 10,
        "current_period_start_utc_ts": 1729123200.0,
        "current_period_end_utc_ts": 1731801600.0
    }
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional SubscriptionService for testing
    """
    try:
        subscription_service = injected_service if injected_service else subscription_service_pool.get()
        body = LambdaEventUtility.get_body_from_event(event)
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        
        result = subscription_service.activate_subscription(
            tenant_id=tenant_id,
            user_id=user_id,
            payload=body
        )
        
        return service_result_to_response(result, success_status=201)
    
    except json.JSONDecodeError:
        return error_response("Invalid JSON in request body.", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
