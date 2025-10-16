# Event Attendee Service

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.domains.events.models import EventAttendee
from geek_cafe_saas_sdk.utilities.dynamodb_utils import build_projection_with_reserved_keywords
import datetime as dt


class EventAttendeeService(DatabaseService[EventAttendee]):
    """Service for EventAttendee database operations (RSVP tracking, invitations, check-in)."""

    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None):
        super().__init__(dynamodb=dynamodb, table_name=table_name)

    # Required abstract methods from DatabaseService
    def create(self, tenant_id: str, user_id: str, **kwargs) -> ServiceResult[EventAttendee]:
        """Create method - delegates to invite() for EventAttendee."""
        if 'event_id' not in kwargs:
            return ServiceResult.error_result("event_id is required", "VALIDATION_ERROR")
        
        event_id = kwargs.pop('event_id')
        invited_by = kwargs.pop('invited_by_user_id', user_id)
        
        return self.invite(
            event_id=event_id,
            user_id=kwargs.pop('user_id', user_id),
            tenant_id=tenant_id,
            invited_by_user_id=invited_by,
            **kwargs
        )

    def get_by_id(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[EventAttendee]:
        """Get method - resource_id should be in format 'event_id:user_id'."""
        try:
            if ':' in resource_id:
                event_id, attendee_user_id = resource_id.split(':', 1)
            else:
                return ServiceResult.error_result("Invalid resource_id format. Use 'event_id:user_id'", "VALIDATION_ERROR")
            
            return self.get_attendee(event_id, attendee_user_id, tenant_id)
        except Exception as e:
            return self._handle_service_exception(e, 'get_by_id', resource_id=resource_id)

    def update(self, resource_id: str, tenant_id: str, user_id: str, updates: Dict[str, Any]) -> ServiceResult[EventAttendee]:
        """Update method - updates attendee record."""
        try:
            if ':' in resource_id:
                event_id, attendee_user_id = resource_id.split(':', 1)
            else:
                return ServiceResult.error_result("Invalid resource_id format. Use 'event_id:user_id'", "VALIDATION_ERROR")
            
            # Get existing attendee
            result = self.get_attendee(event_id, attendee_user_id, tenant_id)
            if not result.success:
                return result
            
            attendee = result.data
            
            # Update fields
            for key, value in updates.items():
                if hasattr(attendee, key):
                    setattr(attendee, key, value)
            
            attendee.updated_by_id = user_id
            attendee.prep_for_save()
            return self._save_model(attendee)
            
        except Exception as e:
            return self._handle_service_exception(e, 'update', resource_id=resource_id)

    def delete(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[bool]:
        """Delete method - soft deletes attendee."""
        try:
            if ':' in resource_id:
                event_id, attendee_user_id = resource_id.split(':', 1)
            else:
                return ServiceResult.error_result("Invalid resource_id format. Use 'event_id:user_id'", "VALIDATION_ERROR")
            
            return self.remove_attendee(event_id, attendee_user_id, tenant_id, user_id)
            
        except Exception as e:
            return self._handle_service_exception(e, 'delete', resource_id=resource_id)

    def invite(self, event_id: str, user_id: str, tenant_id: str, 
               invited_by_user_id: str, **kwargs) -> ServiceResult[EventAttendee]:
        """
        Invite a user to an event.
        
        Args:
            event_id: Event ID
            user_id: User ID to invite
            tenant_id: Tenant ID
            invited_by_user_id: Who is inviting
            **kwargs: Additional fields (role, registration_data, etc.)
        """
        try:
            # Check if already invited
            existing = self.get_attendee(event_id, user_id, tenant_id)
            if existing.success:
                return ServiceResult.error_result("User is already invited to this event", "ALREADY_INVITED")

            # Create attendee record
            attendee = EventAttendee()
            attendee.event_id = event_id
            attendee.user_id = user_id
            attendee.tenant_id = tenant_id
            attendee.rsvp_status = kwargs.get('rsvp_status', 'invited')
            attendee.role = kwargs.get('role', 'attendee')
            attendee.invited_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.invited_by_user_id = invited_by_user_id
            attendee.created_by_id = invited_by_user_id

            # Optional fields
            if 'registration_data' in kwargs:
                attendee.registration_data = kwargs['registration_data']
            if 'registration_notes' in kwargs:
                attendee.registration_notes = kwargs['registration_notes']
            if 'notification_preferences' in kwargs:
                attendee.notification_preferences = kwargs['notification_preferences']

            attendee.prep_for_save()
            return self._save_model(attendee)

        except Exception as e:
            return self._handle_service_exception(e, 'invite_attendee', event_id=event_id, user_id=user_id)

    def update_rsvp(self, event_id: str, user_id: str, tenant_id: str,
                    rsvp_status: str, **kwargs) -> ServiceResult[EventAttendee]:
        """
        Update RSVP status for an attendee.
        
        Args:
            event_id: Event ID
            user_id: User ID
            tenant_id: Tenant ID
            rsvp_status: New RSVP status (accepted, declined, tentative)
            **kwargs: Additional fields (plus_one_count, etc.)
        """
        try:
            # Validate status
            if rsvp_status not in ['accepted', 'declined', 'tentative', 'waitlist']:
                raise ValidationError(f"Invalid RSVP status: {rsvp_status}")

            # Get existing attendee
            result = self.get_attendee(event_id, user_id, tenant_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found for event {event_id}")

            attendee = result.data
            old_status = attendee.rsvp_status

            # Update status
            attendee.rsvp_status = rsvp_status
            attendee.responded_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.updated_by_id = user_id

            # Update optional fields
            if 'plus_one_count' in kwargs:
                attendee.plus_one_count = kwargs['plus_one_count']
            if 'plus_one_names' in kwargs:
                attendee.plus_one_names = kwargs['plus_one_names']
            if 'registration_data' in kwargs:
                attendee.registration_data = kwargs['registration_data']
            if 'registration_notes' in kwargs:
                attendee.registration_notes = kwargs['registration_notes']

            attendee.prep_for_save()
            return self._save_model(attendee)

        except Exception as e:
            return self._handle_service_exception(e, 'update_rsvp', event_id=event_id, user_id=user_id)

    def add_host(self, event_id: str, user_id: str, tenant_id: str,
                 added_by_user_id: str, role: str = 'co_host') -> ServiceResult[EventAttendee]:
        """
        Add a host/co-organizer to an event.
        
        Args:
            event_id: Event ID
            user_id: User ID to make host
            tenant_id: Tenant ID
            added_by_user_id: Who is adding them
            role: 'organizer' or 'co_host'
        """
        try:
            if role not in ['organizer', 'co_host']:
                raise ValidationError(f"Invalid host role: {role}")

            # Check if already attendee
            result = self.get_attendee(event_id, user_id, tenant_id)
            
            if result.success:
                # Update existing attendee to host role
                attendee = result.data
                attendee.role = role
                attendee.rsvp_status = 'accepted'  # Hosts are auto-accepted
                attendee.updated_by_id = added_by_user_id
                attendee.prep_for_save()
                return self._save_model(attendee)
            else:
                # Create new host attendee
                return self.invite(
                    event_id=event_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    invited_by_user_id=added_by_user_id,
                    role=role,
                    rsvp_status='accepted'
                )

        except Exception as e:
            return self._handle_service_exception(e, 'add_host', event_id=event_id, user_id=user_id)

    def get_attendee(self, event_id: str, user_id: str, tenant_id: str, 
                    include_deleted: bool = False) -> ServiceResult[EventAttendee]:
        """Get a specific attendee record.
        
        Args:
            event_id: Event ID
            user_id: User ID
            tenant_id: Tenant ID
            include_deleted: If True, return deleted attendees as well
        """
        try:
            # Use GSI1 to query by event, then filter by user_id
            # This is more efficient than scanning
            temp = EventAttendee()
            temp.event_id = event_id
            
            # Query by event using GSI1
            result = self._query_by_index(
                model=temp,
                index_name="gsi1",
                limit=100  # Should be small number per event
            )
            
            if not result.success:
                return result
            
            # Find the specific user's attendee record
            for attendee in result.data:
                if attendee.user_id == user_id and attendee.tenant_id == tenant_id:
                    # Return even if deleted if include_deleted is True
                    if not include_deleted and attendee.is_deleted():
                        return ServiceResult.error_result(f"Attendee not found", "NOT_FOUND")
                    return ServiceResult.success_result(attendee)
            
            return ServiceResult.error_result(f"Attendee not found", "NOT_FOUND")

        except Exception as e:
            return self._handle_service_exception(e, 'get_attendee', event_id=event_id, user_id=user_id)

    def list_by_event(self, event_id: str, tenant_id: str, 
                      rsvp_status: str = None, role: str = None,
                      limit: int = 100) -> ServiceResult[List[EventAttendee]]:
        """
        List all attendees for an event.
        
        Args:
            event_id: Event ID
            tenant_id: Tenant ID
            rsvp_status: Optional filter by RSVP status
            role: Optional filter by role
            limit: Max results
        """
        try:
            temp = EventAttendee()
            temp.event_id = event_id
            # Leave role and rsvp_status as None to query across all values
            # (model defaults are now None, so GSI keys won't include them)
            if role:
                temp.role = role
            if rsvp_status:
                temp.rsvp_status = rsvp_status

            # Use helper method for query
            result = self._query_by_index(
                model=temp,
                index_name="gsi1",
                ascending=False,
                limit=limit
            )

            if not result.success:
                return result

            # Post-query filtering
            valid_attendees = []
            for attendee in result.data:
                # Tenant isolation and deleted check
                if attendee.tenant_id != tenant_id or attendee.is_deleted():
                    continue
                
                # Filter by RSVP status if specified (post-query for flexibility)
                if rsvp_status and attendee.rsvp_status != rsvp_status:
                    continue
                
                # Filter by role if specified (post-query for flexibility)
                if role and attendee.role != role:
                    continue
                
                valid_attendees.append(attendee)

            return ServiceResult.success_result(valid_attendees)

        except Exception as e:
            return self._handle_service_exception(e, 'list_by_event', event_id=event_id)

    def list_user_events(self, user_id: str, tenant_id: str,
                        rsvp_status: str = None, upcoming_only: bool = True,
                        limit: int = 50) -> ServiceResult[List[EventAttendee]]:
        """
        List events a user is attending/invited to.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            rsvp_status: Optional filter by RSVP status
            upcoming_only: Only future events
            limit: Max results
        """
        try:
            temp = EventAttendee()
            temp.user_id = user_id
            # Leave rsvp_status as None to query across all values
            if rsvp_status:
                temp.rsvp_status = rsvp_status

            # Use helper method for query
            result = self._query_by_index(
                model=temp,
                index_name="gsi2",
                ascending=False,
                limit=limit
            )

            if not result.success:
                return result

            # Post-query filtering
            valid_attendees = []
            for attendee in result.data:
                # Tenant isolation and deleted check
                if attendee.tenant_id != tenant_id or attendee.is_deleted():
                    continue
                
                # Filter by RSVP status if specified
                if rsvp_status and attendee.rsvp_status != rsvp_status:
                    continue
                
                valid_attendees.append(attendee)

            return ServiceResult.success_result(valid_attendees)

        except Exception as e:
            return self._handle_service_exception(e, 'list_user_events', user_id=user_id)

    def list_hosts(self, event_id: str, tenant_id: str, limit: int = 20) -> ServiceResult[List[EventAttendee]]:
        """
        List all hosts (organizers and co-hosts) for an event.
        
        Args:
            event_id: Event ID
            tenant_id: Tenant ID
            limit: Max results
        """
        try:
            # Get organizers
            organizers = self.list_by_event(event_id, tenant_id, role="organizer", limit=limit)
            
            # Get co-hosts
            co_hosts = self.list_by_event(event_id, tenant_id, role="co_host", limit=limit)

            # Combine
            all_hosts = []
            if organizers.success:
                all_hosts.extend(organizers.data)
            if co_hosts.success:
                all_hosts.extend(co_hosts.data)

            return ServiceResult.success_result(all_hosts)

        except Exception as e:
            return self._handle_service_exception(e, 'list_hosts', event_id=event_id)

    def get_attendee_count(self, event_id: str, tenant_id: str,
                          rsvp_status: str = 'accepted') -> ServiceResult[int]:
        """
        Get count of attendees by RSVP status.
        
        Args:
            event_id: Event ID
            tenant_id: Tenant ID
            rsvp_status: RSVP status to count
        """
        try:
            result = self.list_by_event(event_id, tenant_id, rsvp_status=rsvp_status, limit=1000)
            if not result.success:
                return ServiceResult.error_result("Failed to count attendees", "COUNT_FAILED")

            count = len(result.data)
            
            # Add up +1 guests for accepted
            if rsvp_status == 'accepted':
                total_count = sum(a.total_attendee_count() for a in result.data)
                return ServiceResult.success_result(total_count)

            return ServiceResult.success_result(count)

        except Exception as e:
            return self._handle_service_exception(e, 'get_attendee_count', event_id=event_id)

    def check_in(self, event_id: str, user_id: str, tenant_id: str,
                 checked_in_by_user_id: str) -> ServiceResult[EventAttendee]:
        """
        Check in an attendee at the event.
        
        Args:
            event_id: Event ID
            user_id: Attendee user ID
            tenant_id: Tenant ID
            checked_in_by_user_id: Who is checking them in
        """
        try:
            # Get attendee
            result = self.get_attendee(event_id, user_id, tenant_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found")

            attendee = result.data

            # Must be accepted to check in
            if not attendee.has_accepted():
                raise ValidationError("Only accepted attendees can check in")

            # Already checked in?
            if attendee.checked_in:
                return ServiceResult.error_result("Attendee already checked in", "ALREADY_CHECKED_IN")

            # Check in
            attendee.checked_in = True
            attendee.checked_in_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.checked_in_by_user_id = checked_in_by_user_id
            attendee.updated_by_id = checked_in_by_user_id

            attendee.prep_for_save()
            return self._save_model(attendee)

        except Exception as e:
            return self._handle_service_exception(e, 'check_in', event_id=event_id, user_id=user_id)

    def promote_from_waitlist(self, event_id: str, user_id: str, tenant_id: str,
                              promoted_by_user_id: str) -> ServiceResult[EventAttendee]:
        """
        Promote an attendee from waitlist to accepted.
        
        Args:
            event_id: Event ID
            user_id: User ID on waitlist
            tenant_id: Tenant ID
            promoted_by_user_id: Who is promoting them
        """
        try:
            # Get attendee
            result = self.get_attendee(event_id, user_id, tenant_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found")

            attendee = result.data

            # Must be on waitlist
            if not attendee.is_on_waitlist():
                raise ValidationError("Attendee is not on waitlist")

            # Promote to accepted
            attendee.rsvp_status = 'accepted'
            attendee.responded_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.updated_by_id = promoted_by_user_id

            attendee.prep_for_save()
            return self._save_model(attendee)

        except Exception as e:
            return self._handle_service_exception(e, 'promote_from_waitlist', event_id=event_id, user_id=user_id)

    def remove_attendee(self, event_id: str, user_id: str, tenant_id: str,
                       removed_by_user_id: str) -> ServiceResult[bool]:
        """
        Remove an attendee from an event (soft delete).
        
        Args:
            event_id: Event ID
            user_id: User ID to remove
            tenant_id: Tenant ID
            removed_by_user_id: Who is removing them
        """
        try:
            # Get attendee
            result = self.get_attendee(event_id, user_id, tenant_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found")

            attendee = result.data

            # Soft delete
            attendee.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.deleted_by_id = removed_by_user_id
            attendee.updated_by_id = removed_by_user_id

            attendee.prep_for_save()
            save_result = self._save_model(attendee)
            
            return ServiceResult.success_result(save_result.success)

        except Exception as e:
            return self._handle_service_exception(e, 'remove_attendee', event_id=event_id, user_id=user_id)

    def bulk_invite(self, event_id: str, user_ids: List[str], tenant_id: str,
                   invited_by_user_id: str, **kwargs) -> ServiceResult[Dict[str, Any]]:
        """
        Invite multiple users to an event.
        
        Args:
            event_id: Event ID
            user_ids: List of user IDs to invite
            tenant_id: Tenant ID
            invited_by_user_id: Who is inviting
            **kwargs: Additional fields applied to all invites
            
        Returns:
            Dict with 'invited_count', 'failed_count', 'successful', and 'failed' lists
        """
        try:
            successful = []
            failed = []

            for user_id in user_ids:
                result = self.invite(
                    event_id=event_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    invited_by_user_id=invited_by_user_id,
                    **kwargs
                )

                if result.success:
                    successful.append({
                        'user_id': user_id,
                        'id': result.data.id
                    })
                else:
                    failed.append({
                        'user_id': user_id,
                        'error': result.error_message
                    })

            results = {
                'invited_count': len(successful),
                'failed_count': len(failed),
                'successful': successful,
                'failed': failed
            }

            return ServiceResult.success_result(results)

        except Exception as e:
            return self._handle_service_exception(e, 'bulk_invite', event_id=event_id)
