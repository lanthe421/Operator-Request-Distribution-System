"""
Property-based tests for request distribution by source.
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
    num_sources=st.integers(min_value=1, max_value=5),
    requests_per_source=st.lists(
        st.integers(min_value=1, max_value=10),
        min_size=1,
        max_size=5
    )
)
def test_request_distribution_by_source(num_sources, requests_per_source):
    """
    Feature: operator-request-distribution, Property 25: Request distribution by source
    
    For any set of requests from different sources, the distribution statistics should
    correctly count requests grouped by source_id.
    
    Validates: Requirements 8.2
    """
    session = TestSessionLocal()
    try:
        # Ensure we have the right number of request counts
        requests_per_source = requests_per_source[:num_sources]
        while len(requests_per_source) < num_sources:
            requests_per_source.append(1)
        
        # Create a user and operator for requests
        user = User(identifier="test_user")
        session.add(user)
        operator = Operator(
            name="test_operator",
            max_load_limit=1000,
            current_load=0,
            is_active=True
        )
        session.add(operator)
        session.flush()
        
        # Create sources and their requests
        source_request_counts = {}
        for i, request_count in enumerate(requests_per_source):
            source = Source(
                name=f"source_{i}",
                identifier=f"source_id_{i}"
            )
            session.add(source)
            session.flush()
            
            # Create requests for this source
            for j in range(request_count):
                request = Request(
                    user_id=user.id,
                    source_id=source.id,
                    operator_id=operator.id,
                    message=f"message_{i}_{j}",
                    status="pending"
                )
                session.add(request)
            
            source_request_counts[source.id] = request_count
        
        session.commit()
        
        # Get distribution statistics
        stats_service = StatsService(session)
        distribution_stats = stats_service.get_request_distribution_stats()
        
        # Verify distribution by source
        by_source = distribution_stats.by_source
        
        # Verify we have stats for all sources
        assert len(by_source) == num_sources, \
            f"Expected {num_sources} sources in stats, got {len(by_source)}"
        
        # Create a mapping of source_id to request count from stats
        stats_counts = {stat.source_id: stat.request_count for stat in by_source}
        
        # Verify each source's request count
        for source_id, expected_count in source_request_counts.items():
            assert source_id in stats_counts, \
                f"Source {source_id} with {expected_count} requests not found in stats"
            assert stats_counts[source_id] == expected_count, \
                f"Expected {expected_count} requests for source {source_id}, got {stats_counts[source_id]}"
        
        # Verify total count matches
        total_expected = sum(requests_per_source)
        total_from_stats = sum(stat.request_count for stat in by_source)
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
