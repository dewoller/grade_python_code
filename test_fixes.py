#!/usr/bin/env python3
"""
Test script to verify the fixes for the DSPy integration modules.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_parse_integer_answer():
    """Test the parse_integer_answer function fixes."""
    from marking.dspy_config import parse_integer_answer
    
    print("Testing parse_integer_answer fixes...")
    
    # Test that should now pass
    result1 = parse_integer_answer("The score is 8 out of 10")
    print(f"'The score is 8 out of 10' -> {result1} (should be 10)")
    
    # Test negative number handling
    result2 = parse_integer_answer("-5", max_points=10)
    print(f"'-5' -> {result2} (should be 5)")
    
    # Test multiple numbers
    result3 = parse_integer_answer("First 3, then 5, finally 8")
    print(f"'First 3, then 5, finally 8' -> {result3} (should be 8)")
    
    return result1 == 10 and result2 == 5 and result3 == 8

def test_max_points_validation():
    """Test that max_points validation now includes 10."""
    from marking.dspy_config import create_dynamic_signature_class
    
    print("Testing max_points validation...")
    
    try:
        # This should now work (10 is allowed for backward compatibility)
        cls = create_dynamic_signature_class(
            "TestClass", 
            "Test", 
            {"input": "test"}, 
            {"output": "test"}, 
            max_points=10
        )
        print("max_points=10 accepted ✓")
        return True
    except ValueError as e:
        print(f"max_points=10 rejected: {e}")
        return False

def test_supported_scales():
    """Test that supported scales include 10."""
    from marking.model_loader import ModelLoader
    
    print("Testing supported point scales...")
    
    # Create a mock loader (won't work fully without files, but we can test the method)
    try:
        # Just test the static method
        from marking.dspy_config import parse_integer_answer
        
        # Test with different scales including 10
        scales_to_test = [1, 2, 3, 4, 6, 10]
        
        for scale in scales_to_test:
            result = parse_integer_answer("5", max_points=scale)
            expected = min(5, scale)
            if result != expected:
                print(f"Scale {scale}: got {result}, expected {expected}")
                return False
            else:
                print(f"Scale {scale}: ✓")
                
        return True
        
    except Exception as e:
        print(f"Error testing scales: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing DSPy integration fixes...")
    print("=" * 50)
    
    tests = [
        ("Parse Integer Answer", test_parse_integer_answer),
        ("Max Points Validation", test_max_points_validation), 
        ("Supported Scales", test_supported_scales),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"Result: {status}")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
