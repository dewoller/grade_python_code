"""
DSPy marking system integration module.

This module provides functionality for loading pre-trained MIPRO models,
configuring DSPy with OpenAI, and creating dynamic signature classes for
variable point scales in the marking system.
"""

from .dspy_config import DSPyConfig, initialize_dspy
from .model_loader import ModelLoader
from .criterion_evaluator import CriterionEvaluator, EvaluationResult
from .assignment_marker import AssignmentMarker, MarkingResult, TaskResult, AssignmentMarkingError

__all__ = [
    'DSPyConfig', 'initialize_dspy', 'ModelLoader', 
    'CriterionEvaluator', 'EvaluationResult',
    'AssignmentMarker', 'MarkingResult', 'TaskResult', 'AssignmentMarkingError'
]
