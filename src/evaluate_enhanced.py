"""
Enhanced evaluate.py with DSPy integration for variable point scales.

This module extends the original evaluate.py functionality to support
variable maximum points (1-6 range) while maintaining backward compatibility.
"""

import dspy
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import json
from matplotlib import pyplot as plt
import toml
import logging

# Import our new marking system modules
from .marking.dspy_config import (
    create_dynamic_signature_class as new_create_dynamic_signature_class,
    create_dynamic_signature_instance as new_create_dynamic_signature_instance,
    parse_integer_answer as new_parse_integer_answer
)
from .marking.model_loader import ModelLoader

logger = logging.getLogger(__name__)


# Backward compatibility: keep original functions with deprecation warnings
def create_dynamic_signature_class(class_name, doc_string, input_fields, output_fields):
    """
    Create a dynamic signature class with given input and output fields.
    
    DEPRECATED: Use marking.dspy_config.create_dynamic_signature_class instead.
    This function is maintained for backward compatibility.
    
    Args:
    - class_name: The name of the class to be created.
    - input_fields: A dictionary where keys are field names and values are descriptions.
    - output_fields: A dictionary where keys are field names and values are descriptions.
    
    Returns:
    - A dynamically created class.
    """
    import warnings
    warnings.warn(
        "create_dynamic_signature_class is deprecated. Use marking.dspy_config.create_dynamic_signature_class instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Use new implementation with default max_points=10 for backward compatibility
    return new_create_dynamic_signature_class(
        class_name, doc_string, input_fields, output_fields, max_points=10
    )


def create_dynamic_signature_instance(class_name, DynamicSignatureClass):
    """
    Create a dynamic signature instance from a given dynamic signature class. 
    
    DEPRECATED: Use marking.dspy_config.create_dynamic_signature_instance instead.
    This function is maintained for backward compatibility.
    
    Returns:
    - An instance of a dynamically created class with a `forward` method.
    """
    import warnings
    warnings.warn(
        "create_dynamic_signature_instance is deprecated. Use marking.dspy_config.create_dynamic_signature_instance instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return new_create_dynamic_signature_instance(class_name, DynamicSignatureClass)


def parse_integer_answer(answer, only_first_line=True):
    """
    Robust number parser.
    
    DEPRECATED: Use marking.dspy_config.parse_integer_answer instead.
    This function is maintained for backward compatibility.
    """
    import warnings
    warnings.warn(
        "parse_integer_answer is deprecated. Use marking.dspy_config.parse_integer_answer instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return new_parse_integer_answer(answer, only_first_line, max_points=10)


# Enhanced functions that support variable point scales
def create_dynamic_marker_with_scale(marker_name: str, 
                                   config: Dict[str, Any], 
                                   max_points: int = 10) -> Any:
    """
    Create a dynamic marker with specified point scale.
    
    Args:
        marker_name: Name of the marker
        config: Marker configuration dictionary
        max_points: Maximum points for the scale (1-6 supported)
        
    Returns:
        Marker instance configured for the specified scale
    """
    marker_class = new_create_dynamic_signature_class(
        class_name=f"{marker_name}_{max_points}Point",
        doc_string=config['docstring'],
        input_fields=config['input_fields'],
        output_fields=config['output_fields'],
        max_points=max_points
    )
    
    return new_create_dynamic_signature_instance(
        class_name=f"{marker_name}_{max_points}Point",
        dynamic_signature_class=marker_class
    )


def numeric_metric_with_scale(example, pred, max_points: int = 10, trace=None):
    """
    Calculate numeric metric for variable point scales.
    
    Args:
        example: Example with student_mark_normalized
        pred: Prediction with score field
        max_points: Maximum points for the scale
        trace: Optional trace parameter
        
    Returns:
        Normalized score based on the scale
    """
    # Get the predicted score, handling different field names
    pred_score = 0
    score_fields = ['student_mark_out_of_10', 'score', 'grade', 'mark']
    
    for field in score_fields:
        if hasattr(pred, field):
            pred_score = new_parse_integer_answer(str(getattr(pred, field)), max_points=max_points)
            break
    
    # Normalize both scores to 0-10 scale for comparison
    normalized_example = example.student_mark_normalized
    normalized_pred = (pred_score / max_points) * 10
    
    distance = abs(normalized_example - normalized_pred)
    
    if trace is not None:
        return distance < 0.5
    
    # Return score out of 10
    return (10 - distance) / 10


def numeric_metric_out_of_10(example, pred, trace=None):
    """
    Original numeric metric function maintained for backward compatibility.
    
    Distance from student mark to predicted mark, out of 10.
    """
    return numeric_metric_with_scale(example, pred, max_points=10, trace=trace)


# Define the signature for automatic assessments.
class Assess(dspy.Signature):
    """Assess the quality of a tweet along the specified dimension."""

    assessed_text = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer = dspy.OutputField(desc="Yes or No")


def plot_results(results, max_points: int = 10):
    """
    Plot results with support for variable point scales.
    
    Args:
        results: List of (example, prediction) tuples
        max_points: Maximum points for the scale
    """
    x = [int(item[0].student_mark_normalized) for item in results]
    
    # Extract scores handling different field names
    y = []
    for item in results:
        pred = item[1]
        pred_score = 0
        score_fields = ['student_mark_out_of_10', 'score', 'grade', 'mark']
        
        for field in score_fields:
            if hasattr(pred, field):
                pred_score = new_parse_integer_answer(str(getattr(pred, field)), max_points=max_points)
                break
        
        y.append(pred_score)

    # Create the plot
    plt.figure(figsize=(10, 6))
    
    jitter_amount = 0.2
    x_jittered = x + np.random.normal(0, jitter_amount, len(x))
    y_jittered = y + np.random.normal(0, jitter_amount, len(y))

    plt.scatter(x_jittered, y_jittered, color='blue', alpha=0.6, s=100)

    # Customize the plot
    plt.title(f'Student Mark Normalized vs Student Mark (Max: {max_points})', fontsize=16)
    plt.xlabel('Student Mark Normalized (0-10)', fontsize=12)
    plt.ylabel(f'Student Mark (0-{max_points})', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)

    # Add reference lines
    plt.plot([0, 10], [0, max_points], color='red', linestyle='--', alpha=0.5, label='Perfect Correlation')

    plt.legend()
    plt.tight_layout()
    plt.show()


def read_from_toml(file_path: str) -> Dict[str, Any]:
    """Read configuration from TOML file."""
    with open(file_path, 'r') as f:
        data = toml.load(f)
    return data


def create_dynamic_marker_classes_from_toml(file_path: str, max_points: int = 10):
    """
    Create dynamic marker classes from TOML configuration with variable point scales.
    
    Args:
        file_path: Path to TOML configuration file
        max_points: Maximum points for the scale
        
    Returns:
        Dictionary of marker configurations
    """
    data = read_from_toml(file_path)
    markers = {}
    
    for name, config in data.items():
        marker_class = new_create_dynamic_signature_class(
            class_name=f"{name}_{max_points}Point",
            doc_string=config['docstring'],
            input_fields=config['input_fields'],
            output_fields=config['output_fields'],
            max_points=max_points
        )
        
        markers[name] = {
            'docstring': config['docstring'],
            'input_fields': config['input_fields'],
            'output_fields': config['output_fields'],
            'marker_class': marker_class,
            'max_points': max_points
        }
    
    return markers


def create_dynamic_markers_from_toml(file_path: str, max_points: int = 10):
    """
    Create dynamic markers from TOML configuration with variable point scales.
    
    Args:
        file_path: Path to TOML configuration file
        max_points: Maximum points for the scale
        
    Returns:
        Dictionary of marker instances
    """
    markers = create_dynamic_marker_classes_from_toml(file_path, max_points)
    
    for name, data in markers.items():
        data['marker'] = new_create_dynamic_signature_instance(
            class_name=f"{name}_{max_points}Point",
            dynamic_signature_class=data['marker_class']
        )
    
    return markers


def create_optimized_markers_from_toml(file_path: str, 
                                     max_points: int = 10,
                                     programs_dir: str = "programs") -> Dict[str, Any]:
    """
    Create optimized markers using pre-trained models when available.
    
    Args:
        file_path: Path to TOML configuration file
        max_points: Maximum points for the scale
        programs_dir: Directory containing pre-trained models
        
    Returns:
        Dictionary of optimized marker instances
    """
    try:
        model_loader = ModelLoader(programs_dir, file_path)
        markers = {}
        
        # Load marker configurations
        configs = model_loader.load_marker_configurations()
        
        for name, config in configs.items():
            try:
                # Create optimized marker with pre-trained model if available
                marker = model_loader.create_optimized_marker(
                    marker_name=name,
                    max_points=max_points,
                    load_pretrained=True
                )
                
                markers[name] = {
                    'docstring': config['docstring'],
                    'input_fields': config['input_fields'],
                    'output_fields': config['output_fields'],
                    'marker': marker,
                    'max_points': max_points,
                    'optimized': True
                }
                
                logger.info(f"Created optimized marker: {name} ({max_points} points)")
                
            except Exception as e:
                logger.warning(f"Failed to create optimized marker {name}: {e}")
                
                # Fallback to basic marker
                marker = create_dynamic_marker_with_scale(name, config, max_points)
                markers[name] = {
                    'docstring': config['docstring'],
                    'input_fields': config['input_fields'],
                    'output_fields': config['output_fields'],
                    'marker': marker,
                    'max_points': max_points,
                    'optimized': False
                }
        
        return markers
        
    except Exception as e:
        logger.error(f"Failed to create optimized markers: {e}")
        # Fallback to basic implementation
        return create_dynamic_markers_from_toml(file_path, max_points)


def dump_single_evaluation(evaluation):
    """Dump a single evaluation to JSON format."""
    example_json = json.dumps(evaluation[0].toDict())
    prediction_json = json.dumps(evaluation[1].toDict())
    confidence = str(evaluation[2])
    return example_json, prediction_json, confidence


def write_evaluations_to_csv(marker_name, evaluations, file_path=None):
    """Write evaluations to CSV file."""
    if file_path is None:
        file_path = f'./evaluations/{marker_name}_evaluations.csv' 
    
    data = []
    for evaluation in evaluations:
        example_json, prediction_json, confidence = dump_single_evaluation(evaluation)
        data.append({
            'MarkerName': marker_name,
            'Example': example_json,
            'Prediction': prediction_json,
            'Confidence': confidence
        })
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)


def exemplify_data(dataset_details: pd.DataFrame):
    """Convert DataFrame to DSPy Examples."""
    dataset_details_ex = []
    for index, row in dataset_details.iterrows():
        ex = dspy.Example(base=row.to_dict())
        dataset_details_ex.append(ex)
    return dataset_details_ex


def split_data(dataset_details_ex: List[dspy.Example], inputs: List[str], n=None):
    """Split data into train, validation, and development sets."""
    if n is None:
        n = int(len(dataset_details_ex) / 10)

    from sklearn.model_selection import train_test_split
    
    # Splitting data
    train, temp = train_test_split(dataset_details_ex, test_size=0.2, random_state=42)  
    val, dev = train_test_split(temp, test_size=0.5, random_state=42)    

    trainset = [x.with_inputs(*inputs) for x in train[1:n*8]]
    valset = [x.with_inputs(*inputs) for x in val[1:n]]
    devset = [x.with_inputs(*inputs) for x in dev[1:n]]
    
    return trainset, valset, devset


# Utility functions for working with different point scales
def get_supported_point_scales() -> List[int]:
    """Get list of supported point scales."""
    return [1, 2, 3, 4, 6, 10]  # 10 included for backward compatibility


def validate_point_scale(max_points: int) -> bool:
    """Validate that a point scale is supported."""
    return max_points in get_supported_point_scales()


def convert_score_to_scale(score: float, from_scale: int, to_scale: int) -> float:
    """
    Convert a score from one scale to another.
    
    Args:
        score: The score to convert
        from_scale: The current maximum scale
        to_scale: The target maximum scale
        
    Returns:
        Converted score
    """
    if from_scale == to_scale:
        return score
    
    # Normalize to 0-1, then scale to target
    normalized = score / from_scale
    return normalized * to_scale
