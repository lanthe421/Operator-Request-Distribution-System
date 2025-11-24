"""
Integration tests for statistics API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base, get_db
from app.models.operator import Operator
from app.models.source import Source
from app.models.user import User
from app.models.request import Request
from app.models.operator_source_weight import OperatorSourceWeight


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Create test client with test database."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_get_operators_load_empty(client):
    """Test getting operator load statistics when no operators exist."""
    response = client.get("/api/v1/stats/operators-load")
    
    assert response.status_code == 200
    assert response.json() == []


def test_get_operators_load_with_data(client):
    """Test getting operator load statistics with operators."""
    # Create operators
    db = TestingSessionLocal()
    
    operator1 = Operator(
        name="Operator 1",
        max_load_limit=10,
        current_load=5,
        is_active=True
    )
    operator2 = Operator(
        name="Operator 2",
        max_load_limit=20,
        current_load=0,
        is_active=False
    )
    
    db.add(operator1)
    db.add(operator2)
    db.commit()
    db.close()
    
    # Get statistics
    response = client.get("/api/v1/stats/operators-load")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Check first operator
    op1_stats = next(s for s in data if s["operator_name"] == "Operator 1")
    assert op1_stats["current_load"] == 5
    assert op1_stats["max_load_limit"] == 10
    assert op1_stats["load_percentage"] == 50.0
    assert op1_stats["is_active"] is True
    
    # Check second operator
    op2_stats = next(s for s in data if s["operator_name"] == "Operator 2")
    assert op2_stats["current_load"] == 0
    assert op2_stats["max_load_limit"] == 20
    assert op2_stats["load_percentage"] == 0.0
    assert op2_stats["is_active"] is False


def test_get_requests_distribution_empty(client):
    """Test getting request distribution when no requests exist."""
    response = client.get("/api/v1/stats/requests-distribution")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 0
    assert data["unassigned_requests"] == 0
    assert data["by_operator"] == []
    assert data["by_source"] == []


def test_get_requests_distribution_with_data(client):
    """Test getting request distribution with requests."""
    db = TestingSessionLocal()
    
    # Create operators
    operator1 = Operator(name="Op1", max_load_limit=10, current_load=2, is_active=True)
    operator2 = Operator(name="Op2", max_load_limit=10, current_load=1, is_active=True)
    db.add(operator1)
    db.add(operator2)
    db.commit()
    
    # Create sources
    source1 = Source(name="Email", identifier="email")
    source2 = Source(name="Phone", identifier="phone")
    db.add(source1)
    db.add(source2)
    db.commit()
    
    # Create users
    user1 = User(identifier="user1@example.com")
    user2 = User(identifier="user2@example.com")
    db.add(user1)
    db.add(user2)
    db.commit()
    
    # Create requests
    request1 = Request(
        user_id=user1.id,
        source_id=source1.id,
        operator_id=operator1.id,
        message="Request 1",
        status="assigned"
    )
    request2 = Request(
        user_id=user1.id,
        source_id=source1.id,
        operator_id=operator1.id,
        message="Request 2",
        status="assigned"
    )
    request3 = Request(
        user_id=user2.id,
        source_id=source2.id,
        operator_id=operator2.id,
        message="Request 3",
        status="assigned"
    )
    request4 = Request(
        user_id=user2.id,
        source_id=source1.id,
        operator_id=None,
        message="Request 4",
        status="waiting"
    )
    
    db.add_all([request1, request2, request3, request4])
    db.commit()
    db.close()
    
    # Get distribution statistics
    response = client.get("/api/v1/stats/requests-distribution")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check totals
    assert data["total_requests"] == 4
    assert data["unassigned_requests"] == 1
    
    # Check distribution by operator
    by_operator = data["by_operator"]
    assert len(by_operator) == 3  # 2 operators + unassigned
    
    op1_dist = next(d for d in by_operator if d["operator_name"] == "Op1")
    assert op1_dist["request_count"] == 2
    
    op2_dist = next(d for d in by_operator if d["operator_name"] == "Op2")
    assert op2_dist["request_count"] == 1
    
    unassigned_dist = next(d for d in by_operator if d["operator_id"] is None)
    assert unassigned_dist["request_count"] == 1
    
    # Check distribution by source
    by_source = data["by_source"]
    assert len(by_source) == 2
    
    email_dist = next(d for d in by_source if d["source_name"] == "Email")
    assert email_dist["request_count"] == 3
    
    phone_dist = next(d for d in by_source if d["source_name"] == "Phone")
    assert phone_dist["request_count"] == 1


def test_get_requests_distribution_only_unassigned(client):
    """Test distribution statistics with only unassigned requests."""
    db = TestingSessionLocal()
    
    # Create source and user
    source = Source(name="Email", identifier="email")
    user = User(identifier="user@example.com")
    db.add(source)
    db.add(user)
    db.commit()
    
    # Create unassigned request
    request = Request(
        user_id=user.id,
        source_id=source.id,
        operator_id=None,
        message="Unassigned request",
        status="waiting"
    )
    db.add(request)
    db.commit()
    db.close()
    
    # Get statistics
    response = client.get("/api/v1/stats/requests-distribution")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_requests"] == 1
    assert data["unassigned_requests"] == 1
    assert len(data["by_operator"]) == 1
    assert data["by_operator"][0]["operator_id"] is None
    assert data["by_operator"][0]["request_count"] == 1
