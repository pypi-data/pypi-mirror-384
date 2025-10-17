"""
Lambda handler for listing files.

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
    """List files handler."""
    try:
        query_params = event.get('queryStringParameters', {})
        
        tenant_id = query_params.get('tenant_id')
        user_id = query_params.get('user_id')
        directory_id = query_params.get('directory_id')
        owner_id = query_params.get('owner_id')
        limit = int(query_params.get('limit', '100'))
        
        if not all([tenant_id, user_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'Missing required parameters'
                })
            }
        
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
        
        if directory_id:
            result = file_service.list_files_by_directory(
                tenant_id=tenant_id,
                directory_id=directory_id,
                user_id=user_id,
                limit=limit
            )
        elif owner_id:
            result = file_service.list_files_by_owner(
                tenant_id=tenant_id,
                owner_id=owner_id,
                user_id=user_id,
                limit=limit
            )
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'Must provide directory_id or owner_id'
                })
            }
        
        if result.success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'data': [f.to_dictionary() for f in result.data],
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
