"""
Property-based tests for request timestamp recording.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

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
def test_request_timestamp_recording(user_identifier: str, source_name: str, message: str):
    """
    Feature: operator-request-distribution, Property 14: Request timestamp recording
    
    For any created request, the request should have a creation timestamp that is
    set and represents a valid datetime.
    
    Validates: Requirements 4.5
    """
    session = TestSessionLocal()
    try:
        # Create a source for the request
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Record time before creating request
        time_before = datetime.utcnow()
        
        # Create request service
        request_service = RequestService(session)
        
        # Create the request
        request = request_service.create_request(
            user_identifier=user_identifier,
            source_id=source.id,
            message=message
        )
        
        session.commit()
        
        # Record time after creating request
        time_after = datetime.utcnow()
        
        # Verify the request has a created_at timestamp
        assert request.created_at is not None, "Request should have a created_at timestamp"
        
        # Verify it's a datetime object
        assert isinstance(request.created_at, datetime), \
            f"created_at should be a datetime object, got {type(request.created_at)}"
        
        # Verify the timestamp is reasonable (between before and after)
        assert time_before <= request.created_at <= time_after, \
            f"Timestamp {request.created_at} should be between {time_before} and {time_after}"
        
        # Verify the timestamp is persisted in the database
        retrieved_request = session.query(Request).filter(Request.id == request.id).first()
        assert retrieved_request is not None, "Request should be retrievable from database"
        assert retrieved_request.created_at is not None, "Retrieved request should have created_at timestamp"
        assert retrieved_request.created_at == request.created_at, \
            "Retrieved request should have the same timestamp as the original"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
