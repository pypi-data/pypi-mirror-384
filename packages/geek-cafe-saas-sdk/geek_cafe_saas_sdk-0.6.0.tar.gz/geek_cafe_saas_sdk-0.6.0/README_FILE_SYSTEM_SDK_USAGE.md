# Geek Cafe SaaS SDK - File System Module

A comprehensive, production-ready file system SDK for building multi-tenant SaaS applications on AWS.

---

## Overview

The File System module provides a complete solution for managing files, directories, versions, and sharing in a multi-tenant environment using AWS S3 and DynamoDB.

### Key Features

- ✅ **Multi-tenant isolation** with tenant-based access control
- ✅ **S3 + DynamoDB** for scalable file storage and metadata
- ✅ **Dual versioning strategies** (S3 native or explicit tracking)
- ✅ **Virtual directory hierarchies** with efficient path management
- ✅ **File sharing** with granular permissions (view/download/edit)
- ✅ **Version management** with restore capabilities
- ✅ **Presigned URLs** for direct client uploads/downloads
- ✅ **Comprehensive testing** with 99 passing tests using Moto

---

## Installation

```bash
pip install geek-cafe-saas-sdk
```

### Dependencies

```bash
pip install boto3>=1.28.0
pip install boto3-assist>=1.0.0
```

---

## Quick Start

### 1. Initialize Services

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.s3.s3_connection import S3Connection
from boto3_assist.s3.s3_object import S3Object
from boto3_assist.s3.s3_bucket import S3Bucket

from geek_cafe_saas_sdk.domains.files.services.file_system_service import FileSystemService
from geek_cafe_saas_sdk.domains.files.services.s3_file_service import S3FileService

# Initialize AWS clients
db = DynamoDB()
connection = S3Connection()

# Initialize S3 service
s3_service = S3FileService(
    s3_object=S3Object(connection=connection),
    s3_bucket=S3Bucket(connection=connection),
    default_bucket="my-files-bucket"
)

# Initialize file service
file_service = FileSystemService(
    dynamodb=db,
    table_name="my-table",
    s3_service=s3_service,
    default_bucket="my-files-bucket"
)
```

### 2. Upload a File

```python
# Upload file
result = file_service.create(
    tenant_id="tenant-123",
    user_id="user-456",
    file_name="document.pdf",
    file_data=b"PDF content here",
    mime_type="application/pdf"
)

if result.success:
    file = result.data
    print(f"File uploaded: {file.file_id}")
else:
    print(f"Error: {result.message}")
```

### 3. Download a File

```python
# Download file content
download_result = file_service.download_file(
    tenant_id="tenant-123",
    file_id="file-789",
    user_id="user-456"
)

if download_result.success:
    file_data = download_result.data
    with open("downloaded.pdf", "wb") as f:
        f.write(file_data)
```

---

## AWS Infrastructure Requirements

### DynamoDB Table

Create a table with this schema:

```python
# Using boto3
dynamodb = boto3.client('dynamodb')

dynamodb.create_table(
    TableName='files-table',
    BillingMode='PAY_PER_REQUEST',
    AttributeDefinitions=[
        {'AttributeName': 'pk', 'AttributeType': 'S'},
        {'AttributeName': 'sk', 'AttributeType': 'S'},
        {'AttributeName': 'gsi1_pk', 'AttributeType': 'S'},
        {'AttributeName': 'gsi1_sk', 'AttributeType': 'S'},
        {'AttributeName': 'gsi2_pk', 'AttributeType': 'S'},
        {'AttributeName': 'gsi2_sk', 'AttributeType': 'S'},
    ],
    KeySchema=[
        {'AttributeName': 'pk', 'KeyType': 'HASH'},
        {'AttributeName': 'sk', 'KeyType': 'RANGE'}
    ],
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'gsi1',
            'KeySchema': [
                {'AttributeName': 'gsi1_pk', 'KeyType': 'HASH'},
                {'AttributeName': 'gsi1_sk', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        },
        {
            'IndexName': 'gsi2',
            'KeySchema': [
                {'AttributeName': 'gsi2_pk', 'KeyType': 'HASH'},
                {'AttributeName': 'gsi2_sk', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ]
)
```

**Or use CloudFormation/CDK/Terraform** - see `docs/LAMBDA_DEPLOYMENT.md` for examples.

### S3 Bucket

```python
s3 = boto3.client('s3')
s3.create_bucket(Bucket='my-files-bucket')

# Optional: Enable versioning for S3-native strategy
s3.put_bucket_versioning(
    Bucket='my-files-bucket',
    VersioningConfiguration={'Status': 'Enabled'}
)
```

---

## Core Services

### 1. FileSystemService

Core file operations - upload, download, update, delete, list.

```python
from geek_cafe_saas_sdk.domains.files.services.file_system_service import FileSystemService

file_service = FileSystemService(dynamodb, table_name, s3_service, bucket)
```

**Key Methods:**
- `create()` - Upload new file
- `get_by_id()` - Get file metadata
- `update()` - Update metadata
- `delete()` - Soft or hard delete
- `download_file()` - Download content
- `generate_download_url()` - Get presigned URL
- `list_files_by_directory()` - List files
- `list_files_by_owner()` - List by owner

### 2. DirectoryService

Virtual directory management.

```python
from geek_cafe_saas_sdk.domains.files.services.directory_service import DirectoryService

dir_service = DirectoryService(dynamodb, table_name)
```

**Key Methods:**
- `create()` - Create directory
- `get_by_id()` - Get directory
- `update()` - Update directory
- `delete()` - Delete directory
- `list_by_parent()` - List subdirectories
- `move()` - Move to new parent
- `get_path_components()` - Get breadcrumb path

### 3. FileVersionService

Explicit version tracking and management.

```python
from geek_cafe_saas_sdk.domains.files.services.file_version_service import FileVersionService

version_service = FileVersionService(dynamodb, table_name, s3_service, bucket)
```

**Key Methods:**
- `create()` - Create new version
- `list_versions()` - List all versions
- `restore_version()` - Restore old version
- `download_version()` - Download specific version
- `delete()` - Delete version

### 4. FileShareService

File sharing with permissions.

```python
from geek_cafe_saas_sdk.domains.files.services.file_share_service import FileShareService

share_service = FileShareService(dynamodb, table_name)
```

**Key Methods:**
- `create()` - Share file with user
- `list_shares_by_file()` - List file shares
- `list_shares_with_user()` - List shares with user
- `check_access()` - Validate access
- `update()` - Update permissions
- `delete()` - Revoke share

### 5. S3FileService

Low-level S3 operations.

```python
from geek_cafe_saas_sdk.domains.files.services.s3_file_service import S3FileService

s3_service = S3FileService(s3_object, s3_bucket, bucket)
```

**Key Methods:**
- `upload_file()` - Upload to S3
- `download_file()` - Download from S3
- `delete_file()` - Delete from S3
- `generate_presigned_url()` - Generate URLs

---

## Using in Your Application

### Option 1: Direct Service Usage

Use the services directly in your application code:

```python
from geek_cafe_saas_sdk.domains.files.services import FileSystemService

# In your business logic
def handle_file_upload(tenant_id, user_id, file_data):
    file_service = get_file_service()  # Your initialization
    
    result = file_service.create(
        tenant_id=tenant_id,
        user_id=user_id,
        file_name="document.pdf",
        file_data=file_data,
        mime_type="application/pdf"
    )
    
    return result.data if result.success else None
```

### Option 2: Lambda Handlers (Reference)

The SDK includes **reference Lambda handler implementations** in `lambda_handlers/`. These are templates to copy into your project and customize:

```bash
# Copy handlers to your project
cp -r geek-cafe-saas-sdk/lambda_handlers/files your-project/handlers/

# Customize and deploy with SAM/Serverless/CDK
```

See `src/geek_cafe_saas_sdk/lambda_handlers/README.md` for details.

### Option 3: Integrate with Existing APIs

Wrap SDK services in your existing API framework:

```python
# Flask example
from flask import Flask, request
from geek_cafe_saas_sdk.domains.files.services import FileSystemService

app = Flask(__name__)

@app.route('/api/files', methods=['POST'])
def upload_file():
    file_service = get_file_service()
    
    result = file_service.create(
        tenant_id=request.json['tenant_id'],
        user_id=get_current_user(),
        file_name=request.json['file_name'],
        file_data=base64.b64decode(request.json['file_data']),
        mime_type=request.json.get('mime_type')
    )
    
    if result.success:
        return {'file_id': result.data.file_id}, 201
    else:
        return {'error': result.message}, 400
```

---

## Testing

The SDK uses Moto for AWS mocking in tests:

```python
import pytest
from moto import mock_aws
import boto3

@pytest.fixture
def aws_setup():
    with mock_aws():
        # Create test bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        # Create test table
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.create_table(...)
        
        yield

def test_file_upload(aws_setup):
    file_service = FileSystemService(...)
    
    result = file_service.create(
        tenant_id="test",
        user_id="user1",
        file_name="test.txt",
        file_data=b"content"
    )
    
    assert result.success is True
```

See `tests/` directory for 99 comprehensive test examples.

---

## Documentation

- **[Usage Guide](docs/FILE_SYSTEM_USAGE.md)** - Complete guide with examples
- **[API Reference](docs/FILE_SYSTEM_API.md)** - Detailed API documentation
- **[Lambda Reference](docs/LAMBDA_DEPLOYMENT.md)** - Lambda handler templates
- **[Design Doc](docs/FILE_SYSTEM_DESIGN.md)** - Architecture and design decisions

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Your Application                        │
│         (Lambda, Flask, FastAPI, Django, etc.)           │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ imports
                         ▼
┌──────────────────────────────────────────────────────────┐
│              Geek Cafe SaaS SDK (this package)           │
│  ┌────────────────────────────────────────────────────┐  │
│  │  FileSystemService                                 │  │
│  │  DirectoryService                                  │  │
│  │  FileVersionService                                │  │
│  │  FileShareService                                  │  │
│  │  S3FileService                                     │  │
│  └────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────┬────────────────┘
             │                            │
             ▼                            ▼
    ┌────────────────┐         ┌──────────────────┐
    │   DynamoDB     │         │    S3 Bucket     │
    │   (Metadata)   │         │  (File Storage)  │
    └────────────────┘         └──────────────────┘
```

---

## Examples

See `docs/FILE_SYSTEM_USAGE.md` for complete examples including:

- Upload files to directories
- Create file versions
- Share files with permissions
- Generate presigned URLs
- List and search files
- Move files between directories
- Restore previous versions
- Multi-user collaboration workflows

---

## License

MIT License. See LICENSE file for details.

---

## Support

For issues, questions, or contributions:
- GitHub: [geek-cafe/geek-cafe-saas-sdk](https://github.com/geek-cafe/geek-cafe-saas-sdk)
- Documentation: See `docs/` directory
- Tests: See `tests/` for examples

---

**Build better SaaS applications with Geek Cafe SDK!** 🚀
