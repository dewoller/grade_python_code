#!/usr/bin/env python3
"""
Example usage of the enhanced DSPy marking system with variable point scales.

This script demonstrates how to:
1. Initialize DSPy with OpenAI configuration
2. Load pre-trained models
3. Create markers with different point scales
4. Use the marking system for evaluation
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from marking import initialize_dspy, ModelLoader
from marking.dspy_config import create_dynamic_signature_class, parse_integer_answer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    print("DSPy Marking System Example")
    print("=" * 40)
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        return
    
    try:
        # 1. Initialize DSPy
        print("\n1. Initializing DSPy...")
        config = initialize_dspy(
            model="gpt-4o-mini",
            temperature=0.0
        )
        print(f"✓ DSPy initialized with model: gpt-4o-mini")
        
        # 2. Create ModelLoader
        print("\n2. Setting up ModelLoader...")
        model_loader = ModelLoader(
            programs_dir="programs",
            marking_config_file="marking_runs.toml"
        )
        
        # List available models
        available_models = model_loader.list_available_models()
        print(f"✓ Found {len(available_models)} pre-trained models")
        
        # Load marker configurations
        marker_configs = model_loader.load_marker_configurations()
        print(f"✓ Loaded {len(marker_configs)} marker configurations")
        
        # 3. Demonstrate different point scales
        print("\n3. Creating markers with different point scales...")
        
        supported_scales = model_loader.get_supported_point_scales()
        print(f"Supported scales: {supported_scales}")
        
        # Create markers for different scales
        markers = {}
        for marker_name in marker_configs.keys():
            print(f"\nCreating markers for '{marker_name}':")
            
            for scale in [3, 6, 10]:  # Test different scales
                try:
                    marker = model_loader.create_marker_with_dynamic_scale(
                        marker_name=marker_name,
                        max_points=scale
                    )
                    markers[f"{marker_name}_{scale}"] = marker
                    print(f"  ✓ {scale}-point scale marker created")
                except Exception as e:
                    print(f"  ✗ Failed to create {scale}-point scale: {e}")
        
        # 4. Demonstrate optimized markers with pre-trained models
        print("\n4. Creating optimized markers...")
        
        for marker_name in list(marker_configs.keys())[:2]:  # Test first 2 markers
            try:
                optimized_marker = model_loader.create_optimized_marker(
                    marker_name=marker_name,
                    max_points=6,
                    load_pretrained=True
                )
                markers[f"{marker_name}_optimized"] = optimized_marker
                print(f"  ✓ Optimized marker created for '{marker_name}'")
            except Exception as e:
                print(f"  ✗ Failed to create optimized marker for '{marker_name}': {e}")
        
        # 5. Demonstrate parse_integer_answer with different scales
        print("\n5. Testing score parsing with different scales...")
        
        test_responses = [
            "The score is 8 out of 10",
            "I would rate this a 4",
            "Score: 2.5/6",
            "This deserves a 3",
            "Grade: 15 (should be clamped)"
        ]
        
        for response in test_responses:
            for scale in [3, 6, 10]:
                parsed_score = parse_integer_answer(response, max_points=scale)
                print(f"  '{response}' -> {parsed_score}/{scale}")
        
        # 6. Show example usage pattern
        print("\n6. Example usage pattern:")
        print("""
# Basic usage:
from marking import initialize_dspy, ModelLoader

# Initialize system
config = initialize_dspy()
loader = ModelLoader()

# Create marker with 6-point scale
marker = loader.create_optimized_marker('question_subquestion_v2', max_points=6)

# Use marker (example inputs)
result = marker(
    code="print('Hello World')",
    question_text="Write a program that prints Hello World",
    subquestion="Correct output"
)

# Parse the result
score = parse_integer_answer(result.student_mark_out_of_10, max_points=6)
        """)
        
        print("\n✓ Example completed successfully!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
