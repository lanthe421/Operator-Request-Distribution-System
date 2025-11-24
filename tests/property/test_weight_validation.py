"""
Property-based tests for weight boundary validation.

Feature: operator-request-distribution, Property 9: Weight boundary validation
Validates: Requirements 3.3
"""
import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from app.schemas.source import OperatorWeightConfig


class TestWeightBoundaryValidation:
    """
    Property 9: Weight boundary validation
    For any weight value less than 1 or greater than 100, 
    the system should reject the weight assignment.
    Validates: Requirements 3.3
    """
    
    @given(
        operator_id=st.integers(min_value=1, max_value=1000),
        weight=st.integers(max_value=0)
    )
    def test_weight_below_minimum_rejected(self, operator_id: int, weight: int):
        """
        Feature: operator-request-distribution, Property 9: Weight boundary validation
        
        Test that weight values less than 1 are rejected.
        """
        with pytest.raises(ValidationError) as exc_info:
            OperatorWeightConfig(operator_id=operator_id, weight=weight)
        
        # Verify that the error is about weight validation
        errors = exc_info.value.errors()
        assert any('weight' in str(error.get('loc', [])) for error in errors), \
            f"Expected weight validation error, got: {errors}"
    
    @given(
        operator_id=st.integers(min_value=1, max_value=1000),
        weight=st.integers(min_value=101)
    )
    def test_weight_above_maximum_rejected(self, operator_id: int, weight: int):
        """
        Feature: operator-request-distribution, Property 9: Weight boundary validation
        
        Test that weight values greater than 100 are rejected.
        """
        with pytest.raises(ValidationError) as exc_info:
            OperatorWeightConfig(operator_id=operator_id, weight=weight)
        
        # Verify that the error is about weight validation
        errors = exc_info.value.errors()
        assert any('weight' in str(error.get('loc', [])) for error in errors), \
            f"Expected weight validation error, got: {errors}"
    
    @given(
        operator_id=st.integers(min_value=1, max_value=1000),
        weight=st.integers(min_value=1, max_value=100)
    )
    def test_weight_within_valid_range_accepted(self, operator_id: int, weight: int):
        """
        Feature: operator-request-distribution, Property 9: Weight boundary validation
        
        Test that weight values between 1 and 100 (inclusive) are accepted.
        """
        config = OperatorWeightConfig(operator_id=operator_id, weight=weight)
        
        assert config.operator_id == operator_id
        assert config.weight == weight
        assert 1 <= config.weight <= 100
