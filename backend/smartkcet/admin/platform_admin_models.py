"""Pydantic models for Platform Admin API.

This module defines request and response schemas for Platform Admin endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# -----------------------------------------------------------------------------
# Admin Authentication
# -----------------------------------------------------------------------------


class AdminLoginRequest(BaseModel):
    """Request model for admin login."""
    
    email: str = Field(..., description="Admin email")
    password: str = Field(..., description="Admin password")


class AdminLoginResponse(BaseModel):
    """Response model for admin login."""
    
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Login result message")
    admin_configured: bool = Field(..., description="Whether admin is configured")


# -----------------------------------------------------------------------------
# Subscription Plan CRUD
# -----------------------------------------------------------------------------


class CreateSubscriptionPlanRequest(BaseModel):
    """Request model for creating a subscription plan."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Plan name")
    plan_type: str = Field(..., description="Plan type: 'individual' or 'institution'")
    billing_period: str = Field(..., description="Billing period: 'weekly' or 'monthly'")
    price: Decimal = Field(..., ge=0, description="Plan price")
    max_test_attempts_per_period: Optional[int] = Field(
        None, ge=1, description="Max test attempts per period (None = unlimited)"
    )
    max_student_seats: Optional[int] = Field(
        None, ge=1, description="Max student seats (required for institution plans)"
    )
    feature_flags: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional feature flags"
    )
    
    @field_validator("plan_type")
    @classmethod
    def validate_plan_type(cls, v: str) -> str:
        if v not in ["individual", "institution"]:
            raise ValueError("plan_type must be 'individual' or 'institution'")
        return v
    
    @field_validator("billing_period")
    @classmethod
    def validate_billing_period(cls, v: str) -> str:
        if v not in ["weekly", "monthly"]:
            raise ValueError("billing_period must be 'weekly' or 'monthly'")
        return v


class UpdateSubscriptionPlanRequest(BaseModel):
    """Request model for updating a subscription plan."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Plan name")
    price: Optional[Decimal] = Field(None, ge=0, description="Plan price")
    max_test_attempts_per_period: Optional[int] = Field(
        None, ge=1, description="Max test attempts per period"
    )
    max_student_seats: Optional[int] = Field(
        None, ge=1, description="Max student seats"
    )
    feature_flags: Optional[Dict[str, Any]] = Field(None, description="Feature flags")
    is_active: Optional[bool] = Field(None, description="Active status")


class SubscriptionPlanResponse(BaseModel):
    """Response model for subscription plan."""
    
    id: UUID
    name: str
    plan_type: str
    billing_period: str
    price: Decimal
    max_test_attempts_per_period: Optional[int]
    max_student_seats: Optional[int]
    feature_flags: Dict[str, Any]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Institution Management
# -----------------------------------------------------------------------------


class InstitutionResponse(BaseModel):
    """Response model for institution."""
    
    id: UUID
    name: str
    institution_code: Optional[str] = None
    contact_phone: str
    subscription_status: str
    registered_at: Optional[datetime] = None
    student_count: int = 0
    question_count: int = 0
    exam_count: int = 0
    plan_name: Optional[str] = None
    next_renewal_date: Optional[str] = None
    
    class Config:
        from_attributes = True


class InstitutionListResponse(BaseModel):
    """Response model for institution list."""
    
    institutions: List[InstitutionResponse]
    total: int


# -----------------------------------------------------------------------------
# Analytics
# -----------------------------------------------------------------------------


class ActiveUsersAnalytics(BaseModel):
    """Analytics for active users."""
    
    total_users: int
    platform_admins: int
    institution_admins: int
    total_students: int
    active_subscribers: int
    direct_subscribers: int
    institution_linked: int
    dual_subscribers: int


class SubscriptionDistributionAnalytics(BaseModel):
    """Analytics for subscription distribution."""
    
    by_status: Dict[str, int]
    individual_subscriptions: int
    institution_subscriptions: int
    by_plan: Dict[str, int]


class ExamAttemptsAnalytics(BaseModel):
    """Analytics for exam attempts."""
    
    total_attempts: int
    by_subject: Dict[str, int]
    avg_attempts_per_user: float
    trial_attempts: int
    pro_attempts: int


class RevenueAnalytics(BaseModel):
    """Analytics for revenue."""
    
    total_revenue: str
    by_plan: Dict[str, str]
    pending_revenue: str
    failed_revenue: str


class AggregateAnalyticsResponse(BaseModel):
    """Response model for aggregate analytics."""
    
    active_users: ActiveUsersAnalytics
    subscription_distribution: SubscriptionDistributionAnalytics
    exam_attempts: ExamAttemptsAnalytics
    revenue: RevenueAnalytics
    generated_at: str


# -----------------------------------------------------------------------------
# Generic Responses
# -----------------------------------------------------------------------------


class SuccessResponse(BaseModel):
    """Generic success response."""
    
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Generic error response."""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


__all__ = [
    "AdminLoginRequest",
    "AdminLoginResponse",
    "CreateSubscriptionPlanRequest",
    "UpdateSubscriptionPlanRequest",
    "SubscriptionPlanResponse",
    "InstitutionResponse",
    "InstitutionListResponse",
    "ActiveUsersAnalytics",
    "SubscriptionDistributionAnalytics",
    "ExamAttemptsAnalytics",
    "RevenueAnalytics",
    "AggregateAnalyticsResponse",
    "SuccessResponse",
    "ErrorResponse",
]
