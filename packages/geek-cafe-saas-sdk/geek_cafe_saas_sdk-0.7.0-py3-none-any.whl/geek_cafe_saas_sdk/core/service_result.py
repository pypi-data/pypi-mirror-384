"""Base service classes for collaborative property operations."""


import traceback
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime

from aws_lambda_powertools import Logger

logger = Logger()


T = TypeVar('T')


class ServiceResult(Generic[T]):
    """Standard service operation result with enhanced error handling."""
    
    def __init__(self, success: bool, data: Optional[T] = None, 
                 message: Optional[str] = None, error_code: Optional[str] = None,
                 error_details: Optional[Dict[str, Any]] = None,
                 stack_trace: Optional[str] = None):
        self.success = success
        self.data = data
        self.message = message
        self.error_code = error_code
        self.error_details = error_details or {}
        self.stack_trace = stack_trace
        self.timestamp = datetime.now()
    
    @classmethod
    def success_result(cls, data: T) -> 'ServiceResult[T]':
        """Create a successful result."""
        return cls(success=True, data=data)
    
    @classmethod
    def error_result(cls, message: str, error_code: Optional[str] = None, 
                    error_details: Optional[Dict[str, Any]] = None) -> 'ServiceResult[T]':
        """Create an error result with basic error information."""
        return cls(success=False, message=message, error_code=error_code, error_details=error_details)
    
    @classmethod
    def exception_result(cls, exception: Exception, error_code: Optional[str] = None,
                        context: Optional[str] = None) -> 'ServiceResult[T]':
        """Create an error result from an exception with full stack trace logging."""
        
        # Get the full stack trace
        stack_trace = traceback.format_exc()
        
        # Create detailed error message
        error_message = f"{type(exception).__name__}: {str(exception)}"
        if context:
            error_message = f"{context} - {error_message}"
        
        # Prepare error details
        error_details = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log the full error with stack trace to CloudWatch
        logger.error(
            f"Service operation failed: {error_message}\n"
            f"Context: {context or 'None'}\n"
            f"Exception Type: {type(exception).__name__}\n"
            f"Exception Message: {str(exception)}\n"
            f"Stack Trace:\n{stack_trace}",
            extra={
                'error_code': error_code,
                'exception_type': type(exception).__name__,
                'context': context,
                'stack_trace': stack_trace
            }
        )
        
        # Also print to console for immediate visibility
        print(f"\n🚨 SERVICE ERROR: {error_message}")
        print(f"📍 Context: {context or 'None'}")
        print(f"🔍 Exception Type: {type(exception).__name__}")
        print(f"📝 Stack Trace:")
        print(stack_trace)
        print("" + "="*80 + "")
        
        return cls(
            success=False, 
            message=error_message, 
            error_code=error_code or 'INTERNAL_ERROR',
            error_details=error_details,
            stack_trace=stack_trace
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for API responses."""
        result = {
            'success': self.success,
            'timestamp': self.timestamp.isoformat()
        }
        
        if self.success:
            result['data'] = self.data
        else:
            result['error'] = {
                'message': self.message,
                'code': self.error_code,
                'details': self.error_details
            }
            # Only include stack trace in development/debug mode
            # You might want to add a flag to control this
            if self.stack_trace:
                result['error']['stack_trace'] = self.stack_trace
        
        return result







