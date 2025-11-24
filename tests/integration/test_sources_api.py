"""
Integration tests for source API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base, get_db


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


def test_create_source(client):
    """Test POST /api/v1/sources/ endpoint."""
    response = client.post(
        "/api/v1/sources/",
        json={"name": "Email Support", "identifier": "email"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Email Support"
    assert data["identifier"] == "email"
    assert "id" in data
    assert "created_at" in data


def test_create_source_empty_name(client):
    """Test creating source with empty name fails."""
    response = client.post(
        "/api/v1/sources/",
        json={"name": "", "identifier": "email"}
    )
    
    assert response.status_code == 422  # Validation error from Pydantic


def test_create_source_whitespace_name(client):
    """Test creating source with whitespace-only name fails."""
    response = client.post(
        "/api/v1/sources/",
        json={"name": "   ", "identifier": "email"}
    )
    
    assert response.status_code == 422
    assert "whitespace" in str(response.json()).lower()


def test_create_source_duplicate_identifier(client):
    """Test creating source with duplicate identifier fails."""
    # Create first source
    client.post(
        "/api/v1/sources/",
        json={"name": "Email Support", "identifier": "email"}
    )
    
    # Try to create second source with same identifier
    response = client.post(
        "/api/v1/sources/",
        json={"name": "Email Sales", "identifier": "email"}
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_list_sources(client):
    """Test GET /api/v1/sources/ endpoint."""
    # Create some sources first
    client.post("/api/v1/sources/", json={"name": "Email", "identifier": "email"})
    client.post("/api/v1/sources/", json={"name": "Phone", "identifier": "phone"})
    
    response = client.get("/api/v1/sources/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Email"
    assert data[1]["name"] == "Phone"


def test_list_sources_empty(client):
    """Test listing sources when none exist."""
    response = client.get("/api/v1/sources/")
    
    assert response.status_code == 200
    assert response.json() == []


def test_configure_operator_weights(client):
    """Test POST /api/v1/sources/{id}/operators endpoint."""
    # Create source
    source_response = client.post(
        "/api/v1/sources/",
        json={"name": "Email", "identifier": "email"}
    )
    source_id = source_response.json()["id"]
    
    # Create operators
    op1_response = client.post(
        "/api/v1/operators/",
        json={"name": "Operator 1", "max_load_limit": 10}
    )
    op1_id = op1_response.json()["id"]
    
    op2_response = client.post(
        "/api/v1/operators/",
        json={"name": "Operator 2", "max_load_limit": 15}
    )
    op2_id = op2_response.json()["id"]
    
    # Configure weights
    response = client.post(
        f"/api/v1/sources/{source_id}/operators",
        json={
            "weights": [
                {"operator_id": op1_id, "weight": 30},
                {"operator_id": op2_id, "weight": 70}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Check weights are configured correctly
    weights_by_id = {w["operator_id"]: w for w in data}
    assert weights_by_id[op1_id]["weight"] == 30
    assert weights_by_id[op1_id]["operator_name"] == "Operator 1"
    assert weights_by_id[op2_id]["weight"] == 70
    assert weights_by_id[op2_id]["operator_name"] == "Operator 2"


def test_configure_operator_weights_update_existing(client):
    """Test updating existing operator weights."""
    # Create source and operator
    source_response = client.post(
        "/api/v1/sources/",
        json={"name": "Email", "identifier": "email"}
    )
    source_id = source_response.json()["id"]
    
    op_response = client.post(
        "/api/v1/operators/",
        json={"name": "Operator 1", "max_load_limit": 10}
    )
    op_id = op_response.json()["id"]
    
    # Configure initial weight
    client.post(
        f"/api/v1/sources/{source_id}/operators",
        json={"weights": [{"operator_id": op_id, "weight": 30}]}
    )
    
    # Update weight
    response = client.post(
        f"/api/v1/sources/{source_id}/operators",
        json={"weights": [{"operator_id": op_id, "weight": 80}]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["weight"] == 80


def test_configure_operator_weights_invalid_weight(client):
    """Test configuring weight outside valid range fails."""
    # Create source and operator
    source_response = client.post(
        "/api/v1/sources/",
        json={"name": "Email", "identifier": "email"}
    )
    source_id = source_response.json()["id"]
    
    op_response = client.post(
        "/api/v1/operators/",
        json={"name": "Operator 1", "max_load_limit": 10}
    )
    op_id = op_response.json()["id"]
    
    # Try to configure weight > 100
    response = client.post(
        f"/api/v1/sources/{source_id}/operators",
        json={"weights": [{"operator_id": op_id, "weight": 150}]}
    )
    
    assert response.status_code == 422  # Pydantic validation


def test_configure_operator_weights_source_not_found(client):
    """Test configuring weights for non-existent source."""
    # Create operator
    op_response = client.post(
        "/api/v1/operators/",
        json={"name": "Operator 1", "max_load_limit": 10}
    )
    op_id = op_response.json()["id"]
    
    # Try to configure weights for non-existent source
    response = client.post(
        "/api/v1/sources/999/operators",
        json={"weights": [{"operator_id": op_id, "weight": 50}]}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_configure_operator_weights_operator_not_found(client):
    """Test configuring weights for non-existent operator."""
    # Create source
    source_response = client.post(
        "/api/v1/sources/",
        json={"name": "Email", "identifier": "email"}
    )
    source_id = source_response.json()["id"]
    
    # Try to configure weights for non-existent operator
    response = client.post(
        f"/api/v1/sources/{source_id}/operators",
        json={"weights": [{"operator_id": 999, "weight": 50}]}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
