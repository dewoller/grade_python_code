# DSPy Code Evaluation Framework - Claude Commands

## Build/Test Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/

# Run a specific test file
python -m pytest tests/test_criterion_evaluator.py

# Run a specific test
python -m pytest tests/test_criterion_evaluator.py::TestCriterionEvaluator::test_evaluate_criterion

# Run integration tests
python run_integration_tests.py

# Generate test fixtures
python generate_test_fixtures.py
```

## Code Style & Conventions
- **Formatting**: Use black for auto-formatting, line length 88
- **Linting**: flake8 for code quality and error detection
- **Type Hints**: Use mypy type annotations throughout codebase
- **Imports**: Organize imports with isort (stdlib, third-party, local)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: Use custom exceptions from src.utils.error_handling
- **Documentation**: Docstrings for modules, classes, functions, complex methods
- **Testing**: Pytest fixtures in conftest.py, integration tests marked with @pytest.mark.integration