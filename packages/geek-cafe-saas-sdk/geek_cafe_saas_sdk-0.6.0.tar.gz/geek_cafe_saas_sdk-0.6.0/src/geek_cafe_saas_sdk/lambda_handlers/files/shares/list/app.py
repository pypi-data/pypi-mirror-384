"""
Lambda handler for listing file shares.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.domains.files.services.file_share_service import FileShareService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """List shares handler."""
    try:
        query_params = event.get('queryStringParameters', {})
        
        tenant_id = query_params.get('tenant_id')
        user_id = query_params.get('user_id')
        file_id = query_params.get('file_id')
        limit = int(query_params.get('limit', '50'))
        
        if not all([tenant_id, user_id]):
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
        
        if file_id:
            # List shares for a specific file
            result = share_service.list_shares_by_file(
                tenant_id=tenant_id,
                file_id=file_id,
                user_id=user_id,
                limit=limit
            )
        else:
            # List shares with current user
            result = share_service.list_shares_with_user(
                tenant_id=tenant_id,
                user_id=user_id,
                limit=limit
            )
        
        if result.success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'data': [s.to_dictionary() for s in result.data],
                    'count': len(result.data)
                })
            }
        else:
            return {
                'statusCode': 400,
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
