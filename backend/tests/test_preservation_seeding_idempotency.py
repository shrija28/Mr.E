"""Preservation property tests for database seeding idempotency.

This module contains preservation tests for Bug 2: Database seeding not 
called automatically on startup.

**Validates: Requirement 3.3**

Preservation Requirement: When subscription_plans table already has plans, 
subsequent calls to seed_subscription_plans() return 0 and add no new rows.
Existing plan data (name, price, feature_flags) is never modified.

CRITICAL: This test MUST PASS on unfixed code to confirm we've captured 
the baseline idempotent behavior that must be preserved. This is the 
preservation guarantee — we verify the non-buggy behavior path (plans 
already exist) continues to work correctly.

Observation-First Methodology:
1. OBSERVE: When seed_subscription_plans() is called once, 6 plans are created
2. OBSERVE: When seed_subscription_plans() is called a second time, what happens?
   - Does it return 0? (idempotent)
   - Does it add new plans? (should not)
   - Are existing plan data modified? (should not)
3. WRITE: Property-based test that captures this pattern
4. VERIFY: Test passes on unfixed code (confirms baseline captured)
"""

import uuid
from decimal import Decimal
from pathlib import Path 
import sys
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from smartkcet.db.base import Base
from smartkcet.db.subscription_models import SubscriptionPlan
from smartkcet.db.seed import seed_subscription_plans


# =============================================================================
# Test Setup: Fresh Database Sessions
# =============================================================================


@pytest.fixture
def fresh_db_session():
    """Create a fresh in-memory database session for each test.
    
    Creates a clean database state mimicking a first startup where no
    seeding has occurred yet. Allows testing the idempotent behavior
    when plans already exist.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    
    # Create all tables (schema only, no data)
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestSessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()


# =============================================================================
# Hypothesis Strategies
# =============================================================================


@st.composite
def seeding_attempts(draw):
    """Generate a sequence of 2-5 seeding attempts.
    
    This strategy generates between 2 and 5 seeding attempts to test
    the idempotency property with multiple consecutive calls.
    """
    return draw(st.integers(min_value=2, max_value=5))


# =============================================================================
# Preservation Property Tests
# =============================================================================


class TestSeedingIdempotency:
    """
    Property: Preservation - Idempotent Seeding on Existing Plans
    
    **Validates: Requirement 3.3**
    
    For all cases where plans already exist in the subscription_plans table,
    subsequent calls to seed_subscription_plans() SHALL:
    (a) Return 0 to indicate no new plans were inserted
    (b) Preserve existing plan count (no duplicates)
    (c) Preserve all existing plan data (name, price, feature_flags)
    
    This is the preservation guarantee: we must ensure that when the fix
    is applied (adding the seed call to startup), it doesn't break the
    idempotent behavior that already exists.
    """

    def test_preservation_seeding_returns_zero_when_plans_exist(
        self, fresh_db_session: Session
    ):
        """Preservation: seed_subscription_plans() returns 0 on existing plans.
        
        **Validates: Requirement 3.3**
        
        When subscription_plans table already has plans, subsequent calls to
        seed_subscription_plans() SHALL return 0, indicating idempotency.
        
        This test MUST PASS on unfixed code (confirms baseline behavior).
        After the fix is applied, this should still PASS (preservation).
        """
        # Step 1: Seed the database for the first time
        seeded_count_1 = seed_subscription_plans(fresh_db_session)
        assert seeded_count_1 == 8, (
            f"First seed should insert 8 plans, got {seeded_count_1}"
        )
        
        # Step 2: Seed again with plans already existing
        seeded_count_2 = seed_subscription_plans(fresh_db_session)
        
        # ASSERT: Second seed should return 0 (idempotent)
        assert seeded_count_2 == 0, (
            f"PRESERVATION FAILURE: Second seed should return 0 (idempotent), "
            f"got {seeded_count_2}. This breaks the idempotency guarantee."
        )

    def test_preservation_plan_count_unchanged_after_reseed(
        self, fresh_db_session: Session
    ):
        """Preservation: Plan count stays same (no duplicates on reseed).
        
        **Validates: Requirement 3.3**
        
        When subscription_plans table already has 6 plans, subsequent
        calls to seed_subscription_plans() SHALL NOT add new plans.
        The count must remain exactly 6.
        
        This test MUST PASS on unfixed code (confirms baseline behavior).
        After the fix is applied, this should still PASS (preservation).
        """
        # Step 1: Seed the database for the first time
        seed_subscription_plans(fresh_db_session)
        plan_count_after_first = fresh_db_session.query(SubscriptionPlan).count()
        assert plan_count_after_first == 8, "First seed should create 8 plans"
        
        # Step 2: Seed again and verify count unchanged
        seed_subscription_plans(fresh_db_session)
        plan_count_after_second = fresh_db_session.query(SubscriptionPlan).count()
        
        # ASSERT: Count should remain 8 (no duplicates)
        assert plan_count_after_second == 8, (
            f"PRESERVATION FAILURE: Plan count should remain 8, "
            f"got {plan_count_after_second}. "
            f"This indicates duplicate plans were created on reseed."
        )

    def test_preservation_plan_data_unchanged_after_reseed(
        self, fresh_db_session: Session
    ):
        """Preservation: Plan data (name, price, features) unchanged after reseed.
        
        **Validates: Requirement 3.3**
        
        When subscription_plans table already has plans, subsequent calls to
        seed_subscription_plans() SHALL NOT modify existing plan data.
        All plan names, prices, and feature_flags must remain identical.
        
        This test MUST PASS on unfixed code (confirms baseline behavior).
        After the fix is applied, this should still PASS (preservation).
        """
        # Step 1: Seed the database for the first time and capture data
        seed_subscription_plans(fresh_db_session)
        
        plans_after_first = fresh_db_session.query(SubscriptionPlan).all()
        plan_data_before = {
            plan.id: {
                "name": plan.name,
                "price": plan.price,
                "plan_type": plan.plan_type,
                "billing_period": plan.billing_period,
                "max_test_attempts_per_period": plan.max_test_attempts_per_period,
                "feature_flags": plan.feature_flags,
                "is_active": plan.is_active,
            }
            for plan in plans_after_first
        }
        
        # Step 2: Seed again with plans already existing
        seed_subscription_plans(fresh_db_session)
        
        # Step 3: Capture data after second seed and compare
        plans_after_second = fresh_db_session.query(SubscriptionPlan).all()
        plan_data_after = {
            plan.id: {
                "name": plan.name,
                "price": plan.price,
                "plan_type": plan.plan_type,
                "billing_period": plan.billing_period,
                "max_test_attempts_per_period": plan.max_test_attempts_per_period,
                "feature_flags": plan.feature_flags,
                "is_active": plan.is_active,
            }
            for plan in plans_after_second
        }
        
        # ASSERT: Plan data must be identical before and after second seed
        assert plan_data_before == plan_data_after, (
            f"PRESERVATION FAILURE: Plan data changed after reseed. "
            f"This indicates existing plans were modified. "
            f"Data before: {plan_data_before}, "
            f"Data after: {plan_data_after}"
        )

    def test_preservation_plan_names_unchanged(
        self, fresh_db_session: Session
    ):
        """Preservation: Individual plan names unchanged after reseed.
        
        **Validates: Requirement 3.3**
        
        Captures the specific names of each seeded plan and verifies they
        remain unchanged after a subsequent seed call. This is a focused
        check on the plan name preservation.
        """
        # Step 1: Seed and capture plan names
        seed_subscription_plans(fresh_db_session)
        plans_before = fresh_db_session.query(SubscriptionPlan).all()
        names_before = sorted([plan.name for plan in plans_before])
        
        # Step 2: Seed again
        seed_subscription_plans(fresh_db_session)
        plans_after = fresh_db_session.query(SubscriptionPlan).all()
        names_after = sorted([plan.name for plan in plans_after])
        
        # ASSERT: Plan names must be identical
        assert names_before == names_after, (
            f"PRESERVATION FAILURE: Plan names changed. "
            f"Before: {names_before}, After: {names_after}"
        )
        
        # ASSERT: Names must be the expected 8 plans
        expected_names = sorted([
            "Free",
            "7-Day Premium Trial",
            "Pro Monthly",
            "Pro Yearly",
            "Starter",
            "Basic",
            "Premium",
            "Enterprise",
        ])
        assert names_after == expected_names, (
            f"PRESERVATION FAILURE: Plan names don't match expected. "
            f"Expected: {expected_names}, Got: {names_after}"
        )

    def test_preservation_plan_prices_unchanged(
        self, fresh_db_session: Session
    ):
        """Preservation: Individual plan prices unchanged after reseed.
        
        **Validates: Requirement 3.3**
        
        Captures the specific prices of each seeded plan and verifies they
        remain unchanged after a subsequent seed call. This is a focused
        check on price preservation.
        """
        # Step 1: Seed and capture plan prices
        seed_subscription_plans(fresh_db_session)
        plans_before = fresh_db_session.query(SubscriptionPlan).all()
        prices_before = {plan.name: plan.price for plan in plans_before}
        
        # Step 2: Seed again
        seed_subscription_plans(fresh_db_session)
        plans_after = fresh_db_session.query(SubscriptionPlan).all()
        prices_after = {plan.name: plan.price for plan in plans_after}
        
        # ASSERT: Prices must be identical for each plan
        assert prices_before == prices_after, (
            f"PRESERVATION FAILURE: Plan prices changed. "
            f"Before: {prices_before}, After: {prices_after}"
        )
        
        # ASSERT: Prices must match expected values
        expected_prices = {
            "Free": Decimal("0.00"),
            "7-Day Premium Trial": Decimal("99.00"),
            "Pro Monthly": Decimal("349.00"),
            "Pro Yearly": Decimal("2999.00"),
            "Starter": Decimal("1499.00"),
            "Basic": Decimal("2999.00"),
            "Premium": Decimal("7999.00"),
            "Enterprise": Decimal("0.00"),
        }
        assert prices_after == expected_prices, (
            f"PRESERVATION FAILURE: Plan prices don't match expected. "
            f"Expected: {expected_prices}, Got: {prices_after}"
        )

    @given(num_attempts=seeding_attempts())
    @settings(max_examples=50)
    def test_preservation_multiple_seeding_attempts_property(
        self, num_attempts: int
    ):
        """Property: Multiple seeding attempts preserve idempotency.
        
        **Validates: Requirement 3.3**
        
        **Scoped Property-Based Test**: For all N in [2, 5], when
        seed_subscription_plans() is called N times (N >= 2), then:
        (a) First call returns 6 (plans inserted)
        (b) All subsequent calls return 0 (idempotent)
        (c) Final plan count is exactly 6 (no duplicates)
        (d) All plan data remains unchanged
        
        This test MUST PASS on unfixed code (confirms baseline idempotent
        behavior with multiple attempts).
        """
        # Create a fresh database for this property test
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        db_session = TestSessionLocal()
        
        try:
            # Verify num_attempts is in expected range
            assert 2 <= num_attempts <= 5, (
                f"num_attempts should be 2-5, got {num_attempts}"
            )
            
            # Perform multiple seeding attempts
            results = []
            for attempt_num in range(1, num_attempts + 1):
                result = seed_subscription_plans(db_session)
                results.append(result)
            
            # ASSERT (a): First seed returns 8
            assert results[0] == 8, (
                f"PRESERVATION FAILURE: First seed should return 8, "
                f"got {results[0]}"
            )
            
            # ASSERT (b): All subsequent seeds return 0
            for i, result in enumerate(results[1:], start=2):
                assert result == 0, (
                    f"PRESERVATION FAILURE: Seed attempt {i} should return 0 "
                    f"(idempotent), got {result}"
                )
            
            # ASSERT (c): Final plan count is exactly 8
            final_plan_count = db_session.query(SubscriptionPlan).count()
            assert final_plan_count == 8, (
                f"PRESERVATION FAILURE: After {num_attempts} seeding attempts, "
                f"plan count should be 8, got {final_plan_count}"
            )
            
            # ASSERT (d): Verify all plans exist with correct names
            plans = db_session.query(SubscriptionPlan).all()
            plan_names = sorted([plan.name for plan in plans])
            expected_names = sorted([
                "Free",
                "7-Day Premium Trial",
                "Pro Monthly",
                "Pro Yearly",
                "Starter",
                "Basic",
                "Premium",
                "Enterprise",
            ])
            assert plan_names == expected_names, (
                f"PRESERVATION FAILURE: After {num_attempts} attempts, "
                f"plan names don't match expected. "
                f"Expected: {expected_names}, Got: {plan_names}"
            )
        finally:
            db_session.close()
            engine.dispose()

    def test_preservation_idempotency_with_three_attempts(
        self, fresh_db_session: Session
    ):
        """Concrete test: Idempotency with 3 seeding attempts.
        
        **Validates: Requirement 3.3**
        
        Concrete example showing idempotency works correctly with
        3 consecutive seeding attempts.
        """
        # Attempt 1: Seed fresh database
        result_1 = seed_subscription_plans(fresh_db_session)
        count_1 = fresh_db_session.query(SubscriptionPlan).count()
        
        # Attempt 2: Seed again (plans exist)
        result_2 = seed_subscription_plans(fresh_db_session)
        count_2 = fresh_db_session.query(SubscriptionPlan).count()
        
        # Attempt 3: Seed again (plans exist)
        result_3 = seed_subscription_plans(fresh_db_session)
        count_3 = fresh_db_session.query(SubscriptionPlan).count()
        
        # Verify idempotency pattern
        assert result_1 == 8 and count_1 == 8, "First seed should insert 8"
        assert result_2 == 0 and count_2 == 8, "Second seed should return 0, count=8"
        assert result_3 == 0 and count_3 == 8, "Third seed should return 0, count=8"

    def test_preservation_idempotency_with_five_attempts(
        self, fresh_db_session: Session
    ):
        """Concrete test: Idempotency with 5 seeding attempts.
        
        **Validates: Requirement 3.3**
        
        Concrete example showing idempotency works correctly with
        5 consecutive seeding attempts (stress test).
        """
        # Perform 5 seeding attempts
        results = []
        counts = []
        for attempt in range(5):
            result = seed_subscription_plans(fresh_db_session)
            count = fresh_db_session.query(SubscriptionPlan).count()
            results.append(result)
            counts.append(count)
        
        # Verify pattern: first returns 8, rest return 0
        assert results[0] == 8, f"First seed should return 8, got {results[0]}"
        for i, result in enumerate(results[1:], start=2):
            assert result == 0, (
                f"Seed attempt {i} should return 0, got {result}"
            )
        
        # Verify counts stay at 8
        for i, count in enumerate(counts, start=1):
            assert count == 8, (
                f"After seed attempt {i}, count should be 8, got {count}"
            )


class TestSeedingPreservationEdgeCases:
    """Edge case tests for preservation of seeding idempotency."""

    def test_preservation_direct_table_inspection(
        self, fresh_db_session: Session
    ):
        """Direct table inspection: Verify rows not duplicated on reseed.
        
        **Validates: Requirement 3.3**
        
        Uses direct row-by-row inspection to verify that reseed doesn't
        create duplicate rows. Each plan should have a unique ID and appear
        exactly once after each seed call.
        """
        # Seed once
        seed_subscription_plans(fresh_db_session)
        plans_first = fresh_db_session.query(SubscriptionPlan).all()
        ids_first = sorted([str(plan.id) for plan in plans_first])
        
        # Seed again
        seed_subscription_plans(fresh_db_session)
        plans_second = fresh_db_session.query(SubscriptionPlan).all()
        ids_second = sorted([str(plan.id) for plan in plans_second])
        
        # ASSERT: IDs should be identical (same 6 plans)
        assert ids_first == ids_second, (
            f"PRESERVATION FAILURE: Plan IDs changed after reseed. "
            f"This indicates different plans were created. "
            f"Before: {ids_first}, After: {ids_second}"
        )
        
        # ASSERT: Each plan appears exactly once
        assert len(ids_second) == 8, (
            f"PRESERVATION FAILURE: Should have exactly 8 unique plans, "
            f"got {len(ids_second)}"
        )

    def test_preservation_feature_flags_unchanged(
        self, fresh_db_session: Session
    ):
        """Preservation: Feature flags unchanged after reseed.
        
        **Validates: Requirement 3.3**
        
        Verifies that the feature_flags JSON field is preserved unchanged
        after a subsequent seed call.
        """
        # Seed and capture feature flags
        seed_subscription_plans(fresh_db_session)
        plans_before = fresh_db_session.query(SubscriptionPlan).all()
        flags_before = {
            plan.name: plan.feature_flags 
            for plan in plans_before
        }
        
        # Seed again
        seed_subscription_plans(fresh_db_session)
        plans_after = fresh_db_session.query(SubscriptionPlan).all()
        flags_after = {
            plan.name: plan.feature_flags 
            for plan in plans_after
        }
        
        # ASSERT: Feature flags must be identical
        assert flags_before == flags_after, (
            f"PRESERVATION FAILURE: Feature flags changed. "
            f"Before: {flags_before}, After: {flags_after}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
