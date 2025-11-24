"""
Property-based tests for new user auto-creation.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.source import Source
from app.models.request import Request
from app.models.user import User
from app.services.request_service import RequestService
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
    source_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
)
def test_new_user_auto_creation(user_identifier: str, source_name: str, message: str):
    """
    Feature: operator-request-distribution, Property 12: New user auto-creation
    
    For any user_identifier that doesn't exist in the system, submitting a request
    with that identifier should create a new user record.
    
    Validates: Requirements 4.2
    """
    session = TestSessionLocal()
    try:
        # Create a source for the request
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Verify the user doesn't exist before creating the request
        existing_user = session.query(User).filter(User.identifier == user_identifier).first()
        assert existing_user is None, f"User with identifier '{user_identifier}' should not exist before test"
        
        # Create request service
        request_service = RequestService(session)
        
        # Create the request with a new user_identifier
        request = request_service.create_request(
            user_identifier=user_identifier,
            source_id=source.id,
            message=message
        )
        
        session.commit()
        
        # Verify a new user was created
        created_user = session.query(User).filter(User.identifier == user_identifier).first()
        assert created_user is not None, f"User with identifier '{user_identifier}' should have been created"
        assert created_user.identifier == user_identifier, \
            f"Created user should have identifier '{user_identifier}', got '{created_user.identifier}'"
        
        # Verify the request is associated with the newly created user
        assert request.user_id == created_user.id, \
            f"Request should be associated with user {created_user.id}, got {request.user_id}"
        
        # Verify only one user was created with this identifier
        user_count = session.query(User).filter(User.identifier == user_identifier).count()
        assert user_count == 1, f"Expected exactly 1 user with identifier '{user_identifier}', got {user_count}"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
