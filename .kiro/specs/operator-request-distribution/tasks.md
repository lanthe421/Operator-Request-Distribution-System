	# Implementation Plan

- [x] 1. Set up project structure and dependencies





  - Create directory structure for app, models, schemas, services, repositories, api, core, utils
  - Create requirements.txt with FastAPI, SQLAlchemy, Alembic, Pydantic, Hypothesis, pytest
  - Create main.py as application entry point
  - Set up .env configuration file
  - _Requirements: All_

- [x] 2. Configure database and core infrastructure





  - Create core/config.py with Settings class using Pydantic BaseSettings
  - Create core/database.py with SQLAlchemy engine, SessionLocal, and Base
  - Initialize Alembic for migrations
  - Create initial migration for database schema
  - _Requirements: All_

- [x] 3. Implement data models





  - Create models/operator.py with Operator SQLAlchemy model
  - Create models/user.py with User SQLAlchemy model
  - Create models/source.py with Source SQLAlchemy model
  - Create models/operator_source_weight.py with OperatorSourceWeight model
  - Create models/request.py with Request model
  - Define all relationships between models
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [x] 3.1 Write property test for operator creation initialization


  - **Property 1: Operator creation initializes state correctly**
  - **Validates: Requirements 1.1**

- [x] 3.2 Write property test for non-empty string validation


  - **Property 4: Non-empty string validation**
  - **Validates: Requirements 1.5, 2.4, 4.4**

- [x] 3.3 Write property test for source identifier uniqueness


  - **Property 6: Source identifier uniqueness**
  - **Validates: Requirements 2.3**

- [x] 4. Create Pydantic schemas for request/response validation





  - Create schemas/operator.py with OperatorCreate, OperatorUpdate, OperatorResponse
  - Create schemas/source.py with SourceCreate, SourceResponse, OperatorWeightConfig
  - Create schemas/request.py with RequestCreate, RequestResponse
  - Create schemas/stats.py with OperatorLoadStats, DistributionStats
  - Add validation for non-empty strings and weight ranges
  - _Requirements: 1.5, 2.4, 3.3, 4.4_

- [x] 4.1 Write property test for weight boundary validation


  - **Property 9: Weight boundary validation**
  - **Validates: Requirements 3.3**

- [x] 5. Implement repository layer for data access





  - Create repositories/operator_repository.py with CRUD operations and load management
  - Create repositories/user_repository.py with get_by_identifier and create methods
  - Create repositories/source_repository.py with CRUD operations
  - Create repositories/request_repository.py with CRUD and query methods
  - Implement transaction management utilities
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 4.1, 4.2, 4.3_

- [x] 5.1 Write property test for list retrieval completeness


  - **Property 5: List retrieval returns all entities**
  - **Validates: Requirements 1.2, 2.2, 9.2**

- [x] 5.2 Write property test for operator update


  - **Property 2: Operator update modifies max_load_limit**
  - **Validates: Requirements 1.3**

- [x] 5.3 Write property test for existing user reuse


  - **Property 13: Existing user reuse**
  - **Validates: Requirements 4.3**

- [x] 6. Implement weighted random selection algorithm





  - Create utils/weighted_random.py with select_operator_by_weight function
  - Implement cumulative weights calculation
  - Implement binary search for operator selection
  - Add edge case handling for empty operator list
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 6.1 Write property test for weight sum calculation


  - **Property 18: Weight sum calculation**
  - **Validates: Requirements 6.1**

- [x] 6.2 Write property test for random number bounds

  - **Property 19: Random number within bounds**
  - **Validates: Requirements 6.2**


- [x] 6.3 Write property test for correct operator selection by range


  - **Property 20: Correct operator selection by range**
  - **Validates: Requirements 6.3**




- [x] 6.4 Write property test for statistical distribution





  - **Property 21: Statistical distribution matches weights**
  - **Validates: Requirements 6.5, 5.3**

- [x] 7. Implement distribution service





  - Create services/distribution_service.py
  - Implement get_available_operators method with filtering logic
  - Implement assign_operator method with load increment
  - Implement handle_no_operators_available for unassigned requests
  - Add transaction management for atomic operations
  - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [x] 7.1 Write property test for available operator identification


  - **Property 15: Available operator identification**
  - **Validates: Requirements 5.1, 5.2**

- [x] 7.2 Write property test for load increment on assignment


  - **Property 16: Load increment on assignment**
  - **Validates: Requirements 5.4**

- [x] 7.3 Write property test for unassigned request handling


  - **Property 17: Unassigned request handling**
  - **Validates: Requirements 5.5**

- [x] 8. Implement operator service





  - Create services/operator_service.py
  - Implement create_operator method
  - Implement get_operators method
  - Implement update_operator method
  - Implement toggle_active method
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 8.1 Write property test for toggle active status


  - **Property 3: Toggle changes active status**
  - **Validates: Requirements 1.4**

- [x] 9. Implement source service





  - Create services/source_service.py
  - Implement create_source method
  - Implement get_sources method
  - Implement configure_weights method for operator-source weights
  - Add validation for weight range and uniqueness
  - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.4_

- [x] 9.1 Write property test for weight storage


  - **Property 7: Weight storage within valid range**
  - **Validates: Requirements 3.1**

- [x] 9.2 Write property test for weight update


  - **Property 8: Weight update modifies existing value**
  - **Validates: Requirements 3.2**

- [x] 9.3 Write property test for weight retrieval completeness


  - **Property 10: Weight retrieval completeness**
  - **Validates: Requirements 3.4**

- [x] 10. Implement request service





  - Create services/request_service.py
  - Implement create_request method with user auto-creation
  - Integrate distribution_service for operator assignment
  - Implement get_requests method
  - Implement get_request_by_id method with relationship loading
  - Add timestamp recording
  - _Requirements: 4.1, 4.2, 4.3, 4.5, 9.1, 9.2_

- [x] 10.1 Write property test for request creation


  - **Property 11: Request creation stores all data**
  - **Validates: Requirements 4.1**

- [x] 10.2 Write property test for new user auto-creation


  - **Property 12: New user auto-creation**
  - **Validates: Requirements 4.2**

- [x] 10.3 Write property test for request timestamp recording


  - **Property 14: Request timestamp recording**
  - **Validates: Requirements 4.5**

- [x] 10.4 Write property test for request detail retrieval


  - **Property 27: Request detail retrieval with relationships**
  - **Validates: Requirements 9.1, 9.3**

- [x] 11. Implement statistics service





  - Create services/stats_service.py
  - Implement get_operator_load_stats with percentage calculation
  - Implement get_request_distribution_stats grouped by operator
  - Implement get_request_distribution_by_source
  - Include unassigned requests in statistics
  - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_

- [x] 11.1 Write property test for operator load statistics


  - **Property 22: Operator load statistics calculation**
  - **Validates: Requirements 7.1, 7.2**

- [x] 11.2 Write property test for statistics include all operators


  - **Property 23: Statistics include all operators**
  - **Validates: Requirements 7.3**

- [x] 11.3 Write property test for request distribution by operator


  - **Property 24: Request distribution by operator**
  - **Validates: Requirements 8.1**

- [x] 11.4 Write property test for request distribution by source


  - **Property 25: Request distribution by source**
  - **Validates: Requirements 8.2**

- [x] 11.5 Write property test for unassigned requests in statistics


  - **Property 26: Unassigned requests in statistics**
  - **Validates: Requirements 8.3**

- [x] 12. Implement API endpoints for operators





  - Create api/v1/operators.py
  - Implement POST / endpoint for creating operators
  - Implement GET / endpoint for listing operators
  - Implement PUT /{id} endpoint for updating operators
  - Implement PUT /{id}/toggle-active endpoint
  - Add error handling and validation
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 13. Implement API endpoints for sources




  - Create api/v1/sources.py
  - Implement POST / endpoint for creating sources
  - Implement GET / endpoint for listing sources
  - Implement POST /{id}/operators endpoint for configuring weights
  - Add error handling and validation
  - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.4_

- [x] 14. Implement API endpoints for requests




  - Create api/v1/requests.py
  - Implement POST / endpoint for creating requests with distribution
  - Implement GET / endpoint for listing requests
  - Implement GET /{id} endpoint for request details
  - Add error handling and validation
  - _Requirements: 4.1, 4.2, 4.3, 9.1, 9.2_

- [x] 15. Implement API endpoints for statistics





  - Create api/v1/stats.py
  - Implement GET /operators-load endpoint
  - Implement GET /requests-distribution endpoint
  - Add response formatting
  - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_



- [x] 16. Wire up FastAPI application


  - Configure FastAPI app in main.py
  - Register all API routers with /api/v1 prefix
  - Add CORS middleware if needed
  - Configure exception handlers
  - Add startup/shutdown events for database
  - _Requirements: All_

- [x] 16.1 Write property test for foreign key integrity


  - **Property 28: Foreign key integrity**
  - **Validates: Requirements 10.2, 10.3**

- [x] 16.2 Write property test for operator assignment validation


  - **Property 29: Operator assignment validation**
  - **Validates: Requirements 10.1**

- [x] 16.3 Write property test for cascade deletion prevention



  - **Property 30: Cascade deletion prevention**
  - **Validates: Requirements 10.4, 10.5**

- [ ] 17. Add database indexes for performance








  - Create migration for indexes on operators(is_active, current_load)
  - Add index on operator_source_weights(source_id)
  - Add index on requests(operator_id, source_id, status)
  - Add index on users(identifier)
  - _Requirements: Performance optimization_

- [x] 18. Checkpoint - Ensure all tests pass


  - Ensure all tests pass, ask the user if questions arise.
