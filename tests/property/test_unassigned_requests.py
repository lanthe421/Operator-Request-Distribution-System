"""
Property-based tests for unassigned request handling.

**Feature: operator-request-distribution, Property 17: Unassigned request handling**
**Validates: Requirements 5.5**
"""
from hypothesis import given, strategies as st, settings
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.operator import Operator
from app.models.source import Source
from app.models.user import User
from app.models.request import Request
from app.models.operator_source_weight import OperatorSourceWeight
from app.services.distribution_service import DistributionService


# Strategies for generating test data
message_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())


@given(
    message=message_strategy
)
@settings(max_examples=100, deadline=None)
def test_unassigned_request_when_no_operators(message: str):
    """
    Property: For any request created when no available operators exist,
    the request should be created with operator_id set to NULL and status
    set to 'waiting'.
    
    **Feature: operator-request-distribution, Property 17: Unassigned request handling**
    **Validates: Requirements 5.5**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_no_ops")
        session.add(source)
        session.flush()
        
        # Create a user
        user = User(identifier=f"test_user_no_ops")
        session.add(user)
        session.flush()
        
        # Create a request (no operators available)
        request = Request(
            user_id=user.id,
            source_id=source.id,
            message=message,
            status="pending"
        )
        session.add(request)
        session.flush()
        
        # Test: Handle no operators available
        distribution_service = DistributionService(session)
        distribution_service.handle_no_operators_available(request.id)
        
        # Refresh request to get updated values
        session.refresh(request)
        
        # Verify: operator_id is NULL
        assert request.operator_id is None, \
            f"Expected operator_id to be NULL, got {request.operator_id}"
        
        # Verify: status is 'waiting'
        assert request.status == "waiting", \
            f"Expected status to be 'waiting', got '{request.status}'"
        
        session.commit()
    finally:
        session.close()


@given(
    all_inactive=st.booleans()
)
@settings(max_examples=100, deadline=None)
def test_unassigned_when_operators_inactive(all_inactive: bool):
    """
    Property: For any request when all operators are inactive,
    the request should remain unassigned with status 'waiting'.
    
    **Feature: operator-request-distribution, Property 17: Unassigned request handling**
    **Validates: Requirements 5.5**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_inactive_{all_inactive}")
        session.add(source)
        session.flush()
        
        # Create a user
        user = User(identifier=f"test_user_inactive_{all_inactive}")
        session.add(user)
        session.flush()
        
        # Create operators (all inactive if all_inactive is True)
        for i in range(3):
            operator = Operator(
                name=f"Operator_{i}",
                is_active=not all_inactive,  # inactive if all_inactive is True
                max_load_limit=10,
                current_load=0
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
        
        # Create a request
        request = Request(
            user_id=user.id,
            source_id=source.id,
            message="Test message",
            status="pending"
        )
        session.add(request)
        session.flush()
        
        # Test: Distribute request
        distribution_service = DistributionService(session)
        assigned_operator_id = distribution_service.distribute_request(request.id, source.id)
        
        # Refresh request
        session.refresh(request)
        
        if all_inactive:
            # Verify: No operator assigned
            assert assigned_operator_id is None, \
                f"Expected no operator assigned, got {assigned_operator_id}"
            assert request.operator_id is None, \
                f"Expected operator_id to be NULL, got {request.operator_id}"
            assert request.status == "waiting", \
                f"Expected status to be 'waiting', got '{request.status}'"
        else:
            # Verify: Operator assigned
            assert assigned_operator_id is not None, \
                "Expected operator to be assigned"
            assert request.operator_id is not None, \
                "Expected operator_id to be set"
            assert request.status == "assigned", \
                f"Expected status to be 'assigned', got '{request.status}'"
        
        session.commit()
    finally:
        session.close()


@given(
    num_operators=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_unassigned_when_all_at_capacity(num_operators: int):
    """
    Property: For any request when all operators are at maximum capacity,
    the request should remain unassigned with status 'waiting'.
    
    **Feature: operator-request-distribution, Property 17: Unassigned request handling**
    **Validates: Requirements 5.5**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_capacity_{num_operators}")
        session.add(source)
        session.flush()
        
        # Create a user
        user = User(identifier=f"test_user_capacity_{num_operators}")
        session.add(user)
        session.flush()
        
        # Create operators all at maximum capacity
        for i in range(num_operators):
            max_load = 5
            operator = Operator(
                name=f"Operator_{i}",
                is_active=True,
                max_load_limit=max_load,
                current_load=max_load  # At capacity
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
        
        # Create a request
        request = Request(
            user_id=user.id,
            source_id=source.id,
            message="Test message",
            status="pending"
        )
        session.add(request)
        session.flush()
        
        # Test: Distribute request
        distribution_service = DistributionService(session)
        assigned_operator_id = distribution_service.distribute_request(request.id, source.id)
        
        # Refresh request
        session.refresh(request)
        
        # Verify: No operator assigned (all at capacity)
        assert assigned_operator_id is None, \
            f"Expected no operator assigned, got {assigned_operator_id}"
        assert request.operator_id is None, \
            f"Expected operator_id to be NULL, got {request.operator_id}"
        assert request.status == "waiting", \
            f"Expected status to be 'waiting', got '{request.status}'"
        
        session.commit()
    finally:
        session.close()


@given(
    has_weight_config=st.booleans()
)
@settings(max_examples=100, deadline=None)
def test_unassigned_when_no_weight_configured(has_weight_config: bool):
    """
    Property: For any request when operators have no weight configured for the source,
    the request should remain unassigned with status 'waiting'.
    
    **Feature: operator-request-distribution, Property 17: Unassigned request handling**
    **Validates: Requirements 5.5**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_weight_{has_weight_config}")
        session.add(source)
        session.flush()
        
        # Create a user
        user = User(identifier=f"test_user_weight_{has_weight_config}")
        session.add(user)
        session.flush()
        
        # Create an active operator with available capacity
        operator = Operator(
            name="Operator_1",
            is_active=True,
            max_load_limit=10,
            current_load=0
        )
        session.add(operator)
        session.flush()
        
        # Conditionally add weight configuration
        if has_weight_config:
            weight_config = OperatorSourceWeight(
                operator_id=operator.id,
                source_id=source.id,
                weight=50
            )
            session.add(weight_config)
            session.flush()
        
        # Create a request
        request = Request(
            user_id=user.id,
            source_id=source.id,
            message="Test message",
            status="pending"
        )
        session.add(request)
        session.flush()
        
        # Test: Distribute request
        distribution_service = DistributionService(session)
        assigned_operator_id = distribution_service.distribute_request(request.id, source.id)
        
        # Refresh request
        session.refresh(request)
        
        if has_weight_config:
            # Verify: Operator assigned
            assert assigned_operator_id is not None, \
                "Expected operator to be assigned"
            assert request.operator_id is not None, \
                "Expected operator_id to be set"
            assert request.status == "assigned", \
                f"Expected status to be 'assigned', got '{request.status}'"
        else:
            # Verify: No operator assigned (no weight configured)
            assert assigned_operator_id is None, \
                f"Expected no operator assigned, got {assigned_operator_id}"
            assert request.operator_id is None, \
                f"Expected operator_id to be NULL, got {request.operator_id}"
            assert request.status == "waiting", \
                f"Expected status to be 'waiting', got '{request.status}'"
        
        session.commit()
    finally:
        session.close()
