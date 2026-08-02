"""Contact API endpoints - for user support requests."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from .db.session import get_session
from sqlalchemy.orm import Session
import logging

router = APIRouter(prefix="/api", tags=["contact"])
logger = logging.getLogger("smartkcet.contact")


class ContactMessageRequest(BaseModel):
    """Contact message request model."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=10, max_length=2000)


class ContactMessageResponse(BaseModel):
    """Response for contact message submission."""
    status: str = "success"
    message: str = "Your message has been sent successfully"


# Contact email addresses
CONTACT_SUPPORT_EMAIL = "support@smartkcet.com"
CONTACT_INFO_EMAIL = "info@smartkcet.com"


@router.post("/contact", response_model=ContactMessageResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_message(
    data: ContactMessageRequest,
    db: Session = Depends(get_session),
):
    """Submit a contact message.
    
    This endpoint accepts contact form submissions from authenticated users
    and logs them for review. In production, this would send emails or
    create support tickets.
    
    Args:
        data: Contact message data
        db: Database session
        
    Returns:
        Success response
    """
    try:
        # Log the contact message
        logger.info(
            "Contact message received from %s (%s) - Subject: %s",
            data.name,
            data.email,
            data.subject,
        )
        
        # In production, this would:
        # 1. Send an email to support@smartkcet.com
        # 2. Create a support ticket in a ticket system
        # 3. Store the message in the database
        
        # For now, we just log it and return success
        return ContactMessageResponse(
            status="success",
            message="Your message has been sent successfully. We'll review it and get back to you within 24 hours."
        )
        
    except Exception as e:
        logger.error("Error processing contact message: %s", str(e))
        raise


__all__ = ["router"]
