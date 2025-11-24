"""
Integration tests for operator API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base, get_db
from app.models.operator import Operator


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


def test_create_operator(client):
    """Test POST /api/v1/operators/ endpoint."""
    response = client.post(
        "/api/v1/operators/",
        json={"name": "Test Operator", "max_load_limit": 10}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Operator"
    assert data["max_load_limit"] == 10
    assert data["is_active"] is True
    assert data["current_load"] == 0
    assert "id" in data
    assert "created_at" in data


def test_create_operator_empty_name(client):
    """Test creating operator with empty name fails."""
    response = client.post(
        "/api/v1/operators/",
        json={"name": "", "max_load_limit": 10}
    )
    
    assert response.status_code == 422  # Validation error from Pydantic


def test_create_operator_whitespace_name(client):
    """Test creating operator with whitespace-only name fails."""
    response = client.post(
        "/api/v1/operators/",
        json={"name": "   ", "max_load_limit": 10}
    )
    
    # Pydantic validation catches this at 422 level
    assert response.status_code == 422
    assert "whitespace" in str(response.json()).lower()


def test_list_operators(client):
    """Test GET /api/v1/operators/ endpoint."""
    # Create some operators first
    client.post("/api/v1/operators/", json={"name": "Operator 1", "max_load_limit": 5})
    client.post("/api/v1/operators/", json={"name": "Operator 2", "max_load_limit": 10})
    
    response = client.get("/api/v1/operators/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Operator 1"
    assert data[1]["name"] == "Operator 2"


def test_list_operators_empty(client):
    """Test listing operators when none exist."""
    response = client.get("/api/v1/operators/")
    
    assert response.status_code == 200
    assert response.json() == []


def test_update_operator(client):
    """Test PUT /api/v1/operators/{id} endpoint."""
    # Create operator first
    create_response = client.post(
        "/api/v1/operators/",
        json={"name": "Test Operator", "max_load_limit": 10}
    )
    operator_id = create_response.json()["id"]
    
    # Update operator
    response = client.put(
        f"/api/v1/operators/{operator_id}",
        json={"max_load_limit": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == operator_id
    assert data["max_load_limit"] == 20
    assert data["name"] == "Test Operator"  # Name unchanged


def test_update_operator_not_found(client):
    """Test updating non-existent operator."""
    response = client.put(
        "/api/v1/operators/999",
        json={"max_load_limit": 20}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_toggle_operator_active(client):
    """Test PUT /api/v1/operators/{id}/toggle-active endpoint."""
    # Create operator first
    create_response = client.post(
        "/api/v1/operators/",
        json={"name": "Test Operator", "max_load_limit": 10}
    )
    operator_id = create_response.json()["id"]
    
    # Toggle active status (should become False)
    response = client.put(f"/api/v1/operators/{operator_id}/toggle-active")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == operator_id
    assert data["is_active"] is False
    
    # Toggle again (should become True)
    response = client.put(f"/api/v1/operators/{operator_id}/toggle-active")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True


def test_toggle_operator_not_found(client):
    """Test toggling non-existent operator."""
    response = client.put("/api/v1/operators/999/toggle-active")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
