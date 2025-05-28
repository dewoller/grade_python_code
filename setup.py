"""Setup script for the student marking tool."""

from pathlib import Path
from setuptools import setup, find_packages

# Read the README file
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text()
else:
    long_description = "A CLI tool for marking programming assignments from Jupyter notebooks."

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]
else:
    requirements = [
        "click>=8.1.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "pyyaml>=6.0",
        "dspy-ai>=2.0.0",
        "openai>=1.0.0",
        "nbformat>=5.9.0",
    ]

setup(
    name="mark-student",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A CLI tool for marking programming assignments from Jupyter notebooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mark-student",
    packages=find_packages(where=".", include=["src*", "tests*"]),
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Topic :: Education :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mark-student=src.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["*.yaml", "*.toml"],
    },
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/yourusername/mark-student/issues",
        "Source": "https://github.com/yourusername/mark-student",
    },
)
