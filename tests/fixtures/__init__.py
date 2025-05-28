"""
Test fixtures package for the marking system.

This package provides comprehensive test fixtures including:
- Jupyter notebooks with various scenarios
- Rubric CSV files  
- Mock API responses
- Expected Excel outputs

All fixtures are generated programmatically for consistent testing.
"""

from .generate_fixtures import FixtureCoordinator
from .notebook_generator import NotebookFixtureGenerator
from .rubric_generator import RubricFixtureGenerator
from .api_mock_generator import APIResponseGenerator
from .excel_mock_generator import ExcelMockGenerator

__all__ = [
    'FixtureCoordinator',
    'NotebookFixtureGenerator', 
    'RubricFixtureGenerator',
    'APIResponseGenerator',
    'ExcelMockGenerator'
]
