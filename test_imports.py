#!/usr/bin/env python3
"""
Simple test to check imports before running main test suite.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all required imports for integration tests."""
    try:
        print("Testing basic imports...")
        
        # Test error handling imports
        from src.utils.error_handling import (
            NotebookParsingError, 
            RubricParsingError, 
            CriterionEvaluationError
        )
        print("✓ Error handling imports successful")
        
        # Test marking imports
        from src.marking.assignment_marker import AssignmentMarker
        print("✓ AssignmentMarker import successful")
        
        # Test parsers
        from src.parsers.notebook_parser import NotebookParser
        from src.parsers.rubric_parser import RubricParser
        print("✓ Parser imports successful")
        
        # Test output
        from src.output.excel_generator import ExcelGenerator
        print("✓ Excel generator import successful")
        
        print("All imports successful!")
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
