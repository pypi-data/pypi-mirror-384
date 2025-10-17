"""
Lambda handler for downloading complete lineage bundle with file content.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.domains.files.services import FileLineageService
import base64


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileLineageService,
    require_body=False,
    convert_case=True
)


def handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Download complete lineage bundle with file content.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileLineageService for testing
    
    Path parameters:
        fileId: File ID to bundle
    
    Returns 200 with bundle including file data (base64 encoded):
    {
        "selected": {
            "file": {file object},
            "data": "base64_encoded_content"
        },
        "main": {
            "file": {file object},
            "data": "base64_encoded_content"
        },
        "original": {
            "file": {file object},
            "data": "base64_encoded_content"
        },
        "metadata": {transformation chain}
    }
    """
    return handler_wrapper.execute(event, context, download_bundle, injected_service)


def download_bundle(
    event: Dict[str, Any],
    service: FileLineageService,
    user_context: Dict[str, str]
) -> Dict[str, Any]:
    """
    Business logic for downloading lineage bundle.
    """
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Get file ID from path parameters
    path_params = event.get("pathParameters", {})
    file_id = path_params.get("fileId") or path_params.get("id")
    
    if not file_id:
        raise ValueError("fileId path parameter is required")
    
    # Download bundle
    result = service.download_lineage_bundle(
        selected_file_id=file_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    if result.success:
        bundle = result.data
        
        # Encode file data as base64 for JSON response
        if bundle.get('selected') and bundle['selected'].get('data'):
            bundle['selected']['data'] = base64.b64encode(
                bundle['selected']['data']
            ).decode('utf-8')
        
        if bundle.get('main') and bundle['main'].get('data'):
            bundle['main']['data'] = base64.b64encode(
                bundle['main']['data']
            ).decode('utf-8')
        
        if bundle.get('original') and bundle['original'].get('data'):
            bundle['original']['data'] = base64.b64encode(
                bundle['original']['data']
            ).decode('utf-8')
        
        return bundle
    
    return result
