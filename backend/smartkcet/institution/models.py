"""Pydantic schemas for institution service API request/response.

This module defines the data transfer objects (DTOs) used by the institution
service for API interactions, validation, and serialization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class InstitutionRegistrationData(BaseModel):
    """Request schema for institution registration.
    
    **Requirements:** 6.1, 6.2, 6.8
    
    Validation rules:
    - name: 1-100 characters
    - admin_email: RFC 5322 format, max 254 characters
    - admin_password: 8-72 characters with at least one digit
    - contact_phone: 10-15 digits (including country code)
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Institution name (1-100 characters)",
    )
    admin_email: str = Field(
        ...,
        max_length=254,
        description="Admin email address (RFC 5322 format, max 254 characters)",
    )
    admin_password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Admin password (8-72 characters with at least one digit)",
    )
    contact_phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Institution contact phone number (10-15 digits including country code)",
    )

    @field_validator("contact_phone")
    @classmethod
    def validate_phone_digits(cls, v: str) -> str:
        """Ensure phone number contains only digits."""
        if not v.isdigit():
            raise ValueError("contact_phone must contain only digits")
        return v

    @field_validator("admin_password")
    @classmethod
    def validate_password_has_digit(cls, v: str) -> str:
        """Ensure password contains at least one digit."""
        if not any(ch.isdigit() for ch in v):
            raise ValueError("admin_password must contain at least one digit")
        return v


class InvitationCreate(BaseModel):
    """Request schema for creating an institution invitation."""

    # No additional fields needed - institution_id comes from auth context
    pass


class InvitationAccept(BaseModel):
    """Request schema for accepting an institution invitation."""

    code: str = Field(
        ...,
        min_length=32,
        description="Invitation code (minimum 32 alphanumeric characters)",
    )


class StudentRemove(BaseModel):
    """Request schema for removing a student from an institution."""

    student_id: UUID = Field(
        ...,
        description="Student user ID to remove from the institution",
    )


class InstitutionPlanSelect(BaseModel):
    """Request schema for selecting an institution subscription plan."""

    plan_id: UUID = Field(
        ...,
        description="Subscription plan ID to activate",
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class InstitutionResponse(BaseModel):
    """Response schema for institution details."""

    id: UUID
    name: str
    contact_phone: str
    subscription_status: str
    registered_at: datetime

    class Config:
        from_attributes = True


class InstitutionRegistrationResponse(BaseModel):
    """Response schema for successful institution registration.
    
    **Requirements:** 6.1
    """

    institution_id: UUID = Field(
        ...,
        description="Generated institution identifier",
    )
    admin_user_id: UUID = Field(
        ...,
        description="Generated institution admin user identifier",
    )
    institution_name: str
    admin_email: str
    registered_at: datetime


class InvitationCodeResponse(BaseModel):
    """Response schema for generated invitation code."""

    id: UUID
    code: str = Field(
        ...,
        description="Invitation code (minimum 32 alphanumeric characters)",
    )
    institution_id: UUID
    status: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class StudentSummary(BaseModel):
    """Summary information for a student linked to an institution."""

    user_id: UUID
    email: str
    display_name: str
    kcet_student_id: Optional[str] = None
    linked_at: datetime
    student_subtype: str

    class Config:
        from_attributes = True


class InstitutionStudentsResponse(BaseModel):
    """Response schema for listing institution students."""

    institution_id: UUID
    institution_name: str
    total_students: int
    max_seats: Optional[int] = None
    students: list[StudentSummary]


__all__ = [
    "InstitutionRegistrationData",
    "InstitutionRegistrationResponse",
    "InstitutionResponse",
    "InvitationAccept",
    "InvitationCodeResponse",
    "InvitationCreate",
    "InstitutionStudentsResponse",
    "InstitutionPlanSelect",
    "StudentRemove",
    "StudentSummary",
]
