"""
Property-based tests for statistics including all operators.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.operator import Operator
from app.services.stats_service import StatsService
from app.core.database import Base


# Create a separate in-memory database for testing
test_engine = create_engine("sqlite:///:memory:", echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def setup_module():
    """Create database schema once for all tests in this module."""
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    """Drop database schema after all tests."""
    Base.metadata.drop_all(bind=test_engine)


@settings(max_examples=100, deadline=1000)
@given(
    active_operators=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
            st.integers(min_value=1, max_value=100),
            st.integers(min_value=0, max_value=100)
        ),
        min_size=0,
        max_size=5
    ),
    inactive_operators=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
            st.integers(min_value=1, max_value=100),
            st.integers(min_value=0, max_value=100)
        ),
        min_size=0,
        max_size=5
    )
)
def test_statistics_include_all_operators(active_operators, inactive_operators):
    """
    Feature: operator-request-distribution, Property 23: Statistics include all operators
    
    For any mix of active and inactive operators, the statistics should include
    all operators regardless of their active status.
    
    Validates: Requirements 7.3
    """
    session = TestSessionLocal()
    try:
        total_operators = len(active_operators) + len(inactive_operators)
        
        # Skip if no operators
        if total_operators == 0:
            return
        
        created_operator_ids = []
        
        # Create active operators
        for name, max_load_limit, current_load in active_operators:
            actual_current_load = min(current_load, max_load_limit)
            operator = Operator(
                name=name,
                max_load_limit=max_load_limit,
                current_load=actual_current_load,
                is_active=True
            )
            session.add(operator)
            session.flush()
            created_operator_ids.append(operator.id)
        
        # Create inactive operators
        for name, max_load_limit, current_load in inactive_operators:
            actual_current_load = min(current_load, max_load_limit)
            operator = Operator(
                name=name,
                max_load_limit=max_load_limit,
                current_load=actual_current_load,
                is_active=False
            )
            session.add(operator)
            session.flush()
            created_operator_ids.append(operator.id)
        
        session.commit()
        
        # Get statistics
        stats_service = StatsService(session)
        stats = stats_service.get_operator_load_stats()
        
        # Verify all operators are included
        assert len(stats) == total_operators, \
            f"Expected {total_operators} operators in stats, got {len(stats)}"
        
        # Verify all created operator IDs are present
        stats_operator_ids = {stat.operator_id for stat in stats}
        for operator_id in created_operator_ids:
            assert operator_id in stats_operator_ids, \
                f"Operator {operator_id} not found in statistics"
        
        # Verify we have both active and inactive operators if both were created
        if len(active_operators) > 0 and len(inactive_operators) > 0:
            active_count = sum(1 for stat in stats if stat.is_active)
            inactive_count = sum(1 for stat in stats if not stat.is_active)
            
            assert active_count == len(active_operators), \
                f"Expected {len(active_operators)} active operators, got {active_count}"
            assert inactive_count == len(inactive_operators), \
                f"Expected {len(inactive_operators)} inactive operators, got {inactive_count}"
        
    finally:
        # Clean up
        session.query(Operator).delete()
        session.commit()
        session.close()
