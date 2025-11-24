"""
Property-based tests for weight storage.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
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
    weight=st.integers(min_value=1, max_value=100)
)
def test_weight_storage_within_valid_range(
    operator_name: str,
    source_name: str,
    source_identifier: str,
    weight: int
):
    """
    Feature: operator-request-distribution, Property 7: Weight storage within valid range
    
    For any operator-source pair and weight value between 1 and 100,
    assigning the weight should store it correctly.
    
    Validates: Requirements 3.1
    """
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
        
        # Configure weight using service
        service = SourceService(session)
        service.configure_weights(source.id, [(operator.id, weight)])
        
        # Verify weight was stored correctly
        stored_weight = (
            session.query(OperatorSourceWeight)
            .filter(
                OperatorSourceWeight.operator_id == operator.id,
                OperatorSourceWeight.source_id == source.id
            )
            .first()
        )
        
        assert stored_weight is not None, "Weight configuration should be stored"
        assert stored_weight.weight == weight, f"Expected weight to be {weight}, got {stored_weight.weight}"
        assert stored_weight.operator_id == operator.id, f"Expected operator_id to be {operator.id}"
        assert stored_weight.source_id == source.id, f"Expected source_id to be {source.id}"
        
    finally:
        # Clean up
        session.query(OperatorSourceWeight).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
