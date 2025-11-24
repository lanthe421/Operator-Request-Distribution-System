"""
Property-based tests for unassigned requests in statistics.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.operator import Operator
from app.models.user import User
from app.models.source import Source
from app.models.request import Request
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


@settings(max_examples=100, deadline=2000)
@given(
    num_assigned=st.integers(min_value=0, max_value=10),
    num_unassigned=st.integers(min_value=1, max_value=10)
)
def test_unassigned_requests_in_statistics(num_assigned, num_unassigned):
    """
    Feature: operator-request-distribution, Property 26: Unassigned requests in statistics
    
    For any requests with NULL operator_id, the distribution statistics should
    include them as unassigned requests.
    
    Validates: Requirements 8.3
    """
    session = TestSessionLocal()
    try:
        # Create a user and source for requests
        user = User(identifier="test_user")
        session.add(user)
        source = Source(name="test_source", identifier="test_source_id")
        session.add(source)
        session.flush()
        
        # Create an operator for assigned requests
        operator = None
        if num_assigned > 0:
            operator = Operator(
                name="test_operator",
                max_load_limit=100,
                current_load=0,
                is_active=True
            )
            session.add(operator)
            session.flush()
        
        # Create assigned requests
        for i in range(num_assigned):
            request = Request(
                user_id=user.id,
                source_id=source.id,
                operator_id=operator.id,
                message=f"assigned_message_{i}",
                status="pending"
            )
            session.add(request)
        
        # Create unassigned requests (operator_id = NULL)
        for i in range(num_unassigned):
            request = Request(
                user_id=user.id,
                source_id=source.id,
                operator_id=None,
                message=f"unassigned_message_{i}",
                status="waiting"
            )
            session.add(request)
        
        session.commit()
        
        # Get distribution statistics
        stats_service = StatsService(session)
        distribution_stats = stats_service.get_request_distribution_stats()
        
        # Verify unassigned count
        assert distribution_stats.unassigned_requests == num_unassigned, \
            f"Expected {num_unassigned} unassigned requests, got {distribution_stats.unassigned_requests}"
        
        # Verify total count
        assert distribution_stats.total_requests == num_assigned + num_unassigned, \
            f"Expected {num_assigned + num_unassigned} total requests, got {distribution_stats.total_requests}"
        
        # Verify unassigned requests appear in by_operator distribution
        by_operator = distribution_stats.by_operator
        unassigned_in_distribution = [stat for stat in by_operator if stat.operator_id is None]
        
        if num_unassigned > 0:
            assert len(unassigned_in_distribution) == 1, \
                f"Expected 1 unassigned entry in by_operator, got {len(unassigned_in_distribution)}"
            assert unassigned_in_distribution[0].request_count == num_unassigned, \
                f"Expected {num_unassigned} unassigned requests in by_operator, got {unassigned_in_distribution[0].request_count}"
            assert unassigned_in_distribution[0].operator_name is None, \
                "Expected operator_name to be None for unassigned requests"
        else:
            assert len(unassigned_in_distribution) == 0, \
                "Expected no unassigned entry when num_unassigned is 0"
        
        # Verify assigned requests count
        assigned_in_distribution = [stat for stat in by_operator if stat.operator_id is not None]
        total_assigned_from_stats = sum(stat.request_count for stat in assigned_in_distribution)
        assert total_assigned_from_stats == num_assigned, \
            f"Expected {num_assigned} assigned requests, got {total_assigned_from_stats}"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.query(User).delete()
        session.commit()
        session.close()
