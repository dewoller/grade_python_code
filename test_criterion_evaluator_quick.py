#!/usr/bin/env python3
"""
Quick test script to verify the criterion evaluator fixes.
"""

import sys
import os
sys.path.append('/Users/dewoller/code/Richard_marking_project/code_evaluate_dspy')

from src.marking.criterion_evaluator import CriterionEvaluator, EvaluationResult

def test_confidence_calculation():
    """Test the confidence calculation logic."""
    evaluator = CriterionEvaluator(verbosity=0)
    
    # Test cases that were failing
    test_cases = [
        ("8", "Good implementation", 8, 10, 1.0, "Perfect response"),
        ("excellent", "Good work", 8, 10, 0.7, "Non-numeric score"),
        ("8", "", 8, 10, 0.8, "No reasoning"),
        ("15", "Good work", 15, 10, 0.7, "Invalid score range"),
        ("", "", 0, 10, 0.3, "Empty response"),
    ]
    
    print("Testing confidence calculation:")
    for raw_score, raw_reasoning, parsed_score, max_points, expected_confidence, description in test_cases:
        actual_confidence = evaluator._calculate_confidence(raw_score, raw_reasoning, parsed_score, max_points)
        passed = abs(actual_confidence - expected_confidence) < 0.01
        status = "✓" if passed else "✗"
        print(f"  {status} {description}: expected {expected_confidence}, got {actual_confidence:.2f}")

def test_syntax_vs_placeholder():
    """Test that syntax errors are detected before placeholder code."""
    evaluator = CriterionEvaluator(verbosity=0)
    
    test_cases = [
        ("pass", "PLACEHOLDER_CODE", "Lone pass statement"),
        ("def func(\n    pass", "SYNTAX_ERROR", "Unclosed parenthesis"),
        ("if True\n    print('hello')", "SYNTAX_ERROR", "Missing colon"),
        ("print('hello'", "SYNTAX_ERROR", "Unclosed string"),
    ]
    
    print("\nTesting syntax vs placeholder detection:")
    for code, expected_error, description in test_cases:
        result = evaluator.evaluate_criterion(code, "Test task", "Test criterion", 10)
        passed = result.error == expected_error
        status = "✓" if passed else "✗"
        print(f"  {status} {description}: expected {expected_error}, got {result.error}")

if __name__ == "__main__":
    test_confidence_calculation()
    test_syntax_vs_placeholder()
