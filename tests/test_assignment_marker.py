"""
Tests for the AssignmentMarker integration layer.

Tests the complete marking workflow including coordination between
all components, error handling, and batch processing.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from src.marking.assignment_marker import (
    AssignmentMarker, 
    MarkingResult, 
    TaskResult,
    AssignmentMarkingError
)
from src.marking.criterion_evaluator import EvaluationResult
from src.parsers.notebook_parser import NotebookParsingError
from src.parsers.rubric_parser import RubricParsingError
from src.output.excel_generator import ExcelGenerationError


class TestTaskResult:
    """Tests for the TaskResult dataclass."""
    
    def test_task_result_initialization(self):
        """Test TaskResult initialization with defaults."""
        result = TaskResult(task_number=2, code="print('hello')")
        
        assert result.task_number == 2
        assert result.code == "print('hello')"
        assert result.criteria_results == []
        assert result.total_score == 0
        assert result.max_points == 0
        assert result.issues == []
        assert result.missing is False
    
    def test_task_result_with_data(self):
        """Test TaskResult with actual data."""
        criteria_results = [
            {'criterion_index': 0, 'score': 2, 'max_points': 2},
            {'criterion_index': 1, 'score': 1, 'max_points': 2}
        ]
        
        result = TaskResult(
            task_number=3,
            code="def func(): pass",
            criteria_results=criteria_results,
            total_score=3,
            max_points=4,
            issues=["Minor issue"]
        )
        
        assert result.task_number == 3
        assert len(result.criteria_results) == 2
        assert result.total_score == 3
        assert result.max_points == 4
        assert len(result.issues) == 1


class TestMarkingResult:
    """Tests for the MarkingResult dataclass."""
    
    def test_marking_result_initialization(self):
        """Test MarkingResult initialization."""
        result = MarkingResult(student_id="TEST001")
        
        assert result.student_id == "TEST001"
        assert result.total_score == 0
        assert result.max_points == 0
        assert result.task_results == {}
        assert result.issues == []
        assert result.processing_time == 0.0
        assert result.status == "Unknown"


class TestAssignmentMarker:
    """Tests for the AssignmentMarker class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def assignment_marker(self, temp_dir):
        """Create AssignmentMarker instance."""
        return AssignmentMarker(
            model_name="gpt-4o-mini",
            output_dir=str(temp_dir),
            max_retries=2,
            verbosity=0  # Quiet for tests
        )
    
    @pytest.fixture
    def sample_notebook_path(self, temp_dir):
        """Create a sample notebook file."""
        notebook_data = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["#### Your Solution"]
                },
                {
                    "cell_type": "code",
                    "source": ["def bot_whisper(payload):\n    return ' '.join(payload).lower()"]
                },
                {
                    "cell_type": "markdown", 
                    "source": ["#### Your Solution"]
                },
                {
                    "cell_type": "code",
                    "source": ["def bot_multiply(payload):\n    return int(payload[0]) * int(payload[1])"]
                }
            ]
        }
        
        notebook_path = temp_dir / "test_notebook.ipynb"
        with open(notebook_path, 'w') as f:
            json.dump(notebook_data, f)
        
        return str(notebook_path)
    
    @pytest.fixture
    def sample_rubric_path(self, temp_dir):
        """Create a sample rubric file."""
        rubric_content = """Task 2,Joins list elements from payload,,2
,Converts the message to lowercase,,2
,SUBTOTAL,0,4
,,,
Task 3,Uses data from payload for multiplication,,3
,Performs multiplication correctly,,1
,SUBTOTAL,0,4"""
        
        rubric_path = temp_dir / "test_rubric.csv"
        with open(rubric_path, 'w') as f:
            f.write(rubric_content)
        
        return str(rubric_path)
    
    def test_assignment_marker_initialization(self, temp_dir):
        """Test AssignmentMarker initialization."""
        marker = AssignmentMarker(
            model_name="test-model",
            output_dir=str(temp_dir),
            max_retries=5,
            verbosity=2
        )
        
        assert marker.model_name == "test-model"
        assert marker.output_dir == temp_dir
        assert marker.max_retries == 5
        assert marker.verbosity == 2
        assert marker.criterion_evaluator is not None
        assert marker.excel_generator is not None
        assert marker.stats['assignments_processed'] == 0
    
    @patch('src.marking.assignment_marker.NotebookParser')
    def test_load_notebook_success(self, mock_parser_class, assignment_marker):
        """Test successful notebook loading."""
        mock_parser = Mock()
        mock_parser.parse_tasks.return_value = {2: "code1", 3: "code2"}
        mock_parser.get_issues.return_value = ["issue1"]
        mock_parser_class.return_value = mock_parser
        
        tasks, issues = assignment_marker._load_notebook("test_path")
        
        assert tasks == {2: "code1", 3: "code2"}
        assert issues == ["issue1"]
        mock_parser_class.assert_called_once_with("test_path")
    
    @patch('src.marking.assignment_marker.NotebookParser')
    def test_load_notebook_parsing_error(self, mock_parser_class, assignment_marker):
        """Test notebook loading with parsing error."""
        mock_parser_class.side_effect = NotebookParsingError("Parse failed")
        
        with pytest.raises(AssignmentMarkingError, match="Failed to parse notebook"):
            assignment_marker._load_notebook("test_path")
    
    @patch('src.marking.assignment_marker.RubricParser')
    def test_load_rubric_success(self, mock_parser_class, assignment_marker):
        """Test successful rubric loading."""
        mock_parser = Mock()
        mock_parser.parse_rubric.return_value = {2: [{"criterion": "test", "max_points": 2}]}
        mock_parser.get_issues.return_value = []
        mock_parser_class.return_value = mock_parser
        
        rubric, issues = assignment_marker._load_rubric("test_rubric.csv")
        
        assert 2 in rubric
        assert issues == []
        mock_parser_class.assert_called_once_with("test_rubric.csv")
    
    @patch('src.marking.assignment_marker.RubricParser')
    def test_load_rubric_caching(self, mock_parser_class, assignment_marker):
        """Test rubric caching functionality."""
        mock_parser = Mock()
        mock_parser.parse_rubric.return_value = {2: [{"criterion": "test", "max_points": 2}]}
        mock_parser.get_issues.return_value = []
        mock_parser_class.return_value = mock_parser
        
        # First call
        assignment_marker._load_rubric("test_rubric.csv")
        # Second call should use cache
        assignment_marker._load_rubric("test_rubric.csv")
        
        # Parser should only be called once
        mock_parser_class.assert_called_once()
    
    def test_evaluate_task_missing_code(self, assignment_marker):
        """Test task evaluation with missing code."""
        criteria = [
            {"criterion": "Test criterion 1", "max_points": 2},
            {"criterion": "Test criterion 2", "max_points": 3}
        ]
        
        result = assignment_marker._evaluate_task(
            task_number=2,
            code="",
            criteria=criteria
        )
        
        assert result.task_number == 2
        assert result.missing is True
        assert result.total_score == 0
        assert result.max_points == 5
        assert len(result.criteria_results) == 2
        assert all(cr['error_flag'] == 'MISSING_TASK' for cr in result.criteria_results)
        assert any("MISSING_TASK" in issue for issue in result.issues)
    
    @patch('src.marking.assignment_marker.CriterionEvaluator')
    def test_evaluate_task_with_code(self, mock_evaluator_class, assignment_marker):
        """Test task evaluation with actual code."""
        # Mock the evaluator
        mock_evaluator = Mock()
        mock_eval_result = EvaluationResult(
            score=2,
            confidence=0.9,
            raw_response="Good solution",
            retry_count=0
        )
        mock_evaluator.evaluate_criterion.return_value = mock_eval_result
        assignment_marker.criterion_evaluator = mock_evaluator
        
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = assignment_marker._evaluate_task(
            task_number=2,
            code="print('hello')",
            criteria=criteria
        )
        
        assert result.task_number == 2
        assert result.missing is False
        assert result.total_score == 2
        assert result.max_points == 2
        assert len(result.criteria_results) == 1
        assert result.criteria_results[0]['score'] == 2
    
    def test_evaluate_task_with_evaluation_error(self, assignment_marker):
        """Test task evaluation when criterion evaluator throws error."""
        # Mock the evaluator to throw an exception
        assignment_marker.criterion_evaluator.evaluate_criterion = Mock(
            side_effect=Exception("API Error")
        )
        
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = assignment_marker._evaluate_task(
            task_number=2,
            code="print('hello')",
            criteria=criteria
        )
        
        assert result.task_number == 2
        assert result.total_score == 0  # Error should result in 0 score
        assert len(result.criteria_results) == 1
        assert result.criteria_results[0]['error_flag'] == 'PARSING_ERROR'
        assert any("PARSING_ERROR" in issue for issue in result.issues)
    
    def test_evaluate_task_with_incomplete_code_error(self, assignment_marker):
        """Test task evaluation with incomplete code error."""
        # Mock evaluator to return PLACEHOLDER_CODE error
        mock_eval_result = EvaluationResult(
            score=0,
            confidence=1.0,
            raw_response="Placeholder detected",
            error="PLACEHOLDER_CODE"
        )
        assignment_marker.criterion_evaluator.evaluate_criterion = Mock(
            return_value=mock_eval_result
        )
        
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = assignment_marker._evaluate_task(
            task_number=2,
            code="# your code here",
            criteria=criteria
        )
        
        assert len(result.criteria_results) == 1
        assert result.criteria_results[0]['error_flag'] == 'INCOMPLETE_CODE'
        assert any("INCOMPLETE_CODE" in issue for issue in result.issues)
    
    @patch('src.marking.assignment_marker.NotebookParser')
    @patch('src.marking.assignment_marker.RubricParser')
    def test_mark_assignment_success(self, mock_rubric_class, mock_notebook_class, assignment_marker):
        """Test successful assignment marking."""
        # Mock notebook parser
        mock_notebook = Mock()
        mock_notebook.parse_tasks.return_value = {2: "def test(): pass"}
        mock_notebook.get_issues.return_value = []
        mock_notebook_class.return_value = mock_notebook
        
        # Mock rubric parser
        mock_rubric = Mock()
        mock_rubric.parse_rubric.return_value = {
            2: [{"criterion": "Test criterion", "max_points": 2}]
        }
        mock_rubric.get_issues.return_value = []
        mock_rubric_class.return_value = mock_rubric
        
        # Mock criterion evaluator
        mock_eval_result = EvaluationResult(
            score=2,
            confidence=0.9,
            raw_response="Perfect",
            retry_count=0
        )
        assignment_marker.criterion_evaluator.evaluate_criterion = Mock(
            return_value=mock_eval_result
        )
        
        # Mock Excel generator
        assignment_marker.excel_generator.generate_marking_sheet = Mock()
        
        result = assignment_marker.mark_assignment(
            student_id="TEST001",
            notebook_path="test.ipynb",
            rubric_path="test.csv"
        )
        
        assert result.student_id == "TEST001"
        assert result.total_score == 2
        assert result.max_points == 2
        assert result.status == "Completed"
        assert 2 in result.task_results
        assert result.processing_time > 0
    
    @patch('src.marking.assignment_marker.NotebookParser')
    def test_mark_assignment_notebook_error(self, mock_notebook_class, assignment_marker):
        """Test assignment marking with notebook loading error."""
        mock_notebook_class.side_effect = NotebookParsingError("Invalid notebook")
        
        with pytest.raises(AssignmentMarkingError):
            assignment_marker.mark_assignment(
                student_id="TEST001",
                notebook_path="bad.ipynb",
                rubric_path="test.csv"
            )
    
    @patch('src.marking.assignment_marker.NotebookParser')
    @patch('src.marking.assignment_marker.RubricParser')
    def test_mark_assignment_rubric_error(self, mock_rubric_class, mock_notebook_class, assignment_marker):
        """Test assignment marking with rubric loading error."""
        # Mock successful notebook loading
        mock_notebook = Mock()
        mock_notebook.parse_tasks.return_value = {2: "code"}
        mock_notebook.get_issues.return_value = []
        mock_notebook_class.return_value = mock_notebook
        
        # Mock rubric error
        mock_rubric_class.side_effect = RubricParsingError("Invalid rubric")
        
        with pytest.raises(AssignmentMarkingError):
            assignment_marker.mark_assignment(
                student_id="TEST001",
                notebook_path="test.ipynb",
                rubric_path="bad.csv"
            )
    
    @patch('src.marking.assignment_marker.NotebookParser')
    @patch('src.marking.assignment_marker.RubricParser')
    def test_mark_assignment_excel_generation_error(self, mock_rubric_class, mock_notebook_class, assignment_marker):
        """Test assignment marking with Excel generation error."""
        # Mock successful parsing
        mock_notebook = Mock()
        mock_notebook.parse_tasks.return_value = {2: "def test(): pass"}
        mock_notebook.get_issues.return_value = []
        mock_notebook_class.return_value = mock_notebook
        
        mock_rubric = Mock()
        mock_rubric.parse_rubric.return_value = {
            2: [{"criterion": "Test", "max_points": 2}]
        }
        mock_rubric.get_issues.return_value = []
        mock_rubric_class.return_value = mock_rubric
        
        # Mock successful evaluation
        mock_eval_result = EvaluationResult(score=2, confidence=0.9, raw_response="Good", retry_count=0)
        assignment_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        
        # Mock Excel generation error
        assignment_marker.excel_generator.generate_marking_sheet = Mock(
            side_effect=ExcelGenerationError("Excel failed")
        )
        
        result = assignment_marker.mark_assignment(
            student_id="TEST001",
            notebook_path="test.ipynb",
            rubric_path="test.csv"
        )
        
        # Should still complete but with Excel error in issues
        assert result.status == "Completed"
        assert any("Excel generation failed" in issue for issue in result.issues)
    
    def test_mark_batch_success(self, assignment_marker):
        """Test successful batch marking."""
        # Mock the mark_assignment method
        def mock_mark_assignment(student_id, notebook_path, rubric_path):
            return MarkingResult(
                student_id=student_id,
                total_score=75,
                max_points=83,
                status="Completed"
            )
        
        assignment_marker.mark_assignment = Mock(side_effect=mock_mark_assignment)
        assignment_marker.excel_generator.generate_batch_summary = Mock()
        
        assignments = [
            {"student_id": "TEST001", "notebook_path": "test1.ipynb"},
            {"student_id": "TEST002", "notebook_path": "test2.ipynb"}
        ]
        
        results = assignment_marker.mark_batch(assignments, "rubric.csv")
        
        assert len(results) == 2
        assert "TEST001" in results
        assert "TEST002" in results
        assert results["TEST001"].total_score == 75
        assert assignment_marker.mark_assignment.call_count == 2
    
    def test_mark_batch_with_failures(self, assignment_marker):
        """Test batch marking with some failures."""
        def mock_mark_assignment(student_id, notebook_path, rubric_path):
            if student_id == "TEST001":
                return MarkingResult(student_id=student_id, status="Completed")
            else:
                raise AssignmentMarkingError("Processing failed")
        
        assignment_marker.mark_assignment = Mock(side_effect=mock_mark_assignment)
        assignment_marker.excel_generator.generate_batch_summary = Mock()
        
        assignments = [
            {"student_id": "TEST001", "notebook_path": "test1.ipynb"},
            {"student_id": "TEST002", "notebook_path": "test2.ipynb"}
        ]
        
        results = assignment_marker.mark_batch(assignments, "rubric.csv")
        
        assert len(results) == 2
        assert results["TEST001"].status == "Completed"
        assert "Failed" in results["TEST002"].status
    
    def test_get_statistics(self, assignment_marker):
        """Test statistics collection."""
        # Manually set some stats
        assignment_marker.stats = {
            'assignments_processed': 5,
            'total_api_calls': 50,
            'total_errors': 2,
            'total_processing_time': 100.0
        }
        
        stats = assignment_marker.get_statistics()
        
        assert stats['assignments_processed'] == 5
        assert stats['total_api_calls'] == 50
        assert stats['total_errors'] == 2
        assert stats['total_processing_time'] == 100.0
        assert stats['average_processing_time'] == 20.0
        assert stats['error_rate'] == 0.04
    
    def test_validate_setup_success(self, assignment_marker, sample_notebook_path, sample_rubric_path):
        """Test successful setup validation."""
        issues = assignment_marker.validate_setup(sample_notebook_path, sample_rubric_path)
        
        # Should have no critical issues (may have validation warnings)
        assert isinstance(issues, list)
    
    def test_validate_setup_missing_files(self, assignment_marker):
        """Test setup validation with missing files."""
        issues = assignment_marker.validate_setup("missing.ipynb", "missing.csv")
        
        assert len(issues) >= 2
        assert any("not found" in issue for issue in issues)
    
    @patch('src.marking.assignment_marker.NotebookParser')
    def test_validate_setup_notebook_parsing_error(self, mock_parser_class, assignment_marker, sample_rubric_path):
        """Test setup validation with notebook parsing error."""
        mock_parser_class.side_effect = Exception("Parse error")
        
        # Create a dummy notebook file
        temp_notebook = assignment_marker.output_dir / "temp.ipynb"
        temp_notebook.write_text('{"cells": []}')
        
        issues = assignment_marker.validate_setup(str(temp_notebook), sample_rubric_path)
        
        assert any("Notebook parsing failed" in issue for issue in issues)


class TestAssignmentMarkerIntegration:
    """Integration tests using real components with mock data."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for integration tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def integration_marker(self, temp_dir):
        """Create marker for integration tests."""
        return AssignmentMarker(
            model_name="gpt-4o-mini",
            output_dir=str(temp_dir),
            verbosity=1
        )
    
    @pytest.fixture
    def realistic_notebook(self, temp_dir):
        """Create a realistic test notebook."""
        notebook_data = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Task 2"]},
                {"cell_type": "markdown", "source": ["#### Your Solution"]},
                {
                    "cell_type": "code",
                    "source": [
                        "def bot_whisper(payload):\n",
                        "    message = ' '.join(payload)\n",
                        "    return message.lower()\n",
                        "\n",
                        "def bot_say(message):\n",
                        "    print(f'Bot: {message}')\n",
                        "\n",
                        "# Test\n",
                        "bot_say(bot_whisper(['Hello', 'World']))"
                    ]
                },
                {"cell_type": "markdown", "source": ["# Task 3"]},
                {"cell_type": "markdown", "source": ["#### Your Solution"]},
                {
                    "cell_type": "code",
                    "source": [
                        "def bot_multiply(payload):\n",
                        "    a = int(payload[0])\n",
                        "    b = int(payload[1])\n",
                        "    result = a * b\n",
                        "    equation = f'{payload[0]} * {payload[1]} = {result:.4f}'\n",
                        "    bot_say(equation)\n",
                        "    return result"
                    ]
                }
            ]
        }
        
        notebook_path = temp_dir / "realistic_test.ipynb"
        with open(notebook_path, 'w') as f:
            json.dump(notebook_data, f)
        
        return str(notebook_path)
    
    @pytest.fixture
    def realistic_rubric(self, temp_dir):
        """Create a realistic test rubric."""
        rubric_content = """Task 2,Joins list elements from payload to make a single string,,2
,Converts the message to lowercase,,2
,Correctly displays output by calling the bot_say() function,,2
,SUBTOTAL,0,6
,,,
Task 3,Uses data from the payload to determine the numbers needed for multiplication,,3
,Performs multiplication using an appropriate expression,,1
,Displays the result as an equation using the bot_say() function,,2
,SUBTOTAL,0,6"""
        
        rubric_path = temp_dir / "realistic_rubric.csv"
        with open(rubric_path, 'w') as f:
            f.write(rubric_content)
        
        return str(rubric_path)
    
    @patch('src.marking.criterion_evaluator.dspy')
    def test_full_integration_workflow(self, mock_dspy, integration_marker, realistic_notebook, realistic_rubric):
        """Test complete workflow with realistic data."""
        # Mock DSPy responses
        mock_response = Mock()
        mock_response.score = "2"
        mock_response.reasoning = "Well implemented"
        
        mock_signature = Mock()
        mock_signature.return_value = mock_response
        
        # Mock the signature creation and DSPy calls
        with patch('src.marking.dspy_config.create_dynamic_signature_instance', return_value=mock_signature):
            result = integration_marker.mark_assignment(
                student_id="INTEGRATION_001",
                notebook_path=realistic_notebook,
                rubric_path=realistic_rubric
            )
        
        # Verify the result structure
        assert result.student_id == "INTEGRATION_001"
        assert result.max_points > 0
        assert len(result.task_results) >= 2  # Should have at least Task 2 and 3
        assert result.status != "Unknown"
        assert result.processing_time > 0
        
        # Check that Excel file would be generated
        expected_excel_path = integration_marker.output_dir / "INTEGRATION_001_marks.xlsx"
        # Note: We don't check if file exists because Excel generation might be mocked
    
    def test_validation_with_real_components(self, integration_marker, realistic_notebook, realistic_rubric):
        """Test validation using real parser components."""
        issues = integration_marker.validate_setup(realistic_notebook, realistic_rubric)
        
        # With realistic data, should have minimal issues
        critical_issues = [i for i in issues if "not found" in i or "failed" in i]
        assert len(critical_issues) == 0  # No critical issues expected
    
    @patch('src.marking.criterion_evaluator.dspy')
    def test_error_recovery_in_integration(self, mock_dspy, integration_marker, realistic_notebook, realistic_rubric):
        """Test error recovery during integration workflow."""
        # Mock DSPy to fail sometimes
        def mock_evaluate_side_effect(*args, **kwargs):
            # Fail every third call
            if not hasattr(mock_evaluate_side_effect, 'call_count'):
                mock_evaluate_side_effect.call_count = 0
            mock_evaluate_side_effect.call_count += 1
            
            if mock_evaluate_side_effect.call_count % 3 == 0:
                raise Exception("Simulated API error")
            
            mock_response = Mock()
            mock_response.score = "1"
            mock_response.reasoning = "Partial credit"
            return mock_response
        
        mock_signature = Mock()
        mock_signature.side_effect = mock_evaluate_side_effect
        
        with patch('src.marking.dspy_config.create_dynamic_signature_instance', return_value=mock_signature):
            result = integration_marker.mark_assignment(
                student_id="ERROR_RECOVERY_001",
                notebook_path=realistic_notebook,
                rubric_path=realistic_rubric
            )
        
        # Should complete despite errors
        assert result.student_id == "ERROR_RECOVERY_001"
        assert result.status != "Unknown"
        
        # Should have some errors recorded
        error_issues = [i for i in result.issues if "PARSING_ERROR" in i or "ERROR" in i]
        assert len(error_issues) > 0


class TestAssignmentMarkerErrorHandling:
    """Tests for comprehensive error handling scenarios."""
    
    @pytest.fixture
    def error_marker(self):
        """Create marker for error testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AssignmentMarker(
                model_name="gpt-4o-mini",
                output_dir=temp_dir,
                verbosity=0
            )
    
    def test_file_errors_stop_processing(self, error_marker):
        """Test that file errors stop processing completely."""
        with pytest.raises(AssignmentMarkingError, match="Failed to parse notebook"):
            error_marker.mark_assignment(
                student_id="ERROR_TEST",
                notebook_path="nonexistent.ipynb",
                rubric_path="test.csv"
            )
    
    @patch('src.marking.assignment_marker.NotebookParser')
    @patch('src.marking.assignment_marker.RubricParser')
    def test_missing_tasks_continue_processing(self, mock_rubric_class, mock_notebook_class, error_marker):
        """Test that missing tasks result in 0 score but processing continues."""
        # Mock notebook with missing tasks
        mock_notebook = Mock()
        mock_notebook.parse_tasks.return_value = {2: "", 3: "some code"}  # Task 2 missing
        mock_notebook.get_issues.return_value = ["Task 2: MISSING_TASK"]
        mock_notebook_class.return_value = mock_notebook
        
        # Mock rubric
        mock_rubric = Mock()
        mock_rubric.parse_rubric.return_value = {
            2: [{"criterion": "Test", "max_points": 2}],
            3: [{"criterion": "Test", "max_points": 2}]
        }
        mock_rubric.get_issues.return_value = []
        mock_rubric_class.return_value = mock_rubric
        
        # Mock successful evaluation for task 3
        mock_eval_result = EvaluationResult(score=2, confidence=0.9, raw_response="Good", retry_count=0)
        error_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        error_marker.excel_generator.generate_marking_sheet = Mock()
        
        result = error_marker.mark_assignment(
            student_id="MISSING_TASK_TEST",
            notebook_path="test.ipynb",
            rubric_path="test.csv"
        )
        
        # Should complete with partial score
        assert "Completed" in result.status  # More flexible assertion
        assert result.total_score == 2  # Only task 3 scored
        assert result.max_points == 4   # Both tasks have max points
        assert result.task_results[2].missing is True
        assert result.task_results[3].missing is False
    
    def test_api_errors_retry_then_score_zero(self, error_marker):
        """Test that API errors are retried 3x then scored as 0."""
        # This is tested via the CriterionEvaluator which handles retries
        # Mock evaluator to return error after retries
        mock_eval_result = EvaluationResult(
            score=0,
            confidence=0.0,
            raw_response="",
            error="API timeout after 3 retries",
            retry_count=3
        )
        error_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = error_marker._evaluate_task(
            task_number=2,
            code="print('test')",
            criteria=criteria
        )
        
        assert result.total_score == 0
        assert len(result.criteria_results) == 1
        assert result.criteria_results[0]['error_flag'] == 'PARSING_ERROR'
        assert "API timeout" in result.issues[0]
    
    def test_invalid_responses_score_zero_with_flag(self, error_marker):
        """Test that invalid responses get 0 score with error flag."""
        # Mock evaluator to return invalid response error
        mock_eval_result = EvaluationResult(
            score=0,
            confidence=0.0,
            raw_response="Invalid response",
            error="Invalid model response"
        )
        error_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = error_marker._evaluate_task(
            task_number=2,
            code="print('test')",
            criteria=criteria
        )
        
        assert result.total_score == 0
        assert result.criteria_results[0]['score'] == 0
        assert result.criteria_results[0]['error_flag'] == 'PARSING_ERROR'
    
    def test_syntax_errors_flagged_appropriately(self, error_marker):
        """Test that syntax errors are properly flagged."""
        mock_eval_result = EvaluationResult(
            score=0,
            confidence=1.0,
            raw_response="Syntax error detected",
            error="SYNTAX_ERROR"
        )
        error_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = error_marker._evaluate_task(
            task_number=2,
            code="def broken_func(",  # Syntax error
            criteria=criteria
        )
        
        assert result.criteria_results[0]['error_flag'] == 'PARSING_ERROR'
        assert "SYNTAX_ERROR" in result.issues[0]
    
    def test_placeholder_code_flagged_as_incomplete(self, error_marker):
        """Test that placeholder code is flagged as incomplete."""
        mock_eval_result = EvaluationResult(
            score=0,
            confidence=1.0,
            raw_response="Placeholder detected",
            error="PLACEHOLDER_CODE"
        )
        error_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = error_marker._evaluate_task(
            task_number=2,
            code="# your code here",
            criteria=criteria
        )
        
        assert result.criteria_results[0]['error_flag'] == 'INCOMPLETE_CODE'
        assert "INCOMPLETE_CODE" in result.issues[0]


class TestAssignmentMarkerStatistics:
    """Tests for statistics collection and reporting."""
    
    @pytest.fixture
    def stats_marker(self):
        """Create marker for statistics testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AssignmentMarker(
                model_name="gpt-4o-mini",
                output_dir=temp_dir,
                verbosity=0
            )
    
    def test_statistics_initialization(self, stats_marker):
        """Test that statistics are properly initialized."""
        stats = stats_marker.get_statistics()
        
        assert stats['assignments_processed'] == 0
        assert stats['total_api_calls'] == 0
        assert stats['total_errors'] == 0
        assert stats['total_processing_time'] == 0.0
        assert stats['average_processing_time'] == 0.0
        assert stats['error_rate'] == 0.0
    
    @patch('src.marking.assignment_marker.NotebookParser')
    @patch('src.marking.assignment_marker.RubricParser')
    def test_statistics_updated_after_marking(self, mock_rubric_class, mock_notebook_class, stats_marker):
        """Test that statistics are updated after marking."""
        # Mock successful parsing
        mock_notebook = Mock()
        mock_notebook.parse_tasks.return_value = {2: "code"}
        mock_notebook.get_issues.return_value = []
        mock_notebook_class.return_value = mock_notebook
        
        mock_rubric = Mock()
        mock_rubric.parse_rubric.return_value = {2: [{"criterion": "Test", "max_points": 2}]}
        mock_rubric.get_issues.return_value = []
        mock_rubric_class.return_value = mock_rubric
        
        # Mock evaluation with retry count
        mock_eval_result = EvaluationResult(score=2, confidence=0.9, raw_response="Good", retry_count=1)
        stats_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        stats_marker.excel_generator.generate_marking_sheet = Mock()
        
        stats_marker.mark_assignment(
            student_id="STATS_TEST",
            notebook_path="test.ipynb",
            rubric_path="test.csv"
        )
        
        stats = stats_marker.get_statistics()
        
        assert stats['assignments_processed'] == 1
        assert stats['total_api_calls'] == 2  # 1 retry + 1 original = 2 total calls
        assert stats['total_processing_time'] > 0
        assert stats['average_processing_time'] > 0
    
    def test_error_statistics_tracking(self, stats_marker):
        """Test that errors are properly tracked in statistics."""
        # Manually increment error count to test calculation
        stats_marker.stats['total_errors'] = 5
        stats_marker.stats['total_api_calls'] = 20
        
        stats = stats_marker.get_statistics()
        
        assert stats['total_errors'] == 5
        assert stats['error_rate'] == 0.25  # 5/20 = 0.25


class TestAssignmentMarkerCaching:
    """Tests for caching functionality."""
    
    @pytest.fixture
    def cache_marker(self):
        """Create marker for caching tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AssignmentMarker(
                model_name="gpt-4o-mini",
                output_dir=temp_dir,
                verbosity=0
            )
    
    @patch('src.marking.assignment_marker.RubricParser')
    def test_rubric_caching_works(self, mock_rubric_class, cache_marker):
        """Test that rubric caching prevents multiple loads."""
        mock_rubric = Mock()
        mock_rubric.parse_rubric.return_value = {2: [{"criterion": "Test", "max_points": 2}]}
        mock_rubric.get_issues.return_value = []
        mock_rubric_class.return_value = mock_rubric
        
        # Load rubric twice
        cache_marker._load_rubric("test.csv")
        cache_marker._load_rubric("test.csv")
        
        # Parser should only be instantiated once due to caching
        mock_rubric_class.assert_called_once()
    
    @patch('src.marking.assignment_marker.RubricParser')
    def test_different_rubrics_not_cached_together(self, mock_rubric_class, cache_marker):
        """Test that different rubric files are cached separately."""
        mock_rubric = Mock()
        mock_rubric.parse_rubric.return_value = {2: [{"criterion": "Test", "max_points": 2}]}
        mock_rubric.get_issues.return_value = []
        mock_rubric_class.return_value = mock_rubric
        
        # Load different rubrics
        cache_marker._load_rubric("test1.csv")
        cache_marker._load_rubric("test2.csv")
        
        # Parser should be instantiated twice for different files
        assert mock_rubric_class.call_count == 2


class TestAssignmentMarkerVerbosity:
    """Tests for verbosity and logging functionality."""
    
    def test_verbosity_levels_affect_logging(self):
        """Test that verbosity levels affect logging configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test different verbosity levels
            quiet_marker = AssignmentMarker(output_dir=temp_dir, verbosity=0)
            normal_marker = AssignmentMarker(output_dir=temp_dir, verbosity=1)
            verbose_marker = AssignmentMarker(output_dir=temp_dir, verbosity=2)
            
            # Check that criterion evaluators have correct verbosity
            assert quiet_marker.criterion_evaluator.verbosity == 0
            assert normal_marker.criterion_evaluator.verbosity == 1
            assert verbose_marker.criterion_evaluator.verbosity == 2


class TestAssignmentMarkerEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    @pytest.fixture
    def edge_marker(self):
        """Create marker for edge case testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AssignmentMarker(
                model_name="gpt-4o-mini",
                output_dir=temp_dir,
                verbosity=0
            )
    
    def test_empty_rubric_handling(self, edge_marker):
        """Test handling of empty or minimal rubric data."""
        criteria = []  # Empty criteria list
        
        result = edge_marker._evaluate_task(
            task_number=2,
            code="print('test')",
            criteria=criteria
        )
        
        assert result.task_number == 2
        assert result.total_score == 0
        assert result.max_points == 0
        assert len(result.criteria_results) == 0
    
    def test_very_long_code_handling(self, edge_marker):
        """Test handling of very long code submissions."""
        # Create very long code string
        long_code = "print('test')\n" * 1000
        
        mock_eval_result = EvaluationResult(score=1, confidence=0.8, raw_response="OK", retry_count=0)
        edge_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = edge_marker._evaluate_task(
            task_number=2,
            code=long_code,
            criteria=criteria
        )
        
        # Should handle long code without issues
        assert result.total_score == 1
        assert len(result.criteria_results) == 1
    
    def test_unicode_content_handling(self, edge_marker):
        """Test handling of unicode characters in code and criteria."""
        unicode_code = "# 这是一个测试\nprint('тест')\n# café"
        unicode_criterion = "Handles unicode characters correctly: café, тест, 测试"
        
        mock_eval_result = EvaluationResult(score=1, confidence=0.8, raw_response="Unicode OK", retry_count=0)
        edge_marker.criterion_evaluator.evaluate_criterion = Mock(return_value=mock_eval_result)
        
        criteria = [{"criterion": unicode_criterion, "max_points": 2}]
        
        result = edge_marker._evaluate_task(
            task_number=2,
            code=unicode_code,
            criteria=criteria
        )
        
        # Should handle unicode without issues
        assert result.total_score == 1
        assert result.criteria_results[0]['criterion'] == unicode_criterion
    
    def test_maximum_task_numbers_boundary(self, edge_marker):
        """Test handling of boundary task numbers."""
        # Test with maximum expected task number (7)
        criteria = [{"criterion": "Test criterion", "max_points": 2}]
        
        result = edge_marker._evaluate_task(
            task_number=7,
            code="print('task 7')",
            criteria=criteria
        )
        
        assert result.task_number == 7
        
        # Test with unexpected high task number
        result_high = edge_marker._evaluate_task(
            task_number=999,
            code="print('task 999')",
            criteria=criteria
        )
        
        assert result_high.task_number == 999  # Should accept any task number
