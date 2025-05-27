## Detailed Step-by-Step Blueprint for Production CLI Tool

### Phase 1: Project Setup and Infrastructure
1. Create new CLI project structure with proper module organization
2. Set up configuration management for paths and API keys
3. Create logging infrastructure with different verbosity levels
4. Set up testing framework with pytest

### Phase 2: Core Parsing Components
1. Build notebook parser to extract tasks from Jupyter notebooks
2. Build rubric parser to load marking criteria from CSV
3. Create error handling for malformed inputs
4. Add validation for extracted content

### Phase 3: DSPy Integration
1. Create dynamic marker adapter for variable point scales
2. Load pre-trained MIPRO models
3. Build criterion evaluator using DSPy
4. Add retry logic for API calls

### Phase 4: Output Generation
1. Build Excel spreadsheet generator
2. Add error flagging system
3. Create summary section for issues
4. Format output matching specifications

### Phase 5: CLI Interface
1. Build Click-based CLI interface
2. Wire all components together
3. Add batch processing support
4. Create comprehensive error reporting

### Phase 6: Testing and Validation
1. Unit tests for all components
2. Integration tests for full workflow
3. Performance testing
4. Quality assurance checks

## Iterative Implementation Prompts

### Prompt 1: Project Setup and Configuration

```text
Create the initial project structure for a Python CLI tool that will mark programming assignments. The tool needs to process Jupyter notebooks and generate Excel marking sheets.

Set up the following structure:
- mark_student.py (main CLI entry point)
- src/cli/__init__.py
- src/cli/main.py (CLI logic using Click library)
- src/cli/logging_config.py (logging setup)
- src/utils/__init__.py
- src/utils/config.py (configuration management)
- src/utils/error_handling.py (custom exceptions)
- tests/__init__.py
- tests/conftest.py (pytest configuration)
- requirements.txt
- setup.py

The CLI should accept these parameters:
- --notebook PATH (required): Student notebook file
- --rubric PATH (required): Marking criteria CSV file  
- --model TEXT (required): OpenAI model name
- --output-dir PATH (required): Directory for output files
- --verbose (optional): Show detailed logs
- --debug (optional): Show full debug output

Create a basic Click command that validates inputs exist and sets up logging based on verbosity flags. Include proper error handling for missing files.

Files to create:
- mark_student.py
- src/cli/__init__.py
- src/cli/main.py
- src/cli/logging_config.py
- src/utils/__init__.py
- src/utils/config.py
- src/utils/error_handling.py
- tests/conftest.py
- requirements.txt
- setup.py
```

### Prompt 2: Notebook Parser Module

```text
Create a notebook parser module that extracts programming tasks from Jupyter notebooks.

The notebooks contain 6 tasks marked with either:
- Primary marker: "#### Your Solution" (140 files)
- Secondary marker: "# Your Solution:" (4-7 files)

Each task contains student code in the cells following the marker. Tasks are numbered 2-7.

Create:
- src/parsers/__init__.py
- src/parsers/notebook_parser.py
- tests/test_notebook_parser.py

The NotebookParser class should:
1. Load a Jupyter notebook from a file path
2. Find all solution markers (both formats)
3. Extract code from cells following each marker
4. Associate code with task numbers (Task 2-7)
5. Return a dictionary: {task_number: code_content}
6. Validate all 6 tasks are present
7. Flag missing or incomplete tasks

Include comprehensive error handling for:
- Missing notebook files
- Corrupted JSON
- Missing solution markers
- Empty code cells

Create test fixtures with example notebooks for testing.

Context files:
- data/anonymized_assignments/001.ipynb (example notebook structure)

Files to create:
- src/parsers/__init__.py
- src/parsers/notebook_parser.py
- tests/test_notebook_parser.py
- tests/fixtures/notebooks/complete_notebook.ipynb
- tests/fixtures/notebooks/missing_tasks_notebook.ipynb
```

### Prompt 3: Rubric Parser Module

```text
Create a rubric parser module that loads marking criteria from CSV files.

The rubric CSV has 4 columns:
1. Task names (Task 2, Task 3, etc.)
2. Criterion descriptions
3. Empty (for scores)
4. Maximum points per criterion

Point distribution:
- Task 2: 8 points (5 criteria)
- Task 3: 10 points (6 criteria)
- Task 4: 15 points (7 criteria)
- Task 5: 15 points (7 criteria)
- Task 6: 15 points (6 criteria)
- Task 7: 20 points (5 criteria)
- Total: 83 points

Create:
- src/parsers/rubric_parser.py
- tests/test_rubric_parser.py

The RubricParser class should:
1. Load CSV file using pandas
2. Parse task names and criteria
3. Extract maximum points for each criterion
4. Group criteria by task
5. Validate total points = 83
6. Return structured rubric data

Include error handling for:
- Missing CSV files
- Malformed CSV structure
- Invalid point values
- Missing required columns

Context files:
- data/2025_specs/2025_S1_Marking_Sheet_edited.csv (rubric structure)

Files to create/modify:
- src/parsers/rubric_parser.py
- tests/test_rubric_parser.py
- tests/fixtures/rubrics/valid_rubric.csv
- tests/fixtures/rubrics/invalid_rubric.csv
```

### Prompt 4: DSPy Configuration and Model Loading

```text
Create DSPy integration modules for loading pre-trained MIPRO models and configuring the marking system.

The existing system uses DSPy with dynamic signatures for different point scales. We need to adapt the existing evaluate.py code to support variable maximum points (1-6 range).

Create:
- src/marking/__init__.py
- src/marking/dspy_config.py
- src/marking/model_loader.py
- tests/test_dspy_config.py

The modules should:
1. Initialize DSPy with OpenAI configuration
2. Load pre-trained models from programs/ directory
3. Create dynamic signature classes for variable point scales
4. Adapt existing create_dynamic_signature_class function
5. Support different maximum points (1, 2, 3, 4, 6)

Modify the scoring prompts to use dynamic scales:
- "Grade this criterion on a scale of 0-{max_points}"

Include proper environment variable handling for OPENAI_API_KEY.

Context files:
- src/evaluate.py (existing DSPy code)
- marking_runs.toml (marker configurations)
- programs/ directory (pre-trained models)

Files to create/modify:
- src/marking/__init__.py
- src/marking/dspy_config.py
- src/marking/model_loader.py
- tests/test_dspy_config.py
```

### Prompt 5: Criterion Evaluator

```text
Create the criterion evaluator that marks individual criteria using DSPy models.

Build on the DSPy configuration to create an evaluator that:
1. Takes student code, task description, and criterion
2. Uses appropriate pre-trained model
3. Generates score based on maximum points
4. Returns score and confidence level
5. Handles API errors with retry logic

Create:
- src/marking/criterion_evaluator.py
- tests/test_criterion_evaluator.py

The CriterionEvaluator class should:
1. Use dynamic prompting based on max_points
2. Parse numeric responses robustly
3. Handle non-numeric AI responses
4. Implement exponential backoff for retries
5. Log all API interactions based on verbosity

Add these evaluation scenarios:
- Perfect code (full marks)
- Partial implementation (partial marks)
- Missing functionality (zero marks)
- Syntax errors (zero marks)

Use the existing parse_integer_answer function as reference.

Context files:
- src/evaluate.py (parse_integer_answer function)
- marking_runs.toml (signature templates)

Files to create/modify:
- src/marking/criterion_evaluator.py
- tests/test_criterion_evaluator.py
```

### Prompt 6: Excel Output Generator

```text
Create an Excel output generator that produces individual student marking sheets.

The Excel file should match this structure:
- Column 1: Task Name (Task 2, Task 3, etc.)
- Column 2: Criterion Description
- Column 3: Student Score (with error flags if needed)
- Column 4: Max Points

Include subtotals for each task and a grand total.

Create:
- src/output/__init__.py
- src/output/excel_generator.py
- src/output/formatting.py
- tests/test_excel_generator.py

The ExcelGenerator class should:
1. Create workbook with proper formatting
2. Add task sections with criteria
3. Calculate subtotals per task
4. Add error flags: (MISSING_TASK), (INCOMPLETE_CODE), (PARSING_ERROR)
5. Add issues summary section at the end
6. Save as {student_id}_marks.xlsx

Error flag format in cells:
- "0 (MISSING_TASK)" - Task not found
- "0 (INCOMPLETE_CODE)" - Only placeholder code
- "0 (PARSING_ERROR)" - AI processing failed

Include summary section:
```
ISSUES FOUND:
- Task 4: MISSING_TASK
- Task 6 Criterion 3: PARSING_ERROR
- Manual review required for 2 items
```

Files to create:
- src/output/__init__.py
- src/output/excel_generator.py
- src/output/formatting.py
- tests/test_excel_generator.py
```

### Prompt 7: Integration Layer

```text
Create the integration layer that connects all components together.

Build a coordinator class that:
1. Loads student notebook using NotebookParser
2. Loads rubric using RubricParser
3. Evaluates each criterion using CriterionEvaluator
4. Generates Excel output using ExcelGenerator
5. Handles errors gracefully throughout

Create:
- src/marking/assignment_marker.py
- tests/test_assignment_marker.py

The AssignmentMarker class should:
1. Orchestrate the entire marking process
2. Track all errors and issues
3. Continue processing despite failures
4. Aggregate results for Excel generation
5. Provide detailed progress logging

Error handling strategy:
- File errors: Stop processing
- Missing tasks: Score 0, continue
- API errors: Retry 3x, then score 0
- Invalid responses: Score 0, flag error

Create comprehensive integration tests using mock data.

Context files:
- All previously created modules

Files to create:
- src/marking/assignment_marker.py
- tests/test_assignment_marker.py
```

### Prompt 8: CLI Wiring and Main Entry Point

```text
Wire together the CLI interface with all components to create the working application.

Update the CLI main.py to:
1. Initialize AssignmentMarker with configuration
2. Process single student notebook
3. Generate output Excel file
4. Display progress and results
5. Handle all errors gracefully

Update mark_student.py to be the main entry point that calls the CLI.

Add features:
- Progress bars for long operations
- Colored output for errors/warnings
- Summary statistics after completion
- Batch processing script example

Create:
- mark_all_students.sh (batch processing script)

The final CLI should show:
```
Processing student 001...
✓ Loaded notebook (6 tasks found)
✓ Loaded rubric (36 criteria)
⠼ Marking Task 2... (5/5 criteria)
✓ Task 2 complete: 7/8 points
...
✓ Generated 001_marks.xlsx

Summary:
- Total: 72/83 points
- Issues: 2 (see Excel file)
- Time: 2m 34s
```

Files to modify:
- src/cli/main.py
- mark_student.py
- mark_all_students.sh
```

### Prompt 9: Comprehensive Testing Suite

```text
Create a comprehensive testing suite covering all components and workflows.

Add tests for:
1. Unit tests for each module
2. Integration tests for full workflow
3. Performance tests
4. Error scenario tests

Create:
- tests/test_integration.py
- tests/test_performance.py
- tests/fixtures/generate_fixtures.py

Test scenarios:
1. Perfect student (all tasks complete)
2. Missing tasks student
3. Syntax errors in code
4. Empty notebook
5. Corrupted files
6. API failures
7. Rate limiting

Add fixtures:
- Sample notebooks with various issues
- Mock API responses
- Expected Excel outputs

Performance requirements:
- Single student < 5 minutes
- Memory usage < 500MB
- Graceful degradation

Create a fixture generator that creates test notebooks programmatically.

Files to create:
- tests/test_integration.py
- tests/test_performance.py
- tests/fixtures/generate_fixtures.py
```

### Prompt 10: Documentation and Final Polish

```text
Add comprehensive documentation and final polish to the production system.

Create:
- README.md (user documentation)
- DEVELOPMENT.md (developer guide)
- examples/ directory with sample usage
- Docker support (optional)

The README should include:
1. Installation instructions
2. Configuration setup
3. Basic usage examples
4. Troubleshooting guide
5. API key setup

Add final features:
1. --dry-run option to preview without marking
2. --continue-from option to resume batch processing
3. JSON output option for integration
4. Validation mode to check setup

Polish items:
- Consistent error messages
- Helpful command hints
- Version information
- License file

Create example configuration files and templates.

Files to create:
- README.md
- DEVELOPMENT.md
- examples/config.example.yaml
- examples/batch_process.example.sh
- Dockerfile (optional)
- .env.example
```


