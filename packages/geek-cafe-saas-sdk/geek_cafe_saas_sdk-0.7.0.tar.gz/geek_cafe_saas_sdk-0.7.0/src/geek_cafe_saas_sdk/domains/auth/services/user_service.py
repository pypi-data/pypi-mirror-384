# User Service

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.utilities.dynamodb_utils import build_projection_with_reserved_keywords
from geek_cafe_saas_sdk.domains.auth.models import User
import datetime as dt


class UserService(DatabaseService[User]):

    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None):
        super().__init__(dynamodb=dynamodb, table_name=table_name)

    def create(self, tenant_id: str, user_id: str, **kwargs) -> ServiceResult[User]:
        """Create a new user."""
        try:
            # Validate required fields
            required_fields = ['email', 'first_name', 'last_name']
            self._validate_required_fields(kwargs, required_fields)

            # Create user instance using map() approach
            user = User().map(kwargs)
            user.tenant_id = tenant_id
            user.user_id = user_id  # Set creator
            user.created_by_id = user_id

            # Prepare for save (sets ID and timestamps)
            user.prep_for_save()

            # Save to database
            return self._save_model(user)

        except Exception as e:
            return self._handle_service_exception(e, 'create_user', tenant_id=tenant_id, user_id=user_id)

    def get_by_id(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[User]:
        """Get user by ID with access control."""
        try:
            user = self._get_model_by_id(resource_id, User)

            if not user:
                raise NotFoundError(f"User with ID {resource_id} not found")

            # Check if deleted
            if user.is_deleted():
                raise NotFoundError(f"User with ID {resource_id} not found")

            # Validate tenant access
            if hasattr(user, 'tenant_id'):
                self._validate_tenant_access(user.tenant_id, tenant_id)

            return ServiceResult.success_result(user)

        except Exception as e:
            return self._handle_service_exception(e, 'get_user', resource_id=resource_id, tenant_id=tenant_id)

    def get_by_email(self, email: str, tenant_id: str, user_id: str) -> ServiceResult[User]:
        """Get user by email using GSI1."""
        try:
            # Create a temporary user instance to get the GSI key
            temp_user = User()
            temp_user.email = email

            result = self._query_by_index(
                temp_user,
                "gsi1",
                ascending=False
            )

            if not result.success or not result.data:
                raise NotFoundError(f"User with email {email} not found")

            # Get the first (most recent) result
            user = result.data[0]

            # Check if deleted
            if user.is_deleted():
                raise NotFoundError(f"User with email {email} not found")

            # Validate tenant access
            self._validate_tenant_access(user.tenant_id, tenant_id)

            return ServiceResult.success_result(user)

        except Exception as e:
            return self._handle_service_exception(e, 'get_user_by_email', email=email, tenant_id=tenant_id)

    def get_users_by_tenant(self, tenant_id: str, user_id: str, limit: int = 50) -> ServiceResult[List[User]]:
        """Get all users for a tenant using GSI2."""
        try:
            # Create a temporary user instance to get the GSI key
            temp_user = User()
            temp_user.tenant_id = tenant_id

            result = self._query_by_index(
                temp_user,
                "gsi2",
                ascending=False,  # Most recent first
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted users and validate tenant access
            active_users = []
            for user in result.data:
                if not user.is_deleted() and user.tenant_id == tenant_id:
                    active_users.append(user)

            return ServiceResult.success_result(active_users)

        except Exception as e:
            return self._handle_service_exception(e, 'get_users_by_tenant', tenant_id=tenant_id)

    def get_users_by_role(self, role: str, tenant_id: str, user_id: str, limit: int = 50) -> ServiceResult[List[User]]:
        """Get users by role within a tenant using GSI3."""
        try:
            # Create a temporary user instance to get the GSI key
            temp_user = User()
            temp_user._roles = [role]  # Set the primary role

            result = self._query_by_index(
                temp_user,
                "gsi3",
                ascending=False,  # Most recent first
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted users and validate tenant access
            active_users = []
            for user in result.data:
                if not user.is_deleted() and user.tenant_id == tenant_id and user.has_role(role):
                    active_users.append(user)

            return ServiceResult.success_result(active_users)

        except Exception as e:
            return self._handle_service_exception(e, 'get_users_by_role', role=role, tenant_id=tenant_id)

    def restore_user(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[User]:
        """Restore a soft-deleted user (admin only)."""
        try:
            # Check permissions (admin only)
            if not self._is_admin_user(user_id, tenant_id):
                raise AccessDeniedError("Access denied: insufficient permissions")

            # Get existing user (even if deleted)
            user = self._get_model_by_id(resource_id, User)

            if not user:
                raise NotFoundError(f"User with ID {resource_id} not found")

            # Validate tenant access
            if hasattr(user, 'tenant_id'):
                self._validate_tenant_access(user.tenant_id, tenant_id)

            # Check if actually deleted
            if not user.is_deleted():
                return ServiceResult.success_result(user)  # Already active

            # Restore: clear deleted timestamp and metadata
            user.deleted_utc_ts = None
            user.deleted_by_id = None
            user.updated_by_id = user_id
            user.prep_for_save()  # Updates timestamp

            # Save the restored user
            save_result = self._save_model(user)
            if save_result.success:
                return ServiceResult.success_result(user)
            else:
                return save_result

        except Exception as e:
            return self._handle_service_exception(e, 'restore_user', resource_id=resource_id, tenant_id=tenant_id)

    def update(self, resource_id: str, tenant_id: str, user_id: str,
               updates: Dict[str, Any]) -> ServiceResult[User]:
        try:
            # Get existing user
            user = self._get_model_by_id(resource_id, User)

            if not user:
                raise NotFoundError(f"User with ID {resource_id} not found")

            # Validate tenant access
            if hasattr(user, 'tenant_id'):
                self._validate_tenant_access(user.tenant_id, tenant_id)

            # Check if user can update (admin or self)
            if not (user_id == resource_id or self._is_admin_user(user_id, tenant_id)):
                raise AccessDeniedError("Access denied: insufficient permissions")

            # Prevent non-admins from updating roles
            if 'roles' in updates and not self._is_admin_user(user_id, tenant_id):
                raise AccessDeniedError("Access denied: only admins can update roles")

            # Apply updates
            for field, value in updates.items():
                if hasattr(user, field) and field not in ['id', 'created_utc_ts', 'tenant_id', 'organizer_id']:
                    if field == 'email':
                        user.email = value
                    elif field == 'first_name':
                        user.first_name = value
                    elif field == 'last_name':
                        user.last_name = value
                    elif field == 'roles':
                        user.roles = value
                    elif field == 'avatar':
                        user.avatar = value

            # Update metadata
            user.updated_by_id = user_id
            user.prep_for_save()  # Updates timestamp

            # Save updated user
            return self._save_model(user)

        except Exception as e:
            return self._handle_service_exception(e, 'update_user', resource_id=resource_id, tenant_id=tenant_id)

    def delete(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[bool]:
        """Soft delete user with access control."""
        try:
            # Get existing user
            user = self._get_model_by_id(resource_id, User)

            if not user:
                raise NotFoundError(f"User with ID {resource_id} not found")

            # Check if already deleted
            if user.is_deleted():
                return ServiceResult.success_result(True)

            # Validate tenant access
            if hasattr(user, 'tenant_id'):
                self._validate_tenant_access(user.tenant_id, tenant_id)

            # Check permissions (admin or self)
            if not (user_id == resource_id or self._is_admin_user(user_id, tenant_id)):
                raise AccessDeniedError("Access denied: insufficient permissions")

            # Prevent deleting self
            if user_id == resource_id:
                raise ValidationError("Cannot delete your own account")

            # Soft delete: set deleted timestamp and metadata
            user.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            user.deleted_by_id = user_id
            user.prep_for_save()  # Updates timestamp

            # Save the updated user
            save_result = self._save_model(user)
            if save_result.success:
                return ServiceResult.success_result(True)
            else:
                return save_result

        except Exception as e:
            return self._handle_service_exception(e, 'delete_user', resource_id=resource_id, tenant_id=tenant_id)

    def _is_admin_user(self, user_id: str, tenant_id: str) -> bool:
        """Check if user has admin role (placeholder - will be implemented when UserService is available)."""
        # For now, assume no admin privileges
        # This will be enhanced when we have user service integration
        return False
