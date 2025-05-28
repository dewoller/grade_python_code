"""
Pytest configuration and fixtures for the marking system tests.

This module provides common fixtures and configuration for all tests
across the marking system components.
"""

import os
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import pandas as pd


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_openai_api_key():
    """Provide a mock OpenAI API key for testing."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key-12345'}):
        yield 'test-api-key-12345'


@pytest.fixture
def valid_rubric_path(tmp_path):
    """Create a valid rubric CSV file for testing."""
    rubric_data = [
        ["Task", "Criterion", "Score", "Max Points"],
        ["Task 2", "Correctness of recursive implementation", "", "4"],
        ["", "Proper base case handling", "", "2"],
        ["", "Code efficiency", "", "2"],
        ["Task 3", "Correct sorting algorithm implementation", "", "5"],
        ["", "Proper array manipulation", "", "3"],
        ["", "Edge case handling", "", "2"],
        ["Task 4", "Data structure usage", "", "6"],
        ["", "Algorithm efficiency", "", "5"],
        ["", "Code readability", "", "4"],
        ["Task 5", "Problem decomposition", "", "6"],
        ["", "Function design", "", "5"],
        ["", "Error handling", "", "4"],
        ["Task 6", "Object-oriented design", "", "6"],
        ["", "Encapsulation", "", "5"],
        ["", "Code documentation", "", "4"],
        ["Task 7", "Algorithm complexity", "", "8"],
        ["", "Optimization techniques", "", "7"],
        ["", "Performance analysis", "", "5"]
    ]
    
    rubric_file = tmp_path / "valid_rubric.csv"
    with open(rubric_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rubric_data)
    
    return str(rubric_file)


@pytest.fixture
def invalid_rubric_path(tmp_path):
    """Create an invalid rubric CSV file for testing."""
    rubric_data = [
        ["Task", "Criterion", "Score", "Max Points"],
        ["Task 2", "Some criterion", "", "invalid_points"],  # Invalid points
        ["", "Another criterion", "", ""],  # Missing points
        ["Task 9", "Out of range task", "", "5"],  # Invalid task number
        ["", "", "", "3"],  # Missing criterion
    ]
    
    rubric_file = tmp_path / "invalid_rubric.csv"
    with open(rubric_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rubric_data)
    
    return str(rubric_file)


@pytest.fixture
def complete_notebook_path(tmp_path):
    """Create a complete notebook file for testing."""
    notebook_content = {
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4,
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Task 2", "#### Your Solution"]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def fibonacci(n):",
                    "    if n <= 1:",
                    "        return n",
                    "    return fibonacci(n-1) + fibonacci(n-2)"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Task 3", "#### Your Solution"]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def sort_array(arr):",
                    "    return sorted(arr)"
                ]
            }
        ]
    }
    
    notebook_file = tmp_path / "complete_notebook.ipynb"
    notebook_file.write_text(json.dumps(notebook_content, indent=2))
    return str(notebook_file)


@pytest.fixture
def missing_tasks_notebook_path(tmp_path):
    """Create a notebook with missing tasks for testing."""
    notebook_content = {
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4,
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Task 2", "#### Your Solution"]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["print('Hello World')"]
            }
            # Missing other tasks
        ]
    }
    
    notebook_file = tmp_path / "missing_tasks_notebook.ipynb"
    notebook_file.write_text(json.dumps(notebook_content, indent=2))
    return str(notebook_file)


@pytest.fixture
def sample_notebook_content():
    """Provide sample notebook content for testing."""
    return {
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4,
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Task 2", "#### Your Solution"]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def fibonacci(n):",
                    "    if n <= 1:",
                    "        return n",
                    "    return fibonacci(n-1) + fibonacci(n-2)"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Task 3", "#### Your Solution"]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def sort_list(arr):",
                    "    return sorted(arr)"
                ]
            }
        ]
    }


@pytest.fixture
def sample_rubric_data():
    """Provide sample rubric data for testing."""
    return [
        ["Task 2", "Correctness of implementation", "", "5"],
        ["Task 2", "Code efficiency", "", "3"],
        ["Task 3", "Correct sorting algorithm", "", "4"],
        ["Task 3", "Edge case handling", "", "2"],
        ["Task 4", "Data structure usage", "", "6"],
        ["Task 4", "Algorithm complexity", "", "4"]
    ]


@pytest.fixture
def create_test_notebook(tmp_path, sample_notebook_content):
    """Create a test notebook file."""
    def _create_notebook(filename="test_notebook.ipynb", content=None):
        if content is None:
            content = sample_notebook_content
        
        notebook_file = tmp_path / filename
        notebook_file.write_text(json.dumps(content, indent=2))
        return notebook_file
    
    return _create_notebook


@pytest.fixture
def create_test_rubric(tmp_path, sample_rubric_data):
    """Create a test rubric CSV file."""
    def _create_rubric(filename="test_rubric.csv", data=None):
        if data is None:
            data = sample_rubric_data
        
        rubric_file = tmp_path / filename
        df = pd.DataFrame(data, columns=["Task", "Criterion", "Score", "Max Points"])
        df.to_csv(rubric_file, index=False)
        return rubric_file
    
    return _create_rubric


@pytest.fixture
def mock_criterion_evaluator():
    """Provide a mock criterion evaluator for testing."""
    with patch('src.marking.criterion_evaluator.CriterionEvaluator') as mock_class:
        mock_evaluator = Mock()
        mock_class.return_value = mock_evaluator
        
        # Default evaluation result
        from src.marking.criterion_evaluator import EvaluationResult
        default_result = EvaluationResult(
            score=3,
            confidence=0.8,
            raw_response="Good implementation",
            error=None,
            retry_count=0
        )
        mock_evaluator.evaluate_criterion.return_value = default_result
        
        yield mock_evaluator


@pytest.fixture
def mock_excel_generator():
    """Provide a mock Excel generator for testing."""
    with patch('src.output.excel_generator.ExcelGenerator') as mock_class:
        mock_generator = Mock()
        mock_class.return_value = mock_generator
        
        # Mock successful file generation
        mock_generator.generate_marking_sheet.return_value = None
        mock_generator.generate_batch_summary.return_value = None
        
        yield mock_generator


@pytest.fixture
def test_output_dir(tmp_path):
    """Provide a temporary output directory for tests."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def clean_environment():
    """Provide a clean environment for testing."""
    # Store original environment
    original_env = dict(os.environ)
    
    # Clear relevant environment variables
    env_vars_to_clear = ['OPENAI_API_KEY', 'DSPY_CACHE_DIR']
    for var in env_vars_to_clear:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_dspy_models():
    """Mock DSPy model loading for testing."""
    with patch('src.marking.model_loader.load_pretrained_model') as mock_load:
        mock_model = Mock()
        mock_load.return_value = mock_model
        yield mock_model


@pytest.fixture(scope="session")
def test_fixtures_dir(tmp_path_factory):
    """Create a session-scoped fixtures directory."""
    fixtures_dir = tmp_path_factory.mktemp("fixtures")
    
    # Create sample files that can be reused across tests
    sample_notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["#### Your Solution"]
            },
            {
                "cell_type": "code",
                "source": ["print('Hello, World!')"]
            }
        ]
    }
    
    notebook_file = fixtures_dir / "sample.ipynb"
    notebook_file.write_text(json.dumps(sample_notebook))
    
    # Create sample rubric
    sample_rubric_data = [
        ["Task 2", "Test criterion", "", "5"]
    ]
    rubric_file = fixtures_dir / "sample_rubric.csv"
    df = pd.DataFrame(sample_rubric_data, columns=["Task", "Criterion", "Score", "Max Points"])
    df.to_csv(rubric_file, index=False)
    
    return fixtures_dir


@pytest.fixture
def isolated_temp_dir():
    """Provide an isolated temporary directory for each test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_assignment_marker():
    """Provide a mock AssignmentMarker for testing."""
    with patch('src.marking.assignment_marker.AssignmentMarker') as mock_class:
        mock_marker = Mock()
        mock_class.return_value = mock_marker
        
        # Default return values
        from src.marking.assignment_marker import MarkingResult, TaskResult
        default_result = MarkingResult(
            student_id="test_student",
            total_score=10,
            max_points=15,
            task_results={
                2: TaskResult(
                    task_number=2,
                    code="print('test')",
                    total_score=10,
                    max_points=15
                )
            },
            status="Completed",
            processing_time=1.5
        )
        
        mock_marker.mark_assignment.return_value = default_result
        mock_marker.validate_setup.return_value = []
        mock_marker.get_statistics.return_value = {
            'assignments_processed': 1,
            'total_api_calls': 3,
            'total_errors': 0,
            'total_processing_time': 1.5,
            'error_rate': 0.0
        }
        
        yield mock_marker


@pytest.fixture
def capture_logs(caplog):
    """Capture logs with appropriate level for testing."""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing without actual file I/O."""
    mocks = {}
    
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('pathlib.Path.write_text') as mock_write_text, \
         patch('pathlib.Path.read_text') as mock_read_text:
        
        mocks['exists'] = mock_exists
        mocks['mkdir'] = mock_mkdir
        mocks['write_text'] = mock_write_text
        mocks['read_text'] = mock_read_text
        
        # Default behaviors
        mock_exists.return_value = True
        mock_mkdir.return_value = None
        mock_write_text.return_value = None
        mock_read_text.return_value = '{"cells": []}'
        
        yield mocks


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api: mark test as requiring API access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark tests that might be slow
        if any(keyword in item.nodeid for keyword in ["complete", "workflow", "batch"]):
            item.add_marker(pytest.mark.slow)
        
        # Mark tests requiring API
        if any(keyword in item.nodeid for keyword in ["api", "openai", "evaluator"]):
            item.add_marker(pytest.mark.requires_api)
