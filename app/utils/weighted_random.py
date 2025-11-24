"""
Weighted random selection algorithm for operator distribution.
"""
import random
from typing import List, Tuple, Optional, TypeVar, Any


T = TypeVar('T')


def select_operator_by_weight(operators_with_weights: List[Tuple[T, int]]) -> Optional[T]:
    """
    Select an operator using weighted random selection with cumulative weights method.
    
    Algorithm:
    1. Calculate the sum of all weights
    2. Generate a random number between 0 and total weight
    3. Iterate through operators, accumulating weights
    4. Return the operator whose cumulative range contains the random number
    
    Example:
        operators = [("A", 50), ("B", 30), ("C", 20)]
        # Total weight = 100
        # Ranges: A=[0,50), B=[50,80), C=[80,100)
        # If random=65, select B
    
    Args:
        operators_with_weights: List of (operator, weight) tuples
        
    Returns:
        Selected operator or None if list is empty
    """
    if not operators_with_weights:
        return None
    
    # Calculate total weight
    total_weight = sum(weight for _, weight in operators_with_weights)
    
    if total_weight == 0:
        return None
    
    # Generate random number in range [0, total_weight)
    random_value = random.uniform(0, total_weight)
    
    # Find operator by cumulative weight
    cumulative = 0
    for operator, weight in operators_with_weights:
        cumulative += weight
        if random_value < cumulative:
            return operator
    
    # Fallback (should not reach here due to floating point precision)
    return operators_with_weights[-1][0]
