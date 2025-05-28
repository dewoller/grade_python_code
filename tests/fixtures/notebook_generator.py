"""
Notebook fixture generator for creating test Jupyter notebooks.

This module creates realistic Jupyter notebook fixtures with:
- Perfect student solutions
- Missing tasks
- Syntax errors
- Empty notebooks
- Special characters
- Corrupted files

All notebooks match the expected format from the project brief.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from .code_templates import CodeTemplateProvider


class NotebookFixtureGenerator:
    """Generate Jupyter notebook fixtures for testing."""
    
    TASK_NUMBERS = [2, 3, 4, 5, 6, 7]
    PRIMARY_MARKER = "#### Your Solution"
    SECONDARY_MARKER = "# Your Solution:"
    
    def __init__(self, fixtures_dir: str = "tests/fixtures"):
        self.fixtures_dir = Path(fixtures_dir)
        self.notebooks_dir = self.fixtures_dir / "notebooks"
        self.notebooks_dir.mkdir(parents=True, exist_ok=True)
        
        self.code_provider = CodeTemplateProvider()
    
    def create_basic_notebook_structure(self) -> Dict[str, Any]:
        """Create basic Jupyter notebook structure."""
        return {
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
    
    def create_markdown_cell(self, content: str) -> Dict[str, Any]:
        """Create a markdown cell."""
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [content]
        }
    
    def create_code_cell(self, code: str, executed: bool = True) -> Dict[str, Any]:
        """Create a code cell."""
        return {
            "cell_type": "code",
            "execution_count": 1 if executed else None,
            "metadata": {},
            "outputs": [],
            "source": [code]
        }
    
    def create_perfect_student_notebook(self) -> Dict[str, Any]:
        """Create notebook for perfect student with all tasks complete."""
        notebook = self.create_basic_notebook_structure()
        
        # Add introduction
        intro_cell = self.create_markdown_cell(
            "# Data Science Assignment - Student Solution\\n\\n"
            "This notebook contains my solutions for all 6 tasks.\\n"
            "All code has been tested and produces the expected outputs.\\n"
        )
        notebook["cells"].append(intro_cell)
        
        # Add each task
        for task_num in self.TASK_NUMBERS:
            # Task header
            header_cell = self.create_markdown_cell(
                f"## Task {task_num}\\n\\n"
                f"Below is my solution for Task {task_num}.\\n"
            )
            notebook["cells"].append(header_cell)
            
            # Solution marker
            marker_cell = self.create_markdown_cell(f"{self.PRIMARY_MARKER}\\n")
            notebook["cells"].append(marker_cell)
            
            # Solution code
            code = self.code_provider.get_perfect_code(task_num)
            code_cell = self.create_code_cell(code)
            notebook["cells"].append(code_cell)
            
        return notebook
    
    def create_missing_tasks_notebook(self, missing_tasks: List[int] = [4, 6]) -> Dict[str, Any]:
        """Create notebook with some tasks missing."""
        notebook = self.create_basic_notebook_structure()
        
        # Add introduction
        intro_cell = self.create_markdown_cell(
            "# Data Science Assignment - Partial Solution\\n\\n"
            "This notebook contains solutions for most tasks.\\n"
            f"Tasks {', '.join(map(str, missing_tasks))} are incomplete.\\n"
        )
        notebook["cells"].append(intro_cell)
        
        # Add each task (skip missing ones)
        for task_num in self.TASK_NUMBERS:
            if task_num in missing_tasks:
                # Add task header but no solution
                header_cell = self.create_markdown_cell(
                    f"## Task {task_num}\\n\\n"
                    f"TODO: Complete Task {task_num}\\n"
                )
                notebook["cells"].append(header_cell)
                continue
            
            # Complete task
            header_cell = self.create_markdown_cell(f"## Task {task_num}\\n")
            notebook["cells"].append(header_cell)
            
            marker_cell = self.create_markdown_cell(f"{self.PRIMARY_MARKER}\\n")
            notebook["cells"].append(marker_cell)
            
            code = self.code_provider.get_partial_code(task_num)
            code_cell = self.create_code_cell(code)
            notebook["cells"].append(code_cell)
            
        return notebook
    
    def create_syntax_errors_notebook(self) -> Dict[str, Any]:
        """Create notebook with syntax errors in code."""
        notebook = self.create_basic_notebook_structure()
        
        # Add introduction
        intro_cell = self.create_markdown_cell(
            "# Data Science Assignment - With Syntax Errors\\n\\n"
            "This notebook contains attempts at all tasks but has syntax errors.\\n"
        )
        notebook["cells"].append(intro_cell)
        
        # Add each task with errors
        for task_num in self.TASK_NUMBERS:
            header_cell = self.create_markdown_cell(f"## Task {task_num}\\n")
            notebook["cells"].append(header_cell)
            
            marker_cell = self.create_markdown_cell(f"{self.PRIMARY_MARKER}\\n")
            notebook["cells"].append(marker_cell)
            
            code = self.code_provider.get_syntax_error_code(task_num)
            code_cell = self.create_code_cell(code, executed=False)
            notebook["cells"].append(code_cell)
            
        return notebook
    
    def create_empty_notebook(self) -> Dict[str, Any]:
        """Create empty notebook with no solutions."""
        notebook = self.create_basic_notebook_structure()
        
        # Add just the introduction
        intro_cell = self.create_markdown_cell(
            "# Data Science Assignment - Empty\\n\\n"
            "This notebook template is ready for solutions.\\n"
        )
        notebook["cells"].append(intro_cell)
        
        # Add task headers but no solutions
        for task_num in self.TASK_NUMBERS:
            header_cell = self.create_markdown_cell(
                f"## Task {task_num}\\n\\n"
                "Please add your solution below.\\n"
            )
            notebook["cells"].append(header_cell)
            
        return notebook
    
    def create_special_chars_notebook(self) -> Dict[str, Any]:
        """Create notebook with special characters and unicode."""
        notebook = self.create_basic_notebook_structure()
        
        # Add introduction with special characters
        intro_cell = self.create_markdown_cell(
            "# Assignment de Data Science — Solutions Complètes 🎓\\n\\n"
            "Ce notebook contient les solutions avec caractères spéciaux.\\n"
            "Includes: áéíóú, 中文, русский, emojis 🎉, math symbols: μ σ ± ≤ ≥\\n"
        )
        notebook["cells"].append(intro_cell)
        
        # Add each task with special characters
        for task_num in self.TASK_NUMBERS:
            header_cell = self.create_markdown_cell(
                f"## Tâche {task_num} — Data Processing ⚡\\n\\n"
                f"Solution pour la tâche {task_num} avec caractères spéciaux.\\n"
            )
            notebook["cells"].append(header_cell)
            
            marker_cell = self.create_markdown_cell(f"{self.PRIMARY_MARKER}\\n")
            notebook["cells"].append(marker_cell)
            
            code = self.code_provider.get_special_chars_code(task_num)
            code_cell = self.create_code_cell(code)
            notebook["cells"].append(code_cell)
            
        return notebook
    
    def create_secondary_marker_notebook(self) -> Dict[str, Any]:
        """Create notebook using secondary marker format."""
        notebook = self.create_basic_notebook_structure()
        
        # Add introduction
        intro_cell = self.create_markdown_cell(
            "# Data Science Assignment - Secondary Marker Format\\n\\n"
            "This notebook uses the alternative solution marker format.\\n"
        )
        notebook["cells"].append(intro_cell)
        
        # Add tasks with secondary marker
        for task_num in self.TASK_NUMBERS:
            header_cell = self.create_markdown_cell(f"## Task {task_num}\\n")
            notebook["cells"].append(header_cell)
            
            # Use secondary marker format
            marker_cell = self.create_markdown_cell(f"{self.SECONDARY_MARKER}\\n")
            notebook["cells"].append(marker_cell)
            
            code = self.code_provider.get_perfect_code(task_num)
            code_cell = self.create_code_cell(code)
            notebook["cells"].append(code_cell)
            
        return notebook
    
    def save_notebook(self, notebook: Dict[str, Any], filename: str):
        """Save notebook to file."""
        filepath = self.notebooks_dir / f"{filename}.ipynb"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
    
    def create_corrupted_notebook_file(self, filename: str):
        """Create corrupted JSON file."""
        filepath = self.notebooks_dir / f"{filename}.ipynb"
        with open(filepath, 'w') as f:
            f.write('{"cells": [invalid json structure, "missing": brackets')
    
    def generate_all_notebooks(self):
        """Generate all notebook fixtures."""
        # Perfect student
        perfect_nb = self.create_perfect_student_notebook()
        self.save_notebook(perfect_nb, "perfect_student")
        
        # Missing tasks
        missing_nb = self.create_missing_tasks_notebook([4, 6])
        self.save_notebook(missing_nb, "missing_tasks_student")
        
        # Syntax errors
        syntax_nb = self.create_syntax_errors_notebook()
        self.save_notebook(syntax_nb, "syntax_errors_student")
        
        # Empty notebook
        empty_nb = self.create_empty_notebook()
        self.save_notebook(empty_nb, "empty_notebook")
        
        # Special characters
        special_nb = self.create_special_chars_notebook()
        self.save_notebook(special_nb, "special_chars_student")
        
        # Secondary marker format
        secondary_nb = self.create_secondary_marker_notebook()
        self.save_notebook(secondary_nb, "secondary_marker_student")
        
        # Corrupted notebook
        self.create_corrupted_notebook_file("corrupted_notebook")
