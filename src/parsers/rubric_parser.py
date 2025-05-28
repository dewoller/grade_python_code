"""
Rubric Parser for loading marking criteria from CSV files.

This module parses CSV rubric files to extract marking criteria for each task,
including task names, criterion descriptions, and maximum points per criterion.
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class RubricParsingError(Exception):
    """Custom exception for rubric parsing errors."""
    pass


class RubricParser:
    """
    Parser for extracting marking criteria from CSV rubric files.
    
    The parser loads CSV files containing task criteria and point allocations,
    validates the structure, and provides structured access to marking criteria.
    """
    
    # Expected total points across all tasks
    EXPECTED_TOTAL_POINTS = 83
    
    # Expected task point distribution
    EXPECTED_TASK_POINTS = {
        2: 8,   # Task 2: 4 criteria
        3: 10,  # Task 3: 5 criteria  
        4: 15,  # Task 4: 7 criteria
        5: 15,  # Task 5: 7 criteria
        6: 15,  # Task 6: 6 criteria
        7: 20   # Task 7: 5 criteria
    }
    
    def __init__(self, rubric_path: str):
        """
        Initialize the parser with a rubric CSV file path.
        
        Args:
            rubric_path: Path to the CSV rubric file
            
        Raises:
            RubricParsingError: If file doesn't exist or can't be read
        """
        self.rubric_path = Path(rubric_path)
        self.rubric_data = None
        self.tasks = {}
        self.issues = []
        
        if not self.rubric_path.exists():
            raise RubricParsingError(f"Rubric file not found: {rubric_path}")
        
        self._load_rubric()
    
    def _load_rubric(self) -> None:
        """
        Load and parse the CSV rubric file.
        
        Raises:
            RubricParsingError: If CSV is corrupted or invalid
        """
        try:
            # Load CSV with pandas, handling potential encoding issues including BOM
            self.rubric_data = pd.read_csv(
                self.rubric_path, 
                header=None,
                names=['task', 'criterion', 'score', 'max_points'],
                dtype={
                    'task': 'str',
                    'criterion': 'str', 
                    'score': 'str',
                    'max_points': 'str'
                },
                keep_default_na=False,
                encoding='utf-8-sig'  # Handle BOM
            )
            
            # Check if file is effectively empty after loading
            if len(self.rubric_data) == 0:
                raise RubricParsingError("Rubric CSV file is empty")
            
            logger.info(f"Successfully loaded rubric with {len(self.rubric_data)} rows")
            
        except pd.errors.EmptyDataError:
            raise RubricParsingError("Rubric CSV file is empty")
        except pd.errors.ParserError as e:
            raise RubricParsingError(f"Error parsing CSV file: {e}")
        except UnicodeDecodeError as e:
            raise RubricParsingError(f"Error reading CSV file encoding: {e}")
        except Exception as e:
            raise RubricParsingError(f"Error loading rubric: {e}")
    
    def _extract_task_number(self, task_text: str) -> Optional[int]:
        """
        Extract task number from task text.
        
        Args:
            task_text: Text containing task information
            
        Returns:
            Task number (2-7) or None if not found
        """
        if not task_text or pd.isna(task_text):
            return None
        
        # Look for "Task X" pattern
        match = re.search(r'Task\s+(\d+)', str(task_text), re.IGNORECASE)
        if match:
            task_num = int(match.group(1))
            if 2 <= task_num <= 7:
                return task_num
        
        return None
    
    def _parse_max_points(self, points_text: str) -> Optional[int]:
        """
        Parse maximum points from text.
        
        Args:
            points_text: Text containing point value
            
        Returns:
            Point value as integer or None if invalid
        """
        if not points_text or pd.isna(points_text):
            return None
        
        # Clean the text and try to extract integer
        clean_text = str(points_text).strip()
        if not clean_text or clean_text == '':
            return None
        
        try:
            return int(float(clean_text))
        except (ValueError, TypeError):
            return None
    
    def _is_subtotal_row(self, row: pd.Series) -> bool:
        """
        Check if a row represents a subtotal.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if this is a subtotal row
        """
        criterion_text = str(row['criterion']).strip().upper()
        return 'SUBTOTAL' in criterion_text
    
    def _is_empty_row(self, row: pd.Series) -> bool:
        """
        Check if a row is empty or contains only whitespace.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if row is effectively empty
        """
        for col in ['task', 'criterion', 'max_points']:
            if str(row[col]).strip():
                return False
        return True
    
    def parse_rubric(self) -> Dict[int, List[Dict[str, Any]]]:
        """
        Parse the rubric CSV and extract all task criteria.
        
        Returns:
            Dictionary mapping task numbers to lists of criteria
            
        Raises:
            RubricParsingError: If parsing fails
        """
        if self.rubric_data is None:
            raise RubricParsingError("Rubric not loaded")
        
        tasks = {}
        current_task = None
        
        logger.info(f"Parsing rubric with {len(self.rubric_data)} rows")
        
        for idx, row in self.rubric_data.iterrows():
            # Skip empty rows
            if self._is_empty_row(row):
                continue
            
            # Skip subtotal rows
            if self._is_subtotal_row(row):
                continue
            
            # Check if this row starts a new task
            task_num = self._extract_task_number(row['task'])
            if task_num is not None:
                current_task = task_num
                if current_task not in tasks:
                    tasks[current_task] = []
                logger.debug(f"Found Task {current_task}")
            
            # Extract criterion information
            criterion_text = str(row['criterion']).strip()
            max_points = self._parse_max_points(row['max_points'])
            
            # Skip rows without criterion text or points
            if not criterion_text or max_points is None:
                continue
            
            if current_task is None:
                issue = f"Found criterion without task context at row {idx}: {criterion_text}"
                self.issues.append(issue)
                logger.warning(issue)
                continue
            
            # Add criterion to current task
            criterion = {
                'task_number': current_task,
                'criterion': criterion_text,
                'max_points': max_points,
                'row_index': idx
            }
            
            tasks[current_task].append(criterion)
            logger.debug(f"Added criterion to Task {current_task}: {criterion_text} ({max_points} pts)")
        
        # Validate task structure
        self._validate_task_structure(tasks)
        
        self.tasks = tasks
        logger.info(f"Successfully parsed {len(tasks)} tasks with {sum(len(criteria) for criteria in tasks.values())} criteria")
        
        return tasks
    
    def _validate_task_structure(self, tasks: Dict[int, List[Dict[str, Any]]]) -> None:
        """
        Validate the parsed task structure against expected values.
        
        Args:
            tasks: Parsed tasks dictionary
        """
        # Check all expected tasks are present
        for expected_task in self.EXPECTED_TASK_POINTS.keys():
            if expected_task not in tasks:
                issue = f"Missing Task {expected_task}"
                self.issues.append(issue)
                logger.warning(issue)
        
        # Check point totals for each task
        for task_num, criteria in tasks.items():
            actual_points = sum(criterion['max_points'] for criterion in criteria)
            expected_points = self.EXPECTED_TASK_POINTS.get(task_num)
            
            if expected_points and actual_points != expected_points:
                issue = f"Task {task_num}: Expected {expected_points} points, found {actual_points}"
                self.issues.append(issue)
                logger.warning(issue)
        
        # Check total points
        total_points = sum(
            sum(criterion['max_points'] for criterion in criteria)
            for criteria in tasks.values()
        )
        
        if total_points != self.EXPECTED_TOTAL_POINTS:
            issue = f"Total points: Expected {self.EXPECTED_TOTAL_POINTS}, found {total_points}"
            self.issues.append(issue)
            logger.warning(issue)
    
    def get_task_criteria(self, task_number: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get all criteria for a specific task.
        
        Args:
            task_number: The task number (2-7)
            
        Returns:
            List of criteria dictionaries or None if task not found
        """
        if not self.tasks:
            self.parse_rubric()
        
        return self.tasks.get(task_number)
    
    def get_all_tasks(self) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get all parsed tasks and their criteria.
        
        Returns:
            Dictionary mapping task numbers to criteria lists
        """
        if not self.tasks:
            self.parse_rubric()
        
        return self.tasks.copy()
    
    def get_task_max_points(self, task_number: int) -> int:
        """
        Get maximum points for a specific task.
        
        Args:
            task_number: The task number (2-7)
            
        Returns:
            Maximum points for the task
        """
        if not self.tasks:
            self.parse_rubric()
        
        criteria = self.get_task_criteria(task_number)
        if not criteria:
            return 0
        
        return sum(criterion['max_points'] for criterion in criteria)
    
    def get_total_max_points(self) -> int:
        """
        Get total maximum points across all tasks.
        
        Returns:
            Total maximum points
        """
        if not self.tasks:
            self.parse_rubric()
        
        return sum(self.get_task_max_points(task) for task in self.tasks.keys())
    
    def get_issues(self) -> List[str]:
        """
        Get list of parsing issues encountered.
        
        Returns:
            List of issue descriptions
        """
        return self.issues.copy()
    
    def is_valid(self) -> bool:
        """
        Check if the rubric is valid (no critical issues).
        
        Returns:
            True if rubric is valid
        """
        if not self.tasks:
            self.parse_rubric()
        
        # Check for critical issues
        critical_keywords = ['Missing Task', 'Total points']
        for issue in self.issues:
            for keyword in critical_keywords:
                if keyword in issue:
                    return False
        
        return len(self.tasks) > 0
    
    def get_criterion_by_index(self, task_number: int, criterion_index: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific criterion by task and index.
        
        Args:
            task_number: The task number (2-7)
            criterion_index: Index of criterion within task (0-based)
            
        Returns:
            Criterion dictionary or None if not found
        """
        criteria = self.get_task_criteria(task_number)
        if not criteria or criterion_index >= len(criteria):
            return None
        
        return criteria[criterion_index]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the rubric parsing results.
        
        Returns:
            Dictionary with rubric statistics and issues
        """
        if not self.tasks:
            self.parse_rubric()
        
        task_summaries = {}
        for task_num, criteria in self.tasks.items():
            task_summaries[task_num] = {
                'criteria_count': len(criteria),
                'max_points': sum(c['max_points'] for c in criteria),
                'expected_points': self.EXPECTED_TASK_POINTS.get(task_num, 0)
            }
        
        return {
            'rubric_path': str(self.rubric_path),
            'total_rows': len(self.rubric_data) if self.rubric_data is not None else 0,
            'tasks_found': len(self.tasks),
            'expected_tasks': len(self.EXPECTED_TASK_POINTS),
            'total_criteria': sum(len(criteria) for criteria in self.tasks.values()),
            'total_max_points': self.get_total_max_points(),
            'expected_total_points': self.EXPECTED_TOTAL_POINTS,
            'is_valid': self.is_valid(),
            'issues_count': len(self.issues),
            'issues': self.issues,
            'task_summaries': task_summaries
        }
    
    def export_structured_rubric(self) -> Dict[str, Any]:
        """
        Export the rubric in a structured format for use by other components.
        
        Returns:
            Structured rubric data suitable for marking system
        """
        if not self.tasks:
            self.parse_rubric()
        
        structured = {
            'metadata': {
                'total_points': self.get_total_max_points(),
                'task_count': len(self.tasks),
                'is_valid': self.is_valid()
            },
            'tasks': {}
        }
        
        for task_num, criteria in self.tasks.items():
            structured['tasks'][task_num] = {
                'task_number': task_num,
                'max_points': sum(c['max_points'] for c in criteria),
                'criteria_count': len(criteria),
                'criteria': [
                    {
                        'index': idx,
                        'description': criterion['criterion'],
                        'max_points': criterion['max_points']
                    }
                    for idx, criterion in enumerate(criteria)
                ]
            }
        
        return structured
