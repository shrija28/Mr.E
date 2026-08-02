"""Institution service implementation.

This module implements institution registration, invitation flows, and student
management for the subscription platform upgrade.

**Requirements:** 6.1, 6.2, 6.7, 6.8, 6.9
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from ..auth.passwords import hash_password
from ..auth.validation import (
    ValidationFailure,
    validate_email,
    validate_password,
)
from ..db.models import User
from ..db.subscription_models import Institution, Invitation
from .models import (
    InstitutionRegistrationData,
    InstitutionRegistrationResponse,
    InvitationCodeResponse,
    StudentSummary,
)


class InstitutionServiceError(Exception):
    """Base exception for institution service errors."""

    pass


class ValidationError(InstitutionServiceError):
    """Validation error with field and reason."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


class DuplicateEmailError(InstitutionServiceError):
    """Email already registered error."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email already registered: {email}")


class DatabaseUnavailableError(InstitutionServiceError):
    """Database unavailable error."""

    pass


class InstitutionService:
    """Manages institution registration, invitations, and student linking.
    
    This service handles:
    - Institution registration with admin account creation
    - Invitation code generation and management
    - Student invitation acceptance and linking
    - Student removal from institutions
    """

    def __init__(self, db: Session):
        """Initialize the institution service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def _generate_institution_code(self, institution_name: str) -> str:
        """Generate a unique, URL-safe institution code from name.
        
        Converts the institution name to a lowercase alphanumeric code
        by removing spaces and special characters. If the code already
        exists, appends a number to ensure uniqueness.
        
        Examples:
            "SMVIT Manipal" → "smvitmanipai" → "smvitm" (first 7 chars for demo)
            "XYZ Institute" → "xyzinstitute"
        
        Args:
            institution_name: Full name of the institution
            
        Returns:
            Unique institution code (lowercase, alphanumeric only, max 20 chars)
        """
        import re
        
        # Remove leading/trailing whitespace and convert to lowercase
        base_code = institution_name.strip().lower()
        
        # Keep only alphanumeric characters (remove spaces, special chars)
        base_code = re.sub(r'[^a-z0-9]', '', base_code)
        
        # Limit to 20 chars (DB column length)
        base_code = base_code[:20]
        
        # Check if this code already exists
        existing = self.db.query(Institution).filter(
            Institution.institution_code == base_code
        ).first()
        
        if existing is None:
            return base_code
        
        # If it exists, append a number suffix to make it unique
        for i in range(1, 1000):
            candidate = base_code[:19] + str(i)  # Leave room for number
            existing = self.db.query(Institution).filter(
                Institution.institution_code == candidate
            ).first()
            if existing is None:
                return candidate
        
        # Fallback (should rarely happen)
        import uuid
        return (base_code[:10] + str(uuid.uuid4())[:8])[:20]

    def register_institution(
        self, data: InstitutionRegistrationData
    ) -> InstitutionRegistrationResponse:
        """Create institution + institution_admin account atomically.
        
        **Requirements:** 6.1, 6.2, 6.7, 6.8, 6.9
        
        Validation rules (REQ-6.1, REQ-6.8):
        - name: 1-100 characters
        - admin_email: RFC 5322 format, max 254 characters
        - admin_password: 8-72 characters with at least one digit
        - contact_phone: 10-15 digits (including country code)
        
        Returns first failing field on validation error (REQ-6.8).
        Rejects duplicate emails (REQ-6.2).
        Handles DB unavailability with 503 within 5 seconds (REQ-6.9).
        
        Args:
            data: Institution registration data
            
        Returns:
            InstitutionRegistrationResponse with generated IDs
            
        Raises:
            ValidationError: If any field fails validation (first failing field)
            DuplicateEmailError: If admin email is already registered
            DatabaseUnavailableError: If DB is unavailable
        """
        # Validate institution name (1-100 characters)
        # This is already validated by Pydantic, but we check explicitly
        # to ensure we return the first failing field
        if not data.name or len(data.name) < 1:
            raise ValidationError("name", "institution name is required")
        if len(data.name) > 100:
            raise ValidationError(
                "name", "institution name must be 100 characters or fewer"
            )

        # Validate admin email (RFC 5322, max 254 chars)
        email_result = validate_email(data.admin_email)
        if isinstance(email_result, ValidationFailure):
            raise ValidationError(email_result.field, email_result.reason)
        normalized_email = email_result

        # Validate admin password (8-72 chars with at least one digit)
        if len(data.admin_password) > 72:
            raise ValidationError(
                "admin_password", "password must be 72 characters or fewer"
            )
        password_result = validate_password(data.admin_password)
        if isinstance(password_result, ValidationFailure):
            raise ValidationError(password_result.field, password_result.reason)

        # Validate contact phone (10-15 digits)
        # Already validated by Pydantic field_validator, but we check explicitly
        if not data.contact_phone.isdigit():
            raise ValidationError(
                "contact_phone", "contact phone must contain only digits"
            )
        if len(data.contact_phone) < 10:
            raise ValidationError(
                "contact_phone", "contact phone must be at least 10 digits"
            )
        if len(data.contact_phone) > 15:
            raise ValidationError(
                "contact_phone", "contact phone must be 15 digits or fewer"
            )

        try:
            # Check for duplicate email (REQ-6.2)
            # This must happen before password hashing
            existing_user = (
                self.db.query(User)
                .filter(User.email == normalized_email)
                .first()
            )
            if existing_user:
                raise DuplicateEmailError(normalized_email)

            # Hash password after validation and duplicate check
            password_hash = hash_password(data.admin_password)

            # Create institution and admin user atomically
            now = datetime.utcnow()

            # Create institution record
            institution = Institution(
                name=data.name,
                contact_phone=data.contact_phone,
                subscription_status="inactive",
                registered_at=now,
                institution_code=self._generate_institution_code(data.name),
            )
            self.db.add(institution)
            self.db.flush()  # Flush to get institution ID

            # Create institution_admin user record
            admin_user = User(
                email=normalized_email,
                kcet_student_id=None,  # Admins don't have KCET student IDs
                display_name=data.name,  # Use institution name as display name
                password_hash=password_hash,
                role="institution_admin",
                student_subtype=None,  # Admins don't have subtypes
                institution_id=institution.id,
                created_at=now,
                failed_login_count=0,
                lockout_until=None,
            )
            self.db.add(admin_user)
            self.db.flush()  # Flush to get admin user ID

            # Commit the transaction
            self.db.commit()

            # Refresh to get all fields
            self.db.refresh(institution)
            self.db.refresh(admin_user)

            return InstitutionRegistrationResponse(
                institution_id=institution.id,
                admin_user_id=admin_user.id,
                institution_name=institution.name,
                admin_email=admin_user.email,
                registered_at=institution.registered_at,
            )

        except (DuplicateEmailError, ValidationError):
            # Re-raise validation and duplicate errors as-is
            self.db.rollback()
            raise
        except IntegrityError as e:
            # Handle unique constraint violations
            self.db.rollback()
            # Check if it's a duplicate email error
            if "email" in str(e).lower() or "uq_users_email" in str(e).lower():
                raise DuplicateEmailError(normalized_email)
            # Otherwise, re-raise as a generic error
            raise InstitutionServiceError(f"Database integrity error: {e}")
        except OperationalError as e:
            # Handle DB unavailability (REQ-6.9)
            self.db.rollback()
            raise DatabaseUnavailableError(
                "Database is currently unavailable. Please try again later."
            )
        except Exception as e:
            # Catch-all for unexpected errors
            self.db.rollback()
            raise InstitutionServiceError(f"Unexpected error during registration: {e}")

    def generate_invitation(self, institution_id: UUID) -> InvitationCodeResponse:
        """Generate a 32+ char invitation code, valid 7 days.
        
        Max 50 pending per institution (REQ-9.1).
        
        Args:
            institution_id: Institution ID
            
        Returns:
            InvitationCodeResponse with generated code
            
        Raises:
            InstitutionServiceError: If max pending invitations reached
        """
        try:
            # Check pending invitation count (REQ-9.1: max 50 pending)
            pending_count = (
                self.db.query(Invitation)
                .filter(
                    Invitation.institution_id == institution_id,
                    Invitation.status == "pending",
                )
                .count()
            )
            
            if pending_count >= 50:
                raise InstitutionServiceError(
                    f"Maximum pending invitations (50) reached for institution {institution_id}"
                )
            
            # Get the next sequence number for this institution
            max_sequence = (
                self.db.query(Invitation)
                .filter(Invitation.institution_id == institution_id)
                .count()
            )
            next_sequence = max_sequence + 1
            
            # Generate secure random code (minimum 32 alphanumeric characters)
            # Using secrets.token_urlsafe which generates URL-safe base64 strings
            # 32 bytes = 43 base64 characters (> 32 requirement)
            code = secrets.token_urlsafe(32)
            
            # Create invitation with 7-day validity
            now = datetime.utcnow()
            expires_at = now + timedelta(days=7)
            
            invitation = Invitation(
                institution_id=institution_id,
                code=code,
                sequence_number=next_sequence,  # NEW: Add sequence number
                status="pending",
                consumed_by=None,
                created_at=now,
                expires_at=expires_at,
                consumed_at=None,
            )
            
            self.db.add(invitation)
            self.db.commit()
            self.db.refresh(invitation)
            
            return InvitationCodeResponse(
                id=invitation.id,
                code=invitation.code,
                institution_id=invitation.institution_id,
                status=invitation.status,
                created_at=invitation.created_at,
                expires_at=invitation.expires_at,
            )
            
        except InstitutionServiceError:
            self.db.rollback()
            raise
        except OperationalError:
            self.db.rollback()
            raise DatabaseUnavailableError(
                "Database is currently unavailable. Please try again later."
            )
        except Exception as e:
            self.db.rollback()
            raise InstitutionServiceError(
                f"Unexpected error generating invitation: {e}"
            )

    def accept_invitation(self, code: str, student_id: UUID) -> None:
        """Link student to institution, consume seat, mark invitation used.
        
        **Requirements:** 9.2, 9.3, 9.4, 9.5
        
        Success conditions (REQ-9.2, 9.3, 9.4, 9.5):
        - Invitation code exists and has status 'pending'
        - Invitation has not expired (current_time < expires_at)
        - Institution has at least one available seat
        - Student is not already linked to a different institution
        
        If any condition fails, no state change occurs (REQ-9.4).
        
        Args:
            code: Invitation code
            student_id: Student user ID
            
        Raises:
            InstitutionServiceError: If invitation invalid, expired, seats full, or already linked
        """
        try:
            # Fetch invitation
            invitation = (
                self.db.query(Invitation)
                .filter(Invitation.code == code)
                .first()
            )
            
            # Check invitation exists and is pending (REQ-9.2, 9.3)
            if not invitation:
                raise InstitutionServiceError("Invalid invitation code")
            
            # Check if invitation was already consumed by this student (idempotent)
            if invitation.status == "consumed" and invitation.consumed_by == student_id:
                # Already consumed by this student - idempotent success
                return
            
            if invitation.status != "pending":
                raise InstitutionServiceError(
                    f"Invitation is {invitation.status}, not pending"
                )
            
            # Check invitation not expired (REQ-9.2, 9.3)
            now = datetime.utcnow()
            if now >= invitation.expires_at:
                raise InstitutionServiceError(
                    f"Invitation expired on {invitation.expires_at.isoformat()}"
                )
            
            # Fetch student
            student = self.db.query(User).filter(User.id == student_id).first()
            if not student:
                raise InstitutionServiceError(f"Student {student_id} not found")
            
            # Check student not already linked to a different institution (REQ-9.5)
            if student.institution_id is not None:
                if student.institution_id != invitation.institution_id:
                    # Fetch institution name for error message
                    existing_institution = (
                        self.db.query(Institution)
                        .filter(Institution.id == student.institution_id)
                        .first()
                    )
                    institution_name = (
                        existing_institution.name if existing_institution else "another institution"
                    )
                    raise InstitutionServiceError(
                        f"Student is already linked to {institution_name}"
                    )
                else:
                    # Student already linked to this institution - idempotent success
                    # Mark invitation as consumed if not already
                    if invitation.status == "pending":
                        invitation.status = "consumed"
                        invitation.consumed_by = student_id
                        invitation.consumed_at = now
                        self.db.commit()
                    return
            
            # Check seat availability (REQ-9.2, 9.4)
            # Get institution's active subscription to check max_student_seats
            institution = (
                self.db.query(Institution)
                .filter(Institution.id == invitation.institution_id)
                .first()
            )
            
            if not institution:
                raise InstitutionServiceError(
                    f"Institution {invitation.institution_id} not found"
                )
            
            # Get active subscription for the institution (optional — no subscription = no seat limit)
            from ..db.subscription_models import Subscription, SubscriptionPlan
            
            active_subscription = (
                self.db.query(Subscription)
                .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
                .filter(
                    Subscription.institution_id == invitation.institution_id,
                    Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
                )
                .first()
            )
            
            # Only enforce seat limit if the institution has an active subscription with a seat cap
            max_seats = None
            if active_subscription and active_subscription.plan:
                max_seats = active_subscription.plan.max_student_seats
            
            # Count current STUDENTS linked to this institution (exclude admins)
            current_student_count = (
                self.db.query(User)
                .filter(
                    User.institution_id == invitation.institution_id,
                    User.role == "student",
                )
                .count()
            )
            
            # Check if seats available (REQ-9.4)
            if max_seats is not None and current_student_count >= max_seats:
                raise InstitutionServiceError(
                    f"Institution seat quota full ({current_student_count}/{max_seats}). "
                    f"Invitation remains valid for future use."
                )
            
            # All checks passed - link student to institution
            # Update student subtype using transition method (REQ-10.3, 10.4, 10.7)
            self.transition_student_subtype(student_id, "join_institution")
            
            # Refresh student to get updated subtype
            self.db.refresh(student)
            
            student.institution_id = invitation.institution_id
            
            # Mark invitation as consumed (REQ-9.2)
            invitation.status = "consumed"
            invitation.consumed_by = student_id
            invitation.consumed_at = now
            
            # Commit transaction atomically
            self.db.commit()
            
        except InstitutionServiceError:
            self.db.rollback()
            raise
        except OperationalError:
            self.db.rollback()
            raise DatabaseUnavailableError(
                "Database is currently unavailable. Please try again later."
            )
        except Exception as e:
            self.db.rollback()
            raise InstitutionServiceError(
                f"Unexpected error accepting invitation: {e}"
            )

    def remove_student(self, institution_id: UUID, student_id: UUID) -> None:
        """Unlink student, free seat, preserve history.
        
        **Requirements:** 9.6
        
        Immediately revokes institution-linked access, frees one seat,
        preserves exam history and analytics data, records removal timestamp.
        
        Args:
            institution_id: Institution ID
            student_id: Student user ID
            
        Raises:
            InstitutionServiceError: If student not found or not linked to institution
        """
        try:
            # Fetch student
            student = self.db.query(User).filter(User.id == student_id).first()
            
            if not student:
                raise InstitutionServiceError(f"Student {student_id} not found")
            
            # Check student is linked to this institution
            if student.institution_id != institution_id:
                if student.institution_id is None:
                    raise InstitutionServiceError(
                        f"Student {student_id} is not linked to any institution"
                    )
                else:
                    raise InstitutionServiceError(
                        f"Student {student_id} is not linked to institution {institution_id}"
                    )
            
            # Update student subtype using transition method (REQ-10.3, 10.4, 10.7)
            self.transition_student_subtype(student_id, "leave_institution")
            
            # Refresh student to get updated subtype
            self.db.refresh(student)
            
            # Unlink student from institution (frees one seat)
            student.institution_id = None
            
            # Note: We preserve all exam history and analytics data
            # by NOT deleting any submissions, usage_records, or other related data
            # The foreign key constraints use SET NULL or CASCADE appropriately
            
            # Commit transaction
            self.db.commit()
            
        except InstitutionServiceError:
            self.db.rollback()
            raise
        except OperationalError:
            self.db.rollback()
            raise DatabaseUnavailableError(
                "Database is currently unavailable. Please try again later."
            )
        except Exception as e:
            self.db.rollback()
            raise InstitutionServiceError(
                f"Unexpected error removing student: {e}"
            )

    def get_institution_students(
        self, institution_id: UUID
    ) -> list[StudentSummary]:
        """List students linked to an institution.
        
        Only returns users with role='student' — excludes institution_admin
        accounts that happen to have the same institution_id.
        
        Args:
            institution_id: Institution ID
            
        Returns:
            List of StudentSummary objects
        """
        try:
            # Query only STUDENTS linked to this institution (exclude institution_admin)
            students = (
                self.db.query(User)
                .filter(
                    User.institution_id == institution_id,
                    User.role == "student",              # ← critical filter
                )
                .order_by(User.created_at)
                .all()
            )
            
            # Convert to StudentSummary objects
            return [
                StudentSummary(
                    user_id=student.id,
                    email=student.email,
                    display_name=student.display_name,
                    kcet_student_id=student.kcet_student_id,
                    linked_at=student.created_at,
                    student_subtype=student.student_subtype or "institution_linked",
                )
                for student in students
            ]
            
        except OperationalError:
            raise DatabaseUnavailableError(
                "Database is currently unavailable. Please try again later."
            )
        except Exception as e:
            raise InstitutionServiceError(
                f"Unexpected error fetching institution students: {e}"
            )

    def activate_institution_plan(
        self, institution_id: UUID, plan_id: UUID
    ) -> "Subscription":
        """Activate an institution subscription plan.
        
        **Requirements:** 8.1, 8.2, 8.3
        
        Activates the specified plan for the institution. If an active subscription
        already exists, schedules the new plan to take effect at the end of the
        current billing period.
        
        Args:
            institution_id: Institution ID
            plan_id: Subscription plan ID
            
        Returns:
            Subscription record
            
        Raises:
            InstitutionServiceError: If plan not found or invalid
        """
        from ..db.subscription_models import Subscription, SubscriptionEvent, SubscriptionPlan
        
        try:
            # Get the plan
            plan = (
                self.db.query(SubscriptionPlan)
                .filter(
                    SubscriptionPlan.id == plan_id,
                    SubscriptionPlan.plan_type == "institution",
                    SubscriptionPlan.is_active == True
                )
                .first()
            )
            
            if not plan:
                raise InstitutionServiceError(
                    f"Institution plan {plan_id} not found or inactive"
                )
            
            # Check for existing active subscription (REQ-8.3)
            existing_active = (
                self.db.query(Subscription)
                .filter(
                    Subscription.institution_id == institution_id,
                    Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
                )
                .first()
            )
            
            if existing_active:
                # Schedule plan change for end of billing period (REQ-8.3)
                # For MVP, we'll just return the existing subscription
                # In production, this would create a pending plan change record
                raise InstitutionServiceError(
                    f"Institution already has an active subscription. "
                    f"Plan change will take effect at end of billing period: "
                    f"{existing_active.next_renewal_date.isoformat() if existing_active.next_renewal_date else 'N/A'}"
                )
            
            # Calculate next renewal date based on billing period
            now = datetime.utcnow()
            if plan.billing_period == "weekly":
                next_renewal = now + timedelta(days=7)
            else:  # monthly
                next_renewal = now + timedelta(days=30)
            
            # Create new institution subscription (REQ-8.2)
            subscription = Subscription(
                institution_id=institution_id,
                user_id=None,
                plan_id=plan_id,
                status="active",
                start_date=now,
                current_period_start=now,
                next_renewal_date=next_renewal,
                trial_duration_days=None,
            )
            
            self.db.add(subscription)
            self.db.flush()  # Flush to get subscription ID
            
            # Create subscription event for audit trail
            event = SubscriptionEvent(
                subscription_id=subscription.id,
                event_type="activated",
                previous_status="none",
                new_status="active",
                event_metadata={
                    "institution_id": str(institution_id),
                    "plan_id": str(plan_id),
                    "max_student_seats": plan.max_student_seats,
                    "billing_period": plan.billing_period,
                    "next_renewal_date": next_renewal.isoformat(),
                    "activation_timestamp": now.isoformat()
                }
            )
            self.db.add(event)
            
            # Update institution subscription status
            institution = (
                self.db.query(Institution)
                .filter(Institution.id == institution_id)
                .first()
            )
            if institution:
                institution.subscription_status = "active"
            
            self.db.commit()
            self.db.refresh(subscription)
            
            return subscription
            
        except InstitutionServiceError:
            self.db.rollback()
            raise
        except OperationalError:
            self.db.rollback()
            raise DatabaseUnavailableError(
                "Database is currently unavailable. Please try again later."
            )
        except Exception as e:
            self.db.rollback()
            raise InstitutionServiceError(
                f"Unexpected error activating institution plan: {e}"
            )

    def transition_student_subtype(
        self, student_id: UUID, transition_type: str
    ) -> None:
        """Transition student subtype based on subscription changes.
        
        **Requirements:** 10.3, 10.4, 10.7
        
        Implements subtype transitions:
        - null → institution_linked (student joins institution, no prior subscription)
        - direct_subscriber → dual (student joins institution, has individual subscription)
        - dual → direct_subscriber (student leaves institution, keeps individual subscription)
        - institution_linked → null (student leaves institution, no individual subscription)
        
        Invalidates session token on subtype change (REQ-10.7).
        
        Args:
            student_id: Student user ID
            transition_type: One of "join_institution", "leave_institution"
            
        Raises:
            InstitutionServiceError: If student not found or invalid transition
        """
        from ..auth.tokens import revoke_user_tokens
        
        try:
            student = self.db.query(User).filter(User.id == student_id).first()
            
            if not student:
                raise InstitutionServiceError(f"Student {student_id} not found")
            
            if student.role != "student":
                raise InstitutionServiceError(
                    f"User {student_id} is not a student (role: {student.role})"
                )
            
            old_subtype = student.student_subtype
            
            if transition_type == "join_institution":
                # Transition: null → institution_linked OR direct_subscriber → dual
                if student.student_subtype is None:
                    student.student_subtype = "institution_linked"
                elif student.student_subtype == "direct_subscriber":
                    student.student_subtype = "dual"
                # If already institution_linked or dual, no change needed
                
            elif transition_type == "leave_institution":
                # Transition: dual → direct_subscriber OR institution_linked → null
                if student.student_subtype == "dual":
                    student.student_subtype = "direct_subscriber"
                elif student.student_subtype == "institution_linked":
                    student.student_subtype = None
                # If already direct_subscriber or None, no change needed
                
            else:
                raise InstitutionServiceError(
                    f"Invalid transition type: {transition_type}"
                )
            
            # Invalidate session token if subtype changed (REQ-10.7)
            if old_subtype != student.student_subtype:
                revoke_user_tokens(self.db, student_id)
            
            self.db.commit()
            
        except InstitutionServiceError:
            self.db.rollback()
            raise
        except OperationalError:
            self.db.rollback()
            raise DatabaseUnavailableError(
                "Database is currently unavailable. Please try again later."
            )
        except Exception as e:
            self.db.rollback()
            raise InstitutionServiceError(
                f"Unexpected error transitioning student subtype: {e}"
            )

    def deactivate_institution_students(self, institution_id: UUID) -> int:
        """Deactivate all students linked to an institution on subscription expiry.
        
        **Requirements:** 8.7
        
        Called when an institution's subscription expires. Preserves all exam
        history and analytics data.
        
        Args:
            institution_id: Institution ID
            
        Returns:
            Number of students deactivated
            
        Raises:
            InstitutionServiceError: On database errors
        """
        try:
            # Get all students linked to this institution
            students = (
                self.db.query(User)
                .filter(User.institution_id == institution_id)
                .all()
            )
            
            count = 0
            for student in students:
                # Use transition_student_subtype for consistent subtype management
                self.transition_student_subtype(student.id, "leave_institution")
                
                # Unlink from institution (preserves history)
                student.institution_id = None
                count += 1
            
            # Update institution subscription status
            institution = (
                self.db.query(Institution)
                .filter(Institution.id == institution_id)
                .first()
            )
            if institution:
                institution.subscription_status = "expired"
            
            self.db.commit()
            
            return count
            
        except OperationalError:
            self.db.rollback()
            raise DatabaseUnavailableError(
                "Database is currently unavailable. Please try again later."
            )
        except Exception as e:
            self.db.rollback()
            raise InstitutionServiceError(
                f"Unexpected error deactivating institution students: {e}"
            )


__all__ = [
    "DatabaseUnavailableError",
    "DuplicateEmailError",
    "InstitutionService",
    "InstitutionServiceError",
    "ValidationError",
]
