"""
Property-based tests for operator toggle active status.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.operator import Operator
from app.services.operator_service import OperatorService
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
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    max_load_limit=st.integers(min_value=1, max_value=100),
    initial_active=st.booleans()
)
def test_toggle_changes_active_status(
    name: str,
    max_load_limit: int,
    initial_active: bool
):
    """
    Feature: operator-request-distribution, Property 3: Toggle changes active status
    
    For any operator, toggling the active status should flip the is_active flag
    from True to False or False to True.
    
    Validates: Requirements 1.4
    """
    session = TestSessionLocal()
    try:
        # Create service
        service = OperatorService(session)
        
        # Create an operator
        operator = service.create_operator(name=name, max_load_limit=max_load_limit)
        session.commit()
        
        # Set initial active status
        operator.is_active = initial_active
        session.commit()
        
        # Store the operator ID and initial status
        operator_id = operator.id
        
        # Verify initial state
        assert operator.is_active == initial_active, \
            f"Expected initial is_active to be {initial_active}, got {operator.is_active}"
        
        # Toggle the active status
        toggled_operator = service.toggle_active(operator_id)
        session.commit()
        
        # Verify the status was toggled
        expected_status = not initial_active
        assert toggled_operator.is_active == expected_status, \
            f"Expected is_active to be toggled to {expected_status}, got {toggled_operator.is_active}"
        
        # Toggle again to verify it flips back
        toggled_again_operator = service.toggle_active(operator_id)
        session.commit()
        
        assert toggled_again_operator.is_active == initial_active, \
            f"Expected is_active to be toggled back to {initial_active}, got {toggled_again_operator.is_active}"
        
        # Verify other fields remain unchanged
        assert toggled_again_operator.name == name, \
            f"Name should remain unchanged, expected '{name}', got '{toggled_again_operator.name}'"
        assert toggled_again_operator.max_load_limit == max_load_limit, \
            f"max_load_limit should remain unchanged, expected {max_load_limit}, got {toggled_again_operator.max_load_limit}"
        assert toggled_again_operator.current_load == 0, \
            "current_load should remain unchanged"
        
    finally:
        # Clean up
        session.query(Operator).delete()
        session.commit()
        session.close()
