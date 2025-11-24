"""
Integration tests for requests API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from main import app
from app.models.operator import Operator
from app.models.source import Source
from app.models.operator_source_weight import OperatorSourceWeight
from app.models.request import Request
from app.models.user import User


# Create test database with shared cache
SQLALCHEMY_DATABASE_URL = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},
    poolclass=None
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables once
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before and after each test."""
    # Clean before test
    db = TestingSessionLocal()
    try:
        # Delete in reverse order to respect foreign keys
        db.query(Request).delete(synchronize_session=False)
        db.query(OperatorSourceWeight).delete(synchronize_session=False)
        db.query(Operator).delete(synchronize_session=False)
        db.query(Source).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    
    yield
    
    # Clean after test
    db = TestingSessionLocal()
    try:
        # Delete in reverse order to respect foreign keys
        db.query(Request).delete(synchronize_session=False)
        db.query(OperatorSourceWeight).delete(synchronize_session=False)
        db.query(Operator).delete(synchronize_session=False)
        db.query(Source).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def setup_test_data():
    """Setup test data for requests."""
    db = TestingSessionLocal()
    try:
        # Create operator
        operator = Operator(
            name="Test Operator",
            is_active=True,
            max_load_limit=10,
            current_load=0
        )
        db.add(operator)
        db.flush()
        
        # Create source
        source = Source(
            name="Test Source",
            identifier="test-source"
        )
        db.add(source)
        db.flush()
        
        # Create weight
        weight = OperatorSourceWeight(
            operator_id=operator.id,
            source_id=source.id,
            weight=50
        )
        db.add(weight)
        db.commit()
        
        return {
            "operator_id": operator.id,
            "source_id": source.id
        }
    finally:
        db.close()


def test_create_request_success(client, setup_test_data):
    """Test successful request creation with operator assignment."""
    response = client.post(
        "/api/v1/requests/",
        json={
            "user_identifier": "user@example.com",
            "source_id": setup_test_data["source_id"],
            "message": "Test request message"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] is not None
    assert data["source_id"] == setup_test_data["source_id"]
    assert data["message"] == "Test request message"
    assert data["status"] in ["assigned", "waiting"]
    assert "created_at" in data


def test_create_request_new_user(client, setup_test_data):
    """Test request creation with new user auto-creation."""
    response = client.post(
        "/api/v1/requests/",
        json={
            "user_identifier": "newuser@example.com",
            "source_id": setup_test_data["source_id"],
            "message": "First request"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    user_id = data["user_id"]
    
    # Create another request with same user
    response2 = client.post(
        "/api/v1/requests/",
        json={
            "user_identifier": "newuser@example.com",
            "source_id": setup_test_data["source_id"],
            "message": "Second request"
        }
    )
    
    assert response2.status_code == 201
    data2 = response2.json()
    # Should reuse the same user
    assert data2["user_id"] == user_id


def test_create_request_empty_message(client, setup_test_data):
    """Test request creation with empty message fails."""
    response = client.post(
        "/api/v1/requests/",
        json={
            "user_identifier": "user@example.com",
            "source_id": setup_test_data["source_id"],
            "message": "   "
        }
    )
    
    # Pydantic validation returns 422 for invalid data
    assert response.status_code == 422


def test_create_request_invalid_source(client):
    """Test request creation with invalid source ID."""
    response = client.post(
        "/api/v1/requests/",
        json={
            "user_identifier": "user@example.com",
            "source_id": 9999,
            "message": "Test message"
        }
    )
    
    assert response.status_code == 404


def test_list_requests(client, setup_test_data):
    """Test listing all requests."""
    # Create some requests
    for i in range(3):
        client.post(
            "/api/v1/requests/",
            json={
                "user_identifier": f"user{i}@example.com",
                "source_id": setup_test_data["source_id"],
                "message": f"Request {i}"
            }
        )
    
    # List requests
    response = client.get("/api/v1/requests/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("id" in req for req in data)
    assert all("message" in req for req in data)


def test_get_request_details(client, setup_test_data):
    """Test getting detailed request information."""
    # Create a request
    create_response = client.post(
        "/api/v1/requests/",
        json={
            "user_identifier": "detailuser@example.com",
            "source_id": setup_test_data["source_id"],
            "message": "Detail test"
        }
    )
    
    request_id = create_response.json()["id"]
    
    # Get details
    response = client.get(f"/api/v1/requests/{request_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == request_id
    assert data["user_identifier"] == "detailuser@example.com"
    assert data["source_name"] == "Test Source"
    assert data["message"] == "Detail test"
    assert "created_at" in data


def test_get_request_details_not_found(client):
    """Test getting details for non-existent request."""
    response = client.get("/api/v1/requests/9999")
    
    assert response.status_code == 404


def test_request_without_available_operators(client):
    """Test request creation when no operators are available."""
    db = TestingSessionLocal()
    try:
        # Create source without operators
        source = Source(
            name="No Operator Source",
            identifier="no-op-source"
        )
        db.add(source)
        db.commit()
        source_id = source.id
    finally:
        db.close()
    
    response = client.post(
        "/api/v1/requests/",
        json={
            "user_identifier": "user@example.com",
            "source_id": source_id,
            "message": "Unassigned request"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["operator_id"] is None
    assert data["status"] == "waiting"
