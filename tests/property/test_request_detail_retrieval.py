"""
Property-based tests for request detail retrieval with relationships.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.source import Source
from app.models.request import Request
from app.models.user import User
from app.models.operator import Operator
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
    operator_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
    max_load=st.integers(min_value=1, max_value=100)
)
def test_request_detail_retrieval_with_relationships(
    user_identifier: str,
    source_name: str,
    operator_name: str,
    message: str,
    max_load: int
):
    """
    Feature: operator-request-distribution, Property 27: Request detail retrieval with relationships
    
    For any request ID, retrieving the request details should return the request with
    complete user, source, operator information, and creation timestamp.
    
    Validates: Requirements 9.1, 9.3
    """
    session = TestSessionLocal()
    try:
        # Create a source
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Create an operator
        operator = Operator(
            name=operator_name,
            max_load_limit=max_load,
            is_active=True,
            current_load=0
        )
        session.add(operator)
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
        
        # Retrieve the request by ID using the service method
        retrieved_request = request_service.get_request_by_id(request.id)
        
        # Verify the request was retrieved
        assert retrieved_request is not None, f"Request with ID {request.id} should be retrievable"
        
        # Verify basic request data
        assert retrieved_request.id == request.id, "Retrieved request should have the same ID"
        assert retrieved_request.message == message, "Retrieved request should have the same message"
        
        # Verify user relationship is loaded
        assert retrieved_request.user is not None, "Request should have user relationship loaded"
        assert retrieved_request.user.identifier == user_identifier, \
            f"User identifier should be '{user_identifier}', got '{retrieved_request.user.identifier}'"
        
        # Verify source relationship is loaded
        assert retrieved_request.source is not None, "Request should have source relationship loaded"
        assert retrieved_request.source.name == source_name, \
            f"Source name should be '{source_name}', got '{retrieved_request.source.name}'"
        assert retrieved_request.source.identifier == source_identifier, \
            f"Source identifier should be '{source_identifier}', got '{retrieved_request.source.identifier}'"
        
        # Verify operator relationship is loaded (may be None if no operator was assigned)
        # The operator relationship should be accessible without additional queries
        if retrieved_request.operator_id is not None:
            assert retrieved_request.operator is not None, \
                "If operator_id is set, operator relationship should be loaded"
            # Verify we can access operator attributes without triggering additional queries
            operator_name_from_request = retrieved_request.operator.name
            assert operator_name_from_request is not None, "Operator name should be accessible"
        
        # Verify creation timestamp is included
        assert retrieved_request.created_at is not None, "Request should have creation timestamp"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
