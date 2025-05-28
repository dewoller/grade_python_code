"""
Model loader module for pre-trained MIPRO models.

This module handles loading and managing pre-trained DSPy models from the
programs directory and provides functionality to work with different
marker configurations.
"""

import os
import dspy
import pickle
import toml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .dspy_config import create_dynamic_signature_class, create_dynamic_signature_instance

logger = logging.getLogger(__name__)


class ModelLoader:
    """Loader for pre-trained MIPRO models and marker configurations."""
    
    def __init__(self, 
                 programs_dir: str = "programs",
                 marking_config_file: str = "marking_runs.toml"):
        """
        Initialize the model loader.
        
        Args:
            programs_dir: Directory containing pre-trained models
            marking_config_file: Path to TOML file with marker configurations
        """
        self.programs_dir = Path(programs_dir)
        self.marking_config_file = Path(marking_config_file)
        self.loaded_models: Dict[str, Any] = {}
        self.marker_configs: Dict[str, Dict[str, Any]] = {}
        
        if not self.programs_dir.exists():
            raise FileNotFoundError(f"Programs directory not found: {programs_dir}")
            
        if not self.marking_config_file.exists():
            raise FileNotFoundError(f"Marking config file not found: {marking_config_file}")
    
    def load_marker_configurations(self) -> Dict[str, Dict[str, Any]]:
        """
        Load marker configurations from TOML file.
        
        Returns:
            Dictionary of marker configurations
        """
        try:
            with open(self.marking_config_file, 'r') as f:
                data = toml.load(f)
            
            markers = {}
            for name, config in data.items():
                markers[name] = {
                    'docstring': config['docstring'],
                    'input_fields': config['input_fields'],
                    'output_fields': config['output_fields']
                }
            
            self.marker_configs = markers
            logger.info(f"Loaded {len(markers)} marker configurations")
            return markers
            
        except Exception as e:
            logger.error(f"Failed to load marker configurations: {e}")
            raise
    
    def list_available_models(self) -> List[str]:
        """
        List all available pre-trained models in the programs directory.
        
        Returns:
            List of model names
        """
        model_files = []
        for file_path in self.programs_dir.iterdir():
            if file_path.is_file():
                model_files.append(file_path.name)
        
        logger.info(f"Found {len(model_files)} available models")
        return sorted(model_files)
    
    def load_pretrained_model(self, model_name: str) -> Any:
        """
        Load a pre-trained MIPRO model.
        
        Args:
            model_name: Name of the model file to load
            
        Returns:
            Loaded DSPy module
        """
        model_path = self.programs_dir / model_name
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            # Try to load as a saved DSPy module
            if model_name in self.loaded_models:
                logger.info(f"Using cached model: {model_name}")
                return self.loaded_models[model_name]
            
            # Load the model
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            self.loaded_models[model_name] = model
            logger.info(f"Successfully loaded model: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def create_marker_with_dynamic_scale(self, 
                                       marker_name: str, 
                                       max_points: int = 10) -> Any:
        """
        Create a marker instance with dynamic point scale.
        
        Args:
            marker_name: Name of the marker configuration to use
            max_points: Maximum points for the scoring scale
            
        Returns:
            DSPy module instance configured for the specified point scale
        """
        if not self.marker_configs:
            self.load_marker_configurations()
        
        if marker_name not in self.marker_configs:
            raise ValueError(f"Marker configuration '{marker_name}' not found")
        
        config = self.marker_configs[marker_name]
        
        # Create dynamic signature class with specified max_points
        signature_class = create_dynamic_signature_class(
            class_name=f"{marker_name}_{max_points}Point",
            doc_string=config['docstring'],
            input_fields=config['input_fields'],
            output_fields=config['output_fields'],
            max_points=max_points
        )
        
        # Create and return the marker instance
        marker_instance = create_dynamic_signature_instance(
            class_name=f"{marker_name}_{max_points}Point",
            dynamic_signature_class=signature_class
        )
        
        logger.info(f"Created marker '{marker_name}' with {max_points}-point scale")
        return marker_instance
    
    def get_best_model_for_marker(self, marker_name: str) -> Optional[str]:
        """
        Get the best available pre-trained model for a specific marker.
        
        Args:
            marker_name: Name of the marker
            
        Returns:
            Best model name or None if no suitable model found
        """
        available_models = self.list_available_models()
        
        # Look for models that match the marker name
        matching_models = [
            model for model in available_models 
            if marker_name.lower() in model.lower()
        ]
        
        if not matching_models:
            logger.warning(f"No pre-trained models found for marker: {marker_name}")
            return None
        
        # Prefer MIPRO models with higher optimization scores
        mipro_models = [model for model in matching_models if 'MIPRO' in model]
        
        if mipro_models:
            # Sort by name to get the most recent/best version
            best_model = sorted(mipro_models)[-1]
            logger.info(f"Selected best model for {marker_name}: {best_model}")
            return best_model
        
        # Fallback to any matching model
        best_model = sorted(matching_models)[-1]
        logger.info(f"Selected fallback model for {marker_name}: {best_model}")
        return best_model
    
    def create_optimized_marker(self, 
                              marker_name: str, 
                              max_points: int = 10,
                              load_pretrained: bool = True) -> Any:
        """
        Create an optimized marker that uses pre-trained models if available.
        
        Args:
            marker_name: Name of the marker configuration
            max_points: Maximum points for scoring scale
            load_pretrained: Whether to load pre-trained model if available
            
        Returns:
            Optimized DSPy marker instance
        """
        # Create the base marker with dynamic scale
        marker = self.create_marker_with_dynamic_scale(marker_name, max_points)
        
        if load_pretrained:
            # Try to load and apply pre-trained model
            best_model_name = self.get_best_model_for_marker(marker_name)
            
            if best_model_name:
                try:
                    pretrained_model = self.load_pretrained_model(best_model_name)
                    
                    # If the loaded model has compatible structure, use its parameters
                    if hasattr(pretrained_model, 'prog') and hasattr(marker, 'prog'):
                        # Try to transfer learned parameters
                        if hasattr(pretrained_model.prog, 'signature') and hasattr(marker.prog, 'signature'):
                            marker.prog = pretrained_model.prog
                            logger.info(f"Applied pre-trained model to marker: {marker_name}")
                        
                except Exception as e:
                    logger.warning(f"Failed to apply pre-trained model: {e}. Using base marker.")
        
        return marker
    
    def get_marker_config(self, marker_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific marker.
        
        Args:
            marker_name: Name of the marker
            
        Returns:
            Marker configuration dictionary
        """
        if not self.marker_configs:
            self.load_marker_configurations()
        
        if marker_name not in self.marker_configs:
            raise ValueError(f"Marker configuration '{marker_name}' not found")
        
        return self.marker_configs[marker_name]
    
    def get_supported_point_scales(self) -> List[int]:
        """
        Get list of supported point scales.
        
        Returns:
            List of supported maximum point values
        """
        return [1, 2, 3, 4, 6, 10]
