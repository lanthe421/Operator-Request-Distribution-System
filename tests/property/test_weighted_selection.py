"""
Property-based tests for weighted random selection algorithm.
"""
import random
from typing import List, Tuple
from hypothesis import given, strategies as st, settings, assume
from app.utils.weighted_random import select_operator_by_weight


# Strategy for generating valid weights (1-100)
valid_weight = st.integers(min_value=1, max_value=100)

# Strategy for generating lists of (operator, weight) tuples
operators_with_weights = st.lists(
    st.tuples(st.text(min_size=1, max_size=50), valid_weight),
    min_size=1,
    max_size=20
)


@given(operators_with_weights)
@settings(max_examples=100)
def test_weight_sum_calculation(ops_weights: List[Tuple[str, int]]):
    """
    Feature: operator-request-distribution, Property 18: Weight sum calculation
    
    For any list of operators with weights, the sum of all weights should equal
    the total used for random selection.
    
    Validates: Requirements 6.1
    """
    # Calculate expected sum
    expected_sum = sum(weight for _, weight in ops_weights)
    
    # Mock random.uniform to capture the total parameter
    original_uniform = random.uniform
    captured_total = None
    
    def mock_uniform(a, b):
        nonlocal captured_total
        captured_total = b
        return original_uniform(a, b)
    
    random.uniform = mock_uniform
    try:
        # Call the function
        select_operator_by_weight(ops_weights)
        
        # Verify the total matches expected sum
        assert captured_total == expected_sum, \
            f"Weight sum mismatch: expected {expected_sum}, got {captured_total}"
    finally:
        random.uniform = original_uniform


@given(operators_with_weights)
@settings(max_examples=100)
def test_random_number_within_bounds(ops_weights: List[Tuple[str, int]]):
    """
    Feature: operator-request-distribution, Property 19: Random number within bounds
    
    For any weighted random selection, the generated random number should be
    greater than or equal to 0 and less than the total weight sum.
    
    Validates: Requirements 6.2
    """
    total_weight = sum(weight for _, weight in ops_weights)
    
    # Mock random.uniform to capture parameters
    original_uniform = random.uniform
    captured_calls = []
    
    def mock_uniform(a, b):
        captured_calls.append((a, b))
        return original_uniform(a, b)
    
    random.uniform = mock_uniform
    try:
        # Call the function
        select_operator_by_weight(ops_weights)
        
        # Verify bounds
        assert len(captured_calls) == 1, "Should call random.uniform exactly once"
        a, b = captured_calls[0]
        assert a == 0, f"Lower bound should be 0, got {a}"
        assert b == total_weight, f"Upper bound should be {total_weight}, got {b}"
    finally:
        random.uniform = original_uniform


@given(
    ops_weights=operators_with_weights,
    seed=st.integers(min_value=0, max_value=1000000)
)
@settings(max_examples=100)
def test_correct_operator_selection_by_range(
    ops_weights: List[Tuple[str, int]], 
    seed: int
):
    """
    Feature: operator-request-distribution, Property 20: Correct operator selection by range
    
    For any mocked random value and list of operators with weights, the selected
    operator should be the one whose cumulative weight range contains the random value.
    
    Validates: Requirements 6.3
    """
    # Calculate cumulative weights
    cumulative_weights = []
    total = 0
    for _, weight in ops_weights:
        total += weight
        cumulative_weights.append(total)
    
    # Generate a deterministic random value
    random.seed(seed)
    random_value = random.uniform(0, total)
    
    # Determine expected operator manually
    expected_index = 0
    for i, cum_weight in enumerate(cumulative_weights):
        if random_value < cum_weight:
            expected_index = i
            break
    expected_operator = ops_weights[expected_index][0]
    
    # Mock random.uniform to return our specific value
    original_uniform = random.uniform
    
    def mock_uniform(a, b):
        return random_value
    
    random.uniform = mock_uniform
    try:
        # Call the function
        selected = select_operator_by_weight(ops_weights)
        
        # Verify correct selection
        assert selected == expected_operator, \
            f"Expected operator {expected_operator}, got {selected} for random value {random_value}"
    finally:
        random.uniform = original_uniform


@given(
    ops_weights=st.lists(
        st.tuples(st.text(min_size=1, max_size=10), valid_weight),
        min_size=2,
        max_size=5
    )
)
@settings(max_examples=50, deadline=None)
def test_statistical_distribution_matches_weights(ops_weights: List[Tuple[str, int]]):
    """
    Feature: operator-request-distribution, Property 21: Statistical distribution matches weights
    
    For any set of operators with configured weights, running the distribution
    algorithm many times should result in selection frequencies proportional to
    the weights (within statistical tolerance).
    
    Validates: Requirements 6.5, 5.3
    """
    # Ensure we have unique operators for counting
    unique_ops = {}
    for op, weight in ops_weights:
        if op not in unique_ops:
            unique_ops[op] = weight
        else:
            # Sum weights for duplicate operators
            unique_ops[op] += weight
    
    # Skip if we don't have at least 2 unique operators
    assume(len(unique_ops) >= 2)
    
    ops_list = list(unique_ops.items())
    total_weight = sum(unique_ops.values())
    
    # Run selection many times
    iterations = 1000
    selection_counts = {op: 0 for op, _ in ops_list}
    
    for _ in range(iterations):
        selected = select_operator_by_weight(ops_list)
        selection_counts[selected] += 1
    
    # Verify proportions are within tolerance
    # Using chi-square-like tolerance: allow 3 standard deviations
    # For binomial distribution: std = sqrt(n * p * (1-p))
    # We use a simpler approach: absolute tolerance of 5% or relative tolerance of 30%
    
    for op, weight in ops_list:
        expected_proportion = weight / total_weight
        actual_proportion = selection_counts[op] / iterations
        expected_count = expected_proportion * iterations
        
        # Calculate standard deviation for binomial distribution
        std_dev = (expected_proportion * (1 - expected_proportion) * iterations) ** 0.5
        
        # Allow 3 standard deviations (99.7% confidence interval)
        max_allowed_difference = 3 * std_dev / iterations
        
        # Also ensure minimum absolute tolerance of 5%
        max_allowed_difference = max(max_allowed_difference, 0.05)
        
        difference = abs(actual_proportion - expected_proportion)
        
        assert difference <= max_allowed_difference, \
            f"Operator {op}: expected proportion {expected_proportion:.3f}, " \
            f"got {actual_proportion:.3f} (difference {difference:.3f} > {max_allowed_difference:.3f})"


def test_empty_list_returns_none():
    """
    Edge case: Empty operator list should return None.
    """
    result = select_operator_by_weight([])
    assert result is None, "Empty list should return None"
