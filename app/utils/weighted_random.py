"""
Weighted random selection utilities for operator distribution.
"""
import random
import bisect
from typing import List, Tuple, Optional, TypeVar

T = TypeVar('T')


def select_operator_by_weight(
    operators_with_weights: List[Tuple[T, int]]
) -> Optional[T]:
    """
    Select an item using weighted random selection.
    
    Uses cumulative weights method with binary search for efficient selection.
    The probability of selecting each item is proportional to its weight.
    
    Args:
        operators_with_weights: List of (item, weight) tuples where weight > 0
        
    Returns:
        Selected item or None if list is empty
        
    Example:
        >>> items = [('A', 20), ('B', 30), ('C', 50)]
        >>> selected = select_operator_by_weight(items)
        >>> # 'A' has 20% chance, 'B' has 30% chance, 'C' has 50% chance
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
    # bisect_right returns the index where random_value would be inserted
    # to keep the list sorted, which gives us the operator whose range
    # contains the random value
    index = bisect.bisect_right(cumulative_weights, random_value)
    
    return operators_with_weights[index][0]
