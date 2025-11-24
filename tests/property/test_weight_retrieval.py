"""
Property-based tests for weight retrieval completeness.
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


@settings(max_examples=100, deadline=2000)
@given(
    source_name=st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
    source_identifier=st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
    # Generate a list of operator configurations (name, weight)
    operator_configs=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),  # operator name
            st.integers(min_value=1, max_value=100)  # weight
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]  # Ensure unique operator names
    )
)
def test_weight_retrieval_completeness(
    source_name: str,
    source_identifier: str,
    operator_configs: list
):
    """
    Feature: operator-request-distribution, Property 10: Weight retrieval completeness
    
    For any source with configured operator weights,
    retrieving the weights should return all operators with their configured weights for that source.
    
    Validates: Requirements 3.4
    """
    session = TestSessionLocal()
    try:
        # Create source
        source = Source(name=source_name, identifier=source_identifier)
        session.add(source)
        session.commit()
        session.refresh(source)
        
        # Create operators and configure weights
        created_operators = []
        weight_configs = []
        
        for operator_name, weight in operator_configs:
            operator = Operator(name=operator_name, max_load_limit=10)
            session.add(operator)
            session.commit()
            session.refresh(operator)
            created_operators.append(operator)
            weight_configs.append((operator.id, weight))
        
        # Configure all weights using service
        service = SourceService(session)
        service.configure_weights(source.id, weight_configs)
        
        # Retrieve weights using service
        retrieved_weights = service.get_operator_weights(source.id)
        
        # Verify completeness: all configured operators should be returned
        assert len(retrieved_weights) == len(operator_configs), \
            f"Expected {len(operator_configs)} weight configurations, got {len(retrieved_weights)}"
        
        # Create a mapping of operator_id to (name, weight) for verification
        retrieved_map = {op_id: (name, weight) for op_id, name, weight in retrieved_weights}
        
        # Verify each configured operator is in the retrieved results with correct weight
        for operator, (expected_name, expected_weight) in zip(created_operators, operator_configs):
            assert operator.id in retrieved_map, \
                f"Operator {operator.id} ({expected_name}) not found in retrieved weights"
            
            retrieved_name, retrieved_weight = retrieved_map[operator.id]
            assert retrieved_name == expected_name, \
                f"Expected operator name '{expected_name}', got '{retrieved_name}'"
            assert retrieved_weight == expected_weight, \
                f"Expected weight {expected_weight} for operator {expected_name}, got {retrieved_weight}"
        
        # Verify no extra weights are returned
        retrieved_operator_ids = {op_id for op_id, _, _ in retrieved_weights}
        expected_operator_ids = {op.id for op in created_operators}
        assert retrieved_operator_ids == expected_operator_ids, \
            "Retrieved operator IDs should match exactly the configured operators"
        
    finally:
        # Clean up
        session.query(OperatorSourceWeight).delete()
        session.query(Operator).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
