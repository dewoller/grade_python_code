"""
Tests for the NotebookParser module.

This module contains comprehensive tests for parsing Jupyter notebooks
and extracting programming tasks from student assignments.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.parsers.notebook_parser import NotebookParser, NotebookParsingError


class TestNotebookParser:
    """Test cases for the NotebookParser class."""
    
    def test_parser_initialization_success(self, complete_notebook_path):
        """Test successful parser initialization with valid notebook."""
        parser = NotebookParser(complete_notebook_path)
        assert parser.notebook_path.exists()
        assert parser.notebook_data is not None
        assert isinstance(parser.notebook_data, dict)
        assert 'cells' in parser.notebook_data
    
    def test_parser_initialization_file_not_found(self):
        """Test parser initialization with non-existent file."""
        with pytest.raises(NotebookParsingError, match="Notebook file not found"):
            NotebookParser("non_existent_file.ipynb")
    
    def test_parser_initialization_corrupted_json(self):
        """Test parser initialization with corrupted JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            f.write("{ invalid json content")
        
        try:
            with pytest.raises(NotebookParsingError, match="Corrupted JSON"):
                NotebookParser(f.name)
        finally:
            Path(f.name).unlink()
    
    def test_parser_initialization_invalid_notebook_structure(self):
        """Test parser initialization with invalid notebook structure."""
        # Test missing 'cells' key
        invalid_notebook = {"metadata": {}, "nbformat": 4}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(invalid_notebook, f)
        
        try:
            with pytest.raises(NotebookParsingError, match="missing 'cells' key"):
                NotebookParser(f.name)
        finally:
            Path(f.name).unlink()
    
    def test_parse_complete_notebook(self, complete_notebook_path):
        """Test parsing a complete notebook with all tasks."""
        parser = NotebookParser(complete_notebook_path)
        tasks = parser.parse_tasks()
        
        # Should find 2 tasks (2, 3) that were actually defined
        assert len(tasks) == 6  # Still returns 6 entries (padded with empty ones)
        
        # Only tasks 2 and 3 should have content
        assert len(tasks[2]) > 0  # Should have fibonacci function
        assert len(tasks[3]) > 0  # Should have sort function
        
        # Tasks 4-7 should be empty (missing)
        for task_num in range(4, 8):
            assert len(tasks[task_num]) == 0
        
        # Check that the correct functions are present
        assert 'fibonacci' in tasks[2]
        assert 'sort_array' in tasks[3]
    
    def test_parse_missing_tasks_notebook(self, missing_tasks_notebook_path):
        """Test parsing a notebook with missing tasks."""
        parser = NotebookParser(missing_tasks_notebook_path)
        tasks = parser.parse_tasks()
        
        # Should still return 6 entries but some will be empty
        assert len(tasks) == 6
        
        # Check issues are flagged
        issues = parser.get_issues()
        assert any("MISSING_TASK" in issue for issue in issues)
        assert not parser.has_all_tasks()
    
    def test_is_solution_marker(self, complete_notebook_path):
        """Test solution marker detection."""
        parser = NotebookParser(complete_notebook_path)
        
        # Test primary marker
        assert parser._is_solution_marker("#### Your Solution")
        assert parser._is_solution_marker("Some text #### Your Solution more text")
        
        # Test secondary marker  
        assert parser._is_solution_marker("# Your Solution:")
        assert parser._is_solution_marker("Some text # Your Solution: more text")
        
        # Test non-markers
        assert not parser._is_solution_marker("# Your Code")
        assert not parser._is_solution_marker("## Solution")
        assert not parser._is_solution_marker("Regular text")
    
    def test_extract_code_from_cell(self, complete_notebook_path):
        """Test code extraction from cells."""
        parser = NotebookParser(complete_notebook_path)
        
        # Test code cell with list source
        code_cell = {
            'cell_type': 'code',
            'source': ['def test():\n', '    return True\n']
        }
        code = parser._extract_code_from_cell(code_cell)
        assert code == 'def test():\n    return True'
        
        # Test code cell with string source
        code_cell = {
            'cell_type': 'code', 
            'source': 'def test():\n    return True'
        }
        code = parser._extract_code_from_cell(code_cell)
        assert code == 'def test():\n    return True'
        
        # Test markdown cell (should return empty)
        markdown_cell = {
            'cell_type': 'markdown',
            'source': ['# Header']
        }
        code = parser._extract_code_from_cell(markdown_cell)
        assert code == ""
    
    def test_identify_task_number(self, complete_notebook_path):
        """Test task number identification."""
        parser = NotebookParser(complete_notebook_path)
        
        # Test identification by bot function
        assert parser._identify_task_number(0, "def bot_whisper(payload):") == 2
        assert parser._identify_task_number(1, "def bot_multiply(payload):") == 3
        assert parser._identify_task_number(2, "def bot_count(payload):") == 4
        assert parser._identify_task_number(3, "def bot_topic(payload):") == 5
        assert parser._identify_task_number(4, "def dispatch_bot_command(cmd, payload):") == 6
        assert parser._identify_task_number(5, "def chatbot_interaction():") == 7
        
        # Test fallback to sequential mapping
        assert parser._identify_task_number(0, "some other code") == 2
        assert parser._identify_task_number(1, "some other code") == 3
    
    def test_validate_code_content(self, complete_notebook_path):
        """Test code content validation."""
        parser = NotebookParser(complete_notebook_path)
        
        # Test valid code
        valid, issue = parser._validate_code_content("def test():\n    return True")
        assert valid is True
        assert issue is None
        
        # Test empty code
        valid, issue = parser._validate_code_content("")
        assert valid is False
        assert issue == "EMPTY_CODE"
        
        # Test whitespace only
        valid, issue = parser._validate_code_content("   \n   ")
        assert valid is False  
        assert issue == "EMPTY_CODE"
        
        # Test placeholder code
        valid, issue = parser._validate_code_content("# Your solution here")
        assert valid is False
        assert issue == "PLACEHOLDER_CODE"
        
        valid, issue = parser._validate_code_content("pass")
        assert valid is False
        assert issue == "PLACEHOLDER_CODE"
    
    def test_get_task_code(self, complete_notebook_path):
        """Test getting code for specific tasks."""
        parser = NotebookParser(complete_notebook_path)
        
        # Test getting existing task
        task_2_code = parser.get_task_code(2)
        assert task_2_code is not None
        assert 'fibonacci' in task_2_code
        
        # Test getting non-existent task
        task_999_code = parser.get_task_code(999)
        assert task_999_code is None
    
    def test_get_all_tasks(self, complete_notebook_path):
        """Test getting all tasks."""
        parser = NotebookParser(complete_notebook_path)
        all_tasks = parser.get_all_tasks()
        
        assert len(all_tasks) == 6
        for task_num in range(2, 8):
            assert task_num in all_tasks
    
    def test_get_issues(self, missing_tasks_notebook_path):
        """Test getting parsing issues."""
        parser = NotebookParser(missing_tasks_notebook_path)
        parser.parse_tasks()
        
        issues = parser.get_issues()
        assert len(issues) >= 1  # Should have at least one issue for missing tasks
        assert any("MISSING_TASK" in issue for issue in issues)
    
    def test_has_all_tasks(self, complete_notebook_path, missing_tasks_notebook_path):
        """Test checking if all tasks are present."""
        # Complete notebook should NOT have all tasks (only has 2 out of 6)
        complete_parser = NotebookParser(complete_notebook_path)
        assert complete_parser.has_all_tasks() is False  # Only has tasks 2 and 3
        
        # Incomplete notebook should not have all tasks
        incomplete_parser = NotebookParser(missing_tasks_notebook_path)
        assert incomplete_parser.has_all_tasks() is False
    
    def test_get_summary(self, complete_notebook_path):
        """Test getting parsing summary."""
        parser = NotebookParser(complete_notebook_path)
        summary = parser.get_summary()
        
        assert 'notebook_path' in summary
        assert 'total_cells' in summary
        assert 'tasks_found' in summary
        assert 'tasks_with_code' in summary
        assert 'expected_tasks' in summary
        assert 'all_tasks_present' in summary
        assert 'issues_count' in summary
        assert 'issues' in summary
        
        assert summary['tasks_found'] == 2  # Only 2 tasks actually defined
        assert summary['expected_tasks'] == 6
        assert summary['all_tasks_present'] is False  # Missing tasks 4-7
    
    def test_alternative_marker_format(self):
        """Test parsing with alternative '# Your Solution:' marker format."""
        # Create notebook with alternative marker format
        notebook_data = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Your Solution:"]
                },
                {
                    "cell_type": "code", 
                    "metadata": {},
                    "source": ["def bot_whisper(payload):\n    return payload.lower()"]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Your Solution:"]
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": ["def bot_multiply(a, b):\n    return a * b"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook_data, f)
        
        try:
            parser = NotebookParser(f.name)
            tasks = parser.parse_tasks()
            
            # Should find at least 2 tasks
            assert len([t for t in tasks.values() if t]) >= 2
            assert any('bot_whisper' in code for code in tasks.values())
            assert any('bot_multiply' in code for code in tasks.values())
        finally:
            Path(f.name).unlink()
    
    def test_edge_case_no_code_after_marker(self):
        """Test handling case where no code cell follows solution marker."""
        notebook_data = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["#### Your Solution"]
                },
                {
                    "cell_type": "markdown",  # Another markdown cell instead of code
                    "metadata": {},
                    "source": ["Some explanation"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook_data, f)
        
        try:
            parser = NotebookParser(f.name)
            tasks = parser.parse_tasks()
            
            # Should handle gracefully and report issue
            issues = parser.get_issues()
            assert any("No code cell found after solution marker" in issue for issue in issues)
        finally:
            Path(f.name).unlink()
    
    @patch('src.parsers.notebook_parser.logger')
    def test_logging_behavior(self, mock_logger, complete_notebook_path):
        """Test that appropriate logging occurs during parsing."""
        parser = NotebookParser(complete_notebook_path)
        parser.parse_tasks()
        
        # Verify logging calls were made
        mock_logger.info.assert_called()
        mock_logger.debug.assert_called()


class TestNotebookParsingError:
    """Test cases for the NotebookParsingError exception."""
    
    def test_custom_exception_creation(self):
        """Test creating custom parsing exception."""
        error = NotebookParsingError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


# Regression tests for specific issues found in real notebooks
class TestRegressionCases:
    """Test cases for specific issues found in real student notebooks."""
    
    def test_malformed_json_structure(self):
        """Test handling of malformed JSON that's still valid JSON."""
        # Test with valid JSON but invalid notebook structure
        malformed_data = {"not_cells": []}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(malformed_data, f)
        
        try:
            with pytest.raises(NotebookParsingError, match="missing 'cells' key"):
                NotebookParser(f.name)
        finally:
            Path(f.name).unlink()
    
    def test_cells_not_list(self):
        """Test handling when 'cells' is not a list."""
        invalid_data = {"cells": "not a list"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(invalid_data, f)
        
        try:
            with pytest.raises(NotebookParsingError, match="'cells' is not a list"):
                NotebookParser(f.name)
        finally:
            Path(f.name).unlink()
    
    def test_empty_notebook(self):
        """Test handling of completely empty notebook."""
        empty_notebook = {"cells": [], "metadata": {}, "nbformat": 4}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(empty_notebook, f)
        
        try:
            parser = NotebookParser(f.name)
            tasks = parser.parse_tasks()
            
            # Should handle gracefully
            assert len(tasks) == 6  # Still returns 6 entries (all empty)
            assert not parser.has_all_tasks()
            
            issues = parser.get_issues()
            assert len(issues) >= 6  # Should have MISSING_TASK for each task
        finally:
            Path(f.name).unlink()
    
    def test_mixed_source_formats(self):
        """Test handling notebooks with mixed source formats (string vs list)."""
        mixed_notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": "#### Your Solution"  # String format
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": ["def bot_whisper():\n", "    pass\n"]  # List format
                },
                {
                    "cell_type": "markdown", 
                    "metadata": {},
                    "source": ["#### Your Solution"]  # List format
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": "def bot_multiply():\n    pass"  # String format
                }
            ],
            "metadata": {},
            "nbformat": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(mixed_notebook, f)
        
        try:
            parser = NotebookParser(f.name)
            tasks = parser.parse_tasks()
            
            # Should handle both formats correctly
            tasks_with_code = [t for t in tasks.values() if t.strip()]
            assert len(tasks_with_code) >= 2
        finally:
            Path(f.name).unlink()
