"""
Output generation module for creating student marking sheets.

This module provides functionality to generate Excel files containing 
student marks and feedback in a standardized format.
"""

from .excel_generator import ExcelGenerator
from .formatting import ExcelFormatter

__all__ = ['ExcelGenerator', 'ExcelFormatter']
