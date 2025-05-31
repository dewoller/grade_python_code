# Academic Marking System

An automated programming assignment marking tool that uses DSPy and OpenAI to evaluate student Jupyter notebooks against predefined rubrics and generate comprehensive Excel marking sheets.

## Features

- 🔍 **Automated Code Analysis**: Evaluates student programming assignments using AI
- 📊 **Excel Output**: Generates detailed marking sheets with scores and feedback
- 🎯 **Flexible Rubrics**: Supports custom CSV-based marking criteria
- 📝 **Comprehensive Logging**: Detailed logging with multiple verbosity levels
- 🔄 **Batch Processing**: Process multiple students efficiently
- 🛡️ **Error Handling**: Robust error handling and graceful degradation
- 📋 **JSON Export**: Machine-readable output for integration
- ✅ **Validation Mode**: Pre-flight checks for setup validation

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Git (for cloning the repository)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd code_evaluate_dspy
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

5. **Verify installation:**
   ```bash
   python mark_student.py --version
   python mark_student.py --validate --notebook data/example.ipynb --rubric data/rubric.csv
   ```

## Configuration Setup

### API Key Configuration

The system requires an OpenAI API key. Set it using one of these methods:

**Method 1: Environment Variable**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Method 2: .env File**
Create a `.env` file in the project root:
```
OPENAI_API_KEY=sk-your-key-here
```

**Method 3: System Environment**
Add to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### Rubric Format

The rubric should be a CSV file with the following structure:

| Task Name | Criterion Description | Score | Max Points |
|-----------|----------------------|--------|------------|
| Task 2    | Implementation correctness | | 2 |
| Task 2    | Code quality | | 1 |
| Task 3    | Algorithm efficiency | | 3 |

Example rubric files are provided in the `examples/` directory.

## Basic Usage

### Single Student Marking

```bash
# Basic usage
python mark_student.py \
  --notebook path/to/student.ipynb \
  --rubric path/to/rubric.csv \
  --model gpt-4o-mini \
  --output-dir ./results

# With verbose output
python mark_student.py \
  --notebook student_001.ipynb \
  --rubric marking_criteria.csv \
  --verbose

# Dry run (validation only)
python mark_student.py \
  --notebook student_001.ipynb \
  --rubric marking_criteria.csv \
  --dry-run
```

### Batch Processing

```bash
# Process all students in a directory
./mark_all_students.sh data/assignments/ rubric.csv results/

# Continue from specific student
python mark_student.py \
  --notebook students/batch/*.ipynb \
  --rubric rubric.csv \
  --continue-from student_015
```

### Advanced Options

```bash
# Generate JSON output for integration
python mark_student.py \
  --notebook student.ipynb \
  --rubric rubric.csv \
  --json-output

# Use different OpenAI model
python mark_student.py \
  --notebook student.ipynb \
  --rubric rubric.csv \
  --model gpt-4

# Debug mode with full logging
python mark_student.py \
  --notebook student.ipynb \
  --rubric rubric.csv \
  --debug
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--notebook` | `-n` | Path to student notebook file | Required |
| `--rubric` | `-r` | Path to marking criteria CSV | Required |
| `--model` | `-m` | OpenAI model name | `gpt-4o-mini` |
| `--output-dir` | `-o` | Output directory | `marking_output` |
| `--student-id` | `-s` | Student ID override | Notebook filename |
| `--verbose` | `-v` | Show detailed logs | False |
| `--debug` | `-d` | Show debug output | False |
| `--dry-run` | | Preview without marking | False |
| `--json-output` | | Generate JSON output | False |
| `--validate` | | Run validation mode | False |
| `--continue-from` | | Resume from student ID | None |
| `--version` | | Show version info | False |

## Output Files

### Excel Marking Sheet

For each student, the system generates `{student_id}_marks.xlsx` containing:

- **Task Breakdown**: Scores for each task and criterion
- **Error Flags**: Indicates missing tasks, incomplete code, or parsing errors
- **Summary Section**: Overview of issues found
- **Total Score**: Final grade calculation

### JSON Output (Optional)

When `--json-output` is used, generates `{student_id}_results.json`:

```json
{
  \"timestamp\": \"2025-01-15T10:30:00\",
  \"student_id\": \"001\",
  \"total_score\": 72,
  \"max_points\": 83,
  \"percentage\": 86.7,
  \"status\": \"completed\",
  \"processing_time_seconds\": 156.2,
  \"task_results\": {
    \"task_2\": {
      \"score\": 7,
      \"max_points\": 8,
      \"percentage\": 87.5,
      \"issues\": []
    }
  },
  \"issues\": [],
  \"statistics\": {
    \"total_api_calls\": 36,
    \"total_errors\": 2,
    \"error_rate\": 0.056
  }
}
```

## Troubleshooting

### Common Issues

**1. "OPENAI_API_KEY not found" Error**
```bash
# Solution: Set your API key
export OPENAI_API_KEY="your-key-here"
# Or add to .env file
```

**2. "File not found" Error**
```bash
# Check file paths
ls -la path/to/notebook.ipynb
# Use absolute paths if needed
python mark_student.py --notebook /full/path/to/notebook.ipynb
```

**3. "Permission denied" Error**
```bash
# Check output directory permissions
chmod 755 output_directory/
# Or use a different output directory
python mark_student.py --output-dir ~/marking_results
```

**4. API Rate Limiting**
```bash
# Use a less powerful model to reduce costs
python mark_student.py --model gpt-3.5-turbo

# Run validation first to check setup
python mark_student.py --validate
```

### Error Codes in Output

| Error Flag | Description | Solution |
|------------|-------------|----------|
| `MISSING_TASK` | Task not found in notebook | Check task markers in notebook |
| `INCOMPLETE_CODE` | Only placeholder code found | Review student submission |
| `PARSING_ERROR` | AI failed to process code | Check code syntax, retry |

### Performance Optimization

**For large batches:**
- Use `gpt-4o-mini` instead of `gpt-4` for faster processing
- Process in smaller batches to avoid rate limits
- Use `--continue-from` to resume interrupted batches

**Memory usage:**
- Close other applications when processing large batches
- Use `--dry-run` first to estimate processing time

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
python mark_student.py \
  --notebook problem_student.ipynb \
  --rubric rubric.csv \
  --debug \
  --output-dir debug_output
```

This provides:
- Full API request/response logs
- Detailed parsing information
- Step-by-step processing trace
- Memory usage statistics

## Support

For issues and questions:

1. **Check logs**: Use `--verbose` or `--debug` for detailed information
2. **Validate setup**: Run `--validate` to check configuration
3. **Test with examples**: Use provided example files in `examples/`
4. **Review documentation**: Check `DEVELOPMENT.md` for technical details

## License

See `LICENSE` file for details.

## Contributing

See `DEVELOPMENT.md` for development setup and contribution guidelines.
