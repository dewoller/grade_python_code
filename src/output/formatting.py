"""
Excel formatting utilities for student marking sheets.

This module provides formatting functions and styles for creating
professional-looking Excel marking sheets with consistent styling.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExcelFormatter:
    """
    Provides formatting utilities for Excel worksheets.
    
    This class contains style definitions and formatting methods
    for creating consistent, professional-looking marking sheets.
    """
    
    @staticmethod
    def get_header_style() -> Dict[str, Any]:
        """
        Get the style for header rows.
        
        Returns:
            Dictionary with style properties for headers
        """
        return {
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        }
    
    @staticmethod
    def get_task_header_style() -> Dict[str, Any]:
        """
        Get the style for task section headers.
        
        Returns:
            Dictionary with style properties for task headers
        """
        return {
            'bold': True,
            'bg_color': '#D9E2F3',
            'font_color': 'black',
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        }
    
    @staticmethod
    def get_criterion_style() -> Dict[str, Any]:
        """
        Get the style for criterion rows.
        
        Returns:
            Dictionary with style properties for criteria
        """
        return {
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True
        }
    
    @staticmethod
    def get_score_style() -> Dict[str, Any]:
        """
        Get the style for score cells.
        
        Returns:
            Dictionary with style properties for scores
        """
        return {
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0'
        }
    
    @staticmethod
    def get_error_score_style() -> Dict[str, Any]:
        """
        Get the style for error score cells.
        
        Returns:
            Dictionary with style properties for error scores
        """
        return {
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FFE6E6',
            'font_color': '#D00000'
        }
    
    @staticmethod
    def get_subtotal_style() -> Dict[str, Any]:
        """
        Get the style for subtotal rows.
        
        Returns:
            Dictionary with style properties for subtotals
        """
        return {
            'bold': True,
            'bg_color': '#F2F2F2',
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '0'
        }
    
    @staticmethod
    def get_total_style() -> Dict[str, Any]:
        """
        Get the style for grand total row.
        
        Returns:
            Dictionary with style properties for grand total
        """
        return {
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 2,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '0'
        }
    
    @staticmethod
    def get_issues_header_style() -> Dict[str, Any]:
        """
        Get the style for issues section header.
        
        Returns:
            Dictionary with style properties for issues header
        """
        return {
            'bold': True,
            'bg_color': '#FFD966',
            'font_color': 'black',
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        }
    
    @staticmethod
    def get_issues_style() -> Dict[str, Any]:
        """
        Get the style for issues text.
        
        Returns:
            Dictionary with style properties for issues
        """
        return {
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True,
            'bg_color': '#FFF9E6'
        }
    
    @staticmethod
    def get_column_widths() -> Dict[str, float]:
        """
        Get recommended column widths for the marking sheet.
        
        Returns:
            Dictionary mapping column letters to widths
        """
        return {
            'A': 12,   # Task Name
            'B': 60,   # Criterion Description  
            'C': 15,   # Student Score
            'D': 12    # Max Points
        }
    
    @staticmethod
    def apply_worksheet_formatting(worksheet, workbook) -> None:
        """
        Apply general formatting to the worksheet.
        
        Args:
            worksheet: The xlsxwriter worksheet object
            workbook: The xlsxwriter workbook object
        """
        # Set column widths
        column_widths = ExcelFormatter.get_column_widths()
        for col_letter, width in column_widths.items():
            col_index = ord(col_letter) - ord('A')
            worksheet.set_column(col_index, col_index, width)
        
        # Freeze the header row
        worksheet.freeze_panes(1, 0)
        
        # Set default row height
        worksheet.set_default_row(15)
        
        logger.debug("Applied general worksheet formatting")
    
    @staticmethod
    def create_format(workbook, style_dict: Dict[str, Any]):
        """
        Create an xlsxwriter format object from a style dictionary.
        
        Args:
            workbook: The xlsxwriter workbook object
            style_dict: Dictionary with style properties
            
        Returns:
            xlsxwriter format object
        """
        format_obj = workbook.add_format()
        
        # Apply each style property
        for prop, value in style_dict.items():
            if hasattr(format_obj, f'set_{prop}'):
                getattr(format_obj, f'set_{prop}')(value)
        
        return format_obj
    
    @staticmethod
    def format_error_flag(error_type: str) -> str:
        """
        Format an error flag for display in score cells.
        
        Args:
            error_type: Type of error (MISSING_TASK, INCOMPLETE_CODE, PARSING_ERROR)
            
        Returns:
            Formatted error string
        """
        return f"0 ({error_type})"
    
    @staticmethod
    def get_error_types() -> Dict[str, str]:
        """
        Get available error types and their descriptions.
        
        Returns:
            Dictionary mapping error codes to descriptions
        """
        return {
            'MISSING_TASK': 'Task not found in student notebook',
            'INCOMPLETE_CODE': 'Only placeholder code provided',
            'PARSING_ERROR': 'AI processing failed for this criterion',
            'API_ERROR': 'Unable to evaluate due to API issues',
            'TIMEOUT_ERROR': 'Evaluation timed out'
        }
