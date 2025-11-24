"""
Property-based tests for weight update.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.operator import Operator
from app.models.source import Source
from app.models.operator_source_weight import OperatorSourceWeight
from app.services.source_service import SourceService
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
    operator_name=st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
    source_name=st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
    source_identifier=st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
    initial_weight=st.integers(min_value=1, max_value=100),
    new_weight=st.integers(min_value=1, max_value=100)
)
def test_weight_update_modifies_existing_value(
    operator_name: str,
    source_name: str,
    source_identifier: str,
    initial_weight: int,
    new_weight: int
):
    """
    Feature: operator-request-distribution, Property 8: Weight update modifies existing value
    
    For any existing operator-source weight configuration,
    updating the weight should change it to the new value.
    
    Validates: Requirements 3.2
    """
    # Ensure initial and new weights are different to test actual update
    assume(initial_weight != new_weight)
    
    session = TestSessionLocal()
    try:
        # Create operator
        operator = Operator(name=operator_name, max_load_limit=10)
        session.add(operator)
        session.commit()
        session.refresh(operator)
        
        # Create source
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        session.refresh(source)
        
        # Configure initial weight using service
        service = SourceService(session)
        service.configure_weights(source.id, [(operator.id, initial_weight)])
        
        # Verify initial weight was stored
        stored_weight = (
            session.query(OperatorSourceWeight)
            .filter(
                OperatorSourceWeight.operator_id == operator.id,
                OperatorSourceWeight.source_id == source.id
            )
            .first()
        )
        assert stored_weight is not None, "Initial weight configuration should be stored"
        assert stored_weight.weight == initial_weight, f"Expected initial weight to be {initial_weight}"
        
        # Update weight to new value
        service.configure_weights(source.id, [(operator.id, new_weight)])
        
        # Refresh to get updated value
        session.refresh(stored_weight)
        
        # Verify weight was updated
        assert stored_weight.weight == new_weight, f"Expected weight to be updated to {new_weight}, got {stored_weight.weight}"
        
        # Verify only one weight configuration exists (no duplicates)
        weight_count = (
            session.query(OperatorSourceWeight)
            .filter(
                OperatorSourceWeight.operator_id == operator.id,
                OperatorSourceWeight.source_id == source.id
            )
            .count()
        )
        assert weight_count == 1, f"Expected exactly 1 weight configuration, found {weight_count}"
        
    finally:
        # Clean up
        session.query(OperatorSourceWeight).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
