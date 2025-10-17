"""
Lambda handler for sharing files.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.domains.files.services.file_share_service import FileShareService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Share file handler."""
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        tenant_id = body.get('tenant_id')
        user_id = body.get('user_id')
        file_id = body.get('file_id')
        shared_with_user_id = body.get('shared_with_user_id')
        permission = body.get('permission', 'view')
        expires_at = body.get('expires_at')
        message = body.get('message')
        
        if not all([tenant_id, user_id, file_id, shared_with_user_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'Missing required fields'
                })
            }
        
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'files-table')
        db = DynamoDB()
        
        share_service = FileShareService(
            dynamodb=db,
            table_name=table_name
        )
        
        result = share_service.create(
            tenant_id=tenant_id,
            user_id=user_id,
            file_id=file_id,
            shared_with_user_id=shared_with_user_id,
            permission=permission,
            expires_at=expires_at,
            message=message
        )
        
        if result.success:
            return {
                'statusCode': 201,
                'body': json.dumps({
                    'success': True,
                    'data': result.data.to_dictionary()
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
