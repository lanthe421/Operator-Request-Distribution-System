"""
Property-based tests for operator assignment validation.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models.operator import Operator
from app.models.source import Source
from app.models.request import Request
from app.models.user import User
from app.models.operator_source_weight import OperatorSourceWeight
from app.services.request_service import RequestService
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
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
    weight=st.integers(min_value=1, max_value=100)
)
def test_operator_assignment_validation_for_active_operators(
    operator_name: str,
    max_load: int,
    source_name: str,
    user_identifier: str,
    message: str,
    weight: int
):
    """
    Feature: operator-request-distribution, Property 29: Operator assignment validation
    
    For any operator assignment, the system should ensure the operator exists and 
    is active at the time of assignment.
    
    Validates: Requirements 10.1
    """
    session = TestSessionLocal()
    try:
        # Create an active operator
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
        
        # Configure weight for operator-source
        operator_weight = OperatorSourceWeight(
            operator_id=operator.id,
            source_id=source.id,
            weight=weight
        )
        session.add(operator_weight)
        session.commit()
        
        # Create request service
        request_service = RequestService(session)
        
        # Create a request (should be assigned to the active operator)
        request = request_service.create_request(
            user_identifier=user_identifier,
            source_id=source.id,
            message=message
        )
        session.commit()
        
        # Verify the operator was assigned and is active
        if request.operator_id is not None:
            assigned_operator = session.query(Operator).filter(
                Operator.id == request.operator_id
            ).first()
            
            assert assigned_operator is not None, "Assigned operator should exist"
            assert assigned_operator.is_active is True, \
                "Assigned operator should be active at time of assignment"
            assert assigned_operator.id == operator.id, \
                "Request should be assigned to the created operator"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(OperatorSourceWeight).delete()
        session.query(User).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.commit()
        session.close()


@settings(max_examples=100, deadline=2000)
@given(
    operator_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    max_load=st.integers(min_value=1, max_value=50),
    source_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    user_identifier=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
    weight=st.integers(min_value=1, max_value=100)
)
def test_operator_assignment_validation_rejects_inactive_operators(
    operator_name: str,
    max_load: int,
    source_name: str,
    user_identifier: str,
    message: str,
    weight: int
):
    """
    Feature: operator-request-distribution, Property 29: Operator assignment validation
    
    The system should not assign requests to inactive operators.
    
    Validates: Requirements 10.1
    """
    session = TestSessionLocal()
    try:
        # Create an inactive operator
        operator = Operator(
            name=operator_name,
            is_active=False,  # Inactive
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
        
        # Configure weight for operator-source
        operator_weight = OperatorSourceWeight(
            operator_id=operator.id,
            source_id=source.id,
            weight=weight
        )
        session.add(operator_weight)
        session.commit()
        
        # Create request service
        request_service = RequestService(session)
        
        # Create a request (should NOT be assigned to the inactive operator)
        request = request_service.create_request(
            user_identifier=user_identifier,
            source_id=source.id,
            message=message
        )
        session.commit()
        
        # Verify the inactive operator was NOT assigned
        assert request.operator_id is None or request.operator_id != operator.id, \
            "Inactive operator should not be assigned to requests"
        
        # If an operator was assigned, verify it's active
        if request.operator_id is not None:
            assigned_operator = session.query(Operator).filter(
                Operator.id == request.operator_id
            ).first()
            assert assigned_operator.is_active is True, \
                "Only active operators should be assigned"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(OperatorSourceWeight).delete()
        session.query(User).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.commit()
        session.close()


@settings(max_examples=100, deadline=2000)
@given(
    operator_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    source_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    user_identifier=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
    weight=st.integers(min_value=1, max_value=100)
)
def test_operator_assignment_validation_rejects_at_capacity_operators(
    operator_name: str,
    source_name: str,
    user_identifier: str,
    message: str,
    weight: int
):
    """
    Feature: operator-request-distribution, Property 29: Operator assignment validation
    
    The system should not assign requests to operators at maximum capacity.
    
    Validates: Requirements 10.1
    """
    session = TestSessionLocal()
    try:
        # Create an operator at maximum capacity
        max_load = 5
        operator = Operator(
            name=operator_name,
            is_active=True,
            max_load_limit=max_load,
            current_load=max_load  # At capacity
        )
        session.add(operator)
        session.commit()
        
        # Create a source
        source_identifier = f"src_{source_name[:20]}"
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        
        # Configure weight for operator-source
        operator_weight = OperatorSourceWeight(
            operator_id=operator.id,
            source_id=source.id,
            weight=weight
        )
        session.add(operator_weight)
        session.commit()
        
        # Create request service
        request_service = RequestService(session)
        
        # Create a request (should NOT be assigned to the at-capacity operator)
        request = request_service.create_request(
            user_identifier=user_identifier,
            source_id=source.id,
            message=message
        )
        session.commit()
        
        # Verify the at-capacity operator was NOT assigned
        assert request.operator_id is None or request.operator_id != operator.id, \
            "Operator at maximum capacity should not be assigned to new requests"
        
        # If an operator was assigned, verify it's not at capacity
        if request.operator_id is not None:
            assigned_operator = session.query(Operator).filter(
                Operator.id == request.operator_id
            ).first()
            assert assigned_operator.current_load < assigned_operator.max_load_limit, \
                "Only operators below capacity should be assigned"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(OperatorSourceWeight).delete()
        session.query(User).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
