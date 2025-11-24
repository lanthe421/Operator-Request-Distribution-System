"""
Property-based tests for list retrieval completeness.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.operator import Operator
from app.models.source import Source
from app.models.user import User
from app.models.request import Request
from app.repositories.operator_repository import OperatorRepository
from app.repositories.source_repository import SourceRepository
from app.repositories.request_repository import RequestRepository
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
    operator_count=st.integers(min_value=1, max_value=10),
    names=st.lists(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        min_size=1,
        max_size=10
    ),
    max_loads=st.lists(
        st.integers(min_value=1, max_value=100),
        min_size=1,
        max_size=10
    )
)
def test_operator_list_retrieval_completeness(operator_count: int, names: list, max_loads: list):
    """
    Feature: operator-request-distribution, Property 5: List retrieval returns all entities
    
    For any set of created operators, retrieving the list should return
    all created operators with complete information.
    
    Validates: Requirements 1.2, 2.2, 9.2
    """
    session = TestSessionLocal()
    try:
        # Ensure we have enough names and max_loads
        actual_count = min(operator_count, len(names), len(max_loads))
        
        # Create repository
        repo = OperatorRepository(session)
        
        # Create operators
        created_operators = []
        for i in range(actual_count):
            operator = repo.create(name=names[i], max_load_limit=max_loads[i])
            created_operators.append(operator)
        
        session.commit()
        
        # Retrieve all operators
        retrieved_operators = repo.get_all()
        
        # Verify count matches
        assert len(retrieved_operators) == actual_count, \
            f"Expected {actual_count} operators, got {len(retrieved_operators)}"
        
        # Verify all created operators are in retrieved list
        created_ids = {op.id for op in created_operators}
        retrieved_ids = {op.id for op in retrieved_operators}
        
        assert created_ids == retrieved_ids, \
            f"Created IDs {created_ids} don't match retrieved IDs {retrieved_ids}"
        
        # Verify complete information for each operator
        for operator in retrieved_operators:
            assert operator.id is not None, "Operator should have an ID"
            assert operator.name is not None, "Operator should have a name"
            assert operator.max_load_limit is not None, "Operator should have max_load_limit"
            assert operator.is_active is not None, "Operator should have is_active"
            assert operator.current_load is not None, "Operator should have current_load"
            assert operator.created_at is not None, "Operator should have created_at"
        
    finally:
        # Clean up
        session.query(Operator).delete()
        session.commit()
        session.close()


@settings(max_examples=100, deadline=2000)
@given(
    source_count=st.integers(min_value=1, max_value=10),
    names=st.lists(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        min_size=1,
        max_size=10
    ),
    identifiers=st.lists(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x.isalnum()),
        min_size=1,
        max_size=10,
        unique=True
    )
)
def test_source_list_retrieval_completeness(source_count: int, names: list, identifiers: list):
    """
    Feature: operator-request-distribution, Property 5: List retrieval returns all entities
    
    For any set of created sources, retrieving the list should return
    all created sources with complete information.
    
    Validates: Requirements 1.2, 2.2, 9.2
    """
    session = TestSessionLocal()
    try:
        # Ensure we have enough names and identifiers
        actual_count = min(source_count, len(names), len(identifiers))
        
        # Create repository
        repo = SourceRepository(session)
        
        # Create sources
        created_sources = []
        for i in range(actual_count):
            source = repo.create(name=names[i], identifier=identifiers[i])
            created_sources.append(source)
        
        session.commit()
        
        # Retrieve all sources
        retrieved_sources = repo.get_all()
        
        # Verify count matches
        assert len(retrieved_sources) == actual_count, \
            f"Expected {actual_count} sources, got {len(retrieved_sources)}"
        
        # Verify all created sources are in retrieved list
        created_ids = {src.id for src in created_sources}
        retrieved_ids = {src.id for src in retrieved_sources}
        
        assert created_ids == retrieved_ids, \
            f"Created IDs {created_ids} don't match retrieved IDs {retrieved_ids}"
        
        # Verify complete information for each source
        for source in retrieved_sources:
            assert source.id is not None, "Source should have an ID"
            assert source.name is not None, "Source should have a name"
            assert source.identifier is not None, "Source should have an identifier"
            assert source.created_at is not None, "Source should have created_at"
        
    finally:
        # Clean up
        session.query(Source).delete()
        session.commit()
        session.close()


@settings(max_examples=100, deadline=2000)
@given(
    request_count=st.integers(min_value=1, max_value=10),
    messages=st.lists(
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        min_size=1,
        max_size=10
    )
)
def test_request_list_retrieval_completeness(request_count: int, messages: list):
    """
    Feature: operator-request-distribution, Property 5: List retrieval returns all entities
    
    For any set of created requests, retrieving the list should return
    all created requests with complete information.
    
    Validates: Requirements 1.2, 2.2, 9.2
    """
    session = TestSessionLocal()
    try:
        # Ensure we have enough messages
        actual_count = min(request_count, len(messages))
        
        # Create a user and source for the requests
        user = User(identifier="test_user_list_retrieval")
        source = Source(name="test_source", identifier="test_source_list_retrieval")
        session.add(user)
        session.add(source)
        session.commit()
        
        # Create repository
        repo = RequestRepository(session)
        
        # Create requests
        created_requests = []
        for i in range(actual_count):
            request = repo.create(
                user_id=user.id,
                source_id=source.id,
                message=messages[i]
            )
            created_requests.append(request)
        
        session.commit()
        
        # Retrieve all requests
        retrieved_requests = repo.get_all()
        
        # Verify count matches (at least our created requests)
        assert len(retrieved_requests) >= actual_count, \
            f"Expected at least {actual_count} requests, got {len(retrieved_requests)}"
        
        # Verify all created requests are in retrieved list
        created_ids = {req.id for req in created_requests}
        retrieved_ids = {req.id for req in retrieved_requests}
        
        assert created_ids.issubset(retrieved_ids), \
            f"Created IDs {created_ids} not found in retrieved IDs {retrieved_ids}"
        
        # Verify complete information for our created requests
        for request in created_requests:
            retrieved = next((r for r in retrieved_requests if r.id == request.id), None)
            assert retrieved is not None, f"Request {request.id} not found in retrieved list"
            assert retrieved.user_id is not None, "Request should have user_id"
            assert retrieved.source_id is not None, "Request should have source_id"
            assert retrieved.message is not None, "Request should have message"
            assert retrieved.status is not None, "Request should have status"
            assert retrieved.created_at is not None, "Request should have created_at"
        
    finally:
        # Clean up
        session.query(Request).delete()
        session.query(User).delete()
        session.query(Source).delete()
        session.commit()
        session.close()
