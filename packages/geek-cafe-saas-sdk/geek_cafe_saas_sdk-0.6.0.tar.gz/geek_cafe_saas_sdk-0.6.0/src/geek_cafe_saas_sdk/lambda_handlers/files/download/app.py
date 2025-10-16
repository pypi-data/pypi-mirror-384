"""
Lambda handler for file download.

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
    Download file handler.
    
    Expected Event:
    {
        "pathParameters": {
            "file_id": "file-123"
        },
        "queryStringParameters": {
            "tenant_id": "tenant-456",
            "user_id": "user-789",
            "presigned": "true"  # Optional, return presigned URL instead
        }
    }
    
    Returns (Direct Download):
    {
        "statusCode": 200,
        "isBase64Encoded": true,
        "headers": {
            "Content-Type": "application/pdf",
            "Content-Disposition": "attachment; filename=document.pdf"
        },
        "body": "base64_encoded_file_content"
    }
    
    Returns (Presigned URL):
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "data": {
                "download_url": "https://s3.amazonaws.com/..."
            }
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
        presigned = query_params.get('presigned', 'false').lower() == 'true'
        expires_in = int(query_params.get('expires_in', '300'))
        
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
        
        # Return presigned URL if requested
        if presigned:
            url_result = file_service.generate_download_url(
                tenant_id=tenant_id,
                file_id=file_id,
                user_id=user_id,
                expires_in=expires_in
            )
            
            if url_result.success:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'data': {
                            'download_url': url_result.data,
                            'expires_in': expires_in
                        }
                    })
                }
            else:
                return {
                    'statusCode': 404 if url_result.error_code == 'NOT_FOUND' else 403,
                    'body': json.dumps({
                        'success': False,
                        'message': url_result.message,
                        'error_code': url_result.error_code
                    })
                }
        
        # Get file metadata
        file_result = file_service.get_by_id(
            resource_id=file_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        if not file_result.success:
            return {
                'statusCode': 404 if file_result.error_code == 'NOT_FOUND' else 403,
                'body': json.dumps({
                    'success': False,
                    'message': file_result.message,
                    'error_code': file_result.error_code
                })
            }
        
        file = file_result.data
        
        # Download file content
        download_result = file_service.download_file(
            tenant_id=tenant_id,
            file_id=file_id,
            user_id=user_id
        )
        
        if download_result.success:
            file_data = download_result.data
            
            # Return file as base64-encoded response
            return {
                'statusCode': 200,
                'isBase64Encoded': True,
                'headers': {
                    'Content-Type': file.mime_type,
                    'Content-Disposition': f'attachment; filename="{file.file_name}"'
                },
                'body': base64.b64encode(file_data).decode('utf-8')
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'message': download_result.message,
                    'error_code': download_result.error_code
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
