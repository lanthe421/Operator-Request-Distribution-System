"""
Property-based tests for available operator identification.

**Feature: operator-request-distribution, Property 15: Available operator identification**
**Validates: Requirements 5.1, 5.2**
"""
from hypothesis import given, strategies as st, settings
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.operator import Operator
from app.models.source import Source
from app.models.operator_source_weight import OperatorSourceWeight
from app.services.distribution_service import DistributionService


# Strategies for generating test data
operator_name_strategy = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
max_load_strategy = st.integers(min_value=1, max_value=20)
current_load_strategy = st.integers(min_value=0, max_value=20)
weight_strategy = st.integers(min_value=1, max_value=100)
is_active_strategy = st.booleans()


@given(
    is_active=is_active_strategy,
    max_load_limit=max_load_strategy,
    current_load=current_load_strategy,
    weight=weight_strategy
)
@settings(max_examples=100, deadline=None)
def test_available_operator_identification(
    is_active: bool,
    max_load_limit: int,
    current_load: int,
    weight: int
):
    """
    Property: For any operator, it should be identified as available only if:
    - is_active equals True
    - current_load < max_load_limit
    - weight is configured for the source
    
    **Feature: operator-request-distribution, Property 15: Available operator identification**
    **Validates: Requirements 5.1, 5.2**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_{is_active}_{current_load}")
        session.add(source)
        session.flush()
        
        # Create an operator with the given properties
        operator = Operator(
            name=f"Operator_{is_active}_{current_load}",
            is_active=is_active,
            max_load_limit=max_load_limit,
            current_load=current_load
        )
        session.add(operator)
        session.flush()
        
        # Create weight configuration for operator-source pair
        weight_config = OperatorSourceWeight(
            operator_id=operator.id,
            source_id=source.id,
            weight=weight
        )
        session.add(weight_config)
        session.flush()
        
        # Test: Get available operators
        distribution_service = DistributionService(session)
        available_operators = distribution_service.get_available_operators(source.id)
        
        # Verify: Operator should be available only if all conditions are met
        expected_available = is_active and (current_load < max_load_limit)
        
        if expected_available:
            # Operator should be in the available list
            assert len(available_operators) == 1, \
                f"Expected 1 available operator, got {len(available_operators)}"
            assert available_operators[0][0].id == operator.id, \
                f"Expected operator {operator.id} to be available"
            assert available_operators[0][1] == weight, \
                f"Expected weight {weight}, got {available_operators[0][1]}"
        else:
            # Operator should NOT be in the available list
            assert len(available_operators) == 0, \
                f"Expected 0 available operators, got {len(available_operators)}"
        
        session.commit()
    finally:
        session.close()


@given(
    num_operators=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_multiple_operators_availability(num_operators: int):
    """
    Property: For any set of operators, only those meeting all availability
    criteria should be returned.
    
    **Feature: operator-request-distribution, Property 15: Available operator identification**
    **Validates: Requirements 5.1, 5.2**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_multi_{num_operators}")
        session.add(source)
        session.flush()
        
        expected_available_count = 0
        
        # Create multiple operators with varying properties
        for i in range(num_operators):
            # Vary the properties to test different combinations
            is_active = i % 2 == 0  # Alternate active/inactive
            max_load_limit = 5
            current_load = i % 6  # 0, 1, 2, 3, 4, 5 (last one at capacity)
            
            operator = Operator(
                name=f"Operator_{i}",
                is_active=is_active,
                max_load_limit=max_load_limit,
                current_load=current_load
            )
            session.add(operator)
            session.flush()
            
            # Add weight configuration
            weight_config = OperatorSourceWeight(
                operator_id=operator.id,
                source_id=source.id,
                weight=50
            )
            session.add(weight_config)
            session.flush()
            
            # Count expected available operators
            if is_active and current_load < max_load_limit:
                expected_available_count += 1
        
        # Test: Get available operators
        distribution_service = DistributionService(session)
        available_operators = distribution_service.get_available_operators(source.id)
        
        # Verify: Count matches expected
        assert len(available_operators) == expected_available_count, \
            f"Expected {expected_available_count} available operators, got {len(available_operators)}"
        
        # Verify: All returned operators meet the criteria
        for operator, weight in available_operators:
            assert operator.is_active is True, \
                f"Operator {operator.id} is not active but was returned as available"
            assert operator.current_load < operator.max_load_limit, \
                f"Operator {operator.id} is at capacity but was returned as available"
        
        session.commit()
    finally:
        session.close()


@given(
    has_weight=st.booleans()
)
@settings(max_examples=100, deadline=None)
def test_operator_without_weight_not_available(has_weight: bool):
    """
    Property: For any operator without a configured weight for a source,
    it should not be identified as available for that source.
    
    **Feature: operator-request-distribution, Property 15: Available operator identification**
    **Validates: Requirements 5.1, 5.2**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_weight_{has_weight}")
        session.add(source)
        session.flush()
        
        # Create an active operator with available capacity
        operator = Operator(
            name="Available Operator",
            is_active=True,
            max_load_limit=10,
            current_load=0
        )
        session.add(operator)
        session.flush()
        
        # Conditionally add weight configuration
        if has_weight:
            weight_config = OperatorSourceWeight(
                operator_id=operator.id,
                source_id=source.id,
                weight=50
            )
            session.add(weight_config)
            session.flush()
        
        # Test: Get available operators
        distribution_service = DistributionService(session)
        available_operators = distribution_service.get_available_operators(source.id)
        
        # Verify: Operator should be available only if weight is configured
        if has_weight:
            assert len(available_operators) == 1, \
                f"Expected 1 available operator with weight, got {len(available_operators)}"
        else:
            assert len(available_operators) == 0, \
                f"Expected 0 available operators without weight, got {len(available_operators)}"
        
        session.commit()
    finally:
        session.close()
