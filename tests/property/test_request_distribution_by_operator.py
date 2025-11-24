"""
Property-based tests for request distribution by operator.
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
    num_operators=st.integers(min_value=1, max_value=5),
    requests_per_operator=st.lists(
        st.integers(min_value=0, max_value=10),
        min_size=1,
        max_size=5
    )
)
def test_request_distribution_by_operator(num_operators, requests_per_operator):
    """
    Feature: operator-request-distribution, Property 24: Request distribution by operator
    
    For any set of requests assigned to operators, the distribution statistics should
    correctly count requests grouped by operator_id.
    
    Validates: Requirements 8.1
    """
    session = TestSessionLocal()
    try:
        # Ensure we have the right number of request counts
        requests_per_operator = requests_per_operator[:num_operators]
        while len(requests_per_operator) < num_operators:
            requests_per_operator.append(0)
        
        # Create a user and source for requests
        user = User(identifier="test_user")
        session.add(user)
        source = Source(name="test_source", identifier="test_source_id")
        session.add(source)
        session.flush()
        
        # Create operators and their requests
        operator_request_counts = {}
        for i, request_count in enumerate(requests_per_operator):
            operator = Operator(
                name=f"operator_{i}",
                max_load_limit=100,
                current_load=0,
                is_active=True
            )
            session.add(operator)
            session.flush()
            
            # Create requests for this operator
            for j in range(request_count):
                request = Request(
                    user_id=user.id,
                    source_id=source.id,
                    operator_id=operator.id,
                    message=f"message_{i}_{j}",
                    status="pending"
                )
                session.add(request)
            
            operator_request_counts[operator.id] = request_count
        
        session.commit()
        
        # Get distribution statistics
        stats_service = StatsService(session)
        distribution_stats = stats_service.get_request_distribution_stats()
        
        # Verify distribution by operator
        by_operator = distribution_stats.by_operator
        
        # Create a mapping of operator_id to request count from stats
        stats_counts = {}
        for stat in by_operator:
            if stat.operator_id is not None:  # Exclude unassigned
                stats_counts[stat.operator_id] = stat.request_count
        
        # Verify each operator's request count
        for operator_id, expected_count in operator_request_counts.items():
            if expected_count > 0:
                assert operator_id in stats_counts, \
                    f"Operator {operator_id} with {expected_count} requests not found in stats"
                assert stats_counts[operator_id] == expected_count, \
                    f"Expected {expected_count} requests for operator {operator_id}, got {stats_counts[operator_id]}"
            else:
                # Operators with 0 requests should not appear in stats
                assert operator_id not in stats_counts, \
                    f"Operator {operator_id} with 0 requests should not appear in stats"
        
        # Verify total count matches
        total_expected = sum(requests_per_operator)
        total_from_stats = sum(stat.request_count for stat in by_operator if stat.operator_id is not None)
        assert total_from_stats == total_expected, \
            f"Expected total of {total_expected} requests, got {total_from_stats}"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.query(User).delete()
        session.commit()
        session.close()
