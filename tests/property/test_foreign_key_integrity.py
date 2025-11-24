"""
Property-based tests for foreign key integrity.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.models.source import Source
from app.models.request import Request
from app.models.user import User
from app.core.database import Base


# Create a separate in-memory database for testing
test_engine = create_engine("sqlite:///:memory:", echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Enable foreign key constraints for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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
def test_foreign_key_integrity_for_valid_references(
    user_identifier: str, 
    source_name: str, 
    message: str
):
    """
    Feature: operator-request-distribution, Property 28: Foreign key integrity
    
    For any request, the system should ensure that the referenced source_id and 
    user_id exist in their respective tables.
    
    Validates: Requirements 10.2, 10.3
    """
    session = TestSessionLocal()
    try:
        # Create a valid user
        user = User(identifier=user_identifier)
        session.add(user)
        session.commit()
        
        # Create a valid source
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Create a request with valid foreign keys
        request = Request(
            user_id=user.id,
            source_id=source.id,
            message=message,
            status="pending"
        )
        session.add(request)
        session.commit()
        
        # Verify the request was created successfully
        assert request.id is not None, "Request should be created with valid foreign keys"
        
        # Verify relationships are intact
        retrieved_request = session.query(Request).filter(Request.id == request.id).first()
        assert retrieved_request.user_id == user.id, "Request should reference the correct user"
        assert retrieved_request.source_id == source.id, "Request should reference the correct source"
        
        # Verify we can access related objects
        assert retrieved_request.user is not None, "Request should have access to user relationship"
        assert retrieved_request.source is not None, "Request should have access to source relationship"
        assert retrieved_request.user.identifier == user_identifier
        assert retrieved_request.source.name == source_name
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Source).delete()
        session.commit()
        session.close()


@settings(max_examples=50, deadline=2000)
@given(
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
    invalid_id=st.integers(min_value=99999, max_value=999999)
)
def test_foreign_key_integrity_rejects_invalid_source(message: str, invalid_id: int):
    """
    Feature: operator-request-distribution, Property 28: Foreign key integrity
    
    The system should reject requests with non-existent source_id.
    
    Validates: Requirements 10.2
    """
    session = TestSessionLocal()
    try:
        # Create a valid user
        user = User(identifier=f"user_{invalid_id}")
        session.add(user)
        session.commit()
        
        # Ensure the invalid_id doesn't exist as a source
        existing_source = session.query(Source).filter(Source.id == invalid_id).first()
        if existing_source:
            pytest.skip("Generated ID already exists")
        
        # Try to create a request with invalid source_id
        request = Request(
            user_id=user.id,
            source_id=invalid_id,  # Non-existent source
            message=message,
            status="pending"
        )
        session.add(request)
        
        # This should fail due to foreign key constraint
        with pytest.raises(IntegrityError):
            session.commit()
        
        session.rollback()
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(User).delete()
        session.commit()
        session.close()


@settings(max_examples=50, deadline=2000)
@given(
    source_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
    invalid_id=st.integers(min_value=99999, max_value=999999)
)
def test_foreign_key_integrity_rejects_invalid_user(
    source_name: str, 
    message: str, 
    invalid_id: int
):
    """
    Feature: operator-request-distribution, Property 28: Foreign key integrity
    
    The system should reject requests with non-existent user_id.
    
    Validates: Requirements 10.3
    """
    session = TestSessionLocal()
    try:
        # Create a valid source
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Ensure the invalid_id doesn't exist as a user
        existing_user = session.query(User).filter(User.id == invalid_id).first()
        if existing_user:
            pytest.skip("Generated ID already exists")
        
        # Try to create a request with invalid user_id
        request = Request(
            user_id=invalid_id,  # Non-existent user
            source_id=source.id,
            message=message,
            status="pending"
        )
        session.add(request)
        
        # This should fail due to foreign key constraint
        with pytest.raises(IntegrityError):
            session.commit()
        
        session.rollback()
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
