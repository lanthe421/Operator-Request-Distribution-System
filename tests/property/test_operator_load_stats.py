"""
Property-based tests for operator load statistics.
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
    operators_data=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),  # name
            st.integers(min_value=1, max_value=100),  # max_load_limit
            st.integers(min_value=0, max_value=100),  # current_load
            st.booleans()  # is_active
        ),
        min_size=1,
        max_size=10
    )
)
def test_operator_load_statistics_calculation(operators_data):
    """
    Feature: operator-request-distribution, Property 22: Operator load statistics calculation
    
    For any set of operators, the load statistics should return each operator's current_load,
    max_load_limit, and correctly calculated load percentage ((current_load / max_load_limit) * 100).
    
    Validates: Requirements 7.1, 7.2
    """
    session = TestSessionLocal()
    try:
        # Create operators with specified data
        created_operators = []
        for name, max_load_limit, current_load, is_active in operators_data:
            # Ensure current_load doesn't exceed max_load_limit
            actual_current_load = min(current_load, max_load_limit)
            
            operator = Operator(
                name=name,
                max_load_limit=max_load_limit,
                current_load=actual_current_load,
                is_active=is_active
            )
            session.add(operator)
            created_operators.append((operator, actual_current_load, max_load_limit))
        
        session.commit()
        
        # Refresh to get IDs
        for operator, _, _ in created_operators:
            session.refresh(operator)
        
        # Get statistics
        stats_service = StatsService(session)
        stats = stats_service.get_operator_load_stats()
        
        # Verify we got stats for all operators
        assert len(stats) == len(created_operators), \
            f"Expected {len(created_operators)} stats, got {len(stats)}"
        
        # Create a mapping of operator_id to stats
        stats_by_id = {stat.operator_id: stat for stat in stats}
        
        # Verify each operator's statistics
        for operator, expected_current_load, expected_max_load in created_operators:
            assert operator.id in stats_by_id, \
                f"Operator {operator.id} not found in statistics"
            
            stat = stats_by_id[operator.id]
            
            # Verify basic fields
            assert stat.operator_name == operator.name, \
                f"Expected name '{operator.name}', got '{stat.operator_name}'"
            assert stat.is_active == operator.is_active, \
                f"Expected is_active {operator.is_active}, got {stat.is_active}"
            assert stat.current_load == expected_current_load, \
                f"Expected current_load {expected_current_load}, got {stat.current_load}"
            assert stat.max_load_limit == expected_max_load, \
                f"Expected max_load_limit {expected_max_load}, got {stat.max_load_limit}"
            
            # Verify percentage calculation
            expected_percentage = (expected_current_load / expected_max_load) * 100
            assert abs(stat.load_percentage - expected_percentage) < 0.01, \
                f"Expected load_percentage {expected_percentage}, got {stat.load_percentage}"
        
    finally:
        # Clean up
        session.query(Operator).delete()
        session.commit()
        session.close()
