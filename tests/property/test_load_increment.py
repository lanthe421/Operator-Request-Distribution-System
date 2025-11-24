"""
Property-based tests for load increment on operator assignment.

**Feature: operator-request-distribution, Property 16: Load increment on assignment**
**Validates: Requirements 5.4**
"""
from hypothesis import given, strategies as st, settings
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.operator import Operator
from app.models.source import Source
from app.models.user import User
from app.models.request import Request
from app.services.distribution_service import DistributionService


# Strategies for generating test data
operator_name_strategy = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
initial_load_strategy = st.integers(min_value=0, max_value=10)


@given(
    initial_load=initial_load_strategy
)
@settings(max_examples=100, deadline=None)
def test_load_increment_on_assignment(initial_load: int):
    """
    Property: For any operator assigned to a request, the operator's current_load
    should increase by exactly 1.
    
    **Feature: operator-request-distribution, Property 16: Load increment on assignment**
    **Validates: Requirements 5.4**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_{initial_load}")
        session.add(source)
        session.flush()
        
        # Create a user
        user = User(identifier=f"test_user_{initial_load}")
        session.add(user)
        session.flush()
        
        # Create an operator with initial load
        operator = Operator(
            name=f"Operator_{initial_load}",
            is_active=True,
            max_load_limit=20,
            current_load=initial_load
        )
        session.add(operator)
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
        
        # Record the initial load
        load_before = operator.current_load
        
        # Test: Assign operator to request
        distribution_service = DistributionService(session)
        distribution_service.assign_operator(request.id, operator.id)
        
        # Refresh operator to get updated load
        session.refresh(operator)
        load_after = operator.current_load
        
        # Verify: Load increased by exactly 1
        assert load_after == load_before + 1, \
            f"Expected load to increase from {load_before} to {load_before + 1}, got {load_after}"
        
        # Verify: Request is assigned to the operator
        session.refresh(request)
        assert request.operator_id == operator.id, \
            f"Expected request to be assigned to operator {operator.id}, got {request.operator_id}"
        
        # Verify: Request status is updated to 'assigned'
        assert request.status == "assigned", \
            f"Expected request status to be 'assigned', got '{request.status}'"
        
        session.commit()
    finally:
        session.close()


@given(
    num_assignments=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_multiple_assignments_increment_load(num_assignments: int):
    """
    Property: For any operator, assigning multiple requests should increment
    the load by the number of assignments.
    
    **Feature: operator-request-distribution, Property 16: Load increment on assignment**
    **Validates: Requirements 5.4**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_multi_{num_assignments}")
        session.add(source)
        session.flush()
        
        # Create a user
        user = User(identifier=f"test_user_multi_{num_assignments}")
        session.add(user)
        session.flush()
        
        # Create an operator with initial load of 0
        operator = Operator(
            name="Test Operator",
            is_active=True,
            max_load_limit=20,
            current_load=0
        )
        session.add(operator)
        session.flush()
        
        initial_load = operator.current_load
        
        # Create and assign multiple requests
        distribution_service = DistributionService(session)
        
        for i in range(num_assignments):
            # Create a request
            request = Request(
                user_id=user.id,
                source_id=source.id,
                message=f"Test message {i}",
                status="pending"
            )
            session.add(request)
            session.flush()
            
            # Assign operator to request
            distribution_service.assign_operator(request.id, operator.id)
        
        # Refresh operator to get updated load
        session.refresh(operator)
        final_load = operator.current_load
        
        # Verify: Load increased by exactly num_assignments
        assert final_load == initial_load + num_assignments, \
            f"Expected load to increase from {initial_load} to {initial_load + num_assignments}, got {final_load}"
        
        session.commit()
    finally:
        session.close()


@given(
    initial_load=initial_load_strategy
)
@settings(max_examples=100, deadline=None)
def test_assignment_is_atomic(initial_load: int):
    """
    Property: For any operator assignment, both the request assignment and
    load increment should happen atomically (both or neither).
    
    **Feature: operator-request-distribution, Property 16: Load increment on assignment**
    **Validates: Requirements 5.4**
    """
    # Setup: Create fresh database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session: Session = SessionLocal()
    
    try:
        # Create a source
        source = Source(name="Test Source", identifier=f"test_source_atomic_{initial_load}")
        session.add(source)
        session.flush()
        
        # Create a user
        user = User(identifier=f"test_user_atomic_{initial_load}")
        session.add(user)
        session.flush()
        
        # Create an operator
        operator = Operator(
            name=f"Operator_{initial_load}",
            is_active=True,
            max_load_limit=20,
            current_load=initial_load
        )
        session.add(operator)
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
        
        # Test: Assign operator to request
        distribution_service = DistributionService(session)
        distribution_service.assign_operator(request.id, operator.id)
        
        # Refresh both entities
        session.refresh(operator)
        session.refresh(request)
        
        # Verify: Both changes happened together
        # If request is assigned, load must be incremented
        if request.operator_id == operator.id:
            assert operator.current_load == initial_load + 1, \
                "Request assigned but load not incremented - atomicity violated"
        
        # If load is incremented, request must be assigned
        if operator.current_load == initial_load + 1:
            assert request.operator_id == operator.id, \
                "Load incremented but request not assigned - atomicity violated"
        
        session.commit()
    finally:
        session.close()
