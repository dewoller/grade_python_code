"""
Main fixture generator entry point.

This module coordinates the creation of all test fixtures including:
- Jupyter notebooks with various scenarios
- Rubric CSV files
- Mock API responses
- Expected Excel outputs

All fixtures are generated programmatically for consistent testing.
"""

from pathlib import Path
from .notebook_generator import NotebookFixtureGenerator
from .rubric_generator import RubricFixtureGenerator
from .api_mock_generator import APIResponseGenerator
from .excel_mock_generator import ExcelMockGenerator


class FixtureCoordinator:
    """Coordinates creation of all test fixtures."""
    
    def __init__(self, fixtures_dir: str = "tests/fixtures"):
        self.fixtures_dir = Path(fixtures_dir)
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        self.notebook_gen = NotebookFixtureGenerator(fixtures_dir)
        self.rubric_gen = RubricFixtureGenerator(fixtures_dir)
        self.api_gen = APIResponseGenerator(fixtures_dir)
        self.excel_gen = ExcelMockGenerator(fixtures_dir)
    
    def generate_all_fixtures(self):
        """Generate all test fixtures."""
        print("Generating test fixtures...")
        
        # Generate notebooks
        print("  Creating notebook fixtures...")
        self.notebook_gen.generate_all_notebooks()
        
        # Generate rubrics
        print("  Creating rubric fixtures...")
        self.rubric_gen.generate_all_rubrics()
        
        # Generate API mocks
        print("  Creating API mock responses...")
        self.api_gen.generate_all_responses()
        
        # Generate Excel mocks
        print("  Creating Excel mock outputs...")
        self.excel_gen.generate_all_excel_fixtures()
        
        print("All fixtures generated successfully!")
    
    def clean_fixtures(self):
        """Remove all generated fixtures."""
        import shutil
        if self.fixtures_dir.exists():
            shutil.rmtree(self.fixtures_dir)
        print("All fixtures cleaned up!")


def main():
    """Generate all fixtures when run as script."""
    coordinator = FixtureCoordinator()
    coordinator.generate_all_fixtures()


if __name__ == "__main__":
    main()
