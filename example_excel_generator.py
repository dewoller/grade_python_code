#!/usr/bin/env python3
"""
Example usage of the Excel output generator.

This script demonstrates how to use the ExcelGenerator to create 
student marking sheets with proper formatting and error handling.
"""

import sys
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.output.excel_generator import ExcelGenerator
from src.parsers.rubric_parser import RubricParser


def create_sample_data():
    """Create sample data for demonstration."""
    
    # Sample rubric data (would normally come from RubricParser)
    rubric_data = {
        2: [
            {'criterion': 'Joins list elements from payload to make a single string', 'max_points': 2},
            {'criterion': 'Converts the message to lowercase', 'max_points': 2},
            {'criterion': 'Correctly displays output by calling the bot_say() function', 'max_points': 2},
            {'criterion': 'Includes an additional test call to bot_shout() with different argument', 'max_points': 2},
        ],
        3: [
            {'criterion': 'Uses data from the payload to determine the numbers needed for multiplication', 'max_points': 3},
            {'criterion': 'Performs multiplication using an appropriate expression', 'max_points': 1},
            {'criterion': 'Converts elements in the payload to an appropriate type', 'max_points': 2},
            {'criterion': 'Displays the result as an equation using the bot_say() function', 'max_points': 2},
            {'criterion': 'Displays both numbers exactly as the user typed them (same order), answer to 4 decimal places', 'max_points': 2},
        ],
        4: [
            {'criterion': 'Correct function definition (def, function name, parameters)', 'max_points': 2},
            {'criterion': 'Converts elements in the payload to an appropriate type', 'max_points': 2},
            {'criterion': 'Uses a loop to repeatedly call bot_say()', 'max_points': 2},
            {'criterion': 'The loop repeats the correct number of times', 'max_points': 2},
            {'criterion': 'The correct numbers are displayed, with one number per chatbot message', 'max_points': 2},
            {'criterion': 'The bot aggregates the sum and displays the total sum after counting', 'max_points': 3},
            {'criterion': 'The bot correctly counts up from one when only a single value is provided', 'max_points': 2},
        ]
    }
    
    # Sample marking results with various scores and error flags
    marking_results = {
        2: [
            {'score': 2, 'criterion_index': 0},  # Full marks
            {'score': 2, 'criterion_index': 1},  # Full marks
            {'score': 1, 'criterion_index': 2},  # Partial marks
            {'score': 0, 'error_flag': 'INCOMPLETE_CODE', 'criterion_index': 3},  # Error
        ],
        3: [
            {'score': 3, 'criterion_index': 0},  # Full marks
            {'score': 1, 'criterion_index': 1},  # Full marks
            {'score': 2, 'criterion_index': 2},  # Full marks
            {'score': 0, 'error_flag': 'PARSING_ERROR', 'criterion_index': 3},  # Error
            {'score': 2, 'criterion_index': 4},  # Full marks
        ],
        4: [
            {'score': 0, 'error_flag': 'MISSING_TASK', 'criterion_index': 0},  # Task not found
            {'score': 0, 'error_flag': 'MISSING_TASK', 'criterion_index': 1},
            {'score': 0, 'error_flag': 'MISSING_TASK', 'criterion_index': 2},
            {'score': 0, 'error_flag': 'MISSING_TASK', 'criterion_index': 3},
            {'score': 0, 'error_flag': 'MISSING_TASK', 'criterion_index': 4},
            {'score': 0, 'error_flag': 'MISSING_TASK', 'criterion_index': 5},
            {'score': 0, 'error_flag': 'MISSING_TASK', 'criterion_index': 6},
        ]
    }
    
    # Sample issues that occurred during marking
    issues = [
        "Task 2 Criterion 4: INCOMPLETE_CODE - Only placeholder code found",
        "Task 3 Criterion 4: PARSING_ERROR - AI evaluation failed after 3 retries",
        "Task 4: MISSING_TASK - No solution found in notebook",
        "Manual review required for 3 items"
    ]
    
    return rubric_data, marking_results, issues


def demonstrate_excel_generation():
    """Demonstrate Excel generation with sample data."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create output directory
        output_dir = Path("example_output")
        output_dir.mkdir(exist_ok=True)
        
        # Initialize generator
        generator = ExcelGenerator(output_dir)
        logger.info(f"Created Excel generator with output directory: {output_dir}")
        
        # Get sample data
        rubric_data, marking_results, issues = create_sample_data()
        
        # Validate input data
        validation_issues = generator.validate_input_data(rubric_data, marking_results)
        if validation_issues:
            logger.warning(f"Validation issues found: {validation_issues}")
        else:
            logger.info("Input data validation passed")
        
        # Generate marking sheet for a sample student
        student_id = "EXAMPLE_001"
        logger.info(f"Generating marking sheet for student: {student_id}")
        
        output_file = generator.generate_marking_sheet(
            student_id=student_id,
            rubric_data=rubric_data,
            marking_results=marking_results,
            issues=issues
        )
        
        logger.info(f"Successfully generated marking sheet: {output_file}")
        
        # Calculate and display summary
        total_score = sum(
            sum(r.get('score', 0) for r in results if not r.get('error_flag'))
            for results in marking_results.values()
        )
        
        total_max = sum(
            sum(c['max_points'] for c in criteria)
            for criteria in rubric_data.values()
        )
        
        percentage = (total_score / total_max * 100) if total_max > 0 else 0
        
        print(f"\n=== MARKING SUMMARY ===")
        print(f"Student ID: {student_id}")
        print(f"Total Score: {total_score}/{total_max} ({percentage:.1f}%)")
        print(f"Issues Found: {len(issues)}")
        print(f"Output File: {output_file}")
        print(f"File Size: {output_file.stat().st_size:,} bytes")
        
        # Generate batch summary example
        batch_results = {
            "EXAMPLE_001": {
                "total_score": total_score,
                "max_points": total_max,
                "issues": issues,
                "status": "Completed with issues"
            },
            "EXAMPLE_002": {
                "total_score": 75,
                "max_points": total_max,
                "issues": [],
                "status": "Completed"
            },
            "EXAMPLE_003": {
                "total_score": 45,
                "max_points": total_max,
                "issues": ["Task 7: MISSING_TASK"],
                "status": "Incomplete"
            }
        }
        
        summary_file = generator.generate_batch_summary(batch_results)
        logger.info(f"Generated batch summary: {summary_file}")
        
        print(f"Batch Summary: {summary_file}")
        print(f"\nFiles created in: {output_dir.absolute()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during Excel generation: {e}")
        return False


def demonstrate_with_real_rubric():
    """Demonstrate using real rubric file if available."""
    
    rubric_path = Path("data/2025_specs/2025_S1_Marking_Sheet_edited.csv")
    
    if not rubric_path.exists():
        print(f"Real rubric file not found at: {rubric_path}")
        return False
    
    try:
        # Parse real rubric
        parser = RubricParser(str(rubric_path))
        rubric_data = parser.parse_rubric()
        
        print(f"\n=== REAL RUBRIC DEMO ===")
        print(f"Loaded rubric with {len(rubric_data)} tasks")
        
        # Create realistic results with some errors
        marking_results = {}
        issues = []
        
        for task_num, criteria in rubric_data.items():
            task_results = []
            for idx, criterion in enumerate(criteria):
                # Simulate realistic scoring patterns
                if task_num == 4:  # Simulate missing task
                    task_results.append({
                        'score': 0,
                        'error_flag': 'MISSING_TASK',
                        'criterion_index': idx
                    })
                    if idx == 0:  # Only add issue once per task
                        issues.append(f"Task {task_num}: MISSING_TASK")
                elif idx % 5 == 0:  # Simulate occasional parsing errors
                    task_results.append({
                        'score': 0,
                        'error_flag': 'PARSING_ERROR',
                        'criterion_index': idx
                    })
                    issues.append(f"Task {task_num} Criterion {idx+1}: PARSING_ERROR")
                else:
                    # Random but realistic score
                    max_points = criterion['max_points']
                    score = min(max_points, max(0, max_points - (idx % 3)))
                    task_results.append({
                        'score': score,
                        'criterion_index': idx
                    })
            
            marking_results[task_num] = task_results
        
        # Generate with real data
        output_dir = Path("example_output")
        generator = ExcelGenerator(output_dir)
        
        output_file = generator.generate_marking_sheet(
            student_id="REAL_RUBRIC_001",
            rubric_data=rubric_data,
            marking_results=marking_results,
            issues=issues
        )
        
        print(f"Generated real rubric example: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error with real rubric demo: {e}")
        return False


def main():
    """Main function to run demonstrations."""
    
    print("Excel Generator Demonstration")
    print("=" * 40)
    
    # Run basic demonstration
    print("\n1. Basic Excel Generation Demo")
    success1 = demonstrate_excel_generation()
    
    # Run real rubric demonstration if available
    print("\n2. Real Rubric Demo")
    success2 = demonstrate_with_real_rubric()
    
    # Summary
    print(f"\n=== DEMONSTRATION SUMMARY ===")
    print(f"Basic Demo: {'✓ Success' if success1 else '✗ Failed'}")
    print(f"Real Rubric Demo: {'✓ Success' if success2 else '✗ Failed'}")
    
    if success1 or success2:
        print(f"\nCheck the 'example_output' directory for generated Excel files.")
        print(f"Files can be opened in Excel, LibreOffice Calc, or Google Sheets.")
    
    return success1 or success2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
