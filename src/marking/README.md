# DSPy Integration Modules for Variable Point Scales

This directory contains the DSPy integration modules that enable loading pre-trained MIPRO models and configuring the marking system with variable point scales (1-6 range).

## Overview

The marking system has been enhanced to support:
- Variable maximum points (1, 2, 3, 4, 6)
- Pre-trained MIPRO model loading
- Dynamic signature generation for different scales
- OpenAI API configuration management
- Backward compatibility with existing code

## Module Structure

```
src/marking/
├── __init__.py          # Main exports
├── dspy_config.py       # DSPy configuration and signature creation
├── model_loader.py      # Pre-trained model loading and management
└── README.md           # This file
```

## Quick Start

### 1. Basic Usage

```python
from marking import initialize_dspy, ModelLoader

# Initialize DSPy with OpenAI
config = initialize_dspy(model="gpt-4o-mini")

# Create model loader
loader = ModelLoader()

# Create a 6-point scale marker
marker = loader.create_optimized_marker(
    marker_name="question_subquestion_v2",
    max_points=6
)

# Use the marker
result = marker(
    code="print('Hello World')",
    question_text="Write a program that prints Hello World",
    subquestion="Correct output"
)
```

### 2. Environment Setup

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## API Reference

### DSPyConfig

Main configuration class for DSPy with OpenAI integration.

```python
from marking.dspy_config import DSPyConfig

config = DSPyConfig(
    model="gpt-4o-mini",      # OpenAI model name
    api_key=None,             # API key (uses env var if None)
    max_tokens=1000,          # Max response tokens
    temperature=0.0           # Response temperature
)
config.configure_dspy()
```

### ModelLoader

Handles pre-trained model loading and marker creation.

```python
from marking.model_loader import ModelLoader

loader = ModelLoader(
    programs_dir="programs",           # Pre-trained models directory
    marking_config_file="marking_runs.toml"  # Marker configurations
)

# Load configurations
configs = loader.load_marker_configurations()

# List available models
models = loader.list_available_models()

# Create optimized marker
marker = loader.create_optimized_marker(
    marker_name="question_subquestion_v2",
    max_points=6,
    load_pretrained=True
)
```

### Dynamic Signature Creation

Create markers with variable point scales:

```python
from marking.dspy_config import create_dynamic_signature_class

# Create signature class for 6-point scale
signature_class = create_dynamic_signature_class(
    class_name="CustomMarker",
    doc_string="Grade code on a 6-point scale",
    input_fields={
        "code": "Student code snippet",
        "question": "Question description"
    },
    output_fields={
        "score": "Numeric grade"
    },
    max_points=6
)
```

### Score Parsing

Parse model responses with scale-aware clamping:

```python
from marking.dspy_config import parse_integer_answer

# Parse with 6-point scale (clamps to 0-6)
score = parse_integer_answer("The score is 8", max_points=6)
# Returns: 6 (clamped)

# Parse with default 10-point scale
score = parse_integer_answer("Grade: 7/10")
# Returns: 7
```

## Supported Point Scales

The system supports the following maximum point values:
- **1 point**: Binary pass/fail
- **2 points**: Basic/Advanced
- **3 points**: Poor/Average/Good
- **4 points**: Four-level scale
- **6 points**: Six-level detailed scale

Note: 10-point scale is maintained for backward compatibility but not officially part of the 1-6 range requirement.

## Pre-trained Model Integration

The system automatically loads and applies pre-trained MIPRO models when available:

1. **Model Discovery**: Searches `programs/` directory for matching models
2. **MIPRO Preference**: Prioritizes models with "MIPRO" in the filename
3. **Automatic Loading**: Applies pre-trained parameters to markers
4. **Graceful Fallback**: Uses base markers if pre-trained models fail to load

Model filename matching patterns:
- `question_subquestion_v2_*` → matches `question_subquestion_v2` marker
- `*_MIPRO_*` → preferred over non-MIPRO models

## Configuration File Format

The `marking_runs.toml` file defines marker configurations:

```toml
[question_subquestion_v2]
docstring = "Grade a code snippet according to how well it answers a question and subquestion aspect on a scale of 0-{max_points}"

[question_subquestion_v2.input_fields]
code = "code snippet"
question_text = "Question description"
subquestion = "Subquestion Aspect"

[question_subquestion_v2.output_fields]
student_mark_out_of_10 = "Numeric grade between 0-{max_points}"
```

The `{max_points}` placeholder is automatically replaced with the actual scale value.

## Backward Compatibility

All original functions in `evaluate.py` are maintained with deprecation warnings:

```python
# Old way (deprecated but still works)
from src.evaluate import create_dynamic_signature_class
marker_class = create_dynamic_signature_class(...)

# New way (recommended)
from marking.dspy_config import create_dynamic_signature_class
marker_class = create_dynamic_signature_class(..., max_points=6)
```

## Error Handling

The modules include comprehensive error handling:

- **Missing API Key**: Clear error message with setup instructions
- **Invalid Point Scales**: Validation with supported values listed
- **Missing Models**: Graceful fallback to base markers
- **File Not Found**: Informative error messages with file paths
- **Configuration Errors**: Detailed parsing error information

## Testing

Run the test suite:

```bash
# Test DSPy configuration
pytest tests/test_dspy_config.py -v

# Test model loader
pytest tests/test_model_loader.py -v

# Run all tests
pytest tests/ -v
```

## Example Integration

See `example_usage.py` for a complete example showing:
- DSPy initialization
- Model loading
- Creating markers with different scales
- Score parsing
- Error handling

## Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Now you'll see detailed information about:
# - Model loading progress
# - Configuration parsing
# - Pre-trained model application
# - Error diagnostics
```

## Performance Considerations

- **Model Caching**: Pre-trained models are cached after first load
- **Configuration Caching**: TOML files are parsed once and cached
- **Memory Usage**: Each marker instance maintains its own parameters
- **API Efficiency**: Uses optimized DSPy ChainOfThought modules

## Migration Guide

### From Original evaluate.py

```python
# Before
from src.evaluate import create_dynamic_markers_from_toml
markers = create_dynamic_markers_from_toml("marking_runs.toml")

# After
from src.evaluate_enhanced import create_optimized_markers_from_toml
markers = create_optimized_markers_from_toml("marking_runs.toml", max_points=6)
```

### Adding New Point Scales

To add support for new point scales, update the validation in `dspy_config.py`:

```python
# In create_dynamic_signature_class function
if max_points not in [1, 2, 3, 4, 6, NEW_SCALE]:
    raise ValueError(f"max_points must be one of [1, 2, 3, 4, 6, {NEW_SCALE}]")
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key not provided"**
   - Set the `OPENAI_API_KEY` environment variable
   - Or pass `api_key` parameter to `initialize_dspy()`

2. **"max_points must be one of [1, 2, 3, 4, 6]"**
   - Use only supported point scales
   - Check that you're passing `max_points` as an integer

3. **"Programs directory not found"**
   - Ensure the `programs/` directory exists
   - Check the path in `ModelLoader()` initialization

4. **"No pre-trained models found for marker"**
   - This is a warning, not an error
   - The system will use base markers instead
   - Check model filename patterns match marker names

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show:
# - Detailed model loading steps
# - Configuration parsing details
# - API call information
# - Error stack traces
```
