# Excel Output Generator

This module provides functionality to generate properly formatted Excel marking sheets for individual students. The generated Excel files include task-by-task scoring, error flags, subtotals, and an issues summary section.

## Features

- **Professional Formatting**: Consistent styling with headers, colors, and borders
- **Error Flag Support**: Clear indication of missing tasks, parsing errors, and incomplete code
- **Subtotals and Totals**: Automatic calculation of task subtotals and grand totals
- **Issues Summary**: Comprehensive list of problems encountered during marking
- **Batch Processing**: Support for generating summary sheets across multiple students
- **Data Validation**: Input validation to ensure consistency between rubric and results

## Usage

### Basic Usage

```python
from src.output.excel_generator import ExcelGenerator

# Initialize generator with output directory
generator = ExcelGenerator("output_directory")

# Generate marking sheet
output_file = generator.generate_marking_sheet(
    student_id="STUDENT_001",
    rubric_data=rubric_data,
    marking_results=marking_results,
    issues=issues_list
)
```

### Data Structures

#### Rubric Data Format
```python
rubric_data = {
    2: [  # Task 2
        {'criterion': 'Description of criterion', 'max_points': 2},
        {'criterion': 'Another criterion', 'max_points': 3},
    ],
    3: [  # Task 3
        {'criterion': 'Task 3 criterion', 'max_points': 1},
    ]
}
```

#### Marking Results Format
```python
marking_results = {
    2: [  # Task 2 results
        {'score': 2, 'criterion_index': 0},  # Full marks
        {'score': 1, 'criterion_index': 1},  # Partial marks
        {'score': 0, 'error_flag': 'PARSING_ERROR', 'criterion_index': 2},  # Error
    ],
    3: [  # Task 3 results
        {'score': 1, 'criterion_index': 0},
    ]
}
```

## Error Flags

The system supports several error flag types:

- `MISSING_TASK`: Task not found in student notebook
- `INCOMPLETE_CODE`: Only placeholder code provided
- `PARSING_ERROR`: AI processing failed for this criterion
- `API_ERROR`: Unable to evaluate due to API issues
- `TIMEOUT_ERROR`: Evaluation timed out

Error flags are displayed in score cells as "0 (ERROR_TYPE)" with distinctive formatting.

## Excel File Structure

The generated Excel files follow this structure:

1. **Header Row**: Column titles (Task Name, Criterion Description, Student Score, Max Points)
2. **Task Sections**: Each task with its criteria, one per row
3. **Subtotals**: Subtotal row after each task
4. **Grand Total**: Overall total across all tasks
5. **Issues Section**: List of problems encountered (if any)

## Styling

The module includes professional formatting:

- **Headers**: Blue background with white text
- **Task Headers**: Light blue background
- **Error Scores**: Light red background with red text
- **Subtotals**: Gray background with bold text
- **Grand Total**: Blue background with white text and thick border
- **Issues**: Yellow background for easy identification

## Batch Processing

Generate summary sheets for multiple students:

```python
batch_results = {
    "STUDENT_001": {
        "total_score": 75,
        "max_points": 83,
        "issues": ["Task 4: PARSING_ERROR"],
        "status": "Completed"
    },
    "STUDENT_002": {
        "total_score": 80,
        "max_points": 83,
        "issues": [],
        "status": "Completed"
    }
}

summary_file = generator.generate_batch_summary(batch_results)
```

## Validation

The generator includes input validation:

```python
validation_issues = generator.validate_input_data(rubric_data, marking_results)
if validation_issues:
    print("Issues found:", validation_issues)
```

## Example Output

A typical marking sheet will show:

```
Task Name    | Criterion Description                           | Student Score | Max Points
-------------|------------------------------------------------|---------------|------------
Task 2       | Joins list elements from payload              | 2             | 2
             | Converts message to lowercase                  | 2             | 2
             | Correctly displays output                      | 1             | 2
             | Includes additional test call                  | 0 (INCOMPLETE_CODE) | 2
             | SUBTOTAL                                       | 5             | 8

Task 3       | Uses data from payload                         | 3             | 3
             | Performs multiplication                        | 1             | 1
             | SUBTOTAL                                       | 4             | 4

             | GRAND TOTAL                                    | 9             | 12

ISSUES FOUND:
• Task 2 Criterion 4: INCOMPLETE_CODE - Only placeholder found
• Manual review required for 1 items
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_excel_generator.py -v
```

## Example Script

Run the example script to see the generator in action:

```bash
python example_excel_generator.py
```

This will create sample Excel files in the `example_output` directory.

## Dependencies

- `xlsxwriter`: For Excel file generation
- `pathlib`: For file path handling
- `logging`: For debug and error reporting

## Integration

This module integrates with:

- `src.parsers.rubric_parser`: For loading rubric data
- `src.marking.criterion_evaluator`: For getting marking results
- `src.cli.main`: For command-line interface integration
