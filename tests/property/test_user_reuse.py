"""
Property-based tests for user reuse operations.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.source import Source
from app.models.request import Request
from app.repositories.user_repository import UserRepository
from app.repositories.request_repository import RequestRepository
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
    user_identifier=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    request_count=st.integers(min_value=2, max_value=10),
    messages=st.lists(
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        min_size=2,
        max_size=10
    )
)
def test_existing_user_reuse(user_identifier: str, request_count: int, messages: list):
    """
    Feature: operator-request-distribution, Property 13: Existing user reuse
    
    For any existing user_identifier, submitting multiple requests with that identifier
    should associate all requests with the same user (no duplicate users created).
    
    Validates: Requirements 4.3
    """
    session = TestSessionLocal()
    try:
        # Ensure we have enough messages
        actual_count = min(request_count, len(messages))
        
        # Create repositories
        user_repo = UserRepository(session)
        request_repo = RequestRepository(session)
        
        # Create a source for the requests
        source = Source(name="test_source", identifier=f"test_source_{user_identifier[:20]}")
        session.add(source)
        session.commit()
        
        # Create the first user with the identifier
        user = user_repo.create(identifier=user_identifier)
        session.commit()
        
        # Store the user ID
        original_user_id = user.id
        
        # Count users before creating requests
        users_before = session.query(User).filter(User.identifier == user_identifier).count()
        assert users_before == 1, f"Expected 1 user before creating requests, got {users_before}"
        
        # Create multiple requests with the same user_identifier
        created_requests = []
        for i in range(actual_count):
            # Get or create user (simulating the behavior of request service)
            existing_user = user_repo.get_by_identifier(user_identifier)
            
            if existing_user is None:
                # This should not happen in this test
                existing_user = user_repo.create(identifier=user_identifier)
                session.commit()
            
            # Create request with the existing user
            request = request_repo.create(
                user_id=existing_user.id,
                source_id=source.id,
                message=messages[i]
            )
            created_requests.append(request)
        
        session.commit()
        
        # Count users after creating requests
        users_after = session.query(User).filter(User.identifier == user_identifier).count()
        
        # Verify no duplicate users were created
        assert users_after == 1, \
            f"Expected 1 user after creating {actual_count} requests, got {users_after}. Duplicate users were created!"
        
        # Verify all requests are associated with the same user
        for request in created_requests:
            assert request.user_id == original_user_id, \
                f"Request {request.id} has user_id {request.user_id}, expected {original_user_id}"
        
        # Verify the user has all the requests
        user_requests = session.query(Request).filter(Request.user_id == original_user_id).all()
        assert len(user_requests) >= actual_count, \
            f"Expected at least {actual_count} requests for user {original_user_id}, got {len(user_requests)}"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
