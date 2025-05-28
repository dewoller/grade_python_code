"""
Parsers module for extracting data from assignment files.

This module provides parsers for:
- Jupyter notebooks: Extract programming tasks and student solutions
- Rubric files: Parse marking criteria and point allocations
"""

from .notebook_parser import NotebookParser

__all__ = ['NotebookParser']
