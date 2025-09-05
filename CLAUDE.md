# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Academic Marking System Overview

This is an automated programming assignment marking tool that uses DSPy and OpenAI to evaluate student Jupyter notebooks against predefined rubrics and generate comprehensive Excel marking sheets.

## Build/Test Commands

### Development Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
# Or create .env file with OPENAI_API_KEY=your-api-key-here
```

### Testing Commands
```bash
# Run all tests
python -m pytest tests/

# Run specific test files
python -m pytest tests/test_criterion_evaluator.py
python -m pytest tests/test_notebook_parser.py
python -m pytest tests/test_rubric_parser.py

# Run a specific test method
python -m pytest tests/test_criterion_evaluator.py::TestCriterionEvaluator::test_evaluate_criterion

# Run integration tests
python run_integration_tests.py

# Generate test fixtures for development
python generate_test_fixtures.py

# Quick criterion evaluator test
python test_criterion_evaluator_quick.py
```

### CLI Usage
```bash
# Basic student marking
python mark_student.py --notebook path/to/student.ipynb --rubric path/to/rubric.csv

# Validation mode (check setup without processing)
python mark_student.py --validate --notebook data/example.ipynb --rubric data/rubric.csv

# Dry run (preview without actual marking)
python mark_student.py --notebook student.ipynb --rubric rubric.csv --dry-run

# Batch processing
./mark_all_students.sh data/assignments/ rubric.csv results/

# Debug mode with verbose output
python mark_student.py --notebook student.ipynb --rubric rubric.csv --debug
```

## Core Architecture

### Main Components Structure
```
src/
├── cli/                 # Command-line interface (Click-based)
│   ├── main.py         # CLI entry point with all commands
│   └── logging_config.py
├── marking/            # Core marking logic
│   ├── assignment_marker.py    # Main orchestrator class
│   ├── criterion_evaluator.py  # DSPy-based evaluation
│   ├── model_loader.py         # OpenAI model configuration
│   └── dspy_config.py         # DSPy framework setup
├── parsers/            # Input file processors
│   ├── notebook_parser.py     # Jupyter notebook extraction
│   └── rubric_parser.py       # CSV rubric processing  
├── output/            # Result generation
│   ├── excel_generator.py    # Excel file creation
│   └── formatting.py         # Output formatting utilities
└── utils/             # Shared utilities
    ├── error_handling.py     # Custom exception classes
    └── config.py            # Configuration management
```

### Key Data Flow
1. **CLI** (src/cli/main.py) → validates inputs and orchestrates process
2. **AssignmentMarker** (src/marking/assignment_marker.py) → coordinates all components
3. **NotebookParser** → extracts student code from .ipynb files using "#### Your Solution" markers
4. **RubricParser** → loads marking criteria from CSV files
5. **CriterionEvaluator** → uses DSPy + OpenAI to evaluate code against criteria
6. **ExcelGenerator** → creates detailed marking sheets with scores and feedback

### DSPy Integration
- Uses DSPy framework for structured AI prompting and evaluation
- Configured in src/marking/dspy_config.py with OpenAI models
- CriterionEvaluator implements DSPy Signature for consistent evaluation
- Default model: gpt-4o-mini (configurable via --model flag)

### Error Handling Strategy
- Custom exceptions in src/utils/error_handling.py
- Graceful degradation with detailed error messages
- Comprehensive validation mode (--validate flag)
- Issues tracking throughout marking process

## Code Style & Development Conventions

### Code Standards
- **Formatting**: Use black (line length 88), flake8 for linting
- **Type Hints**: mypy annotations throughout codebase  
- **Imports**: Organized with isort (stdlib, third-party, local)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Documentation**: Docstrings for modules, classes, and complex methods

### Testing Framework
- **Framework**: pytest with fixtures in tests/conftest.py
- **Integration Tests**: Mark with @pytest.mark.integration
- **Test Data**: Auto-generated fixtures via tests/fixtures/ modules
- **Coverage**: Use pytest-cov for coverage reporting

### Marker Standards
- Notebooks must contain "#### Your Solution" or "# Your Solution:" markers
- Rubric CSV format: Task Name | Criterion Description | Score | Max Points
- Expected 6 tasks per assignment (configurable in NotebookParser.EXPECTED_TASK_COUNT)

## Key Entry Points
- **CLI**: python mark_student.py (main interface)
- **Testing**: python -m pytest tests/
- **Validation**: --validate flag for setup verification  
- **Integration**: run_integration_tests.py for end-to-end testing

## Important File Paths
- Main script: mark_student.py
- Batch script: mark_all_students.sh  
- Requirements: requirements.txt
- Setup: setup.py (console_scripts entry point)
- Config: .env (for OPENAI_API_KEY)