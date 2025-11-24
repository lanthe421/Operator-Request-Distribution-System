# Design Document

## Overview

Мини-CRM система представляет собой REST API сервис на базе FastAPI для автоматического распределения входящих обращений между операторами. Система использует SQLAlchemy ORM для работы с SQLite базой данных и реализует вероятностный алгоритм распределения на основе весовых коэффициентов.

Ключевые особенности архитектуры:
- Трехслойная архитектура (API → Service → Repository)
- Транзакционная целостность при распределении обращений
- Атомарное обновление загрузки операторов
- Stateless API для горизонтального масштабирования

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │
│  - Request validation (Pydantic)    │
│  - Response serialization           │
│  - HTTP routing                     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        Service Layer                │
│  - Business logic                   │
│  - Distribution algorithm           │
│  - Transaction management           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      Repository Layer               │
│  - Data access (SQLAlchemy)         │
│  - Query optimization               │
│  - Database operations              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      Database (SQLite)              │
└─────────────────────────────────────┘
```

### Directory Structure

```
.
├── alembic/                    # Database migrations
│   └── versions/
├── app/
│   ├── api/                    # API endpoints
│   │   └── v1/
│   │       ├── operators.py
│   │       ├── sources.py
│   │       ├── requests.py
│   │       └── stats.py
│   ├── models/                 # SQLAlchemy models
│   │   ├── operator.py
│   │   ├── user.py
│   │   ├── source.py
│   │   ├── operator_source_weight.py
│   │   └── request.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── operator.py
│   │   ├── source.py
│   │   └── request.py
│   ├── services/               # Business logic
│   │   ├── operator_service.py
│   │   ├── source_service.py
│   │   ├── request_service.py
│   │   └── distribution_service.py
│   ├── repositories/           # Data access
│   │   ├── operator_repository.py
│   │   ├── source_repository.py
│   │   ├── user_repository.py
│   │   └── request_repository.py
│   ├── core/                   # Core configuration
│   │   ├── config.py
│   │   └── database.py
│   └── utils/                  # Utilities
│       └── weighted_random.py
├── tests/                      # Test files
│   ├── unit/
│   ├── integration/
│   └── property/
├── main.py                     # Application entry point
├── requirements.txt
└── alembic.ini
```

## Components and Interfaces

### 1. API Layer

**Operators API (`/api/v1/operators`)**
- `POST /` - Create operator
- `GET /` - List operators
- `PUT /{id}` - Update operator
- `PUT /{id}/toggle-active` - Toggle active status

**Sources API (`/api/v1/sources`)**
- `POST /` - Create source
- `GET /` - List sources
- `POST /{id}/operators` - Configure operator weights

**Requests API (`/api/v1/requests`)**
- `POST /` - Create request (triggers distribution)
- `GET /` - List requests
- `GET /{id}` - Get request details

**Stats API (`/api/v1/stats`)**
- `GET /operators-load` - Operator load statistics
- `GET /requests-distribution` - Request distribution statistics

### 2. Service Layer

**OperatorService**
```python
class OperatorService:
    def create_operator(name: str, max_load_limit: int) -> Operator
    def get_operators() -> List[Operator]
    def update_operator(id: int, max_load_limit: int) -> Operator
    def toggle_active(id: int) -> Operator
```

**SourceService**
```python
class SourceService:
    def create_source(name: str, identifier: str) -> Source
    def get_sources() -> List[Source]
    def configure_weights(source_id: int, weights: List[OperatorWeight]) -> None
```

**RequestService**
```python
class RequestService:
    def create_request(user_identifier: str, source_id: int, message: str) -> Request
    def get_requests() -> List[Request]
    def get_request_by_id(id: int) -> Request
```

**DistributionService**
```python
class DistributionService:
    def get_available_operators(source_id: int) -> List[Tuple[Operator, int]]
    def select_operator_by_weight(operators: List[Tuple[Operator, int]]) -> Optional[Operator]
    def assign_operator(request_id: int, operator_id: int) -> None
```

### 3. Repository Layer

**OperatorRepository**
```python
class OperatorRepository:
    def create(operator: Operator) -> Operator
    def get_all() -> List[Operator]
    def get_by_id(id: int) -> Optional[Operator]
    def update(operator: Operator) -> Operator
    def increment_load(operator_id: int) -> None
    def decrement_load(operator_id: int) -> None
```

**UserRepository**
```python
class UserRepository:
    def get_by_identifier(identifier: str) -> Optional[User]
    def create(identifier: str) -> User
```

**RequestRepository**
```python
class RequestRepository:
    def create(request: Request) -> Request
    def get_all() -> List[Request]
    def get_by_id(id: int) -> Optional[Request]
    def update(request: Request) -> Request
```

## Data Models

### Database Schema

```sql
-- Operators table
CREATE TABLE operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    max_load_limit INTEGER NOT NULL,
    current_load INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sources table
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    identifier VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Operator-Source weights table
CREATE TABLE operator_source_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    weight INTEGER NOT NULL CHECK (weight >= 1 AND weight <= 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operator_id) REFERENCES operators(id),
    FOREIGN KEY (source_id) REFERENCES sources(id),
    UNIQUE (operator_id, source_id)
);

-- Requests table
CREATE TABLE requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    operator_id INTEGER NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (source_id) REFERENCES sources(id),
    FOREIGN KEY (operator_id) REFERENCES operators(id)
);
```

### SQLAlchemy Models

**Operator Model**
```python
class Operator(Base):
    __tablename__ = "operators"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    max_load_limit: Mapped[int]
    current_load: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    weights: Mapped[List["OperatorSourceWeight"]] = relationship(back_populates="operator")
    requests: Mapped[List["Request"]] = relationship(back_populates="operator")
```

### Pydantic Schemas

**Request Schemas**
```python
class OperatorCreate(BaseModel):
    name: str
    max_load_limit: int

class OperatorResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    max_load_limit: int
    current_load: int
    
class RequestCreate(BaseModel):
    user_identifier: str
    source_id: int
    message: str
    
class RequestResponse(BaseModel):
    id: int
    user_id: int
    source_id: int
    operator_id: Optional[int]
    message: str
    status: str
    created_at: datetime
```

## Weighted Random Distribution Algorithm

### Algorithm Description

Алгоритм использует метод "накопительных весов" (cumulative weights) для вероятностного выбора:

1. **Сбор доступных операторов**: Выбираются операторы с `is_active=True`, `current_load < max_load_limit` и настроенным весом для источника
2. **Вычисление накопительных весов**: Создается массив накопительных сумм весов
3. **Генерация случайного числа**: Генерируется число от 0 до суммы всех весов
4. **Бинарный поиск**: Находится оператор, чей диапазон содержит случайное число

### Implementation

```python
def select_operator_by_weight(
    operators_with_weights: List[Tuple[Operator, int]]
) -> Optional[Operator]:
    """
    Select operator using weighted random selection.
    
    Args:
        operators_with_weights: List of (operator, weight) tuples
        
    Returns:
        Selected operator or None if list is empty
    """
    if not operators_with_weights:
        return None
    
    # Calculate cumulative weights
    cumulative_weights = []
    total = 0
    for operator, weight in operators_with_weights:
        total += weight
        cumulative_weights.append(total)
    
    # Generate random number [0, total)
    random_value = random.uniform(0, total)
    
    # Binary search for the operator
    index = bisect.bisect_right(cumulative_weights, random_value)
    
    return operators_with_weights[index][0]
```

### Example

```
Operators:
- Operator A: weight = 20
- Operator B: weight = 30
- Operator C: weight = 50

Cumulative weights: [20, 50, 100]

Random value = 45
bisect_right([20, 50, 100], 45) = 2
Selected: Operator C (index 2)

Probability distribution:
- A: 20/100 = 20%
- B: 30/100 = 30%
- C: 50/100 = 50%
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Operator creation initializes state correctly
*For any* operator created with a valid name and max_load_limit, the operator should be stored with is_active set to True and current_load set to 0.
**Validates: Requirements 1.1**

### Property 2: Operator update modifies max_load_limit
*For any* existing operator and new max_load_limit value, updating the operator should result in the max_load_limit being changed to the new value.
**Validates: Requirements 1.3**

### Property 3: Toggle changes active status
*For any* operator, toggling the active status should flip the is_active flag from True to False or False to True.
**Validates: Requirements 1.4**

### Property 4: Non-empty string validation
*For any* string composed entirely of whitespace or empty string, attempting to use it as a name for operators, sources, or request messages should be rejected.
**Validates: Requirements 1.5, 2.4, 4.4**

### Property 5: List retrieval returns all entities
*For any* set of created entities (operators, sources, or requests), retrieving the list should return all created entities with complete information.
**Validates: Requirements 1.2, 2.2, 9.2**

### Property 6: Source identifier uniqueness
*For any* two sources, if they have the same identifier, the system should reject the creation of the second source.
**Validates: Requirements 2.3**

### Property 7: Weight storage within valid range
*For any* operator-source pair and weight value between 1 and 100, assigning the weight should store it correctly.
**Validates: Requirements 3.1**

### Property 8: Weight update modifies existing value
*For any* existing operator-source weight configuration, updating the weight should change it to the new value.
**Validates: Requirements 3.2**

### Property 9: Weight boundary validation
*For any* weight value less than 1 or greater than 100, the system should reject the weight assignment.
**Validates: Requirements 3.3**

### Property 10: Weight retrieval completeness
*For any* source with configured operator weights, retrieving the weights should return all operators with their configured weights for that source.
**Validates: Requirements 3.4**

### Property 11: Request creation stores all data
*For any* valid user_identifier, source_id, and message, creating a request should store a new request record with all provided data.
**Validates: Requirements 4.1**

### Property 12: New user auto-creation
*For any* user_identifier that doesn't exist in the system, submitting a request with that identifier should create a new user record.
**Validates: Requirements 4.2**

### Property 13: Existing user reuse
*For any* existing user_identifier, submitting multiple requests with that identifier should associate all requests with the same user (no duplicate users created).
**Validates: Requirements 4.3**

### Property 14: Request timestamp recording
*For any* created request, the request should have a creation timestamp that is set and represents a valid datetime.
**Validates: Requirements 4.5**

### Property 15: Available operator identification
*For any* source, the system should identify as available only those operators where is_active equals True AND current_load is less than max_load_limit AND a weight is configured for that source.
**Validates: Requirements 5.1, 5.2**

### Property 16: Load increment on assignment
*For any* operator assigned to a request, the operator's current_load should increase by exactly 1.
**Validates: Requirements 5.4**

### Property 17: Unassigned request handling
*For any* request created when no available operators exist, the request should be created with operator_id set to NULL and status set to waiting.
**Validates: Requirements 5.5**

### Property 18: Weight sum calculation
*For any* list of operators with weights, the sum of all weights should equal the total used for random selection.
**Validates: Requirements 6.1**

### Property 19: Random number within bounds
*For any* weighted random selection, the generated random number should be greater than or equal to 0 and less than the total weight sum.
**Validates: Requirements 6.2**

### Property 20: Correct operator selection by range
*For any* mocked random value and list of operators with weights, the selected operator should be the one whose cumulative weight range contains the random value.
**Validates: Requirements 6.3**

### Property 21: Statistical distribution matches weights
*For any* set of operators with configured weights, running the distribution algorithm many times (1000+ iterations) should result in selection frequencies proportional to the weights (within statistical tolerance).
**Validates: Requirements 6.5, 5.3**

### Property 22: Operator load statistics calculation
*For any* set of operators, the load statistics should return each operator's current_load, max_load_limit, and correctly calculated load percentage ((current_load / max_load_limit) * 100).
**Validates: Requirements 7.1, 7.2**

### Property 23: Statistics include all operators
*For any* mix of active and inactive operators, the statistics should include all operators regardless of their active status.
**Validates: Requirements 7.3**

### Property 24: Request distribution by operator
*For any* set of requests assigned to operators, the distribution statistics should correctly count requests grouped by operator_id.
**Validates: Requirements 8.1**

### Property 25: Request distribution by source
*For any* set of requests from different sources, the distribution statistics should correctly count requests grouped by source_id.
**Validates: Requirements 8.2**

### Property 26: Unassigned requests in statistics
*For any* requests with NULL operator_id, the distribution statistics should include them as unassigned requests.
**Validates: Requirements 8.3**

### Property 27: Request detail retrieval with relationships
*For any* request ID, retrieving the request details should return the request with complete user, source, operator information, and creation timestamp.
**Validates: Requirements 9.1, 9.3**

### Property 28: Foreign key integrity
*For any* request, the system should ensure that the referenced source_id and user_id exist in their respective tables.
**Validates: Requirements 10.2, 10.3**

### Property 29: Operator assignment validation
*For any* operator assignment, the system should ensure the operator exists and is active at the time of assignment.
**Validates: Requirements 10.1**

### Property 30: Cascade deletion prevention
*For any* operator or source that has associated requests, attempting to delete it should be prevented by the system.
**Validates: Requirements 10.4, 10.5**

## Error Handling

### Error Categories

**1. Validation Errors (400 Bad Request)**
- Empty or whitespace-only strings for names/messages
- Weight values outside 1-100 range
- Invalid data types
- Missing required fields

**2. Not Found Errors (404 Not Found)**
- Operator ID not found
- Source ID not found
- Request ID not found
- User ID not found

**3. Conflict Errors (409 Conflict)**
- Duplicate source identifier
- Attempting to delete operator/source with associated requests

**4. Business Logic Errors (422 Unprocessable Entity)**
- Operator at maximum load capacity
- No available operators for source
- Invalid operator-source weight configuration

**5. Database Errors (500 Internal Server Error)**
- Connection failures
- Transaction rollback failures
- Constraint violations

### Error Response Format

```python
class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime
```

### Transaction Management

All operations that modify multiple entities must be wrapped in database transactions:

```python
@contextmanager
def transaction_scope():
    """Provide a transactional scope for database operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Critical transactional operations:
- Request creation + user creation + operator assignment + load increment
- Weight configuration updates
- Operator status changes that affect request distribution

### Retry Logic

For concurrent load updates, implement optimistic locking:

```python
def increment_operator_load(operator_id: int, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            operator = session.query(Operator).with_for_update().get(operator_id)
            operator.current_load += 1
            session.commit()
            return
        except OperationalError:
            session.rollback()
            if attempt == max_retries - 1:
                raise
```

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples and edge cases:

**Operator Management**
- Creating operators with valid data
- Updating operator properties
- Toggling active status
- Edge case: operator with zero max_load_limit

**Source Management**
- Creating sources with unique identifiers
- Duplicate identifier rejection
- Weight configuration CRUD operations

**Request Processing**
- Request creation with new users
- Request creation with existing users
- Empty message rejection

**Distribution Logic**
- Weighted random selection with known random seed
- Edge case: single operator available
- Edge case: no operators available
- Edge case: all operators at capacity

### Property-Based Testing

Property-based testing will verify universal properties across all inputs using **Hypothesis** library for Python.

**Configuration:**
- Minimum 100 iterations per property test
- Use `@given` decorator with appropriate strategies
- Each test must reference its correctness property using format: `**Feature: operator-request-distribution, Property {number}: {property_text}**`

**Test Categories:**

1. **Model Invariants** (Properties 1-4, 6-9, 11-14, 16-17, 28-30)
   - Generate random valid inputs
   - Verify state constraints hold
   - Test boundary conditions

2. **Statistical Properties** (Property 21)
   - Generate operator configurations
   - Run distribution 1000+ times
   - Verify chi-square test for distribution

3. **Aggregation Properties** (Properties 5, 10, 22-27)
   - Generate random datasets
   - Verify completeness and correctness of aggregations

4. **Algorithm Correctness** (Properties 15, 18-20)
   - Test weighted selection logic
   - Verify mathematical properties

**Example Property Test:**

```python
from hypothesis import given, strategies as st

@given(
    name=st.text(min_size=1).filter(lambda x: x.strip()),
    max_load=st.integers(min_value=1, max_value=100)
)
def test_operator_creation_initializes_correctly(name, max_load):
    """
    Feature: operator-request-distribution, Property 1: Operator creation initializes state correctly
    """
    operator = create_operator(name=name, max_load_limit=max_load)
    
    assert operator.is_active is True
    assert operator.current_load == 0
    assert operator.name == name
    assert operator.max_load_limit == max_load
```

### Integration Testing

Integration tests will verify end-to-end workflows:

1. **Complete Request Flow**
   - Create operators and sources
   - Configure weights
   - Submit requests
   - Verify distribution and load updates

2. **Statistics Accuracy**
   - Create diverse data
   - Verify statistics match actual data

3. **Concurrent Request Handling**
   - Simulate multiple simultaneous requests
   - Verify load tracking accuracy
   - Verify no race conditions

### Test Data Generators

For property-based testing, custom strategies will be defined:

```python
# Hypothesis strategies
valid_operator_name = st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
operator_load = st.integers(min_value=0, max_value=100)
weight_value = st.integers(min_value=1, max_value=100)
user_identifier = st.emails() | st.text(min_size=5, max_size=50)
```

## Performance Considerations

### Database Indexing

```sql
CREATE INDEX idx_operators_active_load ON operators(is_active, current_load);
CREATE INDEX idx_operator_source_weights_source ON operator_source_weights(source_id);
CREATE INDEX idx_requests_operator ON requests(operator_id);
CREATE INDEX idx_requests_source ON requests(source_id);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_users_identifier ON users(identifier);
```

### Query Optimization

**Available Operators Query:**
```python
# Optimized query with single database hit
available_operators = (
    session.query(Operator, OperatorSourceWeight.weight)
    .join(OperatorSourceWeight)
    .filter(
        OperatorSourceWeight.source_id == source_id,
        Operator.is_active == True,
        Operator.current_load < Operator.max_load_limit
    )
    .all()
)
```

### Caching Strategy

For read-heavy operations:
- Cache operator weights per source (TTL: 5 minutes)
- Cache source list (TTL: 10 minutes)
- Invalidate cache on configuration changes

### Scalability

**Horizontal Scaling:**
- Stateless API allows multiple instances
- Database connection pooling
- Consider PostgreSQL for production (better concurrency)

**Load Distribution:**
- Expected: 100-1000 requests/minute
- Database connection pool: 20 connections
- API instances: 3-5 behind load balancer

## Deployment

### Database Migrations

Using Alembic for schema versioning:

```bash
# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Environment Configuration

```python
# config.py
class Settings(BaseSettings):
    database_url: str = "sqlite:///./crm.db"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    
    class Config:
        env_file = ".env"
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring and Observability

### Metrics to Track

1. **Request Distribution Metrics**
   - Requests per operator
   - Average assignment time
   - Unassigned request rate

2. **Operator Metrics**
   - Load distribution across operators
   - Average load per operator
   - Operators at capacity

3. **System Metrics**
   - API response times
   - Database query times
   - Error rates by endpoint

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log distribution events
logger.info(
    "Request assigned",
    extra={
        "request_id": request.id,
        "operator_id": operator.id,
        "source_id": source.id,
        "assignment_time_ms": elapsed_time
    }
)
```

## Future Enhancements

1. **Priority-Based Distribution**
   - Add priority field to requests
   - Prioritize high-priority requests in queue

2. **Operator Skills/Tags**
   - Tag-based matching beyond source
   - Multi-dimensional weight calculation

3. **Request Reassignment**
   - Automatic reassignment for stale requests
   - Manual reassignment by administrators

4. **Real-time Notifications**
   - WebSocket support for operator notifications
   - Push notifications for new assignments

5. **Analytics Dashboard**
   - Real-time operator load visualization
   - Historical distribution analysis
   - Performance metrics
