"""
Tests for the CLI main module.

These tests cover the command-line interface functionality including
argument parsing, validation, and integration with the marking system.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from click.testing import CliRunner

from src.cli.main import cli, _validate_inputs, _run_dry_run, _run_marking
from src.utils.error_handling import FileNotFoundError, InvalidFileError, MarkingError
from src.marking.assignment_marker import AssignmentMarker, AssignmentMarkingError


class TestCLIValidation:
    """Test input validation functions."""
    
    def test_validate_inputs_valid_files(self, tmp_path, caplog):
        """Test validation with valid input files."""
        # Create test files
        notebook = tmp_path / "test.ipynb"
        notebook.write_text('{"cells": []}')
        
        rubric = tmp_path / "test.csv"
        rubric.write_text("task,criterion,score,max_points")
        
        output_dir = tmp_path / "output"
        
        # Mock logger
        logger = Mock()
        
        # Should not raise any exceptions
        _validate_inputs(notebook, rubric, output_dir, logger)
        
        # Logger should have debug messages
        assert logger.debug.call_count >= 3
    
    def test_validate_inputs_missing_notebook(self, tmp_path):
        """Test validation with missing notebook file."""
        notebook = tmp_path / "missing.ipynb"
        rubric = tmp_path / "test.csv"
        rubric.write_text("task,criterion")
        output_dir = tmp_path / "output"
        logger = Mock()
        
        with pytest.raises(FileNotFoundError, match="Notebook file not found"):
            _validate_inputs(notebook, rubric, output_dir, logger)
    
    def test_validate_inputs_invalid_notebook_extension(self, tmp_path):
        """Test validation with invalid notebook file extension."""
        notebook = tmp_path / "test.txt"
        notebook.write_text("not a notebook")
        rubric = tmp_path / "test.csv"
        rubric.write_text("task,criterion")
        output_dir = tmp_path / "output"
        logger = Mock()
        
        with pytest.raises(InvalidFileError, match="Invalid notebook file"):
            _validate_inputs(notebook, rubric, output_dir, logger)
    
    def test_validate_inputs_missing_rubric(self, tmp_path):
        """Test validation with missing rubric file."""
        notebook = tmp_path / "test.ipynb"
        notebook.write_text('{"cells": []}')
        rubric = tmp_path / "missing.csv"
        output_dir = tmp_path / "output"
        logger = Mock()
        
        with pytest.raises(FileNotFoundError, match="Rubric file not found"):
            _validate_inputs(notebook, rubric, output_dir, logger)
    
    def test_validate_inputs_invalid_rubric_extension(self, tmp_path):
        """Test validation with invalid rubric file extension."""
        notebook = tmp_path / "test.ipynb"
        notebook.write_text('{"cells": []}')
        rubric = tmp_path / "test.txt"
        rubric.write_text("not a csv")
        output_dir = tmp_path / "output"
        logger = Mock()
        
        with pytest.raises(InvalidFileError, match="Invalid rubric file"):
            _validate_inputs(notebook, rubric, output_dir, logger)


class TestCLICommands:
    """Test CLI command execution."""
    
    def test_cli_missing_required_args(self):
        """Test CLI with missing required arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        
        assert result.exit_code == 2  # Click error for missing required args
        assert "Missing option" in result.output
    
    def test_cli_help(self):
        """Test CLI help message."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Mark programming assignments" in result.output
        assert "--notebook" in result.output
        assert "--rubric" in result.output
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('src.cli.main.AssignmentMarker')
    def test_cli_valid_args_dry_run(self, mock_marker_class, tmp_path):
        """Test CLI with valid arguments in dry run mode."""
        # Create test files
        notebook = tmp_path / "test.ipynb"
        notebook.write_text('{"cells": [{"cell_type": "code", "source": ["print(1)"]}]}')
        
        rubric = tmp_path / "test.csv"
        rubric.write_text("Task,Criterion,Score,Max Points\nTask 2,Test,0,5")
        
        output_dir = tmp_path / "output"
        
        # Mock the marker
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.validate_setup.return_value = []
        mock_marker._load_notebook.return_value = ({2: "print(1)"}, [])
        mock_marker._load_rubric.return_value = ({2: [{"criterion": "Test", "max_points": 5}]}, [])
        mock_marker_class.return_value = mock_marker
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--notebook', str(notebook),
            '--rubric', str(rubric),
            '--output-dir', str(output_dir),
            '--student-id', 'test_student',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        assert "Running dry run" in result.output
        assert "Dry run completed successfully" in result.output
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('src.cli.main.AssignmentMarker')
    def test_cli_valid_args_actual_marking(self, mock_marker_class, tmp_path):
        """Test CLI with valid arguments for actual marking.""" 
        # Create test files
        notebook = tmp_path / "test.ipynb"
        notebook.write_text('{"cells": [{"cell_type": "code", "source": ["print(1)"]}]}')
        
        rubric = tmp_path / "test.csv"
        rubric.write_text("Task,Criterion,Score,Max Points\nTask 2,Test,0,5")
        
        output_dir = tmp_path / "output"
        
        # Mock the marker and result
        from src.marking.assignment_marker import MarkingResult, TaskResult
        mock_result = MarkingResult(
            student_id="test_student",
            total_score=4,
            max_points=5,
            task_results={2: TaskResult(task_number=2, code="print(1)", total_score=4, max_points=5)},
            status="Completed",
            processing_time=1.5
        )
        
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.mark_assignment.return_value = mock_result
        mock_marker.get_statistics.return_value = {
            'assignments_processed': 1,
            'total_api_calls': 3,
            'total_errors': 0,
            'total_processing_time': 1.5,
            'error_rate': 0.0
        }
        mock_marker_class.return_value = mock_marker
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--notebook', str(notebook),
            '--rubric', str(rubric),
            '--output-dir', str(output_dir),
            '--student-id', 'test_student'
        ])
        
        assert result.exit_code == 0
        assert "Processing student: test_student" in result.output
        assert "MARKING RESULTS" in result.output
        assert "4/5" in result.output
    
    def test_cli_missing_api_key(self, tmp_path):
        """Test CLI without API key set."""
        # Create test files
        notebook = tmp_path / "test.ipynb"
        notebook.write_text('{"cells": []}')
        
        rubric = tmp_path / "test.csv"
        rubric.write_text("task,criterion")
        
        output_dir = tmp_path / "output"
        
        # Ensure API key is not set
        with patch.dict(os.environ, {}, clear=True):
            runner = CliRunner()
            result = runner.invoke(cli, [
                '--notebook', str(notebook),
                '--rubric', str(rubric),
                '--output-dir', str(output_dir)
            ])
            
            assert result.exit_code == 1
            assert "OPENAI_API_KEY environment variable not set" in result.output
    
    def test_cli_nonexistent_notebook(self, tmp_path):
        """Test CLI with nonexistent notebook file."""
        rubric = tmp_path / "test.csv"
        rubric.write_text("task,criterion")
        output_dir = tmp_path / "output"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--notebook', str(tmp_path / "missing.ipynb"),
            '--rubric', str(rubric),
            '--output-dir', str(output_dir)
        ])
        
        assert result.exit_code == 2  # Click validation error for missing file
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('src.cli.main.AssignmentMarker')
    def test_cli_assignment_marking_error(self, mock_marker_class, tmp_path):
        """Test CLI when assignment marking fails."""
        # Create test files
        notebook = tmp_path / "test.ipynb"
        notebook.write_text('{"cells": []}')
        
        rubric = tmp_path / "test.csv"
        rubric.write_text("task,criterion")
        
        output_dir = tmp_path / "output"
        
        # Mock marker to raise error
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.mark_assignment.side_effect = AssignmentMarkingError("Test error")
        mock_marker_class.return_value = mock_marker
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--notebook', str(notebook),
            '--rubric', str(rubric),
            '--output-dir', str(output_dir)
        ])
        
        assert result.exit_code == 1
        assert "Assignment marking error" in result.output
    
    def test_cli_keyboard_interrupt(self, tmp_path):
        """Test CLI handling of keyboard interrupt."""
        # Create test files
        notebook = tmp_path / "test.ipynb"
        notebook.write_text('{"cells": []}')
        
        rubric = tmp_path / "test.csv"
        rubric.write_text("task,criterion")
        
        output_dir = tmp_path / "output"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.cli.main.AssignmentMarker') as mock_marker_class:
                mock_marker = Mock(spec=AssignmentMarker)
                mock_marker.mark_assignment.side_effect = KeyboardInterrupt()
                mock_marker_class.return_value = mock_marker
                
                runner = CliRunner()
                result = runner.invoke(cli, [
                    '--notebook', str(notebook),
                    '--rubric', str(rubric),
                    '--output-dir', str(output_dir)
                ])
                
                assert result.exit_code == 130
                assert "Process interrupted by user" in result.output


class TestDryRunFunction:
    """Test the dry run functionality."""
    
    def test_run_dry_run_success(self, capsys):
        """Test successful dry run execution."""
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.validate_setup.return_value = []
        mock_marker._load_notebook.return_value = ({2: "print(1)", 3: "x = 5"}, [])
        mock_marker._load_rubric.return_value = (
            {2: [{"criterion": "Test 1", "max_points": 5}], 3: [{"criterion": "Test 2", "max_points": 3}]}, 
            []
        )
        
        _run_dry_run(mock_marker, "test_student", "/path/to/notebook.ipynb", "/path/to/rubric.csv")
        
        captured = capsys.readouterr()
        assert "Running dry run for student: test_student" in captured.out
        assert "Notebook loaded: 2 tasks found" in captured.out
        assert "Rubric loaded: 2 tasks, 2 criteria, 8 points" in captured.out
        assert "Dry run completed successfully" in captured.out
    
    def test_run_dry_run_validation_failed(self, capsys):
        """Test dry run with validation failures."""
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.validate_setup.return_value = ["Missing file", "Invalid format"]
        
        _run_dry_run(mock_marker, "test_student", "/path/to/notebook.ipynb", "/path/to/rubric.csv")
        
        captured = capsys.readouterr()
        assert "Validation failed:" in captured.err
        assert "Missing file" in captured.out
        assert "Invalid format" in captured.out
    
    def test_run_dry_run_notebook_error(self, capsys):
        """Test dry run with notebook parsing error."""
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.validate_setup.return_value = []
        mock_marker._load_notebook.side_effect = Exception("Notebook error")
        
        _run_dry_run(mock_marker, "test_student", "/path/to/notebook.ipynb", "/path/to/rubric.csv")
        
        captured = capsys.readouterr()
        assert "Notebook parsing failed: Notebook error" in captured.err
    
    def test_run_dry_run_rubric_error(self, capsys):
        """Test dry run with rubric parsing error."""
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.validate_setup.return_value = []
        mock_marker._load_notebook.return_value = ({2: "print(1)"}, [])
        mock_marker._load_rubric.side_effect = Exception("Rubric error")
        
        _run_dry_run(mock_marker, "test_student", "/path/to/notebook.ipynb", "/path/to/rubric.csv")
        
        captured = capsys.readouterr()
        assert "Rubric parsing failed: Rubric error" in captured.err


class TestMarkingFunction:
    """Test the actual marking functionality."""
    
    def test_run_marking_success(self, capsys):
        """Test successful marking execution."""
        from src.marking.assignment_marker import MarkingResult, TaskResult
        
        mock_result = MarkingResult(
            student_id="test_student",
            total_score=15,
            max_points=20,
            task_results={
                2: TaskResult(task_number=2, code="print(1)", total_score=8, max_points=10),
                3: TaskResult(task_number=3, code="x = 5", total_score=7, max_points=10)
            },
            status="Completed",
            issues=["Task 2 Criterion 1: Minor issue"],
            processing_time=2.5
        )
        
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.mark_assignment.return_value = mock_result
        mock_marker.get_statistics.return_value = {
            'assignments_processed': 1,
            'total_api_calls': 5,
            'total_errors': 1,
            'total_processing_time': 2.5,
            'error_rate': 0.2
        }
        
        _run_marking(mock_marker, "test_student", "/path/to/notebook.ipynb", "/path/to/rubric.csv", 1000.0)
        
        captured = capsys.readouterr()
        assert "Processing student: test_student" in captured.out
        assert "MARKING RESULTS - test_student" in captured.out
        assert "15/20" in captured.out
        assert "75.0%" in captured.out
        assert "Task 2: 8/10" in captured.out
        assert "Task 3: 7/10" in captured.out
        assert "Issues Found:" in captured.out
        assert "test_student_marks.xlsx" in captured.out
    
    def test_run_marking_failure(self, capsys):
        """Test marking execution with failure."""
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.mark_assignment.side_effect = Exception("Marking failed")
        
        with pytest.raises(Exception, match="Marking failed"):
            _run_marking(mock_marker, "test_student", "/path/to/notebook.ipynb", "/path/to/rubric.csv", 1000.0)
        
        captured = capsys.readouterr()
        assert "Marking failed: Marking failed" in captured.err


class TestCLIIntegration:
    """Integration tests for the complete CLI workflow."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('src.cli.main.AssignmentMarker')
    def test_full_workflow_success(self, mock_marker_class, tmp_path):
        """Test the complete CLI workflow from start to finish."""
        # Create realistic test files
        notebook = tmp_path / "student_001.ipynb"
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["#### Your Solution"]
                },
                {
                    "cell_type": "code",
                    "source": ["def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"]
                }
            ]
        }
        notebook.write_text(str(notebook_content).replace("'", '"'))
        
        rubric = tmp_path / "rubric.csv"
        rubric.write_text("Task,Criterion,Score,Max Points\nTask 2,Correctness,0,5\nTask 2,Efficiency,0,3")
        
        output_dir = tmp_path / "output"
        
        # Mock complete marking result
        from src.marking.assignment_marker import MarkingResult, TaskResult
        mock_result = MarkingResult(
            student_id="student_001",
            total_score=7,
            max_points=8,
            task_results={
                2: TaskResult(
                    task_number=2, 
                    code="def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                    total_score=7,
                    max_points=8,
                    criteria_results=[
                        {"criterion": "Correctness", "score": 5, "max_points": 5},
                        {"criterion": "Efficiency", "score": 2, "max_points": 3}
                    ]
                )
            },
            status="Completed",
            processing_time=3.2
        )
        
        mock_marker = Mock(spec=AssignmentMarker)
        mock_marker.mark_assignment.return_value = mock_result
        mock_marker.get_statistics.return_value = {
            'assignments_processed': 1,
            'total_api_calls': 2,
            'total_errors': 0,
            'total_processing_time': 3.2,
            'error_rate': 0.0
        }
        mock_marker_class.return_value = mock_marker
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--notebook', str(notebook),
            '--rubric', str(rubric),
            '--output-dir', str(output_dir),
            '--model', 'gpt-4o-mini',
            '--verbose'
        ])
        
        # Verify successful execution
        assert result.exit_code == 0
        assert "student_001" in result.output
        assert "7/8" in result.output
        assert "87.5%" in result.output
        assert "Completed" in result.output
        
        # Verify marker was called correctly
        mock_marker_class.assert_called_once()
        mock_marker.mark_assignment.assert_called_once_with(
            "student_001", str(notebook), str(rubric)
        )
    
    def test_student_id_inference(self, tmp_path):
        """Test that student ID is correctly inferred from notebook filename."""
        notebook = tmp_path / "assignment_042.ipynb"
        notebook.write_text('{"cells": []}')
        
        rubric = tmp_path / "rubric.csv"
        rubric.write_text("Task,Criterion")
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.cli.main.AssignmentMarker') as mock_marker_class:
                mock_marker = Mock(spec=AssignmentMarker)
                mock_marker.validate_setup.return_value = []
                mock_marker._load_notebook.return_value = ({}, [])
                mock_marker._load_rubric.return_value = ({}, [])
                mock_marker_class.return_value = mock_marker
                
                runner = CliRunner()
                result = runner.invoke(cli, [
                    '--notebook', str(notebook),
                    '--rubric', str(rubric),
                    '--dry-run'
                ])
                
                assert result.exit_code == 0
                assert "assignment_042" in result.output
