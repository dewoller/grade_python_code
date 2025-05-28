"""
DSPy configuration module for the marking system.

This module handles DSPy initialization with OpenAI configuration and
provides utilities for creating dynamic signature classes with variable
point scales.
"""

import os
import dspy
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DSPyConfig:
    """Configuration class for DSPy with OpenAI integration."""
    
    def __init__(self, 
                 model: str = "gpt-4o-mini",
                 api_key: Optional[str] = None,
                 max_tokens: int = 1000,
                 temperature: float = 0.0):
        """
        Initialize DSPy configuration.
        
        Args:
            model: OpenAI model name (default: "gpt-4o-mini")
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
            max_tokens: Maximum tokens for model responses
            temperature: Temperature for model responses
        """
        self.model = model
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or provide api_key parameter."
            )
    
    def configure_dspy(self) -> None:
        """Configure DSPy with OpenAI client."""
        try:
            lm = dspy.LM(
                model=f"openai/{self.model}",
                api_key=self.api_key,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            dspy.configure(lm=lm)
            logger.info(f"DSPy configured with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to configure DSPy: {e}")
            raise


def initialize_dspy(model: str = "gpt-4o-mini", 
                   api_key: Optional[str] = None,
                   max_tokens: int = 1000,
                   temperature: float = 0.0) -> DSPyConfig:
    """
    Initialize DSPy with OpenAI configuration.
    
    Args:
        model: OpenAI model name
        api_key: OpenAI API key (if None, reads from environment)
        max_tokens: Maximum tokens for responses
        temperature: Temperature for responses
        
    Returns:
        DSPyConfig instance
    """
    config = DSPyConfig(model, api_key, max_tokens, temperature)
    config.configure_dspy()
    return config


def create_dynamic_signature_class(class_name: str, 
                                  doc_string: str, 
                                  input_fields: Dict[str, str], 
                                  output_fields: Dict[str, str],
                                  max_points: int = 10) -> type:
    """
    Create a dynamic signature class with given input and output fields.
    Adapts scoring prompts to use dynamic scales based on max_points.
    
    Args:
        class_name: The name of the class to be created
        doc_string: Documentation string for the class
        input_fields: Dictionary mapping field names to descriptions
        output_fields: Dictionary mapping field names to descriptions
        max_points: Maximum points for the scoring scale (1-6 range supported)
        
    Returns:
        Dynamically created DSPy Signature class
    """
    # Validate max_points
    if max_points not in [1, 2, 3, 4, 6, 10]:
        raise ValueError(f"max_points must be one of [1, 2, 3, 4, 6, 10], got {max_points}")
    
    # Define the fields
    fields = {}
    
    # Add input fields
    for field_name, description in input_fields.items():
        fields[field_name] = dspy.InputField(desc=description)
    
    # Add output fields with dynamic scaling
    for field_name, description in output_fields.items():
        # Modify description to include dynamic scale if it's a scoring field
        if 'out_of_10' in field_name or 'grade' in field_name.lower() or 'mark' in field_name.lower():
            dynamic_desc = f"{description}. Grade this criterion on a scale of 0-{max_points}"
        else:
            dynamic_desc = description
            
        fields[field_name] = dspy.OutputField(desc=dynamic_desc)

    fields['__doc__'] = doc_string
    
    # Create the class dynamically
    new_class = type(class_name, (dspy.Signature,), fields)
    return new_class


def create_dynamic_signature_instance(class_name: str, 
                                    dynamic_signature_class: type) -> Any:
    """
    Create a dynamic signature instance from a given dynamic signature class.
    
    Args:
        class_name: Name for the instance class
        dynamic_signature_class: The dynamic signature class
        
    Returns:
        An instance of a dynamically created class with a forward method
    """
    # Define the dynamic module class with a forward method
    dynamic_instance = type(
        class_name + "Module",
        (dspy.Module,),
        {
            '__init__': lambda self: setattr(self, 'prog', dspy.ChainOfThought(dynamic_signature_class)),
            'forward': lambda self, *args, **kwargs: self.prog(*args, **kwargs)
        }
    )
    
    # Instantiate and return the dynamic module class
    return dynamic_instance()


def parse_integer_answer(answer: str, only_first_line: bool = True, max_points: int = 10) -> int:
    """
    Robust parser for extracting integer scores from model responses.
    Adapted to handle variable maximum points.
    
    Args:
        answer: The model's text response
        only_first_line: Whether to only consider the first line
        max_points: Maximum allowed score
        
    Returns:
        Parsed integer score, clamped to [0, max_points]
    """
    try:
        if only_first_line:
            answer = answer.strip().split('\n')[0]

        # Find the last token that has a number in it
        tokens_with_numbers = [token for token in answer.split() if any(c.isdigit() for c in token)]
        if not tokens_with_numbers:
            return 0
        
        last_token = tokens_with_numbers[-1]
        
        # Handle negative numbers by removing the minus sign
        if last_token.startswith('-'):
            last_token = last_token[1:]
        
        # Extract the numeric part
        last_token = last_token.split('.')[0]  # Remove decimal part
        last_token = last_token.split('/')[0]  # Remove fraction part
        numeric_chars = ''.join([c for c in last_token if c.isdigit()])
        
        if not numeric_chars:
            return 0
            
        parsed_score = int(numeric_chars)
        
        # Clamp to valid range
        return max(0, min(parsed_score, max_points))

    except (ValueError, IndexError):
        logger.warning(f"Failed to parse answer: {answer}")
        return 0
