"""
Lambda handler for file upload.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import base64
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
    Upload file handler.
    
    Expected Event:
    {
        "body": {
            "tenant_id": "tenant-123",
            "user_id": "user-456",
            "file_name": "document.pdf",
            "file_data": "base64_encoded_content",
            "mime_type": "application/pdf",
            "directory_id": "dir-789",  # Optional
            "versioning_strategy": "explicit",  # Optional
            "description": "Monthly report",  # Optional
            "tags": ["report", "monthly"]  # Optional
        }
    }
    
    Returns:
    {
        "statusCode": 201,
        "body": {
            "success": true,
            "data": {
                "file_id": "file-123",
                "file_name": "document.pdf",
                "s3_key": "tenant-123/files/...",
                "file_size": 12345
            }
        }
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract parameters
        tenant_id = body.get('tenant_id')
        user_id = body.get('user_id')
        file_name = body.get('file_name')
        file_data_b64 = body.get('file_data')
        mime_type = body.get('mime_type', 'application/octet-stream')
        directory_id = body.get('directory_id')
        versioning_strategy = body.get('versioning_strategy', 's3_native')
        description = body.get('description')
        tags = body.get('tags', [])
        
        # Validate required fields
        if not all([tenant_id, user_id, file_name, file_data_b64]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'Missing required fields: tenant_id, user_id, file_name, file_data'
                })
            }
        
        # Decode file data
        file_data = base64.b64decode(file_data_b64)
        
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
        
        # Upload file
        result = file_service.create(
            tenant_id=tenant_id,
            user_id=user_id,
            file_name=file_name,
            file_data=file_data,
            mime_type=mime_type,
            directory_id=directory_id,
            versioning_strategy=versioning_strategy,
            description=description,
            tags=tags
        )
        
        if result.success:
            file = result.data
            return {
                'statusCode': 201,
                'body': json.dumps({
                    'success': True,
                    'data': {
                        'file_id': file.file_id,
                        'file_name': file.file_name,
                        's3_key': file.s3_key,
                        'file_size': file.file_size,
                        'created_utc_ts': file.created_utc_ts
                    }
                })
            }
        else:
            return {
                'statusCode': 400,
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
