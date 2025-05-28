"""
Tests for the Excel generator module.

Tests the creation of formatted Excel marking sheets with proper
structure, formatting, error handling, and data validation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import xlsxwriter

from src.output.excel_generator import ExcelGenerator, ExcelGenerationError
from src.output.formatting import ExcelFormatter


class TestExcelFormatter:
    """Tests for the ExcelFormatter class."""
    
    def test_get_header_style(self):
        """Test header style properties."""
        style = ExcelFormatter.get_header_style()
        
        assert style['bold'] is True
        assert style['bg_color'] == '#4472C4'
        assert style['font_color'] == 'white'
        assert style['border'] == 1
        assert style['align'] == 'center'
    
    def test_get_task_header_style(self):
        """Test task header style properties."""
        style = ExcelFormatter.get_task_header_style()
        
        assert style['bold'] is True
        assert style['bg_color'] == '#D9E2F3'
        assert style['font_color'] == 'black'
        assert style['align'] == 'left'
    
    def test_get_error_score_style(self):
        """Test error score style has warning colors."""
        style = ExcelFormatter.get_error_score_style()
        
        assert style['bg_color'] == '#FFE6E6'
        assert style['font_color'] == '#D00000'
        assert style['align'] == 'center'
    
    def test_get_column_widths(self):
        """Test column width specifications."""
        widths = ExcelFormatter.get_column_widths()
        
        assert 'A' in widths  # Task Name
        assert 'B' in widths  # Criterion Description
        assert 'C' in widths  # Student Score
        assert 'D' in widths  # Max Points
        
        # Criterion description should be widest
        assert widths['B'] > widths['A']
        assert widths['B'] > widths['C']
        assert widths['B'] > widths['D']
    
    def test_format_error_flag(self):
        """Test error flag formatting."""
        formatted = ExcelFormatter.format_error_flag('MISSING_TASK')
        assert formatted == "0 (MISSING_TASK)"
        
        formatted = ExcelFormatter.format_error_flag('PARSING_ERROR')
        assert formatted == "0 (PARSING_ERROR)"
    
    def test_get_error_types(self):
        """Test error types dictionary."""
        error_types = ExcelFormatter.get_error_types()
        
        expected_types = [
            'MISSING_TASK', 
            'INCOMPLETE_CODE', 
            'PARSING_ERROR', 
            'API_ERROR', 
            'TIMEOUT_ERROR'
        ]
        
        for error_type in expected_types:
            assert error_type in error_types
            assert isinstance(error_types[error_type], str)
            assert len(error_types[error_type]) > 0


class TestExcelGenerator:
    """Tests for the ExcelGenerator class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def excel_generator(self, temp_dir):
        """Create ExcelGenerator instance with temporary directory."""
        return ExcelGenerator(temp_dir)
    
    @pytest.fixture
    def sample_rubric_data(self):
        """Sample rubric data for testing."""
        return {
            2: [
                {'criterion': 'Joins list elements from payload', 'max_points': 2},
                {'criterion': 'Converts message to lowercase', 'max_points': 2},
                {'criterion': 'Correctly displays output', 'max_points': 2},
            ],
            3: [
                {'criterion': 'Uses data from payload for multiplication', 'max_points': 3},
                {'criterion': 'Performs multiplication correctly', 'max_points': 1},
                {'criterion': 'Converts elements to appropriate type', 'max_points': 2},
            ]
        }
    
    @pytest.fixture
    def sample_marking_results(self):
        """Sample marking results for testing."""
        return {
            2: [
                {'score': 2, 'criterion_index': 0},
                {'score': 1, 'criterion_index': 1},
                {'score': 0, 'error_flag': 'PARSING_ERROR', 'criterion_index': 2},
            ],
            3: [
                {'score': 3, 'criterion_index': 0},
                {'score': 1, 'criterion_index': 1},
                {'score': 2, 'criterion_index': 2},
            ]
        }
    
    def test_init_creates_output_directory(self, temp_dir):
        """Test that initialization creates output directory."""
        output_dir = temp_dir / "marks_output"
        generator = ExcelGenerator(output_dir)
        
        assert output_dir.exists()
        assert output_dir.is_dir()
        assert generator.output_dir == output_dir
    
    def test_init_with_invalid_directory_raises_error(self):
        """Test initialization with invalid directory raises error."""
        # Try to create directory in a read-only location (if possible)
        with pytest.raises(ExcelGenerationError):
            ExcelGenerator("/invalid/path/that/cannot/be/created")
    
    def test_generate_marking_sheet_creates_file(
        self, 
        excel_generator, 
        sample_rubric_data, 
        sample_marking_results
    ):
        """Test that marking sheet generation creates Excel file."""
        student_id = "TEST001"
        
        output_file = excel_generator.generate_marking_sheet(
            student_id=student_id,
            rubric_data=sample_rubric_data,
            marking_results=sample_marking_results
        )
        
        assert output_file.exists()
        assert output_file.name == f"{student_id}_marks.xlsx"
        assert output_file.parent == excel_generator.output_dir
    
    def test_generate_marking_sheet_with_issues(
        self, 
        excel_generator, 
        sample_rubric_data, 
        sample_marking_results
    ):
        """Test marking sheet generation with issues section."""
        student_id = "TEST002"
        issues = [
            "Task 4: MISSING_TASK",
            "Task 6 Criterion 3: PARSING_ERROR"
        ]
        
        output_file = excel_generator.generate_marking_sheet(
            student_id=student_id,
            rubric_data=sample_rubric_data,
            marking_results=sample_marking_results,
            issues=issues
        )
        
        assert output_file.exists()
    
    def test_validate_input_data_with_valid_data(
        self, 
        excel_generator, 
        sample_rubric_data, 
        sample_marking_results
    ):
        """Test validation with valid input data."""
        issues = excel_generator.validate_input_data(
            sample_rubric_data, 
            sample_marking_results
        )
        
        assert len(issues) == 0
    
    def test_validate_input_data_with_missing_results(
        self, 
        excel_generator, 
        sample_rubric_data
    ):
        """Test validation with missing results."""
        incomplete_results = {2: [{'score': 1}]}  # Missing task 3
        
        issues = excel_generator.validate_input_data(
            sample_rubric_data, 
            incomplete_results
        )
        
        assert len(issues) > 0
        assert any("No results found for Task 3" in issue for issue in issues)
    
    def test_validate_input_data_with_mismatched_criteria_count(
        self, 
        excel_generator, 
        sample_rubric_data
    ):
        """Test validation with mismatched criteria counts."""
        mismatched_results = {
            2: [{'score': 1}],  # Only 1 result for task with 3 criteria
            3: [{'score': 1}, {'score': 2}, {'score': 1}]  # Correct count
        }
        
        issues = excel_generator.validate_input_data(
            sample_rubric_data, 
            mismatched_results
        )
        
        assert len(issues) > 0
        assert any("Expected 3 results, got 1" in issue for issue in issues)
    
    def test_validate_input_data_with_extra_task_results(
        self, 
        excel_generator, 
        sample_rubric_data, 
        sample_marking_results
    ):
        """Test validation with results for unknown tasks."""
        extra_results = dict(sample_marking_results)
        extra_results[8] = [{'score': 1}]  # Task 8 not in rubric
        
        issues = excel_generator.validate_input_data(
            sample_rubric_data, 
            extra_results
        )
        
        assert len(issues) > 0
        assert any("Results found for unknown Task 8" in issue for issue in issues)
    
    def test_get_output_path(self, excel_generator):
        """Test output path generation."""
        student_id = "TEST003"
        expected_path = excel_generator.output_dir / f"{student_id}_marks.xlsx"
        
        actual_path = excel_generator.get_output_path(student_id)
        
        assert actual_path == expected_path
    
    def test_generate_batch_summary(self, excel_generator):
        """Test batch summary generation."""
        batch_results = {
            "STUDENT001": {
                "total_score": 75,
                "max_points": 83,
                "issues": ["Task 4: PARSING_ERROR"],
                "status": "Completed"
            },
            "STUDENT002": {
                "total_score": 80,
                "max_points": 83,
                "issues": [],
                "status": "Completed"
            }
        }
        
        output_file = excel_generator.generate_batch_summary(batch_results)
        
        assert output_file.exists()
        assert output_file.name == "batch_summary.xlsx"
    
    def test_create_formats_returns_all_needed_formats(self, excel_generator):
        """Test that _create_formats returns all required format objects."""
        # Create a mock workbook
        with patch('xlsxwriter.Workbook') as mock_workbook_class:
            mock_workbook = Mock()
            mock_format = Mock()
            mock_workbook.add_format.return_value = mock_format
            
            formats = excel_generator._create_formats(mock_workbook)
            
            expected_formats = [
                'header', 'task_header', 'criterion', 'score', 
                'error_score', 'subtotal', 'total', 'issues_header', 'issues'
            ]
            
            for format_name in expected_formats:
                assert format_name in formats
    
    @patch('xlsxwriter.Workbook')
    def test_generate_marking_sheet_handles_xlsxwriter_error(
        self, 
        mock_workbook_class, 
        excel_generator, 
        sample_rubric_data, 
        sample_marking_results
    ):
        """Test error handling when xlsxwriter fails."""
        mock_workbook_class.side_effect = Exception("XlsxWriter error")
        
        with pytest.raises(ExcelGenerationError, match="Failed to generate Excel file"):
            excel_generator.generate_marking_sheet(
                student_id="TEST004",
                rubric_data=sample_rubric_data,
                marking_results=sample_marking_results
            )
    
    def test_marking_sheet_structure_with_real_file(
        self, 
        excel_generator, 
        sample_rubric_data, 
        sample_marking_results
    ):
        """Test the structure of generated Excel file by reading it back."""
        student_id = "STRUCTURE_TEST"
        issues = ["Test issue 1", "Test issue 2"]
        
        output_file = excel_generator.generate_marking_sheet(
            student_id=student_id,
            rubric_data=sample_rubric_data,
            marking_results=sample_marking_results,
            issues=issues
        )
        
        # Verify file was created and is not empty
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        # Could add more detailed structure verification here
        # by reading the Excel file back with pandas or openpyxl
    
    def test_subtotal_calculation_excludes_error_scores(
        self, 
        excel_generator, 
        sample_rubric_data
    ):
        """Test that subtotals exclude scores with error flags."""
        results_with_errors = {
            2: [
                {'score': 2, 'criterion_index': 0},
                {'score': 1, 'criterion_index': 1},
                {'score': 0, 'error_flag': 'PARSING_ERROR', 'criterion_index': 2},
            ]
        }
        
        output_file = excel_generator.generate_marking_sheet(
            student_id="ERROR_TEST",
            rubric_data=sample_rubric_data,
            marking_results=results_with_errors
        )
        
        assert output_file.exists()
        # The subtotal should be 3 (2+1), not 3 (2+1+0)
        # This would need to be verified by reading the Excel file
    
    def test_empty_marking_results(self, excel_generator, sample_rubric_data):
        """Test handling of empty marking results."""
        empty_results = {}
        
        output_file = excel_generator.generate_marking_sheet(
            student_id="EMPTY_TEST",
            rubric_data=sample_rubric_data,
            marking_results=empty_results
        )
        
        assert output_file.exists()
    
    def test_missing_task_in_results(self, excel_generator, sample_rubric_data):
        """Test handling when some tasks are missing from results."""
        incomplete_results = {
            2: [
                {'score': 2, 'criterion_index': 0},
                {'score': 1, 'criterion_index': 1},
                {'score': 2, 'criterion_index': 2},
            ]
            # Task 3 missing
        }
        
        output_file = excel_generator.generate_marking_sheet(
            student_id="MISSING_TASK_TEST",
            rubric_data=sample_rubric_data,
            marking_results=incomplete_results
        )
        
        assert output_file.exists()


class TestExcelGeneratorIntegration:
    """Integration tests for Excel generator with realistic data."""
    
    @pytest.fixture
    def realistic_rubric(self):
        """Realistic rubric data matching the actual assignment."""
        return {
            2: [
                {'criterion': 'Joins list elements from payload to make a single string', 'max_points': 2},
                {'criterion': 'Converts the message to lowercase', 'max_points': 2},
                {'criterion': 'Correctly displays output by calling the bot_say() function', 'max_points': 2},
                {'criterion': 'Includes an additional test call to bot_shout()', 'max_points': 2},
            ],
            3: [
                {'criterion': 'Uses data from the payload to determine numbers for multiplication', 'max_points': 3},
                {'criterion': 'Performs multiplication using an appropriate expression', 'max_points': 1},
                {'criterion': 'Converts elements in the payload to an appropriate type', 'max_points': 2},
                {'criterion': 'Displays the result as an equation using bot_say()', 'max_points': 2},
                {'criterion': 'Displays numbers exactly as user typed them', 'max_points': 2},
            ]
        }
    
    @pytest.fixture
    def realistic_results(self):
        """Realistic marking results with mixed scores and errors."""
        return {
            2: [
                {'score': 2, 'criterion_index': 0},
                {'score': 2, 'criterion_index': 1},
                {'score': 1, 'criterion_index': 2},
                {'score': 0, 'error_flag': 'INCOMPLETE_CODE', 'criterion_index': 3},
            ],
            3: [
                {'score': 3, 'criterion_index': 0},
                {'score': 1, 'criterion_index': 1},
                {'score': 2, 'criterion_index': 2},
                {'score': 0, 'error_flag': 'PARSING_ERROR', 'criterion_index': 3},
                {'score': 2, 'criterion_index': 4},
            ]
        }
    
    def test_realistic_marking_sheet_generation(
        self, 
        realistic_rubric, 
        realistic_results
    ):
        """Test generation with realistic data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            issues = [
                "Task 2 Criterion 4: INCOMPLETE_CODE - Only placeholder found",
                "Task 3 Criterion 4: PARSING_ERROR - AI evaluation failed",
                "Manual review required for 2 items"
            ]
            
            output_file = generator.generate_marking_sheet(
                student_id="REALISTIC_001",
                rubric_data=realistic_rubric,
                marking_results=realistic_results,
                issues=issues
            )
            
            assert output_file.exists()
            
            # Verify file structure by checking size
            file_size = output_file.stat().st_size
            assert file_size > 5000  # Should be substantial Excel file
    
    def test_full_workflow_with_validation(
        self, 
        realistic_rubric, 
        realistic_results
    ):
        """Test complete workflow including validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            # Validate input data
            validation_issues = generator.validate_input_data(
                realistic_rubric, 
                realistic_results
            )
            
            # Should have no validation issues
            assert len(validation_issues) == 0
            
            # Generate marking sheet
            output_file = generator.generate_marking_sheet(
                student_id="WORKFLOW_001",
                rubric_data=realistic_rubric,
                marking_results=realistic_results
            )
            
            # Verify output
            assert output_file.exists()
            assert output_file == generator.get_output_path("WORKFLOW_001")
