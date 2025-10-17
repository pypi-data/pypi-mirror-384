"""
Base Lambda handler with common functionality.

Provides a foundation for creating Lambda handlers with standardized
request/response handling, error management, and service injection.
"""

import json
from typing import Dict, Any, Callable, Optional, Type, TypeVar
from aws_lambda_powertools import Logger

from geek_cafe_saas_sdk.utilities.response import (
    error_response,
    service_result_to_response,
)
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility
from geek_cafe_saas_sdk.middleware.auth import extract_user_context
from .service_pool import ServicePool

logger = Logger()

T = TypeVar('T')  # Service type


class BaseLambdaHandler:
    """
    Base class for Lambda handlers with common functionality.
    
    Handles:
    - Request body parsing and case conversion
    - Service initialization and pooling
    - User context extraction
    - Response formatting
    - Event unwrapping (SQS, SNS, etc.)
    
    """
    
    def __init__(
        self,
        service_class: Optional[Type[T]] = None,
        service_kwargs: Optional[Dict[str, Any]] = None,
        require_body: bool = False,
        convert_case: bool = True,
        unwrap_message: bool = True,
        apply_cors: bool = True,
        apply_error_handling: bool = True,
        require_auth: bool = True,
    ):
        self.service_class = service_class
        self.service_kwargs = service_kwargs or {}
        self.require_body = require_body
        self.convert_case = convert_case
        self.unwrap_message = unwrap_message
        self.apply_cors = apply_cors
        self.apply_error_handling = apply_error_handling
        self.require_auth = require_auth

        # Initialize service pool if a class is provided
        self._service_pool = ServicePool(service_class, **self.service_kwargs) if service_class else None

    def _get_service(self, injected_service: Optional[T]) -> Optional[T]:
        """
        Get service instance (injected or from pool).
        """
        if injected_service:
            return injected_service
        
        if self._service_pool:
            return self._service_pool.get()
        
        # Fallback for direct instantiation if pooling is not used (rare)
        if self.service_class:
            return self.service_class(**self.service_kwargs)

        return None

    def execute(
        self,
        event: Dict[str, Any],
        context: Any,
        business_logic: Callable[[Dict[str, Any], Any, Dict[str, Any]], Any],
        injected_service: Optional[T] = None
    ) -> Dict[str, Any]:
        """
        Execute the Lambda handler with the given business logic.
        
        Args:
            event: Lambda event dictionary
            context: Lambda context object
            business_logic: Callable that implements the business logic
            injected_service: Optional service instance for testing
            
        Returns:
            Lambda response dictionary
        """
        try:
            # Unwrap message if needed (SQS, SNS, etc.)
            if self.unwrap_message and "message" in event:
                event = event["message"]
            
            # Validate requestContext presence (Rule #4)
            if "requestContext" not in event:
                return error_response(
                    "requestContext missing from event. Ensure API Gateway is properly configured.",
                    "CONFIGURATION_ERROR",
                    500
                )
            
            # Validate authentication if required
            if self.require_auth:
                authorizer = event.get("requestContext", {}).get("authorizer")
                if not authorizer or not authorizer.get("claims", {}).get("custom:user_id"):
                    return error_response(
                        "Authentication required but not provided",
                        "AUTHENTICATION_REQUIRED",
                        401
                    )
            
            # Check if body is required
            if self.require_body and not event.get("body"):
                return error_response(
                    "Request body is required",
                    "VALIDATION_ERROR",
                    400
                )
            
            # Parse and validate body
            if event.get("body"):
                try:
                    body = LambdaEventUtility.get_body_from_event(event, raise_on_error=self.require_body)
                    if body and self.convert_case:
                        body = LambdaEventUtility.to_snake_case_for_backend(body)
                    if body:
                        event["parsed_body"] = body
                except (ValueError, KeyError) as e:
                    # If error handling is disabled, let the exception propagate for testing
                    if not self.apply_error_handling:
                        raise
                    return error_response(
                        str(e),
                        "VALIDATION_ERROR",
                        400
                    )
            
            # Extract user context from authorizer claims
            user_context = extract_user_context(event)
            
            # Get service instance
            service = self._get_service(injected_service)
            
            # Execute business logic
            result = business_logic(event, service, user_context)
            
            # Determine appropriate HTTP status code based on HTTP method
            http_method = event.get('httpMethod', '').upper()
            if http_method == 'POST':
                success_status = 201  # Created
            elif http_method == 'DELETE':
                success_status = 204  # No Content
            else:
                success_status = 200  # OK (GET, PUT, PATCH, etc.)
            
            # Format response - handle both ServiceResult and plain dict
            if hasattr(result, 'success'):
                # It's a ServiceResult object
                response = service_result_to_response(result, success_status=success_status)
            else:
                # It's a plain dict - wrap it in a success response
                from geek_cafe_saas_sdk.utilities.response import success_response
                response = success_response(result, success_status)
            
            # Note: CORS headers are already added by success_response/service_result_to_response
            # The apply_cors flag is for decorator usage, not runtime response modification
            return response
            
        except Exception as e:
            logger.exception(f"Handler execution error: {e}")
            if self.apply_error_handling:
                # Convert exception to error response (error_response is imported at top)
                return error_response(
                    str(e),
                    "INTERNAL_ERROR",
                    500
                )
            raise
