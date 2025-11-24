"""
Property-based tests for Operator model.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.operator import Operator
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


@settings(max_examples=100, deadline=1000)
@given(
    name=st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
    max_load_limit=st.integers(min_value=1, max_value=1000)
)
def test_operator_creation_initializes_correctly(name: str, max_load_limit: int):
    """
    Feature: operator-request-distribution, Property 1: Operator creation initializes state correctly
    
    For any operator created with a valid name and max_load_limit,
    the operator should be stored with is_active set to True and current_load set to 0.
    
    Validates: Requirements 1.1
    """
    session = TestSessionLocal()
    try:
        # Create operator
        operator = Operator(
            name=name,
            max_load_limit=max_load_limit
        )
        
        session.add(operator)
        session.commit()
        session.refresh(operator)
        
        # Verify initialization
        assert operator.is_active is True, f"Expected is_active to be True, got {operator.is_active}"
        assert operator.current_load == 0, f"Expected current_load to be 0, got {operator.current_load}"
        assert operator.name == name, f"Expected name to be '{name}', got '{operator.name}'"
        assert operator.max_load_limit == max_load_limit, f"Expected max_load_limit to be {max_load_limit}, got {operator.max_load_limit}"
        assert operator.id is not None, "Expected operator to have an ID after commit"
        assert operator.created_at is not None, "Expected operator to have a created_at timestamp"
        
    finally:
        # Clean up
        session.query(Operator).delete()
        session.commit()
        session.close()


