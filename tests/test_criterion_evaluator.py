"""
Tests for the criterion evaluator module.

This module contains comprehensive tests for the CriterionEvaluator class,
including unit tests for different evaluation scenarios and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from src.marking.criterion_evaluator import CriterionEvaluator, EvaluationResult


class TestCriterionEvaluator:
    """Test suite for CriterionEvaluator class."""
    
    @pytest.fixture
    def evaluator(self):
        """Create a CriterionEvaluator instance for testing."""
        return CriterionEvaluator(verbosity=0)  # Quiet mode for tests
    
    def test_initialization(self):
        """Test CriterionEvaluator initialization with various parameters."""
        # Default initialization
        evaluator = CriterionEvaluator()
        assert evaluator.model_name == "gpt-4o-mini"
        assert evaluator.max_retries == 3
        assert evaluator.base_delay == 1.0
        assert evaluator.max_delay == 60.0
        assert evaluator.verbosity == 0
        
        # Custom initialization
        evaluator = CriterionEvaluator(
            model_name="gpt-4",
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            verbosity=2
        )
        assert evaluator.model_name == "gpt-4"
        assert evaluator.max_retries == 5
        assert evaluator.base_delay == 2.0
        assert evaluator.max_delay == 120.0
        assert evaluator.verbosity == 2
    
    def test_exponential_backoff(self, evaluator):
        """Test exponential backoff calculation."""
        # Test exponential growth
        assert evaluator._exponential_backoff(0) == 1.0
        assert evaluator._exponential_backoff(1) == 2.0
        assert evaluator._exponential_backoff(2) == 4.0
        assert evaluator._exponential_backoff(3) == 8.0
        
        # Test max delay cap
        evaluator.max_delay = 5.0
        assert evaluator._exponential_backoff(10) == 5.0
    
    def test_calculate_confidence(self, evaluator):
        """Test confidence calculation logic."""
        # Perfect response
        confidence = evaluator._calculate_confidence("8", "Good implementation", 8, 10)
        assert confidence == 1.0
        
        # Non-numeric score ("excellent" is non-numeric, "Good work" has 9 chars < 10)
        confidence = evaluator._calculate_confidence("excellent", "Good work", 8, 10)
        assert abs(confidence - 0.5) < 0.01  # -0.3 for non-numeric, -0.2 for short reasoning
        
        # No reasoning
        confidence = evaluator._calculate_confidence("8", "", 8, 10)
        assert confidence == 0.8  # -0.2 for no reasoning
        
        # Invalid score range
        confidence = evaluator._calculate_confidence("15", "Good work that is long enough", 15, 10)
        assert confidence == 0.7  # -0.3 for invalid range
        
        # Empty response
        confidence = evaluator._calculate_confidence("", "", 0, 10)
        assert abs(confidence - 0.3) < 0.01  # -0.7 for empty response
    
    def test_evaluate_criterion_empty_code(self, evaluator):
        """Test evaluation with empty or whitespace-only code."""
        result = evaluator.evaluate_criterion("", "Test task", "Test criterion", 10)
        assert result.score == 0
        assert result.confidence == 1.0
        assert result.error == "EMPTY_CODE"
        
        result = evaluator.evaluate_criterion("   ", "Test task", "Test criterion", 10)
        assert result.score == 0
        assert result.confidence == 1.0
        assert result.error == "EMPTY_CODE"
    
    def test_evaluate_criterion_empty_criterion(self, evaluator):
        """Test evaluation with empty criterion."""
        result = evaluator.evaluate_criterion("print('hello')", "Test task", "", 10)
        assert result.score == 0
        assert result.confidence == 0.0
        assert result.error == "EMPTY_CRITERION"
    
    def test_evaluate_criterion_invalid_max_points(self, evaluator):
        """Test evaluation with invalid max_points."""
        result = evaluator.evaluate_criterion("print('hello')", "Test task", "Test criterion", 0)
        assert result.score == 0
        assert result.confidence == 0.0
        assert result.error == "INVALID_MAX_POINTS"
        
        result = evaluator.evaluate_criterion("print('hello')", "Test task", "Test criterion", -5)
        assert result.score == 0
        assert result.confidence == 0.0
        assert result.error == "INVALID_MAX_POINTS"
    
    def test_evaluate_criterion_placeholder_code(self, evaluator):
        """Test evaluation with placeholder code patterns."""
        placeholder_codes = [
            "# your code here",
            "# YOUR CODE HERE", 
            "# your solution here",
            "pass",
            "# TODO",
            "# implement this",
            "raise NotImplementedError",
        ]
        
        for code in placeholder_codes:
            result = evaluator.evaluate_criterion(code, "Test task", "Test criterion", 10)
            assert result.score == 0
            assert result.confidence == 1.0
            assert result.error == "PLACEHOLDER_CODE"
    
    def test_evaluate_criterion_syntax_error(self, evaluator):
        """Test evaluation with syntax errors."""
        syntax_error_codes = [
            "def func(\n    pass",  # Unclosed parenthesis
            "if True\n    print('hello')",  # Missing colon
            "print('hello'",  # Unclosed string
            "for i in range(10\n    print(i)",  # Unclosed parenthesis
        ]
        
        for code in syntax_error_codes:
            result = evaluator.evaluate_criterion(code, "Test task", "Test criterion", 10)
            assert result.score == 0
            assert result.confidence == 1.0
            assert result.error == "SYNTAX_ERROR"
    
    @patch('src.marking.criterion_evaluator.CriterionEvaluator._get_signature_instance')
    def test_evaluate_criterion_perfect_code(self, mock_get_instance, evaluator):
        """Test evaluation of perfect code that should get full marks."""
        # Setup mock
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.score = "10"
        mock_response.reasoning = "Perfect implementation with all requirements met"
        mock_instance.return_value = mock_response
        mock_get_instance.return_value = mock_instance
        
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
        """
        
        result = evaluator.evaluate_criterion(
            code, 
            "Implement recursive factorial function", 
            "Correct recursive implementation",
            10
        )
        
        assert result.score == 10
        assert result.confidence == 1.0
        assert result.error is None
        assert result.retry_count == 0
        assert "Perfect implementation" in result.raw_response
    
    @patch('src.marking.criterion_evaluator.CriterionEvaluator._get_signature_instance')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_evaluate_criterion_with_retries(self, mock_sleep, mock_get_instance, evaluator):
        """Test evaluation with API failures and retries."""
        # Setup mock to fail twice then succeed
        mock_instance = Mock()
        mock_instance.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"), 
            Mock(score="8", reasoning="Good implementation")
        ]
        mock_get_instance.return_value = mock_instance
        
        result = evaluator.evaluate_criterion(
            "def func(): return 42", 
            "Test task", 
            "Test criterion",
            10
        )
        
        assert result.score == 8
        assert result.confidence == 1.0
        assert result.error is None
        assert result.retry_count == 2  # Two retries before success
        assert mock_sleep.call_count == 2  # Should have slept twice


class TestEvaluationResult:
    """Test suite for EvaluationResult dataclass."""
    
    def test_evaluation_result_creation(self):
        """Test EvaluationResult creation with various parameters."""
        # Minimal creation
        result = EvaluationResult(score=8, confidence=0.9, raw_response="Good work")
        assert result.score == 8
        assert result.confidence == 0.9
        assert result.raw_response == "Good work"
        assert result.error is None
        assert result.retry_count == 0
        
        # Full creation
        result = EvaluationResult(
            score=5,
            confidence=0.7,
            raw_response="Partial implementation",
            error="API_WARNING",
            retry_count=2
        )
        assert result.score == 5
        assert result.confidence == 0.7
        assert result.raw_response == "Partial implementation"
        assert result.error == "API_WARNING"
        assert result.retry_count == 2


class TestIntegrationScenarios:
    """Integration tests for common evaluation scenarios."""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with higher verbosity for integration tests."""
        return CriterionEvaluator(verbosity=1)
    
    @patch('src.marking.criterion_evaluator.CriterionEvaluator._get_signature_instance')
    def test_real_world_scenario_complete_solution(self, mock_get_instance, evaluator):
        """Test evaluation of a complete, well-implemented solution."""
        # Setup mock for perfect solution
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.score = "10" 
        mock_response.reasoning = "Excellent implementation with proper error handling and edge cases"
        mock_instance.return_value = mock_response
        mock_get_instance.return_value = mock_instance
        
        code = """
def fibonacci(n):
    if n < 0:
        raise ValueError("Input must be non-negative")
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test cases
print(fibonacci(0))  # 0
print(fibonacci(1))  # 1
print(fibonacci(5))  # 5
        """
        
        result = evaluator.evaluate_criterion(
            code=code,
            task_description="Implement a recursive Fibonacci function with error handling",
            criterion="Function correctly implements recursive Fibonacci with proper edge case handling",
            max_points=10
        )
        
        assert result.score == 10
        assert result.confidence == 1.0
        assert result.error is None
        assert "excellent implementation" in result.raw_response.lower()
    
    @patch('src.marking.criterion_evaluator.CriterionEvaluator.evaluate_criterion')
    def test_evaluate_multiple_criteria(self, mock_evaluate, evaluator):
        """Test evaluation of multiple criteria."""
        # Setup mock to return different results for different criteria
        def side_effect(code, task, criterion, max_points):
            if "criterion 1" in criterion:
                return EvaluationResult(8, 1.0, "Good work", None, 0)
            elif "criterion 2" in criterion:
                return EvaluationResult(6, 0.8, "Partial work", None, 0)
            else:
                return EvaluationResult(10, 1.0, "Perfect work", None, 0)
        
        mock_evaluate.side_effect = side_effect
        
        criteria = {
            "Test criterion 1": 10,
            "Test criterion 2": 8,
            "Test criterion 3": 6
        }
        
        results = evaluator.evaluate_multiple_criteria(
            "def func(): return 42",
            "Test task",
            criteria
        )
        
        assert len(results) == 3
        assert results["Test criterion 1"].score == 8
        assert results["Test criterion 2"].score == 6
        assert results["Test criterion 3"].score == 10
        
        # Verify all criteria were evaluated
        assert mock_evaluate.call_count == 3


class TestErrorHandling:
    """Test suite focused on error handling scenarios."""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator for error handling tests."""
        return CriterionEvaluator(max_retries=2, verbosity=0)
    
    def test_invalid_code_patterns(self, evaluator):
        """Test handling of various invalid code patterns."""
        invalid_patterns = [
            ("", "EMPTY_CODE"),
            ("   \n\t  ", "EMPTY_CODE"),
            ("# your code here", "PLACEHOLDER_CODE"),
            ("pass", "PLACEHOLDER_CODE"),
            ("def func(\n    pass", "SYNTAX_ERROR"),
            ("print('unclosed string", "SYNTAX_ERROR"),
        ]
        
        for code, expected_error in invalid_patterns:
            result = evaluator.evaluate_criterion(
                code, "Test task", "Test criterion", 10
            )
            assert result.score == 0
            assert result.error == expected_error
            assert result.confidence in [0.0, 1.0]  # Should be definitive
    
    @patch('src.marking.criterion_evaluator.CriterionEvaluator._get_signature_instance')
    def test_malformed_api_responses(self, mock_get_instance, evaluator):
        """Test handling of malformed API responses."""
        # Test cases with different malformed responses
        test_cases = [
            (Mock(score="", reasoning="Good work"), "Missing score"),
            (Mock(score="invalid", reasoning=""), "Invalid score format"),
            (Mock(score="", reasoning=""), "Missing both score and reasoning"),
        ]
        
        for mock_response, description in test_cases:
            mock_instance = Mock()
            mock_instance.return_value = mock_response
            mock_get_instance.return_value = mock_instance
            
            result = evaluator.evaluate_criterion(
                "def func(): return 42",
                "Test task",
                "Test criterion",
                10
            )
            
            # Should handle gracefully with reduced confidence
            assert isinstance(result.score, int)
            assert 0 <= result.score <= 10
            assert result.confidence < 1.0  # Confidence should be reduced
            assert result.error is None  # No error, just low confidence
