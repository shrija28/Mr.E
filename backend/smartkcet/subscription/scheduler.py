"""Subscription lifecycle scheduler.

This module implements the background task that processes subscription
lifecycle events such as renewals, grace periods, and expirations.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.subscription_models import Subscription, SubscriptionEvent, SubscriptionPlan

logger = logging.getLogger(__name__)

# Global reference to the scheduler task
_scheduler_task: Optional[asyncio.Task] = None


class SubscriptionScheduler:
    """Background scheduler for subscription lifecycle management.
    
    This scheduler runs periodically (default: every 60 minutes) to:
    - Process pending renewals
    - Transition subscriptions to grace period
    - Expire subscriptions past grace period
    - Clean up old subscription events
    """

    def __init__(self, db: Session):
        """Initialize the subscription scheduler.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    async def subscription_lifecycle_tick(self) -> dict:
        """Process all pending subscription state transitions.
        
        This method is called periodically by the scheduler to:
        1. Check for subscriptions past their renewal date
        2. Process renewals (extend or enter grace period)
        3. Expire subscriptions past grace period
        
        **Requirements:** 4.1, 4.2, 4.4, 4.10
        
        Returns:
            Dictionary with counts of processed subscriptions:
            {
                "renewed": int,
                "grace_period": int,
                "expired": int,
                "errors": int
            }
        """
        logger.info("Starting subscription lifecycle tick")
        
        results = {
            "renewed": 0,
            "grace_period": 0,
            "expired": 0,
            "errors": 0
        }
        
        try:
            # Process pending renewals (subscriptions past renewal date)
            grace_period_count = await self.process_pending_renewals()
            results["grace_period"] = grace_period_count
            
            # Expire subscriptions past grace period
            expired_count = await self.process_grace_period_expirations()
            results["expired"] = expired_count
            
            # Process cancellations (subscriptions marked for cancellation)
            cancelled_count = await self.process_pending_cancellations()
            results["cancelled"] = cancelled_count
            
            logger.info(
                f"Lifecycle tick completed: {grace_period_count} entered grace period, "
                f"{expired_count} expired, {cancelled_count} cancelled"
            )
            
        except Exception as e:
            logger.error(f"Error during lifecycle tick: {e}", exc_info=True)
            results["errors"] = 1
        
        return results

    async def process_pending_renewals(self) -> int:
        """Process subscriptions that have reached their renewal date.
        
        For subscriptions past their renewal date + 24 hours without payment,
        transition them to grace_period status.
        
        **Requirements:** 4.2
        
        Returns:
            Count of subscriptions transitioned to grace period
        """
        now = datetime.utcnow()
        grace_period_threshold = now - timedelta(hours=24)
        
        # Find active subscriptions past renewal date + 24h
        subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.next_renewal_date.isnot(None),
                Subscription.next_renewal_date <= grace_period_threshold
            )
            .all()
        )
        
        count = 0
        for subscription in subscriptions:
            try:
                # Transition to grace period (3 days from renewal date)
                grace_period_end = subscription.next_renewal_date + timedelta(days=3)
                previous_status = subscription.status
                
                subscription.status = "grace_period"
                subscription.grace_period_end = grace_period_end
                
                # Create grace period event
                event = SubscriptionEvent(
                    subscription_id=subscription.id,
                    event_type="grace_period",
                    previous_status=previous_status,
                    new_status="grace_period",
                    event_metadata={
                        "grace_period_end": grace_period_end.isoformat(),
                        "entered_grace_period_at": now.isoformat(),
                        "reason": "payment_not_confirmed_within_24h"
                    }
                )
                self.db.add(event)
                count += 1
                
                logger.info(
                    f"Subscription {subscription.id} entered grace period "
                    f"(expires {grace_period_end.isoformat()})"
                )
                
            except Exception as e:
                logger.error(
                    f"Error processing renewal for subscription {subscription.id}: {e}",
                    exc_info=True
                )
                self.db.rollback()
                continue
        
        if count > 0:
            self.db.commit()
        
        return count

    async def process_grace_period_expirations(self) -> int:
        """Expire subscriptions that have passed their grace period.
        
        **Requirements:** 4.4
        
        Returns:
            Count of subscriptions expired
        """
        now = datetime.utcnow()
        
        # Find subscriptions in grace period that have expired
        subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.status == "grace_period",
                Subscription.grace_period_end.isnot(None),
                Subscription.grace_period_end <= now
            )
            .all()
        )
        
        count = 0
        for subscription in subscriptions:
            try:
                previous_status = subscription.status
                
                subscription.status = "expired"
                
                # Create expiry event
                event = SubscriptionEvent(
                    subscription_id=subscription.id,
                    event_type="expired",
                    previous_status=previous_status,
                    new_status="expired",
                    event_metadata={
                        "expired_at": now.isoformat(),
                        "grace_period_end": subscription.grace_period_end.isoformat(),
                        "reason": "grace_period_expired_without_payment"
                    }
                )
                self.db.add(event)
                count += 1
                
                logger.info(
                    f"Subscription {subscription.id} expired after grace period"
                )
                
            except Exception as e:
                logger.error(
                    f"Error expiring subscription {subscription.id}: {e}",
                    exc_info=True
                )
                self.db.rollback()
                continue
        
        if count > 0:
            self.db.commit()
        
        return count

    async def process_pending_cancellations(self) -> int:
        """Process subscriptions marked for cancellation.
        
        Subscriptions with a cancellation_date set and past their
        next_renewal_date should be transitioned to cancelled status.
        
        **Requirements:** 4.7
        
        Returns:
            Count of subscriptions cancelled
        """
        now = datetime.utcnow()
        
        # Find subscriptions marked for cancellation that have reached their end date
        subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.cancellation_date.isnot(None),
                Subscription.next_renewal_date.isnot(None),
                Subscription.next_renewal_date <= now,
                Subscription.status.in_(["active", "grace_period"])
            )
            .all()
        )
        
        count = 0
        for subscription in subscriptions:
            try:
                previous_status = subscription.status
                
                subscription.status = "cancelled"
                
                # Create cancellation event
                event = SubscriptionEvent(
                    subscription_id=subscription.id,
                    event_type="cancelled",
                    previous_status=previous_status,
                    new_status="cancelled",
                    event_metadata={
                        "cancelled_at": now.isoformat(),
                        "cancellation_requested_at": subscription.cancellation_date.isoformat(),
                        "reason": "user_requested_cancellation"
                    }
                )
                self.db.add(event)
                count += 1
                
                logger.info(
                    f"Subscription {subscription.id} cancelled at end of billing period"
                )
                
            except Exception as e:
                logger.error(
                    f"Error cancelling subscription {subscription.id}: {e}",
                    exc_info=True
                )
                self.db.rollback()
                continue
        
        if count > 0:
            self.db.commit()
        
        return count

    async def cleanup_old_events(self, days_to_keep: int = 90) -> int:
        """Clean up subscription events older than specified days.
        
        Args:
            days_to_keep: Number of days of events to retain (default 90)
            
        Returns:
            Count of events deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            # Delete old events
            deleted = (
                self.db.query(SubscriptionEvent)
                .filter(SubscriptionEvent.occurred_at < cutoff_date)
                .delete()
            )
            
            self.db.commit()
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} subscription events older than {days_to_keep} days")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up old events: {e}", exc_info=True)
            self.db.rollback()
            return 0


async def start_subscription_scheduler(db: Session, interval_minutes: int = 60):
    """Start the subscription lifecycle scheduler.
    
    This function should be called on application startup to begin
    periodic subscription lifecycle processing.
    
    Args:
        db: SQLAlchemy database session
        interval_minutes: Interval between scheduler ticks (default 60)
    """
    global _scheduler_task
    
    logger.info(
        f"Starting subscription lifecycle scheduler "
        f"(interval: {interval_minutes} minutes)"
    )
    
    async def scheduler_loop():
        """Main scheduler loop that runs periodically."""
        while True:
            try:
                scheduler = SubscriptionScheduler(db)
                results = await scheduler.subscription_lifecycle_tick()
                
                logger.debug(f"Scheduler tick results: {results}")
                
            except Exception as e:
                logger.error(f"Scheduler tick failed: {e}", exc_info=True)
            
            # Wait for next tick
            await asyncio.sleep(interval_minutes * 60)
    
    # Start the scheduler task
    _scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("Subscription lifecycle scheduler started")


async def stop_subscription_scheduler():
    """Stop the subscription lifecycle scheduler.
    
    This function should be called on application shutdown to gracefully
    stop the scheduler task.
    """
    global _scheduler_task
    
    if _scheduler_task:
        logger.info("Stopping subscription lifecycle scheduler")
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
        logger.info("Subscription lifecycle scheduler stopped")


def get_scheduler_interval() -> int:
    """Get the scheduler interval from environment variable.
    
    Returns:
        Interval in minutes (default: 60)
    """
    try:
        interval = int(os.getenv("SUBSCRIPTION_SCHEDULER_INTERVAL_MINUTES", "60"))
        if interval < 1:
            logger.warning(
                f"Invalid scheduler interval {interval}, using default 60 minutes"
            )
            return 60
        return interval
    except ValueError:
        logger.warning(
            "Invalid SUBSCRIPTION_SCHEDULER_INTERVAL_MINUTES value, using default 60 minutes"
        )
        return 60


__all__ = [
    "SubscriptionScheduler",
    "start_subscription_scheduler",
    "stop_subscription_scheduler",
    "get_scheduler_interval"
]
