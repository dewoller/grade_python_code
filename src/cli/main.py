"""Main CLI module using Click library."""

import os
import sys
import time
from pathlib import Path

import click
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init

from src.cli.logging_config import setup_logging
from src.utils.error_handling import (
    FileNotFoundError,
    InvalidFileError,
    MarkingError,
)
from src.marking.assignment_marker import AssignmentMarker, AssignmentMarkingError

# Initialize colorama for cross-platform colored output
colorama_init()


@click.command()
@click.option(
    "--notebook",
    "-n",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to student notebook file",
)
@click.option(
    "--rubric",
    "-r",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to marking criteria CSV file",
)
@click.option(
    "--model",
    "-m",
    type=str,
    default="gpt-4o-mini",
    help="OpenAI model name (default: gpt-4o-mini)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default="marking_output",
    help="Directory for output files (default: marking_output)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed logs",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Show full debug output",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview operation without actually marking",
)
@click.option(
    "--student-id",
    "-s",
    type=str,
    help="Student ID (defaults to notebook filename without extension)",
)
def cli(
    notebook: Path,
    rubric: Path,
    model: str,
    output_dir: Path,
    verbose: bool,
    debug: bool,
    dry_run: bool,
    student_id: str,
):
    """
    Mark programming assignments from Jupyter notebooks.

    This tool processes student notebooks, evaluates them against a rubric,
    and generates Excel marking sheets with scores and feedback.
    """
    # Setup logging based on verbosity flags
    logger = setup_logging(verbose=verbose, debug=debug)
    
    # Determine student ID
    if not student_id:
        student_id = notebook.stem
    
    logger.info(f"Starting student marking process for: {student_id}")
    logger.debug(f"Notebook: {notebook}")
    logger.debug(f"Rubric: {rubric}")
    logger.debug(f"Model: {model}")
    logger.debug(f"Output directory: {output_dir}")
    logger.debug(f"Dry run: {dry_run}")
    
    start_time = time.time()
    
    try:
        # Validate inputs
        _validate_inputs(notebook, rubric, output_dir, logger)
        
        # Check API key (only if not dry run)
        if not dry_run:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise MarkingError(
                    "OPENAI_API_KEY environment variable not set. "
                    "Please set it before running the tool."
                )
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured output directory exists: {output_dir}")
        
        # Initialize AssignmentMarker
        verbosity_level = 2 if debug else (1 if verbose else 0)
        marker = AssignmentMarker(
            model_name=model,
            output_dir=str(output_dir),
            verbosity=verbosity_level
        )
        
        if dry_run:
            _run_dry_run(marker, student_id, str(notebook), str(rubric))
        else:
            _run_marking(marker, student_id, str(notebook), str(rubric), start_time)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        _print_error(f"File not found: {e}")
        sys.exit(1)
    except InvalidFileError as e:
        logger.error(f"Invalid file: {e}")
        _print_error(f"Invalid file: {e}")
        sys.exit(1)
    except MarkingError as e:
        logger.error(f"Marking error: {e}")
        _print_error(f"Marking error: {e}")
        sys.exit(1)
    except AssignmentMarkingError as e:
        logger.error(f"Assignment marking error: {e}")
        _print_error(f"Assignment marking error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        _print_warning("\nProcess interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        _print_error(f"Unexpected error: {e}")
        sys.exit(1)


def _validate_inputs(notebook: Path, rubric: Path, output_dir: Path, logger):
    """Validate input files and directories."""
    # Check notebook file
    if not notebook.exists():
        raise FileNotFoundError(f"Notebook file not found: {notebook}")
    
    if not notebook.suffix.lower() == ".ipynb":
        raise InvalidFileError(
            f"Invalid notebook file: {notebook}. Expected .ipynb file."
        )
    
    logger.debug(f"Validated notebook file: {notebook}")
    
    # Check rubric file
    if not rubric.exists():
        raise FileNotFoundError(f"Rubric file not found: {rubric}")
    
    if not rubric.suffix.lower() == ".csv":
        raise InvalidFileError(
            f"Invalid rubric file: {rubric}. Expected .csv file."
        )
    
    logger.debug(f"Validated rubric file: {rubric}")
    
    # Check output directory permissions
    if output_dir.exists() and not os.access(output_dir, os.W_OK):
        raise MarkingError(
            f"Output directory is not writable: {output_dir}"
        )
    
    logger.debug("All inputs validated successfully")


def _print_success(message: str) -> None:
    """Print success message in green."""
    click.echo(click.style(f"✓ {message}", fg="green"))


def _print_error(message: str) -> None:
    """Print error message in red."""
    click.echo(click.style(f"✗ {message}", fg="red"), err=True)


def _print_warning(message: str) -> None:
    """Print warning message in yellow."""
    click.echo(click.style(f"⚠ {message}", fg="yellow"))


def _print_info(message: str) -> None:
    """Print info message in blue."""
    click.echo(click.style(f"ℹ {message}", fg="blue"))


def _run_dry_run(marker: AssignmentMarker, student_id: str, notebook_path: str, rubric_path: str) -> None:
    """Run a dry run to validate setup without actual marking."""
    _print_info(f"Running dry run for student: {student_id}")
    
    with click.progressbar(
        length=4,
        label="Validating setup",
        fill_char=click.style("█", fg="green"),
        empty_char="░"
    ) as bar:
        # Validate setup
        issues = marker.validate_setup(notebook_path, rubric_path)
        bar.update(1)
        
        if issues:
            _print_error("Validation failed:")
            for issue in issues:
                click.echo(f"  • {issue}")
            return
        
        bar.update(1)
        _print_success("All components validated")
        
        # Test notebook parsing
        try:
            tasks, notebook_issues = marker._load_notebook(notebook_path)
            bar.update(1)
            _print_success(f"Notebook loaded: {len(tasks)} tasks found")
            if notebook_issues:
                _print_warning(f"Notebook issues: {len(notebook_issues)}")
                for issue in notebook_issues[:3]:  # Show first 3 issues
                    click.echo(f"  • {issue}")
        except Exception as e:
            _print_error(f"Notebook parsing failed: {e}")
            return
        
        # Test rubric parsing
        try:
            rubric_data, rubric_issues = marker._load_rubric(rubric_path)
            bar.update(1)
            total_criteria = sum(len(criteria) for criteria in rubric_data.values())
            total_points = sum(
                sum(c['max_points'] for c in criteria)
                for criteria in rubric_data.values()
            )
            _print_success(f"Rubric loaded: {len(rubric_data)} tasks, {total_criteria} criteria, {total_points} points")
            if rubric_issues:
                _print_warning(f"Rubric issues: {len(rubric_issues)}")
        except Exception as e:
            _print_error(f"Rubric parsing failed: {e}")
            return
    
    _print_success("Dry run completed successfully")
    _print_info("Ready to process with actual marking")


def _run_marking(marker: AssignmentMarker, student_id: str, notebook_path: str, 
                 rubric_path: str, start_time: float) -> None:
    """Run the actual marking process."""
    _print_info(f"Processing student: {student_id}")
    
    try:
        # Run the marking process
        result = marker.mark_assignment(student_id, notebook_path, rubric_path)
        
        # Calculate processing time
        total_time = time.time() - start_time
        
        # Display results
        _display_results(result, total_time)
        
        # Display statistics
        stats = marker.get_statistics()
        _display_statistics(stats)
        
    except Exception as e:
        _print_error(f"Marking failed: {e}")
        raise


def _display_results(result, total_time: float) -> None:
    """Display marking results in a formatted way."""
    click.echo("\n" + "=" * 60)
    click.echo(click.style(f"MARKING RESULTS - {result.student_id}", fg="cyan", bold=True))
    click.echo("=" * 60)
    
    # Overall score
    percentage = (result.total_score / result.max_points * 100) if result.max_points > 0 else 0
    score_color = "green" if percentage >= 70 else "yellow" if percentage >= 50 else "red"
    
    click.echo(f"\n{click.style('Total Score:', bold=True)} "
               f"{click.style(f'{result.total_score}/{result.max_points}', fg=score_color, bold=True)} "
               f"({percentage:.1f}%)")
    
    # Task breakdown
    if result.task_results:
        click.echo(f"\n{click.style('Task Breakdown:', bold=True)}")
        for task_number in sorted(result.task_results.keys()):
            task_result = result.task_results[task_number]
            task_percentage = (task_result.total_score / task_result.max_points * 100) if task_result.max_points > 0 else 0
            task_color = "green" if task_percentage >= 70 else "yellow" if task_percentage >= 50 else "red"
            
            status_icon = "✓" if not task_result.issues else "⚠" if task_result.total_score > 0 else "✗"
            click.echo(f"  {status_icon} Task {task_number}: "
                       f"{click.style(f'{task_result.total_score}/{task_result.max_points}', fg=task_color)} "
                       f"({task_percentage:.1f}%)")
    
    # Issues summary
    if result.issues:
        click.echo(f"\n{click.style('Issues Found:', fg='yellow', bold=True)}")
        issue_counts = {}
        for issue in result.issues:
            if 'MISSING_TASK' in issue:
                issue_counts['Missing Tasks'] = issue_counts.get('Missing Tasks', 0) + 1
            elif 'INCOMPLETE_CODE' in issue:
                issue_counts['Incomplete Code'] = issue_counts.get('Incomplete Code', 0) + 1
            elif 'PARSING_ERROR' in issue:
                issue_counts['Parsing Errors'] = issue_counts.get('Parsing Errors', 0) + 1
            else:
                issue_counts['Other'] = issue_counts.get('Other', 0) + 1
        
        for issue_type, count in issue_counts.items():
            click.echo(f"  • {issue_type}: {count}")
        
        if len(result.issues) <= 5:
            click.echo("\nDetailed Issues:")
            for issue in result.issues:
                click.echo(f"  - {issue}")
        else:
            click.echo(f"\n(See Excel file for detailed list of {len(result.issues)} issues)")
    
    # Status and timing
    click.echo(f"\n{click.style('Status:', bold=True)} {result.status}")
    click.echo(f"{click.style('Processing Time:', bold=True)} {total_time:.1f}s")
    
    # Output file location
    excel_filename = f"{result.student_id}_marks.xlsx"
    _print_success(f"Excel file generated: {excel_filename}")
    
    click.echo("=" * 60)


def _display_statistics(stats: dict) -> None:
    """Display processing statistics."""
    if stats['assignments_processed'] == 0:
        return
    
    click.echo(f"\n{click.style('Processing Statistics:', bold=True)}")
    click.echo(f"  • API Calls: {stats['total_api_calls']}")
    click.echo(f"  • Errors: {stats['total_errors']}")
    click.echo(f"  • Error Rate: {stats['error_rate']:.1%}")
    if stats['total_api_calls'] > 0:
        click.echo(f"  • Avg Time per API Call: {stats['total_processing_time'] / stats['total_api_calls']:.1f}s")


if __name__ == "__main__":
    cli()
