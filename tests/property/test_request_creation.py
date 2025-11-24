"""
Property-based tests for request creation operations.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine, text
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
def test_request_creation_stores_all_data(user_identifier: str, source_name: str, message: str):
    """
    Feature: operator-request-distribution, Property 11: Request creation stores all data
    
    For any valid user_identifier, source_id, and message, creating a request should
    store a new request record with all provided data.
    
    Validates: Requirements 4.1
    """
    session = TestSessionLocal()
    try:
        # Create a source for the request
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Create request service
        request_service = RequestService(session)
        
        # Create the request
        request = request_service.create_request(
            user_identifier=user_identifier,
            source_id=source.id,
            message=message
        )
        
        session.commit()
        
        # Verify the request was created and stored with all data
        assert request.id is not None, "Request should have an ID after creation"
        assert request.user_id is not None, "Request should have a user_id"
        assert request.source_id == source.id, f"Request source_id should be {source.id}, got {request.source_id}"
        assert request.message == message, f"Request message should be '{message}', got '{request.message}'"
        assert request.status in ["pending", "assigned", "waiting"], \
            f"Request status should be valid, got '{request.status}'"
        assert request.created_at is not None, "Request should have a created_at timestamp"
        
        # Verify the request can be retrieved from database
        retrieved_request = session.query(Request).filter(Request.id == request.id).first()
        assert retrieved_request is not None, "Request should be retrievable from database"
        assert retrieved_request.message == message, "Retrieved request should have the same message"
        assert retrieved_request.source_id == source.id, "Retrieved request should have the same source_id"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
