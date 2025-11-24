"""
Property-based tests for operator update operations.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.operator import Operator
from app.repositories.operator_repository import OperatorRepository
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
    initial_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    initial_max_load=st.integers(min_value=1, max_value=100),
    new_max_load=st.integers(min_value=1, max_value=100)
)
def test_operator_update_modifies_max_load_limit(
    initial_name: str,
    initial_max_load: int,
    new_max_load: int
):
    """
    Feature: operator-request-distribution, Property 2: Operator update modifies max_load_limit
    
    For any existing operator and new max_load_limit value, updating the operator
    should result in the max_load_limit being changed to the new value.
    
    Validates: Requirements 1.3
    """
    session = TestSessionLocal()
    try:
        # Create repository
        repo = OperatorRepository(session)
        
        # Create an operator
        operator = repo.create(name=initial_name, max_load_limit=initial_max_load)
        session.commit()
        
        # Store the operator ID
        operator_id = operator.id
        
        # Verify initial state
        assert operator.max_load_limit == initial_max_load, \
            f"Expected initial max_load_limit to be {initial_max_load}, got {operator.max_load_limit}"
        
        # Update the operator's max_load_limit
        operator.max_load_limit = new_max_load
        repo.update(operator)
        session.commit()
        
        # Retrieve the operator again to verify persistence
        updated_operator = repo.get_by_id(operator_id)
        
        assert updated_operator is not None, "Operator should still exist after update"
        assert updated_operator.max_load_limit == new_max_load, \
            f"Expected max_load_limit to be updated to {new_max_load}, got {updated_operator.max_load_limit}"
        
        # Verify other fields remain unchanged
        assert updated_operator.name == initial_name, \
            f"Name should remain unchanged, expected '{initial_name}', got '{updated_operator.name}'"
        assert updated_operator.is_active is True, \
            "is_active should remain unchanged"
        assert updated_operator.current_load == 0, \
            "current_load should remain unchanged"
        
    finally:
        # Clean up
        session.query(Operator).delete()
        session.commit()
        session.close()
