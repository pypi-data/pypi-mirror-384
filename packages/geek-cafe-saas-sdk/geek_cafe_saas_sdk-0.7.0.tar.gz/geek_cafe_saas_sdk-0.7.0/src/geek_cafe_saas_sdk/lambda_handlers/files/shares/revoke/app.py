"""
Lambda handler for revoking file shares.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.domains.files.services.file_share_service import FileShareService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Revoke share handler."""
    try:
        path_params = event.get('pathParameters', {})
        query_params = event.get('queryStringParameters', {})
        
        share_id = path_params.get('share_id')
        tenant_id = query_params.get('tenant_id')
        user_id = query_params.get('user_id')
        file_id = query_params.get('file_id')
        
        if not all([share_id, tenant_id, user_id, file_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'Missing required parameters'
                })
            }
        
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'files-table')
        db = DynamoDB()
        
        share_service = FileShareService(
            dynamodb=db,
            table_name=table_name
        )
        
        result = share_service.delete(
            resource_id=share_id,
            tenant_id=tenant_id,
            user_id=user_id,
            file_id=file_id
        )
        
        if result.success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Share revoked successfully'
                })
            }
        else:
            status_code = 404 if result.error_code == 'NOT_FOUND' else 403
            return {
                'statusCode': status_code,
                'body': json.dumps({
                    'success': False,
                    'message': result.message
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': str(e)
            })
        }
