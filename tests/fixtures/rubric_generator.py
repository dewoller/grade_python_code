"""
Rubric fixture generator for creating test CSV files.

This module creates realistic rubric CSV files with:
- Standard valid rubric matching project requirements
- Invalid rubrics with various errors
- Edge cases for testing parsing logic

All rubrics follow the expected format from the project brief.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any


class RubricFixtureGenerator:
    """Generate rubric CSV fixtures for testing."""
    
    def __init__(self, fixtures_dir: str = "tests/fixtures"):
        self.fixtures_dir = Path(fixtures_dir)
        self.rubrics_dir = self.fixtures_dir / "rubrics"
        self.rubrics_dir.mkdir(parents=True, exist_ok=True)
    
    def create_standard_rubric_data(self) -> List[List[str]]:
        """Create standard rubric data matching project requirements."""
        rubric_data = [
            ["Task Name", "Criterion Description", "Score", "Max Points"],
            
            # Task 2: 8 points (5 criteria)
            ["Task 2", "Data loading implementation", "", "2"],
            ["Task 2", "Data cleaning functionality", "", "2"],
            ["Task 2", "Statistical analysis correctness", "", "2"],
            ["Task 2", "Code organization and structure", "", "1"],
            ["Task 2", "Documentation and comments", "", "1"],
            
            # Task 3: 10 points (6 criteria)
            ["Task 3", "Histogram creation and formatting", "", "2"],
            ["Task 3", "Scatter plot implementation", "", "2"],
            ["Task 3", "Plot customization and labels", "", "2"],
            ["Task 3", "Data visualization best practices", "", "2"],
            ["Task 3", "Code quality and efficiency", "", "1"],
            ["Task 3", "Error handling for plots", "", "1"],
            
            # Task 4: 15 points (7 criteria)
            ["Task 4", "Data preprocessing implementation", "", "3"],
            ["Task 4", "Feature scaling correctness", "", "2"],
            ["Task 4", "Clustering algorithm application", "", "3"],
            ["Task 4", "Parameter selection and tuning", "", "2"],
            ["Task 4", "Results interpretation", "", "2"],
            ["Task 4", "Code modularity and reusability", "", "2"],
            ["Task 4", "Documentation and testing", "", "1"],
            
            # Task 5: 15 points (7 criteria)
            ["Task 5", "Correlation analysis implementation", "", "3"],
            ["Task 5", "Statistical test selection", "", "2"],
            ["Task 5", "Hypothesis testing correctness", "", "3"],
            ["Task 5", "Results interpretation and significance", "", "2"],
            ["Task 5", "Statistical assumptions validation", "", "2"],
            ["Task 5", "Code efficiency and clarity", "", "2"],
            ["Task 5", "Documentation and explanations", "", "1"],
            
            # Task 6: 15 points (6 criteria)
            ["Task 6", "Model selection and implementation", "", "3"],
            ["Task 6", "Cross-validation methodology", "", "3"],
            ["Task 6", "Performance metrics calculation", "", "3"],
            ["Task 6", "Model evaluation and comparison", "", "3"],
            ["Task 6", "Code organization and testing", "", "2"],
            ["Task 6", "Documentation and interpretation", "", "1"],
            
            # Task 7: 20 points (5 criteria)
            ["Task 7", "Comprehensive report generation", "", "5"],
            ["Task 7", "Data visualization integration", "", "4"],
            ["Task 7", "Statistical summary and insights", "", "4"],
            ["Task 7", "Conclusions and recommendations", "", "4"],
            ["Task 7", "Professional presentation quality", "", "3"]
        ]
        
        return rubric_data
    
    def create_invalid_rubric_data(self) -> List[List[str]]:
        """Create invalid rubric for testing error handling."""
        return [
            ["Task Name", "Criterion", "Score"],  # Missing Max Points column
            ["Task 2", "Basic implementation", "", "invalid_points"],  # Invalid points
            ["Task 3", "Visualization", "", ""],  # Empty points
            ["Invalid Task", "Some criterion", "", "2"],  # Invalid task name
            ["Task 4", "", "", "3"],  # Empty criterion
        ]
    
    def create_empty_rubric_data(self) -> List[List[str]]:
        """Create empty rubric for testing."""
        return [
            ["Task Name", "Criterion Description", "Score", "Max Points"]
        ]
    
    def create_missing_columns_rubric_data(self) -> List[List[str]]:
        """Create rubric with missing required columns."""
        return [
            ["Task", "Description"],  # Missing Score and Max Points
            ["Task 2", "Some criterion"],
            ["Task 3", "Another criterion"]
        ]
    
    def create_duplicate_tasks_rubric_data(self) -> List[List[str]]:
        """Create rubric with duplicate task entries for testing."""
        return [
            ["Task Name", "Criterion Description", "Score", "Max Points"],
            ["Task 2", "First criterion", "", "2"],
            ["Task 2", "Second criterion", "", "2"],
            ["Task 2", "Third criterion", "", "2"],  # Same task repeated
            ["Task 2", "Fourth criterion", "", "2"],
            ["Task 3", "Visualization criterion", "", "3"]
        ]
    
    def create_wrong_total_points_rubric_data(self) -> List[List[str]]:
        """Create rubric with wrong total points (not 83)."""
        return [
            ["Task Name", "Criterion Description", "Score", "Max Points"],
            ["Task 2", "Basic implementation", "", "10"],  # Too many points
            ["Task 3", "Visualization", "", "10"],
            ["Task 4", "Processing", "", "10"],
            ["Task 5", "Analysis", "", "10"],
            ["Task 6", "Modeling", "", "10"],
            ["Task 7", "Reporting", "", "10"]  # Total = 60, not 83
        ]
    
    def create_special_chars_rubric_data(self) -> List[List[str]]:
        """Create rubric with special characters for testing."""
        return [
            ["Task Name", "Criterion Description", "Score", "Max Points"],
            ["Task 2", "Données manipulation — áéíóú 🎉", "", "2"],
            ["Task 3", "Visualisation avec caractères spéciaux", "", "3"],
            ["Task 4", "Traitement avancé (μ, σ, ±)", "", "3"],
            ["Task 5", "Analyse statistique — 中文 test", "", "2"],
            ["Task 6", "Modélisation ML ⚡", "", "3"],
            ["Task 7", "Rapport final 📊", "", "2"]
        ]
    
    def save_rubric_csv(self, data: List[List[str]], filename: str):
        """Save rubric data to CSV file."""
        filepath = self.rubrics_dir / f"{filename}.csv"
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)
    
    def create_malformed_csv_file(self, filename: str):
        """Create malformed CSV file for testing."""
        filepath = self.rubrics_dir / f"{filename}.csv"
        with open(filepath, 'w') as f:
            f.write('Task Name,Criterion,Score,Max Points\n')
            f.write('Task 2,"Unclosed quote,3\n')  # Malformed CSV
            f.write('Task 3,Normal criterion,2\n')
            f.write('Task 4,Another "quote problem,4\n')
    
    def generate_all_rubrics(self):
        """Generate all rubric fixtures."""
        # Standard valid rubric
        standard_data = self.create_standard_rubric_data()
        self.save_rubric_csv(standard_data, "standard_rubric")
        
        # Invalid rubrics
        invalid_data = self.create_invalid_rubric_data()
        self.save_rubric_csv(invalid_data, "invalid_rubric")
        
        # Empty rubric
        empty_data = self.create_empty_rubric_data()
        self.save_rubric_csv(empty_data, "empty_rubric")
        
        # Missing columns
        missing_cols_data = self.create_missing_columns_rubric_data()
        self.save_rubric_csv(missing_cols_data, "missing_columns_rubric")
        
        # Duplicate tasks
        duplicate_data = self.create_duplicate_tasks_rubric_data()
        self.save_rubric_csv(duplicate_data, "duplicate_tasks_rubric")
        
        # Wrong total points
        wrong_total_data = self.create_wrong_total_points_rubric_data()
        self.save_rubric_csv(wrong_total_data, "wrong_total_points_rubric")
        
        # Special characters
        special_chars_data = self.create_special_chars_rubric_data()
        self.save_rubric_csv(special_chars_data, "special_chars_rubric")
        
        # Malformed CSV
        self.create_malformed_csv_file("malformed_rubric")
