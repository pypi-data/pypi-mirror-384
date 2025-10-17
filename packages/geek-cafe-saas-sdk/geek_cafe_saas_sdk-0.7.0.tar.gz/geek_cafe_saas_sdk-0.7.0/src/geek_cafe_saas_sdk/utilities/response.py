"""
Utility functions for creating standardized Lambda responses.
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime, UTC
from boto3_assist.utilities.serialization_utility import JsonConversions
from typing import Union, List
from ..core.error_codes import ErrorCode


def json_snake_to_camel(
    payload: Union[List[Dict[str, Any]], Dict[str, Any], None],
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convert backend data from snake_case to camelCase for UI consumption.

    Args:
        payload: The backend data in snake_case format (dict or list of dicts)

    Returns:
        The payload converted to camelCase format, maintaining the same structure

    Raises:
        ValueError: If the payload is None
    """
    if payload is None:
        raise ValueError("Payload cannot be None")
    if not payload:
        return payload  # Return empty dict/list as-is

    return JsonConversions.json_snake_to_camel(payload)


def success_response(
    data: Any, status_code: int = 200, message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a successful API Gateway response with automatic camelCase conversion.

    Args:
        data: Response data to include in body (will be converted to camelCase)
        status_code: HTTP status code (default: 200)
        message: Optional success message

    Returns:
        API Gateway response dictionary
    """
    # Convert data to camelCase for UI consumption
    ui_data = json_snake_to_camel(data) if data is not None and data != {} else data

    body = {
        "data": ui_data,
        "timestamp": datetime.now(UTC).isoformat(),
        "status_code": status_code,
        "success": True,
    }

    
    if message:
        body["message"] = message 

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }


def error_response(
    error: str, error_code: str, status_code: int = 400
) -> Dict[str, Any]:
    """
    Create an error API Gateway response.

    Args:
        error: Error message
        error_code: Standardized error code
        status_code: HTTP status code (default: 400)

    Returns:
        API Gateway response dictionary
    """

    body = {
        "error": error,
        "error_code": error_code,
        "timestamp": datetime.now(UTC).isoformat(),
        "status_code": status_code,
        "success": False,
    }

    body = json_snake_to_camel(body)

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }


def validation_error_response(error: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Create a validation error response.

    Args:
        error: Validation error message
        status_code: HTTP status code (default: 400)

    Returns:
        API Gateway response dictionary
    """
    return error_response(error, "VALIDATION_ERROR", status_code)


def service_result_to_response(result, success_status: int = 200) -> Dict[str, Any]:
    """
    Convert a ServiceResult to an API Gateway response.

    Args:
        result: ServiceResult object from service layer
        success_status: HTTP status code for successful operations

    Returns:
        API Gateway response dictionary
    """
    if result.success:
        # Handle model serialization for different data types
        data = result.data
        if hasattr(data, 'to_dictionary'):
            # Single model object
            data = data.to_dictionary()
        elif isinstance(data, list) and data and hasattr(data[0], 'to_dictionary'):
            # List of model objects
            data = [item.to_dictionary() for item in data]
        
        return success_response(data, success_status)
    else:
        # Get HTTP status code from ErrorCode enum (or use default mapping)
        try:
            # Try to convert string error code to ErrorCode enum
            error_code_enum = ErrorCode(result.error_code) if result.error_code else None
            status_code = ErrorCode.get_http_status(error_code_enum) if error_code_enum else 400
        except ValueError:
            # Fallback for unknown error codes
            legacy_map = {
                "DUPLICATE_NAME": 409,
                "DUPLICATE_ITEM": 409,
                "GROUP_NOT_FOUND": 404,
            }
            status_code = legacy_map.get(result.error_code, 400)
        
        # Create structured error response with nested structure
        error_data = {
            "message": result.message,
            "code": result.error_code,
            "details": result.error_details
        }
        
        body = {
            "error": error_data,
            "timestamp": datetime.now(UTC).isoformat(),
            "status_code": status_code,
            "success": False,
        }

        body = json_snake_to_camel(body)

        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(body, default=str),
        }


def extract_path_parameters(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract path parameters from API Gateway event.

    Args:
        event: API Gateway event

    Returns:
        Dictionary of path parameters
    """
    return event.get("pathParameters") or {}


def extract_query_parameters(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract query string parameters from API Gateway event.

    Args:
        event: API Gateway event

    Returns:
        Dictionary of query parameters
    """
    return event.get("queryStringParameters") or {}
