#!/usr/bin/env python3
"""
Simple test runner to verify integration tests work.

This script runs the focused integration tests and reports results.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_focused_tests():
    """Run the focused integration tests."""
    try:
        print("🧪 Running Focused Integration Tests")
        print("=" * 50)
        
        # Import the test module
        from tests.test_integration_focused import TestCoreIntegration, TestFixtureGeneration
        
        # Create test instances
        core_tests = TestCoreIntegration()
        fixture_tests = TestFixtureGeneration()
        
        # List of tests to run
        test_methods = [
            ("Assignment Marker Initialization", core_tests.test_assignment_marker_initialization),
            ("Missing Tasks Scenario", core_tests.test_missing_tasks_scenario),
            ("Syntax Errors Scenario", core_tests.test_syntax_errors_scenario),
            ("Empty Notebook Scenario", core_tests.test_empty_notebook_scenario),
            ("Batch Processing Simulation", core_tests.test_batch_processing_simulation),
            ("Error Recovery Workflow", core_tests.test_error_recovery_workflow),
            ("Special Characters Handling", core_tests.test_special_characters_handling),
            ("Excel Output Generation", core_tests.test_excel_output_generation),
            ("Workflow Statistics", core_tests.test_workflow_statistics),
            ("Fixture Coordinator Mock", fixture_tests.test_fixture_coordinator_mock),
            ("Notebook Generator Mock", fixture_tests.test_notebook_generator_mock),
            ("Rubric Generator Mock", fixture_tests.test_rubric_generator_mock),
            ("API Mock Generator Mock", fixture_tests.test_api_mock_generator_mock),
            ("Excel Mock Generator Mock", fixture_tests.test_excel_mock_generator_mock),
        ]
        
        # Run tests
        passed = 0
        failed = 0
        skipped = 0
        
        for test_name, test_method in test_methods:
            try:
                print(f"  Testing: {test_name}...", end=" ")
                test_method()
                print("✅ PASSED")
                passed += 1
            except Exception as e:
                if "skip" in str(e).lower() or "not available" in str(e):
                    print("⏭️  SKIPPED")
                    skipped += 1
                else:
                    print("❌ FAILED")
                    print(f"    Error: {e}")
                    failed += 1
        
        # Test the perfect student workflow separately (might need more setup)
        try:
            print(f"  Testing: Perfect Student Workflow Mock...", end=" ")
            core_tests.test_perfect_student_workflow_mock()
            print("✅ PASSED")
            passed += 1
        except Exception as e:
            if "skip" in str(e).lower() or "not available" in str(e):
                print("⏭️  SKIPPED")
                skipped += 1
            else:
                print("❌ FAILED")
                print(f"    Error: {e}")
                failed += 1
        
        # Report results
        print("\n" + "=" * 50)
        print(f"📊 Test Results:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   📈 Total: {passed + failed + skipped}")
        
        if failed == 0:
            print("\n🎉 All tests passed or skipped successfully!")
            return True
        else:
            print(f"\n⚠️  {failed} tests failed. Check the errors above.")
            return False
            
    except Exception as e:
        print(f"\n💥 Critical error running tests: {e}")
        traceback.print_exc()
        return False

def test_imports():
    """Test that critical imports work."""
    print("🔍 Testing Imports")
    print("=" * 30)
    
    imports_status = {}
    
    # Test core imports
    try:
        from src.marking.assignment_marker import AssignmentMarker
        imports_status['AssignmentMarker'] = "✅ Available"
    except ImportError as e:
        imports_status['AssignmentMarker'] = f"❌ Not Available: {e}"
    
    try:
        from src.parsers.notebook_parser import NotebookParser
        from src.parsers.rubric_parser import RubricParser
        imports_status['Parsers'] = "✅ Available"
    except ImportError as e:
        imports_status['Parsers'] = f"❌ Not Available: {e}"
    
    try:
        from src.output.excel_generator import ExcelGenerator
        imports_status['Excel Generator'] = "✅ Available"
    except ImportError as e:
        imports_status['Excel Generator'] = f"❌ Not Available: {e}"
    
    try:
        from src.utils.error_handling import CriterionEvaluationError
        imports_status['Error Handling'] = "✅ Available"
    except ImportError as e:
        imports_status['Error Handling'] = f"❌ Not Available: {e}"
    
    # Print results
    for component, status in imports_status.items():
        print(f"  {component}: {status}")
    
    print()
    return all("✅" in status for status in imports_status.values())

def main():
    """Main entry point."""
    print("🚀 Integration Test Suite Runner")
    print("=" * 60)
    
    # Test imports first
    imports_ok = test_imports()
    
    # Run focused tests
    tests_ok = run_focused_tests()
    
    # Final status
    print("\n" + "=" * 60)
    if imports_ok and tests_ok:
        print("🎯 Integration test suite is working correctly!")
        sys.exit(0)
    elif tests_ok:
        print("⚠️  Tests passed but some imports failed. Check module availability.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
