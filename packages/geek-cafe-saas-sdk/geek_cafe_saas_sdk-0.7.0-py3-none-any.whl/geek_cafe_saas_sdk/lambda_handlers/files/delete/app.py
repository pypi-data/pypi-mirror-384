"""
Lambda handler for deleting files.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.s3.s3_connection import S3Connection
from boto3_assist.s3.s3_object import S3Object
from boto3_assist.s3.s3_bucket import S3Bucket

from geek_cafe_saas_sdk.domains.files.services.file_system_service import FileSystemService
from geek_cafe_saas_sdk.domains.files.services.s3_file_service import S3FileService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Delete file handler.
    
    Expected Event:
    {
        "pathParameters": {
            "file_id": "file-123"
        },
        "queryStringParameters": {
            "tenant_id": "tenant-456",
            "user_id": "user-789",
            "hard_delete": "false"  # Optional, default false
        }
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "message": "File deleted successfully"
        }
    }
    """
    try:
        # Extract parameters
        path_params = event.get('pathParameters', {})
        query_params = event.get('queryStringParameters', {})
        
        file_id = path_params.get('file_id')
        tenant_id = query_params.get('tenant_id')
        user_id = query_params.get('user_id')
        hard_delete = query_params.get('hard_delete', 'false').lower() == 'true'
        
        # Validate required fields
        if not all([file_id, tenant_id, user_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'Missing required parameters: file_id, tenant_id, user_id'
                })
            }
        
        # Initialize services
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'files-table')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'files-bucket')
        
        db = DynamoDB()
        connection = S3Connection()
        
        s3_service = S3FileService(
            s3_object=S3Object(connection=connection),
            s3_bucket=S3Bucket(connection=connection),
            default_bucket=bucket_name
        )
        
        file_service = FileSystemService(
            dynamodb=db,
            table_name=table_name,
            s3_service=s3_service,
            default_bucket=bucket_name
        )
        
        # Delete file
        result = file_service.delete(
            resource_id=file_id,
            tenant_id=tenant_id,
            user_id=user_id,
            hard_delete=hard_delete
        )
        
        if result.success:
            delete_type = "permanently" if hard_delete else "soft"
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': f'File {delete_type} deleted successfully'
                })
            }
        else:
            status_code = 404 if result.error_code == 'NOT_FOUND' else 403
            return {
                'statusCode': status_code,
                'body': json.dumps({
                    'success': False,
                    'message': result.message,
                    'error_code': result.error_code
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': f'Internal server error: {str(e)}'
            })
        }
