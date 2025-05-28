"""
Excel generator for creating individual student marking sheets.

This module creates Excel files containing task-by-task marking results
with proper formatting, error flags, and summary sections.
"""

import xlsxwriter
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime

from .formatting import ExcelFormatter

logger = logging.getLogger(__name__)


class ExcelGenerationError(Exception):
    """Custom exception for Excel generation errors."""
    pass


class ExcelGenerator:
    """
    Generator for creating Excel marking sheets for individual students.
    
    Creates formatted Excel files with task sections, criteria scoring,
    subtotals, error flags, and issues summary.
    """
    
    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the Excel generator.
        
        Args:
            output_dir: Directory where Excel files will be saved
            
        Raises:
            ExcelGenerationError: If output directory is invalid
        """
        self.output_dir = Path(output_dir)
        self.formatter = ExcelFormatter()
        
        # Create output directory if it doesn't exist
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ExcelGenerationError(f"Cannot create output directory: {e}")
        
        logger.info(f"Initialized Excel generator with output dir: {self.output_dir}")
    
    def generate_marking_sheet(
        self, 
        student_id: str,
        rubric_data: Dict[int, List[Dict[str, Any]]],
        marking_results: Dict[int, List[Dict[str, Any]]],
        issues: Optional[List[str]] = None
    ) -> Path:
        """
        Generate a complete marking sheet for a student.
        
        Args:
            student_id: Unique identifier for the student
            rubric_data: Dictionary mapping task numbers to criteria lists
            marking_results: Dictionary mapping task numbers to scored criteria
            issues: List of issues encountered during marking
            
        Returns:
            Path to the generated Excel file
            
        Raises:
            ExcelGenerationError: If generation fails
        """
        output_file = self.output_dir / f"{student_id}_marks.xlsx"
        
        try:
            workbook = xlsxwriter.Workbook(str(output_file))
            worksheet = workbook.add_worksheet('Marking Sheet')
            
            # Apply general formatting
            self.formatter.apply_worksheet_formatting(worksheet, workbook)
            
            # Create format objects
            formats = self._create_formats(workbook)
            
            # Write content
            current_row = 0
            current_row = self._write_header(worksheet, formats, current_row)
            current_row = self._write_tasks(worksheet, formats, rubric_data, marking_results, current_row)
            current_row = self._write_grand_total(worksheet, formats, rubric_data, marking_results, current_row)
            
            if issues:
                current_row = self._write_issues_section(worksheet, formats, issues, current_row)
            
            workbook.close()
            
            logger.info(f"Generated marking sheet: {output_file}")
            return output_file
            
        except Exception as e:
            if 'workbook' in locals():
                try:
                    workbook.close()
                except:
                    pass
            raise ExcelGenerationError(f"Failed to generate Excel file: {e}")
    
    def _create_formats(self, workbook) -> Dict[str, Any]:
        """
        Create all format objects needed for the worksheet.
        
        Args:
            workbook: xlsxwriter workbook object
            
        Returns:
            Dictionary of format objects
        """
        return {
            'header': self.formatter.create_format(workbook, self.formatter.get_header_style()),
            'task_header': self.formatter.create_format(workbook, self.formatter.get_task_header_style()),
            'criterion': self.formatter.create_format(workbook, self.formatter.get_criterion_style()),
            'score': self.formatter.create_format(workbook, self.formatter.get_score_style()),
            'error_score': self.formatter.create_format(workbook, self.formatter.get_error_score_style()),
            'subtotal': self.formatter.create_format(workbook, self.formatter.get_subtotal_style()),
            'total': self.formatter.create_format(workbook, self.formatter.get_total_style()),
            'issues_header': self.formatter.create_format(workbook, self.formatter.get_issues_header_style()),
            'issues': self.formatter.create_format(workbook, self.formatter.get_issues_style())
        }
    
    def _write_header(self, worksheet, formats: Dict[str, Any], start_row: int) -> int:
        """
        Write the column headers.
        
        Args:
            worksheet: xlsxwriter worksheet object
            formats: Dictionary of format objects
            start_row: Starting row number
            
        Returns:
            Next available row number
        """
        headers = ['Task Name', 'Criterion Description', 'Student Score', 'Max Points']
        
        for col, header in enumerate(headers):
            worksheet.write(start_row, col, header, formats['header'])
        
        logger.debug("Wrote header row")
        return start_row + 1
    
    def _write_tasks(
        self, 
        worksheet, 
        formats: Dict[str, Any], 
        rubric_data: Dict[int, List[Dict[str, Any]]],
        marking_results: Dict[int, List[Dict[str, Any]]],
        start_row: int
    ) -> int:
        """
        Write all task sections with criteria and scores.
        
        Args:
            worksheet: xlsxwriter worksheet object
            formats: Dictionary of format objects
            rubric_data: Rubric criteria data
            marking_results: Marking scores and flags
            start_row: Starting row number
            
        Returns:
            Next available row number
        """
        current_row = start_row
        
        # Sort tasks by number
        task_numbers = sorted(rubric_data.keys())
        
        for task_num in task_numbers:
            current_row = self._write_task_section(
                worksheet, formats, task_num, 
                rubric_data[task_num], 
                marking_results.get(task_num, []),
                current_row
            )
            current_row += 1  # Add spacing between tasks
        
        return current_row
    
    def _write_task_section(
        self,
        worksheet,
        formats: Dict[str, Any],
        task_num: int,
        criteria: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        start_row: int
    ) -> int:
        """
        Write a single task section with all its criteria.
        
        Args:
            worksheet: xlsxwriter worksheet object
            formats: Dictionary of format objects
            task_num: Task number
            criteria: List of criteria for this task
            results: List of marking results for this task
            start_row: Starting row number
            
        Returns:
            Next available row number
        """
        current_row = start_row
        
        # Create results lookup for quick access
        results_lookup = {r.get('criterion_index', idx): r for idx, r in enumerate(results)}
        
        # Write each criterion
        for idx, criterion in enumerate(criteria):
            task_name = f"Task {task_num}" if idx == 0 else ""
            criterion_desc = criterion['criterion']
            max_points = criterion['max_points']
            
            # Get result for this criterion
            result = results_lookup.get(idx, {})
            score_value = result.get('score', 0)
            error_flag = result.get('error_flag')
            
            # Format score cell
            if error_flag:
                score_text = self.formatter.format_error_flag(error_flag)
                score_format = formats['error_score']
            else:
                score_text = score_value
                score_format = formats['score']
            
            # Write row
            worksheet.write(current_row, 0, task_name, formats['task_header'])
            worksheet.write(current_row, 1, criterion_desc, formats['criterion'])
            worksheet.write(current_row, 2, score_text, score_format)
            worksheet.write(current_row, 3, max_points, formats['score'])
            
            current_row += 1
        
        # Write subtotal
        current_row = self._write_subtotal(worksheet, formats, task_num, criteria, results, current_row)
        
        logger.debug(f"Wrote Task {task_num} section")
        return current_row
    
    def _write_subtotal(
        self,
        worksheet,
        formats: Dict[str, Any],
        task_num: int,
        criteria: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        row: int
    ) -> int:
        """
        Write subtotal row for a task.
        
        Args:
            worksheet: xlsxwriter worksheet object
            formats: Dictionary of format objects
            task_num: Task number
            criteria: List of criteria for this task
            results: List of marking results for this task
            row: Row number for subtotal
            
        Returns:
            Next available row number
        """
        # Calculate subtotal (only count non-error scores)
        subtotal_score = sum(
            r.get('score', 0) for r in results 
            if not r.get('error_flag')
        )
        
        # Calculate max points for task
        max_points = sum(c['max_points'] for c in criteria)
        
        # Write subtotal row
        worksheet.write(row, 0, "", formats['subtotal'])
        worksheet.write(row, 1, "SUBTOTAL", formats['subtotal'])
        worksheet.write(row, 2, subtotal_score, formats['subtotal'])
        worksheet.write(row, 3, max_points, formats['subtotal'])
        
        return row + 1
    
    def _write_grand_total(
        self,
        worksheet,
        formats: Dict[str, Any],
        rubric_data: Dict[int, List[Dict[str, Any]]],
        marking_results: Dict[int, List[Dict[str, Any]]],
        start_row: int
    ) -> int:
        """
        Write grand total row.
        
        Args:
            worksheet: xlsxwriter worksheet object
            formats: Dictionary of format objects
            rubric_data: Rubric criteria data
            marking_results: Marking scores and flags
            start_row: Starting row number
            
        Returns:
            Next available row number
        """
        # Calculate grand total
        grand_total_score = 0
        grand_total_max = 0
        
        for task_num, criteria in rubric_data.items():
            results = marking_results.get(task_num, [])
            
            # Add scores (excluding errors)
            task_score = sum(
                r.get('score', 0) for r in results 
                if not r.get('error_flag')
            )
            grand_total_score += task_score
            
            # Add max points
            task_max = sum(c['max_points'] for c in criteria)
            grand_total_max += task_max
        
        # Write grand total row
        worksheet.write(start_row, 0, "", formats['total'])
        worksheet.write(start_row, 1, "GRAND TOTAL", formats['total'])
        worksheet.write(start_row, 2, grand_total_score, formats['total'])
        worksheet.write(start_row, 3, grand_total_max, formats['total'])
        
        logger.debug(f"Wrote grand total: {grand_total_score}/{grand_total_max}")
        return start_row + 1
    
    def _write_issues_section(
        self,
        worksheet,
        formats: Dict[str, Any],
        issues: List[str],
        start_row: int
    ) -> int:
        """
        Write issues summary section.
        
        Args:
            worksheet: xlsxwriter worksheet object
            formats: Dictionary of format objects
            issues: List of issues to display
            start_row: Starting row number
            
        Returns:
            Next available row number
        """
        current_row = start_row + 1  # Add some spacing
        
        # Write issues header
        worksheet.write(current_row, 0, "ISSUES FOUND:", formats['issues_header'])
        worksheet.write(current_row, 1, "", formats['issues_header'])
        worksheet.write(current_row, 2, "", formats['issues_header'])
        worksheet.write(current_row, 3, "", formats['issues_header'])
        current_row += 1
        
        # Write each issue
        for issue in issues:
            worksheet.write(current_row, 0, "•", formats['issues'])
            worksheet.write(current_row, 1, issue, formats['issues'])
            worksheet.write(current_row, 2, "", formats['issues'])
            worksheet.write(current_row, 3, "", formats['issues'])
            current_row += 1
        
        # Add summary line
        manual_review_count = len([i for i in issues if any(
            keyword in i for keyword in ['PARSING_ERROR', 'API_ERROR', 'TIMEOUT_ERROR']
        )])
        
        if manual_review_count > 0:
            summary = f"Manual review required for {manual_review_count} items"
            worksheet.write(current_row, 0, "•", formats['issues'])
            worksheet.write(current_row, 1, summary, formats['issues'])
            worksheet.write(current_row, 2, "", formats['issues'])
            worksheet.write(current_row, 3, "", formats['issues'])
            current_row += 1
        
        logger.debug(f"Wrote issues section with {len(issues)} issues")
        return current_row
    
    def generate_batch_summary(
        self,
        batch_results: Dict[str, Dict[str, Any]],
        summary_filename: str = "batch_summary.xlsx"
    ) -> Path:
        """
        Generate a summary Excel file for batch processing results.
        
        Args:
            batch_results: Dictionary mapping student IDs to their results
            summary_filename: Name for the summary file
            
        Returns:
            Path to the generated summary file
            
        Raises:
            ExcelGenerationError: If generation fails
        """
        output_file = self.output_dir / summary_filename
        
        try:
            workbook = xlsxwriter.Workbook(str(output_file))
            worksheet = workbook.add_worksheet('Batch Summary')
            
            # Create formats
            formats = self._create_formats(workbook)
            
            # Write headers
            headers = ['Student ID', 'Total Score', 'Max Points', 'Percentage', 'Issues Count', 'Status']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, formats['header'])
            
            # Write data
            row = 1
            for student_id, result in sorted(batch_results.items()):
                total_score = result.get('total_score', 0)
                max_points = result.get('max_points', 0)
                percentage = (total_score / max_points * 100) if max_points > 0 else 0
                issues_count = len(result.get('issues', []))
                status = result.get('status', 'Unknown')
                
                worksheet.write(row, 0, student_id, formats['criterion'])
                worksheet.write(row, 1, total_score, formats['score'])
                worksheet.write(row, 2, max_points, formats['score'])
                worksheet.write(row, 3, f"{percentage:.1f}%", formats['score'])
                worksheet.write(row, 4, issues_count, formats['score'])
                worksheet.write(row, 5, status, formats['criterion'])
                
                row += 1
            
            # Set column widths
            worksheet.set_column(0, 0, 15)  # Student ID
            worksheet.set_column(1, 4, 12)  # Numeric columns
            worksheet.set_column(5, 5, 15)  # Status
            
            workbook.close()
            
            logger.info(f"Generated batch summary: {output_file}")
            return output_file
            
        except Exception as e:
            if 'workbook' in locals():
                try:
                    workbook.close()
                except:
                    pass
            raise ExcelGenerationError(f"Failed to generate batch summary: {e}")
    
    def validate_input_data(
        self,
        rubric_data: Dict[int, List[Dict[str, Any]]],
        marking_results: Dict[int, List[Dict[str, Any]]]
    ) -> List[str]:
        """
        Validate input data for consistency and completeness.
        
        Args:
            rubric_data: Dictionary mapping task numbers to criteria lists
            marking_results: Dictionary mapping task numbers to scored criteria
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Check that all rubric tasks have corresponding results
        for task_num, criteria in rubric_data.items():
            results = marking_results.get(task_num, [])
            
            if not results:
                issues.append(f"No results found for Task {task_num}")
                continue
            
            # Check criteria count matches
            if len(results) != len(criteria):
                issues.append(
                    f"Task {task_num}: Expected {len(criteria)} results, got {len(results)}"
                )
        
        # Check for extra results not in rubric
        for task_num in marking_results:
            if task_num not in rubric_data:
                issues.append(f"Results found for unknown Task {task_num}")
        
        return issues
    
    def get_output_path(self, student_id: str) -> Path:
        """
        Get the expected output path for a student's marking sheet.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Expected file path
        """
        return self.output_dir / f"{student_id}_marks.xlsx"
