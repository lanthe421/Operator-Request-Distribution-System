"""
Property-based tests for cascade deletion prevention.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.models.operator import Operator
from app.models.source import Source
from app.models.request import Request
from app.models.user import User
from app.models.operator_source_weight import OperatorSourceWeight
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
    operator_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    max_load=st.integers(min_value=1, max_value=50),
    source_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    user_identifier=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
)
def test_cascade_deletion_prevention_for_operators_with_requests(
    operator_name: str,
    max_load: int,
    source_name: str,
    user_identifier: str,
    message: str
):
    """
    Feature: operator-request-distribution, Property 30: Cascade deletion prevention
    
    For any operator that has assigned requests, attempting to delete it should 
    be prevented by the system.
    
    Validates: Requirements 10.4
    """
    session = TestSessionLocal()
    try:
        # Create an operator
        operator = Operator(
            name=operator_name,
            is_active=True,
            max_load_limit=max_load,
            current_load=0
        )
        session.add(operator)
        session.commit()
        
        # Create a source
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Create a user
        user = User(identifier=user_identifier)
        session.add(user)
        session.commit()
        
        # Create a request assigned to the operator
        request = Request(
            user_id=user.id,
            source_id=source.id,
            operator_id=operator.id,
            message=message,
            status="assigned"
        )
        session.add(request)
        session.commit()
        
        # Try to delete the operator (should fail due to foreign key constraint)
        session.delete(operator)
        
        with pytest.raises(IntegrityError):
            session.commit()
        
        session.rollback()
        
        # Verify the operator still exists
        existing_operator = session.query(Operator).filter(
            Operator.id == operator.id
        ).first()
        assert existing_operator is not None, \
            "Operator with assigned requests should not be deleted"
        
    finally:
        # Clean up (delete in correct order)
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.commit()
        session.close()


@settings(max_examples=100, deadline=2000)
@given(
    source_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    user_identifier=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
)
def test_cascade_deletion_prevention_for_sources_with_requests(
    source_name: str,
    user_identifier: str,
    message: str
):
    """
    Feature: operator-request-distribution, Property 30: Cascade deletion prevention
    
    For any source that has associated requests, attempting to delete it should 
    be prevented by the system.
    
    Validates: Requirements 10.5
    """
    session = TestSessionLocal()
    try:
        # Create a source
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Create a user
        user = User(identifier=user_identifier)
        session.add(user)
        session.commit()
        
        # Create a request associated with the source
        request = Request(
            user_id=user.id,
            source_id=source.id,
            operator_id=None,
            message=message,
            status="pending"
        )
        session.add(request)
        session.commit()
        
        # Try to delete the source (should fail due to foreign key constraint)
        session.delete(source)
        
        with pytest.raises(IntegrityError):
            session.commit()
        
        session.rollback()
        
        # Verify the source still exists
        existing_source = session.query(Source).filter(
            Source.id == source.id
        ).first()
        assert existing_source is not None, \
            "Source with associated requests should not be deleted"
        
    finally:
        # Clean up (delete in correct order)
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Source).delete()
        session.commit()
        session.close()


@settings(max_examples=100, deadline=2000)
@given(
    operator_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    max_load=st.integers(min_value=1, max_value=50)
)
def test_cascade_deletion_allows_operators_without_requests(
    operator_name: str,
    max_load: int
):
    """
    Feature: operator-request-distribution, Property 30: Cascade deletion prevention
    
    Operators without assigned requests should be allowed to be deleted.
    
    Validates: Requirements 10.4
    """
    session = TestSessionLocal()
    try:
        # Create an operator
        operator = Operator(
            name=operator_name,
            is_active=True,
            max_load_limit=max_load,
            current_load=0
        )
        session.add(operator)
        session.commit()
        
        operator_id = operator.id
        
        # Delete the operator (should succeed since no requests are assigned)
        session.delete(operator)
        session.commit()
        
        # Verify the operator was deleted
        deleted_operator = session.query(Operator).filter(
            Operator.id == operator_id
        ).first()
        assert deleted_operator is None, \
            "Operator without assigned requests should be deletable"
        
    finally:
        # Clean up
        session.query(Operator).delete()
        session.commit()
        session.close()


@settings(max_examples=100, deadline=2000)
@given(
    source_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
)
def test_cascade_deletion_allows_sources_without_requests(
    source_name: str
):
    """
    Feature: operator-request-distribution, Property 30: Cascade deletion prevention
    
    Sources without associated requests should be allowed to be deleted.
    
    Validates: Requirements 10.5
    """
    session = TestSessionLocal()
    try:
        # Create a source
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        source_id = source.id
        
        # Delete the source (should succeed since no requests are associated)
        session.delete(source)
        session.commit()
        
        # Verify the source was deleted
        deleted_source = session.query(Source).filter(
            Source.id == source_id
        ).first()
        assert deleted_source is None, \
            "Source without associated requests should be deletable"
        
    finally:
        # Clean up
        session.query(Source).delete()
        session.commit()
        session.close()
