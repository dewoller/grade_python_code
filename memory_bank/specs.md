# Automated Programming Assignment Marking System - Developer Specification

## 1. Project Overview

### 1.1 Purpose
Convert an existing research-based DSPy code evaluation system into a production CLI tool for automatically marking 147 anonymized programming assignments using optimized AI models.

### 1.2 Current System
- **Research codebase**: R/Python hybrid system using DSPy framework
- **Existing models**: Pre-trained MIPRO-optimized marking models
- **Data pipeline**: R-based notebook processing with Python AI evaluation
- **Location**: `/Users/dewoller/code/Richard_marking_project/code_evaluate_dspy`

### 1.3 Production Requirements
- **Input**: 147 individual Jupyter notebooks (001.ipynb - 147.ipynb)
- **Output**: Individual Excel marking sheets per student
- **Interface**: Command-line tool for single-student processing
- **Performance**: Reliable, error-tolerant, production-ready

---

## 2. Architecture Overview

### 2.1 System Components
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │ -> │  Notebook Parser │ -> │ Marking Engine  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                |                        |
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Rubric Loader   │    │ Output Generator│
                       └──────────────────┘    └─────────────────┘
```

### 2.2 Technology Stack
- **Python**: Main CLI application
- **DSPy Framework**: AI marking with pre-trained models
- **OpenAI API**: GPT-4/GPT-3.5 models
- **Pandas**: Data processing
- **openpyxl**: Excel output generation
- **Click**: CLI framework (per user preferences)

### 2.3 Data Flow
1. **Input**: Notebook file + rubric CSV
2. **Parse**: Extract 6 tasks from notebook
3. **Load**: Rubric criteria and scoring
4. **Mark**: Each criterion using optimized DSPy models
5. **Generate**: Individual Excel spreadsheet
6. **Log**: Process details and errors

---

## 3. Detailed Requirements

### 3.1 CLI Interface
```bash
python mark_student.py [OPTIONS]
```

**Required Parameters:**
- `--notebook PATH`: Student notebook file (001.ipynb, etc.)
- `--rubric PATH`: Marking criteria CSV file
- `--model TEXT`: OpenAI model (gpt-4, gpt-3.5-turbo)
- `--output-dir PATH`: Directory for output files

**Optional Parameters:**
- `--verbose`: Show detailed AI interaction logs
- `--debug`: Show full debug output with code snippets
- `--help`: Display usage information

**Example Usage:**
```bash
python mark_student.py --notebook 001.ipynb --rubric 2025_S1_Marking_Sheet_edited.csv --model gpt-4 --output-dir ./results --verbose
```

### 3.2 Input Data Specifications

#### 3.2.1 Notebook Structure
- **Format**: Jupyter notebook (.ipynb)
- **Location**: `/Users/dewoller/code/Richard_marking_project/code_evaluate_dspy/data/anonymized_assignments/`
- **Naming**: Sequential (001.ipynb, 002.ipynb, ..., 147.ipynb)
- **Tasks**: 6 programming tasks per assignment
- **Task Markers**: 
  - Primary: `#### Your Solution` (140 files)
  - Secondary: `# Your Solution:` (4-7 files)
- **Task Sequence**:
  1. `bot_whisper` - text processing/conversion
  2. `bot_multiply` - mathematical operations  
  3. `bot_count` - counting/iteration logic
  4. `bot_topic` - complex chatbot logic
  5. `bot_say` - usage or variations
  6. Integration task

#### 3.2.2 Rubric Structure
- **File**: `2025_S1_Marking_Sheet_edited.csv`
- **Format**: CSV with 4 columns
  - Column 1: Task names (Task 2, Task 3, etc.)
  - Column 2: Criterion descriptions
  - Column 3: Empty (for scores)
  - Column 4: Maximum points per criterion
- **Point Distribution**:
  - Task 2: 8 points (5 criteria)
  - Task 3: 10 points (6 criteria)
  - Task 4: 15 points (7 criteria)
  - Task 5: 15 points (7 criteria)
  - Task 6: 15 points (6 criteria)
  - Task 7: 20 points (5 criteria)
  - **Total**: 83 points

### 3.3 Output Specifications

#### 3.3.1 File Naming and Location
- **Directory**: User-specified via `--output-dir`
- **Filename**: `{student_id}_marks.xlsx` (e.g., `001_marks.xlsx`)
- **Format**: Excel (.xlsx)

#### 3.3.2 Spreadsheet Structure
```
Task 2          | Joins list elements from payload        | 2 | 2
                | Converts the message to lowercase        | 1 | 2
                | Correctly displays output by calling bot | 2 | 2
                | Includes additional test call            | 2 | 2
                | SUBTOTAL                                 | 7 | 8
                |                                          |   |
Task 3          | Uses data from payload for numbers       | 3 | 3
                | Performs multiplication                  | 1 | 1
                | ...                                      |...|...
```

**Columns:**
1. **Task Name**: Task 2, Task 3, etc.
2. **Criterion Description**: Full text from rubric
3. **Student Score**: AI-generated score with flags if needed
4. **Max Points**: Maximum possible points

#### 3.3.3 Error Flagging System
**In-cell flags (Option A):**
- `0 (MISSING_TASK)` - Task not found in notebook
- `0 (INCOMPLETE_CODE)` - Only placeholder code found
- `0 (PARSING_ERROR)` - AI processing failed

**Summary section (Option D):**
```
ISSUES FOUND:
- Task 4: MISSING_TASK
- Task 6 Criterion 3: PARSING_ERROR  
- Manual review required for 2 items
```

---

## 4. Implementation Details

### 4.1 File Structure
```
mark_student.py                    # Main CLI entry point
src/
├── cli/
│   ├── __init__.py
│   ├── main.py                   # CLI logic
│   └── logging_config.py         # Logging setup
├── parsers/
│   ├── __init__.py
│   ├── notebook_parser.py        # Extract tasks from notebooks
│   └── rubric_parser.py          # Load marking criteria
├── marking/
│   ├── __init__.py
│   ├── dspy_marker.py           # DSPy integration
│   └── criteria_evaluator.py    # Individual criterion marking
├── output/
│   ├── __init__.py
│   ├── excel_generator.py       # Generate marking spreadsheets
│   └── formatting.py            # Excel formatting utilities
└── utils/
    ├── __init__.py
    ├── error_handling.py        # Error management
    └── config.py                # Configuration management
```

### 4.2 Key Components

#### 4.2.1 Notebook Parser (`src/parsers/notebook_parser.py`)
```python
class NotebookParser:
    def parse_notebook(self, notebook_path: str) -> Dict[str, str]:
        """Extract tasks from Jupyter notebook."""
        # Parse JSON notebook
        # Find "Your Solution" markers (both formats)
        # Extract following code cells
        # Return dict: {task_number: code_content}
        
    def validate_tasks(self, tasks: Dict[str, str]) -> List[str]:
        """Validate extracted tasks and return issues."""
        # Check for 6 expected tasks
        # Identify missing/incomplete tasks
        # Return list of validation issues
```

#### 4.2.2 DSPy Marker (`src/marking/dspy_marker.py`)
```python
class DSPyMarker:
    def __init__(self, model_name: str):
        """Initialize with pre-trained MIPRO models."""
        # Load optimized models from programs/ directory
        # Configure OpenAI API
        
    def mark_criterion(self, code: str, task_desc: str, 
                      criterion: str, max_points: int) -> Tuple[int, float]:
        """Mark single criterion and return score + confidence."""
        # Use dynamic scoring based on max_points
        # Return (score, confidence_level)
        
    def create_dynamic_prompt(self, max_points: int) -> str:
        """Generate scoring prompt for specific point scale."""
        # Create prompt: "Grade on scale of 0-{max_points}"
```

#### 4.2.3 Excel Generator (`src/output/excel_generator.py`)
```python
class ExcelGenerator:
    def generate_marking_sheet(self, student_id: str, results: Dict, 
                              output_dir: str) -> str:
        """Generate individual student marking spreadsheet."""
        # Create Excel workbook
        # Format like original marking sheet
        # Include error flags and summary
        # Return output filepath
        
    def add_error_summary(self, worksheet, errors: List[str]):
        """Add issues summary section to spreadsheet."""
```

### 4.3 Modified Existing Components

#### 4.3.1 Updates to `src/evaluate.py`
```python
# MODIFY: Change from 0-10 scale to dynamic scale
def create_dynamic_signature_class(class_name, doc_string, input_fields, 
                                  output_fields, max_points):
    """Add max_points parameter for dynamic scoring."""
    
# MODIFY: Update scoring prompts
def create_scoring_prompt(criterion_desc: str, max_points: int) -> str:
    return f"Grade this criterion on a scale of 0-{max_points}: {criterion_desc}"
```

#### 4.3.2 Updates to `marking_runs.toml`
```toml
[individual_criterion_marker]
docstring = "Grade a code snippet for a specific criterion on its native point scale"

[individual_criterion_marker.input_fields]
code = "Student code snippet"
task_description = "Full task description and requirements"
criterion_description = "Specific criterion being evaluated"
examples_and_hints = "Examples and hints for this criterion"
max_points = "Maximum points possible for this criterion"

[individual_criterion_marker.output_fields]
criterion_score = "Score for this criterion (0 to max_points)"
```

---

## 5. Error Handling Strategy

### 5.1 Error Categories and Responses

| Error Type | Cause | Response | Flag | Continue? |
|------------|-------|----------|------|-----------|
| **File Not Found** | Missing notebook/rubric | Log error, exit | N/A | No |
| **Corrupted Notebook** | Invalid JSON/structure | Score 0 all tasks | `(MISSING_TASK)` | Yes |
| **Missing Task** | No solution marker found | Score 0 for task | `(MISSING_TASK)` | Yes |
| **Incomplete Code** | Only placeholder text | Score 0 for task | `(INCOMPLETE_CODE)` | Yes |
| **API Timeout** | OpenAI unavailable | Score 0, retry 3x | `(PARSING_ERROR)` | Yes |
| **API Rate Limit** | Too many requests | Exponential backoff | `(PARSING_ERROR)` | Yes |
| **Invalid Response** | AI returns non-numeric | Score 0 | `(PARSING_ERROR)` | Yes |
| **Rubric Parse Error** | Malformed CSV | Log error, exit | N/A | No |

### 5.2 Retry Logic
```python
@retry(stop=stop_after_attempt(3), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
def call_openai_api(prompt: str) -> str:
    """Call OpenAI with exponential backoff retry."""
```

### 5.3 Logging Strategy
```python
# Verbose mode (--verbose)
logger.info("Processing Task 2 - Criterion: 'Joins list elements'")
logger.info("→ Sending to OpenAI: [prompt preview]")
logger.info("← Received score: 2/2 (confidence: 0.85)")

# Debug mode (--debug)  
logger.debug("Full prompt: {full_prompt}")
logger.debug("Student code: {code_snippet}")
logger.debug("Complete API response: {api_response}")
```

---

## 6. Testing Plan

### 6.1 Unit Tests

#### 6.1.1 Notebook Parser Tests (`tests/test_parsers.py`)
```python
def test_parse_standard_format():
    """Test parsing notebooks with '#### Your Solution' markers."""
    
def test_parse_alternative_format():
    """Test parsing notebooks with '# Your Solution:' markers."""
    
def test_missing_tasks():
    """Test handling notebooks with missing tasks."""
    
def test_corrupted_notebook():
    """Test handling invalid JSON notebooks."""
    
def test_empty_notebook():
    """Test handling completely empty notebooks."""
```

#### 6.1.2 Marking Engine Tests (`tests/test_marking.py`)
```python
def test_dynamic_scoring():
    """Test scoring on different point scales (1, 2, 3, 4, 6 points)."""
    
def test_criterion_evaluation():
    """Test individual criterion marking accuracy."""
    
def test_api_error_handling():
    """Test handling OpenAI API failures."""
    
def test_prompt_generation():
    """Test dynamic prompt creation for different point scales."""
```

#### 6.1.3 Output Generation Tests (`tests/test_output.py`)
```python
def test_excel_generation():
    """Test Excel spreadsheet creation and formatting."""
    
def test_error_flagging():
    """Test error flags appear correctly in spreadsheets."""
    
def test_summary_section():
    """Test issues summary section generation."""
```

### 6.2 Integration Tests

#### 6.2.1 End-to-End Tests (`tests/test_integration.py`)
```python
def test_complete_marking_flow():
    """Test full CLI execution from notebook to Excel output."""
    
def test_error_recovery():
    """Test system continues after partial failures."""
    
def test_batch_consistency():
    """Test marking same student multiple times gives consistent results."""
```

### 6.3 Test Data
```
tests/fixtures/
├── notebooks/
│   ├── perfect_student.ipynb      # All tasks complete
│   ├── missing_tasks.ipynb        # Some tasks missing
│   ├── empty_student.ipynb        # No solutions provided
│   ├── corrupted.ipynb           # Invalid JSON
│   └── alternative_format.ipynb  # Uses '# Your Solution:'
├── rubrics/
│   ├── standard_rubric.csv       # Normal rubric
│   └── malformed_rubric.csv      # Invalid format
└── expected_outputs/
    ├── perfect_student_marks.xlsx
    ├── missing_tasks_marks.xlsx
    └── empty_student_marks.xlsx
```

### 6.4 Performance Tests
```python
def test_processing_time():
    """Ensure single student processing completes within 5 minutes."""
    
def test_api_rate_limits():
    """Test handling OpenAI rate limits gracefully."""
    
def test_memory_usage():
    """Ensure memory usage stays reasonable for large notebooks."""
```

---

## 7. Configuration and Deployment

### 7.1 Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Install CLI tool
pip install -e .
```

### 7.2 Configuration Files
```
config/
├── api_config.yaml           # OpenAI API settings
├── logging_config.yaml       # Logging configuration  
├── marking_thresholds.yaml   # Quality control settings
└── paths_config.yaml         # Default file paths
```

### 7.3 Quality Assurance Checklist
- [ ] CLI accepts all required parameters
- [ ] Handles both solution marker formats
- [ ] Processes all 6 task types correctly
- [ ] Generates properly formatted Excel files
- [ ] Error flags appear in correct locations
- [ ] Issues summary section is complete
- [ ] Logging works at both verbose and debug levels
- [ ] Pre-trained MIPRO models load successfully
- [ ] API errors are handled gracefully
- [ ] Zero scores assigned for missing/failed content

---

## 8. Usage Instructions

### 8.1 Basic Usage
```bash
# Mark single student
python mark_student.py \
  --notebook data/anonymized_assignments/001.ipynb \
  --rubric data/2025_specs/2025_S1_Marking_Sheet_edited.csv \
  --model gpt-4 \
  --output-dir ./results \
  --verbose

# Expected output: ./results/001_marks.xlsx
```

### 8.2 Batch Processing Script
```bash
#!/bin/bash
# mark_all_students.sh - Process all 147 students

for i in {001..147}; do
    echo "Processing student $i..."
    python mark_student.py \
      --notebook data/anonymized_assignments/$i.ipynb \
      --rubric data/2025_specs/2025_S1_Marking_Sheet_edited.csv \
      --model gpt-4 \
      --output-dir ./results \
      --verbose
    sleep 2  # Rate limiting
done
```

### 8.3 Quality Control Workflow
1. **Test run**: Process 3-5 students manually
2. **Review outputs**: Check Excel formatting and accuracy  
3. **Validate flagging**: Ensure errors are properly marked
4. **Batch process**: Run all 147 students
5. **Final review**: Check summary logs for any systemic issues

---

## 9. Success Criteria

### 9.1 Functional Requirements
- [ ] CLI processes individual notebooks successfully
- [ ] Extracts all 6 tasks from properly formatted notebooks
- [ ] Marks each criterion using appropriate point scale
- [ ] Generates Excel spreadsheets matching required format
- [ ] Handles errors gracefully with appropriate flags
- [ ] Provides detailed logging and progress feedback

### 9.2 Performance Requirements
- [ ] Single student processing completes within 5 minutes
- [ ] Handles API rate limits without failing
- [ ] Memory usage remains stable for large notebooks
- [ ] Error recovery allows continued processing

### 9.3 Quality Requirements
- [ ] Marking accuracy comparable to research system results
- [ ] Consistent scoring across multiple runs of same student
- [ ] Clear error reporting for manual review items
- [ ] Professional Excel output suitable for grade records

This specification provides everything needed for immediate implementation of the production marking system using the existing research codebase as the foundation.
