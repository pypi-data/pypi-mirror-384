# src/geek_cafe_saas_sdk/lambda_handlers/subscriptions/record_payment/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.services import SubscriptionService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

subscription_service_pool = ServicePool(SubscriptionService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for recording a payment on a subscription.
    
    This updates the subscription with payment details and can change status from past_due to active.
    
    Expected body:
    {
        "amount_cents": 2999
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
        resource_id = LambdaEventUtility.get_value_from_path_parameters(event, 'id')
        
        if not resource_id:
            return error_response("Subscription ID is required in the path.", "VALIDATION_ERROR", 400)
        
        # Get payment amount
        amount_cents = body.get('amount_cents')
        if amount_cents is None:
            return error_response("Payment amount_cents is required.", "VALIDATION_ERROR", 400)
        
        result = subscription_service.record_payment(
            subscription_id=resource_id,
            tenant_id=tenant_id,
            user_id=user_id,
            amount_cents=amount_cents
        )
        
        return service_result_to_response(result)
    
    except json.JSONDecodeError:
        return error_response("Invalid JSON in request body.", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
