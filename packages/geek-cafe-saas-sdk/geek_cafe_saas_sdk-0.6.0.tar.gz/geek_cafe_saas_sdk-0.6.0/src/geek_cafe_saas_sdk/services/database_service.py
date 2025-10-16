# Database Service

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Dict, Any, List, Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from ..core.service_result import ServiceResult
from ..core.service_errors import ValidationError, AccessDeniedError, NotFoundError
from ..core.error_codes import ErrorCode
import os

T = TypeVar("T")


class DatabaseService(ABC, Generic[T]):
    """Base service class for database operations."""

    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None):
        self.dynamodb = dynamodb or DynamoDB()
        self.table_name = (
            table_name or os.getenv("DYNAMODB_TABLE_NAME")
        )

        if not self.table_name:
            raise ValueError("Table name is required")

    @abstractmethod
    def create(self, tenant_id: str, user_id: str, **kwargs) -> ServiceResult[T]:
        """Create a new resource."""
        pass

    @abstractmethod
    def get_by_id(
        self, resource_id: str, tenant_id: str, user_id: str
    ) -> ServiceResult[T]:
        """Get resource by ID with access control."""
        pass

    @abstractmethod
    def update(
        self, resource_id: str, tenant_id: str, user_id: str, updates: Dict[str, Any]
    ) -> ServiceResult[T]:
        """Update resource with access control."""
        pass

    @abstractmethod
    def delete(
        self, resource_id: str, tenant_id: str, user_id: str
    ) -> ServiceResult[bool]:
        """Delete resource with access control."""
        pass

    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """Validate required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            if len(missing_fields) == 1:
                raise ValidationError(f"Field '{missing_fields[0]}' is required", missing_fields[0])
            else:
                field_list = "', '".join(missing_fields)
                raise ValidationError(f"Fields '{field_list}' are required", missing_fields)
    
    def _validate_owner_field(
        self, payload: Dict[str, Any], authenticated_user_id: str, field_name: str = "owner_id"
    ) -> str:
        """
        Validate and resolve owner field following Rule #3.
        
        Pattern:
        - Missing owner_id: Default to authenticated user (self-service)
        - Present owner_id with value: Use specified owner (admin-on-behalf)
        - Present owner_id but empty/null: ERROR (explicit but invalid)
        
        Args:
            payload: Request payload
            authenticated_user_id: User ID from JWT
            field_name: Name of owner field (default: "owner_id")
            
        Returns:
            Resolved owner user ID
            
        Raises:
            ValidationError: If owner_id is explicitly provided but empty/null
        """
        # Check if field is explicitly provided in payload
        if field_name in payload:
            owner_id = payload[field_name]
            # Explicit but empty/null = error (fail fast)
            if not owner_id:
                raise ValidationError(
                    f"{field_name} cannot be empty when explicitly provided",
                    field_name
                )
            return owner_id
        
        # Field not provided = default to authenticated user (self-service)
        return authenticated_user_id

    def _validate_tenant_access(
        self, resource_tenant_id: str, user_tenant_id: str
    ) -> None:
        """Validate user has access to tenant resources."""
        if resource_tenant_id != user_tenant_id:
            raise AccessDeniedError("Access denied to resource in different tenant")

    def _save_model(self, model: T) -> ServiceResult[T]:
        """Save model to database with enhanced error handling."""
        try:
            # The boto3_assist library handles all GSI key population automatically.
            self.dynamodb.save(table_name=self.table_name, item=model)
            return ServiceResult.success_result(model)
        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_SAVE_FAILED,
                context=f"Failed to save model to table {self.table_name}",
            )

    def _get_model_by_id(self, resource_id: str, model_class) -> Optional[T]:
        """Get model by ID from database."""
        try:
            # Create temporary model instance to get the primary key
            temp_model = model_class()
            temp_model.id = resource_id
            key = temp_model.get_key("primary").key()

            result = self.dynamodb.get(table_name=self.table_name, key=key)
            if not result or "Item" not in result:
                return None

            # Create model instance from database result
            model = model_class()
            model.map(result["Item"])

            return model
        except Exception:
            return None

    def _get_model_by_id_with_tenant_check(
        self, resource_id: str, model_class, tenant_id: str
    ) -> Optional[T]:
        """
        Get model by ID with automatic tenant validation.
        
        This method provides tenant isolation security by ensuring that resources
        can only be accessed within their own tenant. If the resource belongs to
        a different tenant, it returns None (hiding its existence).
        
        Args:
            resource_id: The resource ID to fetch
            model_class: The model class to instantiate
            tenant_id: The tenant ID from JWT (authenticated user's tenant)
            
        Returns:
            The model if found and belongs to tenant, None otherwise
            
        Security:
            - Returns None for resources in different tenants (prevents enumeration)
            - Returns None for deleted resources
            - Single source of truth: tenant_id from JWT only
        """
        model = self._get_model_by_id(resource_id, model_class)
        
        if not model:
            return None
        
        # Tenant isolation: Only return resource if it belongs to user's tenant
        if hasattr(model, 'tenant_id') and model.tenant_id != tenant_id:
            # Return None instead of raising error to hide existence
            # from users in other tenants (prevent enumeration attacks)
            return None
        
        # Hide deleted resources
        if hasattr(model, 'is_deleted') and callable(model.is_deleted):
            if model.is_deleted():
                return None
        
        return model

    def _delete_model(self, model: T) -> ServiceResult[bool]:
        """Delete model from database with enhanced error handling."""
        try:
            primary_key = model.get_key("primary").key()
            self.dynamodb.delete(table_name=self.table_name, primary_key=primary_key)
            return ServiceResult.success_result(True)
        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_DELETE_FAILED,
                context=f"Failed to delete model from table {self.table_name}",
            )

    def _query_by_index(
        self,
        model: T,
        index_name: str,
        *,
        ascending: bool = False,
        strongly_consistent: bool = False,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        start_key: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> ServiceResult[List[T]]:
        """
        Generic query method for GSI queries with automatic model mapping.

        Args:
            model: The pre-configured model instance to use for the query
            index_name: The name of the GSI index to query

        Returns:
            ServiceResult containing a list of mapped model instances.
            Pagination info is included in error_details as 'last_evaluated_key' if more results exist.
        """
        try:
            # Get the key for the specified index from the provided model
            key = model.get_key(index_name).key()

            # Execute the query
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                index_name=index_name,
                ascending=ascending,
                strongly_consistent=strongly_consistent,
                projection_expression=projection_expression,
                expression_attribute_names=expression_attribute_names,
                start_key=start_key,
                limit=limit,
            )

            # Extract items from response
            data = response.get("Items", [])

            # Map each item to a model instance
            model_class = type(model)
            items = [model_class().map(item) for item in data]

            # Include pagination info if present
            result = ServiceResult.success_result(items)
            if "LastEvaluatedKey" in response:
                result.error_details = {"last_evaluated_key": response["LastEvaluatedKey"]}

            return result

        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_QUERY_FAILED,
                context=f"Failed to query index {index_name} on table {self.table_name}",
            )

    def _query_by_pk_with_sk_prefix(
        self,
        model_class: type,
        pk: str,
        sk_prefix: str,
        *,
        index_name: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        start_key: Optional[dict] = None,
    ) -> ServiceResult[List[T]]:
        """
        Query by partition key with sort key prefix (begins_with pattern).
        
        This is useful for adjacent record patterns where multiple record types
        are stored under the same partition key, distinguished by sort key prefix:
        - pk="channel#123" AND sk BEGINS_WITH "member#" (all members)
        - pk="channel#123" AND sk BEGINS_WITH "message#" (all messages)
        - pk="user#456" AND sk BEGINS_WITH "session#" (all sessions)
        
        Args:
            model_class: The model class to map results to
            pk: Partition key value
            sk_prefix: Sort key prefix for begins_with condition
            index_name: Index to query (None for primary index)
            ascending: Sort order (True=ascending, False=descending)
            limit: Maximum number of items to return
            start_key: For pagination
            
        Returns:
            ServiceResult containing list of mapped model instances
            
        Example:
            # Get all members in a channel
            result = self._query_by_pk_with_sk_prefix(
                model_class=ChatChannelMember,
                pk="channel#channel_123",
                sk_prefix="member#",
                limit=100
            )
        """
        try:
            # Build key condition expression
            if index_name:
                pk_attr = f"{index_name}_pk" if index_name.startswith("gsi") else "pk"
                sk_attr = f"{index_name}_sk" if index_name.startswith("gsi") else "sk"
            else:
                pk_attr = "pk"
                sk_attr = "sk"
            
            # Use boto3 client for begins_with condition
            query_params = {
                "TableName": self.table_name,
                "KeyConditionExpression": f"{pk_attr} = :pk AND begins_with({sk_attr}, :prefix)",
                "ExpressionAttributeValues": {
                    ":pk": pk,
                    ":prefix": sk_prefix
                },
                "ScanIndexForward": ascending,
            }
            
            if index_name:
                query_params["IndexName"] = index_name
            if limit:
                query_params["Limit"] = limit
            if start_key:
                query_params["ExclusiveStartKey"] = start_key
            
            response = self.dynamodb.client.query(**query_params)
            
            # Map results to model instances
            items = [model_class().map(item) for item in response.get("Items", [])]
            
            # Include pagination info
            result = ServiceResult.success_result(items)
            if "LastEvaluatedKey" in response:
                result.error_details = {"last_evaluated_key": response["LastEvaluatedKey"]}
            
            return result
            
        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_QUERY_FAILED,
                context=f"Failed to query with pk prefix on table {self.table_name}",
            )

    def _delete_by_composite_key(
        self,
        pk: str,
        sk: str,
    ) -> ServiceResult[bool]:
        """
        Delete an item by composite key (pk + sk).
        
        Useful for adjacent record patterns where items use composite keys
        instead of a single id field.
        
        Args:
            pk: Partition key value
            sk: Sort key value
            
        Returns:
            ServiceResult[bool] - True if successful
            
        Example:
            # Delete a specific member from a channel
            result = self._delete_by_composite_key(
                pk="channel#channel_123",
                sk="member#user_456"
            )
        """
        try:
            # Use boto3 resource (simpler API that handles typing)
            key = {"pk": pk, "sk": sk}
            self.dynamodb.delete(table_name=self.table_name, primary_key=key)
            return ServiceResult.success_result(True)
            
        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_DELETE_FAILED,
                context=f"Failed to delete item by composite key from table {self.table_name}",
            )

    def _handle_service_exception(
        self, e: Exception, operation: str, **context
    ) -> ServiceResult[T]:
        """
        Common exception handler for service operations.
        
        Maps exception types to standardized error codes and formats error details.
        Always includes operation name in error details for debugging.
        
        Args:
            e: The exception that was raised
            operation: Name of the operation that failed (for logging/debugging)
            **context: Additional context information (resource_id, tenant_id, etc.)
        
        Returns:
            ServiceResult with appropriate error information
        """
        # Build base error details with operation
        error_details = {"operation": operation, **context}
        
        # Validation errors (4xx equivalent)
        if isinstance(e, ValidationError):
            field_info = getattr(e, "field", None)
            # Handle both single field and list of fields
            if isinstance(field_info, list):
                error_details["fields"] = field_info
            elif field_info:
                error_details["field"] = field_info
            
            return ServiceResult.error_result(
                message=f"Validation failed: {str(e)}",
                error_code=ErrorCode.VALIDATION_ERROR,
                error_details=error_details,
            )
        
        # Authorization errors (403 equivalent)
        elif isinstance(e, AccessDeniedError):
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.ACCESS_DENIED,
                error_details=error_details
            )
        
        # Resource not found (404 equivalent)
        elif isinstance(e, NotFoundError):
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.NOT_FOUND,
                error_details=error_details
            )
        
        # Unexpected errors (500 equivalent)
        else:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context=f"Operation '{operation}' failed: {str(e)}"
            )
