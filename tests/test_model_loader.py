"""
Tests for the ModelLoader class.
"""

import pytest
import tempfile
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.marking.model_loader import ModelLoader


class TestModelLoader:
    """Test cases for ModelLoader class."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            programs_dir = temp_path / "programs"
            programs_dir.mkdir()
            
            # Create some mock model files
            (programs_dir / "question_subquestion_v2_model").touch()
            (programs_dir / "question_subquestion_code_model").touch()
            (programs_dir / "other_model").touch()
            
            # Create mock toml file
            toml_file = temp_path / "marking_runs.toml"
            toml_content = """
[question_subquestion_v2]
docstring = "Grade a code snippet"

[question_subquestion_v2.input_fields]
code = "code snippet"
question_text = "Question description"

[question_subquestion_v2.output_fields]
student_mark_out_of_10 = "Numeric grade between 0-10"

[question_subquestion_code]
docstring = "Grade with gold standard"

[question_subquestion_code.input_fields]
answer_code = "Gold standard code"
code = "code snippet"

[question_subquestion_code.output_fields]
student_mark_out_of_10 = "Numeric grade"
"""
            toml_file.write_text(toml_content)
            
            yield {
                'programs_dir': str(programs_dir),
                'toml_file': str(toml_file),
                'temp_path': temp_path
            }
    
    def test_init_success(self, temp_dirs):
        """Test successful ModelLoader initialization."""
        loader = ModelLoader(
            programs_dir=temp_dirs['programs_dir'],
            marking_config_file=temp_dirs['toml_file']
        )
        
        assert loader.programs_dir.exists()
        assert loader.marking_config_file.exists()
        assert loader.loaded_models == {}
        assert loader.marker_configs == {}
    
    def test_init_missing_programs_dir(self, temp_dirs):
        """Test initialization with missing programs directory."""
        with pytest.raises(FileNotFoundError, match="Programs directory not found"):
            ModelLoader(
                programs_dir="nonexistent_dir",
                marking_config_file=temp_dirs['toml_file']
            )
    
    def test_load_marker_configurations(self, temp_dirs):
        """Test loading marker configurations from TOML."""
        loader = ModelLoader(
            programs_dir=temp_dirs['programs_dir'],
            marking_config_file=temp_dirs['toml_file']
        )
        
        configs = loader.load_marker_configurations()
        
        assert len(configs) == 2
        assert 'question_subquestion_v2' in configs
        assert 'question_subquestion_code' in configs
        
        # Check structure
        config = configs['question_subquestion_v2']
        assert 'docstring' in config
        assert 'input_fields' in config
        assert 'output_fields' in config
        assert config['docstring'] == "Grade a code snippet"
    
    def test_list_available_models(self, temp_dirs):
        """Test listing available models."""
        loader = ModelLoader(
            programs_dir=temp_dirs['programs_dir'],
            marking_config_file=temp_dirs['toml_file']
        )
        
        models = loader.list_available_models()
        
        assert len(models) == 3
        assert "other_model" in models
        assert "question_subquestion_code_model" in models
        assert "question_subquestion_v2_model" in models
        # Should be sorted
        assert models == sorted(models)
    
    def test_get_best_model_for_marker(self, temp_dirs):
        """Test getting best model for a marker."""
        loader = ModelLoader(
            programs_dir=temp_dirs['programs_dir'],
            marking_config_file=temp_dirs['toml_file']
        )
        
        # Test exact match
        best_model = loader.get_best_model_for_marker("question_subquestion_v2")
        assert best_model == "question_subquestion_v2_model"
        
        # Test partial match
        best_model = loader.get_best_model_for_marker("question_subquestion_code")
        assert best_model == "question_subquestion_code_model"
        
        # Test no match
        best_model = loader.get_best_model_for_marker("nonexistent")
        assert best_model is None
    
    @patch('src.marking.model_loader.create_dynamic_signature_class')
    @patch('src.marking.model_loader.create_dynamic_signature_instance')
    def test_create_marker_with_dynamic_scale(self, mock_instance, mock_class, temp_dirs):
        """Test creating marker with dynamic scale."""
        mock_signature_class = MagicMock()
        mock_class.return_value = mock_signature_class
        mock_marker_instance = MagicMock()
        mock_instance.return_value = mock_marker_instance
        
        loader = ModelLoader(
            programs_dir=temp_dirs['programs_dir'],
            marking_config_file=temp_dirs['toml_file']
        )
        
        loader.load_marker_configurations()
        
        marker = loader.create_marker_with_dynamic_scale(
            "question_subquestion_v2",
            max_points=6
        )
        
        # Check that the signature class was created with correct parameters
        mock_class.assert_called_once()
        call_args = mock_class.call_args
        assert call_args[1]['max_points'] == 6
        assert 'question_subquestion_v2_6Point' in call_args[1]['class_name']
        
        # Check that instance was created
        mock_instance.assert_called_once_with(
            class_name='question_subquestion_v2_6Point',
            dynamic_signature_class=mock_signature_class
        )
        
        assert marker == mock_marker_instance
    
    def test_get_supported_point_scales(self, temp_dirs):
        """Test getting supported point scales."""
        loader = ModelLoader(
            programs_dir=temp_dirs['programs_dir'],
            marking_config_file=temp_dirs['toml_file']
        )
        
        scales = loader.get_supported_point_scales()
        assert scales == [1, 2, 3, 4, 6, 10]
