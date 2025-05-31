"""
Jupyter Notebook Parser for extracting programming tasks from student assignments.

This module parses Jupyter notebooks to extract student solutions for each task.
It handles both standard "#### Your Solution" and alternative "# Your Solution:" markers.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class NotebookParsingError(Exception):
    """Custom exception for notebook parsing errors."""
    pass


class NotebookParser:
    """
    Parser for extracting programming tasks from Jupyter notebooks.
    
    The parser identifies task solution markers and extracts the associated code
    from subsequent cells. It supports both primary and secondary marker formats
    and provides comprehensive error handling.
    """
    
    # Standard solution markers found in notebooks
    PRIMARY_MARKER = "#### Your Solution"
    SECONDARY_MARKER = "# Your Solution:"
    
    # Expected number of tasks per assignment
    EXPECTED_TASK_COUNT = 6
    
    def __init__(self, notebook_path: str):
        """
        Initialize the parser with a notebook file path.
        
        Args:
            notebook_path: Path to the Jupyter notebook file
            
        Raises:
            NotebookParsingError: If file doesn't exist or can't be read
        """
        self.notebook_path = Path(notebook_path)
        self.notebook_data = None
        self.tasks = {}
        self.issues = []
        
        if not self.notebook_path.exists():
            raise NotebookParsingError(f"Notebook file not found: {notebook_path}")
        
        self._load_notebook()
    
    def _load_notebook(self) -> None:
        """
        Load and parse the JSON notebook file.
        
        Raises:
            NotebookParsingError: If JSON is corrupted or invalid
        """
        try:
            with open(self.notebook_path, 'r', encoding='utf-8') as f:
                self.notebook_data = json.load(f)
            
            # Validate basic notebook structure
            if not isinstance(self.notebook_data, dict):
                raise NotebookParsingError("Invalid notebook format: not a JSON object")
            
            if 'cells' not in self.notebook_data:
                raise NotebookParsingError("Invalid notebook format: missing 'cells' key")
            
            if not isinstance(self.notebook_data['cells'], list):
                raise NotebookParsingError("Invalid notebook format: 'cells' is not a list")
                
            logger.info(f"Successfully loaded notebook with {len(self.notebook_data['cells'])} cells")
            
        except json.JSONDecodeError as e:
            raise NotebookParsingError(f"Corrupted JSON in notebook: {e}")
        except Exception as e:
            raise NotebookParsingError(f"Error loading notebook: {e}")
    
    def _is_solution_marker(self, cell_source: str) -> bool:
        """
        Check if a cell contains a solution marker.
        
        Args:
            cell_source: The source text of a cell
            
        Returns:
            True if cell contains either primary or secondary marker
        """
        return (self.PRIMARY_MARKER in cell_source or 
                self.SECONDARY_MARKER in cell_source)
    
    def _extract_code_from_cell(self, cell: Dict[str, Any]) -> str:
        """
        Extract code content from a notebook cell.
        
        Args:
            cell: A notebook cell dictionary
            
        Returns:
            The code content as a string
        """
        if cell.get('cell_type') != 'code':
            return ""
        
        source = cell.get('source', [])
        if isinstance(source, list):
            return ''.join(source).strip()
        elif isinstance(source, str):
            return source.strip()
        else:
            return ""
    
    def _identify_task_number(self, task_index: int, code_content: str) -> int:
        """
        Identify the task number based on its position and code content.
        
        Since tasks are numbered 2-7, we map the sequential position to task numbers.
        We also try to identify tasks by their bot function names.
        
        Args:
            task_index: The sequential index of the task (0-based)
            code_content: The code content to analyze
            
        Returns:
            The task number (2-7)
        """
        # Map sequential task index to actual task numbers (2-7)
        task_number = task_index + 2
        
        # Use sequential mapping as primary method since notebooks are ordered
        # Only use function identification as validation/debugging
        if task_number <= 7:
            # Add validation by checking for expected function
            expected_functions = {
                2: 'bot_whisper',
                3: 'bot_multiply', 
                4: 'bot_count',
                5: 'bot_topic',
                6: 'dispatch_bot_command', 
                7: 'chatbot_interaction'
            }
            
            expected_func = expected_functions.get(task_number)
            if expected_func and f'def {expected_func}(' in code_content:
                logger.debug(f"Sequential mapping validated: task_index {task_index} -> task {task_number} (found {expected_func})")
            else:
                logger.debug(f"Sequential mapping: task_index {task_index} -> task {task_number} (expected {expected_func})")
            
            return task_number
        else:
            logger.warning(f"Task index {task_index} exceeds expected range, using fallback")
            return min(task_number, 7)
    
    def _validate_code_content(self, code_content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that code content is not empty or placeholder.
        
        Args:
            code_content: The code to validate
            
        Returns:
            Tuple of (is_valid, issue_description)
        """
        if not code_content.strip():
            return False, "EMPTY_CODE"
        
        # Check for common placeholder patterns
        placeholder_patterns = [
            r'^\s*#.*your.*solution.*here.*$',
            r'^\s*pass\s*$',
            r'^\s*\.\.\.\s*$',
            r'^\s*#\s*TODO\s*$'
        ]
        
        lines = [line.strip() for line in code_content.split('\n') if line.strip()]
        
        # If only placeholder content
        if len(lines) <= 2:
            for pattern in placeholder_patterns:
                if any(re.match(pattern, line, re.IGNORECASE) for line in lines):
                    return False, "PLACEHOLDER_CODE"
        
        return True, None
    
    def parse_tasks(self) -> Dict[int, str]:
        """
        Parse the notebook and extract all task solutions.
        
        Returns:
            Dictionary mapping task numbers (2-7) to code content
            
        Raises:
            NotebookParsingError: If parsing fails
        """
        if not self.notebook_data:
            raise NotebookParsingError("Notebook not loaded")
        
        cells = self.notebook_data['cells']
        task_index = 0
        found_tasks = {}
        
        logger.info(f"Parsing notebook with {len(cells)} cells")
        
        for i, cell in enumerate(cells):
            # Skip non-markdown cells for markers
            if cell.get('cell_type') != 'markdown':
                continue
            
            # Check if this cell contains a solution marker
            source = cell.get('source', [])
            if isinstance(source, list):
                cell_text = ''.join(source)
            else:
                cell_text = str(source)
            
            if not self._is_solution_marker(cell_text):
                continue
            
            logger.debug(f"Found solution marker in cell {i}")
            
            # Look for the next code cell
            code_content = ""
            code_cell_found = False
            
            for j in range(i + 1, min(i + 3, len(cells))):  # Look ahead up to 2 cells
                next_cell = cells[j]
                if next_cell.get('cell_type') == 'code':
                    code_content = self._extract_code_from_cell(next_cell)
                    code_cell_found = True
                    logger.debug(f"Found code in cell {j} with {len(code_content)} characters")
                    break
            
            if not code_cell_found:
                issue = f"No code cell found after solution marker in cell {i}"
                self.issues.append(issue)
                logger.warning(issue)
                continue
            
            # Determine task number
            task_number = self._identify_task_number(task_index, code_content)
            logger.debug(f"Task {task_index} assigned to task number {task_number}")
            
            # Check for duplicate task numbers
            if task_number in found_tasks:
                logger.warning(f"Duplicate task number {task_number} found - overwriting previous")
            
            # Validate code content
            is_valid, issue = self._validate_code_content(code_content)
            if not is_valid:
                self.issues.append(f"Task {task_number}: {issue}")
                logger.warning(f"Task {task_number} has issue: {issue}")
            
            found_tasks[task_number] = code_content
            task_index += 1
        
        # Validate expected task count
        if len(found_tasks) < self.EXPECTED_TASK_COUNT:
            issue = f"Expected {self.EXPECTED_TASK_COUNT} tasks, found {len(found_tasks)}"
            self.issues.append(issue)
            logger.warning(issue)
        
        # Ensure all expected tasks are present (2-7)
        for expected_task in range(2, 8):
            if expected_task not in found_tasks:
                found_tasks[expected_task] = ""
                self.issues.append(f"Task {expected_task}: MISSING_TASK")
                logger.warning(f"Task {expected_task} is missing")
        
        # Sort the found tasks to ensure consistent ordering
        found_tasks = dict(sorted(found_tasks.items()))
        
        self.tasks = found_tasks
        logger.info(f"Successfully parsed {len([t for t in found_tasks.values() if t])} tasks with code")
        
        return found_tasks
    
    def get_task_code(self, task_number: int) -> Optional[str]:
        """
        Get the code for a specific task number.
        
        Args:
            task_number: The task number (2-7)
            
        Returns:
            The code content or None if task not found
        """
        if not self.tasks:
            self.parse_tasks()
        
        return self.tasks.get(task_number)
    
    def get_all_tasks(self) -> Dict[int, str]:
        """
        Get all parsed tasks.
        
        Returns:
            Dictionary mapping task numbers to code content
        """
        if not self.tasks:
            self.parse_tasks()
        
        return self.tasks.copy()
    
    def get_issues(self) -> List[str]:
        """
        Get list of parsing issues encountered.
        
        Returns:
            List of issue descriptions
        """
        return self.issues.copy()
    
    def has_all_tasks(self) -> bool:
        """
        Check if all expected tasks are present and have code.
        
        Returns:
            True if all 6 tasks (2-7) have non-empty code
        """
        if not self.tasks:
            self.parse_tasks()
        
        for task_num in range(2, 8):
            if task_num not in self.tasks or not self.tasks[task_num].strip():
                return False
        
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the parsing results.
        
        Returns:
            Dictionary with parsing statistics and issues
        """
        if not self.tasks:
            self.parse_tasks()
        
        tasks_with_code = sum(1 for code in self.tasks.values() if code.strip())
        
        return {
            'notebook_path': str(self.notebook_path),
            'total_cells': len(self.notebook_data['cells']) if self.notebook_data else 0,
            'tasks_found': tasks_with_code,  # Number of tasks with actual code
            'tasks_with_code': tasks_with_code,
            'expected_tasks': self.EXPECTED_TASK_COUNT,
            'all_tasks_present': self.has_all_tasks(),
            'issues_count': len(self.issues),
            'issues': self.issues
        }
