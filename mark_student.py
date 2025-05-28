#!/usr/bin/env python3
"""
Main entry point for the student marking CLI tool.

This script provides a command-line interface for marking programming assignments
from Jupyter notebooks using AI-powered evaluation against rubric criteria.

Usage:
    python mark_student.py --notebook path/to/notebook.ipynb --rubric path/to/rubric.csv
    
Example:
    python mark_student.py -n data/001.ipynb -r data/rubric.csv -o output/
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.main import cli


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
