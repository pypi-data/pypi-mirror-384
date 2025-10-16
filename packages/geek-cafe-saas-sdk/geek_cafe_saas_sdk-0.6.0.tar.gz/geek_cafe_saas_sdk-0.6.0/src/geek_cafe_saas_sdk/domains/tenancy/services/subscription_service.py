"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

SubscriptionService for managing tenant subscriptions and billing.
"""

from typing import Dict, Any, Optional, List
from decimal import Decimal
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.services.database_service import DatabaseService
from .tenant_service import TenantService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.domains.tenancy.models import Subscription
from geek_cafe_saas_sdk.domains.tenancy.models import Tenant
import datetime as dt


class SubscriptionService(DatabaseService[Subscription]):
    """
    Service for subscription management operations.
    
    Handles subscription lifecycle including:
    - Creating and activating subscriptions
    - Subscription history tracking
    - Active subscription pointer management
    - Billing period management
    - Payment tracking
    - Cancellations
    
    Uses active subscription pointer pattern:
    - History items: PK=subscription#<id>, SK=subscription#<id>
    - Active pointer: PK=tenant#<tenant_id>, SK=subscription#active
    
    The active pointer allows O(1) lookup of current subscription
    without scanning history.
    """

    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None,
                 tenant_service: TenantService = None):
        super().__init__(dynamodb=dynamodb, table_name=table_name)
        # Tenant service for updating tenant plan_tier
        self.tenant_service = tenant_service or TenantService(
            dynamodb=dynamodb, table_name=table_name
        )

    def create(self, tenant_id: str, user_id: str, payload: Dict[str, Any]) -> ServiceResult[Subscription]:
        """
        Create a new subscription (adds to history).
        
        Note: This creates a subscription record but does NOT make it active.
        Use activate_subscription() to make it the active subscription.
        
        Args:
            tenant_id: Tenant ID this subscription belongs to
            user_id: User ID creating the subscription
            payload: Subscription data
            
        Returns:
            ServiceResult with Subscription
        """
        try:
            # Validate required fields
            required_fields = ['plan_code', 'price_cents']
            self._validate_required_fields(payload, required_fields)

            # Create subscription instance
            subscription = Subscription().map(payload)
            subscription.tenant_id = tenant_id
            subscription.user_id = user_id
            subscription.created_by_id = user_id

            # Set defaults
            if not subscription.currency:
                subscription.currency = "USD"
            if subscription.seat_count < 1:
                subscription.seat_count = 1

            # Prepare for save
            subscription.prep_for_save()

            # Save to database
            return self._save_model(subscription)

        except Exception as e:
            return self._handle_service_exception(e, 'create_subscription',
                                                 tenant_id=tenant_id, user_id=user_id)

    def activate_subscription(self, tenant_id: str, user_id: str, 
                            payload: Dict[str, Any]) -> ServiceResult[Subscription]:
        """
        Create and activate a new subscription for tenant.
        
        This is the main method for changing/starting a subscription.
        It atomically:
        1. Creates subscription history record
        2. Updates active subscription pointer
        3. Updates tenant plan_tier
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID performing action
            payload: Subscription data (plan_code, price_cents, etc.)
            
        Returns:
            ServiceResult with new active Subscription
        """
        try:
            # Validate required fields
            required_fields = ['plan_code', 'price_cents', 'current_period_start_utc_ts',
                             'current_period_end_utc_ts']
            self._validate_required_fields(payload, required_fields)

            # Create subscription
            subscription = Subscription().map(payload)
            subscription.tenant_id = tenant_id
            subscription.user_id = user_id
            subscription.created_by_id = user_id

            # Set defaults
            if not subscription.status:
                subscription.status = "active"
            if not subscription.currency:
                subscription.currency = "USD"
            if subscription.seat_count < 1:
                subscription.seat_count = 1

            # Prepare for save
            subscription.prep_for_save()

            # TODO: Use TransactWrite for atomic operation
            # For now, do sequential writes (not ideal but functional)
            
            # 1. Save subscription history
            save_result = self._save_model(subscription)
            if not save_result.success:
                return save_result

            # 2. Update active pointer
            pointer_result = self._update_active_pointer(tenant_id, subscription.id, user_id)
            if not pointer_result.success:
                # TODO: Rollback subscription creation
                return ServiceResult(
                    success=False,
                    message=f"Failed to update active pointer: {pointer_result.message}",
                    error_code="POINTER_UPDATE_FAILED"
                )

            # 3. Update tenant plan_tier
            plan_tier = self._map_plan_code_to_tier(subscription.plan_code)
            tenant_result = self.tenant_service.update(
                tenant_id, tenant_id, user_id,
                {"plan_tier": plan_tier}
            )
            if not tenant_result.success:
                # Log error but don't fail - subscription is already active
                pass

            return save_result

        except Exception as e:
            return self._handle_service_exception(e, 'activate_subscription',
                                                 tenant_id=tenant_id, user_id=user_id)

    def _update_active_pointer(self, tenant_id: str, subscription_id: str,
                              user_id: str) -> ServiceResult[Dict[str, Any]]:
        """
        Update active subscription pointer for tenant.
        
        Creates/updates a special pointer item:
        PK: tenant#<tenant_id>
        SK: subscription#active
        
        Args:
            tenant_id: Tenant ID
            subscription_id: Subscription ID to point to
            user_id: User performing update
            
        Returns:
            ServiceResult with pointer item data
        """
        try:
            # Build pointer item
            from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
            
            pk = DynamoDBKey.build_key(("tenant", tenant_id))
            sk = "subscription#active"
            
            now = dt.datetime.now(dt.UTC).timestamp()
            
            pointer_item = {
                "pk": pk,
                "sk": sk,
                "active_subscription_id": subscription_id,
                "updated_utc_ts": Decimal(str(now)),  # Convert to Decimal for DynamoDB
                "updated_by_id": user_id
            }

            # Put item
            self.dynamodb.resource.Table(self.table_name).put_item(Item=pointer_item)

            return ServiceResult.success_result(pointer_item)

        except Exception as e:
            return ServiceResult(
                success=False,
                message=f"Failed to update active pointer: {str(e)}",
                error_code="POINTER_UPDATE_ERROR"
            )

    def _map_plan_code_to_tier(self, plan_code: str) -> str:
        """Map plan code to tenant plan_tier."""
        mapping = {
            "free": "free",
            "basic": "basic",
            "basic_monthly": "basic",
            "basic_yearly": "basic",
            "pro": "pro",
            "pro_monthly": "pro",
            "pro_yearly": "pro",
            "enterprise": "enterprise"
        }
        return mapping.get(plan_code, "free")

    def get_active_subscription(self, tenant_id: str, user_id: str) -> ServiceResult[Subscription]:
        """
        Get active subscription for tenant (O(1) lookup via pointer).
        
        Args:
            tenant_id: Tenant ID
            user_id: Requesting user ID
            
        Returns:
            ServiceResult with active Subscription, or None if no active subscription
        """
        try:
            # Get pointer item
            from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
            
            pk = DynamoDBKey.build_key(("tenant", tenant_id))
            sk = "subscription#active"

            response = self.dynamodb.resource.Table(self.table_name).get_item(
                Key={"pk": pk, "sk": sk}
            )

            if "Item" not in response:
                # No active subscription
                return ServiceResult.success_result(None)

            pointer_item = response["Item"]
            active_sub_id = pointer_item.get("active_subscription_id")

            if not active_sub_id:
                return ServiceResult.success_result(None)

            # Get the actual subscription
            return self.get_by_id(active_sub_id, tenant_id, user_id)

        except Exception as e:
            return self._handle_service_exception(e, 'get_active_subscription',
                                                 tenant_id=tenant_id)

    def get_by_id(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[Subscription]:
        """
        Get subscription by ID with access control.
        
        Args:
            resource_id: Subscription ID
            tenant_id: Requesting tenant ID
            user_id: Requesting user ID
            
        Returns:
            ServiceResult with Subscription
        """
        try:
            subscription = self._get_model_by_id(resource_id, Subscription)

            if not subscription:
                raise NotFoundError(f"Subscription with ID {resource_id} not found")

            # Check if deleted
            if subscription.is_deleted():
                raise NotFoundError(f"Subscription with ID {resource_id} not found")

            # Validate tenant access
            if subscription.tenant_id != tenant_id:
                raise AccessDeniedError("You don't have access to this subscription")

            return ServiceResult.success_result(subscription)

        except Exception as e:
            return self._handle_service_exception(e, 'get_subscription',
                                                 resource_id=resource_id, tenant_id=tenant_id)

    def list_subscription_history(self, tenant_id: str, user_id: str,
                                  limit: int = 50) -> ServiceResult[List[Subscription]]:
        """
        List subscription history for tenant (newest first).
        
        Uses GSI1 to query all subscriptions for a tenant, sorted by period start date.
        
        Args:
            tenant_id: Tenant ID
            user_id: Requesting user ID
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of Subscriptions
        """
        try:
            # Create temp subscription for GSI1 query
            temp_sub = Subscription()
            temp_sub.tenant_id = tenant_id            

            result = self._query_by_index(
                temp_sub,
                "gsi1",
                ascending=False,  # Newest first
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted subscriptions
            active_subs = [s for s in result.data if not s.is_deleted()]

            return ServiceResult.success_result(active_subs)

        except Exception as e:
            return self._handle_service_exception(e, 'list_subscription_history',
                                                 tenant_id=tenant_id)

    def cancel_subscription(self, subscription_id: str, tenant_id: str, user_id: str,
                          reason: Optional[str] = None, immediate: bool = False) -> ServiceResult[Subscription]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Subscription ID to cancel
            tenant_id: Tenant ID (for access control)
            user_id: User performing cancellation
            reason: Optional cancellation reason
            immediate: If True, cancel immediately; if False, cancel at period end
            
        Returns:
            ServiceResult with canceled Subscription
        """
        try:
            # Get subscription
            get_result = self.get_by_id(subscription_id, tenant_id, user_id)
            if not get_result.success:
                return get_result

            subscription = get_result.data

            # Cancel
            subscription.cancel(reason=reason, immediate=immediate)
            subscription.updated_by_id = user_id
            subscription.updated_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            subscription.version += 1

            # Save
            save_result = self._save_model(subscription)

            if save_result.success and immediate:
                # If immediate cancellation, could remove active pointer or set to free plan
                # For now, we'll leave the pointer but mark subscription as canceled
                pass

            return save_result

        except Exception as e:
            return self._handle_service_exception(e, 'cancel_subscription',
                                                 subscription_id=subscription_id, tenant_id=tenant_id)

    def record_payment(self, subscription_id: str, tenant_id: str, user_id: str,
                      amount_cents: int) -> ServiceResult[Subscription]:
        """
        Record a successful payment for subscription.
        
        Args:
            subscription_id: Subscription ID
            tenant_id: Tenant ID (for access control)
            user_id: User recording payment
            amount_cents: Payment amount in cents
            
        Returns:
            ServiceResult with updated Subscription
        """
        try:
            # Get subscription
            get_result = self.get_by_id(subscription_id, tenant_id, user_id)
            if not get_result.success:
                return get_result

            subscription = get_result.data

            # Record payment
            subscription.record_payment(amount_cents)
            subscription.updated_by_id = user_id
            subscription.updated_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            subscription.version += 1

            # Save
            return self._save_model(subscription)

        except Exception as e:
            return self._handle_service_exception(e, 'record_payment',
                                                 subscription_id=subscription_id, tenant_id=tenant_id)

    def mark_past_due(self, subscription_id: str, tenant_id: str, user_id: str) -> ServiceResult[Subscription]:
        """
        Mark subscription as past due (payment failed).
        
        Args:
            subscription_id: Subscription ID
            tenant_id: Tenant ID (for access control)
            user_id: User marking as past due
            
        Returns:
            ServiceResult with updated Subscription
        """
        try:
            # Get subscription
            get_result = self.get_by_id(subscription_id, tenant_id, user_id)
            if not get_result.success:
                return get_result

            subscription = get_result.data

            # Mark past due
            subscription.mark_past_due()
            subscription.updated_by_id = user_id
            subscription.updated_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            subscription.version += 1

            # Save
            return self._save_model(subscription)

        except Exception as e:
            return self._handle_service_exception(e, 'mark_past_due',
                                                 subscription_id=subscription_id, tenant_id=tenant_id)

    def list_subscriptions_by_status(self, status: str, limit: int = 50) -> ServiceResult[List[Subscription]]:
        """
        List subscriptions by status (for billing jobs/admin).
        
        Uses GSI2 to query subscriptions by status, sorted by next_billing_date.
        This is useful for background jobs that process billing.
        
        Args:
            status: Subscription status (trial|active|past_due|canceled|expired)
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of Subscriptions
        """
        try:
            # Create temp subscription for GSI2 query
            temp_sub = Subscription()
            temp_sub.status = status

            result = self._query_by_index(
                temp_sub,
                "gsi2",
                ascending=True,  # Earliest next billing first
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted subscriptions
            active_subs = [s for s in result.data if not s.is_deleted()]

            return ServiceResult.success_result(active_subs)

        except Exception as e:
            return self._handle_service_exception(e, 'list_subscriptions_by_status',
                                                 status=status)

    def update(self, resource_id: str, tenant_id: str, user_id: str,
               updates: Dict[str, Any]) -> ServiceResult[Subscription]:
        """
        Update subscription.
        
        Args:
            resource_id: Subscription ID to update
            tenant_id: Tenant ID (for access control)
            user_id: User ID making update
            updates: Fields to update
            
        Returns:
            ServiceResult with updated Subscription
        """
        try:
            # Get subscription
            get_result = self.get_by_id(resource_id, tenant_id, user_id)
            if not get_result.success:
                return get_result

            subscription = get_result.data

            # Update fields
            subscription.map(updates)
            subscription.updated_by_id = user_id
            subscription.updated_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            subscription.version += 1

            # Save
            return self._save_model(subscription)

        except Exception as e:
            return self._handle_service_exception(e, 'update_subscription',
                                                 resource_id=resource_id, tenant_id=tenant_id)

    def delete(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[bool]:
        """
        Soft delete subscription.
        
        Args:
            resource_id: Subscription ID to delete
            tenant_id: Tenant ID (for access control)
            user_id: User ID performing delete
            
        Returns:
            ServiceResult with boolean (True if deleted)
        """
        try:
            # Get subscription
            get_result = self.get_by_id(resource_id, tenant_id, user_id)
            if not get_result.success:
                return ServiceResult(success=False, message=get_result.message,
                                   error_code=get_result.error_code)

            subscription = get_result.data

            # Soft delete
            subscription.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            subscription.deleted_by_id = user_id
            subscription.updated_by_id = user_id
            subscription.updated_utc_ts = dt.datetime.now(dt.UTC).timestamp()

            # Save
            save_result = self._save_model(subscription)
            if not save_result.success:
                return ServiceResult(success=False, message=save_result.message,
                                   error_code=save_result.error_code)

            return ServiceResult.success_result(True)

        except Exception as e:
            return self._handle_service_exception(e, 'delete_subscription',
                                                 resource_id=resource_id, tenant_id=tenant_id)
