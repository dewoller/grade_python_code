"""
Tests for DSPy configuration module.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
import dspy

from src.marking.dspy_config import (
    DSPyConfig, 
    initialize_dspy, 
    create_dynamic_signature_class,
    create_dynamic_signature_instance,
    parse_integer_answer
)


class TestDSPyConfig:
    """Test cases for DSPyConfig class."""
    
    def test_init_with_api_key(self):
        """Test DSPyConfig initialization with provided API key."""
        config = DSPyConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 1000
        assert config.temperature == 0.0
    
    def test_init_with_env_var(self):
        """Test DSPyConfig initialization with environment variable."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'}):
            config = DSPyConfig()
            assert config.api_key == "env-key"
    
    def test_init_no_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not provided"):
                DSPyConfig()
    
    def test_init_custom_parameters(self):
        """Test DSPyConfig initialization with custom parameters."""
        config = DSPyConfig(
            model="gpt-4",
            api_key="test-key",
            max_tokens=2000,
            temperature=0.5
        )
        assert config.model == "gpt-4"
        assert config.max_tokens == 2000
        assert config.temperature == 0.5
    
    @patch('dspy.configure')
    @patch('dspy.LM')
    def test_configure_dspy_success(self, mock_lm, mock_configure):
        """Test successful DSPy configuration."""
        mock_lm_instance = MagicMock()
        mock_lm.return_value = mock_lm_instance
        
        config = DSPyConfig(api_key="test-key")
        config.configure_dspy()
        
        mock_lm.assert_called_once_with(
            model="openai/gpt-4o-mini",
            api_key="test-key",
            max_tokens=1000,
            temperature=0.0
        )
        mock_configure.assert_called_once_with(lm=mock_lm_instance)
    
    @patch('dspy.configure')
    @patch('dspy.LM')
    def test_configure_dspy_failure(self, mock_lm, mock_configure):
        """Test DSPy configuration failure handling."""
        mock_lm.side_effect = Exception("Connection failed")
        
        config = DSPyConfig(api_key="test-key")
        
        with pytest.raises(Exception, match="Connection failed"):
            config.configure_dspy()


class TestInitializeDSpy:
    """Test cases for initialize_dspy function."""
    
    @patch('src.marking.dspy_config.DSPyConfig')
    def test_initialize_dspy_with_defaults(self, mock_config_class):
        """Test initialize_dspy with default parameters."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        result = initialize_dspy()
        
        mock_config_class.assert_called_once_with("gpt-4o-mini", None, 1000, 0.0)
        mock_config.configure_dspy.assert_called_once()
        assert result == mock_config
    
    @patch('src.marking.dspy_config.DSPyConfig')
    def test_initialize_dspy_with_parameters(self, mock_config_class):
        """Test initialize_dspy with custom parameters."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        result = initialize_dspy(
            model="gpt-4",
            api_key="test-key",
            max_tokens=2000,
            temperature=0.5
        )
        
        mock_config_class.assert_called_once_with("gpt-4", "test-key", 2000, 0.5)
        mock_config.configure_dspy.assert_called_once()
        assert result == mock_config


class TestCreateDynamicSignatureClass:
    """Test cases for create_dynamic_signature_class function."""
    
    def test_create_basic_signature_class(self):
        """Test creating a basic dynamic signature class."""
        input_fields = {"code": "Student code snippet"}
        output_fields = {"score": "Numeric score"}
        
        cls = create_dynamic_signature_class(
            "TestSignature",
            "Test docstring",
            input_fields,
            output_fields
        )
        
        assert cls.__name__ == "TestSignature"
        assert issubclass(cls, dspy.Signature)
        assert cls.__doc__ == "Test docstring"
    
    def test_create_signature_with_max_points(self):
        """Test creating signature class with custom max_points."""
        input_fields = {"code": "Student code"}
        output_fields = {"student_mark_out_of_10": "Grade"}
        
        cls = create_dynamic_signature_class(
            "TestSignature",
            "Test docstring",
            input_fields,
            output_fields,
            max_points=6
        )
        
        # Check basic properties
        assert cls.__name__ == "TestSignature"
        assert issubclass(cls, dspy.Signature)
    
    def test_invalid_max_points_raises_error(self):
        """Test that invalid max_points raises ValueError."""
        input_fields = {"code": "Student code"}
        output_fields = {"score": "Grade"}
        
        with pytest.raises(ValueError, match="max_points must be one of"):
            create_dynamic_signature_class(
                "TestSignature",
                "Test docstring",
                input_fields,
                output_fields,
                max_points=7
            )
    
    def test_valid_max_points_values(self):
        """Test all valid max_points values."""
        input_fields = {"code": "Student code"}
        output_fields = {"score": "Grade"}
        
        valid_points = [1, 2, 3, 4, 6, 10]  # Added 10 for backward compatibility
        
        for points in valid_points:
            cls = create_dynamic_signature_class(
                f"TestSignature{points}",
                "Test docstring",
                input_fields,
                output_fields,
                max_points=points
            )
            assert cls.__name__ == f"TestSignature{points}"


class TestCreateDynamicSignatureInstance:
    """Test cases for create_dynamic_signature_instance function."""
    
    def test_create_signature_instance(self):
        """Test creating a dynamic signature instance."""
        # First create a signature class
        input_fields = {"code": "Student code"}
        output_fields = {"score": "Grade"}
        
        signature_class = create_dynamic_signature_class(
            "TestSignature",
            "Test docstring",
            input_fields,
            output_fields,
            max_points=6  # Use valid max_points
        )
        
        # Then create an instance
        instance = create_dynamic_signature_instance("Test", signature_class)
        
        assert hasattr(instance, 'prog')
        assert hasattr(instance, 'forward')
        assert callable(instance.forward)


class TestParseIntegerAnswer:
    """Test cases for parse_integer_answer function."""
    
    def test_parse_simple_number(self):
        """Test parsing simple numeric answer."""
        assert parse_integer_answer("7") == 7
        assert parse_integer_answer("0") == 0
        assert parse_integer_answer("10") == 10
    
    def test_parse_number_in_sentence(self):
        """Test parsing number from sentence."""
        # The function takes the last number token, so "10" from "8 out of 10"
        assert parse_integer_answer("The score is 8 out of 10") == 10
        assert parse_integer_answer("I would give this a 6") == 6
    
    def test_parse_with_decimal(self):
        """Test parsing number with decimal (should take integer part)."""
        assert parse_integer_answer("7.5") == 7
        assert parse_integer_answer("The score is 8.9") == 8
    
    def test_parse_with_fraction(self):
        """Test parsing number with fraction (should take numerator)."""
        assert parse_integer_answer("7/10") == 7
        assert parse_integer_answer("Score: 8/10") == 8
    
    def test_parse_multiline_first_line_only(self):
        """Test parsing only first line when only_first_line=True."""
        multiline = "Score: 7\nExplanation: Good work\nMore text"
        assert parse_integer_answer(multiline, only_first_line=True) == 7
    
    def test_parse_multiline_all_lines(self):
        """Test parsing all lines when only_first_line=False."""
        multiline = "Some text\nScore: 8\nMore text"
        assert parse_integer_answer(multiline, only_first_line=False) == 8
    
    def test_parse_invalid_returns_zero(self):
        """Test that invalid input returns 0."""
        assert parse_integer_answer("no numbers here") == 0
        assert parse_integer_answer("") == 0
        assert parse_integer_answer("abc def") == 0
    
    def test_parse_with_max_points_clamping(self):
        """Test clamping to max_points."""
        assert parse_integer_answer("15", max_points=10) == 10
        assert parse_integer_answer("7", max_points=6) == 6
        # Negative numbers have the minus sign stripped, so "-5" becomes "5"
        assert parse_integer_answer("-5", max_points=10) == 5
    
    def test_parse_multiple_numbers_takes_last(self):
        """Test that multiple numbers results in taking the last one."""
        assert parse_integer_answer("First 3, then 5, finally 8") == 8
        assert parse_integer_answer("1 2 3 4 5") == 5


@pytest.fixture
def sample_marker_config():
    """Fixture providing sample marker configuration."""
    return {
        'docstring': 'Grade code on a scale',
        'input_fields': {'code': 'Student code'},
        'output_fields': {'score': 'Numeric grade'}
    }


class TestIntegration:
    """Integration tests for the DSPy configuration system."""
    
    @patch('dspy.configure')
    @patch('dspy.LM')
    def test_full_workflow(self, mock_lm, mock_configure):
        """Test complete workflow from initialization to signature creation."""
        mock_lm_instance = MagicMock()
        mock_lm.return_value = mock_lm_instance
        
        # Initialize DSPy
        config = initialize_dspy(api_key="test-key")
        
        # Create signature class
        input_fields = {"code": "Student code"}
        output_fields = {"student_mark_out_of_10": "Grade"}
        
        signature_class = create_dynamic_signature_class(
            "TestMarker",
            "Test marker",
            input_fields,
            output_fields,
            max_points=6
        )
        
        # Create instance
        marker = create_dynamic_signature_instance("TestMarker", signature_class)
        
        # Verify all components work together
        assert mock_configure.called
        assert signature_class.__name__ == "TestMarker"
        assert hasattr(marker, 'prog')
