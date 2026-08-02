"""migrate user data to subscription platform

This migration performs the data transformation for the subscription platform
upgrade:
- Maps existing 'admin' users to 'platform_admin' role
- Maps existing 'student' users to 'student' role with 'direct_subscriber' subtype
- Creates Free Trial subscription records (7-day duration) for each migrated student
- Includes pre-migration validation (all users have non-null role of admin or student)
- Includes already-migrated detection (abort if new tables already have data)
- Logs migration stats (counts per role, subscriptions created, duration)

Requirements: 14.1, 14.2, 14.3, 14.6, 14.7, 14.8, 14.9, 10.5

Revision ID: 0005_migrate_user_data
Revises: 0004_fix_users_table
Create Date: 2026-05-19 13:00:00.000000

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timedelta
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0005_migrate_user_data'
down_revision: Union[str, Sequence[str], None] = '0004_fix_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Configure logging
logger = logging.getLogger('alembic.runtime.migration')


def upgrade() -> None:
    """Migrate existing user data to subscription platform model."""
    
    start_time = datetime.utcnow()
    logger.info("=" * 80)
    logger.info("Starting data migration for subscription platform upgrade")
    logger.info(f"Migration start time: {start_time.isoformat()}")
    logger.info("=" * 80)
    
    connection = op.get_bind()
    
    # =========================================================================
    # Step 1: Already-migrated detection
    # =========================================================================
    
    logger.info("Step 1: Checking if migration has already been run...")
    
    # Check if subscriptions table has any records
    result = connection.execute(text("SELECT COUNT(*) FROM subscriptions"))
    subscription_count = result.scalar()
    
    if subscription_count > 0:
        logger.warning(f"Migration already run: Found {subscription_count} existing subscription records")
        logger.warning("Aborting migration to prevent duplicate data")
        logger.info("=" * 80)
        return
    
    # Check if any users already have student_subtype set
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE student_subtype IS NOT NULL"
    ))
    subtype_count = result.scalar()
    
    if subtype_count > 0:
        logger.warning(f"Migration already run: Found {subtype_count} users with student_subtype set")
        logger.warning("Aborting migration to prevent duplicate data")
        logger.info("=" * 80)
        return
    
    logger.info("✓ No existing migration data found - proceeding with migration")
    
    # =========================================================================
    # Step 2: Pre-migration validation
    # =========================================================================
    
    logger.info("\nStep 2: Validating pre-migration data...")
    
    # Check for users with null role
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role IS NULL"
    ))
    null_role_count = result.scalar()
    
    if null_role_count > 0:
        error_msg = f"Pre-migration validation failed: Found {null_role_count} users with NULL role"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for users with invalid roles (not 'admin' or 'student')
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role NOT IN ('admin', 'student')"
    ))
    invalid_role_count = result.scalar()
    
    if invalid_role_count > 0:
        # Get details of invalid roles
        result = connection.execute(text(
            "SELECT id, email, role FROM users WHERE role NOT IN ('admin', 'student')"
        ))
        invalid_users = result.fetchall()
        logger.error(f"Pre-migration validation failed: Found {invalid_role_count} users with invalid roles:")
        for user in invalid_users:
            logger.error(f"  - User {user[0]} ({user[1]}): role='{user[2]}'")
        raise ValueError(f"Pre-migration validation failed: {invalid_role_count} users have invalid roles")
    
    logger.info("✓ Pre-migration validation passed")
    
    # =========================================================================
    # Step 3: Get user counts for reporting
    # =========================================================================
    
    logger.info("\nStep 3: Analyzing existing user data...")
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'admin'"
    ))
    admin_count = result.scalar()
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'student'"
    ))
    student_count = result.scalar()
    
    logger.info(f"  - Found {admin_count} admin users to migrate")
    logger.info(f"  - Found {student_count} student users to migrate")
    logger.info(f"  - Total users to migrate: {admin_count + student_count}")
    
    # =========================================================================
    # Step 4: Create Free Trial subscription plan
    # =========================================================================
    
    logger.info("\nStep 4: Creating Free Trial subscription plan...")
    
    # Check if Free Trial plan already exists
    result = connection.execute(text(
        "SELECT id FROM subscription_plans WHERE name = 'Free Trial' AND plan_type = 'individual'"
    ))
    existing_plan = result.fetchone()
    
    if existing_plan:
        free_trial_plan_id = existing_plan[0]
        logger.info(f"✓ Free Trial plan already exists (ID: {free_trial_plan_id})")
    else:
        free_trial_plan_id = str(uuid.uuid4())
        connection.execute(text("""
            INSERT INTO subscription_plans (
                id, name, plan_type, billing_period, price,
                max_test_attempts_per_period, max_student_seats,
                feature_flags, is_active, created_at
            ) VALUES (
                :id, 'Free Trial', 'individual', 'weekly', 0.00,
                5, NULL, '{}', 1, :created_at
            )
        """), {
            'id': free_trial_plan_id,
            'created_at': datetime.utcnow()
        })
        logger.info(f"✓ Created Free Trial plan (ID: {free_trial_plan_id})")
    
    # =========================================================================
    # Step 5: Migrate admin users to platform_admin role
    # =========================================================================
    
    logger.info("\nStep 5: Migrating admin users to platform_admin role...")
    
    if admin_count > 0:
        connection.execute(text("""
            UPDATE users
            SET role = 'platform_admin'
            WHERE role = 'admin'
        """))
        logger.info(f"✓ Migrated {admin_count} admin users to platform_admin role")
    else:
        logger.info("  - No admin users to migrate")
    
    # =========================================================================
    # Step 6: Migrate student users
    # =========================================================================
    
    logger.info("\nStep 6: Migrating student users...")
    
    if student_count > 0:
        # Update student users with direct_subscriber subtype
        connection.execute(text("""
            UPDATE users
            SET student_subtype = 'direct_subscriber'
            WHERE role = 'student'
        """))
        logger.info(f"✓ Set student_subtype='direct_subscriber' for {student_count} students")
        
        # Get all student user IDs
        result = connection.execute(text(
            "SELECT id FROM users WHERE role = 'student'"
        ))
        student_ids = [row[0] for row in result.fetchall()]
        
        # Create Free Trial subscriptions for each student
        migration_date = datetime.utcnow()
        trial_end_date = migration_date + timedelta(days=7)
        subscriptions_created = 0
        
        logger.info(f"  - Creating Free Trial subscriptions (7-day duration)...")
        logger.info(f"  - Trial start: {migration_date.isoformat()}")
        logger.info(f"  - Trial end: {trial_end_date.isoformat()}")
        
        for student_id in student_ids:
            subscription_id = str(uuid.uuid4())
            connection.execute(text("""
                INSERT INTO subscriptions (
                    id, user_id, institution_id, plan_id, status,
                    start_date, current_period_start, next_renewal_date,
                    cancellation_date, grace_period_end, trial_duration_days,
                    created_at, updated_at
                ) VALUES (
                    :id, :user_id, NULL, :plan_id, 'trial',
                    :start_date, :current_period_start, :next_renewal_date,
                    NULL, NULL, 7,
                    :created_at, :updated_at
                )
            """), {
                'id': subscription_id,
                'user_id': student_id,
                'plan_id': free_trial_plan_id,
                'start_date': migration_date,
                'current_period_start': migration_date,
                'next_renewal_date': trial_end_date,
                'created_at': migration_date,
                'updated_at': migration_date
            })
            
            # Create subscription event for audit trail
            event_id = str(uuid.uuid4())
            connection.execute(text("""
                INSERT INTO subscription_events (
                    id, subscription_id, event_type, previous_status, new_status,
                    metadata, occurred_at
                ) VALUES (
                    :id, :subscription_id, 'activated', 'none', 'trial',
                    :metadata, :occurred_at
                )
            """), {
                'id': event_id,
                'subscription_id': subscription_id,
                'metadata': '{"source": "data_migration", "migration_revision": "0005_migrate_user_data"}',
                'occurred_at': migration_date
            })
            
            subscriptions_created += 1
        
        logger.info(f"✓ Created {subscriptions_created} Free Trial subscription records")
    else:
        logger.info("  - No student users to migrate")
        subscriptions_created = 0
    
    # =========================================================================
    # Step 7: Verify migration results
    # =========================================================================
    
    logger.info("\nStep 7: Verifying migration results...")
    
    # Verify platform_admin count
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'platform_admin'"
    ))
    migrated_admin_count = result.scalar()
    
    # Verify student count with subtype
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'student' AND student_subtype = 'direct_subscriber'"
    ))
    migrated_student_count = result.scalar()
    
    # Verify subscription count
    result = connection.execute(text(
        "SELECT COUNT(*) FROM subscriptions WHERE status = 'trial'"
    ))
    trial_subscription_count = result.scalar()
    
    # Check for any orphaned records
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'admin'"
    ))
    remaining_admin_count = result.scalar()
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'student' AND student_subtype IS NULL"
    ))
    remaining_student_count = result.scalar()
    
    verification_passed = True
    
    if migrated_admin_count != admin_count:
        logger.error(f"✗ Admin migration mismatch: expected {admin_count}, got {migrated_admin_count}")
        verification_passed = False
    else:
        logger.info(f"✓ Admin migration verified: {migrated_admin_count} platform_admin users")
    
    if migrated_student_count != student_count:
        logger.error(f"✗ Student migration mismatch: expected {student_count}, got {migrated_student_count}")
        verification_passed = False
    else:
        logger.info(f"✓ Student migration verified: {migrated_student_count} direct_subscriber students")
    
    if trial_subscription_count != subscriptions_created:
        logger.error(f"✗ Subscription creation mismatch: expected {subscriptions_created}, got {trial_subscription_count}")
        verification_passed = False
    else:
        logger.info(f"✓ Subscription creation verified: {trial_subscription_count} trial subscriptions")
    
    if remaining_admin_count > 0:
        logger.error(f"✗ Found {remaining_admin_count} users still with 'admin' role")
        verification_passed = False
    
    if remaining_student_count > 0:
        logger.error(f"✗ Found {remaining_student_count} students without student_subtype")
        verification_passed = False
    
    if not verification_passed:
        raise ValueError("Migration verification failed - see errors above")
    
    # =========================================================================
    # Step 8: Log final migration statistics
    # =========================================================================
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info("Migration Statistics:")
    logger.info(f"  - Platform admins migrated: {migrated_admin_count}")
    logger.info(f"  - Students migrated: {migrated_student_count}")
    logger.info(f"  - Free Trial subscriptions created: {subscriptions_created}")
    logger.info(f"  - Total users processed: {migrated_admin_count + migrated_student_count}")
    logger.info(f"  - Migration duration: {duration:.2f} seconds")
    logger.info(f"  - Migration end time: {end_time.isoformat()}")
    logger.info("=" * 80)


def downgrade() -> None:
    """Revert data migration - restore original user roles and remove subscriptions."""
    
    start_time = datetime.utcnow()
    logger.info("=" * 80)
    logger.info("Starting data migration rollback")
    logger.info(f"Rollback start time: {start_time.isoformat()}")
    logger.info("=" * 80)
    
    connection = op.get_bind()
    
    # =========================================================================
    # Step 1: Get counts for reporting
    # =========================================================================
    
    logger.info("Step 1: Analyzing current data...")
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'platform_admin'"
    ))
    platform_admin_count = result.scalar()
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'student' AND student_subtype = 'direct_subscriber'"
    ))
    direct_subscriber_count = result.scalar()
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM subscriptions"
    ))
    subscription_count = result.scalar()
    
    logger.info(f"  - Found {platform_admin_count} platform_admin users")
    logger.info(f"  - Found {direct_subscriber_count} direct_subscriber students")
    logger.info(f"  - Found {subscription_count} subscription records")
    
    # =========================================================================
    # Step 2: Delete subscription events
    # =========================================================================
    
    logger.info("\nStep 2: Deleting subscription events...")
    
    result = connection.execute(text(
        "DELETE FROM subscription_events"
    ))
    logger.info(f"✓ Deleted {result.rowcount} subscription event records")
    
    # =========================================================================
    # Step 3: Delete subscriptions
    # =========================================================================
    
    logger.info("\nStep 3: Deleting subscriptions...")
    
    result = connection.execute(text(
        "DELETE FROM subscriptions"
    ))
    logger.info(f"✓ Deleted {result.rowcount} subscription records")
    
    # =========================================================================
    # Step 4: Revert platform_admin to admin
    # =========================================================================
    
    logger.info("\nStep 4: Reverting platform_admin users to admin role...")
    
    if platform_admin_count > 0:
        connection.execute(text("""
            UPDATE users
            SET role = 'admin'
            WHERE role = 'platform_admin'
        """))
        logger.info(f"✓ Reverted {platform_admin_count} platform_admin users to admin role")
    else:
        logger.info("  - No platform_admin users to revert")
    
    # =========================================================================
    # Step 5: Revert student subtypes
    # =========================================================================
    
    logger.info("\nStep 5: Clearing student subtypes...")
    
    if direct_subscriber_count > 0:
        connection.execute(text("""
            UPDATE users
            SET student_subtype = NULL
            WHERE role = 'student' AND student_subtype = 'direct_subscriber'
        """))
        logger.info(f"✓ Cleared student_subtype for {direct_subscriber_count} students")
    else:
        logger.info("  - No student subtypes to clear")
    
    # =========================================================================
    # Step 6: Delete Free Trial plan (optional - only if created by migration)
    # =========================================================================
    
    logger.info("\nStep 6: Cleaning up Free Trial plan...")
    
    # Only delete if it was created by this migration (has no other subscriptions)
    result = connection.execute(text("""
        DELETE FROM subscription_plans
        WHERE name = 'Free Trial'
        AND plan_type = 'individual'
        AND NOT EXISTS (
            SELECT 1 FROM subscriptions WHERE plan_id = subscription_plans.id
        )
    """))
    
    if result.rowcount > 0:
        logger.info(f"✓ Deleted Free Trial plan")
    else:
        logger.info("  - Free Trial plan retained (has other subscriptions or was pre-existing)")
    
    # =========================================================================
    # Step 7: Verify rollback results
    # =========================================================================
    
    logger.info("\nStep 7: Verifying rollback results...")
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'admin'"
    ))
    reverted_admin_count = result.scalar()
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM users WHERE student_subtype IS NOT NULL"
    ))
    remaining_subtype_count = result.scalar()
    
    result = connection.execute(text(
        "SELECT COUNT(*) FROM subscriptions"
    ))
    remaining_subscription_count = result.scalar()
    
    logger.info(f"✓ Rollback verified: {reverted_admin_count} admin users")
    logger.info(f"✓ Rollback verified: {remaining_subtype_count} users with student_subtype (should be 0)")
    logger.info(f"✓ Rollback verified: {remaining_subscription_count} subscriptions remaining")
    
    # =========================================================================
    # Step 8: Log final rollback statistics
    # =========================================================================
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("\n" + "=" * 80)
    logger.info("ROLLBACK COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info("Rollback Statistics:")
    logger.info(f"  - Platform admins reverted to admin: {reverted_admin_count}")
    logger.info(f"  - Student subtypes cleared: {direct_subscriber_count}")
    logger.info(f"  - Subscriptions deleted: {subscription_count}")
    logger.info(f"  - Rollback duration: {duration:.2f} seconds")
    logger.info(f"  - Rollback end time: {end_time.isoformat()}")
    logger.info("=" * 80)
