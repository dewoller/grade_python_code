"""
Tests for the main entry point script.

These tests ensure the mark_student.py script correctly handles
execution and error conditions.
"""

import sys
from unittest.mock import patch, Mock
import pytest

import mark_student


class TestMainEntryPoint:
    """Test the main entry point functionality."""
    
    @patch('mark_student.cli')
    def test_main_success(self, mock_cli):
        """Test successful execution of main function."""
        mock_cli.return_value = None
        
        # Should not raise any exception
        mark_student.main()
        
        # CLI should be called once
        mock_cli.assert_called_once()
    
    @patch('mark_student.cli')
    def test_main_keyboard_interrupt(self, mock_cli, capsys):
        """Test main function handling keyboard interrupt."""
        mock_cli.side_effect = KeyboardInterrupt()
        
        with pytest.raises(SystemExit) as exc_info:
            mark_student.main()
        
        assert exc_info.value.code == 130
        
        captured = capsys.readouterr()
        assert "Process interrupted by user" in captured.out
    
    @patch('mark_student.cli')
    def test_main_general_exception(self, mock_cli, capsys):
        """Test main function handling general exceptions."""
        mock_cli.side_effect = Exception("Test error")
        
        with pytest.raises(SystemExit) as exc_info:
            mark_student.main()
        
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Unexpected error: Test error" in captured.out
    
    def test_main_module_execution(self):
        """Test that the module can be executed directly."""
        # This tests the if __name__ == "__main__" block
        # We can't easily test the actual execution, but we can verify
        # the structure is correct
        assert hasattr(mark_student, 'main')
        assert callable(mark_student.main)
    
    def test_project_root_in_path(self):
        """Test that project root is added to Python path."""
        # The import should work because the path is set up correctly
        import mark_student
        from pathlib import Path
        
        # Verify the project root path manipulation
        project_root = Path(mark_student.__file__).parent
        assert str(project_root) in sys.path


class TestDocstring:
    """Test the module docstring and usage examples."""
    
    def test_module_has_docstring(self):
        """Test that the module has a proper docstring."""
        assert mark_student.__doc__ is not None
        assert "Main entry point" in mark_student.__doc__
        assert "Usage:" in mark_student.__doc__
        assert "Example:" in mark_student.__doc__
    
    def test_docstring_contains_usage_info(self):
        """Test that docstring contains helpful usage information."""
        docstring = mark_student.__doc__
        
        # Should contain command line examples
        assert "python mark_student.py" in docstring
        assert "--notebook" in docstring
        assert "--rubric" in docstring
        
        # Should have clear examples
        assert "Example:" in docstring
        assert ".ipynb" in docstring
        assert ".csv" in docstring


class TestImports:
    """Test that all required imports work correctly."""
    
    def test_required_imports_available(self):
        """Test that all required modules can be imported."""
        # These should not raise ImportError
        import sys
        import os
        from pathlib import Path
        
        # The CLI module should be importable after path setup
        from src.cli.main import cli
        
        assert callable(cli)
    
    def test_path_setup_works(self):
        """Test that the Python path setup allows imports."""
        # After importing mark_student, we should be able to import src modules
        import mark_student  # This sets up the path
        
        try:
            from src.cli.main import cli
            from src.marking.assignment_marker import AssignmentMarker
            import_success = True
        except ImportError:
            import_success = False
        
        assert import_success, "Path setup should allow importing src modules"


class TestExecutionFlow:
    """Test the overall execution flow."""
    
    @patch('mark_student.cli')
    def test_execution_flow(self, mock_cli):
        """Test the complete execution flow."""
        # Mock successful CLI execution
        mock_cli.return_value = None
        
        # Execute main
        mark_student.main()
        
        # Verify CLI was called
        mock_cli.assert_called_once_with()
    
    @patch('mark_student.cli')
    @patch('sys.exit')
    def test_error_handling_flow(self, mock_exit, mock_cli):
        """Test error handling flow."""
        # Mock CLI to raise an exception
        mock_cli.side_effect = RuntimeError("Test error")
        
        # Execute main
        mark_student.main()
        
        # Verify exit was called with error code
        mock_exit.assert_called_once_with(1)
    
    @patch('mark_student.cli')
    @patch('sys.exit')
    def test_keyboard_interrupt_flow(self, mock_exit, mock_cli):
        """Test keyboard interrupt handling flow."""
        # Mock CLI to raise KeyboardInterrupt
        mock_cli.side_effect = KeyboardInterrupt()
        
        # Execute main
        mark_student.main()
        
        # Verify exit was called with interrupt code
        mock_exit.assert_called_once_with(130)
