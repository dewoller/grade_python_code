"""
Assignment Marker - Integration layer that coordinates all marking components.

This module provides the AssignmentMarker class that orchestrates the entire
marking process by coordinating the notebook parser, rubric parser, criterion
evaluator, and Excel generator components.
"""

import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass, field

from src.parsers.notebook_parser import NotebookParser, NotebookParsingError
from src.parsers.rubric_parser import RubricParser, RubricParsingError
from .criterion_evaluator import CriterionEvaluator, EvaluationResult
from src.output.excel_generator import ExcelGenerator, ExcelGenerationError

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result for a single task's evaluation."""
    task_number: int
    code: str
    criteria_results: List[Dict[str, Any]] = field(default_factory=list)
    total_score: int = 0
    max_points: int = 0
    issues: List[str] = field(default_factory=list)
    missing: bool = False


@dataclass
class MarkingResult:
    """Complete marking result for a student."""
    student_id: str
    total_score: int = 0
    max_points: int = 0
    task_results: Dict[int, TaskResult] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    status: str = "Unknown"


class AssignmentMarkingError(Exception):
    """Custom exception for assignment marking errors."""
    pass


class AssignmentMarker:
    """
    Orchestrates the complete marking process for student assignments.
    
    This class coordinates all components:
    1. NotebookParser - extracts student code from notebooks
    2. RubricParser - loads marking criteria
    3. CriterionEvaluator - scores individual criteria
    4. ExcelGenerator - produces formatted output
    
    Handles errors gracefully and provides detailed progress logging.
    """
    
    def __init__(self,
                 model_name: str = "gpt-4o-mini",
                 output_dir: str = "marking_output",
                 max_retries: int = 3,
                 verbosity: int = 1):
        """
        Initialize the assignment marker.
        
        Args:
            model_name: AI model to use for evaluation
            output_dir: Directory for output files
            max_retries: Maximum retry attempts for API calls
            verbosity: Logging level (0=quiet, 1=normal, 2=verbose)
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries
        self.verbosity = verbosity
        
        # Initialize components
        self.criterion_evaluator = CriterionEvaluator(
            model_name=model_name,
            max_retries=max_retries,
            verbosity=verbosity
        )
        
        self.excel_generator = ExcelGenerator(output_dir)
        
        # Caches
        self._rubric_cache: Dict[str, Dict[int, List[Dict[str, Any]]]] = {}
        
        # Statistics
        self.stats = {
            'assignments_processed': 0,
            'total_api_calls': 0,
            'total_errors': 0,
            'total_processing_time': 0.0
        }
        
        # Set up logging
        if verbosity >= 2:
            logger.setLevel(logging.DEBUG)
        elif verbosity >= 1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)
        
        logger.info(f"Initialized AssignmentMarker with model: {model_name}")
    
    def _load_notebook(self, notebook_path: str) -> Tuple[Dict[int, str], List[str]]:
        """
        Load and parse student notebook.
        
        Args:
            notebook_path: Path to the notebook file
            
        Returns:
            Tuple of (task_code_dict, issues_list)
            
        Raises:
            AssignmentMarkingError: If notebook cannot be loaded
        """
        try:
            logger.info(f"Loading notebook: {notebook_path}")
            parser = NotebookParser(notebook_path)
            tasks = parser.parse_tasks()
            issues = parser.get_issues()
            
            logger.info(f"Notebook loaded: {len(tasks)} tasks found, {len(issues)} issues")
            return tasks, issues
            
        except NotebookParsingError as e:
            raise AssignmentMarkingError(f"Failed to parse notebook: {e}")
        except Exception as e:
            raise AssignmentMarkingError(f"Unexpected error loading notebook: {e}")
    
    def _load_rubric(self, rubric_path: str) -> Tuple[Dict[int, List[Dict[str, Any]]], List[str]]:
        """
        Load and parse rubric file.
        
        Args:
            rubric_path: Path to the rubric CSV file
            
        Returns:
            Tuple of (rubric_dict, issues_list)
            
        Raises:
            AssignmentMarkingError: If rubric cannot be loaded
        """
        # Check cache first
        if rubric_path in self._rubric_cache:
            logger.debug(f"Using cached rubric: {rubric_path}")
            return self._rubric_cache[rubric_path], []
        
        try:
            logger.info(f"Loading rubric: {rubric_path}")
            parser = RubricParser(rubric_path)
            rubric_data = parser.parse_rubric()
            issues = parser.get_issues()
            
            # Cache the rubric
            self._rubric_cache[rubric_path] = rubric_data
            
            logger.info(f"Rubric loaded: {len(rubric_data)} tasks, {len(issues)} issues")
            return rubric_data, issues
            
        except RubricParsingError as e:
            raise AssignmentMarkingError(f"Failed to parse rubric: {e}")
        except Exception as e:
            raise AssignmentMarkingError(f"Unexpected error loading rubric: {e}")
    
    def _evaluate_task(self,
                      task_number: int,
                      code: str,
                      criteria: List[Dict[str, Any]],
                      task_description: str = "") -> TaskResult:
        """
        Evaluate a single task against its criteria.
        
        Args:
            task_number: The task number
            code: Student code for this task
            criteria: List of criteria dictionaries
            task_description: Description of the task
            
        Returns:
            TaskResult with evaluation outcomes
        """
        result = TaskResult(
            task_number=task_number,
            code=code,
            max_points=sum(c['max_points'] for c in criteria)
        )
        
        # Check if task is missing
        if not code or not code.strip():
            result.missing = True
            result.issues.append(f"Task {task_number}: MISSING_TASK")
            logger.warning(f"Task {task_number} has no code")
            
            # Create zero-score results for all criteria
            for idx, criterion in enumerate(criteria):
                result.criteria_results.append({
                    'criterion_index': idx,
                    'criterion': criterion['criterion'],
                    'max_points': criterion['max_points'],
                    'score': 0,
                    'error_flag': 'MISSING_TASK',
                    'confidence': 1.0,
                    'raw_response': 'Task not found'
                })
            
            return result
        
        # Generate task description if not provided
        if not task_description:
            task_description = f"Programming task {task_number} from student assignment"
        
        logger.info(f"Evaluating Task {task_number} with {len(criteria)} criteria")
        
        # Evaluate each criterion
        for idx, criterion in enumerate(criteria):
            criterion_desc = criterion['criterion']
            max_points = criterion['max_points']
            
            logger.debug(f"Evaluating Task {task_number} Criterion {idx + 1}: {criterion_desc[:50]}...")
            
            try:
                # Evaluate the criterion
                eval_result = self.criterion_evaluator.evaluate_criterion(
                    code=code,
                    task_description=task_description,
                    criterion=criterion_desc,
                    max_points=max_points
                )
                
                self.stats['total_api_calls'] += eval_result.retry_count + 1
                
                # Create result entry
                criterion_result = {
                    'criterion_index': idx,
                    'criterion': criterion_desc,
                    'max_points': max_points,
                    'score': eval_result.score,
                    'confidence': eval_result.confidence,
                    'raw_response': eval_result.raw_response
                }
                
                # Handle errors
                if eval_result.error:
                    if eval_result.error in ['EMPTY_CODE', 'PLACEHOLDER_CODE']:
                        criterion_result['error_flag'] = 'INCOMPLETE_CODE'
                        result.issues.append(f"Task {task_number} Criterion {idx + 1}: INCOMPLETE_CODE")
                    elif eval_result.error in ['SYNTAX_ERROR']:
                        criterion_result['error_flag'] = 'PARSING_ERROR'
                        result.issues.append(f"Task {task_number} Criterion {idx + 1}: SYNTAX_ERROR")
                    else:
                        criterion_result['error_flag'] = 'PARSING_ERROR'
                        result.issues.append(f"Task {task_number} Criterion {idx + 1}: PARSING_ERROR - {eval_result.error}")
                
                result.criteria_results.append(criterion_result)
                
                # Add to total score if no error flag
                if not criterion_result.get('error_flag'):
                    result.total_score += eval_result.score
                
                logger.debug(f"Criterion evaluated: {eval_result.score}/{max_points}")
                
            except Exception as e:
                self.stats['total_errors'] += 1
                logger.error(f"Error evaluating Task {task_number} Criterion {idx + 1}: {e}")
                
                # Create error result
                criterion_result = {
                    'criterion_index': idx,
                    'criterion': criterion_desc,
                    'max_points': max_points,
                    'score': 0,
                    'error_flag': 'PARSING_ERROR',
                    'confidence': 0.0,
                    'raw_response': f"Evaluation failed: {str(e)}"
                }
                
                result.criteria_results.append(criterion_result)
                result.issues.append(f"Task {task_number} Criterion {idx + 1}: PARSING_ERROR - {str(e)}")
        
        logger.info(f"Task {task_number} completed: {result.total_score}/{result.max_points} points")
        return result
    
    def mark_assignment(self,
                       student_id: str,
                       notebook_path: str,
                       rubric_path: str) -> MarkingResult:
        """
        Mark a complete student assignment.
        
        Args:
            student_id: Unique identifier for the student
            notebook_path: Path to the student's notebook
            rubric_path: Path to the marking rubric
            
        Returns:
            MarkingResult with complete evaluation
            
        Raises:
            AssignmentMarkingError: If critical errors prevent marking
        """
        start_time = time.time()
        
        result = MarkingResult(student_id=student_id)
        
        try:
            logger.info(f"Starting marking for student: {student_id}")
            
            # Step 1: Load notebook
            try:
                task_codes, notebook_issues = self._load_notebook(notebook_path)
                result.issues.extend(notebook_issues)
            except AssignmentMarkingError:
                result.status = "Failed - Notebook Error"
                raise
            
            # Step 2: Load rubric
            try:
                rubric_data, rubric_issues = self._load_rubric(rubric_path)
                result.issues.extend(rubric_issues)
                result.max_points = sum(
                    sum(c['max_points'] for c in criteria)
                    for criteria in rubric_data.values()
                )
            except AssignmentMarkingError:
                result.status = "Failed - Rubric Error"
                raise
            
            # Step 3: Evaluate each task
            for task_number in sorted(rubric_data.keys()):
                criteria = rubric_data[task_number]
                code = task_codes.get(task_number, "")
                
                logger.info(f"Processing Task {task_number}...")
                
                try:
                    task_result = self._evaluate_task(
                        task_number=task_number,
                        code=code,
                        criteria=criteria
                    )
                    
                    result.task_results[task_number] = task_result
                    result.total_score += task_result.total_score
                    result.issues.extend(task_result.issues)
                    
                except Exception as e:
                    logger.error(f"Error processing Task {task_number}: {e}")
                    self.stats['total_errors'] += 1
                    
                    # Create failed task result
                    failed_result = TaskResult(
                        task_number=task_number,
                        code=code,
                        max_points=sum(c['max_points'] for c in criteria),
                        issues=[f"Task {task_number}: PROCESSING_ERROR - {str(e)}"]
                    )
                    
                    result.task_results[task_number] = failed_result
                    result.issues.extend(failed_result.issues)
            
            # Step 4: Generate Excel output
            try:
                self._generate_excel_output(result, rubric_data)
                logger.info(f"Excel output generated for {student_id}")
            except Exception as e:
                logger.error(f"Error generating Excel output: {e}")
                result.issues.append(f"Excel generation failed: {str(e)}")
            
            # Determine final status
            if not result.task_results:
                result.status = "Failed - No Tasks Processed"
            elif result.total_score == 0:
                result.status = "Completed - Zero Score"
            elif len(result.issues) > 2:  # Changed from 5 to 2 for more sensitive detection
                result.status = "Completed with Issues"
            else:
                result.status = "Completed"
            
            # Update statistics
            result.processing_time = time.time() - start_time
            self.stats['assignments_processed'] += 1
            self.stats['total_processing_time'] += result.processing_time
            
            logger.info(f"Marking completed for {student_id}: {result.total_score}/{result.max_points} ({result.status})")
            
            return result
            
        except Exception as e:
            result.processing_time = time.time() - start_time
            result.status = f"Failed - {str(e)}"
            logger.error(f"Marking failed for {student_id}: {e}")
            raise
    
    def _generate_excel_output(self,
                              marking_result: MarkingResult,
                              rubric_data: Dict[int, List[Dict[str, Any]]]) -> None:
        """
        Generate Excel output for the marking result.
        
        Args:
            marking_result: The completed marking result
            rubric_data: The rubric criteria data
        """
        # Convert task results to Excel format
        excel_marking_results = {}
        
        for task_number, task_result in marking_result.task_results.items():
            excel_marking_results[task_number] = task_result.criteria_results
        
        # Generate the Excel file
        self.excel_generator.generate_marking_sheet(
            student_id=marking_result.student_id,
            rubric_data=rubric_data,
            marking_results=excel_marking_results,
            issues=marking_result.issues
        )
    
    def mark_batch(self,
                   assignments: List[Dict[str, str]],
                   rubric_path: str) -> Dict[str, MarkingResult]:
        """
        Mark multiple assignments in batch.
        
        Args:
            assignments: List of dicts with 'student_id' and 'notebook_path' keys
            rubric_path: Path to the marking rubric
            
        Returns:
            Dictionary mapping student IDs to MarkingResults
        """
        results = {}
        total_assignments = len(assignments)
        
        logger.info(f"Starting batch marking of {total_assignments} assignments")
        
        for i, assignment in enumerate(assignments, 1):
            student_id = assignment['student_id']
            notebook_path = assignment['notebook_path']
            
            logger.info(f"Processing assignment {i}/{total_assignments}: {student_id}")
            
            try:
                result = self.mark_assignment(student_id, notebook_path, rubric_path)
                results[student_id] = result
                
            except Exception as e:
                logger.error(f"Failed to mark {student_id}: {e}")
                results[student_id] = MarkingResult(
                    student_id=student_id,
                    status=f"Failed - {str(e)}",
                    issues=[f"Critical error: {str(e)}"]
                )
        
        # Generate batch summary
        try:
            batch_summary = {
                student_id: {
                    'total_score': result.total_score,
                    'max_points': result.max_points,
                    'issues': result.issues,
                    'status': result.status
                }
                for student_id, result in results.items()
            }
            
            self.excel_generator.generate_batch_summary(batch_summary)
            logger.info("Batch summary generated")
            
        except Exception as e:
            logger.error(f"Failed to generate batch summary: {e}")
        
        logger.info(f"Batch marking completed: {len(results)} assignments processed")
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        avg_time = (self.stats['total_processing_time'] / max(1, self.stats['assignments_processed']))
        
        return {
            'assignments_processed': self.stats['assignments_processed'],
            'total_api_calls': self.stats['total_api_calls'],
            'total_errors': self.stats['total_errors'],
            'total_processing_time': self.stats['total_processing_time'],
            'average_processing_time': avg_time,
            'error_rate': self.stats['total_errors'] / max(1, self.stats['total_api_calls'])
        }
    
    def validate_setup(self, notebook_path: str, rubric_path: str) -> List[str]:
        """
        Validate that all required files and components are working.
        
        Args:
            notebook_path: Path to a test notebook
            rubric_path: Path to the rubric file
            
        Returns:
            List of validation issues (empty if all good)
        """
        issues = []
        
        # Check file existence
        if not Path(notebook_path).exists():
            issues.append(f"Notebook file not found: {notebook_path}")
        
        if not Path(rubric_path).exists():
            issues.append(f"Rubric file not found: {rubric_path}")
        
        if issues:
            return issues
        
        # Test notebook parsing
        try:
            self._load_notebook(notebook_path)
        except Exception as e:
            issues.append(f"Notebook parsing failed: {e}")
        
        # Test rubric parsing
        try:
            self._load_rubric(rubric_path)
        except Exception as e:
            issues.append(f"Rubric parsing failed: {e}")
        
        # Test output directory
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True) 
        except Exception as e:
            issues.append(f"Cannot create output directory: {e}")
        
        return issues
