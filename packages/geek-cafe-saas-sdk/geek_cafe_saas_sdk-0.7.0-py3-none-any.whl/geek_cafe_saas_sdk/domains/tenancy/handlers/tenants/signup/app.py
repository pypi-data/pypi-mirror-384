# src/geek_cafe_saas_sdk/lambda_handlers/tenants/signup/app.py

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.services import TenantService
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.response import service_result_to_response, error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility

tenant_service_pool = ServicePool(TenantService)

def handler(event: Dict[str, Any], context: object, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for tenant signup (creates tenant + primary admin user).
    
    This is the initial signup endpoint that creates both a tenant and its first admin user.
    
    Expected body:
    {
        "user": {
            "email": "admin@company.com",
            "first_name": "John",
            "last_name": "Doe"
        },
        "tenant": {
            "name": "Company Name"
        }
    }
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional TenantService for testing
    """
    try:
        tenant_service = injected_service if injected_service else tenant_service_pool.get()
        body = LambdaEventUtility.get_body_from_event(event)
        
        # Extract user and tenant payloads
        user_payload = body.get('user', {})
        tenant_payload = body.get('tenant', {})
        
        if not user_payload:
            return error_response("User information is required.", "VALIDATION_ERROR", 400)
        
        if not tenant_payload:
            return error_response("Tenant information is required.", "VALIDATION_ERROR", 400)
        
        # Create tenant with user (signup flow)
        result = tenant_service.create_with_user(
            user_payload=user_payload,
            tenant_payload=tenant_payload
        )
        
        return service_result_to_response(result, success_status=201)
    
    except json.JSONDecodeError:
        return error_response("Invalid JSON in request body.", "VALIDATION_ERROR", 400)
    except Exception as e:
        return error_response(f"An unexpected error occurred: {str(e)}", "INTERNAL_ERROR", 500)
