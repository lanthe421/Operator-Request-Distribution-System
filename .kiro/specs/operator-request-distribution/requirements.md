# Requirements Document

## Introduction

Мини-CRM система для автоматического распределения входящих обращений от пользователей между операторами. Система учитывает загрузку операторов, их компетенции по разным каналам связи и правила распределения по весовым коэффициентам. Распределение происходит вероятностным методом на основе настроенных весов.

## Glossary

- **System** - Мини-CRM система распределения обращений
- **Operator** - Сотрудник, обрабатывающий обращения пользователей
- **User** - Пользователь, создающий обращение в систему
- **Request** - Обращение от пользователя, требующее обработки оператором
- **Source** - Источник/канал связи, через который поступает обращение (бот, email, телефон)
- **Weight** - Весовой коэффициент (1-100), определяющий вероятность назначения оператора для конкретного источника
- **Load** - Количество активных обращений, назначенных оператору
- **Active Operator** - Оператор, доступный для получения новых обращений
- **Available Operator** - Активный оператор, у которого текущая загрузка меньше максимального лимита

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to manage operators in the system, so that I can control who processes incoming requests.

#### Acceptance Criteria

1. WHEN an administrator creates a new operator with name and max_load_limit THEN the System SHALL store the operator with is_active set to True and current_load set to 0
2. WHEN an administrator retrieves the list of operators THEN the System SHALL return all operators with their current status and load information
3. WHEN an administrator updates an operator's max_load_limit THEN the System SHALL modify the operator's maximum load capacity
4. WHEN an administrator toggles an operator's active status THEN the System SHALL change the is_active flag and prevent or allow new request assignments accordingly
5. THE System SHALL ensure that operator names are non-empty strings

### Requirement 2

**User Story:** As a system administrator, I want to manage sources in the system, so that I can track different communication channels.

#### Acceptance Criteria

1. WHEN an administrator creates a new source with name and identifier THEN the System SHALL store the source with a unique identifier
2. WHEN an administrator retrieves the list of sources THEN the System SHALL return all registered sources
3. THE System SHALL ensure that source identifiers are unique across all sources
4. THE System SHALL ensure that source names are non-empty strings

### Requirement 3

**User Story:** As a system administrator, I want to configure operator weights for different sources, so that I can control request distribution based on operator competencies.

#### Acceptance Criteria

1. WHEN an administrator assigns a weight to an operator for a specific source THEN the System SHALL store the weight value between 1 and 100
2. WHEN an administrator updates an operator's weight for a source THEN the System SHALL modify the existing weight value
3. THE System SHALL reject weight values outside the range of 1 to 100
4. WHEN an administrator retrieves operator weights for a source THEN the System SHALL return all operators with their configured weights for that source

### Requirement 4

**User Story:** As a user, I want to submit requests through different sources, so that I can get help from operators.

#### Acceptance Criteria

1. WHEN a user submits a request with user_identifier, source_id, and message THEN the System SHALL create a new request record
2. WHEN a request is submitted with a new user_identifier THEN the System SHALL create a new user record with that identifier
3. WHEN a request is submitted with an existing user_identifier THEN the System SHALL associate the request with the existing user
4. THE System SHALL ensure that request messages are non-empty strings
5. THE System SHALL record the creation timestamp for each request

### Requirement 5

**User Story:** As the system, I want to automatically assign requests to available operators, so that workload is distributed efficiently.

#### Acceptance Criteria

1. WHEN a new request is created for a source THEN the System SHALL identify all available operators for that source
2. WHEN identifying available operators THEN the System SHALL select only operators where is_active equals True and current_load is less than max_load_limit and weight is configured for the source
3. WHEN multiple available operators exist THEN the System SHALL use weighted random selection based on operator weights
4. WHEN an operator is assigned to a request THEN the System SHALL increment the operator's current_load by 1
5. WHEN no available operators exist THEN the System SHALL create the request with operator_id set to NULL and status set to waiting

### Requirement 6

**User Story:** As a system, I want to implement weighted random distribution, so that operators with higher weights receive proportionally more requests.

#### Acceptance Criteria

1. WHEN calculating weighted random selection THEN the System SHALL compute the sum of all available operator weights
2. WHEN selecting an operator THEN the System SHALL generate a random number between 0 and the total weight sum
3. WHEN the random number is generated THEN the System SHALL assign the request to the operator whose weight range contains that number
4. THE System SHALL ensure that operators with weight 0 are excluded from selection
5. THE System SHALL ensure that the probability of selection is proportional to the operator's weight relative to the total weight sum

### Requirement 7

**User Story:** As a system administrator, I want to view operator load statistics, so that I can monitor workload distribution.

#### Acceptance Criteria

1. WHEN an administrator requests operator load statistics THEN the System SHALL return each operator's current_load and max_load_limit
2. WHEN displaying operator statistics THEN the System SHALL calculate the load percentage for each operator
3. THE System SHALL include both active and inactive operators in the statistics

### Requirement 8

**User Story:** As a system administrator, I want to view request distribution statistics, so that I can analyze how requests are distributed across operators and sources.

#### Acceptance Criteria

1. WHEN an administrator requests distribution statistics THEN the System SHALL return the count of requests grouped by operator
2. WHEN displaying distribution statistics THEN the System SHALL include requests grouped by source
3. WHEN calculating statistics THEN the System SHALL include requests with NULL operator_id as unassigned requests

### Requirement 9

**User Story:** As a system administrator, I want to retrieve request details, so that I can review individual requests and their assignments.

#### Acceptance Criteria

1. WHEN an administrator requests a specific request by ID THEN the System SHALL return the request with user, source, and operator information
2. WHEN an administrator requests the list of all requests THEN the System SHALL return all requests with their current status and assignment information
3. THE System SHALL include the creation timestamp in request details

### Requirement 10

**User Story:** As a system, I want to maintain data integrity, so that the system state remains consistent.

#### Acceptance Criteria

1. WHEN an operator is assigned to a request THEN the System SHALL ensure the operator exists and is active
2. WHEN a request references a source THEN the System SHALL ensure the source exists
3. WHEN a request references a user THEN the System SHALL ensure the user exists
4. THE System SHALL prevent deletion of operators that have assigned requests
5. THE System SHALL prevent deletion of sources that have associated requests
