"""
Tests for the RubricParser module.

This module contains comprehensive tests for parsing CSV rubric files
and extracting task criteria and point allocations.
"""

import pytest
import pandas as pd
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.parsers.rubric_parser import RubricParser, RubricParsingError


class TestRubricParser:
    """Test cases for the RubricParser class."""
    
    def test_parser_initialization_success(self, valid_rubric_path):
        """Test successful parser initialization with valid rubric."""
        parser = RubricParser(valid_rubric_path)
        assert parser.rubric_path.exists()
        assert parser.rubric_data is not None
        assert isinstance(parser.rubric_data, pd.DataFrame)
    
    def test_parser_initialization_file_not_found(self):
        """Test parser initialization with non-existent file."""
        with pytest.raises(RubricParsingError, match="Rubric file not found"):
            RubricParser("non_existent_file.csv")
    
    def test_parser_initialization_empty_file(self):
        """Test parser initialization with empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pass  # Create empty file
        
        try:
            with pytest.raises(RubricParsingError, match="Rubric CSV file is empty"):
                RubricParser(f.name)
        finally:
            Path(f.name).unlink()
    
    def test_parser_initialization_malformed_csv(self):
        """Test parser initialization with malformed CSV."""
        # Test by mocking pandas to raise a ParserError
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("some,basic,csv,data\n")
        
        try:
            # Mock pandas to raise a ParserError
            with patch('src.parsers.rubric_parser.pd.read_csv') as mock_read_csv:
                mock_read_csv.side_effect = pd.errors.ParserError("Test parser error")
                
                with pytest.raises(RubricParsingError, match="Error parsing CSV file"):
                    RubricParser(f.name)
        finally:
            Path(f.name).unlink()
    
    def test_parser_initialization_unicode_error(self):
        """Test parser initialization with unicode decoding error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("some,basic,csv,data\n")
        
        try:
            # Mock pandas to raise a UnicodeDecodeError
            with patch('src.parsers.rubric_parser.pd.read_csv') as mock_read_csv:
                mock_read_csv.side_effect = UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid start byte')
                
                with pytest.raises(RubricParsingError, match="Error reading CSV file encoding"):
                    RubricParser(f.name)
        finally:
            Path(f.name).unlink()
    
    def test_parse_valid_rubric(self, valid_rubric_path):
        """Test parsing a valid rubric file."""
        parser = RubricParser(valid_rubric_path)
        tasks = parser.parse_rubric()
        
        # Should find all 6 tasks (2-7)
        assert len(tasks) == 6
        for task_num in range(2, 8):
            assert task_num in tasks
            assert len(tasks[task_num]) > 0  # Should have criteria
        
        # Check expected point totals
        expected_points = {2: 8, 3: 10, 4: 15, 5: 15, 6: 15, 7: 20}
        for task_num, expected in expected_points.items():
            actual = sum(c['max_points'] for c in tasks[task_num])
            assert actual == expected, f"Task {task_num}: expected {expected}, got {actual}"
    
    def test_parse_invalid_rubric(self, invalid_rubric_path):
        """Test parsing an invalid rubric file."""
        parser = RubricParser(invalid_rubric_path)
        tasks = parser.parse_rubric()
        
        # Should still parse but have issues
        issues = parser.get_issues()
        assert len(issues) > 0
        assert not parser.is_valid()
    
    def test_extract_task_number(self, valid_rubric_path):
        """Test task number extraction."""
        parser = RubricParser(valid_rubric_path)
        
        # Test valid task patterns
        assert parser._extract_task_number("Task 2") == 2
        assert parser._extract_task_number("Task 7") == 7
        assert parser._extract_task_number("  Task 3  ") == 3
        assert parser._extract_task_number("Task 5,Something") == 5
        
        # Test invalid patterns
        assert parser._extract_task_number("Task 1") is None  # Out of range
        assert parser._extract_task_number("Task 8") is None  # Out of range
        assert parser._extract_task_number("Not a task") is None
        assert parser._extract_task_number("") is None
        assert parser._extract_task_number(None) is None
    
    def test_parse_max_points(self, valid_rubric_path):
        """Test maximum points parsing."""
        parser = RubricParser(valid_rubric_path)
        
        # Test valid point values
        assert parser._parse_max_points("2") == 2
        assert parser._parse_max_points("10") == 10
        assert parser._parse_max_points("  5  ") == 5
        assert parser._parse_max_points("3.0") == 3
        
        # Test invalid values
        assert parser._parse_max_points("") is None
        assert parser._parse_max_points("abc") is None
        assert parser._parse_max_points(None) is None
        assert parser._parse_max_points("  ") is None
    
    def test_is_subtotal_row(self, valid_rubric_path):
        """Test subtotal row detection."""
        parser = RubricParser(valid_rubric_path)
        
        # Create test rows
        subtotal_row = pd.Series({
            'task': '',
            'criterion': 'SUBTOTAL',
            'score': '0',
            'max_points': '8'
        })
        
        regular_row = pd.Series({
            'task': 'Task 2',
            'criterion': 'Some criterion',
            'score': '',
            'max_points': '2'
        })
        
        assert parser._is_subtotal_row(subtotal_row) is True
        assert parser._is_subtotal_row(regular_row) is False
    
    def test_is_empty_row(self, valid_rubric_path):
        """Test empty row detection."""
        parser = RubricParser(valid_rubric_path)
        
        # Create test rows
        empty_row = pd.Series({
            'task': '',
            'criterion': '',
            'score': '',
            'max_points': ''
        })
        
        whitespace_row = pd.Series({
            'task': '  ',
            'criterion': '\t',
            'score': '',
            'max_points': ' '
        })
        
        content_row = pd.Series({
            'task': 'Task 2',
            'criterion': '',
            'score': '',
            'max_points': '2'
        })
        
        assert parser._is_empty_row(empty_row) is True
        assert parser._is_empty_row(whitespace_row) is True
        assert parser._is_empty_row(content_row) is False
    
    def test_get_task_criteria(self, valid_rubric_path):
        """Test getting criteria for specific tasks."""
        parser = RubricParser(valid_rubric_path)
        
        # Test getting existing task
        task_2_criteria = parser.get_task_criteria(2)
        assert task_2_criteria is not None
        assert len(task_2_criteria) == 3  # Task 2 should have 3 criteria per fixture
        
        # Check criterion structure
        for criterion in task_2_criteria:
            assert 'task_number' in criterion
            assert 'criterion' in criterion
            assert 'max_points' in criterion
            assert criterion['task_number'] == 2
            assert isinstance(criterion['max_points'], int)
        
        # Test getting non-existent task
        task_999_criteria = parser.get_task_criteria(999)
        assert task_999_criteria is None
    
    def test_get_all_tasks(self, valid_rubric_path):
        """Test getting all tasks."""
        parser = RubricParser(valid_rubric_path)
        all_tasks = parser.get_all_tasks()
        
        assert len(all_tasks) == 6
        for task_num in range(2, 8):
            assert task_num in all_tasks
            assert len(all_tasks[task_num]) > 0
    
    def test_get_task_max_points(self, valid_rubric_path):
        """Test getting maximum points for tasks."""
        parser = RubricParser(valid_rubric_path)
        
        # Test expected point values
        expected_points = {2: 8, 3: 10, 4: 15, 5: 15, 6: 15, 7: 20}
        for task_num, expected in expected_points.items():
            actual = parser.get_task_max_points(task_num)
            assert actual == expected
        
        # Test non-existent task
        assert parser.get_task_max_points(999) == 0
    
    def test_get_total_max_points(self, valid_rubric_path):
        """Test getting total maximum points."""
        parser = RubricParser(valid_rubric_path)
        total = parser.get_total_max_points()
        assert total == 83  # Expected total
    
    def test_get_issues(self, invalid_rubric_path):
        """Test getting parsing issues."""
        parser = RubricParser(invalid_rubric_path)
        parser.parse_rubric()
        
        issues = parser.get_issues()
        assert len(issues) >= 1
        assert all(isinstance(issue, str) for issue in issues)
    
    def test_is_valid(self, valid_rubric_path, invalid_rubric_path):
        """Test rubric validation."""
        # Valid rubric should be valid
        valid_parser = RubricParser(valid_rubric_path)
        assert valid_parser.is_valid() is True
        
        # Invalid rubric should not be valid
        invalid_parser = RubricParser(invalid_rubric_path)
        assert invalid_parser.is_valid() is False
    
    def test_get_criterion_by_index(self, valid_rubric_path):
        """Test getting specific criterion by index."""
        parser = RubricParser(valid_rubric_path)
        
        # Test getting existing criterion
        criterion = parser.get_criterion_by_index(2, 0)
        assert criterion is not None
        assert criterion['task_number'] == 2
        assert 'criterion' in criterion
        assert 'max_points' in criterion
        
        # Test invalid indices
        assert parser.get_criterion_by_index(2, 999) is None
        assert parser.get_criterion_by_index(999, 0) is None
    
    def test_get_summary(self, valid_rubric_path):
        """Test getting rubric summary."""
        parser = RubricParser(valid_rubric_path)
        summary = parser.get_summary()
        
        # Check required fields
        required_fields = [
            'rubric_path', 'total_rows', 'tasks_found', 'expected_tasks',
            'total_criteria', 'total_max_points', 'expected_total_points',
            'is_valid', 'issues_count', 'issues', 'task_summaries'
        ]
        for field in required_fields:
            assert field in summary
        
        # Check values
        assert summary['tasks_found'] == 6
        assert summary['expected_tasks'] == 6
        assert summary['total_max_points'] == 83
        assert summary['expected_total_points'] == 83
        assert summary['is_valid'] is True
        
        # Check task summaries
        assert len(summary['task_summaries']) == 6
        for task_num in range(2, 8):
            assert task_num in summary['task_summaries']
            task_summary = summary['task_summaries'][task_num]
            assert 'criteria_count' in task_summary
            assert 'max_points' in task_summary
            assert 'expected_points' in task_summary
    
    def test_export_structured_rubric(self, valid_rubric_path):
        """Test exporting structured rubric data."""
        parser = RubricParser(valid_rubric_path)
        structured = parser.export_structured_rubric()
        
        # Check top-level structure
        assert 'metadata' in structured
        assert 'tasks' in structured
        
        # Check metadata
        metadata = structured['metadata']
        assert metadata['total_points'] == 83
        assert metadata['task_count'] == 6
        assert metadata['is_valid'] is True
        
        # Check tasks structure
        tasks = structured['tasks']
        assert len(tasks) == 6
        
        for task_num in range(2, 8):
            assert task_num in tasks
            task_data = tasks[task_num]
            
            assert 'task_number' in task_data
            assert 'max_points' in task_data
            assert 'criteria_count' in task_data
            assert 'criteria' in task_data
            
            # Check criteria structure
            criteria = task_data['criteria']
            assert len(criteria) > 0
            
            for criterion in criteria:
                assert 'index' in criterion
                assert 'description' in criterion
                assert 'max_points' in criterion
                assert isinstance(criterion['index'], int)
                assert isinstance(criterion['description'], str)
                assert isinstance(criterion['max_points'], int)
    
    def test_validate_task_structure(self, valid_rubric_path):
        """Test task structure validation."""
        parser = RubricParser(valid_rubric_path)
        
        # Create test tasks with correct structure
        correct_tasks = {
            2: [{'max_points': 2}, {'max_points': 2}, {'max_points': 2}, {'max_points': 2}],  # 8 points
            3: [{'max_points': 3}, {'max_points': 1}, {'max_points': 2}, {'max_points': 2}, {'max_points': 2}]  # 10 points
        }
        
        # Should not raise issues for correct tasks
        initial_issues = len(parser.issues)
        parser._validate_task_structure(correct_tasks)
        # Should have some issues about missing tasks, but not about point totals for existing tasks
        
        # Create test tasks with incorrect points
        incorrect_tasks = {
            2: [{'max_points': 5}],  # Wrong total (5 instead of 8)
            3: [{'max_points': 15}]  # Wrong total (15 instead of 10)
        }
        
        parser.issues = []  # Reset issues
        parser._validate_task_structure(incorrect_tasks)
        assert len(parser.issues) > 0
        assert any("Task 2: Expected 8 points, found 5" in issue for issue in parser.issues)
    
    @patch('src.parsers.rubric_parser.logger')
    def test_logging_behavior(self, mock_logger, valid_rubric_path):
        """Test that appropriate logging occurs during parsing."""
        parser = RubricParser(valid_rubric_path)
        parser.parse_rubric()
        
        # Verify logging calls were made
        mock_logger.info.assert_called()
        mock_logger.debug.assert_called()


class TestRubricParsingError:
    """Test cases for the RubricParsingError exception."""
    
    def test_custom_exception_creation(self):
        """Test creating custom parsing exception."""
        error = RubricParsingError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


# Regression tests for specific rubric parsing issues
class TestRegressionCases:
    """Test cases for specific issues found in real rubric files."""
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in rubric."""
        rubric_data = [
            ["Task 2", "Criterion with unicode: café", "", "2"],
            ["", "Another criterion with émojis 🎉", "", "3"]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rubric_data)
        
        try:
            parser = RubricParser(f.name)
            tasks = parser.parse_rubric()
            
            # Should handle unicode correctly
            assert len(tasks[2]) >= 2
            criteria_text = [c['criterion'] for c in tasks[2]]
            assert any("café" in text for text in criteria_text)
            assert any("🎉" in text for text in criteria_text)
        finally:
            Path(f.name).unlink()
    
    def test_mixed_case_task_names(self):
        """Test handling of mixed case in task names."""
        rubric_data = [
            ["task 2", "First criterion", "", "2"],
            ["TASK 3", "Second criterion", "", "3"],
            ["Task 4", "Third criterion", "", "2"]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerows(rubric_data)
        
        try:
            parser = RubricParser(f.name)
            tasks = parser.parse_rubric()
            
            # Should recognize all task formats
            assert 2 in tasks
            assert 3 in tasks
            assert 4 in tasks
        finally:
            Path(f.name).unlink()
    
    def test_extra_whitespace_handling(self):
        """Test handling of extra whitespace in CSV."""
        rubric_data = [
            ["  Task 2  ", "  Criterion with spaces  ", "", "  2  "],
            ["", "  Another criterion  ", "", "  3  "]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerows(rubric_data)
        
        try:
            parser = RubricParser(f.name)
            tasks = parser.parse_rubric()
            
            # Should handle whitespace correctly
            assert 2 in tasks
            assert len(tasks[2]) == 2
            
            # Check that whitespace is stripped
            for criterion in tasks[2]:
                assert not criterion['criterion'].startswith(' ')
                assert not criterion['criterion'].endswith(' ')
        finally:
            Path(f.name).unlink()
    
    def test_decimal_points_conversion(self):
        """Test conversion of decimal point values to integers."""
        rubric_data = [
            ["Task 2", "First criterion", "", "2.0"],
            ["", "Second criterion", "", "3.5"],  # Should convert to 3
            ["", "Third criterion", "", "1.9"]   # Should convert to 1
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerows(rubric_data)
        
        try:
            parser = RubricParser(f.name)
            tasks = parser.parse_rubric()
            
            # Should convert decimals to integers
            assert 2 in tasks
            assert len(tasks[2]) == 3
            
            points = [c['max_points'] for c in tasks[2]]
            assert points == [2, 3, 1]
        finally:
            Path(f.name).unlink()
    
    def test_missing_columns_handling(self):
        """Test handling of CSV with missing columns."""
        # CSV with only 3 columns instead of 4
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Task 2,First criterion,2\n")
            f.write(",Second criterion,3\n")
        
        try:
            parser = RubricParser(f.name)
            # Should handle gracefully but may have parsing issues
            tasks = parser.parse_rubric()
            # The exact behavior depends on pandas handling of missing columns
        finally:
            Path(f.name).unlink()
    
    def test_bom_handling(self):
        """Test handling of CSV files with BOM (Byte Order Mark)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows([
                ["Task 2", "First criterion", "", "2"],
                ["", "Second criterion", "", "3"]
            ])
        
        try:
            parser = RubricParser(f.name)
            tasks = parser.parse_rubric()
            
            # Should handle BOM correctly
            assert 2 in tasks
            assert len(tasks[2]) == 2
        finally:
            Path(f.name).unlink()
